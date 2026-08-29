#!/usr/bin/env python3
"""
通用本地 LLM 实时性能监测服务 v2（支持 llama-server + vLLM 双引擎）
- 自动发现所有运行中的 llama-server / vllm.entrypoints 实例，追踪各自的 P(prefill)/D(decode) 速率
- 智能追踪最新 log：每 N 秒通过 /proc/PID/fd 重新绑定活跃进程的日志文件
- llama-server：解析 prompt processing / process_toke 行（瞬时 P/D）
- vLLM：解析 "Avg prompt throughput / Avg generation throughput" 引擎统计行（10s 引擎级均值）
- 支持多模型：qwen3.8-27b(vllm)、qwen3.8-27b(llama gguf) 等，每个模型一个监测卡片
- Web 页面(127.0.0.1:PORT)，每 5s 刷新，白天/黑夜深浅主题
- /api 返回所有模型的 P/D 数据数组，/api/<model_id> 返回单个
"""
import os, re, json, time, threading, subprocess, urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.getenv("MONITOR_PORT", "8096"))
MAX_LOG_BYTES = int(os.getenv("MONITOR_MAX_BYTES", str(100 * 1024 * 1024)))
SCAN_INTERVAL = 1  # 重新扫描日志文件的间隔(秒)，监控实时性
STATE_FILE = os.getenv("MONITOR_STATE", "/home/wuyangcheng/scripts/llm_monitor_state.json")  # 状态持久化（重启不丢下线模型）

# 追踪的进程模式：llama-server（llama.cpp）、vllm api_server 主进程 + VLLM Worker 子进程
# Worker 继承 stdout fd：即使主进程已死（孤儿 Worker 仍占 GPU），也可从 Worker /proc/fd 找到日志
PROC_PATTERNS = ["llama-server", "vllm.entrypoints", "VLLM::Worker"]

# [2026-08-29 decode 修正] decode 主导窗口判据：prefill 吞吐不超过 generation 的
# 该倍数，才视为“decode 主导窗口”（否则该窗口被 prefill 占满 GPU 时间，generation 被稀释）。
# 用于排除 prefill 污染，使 decode 速率更贴近纯 decode。
DECODE_PREFILL_MAX_RATIO = 1.0  # pf_tps <= gen_tps * 该值 视为 decode 主导；0=只要无 prefill(pf_tps=0) 才计入

def infer_model(log_path):
    """从日志路径推断模型名并规范化：
    llama_dsv4flash_v9.log -> dsv4flash；vllm_awq_int4_tp2_test.log -> awq_int4_tp2_test"""
    name = os.path.basename(log_path)
    m = re.match(r"(?:llama|vllm)_([a-zA-Z0-9_.\-]+?)\.log", name)
    if m:
        raw = m.group(1)
        # 去掉 _vN 版本后缀（dsv4flash_v9 -> dsv4flash, qwen3.8_v2 -> qwen3.8）
        raw = re.sub(r"_[vV]\d+$", "", raw)
        return raw
    return name

# ---------- 模型状态 ----------
class ModelState:
    def __init__(self, model_id, log_path, source):
        self.model_id = model_id
        self.log_path = log_path
        self.source = source  # "llama" | "vllm"
        self.last_pos = 0
        self.last_seen = time.time()  # 最近一次活跃时间（down 保留用）
        self.lock = threading.Lock()
        self.state = {
            "model_id": model_id, "log": log_path, "source": source,
            "alive": True, "mtp": False,
            "latest_task": None, "prefill_last": None,
            "decode": {"last_n": None, "last_ts": None, "last_rate": 0.0, "window_n": []},
            "peak_decode": 0.0, "peak_task": None, "peak_prefill": 0.0,
            "peak_ts": None,  # 最近一次速率数据时间（会话级峰值判定用）
        }

    def scan(self):
        try:
            size = os.path.getsize(self.log_path)
            if size < self.last_pos: self.last_pos = 0
            offset = self.last_pos
            if size - offset > MAX_LOG_BYTES: offset = size - MAX_LOG_BYTES
            with open(self.log_path, "r", encoding="utf-8", errors="replace") as f:
                f.seek(offset); content = f.read()
            self.last_pos = size
        except Exception:
            return
        if self.source == "llama":
            self._scan_llama(content)
        else:
            self._scan_vllm(content)

    # ---- llama-server：瞬时 P/D（逐 token 级） ----
    def _scan_llama(self, content):
        prefill_pat = re.compile(r"prompt processing.*n_tokens =\s*(\d+).*progress = ([\d.]+).*t =\s*([\d.]+) s.*?([\d.]+) tokens per second")
        decode_pat = re.compile(r"task (\d+).*n_gen =\s*(\d+).*n_remaining =\s*(\d+)")
        s = self.state
        now = time.time()
        with self.lock:
            tasks = re.findall(r"task (\d+)", content)
            if tasks: s["latest_task"] = tasks[-1]
            pf = prefill_pat.findall(content)
            if pf:
                nt, prog, t, tps = pf[-1]
                s["prefill_last"] = {"task": s.get("latest_task"), "tokens": int(nt), "t": float(t), "progress": float(prog), "tps": float(tps)}
                # 会话级峰值：任务变化或 30s 无数据时重置
                if s.get("peak_task") != s.get("latest_task") or (s.get("peak_ts") and now - s["peak_ts"] > 30):
                    s["peak_prefill"] = 0.0
                s["peak_prefill"] = max(s["peak_prefill"], float(tps))
                s["peak_ts"] = now
            dec = []
            for line in content.splitlines():
                if "process_toke" not in line: continue
                m = decode_pat.search(line)
                if m:
                    ts = re.match(r"(\d+\.\d+\.\d+\.\d+)", line)
                    if ts:
                        mn, sec, msec, usec = map(int, ts.group(1).split("."))
                        dec.append((((mn*60+sec)*1000)+msec, int(m.group(2))))
            if dec:
                last_ts, last_n = dec[-1]
                cur_task = s.get("latest_task")
                if s.get("peak_task") != cur_task:
                    s["peak_decode"] = 0.0; s["peak_task"] = cur_task
                    s["peak_prefill"] = 0.0
                    s["decode"]["window_n"] = []; s["decode"]["last_n"] = None; s["decode"]["last_ts"] = None
                d = s["decode"]
                if d["last_n"] is not None and d["last_ts"] is not None:
                    dt = last_ts - d["last_ts"]; dn = last_n - d["last_n"]
                    if dt > 0 and dn > 0:
                        rate = dn * 1000.0 / dt
                        d["last_rate"] = rate
                        s["peak_decode"] = max(s["peak_decode"], rate)
                        d["window_n"].append((last_ts, last_n))
                        d["window_n"] = [(t, n) for (t, n) in d["window_n"] if last_ts - t <= 12000]
                d["last_n"] = last_n; d["last_ts"] = last_ts

    # ---- vLLM：引擎级 10s 均值（Avg prompt/generation throughput） ----
    def _scan_vllm(self, content):
        eng_pat = re.compile(r"Avg prompt throughput:\s*([\d.]+) tokens/s,\s*Avg generation throughput:\s*([\d.]+) tokens/s")
        run_pat = re.compile(r"Running:\s*(\d+) reqs")
        s = self.state
        with self.lock:
            runs = run_pat.findall(content)
            running = int(runs[-1]) if runs else None
            if runs: s["latest_task"] = f"run={runs[-1]}"
            eng = eng_pat.findall(content)
            if eng:
                pf_tps, gen_tps = eng[-1]
                pf_tps, gen_tps = float(pf_tps), float(gen_tps)
                now = time.time()
                # 会话级峰值：30s 无新速率数据视为新会话（vLLM 无 task 概念，用时间窗）
                if s.get("peak_ts") and now - s["peak_ts"] > 30:
                    s["peak_decode"] = 0.0
                    s["peak_prefill"] = 0.0
                s["peak_ts"] = now
                # 严格口径：prefill/decode 只取有请求活动的窗口（Running>0），
                # 跳过空闲 0 稀释窗口；无活动时保留最近真实值
                if pf_tps > 0:
                    s["prefill_last"] = {"task": s.get("latest_task"), "tokens": 0, "t": 0.0, "progress": 0.0, "tps": pf_tps}
                    s["peak_prefill"] = max(s["peak_prefill"], pf_tps)
                # [2026-08-29 decode 修正] decode 瞬时速率由 fetch_vllm_metrics（/metrics 每秒差分）
                # 负责写 last_rate/peak_decode/window_n；这里不再写 decode，避免 10s 引擎日志
                # Avg 均值覆盖每秒瞬时值。prefill_last/peak_prefill 仍由本函数（日志 pf_tps）跟踪。
                # （之前的问题：本函数写 decode 字段，与 fetch 差分竞争覆盖，导致看板拿到 10s 均值）

# ---------- 发现活跃进程日志（llama-server + vLLM） ----------
def _proc_port(pid: str):
    """从 /proc/PID/cmdline 解析 --port（llama-server / vllm 都有）"""
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            cmd = f.read().decode("utf-8", errors="replace").replace("\x00", " ")
        m = re.search(r"--port\s+(\d+)", cmd) or re.search(r"--port=(\d+)", cmd)
        return m.group(1) if m else None
    except Exception:
        return None

def _proc_gpus(pid: str):
    """从 /proc/PID/environ 解析 CUDA_VISIBLE_DEVICES（实例实际使用的 GPU 卡）"""
    try:
        with open(f"/proc/{pid}/environ", "rb") as f:
            env = f.read().decode("utf-8", errors="replace").replace("\x00", "\n")
        for line in env.splitlines():
            if line.startswith("CUDA_VISIBLE_DEVICES="):
                return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return None

def _proc_mtp(pid: str):
    """从 /proc/PID/cmdline 判断是否启用 MTP（--speculative-config 含 mtp）"""
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            cmd = f.read().decode("utf-8", errors="replace").replace("\x00", " ")
        return bool(re.search(r"speculative-config[^\s]*\"?\s*(mtp|\{)", cmd) or re.search(r"\bmtp\b", cmd))
    except Exception:
        return False

def find_active_logs():
    """通过 pgrep 找活跃进程（llama-server / vllm api_server），
    用 /proc/PID/fd 找它打开的日志文件，返回 {log_path: (port, gpus, mtp)}"""
    logs: dict[str, tuple] = {}
    for pat in PROC_PATTERNS:
        try:
            out = subprocess.run(["pgrep", "-f", pat], capture_output=True, text=True)
            pids = [p for p in out.stdout.split() if p.isdigit()]
            for pid in pids:
                port = _proc_port(pid)
                gpus = _proc_gpus(pid)
                mtp = _proc_mtp(pid)
                try:
                    fd_dir = f"/proc/{pid}/fd"
                    for fd in os.listdir(fd_dir):
                        try:
                            target = os.readlink(f"{fd_dir}/{fd}")
                            if re.search(r"(llama|vllm).*\.log", target) and target.endswith(".log"):
                                rp = os.path.realpath(target)
                                if rp not in logs or port:
                                    logs[rp] = (port or (logs[rp][0] if rp in logs else None),
                                                gpus or (logs[rp][1] if rp in logs else None),
                                                mtp or (logs[rp][2] if rp in logs else False))
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass
    return logs

# ---------- 模型实例管理 ----------
models = {}
models_lock = threading.Lock()

def refresh_models():
    logs = find_active_logs()  # {log_path: (port, gpus, mtp)}
    now = time.time()
    with models_lock:
        # 先全部标记为下线，活跃进程再翻回 alive（下线实例保留数据供对比）
        for m in models.values():
            m.state["alive"] = False
        active_keys = set()
        for lp, (port, gpus, mtp) in logs.items():
            mid = infer_model(lp)
            if mid in active_keys:
                continue  # 同模型多个日志取第一个
            active_keys.add(mid)
            if mid in models:
                m = models[mid]
                m.state["alive"] = True
                m.last_seen = now
                if port: m.state["port"] = port
                if gpus: m.state["gpus"] = gpus
                m.state["mtp"] = bool(mtp)
            else:
                source = "vllm" if "vllm" in os.path.basename(lp).lower() else "llama"
                m = ModelState(mid, lp, source)
                if port: m.state["port"] = port
                if gpus: m.state["gpus"] = gpus
                m.state["mtp"] = bool(mtp)
                models[mid] = m
        # 清理下线超过 2 小时的实例（避免无限累积）
        for mid in [k for k, m in list(models.items())
                    if not m.state.get("alive") and now - (m.last_seen or 0) > 7200]:
            del models[mid]
    for mid, m in list(models.items()):
        if m.state.get("alive"):
            m.scan()

def fetch_vllm_metrics(port):
    """拉取 vLLM /metrics 的 token 计数器（vllm:prompt_tokens_total / generation_tokens_total）
    返回 (prompt_total, generation_total) 或 None"""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/metrics", timeout=1) as r:
            txt = r.read().decode("utf-8", errors="replace")
        # [2026-08-29 fix] vLLM /metrics 的这两个计数器带 label {engine=...,model_name=...}，
        # 原 regex 锚定行首 + \s+ 匹配不到带 label 的值 -> 恒 None -> 瞬时差分从未生效（看板只有 10s 日志均值）。
        # 改为允许 {label} 存在。
        pt = re.search(r"^vllm:prompt_tokens_total(?:\{[^}]*\})?\s+([\d.]+)", txt, re.M)
        gt = re.search(r"^vllm:generation_tokens_total(?:\{[^}]*\})?\s+([\d.]+)", txt, re.M)
        if pt and gt:
            return float(pt.group(1)), float(gt.group(1))
    except Exception:
        pass
    return None

def fetch_vllm_specmetrics(port):
    """拉取 vLLM /metrics 的 MTP 投机计数器（spec_decode_num_draft_tokens_total /
    spec_decode_num_accepted_tokens_total），返回 (draft_total, accepted_total) 或 None。
    [2026-08-30] 用于计算平均 MTP 接受率（accepted/draft）。"""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/metrics", timeout=1) as r:
            txt = r.read().decode("utf-8", errors="replace")
        dr = re.search(r"^vllm:spec_decode_num_draft_tokens_total(?:\{[^}]*\})?\s+([\d.]+)", txt, re.M)
        ac = re.search(r"^vllm:spec_decode_num_accepted_tokens_total(?:\{[^}]*\})?\s+([\d.]+)", txt, re.M)
        if dr and ac:
            return float(dr.group(1)), float(ac.group(1))
    except Exception:
        pass
    return None

def _instant_decoder_thread():
    """[2026-08-29] 独立 1s 瞬时 decode 采样：每 1s 对每个 alive vllm 实例做
    fetch_vllm_metrics 计数器差分，直接写 decode.last_rate/peak_decode/window_n。
    与主 loop（含日志 scan）隔离，避免 scan 读日志阻塞或 10s 引擎均值覆盖，
    保证看板 decode 呈现 1s 瞬时速率（数据源 generation_tokens_total 每秒均更新）。
    """
    prev: dict = {}
    prev_spec: dict = {}  # model_id -> (ts, draft_total, accepted_total)
    import sys as _sys
    dbg = int(__import__("os").getenv("INSTANT_DEBUG", "0"))
    while True:
        try:
            now = time.time()
            with models_lock:
                vms = [(mid, m) for mid, m in models.items()
                       if m.state.get("alive") and m.state.get("source") == "vllm" and m.state.get("port")]
            for mid, m in vms:
                try:
                    # fetch 放锁外，避免 m.lock 争抢阻塞
                    res = fetch_vllm_metrics(m.state["port"])
                    if not res:
                        if dbg:
                            print(f"[instant][{mid}] fetch None", file=_sys.stderr, flush=True)
                        continue
                    pt, gt = res
                    pr = prev.get(mid)
                    # [2026-08-30] 并行拉 MTP 投机计数器，差分算平均接受率
                    sp = fetch_vllm_specmetrics(m.state["port"])
                    with m.lock:
                        st = m.state
                        d = st["decode"]
                        if pr and gt >= pr[2] and pt >= pr[1]:
                            dt = now - pr[0]
                            if dt > 0.5:
                                gen_rate = (gt - pr[2]) / dt
                                if gen_rate > 0:
                                    d["last_rate"] = round(gen_rate, 1)
                                    st["peak_decode"] = max(st.get("peak_decode") or 0, gen_rate)
                                    d["window_n"].append((int(now * 1000), gen_rate))
                                    d["window_n"] = [(t, v) for (t, v) in d["window_n"] if now * 1000 - t <= 120000]
                                    d["last_n"] = gen_rate
                                    d["last_ts"] = int(now * 1000)
                        # [2026-08-30] MTP 接受率 / 平均接受长度（瞬时 + 累计）
                        # [2026-08-30 fix] 无 MTP 实例（spec_decode 计数器不存在，sp=None）
                        # 必须清除曾写入的 MTP 字段，否则残留的 cum_accept_rate 会让前端误判为 MTP 实例。
                        if sp is None:
                            for _k in ("last_accept_rate", "last_accept_len", "cum_accept_rate", "cum_accept_len"):
                                d.pop(_k, None)
                            prev_spec.pop(mid, None)
                        if sp:
                            sp_prev = prev_spec.get(mid)
                            if sp_prev and sp[0] >= sp_prev[1] and sp[1] >= sp_prev[2]:
                                sdt = now - sp_prev[0]
                                if sdt > 0.5:
                                    d_draft = sp[0] - sp_prev[1]
                                    d_acc = sp[1] - sp_prev[2]
                                    if d_draft > 0:
                                        inst_ar = d_acc / d_draft
                                        d["last_accept_rate"] = round(inst_ar * 100, 1)  # %
                                        d["last_accept_len"] = round((d_acc / d_draft) + 1.0, 2)  # 平均步产出 token
                            # 累计接受率（历史累积）
                            if sp[0] > 0:
                                cum_ar = sp[1] / sp[0]
                                d["cum_accept_rate"] = round(cum_ar * 100, 1)
                                d["cum_accept_len"] = round((sp[1] / sp[0]) + 1.0, 2)
                            prev_spec[mid] = (now, sp[0], sp[1])
                        prev[mid] = (now, pt, gt)
                except Exception as e:
                    if dbg:
                        print(f"[instant][{mid}] ERR {e!r}", file=_sys.stderr, flush=True)
        except Exception as e:
            if dbg:
                print(f"[instant] OUTER ERR {e!r}", file=_sys.stderr, flush=True)
        time.sleep(1.0)


def loop():
    metric_prev: dict[str, tuple] = {}  # model_id -> (ts, prompt_total, gen_total)
    while True:
        try:
            refresh_models()
            # vLLM 实时速率：/metrics 计数器每秒差分（比引擎 10s Avg 窗口更实时）
            now = time.time()
            with models_lock:
                vllm_models = [(mid, m) for mid, m in models.items()
                               if m.state.get("alive") and m.state.get("source") == "vllm" and m.state.get("port")]
            for mid, m in vllm_models:
                try:
                    res = fetch_vllm_metrics(m.state["port"])
                    if not res:
                        continue
                    pt, gt = res
                    prev = metric_prev.get(mid)
                    with m.lock:
                        st = m.state
                        if prev and pt >= prev[1] and gt >= prev[2]:
                            dt = now - prev[0]
                            if dt > 0:
                                pf_rate = (pt - prev[1]) / dt
                                gen_rate = (gt - prev[2]) / dt
                                if pf_rate > 0:
                                    st["prefill_last"] = {"task": st.get("latest_task"), "tokens": int(pt), "t": 0.0, "progress": 0.0, "tps": round(pf_rate, 1)}
                                    st["peak_prefill"] = max(st.get("peak_prefill") or 0, pf_rate)
                                # [2026-08-30] decode 瞬时速率/peak/window 由 _instant_decoder_thread 唯一负责，
                                # 这里不再写 decode，避免与 1s 瞬时竞争（loop 的 pf_rate 引擎均值会覆盖瞬时）
                        metric_prev[mid] = (now, pt, gt)
                except Exception:
                    pass
            # 持久化状态（下线模型数据留存，重启可恢复）
            try:
                with models_lock:
                    snap = [json.loads(json.dumps(m.state)) for m in models.values()]
                tmp = STATE_FILE + ".tmp"
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump({"at": time.strftime("%F %T"), "models": snap}, f, ensure_ascii=False)
                os.replace(tmp, STATE_FILE)
            except Exception:
                pass
        except Exception:
            pass
        time.sleep(SCAN_INTERVAL)

def load_state():
    """启动时恢复上次状态（保留已下线模型的历史数据）"""
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        with models_lock:
            for s in data.get("models", []):
                mid = s.get("model_id")
                if not mid or mid in models:
                    continue
                m = ModelState(mid, s.get("log", mid), s.get("source", "llama"))
                m.state = s
                m.last_seen = time.time() - 3600  # 视为已下线一段时间
                models[mid] = m
    except Exception:
        pass

# ---------- HTML ----------
HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>本地 LLM 实时监测 (多引擎)</title>
<style>
:root{--bg:#111;--card:#1a1a1a;--line:#333;--text:#0f0;--dim:#888;--green:#0f0;--yellow:#ff0;--cyan:#0ff;--err:#fca5a5}
@media (prefers-color-scheme: light){:root{--bg:#f5f5f5;--card:#fff;--line:#ddd;--text:#064e00;--dim:#666;--green:#0a7a2e;--yellow:#a16207;--cyan:#0e7490;--err:#b91c1c}}
body{font-family:monospace;background:var(--bg);color:var(--text);padding:20px}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:15px;margin:10px 0}
.big{font-size:34px;font-weight:bold}
.green{color:var(--green)}.yellow{color:var(--yellow)}.cyan{color:var(--cyan)}.dim{color:var(--dim)}
.tag{display:inline-block;font-size:11px;border:1px solid var(--line);border-radius:4px;padding:1px 6px;margin-left:8px;vertical-align:middle;color:var(--dim)}
.empty{color:var(--dim);font-size:13px}
</style>
<script>
async function refresh(){
  try{
    const r=await fetch('/api');const models=await r.json();
    const list=Array.isArray(models)?models:[models];
    const wrap=document.getElementById('models');
    let html='';
    for(const d of list){
      const dec=d.decode||{};const pf=d.prefill_last||{};
      const dx=dec.last_rate!=null?dec.last_rate.toFixed(1):'—';
      const dp=d.peak_decode!=null?d.peak_decode.toFixed(1):'—';
      let dw='—';const wn=dec.window_n||[];if(wn.length>1){const now=wn[wn.length-1][0];const w5=wn.filter(e=>now-e[0]<=5000);const ww=w5.length>1?w5:wn;const dts=ww[ww.length-1][0]-ww[0][0];const dns=ww[ww.length-1][1]-ww[0][1];dw=dts>0?(dns*1000/dts).toFixed(1):'—'}
      const pftps=pf.tps!=null?pf.tps.toFixed(1):'—';
      const pfptr=pf.progress!=null?(pf.progress*100).toFixed(0):'—';
      const pfTok=pf.tokens!=null?pf.tokens:'—';
      const src=(d.source||'llama')==='vllm'?'vLLM':'llama.cpp';
      // [2026-08-30] MTP 接受率（仅 MTP 实例有）
      const arNow=dec.last_accept_rate!=null?dec.last_accept_rate.toFixed(1):'—';
      const arCum=dec.cum_accept_rate!=null?dec.cum_accept_rate.toFixed(1):'—';
      const alNow=dec.last_accept_len!=null?dec.last_accept_len.toFixed(2):'—';
      const alCum=dec.cum_accept_len!=null?dec.cum_accept_len.toFixed(2):'—';
      const hasMtp=!!d.mtp&&!(dec.last_accept_rate==null&&dec.cum_accept_rate==null);
      html+=`<div class="card"><h3 style="margin:0 0 10px;color:var(--cyan)">${d.model_id||'?'}<span class="tag">${src}</span></h3>
        <div style="display:flex;gap:26px;flex-wrap:wrap">
          <div><div class="dim">task</div><div class="big cyan">${d.latest_task||'—'}</div></div>
          <div><div class="dim">Decode 瞬时</div><div class="big green">${dx}</div><div class="dim">tok/s</div></div>
          <div><div class="dim">Decode 5s均值</div><div class="big yellow">${dw}</div><div class="dim">tok/s</div></div>
          <div><div class="dim">Decode 峰值</div><div class="big green">${dp}</div><div class="dim">tok/s</div></div>
        </div>
        <div class="dim" style="border-top:1px solid var(--line);margin-top:8px;padding-top:8px">Prefill: <b style="color:var(--yellow)">${pftps}</b> tok/s · ${pfptr}% · ${pfTok} tok</div>
        ${hasMtp?`<div class="dim" style="border-top:1px solid var(--line);margin-top:8px;padding-top:8px">MTP: 接受率 <b style="color:var(--green)">${arNow}%</b>(瞬时) / <b style="color:var(--cyan)">${arCum}%</b>(累计) · 平均每步 <b style="color:var(--yellow)">${alNow}</b>(瞬时)/<b style="color:var(--cyan)">${alCum}</b>(累计) token</div>`:''}
        <div class="dim" style="font-size:11px">log: ${d.log||''}</div></div>`;
    }
    wrap.innerHTML=html||'<div class="empty">未发现活跃 llama-server / vLLM 实例</div>';
  }catch(e){document.getElementById('err').textContent='连接失败 '+e;}
}
setInterval(refresh,5000);refresh();
</script></head><body>
<h2>本地 LLM 实时监测 (P/D · llama.cpp + vLLM)</h2>
<div id="models"></div>
<div class="card dim" id="err"></div>
</body></html>
"""

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api":
            with models_lock:
                d = [json.loads(json.dumps(m.state)) for m in models.values()]
            body = json.dumps(d).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
        elif self.path.startswith("/api/"):
            mid = self.path.split("/api/")[1]
            with models_lock:
                m = models.get(mid)
                d = json.loads(json.dumps(m.state)) if m else {"error": "not found", "model_id": mid}
            body = json.dumps(d).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
        else:
            body = HTML.encode()
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
    def log_message(self, *a): pass

if __name__ == "__main__":
    load_state()
    threading.Thread(target=loop, daemon=True).start()
    threading.Thread(target=_instant_decoder_thread, daemon=True).start()
    httpd = HTTPServer(("127.0.0.1", PORT), Handler)
    print(f"monitor v2 on http://127.0.0.1:{PORT} (多引擎多模型智能追踪 + 下线留存)")
    httpd.serve_forever()

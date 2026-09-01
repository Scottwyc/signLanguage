#!/usr/bin/env python3
"""daemon 版死循环监督 watchdog v1：检测成员会话陷入思考/输出死循环，自动打断 + 按 ctx 余量恢复。

背景（2026-09-01 Owner 要求）：
- 本地 AWQ4 量化的 Qwen3.6 MoE（35b 等）会出现"思考循环"问题——模型在思考/输出阶段
  陷入无限重复，耗尽 token/上下文却不产出有效结果，会话像卡死。
- 已有 daemon_context_watchdog_v1.py 管"context 超限→两级压缩"，但管不了"死循环"
  （上下文未必超限，只是模型自己在空转）。
- 需要给团队成员会话增加一个监督：抓取 transcript 尾部，若发现陷入死循环达到一定次数，
  及时打断，并根据 ctx 余量占比决定是否需要 /compress，再补发「继续完成」恢复任务。

数据源（只读，不依赖 SSE 事件流——SSE 只吐 git_status_changed 这类离散事件，不流式吐 token）：
- chats/<session_id>.jsonl：Qwen Code 会话 transcript。assistant 消息的
  message.role == 'model'，正文在 message.parts[].text（Qwen Code 不落盘 thinking，
  parts 元素还有 functionCall 等）。检测从这些 text 提取、做重复性判定。
- daemon /session/:id/context-usage：精确 totalTokens / contextWindowSize → 算 ctx 余量占比。
- daemon /session/:id/status：hasActivePrompt / hasTurnError 等（判定会话是否正在生成）。

判定与恢复流程（对每个角色的单个检测周期）：
1. 读取最近 LOOKBACK 条 model 消息的 text（仅取 transcript 尾部，见 TAIL_BYTES）。
2. 归一化后计算"连续重复度"：取最近 N=REPEAT_WINDOW 条，若它们两两高度相似
   （相似度 >= SIMILARITY_THRESHOLD），判定为死循环。
3. 命中且满足触发条件（正在生成 / 冷却期外 / 历史触发次数未达上限）→ 执行恢复：
   a) POST /session/:id/cancel 打断当前生成（保留上下文）。
   b) 查 context-usage：若余量占比 < CONTEXT_LOW_RATIO（默认 0.2=20%）→ 先 POST
      /compress（等完成），再补发「继续完成」；否则直接补发「继续完成」。
      （仅用 /compress 单级而非 /compress-fast 是遵循 Owner 指点；compress 完成后
      上下文字段更紧凑，补发「继续完成」让模型从断点续做。）
4. 冷却 COOLDOWN_SECONDS，防止同一会话被反复打断；窗口内触发次数达上限转人工。

运行模式：常驻进程（与 daemon_context_watchdog_v1.py 同模式），输出到
.team/daemon_v1/loop_watchdog_state.json + loop_watchdog.log，告警写 team_messages.log。

用法：
    python3 daemon_loop_watchdog_v1.py --interval 10
    python3 daemon_loop_watchdog_v1.py --once            # 单周期（调试）
    python3 daemon_loop_watchdog_v1.py --dry-run         # 只检测不执行 cancel/compress/prompt
    python3 daemon_loop_watchdog_v1.py --only signL10    # 只监护指定角色
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from daemon_auth_v1 import auth_headers

BASE = Path("/data/WYC/signLanguage/.team")
OUT_DIR = BASE / "daemon_v1"
REGISTRY = OUT_DIR / "registry.json"
STATE = OUT_DIR / "loop_watchdog_state.json"
LOG = OUT_DIR / "loop_watchdog.log"
TEAM_MESSAGES = BASE / "team_messages.log"
INTERVENTION_QUEUE = BASE / "team_intervention_queue.json"
MEMBERS_DIR = OUT_DIR / "members"
CHATS_DIR = Path("/home/wuyangcheng/.qwen/projects/-data-WYC-signLanguage/chats")

DAEMON_URL = "http://127.0.0.1:4194"
WORKSPACE = "/data/WYC/signLanguage"

# ---- 死循环检测参数 ----
LOOKBACK = 12            # 检测时往回看多少条 model 消息（含当前窗口）
REPEAT_WINDOW = 3        # 判定"连续重复"需要最近 N 条高度相似
SIMILARITY_THRESHOLD = 0.90   # 归一化后两两相似度阈值（>= 判为重复）
TAIL_BYTES = 512 * 1024  # 只读 transcript 尾部，避免大文件全扫（曾 120s 超时）
MIN_TEXT_LEN = 120       # 文本长度低于此值不判死循环（太短无意义，避免误伤）

# ---- 恢复/打断参数 ----
CONTEXT_LOW_RATIO = 0.20      # ctx 余量占比低于此值 → 需 /compress
COMPRESS_TIMEOUT_SECONDS = 900  # /compress turn 完成超时
CONTINUE_PROMPT = ("【系统通知】检测到你的输出陷入重复循环，已自动打断。请检查你当前的工作进度，"
                   "并继续完成之前的任务。")
STATUS_POLL_SECONDS = 5        # 等 turn 完成的轮询间隔

# ---- 冷却/限流 ----
COOLDOWN_SECONDS = 120          # 同一会话两次自动打断的最小间隔
TRIGGER_LIMIT = 3               # 单会话窗口内触发次数上限，超过转人工
TRIGGER_WINDOW_SECONDS = 3600   # 触发次数统计窗口
ALERT_SUPPRESS_SECONDS = 600    # 告警抑制（同一会话重复告警不刷屏）


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def log(msg: str) -> None:
    line = f"[{now_iso()}] {msg}"
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line, flush=True)


def alert(role: str, kind: str, detail: str) -> None:
    line = f"[{now_iso()}] 【自动健康告警】loop-watchdog | 角色: {role} | 类型: {kind} | 详情: {detail[:300]}"
    with TEAM_MESSAGES.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    log(f"[ALERT] {role} {kind}: {detail[:200]}")


def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def http_json(method: str, path: str, body: dict | None = None, timeout: float = 10.0) -> tuple[int, dict]:
    headers = auth_headers({"Accept": "application/json"})
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(DAEMON_URL.rstrip("/") + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        try:
            raw = e.read().decode("utf-8")
            parsed = json.loads(raw) if raw else {}
        except (OSError, json.JSONDecodeError):
            parsed = {"error": str(e)}
        return e.code, parsed
    except (urllib.error.URLError, OSError) as e:
        return 0, {"error": f"{type(e).__name__}: {e}"}


def session_status(session_id: str) -> tuple[int, dict]:
    return http_json("GET", f"/session/{urllib.parse.quote(session_id, safe='')}/status")


def context_usage(session_id: str) -> tuple[int, dict]:
    return http_json("GET", f"/session/{urllib.parse.quote(session_id, safe='')}/context-usage")


def cancel_session(session_id: str) -> tuple[int, dict]:
    return http_json("POST", f"/session/{urllib.parse.quote(session_id, safe='')}/cancel", {})


def send_prompt(session_id: str, text: str) -> tuple[int, dict]:
    return http_json("POST", f"/session/{urllib.parse.quote(session_id, safe='')}/prompt",
                     {"prompt": [{"type": "text", "text": text}]}, timeout=30.0)


def wait_turn_complete(session_id: str, timeout: float) -> tuple[bool, str]:
    deadline = time.time() + timeout
    while time.time() < deadline:
        code, st = session_status(session_id)
        if code == 404:
            return False, "session_not_found during wait"
        if code == 200:
            if st.get("hasTurnError"):
                return False, "turn_error during wait"
            if not st.get("hasActivePrompt"):
                return True, "completed"
        time.sleep(STATUS_POLL_SECONDS)
    return False, f"timeout after {timeout:.0f}s"


def clean_text(raw: str) -> str:
    """归一化文本：去除空白/控制字符，统一小写，便于相似度比较。"""
    if not raw:
        return ""
    raw = raw.replace("\r", " ").replace("\t", " ")
    raw = re.sub(r"[ \u3000]+", " ", raw)
    raw = re.sub(r"\s*\n\s*", " ", raw)
    return raw.strip().lower()


def extract_model_texts(session_id: str) -> list[str]:
    """读 transcript 尾部，提取最近 model(assistant) 消息的正文文本列表（按时间序）。

    只取 message.role=='model' 且 parts[].text 的文本；过滤掉过短片段。
    """
    path = CHATS_DIR / f"{session_id}.jsonl"
    texts: list[str] = []
    try:
        size = path.stat().st_size
        with path.open("rb") as f:
            f.seek(max(0, size - TAIL_BYTES))
            raw_tail = f.read().decode("utf-8", errors="ignore")
    except OSError:
        return texts
    for line in raw_tail.splitlines():
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        m = d.get("message") or {}
        if m.get("role") != "model":
            continue
        parts = m.get("parts")
        if not isinstance(parts, list):
            continue
        for p in parts:
            if isinstance(p, dict) and isinstance(p.get("text"), str) and p["text"].strip():
                texts.append(p["text"])
    return texts


def similarity(a: str, b: str) -> float:
    """两个归一化文本的相似度（0~1），用 SequenceMatcher。"""
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def detect_repeat_loop(texts: list[str], window: int = REPEAT_WINDOW,
                       threshold: float = SIMILARITY_THRESHOLD) -> bool:
    """判定最近 window 条 model 文本是否高度重复（死循环）。

    以"最后一条为中心"：死循环的本质是模型反复输出同一段话，因此取最近 window 条，
    若最后一条（必须是足够长的正文）与窗口内其余每一条都高度相似（>= threshold），
    则判为死循环。
    - 需至少有 window 条文本；
    - 只要求最后一条长度 >= MIN_TEXT_LEN（其余作为"前面重复的参考"，不强制长度，
      避免把短前缀/工具调用误判——真实死循环每条都接近等长重复大段文本）；
    - 最后一条与其他每条两两相似度均 >= threshold 才判 True。
    """
    if len(texts) < window:
        return False
    recent = texts[-window:]
    latest = recent[-1]
    latest_clean = clean_text(latest)
    # 最后一条必须是足够长的正文（太短可能是工具/短响应，不判）
    if len(latest_clean) < MIN_TEXT_LEN:
        return False
    for prev in recent[:-1]:
        prev_clean = clean_text(prev)
        if len(prev_clean) < MIN_TEXT_LEN // 2:
            continue  # 跳过过短的参考条（避免短前缀干扰），但仍计入窗口
        if similarity(latest_clean, prev_clean) < threshold:
            return False
    return True


def queue_intervention(role: str, detail: str) -> None:
    queue = read_json(INTERVENTION_QUEUE, [])
    if not isinstance(queue, list):
        queue = []
    queue.append({
        "id": f"loop-{int(time.time())}",
        "window": f"daemon:{role}",
        "task": f"daemon loop watchdog 死循环自愈达上限，需人工处理：{detail[:200]}",
        "path": str(STATE),
        "status": "waiting",
        "created_at": now_iso(),
        "completed_at": None,
    })
    INTERVENTION_QUEUE.write_text(json.dumps(queue, ensure_ascii=False, indent=1), encoding="utf-8")


def do_recover(role: str, session_id: str, dry_run: bool) -> dict:
    """执行死循环恢复：cancel 打断 → 查 ctx 余量 → 低余量则 /compress → 补发「继续完成」。"""
    result = {"role": role, "started_at": now_iso(), "stages": []}
    if dry_run:
        result.update({"dry_run": True, "ok": True, "note": "dry-run 跳过实际恢复"})
        return result

    # 阶段 1：cancel 打断当前生成（保留上下文，不丢任务）
    log(f"[{role}] 检测到死循环，发起 cancel 打断")
    ccode, cresp = cancel_session(session_id)
    result["stages"].append({"step": "cancel", "code": ccode, "resp": str(cresp)[:200]})
    if ccode not in (200, 202, 204):
        result.update({"ok": False, "failed_step": "cancel", "error": f"cancel failed: {cresp}"})
        return result

    # 阶段 2：查 ctx 余量，决定是否需要 /compress
    time.sleep(1.5)  # 给 cancel 一点生效时间
    ucode, udata = context_usage(session_id)
    total = window = None
    if ucode == 200:
        usage = udata.get("usage", {})
        total = usage.get("totalTokens")
        window = usage.get("contextWindowSize")
    result["context"] = {"total": total, "window": window}
    need_compress = False
    if window and total is not None:
        remain_ratio = 1 - (total / window)
        need_compress = remain_ratio < CONTEXT_LOW_RATIO
        result["context"]["remain_ratio"] = round(remain_ratio, 4)
        result["context"]["need_compress"] = need_compress
        log(f"[{role}] ctx 余量 {remain_ratio:.1%} -> {'需压缩' if need_compress else '无需压缩'}")

    # 阶段 3：需要则 /compress
    if need_compress:
        log(f"[{role}] ctx 余量低，发起 /compress")
        pcode, presp = send_prompt(session_id, "/compress")
        result["stages"].append({"step": "compress", "code": pcode, "resp": str(presp)[:200]})
        if pcode not in (200, 202):
            result.update({"ok": False, "failed_step": "compress", "error": f"compress send failed: {presp}"})
            return result
        ok, why = wait_turn_complete(session_id, COMPRESS_TIMEOUT_SECONDS)
        result["stages"].append({"step": "compress_wait", "ok": ok, "why": why})
        if not ok:
            result.update({"ok": False, "failed_step": "compress_wait", "error": why})
            return result

    # 阶段 4：补发「继续完成」
    log(f"[{role}] 补发「继续完成」重启任务")
    kcode, kresp = send_prompt(session_id, CONTINUE_PROMPT)
    result["stages"].append({"step": "continue", "code": kcode, "resp": str(kresp)[:200]})
    ok = kcode in (200, 202)
    result.update({"ok": ok, "failed_step": None if ok else "continue", "error": None if ok else f"{kresp}",
                   "finished_at": now_iso()})
    alert(role, "死循环自愈", f"cancel+{'compress+' if need_compress else ''}continue 完成" if ok else f"恢复失败({kresp})")
    return result


def check_role(role: str, info: dict, mem: dict, args: argparse.Namespace,
               state: dict) -> dict:
    session_id = info.get("session_id")
    name = info.get("name", role)
    if not session_id:
        return mem
    if args.only and role != args.only:
        return mem

    ts = time.time()
    entry = state.setdefault(role, {"name": name, "session_id": session_id, "status": "unknown"})
    entry["checked_at"] = now_iso()

    # 1. 会话存活
    code, st = session_status(session_id)
    if code == 404:
        entry.update({"status": "session_lost"})
        return mem
    if code != 200:
        entry.update({"status": "status_error", "note": str(st)[:200]})
        return mem

    active = st.get("hasActivePrompt", False)
    entry.update({"status": "generating" if active else "idle",
                  "has_active_prompt": active,
                  "has_turn_error": st.get("hasTurnError", False)})

    # 2. 死循环检测：只在会话正在生成时检测（空闲不会空转）
    texts = extract_model_texts(session_id)
    entry["model_msg_count"] = len(texts)
    is_loop = detect_repeat_loop(texts)
    entry["repeat_loop_detected"] = is_loop

    # 命中判定：需正在生成 + 是循环 + 触发条件满足
    if is_loop and active:
        last_trigger = mem.get("last_trigger_at", 0)
        if ts - last_trigger < COOLDOWN_SECONDS:
            entry["status"] = "loop_cooldown"
            return mem
        # 窗口内触发次数限流
        triggers = [t for t in mem.get("trigger_events", []) if ts - t < TRIGGER_WINDOW_SECONDS]
        if len(triggers) >= TRIGGER_LIMIT:
            entry["status"] = "loop_manual"
            alert(role, "死循环且触发达上限", f"最近 {TRIGGER_WINDOW_SECONDS//60}min 触发 {len(triggers)} 次，转人工")
            if not mem.get("intervention_queued"):
                queue_intervention(role, f"死循环自动打断 {TRIGGER_LIMIT} 次未恢复")
                mem["intervention_queued"] = True
            return mem
        # 执行恢复
        mem["last_trigger_at"] = ts
        mem["trigger_events"] = triggers + [ts]
        log(f"[{role}] 死循环命中（连续 {REPEAT_WINDOW} 条重复），启动恢复")
        result = do_recover(role, session_id, args.dry_run)
        entry["last_recovery"] = result
        if result.get("ok"):
            entry["status"] = "recovered"
            mem["intervention_queued"] = False
        else:
            entry["status"] = "recover_failed"
            alert(role, "死循环恢复失败", f"step={result.get('failed_step')} err={result.get('error')}")
    elif is_loop:
        entry["status"] = "loop_idle"  # 命中但会话空闲，暂不打断（等生成时再处理）
    return mem


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="daemon 版死循环监督 watchdog v1")
    ap.add_argument("--interval", type=float, default=10.0, help="检测周期（秒）")
    ap.add_argument("--once", action="store_true", help="只跑一个周期（调试）")
    ap.add_argument("--dry-run", action="store_true", help="只检测，不执行 cancel/compress/prompt")
    ap.add_argument("--only", default=None, help="只监护指定角色 id（调试）")
    ap.add_argument("--similarity-threshold", type=float, default=SIMILARITY_THRESHOLD,
                    help=f"重复判定相似度阈值（默认 {SIMILARITY_THRESHOLD}）")
    ap.add_argument("--repeat-window", type=int, default=REPEAT_WINDOW,
                    help=f"连续重复窗口条数（默认 {REPEAT_WINDOW}）")
    ap.add_argument("--context-low-ratio", type=float, default=CONTEXT_LOW_RATIO,
                    help=f"ctx 余量低于此值需 /compress（默认 {CONTEXT_LOW_RATIO}）")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    log(f"loop-watchdog 启动 interval={args.interval}s dry_run={args.dry_run} "
        f"threshold={args.similarity_threshold} window={args.repeat_window} "
        f"ctx_low_ratio={args.context_low_ratio} only={args.only}")
    while True:
        ts = time.time()
        registry = read_json(REGISTRY, {})
        roles = registry.get("roles", {})
        state = read_json(STATE, {})
        if not isinstance(state, dict):
            state = {}
        memories: dict[str, dict] = state.pop("_memories", {})
        if not isinstance(memories, dict):
            memories = {}
        for role, info in roles.items():
            try:
                memories[role] = check_role(role, info, memories.get(role, {}), args, state)
            except Exception as exc:
                log(f"[{role}] 检测异常: {type(exc).__name__}: {exc}")
        state["_memories"] = memories
        state["_heartbeat"] = {"updated_at": now_iso(), "daemon_url": DAEMON_URL,
                               "roles_checked": len(roles), "dry_run": args.dry_run}
        STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
        if args.once:
            break
        time.sleep(args.interval)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

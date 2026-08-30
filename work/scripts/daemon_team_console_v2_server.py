#!/usr/bin/env python3
"""daemon team console v2 的本地只读控制面与显式确认消息网关。

仅使用 Python 标准库。默认绑定 127.0.0.1:8466；v2 审计独立写入
.team/daemon_v2/messages.jsonl，绝不写入旧 TUI/v1 日志。
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import threading
import re
import shlex
import subprocess
import time
import uuid
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, Mapping, Optional
from urllib.parse import parse_qs, quote, unquote, urlparse
from urllib.request import Request, urlopen

from daemon_auth_v1 import auth_headers, load_token

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DAEMON_URL = "http://127.0.0.1:4194"
ROLE_RE = re.compile(r"@([A-Za-z0-9_-]+)")
SENSITIVE_RE = re.compile(r"(?i)(bearer\s+|api[_-]?key\s*[=:]\s*|token\s*[=:]\s*|password\s*[=:]\s*)[^\s,;]+")

# ---------------- API 用量追踪（可配置常量） ----------------
# DeepSeek 官方 off-peak 参考价（单位：USD 或 CNY / 1M tokens，高峰时段为 off-peak 的 2 倍）。
# 价格来源：DeepSeek 官网 https://api-docs.deepseek.com/quick_start/pricing（英文页 USD）与
# https://api-docs.deepseek.com/zh-cn/quick_start/pricing（中文页 CNY），检索日期 2026-08-19。
# 模型版本：deepseek-v4-flash=DeepSeek-V4-Flash-0731，deepseek-v4-pro=DeepSeek-V4-Pro-0813。
# 高峰时段：北京时间 09:00-12:00 / 14:00-18:00（即 UTC 01:00-04:00 / 06:00-10:00），
#           其余为空闲时段（off-peak）。面板只用于估算，不作为计费依据。
# 更新方式：无公开价格 JSON API，改价时人工更新下方两个常量表并同步 PRICE_UPDATE_DATE。
PRICE_SOURCE = "DeepSeek 官网 api-docs.deepseek.com/quick_start/pricing（官方价格页）"
PRICE_UPDATE_DATE = "2026-08-19"
DS_PRICE_USD: dict[str, dict[str, float]] = {
    "deepseek-v4-flash": {"input_cache_hit": 0.007, "input_cache_miss": 0.22, "output": 0.66},
    "deepseek-v4-pro": {"input_cache_hit": 0.022, "input_cache_miss": 0.66, "output": 1.98},
}
DS_PRICE_CNY: dict[str, dict[str, float]] = {
    "deepseek-v4-flash": {"input_cache_hit": 0.05, "input_cache_miss": 1.5, "output": 4.5},
    "deepseek-v4-pro": {"input_cache_hit": 0.15, "input_cache_miss": 4.5, "output": 13.5},
}
DS_PEAK_MULTIPLIER = 2.0    # 高峰时段价格 = off-peak × 2（DeepSeek 官方规则）
USD_CNY_RATE = 6.79         # 汇率：PBOC 中间价 2026-08-19 为 6.7905；Google Finance 即期 6.7433（同日）。用于 USD↔CNY 对照展示；CNY 费用直接按官方 CNY 价表计算
USAGE_CACHE_TTL = 30        # api-usage 端点内存缓存秒数（daemon 侧 dashboard 已自带 60s 缓存）

# ---------------- 工作状态判定常量 ----------------
WORK_STATE_CACHE_TTL = 10.0     # work_states 判定结果内存缓存秒数（避免前端轮询反复压 daemon）
STALL_THRESHOLD_SECONDS = 300   # running prompt 排队超过该秒数仍未完成 → 判定 stalled（本地模型 prefill 通常 < 120s）

# ---------------- SSE 实时活动监控常量（方案D：真实活动判定工作状态） ----------------
SSE_CHUNK_FRESH_SECONDS = 60.0  # chunk 事件（thought/message）距今 < 该秒数 → 判定 generating（正在生成）
SSE_RECONNECT_DELAY = 5.0       # SSE 断连后重连等待秒数
SSE_MONITOR_SCAN_INTERVAL = 10.0  # 监控主循环扫描成员/补线程的周期秒数

# ---------------- subagent / side task 追踪常量 ----------------
SUBAGENT_STALE_SECONDS = 600.0  # meta 状态非终态但 last_updated 距今超过该秒数 → 标记 stale（疑似已死）
SUBAGENT_TERMINAL_STATUSES = {"completed", "cancelled", "failed"}  # 终态：不再视为活跃 subagent
# 本地模型前缀兜底：当 team_topology.json 注册表不可读时，仍能识别这些家族前缀为本地模型。
# 本地模型 = zhuhai vLLM INT4 的 qwen3.8-27b 系列（含 -zhuhai / -int4-tp2-* / -int4-tp1-* 别名）。
# 注意：主判定是动态读注册表 local_model_services.services[].aliases（唯一事实源，可随新服务自动扩展），
# 本前缀仅供注册表不可读时兜底；外部 API（gpt-5.x 走 11435 转发、deepseek 直连）永远不显示。
LOCAL_MODEL_PREFIXES = ("qwen3.8-27b", "Qwen3.8-27B", "qwen3-vl", "Qwen3.6-27B-Coder")

_LOCAL_MODEL_ALIASES_CACHE: dict[str, Any] = {"ts": 0.0, "val": []}
LOCAL_MODEL_ALIASES_TTL = 60.0  # 本地模型别名集缓存秒数（topology 很少变）


def load_local_model_aliases() -> tuple[str, ...]:
    """从 team_topology.json 的 local_model_services.services 读本地模型别名集（唯一事实源）。

    返回每个 service 的 aliases + id（去重）。这样新增本地服务只需更新注册表，
    subagent 本地模型判定即自动生效，无需改代码。带 60s 缓存。
    """
    now = time.time()
    if now - _LOCAL_MODEL_ALIASES_CACHE["ts"] < LOCAL_MODEL_ALIASES_TTL:
        return tuple(_LOCAL_MODEL_ALIASES_CACHE["val"])
    aliases: set[str] = set()
    try:
        topo = json.loads(Path("/data/WYC/signLanguage/.team/team_topology.json").read_text(encoding="utf-8"))
        for svc in topo.get("local_model_services", {}).get("services", []):
            for a in svc.get("aliases", []) or []:
                base = str(a).split("（")[0].split("(")[0].strip()
                if base:
                    aliases.add(base)
            if svc.get("id"):
                aliases.add(str(svc["id"]))
    except (OSError, ValueError):
        pass
    _LOCAL_MODEL_ALIASES_CACHE["ts"] = now
    _LOCAL_MODEL_ALIASES_CACHE["val"] = sorted(aliases)
    return tuple(_LOCAL_MODEL_ALIASES_CACHE["val"])

# ---------------- 实时 GPU 抓取常量 ----------------
GPU_LIVE_CACHE_TTL = 5.0        # gpu_live 结果内存缓存秒数（前端 5s 轮询，需保持 ≤5s 才准确实时）
GPU_SSH_TIMEOUT = 6.0           # SSH nvidia-smi 单次超时秒数
MODEL_CACHE_TTL = 30.0          # 成员当前模型 id 缓存秒数（避免每 5s 对 11 个成员逐个查 daemon context）
GPU_HOST = os.environ.get("DAEMON_V2_GPU_HOST", "zhuhai")


def load_local_model_gpu_map() -> dict[str, list[int]]:
    """从 team_topology.json 的 local_model_services 自动构建 模型名→GPU 卡 映射。

    事实源：team_topology.json（唯一权威）。aliases 形如
    "qwen3.8-27b-q4-lite（GPU9/8029）" / "qwen3.8-27b-q4-tp2（...GPU5+6...）"，
    解析括号内的 GPU 卡号（支持 "GPU9"、"GPU5+6"、"GPU7+8" 与区间写法）。
    动态实例（tp2-e/tp4/auto/tp2-x/tp4-x 等自动选卡）解析不到固定卡 → 标记动态，
    由运行时探测兜底（见 _gpu_snapshot_live 的进程→GPU 关联）。
    """
    topo = {}
    try:
        topo = json.loads(Path("/data/WYC/signLanguage/.team/team_topology.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        topo = {}
    services = topo.get("local_model_services", {}).get("services", [])
    result: dict[str, list[int]] = {}
    gpu_re = re.compile(r"GPU\s*([0-9+\-\s,]+)")
    for svc in services:
        gpus_cfg = svc.get("gpus")
        fixed: Optional[list[int]] = None
        if isinstance(gpus_cfg, list) and gpus_cfg and all(isinstance(x, int) for x in gpus_cfg):
            fixed = [int(x) for x in gpus_cfg]
        for alias in svc.get("aliases", []) or []:
            base = str(alias).split("（")[0].split("(")[0].strip()
            if not base:
                continue
            m = gpu_re.search(str(alias))
            if m and fixed is None:
                nums = [int(x) for x in re.findall(r"\d+", m.group(1))]
                fixed = nums or None
            if fixed:
                result[base] = fixed
    return result


# zhuhai 本地模型服务 → GPU 卡映射（硬编码兜底；优先使用 team_topology.json 自动加载）。
# 注意弹性单卡：lite=GPU9/8029、lite2=GPU0/8030、lite3=GPU2/8031、lite4=GPU3/8032、lite5=GPU4/8033
# （2026-08-26 核实：曾把 lite/lite2 卡号写反导致调研/本地B 显示错卡）。
LOCAL_MODEL_GPU_MAP_FALLBACK: dict[str, list[int]] = {
    # 弹性单卡 liteN 系列
    "qwen3.8-27b-q4-lite": [9],
    "qwen3.8-27b-q4-lite2": [0],
    "qwen3.8-27b-q4-lite3": [2],
    "qwen3.8-27b-q4-lite4": [3],
    "qwen3.8-27b-q4-lite5": [4],
    # 兼容 gpuN 命名（部分历史配置/别名）
    "qwen3.8-27b-q4-gpu9": [9],
    "qwen3.8-27b-q4-gpu0": [0],
    "qwen3.8-27b-q4-gpu2": [2],
    "qwen3.8-27b-q4-gpu3": [3],
    "qwen3.8-27b-q4-gpu4": [4],
    # 2026-08-26 扩展 GPU5-8 单卡弹性槽（本地A/B 停机时可用）
    "qwen3.8-27b-q4-gpu5": [5],
    "qwen3.8-27b-q4-gpu6": [6],
    "qwen3.8-27b-q4-gpu7": [7],
    "qwen3.8-27b-q4-gpu8": [8],
    "qwen3.8-27b-q4-lite-pool": [0, 2, 3, 4, 9],
    "qwen3.8-27b-q4-tp2": [5, 6],
    "qwen3.8-27b-q4-b-tp2": [7, 8],
    "qwen3.8-27b-q4-tp2-e": [5, 6, 7, 8],
    "qwen3.8-27b-q4-tp4": [0, 1, 2, 3],
    "qwen3.8-27b-q4-auto": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    "qwen3.8-27b-q4-tp2-x": [5, 6],
    "qwen3.8-27b-q4-tp4-x": [0, 1, 2, 3],
    "qwen3-vl-8b": [9],
}

# 自动加载 + 硬编码兜底合并（team_topology 优先）
LOCAL_MODEL_GPU_MAP: dict[str, list[int]] = load_local_model_gpu_map()
LOCAL_MODEL_GPU_MAP.update(LOCAL_MODEL_GPU_MAP_FALLBACK)

# ---------------- 用户在线判定（可配置常量） ----------------
USER_ONLINE_WINDOW_SECONDS = 600    # 用户最近活动判定窗口：10 分钟内有过活动 → 在线
USER_ONLINE_CACHE_TTL = 10.0        # user_online 计算缓存秒数（daemon 探测成功时）
USER_ONLINE_NEG_CACHE_TTL = 30.0    # daemon 探测失败时的负缓存秒数（避免反复超时探测）

# ---------------- 分时（hourly）用量追踪（可配置常量） ----------------
# 数据源：各成员 session chat 文件（chats/*.jsonl）中 subtype=ui_telemetry 且
# event.name=qwen-code.api_response 的事件（含精确时间戳与 input/output/cached/thoughts
# token 计数）。按小时桶聚合，费用按 DeepSeek 官方分时价（peak=全价，off-peak=半价）计算。
# 官方分时定义（2026-08-19 官网）：高峰时段 = 北京时间 9:00-12:00、14:00-18:00
# （即 UTC 01:00-04:00、06:00-10:00），其余为空闲时段；空闲时段价格为高峰时段价格的一半。
CHATS_DIR = Path(os.environ.get("DAEMON_V2_CHATS_DIR",
                                "/home/wuyangcheng/.qwen/projects/-data-WYC-signLanguage/chats"))
HOURLY_KEEP_HOURS = 96          # 保留小时桶数量（4 天，覆盖最近 24h + 今日/昨日对比）
LOCAL_TZ_OFFSET = dt.timedelta(hours=8)   # 北京时间 = UTC+8
DS_PEAK_USD: dict[str, dict[str, float]] = {
    m: {k: v * DS_PEAK_MULTIPLIER for k, v in p.items()} for m, p in DS_PRICE_USD.items()}
DS_PEAK_CNY: dict[str, dict[str, float]] = {
    m: {k: v * DS_PEAK_MULTIPLIER for k, v in p.items()} for m, p in DS_PRICE_CNY.items()}


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError, TypeError):
        return default


def preview(text: str, limit: int = 240) -> str:
    """保存可审计但不含凭据的短摘要。"""
    value = SENSITIVE_RE.sub(r"\1[REDACTED]", str(text)).replace("\x00", "")
    return value[:limit]


def text_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()


def parse_mentions(text: str) -> tuple[list[str], str]:
    mentions = list(dict.fromkeys(m.group(1) for m in ROLE_RE.finditer(text)))
    return mentions, ROLE_RE.sub("", text).strip()


class V2State:
    """文件聚合、registry 核验和可注入 daemon HTTP 客户端。"""

    def __init__(self, root: Path = ROOT, daemon_url: Optional[str] = None,
                 http_get: Optional[Callable[[str], Any]] = None,
                 http_post: Optional[Callable[[str, Mapping[str, Any]], Any]] = None,
                 http_stream: Optional[Callable[[str, Mapping[str, str]], Any]] = None,
                 stale_seconds: int = 86400, current_session_id: Optional[str] = None):
        """初始化 v2 状态；HTTP 依赖可注入，便于完全离线测试。"""
        self.root = Path(root)
        self.v1 = self.root / ".team" / "daemon_v1"
        self.v2 = self.root / ".team" / "daemon_v2"
        self.registry_path = self.v1 / "registry.json"
        self.dashboard_path = self.v1 / "dashboard_data.json"
        self.manifest_path = self.root / ".team" / "daemon_migration_4194_manifest.json"
        self.groups_path = self.v2 / "groups.json"
        self.audit_path = self.v2 / "messages.jsonl"
        self.daemon_url = daemon_url or os.environ.get("DAEMON_V2_DAEMON_URL", DEFAULT_DAEMON_URL)
        self.http_get = http_get or self._http_get
        self.http_post = http_post or self._http_post_json
        self.http_stream = http_stream or self._http_stream
        self.stale_seconds = stale_seconds
        self.current_session_id = current_session_id
        self._lock = threading.Lock()
        # API 用量追踪的短 TTL 内存缓存（避免前端轮询时反复压 daemon）
        self._usage_cache: Optional[dict[str, Any]] = None
        self._usage_cache_ts = 0.0
        self._usage_cache_ttl = 0.0
        self._usage_lock = threading.Lock()
        self._dsv4_cache: Optional[dict[str, Any]] = None
        # 用户在线判定的短 TTL 内存缓存（含负缓存：daemon 探测失败时不反复超时探测）
        self._user_online_cache: Optional[dict[str, Any]] = None
        self._user_online_ts = 0.0
        # 工作状态判定的短 TTL 内存缓存
        self._work_state_cache: Optional[dict[str, Any]] = None
        self._work_state_cache_ts = 0.0
        # SSE 实时活动监控（方案D）：每个成员 session 一个监控线程，跟踪
        # last_event_ts / last_chunk_ts / open_tools，用于按真实活动判定工作状态。
        # 结构：sid -> {"last_event_ts": float, "last_chunk_ts": float,
        #               "last_event_kind": str, "open_tools": {toolCallId: {...}},
        #               "sse_connected": bool, "sse_error": str}
        self._sse_activity: dict[str, dict[str, Any]] = {}
        self._sse_lock = threading.Lock()
        self._sse_monitor_threads: dict[str, threading.Thread] = {}
        self._sse_monitor_started = False
        # 实时 GPU 抓取的短 TTL 内存缓存
        self._gpu_live_cache: Optional[dict[str, Any]] = None
        self._gpu_live_cache_ts = 0.0
        self._gpu_live_refreshing = False          # stale-while-revalidate 后台刷新标记
        self._host_res_cache: Optional[dict[str, Any]] = None
        self._host_res_cache_ts = 0.0
        self._host_res_refreshing = False
        # local_services（services/health）stale-while-revalidate 缓存
        self._local_svc_cache: Optional[dict[str, Any]] = None
        self._local_svc_cache_ts = 0.0
        self._local_svc_refreshing = False
        # 弹性实例端口探测的短 TTL 内存缓存
        self._elastic_cache: Optional[dict[str, str]] = None
        self._elastic_cache_ts = 0.0
        # 弹性实例速率探测的短 TTL 内存缓存
        self._elastic_rates_cache: Optional[dict[str, dict[str, float]]] = None
        self._elastic_rates_cache_ts = 0.0
        # 成员当前模型 id 缓存（session_id -> (model, ts)），失败回退用
        self._model_cache: dict[str, tuple[str, float]] = {}
        # 分时（hourly）用量追踪器（懒加载；复用 _usage_lock 串行化刷新）
        self._hourly_tracker: Optional[HourlyTracker] = None

    def _http_get(self, path: str) -> Any:
        req = Request(self.daemon_url.rstrip("/") + path, headers=auth_headers({"Accept": "application/json"}))
        with urlopen(req, timeout=2.0) as response:
            return json.loads(response.read().decode("utf-8"))

    def registry(self) -> dict[str, Any]:
        return load_json(self.registry_path, {"roles": {}})

    def manifest(self) -> dict[str, Any]:
        return load_json(self.manifest_path, {})

    def groups(self) -> list[dict[str, Any]]:
        value = load_json(self.groups_path, {"groups": []})
        return value.get("groups", []) if isinstance(value, dict) else []

    # ---------------- 本地数据源层（只读；全部读 .team/daemon_v1 已落盘文件，绝不访问 daemon） ----------------

    def _tail_lines(self, path: Path, max_lines: int) -> list[str]:
        """流式读取文件末尾最多 max_lines 行；文件缺失/不可读时返回空列表。

        [20260827] 修复：原实现 `deque(fh, maxlen)` 从文件头全量遍历——inbox/events 累积
        数 GB 时每次调用完整读文件（超时 + 100% CPU，看板乱跳根因）。
        改为从文件尾部倒读，只读末尾约 max_lines 行（O(尾行数)，与文件总长无关）。
        """
        if max_lines <= 0:
            return []
        try:
            with path.open("rb") as fh:
                fh.seek(0, 2)
                size = fh.tell()
                if size == 0:
                    return []
                lines: list[bytes] = []
                pos = size
                block = 8192
                remaining = max_lines
                buf = b""
                while pos > 0 and remaining > 0:
                    read_len = min(block, pos)
                    pos -= read_len
                    fh.seek(pos)
                    chunk = fh.read(read_len)
                    buf = chunk + buf
                    # 已读满 2×max_lines 行字节仍不足时提前止损（防畸形大行）
                    if buf.count(b"\n") >= remaining * 2 + 1:
                        break
                lines = buf.split(b"\n")
                lines = [ln for ln in lines if ln != b""]
                tail = lines[-remaining:]
                return [ln.decode("utf-8", errors="replace") for ln in tail]
        except OSError:
            return []

    def local_status(self) -> dict[str, Any]:
        """读 message_supervisor.json（supervisor 聚合快照），返回成员与升级事件。"""
        value = load_json(self.v1 / "message_supervisor.json", None)
        if not isinstance(value, dict) or "members" not in value:
            return {"ok": False, "source": "local", "error": "message_supervisor.json missing or invalid"}
        members = value.get("members")
        escalations = value.get("escalations", [])
        return {"ok": True, "source": "local", "generated_at": value.get("generated_at"),
                "members": members if isinstance(members, list) else [],
                "escalations": escalations if isinstance(escalations, list) else []}

    # ---------------- 用户在线判定（daemon 可达 + 用户最近活动） ----------------

    @staticmethod
    def _parse_dt(value: Any) -> Optional[dt.datetime]:
        """解析 daemon/registry 的 ISO 时间戳（容忍 Z 后缀与 +HHMM 无冒号格式）。

        Python 3.10 的 fromisoformat 要求时区形如 +08:00（带冒号），而 registry
        的 generated_at 形如 +0800（无冒号），这里统一兼容；无时区按 UTC 处理。
        """
        if not value:
            return None
        text = str(value)
        try:
            if text.endswith("Z"):
                return dt.datetime.fromisoformat(text[:-1] + "+00:00")
            if re.search(r"[+-]\d{4}$", text):
                text = text[:-2] + ":" + text[-2:]
            parsed = dt.datetime.fromisoformat(text)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=dt.timezone.utc)
            return parsed
        except ValueError:
            return None

    def _user_sessions(self) -> list[dict[str, Any]]:
        """registry unassigned_sessions 中属于用户的会话（排除团队 side_task 子任务会话）。

        用户（Owner）会话特征：sourceType 为 default（终端直接创建）或 channel（如微信渠道），
        以及迁移早期无 sourceType 的旧会话；side_task 是团队角色 fork 出的子任务，不算用户活动。
        """
        out: list[dict[str, Any]] = []
        for s in self.registry().get("unassigned_sessions") or []:
            if not isinstance(s, dict):
                continue
            if s.get("sourceType") == "side_task":
                continue
            out.append(s)
        return out

    def user_online_status(self) -> dict[str, Any]:
        """判定用户（Owner）在线状态：daemon 可达 且 用户最近有活动 → online。

        规则：
        - daemon 可达：实时探测 /daemon/status（单次、2s 超时，见 _http_get）；
          探测失败时回退 registry 新鲜度——refresher 每 5s 重写 registry，
          daemon 不可达时 registry 会变陈旧（generated_at 超过 30s 且非 ok）。
        - 用户最近活动：registry unassigned_sessions 中用户会话（非 side_task）的
          最近 updatedAt 在 USER_ONLINE_WINDOW_SECONDS 内，或该会话 hasActivePrompt。
        结果带短 TTL 缓存；daemon 探测失败时用更长的负缓存，避免反复超时探测拖慢 /api/local/status。
        """
        import time as _time
        now = _time.time()
        with self._usage_lock:
            cached = self._user_online_cache
            if cached is not None and now - self._user_online_ts < cached.get("_ttl", 0.0):
                return {k: v for k, v in cached.items() if not k.startswith("_")}
        # 1) daemon 可达性：实时探测（http_get 已注入/2s 超时）
        daemon_up = False
        daemon_status_value: Optional[str] = None
        active_sessions: Optional[int] = None
        probe_error: Optional[str] = None
        try:
            st = self.http_get("/daemon/status")
            if isinstance(st, dict):
                daemon_up = True
                daemon_status_value = st.get("status")
                runtime = st.get("runtime") or {}
                active_sessions = (runtime.get("sessions") or {}).get("active")
        except Exception as exc:
            probe_error = type(exc).__name__
        if not daemon_up:
            # 回退：registry 新鲜度（refresher 每 5s 重写；daemon 不可达则陈旧）
            reg = self.registry()
            gen = self._parse_dt(reg.get("generated_at"))
            if gen is not None:
                age = (dt.datetime.now(dt.timezone.utc) - gen).total_seconds()
                if 0 <= age <= 30.0 and (reg.get("daemon_status") or {}).get("status") == "ok":
                    daemon_up = True
        # 2) 用户最近活动
        has_active_prompt = False
        latest_ts: Optional[dt.datetime] = None
        latest_raw: Optional[str] = None
        for s in self._user_sessions():
            if s.get("hasActivePrompt"):
                has_active_prompt = True
            stamp = s.get("updatedAt") or s.get("updated_at")
            ts = self._parse_dt(stamp)
            if ts is None:
                continue
            if latest_ts is None or ts > latest_ts:
                latest_ts, latest_raw = ts, stamp
        active_within = (latest_ts is not None
                         and (dt.datetime.now(dt.timezone.utc) - latest_ts).total_seconds()
                         <= USER_ONLINE_WINDOW_SECONDS)
        online = daemon_up and (has_active_prompt or active_within)
        result = {
            "online": online,
            "daemon_up": daemon_up,
            "daemon_status": daemon_status_value,
            "user_active": bool(has_active_prompt or active_within),
            "last_user_activity": latest_raw,
            "activity_window_seconds": USER_ONLINE_WINDOW_SECONDS,
            "has_active_prompt": has_active_prompt,
            "active_sessions": active_sessions,
            "probe_error": probe_error,
            "checked_at": now_iso(),
            "note": "online = daemon 可达 且 用户（Owner）最近 10 分钟内有过活动（unassigned 用户会话 updatedAt / 活跃 prompt）",
        }
        ttl = USER_ONLINE_CACHE_TTL if daemon_up else USER_ONLINE_NEG_CACHE_TTL
        with self._usage_lock:
            self._user_online_cache = {**result, "_ttl": ttl}
            self._user_online_ts = now
        return result

    def _event_summary(self, row: Mapping[str, Any]) -> str:
        """把 inbox 行转成短的可读摘要（预览脱敏 + 截断）。"""
        ev = row.get("event")
        if not isinstance(ev, dict):
            return ""
        typ = ev.get("type") or ""
        data = ev.get("data")
        if typ == "session_update" and isinstance(data, dict):
            update = data.get("update")
            if isinstance(update, dict):
                su = update.get("sessionUpdate") or ""
                content = update.get("content")
                text = ""
                if isinstance(content, dict):
                    text = content.get("text") or ""
                elif isinstance(content, list):
                    text = "".join((c.get("content") or {}).get("text") or c.get("text") or ""
                                   for c in content if isinstance(c, dict))
                return f"[{su}] {preview(text, 160)}".rstrip()
            return f"[{typ}]"
        if typ == "git_status_changed" and isinstance(data, dict):
            return f"git: branch={data.get('branch')} unstaged={data.get('unstaged')} untracked={data.get('untracked')}"
        known = {"turn_complete": "回合完成", "replay_complete": "事件回放完成",
                 "state_resync_required": "状态需重新同步", "session_died": "session 终止",
                 "approval_mode_changed": "审批模式变更", "settings_changed": "设置变更",
                 "session_metadata_updated": "会话元数据更新", "git_status_changed": "git 状态变更"}
        return known.get(typ, typ or "event")

    def local_messages(self, per_member: int = 20, tail_lines: int = 400) -> dict[str, Any]:
        """聚合 members/*/inbox.jsonl：跳过 helper_error 行，每成员最近最多 per_member 条，
        全局按 observed_at 倒序返回。只读本地文件，不访问 daemon。"""
        members_dir = self.v1 / "members"
        if not members_dir.is_dir():
            return {"ok": False, "source": "local", "error": "members directory missing"}
        per_role: dict[str, list[dict[str, Any]]] = {}
        for role_dir in sorted(p for p in members_dir.iterdir() if p.is_dir()):
            inbox = role_dir / "inbox.jsonl"
            if not inbox.exists():
                continue
            rows: list[dict[str, Any]] = []
            for line in self._tail_lines(inbox, tail_lines):
                try:
                    row = json.loads(line)
                except (ValueError, TypeError):
                    continue
                if not isinstance(row, dict) or row.get("kind") == "helper_error" or "event" not in row:
                    continue
                rows.append(row)
            rows.sort(key=lambda r: str(r.get("observed_at", "")), reverse=True)
            per_role[role_dir.name] = rows[:per_member]
        messages: list[dict[str, Any]] = []
        for role, rows in per_role.items():
            for row in rows:
                ev = row.get("event")
                messages.append({
                    "role": row.get("role") or role,
                    "session_id": row.get("session_id"),
                    "status": row.get("status"),
                    "observed_at": row.get("observed_at"),
                    "type": ev.get("type") if isinstance(ev, dict) else None,
                    "text": self._event_summary(row),
                })
        messages.sort(key=lambda m: str(m.get("observed_at", "")), reverse=True)
        return {"ok": True, "source": "local", "messages": messages}

    @staticmethod
    def _chat_text(update: Mapping[str, Any]) -> str:
        """从 sessionUpdate 的 content 中提取文本（dict 或 content-block 数组两种形态）。"""
        content = update.get("content")
        if isinstance(content, dict):
            return content.get("text") or ""
        if isinstance(content, list):
            return "".join((c.get("content") or {}).get("text") or c.get("text") or ""
                           for c in content if isinstance(c, dict))
        return ""

    def _group_chat_events(self, rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
        """把 session_update 事件流按前端 appendEvent 相同的语义分组为 user/assistant/thought/tool。"""
        msgs: list[dict[str, Any]] = []

        def last() -> Optional[dict[str, Any]]:
            return msgs[-1] if msgs else None

        def close_assistant() -> None:
            for m in msgs:
                if m["kind"] == "assistant":
                    m["streaming"] = False
                if m["kind"] == "user":
                    m["queued"] = False

        for row in rows:
            ev = row.get("event")
            if not isinstance(ev, dict) or ev.get("type") != "session_update":
                continue
            data = ev.get("data")
            if not isinstance(data, dict):
                continue
            update = data.get("update")
            if not isinstance(update, dict):
                continue
            su = update.get("sessionUpdate")
            text = self._chat_text(update)
            if su in ("user_message_chunk", "user_message_start", "user_message_end"):
                if su == "user_message_end":
                    continue
                close_assistant()
                if last() and last()["kind"] == "user":
                    last()["text"] += text
                else:
                    msgs.append({"kind": "user", "text": text})
            elif su in ("agent_message_chunk", "agent_message_start"):
                if last() and last()["kind"] == "assistant":
                    last()["text"] += text
                else:
                    close_assistant()
                    msgs.append({"kind": "assistant", "text": text, "streaming": True})
            elif su == "agent_message_end":
                if last() and last()["kind"] == "assistant":
                    last()["streaming"] = False
            elif su == "agent_thought_chunk":
                if last() and last()["kind"] == "thought":
                    last()["text"] += text
                else:
                    close_assistant()
                    msgs.append({"kind": "thought", "text": text})
            elif su == "tool_call":
                if last() and last()["kind"] == "assistant":
                    last()["streaming"] = False
                meta = update.get("_meta") or {}
                msgs.append({"kind": "tool", "toolCallId": update.get("toolCallId"),
                             "title": update.get("title") or meta.get("toolName") or "tool",
                             "status": update.get("status") or "in_progress", "text": ""})
            elif su == "tool_call_update":
                m = next((m for m in msgs if m["kind"] == "tool"
                          and m.get("toolCallId") == update.get("toolCallId")), None)
                if m:
                    m["status"] = update.get("status") or m["status"]
                    if text:
                        m["text"] = text
        return msgs

    def local_chat(self, role: str, max_events: int = 200) -> dict[str, Any]:
        """读该成员 events.jsonl，把最近 max_events 条 session_update 事件分组为可渲染对话消息。"""
        if not role:
            return {"ok": False, "source": "local", "role": role, "error": "role is required"}
        events_path = self.v1 / "members" / role / "events.jsonl"
        if not events_path.exists():
            return {"ok": False, "source": "local", "role": role, "error": "events.jsonl missing"}
        rows: list[dict[str, Any]] = []
        for line in self._tail_lines(events_path, max_events):
            try:
                row = json.loads(line)
            except (ValueError, TypeError):
                continue
            if isinstance(row, dict):
                rows.append(row)
        return {"ok": True, "source": "local", "role": role,
                "events_parsed": len(rows), "messages": self._group_chat_events(rows)}

    def dashboard(self) -> dict[str, Any]:
        value = load_json(self.dashboard_path, {})
        return value if isinstance(value, dict) else {}

    def _elastic_ports_from_topology(self) -> list[str]:
        """从 team_topology.json 读弹性服务端口（type=elastic），动态适配槽位变化。"""
        try:
            topo = json.loads(Path("/data/WYC/signLanguage/.team/team_topology.json").read_text(encoding="utf-8"))
            return [str(s["port"]) for s in topo.get("local_model_services", {}).get("services", [])
                    if s.get("type") == "elastic" and str(s.get("port", "")).isdigit()]
        except (OSError, ValueError):
            return ["8051", "8052", "8053", "8054"]

    def _elastic_port_id_map(self) -> dict[str, str]:
        """从 team_topology.json 读弹性服务 {端口: 服务id}（如 {"8054": "int4-tp2-g29"}）。

        用于把巡检/8096 的纯端口数据关联到规范服务 id（模型 id），
        实例刚拉起、巡检（2min 间隔）尚未覆盖时也能补出带正确 id 的卡片。
        """
        try:
            topo = json.loads(Path("/data/WYC/signLanguage/.team/team_topology.json").read_text(encoding="utf-8"))
            out: dict[str, str] = {}
            for s in topo.get("local_model_services", {}).get("services", []):
                if s.get("type") == "elastic" and str(s.get("port", "")).isdigit():
                    out[str(s["port"])] = s.get("id", "")
            return out
        except (OSError, ValueError):
            return {}

    def _active_elastic_services(self) -> dict[str, str]:
        """SSH 探测 zhuhai 上当前活跃的弹性实例端口（从 topology 动态读），返回 {port: UP}。

        巡检 v2 每 2 分钟落盘一次状态；看板这里每轮实时补探测（TTL 缓存），
        让「按需拉起」的实例尽快出现在面板。弹性实例 DOWN 属正常（按需启动）。
        """
        now = time.time()
        with self._lock:
            if (self._elastic_cache is not None
                    and now - self._elastic_cache_ts < GPU_LIVE_CACHE_TTL):
                return self._elastic_cache
        ports = self._elastic_ports_from_topology()
        result: dict[str, str] = {}
        if ports:
            # [20260827] 改用本机 SSH 隧道探测（127.0.0.1:180xx → zhuhai 80xx）：
            # 原实现每次 SSH zhuhai 执行 /dev/tcp 探测（约 2-4s/次），前端轮询
            # 高频触发导致 SSH 线程堆积 + 看板接口超时/100% CPU。隧道在本机常开，
            # 本地 health 探测毫秒级，且不占用 zhuhai sshd 连接。
            for p in ports:
                if not p.isdigit():
                    continue
                tunnel = 18000 + int(p)
                up = False
                try:
                    with urllib.request.urlopen(
                            f"http://127.0.0.1:{tunnel}/health", timeout=1.5) as r:
                        up = r.status == 200
                except (urllib.error.URLError, urllib.error.HTTPError, OSError):
                    up = False
                result[p] = "UP" if up else "DOWN"
        with self._lock:
            self._elastic_cache = result
            self._elastic_cache_ts = time.time()
        return result

    def _elastic_rates_live(self, ports: list[str]) -> dict[str, dict[str, float]]:
        """从 zhuhai 8096 监控 API 拉活跃弹性实例的最近 decode/prefill（vLLM /metrics 差分）。

        8096 为 vLLM 实例速率监控（/metrics 每秒差分），通过 18096 隧道访问；按实例端口关联。
        """
        if not ports:
            return {}
        now = time.time()
        with self._lock:
            if (self._elastic_rates_cache is not None
                    and now - self._elastic_rates_cache_ts < GPU_LIVE_CACHE_TTL):
                return self._elastic_rates_cache
        result: dict[str, dict[str, float]] = {}
        try:
            with urlopen("http://127.0.0.1:18096/api", timeout=4) as r:
                data = json.loads(r.read().decode())
            for m in data if isinstance(data, list) else []:
                if not m.get("alive"):
                    continue
                port = str(m.get("port") or "")
                if port not in ports:
                    continue
                d = (m.get("decode") or {}).get("last_rate")
                p = (m.get("prefill_last") or {}).get("tps")
                result[port] = {
                    "decode": float(d) if d is not None else None,
                    "prefill": float(p) if p is not None else None,
                }
        except Exception as exc:
            result["_error"] = f"{type(exc).__name__}: {exc}"
        with self._lock:
            self._elastic_rates_cache = result
            self._elastic_rates_cache_ts = time.time()
        return result

    def _llama_auto_discover(self) -> tuple[dict[str, str], dict[str, dict[str, float]]]:
        """自动发现 zhuhai 上活跃的 llama.cpp 服务并补入看板卡片 + 速率。

        8096 监控（llm_monitor_generic_v2）本身就自动发现 llama-server 并测 P/D 速率
        （PROC_PATTERNS 含 "llama-server"，_scan_llama 解析日志），只是看板消费端
        只认 topology 的 elastic/vllm 服务。这里直接拉 8096 /api，把 source=="llama"
        且 alive 的实例补出来，键名 "端口(llama-模型id)"，速率挂 decode/prefill。
        不改 topology / 巡检脚本；任何 llama-server 一在 zhuhai 跑起来即自动显示。

        返回 (services 增量, rates 增量)。
        """
        services_inc: dict[str, str] = {}
        rates_inc: dict[str, dict[str, float]] = {}
        try:
            with urlopen("http://127.0.0.1:18096/api", timeout=4) as r:
                data = json.loads(r.read().decode())
            for m in data if isinstance(data, list) else []:
                if not m.get("alive"):
                    continue
                if m.get("source") != "llama":
                    continue
                port = str(m.get("port") or "").strip()
                mid = str(m.get("model_id") or "llama").strip()
                if not port or not port.isdigit():
                    continue
                key = f"{port}(llama-{mid})"
                services_inc[key] = "UP(llama)"
                d = (m.get("decode") or {}).get("last_rate")
                p = (m.get("prefill_last") or {}).get("tps")
                rates_inc[key] = {
                    "decode": float(d) if d is not None else None,
                    "prefill": float(p) if p is not None else None,
                }
        except Exception:
            # 8096 不可用时静默，不影响 vLLM 面板（自动发现是增强而非必需）
            pass
        return services_inc, rates_inc

    def _fetch_local_services(self) -> dict[str, Any]:
        """local_services 数据抓取主体（读巡检文件 + 活跃弹性实例 + 速率），由缓存层调用。

        巡检覆盖弹性槽（8051-8054）+ VL 8000；这里实时补充"当前活跃的弹性实例"
        （本机隧道探测正在监听的端口，TTL 5s），并把 rates 键规范化为
        "端口(服务id)"（如 "8054(int4-tp2-g29)"），与 topology/8096 对齐。
        DOWN 槽位不补卡（前端只显示 UP，属既定要求：按需实例 DOWN 正常）。
        """
        state = load_json(self.v1 / "local_services_health_state.json", {})
        if not isinstance(state, dict) or not state:
            return {"ok": True, "latest": {}, "history": {}, "updated_at": None}
        keys = sorted(state.keys())
        latest = state[keys[-1]] if keys else {}
        # 每实例最近 N 轮速率趋势（decode/prefill 序列）
        history: dict[str, list[dict[str, Any]]] = {}
        for k in keys[-12:]:
            entry = state[k]
            for svc, r in entry.get("rates", {}).items():
                history.setdefault(svc, []).append(dict(r, ts=k))
        # 巡检 services + 实时活跃弹性实例合并
        services = dict(latest.get("services", {}) or {})
        rates = dict(latest.get("rates", {}) or {})
        # 端口 → 服务 id 映射：优先从巡检键 "8054(int4-tp2-g29)" 解析，
        # topology（type=elastic）兜底补全（实例刚拉起、巡检未覆盖时也能拿到 id）
        port_sid: dict[str, str] = {}
        for k in list(services):
            m = re.match(r"^(\d+)\(([^)]+)\)$", str(k))
            if m:
                port_sid.setdefault(m.group(1), m.group(2))
        port_sid.update(self._elastic_port_id_map())
        # rates 键规范化：巡检落盘的纯端口键（"8054"）→ 规范键 "8054(int4-tp2-g29)"，
        # 保证前端用服务键能查到速率；无映射的键保留原样
        for rk in list(rates):
            base = str(rk).split("(")[0].strip()
            if base.isdigit() and base in port_sid:
                canonical = f"{base}({port_sid[base]})"
                if canonical not in rates:
                    rates[canonical] = rates[rk]
                del rates[rk]
        active_elastic: dict[str, str] = {}
        try:
            active_elastic = self._active_elastic_services()
            up_ports = [p for p, s in active_elastic.items() if s == "UP"]
            if up_ports:
                live_rates = self._elastic_rates_live(up_ports)
                for p in up_ports:
                    # 巡检已覆盖该端口（键前缀 端口( 匹配）→ 实时速率挂到既有键，不重复补卡片
                    matched = next((k for k in services if str(k).startswith(p + "(")), None)
                    if matched:
                        if p in live_rates and live_rates[p]:
                            rates[matched] = live_rates[p]
                        continue
                    # 巡检未覆盖（间隔 2min 内刚拉起）→ 用 topology 的 id 补规范键，
                    # 避免产生裸端口键（前端无法反查模型 id 会显示空名坏卡）
                    key = f"{p}({port_sid[p]})" if p in port_sid else f"{p}(弹性)"
                    if key not in services:
                        services[key] = "UP(活跃)"
                    if p in live_rates and live_rates[p]:
                        rates[key] = live_rates[p]
        except Exception:
            pass
        # rates 中出现但 services 缺失的实例也补入（有速率数据 = 实例活着，
        # 如 8036(tp2-x) 巡检只采速率不查状态，会被漏掉）。
        # 但以实时探测为准：探测确认 DOWN 的端口不算 UP（弹性实例可能已空闲自停）；
        # 补卡一律用规范键 "端口(服务id)"，不产生裸端口键（前端无法反查 id）。
        for rk, r in (latest.get("rates", {}) or {}).items():
            base = str(rk).split("(")[0].strip()
            if not base.isdigit() or rk in services or base in port_sid:
                continue
            live = active_elastic.get(base)
            if live == "UP":
                services[f"{base}(弹性)"] = "UP(速率)"
        # llama.cpp 服务自动发现：从 8096 已发现的 llama-server 实例补出卡片+速率，
        # 让 llama 引擎的本地模型也能在看板"本地模型服务"面板测速（无 topology 登记也可）。
        llama_services, llama_rates = self._llama_auto_discover()
        for k, v in llama_services.items():
            services.setdefault(k, v)
        for k, v in llama_rates.items():
            rates.setdefault(k, v)
        latest = dict(latest)
        latest["services"] = services
        latest["rates"] = rates
        # GPU 快照解析为结构化（index, used_mib, util）
        gpu_rows: list[dict[str, Any]] = []
        snap = latest.get("gpu_snapshot", "")
        for part in str(snap).split(";"):
            fields = part.split(",")
            if len(fields) >= 3:
                gpu_rows.append({
                    "gpu": fields[0].strip(),
                    "used_mib": int(fields[1].strip() or 0),
                    "util": int(fields[2].strip() or 0),
                })
        # 角色 → 本地模型 → 实例 → GPU 追踪
        role_usage = self._role_gpu_usage(gpu_rows)
        return {
            "ok": True,
            "latest": latest,
            "history": history,
            "gpu": gpu_rows,
            "role_usage": role_usage,
            "updated_at": keys[-1] if keys else None,
        }

    def local_services(self) -> dict[str, Any]:
        """本地模型服务健康与速率（stale-while-revalidate 缓存，TTL 5s）。

        数据来自巡检文件 + 活跃弹性实例探测；缓存过期时返回旧数据 + stale 标记
        （后台刷新），隧道探测慢/失败不再阻塞接口（services/health 快速响应）。
        """
        return self._cached_swr(
            "_local_svc_cache", "_local_svc_cache_ts", "_local_svc_refreshing",
            GPU_LIVE_CACHE_TTL, self._fetch_local_services,
        )

    def local_services_meta(self) -> dict[str, Any]:
        """本地模型服务元信息：svc_id -> {model, aliases, gpus, type, owner_role, status}
        来自 team_topology.json 的 local_model_services，供前端"说明是什么模型"""
        try:
            topo = json.loads(Path("/data/WYC/signLanguage/.team/team_topology.json").read_text(encoding="utf-8"))
            services = topo.get("local_model_services", {}).get("services", [])
            meta: dict[str, dict[str, Any]] = {}
            for s in services:
                meta[s.get("id", "")] = {
                    "id": s.get("id", ""),
                    "model": s.get("model", ""),
                    "aliases": s.get("aliases", []),
                    "gpus": s.get("gpus"),
                    "port": s.get("port"),
                    "tunnel_port": s.get("tunnel_port"),
                    "type": s.get("type", ""),
                    "owner_role": s.get("owner_role", ""),
                    "status": s.get("status", ""),
                }
            return {"ok": True, "services": meta, "at": dt.datetime.now().isoformat()}
        except Exception as exc:
            return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    def dsV4_status(self) -> dict[str, Any]:
        """dsv4flash 实时性能（代理到 zhuhai 8096 监测服务 /api）

        8096 监测服务返回：{"latest_task":..., "prefill_last":{tokens,t,tps,...},
        "decode":{last_rate,peak_decode,window_n,...}, "gpu":{"9":...}}
        短 TTL 内存缓存，避免每次 8466 轮询都压 8096。
        """
        h = self._dsv4_cache
        now = time.time()
        if h and now - h["at"] < 0.2:
            return h["data"]
        url = "http://127.0.0.1:18096/api"  # natureza SSH 隧道 -> zhuhai 8096 监测服务
        try:
            req = Request(url, headers={"Accept": "application/json"})
            with urlopen(req, timeout=2.0) as resp:
                d = json.loads(resp.read().decode("utf-8"))
            data = {"ok": True, "data": d, "at": dt.datetime.now().isoformat()}
        except Exception as exc:
            data = {"ok": False, "error": f"{type(exc).__name__}: {exc}", "at": dt.datetime.now().isoformat()}
        self._dsv4_cache = {"at": now, "data": data}
        return data

    def _role_gpu_usage(self, gpu_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """各角色当前使用的本地模型服务与 GPU 卡
        角色 model 优先取 dashboard_data.json 的 model 字段（含具体实例名，如
        "qwen3.8-27b-int4-tp2-g29(openai)"），去掉 (openai) 后缀后匹配 topology 别名定位实例与 GPU；
        缺失时回退到 chat jsonl 最近 api_response 泛化名 + 11435 路由日志按时间匹配。"""
        registry = self.registry()
        roles = registry.get("roles", {}) if isinstance(registry, dict) else {}
        # 拓扑：服务 aliases/端口 → (service_id, gpus)
        topo = load_json(self.root / ".team" / "team_topology.json", {})
        services = topo.get("local_model_services", {}).get("services", [])
        alias_map: dict[str, dict[str, Any]] = {}
        port_service: dict[str, dict[str, Any]] = {}
        for s in services:
            for a in s.get("aliases", []) or []:
                # 别名可能带中文注释（如 "qwen3.8-27b-q4-tp2-x（独占双卡/8036...）"），提取纯 id
                base = str(a).split("（")[0].split("(")[0].strip()
                alias_map[base] = s
            alias_map[str(s.get("id", ""))] = s
            p = str(s.get("port", ""))
            if p.isdigit():
                port_service[p] = s
            elif isinstance(p, list):
                for pp in p:
                    port_service[str(pp)] = s
        # 路由日志：[(ts, model, port)]
        routes: list[tuple[int, str, str]] = []
        try:
            for line in open("/home/wuyangcheng/codex-deepseek-proxy/proxy_q4b.log", encoding="utf-8", errors="ignore"):
                if "[route]" not in line:
                    continue
                m = re.search(r"ts=(\d+) model=(\S+) -> http://[^:]+:(\d+)/v1", line)
                if m:
                    routes.append((int(m.group(1)), m.group(2), m.group(3)))
        except Exception:
            pass
        routes.sort()
        gpu_used = {g["gpu"]: g for g in gpu_rows}
        out = []
        for rid, rv in (roles or {}).items():
            sid = rv.get("session_id") or ""
            role_name = rv.get("display_name") or rv.get("name") or rid
            model, ts = self._session_last_model(sid) if sid else ("", 0)
            service = None
            # 1) 精确别名匹配
            if model:
                service = alias_map.get(model)
            # 2) 时间匹配路由日志（±600s 内最近一条；gguf 路径/本地 Q4 走此兜底）
            if not service and ts and routes:
                best = None
                for rt, rmodel, rport in routes:
                    if abs(rt - ts) > 600:
                        continue
                    cand = port_service.get(rport)
                    if cand and (best is None or abs(rt - ts) < abs(best[0] - ts)):
                        best = (rt, cand)
                if best:
                    service = best[1]
            gpus = service.get("gpus") if service else None
            gpu_info = []
            if isinstance(gpus, list):
                for g in gpus:
                    info = gpu_used.get(str(g), {})
                    gpu_info.append({"gpu": str(g), "used_mib": info.get("used_mib"), "util": info.get("util")})
            gpu_label = [str(g) for g in gpus] if isinstance(gpus, list) else (["动态"] if service else [])
            out.append({
                "role": rid,
                "role_name": role_name,
                "model": model or "（未用本地/云端）",
                "service": service.get("id") if service else None,
                "gpus": gpu_label,
                "gpu_info": gpu_info,
            })
        return out

    def _session_last_model(self, session_id: str) -> tuple[str, int]:
        """从会话 jsonl 最近 api_response 提取 model 与 Unix 时间戳"""
        p = CHATS_DIR / f"{session_id}.jsonl"
        try:
            lines = [l for l in open(p, encoding="utf-8").read().split("\n") if l.strip()]
            for l in reversed(lines[-80:]):
                try:
                    d = json.loads(l)
                    ev = d.get("systemPayload", {}).get("uiEvent", {})
                    if ev.get("event.name") != "qwen-code.api_response":
                        continue
                    m = ev.get("model")
                    ts = ev.get("event.timestamp") or d.get("timestamp") or ""
                    if not m:
                        continue
                    ts_unix = 0
                    if ts:
                        try:
                            from datetime import datetime
                            ts_unix = int(datetime.fromisoformat(str(ts).replace("Z", "+00:00")).timestamp())
                        except Exception:
                            ts_unix = 0
                    return str(m), ts_unix
                except Exception:
                    continue
        except Exception:
            pass
        return "", 0

    def members(self) -> list[dict[str, Any]]:
        """优先返回 dashboard_data.json 的 members（含 id/daemon_session_id 等前端字段）；
        缺失时回退到 registry 生成，并补齐 id/daemon_session_id。"""
        dd = self.dashboard()
        ms = dd.get("members")
        if isinstance(ms, list) and ms:
            return ms
        roles = self.registry().get("roles", {})
        result = []
        for role, raw in roles.items():
            item = dict(raw) if isinstance(raw, dict) else {}
            item["id"] = role
            item["role"] = role
            item["daemon_session_id"] = item.get("live_session_id") or item.get("session_id")
            item["stale"] = self.is_stale(item)
            result.append(item)
        return result

    def member(self, member_id: str) -> Optional[dict[str, Any]]:
        raw = unquote(member_id)
        key = raw.lower()
        return next((m for m in self.members()
                     if (m.get("id") or "").lower() == key
                     or (m.get("role") or "").lower() == key
                     or (m.get("session") or "").lower() == key
                     or m.get("daemon_session_id") == raw
                     or m.get("session_id") == raw), None)

    def is_stale(self, member: Mapping[str, Any]) -> bool:
        # dashboard_data.json 已带 stale 布尔，直接采用。
        if member.get("stale") is True:
            return True
        sid = member.get("daemon_session_id") or member.get("session_id")
        live = member.get("live") or {}
        if member.get("session_id_state") in {"stale", "expired", "invalid", "not_listed"}:
            return True
        if not sid or live.get("isArchived"):
            return True
        stamp = live.get("updatedAt")
        if stamp:
            try:
                parsed = dt.datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
                age = (dt.datetime.now(dt.timezone.utc) - parsed).total_seconds()
                if age > self.stale_seconds:
                    return True
            except ValueError:
                pass
        return False

    def resolve_targets(self, text: str) -> tuple[list[dict[str, Any]], str, list[str]]:
        mentions, body = parse_mentions(text)
        targets: list[dict[str, Any]] = []
        groups = {g.get("id", "").lower(): g for g in self.groups()}
        # 当前控制 session 是默认 viewer；只有显式 @mention 才覆盖该目标。
        default = self.current_session_id or os.environ.get("DAEMON_V2_CURRENT_SESSION_ID")
        requested = mentions or ([default] if default else ["SignL3"])
        for mention in requested:
            group = groups.get(mention.lower())
            names = group.get("members", []) if group else [mention]
            for name in names:
                member = self.member(name)
                if member and member not in targets:
                    targets.append(member)
        return targets, body, mentions

    def explicit_targets(self, target_type: str, target: str) -> list[dict[str, Any]]:
        """按前端传入的 target_type/target 显式解析目标，不依赖 @mention。"""
        if target_type == "session":
            try:
                return [self.session_member(target)]
            except ValueError:
                return []
        if target_type == "group":
            groups = {g.get("id", "").lower(): g for g in self.groups()}
            group = groups.get(target.lower())
            if not group:
                return []
            seen: list[dict[str, Any]] = []
            for name in group.get("members", []):
                member = self.member(name)
                if member and member not in seen:
                    seen.append(member)
            return seen
        member = self.member(target)
        return [member] if member else []

    def session_member(self, session_id: str) -> dict[str, Any]:
        for member in self.members():
            if member.get("daemon_session_id") == session_id or member.get("session_id") == session_id:
                if self.is_stale(member):
                    raise ValueError("stale session")
                return member
        raise ValueError("session is not registered")

    def live_session(self, session_id: str) -> dict[str, Any]:
        """实时 status 核验；registry 只用于发现，不作为存活证明。"""
        self.session_member(session_id)
        try:
            live = self.http_get(f"/session/{quote(session_id, safe='')}/status")
            return {"ok": True, "session_id": session_id, "registry": "listed", "live": live}
        except Exception as exc:
            return {"ok": False, "session_id": session_id, "registry": "listed", "live": False,
                    "error": type(exc).__name__}

    def daemon_session(self, session_id: str, endpoint: str) -> Any:
        self.session_member(session_id)  # 先核验 registry，禁止任意 session 探测
        try:
            return self.http_get(f"/session/{quote(session_id, safe='')}/{endpoint}")
        except Exception as exc:
            return {"ok": False, "error": type(exc).__name__, "session_id": session_id}

    # ---------------- 工作状态判定（区分 prefill 进行中 / 卡住） ----------------

    def work_states(self) -> dict[str, Any]:
        """判定每个成员的 daemon 工作状态：generating / tool_running / stalled / working / idle / error。

        判定逻辑（方案D：基于 SSE 事件流的真实活动，而非仅排队时长）：
        - hasTurnError=true                       → error（turn 报错）
        - hasActivePrompt=false                   → idle（空闲）
        - 有 active prompt 且 SSE 已连接：
            - chunk 事件（thought/message）距今 < SSE_CHUNK_FRESH_SECONDS → generating（正在生成）
            - 有未完成的 tool_call（status pending/in_progress）          → tool_running（工具执行中，绝不判 stalled）
            - 最近事件距今 > STALL_THRESHOLD_SECONDS                       → stalled（真卡住）
            - 其余（近期有事件但非 chunk/工具）                            → working
        - 有 active prompt 但 SSE 不可用（断连/异常）：
            - 回退到排队时长/updatedAt 粗判，但不误报 stalled（按 working 处理）
        结果带短 TTL 缓存（WORK_STATE_CACHE_TTL），避免前端轮询反复压 daemon。
        """
        now = time.time()
        with self._lock:
            if (self._work_state_cache is not None
                    and now - self._work_state_cache_ts < WORK_STATE_CACHE_TTL):
                return self._work_state_cache
        members = []
        for m in self.members():
            sid = m.get("daemon_session_id") or m.get("session_id")
            state = "unknown"
            detail = ""
            if not sid:
                detail = "无 session id"
            else:
                try:
                    state, detail = self._compute_work_state(sid, now)
                except Exception as exc:
                    state, detail = "error", type(exc).__name__
            members.append({
                "id": m.get("id") or m.get("role") or sid,
                "role": m.get("role") or m.get("id"),
                "session_id": sid,
                "state": state,
                "detail": detail,
                "subagents": self._active_tasks(sid),
            })
        # Jarvis（Owner 私人代理，微信 channel 会话）：unassigned 中 displayName=Jarvis
        for us in self.registry().get("unassigned_sessions") or []:
            if not isinstance(us, dict):
                continue
            if str(us.get("displayName") or "").lower() != "jarvis":
                continue
            jid = us.get("sessionId") or ""
            state, detail = "unknown", ""
            if jid:
                try:
                    state, detail = self._compute_work_state(jid, now)
                except Exception as exc:
                    state, detail = "error", type(exc).__name__
            members.append({"id": "Jarvis", "role": "Jarvis", "session_id": jid,
                            "state": state, "detail": detail,
                            "subagents": self._active_tasks(jid)})
            break
        result = {"members": members, "generated_at": now_iso()}
        with self._lock:
            self._work_state_cache = result
            self._work_state_cache_ts = time.time()
        return result

    def _compute_work_state(self, sid: str, now: float) -> tuple[str, str]:
        """基于 daemon status + pending-prompts + SSE 真实活动，计算单个 session 的工作状态。

        返回 (state, detail)。SSE 活动状态来自后台监控线程（_sse_activity）。
        """
        st = self.http_get(f"/session/{quote(sid, safe='')}/status")
        has_active = bool(st.get("hasActivePrompt"))
        turn_error = bool(st.get("hasTurnError"))
        running_since: Optional[float] = None
        try:
            pp = self.http_get(f"/session/{quote(sid, safe='')}/pending-prompts")
            for p in (pp.get("pendingPrompts") if isinstance(pp, dict) else []) or []:
                if p.get("state") == "running" and p.get("queuedAt"):
                    running_since = float(p["queuedAt"]) / 1000.0
        except Exception:
            pass
        with self._sse_lock:
            act = dict(self._sse_activity.get(sid) or self._sse_empty_activity())
            open_tools = dict(act.get("open_tools") or {})
        if turn_error:
            return "error", "turn 报错"
        if not has_active:
            return "idle", "空闲"
        if act.get("sse_connected"):
            # 方案D：基于 SSE 真实活动判定（serverTimestamp 新鲜度，避免重放旧事件误判）
            chunk_age = now - act.get("last_chunk_ts", 0.0)
            event_age = now - act.get("last_event_ts", 0.0)
            if act.get("last_chunk_ts", 0.0) > 0 and chunk_age <= SSE_CHUNK_FRESH_SECONDS:
                return "generating", f"生成中 {int(max(chunk_age, 0))}s"
            if open_tools:
                latest = max(open_tools.values(), key=lambda t: t.get("ts", 0.0))
                return "tool_running", f"{latest.get('toolName', 'tool')} 执行中"
            if act.get("last_event_ts", 0.0) > 0 and event_age > STALL_THRESHOLD_SECONDS:
                return "stalled", f"{int(event_age)}s 无事件"
            return "working", "工作中"
        # SSE 不可用：回退到排队时长/updatedAt 粗判，但不误报 stalled
        if running_since is not None:
            age = now - running_since
            return "working", f"生成中 {int(max(age, 0))}s（SSE 不可用）"
        stamp = self._parse_dt(st.get("updatedAt"))
        if stamp is not None:
            age = (dt.datetime.now(dt.timezone.utc) - stamp).total_seconds()
            return "working", f"updatedAt {int(age)}s 前（SSE 不可用）"
        return "working", "active 状态（SSE 不可用）"

    # ---------------- subagent / side task 追踪 ----------------

    def _is_local_model(self, model: str) -> bool:
        """判定 subagent 用的模型是否为「本地模型服务」（占成员服务线）。

        主判定：model 命中注册表 local_model_services.services[].aliases（唯一事实源），
        支持精确/前缀双向匹配以覆盖家族变体（如 alias=int4-tp1、model=int4-tp1-g0）。
        注册表不可读时用 LOCAL_MODEL_PREFIXES 前缀兜底。
        外部 API（gpt-5.x / deepseek）不命中 → False。
        """
        if not model:
            return False
        for a in load_local_model_aliases():
            if model == a or model.startswith(a) or a.startswith(model):
                return True
        return model.startswith(LOCAL_MODEL_PREFIXES)

    def _active_subagents(self, session_id: str) -> list[dict[str, Any]]:
        """扫描 ~/.qwen/projects/*/subagents/<session_id>/agent-*.meta.json，返回该 session 当前活跃且用了本地模型的 subagent。

        Qwen Code 每次 agent（subagent/side task）调用都会写 agent-*.meta.json，
        status 从 pending/running 过渡到 completed/cancelled/failed。后台 subagent 的
        tool_call 在启动后即 completed，实际工作仍在后台进行，因此不能依赖 SSE
        open_tools 判定，必须看 meta 状态。
        stale：状态非终态但 last_updated 距今超过 SUBAGENT_STALE_SECONDS → 疑似已死。
        只返回「用了本地模型服务」的 subagent（persistedCliFlags.model 命中原生 LOCAL_MODEL_PREFIXES）：
        只有本地模型才占用成员服务线，外部 API（gpt-5.x / deepseek）不显示到「成员用卡」。
        """
        if not session_id:
            return []
        now = time.time()
        out: list[dict[str, Any]] = []
        base = Path(os.path.expanduser("~/.qwen/projects"))
        try:
            metas = sorted(base.glob(f"*/subagents/{session_id}/agent-*.meta.json"))
        except OSError:
            return []
        for mf in metas:
            try:
                m = json.loads(mf.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if not isinstance(m, dict):
                continue
            status = str(m.get("status") or "").lower()
            if status in SUBAGENT_TERMINAL_STATUSES:
                continue
            flags = m.get("persistedCliFlags") or {}
            model = str(flags.get("model") or "").strip()
            # 仅统计用了本地模型的 subagent（占成员服务线）；外部 API 不显示
            if not self._is_local_model(model):
                continue
            created = self._parse_dt(m.get("createdAt"))
            last_up = self._parse_dt(m.get("lastUpdatedAt")) or created
            last_ts = last_up.timestamp() if last_up else 0.0
            out.append({
                "agent_id": m.get("agentId") or mf.name[:-len(".meta.json")],
                "kind": "subagent",
                "description": m.get("description") or m.get("subagentName") or "subagent",
                "status": status or "unknown",
                "model": model,
                "created_at": m.get("createdAt") or "",
                "last_updated": m.get("lastUpdatedAt") or "",
                "elapsed_seconds": int(max(now - created.timestamp(), 0)) if created else 0,
                "stale": bool(last_ts and now - last_ts > SUBAGENT_STALE_SECONDS),
            })
        out.sort(key=lambda x: x.get("created_at") or "", reverse=True)
        return out

    def _active_side_tasks(self, session_id: str) -> list[dict[str, Any]]:
        """返回该成员 session 派生、当前活跃且用了本地模型的 side task（fork 出的独立子会话）。

        side task 记录在 daemon registry unassigned_sessions，特征：sourceType=="side_task"，
        sourceId 指向派生的源会话（=成员 session_id）。
        活跃 = 未归档 且（有客户端连接 clientCount>0 或 正在处理 prompt hasActivePrompt/pending>0）。
        [2026-08-29] 判定放宽：有连接即视为活跃，避免 side task 完成一轮/等待输入时
        hasActivePrompt=false 而成员用卡忽显忽隐（用户启动的本地模型 side task 应稳定显示）。
        闲置（有连接但无 active prompt）不隐藏，status=idle；stale 仅对 running 且超时判定。
        外部模型 / 已归档 / 无连接且空闲 的 side task 不显示。
        模型判定：该 side task 会话当前模型命中本地模型（_member_current_model 查 daemon context）。
        """
        if not session_id:
            return []
        now = time.time()
        out: list[dict[str, Any]] = []
        for s in self.registry().get("unassigned_sessions") or []:
            if not isinstance(s, dict):
                continue
            if s.get("sourceType") != "side_task":
                continue
            if str(s.get("sourceId") or "") != session_id:
                continue
            if s.get("isArchived"):
                continue
            running = bool(s.get("hasActivePrompt") or (s.get("pendingInteractionCount") or 0) > 0)
            connected = (s.get("clientCount") or 0) > 0
            if not (running or connected):
                continue  # 既无客户端连接也不在处理 → 视为已结束，不显示
            task_sid = s.get("sessionId") or ""
            if not task_sid:
                continue
            model = self._member_current_model(task_sid)
            if not self._is_local_model(model):
                continue
            updated = self._parse_dt(s.get("updatedAt"))
            out.append({
                "agent_id": task_sid,
                "kind": "side_task",
                "description": (str(s.get("displayName") or "side task").strip())[:60],
                "status": "running" if running else "idle",
                "model": model,
                "created_at": s.get("createdAt") or "",
                "last_updated": s.get("updatedAt") or "",
                "elapsed_seconds": int(max(now - updated.timestamp(), 0)) if updated else 0,
                "stale": bool(running and updated and now - updated.timestamp() > SUBAGENT_STALE_SECONDS),
            })
        out.sort(key=lambda x: x.get("created_at") or "", reverse=True)
        return out

    def _active_tasks(self, session_id: str) -> list[dict[str, Any]]:
        """合并 subagent + side task（都用本地模型才显示），供「成员用卡」右侧小卡片。"""
        tasks = self._active_subagents(session_id) + self._active_side_tasks(session_id)
        tasks.sort(key=lambda x: x.get("created_at") or "", reverse=True)
        return tasks

    # ---------------- SSE 实时活动监控（方案D：真实活动判定工作状态） ----------------

    @staticmethod
    def _sse_empty_activity() -> dict[str, Any]:
        return {"last_event_ts": 0.0, "last_chunk_ts": 0.0,
                "last_event_kind": "", "open_tools": {},
                "sse_connected": False, "sse_error": ""}

    def start_sse_activity_monitor(self) -> None:
        """启动 SSE 活动监控守护线程（幂等）。在 main() 中调用一次。"""
        with self._sse_lock:
            if self._sse_monitor_started:
                return
            self._sse_monitor_started = True
        threading.Thread(target=self._sse_monitor_loop, name="sse-activity-monitor", daemon=True).start()

    def _sse_member_sids(self) -> list[str]:
        """当前需要监控的 session id 列表（成员 + Jarvis）。"""
        sids: list[str] = []
        seen: set[str] = set()
        try:
            for m in self.members():
                sid = m.get("daemon_session_id") or m.get("session_id")
                if sid and sid not in seen:
                    seen.add(sid); sids.append(sid)
            for us in self.registry().get("unassigned_sessions") or []:
                if not isinstance(us, dict):
                    continue
                if str(us.get("displayName") or "").lower() != "jarvis":
                    continue
                jid = us.get("sessionId") or ""
                if jid and jid not in seen:
                    seen.add(jid); sids.append(jid)
        except Exception:
            pass
        return sids

    def _sse_monitor_loop(self) -> None:
        """主循环：为每个成员 session 确保有一个 SSE 监控线程在跑（断线自动补线程）。"""
        while True:
            try:
                sids = self._sse_member_sids()
                with self._sse_lock:
                    for sid in sids:
                        th = self._sse_monitor_threads.get(sid)
                        if th is None or not th.is_alive():
                            th = threading.Thread(target=self._sse_session_monitor, args=(sid,),
                                                   name=f"sse-mon-{sid[:8]}", daemon=True)
                            self._sse_monitor_threads[sid] = th
                            th.start()
            except Exception:
                pass
            time.sleep(SSE_MONITOR_SCAN_INTERVAL)

    def _sse_session_monitor(self, sid: str) -> None:
        """单个 session 的 SSE 长连接监控：持续读取 /events 事件流，更新活动状态。

        断连后等待 SSE_RECONNECT_DELAY 秒自动重连；异常只记录 sse_error，不抛到主循环。
        """
        while True:
            try:
                resp = self.http_stream(f"/session/{quote(sid, safe='')}/events",
                                        {"Accept": "text/event-stream"})
                with self._sse_lock:
                    self._sse_activity.setdefault(sid, self._sse_empty_activity())
                    self._sse_activity[sid]["sse_connected"] = True
                    self._sse_activity[sid]["sse_error"] = ""
                try:
                    buf = ""
                    for raw in resp:
                        if isinstance(raw, bytes):
                            raw = raw.decode("utf-8", "replace")
                        buf += raw
                        # SSE 事件以换行分隔；逐行解析 data: 行（忽略 event:/注释行）
                        while "\n" in buf:
                            line, buf = buf.split("\n", 1)
                            line = line.strip()
                            if not line.startswith("data:"):
                                continue
                            payload = line[5:].strip()
                            if not payload or payload == "[DONE]":
                                continue
                            try:
                                ev = json.loads(payload)
                            except ValueError:
                                continue
                            self._sse_record_event(sid, ev)
                finally:
                    try:
                        resp.close()
                    except Exception:
                        pass
                with self._sse_lock:
                    if sid in self._sse_activity:
                        self._sse_activity[sid]["sse_connected"] = False
            except Exception as exc:
                with self._sse_lock:
                    self._sse_activity.setdefault(sid, self._sse_empty_activity())
                    self._sse_activity[sid]["sse_connected"] = False
                    self._sse_activity[sid]["sse_error"] = type(exc).__name__
            time.sleep(SSE_RECONNECT_DELAY)

    def _sse_record_event(self, sid: str, ev: dict[str, Any]) -> None:
        """解析单个 SSE 事件，更新该 session 的活动状态。

        事件结构：{"event": {"type": "session_update", "data": {"update": {
        "sessionUpdate": "agent_thought_chunk|agent_message_chunk|tool_call|tool_call_update|...",
        "toolCallId": "...", "status": "pending|in_progress|completed",
        "_meta": {"toolName": "...", "serverTimestamp": ms}}}}}
        新鲜度用 _meta.serverTimestamp 判定（避免重放的旧事件被误判为近期活动）。
        """
        inner = ev.get("event") if isinstance(ev.get("event"), dict) else ev
        etype = inner.get("type") or ""
        data = inner.get("data") or {}
        update = data.get("update") or {}
        kind = update.get("sessionUpdate") or ""
        now = time.time()
        meta = inner.get("_meta") or {}
        ts_raw = meta.get("serverTimestamp")
        try:
            event_ts = float(ts_raw) / 1000.0 if ts_raw else now
        except (TypeError, ValueError):
            event_ts = now
        with self._sse_lock:
            act = self._sse_activity.setdefault(sid, self._sse_empty_activity())
            act["last_event_ts"] = max(act["last_event_ts"], event_ts)
            act["last_event_kind"] = kind or etype
            if kind in ("agent_thought_chunk", "agent_message_chunk"):
                act["last_chunk_ts"] = max(act["last_chunk_ts"], event_ts)
            if kind in ("tool_call", "tool_call_update"):
                tool_id = update.get("toolCallId") or ""
                status = update.get("status") or ""
                tool_name = (update.get("_meta") or {}).get("toolName") or update.get("title") or "tool"
                if tool_id:
                    if status in ("completed", "failed", "cancelled"):
                        act["open_tools"].pop(tool_id, None)
                    else:
                        act["open_tools"][tool_id] = {"toolName": tool_name, "status": status, "ts": event_ts}

    # ---------------- 实时 GPU 抓取（SSH → nvidia-smi） ----------------

    def _gpu_snapshot_live(self) -> list[dict[str, Any]]:
        """SSH 到 zhuhai 实时抓 nvidia-smi（index, name, util, mem），失败返回空列表。

        使用 BatchMode 非交互 + 短超时；本机无 nvidia-smi（nature 无 GPU）时
        通过 ~/.ssh/config 的 zhuhai 别名直连。单条命令带 JSON 输出。
        """
        cmd = ("nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total "
               "--format=csv,noheader,nounits")
        try:
            proc = subprocess.run(
                ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=4",
                 "-o", "StrictHostKeyChecking=accept-new", GPU_HOST, cmd],
                capture_output=True, text=True, timeout=GPU_SSH_TIMEOUT,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return [{"error": type(exc).__name__}]
        if proc.returncode != 0:
            return [{"error": f"ssh rc={proc.returncode}: {proc.stderr.strip()[:160]}"}]
        rows = []
        for line in proc.stdout.splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 5:
                continue
            try:
                rows.append({
                    "index": int(parts[0]),
                    "name": parts[1],
                    "util": int(parts[2]),
                    "used_mib": int(parts[3]),
                    "total_mib": int(parts[4]),
                })
            except ValueError:
                continue
        return rows

    def _member_current_model(self, session_id: str) -> str:
        """从 daemon /session/:id/context 读当前模型 id。

        带短 TTL 缓存 + 失败回退：context 查询偶发超时（daemon 忙）时不返回空串
        导致成员用卡间歇性消失，而是回退最近一次成功值。
        """
        if not session_id:
            return ""
        now = time.time()
        with self._lock:
            cached = self._model_cache.get(session_id)
            if cached and now - cached[1] < MODEL_CACHE_TTL:
                return cached[0]
        try:
            ctx = self.http_get(f"/session/{quote(session_id, safe='')}/context")
            models = (ctx.get("state") or {}).get("models") or {}
            mid = models.get("currentModelId") or ""
            model = str(mid).split("(")[0].strip()
        except Exception:
            model = ""
        if model:
            with self._lock:
                self._model_cache[session_id] = (model, now)
        else:
            # 本次读取失败：回退上次成功值（若有），避免间歇性消失
            with self._lock:
                cached = self._model_cache.get(session_id)
                if cached:
                    model = cached[0]
        return model

    def _cached_swr(self, cache_attr: str, ts_attr: str, refreshing_attr: str,
                    ttl: float, fetch, extra_stale: dict | None = None) -> dict:
        """stale-while-revalidate：缓存新鲜→直接返回；过期→返回旧缓存 + 后台线程刷新；
        无缓存→同步 fetch 并缓存。SSH/慢数据源不再阻塞接口（有缓存后接口永远快速返回，
        慢源失败时保留旧数据并标记 stale，页面显示「数据陈旧」而非卡死/空白）。
        线程安全：self._lock 保护缓存与刷新标记；同一时刻只允许一个刷新线程。"""
        now = time.time()
        with self._lock:
            cache = getattr(self, cache_attr)
            ts = getattr(self, ts_attr, 0.0)
            if cache is not None and now - ts < ttl:
                return cache
            has_cache = cache is not None
            refreshing = getattr(self, refreshing_attr, False)
            if has_cache:
                if not refreshing:
                    setattr(self, refreshing_attr, True)

                    def _bg() -> None:
                        try:
                            data = fetch()
                            with self._lock:
                                setattr(self, cache_attr, data)
                                setattr(self, ts_attr, time.time())
                        except Exception:  # noqa: BLE001 后台刷新失败保留旧缓存
                            pass
                        finally:
                            with self._lock:
                                setattr(self, refreshing_attr, False)

                    threading.Thread(target=_bg, daemon=True).start()
                stale = dict(cache)
                stale["stale"] = True
                stale["stale_ts"] = now_iso()
                if extra_stale:
                    stale.update(extra_stale)
                return stale
        data = fetch()
        with self._lock:
            setattr(self, cache_attr, data)
            setattr(self, ts_attr, time.time())
        return data

    def _fetch_gpu_live(self) -> dict[str, Any]:
        """gpu_live 数据抓取主体（SSH nvidia-smi + 成员模型关联），由缓存层调用。"""
        gpus = self._gpu_snapshot_live()
        error = None
        if gpus and gpus[0].get("error"):
            error = gpus[0]["error"]
            gpus = []
        gpu_by_index = {g["index"]: g for g in gpus}
        members = []

        def _member_gpu(role: str, sid: str) -> dict[str, Any]:
            """单个 session 的 模型→GPU 关联（roles 成员与 Jarvis 通用）。"""
            model = self._member_current_model(sid) if sid else ""
            mapped = LOCAL_MODEL_GPU_MAP.get(model, [])
            gpu_info = []
            for idx in mapped:
                info = gpu_by_index.get(idx)
                if info:
                    gpu_info.append({"gpu": idx, "util": info.get("util"), "used_mib": info.get("used_mib")})
            return {
                "role": role,
                "model": model,
                "gpus": mapped,
                "gpu_info": gpu_info,
                "local_model": bool(mapped),
            }

        def _member_gpu_with_tasks(role: str, sid: str) -> None:
            """追加单个 session 的主会话 GPU 关联 + 其派生的活跃本地模型子任务（side task/subagent）。

            roles 成员与 Jarvis 通用：Jarvis（微信 channel 会话）同样会启动 sub/side task，
            必须一并纳入「成员用卡」，否则 Jarvis 的子任务用卡不显示（2026-08-30 修复）。
            """
            members.append(_member_gpu(role, sid))
            # 该成员派生的活跃本地模型子任务（side task/subagent）：按其实际用卡（model→GPU）归位到
            # 对应模型分组，并在 role 前标注归属成员，体现"是它的子任务在用卡"（可能与主会话模型不同）。
            for t in self._active_tasks(sid):
                t_model = t.get("model") or ""
                t_mapped = LOCAL_MODEL_GPU_MAP.get(t_model, [])
                t_info = []
                for idx in t_mapped:
                    g = gpu_by_index.get(idx)
                    if g:
                        t_info.append({"gpu": idx, "util": g.get("util"), "used_mib": g.get("used_mib")})
                members.append({
                    "role": f"{role}{'side' if t.get('kind') == 'side_task' else 'sub'}",
                    "model": t_model,
                    "gpus": t_mapped,
                    "gpu_info": t_info,
                    "local_model": bool(t_mapped),
                    "task_type": t.get("kind"),
                    "task_status": t.get("status", ""),
                })

        for m in self.members():
            sid = m.get("daemon_session_id") or m.get("session_id")
            role = m.get("role") or m.get("id")
            _member_gpu_with_tasks(role, sid)
        # Jarvis（Owner 私人代理，微信 channel 会话）：unassigned 中 displayName=Jarvis
        for us in self.registry().get("unassigned_sessions") or []:
            if not isinstance(us, dict):
                continue
            if str(us.get("displayName") or "").lower() != "jarvis":
                continue
            _member_gpu_with_tasks("Jarvis", us.get("sessionId") or "")
            break
        return {
            "gpus": gpus,
            "members": members,
            "snapshot_error": error,
            "updated_at": now_iso(),
        }

    def gpu_live(self) -> dict[str, Any]:
        """实时 GPU 状态 + 成员→模型→GPU 关联（stale-while-revalidate 缓存，TTL 5s）。

        返回：
        - gpus: [{index,name,util,used_mib}]（zhuhai 实时 nvidia-smi）
        - members: [{role, model, gpus:[int], gpu_info:[{gpu,util,used_mib}]}]
        - snapshot_error: SSH/解析失败时的错误信息
        - stale / stale_ts: 缓存过期后台刷新中/刷新失败时为 True（前端可提示数据陈旧）
        - updated_at
        """
        return self._cached_swr(
            "_gpu_live_cache", "_gpu_live_cache_ts", "_gpu_live_refreshing",
            GPU_LIVE_CACHE_TTL, self._fetch_gpu_live,
        )

    def _fetch_host_resources(self) -> dict[str, Any]:
        """host_resources 数据抓取主体（SSH zhuhai 双采样 + 本机 /proc 采样），由缓存层调用。"""
        hosts: list[dict[str, Any]] = []
        # 1. zhuhai（SSH，base64 传输避免多层转义破坏多行脚本）
        zh = self._ssh_host_resources()
        zh["name"] = "zhuhai"; zh["source"] = "ssh"
        hosts.append(zh)
        # 2. 本机 nature（/proc + ps 直接采样）
        local: dict[str, Any] = {"name": "nature", "source": "localhost", "ok": True}
        try:
            def _cpu_total_idle() -> tuple[int, int]:
                for line in Path("/proc/stat").read_text(encoding="utf-8").splitlines():
                    if line.startswith("cpu "):
                        nums = [int(p) for p in line.split()[1:8]]
                        return sum(nums), nums[3]  # (total, idle)
                return 0, 0
            t1, i1 = _cpu_total_idle()
            time.sleep(0.5)
            t2, i2 = _cpu_total_idle()
            dt, di = t2 - t1, i2 - i1
            if dt > 0:
                local["cpu_pct"] = round(100 * (1 - di / dt), 1)
            mem: dict[str, int] = {}
            for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
                key, _, rest = line.partition(":")
                mem[key] = int(rest.split()[0])  # kB
            total = mem.get("MemTotal", 0)
            avail = mem.get("MemAvailable", total)
            if total > 0:
                used = total - avail
                local["mem_total_gib"] = round(total / 1024 / 1024, 1)
                local["mem_used_gib"] = round(used / 1024 / 1024, 1)
                local["mem_avail_gib"] = round(avail / 1024 / 1024, 1)
                local["mem_pct"] = round(100 * used / total, 1)
            # 用户 wuyangcheng 用量（与 zhuhai 同口径：ps pcpu/rss 求和，CPU 按核数归一化）
            try:
                cores = int(subprocess.run(["nproc"], capture_output=True, text=True, timeout=5).stdout.strip() or 0)
            except (OSError, subprocess.TimeoutExpired, ValueError):
                cores = 0
            if cores <= 0:
                cores = sum(1 for _ in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines() if "processor" in _)
            def _ps_sum(col: str) -> float:
                try:
                    out = subprocess.run(f"ps -u wuyangcheng -o {col}= --no-headers 2>/dev/null | awk '{{s+=$1}}END{{print s+0}}'",
                                         shell=True, capture_output=True, text=True, timeout=5).stdout.strip()
                    return float(out or 0)
                except (OSError, subprocess.TimeoutExpired, ValueError):
                    return 0.0
            user_cpu_raw = _ps_sum("pcpu")
            user_rss_kb = _ps_sum("rss")
            if cores > 0:
                local["cpu_cores"] = cores
                local["user_cpu_pct"] = round(user_cpu_raw / cores, 1)
                local["user_cpu_raw_pct"] = round(user_cpu_raw, 1)
            if total > 0:
                local["user_mem_gib"] = round(user_rss_kb / 1024 / 1024, 2)
                local["user_mem_pct"] = round(user_rss_kb / total * 100, 1) if user_rss_kb > 0 else 0.0
        except Exception as exc:  # noqa: BLE001
            local["ok"] = False
            local["error"] = str(exc)
        hosts.append(local)
        return {"ok": True, "hosts": hosts, "updated_at": now_iso()}

    def host_resources(self) -> dict[str, Any]:
        """zhuhai + 本机（nature）CPU 与内存总量使用率监控（stale-while-revalidate 缓存）。

        返回 {ok, hosts: [{name, source, cpu_pct, mem_pct, mem_total_gib, mem_used_gib,
        mem_avail_gib, error?}], stale?, updated_at}；zhuhai 在前（SSH base64 传 python 脚本
        双采样），本机在后（/proc 直接采样）。预警阈值（≤20% 绿 / >20% 红）由前端判定。
        缓存过期时返回旧数据 + stale 标记（后台刷新），SSH 抖动不再阻塞/清空面板。
        """
        return self._cached_swr(
            "_host_res_cache", "_host_res_cache_ts", "_host_res_refreshing",
            GPU_LIVE_CACHE_TTL, self._fetch_host_resources,
        )

    def _ssh_host_resources(self) -> dict[str, Any]:
        """SSH 到 zhuhai 抓 CPU/内存（/proc 双采样 + 用户 wuyangcheng 用量），失败返回 error 字段。"""
        remote = (
            "import json,time,subprocess\n"
            "def cpu():\n"
            "    for line in open('/proc/stat'):\n"
            "        if line.startswith('cpu '):\n"
            "            n=[int(x) for x in line.split()[1:8]]\n"
            "            return sum(n),n[3]\n"
            "    return 0,0\n"
            "t1,i1=cpu();time.sleep(0.5);t2,i2=cpu()\n"
            "dt,di=t2-t1,i2-i1\n"
            "mem={}\n"
            "for line in open('/proc/meminfo'):\n"
            "    k,_,v=line.partition(':');mem[k]=int(v.split()[0])\n"
            "total=mem.get('MemTotal',0);avail=mem.get('MemAvailable',total)\n"
            "used=total-avail if total>0 else 0\n"
            "try:\n"
            "    cores=int(subprocess.run(['nproc'],capture_output=True,text=True).stdout.strip() or 0)\n"
            "except Exception:\n"
            "    cores=0\n"
            "if cores<=0:\n"
            "    try:\n"
            "        cores=sum(1 for _ in open('/proc/cpuinfo') if 'processor' in _)\n"
            "    except Exception:\n"
            "        cores=0\n"
            "def ps_sum(col):\n"
            "    try:\n"
            "        s=subprocess.run(f\"ps -u wuyangcheng -o {col}= --no-headers 2>/dev/null | awk '{{s+=$1}}END{{print s+0}}'\",shell=True,capture_output=True,text=True)\n"
            "        return float(s.stdout.strip() or 0)\n"
            "    except Exception:\n"
            "        return 0.0\n"
            "user_cpu_raw=ps_sum('pcpu')\n"
            "user_rss_kb=ps_sum('rss')\n"
            "print(json.dumps({'cpu_pct': round(100*(1-di/dt),1) if dt>0 else None,\n"
            "    'mem_pct': round(100*used/total,1) if total>0 else None,\n"
            "    'mem_total_gib': round(total/1024/1024,1) if total>0 else None,\n"
            "    'mem_used_gib': round(used/1024/1024,1) if total>0 else None,\n"
            "    'mem_avail_gib': round(avail/1024/1024,1) if total>0 else None,\n"
            "    'cpu_cores': cores,\n"
            "    'user_cpu_pct': round(user_cpu_raw/cores,1) if cores>0 else None,\n"
            "    'user_cpu_raw_pct': round(user_cpu_raw,1),\n"
            "    'user_mem_gib': round(user_rss_kb/1024/1024,2) if user_rss_kb>0 else 0.0,\n"
            "    'user_mem_pct': round(user_rss_kb/total*100,1) if total>0 and user_rss_kb>0 else None}))\n"
        )
        import base64 as _b64
        b64 = _b64.b64encode(remote.encode("utf-8")).decode()
        cmd = f"echo {b64} | base64 -d | python3"
        try:
            proc = subprocess.run(
                ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=4",
                 "-o", "StrictHostKeyChecking=accept-new", GPU_HOST, cmd],
                capture_output=True, text=True, timeout=GPU_SSH_TIMEOUT,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {"ok": False, "error": type(exc).__name__}
        if proc.returncode != 0:
            return {"ok": False, "error": f"ssh rc={proc.returncode}: {proc.stderr.strip()[:160]}"}
        try:
            data = json.loads(proc.stdout.strip().splitlines()[-1])
            data["ok"] = True
            return data
        except (ValueError, IndexError):
            return {"ok": False, "error": "zhuhai 返回解析失败"}

    def transcript_latest(self, session_id: str, max_events: int = 600, max_pages: int = 60) -> dict[str, Any]:
        """循环分页 daemon transcript（从最早开始），只返回最新 max_events 条。"""
        self.session_member(session_id)
        all_events: list[dict[str, Any]] = []
        cursor: Optional[str] = None
        for _ in range(max_pages):
            path = f"/session/{quote(session_id, safe='')}/transcript?limit=500"
            if cursor:
                path += f"&cursor={quote(cursor, safe='')}"
            try:
                data = self.http_get(path)
            except Exception:
                break
            events = data.get("events", []) if isinstance(data, dict) else []
            all_events.extend(events)
            cursor = data.get("nextCursor") or data.get("next_cursor")
            if not data.get("hasMore") or not cursor:
                break
        latest = all_events[-max_events:]
        return {"ok": True, "session_id": session_id, "events": latest,
                "total": len(all_events), "truncated": len(all_events) > max_events}

    # ---------------- API 用量追踪 ----------------
    # 数据源（均为 daemon 精确统计，非估算）：
    #   今日/趋势 -> GET /usage/dashboard?range=today|week（daemon 用量追踪，合并 live session）
    #   成员分布   -> GET /session/{id}/stats（各会话生命周期累计：tokens.prompt/candidates/cached/thoughts）
    # 费用为估算：DeepSeek 模型按 DS_PRICE_USD 参考价（可配置），GPT 订阅模型不计费。

    def _usage_http_get(self, path: str) -> Any:
        """API 用量专用的 daemon 只读 GET：超时放宽到 30s 并对超时/连接失败重试一次
        （daemon 首次重建 usage dashboard 可能较慢）。"""
        if self.http_get is not self._http_get:
            return self.http_get(path)  # 测试注入
        last: Optional[Exception] = None
        for attempt in (1, 2):
            try:
                req = Request(self.daemon_url.rstrip("/") + path, headers=auth_headers({"Accept": "application/json"}))
                with urlopen(req, timeout=30.0) as response:
                    return json.loads(response.read().decode("utf-8"))
            except (TimeoutError, OSError) as exc:
                last = exc
        raise last  # type: ignore[misc]

    @staticmethod
    def _model_cost(model: str, in_tokens: int, cached_tokens: int, out_tokens: int) -> tuple[float, float]:
        """单模型 DeepSeek 费用估算，返回 (usd, cny)。

        cached 属于输入的一部分；分别按「缓存命中输入 / 缓存未命中输入 / 输出」三档计价，
        USD 走官方 USD 价表、CNY 走官方 CNY 价表（均为 off-peak 参考价），互不依赖汇率换算。
        """
        usd_price = DS_PRICE_USD.get(model)
        cny_price = DS_PRICE_CNY.get(model)
        if not usd_price or not cny_price:
            return 0.0, 0.0
        miss = max(0, in_tokens - cached_tokens)
        usd = (cached_tokens / 1e6 * usd_price["input_cache_hit"]
               + miss / 1e6 * usd_price["input_cache_miss"]
               + out_tokens / 1e6 * usd_price["output"])
        cny = (cached_tokens / 1e6 * cny_price["input_cache_hit"]
               + miss / 1e6 * cny_price["input_cache_miss"]
               + out_tokens / 1e6 * cny_price["output"])
        return usd, cny

    # ---------------- 分时（hourly）用量追踪（chat 事件解析） ----------------

    def _hourly_targets(self) -> list[tuple[str, str]]:
        """返回 (session_id, 显示名) 列表：注册角色 session + Jarvis 会话（与成员分布一致）。"""
        roles_name = {k: (v.get("name") or k) for k, v in (self.registry().get("roles") or {}).items()}
        out: list[tuple[str, str]] = []
        seen: set[str] = set()
        for m in self.members():
            sid = m.get("daemon_session_id") or m.get("session_id")
            if not sid or sid in seen:
                continue
            seen.add(sid)
            mid = m.get("id") or m.get("role")
            out.append((sid, roles_name.get(mid) or m.get("name") or m.get("displayName") or mid))
        for us in self.registry().get("unassigned_sessions") or []:
            sid = us.get("sessionId")
            if not sid or sid in seen:
                continue
            if str(us.get("displayName") or "") == "Jarvis":
                seen.add(sid)
                out.append((sid, "Jarvis"))
        return out

    def _get_hourly_tracker(self) -> HourlyTracker:
        if self._hourly_tracker is None:
            self._hourly_tracker = HourlyTracker(CHATS_DIR, self.v2 / "hourly_usage_state.json",
                                                 self._hourly_targets)
        return self._hourly_tracker

    def hourly_usage(self) -> dict[str, Any]:
        """分时用量报告（最近 24h 小时分布 + 今日 peak/off-peak 费用拆分）。"""
        try:
            return self._get_hourly_tracker().report()
        except Exception as exc:
            return {"ok": False, "source": "chat_api_response",
                    "error": type(exc).__name__, "error_detail": preview(str(exc), 200)}

    def _build_api_usage(self) -> dict[str, Any]:
        today_dash = self._usage_http_get("/usage/dashboard?range=today") or {}
        week_dash = self._usage_http_get("/usage/dashboard?range=week") or {}
        summary = today_dash.get("summary") or {}
        daily = week_dash.get("daily") or []

        total = summary.get("totalTokens") or 0
        out_tokens = summary.get("outputTokens") or 0
        out_ratio = out_tokens / total if total else 0.0

        # ---- 今日费用：优先用 chat 事件分时聚合（按小时 × peak/off-peak 精确计价，
        # response_id 去重、思考 token 并入输出）；chat 数据不可用时回退 daemon
        # dashboard 比例估算（每模型只有 totalTokens + cacheReadRate，缓存只作用于输入）。----
        cost_usd = 0.0
        cost_cny = 0.0
        cost_peak_usd = cost_peak_cny = 0.0
        cost_offpeak_usd = cost_offpeak_cny = 0.0
        cost_models: list[dict[str, Any]] = []
        hourly: list[dict[str, Any]] = []
        cost_method = "daemon_ratio_estimate"
        hourly_report = self.hourly_usage()
        if hourly_report.get("ok"):
            today_hr = hourly_report.get("today") or {}
            if today_hr.get("cost_usd") is not None:
                cost_usd = today_hr["cost_usd"]
                cost_cny = today_hr["cost_cny"]
                cost_peak_usd = today_hr.get("cost_peak_usd") or 0.0
                cost_peak_cny = today_hr.get("cost_peak_cny") or 0.0
                cost_offpeak_usd = today_hr.get("cost_offpeak_usd") or 0.0
                cost_offpeak_cny = today_hr.get("cost_offpeak_cny") or 0.0
                hourly = hourly_report.get("hourly") or []
                cost_models = [
                    {"model": name, "input_tokens": v["input"], "output_tokens": v["output"],
                     "cached_tokens": v["cached"], "requests": v["count"],
                     "cost_usd": v["cost_usd"], "cost_cny": v["cost_cny"],
                     "cost_peak_usd": v["cost_peak_usd"], "cost_offpeak_usd": v["cost_offpeak_usd"]}
                    for name, v in (today_hr.get("models") or {}).items()]
                cost_method = "chat_api_response_hourly"
        if cost_method == "daemon_ratio_estimate":
            for m in today_dash.get("models") or []:
                name = str(m.get("model") or "")
                if name not in DS_PRICE_USD:
                    continue
                tokens = m.get("totalTokens") or 0
                rate = m.get("cacheReadRate") or 0.0
                out_m = int(tokens * out_ratio)
                in_m = max(0, int(tokens) - out_m)
                cached_m = int(in_m * rate)
                usd, cny = self._model_cost(name, in_m, cached_m, out_m)
                cost_usd += usd
                cost_cny += cny
                cost_models.append({"model": name, "tokens": tokens,
                                    "input_tokens": in_m, "output_tokens": out_m,
                                    "cached_tokens": cached_m,
                                    "cache_read_rate": rate,
                                    "cost_usd": round(usd, 4), "cost_cny": round(cny, 4)})

        # ---- 近 7 天趋势 + 昨日对比（daily 数组，最后一条为今日）----
        trend = [{"date": d.get("date"), "tokens": d.get("tokens") or 0,
                  "sessions": d.get("sessions") or 0} for d in daily[-7:]]
        today_entry = daily[-1] if daily else {}
        yesterday_entry = daily[-2] if len(daily) >= 2 else {}
        yesterday_tokens = yesterday_entry.get("tokens") or 0
        today_tokens = total or today_entry.get("tokens") or 0
        delta_pct = None
        if yesterday_tokens > 0:
            delta_pct = round((today_tokens - yesterday_tokens) / yesterday_tokens * 100, 1)

        # ---- 成员分布：注册角色 session + Jarvis 会话（unassigned 中 displayName=Jarvis）----
        roles_name = {k: (v.get("name") or k) for k, v in (self.registry().get("roles") or {}).items()}
        members: list[dict[str, Any]] = []
        seen_sessions = set()
        for member in self.members():
            sid = member.get("daemon_session_id") or member.get("session_id")
            if not sid or sid in seen_sessions:
                continue
            seen_sessions.add(sid)
            mid = member.get("id") or member.get("role")
            # name = team 角色中文名（主管/视频等，从 registry roles 映射），前端成员分布按 name 显示
            members.append({"id": mid,
                            "role": member.get("role") or mid,
                            "name": roles_name.get(mid) or member.get("name") or member.get("displayName") or mid,
                            "session_id": sid})
        for us in self.registry().get("unassigned_sessions") or []:
            sid = us.get("sessionId")
            if not sid or sid in seen_sessions:
                continue
            if str(us.get("displayName") or "") == "Jarvis":
                seen_sessions.add(sid)
                members.append({"id": "Jarvis", "role": "Jarvis", "name": "Jarvis", "session_id": sid})

        member_rows = []
        for m in members:
            try:
                st = self._usage_http_get(f"/session/{quote(m['session_id'], safe='')}/stats")
            except Exception:
                m["error"] = "stats_unavailable"
                member_rows.append(m)
                continue
            if not isinstance(st, dict) or "models" not in st:
                m["error"] = "stats_missing"
                member_rows.append(m)
                continue
            in_t = out_t = cached_t = thoughts_t = requests = 0
            member_usd = member_cny = 0.0
            per_model: dict[str, Any] = {}
            for name, mm in (st.get("models") or {}).items():
                tok = mm.get("tokens") or {}
                api = mm.get("api") or {}
                t_in = tok.get("prompt") or 0
                t_out = tok.get("candidates") or 0
                t_cached = tok.get("cached") or 0
                t_thoughts = tok.get("thoughts") or 0
                req = api.get("totalRequests") or 0
                in_t += t_in; out_t += t_out; cached_t += t_cached
                thoughts_t += t_thoughts; requests += req
                usd, cny = self._model_cost(name, t_in, t_cached, t_out)
                member_usd += usd; member_cny += cny
                per_model[name] = {"in_tokens": t_in, "out_tokens": t_out,
                                   "cached_tokens": t_cached, "requests": req}
            m.update({"session_start": st.get("sessionStartTimeMs"),
                      "in_tokens": in_t, "out_tokens": out_t, "cached_tokens": cached_t,
                      "thoughts_tokens": thoughts_t, "total_tokens": in_t + out_t,
                      "requests": requests, "models": per_model,
                      "cost_usd": round(member_usd, 4), "cost_cny": round(member_cny, 4)})
            member_rows.append(m)
        member_rows.sort(key=lambda x: x.get("total_tokens") or 0, reverse=True)

        return {
            "ok": True, "source": "daemon", "generated_at": now_iso(),
            "prices": {"usd_cny": USD_CNY_RATE,
                       "source": PRICE_SOURCE, "updated": PRICE_UPDATE_DATE,
                       "peak_multiplier": DS_PEAK_MULTIPLIER,
                       "peak_hours": "北京时间 09:00-12:00 / 14:00-18:00（UTC 01:00-04:00 / 06:00-10:00），其余为 off-peak（半价）",
                       "usd": DS_PRICE_USD, "cny": DS_PRICE_CNY,
                       "note": "DeepSeek 官方 off-peak 参考价；高峰时段 ×2；GPT 订阅模型不计费；无公开价格 JSON API，改价需人工更新常量"},
            "today": {"date": today_entry.get("date"),
                      "total_tokens": total, "input_tokens": summary.get("inputTokens") or 0,
                      "output_tokens": out_tokens, "cached_tokens": summary.get("cachedTokens") or 0,
                      "requests": summary.get("requests") or 0, "sessions": summary.get("sessions") or 0,
                      "tool_calls": summary.get("toolCalls") or 0,
                      "thoughts_tokens": summary.get("thoughtsTokens") or 0,
                      "cache_read_rate": summary.get("cacheReadRate") or 0.0,
                      "cost_method": cost_method,
                      "cost_usd": round(cost_usd, 4), "cost_cny": round(cost_cny, 4),
                      "cost_peak_usd": round(cost_peak_usd, 4), "cost_peak_cny": round(cost_peak_cny, 4),
                      "cost_offpeak_usd": round(cost_offpeak_usd, 4), "cost_offpeak_cny": round(cost_offpeak_cny, 4),
                      "cost_models": cost_models,
                      "chat_tokens": {"input": (hourly_report.get("today") or {}).get("input_tokens"),
                                      "cached": (hourly_report.get("today") or {}).get("cached_tokens"),
                                      "output": (hourly_report.get("today") or {}).get("output_tokens"),
                                      "requests": (hourly_report.get("today") or {}).get("requests")}
                      if hourly_report.get("ok") else None,
                      "yesterday_tokens": yesterday_tokens, "delta_pct": delta_pct},
            "hourly": hourly,
            "hourly_window": (hourly_report.get("window") or {}) if hourly_report.get("ok") else {},
            "trend": trend,
            "members": member_rows,
            "notes": [
                "今日汇总/趋势：daemon /usage/dashboard 精确统计（含运行中 session 重建）；今日费用与小时分布来自 chat 事件分时聚合",
                "费用（cost_method=chat_api_response_hourly 时）：解析 8 角色 + Jarvis session 的 chat 文件 qwen-code.api_response 事件（含 response_id 去重、思考 token 按输出计费），按北京时间小时判定高峰/空闲分别计价",
                "成员分布：/session/{id}/stats 精确统计，为会话生命周期累计（session 自 08-18 启动以来）；其费用按 off-peak 参考价估算",
                f"价格来源：{PRICE_SOURCE}，更新日期 {PRICE_UPDATE_DATE}；高峰时段（北京 9-12/14-18 点）价格 ×{DS_PEAK_MULTIPLIER:g}（off-peak 半价）",
                "回退口径（cost_method=daemon_ratio_estimate）：daemon dashboard 每模型仅有 totalTokens+cacheReadRate，输出按整体比例分摊；缓存只作用于输入部分",
            ],
        }

    def api_usage(self) -> dict[str, Any]:
        """聚合 daemon 用量统计并返回 API 用量板块数据（带短 TTL 缓存）。

        成功结果缓存 USAGE_CACHE_TTL 秒；失败只缓存 5 秒（避免瞬态错误毒化面板，
        也避免 daemon 不可用时每次轮询都做 11 次带超时请求）。"""
        import time as _time
        now = _time.time()
        with self._usage_lock:
            if self._usage_cache is not None and now - self._usage_cache_ts < self._usage_cache_ttl:
                return self._usage_cache
        try:
            data = self._build_api_usage()
            ttl = USAGE_CACHE_TTL
        except Exception as exc:
            data = {"ok": False, "source": "daemon", "error": type(exc).__name__,
                    "error_detail": preview(str(exc), 200)}
            ttl = 5.0
        with self._usage_lock:
            self._usage_cache = data
            self._usage_cache_ts = now
            self._usage_cache_ttl = ttl
        return data

    def _http_post_json(self, path: str, payload: Mapping[str, Any]) -> Any:
        req = Request(self.daemon_url.rstrip("/") + path, data=json.dumps(payload).encode(), method="POST",
                      headers=auth_headers({"Content-Type": "application/json", "Accept": "application/json"}))
        with urlopen(req, timeout=5.0) as response:
            return json.loads(response.read().decode("utf-8"))

    def _http_stream(self, path: str, headers: Mapping[str, str]):
        req = Request(self.daemon_url.rstrip("/") + path, headers=auth_headers(dict(headers)))
        # SSE 长连接：idle 超时放宽到 5 分钟，避免空闲 session 回放后 10 秒即断连
        return urlopen(req, timeout=300.0)

    def session_action(self, session_id: str, action: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        self.session_member(session_id)
        dry_run = bool(payload.get("dry_run", True)); confirmed = bool(payload.get("confirm", False))
        if dry_run or not confirmed:
            return {"ok": True, "dry_run": True, "action": action, "session_id": session_id,
                    "would_call": f"/session/{quote(session_id, safe='')}/{action}"}
        try:
            return {"ok": True, "dry_run": False, "action": action,
                    "result": self.http_post(f"/session/{quote(session_id, safe='')}/{action}", payload)}
        except Exception as exc:
            return {"ok": False, "dry_run": False, "action": action, "error": type(exc).__name__}

    def write_audit(self, record: dict[str, Any]) -> None:
        self.v2.mkdir(parents=True, exist_ok=True)
        with self._lock, self.audit_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")

    def send(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        text = str(payload.get("text", ""))
        if not text.strip():
            raise ValueError("text is required")
        explicit_target = payload.get("target")
        if explicit_target:
            # 显式目标（session/member/group），跳过 @mention 解析
            targets = self.explicit_targets(str(payload.get("target_type", "member")), str(explicit_target))
            body, mentions = text, []
            group_id = str(explicit_target) if payload.get("target_type") == "group" else None
        else:
            targets, body, mentions = self.resolve_targets(text)
            group_id = next((m for m in mentions if m.lower().startswith("team")), None)
        if not targets:
            raise ValueError("no registered target")
        dry_run = bool(payload.get("dry_run", True))
        confirmed = bool(payload.get("confirm", False))
        if not dry_run and not confirmed:
            raise PermissionError("explicit confirm=true is required")
        records = []
        for member in targets:
            session_id = member.get("daemon_session_id") or member.get("session_id")
            if self.is_stale(member):
                state, error = "rejected_stale", "stale session"
            elif dry_run:
                state, error = "dry_run", None
            else:
                try:
                    result = self._post_prompt(session_id, body)
                    state, error = "sent", None
                except Exception as exc:
                    result, state, error = None, "failed", type(exc).__name__
            record = {"message_id": str(uuid.uuid4()), "timestamp": now_iso(), "source": "controller",
                      "sender": str(payload.get("sender", "SignL3")),
                      "target_type": "group" if group_id else "member",
                      "target": member.get("id") or member.get("role"), "group_id": group_id,
                      "session_id": session_id, "text_preview": preview(body), "text_sha256": text_hash(body),
                      "state": state, "error": error}
            self.write_audit(record)
            records.append(record)
        return {"ok": True, "dry_run": dry_run, "mentions": mentions, "targets": records}

    def _post_prompt(self, session_id: str, text: str) -> Any:
        # daemon v2 协议要求 prompt 为 content-block 数组，不能发送裸字符串。
        return self.http_post(f"/session/{quote(session_id, safe='')}/prompt",
                              {"prompt": [{"type": "text", "text": text}]})


class HourlyTracker:
    """按小时聚合 chat 文件 api_response 事件并分时计价（增量解析 + 落盘状态）。

    数据源：chats/*.jsonl 中 subtype=ui_telemetry 且 event.name=qwen-code.api_response
    的记录（含 event.timestamp / model / input_token_count / output_token_count /
    cached_content_token_count / thoughts_token_count）。
    - 增量解析：按「文件字节断点 + size/mtime」判定变化，只读新增字节；文件被截断/重写时
      清空该文件桶并全量重扫。
    - 去重：同 response_id 在本次运行窗口内只计一次（镜像双写保护）。
    - 分时计价：按北京时间小时判定 peak/off-peak，费用 = 缓存命中输入 + 未命中输入 + 输出
      （输出含思考 token），USD/CNY 分别按官方分时价表。
    - 状态落盘（per_file_buckets + 断点），重启后无需全扫。
    """

    def __init__(self, chats_dir: Path, state_path: Path,
                 target_provider: Callable[[], list[tuple[str, str]]]):
        self.chats_dir = Path(chats_dir)
        self.state_path = Path(state_path)
        self.target_provider = target_provider
        self._lock = threading.Lock()
        self._files: dict[str, dict[str, Any]] = {}        # basename -> {size, mtime_ns, offset}
        self._per_file: dict[str, dict[str, dict[str, dict[str, int]]]] = {}
        # basename -> hour_key(UTC) -> model -> {input, cached, output, count}
        self._seen_ids: set[str] = set()                    # 本次运行窗口内已计 response_id
        self._file_ids: dict[str, set[str]] = {}            # basename -> 该文件贡献的 response_id
        self._loaded = False
        self._dirty = False

    # ---------------- 状态读写 ----------------

    def _load(self) -> None:
        if self._loaded:
            return
        state = load_json(self.state_path, None)
        if isinstance(state, dict):
            self._files = state.get("files") or {}
            self._per_file = state.get("per_file_buckets") or {}
        self._loaded = True

    def _save(self) -> None:
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {"version": 1, "updated_at": now_iso(),
                       "files": self._files, "per_file_buckets": self._per_file}
            tmp = self.state_path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, self.state_path)
        except OSError:
            pass

    # ---------------- 解析 ----------------

    @staticmethod
    def _parse_ts(value: Any) -> Optional[dt.datetime]:
        """解析 ISO 时间戳（容忍 Z / +HHMM 无冒号 / 无时区按 UTC）。"""
        if not value:
            return None
        text = str(value)
        try:
            if text.endswith("Z"):
                return dt.datetime.fromisoformat(text[:-1] + "+00:00")
            if re.search(r"[+-]\d{4}$", text):
                text = text[:-2] + ":" + text[-2:]
            parsed = dt.datetime.fromisoformat(text)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=dt.timezone.utc)
            return parsed
        except ValueError:
            return None

    @staticmethod
    def _is_peak(local_hour: int) -> bool:
        """北京时区小时是否高峰（9-12、14-18 点，含下界不含上界）。"""
        return (9 <= local_hour < 12) or (14 <= local_hour < 18)

    @staticmethod
    def _bucket_cost(model: str, toks: Mapping[str, int], peak: bool) -> tuple[float, float]:
        """单模型单小时桶费用（USD, CNY）；思考 token 已并入 output。GPT 订阅模型计 0。"""
        usd_p = (DS_PEAK_USD if peak else DS_PRICE_USD).get(model)
        cny_p = (DS_PEAK_CNY if peak else DS_PRICE_CNY).get(model)
        if not usd_p or not cny_p:
            return 0.0, 0.0
        miss = max(0, int(toks.get("input") or 0) - int(toks.get("cached") or 0))
        cached = int(toks.get("cached") or 0)
        out = int(toks.get("output") or 0)
        usd = (cached / 1e6 * usd_p["input_cache_hit"] + miss / 1e6 * usd_p["input_cache_miss"]
               + out / 1e6 * usd_p["output"])
        cny = (cached / 1e6 * cny_p["input_cache_hit"] + miss / 1e6 * cny_p["input_cache_miss"]
               + out / 1e6 * cny_p["output"])
        return usd, cny

    def _ingest(self, sid: str, rec: Mapping[str, Any]) -> None:
        """解析单条记录并入小时桶。"""
        if rec.get("subtype") != "ui_telemetry":
            return
        ev = (rec.get("systemPayload") or {}).get("uiEvent") or {}
        if not isinstance(ev, dict) or ev.get("event.name") != "qwen-code.api_response":
            return
        ts = self._parse_ts(ev.get("event.timestamp"))
        if ts is None:
            return
        model = str(ev.get("model") or "")
        if not model:
            return
        rid = str(ev.get("response_id") or "")
        if rid:
            if rid in self._seen_ids:
                return  # 镜像/重复记录去重
            self._seen_ids.add(rid)
        inp = int(ev.get("input_token_count") or 0)
        out = int(ev.get("output_token_count") or 0)
        cached = int(ev.get("cached_content_token_count") or 0)
        thoughts = int(ev.get("thoughts_token_count") or 0)
        if inp <= 0 and out <= 0 and thoughts <= 0:
            return
        hour_key = ts.replace(minute=0, second=0, microsecond=0).isoformat()
        bucket = (self._per_file.setdefault(sid, {}).setdefault(hour_key, {})
                  .setdefault(model, {"input": 0, "cached": 0, "output": 0, "count": 0}))
        bucket["input"] += inp
        bucket["cached"] += cached
        bucket["output"] += out + thoughts     # 思考 token 按输出价计费
        bucket["count"] += 1
        self._dirty = True

    def _scan_bytes(self, fp: Path, offset: int, sid: str) -> int:
        """从字节断点读取新增内容，返回已消费字节数（尾部未完成行不消费）。"""
        with fp.open("rb") as fh:
            fh.seek(offset)
            data = fh.read()
        parts = data.split(b"\n")
        complete = parts[:-1]                  # 最后一段可能是未完成行
        consumed = sum(len(p) + 1 for p in complete)
        for part in complete:
            if not part.strip():
                continue
            try:
                rec = json.loads(part.decode("utf-8", "replace"))
            except (ValueError, TypeError):
                continue
            if not isinstance(rec, dict):
                continue
            ev = (rec.get("systemPayload") or {}).get("uiEvent") or {}
            if isinstance(ev, dict) and ev.get("response_id"):
                self._file_ids.setdefault(sid, set()).add(str(ev["response_id"]))
            self._ingest(sid, rec)
        return consumed

    def _prune(self) -> None:
        cutoff = (dt.datetime.now(dt.timezone.utc)
                  - dt.timedelta(hours=HOURLY_KEEP_HOURS)).replace(minute=0, second=0, microsecond=0)
        cutoff_key = cutoff.isoformat()
        for sid in list(self._per_file):
            hours = self._per_file[sid]
            for hk in list(hours):
                if hk < cutoff_key:
                    del hours[hk]
            if not hours:
                del self._per_file[sid]

    # ---------------- 对外接口 ----------------

    def refresh(self) -> dict[str, Any]:
        """增量扫描目标 session 的 chat 文件；返回扫描统计。"""
        with self._lock:
            self._load()
            targets = self.target_provider()
            scanned = new_events = 0
            for sid, _name in targets:
                fp = self.chats_dir / f"{sid}.jsonl"
                if not fp.exists():
                    continue
                try:
                    st = fp.stat()
                except OSError:
                    continue
                key = fp.name
                cp = self._files.get(key)
                if cp and cp.get("size") == st.st_size and cp.get("mtime_ns") == st.st_mtime_ns:
                    continue  # 文件未变化，跳过
                if cp and st.st_size < cp.get("size", 0):
                    # 文件被截断/重写：移除该文件桶与 response_id，全量重扫
                    self._per_file.pop(sid, None)
                    self._files.pop(key, None)
                    removed = self._file_ids.pop(sid, set())
                    self._seen_ids -= removed
                    cp = None  # 强制从字节 0 全量重扫
                offset = cp.get("offset", 0) if cp else 0
                consumed = self._scan_bytes(fp, offset, sid)
                new_events += consumed
                scanned += 1
                self._files[key] = {"size": st.st_size, "mtime_ns": st.st_mtime_ns,
                                    "offset": offset + consumed}
            self._prune()
            if self._dirty:
                self._save()
                self._dirty = False
            return {"targets": len(targets), "scanned": scanned, "new_events": new_events}

    def report(self) -> dict[str, Any]:
        """最近 24h 每小时分布 + 今日（北京日）peak/off-peak 费用拆分。"""
        self.refresh()
        with self._lock:
            merged: dict[str, dict[str, dict[str, int]]] = {}
            for sid, hours in self._per_file.items():
                for hk, models in hours.items():
                    target = merged.setdefault(hk, {})
                    for model, toks in models.items():
                        b = target.setdefault(model, {"input": 0, "cached": 0, "output": 0, "count": 0})
                        for k in ("input", "cached", "output", "count"):
                            b[k] += toks[k]
            if not merged:
                return {"ok": False, "source": "chat_api_response",
                        "error": "no api_response data in window"}
            local_now = dt.datetime.now(dt.timezone.utc) + LOCAL_TZ_OFFSET
            local_hour = local_now.replace(minute=0, second=0, microsecond=0)

            hourly: list[dict[str, Any]] = []
            for i in range(23, -1, -1):
                lh = local_hour - dt.timedelta(hours=i)
                utc_key = (lh - LOCAL_TZ_OFFSET).isoformat()
                models = merged.get(utc_key) or {}
                peak = self._is_peak(lh.hour)
                in_t = sum(m["input"] for m in models.values())
                out_t = sum(m["output"] for m in models.values())
                cac_t = sum(m["cached"] for m in models.values())
                usd = cny = 0.0
                per_model: dict[str, Any] = {}
                for model, toks in models.items():
                    u, c = self._bucket_cost(model, toks, peak)
                    usd += u
                    cny += c
                    per_model[model] = {"input": toks["input"], "output": toks["output"],
                                        "cached": toks["cached"], "count": toks["count"],
                                        "cost_usd": round(u, 4), "cost_cny": round(c, 4)}
                hourly.append({"hour": lh.strftime("%m-%d %H:00"), "utc": utc_key,
                               "is_peak": peak, "requests": sum(m["count"] for m in models.values()),
                               "input_tokens": in_t, "output_tokens": out_t, "cached_tokens": cac_t,
                               "total_tokens": in_t + out_t,
                               "cost_usd": round(usd, 4), "cost_cny": round(cny, 4),
                               "models": per_model})

            # 今日（北京日 00:00 起）peak/off-peak 拆分
            today_start_local = local_hour - dt.timedelta(hours=local_hour.hour)
            today_utc_start = (today_start_local - LOCAL_TZ_OFFSET).isoformat()
            peak_usd = peak_cny = off_usd = off_cny = 0.0
            t_in = t_cac = t_out = t_cnt = 0
            today_models: dict[str, Any] = {}
            for hk, models in merged.items():
                if hk < today_utc_start:
                    continue
                lh = self._parse_ts(hk) + LOCAL_TZ_OFFSET
                peak = self._is_peak(lh.hour)
                for model, toks in models.items():
                    u, c = self._bucket_cost(model, toks, peak)
                    tm = today_models.setdefault(model, {
                        "input": 0, "cached": 0, "output": 0, "count": 0,
                        "cost_usd": 0.0, "cost_cny": 0.0,
                        "cost_peak_usd": 0.0, "cost_peak_cny": 0.0,
                        "cost_offpeak_usd": 0.0, "cost_offpeak_cny": 0.0})
                    tm["input"] += toks["input"]; tm["cached"] += toks["cached"]
                    tm["output"] += toks["output"]; tm["count"] += toks["count"]
                    tm["cost_usd"] += u; tm["cost_cny"] += c
                    t_in += toks["input"]; t_cac += toks["cached"]
                    t_out += toks["output"]; t_cnt += toks["count"]
                    if peak:
                        peak_usd += u; peak_cny += c
                        tm["cost_peak_usd"] += u; tm["cost_peak_cny"] += c
                    else:
                        off_usd += u; off_cny += c
                        tm["cost_offpeak_usd"] += u; tm["cost_offpeak_cny"] += c
            for tm in today_models.values():
                for k in ("cost_usd", "cost_cny", "cost_peak_usd", "cost_peak_cny",
                          "cost_offpeak_usd", "cost_offpeak_cny"):
                    tm[k] = round(tm[k], 4)
            return {
                "ok": True, "source": "chat_api_response",
                "generated_at": now_iso(),
                "window": {"keep_hours": HOURLY_KEEP_HOURS,
                           "peak_hours": "北京时间 9:00-12:00 / 14:00-18:00（off-peak 半价）"},
                "hourly": hourly,
                "today": {"input_tokens": t_in, "cached_tokens": t_cac,
                          "output_tokens": t_out, "requests": t_cnt,
                          "cost_usd": round(peak_usd + off_usd, 4),
                          "cost_cny": round(peak_cny + off_cny, 4),
                          "cost_peak_usd": round(peak_usd, 4), "cost_peak_cny": round(peak_cny, 4),
                          "cost_offpeak_usd": round(off_usd, 4), "cost_offpeak_cny": round(off_cny, 4),
                          "models": today_models},
            }


HTML = """<!doctype html><meta charset=utf-8><title>daemon team console v2</title>
<h1>daemon team console v2</h1><p>127.0.0.1 控制面；默认只读。</p><script>
fetch('/api/dashboard').then(r=>r.json()).then(x=>document.body.insertAdjacentHTML('beforeend','<pre>'+JSON.stringify(x,null,2)+'</pre>'))
</script>"""


class Handler(BaseHTTPRequestHandler):
    state = V2State()
    server_version = "daemon-team-console-v2"

    def _json(self, value: Any, status: int = 200) -> None:
        data = json.dumps(value, ensure_ascii=False).encode("utf-8")
        try:
            self.send_response(status); self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache"); self.send_header("Expires", "0")
            self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError, OSError):
            # 客户端提前断开：写错误不是服务错误，直接忽略，避免二次写错误/traceback 刷屏
            pass

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path.strip("/").split("/")
        try:
            if len(path) == 4 and path[:2] == ["api", "sessions"] and path[3] == "events":
                session_id = path[2]; self.state.session_member(session_id)
                headers = {"Accept": "text/event-stream"}
                for key in ("Last-Event-ID", "X-Qwen-Event-Epoch"):
                    if self.headers.get(key): headers[key] = self.headers[key]
                upstream = self.state.http_stream(f"/session/{quote(session_id, safe='')}/events", headers)
                self.send_response(200); self.send_header("Content-Type", "text/event-stream; charset=utf-8")
                self.send_header("Cache-Control", "no-cache"); self.send_header("Connection", "keep-alive"); self.end_headers()
                try:
                    # [20260827] SSE 转发合并缓冲：原每块立即 write+flush（上游每块数据
                    # 一次系统调用），多面板并发时系统调用风暴 → 8466 高 CPU/看板卡。
                    # 改为 ≥8KB 或 ≥50ms 批量 flush（SSE 事件实时性不受影响，延迟 <50ms 无感）
                    buf = bytearray()
                    last_flush = time.monotonic()
                    for chunk in upstream:
                        if isinstance(chunk, str):
                            chunk = chunk.encode("utf-8")
                        buf += chunk
                        now = time.monotonic()
                        if len(buf) >= 8192 or (now - last_flush) >= 0.05:
                            self.wfile.write(bytes(buf))
                            self.wfile.flush()
                            buf.clear()
                            last_flush = now
                    if buf:
                        self.wfile.write(bytes(buf))
                        self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError, OSError):
                    pass
                finally:
                    close = getattr(upstream, "close", None)
                    if close: close()
                return
            if self.path in ("/", "/index.html") or not path[0]:
                index_path = self.state.v2 / "index.html"
                data = index_path.read_bytes() if index_path.exists() else HTML.encode()
                status, typ = 200, "text/html; charset=utf-8"
            elif path == ["api", "health"]:
                data, status, typ = json.dumps({"ok": True, "service": "daemon-team-console-v2", "bind": "127.0.0.1"}).encode(), 200, "application/json"
            elif path == ["api", "dashboard"]:
                result = self.state.dashboard()
                result["ok"] = True
                result["groups"] = self.state.groups()
                if not result.get("members"):
                    result["members"] = self.state.members()
                if not result.get("activity"):
                    result["activity"] = result.get("messages") or []
                # user_online：以 v2 实时判定为准（v1 dashboard_data.json 的 user_online 恒为 False）
                online = self.state.user_online_status()
                result["user_online"] = online.get("online", False)
                result["user_online_details"] = online
                data, status, typ = json.dumps(result, ensure_ascii=False).encode(), 200, "application/json"
            elif path == ["api", "local", "services", "health"]:
                data, status, typ = json.dumps(self.state.local_services(), ensure_ascii=False).encode(), 200, "application/json"
            elif path == ["api", "members"]:
                data, status, typ = json.dumps({"members": self.state.members()}, ensure_ascii=False).encode(), 200, "application/json"
            elif len(path) == 3 and path[:2] == ["api", "members"]:
                member = self.state.member(path[2]); data, status, typ = json.dumps(member or {"error": "member not found"}, ensure_ascii=False).encode(), (200 if member else 404), "application/json"
            elif len(path) == 4 and path[:2] == ["api", "sessions"] and path[3] == "live":
                data, status, typ = json.dumps(self.state.live_session(path[2]), ensure_ascii=False).encode(), 200, "application/json"
            elif len(path) == 4 and path[:2] == ["api", "sessions"] and path[3] == "transcript_latest":
                data, status, typ = json.dumps(self.state.transcript_latest(path[2]), ensure_ascii=False).encode(), 200, "application/json"
            elif len(path) == 4 and path[:2] == ["api", "sessions"] and path[3] in {"status", "context", "transcript", "context-usage"}:
                data, status, typ = json.dumps(self.state.daemon_session(path[2], path[3]), ensure_ascii=False).encode(), 200, "application/json"
            elif path == ["api", "groups"]:
                data, status, typ = json.dumps({"groups": self.state.groups()}, ensure_ascii=False).encode(), 200, "application/json"
            elif len(path) == 4 and path[:2] == ["api", "groups"] and path[3] == "messages":
                gid = path[2]; rows = []
                if self.state.audit_path.exists():
                    for line in self.state.audit_path.read_text(encoding="utf-8").splitlines():
                        try:
                            row = json.loads(line)
                            if row.get("group_id") == gid: rows.append(row)
                        except ValueError: continue
                data, status, typ = json.dumps({"group_id": gid, "messages": rows}, ensure_ascii=False).encode(), 200, "application/json"
            elif path == ["api", "shell-url"]:
                shell = DEFAULT_DAEMON_URL.rstrip("/") + "/"
                token = load_token()
                if token:
                    shell += "#token=" + token
                data, status, typ = json.dumps({"ok": True, "shell_url": shell}).encode(), 200, "application/json"
            elif path == ["api", "local", "status"]:
                # 本地数据源：读 message_supervisor.json；user_online 为共享缓存判定
                # （daemon 探测失败时回退 registry 新鲜度，不阻塞本地状态返回）
                result = self.state.local_status()
                online = self.state.user_online_status()
                result["user_online"] = online.get("online", False)
                result["user_online_details"] = online
                data, status, typ = json.dumps(result, ensure_ascii=False).encode(), 200, "application/json"
            elif path == ["api", "local", "work-states"]:
                # 工作状态判定（prefilling / stalled / idle / error），带短 TTL 缓存
                result = self.state.work_states()
                data, status, typ = json.dumps(result, ensure_ascii=False).encode(), 200, "application/json"
            elif path == ["api", "local", "gpu-live"]:
                # 实时 GPU 抓取（SSH → zhuhai nvidia-smi）+ 成员→模型→GPU 关联
                result = self.state.gpu_live()
                data, status, typ = json.dumps(result, ensure_ascii=False).encode(), 200, "application/json"
            elif path == ["api", "local", "host-resources"]:
                # 本机 CPU/内存总量使用率（≤20% 绿 / >20% 红的预警判定在前端）
                data, status, typ = json.dumps(self.state.host_resources(), ensure_ascii=False).encode(), 200, "application/json"
            elif path == ["api", "local", "messages"]:
                result = self.state.local_messages()
                data, status, typ = json.dumps(result, ensure_ascii=False).encode(), 200, "application/json"
            elif path == ["api", "local", "chat"]:
                qs = parse_qs(urlparse(self.path).query)
                role = (qs.get("role") or [""])[0]
                result = self.state.local_chat(role) if role else {"ok": False, "source": "local", "role": role, "error": "role query parameter is required"}
                data, status, typ = json.dumps(result, ensure_ascii=False).encode(), 200, "application/json"
            elif path == ["api", "local", "api-usage"]:
                # API 用量追踪：今日/趋势/成员分布（daemon 精确统计 + DeepSeek 参考价估算费用）
                data, status, typ = json.dumps(self.state.api_usage(), ensure_ascii=False).encode(), 200, "application/json"
            elif path == ["api", "dsv4"]:
                # dsv4flash 实时性能（代理到 zhuhai 8096 监测服务）
                data, status, typ = json.dumps(self.state.dsV4_status(), ensure_ascii=False).encode(), 200, "application/json"
            elif path == ["api", "local", "services", "meta"]:
                # 本地模型服务元信息（topology：模型名/别名/GPU/类型）
                data, status, typ = json.dumps(self.state.local_services_meta(), ensure_ascii=False).encode(), 200, "application/json"
            else:
                data, status, typ = json.dumps({"error": "not found"}).encode(), 404, "application/json"
            try:
                self.send_response(status); self.send_header("Content-Type", typ)
                self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
                self.send_header("Pragma", "no-cache"); self.send_header("Expires", "0")
                self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass  # 客户端提前断开（浏览器刷新/关页）：忽略写错误，避免 traceback
        except Exception as exc:
            self._json({"ok": False, "error": str(exc)}, 500)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path).path.strip("/").split("/")
        if len(parsed) == 4 and parsed[:2] == ["api", "sessions"] and parsed[3] in {"load", "cancel"}:
            try:
                length = int(self.headers.get("Content-Length", "0")); payload = json.loads(self.rfile.read(length) or b"{}")
                self._json(self.state.session_action(parsed[2], parsed[3], payload), 200)
            except ValueError as exc: self._json({"ok": False, "error": str(exc)}, 400)
            except Exception as exc: self._json({"ok": False, "error": str(exc)}, 403)
            return
        if urlparse(self.path).path != "/api/messages": self._json({"error": "not found"}, 404); return
        try:
            length = int(self.headers.get("Content-Length", "0")); payload = json.loads(self.rfile.read(length) or b"{}")
            self._json(self.state.send(payload), 200)
        except PermissionError as exc: self._json({"ok": False, "error": str(exc)}, 403)
        except ValueError as exc: self._json({"ok": False, "error": str(exc)}, 400)
        except Exception as exc: self._json({"ok": False, "error": str(exc)}, 500)

    def log_message(self, *_args: Any) -> None: return


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--host", default="127.0.0.1"); parser.add_argument("--port", type=int, default=8466); args = parser.parse_args()
    if args.host != "127.0.0.1":
        parser.error("v2 control service only permits --host 127.0.0.1")
    Handler.state = V2State(); Handler.state.start_sse_activity_monitor()  # 方案D：SSE 真实活动监控
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"daemon team console v2 listening on http://{args.host}:{args.port}", flush=True); server.serve_forever()


if __name__ == "__main__": main()

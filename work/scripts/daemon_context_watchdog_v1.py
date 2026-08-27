#!/usr/bin/env python3
"""daemon 版团队健康 watchdog v1：小上下文模型场景的 context 健康监督 + 自动两级压缩。

背景（2026-08-25 Owner 要求）：
- 团队会话切到小上下文模型（qwen3.8-27b，256K 窗口）后，context 超限报错
  （prompt is too long / context length exceeded / context overflow 等）会让
  会话卡死在 turn error 状态，需要人工发现并手动 /compress。
- 本服务是 daemon 版常驻健康监督（旧 tmux 版 team_health_monitor.py 只覆盖
  tmux 窗口，daemon 迁移后团队会话都在 4194，tmux 版覆盖不到）。

监护对象：
- `.team/daemon_v1/registry.json` 中的全部团队角色会话（SignL3 + signL2..signL11）。
- Jarvis（Owner 私人代理，channel 会话）是 team 外关联角色，不在 registry roles 中，
  天然不纳入监护（也不应为其发消息打扰）。

检测与自愈：
1. context 超限报错：GET /session/:id/status 的 hasTurnError=true →
   读会话 transcript 尾部（仅最后 512KB，不扫全文件）确认是 context 类报错 →
   会话空闲（无 active prompt、无等待交互）且冷却期外 → 自动两级压缩：
     a) POST /session/:id/prompt  {"prompt":[{"type":"text","text":"/compress-fast"}]}
        （无 AI 快速压缩，剥离旧 tool 输出/思考）
     b) 轮询 status 等 turn 完成（超时 600s）
     c) 再发 "/compress"（AI 摘要压缩），等 turn 完成（超时 900s）
   任一阶段失败/超时 → 停止后续阶段并告警；同一会话冷却 10 分钟防压缩死循环；
   1 小时内 3 次无效压缩 → 停止自愈，转人工介入队列。
2. 会话死亡/失联：status 返回 session_not_found →
   若 workspace 列表仍有该会话（daemon 重启后未载入 runtime）→ 自动
   POST /session/:id/resume 自愈（2026-08-25 本地B 实例）；列表也没有 → 告警。
3. helper 死亡：members/<role>/helper_health.json 的 updated_at 超过 90s →
   告警（消息通道失联，需运维重启 helper）。
4. context 水位预警（主动）：每 60s 轮询一次 /session/:id/context-usage，
   currentTier 进入 warn/auto/hard → 告警一次（回落 safe 前不重复）。

输出：
- 状态：.team/daemon_v1/context_watchdog_state.json（每角色明细 + 心跳）
- 日志：.team/daemon_v1/context_watchdog.log
- 告警：追加 .team/team_messages.log（【自动健康告警】前缀，与 tmux 版格式一致，
  由 team_message_monitor 转发提醒主管）

保活：tmux 会话 slu-team-context-watchdog 运行（与 slu-team-health 同惯例）。

用法：
    python3 daemon_context_watchdog_v1.py --interval 10
    python3 daemon_context_watchdog_v1.py --once            # 单周期（调试）
    python3 daemon_context_watchdog_v1.py --dry-run         # 只检测不执行压缩/resume
    python3 daemon_context_watchdog_v1.py --only signL10    # 只监护指定角色
"""
from __future__ import annotations

import argparse
import json
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
STATE = OUT_DIR / "context_watchdog_state.json"
LOG = OUT_DIR / "context_watchdog.log"
TEAM_MESSAGES = BASE / "team_messages.log"
INTERVENTION_QUEUE = BASE / "team_intervention_queue.json"
MEMBERS_DIR = OUT_DIR / "members"
CHATS_DIR = Path("/home/wuyangcheng/.qwen/projects/-data-WYC-signLanguage/chats")

DAEMON_URL = "http://127.0.0.1:4194"
WORKSPACE = "/data/WYC/signLanguage"

# context 超限报错标记（transcript 尾部命中任一即判定为 context 类 turn error）。
# 来源：上游 API（prompt is too long / maximum context length）、
# qwen-code 内部（Context length exceeded; attempting reactive compression /
# Reactive compression already attempted; propagating the context overflow error）。
CONTEXT_ERROR_MARKS = (
    "prompt is too long",
    "context length exceeded",
    "context overflow",
    "context oversized",
    "maximum context length",
    "exceeds the model's maximum",
    "reduce the length",
    "too many tokens",
    "reactive compression",
)

TRANSCRIPT_TAIL_BYTES = 512 * 1024   # 只读 transcript 尾部，避免大文件全扫（曾 120s 超时）
RECOVERY_COOLDOWN_SECONDS = 600      # 同一会话两次自动压缩的最小间隔
INEFFECTIVE_WINDOW_SECONDS = 3600    # "无效压缩"统计窗口
INEFFECTIVE_LIMIT = 3                # 窗口内无效压缩次数上限，超过转人工
FAST_TIMEOUT_SECONDS = 600           # /compress-fast turn 完成超时
COMPRESS_TIMEOUT_SECONDS = 900       # /compress turn 完成超时
HELPER_STALE_SECONDS = 90            # helper 健康文件超时阈值
USAGE_POLL_SECONDS = 60              # context-usage 轮询间隔（每角色）
STATUS_POLL_SECONDS = 5              # 等 turn 完成的轮询间隔
ALERT_SUPPRESS_SECONDS = 1800        # 同类告警抑制窗口


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def log(msg: str) -> None:
    line = f"[{now_iso()}] {msg}"
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line, flush=True)


def alert(role: str, kind: str, detail: str) -> None:
    """告警：写 team_messages.log（共享通道，message monitor 会转发提醒主管）。"""
    line = f"[{now_iso()}] 【自动健康告警】daemon-watchdog | 角色: {role} | 类型: {kind} | 详情: {detail[:300]}"
    with TEAM_MESSAGES.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    log(f"[ALERT] {role} {kind}: {detail[:200]}")


def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def http_json(method: str, path: str, body: dict | None = None, timeout: float = 10.0) -> tuple[int, dict]:
    """daemon HTTP 请求；返回 (status_code, parsed_json)。404 也解析 body。"""
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


def session_in_list(session_id: str) -> bool:
    """workspace 会话列表里是否还有该会话（daemon 重启后可能只在磁盘索引、未载入 runtime）。"""
    code, data = http_json("GET", f"/workspace/{urllib.parse.quote(WORKSPACE, safe='')}/sessions?limit=100")
    if code != 200:
        return False
    return any(s.get("sessionId") == session_id for s in data.get("sessions", []))


def resume_session(session_id: str) -> tuple[int, dict]:
    return http_json("POST", f"/session/{urllib.parse.quote(session_id, safe='')}/resume",
                     {"cwd": WORKSPACE})


def send_prompt(session_id: str, text: str) -> tuple[int, dict]:
    """daemon v2 协议：prompt 必须是 content-block 数组（与 console v2 _post_prompt 一致）。"""
    return http_json("POST", f"/session/{urllib.parse.quote(session_id, safe='')}/prompt",
                     {"prompt": [{"type": "text", "text": text}]}, timeout=30.0)


def wait_turn_complete(session_id: str, timeout: float) -> tuple[bool, str]:
    """轮询 status 等 turn 结束。返回 (是否干净完成, 说明)。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        code, st = session_status(session_id)
        if code == 404:
            return False, "session_not_found during wait"
        if code == 200:
            if st.get("hasTurnError"):
                return False, "turn_error during compress"
            if not st.get("hasActivePrompt"):
                return True, "completed"
        time.sleep(STATUS_POLL_SECONDS)
    return False, f"timeout after {timeout:.0f}s"


def transcript_tail_has_context_error(session_id: str) -> str:
    """读 transcript 尾部 512KB，返回命中的 context 报错标记（无则空串）。不扫全文件。"""
    path = CHATS_DIR / f"{session_id}.jsonl"
    try:
        size = path.stat().st_size
        with path.open("rb") as f:
            f.seek(max(0, size - TRANSCRIPT_TAIL_BYTES))
            tail = f.read().decode("utf-8", errors="ignore").lower()
    except OSError:
        return ""
    for mark in CONTEXT_ERROR_MARKS:
        if mark in tail:
            return mark
    return ""


def queue_intervention(role: str, detail: str) -> None:
    """转人工介入队列（与 tmux 版同一队列文件，monitor/主管可见）。"""
    queue = read_json(INTERVENTION_QUEUE, [])
    if not isinstance(queue, list):
        queue = []
    queue.append({
        "id": f"watchdog-{int(time.time())}",
        "window": f"daemon:{role}",
        "task": f"daemon context watchdog 自愈失败，需人工处理：{detail[:200]}",
        "path": str(STATE),
        "status": "waiting",
        "created_at": now_iso(),
        "completed_at": None,
    })
    INTERVENTION_QUEUE.write_text(json.dumps(queue, ensure_ascii=False, indent=1), encoding="utf-8")


def two_stage_compress(role: str, session_id: str, dry_run: bool) -> dict:
    """两级压缩：/compress-fast → 等完成 → /compress → 等完成；压缩成功后补发「继续」prompt，
    让因上下文超限被打断的任务自动恢复。返回结果记录（continue_sent 标记补发是否成功）。"""
    result = {"role": role, "started_at": now_iso(), "stages": []}
    if dry_run:
        result.update({"dry_run": True, "ok": True, "note": "dry-run 跳过实际压缩"})
        return result
    # 阶段 1：快速压缩（无 AI）
    log(f"[{role}] 发送 /compress-fast")
    code, resp = send_prompt(session_id, "/compress-fast")
    if code not in (200, 202):
        result.update({"ok": False, "failed_stage": "compress-fast", "error": f"send failed: {resp}"})
        return result
    ok, why = wait_turn_complete(session_id, FAST_TIMEOUT_SECONDS)
    result["stages"].append({"cmd": "/compress-fast", "ok": ok, "why": why})
    if not ok:
        result.update({"ok": False, "failed_stage": "compress-fast", "error": why})
        return result
    # 阶段 2：AI 摘要压缩
    log(f"[{role}] /compress-fast 完成，发送 /compress")
    code, resp = send_prompt(session_id, "/compress")
    if code not in (200, 202):
        result.update({"ok": False, "failed_stage": "compress", "error": f"send failed: {resp}"})
        return result
    ok, why = wait_turn_complete(session_id, COMPRESS_TIMEOUT_SECONDS)
    result["stages"].append({"cmd": "/compress", "ok": ok, "why": why})
    if ok:
        # 压缩成功：补发「继续」prompt，恢复之前被上下文超限打断的任务
        continue_text = ("【系统通知】你的上下文已自动压缩完成（compress-fast + compress）。"
                         "之前因上下文超限被打断的任务现在可以继续，请检查并继续完成未完成的工作。")
        ccode, cresp = send_prompt(session_id, continue_text)
        result["continue_sent"] = ccode in (200, 202)
        if not result["continue_sent"]:
            log(f"[{role}] 压缩成功但补发「继续」失败: {cresp}")
    else:
        result["continue_sent"] = False
    result.update({"ok": ok, "failed_stage": None if ok else "compress", "error": None if ok else why,
                   "finished_at": now_iso()})
    return result


def check_role(role: str, info: dict, mem: dict, args: argparse.Namespace,
               state: dict, ts: float) -> dict:
    """单角色一个检测周期。返回更新后的记忆 dict。"""
    session_id = info.get("session_id")
    name = info.get("name", role)
    if not session_id:
        return mem
    if args.only and role != args.only:
        return mem

    entry = state.setdefault(role, {"name": name, "session_id": session_id, "status": "unknown"})
    entry["checked_at"] = now_iso()

    # ---- 1. 会话存活 ----
    code, st = session_status(session_id)
    if code == 404:
        # daemon 重启后磁盘索引有、runtime 无 → resume 自愈
        if session_in_list(session_id):
            if args.dry_run:
                entry.update({"status": "resume_needed", "note": "dry-run 跳过 resume"})
            else:
                log(f"[{role}] 会话未载入 runtime，执行 resume 自愈")
                rcode, rresp = resume_session(session_id)
                if rcode in (200, 202):
                    entry.update({"status": "resumed", "resume_at": now_iso()})
                    alert(role, "会话失联自愈", f"daemon 重启后会话未载入 runtime，已自动 resume（{session_id[:8]}）")
                else:
                    entry.update({"status": "resume_failed", "note": str(rresp)[:200]})
                    if mem.get("last_alert_at", 0) and ts - mem["last_alert_at"] > ALERT_SUPPRESS_SECONDS:
                        alert(role, "会话失联且 resume 失败", f"{rresp}")
                        mem["last_alert_at"] = ts
            return mem
        entry.update({"status": "session_lost"})
        if mem.get("lost_alerted") != session_id:
            alert(role, "会话丢失", f"session {session_id[:8]} 在 daemon 中不存在且不在 workspace 列表")
            mem["lost_alerted"] = session_id
        return mem
    if code != 200:
        entry.update({"status": "status_error", "note": str(st)[:200]})
        return mem

    entry.update({
        "status": "alive",
        "has_active_prompt": st.get("hasActivePrompt", False),
        "has_turn_error": st.get("hasTurnError", False),
        "client_count": st.get("clientCount"),
    })

    # ---- 2. context 超限 turn error → 两级压缩自愈 ----
    if st.get("hasTurnError") and not st.get("hasActivePrompt") \
            and not st.get("isWaitingForPermission") and not st.get("isWaitingForUserQuestion"):
        mark = transcript_tail_has_context_error(session_id)
        if mark:
            last_attempt = mem.get("last_recovery_at", 0)
            if ts - last_attempt < RECOVERY_COOLDOWN_SECONDS:
                entry["status"] = "context_error_cooldown"
            else:
                mem["last_recovery_at"] = ts
                log(f"[{role}] 检测到 context 超限报错（{mark}），启动两级压缩")
                if not args.dry_run and mem.get("ineffective_count", 0) >= INEFFECTIVE_LIMIT:
                    entry.update({"status": "context_error_manual", "note": f"无效压缩达上限（{mark}）"})
                    alert(role, "context 超限且自愈已达上限", f"标记={mark}；1h 内 {INEFFECTIVE_LIMIT} 次压缩无效，转人工")
                    if not mem.get("intervention_queued"):
                        queue_intervention(role, f"context 超限（{mark}），自动两级压缩 {INEFFECTIVE_LIMIT} 次未恢复")
                        mem["intervention_queued"] = True
                else:
                    result = two_stage_compress(role, session_id, args.dry_run)
                    entry["last_recovery"] = result
                    if result.get("ok"):
                        # 压缩后若 turn error 仍在（说明压缩没解决问题）→ 记无效
                        time.sleep(STATUS_POLL_SECONDS)
                        _, st2 = session_status(session_id)
                        still = st2.get("hasTurnError", False) if st2.get("hasTurnError") is not None else False
                        if still:
                            mem["ineffective_events"] = [t for t in mem.get("ineffective_events", [])
                                                         if ts - t < INEFFECTIVE_WINDOW_SECONDS]
                            mem["ineffective_events"].append(ts)
                            mem["ineffective_count"] = len(mem["ineffective_events"])
                            entry["status"] = "compress_ineffective"
                            alert(role, "压缩后 turn error 仍在", f"标记={mark}；累计 {mem['ineffective_count']}/{INEFFECTIVE_LIMIT}")
                        else:
                            mem["ineffective_events"] = []
                            mem["ineffective_count"] = 0
                            entry["status"] = "recovered"
                            alert(role, "context 超限已自愈", f"标记={mark}；两级压缩完成，turn error 清除")
                    else:
                        entry["status"] = "compress_failed"
                        alert(role, "自动压缩失败", f"阶段={result.get('failed_stage')} 原因={result.get('error')}")
        else:
            entry["status"] = "turn_error_non_context"
            entry["note"] = "turn error 非 context 类（由 tmux 版/API 告警链路处理）"
    elif st.get("hasTurnError"):
        entry["status"] = "turn_error_busy"  # 有 error 但 turn 进行中/等待交互，等下一轮

    # ---- 3. context 水位预警（每 60s 一次）----
    if ts - mem.get("last_usage_check", 0) >= USAGE_POLL_SECONDS:
        mem["last_usage_check"] = ts
        ucode, udata = http_json("GET", f"/session/{urllib.parse.quote(session_id, safe='')}/context-usage")
        if ucode == 200:
            usage = udata.get("usage", {})
            breakdown = usage.get("breakdown", {}) if isinstance(usage, dict) else {}
            tier = breakdown.get("currentTier") or usage.get("currentTier")
            total = usage.get("totalTokens")
            window = usage.get("contextWindowSize")
            entry["context_usage"] = {"total": total, "window": window, "tier": tier}
            if tier in ("warn", "auto", "hard") and mem.get("warned_tier") != tier:
                mem["warned_tier"] = tier
                alert(role, "context 水位预警", f"tier={tier} total={total}/{window}（建议尽快 /compress-fast + /compress）")
            elif tier == "safe":
                mem.pop("warned_tier", None)
            # 主动自愈：hard 档（≈窗口 91%+）的空闲会话，下一个请求必然 context 超限失败 →
            # 立即两级压缩（/compress-fast 本地剥离旧 tool 输出不需要模型调用，能把上下文
            # 降到 /compress 可执行的范围；若仍超，/compress 失败走告警+冷却，不会更糟）。
            if (tier == "hard" and not st.get("hasActivePrompt")
                    and not st.get("isWaitingForPermission") and not st.get("isWaitingForUserQuestion")
                    and ts - mem.get("last_recovery_at", 0) >= RECOVERY_COOLDOWN_SECONDS
                    and mem.get("ineffective_count", 0) < INEFFECTIVE_LIMIT):
                mem["last_recovery_at"] = ts
                log(f"[{role}] hard 档空闲会话（{total}/{window}），主动两级压缩")
                result = two_stage_compress(role, session_id, args.dry_run)
                entry["last_recovery"] = result
                if result.get("ok"):
                    entry["status"] = "proactively_recovered"
                    mem["ineffective_events"] = []
                    mem["ineffective_count"] = 0
                    alert(role, "hard 档主动压缩完成", f"压缩前 total={total}/{window}；两级压缩成功，会话恢复可用")
                else:
                    entry["status"] = "compress_failed"
                    alert(role, "主动压缩失败", f"阶段={result.get('failed_stage')} 原因={result.get('error')}；tier={tier} total={total}/{window}")

    # ---- 4. helper 存活（消息通道）----
    health = read_json(MEMBERS_DIR / role / "helper_health.json", {})
    updated = health.get("updated_at")
    if isinstance(updated, (int, float)):
        age = ts - updated
        entry["helper_age_seconds"] = round(age, 1)
        if age > HELPER_STALE_SECONDS and not mem.get("helper_alerted"):
            mem["helper_alerted"] = True
            alert(role, "helper 失联", f"helper_health.json 已 {age:.0f}s 未更新，消息通道可能断裂，请运维重启 helper")
    else:
        entry["helper_age_seconds"] = None
        mem["helper_alerted"] = False

    # helper 恢复新鲜后重置告警标记（下次再失联可重新告警）
    if isinstance(updated, (int, float)) and ts - updated <= HELPER_STALE_SECONDS:
        mem.pop("helper_alerted", None)
    return mem


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="daemon 版团队 context 健康 watchdog v1")
    ap.add_argument("--interval", type=float, default=10.0, help="检测周期（秒）")
    ap.add_argument("--once", action="store_true", help="只跑一个周期（调试）")
    ap.add_argument("--dry-run", action="store_true", help="只检测，不执行压缩/resume")
    ap.add_argument("--only", default=None, help="只监护指定角色 id（调试）")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    log(f"watchdog 启动 interval={args.interval}s dry_run={args.dry_run} only={args.only}")
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
                memories[role] = check_role(role, info, memories.get(role, {}), args, state, ts)
            except Exception as exc:  # 单角色异常不影响其他角色
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

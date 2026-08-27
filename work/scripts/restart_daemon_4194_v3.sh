#!/bin/bash
# 重启 daemon（默认 4194）保持 session 工作连续性 v3（2026-08-27）
# 用法: bash restart_daemon_4194_v3.sh [--port 4194] [--workspace /data/WYC/signLanguage] [--token xxx]
#       [--no-notify-waiting] [--dry-run]
#
# v3 相对 v2 的改进（工作连续性 + approval 等级）：
#   - ① 重启前捕捉工作状态：枚举全部 session，识别正在工作的（hasActivePrompt=true，
#     含 side_task/后台 sub 运行中）与等待输入的（isWaitingForUserQuestion/Permission），
#     连同模型、approval mode 一起写入快照 .team/daemon_v1/daemon_work_snapshot_restart.json
#   - ⑤ 恢复模型映射 + **approval mode**（POST /session/:id/approval-mode，之前 full access=yolo
#     的会话重启后保持 yolo，不会回落到需要审批的 default）
#   - ⑥ 重启完成后：对「被打断的工作 session」发送「继续完成」prompt，让成员自动恢复；
#     对「等待输入的 session」发送说明（等待状态已被重启清空），避免成员空等
#   - 支持 --port/--workspace/--token 参数化（用于独立测试实例验证，如 4195）
#   - --dry-run: 只执行 ① 捕捉与 ⑤ 恢复预演，不 kill/不启动/不发送（用于验证捕捉逻辑）
#
# 流程: ① 捕捉工作状态+记录模型与 mode → ② kill 旧 daemon → ③ setsid 保活重启
#       → ④ 等待就绪 → ⑤ 恢复模型+approval mode（lazy 会话先 load）→ ⑥ 发送继续完成 → ⑦ 验证
set -uo pipefail
BASE="/data/WYC/signLanguage"
# STATE 可用环境变量覆盖（测试实例指向独立目录，避免污染生产快照/日志）
STATE="${STATE:-$BASE/.team/daemon_v1}"

# ── 参数解析（默认 4194 生产实例） ──
PORT="4194"; WORKSPACE="$BASE"; TOKEN=""; NOTIFY_WAITING="yes"; DRY_RUN="no"; CHANNEL="weixin"
while [ $# -gt 0 ]; do
  case "$1" in
    --port) PORT="$2"; shift 2 ;;
    --workspace) WORKSPACE="$2"; shift 2 ;;
    --token) TOKEN="$2"; shift 2 ;;
    --channel) CHANNEL="$2"; shift 2 ;;   # 传 none 表示不启用 channel（测试实例必须 none，否则与生产 weixin channel 冲突）
    --no-notify-waiting) NOTIFY_WAITING="no"; shift ;;
    --dry-run) DRY_RUN="yes"; shift ;;
    *) echo "未知参数: $1"; exit 2 ;;
  esac
done
[ -z "$TOKEN" ] && TOKEN=$(cat "$STATE/.daemon_token" 2>/dev/null || true)
DAEMON_URL="http://127.0.0.1:$PORT"
LOG="$BASE/work/logs/daemon_restart_4194.log"
MAPFILE="$STATE/daemon_model_map_restart.json"
PENDINGFILE="$STATE/daemon_model_pending_restore.json"
SNAPSHOT="$STATE/daemon_work_snapshot_restart.json"
CONTINUE_FILE="$STATE/daemon_continue_sent.json"
WS_ENC=$(python3 -c "import urllib.parse;print(urllib.parse.quote('$WORKSPACE', safe=''))")
TS=$(date '+%Y-%m-%d %H:%M:%S')
CHANNEL_ARGS=""
[ "$CHANNEL" != "none" ] && CHANNEL_ARGS="--channel $CHANNEL"

log() { echo "[$(date '+%Y-%m-%dT%H:%M:%S%z')] $*" | tee -a "$LOG"; }

# ── ① 捕捉工作状态 + 记录模型映射（一次枚举，两份产物） ──
log "① 捕捉工作状态（port=$PORT workspace=$WORKSPACE）..."
python3 - "$SNAPSHOT" "$MAPFILE" "$DAEMON_URL" "$TOKEN" "$WS_ENC" << 'PYEOF'
import json, sys, time, urllib.request, urllib.parse, urllib.error

snap_path, map_path, base, token, ws_enc = sys.argv[1:6]
headers = {"Authorization": f"Bearer {token}"} if token else {}
SESSIONS_URL = f"{base}/workspace/{ws_enc}/sessions?limit=100"

def _req(method: str, path: str, timeout: float = 6.0):
    req = urllib.request.Request(f"{base}{path}", headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()

def get_status(sid: str):
    try:
        _, raw = _req("GET", f"/session/{sid}/status", timeout=6)
        return json.loads(raw)
    except Exception:
        return None

def get_meta(sid: str):
    """返回 (model, approval_mode)，任一不可得则为 None。mode 从 configOptions id=mode 读取。"""
    try:
        _, raw = _req("GET", f"/session/{sid}/context", timeout=6)
        ctx = json.loads(raw)
        st = ctx.get("state") or {}
        mid = str((st.get("models") or {}).get("currentModelId") or "")
        mid = mid.split("(")[0].strip() or None
        mode = None
        for o in (st.get("configOptions") or []):
            if o.get("id") == "mode":
                mode = o.get("currentValue") or None
        return mid, mode
    except Exception:
        return None, None

# 枚举全部 session
try:
    _, raw = _req("GET", f"/workspace/{ws_enc}/sessions?limit=100", timeout=8)
    d = json.loads(raw)
    sessions = [s for s in d.get("sessions", []) if isinstance(s, dict)]
except Exception as e:
    print(f"session 枚举失败: {e}", flush=True)
    sys.exit(1)

working, waiting, idle, stale = [], [], [], []
mapping = {}
for s in sessions:
    sid = s.get("sessionId")
    if not sid:
        continue
    name = str(s.get("displayName") or sid)[:40]
    st = get_status(sid)
    model, mode = get_meta(sid)
    if model:
        mapping[sid] = {"name": name, "model": model, "mode": mode}
    rec = {
        "sessionId": sid, "name": name,
        "sourceType": s.get("sourceType"), "model": model, "approval_mode": mode,
    }
    if st is None:
        rec["state"] = "stale"; stale.append(rec)
    elif st.get("hasActivePrompt"):
        rec["state"] = "working"; working.append(rec)
    elif st.get("isWaitingForUserQuestion") or st.get("isWaitingForPermission"):
        rec["state"] = "waiting_input"; waiting.append(rec)
    else:
        rec["state"] = "idle"; idle.append(rec)

snapshot = {
    "captured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    "port": base, "workspace": ws_enc,
    "summary": {"total": len(sessions), "working": len(working),
                "waiting_input": len(waiting), "idle": len(idle), "stale": len(stale)},
    "working": working, "waiting_input": waiting, "idle": idle, "stale": stale,
}
json.dump(snapshot, open(snap_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(mapping, open(map_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"快照: 总数 {len(sessions)} = 工作 {len(working)} + 等待输入 {len(waiting)} + 空闲 {len(idle)} + 失联 {len(stale)}", flush=True)
print(f"模型映射: {len(mapping)} 个会话", flush=True)
if working:
    print("⏳ 工作中（重启后发送继续完成）:", flush=True)
    for r in working:
        print(f"  - {r['name'][:24]:24s} {r['sessionId'][:8]} model={r['model']}", flush=True)
if waiting:
    print("⏸ 等待输入（重启后发送状态说明）:", flush=True)
    for r in waiting:
        print(f"  - {r['name'][:24]:24s} {r['sessionId'][:8]}", flush=True)
PYEOF
[ -f "$SNAPSHOT" ] || { log "工作快照生成失败，中止"; exit 1; }

if [ "$DRY_RUN" = "yes" ]; then
  log "dry-run：仅捕捉，不执行重启/发送。快照: $SNAPSHOT"
  exit 0
fi

# ── ② kill 旧 daemon ──
OLD=$(pgrep -f "qwen serve.*--port $PORT" | grep -v $$ | head -1 || true)
# 兜底：pgrep 匹配不到时按监听端口找 PID（覆盖端口自动转移等边界情况）
if [ -z "$OLD" ]; then
  OLD=$(ss -tlnp 2>/dev/null | grep ":$PORT " | grep -oE "pid=[0-9]+" | head -1 | cut -d= -f2 || true)
fi
if [ -n "$OLD" ]; then
  log "② kill 旧 daemon PID=$OLD"
  kill "$OLD"; sleep 3
  # 确认端口已释放
  if ss -tln 2>/dev/null | grep -q ":$PORT "; then
    log "  ⚠️ 端口 $PORT 仍被占用，强制清理..."
    kill -9 "$OLD" 2>/dev/null || true; sleep 2
  fi
else
  log "② 未发现运行中的 $PORT daemon（直接启动）"
fi

# ── ③ setsid 保活重启（带 writer-idle-timeout 根治游离 SSE 泄漏，见 ops v1.11） ──
log "③ 启动新 daemon..."
cd "$WORKSPACE" && setsid nohup node /home/wuyangcheng/.npm-global/bin/qwen serve \
  --http-bridge --hostname 127.0.0.1 --port "$PORT" --workspace "$WORKSPACE" \
  --max-sessions 16 --chat-recording --token "$TOKEN" --require-auth $CHANNEL_ARGS \
  --writer-idle-timeout-ms 300000 \
  >> "$STATE/daemon_4194.log" 2>&1 < /dev/null &

# ── ④ 等待就绪（HTTP 200 且 /daemon/status.pid 已切换为新进程） ──
log "④ 等待 daemon 就绪..."
READY=""
for i in $(seq 1 30); do
  sleep 2
  if curl -s -m 2 -o /dev/null -w "%{http_code}" "$DAEMON_URL/" -H "Authorization: Bearer $TOKEN" 2>/dev/null | grep -q 200; then
    NEWPID=$(curl -s -m 2 -H "Authorization: Bearer $TOKEN" "$DAEMON_URL/daemon/status" 2>/dev/null | python3 -c "import json,sys;print(json.load(sys.stdin).get('daemon',{}).get('pid',''))" 2>/dev/null || true)
    if [ -n "$OLD" ] && [ "$NEWPID" = "$OLD" ]; then
      continue   # 仍是旧 daemon 响应（端口未真正切换），继续等
    fi
    READY="yes"; log "  就绪（${i} 次探测，pid=$NEWPID）"; break
  fi
done
[ -n "$READY" ] || { log "daemon 就绪超时，跳过模型恢复与继续完成（快照 $SNAPSHOT 留档）"; exit 1; }

# ── ⑤ 恢复模型映射（lazy/channel 会话先 load） ──
log "⑤ 恢复会话模型映射（lazy/channel 会话先 load）..."
python3 - "$MAPFILE" "$PENDINGFILE" "$DAEMON_URL" "$TOKEN" << 'PYEOF'
import json, sys, time, urllib.request, urllib.error

map_path, pending_path, base, token = sys.argv[1:5]
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"} if token else {"Content-Type": "application/json"}

def _req(method: str, path: str, body=None, timeout: float = 8.0):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{base}{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()

def get_model(sid: str):
    try:
        _, raw = _req("GET", f"/session/{sid}/context", timeout=6)
        ctx = json.loads(raw)
        mid = str(((ctx.get("state") or {}).get("models") or {}).get("currentModelId") or "")
        return mid.split("(")[0].strip()
    except Exception:
        return None

def ensure_loaded(sid: str) -> bool:
    if get_model(sid) is not None:
        return True
    for attempt in range(3):
        try:
            st, _ = _req("POST", f"/session/{sid}/load", body={}, timeout=8)
            if st == 200:
                time.sleep(2)
                return True
        except (urllib.error.HTTPError, urllib.error.URLError, OSError, TimeoutError):
            pass
        time.sleep(2)
    return False

def set_model(sid: str, mid: str) -> bool:
    for attempt in range(3):
        try:
            st, _ = _req("POST", f"/session/{sid}/model", body={"modelId": mid}, timeout=10)
            if st == 200:
                return True
        except (urllib.error.HTTPError, urllib.error.URLError, OSError, TimeoutError):
            pass
        time.sleep(3)
    return False

def set_mode(sid: str, mode: str) -> bool:
    """恢复 approval 等级（POST /session/:id/approval-mode，mode∈plan/default/auto-edit/auto/yolo）。"""
    for attempt in range(3):
        try:
            st, _ = _req("POST", f"/session/{sid}/approval-mode", body={"mode": mode}, timeout=10)
            if st == 200:
                return True
        except (urllib.error.HTTPError, urllib.error.URLError, OSError, TimeoutError):
            pass
        time.sleep(3)
    return False

mapping = json.load(open(map_path, encoding="utf-8"))
pending, ok, fail = [], 0, []
for sid, info in mapping.items():
    mid = info.get("model")
    mode = info.get("mode")
    if not ensure_loaded(sid):
        pending.append({"sessionId": sid, "name": info["name"], "model": mid, "mode": mode})
        print(f"  ⏳ {info['name'][:22]:22s} {sid[:8]} → 会话不在 daemon（load 失败），记入待恢复", flush=True)
        continue
    if mid and not set_model(sid, mid):
        fail.append(f"{info['name']}({sid[:8]}): 设置模型失败")
        print(f"  ❌ {info['name'][:22]:22s} {sid[:8]} → 模型设置失败", flush=True)
        continue
    if mode and not set_mode(sid, mode):
        fail.append(f"{info['name']}({sid[:8]}): 设置 approval mode 失败")
        print(f"  ❌ {info['name'][:22]:22s} {sid[:8]} → approval mode({mode}) 设置失败", flush=True)
        continue
    got = None
    for _ in range(6):
        time.sleep(3)
        try:
            _, raw = _req("GET", f"/session/{sid}/context", timeout=6)
            ctx = json.loads(raw)
            st = ctx.get("state") or {}
            got_m = str((st.get("models") or {}).get("currentModelId") or "").split("(")[0].strip()
            got_mode = None
            for o in (st.get("configOptions") or []):
                if o.get("id") == "mode":
                    got_mode = o.get("currentValue")
            if (not mid or got_m == mid) and (not mode or got_mode == mode):
                got = "ok"
                break
        except Exception:
            pass
    if got == "ok":
        ok += 1
        print(f"  ✅ {info['name'][:22]:22s} {sid[:8]} → model={mid} mode={mode}", flush=True)
    else:
        fail.append(f"{info['name']}({sid[:8]}): 设置后核对失败")
        print(f"  ⚠️ {info['name'][:22]:22s} {sid[:8]} → 设置后核对未通过", flush=True)

json.dump(pending, open(pending_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"恢复完成: {ok}/{len(mapping)} 成功，{len(pending)} 待恢复，{len(fail)} 失败", flush=True)
if fail:
    print("失败项:", flush=True)
    for f in fail:
        print(f"  - {f}", flush=True)
PYEOF

# ── ⑥ 发送「继续完成」给被打断的工作 session；等待输入的发送状态说明 ──
log "⑥ 发送继续完成（working session）..."
python3 - "$SNAPSHOT" "$CONTINUE_FILE" "$DAEMON_URL" "$TOKEN" "$NOTIFY_WAITING" "$TS" << 'PYEOF'
import json, sys, time, urllib.request, urllib.error

snap_path, out_path, base, token, notify_waiting, ts = sys.argv[1:7]
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"} if token else {"Content-Type": "application/json"}

CONTINUE_MSG = (
    f"【系统通知】daemon 服务于 {ts} 重启，你正在进行的任务被中断"
    "（可能正在运行的 sub/后台任务也已被终止）。请立即：\n"
    "1. 检查你的任务/会话状态，识别哪些工作尚未完成；\n"
    "2. 检查并重新启动被中断的 sub 或后台任务（如有）；\n"
    "3. 继续完成未完成的工作，完成后按团队规范回报。"
)
WAITING_MSG = (
    f"【系统通知】daemon 服务于 {ts} 重启，你之前等待用户输入/权限确认的状态已被清空。"
    "如果仍需用户介入，请重新发起请求（等待输入的选择题将自动推送用户）。"
)

def send_prompt(sid: str, text: str) -> bool:
    body = json.dumps({"prompt": [{"type": "text", "text": text}]}, ensure_ascii=False).encode("utf-8")
    for attempt in range(3):
        try:
            req = urllib.request.Request(f"{base}/session/{sid}/prompt", data=body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=15) as r:
                # daemon 对 prompt 投递返回 202 Accepted（prompt enqueued），200/202 均视为成功
                return r.status in (200, 202)
        except (urllib.error.HTTPError, urllib.error.URLError, OSError, TimeoutError):
            time.sleep(3)
    return False

snap = json.load(open(snap_path, encoding="utf-8"))
result = {"ts": ts, "continue_sent": [], "waiting_notified": [], "failed": []}

for rec in snap.get("working", []):
    sid, name = rec["sessionId"], rec["name"]
    if send_prompt(sid, CONTINUE_MSG):
        result["continue_sent"].append({"sessionId": sid, "name": name})
        print(f"  📨 继续完成 → {name[:22]:22s} {sid[:8]}", flush=True)
    else:
        result["failed"].append({"sessionId": sid, "name": name, "kind": "continue"})
        print(f"  ❌ 发送失败 → {name[:22]:22s} {sid[:8]}", flush=True)

if notify_waiting == "yes":
    for rec in snap.get("waiting_input", []):
        sid, name = rec["sessionId"], rec["name"]
        if send_prompt(sid, WAITING_MSG):
            result["waiting_notified"].append({"sessionId": sid, "name": name})
            print(f"  📨 等待状态说明 → {name[:22]:22s} {sid[:8]}", flush=True)
        else:
            result["failed"].append({"sessionId": sid, "name": name, "kind": "waiting"})
            print(f"  ❌ 发送失败 → {name[:22]:22s} {sid[:8]}", flush=True)

json.dump(result, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"发送完成: 继续完成 {len(result['continue_sent'])} 条，等待说明 {len(result['waiting_notified'])} 条，失败 {len(result['failed'])} 条", flush=True)
PYEOF

# ── ⑦ 结束 ──
NPID=$(pgrep -f "qwen serve.*--port $PORT" | head -1 || true)
log "⑦ 完成。新 daemon PID=$NPID（port=$PORT），快照: $SNAPSHOT，继续完成记录: $CONTINUE_FILE"

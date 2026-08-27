#!/bin/bash
# 重启 4194 daemon 并保持各 session 模型映射 v2（2026-08-27）
# 用法: bash restart_daemon_4194_v2.sh
# v2 相对 v1 的改进：
#   - 恢复模型前先确保会话已加载（POST /session/:id/load），修复 channel/lazy 会话
#     （如 Jarvis 的 weixin channel 会话）重启后不在 daemon 内存导致 set_model 404 的问题
#   - 失败项区分「可重试失败」与「会话不存在（待恢复）」，后者写入待恢复清单文件
# 流程: ① 记录所有会话当前模型 → ② kill 旧 daemon → ③ setsid 保活重启
#       → ④ 等待就绪 → ⑤ 逐会话 load+恢复模型映射 → ⑥ 验证差异
# 认证: token 读自 .team/daemon_v1/.daemon_token
set -uo pipefail
BASE="/data/WYC/signLanguage"
STATE="$BASE/.team/daemon_v1"
TOKEN=$(cat "$STATE/.daemon_token" 2>/dev/null)
LOG="$BASE/work/logs/daemon_restart_4194.log"
DAEMON_URL="http://127.0.0.1:4194"
MAPFILE="$STATE/daemon_model_map_restart.json"
PENDINGFILE="$STATE/daemon_model_pending_restore.json"   # v2: 待恢复清单

log() { echo "[$(date '+%Y-%m-%dT%H:%M:%S%z')] $*" | tee -a "$LOG"; }

# ── ① 记录当前各会话模型映射 ──
log "① 记录会话模型映射..."
python3 - "$MAPFILE" "$DAEMON_URL" "$TOKEN" << 'PYEOF'
import json, os, sys, urllib.request, urllib.error

map_path, base, token = sys.argv[1:4]
reg_path = "/data/WYC/signLanguage/.team/daemon_v1/registry.json"
headers = {"Authorization": f"Bearer {token}"} if token else {}

def get_model(sid: str):
    try:
        req = urllib.request.Request(f"{base}/session/{sid}/context", headers=headers)
        with urllib.request.urlopen(req, timeout=6) as r:
            ctx = json.loads(r.read().decode())
        mid = str(((ctx.get("state") or {}).get("models") or {}).get("currentModelId") or "")
        mid = mid.split("(")[0].strip()          # 去掉 (provider) 后缀
        return mid or None
    except Exception:
        return None

sessions = {}
try:
    reg = json.load(open(reg_path, encoding="utf-8"))
    for role, info in (reg.get("roles") or {}).items():
        sid = info.get("session_id")
        if sid:
            sessions[sid] = f"{info.get('name') or role}({role})"
    for s in (reg.get("unassigned_sessions") or []):
        sid = s.get("sessionId")
        if sid:
            sessions[sid] = str(s.get("displayName") or sid)[:40]
except Exception as e:
    print(f"registry 读取失败: {e}", flush=True)
    sys.exit(1)

mapping = {}
for sid, name in sessions.items():
    m = get_model(sid)
    if m:
        mapping[sid] = {"name": name, "model": m}
json.dump(mapping, open(map_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"已记录 {len(mapping)} 个会话模型:", flush=True)
for sid, info in mapping.items():
    print(f"  {info['name'][:22]:22s} {sid[:8]} → {info['model']}", flush=True)
PYEOF
[ -f "$MAPFILE" ] || { log "模型映射记录失败，中止"; exit 1; }

# ── ② kill 旧 daemon ──
OLD=$(pgrep -f "qwen serve.*--port 4194" | grep -v $$ | head -1 || true)
if [ -n "$OLD" ]; then
  log "② kill 旧 daemon PID=$OLD"
  kill "$OLD"; sleep 3
else
  log "② 未发现运行中的 4194 daemon（直接启动）"
fi

# ── ③ setsid 保活重启 ──
log "③ 启动新 daemon..."
# --writer-idle-timeout-ms 300000: 游离 SSE 流 5 分钟无活动自动断开（根治连接泄漏，
#   2026-08-27 调研确认 0.21.12 起支持该参数但此前从未启用；前端 autoReconnect 自动重连，体验无感）
cd "$BASE" && setsid nohup node /home/wuyangcheng/.npm-global/bin/qwen serve \
  --http-bridge --hostname 127.0.0.1 --port 4194 --workspace "$BASE" \
  --max-sessions 16 --chat-recording --token "$TOKEN" --require-auth --channel weixin \
  --writer-idle-timeout-ms 300000 \
  >> "$STATE/daemon_4194.log" 2>&1 < /dev/null &

# ── ④ 等待就绪（端口 + /health） ──
log "④ 等待 daemon 就绪..."
READY=""
for i in $(seq 1 30); do
  sleep 2
  if curl -s -m 2 -o /dev/null -w "%{http_code}" "$DAEMON_URL/" -H "Authorization: Bearer $TOKEN" 2>/dev/null | grep -q 200; then
    READY="yes"; log "  就绪（${i} 次探测）"; break
  fi
done
[ -n "$READY" ] || { log "daemon 就绪超时，模型恢复跳过（可稍后手动恢复 $MAPFILE）"; exit 1; }

# ── ⑤ 逐会话恢复模型映射（v2：先 load 再 set_model） ──
log "⑤ 恢复会话模型映射（v2：lazy/channel 会话先 load）..."
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
    """确保会话在 daemon 内存中。channel/lazy 会话重启后不在内存（GET 404），
    需要 POST /session/:id/load 主动加载后才可设置模型。"""
    if get_model(sid) is not None:
        return True                     # 会话已在内存
    for attempt in range(3):            # 404 → 尝试 load
        try:
            st, _ = _req("POST", f"/session/{sid}/load", body={}, timeout=8)
            if st == 200:
                time.sleep(2)           # 等加载落定；load 成功即会话在内存，可设置模型
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

mapping = json.load(open(map_path, encoding="utf-8"))
pending, ok, fail = [], 0, []
for sid, info in mapping.items():
    mid = info["model"]
    if not ensure_loaded(sid):
        pending.append({"sessionId": sid, "name": info["name"], "model": mid})
        print(f"  ⏳ {info['name'][:22]:22s} {sid[:8]} → 会话不在 daemon（load 失败），记入待恢复", flush=True)
        continue
    if set_model(sid, mid):
        got = None
        for _ in range(6):              # 核对生效
            time.sleep(3)
            got = get_model(sid)
            if got == mid:
                break
        if got == mid:
            ok += 1
            print(f"  ✅ {info['name'][:22]:22s} {sid[:8]} → {mid}", flush=True)
        else:
            fail.append(f"{info['name']}({sid[:8]}): 设置 {mid} 但核对读到 {got}")
            print(f"  ⚠️ {info['name'][:22]:22s} {sid[:8]} → 设置 {mid}，核对读到 {got}", flush=True)
    else:
        fail.append(f"{info['name']}({sid[:8]}): 设置请求失败")
        print(f"  ❌ {info['name'][:22]:22s} {sid[:8]} → 设置失败", flush=True)

json.dump(pending, open(pending_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"恢复完成: {ok}/{len(mapping)} 成功，{len(pending)} 待恢复，{len(fail)} 失败", flush=True)
if pending:
    print("待恢复清单（会话 active 后手动执行 v2 脚本 ⑤ 段或 POST /session/:id/load + /model）:", flush=True)
    for p in pending:
        print(f"  - {p['name']} ({p['sessionId']}) → {p['model']}", flush=True)
if fail:
    print("失败项:", flush=True)
    for f in fail:
        print(f"  - {f}", flush=True)
PYEOF

# ── ⑥ 结束 ──
NPID=$(pgrep -f "qwen serve.*--port 4194" | head -1 || true)
log "⑥ 完成。新 daemon PID=$NPID，模型映射文件: $MAPFILE，待恢复清单: $PENDINGFILE"

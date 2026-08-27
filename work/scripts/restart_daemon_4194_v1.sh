#!/bin/bash
# 重启 4194 daemon 并保持各 session 模型映射 v1（2026-08-27）
# 用法: bash restart_daemon_4194_v1.sh
# 流程: ① 记录所有会话当前模型 → ② kill 旧 daemon → ③ setsid 保活重启
#       → ④ 等待就绪 → ⑤ 逐会话恢复模型映射 → ⑥ 验证差异
# 说明: daemon 重启后会话 resume 但模型可能回落默认，本脚本显式恢复每个会话的模型。
# 认证: token 读自 .team/daemon_v1/.daemon_token
set -uo pipefail
BASE="/data/WYC/signLanguage"
STATE="$BASE/.team/daemon_v1"
TOKEN=$(cat "$STATE/.daemon_token" 2>/dev/null)
LOG="$BASE/work/logs/daemon_restart_4194.log"
DAEMON_URL="http://127.0.0.1:4194"
MAPFILE="$STATE/daemon_model_map_restart.json"

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
cd "$BASE" && setsid nohup node /home/wuyangcheng/.npm-global/bin/qwen serve \
  --http-bridge --hostname 127.0.0.1 --port 4194 --workspace "$BASE" \
  --max-sessions 16 --chat-recording --token "$TOKEN" --require-auth --channel weixin \
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

# ── ⑤ 逐会话恢复模型映射 ──
log "⑤ 恢复会话模型映射..."
python3 - "$MAPFILE" "$DAEMON_URL" "$TOKEN" << 'PYEOF'
import json, sys, time, urllib.request, urllib.error

map_path, base, token = sys.argv[1:4]
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"} if token else {"Content-Type": "application/json"}

def set_model(sid: str, mid: str) -> bool:
    body = json.dumps({"modelId": mid}).encode()
    for attempt in range(3):
        try:
            req = urllib.request.Request(f"{base}/session/{sid}/model", data=body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status == 200
        except (urllib.error.HTTPError, urllib.error.URLError, OSError):
            time.sleep(3)
    return False

def get_model(sid: str):
    try:
        req = urllib.request.Request(f"{base}/session/{sid}/context", headers=headers)
        with urllib.request.urlopen(req, timeout=6) as r:
            ctx = json.loads(r.read().decode())
        mid = str(((ctx.get("state") or {}).get("models") or {}).get("currentModelId") or "")
        return mid.split("(")[0].strip()
    except Exception:
        return None

mapping = json.load(open(map_path, encoding="utf-8"))
ok, fail = 0, []
for sid, info in mapping.items():
    mid = info["model"]
    if set_model(sid, mid):
        # 等待会话恢复生效后核对
        got = None
        for _ in range(6):
            time.sleep(3)
            got = get_model(sid)
            if got == mid:
                break
        if got == mid:
            ok += 1
            print(f"  ✅ {info['name'][:22]:22s} {sid[:8]} → {mid}", flush=True)
        else:
            fail.append(f"{info['name']}({sid[:8]}): 设置 {mid} 但读到 {got}")
            print(f"  ⚠️ {info['name'][:22]:22s} {sid[:8]} → 设置 {mid}，核对读到 {got}", flush=True)
    else:
        fail.append(f"{info['name']}({sid[:8]}): 设置请求失败")
        print(f"  ❌ {info['name'][:22]:22s} {sid[:8]} → 设置失败", flush=True)

print(f"恢复完成: {ok}/{len(mapping)} 成功", flush=True)
if fail:
    print("失败项:", flush=True)
    for f in fail:
        print(f"  - {f}", flush=True)
PYEOF

# ── ⑥ 结束 ──
NPID=$(pgrep -f "qwen serve.*--port 4194" | head -1 || true)
log "⑥ 完成。新 daemon PID=$NPID，模型映射文件: $MAPFILE"

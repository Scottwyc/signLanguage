#!/usr/bin/env bash
# daemon team 消息机制常驻服务启动脚本 v1
# 功能：为每个有活跃 session 的成员启动 SSE helper，并启动聚合 supervisor。
# 用法：bash daemon_team_message_services_v1.sh [start|status]
set -uo pipefail

ROOT=/data/WYC/signLanguage
MEMBERS_DIR="$ROOT/.team/daemon_v1/members"
HELPER="$ROOT/work/scripts/daemon_team_member_helper_v2.py"
SUPERVISOR="$ROOT/work/scripts/daemon_team_message_supervisor_v1.py"
DAEMON_URL="http://127.0.0.1:4194"

start() {
  mkdir -p "$MEMBERS_DIR"
  # 从 registry 读 role -> session_id（跳过无 session 或 stale 的成员）
  local map_file
  map_file=$(mktemp)
  python3 - "$ROOT" > "$map_file" <<'PY'
import json, sys
root = sys.argv[1]
reg = json.load(open(f"{root}/.team/daemon_v1/registry.json"))
roles = reg.get("roles", {})
for role, info in roles.items():
    sid = info.get("live_session_id") or info.get("session_id")
    state = info.get("session_id_state", "")
    if sid and state not in ("stale", "expired", "invalid", "not_listed"):
        print(f"{role}\t{sid}")
PY
  while IFS=$'\t' read -r role sid; do
    [ -z "$role" ] && continue
    local log="$MEMBERS_DIR/${role}.log"
    setsid nohup python3 "$HELPER" --role "$role" --session-id "$sid" \
      --daemon-url "$DAEMON_URL" --poll-seconds 5 \
      > "$log" 2>&1 < /dev/null &
    echo "启动 helper: $role ($sid)"
  done < "$map_file"
  python3 -c "import os; os.remove('$map_file')" 2>/dev/null || true

  setsid nohup python3 "$SUPERVISOR" \
    --registry "$ROOT/.team/daemon_v1/registry.json" \
    --members-dir "$MEMBERS_DIR" \
    --output "$ROOT/.team/daemon_v1/message_supervisor.json" \
    --timeout-seconds 30 \
    > "$ROOT/.team/daemon_v1/message_supervisor.log" 2>&1 < /dev/null &
  echo "启动 supervisor"
  sleep 2
  status
}

status() {
  echo "=== helper 进程 ==="
  pgrep -af "daemon_team_member_helper_v1.py" | grep -v grep || echo "  无 helper 进程"
  echo "=== supervisor 进程 ==="
  pgrep -af "daemon_team_message_supervisor_v1.py" | grep -v grep || echo "  无 supervisor 进程"
}

case "${1:-start}" in
  start) start ;;
  status) status ;;
  *) echo "用法: $0 [start|status]"; exit 1 ;;
esac

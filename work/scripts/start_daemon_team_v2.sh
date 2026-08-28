#!/usr/bin/env bash
# ============================================================
# agent team daemon 一键启动/停止/状态脚本 v2
#
# v2 变更（2026-08-14）：
#   - 新增 daemon channels 支持（--channel github 等），通过 CHANNEL 变量或
#     --channel 参数传入，为空则不带 --channel（v1 行为）
#
# 功能：
#   1. 4194 生产 daemon（setsid+nohup 保活，带 bearer token + --require-auth）
#   2. daemon channels（如 github，配置见 ~/.qwen/settings.json 的 "channels"）
#   3. refresher（每 1 秒刷新 registry/health/dashboard 缓存）
#   4. 各成员 SSE helper + message supervisor（复用 daemon_team_message_services_v1.sh）
#   5. v2 集成控制台 8466、v1 dashboard 8465
#
# 用法：
#   bash start_daemon_team_v2.sh                      # 启动（幂等：已运行则跳过）
#   bash start_daemon_team_v2.sh --channel github start
#   bash start_daemon_team_v2.sh start|restart|stop|status
#   bash start_daemon_team_v2.sh --port 4194 --token-file <path> --channel <name> start
#
# 说明：
#   - token 文件不存在时自动用 openssl rand -hex 32 生成（chmod 600）
#   - 所有进程 setsid 保活，退出 shell 后继续运行（PPID 归 1/systemd）
#   - 原 v1 脚本保留：/data/WYC/signLanguage/work/scripts/start_daemon_team_v1.sh
# ============================================================
set -uo pipefail

ROOT=/data/WYC/signLanguage
SCRIPTS="$ROOT/work/scripts"
TEAM_DIR="$ROOT/.team/daemon_v1"
MEMBERS_DIR="$TEAM_DIR/members"
TOKEN_FILE="$TEAM_DIR/.daemon_token"
DAEMON_URL="http://127.0.0.1:4194"
PORT=4194
MAX_SESSIONS=16
QWEN_BIN=/home/wuyangcheng/.npm-global/bin/qwen
DAEMON_LOG="$TEAM_DIR/daemon_4194.stdout.log"
CHANNEL=""   # 为空则不启用 channel；可传 github / telegram / all 等

# ---------- 基础工具 ----------
log() { printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }

# ---------- token 管理 ----------
ensure_token() {
  if [ ! -s "$TOKEN_FILE" ]; then
    mkdir -p "$TEAM_DIR"
    openssl rand -hex 32 > "$TOKEN_FILE"
    chmod 600 "$TOKEN_FILE"
    log "已生成新 token -> $TOKEN_FILE"
  fi
}

# ---------- 4194 daemon ----------
daemon_is_running() { ss -tlnp 2>/dev/null | grep -q ":$PORT "; }

daemon_start() {
  if daemon_is_running; then
    log "daemon 已在运行（端口 $PORT），跳过（如需重启用 restart）"
    return 0
  fi
  ensure_token
  log "启动 daemon: qwen serve --port $PORT（--token + --require-auth${CHANNEL:+ + --channel $CHANNEL}）"
  local channel_args=()
  if [ -n "$CHANNEL" ]; then
    channel_args+=(--channel "$CHANNEL")
  fi
  setsid nohup "$QWEN_BIN" serve \
    --http-bridge --hostname 127.0.0.1 --port "$PORT" \
    --workspace "$ROOT" --max-sessions "$MAX_SESSIONS" --chat-recording \
    --token "$(cat "$TOKEN_FILE")" --require-auth \
    "${channel_args[@]}" \
    > "$DAEMON_LOG" 2>&1 < /dev/null &
  # 同一命令内等待并校验（避免跨命令被清理）
  local waited=0
  while [ $waited -lt 30 ]; do
    sleep 2; waited=$((waited+2))
    daemon_is_running && break
  done
  if daemon_is_running; then
    local pid
    pid=$(ss -tlnp 2>/dev/null | grep ":$PORT " | grep -oE 'pid=[0-9]+' | head -1 | cut -d= -f2)
    log "daemon 启动成功 pid=$pid 端口 $PORT"
    return 0
  else
    log "ERROR: daemon 启动失败，见 $DAEMON_LOG"
    tail -20 "$DAEMON_LOG" 2>/dev/null
    return 1
  fi
}

daemon_stop() {
  if daemon_is_running; then
    local pid
    pid=$(ss -tlnp 2>/dev/null | grep ":$PORT " | grep -oE 'pid=[0-9]+' | head -1 | cut -d= -f2)
    log "停止 daemon pid=$pid"
    kill "$pid" 2>/dev/null
    sleep 3
    # 确认退出（含 ACP 子进程）
    if daemon_is_running; then
      log "警告: daemon 未退出，尝试 SIGKILL（请人工确认无正在处理的会话）"
      kill -9 "$pid" 2>/dev/null || true
      sleep 1
    fi
    daemon_is_running && log "ERROR: daemon 仍在运行" || log "daemon 已停止"
  else
    log "daemon 未在运行"
  fi
}

# ---------- 辅助进程（refresher/console/dashboard） ----------
aux_start() {
  # refresher：每 1 秒刷新 registry/health/dashboard
  if pgrep -f "daemon_team_refresher_v1.py" >/dev/null 2>&1; then
    log "refresher 已在运行"
  else
    log "启动 refresher"
    setsid nohup python3 -u "$SCRIPTS/daemon_team_refresher_v1.py" \
      --interval 1 --daemon-url "$DAEMON_URL" \
      > "$TEAM_DIR/refresher.stdout.log" 2>&1 < /dev/null &
  fi
  # v2 集成控制台 8466
  if ss -tlnp 2>/dev/null | grep -q ":8466 "; then
    log "console_v2(8466) 已在运行"
  else
    log "启动 console_v2(8466)"
    setsid nohup python3 -u "$SCRIPTS/daemon_team_console_v2_server.py" \
      --host 127.0.0.1 --port 8466 \
      > "$TEAM_DIR/console_v2.stdout.log" 2>&1 < /dev/null &
  fi
  # v1 dashboard 8465（静态缓存服务）
  if ss -tlnp 2>/dev/null | grep -q ":8465 "; then
    log "dashboard_v1(8465) 已在运行"
  else
    log "启动 dashboard_v1(8465)"
    setsid nohup python3 -u "$SCRIPTS/daemon_team_dashboard_server_v1.py" \
      --host 127.0.0.1 --port 8465 \
      > "$TEAM_DIR/dashboard.stdout.log" 2>&1 < /dev/null &
  fi
}

aux_stop() {
  # 按脚本名精确停止，避免误杀
  for pat in "daemon_team_refresher_v1.py" "daemon_team_console_v2_server.py" "daemon_team_dashboard_server_v1.py" "daemon_team_message_supervisor_v1.py" "daemon_team_member_helper_v1.py"; do
    pkill -f "$pat" 2>/dev/null && log "已停止: $pat" || true
  done
  sleep 1
}

# ---------- 成员 helpers + supervisor（复用已有脚本） ----------
helpers_start() {
  # 幂等检查匹配 v1/v2 helper（8-18 起实际运行 v2，v1 检查会漏掉导致重复启动）
  if pgrep -f "daemon_team_member_helper_v[12].py" >/dev/null 2>&1; then
    log "成员 helpers 已在运行，跳过（message_services_v1.sh 无幂等，勿重复调用）"
    return 0
  fi
  log "启动成员 helpers + supervisor（复用 daemon_team_message_services_v1.sh）"
  bash "$SCRIPTS/daemon_team_message_services_v1.sh" start
}

# ---------- 状态 ----------
status() {
  echo "=== daemon $PORT ==="
  if daemon_is_running; then
    ss -tlnp 2>/dev/null | grep ":$PORT " | sed 's/^/  /'
    local token_ok no_token
    token_ok=$(curl -s -m 5 -H "Authorization: Bearer $(cat "$TOKEN_FILE")" -o /dev/null -w '%{http_code}' http://127.0.0.1:4194/health 2>/dev/null)
    no_token=$(curl -s -m 5 -o /dev/null -w '%{http_code}' http://127.0.0.1:4194/health 2>/dev/null)
    echo "  认证检查: 无 token=$no_token, 带 token=$token_ok（期望 401/200）"
  else
    echo "  NOT RUNNING"
  fi
  echo "=== 辅助进程 ==="
  pgrep -af "daemon_team_(refresher|member_helper|message_supervisor|console_v2|dashboard_server)_v1" | grep -v grep | sed 's/^/  /' || echo "  无"
  echo "=== 端口 ==="
  ss -tlnp 2>/dev/null | grep -E ":(4194|8465|8466) " | sed 's/^/  /' || echo "  无"
}

# ---------- 主流程 ----------
ACTION=start
while [ $# -gt 0 ]; do
  case "$1" in
    --port) PORT=$2; shift 2 ;;
    --token-file) TOKEN_FILE=$2; shift 2 ;;
    --channel) CHANNEL=$2; shift 2 ;;
    start|restart|stop|status) ACTION=$1; shift ;;
    *) echo "未知参数: $1"; exit 1 ;;
  esac
done

case "$ACTION" in
  start)
    daemon_start
    aux_start
    helpers_start
    sleep 2
    status
    ;;
  restart)
    log "===== 重启 agent team ====="
    daemon_stop
    aux_stop
    sleep 2
    daemon_start
    aux_start
    helpers_start
    sleep 2
    status
    ;;
  stop)
    log "===== 停止 agent team ====="
    daemon_stop
    aux_stop
    status
    ;;
  status)
    status
    ;;
esac

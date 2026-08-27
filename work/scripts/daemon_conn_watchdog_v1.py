#!/usr/bin/env python3
"""4194 daemon 连接数 watchdog v1（2026-08-27）——保护 daemon 可用性。

背景：VS Code 内置浏览器端口转发器对 4194 的 SSE/TCP 连接持续累积（8-26/8-27 多次
从正常 20-30 涨到 104/160/218），占满 listenerMaxConnections=256 后 daemon 本身不可用
（成员 Connection error、看板 SSE 代理挂起）。writer-idle-timeout 只回收写侧空闲 SSE 流，
半开 TCP 连接只能等系统 keepalive（约 2h）——服务端必须主动兜底。

本 watchdog：
- 每 30s 统计 4194 的 ESTAB 连接数
- ESTAB > WARN（120）：微信推送预警（含当前数/涨幅）
- ESTAB > RESTART（192，连续 2 次确认）：自动调 restart_daemon_4194_v3.sh 重启
  （保持模型映射 + approval + 对被打断工作会话发送继续完成），重启后冷却 30 分钟
- 全部走 setsid 保活 + 日志；重启动作放独立 tmux，避免自身被重启连带

用法: setsid nohup python3 -u daemon_conn_watchdog_v1.py >> log 2>&1 < /dev/null &
"""
from __future__ import annotations

import datetime
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/data/WYC/signLanguage")
SCRIPTS = ROOT / "work/scripts"
STATE = ROOT / ".team" / "daemon_v1"
LOG = ROOT / "work/logs/daemon_conn_watchdog.log"
RESTART_SCRIPT = SCRIPTS / "restart_daemon_4194_v3.sh"
WEIXIN_PUSH = Path("/data/WYC/signLanguage/work/scripts/weixin_push.py")

INTERVAL = 30          # 检测周期（秒）
WARN = 120             # 预警阈值
RESTART = 192          # 自动重启阈值（256 上限的 75%）
CONFIRM_ROUNDS = 2     # 连续超 RESTART 轮数才重启（防抖动）
COOLDOWN = 1800        # 重启后冷却（秒）
STATE_FILE = STATE / "conn_watchdog_state.json"

ADMIN = "运维"


def log(msg: str) -> None:
    line = f"[{datetime.datetime.now():%Y-%m-%dT%H:%M:%S%z}] {msg}"
    print(line, flush=True)
    try:
        with LOG.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def conn_count() -> int:
    """统计 4194 的 ESTAB 连接数。"""
    try:
        out = subprocess.run(
            ["ss", "-tn"], capture_output=True, text=True, timeout=10
        ).stdout
        return sum(1 for ln in out.splitlines() if ":4194" in ln and "ESTAB" in ln)
    except (OSError, subprocess.TimeoutExpired):
        return -1


def push_weixin(text: str) -> None:
    try:
        subprocess.run(
            [sys.executable, str(WEIXIN_PUSH), text],
            capture_output=True, text=True, timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        pass


def load_state() -> dict:
    try:
        import json
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_state(state: dict) -> None:
    import json
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    state = load_state()
    over_rounds = int(state.get("over_rounds", 0))
    last_restart = float(state.get("last_restart_at", 0))
    warned = bool(state.get("warned", False))
    last_warn_conn = int(state.get("last_warn_conn", 0))
    log(f"连接数 watchdog 启动（WARN={WARN} RESTART={RESTART} interval={INTERVAL}s）")

    while True:
        time.sleep(INTERVAL)
        n = conn_count()
        now = time.time()
        if n < 0:
            log("ss 查询失败，跳过本轮")
            continue
        # 冷却期内只记录不动作
        if now - last_restart < COOLDOWN:
            if n > WARN:
                log(f"冷却期（{COOLDOWN - (now - last_restart):.0f}s 剩余），连接 {n}，仅记录")
            over_rounds = 0
            continue

        if n > RESTART:
            over_rounds += 1
            log(f"⚠️ 连接 {n} > {RESTART}（连续 {over_rounds}/{CONFIRM_ROUNDS}）")
            if over_rounds >= CONFIRM_ROUNDS:
                log(f"🚨 触发自动重启（连接 {n}）")
                push_weixin(f"【自动重启】4194 连接数 {n} 连续超阈值，自动执行 v3 重启（保持模型映射+继续完成）")
                try:
                    subprocess.run(
                        ["tmux", "new-session", "-d", "-s", "connwatch_restart",
                         f"bash {RESTART_SCRIPT}; sleep 600"],
                        timeout=10,
                    )
                except (OSError, subprocess.TimeoutExpired) as exc:
                    log(f"重启启动失败: {exc}")
                last_restart = now
                over_rounds = 0
                warned = False
                last_warn_conn = 0
        elif n > WARN:
            over_rounds = 0
            if not warned or n > last_warn_conn + 20:
                log(f"⚠️ 预警：连接 {n} > {WARN}")
                push_weixin(f"【预警】4194 连接数 {n}（阈值 {WARN}），持续上涨将自动重启（{RESTART}）")
                warned = True
                last_warn_conn = n
            else:
                log(f"连接 {n}（预警中，阈值 {WARN}）")
        else:
            over_rounds = 0
            if warned:
                log(f"✅ 连接回落至 {n}，预警解除")
                warned = False
                last_warn_conn = 0

        save_state({
            "over_rounds": over_rounds,
            "last_restart_at": last_restart,
            "warned": warned,
            "last_warn_conn": last_warn_conn,
        })
    return 0


if __name__ == "__main__":
    sys.exit(main())

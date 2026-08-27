#!/usr/bin/env python3
"""VS Code Server 自动恢复 watchdog v1（2026-08-28）——保护 inotify 与 SSE 连接资源。

背景：VS Code Server（.vscode-server/cli/servers/Stable-*）长时间运行会累积两类泄漏：
1. **inotify watch**（文件监控）：2026-08-28 实测单进程泄漏 56193 个（系统上限 65536 的
   86%）→ inotify 耗尽 → systemd 无法为服务建 watch（"No space left on device"）→
   代理等服务崩溃循环 → 本地模型全挂（本地B 卡死 / g29 503 的真凶）
2. **SSE/TCP 连接**：对 4194 累积 69+ 条游离连接（与 daemon 的 writer-idle-timeout 互补，
   但 inotify 泄漏是本 watchdog 的主监控对象）

本 watchdog（与 daemon_conn_watchdog_v1.py 互补，daemon 那个管 4194 连接、这个管 VS Code 进程）：
- 每 60s 统计 VS Code Server 主进程的 inotify watch 数
- inotify > WARN（40000）：微信预警（涨幅 >10000 再报，防轰炸）
- inotify > RESTART（55000，连续 2 次确认）：自动 kill VS Code Server 主进程
  （用户 VS Code 重连时自动拉起新实例，inotify/连接全部清空），重启后冷却 6h
- 全部 setsid 保活 + 日志 + 状态落盘

用法: setsid nohup python3 -u vscode_server_watchdog_v1.py >> log 2>&1 < /dev/null &
"""
from __future__ import annotations

import datetime
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/data/WYC/signLanguage")
STATE = ROOT / ".team" / "daemon_v1"
LOG = ROOT / "work/logs/vscode_server_watchdog.log"
WEIXIN_PUSH = ROOT / "work/scripts/weixin_push.py"
STATE_FILE = STATE / "vscode_watchdog_state.json"

INTERVAL = 60           # 检测周期（秒）
WARN = 40000            # 预警阈值（inotify watch 数）
RESTART = 55000         # 自动重启阈值（65536 上限的 84%）
CONFIRM_ROUNDS = 2      # 连续超阈值轮数才重启
COOLDOWN = 21600        # 重启后冷却（秒，6 小时——重启会断用户 VS Code，不能频繁）
WARN_DELTA = 10000      # 预警涨幅再报阈值


def log(msg: str) -> None:
    line = f"[{datetime.datetime.now():%Y-%m-%dT%H:%M:%S%z}] {msg}"
    print(line, flush=True)
    try:
        with LOG.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def find_vscode_server() -> int | None:
    """找到**当前用户（wuyangcheng）**的 VS Code Server **cli 守护进程** PID。

    必须：
    1. 按 uid 过滤（其他用户如 guxifeng 有同名进程，跨用户 fdinfo 不可读）
    2. 优先匹配 **cli 守护**（cmdline 以 `/server/` 结尾，无参数）——它是 server
       实例的父进程/管理器，kill 它整个进程树清空（实例会自动被拉起的新树替代）；
       只 kill server 实例（server-main.js）会被守护立即重新拉起，泄漏复现。
    """
    candidates: list[int] = []
    try:
        out = subprocess.run(["pgrep", "-f", r"\.vscode-server/cli/servers/Stable-.*/server/"],
                             capture_output=True, text=True, timeout=10).stdout
        for line in out.splitlines():
            pid = line.strip()
            if not pid.isdigit():
                continue
            try:
                status = Path(f"/proc/{pid}/status").read_text(encoding="utf-8")
                uid = int(status.split("Uid:")[1].split()[0])
                if uid != os.getuid():
                    continue
                cmd = Path(f"/proc/{pid}/cmdline").read_bytes().replace(b"\0", b" ").decode("utf-8", errors="replace")
                candidates.append((int(pid), cmd))
            except (OSError, ValueError, IndexError):
                continue
    except (OSError, subprocess.TimeoutExpired):
        return None
    if not candidates:
        return None
    # cli 守护优先：cmdline 以 '/server/' 结尾（无 node/server-main 等参数）
    for pid, cmd in candidates:
        if cmd.rstrip().endswith("/server/"):
            return pid
    # 兜底：取最小的 PID（最可能靠近树根）
    return min(pid for pid, _ in candidates)


def count_inotify_watches(pid: int) -> int:
    """统计进程的全部 inotify watch（遍历 /proc/PID/fdinfo/* 数 'inotify wd'）。"""
    total = 0
    fdinfo_dir = Path(f"/proc/{pid}/fdinfo")
    try:
        for f in fdinfo_dir.iterdir():
            try:
                content = f.read_text(encoding="utf-8", errors="replace")
                if "inotify" in content:
                    total += content.count("inotify wd")
            except OSError:
                continue
    except OSError:
        return -1
    return total


def count_vscode_watches() -> int:
    """统计**当前用户全部 VS Code Server 相关进程**的 inotify watch 总和。

    watch 可能分布在主进程、fileWatcher（--type=fileWatcher）或 extensionHost 子进程，
    只盯主进程会漏掉真正的泄漏进程（2026-08-28 实测主进程=0、fileWatcher=14683）。
    """
    total = 0
    for p in Path("/proc").iterdir():
        if not p.name.isdigit():
            continue
        try:
            status = (p / "status").read_text(encoding="utf-8")
            uid = int(status.split("Uid:")[1].split()[0])
            if uid != os.getuid():
                continue
            cmd = (p / "cmdline").read_bytes().replace(b"\0", b" ")
            if b".vscode-server/cli/servers/Stable" not in cmd:
                continue
        except (OSError, ValueError, IndexError):
            continue
        try:
            for fdinfo in (p / "fdinfo").iterdir():
                try:
                    c = fdinfo.read_text(encoding="utf-8", errors="replace")
                    if "inotify" in c:
                        total += c.count("inotify wd")
                except OSError:
                    continue
        except OSError:
            continue
    return total


def push_weixin(text: str) -> None:
    try:
        subprocess.run([sys.executable, str(WEIXIN_PUSH), text],
                       capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        pass


def restart_vscode_server(pid: int) -> bool:
    """kill VS Code Server 主进程（用户 VS Code 重连时自动拉起新实例）。"""
    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(5)
        # 确认进程已退出
        if os.path.exists(f"/proc/{pid}"):
            os.kill(pid, signal.SIGKILL)
            time.sleep(2)
        return not os.path.exists(f"/proc/{pid}")
    except (OSError, ProcessLookupError):
        return True  # 已不在 = 已退出


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
    last_warn_watches = int(state.get("last_warn_watches", 0))
    log(f"VS Code Server watchdog 启动（WARN={WARN} RESTART={RESTART} interval={INTERVAL}s）")

    while True:
        time.sleep(INTERVAL)
        pid = find_vscode_server()
        now = time.time()
        if pid is None:
            log("VS Code Server 未运行（用户未连接或已退出），正常")
            over_rounds = 0
            warned = False
            last_warn_watches = 0
            save_state({"over_rounds": 0, "last_restart_at": last_restart,
                        "warned": False, "last_warn_watches": 0})
            continue
        watches = count_vscode_watches()   # 进程树总和（主+fileWatcher+extensionHost）
        log(f"VS Code Server PID={pid} inotify={watches}（进程树总和）")

        if now - last_restart < COOLDOWN:
            if watches > WARN:
                log(f"冷却期（{COOLDOWN - (now - last_restart):.0f}s 剩余），inotify={watches}，仅记录")
            over_rounds = 0
            continue

        if watches > RESTART:
            over_rounds += 1
            log(f"⚠️ inotify {watches} > {RESTART}（连续 {over_rounds}/{CONFIRM_ROUNDS}）")
            if over_rounds >= CONFIRM_ROUNDS:
                log(f"🚨 触发自动重启 VS Code Server（PID {pid}，inotify {watches}）")
                push_weixin(f"【自动重启】VS Code Server inotify 泄漏 {watches} 个（上限 65536），"
                            "自动重启清空（你当前 VS Code 需重新连接 Remote）")
                ok = restart_vscode_server(pid)
                log(f"VS Code Server 重启{'成功' if ok else '失败/超时'}（PID {pid}）")
                if ok:
                    push_weixin("【已恢复】VS Code Server 已重启，inotify/连接已清空，重连 Remote 即可")
                last_restart = now
                over_rounds = 0
                warned = False
                last_warn_watches = 0
        elif watches > WARN:
            over_rounds = 0
            if not warned or watches > last_warn_watches + WARN_DELTA:
                log(f"⚠️ 预警：inotify {watches} > {WARN}")
                push_weixin(f"【预警】VS Code Server inotify 已累积 {watches} 个（阈值 {WARN}），"
                            f"持续上涨将自动重启（{RESTART}）")
                warned = True
                last_warn_watches = watches
        else:
            over_rounds = 0
            if warned:
                log(f"✅ inotify 回落至 {watches}，预警解除")
                warned = False
                last_warn_watches = 0

        save_state({"over_rounds": over_rounds, "last_restart_at": last_restart,
                    "warned": warned, "last_warn_watches": last_warn_watches})
    return 0


if __name__ == "__main__":
    sys.exit(main())

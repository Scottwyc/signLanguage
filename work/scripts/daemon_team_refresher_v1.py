#!/usr/bin/env python3
"""独立刷新生产 daemon 4194 的 team registry 与只读 dashboard 数据。

本脚本只调用 daemon_team_v1.py / daemon_team_dashboard_v1.py，不触碰旧 team_health、旧
 dashboard data 或 TUI monitor。默认每 5 秒刷新；失败按状态变化或 60 秒节流写入独立日志。
"""
from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/data/WYC/signLanguage")
TEAM_DIR = ROOT / ".team" / "daemon_v1"
LOG_PATH = TEAM_DIR / "refresher.log"
DAEMON_SCRIPT = ROOT / "work/scripts/daemon_team_v1.py"
DASHBOARD_SCRIPT = ROOT / "work/scripts/daemon_team_dashboard_v1.py"
# [20260827] topology 角色→模型自动同步（读 daemon 实时 currentModelId 更新 team_topology.json，
# 脚本内部 60s 节流写盘，失败不阻塞主刷新链路）
SYNC_TOPO_SCRIPT = ROOT / "work/scripts/sync_team_topology_models_v1.py"


class ThrottledFailureLogger:
    """避免 daemon 不可用时每轮重复刷屏，同时保留首次/恢复/定期错误。"""

    def __init__(self, logger: logging.Logger, cooldown: float = 60.0) -> None:
        self.logger = logger
        self.cooldown = cooldown
        self.last_key: str | None = None
        self.last_time = 0.0

    def failure(self, stage: str, error: str) -> None:
        key = f"{stage}:{error}"
        now = time.monotonic()
        if key != self.last_key or now - self.last_time >= self.cooldown:
            self.logger.error("refresh failed stage=%s error=%s", stage, error)
            self.last_key, self.last_time = key, now

    def recovered(self) -> None:
        if self.last_key is not None:
            self.logger.info("refresh recovered after failure stage=%s", self.last_key.split(":", 1)[0])
            self.last_key = None


def setup_logger() -> logging.Logger:
    TEAM_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("daemon_team_refresher_v1")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    return logger


def run_script(script: Path, extra: list[str]) -> None:
    command = [sys.executable, str(script), *extra]
    result = subprocess.run(command, cwd=str(ROOT), capture_output=True, text=True, timeout=30)
    if result.returncode:
        detail = (result.stderr or result.stdout or "no output").strip().replace("\n", " | ")
        raise RuntimeError(f"exit={result.returncode} {detail[-1000:]}")


def refresh(daemon_url: str | None, failure_logger: ThrottledFailureLogger) -> bool:
    daemon_args = ["--daemon-url", daemon_url] if daemon_url else []
    try:
        run_script(DAEMON_SCRIPT, daemon_args)
    except (OSError, subprocess.SubprocessError, RuntimeError) as exc:
        failure_logger.failure("daemon_team", str(exc))
        return False
    try:
        run_script(DASHBOARD_SCRIPT, [])
    except (OSError, subprocess.SubprocessError, RuntimeError) as exc:
        failure_logger.failure("dashboard", str(exc))
        return False
    # [20260827] topology 角色→模型同步（节流在 sync 脚本内部；失败仅记录，不阻塞）
    try:
        run_script(SYNC_TOPO_SCRIPT, [])
    except (OSError, subprocess.SubprocessError, RuntimeError) as exc:
        failure_logger.failure("topology_sync", str(exc))
    failure_logger.recovered()
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh daemon team v1 files")
    parser.add_argument("--interval", type=float, default=5.0, help="refresh interval in seconds (default: 5)")
    parser.add_argument("--daemon-url", help="override daemon base URL")
    parser.add_argument("--once", action="store_true", help="run one refresh and exit")
    args = parser.parse_args()
    if args.interval <= 0:
        parser.error("--interval must be positive")
    logger = setup_logger()
    failure_logger = ThrottledFailureLogger(logger)
    if args.once:
        return 0 if refresh(args.daemon_url, failure_logger) else 1
    logger.info("refresher started interval=%.3fs daemon_url=%s", args.interval, args.daemon_url or "manifest/default")
    while True:
        refresh(args.daemon_url, failure_logger)
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())

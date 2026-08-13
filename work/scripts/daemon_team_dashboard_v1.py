#!/usr/bin/env python3
"""生成独立 daemon team dashboard v1 数据，不触碰旧 dashboard 生成链路。"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/data/WYC/signLanguage")
DAEMON_DIR = ROOT / ".team" / "daemon_v1"
REGISTRY_PATH = DAEMON_DIR / "registry.json"
HEALTH_PATH = DAEMON_DIR / "health_snapshot.json"
LEGACY_DATA_PATH = ROOT / ".team" / "dashboard" / "data.json"
OUTPUT_PATH = DAEMON_DIR / "dashboard_data.json"


def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _role_aliases(role: str, member: dict[str, Any]) -> set[str]:
    """允许 daemon role 与旧 dashboard 的 id/session 命名自然对齐。"""
    member_id = str(member.get("id", ""))
    values = {role, member_id, str(member.get("session", ""))}
    if role.lower() == "supervisor" or member_id.lower() == "signl3":
        values.update({"supervisor", "SignL3"})
    return {value.lower() for value in values if value}


def _health_by_role(registry: dict[str, Any], health: dict[str, Any]) -> dict[str, dict[str, Any]]:
    by_session = {
        str(item.get("session_id")): item
        for item in health.get("members", [])
        if isinstance(item, dict) and item.get("session_id")
    }
    result: dict[str, dict[str, Any]] = {}
    for role, entry in registry.get("roles", {}).items():
        if not isinstance(entry, dict):
            continue
        sid = entry.get("live_session_id") or entry.get("session_id")
        item = by_session.get(str(sid), {})
        result[role.lower()] = {**item, "daemon_session_id": sid}
    return result


def build_dashboard_data(
    registry: dict[str, Any], health: dict[str, Any], legacy: dict[str, Any]
) -> dict[str, Any]:
    """合并 daemon 状态与旧 dashboard 的业务字段；旧文件仅读取 goals/queue/messages。"""
    health_by_role = _health_by_role(registry, health)
    members: list[dict[str, Any]] = []
    for old_member in legacy.get("members", []):
        if not isinstance(old_member, dict):
            continue
        match: dict[str, Any] = {}
        aliases = _role_aliases("", old_member)
        for role, item in health_by_role.items():
            if role in aliases or str(item.get("daemon_session_id", "")).lower() in aliases:
                match = item
                break
        member = dict(old_member)
        member.update({
            "daemon_session_id": match.get("daemon_session_id"),
            "session_state": match.get("session_state", "unknown"),
            "has_active_prompt": bool(match.get("has_active_prompt", False)),
            "client_count": match.get("client_count", 0),
            "api_error": match.get("api_error"),
        })
        members.append(member)

    # daemon 中未出现在旧 members 的角色也保留，避免新 session 被 dashboard 丢弃。
    known_ids = {str(item.get("daemon_session_id")) for item in members if item.get("daemon_session_id")}
    for role, item in health_by_role.items():
        sid = item.get("daemon_session_id")
        if sid and str(sid) not in known_ids:
            members.append({
                "id": role,
                "role": role,
                "daemon_session_id": sid,
                "session_state": item.get("session_state", "unknown"),
                "has_active_prompt": bool(item.get("has_active_prompt", False)),
                "client_count": item.get("client_count", 0),
                "api_error": item.get("api_error"),
            })

    return {
        "version": "daemon-team-dashboard-v1",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "daemon_url": registry.get("daemon_url") or health.get("daemon_url"),
        "workspace": registry.get("workspace") or health.get("workspace"),
        "members": members,
        "goals": legacy.get("goals", []),
        "queue": legacy.get("queue", {}),
        "messages": legacy.get("messages", []),
    }


def generate(
    registry_path: Path = REGISTRY_PATH,
    health_path: Path = HEALTH_PATH,
    legacy_path: Path = LEGACY_DATA_PATH,
    output_path: Path = OUTPUT_PATH,
) -> dict[str, Any]:
    registry = read_json(registry_path, {})
    health = read_json(health_path, {})
    legacy = read_json(legacy_path, {})
    payload = build_dashboard_data(registry, health, legacy)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate daemon team dashboard v1 data")
    parser.add_argument("--registry", type=Path, default=REGISTRY_PATH)
    parser.add_argument("--health", type=Path, default=HEALTH_PATH)
    parser.add_argument("--legacy-data", type=Path, default=LEGACY_DATA_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()
    payload = generate(args.registry, args.health, args.legacy_data, args.output)
    print(json.dumps({"output": str(args.output), "members": len(payload["members"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()

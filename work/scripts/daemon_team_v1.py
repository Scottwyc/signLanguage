#!/usr/bin/env python3
"""Daemon team v1：独立于旧 TUI/tmux 链路的 session 盘点与健康采集适配器。

只读取 daemon HTTP API 和团队 registry，不修改 daemon session，也不写旧 team_health.json。
默认生产实例来自 .team/daemon_migration_4194_manifest.json；可用 --daemon-url 覆盖。
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

BASE = Path("/data/WYC/signLanguage/.team")
MANIFEST = BASE / "daemon_migration_4194_manifest.json"
TOPOLOGY = BASE / "team_topology.json"
OUT_DIR = BASE / "daemon_v1"
REGISTRY = OUT_DIR / "registry.json"
SNAPSHOT = OUT_DIR / "health_snapshot.json"


def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def request_json(base: str, path: str, timeout: float = 8.0) -> dict[str, Any]:
    request = urllib.request.Request(base.rstrip("/") + path, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        value = json.loads(response.read().decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"daemon response is not an object: {path}")
    return value


def workspace_path(workspace: str) -> str:
    return urllib.parse.quote(workspace, safe="")


def session_list(base: str, workspace: str) -> list[dict[str, Any]]:
    result = request_json(base, f"/workspace/{workspace_path(workspace)}/sessions?limit=100")
    return [item for item in result.get("sessions", []) if isinstance(item, dict)]


def derive_registry(manifest: dict[str, Any], sessions: list[dict[str, Any]], topology: dict[str, Any]) -> dict[str, Any]:
    by_id = {item.get("sessionId"): item for item in sessions if item.get("sessionId")}
    migrated: dict[str, Any] = {}
    for container_name in ("roles", "copied"):
        entries = manifest.get(container_name, {})
        if isinstance(entries, dict):
            migrated.update(entries)
    roles: dict[str, Any] = {}
    topo_roles = topology.get("roles", {}) if isinstance(topology, dict) else {}
    for stable_id, topo_entry in topo_roles.items():
        candidates = [stable_id, stable_id.lower(), f"{stable_id}-video", f"{stable_id}-overlay", f"{stable_id}-algorithm", f"{stable_id}-promoter", f"{stable_id}-ops", f"{stable_id}-research"]
        source_name = next((name for name in candidates if name in migrated), None)
        item = migrated.get(source_name, {}) if source_name else {}
        old_id = item.get("session_id") if isinstance(item, dict) else None
        roles[stable_id] = {
            "role": stable_id,
            "name": topo_entry.get("name") if isinstance(topo_entry, dict) else stable_id,
            "duty": topo_entry.get("duty") if isinstance(topo_entry, dict) else "",
            "session_id": old_id,
            "session_id_state": "listed" if old_id in by_id else "not_listed",
            "live": by_id.get(old_id),
            "source": f"daemon_migration_manifest.{source_name}" if source_name else "topology_unmapped",
        }
    # supervisor 的历史 session 被复制为新 ID；新 ID 是角色归属，旧 ID 仍保留为迁移证据。
    migrated_target = manifest.get("supervisor_migrated_target")
    assigned_ids = {r.get("session_id") for r in roles.values() if r.get("session_id")}
    if migrated_target:
        supervisor = roles.setdefault("SignL3", roles.get("supervisor", {"role": "SignL3"}))
        supervisor["live_session_id"] = migrated_target
        supervisor["live_session_source"] = "manifest.supervisor_migrated_target"
        supervisor["live"] = by_id.get(migrated_target)
        supervisor["session_id_state"] = "migrated_target_listed" if migrated_target in by_id else "migrated_target_not_listed"
        assigned_ids.add(migrated_target)
        roles.pop("supervisor", None)
    return {
        "version": "daemon-team-v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "daemon_url": manifest.get("daemon_url"),
        "workspace": manifest.get("workspace"),
        "roles": roles,
        "unassigned_sessions": [item for item in sessions if item.get("sessionId") not in assigned_ids],
    }


def classify(item: dict[str, Any], status: dict[str, Any] | None, events_error: str | None = None) -> str:
    if events_error:
        return "degraded"
    if item.get("isArchived"):
        return "archived"
    if item.get("hasTurnError"):
        return "api_error"
    if item.get("isWaitingForPermission") or item.get("isWaitingForUserQuestion"):
        return "waiting_input"
    if (status or {}).get("hasActivePrompt") or item.get("hasActivePrompt"):
        return "working"
    return "idle"


def collect_health(base: str, registry: dict[str, Any], sessions: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {item.get("sessionId"): item for item in sessions}
    members = []
    for role, entry in registry.get("roles", {}).items():
        sid = entry.get("live_session_id") or entry.get("session_id")
        item = by_id.get(sid, entry.get("live") or {})
        status = None
        error = None
        if sid:
            try:
                status = request_json(base, f"/session/{sid}/status")
            except (OSError, ValueError, urllib.error.HTTPError) as exc:
                error = f"{type(exc).__name__}: {exc}"
        members.append({
            "id": role,
            "session_id": sid,
            "session_state": classify(item, status, error),
            "listed": bool(item),
            "has_active_prompt": bool((status or {}).get("hasActivePrompt", item.get("hasActivePrompt", False))),
            "client_count": (status or {}).get("clientCount", item.get("clientCount", 0)),
            "updated_at": item.get("updatedAt"),
            "display_name": item.get("displayName"),
            "api_error": error,
        })
    return {
        "version": "daemon-team-v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "daemon_url": base,
        "workspace": registry.get("workspace"),
        "members": members,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--daemon-url")
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    manifest = read_json(args.manifest, {})
    base = args.daemon_url or manifest.get("daemon_url", "http://127.0.0.1:4194")
    workspace = manifest.get("workspace", str(Path.cwd()))
    capabilities = request_json(base, "/capabilities")
    daemon_status = request_json(base, "/daemon/status")
    sessions = session_list(base, workspace)
    topology = read_json(TOPOLOGY, {})
    registry = derive_registry(manifest, sessions, topology)
    registry["capabilities"] = capabilities.get("features", [])
    registry["daemon_status"] = {
        "status": daemon_status.get("status"),
        "generated_at": daemon_status.get("generatedAt"),
        "runtime": daemon_status.get("runtime", {}),
    }
    health = collect_health(base, registry, sessions)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "registry.json").write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.output_dir / "health_snapshot.json").write_text(json.dumps(health, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"registry": str(args.output_dir / "registry.json"), "health": str(args.output_dir / "health_snapshot.json"), "session_count": len(sessions)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

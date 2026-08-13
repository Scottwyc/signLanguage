from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "work" / "scripts"))

import daemon_team_dashboard_v1 as dashboard


def test_build_dashboard_data_preserves_legacy_business_fields_and_adds_daemon_state() -> None:
    registry = {
        "daemon_url": "http://127.0.0.1:4194",
        "workspace": "/tmp/workspace",
        "roles": {"supervisor": {"session_id": "old", "live_session_id": "live-1"}},
    }
    health = {
        "members": [{
            "id": "supervisor",
            "session_id": "live-1",
            "session_state": "working",
            "has_active_prompt": True,
            "client_count": 2,
            "api_error": None,
        }],
    }
    legacy = {
        "members": [{"id": "SignL3", "session": "SignL3-304", "alive": True}],
        "goals": [{"id": "goal-1"}],
        "queue": {"waiting": [{"id": "task-1"}]},
        "messages": ["hello"],
        "tmux": {"must_not": "appear"},
        "team_health": {"must_not": "appear"},
    }

    result = dashboard.build_dashboard_data(registry, health, legacy)

    assert result["goals"] == legacy["goals"]
    assert result["queue"] == legacy["queue"]
    assert result["messages"] == legacy["messages"]
    assert "tmux" not in result
    assert "team_health" not in result
    member = result["members"][0]
    assert member["daemon_session_id"] == "live-1"
    assert member["session_state"] == "working"
    assert member["has_active_prompt"] is True
    assert member["client_count"] == 2
    assert member["api_error"] is None


def test_generate_reads_fixtures_and_writes_dashboard(tmp_path: Path) -> None:
    registry = tmp_path / "registry.json"
    health = tmp_path / "health_snapshot.json"
    legacy = tmp_path / "data.json"
    output = tmp_path / "dashboard_data.json"
    registry.write_text(json.dumps({"roles": {}, "workspace": "/w"}), encoding="utf-8")
    health.write_text(json.dumps({"members": []}), encoding="utf-8")
    legacy.write_text(json.dumps({"goals": [], "queue": {}, "messages": [], "members": []}), encoding="utf-8")

    payload = dashboard.generate(registry, health, legacy, output)

    assert output.exists()
    assert json.loads(output.read_text(encoding="utf-8")) == payload
    assert payload["workspace"] == "/w"

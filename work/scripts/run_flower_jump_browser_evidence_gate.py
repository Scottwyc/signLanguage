#!/usr/bin/env python3
"""Validate strict browser-capture evidence boundaries for flower/jump.

This gate is read-only with respect to the formal web sample store. It copies
known saved flower/jump score results into an isolated fixture directory,
mutates only metadata, then runs the goal-readiness audit against each fixture.
It does not call /api/score, run Holistic, restart 5080, or move the marker.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence


REPO_ROOT = Path("/data/WYC/signLanguage")
SCRIPTS_DIR = REPO_ROOT / "work/scripts"
DEFAULT_OUTPUT_BASE = REPO_ROOT / "work/generated/scoring_mvp_run3"
DEFAULT_WEB_ROOT = REPO_ROOT / "work/generated/web_scoring_mvp"
DEFAULT_REQUEST_IDS = ["web_20260602_233343_899e6970", "web_20260602_233348_53e3df5d"]


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _fmt_bool(value: bool) -> str:
    return "PASS" if value else "FAIL"


def _run_command(cmd: Sequence[str]) -> Dict[str, Any]:
    completed = subprocess.run(
        list(cmd),
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        "command": list(cmd),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def _make_watch_status(path: Path, request_ids: Sequence[str]) -> None:
    by_word: Dict[str, int] = {}
    for request_id in request_ids:
        source_path = DEFAULT_WEB_ROOT / request_id / "scoring_result.json"
        word = str((_load_json(source_path)).get("target_word") or "")
        by_word[word] = by_word.get(word, 0) + 1

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "event": "diagnose_done",
        "watcher_pid": 1,
        "status": {
            "checked_at": datetime.now().isoformat(timespec="seconds"),
            "marker_last_request_id": "fixture_marker",
            "new_summary": {
                "count": len(request_ids),
                "first_request_id": request_ids[0] if request_ids else "",
                "last_request_id": request_ids[-1] if request_ids else "",
                "by_word": by_word,
            },
            "target_summary": {
                "count": len(request_ids),
                "first_request_id": request_ids[0] if request_ids else "",
                "last_request_id": request_ids[-1] if request_ids else "",
                "by_word": by_word,
            },
            "target_request_ids": list(request_ids),
        },
        "latest_diagnosis": {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "web_root": "",
            "diagnosed_request_ids": list(request_ids),
            "regression_returncode": 0,
            "confusion_returncode": 0,
            "visual_returncode": 0,
        },
    }
    _write_json(path, payload)


def _clone_variant(
    fixture_root: Path,
    name: str,
    request_ids: Sequence[str],
    mutate: Callable[[Dict[str, Any]], None],
) -> Path:
    root = fixture_root / name
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    for request_id in request_ids:
        source_dir = DEFAULT_WEB_ROOT / request_id
        target_dir = root / request_id
        if not source_dir.exists():
            raise FileNotFoundError(f"missing source request directory: {source_dir}")
        shutil.copytree(source_dir, target_dir)
        result_path = target_dir / "scoring_result.json"
        payload = _load_json(result_path)
        mutate(payload)
        _write_json(result_path, payload)
    return root


def _clear_client(payload: Dict[str, Any]) -> None:
    payload["client_source"] = None
    payload["client"] = {"source": None, "session_id": None, "capture_id": None}


def _mutate_legacy(payload: Dict[str, Any]) -> None:
    _clear_client(payload)
    payload["frame_weights"] = None


def _mutate_nonuniform(payload: Dict[str, Any]) -> None:
    _clear_client(payload)
    count = int(payload.get("frame_count") or 0)
    payload["frame_weights"] = [1.0 + ((idx % 5) - 2) * 0.05 for idx in range(count)]


def _mutate_uniform(payload: Dict[str, Any]) -> None:
    _clear_client(payload)
    count = int(payload.get("frame_count") or 0)
    payload["frame_weights"] = [1.0 for _ in range(count)]


def _mutate_client_source(payload: Dict[str, Any]) -> None:
    payload["frame_weights"] = None
    payload["client_source"] = "browser_camera"
    payload["client"] = {
        "source": "browser_camera",
        "session_id": "fixture_session",
        "capture_id": "fixture_capture",
    }


def _case_specs() -> List[Dict[str, Any]]:
    return [
        {
            "name": "legacy_frame_slice_only",
            "mutate": _mutate_legacy,
            "expected_ready": False,
            "expected_evidence_passed": False,
            "expected_levels": {"legacy_frame_slice_metadata"},
            "expected_reasons": {"legacy_frame_slice_metadata_not_completion_evidence"},
        },
        {
            "name": "strong_nonuniform_frame_weights",
            "mutate": _mutate_nonuniform,
            "expected_ready": True,
            "expected_evidence_passed": True,
            "expected_levels": {"strong_nonuniform_frame_weights"},
            "expected_reasons": {"strong_nonuniform_frame_weights"},
        },
        {
            "name": "uniform_frame_weights",
            "mutate": _mutate_uniform,
            "expected_ready": False,
            "expected_evidence_passed": False,
            "expected_levels": {"none"},
            "expected_reasons": {"source_metadata_missing"},
        },
        {
            "name": "strong_client_source",
            "mutate": _mutate_client_source,
            "expected_ready": True,
            "expected_evidence_passed": True,
            "expected_levels": {"strong_client_source"},
            "expected_reasons": {"strong_client_source"},
        },
    ]


def _run_audit(
    case_name: str,
    web_root: Path,
    watch_status_json: Path,
    output_dir: Path,
    quality_gate_json: Optional[Path],
) -> Dict[str, Any]:
    case_output = output_dir / case_name
    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "audit_flower_jump_goal_readiness.py"),
        "--watch-status-json",
        str(watch_status_json),
        "--web-root",
        str(web_root),
        "--output-dir",
        str(case_output),
    ]
    if quality_gate_json:
        cmd.extend(["--quality-gate-json", str(quality_gate_json)])
    run = _run_command(cmd)
    audit_json = case_output / "flower_jump_goal_readiness_audit.json"
    payload = _load_json(audit_json) if audit_json.exists() else {}
    return {"run": run, "audit_json": str(audit_json), "audit_payload": payload}


def _evaluate_case(spec: Dict[str, Any], audit: Dict[str, Any]) -> Dict[str, Any]:
    payload = audit.get("audit_payload") or {}
    evidence = payload.get("browser_capture_evidence") or {}
    rows = evidence.get("rows") or []
    row_levels = {str(row.get("evidence_level") or "none") for row in rows}
    row_reasons = {str(row.get("reason") or "") for row in rows}
    row_pass_values = [bool(row.get("passed")) for row in rows]
    expected_ready = bool(spec["expected_ready"])
    expected_evidence = bool(spec["expected_evidence_passed"])
    checks = {
        "audit_command_returned": int((audit.get("run") or {}).get("returncode") or 0) == 0,
        "ready_matches": bool(payload.get("ready_to_complete")) == expected_ready,
        "evidence_passed_matches": bool(evidence.get("passed")) == expected_evidence,
        "all_rows_expected_pass": all(row_pass_values) == expected_evidence if row_pass_values else not expected_evidence,
        "levels_match": row_levels == set(spec["expected_levels"]),
        "reasons_match": row_reasons == set(spec["expected_reasons"]),
    }
    passed = all(checks.values())
    return {
        "name": spec["name"],
        "passed": passed,
        "expected_ready": expected_ready,
        "actual_ready": bool(payload.get("ready_to_complete")),
        "expected_evidence_passed": expected_evidence,
        "actual_evidence_passed": bool(evidence.get("passed")),
        "row_levels": sorted(row_levels),
        "row_reasons": sorted(row_reasons),
        "row_pass_values": row_pass_values,
        "checks": checks,
        "audit_json": audit.get("audit_json"),
        "stdout": (audit.get("run") or {}).get("stdout", ""),
        "stderr": (audit.get("run") or {}).get("stderr", ""),
    }


def _build_markdown(payload: Dict[str, Any]) -> str:
    lines = [
        "# 花/跳浏览器采集证据门",
        "",
        f"- generated_at: `{payload.get('generated_at')}`",
        f"- status: **{'PASS' if payload.get('passed') else 'FAIL'}**",
        f"- fixture_root: `{payload.get('fixture_root')}`",
        f"- watch_status_json: `{payload.get('watch_status_json')}`",
        "- 口径：只复制保存样本到隔离目录并修改 metadata；不调用 `/api/score`，不运行 Holistic，不移动 marker。",
        "",
        "| case | result | ready | evidence | levels | reasons |",
        "|---|---|---:|---:|---|---|",
    ]
    for case in payload.get("cases") or []:
        lines.append(
            f"| `{case['name']}` | `{_fmt_bool(case['passed'])}` | "
            f"`{case['actual_ready']}` | `{case['actual_evidence_passed']}` | "
            f"`{', '.join(case['row_levels'])}` | `{', '.join(case['row_reasons'])}` |"
        )
    lines.extend(["", "## 结论", ""])
    if payload.get("passed"):
        lines.append("- 严格浏览器证据门通过：非均匀 frame_weights / browser client_source 可关闭证据门，legacy 或均匀权重不会误关。")
    else:
        lines.append("- 严格浏览器证据门失败：需要检查上表中不符合预期的 case。")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_browser_evidence_gate_current"))
    parser.add_argument("--quality-gate-json", default="")
    parser.add_argument("--request-ids", nargs="*", default=DEFAULT_REQUEST_IDS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    fixture_root = output_dir / "fixtures"
    if fixture_root.exists():
        shutil.rmtree(fixture_root)
    fixture_root.mkdir(parents=True)
    request_ids = [str(item) for item in args.request_ids]
    watch_status_json = fixture_root / "watch_status.json"
    _make_watch_status(watch_status_json, request_ids)
    quality_gate_json = Path(args.quality_gate_json) if args.quality_gate_json else None

    cases: List[Dict[str, Any]] = []
    for spec in _case_specs():
        web_root = _clone_variant(fixture_root, str(spec["name"]), request_ids, spec["mutate"])
        audit = _run_audit(str(spec["name"]), web_root, watch_status_json, output_dir, quality_gate_json)
        cases.append(_evaluate_case(spec, audit))

    passed = all(bool(case["passed"]) for case in cases)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "passed": passed,
        "fixture_root": str(fixture_root),
        "watch_status_json": str(watch_status_json),
        "request_ids": request_ids,
        "cases": cases,
    }
    json_path = output_dir / "flower_jump_browser_evidence_gate.json"
    md_path = output_dir / "flower_jump_browser_evidence_gate.md"
    _write_json(json_path, payload)
    md_path.write_text(_build_markdown(payload), encoding="utf-8")

    print(f"已生成花/跳浏览器采集证据门 JSON：{json_path}")
    print(f"已生成花/跳浏览器采集证据门报告：{md_path}")
    print(f"综合状态：{'PASS' if passed else 'FAIL'}")
    for case in cases:
        print(
            f"- {case['name']}: {_fmt_bool(case['passed'])} "
            f"ready={case['actual_ready']} evidence={case['actual_evidence_passed']} "
            f"levels={case['row_levels']}"
        )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Executable browser upload-weight simulation gate.

This gate does not call /api/score, move the formal marker, or restart the
backend. It extracts the current browser sampling helpers from static app.js and
runs synthetic motion/static cases in Node.js so retest readiness can verify
that the frontend upload path produces nonuniform frame weights for real motion
and uniform weights for static clips.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Sequence


REPO_ROOT = Path("/data/WYC/signLanguage")
DEFAULT_APP_JS = REPO_ROOT / "work/web/static/app.js"
DEFAULT_OUTPUT_BASE = REPO_ROOT / "work/generated/scoring_mvp_run3"


def _find_matching_brace(text: str, open_index: int) -> int:
    depth = 0
    quote: str | None = None
    escape = False
    line_comment = False
    block_comment = False
    for idx in range(open_index, len(text)):
        ch = text[idx]
        nxt = text[idx + 1] if idx + 1 < len(text) else ""
        if line_comment:
            if ch == "\n":
                line_comment = False
            continue
        if block_comment:
            if ch == "*" and nxt == "/":
                block_comment = False
            continue
        if quote:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                quote = None
            continue
        if ch == "/" and nxt == "/":
            line_comment = True
            continue
        if ch == "/" and nxt == "*":
            block_comment = True
            continue
        if ch in ("'", '"', "`"):
            quote = ch
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return idx
    raise ValueError(f"unmatched brace at {open_index}")


def _extract_function(text: str, name: str) -> str:
    marker = f"function {name}("
    start = text.find(marker)
    if start < 0:
        raise ValueError(f"function not found: {name}")
    brace_start = text.find("{", start)
    if brace_start < 0:
        raise ValueError(f"function brace not found: {name}")
    brace_end = _find_matching_brace(text, brace_start)
    return text[start : brace_end + 1]


def _extract_const_object(text: str, name: str) -> str:
    marker = f"const {name} ="
    start = text.find(marker)
    if start < 0:
        raise ValueError(f"const object not found: {name}")
    brace_start = text.find("{", start)
    if brace_start < 0:
        raise ValueError(f"const object brace not found: {name}")
    brace_end = _find_matching_brace(text, brace_start)
    return text[start : brace_end + 1] + ";"


def _node_simulation_code(app_js_text: str) -> str:
    capture_recommendations = _extract_const_object(app_js_text, "CAPTURE_RECOMMENDATIONS")
    signature_motion = _extract_function(app_js_text, "signatureMotion")
    normalize_frame_weights = _extract_function(app_js_text, "normalizeFrameWeights")
    select_energy_coverage = _extract_function(app_js_text, "selectEnergyCoverageFrames")
    return f"""
{capture_recommendations}
{signature_motion}
{normalize_frame_weights}
{select_energy_coverage}

const SIG_LEN = 32 * 24;

function gaussian(index, center, width) {{
  const x = (index - center) / width;
  return Math.exp(-0.5 * x * x);
}}

function scenarioSignatures(name, count) {{
  const signatures = [];
  for (let i = 0; i < count; i += 1) {{
    const arr = new Array(SIG_LEN).fill(0);
    if (name === "flower_opening_motion") {{
      const opening = Math.min(1, Math.max(0, (i - count * 0.18) / (count * 0.58)));
      const lift = Math.min(1, Math.max(0, (i - count * 0.10) / (count * 0.72)));
      arr[180] = opening;
      arr[181] = Math.sin(opening * Math.PI) * 0.55;
      arr[214] = lift * 0.7;
      arr[215] = gaussian(i, count * 0.58, count * 0.16) * 0.35;
    }} else if (name === "jump_burst_motion") {{
      const up = gaussian(i, count * 0.48, count * 0.09);
      const down = gaussian(i, count * 0.62, count * 0.08);
      arr[300] = up;
      arr[301] = down * 0.85;
      arr[302] = Math.max(0, up - down) * 0.55;
    }} else if (name === "static_hold") {{
      arr[180] = 0.35;
      arr[300] = 0.2;
    }} else {{
      throw new Error(`unknown scenario ${{name}}`);
    }}
    signatures.push(arr);
  }}
  return signatures;
}}

function smoothEnergies(signatures) {{
  const raw = [];
  let prev = null;
  for (const signature of signatures) {{
    raw.push(signatureMotion(prev, signature));
    prev = signature;
  }}
  return raw.map((energy, idx) => {{
    const left = raw[Math.max(0, idx - 1)];
    const right = raw[Math.min(raw.length - 1, idx + 1)];
    return 0.25 * left + 0.5 * energy + 0.25 * right;
  }});
}}

function capturePlan(word, durationSec, uploadFps) {{
  const rec = CAPTURE_RECOMMENDATIONS[word] || CAPTURE_RECOMMENDATIONS.default;
  const targetFrames = Math.max(rec.minFrames, Math.min(90, Math.round(durationSec * uploadFps)));
  const candidateFps = Math.max(uploadFps, Math.min(18, uploadFps * 2));
  const candidateFrames = Math.max(targetFrames, Math.round(durationSec * candidateFps));
  return {{ word, durationSec, uploadFps, targetFrames, candidateFps, candidateFrames, minFrames: rec.minFrames }};
}}

function simulateCase(name, word, durationSec, uploadFps) {{
  const plan = capturePlan(word, durationSec, uploadFps);
  const signatures = scenarioSignatures(name, plan.candidateFrames);
  const energies = smoothEnergies(signatures);
  const weights = normalizeFrameWeights(energies);
  const candidates = energies.map((energy, idx) => ({{
    candidateIndex: idx,
    frame: {{ id: idx }},
    energy,
    energySmooth: energy,
    frameWeight: weights[idx] || 1.0,
  }}));
  const selected = selectEnergyCoverageFrames(candidates, plan.targetFrames);
  const frameIndices = selected.map((item) => item.candidateIndex);
  const frameWeights = selected.map((item) => item.uploadWeight);
  const rankedEnergy = energies
    .map((energy, idx) => ({{ idx, energy }}))
    .sort((a, b) => b.energy - a.energy);
  return {{
    name,
    word,
    plan,
    selected_count: selected.length,
    frame_indices: frameIndices,
    frame_weights: frameWeights,
    weights_min: Math.min(...frameWeights),
    weights_max: Math.max(...frameWeights),
    weights_range: Math.max(...frameWeights) - Math.min(...frameWeights),
    weights_unique_4dp: new Set(frameWeights.map((value) => Number(value).toFixed(4))).size,
    top_energy_indices: rankedEnergy.slice(0, 6).map((row) => row.idx),
    selected_top_energy_count: rankedEnergy.slice(0, 6).filter((row) => frameIndices.includes(row.idx)).length,
    selected_in_order: frameIndices.every((value, idx) => idx === 0 || frameIndices[idx - 1] < value),
    includes_first_frame: frameIndices.includes(0),
    includes_last_frame: frameIndices.includes(plan.candidateFrames - 1),
    nonuniform_weights: Math.max(...frameWeights) - Math.min(...frameWeights) >= 0.10,
  }};
}}

const cases = [
  simulateCase("flower_opening_motion", "花", 2.5, 5),
  simulateCase("jump_burst_motion", "跳", 2.0, 5),
  simulateCase("static_hold", "花", 2.5, 5),
];
console.log(JSON.stringify({{ cases }}, null, 2));
"""


def _run_node_simulation(app_js_path: Path) -> dict[str, Any]:
    app_js_text = app_js_path.read_text(encoding="utf-8")
    node_code = _node_simulation_code(app_js_text)
    completed = subprocess.run(
        ["node", "-"],
        input=node_code,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        return {
            "ok": False,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "cases": [],
        }
    json_start = completed.stdout.find("{")
    json_text = completed.stdout[json_start:] if json_start >= 0 else completed.stdout
    try:
        payload = json.loads(json_text)
    except json.JSONDecodeError as exc:
        return {
            "ok": False,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": f"{completed.stderr}\nJSON parse failed: {exc}",
            "cases": [],
        }
    payload["ok"] = True
    payload["returncode"] = completed.returncode
    payload["stderr"] = completed.stderr
    return payload


def _case_checks(case: dict[str, Any]) -> list[dict[str, Any]]:
    name = str(case.get("name") or "")
    plan = case.get("plan") if isinstance(case.get("plan"), dict) else {}
    indices = case.get("frame_indices") if isinstance(case.get("frame_indices"), list) else []
    checks = [
        {
            "name": "selected_count_matches_target",
            "passed": case.get("selected_count") == plan.get("targetFrames"),
            "detail": f"selected={case.get('selected_count')} target={plan.get('targetFrames')}",
        },
        {
            "name": "target_frames_meet_recommendation",
            "passed": (plan.get("targetFrames") or 0) >= (plan.get("minFrames") or math.inf),
            "detail": f"target={plan.get('targetFrames')} min={plan.get('minFrames')}",
        },
        {
            "name": "candidate_pool_is_denser_than_upload",
            "passed": (plan.get("candidateFrames") or 0) > (plan.get("targetFrames") or math.inf),
            "detail": f"candidate={plan.get('candidateFrames')} target={plan.get('targetFrames')}",
        },
        {
            "name": "frame_indices_strictly_in_order",
            "passed": bool(case.get("selected_in_order")),
            "detail": f"indices={indices}",
        },
        {
            "name": "coverage_keeps_start_and_end",
            "passed": bool(case.get("includes_first_frame") and case.get("includes_last_frame")),
            "detail": f"first={case.get('includes_first_frame')} last={case.get('includes_last_frame')}",
        },
    ]
    if name == "static_hold":
        checks.extend(
            [
                {
                    "name": "static_weights_remain_uniform",
                    "passed": not bool(case.get("nonuniform_weights")) and float(case.get("weights_range") or 0.0) < 1e-6,
                    "detail": f"range={case.get('weights_range')}",
                },
                {
                    "name": "static_not_completion_strong_frame_weight_evidence",
                    "passed": not bool(case.get("nonuniform_weights")),
                    "detail": f"nonuniform={case.get('nonuniform_weights')}",
                },
            ]
        )
    else:
        checks.extend(
            [
                {
                    "name": "motion_weights_are_nonuniform",
                    "passed": bool(case.get("nonuniform_weights")),
                    "detail": f"range={case.get('weights_range')}, min={case.get('weights_min')}, max={case.get('weights_max')}",
                },
                {
                    "name": "motion_weight_has_multiple_levels",
                    "passed": int(case.get("weights_unique_4dp") or 0) >= 4,
                    "detail": f"unique_4dp={case.get('weights_unique_4dp')}",
                },
                {
                    "name": "motion_peaks_are_selected",
                    "passed": int(case.get("selected_top_energy_count") or 0) >= 4,
                    "detail": (
                        f"selected_top_energy_count={case.get('selected_top_energy_count')} "
                        f"top_energy_indices={case.get('top_energy_indices')}"
                    ),
                },
            ]
        )
    return checks


def _build_report(payload: dict[str, Any], output_dir: Path, app_js_path: Path) -> dict[str, Any]:
    cases = payload.get("cases") if isinstance(payload.get("cases"), list) else []
    report_cases = []
    for case in cases:
        checks = _case_checks(case)
        report_cases.append(
            {
                **case,
                "checks": checks,
                "passed": all(bool(row.get("passed")) for row in checks),
            }
        )
    passed = bool(payload.get("ok") and report_cases and all(case.get("passed") for case in report_cases))
    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "passed": passed,
        "app_js": str(app_js_path),
        "node_returncode": payload.get("returncode"),
        "node_stdout": payload.get("stdout") or "",
        "node_stderr": payload.get("stderr") or "",
        "cases": report_cases,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "browser_upload_weight_simulation_gate.json"
    md_path = output_dir / "browser_upload_weight_simulation_gate.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Browser Upload Weight Simulation Gate",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- status: **{'PASS' if passed else 'FAIL'}**",
        f"- app_js: `{app_js_path}`",
        f"- node_returncode: `{payload.get('returncode')}`",
        "",
        "## Cases",
        "",
        "| case | word | status | selected/target | candidate | weight range | unique | top selected | endpoints |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for case in report_cases:
        plan = case.get("plan") or {}
        endpoints = f"{case.get('includes_first_frame')}/{case.get('includes_last_frame')}"
        lines.append(
            f"| `{case.get('name')}` | `{case.get('word')}` | `{'PASS' if case.get('passed') else 'FAIL'}` | "
            f"{case.get('selected_count')}/{plan.get('targetFrames')} | {plan.get('candidateFrames')} | "
            f"{float(case.get('weights_range') or 0.0):.4f} | {case.get('weights_unique_4dp')} | "
            f"{case.get('selected_top_energy_count')} | {endpoints} |"
        )
    lines.extend(["", "## Checks", "", "| case | check | result | detail |", "| --- | --- | --- | --- |"])
    for case in report_cases:
        for check in case.get("checks") or []:
            detail = str(check.get("detail") or "").replace("|", "\\|").replace("\n", " ")
            lines.append(
                f"| `{case.get('name')}` | `{check.get('name')}` | "
                f"`{'PASS' if check.get('passed') else 'FAIL'}` | {detail} |"
            )
    if payload.get("stderr"):
        lines.extend(["", "## Node Stderr", "", "```", str(payload.get("stderr")), "```"])
    if payload.get("stdout") and not cases:
        lines.extend(["", "## Node Stdout", "", "```", str(payload.get("stdout")), "```"])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    report["json_path"] = str(json_path)
    report["md_path"] = str(md_path)
    return report


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-js", type=Path, default=DEFAULT_APP_JS)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_BASE / f"browser_upload_weight_simulation_gate_{stamp}",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    payload = _run_node_simulation(args.app_js)
    report = _build_report(payload, args.output_dir, args.app_js)
    print(f"browser upload weight simulation: {'PASS' if report['passed'] else 'FAIL'}")
    print(f"JSON: {report['json_path']}")
    print(f"MD: {report['md_path']}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run the full flower/jump scoring quality gate.

This wrapper collects the checks that are currently needed before we can
claim a scoring change is safe for the flower/jump web workflow:

1. saved web/API sample regression with the active template root
2. saved web/API cross-word confusion gate: flower and jump queries stay separated
3. synthetic robustness cross-confusion gate: positive perturbations stay separated by word
4. offline discrimination gate: target variants high, other/fake actions low
5. pose/camera robustness gate: sitting/global-position perturbations high
6. framing robustness gate: whole-person zoom, slight tilt, and off-center framing remain high
7. aspect-ratio robustness gate: mild non-uniform camera/canvas stretch remains high
8. camera-roll robustness gate: whole-skeleton image-plane tilt remains high after derived-feature rebuild
9. body-anchor robustness gate: non-core pose/face drift does not drag down hand signs
10. z/depth robustness gate: moderate Holistic depth drift remains high
11. edge-clipping robustness gate: noncritical frame-edge clipping high, core clipping low
12. browser mirror robustness gate: horizontal camera/previews remain high
13. hand-role robustness gate: single-hand dominance can swap, role-specific jump cannot
14. hand-label flicker robustness gate: brief detector side flicker high, severe flicker low
15. hand-dropout burst robustness gate: brief contiguous hand detector gaps high, sustained core gaps low
16. frame-count robustness gate: recommended web sampling lengths remain high
17. temporal-stutter robustness gate: short browser frame freezes high, sustained core freezes low
18. temporal-rate robustness gate: local/global signing speed changes remain high
19. composite browser robustness gate: mild combined web perturbation stacks remain high
20. frame-weights robustness gate: browser-upload motion-weight patterns and malformed upload weights remain high after sanitization
21. coordinate-precision robustness gate: camera/grid coordinate quantization remains high
22. motion-amplitude/blur robustness gate: mild amplitude shifts high, heavy smoothing diagnostic
23. landmark-noise robustness gate: mild hand jitter and rare hand-frame instability remain high
24. landmark-spike robustness gate: isolated/sparse large hand outliers remain high
25. fingertip-occlusion robustness gate: short fingertip mask loss high, sustained core-tip loss low
26. hand-shape scale robustness gate: local hand-size/aspect changes remain high
27. hand-orientation robustness gate: local wrist/hand rotation changes remain high
28. missing/mask robustness gate: noncritical masks high, core-hand masks low
29. temporal padding gate: prep/end static holds tolerated, purely static clips rejected
30. action-crop robustness gate: mild recording-boundary crops high, missing-core half clips low
31. action-repeat robustness gate: repeated complete recordings high, setup-only clips low
32. phase-order robustness gate: monotonic timing warps high, reversed/scrambled phases low
33. non-core hand/finger distractor robustness gate: irrelevant hand/finger motion remains high
34. relation-geometry robustness gate: mild two-hand relation geometry changes remain high
35. core hand-shape amplitude robustness gate: flower opening and jump two-finger shape amplitude changes remain high
36. perspective/shear robustness gate: mild oblique-camera shear and z-perspective drift remain high
37. palm-anchor occlusion robustness gate: short wrist/MCP anchor mask loss high, sustained core-anchor loss low
38. inter-hand temporal desync robustness gate: mild one-hand phase lead/lag remains high
39. temporal order jitter robustness gate: small adjacent-frame order glitches remain high
40. finger identity jitter robustness gate: neighboring finger-chain label confusion remains high
41. hand-scale flicker robustness gate: temporal detector hand-box breathing remains high
42. hand-center flicker robustness gate: temporal detector hand-box center wobble remains high
43. global-framing flicker robustness gate: temporal whole-frame pan/zoom drift remains high
44. finger mid-joint occlusion robustness gate: short PIP/DIP/thumb-IP mask loss remains high
45. z-flicker robustness gate: temporal Holistic z/depth breathing remains high
46. hand-trajectory interpolation robustness gate: short tracker interpolation gaps remain high
47. hand z-tilt robustness gate: local out-of-plane palm tilt remains high
48. finger curl style robustness gate: mild user finger bend remains high
49. finger length style robustness gate: mild user finger proportion changes remain high
50. moving setup/exit robustness gate: dynamic non-semantic entry/exit frames tolerated
51. core-phase speed robustness gate: word-specific semantic core speed style changes remain high
52. hand-confidence attenuation robustness gate: near-threshold hand landmark confidence remains high
53. motion-energy sampling robustness gate: frontend energy-selected frame sets remain high
54. rolling-shutter shear robustness gate: mild time-varying line skew remains high
55. hand-detail-loss robustness gate: low-detail inner-joint simplification remains high
56. hand-stream latency robustness gate: mild hand landmark stream frame delay remains high
57. ghost-hand duplicate robustness gate: short/sparse single-hand duplicate-as-both-hands remains high
58. hand-overlap merge robustness gate: short/sparse hand landmark merge remains high
59. wrist-anchor drift robustness gate: short/sparse wrist/MCP palm-root coordinate drift remains high
60. finger-chain latency robustness gate: short/sparse intra-hand distal finger latency remains high
61. finger-fan geometry robustness gate: mild distal inter-finger fan drift remains high
62. finger-base geometry robustness gate: mild MCP/CMC base drift remains high
63. finger-chain confidence robustness gate: local finger-chain soft confidence loss remains high
64. finger-chain temporal smoothing robustness gate: local distal finger-chain low-pass smoothing remains high
65. finite-coordinate robustness gate: isolated NaN/Inf landmarks are sanitized as missing points
66. bounded-coordinate robustness gate: isolated hand/face out-of-frame x/y, z-depth outliers, exact-zero placeholders, and collapsed hands are sanitized as missing points

It does not run Holistic and does not restart the 5080 backend. The web
regression reuses saved Holistic JSON; the offline gates reuse cached template
Holistic JSON.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


REPO_ROOT = Path("/data/WYC/signLanguage")
SCRIPTS_DIR = REPO_ROOT / "work/scripts"
DEFAULT_OUTPUT_BASE = REPO_ROOT / "work/generated/scoring_mvp_run3"
DEFAULT_WEB_ROOT = REPO_ROOT / "work/generated/web_scoring_mvp"
DEFAULT_TEMPLATE_ROOT = REPO_ROOT / "work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results"
DEFAULT_SEMANTIC_PROFILE_JSON = REPO_ROOT / "work/generated/scoring_semantic_profiles/sign_semantic_weights.json"
DEFAULT_BACKEND_URL = "http://127.0.0.1:5080"


def _safe_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt(value: Any, digits: int = 3) -> str:
    number = _safe_float(value)
    if number is None:
        return "-"
    return f"{number:.{digits}f}"


def _run_command(name: str, cmd: Sequence[str], cwd: Path) -> Dict[str, Any]:
    started_at = datetime.now().isoformat(timespec="seconds")
    completed = subprocess.run(
        list(cmd),
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        "name": name,
        "command": list(cmd),
        "started_at": started_at,
        "finished_at": datetime.now().isoformat(timespec="seconds"),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_marker_status() -> Dict[str, Any]:
    cmd = [sys.executable, str(SCRIPTS_DIR / "manage_web_sample_marker.py"), "status"]
    completed = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    payload: Dict[str, Any] = {
        "command": cmd,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    if completed.returncode == 0:
        try:
            payload["payload"] = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            payload["parse_error"] = str(exc)
    return payload


def _web_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    diagnostics = payload.get("diagnostics") or {}
    diag_summary = diagnostics.get("summary") or {}
    effective = diag_summary.get("effective") or {}
    by_word = diag_summary.get("by_word") or {}
    replay = (payload.get("replay") or {}).get("summary") or {}
    return {
        "passed": bool(payload.get("passed")),
        "samples": replay.get("samples"),
        "replay_errors": replay.get("errors"),
        "diagnostics_samples": diag_summary.get("samples"),
        "diagnostics_errors": diag_summary.get("errors"),
        "effective_reliable": effective.get("reliable_samples"),
        "effective_normal_or_borderline": effective.get("normal_or_borderline"),
        "effective_low": effective.get("low"),
        "effective_rate": effective.get("normal_or_borderline_rate"),
        "by_word_effective": {
            word: (item.get("effective") or {})
            for word, item in by_word.items()
        },
        "gates": payload.get("gates") or [],
    }


def _confusion_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    summary = payload.get("summary") or {}
    by_word: Dict[str, Dict[str, Any]] = {}
    for word, item in (summary.get("by_word") or {}).items():
        by_word[word] = {
            "samples": item.get("samples"),
            "eligible": item.get("eligible"),
            "pass": item.get("pass"),
            "fail": item.get("fail"),
            "other_score_max": item.get("other_score_max"),
            "margin_min": item.get("margin_min"),
            "margin_mean": item.get("margin_mean"),
        }
    return {
        "passed": bool(payload.get("passed")),
        "samples": summary.get("samples"),
        "errors": summary.get("errors"),
        "eligible": summary.get("eligible"),
        "pass": summary.get("pass"),
        "fail": summary.get("fail"),
        "by_word": by_word,
    }


def _discrimination_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        suite = item.get("suite") or {}
        top_negative = item.get("top_negative") or {}
        weakest = item.get("weakest_positive") or {}
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(suite.get("gate_pass")),
                "min_positive_score": suite.get("min_positive_score"),
                "max_negative_score": suite.get("max_negative_score"),
                "margin": suite.get("margin"),
                "top_negative": top_negative.get("case_id"),
                "weakest_positive": weakest.get("case_id"),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _synthetic_confusion_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("summary_by_word") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": int(item.get("fail") or 0) == 0 and int(item.get("samples") or 0) > 0,
                "samples": item.get("samples"),
                "pass": item.get("pass"),
                "fail": item.get("fail"),
                "target_score_min": item.get("target_score_min"),
                "cross_score_max": item.get("cross_score_max"),
                "margin_min": item.get("margin_min"),
                "weakest_variant": item.get("weakest_variant"),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _pose_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "min_observed_score": item.get("min_observed_score"),
                "weakest_variant": item.get("weakest_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _framing_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _aspect_ratio_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _camera_roll_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _body_anchor_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _depth_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _z_flicker_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _hand_trajectory_interpolation_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _edge_clipping_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "strongest_negative_score": item.get("strongest_negative_score"),
                "strongest_negative_variant": item.get("strongest_negative_variant"),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _mirror_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _hand_role_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "strongest_negative_score": item.get("strongest_negative_score"),
                "strongest_negative_variant": item.get("strongest_negative_variant"),
            }
        )
    return {
        "passed": bool(payload.get("passed")),
        "accepted_negative_quality": payload.get("accepted_negative_quality"),
        "rows": rows,
    }


def _noncore_hand_distractor_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _relation_geometry_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "strongest_negative_score": item.get("strongest_negative_score"),
                "strongest_negative_variant": item.get("strongest_negative_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
                "negative_max_score": item.get("negative_max_score", payload.get("negative_max_score")),
            }
        )
    return {
        "passed": bool(payload.get("passed")),
        "accepted_negative_quality": payload.get("accepted_negative_quality"),
        "rows": rows,
    }


def _core_shape_amplitude_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "strongest_negative_score": item.get("strongest_negative_score"),
                "strongest_negative_variant": item.get("strongest_negative_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
                "negative_max_score": item.get("negative_max_score", payload.get("negative_max_score")),
            }
        )
    return {
        "passed": bool(payload.get("passed")),
        "accepted_negative_quality": payload.get("accepted_negative_quality"),
        "rows": rows,
    }


def _perspective_shear_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _hand_label_flicker_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "strongest_negative_score": item.get("strongest_negative_score"),
                "strongest_negative_variant": item.get("strongest_negative_variant"),
            }
        )
    return {
        "passed": bool(payload.get("passed")),
        "accepted_negative_quality": payload.get("accepted_negative_quality"),
        "rows": rows,
    }


def _hand_dropout_burst_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "strongest_negative_score": item.get("strongest_negative_score"),
                "strongest_negative_variant": item.get("strongest_negative_variant"),
            }
        )
    return {
        "passed": bool(payload.get("passed")),
        "accepted_negative_quality": payload.get("accepted_negative_quality"),
        "rows": rows,
    }


def _frame_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "min_observed_score": item.get("min_observed_score"),
                "weakest_variant": item.get("weakest_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
                "min_valid_frames": item.get("min_valid_frames"),
                "diagnostic_min_score": item.get("diagnostic_min_score"),
                "diagnostic_weakest_variant": item.get("diagnostic_weakest_variant"),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _temporal_stutter_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "strongest_negative_score": item.get("strongest_negative_score"),
                "strongest_negative_variant": item.get("strongest_negative_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
            }
        )
    return {
        "passed": bool(payload.get("passed")),
        "accepted_negative_quality": payload.get("accepted_negative_quality"),
        "rows": rows,
    }


def _temporal_rate_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": payload.get("min_score"),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _temporal_metadata_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _composite_browser_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": payload.get("min_score"),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _frame_weight_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _coordinate_precision_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _motion_blur_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _landmark_noise_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _landmark_spike_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _fingertip_occlusion_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "strongest_negative_score": item.get("strongest_negative_score"),
                "strongest_negative_variant": item.get("strongest_negative_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
                "negative_max_score": item.get("negative_max_score", payload.get("negative_max_score")),
            }
        )
    return {
        "passed": bool(payload.get("passed")),
        "accepted_negative_quality": payload.get("accepted_negative_quality"),
        "rows": rows,
    }


def _palm_anchor_occlusion_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "strongest_negative_score": item.get("strongest_negative_score"),
                "strongest_negative_variant": item.get("strongest_negative_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
                "negative_max_score": item.get("negative_max_score", payload.get("negative_max_score")),
            }
        )
    return {
        "passed": bool(payload.get("passed")),
        "accepted_negative_quality": payload.get("accepted_negative_quality"),
        "rows": rows,
    }


def _finger_mid_joint_occlusion_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _interhand_temporal_desync_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _temporal_order_jitter_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _finger_identity_jitter_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _hand_scale_flicker_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _hand_center_flicker_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _global_framing_flicker_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _hand_shape_scale_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _hand_orientation_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _hand_z_tilt_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _finger_curl_style_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _finger_length_style_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _moving_setup_exit_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "strongest_negative_score": item.get("strongest_negative_score"),
                "strongest_negative_variant": item.get("strongest_negative_variant"),
                "diagnostic_lowest_score": item.get("diagnostic_lowest_score"),
                "diagnostic_lowest_variant": item.get("diagnostic_lowest_variant"),
                "diagnostic_highest_score": item.get("diagnostic_highest_score"),
                "diagnostic_highest_variant": item.get("diagnostic_highest_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {
        "passed": bool(payload.get("passed")),
        "accepted_negative_quality": payload.get("accepted_negative_quality"),
        "rows": rows,
    }


def _core_phase_speed_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _hand_confidence_attenuation_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _energy_sampling_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
                "min_upload_frames": item.get("min_upload_frames"),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _rolling_shutter_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _hand_detail_loss_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _hand_stream_latency_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _ghost_hand_duplicate_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _hand_overlap_merge_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _wrist_anchor_drift_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _finger_chain_latency_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _finger_fan_geometry_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _finger_base_geometry_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _finger_chain_confidence_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _finger_chain_smoothing_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _finite_coordinate_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _bounded_coordinate_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "weakest_diagnostic_score": item.get("weakest_diagnostic_score"),
                "weakest_diagnostic_variant": item.get("weakest_diagnostic_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _missing_mask_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "strongest_negative_score": item.get("strongest_negative_score"),
                "strongest_negative_variant": item.get("strongest_negative_variant"),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _temporal_padding_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "strongest_negative_score": item.get("strongest_negative_score"),
                "strongest_negative_variant": item.get("strongest_negative_variant"),
            }
        )
    return {"passed": bool(payload.get("passed")), "rows": rows}


def _phase_order_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "strongest_negative_score": item.get("strongest_negative_score"),
                "strongest_negative_variant": item.get("strongest_negative_variant"),
            }
        )
    return {
        "passed": bool(payload.get("passed")),
        "accepted_negative_quality": payload.get("accepted_negative_quality"),
        "rows": rows,
    }


def _action_crop_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "strongest_negative_score": item.get("strongest_negative_score"),
                "strongest_negative_variant": item.get("strongest_negative_variant"),
                "diagnostic_lowest_score": item.get("diagnostic_lowest_score"),
                "diagnostic_lowest_variant": item.get("diagnostic_lowest_variant"),
                "diagnostic_highest_score": item.get("diagnostic_highest_score"),
                "diagnostic_highest_variant": item.get("diagnostic_highest_variant"),
            }
        )
    return {
        "passed": bool(payload.get("passed")),
        "accepted_negative_quality": payload.get("accepted_negative_quality"),
        "rows": rows,
    }


def _action_repeat_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in payload.get("results") or []:
        rows.append(
            {
                "word": item.get("word"),
                "passed": bool(item.get("gate_pass")),
                "weakest_positive_score": item.get("weakest_positive_score"),
                "weakest_positive_variant": item.get("weakest_positive_variant"),
                "strongest_negative_score": item.get("strongest_negative_score"),
                "strongest_negative_variant": item.get("strongest_negative_variant"),
                "diagnostic_lowest_score": item.get("diagnostic_lowest_score"),
                "diagnostic_lowest_variant": item.get("diagnostic_lowest_variant"),
                "diagnostic_highest_score": item.get("diagnostic_highest_score"),
                "diagnostic_highest_variant": item.get("diagnostic_highest_variant"),
                "min_required_score": item.get("min_required_score", payload.get("min_score")),
            }
        )
    return {
        "passed": bool(payload.get("passed")),
        "accepted_negative_quality": payload.get("accepted_negative_quality"),
        "rows": rows,
    }


def _build_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# 花/跳评分统一质量门")
    lines.append("")
    lines.append(f"- 生成时间：`{payload['generated_at']}`")
    lines.append(f"- 综合状态：`{'PASS' if payload['passed'] else 'FAIL'}`")
    lines.append(f"- Web 样本根目录：`{payload['web_root']}`")
    lines.append(f"- 标准库：`{payload['template_root']}`")
    lines.append(f"- 语义 profile：`{payload['semantic_profile_json']}`")
    lines.append("- 口径：不重新运行 Holistic，不重启 5080；只读保存的 web/API Holistic JSON 和模板 Holistic JSON。")
    filters = payload.get("web_filters") or {}
    if any(filters.values()):
        lines.append(
            f"- Web 样本过滤：latest=`{filters.get('latest') or 0}`，"
            f"since_request_id=`{filters.get('since_request_id') or ''}`，"
            f"request_ids=`{', '.join(filters.get('request_ids') or []) or '-'}`"
        )
    lines.append("")
    lines.append("## 子门状态")
    lines.append("")
    lines.append("| 子门 | 状态 | 返回码 | 报告 |")
    lines.append("|---|---|---:|---|")
    for item in payload["subgates"]:
        lines.append(
            f"| {item['name']} | {'PASS' if item.get('passed') else 'FAIL'} | "
            f"{item.get('returncode')} | `{item.get('md_path') or '-'}` |"
        )
    lines.append("")

    web = payload.get("web_summary") or {}
    lines.append("## 网页保存样本回归")
    lines.append("")
    rate = _safe_float(web.get("effective_rate"))
    lines.append(
        f"- replay 样本 `{web.get('samples')}`，错误 `{web.get('replay_errors')}`；"
        f"花/跳 diagnostics `{web.get('diagnostics_samples')}`，错误 `{web.get('diagnostics_errors')}`。"
    )
    lines.append(
        f"- 有效采集 `{web.get('effective_reliable')}`，有效正常+边界 "
        f"`{web.get('effective_normal_or_borderline')}`，有效低分 `{web.get('effective_low')}`，"
        f"有效正常+边界率 `{_fmt((rate or 0.0) * 100, 1)}%`。"
    )
    lines.append("")
    lines.append("| 词条 | 有效采集 | 正常+边界 | 有效低分 | 有效率 | 有效均分 |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for word, item in (web.get("by_word_effective") or {}).items():
        word_rate = _safe_float(item.get("normal_or_borderline_rate"))
        lines.append(
            f"| {word} | {item.get('reliable_samples')} | {item.get('normal_or_borderline')} | "
            f"{item.get('low')} | {_fmt((word_rate or 0.0) * 100, 1)}% | {_fmt(item.get('score_mean'))} |"
        )
    lines.append("")

    confusion = payload.get("confusion_summary") or {}
    lines.append("## 网页保存样本花/跳交叉混淆门")
    lines.append("")
    lines.append(
        f"- 样本 `{confusion.get('samples')}`，错误 `{confusion.get('errors')}`；"
        f"eligible `{confusion.get('eligible')}`，pass `{confusion.get('pass')}`，fail `{confusion.get('fail')}`。"
    )
    lines.append("")
    lines.append("| 目标词 | 样本 | eligible | pass | fail | 交叉最高 | margin 最低 | margin 均值 |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for word, item in (confusion.get("by_word") or {}).items():
        lines.append(
            f"| {word} | {item.get('samples')} | {item.get('eligible')} | {item.get('pass')} | {item.get('fail')} | "
            f"{_fmt(item.get('other_score_max'))} | {_fmt(item.get('margin_min'))} | {_fmt(item.get('margin_mean'))} |"
        )
    lines.append("")

    synthetic_confusion = payload.get("synthetic_confusion_summary") or {}
    lines.append("## 合成鲁棒变体花/跳交叉混淆门")
    lines.append("")
    lines.append("- 代表性正向扰动需保持目标词高分，同时按另一个词模板复评仍低分且 margin 足够。")
    lines.append("")
    lines.append("| 目标词 | 状态 | cases | pass | fail | 目标最低 | 交叉最高 | margin 最低 | 最弱变体 |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---|")
    for row in synthetic_confusion.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{row.get('samples')} | {row.get('pass')} | {row.get('fail')} | "
            f"{_fmt(row.get('target_score_min'))} | {_fmt(row.get('cross_score_max'))} | "
            f"{_fmt(row.get('margin_min'))} | {row.get('weakest_variant') or '-'} |"
        )
    lines.append("")

    disc = payload.get("discrimination_summary") or {}
    lines.append("## 负例判别门")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正例最低 | 最弱正例 | 负例最高 | 最强负例 | margin |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in disc.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('min_positive_score'))} | {row.get('weakest_positive') or '-'} | "
            f"{_fmt(row.get('max_negative_score'))} | {row.get('top_negative') or '-'} | "
            f"{_fmt(row.get('margin'))} |"
        )
    lines.append("")

    pose = payload.get("pose_summary") or {}
    lines.append("## 坐姿与镜头扰动门")
    lines.append("")
    lines.append("| 目标词 | 状态 | 最低分 | 最弱扰动 | 门槛 |")
    lines.append("|---|---|---:|---|---:|")
    for row in pose.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('min_observed_score'))} | {row.get('weakest_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    framing = payload.get("framing_summary") or {}
    lines.append("## 取景尺度与轻微旋转鲁棒性门")
    lines.append("")
    lines.append("- 整人 zoom、画面偏移和轻微倾斜需保持高分；极端 zoom/pan 仅记录诊断边界。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向取景扰动 | 诊断最低分 | 最弱诊断扰动 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in framing.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    aspect_ratio = payload.get("aspect_ratio_summary") or {}
    lines.append("## 宽高比失真鲁棒性门")
    lines.append("")
    lines.append("- 轻中度非等比摄像头/画布拉伸需保持高分；极端拉伸仅记录诊断边界。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向宽高比 | 诊断最低分 | 最弱诊断宽高比 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in aspect_ratio.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    camera_roll = payload.get("camera_roll_summary") or {}
    lines.append("## 摄像头整体倾斜鲁棒性门")
    lines.append("")
    lines.append("- 全身骨架 image-plane roll 后重建派生特征；±20 度内需保持高分，35/45 度极端倾斜仅记录诊断边界。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向倾斜 | 诊断最低分 | 最弱诊断倾斜 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in camera_roll.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    body_anchor = payload.get("body_anchor_summary") or {}
    lines.append("## 非核心身体锚点漂移鲁棒性门")
    lines.append("")
    lines.append("- 仅扰动 pose/face 并保留手部核心语义；非核心身体/脸部锚点漂移、抖动或比例异常不应拖低 `花/跳`。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向锚点漂移 | 诊断最低分 | 最弱诊断漂移 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in body_anchor.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    depth = payload.get("depth_summary") or {}
    lines.append("## z/depth 深度鲁棒性门")
    lines.append("")
    lines.append("- 中等 Holistic z 坐标偏移/缩放需保持高分；逐点 z 噪声和极端缩放仅记录诊断边界。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向深度扰动 | 诊断最低分 | 最弱诊断深度扰动 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in depth.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    z_flicker = payload.get("z_flicker_summary") or {}
    lines.append("## z 深度时序抖动鲁棒性门")
    lines.append("")
    lines.append("- 逐帧 Holistic z offset/scale breathing 和少量手部 z 跳动需保持高分；强 z 漂移只记录诊断边界。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向 z 抖动 | 诊断最低分 | 最弱诊断 z 抖动 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in z_flicker.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    edge_clipping = payload.get("edge_clipping_summary") or {}
    lines.append("## 画面边缘裁切鲁棒性门")
    lines.append("")
    lines.append("- 非关键或轻度边缘裁切需保持高分；核心手语信息出画面需低分或重采/语义失败。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向边缘裁切 | 核心裁切最高分 | 最强核心裁切 |")
    lines.append("|---|---|---:|---|---:|---|")
    for row in edge_clipping.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('strongest_negative_score'))} | {row.get('strongest_negative_variant') or '-'} |"
        )
    lines.append("")

    mirror = payload.get("mirror_summary") or {}
    lines.append("## 浏览器镜像鲁棒性门")
    lines.append("")
    lines.append("- `mirror_x` 是正向门；左右标签互换仅记录诊断边界，不作为通过条件。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向变体 | 左右标签诊断最低分 | 最弱诊断变体 |")
    lines.append("|---|---|---:|---|---:|---|")
    for row in mirror.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} |"
        )
    lines.append("")

    hand_role = payload.get("hand_role_summary") or {}
    lines.append("## 手角色鲁棒性门")
    lines.append("")
    lines.append(
        f"- `花` 作为单手主导词需支持左右惯用手；`跳` 作为双手角色词的地面手/跳跃手互换需低分或语义失败。"
        f"负向质量口径：`{hand_role.get('accepted_negative_quality') or '-'}`。"
    )
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向角色变体 | 角色互换最高分 | 最强角色互换负例 |")
    lines.append("|---|---|---:|---|---:|---|")
    for row in hand_role.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('strongest_negative_score'))} | {row.get('strongest_negative_variant') or '-'} |"
        )
    lines.append("")

    noncore_hand_distractor = payload.get("noncore_hand_distractor_summary") or {}
    lines.append("## 非核心手与非语义手指干扰鲁棒性门")
    lines.append("")
    lines.append("- `花` 的非核心左手干扰、`跳` 的右手非语义手指干扰需保持高分；核心破坏仅记录诊断边界。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向干扰 | 诊断最低分 | 最弱诊断核心扰动 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in noncore_hand_distractor.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    relation_geometry = payload.get("relation_geometry_summary") or {}
    lines.append("## 双手关系几何鲁棒性门")
    lines.append("")
    lines.append(
        "- 温和右手相对位置、跳跃高度、横向轨迹和关系抖动需保持高分；"
        f"`跳` 的过小高度/强水平化/反向关系需低分或语义失败。负向质量口径：`{relation_geometry.get('accepted_negative_quality') or '-'}`。"
    )
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向关系扰动 | 负向最高分 | 最强负向关系 | 诊断最低分 | 最弱诊断关系 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|---|---:|")
    for row in relation_geometry.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('strongest_negative_score'))} | {row.get('strongest_negative_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    core_shape_amplitude = payload.get("core_shape_amplitude_summary") or {}
    lines.append("## 核心手形幅度鲁棒性门")
    lines.append("")
    lines.append(
        "- `花` 的温和开花开合幅度变化需保持高分，严重不开花需低分或语义失败；"
        f"`跳` 的两指小人温和局部形变需保持高分。负向质量口径：`{core_shape_amplitude.get('accepted_negative_quality') or '-'}`。"
    )
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向核心形变 | 负向最高分 | 最强负向核心形变 | 诊断最低分 | 最弱诊断形变 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|---|---:|")
    for row in core_shape_amplitude.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('strongest_negative_score'))} | {row.get('strongest_negative_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    perspective_shear = payload.get("perspective_shear_summary") or {}
    lines.append("## 斜拍透视剪切鲁棒性门")
    lines.append("")
    lines.append("- 轻中度 image-plane shear、z-to-x/y 透视偏移和局部手部剪切需保持高分；强剪切/强透视只记录诊断边界。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向透视/剪切 | 诊断最低分 | 最弱诊断透视/剪切 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in perspective_shear.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    hand_label_flicker = payload.get("hand_label_flicker_summary") or {}
    lines.append("## 左右手标签抖动鲁棒性门")
    lines.append("")
    lines.append(
        "- 单帧或稀疏 handedness flicker 需保持可评分；持续或交替 flicker 需低分并进入重采/语义失败。"
        f"负向质量口径：`{hand_label_flicker.get('accepted_negative_quality') or '-'}`。"
    )
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向 flicker | 负向最高分 | 最强负向 flicker |")
    lines.append("|---|---|---:|---|---:|---|")
    for row in hand_label_flicker.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('strongest_negative_score'))} | {row.get('strongest_negative_variant') or '-'} |"
        )
    lines.append("")

    hand_dropout_burst = payload.get("hand_dropout_burst_summary") or {}
    lines.append("## 连续手部检出空洞鲁棒性门")
    lines.append("")
    lines.append(
        "- 短 burst hand detector 空洞需保持可评分；持续核心手空洞需低分并进入重采/语义失败。"
        f"负向质量口径：`{hand_dropout_burst.get('accepted_negative_quality') or '-'}`。"
    )
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向空洞 | 持续空洞最高分 | 最强持续空洞 |")
    lines.append("|---|---|---:|---|---:|---|")
    for row in hand_dropout_burst.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('strongest_negative_score'))} | {row.get('strongest_negative_variant') or '-'} |"
        )
    lines.append("")

    frame = payload.get("frame_summary") or {}
    lines.append("## 帧数与采样密度扰动门")
    lines.append("")
    lines.append("| 目标词 | 状态 | 推荐最少帧 | 最低分 | 最弱采样 | 门槛 | 欠采样最低分 |")
    lines.append("|---|---|---:|---:|---|---:|---:|")
    for row in frame.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{row.get('min_valid_frames')} | {_fmt(row.get('min_observed_score'))} | "
            f"{row.get('weakest_variant') or '-'} | {_fmt(row.get('min_required_score'))} | "
            f"{_fmt(row.get('diagnostic_min_score'))} |"
        )
    lines.append("")

    temporal_stutter = payload.get("temporal_stutter_summary") or {}
    lines.append("## 时序帧冻结 stutter 鲁棒性门")
    lines.append("")
    lines.append(
        "- 固定上传帧数内的短 burst 或稀疏重复帧需保持可评分；持续核心动作冻结需低分并进入重采/语义失败。"
        f"负向质量口径：`{temporal_stutter.get('accepted_negative_quality') or '-'}`。"
    )
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向 stutter | 持续冻结最高分 | 最强持续冻结 | 诊断最低分 | 最弱诊断边界 |")
    lines.append("|---|---|---:|---|---:|---|---:|---|")
    for row in temporal_stutter.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('strongest_negative_score'))} | {row.get('strongest_negative_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} |"
        )
    lines.append("")

    hand_trajectory_interpolation = payload.get("hand_trajectory_interpolation_summary") or {}
    lines.append("## 手部轨迹插值补洞鲁棒性门")
    lines.append("")
    lines.append("- 短 tracker 插值补洞和稀疏插值帧需保持高分；更长连续补洞仅记录诊断边界。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向插值 | 诊断最低分 | 最弱诊断插值 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in hand_trajectory_interpolation.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    temporal_rate = payload.get("temporal_rate_summary") or {}
    lines.append("## 时序速率鲁棒性门")
    lines.append("")
    lines.append("- 同样帧数内局部速度变化、整体快慢变化和轻微采样间隔不均需保持高分；极端速率/内部缺口仅记录诊断边界。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向速率扰动 | 诊断最低分 | 最弱诊断边界 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in temporal_rate.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    temporal_metadata = payload.get("temporal_metadata_summary") or {}
    lines.append("## 时间元数据清洗鲁棒性门")
    lines.append("")
    lines.append("- 畸形 fps、total_frames、frame_idx 和 timestamp_sec 必须被安全清洗，且不能改变动作顺序或产生非有限诊断。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱时间元数据变体 | 门槛 |")
    lines.append("|---|---|---:|---|---:|")
    for row in temporal_metadata.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    composite_browser = payload.get("composite_browser_summary") or {}
    lines.append("## 组合网页扰动鲁棒性门")
    lines.append("")
    lines.append("- 轻微宽高比、坐标量化、速率变化、短 stutter 和短手部检出缺口组合出现时需保持高分；强组合扰动仅记录诊断边界。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向组合 | 诊断最低分 | 最弱诊断组合 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in composite_browser.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    frame_weight = payload.get("frame_weight_summary") or {}
    lines.append("## frame_weights 上传权重鲁棒性门")
    lines.append("")
    lines.append("- 浏览器上传 motion 权重、轻微错位/噪声、宽泛前后段加权、无非均匀权重和异常上传权重清洗后需保持高分；反向 motion 权重仅记录诊断。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向权重 | 诊断最低分 | 最弱诊断权重 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in frame_weight.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    coordinate_precision = payload.get("coordinate_precision_summary") or {}
    lines.append("## 坐标精度量化鲁棒性门")
    lines.append("")
    lines.append("- 常见摄像头像素网格、归一化坐标精度和低分辨率取整需保持高分；极粗网格只记录诊断边界。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向精度扰动 | 诊断最低分 | 最弱诊断精度扰动 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in coordinate_precision.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    motion_blur = payload.get("motion_blur_summary") or {}
    lines.append("## 运动幅度与模糊诊断鲁棒性门")
    lines.append("")
    lines.append("- 10%-15% 全身/手部运动幅度变化需保持高分；低通平滑可能抹掉 `花` 的 opening 动态，只记录诊断边界。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向幅度变体 | 诊断最低分 | 最弱诊断平滑/模糊 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in motion_blur.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    landmark_noise = payload.get("landmark_noise_summary") or {}
    lines.append("## Landmark 噪声鲁棒性门")
    lines.append("")
    lines.append("- 小幅连续手部关键点抖动和稀少整帧手部不稳定需保持高分；严重噪声/逐点丢失仅记录诊断边界。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向噪声 | 诊断最低分 | 最弱诊断噪声 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in landmark_noise.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    landmark_spike = payload.get("landmark_spike_summary") or {}
    lines.append("## Landmark 跳点鲁棒性门")
    lines.append("")
    lines.append("- 单帧或稀疏 hand landmark 大跳点需保持可评分；连续核心跳点和 landmark 顺序扰动仅记录诊断边界。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向跳点 | 诊断最低分 | 最弱诊断跳点 |")
    lines.append("|---|---|---:|---|---:|---|")
    for row in landmark_spike.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} |"
        )
    lines.append("")

    fingertip_occlusion = payload.get("fingertip_occlusion_summary") or {}
    lines.append("## 指尖遮挡鲁棒性门")
    lines.append("")
    lines.append(
        f"- 负向样本质量口径：`{fingertip_occlusion.get('accepted_negative_quality') or '-'}`；"
        "短时/稀疏 fingertip mask 丢失需保持高分，关键指尖全程缺失需低分或重采/语义失败。"
    )
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向遮挡 | 核心缺失最高分 | 最强核心缺失负例 | 诊断最低分 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|---:|")
    for row in fingertip_occlusion.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('strongest_negative_score'))} | {row.get('strongest_negative_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    palm_anchor_occlusion = payload.get("palm_anchor_occlusion_summary") or {}
    lines.append("## 掌根锚点遮挡鲁棒性门")
    lines.append("")
    lines.append(
        f"- 负向样本质量口径：`{palm_anchor_occlusion.get('accepted_negative_quality') or '-'}`；"
        "短时/稀疏 wrist/MCP palm-anchor mask 丢失需保持高分，核心掌根锚点全程缺失需低分或重采/语义失败。"
    )
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向锚点缺失 | 核心锚点全缺最高分 | 最强负例 | 诊断最低分 | 最弱诊断锚点缺失 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|---|---:|")
    for row in palm_anchor_occlusion.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('strongest_negative_score'))} | {row.get('strongest_negative_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    finger_mid_joint_occlusion = payload.get("finger_mid_joint_occlusion_summary") or {}
    lines.append("## 手指中段关节遮挡鲁棒性门")
    lines.append("")
    lines.append("- 单帧、稀疏或局部中段 PIP/DIP/thumb-IP mask 丢失需保持高分；持续强缺失只记录诊断边界。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向中段指节遮挡 | 诊断最低分 | 最弱诊断遮挡 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in finger_mid_joint_occlusion.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    interhand_temporal_desync = payload.get("interhand_temporal_desync_summary") or {}
    lines.append("## 手间时序错位鲁棒性门")
    lines.append("")
    lines.append("- 单只手相对其它骨架组轻微提前/滞后需保持高分，强错位只记录诊断边界。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向错位 | 诊断最低分 | 最弱诊断错位 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in interhand_temporal_desync.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    temporal_order_jitter = payload.get("temporal_order_jitter_summary") or {}
    lines.append("## 时序顺序抖动鲁棒性门")
    lines.append("")
    lines.append("- 相邻帧交换和局部三帧错序需保持高分；块状倒序只记录诊断边界，硬拒绝由 phase-order 门覆盖。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向抖动 | 诊断最低分 | 最弱诊断抖动 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in temporal_order_jitter.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    finger_identity_jitter = payload.get("finger_identity_jitter_summary") or {}
    lines.append("## 手指身份抖动鲁棒性门")
    lines.append("")
    lines.append("- 相邻 finger-chain 标签混淆和少量帧级手指身份抖动需保持高分；非相邻或多链强交换只记录诊断边界。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向指链抖动 | 诊断最低分 | 最弱诊断抖动 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in finger_identity_jitter.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    hand_scale_flicker = payload.get("hand_scale_flicker_summary") or {}
    lines.append("## 手部尺度时序呼吸鲁棒性门")
    lines.append("")
    lines.append("- 逐帧 hand-box scale/aspect breathing 和少量 detector scale flicker 需保持高分；强尺度尖峰只记录诊断边界。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向尺度呼吸 | 诊断最低分 | 最弱诊断尺度呼吸 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in hand_scale_flicker.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    hand_center_flicker = payload.get("hand_center_flicker_summary") or {}
    lines.append("## 手部中心时序漂移鲁棒性门")
    lines.append("")
    lines.append("- 逐帧 hand-box center wobble 和少量 detector center flicker 需保持高分；强中心跳点只记录诊断边界。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向中心漂移 | 诊断最低分 | 最弱诊断中心漂移 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in hand_center_flicker.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    global_framing_flicker = payload.get("global_framing_flicker_summary") or {}
    lines.append("## 全局取景时序漂移鲁棒性门")
    lines.append("")
    lines.append("- 整人画面级 pan/zoom 随时间漂移和少量自动取景跳点需保持高分；强 pan/zoom 跳点只记录诊断边界。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向全局取景漂移 | 诊断最低分 | 最弱诊断全局取景漂移 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in global_framing_flicker.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    hand_shape_scale = payload.get("hand_shape_scale_summary") or {}
    lines.append("## 手形局部尺度鲁棒性门")
    lines.append("")
    lines.append("- 手部局部大小和轻微透视变化会重算 `*_hand_shape`；正向变体需保持高分，极端形变只记录诊断边界。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向手形尺度 | 诊断最低分 | 最弱诊断尺度 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in hand_shape_scale.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    hand_orientation = payload.get("hand_orientation_summary") or {}
    lines.append("## 手部局部旋转鲁棒性门")
    lines.append("")
    lines.append("- 手腕/手部局部角度变化会重算 `*_hand_shape`；正向变体需保持高分，极端旋转只记录诊断边界。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向旋转 | 诊断最低分 | 最弱诊断旋转 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in hand_orientation.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    hand_z_tilt = payload.get("hand_z_tilt_summary") or {}
    lines.append("## 手部 z 倾角鲁棒性门")
    lines.append("")
    lines.append("- 手掌轻微出平面俯仰/侧倾会重算 hand-shape、motion 和 two-hand relation；强倾角只记录诊断边界。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向 z 倾角 | 诊断最低分 | 最弱诊断 z 倾角 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in hand_z_tilt.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    finger_curl_style = payload.get("finger_curl_style_summary") or {}
    lines.append("## 手指弯曲风格鲁棒性门")
    lines.append("")
    lines.append("- 轻微手指弯曲风格会重算 hand-shape、motion 和 two-hand relation；强弯曲只记录诊断边界。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向弯曲 | 诊断最低分 | 最弱诊断弯曲 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in finger_curl_style.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    finger_length_style = payload.get("finger_length_style_summary") or {}
    lines.append("## 手指长度比例鲁棒性门")
    lines.append("")
    lines.append("- 轻微手指长度/比例风格会重算 hand-shape、motion 和 two-hand relation；强比例变化只记录诊断边界。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向比例 | 诊断最低分 | 最弱诊断比例 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in finger_length_style.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    moving_setup_exit = payload.get("moving_setup_exit_summary") or {}
    lines.append("## 动态入场退场鲁棒性门")
    lines.append("")
    lines.append("- 动作前后移动手到位/放下手时，完整核心动作仍需高分；只有入场片段需低分或重采/语义失败。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向动态污染 | 入场-only 最高分 | 最强入场-only | 诊断最低分 | 最弱诊断 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|---|---:|")
    for row in moving_setup_exit.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('strongest_negative_score'))} | {row.get('strongest_negative_variant') or '-'} | "
            f"{_fmt(row.get('diagnostic_lowest_score'))} | {row.get('diagnostic_lowest_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    core_phase_speed = payload.get("core_phase_speed_summary") or {}
    lines.append("## 核心相位速度鲁棒性门")
    lines.append("")
    lines.append("- 只改变 `花` 绽放核心和 `跳` 起跳/双手关系核心的局部速度；核心被跳过只记录诊断边界。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向核心速度 | 诊断最低分 | 最弱诊断边界 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in core_phase_speed.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    hand_confidence_attenuation = payload.get("hand_confidence_attenuation_summary") or {}
    lines.append("## 手部置信度衰减鲁棒性门")
    lines.append("")
    lines.append("- 保留手部坐标，仅降低 hand/hand-shape mask 置信权重；极端低置信按有效缺失诊断。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向低置信 | 诊断最低分 | 最弱诊断边界 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in hand_confidence_attenuation.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    energy_sampling = payload.get("energy_sampling_summary") or {}
    lines.append("## 运动能量选帧鲁棒性门")
    lines.append("")
    lines.append("- 按前端自适应 motion-energy coverage 算法选择实际上传帧集合，并重建 motion/two-hand relation；坏选帧只记录诊断。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向选帧 | 诊断最低分 | 最弱诊断边界 | 推荐帧 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|---:|")
    for row in energy_sampling.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{row.get('min_upload_frames') or '-'} | {_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    rolling_shutter = payload.get("rolling_shutter_summary") or {}
    lines.append("## 滚动快门时变斜切鲁棒性门")
    lines.append("")
    lines.append("- 合成逐帧 rolling-shutter-like line shear 并重建 motion/two-hand relation；强 skew 只记录诊断。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向 rolling-shutter | 诊断最低分 | 最弱诊断边界 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in rolling_shutter.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    hand_detail_loss = payload.get("hand_detail_loss_summary") or {}
    lines.append("## 手部细节损失鲁棒性门")
    lines.append("")
    lines.append("- 合成低分辨率/低细节下的手部内关节线性化并重建 hand-shape/motion/two-hand relation；强指尖塌缩只记录诊断。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向细节损失 | 诊断最低分 | 最弱诊断边界 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in hand_detail_loss.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    hand_stream_latency = payload.get("hand_stream_latency_summary") or {}
    lines.append("## 手部流帧级延迟鲁棒性门")
    lines.append("")
    lines.append("- 合成双手 landmark 流相对当前帧轻微滞后/提前并重建 hand-shape/motion/two-hand relation；明显对齐错误只记录诊断。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向手部流延迟 | 诊断最低分 | 最弱诊断边界 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in hand_stream_latency.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    ghost_hand_duplicate = payload.get("ghost_hand_duplicate_summary") or {}
    lines.append("## 幽灵手重复鲁棒性门")
    lines.append("")
    lines.append("- 合成单手被复制成双手的 ghost-hand 误检并重建 hand-shape/motion/two-hand relation；持续核心重复只记录诊断边界。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向幽灵手 | 诊断最低分 | 最弱诊断边界 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in ghost_hand_duplicate.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    hand_overlap_merge = payload.get("hand_overlap_merge_summary") or {}
    lines.append("## 手部重叠融合鲁棒性门")
    lines.append("")
    lines.append("- 合成双手重叠/遮挡时一只手 landmarks 局部向另一只手或掌心融合，并重建 hand-shape/motion/two-hand relation；持续核心融合只记录诊断边界。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向融合 | 诊断最低分 | 最弱诊断边界 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in hand_overlap_merge.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    wrist_anchor_drift = payload.get("wrist_anchor_drift_summary") or {}
    lines.append("## 手腕掌根锚点漂移鲁棒性门")
    lines.append("")
    lines.append("- 合成 hand mask 仍有效时 wrist/MCP/palm anchors 坐标短时漂移，并重建 hand-shape/motion/two-hand relation；持续核心漂移只记录诊断边界。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向漂移 | 诊断最低分 | 最弱诊断边界 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in wrist_anchor_drift.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    finger_chain_latency = payload.get("finger_chain_latency_summary") or {}
    lines.append("## 手指链帧级延迟鲁棒性门")
    lines.append("")
    lines.append("- 合成同一手内 distal finger chains 相对 wrist/MCP/palm anchors 的单帧、稀疏或短窗口帧级延迟，并重建 hand-shape/motion/two-hand relation；持续全程错相只记录诊断边界。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向延迟 | 诊断最低分 | 最弱诊断边界 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in finger_chain_latency.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    finger_fan_geometry = payload.get("finger_fan_geometry_summary") or {}
    lines.append("## 手指扇形几何鲁棒性门")
    lines.append("")
    lines.append("- 合成相邻 distal finger chains 的指缝压缩、拉开和几何交叉，landmark 身份、mask 与 wrist/MCP/palm anchors 保持不变，并重建 hand-shape/motion/two-hand relation；持续强交叉只记录诊断边界。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向扇形漂移 | 诊断最低分 | 最弱诊断边界 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in finger_fan_geometry.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    finger_base_geometry = payload.get("finger_base_geometry_summary") or {}
    lines.append("## 手指基座几何鲁棒性门")
    lines.append("")
    lines.append("- 合成相邻 MCP/CMC finger-base landmarks 的指根压缩、拉开和几何交叉，distal finger chains、landmark 身份与 mask 保持不变，并重建 hand-shape/motion/two-hand relation；持续强基座交叉只记录诊断边界。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向基座漂移 | 诊断最低分 | 最弱诊断边界 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in finger_base_geometry.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    finger_chain_confidence = payload.get("finger_chain_confidence_summary") or {}
    lines.append("## 手指链软置信鲁棒性门")
    lines.append("")
    lines.append("- 合成特定 finger-chain 坐标完整但 hand mask 权重下降的 near-threshold 低置信场景，并重建 motion/two-hand relation；硬缺失由遮挡/缺失门覆盖。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向低置信 | 诊断最低分 | 最弱诊断边界 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in finger_chain_confidence.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    finger_chain_smoothing = payload.get("finger_chain_smoothing_summary") or {}
    lines.append("## 手指链时间平滑鲁棒性门")
    lines.append("")
    lines.append("- 只对选定 distal finger-chain 做短窗口低通，palm/wrist 锚点和 mask 保持当前帧；轻度或短窗口 tracker smoothing 不应拖低正确动作。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向时间平滑 | 诊断最低分 | 最弱诊断边界 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in finger_chain_smoothing.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    finite_coordinate = payload.get("finite_coordinate_summary") or {}
    lines.append("## 非有限坐标清洗鲁棒性门")
    lines.append("")
    lines.append("- 通过带 `NaN/Inf` 的临时 Holistic JSON fixture 走正常加载和评分路径；孤立坏点应被视作缺失点，DTW/分数诊断必须保持有限。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向坏点 | 诊断最低分 | 最弱诊断边界 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in finite_coordinate.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    bounded_coordinate = payload.get("bounded_coordinate_summary") or {}
    lines.append("## 有限异常 / 退化坐标清洗鲁棒性门")
    lines.append("")
    lines.append("- 通过带 hand/face out-of-frame x/y、z-depth 有限离群、exact-zero 占位和整手极小跨度塌缩的临时 Holistic JSON fixture 走正常加载和评分路径；稀疏坏点应被视作缺失点，持续核心手退化必须低分或触发重采/语义失败诊断。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向越界点 | 诊断最低分 | 最弱诊断边界 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for row in bounded_coordinate.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('weakest_diagnostic_score'))} | {row.get('weakest_diagnostic_variant') or '-'} | "
            f"{_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    temporal_padding = payload.get("temporal_padding_summary") or {}
    lines.append("## 静止 padding 与时序鲁棒性门")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向变体 | 静态最高分 | 最强静态变体 |")
    lines.append("|---|---|---:|---|---:|---|")
    for row in temporal_padding.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('strongest_negative_score'))} | {row.get('strongest_negative_variant') or '-'} |"
        )
    lines.append("")

    phase_order = payload.get("phase_order_summary") or {}
    lines.append("## 语义相位顺序鲁棒性门")
    lines.append("")
    lines.append(
        f"- 负向样本质量口径：`{phase_order.get('accepted_negative_quality') or '-'}`；"
        "单调变速/采样抖动需保持高分，倒放/半段交换/三相位乱序需低分。"
    )
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向变体 | 乱序最高分 | 最强乱序变体 |")
    lines.append("|---|---|---:|---|---:|---|")
    for row in phase_order.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('strongest_negative_score'))} | {row.get('strongest_negative_variant') or '-'} |"
        )
    lines.append("")

    action_crop = payload.get("action_crop_summary") or {}
    lines.append("## 录制起止裁剪鲁棒性门")
    lines.append("")
    lines.append("- 轻度起录/停录裁剪需保持高分；词条专属缺核心半段需低分或语义失败；不稳定半段仅诊断。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向裁剪 | 缺核心最高分 | 最强缺核心裁剪 | 诊断分数范围 |")
    lines.append("|---|---|---:|---|---:|---|---|")
    for row in action_crop.get("rows") or []:
        diagnostic_range = "-"
        if row.get("diagnostic_lowest_score") is not None:
            diagnostic_range = f"{_fmt(row.get('diagnostic_lowest_score'))} - {_fmt(row.get('diagnostic_highest_score'))}"
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('strongest_negative_score'))} | {row.get('strongest_negative_variant') or '-'} | "
            f"{diagnostic_range} |"
        )
    lines.append("")

    action_repeat = payload.get("action_repeat_summary") or {}
    lines.append("## 重复动作录制鲁棒性门")
    lines.append("")
    lines.append("- 一次网页录制里多做一遍、先试半遍再完整做、或完整后又开始下一遍时需保持高分；setup-only 极短片段需低分或重采/语义失败。")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向重复 | 不完整最高分 | 最强不完整负例 | 诊断分数范围 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---|---:|")
    for row in action_repeat.get("rows") or []:
        diagnostic_range = "-"
        if row.get("diagnostic_lowest_score") is not None:
            diagnostic_range = f"{_fmt(row.get('diagnostic_lowest_score'))} - {_fmt(row.get('diagnostic_highest_score'))}"
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('strongest_negative_score'))} | {row.get('strongest_negative_variant') or '-'} | "
            f"{diagnostic_range} | {_fmt(row.get('min_required_score'))} |"
        )
    lines.append("")

    missing_mask = payload.get("missing_mask_summary") or {}
    lines.append("## 缺失与关键 mask 鲁棒性门")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向变体 | 关键缺失最高分 | 最强关键缺失变体 |")
    lines.append("|---|---|---:|---|---:|---|")
    for row in missing_mask.get("rows") or []:
        lines.append(
            f"| {row.get('word')} | {'PASS' if row.get('passed') else 'FAIL'} | "
            f"{_fmt(row.get('weakest_positive_score'))} | {row.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(row.get('strongest_negative_score'))} | {row.get('strongest_negative_variant') or '-'} |"
        )
    lines.append("")

    marker = payload.get("marker_status") or {}
    marker_payload = marker.get("payload") or {}
    if marker_payload:
        new_summary = marker_payload.get("new_summary") or {}
        target_summary = marker_payload.get("target_summary") or {}
        lines.append("## Marker 状态")
        lines.append("")
        lines.append(f"- marker last_request_id：`{marker_payload.get('marker_last_request_id')}`")
        lines.append(f"- marker 后新增样本：`{new_summary.get('count')}`")
        lines.append(f"- marker 后新增花/跳样本：`{target_summary.get('count')}`")
        lines.append("")

    lines.append("## 使用说明")
    lines.append("")
    lines.append("- 修改 `score_holistic_sequence_mvp.py`、语义 profile、模板权重、score scaling 或对齐策略后，优先运行本脚本。")
    lines.append("- 若本脚本 PASS，只能说明当前保存样本与合成鲁棒性门没有回退；真实用户网页测试仍需要新的摄像头样本和人工复核。")
    return "\n".join(lines) + "\n"


def _default_output_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return DEFAULT_OUTPUT_BASE / f"flower_jump_quality_gate_{stamp}"


def run_quality_gate(args: argparse.Namespace) -> Dict[str, Any]:
    output_dir = Path(args.output_dir) if args.output_dir else _default_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    template_root = Path(args.template_root)
    semantic_profile_json = Path(args.semantic_profile_json)
    web_root = Path(args.web_root)

    web_dir = output_dir / "web_regression"
    confusion_dir = output_dir / "web_confusion_gate"
    synthetic_confusion_dir = output_dir / "synthetic_confusion_robustness_gate"
    disc_dir = output_dir / "discrimination_gate"
    pose_dir = output_dir / "pose_robustness_gate"
    framing_dir = output_dir / "framing_robustness_gate"
    aspect_ratio_dir = output_dir / "aspect_ratio_robustness_gate"
    camera_roll_dir = output_dir / "camera_roll_robustness_gate"
    body_anchor_dir = output_dir / "body_anchor_robustness_gate"
    depth_dir = output_dir / "depth_robustness_gate"
    z_flicker_dir = output_dir / "z_flicker_robustness_gate"
    edge_clipping_dir = output_dir / "edge_clipping_robustness_gate"
    mirror_dir = output_dir / "mirror_robustness_gate"
    hand_role_dir = output_dir / "hand_role_robustness_gate"
    hand_label_flicker_dir = output_dir / "hand_label_flicker_robustness_gate"
    hand_dropout_burst_dir = output_dir / "hand_dropout_burst_robustness_gate"
    frame_dir = output_dir / "frame_count_robustness_gate"
    temporal_stutter_dir = output_dir / "temporal_stutter_robustness_gate"
    temporal_rate_dir = output_dir / "temporal_rate_robustness_gate"
    temporal_metadata_dir = output_dir / "temporal_metadata_robustness_gate"
    hand_trajectory_interpolation_dir = output_dir / "hand_trajectory_interpolation_robustness_gate"
    composite_browser_dir = output_dir / "composite_browser_robustness_gate"
    frame_weight_dir = output_dir / "frame_weight_robustness_gate"
    coordinate_precision_dir = output_dir / "coordinate_precision_robustness_gate"
    motion_blur_dir = output_dir / "motion_blur_robustness_gate"
    landmark_noise_dir = output_dir / "landmark_noise_robustness_gate"
    landmark_spike_dir = output_dir / "landmark_spike_robustness_gate"
    fingertip_occlusion_dir = output_dir / "fingertip_occlusion_robustness_gate"
    palm_anchor_occlusion_dir = output_dir / "palm_anchor_occlusion_robustness_gate"
    hand_shape_scale_dir = output_dir / "hand_shape_scale_robustness_gate"
    hand_orientation_dir = output_dir / "hand_orientation_robustness_gate"
    hand_z_tilt_dir = output_dir / "hand_z_tilt_robustness_gate"
    finger_curl_style_dir = output_dir / "finger_curl_style_robustness_gate"
    finger_length_style_dir = output_dir / "finger_length_style_robustness_gate"
    moving_setup_exit_dir = output_dir / "moving_setup_exit_robustness_gate"
    core_phase_speed_dir = output_dir / "core_phase_speed_robustness_gate"
    hand_confidence_attenuation_dir = output_dir / "hand_confidence_attenuation_robustness_gate"
    energy_sampling_dir = output_dir / "energy_sampling_robustness_gate"
    rolling_shutter_dir = output_dir / "rolling_shutter_robustness_gate"
    hand_detail_loss_dir = output_dir / "hand_detail_loss_robustness_gate"
    hand_stream_latency_dir = output_dir / "hand_stream_latency_robustness_gate"
    ghost_hand_duplicate_dir = output_dir / "ghost_hand_duplicate_robustness_gate"
    hand_overlap_merge_dir = output_dir / "hand_overlap_merge_robustness_gate"
    wrist_anchor_drift_dir = output_dir / "wrist_anchor_drift_robustness_gate"
    finger_chain_latency_dir = output_dir / "finger_chain_latency_robustness_gate"
    finger_fan_geometry_dir = output_dir / "finger_fan_geometry_robustness_gate"
    finger_base_geometry_dir = output_dir / "finger_base_geometry_robustness_gate"
    finger_chain_confidence_dir = output_dir / "finger_chain_confidence_robustness_gate"
    finger_chain_smoothing_dir = output_dir / "finger_chain_smoothing_robustness_gate"
    finite_coordinate_dir = output_dir / "finite_coordinate_robustness_gate"
    bounded_coordinate_dir = output_dir / "bounded_coordinate_robustness_gate"
    missing_mask_dir = output_dir / "missing_mask_robustness_gate"
    temporal_padding_dir = output_dir / "temporal_padding_robustness_gate"
    phase_order_dir = output_dir / "phase_order_robustness_gate"
    action_crop_dir = output_dir / "action_crop_robustness_gate"
    action_repeat_dir = output_dir / "action_repeat_robustness_gate"
    noncore_hand_distractor_dir = output_dir / "noncore_hand_distractor_robustness_gate"
    relation_geometry_dir = output_dir / "relation_geometry_robustness_gate"
    core_shape_amplitude_dir = output_dir / "core_shape_amplitude_robustness_gate"
    perspective_shear_dir = output_dir / "perspective_shear_robustness_gate"
    interhand_temporal_desync_dir = output_dir / "interhand_temporal_desync_robustness_gate"
    temporal_order_jitter_dir = output_dir / "temporal_order_jitter_robustness_gate"
    finger_identity_jitter_dir = output_dir / "finger_identity_jitter_robustness_gate"
    hand_scale_flicker_dir = output_dir / "hand_scale_flicker_robustness_gate"
    hand_center_flicker_dir = output_dir / "hand_center_flicker_robustness_gate"
    global_framing_flicker_dir = output_dir / "global_framing_flicker_robustness_gate"
    finger_mid_joint_occlusion_dir = output_dir / "finger_mid_joint_occlusion_robustness_gate"

    web_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_web_regression.py"),
        "--web-root",
        str(web_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--template-root",
        str(template_root),
        "--output-dir",
        str(web_dir),
        "--backend-url",
        args.backend_url,
    ]
    if args.latest:
        web_cmd.extend(["--latest", str(args.latest)])
    if args.since_request_id:
        web_cmd.extend(["--since-request-id", args.since_request_id])
    if args.request_ids:
        web_cmd.append("--request-ids")
        web_cmd.extend(args.request_ids)

    confusion_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_web_confusion_gate.py"),
        "--web-root",
        str(web_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--template-root",
        str(template_root),
        "--output-dir",
        str(confusion_dir),
        "--backend-url",
        args.backend_url,
        "--min-target-score",
        str(args.confusion_min_target_score),
        "--max-cross-score",
        str(args.confusion_max_cross_score),
        "--min-margin",
        str(args.confusion_min_margin),
        "--min-eligible-per-word",
        str(args.confusion_min_eligible_per_word),
    ]
    if args.latest:
        confusion_cmd.extend(["--latest", str(args.latest)])
    if args.since_request_id:
        confusion_cmd.extend(["--since-request-id", args.since_request_id])
    if args.request_ids:
        confusion_cmd.append("--request-ids")
        confusion_cmd.extend(args.request_ids)

    synthetic_confusion_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_synthetic_confusion_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(synthetic_confusion_dir),
        "--backend-url",
        args.backend_url,
        "--min-target-score",
        str(args.synthetic_confusion_min_target_score),
        "--max-cross-score",
        str(args.synthetic_confusion_max_cross_score),
        "--min-margin",
        str(args.synthetic_confusion_min_margin),
    ]

    disc_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_discrimination_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(disc_dir),
        "--backend-url",
        args.backend_url,
        "--positive-threshold",
        str(args.positive_threshold),
        "--negative-threshold",
        str(args.negative_threshold),
    ]
    pose_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_pose_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(pose_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.pose_min_score),
    ]
    framing_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_framing_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(framing_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.framing_min_score),
    ]
    aspect_ratio_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_aspect_ratio_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(aspect_ratio_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.aspect_ratio_min_score),
    ]
    camera_roll_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_camera_roll_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(camera_roll_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.camera_roll_min_score),
    ]
    body_anchor_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_body_anchor_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(body_anchor_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.body_anchor_min_score),
    ]
    depth_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_depth_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(depth_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.depth_min_score),
    ]
    z_flicker_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_z_flicker_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(z_flicker_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.z_flicker_min_score),
    ]
    hand_trajectory_interpolation_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_hand_trajectory_interpolation_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(hand_trajectory_interpolation_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.hand_trajectory_interpolation_min_score),
    ]
    edge_clipping_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_edge_clipping_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(edge_clipping_dir),
        "--backend-url",
        args.backend_url,
    ]
    mirror_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_mirror_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(mirror_dir),
        "--backend-url",
        args.backend_url,
    ]
    hand_role_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_hand_role_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(hand_role_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.hand_role_min_score),
        "--max-role-swap-score",
        str(args.hand_role_max_role_swap_score),
    ]
    hand_label_flicker_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_hand_label_flicker_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(hand_label_flicker_dir),
        "--backend-url",
        args.backend_url,
    ]
    hand_dropout_burst_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_hand_dropout_burst_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(hand_dropout_burst_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.hand_dropout_burst_min_score),
    ]
    frame_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_frame_count_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(frame_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.frame_min_score),
        "--flower-min-valid-frames",
        str(args.flower_min_valid_frames),
        "--jump-min-valid-frames",
        str(args.jump_min_valid_frames),
    ]
    temporal_stutter_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_temporal_stutter_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(temporal_stutter_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.temporal_stutter_min_score),
    ]
    temporal_rate_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_temporal_rate_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(temporal_rate_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.temporal_rate_min_score),
    ]
    temporal_metadata_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_temporal_metadata_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(temporal_metadata_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.temporal_metadata_min_score),
    ]
    composite_browser_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_composite_browser_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(composite_browser_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.composite_browser_min_score),
    ]
    frame_weight_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_frame_weight_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(frame_weight_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.frame_weight_min_score),
    ]
    coordinate_precision_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_coordinate_precision_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(coordinate_precision_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.coordinate_precision_min_score),
    ]
    motion_blur_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_motion_blur_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(motion_blur_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.motion_blur_min_score),
    ]
    landmark_noise_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_landmark_noise_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(landmark_noise_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.landmark_noise_min_score),
    ]
    landmark_spike_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_landmark_spike_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(landmark_spike_dir),
        "--backend-url",
        args.backend_url,
    ]
    fingertip_occlusion_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_fingertip_occlusion_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(fingertip_occlusion_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.fingertip_occlusion_min_score),
    ]
    palm_anchor_occlusion_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_palm_anchor_occlusion_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(palm_anchor_occlusion_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.palm_anchor_occlusion_min_score),
        "--negative-max-score",
        str(args.palm_anchor_occlusion_negative_max_score),
    ]
    hand_shape_scale_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_hand_shape_scale_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(hand_shape_scale_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.hand_shape_scale_min_score),
    ]
    hand_orientation_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_hand_orientation_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(hand_orientation_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.hand_orientation_min_score),
    ]
    hand_z_tilt_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_hand_z_tilt_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(hand_z_tilt_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.hand_z_tilt_min_score),
    ]
    finger_curl_style_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_finger_curl_style_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(finger_curl_style_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.finger_curl_style_min_score),
    ]
    finger_length_style_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_finger_length_style_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(finger_length_style_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.finger_length_style_min_score),
    ]
    moving_setup_exit_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_moving_setup_exit_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(moving_setup_exit_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.moving_setup_exit_min_score),
    ]
    core_phase_speed_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_core_phase_speed_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(core_phase_speed_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.core_phase_speed_min_score),
    ]
    hand_confidence_attenuation_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_hand_confidence_attenuation_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(hand_confidence_attenuation_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.hand_confidence_attenuation_min_score),
    ]
    energy_sampling_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_energy_sampling_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(energy_sampling_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.energy_sampling_min_score),
    ]
    rolling_shutter_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_rolling_shutter_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(rolling_shutter_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.rolling_shutter_min_score),
    ]
    hand_detail_loss_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_hand_detail_loss_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(hand_detail_loss_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.hand_detail_loss_min_score),
    ]
    hand_stream_latency_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_hand_stream_latency_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(hand_stream_latency_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.hand_stream_latency_min_score),
    ]
    ghost_hand_duplicate_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_ghost_hand_duplicate_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(ghost_hand_duplicate_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.ghost_hand_duplicate_min_score),
    ]
    hand_overlap_merge_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_hand_overlap_merge_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(hand_overlap_merge_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.hand_overlap_merge_min_score),
    ]
    wrist_anchor_drift_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_wrist_anchor_drift_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(wrist_anchor_drift_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.wrist_anchor_drift_min_score),
    ]
    finger_chain_latency_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_finger_chain_latency_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(finger_chain_latency_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.finger_chain_latency_min_score),
    ]
    finger_fan_geometry_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_finger_fan_geometry_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(finger_fan_geometry_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.finger_fan_geometry_min_score),
    ]
    finger_base_geometry_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_finger_base_geometry_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(finger_base_geometry_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.finger_base_geometry_min_score),
    ]
    finger_chain_confidence_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_finger_chain_confidence_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(finger_chain_confidence_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.finger_chain_confidence_min_score),
    ]
    finger_chain_smoothing_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_finger_chain_smoothing_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(finger_chain_smoothing_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.finger_chain_smoothing_min_score),
    ]
    finite_coordinate_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_finite_coordinate_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(finite_coordinate_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.finite_coordinate_min_score),
    ]
    bounded_coordinate_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_bounded_coordinate_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(bounded_coordinate_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.bounded_coordinate_min_score),
    ]
    missing_mask_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_missing_mask_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(missing_mask_dir),
        "--backend-url",
        args.backend_url,
    ]
    temporal_padding_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_temporal_padding_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(temporal_padding_dir),
        "--backend-url",
        args.backend_url,
    ]
    phase_order_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_phase_order_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(phase_order_dir),
        "--backend-url",
        args.backend_url,
    ]
    action_crop_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_action_crop_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(action_crop_dir),
        "--backend-url",
        args.backend_url,
    ]
    action_repeat_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_action_repeat_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(action_repeat_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.action_repeat_min_score),
    ]
    noncore_hand_distractor_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_noncore_hand_distractor_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(noncore_hand_distractor_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.noncore_hand_distractor_min_score),
    ]
    relation_geometry_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_relation_geometry_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(relation_geometry_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.relation_geometry_min_score),
        "--negative-max-score",
        str(args.relation_geometry_negative_max_score),
    ]
    core_shape_amplitude_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_core_shape_amplitude_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(core_shape_amplitude_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.core_shape_amplitude_min_score),
        "--negative-max-score",
        str(args.core_shape_amplitude_negative_max_score),
    ]
    perspective_shear_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_perspective_shear_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(perspective_shear_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.perspective_shear_min_score),
    ]
    interhand_temporal_desync_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_interhand_temporal_desync_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(interhand_temporal_desync_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.interhand_temporal_desync_min_score),
    ]
    temporal_order_jitter_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_temporal_order_jitter_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(temporal_order_jitter_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.temporal_order_jitter_min_score),
    ]
    finger_identity_jitter_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_finger_identity_jitter_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(finger_identity_jitter_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.finger_identity_jitter_min_score),
    ]
    hand_scale_flicker_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_hand_scale_flicker_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(hand_scale_flicker_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.hand_scale_flicker_min_score),
    ]
    hand_center_flicker_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_hand_center_flicker_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(hand_center_flicker_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.hand_center_flicker_min_score),
    ]
    global_framing_flicker_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_global_framing_flicker_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(global_framing_flicker_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.global_framing_flicker_min_score),
    ]
    finger_mid_joint_occlusion_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_finger_mid_joint_occlusion_robustness_gate.py"),
        "--template-root",
        str(template_root),
        "--semantic-profile-json",
        str(semantic_profile_json),
        "--output-dir",
        str(finger_mid_joint_occlusion_dir),
        "--backend-url",
        args.backend_url,
        "--min-score",
        str(args.finger_mid_joint_occlusion_min_score),
    ]

    command_specs = [
        ("web_regression", web_cmd, web_dir / "flower_jump_web_regression.json"),
        ("web_confusion_gate", confusion_cmd, confusion_dir / "flower_jump_web_confusion_gate.json"),
        (
            "synthetic_confusion_robustness_gate",
            synthetic_confusion_cmd,
            synthetic_confusion_dir / "flower_jump_synthetic_confusion_robustness_gate.json",
        ),
        ("discrimination_gate", disc_cmd, disc_dir / "flower_jump_discrimination_gate.json"),
        ("pose_robustness_gate", pose_cmd, pose_dir / "flower_jump_pose_robustness_gate.json"),
        ("framing_robustness_gate", framing_cmd, framing_dir / "flower_jump_framing_robustness_gate.json"),
        (
            "aspect_ratio_robustness_gate",
            aspect_ratio_cmd,
            aspect_ratio_dir / "flower_jump_aspect_ratio_robustness_gate.json",
        ),
        (
            "camera_roll_robustness_gate",
            camera_roll_cmd,
            camera_roll_dir / "flower_jump_camera_roll_robustness_gate.json",
        ),
        (
            "body_anchor_robustness_gate",
            body_anchor_cmd,
            body_anchor_dir / "flower_jump_body_anchor_robustness_gate.json",
        ),
        ("depth_robustness_gate", depth_cmd, depth_dir / "flower_jump_depth_robustness_gate.json"),
        (
            "edge_clipping_robustness_gate",
            edge_clipping_cmd,
            edge_clipping_dir / "flower_jump_edge_clipping_robustness_gate.json",
        ),
        ("mirror_robustness_gate", mirror_cmd, mirror_dir / "flower_jump_mirror_robustness_gate.json"),
        (
            "hand_role_robustness_gate",
            hand_role_cmd,
            hand_role_dir / "flower_jump_hand_role_robustness_gate.json",
        ),
        (
            "hand_label_flicker_robustness_gate",
            hand_label_flicker_cmd,
            hand_label_flicker_dir / "flower_jump_hand_label_flicker_robustness_gate.json",
        ),
        (
            "hand_dropout_burst_robustness_gate",
            hand_dropout_burst_cmd,
            hand_dropout_burst_dir / "flower_jump_hand_dropout_burst_robustness_gate.json",
        ),
        ("frame_count_robustness_gate", frame_cmd, frame_dir / "flower_jump_frame_count_robustness_gate.json"),
        (
            "temporal_stutter_robustness_gate",
            temporal_stutter_cmd,
            temporal_stutter_dir / "flower_jump_temporal_stutter_robustness_gate.json",
        ),
        (
            "temporal_rate_robustness_gate",
            temporal_rate_cmd,
            temporal_rate_dir / "flower_jump_temporal_rate_robustness_gate.json",
        ),
        (
            "composite_browser_robustness_gate",
            composite_browser_cmd,
            composite_browser_dir / "flower_jump_composite_browser_robustness_gate.json",
        ),
        (
            "frame_weight_robustness_gate",
            frame_weight_cmd,
            frame_weight_dir / "flower_jump_frame_weight_robustness_gate.json",
        ),
        (
            "coordinate_precision_robustness_gate",
            coordinate_precision_cmd,
            coordinate_precision_dir / "flower_jump_coordinate_precision_robustness_gate.json",
        ),
        (
            "motion_blur_robustness_gate",
            motion_blur_cmd,
            motion_blur_dir / "flower_jump_motion_blur_robustness_gate.json",
        ),
        (
            "landmark_noise_robustness_gate",
            landmark_noise_cmd,
            landmark_noise_dir / "flower_jump_landmark_noise_robustness_gate.json",
        ),
        (
            "landmark_spike_robustness_gate",
            landmark_spike_cmd,
            landmark_spike_dir / "flower_jump_landmark_spike_robustness_gate.json",
        ),
        (
            "fingertip_occlusion_robustness_gate",
            fingertip_occlusion_cmd,
            fingertip_occlusion_dir / "flower_jump_fingertip_occlusion_robustness_gate.json",
        ),
        (
            "palm_anchor_occlusion_robustness_gate",
            palm_anchor_occlusion_cmd,
            palm_anchor_occlusion_dir / "flower_jump_palm_anchor_occlusion_robustness_gate.json",
        ),
        (
            "hand_shape_scale_robustness_gate",
            hand_shape_scale_cmd,
            hand_shape_scale_dir / "flower_jump_hand_shape_scale_robustness_gate.json",
        ),
        (
            "hand_orientation_robustness_gate",
            hand_orientation_cmd,
            hand_orientation_dir / "flower_jump_hand_orientation_robustness_gate.json",
        ),
        (
            "missing_mask_robustness_gate",
            missing_mask_cmd,
            missing_mask_dir / "flower_jump_missing_mask_robustness_gate.json",
        ),
        (
            "temporal_padding_robustness_gate",
            temporal_padding_cmd,
            temporal_padding_dir / "flower_jump_temporal_padding_robustness_gate.json",
        ),
        (
            "action_crop_robustness_gate",
            action_crop_cmd,
            action_crop_dir / "flower_jump_action_crop_robustness_gate.json",
        ),
        (
            "action_repeat_robustness_gate",
            action_repeat_cmd,
            action_repeat_dir / "flower_jump_action_repeat_robustness_gate.json",
        ),
        (
            "phase_order_robustness_gate",
            phase_order_cmd,
            phase_order_dir / "flower_jump_phase_order_robustness_gate.json",
        ),
        (
            "noncore_hand_distractor_robustness_gate",
            noncore_hand_distractor_cmd,
            noncore_hand_distractor_dir / "flower_jump_noncore_hand_distractor_robustness_gate.json",
        ),
        (
            "relation_geometry_robustness_gate",
            relation_geometry_cmd,
            relation_geometry_dir / "flower_jump_relation_geometry_robustness_gate.json",
        ),
        (
            "core_shape_amplitude_robustness_gate",
            core_shape_amplitude_cmd,
            core_shape_amplitude_dir / "flower_jump_core_shape_amplitude_robustness_gate.json",
        ),
        (
            "perspective_shear_robustness_gate",
            perspective_shear_cmd,
            perspective_shear_dir / "flower_jump_perspective_shear_robustness_gate.json",
        ),
        (
            "interhand_temporal_desync_robustness_gate",
            interhand_temporal_desync_cmd,
            interhand_temporal_desync_dir / "flower_jump_interhand_temporal_desync_robustness_gate.json",
        ),
        (
            "temporal_order_jitter_robustness_gate",
            temporal_order_jitter_cmd,
            temporal_order_jitter_dir / "flower_jump_temporal_order_jitter_robustness_gate.json",
        ),
        (
            "finger_identity_jitter_robustness_gate",
            finger_identity_jitter_cmd,
            finger_identity_jitter_dir / "flower_jump_finger_identity_jitter_robustness_gate.json",
        ),
        (
            "hand_scale_flicker_robustness_gate",
            hand_scale_flicker_cmd,
            hand_scale_flicker_dir / "flower_jump_hand_scale_flicker_robustness_gate.json",
        ),
        (
            "hand_center_flicker_robustness_gate",
            hand_center_flicker_cmd,
            hand_center_flicker_dir / "flower_jump_hand_center_flicker_robustness_gate.json",
        ),
        (
            "global_framing_flicker_robustness_gate",
            global_framing_flicker_cmd,
            global_framing_flicker_dir / "flower_jump_global_framing_flicker_robustness_gate.json",
        ),
        (
            "finger_mid_joint_occlusion_robustness_gate",
            finger_mid_joint_occlusion_cmd,
            finger_mid_joint_occlusion_dir / "flower_jump_finger_mid_joint_occlusion_robustness_gate.json",
        ),
        ("z_flicker_robustness_gate", z_flicker_cmd, z_flicker_dir / "flower_jump_z_flicker_robustness_gate.json"),
        (
            "hand_trajectory_interpolation_robustness_gate",
            hand_trajectory_interpolation_cmd,
            hand_trajectory_interpolation_dir / "flower_jump_hand_trajectory_interpolation_robustness_gate.json",
        ),
        (
            "hand_z_tilt_robustness_gate",
            hand_z_tilt_cmd,
            hand_z_tilt_dir / "flower_jump_hand_z_tilt_robustness_gate.json",
        ),
        (
            "finger_curl_style_robustness_gate",
            finger_curl_style_cmd,
            finger_curl_style_dir / "flower_jump_finger_curl_style_robustness_gate.json",
        ),
        (
            "finger_length_style_robustness_gate",
            finger_length_style_cmd,
            finger_length_style_dir / "flower_jump_finger_length_style_robustness_gate.json",
        ),
        (
            "moving_setup_exit_robustness_gate",
            moving_setup_exit_cmd,
            moving_setup_exit_dir / "flower_jump_moving_setup_exit_robustness_gate.json",
        ),
        (
            "core_phase_speed_robustness_gate",
            core_phase_speed_cmd,
            core_phase_speed_dir / "flower_jump_core_phase_speed_robustness_gate.json",
        ),
        (
            "hand_confidence_attenuation_robustness_gate",
            hand_confidence_attenuation_cmd,
            hand_confidence_attenuation_dir / "flower_jump_hand_confidence_attenuation_robustness_gate.json",
        ),
        (
            "energy_sampling_robustness_gate",
            energy_sampling_cmd,
            energy_sampling_dir / "flower_jump_energy_sampling_robustness_gate.json",
        ),
        (
            "rolling_shutter_robustness_gate",
            rolling_shutter_cmd,
            rolling_shutter_dir / "flower_jump_rolling_shutter_robustness_gate.json",
        ),
        (
            "hand_detail_loss_robustness_gate",
            hand_detail_loss_cmd,
            hand_detail_loss_dir / "flower_jump_hand_detail_loss_robustness_gate.json",
        ),
        (
            "hand_stream_latency_robustness_gate",
            hand_stream_latency_cmd,
            hand_stream_latency_dir / "flower_jump_hand_stream_latency_robustness_gate.json",
        ),
        (
            "ghost_hand_duplicate_robustness_gate",
            ghost_hand_duplicate_cmd,
            ghost_hand_duplicate_dir / "flower_jump_ghost_hand_duplicate_robustness_gate.json",
        ),
        (
            "hand_overlap_merge_robustness_gate",
            hand_overlap_merge_cmd,
            hand_overlap_merge_dir / "flower_jump_hand_overlap_merge_robustness_gate.json",
        ),
        (
            "wrist_anchor_drift_robustness_gate",
            wrist_anchor_drift_cmd,
            wrist_anchor_drift_dir / "flower_jump_wrist_anchor_drift_robustness_gate.json",
        ),
        (
            "finger_chain_latency_robustness_gate",
            finger_chain_latency_cmd,
            finger_chain_latency_dir / "flower_jump_finger_chain_latency_robustness_gate.json",
        ),
        (
            "finger_fan_geometry_robustness_gate",
            finger_fan_geometry_cmd,
            finger_fan_geometry_dir / "flower_jump_finger_fan_geometry_robustness_gate.json",
        ),
        (
            "finger_base_geometry_robustness_gate",
            finger_base_geometry_cmd,
            finger_base_geometry_dir / "flower_jump_finger_base_geometry_robustness_gate.json",
        ),
        (
            "finger_chain_confidence_robustness_gate",
            finger_chain_confidence_cmd,
            finger_chain_confidence_dir / "flower_jump_finger_chain_confidence_robustness_gate.json",
        ),
        (
            "finger_chain_smoothing_robustness_gate",
            finger_chain_smoothing_cmd,
            finger_chain_smoothing_dir / "flower_jump_finger_chain_smoothing_robustness_gate.json",
        ),
        (
            "finite_coordinate_robustness_gate",
            finite_coordinate_cmd,
            finite_coordinate_dir / "flower_jump_finite_coordinate_robustness_gate.json",
        ),
        (
            "bounded_coordinate_robustness_gate",
            bounded_coordinate_cmd,
            bounded_coordinate_dir / "flower_jump_bounded_coordinate_robustness_gate.json",
        ),
        (
            "temporal_metadata_robustness_gate",
            temporal_metadata_cmd,
            temporal_metadata_dir / "flower_jump_temporal_metadata_robustness_gate.json",
        ),
    ]
    runs: List[Dict[str, Any]] = []
    for name, cmd, json_path in command_specs:
        if args.reuse_existing and json_path.exists():
            now = datetime.now().isoformat(timespec="seconds")
            runs.append(
                {
                    "name": name,
                    "command": list(cmd),
                    "started_at": now,
                    "finished_at": now,
                    "returncode": 0,
                    "stdout": f"reused existing result: {json_path}\n",
                    "stderr": "",
                    "reused_existing": True,
                }
            )
        else:
            runs.append(_run_command(name, cmd, REPO_ROOT))

    subgates: List[Dict[str, Any]] = []
    web_payload: Dict[str, Any] = {}
    confusion_payload: Dict[str, Any] = {}
    synthetic_confusion_payload: Dict[str, Any] = {}
    disc_payload: Dict[str, Any] = {}
    pose_payload: Dict[str, Any] = {}
    framing_payload: Dict[str, Any] = {}
    aspect_ratio_payload: Dict[str, Any] = {}
    camera_roll_payload: Dict[str, Any] = {}
    body_anchor_payload: Dict[str, Any] = {}
    depth_payload: Dict[str, Any] = {}
    z_flicker_payload: Dict[str, Any] = {}
    edge_clipping_payload: Dict[str, Any] = {}
    mirror_payload: Dict[str, Any] = {}
    hand_role_payload: Dict[str, Any] = {}
    hand_label_flicker_payload: Dict[str, Any] = {}
    hand_dropout_burst_payload: Dict[str, Any] = {}
    frame_payload: Dict[str, Any] = {}
    temporal_stutter_payload: Dict[str, Any] = {}
    temporal_rate_payload: Dict[str, Any] = {}
    temporal_metadata_payload: Dict[str, Any] = {}
    composite_browser_payload: Dict[str, Any] = {}
    frame_weight_payload: Dict[str, Any] = {}
    coordinate_precision_payload: Dict[str, Any] = {}
    motion_blur_payload: Dict[str, Any] = {}
    landmark_noise_payload: Dict[str, Any] = {}
    landmark_spike_payload: Dict[str, Any] = {}
    fingertip_occlusion_payload: Dict[str, Any] = {}
    palm_anchor_occlusion_payload: Dict[str, Any] = {}
    hand_shape_scale_payload: Dict[str, Any] = {}
    hand_orientation_payload: Dict[str, Any] = {}
    missing_mask_payload: Dict[str, Any] = {}
    temporal_padding_payload: Dict[str, Any] = {}
    phase_order_payload: Dict[str, Any] = {}
    action_crop_payload: Dict[str, Any] = {}
    action_repeat_payload: Dict[str, Any] = {}
    noncore_hand_distractor_payload: Dict[str, Any] = {}
    relation_geometry_payload: Dict[str, Any] = {}
    core_shape_amplitude_payload: Dict[str, Any] = {}
    perspective_shear_payload: Dict[str, Any] = {}
    interhand_temporal_desync_payload: Dict[str, Any] = {}
    temporal_order_jitter_payload: Dict[str, Any] = {}
    finger_identity_jitter_payload: Dict[str, Any] = {}
    hand_scale_flicker_payload: Dict[str, Any] = {}
    hand_center_flicker_payload: Dict[str, Any] = {}
    global_framing_flicker_payload: Dict[str, Any] = {}
    finger_mid_joint_occlusion_payload: Dict[str, Any] = {}
    hand_trajectory_interpolation_payload: Dict[str, Any] = {}
    hand_z_tilt_payload: Dict[str, Any] = {}
    finger_curl_style_payload: Dict[str, Any] = {}
    finger_length_style_payload: Dict[str, Any] = {}
    moving_setup_exit_payload: Dict[str, Any] = {}
    core_phase_speed_payload: Dict[str, Any] = {}
    hand_confidence_attenuation_payload: Dict[str, Any] = {}
    energy_sampling_payload: Dict[str, Any] = {}
    rolling_shutter_payload: Dict[str, Any] = {}
    hand_detail_loss_payload: Dict[str, Any] = {}
    hand_stream_latency_payload: Dict[str, Any] = {}
    ghost_hand_duplicate_payload: Dict[str, Any] = {}
    hand_overlap_merge_payload: Dict[str, Any] = {}
    wrist_anchor_drift_payload: Dict[str, Any] = {}
    finger_chain_latency_payload: Dict[str, Any] = {}
    finger_fan_geometry_payload: Dict[str, Any] = {}
    finger_base_geometry_payload: Dict[str, Any] = {}
    finger_chain_confidence_payload: Dict[str, Any] = {}
    finger_chain_smoothing_payload: Dict[str, Any] = {}
    finite_coordinate_payload: Dict[str, Any] = {}
    bounded_coordinate_payload: Dict[str, Any] = {}

    def add_subgate(run: Dict[str, Any], json_path: Path, md_path: Path) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        passed = False
        parse_error = ""
        if json_path.exists():
            try:
                payload = _load_json(json_path)
                passed = bool(payload.get("passed")) and int(run["returncode"]) == 0
            except Exception as exc:  # noqa: BLE001 - report parse failures in the aggregate gate.
                parse_error = str(exc)
        else:
            parse_error = f"missing json: {json_path}"
        subgates.append(
            {
                "name": run["name"],
                "returncode": run["returncode"],
                "passed": passed,
                "json_path": str(json_path),
                "md_path": str(md_path) if md_path.exists() else "",
                "parse_error": parse_error,
            }
        )
        return payload

    web_payload = add_subgate(runs[0], web_dir / "flower_jump_web_regression.json", web_dir / "flower_jump_web_regression.md")
    confusion_payload = add_subgate(runs[1], confusion_dir / "flower_jump_web_confusion_gate.json", confusion_dir / "flower_jump_web_confusion_gate.md")
    synthetic_confusion_payload = add_subgate(
        runs[2],
        synthetic_confusion_dir / "flower_jump_synthetic_confusion_robustness_gate.json",
        synthetic_confusion_dir / "flower_jump_synthetic_confusion_robustness_gate.md",
    )
    disc_payload = add_subgate(runs[3], disc_dir / "flower_jump_discrimination_gate.json", disc_dir / "flower_jump_discrimination_gate.md")
    pose_payload = add_subgate(runs[4], pose_dir / "flower_jump_pose_robustness_gate.json", pose_dir / "flower_jump_pose_robustness_gate.md")
    framing_payload = add_subgate(
        runs[5],
        framing_dir / "flower_jump_framing_robustness_gate.json",
        framing_dir / "flower_jump_framing_robustness_gate.md",
    )
    aspect_ratio_payload = add_subgate(
        runs[6],
        aspect_ratio_dir / "flower_jump_aspect_ratio_robustness_gate.json",
        aspect_ratio_dir / "flower_jump_aspect_ratio_robustness_gate.md",
    )
    camera_roll_payload = add_subgate(
        runs[7],
        camera_roll_dir / "flower_jump_camera_roll_robustness_gate.json",
        camera_roll_dir / "flower_jump_camera_roll_robustness_gate.md",
    )
    body_anchor_payload = add_subgate(
        runs[8],
        body_anchor_dir / "flower_jump_body_anchor_robustness_gate.json",
        body_anchor_dir / "flower_jump_body_anchor_robustness_gate.md",
    )
    depth_payload = add_subgate(runs[9], depth_dir / "flower_jump_depth_robustness_gate.json", depth_dir / "flower_jump_depth_robustness_gate.md")
    edge_clipping_payload = add_subgate(
        runs[10],
        edge_clipping_dir / "flower_jump_edge_clipping_robustness_gate.json",
        edge_clipping_dir / "flower_jump_edge_clipping_robustness_gate.md",
    )
    mirror_payload = add_subgate(runs[11], mirror_dir / "flower_jump_mirror_robustness_gate.json", mirror_dir / "flower_jump_mirror_robustness_gate.md")
    hand_role_payload = add_subgate(
        runs[12],
        hand_role_dir / "flower_jump_hand_role_robustness_gate.json",
        hand_role_dir / "flower_jump_hand_role_robustness_gate.md",
    )
    hand_label_flicker_payload = add_subgate(
        runs[13],
        hand_label_flicker_dir / "flower_jump_hand_label_flicker_robustness_gate.json",
        hand_label_flicker_dir / "flower_jump_hand_label_flicker_robustness_gate.md",
    )
    hand_dropout_burst_payload = add_subgate(
        runs[14],
        hand_dropout_burst_dir / "flower_jump_hand_dropout_burst_robustness_gate.json",
        hand_dropout_burst_dir / "flower_jump_hand_dropout_burst_robustness_gate.md",
    )
    frame_payload = add_subgate(runs[15], frame_dir / "flower_jump_frame_count_robustness_gate.json", frame_dir / "flower_jump_frame_count_robustness_gate.md")
    temporal_stutter_payload = add_subgate(
        runs[16],
        temporal_stutter_dir / "flower_jump_temporal_stutter_robustness_gate.json",
        temporal_stutter_dir / "flower_jump_temporal_stutter_robustness_gate.md",
    )
    temporal_rate_payload = add_subgate(
        runs[17],
        temporal_rate_dir / "flower_jump_temporal_rate_robustness_gate.json",
        temporal_rate_dir / "flower_jump_temporal_rate_robustness_gate.md",
    )
    composite_browser_payload = add_subgate(
        runs[18],
        composite_browser_dir / "flower_jump_composite_browser_robustness_gate.json",
        composite_browser_dir / "flower_jump_composite_browser_robustness_gate.md",
    )
    frame_weight_payload = add_subgate(
        runs[19],
        frame_weight_dir / "flower_jump_frame_weight_robustness_gate.json",
        frame_weight_dir / "flower_jump_frame_weight_robustness_gate.md",
    )
    coordinate_precision_payload = add_subgate(
        runs[20],
        coordinate_precision_dir / "flower_jump_coordinate_precision_robustness_gate.json",
        coordinate_precision_dir / "flower_jump_coordinate_precision_robustness_gate.md",
    )
    motion_blur_payload = add_subgate(
        runs[21],
        motion_blur_dir / "flower_jump_motion_blur_robustness_gate.json",
        motion_blur_dir / "flower_jump_motion_blur_robustness_gate.md",
    )
    landmark_noise_payload = add_subgate(
        runs[22],
        landmark_noise_dir / "flower_jump_landmark_noise_robustness_gate.json",
        landmark_noise_dir / "flower_jump_landmark_noise_robustness_gate.md",
    )
    landmark_spike_payload = add_subgate(
        runs[23],
        landmark_spike_dir / "flower_jump_landmark_spike_robustness_gate.json",
        landmark_spike_dir / "flower_jump_landmark_spike_robustness_gate.md",
    )
    fingertip_occlusion_payload = add_subgate(
        runs[24],
        fingertip_occlusion_dir / "flower_jump_fingertip_occlusion_robustness_gate.json",
        fingertip_occlusion_dir / "flower_jump_fingertip_occlusion_robustness_gate.md",
    )
    palm_anchor_occlusion_payload = add_subgate(
        runs[25],
        palm_anchor_occlusion_dir / "flower_jump_palm_anchor_occlusion_robustness_gate.json",
        palm_anchor_occlusion_dir / "flower_jump_palm_anchor_occlusion_robustness_gate.md",
    )
    hand_shape_scale_payload = add_subgate(
        runs[26],
        hand_shape_scale_dir / "flower_jump_hand_shape_scale_robustness_gate.json",
        hand_shape_scale_dir / "flower_jump_hand_shape_scale_robustness_gate.md",
    )
    hand_orientation_payload = add_subgate(
        runs[27],
        hand_orientation_dir / "flower_jump_hand_orientation_robustness_gate.json",
        hand_orientation_dir / "flower_jump_hand_orientation_robustness_gate.md",
    )
    missing_mask_payload = add_subgate(
        runs[28],
        missing_mask_dir / "flower_jump_missing_mask_robustness_gate.json",
        missing_mask_dir / "flower_jump_missing_mask_robustness_gate.md",
    )
    temporal_padding_payload = add_subgate(
        runs[29],
        temporal_padding_dir / "flower_jump_temporal_padding_robustness_gate.json",
        temporal_padding_dir / "flower_jump_temporal_padding_robustness_gate.md",
    )
    action_crop_payload = add_subgate(
        runs[30],
        action_crop_dir / "flower_jump_action_crop_robustness_gate.json",
        action_crop_dir / "flower_jump_action_crop_robustness_gate.md",
    )
    action_repeat_payload = add_subgate(
        runs[31],
        action_repeat_dir / "flower_jump_action_repeat_robustness_gate.json",
        action_repeat_dir / "flower_jump_action_repeat_robustness_gate.md",
    )
    phase_order_payload = add_subgate(
        runs[32],
        phase_order_dir / "flower_jump_phase_order_robustness_gate.json",
        phase_order_dir / "flower_jump_phase_order_robustness_gate.md",
    )
    noncore_hand_distractor_payload = add_subgate(
        runs[33],
        noncore_hand_distractor_dir / "flower_jump_noncore_hand_distractor_robustness_gate.json",
        noncore_hand_distractor_dir / "flower_jump_noncore_hand_distractor_robustness_gate.md",
    )
    relation_geometry_payload = add_subgate(
        runs[34],
        relation_geometry_dir / "flower_jump_relation_geometry_robustness_gate.json",
        relation_geometry_dir / "flower_jump_relation_geometry_robustness_gate.md",
    )
    core_shape_amplitude_payload = add_subgate(
        runs[35],
        core_shape_amplitude_dir / "flower_jump_core_shape_amplitude_robustness_gate.json",
        core_shape_amplitude_dir / "flower_jump_core_shape_amplitude_robustness_gate.md",
    )
    perspective_shear_payload = add_subgate(
        runs[36],
        perspective_shear_dir / "flower_jump_perspective_shear_robustness_gate.json",
        perspective_shear_dir / "flower_jump_perspective_shear_robustness_gate.md",
    )
    interhand_temporal_desync_payload = add_subgate(
        runs[37],
        interhand_temporal_desync_dir / "flower_jump_interhand_temporal_desync_robustness_gate.json",
        interhand_temporal_desync_dir / "flower_jump_interhand_temporal_desync_robustness_gate.md",
    )
    temporal_order_jitter_payload = add_subgate(
        runs[38],
        temporal_order_jitter_dir / "flower_jump_temporal_order_jitter_robustness_gate.json",
        temporal_order_jitter_dir / "flower_jump_temporal_order_jitter_robustness_gate.md",
    )
    finger_identity_jitter_payload = add_subgate(
        runs[39],
        finger_identity_jitter_dir / "flower_jump_finger_identity_jitter_robustness_gate.json",
        finger_identity_jitter_dir / "flower_jump_finger_identity_jitter_robustness_gate.md",
    )
    hand_scale_flicker_payload = add_subgate(
        runs[40],
        hand_scale_flicker_dir / "flower_jump_hand_scale_flicker_robustness_gate.json",
        hand_scale_flicker_dir / "flower_jump_hand_scale_flicker_robustness_gate.md",
    )
    hand_center_flicker_payload = add_subgate(
        runs[41],
        hand_center_flicker_dir / "flower_jump_hand_center_flicker_robustness_gate.json",
        hand_center_flicker_dir / "flower_jump_hand_center_flicker_robustness_gate.md",
    )
    global_framing_flicker_payload = add_subgate(
        runs[42],
        global_framing_flicker_dir / "flower_jump_global_framing_flicker_robustness_gate.json",
        global_framing_flicker_dir / "flower_jump_global_framing_flicker_robustness_gate.md",
    )
    finger_mid_joint_occlusion_payload = add_subgate(
        runs[43],
        finger_mid_joint_occlusion_dir / "flower_jump_finger_mid_joint_occlusion_robustness_gate.json",
        finger_mid_joint_occlusion_dir / "flower_jump_finger_mid_joint_occlusion_robustness_gate.md",
    )
    z_flicker_payload = add_subgate(
        runs[44],
        z_flicker_dir / "flower_jump_z_flicker_robustness_gate.json",
        z_flicker_dir / "flower_jump_z_flicker_robustness_gate.md",
    )
    hand_trajectory_interpolation_payload = add_subgate(
        runs[45],
        hand_trajectory_interpolation_dir / "flower_jump_hand_trajectory_interpolation_robustness_gate.json",
        hand_trajectory_interpolation_dir / "flower_jump_hand_trajectory_interpolation_robustness_gate.md",
    )
    hand_z_tilt_payload = add_subgate(
        runs[46],
        hand_z_tilt_dir / "flower_jump_hand_z_tilt_robustness_gate.json",
        hand_z_tilt_dir / "flower_jump_hand_z_tilt_robustness_gate.md",
    )
    finger_curl_style_payload = add_subgate(
        runs[47],
        finger_curl_style_dir / "flower_jump_finger_curl_style_robustness_gate.json",
        finger_curl_style_dir / "flower_jump_finger_curl_style_robustness_gate.md",
    )
    finger_length_style_payload = add_subgate(
        runs[48],
        finger_length_style_dir / "flower_jump_finger_length_style_robustness_gate.json",
        finger_length_style_dir / "flower_jump_finger_length_style_robustness_gate.md",
    )
    moving_setup_exit_payload = add_subgate(
        runs[49],
        moving_setup_exit_dir / "flower_jump_moving_setup_exit_robustness_gate.json",
        moving_setup_exit_dir / "flower_jump_moving_setup_exit_robustness_gate.md",
    )
    core_phase_speed_payload = add_subgate(
        runs[50],
        core_phase_speed_dir / "flower_jump_core_phase_speed_robustness_gate.json",
        core_phase_speed_dir / "flower_jump_core_phase_speed_robustness_gate.md",
    )
    hand_confidence_attenuation_payload = add_subgate(
        runs[51],
        hand_confidence_attenuation_dir / "flower_jump_hand_confidence_attenuation_robustness_gate.json",
        hand_confidence_attenuation_dir / "flower_jump_hand_confidence_attenuation_robustness_gate.md",
    )
    energy_sampling_payload = add_subgate(
        runs[52],
        energy_sampling_dir / "flower_jump_energy_sampling_robustness_gate.json",
        energy_sampling_dir / "flower_jump_energy_sampling_robustness_gate.md",
    )
    rolling_shutter_payload = add_subgate(
        runs[53],
        rolling_shutter_dir / "flower_jump_rolling_shutter_robustness_gate.json",
        rolling_shutter_dir / "flower_jump_rolling_shutter_robustness_gate.md",
    )
    hand_detail_loss_payload = add_subgate(
        runs[54],
        hand_detail_loss_dir / "flower_jump_hand_detail_loss_robustness_gate.json",
        hand_detail_loss_dir / "flower_jump_hand_detail_loss_robustness_gate.md",
    )
    hand_stream_latency_payload = add_subgate(
        runs[55],
        hand_stream_latency_dir / "flower_jump_hand_stream_latency_robustness_gate.json",
        hand_stream_latency_dir / "flower_jump_hand_stream_latency_robustness_gate.md",
    )
    ghost_hand_duplicate_payload = add_subgate(
        runs[56],
        ghost_hand_duplicate_dir / "flower_jump_ghost_hand_duplicate_robustness_gate.json",
        ghost_hand_duplicate_dir / "flower_jump_ghost_hand_duplicate_robustness_gate.md",
    )
    hand_overlap_merge_payload = add_subgate(
        runs[57],
        hand_overlap_merge_dir / "flower_jump_hand_overlap_merge_robustness_gate.json",
        hand_overlap_merge_dir / "flower_jump_hand_overlap_merge_robustness_gate.md",
    )
    wrist_anchor_drift_payload = add_subgate(
        runs[58],
        wrist_anchor_drift_dir / "flower_jump_wrist_anchor_drift_robustness_gate.json",
        wrist_anchor_drift_dir / "flower_jump_wrist_anchor_drift_robustness_gate.md",
    )
    finger_chain_latency_payload = add_subgate(
        runs[59],
        finger_chain_latency_dir / "flower_jump_finger_chain_latency_robustness_gate.json",
        finger_chain_latency_dir / "flower_jump_finger_chain_latency_robustness_gate.md",
    )
    finger_fan_geometry_payload = add_subgate(
        runs[60],
        finger_fan_geometry_dir / "flower_jump_finger_fan_geometry_robustness_gate.json",
        finger_fan_geometry_dir / "flower_jump_finger_fan_geometry_robustness_gate.md",
    )
    finger_base_geometry_payload = add_subgate(
        runs[61],
        finger_base_geometry_dir / "flower_jump_finger_base_geometry_robustness_gate.json",
        finger_base_geometry_dir / "flower_jump_finger_base_geometry_robustness_gate.md",
    )
    finger_chain_confidence_payload = add_subgate(
        runs[62],
        finger_chain_confidence_dir / "flower_jump_finger_chain_confidence_robustness_gate.json",
        finger_chain_confidence_dir / "flower_jump_finger_chain_confidence_robustness_gate.md",
    )
    finger_chain_smoothing_payload = add_subgate(
        runs[63],
        finger_chain_smoothing_dir / "flower_jump_finger_chain_smoothing_robustness_gate.json",
        finger_chain_smoothing_dir / "flower_jump_finger_chain_smoothing_robustness_gate.md",
    )
    finite_coordinate_payload = add_subgate(
        runs[64],
        finite_coordinate_dir / "flower_jump_finite_coordinate_robustness_gate.json",
        finite_coordinate_dir / "flower_jump_finite_coordinate_robustness_gate.md",
    )
    bounded_coordinate_payload = add_subgate(
        runs[65],
        bounded_coordinate_dir / "flower_jump_bounded_coordinate_robustness_gate.json",
        bounded_coordinate_dir / "flower_jump_bounded_coordinate_robustness_gate.md",
    )
    temporal_metadata_payload = add_subgate(
        runs[66],
        temporal_metadata_dir / "flower_jump_temporal_metadata_robustness_gate.json",
        temporal_metadata_dir / "flower_jump_temporal_metadata_robustness_gate.md",
    )

    marker_status = _load_marker_status()
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "claim_policy": "combined engineering quality gate; not calibrated real-user scoring",
        "web_root": str(web_root),
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_url": args.backend_url,
        "web_filters": {
            "latest": args.latest,
            "since_request_id": args.since_request_id,
            "request_ids": list(args.request_ids),
        },
        "runs": runs,
        "subgates": subgates,
        "web_summary": _web_summary(web_payload) if web_payload else {},
        "confusion_summary": _confusion_summary(confusion_payload) if confusion_payload else {},
        "synthetic_confusion_summary": _synthetic_confusion_summary(synthetic_confusion_payload) if synthetic_confusion_payload else {},
        "discrimination_summary": _discrimination_summary(disc_payload) if disc_payload else {},
        "pose_summary": _pose_summary(pose_payload) if pose_payload else {},
        "framing_summary": _framing_summary(framing_payload) if framing_payload else {},
        "aspect_ratio_summary": _aspect_ratio_summary(aspect_ratio_payload) if aspect_ratio_payload else {},
        "camera_roll_summary": _camera_roll_summary(camera_roll_payload) if camera_roll_payload else {},
        "body_anchor_summary": _body_anchor_summary(body_anchor_payload) if body_anchor_payload else {},
        "depth_summary": _depth_summary(depth_payload) if depth_payload else {},
        "z_flicker_summary": _z_flicker_summary(z_flicker_payload) if z_flicker_payload else {},
        "hand_trajectory_interpolation_summary": (
            _hand_trajectory_interpolation_summary(hand_trajectory_interpolation_payload)
            if hand_trajectory_interpolation_payload
            else {}
        ),
        "edge_clipping_summary": _edge_clipping_summary(edge_clipping_payload) if edge_clipping_payload else {},
        "mirror_summary": _mirror_summary(mirror_payload) if mirror_payload else {},
        "hand_role_summary": _hand_role_summary(hand_role_payload) if hand_role_payload else {},
        "hand_label_flicker_summary": _hand_label_flicker_summary(hand_label_flicker_payload) if hand_label_flicker_payload else {},
        "hand_dropout_burst_summary": _hand_dropout_burst_summary(hand_dropout_burst_payload) if hand_dropout_burst_payload else {},
        "frame_summary": _frame_summary(frame_payload) if frame_payload else {},
        "temporal_stutter_summary": _temporal_stutter_summary(temporal_stutter_payload) if temporal_stutter_payload else {},
        "temporal_rate_summary": _temporal_rate_summary(temporal_rate_payload) if temporal_rate_payload else {},
        "temporal_metadata_summary": _temporal_metadata_summary(temporal_metadata_payload) if temporal_metadata_payload else {},
        "composite_browser_summary": _composite_browser_summary(composite_browser_payload) if composite_browser_payload else {},
        "frame_weight_summary": _frame_weight_summary(frame_weight_payload) if frame_weight_payload else {},
        "coordinate_precision_summary": _coordinate_precision_summary(coordinate_precision_payload) if coordinate_precision_payload else {},
        "motion_blur_summary": _motion_blur_summary(motion_blur_payload) if motion_blur_payload else {},
        "landmark_noise_summary": _landmark_noise_summary(landmark_noise_payload) if landmark_noise_payload else {},
        "landmark_spike_summary": _landmark_spike_summary(landmark_spike_payload) if landmark_spike_payload else {},
        "fingertip_occlusion_summary": _fingertip_occlusion_summary(fingertip_occlusion_payload) if fingertip_occlusion_payload else {},
        "palm_anchor_occlusion_summary": _palm_anchor_occlusion_summary(palm_anchor_occlusion_payload) if palm_anchor_occlusion_payload else {},
        "hand_shape_scale_summary": _hand_shape_scale_summary(hand_shape_scale_payload) if hand_shape_scale_payload else {},
        "hand_orientation_summary": _hand_orientation_summary(hand_orientation_payload) if hand_orientation_payload else {},
        "hand_z_tilt_summary": _hand_z_tilt_summary(hand_z_tilt_payload) if hand_z_tilt_payload else {},
        "finger_curl_style_summary": _finger_curl_style_summary(finger_curl_style_payload) if finger_curl_style_payload else {},
        "finger_length_style_summary": _finger_length_style_summary(finger_length_style_payload) if finger_length_style_payload else {},
        "moving_setup_exit_summary": _moving_setup_exit_summary(moving_setup_exit_payload) if moving_setup_exit_payload else {},
        "core_phase_speed_summary": _core_phase_speed_summary(core_phase_speed_payload) if core_phase_speed_payload else {},
        "hand_confidence_attenuation_summary": (
            _hand_confidence_attenuation_summary(hand_confidence_attenuation_payload)
            if hand_confidence_attenuation_payload
            else {}
        ),
        "energy_sampling_summary": _energy_sampling_summary(energy_sampling_payload) if energy_sampling_payload else {},
        "rolling_shutter_summary": _rolling_shutter_summary(rolling_shutter_payload) if rolling_shutter_payload else {},
        "hand_detail_loss_summary": _hand_detail_loss_summary(hand_detail_loss_payload) if hand_detail_loss_payload else {},
        "hand_stream_latency_summary": (
            _hand_stream_latency_summary(hand_stream_latency_payload)
            if hand_stream_latency_payload
            else {}
        ),
        "ghost_hand_duplicate_summary": (
            _ghost_hand_duplicate_summary(ghost_hand_duplicate_payload)
            if ghost_hand_duplicate_payload
            else {}
        ),
        "hand_overlap_merge_summary": (
            _hand_overlap_merge_summary(hand_overlap_merge_payload)
            if hand_overlap_merge_payload
            else {}
        ),
        "wrist_anchor_drift_summary": (
            _wrist_anchor_drift_summary(wrist_anchor_drift_payload)
            if wrist_anchor_drift_payload
            else {}
        ),
        "finger_chain_latency_summary": (
            _finger_chain_latency_summary(finger_chain_latency_payload)
            if finger_chain_latency_payload
            else {}
        ),
        "finger_fan_geometry_summary": (
            _finger_fan_geometry_summary(finger_fan_geometry_payload)
            if finger_fan_geometry_payload
            else {}
        ),
        "finger_base_geometry_summary": (
            _finger_base_geometry_summary(finger_base_geometry_payload)
            if finger_base_geometry_payload
            else {}
        ),
        "finger_chain_confidence_summary": (
            _finger_chain_confidence_summary(finger_chain_confidence_payload)
            if finger_chain_confidence_payload
            else {}
        ),
        "finger_chain_smoothing_summary": (
            _finger_chain_smoothing_summary(finger_chain_smoothing_payload)
            if finger_chain_smoothing_payload
            else {}
        ),
        "finite_coordinate_summary": (
            _finite_coordinate_summary(finite_coordinate_payload)
            if finite_coordinate_payload
            else {}
        ),
        "bounded_coordinate_summary": (
            _bounded_coordinate_summary(bounded_coordinate_payload)
            if bounded_coordinate_payload
            else {}
        ),
        "missing_mask_summary": _missing_mask_summary(missing_mask_payload) if missing_mask_payload else {},
        "temporal_padding_summary": _temporal_padding_summary(temporal_padding_payload) if temporal_padding_payload else {},
        "phase_order_summary": _phase_order_summary(phase_order_payload) if phase_order_payload else {},
        "action_crop_summary": _action_crop_summary(action_crop_payload) if action_crop_payload else {},
        "action_repeat_summary": _action_repeat_summary(action_repeat_payload) if action_repeat_payload else {},
        "noncore_hand_distractor_summary": _noncore_hand_distractor_summary(noncore_hand_distractor_payload) if noncore_hand_distractor_payload else {},
        "relation_geometry_summary": _relation_geometry_summary(relation_geometry_payload) if relation_geometry_payload else {},
        "core_shape_amplitude_summary": _core_shape_amplitude_summary(core_shape_amplitude_payload) if core_shape_amplitude_payload else {},
        "perspective_shear_summary": _perspective_shear_summary(perspective_shear_payload) if perspective_shear_payload else {},
        "interhand_temporal_desync_summary": _interhand_temporal_desync_summary(interhand_temporal_desync_payload) if interhand_temporal_desync_payload else {},
        "temporal_order_jitter_summary": _temporal_order_jitter_summary(temporal_order_jitter_payload) if temporal_order_jitter_payload else {},
        "finger_identity_jitter_summary": _finger_identity_jitter_summary(finger_identity_jitter_payload) if finger_identity_jitter_payload else {},
        "hand_scale_flicker_summary": _hand_scale_flicker_summary(hand_scale_flicker_payload) if hand_scale_flicker_payload else {},
        "hand_center_flicker_summary": _hand_center_flicker_summary(hand_center_flicker_payload) if hand_center_flicker_payload else {},
        "global_framing_flicker_summary": _global_framing_flicker_summary(global_framing_flicker_payload) if global_framing_flicker_payload else {},
        "finger_mid_joint_occlusion_summary": _finger_mid_joint_occlusion_summary(finger_mid_joint_occlusion_payload) if finger_mid_joint_occlusion_payload else {},
        "marker_status": marker_status,
        "passed": all(item.get("passed") for item in subgates),
    }
    json_path = output_dir / "flower_jump_quality_gate.json"
    md_path = output_dir / "flower_jump_quality_gate.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    payload["json_path"] = str(json_path)
    payload["md_path"] = str(md_path)
    return payload


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run the combined flower/jump quality gate.")
    parser.add_argument("--web-root", default=str(DEFAULT_WEB_ROOT))
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default="", help="Default: date-stamped flower_jump_quality_gate_* under scoring_mvp_run3")
    parser.add_argument("--reuse-existing", action="store_true", help="Reuse completed subgate JSON files in output-dir and run only missing subgates.")
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--latest", type=int, default=0, help="Pass through to saved-web subgates.")
    parser.add_argument("--since-request-id", default="", help="Pass through to saved-web subgates.")
    parser.add_argument("--request-ids", nargs="*", default=[], help="Pass through to saved-web subgates.")
    parser.add_argument("--confusion-min-target-score", type=float, default=60.0)
    parser.add_argument("--confusion-max-cross-score", type=float, default=55.0)
    parser.add_argument("--confusion-min-margin", type=float, default=15.0)
    parser.add_argument("--confusion-min-eligible-per-word", type=int, default=1)
    parser.add_argument("--synthetic-confusion-min-target-score", type=float, default=70.0)
    parser.add_argument("--synthetic-confusion-max-cross-score", type=float, default=55.0)
    parser.add_argument("--synthetic-confusion-min-margin", type=float, default=15.0)
    parser.add_argument("--positive-threshold", type=float, default=75.0)
    parser.add_argument("--negative-threshold", type=float, default=50.0)
    parser.add_argument("--pose-min-score", type=float, default=70.0)
    parser.add_argument("--framing-min-score", type=float, default=70.0)
    parser.add_argument("--aspect-ratio-min-score", type=float, default=75.0)
    parser.add_argument("--camera-roll-min-score", type=float, default=75.0)
    parser.add_argument("--body-anchor-min-score", type=float, default=90.0)
    parser.add_argument("--depth-min-score", type=float, default=70.0)
    parser.add_argument("--z-flicker-min-score", type=float, default=70.0)
    parser.add_argument("--hand-trajectory-interpolation-min-score", type=float, default=70.0)
    parser.add_argument("--frame-min-score", type=float, default=70.0)
    parser.add_argument("--hand-role-min-score", type=float, default=70.0)
    parser.add_argument("--hand-role-max-role-swap-score", type=float, default=50.0)
    parser.add_argument("--hand-dropout-burst-min-score", type=float, default=70.0)
    parser.add_argument("--temporal-stutter-min-score", type=float, default=70.0)
    parser.add_argument("--temporal-rate-min-score", type=float, default=70.0)
    parser.add_argument("--temporal-metadata-min-score", type=float, default=70.0)
    parser.add_argument("--composite-browser-min-score", type=float, default=70.0)
    parser.add_argument("--frame-weight-min-score", type=float, default=70.0)
    parser.add_argument("--coordinate-precision-min-score", type=float, default=70.0)
    parser.add_argument("--motion-blur-min-score", type=float, default=70.0)
    parser.add_argument("--landmark-noise-min-score", type=float, default=70.0)
    parser.add_argument("--fingertip-occlusion-min-score", type=float, default=70.0)
    parser.add_argument("--palm-anchor-occlusion-min-score", type=float, default=70.0)
    parser.add_argument("--palm-anchor-occlusion-negative-max-score", type=float, default=45.0)
    parser.add_argument("--hand-shape-scale-min-score", type=float, default=70.0)
    parser.add_argument("--hand-orientation-min-score", type=float, default=70.0)
    parser.add_argument("--hand-z-tilt-min-score", type=float, default=70.0)
    parser.add_argument("--finger-curl-style-min-score", type=float, default=70.0)
    parser.add_argument("--finger-length-style-min-score", type=float, default=70.0)
    parser.add_argument("--moving-setup-exit-min-score", type=float, default=70.0)
    parser.add_argument("--core-phase-speed-min-score", type=float, default=70.0)
    parser.add_argument("--hand-confidence-attenuation-min-score", type=float, default=70.0)
    parser.add_argument("--energy-sampling-min-score", type=float, default=70.0)
    parser.add_argument("--rolling-shutter-min-score", type=float, default=70.0)
    parser.add_argument("--hand-detail-loss-min-score", type=float, default=70.0)
    parser.add_argument("--hand-stream-latency-min-score", type=float, default=70.0)
    parser.add_argument("--action-repeat-min-score", type=float, default=70.0)
    parser.add_argument("--noncore-hand-distractor-min-score", type=float, default=70.0)
    parser.add_argument("--relation-geometry-min-score", type=float, default=70.0)
    parser.add_argument("--relation-geometry-negative-max-score", type=float, default=45.0)
    parser.add_argument("--core-shape-amplitude-min-score", type=float, default=70.0)
    parser.add_argument("--core-shape-amplitude-negative-max-score", type=float, default=45.0)
    parser.add_argument("--perspective-shear-min-score", type=float, default=70.0)
    parser.add_argument("--interhand-temporal-desync-min-score", type=float, default=70.0)
    parser.add_argument("--temporal-order-jitter-min-score", type=float, default=70.0)
    parser.add_argument("--finger-identity-jitter-min-score", type=float, default=70.0)
    parser.add_argument("--hand-scale-flicker-min-score", type=float, default=70.0)
    parser.add_argument("--hand-center-flicker-min-score", type=float, default=70.0)
    parser.add_argument("--global-framing-flicker-min-score", type=float, default=70.0)
    parser.add_argument("--finger-mid-joint-occlusion-min-score", type=float, default=70.0)
    parser.add_argument("--ghost-hand-duplicate-min-score", type=float, default=70.0)
    parser.add_argument("--hand-overlap-merge-min-score", type=float, default=70.0)
    parser.add_argument("--wrist-anchor-drift-min-score", type=float, default=70.0)
    parser.add_argument("--finger-chain-latency-min-score", type=float, default=70.0)
    parser.add_argument("--finger-fan-geometry-min-score", type=float, default=70.0)
    parser.add_argument("--finger-base-geometry-min-score", type=float, default=70.0)
    parser.add_argument("--finger-chain-confidence-min-score", type=float, default=70.0)
    parser.add_argument("--finger-chain-smoothing-min-score", type=float, default=70.0)
    parser.add_argument("--finite-coordinate-min-score", type=float, default=70.0)
    parser.add_argument("--bounded-coordinate-min-score", type=float, default=70.0)
    parser.add_argument("--flower-min-valid-frames", type=int, default=12)
    parser.add_argument("--jump-min-valid-frames", type=int, default=6)
    args = parser.parse_args(argv)

    payload = run_quality_gate(args)
    print(f"已生成花/跳统一质量门 JSON：{payload['json_path']}")
    print(f"已生成花/跳统一质量门报告：{payload['md_path']}")
    print(f"综合状态：{'PASS' if payload['passed'] else 'FAIL'}")
    for subgate in payload["subgates"]:
        print(f"- {subgate['name']}: {'PASS' if subgate['passed'] else 'FAIL'} returncode={subgate['returncode']}")
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

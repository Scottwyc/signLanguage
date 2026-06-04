#!/usr/bin/env python3
"""Stress-test flower/jump scoring against finite invalid coordinates.

MediaPipe/WebRTC may keep a hand landmark numerically finite even when the
point has drifted outside the camera frame. For hand and face landmarks this
should behave like a missing point; otherwise a single finite but impossible
tip coordinate, z-depth outlier, exact-zero placeholder, or degenerate collapsed
hand can dominate geometry and collapse or falsely lift an otherwise valid web
score. Pose landmarks are intentionally not bounded here because web samples
often contain out-of-frame hip/leg pose points that are irrelevant to hand
semantics.

This script writes mutated cached Holistic JSON fixtures under its output
directory, then reloads them through the normal ``load_sequence`` path. It does
not call /api/score, run Holistic, move the web marker, or restart 5080.
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import numpy as np

from run_flower_jump_finite_coordinate_robustness_gate import (
    _active_indices,
    _records,
    _result_finite,
    _sequence_finite_summary,
)
from run_flower_jump_landmark_noise_robustness_gate import _fmt, _json_default, _load_backend_status
from run_flower_jump_mirror_robustness_gate import _template_json
from score_holistic_sequence_mvp import (
    DEFAULT_SEMANTIC_PROFILE_JSON,
    HAND_DEGENERATE_VISIBLE_MIN_POINTS,
    HAND_DEGENERATE_XY_SPAN_MIN,
    LANDMARK_XY_VISIBLE_MAX,
    LANDMARK_XY_VISIBLE_MIN,
    LANDMARK_ZERO_MISSING_EPS,
    LANDMARK_Z_VISIBLE_MAX,
    LANDMARK_Z_VISIBLE_MIN,
    _profile_summary,
    load_semantic_profile,
    load_sequence,
    run_pair,
)


REPO_ROOT = Path("/data/WYC/signLanguage")
DEFAULT_TEMPLATE_ROOT = REPO_ROOT / "work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results"
DEFAULT_OUTPUT_BASE = REPO_ROOT / "work/generated/scoring_mvp_run3"
DEFAULT_BACKEND_URL = "http://127.0.0.1:5080"
DEFAULT_WORDS = ["花", "跳"]

OUTER_TIPS = [16, 20]
FACE_STABLE_RAW = [33, 133, 61, 291]
LEFT_GROUND_RAW = [0, 5, 9, 13, 17]


def _spec(
    variant: str,
    kind: str,
    *,
    pattern: str,
    mutations: Sequence[Dict[str, Any]],
    rationale: str,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    expected_quality_statuses: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    expected_statuses = [str(item) for item in (expected_quality_statuses or [])]
    return {
        "variant": variant,
        "kind": kind,
        "pattern": pattern,
        "mutations": [dict(item) for item in mutations],
        "min_score": min_score,
        "max_score": max_score,
        "expected_quality_statuses": expected_statuses,
        "gated": kind == "positive" or max_score is not None or bool(expected_statuses),
        "rationale": rationale,
    }


def _mut(group: str, indices: Sequence[int], axis_values: Dict[str, float]) -> Dict[str, Any]:
    return {
        "group": group,
        "indices": [int(item) for item in indices],
        "axis_values": {str(key): float(value) for key, value in axis_values.items()},
    }


def _mut_copy(group: str, indices: Sequence[int], source_index: int = 0) -> Dict[str, Any]:
    return {
        "group": group,
        "indices": [int(item) for item in indices],
        "copy_from_index": int(source_index),
        "axes": ["x", "y", "z"],
    }


def _mut_tiny_span(group: str, indices: Sequence[int], span: float, source_index: int = 0) -> Dict[str, Any]:
    return {
        "group": group,
        "indices": [int(item) for item in indices],
        "tiny_span": float(span),
        "source_index": int(source_index),
    }


def _variant_specs(word: str, min_score: float) -> List[Dict[str, Any]]:
    upper_x = LANDMARK_XY_VISIBLE_MAX + 0.05
    lower_x = LANDMARK_XY_VISIBLE_MIN - 0.05
    upper_y = LANDMARK_XY_VISIBLE_MAX + 0.05
    upper_z = LANDMARK_Z_VISIBLE_MAX + 4.0
    lower_z = LANDMARK_Z_VISIBLE_MIN - 4.0
    tiny_hand_span = HAND_DEGENERATE_XY_SPAN_MIN * 0.4
    specs = [
        _spec(
            "self_reloaded",
            "positive",
            pattern="none",
            mutations=[],
            min_score=95.0,
            rationale="原始标准 JSON 经正常 load_sequence 重载，应保持近满分且所有距离有限。",
        ),
        _spec(
            "face_core_sparse_out_of_frame",
            "positive",
            pattern="sparse_every_7f",
            mutations=[_mut("face_landmarks", FACE_STABLE_RAW, {"x": upper_x})],
            min_score=min_score,
            rationale="face core 稀疏有限越界点应被视为缺失，不能污染手部语义评分。",
        ),
        _spec(
            "face_core_sparse_z_outlier",
            "positive",
            pattern="sparse_every_7f",
            mutations=[_mut("face_landmarks", FACE_STABLE_RAW, {"z": upper_z})],
            min_score=min_score,
            rationale="face core 稀疏有限 z 离群点应被视为缺失，不能污染手部语义评分。",
        ),
        _spec(
            "face_core_sparse_zero_placeholder",
            "positive",
            pattern="sparse_every_7f",
            mutations=[_mut("face_landmarks", FACE_STABLE_RAW, {"x": 0.0, "y": 0.0, "z": 0.0})],
            min_score=min_score,
            rationale="face core 稀疏 exact-zero 占位点应被视为缺失，不能污染手部语义评分。",
        ),
    ]
    if word == "花":
        specs.extend(
            [
                _spec(
                    "flower_right_index_tip_single_out_of_frame",
                    "positive",
                    pattern="single_mid",
                    mutations=[_mut("right_hand_landmarks", [8], {"x": upper_x})],
                    min_score=min_score,
                    rationale="开花核心手单帧 index tip 有限越界应按该点缺失处理，完整开合证据仍应保留。",
                ),
                _spec(
                    "flower_right_index_middle_tip_single_z_outlier",
                    "positive",
                    pattern="single_mid",
                    mutations=[_mut("right_hand_landmarks", [8, 12], {"z": upper_z})],
                    min_score=min_score,
                    rationale="开花核心手单帧 index/middle tip 有限 z 离群应按局部缺失处理，不能把正确开合动作打成低分。",
                ),
                _spec(
                    "flower_right_index_middle_tip_single_zero_placeholder",
                    "positive",
                    pattern="single_mid",
                    mutations=[_mut("right_hand_landmarks", [8, 12], {"x": 0.0, "y": 0.0, "z": 0.0})],
                    min_score=min_score,
                    rationale="开花核心手单帧 index/middle tip exact-zero 占位点应按局部缺失处理。",
                ),
                _spec(
                    "flower_right_outer_tips_sparse_out_of_frame",
                    "positive",
                    pattern="sparse_every_5f",
                    mutations=[_mut("right_hand_landmarks", OUTER_TIPS, {"x": lower_x, "y": upper_y})],
                    min_score=min_score,
                    rationale="开花 ring/pinky 外侧指尖稀疏有限越界，应被局部 mask 掉。",
                ),
                _spec(
                    "flower_right_outer_tips_sparse_z_outlier",
                    "positive",
                    pattern="sparse_every_5f",
                    mutations=[_mut("right_hand_landmarks", OUTER_TIPS, {"z": lower_z})],
                    min_score=min_score,
                    rationale="开花 ring/pinky 外侧指尖稀疏有限 z 离群，应被局部 mask 掉。",
                ),
                _spec(
                    "flower_right_outer_tips_sparse_zero_placeholder",
                    "positive",
                    pattern="sparse_every_5f",
                    mutations=[_mut("right_hand_landmarks", OUTER_TIPS, {"x": 0.0, "y": 0.0, "z": 0.0})],
                    min_score=min_score,
                    rationale="开花 ring/pinky 外侧指尖稀疏 exact-zero 占位点，应被局部 mask 掉。",
                ),
                _spec(
                    "flower_right_core_hand_middle35_out_diagnostic",
                    "diagnostic",
                    pattern="middle_35pct",
                    mutations=[_mut("right_hand_landmarks", list(range(21)), {"x": upper_x})],
                    max_score=55.0,
                    expected_quality_statuses=["needs_recapture", "semantic_mismatch"],
                    rationale="诊断记录：开花核心手较长窗口整手出画面时应触发重采/低分边界。",
                ),
                _spec(
                    "flower_right_core_hand_middle35_z_outlier_diagnostic",
                    "diagnostic",
                    pattern="middle_35pct",
                    mutations=[_mut("right_hand_landmarks", list(range(21)), {"z": upper_z})],
                    max_score=55.0,
                    expected_quality_statuses=["needs_recapture", "semantic_mismatch"],
                    rationale="诊断记录：开花核心手较长窗口整手 z 离群应触发重采/低分边界。",
                ),
                _spec(
                    "flower_right_core_hand_middle35_zero_placeholder_diagnostic",
                    "diagnostic",
                    pattern="middle_35pct",
                    mutations=[_mut("right_hand_landmarks", list(range(21)), {"x": 0.0, "y": 0.0, "z": 0.0})],
                    max_score=55.0,
                    expected_quality_statuses=["needs_recapture", "semantic_mismatch"],
                    rationale="诊断记录：开花核心手较长窗口整手 exact-zero 占位应触发重采/低分边界。",
                ),
                _spec(
                    "flower_right_core_hand_middle35_duplicate_wrist_diagnostic",
                    "diagnostic",
                    pattern="middle_35pct",
                    mutations=[_mut_copy("right_hand_landmarks", list(range(21)), 0)],
                    max_score=55.0,
                    expected_quality_statuses=["needs_recapture", "semantic_mismatch"],
                    rationale="诊断记录：开花核心手较长窗口所有点塌缩到手腕时应触发重采/低分边界。",
                ),
                _spec(
                    "flower_right_core_hand_middle35_tiny_span_diagnostic",
                    "diagnostic",
                    pattern="middle_35pct",
                    mutations=[_mut_tiny_span("right_hand_landmarks", list(range(21)), tiny_hand_span, 0)],
                    max_score=55.0,
                    expected_quality_statuses=["needs_recapture", "semantic_mismatch"],
                    rationale="诊断记录：开花核心手较长窗口整手极小跨度塌缩时应触发重采/低分边界。",
                ),
            ]
        )
    elif word == "跳":
        specs.extend(
            [
                _spec(
                    "jump_right_person_tips_single_out_of_frame",
                    "positive",
                    pattern="single_mid",
                    mutations=[_mut("right_hand_landmarks", [8, 12], {"x": upper_x})],
                    min_score=min_score,
                    rationale="跳的右手两指单帧 tip 有限越界应按局部缺失处理，不应破坏完整弹跳轨迹。",
                ),
                _spec(
                    "jump_right_person_tips_single_z_outlier",
                    "positive",
                    pattern="single_mid",
                    mutations=[_mut("right_hand_landmarks", [8, 12], {"z": upper_z})],
                    min_score=min_score,
                    rationale="跳的右手两指单帧 tip 有限 z 离群应按局部缺失处理，不应破坏完整弹跳轨迹。",
                ),
                _spec(
                    "jump_right_person_tips_single_zero_placeholder",
                    "positive",
                    pattern="single_mid",
                    mutations=[_mut("right_hand_landmarks", [8, 12], {"x": 0.0, "y": 0.0, "z": 0.0})],
                    min_score=min_score,
                    rationale="跳的右手两指单帧 tip exact-zero 占位点应按局部缺失处理，不应破坏完整弹跳轨迹。",
                ),
                _spec(
                    "jump_left_ground_sparse_out_of_frame",
                    "positive",
                    pattern="sparse_every_7f",
                    mutations=[_mut("left_hand_landmarks", LEFT_GROUND_RAW, {"y": upper_y})],
                    min_score=min_score,
                    rationale="跳的左手地面手稀疏有限越界应按缺失处理，多数双手关系帧仍可评分。",
                ),
                _spec(
                    "jump_left_ground_sparse_z_outlier",
                    "positive",
                    pattern="sparse_every_7f",
                    mutations=[_mut("left_hand_landmarks", LEFT_GROUND_RAW, {"z": lower_z})],
                    min_score=min_score,
                    rationale="跳的左手地面手稀疏有限 z 离群应按缺失处理，多数双手关系帧仍可评分。",
                ),
                _spec(
                    "jump_left_ground_sparse_zero_placeholder",
                    "positive",
                    pattern="sparse_every_7f",
                    mutations=[_mut("left_hand_landmarks", LEFT_GROUND_RAW, {"x": 0.0, "y": 0.0, "z": 0.0})],
                    min_score=min_score,
                    rationale="跳的左手地面手稀疏 exact-zero 占位点应按缺失处理，多数双手关系帧仍可评分。",
                ),
                _spec(
                    "jump_right_core_hand_middle35_out_diagnostic",
                    "diagnostic",
                    pattern="middle_35pct",
                    mutations=[_mut("right_hand_landmarks", list(range(21)), {"x": upper_x, "y": upper_y})],
                    max_score=55.0,
                    expected_quality_statuses=["needs_recapture", "semantic_mismatch"],
                    rationale="诊断记录：右手小人较长窗口整手出画面时应触发重采/低分边界。",
                ),
                _spec(
                    "jump_right_core_hand_middle35_z_outlier_diagnostic",
                    "diagnostic",
                    pattern="middle_35pct",
                    mutations=[_mut("right_hand_landmarks", list(range(21)), {"z": upper_z})],
                    max_score=55.0,
                    expected_quality_statuses=["needs_recapture", "semantic_mismatch"],
                    rationale="诊断记录：右手小人较长窗口整手 z 离群应触发重采/低分边界。",
                ),
                _spec(
                    "jump_right_core_hand_middle35_zero_placeholder_diagnostic",
                    "diagnostic",
                    pattern="middle_35pct",
                    mutations=[_mut("right_hand_landmarks", list(range(21)), {"x": 0.0, "y": 0.0, "z": 0.0})],
                    max_score=55.0,
                    expected_quality_statuses=["needs_recapture", "semantic_mismatch"],
                    rationale="诊断记录：右手小人较长窗口整手 exact-zero 占位应触发重采/低分边界。",
                ),
                _spec(
                    "jump_right_core_hand_full_duplicate_wrist_diagnostic",
                    "diagnostic",
                    pattern="full",
                    mutations=[_mut_copy("right_hand_landmarks", list(range(21)), 0)],
                    max_score=55.0,
                    expected_quality_statuses=["needs_recapture", "semantic_mismatch"],
                    rationale="诊断记录：右手小人全程所有点塌缩到手腕时应触发重采/低分边界。",
                ),
                _spec(
                    "jump_right_core_hand_full_tiny_span_diagnostic",
                    "diagnostic",
                    pattern="full",
                    mutations=[_mut_tiny_span("right_hand_landmarks", list(range(21)), tiny_hand_span, 0)],
                    max_score=55.0,
                    expected_quality_statuses=["needs_recapture", "semantic_mismatch"],
                    rationale="诊断记录：右手小人全程整手极小跨度塌缩时应触发重采/低分边界。",
                ),
                _spec(
                    "jump_left_ground_hand_middle35_tiny_span_diagnostic",
                    "diagnostic",
                    pattern="middle_35pct",
                    mutations=[_mut_tiny_span("left_hand_landmarks", list(range(21)), tiny_hand_span, 0)],
                    max_score=55.0,
                    expected_quality_statuses=["needs_recapture", "semantic_mismatch"],
                    rationale="诊断记录：左手地面手较长窗口整手极小跨度塌缩时应触发重采/低分边界。",
                ),
            ]
        )
    return specs


def _write_mutated_json(source_json: Path, dest_json: Path, spec: Dict[str, Any]) -> Dict[str, Any]:
    payload = copy.deepcopy(json.loads(source_json.read_text(encoding="utf-8")))
    records = _records(payload)
    active = _active_indices(str(spec["pattern"]), len(records))
    changed_values = 0
    skipped_values = 0
    for frame_idx in active:
        record = records[frame_idx]
        result_data = record.get("result_data") or {}
        for mutation in spec["mutations"]:
            landmarks = result_data.get(str(mutation["group"])) or []
            if "tiny_span" in mutation:
                target_indices = [int(item) for item in mutation["indices"]]
                source_idx = int(mutation.get("source_index", 0))
                if not 0 <= source_idx < len(landmarks) or not isinstance(landmarks[source_idx], dict):
                    skipped_values += 3 * len(target_indices)
                    continue
                source_point = landmarks[source_idx]
                try:
                    center = {
                        "x": float(source_point.get("x", 0.0)),
                        "y": float(source_point.get("y", 0.0)),
                        "z": float(source_point.get("z", 0.0)),
                    }
                except (TypeError, ValueError):
                    skipped_values += 3 * len(target_indices)
                    continue
                span = float(mutation["tiny_span"])
                offsets: List[Dict[str, float]] = []
                for item_idx in range(len(target_indices)):
                    col = item_idx % 7
                    row = item_idx // 7
                    offsets.append(
                        {
                            "x": (col / 6.0 - 0.5) * span,
                            "y": (row / 2.0 - 0.5) * span,
                            "z": 0.0,
                        }
                    )
                for item_idx, landmark_idx in enumerate(target_indices):
                    if not 0 <= landmark_idx < len(landmarks) or not isinstance(landmarks[landmark_idx], dict):
                        skipped_values += 3
                        continue
                    point = landmarks[landmark_idx]
                    for axis in ["x", "y", "z"]:
                        point[axis] = center[axis] + offsets[item_idx][axis]
                        changed_values += 1
                continue
            axis_values = dict(mutation.get("axis_values") or {})
            if "copy_from_index" in mutation:
                axes = [str(item) for item in (mutation.get("axes") or ["x", "y", "z"])]
                source_idx = int(mutation["copy_from_index"])
                if not 0 <= source_idx < len(landmarks) or not isinstance(landmarks[source_idx], dict):
                    skipped_values += len(axes) * len(mutation["indices"])
                    continue
                source_point = landmarks[source_idx]
                try:
                    axis_values = {axis: float(source_point.get(axis, 0.0)) for axis in axes}
                except (TypeError, ValueError):
                    skipped_values += len(axes) * len(mutation["indices"])
                    continue
            for landmark_idx in mutation["indices"]:
                if not 0 <= int(landmark_idx) < len(landmarks):
                    skipped_values += len(axis_values)
                    continue
                point = landmarks[int(landmark_idx)]
                if not isinstance(point, dict):
                    skipped_values += len(axis_values)
                    continue
                for axis, value in axis_values.items():
                    point[str(axis)] = float(value)
                    changed_values += 1
    dest_json.parent.mkdir(parents=True, exist_ok=True)
    dest_json.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return {
        "active_frame_count": len(active),
        "changed_values": changed_values,
        "skipped_values": skipped_values,
        "total_records": len(records),
    }


def _row_passed(row: Dict[str, Any]) -> bool:
    if row.get("exception"):
        return False
    if not row.get("result_finite"):
        return False
    finite_summary = row.get("query_finite_summary") or {}
    if int(finite_summary.get("vector_nonfinite") or 0) != 0:
        return False
    if int(finite_summary.get("mask_nonfinite") or 0) != 0:
        return False
    score = float(row["score"])
    if row["kind"] == "positive":
        if score < float(row["min_score"]):
            return False
    if row.get("max_score") is not None and score > float(row["max_score"]):
        return False
    expected_statuses = {str(item) for item in (row.get("expected_quality_statuses") or [])}
    if expected_statuses:
        quality = row.get("capture_quality") or {}
        if str(quality.get("status") or "") not in expected_statuses:
            return False
    return True


def _run_word(
    word: str,
    template_root: Path,
    semantic_profile_json: Path,
    feature_mode: str,
    min_score: float,
    fixture_dir: Path,
) -> Dict[str, Any]:
    standard_json = _template_json(template_root, word)
    standard = load_sequence(standard_json, feature_mode, force_bbox=False, apply_sidecar_weights=False)
    profile = load_semantic_profile(word, semantic_profile_json)
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(word, min_score):
        fixture_json = fixture_dir / word / f"{spec['variant']}.json"
        mutation_detail = _write_mutated_json(standard_json, fixture_json, spec)
        row: Dict[str, Any] = {
            "variant": spec["variant"],
            "kind": spec["kind"],
            "gated": bool(spec["gated"]),
            "min_score": spec.get("min_score"),
            "pattern": spec["pattern"],
            "mutations": spec["mutations"],
            "fixture_json": str(fixture_json),
            "rationale": spec["rationale"],
            "max_score": spec.get("max_score"),
            "expected_quality_statuses": spec.get("expected_quality_statuses") or [],
            **mutation_detail,
        }
        try:
            query = load_sequence(fixture_json, feature_mode, force_bbox=False, apply_sidecar_weights=False)
            result = run_pair(standard, query, semantic_profile=profile, target_word=word, enable_cross_check=False)
        except Exception as exc:  # noqa: BLE001 - the gate reports loader/scorer crashes as failures.
            row.update(
                {
                    "exception": f"{type(exc).__name__}: {exc}",
                    "score": None,
                    "dtw_distance": None,
                    "normalized_distance": None,
                    "result_finite": False,
                    "query_finite_summary": {},
                }
            )
        else:
            row.update(
                {
                    "exception": "",
                    "score": float(result["prototype_score"]),
                    "dtw_distance": float(result["dtw_distance"]),
                    "normalized_distance": float(result["normalized_distance"]),
                    "result_finite": _result_finite(result),
                    "query_finite_summary": _sequence_finite_summary(query),
                    "alignment_policy": result.get("alignment_policy"),
                    "capture_quality": (result.get("score_scale") or {}).get("capture_quality"),
                    "semantic_floor": (result.get("score_scale") or {}).get("semantic_floor"),
                    "action_window": result.get("action_window"),
                }
            )
        row["passed"] = _row_passed(row)
        rows.append(row)
    positive_rows = [row for row in rows if row["kind"] == "positive" and row.get("score") is not None]
    diagnostic_rows = [row for row in rows if row["kind"] == "diagnostic" and row.get("score") is not None]
    weakest_positive = min(positive_rows, key=lambda row: float(row["score"])) if positive_rows else None
    weakest_diagnostic = min(diagnostic_rows, key=lambda row: float(row["score"])) if diagnostic_rows else None
    return {
        "word": word,
        "standard_json": str(standard_json),
        "standard_length": len(standard.features),
        "semantic_profile": _profile_summary(profile),
        "gate_pass": all(bool(row["passed"]) for row in rows),
        "weakest_positive_score": float(weakest_positive["score"]) if weakest_positive else None,
        "weakest_positive_variant": weakest_positive["variant"] if weakest_positive else "",
        "weakest_diagnostic_score": float(weakest_diagnostic["score"]) if weakest_diagnostic else None,
        "weakest_diagnostic_variant": weakest_diagnostic["variant"] if weakest_diagnostic else "",
        "min_required_score": min_score,
        "variants": rows,
    }


def _write_rows_csv(path: Path, results: Sequence[Dict[str, Any]]) -> None:
    fields = [
        "word",
        "variant",
        "kind",
        "gated",
        "passed",
        "score",
        "min_score",
        "max_score",
        "expected_quality_statuses",
        "dtw_distance",
        "normalized_distance",
        "result_finite",
        "vector_nonfinite",
        "mask_nonfinite",
        "zero_mask_values",
        "pattern",
        "active_frame_count",
        "changed_values",
        "skipped_values",
        "total_records",
        "fixture_json",
        "capture_quality_status",
        "capture_quality_reason",
        "semantic_floor_source",
        "semantic_floor_reason",
        "exception",
        "rationale",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in results:
            for row in item["variants"]:
                quality = row.get("capture_quality") or {}
                floor = row.get("semantic_floor") or {}
                finite_summary = row.get("query_finite_summary") or {}
                writer.writerow(
                    {
                        "word": item["word"],
                        "variant": row.get("variant"),
                        "kind": row.get("kind"),
                        "gated": row.get("gated"),
                        "passed": row.get("passed"),
                        "score": row.get("score"),
                        "min_score": row.get("min_score"),
                        "max_score": row.get("max_score"),
                        "expected_quality_statuses": ",".join(row.get("expected_quality_statuses") or []),
                        "dtw_distance": row.get("dtw_distance"),
                        "normalized_distance": row.get("normalized_distance"),
                        "result_finite": row.get("result_finite"),
                        "vector_nonfinite": finite_summary.get("vector_nonfinite"),
                        "mask_nonfinite": finite_summary.get("mask_nonfinite"),
                        "zero_mask_values": finite_summary.get("zero_mask_values"),
                        "pattern": row.get("pattern"),
                        "active_frame_count": row.get("active_frame_count"),
                        "changed_values": row.get("changed_values"),
                        "skipped_values": row.get("skipped_values"),
                        "total_records": row.get("total_records"),
                        "fixture_json": row.get("fixture_json"),
                        "capture_quality_status": quality.get("status"),
                        "capture_quality_reason": quality.get("reason"),
                        "semantic_floor_source": floor.get("source"),
                        "semantic_floor_reason": floor.get("reason"),
                        "exception": row.get("exception"),
                        "rationale": row.get("rationale"),
                    }
                )


def _build_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# 花/跳有限异常/退化坐标鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        f"- hand/face 可见坐标边界：x/y `[{payload['xy_visible_min']}, {payload['xy_visible_max']}]`，"
        f"z `[{payload['z_visible_min']}, {payload['z_visible_max']}]`；pose 不套边界，因为网页样本常有非语义 pose 点出画面。",
        f"- exact-zero 占位阈值：`{payload['zero_missing_eps']}`；整手退化检测：可见点数 `>= {payload['hand_degenerate_visible_min_points']}` 且 x/y 跨度 `<= {payload['hand_degenerate_xy_span_min']}`。",
        "- 口径：写入有限 out-of-frame、z-depth 离群、exact-zero 占位和整手极小跨度塌缩的临时 Holistic JSON fixture，再经正常 `load_sequence()` 和 `run_pair()` 评分；不调用 `/api/score`，不运行 Holistic，不移动 marker，不重启 5080。",
        "- 目标：手部/face 稀疏有限坏点被视为缺失点，DTW/normalized distance/score 必须保持有限；持续核心手越界、离群或塌缩必须低分或触发重采/语义失败诊断。",
        "",
    ]
    backend = payload.get("backend_status") or {}
    if backend.get("ok"):
        data = backend.get("payload") or {}
        worker = data.get("worker") or {}
        scoring = data.get("scoring_module") or {}
        process = worker.get("process") or {}
        lines.append(
            f"- 5080 状态：worker=`{worker.get('status')}`，pid=`{process.get('pid') or ((worker.get('ready_payload') or {}).get('pid'))}`，"
            f"reload_count=`{scoring.get('reload_count')}`，last_reload_error=`{scoring.get('last_reload_error')}`"
        )
    else:
        lines.append(f"- 5080 状态：读取失败 `{backend.get('error') or '-'}`")
    lines.extend(["", "## 结论", "", f"- 综合状态：`{'PASS' if payload['passed'] else 'FAIL'}`", ""])
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向越界点 | 诊断最低分 | 最弱诊断边界 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for item in payload["results"]:
        lines.append(
            f"| {item['word']} | {'PASS' if item['gate_pass'] else 'FAIL'} | "
            f"{_fmt(item['weakest_positive_score'])} | {item['weakest_positive_variant'] or '-'} | "
            f"{_fmt(item['weakest_diagnostic_score'])} | {item['weakest_diagnostic_variant'] or '-'} | "
            f"{_fmt(item['min_required_score'])} |"
        )
    lines.append("")
    lines.append("## 分项明细")
    for item in payload["results"]:
        lines.extend(["", f"### {item['word']}", "", f"- 标准序列：`{item['standard_json']}`", ""])
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | finite | vector/mask 非有限 | 改动值 | pattern | capture_quality | semantic_floor | 异常 | 说明 |")
        lines.append("|---|---|---|---:|---|---|---|---:|---|---|---|---|---|")
        for row in sorted(item["variants"], key=lambda value: (value["kind"], float(value["score"] if value.get("score") is not None else -1.0))):
            quality = row.get("capture_quality") or {}
            floor = row.get("semantic_floor") or {}
            finite_summary = row.get("query_finite_summary") or {}
            expected_statuses = row.get("expected_quality_statuses") or []
            if row["kind"] == "positive":
                threshold = f">= {row.get('min_score')}"
                status = "PASS" if row["passed"] else "FAIL"
            elif row.get("max_score") is not None:
                threshold = f"<= {row.get('max_score')}"
                if expected_statuses:
                    threshold += f"; quality in {','.join(expected_statuses)}"
                status = "PASS" if row["passed"] else "FAIL"
            else:
                threshold = "diagnostic"
                status = "DIAG" if row["passed"] else "FAIL"
            nonfinite = f"{finite_summary.get('vector_nonfinite', '-')}/{finite_summary.get('mask_nonfinite', '-')}"
            lines.append(
                f"| {row['variant']} | {row['kind']} | {status} | {_fmt(row.get('score'))} | "
                f"{threshold} | {row.get('result_finite')} | {nonfinite} | {row.get('changed_values')} | "
                f"{row.get('pattern')} | {quality.get('status') or '-'}:{quality.get('reason') or '-'} | "
                f"{floor.get('source') or '-'}:{floor.get('reason') or '-'} | {row.get('exception') or '-'} | "
                f"{row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 该门补充的是手部/face 有限异常和退化坐标的加载清洗，不替代 edge clipping、missing/mask、landmark spike 或 finite-coordinate 门。",
            "- out-of-frame、z-depth 离群、exact-zero 占位和整手极小跨度塌缩都不是有效动作证据；稀疏局部坏点应局部缺失，持续核心手退化应重采或人工复核。",
            "- 该门是缓存 JSON fixture 压力测试，不能替代正式 marker 后的真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run bounded-coordinate robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_bounded_coordinate_robustness_gate_current"))
    parser.add_argument("--words", nargs="+", default=DEFAULT_WORDS)
    parser.add_argument("--feature-mode", choices=["auto", "landmark", "bbox"], default="auto")
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--status-timeout-sec", type=float, default=3.0)
    parser.add_argument("--min-score", type=float, default=70.0)
    args = parser.parse_args(argv)

    template_root = Path(args.template_root)
    semantic_profile_json = Path(args.semantic_profile_json)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    fixture_dir = output_dir / "fixtures"
    results = [
        _run_word(
            word=word,
            template_root=template_root,
            semantic_profile_json=semantic_profile_json,
            feature_mode=args.feature_mode,
            min_score=args.min_score,
            fixture_dir=fixture_dir,
        )
        for word in args.words
    ]
    backend_status = _load_backend_status(args.backend_url, args.status_timeout_sec)
    passed = all(bool(item["gate_pass"]) for item in results)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "passed": passed,
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "feature_mode": args.feature_mode,
        "min_score": args.min_score,
        "xy_visible_min": LANDMARK_XY_VISIBLE_MIN,
        "xy_visible_max": LANDMARK_XY_VISIBLE_MAX,
        "z_visible_min": LANDMARK_Z_VISIBLE_MIN,
        "z_visible_max": LANDMARK_Z_VISIBLE_MAX,
        "zero_missing_eps": LANDMARK_ZERO_MISSING_EPS,
        "hand_degenerate_visible_min_points": HAND_DEGENERATE_VISIBLE_MIN_POINTS,
        "hand_degenerate_xy_span_min": HAND_DEGENERATE_XY_SPAN_MIN,
        "backend_status": backend_status,
        "results": results,
    }
    json_path = output_dir / "flower_jump_bounded_coordinate_robustness_gate.json"
    md_path = output_dir / "flower_jump_bounded_coordinate_robustness_gate.md"
    csv_path = output_dir / "flower_jump_bounded_coordinate_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)
    print(f"已生成有限越界坐标鲁棒性门 JSON：{json_path}")
    print(f"已生成有限越界坐标鲁棒性门报告：{md_path}")
    print(f"综合状态：{'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

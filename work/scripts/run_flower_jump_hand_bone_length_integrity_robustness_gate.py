#!/usr/bin/env python3
"""Stress-test impossible local hand bone shortening and elongation.

The gate edits cached Holistic JSON only. It does not call /api/score, run
Holistic, move the formal marker, or restart 5080.
"""

from __future__ import annotations

import argparse
import copy
import csv
import itertools
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import numpy as np

from run_flower_jump_hand_landmark_collision_robustness_gate import (
    HAND_GROUPS,
    QUANTIZATION_SPECS,
    _parse_hand,
    _quantize_hand,
)
from run_flower_jump_hand_wrist_identity_robustness_gate import _active_indices, _records
from run_flower_jump_landmark_noise_robustness_gate import _fmt, _json_default, _load_backend_status
from run_flower_jump_mirror_robustness_gate import _template_json
from score_holistic_sequence_mvp import (
    DEFAULT_SEMANTIC_PROFILE_JSON,
    HAND_BONE_LENGTH_PALM_REF_MIN,
    HAND_BONE_LENGTH_RATIO_MAX,
    HAND_BONE_LENGTH_RATIO_MIN,
    HAND_BONE_LENGTH_VISIBLE_MIN_POINTS,
    HAND_FINGER_CHAINS,
    HAND_LANDMARK_COUNT,
    LANDMARK_XY_VISIBLE_MAX,
    LANDMARK_XY_VISIBLE_MIN,
    LANDMARK_ZERO_MISSING_EPS,
    LANDMARK_Z_VISIBLE_MAX,
    LANDMARK_Z_VISIBLE_MIN,
    _hand_bone_length_integrity_metrics,
    _hand_global_quantization_signature,
    _landmark_array,
    _mask_degenerate_hand,
    _mask_hand_bone_length_corruption,
    _mask_hand_landmark_collisions,
    _mask_hand_wrist_identity_corruption,
    _profile_summary,
    load_semantic_profile,
    load_sequence,
    run_pair,
)


REPO_ROOT = Path("/data/WYC/signLanguage")
DEFAULT_TEMPLATE_ROOT = REPO_ROOT / "work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results"
DEFAULT_WEB_ROOT = REPO_ROOT / "work/generated/web_scoring_mvp"
DEFAULT_OUTPUT_BASE = REPO_ROOT / "work/generated/scoring_mvp_run3"
DEFAULT_BACKEND_URL = "http://127.0.0.1:5080"
DEFAULT_WORDS = ["花", "跳"]
SHORT_TARGET_RATIO = HAND_BONE_LENGTH_RATIO_MIN * 0.5
LONG_TARGET_RATIO = HAND_BONE_LENGTH_RATIO_MAX * 1.1
DISTAL_EDGES = ((3, 4), (7, 8), (11, 12), (15, 16), (19, 20))
PARTIAL_VISIBILITY_PATTERNS = {
    "single_missing": [(index,) for index in range(HAND_LANDMARK_COUNT)],
    "pair_missing": list(itertools.combinations(range(HAND_LANDMARK_COUNT), 2)),
    "common_multi_missing": [
        (4, 8, 12, 16, 20),
        (1, 5, 9, 13, 17),
        (2, 6, 10, 14, 18),
        (3, 7, 11, 15, 19),
        (4, 7, 11, 15, 19),
        (1, 2, 3, 4, 8),
        (5, 9, 13, 17),
        (0,),
    ],
}
QUANTIZED_PARTIAL_PATTERNS = [
    (4,),
    (4, 8),
    (4, 8, 12),
    (4, 8, 12, 16),
    (4, 8, 12, 16, 20),
]


def _palm_scale(hand: np.ndarray) -> float:
    refs = [float(np.linalg.norm(hand[index] - hand[0])) for index in (5, 9, 13, 17)]
    refs.append(float(np.linalg.norm(hand[5] - hand[17])))
    return float(np.median(np.asarray(refs, dtype=np.float32)))


def _bone_ratios(hand: np.ndarray) -> List[float]:
    scale = _palm_scale(hand)
    return [
        float(np.linalg.norm(hand[start] - hand[end]) / scale)
        for chain in HAND_FINGER_CHAINS
        for start, end in zip(chain[:-1], chain[1:])
    ]


def _pre_bone_hand(landmarks: Any) -> tuple[np.ndarray, np.ndarray]:
    hand, hand_mask = _landmark_array(
        landmarks,
        expected_count=HAND_LANDMARK_COUNT,
        required_input_count=HAND_LANDMARK_COUNT,
        xy_bounds=(LANDMARK_XY_VISIBLE_MIN, LANDMARK_XY_VISIBLE_MAX),
        z_bounds=(LANDMARK_Z_VISIBLE_MIN, LANDMARK_Z_VISIBLE_MAX),
        zero_missing_eps=LANDMARK_ZERO_MISSING_EPS,
    )
    hand, hand_mask = _mask_degenerate_hand(hand, hand_mask)
    hand, hand_mask = _mask_hand_wrist_identity_corruption(hand, hand_mask)
    hand, hand_mask = _mask_hand_landmark_collisions(hand, hand_mask)
    return _mask_degenerate_hand(hand, hand_mask)


def _audit_partial_visibility(normal_hands: Sequence[np.ndarray]) -> Dict[str, Any]:
    patterns: Dict[str, Any] = {}
    for name, missing_patterns in PARTIAL_VISIBILITY_PATTERNS.items():
        evaluated = 0
        skipped = 0
        violation_count = 0
        mask_violation_count = 0
        minimum_ratio = math.inf
        maximum_ratio = -math.inf
        for hand in normal_hands:
            for missing in missing_patterns:
                mask = np.ones(HAND_LANDMARK_COUNT, dtype=np.float32)
                mask[list(missing)] = 0.0
                metrics = _hand_bone_length_integrity_metrics(hand, mask)
                if metrics is None:
                    skipped += 1
                    continue
                evaluated += 1
                violation_count += int(bool(metrics["corrupted"]))
                if metrics.get("minimum_bone_length_ratio") is not None:
                    minimum_ratio = min(minimum_ratio, float(metrics["minimum_bone_length_ratio"]))
                if metrics.get("maximum_bone_length_ratio") is not None:
                    maximum_ratio = max(maximum_ratio, float(metrics["maximum_bone_length_ratio"]))
                _, masked = _mask_hand_bone_length_corruption(hand, mask)
                mask_violation_count += int(bool(np.any(masked != mask)))
        patterns[name] = {
            "pattern_count": len(missing_patterns),
            "evaluated_case_count": evaluated,
            "skipped_case_count": skipped,
            "violation_count": violation_count,
            "mask_violation_count": mask_violation_count,
            "minimum_bone_length_ratio": minimum_ratio if math.isfinite(minimum_ratio) else None,
            "maximum_bone_length_ratio": maximum_ratio if math.isfinite(maximum_ratio) else None,
            "passed": bool(evaluated > 0 and violation_count == 0 and mask_violation_count == 0),
        }
    return {
        "patterns": patterns,
        "passed": bool(patterns and all(bool(item["passed"]) for item in patterns.values())),
    }


def _audit_normal_bone_lengths(template_root: Path, web_root: Path) -> Dict[str, Any]:
    paths = sorted(set(template_root.rglob("*holistic_results.json")) | set(web_root.rglob("*holistic_results.json")))
    hand_frames = 0
    segment_count = 0
    violation_frames = 0
    short_segment_count = 0
    long_segment_count = 0
    raw_global_quantization_signature_frames = 0
    minimum_normal_ratio = math.inf
    maximum_normal_ratio = -math.inf
    normal_hands: List[np.ndarray] = []
    sanitized_visible_point_counts: Dict[int, int] = {}
    sanitized_evaluated_hand_frames = 0
    sanitized_violation_frames = 0
    quantized = {
        name: {
            "hand_frame_count": 0,
            "quantization_signature_violation_count": 0,
            "would_violate_without_bypass_count": 0,
            "quantization_bypass_violation_count": 0,
        }
        for name in QUANTIZATION_SPECS
    }
    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 - malformed files are covered by the structural gate.
            continue
        records = payload.get("records") or payload.get("frames") or payload.get("rows") or []
        if not isinstance(records, list):
            continue
        for record in records:
            if not isinstance(record, dict):
                continue
            result_data = record.get("result_data") if isinstance(record.get("result_data"), dict) else record
            for group in HAND_GROUPS:
                hand = _parse_hand(result_data.get(group) if isinstance(result_data, dict) else None)
                if hand is None:
                    continue
                normal_hands.append(hand)
                mask = np.ones(21, dtype=np.float32)
                metrics = _hand_bone_length_integrity_metrics(hand, mask) or {}
                ratios = _bone_ratios(hand)
                hand_frames += 1
                segment_count += len(ratios)
                minimum_normal_ratio = min(minimum_normal_ratio, min(ratios))
                maximum_normal_ratio = max(maximum_normal_ratio, max(ratios))
                short_segment_count += sum(value < HAND_BONE_LENGTH_RATIO_MIN for value in ratios)
                long_segment_count += sum(value > HAND_BONE_LENGTH_RATIO_MAX for value in ratios)
                violation_frames += int(bool(metrics.get("corrupted")))
                raw_global_quantization_signature_frames += int(
                    _hand_global_quantization_signature(hand, mask) is not None
                )
                sanitized_hand, sanitized_mask = _pre_bone_hand(
                    result_data.get(group) if isinstance(result_data, dict) else None
                )
                visible_count = int(np.sum(sanitized_mask > 0))
                sanitized_visible_point_counts[visible_count] = (
                    sanitized_visible_point_counts.get(visible_count, 0) + 1
                )
                sanitized_metrics = _hand_bone_length_integrity_metrics(sanitized_hand, sanitized_mask)
                if sanitized_metrics is not None:
                    sanitized_evaluated_hand_frames += 1
                    sanitized_violation_frames += int(bool(sanitized_metrics["corrupted"]))
                for name, steps in QUANTIZATION_SPECS.items():
                    candidate = _quantize_hand(hand, steps)
                    item = quantized[name]
                    item["hand_frame_count"] += 1
                    candidate_metrics = _hand_bone_length_integrity_metrics(candidate, mask) or {}
                    item["quantization_signature_violation_count"] += int(
                        candidate_metrics.get("global_quantization_signature") is None
                    )
                    candidate_ratios = _bone_ratios(candidate)
                    item["would_violate_without_bypass_count"] += int(
                        any(
                            value < HAND_BONE_LENGTH_RATIO_MIN or value > HAND_BONE_LENGTH_RATIO_MAX
                            for value in candidate_ratios
                        )
                    )
                    _, masked = _mask_hand_bone_length_corruption(candidate, mask)
                    item["quantization_bypass_violation_count"] += int(bool(np.any(masked <= 0)))
                    for missing in QUANTIZED_PARTIAL_PATTERNS:
                        partial_mask = mask.copy()
                        partial_mask[list(missing)] = 0.0
                        partial_metrics = _hand_bone_length_integrity_metrics(candidate, partial_mask) or {}
                        item.setdefault("partial_quantization_signature_violation_count", 0)
                        item.setdefault("partial_quantization_bypass_violation_count", 0)
                        item["partial_quantization_signature_violation_count"] += int(
                            partial_metrics.get("global_quantization_signature") is None
                        )
                        _, partial_masked = _mask_hand_bone_length_corruption(candidate, partial_mask)
                        item["partial_quantization_bypass_violation_count"] += int(
                            bool(np.any(partial_masked != partial_mask))
                        )
    partial_visibility_audit = _audit_partial_visibility(normal_hands)
    quantized_passed = all(
        int(item["quantization_signature_violation_count"]) == 0
        and int(item["quantization_bypass_violation_count"]) == 0
        and int(item.get("partial_quantization_signature_violation_count") or 0) == 0
        and int(item.get("partial_quantization_bypass_violation_count") or 0) == 0
        for item in quantized.values()
    )
    return {
        "file_count": len(paths),
        "hand_frame_count": hand_frames,
        "segment_count": segment_count,
        "violation_frame_count": violation_frames,
        "short_segment_count": short_segment_count,
        "long_segment_count": long_segment_count,
        "raw_global_quantization_signature_frame_count": raw_global_quantization_signature_frames,
        "sanitized_visible_point_counts": sanitized_visible_point_counts,
        "sanitized_evaluated_hand_frame_count": sanitized_evaluated_hand_frames,
        "sanitized_violation_frame_count": sanitized_violation_frames,
        "minimum_normal_bone_length_ratio": (
            minimum_normal_ratio if math.isfinite(minimum_normal_ratio) else None
        ),
        "maximum_normal_bone_length_ratio": (
            maximum_normal_ratio if math.isfinite(maximum_normal_ratio) else None
        ),
        "partial_visibility_audit": partial_visibility_audit,
        "quantized": quantized,
        "passed": bool(
            hand_frames > 0
            and segment_count > 0
            and violation_frames == 0
            and short_segment_count == 0
            and long_segment_count == 0
            and raw_global_quantization_signature_frames == 0
            and sanitized_violation_frames == 0
            and minimum_normal_ratio >= HAND_BONE_LENGTH_RATIO_MIN
            and maximum_normal_ratio <= HAND_BONE_LENGTH_RATIO_MAX
            and partial_visibility_audit["passed"]
            and quantized_passed
        ),
    }


def _spec(
    variant: str,
    group: str,
    pattern: str,
    operation: str,
    kind: str,
    threshold: float,
    expect_masked: bool,
    rationale: str,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "group": group,
        "presence_group": HAND_GROUPS[group],
        "pattern": pattern,
        "operation": operation,
        "kind": kind,
        "gated": True,
        "threshold": threshold,
        "expect_masked": expect_masked,
        "rationale": rationale,
    }


def _variant_specs(word: str, sparse_min_score: float, diagnostic_max_score: float) -> List[Dict[str, Any]]:
    specs: List[Dict[str, Any]] = [
        {
            "variant": "self_reloaded",
            "group": "",
            "presence_group": "",
            "pattern": "none",
            "operation": "none",
            "kind": "positive",
            "gated": True,
            "threshold": 95.0,
            "expect_masked": False,
            "rationale": "原始标准 JSON 重载后应保持近满分。",
        }
    ]
    groups = ["right_hand_landmarks"]
    if word == "跳":
        groups.append("left_hand_landmarks")
    for group in groups:
        specs.extend(
            [
                _spec(
                    f"{group}_all_edges_short_sparse_preserved",
                    group,
                    "sparse_visible",
                    "all_edges_short",
                    "positive",
                    sparse_min_score,
                    True,
                    "稀疏极短骨段应局部屏蔽，正确动作其余帧仍应可评分。",
                ),
                _spec(
                    f"{group}_all_edges_short_full_recapture",
                    group,
                    "full_visible",
                    "all_edges_short",
                    "diagnostic",
                    diagnostic_max_score,
                    True,
                    "整段核心手极短骨段必须要求重采，不能继续给高分。",
                ),
                _spec(
                    f"{group}_all_distal_long_sparse_preserved",
                    group,
                    "sparse_visible",
                    "all_distal_long",
                    "positive",
                    sparse_min_score,
                    True,
                    "稀疏极长远端骨段应局部屏蔽，正确动作其余帧仍应可评分。",
                ),
                _spec(
                    f"{group}_all_distal_long_full_recapture",
                    group,
                    "full_visible",
                    "all_distal_long",
                    "positive" if word == "跳" and group == "left_hand_landmarks" else "diagnostic",
                    75.0 if word == "跳" and group == "left_hand_landmarks" else diagnostic_max_score,
                    True,
                    (
                        "跳的左手近端关系锚点仍完整，远端异常局部屏蔽后应继续评分。"
                        if word == "跳" and group == "left_hand_landmarks"
                        else "整段核心手极长远端骨段不能继续给高分。"
                    ),
                ),
                _spec(
                    f"{group}_single_index_tip_short_sparse_preserved",
                    group,
                    "sparse_visible",
                    "single_index_tip_short",
                    "positive",
                    70.0,
                    True,
                    "单条极短骨段只屏蔽局部歧义点。",
                ),
                _spec(
                    f"{group}_xyz_1_256_quantized_preserved",
                    group,
                    "full_visible",
                    "quantize_xyz_1_256",
                    "positive",
                    70.0,
                    False,
                    "完整全局量化手即使产生零长度骨段也必须旁路并保留。",
                ),
            ]
        )
        if group == "right_hand_landmarks":
            specs.append(
                _spec(
                    f"{group}_all_distal_long_plus_thumb_tip_out_of_bounds_full_recapture",
                    group,
                    "full_visible",
                    "all_distal_long_plus_thumb_tip_out_of_bounds",
                    "diagnostic",
                    diagnostic_max_score,
                    True,
                    "一个无关点先被清洗为缺失时，其余极长骨段仍必须被部分手规则屏蔽。",
                )
            )
    return specs


def _set_item(item: Dict[str, Any], point: np.ndarray) -> None:
    for axis, value in zip(("x", "y", "z"), point):
        item[axis] = float(value)


def _shorten_edge(points: np.ndarray, start: int, end: int, target_length: float) -> None:
    vector = points[end] - points[start]
    norm = float(np.linalg.norm(vector))
    direction = vector / norm if norm > 1e-12 else np.asarray([1.0, 0.0, 0.0], dtype=np.float32)
    points[end] = points[start] + direction * target_length


def _elongate_edge(points: np.ndarray, start: int, end: int, target_length: float) -> None:
    direction = 1.0 if float(points[start, 2]) <= 0.0 else -1.0
    points[end] = points[start]
    points[end, 2] = points[start, 2] + direction * target_length


def _mutate_array(landmarks: List[Any], operation: str) -> None:
    hand = _parse_hand(landmarks)
    if hand is None:
        return
    scale = _palm_scale(hand)
    if operation == "all_edges_short":
        target = scale * SHORT_TARGET_RATIO
        for chain in HAND_FINGER_CHAINS:
            direction = np.asarray([1.0, 0.0, 0.0], dtype=np.float32)
            for start, end in zip(chain[:-1], chain[1:]):
                hand[end] = hand[start] + direction * target
    elif operation == "all_distal_long":
        target = scale * LONG_TARGET_RATIO
        for start, end in DISTAL_EDGES:
            _elongate_edge(hand, start, end, target)
    elif operation == "all_distal_long_plus_thumb_tip_out_of_bounds":
        target = scale * LONG_TARGET_RATIO
        for start, end in DISTAL_EDGES:
            _elongate_edge(hand, start, end, target)
        hand[4, 0] = LANDMARK_XY_VISIBLE_MAX + 1.0
    elif operation == "single_index_tip_short":
        _shorten_edge(hand, 7, 8, scale * SHORT_TARGET_RATIO)
    elif operation.startswith("quantize_"):
        name = operation.removeprefix("quantize_")
        hand = _quantize_hand(hand, QUANTIZATION_SPECS[name])
    elif operation != "none":
        raise ValueError(f"unknown hand bone length operation: {operation}")
    for item, point in zip(landmarks, hand):
        if isinstance(item, dict):
            _set_item(item, point)


def _write_fixture(source_json: Path, dest_json: Path, spec: Dict[str, Any]) -> Dict[str, Any]:
    payload = copy.deepcopy(json.loads(source_json.read_text(encoding="utf-8")))
    records = _records(payload)
    active = _active_indices(records, str(spec["group"]), str(spec["pattern"])) if spec["group"] else []
    expected_indices: Dict[int, List[int]] = {}
    expected_preserved_indices: Dict[int, List[int]] = {}
    minimum_ratios: List[float] = []
    maximum_ratios: List[float] = []
    short_counts: List[int] = []
    long_counts: List[int] = []
    quantization_bypassed = 0
    for index in active:
        record = records[index]
        result_data = record.get("result_data") if isinstance(record, dict) else None
        landmarks = result_data.get(spec["group"]) if isinstance(result_data, dict) else None
        if not isinstance(landmarks, list) or len(landmarks) != 21:
            continue
        _mutate_array(landmarks, str(spec["operation"]))
        hand, hand_mask = _pre_bone_hand(landmarks)
        metrics = _hand_bone_length_integrity_metrics(hand, hand_mask) or {}
        indices = [int(item) for item in metrics.get("corrupted_indices") or []]
        if indices:
            expected_indices[index] = indices
        if bool(metrics.get("quantization_bypassed")):
            quantization_bypassed += 1
            expected_preserved_indices[index] = list(range(21))
        if metrics.get("minimum_bone_length_ratio") is not None:
            minimum_ratios.append(float(metrics["minimum_bone_length_ratio"]))
        if metrics.get("maximum_bone_length_ratio") is not None:
            maximum_ratios.append(float(metrics["maximum_bone_length_ratio"]))
        short_counts.append(int(metrics.get("short_edge_count") or 0))
        long_counts.append(int(metrics.get("long_edge_count") or 0))
    dest_json.parent.mkdir(parents=True, exist_ok=True)
    dest_json.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return {
        "active_indices": active,
        "changed_frame_count": len(short_counts),
        "corrupted_frame_count": len(expected_indices),
        "quantization_bypassed_frame_count": quantization_bypassed,
        "minimum_bone_length_ratio": min(minimum_ratios) if minimum_ratios else None,
        "maximum_bone_length_ratio": max(maximum_ratios) if maximum_ratios else None,
        "short_edge_count_min": min(short_counts) if short_counts else None,
        "short_edge_count_max": max(short_counts) if short_counts else None,
        "long_edge_count_min": min(long_counts) if long_counts else None,
        "long_edge_count_max": max(long_counts) if long_counts else None,
        "expected_corrupted_indices": expected_indices,
        "expected_preserved_indices": expected_preserved_indices,
        "total_records": len(records),
    }


def _mask_handling(
    query: Any,
    presence_group: str,
    expected_corrupted_indices: Dict[int, List[int]],
    expected_preserved_indices: Dict[int, List[int]],
) -> Dict[str, Any]:
    checked = 0
    handled = 0
    minimum_remaining = 21
    for raw_index, indices in expected_corrupted_indices.items():
        index = int(raw_index)
        if index >= len(query.features):
            continue
        group_slice = query.features[index].groups.get(presence_group)
        if group_slice is None:
            continue
        point_mask = query.features[index].mask[group_slice].reshape(-1, 3).mean(axis=1) > 0.5
        checked += 1
        handled += int(all(not bool(point_mask[item]) for item in indices))
        minimum_remaining = min(minimum_remaining, int(point_mask.sum()))
    for raw_index, indices in expected_preserved_indices.items():
        index = int(raw_index)
        if index >= len(query.features):
            continue
        group_slice = query.features[index].groups.get(presence_group)
        if group_slice is None:
            continue
        point_mask = query.features[index].mask[group_slice].reshape(-1, 3).mean(axis=1) > 0.5
        checked += 1
        handled += int(all(bool(point_mask[item]) for item in indices))
        minimum_remaining = min(minimum_remaining, int(point_mask.sum()))
    expected = len(expected_corrupted_indices) + len(expected_preserved_indices)
    return {
        "frames_checked": checked,
        "frames_handled": handled,
        "handling_rate": handled / checked if checked else 1.0,
        "minimum_remaining_point_count": minimum_remaining if checked else None,
        "passed": bool(checked == expected and handled == checked),
    }


def _finite(value: Any) -> bool:
    if isinstance(value, dict):
        return all(_finite(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_finite(item) for item in value)
    if isinstance(value, (int, float, np.number)):
        return math.isfinite(float(value))
    return True


def _run_word(
    word: str,
    template_root: Path,
    semantic_profile_json: Path,
    feature_mode: str,
    sparse_min_score: float,
    diagnostic_max_score: float,
    fixture_dir: Path,
) -> Dict[str, Any]:
    standard_json = _template_json(template_root, word)
    standard = load_sequence(standard_json, feature_mode, force_bbox=False, apply_sidecar_weights=False)
    profile = load_semantic_profile(word, semantic_profile_json)
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(word, sparse_min_score, diagnostic_max_score):
        fixture_json = fixture_dir / word / f"{spec['variant']}.json"
        detail = _write_fixture(standard_json, fixture_json, spec)
        row: Dict[str, Any] = {**spec, "fixture_json": str(fixture_json), **detail}
        try:
            query = load_sequence(fixture_json, feature_mode, force_bbox=False, apply_sidecar_weights=False)
            result = run_pair(standard, query, semantic_profile=profile, target_word=word, enable_cross_check=False)
        except Exception as exc:  # noqa: BLE001 - loader/scorer crashes are gate failures.
            row.update(
                {
                    "exception": f"{type(exc).__name__}: {exc}",
                    "score": None,
                    "mask_handling": {},
                    "capture_quality": {},
                    "passed": False,
                }
            )
        else:
            handling = (
                _mask_handling(
                    query,
                    str(spec["presence_group"]),
                    detail["expected_corrupted_indices"],
                    detail["expected_preserved_indices"],
                )
                if spec["group"]
                else {"passed": True}
            )
            score = float(result["prototype_score"])
            capture_quality = (result.get("score_scale") or {}).get("capture_quality") or {}
            result_finite = _finite(result)
            if spec["kind"] == "diagnostic":
                score_ok = score <= float(spec["threshold"])
                semantic_ok = capture_quality.get("status") in {"needs_recapture", "semantic_mismatch"}
            else:
                score_ok = score >= float(spec["threshold"])
                semantic_ok = True
            row.update(
                {
                    "exception": "",
                    "score": score,
                    "dtw_distance": float(result["dtw_distance"]),
                    "normalized_distance": float(result["normalized_distance"]),
                    "result_finite": result_finite,
                    "mask_handling": handling,
                    "capture_quality": capture_quality,
                    "passed": bool(result_finite and handling["passed"] and score_ok and semantic_ok),
                }
            )
        rows.append(row)
    positives = [row for row in rows if row["kind"] == "positive" and row.get("score") is not None]
    diagnostics = [row for row in rows if row["kind"] == "diagnostic" and row.get("score") is not None]
    weakest = min(positives, key=lambda row: float(row["score"])) if positives else None
    strongest_diagnostic = max(diagnostics, key=lambda row: float(row["score"])) if diagnostics else None
    return {
        "word": word,
        "standard_json": str(standard_json),
        "standard_length": len(standard.features),
        "semantic_profile": _profile_summary(profile),
        "gate_pass": all(bool(row["passed"]) for row in rows),
        "weakest_positive_score": float(weakest["score"]) if weakest else None,
        "weakest_positive_variant": weakest["variant"] if weakest else "",
        "strongest_diagnostic_score": float(strongest_diagnostic["score"]) if strongest_diagnostic else None,
        "strongest_diagnostic_variant": strongest_diagnostic["variant"] if strongest_diagnostic else "",
        "sparse_min_required_score": sparse_min_score,
        "diagnostic_max_score": diagnostic_max_score,
        "variants": rows,
    }


def _write_rows_csv(path: Path, results: Sequence[Dict[str, Any]]) -> None:
    fields = [
        "word",
        "variant",
        "kind",
        "passed",
        "score",
        "threshold",
        "group",
        "pattern",
        "operation",
        "corrupted_frame_count",
        "quantization_bypassed_frame_count",
        "minimum_bone_length_ratio",
        "maximum_bone_length_ratio",
        "handling_rate",
        "minimum_remaining_point_count",
        "capture_quality",
        "capture_reason",
        "exception",
    ]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for item in results:
            for row in item["variants"]:
                quality = row.get("capture_quality") or {}
                handling = row.get("mask_handling") or {}
                writer.writerow(
                    {
                        "word": item["word"],
                        "variant": row.get("variant"),
                        "kind": row.get("kind"),
                        "passed": row.get("passed"),
                        "score": row.get("score"),
                        "threshold": row.get("threshold"),
                        "group": row.get("group"),
                        "pattern": row.get("pattern"),
                        "operation": row.get("operation"),
                        "corrupted_frame_count": row.get("corrupted_frame_count"),
                        "quantization_bypassed_frame_count": row.get("quantization_bypassed_frame_count"),
                        "minimum_bone_length_ratio": row.get("minimum_bone_length_ratio"),
                        "maximum_bone_length_ratio": row.get("maximum_bone_length_ratio"),
                        "handling_rate": handling.get("handling_rate"),
                        "minimum_remaining_point_count": handling.get("minimum_remaining_point_count"),
                        "capture_quality": quality.get("status"),
                        "capture_reason": quality.get("reason"),
                        "exception": row.get("exception"),
                    }
                )


def _build_markdown(payload: Dict[str, Any]) -> str:
    audit = payload["normal_bone_length_audit"]
    lines = [
        "# 花/跳 Hand 骨段长度完整性鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        (
        f"- 保守边界：相邻指骨长度 / 掌尺度必须在 `[{payload['bone_length_ratio_min']}, "
            f"{payload['bone_length_ratio_max']}]`；至少 `{payload['bone_length_visible_min_points']}` 个可见点、"
            f"wrist 可见且至少 `{payload['bone_length_palm_ref_min']}` 个掌参考时，按 median 掌尺度只屏蔽异常骨段参与点。"
        ),
        (
            f"- 正常证据审计：`{audit['file_count']}` 个模板/网页 JSON、`{audit['hand_frame_count']}` 个完整手帧、"
            f"`{audit['segment_count']}` 条骨段，违反帧 `{audit['violation_frame_count']}`，"
            f"正常范围 `{audit['minimum_normal_bone_length_ratio']}`–`{audit['maximum_normal_bone_length_ratio']}`。"
        ),
        f"- 部分可见手零误伤审计：`{audit['partial_visibility_audit']}`。",
        (
            f"- 全局量化兼容：原始误命中 `{audit['raw_global_quantization_signature_frame_count']}`；"
            f"量化审计 `{audit['quantized']}`。"
        ),
        "- 口径：只写缓存 Holistic JSON fixture；不调用 `/api/score`、不运行 Holistic、不移动 marker、不重启 5080。",
        "",
        "## 结论",
        "",
        f"- 综合状态：`{'PASS' if payload['passed'] else 'FAIL'}`",
        "",
        "| 目标词 | 状态 | 正向最低分 | 最弱正向变体 | 整段损坏诊断最高分 | 最强诊断变体 |",
        "|---|---|---:|---|---:|---|",
    ]
    for item in payload["results"]:
        lines.append(
            f"| {item['word']} | {'PASS' if item['gate_pass'] else 'FAIL'} | "
            f"{_fmt(item['weakest_positive_score'])} | {item['weakest_positive_variant']} | "
            f"{_fmt(item['strongest_diagnostic_score'])} | {item['strongest_diagnostic_variant']} |"
        )
    lines.extend(["", "## 分项明细", ""])
    for item in payload["results"]:
        lines.extend(
            [
                f"### {item['word']}",
                "",
                "| 变体 | 类型 | 状态 | 分数 | 阈值 | 损坏帧 | 量化旁路帧 | 最短比 | 最长比 | 处理率 | 最少剩余点 | capture_quality |",
                "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
            ]
        )
        for row in item["variants"]:
            quality = row.get("capture_quality") or {}
            handling = row.get("mask_handling") or {}
            lines.append(
                f"| {row['variant']} | {row['kind']} | {'PASS' if row['passed'] else 'FAIL'} | "
                f"{_fmt(row.get('score'))} | {_fmt(row.get('threshold'))} | {row.get('corrupted_frame_count')} | "
                f"{row.get('quantization_bypassed_frame_count')} | {_fmt(row.get('minimum_bone_length_ratio'))} | "
                f"{_fmt(row.get('maximum_bone_length_ratio'))} | {_fmt(handling.get('handling_rate'))} | "
                f"{handling.get('minimum_remaining_point_count')} | "
                f"{quality.get('status') or '-'}:{quality.get('reason') or '-'} |"
            )
        lines.append("")
    lines.extend(
        [
            "## 说明",
            "",
            "- 该规则只处理远离正常证据范围的极端局部伸缩；轻微 finger-length 风格变化继续由现有鲁棒性门覆盖。",
            "- 至少 16 点可见的完整/部分全局量化手直接旁路，避免把坐标精度造成的零长度骨段误判为 tracker 损坏。",
            "- 该门补充 landmark 碰撞和内部拓扑门，不替代正式 marker 后真实网页摄像头复测。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run hand bone length integrity robustness gate.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--web-root", default=str(DEFAULT_WEB_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_BASE / "flower_jump_hand_bone_length_integrity_robustness_gate_current"),
    )
    parser.add_argument("--words", nargs="+", default=DEFAULT_WORDS)
    parser.add_argument("--feature-mode", choices=["auto", "landmark"], default="auto")
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--status-timeout-sec", type=float, default=3.0)
    parser.add_argument("--sparse-min-score", type=float, default=75.0)
    parser.add_argument("--diagnostic-max-score", type=float, default=55.0)
    args = parser.parse_args(argv)

    template_root = Path(args.template_root)
    web_root = Path(args.web_root)
    semantic_profile_json = Path(args.semantic_profile_json)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    results = [
        _run_word(
            word,
            template_root,
            semantic_profile_json,
            args.feature_mode,
            args.sparse_min_score,
            args.diagnostic_max_score,
            output_dir / "fixtures",
        )
        for word in args.words
    ]
    normal_bone_length_audit = _audit_normal_bone_lengths(template_root, web_root)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "claim_policy": "synthetic hand-bone-length-integrity robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "web_root": str(web_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": _load_backend_status(args.backend_url, args.status_timeout_sec),
        "bone_length_ratio_min": HAND_BONE_LENGTH_RATIO_MIN,
        "bone_length_ratio_max": HAND_BONE_LENGTH_RATIO_MAX,
        "bone_length_visible_min_points": HAND_BONE_LENGTH_VISIBLE_MIN_POINTS,
        "bone_length_palm_ref_min": HAND_BONE_LENGTH_PALM_REF_MIN,
        "short_target_ratio": SHORT_TARGET_RATIO,
        "long_target_ratio": LONG_TARGET_RATIO,
        "normal_bone_length_audit": normal_bone_length_audit,
        "sparse_min_score": args.sparse_min_score,
        "diagnostic_max_score": args.diagnostic_max_score,
        "results": results,
        "passed": bool(normal_bone_length_audit["passed"] and all(bool(item["gate_pass"]) for item in results)),
    }

    json_path = output_dir / "flower_jump_hand_bone_length_integrity_robustness_gate.json"
    md_path = output_dir / "flower_jump_hand_bone_length_integrity_robustness_gate.md"
    csv_path = output_dir / "flower_jump_hand_bone_length_integrity_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成 Hand 骨段长度完整性 JSON：{json_path}")
    print(f"已生成 Hand 骨段长度完整性报告：{md_path}")
    print(f"综合状态：{'PASS' if payload['passed'] else 'FAIL'}")
    for item in results:
        print(
            f"- {item['word']}: {'PASS' if item['gate_pass'] else 'FAIL'} "
            f"positive_min={_fmt(item['weakest_positive_score'])} "
            f"diagnostic_max={_fmt(item['strongest_diagnostic_score'])}"
        )
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

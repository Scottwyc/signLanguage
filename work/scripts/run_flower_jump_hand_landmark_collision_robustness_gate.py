#!/usr/bin/env python3
"""Stress-test duplicate and near-duplicate landmarks within one hand.

The gate edits cached Holistic JSON only. It does not call /api/score, run
Holistic, move the formal marker, or restart 5080.
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

from run_flower_jump_hand_wrist_identity_robustness_gate import _active_indices, _records
from run_flower_jump_landmark_noise_robustness_gate import _fmt, _json_default, _load_backend_status
from run_flower_jump_mirror_robustness_gate import _template_json
from score_holistic_sequence_mvp import (
    DEFAULT_SEMANTIC_PROFILE_JSON,
    HAND_GLOBAL_QUANTIZATION_RESIDUAL_MAX,
    HAND_GLOBAL_QUANTIZATION_STEPS,
    HAND_LANDMARK_COLLISION_DISTANCE_MAX,
    _hand_global_quantization_signature,
    _hand_landmark_collision_metrics,
    _mask_hand_landmark_collisions,
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
HAND_GROUPS = {
    "left_hand_landmarks": "left_hand",
    "right_hand_landmarks": "right_hand",
}
SEVERE_COLLISION_OPERATIONS = [
    "tip_to_dip_all",
    "dip_tip_to_pip_all",
    "distal_to_mcp_all",
    "index_middle_to_index_mcp",
]
CLUSTER_COLLISION_OPERATIONS = [
    "all_tips_to_wrist",
    "all_mcps_to_wrist",
]
QUANTIZATION_SPECS = {
    "camera_640x480_z1024": (1.0 / 640.0, 1.0 / 480.0, 1.0 / 1024.0),
    "camera_320x240_z512": (1.0 / 320.0, 1.0 / 240.0, 1.0 / 512.0),
    "xyz_1_256": (1.0 / 256.0, 1.0 / 256.0, 1.0 / 256.0),
}


def _parse_hand(landmarks: Any) -> Optional[np.ndarray]:
    if not isinstance(landmarks, list) or len(landmarks) != 21:
        return None
    try:
        hand = np.asarray(
            [[float(item["x"]), float(item["y"]), float(item["z"])] for item in landmarks],
            dtype=np.float32,
        )
    except (KeyError, TypeError, ValueError):
        return None
    return hand if hand.shape == (21, 3) and bool(np.isfinite(hand).all()) else None


def _minimum_pair_distance(hand: np.ndarray) -> float:
    minimum = math.inf
    for left in range(len(hand) - 1):
        for right in range(left + 1, len(hand)):
            minimum = min(minimum, float(np.linalg.norm(hand[left] - hand[right])))
    return minimum


def _quantize_hand(hand: np.ndarray, steps: Sequence[float]) -> np.ndarray:
    result = hand.copy()
    for axis, step in enumerate(steps):
        result[:, axis] = np.round(result[:, axis] / float(step)) * float(step)
    return result


def _audit_normal_collisions(template_root: Path, web_root: Path) -> Dict[str, Any]:
    paths = sorted(set(template_root.rglob("*holistic_results.json")) | set(web_root.rglob("*holistic_results.json")))
    hand_frames = 0
    raw_collision_frames = 0
    raw_global_quantization_signature_frames = 0
    minimum_normal_pair_distance = math.inf
    quantized = {
        name: {
            "collision_frame_count": 0,
            "max_collision_participant_count": 0,
            "max_collision_cluster_size": 0,
            "quantization_signature_violation_count": 0,
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
                hand_frames += 1
                minimum_normal_pair_distance = min(minimum_normal_pair_distance, _minimum_pair_distance(hand))
                raw_metrics = _hand_landmark_collision_metrics(hand, np.ones(21, dtype=np.float32)) or {}
                raw_collision_frames += int(bool(raw_metrics.get("collision_indices")))
                raw_global_quantization_signature_frames += int(
                    _hand_global_quantization_signature(hand, np.ones(21, dtype=np.float32)) is not None
                )
                for name, steps in QUANTIZATION_SPECS.items():
                    candidate = _quantize_hand(hand, steps)
                    metrics = _hand_landmark_collision_metrics(candidate, np.ones(21, dtype=np.float32)) or {}
                    item = quantized[name]
                    item["quantization_signature_violation_count"] += int(
                        metrics.get("global_quantization_signature") is None
                    )
                    participant_count = int(metrics.get("collision_participant_count") or 0)
                    if participant_count <= 0:
                        continue
                    item["collision_frame_count"] += 1
                    item["max_collision_participant_count"] = max(
                        int(item["max_collision_participant_count"]),
                        participant_count,
                    )
                    item["max_collision_cluster_size"] = max(
                        int(item["max_collision_cluster_size"]),
                        int(metrics.get("max_collision_cluster_size") or 0),
                    )
                    _, masked = _mask_hand_landmark_collisions(candidate, np.ones(21, dtype=np.float32))
                    actual_masked = set(np.flatnonzero(masked <= 0).tolist())
                    item["quantization_bypass_violation_count"] += int(bool(actual_masked))
    quantized_passed = all(
        int(item["quantization_signature_violation_count"]) == 0
        and int(item["quantization_bypass_violation_count"]) == 0
        for item in quantized.values()
    )
    return {
        "file_count": len(paths),
        "hand_frame_count": hand_frames,
        "raw_collision_frame_count": raw_collision_frames,
        "raw_global_quantization_signature_frame_count": raw_global_quantization_signature_frames,
        "minimum_normal_pair_distance": (
            minimum_normal_pair_distance if math.isfinite(minimum_normal_pair_distance) else None
        ),
        "collision_distance_max": HAND_LANDMARK_COLLISION_DISTANCE_MAX,
        "quantized": quantized,
        "passed": bool(
            hand_frames > 0
            and raw_collision_frames == 0
            and raw_global_quantization_signature_frames == 0
            and minimum_normal_pair_distance > HAND_LANDMARK_COLLISION_DISTANCE_MAX
            and quantized_passed
        ),
    }


def _spec(
    variant: str,
    group: str,
    pattern: str,
    operation: str,
    kind: str,
    threshold: Optional[float],
    rationale: str,
    *,
    expect_collision_masked: bool = True,
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
        "expect_collision_masked": expect_collision_masked,
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
            "rationale": "原始标准 JSON 重载后应保持近满分。",
        }
    ]
    groups = ["right_hand_landmarks"]
    if word == "跳":
        groups.append("left_hand_landmarks")
    for group in groups:
        for operation in SEVERE_COLLISION_OPERATIONS:
            specs.append(
                _spec(
                    f"{group}_{operation}_sparse_preserved",
                    group,
                    "sparse_visible",
                    operation,
                    "positive",
                    sparse_min_score,
                    "稀疏碰撞只屏蔽歧义点，正确动作其余帧应继续可评分。",
                )
            )
            diagnostic = bool(
                (
                    group == "right_hand_landmarks"
                    and (word == "跳" or operation != "index_middle_to_index_mcp")
                )
                or (
                    group == "left_hand_landmarks"
                    and operation in {"distal_to_mcp_all", "index_middle_to_index_mcp"}
                )
            )
            if diagnostic:
                specs.append(
                    _spec(
                        f"{group}_{operation}_full_semantic_mismatch",
                        group,
                        "full_visible",
                        operation,
                        "diagnostic",
                        diagnostic_max_score,
                        "整段核心手或双手关系锚点严重碰撞在歧义点被屏蔽后不能继续给高分。",
                    )
                )
            else:
                specs.append(
                    _spec(
                        f"{group}_{operation}_full_noncore_preserved",
                        group,
                        "full_visible",
                        operation,
                        "positive",
                        sparse_min_score,
                        "跳的非核心左手严重碰撞被局部屏蔽后，不应误伤核心动作。",
                    )
                )
        for operation in CLUSTER_COLLISION_OPERATIONS:
            specs.append(
                _spec(
                    f"{group}_{operation}_full_local_mask",
                    group,
                    "full_visible",
                    operation,
                    "handling",
                    None,
                    "单个大碰撞簇也只屏蔽碰撞参与点，不凭总数丢弃整只手。",
                )
            )
        specs.append(
            _spec(
                f"{group}_single_index_tip_to_dip_sparse_preserved",
                group,
                "sparse_visible",
                "single_index_tip_to_dip",
                "positive",
                70.0,
                "单对局部碰撞只屏蔽两个歧义点，稀疏错误应保持高分。",
            )
        )
        for quantization in QUANTIZATION_SPECS:
            specs.append(
                _spec(
                    f"{group}_{quantization}_raw_quantized",
                    group,
                    "full_visible",
                    f"quantize_{quantization}",
                    "positive",
                    70.0,
                    "合理原始坐标量化即使产生重复点，也应通过全局量化豁免继续评分。",
                    expect_collision_masked=False,
                )
            )
    return specs


def _mutate_array(landmarks: List[Any], operation: str) -> None:
    if not landmarks:
        return
    original = copy.deepcopy(landmarks)
    if operation == "single_index_tip_to_dip":
        landmarks[8] = copy.deepcopy(original[7])
    elif operation == "tip_to_dip_all":
        for tip, dip in zip((4, 8, 12, 16, 20), (3, 7, 11, 15, 19)):
            landmarks[tip] = copy.deepcopy(original[dip])
    elif operation == "dip_tip_to_pip_all":
        for pip, dip, tip in zip((2, 6, 10, 14, 18), (3, 7, 11, 15, 19), (4, 8, 12, 16, 20)):
            landmarks[dip] = copy.deepcopy(original[pip])
            landmarks[tip] = copy.deepcopy(original[pip])
    elif operation == "distal_to_mcp_all":
        for mcp, pip, dip, tip in zip(
            (1, 5, 9, 13, 17),
            (2, 6, 10, 14, 18),
            (3, 7, 11, 15, 19),
            (4, 8, 12, 16, 20),
        ):
            landmarks[pip] = copy.deepcopy(original[mcp])
            landmarks[dip] = copy.deepcopy(original[mcp])
            landmarks[tip] = copy.deepcopy(original[mcp])
    elif operation == "all_tips_to_wrist":
        for tip in (4, 8, 12, 16, 20):
            landmarks[tip] = copy.deepcopy(original[0])
    elif operation == "all_mcps_to_wrist":
        for mcp in (1, 5, 9, 13, 17):
            landmarks[mcp] = copy.deepcopy(original[0])
    elif operation == "index_middle_to_index_mcp":
        for index in (6, 7, 8, 9, 10, 11, 12):
            landmarks[index] = copy.deepcopy(original[5])
    elif operation.startswith("quantize_"):
        name = operation.removeprefix("quantize_")
        steps = QUANTIZATION_SPECS[name]
        for item in landmarks:
            if not isinstance(item, dict):
                continue
            for axis, step in zip(("x", "y", "z"), steps):
                item[axis] = round(float(item[axis]) / step) * step
    elif operation != "none":
        raise ValueError(f"unknown hand landmark collision operation: {operation}")


def _write_fixture(source_json: Path, dest_json: Path, spec: Dict[str, Any]) -> Dict[str, Any]:
    payload = copy.deepcopy(json.loads(source_json.read_text(encoding="utf-8")))
    records = _records(payload)
    active = _active_indices(records, str(spec["group"]), str(spec["pattern"])) if spec["group"] else []
    expected_collision_indices: Dict[int, List[int]] = {}
    pair_counts: List[int] = []
    participant_counts: List[int] = []
    cluster_sizes: List[int] = []
    for index in active:
        record = records[index]
        result_data = record.get("result_data") if isinstance(record, dict) else None
        landmarks = result_data.get(spec["group"]) if isinstance(result_data, dict) else None
        if not isinstance(landmarks, list) or len(landmarks) != 21:
            continue
        _mutate_array(landmarks, str(spec["operation"]))
        hand = _parse_hand(landmarks)
        metrics = (
            _hand_landmark_collision_metrics(hand, np.ones(21, dtype=np.float32))
            if hand is not None
            else None
        ) or {}
        indices = [int(item) for item in metrics.get("collision_indices") or []]
        if indices:
            expected_collision_indices[index] = indices
        pair_counts.append(int(metrics.get("collision_pair_count") or 0))
        participant_counts.append(int(metrics.get("collision_participant_count") or 0))
        cluster_sizes.append(int(metrics.get("max_collision_cluster_size") or 0))
    dest_json.parent.mkdir(parents=True, exist_ok=True)
    dest_json.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return {
        "active_indices": active,
        "changed_frame_count": len(pair_counts),
        "collision_frame_count": len(expected_collision_indices),
        "collision_frame_rate": len(expected_collision_indices) / len(active) if active else 0.0,
        "collision_pair_count_min": min(pair_counts) if pair_counts else None,
        "collision_pair_count_max": max(pair_counts) if pair_counts else None,
        "collision_participant_count_min": min(participant_counts) if participant_counts else None,
        "collision_participant_count_max": max(participant_counts) if participant_counts else None,
        "max_collision_cluster_size": max(cluster_sizes) if cluster_sizes else None,
        "expected_collision_indices": expected_collision_indices,
        "total_records": len(records),
    }


def _collision_mask_handling(
    query: Any,
    presence_group: str,
    expected_collision_indices: Dict[int, List[int]],
    expect_collision_masked: bool,
) -> Dict[str, Any]:
    checked = 0
    handled = 0
    minimum_remaining = 21
    maximum_remaining = 0
    for raw_index, indices in expected_collision_indices.items():
        index = int(raw_index)
        if index >= len(query.features):
            continue
        frame = query.features[index]
        group_slice = frame.groups.get(presence_group)
        if group_slice is None:
            continue
        point_mask = frame.mask[group_slice].reshape(-1, 3).mean(axis=1) > 0.5
        checked += 1
        handled += int(
            all(
                not bool(point_mask[item]) if expect_collision_masked else bool(point_mask[item])
                for item in indices
            )
        )
        remaining = int(point_mask.sum())
        minimum_remaining = min(minimum_remaining, remaining)
        maximum_remaining = max(maximum_remaining, remaining)
    return {
        "collision_frames_checked": checked,
        "collision_frames_handled": handled,
        "collision_handling_rate": handled / checked if checked else 1.0,
        "expect_collision_masked": expect_collision_masked,
        "minimum_remaining_point_count": minimum_remaining if checked else None,
        "maximum_remaining_point_count": maximum_remaining if checked else None,
        "passed": bool(checked == len(expected_collision_indices) and handled == checked),
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
                    "collision_handling": {},
                    "capture_quality": {},
                    "passed": False,
                }
            )
        else:
            handling = _collision_mask_handling(
                query,
                str(spec["presence_group"]),
                detail["expected_collision_indices"],
                bool(spec.get("expect_collision_masked", True)),
            ) if spec["group"] else {"passed": True}
            score = float(result["prototype_score"])
            capture_quality = (result.get("score_scale") or {}).get("capture_quality") or {}
            result_finite = _finite(result)
            if spec["kind"] == "diagnostic":
                score_ok = score <= float(spec["threshold"])
                semantic_ok = capture_quality.get("status") in {"needs_recapture", "semantic_mismatch"}
            elif spec["kind"] == "positive":
                score_ok = score >= float(spec["threshold"])
                semantic_ok = True
            else:
                score_ok = True
                semantic_ok = True
            row.update(
                {
                    "exception": "",
                    "score": score,
                    "dtw_distance": float(result["dtw_distance"]),
                    "normalized_distance": float(result["normalized_distance"]),
                    "result_finite": result_finite,
                    "collision_handling": handling,
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
        "collision_frame_count",
        "collision_participant_count_min",
        "collision_participant_count_max",
        "max_collision_cluster_size",
        "collision_handling_rate",
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
                handling = row.get("collision_handling") or {}
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
                        "collision_frame_count": row.get("collision_frame_count"),
                        "collision_participant_count_min": row.get("collision_participant_count_min"),
                        "collision_participant_count_max": row.get("collision_participant_count_max"),
                        "max_collision_cluster_size": row.get("max_collision_cluster_size"),
                        "collision_handling_rate": handling.get("collision_handling_rate"),
                        "minimum_remaining_point_count": handling.get("minimum_remaining_point_count"),
                        "capture_quality": quality.get("status"),
                        "capture_reason": quality.get("reason"),
                        "exception": row.get("exception"),
                    }
                )


def _build_markdown(payload: Dict[str, Any]) -> str:
    audit = payload["normal_collision_audit"]
    lines = [
        "# 花/跳 Hand Landmark 碰撞完整性鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 碰撞边界：三维距离 `<= {payload['collision_distance_max']}` 的参与点按歧义点局部屏蔽；"
        "完整手若符合已知全局量化网格则保留。",
        (
            f"- 正常证据审计：`{audit['file_count']}` 个模板/网页 JSON、`{audit['hand_frame_count']}` 个非空手帧，"
            f"原始碰撞帧 `{audit['raw_collision_frame_count']}`，最小正常点间距 `{audit['minimum_normal_pair_distance']}`。"
        ),
        (
            f"- 全局量化签名：原始误命中 `{audit['raw_global_quantization_signature_frame_count']}`；"
            f"候选步长 `{payload['global_quantization_steps']}`，归一残差上限 "
            f"`{payload['global_quantization_residual_max']}`。"
        ),
        f"- 量化兼容审计：`{audit['quantized']}`。",
        "- 口径：只写缓存 Holistic JSON fixture；不调用 `/api/score`、不运行 Holistic、不移动 marker、不重启 5080。",
        "",
        "## 结论",
        "",
        f"- 综合状态：`{'PASS' if payload['passed'] else 'FAIL'}`",
        "",
        "| 目标词 | 状态 | 正向最低分 | 最弱正向变体 | 核心碰撞诊断最高分 | 最强诊断变体 |",
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
                "| 变体 | 类型 | 状态 | 分数 | 阈值 | 碰撞帧 | 参与点范围 | 最大簇 | 屏蔽处理率 | 最少剩余点 | capture_quality |",
                "|---|---|---|---:|---:|---:|---|---:|---:|---:|---|",
            ]
        )
        for row in item["variants"]:
            quality = row.get("capture_quality") or {}
            handling = row.get("collision_handling") or {}
            participant_range = (
                f"{row.get('collision_participant_count_min')}-{row.get('collision_participant_count_max')}"
                if row.get("collision_participant_count_min") is not None
                else "-"
            )
            lines.append(
                f"| {row['variant']} | {row['kind']} | {'PASS' if row['passed'] else 'FAIL'} | "
                f"{_fmt(row.get('score'))} | {_fmt(row.get('threshold'))} | {row.get('collision_frame_count')} | "
                f"{participant_range} | {row.get('max_collision_cluster_size')} | "
                f"{_fmt(handling.get('collision_handling_rate'))} | "
                f"{handling.get('minimum_remaining_point_count')} | "
                f"{quality.get('status') or '-'}:{quality.get('reason') or '-'} |"
            )
        lines.append("")
    lines.extend(
        [
            "## 说明",
            "",
            "- 非量化手只屏蔽碰撞参与点；不能按碰撞参与点总数丢弃整手，因为合理坐标量化也会产生多个重复点。",
            "- 正常原始证据零碰撞和零全局量化签名误命中是硬门；量化审计验证已知网格完整保留。",
            "- 该门补充 wrist 身份、内部拓扑和坐标精度门，不替代正式 marker 后真实网页摄像头复测。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run hand landmark collision robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--web-root", default=str(DEFAULT_WEB_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_hand_landmark_collision_robustness_gate_current"))
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
    fixture_dir = output_dir / "fixtures"
    results = [
        _run_word(
            word,
            template_root,
            semantic_profile_json,
            args.feature_mode,
            args.sparse_min_score,
            args.diagnostic_max_score,
            fixture_dir,
        )
        for word in args.words
    ]
    normal_collision_audit = _audit_normal_collisions(template_root, web_root)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "claim_policy": "synthetic hand-landmark-collision robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "web_root": str(web_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": _load_backend_status(args.backend_url, args.status_timeout_sec),
        "collision_distance_max": HAND_LANDMARK_COLLISION_DISTANCE_MAX,
        "global_quantization_steps": HAND_GLOBAL_QUANTIZATION_STEPS,
        "global_quantization_residual_max": HAND_GLOBAL_QUANTIZATION_RESIDUAL_MAX,
        "normal_collision_audit": normal_collision_audit,
        "sparse_min_score": args.sparse_min_score,
        "diagnostic_max_score": args.diagnostic_max_score,
        "results": results,
        "passed": bool(normal_collision_audit["passed"] and all(bool(item["gate_pass"]) for item in results)),
    }

    json_path = output_dir / "flower_jump_hand_landmark_collision_robustness_gate.json"
    md_path = output_dir / "flower_jump_hand_landmark_collision_robustness_gate.md"
    csv_path = output_dir / "flower_jump_hand_landmark_collision_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成 Hand Landmark 碰撞完整性 JSON：{json_path}")
    print(f"已生成 Hand Landmark 碰撞完整性报告：{md_path}")
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

#!/usr/bin/env python3
"""Stress-test pose normalization anchors used by flower/jump scoring.

Finite but invalid shoulder landmarks can corrupt the shared pose center/scale
normalization even when the hands are tracked correctly. This gate writes
mutated cached-Holistic JSON fixtures and reloads them through the normal
scoring path. It does not call /api/score, run Holistic, move the web marker,
or restart 5080.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from run_flower_jump_finite_coordinate_robustness_gate import (
    _records,
    _result_finite,
    _row_passed,
    _sequence_finite_summary,
    _write_rows_csv,
)
from run_flower_jump_landmark_noise_robustness_gate import _fmt, _json_default, _load_backend_status
from run_flower_jump_mirror_robustness_gate import _template_json
from score_holistic_sequence_mvp import (
    DEFAULT_SEMANTIC_PROFILE_JSON,
    POSE_HAND_WRIST_XY_DISTANCE_MAX,
    POSE_FALLBACK_HAND_SCALE_FACTOR,
    POSE_FALLBACK_SCALE_MAX,
    POSE_FALLBACK_SCALE_MIN,
    POSE_SEQUENCE_SHOULDER_HAND_Z_MEDIAN_MAX,
    POSE_SEQUENCE_SHOULDER_HAND_Z_MEDIAN_MIN,
    POSE_SHOULDER_HIP_WIDTH_RATIO_MAX,
    POSE_SHOULDER_HIP_WIDTH_RATIO_MIN,
    POSE_SHOULDER_NOSE_Y_GAP_MAX,
    POSE_SHOULDER_NOSE_Y_GAP_MIN,
    POSE_SHOULDER_NOSE_Z_GAP_MAX,
    POSE_SHOULDER_NOSE_Z_GAP_MIN,
    POSE_SHOULDER_SCALE_MAX,
    POSE_SHOULDER_SCALE_MIN,
    POSE_SHOULDER_X_MAX,
    POSE_SHOULDER_X_MIN,
    POSE_SHOULDER_Y_MAX,
    POSE_SHOULDER_Y_MIN,
    POSE_SHOULDER_Z_MAX,
    POSE_SHOULDER_Z_MIN,
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


def _spec(
    variant: str,
    pattern: str,
    operation: str,
    rationale: str,
    min_score: float,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": "positive",
        "gated": True,
        "pattern": pattern,
        "operation": operation,
        "mutations": [{"operation": operation}],
        "rationale": rationale,
        "min_score": min_score,
    }


def _variant_specs(min_score: float, sparse_min_score: float) -> List[Dict[str, Any]]:
    return [
        _spec("self_reloaded", "none", "none", "原始标准 JSON 重载后应保持近满分。", 95.0),
        _spec(
            "left_shoulder_xy_outlier_sparse_interpolated",
            "sparse_every_7f",
            "left_shoulder_xy_outlier",
            "稀疏有限肩部 x/y 离群应由相邻可信肩锚点插值，不能制造归一化抖动。",
            sparse_min_score,
        ),
        _spec(
            "left_shoulder_z_outlier_sparse_interpolated",
            "sparse_every_7f",
            "left_shoulder_z_outlier",
            "稀疏有限肩部 z 离群应由相邻可信肩锚点插值。",
            sparse_min_score,
        ),
        _spec(
            "duplicate_shoulders_sparse_interpolated",
            "sparse_every_7f",
            "duplicate_shoulders",
            "稀疏肩点塌缩不能把 shoulder scale 压到近零。",
            sparse_min_score,
        ),
        _spec(
            "extreme_shoulder_span_sparse_interpolated",
            "sparse_every_7f",
            "extreme_shoulder_span",
            "稀疏异常肩宽不能缩放手部与双手关系特征。",
            sparse_min_score,
        ),
        _spec(
            "vertical_shoulder_shift_sparse_interpolated",
            "sparse_every_7f",
            "vertical_shoulder_shift",
            "稀疏肩部 +0.7 边界漂移应由可信相邻帧插值。",
            sparse_min_score,
        ),
        _spec(
            "left_shoulder_xy_outlier_full_hand_fallback",
            "full",
            "left_shoulder_xy_outlier",
            "整段肩部 x/y 离群时，应使用有效手部中心/掌尺度 fallback。",
            min_score,
        ),
        _spec(
            "left_shoulder_z_outlier_full_hand_fallback",
            "full",
            "left_shoulder_z_outlier",
            "整段肩部 z 离群时，应使用有效手部中心/掌尺度 fallback。",
            min_score,
        ),
        _spec(
            "duplicate_shoulders_full_hand_fallback",
            "full",
            "duplicate_shoulders",
            "整段肩点塌缩时，应拒绝近零 shoulder scale 并使用手部 fallback。",
            min_score,
        ),
        _spec(
            "extreme_shoulder_span_full_hand_fallback",
            "full",
            "extreme_shoulder_span",
            "整段异常肩宽时，应拒绝离群 shoulder scale 并使用手部 fallback。",
            min_score,
        ),
        _spec(
            "vertical_shoulder_shift_full_hand_fallback",
            "full",
            "vertical_shoulder_shift",
            "整段肩部 +0.7 边界漂移时，应由 pose 拓扑一致性拒绝并使用手部 fallback。",
            min_score,
        ),
        _spec(
            "both_shoulders_z_positive_full_hand_fallback",
            "full",
            "both_shoulders_z_positive",
            "整段双肩 z 正向漂移时，应由 pose 拓扑或肩手流一致性拒绝。",
            min_score,
        ),
        _spec(
            "both_shoulders_z_negative_full_hand_fallback",
            "full",
            "both_shoulders_z_negative",
            "整段双肩 z 负向漂移时，应由 pose 拓扑或肩手流一致性拒绝。",
            min_score,
        ),
        _spec(
            "all_pose_xy_shift_full_hand_fallback",
            "full",
            "all_pose_xy_shift",
            "整段 pose 流与 hand 流发生 x/y 偏移时，应由 pose-hand wrist 一致性拒绝肩锚点。",
            min_score,
        ),
        _spec(
            "all_pose_z_positive_full_hand_fallback",
            "full",
            "all_pose_z_positive",
            "整段 pose 流与 hand 流发生正向 z 偏移时，应由序列级肩手 z 一致性拒绝肩锚点。",
            min_score,
        ),
        _spec(
            "all_pose_z_negative_full_hand_fallback",
            "full",
            "all_pose_z_negative",
            "整段 pose 流与 hand 流发生负向 z 偏移时，应由序列级肩手 z 一致性拒绝肩锚点。",
            min_score,
        ),
        _spec(
            "all_pose_nonfinite_full_hand_fallback",
            "full",
            "all_pose_nonfinite",
            "整段 pose 非有限但手部完整时，手部主导词仍应可评分。",
            min_score,
        ),
        _spec(
            "all_pose_zero_full_hand_fallback",
            "full",
            "all_pose_zero",
            "整段 pose exact-zero 占位但手部完整时，不能使用零肩宽归一化。",
            min_score,
        ),
        _spec(
            "pose_group_removed_full_hand_fallback",
            "full",
            "pose_group_removed",
            "整段 pose group 缺失但手部完整时，手部主导词仍应可评分。",
            min_score,
        ),
    ]


def _active_indices(pattern: str, length: int) -> List[int]:
    if pattern == "none":
        return []
    if pattern == "full":
        return list(range(length))
    if pattern == "sparse_every_7f":
        return [idx for idx in range(length) if idx % 7 == 3]
    raise ValueError(f"unknown pose-normalization-anchor pattern: {pattern}")


def _apply_operation(result_data: Dict[str, Any], operation: str) -> int:
    pose = result_data.get("pose_landmarks")
    if operation == "pose_group_removed":
        changed = len(pose) if isinstance(pose, list) else 0
        result_data["pose_landmarks"] = []
        return changed
    if not isinstance(pose, list) or len(pose) <= 12:
        return 0
    if not isinstance(pose[11], dict) or not isinstance(pose[12], dict):
        return 0
    if operation == "left_shoulder_xy_outlier":
        pose[11]["x"] = 5.0
        pose[11]["y"] = 5.0
        return 2
    if operation == "left_shoulder_z_outlier":
        pose[11]["z"] = 5.0
        return 1
    if operation == "duplicate_shoulders":
        changed = 0
        for axis in ["x", "y", "z"]:
            pose[12][axis] = pose[11].get(axis, 0.0)
            changed += 1
        return changed
    if operation == "extreme_shoulder_span":
        pose[11]["x"] = 2.0
        pose[12]["x"] = -1.0
        return 2
    if operation == "vertical_shoulder_shift":
        pose[11]["y"] = float(pose[11].get("y", 0.0)) + 0.7
        pose[12]["y"] = float(pose[12].get("y", 0.0)) + 0.7
        return 2
    if operation == "both_shoulders_z_positive":
        pose[11]["z"] = float(pose[11].get("z", 0.0)) + 1.0
        pose[12]["z"] = float(pose[12].get("z", 0.0)) + 1.0
        return 2
    if operation == "both_shoulders_z_negative":
        pose[11]["z"] = float(pose[11].get("z", 0.0)) - 1.0
        pose[12]["z"] = float(pose[12].get("z", 0.0)) - 1.0
        return 2
    if operation == "all_pose_xy_shift":
        changed = 0
        for point in pose:
            if not isinstance(point, dict):
                continue
            point["x"] = float(point.get("x", 0.0)) + 0.6
            point["y"] = float(point.get("y", 0.0)) + 0.6
            changed += 2
        return changed
    if operation in {"all_pose_z_positive", "all_pose_z_negative"}:
        delta = 1.0 if operation == "all_pose_z_positive" else -1.0
        changed = 0
        for point in pose:
            if not isinstance(point, dict):
                continue
            point["z"] = float(point.get("z", 0.0)) + delta
            changed += 1
        return changed
    if operation == "all_pose_nonfinite":
        changed = 0
        for point in pose:
            if not isinstance(point, dict):
                continue
            for axis in ["x", "y", "z"]:
                point[axis] = float("nan")
                changed += 1
        return changed
    if operation == "all_pose_zero":
        changed = 0
        for point in pose:
            if not isinstance(point, dict):
                continue
            for axis in ["x", "y", "z"]:
                point[axis] = 0.0
                changed += 1
        return changed
    if operation == "none":
        return 0
    raise ValueError(f"unknown pose-normalization-anchor operation: {operation}")


def _write_mutated_json(source_json: Path, dest_json: Path, spec: Dict[str, Any]) -> Dict[str, Any]:
    payload = copy.deepcopy(json.loads(source_json.read_text(encoding="utf-8")))
    records = _records(payload)
    active = _active_indices(str(spec["pattern"]), len(records))
    changed_values = 0
    for index in active:
        record = records[index]
        if not isinstance(record, dict):
            continue
        result_data = record.get("result_data")
        if not isinstance(result_data, dict):
            continue
        changed_values += _apply_operation(result_data, str(spec["operation"]))
    dest_json.parent.mkdir(parents=True, exist_ok=True)
    dest_json.write_text(json.dumps(payload, ensure_ascii=False, allow_nan=True), encoding="utf-8")
    return {
        "active_frame_count": len(active),
        "changed_values": changed_values,
        "skipped_values": 0,
        "total_records": len(records),
    }


def _run_word(
    word: str,
    template_root: Path,
    semantic_profile_json: Path,
    feature_mode: str,
    min_score: float,
    sparse_min_score: float,
    fixture_dir: Path,
) -> Dict[str, Any]:
    standard_json = _template_json(template_root, word)
    standard = load_sequence(standard_json, feature_mode, force_bbox=False, apply_sidecar_weights=False)
    profile = load_semantic_profile(word, semantic_profile_json)
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(min_score, sparse_min_score):
        fixture_json = fixture_dir / word / f"{spec['variant']}.json"
        detail = _write_mutated_json(standard_json, fixture_json, spec)
        row: Dict[str, Any] = {
            **spec,
            "fixture_json": str(fixture_json),
            **detail,
        }
        try:
            query = load_sequence(fixture_json, feature_mode, force_bbox=False, apply_sidecar_weights=False)
            result = run_pair(standard, query, semantic_profile=profile, target_word=word, enable_cross_check=False)
        except Exception as exc:  # noqa: BLE001 - loader/scorer crashes are gate failures.
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
    weakest = min(
        [row for row in rows if row.get("score") is not None],
        key=lambda row: float(row["score"]),
        default=None,
    )
    return {
        "word": word,
        "standard_json": str(standard_json),
        "standard_length": len(standard.features),
        "semantic_profile": _profile_summary(profile),
        "gate_pass": all(bool(row["passed"]) for row in rows),
        "weakest_positive_score": float(weakest["score"]) if weakest else None,
        "weakest_positive_variant": weakest["variant"] if weakest else "",
        "min_required_score": min_score,
        "sparse_min_required_score": sparse_min_score,
        "variants": rows,
    }


def _build_markdown(payload: Dict[str, Any]) -> str:
    thresholds = payload["normalization_thresholds"]
    lines = [
        "# 花/跳 Pose 归一化锚点鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        "- 口径：污染缓存 JSON 中的肩部/pose 锚点，再经正常 `load_sequence()` 和 `run_pair()` 评分；不调用 `/api/score`、不运行 Holistic、不移动 marker、不重启 5080。",
        "- 目标：肩部需同时满足绝对边界、pose 拓扑和 pose-hand 流一致性；稀疏坏肩点使用相邻可信锚点插值，整段肩部或 pose 不可信时从有效手部中心与掌尺度回退。",
        f"- 正常审计：`178` 个模板/网页 JSON、`4776` 个 pose 帧，肩宽范围 `0.105884-0.571933`；当前门使用 shoulder scale `[{thresholds['shoulder_scale_min']}, {thresholds['shoulder_scale_max']}]`。",
        "",
        "## 结论",
        "",
        f"- 综合状态：`{'PASS' if payload['passed'] else 'FAIL'}`",
        "",
        "| 目标词 | 状态 | 正向最低分 | 最弱变体 | 基础门槛 | 稀疏门槛 |",
        "|---|---|---:|---|---:|---:|",
    ]
    for item in payload["results"]:
        lines.append(
            f"| {item['word']} | {'PASS' if item['gate_pass'] else 'FAIL'} | "
            f"{_fmt(item['weakest_positive_score'])} | {item['weakest_positive_variant']} | "
            f"{_fmt(item['min_required_score'])} | {_fmt(item['sparse_min_required_score'])} |"
        )
    lines.extend(["", "## 分项明细", ""])
    for item in payload["results"]:
        lines.extend(
            [
                f"### {item['word']}",
                "",
                "| 变体 | 状态 | 分数 | 门槛 | finite | 改动值 | capture_quality | 说明 |",
                "|---|---|---:|---:|---|---:|---|---|",
            ]
        )
        for row in item["variants"]:
            quality = row.get("capture_quality") or {}
            lines.append(
                f"| {row['variant']} | {'PASS' if row['passed'] else 'FAIL'} | {_fmt(row.get('score'))} | "
                f"{_fmt(row.get('min_score'))} | {row.get('result_finite')} | {row.get('changed_values')} | "
                f"{quality.get('status') or '-'}:{quality.get('reason') or '-'} | {row['rationale']} |"
            )
        lines.append("")
    lines.extend(
        [
            "## 说明",
            "",
            "- 该门验证的是归一化入口，不通过放宽 `花/跳` 词义阈值抬分。",
            "- pose 缺失但手部完整时可继续做手部主导词的原型相似度评分；这不等于真实用户分数已校准。",
            "- 该门是缓存 JSON 压力测试，不能替代正式 marker 后真实网页摄像头复测。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run pose-normalization-anchor robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_pose_normalization_anchor_robustness_gate_current"))
    parser.add_argument("--words", nargs="+", default=DEFAULT_WORDS)
    parser.add_argument("--feature-mode", choices=["auto", "landmark", "bbox"], default="auto")
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--status-timeout-sec", type=float, default=3.0)
    parser.add_argument("--min-score", type=float, default=70.0)
    parser.add_argument("--sparse-min-score", type=float, default=75.0)
    args = parser.parse_args(argv)

    template_root = Path(args.template_root)
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
            args.min_score,
            args.sparse_min_score,
            fixture_dir,
        )
        for word in args.words
    ]
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "claim_policy": "synthetic pose-normalization-anchor robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": _load_backend_status(args.backend_url, args.status_timeout_sec),
        "normalization_thresholds": {
            "shoulder_x_min": POSE_SHOULDER_X_MIN,
            "shoulder_x_max": POSE_SHOULDER_X_MAX,
            "shoulder_y_min": POSE_SHOULDER_Y_MIN,
            "shoulder_y_max": POSE_SHOULDER_Y_MAX,
            "shoulder_z_min": POSE_SHOULDER_Z_MIN,
            "shoulder_z_max": POSE_SHOULDER_Z_MAX,
            "shoulder_scale_min": POSE_SHOULDER_SCALE_MIN,
            "shoulder_scale_max": POSE_SHOULDER_SCALE_MAX,
            "shoulder_nose_y_gap_min": POSE_SHOULDER_NOSE_Y_GAP_MIN,
            "shoulder_nose_y_gap_max": POSE_SHOULDER_NOSE_Y_GAP_MAX,
            "shoulder_nose_z_gap_min": POSE_SHOULDER_NOSE_Z_GAP_MIN,
            "shoulder_nose_z_gap_max": POSE_SHOULDER_NOSE_Z_GAP_MAX,
            "shoulder_hip_width_ratio_min": POSE_SHOULDER_HIP_WIDTH_RATIO_MIN,
            "shoulder_hip_width_ratio_max": POSE_SHOULDER_HIP_WIDTH_RATIO_MAX,
            "hand_wrist_xy_distance_max": POSE_HAND_WRIST_XY_DISTANCE_MAX,
            "sequence_shoulder_hand_z_median_min": POSE_SEQUENCE_SHOULDER_HAND_Z_MEDIAN_MIN,
            "sequence_shoulder_hand_z_median_max": POSE_SEQUENCE_SHOULDER_HAND_Z_MEDIAN_MAX,
            "fallback_hand_scale_factor": POSE_FALLBACK_HAND_SCALE_FACTOR,
            "fallback_scale_min": POSE_FALLBACK_SCALE_MIN,
            "fallback_scale_max": POSE_FALLBACK_SCALE_MAX,
        },
        "min_score": args.min_score,
        "sparse_min_score": args.sparse_min_score,
        "results": results,
        "passed": all(bool(item["gate_pass"]) for item in results),
    }

    json_path = output_dir / "flower_jump_pose_normalization_anchor_robustness_gate.json"
    md_path = output_dir / "flower_jump_pose_normalization_anchor_robustness_gate.md"
    csv_path = output_dir / "flower_jump_pose_normalization_anchor_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成 Pose 归一化锚点鲁棒性门 JSON：{json_path}")
    print(f"已生成 Pose 归一化锚点鲁棒性门报告：{md_path}")
    print(f"综合状态：{'PASS' if payload['passed'] else 'FAIL'}")
    for item in results:
        print(
            f"- {item['word']}: {'PASS' if item['gate_pass'] else 'FAIL'} "
            f"positive_min={_fmt(item['weakest_positive_score'])} weakest={item['weakest_positive_variant']}"
        )
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

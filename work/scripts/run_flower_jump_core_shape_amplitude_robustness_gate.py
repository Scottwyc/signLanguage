#!/usr/bin/env python3
"""Stress-test flower/jump scoring against core hand-shape amplitude changes.

Browser users rarely reproduce the template's exact finger-opening amplitude.
For flower, the right hand may open a little less or more while still showing a
clear blooming dynamic; a strongly collapsed opening should be low or diagnosed
as semantic mismatch. For jump, the right index/middle "person" shape may vary
mildly, but severe damage is recorded as diagnostic-only because existing
hard-negative gates already cover missing/clipped/role-swapped core evidence.

This script edits cached skeleton sequences in memory only. It does not call
/api/score, run Holistic, move marker, or restart 5080.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import numpy as np

from run_flower_jump_landmark_noise_robustness_gate import (
    _fmt,
    _hand_array,
    _json_default,
    _load_backend_status,
    _set_hand_group,
)
from run_flower_jump_mirror_robustness_gate import _strip_to_base_groups, _template_json
from score_holistic_sequence_mvp import (
    DEFAULT_SEMANTIC_PROFILE_JSON,
    FrameFeature,
    SequenceData,
    _clone_frame,
    _profile_summary,
    _sequence_with_relative_motion_features,
    load_semantic_profile,
    load_sequence,
    run_pair,
)


REPO_ROOT = Path("/data/WYC/signLanguage")
DEFAULT_TEMPLATE_ROOT = REPO_ROOT / "work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results"
DEFAULT_OUTPUT_BASE = REPO_ROOT / "work/generated/scoring_mvp_run3"
DEFAULT_BACKEND_URL = "http://127.0.0.1:5080"
DEFAULT_WORDS = ["花", "跳"]
ACCEPTED_NEGATIVE_QUALITY = {"needs_recapture", "semantic_mismatch"}

PALM_CENTER_LANDMARKS = [0, 5, 9, 13, 17]
FLOWER_DISTAL_LANDMARKS = [2, 3, 4, 6, 7, 8, 10, 11, 12, 14, 15, 16, 18, 19, 20]
FLOWER_TIPS = [4, 8, 12, 16, 20]
JUMP_INDEX_MIDDLE_LANDMARKS = [5, 6, 7, 8, 9, 10, 11, 12]


def _visible_center(coords: np.ndarray, valid: np.ndarray) -> np.ndarray:
    palm = [idx for idx in PALM_CENTER_LANDMARKS if idx < len(valid) and bool(valid[idx])]
    if palm:
        return coords[palm].mean(axis=0).astype(np.float32)
    visible = np.where(valid)[0]
    if len(visible):
        return coords[visible].mean(axis=0).astype(np.float32)
    return np.zeros(3, dtype=np.float32)


def _dynamic_local_amplitude(
    seq: SequenceData,
    name: str,
    *,
    group: str,
    landmarks: Sequence[int],
    factor: float,
    profile: Any,
) -> tuple[SequenceData, Dict[str, Any]]:
    base = _strip_to_base_groups(seq)
    selected = [int(idx) for idx in landmarks]
    anchors: Dict[int, np.ndarray] = {}
    anchor_frame_indices: List[int] = []
    for frame in base.features:
        coords, valid = _hand_array(frame, group)
        if coords is None or valid is None or not valid.any():
            continue
        center = _visible_center(coords, valid)
        used = False
        for idx in selected:
            if idx < len(valid) and bool(valid[idx]) and idx not in anchors:
                anchors[idx] = coords[idx].copy() - center
                used = True
        if used:
            anchor_frame_indices.append(int(frame.frame_idx))
        if len(anchors) >= len(selected):
            break

    items: List[FrameFeature] = []
    changed_visible_points = 0
    selected_visible_points = 0
    for frame in base.features:
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        presence = dict(frame.presence)
        coords, valid = _hand_array(frame, group)
        if coords is not None and valid is not None and valid.any():
            coords = coords.copy()
            center = _visible_center(coords, valid)
            for idx in selected:
                if idx < len(valid) and bool(valid[idx]) and idx in anchors:
                    selected_visible_points += 1
                    local = coords[idx] - center
                    coords[idx] = center + anchors[idx] + float(factor) * (local - anchors[idx])
                    changed_visible_points += 1
            _set_hand_group(frame, vector, mask, group, coords, valid)
            presence[group] = bool(valid.any())
        item = _clone_frame(frame, vector=vector, mask=mask)
        item.presence = presence
        items.append(item)

    transformed = SequenceData(
        source=f"{base.source}::{name}",
        mode=base.mode,
        fps=base.fps,
        total_frames=base.total_frames,
        features=items,
    )
    detail = {
        "operation": "dynamic_local_amplitude",
        "group": group,
        "landmarks": selected,
        "factor": float(factor),
        "anchor_landmark_count": len(anchors),
        "anchor_frame_indices": anchor_frame_indices,
        "changed_visible_points": changed_visible_points,
        "selected_visible_points": selected_visible_points,
        "total_frames": len(base.features),
    }
    return _sequence_with_relative_motion_features(transformed, profile), detail


def _radial_local_spread(
    seq: SequenceData,
    name: str,
    *,
    group: str,
    landmarks: Sequence[int],
    factor: float,
    profile: Any,
) -> tuple[SequenceData, Dict[str, Any]]:
    base = _strip_to_base_groups(seq)
    selected = [int(idx) for idx in landmarks]
    items: List[FrameFeature] = []
    changed_visible_points = 0
    selected_visible_points = 0
    for frame in base.features:
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        presence = dict(frame.presence)
        coords, valid = _hand_array(frame, group)
        if coords is not None and valid is not None and valid.any():
            coords = coords.copy()
            center = _visible_center(coords, valid)
            for idx in selected:
                if idx < len(valid) and bool(valid[idx]):
                    selected_visible_points += 1
                    coords[idx] = center + float(factor) * (coords[idx] - center)
                    changed_visible_points += 1
            _set_hand_group(frame, vector, mask, group, coords, valid)
            presence[group] = bool(valid.any())
        item = _clone_frame(frame, vector=vector, mask=mask)
        item.presence = presence
        items.append(item)

    transformed = SequenceData(
        source=f"{base.source}::{name}",
        mode=base.mode,
        fps=base.fps,
        total_frames=base.total_frames,
        features=items,
    )
    detail = {
        "operation": "radial_local_spread",
        "group": group,
        "landmarks": selected,
        "factor": float(factor),
        "anchor_landmark_count": 0,
        "anchor_frame_indices": [],
        "changed_visible_points": changed_visible_points,
        "selected_visible_points": selected_visible_points,
        "total_frames": len(base.features),
    }
    return _sequence_with_relative_motion_features(transformed, profile), detail


def _spec(
    variant: str,
    kind: str,
    *,
    operation: str,
    group: str = "right_hand",
    landmarks: Sequence[int],
    factor: float,
    rationale: str,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": kind,
        "operation": operation,
        "group": group,
        "landmarks": [int(idx) for idx in landmarks],
        "factor": float(factor),
        "min_score": min_score,
        "max_score": max_score,
        "gated": kind in {"positive", "negative"},
        "rationale": rationale,
    }


def _variant_specs(word: str, min_score: float, negative_max_score: float) -> List[Dict[str, Any]]:
    specs = [
        _spec(
            "self_recomputed",
            "positive",
            operation="dynamic_local_amplitude",
            landmarks=[],
            factor=1.0,
            min_score=95.0,
            rationale="剥离基础组后重建 hand-shape/motion/relation 特征，应保持近满分。",
        )
    ]
    if word == "花":
        specs.extend(
            [
                _spec(
                    "flower_opening_dynamic_0.85",
                    "positive",
                    operation="dynamic_local_amplitude",
                    landmarks=FLOWER_DISTAL_LANDMARKS,
                    factor=0.85,
                    min_score=min_score,
                    rationale="右手绽放局部动态幅度压缩到 85%，仍应保持可评分。",
                ),
                _spec(
                    "flower_opening_dynamic_0.75",
                    "positive",
                    operation="dynamic_local_amplitude",
                    landmarks=FLOWER_DISTAL_LANDMARKS,
                    factor=0.75,
                    min_score=min_score,
                    rationale="右手绽放局部动态幅度压缩到 75%，覆盖用户开合偏小但清晰的情况。",
                ),
                _spec(
                    "flower_opening_dynamic_1.20",
                    "positive",
                    operation="dynamic_local_amplitude",
                    landmarks=FLOWER_DISTAL_LANDMARKS,
                    factor=1.20,
                    min_score=min_score,
                    rationale="右手绽放局部动态幅度放大到 120%，覆盖开合偏大的情况。",
                ),
                _spec(
                    "flower_tip_spread_radial_0.85",
                    "positive",
                    operation="radial_local_spread",
                    landmarks=FLOWER_TIPS,
                    factor=0.85,
                    min_score=min_score,
                    rationale="五个指尖展开半径略小，仍保留手指张开/绽放语义。",
                ),
                _spec(
                    "flower_tip_spread_radial_1.20",
                    "positive",
                    operation="radial_local_spread",
                    landmarks=FLOWER_TIPS,
                    factor=1.20,
                    min_score=min_score,
                    rationale="五个指尖展开半径略大，仍应保持正常或边界评分。",
                ),
                _spec(
                    "flower_opening_dynamic_0.60_diagnostic",
                    "diagnostic",
                    operation="dynamic_local_amplitude",
                    landmarks=FLOWER_DISTAL_LANDMARKS,
                    factor=0.60,
                    rationale="接近不开花的边界只记录诊断，避免把边界幅度当成正式正例。",
                ),
                _spec(
                    "flower_opening_dynamic_0.45_negative",
                    "negative",
                    operation="dynamic_local_amplitude",
                    landmarks=FLOWER_DISTAL_LANDMARKS,
                    factor=0.45,
                    max_score=negative_max_score,
                    rationale="绽放动态大幅塌缩，应低分或进入 flower_opening_guard_failed。",
                ),
                _spec(
                    "flower_opening_dynamic_0.25_negative",
                    "negative",
                    operation="dynamic_local_amplitude",
                    landmarks=FLOWER_DISTAL_LANDMARKS,
                    factor=0.25,
                    max_score=negative_max_score,
                    rationale="几乎没有手指张开/绽放动态，不能当作完整“花”通过。",
                ),
            ]
        )
    else:
        specs.extend(
            [
                _spec(
                    "jump_two_finger_dynamic_0.80",
                    "positive",
                    operation="dynamic_local_amplitude",
                    landmarks=JUMP_INDEX_MIDDLE_LANDMARKS,
                    factor=0.80,
                    min_score=min_score,
                    rationale="右手食指/中指小人的局部动态幅度略小，双手跳跃关系仍清晰。",
                ),
                _spec(
                    "jump_two_finger_dynamic_1.15",
                    "positive",
                    operation="dynamic_local_amplitude",
                    landmarks=JUMP_INDEX_MIDDLE_LANDMARKS,
                    factor=1.15,
                    min_score=min_score,
                    rationale="右手食指/中指小人的局部动态幅度略大，仍应保持可评分。",
                ),
                _spec(
                    "jump_two_finger_radial_0.90",
                    "positive",
                    operation="radial_local_spread",
                    landmarks=JUMP_INDEX_MIDDLE_LANDMARKS,
                    factor=0.90,
                    min_score=min_score,
                    rationale="两指小人局部展开略收，核心两指和左手地面关系仍保留。",
                ),
                _spec(
                    "jump_two_finger_radial_1.15",
                    "positive",
                    operation="radial_local_spread",
                    landmarks=JUMP_INDEX_MIDDLE_LANDMARKS,
                    factor=1.15,
                    min_score=min_score,
                    rationale="两指小人局部展开略放，核心关系仍应保持正常。",
                ),
                _spec(
                    "jump_two_finger_dynamic_0.45_diagnostic",
                    "diagnostic",
                    operation="dynamic_local_amplitude",
                    landmarks=JUMP_INDEX_MIDDLE_LANDMARKS,
                    factor=0.45,
                    rationale="严重两指局部动态压缩只记录当前边界；硬负例由遮挡/裁切/关系门覆盖。",
                ),
                _spec(
                    "jump_two_finger_radial_0.45_diagnostic",
                    "diagnostic",
                    operation="radial_local_spread",
                    landmarks=JUMP_INDEX_MIDDLE_LANDMARKS,
                    factor=0.45,
                    rationale="严重两指局部展开压缩只记录诊断，不作为当前硬负门。",
                ),
            ]
        )
    return specs


def _row_passed(row: Dict[str, Any]) -> bool:
    score = float(row["score"])
    if row["kind"] == "positive":
        return score >= float(row["min_score"])
    if row["kind"] == "negative":
        quality = (row.get("capture_quality") or {}).get("status")
        return score <= float(row["max_score"]) or quality in ACCEPTED_NEGATIVE_QUALITY
    return True


def _transform_from_spec(seq: SequenceData, spec: Dict[str, Any], profile: Any) -> tuple[SequenceData, Dict[str, Any]]:
    common = {
        "group": str(spec["group"]),
        "landmarks": spec.get("landmarks") or [],
        "factor": float(spec["factor"]),
        "profile": profile,
    }
    operation = str(spec["operation"])
    if operation == "dynamic_local_amplitude":
        return _dynamic_local_amplitude(seq, str(spec["variant"]), **common)
    if operation == "radial_local_spread":
        return _radial_local_spread(seq, str(spec["variant"]), **common)
    raise ValueError(f"unknown operation: {operation}")


def _run_word(
    word: str,
    template_root: Path,
    semantic_profile_json: Path,
    feature_mode: str,
    min_score: float,
    negative_max_score: float,
) -> Dict[str, Any]:
    standard_json = _template_json(template_root, word)
    loaded_standard = load_sequence(standard_json, feature_mode, force_bbox=False)
    profile = load_semantic_profile(word, semantic_profile_json)
    standard, standard_detail = _dynamic_local_amplitude(
        loaded_standard,
        "standard_base",
        group="right_hand",
        landmarks=[],
        factor=1.0,
        profile=profile,
    )
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(word, min_score, negative_max_score):
        query, detail = _transform_from_spec(loaded_standard, spec, profile)
        result = run_pair(standard, query, semantic_profile=profile, target_word=word, enable_cross_check=False)
        score_scale = result.get("score_scale") or {}
        flower_guard = score_scale.get("flower_opening_guard") or {}
        row = {
            "variant": spec["variant"],
            "kind": spec["kind"],
            "gated": bool(spec["gated"]),
            "min_score": spec.get("min_score"),
            "max_score": spec.get("max_score"),
            "rationale": spec["rationale"],
            **detail,
            "score": float(result["prototype_score"]),
            "dtw_distance": float(result["dtw_distance"]),
            "normalized_distance": float(result["normalized_distance"]),
            "alignment_policy": result.get("alignment_policy"),
            "capture_quality": score_scale.get("capture_quality"),
            "semantic_floor": score_scale.get("semantic_floor"),
            "flower_opening_guard": flower_guard,
            "flower_opening_score": flower_guard.get("best_score"),
            "action_window": result.get("action_window"),
        }
        row["passed"] = _row_passed(row)
        rows.append(row)

    positive_rows = [row for row in rows if row["kind"] == "positive"]
    negative_rows = [row for row in rows if row["kind"] == "negative"]
    diagnostic_rows = [row for row in rows if row["kind"] == "diagnostic"]
    weakest_positive = min(positive_rows, key=lambda row: float(row["score"])) if positive_rows else None
    strongest_negative = max(negative_rows, key=lambda row: float(row["score"])) if negative_rows else None
    weakest_diagnostic = min(diagnostic_rows, key=lambda row: float(row["score"])) if diagnostic_rows else None
    return {
        "word": word,
        "standard_json": str(standard_json),
        "standard_length": len(standard.features),
        "standard_transform_detail": standard_detail,
        "semantic_profile": _profile_summary(profile),
        "gate_pass": all(bool(row["passed"]) for row in rows if row["gated"]),
        "weakest_positive_score": float(weakest_positive["score"]) if weakest_positive else None,
        "weakest_positive_variant": weakest_positive["variant"] if weakest_positive else "",
        "strongest_negative_score": float(strongest_negative["score"]) if strongest_negative else None,
        "strongest_negative_variant": strongest_negative["variant"] if strongest_negative else "",
        "weakest_diagnostic_score": float(weakest_diagnostic["score"]) if weakest_diagnostic else None,
        "weakest_diagnostic_variant": weakest_diagnostic["variant"] if weakest_diagnostic else "",
        "min_required_score": min_score,
        "negative_max_score": negative_max_score,
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
        "operation",
        "group",
        "landmarks",
        "factor",
        "anchor_landmark_count",
        "changed_visible_points",
        "selected_visible_points",
        "flower_opening_score",
        "alignment_mode",
        "capture_quality_status",
        "capture_quality_reason",
        "semantic_floor_source",
        "semantic_floor_reason",
        "rationale",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in results:
            for row in item["variants"]:
                quality = row.get("capture_quality") or {}
                floor = row.get("semantic_floor") or {}
                policy = row.get("alignment_policy") or {}
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
                        "operation": row.get("operation"),
                        "group": row.get("group"),
                        "landmarks": ",".join(str(value) for value in (row.get("landmarks") or [])),
                        "factor": row.get("factor"),
                        "anchor_landmark_count": row.get("anchor_landmark_count"),
                        "changed_visible_points": row.get("changed_visible_points"),
                        "selected_visible_points": row.get("selected_visible_points"),
                        "flower_opening_score": row.get("flower_opening_score"),
                        "alignment_mode": policy.get("mode"),
                        "capture_quality_status": quality.get("status"),
                        "capture_quality_reason": quality.get("reason"),
                        "semantic_floor_source": floor.get("source"),
                        "semantic_floor_reason": floor.get("reason"),
                        "rationale": row.get("rationale"),
                    }
                )


def _build_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# 花/跳核心手形幅度鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，调整右手核心手指的局部开合/展开幅度并重建 hand-shape/motion/relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：`花` 的温和开花幅度变化保持高分，严重不开花低分或语义失败；`跳` 的两指小人温和局部形变保持高分，严重形变只记录诊断边界。",
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
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向核心形变 | 负向最高分 | 最强负向核心形变 | 诊断最低分 | 最弱诊断形变 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|---|---:|")
    for item in payload["results"]:
        lines.append(
            f"| {item['word']} | {'PASS' if item['gate_pass'] else 'FAIL'} | "
            f"{_fmt(item['weakest_positive_score'])} | {item['weakest_positive_variant']} | "
            f"{_fmt(item['strongest_negative_score'])} | {item['strongest_negative_variant'] or '-'} | "
            f"{_fmt(item['weakest_diagnostic_score'])} | {item['weakest_diagnostic_variant'] or '-'} | "
            f"{_fmt(item['min_required_score'])} |"
        )
    lines.append("")
    lines.append("## 分项明细")
    for item in payload["results"]:
        lines.extend(["", f"### {item['word']}", "", f"- 标准序列：`{item['standard_json']}`", ""])
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | 操作 | factor | 改动点数 | opening | capture_quality | semantic_floor | 说明 |")
        lines.append("|---|---|---|---:|---|---|---:|---:|---:|---|---|---|")
        for row in sorted(item["variants"], key=lambda value: (value["kind"], float(value["score"]))):
            quality = row.get("capture_quality") or {}
            floor = row.get("semantic_floor") or {}
            if row["kind"] == "positive":
                threshold = f">= {row.get('min_score')}"
                status = "PASS" if row["passed"] else "FAIL"
            elif row["kind"] == "negative":
                threshold = f"<= {row.get('max_score')} 或重采/语义失败"
                status = "PASS" if row["passed"] else "FAIL"
            else:
                threshold = "diagnostic"
                status = "DIAG"
            lines.append(
                f"| {row['variant']} | {row['kind']} | {status} | {_fmt(row['score'])} | "
                f"{threshold} | {row.get('operation') or '-'} | {_fmt(row.get('factor'))} | "
                f"{row.get('changed_visible_points')} | {_fmt(row.get('flower_opening_score'))} | "
                f"{quality.get('status') or '-'}:{quality.get('reason') or '-'} | "
                f"{floor.get('source') or '-'}:{floor.get('reason') or '-'} | {row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- `花` 的负向门允许 capture_quality 证明 `flower_opening_guard_failed`，因为语义失败比单一分数阈值更可靠。",
            "- `跳` 的严重两指形变目前只作诊断，不放宽也不新增硬负例；硬保护仍由遮挡、裁切、手角色、关系几何和相位顺序等门承担。",
            "- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run core hand-shape amplitude robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_core_shape_amplitude_robustness_gate_current"))
    parser.add_argument("--words", nargs="+", default=DEFAULT_WORDS)
    parser.add_argument("--feature-mode", choices=["auto", "landmark", "bbox"], default="auto")
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--status-timeout-sec", type=float, default=3.0)
    parser.add_argument("--min-score", type=float, default=70.0)
    parser.add_argument("--negative-max-score", type=float, default=45.0)
    args = parser.parse_args(argv)

    template_root = Path(args.template_root)
    semantic_profile_json = Path(args.semantic_profile_json)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    results = [
        _run_word(
            word=word,
            template_root=template_root,
            semantic_profile_json=semantic_profile_json,
            feature_mode=args.feature_mode,
            min_score=args.min_score,
            negative_max_score=args.negative_max_score,
        )
        for word in args.words
    ]
    backend_status = _load_backend_status(args.backend_url, args.status_timeout_sec)
    passed = all(bool(item["gate_pass"]) for item in results)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "claim_policy": "synthetic core hand-shape amplitude robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": backend_status,
        "passed": passed,
        "min_score": args.min_score,
        "negative_max_score": args.negative_max_score,
        "accepted_negative_quality": sorted(ACCEPTED_NEGATIVE_QUALITY),
        "results": results,
    }

    json_path = output_dir / "flower_jump_core_shape_amplitude_robustness_gate.json"
    md_path = output_dir / "flower_jump_core_shape_amplitude_robustness_gate.md"
    csv_path = output_dir / "flower_jump_core_shape_amplitude_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳核心手形幅度鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳核心手形幅度鲁棒性报告：{md_path}")
    print(f"已生成花/跳核心手形幅度鲁棒性 CSV：{csv_path}")
    print(f"综合状态：{'PASS' if passed else 'FAIL'}")
    for item in results:
        print(
            f"- {item['word']}: {'PASS' if item['gate_pass'] else 'FAIL'} "
            f"positive_min={_fmt(item['weakest_positive_score'])} "
            f"weakest={item['weakest_positive_variant']} "
            f"negative_max={_fmt(item['strongest_negative_score'])} "
            f"diagnostic_min={_fmt(item['weakest_diagnostic_score'])}"
        )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

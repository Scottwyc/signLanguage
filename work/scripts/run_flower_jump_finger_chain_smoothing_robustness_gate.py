#!/usr/bin/env python3
"""Stress-test flower/jump scoring against finger-chain temporal smoothing.

Low-resolution webcam capture and tracker stabilization can keep hand
landmarks visible and confident while smoothing only the distal finger chains
across nearby frames. This differs from whole-hand motion blur, frame stutter,
finger-chain latency, confidence attenuation, and occlusion: palm/wrist anchors
stay on the current frame, masks remain valid, landmark identity is preserved,
and only selected distal finger coordinates are low-pass filtered.

This script edits cached skeleton sequences in memory only. It does not call
/api/score, run Holistic, move the web marker, or restart 5080.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

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

THUMB_DISTAL = [2, 3, 4]
INDEX_DISTAL = [6, 7, 8]
MIDDLE_DISTAL = [10, 11, 12]
RING_DISTAL = [14, 15, 16]
PINKY_DISTAL = [18, 19, 20]
ALL_DISTAL = THUMB_DISTAL + INDEX_DISTAL + MIDDLE_DISTAL + RING_DISTAL + PINKY_DISTAL
INDEX_MIDDLE_DISTAL = INDEX_DISTAL + MIDDLE_DISTAL
OUTER_DISTAL = RING_DISTAL + PINKY_DISTAL


def _active_indices(pattern: str, length: int) -> Set[int]:
    if length <= 0:
        return set()
    if pattern == "none":
        return set()
    if pattern == "single_mid":
        return {length // 2}
    if pattern == "full":
        return set(range(length))
    if pattern == "sparse_every_5f":
        return {idx for idx in range(1, length - 1) if idx % 5 == 2}
    if pattern == "middle_20pct":
        start = int(round(length * 0.40))
        end = max(start + 1, int(round(length * 0.60)))
        return set(range(max(1, start), min(length - 1, end)))
    if pattern == "middle_35pct":
        start = int(round(length * 0.325))
        end = max(start + 1, int(round(length * 0.675)))
        return set(range(max(1, start), min(length - 1, end)))
    raise ValueError(f"unknown finger-chain smoothing pattern: {pattern}")


def _smoothed_landmark(
    frames: Sequence[FrameFeature],
    idx: int,
    *,
    group: str,
    landmark_idx: int,
    weights: Sequence[float],
) -> Tuple[Optional[np.ndarray], int]:
    radius = len(weights) // 2
    numerator = np.zeros(3, dtype=np.float32)
    denominator = 0.0
    used_sources = 0
    for offset, weight in enumerate(weights):
        src_idx = idx + offset - radius
        if src_idx < 0 or src_idx >= len(frames) or float(weight) <= 0.0:
            continue
        coords, valid = _hand_array(frames[src_idx], group)
        if coords is None or valid is None:
            continue
        if not 0 <= landmark_idx < len(valid) or not bool(valid[landmark_idx]):
            continue
        numerator += float(weight) * coords[landmark_idx].astype(np.float32)
        denominator += float(weight)
        used_sources += 1
    if denominator <= 1e-8:
        return None, used_sources
    return numerator / float(denominator), used_sources


def _smoothing_sequence(
    seq: SequenceData,
    name: str,
    *,
    group: str,
    landmarks: Sequence[int],
    weights: Sequence[float],
    strength: float,
    pattern: str,
    profile: Any,
) -> Tuple[SequenceData, Dict[str, Any]]:
    base = _strip_to_base_groups(seq)
    n = len(base.features)
    active = _active_indices(pattern, n)
    selected_landmarks = [int(item) for item in landmarks]
    weights_list = [float(item) for item in weights]
    features: List[FrameFeature] = []
    changed_frames = 0
    changed_points = 0
    skipped_points = 0
    source_counts: List[int] = []

    for idx, frame in enumerate(base.features):
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        presence = dict(frame.presence)
        frame_changed = False
        if idx in active and selected_landmarks:
            coords, valid = _hand_array(frame, group)
            if coords is not None and valid is not None and bool(valid.any()):
                coords = coords.copy()
                valid = valid.copy()
                for landmark_idx in selected_landmarks:
                    if not 0 <= landmark_idx < len(valid) or not bool(valid[landmark_idx]):
                        skipped_points += 1
                        continue
                    target, used_sources = _smoothed_landmark(
                        base.features,
                        idx,
                        group=group,
                        landmark_idx=landmark_idx,
                        weights=weights_list,
                    )
                    source_counts.append(used_sources)
                    if target is None or used_sources <= 1:
                        skipped_points += 1
                        continue
                    updated = coords[landmark_idx] + float(strength) * (target - coords[landmark_idx])
                    if float(np.linalg.norm(updated - coords[landmark_idx])) > 1e-8:
                        coords[landmark_idx] = updated.astype(np.float32)
                        changed_points += 1
                        frame_changed = True
                    else:
                        skipped_points += 1
                _set_hand_group(frame, vector, mask, group, coords, valid)
                presence[group] = bool(valid.any())
        if frame_changed:
            changed_frames += 1
        item = _clone_frame(frame, vector=vector, mask=mask)
        item.presence = presence
        features.append(item)

    transformed = SequenceData(
        source=f"{base.source}::{name}",
        mode=base.mode,
        fps=base.fps,
        total_frames=base.total_frames,
        features=features,
    )
    detail = {
        "operation": "finger_chain_temporal_smoothing",
        "group": group,
        "landmarks": selected_landmarks,
        "weights": weights_list,
        "strength": float(strength),
        "pattern": pattern,
        "active_frame_count": len(active),
        "changed_frames": changed_frames,
        "changed_points": changed_points,
        "skipped_points": skipped_points,
        "mean_source_count": float(np.mean(source_counts)) if source_counts else None,
        "total_frames": n,
    }
    return _sequence_with_relative_motion_features(transformed, profile), detail


def _spec(
    variant: str,
    kind: str,
    *,
    group: str,
    landmarks: Sequence[int],
    weights: Sequence[float],
    strength: float,
    pattern: str,
    rationale: str,
    min_score: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": kind,
        "group": group,
        "landmarks": [int(item) for item in landmarks],
        "weights": [float(item) for item in weights],
        "strength": float(strength),
        "pattern": pattern,
        "min_score": min_score,
        "gated": kind == "positive",
        "rationale": rationale,
    }


def _variant_specs(word: str, min_score: float) -> List[Dict[str, Any]]:
    kernel_3 = [0.25, 0.50, 0.25]
    kernel_5 = [0.10, 0.20, 0.40, 0.20, 0.10]
    heavy_5 = [0.16, 0.22, 0.24, 0.22, 0.16]
    specs = [
        _spec(
            "self_recomputed",
            "positive",
            group="right_hand",
            landmarks=[],
            weights=[1.0],
            strength=0.0,
            pattern="none",
            min_score=95.0,
            rationale="标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。",
        )
    ]
    if word == "花":
        specs.extend(
            [
                _spec(
                    "flower_right_all_distal_3tap_strength_0p35_full",
                    "positive",
                    group="right_hand",
                    landmarks=ALL_DISTAL,
                    weights=kernel_3,
                    strength=0.35,
                    pattern="full",
                    min_score=min_score,
                    rationale="开花核心手所有 distal finger chains 全程轻度 3 帧平滑，模拟 tracker 稳定化但保留开合轨迹。",
                ),
                _spec(
                    "flower_right_all_distal_5tap_strength_0p45_sparse",
                    "positive",
                    group="right_hand",
                    landmarks=ALL_DISTAL,
                    weights=kernel_5,
                    strength=0.45,
                    pattern="sparse_every_5f",
                    min_score=min_score,
                    rationale="开花核心手稀疏帧 5 帧平滑，模拟低 FPS 选帧处的局部 finger-chain 黏连。",
                ),
                _spec(
                    "flower_right_outer_distal_3tap_strength_0p55_middle20",
                    "positive",
                    group="right_hand",
                    landmarks=OUTER_DISTAL,
                    weights=kernel_3,
                    strength=0.55,
                    pattern="middle_20pct",
                    min_score=min_score,
                    rationale="开花右手外侧 ring/pinky distal chains 短核心窗口平滑，完整开花证据仍应可评分。",
                ),
                _spec(
                    "flower_right_all_distal_3tap_strength_0p50_middle20",
                    "positive",
                    group="right_hand",
                    landmarks=ALL_DISTAL,
                    weights=kernel_3,
                    strength=0.50,
                    pattern="middle_20pct",
                    min_score=min_score,
                    rationale="开花短核心窗口所有 distal finger chains 中度平滑，覆盖较明显但局部的 tracker smoothing。",
                ),
                _spec(
                    "flower_right_all_distal_heavy5_strength_1p00_full_diagnostic",
                    "diagnostic",
                    group="right_hand",
                    landmarks=ALL_DISTAL,
                    weights=heavy_5,
                    strength=1.0,
                    pattern="full",
                    rationale="诊断记录：开花核心手所有 distal finger chains 全程强低通时的边界分。",
                ),
            ]
        )
    elif word == "跳":
        specs.extend(
            [
                _spec(
                    "jump_right_person_distal_3tap_strength_0p35_full",
                    "positive",
                    group="right_hand",
                    landmarks=INDEX_MIDDLE_DISTAL,
                    weights=kernel_3,
                    strength=0.35,
                    pattern="full",
                    min_score=min_score,
                    rationale="跳的右手两指小人 distal chains 全程轻度 3 帧平滑，跳跃轨迹和双手关系仍完整。",
                ),
                _spec(
                    "jump_left_ground_distal_3tap_strength_0p35_full",
                    "positive",
                    group="left_hand",
                    landmarks=ALL_DISTAL,
                    weights=kernel_3,
                    strength=0.35,
                    pattern="full",
                    min_score=min_score,
                    rationale="跳的左手地面手 distal chains 全程轻度平滑，右手小人和关系语义仍应稳定。",
                ),
                _spec(
                    "jump_right_person_distal_5tap_strength_0p45_sparse",
                    "positive",
                    group="right_hand",
                    landmarks=INDEX_MIDDLE_DISTAL,
                    weights=kernel_5,
                    strength=0.45,
                    pattern="sparse_every_5f",
                    min_score=min_score,
                    rationale="跳的右手两指小人稀疏帧 5 帧平滑，模拟 tracker 局部时间黏连。",
                ),
                _spec(
                    "jump_right_person_distal_3tap_strength_0p50_middle20",
                    "positive",
                    group="right_hand",
                    landmarks=INDEX_MIDDLE_DISTAL,
                    weights=kernel_3,
                    strength=0.50,
                    pattern="middle_20pct",
                    min_score=min_score,
                    rationale="跳的右手两指核心短窗口中度平滑，仍应保留弹跳语义。",
                ),
                _spec(
                    "jump_right_person_distal_heavy5_strength_1p00_full_diagnostic",
                    "diagnostic",
                    group="right_hand",
                    landmarks=INDEX_MIDDLE_DISTAL,
                    weights=heavy_5,
                    strength=1.0,
                    pattern="full",
                    rationale="诊断记录：右手两指小人全程强低通时的边界分。",
                ),
                _spec(
                    "jump_right_person_distal_heavy5_strength_0p85_middle35_diagnostic",
                    "diagnostic",
                    group="right_hand",
                    landmarks=INDEX_MIDDLE_DISTAL,
                    weights=heavy_5,
                    strength=0.85,
                    pattern="middle_35pct",
                    rationale="诊断记录：右手两指小人较长核心窗口强平滑时的边界分。",
                ),
            ]
        )
    return specs


def _row_passed(row: Dict[str, Any]) -> bool:
    if row["kind"] == "positive":
        return float(row["score"]) >= float(row["min_score"])
    return True


def _run_word(
    word: str,
    template_root: Path,
    semantic_profile_json: Path,
    feature_mode: str,
    min_score: float,
) -> Dict[str, Any]:
    standard_json = _template_json(template_root, word)
    loaded_standard = load_sequence(standard_json, feature_mode, force_bbox=False)
    profile = load_semantic_profile(word, semantic_profile_json)
    standard, standard_detail = _smoothing_sequence(
        loaded_standard,
        "standard_base",
        group="right_hand",
        landmarks=[],
        weights=[1.0],
        strength=0.0,
        pattern="none",
        profile=profile,
    )
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(word, min_score):
        query, detail = _smoothing_sequence(
            loaded_standard,
            str(spec["variant"]),
            group=str(spec["group"]),
            landmarks=spec["landmarks"],
            weights=spec["weights"],
            strength=float(spec["strength"]),
            pattern=str(spec["pattern"]),
            profile=profile,
        )
        result = run_pair(standard, query, semantic_profile=profile, target_word=word, enable_cross_check=False)
        score_scale = result.get("score_scale") or {}
        row = {
            "variant": spec["variant"],
            "kind": spec["kind"],
            "gated": bool(spec["gated"]),
            "min_score": spec.get("min_score"),
            "rationale": spec["rationale"],
            **detail,
            "score": float(result["prototype_score"]),
            "dtw_distance": float(result["dtw_distance"]),
            "normalized_distance": float(result["normalized_distance"]),
            "alignment_policy": result.get("alignment_policy"),
            "capture_quality": score_scale.get("capture_quality"),
            "semantic_floor": score_scale.get("semantic_floor"),
            "action_window": result.get("action_window"),
        }
        row["passed"] = _row_passed(row)
        rows.append(row)
    positive_rows = [row for row in rows if row["kind"] == "positive"]
    diagnostic_rows = [row for row in rows if row["kind"] == "diagnostic"]
    weakest_positive = min(positive_rows, key=lambda row: float(row["score"])) if positive_rows else None
    weakest_diagnostic = min(diagnostic_rows, key=lambda row: float(row["score"])) if diagnostic_rows else None
    return {
        "word": word,
        "standard_json": str(standard_json),
        "standard_length": len(standard.features),
        "standard_mutation_detail": standard_detail,
        "semantic_profile": _profile_summary(profile),
        "gate_pass": all(bool(row["passed"]) for row in rows if row["gated"]),
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
        "group",
        "landmarks",
        "weights",
        "strength",
        "pattern",
        "active_frame_count",
        "changed_frames",
        "changed_points",
        "skipped_points",
        "mean_source_count",
        "total_frames",
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
                        "group": row.get("group"),
                        "landmarks": row.get("landmarks"),
                        "weights": row.get("weights"),
                        "strength": row.get("strength"),
                        "pattern": row.get("pattern"),
                        "active_frame_count": row.get("active_frame_count"),
                        "changed_frames": row.get("changed_frames"),
                        "changed_points": row.get("changed_points"),
                        "skipped_points": row.get("skipped_points"),
                        "mean_source_count": row.get("mean_source_count"),
                        "total_frames": row.get("total_frames"),
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
        "# 花/跳手指链时间平滑鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，只对选定 distal finger chains 做短窗口时间低通，wrist/MCP/palm anchors 保持当前帧，mask 和 landmark 身份不变；随后重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：轻度、稀疏或短窗口 finger-chain smoothing 仍可正常评分；持续强低通只记录诊断边界，因为它可能真实抹掉手形相位。",
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
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向平滑 | 诊断最低分 | 最弱诊断边界 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for item in payload["results"]:
        lines.append(
            f"| {item['word']} | {'PASS' if item['gate_pass'] else 'FAIL'} | "
            f"{_fmt(item['weakest_positive_score'])} | {item['weakest_positive_variant']} | "
            f"{_fmt(item['weakest_diagnostic_score'])} | {item['weakest_diagnostic_variant'] or '-'} | "
            f"{_fmt(item['min_required_score'])} |"
        )
    lines.append("")
    lines.append("## 分项明细")
    for item in payload["results"]:
        lines.extend(["", f"### {item['word']}", "", f"- 标准序列：`{item['standard_json']}`", ""])
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | group | landmarks | strength | pattern | 改动帧 | 改动点 | source均值 | capture_quality | semantic_floor | 说明 |")
        lines.append("|---|---|---|---:|---|---|---|---:|---|---:|---:|---:|---|---|---|")
        for row in sorted(item["variants"], key=lambda value: (value["kind"], float(value["score"]))):
            quality = row.get("capture_quality") or {}
            floor = row.get("semantic_floor") or {}
            if row["kind"] == "positive":
                threshold = f">= {row.get('min_score')}"
                status = "PASS" if row["passed"] else "FAIL"
            else:
                threshold = "diagnostic"
                status = "DIAG"
            lines.append(
                f"| {row['variant']} | {row['kind']} | {status} | {_fmt(row['score'])} | "
                f"{threshold} | {row.get('group')} | {row.get('landmarks')} | "
                f"{_fmt(row.get('strength'))} | {row.get('pattern')} | {row.get('changed_frames')} | "
                f"{row.get('changed_points')} | {_fmt(row.get('mean_source_count'))} | "
                f"{quality.get('status') or '-'}:{quality.get('reason') or '-'} | "
                f"{floor.get('source') or '-'}:{floor.get('reason') or '-'} | {row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 该门补充的是同一手内部 distal finger-chain 坐标被时间平滑，不替代 motion-blur、finger-chain latency、confidence attenuation、occlusion、stutter 或 interpolation 门。",
            "- 持续强平滑可能真实移除 `花` 的开合或 `跳` 的两指弹跳相位，本轮只作为诊断边界；是否升级硬负例需要真实网页样本或人工标签。",
            "- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run finger-chain temporal smoothing robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_finger_chain_smoothing_robustness_gate_current"))
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
    results = [
        _run_word(
            word=word,
            template_root=template_root,
            semantic_profile_json=semantic_profile_json,
            feature_mode=args.feature_mode,
            min_score=args.min_score,
        )
        for word in args.words
    ]
    backend_status = _load_backend_status(args.backend_url, args.status_timeout_sec)
    passed = all(bool(item["gate_pass"]) for item in results)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "claim_policy": "synthetic finger-chain temporal smoothing robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": backend_status,
        "passed": passed,
        "min_score": args.min_score,
        "results": results,
    }

    json_path = output_dir / "flower_jump_finger_chain_smoothing_robustness_gate.json"
    md_path = output_dir / "flower_jump_finger_chain_smoothing_robustness_gate.md"
    csv_path = output_dir / "flower_jump_finger_chain_smoothing_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳手指链时间平滑鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳手指链时间平滑鲁棒性报告：{md_path}")
    print(f"已生成花/跳手指链时间平滑鲁棒性 CSV：{csv_path}")
    print(f"综合状态：{'PASS' if passed else 'FAIL'}")
    for item in results:
        print(
            f"- {item['word']}: {'PASS' if item['gate_pass'] else 'FAIL'} "
            f"positive_min={_fmt(item['weakest_positive_score'])} "
            f"weakest={item['weakest_positive_variant']} "
            f"diagnostic_min={_fmt(item['weakest_diagnostic_score'])}"
        )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

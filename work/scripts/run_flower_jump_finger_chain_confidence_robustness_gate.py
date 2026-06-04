#!/usr/bin/env python3
"""Stress-test flower/jump scoring against per-finger soft confidence loss.

Hard missing-mask and fingertip/mid-joint occlusion gates cover coordinates
that disappear. Whole-hand confidence attenuation covers the entire hand mask
dropping together. Webcam tracking can also keep coordinates for a specific
finger chain while only that chain's confidence is near the valid threshold.
This gate attenuates selected finger-chain mask values while preserving
coordinates, landmark identity, and the rest of the hand.

This script edits cached skeleton sequences in memory only. It does not call
/api/score, run Holistic, move the web marker, or restart 5080.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set

import numpy as np

from run_flower_jump_mirror_robustness_gate import _strip_to_base_groups, _template_json
from run_flower_jump_temporal_rate_robustness_gate import (
    _fmt,
    _json_default,
    _load_backend_status,
    _rebuild_derived_groups,
)
from score_holistic_sequence_mvp import (
    DEFAULT_SEMANTIC_PROFILE_JSON,
    FrameFeature,
    SequenceData,
    _clone_frame,
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

FINGER_CHAINS: Dict[str, List[int]] = {
    "thumb": [1, 2, 3, 4],
    "index": [5, 6, 7, 8],
    "middle": [9, 10, 11, 12],
    "ring": [13, 14, 15, 16],
    "pinky": [17, 18, 19, 20],
}
OUTER_FINGERS = ["ring", "pinky"]
PERSON_FINGERS = ["index", "middle"]
ALL_FINGERS = ["thumb", "index", "middle", "ring", "pinky"]


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
    raise ValueError(f"unknown finger-chain confidence pattern: {pattern}")


def _presence_from_mask(frame: FrameFeature) -> Dict[str, bool]:
    presence = dict(frame.presence)
    for group in ["pose", "left_hand", "right_hand", "face"]:
        if group not in frame.groups:
            presence[group] = False
            continue
        sl = frame.groups[group]
        presence[group] = bool(float(frame.mask[sl].mean()) >= 0.35)
    return presence


def _scale_landmark_mask(mask: np.ndarray, frame: FrameFeature, group: str, landmark_idx: int, scale: float) -> bool:
    if group not in frame.groups:
        return False
    sl = frame.groups[group]
    values = mask[sl]
    if values.size % 3 != 0:
        return False
    point_count = values.size // 3
    if not 0 <= landmark_idx < point_count:
        return False
    start = sl.start + landmark_idx * 3
    end = start + 3
    before = mask[start:end].copy()
    mask[start:end] = np.clip(mask[start:end] * float(scale), 0.0, 1.0).astype(np.float32)
    return bool(np.any(before > 0))


def _attenuate_sequence(
    seq: SequenceData,
    name: str,
    *,
    group: str,
    fingers: Sequence[str],
    scale: float,
    pattern: str,
    profile: Any,
) -> tuple[SequenceData, Dict[str, Any]]:
    base = _strip_to_base_groups(seq)
    active = _active_indices(pattern, len(base.features))
    selected_fingers = [str(item) for item in fingers]
    selected_landmarks: List[int] = []
    for finger in selected_fingers:
        selected_landmarks.extend(FINGER_CHAINS.get(finger, []))
    features: List[FrameFeature] = []
    changed_frames = 0
    attenuated_points = 0
    skipped_points = 0
    for idx, frame in enumerate(base.features):
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        frame_changed = False
        if idx in active and selected_landmarks:
            for landmark_idx in selected_landmarks:
                if _scale_landmark_mask(mask, frame, group, int(landmark_idx), scale):
                    attenuated_points += 1
                    frame_changed = True
                else:
                    skipped_points += 1
        item = _clone_frame(frame, vector=vector, mask=mask)
        item.presence = _presence_from_mask(item)
        features.append(item)
        if frame_changed:
            changed_frames += 1
    transformed = SequenceData(
        source=f"{base.source}::{name}",
        mode=base.mode,
        fps=base.fps,
        total_frames=base.total_frames,
        features=features,
    )
    detail = {
        "operation": "finger_chain_confidence",
        "group": group,
        "fingers": selected_fingers,
        "landmarks": selected_landmarks,
        "scale": float(scale),
        "pattern": pattern,
        "active_frame_count": len(active),
        "changed_frames": changed_frames,
        "attenuated_points": attenuated_points,
        "skipped_points": skipped_points,
        "total_frames": len(base.features),
    }
    return _rebuild_derived_groups(transformed, profile), detail


def _presence_ratio(seq: SequenceData) -> Dict[str, float]:
    if not seq.features:
        return {"pose": 0.0, "left_hand": 0.0, "right_hand": 0.0, "face": 0.0}
    return {
        group: sum(1 for item in seq.features if item.presence.get(group)) / len(seq.features)
        for group in ["pose", "left_hand", "right_hand", "face"]
    }


def _mean_group_mask(seq: SequenceData, group: str) -> Optional[float]:
    values: List[float] = []
    for item in seq.features:
        if group not in item.groups:
            continue
        sl = item.groups[group]
        values.append(float(item.mask[sl].mean()))
    if not values:
        return None
    return float(np.mean(values))


def _spec(
    variant: str,
    kind: str,
    *,
    group: str,
    fingers: Sequence[str],
    scale: float,
    pattern: str,
    rationale: str,
    min_score: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": kind,
        "group": group,
        "fingers": [str(item) for item in fingers],
        "scale": float(scale),
        "pattern": pattern,
        "min_score": min_score,
        "gated": kind == "positive",
        "rationale": rationale,
    }


def _variant_specs(word: str, min_score: float) -> List[Dict[str, Any]]:
    specs = [
        _spec(
            "self_recomputed",
            "positive",
            group="right_hand",
            fingers=[],
            scale=1.0,
            pattern="none",
            min_score=95.0,
            rationale="标准序列剥离基础组后重建 motion/relation，应保持近满分。",
        )
    ]
    if word == "花":
        specs.extend(
            [
                _spec(
                    "flower_right_all_fingers_confidence_0p85_full",
                    "positive",
                    group="right_hand",
                    fingers=ALL_FINGERS,
                    scale=0.85,
                    pattern="full",
                    min_score=min_score,
                    rationale="开花核心手所有手指链全程轻度低置信，但坐标完整。",
                ),
                _spec(
                    "flower_right_all_fingers_confidence_0p65_middle20",
                    "positive",
                    group="right_hand",
                    fingers=ALL_FINGERS,
                    scale=0.65,
                    pattern="middle_20pct",
                    min_score=min_score,
                    rationale="开花核心窗口所有手指链中度低置信，仍高于有效阈值。",
                ),
                _spec(
                    "flower_right_outer_fingers_confidence_0p55_sparse",
                    "positive",
                    group="right_hand",
                    fingers=OUTER_FINGERS,
                    scale=0.55,
                    pattern="sparse_every_5f",
                    min_score=min_score,
                    rationale="开花 ring/pinky 指链稀疏帧 near-threshold 低置信，完整绽放证据仍应保留。",
                ),
                _spec(
                    "flower_right_index_middle_confidence_0p55_single_mid",
                    "positive",
                    group="right_hand",
                    fingers=PERSON_FINGERS,
                    scale=0.55,
                    pattern="single_mid",
                    min_score=min_score,
                    rationale="开花 index/middle 指链单帧 near-threshold 低置信，模拟瞬时手指置信跳变。",
                ),
                _spec(
                    "flower_right_all_fingers_confidence_0p51_middle35_diagnostic",
                    "diagnostic",
                    group="right_hand",
                    fingers=ALL_FINGERS,
                    scale=0.51,
                    pattern="middle_35pct",
                    rationale="诊断记录：开花核心手所有手指链较长窗口接近有效阈值时的边界分。",
                ),
            ]
        )
    elif word == "跳":
        specs.extend(
            [
                _spec(
                    "jump_right_person_fingers_confidence_0p85_full",
                    "positive",
                    group="right_hand",
                    fingers=PERSON_FINGERS,
                    scale=0.85,
                    pattern="full",
                    min_score=min_score,
                    rationale="跳的右手两指小人 index/middle 全程轻度低置信，双手关系和坐标仍完整。",
                ),
                _spec(
                    "jump_right_person_fingers_confidence_0p65_full",
                    "positive",
                    group="right_hand",
                    fingers=PERSON_FINGERS,
                    scale=0.65,
                    pattern="full",
                    min_score=min_score,
                    rationale="跳的右手两指小人全程中度低置信，仍高于关系/手形有效阈值。",
                ),
                _spec(
                    "jump_right_person_fingers_confidence_0p55_sparse",
                    "positive",
                    group="right_hand",
                    fingers=PERSON_FINGERS,
                    scale=0.55,
                    pattern="sparse_every_5f",
                    min_score=min_score,
                    rationale="跳的右手两指小人稀疏帧 near-threshold 低置信，跳跃轨迹仍应保留。",
                ),
                _spec(
                    "jump_left_ground_fingers_confidence_0p65_middle20",
                    "positive",
                    group="left_hand",
                    fingers=ALL_FINGERS,
                    scale=0.65,
                    pattern="middle_20pct",
                    min_score=min_score,
                    rationale="跳的左手地面手核心短窗口手指链中度低置信，右手小人和双手关系仍应稳定。",
                ),
                _spec(
                    "jump_right_person_fingers_confidence_0p51_middle35_diagnostic",
                    "diagnostic",
                    group="right_hand",
                    fingers=PERSON_FINGERS,
                    scale=0.51,
                    pattern="middle_35pct",
                    rationale="诊断记录：右手两指小人较长窗口接近有效阈值时的边界分。",
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
    standard, standard_detail = _attenuate_sequence(
        loaded_standard,
        "standard_base",
        group="right_hand",
        fingers=[],
        scale=1.0,
        pattern="none",
        profile=profile,
    )
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(word, min_score):
        query, detail = _attenuate_sequence(
            loaded_standard,
            str(spec["variant"]),
            group=str(spec["group"]),
            fingers=spec["fingers"],
            scale=float(spec["scale"]),
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
            "query_presence": _presence_ratio(query),
            "mean_left_hand_mask": _mean_group_mask(query, "left_hand"),
            "mean_right_hand_mask": _mean_group_mask(query, "right_hand"),
            "mean_left_shape_mask": _mean_group_mask(query, "left_hand_shape"),
            "mean_right_shape_mask": _mean_group_mask(query, "right_hand_shape"),
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
        "standard_presence": _presence_ratio(standard),
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
        "fingers",
        "landmarks",
        "scale",
        "pattern",
        "active_frame_count",
        "changed_frames",
        "attenuated_points",
        "skipped_points",
        "total_frames",
        "left_hand_presence",
        "right_hand_presence",
        "mean_left_hand_mask",
        "mean_right_hand_mask",
        "mean_left_shape_mask",
        "mean_right_shape_mask",
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
                presence = row.get("query_presence") or {}
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
                        "fingers": row.get("fingers"),
                        "landmarks": row.get("landmarks"),
                        "scale": row.get("scale"),
                        "pattern": row.get("pattern"),
                        "active_frame_count": row.get("active_frame_count"),
                        "changed_frames": row.get("changed_frames"),
                        "attenuated_points": row.get("attenuated_points"),
                        "skipped_points": row.get("skipped_points"),
                        "total_frames": row.get("total_frames"),
                        "left_hand_presence": presence.get("left_hand"),
                        "right_hand_presence": presence.get("right_hand"),
                        "mean_left_hand_mask": row.get("mean_left_hand_mask"),
                        "mean_right_hand_mask": row.get("mean_right_hand_mask"),
                        "mean_left_shape_mask": row.get("mean_left_shape_mask"),
                        "mean_right_shape_mask": row.get("mean_right_shape_mask"),
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
        "# 花/跳手指链软置信鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，保留坐标和 landmark 身份，只降低选定 finger-chain 的 hand mask 权重，并重建 motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：覆盖网页摄像头中特定手指链可见但置信度 near-threshold 的软 mask 场景；严重低置信只记录诊断边界。",
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
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向低置信 | 诊断最低分 | 最弱诊断边界 | 门槛 |")
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
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | group | fingers | scale | pattern | 改动帧 | 衰减点 | L/R mask | capture_quality | semantic_floor | 说明 |")
        lines.append("|---|---|---|---:|---|---|---|---:|---|---:|---:|---|---|---|---|")
        for row in sorted(item["variants"], key=lambda value: (value["kind"], float(value["score"]))):
            quality = row.get("capture_quality") or {}
            floor = row.get("semantic_floor") or {}
            if row["kind"] == "positive":
                threshold = f">= {row.get('min_score')}"
                status = "PASS" if row["passed"] else "FAIL"
            else:
                threshold = "diagnostic"
                status = "DIAG"
            lr_mask = f"{_fmt(row.get('mean_left_hand_mask'))}/{_fmt(row.get('mean_right_hand_mask'))}"
            lines.append(
                f"| {row['variant']} | {row['kind']} | {status} | {_fmt(row['score'])} | "
                f"{threshold} | {row.get('group')} | {row.get('fingers')} | {_fmt(row.get('scale'))} | "
                f"{row.get('pattern')} | {row.get('changed_frames')} | {row.get('attenuated_points')} | "
                f"{lr_mask} | {quality.get('status') or '-'}:{quality.get('reason') or '-'} | "
                f"{floor.get('source') or '-'}:{floor.get('reason') or '-'} | {row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 该门补充的是 finger-chain 级软置信衰减，不替代整手置信度衰减、missing/mask、fingertip/mid-joint occlusion 或 hand dropout burst 门。",
            "- 正向变体只覆盖 mild/near-threshold 低置信；低于有效阈值的严重情况应由缺失/重采诊断处理。",
            "- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run finger-chain confidence robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_finger_chain_confidence_robustness_gate_current"))
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
        "claim_policy": "synthetic finger-chain confidence robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": backend_status,
        "passed": passed,
        "min_score": args.min_score,
        "results": results,
    }

    json_path = output_dir / "flower_jump_finger_chain_confidence_robustness_gate.json"
    md_path = output_dir / "flower_jump_finger_chain_confidence_robustness_gate.md"
    csv_path = output_dir / "flower_jump_finger_chain_confidence_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳手指链软置信鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳手指链软置信鲁棒性报告：{md_path}")
    print(f"已生成花/跳手指链软置信鲁棒性 CSV：{csv_path}")
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

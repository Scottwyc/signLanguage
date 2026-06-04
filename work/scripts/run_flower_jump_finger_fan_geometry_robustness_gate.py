#!/usr/bin/env python3
"""Stress-test flower/jump scoring against finger fan-geometry drift.

Webcam/Holistic tracking can keep finger landmarks visible and consistently
labeled while squeezing or spreading adjacent finger chains in the image plane.
This is different from finger identity swaps, curl/length style changes,
occlusion, hand detail loss, or finger-chain latency: landmark identity and
presence stay intact, wrist/MCP/palm anchors stay on the current frame, and
only distal inter-finger fan geometry is compressed/spread.

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

FINGER_CHAINS: Dict[str, List[int]] = {
    "thumb": [2, 3, 4],
    "index": [6, 7, 8],
    "middle": [10, 11, 12],
    "ring": [14, 15, 16],
    "pinky": [18, 19, 20],
}
INNER_PAIR = [("index", "middle")]
OUTER_PAIR = [("ring", "pinky")]
NONOVERLAP_FAN_PAIRS = [("index", "middle"), ("ring", "pinky")]
WIDE_FAN_PAIRS = [("thumb", "index"), ("middle", "ring")]
FULL_FAN_PAIRS = [("thumb", "index"), ("index", "middle"), ("middle", "ring"), ("ring", "pinky")]


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
    raise ValueError(f"unknown finger fan-geometry pattern: {pattern}")


def _chain_center(coords: np.ndarray, valid: np.ndarray, chain: Sequence[int]) -> Optional[np.ndarray]:
    usable = [idx for idx in chain if 0 <= idx < len(valid) and bool(valid[idx])]
    if not usable:
        return None
    return coords[usable].mean(axis=0)


def _fan_sequence(
    seq: SequenceData,
    name: str,
    *,
    group: str,
    pairs: Sequence[Tuple[str, str]],
    alpha: float,
    mode: str,
    pattern: str,
    profile: Any,
) -> Tuple[SequenceData, Dict[str, Any]]:
    base = _strip_to_base_groups(seq)
    n = len(base.features)
    active = _active_indices(pattern, n)
    selected_pairs = [(str(left), str(right)) for left, right in pairs]
    features: List[FrameFeature] = []
    changed_frames = 0
    changed_points = 0
    changed_pairs = 0
    skipped_pairs = 0

    for idx, frame in enumerate(base.features):
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        presence = dict(frame.presence)
        frame_changed = False
        if idx in active and selected_pairs:
            coords, valid = _hand_array(frame, group)
            if coords is not None and valid is not None and bool(valid.any()):
                coords = coords.copy()
                valid = valid.copy()
                deltas = np.zeros_like(coords)
                touched: Set[int] = set()
                centers = {
                    finger: _chain_center(coords, valid, chain)
                    for finger, chain in FINGER_CHAINS.items()
                }
                for left, right in selected_pairs:
                    left_chain = FINGER_CHAINS.get(left)
                    right_chain = FINGER_CHAINS.get(right)
                    left_center = centers.get(left)
                    right_center = centers.get(right)
                    if not left_chain or not right_chain or left_center is None or right_center is None:
                        skipped_pairs += 1
                        continue
                    vector_lr = (right_center - left_center).astype(np.float32)
                    vector_lr[2] = 0.0
                    if mode == "compress":
                        left_delta = float(alpha) * vector_lr
                        right_delta = -float(alpha) * vector_lr
                    elif mode == "spread":
                        left_delta = -float(alpha) * vector_lr
                        right_delta = float(alpha) * vector_lr
                    elif mode == "cross":
                        left_delta = float(alpha) * vector_lr
                        right_delta = -float(alpha) * vector_lr
                    else:
                        raise ValueError(f"unknown finger fan-geometry mode: {mode}")
                    for landmark_idx in left_chain:
                        if 0 <= landmark_idx < len(valid) and bool(valid[landmark_idx]):
                            deltas[landmark_idx] += left_delta
                            touched.add(landmark_idx)
                    for landmark_idx in right_chain:
                        if 0 <= landmark_idx < len(valid) and bool(valid[landmark_idx]):
                            deltas[landmark_idx] += right_delta
                            touched.add(landmark_idx)
                    changed_pairs += 1
                if touched:
                    touched_list = sorted(touched)
                    coords[touched_list] = coords[touched_list] + deltas[touched_list]
                    changed_points += len(touched_list)
                    frame_changed = True
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
        "operation": "finger_fan_geometry",
        "group": group,
        "pairs": selected_pairs,
        "alpha": float(alpha),
        "mode": mode,
        "pattern": pattern,
        "active_frame_count": len(active),
        "changed_frames": changed_frames,
        "changed_points": changed_points,
        "changed_pairs": changed_pairs,
        "skipped_pairs": skipped_pairs,
        "total_frames": n,
    }
    return _sequence_with_relative_motion_features(transformed, profile), detail


def _spec(
    variant: str,
    kind: str,
    *,
    group: str,
    pairs: Sequence[Tuple[str, str]],
    alpha: float,
    mode: str,
    pattern: str,
    rationale: str,
    min_score: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": kind,
        "group": group,
        "pairs": [(str(left), str(right)) for left, right in pairs],
        "alpha": float(alpha),
        "mode": mode,
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
            pairs=[],
            alpha=0.0,
            mode="compress",
            pattern="none",
            min_score=95.0,
            rationale="标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。",
        )
    ]
    if word == "花":
        specs.extend(
            [
                _spec(
                    "flower_right_index_middle_single_mid_compress_0p35",
                    "positive",
                    group="right_hand",
                    pairs=INNER_PAIR,
                    alpha=0.35,
                    mode="compress",
                    pattern="single_mid",
                    min_score=min_score,
                    rationale="开花核心手 index/middle 指缝单帧压缩，模拟瞬时手指扇形识别塌缩。",
                ),
                _spec(
                    "flower_right_nonoverlap_sparse_compress_0p25_every_5f",
                    "positive",
                    group="right_hand",
                    pairs=NONOVERLAP_FAN_PAIRS,
                    alpha=0.25,
                    mode="compress",
                    pattern="sparse_every_5f",
                    min_score=min_score,
                    rationale="开花核心手相邻指缝稀疏帧轻中度压缩，完整张开证据仍应保留。",
                ),
                _spec(
                    "flower_right_wide_middle20_spread_0p16",
                    "positive",
                    group="right_hand",
                    pairs=WIDE_FAN_PAIRS,
                    alpha=0.16,
                    mode="spread",
                    pattern="middle_20pct",
                    min_score=min_score,
                    rationale="开花核心窗口 thumb/index 与 middle/ring 指缝轻度拉大，覆盖 fan spread 漂移。",
                ),
                _spec(
                    "flower_right_nonoverlap_middle20_compress_0p18",
                    "positive",
                    group="right_hand",
                    pairs=NONOVERLAP_FAN_PAIRS,
                    alpha=0.18,
                    mode="compress",
                    pattern="middle_20pct",
                    min_score=min_score,
                    rationale="开花短核心窗口非重叠相邻指缝压缩，验证局部扇形几何容错。",
                ),
                _spec(
                    "flower_right_nonoverlap_full_compress_0p08",
                    "positive",
                    group="right_hand",
                    pairs=NONOVERLAP_FAN_PAIRS,
                    alpha=0.08,
                    mode="compress",
                    pattern="full",
                    min_score=min_score,
                    rationale="开花全程轻微相邻指缝压缩，不应破坏开合相位和核心手形。",
                ),
                _spec(
                    "flower_right_full_fan_middle35_compress_0p72_diagnostic",
                    "diagnostic",
                    group="right_hand",
                    pairs=FULL_FAN_PAIRS,
                    alpha=0.72,
                    mode="compress",
                    pattern="middle_35pct",
                    rationale="诊断记录：较长核心窗口全扇形指缝明显塌缩时的边界分。",
                ),
                _spec(
                    "flower_right_full_fan_full_cross_1p20_diagnostic",
                    "diagnostic",
                    group="right_hand",
                    pairs=FULL_FAN_PAIRS,
                    alpha=1.20,
                    mode="cross",
                    pattern="full",
                    rationale="诊断记录：全程相邻手指 distal chains 发生几何交叉时的边界分。",
                ),
            ]
        )
    elif word == "跳":
        specs.extend(
            [
                _spec(
                    "jump_right_person_full_compress_0p08",
                    "positive",
                    group="right_hand",
                    pairs=INNER_PAIR,
                    alpha=0.08,
                    mode="compress",
                    pattern="full",
                    min_score=min_score,
                    rationale="跳的右手两指小人 index/middle 指缝全程轻微压缩，双手关系和两指手形仍应稳定。",
                ),
                _spec(
                    "jump_right_person_full_spread_0p08",
                    "positive",
                    group="right_hand",
                    pairs=INNER_PAIR,
                    alpha=0.08,
                    mode="spread",
                    pattern="full",
                    min_score=min_score,
                    rationale="跳的右手两指小人 index/middle 指缝全程轻微拉大，覆盖相反 fan drift。",
                ),
                _spec(
                    "jump_right_person_sparse_compress_0p20_every_5f",
                    "positive",
                    group="right_hand",
                    pairs=INNER_PAIR,
                    alpha=0.20,
                    mode="compress",
                    pattern="sparse_every_5f",
                    min_score=min_score,
                    rationale="跳的右手两指小人稀疏帧中度指缝压缩，跳跃轨迹仍应保持。",
                ),
                _spec(
                    "jump_right_person_middle20_compress_0p14",
                    "positive",
                    group="right_hand",
                    pairs=INNER_PAIR,
                    alpha=0.14,
                    mode="compress",
                    pattern="middle_20pct",
                    min_score=min_score,
                    rationale="跳的右手两指核心短窗口轻度指缝压缩，验证局部 fan geometry 容错。",
                ),
                _spec(
                    "jump_left_ground_nonoverlap_full_compress_0p10",
                    "positive",
                    group="left_hand",
                    pairs=NONOVERLAP_FAN_PAIRS,
                    alpha=0.10,
                    mode="compress",
                    pattern="full",
                    min_score=min_score,
                    rationale="跳的左手地面手相邻指缝轻度压缩，右手两指语义和双手关系应不受影响。",
                ),
                _spec(
                    "jump_right_person_full_cross_1p20_diagnostic",
                    "diagnostic",
                    group="right_hand",
                    pairs=INNER_PAIR,
                    alpha=1.20,
                    mode="cross",
                    pattern="full",
                    rationale="诊断记录：右手两指小人 index/middle distal chains 全程几何交叉时的边界分。",
                ),
                _spec(
                    "jump_right_person_middle35_compress_0p80_diagnostic",
                    "diagnostic",
                    group="right_hand",
                    pairs=INNER_PAIR,
                    alpha=0.80,
                    mode="compress",
                    pattern="middle_35pct",
                    rationale="诊断记录：右手两指小人较长核心窗口明显指缝塌缩时的边界分。",
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
    standard, standard_detail = _fan_sequence(
        loaded_standard,
        "standard_base",
        group="right_hand",
        pairs=[],
        alpha=0.0,
        mode="compress",
        pattern="none",
        profile=profile,
    )
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(word, min_score):
        query, detail = _fan_sequence(
            loaded_standard,
            str(spec["variant"]),
            group=str(spec["group"]),
            pairs=spec["pairs"],
            alpha=float(spec["alpha"]),
            mode=str(spec["mode"]),
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
        "pairs",
        "alpha",
        "mode",
        "pattern",
        "active_frame_count",
        "changed_frames",
        "changed_points",
        "changed_pairs",
        "skipped_pairs",
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
                        "pairs": row.get("pairs"),
                        "alpha": row.get("alpha"),
                        "mode": row.get("mode"),
                        "pattern": row.get("pattern"),
                        "active_frame_count": row.get("active_frame_count"),
                        "changed_frames": row.get("changed_frames"),
                        "changed_points": row.get("changed_points"),
                        "changed_pairs": row.get("changed_pairs"),
                        "skipped_pairs": row.get("skipped_pairs"),
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
        "# 花/跳手指扇形几何鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，只压缩/拉开同一手内相邻 distal finger chains 的二维扇形几何，landmark 身份和 mask 不变，wrist/MCP/palm anchors 保持当前帧；随后重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：单帧、稀疏和短窗口 finger fan drift 仍可正常评分；持续强压缩或几何交叉只记录诊断边界。",
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
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向扇形漂移 | 诊断最低分 | 最弱诊断边界 | 门槛 |")
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
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | group | pairs | alpha | mode | pattern | 改动帧 | 改动点 | capture_quality | semantic_floor | 说明 |")
        lines.append("|---|---|---|---:|---|---|---|---:|---|---|---:|---:|---|---|---|")
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
                f"{threshold} | {row.get('group')} | {row.get('pairs')} | {_fmt(row.get('alpha'))} | "
                f"{row.get('mode')} | {row.get('pattern')} | {row.get('changed_frames')} | "
                f"{row.get('changed_points')} | {quality.get('status') or '-'}:{quality.get('reason') or '-'} | "
                f"{floor.get('source') or '-'}:{floor.get('reason') or '-'} | {row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 该门补充的是相邻手指 distal chains 的扇形间距/指缝几何漂移，不替代 finger identity jitter、finger curl/length style、fingertip/mid-joint occlusion、hand detail loss、hand overlap merge 或 finger-chain latency 门。",
            "- 持续核心窗口的强 fan collapse/crossing 可能改变真实手形语义，本轮只作为诊断边界；是否升级硬负例需要真实网页样本或人工标签。",
            "- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run finger fan-geometry robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_finger_fan_geometry_robustness_gate_current"))
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
        "claim_policy": "synthetic finger fan-geometry robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": backend_status,
        "passed": passed,
        "min_score": args.min_score,
        "results": results,
    }

    json_path = output_dir / "flower_jump_finger_fan_geometry_robustness_gate.json"
    md_path = output_dir / "flower_jump_finger_fan_geometry_robustness_gate.md"
    csv_path = output_dir / "flower_jump_finger_fan_geometry_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳手指扇形几何鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳手指扇形几何鲁棒性报告：{md_path}")
    print(f"已生成花/跳手指扇形几何鲁棒性 CSV：{csv_path}")
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

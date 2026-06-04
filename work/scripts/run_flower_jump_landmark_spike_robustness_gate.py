#!/usr/bin/env python3
"""Stress-test flower/jump scoring against short-lived landmark spikes.

Webcam Holistic streams can contain one-frame hand teleports or fingertip
outliers even when the surrounding motion is correct. The scorer should
tolerate isolated or sparse spikes, while sustained or alternating spikes are
kept as diagnostics instead of being promoted as normal captures.

This script edits cached skeleton sequences in memory only. It does not call
/api/score, run Holistic, move marker, or restart 5080.
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
HAND_GROUPS = ["left_hand", "right_hand"]
TIP_LANDMARKS = [4, 8, 12, 16, 20]


def _indices_for_pattern(pattern: str, length: int) -> Set[int]:
    if length <= 0:
        return set()
    if pattern == "none":
        return set()
    if pattern == "single_mid":
        return {length // 2}
    if pattern == "sparse_every_7th":
        return {idx for idx in range(length) if idx % 7 == 3}
    if pattern == "middle_20pct":
        start = int(round(length * 0.40))
        end = max(start + 1, int(round(length * 0.60)))
        return set(range(max(0, start), min(length, end)))
    if pattern == "alternating_half":
        return {idx for idx in range(length) if idx % 2 == 1}
    raise ValueError(f"unknown spike pattern: {pattern}")


def _apply_spike_to_hand(
    coords: np.ndarray,
    valid: np.ndarray,
    mode: str,
    *,
    seed: int,
) -> np.ndarray:
    coords = coords.copy()
    visible = np.where(valid)[0]
    if mode == "none" or not len(visible):
        return coords
    if mode == "whole_hand_translation":
        coords[valid, 0] += 0.16
        coords[valid, 1] -= 0.10
        coords[valid, 2] += 0.02
    elif mode == "one_tip_spike":
        for landmark_idx in [8, 12]:
            if landmark_idx < len(coords) and valid[landmark_idx]:
                coords[landmark_idx] += np.asarray([0.16, -0.10, 0.03], dtype=np.float32)
    elif mode == "all_tip_spike":
        for landmark_idx in TIP_LANDMARKS:
            if landmark_idx < len(coords) and valid[landmark_idx]:
                coords[landmark_idx] += np.asarray([0.18, -0.14, 0.04], dtype=np.float32)
    elif mode == "visible_shuffle":
        if len(visible) > 1:
            rng = np.random.default_rng(seed)
            coords[visible] = coords[rng.permutation(visible)]
    else:
        raise ValueError(f"unknown spike mode: {mode}")
    return coords


def _spike_sequence(
    seq: SequenceData,
    name: str,
    *,
    pattern: str,
    mode: str,
    profile: Any,
) -> Tuple[SequenceData, Dict[str, Any]]:
    base = _strip_to_base_groups(seq)
    selected = _indices_for_pattern(pattern, len(base.features))
    features: List[FrameFeature] = []
    for idx, frame in enumerate(base.features):
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        presence = dict(frame.presence)
        if idx in selected and mode != "none":
            for group in HAND_GROUPS:
                coords, valid = _hand_array(frame, group)
                if coords is None or valid is None or not valid.any():
                    continue
                updated = _apply_spike_to_hand(coords, valid, mode, seed=137 + idx)
                _set_hand_group(frame, vector, mask, group, updated, valid)
                presence[group] = bool(valid.any())
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
        "pattern": pattern,
        "spike_mode": mode,
        "spike_frame_count": len(selected),
        "total_frames": len(base.features),
        "spike_ratio": (len(selected) / len(base.features)) if base.features else 0.0,
        "spike_indices": sorted(selected),
    }
    return _sequence_with_relative_motion_features(transformed, profile), detail


def _variant_specs(word: str) -> List[Dict[str, Any]]:
    flower = word == "花"
    return [
        {
            "variant": "self_recomputed",
            "kind": "positive",
            "pattern": "none",
            "spike_mode": "none",
            "min_score": 95.0,
            "rationale": "标准序列剥离基础组后重建 motion/relation 特征，应保持近满分。",
        },
        {
            "variant": "single_frame_whole_hand_spike",
            "kind": "positive",
            "pattern": "single_mid",
            "spike_mode": "whole_hand_translation",
            "min_score": 90.0 if flower else 70.0,
            "rationale": "单帧整手跳点属于 Holistic 短时检测抖动，应保持可评分。",
        },
        {
            "variant": "single_frame_tip_spike",
            "kind": "positive",
            "pattern": "single_mid",
            "spike_mode": "one_tip_spike",
            "min_score": 90.0 if flower else 70.0,
            "rationale": "单帧食指/中指 tip 跳点不应破坏完整正确动作。",
        },
        {
            "variant": "sparse_tip_spike_every_7th",
            "kind": "positive",
            "pattern": "sparse_every_7th",
            "spike_mode": "one_tip_spike",
            "min_score": 85.0 if flower else 70.0,
            "rationale": "稀疏 fingertip 跳点应靠 DTW/时序冗余保持正常或边界评分。",
        },
        {
            "variant": "middle_20pct_all_tip_spike_diagnostic",
            "kind": "diagnostic",
            "pattern": "middle_20pct",
            "spike_mode": "all_tip_spike",
            "rationale": "连续核心片段多 fingertip 跳点属于边界诊断，不作为正向门。",
        },
        {
            "variant": "alternating_tip_spike_diagnostic",
            "kind": "diagnostic",
            "pattern": "alternating_half",
            "spike_mode": "all_tip_spike",
            "rationale": "交替半数帧 tip 跳点过强，只记录评分边界。",
        },
        {
            "variant": "middle_20pct_visible_shuffle_diagnostic",
            "kind": "diagnostic",
            "pattern": "middle_20pct",
            "spike_mode": "visible_shuffle",
            "rationale": "连续片段 landmark 顺序扰动是严重检测错误，只作诊断。",
        },
    ]


def _run_word(
    word: str,
    template_root: Path,
    semantic_profile_json: Path,
    feature_mode: str,
) -> Dict[str, Any]:
    standard_json = _template_json(template_root, word)
    loaded_standard = load_sequence(standard_json, feature_mode, force_bbox=False)
    profile = load_semantic_profile(word, semantic_profile_json)
    standard, standard_detail = _spike_sequence(
        loaded_standard,
        "standard_base",
        pattern="none",
        mode="none",
        profile=profile,
    )
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(word):
        query, spike_detail = _spike_sequence(
            loaded_standard,
            str(spec["variant"]),
            pattern=str(spec["pattern"]),
            mode=str(spec["spike_mode"]),
            profile=profile,
        )
        result = run_pair(standard, query, semantic_profile=profile, enable_cross_check=False)
        score_scale = result.get("score_scale") or {}
        row = {
            **spec,
            **spike_detail,
            "score": float(result["prototype_score"]),
            "dtw_distance": float(result["dtw_distance"]),
            "normalized_distance": float(result["normalized_distance"]),
            "alignment_policy": result.get("alignment_policy"),
            "capture_quality": score_scale.get("capture_quality"),
            "semantic_floor": score_scale.get("semantic_floor"),
            "score_scale_reason": score_scale.get("reason"),
        }
        row["passed"] = row["kind"] != "positive" or float(row["score"]) >= float(row["min_score"])
        rows.append(row)
    positive_rows = [row for row in rows if row["kind"] == "positive"]
    diagnostic_rows = [row for row in rows if row["kind"] == "diagnostic"]
    weakest_positive = min(positive_rows, key=lambda row: float(row["score"])) if positive_rows else None
    weakest_diagnostic = min(diagnostic_rows, key=lambda row: float(row["score"])) if diagnostic_rows else None
    return {
        "word": word,
        "standard_json": str(standard_json),
        "standard_length": len(standard.features),
        "standard_spike_detail": standard_detail,
        "semantic_profile": _profile_summary(profile),
        "gate_pass": all(bool(row["passed"]) for row in positive_rows),
        "weakest_positive_score": float(weakest_positive["score"]) if weakest_positive else None,
        "weakest_positive_variant": weakest_positive["variant"] if weakest_positive else "",
        "weakest_diagnostic_score": float(weakest_diagnostic["score"]) if weakest_diagnostic else None,
        "weakest_diagnostic_variant": weakest_diagnostic["variant"] if weakest_diagnostic else "",
        "variants": rows,
    }


def _write_rows_csv(path: Path, results: Sequence[Dict[str, Any]]) -> None:
    fields = [
        "word",
        "variant",
        "kind",
        "passed",
        "score",
        "min_score",
        "spike_mode",
        "spike_frame_count",
        "spike_ratio",
        "dtw_distance",
        "normalized_distance",
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
                        "passed": row.get("passed"),
                        "score": row.get("score"),
                        "min_score": row.get("min_score"),
                        "spike_mode": row.get("spike_mode"),
                        "spike_frame_count": row.get("spike_frame_count"),
                        "spike_ratio": row.get("spike_ratio"),
                        "dtw_distance": row.get("dtw_distance"),
                        "normalized_distance": row.get("normalized_distance"),
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
        "# 花/跳 landmark 跳点鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，先剥离到基础骨架组，再在手部坐标层合成单帧/稀疏 landmark 跳点并重建 motion/relation/hand-shape 特征；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：单帧和稀疏跳点仍保持正常或边界分；连续核心跳点和 landmark 顺序扰动只作为诊断边界。",
        "",
    ]
    backend = payload.get("backend_status") or {}
    if backend.get("ok"):
        data = backend.get("payload") or {}
        worker = data.get("worker") or {}
        scoring = data.get("scoring_module") or {}
        process = worker.get("process") or {}
        lines.append(
            f"- 后端：`{backend.get('url')}`，worker=`{worker.get('status')}`，"
            f"pid=`{process.get('pid')}`，scoring reload=`{scoring.get('reload_count')}`，"
            f"last_reload_error=`{scoring.get('last_reload_error')}`"
        )
    else:
        lines.append(f"- 后端状态读取失败：`{backend.get('error')}`")
    lines.append("")
    lines.append("## 汇总")
    lines.append("")
    lines.append(f"- 总体：`{'PASS' if payload.get('passed') else 'FAIL'}`")
    lines.append("")
    lines.append("| 词条 | 状态 | 正向最低分 | 最弱正向跳点 | 诊断最低分 | 最弱诊断跳点 |")
    lines.append("|---|---|---:|---|---:|---|")
    for item in payload.get("results") or []:
        lines.append(
            f"| {item.get('word')} | {'PASS' if item.get('gate_pass') else 'FAIL'} | "
            f"{_fmt(item.get('weakest_positive_score'))} | {item.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(item.get('weakest_diagnostic_score'))} | {item.get('weakest_diagnostic_variant') or '-'} |"
        )
    lines.append("")
    for item in payload.get("results") or []:
        lines.append(f"## {item.get('word')} 明细")
        lines.append("")
        lines.append("| 变体 | 类型 | 状态 | 分数 | 帧数 | 质量 | 语义 floor | 说明 |")
        lines.append("|---|---|---|---:|---:|---|---|---|")
        for row in item.get("variants") or []:
            quality = row.get("capture_quality") or {}
            floor = row.get("semantic_floor") or {}
            lines.append(
                f"| {row.get('variant')} | {row.get('kind')} | {'PASS' if row.get('passed') else 'FAIL'} | "
                f"{_fmt(row.get('score'))} | {row.get('spike_frame_count')}/{row.get('total_frames')} | "
                f"{quality.get('status') or '-'}:{quality.get('reason') or '-'} | "
                f"{floor.get('source') or '-'}:{floor.get('reason') or '-'} | "
                f"{row.get('rationale')} |"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def _default_output_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return DEFAULT_OUTPUT_BASE / f"flower_jump_landmark_spike_robustness_gate_{stamp}"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run flower/jump landmark spike robustness gate.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--backend-timeout-sec", type=float, default=5.0)
    parser.add_argument("--feature-mode", choices=["auto", "landmark", "bbox"], default="auto")
    parser.add_argument("--words", nargs="+", default=DEFAULT_WORDS)
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir) if args.output_dir else _default_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    template_root = Path(args.template_root)
    semantic_profile_json = Path(args.semantic_profile_json)
    results = [
        _run_word(word, template_root, semantic_profile_json, args.feature_mode)
        for word in args.words
    ]
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "claim_policy": "engineering robustness gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_url": args.backend_url,
        "backend_status": _load_backend_status(args.backend_url, args.backend_timeout_sec),
        "results": results,
        "passed": all(bool(item.get("gate_pass")) for item in results),
    }
    json_path = output_dir / "flower_jump_landmark_spike_robustness_gate.json"
    md_path = output_dir / "flower_jump_landmark_spike_robustness_gate.md"
    csv_path = output_dir / "flower_jump_landmark_spike_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    _write_rows_csv(csv_path, results)
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    print(f"landmark spike gate: {'PASS' if payload['passed'] else 'FAIL'}")
    print(f"json: {json_path}")
    print(f"md: {md_path}")
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

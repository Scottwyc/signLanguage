#!/usr/bin/env python3
"""Stress-test flower/jump scoring against transient left/right hand-label flicker.

This gate targets a webcam/Holistic-specific risk that is distinct from a full
hand-role swap: the detector may briefly assign the same physical hand to the
other side for one or a few frames. Mild isolated flicker should not break an
otherwise correct sequence, while sustained or alternating label flicker should
remain a recapture or semantic-failure diagnostic instead of being accepted as
normal.

The script only reads cached Holistic JSON and edits skeleton features in
memory. It does not call /api/score, run Holistic, move marker, or restart 5080.
"""

from __future__ import annotations

import argparse
import csv
import json
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from run_flower_jump_mirror_robustness_gate import SWAP_PAIRS, _strip_to_base_groups, _template_json
from score_holistic_sequence_mvp import (
    DEFAULT_SEMANTIC_PROFILE_JSON,
    FrameFeature,
    SequenceData,
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
ACCEPTED_NEGATIVE_QUALITY = {"semantic_mismatch", "needs_recapture"}


def _json_default(value: Any) -> Any:
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _load_backend_status(backend_url: str, timeout_sec: float) -> Dict[str, Any]:
    url = backend_url.rstrip("/") + "/api/status"
    try:
        with urllib.request.urlopen(url, timeout=timeout_sec) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return {"ok": True, "url": url, "payload": payload, "error": ""}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"ok": False, "url": url, "payload": {}, "error": str(exc)}


def _fmt(value: Any, digits: int = 3) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "-"


def _swap_hand_labels(frame: FrameFeature) -> FrameFeature:
    vector = frame.vector.copy()
    mask = frame.mask.copy()
    groups = dict(frame.groups)
    presence = dict(frame.presence)
    for left, right in SWAP_PAIRS:
        if left not in groups or right not in groups:
            continue
        left_sl = groups[left]
        right_sl = groups[right]
        left_vector = vector[left_sl].copy()
        right_vector = vector[right_sl].copy()
        left_mask = mask[left_sl].copy()
        right_mask = mask[right_sl].copy()
        vector[left_sl] = right_vector
        vector[right_sl] = left_vector
        mask[left_sl] = right_mask
        mask[right_sl] = left_mask
    presence["left_hand"], presence["right_hand"] = (
        bool(presence.get("right_hand", False)),
        bool(presence.get("left_hand", False)),
    )
    return FrameFeature(
        frame_idx=frame.frame_idx,
        timestamp_sec=frame.timestamp_sec,
        vector=vector,
        mask=mask,
        groups=groups,
        presence=presence,
        frame_weight=float(frame.frame_weight),
        semantic_phase=float(frame.semantic_phase),
    )


def _indices_for_pattern(pattern: str, length: int) -> Set[int]:
    if length <= 0:
        return set()
    if pattern == "none":
        return set()
    if pattern == "single_mid":
        return {length // 2}
    if pattern == "sparse_every_5th":
        return {idx for idx in range(length) if idx % 5 == 2}
    if pattern == "middle_20pct":
        start = int(round(length * 0.40))
        end = max(start + 1, int(round(length * 0.60)))
        return set(range(max(0, start), min(length, end)))
    if pattern == "alternating_half":
        return {idx for idx in range(length) if idx % 2 == 1}
    raise ValueError(f"unknown flicker pattern: {pattern}")


def _flicker_sequence(seq: SequenceData, name: str, pattern: str, profile: Any) -> Tuple[SequenceData, Dict[str, Any]]:
    base = _strip_to_base_groups(seq)
    indices = _indices_for_pattern(pattern, len(base.features))
    features = [
        _swap_hand_labels(frame) if idx in indices else frame
        for idx, frame in enumerate(base.features)
    ]
    transformed = SequenceData(
        source=f"{base.source}::{name}",
        mode=base.mode,
        fps=base.fps,
        total_frames=base.total_frames,
        features=features,
    )
    detail = {
        "pattern": pattern,
        "flicker_frame_count": len(indices),
        "total_frames": len(base.features),
        "flicker_ratio": (len(indices) / len(base.features)) if base.features else 0.0,
        "flicker_indices": sorted(indices),
    }
    return _sequence_with_relative_motion_features(transformed, profile), detail


def _variant_specs(word: str) -> List[Dict[str, Any]]:
    base = [
        {
            "variant": "self_recomputed",
            "kind": "positive",
            "pattern": "none",
            "min_score": 95.0,
            "expected": "same sequence should stay near perfect after feature recomputation",
        },
        {
            "variant": "single_frame_label_flicker",
            "kind": "positive",
            "pattern": "single_mid",
            "min_score": 65.0 if word == "跳" else 90.0,
            "expected": "one-frame detector side flicker should not break an otherwise correct sign",
        },
        {
            "variant": "sparse_label_flicker",
            "kind": "positive",
            "pattern": "sparse_every_5th",
            "min_score": 70.0 if word == "跳" else 85.0,
            "expected": "sparse detector side flicker should remain scoreable",
        },
    ]
    if word == "跳":
        base.append(
            {
                "variant": "short_contiguous_role_flicker",
                "kind": "positive",
                "pattern": "middle_20pct",
                "min_score": 65.0,
                "expected": "short role-label flicker should not erase the local jump segment",
            }
        )
    else:
        base.append(
            {
                "variant": "sustained_core_label_flicker_negative",
                "kind": "negative",
                "pattern": "middle_20pct",
                "max_score": 50.0,
                "expected": "sustained core-side instability should become recapture/semantic-failure evidence",
            }
        )
    base.append(
        {
            "variant": "alternating_label_flicker_negative",
            "kind": "negative",
            "pattern": "alternating_half",
            "max_score": 50.0,
            "expected": "alternating label flicker is too unstable to accept as a normal web capture",
        }
    )
    return base


def _row_passed(row: Dict[str, Any]) -> bool:
    score = float(row["score"])
    if row["kind"] == "positive":
        return score >= float(row["min_score"])
    quality = (row.get("capture_quality") or {}).get("status")
    return score <= float(row["max_score"]) and quality in ACCEPTED_NEGATIVE_QUALITY


def _run_word(
    word: str,
    template_root: Path,
    semantic_profile_json: Path,
    feature_mode: str,
) -> Dict[str, Any]:
    standard_json = _template_json(template_root, word)
    loaded_standard = load_sequence(standard_json, feature_mode, force_bbox=False)
    profile = load_semantic_profile(word, semantic_profile_json)
    standard, standard_flicker = _flicker_sequence(loaded_standard, "standard_base", "none", profile)
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(word):
        query, flicker_detail = _flicker_sequence(loaded_standard, spec["variant"], str(spec["pattern"]), profile)
        result = run_pair(standard, query, semantic_profile=profile, enable_cross_check=False)
        score_scale = result.get("score_scale") or {}
        sequence_penalty = result.get("sequence_penalty") or {}
        row = {
            **spec,
            **flicker_detail,
            "score": float(result["prototype_score"]),
            "dtw_distance": float(result["dtw_distance"]),
            "normalized_distance": float(result["normalized_distance"]),
            "alignment_policy": result.get("alignment_policy"),
            "capture_quality": score_scale.get("capture_quality"),
            "semantic_floor": score_scale.get("semantic_floor"),
            "score_scale_reason": score_scale.get("reason"),
            "sequence_penalty_total": sequence_penalty.get("total_sequence_penalty"),
        }
        row["passed"] = _row_passed(row)
        rows.append(row)
    positive_rows = [row for row in rows if row["kind"] == "positive"]
    negative_rows = [row for row in rows if row["kind"] == "negative"]
    weakest_positive = min(positive_rows, key=lambda row: float(row["score"])) if positive_rows else None
    strongest_negative = max(negative_rows, key=lambda row: float(row["score"])) if negative_rows else None
    return {
        "word": word,
        "standard_json": str(standard_json),
        "standard_length": len(standard.features),
        "standard_flicker_detail": standard_flicker,
        "semantic_profile": _profile_summary(profile),
        "gate_pass": all(bool(row["passed"]) for row in rows),
        "weakest_positive_score": float(weakest_positive["score"]) if weakest_positive else None,
        "weakest_positive_variant": weakest_positive["variant"] if weakest_positive else "",
        "strongest_negative_score": float(strongest_negative["score"]) if strongest_negative else None,
        "strongest_negative_variant": strongest_negative["variant"] if strongest_negative else "",
        "variants": rows,
    }


def _write_csv(path: Path, results: Sequence[Dict[str, Any]]) -> None:
    fields = [
        "word",
        "variant",
        "kind",
        "pattern",
        "flicker_frame_count",
        "total_frames",
        "flicker_ratio",
        "score",
        "passed",
        "min_score",
        "max_score",
        "capture_quality_status",
        "capture_quality_reason",
        "semantic_floor_reason",
        "sequence_penalty_total",
        "expected",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in results:
            for row in item["variants"]:
                quality = row.get("capture_quality") or {}
                floor = row.get("semantic_floor") or {}
                writer.writerow(
                    {
                        "word": item["word"],
                        "variant": row.get("variant"),
                        "kind": row.get("kind"),
                        "pattern": row.get("pattern"),
                        "flicker_frame_count": row.get("flicker_frame_count"),
                        "total_frames": row.get("total_frames"),
                        "flicker_ratio": row.get("flicker_ratio"),
                        "score": row.get("score"),
                        "passed": row.get("passed"),
                        "min_score": row.get("min_score", ""),
                        "max_score": row.get("max_score", ""),
                        "capture_quality_status": quality.get("status", ""),
                        "capture_quality_reason": quality.get("reason", ""),
                        "semantic_floor_reason": floor.get("reason", ""),
                        "sequence_penalty_total": row.get("sequence_penalty_total"),
                        "expected": row.get("expected"),
                    }
                )


def _build_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# 花/跳左右手标签抖动鲁棒性门")
    lines.append("")
    lines.append(f"- 生成时间：`{payload['generated_at']}`")
    lines.append(f"- 综合状态：`{'PASS' if payload['passed'] else 'FAIL'}`")
    lines.append(f"- 标准库：`{payload['template_root']}`")
    lines.append(f"- 语义 profile：`{payload['semantic_profile_json']}`")
    lines.append("- 口径：只读缓存 Holistic JSON；在部分帧交换 left/right hand 与 hand-shape 标签后复算相对运动；不调用 `/api/score`，不移动 marker，不运行 Holistic，不重启 5080。")
    lines.append("")
    lines.append("## 判定口径")
    lines.append("")
    lines.append("- 单帧或稀疏左右手标签 flicker 是正向鲁棒性门；这模拟 Holistic 短暂 handedness 抖动。")
    lines.append("- 持续核心段 flicker 或交替 flicker 是负向边界；这类采集太不稳定，应低分并进入 `needs_recapture/semantic_mismatch`。")
    lines.append("")
    lines.append("## 摘要")
    lines.append("")
    lines.append("| 词条 | 状态 | 正向最低分 | 最弱正向 flicker | 负向最高分 | 最强负向 flicker |")
    lines.append("|---|---|---:|---|---:|---|")
    for item in payload["results"]:
        lines.append(
            f"| {item['word']} | {'PASS' if item['gate_pass'] else 'FAIL'} | "
            f"{_fmt(item.get('weakest_positive_score'))} | {item.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(item.get('strongest_negative_score'))} | {item.get('strongest_negative_variant') or '-'} |"
        )
    lines.append("")
    lines.append("## 明细")
    lines.append("")
    lines.append("| 词条 | 变体 | 类型 | flicker 帧 | 分数 | 状态 | 采集质量 | floor 原因 | 说明 |")
    lines.append("|---|---|---|---:|---:|---|---|---|---|")
    for item in payload["results"]:
        for row in item["variants"]:
            quality = row.get("capture_quality") or {}
            floor = row.get("semantic_floor") or {}
            lines.append(
                f"| {item['word']} | {row.get('variant')} | {row.get('kind')} | "
                f"{row.get('flicker_frame_count')}/{row.get('total_frames')} | {_fmt(row.get('score'))} | "
                f"{'PASS' if row.get('passed') else 'FAIL'} | {quality.get('status') or '-'} / {quality.get('reason') or '-'} | "
                f"{floor.get('reason') or '-'} | {row.get('expected') or '-'} |"
            )
    lines.append("")
    lines.append("## 结论")
    lines.append("")
    if payload["passed"]:
        lines.append("- 左右手标签抖动边界通过：短暂 flicker 不破坏 `花/跳` 正常评分，持续/交替 flicker 不会被误接收为正常动作。")
    else:
        lines.append("- 左右手标签抖动边界未通过；需要复查手部标签稳定性、sequence penalty 或角色语义 guard。")
    return "\n".join(lines) + "\n"


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template-root", type=Path, default=DEFAULT_TEMPLATE_ROOT)
    parser.add_argument("--semantic-profile-json", type=Path, default=DEFAULT_SEMANTIC_PROFILE_JSON)
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--http-timeout-sec", type=float, default=3.0)
    parser.add_argument("--feature-mode", default="auto", choices=["auto", "landmark", "bbox"])
    parser.add_argument("--words", nargs="+", default=DEFAULT_WORDS)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_BASE / f"flower_jump_hand_label_flicker_robustness_gate_{stamp}",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    results = [
        _run_word(
            word,
            args.template_root,
            args.semantic_profile_json,
            args.feature_mode,
        )
        for word in args.words
    ]
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "claim_policy": "hand-label flicker robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(args.template_root),
        "semantic_profile_json": str(args.semantic_profile_json),
        "feature_mode": args.feature_mode,
        "backend_status": _load_backend_status(args.backend_url, args.http_timeout_sec),
        "accepted_negative_quality": sorted(ACCEPTED_NEGATIVE_QUALITY),
        "passed": all(bool(item["gate_pass"]) for item in results),
        "results": results,
    }
    json_path = args.output_dir / "flower_jump_hand_label_flicker_robustness_gate.json"
    md_path = args.output_dir / "flower_jump_hand_label_flicker_robustness_gate.md"
    csv_path = args.output_dir / "flower_jump_hand_label_flicker_robustness_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_csv(csv_path, results)

    print(f"已生成花/跳左右手标签抖动鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳左右手标签抖动鲁棒性报告：{md_path}")
    print(f"已生成花/跳左右手标签抖动鲁棒性 CSV：{csv_path}")
    print(f"综合状态：{'PASS' if payload['passed'] else 'FAIL'}")
    for item in results:
        print(
            f"- {item['word']}: {'PASS' if item['gate_pass'] else 'FAIL'} "
            f"positive_min={_fmt(item.get('weakest_positive_score'))} "
            f"weakest={item.get('weakest_positive_variant') or '-'} "
            f"negative_max={_fmt(item.get('strongest_negative_score'))}"
        )
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

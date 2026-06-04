#!/usr/bin/env python3
"""Stress-test flower/jump scoring against moving setup/exit contamination.

Real browser clips often include non-semantic hand movement before the user
starts the sign or after the user finishes it. Static padding and repeated
actions are already covered elsewhere; this gate targets moving entry/exit
frames while the complete semantic core is still present.

This script edits cached skeleton sequences in memory only. It does not call
/api/score, run Holistic, move the web marker, or restart 5080.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

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
    _clone_sequence,
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

OffsetMap = Dict[str, Tuple[float, float, float]]
QueryFactory = Callable[[SequenceData, Any], SequenceData]


def _word_offsets(word: str, phase: str) -> OffsetMap:
    if word == "花":
        if phase == "entry":
            return {"right_hand": (-0.18, 0.16, 0.02)}
        return {"right_hand": (0.16, 0.18, -0.02)}
    if phase == "entry":
        return {
            "left_hand": (-0.13, 0.14, 0.00),
            "right_hand": (0.13, 0.14, 0.00),
        }
    return {
        "left_hand": (-0.16, 0.18, 0.00),
        "right_hand": (0.16, 0.18, 0.00),
    }


def _move_hand_frame(frame: FrameFeature, offsets: OffsetMap, factor: float) -> FrameFeature:
    vector = frame.vector.copy()
    mask = frame.mask.copy()
    presence = dict(frame.presence)
    for group, offset in offsets.items():
        coords, valid = _hand_array(frame, group)
        if coords is None or valid is None or not valid.any():
            continue
        moved = coords.copy()
        moved[valid] = moved[valid] + np.asarray(offset, dtype=np.float32) * float(factor)
        _set_hand_group(frame, vector, mask, group, moved, valid)
        presence[group] = bool(valid.any())
    item = _clone_frame(frame, vector=vector, mask=mask)
    item.presence = presence
    return item


def _entry_frames(seq: SequenceData, count: int, offsets: OffsetMap) -> List[FrameFeature]:
    if not seq.features or count <= 0:
        return []
    anchor = seq.features[0]
    frames: List[FrameFeature] = []
    for idx in range(int(count)):
        # Far from the start pose first, then approach the real first frame.
        factor = 1.0 - ((idx + 1) / (int(count) + 1))
        frames.append(_move_hand_frame(anchor, offsets, factor))
    return frames


def _exit_frames(seq: SequenceData, count: int, offsets: OffsetMap) -> List[FrameFeature]:
    if not seq.features or count <= 0:
        return []
    anchor = seq.features[-1]
    frames: List[FrameFeature] = []
    for idx in range(int(count)):
        # Leave the final sign pose gradually.
        factor = (idx + 1) / max(int(count), 1)
        frames.append(_move_hand_frame(anchor, offsets, factor))
    return frames


def _renumber(items: Sequence[FrameFeature], fps: float) -> List[FrameFeature]:
    safe_fps = max(float(fps or 0.0), 1.0)
    total = max(len(items) - 1, 1)
    renumbered: List[FrameFeature] = []
    for idx, frame in enumerate(items):
        item = _clone_frame(frame)
        item.frame_idx = idx
        item.timestamp_sec = idx / safe_fps
        item.semantic_phase = idx / total
        renumbered.append(item)
    return renumbered


def _compose(
    seq: SequenceData,
    profile: Any,
    name: str,
    *,
    word: str,
    entry_ratio: float = 0.0,
    exit_ratio: float = 0.0,
    include_core: bool = True,
    entry_scale: float = 1.0,
    exit_scale: float = 1.0,
) -> SequenceData:
    base = _strip_to_base_groups(seq)
    n = len(base.features)
    entry_count = max(0, int(round(n * float(entry_ratio))))
    exit_count = max(0, int(round(n * float(exit_ratio))))
    entry_offsets = {
        group: tuple(float(value) * float(entry_scale) for value in offset)
        for group, offset in _word_offsets(word, "entry").items()
    }
    exit_offsets = {
        group: tuple(float(value) * float(exit_scale) for value in offset)
        for group, offset in _word_offsets(word, "exit").items()
    }
    items: List[FrameFeature] = []
    items.extend(_entry_frames(base, entry_count, entry_offsets))
    if include_core:
        items.extend(_clone_frame(frame) for frame in base.features)
    items.extend(_exit_frames(base, exit_count, exit_offsets))
    raw = _clone_sequence(base, name, _renumber(items, base.fps))
    return _sequence_with_relative_motion_features(raw, profile)


def _spec(
    variant: str,
    kind: str,
    query: QueryFactory,
    rationale: str,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": kind,
        "query": query,
        "min_score": min_score,
        "max_score": max_score,
        "gated": kind in {"positive", "negative"},
        "rationale": rationale,
    }


def _variant_specs(word: str, min_score: float) -> List[Dict[str, Any]]:
    return [
        _spec(
            "self_recomputed",
            "positive",
            lambda seq, profile: _compose(seq, profile, "self_recomputed", word=word, include_core=True),
            "标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。",
            min_score=95.0,
        ),
        _spec(
            "prefix_moving_entry_25pct",
            "positive",
            lambda seq, profile: _compose(seq, profile, "prefix_moving_entry_25pct", word=word, entry_ratio=0.25),
            "动作前有手部移动入场，但完整核心动作仍在。",
            min_score=min_score,
        ),
        _spec(
            "suffix_moving_exit_25pct",
            "positive",
            lambda seq, profile: _compose(seq, profile, "suffix_moving_exit_25pct", word=word, exit_ratio=0.25),
            "动作后有手部移动离场，但完整核心动作仍在。",
            min_score=min_score,
        ),
        _spec(
            "entry_exit_moving_18pct",
            "positive",
            lambda seq, profile: _compose(
                seq,
                profile,
                "entry_exit_moving_18pct",
                word=word,
                entry_ratio=0.18,
                exit_ratio=0.18,
            ),
            "录制前后都有动态手部污染，核心手语完整。",
            min_score=min_score,
        ),
        _spec(
            "long_prefix_moving_entry_35pct",
            "positive",
            lambda seq, profile: _compose(seq, profile, "long_prefix_moving_entry_35pct", word=word, entry_ratio=0.35),
            "较长移动入场，验证 action-window 能聚焦真实核心。",
            min_score=min_score,
        ),
        _spec(
            "moving_entry_only_35pct_negative",
            "negative",
            lambda seq, profile: _compose(
                seq,
                profile,
                "moving_entry_only_35pct_negative",
                word=word,
                entry_ratio=0.35,
                include_core=False,
            ),
            "只有移动入场，没有完整手语核心，不能当作目标通过。",
            max_score=45.0,
        ),
        _spec(
            "strong_entry_exit_45pct_diagnostic",
            "diagnostic",
            lambda seq, profile: _compose(
                seq,
                profile,
                "strong_entry_exit_45pct_diagnostic",
                word=word,
                entry_ratio=0.45,
                exit_ratio=0.45,
                entry_scale=1.35,
                exit_scale=1.35,
            ),
            "更长且更大幅的动态入场/退场，只记录诊断边界。",
        ),
        _spec(
            "moving_exit_only_35pct_diagnostic",
            "diagnostic",
            lambda seq, profile: _compose(
                seq,
                profile,
                "moving_exit_only_35pct_diagnostic",
                word=word,
                exit_ratio=0.35,
                include_core=False,
            ),
            "只有移动离场可能保留结束姿态，不作为负向硬门，仅记录边界。",
        ),
    ]


def _row_passed(row: Dict[str, Any]) -> bool:
    score = float(row["score"])
    if row["kind"] == "positive":
        return score >= float(row["min_score"])
    if row["kind"] == "negative":
        quality = (row.get("capture_quality") or {}).get("status")
        return score <= float(row["max_score"]) or quality in ACCEPTED_NEGATIVE_QUALITY
    return True


def _run_word(
    word: str,
    template_root: Path,
    semantic_profile_json: Path,
    feature_mode: str,
    min_score: float,
) -> Dict[str, Any]:
    standard_json = _template_json(template_root, word)
    standard = load_sequence(standard_json, feature_mode, force_bbox=False)
    profile = load_semantic_profile(word, semantic_profile_json)
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(word, min_score):
        query = spec["query"](standard, profile)
        result = run_pair(standard, query, semantic_profile=profile, target_word=word, enable_cross_check=False)
        score_scale = result.get("score_scale") or {}
        row = {
            "variant": spec["variant"],
            "kind": spec["kind"],
            "gated": bool(spec["gated"]),
            "min_score": spec.get("min_score"),
            "max_score": spec.get("max_score"),
            "rationale": spec["rationale"],
            "score": float(result["prototype_score"]),
            "dtw_distance": float(result["dtw_distance"]),
            "normalized_distance": float(result["normalized_distance"]),
            "query_length": len(query.features),
            "length_ratio": len(query.features) / max(len(standard.features), 1),
            "alignment_policy": result.get("alignment_policy"),
            "capture_quality": score_scale.get("capture_quality"),
            "semantic_floor": score_scale.get("semantic_floor"),
            "semantic_phase_order_guard": score_scale.get("semantic_phase_order_guard"),
            "action_window": result.get("action_window"),
        }
        row["passed"] = _row_passed(row)
        rows.append(row)
    positive_rows = [row for row in rows if row["kind"] == "positive"]
    negative_rows = [row for row in rows if row["kind"] == "negative"]
    diagnostic_rows = [row for row in rows if row["kind"] == "diagnostic"]
    weakest_positive = min(positive_rows, key=lambda row: float(row["score"])) if positive_rows else None
    strongest_negative = max(negative_rows, key=lambda row: float(row["score"])) if negative_rows else None
    diagnostic_lowest = min(diagnostic_rows, key=lambda row: float(row["score"])) if diagnostic_rows else None
    diagnostic_highest = max(diagnostic_rows, key=lambda row: float(row["score"])) if diagnostic_rows else None
    return {
        "word": word,
        "standard_json": str(standard_json),
        "standard_length": len(standard.features),
        "semantic_profile": _profile_summary(profile),
        "gate_pass": all(bool(row["passed"]) for row in rows if row["gated"]),
        "weakest_positive_score": float(weakest_positive["score"]) if weakest_positive else None,
        "weakest_positive_variant": weakest_positive["variant"] if weakest_positive else "",
        "strongest_negative_score": float(strongest_negative["score"]) if strongest_negative else None,
        "strongest_negative_variant": strongest_negative["variant"] if strongest_negative else "",
        "diagnostic_lowest_score": float(diagnostic_lowest["score"]) if diagnostic_lowest else None,
        "diagnostic_lowest_variant": diagnostic_lowest["variant"] if diagnostic_lowest else "",
        "diagnostic_highest_score": float(diagnostic_highest["score"]) if diagnostic_highest else None,
        "diagnostic_highest_variant": diagnostic_highest["variant"] if diagnostic_highest else "",
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
        "query_length",
        "length_ratio",
        "alignment_mode",
        "capture_quality_status",
        "capture_quality_reason",
        "semantic_floor_source",
        "semantic_floor_reason",
        "phase_order_blocked",
        "phase_order_reason",
        "rationale",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in results:
            for row in item["variants"]:
                quality = row.get("capture_quality") or {}
                floor = row.get("semantic_floor") or {}
                phase_order = row.get("semantic_phase_order_guard") or {}
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
                        "query_length": row.get("query_length"),
                        "length_ratio": row.get("length_ratio"),
                        "alignment_mode": policy.get("mode"),
                        "capture_quality_status": quality.get("status"),
                        "capture_quality_reason": quality.get("reason"),
                        "semantic_floor_source": floor.get("source"),
                        "semantic_floor_reason": floor.get("reason"),
                        "phase_order_blocked": phase_order.get("blocked"),
                        "phase_order_reason": phase_order.get("reason"),
                        "rationale": row.get("rationale"),
                    }
                )


def _build_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# 花/跳动态入场退场鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，在骨架层合成手部移动入场/退场并重建 hand-shape、motion、two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：真实网页录制出现开始前移动手到位或结束后放下手时，只要完整核心动作仍在，评分保持正常；只有入场片段不能通过。",
        "",
    ]
    backend = payload.get("backend_status") or {}
    if backend.get("ok"):
        data = backend.get("payload") or {}
        worker = data.get("worker") or {}
        scoring = data.get("scoring_module") or {}
        lines.append(
            f"- 5080 状态：worker=`{worker.get('status')}`，worker_pid=`{((worker.get('ready_payload') or {}).get('pid'))}`，"
            f"reload_count=`{scoring.get('reload_count')}`，last_reload_error=`{scoring.get('last_reload_error')}`"
        )
    else:
        lines.append(f"- 5080 状态：读取失败 `{backend.get('error') or '-'}`")
    lines.extend(["", "## 结论", "", f"- 综合状态：`{'PASS' if payload['passed'] else 'FAIL'}`", ""])
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向动态污染 | 入场-only 最高分 | 最强入场-only | 诊断分数范围 |")
    lines.append("|---|---|---:|---|---:|---|---|")
    for item in payload["results"]:
        diagnostic_range = "-"
        if item.get("diagnostic_lowest_score") is not None:
            diagnostic_range = f"{_fmt(item.get('diagnostic_lowest_score'))} - {_fmt(item.get('diagnostic_highest_score'))}"
        lines.append(
            f"| {item['word']} | {'PASS' if item['gate_pass'] else 'FAIL'} | "
            f"{_fmt(item['weakest_positive_score'])} | {item['weakest_positive_variant']} | "
            f"{_fmt(item['strongest_negative_score'])} | {item['strongest_negative_variant']} | {diagnostic_range} |"
        )
    lines.append("")
    lines.append("## 分项明细")
    for item in payload["results"]:
        lines.extend(["", f"### {item['word']}", "", f"- 标准序列：`{item['standard_json']}`", ""])
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | 长度比 | alignment | capture_quality | reason | 说明 |")
        lines.append("|---|---|---|---:|---|---:|---|---|---|---|")
        for row in sorted(item["variants"], key=lambda x: (x["kind"], float(x["score"]))):
            quality = row.get("capture_quality") or {}
            floor = row.get("semantic_floor") or {}
            phase_order = row.get("semantic_phase_order_guard") or {}
            policy = row.get("alignment_policy") or {}
            if row["kind"] == "positive":
                threshold = f">= {row.get('min_score')}"
                status = "PASS" if row["passed"] else "FAIL"
            elif row["kind"] == "negative":
                threshold = f"<= {row.get('max_score')} 或重采/语义失败"
                status = "PASS" if row["passed"] else "FAIL"
            else:
                threshold = "diagnostic"
                status = "DIAG"
            reason = quality.get("reason") or phase_order.get("reason") or floor.get("reason") or "-"
            lines.append(
                f"| {row['variant']} | {row['kind']} | {status} | "
                f"{_fmt(row['score'])} | {threshold} | {_fmt(row['length_ratio'])} | "
                f"{policy.get('mode') or '-'} | {quality.get('status') or '-'} | {reason} | {row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 该门补充静止 padding 门：这里额外帧是移动手部，不是重复第一帧或最后一帧。",
            "- 该门补充重复动作门：这里不是完整动作重复，而是非语义入场/退场污染。",
            "- 该门是合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run moving setup/exit robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_moving_setup_exit_robustness_gate_current"))
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
        "claim_policy": "synthetic moving setup/exit robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": backend_status,
        "passed": passed,
        "min_score": args.min_score,
        "accepted_negative_quality": sorted(ACCEPTED_NEGATIVE_QUALITY),
        "results": results,
    }

    json_path = output_dir / "flower_jump_moving_setup_exit_robustness_gate.json"
    md_path = output_dir / "flower_jump_moving_setup_exit_robustness_gate.md"
    csv_path = output_dir / "flower_jump_moving_setup_exit_robustness_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳动态入场退场鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳动态入场退场鲁棒性报告：{md_path}")
    print(f"已生成花/跳动态入场退场鲁棒性 CSV：{csv_path}")
    print(f"综合状态：{'PASS' if passed else 'FAIL'}")
    for item in results:
        print(
            f"- {item['word']}: {'PASS' if item['gate_pass'] else 'FAIL'} "
            f"positive_min={_fmt(item['weakest_positive_score'])} "
            f"entry_only_max={_fmt(item['strongest_negative_score'])} "
            f"diagnostic_min={_fmt(item['diagnostic_lowest_score'])}"
        )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

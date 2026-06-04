#!/usr/bin/env python3
"""Stress-test flower/jump scoring against repeated actions in one recording.

In real browser retests, a user may sign once, hesitate, and sign again before
stopping the capture. A robust scorer should still find one complete semantic
instance and keep the result high. Very short setup-only clips should remain
low or be diagnosed as recapture/semantic failures.

This script edits cached skeleton sequences in memory only. It does not call
/api/score, run Holistic, move the web marker, or restart 5080.
"""

from __future__ import annotations

import argparse
import csv
import json
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np

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
BASE_GROUPS = ["pose", "left_hand", "right_hand", "left_hand_shape", "right_hand_shape", "face"]
ACCEPTED_NEGATIVE_QUALITY = {"needs_recapture", "semantic_mismatch"}

Segment = Union[str, Tuple[str, float, float], Tuple[str, float, int]]
QueryFactory = Callable[[SequenceData, Any], SequenceData]


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


def _template_json(template_root: Path, word: str) -> Path:
    path = template_root / word / f"{word}_holistic_results.json"
    if not path.exists():
        raise FileNotFoundError(f"missing template json for {word}: {path}")
    return path


def _fmt(value: Any, digits: int = 3) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "-"


def _strip_to_base_groups(seq: SequenceData, name: str) -> SequenceData:
    items: List[FrameFeature] = []
    for frame in seq.features:
        parts: List[np.ndarray] = []
        masks: List[np.ndarray] = []
        groups: Dict[str, slice] = {}
        start = 0
        for group in BASE_GROUPS:
            if group not in frame.groups:
                continue
            sl = frame.groups[group]
            vector = frame.vector[sl].copy()
            mask = frame.mask[sl].copy()
            groups[group] = slice(start, start + vector.size)
            start += vector.size
            parts.append(vector)
            masks.append(mask)
        if not parts:
            continue
        items.append(
            FrameFeature(
                frame_idx=len(items),
                timestamp_sec=len(items) / max(float(seq.fps or 0.0), 1.0),
                vector=np.concatenate(parts).astype(np.float32),
                mask=np.concatenate(masks).astype(np.float32),
                groups=groups,
                presence=dict(frame.presence),
                frame_weight=float(frame.frame_weight),
                semantic_phase=float(frame.semantic_phase),
            )
        )
    return SequenceData(f"{seq.source}::{name}", seq.mode, seq.fps, len(items), items)


def _rebuild_derived_groups(seq: SequenceData, profile: Any, name: str) -> SequenceData:
    rebuilt = _sequence_with_relative_motion_features(_strip_to_base_groups(seq, name), profile)
    rebuilt.source = f"{seq.source}::{name}::rebuilt"
    return rebuilt


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


def _slice_items(seq: SequenceData, start_ratio: float, end_ratio: float) -> List[FrameFeature]:
    items = list(seq.features)
    if not items:
        return []
    n = len(items)
    start = max(0, min(n - 1, int(round(n * float(start_ratio)))))
    end = max(start + 1, min(n, int(round(n * float(end_ratio)))))
    return [_clone_frame(frame) for frame in items[start:end]]


def _hold_items(seq: SequenceData, ratio: float, count: int) -> List[FrameFeature]:
    if not seq.features or count <= 0:
        return []
    idx = max(0, min(len(seq.features) - 1, int(round((len(seq.features) - 1) * float(ratio)))))
    return [_clone_frame(seq.features[idx]) for _ in range(int(count))]


def _compose(seq: SequenceData, profile: Any, name: str, segments: Sequence[Segment]) -> SequenceData:
    items: List[FrameFeature] = []
    for segment in segments:
        if segment == "all":
            items.extend(_clone_frame(frame) for frame in seq.features)
            continue
        kind = segment[0]
        if kind == "slice":
            _, start, end = segment
            items.extend(_slice_items(seq, float(start), float(end)))
        elif kind == "hold":
            _, ratio, count = segment
            items.extend(_hold_items(seq, float(ratio), int(count)))
        else:
            raise ValueError(f"unknown segment kind: {kind}")
    raw = _clone_sequence(seq, name, _renumber(items, seq.fps))
    return _rebuild_derived_groups(raw, profile, name)


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
    mid_pause = 5 if word == "花" else 3
    specs = [
        _spec(
            "repeat_full_2x",
            "positive",
            lambda seq, profile: _compose(seq, profile, "repeat_full_2x", ["all", "all"]),
            "完整动作连续做两遍，录制应能匹配其中一个完整实例。",
            min_score=min_score,
        ),
        _spec(
            "repeat_full_2x_mid_pause",
            "positive",
            lambda seq, profile: _compose(seq, profile, "repeat_full_2x_mid_pause", ["all", ("hold", 1.0, mid_pause), "all"]),
            "两遍动作之间有短暂停顿，模拟用户重做一次后才停止。",
            min_score=min_score,
        ),
        _spec(
            "prefix_partial_then_full",
            "positive",
            lambda seq, profile: _compose(seq, profile, "prefix_partial_then_full", [("slice", 0.0, 0.35), "all"]),
            "先做了不完整开头，然后补做一遍完整动作。",
            min_score=min_score,
        ),
        _spec(
            "full_then_suffix_partial",
            "positive",
            lambda seq, profile: _compose(seq, profile, "full_then_suffix_partial", ["all", ("slice", 0.65, 1.0)]),
            "完整动作后又开始下一遍的后段/收尾，停止偏晚。",
            min_score=min_score,
        ),
        _spec(
            "core_repeat_middle",
            "positive",
            lambda seq, profile: _compose(
                seq,
                profile,
                "core_repeat_middle",
                [("slice", 0.0, 0.20), ("slice", 0.20, 0.80), ("slice", 0.20, 0.80), ("slice", 0.80, 1.0)],
            ),
            "核心动作段重复一次，完整起止仍可见。",
            min_score=min_score,
        ),
        _spec(
            "setup_only_35pct_negative",
            "negative",
            lambda seq, profile: _compose(seq, profile, "setup_only_35pct_negative", [("slice", 0.0, 0.35)]),
            "只录到动作开头 setup，不能当作完整手语通过。",
            max_score=45.0,
        ),
        _spec(
            "repeat_full_3x_diagnostic",
            "diagnostic",
            lambda seq, profile: _compose(seq, profile, "repeat_full_3x_diagnostic", ["all", "all", "all"]),
            "连续做三遍属于长录制诊断边界，记录分数但不作为硬门。",
        ),
    ]
    if word == "花":
        specs.append(
            _spec(
                "late_bloom_only_diagnostic",
                "diagnostic",
                lambda seq, profile: _compose(seq, profile, "late_bloom_only_diagnostic", [("slice", 0.65, 1.0)]),
                "花的后段可能仍包含绽放核心，作为诊断边界记录，不设负向门。",
            )
        )
    elif word == "跳":
        specs.append(
            _spec(
                "landing_only_35pct_negative",
                "negative",
                lambda seq, profile: _compose(seq, profile, "landing_only_35pct_negative", [("slice", 0.65, 1.0)]),
                "跳只录到后段落点/收尾，缺少完整起跳关系。",
                max_score=45.0,
            )
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
        "# 花/跳重复动作录制鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，在骨架序列层面拼接/重复动作片段并重建派生特征；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：用户在一次网页录制中多做一遍或停止偏晚时，完整动作实例仍可被高分识别；setup-only 片段不能通过。",
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
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向重复 | 不完整最高分 | 最强不完整负例 | 诊断分数范围 |")
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
            "- 正向重复验证网页录制里出现“先试一次、再完整做一次”或“完整做完后又开始下一遍”时，评分仍能落在正常区间。",
            "- 负向不完整样本只验证 setup-only 或缺核心的极短片段不能关闭目标；不稳定半段保留为诊断输出。",
            "- 该门是合成重复压力测试，不能替代正式 marker 后的真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run repeated-action robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_action_repeat_robustness_gate_current"))
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
        "claim_policy": "synthetic repeated-action robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": backend_status,
        "passed": passed,
        "min_score": args.min_score,
        "accepted_negative_quality": sorted(ACCEPTED_NEGATIVE_QUALITY),
        "results": results,
    }

    json_path = output_dir / "flower_jump_action_repeat_robustness_gate.json"
    md_path = output_dir / "flower_jump_action_repeat_robustness_gate.md"
    csv_path = output_dir / "flower_jump_action_repeat_robustness_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳重复动作鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳重复动作鲁棒性报告：{md_path}")
    print(f"已生成花/跳重复动作鲁棒性 CSV：{csv_path}")
    print(f"综合状态：{'PASS' if passed else 'FAIL'}")
    for item in results:
        print(
            f"- {item['word']}: {'PASS' if item['gate_pass'] else 'FAIL'} "
            f"positive_min={_fmt(item['weakest_positive_score'])} "
            f"incomplete_max={_fmt(item['strongest_negative_score'])}"
        )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

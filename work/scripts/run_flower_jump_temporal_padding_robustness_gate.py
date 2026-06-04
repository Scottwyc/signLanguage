#!/usr/bin/env python3
"""Stress-test flower/jump scoring against temporal padding and static holds.

Browser recordings often include preparation or ending stillness around the
actual sign. A robust semantic-DTW scorer should tolerate extra static frames
when the complete core action is present, while rejecting purely static clips.

This script edits cached skeleton sequences in memory only. It does not call
/api/score, run Holistic, move marker, or restart 5080.
"""

from __future__ import annotations

import argparse
import csv
import json
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from score_holistic_sequence_mvp import (
    DEFAULT_SEMANTIC_PROFILE_JSON,
    FrameFeature,
    SequenceData,
    _clone_sequence,
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
ACCEPTED_NEGATIVE_QUALITY = {"needs_recapture", "semantic_mismatch"}


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


def _repeat_feature(feature: FrameFeature, count: int) -> List[FrameFeature]:
    return [feature for _ in range(max(0, int(count)))]


def _pad_sequence(seq: SequenceData, name: str, prefix_ratio: float = 0.0, suffix_ratio: float = 0.0) -> SequenceData:
    items = list(seq.features)
    if not items:
        return _clone_sequence(seq, name, [])
    prefix = max(0, int(round(len(items) * float(prefix_ratio))))
    suffix = max(0, int(round(len(items) * float(suffix_ratio))))
    selected = _repeat_feature(items[0], prefix) + items + _repeat_feature(items[-1], suffix)
    return _clone_sequence(seq, name, selected)


def _repeat_each(seq: SequenceData, name: str, repeats: int) -> SequenceData:
    selected: List[FrameFeature] = []
    for item in seq.features:
        selected.extend(_repeat_feature(item, repeats))
    return _clone_sequence(seq, name, selected)


def _static_hold(seq: SequenceData, name: str, anchor: str) -> SequenceData:
    items = list(seq.features)
    if not items:
        return _clone_sequence(seq, name, [])
    if anchor == "start":
        frame = items[0]
    elif anchor == "end":
        frame = items[-1]
    else:
        frame = items[len(items) // 2]
    return _clone_sequence(seq, name, _repeat_feature(frame, len(items)))


def _variant_specs(seq: SequenceData) -> List[Dict[str, Any]]:
    return [
        {
            "variant": "prefix_hold_25pct",
            "kind": "positive",
            "expected": "score_high",
            "min_score": 70.0,
            "query": _pad_sequence(seq, "prefix_hold_25pct", prefix_ratio=0.25),
            "rationale": "动作前有准备静止帧，但完整动作仍在。",
        },
        {
            "variant": "suffix_hold_25pct",
            "kind": "positive",
            "expected": "score_high",
            "min_score": 70.0,
            "query": _pad_sequence(seq, "suffix_hold_25pct", suffix_ratio=0.25),
            "rationale": "动作后有结束静止帧，但完整动作仍在。",
        },
        {
            "variant": "both_hold_20pct",
            "kind": "positive",
            "expected": "score_high",
            "min_score": 70.0,
            "query": _pad_sequence(seq, "both_hold_20pct", prefix_ratio=0.20, suffix_ratio=0.20),
            "rationale": "采集窗口前后都有静止帧，但核心动作完整。",
        },
        {
            "variant": "prefix_hold_50pct",
            "kind": "positive",
            "expected": "score_high",
            "min_score": 65.0,
            "query": _pad_sequence(seq, "prefix_hold_50pct", prefix_ratio=0.50),
            "rationale": "较长准备静止帧，仍应主要由核心动作决定。",
        },
        {
            "variant": "slow_repeat_each_2x",
            "kind": "positive",
            "expected": "score_high",
            "min_score": 70.0,
            "query": _repeat_each(seq, "slow_repeat_each_2x", repeats=2),
            "rationale": "动作速度变慢但语义相位完整。",
        },
        {
            "variant": "static_hold_start",
            "kind": "negative",
            "expected": "not_accepted",
            "max_score": 45.0,
            "query": _static_hold(seq, "static_hold_start", "start"),
            "rationale": "只有起始静止姿态，缺少动作语义。",
        },
        {
            "variant": "static_hold_mid",
            "kind": "negative",
            "expected": "not_accepted",
            "max_score": 45.0,
            "query": _static_hold(seq, "static_hold_mid", "mid"),
            "rationale": "只有中间静止姿态，缺少起止动态。",
        },
        {
            "variant": "static_hold_end",
            "kind": "negative",
            "expected": "not_accepted",
            "max_score": 45.0,
            "query": _static_hold(seq, "static_hold_end", "end"),
            "rationale": "只有结束静止姿态，缺少完整动作过程。",
        },
    ]


def _row_passed(row: Dict[str, Any]) -> bool:
    score = float(row["score"])
    if row["kind"] == "positive":
        return score >= float(row["min_score"])
    quality = (row.get("capture_quality") or {}).get("status")
    return score <= float(row["max_score"]) or quality in ACCEPTED_NEGATIVE_QUALITY


def _run_word(
    word: str,
    template_root: Path,
    semantic_profile_json: Path,
    feature_mode: str,
) -> Dict[str, Any]:
    standard_json = _template_json(template_root, word)
    standard = load_sequence(standard_json, feature_mode, force_bbox=False)
    profile = load_semantic_profile(word, semantic_profile_json)
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(standard):
        result = run_pair(standard, spec["query"], semantic_profile=profile, enable_cross_check=False)
        score_scale = result.get("score_scale") or {}
        row = {
            "variant": spec["variant"],
            "kind": spec["kind"],
            "expected": spec["expected"],
            "min_score": spec.get("min_score"),
            "max_score": spec.get("max_score"),
            "rationale": spec["rationale"],
            "score": float(result["prototype_score"]),
            "dtw_distance": float(result["dtw_distance"]),
            "normalized_distance": float(result["normalized_distance"]),
            "query_length": len(spec["query"].features),
            "length_ratio": len(spec["query"].features) / max(len(standard.features), 1),
            "alignment_policy": result.get("alignment_policy"),
            "capture_quality": score_scale.get("capture_quality"),
            "semantic_floor": score_scale.get("semantic_floor"),
            "action_window": result.get("action_window"),
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
        "semantic_profile": _profile_summary(profile),
        "gate_pass": all(bool(row["passed"]) for row in rows),
        "weakest_positive_score": float(weakest_positive["score"]) if weakest_positive else None,
        "weakest_positive_variant": weakest_positive["variant"] if weakest_positive else "",
        "strongest_negative_score": float(strongest_negative["score"]) if strongest_negative else None,
        "strongest_negative_variant": strongest_negative["variant"] if strongest_negative else "",
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
        "max_score",
        "query_length",
        "length_ratio",
        "alignment_policy",
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
                writer.writerow(
                    {
                        "word": item["word"],
                        "variant": row.get("variant"),
                        "kind": row.get("kind"),
                        "passed": row.get("passed"),
                        "score": row.get("score"),
                        "min_score": row.get("min_score"),
                        "max_score": row.get("max_score"),
                        "query_length": row.get("query_length"),
                        "length_ratio": row.get("length_ratio"),
                        "alignment_policy": row.get("alignment_policy"),
                        "capture_quality_status": quality.get("status"),
                        "capture_quality_reason": quality.get("reason"),
                        "semantic_floor_source": floor.get("source"),
                        "semantic_floor_reason": floor.get("reason"),
                        "rationale": row.get("rationale"),
                    }
                )


def _build_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# 花/跳静止 padding 与时序鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，在骨架序列层面加入前后静止帧或静态假动作；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：完整动作被前后静止帧包围或整体变慢时仍高分；纯静态起始/中段/结束姿态不能通过。",
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
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向变体 | 静态最高分 | 最强静态变体 |")
    lines.append("|---|---|---:|---|---:|---|")
    for item in payload["results"]:
        lines.append(
            f"| {item['word']} | {'PASS' if item['gate_pass'] else 'FAIL'} | "
            f"{_fmt(item['weakest_positive_score'])} | {item['weakest_positive_variant']} | "
            f"{_fmt(item['strongest_negative_score'])} | {item['strongest_negative_variant']} |"
        )
    lines.append("")
    lines.append("## 分项明细")
    for item in payload["results"]:
        lines.extend(["", f"### {item['word']}", "", f"- 标准序列：`{item['standard_json']}`", ""])
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | 长度比 | capture_quality | reason | 说明 |")
        lines.append("|---|---|---|---:|---|---:|---|---|---|")
        for row in sorted(item["variants"], key=lambda x: (x["kind"], float(x["score"]))):
            quality = row.get("capture_quality") or {}
            floor = row.get("semantic_floor") or {}
            threshold = f">= {row.get('min_score')}" if row["kind"] == "positive" else f"<= {row.get('max_score')} 或重采/语义失败"
            reason = quality.get("reason") or floor.get("reason") or "-"
            lines.append(
                f"| {row['variant']} | {row['kind']} | {'PASS' if row['passed'] else 'FAIL'} | "
                f"{_fmt(row['score'])} | {threshold} | {_fmt(row['length_ratio'])} | "
                f"{quality.get('status') or '-'} | {reason} | {row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 正向 padding 变体验证真实采集窗口含准备/结束静止帧时仍可对齐核心动作。",
            "- 负向静态变体验证仅有手形或姿态、没有动态语义时不会被误判为通过。",
            "- 该门是合成时序压力测试，不能替代真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run temporal padding robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_temporal_padding_robustness_gate_current"))
    parser.add_argument("--words", nargs="+", default=DEFAULT_WORDS)
    parser.add_argument("--feature-mode", choices=["auto", "landmark", "bbox"], default="auto")
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--status-timeout-sec", type=float, default=3.0)
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
        )
        for word in args.words
    ]
    backend_status = _load_backend_status(args.backend_url, args.status_timeout_sec)
    passed = all(bool(item["gate_pass"]) for item in results)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "claim_policy": "synthetic temporal padding robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": backend_status,
        "passed": passed,
        "accepted_negative_quality": sorted(ACCEPTED_NEGATIVE_QUALITY),
        "results": results,
    }

    json_path = output_dir / "flower_jump_temporal_padding_robustness_gate.json"
    md_path = output_dir / "flower_jump_temporal_padding_robustness_gate.md"
    csv_path = output_dir / "flower_jump_temporal_padding_robustness_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳时序 padding 鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳时序 padding 鲁棒性报告：{md_path}")
    print(f"已生成花/跳时序 padding 鲁棒性 CSV：{csv_path}")
    print(f"综合状态：{'PASS' if passed else 'FAIL'}")
    for item in results:
        print(
            f"- {item['word']}: {'PASS' if item['gate_pass'] else 'FAIL'} "
            f"positive_min={_fmt(item['weakest_positive_score'])} "
            f"static_max={_fmt(item['strongest_negative_score'])}"
        )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

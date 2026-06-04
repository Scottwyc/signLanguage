#!/usr/bin/env python3
"""Stress-test flower/jump scoring against semantic phase warps and disorder.

Real browser signing speed is not uniform: a user may start slowly, finish
quickly, pause around the core pose, or produce mild frame-order jitter from
sampling. A robust semantic-DTW scorer should tolerate monotonic phase warps
when the complete action is present, while rejecting reversed or phase-scrambled
clips.

This script edits cached skeleton sequences in memory only. It does not call
/api/score, run Holistic, move marker, or restart 5080.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
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


def _pick(items: Sequence[FrameFeature], pos: float) -> FrameFeature:
    index = int(round(max(0.0, min(float(len(items) - 1), pos))))
    return items[index]


def _warp_sequence(seq: SequenceData, name: str, mode: str) -> SequenceData:
    items = list(seq.features)
    n = len(items)
    if n <= 1:
        return _clone_sequence(seq, name, items)
    selected: List[FrameFeature] = []
    for i in range(n):
        t = i / max(n - 1, 1)
        if mode == "slow_start_fast_end":
            src_t = t**1.7
        elif mode == "fast_start_slow_end":
            src_t = 1.0 - (1.0 - t) ** 1.7
        elif mode == "ease_in_out":
            src_t = t * t * (3.0 - 2.0 * t)
        elif mode == "ordered_jitter":
            jitter = 0.035 * math.sin(i * 1.618)
            src_t = max(0.0, min(1.0, t + jitter))
        else:
            src_t = t
        selected.append(_pick(items, src_t * (n - 1)))
    return _clone_sequence(seq, name, selected)


def _middle_hold(seq: SequenceData, name: str, ratio: float) -> SequenceData:
    items = list(seq.features)
    if not items:
        return _clone_sequence(seq, name, [])
    mid = len(items) // 2
    hold = [items[mid]] * max(1, int(round(len(items) * ratio)))
    return _clone_sequence(seq, name, items[: mid + 1] + hold + items[mid + 1 :])


def _reverse(seq: SequenceData, name: str) -> SequenceData:
    return _clone_sequence(seq, name, list(reversed(seq.features)))


def _swap_halves(seq: SequenceData, name: str) -> SequenceData:
    items = list(seq.features)
    if len(items) < 4:
        return _clone_sequence(seq, name, items)
    mid = len(items) // 2
    return _clone_sequence(seq, name, items[mid:] + items[:mid])


def _scramble_three_phases(seq: SequenceData, name: str) -> SequenceData:
    items = list(seq.features)
    if len(items) < 6:
        return _swap_halves(seq, name)
    a = len(items) // 3
    b = (2 * len(items)) // 3
    return _clone_sequence(seq, name, items[b:] + items[a:b] + items[:a])


def _variant_specs(seq: SequenceData) -> List[Dict[str, Any]]:
    return [
        {
            "variant": "slow_start_fast_end",
            "kind": "positive",
            "expected": "score_high",
            "min_score": 70.0,
            "query": _warp_sequence(seq, "slow_start_fast_end", "slow_start_fast_end"),
            "rationale": "动作相位单调但前段慢、后段快。",
        },
        {
            "variant": "fast_start_slow_end",
            "kind": "positive",
            "expected": "score_high",
            "min_score": 70.0,
            "query": _warp_sequence(seq, "fast_start_slow_end", "fast_start_slow_end"),
            "rationale": "动作相位单调但前段快、后段慢。",
        },
        {
            "variant": "ease_in_out",
            "kind": "positive",
            "expected": "score_high",
            "min_score": 70.0,
            "query": _warp_sequence(seq, "ease_in_out", "ease_in_out"),
            "rationale": "自然加速再减速，核心语义顺序不变。",
        },
        {
            "variant": "ordered_jitter",
            "kind": "positive",
            "expected": "score_high",
            "min_score": 68.0,
            "query": _warp_sequence(seq, "ordered_jitter", "ordered_jitter"),
            "rationale": "轻微采样抖动但整体相位顺序不变。",
        },
        {
            "variant": "middle_hold_30pct",
            "kind": "positive",
            "expected": "score_high",
            "min_score": 70.0,
            "query": _middle_hold(seq, "middle_hold_30pct", 0.30),
            "rationale": "核心姿态附近短暂停留，但完整动作仍在。",
        },
        {
            "variant": "reverse_full",
            "kind": "negative",
            "expected": "not_accepted",
            "max_score": 50.0,
            "query": _reverse(seq, "reverse_full"),
            "rationale": "完整倒放，动作语义起终点和方向相反。",
        },
        {
            "variant": "swap_halves",
            "kind": "negative",
            "expected": "not_accepted",
            "max_score": 50.0,
            "query": _swap_halves(seq, "swap_halves"),
            "rationale": "前后半段错序，语义相位不连续。",
        },
        {
            "variant": "scramble_three_phases",
            "kind": "negative",
            "expected": "not_accepted",
            "max_score": 50.0,
            "query": _scramble_three_phases(seq, "scramble_three_phases"),
            "rationale": "结束、中段、开始三相位乱序。",
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
        "# 花/跳语义相位顺序鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，在骨架序列层面加入相位速度变形或错序假动作；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：单调相位快慢变化仍高分；倒放、前后错序、三相位乱序不能通过。",
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
    lines.append("| 目标词 | 状态 | 单调变形最低分 | 最弱单调变形 | 错序最高分 | 最强错序变体 |")
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
            "- 正向相位变形验证不同用户动作速度曲线不一致时，DTW 仍能对齐核心语义顺序。",
            "- 负向错序变体验证评分不是只看静态骨架集合，而是看动作语义的起点、中段和终点顺序。",
            "- 该门是合成时序压力测试，不能替代真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run semantic phase-order robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_phase_order_robustness_gate_current"))
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
        "claim_policy": "synthetic semantic phase-order robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": backend_status,
        "passed": passed,
        "accepted_negative_quality": sorted(ACCEPTED_NEGATIVE_QUALITY),
        "results": results,
    }

    json_path = output_dir / "flower_jump_phase_order_robustness_gate.json"
    md_path = output_dir / "flower_jump_phase_order_robustness_gate.md"
    csv_path = output_dir / "flower_jump_phase_order_robustness_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳相位顺序鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳相位顺序鲁棒性报告：{md_path}")
    print(f"已生成花/跳相位顺序鲁棒性 CSV：{csv_path}")
    print(f"综合状态：{'PASS' if passed else 'FAIL'}")
    for item in results:
        print(
            f"- {item['word']}: {'PASS' if item['gate_pass'] else 'FAIL'} "
            f"positive_min={_fmt(item['weakest_positive_score'])} "
            f"disordered_max={_fmt(item['strongest_negative_score'])}"
        )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

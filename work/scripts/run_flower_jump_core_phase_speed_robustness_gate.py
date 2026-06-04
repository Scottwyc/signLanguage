#!/usr/bin/env python3
"""Stress-test flower/jump scoring against core-phase speed style changes.

General temporal-rate gates cover whole-sequence fast/slow signing. This gate
targets the word-specific semantic core: the flower opening phase or the jump
takeoff/relation phase may be signed faster, slower, or with a short local
hesitation while the action remains correct.

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

from run_flower_jump_temporal_rate_robustness_gate import (
    _fmt,
    _json_default,
    _load_backend_status,
    _rebuild_derived_groups,
    _template_json,
)
from score_holistic_sequence_mvp import (
    DEFAULT_SEMANTIC_PROFILE_JSON,
    FrameFeature,
    SequenceData,
    _clone_frame,
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

QueryFactory = Callable[[SequenceData, Any], SequenceData]


def _core_bounds(word: str) -> Tuple[float, float]:
    if word == "花":
        return 0.34, 0.78
    return 0.22, 0.76


def _segment_bounds(seq: SequenceData, start_ratio: float, end_ratio: float) -> Tuple[int, int]:
    n = len(seq.features)
    if n <= 1:
        return 0, n
    start = max(0, min(n - 2, int(round((n - 1) * float(start_ratio)))))
    end = max(start + 2, min(n, int(round((n - 1) * float(end_ratio))) + 1))
    return start, end


def _resample_frames(frames: Sequence[FrameFeature], out_len: int) -> List[FrameFeature]:
    if not frames:
        return []
    out_len = max(1, int(out_len))
    if len(frames) == 1 or out_len == 1:
        return [_clone_frame(frames[len(frames) // 2])]
    positions = np.linspace(0.0, float(len(frames) - 1), out_len)
    return [_clone_frame(frames[int(round(float(pos)))]) for pos in positions]


def _renumber_sequence(seq: SequenceData, name: str, frames: Sequence[FrameFeature]) -> SequenceData:
    return _clone_sequence(seq, name, [_clone_frame(frame) for frame in frames])


def _core_rate(seq: SequenceData, profile: Any, word: str, name: str, factor: float) -> SequenceData:
    start_ratio, end_ratio = _core_bounds(word)
    start, end = _segment_bounds(seq, start_ratio, end_ratio)
    core = list(seq.features[start:end])
    out_len = max(2, int(round(len(core) * float(factor))))
    frames = list(seq.features[:start]) + _resample_frames(core, out_len) + list(seq.features[end:])
    return _rebuild_derived_groups(_renumber_sequence(seq, name, frames), profile)


def _core_ease(seq: SequenceData, profile: Any, word: str, name: str, mode: str) -> SequenceData:
    start_ratio, end_ratio = _core_bounds(word)
    start, end = _segment_bounds(seq, start_ratio, end_ratio)
    core = list(seq.features[start:end])
    if len(core) <= 2:
        return _rebuild_derived_groups(_renumber_sequence(seq, name, seq.features), profile)
    n = len(core)
    positions: List[float] = []
    for i in range(n):
        t = i / max(n - 1, 1)
        if mode == "fast_then_slow":
            src_t = 1.0 - (1.0 - t) ** 1.55
        elif mode == "slow_then_fast":
            src_t = t**1.55
        else:
            src_t = t + 0.06 * np.sin(2.0 * np.pi * t)
        positions.append(max(0.0, min(1.0, float(src_t))) * (n - 1))
    positions = np.maximum.accumulate(np.asarray(positions, dtype=np.float32)).tolist()
    warped = [_clone_frame(core[int(round(pos))]) for pos in positions]
    frames = list(seq.features[:start]) + warped + list(seq.features[end:])
    return _rebuild_derived_groups(_renumber_sequence(seq, name, frames), profile)


def _core_pause(seq: SequenceData, profile: Any, word: str, name: str, pause_ratio: float) -> SequenceData:
    start_ratio, end_ratio = _core_bounds(word)
    start, end = _segment_bounds(seq, start_ratio, end_ratio)
    core = list(seq.features[start:end])
    if not core:
        return _rebuild_derived_groups(_renumber_sequence(seq, name, seq.features), profile)
    mid = len(core) // 2
    hold_count = max(1, int(round(len(core) * float(pause_ratio))))
    frames = (
        list(seq.features[:start])
        + core[: mid + 1]
        + [_clone_frame(core[mid]) for _ in range(hold_count)]
        + core[mid + 1 :]
        + list(seq.features[end:])
    )
    return _rebuild_derived_groups(_renumber_sequence(seq, name, frames), profile)


def _core_gap(seq: SequenceData, profile: Any, word: str, name: str, gap_ratio: float) -> SequenceData:
    start_ratio, end_ratio = _core_bounds(word)
    start, end = _segment_bounds(seq, start_ratio, end_ratio)
    core = list(seq.features[start:end])
    if len(core) < 4:
        return _rebuild_derived_groups(_renumber_sequence(seq, name, seq.features), profile)
    gap_len = max(1, int(round(len(core) * float(gap_ratio))))
    gap_start = max(1, (len(core) - gap_len) // 2)
    gap_end = min(len(core) - 1, gap_start + gap_len)
    kept_core = core[:gap_start] + core[gap_end:]
    frames = list(seq.features[:start]) + kept_core + list(seq.features[end:])
    return _rebuild_derived_groups(_renumber_sequence(seq, name, frames), profile)


def _spec(
    variant: str,
    kind: str,
    query: QueryFactory,
    rationale: str,
    min_score: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": kind,
        "query": query,
        "min_score": min_score,
        "gated": kind == "positive",
        "rationale": rationale,
    }


def _variant_specs(word: str, min_score: float) -> List[Dict[str, Any]]:
    core_name = "bloom" if word == "花" else "jump_relation"
    slow_factor = 1.55 if word == "花" else 1.40
    slow_variant = f"{core_name}_core_slow_{slow_factor:.2f}x"
    specs = [
        _spec(
            "self_recomputed",
            "positive",
            lambda seq, profile: _core_rate(seq, profile, word, "self_recomputed", 1.0),
            "标准序列剥离派生组后重建 motion/relation，应保持近满分。",
            min_score=95.0,
        ),
        _spec(
            f"{core_name}_core_fast_0.70x",
            "positive",
            lambda seq, profile: _core_rate(seq, profile, word, f"{core_name}_core_fast_0.70x", 0.70),
            "词义核心段更快，但核心过程仍完整可见。",
            min_score=min_score,
        ),
        _spec(
            slow_variant,
            "positive",
            lambda seq, profile, slow_factor=slow_factor, slow_variant=slow_variant: _core_rate(
                seq,
                profile,
                word,
                slow_variant,
                slow_factor,
            ),
            "词义核心段更慢，局部帧更密但语义顺序不变。",
            min_score=min_score,
        ),
        _spec(
            f"{core_name}_core_fast_then_slow",
            "positive",
            lambda seq, profile: _core_ease(seq, profile, word, f"{core_name}_core_fast_then_slow", "fast_then_slow"),
            "核心段前半快、后半慢，模拟用户在关键姿态附近减速。",
            min_score=min_score,
        ),
        _spec(
            f"{core_name}_core_slow_then_fast",
            "positive",
            lambda seq, profile: _core_ease(seq, profile, word, f"{core_name}_core_slow_then_fast", "slow_then_fast"),
            "核心段前半慢、后半快，模拟用户完成核心动作时加速。",
            min_score=min_score,
        ),
        _spec(
            f"{core_name}_core_pause_0.25",
            "positive",
            lambda seq, profile: _core_pause(seq, profile, word, f"{core_name}_core_pause_0.25", 0.25),
            "核心段有短暂停顿，但动作起止和关键形态完整。",
            min_score=min_score,
        ),
        _spec(
            f"{core_name}_core_fast_0.45x_diagnostic",
            "diagnostic",
            lambda seq, profile: _core_rate(seq, profile, word, f"{core_name}_core_fast_0.45x_diagnostic", 0.45),
            "核心段极度压缩，作为快动作/欠采样边界。",
        ),
        _spec(
            f"{core_name}_core_gap_0.45_diagnostic",
            "diagnostic",
            lambda seq, profile: _core_gap(seq, profile, word, f"{core_name}_core_gap_0.45_diagnostic", 0.45),
            "核心段中部被跳过，记录缺核心边界，不作为普通速率鲁棒性。",
        ),
    ]
    if word == "跳":
        specs.append(
            _spec(
                "jump_relation_core_slow_1.55x_diagnostic",
                "diagnostic",
                lambda seq, profile: _core_rate(
                    seq,
                    profile,
                    word,
                    "jump_relation_core_slow_1.55x_diagnostic",
                    1.55,
                ),
                "跳的核心段强拉伸会触发两手关系覆盖边界，只记录诊断。",
            )
        )
    return specs


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
        "query_length",
        "standard_length",
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
                        "query_length": row.get("query_length"),
                        "standard_length": item.get("standard_length"),
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
        "# 花/跳核心相位速度鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，只改变词义核心窗口内的帧密度/速度曲线，并重建 motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：`花` 的绽放核心和 `跳` 的起跳/双手关系核心快慢不同仍可评分；核心中段被跳过只记录诊断边界。",
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
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向核心速度 | 诊断最低分 | 最弱诊断边界 | 门槛 |")
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
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | 长度比 | alignment | capture_quality | reason | 说明 |")
        lines.append("|---|---|---|---:|---|---:|---|---|---|---|")
        for row in sorted(item["variants"], key=lambda value: (value["kind"], float(value["score"]))):
            quality = row.get("capture_quality") or {}
            floor = row.get("semantic_floor") or {}
            phase_order = row.get("semantic_phase_order_guard") or {}
            policy = row.get("alignment_policy") or {}
            threshold = f">= {row.get('min_score')}" if row["kind"] == "positive" else "diagnostic"
            status = "PASS" if row["passed"] else "FAIL"
            if row["kind"] == "diagnostic":
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
            "- 该门补充一般 temporal-rate gate：这里只变核心语义窗口，不做整段全局速率重采样。",
            "- 诊断核心缺口用于观察 scorer 对缺核心样本的边界，不能作为正常快慢风格放宽。",
            "- 该门是合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run core-phase speed robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_core_phase_speed_robustness_gate_current"))
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
        "claim_policy": "synthetic core-phase speed robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": backend_status,
        "passed": passed,
        "min_score": args.min_score,
        "results": results,
    }

    json_path = output_dir / "flower_jump_core_phase_speed_robustness_gate.json"
    md_path = output_dir / "flower_jump_core_phase_speed_robustness_gate.md"
    csv_path = output_dir / "flower_jump_core_phase_speed_robustness_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳核心相位速度鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳核心相位速度鲁棒性报告：{md_path}")
    print(f"已生成花/跳核心相位速度鲁棒性 CSV：{csv_path}")
    print(f"综合状态：{'PASS' if passed else 'FAIL'}")
    for item in results:
        print(
            f"- {item['word']}: {'PASS' if item['gate_pass'] else 'FAIL'} "
            f"positive_min={_fmt(item['weakest_positive_score'])} "
            f"diagnostic_min={_fmt(item['weakest_diagnostic_score'])}"
        )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

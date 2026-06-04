#!/usr/bin/env python3
"""Stress-test flower/jump scoring against temporal-rate changes.

Browser captures can preserve the full action but sample it with uneven local
speed: one phase may be over-sampled, another under-sampled, or the user may
perform the same sign faster/slower than the template. This gate rebuilds
motion-derived features after each time warp so it tests the scorer under the
kind of motion vectors the web pipeline would actually see.

The script edits cached skeleton sequences in memory only. It does not call
/api/score, run Holistic, move the web marker, or restart 5080.
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
DERIVED_GROUPS = {"two_hand_relation", "two_hand_relation_motion"}
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


def _strip_derived_groups(seq: SequenceData, name: str) -> SequenceData:
    items: List[FrameFeature] = []
    for frame in seq.features:
        vectors: List[np.ndarray] = []
        masks: List[np.ndarray] = []
        groups: Dict[str, slice] = {}
        pos = 0
        for group, sl in frame.groups.items():
            if group in DERIVED_GROUPS or group.endswith("_motion"):
                continue
            vector = frame.vector[sl].copy()
            mask = frame.mask[sl].copy()
            vectors.append(vector)
            masks.append(mask)
            groups[group] = slice(pos, pos + len(vector))
            pos += len(vector)
        if vectors:
            merged_vector = np.concatenate(vectors).astype(np.float32)
            merged_mask = np.concatenate(masks).astype(np.float32)
        else:
            merged_vector = np.zeros((0,), dtype=np.float32)
            merged_mask = np.zeros((0,), dtype=np.float32)
        item = _clone_frame(frame, vector=merged_vector, mask=merged_mask)
        item.groups = groups
        items.append(item)
    return _clone_sequence(seq, name, items)


def _rebuild_derived_groups(seq: SequenceData, profile: Any) -> SequenceData:
    stripped = _strip_derived_groups(seq, f"{seq.source}::base_groups_only")
    return _sequence_with_relative_motion_features(stripped, profile)


def _pick_by_positions(seq: SequenceData, name: str, positions: Sequence[float]) -> SequenceData:
    items = list(seq.features)
    if not items:
        return _clone_sequence(seq, name, [])
    selected: List[FrameFeature] = []
    last = len(items) - 1
    for pos in positions:
        idx = int(round(max(0.0, min(float(last), float(pos)))))
        selected.append(items[idx])
    return _clone_sequence(seq, name, selected)


def _linear_positions(length: int, out_len: int) -> np.ndarray:
    if length <= 1:
        return np.zeros((max(1, out_len),), dtype=np.float32)
    if out_len <= 1:
        return np.array([float(length // 2)], dtype=np.float32)
    return np.linspace(0.0, float(length - 1), int(out_len), dtype=np.float32)


def _warp_same_count(seq: SequenceData, name: str, mode: str) -> SequenceData:
    items = list(seq.features)
    n = len(items)
    if n <= 1:
        return _clone_sequence(seq, name, items)
    values: List[float] = []
    for i in range(n):
        t = i / max(n - 1, 1)
        if mode == "front_slow_back_fast":
            src_t = t**1.25
        elif mode == "front_fast_back_slow":
            src_t = 1.0 - (1.0 - t) ** 1.25
        elif mode == "core_slow":
            src_t = t + 0.06 * math.sin(2.0 * math.pi * t)
        elif mode == "core_fast":
            src_t = t - 0.06 * math.sin(2.0 * math.pi * t)
        elif mode == "micro_rate_jitter":
            src_t = t + 0.008 * math.sin(i * 1.73) + 0.006 * math.sin(i * 0.41)
        else:
            src_t = t
        values.append(max(0.0, min(1.0, src_t)) * (n - 1))
    positions = np.maximum.accumulate(np.asarray(values, dtype=np.float32))
    positions[0] = 0.0
    positions[-1] = float(n - 1)
    return _pick_by_positions(seq, name, positions)


def _global_rate(seq: SequenceData, name: str, ratio: float) -> SequenceData:
    n = len(seq.features)
    out_len = max(2, int(round(n * float(ratio))))
    return _pick_by_positions(seq, name, _linear_positions(n, out_len))


def _core_rate(seq: SequenceData, name: str, core_start: float, core_end: float, core_repeat: int) -> SequenceData:
    items = list(seq.features)
    if not items:
        return _clone_sequence(seq, name, [])
    n = len(items)
    start = max(0, min(n - 1, int(round((n - 1) * float(core_start)))))
    end = max(start + 1, min(n, int(round((n - 1) * float(core_end))) + 1))
    selected = items[:start] + items[start:end] * max(1, int(core_repeat)) + items[end:]
    return _clone_sequence(seq, name, selected)


def _internal_gap(seq: SequenceData, name: str, start_ratio: float, end_ratio: float) -> SequenceData:
    items = list(seq.features)
    if len(items) < 4:
        return _clone_sequence(seq, name, items)
    n = len(items)
    start = max(1, min(n - 2, int(round(n * float(start_ratio)))))
    end = max(start + 1, min(n - 1, int(round(n * float(end_ratio)))))
    base = items[:start] + items[end:]
    positions = _linear_positions(len(base), n)
    return _pick_by_positions(_clone_sequence(seq, name + "::gap_base", base), name, positions)


def _spec(
    variant: str,
    kind: str,
    query: SequenceData,
    rationale: str,
    *,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    rate_ratio: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": kind,
        "query": query,
        "min_score": min_score,
        "max_score": max_score,
        "rate_ratio": rate_ratio,
        "rationale": rationale,
    }


def _variant_specs(word: str, seq: SequenceData, min_score: float) -> List[Dict[str, Any]]:
    common = [
        _spec(
            "same_count_front_slow_back_fast",
            "positive",
            _warp_same_count(seq, "same_count_front_slow_back_fast", "front_slow_back_fast"),
            "同样帧数内前段慢、后段快，完整语义相位仍在。",
            min_score=min_score,
        ),
        _spec(
            "same_count_front_fast_back_slow",
            "positive",
            _warp_same_count(seq, "same_count_front_fast_back_slow", "front_fast_back_slow"),
            "同样帧数内前段快、后段慢，完整语义相位仍在。",
            min_score=min_score,
        ),
        _spec(
            "same_count_core_slow",
            "positive",
            _warp_same_count(seq, "same_count_core_slow", "core_slow"),
            "同样帧数内核心动作被采得更密，起止顺序不变。",
            min_score=min_score,
        ),
        _spec(
            "same_count_core_fast",
            "positive",
            _warp_same_count(seq, "same_count_core_fast", "core_fast"),
            "同样帧数内核心动作被采得更稀，仍保留核心过程。",
            min_score=min_score,
        ),
        _spec(
            "same_count_micro_rate_jitter",
            "positive",
            _warp_same_count(seq, "same_count_micro_rate_jitter", "micro_rate_jitter"),
            "浏览器采样间隔轻微不均匀，但时间顺序单调。",
            min_score=min_score,
        ),
        _spec(
            "global_fast_0.75x",
            "positive",
            _global_rate(seq, "global_fast_0.75x", 0.75),
            "用户动作整体更快，保留约 75% 帧数并重建运动特征。",
            min_score=min_score,
            rate_ratio=0.75,
        ),
        _spec(
            "global_slow_1.50x",
            "positive",
            _global_rate(seq, "global_slow_1.50x", 1.50),
            "用户动作整体更慢，约 1.5 倍采样帧并重建运动特征。",
            min_score=min_score,
            rate_ratio=1.50,
        ),
    ]
    if word == "花":
        common.extend(
            [
                _spec(
                    "bloom_core_hold_2x",
                    "positive",
                    _core_rate(seq, "bloom_core_hold_2x", 0.35, 0.72, 2),
                    "开花核心阶段停留更久，但撮合到绽放过程完整。",
                    min_score=min_score,
                    rate_ratio=1.35,
                ),
                _spec(
                    "global_fast_0.50x_diagnostic",
                    "diagnostic",
                    _global_rate(seq, "global_fast_0.50x_diagnostic", 0.50),
                    "极快采样只保留约半数帧，作为欠采样边界诊断。",
                    rate_ratio=0.50,
                ),
                _spec(
                    "global_slow_2.25x_diagnostic",
                    "diagnostic",
                    _global_rate(seq, "global_slow_2.25x_diagnostic", 2.25),
                    "极慢动作或高频重复采样，作为过采样边界诊断。",
                    rate_ratio=2.25,
                ),
                _spec(
                    "bloom_core_gap_diagnostic",
                    "diagnostic",
                    _internal_gap(seq, "bloom_core_gap_diagnostic", 0.42, 0.72),
                    "内部绽放核心被采样跳过，记录当前 scorer 边界，不作为速率负向门。",
                ),
            ]
        )
    elif word == "跳":
        common.extend(
            [
                _spec(
                    "jump_core_hold_2x",
                    "positive",
                    _core_rate(seq, "jump_core_hold_2x", 0.25, 0.70, 2),
                    "弹跳核心阶段稍慢，左右手关系和两指手形仍完整。",
                    min_score=min_score,
                    rate_ratio=1.45,
                ),
                _spec(
                    "global_fast_0.50x_diagnostic",
                    "diagnostic",
                    _global_rate(seq, "global_fast_0.50x_diagnostic", 0.50),
                    "极快弹跳只保留约半数帧，记录采样边界。",
                    rate_ratio=0.50,
                ),
                _spec(
                    "global_slow_2.25x_diagnostic",
                    "diagnostic",
                    _global_rate(seq, "global_slow_2.25x_diagnostic", 2.25),
                    "极慢弹跳或高频重复采样，记录过采样边界。",
                    rate_ratio=2.25,
                ),
                _spec(
                    "jump_relation_core_gap_diagnostic",
                    "diagnostic",
                    _internal_gap(seq, "jump_relation_core_gap_diagnostic", 0.28, 0.68),
                    "内部弹跳关系变化被采样跳过，记录当前 relation floor 边界，不作为速率负向门。",
                ),
            ]
        )
    return common


def _row_passed(row: Dict[str, Any]) -> bool:
    if row["kind"] == "diagnostic":
        return True
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
    min_score: float,
) -> Dict[str, Any]:
    standard_json = _template_json(template_root, word)
    standard = load_sequence(standard_json, feature_mode, force_bbox=False)
    profile = load_semantic_profile(word, semantic_profile_json)
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(word, standard, min_score):
        query = _rebuild_derived_groups(spec["query"], profile)
        result = run_pair(standard, query, semantic_profile=profile, enable_cross_check=False)
        score_scale = result.get("score_scale") or {}
        row = {
            "variant": spec["variant"],
            "kind": spec["kind"],
            "min_score": spec.get("min_score"),
            "max_score": spec.get("max_score"),
            "rate_ratio": spec.get("rate_ratio"),
            "rationale": spec["rationale"],
            "score": float(result["prototype_score"]),
            "dtw_distance": float(result["dtw_distance"]),
            "normalized_distance": float(result["normalized_distance"]),
            "query_length": len(query.features),
            "length_ratio": len(query.features) / max(len(standard.features), 1),
            "alignment_policy": result.get("alignment_policy"),
            "capture_quality": score_scale.get("capture_quality"),
            "semantic_floor": score_scale.get("semantic_floor"),
            "action_window": result.get("action_window"),
        }
        row["passed"] = _row_passed(row)
        rows.append(row)
    positive_rows = [row for row in rows if row["kind"] == "positive"]
    negative_rows = [row for row in rows if row["kind"] == "negative"]
    diagnostic_rows = [row for row in rows if row["kind"] == "diagnostic"]
    weakest_positive = min(positive_rows, key=lambda row: float(row["score"])) if positive_rows else None
    strongest_negative = max(negative_rows, key=lambda row: float(row["score"])) if negative_rows else None
    weakest_diagnostic = min(diagnostic_rows, key=lambda row: float(row["score"])) if diagnostic_rows else None
    return {
        "word": word,
        "standard_json": str(standard_json),
        "standard_length": len(standard.features),
        "semantic_profile": _profile_summary(profile),
        "accepted_negative_quality": sorted(ACCEPTED_NEGATIVE_QUALITY),
        "gate_pass": all(bool(row["passed"]) for row in rows),
        "weakest_positive_score": float(weakest_positive["score"]) if weakest_positive else None,
        "weakest_positive_variant": weakest_positive["variant"] if weakest_positive else "",
        "strongest_negative_score": float(strongest_negative["score"]) if strongest_negative else None,
        "strongest_negative_variant": strongest_negative["variant"] if strongest_negative else "",
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
        "max_score",
        "query_length",
        "standard_length",
        "length_ratio",
        "rate_ratio",
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
                        "standard_length": item.get("standard_length"),
                        "length_ratio": row.get("length_ratio"),
                        "rate_ratio": row.get("rate_ratio"),
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
        "# 花/跳时序速率鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 总体：`{'PASS' if payload.get('passed') else 'FAIL'}`",
        f"- 模板根目录：`{payload['template_root']}`",
        f"- 语义权重：`{payload['semantic_profile_json']}`",
        f"- 门槛：正向速率变化最低分 `>= {payload['min_score']}`；极端速率和内部核心缺口仅记录诊断边界。",
        "- 口径：只读缓存 Holistic JSON，在骨架序列层面做单调时间轴压缩/拉伸/局部速率变化，并重建 motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "",
        "## 汇总",
        "",
        "| 词条 | 状态 | 正向最低分 | 最弱正向速率扰动 | 诊断最低分 | 最弱诊断边界 |",
        "|---|---|---:|---|---:|---|",
    ]
    for item in payload["results"]:
        lines.append(
            f"| {item['word']} | {'PASS' if item['gate_pass'] else 'FAIL'} | "
            f"{_fmt(item['weakest_positive_score'])} | {item['weakest_positive_variant']} | "
            f"{_fmt(item['weakest_diagnostic_score'])} | {item['weakest_diagnostic_variant'] or '-'} |"
        )
    lines.extend(["", "## 明细", ""])
    for item in payload["results"]:
        lines.extend(
            [
                f"### {item['word']}",
                "",
                "| 变体 | 类型 | 状态 | 分数 | 阈值 | 帧数/比例 | quality | floor | 说明 |",
                "|---|---|---|---:|---|---|---|---|---|",
            ]
        )
        for row in item["variants"]:
            quality = row.get("capture_quality") or {}
            floor = row.get("semantic_floor") or {}
            if row["kind"] == "positive":
                threshold = f">= {row.get('min_score')}"
            elif row["kind"] == "negative":
                threshold = f"<= {row.get('max_score')} 或重采/语义失败"
            else:
                threshold = "diagnostic"
            ratio = row.get("rate_ratio")
            ratio_text = f"rate={_fmt(ratio, 2)}" if ratio is not None else f"len_ratio={_fmt(row.get('length_ratio'), 2)}"
            lines.append(
                f"| {row['variant']} | {row['kind']} | {'PASS' if row['passed'] else 'FAIL'} | "
                f"{_fmt(row['score'])} | {threshold} | {row.get('query_length')} / {ratio_text} | "
                f"{quality.get('status') or '-'}:{quality.get('reason') or '-'} | "
                f"{floor.get('source') or '-'}:{floor.get('reason') or '-'} | "
                f"{row['rationale']} |"
            )
        lines.append("")
    lines.extend(
        [
            "## 结论",
            "",
            "- 单调局部速度变化和整体快慢变化用于验证网页摄像头帧率/用户动作速度差异不会直接打崩正常动作。",
            "- 内部核心语义被采样跳过是重采或语义失败边界，不能用速率鲁棒性把缺核心动作样本抬成正常高分。",
            "- 该门仍是合成压力测试，不能替代正式 marker 后真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def _default_output_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return DEFAULT_OUTPUT_BASE / f"flower_jump_temporal_rate_robustness_gate_{stamp}"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run flower/jump temporal-rate robustness gate.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--backend-timeout-sec", type=float, default=5.0)
    parser.add_argument("--feature-mode", choices=["auto", "landmark", "bbox"], default="auto")
    parser.add_argument("--min-score", type=float, default=70.0)
    parser.add_argument("--words", nargs="+", default=DEFAULT_WORDS)
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir) if args.output_dir else _default_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    template_root = Path(args.template_root)
    semantic_profile_json = Path(args.semantic_profile_json)
    results = [
        _run_word(word, template_root, semantic_profile_json, args.feature_mode, args.min_score)
        for word in args.words
    ]
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "claim_policy": "synthetic temporal-rate robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": _load_backend_status(args.backend_url, args.backend_timeout_sec),
        "feature_mode": args.feature_mode,
        "min_score": args.min_score,
        "accepted_negative_quality": sorted(ACCEPTED_NEGATIVE_QUALITY),
        "results": results,
        "passed": all(bool(item.get("gate_pass")) for item in results),
    }
    json_path = output_dir / "flower_jump_temporal_rate_robustness_gate.json"
    md_path = output_dir / "flower_jump_temporal_rate_robustness_gate.md"
    csv_path = output_dir / "flower_jump_temporal_rate_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    _write_rows_csv(csv_path, results)
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    print(f"temporal rate gate: {'PASS' if payload['passed'] else 'FAIL'}")
    print(f"json: {json_path}")
    print(f"md: {md_path}")
    print(f"csv: {csv_path}")
    for item in results:
        print(
            f"- {item['word']}: gate={item['gate_pass']} "
            f"positive_min={_fmt(item['weakest_positive_score'])} "
            f"weakest={item['weakest_positive_variant']} "
            f"negative_max={_fmt(item['strongest_negative_score'])}"
        )
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

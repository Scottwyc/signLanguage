#!/usr/bin/env python3
"""Stress-test flower/jump scoring against motion-energy frame selection.

The browser captures high-frequency candidates, then uploads a smaller frame
set selected by motion-energy coverage. Frame-count gates test uniform/front-
back sampling and frame-weight gates test uploaded weights, but neither changes
the query frame set exactly like the frontend selector. This gate uses cached
skeleton sequences, selects frames by semantic motion energy, rebuilds derived
features, and verifies that complete energy-selected captures still score high.

It does not call /api/score, run Holistic, move the marker, or restart 5080.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

import numpy as np

from run_flower_jump_mirror_robustness_gate import _strip_to_base_groups
from run_flower_jump_temporal_rate_robustness_gate import (
    _fmt,
    _json_default,
    _load_backend_status,
    _rebuild_derived_groups,
    _template_json,
)
from score_holistic_sequence_mvp import (
    DEFAULT_SEMANTIC_PROFILE_JSON,
    SequenceData,
    _clone_sequence,
    _normalize_frame_weights,
    _profile_summary,
    compute_semantic_frame_weight_values,
    load_semantic_profile,
    load_sequence,
    run_pair,
)


REPO_ROOT = Path("/data/WYC/signLanguage")
DEFAULT_TEMPLATE_ROOT = REPO_ROOT / "work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results"
DEFAULT_OUTPUT_BASE = REPO_ROOT / "work/generated/scoring_mvp_run3"
DEFAULT_BACKEND_URL = "http://127.0.0.1:5080"
DEFAULT_WORDS = ["花", "跳"]
MIN_UPLOAD_FRAMES = {"花": 12, "跳": 6}

QueryFactory = Callable[[SequenceData, Any], SequenceData]


def _smooth(values: np.ndarray) -> np.ndarray:
    if values.size < 3:
        return values.astype(np.float32)
    out = values.astype(np.float32).copy()
    out[1:-1] = 0.25 * values[:-2] + 0.50 * values[1:-1] + 0.25 * values[2:]
    out[0] = 0.75 * values[0] + 0.25 * values[1]
    out[-1] = 0.75 * values[-1] + 0.25 * values[-2]
    return out.astype(np.float32)


def _semantic_energy(seq: SequenceData, profile: Any) -> np.ndarray:
    weights = compute_semantic_frame_weight_values(seq, profile=profile, combine_stored=False)
    return _smooth(np.asarray(weights, dtype=np.float32))


def _coverage_indices(count: int, coverage_count: int) -> List[int]:
    if count <= 0:
        return []
    if coverage_count <= 1:
        return [0]
    return [
        int(round((idx * (count - 1)) / max(coverage_count - 1, 1)))
        for idx in range(int(coverage_count))
    ]


def _frontend_coverage_ratio(target_frames: int) -> float:
    return max(0.45, min(1.0, 0.25 + float(target_frames) / 32.0))


def _energy_coverage_indices(
    energy: np.ndarray,
    target_frames: int,
    *,
    coverage_ratio: Optional[float] = None,
    force_endpoints: bool = True,
) -> List[int]:
    count = int(energy.size)
    if count <= 0:
        return []
    target = max(1, min(int(target_frames), count))
    if target >= count:
        return list(range(count))
    selected = set()
    ratio = _frontend_coverage_ratio(target) if coverage_ratio is None else float(coverage_ratio)
    coverage_count = max(2, min(target, int(np.ceil(target * ratio))))
    selected.update(_coverage_indices(count, coverage_count))
    if force_endpoints:
        selected.add(0)
        selected.add(count - 1)
    ranked = sorted(range(count), key=lambda idx: float(energy[idx]), reverse=True)
    for idx in ranked:
        if len(selected) >= target:
            break
        selected.add(int(idx))
    return sorted(selected)


def _top_energy_indices(energy: np.ndarray, target_frames: int, *, force_endpoints: bool) -> List[int]:
    count = int(energy.size)
    if count <= 0:
        return []
    target = max(1, min(int(target_frames), count))
    selected = set()
    if force_endpoints:
        selected.update([0, count - 1])
    for idx in sorted(range(count), key=lambda item: float(energy[item]), reverse=True):
        if len(selected) >= target:
            break
        selected.add(int(idx))
    return sorted(selected)


def _low_energy_indices(energy: np.ndarray, target_frames: int) -> List[int]:
    count = int(energy.size)
    if count <= 0:
        return []
    target = max(1, min(int(target_frames), count))
    selected = {0, count - 1}
    for idx in sorted(range(count), key=lambda item: float(energy[item])):
        if len(selected) >= target:
            break
        selected.add(int(idx))
    return sorted(selected)


def _query_from_indices(seq: SequenceData, profile: Any, name: str, indices: Sequence[int]) -> SequenceData:
    base = _strip_to_base_groups(seq)
    valid_indices = [int(idx) for idx in indices if 0 <= int(idx) < len(base.features)]
    selected = [base.features[idx] for idx in valid_indices]
    if not selected and base.features:
        selected = [base.features[0]]
        valid_indices = [0]
    sampled = _clone_sequence(base, name, selected)
    denom = max(len(base.features) - 1, 1)
    for item, source_idx in zip(sampled.features, valid_indices):
        item.semantic_phase = float(source_idx) / float(denom)
    return _rebuild_derived_groups(sampled, profile)


def _with_frontend_weights(query: SequenceData, standard_energy: np.ndarray, indices: Sequence[int]) -> SequenceData:
    if not query.features:
        return query
    selected_energy = np.asarray([standard_energy[int(idx)] for idx in indices], dtype=np.float32)
    weights = _normalize_frame_weights(selected_energy, low=0.45, high=2.75)
    features = []
    for idx, feature in enumerate(query.features):
        item = feature
        item.frame_weight = float(weights[idx]) if idx < weights.size else 1.0
        features.append(item)
    return _clone_sequence(query, f"{query.source}::frontend_weights", features)


def _select_query(
    seq: SequenceData,
    profile: Any,
    name: str,
    indices: Sequence[int],
    energy: np.ndarray,
    *,
    upload_weights: bool = False,
) -> SequenceData:
    query = _query_from_indices(seq, profile, name, indices)
    if upload_weights:
        return _with_frontend_weights(query, energy, indices)
    return query


def _spec(
    variant: str,
    kind: str,
    query: QueryFactory,
    rationale: str,
    *,
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
    min_frames = int(MIN_UPLOAD_FRAMES[word])
    plus_frames = min_frames + (4 if word == "花" else 2)
    rich_frames = min_frames + (8 if word == "花" else 4)

    def coverage(seq: SequenceData, profile: Any, target: int, name: str, ratio: Optional[float] = None) -> SequenceData:
        energy = _semantic_energy(seq, profile)
        indices = _energy_coverage_indices(energy, target, coverage_ratio=ratio, force_endpoints=True)
        return _select_query(seq, profile, name, indices, energy)

    def coverage_weighted(seq: SequenceData, profile: Any, target: int, name: str, ratio: Optional[float] = None) -> SequenceData:
        energy = _semantic_energy(seq, profile)
        indices = _energy_coverage_indices(energy, target, coverage_ratio=ratio, force_endpoints=True)
        return _select_query(seq, profile, name, indices, energy, upload_weights=True)

    def peaks(seq: SequenceData, profile: Any, target: int, name: str, endpoints: bool) -> SequenceData:
        energy = _semantic_energy(seq, profile)
        indices = _top_energy_indices(energy, target, force_endpoints=endpoints)
        return _select_query(seq, profile, name, indices, energy)

    def lows(seq: SequenceData, profile: Any, target: int, name: str) -> SequenceData:
        energy = _semantic_energy(seq, profile)
        indices = _low_energy_indices(energy, target)
        return _select_query(seq, profile, name, indices, energy)

    return [
        _spec(
            "self_rebuilt",
            "positive",
            lambda seq, profile: coverage(seq, profile, len(seq.features), "self_rebuilt", None),
            "剥离基础组后重建完整序列，应保持近满分。",
            min_score=95.0,
        ),
        _spec(
            f"frontend_energy_coverage_{min_frames}f",
            "positive",
            lambda seq, profile, min_frames=min_frames: coverage(
                seq,
                profile,
                min_frames,
                f"frontend_energy_coverage_{min_frames}f",
            ),
            "模拟前端推荐上传帧数：覆盖采样加高运动帧补齐。",
            min_score=min_score,
        ),
        _spec(
            f"frontend_energy_coverage_{plus_frames}f",
            "positive",
            lambda seq, profile, plus_frames=plus_frames: coverage(
                seq,
                profile,
                plus_frames,
                f"frontend_energy_coverage_{plus_frames}f",
            ),
            "比最低推荐多少量帧的前端能量覆盖选择。",
            min_score=min_score,
        ),
        _spec(
            f"frontend_energy_coverage_{rich_frames}f",
            "positive",
            lambda seq, profile, rich_frames=rich_frames: coverage(
                seq,
                profile,
                rich_frames,
                f"frontend_energy_coverage_{rich_frames}f",
            ),
            "帧数更充足时的前端能量覆盖选择。",
            min_score=min_score,
        ),
        _spec(
            f"frontend_energy_weighted_{plus_frames}f",
            "positive",
            lambda seq, profile, plus_frames=plus_frames: coverage_weighted(
                seq,
                profile,
                plus_frames,
                f"frontend_energy_weighted_{plus_frames}f",
            ),
            "同时模拟前端选帧和对应 upload frame_weights。",
            min_score=min_score,
        ),
        _spec(
            f"top_energy_with_endpoints_{plus_frames}f",
            "diagnostic",
            lambda seq, profile, plus_frames=plus_frames: peaks(
                seq,
                profile,
                plus_frames,
                f"top_energy_with_endpoints_{plus_frames}f",
                True,
            ),
            "只保留端点再偏向高运动峰值，记录缺相位覆盖的坏选帧边界。",
        ),
        _spec(
            f"top_energy_no_endpoints_{min_frames}f_diagnostic",
            "diagnostic",
            lambda seq, profile, min_frames=min_frames: peaks(
                seq,
                profile,
                min_frames,
                f"top_energy_no_endpoints_{min_frames}f_diagnostic",
                False,
            ),
            "只取高运动峰值而不保证起止覆盖，记录前端选择失误边界。",
        ),
        _spec(
            f"low_energy_with_endpoints_{min_frames}f_diagnostic",
            "diagnostic",
            lambda seq, profile, min_frames=min_frames: lows(
                seq,
                profile,
                min_frames,
                f"low_energy_with_endpoints_{min_frames}f_diagnostic",
            ),
            "只取低运动帧会丢失核心动态，作为坏选帧诊断边界。",
        ),
    ]


def _selection_summary(seq: SequenceData, profile: Any, query: SequenceData) -> Dict[str, Any]:
    # Query frame_idx is renumbered after cloning, so recover selected source
    # positions from the source suffix when possible is brittle. Instead report
    # score-facing length and selected semantic-phase coverage.
    phases = [float(item.semantic_phase) for item in query.features]
    return {
        "query_length": int(len(query.features)),
        "phase_min": min(phases) if phases else None,
        "phase_max": max(phases) if phases else None,
        "phase_span": (max(phases) - min(phases)) if phases else None,
        "energy_min": float(_semantic_energy(seq, profile).min()) if seq.features else None,
        "energy_max": float(_semantic_energy(seq, profile).max()) if seq.features else None,
    }


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
            "standard_length": len(standard.features),
            **_selection_summary(standard, profile, query),
            "alignment_policy": result.get("alignment_policy"),
            "capture_quality": score_scale.get("capture_quality"),
            "semantic_floor": score_scale.get("semantic_floor"),
            "semantic_phase_order_guard": score_scale.get("semantic_phase_order_guard"),
            "action_window": result.get("action_window"),
            "frame_weight_summary": result.get("frame_weight_summary"),
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
        "min_upload_frames": MIN_UPLOAD_FRAMES[word],
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
        "phase_min",
        "phase_max",
        "phase_span",
        "energy_min",
        "energy_max",
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
                        "standard_length": row.get("standard_length"),
                        "phase_min": row.get("phase_min"),
                        "phase_max": row.get("phase_max"),
                        "phase_span": row.get("phase_span"),
                        "energy_min": row.get("energy_min"),
                        "energy_max": row.get("energy_max"),
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
        "# 花/跳运动能量选帧鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，按语义运动能量选择实际 query 帧集合并重建 motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：模拟前端高频候选帧经过 `selectEnergyCoverageFrames` 上传后的骨架帧集合，而不只是修改 frame_weights。",
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
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向选帧 | 诊断最低分 | 最弱诊断边界 | 门槛 |")
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
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | query 帧 | 相位覆盖 | alignment | capture_quality | reason | 说明 |")
        lines.append("|---|---|---|---:|---|---:|---:|---|---|---|---|")
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
                f"| {row['variant']} | {row['kind']} | {status} | {_fmt(row['score'])} | {threshold} | "
                f"{row.get('query_length')} | {_fmt(row.get('phase_span'))} | {policy.get('mode') or '-'} | "
                f"{quality.get('status') or '-'} | {reason} | {row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 该门补充 frame-count 和 frame_weights：它改变上传帧集合本身，再重新计算派生运动/关系特征。",
            "- 诊断变体覆盖只取高运动峰值或低运动帧的坏选帧边界，不作为正常网页采样口径。",
            "- 该门是合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run motion-energy frame-selection robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_energy_sampling_robustness_gate_current"))
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
        "claim_policy": "synthetic motion-energy frame-selection robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": backend_status,
        "passed": passed,
        "min_score": args.min_score,
        "min_upload_frames": MIN_UPLOAD_FRAMES,
        "results": results,
    }

    json_path = output_dir / "flower_jump_energy_sampling_robustness_gate.json"
    md_path = output_dir / "flower_jump_energy_sampling_robustness_gate.md"
    csv_path = output_dir / "flower_jump_energy_sampling_robustness_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳运动能量选帧鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳运动能量选帧鲁棒性报告：{md_path}")
    print(f"已生成花/跳运动能量选帧鲁棒性 CSV：{csv_path}")
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

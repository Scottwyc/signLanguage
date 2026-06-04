#!/usr/bin/env python3
"""Stress-test flower/jump scoring against small temporal order jitter.

Browser sampling and upload timing can occasionally produce a tiny local order
glitch: two adjacent skeleton frames arrive swapped, or a short local triplet is
slightly out of order. A robust semantic-DTW scorer should tolerate these small
jitters when the complete action is present. Strong block-level disorder is
reported as a diagnostic boundary here; phase-order robustness remains the hard
guard for reversed or scrambled actions.

This script edits cached skeleton sequences in memory only. It does not call
/api/score, run Holistic, move the web marker, or restart 5080.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from run_flower_jump_landmark_noise_robustness_gate import _fmt, _json_default, _load_backend_status
from run_flower_jump_mirror_robustness_gate import _strip_to_base_groups, _template_json
from score_holistic_sequence_mvp import (
    DEFAULT_SEMANTIC_PROFILE_JSON,
    FrameFeature,
    SequenceData,
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


def _swap_indices(length: int, pairs: Sequence[Tuple[int, int]]) -> List[int]:
    indices = list(range(length))
    for left, right in pairs:
        if 0 <= left < length and 0 <= right < length:
            indices[left], indices[right] = indices[right], indices[left]
    return indices


def _local_adjacent_swaps(length: int, every: int) -> List[int]:
    pairs: List[Tuple[int, int]] = []
    # Preserve the first/last two frames so action-boundary evidence is not
    # converted into an action-crop test.
    for idx in range(2, max(2, length - 2), max(1, int(every))):
        pairs.append((idx, min(idx + 1, length - 2)))
    return _swap_indices(length, pairs)


def _center_triplet(length: int, order: Sequence[int]) -> List[int]:
    indices = list(range(length))
    start = max(0, length // 2 - 1)
    values = indices[start : start + 3]
    if len(values) == 3 and len(order) == 3:
        indices[start : start + 3] = [values[int(pos)] for pos in order]
    return indices


def _block_reverse(length: int, start: int, block_len: int) -> List[int]:
    indices = list(range(length))
    stop = min(length, start + max(1, int(block_len)))
    indices[start:stop] = list(reversed(indices[start:stop]))
    return indices


def _center_start(length: int, block_len: int) -> int:
    return max(0, int(length // 2) - int(block_len // 2))


def _permutation_detail(indices: Sequence[int]) -> Dict[str, Any]:
    changed = sum(1 for pos, src in enumerate(indices) if int(src) != pos)
    max_displacement = max((abs(pos - int(src)) for pos, src in enumerate(indices)), default=0)
    inversions = 0
    for left in range(len(indices)):
        src_left = int(indices[left])
        for right in range(left + 1, len(indices)):
            if src_left > int(indices[right]):
                inversions += 1
    return {
        "changed_positions": changed,
        "max_source_displacement": max_displacement,
        "inversions": inversions,
        "total_frames": len(indices),
    }


def _reordered_sequence(
    seq: SequenceData,
    name: str,
    *,
    indices: Sequence[int],
    profile: Any,
) -> Tuple[SequenceData, Dict[str, Any]]:
    base = _strip_to_base_groups(seq)
    if len(indices) != len(base.features):
        raise ValueError(f"permutation length mismatch for {name}: {len(indices)} != {len(base.features)}")
    selected: List[FrameFeature] = [base.features[int(index)] for index in indices]
    reordered = _clone_sequence(base, name, selected)
    detail = _permutation_detail(indices)
    return _sequence_with_relative_motion_features(reordered, profile), detail


def _spec(
    variant: str,
    kind: str,
    *,
    indices: Sequence[int],
    rationale: str,
    min_score: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": kind,
        "indices": list(indices),
        "min_score": min_score,
        "gated": kind == "positive",
        "rationale": rationale,
    }


def _variant_specs(word: str, seq_len: int, min_score: float) -> List[Dict[str, Any]]:
    center = seq_len // 2
    center_pair = (center, min(center + 1, seq_len - 1))
    core_pairs = [
        (max(1, center - 2), max(1, center - 1)),
        (min(seq_len - 2, center + 1), min(seq_len - 1, center + 2)),
    ]
    block_15 = max(1, round(seq_len * 0.15))
    block_25 = max(1, round(seq_len * 0.25))
    word_note = "开花核心序列" if word == "花" else "弹跳核心序列"
    return [
        _spec(
            "self_recomputed",
            "positive",
            indices=list(range(seq_len)),
            min_score=95.0,
            rationale="标准序列剥离基础组后重建 motion/relation 特征，应保持近满分。",
        ),
        _spec(
            "single_center_adjacent_swap",
            "positive",
            indices=_swap_indices(seq_len, [center_pair]),
            min_score=min_score,
            rationale=f"{word_note}中间相邻两帧交换，模拟一次上传/时间戳抖动。",
        ),
        _spec(
            "adjacent_swap_every_8f",
            "positive",
            indices=_local_adjacent_swaps(seq_len, 8),
            min_score=min_score,
            rationale="每约 8 帧出现一次相邻帧交换，整体动作顺序仍基本保留。",
        ),
        _spec(
            "adjacent_swap_every_6f",
            "positive",
            indices=_local_adjacent_swaps(seq_len, 6),
            min_score=min_score,
            rationale="更密集的轻微相邻帧交换，覆盖短浏览器采集中的局部到达顺序抖动。",
        ),
        _spec(
            "core_two_adjacent_swaps",
            "positive",
            indices=_swap_indices(seq_len, core_pairs),
            min_score=min_score,
            rationale="核心动作附近两处相邻帧交换，仍应保留可评分的语义轨迹。",
        ),
        _spec(
            "center_triplet_102",
            "positive",
            indices=_center_triplet(seq_len, [1, 0, 2]),
            min_score=min_score,
            rationale="核心三帧中的前两帧局部错序，相当于单个 ±1 帧 jitter。",
        ),
        _spec(
            "center_triplet_120_diagnostic",
            "diagnostic",
            indices=_center_triplet(seq_len, [1, 2, 0]),
            rationale="核心三帧循环错序，作为比相邻交换更强的诊断边界。",
        ),
        _spec(
            "block_reverse_15pct_diagnostic",
            "diagnostic",
            indices=_block_reverse(seq_len, _center_start(seq_len, block_15), block_15),
            rationale="中段约 15% 块状倒序，不作为正常网页采集要求，仅记录边界。",
        ),
        _spec(
            "block_reverse_25pct_diagnostic",
            "diagnostic",
            indices=_block_reverse(seq_len, _center_start(seq_len, block_25), block_25),
            rationale="中段约 25% 块状倒序，phase-order 门负责硬拒绝；这里仅记录分数。",
        ),
    ]


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
    standard, standard_detail = _reordered_sequence(
        loaded_standard,
        "standard_base",
        indices=list(range(len(loaded_standard.features))),
        profile=profile,
    )
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(word, len(standard.features), min_score):
        query, detail = _reordered_sequence(
            loaded_standard,
            str(spec["variant"]),
            indices=spec["indices"],
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
        "standard_permutation_detail": standard_detail,
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
        "changed_positions",
        "max_source_displacement",
        "inversions",
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
                        "changed_positions": row.get("changed_positions"),
                        "max_source_displacement": row.get("max_source_displacement"),
                        "inversions": row.get("inversions"),
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
        "# 花/跳时序顺序抖动鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，重排基础骨架帧后重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：轻微相邻帧交换、小范围局部错序仍可评分；块状倒序只作为诊断边界，硬拒绝仍由 phase-order 门覆盖。",
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
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向抖动 | 诊断最低分 | 最弱诊断抖动 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for item in payload["results"]:
        lines.append(
            f"| {item['word']} | {'PASS' if item['gate_pass'] else 'FAIL'} | "
            f"{_fmt(item['weakest_positive_score'])} | {item['weakest_positive_variant']} | "
            f"{_fmt(item['weakest_diagnostic_score'])} | {item['weakest_diagnostic_variant']} | "
            f"{_fmt(item['min_required_score'])} |"
        )
    lines.append("")
    lines.append("## 分项明细")
    for item in payload["results"]:
        lines.extend(["", f"### {item['word']}", "", f"- 标准序列：`{item['standard_json']}`", ""])
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | 改动位置 | 最大位移 | 逆序数 | capture_quality | semantic_floor | 说明 |")
        lines.append("|---|---|---|---:|---|---:|---:|---:|---|---|---|")
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
                f"{threshold} | {row.get('changed_positions')} | {row.get('max_source_displacement')} | "
                f"{row.get('inversions')} | {quality.get('status') or '-'}:{quality.get('reason') or '-'} | "
                f"{floor.get('source') or '-'}:{floor.get('reason') or '-'} | {row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 该门补充的是帧到达顺序的局部抖动，不替代 temporal-stutter、temporal-rate、inter-hand desync 或 phase-order 门。",
            "- `跳` 的短序列对局部错序更敏感，因此正向阈值保留在工程 sanity gate 的 `70` 分。",
            "- 块状倒序不是正常网页采集要求；本门只记录其诊断分，真实硬拒绝仍看 phase-order/semantic-mismatch。",
            "- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run temporal order jitter robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_temporal_order_jitter_robustness_gate_current"))
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
        "claim_policy": "synthetic temporal-order-jitter robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": backend_status,
        "passed": passed,
        "min_score": args.min_score,
        "results": results,
    }

    json_path = output_dir / "flower_jump_temporal_order_jitter_robustness_gate.json"
    md_path = output_dir / "flower_jump_temporal_order_jitter_robustness_gate.md"
    csv_path = output_dir / "flower_jump_temporal_order_jitter_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳时序顺序抖动鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳时序顺序抖动鲁棒性报告：{md_path}")
    print(f"已生成花/跳时序顺序抖动鲁棒性 CSV：{csv_path}")
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

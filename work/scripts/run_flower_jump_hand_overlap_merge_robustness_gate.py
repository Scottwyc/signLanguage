#!/usr/bin/env python3
"""Stress-test flower/jump scoring against hand-overlap merge artifacts.

When two hands overlap or pass close to each other, browser/Holistic tracking
can partially pull one hand's landmarks toward the other hand. This differs
from ghost-hand duplication: both hands remain present, but one hand is blended
toward the other for a few frames. Short and sparse merge artifacts should not
break an otherwise correct sequence, while sustained core-hand merge is kept as
a diagnostic boundary.

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


def _active_indices(pattern: str, length: int) -> List[int]:
    if pattern == "none":
        return []
    if pattern == "single_mid":
        return [length // 2] if length > 0 else []
    if pattern == "sparse_every_6f":
        return [idx for idx in range(length) if idx % 6 == 3]
    if pattern == "middle_20pct":
        start = int(round(length * 0.40))
        end = max(start + 1, int(round(length * 0.60)))
        return list(range(max(0, start), min(length, end)))
    if pattern == "middle_35pct":
        start = int(round(length * 0.325))
        end = max(start + 1, int(round(length * 0.675)))
        return list(range(max(0, start), min(length, end)))
    if pattern == "full":
        return list(range(length))
    raise ValueError(f"unknown hand-overlap merge pattern: {pattern}")


def _merge_hand_sequence(
    seq: SequenceData,
    name: str,
    *,
    source_group: str,
    target_group: str,
    pattern: str,
    alpha: float,
    profile: Any,
) -> Tuple[SequenceData, Dict[str, Any]]:
    base = _strip_to_base_groups(seq)
    active = set(_active_indices(pattern, len(base.features)))
    features: List[FrameFeature] = []
    changed_frames = 0
    changed_points = 0
    skipped_points = 0

    for idx, frame in enumerate(base.features):
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        presence = dict(frame.presence)
        if idx in active:
            target_coords, target_valid = _hand_array(frame, target_group)
            if target_coords is not None and target_valid is not None:
                coords = target_coords.copy()
                valid = target_valid.copy()
                if source_group == "self_center":
                    palm_indices = [idx for idx in [0, 1, 5, 9, 13, 17] if idx < len(valid) and bool(valid[idx])]
                    if palm_indices:
                        center = coords[palm_indices].mean(axis=0)
                        source_coords = np.repeat(center.reshape(1, 3), coords.shape[0], axis=0)
                        source_valid = valid.copy()
                    else:
                        source_coords = np.zeros_like(coords)
                        source_valid = np.zeros_like(valid, dtype=bool)
                else:
                    source_coords, source_valid = _hand_array(frame, source_group)
                    if source_coords is None or source_valid is None:
                        source_coords = np.zeros_like(coords)
                        source_valid = np.zeros_like(valid, dtype=bool)
                blend_valid = source_valid & target_valid
                if blend_valid.any():
                    coords[blend_valid] = (
                        (1.0 - float(alpha)) * coords[blend_valid]
                        + float(alpha) * source_coords[blend_valid]
                    )
                    changed_points += int(blend_valid.sum())
                    changed_frames += 1
                skipped_points += int((target_valid & ~source_valid).sum())
                _set_hand_group(frame, vector, mask, target_group, coords, valid)
                presence[target_group] = bool(valid.any())
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
        "operation": "hand_overlap_merge",
        "source_group": source_group,
        "target_group": target_group,
        "pattern": pattern,
        "alpha": float(alpha),
        "active_frame_count": len(active),
        "changed_frames": changed_frames,
        "changed_points": changed_points,
        "skipped_points": skipped_points,
        "total_frames": len(base.features),
    }
    return _sequence_with_relative_motion_features(transformed, profile), detail


def _spec(
    variant: str,
    kind: str,
    *,
    source_group: str,
    target_group: str,
    pattern: str,
    alpha: float,
    rationale: str,
    min_score: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": kind,
        "source_group": source_group,
        "target_group": target_group,
        "pattern": pattern,
        "alpha": float(alpha),
        "min_score": min_score,
        "gated": kind == "positive",
        "rationale": rationale,
    }


def _variant_specs(word: str, min_score: float) -> List[Dict[str, Any]]:
    specs = [
        _spec(
            "self_recomputed",
            "positive",
            source_group="left_hand",
            target_group="right_hand",
            pattern="none",
            alpha=0.0,
            min_score=95.0,
            rationale="标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。",
        ),
        _spec(
            "single_mid_left_blend_toward_right_0.45",
            "positive",
            source_group="right_hand",
            target_group="left_hand",
            pattern="single_mid",
            alpha=0.45,
            min_score=min_score,
            rationale="单帧左手 landmark 被右手局部吸引，模拟双手短暂重叠。",
        ),
        _spec(
            "single_mid_right_blend_toward_left_0.45",
            "positive",
            source_group="left_hand",
            target_group="right_hand",
            pattern="single_mid",
            alpha=0.45,
            min_score=min_score,
            rationale="单帧右手 landmark 被左手局部吸引，模拟双手短暂重叠。",
        ),
        _spec(
            "sparse_left_blend_toward_right_0.35_every_6f",
            "positive",
            source_group="right_hand",
            target_group="left_hand",
            pattern="sparse_every_6f",
            alpha=0.35,
            min_score=min_score,
            rationale="稀疏帧左手向右手融合，完整动作证据仍应可评分。",
        ),
        _spec(
            "sparse_right_blend_toward_left_0.35_every_6f",
            "positive",
            source_group="left_hand",
            target_group="right_hand",
            pattern="sparse_every_6f",
            alpha=0.35,
            min_score=min_score,
            rationale="稀疏帧右手向左手融合，完整动作证据仍应可评分。",
        ),
    ]
    if word == "花":
        specs.extend(
            [
                _spec(
                    "flower_middle20_left_noncore_blend_right_0.55",
                    "positive",
                    source_group="right_hand",
                    target_group="left_hand",
                    pattern="middle_20pct",
                    alpha=0.55,
                    min_score=min_score,
                    rationale="花的非核心左手中段向开花手融合，不应拖低右手核心开花语义。",
                ),
                _spec(
                    "flower_full_left_noncore_blend_right_0.45",
                    "positive",
                    source_group="right_hand",
                    target_group="left_hand",
                    pattern="full",
                    alpha=0.45,
                    min_score=65.0,
                    rationale="花的非核心左手全程轻度向开花手融合，按非核心手干扰局部门槛处理。",
                ),
                _spec(
                    "flower_right_hand_self_overlap_0.12",
                    "positive",
                    source_group="self_center",
                    target_group="right_hand",
                    pattern="full",
                    alpha=0.12,
                    min_score=min_score,
                    rationale="花的开花手 landmarks 轻微向掌心融合，模拟单手自遮挡/手指重叠但开花语义仍清晰。",
                ),
                _spec(
                    "flower_middle20_right_self_overlap_0.20",
                    "positive",
                    source_group="self_center",
                    target_group="right_hand",
                    pattern="middle_20pct",
                    alpha=0.20,
                    min_score=min_score,
                    rationale="花的开花手中段轻度向掌心融合，验证核心片段轻微自遮挡仍可评分。",
                ),
                _spec(
                    "flower_middle35_right_core_blend_left_0.60_diagnostic",
                    "diagnostic",
                    source_group="left_hand",
                    target_group="right_hand",
                    pattern="middle_35pct",
                    alpha=0.60,
                    rationale="诊断记录：开花核心手中段向非核心手融合时的边界分。",
                ),
                _spec(
                    "flower_middle35_right_self_overlap_0.45_diagnostic",
                    "diagnostic",
                    source_group="self_center",
                    target_group="right_hand",
                    pattern="middle_35pct",
                    alpha=0.45,
                    rationale="诊断记录：开花核心手较强自遮挡融合时的边界分。",
                ),
            ]
        )
    elif word == "跳":
        specs.extend(
            [
                _spec(
                    "jump_middle20_left_ground_blend_right_0.25",
                    "positive",
                    source_group="right_hand",
                    target_group="left_hand",
                    pattern="middle_20pct",
                    alpha=0.25,
                    min_score=min_score,
                    rationale="跳的左手地面在短核心窗口内轻微向右手融合，双手关系仍应保留。",
                ),
                _spec(
                    "jump_middle20_right_person_blend_left_0.25",
                    "positive",
                    source_group="left_hand",
                    target_group="right_hand",
                    pattern="middle_20pct",
                    alpha=0.25,
                    min_score=min_score,
                    rationale="跳的右手小人在短核心窗口内轻微向左手融合，双手关系仍应保留。",
                ),
                _spec(
                    "jump_right_person_self_overlap_0.08",
                    "positive",
                    source_group="self_center",
                    target_group="right_hand",
                    pattern="full",
                    alpha=0.08,
                    min_score=min_score,
                    rationale="跳的右手两指小人轻微自遮挡融合，手形仍应保持可识别。",
                ),
                _spec(
                    "jump_middle35_left_ground_blend_right_0.55_diagnostic",
                    "diagnostic",
                    source_group="right_hand",
                    target_group="left_hand",
                    pattern="middle_35pct",
                    alpha=0.55,
                    rationale="诊断记录：左手地面较长核心段向右手融合时的边界分。",
                ),
                _spec(
                    "jump_middle35_right_person_blend_left_0.55_diagnostic",
                    "diagnostic",
                    source_group="left_hand",
                    target_group="right_hand",
                    pattern="middle_35pct",
                    alpha=0.55,
                    rationale="诊断记录：右手小人较长核心段向左手融合时的边界分。",
                ),
                _spec(
                    "jump_right_person_self_overlap_0.30_diagnostic",
                    "diagnostic",
                    source_group="self_center",
                    target_group="right_hand",
                    pattern="middle_35pct",
                    alpha=0.30,
                    rationale="诊断记录：右手两指小人较强自遮挡融合时的边界分。",
                ),
            ]
        )
    return specs


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
    standard, standard_detail = _merge_hand_sequence(
        loaded_standard,
        "standard_base",
        source_group="left_hand",
        target_group="right_hand",
        pattern="none",
        alpha=0.0,
        profile=profile,
    )
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(word, min_score):
        query, detail = _merge_hand_sequence(
            loaded_standard,
            str(spec["variant"]),
            source_group=str(spec["source_group"]),
            target_group=str(spec["target_group"]),
            pattern=str(spec["pattern"]),
            alpha=float(spec["alpha"]),
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
        "standard_mutation_detail": standard_detail,
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
        "source_group",
        "target_group",
        "pattern",
        "alpha",
        "active_frame_count",
        "changed_frames",
        "changed_points",
        "skipped_points",
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
                        "source_group": row.get("source_group"),
                        "target_group": row.get("target_group"),
                        "pattern": row.get("pattern"),
                        "alpha": row.get("alpha"),
                        "active_frame_count": row.get("active_frame_count"),
                        "changed_frames": row.get("changed_frames"),
                        "changed_points": row.get("changed_points"),
                        "skipped_points": row.get("skipped_points"),
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
        "# 花/跳手部重叠融合鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，将一只手的 landmarks 按比例拉向另一只手，模拟双手重叠/遮挡时的局部 merge；随后重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：单帧、稀疏和轻度短窗口融合仍可正常评分；持续核心手融合只记录诊断边界。",
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
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向融合 | 诊断最低分 | 最弱诊断边界 | 门槛 |")
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
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | source->target | pattern | alpha | 改动帧 | 改动点 | capture_quality | semantic_floor | 说明 |")
        lines.append("|---|---|---|---:|---|---|---|---:|---:|---:|---|---|---|")
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
                f"{threshold} | {row.get('source_group')}->{row.get('target_group')} | "
                f"{row.get('pattern')} | {_fmt(row.get('alpha'))} | {row.get('changed_frames')} | "
                f"{row.get('changed_points')} | {quality.get('status') or '-'}:{quality.get('reason') or '-'} | "
                f"{floor.get('source') or '-'}:{floor.get('reason') or '-'} | {row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 该门补充的是双手接近/遮挡时的局部 landmark 融合，不替代 ghost-hand duplicate、hand-label-flicker、relation-geometry 或 inter-hand temporal desync 门。",
            "- 持续核心融合可能改变真实语义，本轮只作为诊断边界；是否升级硬负例需要真实网页样本或人工标签。",
            "- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run hand-overlap merge robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_hand_overlap_merge_robustness_gate_current"))
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
        "claim_policy": "synthetic hand-overlap merge robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": backend_status,
        "passed": passed,
        "min_score": args.min_score,
        "results": results,
    }

    json_path = output_dir / "flower_jump_hand_overlap_merge_robustness_gate.json"
    md_path = output_dir / "flower_jump_hand_overlap_merge_robustness_gate.md"
    csv_path = output_dir / "flower_jump_hand_overlap_merge_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳手部重叠融合鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳手部重叠融合鲁棒性报告：{md_path}")
    print(f"已生成花/跳手部重叠融合鲁棒性 CSV：{csv_path}")
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

#!/usr/bin/env python3
"""Stress-test flower/jump scoring against short hand-trajectory interpolation.

Some browser/Holistic pipelines can smooth over short hand tracking gaps by
interpolating landmark coordinates between surrounding frames. That is different
from frame freezing or hand dropout: masks remain present, but local hand motion
is partially linearized. Short interpolation spans should remain scoreable,
while stronger core spans are recorded as diagnostic boundaries.

This script edits cached skeleton sequences in memory only. It does not call
/api/score, run Holistic, move the web marker, or restart 5080.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

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
HAND_GROUPS = ["left_hand", "right_hand"]


def _indices_for_pattern(pattern: str, length: int) -> Set[int]:
    if length <= 0:
        return set()
    if pattern == "none":
        return set()
    if pattern == "single_mid":
        return {length // 2}
    if pattern == "sparse_every_6th":
        return {idx for idx in range(1, length - 1) if idx % 6 == 3}
    if pattern == "middle_12pct":
        start = int(round(length * 0.44))
        end = max(start + 1, int(round(length * 0.56)))
        return set(range(max(1, start), min(length - 1, end)))
    if pattern == "middle_18pct":
        start = int(round(length * 0.41))
        end = max(start + 1, int(round(length * 0.59)))
        return set(range(max(1, start), min(length - 1, end)))
    if pattern == "middle_25pct":
        start = int(round(length * 0.375))
        end = max(start + 1, int(round(length * 0.625)))
        return set(range(max(1, start), min(length - 1, end)))
    if pattern == "core_40pct":
        start = int(round(length * 0.30))
        end = max(start + 1, int(round(length * 0.70)))
        return set(range(max(1, start), min(length - 1, end)))
    raise ValueError(f"unknown interpolation pattern: {pattern}")


def _contiguous_ranges(indices: Set[int]) -> List[Tuple[int, int]]:
    if not indices:
        return []
    sorted_indices = sorted(indices)
    ranges: List[Tuple[int, int]] = []
    start = sorted_indices[0]
    prev = start
    for idx in sorted_indices[1:]:
        if idx == prev + 1:
            prev = idx
            continue
        ranges.append((start, prev + 1))
        start = idx
        prev = idx
    ranges.append((start, prev + 1))
    return ranges


def _interpolated_sequence(
    seq: SequenceData,
    name: str,
    *,
    groups: Sequence[str],
    pattern: str,
    profile: Any,
) -> Tuple[SequenceData, Dict[str, Any]]:
    base = _strip_to_base_groups(seq)
    selected = _indices_for_pattern(pattern, len(base.features))
    ranges = _contiguous_ranges(selected)
    items: List[FrameFeature] = []
    changed_visible_points = 0
    changed_frames: Set[int] = set()
    n = len(base.features)

    for idx, frame in enumerate(base.features):
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        presence = dict(frame.presence)
        active_range = next((item for item in ranges if item[0] <= idx < item[1]), None)
        if active_range is not None:
            start, stop = active_range
            left_idx = max(0, start - 1)
            right_idx = min(n - 1, stop)
            denom = max(1, right_idx - left_idx)
            frac = (idx - left_idx) / float(denom)
            for group in groups:
                coords, valid = _hand_array(frame, group)
                left_coords, left_valid = _hand_array(base.features[left_idx], group)
                right_coords, right_valid = _hand_array(base.features[right_idx], group)
                if (
                    coords is None
                    or valid is None
                    or left_coords is None
                    or left_valid is None
                    or right_coords is None
                    or right_valid is None
                ):
                    continue
                coords = coords.copy()
                valid = valid.copy()
                use = valid & left_valid & right_valid
                if use.any():
                    interpolated = left_coords[use] * (1.0 - frac) + right_coords[use] * frac
                    coords[use] = interpolated
                    changed_visible_points += int(use.sum())
                    changed_frames.add(idx)
                _set_hand_group(frame, vector, mask, group, coords, valid)
                presence[group] = bool(valid.any())
        item = _clone_frame(frame, vector=vector, mask=mask)
        item.presence = presence
        items.append(item)

    transformed = SequenceData(
        source=f"{base.source}::{name}",
        mode=base.mode,
        fps=base.fps,
        total_frames=base.total_frames,
        features=items,
    )
    detail = {
        "operation": "hand_trajectory_interpolation",
        "groups": list(groups),
        "pattern": pattern,
        "interpolated_frame_count": len(selected),
        "changed_frame_count": len(changed_frames),
        "changed_visible_points": changed_visible_points,
        "total_frames": n,
        "interpolated_indices": sorted(selected),
        "interpolated_ranges": [[start, stop] for start, stop in ranges],
    }
    return _sequence_with_relative_motion_features(transformed, profile), detail


def _spec(
    variant: str,
    kind: str,
    *,
    groups: Sequence[str],
    pattern: str,
    rationale: str,
    min_score: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": kind,
        "groups": list(groups),
        "pattern": pattern,
        "min_score": min_score,
        "gated": kind == "positive",
        "rationale": rationale,
    }


def _variant_specs(word: str, min_score: float) -> List[Dict[str, Any]]:
    specs = [
        _spec(
            "self_recomputed",
            "positive",
            groups=HAND_GROUPS,
            pattern="none",
            min_score=95.0,
            rationale="标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。",
        )
    ]
    if word == "花":
        return specs + [
            _spec(
                "right_hand_single_mid_interp",
                "positive",
                groups=["right_hand"],
                pattern="single_mid",
                min_score=min_score,
                rationale="开花核心手单帧轨迹被前后帧线性插值，模拟 tracker 短补洞。",
            ),
            _spec(
                "right_hand_sparse_interp_every_6th",
                "positive",
                groups=["right_hand"],
                pattern="sparse_every_6th",
                min_score=min_score,
                rationale="开花核心手稀疏帧被线性插值，短时开合证据仍应保留。",
            ),
            _spec(
                "right_hand_middle12_interp",
                "positive",
                groups=["right_hand"],
                pattern="middle_12pct",
                min_score=min_score,
                rationale="开花核心段约 12% 手部轨迹线性化，作为正常短补洞正向门。",
            ),
            _spec(
                "both_hands_middle12_interp",
                "positive",
                groups=HAND_GROUPS,
                pattern="middle_12pct",
                min_score=min_score,
                rationale="双手约 12% 轨迹线性化，验证非核心手同时受平滑影响仍可评分。",
            ),
            _spec(
                "right_hand_middle18_interp_diagnostic",
                "diagnostic",
                groups=["right_hand"],
                pattern="middle_18pct",
                rationale="开花核心段约 18% 轨迹线性化偏强，只记录诊断边界。",
            ),
            _spec(
                "right_hand_middle25_interp_diagnostic",
                "diagnostic",
                groups=["right_hand"],
                pattern="middle_25pct",
                rationale="开花核心段约 25% 轨迹线性化属于强边界，只作诊断。",
            ),
        ]
    if word == "跳":
        return specs + [
            _spec(
                "right_hand_single_mid_interp",
                "positive",
                groups=["right_hand"],
                pattern="single_mid",
                min_score=min_score,
                rationale="右手两指小人单帧轨迹补洞，双手关系仍应可评分。",
            ),
            _spec(
                "left_hand_single_mid_interp",
                "positive",
                groups=["left_hand"],
                pattern="single_mid",
                min_score=min_score,
                rationale="左手地面单帧轨迹补洞，不应导致跳跃关系失败。",
            ),
            _spec(
                "right_hand_sparse_interp_every_6th",
                "positive",
                groups=["right_hand"],
                pattern="sparse_every_6th",
                min_score=min_score,
                rationale="右手稀疏帧线性补洞，弹跳主方向仍应保留。",
            ),
            _spec(
                "left_hand_sparse_interp_every_6th",
                "positive",
                groups=["left_hand"],
                pattern="sparse_every_6th",
                min_score=min_score,
                rationale="左手地面稀疏帧线性补洞，右手弹跳关系仍应稳定。",
            ),
            _spec(
                "right_hand_middle12_interp",
                "positive",
                groups=["right_hand"],
                pattern="middle_12pct",
                min_score=min_score,
                rationale="右手约 12% 弹跳轨迹线性化，作为短补洞正向门。",
            ),
            _spec(
                "left_hand_middle12_interp",
                "positive",
                groups=["left_hand"],
                pattern="middle_12pct",
                min_score=min_score,
                rationale="左手地面约 12% 轨迹线性化，双手关系仍应可恢复。",
            ),
            _spec(
                "both_hands_middle12_interp_diagnostic",
                "diagnostic",
                groups=HAND_GROUPS,
                pattern="middle_12pct",
                rationale="短动作双手同时线性化约 12% 偏强，只记录诊断边界。",
            ),
            _spec(
                "right_hand_middle18_interp_diagnostic",
                "diagnostic",
                groups=["right_hand"],
                pattern="middle_18pct",
                rationale="右手弹跳核心约 18% 线性化偏强，只记录诊断边界。",
            ),
            _spec(
                "both_hands_middle25_interp_diagnostic",
                "diagnostic",
                groups=HAND_GROUPS,
                pattern="middle_25pct",
                rationale="双手核心约 25% 轨迹线性化属于强边界，只作诊断。",
            ),
        ]
    return specs


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
    standard, standard_detail = _interpolated_sequence(
        loaded_standard,
        "standard_base",
        groups=HAND_GROUPS,
        pattern="none",
        profile=profile,
    )
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(word, min_score):
        query, detail = _interpolated_sequence(
            loaded_standard,
            str(spec["variant"]),
            groups=spec["groups"],
            pattern=str(spec["pattern"]),
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
        row["passed"] = float(row["score"]) >= float(row["min_score"]) if row["kind"] == "positive" else True
        rows.append(row)
    positive_rows = [row for row in rows if row["kind"] == "positive"]
    diagnostic_rows = [row for row in rows if row["kind"] == "diagnostic"]
    weakest_positive = min(positive_rows, key=lambda row: float(row["score"])) if positive_rows else None
    weakest_diagnostic = min(diagnostic_rows, key=lambda row: float(row["score"])) if diagnostic_rows else None
    return {
        "word": word,
        "standard_json": str(standard_json),
        "standard_length": len(standard.features),
        "standard_interpolation_detail": standard_detail,
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
        "groups",
        "pattern",
        "interpolated_frame_count",
        "changed_frame_count",
        "changed_visible_points",
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
                        "groups": ",".join(row.get("groups") or []),
                        "pattern": row.get("pattern"),
                        "interpolated_frame_count": row.get("interpolated_frame_count"),
                        "changed_frame_count": row.get("changed_frame_count"),
                        "changed_visible_points": row.get("changed_visible_points"),
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
        "# 花/跳手部轨迹插值补洞鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，把短片段手部 landmark 线性插值到前后帧之间，并重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：短时 tracker 补洞或平滑线性化不应压低 `花/跳` 网页评分；较长核心段线性化只作诊断边界。",
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
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向插值 | 诊断最低分 | 最弱诊断插值 | 门槛 |")
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
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | 组 | 插值帧 | capture_quality | 说明 |")
        lines.append("|---|---|---|---:|---|---|---:|---|---|")
        for row in sorted(item["variants"], key=lambda value: (value["kind"], float(value["score"]))):
            quality = row.get("capture_quality") or {}
            if row["kind"] == "positive":
                threshold = f">= {row.get('min_score')}"
                status = "PASS" if row["passed"] else "FAIL"
            else:
                threshold = "diagnostic"
                status = "DIAG"
            lines.append(
                f"| {row['variant']} | {row['kind']} | {status} | {_fmt(row['score'])} | "
                f"{threshold} | {','.join(row.get('groups') or [])} | "
                f"{row.get('interpolated_frame_count')}/{row.get('total_frames')} | "
                f"{quality.get('status') or '-'}:{quality.get('reason') or '-'} | "
                f"{row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 正向门只覆盖单帧、稀疏或约 12% 的短片段手部轨迹插值补洞。",
            "- 较长核心段插值会线性化关键动作轨迹，只作为诊断边界，不提升为正常网页采集要求。",
            "- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run hand-trajectory interpolation robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_hand_trajectory_interpolation_robustness_gate_current"))
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
        "claim_policy": "synthetic hand-trajectory-interpolation robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": backend_status,
        "passed": passed,
        "min_score": args.min_score,
        "results": results,
    }

    json_path = output_dir / "flower_jump_hand_trajectory_interpolation_robustness_gate.json"
    md_path = output_dir / "flower_jump_hand_trajectory_interpolation_robustness_gate.md"
    csv_path = output_dir / "flower_jump_hand_trajectory_interpolation_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳手部轨迹插值补洞鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳手部轨迹插值补洞鲁棒性报告：{md_path}")
    print(f"已生成花/跳手部轨迹插值补洞鲁棒性 CSV：{csv_path}")
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

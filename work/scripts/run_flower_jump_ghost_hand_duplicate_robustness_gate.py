#!/usr/bin/env python3
"""Stress-test flower/jump scoring against ghost hand duplication.

Browser/Holistic hand tracking can occasionally duplicate one physical hand as
both left and right hands. This is distinct from a left/right label swap: the
missing hand is replaced by a copy of the visible hand. Short or sparse ghost
duplicates should not break an otherwise correct sequence, while sustained core
duplication is kept as a diagnostic boundary.

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
    if pattern == "full":
        return list(range(length))
    if pattern == "single_mid":
        return [length // 2] if length > 0 else []
    if pattern == "sparse_every_6f":
        return [idx for idx in range(length) if idx % 6 == 3]
    if pattern == "middle_30pct":
        start = int(round(length * 0.35))
        end = max(start + 1, int(round(length * 0.65)))
        return list(range(max(0, start), min(length, end)))
    if pattern == "middle_45pct":
        start = int(round(length * 0.275))
        end = max(start + 1, int(round(length * 0.725)))
        return list(range(max(0, start), min(length, end)))
    raise ValueError(f"unknown ghost duplicate pattern: {pattern}")


def _duplicate_hand_sequence(
    seq: SequenceData,
    name: str,
    *,
    source_group: str,
    target_group: str,
    pattern: str,
    offset: Sequence[float],
    profile: Any,
) -> Tuple[SequenceData, Dict[str, Any]]:
    base = _strip_to_base_groups(seq)
    active = set(_active_indices(pattern, len(base.features)))
    delta = np.asarray(offset, dtype=np.float32)
    features: List[FrameFeature] = []
    changed_frames = 0
    changed_points = 0
    visible_source_frames = 0

    for idx, frame in enumerate(base.features):
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        presence = dict(frame.presence)
        if idx in active:
            coords, valid = _hand_array(frame, source_group)
            if coords is not None and valid is not None:
                coords = coords.copy()
                valid = valid.copy()
                if valid.any():
                    visible_source_frames += 1
                    coords[valid] += delta
                    changed_points += int(valid.sum())
                _set_hand_group(frame, vector, mask, target_group, coords, valid)
                presence[target_group] = bool(valid.any())
                changed_frames += 1
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
        "operation": "ghost_hand_duplicate",
        "source_group": source_group,
        "target_group": target_group,
        "pattern": pattern,
        "offset": [float(value) for value in delta.tolist()],
        "active_frame_count": len(active),
        "changed_frames": changed_frames,
        "changed_points": changed_points,
        "visible_source_frames": visible_source_frames,
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
    rationale: str,
    min_score: Optional[float] = None,
    offset: Sequence[float] = (0.0, 0.0, 0.0),
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": kind,
        "source_group": source_group,
        "target_group": target_group,
        "pattern": pattern,
        "offset": [float(value) for value in offset],
        "min_score": min_score,
        "gated": kind == "positive",
        "rationale": rationale,
    }


def _variant_specs(word: str, min_score: float) -> List[Dict[str, Any]]:
    common = [
        _spec(
            "self_recomputed",
            "positive",
            source_group="left_hand",
            target_group="right_hand",
            pattern="none",
            min_score=95.0,
            rationale="标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。",
        ),
        _spec(
            "single_mid_left_duplicates_right",
            "positive",
            source_group="right_hand",
            target_group="left_hand",
            pattern="single_mid",
            min_score=min_score,
            rationale="单帧左手被右手幽灵副本替代，模拟偶发双手检测误报。",
        ),
        _spec(
            "single_mid_right_duplicates_left",
            "positive",
            source_group="left_hand",
            target_group="right_hand",
            pattern="single_mid",
            min_score=min_score,
            rationale="单帧右手被左手幽灵副本替代，模拟偶发双手检测误报。",
        ),
        _spec(
            "sparse_left_duplicates_right_every_6f",
            "positive",
            source_group="right_hand",
            target_group="left_hand",
            pattern="sparse_every_6f",
            min_score=min_score,
            rationale="稀疏帧左手变成右手幽灵副本，完整动作证据仍应可评分。",
        ),
        _spec(
            "sparse_right_duplicates_left_every_6f",
            "positive",
            source_group="left_hand",
            target_group="right_hand",
            pattern="sparse_every_6f",
            min_score=min_score,
            rationale="稀疏帧右手变成左手幽灵副本，完整动作证据仍应可评分。",
        ),
    ]
    if word == "花":
        common.extend(
            [
                _spec(
                    "flower_full_left_ghost_from_right_offset",
                    "positive",
                    source_group="right_hand",
                    target_group="left_hand",
                    pattern="full",
                    offset=(-0.18, 0.04, 0.0),
                    min_score=min(65.0, min_score),
                    rationale="花的非核心左手全程成为右手开花手的幽灵副本，不应拖低清晰开花语义。",
                ),
                _spec(
                    "flower_middle30_left_ghost_from_right",
                    "positive",
                    source_group="right_hand",
                    target_group="left_hand",
                    pattern="middle_30pct",
                    min_score=min_score,
                    rationale="花的非核心左手核心中段被右手副本替代，应仍由开花手主语义评分。",
                ),
                _spec(
                    "flower_middle45_right_core_ghost_from_left_diagnostic",
                    "diagnostic",
                    source_group="left_hand",
                    target_group="right_hand",
                    pattern="middle_45pct",
                    rationale="诊断记录：开花核心手被非核心手副本替代时的边界分。",
                ),
            ]
        )
    elif word == "跳":
        common.extend(
            [
                _spec(
                    "jump_middle30_left_ghost_from_right_diagnostic",
                    "diagnostic",
                    source_group="right_hand",
                    target_group="left_hand",
                    pattern="middle_30pct",
                    rationale="诊断记录：左手地面核心段被右手小人副本替代时的边界分。",
                ),
                _spec(
                    "jump_middle30_right_ghost_from_left_diagnostic",
                    "diagnostic",
                    source_group="left_hand",
                    target_group="right_hand",
                    pattern="middle_30pct",
                    rationale="诊断记录：右手小人核心段被左手地面副本替代时的边界分。",
                ),
                _spec(
                    "jump_full_left_ghost_from_right_diagnostic",
                    "diagnostic",
                    source_group="right_hand",
                    target_group="left_hand",
                    pattern="full",
                    offset=(-0.12, 0.02, 0.0),
                    rationale="全程左手是右手幽灵副本，属于明显双手关系失真，只记录诊断边界。",
                ),
                _spec(
                    "jump_full_right_ghost_from_left_diagnostic",
                    "diagnostic",
                    source_group="left_hand",
                    target_group="right_hand",
                    pattern="full",
                    offset=(0.12, -0.02, 0.0),
                    rationale="全程右手是左手幽灵副本，属于明显双手关系失真，只记录诊断边界。",
                ),
            ]
        )
    return common


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
    standard, standard_detail = _duplicate_hand_sequence(
        loaded_standard,
        "standard_base",
        source_group="left_hand",
        target_group="right_hand",
        pattern="none",
        offset=(0.0, 0.0, 0.0),
        profile=profile,
    )
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(word, min_score):
        query, detail = _duplicate_hand_sequence(
            loaded_standard,
            str(spec["variant"]),
            source_group=str(spec["source_group"]),
            target_group=str(spec["target_group"]),
            pattern=str(spec["pattern"]),
            offset=spec["offset"],
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
        "active_frame_count",
        "changed_frames",
        "changed_points",
        "visible_source_frames",
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
                        "active_frame_count": row.get("active_frame_count"),
                        "changed_frames": row.get("changed_frames"),
                        "changed_points": row.get("changed_points"),
                        "visible_source_frames": row.get("visible_source_frames"),
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
        "# 花/跳幽灵手重复鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，将一只手的 21 点复制到另一只手，模拟单手被检测成双手的幽灵手；随后重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：短暂或稀疏幽灵手不应破坏正常分数；`花` 的非核心左手幽灵副本不应拖低开花手核心语义；持续核心重复只记录诊断边界。",
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
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向幽灵手 | 诊断最低分 | 最弱诊断边界 | 门槛 |")
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
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | source->target | pattern | 改动帧 | 改动点 | capture_quality | semantic_floor | 说明 |")
        lines.append("|---|---|---|---:|---|---|---|---:|---:|---|---|---|")
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
                f"{row.get('pattern')} | {row.get('changed_frames')} | {row.get('changed_points')} | "
                f"{quality.get('status') or '-'}:{quality.get('reason') or '-'} | "
                f"{floor.get('source') or '-'}:{floor.get('reason') or '-'} | {row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 该门补充的是单手检测被误复制成双手的网页跟踪风险，不替代 hand-label-flicker、hand-dropout、missing-mask 或 inter-hand temporal desync 门。",
            "- 强持续幽灵手会改变真实双手语义，本轮仅作为诊断边界记录；是否升级为硬负例需结合真实摄像头样本和人工标注。",
            "- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run ghost-hand duplicate robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_ghost_hand_duplicate_robustness_gate_current"))
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
        "claim_policy": "synthetic ghost-hand duplicate robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": backend_status,
        "passed": passed,
        "min_score": args.min_score,
        "results": results,
    }

    json_path = output_dir / "flower_jump_ghost_hand_duplicate_robustness_gate.json"
    md_path = output_dir / "flower_jump_ghost_hand_duplicate_robustness_gate.md"
    csv_path = output_dir / "flower_jump_ghost_hand_duplicate_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳幽灵手重复鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳幽灵手重复鲁棒性报告：{md_path}")
    print(f"已生成花/跳幽灵手重复鲁棒性 CSV：{csv_path}")
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

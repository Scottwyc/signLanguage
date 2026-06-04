#!/usr/bin/env python3
"""Stress-test flower/jump scoring against relation-geometry variation.

Browser users do not place the right action hand at exactly the same height,
spacing, or trajectory as the template. This gate edits cached skeletons in
memory and verifies mild right-hand relation geometry changes remain scoreable,
especially for jump's left-ground/right-jumper relation. Strongly horizontal,
too-small, or reversed jump relation motion must be diagnosed as semantic
mismatch or score low.

This script does not call /api/score, run Holistic, move marker, or restart
5080.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

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
    _relation_delta_summary,
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
ACCEPTED_NEGATIVE_QUALITY = {"needs_recapture", "semantic_mismatch"}


def _right_hand_centers(seq: SequenceData) -> tuple[List[Optional[np.ndarray]], np.ndarray]:
    centers: List[Optional[np.ndarray]] = []
    visible: List[np.ndarray] = []
    for frame in seq.features:
        coords, valid = _hand_array(frame, "right_hand")
        if coords is None or valid is None or not valid.any():
            centers.append(None)
            continue
        center = coords[valid].mean(axis=0).astype(np.float32)
        centers.append(center)
        visible.append(center)
    if not visible:
        return centers, np.zeros(3, dtype=np.float32)
    return centers, np.stack(visible, axis=0).mean(axis=0).astype(np.float32)


def _delta_summary_json(seq: SequenceData) -> Optional[Dict[str, Any]]:
    summary = _relation_delta_summary(seq)
    if summary is None:
        return None
    return {
        "valid_count": int(summary.get("valid_count") or 0),
        "start_frame_idx": int(summary.get("start_frame_idx") or 0),
        "end_frame_idx": int(summary.get("end_frame_idx") or 0),
        "delta": [float(value) for value in np.asarray(summary.get("delta"), dtype=np.float32).tolist()],
        "start": [float(value) for value in np.asarray(summary.get("start"), dtype=np.float32).tolist()],
        "end": [float(value) for value in np.asarray(summary.get("end"), dtype=np.float32).tolist()],
        "source": summary.get("source"),
    }


def _transform_sequence(
    seq: SequenceData,
    name: str,
    *,
    profile: Any,
    offset: Sequence[float] = (0.0, 0.0, 0.0),
    y_amplitude_factor: Optional[float] = None,
    x_from_y: float = 0.0,
    reverse_y: bool = False,
    relation_jitter: float = 0.0,
    seed: int = 31,
) -> tuple[SequenceData, Dict[str, Any]]:
    base = _strip_to_base_groups(seq)
    centers, center_mean = _right_hand_centers(base)
    rng = np.random.default_rng(seed)
    items: List[FrameFeature] = []
    changed_frames = 0
    changed_visible_points = 0
    for idx, frame in enumerate(base.features):
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        presence = dict(frame.presence)
        coords, valid = _hand_array(frame, "right_hand")
        if coords is not None and valid is not None and valid.any() and centers[idx] is not None:
            coords = coords.copy()
            delta = np.asarray(offset, dtype=np.float32).copy()
            temporal_relation = centers[idx] - center_mean
            if y_amplitude_factor is not None:
                delta[1] += (float(y_amplitude_factor) - 1.0) * temporal_relation[1]
            if reverse_y:
                delta[1] += -2.0 * temporal_relation[1]
            if x_from_y:
                delta[0] += float(x_from_y) * temporal_relation[1]
            if relation_jitter > 0.0:
                delta[:2] += rng.normal(0.0, float(relation_jitter), size=2).astype(np.float32)
            if np.linalg.norm(delta) > 1e-8:
                coords[valid] = coords[valid] + delta
                changed_frames += 1
                changed_visible_points += int(valid.sum())
            _set_hand_group(frame, vector, mask, "right_hand", coords, valid)
            presence["right_hand"] = bool(valid.any())
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
        "offset": [float(value) for value in offset],
        "y_amplitude_factor": y_amplitude_factor,
        "x_from_y": float(x_from_y),
        "reverse_y": bool(reverse_y),
        "relation_jitter": float(relation_jitter),
        "changed_frames": changed_frames,
        "changed_visible_points": changed_visible_points,
        "total_frames": len(base.features),
    }
    return _sequence_with_relative_motion_features(transformed, profile), detail


def _spec(
    variant: str,
    kind: str,
    *,
    rationale: str,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": kind,
        "transform": kwargs,
        "min_score": min_score,
        "max_score": max_score,
        "gated": kind in {"positive", "negative"},
        "rationale": rationale,
    }


def _variant_specs(word: str, min_score: float, negative_max_score: float) -> List[Dict[str, Any]]:
    specs = [
        _spec(
            "self_recomputed",
            "positive",
            min_score=95.0,
            rationale="剥离基础组后重建 relation/motion 特征，应保持近满分。",
        ),
        _spec(
            "right_relation_offset_up_0.15",
            "positive",
            offset=(0.0, -0.15, 0.0),
            min_score=min_score,
            rationale="右手整体相对左手略高，模拟用户起手/镜头位置差异。",
        ),
        _spec(
            "right_relation_offset_down_0.15",
            "positive",
            offset=(0.0, 0.15, 0.0),
            min_score=min_score,
            rationale="右手整体相对左手略低，模拟手势位置差异。",
        ),
        _spec(
            "right_relation_offset_x_0.15",
            "positive",
            offset=(0.15, 0.0, 0.0),
            min_score=min_score,
            rationale="右手整体横向间距略变，核心动作和手形仍保留。",
        ),
        _spec(
            "right_relation_y_amplitude_0.70",
            "positive",
            y_amplitude_factor=0.70,
            min_score=min_score,
            rationale="右手相对运动高度缩小到 70%，仍应保持可评分。",
        ),
        _spec(
            "right_relation_y_amplitude_1.35",
            "positive",
            y_amplitude_factor=1.35,
            min_score=min_score,
            rationale="右手相对运动高度放大到 135%，仍应保持可评分。",
        ),
        _spec(
            "right_relation_x_from_y_0.35",
            "positive",
            x_from_y=0.35,
            min_score=min_score,
            rationale="右手跳跃轨迹带轻微横向分量，垂直关系仍清晰。",
        ),
        _spec(
            "right_relation_jitter_0.035",
            "positive",
            relation_jitter=0.035,
            min_score=min_score,
            rationale="右手相对左手的逐帧关系有小幅抖动，模拟网页关键点不稳。",
        ),
        _spec(
            "right_relation_y_amplitude_1.75_diagnostic",
            "diagnostic",
            y_amplitude_factor=1.75,
            rationale="更大相对运动高度只记录边界，不作为通过条件。",
        ),
    ]
    if word == "跳":
        specs.extend(
            [
                _spec(
                    "jump_relation_y_amplitude_0.45_negative",
                    "negative",
                    y_amplitude_factor=0.45,
                    max_score=negative_max_score,
                    rationale="跳跃相对高度过小，应低分或进入语义失败解释。",
                ),
                _spec(
                    "jump_relation_x_from_y_0.90_negative",
                    "negative",
                    x_from_y=0.90,
                    max_score=negative_max_score,
                    rationale="跳跃关系过度水平化，应低分或进入语义失败解释。",
                ),
                _spec(
                    "jump_relation_reverse_y_negative",
                    "negative",
                    reverse_y=True,
                    max_score=negative_max_score,
                    rationale="右手相对左手的跳跃方向反向，应低分或进入语义失败解释。",
                ),
            ]
        )
    else:
        specs.extend(
            [
                _spec(
                    "flower_relation_x_from_y_0.90_diagnostic",
                    "diagnostic",
                    x_from_y=0.90,
                    rationale="花不是双手关系核心词，强横向关系扰动只记录对右手开花主语义的边界。",
                ),
                _spec(
                    "flower_relation_reverse_y_diagnostic",
                    "diagnostic",
                    reverse_y=True,
                    rationale="花不是双手关系核心词，反向关系轨迹只记录诊断边界。",
                ),
            ]
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
    negative_max_score: float,
) -> Dict[str, Any]:
    standard_json = _template_json(template_root, word)
    loaded_standard = load_sequence(standard_json, feature_mode, force_bbox=False)
    profile = load_semantic_profile(word, semantic_profile_json)
    standard, standard_detail = _transform_sequence(loaded_standard, "standard_base", profile=profile)
    standard_relation_delta = _delta_summary_json(standard)
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(word, min_score, negative_max_score):
        query, detail = _transform_sequence(
            loaded_standard,
            str(spec["variant"]),
            profile=profile,
            **(spec.get("transform") or {}),
        )
        result = run_pair(standard, query, semantic_profile=profile, target_word=word, enable_cross_check=False)
        score_scale = result.get("score_scale") or {}
        row = {
            "variant": spec["variant"],
            "kind": spec["kind"],
            "gated": bool(spec["gated"]),
            "min_score": spec.get("min_score"),
            "max_score": spec.get("max_score"),
            "rationale": spec["rationale"],
            **detail,
            "score": float(result["prototype_score"]),
            "dtw_distance": float(result["dtw_distance"]),
            "normalized_distance": float(result["normalized_distance"]),
            "alignment_policy": result.get("alignment_policy"),
            "capture_quality": score_scale.get("capture_quality"),
            "semantic_floor": score_scale.get("semantic_floor"),
            "action_window": result.get("action_window"),
            "query_relation_delta": _delta_summary_json(query),
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
        "standard_transform_detail": standard_detail,
        "standard_relation_delta": standard_relation_delta,
        "semantic_profile": _profile_summary(profile),
        "gate_pass": all(bool(row["passed"]) for row in rows if row["gated"]),
        "weakest_positive_score": float(weakest_positive["score"]) if weakest_positive else None,
        "weakest_positive_variant": weakest_positive["variant"] if weakest_positive else "",
        "strongest_negative_score": float(strongest_negative["score"]) if strongest_negative else None,
        "strongest_negative_variant": strongest_negative["variant"] if strongest_negative else "",
        "weakest_diagnostic_score": float(weakest_diagnostic["score"]) if weakest_diagnostic else None,
        "weakest_diagnostic_variant": weakest_diagnostic["variant"] if weakest_diagnostic else "",
        "min_required_score": min_score,
        "negative_max_score": negative_max_score,
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
        "offset",
        "y_amplitude_factor",
        "x_from_y",
        "reverse_y",
        "relation_jitter",
        "changed_frames",
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
                        "max_score": row.get("max_score"),
                        "offset": ",".join(str(value) for value in (row.get("offset") or [])),
                        "y_amplitude_factor": row.get("y_amplitude_factor"),
                        "x_from_y": row.get("x_from_y"),
                        "reverse_y": row.get("reverse_y"),
                        "relation_jitter": row.get("relation_jitter"),
                        "changed_frames": row.get("changed_frames"),
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
        "# 花/跳双手关系几何鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，调整右手相对左手的固定偏移、运动高度、横向分量和逐帧关系抖动，并重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：温和关系几何变化仍可正常评分；`跳` 的高度过小、强水平化、反向跳跃必须低分或进入重采/语义失败解释。",
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
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向关系扰动 | 负向最高分 | 最强负向关系 | 诊断最低分 | 最弱诊断关系 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|---|---:|")
    for item in payload["results"]:
        lines.append(
            f"| {item['word']} | {'PASS' if item['gate_pass'] else 'FAIL'} | "
            f"{_fmt(item['weakest_positive_score'])} | {item['weakest_positive_variant']} | "
            f"{_fmt(item['strongest_negative_score'])} | {item['strongest_negative_variant'] or '-'} | "
            f"{_fmt(item['weakest_diagnostic_score'])} | {item['weakest_diagnostic_variant'] or '-'} | "
            f"{_fmt(item['min_required_score'])} |"
        )
    lines.append("")
    lines.append("## 分项明细")
    for item in payload["results"]:
        lines.extend(["", f"### {item['word']}", "", f"- 标准序列：`{item['standard_json']}`", ""])
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | offset | y_amp | x_from_y | capture_quality | semantic_floor | 说明 |")
        lines.append("|---|---|---|---:|---|---|---:|---:|---|---|---|")
        for row in sorted(item["variants"], key=lambda value: (value["kind"], float(value["score"]))):
            quality = row.get("capture_quality") or {}
            floor = row.get("semantic_floor") or {}
            if row["kind"] == "positive":
                threshold = f">= {row.get('min_score')}"
                status = "PASS" if row["passed"] else "FAIL"
            elif row["kind"] == "negative":
                threshold = f"<= {row.get('max_score')} 或重采/语义失败"
                status = "PASS" if row["passed"] else "FAIL"
            else:
                threshold = "diagnostic"
                status = "DIAG"
            lines.append(
                f"| {row['variant']} | {row['kind']} | {status} | {_fmt(row['score'])} | "
                f"{threshold} | {','.join(str(value) for value in (row.get('offset') or [])) or '-'} | "
                f"{_fmt(row.get('y_amplitude_factor'))} | {_fmt(row.get('x_from_y'))} | "
                f"{quality.get('status') or '-'}:{quality.get('reason') or '-'} | "
                f"{floor.get('source') or '-'}:{floor.get('reason') or '-'} | {row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 正向门覆盖不同用户常见的右手位置、跳跃高度和轻微横向轨迹差异。",
            "- `跳` 的负向关系门允许 capture_quality 证明语义失败，因为当前 score 值本身可能仍由其它相似证据托住。",
            "- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run relation-geometry robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_relation_geometry_robustness_gate_current"))
    parser.add_argument("--words", nargs="+", default=DEFAULT_WORDS)
    parser.add_argument("--feature-mode", choices=["auto", "landmark", "bbox"], default="auto")
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--status-timeout-sec", type=float, default=3.0)
    parser.add_argument("--min-score", type=float, default=70.0)
    parser.add_argument("--negative-max-score", type=float, default=45.0)
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
            negative_max_score=args.negative_max_score,
        )
        for word in args.words
    ]
    backend_status = _load_backend_status(args.backend_url, args.status_timeout_sec)
    passed = all(bool(item["gate_pass"]) for item in results)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "claim_policy": "synthetic relation-geometry robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": backend_status,
        "passed": passed,
        "min_score": args.min_score,
        "negative_max_score": args.negative_max_score,
        "accepted_negative_quality": sorted(ACCEPTED_NEGATIVE_QUALITY),
        "results": results,
    }

    json_path = output_dir / "flower_jump_relation_geometry_robustness_gate.json"
    md_path = output_dir / "flower_jump_relation_geometry_robustness_gate.md"
    csv_path = output_dir / "flower_jump_relation_geometry_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳关系几何鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳关系几何鲁棒性报告：{md_path}")
    print(f"已生成花/跳关系几何鲁棒性 CSV：{csv_path}")
    print(f"综合状态：{'PASS' if passed else 'FAIL'}")
    for item in results:
        print(
            f"- {item['word']}: {'PASS' if item['gate_pass'] else 'FAIL'} "
            f"positive_min={_fmt(item['weakest_positive_score'])} "
            f"negative_max={_fmt(item['strongest_negative_score'])} "
            f"diagnostic_min={_fmt(item['weakest_diagnostic_score'])}"
        )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

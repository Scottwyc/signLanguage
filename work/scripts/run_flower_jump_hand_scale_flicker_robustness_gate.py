#!/usr/bin/env python3
"""Stress-test flower/jump scoring against temporal hand-scale flicker.

Webcam hand detectors can make the local hand crop "breathe" over time: the
whole hand is still plausible, but its local scale or aspect ratio changes from
frame to frame. Static hand-shape scale gates cover a fixed user/camera scale;
this gate covers detector-scale instability across the sequence.

This script edits cached skeleton sequences in memory only. It does not call
/api/score, run Holistic, move the web marker, or restart 5080.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
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
HAND_GROUPS = ["left_hand", "right_hand"]


def _signal(pattern: str, idx: int, length: int, period: int) -> float:
    if pattern == "none":
        return 0.0
    if pattern == "smooth":
        if length <= 1:
            return 0.0
        return math.sin(2.0 * math.pi * idx / float(length - 1))
    if pattern == "sparse":
        if idx <= 0 or idx >= length - 1 or period <= 1:
            return 0.0
        if idx % period != period // 2:
            return 0.0
        return 1.0 if (idx // period) % 2 == 0 else -1.0
    raise ValueError(f"unknown hand-scale flicker pattern: {pattern}")


def _scale_factors(mode: str, signal: float, amplitude: float) -> Tuple[float, float, float]:
    if mode == "uniform_xy":
        scale = 1.0 + amplitude * signal
        return scale, scale, 1.0
    if mode == "aspect_xy":
        return 1.0 + amplitude * signal, 1.0 - amplitude * signal, 1.0
    raise ValueError(f"unknown hand-scale flicker mode: {mode}")


def _mutated_sequence(
    seq: SequenceData,
    name: str,
    *,
    groups: Sequence[str],
    pattern: str,
    mode: str,
    amplitude: float,
    period: int,
    profile: Any,
) -> Tuple[SequenceData, Dict[str, Any]]:
    base = _strip_to_base_groups(seq)
    items: List[FrameFeature] = []
    changed_frames = 0
    changed_visible_points = 0
    sx_values: List[float] = []
    sy_values: List[float] = []
    total_frames = len(base.features)

    for idx, frame in enumerate(base.features):
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        presence = dict(frame.presence)
        sig = _signal(pattern, idx, total_frames, period)
        sx, sy, sz = _scale_factors(mode, sig, amplitude)
        sx_values.append(float(sx))
        sy_values.append(float(sy))
        frame_changed = abs(sx - 1.0) > 1e-6 or abs(sy - 1.0) > 1e-6 or abs(sz - 1.0) > 1e-6

        for group in groups:
            coords, valid = _hand_array(frame, group)
            if coords is None or valid is None or not valid.any():
                continue
            if frame_changed:
                center = coords[0].copy() if bool(valid[0]) else coords[valid].mean(axis=0)
                factors = np.asarray([sx, sy, sz], dtype=np.float32)
                coords[valid] = center + factors * (coords[valid] - center)
                changed_visible_points += int(valid.sum())
            _set_hand_group(frame, vector, mask, group, coords, valid)
            presence[group] = bool(valid.any())

        if frame_changed:
            changed_frames += 1
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
        "operation": "hand_scale_flicker",
        "groups": list(groups),
        "pattern": pattern,
        "mode": mode,
        "amplitude": amplitude,
        "period": period,
        "changed_frames": changed_frames,
        "changed_visible_points": changed_visible_points,
        "total_frames": total_frames,
        "sx_min": min(sx_values) if sx_values else None,
        "sx_max": max(sx_values) if sx_values else None,
        "sy_min": min(sy_values) if sy_values else None,
        "sy_max": max(sy_values) if sy_values else None,
    }
    return _sequence_with_relative_motion_features(transformed, profile), detail


def _spec(
    variant: str,
    kind: str,
    *,
    groups: Sequence[str],
    pattern: str,
    mode: str,
    amplitude: float,
    period: int,
    rationale: str,
    min_score: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": kind,
        "groups": list(groups),
        "pattern": pattern,
        "mode": mode,
        "amplitude": amplitude,
        "period": period,
        "min_score": min_score,
        "gated": kind == "positive",
        "rationale": rationale,
    }


def _variant_specs(min_score: float) -> List[Dict[str, Any]]:
    return [
        _spec(
            "self_recomputed",
            "positive",
            groups=HAND_GROUPS,
            pattern="none",
            mode="uniform_xy",
            amplitude=0.0,
            period=1,
            min_score=95.0,
            rationale="标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。",
        ),
        _spec(
            "both_hands_smooth_uniform_breathing_0.10",
            "positive",
            groups=HAND_GROUPS,
            pattern="smooth",
            mode="uniform_xy",
            amplitude=0.10,
            period=1,
            min_score=min_score,
            rationale="双手局部检测框随时间平滑放大/缩小 10%，模拟 detector box breathing。",
        ),
        _spec(
            "both_hands_smooth_aspect_breathing_0.10",
            "positive",
            groups=HAND_GROUPS,
            pattern="smooth",
            mode="aspect_xy",
            amplitude=0.10,
            period=1,
            min_score=min_score,
            rationale="双手局部 x/y 尺度反向平滑漂移 10%，模拟透视和检测框宽高抖动。",
        ),
        _spec(
            "right_hand_smooth_uniform_breathing_0.12",
            "positive",
            groups=["right_hand"],
            pattern="smooth",
            mode="uniform_xy",
            amplitude=0.12,
            period=1,
            min_score=min_score,
            rationale="右手核心手局部检测框平滑呼吸 12%，不应破坏花开或跳跃核心证据。",
        ),
        _spec(
            "right_hand_sparse_scale_flicker_0.12_every_5f",
            "positive",
            groups=["right_hand"],
            pattern="sparse",
            mode="uniform_xy",
            amplitude=0.12,
            period=5,
            min_score=min_score,
            rationale="少量帧右手局部尺度正负 12% 尖峰，模拟短时 detector scale flicker。",
        ),
        _spec(
            "left_hand_sparse_scale_flicker_0.12_every_5f",
            "positive",
            groups=["left_hand"],
            pattern="sparse",
            mode="uniform_xy",
            amplitude=0.12,
            period=5,
            min_score=min_score,
            rationale="少量帧左手局部尺度正负 12% 尖峰，覆盖跳的地面手和花的非核心手。",
        ),
        _spec(
            "both_hands_sparse_aspect_flicker_0.10_every_6f",
            "positive",
            groups=HAND_GROUPS,
            pattern="sparse",
            mode="aspect_xy",
            amplitude=0.10,
            period=6,
            min_score=min_score,
            rationale="双手少量帧 x/y 宽高反向 flicker 10%，模拟网页上传帧中的检测框宽高抖动。",
        ),
        _spec(
            "both_hands_strong_smooth_uniform_breathing_0.35_diagnostic",
            "diagnostic",
            groups=HAND_GROUPS,
            pattern="smooth",
            mode="uniform_xy",
            amplitude=0.35,
            period=1,
            rationale="双手平滑尺度呼吸 35% 属于强边界，只记录诊断分数。",
        ),
        _spec(
            "both_hands_strong_smooth_aspect_breathing_0.35_diagnostic",
            "diagnostic",
            groups=HAND_GROUPS,
            pattern="smooth",
            mode="aspect_xy",
            amplitude=0.35,
            period=1,
            rationale="双手 x/y 尺度反向平滑漂移 35% 属于强透视边界，只记录诊断分数。",
        ),
        _spec(
            "right_hand_sparse_scale_spike_0.45_every_4f_diagnostic",
            "diagnostic",
            groups=["right_hand"],
            pattern="sparse",
            mode="uniform_xy",
            amplitude=0.45,
            period=4,
            rationale="右手少量帧尺度正负 45% 尖峰不是正常轻微抖动，只记录诊断分数。",
        ),
        _spec(
            "both_hands_sparse_aspect_spike_0.45_every_4f_diagnostic",
            "diagnostic",
            groups=HAND_GROUPS,
            pattern="sparse",
            mode="aspect_xy",
            amplitude=0.45,
            period=4,
            rationale="双手少量帧宽高强尖峰属于 detector 严重不稳定，只记录诊断分数。",
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
    standard, standard_detail = _mutated_sequence(
        loaded_standard,
        "standard_base",
        groups=HAND_GROUPS,
        pattern="none",
        mode="uniform_xy",
        amplitude=0.0,
        period=1,
        profile=profile,
    )
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(min_score):
        query, detail = _mutated_sequence(
            loaded_standard,
            str(spec["variant"]),
            groups=spec["groups"],
            pattern=str(spec["pattern"]),
            mode=str(spec["mode"]),
            amplitude=float(spec["amplitude"]),
            period=int(spec["period"]),
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
        "groups",
        "pattern",
        "mode",
        "amplitude",
        "period",
        "sx_min",
        "sx_max",
        "sy_min",
        "sy_max",
        "changed_frames",
        "changed_visible_points",
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
                        "groups": json.dumps(row.get("groups") or [], ensure_ascii=False),
                        "pattern": row.get("pattern"),
                        "mode": row.get("mode"),
                        "amplitude": row.get("amplitude"),
                        "period": row.get("period"),
                        "sx_min": row.get("sx_min"),
                        "sx_max": row.get("sx_max"),
                        "sy_min": row.get("sy_min"),
                        "sy_max": row.get("sy_max"),
                        "changed_frames": row.get("changed_frames"),
                        "changed_visible_points": row.get("changed_visible_points"),
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
        "# 花/跳手部尺度时序呼吸鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，逐帧缩放手部局部坐标后重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：轻微平滑 hand-box breathing、少量帧级 scale/aspect flicker 仍保持可评分；强尖峰只记录诊断边界。",
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
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向尺度呼吸 | 诊断最低分 | 最弱诊断尺度呼吸 | 门槛 |")
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
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | 手 | pattern | mode | amp | sx | sy | 改动帧 | capture_quality | semantic_floor | 说明 |")
        lines.append("|---|---|---|---:|---|---|---|---|---:|---|---|---:|---|---|---|")
        for row in sorted(item["variants"], key=lambda value: (value["kind"], float(value["score"]))):
            quality = row.get("capture_quality") or {}
            floor = row.get("semantic_floor") or {}
            if row["kind"] == "positive":
                threshold = f">= {row.get('min_score')}"
                status = "PASS" if row["passed"] else "FAIL"
            else:
                threshold = "diagnostic"
                status = "DIAG"
            groups = json.dumps(row.get("groups") or [], ensure_ascii=False)
            lines.append(
                f"| {row['variant']} | {row['kind']} | {status} | {_fmt(row['score'])} | "
                f"{threshold} | `{groups}` | {row.get('pattern') or '-'} | {row.get('mode') or '-'} | "
                f"{_fmt(row.get('amplitude'))} | {_fmt(row.get('sx_min'))}-{_fmt(row.get('sx_max'))} | "
                f"{_fmt(row.get('sy_min'))}-{_fmt(row.get('sy_max'))} | {row.get('changed_frames')} | "
                f"{quality.get('status') or '-'}:{quality.get('reason') or '-'} | "
                f"{floor.get('source') or '-'}:{floor.get('reason') or '-'} | {row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 该门补充的是时间维度的 hand detector 尺度漂移，不替代静态 hand-shape scale、perspective/shear 或 landmark-noise 门。",
            "- 正向变体只覆盖 10%-12% 的平滑或稀疏尺度变化，强 35%-45% 漂移/尖峰不是正常网页采集要求。",
            "- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run temporal hand-scale flicker robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_hand_scale_flicker_robustness_gate_current"))
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
        "claim_policy": "synthetic temporal hand-scale flicker robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": backend_status,
        "passed": passed,
        "min_score": args.min_score,
        "results": results,
    }

    json_path = output_dir / "flower_jump_hand_scale_flicker_robustness_gate.json"
    md_path = output_dir / "flower_jump_hand_scale_flicker_robustness_gate.md"
    csv_path = output_dir / "flower_jump_hand_scale_flicker_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳手部尺度时序呼吸鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳手部尺度时序呼吸鲁棒性报告：{md_path}")
    print(f"已生成花/跳手部尺度时序呼吸鲁棒性 CSV：{csv_path}")
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

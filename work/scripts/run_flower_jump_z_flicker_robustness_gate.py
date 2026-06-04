#!/usr/bin/env python3
"""Stress-test flower/jump scoring against temporal z/depth flicker.

Holistic z values can breathe or jump slightly from frame to frame when webcam
exposure, hand distance, or tracker stabilization changes. Static depth gates
cover fixed z offset/scale; this gate covers temporal z drift while preserving
the visible 2D sign semantics.

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
COORD_GROUPS = ["pose", "left_hand", "right_hand", "face"]
HAND_GROUPS = {"left_hand", "right_hand"}


def _group_coords_and_valid(frame: FrameFeature, group: str) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    if group not in frame.groups:
        return None, None
    sl = frame.groups[group]
    values = frame.vector[sl]
    masks = frame.mask[sl]
    if values.size % 3 != 0 or masks.size % 3 != 0:
        return None, None
    return values.reshape(-1, 3).copy(), masks.reshape(-1, 3).mean(axis=1) > 0.5


def _set_coord_group(frame: FrameFeature, vector: np.ndarray, group: str, coords: np.ndarray) -> None:
    if group not in frame.groups:
        return
    sl = frame.groups[group]
    if vector[sl].size == coords.size:
        vector[sl] = coords.reshape(-1)


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
    raise ValueError(f"unknown z flicker pattern: {pattern}")


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
    value_by_frame: List[float] = []
    total_frames = len(base.features)

    for idx, frame in enumerate(base.features):
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        presence = dict(frame.presence)
        signal = _signal(pattern, idx, total_frames, period)
        value = float(amplitude) * float(signal)
        value_by_frame.append(float(value))
        frame_changed = abs(value) > 1e-6
        for group in groups:
            coords, valid = _group_coords_and_valid(frame, group)
            if coords is None or valid is None or not valid.any():
                continue
            if frame_changed:
                if mode == "offset":
                    coords[valid, 2] += value
                elif mode == "scale":
                    coords[valid, 2] *= 1.0 + value
                else:
                    raise ValueError(f"unknown z flicker mode: {mode}")
                changed_visible_points += int(valid.sum())
            if group in HAND_GROUPS:
                _set_hand_group(frame, vector, mask, group, coords, valid)
                presence[group] = bool(valid.any())
            else:
                _set_coord_group(frame, vector, group, coords)
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
        "operation": "z_flicker",
        "groups": list(groups),
        "pattern": pattern,
        "mode": mode,
        "amplitude": amplitude,
        "period": period,
        "changed_frames": changed_frames,
        "changed_visible_points": changed_visible_points,
        "total_frames": total_frames,
        "value_min": min(value_by_frame) if value_by_frame else None,
        "value_max": max(value_by_frame) if value_by_frame else None,
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
            groups=COORD_GROUPS,
            pattern="none",
            mode="offset",
            amplitude=0.0,
            period=1,
            min_score=95.0,
            rationale="标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。",
        ),
        _spec(
            "smooth_global_z_offset_0.08",
            "positive",
            groups=COORD_GROUPS,
            pattern="smooth",
            mode="offset",
            amplitude=0.08,
            period=1,
            min_score=min_score,
            rationale="整人 z 坐标随时间平滑呼吸 8%，模拟 webcam/Holistic 深度零点漂移。",
        ),
        _spec(
            "smooth_global_z_scale_0.20",
            "positive",
            groups=COORD_GROUPS,
            pattern="smooth",
            mode="scale",
            amplitude=0.20,
            period=1,
            min_score=min_score,
            rationale="整人 z 动态随时间在 0.8-1.2 倍之间平滑变化。",
        ),
        _spec(
            "smooth_hand_z_offset_0.06",
            "positive",
            groups=["left_hand", "right_hand"],
            pattern="smooth",
            mode="offset",
            amplitude=0.06,
            period=1,
            min_score=min_score,
            rationale="双手 z 坐标随时间平滑漂移，模拟手离镜头距离估计轻微波动。",
        ),
        _spec(
            "smooth_hand_z_scale_0.20",
            "positive",
            groups=["left_hand", "right_hand"],
            pattern="smooth",
            mode="scale",
            amplitude=0.20,
            period=1,
            min_score=min_score,
            rationale="双手局部 z 动态随时间平滑缩放，并重建手形特征。",
        ),
        _spec(
            "sparse_hand_z_offset_0.06_every_5f",
            "positive",
            groups=["left_hand", "right_hand"],
            pattern="sparse",
            mode="offset",
            amplitude=0.06,
            period=5,
            min_score=min_score,
            rationale="少量帧出现手部 z 跳动，模拟 tracker 深度闪断。",
        ),
        _spec(
            "right_hand_smooth_z_offset_0.05",
            "positive",
            groups=["right_hand"],
            pattern="smooth",
            mode="offset",
            amplitude=0.05,
            period=1,
            min_score=min_score,
            rationale="右手核心手随时间轻微 z 漂移，验证单手深度抖动不压低语义分。",
        ),
        _spec(
            "strong_global_z_offset_0.25_diagnostic",
            "diagnostic",
            groups=COORD_GROUPS,
            pattern="smooth",
            mode="offset",
            amplitude=0.25,
            period=1,
            rationale="强整人 z 零点漂移不作为正常网页要求，只记录诊断边界。",
        ),
        _spec(
            "strong_hand_z_scale_0.55_diagnostic",
            "diagnostic",
            groups=["left_hand", "right_hand"],
            pattern="smooth",
            mode="scale",
            amplitude=0.55,
            period=1,
            rationale="强手部 z 动态缩放会改变局部手形，只记录诊断边界。",
        ),
        _spec(
            "strong_sparse_hand_z_offset_0.18_every_4f_diagnostic",
            "diagnostic",
            groups=["left_hand", "right_hand"],
            pattern="sparse",
            mode="offset",
            amplitude=0.18,
            period=4,
            rationale="强稀疏手部 z 跳点只记录诊断边界。",
        ),
    ]


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
        groups=COORD_GROUPS,
        pattern="none",
        mode="offset",
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
        "standard_z_flicker_detail": standard_detail,
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
        "changed_frames",
        "changed_visible_points",
        "value_min",
        "value_max",
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
                        "mode": row.get("mode"),
                        "amplitude": row.get("amplitude"),
                        "period": row.get("period"),
                        "changed_frames": row.get("changed_frames"),
                        "changed_visible_points": row.get("changed_visible_points"),
                        "value_min": row.get("value_min"),
                        "value_max": row.get("value_max"),
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
        "# 花/跳 z 深度时序抖动鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，合成逐帧 z offset/scale breathing 和稀疏 z 跳动，并重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：轻微 z 深度呼吸或闪断不应压低 `花/跳` 网页评分；强 z 漂移只记录诊断边界。",
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
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向 z 抖动 | 诊断最低分 | 最弱诊断 z 抖动 | 门槛 |")
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
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | 组 | 模式 | 幅度 | 变化帧 | capture_quality | 说明 |")
        lines.append("|---|---|---|---:|---|---|---|---:|---:|---|---|")
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
                f"{row.get('pattern')}/{row.get('mode')} | {_fmt(row.get('amplitude'))} | "
                f"{row.get('changed_frames')}/{row.get('total_frames')} | "
                f"{quality.get('status') or '-'}:{quality.get('reason') or '-'} | "
                f"{row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 正向门只覆盖轻微平滑 z 呼吸、轻微手部 z 漂移和少量稀疏 z 跳动。",
            "- 强 z scale/offset 或强稀疏跳点仅作诊断边界，因为它们可能真实破坏局部手形或双手关系。",
            "- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run temporal z/depth flicker robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_z_flicker_robustness_gate_current"))
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
        "claim_policy": "synthetic temporal-z-flicker robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": backend_status,
        "passed": passed,
        "min_score": args.min_score,
        "results": results,
    }

    json_path = output_dir / "flower_jump_z_flicker_robustness_gate.json"
    md_path = output_dir / "flower_jump_z_flicker_robustness_gate.md"
    csv_path = output_dir / "flower_jump_z_flicker_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳 z 深度时序抖动鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳 z 深度时序抖动鲁棒性报告：{md_path}")
    print(f"已生成花/跳 z 深度时序抖动鲁棒性 CSV：{csv_path}")
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

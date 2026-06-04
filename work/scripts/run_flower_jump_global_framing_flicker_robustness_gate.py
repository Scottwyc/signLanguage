#!/usr/bin/env python3
"""Stress-test flower/jump scoring against temporal global framing flicker.

Real webcam clips can contain slow auto-framing drift, electronic stabilization
correction, or small user sway toward/away from the camera. Static framing
gates cover fixed zoom/pan; this gate covers frame-to-frame global pan/zoom
changes of the whole visible skeleton while preserving the sign semantics.

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


def _visible_center(seq: SequenceData) -> np.ndarray:
    points: List[np.ndarray] = []
    for frame in seq.features:
        for group in COORD_GROUPS:
            coords, valid = _group_coords_and_valid(frame, group)
            if coords is None or valid is None or not valid.any():
                continue
            points.append(coords[valid, :2])
    if not points:
        return np.zeros(2, dtype=np.float32)
    return np.concatenate(points, axis=0).mean(axis=0).astype(np.float32)


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
    raise ValueError(f"unknown global framing flicker pattern: {pattern}")


def _transform_values(mode: str, signal: float, amplitude: float) -> Tuple[float, float, float]:
    value = float(amplitude) * float(signal)
    if mode == "pan_x":
        return 1.0, value, 0.0
    if mode == "pan_y":
        return 1.0, 0.0, value
    if mode == "pan_diag":
        return 1.0, value, -0.65 * value
    if mode == "zoom":
        return 1.0 + value, 0.0, 0.0
    if mode == "zoom_pan_diag":
        return 1.0 + value, 0.55 * value, -0.35 * value
    raise ValueError(f"unknown global framing flicker mode: {mode}")


def _mutated_sequence(
    seq: SequenceData,
    name: str,
    *,
    pattern: str,
    mode: str,
    amplitude: float,
    period: int,
    profile: Any,
) -> Tuple[SequenceData, Dict[str, Any]]:
    base = _strip_to_base_groups(seq)
    center = _visible_center(base)
    items: List[FrameFeature] = []
    changed_frames = 0
    changed_visible_points = 0
    scale_values: List[float] = []
    dx_values: List[float] = []
    dy_values: List[float] = []
    total_frames = len(base.features)

    for idx, frame in enumerate(base.features):
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        presence = dict(frame.presence)
        scale, dx, dy = _transform_values(mode, _signal(pattern, idx, total_frames, period), amplitude)
        scale_values.append(float(scale))
        dx_values.append(float(dx))
        dy_values.append(float(dy))
        frame_changed = abs(scale - 1.0) > 1e-6 or abs(dx) > 1e-6 or abs(dy) > 1e-6

        for group in COORD_GROUPS:
            coords, valid = _group_coords_and_valid(frame, group)
            if coords is None or valid is None or not valid.any():
                continue
            if frame_changed:
                coords[valid, :2] = center + (coords[valid, :2] - center) * float(scale)
                coords[valid, 0] += float(dx)
                coords[valid, 1] += float(dy)
                coords[valid, 2] *= float(scale)
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
        "operation": "global_framing_flicker",
        "pattern": pattern,
        "mode": mode,
        "amplitude": amplitude,
        "period": period,
        "changed_frames": changed_frames,
        "changed_visible_points": changed_visible_points,
        "total_frames": total_frames,
        "scale_min": min(scale_values) if scale_values else None,
        "scale_max": max(scale_values) if scale_values else None,
        "dx_min": min(dx_values) if dx_values else None,
        "dx_max": max(dx_values) if dx_values else None,
        "dy_min": min(dy_values) if dy_values else None,
        "dy_max": max(dy_values) if dy_values else None,
    }
    return _sequence_with_relative_motion_features(transformed, profile), detail


def _spec(
    variant: str,
    kind: str,
    *,
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
            pattern="none",
            mode="pan_x",
            amplitude=0.0,
            period=1,
            min_score=95.0,
            rationale="标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。",
        ),
        _spec(
            "smooth_global_pan_x_0.06",
            "positive",
            pattern="smooth",
            mode="pan_x",
            amplitude=0.06,
            period=1,
            min_score=min_score,
            rationale="整人画面随时间平滑横向漂移 6%，模拟电子防抖或用户身体轻微平移。",
        ),
        _spec(
            "smooth_global_pan_y_0.06",
            "positive",
            pattern="smooth",
            mode="pan_y",
            amplitude=0.06,
            period=1,
            min_score=min_score,
            rationale="整人画面随时间平滑纵向漂移 6%，模拟自动取景中心慢漂。",
        ),
        _spec(
            "smooth_global_zoom_0.08",
            "positive",
            pattern="smooth",
            mode="zoom",
            amplitude=0.08,
            period=1,
            min_score=min_score,
            rationale="整人画面随时间 0.92-1.08 倍平滑缩放，模拟用户前后轻微移动或自动取景 zoom。",
        ),
        _spec(
            "smooth_global_zoom_pan_diag_0.06",
            "positive",
            pattern="smooth",
            mode="zoom_pan_diag",
            amplitude=0.06,
            period=1,
            min_score=min_score,
            rationale="整人画面同时有轻微缩放和对角漂移，模拟自动取景合成扰动。",
        ),
        _spec(
            "sparse_global_pan_diag_0.05_every_5f",
            "positive",
            pattern="sparse",
            mode="pan_diag",
            amplitude=0.05,
            period=5,
            min_score=min_score,
            rationale="少量帧整人画面中心出现 5% 对角跳动，模拟防抖/裁剪中心短时修正。",
        ),
        _spec(
            "sparse_global_zoom_0.06_every_6f",
            "positive",
            pattern="sparse",
            mode="zoom",
            amplitude=0.06,
            period=6,
            min_score=min_score,
            rationale="少量帧整人画面出现 6% zoom 跳点，完整动作语义仍应可评分。",
        ),
        _spec(
            "strong_smooth_global_pan_y_0.22_diagnostic",
            "diagnostic",
            pattern="smooth",
            mode="pan_y",
            amplitude=0.22,
            period=1,
            rationale="整人画面平滑大幅纵向漂移 22% 属于强边界，只记录诊断分数。",
        ),
        _spec(
            "strong_smooth_global_zoom_0.35_diagnostic",
            "diagnostic",
            pattern="smooth",
            mode="zoom",
            amplitude=0.35,
            period=1,
            rationale="整人画面 0.65-1.35 倍平滑 zoom 属于强边界，只记录诊断分数。",
        ),
        _spec(
            "strong_sparse_global_zoom_pan_0.18_every_4f_diagnostic",
            "diagnostic",
            pattern="sparse",
            mode="zoom_pan_diag",
            amplitude=0.18,
            period=4,
            rationale="少量帧大幅 zoom+pan 跳点不是正常轻微自动取景，只记录诊断分数。",
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
        pattern="none",
        mode="pan_x",
        amplitude=0.0,
        period=1,
        profile=profile,
    )
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(min_score):
        query, detail = _mutated_sequence(
            loaded_standard,
            str(spec["variant"]),
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
        "pattern",
        "mode",
        "amplitude",
        "period",
        "scale_min",
        "scale_max",
        "dx_min",
        "dx_max",
        "dy_min",
        "dy_max",
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
                        "pattern": row.get("pattern"),
                        "mode": row.get("mode"),
                        "amplitude": row.get("amplitude"),
                        "period": row.get("period"),
                        "scale_min": row.get("scale_min"),
                        "scale_max": row.get("scale_max"),
                        "dx_min": row.get("dx_min"),
                        "dx_max": row.get("dx_max"),
                        "dy_min": row.get("dy_min"),
                        "dy_max": row.get("dy_max"),
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
        "# 花/跳全局取景时序漂移鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，对整人 pose/face/双手逐帧做全局 pan/zoom 后重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：轻微自动取景漂移、电子防抖中心修正和用户前后晃动仍保持可评分；强 pan/zoom 跳点只记录诊断边界。",
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
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向全局取景漂移 | 诊断最低分 | 最弱诊断全局取景漂移 | 门槛 |")
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
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | pattern | mode | amp | scale | dx | dy | 改动帧 | capture_quality | semantic_floor | 说明 |")
        lines.append("|---|---|---|---:|---|---|---|---:|---|---|---|---:|---|---|---|")
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
                f"{threshold} | {row.get('pattern') or '-'} | {row.get('mode') or '-'} | "
                f"{_fmt(row.get('amplitude'))} | {_fmt(row.get('scale_min'))}-{_fmt(row.get('scale_max'))} | "
                f"{_fmt(row.get('dx_min'))}-{_fmt(row.get('dx_max'))} | "
                f"{_fmt(row.get('dy_min'))}-{_fmt(row.get('dy_max'))} | {row.get('changed_frames')} | "
                f"{quality.get('status') or '-'}:{quality.get('reason') or '-'} | "
                f"{floor.get('source') or '-'}:{floor.get('reason') or '-'} | {row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 该门补充的是整人画面级的时间漂移，不替代静态 framing、aspect-ratio、hand-center-flicker 或 hand-scale-flicker 门。",
            "- 正向变体覆盖 5%-8% 的平滑/稀疏 pan/zoom，强 18%-35% pan/zoom 不是正常网页采集要求。",
            "- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run temporal global-framing flicker robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_global_framing_flicker_robustness_gate_current"))
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
        "claim_policy": "synthetic temporal global-framing flicker robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": backend_status,
        "passed": passed,
        "min_score": args.min_score,
        "results": results,
    }

    json_path = output_dir / "flower_jump_global_framing_flicker_robustness_gate.json"
    md_path = output_dir / "flower_jump_global_framing_flicker_robustness_gate.md"
    csv_path = output_dir / "flower_jump_global_framing_flicker_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳全局取景时序漂移鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳全局取景时序漂移鲁棒性报告：{md_path}")
    print(f"已生成花/跳全局取景时序漂移鲁棒性 CSV：{csv_path}")
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

#!/usr/bin/env python3
"""Stress-test flower/jump scoring against combined browser-like perturbations.

Single robustness gates cover one failure mode at a time. Real browser webcam
clips can combine several mild issues in one recording: slight aspect stretch,
coordinate quantization, local signing-speed variation, short frame freezes,
and brief hand-detection gaps. This gate composes those mild perturbations and
keeps stronger stacks diagnostic-only.

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
from typing import Any, Callable, Dict, List, Optional, Sequence

import numpy as np

from score_holistic_sequence_mvp import (
    DEFAULT_SEMANTIC_PROFILE_JSON,
    FrameFeature,
    SequenceData,
    _clone_frame,
    _clone_sequence,
    _hand_shape_feature,
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
BASE_GROUPS = ["pose", "left_hand", "right_hand", "left_hand_shape", "right_hand_shape", "face"]
COORD_GROUPS = ["pose", "left_hand", "right_hand", "face"]
HAND_GROUPS = ["left_hand", "right_hand"]
HAND_SHAPE_GROUPS = {
    "left_hand": ["left_hand", "left_hand_shape"],
    "right_hand": ["right_hand", "right_hand_shape"],
}


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


def _strip_to_base_groups(seq: SequenceData, name: str) -> SequenceData:
    items: List[FrameFeature] = []
    for frame in seq.features:
        parts: List[np.ndarray] = []
        masks: List[np.ndarray] = []
        groups: Dict[str, slice] = {}
        start = 0
        for group in BASE_GROUPS:
            if group not in frame.groups:
                continue
            sl = frame.groups[group]
            vector = frame.vector[sl].copy()
            mask = frame.mask[sl].copy()
            groups[group] = slice(start, start + vector.size)
            start += vector.size
            parts.append(vector)
            masks.append(mask)
        items.append(
            FrameFeature(
                frame_idx=frame.frame_idx,
                timestamp_sec=frame.timestamp_sec,
                vector=np.concatenate(parts).astype(np.float32),
                mask=np.concatenate(masks).astype(np.float32),
                groups=groups,
                presence=dict(frame.presence),
                frame_weight=float(frame.frame_weight),
                semantic_phase=float(frame.semantic_phase),
            )
        )
    return SequenceData(f"{seq.source}::{name}", seq.mode, seq.fps, seq.total_frames, items)


def _rebuild_derived_groups(seq: SequenceData, profile: Any, name: str) -> SequenceData:
    rebuilt = _sequence_with_relative_motion_features(_strip_to_base_groups(seq, name), profile)
    rebuilt.source = f"{seq.source}::{name}::rebuilt"
    return rebuilt


def _group_array(frame: FrameFeature, group: str) -> tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    if group not in frame.groups:
        return None, None
    sl = frame.groups[group]
    values = frame.vector[sl]
    masks = frame.mask[sl]
    if values.size % 3 != 0 or masks.size % 3 != 0:
        return None, None
    return values.reshape(-1, 3).copy(), masks.reshape(-1, 3).mean(axis=1) > 0.5


def _set_group(
    frame: FrameFeature,
    vector: np.ndarray,
    mask: np.ndarray,
    group: str,
    coords: np.ndarray,
    valid: np.ndarray,
) -> None:
    if group not in frame.groups:
        return
    sl = frame.groups[group]
    if vector[sl].size != coords.size:
        return
    vector[sl] = coords.reshape(-1)
    mask[sl] = np.repeat(valid.astype(np.float32), 3)
    shape_group = f"{group}_shape"
    if group not in HAND_GROUPS or shape_group not in frame.groups:
        return
    shape, shape_mask = _hand_shape_feature(coords, valid.astype(np.float32))
    shape_sl = frame.groups[shape_group]
    if vector[shape_sl].size == shape.size:
        vector[shape_sl] = shape.reshape(-1)
        mask[shape_sl] = shape_mask.reshape(-1)


def _visible_center(seq: SequenceData) -> np.ndarray:
    points: List[np.ndarray] = []
    for frame in seq.features:
        for group in COORD_GROUPS:
            coords, valid = _group_array(frame, group)
            if coords is None or valid is None or not valid.any():
                continue
            points.append(coords[valid, :2])
    if not points:
        return np.zeros(2, dtype=np.float32)
    return np.concatenate(points, axis=0).mean(axis=0).astype(np.float32)


def _aspect(seq: SequenceData, name: str, sx: float, sy: float) -> SequenceData:
    center = _visible_center(seq)
    items: List[FrameFeature] = []
    for frame in seq.features:
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        presence = dict(frame.presence)
        for group in COORD_GROUPS:
            coords, valid = _group_array(frame, group)
            if coords is None or valid is None or not valid.any():
                continue
            coords[valid, 0] = center[0] + (coords[valid, 0] - center[0]) * float(sx)
            coords[valid, 1] = center[1] + (coords[valid, 1] - center[1]) * float(sy)
            _set_group(frame, vector, mask, group, coords, valid)
            presence[group] = bool(valid.any())
        item = _clone_frame(frame, vector=vector, mask=mask)
        item.presence = presence
        items.append(item)
    return _clone_sequence(seq, name, items)


def _quantize(values: np.ndarray, step: Optional[float]) -> np.ndarray:
    if step is None or step <= 0:
        return values
    return (np.round(values / float(step)) * float(step)).astype(np.float32)


def _quantize_sequence(
    seq: SequenceData,
    name: str,
    *,
    groups: Sequence[str] = COORD_GROUPS,
    x_step: Optional[float] = None,
    y_step: Optional[float] = None,
    z_step: Optional[float] = None,
) -> SequenceData:
    items: List[FrameFeature] = []
    for frame in seq.features:
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        presence = dict(frame.presence)
        for group in groups:
            coords, valid = _group_array(frame, group)
            if coords is None or valid is None or not valid.any():
                continue
            if x_step is not None:
                coords[valid, 0] = _quantize(coords[valid, 0], x_step)
            if y_step is not None:
                coords[valid, 1] = _quantize(coords[valid, 1], y_step)
            if z_step is not None:
                coords[valid, 2] = _quantize(coords[valid, 2], z_step)
            _set_group(frame, vector, mask, group, coords, valid)
            presence[group] = bool(valid.any())
        item = _clone_frame(frame, vector=vector, mask=mask)
        item.presence = presence
        items.append(item)
    return _clone_sequence(seq, name, items)


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


def _rate_warp(seq: SequenceData, name: str, mode: str, ratio: Optional[float] = None) -> SequenceData:
    n = len(seq.features)
    if ratio is not None:
        return _pick_by_positions(seq, name, _linear_positions(n, max(2, int(round(n * float(ratio))))))
    values: List[float] = []
    for i in range(n):
        t = i / max(n - 1, 1)
        if mode == "mild_rate_jitter":
            src_t = t + 0.006 * math.sin(i * 1.73) + 0.004 * math.sin(i * 0.41)
        elif mode == "micro_rate_jitter":
            src_t = t + 0.008 * math.sin(i * 1.73) + 0.006 * math.sin(i * 0.41)
        elif mode == "core_slow":
            src_t = t + 0.045 * math.sin(2.0 * math.pi * t)
        elif mode == "front_fast_back_slow":
            src_t = 1.0 - (1.0 - t) ** 1.18
        else:
            src_t = t
        values.append(max(0.0, min(1.0, src_t)) * max(n - 1, 0))
    positions = np.maximum.accumulate(np.asarray(values, dtype=np.float32))
    if positions.size:
        positions[0] = 0.0
        positions[-1] = float(max(n - 1, 0))
    return _pick_by_positions(seq, name, positions)


def _freeze_burst(seq: SequenceData, name: str, start: int, length: int) -> SequenceData:
    items = list(seq.features)
    if not items:
        return _clone_sequence(seq, name, [])
    n = len(items)
    start = max(0, min(n - 1, int(start)))
    stop = min(n, start + max(1, int(length)))
    replacement = items[(start + stop - 1) // 2]
    selected = [replacement if start <= idx < stop else item for idx, item in enumerate(items)]
    return _clone_sequence(seq, name, selected)


def _sparse_freeze(seq: SequenceData, name: str, every: int) -> SequenceData:
    items = list(seq.features)
    selected: List[FrameFeature] = []
    for idx, item in enumerate(items):
        should_freeze = idx > 0 and idx < len(items) - 1 and idx % int(every) == 0
        selected.append(items[idx - 1] if should_freeze else item)
    return _clone_sequence(seq, name, selected)


def _center_start(length: int, burst_len: int) -> int:
    return max(0, int(length // 2) - int(burst_len // 2))


def _expand_hand_groups(groups: Sequence[str]) -> List[str]:
    expanded: List[str] = []
    for group in groups:
        for item in HAND_SHAPE_GROUPS.get(group, [group]):
            if item not in expanded:
                expanded.append(item)
    return expanded


def _mask_hand_burst(seq: SequenceData, name: str, groups: Sequence[str], start: int, length: int) -> SequenceData:
    expanded = _expand_hand_groups(groups)
    stop = min(len(seq.features), max(0, start) + max(0, length))
    items: List[FrameFeature] = []
    for idx, frame in enumerate(seq.features):
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        presence = dict(frame.presence)
        if start <= idx < stop:
            for group in expanded:
                if group not in frame.groups:
                    continue
                sl = frame.groups[group]
                vector[sl] = 0.0
                mask[sl] = 0.0
            if "left_hand" in expanded or "left_hand_shape" in expanded:
                presence["left_hand"] = False
            if "right_hand" in expanded or "right_hand_shape" in expanded:
                presence["right_hand"] = False
        item = _clone_frame(frame, vector=vector, mask=mask)
        item.presence = presence
        items.append(item)
    return _clone_sequence(seq, name, items)


SequenceTransform = Callable[[SequenceData], SequenceData]


def _spec(
    variant: str,
    kind: str,
    transforms: Sequence[SequenceTransform],
    rationale: str,
    *,
    min_score: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": kind,
        "transforms": list(transforms),
        "min_score": min_score,
        "rationale": rationale,
    }


def _with_names(seq: SequenceData, variant: str, transforms: Sequence[SequenceTransform]) -> SequenceData:
    current = seq
    for transform in transforms:
        current = transform(current)
    current.source = f"{seq.source}::{variant}"
    return current


def _variant_specs(word: str, min_score: float) -> List[Dict[str, Any]]:
    grid640 = (1.0 / 640.0, 1.0 / 480.0)
    grid320 = (1.0 / 320.0, 1.0 / 240.0)
    specs = [
        _spec(
            "combo_aspect_lowres_rate",
            "positive",
            [
                lambda seq: _aspect(seq, "aspect_x1.04_y0.98", 1.04, 0.98),
                lambda seq: _quantize_sequence(seq, "camera_grid_320x240", x_step=grid320[0], y_step=grid320[1], z_step=1.0 / 512.0),
                lambda seq: _rate_warp(seq, "mild_rate_jitter", "mild_rate_jitter"),
            ],
            "轻微宽高比失真、低分辨率坐标取整和轻微采样间隔不均叠加。",
            min_score=min_score,
        ),
        _spec(
            "combo_slow_sparse_freeze_lowres",
            "positive",
            [
                lambda seq: _rate_warp(seq, "global_slow_1.20x", "identity", ratio=1.20),
                lambda seq: _sparse_freeze(seq, "sparse_freeze_every_7th", 7),
                lambda seq: _quantize_sequence(seq, "camera_grid_640x480", x_step=grid640[0], y_step=grid640[1], z_step=1.0 / 1024.0),
            ],
            "动作稍慢、偶发微冻结和常见 640x480 网格取整同时出现。",
            min_score=min_score,
        ),
        _spec(
            "combo_fast_aspect_hand_quant",
            "positive",
            [
                lambda seq: _rate_warp(seq, "global_fast_0.85x", "identity", ratio=0.85),
                lambda seq: _aspect(seq, "aspect_x0.94_y1.06", 0.94, 1.06),
                lambda seq: _quantize_sequence(seq, "hand_xy_quantize_1_192", groups=HAND_GROUPS, x_step=1.0 / 192.0, y_step=1.0 / 192.0),
            ],
            "动作稍快、轻微反向宽高比失真和手部坐标量化同时出现。",
            min_score=min_score,
        ),
    ]
    if word == "花":
        specs.append(
            _spec(
                "combo_flower_short_dropout_stutter",
                "positive",
                [
                    lambda seq: _mask_hand_burst(seq, "right_hand_2f_gap", ["right_hand"], _center_start(len(seq.features), 2), 2),
                    lambda seq: _freeze_burst(seq, "freeze_mid_3f", _center_start(len(seq.features), 3), 3),
                    lambda seq: _aspect(seq, "aspect_x1.04_y0.97", 1.04, 0.97),
                ],
                "开花手 2 帧短检出空洞、3 帧中段冻结和轻微宽高比叠加。",
                min_score=min_score,
            )
        )
    elif word == "跳":
        specs.append(
            _spec(
                "combo_jump_short_dropout_stutter",
                "positive",
                [
                    lambda seq: _mask_hand_burst(seq, "right_hand_1f_gap", ["right_hand"], len(seq.features) // 2, 1),
                    lambda seq: _freeze_burst(seq, "freeze_mid_2f", _center_start(len(seq.features), 2), 2),
                    lambda seq: _aspect(seq, "aspect_x1.04_y0.97", 1.04, 0.97),
                ],
                "跳跃手 1 帧短检出空洞、2 帧中段冻结和轻微宽高比叠加。",
                min_score=min_score,
            )
        )
    specs.extend(
        [
            _spec(
                "diagnostic_quantized_micro_jitter",
                "diagnostic",
                [
                    lambda seq: _aspect(seq, "aspect_x1.04_y0.98", 1.04, 0.98),
                    lambda seq: _quantize_sequence(seq, "camera_grid_320x240", x_step=grid320[0], y_step=grid320[1], z_step=1.0 / 512.0),
                    lambda seq: _rate_warp(seq, "micro_rate_jitter", "micro_rate_jitter"),
                ],
                "320x240 量化与较强采样抖动叠加，`花` 会贴近阈值，只记录边界。",
            ),
            _spec(
                "diagnostic_strong_browser_stack",
                "diagnostic",
                [
                    lambda seq: _rate_warp(seq, "global_fast_0.55x", "identity", ratio=0.55),
                    lambda seq: _aspect(seq, "aspect_x1.25_y0.78", 1.25, 0.78),
                    lambda seq: _quantize_sequence(seq, "coarse_grid_160x120", x_step=1.0 / 160.0, y_step=1.0 / 120.0, z_step=1.0 / 256.0),
                    lambda seq: _freeze_burst(seq, "freeze_mid_20pct", _center_start(len(seq.features), max(1, round(len(seq.features) * 0.20))), max(1, round(len(seq.features) * 0.20))),
                ],
                "强组合压力：极快采样、强宽高比、粗网格和中段冻结，只记录边界。",
            ),
            _spec(
                "diagnostic_dropout_rate_stack",
                "diagnostic",
                [
                    lambda seq: _rate_warp(seq, "global_slow_1.80x", "identity", ratio=1.80),
                    lambda seq: _mask_hand_burst(seq, "right_hand_15pct_gap", ["right_hand"], _center_start(len(seq.features), max(1, round(len(seq.features) * 0.15))), max(1, round(len(seq.features) * 0.15))),
                    lambda seq: _quantize_sequence(seq, "hand_xy_quantize_1_64", groups=HAND_GROUPS, x_step=1.0 / 64.0, y_step=1.0 / 64.0),
                ],
                "较慢动作、核心手短空洞和粗手部坐标量化叠加，只记录边界。",
            ),
        ]
    )
    return specs


def _row_passed(row: Dict[str, Any]) -> bool:
    if row["kind"] != "positive":
        return True
    return float(row["score"]) >= float(row["min_score"])


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
    standard = _rebuild_derived_groups(loaded_standard, profile, "standard_base")
    base_query = _strip_to_base_groups(loaded_standard, "query_base")
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(word, min_score):
        query_base = _with_names(base_query, spec["variant"], spec["transforms"])
        query = _rebuild_derived_groups(query_base, profile, spec["variant"])
        result = run_pair(standard, query, semantic_profile=profile, enable_cross_check=False)
        score_scale = result.get("score_scale") or {}
        row = {
            "variant": spec["variant"],
            "kind": spec["kind"],
            "min_score": spec.get("min_score"),
            "rationale": spec["rationale"],
            "score": float(result["prototype_score"]),
            "dtw_distance": float(result["dtw_distance"]),
            "normalized_distance": float(result["normalized_distance"]),
            "query_length": len(query.features),
            "length_ratio": len(query.features) / max(len(standard.features), 1),
            "alignment_policy": result.get("alignment_policy"),
            "capture_quality": score_scale.get("capture_quality"),
            "semantic_floor": score_scale.get("semantic_floor"),
            "score_scale_reason": score_scale.get("reason"),
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
        "semantic_profile": _profile_summary(profile),
        "min_required_score": min_score,
        "gate_pass": all(bool(row["passed"]) for row in positive_rows),
        "weakest_positive_score": float(weakest_positive["score"]) if weakest_positive else None,
        "weakest_positive_variant": weakest_positive["variant"] if weakest_positive else "",
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
        "query_length",
        "standard_length",
        "length_ratio",
        "alignment_policy",
        "capture_quality_status",
        "capture_quality_reason",
        "semantic_floor_source",
        "semantic_floor_reason",
        "score_scale_reason",
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
                        "query_length": row.get("query_length"),
                        "standard_length": item.get("standard_length"),
                        "length_ratio": row.get("length_ratio"),
                        "alignment_policy": row.get("alignment_policy"),
                        "capture_quality_status": quality.get("status"),
                        "capture_quality_reason": quality.get("reason"),
                        "semantic_floor_source": floor.get("source"),
                        "semantic_floor_reason": floor.get("reason"),
                        "score_scale_reason": row.get("score_scale_reason"),
                        "rationale": row.get("rationale"),
                    }
                )


def _build_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# 花/跳组合网页扰动鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 总体：`{'PASS' if payload.get('passed') else 'FAIL'}`",
        f"- 模板根目录：`{payload['template_root']}`",
        f"- 语义权重：`{payload['semantic_profile_json']}`",
        f"- 门槛：正向组合扰动最低分 `>= {payload['min_score']}`；强组合扰动只记录诊断边界。",
        "- 口径：只读缓存 Holistic JSON，在骨架序列层组合轻微 aspect/坐标/速率/stutter/手部检出扰动，并重建 motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "",
        "## 汇总",
        "",
        "| 词条 | 状态 | 正向最低分 | 最弱正向组合 | 诊断最低分 | 最弱诊断组合 |",
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
            threshold = f">= {row.get('min_score')}" if row["kind"] == "positive" else "diagnostic"
            lines.append(
                f"| {row['variant']} | {row['kind']} | {'PASS' if row['passed'] else 'FAIL'} | "
                f"{_fmt(row['score'])} | {threshold} | {row.get('query_length')} / {_fmt(row.get('length_ratio'), 2)} | "
                f"{quality.get('status') or '-'}:{quality.get('reason') or '-'} | "
                f"{floor.get('source') or '-'}:{floor.get('reason') or '-'} | "
                f"{row['rationale']} |"
            )
        lines.append("")
    lines.extend(
        [
            "## 结论",
            "",
            "- 轻微组合扰动用于验证真实网页摄像头中多个小问题同时出现时，`花/跳` 仍能保持正常或边界以上得分。",
            "- 强组合扰动是采集质量边界，当前仅作为诊断记录，不能替代真实 marker 后网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def _default_output_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return DEFAULT_OUTPUT_BASE / f"flower_jump_composite_browser_robustness_gate_{stamp}"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run flower/jump composite browser robustness gate.")
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
        "claim_policy": "synthetic combined browser perturbation sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": _load_backend_status(args.backend_url, args.backend_timeout_sec),
        "feature_mode": args.feature_mode,
        "min_score": args.min_score,
        "results": results,
        "passed": all(bool(item.get("gate_pass")) for item in results),
    }
    json_path = output_dir / "flower_jump_composite_browser_robustness_gate.json"
    md_path = output_dir / "flower_jump_composite_browser_robustness_gate.md"
    csv_path = output_dir / "flower_jump_composite_browser_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    _write_rows_csv(csv_path, results)
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    print(f"composite browser gate: {'PASS' if payload['passed'] else 'FAIL'}")
    print(f"json: {json_path}")
    print(f"md: {md_path}")
    print(f"csv: {csv_path}")
    for item in results:
        print(
            f"- {item['word']}: gate={item['gate_pass']} "
            f"positive_min={_fmt(item['weakest_positive_score'])} "
            f"weakest={item['weakest_positive_variant']} "
            f"diagnostic_min={_fmt(item['weakest_diagnostic_score'])}"
        )
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

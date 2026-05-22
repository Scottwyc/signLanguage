#!/usr/bin/env python3
"""
手语 Holistic 序列打分 MVP。

这个脚本只读取已经落盘的 Holistic JSON，不重新运行 MediaPipe。
第一阶段目标是验证“标准序列 vs 查询序列”的离线打分链路：
- 特征抽取
- 坐标/尺度归一化
- DTW 时序对齐
- 分组误差统计
- 临时相似度分数与诊断输出

当前项目还没有真实用户视频流样本和人工评分标签，因此这里输出的是
prototype_score，不是已校准的正式评分。
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np


POSE_CORE_INDICES = [0, 11, 12, 13, 14, 15, 16, 23, 24]
FACE_CORE_INDICES = [33, 133, 159, 145, 362, 263, 386, 374, 61, 291, 13, 14]

GROUP_WEIGHTS = {
    "left_hand": 0.32,
    "right_hand": 0.32,
    "left_hand_shape": 0.00,
    "right_hand_shape": 0.00,
    "pose": 0.24,
    "face": 0.06,
    "missing": 0.06,
}

SCORE_SCALE = 0.12
DEFAULT_REPO_ROOT = Path("/data/WYC/signLanguage")
DEFAULT_SEMANTIC_PROFILE_JSON = DEFAULT_REPO_ROOT / "work/generated/scoring_semantic_profiles/sign_semantic_weights.json"
BASE_GROUPS = ["left_hand", "right_hand", "pose", "face"]
HAND_GROUPS = ["left_hand", "right_hand", "left_hand_shape", "right_hand_shape"]
HAND_SHAPE_GROUPS = ["left_hand_shape", "right_hand_shape"]
RELATIVE_MOTION_GROUPS = [
    "left_hand_motion",
    "right_hand_motion",
    "left_hand_shape_motion",
    "right_hand_shape_motion",
    "two_hand_relation",
    "two_hand_relation_motion",
]
FINGER_TIPS = [4, 8, 12, 16, 20]
FINGER_MCPS = [1, 5, 9, 13, 17]
FINGER_PIPS = [2, 6, 10, 14, 18]
FINGER_DIPS = [3, 7, 11, 15, 19]
SPREAD_PAIRS = [(4, 8), (8, 12), (12, 16), (16, 20), (8, 20)]
FINGER_NAMES = ["thumb", "index", "middle", "ring", "pinky"]
POSITIVE_VARIANTS = [
    "self",
    "subsample_even",
    "trim_start_20pct",
    "trim_end_20pct",
    "trim_both_10pct",
    "amplitude_0.85",
    "amplitude_1.15",
]
FAKE_VARIANTS = [
    "fake_reverse_time",
    "fake_shuffle_frames",
    "fake_static_hold",
    "fake_random_landmarks",
    "fake_random_walk",
]


@dataclass
class FrameFeature:
    frame_idx: int
    timestamp_sec: float
    vector: np.ndarray
    mask: np.ndarray
    groups: Dict[str, slice]
    presence: Dict[str, bool]
    frame_weight: float = 1.0
    semantic_phase: float = 0.0


@dataclass
class SequenceData:
    source: str
    mode: str
    fps: float
    total_frames: int
    features: List[FrameFeature]


@dataclass
class SemanticProfile:
    word: str
    version: str
    description: str
    group_weights: Dict[str, float]
    keypoint_weights: Dict[str, Dict[str, float]]
    focus_groups: List[str]
    allow_hand_swap: bool
    semantic_notes: List[str]
    semantic_dtw: Dict[str, Any]


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _default_semantic_profile(word: str = "generic") -> SemanticProfile:
    return SemanticProfile(
        word=word,
        version="builtin-default",
        description="默认均衡手部优先 profile；未命中文本语义配置时使用。",
        group_weights=dict(GROUP_WEIGHTS),
        keypoint_weights={},
        focus_groups=["left_hand", "right_hand"],
        allow_hand_swap=True,
        semantic_notes=["no_word_specific_profile"],
        semantic_dtw={},
    )


def _infer_word_from_source(source: str) -> str:
    path = Path(source.split("::", 1)[0])
    names = [path.parent.name, path.stem]
    for name in names:
        if not name:
            continue
        cleaned = name.replace("_holistic_results", "")
        cleaned = cleaned.replace("_results", "")
        if cleaned:
            return cleaned
    return "generic"


def _normalize_group_weights(raw: Dict[str, Any]) -> Dict[str, float]:
    merged = dict(GROUP_WEIGHTS)
    for key, value in raw.items():
        try:
            merged[key] = max(0.0, float(value))
        except (TypeError, ValueError):
            continue
    missing = max(0.0, min(float(merged.get("missing", GROUP_WEIGHTS["missing"])), 0.35))
    groups = [key for key in merged if key != "missing" and merged.get(key, 0.0) > 0]
    total = sum(float(merged[key]) for key in groups)
    if total <= 1e-8:
        return dict(GROUP_WEIGHTS)
    scale = (1.0 - missing) / total
    normalized = {key: float(merged.get(key, 0.0)) * scale for key in merged if key != "missing"}
    normalized["missing"] = missing
    return normalized


def load_semantic_profile(
    word: str,
    profile_json: Path = DEFAULT_SEMANTIC_PROFILE_JSON,
    disabled: bool = False,
) -> SemanticProfile:
    if disabled:
        return _default_semantic_profile(word)
    if not profile_json.exists():
        return _default_semantic_profile(word)
    payload = _load_json(profile_json)
    profiles = payload.get("profiles") or {}
    raw = profiles.get(word)
    if raw is None and "（" in word:
        raw = profiles.get(word.split("（", 1)[0])
    if raw is None:
        raw = profiles.get("generic")
    if raw is None:
        return _default_semantic_profile(word)
    return SemanticProfile(
        word=str(raw.get("word") or word),
        version=str(payload.get("version") or raw.get("version") or "semantic-profile"),
        description=str(raw.get("description") or ""),
        group_weights=_normalize_group_weights(raw.get("group_weights") or {}),
        keypoint_weights=dict(raw.get("keypoint_weights") or {}),
        focus_groups=list(raw.get("focus_groups") or ["left_hand", "right_hand"]),
        allow_hand_swap=bool(raw.get("allow_hand_swap", True)),
        semantic_notes=list(raw.get("semantic_notes") or []),
        semantic_dtw=dict(raw.get("semantic_dtw") or {}),
    )


def _profile_summary(profile: SemanticProfile) -> Dict[str, Any]:
    return {
        "word": profile.word,
        "version": profile.version,
        "description": profile.description,
        "group_weights": profile.group_weights,
        "keypoint_weights": profile.keypoint_weights,
        "focus_groups": profile.focus_groups,
        "allow_hand_swap": profile.allow_hand_swap,
        "semantic_notes": profile.semantic_notes,
        "semantic_dtw": profile.semantic_dtw,
    }


def _records_from_payload(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    if isinstance(payload.get("records"), list):
        return list(payload["records"])
    if isinstance(payload.get("frames"), list):
        return [{"frame_idx": row.get("frame_idx"), "timestamp_sec": row.get("timestamp_sec"), "row": row} for row in payload["frames"]]
    if isinstance(payload.get("rows"), list):
        return [{"frame_idx": row.get("frame_idx"), "timestamp_sec": row.get("timestamp_sec"), "row": row} for row in payload["rows"]]
    raise RuntimeError("不支持的 Holistic JSON 格式：缺少 records / frames / rows")


def _has_landmark_records(records: Sequence[Dict[str, Any]]) -> bool:
    for item in records:
        result_data = item.get("result_data")
        if not isinstance(result_data, dict):
            return False
        if result_data.get("pose_landmarks") or result_data.get("left_hand_landmarks") or result_data.get("right_hand_landmarks"):
            return True
    return False


def _landmark_array(
    items: Sequence[Dict[str, Any]],
    indices: Optional[Sequence[int]] = None,
    expected_count: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    if indices is not None:
        selected = list(indices)
    elif expected_count is not None:
        selected = list(range(expected_count))
    else:
        selected = list(range(len(items)))
    coords: List[List[float]] = []
    mask: List[float] = []
    for idx in selected:
        if 0 <= idx < len(items):
            lm = items[idx]
            coords.append([float(lm.get("x", 0.0)), float(lm.get("y", 0.0)), float(lm.get("z", 0.0))])
            mask.append(1.0)
        else:
            coords.append([0.0, 0.0, 0.0])
            mask.append(0.0)
    return np.asarray(coords, dtype=np.float32), np.asarray(mask, dtype=np.float32)


def _normalization_from_pose(pose: np.ndarray, pose_mask: np.ndarray) -> Tuple[np.ndarray, float]:
    if pose.shape[0] >= 3 and pose_mask[1] > 0 and pose_mask[2] > 0:
        center = (pose[1] + pose[2]) / 2.0
        scale = float(np.linalg.norm(pose[1, :2] - pose[2, :2]))
        return center, max(scale, 1e-3)
    valid = pose[pose_mask > 0]
    if len(valid) > 0:
        xy = valid[:, :2]
        center = np.asarray([float(xy[:, 0].mean()), float(xy[:, 1].mean()), 0.0], dtype=np.float32)
        span = np.ptp(xy, axis=0)
        return center, max(float(np.linalg.norm(span)), 1e-3)
    return np.zeros(3, dtype=np.float32), 1.0


def _dist(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a[:3] - b[:3]))


def _angle_straightness(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    left = a[:3] - b[:3]
    right = c[:3] - b[:3]
    denom = float(np.linalg.norm(left) * np.linalg.norm(right))
    if denom <= 1e-8:
        return 0.0
    cos_value = float(np.dot(left, right) / denom)
    cos_value = max(-1.0, min(1.0, cos_value))
    return (1.0 - cos_value) / 2.0


def _hand_shape_feature(hand: np.ndarray, hand_mask: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    values: List[float] = []
    masks: List[float] = []

    wrist_ok = hand_mask[0] > 0 if len(hand_mask) > 0 else False
    palm_refs: List[float] = []
    for idx in [5, 9, 13, 17]:
        if wrist_ok and idx < len(hand_mask) and hand_mask[idx] > 0:
            palm_refs.append(_dist(hand[idx], hand[0]))
    if hand_mask[5] > 0 and hand_mask[17] > 0:
        palm_refs.append(_dist(hand[5], hand[17]))
    palm_scale = max(float(np.mean(palm_refs)) if palm_refs else 0.0, 1e-3)

    def append_distance(a_idx: int, b_idx: int) -> None:
        ok = a_idx < len(hand_mask) and b_idx < len(hand_mask) and hand_mask[a_idx] > 0 and hand_mask[b_idx] > 0
        values.append((_dist(hand[a_idx], hand[b_idx]) / palm_scale) if ok else 0.0)
        masks.append(1.0 if ok else 0.0)

    for tip in FINGER_TIPS:
        append_distance(0, tip)
    for a_idx, b_idx in SPREAD_PAIRS:
        append_distance(a_idx, b_idx)
    for mcp, tip in zip(FINGER_MCPS, FINGER_TIPS):
        append_distance(mcp, tip)
    for mcp, pip, tip in zip(FINGER_MCPS, FINGER_PIPS, FINGER_TIPS):
        ok = hand_mask[mcp] > 0 and hand_mask[pip] > 0 and hand_mask[tip] > 0
        values.append(_angle_straightness(hand[mcp], hand[pip], hand[tip]) if ok else 0.0)
        masks.append(1.0 if ok else 0.0)

    return np.asarray(values, dtype=np.float32), np.asarray(masks, dtype=np.float32)


def _append_group(parts: List[np.ndarray], masks: List[np.ndarray], groups: Dict[str, slice], name: str, arr: np.ndarray, mask: np.ndarray) -> None:
    start = sum(part.size for part in parts)
    flat = arr.reshape(-1)
    parts.append(flat)
    repeat = max(1, int(flat.size / max(int(mask.size), 1)))
    masks.append(np.repeat(mask, repeat))
    groups[name] = slice(start, start + flat.size)


def _landmark_feature(record: Dict[str, Any], fps: float) -> FrameFeature:
    result_data = record.get("result_data") or {}
    row = record.get("row") or {}
    pose, pose_mask = _landmark_array(result_data.get("pose_landmarks") or [], POSE_CORE_INDICES)
    left, left_mask = _landmark_array(result_data.get("left_hand_landmarks") or [], expected_count=21)
    right, right_mask = _landmark_array(result_data.get("right_hand_landmarks") or [], expected_count=21)
    face, face_mask = _landmark_array(result_data.get("face_landmarks") or [], FACE_CORE_INDICES)

    center, scale = _normalization_from_pose(pose, pose_mask)

    def norm(arr: np.ndarray) -> np.ndarray:
        if arr.size == 0:
            return arr
        out = arr.copy()
        out[:, :3] = (out[:, :3] - center) / scale
        return out

    parts: List[np.ndarray] = []
    masks: List[np.ndarray] = []
    groups: Dict[str, slice] = {}
    _append_group(parts, masks, groups, "pose", norm(pose), pose_mask)
    _append_group(parts, masks, groups, "left_hand", norm(left), left_mask)
    _append_group(parts, masks, groups, "right_hand", norm(right), right_mask)
    left_shape, left_shape_mask = _hand_shape_feature(norm(left), left_mask)
    right_shape, right_shape_mask = _hand_shape_feature(norm(right), right_mask)
    _append_group(parts, masks, groups, "left_hand_shape", left_shape.reshape(-1, 1), left_shape_mask)
    _append_group(parts, masks, groups, "right_hand_shape", right_shape.reshape(-1, 1), right_shape_mask)
    _append_group(parts, masks, groups, "face", norm(face), face_mask)

    frame_idx = int(record.get("frame_idx") if record.get("frame_idx") is not None else row.get("frame_idx", 0))
    timestamp = float(record.get("timestamp_sec") if record.get("timestamp_sec") is not None else frame_idx / max(fps, 1e-6))
    raw_weight = record.get("frame_weight", row.get("frame_weight", 1.0))
    try:
        frame_weight = max(0.05, float(raw_weight))
    except (TypeError, ValueError):
        frame_weight = 1.0
    return FrameFeature(
        frame_idx=frame_idx,
        timestamp_sec=timestamp,
        vector=np.concatenate(parts).astype(np.float32),
        mask=np.concatenate(masks).astype(np.float32),
        groups=groups,
        presence={
            "pose": bool(pose_mask.sum() > 0),
            "left_hand": bool(left_mask.sum() > 0),
            "right_hand": bool(right_mask.sum() > 0),
            "face": bool(face_mask.sum() > 0),
        },
        frame_weight=frame_weight,
    )


def _bbox_to_features(row: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray, Dict[str, slice], Dict[str, bool]]:
    pose_box = (row.get("pose") or {}).get("bbox") or {}
    center_x = (float(pose_box.get("x_min", 0.0)) + float(pose_box.get("x_max", 1.0))) / 2.0
    center_y = (float(pose_box.get("y_min", 0.0)) + float(pose_box.get("y_max", 1.0))) / 2.0
    span_x = max(float(pose_box.get("x_max", 1.0)) - float(pose_box.get("x_min", 0.0)), 1.0)
    span_y = max(float(pose_box.get("y_max", 1.0)) - float(pose_box.get("y_min", 0.0)), 1.0)
    scale = max(math.hypot(span_x, span_y), 1.0)

    parts: List[np.ndarray] = []
    masks: List[np.ndarray] = []
    groups: Dict[str, slice] = {}
    presence: Dict[str, bool] = {}
    for group in ["pose", "left_hand", "right_hand", "face"]:
        box = (row.get(group) or {}).get("bbox")
        present = bool(row.get(f"{group}_present")) and isinstance(box, dict)
        presence[group] = present
        if present:
            x_min = (float(box.get("x_min", center_x)) - center_x) / scale
            x_max = (float(box.get("x_max", center_x)) - center_x) / scale
            y_min = (float(box.get("y_min", center_y)) - center_y) / scale
            y_max = (float(box.get("y_max", center_y)) - center_y) / scale
            vis = float(box.get("visibility_mean", row.get(group, {}).get("visibility_mean", 0.0)) or 0.0)
            arr = np.asarray([x_min, x_max, y_min, y_max, vis], dtype=np.float32)
            mask = np.ones(5, dtype=np.float32)
        else:
            arr = np.zeros(5, dtype=np.float32)
            mask = np.zeros(5, dtype=np.float32)
        start = sum(part.size for part in parts)
        parts.append(arr)
        masks.append(mask)
        groups[group] = slice(start, start + arr.size)

    return np.concatenate(parts), np.concatenate(masks), groups, presence


def _bbox_feature(record: Dict[str, Any], fps: float) -> FrameFeature:
    row = record.get("row") or record
    vector, mask, groups, presence = _bbox_to_features(row)
    frame_idx = int(row.get("frame_idx", record.get("frame_idx", 0)))
    timestamp = float(row.get("timestamp_sec", record.get("timestamp_sec", frame_idx / max(fps, 1e-6))))
    raw_weight = record.get("frame_weight", row.get("frame_weight", 1.0))
    try:
        frame_weight = max(0.05, float(raw_weight))
    except (TypeError, ValueError):
        frame_weight = 1.0
    return FrameFeature(frame_idx, timestamp, vector.astype(np.float32), mask.astype(np.float32), groups, presence, frame_weight)


def _apply_sidecar_frame_weights(path: Path, features: List[FrameFeature]) -> None:
    manifest_path = path.parent / "semantic_frame_weights.json"
    if not manifest_path.exists():
        return
    try:
        payload = _load_json(manifest_path)
    except Exception:
        return
    rows = payload.get("frame_weights") or []
    weight_by_idx: Dict[int, float] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            frame_idx = int(row.get("frame_idx"))
            weight = float(row.get("semantic_frame_weight", row.get("frame_weight", row.get("weight", 1.0))))
        except (TypeError, ValueError):
            continue
        weight_by_idx[frame_idx] = max(0.05, weight)
    if not weight_by_idx:
        return
    for feature in features:
        if feature.frame_idx in weight_by_idx:
            feature.frame_weight = weight_by_idx[feature.frame_idx]


def load_sequence(
    path: Path,
    requested_mode: str = "auto",
    force_bbox: bool = False,
    apply_sidecar_weights: bool = True,
) -> SequenceData:
    payload = _load_json(path)
    records = _records_from_payload(payload)
    fps = float(payload.get("fps") or payload.get("meta", {}).get("fps") or 25.0)
    total_frames = int(payload.get("total_frames") or payload.get("meta", {}).get("frame_count") or len(records))

    mode = requested_mode
    if requested_mode == "auto":
        mode = "landmark" if _has_landmark_records(records) and not force_bbox else "bbox"
    if force_bbox:
        mode = "bbox"

    if mode == "landmark":
        features = [_landmark_feature(record, fps) for record in records]
    elif mode == "bbox":
        features = [_bbox_feature(record, fps) for record in records]
    else:
        raise RuntimeError(f"未知特征模式：{mode}")

    features = sorted(features, key=lambda item: item.frame_idx)
    if apply_sidecar_weights:
        _apply_sidecar_frame_weights(path, features)
    if not features:
        raise RuntimeError(f"序列为空：{path}")
    return SequenceData(str(path), mode, fps, total_frames, features)


def _presence_ratio(seq: SequenceData) -> Dict[str, float]:
    result: Dict[str, float] = {}
    for group in ["pose", "left_hand", "right_hand", "face"]:
        result[group] = sum(1 for f in seq.features if f.presence.get(group)) / len(seq.features)
    return result


def _clone_frame(feature: FrameFeature, vector: Optional[np.ndarray] = None, mask: Optional[np.ndarray] = None) -> FrameFeature:
    return FrameFeature(
        frame_idx=feature.frame_idx,
        timestamp_sec=feature.timestamp_sec,
        vector=np.asarray(vector if vector is not None else feature.vector, dtype=np.float32).copy(),
        mask=np.asarray(mask if mask is not None else feature.mask, dtype=np.float32).copy(),
        groups=dict(feature.groups),
        presence=dict(feature.presence),
        frame_weight=float(feature.frame_weight),
        semantic_phase=float(feature.semantic_phase),
    )


def _clone_sequence(seq: SequenceData, source_suffix: str, features: Sequence[FrameFeature]) -> SequenceData:
    cloned: List[FrameFeature] = []
    for idx, feature in enumerate(features):
        item = _clone_frame(feature)
        item.frame_idx = idx
        item.timestamp_sec = idx / max(seq.fps, 1e-6)
        cloned.append(item)
    return SequenceData(f"{seq.source}::{source_suffix}", seq.mode, seq.fps, seq.total_frames, cloned)


def _append_feature_group(feature: FrameFeature, name: str, values: np.ndarray, mask: np.ndarray) -> FrameFeature:
    start = int(feature.vector.size)
    flat = np.asarray(values, dtype=np.float32).reshape(-1)
    flat_mask = np.asarray(mask, dtype=np.float32).reshape(-1)
    vector = np.concatenate([feature.vector, flat]).astype(np.float32)
    full_mask = np.concatenate([feature.mask, flat_mask]).astype(np.float32)
    groups = dict(feature.groups)
    groups[name] = slice(start, start + int(flat.size))
    return FrameFeature(
        frame_idx=feature.frame_idx,
        timestamp_sec=feature.timestamp_sec,
        vector=vector,
        mask=full_mask,
        groups=groups,
        presence=dict(feature.presence),
        frame_weight=float(feature.frame_weight),
        semantic_phase=float(feature.semantic_phase),
    )


def _directional_motion_feature(motion: np.ndarray, mask: np.ndarray) -> np.ndarray:
    valid = np.asarray(mask, dtype=np.float32) > 0
    out = np.asarray(motion, dtype=np.float32).copy()
    if not valid.any():
        return out
    norm = float(np.sqrt(np.mean(out[valid] ** 2)))
    if norm <= 1e-8:
        return out
    # Compare motion direction/trend more than frame-density-dependent magnitude.
    return (out / norm).astype(np.float32)


def _two_hand_relation_feature(feature: FrameFeature) -> Tuple[np.ndarray, np.ndarray]:
    relation = np.zeros(8, dtype=np.float32)
    relation_mask = np.zeros(8, dtype=np.float32)
    if "left_hand" not in feature.groups or "right_hand" not in feature.groups:
        return relation, relation_mask

    left_sl = feature.groups["left_hand"]
    right_sl = feature.groups["right_hand"]
    left = feature.vector[left_sl].reshape(-1, 3)
    right = feature.vector[right_sl].reshape(-1, 3)
    left_mask = feature.mask[left_sl].reshape(-1, 3).mean(axis=1) > 0.5
    right_mask = feature.mask[right_sl].reshape(-1, 3).mean(axis=1) > 0.5

    left_ground_indices = [0, 5, 9, 13, 17]
    right_tip_indices = [8, 12]
    right_base_indices = [5, 9]
    if not all(left_mask[idx] for idx in left_ground_indices):
        return relation, relation_mask
    if not all(right_mask[idx] for idx in right_tip_indices + right_base_indices):
        return relation, relation_mask

    left_ground = left[left_ground_indices, :2].mean(axis=0)
    right_tips = right[right_tip_indices, :2].mean(axis=0)
    right_bases = right[right_base_indices, :2].mean(axis=0)
    tip_rel = right_tips - left_ground
    base_rel = right_bases - left_ground
    finger_axis = right_tips - right_bases
    relation_values = np.asarray(
        [
            tip_rel[0],
            tip_rel[1],
            base_rel[0],
            base_rel[1],
            finger_axis[0],
            finger_axis[1],
            float(np.linalg.norm(tip_rel)),
            float(np.linalg.norm(base_rel)),
        ],
        dtype=np.float32,
    )
    return relation_values, np.ones(8, dtype=np.float32)


def _sequence_with_relative_motion_features(seq: SequenceData, profile: Optional[SemanticProfile]) -> SequenceData:
    config = _semantic_dtw_config(profile)
    if not seq.features:
        return seq

    features: List[FrameFeature] = []
    prev_relation: Optional[np.ndarray] = None
    prev_relation_valid = False
    base_groups = ["left_hand", "right_hand", "left_hand_shape", "right_hand_shape"]
    motion_enabled = bool(config.get("relative_motion_enabled", True))

    for idx, feature in enumerate(seq.features):
        item = _clone_frame(feature)
        prev = seq.features[idx - 1] if idx > 0 else None
        if motion_enabled:
            for group in base_groups:
                if group not in item.groups:
                    continue
                sl = item.groups[group]
                curr_values = item.vector[sl]
                curr_mask = item.mask[sl]
                if prev is not None and group in prev.groups:
                    prev_sl = prev.groups[group]
                    prev_values = prev.vector[prev_sl]
                    prev_mask = prev.mask[prev_sl]
                    if curr_values.shape == prev_values.shape:
                        motion_mask = ((curr_mask > 0) & (prev_mask > 0)).astype(np.float32)
                        motion = _directional_motion_feature((curr_values - prev_values) * motion_mask, motion_mask)
                    else:
                        motion = np.zeros_like(curr_values, dtype=np.float32)
                        motion_mask = np.zeros_like(curr_mask, dtype=np.float32)
                else:
                    motion = np.zeros_like(curr_values, dtype=np.float32)
                    motion_mask = np.zeros_like(curr_mask, dtype=np.float32)
                item = _append_feature_group(item, f"{group}_motion", motion, motion_mask)

        relation, relation_mask = _two_hand_relation_feature(item)
        relation_valid = bool(relation_mask.mean() > 0.5)
        item = _append_feature_group(item, "two_hand_relation", relation, relation_mask)
        if motion_enabled and prev_relation is not None and prev_relation_valid and relation_valid:
            relation_motion_mask = np.ones(3, dtype=np.float32)
            relation_motion = _directional_motion_feature((relation[:3] - prev_relation[:3]), relation_motion_mask)
            item = _append_feature_group(item, "two_hand_relation_motion", relation_motion, relation_motion_mask)
        elif motion_enabled:
            relation_motion = np.zeros(3, dtype=np.float32)
            relation_motion_mask = np.zeros(3, dtype=np.float32)
            item = _append_feature_group(item, "two_hand_relation_motion", relation_motion, relation_motion_mask)
        prev_relation = relation
        prev_relation_valid = relation_valid
        features.append(item)

    return SequenceData(seq.source, seq.mode, seq.fps, seq.total_frames, features)


def _visible_matrix(seq: SequenceData) -> Tuple[np.ndarray, np.ndarray]:
    vectors = np.stack([feature.vector for feature in seq.features], axis=0)
    masks = np.stack([feature.mask for feature in seq.features], axis=0)
    return vectors, masks


def _sequence_groups(seq: SequenceData) -> List[str]:
    if not seq.features:
        return []
    names = list(seq.features[0].groups.keys())
    ordered = [
        "left_hand",
        "right_hand",
        "left_hand_shape",
        "right_hand_shape",
        "left_hand_motion",
        "right_hand_motion",
        "left_hand_shape_motion",
        "right_hand_shape_motion",
        "two_hand_relation",
        "two_hand_relation_motion",
        "pose",
        "face",
    ]
    return [group for group in ordered if group in names]


def _sequence_motion_by_group(seq: SequenceData) -> Dict[str, float]:
    if len(seq.features) < 2:
        return {group: 0.0 for group in _sequence_groups(seq)}
    result: Dict[str, float] = {}
    for group in _sequence_groups(seq):
        values: List[float] = []
        for prev, curr in zip(seq.features[:-1], seq.features[1:]):
            sl = prev.groups[group]
            both = (prev.mask[sl] > 0) & (curr.mask[sl] > 0)
            if both.any():
                values.append(float(np.sqrt(np.mean((curr.vector[sl][both] - prev.vector[sl][both]) ** 2))))
        result[group] = float(np.mean(values)) if values else 0.0
    return result


def _sequence_roughness_by_group(seq: SequenceData) -> Dict[str, float]:
    if len(seq.features) < 3:
        return {group: 0.0 for group in _sequence_groups(seq)}
    result: Dict[str, float] = {}
    for group in _sequence_groups(seq):
        values: List[float] = []
        for a, b, c in zip(seq.features[:-2], seq.features[1:-1], seq.features[2:]):
            sl = a.groups[group]
            both = (a.mask[sl] > 0) & (b.mask[sl] > 0) & (c.mask[sl] > 0)
            if both.any():
                accel = c.vector[sl][both] - 2.0 * b.vector[sl][both] + a.vector[sl][both]
                values.append(float(np.sqrt(np.mean(accel ** 2))))
        result[group] = float(np.mean(values)) if values else 0.0
    return result


def _safe_log_ratio(a: float, b: float, eps: float = 1e-4) -> float:
    return abs(math.log((a + eps) / (b + eps)))


def _profile_group_weights(profile: Optional[SemanticProfile], groups: Sequence[str]) -> Dict[str, float]:
    raw = profile.group_weights if profile else GROUP_WEIGHTS
    missing = max(0.0, min(float(raw.get("missing", GROUP_WEIGHTS["missing"])), 0.35))
    present = [group for group in groups if group != "missing"]
    if not present:
        return {"missing": missing}

    semantic_dtw = dict(profile.semantic_dtw) if profile is not None else {}
    relative_motion_weight = max(0.0, min(float(semantic_dtw.get("relative_motion_weight", 0.28)), 1.0))
    two_hand_relation_weight = max(0.0, min(float(semantic_dtw.get("two_hand_relation_weight", 0.22)), 1.0))

    def raw_group_weight(group: str) -> float:
        if group in raw:
            return max(0.0, float(raw.get(group, 0.0)))
        if group.endswith("_motion"):
            base = group[: -len("_motion")]
            if base in raw:
                return relative_motion_weight * max(0.0, float(raw.get(base, 0.0)))
        if group == "two_hand_relation":
            left = max(0.0, float(raw.get("left_hand", 0.0))) + max(0.0, float(raw.get("left_hand_shape", 0.0)))
            right = max(0.0, float(raw.get("right_hand", 0.0))) + max(0.0, float(raw.get("right_hand_shape", 0.0)))
            return two_hand_relation_weight * min(left, right)
        return 0.0

    total = sum(raw_group_weight(group) for group in present)
    if total <= 1e-8:
        return _profile_group_weights(_default_semantic_profile(), groups)
    scale = (1.0 - missing) / total
    weights = {group: raw_group_weight(group) * scale for group in present}
    weights["missing"] = missing
    return weights


def _required_presence_groups(profile: Optional[SemanticProfile]) -> set[str]:
    if profile is None:
        return set()
    raw = profile.semantic_dtw.get("required_presence_groups") or []
    if not isinstance(raw, list):
        return set()
    return {str(item) for item in raw}


def _semantic_core_hand_presence(seq: SequenceData, profile: Optional[SemanticProfile]) -> float:
    presence = _presence_ratio(seq)
    left = float(presence.get("left_hand", 0.0))
    right = float(presence.get("right_hand", 0.0))
    required = _required_presence_groups(profile)
    focus = set(profile.focus_groups) if profile is not None else set()
    if "two_hand_relation" in required or "two_hand_relation" in focus or {"left_hand", "right_hand"}.issubset(required):
        return min(left, right)
    return max(left, right)


def _group_missing_distance_weight(profile: Optional[SemanticProfile], group: str) -> float:
    config = _semantic_dtw_config(profile)
    base = float(config["group_missing_distance_weight"])
    focus = float(config["focus_missing_distance_weight"])
    relation = float(config["relation_missing_distance_weight"])
    required = _required_presence_groups(profile)
    if group == "two_hand_relation":
        return relation
    if group == "two_hand_relation_motion":
        return 0.5 * relation
    if group in required or (profile is not None and group in profile.focus_groups):
        return max(base, focus)
    if group.endswith("_motion"):
        return 0.65 * base
    if group in {"pose", "face"}:
        return min(base, 0.06)
    return base


def _sequence_delta_by_group(seq: SequenceData, group: str) -> Tuple[np.ndarray, np.ndarray]:
    if not seq.features or group not in seq.features[0].groups:
        return np.zeros(0, dtype=np.float32), np.zeros(0, dtype=np.float32)
    valid_indices: List[int] = []
    for idx, item in enumerate(seq.features):
        sl = item.groups[group]
        if float(item.mask[sl].mean()) >= 0.35:
            valid_indices.append(idx)
    if not valid_indices:
        return np.zeros(0, dtype=np.float32), np.zeros(0, dtype=np.float32)
    window = max(1, min(3, int(round(len(valid_indices) * 0.20))))
    start_set = set(valid_indices[:window])
    end_set = set(valid_indices[-window:])
    start_items = [seq.features[idx] for idx in valid_indices if idx in start_set]
    end_items = [seq.features[idx] for idx in valid_indices if idx in end_set]

    def masked_mean(items: Sequence[FrameFeature]) -> Tuple[np.ndarray, np.ndarray]:
        sl = items[0].groups[group]
        vectors = np.stack([item.vector[sl] for item in items], axis=0)
        masks = np.stack([item.mask[sl] for item in items], axis=0)
        denom = np.maximum(masks.sum(axis=0), 1e-6)
        mean = (vectors * masks).sum(axis=0) / denom
        valid = (masks.sum(axis=0) > 0).astype(np.float32)
        return mean.astype(np.float32), valid

    start_mean, start_mask = masked_mean(start_items)
    end_mean, end_mask = masked_mean(end_items)
    valid = (start_mask > 0) & (end_mask > 0)
    return (end_mean - start_mean).astype(np.float32), valid.astype(np.float32)


def _semantic_delta_penalty(standard: SequenceData, query: SequenceData, profile: Optional[SemanticProfile]) -> Tuple[float, Dict[str, float]]:
    if profile is None:
        return 0.0, {}
    focus = [group for group in profile.focus_groups if standard.features and group in standard.features[0].groups]
    if not focus:
        return 0.0, {}
    weights = _profile_group_weights(profile, focus)
    details: Dict[str, float] = {}
    weighted = 0.0
    weight_sum = 0.0
    for group in focus:
        std_delta, std_mask = _sequence_delta_by_group(standard, group)
        qry_delta, qry_mask = _sequence_delta_by_group(query, group)
        if std_delta.size == 0 or qry_delta.size == 0:
            continue
        both = (std_mask > 0) & (qry_mask > 0)
        if not both.any():
            value = 1.0
            details[group] = value
            group_weight = float(weights.get(group, 0.0))
            weighted += group_weight * value
            weight_sum += group_weight
            continue
        rmse = float(np.sqrt(np.mean((std_delta[both] - qry_delta[both]) ** 2)))
        std_vec = std_delta[both]
        qry_vec = qry_delta[both]
        denom = float(np.linalg.norm(std_vec) * np.linalg.norm(qry_vec))
        if denom <= 1e-8:
            direction_error = 0.0
        else:
            cosine = max(-1.0, min(1.0, float(np.dot(std_vec, qry_vec) / denom)))
            direction_error = max(0.0, (0.25 - cosine) / 1.25)
        value = 0.35 * rmse + 0.65 * direction_error
        details[group] = value
        group_weight = float(weights.get(group, 0.0))
        weighted += group_weight * value
        weight_sum += group_weight
    if weight_sum <= 1e-8:
        return 0.0, details
    return 0.14 * (weighted / weight_sum), details


def _hand_dynamic_scale(profile: Optional[SemanticProfile], groups: Sequence[str]) -> float:
    if profile is None:
        return 1.0
    weights = _profile_group_weights(profile, groups)
    hand_mass = sum(float(weights.get(group, 0.0)) for group in HAND_GROUPS)
    non_hand_mass = float(weights.get("pose", 0.0)) + float(weights.get("face", 0.0))
    if hand_mass >= 0.85 and non_hand_mass <= 0.03:
        return 1.55
    if hand_mass >= 0.75 and non_hand_mass <= 0.06:
        return 1.25
    return 1.0


def _semantic_dtw_config(profile: Optional[SemanticProfile]) -> Dict[str, Any]:
    raw = dict(profile.semantic_dtw) if profile is not None else {}
    enabled = bool(raw.get("enabled", True))
    local_phase_weight = float(raw.get("local_phase_weight", 0.018))
    anchor_penalty_weight = float(raw.get("anchor_penalty_weight", 0.10))
    hand_global_position_weight = float(raw.get("hand_global_position_weight", 0.25))
    pose_robust_hand_position = bool(raw.get("pose_robust_hand_position", True))
    relative_motion_enabled = bool(raw.get("relative_motion_enabled", True))
    relative_motion_weight = float(raw.get("relative_motion_weight", 0.28))
    two_hand_relation_weight = float(raw.get("two_hand_relation_weight", 0.22))
    group_missing_distance_weight = float(raw.get("group_missing_distance_weight", 0.0))
    focus_missing_distance_weight = float(raw.get("focus_missing_distance_weight", 0.0))
    relation_missing_distance_weight = float(raw.get("relation_missing_distance_weight", 0.0))
    required_presence_weight = float(raw.get("required_presence_weight", 0.08))
    visible_core_tolerance_cap = float(raw.get("visible_core_tolerance_cap", 0.034))
    core_visible_score_scale = float(raw.get("core_visible_score_scale", SCORE_SCALE))
    core_visible_dtw_threshold = float(raw.get("core_visible_dtw_threshold", 0.045))
    core_visible_presence_threshold = float(raw.get("core_visible_presence_threshold", 0.65))
    core_visible_max_normalized_distance = float(raw.get("core_visible_max_normalized_distance", 0.080))
    jump_relation_semantic_floor_enabled = bool(raw.get("jump_relation_semantic_floor_enabled", False))
    jump_relation_semantic_max_score = float(raw.get("jump_relation_semantic_max_score", 0.0))
    jump_relation_semantic_min_presence = float(raw.get("jump_relation_semantic_min_presence", 0.65))
    jump_relation_semantic_min_direction = float(raw.get("jump_relation_semantic_min_direction", 0.55))
    required_presence_groups = raw.get("required_presence_groups") or []
    if not isinstance(required_presence_groups, list):
        required_presence_groups = []
    anchors = raw.get("anchor_phases") or [0.10, 0.50, 0.90]
    clean_anchors: List[float] = []
    for value in anchors:
        try:
            clean_anchors.append(max(0.0, min(1.0, float(value))))
        except (TypeError, ValueError):
            continue
    if not clean_anchors:
        clean_anchors = [0.10, 0.50, 0.90]
    return {
        "enabled": enabled,
        "local_phase_weight": max(0.0, min(local_phase_weight, 0.08)),
        "anchor_penalty_weight": max(0.0, min(anchor_penalty_weight, 0.25)),
        "anchor_phases": clean_anchors,
        "pose_robust_hand_position": pose_robust_hand_position,
        "hand_global_position_weight": max(0.0, min(hand_global_position_weight, 1.0)),
        "relative_motion_enabled": relative_motion_enabled,
        "relative_motion_weight": max(0.0, min(relative_motion_weight, 1.0)),
        "two_hand_relation_weight": max(0.0, min(two_hand_relation_weight, 1.0)),
        "group_missing_distance_weight": max(0.0, min(group_missing_distance_weight, 0.60)),
        "focus_missing_distance_weight": max(0.0, min(focus_missing_distance_weight, 0.75)),
        "relation_missing_distance_weight": max(0.0, min(relation_missing_distance_weight, 1.00)),
        "required_presence_groups": [str(item) for item in required_presence_groups],
        "required_presence_weight": max(0.0, min(required_presence_weight, 0.40)),
        "visible_core_tolerance_cap": max(0.0, min(visible_core_tolerance_cap, 0.080)),
        "core_visible_score_scale": max(SCORE_SCALE, min(core_visible_score_scale, 0.180)),
        "core_visible_dtw_threshold": max(0.0, min(core_visible_dtw_threshold, 0.120)),
        "core_visible_presence_threshold": max(0.0, min(core_visible_presence_threshold, 1.0)),
        "core_visible_max_normalized_distance": max(0.0, min(core_visible_max_normalized_distance, 0.180)),
        "jump_relation_semantic_floor_enabled": jump_relation_semantic_floor_enabled,
        "jump_relation_semantic_max_score": max(0.0, min(jump_relation_semantic_max_score, 90.0)),
        "jump_relation_semantic_min_presence": max(0.0, min(jump_relation_semantic_min_presence, 1.0)),
        "jump_relation_semantic_min_direction": max(-1.0, min(jump_relation_semantic_min_direction, 1.0)),
    }


def _phase_anchor_frame(seq: SequenceData, target_phase: float) -> Optional[FrameFeature]:
    if not seq.features:
        return None
    phases = np.asarray([float(feature.semantic_phase) for feature in seq.features], dtype=np.float32)
    if not np.isfinite(phases).all() or float(phases.max() - phases.min()) <= 1e-6:
        idx = int(round(max(0.0, min(1.0, target_phase)) * (len(seq.features) - 1)))
        return seq.features[idx]
    idx = int(np.argmin(np.abs(phases - float(target_phase))))
    return seq.features[idx]


def _semantic_phase_anchor_penalty(
    standard: SequenceData,
    query: SequenceData,
    profile: Optional[SemanticProfile],
) -> Tuple[float, Dict[str, Any]]:
    config = _semantic_dtw_config(profile)
    if not config["enabled"] or config["anchor_penalty_weight"] <= 0.0:
        return 0.0, {"enabled": False}
    rows: List[Dict[str, float]] = []
    weighted = 0.0
    weight_sum = 0.0
    for phase in config["anchor_phases"]:
        std_frame = _phase_anchor_frame(standard, float(phase))
        qry_frame = _phase_anchor_frame(query, float(phase))
        if std_frame is None or qry_frame is None:
            continue
        dist, metrics = frame_distance(std_frame, qry_frame, profile)
        semantic_focus_distance = float(metrics.get("weighted", dist))
        phase_gap = abs(float(std_frame.semantic_phase) - float(qry_frame.semantic_phase))
        # Middle-phase mismatch is usually more informative than exact edges.
        anchor_weight = 1.25 if 0.35 <= float(phase) <= 0.65 else 1.0
        weighted += anchor_weight * semantic_focus_distance
        weight_sum += anchor_weight
        rows.append(
            {
                "target_phase": float(phase),
                "standard_phase": float(std_frame.semantic_phase),
                "query_phase": float(qry_frame.semantic_phase),
                "standard_frame_idx": float(std_frame.frame_idx),
                "query_frame_idx": float(qry_frame.frame_idx),
                "phase_gap": phase_gap,
                "distance": semantic_focus_distance,
            }
        )
    if weight_sum <= 1e-8:
        return 0.0, {"enabled": False, "reason": "no_anchor_frames"}
    mean_distance = weighted / weight_sum
    penalty = float(config["anchor_penalty_weight"]) * mean_distance
    return penalty, {
        "enabled": True,
        "anchor_penalty_weight": float(config["anchor_penalty_weight"]),
        "mean_anchor_distance": mean_distance,
        "anchors": rows,
    }


def _relation_delta_summary(seq: SequenceData, group: str = "two_hand_relation") -> Optional[Dict[str, Any]]:
    if not seq.features or group not in seq.features[0].groups:
        return None
    valid: List[np.ndarray] = []
    for item in seq.features:
        sl = item.groups[group]
        if float(item.mask[sl].mean()) >= 0.50:
            valid.append(np.asarray(item.vector[sl], dtype=np.float32))
    if len(valid) < 3:
        return None
    window = max(1, min(3, int(round(len(valid) * 0.25))))
    start = np.stack(valid[:window], axis=0).mean(axis=0)
    end = np.stack(valid[-window:], axis=0).mean(axis=0)
    delta = (end - start).astype(np.float32)
    return {
        "valid_count": len(valid),
        "start": start,
        "end": end,
        "delta": delta,
    }


def _jump_relation_semantic_floor(
    standard: SequenceData,
    query: SequenceData,
    group_mean: Dict[str, float],
    sequence_penalty: Dict[str, Any],
    profile: Optional[SemanticProfile],
    config: Dict[str, Any],
) -> Tuple[float, Dict[str, Any]]:
    if profile is None or profile.word != "跳" or not bool(config.get("jump_relation_semantic_floor_enabled", False)):
        return 0.0, {"enabled": False}
    max_score = float(config.get("jump_relation_semantic_max_score", 0.0))
    if max_score <= 0.0:
        return 0.0, {"enabled": False, "reason": "max_score_disabled"}

    query_presence = sequence_penalty.get("query_presence") or _presence_ratio(query)
    relation_presence = min(float(query_presence.get("left_hand", 0.0)), float(query_presence.get("right_hand", 0.0)))
    min_presence = float(config.get("jump_relation_semantic_min_presence", 0.65))
    if relation_presence < min_presence:
        return 0.0, {
            "enabled": True,
            "used": False,
            "reason": "insufficient_two_hand_presence",
            "relation_presence": relation_presence,
            "min_presence": min_presence,
        }
    if float(sequence_penalty.get("required_presence_penalty", 0.0)) > 0.06:
        return 0.0, {
            "enabled": True,
            "used": False,
            "reason": "required_presence_penalty_too_high",
            "relation_presence": relation_presence,
            "required_presence_penalty": float(sequence_penalty.get("required_presence_penalty", 0.0)),
        }
    if float(group_mean.get("right_hand_shape", 0.0)) > 0.36 or float(group_mean.get("right_hand", 0.0)) > 0.36:
        return 0.0, {
            "enabled": True,
            "used": False,
            "reason": "right_hand_geometry_too_far",
            "right_hand": float(group_mean.get("right_hand", 0.0)),
            "right_hand_shape": float(group_mean.get("right_hand_shape", 0.0)),
        }

    std_summary = _relation_delta_summary(standard)
    qry_summary = _relation_delta_summary(query)
    if std_summary is None or qry_summary is None:
        return 0.0, {"enabled": True, "used": False, "reason": "missing_relation_delta"}
    std_delta = np.asarray(std_summary["delta"], dtype=np.float32)
    qry_delta = np.asarray(qry_summary["delta"], dtype=np.float32)
    semantic_dims = np.asarray([0, 1, 2, 3], dtype=np.int64)
    std_vec = std_delta[semantic_dims]
    qry_vec = qry_delta[semantic_dims]
    std_norm = float(np.linalg.norm(std_vec))
    qry_norm = float(np.linalg.norm(qry_vec))
    if std_norm <= 1e-6 or qry_norm <= 1e-6:
        return 0.0, {"enabled": True, "used": False, "reason": "weak_relation_delta"}
    cosine = max(-1.0, min(1.0, float(np.dot(std_vec, qry_vec) / (std_norm * qry_norm))))
    min_direction = float(config.get("jump_relation_semantic_min_direction", 0.55))
    if cosine < min_direction:
        return 0.0, {
            "enabled": True,
            "used": False,
            "reason": "relation_direction_mismatch",
            "direction_cosine": cosine,
            "min_direction": min_direction,
        }

    vertical_dims = [1, 3]
    vertical_scores: List[float] = []
    for dim in vertical_dims:
        std_value = float(std_delta[dim])
        qry_value = float(qry_delta[dim])
        if abs(std_value) <= 1e-6:
            continue
        signed_ratio = (qry_value * (1.0 if std_value >= 0 else -1.0)) / max(abs(std_value), 1e-6)
        vertical_scores.append(max(0.0, min(1.0, signed_ratio / 0.45)))
    vertical_score = float(np.mean(vertical_scores)) if vertical_scores else 0.0
    if vertical_score < 0.70:
        return 0.0, {
            "enabled": True,
            "used": False,
            "reason": "weak_same_direction_vertical_jump",
            "direction_cosine": cosine,
            "vertical_score": vertical_score,
        }

    std_vertical_mag = float(np.linalg.norm(std_delta[vertical_dims]))
    qry_vertical_mag = float(np.linalg.norm(qry_delta[vertical_dims]))
    amplitude_ratio = qry_vertical_mag / max(std_vertical_mag, 1e-6)
    if amplitude_ratio < 0.42:
        return 0.0, {
            "enabled": True,
            "used": False,
            "reason": "relation_jump_amplitude_too_small",
            "direction_cosine": cosine,
            "vertical_score": vertical_score,
            "amplitude_ratio": amplitude_ratio,
        }
    qry_horizontal_mag = float(np.linalg.norm(qry_delta[[0, 2]]))
    query_horizontal_to_vertical = qry_horizontal_mag / max(qry_vertical_mag, 1e-6)
    if query_horizontal_to_vertical > 1.25:
        return 0.0, {
            "enabled": True,
            "used": False,
            "reason": "relation_motion_too_horizontal",
            "direction_cosine": cosine,
            "vertical_score": vertical_score,
            "amplitude_ratio": amplitude_ratio,
            "query_horizontal_to_vertical": query_horizontal_to_vertical,
        }
    amplitude_score = float(math.exp(-0.32 * min(abs(math.log(max(amplitude_ratio, 1e-6))), 3.0)))
    direction_score = (cosine - min_direction) / max(1.0 - min_direction, 1e-6)
    direction_score = max(0.0, min(1.0, direction_score))
    presence_factor = 0.75 + 0.25 * max(0.0, min(1.0, (relation_presence - min_presence) / max(1.0 - min_presence, 1e-6)))
    relation_quality = 0.45 * direction_score + 0.35 * vertical_score + 0.20 * amplitude_score
    semantic_score = max_score * (0.62 + 0.38 * relation_quality) * presence_factor
    semantic_score = max(0.0, min(max_score, semantic_score))
    return semantic_score, {
        "enabled": True,
        "used": semantic_score > 0.0,
        "score": semantic_score,
        "max_score": max_score,
        "relation_presence": relation_presence,
        "direction_cosine": cosine,
        "direction_score": direction_score,
        "vertical_score": vertical_score,
        "amplitude_ratio": amplitude_ratio,
        "amplitude_score": amplitude_score,
        "query_horizontal_to_vertical": query_horizontal_to_vertical,
        "relation_quality": relation_quality,
        "standard_valid_count": int(std_summary["valid_count"]),
        "query_valid_count": int(qry_summary["valid_count"]),
        "standard_delta": [float(x) for x in std_delta.tolist()],
        "query_delta": [float(x) for x in qry_delta.tolist()],
    }


def _sequence_penalty(
    standard: SequenceData,
    query: SequenceData,
    group_mean: Dict[str, float],
    profile: Optional[SemanticProfile] = None,
) -> Dict[str, Any]:
    n = len(standard.features)
    m = len(query.features)
    length_ratio = min(n, m) / max(n, m, 1)
    positive_like_floor = 0.50
    length_penalty = 0.0
    if length_ratio < positive_like_floor:
        length_penalty = 0.28 * ((positive_like_floor - length_ratio) / positive_like_floor)
    temporal_profile_factor = 0.0 if length_ratio <= 0.50 else min(1.0, (length_ratio - 0.50) / 0.45)

    standard_presence = _presence_ratio(standard)
    query_presence = _presence_ratio(query)
    presence_delta = {
        group: abs(float(standard_presence.get(group, 0.0)) - float(query_presence.get(group, 0.0)))
        for group in ["left_hand", "right_hand", "pose", "face"]
    }
    penalty_weights = _profile_group_weights(profile, _sequence_groups(standard))
    hand_dynamic_scale = _hand_dynamic_scale(profile, _sequence_groups(standard))
    presence_penalty = 0.14 * sum(penalty_weights.get(group, 0.0) * presence_delta[group] for group in presence_delta)

    required_presence_penalty = 0.0
    required_presence_detail: Dict[str, float] = {}
    if profile is not None:
        config = _semantic_dtw_config(profile)
        required_groups = _required_presence_groups(profile)
        required_weight = float(config["required_presence_weight"])
        if required_groups and required_weight > 0.0:
            required_sum = 0.0
            required_weight_sum = 0.0
            for group in ["left_hand", "right_hand"]:
                if group not in required_groups:
                    continue
                deficit = max(0.0, float(standard_presence.get(group, 0.0)) - float(query_presence.get(group, 0.0)))
                group_weight = max(float(penalty_weights.get(group, 0.0)), 0.08)
                required_presence_detail[f"{group}_deficit"] = deficit
                required_sum += group_weight * deficit
                required_weight_sum += group_weight
            if "two_hand_relation" in required_groups:
                standard_pair = min(float(standard_presence.get("left_hand", 0.0)), float(standard_presence.get("right_hand", 0.0)))
                query_pair = min(float(query_presence.get("left_hand", 0.0)), float(query_presence.get("right_hand", 0.0)))
                relation_deficit = max(0.0, standard_pair - query_pair)
                relation_weight = max(float(penalty_weights.get("two_hand_relation", 0.0)), 0.12)
                required_presence_detail["two_hand_relation_deficit"] = relation_deficit
                required_sum += relation_weight * relation_deficit
                required_weight_sum += relation_weight
            if required_weight_sum > 1e-8:
                required_presence_penalty = required_weight * (required_sum / required_weight_sum)

    standard_motion = _sequence_motion_by_group(standard)
    query_motion = _sequence_motion_by_group(query)
    motion_delta = {
        group: min(_safe_log_ratio(float(standard_motion.get(group, 0.0)), float(query_motion.get(group, 0.0))), 3.0)
        for group in _sequence_groups(standard)
    }
    motion_penalty = temporal_profile_factor * 0.025 * hand_dynamic_scale * sum(
        penalty_weights.get(group, 0.0) * motion_delta[group] for group in motion_delta
    )
    dynamic_required_penalty = 0.0
    dynamic_required_detail: Dict[str, float] = {}
    if profile is not None and profile.word in {"跳"}:
        focus_groups = [group for group in profile.focus_groups if group in standard_motion]
        if not focus_groups:
            focus_groups = ["right_hand", "right_hand_shape"]
        standard_focus_motion = max(float(standard_motion.get(group, 0.0)) for group in focus_groups)
        query_focus_motion = max(float(query_motion.get(group, 0.0)) for group in focus_groups)
        motion_ratio = query_focus_motion / max(standard_focus_motion, 1e-6)
        dynamic_required_detail = {
            "standard_focus_motion": standard_focus_motion,
            "query_focus_motion": query_focus_motion,
            "motion_ratio": motion_ratio,
        }
        if standard_focus_motion > 1e-6 and motion_ratio < 0.25:
            dynamic_required_penalty = 0.045 * ((0.25 - motion_ratio) / 0.25)

    standard_roughness = _sequence_roughness_by_group(standard)
    query_roughness = _sequence_roughness_by_group(query)
    roughness_delta = {
        group: min(_safe_log_ratio(float(standard_roughness.get(group, 0.0)), float(query_roughness.get(group, 0.0))), 3.0)
        for group in _sequence_groups(standard)
    }
    # Shuffled or jittery sequences can look locally similar under DTW. Keep a
    # separate temporal roughness penalty so the semantic order is not erased.
    roughness_penalty = temporal_profile_factor * 0.095 * hand_dynamic_scale * sum(
        penalty_weights.get(group, 0.0) * roughness_delta[group] for group in roughness_delta
    )

    info_penalty = 0.0
    if m < 4 and n >= 8:
        info_penalty = 0.16
    elif m < 0.25 * n:
        info_penalty = 0.08

    endpoint_penalty = 0.0
    if n >= 12 and length_ratio >= 0.90 and standard.features and query.features:
        start_dist = frame_distance(standard.features[0], query.features[0], profile)[0]
        end_dist = frame_distance(standard.features[-1], query.features[-1], profile)[0]
        endpoint_penalty = 0.30 * max(0.0, ((start_dist + end_dist) / 2.0) - 0.02)

    # 手部是主要语义源。若标准或查询的手部信息极弱，不能直接给出高置信分。
    hand_info_standard = max(standard_presence["left_hand"], standard_presence["right_hand"])
    hand_info_query = max(query_presence["left_hand"], query_presence["right_hand"])
    confidence_warning_penalty = 0.0
    if hand_info_standard < 0.20 or hand_info_query < 0.20:
        confidence_warning_penalty = 0.04

    semantic_delta_penalty, semantic_delta_detail = _semantic_delta_penalty(standard, query, profile)
    semantic_delta_penalty *= hand_dynamic_scale
    semantic_anchor_penalty, semantic_anchor_detail = _semantic_phase_anchor_penalty(standard, query, profile)
    semantic_anchor_penalty *= min(hand_dynamic_scale, 1.35)

    total_penalty = (
        length_penalty
        + presence_penalty
        + required_presence_penalty
        + motion_penalty
        + dynamic_required_penalty
        + roughness_penalty
        + info_penalty
        + endpoint_penalty
        + confidence_warning_penalty
        + semantic_delta_penalty
        + semantic_anchor_penalty
    )
    return {
        "length_ratio": length_ratio,
        "length_penalty": length_penalty,
        "temporal_profile_factor": temporal_profile_factor,
        "hand_dynamic_scale": hand_dynamic_scale,
        "presence_delta": presence_delta,
        "presence_penalty": presence_penalty,
        "required_presence_penalty": required_presence_penalty,
        "required_presence_detail": required_presence_detail,
        "motion_delta": motion_delta,
        "motion_penalty": motion_penalty,
        "dynamic_required_penalty": dynamic_required_penalty,
        "dynamic_required_detail": dynamic_required_detail,
        "roughness_delta": roughness_delta,
        "roughness_penalty": roughness_penalty,
        "info_penalty": info_penalty,
        "endpoint_penalty": endpoint_penalty,
        "confidence_warning_penalty": confidence_warning_penalty,
        "semantic_delta_penalty": semantic_delta_penalty,
        "semantic_delta_detail": semantic_delta_detail,
        "semantic_anchor_penalty": semantic_anchor_penalty,
        "semantic_anchor_detail": semantic_anchor_detail,
        "total_sequence_penalty": total_penalty,
        "standard_presence": standard_presence,
        "query_presence": query_presence,
        "standard_motion": standard_motion,
        "query_motion": query_motion,
        "standard_roughness": standard_roughness,
        "query_roughness": query_roughness,
    }


def _dimension_weights(group: str, size: int, profile: Optional[SemanticProfile]) -> np.ndarray:
    weights = np.ones(size, dtype=np.float32)
    if profile is None:
        return weights
    if group == "two_hand_relation" and size == 8:
        # [tip_rel_x, tip_rel_y, base_rel_x, base_rel_y, finger_axis_x,
        #  finger_axis_y, |tip_rel|, |base_rel|]. For 跳 the vertical
        # relation of the right "legs" above the left "ground" is semantic.
        if profile.word == "跳":
            return np.asarray([0.90, 2.25, 0.75, 1.45, 0.65, 1.55, 1.25, 0.85], dtype=np.float32)
        return np.asarray([1.00, 1.35, 0.85, 1.10, 0.80, 1.10, 1.05, 0.90], dtype=np.float32)
    spec: Dict[str, float] = {}
    if group.startswith("left_hand"):
        spec.update(profile.keypoint_weights.get("left_hand") or {})
        spec.update(profile.keypoint_weights.get("hand") or {})
    elif group.startswith("right_hand"):
        spec.update(profile.keypoint_weights.get("right_hand") or {})
        spec.update(profile.keypoint_weights.get("hand") or {})
    elif group == "pose":
        spec.update(profile.keypoint_weights.get("pose") or {})
    elif group == "face":
        spec.update(profile.keypoint_weights.get("face") or {})
    if not spec:
        return weights

    if group in {"left_hand", "right_hand"}:
        for raw_idx, raw_weight in spec.items():
            try:
                idx = int(raw_idx)
                value = max(0.0, float(raw_weight))
            except (TypeError, ValueError):
                continue
            start = idx * 3
            if 0 <= start < size:
                weights[start : start + 3] *= value
    elif group in {"left_hand_shape", "right_hand_shape"}:
        shape_alias = {
            "thumb": [0, 5, 10, 15],
            "index": [1, 6, 11, 16],
            "middle": [2, 7, 12, 17],
            "ring": [3, 8, 13, 18],
            "pinky": [4, 9, 14, 19],
            "spread": [5, 6, 7, 8, 9],
            "opening": [5, 6, 7, 8, 9, 15, 16, 17, 18, 19],
        }
        landmark_shape_alias = {
            "4": shape_alias["thumb"],
            "8": shape_alias["index"],
            "12": shape_alias["middle"],
            "16": shape_alias["ring"],
            "20": shape_alias["pinky"],
            "1": shape_alias["thumb"],
            "5": shape_alias["index"],
            "9": shape_alias["middle"],
            "13": shape_alias["ring"],
            "17": shape_alias["pinky"],
        }
        for raw_key, raw_weight in spec.items():
            try:
                value = max(0.0, float(raw_weight))
            except (TypeError, ValueError):
                continue
            key = str(raw_key)
            if key in landmark_shape_alias:
                indices = landmark_shape_alias[key]
            elif key.isdigit():
                indices = [int(raw_key)]
            else:
                indices = shape_alias.get(key, [])
            for idx in indices:
                if 0 <= idx < size:
                    weights[idx] *= value
    return weights


def _weighted_rmse(left: np.ndarray, right: np.ndarray, weights: np.ndarray, cap: Optional[float] = None) -> float:
    weights = np.asarray(weights, dtype=np.float32)
    denom = float(weights.sum())
    if denom <= 1e-8:
        return 0.0
    diff = left - right
    if cap is not None and cap > 0:
        diff = np.clip(diff, -float(cap), float(cap))
    return float(np.sqrt(np.sum(weights * (diff ** 2)) / denom))


def _similarity_aligned_xy_rmse(a_pts: np.ndarray, b_pts: np.ndarray, point_weights: np.ndarray) -> float:
    """2D similarity-align one hand to another before measuring geometry.

    This keeps the hand-shape/relative skeleton comparison, but reduces
    sensitivity to camera angle, wrist rotation, and small palm orientation
    changes that are visible in real browser captures.
    """

    if a_pts.shape != b_pts.shape or a_pts.shape[0] < 3:
        return float("inf")
    weights = np.asarray(point_weights, dtype=np.float64).reshape(-1)
    weights = np.where(np.isfinite(weights), weights, 0.0)
    weights = np.maximum(weights, 0.0)
    if float(weights.sum()) <= 1e-8:
        weights = np.ones(a_pts.shape[0], dtype=np.float64)
    weights = weights / max(float(weights.sum()), 1e-8)

    a_xy = np.asarray(a_pts[:, :2], dtype=np.float64)
    b_xy = np.asarray(b_pts[:, :2], dtype=np.float64)
    a_center = np.sum(a_xy * weights[:, None], axis=0)
    b_center = np.sum(b_xy * weights[:, None], axis=0)
    a0 = a_xy - a_center
    b0 = b_xy - b_center
    denom = float(np.sum(weights * np.sum(b0 * b0, axis=1)))
    if denom <= 1e-8:
        return float("inf")
    h = (b0 * weights[:, None]).T @ a0
    try:
        u, singular_values, vt = np.linalg.svd(h)
    except np.linalg.LinAlgError:
        return float("inf")
    r = vt.T @ u.T
    if np.linalg.det(r) < 0:
        vt[-1, :] *= -1
        r = vt.T @ u.T
    scale = max(0.70, min(1.45, float(np.sum(singular_values) / denom)))
    aligned = scale * (b0 @ r) + a_center
    diff = a_xy - aligned
    return float(np.sqrt(np.sum(weights * np.sum(diff * diff, axis=1))))


def _pose_robust_hand_distance(
    av: np.ndarray,
    bv: np.ndarray,
    am: np.ndarray,
    bm: np.ndarray,
    dim_weights: np.ndarray,
    raw_dist: float,
    profile: Optional[SemanticProfile],
) -> Tuple[float, Dict[str, float]]:
    """Compare hand landmarks mostly in wrist-relative coordinates.

    For pure hand semantics, sitting/standing mainly shifts the whole hand in
    body-normalized space. The local hand geometry should dominate; a small
    global residual keeps direction/placement from disappearing entirely.
    """

    if av.size % 3 != 0 or av.shape != bv.shape:
        return raw_dist, {"hand_pose_robust_used": 0.0}
    config = _semantic_dtw_config(profile)
    if not config["pose_robust_hand_position"]:
        return raw_dist, {"hand_pose_robust_used": 0.0}

    a_pts = av.reshape(-1, 3)
    b_pts = bv.reshape(-1, 3)
    a_mask = am.reshape(-1, 3)
    b_mask = bm.reshape(-1, 3)
    w_pts = dim_weights.reshape(-1, 3)
    both_points = (a_mask.mean(axis=1) > 0.5) & (b_mask.mean(axis=1) > 0.5)
    if int(both_points.sum()) < 2:
        return raw_dist, {"hand_pose_robust_used": 0.0}

    if both_points[0]:
        a_anchor = a_pts[0]
        b_anchor = b_pts[0]
    else:
        a_anchor = a_pts[both_points].mean(axis=0)
        b_anchor = b_pts[both_points].mean(axis=0)
    a_local = a_pts - a_anchor
    b_local = b_pts - b_anchor
    flat_mask = np.repeat(both_points.astype(bool), 3)
    local_dist = _weighted_rmse(a_local.reshape(-1)[flat_mask], b_local.reshape(-1)[flat_mask], w_pts.reshape(-1)[flat_mask])
    point_weights = w_pts[both_points, :2].mean(axis=1)
    aligned_xy_dist = _similarity_aligned_xy_rmse(a_pts[both_points], b_pts[both_points], point_weights)
    global_anchor_dist = float(np.linalg.norm(a_anchor[:3] - b_anchor[:3]))
    global_weight = float(config["hand_global_position_weight"])
    orientation_dist = aligned_xy_dist + global_weight * global_anchor_dist if math.isfinite(aligned_xy_dist) else float("inf")
    robust_dist = min(local_dist + global_weight * global_anchor_dist, orientation_dist)
    return min(raw_dist, robust_dist), {
        "hand_pose_robust_used": 1.0,
        "hand_local_distance": float(local_dist),
        "hand_similarity_aligned_xy_distance": float(aligned_xy_dist) if math.isfinite(aligned_xy_dist) else -1.0,
        "hand_global_anchor_distance": global_anchor_dist,
        "hand_global_position_weight": global_weight,
        "hand_pose_robust_distance": float(robust_dist),
    }


def _group_distance_between(
    a: FrameFeature,
    b: FrameFeature,
    a_group: str,
    b_group: str,
    metric_group: str,
    profile: Optional[SemanticProfile] = None,
) -> Tuple[float, float]:
    if a_group not in a.groups or b_group not in b.groups:
        return 0.0, 0.0
    sl = a.groups[a_group]
    br = b.groups[b_group]
    av = a.vector[sl]
    bv = b.vector[br]
    am = a.mask[sl]
    bm = b.mask[br]
    if av.shape != bv.shape or am.shape != bm.shape:
        return 0.0, 1.0
    both = (am > 0) & (bm > 0)
    either = (am > 0) | (bm > 0)
    mismatch = (am > 0) != (bm > 0)
    if both.any():
        left = av[both]
        right = bv[both]
        dim_weights = _dimension_weights(metric_group, av.shape[0], profile)[both]
        full_dim_weights = _dimension_weights(metric_group, av.shape[0], profile)
        cap = 0.35 if metric_group in HAND_SHAPE_GROUPS else None
        raw_dist = _weighted_rmse(left, right, dim_weights, cap=cap)
        dist = raw_dist
        extra_metrics: Dict[str, float] = {}
        if metric_group in {"left_hand", "right_hand"}:
            dist, extra_metrics = _pose_robust_hand_distance(av, bv, am, bm, full_dim_weights, raw_dist, profile)
        if metric_group in {"left_hand", "right_hand", "pose"}:
            denom = float(np.dot(dim_weights * right, right))
            if denom > 1e-8:
                alpha = float(np.dot(dim_weights * left, right) / denom)
                alpha = max(0.70, min(1.45, alpha))
                scaled_dist = _weighted_rmse(left, alpha * right, dim_weights)
                scale_penalty = 0.004 * abs(math.log(max(alpha, 1e-6)))
                dist = min(raw_dist, scaled_dist + scale_penalty)
                if metric_group in {"left_hand", "right_hand"} and extra_metrics:
                    dist = min(dist, float(extra_metrics["hand_pose_robust_distance"]))
    else:
        dist = 0.0
        extra_metrics = {}
    missing_penalty = float(mismatch.sum()) / float(either.sum()) if either.any() else 0.0
    if extra_metrics:
        # Store the diagnostics on the function object for the caller that
        # immediately consumes this result. This keeps the public tuple stable.
        _group_distance_between.last_extra_metrics = extra_metrics  # type: ignore[attr-defined]
    else:
        _group_distance_between.last_extra_metrics = {}  # type: ignore[attr-defined]
    return dist, missing_penalty


def _group_distance(a: FrameFeature, b: FrameFeature, group: str, profile: Optional[SemanticProfile] = None) -> Tuple[float, float]:
    return _group_distance_between(a, b, group, group, group, profile)


def frame_distance(a: FrameFeature, b: FrameFeature, profile: Optional[SemanticProfile] = None) -> Tuple[float, Dict[str, float]]:
    group_metrics: Dict[str, float] = {}
    weighted = 0.0
    missing = 0.0
    groups = [
        group
        for group in [
            "left_hand",
            "right_hand",
            "left_hand_shape",
            "right_hand_shape",
            "left_hand_motion",
            "right_hand_motion",
            "left_hand_shape_motion",
            "right_hand_shape_motion",
            "two_hand_relation",
            "two_hand_relation_motion",
            "pose",
            "face",
        ]
        if group in a.groups and group in b.groups
    ]
    weights = _profile_group_weights(profile, groups)

    hand_like_groups = [*HAND_GROUPS, *RELATIVE_MOTION_GROUPS]
    hand_groups = [group for group in hand_like_groups if group in groups]
    non_hand_groups = [group for group in groups if group not in hand_like_groups]

    direct_hand: Dict[str, Tuple[float, float]] = {}
    swapped_hand: Dict[str, Tuple[float, float]] = {}
    for group in hand_groups:
        direct_hand[group] = _group_distance(a, b, group, profile)
    if profile is not None and profile.allow_hand_swap:
        swap_pairs = {
            "left_hand": ("left_hand", "right_hand"),
            "right_hand": ("right_hand", "left_hand"),
            "left_hand_shape": ("left_hand_shape", "right_hand_shape"),
            "right_hand_shape": ("right_hand_shape", "left_hand_shape"),
            "left_hand_motion": ("left_hand_motion", "right_hand_motion"),
            "right_hand_motion": ("right_hand_motion", "left_hand_motion"),
            "left_hand_shape_motion": ("left_hand_shape_motion", "right_hand_shape_motion"),
            "right_hand_shape_motion": ("right_hand_shape_motion", "left_hand_shape_motion"),
        }
        for group, (a_group, b_group) in swap_pairs.items():
            if group in hand_groups and a_group in a.groups and b_group in b.groups:
                swapped_hand[group] = _group_distance_between(a, b, a_group, b_group, group, profile)
    def contribution_distance(group: str, dist: float, miss: float) -> float:
        return dist + _group_missing_distance_weight(profile, group) * miss

    direct_weighted = sum(
        weights.get(group, 0.0) * contribution_distance(group, direct_hand[group][0], direct_hand[group][1])
        for group in direct_hand
    )
    swapped_weighted = sum(
        weights.get(group, 0.0)
        * contribution_distance(group, *swapped_hand.get(group, direct_hand.get(group, (0.0, 0.0))))
        for group in hand_groups
    )
    use_swapped = bool(swapped_hand) and swapped_weighted < direct_weighted
    selected_hand = swapped_hand if use_swapped else direct_hand

    missing_weighted = 0.0
    missing_weight_sum = 0.0
    for group in hand_groups:
        dist, miss = selected_hand.get(group, direct_hand.get(group, (0.0, 0.0)))
        missing_distance = _group_missing_distance_weight(profile, group) * miss
        group_metrics[group] = dist
        group_metrics[f"{group}_missing_penalty"] = miss
        group_metrics[f"{group}_missing_distance"] = missing_distance
        group_weight = weights.get(group, 0.0)
        weighted += group_weight * (dist + missing_distance)
        missing_weighted += group_weight * miss
        missing_weight_sum += group_weight
    group_metrics["hand_side_swapped"] = 1.0 if use_swapped else 0.0

    for group in non_hand_groups:
        dist, miss = _group_distance(a, b, group, profile)
        missing_distance = _group_missing_distance_weight(profile, group) * miss
        group_metrics[group] = dist
        group_metrics[f"{group}_missing_penalty"] = miss
        group_metrics[f"{group}_missing_distance"] = missing_distance
        group_weight = weights.get(group, 0.0)
        weighted += group_weight * (dist + missing_distance)
        missing_weighted += group_weight * miss
        missing_weight_sum += group_weight

    missing = missing_weighted / max(missing_weight_sum, 1e-6)
    weighted += weights.get("missing", GROUP_WEIGHTS["missing"]) * missing
    group_metrics["missing"] = missing
    group_metrics["weighted"] = weighted
    return weighted, group_metrics


def _normalize_frame_weights(values: np.ndarray, low: float = 0.45, high: float = 2.75) -> np.ndarray:
    if values.size == 0:
        return values.astype(np.float32)
    clean = np.asarray(values, dtype=np.float32)
    clean = np.where(np.isfinite(clean), clean, 1.0)
    clean = np.maximum(clean, 0.05)
    mean = float(clean.mean())
    if mean <= 1e-8:
        clean = np.ones_like(clean, dtype=np.float32)
    else:
        clean = clean / mean
    clean = np.clip(clean, low, high)
    mean = float(clean.mean())
    if mean > 1e-8:
        clean = clean / mean
    return clean.astype(np.float32)


def _semantic_phase_from_weights(values: np.ndarray) -> np.ndarray:
    """Map frames onto [0, 1] by cumulative semantic energy, not by frame id."""

    n = int(values.size)
    if n == 0:
        return np.zeros(0, dtype=np.float32)
    if n == 1:
        return np.zeros(1, dtype=np.float32)
    clean = np.asarray(values, dtype=np.float32)
    clean = np.where(np.isfinite(clean), clean, 1.0)
    clean = np.maximum(clean, 0.05)
    baseline = float(np.percentile(clean, 20))
    energy = np.maximum(clean - baseline, 0.0)
    if float(energy.sum()) <= 1e-8:
        return np.linspace(0.0, 1.0, n, dtype=np.float32)
    centered_cumulative = np.cumsum(energy, dtype=np.float64) - 0.5 * energy
    denom = max(float(energy.sum()), 1e-8)
    phases = np.asarray(centered_cumulative / denom, dtype=np.float32)
    phases = np.clip(phases, 0.0, 1.0)
    phases[0] = min(float(phases[0]), 0.02)
    phases[-1] = max(float(phases[-1]), 0.98)
    return phases.astype(np.float32)


def _adjacent_group_motion(
    prev: FrameFeature,
    curr: FrameFeature,
    group: str,
    profile: Optional[SemanticProfile],
) -> float:
    if group not in prev.groups or group not in curr.groups:
        return 0.0
    sl = prev.groups[group]
    both = (prev.mask[sl] > 0) & (curr.mask[sl] > 0)
    if not both.any():
        return 0.0
    dim_weights = _dimension_weights(group, prev.vector[sl].shape[0], profile)[both]
    return _weighted_rmse(prev.vector[sl][both], curr.vector[sl][both], dim_weights)


def compute_semantic_frame_weight_values(
    seq: SequenceData,
    profile: Optional[SemanticProfile] = None,
    combine_stored: bool = True,
) -> np.ndarray:
    """Return mean-normalized per-frame weights from semantic motion density.

    The template/action semantics define which feature groups matter. Within
    those groups, adjacent-frame motion is converted into a dense temporal
    importance curve. Stored weights, when available, are treated as an external
    prior from the database or browser-side sampler and combined conservatively.
    """

    n = len(seq.features)
    if n == 0:
        return np.zeros(0, dtype=np.float32)

    groups_in_seq = _sequence_groups(seq)
    if profile is not None:
        focus_groups = [group for group in profile.focus_groups if group in groups_in_seq]
    else:
        focus_groups = []
    if not focus_groups:
        raw_weights = _profile_group_weights(profile, groups_in_seq)
        focus_groups = [group for group in groups_in_seq if raw_weights.get(group, 0.0) > 0.0]
    if not focus_groups:
        dynamic = np.ones(n, dtype=np.float32)
    else:
        group_weights = _profile_group_weights(profile, focus_groups)
        energy = np.zeros(n, dtype=np.float32)
        for idx, (prev, curr) in enumerate(zip(seq.features[:-1], seq.features[1:]), start=1):
            weighted_motion = 0.0
            weight_sum = 0.0
            for group in focus_groups:
                group_weight = float(group_weights.get(group, 0.0))
                if group_weight <= 0.0:
                    continue
                motion = _adjacent_group_motion(prev, curr, group, profile)
                weighted_motion += group_weight * motion
                weight_sum += group_weight
            edge_energy = weighted_motion / weight_sum if weight_sum > 1e-8 else 0.0
            energy[idx - 1] += 0.5 * edge_energy
            energy[idx] += 0.5 * edge_energy

        if n >= 3:
            smooth = energy.copy()
            smooth[1:-1] = 0.25 * energy[:-2] + 0.50 * energy[1:-1] + 0.25 * energy[2:]
            smooth[0] = 0.75 * energy[0] + 0.25 * energy[1]
            smooth[-1] = 0.75 * energy[-1] + 0.25 * energy[-2]
            energy = smooth

        positive = energy[energy > 1e-8]
        if positive.size == 0:
            dynamic = np.ones(n, dtype=np.float32)
        else:
            floor = float(np.mean(positive)) * 0.20
            dynamic = _normalize_frame_weights(energy + floor)

    if not combine_stored:
        return dynamic

    stored = np.asarray([max(0.05, float(feature.frame_weight)) for feature in seq.features], dtype=np.float32)
    stored = _normalize_frame_weights(stored, low=0.35, high=3.0)
    combined = np.sqrt(np.maximum(dynamic, 0.05) * np.maximum(stored, 0.05))
    return _normalize_frame_weights(combined, low=0.40, high=2.85)


def with_dynamic_frame_weights(seq: SequenceData, profile: Optional[SemanticProfile] = None) -> SequenceData:
    working = _sequence_with_relative_motion_features(seq, profile)
    values = compute_semantic_frame_weight_values(working, profile=profile, combine_stored=True)
    phases = _semantic_phase_from_weights(values)
    features: List[FrameFeature] = []
    for idx, (feature, weight) in enumerate(zip(working.features, values)):
        item = _clone_frame(feature)
        item.frame_weight = float(weight)
        item.semantic_phase = float(phases[idx]) if idx < len(phases) else 0.0
        features.append(item)
    return SequenceData(working.source, working.mode, working.fps, working.total_frames, features)


def _pair_temporal_weight(standard_frame: FrameFeature, query_frame: FrameFeature) -> float:
    standard_weight = max(0.20, min(3.50, float(standard_frame.frame_weight)))
    query_weight = max(0.20, min(3.50, float(query_frame.frame_weight)))
    return 0.70 * standard_weight + 0.30 * query_weight


def _frame_weight_summary(seq: SequenceData) -> Dict[str, Any]:
    values = np.asarray([float(feature.frame_weight) for feature in seq.features], dtype=np.float32)
    if values.size == 0:
        return {"count": 0}
    top_indices = list(np.argsort(values)[-min(8, values.size) :][::-1])
    return {
        "count": int(values.size),
        "mean": float(values.mean()),
        "min": float(values.min()),
        "max": float(values.max()),
        "top_frames": [
            {
                "rank": rank + 1,
                "frame_idx": int(seq.features[idx].frame_idx),
                "timestamp_sec": float(seq.features[idx].timestamp_sec),
                "weight": float(values[idx]),
                "semantic_phase": float(seq.features[idx].semantic_phase),
            }
            for rank, idx in enumerate(top_indices)
        ],
    }


def _semantic_action_window(seq: SequenceData) -> Dict[str, Any]:
    values = np.asarray([float(feature.frame_weight) for feature in seq.features], dtype=np.float32)
    n = int(values.size)
    if n == 0:
        return {"start_index": 0, "end_index": -1, "length": 0, "used": False, "reason": "empty"}
    if n < 5:
        return {
            "start_index": 0,
            "end_index": n - 1,
            "length": n,
            "used": False,
            "reason": "too_short",
            "energy_coverage": 1.0,
        }

    baseline = float(np.percentile(values, 20))
    energy = np.maximum(values - baseline, 0.0)
    total_energy = float(energy.sum())
    peak_index = int(np.argmax(values))
    peak_weight = float(values[peak_index])
    contrast = peak_weight / max(float(values.min()), 1e-6)
    if total_energy <= 1e-8 or contrast < 1.12:
        return {
            "start_index": 0,
            "end_index": n - 1,
            "length": n,
            "used": False,
            "reason": "weak_energy_contrast",
            "energy_coverage": 1.0,
            "peak_index": peak_index,
            "peak_frame_idx": int(seq.features[peak_index].frame_idx),
            "peak_timestamp_sec": float(seq.features[peak_index].timestamp_sec),
            "peak_weight": peak_weight,
            "contrast": contrast,
        }

    active_threshold = max(float(np.percentile(values, 65)), baseline + 0.42 * (peak_weight - baseline))
    active = values >= active_threshold
    active[peak_index] = True

    components: List[Tuple[int, int]] = []
    idx = 0
    while idx < n:
        if not active[idx]:
            idx += 1
            continue
        start = idx
        while idx + 1 < n and active[idx + 1]:
            idx += 1
        components.append((start, idx))
        idx += 1

    peak_component = next(((a, b) for a, b in components if a <= peak_index <= b), (peak_index, peak_index))
    left, right = peak_component
    merge_gap = max(1, int(round(n * 0.06)))
    min_component_energy = 0.08 * float(energy[left : right + 1].sum())
    changed = True
    while changed:
        changed = False
        for a, b in components:
            if b < left and (left - b - 1) <= merge_gap and float(energy[a : b + 1].sum()) >= min_component_energy:
                left = a
                changed = True
            if a > right and (a - right - 1) <= merge_gap and float(energy[a : b + 1].sum()) >= min_component_energy:
                right = b
                changed = True

    left_padding = 0
    right_padding = max(1, int(round(n * 0.03)))
    left = max(0, left - left_padding)
    right = min(n - 1, right + right_padding)

    min_fraction = 0.40 if n < 24 else 0.28
    min_base = 6 if n >= 8 else 4
    min_window = min(n, max(min_base, int(round(n * min_fraction))))
    if right - left + 1 < min_window:
        extra = min_window - (right - left + 1)
        left = max(0, left - max(0, extra // 3))
        right = min(n - 1, right + extra - max(0, extra // 3))
        if right - left + 1 < min_window:
            left = max(0, right - min_window + 1)
            right = min(n - 1, left + min_window - 1)

    window_energy = float(energy[left : right + 1].sum())
    coverage = window_energy / total_energy if total_energy > 1e-8 else 1.0
    used = bool(left > 0 or right < n - 1)
    return {
        "start_index": left,
        "end_index": right,
        "length": right - left + 1,
        "used": used,
        "reason": "semantic_energy_window" if used else "full_sequence_already_active",
        "energy_coverage": coverage,
        "baseline_weight": baseline,
        "active_threshold": active_threshold,
        "peak_index": peak_index,
        "peak_frame_idx": int(seq.features[peak_index].frame_idx),
        "peak_timestamp_sec": float(seq.features[peak_index].timestamp_sec),
        "peak_weight": peak_weight,
        "contrast": contrast,
        "discarded_prefix_frames": left,
        "discarded_suffix_frames": n - 1 - right,
        "start_frame_idx": int(seq.features[left].frame_idx),
        "end_frame_idx": int(seq.features[right].frame_idx),
        "start_timestamp_sec": float(seq.features[left].timestamp_sec),
        "end_timestamp_sec": float(seq.features[right].timestamp_sec),
    }


def _slice_sequence_window(seq: SequenceData, window: Dict[str, Any], suffix: str) -> SequenceData:
    start = int(window.get("start_index", 0))
    end = int(window.get("end_index", len(seq.features) - 1))
    if start < 0 or end < start or not seq.features:
        selected = list(seq.features)
    else:
        selected = seq.features[start : end + 1]
    return SequenceData(
        source=f"{seq.source}::{suffix}[{start}:{end}]",
        mode=seq.mode,
        fps=seq.fps,
        total_frames=seq.total_frames,
        features=[_clone_frame(feature) for feature in selected],
    )


def _presence_from_groups(feature: FrameFeature) -> Dict[str, bool]:
    presence: Dict[str, bool] = {}
    for group in ["pose", "left_hand", "right_hand", "face"]:
        if group not in feature.groups:
            presence[group] = False
            continue
        sl = feature.groups[group]
        presence[group] = bool(float(feature.mask[sl].mean()) >= 0.35)
    return presence


def _resample_sequence_to_length(seq: SequenceData, target_len: int, suffix: str) -> SequenceData:
    current_len = len(seq.features)
    if current_len == 0 or target_len <= 0 or current_len == target_len:
        return seq
    if current_len == 1:
        features = [_clone_frame(seq.features[0]) for _ in range(target_len)]
        for idx, feature in enumerate(features):
            feature.frame_idx = int(round(seq.features[0].frame_idx))
            feature.timestamp_sec = seq.features[0].timestamp_sec
        return SequenceData(f"{seq.source}::{suffix}", seq.mode, seq.fps, seq.total_frames, features)

    positions = np.linspace(0.0, float(current_len - 1), target_len)
    features: List[FrameFeature] = []
    for pos in positions:
        left_idx = int(math.floor(float(pos)))
        right_idx = min(current_len - 1, left_idx + 1)
        alpha = float(pos - left_idx)
        left = seq.features[left_idx]
        right = seq.features[right_idx]
        vector = ((1.0 - alpha) * left.vector + alpha * right.vector).astype(np.float32)
        mask = np.minimum(left.mask, right.mask).astype(np.float32)
        frame = _clone_frame(left, vector=vector, mask=mask)
        frame.frame_idx = int(round((1.0 - alpha) * left.frame_idx + alpha * right.frame_idx))
        frame.timestamp_sec = float((1.0 - alpha) * left.timestamp_sec + alpha * right.timestamp_sec)
        frame.frame_weight = float((1.0 - alpha) * left.frame_weight + alpha * right.frame_weight)
        frame.semantic_phase = float((1.0 - alpha) * left.semantic_phase + alpha * right.semantic_phase)
        frame.presence = _presence_from_groups(frame)
        features.append(frame)
    return SequenceData(f"{seq.source}::{suffix}", seq.mode, seq.fps, seq.total_frames, features)


def _maybe_resample_query_window(standard: SequenceData, query: SequenceData) -> Tuple[SequenceData, Dict[str, Any]]:
    n = len(standard.features)
    m = len(query.features)
    if n <= 0 or m <= 0:
        return query, {"used": False, "reason": "empty"}
    ratio = m / max(n, 1)
    if m >= 4 and ratio < 0.45:
        return _resample_sequence_to_length(query, n, "query_temporal_resample"), {
            "used": True,
            "from_length": m,
            "to_length": n,
            "ratio": ratio,
            "method": "linear_feature_interpolation_after_action_window",
        }
    return query, {"used": False, "ratio": ratio}


def _score_scale_for_action_window(standard: SequenceData, action_window: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
    n = len(standard.features)
    query_window = action_window.get("query") or {}
    query_contrast = float(query_window.get("contrast", 1.0) or 1.0)
    query_has_action = query_contrast >= 1.15 and query_window.get("reason") != "weak_energy_contrast"
    if n < 12 and query_has_action:
        scale = min(0.180, SCORE_SCALE * math.sqrt(18.0 / max(float(n), 1.0)))
        return scale, {
            "base_scale": SCORE_SCALE,
            "effective_scale": scale,
            "reason": "short_action_window_with_query_energy_peak",
            "standard_action_length": n,
            "query_contrast": query_contrast,
        }
    return SCORE_SCALE, {
        "base_scale": SCORE_SCALE,
        "effective_scale": SCORE_SCALE,
        "reason": "default",
        "standard_action_length": n,
        "query_contrast": query_contrast,
    }


def _alignment_policy_for_window(
    full_standard: SequenceData,
    standard_window: Dict[str, Any],
    profile: Optional[SemanticProfile],
) -> Dict[str, Any]:
    full_len = len(full_standard.features)
    action_len = int(standard_window.get("length") or full_len)
    action_ratio = action_len / max(float(full_len), 1.0)
    word = profile.word if profile else None
    short_standard_action = action_len < 12 and full_len <= 24
    if short_standard_action:
        return {
            "mode": "semantic_action_window",
            "used_action_window_for_scoring": True,
            "reason": "short_standard_action_window",
            "word": word,
            "standard_full_length": full_len,
            "standard_action_length": action_len,
            "standard_action_ratio": action_ratio,
        }
    return {
        "mode": "full_sequence_with_action_window_diagnostics",
        "used_action_window_for_scoring": False,
        "reason": "long_or_context_sensitive_action_keep_full_sequence",
        "word": word,
        "standard_full_length": full_len,
        "standard_action_length": action_len,
        "standard_action_ratio": action_ratio,
    }


def _trim_tolerant_scoring_path(
    path: Sequence[Tuple[int, int]],
    local_metrics: Sequence[Sequence[Dict[str, float]]],
    n: int,
    m: int,
) -> Tuple[List[Tuple[int, int]], Dict[str, Any]]:
    if not path:
        return list(path), {"enabled": False}
    length_ratio = min(n, m) / max(n, m, 1)
    if length_ratio < 0.65 or length_ratio > 0.95:
        return list(path), {"enabled": False, "reason": "length_ratio_out_of_range"}

    def path_distance(items: Sequence[Tuple[int, int]]) -> Tuple[float, float]:
        weighted = 0.0
        weight_sum = 0.0
        for i, j in items:
            metrics = local_metrics[i][j]
            pair_weight = float(metrics.get("frame_pair_weight", 1.0))
            weighted += pair_weight * float(metrics.get("weighted", 0.0))
            weight_sum += pair_weight
        return (weighted / max(weight_sum, 1e-6), weight_sum)

    original_distance, original_weight_sum = path_distance(path)
    best_path = list(path)
    best_distance = original_distance
    best_penalized = original_distance
    best_detail: Dict[str, Any] = {
        "enabled": True,
        "used": False,
        "raw_distance": original_distance,
        "raw_path_weight_sum": original_weight_sum,
    }

    max_std_skip = max(0, int(round(n * 0.22)))
    max_qry_skip = max(0, int(round(m * 0.22)))
    min_query_coverage = 0.82
    min_standard_coverage = max(0.62, length_ratio - 0.08)

    for std_prefix in range(max_std_skip + 1):
        for std_suffix in range(max_std_skip + 1 - std_prefix):
            std_lo = std_prefix
            std_hi = n - 1 - std_suffix
            if std_lo > std_hi:
                continue
            for qry_prefix in range(max_qry_skip + 1):
                for qry_suffix in range(max_qry_skip + 1 - qry_prefix):
                    qry_lo = qry_prefix
                    qry_hi = m - 1 - qry_suffix
                    if qry_lo > qry_hi:
                        continue
                    if std_prefix == std_suffix == qry_prefix == qry_suffix == 0:
                        continue
                    selected = [
                        (i, j)
                        for i, j in path
                        if std_lo <= i <= std_hi and qry_lo <= j <= qry_hi
                    ]
                    if not selected:
                        continue
                    std_covered = len({i for i, _ in selected}) / max(n, 1)
                    qry_covered = len({j for _, j in selected}) / max(m, 1)
                    if std_covered < min_standard_coverage or qry_covered < min_query_coverage:
                        continue
                    distance, weight_sum = path_distance(selected)
                    skip_fraction = (std_prefix + std_suffix) / max(n, 1) + (qry_prefix + qry_suffix) / max(m, 1)
                    skip_penalty = 0.018 * skip_fraction
                    penalized = distance + skip_penalty
                    if penalized < best_penalized:
                        best_path = selected
                        best_distance = distance
                        best_penalized = penalized
                        best_detail = {
                            "enabled": True,
                            "used": True,
                            "raw_distance": original_distance,
                            "raw_path_weight_sum": original_weight_sum,
                            "trimmed_distance": distance,
                            "penalized_distance": penalized,
                            "skip_penalty": skip_penalty,
                            "std_prefix_skip": std_prefix,
                            "std_suffix_skip": std_suffix,
                            "query_prefix_skip": qry_prefix,
                            "query_suffix_skip": qry_suffix,
                            "standard_coverage": std_covered,
                            "query_coverage": qry_covered,
                            "path_weight_sum": weight_sum,
                        }

    if best_detail.get("used"):
        return best_path, best_detail
    return list(path), best_detail


def dtw_align(standard: SequenceData, query: SequenceData, profile: Optional[SemanticProfile] = None) -> Dict[str, Any]:
    full_standard = with_dynamic_frame_weights(standard, profile)
    full_query = with_dynamic_frame_weights(query, profile)
    standard_window = _semantic_action_window(full_standard)
    query_window = _semantic_action_window(full_query)
    standard_action = _slice_sequence_window(full_standard, standard_window, "semantic_action_window")
    query_action = _slice_sequence_window(full_query, query_window, "semantic_action_window")
    alignment_policy = _alignment_policy_for_window(full_standard, standard_window, profile)
    if alignment_policy["used_action_window_for_scoring"]:
        standard = standard_action
        query = query_action
        query, temporal_resample = _maybe_resample_query_window(standard, query)
    else:
        standard = full_standard
        query = full_query
        temporal_resample = {
            "used": False,
            "reason": "full_sequence_alignment_policy",
            "ratio": len(query.features) / max(float(len(standard.features)), 1.0),
        }
    n = len(standard.features)
    m = len(query.features)
    local = np.zeros((n, m), dtype=np.float32)
    local_metrics: List[List[Dict[str, float]]] = [[{} for _ in range(m)] for _ in range(n)]
    semantic_dtw_config = _semantic_dtw_config(profile)
    local_phase_weight = float(semantic_dtw_config["local_phase_weight"]) if semantic_dtw_config["enabled"] else 0.0

    for i, a in enumerate(standard.features):
        for j, b in enumerate(query.features):
            dist, metrics = frame_distance(a, b, profile)
            phase_gap = abs(float(a.semantic_phase) - float(b.semantic_phase))
            phase_penalty = local_phase_weight * (phase_gap ** 1.35)
            scoring_dist = dist + phase_penalty
            pair_weight = _pair_temporal_weight(a, b)
            local[i, j] = scoring_dist * pair_weight
            metrics["base_weighted"] = float(dist)
            metrics["semantic_phase_gap"] = phase_gap
            metrics["semantic_phase_penalty"] = phase_penalty
            metrics["frame_pair_weight"] = pair_weight
            metrics["temporal_weighted_distance"] = float(local[i, j])
            metrics["standard_frame_weight"] = float(a.frame_weight)
            metrics["query_frame_weight"] = float(b.frame_weight)
            metrics["standard_semantic_phase"] = float(a.semantic_phase)
            metrics["query_semantic_phase"] = float(b.semantic_phase)
            metrics["weighted"] = float(scoring_dist)
            local_metrics[i][j] = metrics

    acc = np.full((n, m), np.inf, dtype=np.float32)
    back = np.zeros((n, m, 2), dtype=np.int32) - 1
    acc[0, 0] = local[0, 0]
    for i in range(n):
        for j in range(m):
            if i == 0 and j == 0:
                continue
            candidates: List[Tuple[float, int, int]] = []
            if i > 0:
                candidates.append((float(acc[i - 1, j]), i - 1, j))
            if j > 0:
                candidates.append((float(acc[i, j - 1]), i, j - 1))
            if i > 0 and j > 0:
                candidates.append((float(acc[i - 1, j - 1]), i - 1, j - 1))
            best, bi, bj = min(candidates, key=lambda item: item[0])
            acc[i, j] = local[i, j] + best
            back[i, j] = [bi, bj]

    path: List[Tuple[int, int]] = []
    i, j = n - 1, m - 1
    while i >= 0 and j >= 0:
        path.append((i, j))
        pi, pj = back[i, j]
        if pi < 0 or pj < 0:
            break
        i, j = int(pi), int(pj)
    path.reverse()
    raw_path = list(path)

    scoring_path, trim_tolerance = _trim_tolerant_scoring_path(path, local_metrics, n, m)
    path = scoring_path

    metric_keys = [
        "left_hand",
        "right_hand",
        "left_hand_shape",
        "right_hand_shape",
        "left_hand_motion",
        "right_hand_motion",
        "left_hand_shape_motion",
        "right_hand_shape_motion",
        "two_hand_relation",
        "two_hand_relation_motion",
        "pose",
        "face",
        "missing",
        "base_weighted",
        "semantic_phase_gap",
        "semantic_phase_penalty",
        "weighted",
        "hand_side_swapped",
    ]
    group_sums: Dict[str, float] = {key: 0.0 for key in metric_keys}
    worst: List[Dict[str, Any]] = []
    path_weight_sum = 0.0
    for i, j in path:
        metrics = local_metrics[i][j]
        pair_weight = float(metrics.get("frame_pair_weight", 1.0))
        path_weight_sum += pair_weight
        for key in group_sums:
            group_sums[key] += pair_weight * float(metrics.get(key, 0.0))
        worst.append(
            {
                "standard_frame_idx": standard.features[i].frame_idx,
                "query_frame_idx": query.features[j].frame_idx,
                "standard_timestamp_sec": standard.features[i].timestamp_sec,
                "query_timestamp_sec": query.features[j].timestamp_sec,
                "weighted_distance": float(metrics.get("weighted", 0.0)),
                "temporal_weighted_distance": float(metrics.get("temporal_weighted_distance", 0.0)),
                "frame_pair_weight": pair_weight,
                "standard_frame_weight": float(metrics.get("standard_frame_weight", 1.0)),
                "query_frame_weight": float(metrics.get("query_frame_weight", 1.0)),
                "standard_semantic_phase": float(metrics.get("standard_semantic_phase", 0.0)),
                "query_semantic_phase": float(metrics.get("query_semantic_phase", 0.0)),
                "semantic_phase_gap": float(metrics.get("semantic_phase_gap", 0.0)),
                "semantic_phase_penalty": float(metrics.get("semantic_phase_penalty", 0.0)),
                "left_hand_distance": float(metrics.get("left_hand", 0.0)),
                "right_hand_distance": float(metrics.get("right_hand", 0.0)),
                "left_hand_shape_distance": float(metrics.get("left_hand_shape", 0.0)),
                "right_hand_shape_distance": float(metrics.get("right_hand_shape", 0.0)),
                "pose_distance": float(metrics.get("pose", 0.0)),
                "face_distance": float(metrics.get("face", 0.0)),
                "missing_penalty": float(metrics.get("missing", 0.0)),
                "hand_side_swapped": float(metrics.get("hand_side_swapped", 0.0)),
            }
        )

    denom = max(path_weight_sum, 1e-6)
    group_mean = {key: value / denom for key, value in group_sums.items()}
    dtw_distance = float(group_mean.get("weighted", 0.0))
    if trim_tolerance.get("used"):
        dtw_distance = float(trim_tolerance.get("penalized_distance", dtw_distance))
    sequence_penalty = _sequence_penalty(standard, query, group_mean, profile)
    normalized_distance = dtw_distance + float(sequence_penalty["total_sequence_penalty"])
    action_window = {
        "standard": standard_window,
        "query": query_window,
        "used_for_scoring": bool(alignment_policy["used_action_window_for_scoring"]),
    }
    score_scale, score_scale_detail = _score_scale_for_action_window(standard, action_window)
    noise_floor = 0.0
    short_action_tolerance = 0.0
    semantic_phase_trim_tolerance = 0.0
    scoring_length_ratio = min(n, m) / max(n, m, 1)
    if (
        score_scale_detail.get("reason") == "short_action_window_with_query_energy_peak"
        and 0.60 <= scoring_length_ratio <= 1.05
        and dtw_distance < 0.055
        and float(sequence_penalty.get("total_sequence_penalty", 0.0)) > 0.0
    ):
        short_action_tolerance = min(0.045, 0.65 * float(sequence_penalty["total_sequence_penalty"]))
        normalized_distance = max(dtw_distance, normalized_distance - short_action_tolerance)
        sequence_penalty["short_action_subsample_tolerance"] = -short_action_tolerance
        sequence_penalty["total_sequence_penalty_after_tolerance"] = normalized_distance - dtw_distance
    elif (
        not alignment_policy["used_action_window_for_scoring"]
        and 0.70 <= scoring_length_ratio <= 1.0
        and dtw_distance < 0.012
        and float(sequence_penalty.get("total_sequence_penalty", 0.0)) > 0.0
    ):
        # If semantic DTW found a near-identical core path, moderate prefix/suffix
        # trimming should not be treated as a semantic error.
        semantic_phase_trim_tolerance = min(0.018, 0.45 * float(sequence_penalty["total_sequence_penalty"]))
        normalized_distance = max(dtw_distance, normalized_distance - semantic_phase_trim_tolerance)
        sequence_penalty["semantic_phase_trim_tolerance"] = -semantic_phase_trim_tolerance
        sequence_penalty["total_sequence_penalty_after_tolerance"] = normalized_distance - dtw_distance
    semantic_core_query_hand_presence = _semantic_core_hand_presence(query, profile)
    visible_semantic_core_tolerance = 0.0
    if (
        profile is not None
        and float(sequence_penalty.get("hand_dynamic_scale", 1.0)) > 1.0
        and semantic_core_query_hand_presence >= 0.65
        and dtw_distance < 0.045
        and float(sequence_penalty.get("total_sequence_penalty_after_tolerance", sequence_penalty["total_sequence_penalty"])) > 0.0
    ):
        # Real browser captures often have visible semantic skeletons but noisy
        # roughness / semantic-delta summaries due to short occlusions. If the
        # main DTW path is already close, treat most sequence penalties as
        # diagnostics instead of hard errors.
        current_penalty = float(sequence_penalty.get("total_sequence_penalty_after_tolerance", sequence_penalty["total_sequence_penalty"]))
        visible_semantic_core_tolerance = min(float(semantic_dtw_config["visible_core_tolerance_cap"]), 0.82 * current_penalty)
        normalized_distance = max(dtw_distance, normalized_distance - visible_semantic_core_tolerance)
        sequence_penalty["visible_semantic_core_tolerance"] = -visible_semantic_core_tolerance
        sequence_penalty["total_sequence_penalty_after_tolerance"] = normalized_distance - dtw_distance
    core_visible_scale_used = False
    if (
        profile is not None
        and semantic_core_query_hand_presence >= float(semantic_dtw_config["core_visible_presence_threshold"])
        and dtw_distance <= float(semantic_dtw_config["core_visible_dtw_threshold"])
        and normalized_distance <= float(semantic_dtw_config["core_visible_max_normalized_distance"])
        and float(semantic_dtw_config["core_visible_score_scale"]) > score_scale
    ):
        score_scale = float(semantic_dtw_config["core_visible_score_scale"])
        core_visible_scale_used = True
        score_scale_detail["reason"] = "visible_semantic_core_scale"
    if (
        score_scale_detail.get("reason") == "short_action_window_with_query_energy_peak"
        and dtw_distance < 0.060
        and semantic_core_query_hand_presence >= 0.50
    ):
        noise_floor = min(0.020, 0.35 * dtw_distance)
    elif (
        float(sequence_penalty.get("hand_dynamic_scale", 1.0)) > 1.0
        and dtw_distance < 0.025
        and normalized_distance < 0.060
        and semantic_core_query_hand_presence >= 0.60
    ):
        noise_floor = min(0.016, 0.65 * dtw_distance)
    score_distance = max(0.0, normalized_distance - noise_floor)
    prototype_score = float(100.0 * math.exp(-score_distance / score_scale))
    semantic_floor_score, semantic_floor_detail = _jump_relation_semantic_floor(
        standard,
        query,
        group_mean,
        sequence_penalty,
        profile,
        semantic_dtw_config,
    )
    if semantic_floor_score > prototype_score:
        prototype_score = semantic_floor_score
        score_scale_detail["reason"] = "jump_relation_semantic_floor"
    score_scale_detail["effective_scale"] = score_scale
    score_scale_detail["noise_floor_distance"] = noise_floor
    score_scale_detail["short_action_subsample_tolerance"] = short_action_tolerance
    score_scale_detail["semantic_phase_trim_tolerance"] = semantic_phase_trim_tolerance
    score_scale_detail["visible_semantic_core_tolerance"] = visible_semantic_core_tolerance
    score_scale_detail["semantic_core_query_hand_presence"] = semantic_core_query_hand_presence
    score_scale_detail["core_visible_scale_used"] = core_visible_scale_used
    score_scale_detail["semantic_floor_score"] = semantic_floor_score
    score_scale_detail["semantic_floor"] = semantic_floor_detail
    score_scale_detail["score_distance"] = score_distance
    worst_sorted = sorted(worst, key=lambda item: item["temporal_weighted_distance"], reverse=True)[:10]

    return {
        "standard_length": n,
        "query_length": m,
        "standard_full_length": len(full_standard.features),
        "query_full_length": len(full_query.features),
        "alignment_policy": alignment_policy,
        "action_window": action_window,
        "temporal_resample": temporal_resample,
        "score_scale": score_scale_detail,
        "path_length": len(path),
        "raw_path_length": len(raw_path),
        "path_weight_sum": path_weight_sum,
        "trim_tolerance": trim_tolerance,
        "dtw_distance": dtw_distance,
        "normalized_distance": normalized_distance,
        "prototype_score": max(0.0, min(100.0, prototype_score)),
        "sequence_penalty": sequence_penalty,
        "group_mean_distance": group_mean,
        "frame_weight_summary": {
            "standard_full": _frame_weight_summary(full_standard),
            "query_full": _frame_weight_summary(full_query),
            "standard_action": _frame_weight_summary(standard_action),
            "query_action": _frame_weight_summary(query_action),
            "standard_scoring": _frame_weight_summary(standard),
            "query_scoring": _frame_weight_summary(query),
        },
        "semantic_profile": _profile_summary(profile) if profile else None,
        "semantic_dtw": semantic_dtw_config,
        "alignment_path": [
            {
                "standard_frame_idx": standard.features[i].frame_idx,
                "query_frame_idx": query.features[j].frame_idx,
                "standard_timestamp_sec": standard.features[i].timestamp_sec,
                "query_timestamp_sec": query.features[j].timestamp_sec,
                "distance": float(local_metrics[i][j].get("weighted", 0.0)),
                "base_distance": float(local_metrics[i][j].get("base_weighted", local_metrics[i][j].get("weighted", 0.0))),
                "semantic_phase_gap": float(local_metrics[i][j].get("semantic_phase_gap", 0.0)),
                "semantic_phase_penalty": float(local_metrics[i][j].get("semantic_phase_penalty", 0.0)),
                "temporal_weighted_distance": float(local_metrics[i][j].get("temporal_weighted_distance", 0.0)),
                "frame_pair_weight": float(local_metrics[i][j].get("frame_pair_weight", 1.0)),
                "standard_frame_weight": float(local_metrics[i][j].get("standard_frame_weight", 1.0)),
                "query_frame_weight": float(local_metrics[i][j].get("query_frame_weight", 1.0)),
                "standard_semantic_phase": float(local_metrics[i][j].get("standard_semantic_phase", 0.0)),
                "query_semantic_phase": float(local_metrics[i][j].get("query_semantic_phase", 0.0)),
            }
            for i, j in path
        ],
        "worst_alignment_points": worst_sorted,
    }


def _variant(seq: SequenceData, name: str) -> SequenceData:
    items = seq.features
    if name == "self":
        selected = list(items)
    elif name == "subsample_even":
        selected = items[::2] if len(items) > 2 else list(items)
    elif name == "trim_start_20pct":
        cut = max(1, int(round(len(items) * 0.2)))
        selected = items[cut:] or list(items)
    elif name == "trim_end_20pct":
        cut = max(1, int(round(len(items) * 0.2)))
        selected = items[:-cut] or list(items)
    elif name == "middle_60pct":
        cut = max(1, int(round(len(items) * 0.2)))
        selected = items[cut:-cut] or list(items)
    elif name == "trim_both_10pct":
        cut = max(1, int(round(len(items) * 0.1)))
        selected = items[cut:-cut] or list(items)
    elif name.startswith("amplitude_"):
        factor = float(name.split("_", 1)[1])
        selected = []
        for item in items:
            vector = item.vector.copy()
            for group in ["left_hand", "right_hand", "pose"]:
                sl = item.groups[group]
                vector[sl] = vector[sl] * factor
            selected.append(_clone_frame(item, vector=vector))
    elif name == "fake_reverse_time":
        selected = list(reversed(items))
    elif name == "fake_shuffle_frames":
        rng = np.random.default_rng(20260520)
        order = list(range(len(items)))
        rng.shuffle(order)
        selected = [items[idx] for idx in order]
    elif name == "fake_static_hold":
        anchor = items[len(items) // 2]
        selected = [_clone_frame(anchor) for _ in items]
    elif name == "fake_random_landmarks":
        rng = np.random.default_rng(20260521)
        selected = []
        vectors, masks = _visible_matrix(seq)
        visible = masks > 0
        scale = float(np.std(vectors[visible])) if visible.any() else 1.0
        scale = max(scale, 0.35)
        for item in items:
            vector = rng.normal(loc=0.0, scale=scale * 1.8, size=item.vector.shape).astype(np.float32)
            vector = vector * item.mask
            selected.append(_clone_frame(item, vector=vector))
    elif name == "fake_random_walk":
        rng = np.random.default_rng(20260522)
        selected = []
        current = items[0].vector.copy()
        for item in items:
            current = current + rng.normal(loc=0.0, scale=0.35, size=current.shape).astype(np.float32) * item.mask
            selected.append(_clone_frame(item, vector=current * item.mask))
    else:
        raise RuntimeError(f"未知 sanity variant：{name}")
    return _clone_sequence(seq, name, selected)


def _case_row(case_id: str, case_type: str, result: Dict[str, Any], query: SequenceData, expected: str) -> Dict[str, Any]:
    score = float(result["prototype_score"])
    return {
        "case_id": case_id,
        "case_type": case_type,
        "expected": expected,
        "query_source": query.source,
        "query_length": len(query.features),
        "prototype_score": score,
        "dtw_distance": result["dtw_distance"],
        "normalized_distance": result["normalized_distance"],
        "sequence_penalty": result["sequence_penalty"],
        "group_mean_distance": result["group_mean_distance"],
    }


def _parse_labeled_path(value: str) -> Tuple[str, Path]:
    if "=" in value:
        label, raw = value.split("=", 1)
        return label.strip() or Path(raw).stem, Path(raw)
    path = Path(value)
    return path.parent.name or path.stem, path


def _slug(text: str) -> str:
    slug = re.sub(r"[^\w._-]+", "_", text.strip(), flags=re.UNICODE)
    return slug.strip("_") or "case"


def run_discrimination_suite(
    standard: SequenceData,
    negative_jsons: Sequence[str],
    feature_mode: str,
    force_bbox: bool,
    positive_threshold: float,
    negative_threshold: float,
    profile: Optional[SemanticProfile] = None,
) -> Dict[str, Any]:
    cases: List[Dict[str, Any]] = []
    for name in POSITIVE_VARIANTS:
        query = _variant(standard, name)
        result = run_pair(standard, query, semantic_profile=profile)
        cases.append(_case_row(name, "target_positive_variant", result, query, "high"))

    for name in FAKE_VARIANTS:
        query = _variant(standard, name)
        result = run_pair(standard, query, semantic_profile=profile)
        cases.append(_case_row(name, "synthetic_fake_action", result, query, "low"))

    for item in negative_jsons:
        label, path = _parse_labeled_path(item)
        query = load_sequence(path, feature_mode, force_bbox=force_bbox)
        if standard.mode != query.mode:
            query = load_sequence(path, feature_mode, force_bbox=True)
        result = run_pair(standard, query, semantic_profile=profile)
        cases.append(_case_row(f"other_demo_{_slug(label)}", "other_demo_action", result, query, "low"))

    positive_scores = [row["prototype_score"] for row in cases if row["case_type"] == "target_positive_variant"]
    negative_scores = [row["prototype_score"] for row in cases if row["case_type"] != "target_positive_variant"]
    min_positive = min(positive_scores) if positive_scores else None
    max_negative = max(negative_scores) if negative_scores else None
    margin = (min_positive - max_negative) if min_positive is not None and max_negative is not None else None
    gate_pass = bool(
        min_positive is not None
        and max_negative is not None
        and min_positive >= positive_threshold
        and max_negative <= negative_threshold
        and margin is not None
        and margin >= 15.0
    )
    return {
        "positive_threshold": positive_threshold,
        "negative_threshold": negative_threshold,
        "required_margin": 15.0,
        "min_positive_score": min_positive,
        "max_negative_score": max_negative,
        "margin": margin,
        "gate_pass": gate_pass,
        "cases": cases,
    }


def _write_alignment_csv(path: Path, alignment_path: Sequence[Dict[str, Any]]) -> None:
    if not alignment_path:
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(alignment_path[0].keys()))
        writer.writeheader()
        writer.writerows(alignment_path)


def _write_cases_csv(path: Path, cases: Sequence[Dict[str, Any]]) -> None:
    if not cases:
        return
    fields = [
        "case_id",
        "case_type",
        "expected",
        "query_length",
        "prototype_score",
        "dtw_distance",
        "normalized_distance",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in cases:
            writer.writerow({key: row.get(key) for key in fields})


def _build_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# Holistic 序列打分 MVP 结果")
    lines.append("")
    lines.append("## 口径说明")
    lines.append("")
    lines.append("- 本结果是 prototype sanity check，不是已校准的真实用户评分。")
    lines.append("- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。")
    lines.append("- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。")
    lines.append("")
    lines.append("## 输入")
    lines.append("")
    lines.append(f"- 标准序列：`{payload['standard']['source']}`")
    lines.append(f"- 查询序列：`{payload['query']['source']}`")
    lines.append(f"- 特征模式：`{payload['feature_mode']}`")
    lines.append("")
    lines.append("## 主对齐结果")
    lines.append("")
    score = payload["main_result"]["prototype_score"]
    dist = payload["main_result"]["normalized_distance"]
    lines.append(f"- prototype_score：`{score:.3f}`")
    lines.append(f"- dtw_distance：`{payload['main_result']['dtw_distance']:.6f}`")
    lines.append(f"- normalized_distance：`{dist:.6f}`")
    lines.append(f"- DTW path length：`{payload['main_result']['path_length']}`")
    lines.append(f"- sequence_penalty：`{payload['main_result']['sequence_penalty']['total_sequence_penalty']:.6f}`")
    lines.append("")
    lines.append("### 分组平均距离")
    lines.append("")
    for key, value in payload["main_result"]["group_mean_distance"].items():
        lines.append(f"- {key}: `{value:.6f}`")
    lines.append("")
    lines.append("### 最差对齐点")
    lines.append("")
    for item in payload["main_result"]["worst_alignment_points"][:5]:
        lines.append(
            f"- standard frame {item['standard_frame_idx']} vs query frame {item['query_frame_idx']}: "
            f"weighted={item['weighted_distance']:.6f}, "
            f"left={item['left_hand_distance']:.6f}, right={item['right_hand_distance']:.6f}, "
            f"pose={item['pose_distance']:.6f}, missing={item['missing_penalty']:.6f}"
        )
    if payload.get("sanity_results"):
        lines.append("")
        lines.append("## 伪用户 sanity check")
        lines.append("")
        for row in payload["sanity_results"]:
            lines.append(
                f"- {row['variant']}: score=`{row['prototype_score']:.3f}`, "
                f"distance=`{row['normalized_distance']:.6f}`, query_length=`{row['query_length']}`"
            )
    if payload.get("discrimination_suite"):
        suite = payload["discrimination_suite"]
        lines.append("")
        lines.append("## 判别性套件")
        lines.append("")
        lines.append(f"- 正例最低分：`{suite.get('min_positive_score'):.3f}`")
        lines.append(f"- 负例最高分：`{suite.get('max_negative_score'):.3f}`")
        lines.append(f"- 分离 margin：`{suite.get('margin'):.3f}`")
        lines.append(f"- 门控是否通过：`{suite.get('gate_pass')}`")
        lines.append("")
        for row in sorted(suite.get("cases", []), key=lambda item: item["prototype_score"], reverse=True):
            lines.append(
                f"- {row['case_id']} [{row['case_type']}]: "
                f"score=`{row['prototype_score']:.3f}`, "
                f"dtw=`{row['dtw_distance']:.6f}`, "
                f"total_dist=`{row['normalized_distance']:.6f}`, "
                f"expected={row['expected']}"
            )
    lines.append("")
    return "\n".join(lines)


def run_pair(
    standard: SequenceData,
    query: SequenceData,
    semantic_profile: Optional[SemanticProfile] = None,
    semantic_profile_json: Path = DEFAULT_SEMANTIC_PROFILE_JSON,
    disable_semantic_profile: bool = False,
    target_word: Optional[str] = None,
) -> Dict[str, Any]:
    if standard.mode != query.mode:
        raise RuntimeError(f"特征模式不一致：standard={standard.mode}, query={query.mode}")
    profile = semantic_profile
    if profile is None:
        word = target_word or _infer_word_from_source(standard.source)
        profile = load_semantic_profile(word, semantic_profile_json, disabled=disable_semantic_profile)
    return dtw_align(standard, query, profile)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Holistic 序列打分 MVP")
    parser.add_argument("--standard-json", required=True, help="标准样本 Holistic JSON")
    parser.add_argument("--query-json", help="查询样本 Holistic JSON；不传时默认和标准样本相同")
    parser.add_argument("--feature-mode", choices=["auto", "landmark", "bbox"], default="auto")
    parser.add_argument("--force-bbox", action="store_true", help="强制使用 bbox 摘要特征，便于兼容旧 probe JSON")
    parser.add_argument("--run-sanity", action="store_true", help="基于标准序列生成伪用户 sanity variants")
    parser.add_argument("--run-discrimination-suite", action="store_true", help="生成目标动作正例、随机假动作和其他 demo 负例的判别性套件")
    parser.add_argument("--negative-json", action="append", default=[], help="其他 demo 负例 JSON，格式 label=path，可重复传入")
    parser.add_argument("--positive-threshold", type=float, default=75.0, help="判别性套件正例最低分门槛")
    parser.add_argument("--negative-threshold", type=float, default=50.0, help="判别性套件负例最高分门槛")
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON), help="文本语义权重 profile JSON")
    parser.add_argument("--target-word", help="显式指定目标词；默认从 standard-json 路径推断")
    parser.add_argument("--disable-semantic-profile", action="store_true", help="关闭文本语义加权，使用旧的均衡手部优先权重")
    parser.add_argument("--output-dir", default="/data/WYC/signLanguage/work/generated/scoring_mvp_run1")
    args = parser.parse_args(argv)

    standard_path = Path(args.standard_json)
    query_path = Path(args.query_json) if args.query_json else standard_path
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    standard = load_sequence(standard_path, args.feature_mode, force_bbox=args.force_bbox)
    force_bbox = args.force_bbox or standard.mode == "bbox"
    query = load_sequence(query_path, args.feature_mode, force_bbox=force_bbox)
    if standard.mode != query.mode:
        standard = load_sequence(standard_path, args.feature_mode, force_bbox=True)
        query = load_sequence(query_path, args.feature_mode, force_bbox=True)

    profile = load_semantic_profile(
        args.target_word or _infer_word_from_source(standard.source),
        Path(args.semantic_profile_json),
        disabled=args.disable_semantic_profile,
    )
    main_result = run_pair(standard, query, semantic_profile=profile)
    sanity_results: List[Dict[str, Any]] = []
    if args.run_sanity:
        for name in POSITIVE_VARIANTS:
            variant = _variant(standard, name)
            result = run_pair(standard, variant, semantic_profile=profile)
            sanity_results.append(
                {
                    "variant": name,
                    "query_length": result["query_length"],
                    "normalized_distance": result["normalized_distance"],
                    "prototype_score": result["prototype_score"],
                    "group_mean_distance": result["group_mean_distance"],
                }
            )
    discrimination_suite = None
    if args.run_discrimination_suite:
        discrimination_suite = run_discrimination_suite(
            standard=standard,
            negative_jsons=args.negative_json,
            feature_mode=args.feature_mode,
            force_bbox=force_bbox,
            positive_threshold=args.positive_threshold,
            negative_threshold=args.negative_threshold,
            profile=profile,
        )

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "claim_policy": "prototype sanity check only; no calibrated real-user score or pass/fail threshold",
        "feature_mode": standard.mode,
        "semantic_profile": _profile_summary(profile),
        "standard": {
            "source": standard.source,
            "length": len(standard.features),
            "fps": standard.fps,
            "total_frames": standard.total_frames,
            "presence_ratio": _presence_ratio(standard),
        },
        "query": {
            "source": query.source,
            "length": len(query.features),
            "fps": query.fps,
            "total_frames": query.total_frames,
            "presence_ratio": _presence_ratio(query),
        },
        "main_result": main_result,
        "sanity_results": sanity_results,
        "discrimination_suite": discrimination_suite,
    }

    json_path = out_dir / "scoring_mvp_result.json"
    md_path = out_dir / "scoring_mvp_result.md"
    csv_path = out_dir / "alignment_path.csv"
    cases_csv_path = out_dir / "discrimination_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_alignment_csv(csv_path, main_result["alignment_path"])
    if discrimination_suite:
        _write_cases_csv(cases_csv_path, discrimination_suite["cases"])

    print(f"已生成打分结果 JSON：{json_path}")
    print(f"已生成打分结果报告：{md_path}")
    print(f"已生成对齐路径 CSV：{csv_path}")
    if discrimination_suite:
        print(f"已生成判别性套件 CSV：{cases_csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

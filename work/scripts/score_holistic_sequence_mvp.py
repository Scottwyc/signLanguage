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

    frame_idx = int(record.get("frame_idx") if record.get("frame_idx") is not None else record.get("row", {}).get("frame_idx", 0))
    timestamp = float(record.get("timestamp_sec") if record.get("timestamp_sec") is not None else frame_idx / max(fps, 1e-6))
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
    return FrameFeature(frame_idx, timestamp, vector.astype(np.float32), mask.astype(np.float32), groups, presence)


def load_sequence(path: Path, requested_mode: str = "auto", force_bbox: bool = False) -> SequenceData:
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
    )


def _clone_sequence(seq: SequenceData, source_suffix: str, features: Sequence[FrameFeature]) -> SequenceData:
    cloned: List[FrameFeature] = []
    for idx, feature in enumerate(features):
        item = _clone_frame(feature)
        item.frame_idx = idx
        item.timestamp_sec = idx / max(seq.fps, 1e-6)
        cloned.append(item)
    return SequenceData(f"{seq.source}::{source_suffix}", seq.mode, seq.fps, seq.total_frames, cloned)


def _visible_matrix(seq: SequenceData) -> Tuple[np.ndarray, np.ndarray]:
    vectors = np.stack([feature.vector for feature in seq.features], axis=0)
    masks = np.stack([feature.mask for feature in seq.features], axis=0)
    return vectors, masks


def _sequence_groups(seq: SequenceData) -> List[str]:
    if not seq.features:
        return []
    names = list(seq.features[0].groups.keys())
    return [group for group in ["left_hand", "right_hand", "left_hand_shape", "right_hand_shape", "pose", "face"] if group in names]


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
    total = sum(max(0.0, float(raw.get(group, 0.0))) for group in present)
    if total <= 1e-8:
        return _profile_group_weights(_default_semantic_profile(), groups)
    scale = (1.0 - missing) / total
    weights = {group: max(0.0, float(raw.get(group, 0.0))) * scale for group in present}
    weights["missing"] = missing
    return weights


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
    presence_penalty = 0.14 * sum(penalty_weights.get(group, 0.0) * presence_delta[group] for group in presence_delta)

    standard_motion = _sequence_motion_by_group(standard)
    query_motion = _sequence_motion_by_group(query)
    motion_delta = {
        group: min(_safe_log_ratio(float(standard_motion.get(group, 0.0)), float(query_motion.get(group, 0.0))), 3.0)
        for group in _sequence_groups(standard)
    }
    motion_penalty = temporal_profile_factor * 0.025 * sum(penalty_weights.get(group, 0.0) * motion_delta[group] for group in motion_delta)

    standard_roughness = _sequence_roughness_by_group(standard)
    query_roughness = _sequence_roughness_by_group(query)
    roughness_delta = {
        group: min(_safe_log_ratio(float(standard_roughness.get(group, 0.0)), float(query_roughness.get(group, 0.0))), 3.0)
        for group in _sequence_groups(standard)
    }
    # Shuffled or jittery sequences can look locally similar under DTW. Keep a
    # separate temporal roughness penalty so the semantic order is not erased.
    roughness_penalty = temporal_profile_factor * 0.095 * sum(penalty_weights.get(group, 0.0) * roughness_delta[group] for group in roughness_delta)

    info_penalty = 0.0
    if m < 4 and n >= 8:
        info_penalty = 0.16
    elif m < 0.25 * n:
        info_penalty = 0.08

    endpoint_penalty = 0.0
    if length_ratio >= 0.90 and standard.features and query.features:
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

    total_penalty = (
        length_penalty
        + presence_penalty
        + motion_penalty
        + roughness_penalty
        + info_penalty
        + endpoint_penalty
        + confidence_warning_penalty
        + semantic_delta_penalty
    )
    return {
        "length_ratio": length_ratio,
        "length_penalty": length_penalty,
        "temporal_profile_factor": temporal_profile_factor,
        "presence_delta": presence_delta,
        "presence_penalty": presence_penalty,
        "motion_delta": motion_delta,
        "motion_penalty": motion_penalty,
        "roughness_delta": roughness_delta,
        "roughness_penalty": roughness_penalty,
        "info_penalty": info_penalty,
        "endpoint_penalty": endpoint_penalty,
        "confidence_warning_penalty": confidence_warning_penalty,
        "semantic_delta_penalty": semantic_delta_penalty,
        "semantic_delta_detail": semantic_delta_detail,
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
        for raw_key, raw_weight in spec.items():
            try:
                value = max(0.0, float(raw_weight))
            except (TypeError, ValueError):
                continue
            if str(raw_key).isdigit():
                indices = [int(raw_key)]
            else:
                indices = shape_alias.get(str(raw_key), [])
            for idx in indices:
                if 0 <= idx < size:
                    weights[idx] *= value
    return weights


def _weighted_rmse(left: np.ndarray, right: np.ndarray, weights: np.ndarray) -> float:
    weights = np.asarray(weights, dtype=np.float32)
    denom = float(weights.sum())
    if denom <= 1e-8:
        return 0.0
    return float(np.sqrt(np.sum(weights * ((left - right) ** 2)) / denom))


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
        raw_dist = _weighted_rmse(left, right, dim_weights)
        dist = raw_dist
        if metric_group in {"left_hand", "right_hand", "pose"}:
            denom = float(np.dot(dim_weights * right, right))
            if denom > 1e-8:
                alpha = float(np.dot(dim_weights * left, right) / denom)
                alpha = max(0.70, min(1.45, alpha))
                scaled_dist = _weighted_rmse(left, alpha * right, dim_weights)
                scale_penalty = 0.004 * abs(math.log(max(alpha, 1e-6)))
                dist = min(raw_dist, scaled_dist + scale_penalty)
    else:
        dist = 0.0
    missing_penalty = float(mismatch.sum()) / float(either.sum()) if either.any() else 0.0
    return dist, missing_penalty


def _group_distance(a: FrameFeature, b: FrameFeature, group: str, profile: Optional[SemanticProfile] = None) -> Tuple[float, float]:
    return _group_distance_between(a, b, group, group, group, profile)


def frame_distance(a: FrameFeature, b: FrameFeature, profile: Optional[SemanticProfile] = None) -> Tuple[float, Dict[str, float]]:
    group_metrics: Dict[str, float] = {}
    weighted = 0.0
    missing = 0.0
    groups = [group for group in ["left_hand", "right_hand", "left_hand_shape", "right_hand_shape", "pose", "face"] if group in a.groups and group in b.groups]
    weights = _profile_group_weights(profile, groups)

    hand_groups = [group for group in HAND_GROUPS if group in groups]
    non_hand_groups = [group for group in groups if group not in HAND_GROUPS]

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
        }
        for group, (a_group, b_group) in swap_pairs.items():
            if group in hand_groups and a_group in a.groups and b_group in b.groups:
                swapped_hand[group] = _group_distance_between(a, b, a_group, b_group, group, profile)
    direct_weighted = sum(weights.get(group, 0.0) * direct_hand[group][0] for group in direct_hand)
    swapped_weighted = sum(weights.get(group, 0.0) * swapped_hand.get(group, direct_hand.get(group, (0.0, 0.0)))[0] for group in hand_groups)
    use_swapped = bool(swapped_hand) and swapped_weighted < direct_weighted
    selected_hand = swapped_hand if use_swapped else direct_hand

    for group in hand_groups:
        dist, miss = selected_hand.get(group, direct_hand.get(group, (0.0, 0.0)))
        group_metrics[group] = dist
        group_metrics[f"{group}_missing_penalty"] = miss
        weighted += weights.get(group, 0.0) * dist
        missing += miss
    group_metrics["hand_side_swapped"] = 1.0 if use_swapped else 0.0

    for group in non_hand_groups:
        dist, miss = _group_distance(a, b, group, profile)
        group_metrics[group] = dist
        group_metrics[f"{group}_missing_penalty"] = miss
        weighted += weights.get(group, 0.0) * dist
        missing += miss

    missing_denom = max(len(groups), 1)
    missing = missing / missing_denom
    weighted += weights.get("missing", GROUP_WEIGHTS["missing"]) * missing
    group_metrics["missing"] = missing
    group_metrics["weighted"] = weighted
    return weighted, group_metrics


def dtw_align(standard: SequenceData, query: SequenceData, profile: Optional[SemanticProfile] = None) -> Dict[str, Any]:
    n = len(standard.features)
    m = len(query.features)
    local = np.zeros((n, m), dtype=np.float32)
    local_metrics: List[List[Dict[str, float]]] = [[{} for _ in range(m)] for _ in range(n)]

    for i, a in enumerate(standard.features):
        for j, b in enumerate(query.features):
            dist, metrics = frame_distance(a, b, profile)
            local[i, j] = dist
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

    metric_keys = ["left_hand", "right_hand", "left_hand_shape", "right_hand_shape", "pose", "face", "missing", "weighted", "hand_side_swapped"]
    group_sums: Dict[str, float] = {key: 0.0 for key in metric_keys}
    worst: List[Dict[str, Any]] = []
    for i, j in path:
        metrics = local_metrics[i][j]
        for key in group_sums:
            group_sums[key] += float(metrics.get(key, 0.0))
        worst.append(
            {
                "standard_frame_idx": standard.features[i].frame_idx,
                "query_frame_idx": query.features[j].frame_idx,
                "standard_timestamp_sec": standard.features[i].timestamp_sec,
                "query_timestamp_sec": query.features[j].timestamp_sec,
                "weighted_distance": float(metrics.get("weighted", 0.0)),
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

    denom = max(len(path), 1)
    group_mean = {key: value / denom for key, value in group_sums.items()}
    dtw_distance = float(acc[n - 1, m - 1] / denom)
    sequence_penalty = _sequence_penalty(standard, query, group_mean, profile)
    normalized_distance = dtw_distance + float(sequence_penalty["total_sequence_penalty"])
    prototype_score = float(100.0 * math.exp(-normalized_distance / SCORE_SCALE))
    worst_sorted = sorted(worst, key=lambda item: item["weighted_distance"], reverse=True)[:10]

    return {
        "standard_length": n,
        "query_length": m,
        "path_length": len(path),
        "dtw_distance": dtw_distance,
        "normalized_distance": normalized_distance,
        "prototype_score": max(0.0, min(100.0, prototype_score)),
        "sequence_penalty": sequence_penalty,
        "group_mean_distance": group_mean,
        "semantic_profile": _profile_summary(profile) if profile else None,
        "alignment_path": [
            {
                "standard_frame_idx": standard.features[i].frame_idx,
                "query_frame_idx": query.features[j].frame_idx,
                "standard_timestamp_sec": standard.features[i].timestamp_sec,
                "query_timestamp_sec": query.features[j].timestamp_sec,
                "distance": float(local_metrics[i][j].get("weighted", 0.0)),
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

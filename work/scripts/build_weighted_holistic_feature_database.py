#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从原始稀疏 Holistic 分片构建语义加权 DTW 派生数据库。"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
from pathlib import Path

import numpy as np

POSE_CORE_IDS = [0, 11, 12, 13, 14, 15, 16, 23, 24]
FINGER_TIPS = [4, 8, 12, 16, 20]
FINGER_MCPS = [1, 5, 9, 13, 17]
FINGER_PIPS = [2, 6, 10, 14, 18]
SPREAD_PAIRS = [(4, 8), (8, 12), (12, 16), (16, 20)]


def read_raw_shard(path: Path) -> dict:
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            return json.load(handle)
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_frames(payload: dict) -> list[dict]:
    if isinstance(payload.get("frames"), list):
        return payload["frames"]
    frames = []
    for record in payload.get("records") or []:
        result_data = record.get("result_data") or {}
        frames.append({
            "source_frame_idx": int(record.get("frame_idx", 0)),
            "source_timestamp_sec": float(record.get("timestamp_sec", 0.0)),
            "segment_timestamp_sec": float(record.get("segment_timestamp_sec", 0.0)),
            "pose": result_data.get("pose_landmarks") or [],
            "left_hand": result_data.get("left_hand_landmarks") or [],
            "right_hand": result_data.get("right_hand_landmarks") or [],
            "face": result_data.get("face_landmarks") or [],
        })
    return frames


def write_gzip(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8", compresslevel=6) as handle:
        json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))


def points(array, dimensions=3):
    if not array:
        return np.empty((0, dimensions), dtype=np.float32)
    rows = []
    for row in array:
        if isinstance(row, dict):
            rows.append([float(row.get(key, 0.0)) for key in ("x", "y", "z")[:dimensions]])
        else:
            rows.append(row[:dimensions])
    return np.asarray(rows, dtype=np.float32)


def normalize_frame(frame: dict):
    pose_all = points(frame["pose"])
    left = points(frame["left_hand"])
    right = points(frame["right_hand"])
    face = points(frame["face"])
    if len(pose_all) >= 25:
        shoulder_center = (pose_all[11] + pose_all[12]) / 2
        shoulder_width = float(np.linalg.norm(pose_all[11, :2] - pose_all[12, :2]))
        hip_center = (pose_all[23] + pose_all[24]) / 2
        torso = float(np.linalg.norm(shoulder_center[:2] - hip_center[:2]))
        scale = max(shoulder_width, torso, 1e-3)
        center = shoulder_center
    else:
        visible = np.concatenate([value for value in (left, right) if len(value)], axis=0) if len(left) or len(right) else np.zeros((1, 3), dtype=np.float32)
        center = np.median(visible, axis=0)
        scale = max(float(np.linalg.norm(np.ptp(visible[:, :2], axis=0))), 1e-3)
    def norm(value):
        if not len(value):
            return value
        return ((value - center) / scale).astype(np.float32)
    pose_core = norm(pose_all[POSE_CORE_IDS]) if len(pose_all) >= 25 else np.empty((0, 3), dtype=np.float32)
    return pose_core, norm(left), norm(right), norm(face)


def distance(a, b):
    return float(np.linalg.norm(a[:3] - b[:3]))


def straightness(a, b, c):
    left, right = a - b, c - b
    denom = float(np.linalg.norm(left) * np.linalg.norm(right))
    if denom <= 1e-8:
        return 0.0
    cosine = max(-1.0, min(1.0, float(np.dot(left, right) / denom)))
    return (1.0 - cosine) / 2.0


def hand_shape(hand):
    if len(hand) != 21:
        return [0.0] * 19, [0] * 19
    refs = [distance(hand[index], hand[0]) for index in (5, 9, 13, 17)]
    refs.append(distance(hand[5], hand[17]))
    scale = max(float(np.mean(refs)), 1e-3)
    values = []
    for tip in FINGER_TIPS:
        values.append(distance(hand[0], hand[tip]) / scale)
    for first, second in SPREAD_PAIRS:
        values.append(distance(hand[first], hand[second]) / scale)
    for mcp, tip in zip(FINGER_MCPS, FINGER_TIPS):
        values.append(distance(hand[mcp], hand[tip]) / scale)
    for mcp, pip, tip in zip(FINGER_MCPS, FINGER_PIPS, FINGER_TIPS):
        values.append(straightness(hand[mcp], hand[pip], hand[tip]))
    return [round(float(value), 7) for value in values], [1] * len(values)


def two_hand_relation(left, right):
    if len(left) != 21 or len(right) != 21:
        return [0.0] * 8, [0] * 8
    left_ground = left[[0, 5, 9, 13, 17], :2].mean(axis=0)
    right_tips = right[[8, 12], :2].mean(axis=0)
    right_bases = right[[5, 9], :2].mean(axis=0)
    tip_rel = right_tips - left_ground
    base_rel = right_bases - left_ground
    axis = right_tips - right_bases
    values = [tip_rel[0], tip_rel[1], base_rel[0], base_rel[1], axis[0], axis[1], np.linalg.norm(tip_rel), np.linalg.norm(base_rel)]
    return [round(float(value), 7) for value in values], [1] * 8


def flatten(array):
    return [round(float(value), 7) for value in np.asarray(array).reshape(-1)]


def keypoint_vector_weights(group: str, dimension: int, profile: dict, source_ids=None):
    weights = np.ones(dimension, dtype=np.float32)
    keypoints = profile.get("keypoint_weights", {})
    if group in {"left_hand", "right_hand"}:
        hand_rules = dict(keypoints.get("hand", {}))
        hand_rules.update(keypoints.get(group, {}))
        for key, value in hand_rules.items():
            if str(key).isdigit():
                index = int(key)
                if 0 <= index < 21:
                    weights[index * 3:(index + 1) * 3] *= float(value)
    elif group == "pose":
        source_to_local = {source: local for local, source in enumerate(POSE_CORE_IDS)}
        for key, value in keypoints.get("pose", {}).items():
            if str(key).isdigit() and int(key) in source_to_local:
                local = source_to_local[int(key)]
                weights[local * 3:(local + 1) * 3] *= float(value)
    elif group == "face" and source_ids:
        source_to_local = {source: local for local, source in enumerate(source_ids)}
        for key, value in keypoints.get("face", {}).items():
            if str(key).isdigit() and int(key) in source_to_local:
                local = source_to_local[int(key)]
                weights[local * 3:(local + 1) * 3] *= float(value)
    elif group in {"left_hand_shape", "right_hand_shape"}:
        hand_rules = keypoints.get("hand", {})
        if "opening" in hand_rules:
            weights[:5] *= float(hand_rules["opening"])
        if "spread" in hand_rules:
            weights[5:9] *= float(hand_rules["spread"])
    return [round(float(value), 7) for value in weights]


def feature_frame(frame: dict, profile: dict, face_source_ids):
    pose, left, right, face = normalize_frame(frame)
    groups = {
        "pose": flatten(pose) if len(pose) == 9 else [0.0] * 27,
        "left_hand": flatten(left) if len(left) == 21 else [0.0] * 63,
        "right_hand": flatten(right) if len(right) == 21 else [0.0] * 63,
        "face": flatten(face) if len(face) == 12 else [0.0] * 36,
    }
    left_shape, left_shape_mask = hand_shape(left)
    right_shape, right_shape_mask = hand_shape(right)
    relation, relation_mask = two_hand_relation(left, right)
    groups.update({"left_hand_shape": left_shape, "right_hand_shape": right_shape, "two_hand_relation": relation})
    masks = {
        "pose": [1 if len(pose) == 9 else 0] * 27,
        "left_hand": [1 if len(left) == 21 else 0] * 63,
        "right_hand": [1 if len(right) == 21 else 0] * 63,
        "face": [1 if len(face) == 12 else 0] * 36,
        "left_hand_shape": left_shape_mask,
        "right_hand_shape": right_shape_mask,
        "two_hand_relation": relation_mask,
    }
    group_weights = profile["group_weights"]
    semantic = profile.get("semantic_dtw", {})
    relation_weight = float(semantic.get("two_hand_relation_weight", 0.0))
    vector_weights = {}
    for name, values in groups.items():
        base = float(group_weights.get(name, 0.0))
        if name == "two_hand_relation":
            base = relation_weight * min(
                float(group_weights.get("left_hand", 0.0)) + float(group_weights.get("left_hand_shape", 0.0)),
                float(group_weights.get("right_hand", 0.0)) + float(group_weights.get("right_hand_shape", 0.0)),
            )
        point_weights = keypoint_vector_weights(name, len(values), profile, face_source_ids)
        vector_weights[name] = [round(base * value, 8) for value in point_weights]
    return {
        "source_frame_idx": frame["source_frame_idx"],
        "source_timestamp_sec": frame["source_timestamp_sec"],
        "segment_timestamp_sec": frame["segment_timestamp_sec"],
        "feature_groups": groups,
        "masks": masks,
        "vector_weights": vector_weights,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--profiles", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    raw_index = json.loads((args.raw_root / "database_index.json").read_text(encoding="utf-8"))
    profile_data = json.loads(args.profiles.read_text(encoding="utf-8"))
    profiles = profile_data["profiles"]
    face_source_ids = raw_index["landmark_schema"]["face"]["source_ids"]
    raw_manifest = list(csv.DictReader((args.raw_root / "sample_manifest.csv").open(encoding="utf-8-sig")))
    weighted_rows = []
    weighted_words = {word: {"profile": profiles[word], "users": {}} for word in profiles}
    for position, row in enumerate(raw_manifest, start=1):
        raw_shard = args.raw_root / row["landmark_shard"]
        relative_raw = Path(row["landmark_shard"]).relative_to("landmarks")
        out_shard = (args.output_root / "features" / relative_raw).with_suffix(
            relative_raw.suffix + ".gz"
        )
        if args.resume and out_shard.exists() and out_shard.stat().st_size > 0:
            payload = read_raw_shard(out_shard)
        else:
            raw_payload = read_raw_shard(raw_shard)
            word = raw_payload["label"]["standard_word"]
            profile_item = profiles[word]
            feature_frames = [
                feature_frame(frame, profile_item, face_source_ids)
                for frame in canonical_frames(raw_payload)
            ]
            payload = {
                "schema_version": "slu-weighted-holistic-feature-v1",
                "sample_id": raw_payload["sample_id"],
                "review_status": raw_payload["review_status"],
                "raw_landmark_shard": str(raw_shard.relative_to(args.raw_root)),
                "label": raw_payload["label"],
                "hierarchy": raw_payload["hierarchy"],
                "profile_version": profile_data["version"],
                "profile": profile_item,
                "feature_schema": {
                    "pose": "9 core points x xyz, shoulder/torso normalized",
                    "left_hand": "21 points x xyz, shoulder/torso normalized",
                    "right_hand": "21 points x xyz, shoulder/torso normalized",
                    "face": "12 core eye/mouth points x xyz, shoulder/torso normalized",
                    "left_hand_shape": "19 palm-normalized features: 5 wrist-tip + 4 spread + 5 MCP-tip + 5 straightness",
                    "right_hand_shape": "19 palm-normalized features: 5 wrist-tip + 4 spread + 5 MCP-tip + 5 straightness",
                    "two_hand_relation": "8 relative ground/tip/base values",
                },
                "frames": feature_frames,
            }
            write_gzip(out_shard, payload)
        word = payload["label"]["standard_word"]
        user = f"{int(payload['hierarchy']['user_id']):02d}"
        view = payload["hierarchy"]["view"]
        repeat = str(int(payload["label"]["repeat_index"]))
        entry = {
            "sample_id": payload["sample_id"],
            "raw_landmark_shard": payload["raw_landmark_shard"],
            "weighted_feature_shard": str(out_shard.relative_to(args.output_root)),
            "frame_count": len(payload["frames"]),
            "review_status": payload["review_status"],
        }
        weighted_words[word]["users"].setdefault(user, {"views": {}})["views"].setdefault(view, {"repetitions": {}})["repetitions"][repeat] = entry
        weighted_rows.append({"word": word, "user_id": user, "view": view, "repeat_index": repeat, **entry})
        if position % 100 == 0:
            print(f"processed={position}/{len(raw_manifest)}", flush=True)
    args.output_root.mkdir(parents=True, exist_ok=True)
    index = {
        "schema_version": "slu-weighted-dtw-database-v2",
        "database_status": "provisional_pending_manual_cutpoint_and_weight_calibration",
        "raw_database_root": str(args.raw_root.resolve()),
        "profile_path": str(args.profiles.resolve()),
        "profile_version": profile_data["version"],
        "sample_count": len(weighted_rows),
        "words": weighted_words,
    }
    (args.output_root / "weighted_database.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    with (args.output_root / "weighted_sample_manifest.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(weighted_rows[0].keys()))
        writer.writeheader(); writer.writerows(weighted_rows)
    print(json.dumps({"output_root": str(args.output_root), "samples": len(weighted_rows), "words": len(weighted_words)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

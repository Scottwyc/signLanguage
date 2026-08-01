#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""严格验证 21 词语义加权 DTW 派生数据库。"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
from collections import Counter
from pathlib import Path

EXPECTED_DIMS = {
    "pose": 27,
    "left_hand": 63,
    "right_hand": 63,
    "face": 36,
    "left_hand_shape": 19,
    "right_hand_shape": 19,
    "two_hand_relation": 8,
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--raw-root", type=Path, required=True)
    args = parser.parse_args()
    index = json.loads((args.root / "weighted_database.json").read_text(encoding="utf-8"))
    rows = list(csv.DictReader((args.root / "weighted_sample_manifest.csv").open(encoding="utf-8-sig")))
    shards = sorted((args.root / "features").glob("**/*.json.gz"))
    errors = []
    stats = Counter()
    if len(index["words"]) != 21:
        errors.append(f"word_count={len(index['words'])}")
    if index["sample_count"] != 1384 or len(rows) != 1384 or len(shards) != 1384:
        errors.append(f"counts=index:{index['sample_count']},manifest:{len(rows)},shards:{len(shards)}")
    profiles = {word: entry["profile"] for word, entry in index["words"].items()}
    if profiles["汽车（一）"].get("semantic_id") != "汽车_方向盘":
        errors.append("汽车（一）映射错误")
    if profiles["汽车二"].get("semantic_id") != "汽车_车身前行":
        errors.append("汽车二映射错误")
    for word, profile in profiles.items():
        total = sum(float(value) for value in profile["group_weights"].values())
        if abs(total - 1.0) > 1e-6:
            errors.append(f"weight_sum={word}:{total}")

    for row in rows:
        raw_path = args.raw_root / row["raw_landmark_shard"]
        weighted_path = args.root / row["weighted_feature_shard"]
        if not raw_path.exists():
            errors.append(f"missing_raw={row['raw_landmark_shard']}")
        if not weighted_path.exists():
            errors.append(f"missing_weighted={row['weighted_feature_shard']}")
            continue
        if "用户_" not in row["weighted_feature_shard"] or "重复_" not in row["weighted_feature_shard"]:
            errors.append(f"non_chinese_hierarchy={row['weighted_feature_shard']}")
        with gzip.open(weighted_path, "rt", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not payload.get("frames"):
            errors.append(f"empty_frames={weighted_path}")
            continue
        if payload["raw_landmark_shard"] != row["raw_landmark_shard"]:
            errors.append(f"raw_ref_mismatch={weighted_path}")
        for frame in payload["frames"]:
            for group, dimension in EXPECTED_DIMS.items():
                values = frame["feature_groups"][group]
                masks = frame["masks"][group]
                weights = frame["vector_weights"][group]
                if not (len(values) == len(masks) == len(weights) == dimension):
                    errors.append(f"dimension={weighted_path}:{group}:{len(values)}/{len(masks)}/{len(weights)}")
                    continue
                if any(value < 0 for value in weights):
                    errors.append(f"negative_weight={weighted_path}:{group}")
                if sum(masks) == 0 and any(value != 0 for value in values):
                    errors.append(f"masked_nonzero={weighted_path}:{group}")
                stats[f"visible_{group}"] += int(sum(masks) > 0)
            stats["frames"] += 1
        stats["samples"] += 1

    summary = {
        "status": "ok" if not errors else "failed",
        "word_count": len(index["words"]),
        "sample_count": stats["samples"],
        "weighted_shard_count": len(shards),
        "frame_count": stats["frames"],
        "feature_dimensions": EXPECTED_DIMS,
        "visible_frame_groups": {key.removeprefix("visible_"): value for key, value in stats.items() if key.startswith("visible_")},
        "car_variant_mapping": {
            "汽车（一）": profiles["汽车（一）"].get("semantic_id"),
            "汽车二": profiles["汽车二"].get("semantic_id"),
        },
        "validation_error_count": len(errors),
        "errors": errors[:100],
    }
    (args.root / "validation_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

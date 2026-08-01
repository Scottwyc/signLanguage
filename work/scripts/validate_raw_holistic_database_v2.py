#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""严格验证中文目录、普通 JSON、旧坐标兼容格式的原始 Holistic 数据库。"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

EXPECTED_FACE_IDS = [33, 133, 159, 145, 362, 263, 386, 374, 61, 291, 13, 14]
NAMES = ["杨亮颖", "窦佳璐", "王艺涵", "李杭朔", "李盛蕾", "王欣", "吴博洋", "仇佳楠", "吴师印", "王榕", "李卓雅"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root
    index = json.loads((root / "database_index.json").read_text(encoding="utf-8"))
    manifest = list(csv.DictReader((root / "sample_manifest.csv").open(encoding="utf-8-sig")))
    files = sorted((root / "landmarks").glob("**/*.json"))
    errors = []
    stats = Counter()
    missing_frames = 0
    requested_frames = 0
    presence_sums = Counter()

    if len(index["words"]) != 21:
        errors.append(f"word_count={len(index['words'])}")
    if len(manifest) != 1384:
        errors.append(f"manifest_count={len(manifest)}")
    if len(files) != 1384:
        errors.append(f"json_file_count={len(files)}")
    if index["missing_sample_count"] != 2:
        errors.append(f"missing_sample_count={index['missing_sample_count']}")
    missing_keys = {(row["word"], row["user_id"], row["view"], row["repeat_index"]) for row in index["missing_samples"]}
    expected_missing = {("指示", 11, "左30", 1), ("指示", 11, "左30", 2)}
    if missing_keys != expected_missing:
        errors.append(f"unexpected_missing={sorted(missing_keys)}")

    for row in manifest:
        path = root / row["landmark_shard"]
        if not path.exists():
            errors.append(f"missing_file={row['landmark_shard']}")
            continue
        if "用户_" not in row["landmark_shard"] or "重复_" not in row["landmark_shard"]:
            errors.append(f"non_chinese_hierarchy={row['landmark_shard']}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload["schema_version"] != "slu-raw-holistic-segment-v2-legacy-coordinate-compatible":
            errors.append(f"bad_schema={path}")
        if not payload.get("records"):
            errors.append(f"empty_records={path}")
            continue
        schema = payload["landmark_schema"]
        if schema["face"]["source_ids"] != EXPECTED_FACE_IDS:
            errors.append(f"bad_face_ids={path}")
        requested_frames += int(payload["summary"].get("requested_frame_count", 0))
        missing_frames += int(payload["summary"].get("missing_frame_count", 0))
        for record in payload["records"]:
            result = record["result_data"]
            expected = {
                "pose_landmarks": 33,
                "left_hand_landmarks": 21,
                "right_hand_landmarks": 21,
                "face_landmarks": 12,
            }
            for group, count in expected.items():
                values = result[group]
                if len(values) not in (0, count):
                    errors.append(f"bad_cardinality={path}:{group}:{len(values)}")
                if values:
                    presence_sums[group] += 1
                for point in values:
                    required = {"x", "y", "z"}
                    if group == "pose_landmarks":
                        required |= {"visibility", "presence"}
                    if not isinstance(point, dict) or not required.issubset(point):
                        errors.append(f"bad_coordinate={path}:{group}")
                        break
            stats["frames"] += 1
        stats["samples"] += 1

    public_text = (root / "database_index.json").read_text(encoding="utf-8") + (root / "word_database.json").read_text(encoding="utf-8") + (root / "sample_manifest.csv").read_text(encoding="utf-8-sig")
    leaked_names = [name for name in NAMES if name in public_text]
    if leaked_names:
        errors.append(f"public_name_leak={leaked_names}")

    summary = {
        "status": "ok" if not errors else "failed",
        "word_count": len(index["words"]),
        "sample_count": stats["samples"],
        "json_file_count": len(files),
        "frame_count": stats["frames"],
        "missing_sample_count": index["missing_sample_count"],
        "missing_samples": index["missing_samples"],
        "requested_frame_count": requested_frames,
        "missing_frame_count": missing_frames,
        "missing_frame_rate": missing_frames / max(requested_frames, 1),
        "present_frame_groups": dict(presence_sums),
        "public_index_anonymous": not leaked_names,
        "validation_error_count": len(errors),
        "errors": errors[:100],
    }
    (root / "validation_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将超出源视频时长的候选节点剔除，并明确标记尾部截断。"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--segments", type=Path, required=True)
    parser.add_argument("--video-duration", type=float, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    rows = list(csv.DictReader(args.segments.open(encoding="utf-8-sig")))
    kept = [row for row in rows if float(row["start_sec"]) < args.video_duration]
    dropped = [row for row in rows if float(row["start_sec"]) >= args.video_duration]
    if not kept:
        raise SystemExit("no valid segment remains")

    for index, row in enumerate(kept):
        end = float(kept[index + 1]["start_sec"]) if index + 1 < len(kept) else args.video_duration
        row["end_sec"] = f"{end:.4f}"
        row["duration_sec"] = f"{end - float(row['start_sec']):.4f}"
        row["source_integrity"] = "tail_truncated" if index == len(kept) - 1 else "available"
        row["manual_status"] = "candidate_needs_preview_review"

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_csv = args.output_dir / "segments_source_truncated.csv"
    with output_csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(kept[0].keys()))
        writer.writeheader()
        writer.writerows(kept)

    manifest = {
        "status": "source_video_tail_truncated",
        "input_segments": str(args.segments),
        "video_duration_sec": args.video_duration,
        "original_node_count": len(rows),
        "usable_node_count": len(kept),
        "dropped_node_count": len(dropped),
        "dropped_nodes": [
            {
                "word_index": row["word_index"],
                "word": row["word"],
                "repeat_index": row["repeat_index"],
                "start_sec": row["start_sec"],
            }
            for row in dropped
        ],
        "last_usable_segment_partial": True,
        "output_segments": str(output_csv),
    }
    (args.output_dir / "source_truncation_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

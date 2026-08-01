#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Assemble 42-node cutpoint candidates for all volunteers and all views.

Rules:
- left30 uses the approved clear-view migration outputs;
- front/right use their own audio nodes when 42 nodes are detected;
- if a non-left clear view is incomplete, it is migrated from the other complete
  clear view with the target view's audio clusters used only as alignment
  anchors.

This script writes candidate segment CSVs and contact-sheet previews.  It does
not copy or encode source videos.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import auto_cut_voice_prompt_segments as core
import batch_migrate_clear_cutpoints_to_left as batch_migrate
import migrate_clear_view_cutpoints_to_left as migration


VIEW_ORDER = {"正": 0, "左30": 1, "右30": 2}


def volunteer_id(name: str) -> int:
    match = re.match(r"^(\d+)", name)
    return int(match.group(1)) if match else 999


def view_files(folder: Path) -> dict[str, Path]:
    result = {}
    for path in folder.glob("*.mov"):
        result[core.view_name(path)] = path
    return result


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def rows_from_starts(source_path: Path, starts: np.ndarray, duration: float, source: str) -> list[dict]:
    rows = []
    ends = list(starts[1:]) + [duration]
    for idx, (start, end) in enumerate(zip(starts, ends)):
        rows.append(
            {
                "source_path": str(source_path),
                "word_index": idx // 2 + 1,
                "word": core.PINYIN_ORDER[idx // 2],
                "repeat_index": idx % 2 + 1,
                "start_sec": round(float(start), 4),
                "end_sec": round(float(end), 4),
                "duration_sec": round(float(end - start), 4),
                "boundary_source": source,
                "segment_rule": "42node_audio_or_clear_view_migration",
                "manual_status": "candidate_needs_preview_review",
            }
        )
    return rows


def migrate_single_reference(reference: np.ndarray, target_detected: dict, target_video: Path):
    candidates = np.asarray([cluster[0][0] for cluster in target_detected["clusters"]], dtype=np.float64)
    mapped, matches, skipped_expected, skipped_candidates, dp_cost, scale, offset = (
        batch_migrate.align_reference_to_left(reference, candidates)
    )
    return mapped, {
        "scale": scale,
        "offset_sec": offset,
        "matched_anchor_count": len(matches),
        "inferred_node_count": len(skipped_expected),
        "inferred_node_indices": [idx + 1 for idx in skipped_expected],
        "skipped_candidate_count": len(skipped_candidates),
        "skipped_candidate_indices": [idx + 1 for idx in skipped_candidates],
        "dp_cost": dp_cost,
    }


def process_view(
    folder: Path,
    view: str,
    video: Path,
    detected: dict[str, dict],
    migration_root: Path,
    out_root: Path,
) -> dict:
    vid = volunteer_id(folder.name)
    out = out_root / f"{vid:02d}" / view
    out.mkdir(parents=True, exist_ok=True)
    duration = core.video_duration(video)
    manifest = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S %z"),
        "volunteer_id": vid,
        "view": view,
        "video": str(video),
        "duration_sec": duration,
        "expected_nodes": core.EXPECTED_PROMPTS,
    }

    if view == "左30":
        source_segments = migration_root / f"{vid:02d}" / "migration" / "segments.csv"
        if not source_segments.exists():
            raise RuntimeError(f"missing left migration segments: {source_segments}")
        rows = list(csv.DictReader(source_segments.open(encoding="utf-8-sig")))
        for row in rows:
            row["manual_status"] = "candidate_needs_preview_review"
        starts = np.asarray([float(row["start_sec"]) for row in rows], dtype=np.float64)
        source = "left_clear_view_migration"
        manifest["source_mode"] = source
        manifest["migration_segments"] = str(source_segments)
    elif len(detected[view]["prompt_starts"]) == core.EXPECTED_PROMPTS:
        starts = np.asarray(detected[view]["prompt_starts"], dtype=np.float64)
        rows = rows_from_starts(video, starts, duration, "own_audio_42node")
        source = "own_audio_42node"
        manifest["source_mode"] = source
    else:
        other = "右30" if view == "正" else "正"
        if len(detected[other]["prompt_starts"]) != core.EXPECTED_PROMPTS:
            raise RuntimeError(
                f"cannot migrate {view}; other clear view {other} has {len(detected[other]['prompt_starts'])} nodes"
            )
        reference = np.asarray(detected[other]["prompt_starts"], dtype=np.float64)
        starts, diag = migrate_single_reference(reference, detected[view], video)
        rows = rows_from_starts(video, starts, duration, f"migrated_from_{other}")
        source = f"migrated_from_{other}"
        manifest["source_mode"] = source
        manifest["migration_diagnostics"] = diag

    if len(rows) != core.EXPECTED_PROMPTS:
        raise RuntimeError(f"{folder.name} {view}: got {len(rows)} rows")
    if not np.all(np.diff(starts) > 0):
        raise RuntimeError(f"{folder.name} {view}: non-monotonic starts")
    write_csv(out / "segments.csv", rows)
    core.write_preview(video, starts, out / "preview_cutpoints.jpg", migration.labels_for_preview())
    manifest["node_count"] = len(rows)
    manifest["segment_csv"] = str(out / "segments.csv")
    manifest["preview"] = str(out / "preview_cutpoints.jpg")
    (out / "cutpoint_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--left-migration-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)

    folders = sorted(
        [path for path in args.input_root.iterdir() if path.is_dir()],
        key=lambda p: volunteer_id(p.name),
    )
    results = []
    for folder in folders:
        files = view_files(folder)
        detected = {
            view: core.detect_prompts(path, expected=core.EXPECTED_PROMPTS, drop_leading_countdown=True)
            for view, path in files.items()
        }
        for view in sorted(files, key=lambda x: VIEW_ORDER.get(x, 9)):
            try:
                item = process_view(
                    folder,
                    view,
                    files[view],
                    detected,
                    args.left_migration_root,
                    args.output_root,
                )
                item["status"] = "ok"
            except Exception as exc:
                item = {
                    "volunteer_id": volunteer_id(folder.name),
                    "view": view,
                    "status": "failed",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            results.append(item)
            print(
                f"id={item['volunteer_id']} view={view} status={item['status']} "
                f"mode={item.get('source_mode','-')}",
                flush=True,
            )
    summary = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S %z"),
        "view_count": len(results),
        "success_count": sum(item["status"] == "ok" for item in results),
        "failed_count": sum(item["status"] != "ok" for item in results),
        "results": results,
    }
    (args.output_root / "all_views_cutpoint_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({
        "views": len(results),
        "success": summary["success_count"],
        "failed": summary["failed_count"],
        "output_root": str(args.output_root),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()

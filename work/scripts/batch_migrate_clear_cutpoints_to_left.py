#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Batch-transfer clear front/right cue nodes to every left-view video.

The batch uses both clear views when both have 42 detected cue nodes. If one
clear view is incomplete, the complete clear view remains authoritative and
the incomplete one is retained only as diagnostic evidence. Left-view audio is
used solely for monotonic timing alignment, never for word identity/order.
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
import migrate_clear_view_cutpoints_to_left as migration


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


def align_reference_to_left(reference: np.ndarray, left_candidates: np.ndarray):
    # Initialize from the dominant near-diagonal camera offset. Starting from
    # zero can fail when the left list contains an early false cluster.
    near_diffs = []
    for ref_sec in reference:
        local = left_candidates[np.abs(left_candidates - ref_sec) <= 0.80]
        near_diffs.extend(float(value - ref_sec) for value in local)
    if near_diffs:
        bins = {}
        for value in near_diffs:
            key = round(value / 0.05) * 0.05
            bins[key] = bins.get(key, 0) + 1
        offset = float(max(bins, key=bins.get))
    else:
        offset = float(left_candidates[0] - reference[0])
    scale = 1.0
    for _ in range(6):
        predicted = scale * reference + offset
        matches, _, _, _ = migration.monotonic_align(predicted, left_candidates)
        if len(matches) < 2:
            raise RuntimeError("not enough left anchors")
        x = np.asarray([reference[i] for i, _ in matches], dtype=np.float64)
        y = np.asarray([left_candidates[j] for _, j in matches], dtype=np.float64)
        new_scale, new_offset, _ = migration.fit_affine(x, y)
        if abs(new_scale - scale) < 1e-8 and abs(new_offset - offset) < 1e-6:
            scale, offset = new_scale, new_offset
            break
        scale, offset = new_scale, new_offset
    mapped = scale * reference + offset
    matches, skipped_expected, skipped_candidates, dp_cost = migration.monotonic_align(
        mapped, left_candidates
    )
    return mapped, matches, skipped_expected, skipped_candidates, dp_cost, scale, offset


def process_one(folder: Path, output_root: Path) -> dict:
    vid = volunteer_id(folder.name)
    files = view_files(folder)
    required = {"正", "右30", "左30"}
    if not required.issubset(files):
        return {
            "volunteer_id": vid,
            "status": "failed",
            "error": f"missing views: {sorted(required - set(files))}",
        }

    detected = {
        view: core.detect_prompts(
            path, expected=core.EXPECTED_PROMPTS, drop_leading_countdown=True
        )
        for view, path in files.items()
    }
    front = np.asarray(detected["正"]["prompt_starts"], dtype=np.float64)
    right = np.asarray(detected["右30"]["prompt_starts"], dtype=np.float64)
    if len(front) == core.EXPECTED_PROMPTS and len(right) == core.EXPECTED_PROMPTS:
        consensus, consensus_diag = migration.consensus_reference(front, right)
        # Equal counts alone are insufficient: an early false/missed cluster
        # can shift the same-index pairing. Keep the right view authoritative
        # when front/right agreement is not tight.
        if (
            consensus_diag["front_right_residual_mean_abs_sec"] <= 0.15
            and consensus_diag["front_right_residual_max_abs_sec"] <= 0.80
        ):
            reference = consensus
            reference_diag = consensus_diag
            reference_mode = "front_right_consensus"
        else:
            reference = right
            reference_diag = {
                "fallback_reason": "front_right_same_index_alignment_unstable",
                "consensus_probe": consensus_diag,
                "front_count": int(len(front)),
                "right_count": int(len(right)),
            }
            reference_mode = "right_only_front_alignment_unstable"
    elif len(right) == core.EXPECTED_PROMPTS:
        reference = right
        reference_mode = "right_only_front_incomplete"
        reference_diag = {
            "front_count": int(len(front)),
            "right_count": int(len(right)),
        }
    elif len(front) == core.EXPECTED_PROMPTS:
        reference = front
        reference_mode = "front_only_right_incomplete"
        reference_diag = {
            "front_count": int(len(front)),
            "right_count": int(len(right)),
        }
    else:
        return {
            "volunteer_id": vid,
            "status": "failed",
            "error": f"no complete clear view: front={len(front)}, right={len(right)}",
        }

    left_candidates = np.asarray(
        [cluster[0][0] for cluster in detected["左30"]["clusters"]],
        dtype=np.float64,
    )
    (
        mapped,
        matches,
        skipped_expected,
        skipped_candidates,
        dp_cost,
        scale,
        offset,
    ) = align_reference_to_left(reference, left_candidates)

    out = output_root / f"{vid:02d}" / "migration"
    out.mkdir(parents=True, exist_ok=True)
    duration = core.video_duration(files["左30"])
    anchor_by_index = {}
    diagnostics = []
    for ref_idx, candidate_idx in matches:
        residual = float(left_candidates[candidate_idx] - mapped[ref_idx])
        item = {
            "node_index": ref_idx + 1,
            "word": core.PINYIN_ORDER[ref_idx // 2],
            "repeat_index": ref_idx % 2 + 1,
            "reference_sec": float(reference[ref_idx]),
            "migrated_left_sec": float(mapped[ref_idx]),
            "left_candidate_index": candidate_idx + 1,
            "left_candidate_sec": float(left_candidates[candidate_idx]),
            "residual_sec": residual,
            "anchor_status": "matched_left_audio_anchor",
        }
        anchor_by_index[ref_idx] = item
        diagnostics.append(item)
    for ref_idx in skipped_expected:
        diagnostics.append(
            {
                "node_index": ref_idx + 1,
                "word": core.PINYIN_ORDER[ref_idx // 2],
                "repeat_index": ref_idx % 2 + 1,
                "reference_sec": float(reference[ref_idx]),
                "migrated_left_sec": float(mapped[ref_idx]),
                "left_candidate_index": "",
                "left_candidate_sec": "",
                "residual_sec": "",
                "anchor_status": "inferred_missing_left_audio_node",
            }
        )
    diagnostics.sort(key=lambda row: int(row["node_index"]))
    rows = migration.build_rows(files["左30"], mapped, duration, anchor_by_index)
    write_csv(out / "segments.csv", rows)
    write_csv(out / "alignment_diagnostics.csv", diagnostics)
    core.write_preview(
        files["左30"],
        mapped,
        out / "preview_migrated_front_right_consensus.jpg",
        migration.labels_for_preview(),
    )
    residuals = [
        abs(float(row["residual_sec"]))
        for row in diagnostics
        if row["anchor_status"] == "matched_left_audio_anchor"
    ]
    manifest = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S %z"),
        "volunteer_id": vid,
        "status": "ok",
        "reference_mode": reference_mode,
        "reference_diagnostics": reference_diag,
        "source_files": {view: str(path) for view, path in files.items()},
        "detected_counts": {
            view: len(data["prompt_starts"]) for view, data in detected.items()
        },
        "left_from_reference_affine": {"scale": scale, "offset_sec": offset},
        "migrated_node_count": len(mapped),
        "matched_left_anchor_count": len(matches),
        "inferred_left_node_count": len(skipped_expected),
        "inferred_node_indices": [idx + 1 for idx in skipped_expected],
        "skipped_left_candidate_count": len(skipped_candidates),
        "skipped_left_candidate_indices": [idx + 1 for idx in skipped_candidates],
        "alignment_dp_cost": dp_cost,
        "mean_abs_anchor_residual_sec": float(np.mean(residuals)) if residuals else None,
        "max_abs_anchor_residual_sec": float(np.max(residuals)) if residuals else None,
        "left_video_duration_sec": duration,
        "output_dir": str(out),
    }
    (out / "migration_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    folders = sorted(
        [path for path in args.input_root.iterdir() if path.is_dir()],
        key=lambda path: volunteer_id(path.name),
    )
    results = []
    for index, folder in enumerate(folders, 1):
        try:
            result = process_one(folder, args.output_root)
        except Exception as exc:
            result = {
                "volunteer_id": volunteer_id(folder.name),
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
            }
        results.append(result)
        print(
            f"[{index}/{len(folders)}] id={result['volunteer_id']} "
            f"status={result['status']} "
            f"nodes={result.get('migrated_node_count', 0)}",
            flush=True,
        )
    summary = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S %z"),
        "video_group_count": len(results),
        "success_count": sum(row["status"] == "ok" for row in results),
        "failed_count": sum(row["status"] != "ok" for row in results),
        "results": results,
    }
    (args.output_root / "batch_migration_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({
        "groups": len(results),
        "success": summary["success_count"],
        "failed": summary["failed_count"],
        "output_root": str(args.output_root),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()

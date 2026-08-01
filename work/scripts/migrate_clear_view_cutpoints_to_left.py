#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Transfer front/right clear-audio segmentation nodes to a left-view video.

This is a privacy-preserving boundary migration utility for the sign-language
universe recordings.  It does not copy/encode any raw video.  It reads the
existing front/right manifests, forms a two-view consensus timeline, then
estimates a monotonic affine mapping onto the left view using the left audio
activity clusters only as alignment anchors.

The important distinction is:
  - word identity/order and all 42 canonical cue indices come from clear views;
  - left audio is used only to estimate camera offset/drift and validate the
    migrated timeline, never as the authority for ASR labels.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import auto_cut_voice_prompt_segments as core


def load_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def fit_affine(x: np.ndarray, y: np.ndarray) -> tuple[float, float, np.ndarray]:
    """Iteratively fit y=a*x+b after rejecting large residual anchors."""
    if len(x) < 2:
        raise ValueError("need at least two alignment anchors")
    keep = np.ones(len(x), dtype=bool)
    a, b = 1.0, float(np.median(y - x))
    for _ in range(8):
        a, b = np.polyfit(x[keep], y[keep], 1)
        residual = y - (a * x + b)
        median = float(np.median(residual[keep]))
        mad = float(np.median(np.abs(residual[keep] - median))) + 1e-6
        threshold = max(0.30, 3.0 * 1.4826 * mad)
        new_keep = np.abs(residual - median) <= threshold
        if np.array_equal(new_keep, keep):
            break
        keep = new_keep
    return float(a), float(b), keep


def monotonic_align(
    predicted: np.ndarray,
    candidates: np.ndarray,
    match_scale_sec: float = 0.25,
    skip_expected_cost: float = 1.20,
    skip_candidate_cost: float = 1.20,
) -> tuple[list[tuple[int, int]], list[int], list[int], float]:
    """Needleman-Wunsch-style timing alignment of expected and observed nodes."""
    n, m = len(predicted), len(candidates)
    cost = np.full((n + 1, m + 1), np.inf)
    back: list[list[tuple[str, int, int] | None]] = [
        [None] * (m + 1) for _ in range(n + 1)
    ]
    cost[0, 0] = 0.0
    for i in range(n + 1):
        for j in range(m + 1):
            current = cost[i, j]
            if not math.isfinite(current):
                continue
            if i < n and current + skip_expected_cost < cost[i + 1, j]:
                cost[i + 1, j] = current + skip_expected_cost
                back[i + 1][j] = ("skip_expected", i, j)
            if j < m and current + skip_candidate_cost < cost[i, j + 1]:
                cost[i, j + 1] = current + skip_candidate_cost
                back[i][j + 1] = ("skip_candidate", i, j)
            if i < n and j < m:
                # Cap the per-match cost so true missing nodes can be skipped.
                match_cost = min(
                    abs(float(predicted[i] - candidates[j])) / match_scale_sec, 4.0
                )
                if current + match_cost < cost[i + 1, j + 1]:
                    cost[i + 1, j + 1] = current + match_cost
                    back[i + 1][j + 1] = ("match", i, j)

    i, j = n, m
    matches: list[tuple[int, int]] = []
    skipped_expected: list[int] = []
    skipped_candidates: list[int] = []
    while i > 0 or j > 0:
        item = back[i][j]
        if item is None:
            raise RuntimeError("alignment backtrace failed")
        kind, prev_i, prev_j = item
        if kind == "match":
            matches.append((prev_i, prev_j))
        elif kind == "skip_expected":
            skipped_expected.append(prev_i)
        else:
            skipped_candidates.append(prev_j)
        i, j = prev_i, prev_j
    return (
        list(reversed(matches)),
        list(reversed(skipped_expected)),
        list(reversed(skipped_candidates)),
        float(cost[n, m]),
    )


def consensus_reference(front: np.ndarray, right: np.ndarray) -> tuple[np.ndarray, dict]:
    """Express right timeline in front coordinates and form a two-view mean."""
    if len(front) != len(right):
        raise ValueError(f"front/right node count mismatch: {len(front)} vs {len(right)}")
    a, b, keep = fit_affine(front, right)
    right_in_front_time = (right - b) / a
    consensus = (front + right_in_front_time) / 2.0
    residual = right - (a * front + b)
    return consensus, {
        "right_from_front_affine": {"scale": a, "offset_sec": b},
        "front_right_anchor_count": int(keep.sum()),
        "front_right_residual_mean_abs_sec": float(np.mean(np.abs(residual))),
        "front_right_residual_max_abs_sec": float(np.max(np.abs(residual))),
    }


def labels_for_preview() -> list[dict]:
    labels = []
    for index in range(core.EXPECTED_PROMPTS):
        labels.append(
            {
                "recognized_standard_word": core.PINYIN_ORDER[index // 2],
                "assignment_confidence": "manual",
            }
        )
    return labels


def build_rows(
    left_path: Path,
    starts: np.ndarray,
    duration_sec: float,
    anchor_by_index: dict[int, dict],
) -> list[dict]:
    ends = list(starts[1:]) + [duration_sec]
    rows = []
    for index, (start, end) in enumerate(zip(starts, ends)):
        anchor = anchor_by_index.get(index)
        rows.append(
            {
                "source_path": str(left_path),
                "word_index": index // 2 + 1,
                "word": core.PINYIN_ORDER[index // 2],
                "repeat_index": index % 2 + 1,
                "start_sec": round(float(start), 4),
                "end_sec": round(float(end), 4),
                "duration_sec": round(float(end - start), 4),
                "boundary_source": (
                    "left_audio_alignment_anchor"
                    if anchor is not None
                    else "front_right_consensus_interpolated"
                ),
                "left_anchor_sec": (
                    round(float(anchor["left_candidate_sec"]), 4) if anchor else ""
                ),
                "left_anchor_residual_sec": (
                    round(float(anchor["residual_sec"]), 4) if anchor else ""
                ),
                "segment_rule": "front_right_consensus_mapped_to_left_affine",
                "view_alignment_status": "migrated_from_clear_front_right_consensus",
                "manual_status": "candidate_needs_preview_review",
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--front-manifest", type=Path, required=True)
    parser.add_argument("--right-manifest", type=Path, required=True)
    parser.add_argument("--left-manifest", type=Path, required=True)
    parser.add_argument("--left-video", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    front_data = load_manifest(args.front_manifest)
    right_data = load_manifest(args.right_manifest)
    left_data = load_manifest(args.left_manifest)
    front = np.asarray(front_data["detected"]["prompt_starts"], dtype=np.float64)
    right = np.asarray(right_data["detected"]["prompt_starts"], dtype=np.float64)

    # Use raw clusters for matching: the noisy left routine can include a
    # spurious early cluster and miss real prompts, which is exactly why it is
    # not used as an ASR/word-order authority.
    left_candidates = np.asarray(
        [cluster[0][0] for cluster in left_data["detected"]["clusters"]],
        dtype=np.float64,
    )
    reference, consensus_diag = consensus_reference(front, right)

    scale, offset = 1.0, 0.0
    for _ in range(6):
        predicted = scale * reference + offset
        matches, skipped_expected, skipped_candidates, dp_cost = monotonic_align(
            predicted, left_candidates
        )
        if len(matches) < 2:
            raise RuntimeError("not enough left-audio anchors after monotonic alignment")
        x = np.asarray([reference[i] for i, _ in matches], dtype=np.float64)
        y = np.asarray([left_candidates[j] for _, j in matches], dtype=np.float64)
        new_scale, new_offset, keep = fit_affine(x, y)
        if abs(new_scale - scale) < 1e-8 and abs(new_offset - offset) < 1e-6:
            scale, offset = new_scale, new_offset
            break
        scale, offset = new_scale, new_offset

    mapped = scale * reference + offset
    matches, skipped_expected, skipped_candidates, dp_cost = monotonic_align(
        mapped, left_candidates
    )
    anchor_by_index = {}
    diagnostics = []
    for reference_index, candidate_index in matches:
        residual = float(left_candidates[candidate_index] - mapped[reference_index])
        entry = {
            "node_index": reference_index + 1,
            "word": core.PINYIN_ORDER[reference_index // 2],
            "repeat_index": reference_index % 2 + 1,
            "front_sec": float(front[reference_index]),
            "right_sec": float(right[reference_index]),
            "consensus_reference_sec": float(reference[reference_index]),
            "migrated_left_sec": float(mapped[reference_index]),
            "left_candidate_index": candidate_index + 1,
            "left_candidate_sec": float(left_candidates[candidate_index]),
            "residual_sec": residual,
            "anchor_status": "matched_left_audio_anchor",
        }
        anchor_by_index[reference_index] = entry
        diagnostics.append(entry)
    for reference_index in skipped_expected:
        diagnostics.append(
            {
                "node_index": reference_index + 1,
                "word": core.PINYIN_ORDER[reference_index // 2],
                "repeat_index": reference_index % 2 + 1,
                "front_sec": float(front[reference_index]),
                "right_sec": float(right[reference_index]),
                "consensus_reference_sec": float(reference[reference_index]),
                "migrated_left_sec": float(mapped[reference_index]),
                "left_candidate_index": "",
                "left_candidate_sec": "",
                "residual_sec": "",
                "anchor_status": "inferred_missing_left_audio_node",
            }
        )
    diagnostics.sort(key=lambda item: item["node_index"])

    duration = core.video_duration(args.left_video)
    if len(mapped) != core.EXPECTED_PROMPTS:
        raise AssertionError(f"expected {core.EXPECTED_PROMPTS} mapped nodes, got {len(mapped)}")
    if not np.all(np.diff(mapped) > 0):
        raise AssertionError("migrated starts are not strictly increasing")
    if mapped[0] <= 0 or mapped[-1] >= duration:
        raise AssertionError("migrated starts fall outside left video duration")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows = build_rows(args.left_video, mapped, duration, anchor_by_index)
    write_csv(args.output_dir / "segments.csv", rows)
    write_csv(args.output_dir / "alignment_diagnostics.csv", diagnostics)
    core.write_preview(
        args.left_video,
        mapped,
        args.output_dir / "preview_migrated_front_right_consensus.jpg",
        labels_for_preview(),
    )

    residuals = np.asarray(
        [item["residual_sec"] for item in diagnostics if item["anchor_status"] == "matched_left_audio_anchor"],
        dtype=np.float64,
    )
    manifest = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S %z"),
        "method": "front_right_consensus_affine_migration_with_left_audio_anchor_validation",
        "privacy": "raw audio and video are read-only; outputs contain only boundaries, diagnostics and preview frames",
        "front_manifest": str(args.front_manifest),
        "right_manifest": str(args.right_manifest),
        "left_manifest": str(args.left_manifest),
        "left_video": str(args.left_video),
        "expected_node_count": core.EXPECTED_PROMPTS,
        "migrated_node_count": int(len(mapped)),
        "left_video_duration_sec": float(duration),
        "front_right_consensus": consensus_diag,
        "left_from_consensus_affine": {"scale": float(scale), "offset_sec": float(offset)},
        "left_audio_candidate_count": int(len(left_candidates)),
        "matched_left_audio_anchor_count": int(len(matches)),
        "inferred_missing_left_audio_node_count": int(len(skipped_expected)),
        "skipped_left_audio_candidate_count": int(len(skipped_candidates)),
        "inferred_node_indices": [index + 1 for index in skipped_expected],
        "skipped_left_candidate_indices": [index + 1 for index in skipped_candidates],
        "alignment_dp_cost": float(dp_cost),
        "matched_anchor_mean_abs_residual_sec": float(np.mean(np.abs(residuals))),
        "matched_anchor_max_abs_residual_sec": float(np.max(np.abs(residuals))),
        "outputs": {
            "segments_csv": str(args.output_dir / "segments.csv"),
            "alignment_diagnostics_csv": str(args.output_dir / "alignment_diagnostics.csv"),
            "preview": str(args.output_dir / "preview_migrated_front_right_consensus.jpg"),
        },
    }
    (args.output_dir / "migration_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

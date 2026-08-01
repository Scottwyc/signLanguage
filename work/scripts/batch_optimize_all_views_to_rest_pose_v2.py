#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""并行批量将全部视角候选切割点微调到最邻近的手臂贴身静止姿态帧。"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

VIEW_ORDER = {"正": 0, "左30": 1, "右30": 2}
REQUIRED_OUTPUTS = (
    "segments_pose_rest_optimized.csv",
    "boundary_pose_rest_diagnostics.csv",
    "preview_pose_rest_optimized_boundaries.jpg",
    "pose_rest_optimization_manifest.json",
)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def output_complete(path: Path) -> bool:
    return all((path / name).exists() for name in REQUIRED_OUTPUTS)


def validate_output(path: Path) -> dict:
    segments = list(csv.DictReader(
        (path / "segments_pose_rest_optimized.csv").open(encoding="utf-8-sig")
    ))
    diagnostics = list(csv.DictReader(
        (path / "boundary_pose_rest_diagnostics.csv").open(encoding="utf-8-sig")
    ))
    if len(segments) != 42:
        raise RuntimeError(f"segment count is {len(segments)}, expected 42")
    if len(diagnostics) != 43:
        raise RuntimeError(f"boundary count is {len(diagnostics)}, expected 43")
    for index, row in enumerate(segments):
        start, end = float(row["start_sec"]), float(row["end_sec"])
        if end <= start:
            raise RuntimeError(f"segment {index + 1} has invalid range {start}..{end}")
        if index + 1 < len(segments):
            next_start = float(segments[index + 1]["start_sec"])
            if abs(end - next_start) > 1e-4:
                raise RuntimeError(f"segment {index + 1} is not continuous")
    manifest = read_json(path / "pose_rest_optimization_manifest.json")
    if int(manifest.get("segment_count", 0)) != 42:
        raise RuntimeError("manifest segment_count is not 42")
    if int(manifest.get("boundary_count", 0)) != 43:
        raise RuntimeError("manifest boundary_count is not 43")
    return manifest


def process_item(item: dict, args: argparse.Namespace) -> dict:
    volunteer_id, view = int(item["volunteer_id"]), item["view"]
    output_dir = args.output_root / f"{volunteer_id:02d}" / view
    result = {
        "volunteer_id": volunteer_id,
        "view": view,
        "source_mode": item.get("source_mode"),
        "status": "pending",
    }
    try:
        if args.resume and output_complete(output_dir):
            manifest = validate_output(output_dir)
            result["execution"] = "resumed_existing"
        else:
            output_dir.mkdir(parents=True, exist_ok=True)
            command = [
                args.python, str(args.optimizer),
                "--video", item["video"],
                "--segments", item["segment_csv"],
                "--output-dir", str(output_dir),
                "--window-sec", str(args.window_sec),
                "--time-weight", str(args.time_weight),
                "--max-width", str(args.max_width),
            ]
            completed = subprocess.run(
                command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            (output_dir / "optimizer_stdout.log").write_text(
                completed.stdout, encoding="utf-8"
            )
            manifest = validate_output(output_dir)
            result["execution"] = "computed"
        result.update({
            "status": "ok",
            "segment_count": int(manifest["segment_count"]),
            "boundary_count": int(manifest["boundary_count"]),
            "pose_valid_boundary_count": int(manifest["pose_valid_boundary_count"]),
            "mean_abs_shift_sec": manifest["shift_summary_sec"]["mean_abs"],
            "max_abs_shift_sec": manifest["shift_summary_sec"]["max_abs"],
            "segments_csv": str(output_dir / "segments_pose_rest_optimized.csv"),
            "diagnostics_csv": str(output_dir / "boundary_pose_rest_diagnostics.csv"),
            "preview": str(output_dir / "preview_pose_rest_optimized_boundaries.jpg"),
        })
    except Exception as exc:
        result["status"] = "failed"
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def write_summary(args: argparse.Namespace, source_count: int, results: list[dict]) -> dict:
    ordered = sorted(results, key=lambda item: (
        int(item["volunteer_id"]), VIEW_ORDER[item["view"]]
    ))
    summary = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S %z"),
        "method": "audio_or_migration_then_holistic_pose_rest_refinement",
        "candidate_root": str(args.candidate_root),
        "window_sec": args.window_sec,
        "time_weight": args.time_weight,
        "jobs": args.jobs,
        "view_count": source_count,
        "processed_count": len(ordered),
        "success_count": sum(row["status"] == "ok" for row in ordered),
        "failed_count": sum(row["status"] == "failed" for row in ordered),
        "results": ordered,
    }
    (args.output_root / "all_views_pose_rest_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--optimizer", type=Path, required=True)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--window-sec", type=float, default=0.65)
    parser.add_argument("--time-weight", type=float, default=0.12)
    parser.add_argument("--max-width", type=int, default=640)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    source_summary = read_json(args.candidate_root / "all_views_cutpoint_summary.json")
    source_items = [item for item in source_summary["results"] if item.get("status") == "ok"]
    source_items.sort(key=lambda item: (int(item["volunteer_id"]), VIEW_ORDER[item["view"]]))
    args.output_root.mkdir(parents=True, exist_ok=True)

    results = []
    with ThreadPoolExecutor(max_workers=args.jobs) as executor:
        futures = {executor.submit(process_item, item, args): item for item in source_items}
        for position, future in enumerate(as_completed(futures), start=1):
            result = future.result()
            results.append(result)
            write_summary(args, len(source_items), results)
            print(
                f"[{position:02d}/{len(source_items):02d}] id={result['volunteer_id']:02d} "
                f"view={result['view']} status={result['status']} "
                f"execution={result.get('execution', '-')}",
                flush=True,
            )

    summary = write_summary(args, len(source_items), results)
    if summary["failed_count"]:
        raise SystemExit(1)
    print(json.dumps({
        "views": summary["view_count"],
        "success": summary["success_count"],
        "failed": summary["failed_count"],
        "output_root": str(args.output_root),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()

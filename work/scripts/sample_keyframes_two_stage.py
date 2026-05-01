#!/usr/bin/env python3
"""
两阶段关键帧采样。

策略特点：
1. 先做全视频粗采样，保证尾部覆盖
2. 再把剩余预算倾斜到高运动区间
3. 对动作开始较晚的视频，比前段截断采样更稳
"""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from keyframe_sampling_common import (
    DEFAULT_VIDEO_ROOT,
    build_candidate_cache,
    build_report,
    configure_headless,
    even_frame_indices,
    get_candidate_video_entry,
    load_candidate_cache,
    select_two_stage_keyframes,
    summarize_rows,
    segment_score,
)
from signlanguage_common import find_demo_videos, probe_video_metadata


DEFAULT_OUTPUT_DIR = Path("/data/WYC/signLanguage/work/generated/keyframe_sampling_two_stage")
DEFAULT_SAMPLE_BUDGET = 12


def build_two_stage_indices(
    video_path: Path,
    sample_budget: int,
    candidate_step: int = 4,
    short_video_threshold: int = 48,
    candidate_cache_path: Optional[Path] = None,
    workers: int = 1,
) -> Dict[str, Any]:
    """基于候选缓存执行两阶段选择。"""

    started = time.perf_counter()
    if candidate_cache_path is not None:
        cache_payload = load_candidate_cache(candidate_cache_path)
        candidate_entry = get_candidate_video_entry(cache_payload, video_path.name)
        candidate_generation_sec = 0.0
    else:
        candidate_build_start = time.perf_counter()
        candidate_entry = build_candidate_cache(
            video_path,
            candidate_step=candidate_step,
            short_video_full_threshold=short_video_threshold,
            workers=workers if workers and workers > 0 else 1,
            result_dir=Path("/data/WYC/signLanguage/work/generated/keyframe_sampling_two_stage_candidates") / video_path.stem,
        )
        candidate_generation_sec = round(time.perf_counter() - candidate_build_start, 3)

    candidate_rows = candidate_entry["rows"]
    meta = candidate_entry.get("meta") or candidate_entry or probe_video_metadata(video_path)
    total_frames = int(
        candidate_entry.get("candidate_summary", {}).get("video_total_frames")
        or candidate_entry.get("total_frames")
        or len(candidate_rows)
    )
    coarse_count = min(max(6, sample_budget // 2 + 1), sample_budget, len(candidate_rows))
    coarse_indices = [int(candidate_rows[pos]["frame_idx"]) for pos in even_frame_indices(len(candidate_rows), coarse_count) if 0 <= pos < len(candidate_rows)]
    notes = [
        f"候选点数：{len(candidate_rows)}",
        "先在候选缓存上粗扫，再将剩余预算分配给高分区间。",
    ]

    selection_start = time.perf_counter()
    final_indices = select_two_stage_keyframes(candidate_rows, sample_budget)
    selection_sec = round(time.perf_counter() - selection_start, 3)
    selected_rows_map = {int(row["frame_idx"]): row for row in candidate_rows}
    selected_rows = [selected_rows_map[idx] for idx in final_indices if idx in selected_rows_map]
    candidate_summary = candidate_entry.get("candidate_summary") or summarize_rows(meta, total_frames, candidate_rows)
    selected_summary = summarize_rows(meta, total_frames, selected_rows)
    combined_sec = round(candidate_generation_sec + selection_sec, 3)
    return {
        "video": video_path.name,
        "video_path": str(video_path),
        "candidate_frame_indices": candidate_entry.get("candidate_frame_indices", []),
        "coarse_indices": coarse_indices,
        "sampled_frame_indices": final_indices,
        "sampled_timestamps_sec": [row["timestamp_sec"] for row in selected_rows],
        "candidate_summary": candidate_summary,
        "evaluation": selected_summary,
        "rows": selected_rows,
        "strategy_notes": notes + [
            "额外采样优先落在高运动区间与更宽的空隙里。",
        ],
        "candidate_generation_sec": candidate_generation_sec,
        "selection_sec": selection_sec,
        "combined_sec": combined_sec,
        "processing_sec": combined_sec,
        "candidate_cache_file": str(candidate_cache_path) if candidate_cache_path is not None else candidate_entry.get("candidate_result_file"),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    configure_headless()
    started = time.perf_counter()

    parser = argparse.ArgumentParser(description="两阶段关键帧采样")
    parser.add_argument("--video-root", default=str(DEFAULT_VIDEO_ROOT), help="视频目录")
    parser.add_argument("--video", action="append", help="单个视频路径，可重复传入")
    parser.add_argument("--sample-budget", type=int, default=DEFAULT_SAMPLE_BUDGET, help="采样帧预算")
    parser.add_argument("--candidate-step", type=int, default=4, help="候选采样步长")
    parser.add_argument("--short-video-threshold", type=int, default=48, help="短视频阈值，低于该帧数时使用全量 dense 候选")
    parser.add_argument("--candidate-cache", help="候选缓存 JSON，提供后将只做选择不再生成候选")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="输出目录")
    parser.add_argument("--workers", type=int, default=0, help="并行进程数，0 表示使用 CPU 核数")
    args = parser.parse_args(argv)

    video_root = Path(args.video_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.video:
        videos = [Path(v) for v in args.video]
    else:
        videos = find_demo_videos(video_root)

    worker_count = args.workers if args.workers and args.workers > 0 else (os.cpu_count() or 1)
    if len(videos) <= 1 or worker_count <= 1:
        results = [build_two_stage_indices(video_path, args.sample_budget, args.candidate_step, args.short_video_threshold, Path(args.candidate_cache) if args.candidate_cache else None, worker_count) for video_path in videos]
    else:
        results = [None] * len(videos)  # type: ignore[list-item]
        with ProcessPoolExecutor(max_workers=min(worker_count, len(videos))) as executor:
            futures = {
                executor.submit(
                    build_two_stage_indices,
                    video_path,
                    args.sample_budget,
                    args.candidate_step,
                    args.short_video_threshold,
                    Path(args.candidate_cache) if args.candidate_cache else None,
                    worker_count,
                ): idx
                for idx, video_path in enumerate(videos)
            }
            for future in as_completed(futures):
                results[futures[future]] = future.result()
        results = [row for row in results if row is not None]
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "elapsed_sec": round(time.perf_counter() - started, 3),
        "combined_sec": round(sum(row.get("combined_sec", 0.0) for row in results), 3),
        "strategy": "two_stage",
        "sample_budget": args.sample_budget,
        "candidate_step": args.candidate_step,
        "output_dir": str(output_dir),
        "videos": results,
    }

    json_path = output_dir / "two_stage_sampling.json"
    md_path = output_dir / "two_stage_sampling.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(build_report(payload, "两阶段关键帧采样实验"), encoding="utf-8")
    print(f"已生成两阶段采样 JSON：{json_path}")
    print(f"已生成两阶段采样报告：{md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

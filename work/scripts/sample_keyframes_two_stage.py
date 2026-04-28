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
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from keyframe_sampling_common import (
    DEFAULT_VIDEO_ROOT,
    build_report,
    choose_interior_frame,
    configure_headless,
    even_frame_indices,
    extract_holistic_rows,
    normalize_total_frames,
    rows_to_map,
    segment_score,
)
from signlanguage_common import find_demo_videos, probe_video_metadata


DEFAULT_OUTPUT_DIR = Path("/data/WYC/signLanguage/work/generated/keyframe_sampling_two_stage")
DEFAULT_SAMPLE_BUDGET = 12


def build_two_stage_indices(video_path: Path, sample_budget: int) -> Dict[str, Any]:
    """生成两阶段采样帧。"""

    started = time.perf_counter()
    meta = probe_video_metadata(video_path)
    total_frames = normalize_total_frames(meta)
    coarse_count = min(max(6, sample_budget // 2 + 1), sample_budget, total_frames)
    coarse_indices = even_frame_indices(total_frames, coarse_count)
    pilot = extract_holistic_rows(video_path, coarse_indices)
    row_map = rows_to_map(pilot["rows"])

    selected = set(coarse_indices)
    notes = [
        f"粗采样点数：{len(coarse_indices)}",
        "先全视频粗扫，再将剩余预算分配给高运动区间。",
    ]

    if len(selected) < sample_budget and len(coarse_indices) > 1:
        segments = []
        for left, right in zip(coarse_indices[:-1], coarse_indices[1:]):
            score = segment_score(left, right, row_map, total_frames)
            segments.append((score, left, right))
        segments.sort(reverse=True)

        # 第一轮：优先给高分区间各放一个中点。
        for _, left, right in segments:
            if len(selected) >= sample_budget:
                break
            cand = choose_interior_frame(left, right, selected)
            if cand is not None:
                selected.add(cand)

        # 第二轮：如果预算仍然有剩，优先填补当前最宽的空隙。
        while len(selected) < sample_budget:
            ordered = sorted(selected)
            gaps = [(b - a, a, b) for a, b in zip(ordered[:-1], ordered[1:]) if b - a > 1]
            if not gaps:
                break
            gaps.sort(reverse=True)
            _, left, right = gaps[0]
            cand = choose_interior_frame(left, right, selected)
            if cand is None:
                break
            selected.add(cand)

    final_indices = sorted(selected)
    evaluated = extract_holistic_rows(video_path, final_indices)
    evaluated["summary"]["strategy"] = "two_stage"
    return {
        "video": video_path.name,
        "video_path": str(video_path),
        "coarse_indices": coarse_indices,
        "sampled_frame_indices": final_indices,
        "sampled_timestamps_sec": [row["timestamp_sec"] for row in evaluated["rows"]],
        "evaluation": evaluated["summary"],
        "rows": evaluated["rows"],
        "strategy_notes": notes + [
            "额外采样优先落在高运动区间与更宽的空隙里。",
        ],
        "processing_sec": round(time.perf_counter() - started, 3),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    configure_headless()
    started = time.perf_counter()

    parser = argparse.ArgumentParser(description="两阶段关键帧采样")
    parser.add_argument("--video-root", default=str(DEFAULT_VIDEO_ROOT), help="视频目录")
    parser.add_argument("--video", action="append", help="单个视频路径，可重复传入")
    parser.add_argument("--sample-budget", type=int, default=DEFAULT_SAMPLE_BUDGET, help="采样帧预算")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="输出目录")
    args = parser.parse_args(argv)

    video_root = Path(args.video_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.video:
        videos = [Path(v) for v in args.video]
    else:
        videos = find_demo_videos(video_root)

    results = [build_two_stage_indices(video_path, args.sample_budget) for video_path in videos]
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "elapsed_sec": round(time.perf_counter() - started, 3),
        "strategy": "two_stage",
        "sample_budget": args.sample_budget,
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

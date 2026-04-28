#!/usr/bin/env python3
"""
全视频均匀关键帧采样。

策略特点：
- 按整段视频等间距取样
- 直接覆盖到首帧和末帧
- 作为后续两阶段 / 自适应采样的基线
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
    configure_headless,
    even_frame_indices,
    extract_holistic_rows,
)
from signlanguage_common import find_demo_videos


DEFAULT_OUTPUT_DIR = Path("/data/WYC/signLanguage/work/generated/keyframe_sampling_uniform")
DEFAULT_SAMPLE_BUDGET = 12


def build_video_result(video_path: Path, sample_budget: int) -> Dict[str, Any]:
    """生成单视频的均匀采样结果。"""

    started = time.perf_counter()
    probe = extract_holistic_rows(video_path, [])
    total_frames = int(probe["summary"]["video_total_frames"])
    indices = even_frame_indices(total_frames, sample_budget)
    evaluated = extract_holistic_rows(video_path, indices)
    evaluated["summary"]["strategy"] = "uniform"
    return {
        "video": video_path.name,
        "video_path": str(video_path),
        "sampled_frame_indices": indices,
        "sampled_timestamps_sec": [row["timestamp_sec"] for row in evaluated["rows"]],
        "evaluation": evaluated["summary"],
        "rows": evaluated["rows"],
        "strategy_notes": [
            "全视频均匀采样，首尾都覆盖。",
            "适合作为后续两阶段 / 自适应采样的基线。",
        ],
        "processing_sec": round(time.perf_counter() - started, 3),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    configure_headless()
    started = time.perf_counter()

    parser = argparse.ArgumentParser(description="全视频均匀关键帧采样")
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

    results: List[Dict[str, Any]] = [build_video_result(video_path, args.sample_budget) for video_path in videos]
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "elapsed_sec": round(time.perf_counter() - started, 3),
        "strategy": "uniform",
        "sample_budget": args.sample_budget,
        "output_dir": str(output_dir),
        "videos": results,
    }

    json_path = output_dir / "uniform_sampling.json"
    md_path = output_dir / "uniform_sampling.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(build_report(payload, "全视频均匀关键帧采样实验"), encoding="utf-8")
    print(f"已生成均匀采样 JSON：{json_path}")
    print(f"已生成均匀采样报告：{md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

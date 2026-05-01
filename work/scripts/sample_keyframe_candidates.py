#!/usr/bin/env python3
"""
候选关键帧生成层。

职责：
- 先按短视频 / 长视频规则生成候选帧索引
- 只做一次 Holistic 评估
- 将候选结果落成缓存文件，供后续选择策略复用
"""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from keyframe_sampling_common import (
    DEFAULT_VIDEO_ROOT,
    build_candidate_cache,
    build_candidate_indices,
    build_report,
    configure_headless,
    load_candidate_cache,
    normalize_total_frames,
    probe_video_metadata,
    summarize_rows,
)
from signlanguage_common import find_demo_videos


DEFAULT_OUTPUT_DIR = Path("/data/WYC/signLanguage/work/generated/keyframe_candidates")
DEFAULT_CANDIDATE_STEP = 4
DEFAULT_SHORT_VIDEO_THRESHOLD = 48


def build_video_candidate(
    video_path: Path,
    candidate_step: int,
    short_video_threshold: int,
    workers: int,
    output_dir: Path,
) -> Dict[str, Any]:
    """生成单视频的候选缓存。"""

    started = time.perf_counter()
    meta = probe_video_metadata(video_path)
    total_frames = normalize_total_frames(meta)
    candidate_indices, candidate_mode = build_candidate_indices(total_frames, candidate_step, short_video_threshold)
    candidate_build_start = time.perf_counter()
    result_dir = output_dir / video_path.stem
    candidate_cache = build_candidate_cache(
        video_path,
        candidate_step=candidate_step,
        short_video_full_threshold=short_video_threshold,
        workers=workers,
        result_dir=result_dir,
    )
    candidate_generation_sec = round(time.perf_counter() - candidate_build_start, 3)
    candidate_cache["candidate_mode"] = candidate_mode
    candidate_cache["candidate_frame_indices"] = candidate_indices
    candidate_cache["candidate_summary"] = summarize_rows(meta, total_frames, candidate_cache["rows"])
    candidate_cache["elapsed_sec"] = round(time.perf_counter() - started, 3)
    candidate_cache["candidate_generation_sec"] = candidate_generation_sec
    candidate_cache["candidate_result_file"] = candidate_cache.get("cache_summary", {}).get("holistic_result_file")
    return candidate_cache


def _build_report(payload: Dict[str, Any]) -> str:
    row = payload["video_result"]
    candidate = row["candidate_summary"]
    cache_summary = row["cache_summary"]

    lines = []
    lines.append("# 候选关键帧生成层")
    lines.append("")
    lines.append(f"- 对象视频：`{payload.get('video_name')}`")
    lines.append(f"- 候选步长：每 `{payload.get('candidate_step')}` 帧采 1 帧")
    lines.append(f"- 短视频阈值：`{payload.get('short_video_threshold')}` 帧")
    lines.append(f"- 候选模式：`{row.get('candidate_mode')}`")
    lines.append("")
    lines.append("## 结果")
    lines.append("")
    lines.append(f"- 候选帧数：{candidate.get('samples')}")
    lines.append(f"- 候选索引：{', '.join(str(x) for x in row.get('candidate_frame_indices', []))}")
    lines.append(f"- 候选缓存文件：{row.get('candidate_result_file')}")
    lines.append(f"- 候选生成耗时：{row.get('candidate_generation_sec')}s")
    lines.append(f"- Holistic 初始化耗时：{cache_summary.get('holistic_init_sec')}s")
    lines.append(f"- Holistic 识别耗时：{cache_summary.get('holistic_eval_sec')}s")
    lines.append(f"- Holistic 总墙钟耗时：{cache_summary.get('holistic_wall_sec')}s")
    lines.append("")
    lines.append("## 说明")
    lines.append("")
    lines.append("- 该层只负责生成候选缓存，不进行关键帧选择。")
    lines.append("- 后续选择策略直接复用这里生成的候选缓存，避免重复跑 Holistic。")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    configure_headless()
    started = time.perf_counter()

    parser = argparse.ArgumentParser(description="候选关键帧生成层")
    parser.add_argument("--video-root", default=str(DEFAULT_VIDEO_ROOT), help="视频目录")
    parser.add_argument("--video", action="append", help="单个视频路径，可重复传入")
    parser.add_argument("--candidate-step", type=int, default=DEFAULT_CANDIDATE_STEP, help="候选采样步长")
    parser.add_argument(
        "--short-video-threshold",
        type=int,
        default=DEFAULT_SHORT_VIDEO_THRESHOLD,
        help="短视频阈值，低于该帧数时使用全量 dense 候选",
    )
    parser.add_argument("--workers", type=int, default=1, help="并行进程数，默认单进程以避免重复初始化")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="输出目录")
    args = parser.parse_args(argv)

    video_root = Path(args.video_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.video:
        videos = [Path(v) for v in args.video]
    else:
        videos = find_demo_videos(video_root)

    worker_count = args.workers if args.workers and args.workers > 0 else 1
    if len(videos) <= 1 or worker_count <= 1:
        results = [build_video_candidate(video_path, args.candidate_step, args.short_video_threshold, worker_count, output_dir) for video_path in videos]
    else:
        results = [None] * len(videos)  # type: ignore[list-item]
        with ProcessPoolExecutor(max_workers=min(worker_count, len(videos))) as executor:
            futures = {
                executor.submit(build_video_candidate, video_path, args.candidate_step, args.short_video_threshold, worker_count, output_dir): idx
                for idx, video_path in enumerate(videos)
            }
            for future in as_completed(futures):
                results[futures[future]] = future.result()
        results = [row for row in results if row is not None]

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "elapsed_sec": round(time.perf_counter() - started, 3),
        "candidate_step": args.candidate_step,
        "short_video_threshold": args.short_video_threshold,
        "output_dir": str(output_dir),
        "videos": results,
    }

    json_path = output_dir / "candidate_cache.json"
    md_path = output_dir / "candidate_cache.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_build_report(payload), encoding="utf-8")
    print(f"已生成候选缓存 JSON：{json_path}")
    print(f"已生成候选缓存报告：{md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

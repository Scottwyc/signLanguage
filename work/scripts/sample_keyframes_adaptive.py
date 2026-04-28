#!/usr/bin/env python3
"""
自适应关键帧采样。

策略特点：
1. 先做全视频 pilot 采样
2. 再根据当前采样点的内容把预算递归塞进更值得细采样的区间
3. 更适合动作开始较晚或动作密度不均匀的视频
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


DEFAULT_OUTPUT_DIR = Path("/data/WYC/signLanguage/work/generated/keyframe_sampling_adaptive")
DEFAULT_SAMPLE_BUDGET = 12


def _proxy_row_from_segment(left_row: Dict[str, Any], right_row: Dict[str, Any], frame_idx: int, fps: float) -> Dict[str, Any]:
    """为递归阶段构造一个轻量代理行，避免每次都重新跑 Holistic。"""

    motion_left = float(left_row.get("motion_energy", 0.0))
    motion_right = float(right_row.get("motion_energy", 0.0))
    return {
        "frame_idx": frame_idx,
        "timestamp_sec": frame_idx / fps,
        "pose_present": bool(left_row.get("pose_present")) or bool(right_row.get("pose_present")),
        "left_hand_present": bool(left_row.get("left_hand_present")) or bool(right_row.get("left_hand_present")),
        "right_hand_present": bool(left_row.get("right_hand_present")) or bool(right_row.get("right_hand_present")),
        "face_present": bool(left_row.get("face_present")) or bool(right_row.get("face_present")),
        "motion_energy": max(motion_left, motion_right) * 0.85 + 0.15 * min(motion_left, motion_right),
    }


def build_adaptive_indices(video_path: Path, sample_budget: int) -> Dict[str, Any]:
    """生成自适应采样帧。"""

    started = time.perf_counter()
    meta = probe_video_metadata(video_path)
    total_frames = normalize_total_frames(meta)
    pilot_count = min(max(5, sample_budget // 2), sample_budget, total_frames)
    selected = set(even_frame_indices(total_frames, pilot_count))

    pilot = extract_holistic_rows(video_path, sorted(selected))
    row_map = rows_to_map(pilot["rows"])
    notes = [
        f"pilot 点数：{len(selected)}",
        "先用全视频 pilot 点估计内容分布，再递归拆分高价值区间。",
    ]

    while len(selected) < sample_budget:
        ordered = sorted(selected)
        segments = []
        for left, right in zip(ordered[:-1], ordered[1:]):
            if right - left <= 1:
                continue
            score = segment_score(left, right, row_map, total_frames)
            segments.append((score, left, right))

        if not segments:
            break

        segments.sort(reverse=True)
        _, left, right = segments[0]
        cand = choose_interior_frame(left, right, selected)
        if cand is None:
            break

        selected.add(cand)
        # 把新中点纳入后续区间评分，但只用代理特征更新，避免每次都重新跑 Holistic。
        row_map[cand] = _proxy_row_from_segment(row_map[left], row_map[right], cand, float(meta.get("fps") or 25.0))

    final_indices = sorted(selected)
    evaluated = extract_holistic_rows(video_path, final_indices)
    evaluated["summary"]["strategy"] = "adaptive"
    return {
        "video": video_path.name,
        "video_path": str(video_path),
        "pilot_indices": sorted(pilot["summary"]["sampled_frame_indices"]),
        "sampled_frame_indices": final_indices,
        "sampled_timestamps_sec": [row["timestamp_sec"] for row in evaluated["rows"]],
        "evaluation": evaluated["summary"],
        "rows": evaluated["rows"],
        "strategy_notes": notes + [
            "每次优先拆分当前最值得继续细采样的区间。",
        ],
        "processing_sec": round(time.perf_counter() - started, 3),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    configure_headless()
    started = time.perf_counter()

    parser = argparse.ArgumentParser(description="自适应关键帧采样")
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

    results = [build_adaptive_indices(video_path, args.sample_budget) for video_path in videos]
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "elapsed_sec": round(time.perf_counter() - started, 3),
        "strategy": "adaptive",
        "sample_budget": args.sample_budget,
        "output_dir": str(output_dir),
        "videos": results,
    }

    json_path = output_dir / "adaptive_sampling.json"
    md_path = output_dir / "adaptive_sampling.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(build_report(payload, "自适应关键帧采样实验"), encoding="utf-8")
    print(f"已生成自适应采样 JSON：{json_path}")
    print(f"已生成自适应采样报告：{md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

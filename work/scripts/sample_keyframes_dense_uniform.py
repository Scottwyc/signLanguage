#!/usr/bin/env python3
"""
能量覆盖率筛选实验。

策略思路：
1. 先按固定步长对整段视频做密采样，例如每 4 帧取 1 帧。
2. 对这批密采样帧一次性跑 Holistic，保存结果文件。
3. 再从密采样结果里均匀筛出目标数量的关键帧，例如 12 帧。

这个方法的核心假设是：
- 不需要把采样决策设计得很复杂
- 只要先把候选帧覆盖得足够密，再从结果里筛就可以
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
    build_candidate_cache,
    configure_headless,
    get_candidate_video_entry,
    load_candidate_cache,
    select_energy_coverage_keyframes,
    summarize_rows,
)
from signlanguage_common import find_demo_videos


DEFAULT_OUTPUT_DIR = Path("/data/WYC/signLanguage/work/generated/keyframe_sampling_dense_uniform_step4_single")
DEFAULT_SAMPLE_BUDGET = 12
DEFAULT_DENSE_STEP = 4
STRATEGY_DISPLAY_NAME = "能量覆盖率筛选"


def build_energy_coverage_result(
    video_path: Path,
    dense_step: int,
    sample_budget: int,
    workers: int = 0,
    candidate_cache_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """基于候选 Holistic 缓存执行能量覆盖率筛选。"""

    started = time.perf_counter()
    if candidate_cache_path is not None:
        cache_payload = load_candidate_cache(candidate_cache_path)
        candidate_entry = get_candidate_video_entry(cache_payload, video_path.name)
        candidate_generation_sec = 0.0
    else:
        candidate_build_start = time.perf_counter()
        candidate_entry = build_candidate_cache(
            video_path,
            candidate_step=dense_step,
            short_video_full_threshold=48,
            workers=workers if workers and workers > 0 else 1,
            result_dir=DEFAULT_OUTPUT_DIR / video_path.stem,
        )
        candidate_generation_sec = round(time.perf_counter() - candidate_build_start, 3)

    candidate_rows = candidate_entry["rows"]
    meta = candidate_entry.get("meta") or candidate_entry or {}
    total_frames = int(
        candidate_entry.get("candidate_summary", {}).get("video_total_frames")
        or candidate_entry.get("total_frames")
        or len(candidate_rows)
    )

    selection_start = time.perf_counter()
    selected_indices = select_energy_coverage_keyframes(candidate_rows, sample_budget)
    selection_sec = round(time.perf_counter() - selection_start, 3)
    row_map = {int(row["frame_idx"]): row for row in candidate_rows}
    selected_rows = [row_map[idx] for idx in selected_indices if idx in row_map]

    dense_summary = candidate_entry.get("candidate_summary") or summarize_rows(meta, total_frames, candidate_rows)
    selected_summary = summarize_rows(meta, total_frames, selected_rows)
    dense_holistic_wall_sec = round(float(candidate_entry.get("cache_summary", {}).get("holistic_wall_sec") or 0.0), 3)
    dense_holistic_init_sec = round(float(candidate_entry.get("cache_summary", {}).get("holistic_init_sec") or 0.0), 3)
    dense_holistic_eval_sec = round(float(candidate_entry.get("cache_summary", {}).get("holistic_eval_sec") or 0.0), 3)
    dense_result_file = candidate_entry.get("candidate_result_file") or candidate_entry.get("cache_summary", {}).get("holistic_result_file")
    dense_indices = [int(x) for x in candidate_entry.get("candidate_frame_indices", [])]
    combined_sec = round(candidate_generation_sec + selection_sec, 3)

    return {
        "video": video_path.name,
        "video_path": str(video_path),
        "dense_step": dense_step,
        "dense_frame_indices": dense_indices,
        "selected_frame_indices": selected_indices,
        "dense_summary": dense_summary,
        "selected_summary": selected_summary,
        "dense_holistic_wall_sec": dense_holistic_wall_sec,
        "dense_holistic_init_sec": dense_holistic_init_sec,
        "dense_holistic_eval_sec": dense_holistic_eval_sec,
        "selection_sec": selection_sec,
        "candidate_generation_sec": candidate_generation_sec,
        "worker_count": workers if workers and workers > 0 else 1,
        "result_file": dense_result_file,
        "candidate_cache_file": str(candidate_cache_path) if candidate_cache_path is not None else dense_result_file,
        "processing_sec": combined_sec,
        "combined_sec": combined_sec,
    }


def _build_report(payload: Dict[str, Any]) -> str:
    """生成能量覆盖率筛选实验报告。"""

    row = payload["video_result"]
    dense = row["dense_summary"]
    selected = row["selected_summary"]

    lines: List[str] = []
    lines.append("# 能量覆盖率筛选实验")
    lines.append("")
    lines.append(f"- 对象视频：`{payload.get('video_name')}`")
    lines.append(f"- 密采样步长：每 `{payload.get('dense_step')}` 帧采 1 帧")
    lines.append(f"- 目标筛选帧数：{payload.get('sample_budget')}")
    lines.append("")
    lines.append("## 方法")
    lines.append("")
    lines.append("- 先对整段视频做固定步长密采样。")
    lines.append("- 对密采样帧一次性跑 Holistic，保留全部结果。")
    lines.append("- 再从密采样结果里先按运动能量取一半，再按双手覆盖率取一半；重复帧则继续往后补。")
    lines.append("")
    lines.append("## 结果")
    lines.append("")
    lines.append(f"- 密采样帧数：{dense.get('samples')}")
    lines.append(f"- 最终筛选帧数：{selected.get('samples')}")
    lines.append(f"- 候选生成耗时：{row.get('candidate_generation_sec')}s")
    lines.append(f"- 密采样 Holistic 初始化总耗时：{row.get('dense_holistic_init_sec')}s")
    lines.append(f"- 密采样 Holistic 识别总耗时：{row.get('dense_holistic_eval_sec')}s")
    lines.append(f"- 密采样 Holistic 总墙钟耗时：{row.get('dense_holistic_wall_sec')}s")
    lines.append(f"- 关键帧筛选耗时：{row.get('selection_sec')}s")
    lines.append(f"- 并行 worker 数：{row.get('worker_count')}")
    lines.append(f"- 密采样帧索引：{', '.join(str(x) for x in row.get('dense_frame_indices', []))}")
    lines.append(f"- 最终 12 帧：{', '.join(str(x) for x in row.get('selected_frame_indices', []))}")
    lines.append(f"- 最终帧覆盖比例：{selected.get('frame_span_ratio')}")
    lines.append(f"- 最终尾部覆盖比例：{selected.get('tail_coverage_ratio')}")
    lines.append(f"- 最终后半段采样占比：{selected.get('late_half_fraction')}")
    lines.append(f"- 最终后 75% 采样占比：{selected.get('late_75_fraction')}")
    lines.append(f"- 最终平均运动能量：{selected.get('motion_energy_mean')}")
    lines.append("")
    lines.append("## 观察")
    lines.append("")
    lines.append("- 这个策略把复杂度从“设计采样策略”转成了“先密采样，再筛选”。")
    lines.append("- 如果密采样候选足够密，最终筛出的 12 帧会保留较好的覆盖，同时实现逻辑更简单。")
    lines.append("- 这条路径的主耗时是密采样 Holistic 的初始化 + 识别总成本，总体是否划算主要看“全量候选覆盖质量”与“总墙钟耗时”之间的平衡。")
    lines.append("")
    lines.append("## 可视化")
    lines.append("")
    lines.append(f"- 密采样 Holistic 结果文件：{row.get('result_file')}")
    lines.append("- 后续可视化将基于该结果文件单独生成，不计入本次核心耗时。")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    configure_headless()
    started = time.perf_counter()

    parser = argparse.ArgumentParser(description="密采样筛选实验")
    parser.add_argument("--video-root", default=str(DEFAULT_VIDEO_ROOT), help="视频目录")
    parser.add_argument("--video", action="append", help="单个视频路径，可重复传入")
    parser.add_argument("--dense-step", type=int, default=DEFAULT_DENSE_STEP, help="密采样步长")
    parser.add_argument("--sample-budget", type=int, default=DEFAULT_SAMPLE_BUDGET, help="最终筛选帧数")
    parser.add_argument("--candidate-cache", help="候选缓存 JSON，提供后将只做筛选不再生成候选")
    parser.add_argument("--workers", type=int, default=0, help="并行 worker 数，0 表示使用 CPU 核数")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="输出目录")
    args = parser.parse_args(argv)

    video_root = Path(args.video_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.video:
        videos = [Path(v) for v in args.video]
    else:
        videos = find_demo_videos(video_root)

    if len(videos) != 1:
        raise RuntimeError("当前密采样筛选实验只建议先针对单个视频运行")

    video_result = build_energy_coverage_result(
        videos[0],
        args.dense_step,
        args.sample_budget,
        args.workers,
        Path(args.candidate_cache) if args.candidate_cache else None,
    )
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "elapsed_sec": round(time.perf_counter() - started, 3),
        "video_name": videos[0].name,
        "dense_step": args.dense_step,
        "sample_budget": args.sample_budget,
        "candidate_cache": args.candidate_cache,
        "video_result": video_result,
    }

    json_path = output_dir / "dense_uniform_step4_sampling.json"
    md_path = output_dir / "dense_uniform_step4_sampling.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_build_report(payload), encoding="utf-8")
    print(f"已生成密采样筛选 JSON：{json_path}")
    print(f"已生成密采样筛选报告：{md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

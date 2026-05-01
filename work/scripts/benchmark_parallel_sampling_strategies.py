#!/usr/bin/env python3
"""
四方案并行采样实验。

目标：
- 同时启动 4 个后台进程，每个进程对应一种关键帧采样方案
- 每个进程都以视频源模式处理同一个视频
- 分别统计：
  - worker 启动耗时
  - 方案完成耗时
  - 全部完成的总耗时

本脚本只负责编排与汇总，不改动各采样策略的核心实现。
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from keyframe_sampling_common import DEFAULT_VIDEO_ROOT, configure_headless
from signlanguage_common import find_demo_videos


DEFAULT_OUTPUT_DIR = Path("/data/WYC/signLanguage/work/generated/parallel_sampling_strategies_run1")
DEFAULT_VIDEO_NAME = "花.mp4"
DEFAULT_SAMPLE_BUDGET = 12
DEFAULT_DENSE_STEP = 4
DEFAULT_SHORT_VIDEO_THRESHOLD = 48
STRATEGY_DISPLAY_NAMES = {
    "uniform": "均匀采样",
    "two_stage": "两阶段采样",
    "adaptive": "自适应采样",
    "dense": "能量覆盖率筛选",
}
STRATEGY_JSON_NAMES = {
    "uniform": "uniform_sampling.json",
    "two_stage": "two_stage_sampling.json",
    "adaptive": "adaptive_sampling.json",
    "dense": "dense_uniform_step4_sampling.json",
}


def _default_video(video_root: Path) -> Path:
    videos = find_demo_videos(video_root)
    for video in videos:
        if video.name == DEFAULT_VIDEO_NAME:
            return video
    if not videos:
        raise RuntimeError(f"未找到视频：{video_root}")
    return videos[0]


def _launch(cmd: Sequence[str], log_path: Path) -> subprocess.Popen:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = open(log_path, "w", encoding="utf-8")
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    return subprocess.Popen(
        list(cmd),
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )


def _extract_strategy(payload: Dict[str, Any]) -> Dict[str, Any]:
    if "videos" in payload and isinstance(payload["videos"], list):
        row = payload["videos"][0]
    elif "video_result" in payload and isinstance(payload["video_result"], dict):
        row = payload["video_result"]
    else:
        raise RuntimeError("策略结果 JSON 格式不正确，缺少 videos/video_result")
    total_sec = float(payload.get("elapsed_sec") or 0.0)
    return {
        "candidate_generation_sec": row.get("candidate_generation_sec"),
        "selection_sec": row.get("selection_sec"),
        "combined_sec": row.get("combined_sec"),
        "total_sec": total_sec,
        "sampled_frame_indices": row.get("sampled_frame_indices", []),
        "processing_sec": row.get("processing_sec"),
        "evaluation": row.get("evaluation"),
        "candidate_summary": row.get("candidate_summary"),
        "dense_summary": row.get("dense_summary"),
        "selected_summary": row.get("selected_summary"),
    }


def _build_report(payload: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# 四方案并行关键帧采样实验")
    lines.append("")
    lines.append("## 实验设置")
    lines.append("")
    lines.append(f"- 对象视频：`{payload['video_name']}`")
    lines.append(f"- 目标采样帧数：{payload['sample_budget']}")
    lines.append(f"- 密采样步长：每 `{payload['dense_step']}` 帧采 1 帧")
    lines.append(f"- 短视频阈值：`{payload['short_video_threshold']}` 帧")
    lines.append(f"- 并行 worker 数：{len(payload['strategies'])}")
    lines.append("")
    lines.append("## 结果")
    lines.append("")
    if payload.get("candidate_generation_sec") is not None:
        lines.append(f"- 候选层生成耗时：{payload.get('candidate_generation_sec')}s")
    lines.append(f"- 全部完成总耗时：{payload['elapsed_sec']}s")
    lines.append("")
    for name, row in payload["strategies"].items():
        display_name = STRATEGY_DISPLAY_NAMES.get(name, name)
        lines.append(f"### {display_name}")
        lines.append(f"- 候选生成耗时：{row.get('candidate_generation_sec')}s")
        lines.append(f"- 选择耗时：{row.get('selection_sec')}s")
        lines.append(f"- 总耗时：{row.get('total_sec')}s")
        lines.append(f"- 关键帧：{', '.join(str(x) for x in row.get('sampled_frame_indices', []))}")
        if row.get("evaluation"):
            eval_ = row["evaluation"]
            lines.append(f"- 帧覆盖比例：{eval_.get('frame_span_ratio')}")
            lines.append(f"- 尾部覆盖比例：{eval_.get('tail_coverage_ratio')}")
            lines.append(f"- 后半段采样占比：{eval_.get('late_half_fraction')}")
            lines.append(f"- 后 75% 采样占比：{eval_.get('late_75_fraction')}")
            lines.append(f"- 平均运动能量：{eval_.get('motion_energy_mean')}")
        if row.get("selected_summary"):
            sel = row["selected_summary"]
            lines.append(f"- 最终帧覆盖比例：{sel.get('frame_span_ratio')}")
            lines.append(f"- 最终尾部覆盖比例：{sel.get('tail_coverage_ratio')}")
            lines.append(f"- 最终后半段采样占比：{sel.get('late_half_fraction')}")
            lines.append(f"- 最终后 75% 采样占比：{sel.get('late_75_fraction')}")
            lines.append(f"- 最终平均运动能量：{sel.get('motion_energy_mean')}")
        lines.append("")

    lines.append("## 观察")
    lines.append("")
    lines.append("- 这次实验把候选层和选择层分开后，四个策略比较的是同一份候选 Holistic 缓存上的选择成本。")
    lines.append("- `均匀采样` 的采样逻辑最简单，完成耗时通常最低。")
    lines.append("- `两阶段采样` 和 `自适应采样` 在采样决策上更复杂，完成耗时更高，但覆盖能力通常更强。")
    lines.append("- `能量覆盖率筛选` 方案把复杂度前移到密采样阶段，再从结果里筛帧，属于实现最直接、覆盖也较稳的一条路线。")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    configure_headless()
    parser = argparse.ArgumentParser(description="四方案并行关键帧采样实验")
    parser.add_argument("--video-root", default=str(DEFAULT_VIDEO_ROOT), help="视频目录")
    parser.add_argument("--video", help="单个视频路径；不传则默认选花.mp4")
    parser.add_argument("--sample-budget", type=int, default=DEFAULT_SAMPLE_BUDGET, help="目标采样帧数")
    parser.add_argument("--dense-step", type=int, default=DEFAULT_DENSE_STEP, help="密采样步长")
    parser.add_argument("--short-video-threshold", type=int, default=DEFAULT_SHORT_VIDEO_THRESHOLD, help="短视频阈值")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="输出目录")
    parser.add_argument("--python", default="/home/wuyangcheng/myenv/bin/python", help="Python 解释器")
    args = parser.parse_args(argv)

    video_root = Path(args.video_root)
    video_path = Path(args.video) if args.video else _default_video(video_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    candidate_dir = output_dir / "candidate_cache"
    candidate_dir.mkdir(parents=True, exist_ok=True)
    candidate_script = Path("/data/WYC/signLanguage/work/scripts/sample_keyframe_candidates.py")
    candidate_log = candidate_dir / "candidate_generation.log"
    candidate_cmd = [
        args.python,
        str(candidate_script),
        "--video",
        str(video_path),
        "--candidate-step",
        str(args.dense_step),
        "--short-video-threshold",
        str(args.short_video_threshold),
        "--workers",
        "1",
        "--output-dir",
        str(candidate_dir),
    ]
    candidate_started = time.perf_counter()
    _launch(candidate_cmd, candidate_log).wait()
    candidate_generation_sec = round(time.perf_counter() - candidate_started, 3)
    candidate_manifest = json.loads((candidate_dir / "candidate_cache.json").read_text(encoding="utf-8"))
    candidate_cache_file = candidate_manifest["videos"][0]["candidate_result_file"]

    strategy_specs = {
        "uniform": {
            "script": Path("/data/WYC/signLanguage/work/scripts/sample_keyframes_uniform.py"),
            "args": ["--video", str(video_path), "--sample-budget", str(args.sample_budget), "--candidate-cache", candidate_cache_file, "--workers", "1"],
            "out_dir": output_dir / "uniform",
        },
        "two_stage": {
            "script": Path("/data/WYC/signLanguage/work/scripts/sample_keyframes_two_stage.py"),
            "args": ["--video", str(video_path), "--sample-budget", str(args.sample_budget), "--candidate-cache", candidate_cache_file, "--workers", "1"],
            "out_dir": output_dir / "two_stage",
        },
        "adaptive": {
            "script": Path("/data/WYC/signLanguage/work/scripts/sample_keyframes_adaptive.py"),
            "args": ["--video", str(video_path), "--sample-budget", str(args.sample_budget), "--candidate-cache", candidate_cache_file, "--workers", "1"],
            "out_dir": output_dir / "adaptive",
        },
        "dense": {
            "script": Path("/data/WYC/signLanguage/work/scripts/sample_keyframes_dense_uniform.py"),
            "args": [
                "--video",
                str(video_path),
                "--sample-budget",
                str(args.sample_budget),
                "--candidate-cache",
                candidate_cache_file,
                "--workers",
                "1",
            ],
            "out_dir": output_dir / "dense",
        },
    }

    launched_at = datetime.now().isoformat(timespec="seconds")
    started = time.perf_counter()
    processes: Dict[str, Dict[str, Any]] = {}
    for name, spec in strategy_specs.items():
        log_path = spec["out_dir"] / f"{name}.log"
        cmd = [args.python, str(spec["script"]), *spec["args"], "--output-dir", str(spec["out_dir"])]
        proc_start = time.perf_counter()
        proc = _launch(cmd, log_path)
        processes[name] = {
            "process": proc,
            "log_path": str(log_path),
            "launch_sec": round(time.perf_counter() - proc_start, 3),
            "started_at": time.perf_counter(),
            "out_dir": str(spec["out_dir"]),
            "cmd": cmd,
        }

    finished: Dict[str, Any] = {}
    while len(finished) < len(processes):
        for name, info in processes.items():
            if name in finished:
                continue
            proc: subprocess.Popen = info["process"]
            ret = proc.poll()
            if ret is None:
                continue
            wall_sec = round(time.perf_counter() - info["started_at"], 3)
            json_path = Path(info["out_dir"]) / (
                "dense_uniform_step4_sampling.json" if name == "dense" else f"{name}_sampling.json"
            )
            if not json_path.exists():
                raise RuntimeError(f"{name} 结果文件不存在：{json_path}")
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            result = _extract_strategy(payload)
            result["process_wall_sec"] = wall_sec
            result["exit_code"] = ret
            finished[name] = result
        time.sleep(1.0)

    elapsed_sec = round(time.perf_counter() - started, 3)
    summary = {
        "generated_at": launched_at,
        "video_name": video_path.name,
        "video_path": str(video_path),
        "sample_budget": args.sample_budget,
        "dense_step": args.dense_step,
        "short_video_threshold": args.short_video_threshold,
        "candidate_generation_sec": candidate_generation_sec,
        "elapsed_sec": elapsed_sec,
        "strategies": finished,
        "output_dir": str(output_dir),
    }

    json_path = output_dir / "parallel_sampling_strategies.json"
    md_path = output_dir / "parallel_sampling_strategies.md"
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_build_report(summary), encoding="utf-8")
    print(f"已生成并行采样 JSON：{json_path}")
    print(f"已生成并行采样报告：{md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

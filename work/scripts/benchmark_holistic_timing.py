#!/usr/bin/env python3
"""
Holistic 严格分段计时基准。

用于拆分：
- 视频元数据读取
- Holistic 初始化
- 单帧/多帧识别

默认对 `花.mp4` 的前两帧做一次严格计时，便于观察初始化是否占主导。
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from keyframe_sampling_common import (
    DEFAULT_VIDEO_ROOT,
    configure_headless,
    _open_holistic,
    _process_frame,
    probe_video_metadata,
)


DEFAULT_OUTPUT_DIR = Path("/data/WYC/signLanguage/work/generated/holistic_timing_benchmark")


def _read_frames(video_path: Path, frame_indices: Sequence[int]):
    import cv2  # type: ignore

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"无法打开视频：{video_path}")

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
    frames: List[Dict[str, object]] = []
    for frame_idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(frame_idx))
        ok, frame = cap.read()
        if not ok:
            raise RuntimeError(f"无法读取帧：{video_path} @ {frame_idx}")
        frames.append({"frame_idx": int(frame_idx), "frame": frame, "fps": fps})
    cap.release()
    return frames


def benchmark(video_path: Path, frame_indices: Sequence[int], model_complexity: int = 1) -> Dict[str, object]:
    """对单个视频做严格分段计时。"""

    started = time.perf_counter()
    probe_start = time.perf_counter()
    meta = probe_video_metadata(video_path)
    probe_sec = round(time.perf_counter() - probe_start, 3)

    read_start = time.perf_counter()
    frames = _read_frames(video_path, frame_indices)
    read_sec = round(time.perf_counter() - read_start, 3)

    cv2_backend, mp, holistic_cls = _open_holistic()
    if cv2_backend is None or mp is None or holistic_cls is None:
        raise RuntimeError("需要安装 mediapipe 和 opencv-python 才能运行基准测试")

    init_start = time.perf_counter()
    with holistic_cls.Holistic(
        static_image_mode=False,
        model_complexity=model_complexity,
        smooth_landmarks=True,
        enable_segmentation=False,
        refine_face_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as holistic:
        init_sec = round(time.perf_counter() - init_start, 3)

        rows = []
        process_secs: List[float] = []
        for item in frames:
            frame_idx = int(item["frame_idx"])
            frame = item["frame"]
            fps = float(item["fps"])
            row_start = time.perf_counter()
            row, _ = _process_frame(frame_idx, fps, frame, holistic, cv2_backend)
            row_sec = round(time.perf_counter() - row_start, 3)
            process_secs.append(row_sec)
            rows.append(row)

    total_sec = round(time.perf_counter() - started, 3)
    return {
        "video": video_path.name,
        "video_path": str(video_path),
        "frame_indices": list(frame_indices),
        "model_complexity": model_complexity,
        "probe_sec": probe_sec,
        "read_sec": read_sec,
        "holistic_init_sec": init_sec,
        "per_frame_process_sec": process_secs,
        "holistic_eval_sec": round(sum(process_secs), 3),
        "total_sec": total_sec,
        "rows": rows,
        "meta": meta,
    }


def build_report(payload: Dict[str, object]) -> str:
    lines: List[str] = []
    lines.append("# Holistic 分段计时基准")
    lines.append("")
    lines.append(f"- 对象视频：`{payload['video']}`")
    lines.append(f"- 目标帧：{', '.join(str(x) for x in payload['frame_indices'])}")
    lines.append(f"- 模型复杂度：{payload['model_complexity']}")
    lines.append("")
    lines.append("## 计时")
    lines.append("")
    lines.append(f"- 元数据读取：{payload['probe_sec']}s")
    lines.append(f"- 帧读取：{payload['read_sec']}s")
    lines.append(f"- Holistic 初始化：{payload['holistic_init_sec']}s")
    lines.append(f"- Holistic 识别总耗时：{payload['holistic_eval_sec']}s")
    lines.append(f"- 单帧识别耗时：{', '.join(str(x) for x in payload['per_frame_process_sec'])}s")
    lines.append(f"- 全流程总耗时：{payload['total_sec']}s")
    lines.append("")
    lines.append("## 观察")
    lines.append("")
    lines.append("- 若初始化明显大于单帧识别，说明当前瓶颈主要在模型加载和图构建。")
    lines.append("- 若单帧识别总耗时远小于初始化，则块并行的收益会被初始化成本快速吞掉。")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    configure_headless()
    parser = argparse.ArgumentParser(description="Holistic 严格分段计时基准")
    parser.add_argument("--video-root", default=str(DEFAULT_VIDEO_ROOT), help="视频目录")
    parser.add_argument("--video", default=None, help="单个视频路径")
    parser.add_argument("--frame-idx", action="append", type=int, default=[0, 4], help="要测试的帧索引，可重复传入")
    parser.add_argument("--model-complexity", type=int, default=1, help="Holistic 模型复杂度")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="输出目录")
    args = parser.parse_args(argv)

    if args.video:
        video_path = Path(args.video)
    else:
        video_path = Path(args.video_root) / "花.mp4"

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    frame_indices = list(dict.fromkeys(int(idx) for idx in args.frame_idx))
    result = benchmark(video_path, frame_indices, args.model_complexity)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        **result,
    }
    json_path = output_dir / "holistic_timing_benchmark.json"
    md_path = output_dir / "holistic_timing_benchmark.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(build_report(payload), encoding="utf-8")
    print(f"已生成基准 JSON：{json_path}")
    print(f"已生成基准报告：{md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
把关键帧采样策略的结果渲染成可视化产物。

输入是各策略导出的 JSON 结果，输出包括：
- 每个采样帧的三联图
- 采样帧联系表
- 覆盖时间轴
- 便于汇报的 Markdown / JSON 摘要

注意：这里直接读取已保存的 Holistic 结果文件，只做统一可视化，不再重复跑识别。
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import cv2
import numpy as np
from PIL import Image, ImageDraw

from keyframe_sampling_common import DEFAULT_VIDEO_ROOT, configure_headless, _render_visual_cache
from visualize_holistic_features import (
    _configure_headless as _viz_configure_headless,
)


DEFAULT_OUTPUT_ROOT = Path("/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals")


def _draw_timeline(video_name: str, total_frames: int, sampled_indices: Sequence[int], output_path: Path) -> None:
    """生成采样时间轴，便于看覆盖是否均匀。"""

    width = 1400
    height = 220
    margin_x = 80
    margin_y = 64
    img = Image.new("RGB", (width, height), (18, 18, 18))
    draw = ImageDraw.Draw(img)
    line_y = 120
    draw.line((margin_x, line_y, width - margin_x, line_y), fill=(210, 210, 210), width=6)

    if total_frames <= 1:
        total_frames = 2

    for frac, label in [(0.0, "0%"), (0.25, "25%"), (0.5, "50%"), (0.75, "75%"), (1.0, "100%")]:
        x = int(margin_x + frac * (width - 2 * margin_x))
        draw.line((x, line_y - 18, x, line_y + 18), fill=(140, 140, 140), width=3)
        draw.text((x - 18, line_y + 28), label, fill=(230, 230, 230))

    for idx in sampled_indices:
        frac = idx / max(1, total_frames - 1)
        x = int(margin_x + frac * (width - 2 * margin_x))
        draw.line((x, line_y - 42, x, line_y + 42), fill=(89, 173, 255), width=5)
        draw.ellipse((x - 8, line_y - 8, x + 8, line_y + 8), fill=(89, 173, 255))

    try:
        from visualize_holistic_features import _load_font  # type: ignore

        font = _load_font(28)
        small_font = _load_font(22)
    except Exception:
        font = None
        small_font = None

    draw.text((margin_x, 20), f"{video_name} 采样时间轴", fill=(255, 255, 255), font=font)
    draw.text((margin_x, 168), f"总帧数：{total_frames}   采样帧数：{len(sampled_indices)}", fill=(220, 220, 220), font=small_font)
    img.save(output_path)


def _render_single_video(
    video_path: Path,
    sampled_indices: Sequence[int],
    out_dir: Path,
    holistic_result_file: Optional[str] = None,
) -> Dict[str, Any]:
    """把一个视频的采样点渲染成可视化结果。"""

    started = time.perf_counter()
    video_name = video_path.stem
    video_out = out_dir / video_name
    video_out.mkdir(parents=True, exist_ok=True)

    selected = sorted({int(idx) for idx in sampled_indices if int(idx) >= 0})

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"无法打开视频：{video_path}")

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if holistic_result_file:
        try:
            payload = json.loads(Path(holistic_result_file).read_text(encoding="utf-8"))
            if not total_frames:
                total_frames = int(payload.get("total_frames") or 0)
            if not fps:
                fps = float(payload.get("fps") or 25.0)
        except Exception:
            pass

    result_file = Path(holistic_result_file) if holistic_result_file else video_out / f"{video_name}_holistic_results.json"
    if not result_file.exists():
        raise RuntimeError(f"缺少 Holistic 结果文件：{result_file}")
    payload = json.loads(result_file.read_text(encoding="utf-8"))
    records = {int(item["frame_idx"]): item for item in payload.get("records", [])}

    visual_cache: List[Dict[str, Any]] = []
    selected_set = set(selected)
    max_target = selected[-1] if selected else -1
    frame_idx = 0
    target_pos = 0
    target = selected[target_pos] if selected else None
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if target is not None and frame_idx > max_target:
            break
        if target is not None and frame_idx < target:
            frame_idx += 1
            continue

        if target is not None and frame_idx == target and frame_idx in selected_set:
            record = records.get(frame_idx)
            if record is None:
                raise RuntimeError(f"结果文件中缺少帧 {frame_idx} 的 Holistic 记录：{result_file}")
            visual_cache.append(
                {
                    "frame": frame.copy(),
                    "frame_idx": frame_idx,
                    "row": record.get("row", {}),
                    "result_data": record.get("result_data", {}),
                }
            )
            target_pos += 1
            target = selected[target_pos] if target_pos < len(selected) else None

        frame_idx += 1

    cap.release()

    rendered = _render_visual_cache(cv2, video_path, fps, total_frames, visual_cache, video_out)
    frame_outputs = rendered["frame_outputs"]
    contact_sheet_path = rendered["contact_sheet_path"]
    timeline_path = rendered["timeline_path"]
    render_sec = round(float(rendered["visualization_sec"]), 3)

    summary = {
        "video": str(video_path),
        "fps": fps,
        "total_frames": total_frames,
        "sampled_frame_indices": selected,
        "sampled_timestamps_sec": [x["timestamp_sec"] for x in frame_outputs],
        "contact_sheet": contact_sheet_path,
        "timeline": timeline_path,
        "frames": frame_outputs,
        "render_sec": render_sec,
        "visualization_sec": render_sec,
        "holistic_result_file": str(holistic_result_file) if holistic_result_file else None,
    }
    (video_out / f"{video_name}_viz_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [
        f"# {video_name} 采样可视化",
        "",
        f"- 视频：{video_path}",
        f"- 总帧数：{total_frames}",
        f"- 采样帧数：{len(selected)}",
        f"- Holistic结果文件：{result_file}",
        f"- 联系表：{contact_sheet_path if contact_sheet_path is not None else '(无)'}",
        f"- 时间轴：{timeline_path}",
        "",
        "## 采样点",
        "",
        ", ".join(str(i) for i in selected) if selected else "(无)",
        "",
        "## 逐帧产物",
        "",
    ]
    for item in frame_outputs:
        md_lines.append(f"### frame {item['frame_idx']}")
        md_lines.append(f"- 时间戳：{item['timestamp_sec']:.3f}s")
        md_lines.append(f"- 三联图：{item['triptych_path']}")
        md_lines.append(f"- 关键点图：{item['annotated_path']}")
        md_lines.append(f"- 骨骼图：{item['skeleton_path']}")
        md_lines.append(f"- pose/left/right/face：{item['pose_present']}/{item['left_hand_present']}/{item['right_hand_present']}/{item['face_present']}")
        md_lines.append("")
    (video_out / f"{video_name}_viz_summary.md").write_text("\n".join(md_lines), encoding="utf-8")

    return summary


def _load_strategy_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: Optional[Sequence[str]] = None) -> int:
    configure_headless()
    _viz_configure_headless()
    started = time.perf_counter()

    parser = argparse.ArgumentParser(description="渲染关键帧采样策略结果")
    parser.add_argument("--strategy-json", action="append", required=True, help="策略 JSON，可重复传入")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT), help="输出根目录")
    args = parser.parse_args(argv)

    out_root = Path(args.output_root)
    out_root.mkdir(parents=True, exist_ok=True)

    rendered: List[Dict[str, Any]] = []
    for json_arg in args.strategy_json:
        json_path = Path(json_arg)
        payload = _load_strategy_json(json_path)
        strategy = payload.get("strategy") or json_path.stem
        strategy_out = out_root / strategy
        strategy_out.mkdir(parents=True, exist_ok=True)

        video_rows = payload.get("videos")
        if not video_rows and isinstance(payload.get("video_result"), dict):
            video_rows = [payload["video_result"]]
        videos: List[Dict[str, Any]] = []
        for row in video_rows or []:
            video_path = Path(row["video_path"])
            sampled_indices = row.get("sampled_frame_indices")
            if sampled_indices is None:
                sampled_indices = row.get("selected_frame_indices")
            if sampled_indices is None:
                sampled_indices = row.get("dense_frame_indices")
            holistic_result_file = row.get("candidate_cache_file") or row.get("result_file")
            videos.append(
                _render_single_video(
                    video_path,
                    sampled_indices or [],
                    strategy_out,
                    holistic_result_file=str(holistic_result_file) if holistic_result_file else None,
                )
            )

        summary = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "elapsed_sec": round(time.perf_counter() - started, 3),
            "strategy": strategy,
            "source_json": str(json_path),
            "output_dir": str(strategy_out),
            "videos": videos,
        }
        (strategy_out / f"{strategy}_visual_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        rendered.append(summary)

    if len(rendered) > 1:
        combined_path = out_root / "combined_visual_summary.json"
        combined_path.write_text(json.dumps({"generated_at": datetime.now().isoformat(timespec="seconds"), "strategies": rendered}, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"已生成组合可视化汇总：{combined_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

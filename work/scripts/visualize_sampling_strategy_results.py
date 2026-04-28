#!/usr/bin/env python3
"""
把关键帧采样策略的结果渲染成可视化产物。

输入是各策略导出的 JSON 结果，输出包括：
- 每个采样帧的三联图
- 采样帧联系表
- 覆盖时间轴
- 便于汇报的 Markdown / JSON 摘要
"""

from __future__ import annotations

import argparse
import json
import math
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

import cv2
import numpy as np
from PIL import Image, ImageDraw

from keyframe_sampling_common import DEFAULT_VIDEO_ROOT, configure_headless, _open_holistic
from visualize_holistic_features import (
    _concat_triptych,
    _configure_headless as _viz_configure_headless,
    _draw_landmarks,
    _draw_skeleton_canvas,
    _label_frame,
    _make_contact_sheet,
)


DEFAULT_OUTPUT_ROOT = Path("/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals")


def _ensure_rgb_text(image: np.ndarray, text: str, position: tuple[int, int], font_size: int = 26) -> np.ndarray:
    """用 PIL 在图像上添加文本。"""

    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(rgb)
    draw = ImageDraw.Draw(pil)
    try:
        from visualize_holistic_features import _load_font  # type: ignore

        font = _load_font(font_size)
    except Exception:
        font = None
    draw.text(position, text, fill=(255, 255, 255), font=font)
    return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)


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


def _render_single_video(video_path: Path, sampled_indices: Sequence[int], out_dir: Path) -> Dict[str, Any]:
    """把一个视频的采样点渲染成可视化结果。"""

    started = time.perf_counter()
    cv2_backend, _, holistic_cls = _open_holistic()
    if cv2_backend is None or holistic_cls is None:
        raise RuntimeError("需要安装 mediapipe 和 opencv-python 才能渲染采样可视化")

    video_name = video_path.stem
    video_out = out_dir / video_name
    video_out.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"无法打开视频：{video_path}")

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    selected = sorted({int(idx) for idx in sampled_indices if int(idx) >= 0})
    selected_set = set(selected)
    max_target = selected[-1] if selected else -1
    frame_idx = 0
    target_pos = 0
    contact_images: List[np.ndarray] = []
    frame_outputs: List[Dict[str, Any]] = []

    with holistic_cls.Holistic(
        static_image_mode=False,
        model_complexity=1,
        smooth_landmarks=True,
        enable_segmentation=False,
        refine_face_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as model:
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
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = model.process(rgb)
                annotated = _draw_landmarks(frame, results)
                skeleton = _draw_skeleton_canvas(frame.shape[:2], results)
                triptych = _concat_triptych(
                    _label_frame(frame, "原图"),
                    _label_frame(annotated, "关键点图"),
                    _label_frame(skeleton, "骨骼图"),
                )
                triptych = _ensure_rgb_text(
                    triptych,
                    f"视频={video_name} | 帧={frame_idx} | 时间={frame_idx / fps:.2f}s | "
                    f"姿态={bool(results.pose_landmarks)} | 左手={bool(results.left_hand_landmarks)} | "
                    f"右手={bool(results.right_hand_landmarks)} | 面部={bool(results.face_landmarks)}",
                    position=(16, 18),
                    font_size=24,
                )

                triptych_path = video_out / f"{video_name}_f{frame_idx:04d}_triptych.png"
                annotated_path = video_out / f"{video_name}_f{frame_idx:04d}_annotated.png"
                skeleton_path = video_out / f"{video_name}_f{frame_idx:04d}_skeleton.png"
                cv2.imwrite(str(triptych_path), triptych)
                cv2.imwrite(str(annotated_path), annotated)
                cv2.imwrite(str(skeleton_path), skeleton)

                contact_images.append(triptych)
                frame_outputs.append(
                    {
                        "frame_idx": frame_idx,
                        "timestamp_sec": frame_idx / fps,
                        "triptych_path": str(triptych_path),
                        "annotated_path": str(annotated_path),
                        "skeleton_path": str(skeleton_path),
                        "pose_present": bool(results.pose_landmarks),
                        "left_hand_present": bool(results.left_hand_landmarks),
                        "right_hand_present": bool(results.right_hand_landmarks),
                        "face_present": bool(results.face_landmarks),
                    }
                )

                target_pos += 1
                target = selected[target_pos] if target_pos < len(selected) else None

            frame_idx += 1

    cap.release()

    contact_sheet = _make_contact_sheet(contact_images, cols=2)
    contact_sheet_path = video_out / f"{video_name}_contact_sheet.png"
    if contact_sheet is not None:
        cv2.imwrite(str(contact_sheet_path), contact_sheet)

    timeline_path = video_out / f"{video_name}_timeline.png"
    _draw_timeline(video_name, total_frames, selected, timeline_path)

    summary = {
        "video": str(video_path),
        "fps": fps,
        "total_frames": total_frames,
        "sampled_frame_indices": selected,
        "sampled_timestamps_sec": [x["timestamp_sec"] for x in frame_outputs],
        "contact_sheet": str(contact_sheet_path) if contact_sheet is not None else None,
        "timeline": str(timeline_path),
        "frames": frame_outputs,
        "render_sec": round(time.perf_counter() - started, 3),
    }
    (video_out / f"{video_name}_viz_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [
        f"# {video_name} 采样可视化",
        "",
        f"- 视频：{video_path}",
        f"- 总帧数：{total_frames}",
        f"- 采样帧数：{len(selected)}",
        f"- 联系表：{contact_sheet_path if contact_sheet is not None else '(无)'}",
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

        videos: List[Dict[str, Any]] = []
        for row in payload.get("videos", []):
            video_path = Path(row["video_path"])
            videos.append(_render_single_video(video_path, row["sampled_frame_indices"], strategy_out))

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

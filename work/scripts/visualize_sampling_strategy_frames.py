#!/usr/bin/env python3
"""
把关键帧采样策略的结果快速渲染成“视频样本采样可视化”。

这个版本不再运行 Holistic，只做以下事情：
- 按采样帧索引抽取原视频帧
- 给每张帧图添加帧号与时间戳
- 保存采样帧联系表
- 保存覆盖时间轴

它更适合当前的策略对比实验，因为重点是“采样覆盖是否更均匀”，
而不是关键点检测本身。
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw

from keyframe_sampling_common import configure_headless
from visualize_holistic_features import _load_font


DEFAULT_OUTPUT_ROOT = Path("/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals")


def _draw_text(image: np.ndarray, text: str, position: Tuple[int, int], font_size: int = 26) -> np.ndarray:
    """在图像上写中文标题。"""

    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(rgb)
    draw = ImageDraw.Draw(pil)
    try:
        font = _load_font(font_size)
    except Exception:
        font = None
    draw.text(position, text, fill=(255, 255, 255), font=font)
    return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)


def _make_contact_sheet(images: List[np.ndarray], cols: int = 2) -> np.ndarray:
    """拼出采样帧联系表。"""

    if not images:
        return np.zeros((240, 320, 3), dtype=np.uint8)

    w = max(img.shape[1] for img in images)
    h = max(img.shape[0] for img in images)
    padded: List[np.ndarray] = []
    for img in images:
        canvas = np.zeros((h, w, 3), dtype=np.uint8)
        canvas[:] = (24, 24, 24)
        y0 = (h - img.shape[0]) // 2
        x0 = (w - img.shape[1]) // 2
        canvas[y0:y0 + img.shape[0], x0:x0 + img.shape[1]] = img
        padded.append(canvas)

    rows: List[np.ndarray] = []
    for start in range(0, len(padded), cols):
        row = padded[start:start + cols]
        if len(row) < cols:
            blank = np.zeros((h, w, 3), dtype=np.uint8)
            blank[:] = (24, 24, 24)
            row = row + [blank] * (cols - len(row))
        rows.append(np.hstack(row))
    return np.vstack(rows)


def _draw_timeline(video_name: str, total_frames: int, sampled_indices: Sequence[int], output_path: Path) -> None:
    """绘制覆盖时间轴。"""

    width = 1400
    height = 220
    margin_x = 80
    img = Image.new("RGB", (width, height), (18, 18, 18))
    draw = ImageDraw.Draw(img)
    font = _load_font(28)
    small_font = _load_font(22)

    line_y = 120
    draw.line((margin_x, line_y, width - margin_x, line_y), fill=(210, 210, 210), width=6)

    if total_frames <= 1:
        total_frames = 2

    for frac, label in [(0.0, "0%"), (0.25, "25%"), (0.5, "50%"), (0.75, "75%"), (1.0, "100%")]:
        x = int(margin_x + frac * (width - 2 * margin_x))
        draw.line((x, line_y - 18, x, line_y + 18), fill=(140, 140, 140), width=3)
        draw.text((x - 18, line_y + 28), label, fill=(230, 230, 230), font=small_font)

    for idx in sampled_indices:
        frac = idx / max(1, total_frames - 1)
        x = int(margin_x + frac * (width - 2 * margin_x))
        draw.line((x, line_y - 42, x, line_y + 42), fill=(89, 173, 255), width=5)
        draw.ellipse((x - 8, line_y - 8, x + 8, line_y + 8), fill=(89, 173, 255))

    draw.text((margin_x, 20), f"{video_name} 采样时间轴", fill=(255, 255, 255), font=font)
    draw.text((margin_x, 168), f"总帧数：{total_frames}   采样帧数：{len(sampled_indices)}", fill=(220, 220, 220), font=small_font)
    img.save(output_path)


def _extract_frames(video_path: Path, frame_indices: Sequence[int]) -> Tuple[float, int, List[Tuple[int, float, np.ndarray]]]:
    """按顺序抽取指定帧。"""

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"无法打开视频：{video_path}")

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    selected = sorted({int(idx) for idx in frame_indices if int(idx) >= 0})

    extracted: List[Tuple[int, float, np.ndarray]] = []
    current_idx = 0
    target_pos = 0
    target = selected[target_pos] if selected else None

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if target is not None and current_idx > selected[-1]:
            break
        if target is not None and current_idx < target:
            current_idx += 1
            continue

        if target is not None and current_idx == target:
            extracted.append((current_idx, current_idx / fps, frame.copy()))
            target_pos += 1
            target = selected[target_pos] if target_pos < len(selected) else None

        current_idx += 1

    cap.release()
    return fps, total_frames, extracted


def _render_video(video_path: Path, sampled_indices: Sequence[int], out_dir: Path) -> Dict[str, Any]:
    """渲染一个视频对应的采样图。"""

    started = time.perf_counter()
    video_name = video_path.stem
    video_out = out_dir / video_name
    video_out.mkdir(parents=True, exist_ok=True)

    fps, total_frames, extracted = _extract_frames(video_path, sampled_indices)
    tiles: List[np.ndarray] = []
    items: List[Dict[str, Any]] = []

    for frame_idx, timestamp_sec, frame in extracted:
        annotated = _draw_text(frame, f"视频={video_name} | 帧={frame_idx} | 时间={timestamp_sec:.2f}s", (16, 16), font_size=26)
        tile = _draw_text(annotated, f"采样帧 {frame_idx}", (16, 54), font_size=22)
        out_path = video_out / f"{video_name}_f{frame_idx:04d}_sample.png"
        cv2.imwrite(str(out_path), tile)
        tiles.append(tile)
        items.append(
            {
                "frame_idx": frame_idx,
                "timestamp_sec": timestamp_sec,
                "image_path": str(out_path),
            }
        )

    contact_sheet = _make_contact_sheet(tiles, cols=2)
    contact_path = video_out / f"{video_name}_contact_sheet.png"
    cv2.imwrite(str(contact_path), contact_sheet)

    timeline_path = video_out / f"{video_name}_timeline.png"
    _draw_timeline(video_name, total_frames, sampled_indices, timeline_path)

    summary = {
        "video": str(video_path),
        "fps": fps,
        "total_frames": total_frames,
        "sampled_frame_indices": list(sampled_indices),
        "sampled_timestamps_sec": [item["timestamp_sec"] for item in items],
        "contact_sheet": str(contact_path),
        "timeline": str(timeline_path),
        "frames": items,
        "render_sec": round(time.perf_counter() - started, 3),
    }
    (video_out / f"{video_name}_sample_viz.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [
        f"# {video_name} 采样可视化",
        "",
        f"- 视频：{video_path}",
        f"- 总帧数：{total_frames}",
        f"- 采样帧数：{len(items)}",
        f"- 联系表：{contact_path}",
        f"- 时间轴：{timeline_path}",
        "",
        "## 采样帧",
        "",
    ]
    for item in items:
        md_lines.append(f"- frame {item['frame_idx']} @ {item['timestamp_sec']:.3f}s -> {item['image_path']}")
    md_lines.append("")
    (video_out / f"{video_name}_sample_viz.md").write_text("\n".join(md_lines), encoding="utf-8")

    return summary


def _load_strategy_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: Optional[Sequence[str]] = None) -> int:
    configure_headless()
    started = time.perf_counter()
    parser = argparse.ArgumentParser(description="快速渲染关键帧采样可视化")
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
            videos.append(_render_video(video_path, row["sampled_frame_indices"], strategy_out))

        summary = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "elapsed_sec": round(time.perf_counter() - started, 3),
            "strategy": strategy,
            "source_json": str(json_path),
            "output_dir": str(strategy_out),
            "videos": videos,
        }
        (strategy_out / f"{strategy}_sample_viz_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        rendered.append(summary)

    if len(rendered) > 1:
        combined_path = out_root / "combined_sample_viz_summary.json"
        combined_path.write_text(json.dumps({"generated_at": datetime.now().isoformat(timespec="seconds"), "strategies": rendered}, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"已生成组合采样可视化汇总：{combined_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Render saved web Holistic JSON as skeleton/contact-sheet diagnostics.

Web scoring samples currently keep the Holistic JSON and scoring metadata, but
not the original browser JPEG frames. This script reuses the existing cached
Holistic renderer with a blank canvas so we can inspect what MediaPipe detected
without rerunning Holistic.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import numpy as np
from PIL import Image, ImageDraw

from keyframe_sampling_common import _render_visual_cache, import_optional_backends
from score_holistic_sequence_mvp import (
    DEFAULT_SEMANTIC_PROFILE_JSON,
    load_semantic_profile,
    load_sequence,
    run_pair,
)
from visualize_holistic_features import _load_font


REPO_ROOT = Path("/data/WYC/signLanguage")
DEFAULT_WEB_ROOT = REPO_ROOT / "work/generated/web_scoring_mvp"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "work/generated/web_holistic_visual_recovery"
DEFAULT_REQUESTS = [
    "web_20260523_043442_e00f8b9c",  # 花, demo/API path normal-like
    "web_20260523_043923_b95a60d0",  # 花, real web low
    "web_20260523_043955_dd909904",  # 花, real web low
    "web_20260523_043446_cbecd916",  # 跳, demo/API path normal-like
    "web_20260523_044323_2eb9eb7e",  # 跳, real web low
    "web_20260523_044336_5d15d099",  # 跳, real web low
    "web_20260523_044358_00db9d4d",  # 跳, real web low
]


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _records(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    return list(payload.get("records") or [])


def _record_by_frame(payload: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
    out: Dict[int, Dict[str, Any]] = {}
    for record in _records(payload):
        try:
            out[int(record["frame_idx"])] = record
        except Exception:
            continue
    return out


def _has_group(record: Dict[str, Any], group: str) -> bool:
    row = record.get("row") or {}
    row_key = {
        "pose": "pose_present",
        "left_hand": "left_hand_present",
        "right_hand": "right_hand_present",
        "face": "face_present",
    }.get(group)
    if row_key is not None and row_key in row:
        return bool(row.get(row_key))
    result = record.get("result_data") or {}
    return bool(result.get(f"{group}_landmarks"))


def _frame_weight(record: Dict[str, Any]) -> float:
    try:
        return float(record.get("frame_weight"))
    except Exception:
        pass
    try:
        return float((record.get("row") or {}).get("frame_weight"))
    except Exception:
        return 1.0


def _nearest_existing_frame(target: int, existing: Sequence[int]) -> Optional[int]:
    if not existing:
        return None
    return min(existing, key=lambda value: (abs(value - target), value))


def _pick_frames(
    payload: Dict[str, Any],
    score: Optional[Dict[str, Any]],
    *,
    side: str,
    max_frames: int,
) -> List[int]:
    records = _records(payload)
    if not records:
        return []
    existing = sorted(_record_by_frame(payload))
    chosen: List[int] = []

    def add(frame_idx: Optional[int]) -> None:
        if frame_idx is None:
            return
        nearest = _nearest_existing_frame(int(frame_idx), existing)
        if nearest is not None and nearest not in chosen:
            chosen.append(nearest)

    add(existing[0])
    add(existing[-1])

    if score:
        action_window = score.get("action_window") or {}
        window = action_window.get("query" if side == "query" else "standard") or {}
        for key in ["start_frame_idx", "peak_frame_idx", "end_frame_idx"]:
            add(window.get(key))
        for point in score.get("worst_alignment_points") or []:
            add(point.get("query_frame_idx" if side == "query" else "standard_frame_idx"))

    weighted = sorted(records, key=_frame_weight, reverse=True)
    for record in weighted[: max(4, max_frames // 2)]:
        add(record.get("frame_idx"))

    if len(chosen) < max_frames:
        span = np.linspace(0, len(existing) - 1, num=min(max_frames, len(existing)))
        for pos in span:
            add(existing[int(round(float(pos)))])

    chosen = sorted(chosen)
    if len(chosen) <= max_frames:
        return chosen

    keep = {chosen[0], chosen[-1]}
    if score:
        action_window = score.get("action_window") or {}
        window = action_window.get("query" if side == "query" else "standard") or {}
        for key in ["start_frame_idx", "peak_frame_idx", "end_frame_idx"]:
            nearest = _nearest_existing_frame(int(window[key]), existing) if key in window else None
            if nearest is not None:
                keep.add(nearest)
    for frame_idx in chosen:
        if len(keep) >= max_frames:
            break
        keep.add(frame_idx)
    return sorted(keep)


def _blank_frame(width: int, height: int, label: str) -> np.ndarray:
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    frame[:] = (28, 28, 28)
    # ASCII only here; Chinese text is added by the reused renderer.
    try:
        import cv2  # type: ignore

        cv2.putText(frame, "raw browser frame not saved", (28, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (210, 210, 210), 2)
        cv2.putText(frame, label[:72], (28, 88), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (170, 210, 255), 1)
    except Exception:
        pass
    return frame


def _build_visual_cache(
    payload: Dict[str, Any],
    frame_indices: Sequence[int],
    *,
    canvas_width: int,
    canvas_height: int,
    label: str,
) -> List[Dict[str, Any]]:
    by_frame = _record_by_frame(payload)
    visual_cache: List[Dict[str, Any]] = []
    for frame_idx in frame_indices:
        record = by_frame.get(int(frame_idx))
        if record is None:
            continue
        visual_cache.append(
            {
                "frame": _blank_frame(canvas_width, canvas_height, label),
                "frame_idx": int(frame_idx),
                "row": record.get("row") or {},
                "result_data": record.get("result_data") or {},
            }
        )
    return visual_cache


def _draw_presence_timeline(payload: Dict[str, Any], output_path: Path, title: str) -> None:
    records = _records(payload)
    width = 1500
    height = 360
    margin_x = 130
    img = Image.new("RGB", (width, height), (22, 22, 22))
    draw = ImageDraw.Draw(img)
    font = _load_font(26)
    small = _load_font(20)
    tiny = _load_font(16)
    draw.text((30, 22), title, fill=(255, 255, 255), font=font)
    if not records:
        draw.text((30, 120), "No records", fill=(255, 120, 120), font=font)
        img.save(output_path)
        return

    frame_indices = [int(record.get("frame_idx", idx)) for idx, record in enumerate(records)]
    min_idx = min(frame_indices)
    max_idx = max(frame_indices)
    span = max(1, max_idx - min_idx)
    groups = [
        ("pose", "pose", (80, 220, 255)),
        ("left_hand", "left", (255, 168, 88)),
        ("right_hand", "right", (255, 105, 105)),
        ("face", "face", (130, 255, 145)),
    ]
    y0 = 95
    row_h = 44
    for row_idx, (group, label, color) in enumerate(groups):
        y = y0 + row_idx * row_h
        draw.text((30, y - 10), label, fill=(230, 230, 230), font=small)
        draw.line((margin_x, y, width - 45, y), fill=(90, 90, 90), width=3)
        for record in records:
            frame_idx = int(record.get("frame_idx", 0))
            x = int(margin_x + (frame_idx - min_idx) / span * (width - margin_x - 45))
            present = _has_group(record, group)
            fill = color if present else (70, 70, 70)
            draw.rectangle((x - 3, y - 12, x + 3, y + 12), fill=fill)

    y = y0 + len(groups) * row_h + 20
    draw.text((30, y - 10), "weight", fill=(230, 230, 230), font=small)
    draw.line((margin_x, y, width - 45, y), fill=(90, 90, 90), width=3)
    weights = [_frame_weight(record) for record in records]
    w_min = min(weights)
    w_max = max(weights)
    w_span = max(1e-6, w_max - w_min)
    for record, weight in zip(records, weights):
        frame_idx = int(record.get("frame_idx", 0))
        x = int(margin_x + (frame_idx - min_idx) / span * (width - margin_x - 45))
        h = int(8 + 28 * ((weight - w_min) / w_span))
        draw.rectangle((x - 3, y - h, x + 3, y + h), fill=(120, 170, 255))

    left_ratio = sum(_has_group(record, "left_hand") for record in records) / len(records)
    right_ratio = sum(_has_group(record, "right_hand") for record in records) / len(records)
    pose_ratio = sum(_has_group(record, "pose") for record in records) / len(records)
    face_ratio = sum(_has_group(record, "face") for record in records) / len(records)
    draw.text(
        (30, height - 42),
        f"frames={len(records)}  span={min_idx}-{max_idx}  left={left_ratio:.2f}  right={right_ratio:.2f}  pose={pose_ratio:.2f}  face={face_ratio:.2f}",
        fill=(230, 230, 230),
        font=tiny,
    )
    img.save(output_path)


def _make_skeleton_contact_sheet(cv2: Any, frame_outputs: Sequence[Dict[str, Any]], output_path: Path, cols: int = 4) -> Optional[str]:
    images: List[np.ndarray] = []
    for item in frame_outputs:
        skeleton_path = item.get("skeleton_path")
        if not skeleton_path:
            continue
        image = cv2.imread(str(skeleton_path))
        if image is None:
            continue
        label = (
            f"f={int(item.get('frame_idx', 0))} "
            f"t={float(item.get('timestamp_sec', 0.0)):.2f}s "
            f"L={int(bool(item.get('left_hand_present')))} "
            f"R={int(bool(item.get('right_hand_present')))}"
        )
        cv2.rectangle(image, (0, 0), (min(image.shape[1], 360), 32), (0, 0, 0), -1)
        cv2.putText(image, label, (10, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (245, 245, 245), 1, cv2.LINE_AA)
        images.append(image)

    if not images:
        return None

    tile_w = max(image.shape[1] for image in images)
    tile_h = max(image.shape[0] for image in images)
    padded: List[np.ndarray] = []
    for image in images:
        canvas = np.zeros((tile_h, tile_w, 3), dtype=np.uint8)
        canvas[:] = (18, 18, 18)
        y0 = (tile_h - image.shape[0]) // 2
        x0 = (tile_w - image.shape[1]) // 2
        canvas[y0:y0 + image.shape[0], x0:x0 + image.shape[1]] = image
        padded.append(canvas)

    rows: List[np.ndarray] = []
    for start in range(0, len(padded), cols):
        row = padded[start:start + cols]
        if len(row) < cols:
            blank = np.zeros((tile_h, tile_w, 3), dtype=np.uint8)
            blank[:] = (18, 18, 18)
            row = row + [blank] * (cols - len(row))
        rows.append(np.hstack(row))
    sheet = np.vstack(rows)
    cv2.imwrite(str(output_path), sheet)
    return str(output_path)


def _render_one_sequence(
    cv2: Any,
    payload: Dict[str, Any],
    score: Optional[Dict[str, Any]],
    output_dir: Path,
    *,
    stem: str,
    side: str,
    max_frames: int,
    canvas_width: int,
    canvas_height: int,
) -> Dict[str, Any]:
    frame_indices = _pick_frames(payload, score, side=side, max_frames=max_frames)
    visual_cache = _build_visual_cache(payload, frame_indices, canvas_width=canvas_width, canvas_height=canvas_height, label=stem)
    output_dir.mkdir(parents=True, exist_ok=True)
    rendered = _render_visual_cache(
        cv2,
        Path(f"{stem}.mp4"),
        float(payload.get("fps") or 18.0),
        int(payload.get("total_frames") or (max(frame_indices) + 1 if frame_indices else 1)),
        visual_cache,
        output_dir,
    )
    triptych_contact = rendered.get("contact_sheet_path")
    skeleton_contact_path = output_dir / f"{stem}_skeleton_contact_sheet.png"
    skeleton_contact = _make_skeleton_contact_sheet(cv2, rendered.get("frame_outputs") or [], skeleton_contact_path)
    timeline_path = output_dir / f"{stem}_presence_timeline.png"
    _draw_presence_timeline(payload, timeline_path, stem)
    rendered["triptych_contact_sheet_path"] = triptych_contact
    if skeleton_contact is not None:
        rendered["contact_sheet_path"] = skeleton_contact
    rendered["skeleton_contact_sheet_path"] = skeleton_contact
    rendered["presence_timeline"] = str(timeline_path)
    rendered["selected_frame_indices"] = list(frame_indices)
    return rendered


def render_request(
    request_id: str,
    *,
    web_root: Path,
    output_root: Path,
    semantic_profile_json: Path,
    rescore_current: bool,
    max_frames: int,
    canvas_width: int,
    canvas_height: int,
) -> Dict[str, Any]:
    request_dir = web_root / request_id
    score_path = request_dir / "scoring_result.json"
    if not score_path.exists():
        raise FileNotFoundError(f"missing scoring_result.json: {score_path}")
    scoring = _load_json(score_path)
    score = scoring.get("score") or {}
    target_word = str(scoring.get("target_word") or "unknown")
    query_json = Path(scoring.get("query_json") or "")
    standard_json = Path(scoring.get("standard_json") or "")
    if not query_json.exists():
        candidates = sorted((request_dir / "holistic").glob("*.json"))
        if not candidates:
            raise FileNotFoundError(f"missing query holistic JSON for {request_id}")
        query_json = candidates[0]
    if not standard_json.exists():
        raise FileNotFoundError(f"missing standard holistic JSON for {request_id}: {standard_json}")

    stored_score = score
    score_source = "stored_scoring_result"
    if rescore_current:
        standard_seq = load_sequence(standard_json, requested_mode="landmark")
        query_seq = load_sequence(query_json, requested_mode="landmark")
        profile = load_semantic_profile(target_word, semantic_profile_json)
        score = run_pair(standard_seq, query_seq, semantic_profile=profile, enable_cross_check=False)
        score_source = "current_scoring_module"

    cv2, _ = import_optional_backends()
    if cv2 is None:
        raise RuntimeError("opencv-python is required for rendering")

    request_out = output_root / request_id
    query_payload = _load_json(query_json)
    standard_payload = _load_json(standard_json)
    query_render = _render_one_sequence(
        cv2,
        query_payload,
        score,
        request_out / "query",
        stem=f"{request_id}_{target_word}_query",
        side="query",
        max_frames=max_frames,
        canvas_width=canvas_width,
        canvas_height=canvas_height,
    )
    standard_render = _render_one_sequence(
        cv2,
        standard_payload,
        score,
        request_out / "standard",
        stem=f"{request_id}_{target_word}_standard",
        side="standard",
        max_frames=max_frames,
        canvas_width=canvas_width,
        canvas_height=canvas_height,
    )
    summary = {
        "request_id": request_id,
        "target_word": target_word,
        "score": score.get("prototype_score"),
        "stored_score": stored_score.get("prototype_score"),
        "score_source": score_source,
        "query_json": str(query_json),
        "standard_json": str(standard_json),
        "query": query_render,
        "standard": standard_render,
    }
    (request_out / "visual_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def build_markdown(results: Sequence[Dict[str, Any]], output_root: Path) -> str:
    lines: List[str] = []
    lines.append("# 网页 Holistic 识别结果可视化恢复")
    lines.append("")
    lines.append("说明：网页样本当前没有保留原始摄像头 JPEG，因此这里复用旧的 Holistic JSON 渲染逻辑，在空白画布上恢复关键点骨架和识别时间线。当前 contact sheet 只拼接骨架图，不再拼原图/关键点图/骨骼图三联。")
    lines.append("")
    for item in results:
        score_text = f"score={float(item['score'] or 0.0):.3f}"
        if item.get("score_source") == "current_scoring_module":
            score_text += f" / stored={float(item.get('stored_score') or 0.0):.3f}"
        lines.append(f"## {item['request_id']} / {item['target_word']} / {score_text}")
        lines.append("")
        lines.append(f"- 分数来源：`{item.get('score_source') or 'stored_scoring_result'}`")
        lines.append(f"- 查询样本联系表：`{item['query'].get('contact_sheet_path')}`")
        lines.append(f"- 查询样本识别时间线：`{item['query'].get('presence_timeline')}`")
        lines.append(f"- 查询样本选帧：`{item['query'].get('selected_frame_indices')}`")
        lines.append(f"- 标准样本联系表：`{item['standard'].get('contact_sheet_path')}`")
        lines.append(f"- 标准样本识别时间线：`{item['standard'].get('presence_timeline')}`")
        lines.append(f"- 标准样本选帧：`{item['standard'].get('selected_frame_indices')}`")
        lines.append("")
    md = "\n".join(lines)
    (output_root / "web_holistic_visual_recovery_summary.md").write_text(md, encoding="utf-8")
    return md


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="恢复网页样本 Holistic 骨架可视化")
    parser.add_argument("--web-root", default=str(DEFAULT_WEB_ROOT))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--rescore-current", action="store_true", help="使用当前评分模块复算分数和 action window")
    parser.add_argument("--requests", nargs="*", default=DEFAULT_REQUESTS)
    parser.add_argument("--max-frames", type=int, default=12)
    parser.add_argument("--canvas-width", type=int, default=960)
    parser.add_argument("--canvas-height", type=int, default=720)
    args = parser.parse_args(argv)

    output_root = Path(args.output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    results = [
        render_request(
            request_id,
            web_root=Path(args.web_root),
            output_root=output_root,
            semantic_profile_json=Path(args.semantic_profile_json),
            rescore_current=bool(args.rescore_current),
            max_frames=max(4, int(args.max_frames)),
            canvas_width=max(320, int(args.canvas_width)),
            canvas_height=max(240, int(args.canvas_height)),
        )
        for request_id in args.requests
    ]
    build_markdown(results, output_root)
    print(f"已生成汇总：{output_root / 'web_holistic_visual_recovery_summary.md'}")
    for item in results:
        print(
            f"{item['request_id']} {item['target_word']} "
            f"score={float(item['score'] or 0.0):.3f} source={item.get('score_source')}"
        )
        print(f"  query_contact={item['query'].get('contact_sheet_path')}")
        print(f"  query_timeline={item['query'].get('presence_timeline')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

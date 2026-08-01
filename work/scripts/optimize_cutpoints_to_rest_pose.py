#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Snap segmentation cutpoints to nearby rest-pose frames.

For each existing cut boundary, this script searches a small time window and
chooses the nearby frame where the MediaPipe Holistic pose best matches
"arms close to body".  It is intended as a second-stage refinement after
audio-based segmentation/migration:

    audio/migrated boundary -> nearby visual rest-pose boundary

The script is privacy-preserving for the current project convention: it reads
the private source video in place and writes only CSV/JSON diagnostics plus a
contact-sheet preview of selected boundary frames.  It does not encode or copy
video clips.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import auto_cut_voice_prompt_segments as core


POSE_IDS = {
    "left_shoulder": 11,
    "right_shoulder": 12,
    "left_elbow": 13,
    "right_elbow": 14,
    "left_wrist": 15,
    "right_wrist": 16,
    "left_hip": 23,
    "right_hip": 24,
}


def read_segments(path: Path) -> list[dict]:
    return list(csv.DictReader(path.open(encoding="utf-8-sig")))


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def landmark_xyv(pose, index: int) -> tuple[float, float, float] | None:
    if pose is None or index >= len(pose.landmark):
        return None
    lm = pose.landmark[index]
    x, y = float(lm.x), float(lm.y)
    visibility = float(getattr(lm, "visibility", 1.0))
    if not (math.isfinite(x) and math.isfinite(y) and math.isfinite(visibility)):
        return None
    return x, y, visibility


def dist(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def rest_pose_score(pose) -> dict:
    """Lower score means arms are closer to a neutral arms-down posture."""
    points = {name: landmark_xyv(pose, idx) for name, idx in POSE_IDS.items()}
    missing = [name for name, point in points.items() if point is None]
    if missing:
        return {
            "rest_score": 999.0,
            "pose_valid": False,
            "missing": ";".join(missing),
            "visibility_min": 0.0,
            "visibility_mean": 0.0,
            "left_score": 999.0,
            "right_score": 999.0,
        }

    vis = np.asarray([point[2] for point in points.values()], dtype=np.float64)
    l_sh, r_sh = points["left_shoulder"], points["right_shoulder"]
    l_hip, r_hip = points["left_hip"], points["right_hip"]
    mid_sh = ((l_sh[0] + r_sh[0]) / 2.0, (l_sh[1] + r_sh[1]) / 2.0, 1.0)
    mid_hip = ((l_hip[0] + r_hip[0]) / 2.0, (l_hip[1] + r_hip[1]) / 2.0, 1.0)
    shoulder_width = max(dist(l_sh, r_sh), 1e-4)
    torso_height = max(dist(mid_sh, mid_hip), 1e-4)
    body_scale = max(shoulder_width, torso_height)

    def side_score(prefix: str) -> float:
        shoulder = points[f"{prefix}_shoulder"]
        elbow = points[f"{prefix}_elbow"]
        wrist = points[f"{prefix}_wrist"]
        hip = points[f"{prefix}_hip"]
        side_x = 0.62 * shoulder[0] + 0.38 * hip[0]
        # Arm close to the side of the torso.
        x_close = (abs(elbow[0] - side_x) + abs(wrist[0] - side_x)) / body_scale
        # Arm roughly vertical and down.
        upper_vertical = abs(elbow[0] - shoulder[0]) / max(abs(elbow[1] - shoulder[1]), 0.03)
        lower_vertical = abs(wrist[0] - elbow[0]) / max(abs(wrist[1] - elbow[1]), 0.03)
        vertical = 0.5 * (upper_vertical + lower_vertical)
        # Correct y ordering for an arm hanging naturally.
        down_penalty = (
            max(0.0, shoulder[1] + 0.03 - elbow[1])
            + max(0.0, elbow[1] + 0.03 - wrist[1])
        ) / body_scale
        # Wrist near the hip/thigh region rather than raised near the chest.
        wrist_to_hip_y = abs(wrist[1] - hip[1]) / body_scale
        wrist_high = max(0.0, hip[1] - wrist[1]) / body_scale
        return (
            1.20 * x_close
            + 0.45 * vertical
            + 1.50 * down_penalty
            + 0.35 * wrist_to_hip_y
            + 0.80 * wrist_high
        )

    left = side_score("left")
    right = side_score("right")
    visibility_penalty = max(0.0, 0.55 - float(np.min(vis))) * 2.0
    return {
        "rest_score": float((left + right) / 2.0 + visibility_penalty),
        "pose_valid": True,
        "missing": "",
        "visibility_min": float(np.min(vis)),
        "visibility_mean": float(np.mean(vis)),
        "left_score": float(left),
        "right_score": float(right),
    }


def collect_candidate_frames(
    video: Path,
    cut_times: list[float],
    fps: float,
    total_frames: int,
    window_sec: float,
) -> dict[int, list[int]]:
    mapping: dict[int, list[int]] = {}
    all_frames: set[int] = set()
    radius = int(round(window_sec * fps))
    for i, sec in enumerate(cut_times):
        center = int(round(sec * fps))
        lo = max(0, center - radius)
        hi = min(total_frames - 1, center + radius)
        frames = list(range(lo, hi + 1))
        mapping[i] = frames
        all_frames.update(frames)
    return mapping


def evaluate_frames(video: Path, frame_indices: list[int], max_width: int) -> dict[int, dict]:
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise RuntimeError(f"cannot open video: {video}")
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
    results: dict[int, dict] = {}
    frame_indices = sorted(set(int(x) for x in frame_indices))
    if hasattr(cv2, "setNumThreads"):
        try:
            cv2.setNumThreads(1)
        except Exception:
            pass

    with mp.solutions.holistic.Holistic(
        static_image_mode=False,
        model_complexity=1,
        smooth_landmarks=True,
        enable_segmentation=False,
        refine_face_landmarks=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as holistic:
        targets = set(frame_indices)
        first_idx, last_idx = frame_indices[0], frame_indices[-1]
        cap.set(cv2.CAP_PROP_POS_FRAMES, first_idx)
        idx = first_idx
        while idx <= last_idx:
            ok, frame = cap.read()
            if not ok:
                break
            if idx in targets:
                if max_width > 0 and frame.shape[1] > max_width:
                    scale = max_width / frame.shape[1]
                    frame = cv2.resize(
                        frame,
                        (max_width, max(1, int(round(frame.shape[0] * scale)))),
                        interpolation=cv2.INTER_AREA,
                    )
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                result = holistic.process(rgb)
                score = rest_pose_score(result.pose_landmarks)
                score.update(
                    {
                        "frame_idx": idx,
                        "timestamp_sec": idx / fps,
                    }
                )
                results[idx] = score
            idx += 1
    cap.release()
    return results


def select_frame(
    original_sec: float,
    frame_indices: list[int],
    frame_scores: dict[int, dict],
    fps: float,
    window_sec: float,
    time_weight: float,
) -> dict:
    valid = []
    fallback = []
    for idx in frame_indices:
        item = frame_scores.get(idx)
        if not item:
            continue
        dt = item["timestamp_sec"] - original_sec
        combined = item["rest_score"] + time_weight * abs(dt) / max(window_sec, 1e-6)
        row = dict(item)
        row["delta_sec"] = dt
        row["combined_score"] = combined
        fallback.append(row)
        if item["pose_valid"]:
            valid.append(row)
    pool = valid or fallback
    if not pool:
        idx = int(round(original_sec * fps))
        return {
            "frame_idx": idx,
            "timestamp_sec": idx / fps,
            "delta_sec": 0.0,
            "rest_score": 999.0,
            "combined_score": 999.0,
            "pose_valid": False,
            "missing": "no_candidate_frame_read",
            "visibility_min": 0.0,
            "visibility_mean": 0.0,
            "left_score": 999.0,
            "right_score": 999.0,
        }
    # Primary: neutral arms-down score; secondary: stay close to audio boundary.
    return min(pool, key=lambda x: (x["combined_score"], abs(x["delta_sec"])))


def render_contact_sheet(video: Path, rows: list[dict], output: Path, cols: int = 4) -> None:
    from PIL import Image, ImageDraw, ImageFont

    cap = cv2.VideoCapture(str(video))
    thumbs = []
    font_path = "/home/wuyangcheng/.fonts/SimHei.ttf"
    font = ImageFont.truetype(font_path, 15) if Path(font_path).exists() else None
    for row in rows:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(row["optimized_frame_idx"]))
        ok, frame = cap.read()
        if not ok:
            continue
        frame = cv2.resize(frame, (320, 180), interpolation=cv2.INTER_AREA)
        canvas = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(canvas)
        draw.rectangle((0, 0, 320, 31), fill=(0, 0, 0))
        text = (
            f"{int(row['boundary_index']):02d} {row['word']} "
            f"{float(row['optimized_sec']):.2f}s Δ{float(row['shift_sec']):+.2f}"
        )
        if font:
            draw.text((5, 3), text, font=font, fill=(255, 240, 0))
        else:
            draw.text((5, 3), text, fill=(255, 240, 0))
        thumbs.append(cv2.cvtColor(np.asarray(canvas), cv2.COLOR_RGB2BGR))
    cap.release()
    if not thumbs:
        return
    rows_n = math.ceil(len(thumbs) / cols)
    sheet = np.zeros((rows_n * 180, cols * 320, 3), dtype=np.uint8)
    for i, frame in enumerate(thumbs):
        r, c = divmod(i, cols)
        sheet[r * 180:(r + 1) * 180, c * 320:(c + 1) * 320] = frame
    output.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output), sheet)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--segments", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--window-sec", type=float, default=0.65)
    parser.add_argument("--time-weight", type=float, default=0.12)
    parser.add_argument("--max-width", type=int, default=640)
    args = parser.parse_args()

    segments = read_segments(args.segments)
    if not segments:
        raise SystemExit("empty segments")

    cap = cv2.VideoCapture(str(args.video))
    if not cap.isOpened():
        raise SystemExit(f"cannot open video: {args.video}")
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = total_frames / fps if fps else 0.0
    cap.release()

    # Optimize all segment starts plus the final end boundary, so every segment
    # has a visually refined start and end.  The final boundary is constrained
    # near the original final end.
    original_starts = [float(row["start_sec"]) for row in segments]
    original_final_end = float(segments[-1]["end_sec"])
    cut_times = original_starts + [original_final_end]
    frame_map = collect_candidate_frames(args.video, cut_times, fps, total_frames, args.window_sec)
    all_frames = sorted({idx for frames in frame_map.values() for idx in frames})
    t0 = time.time()
    frame_scores = evaluate_frames(args.video, all_frames, args.max_width)

    boundary_rows = []
    optimized = []
    for i, sec in enumerate(cut_times):
        selected = select_frame(
            sec,
            frame_map[i],
            frame_scores,
            fps,
            args.window_sec,
            args.time_weight,
        )
        if i > 0 and selected["timestamp_sec"] <= optimized[-1]:
            # Extremely unlikely with the current windows, but preserve
            # monotonically increasing boundaries.
            min_frame = int(math.ceil((optimized[-1] + 1.0 / fps) * fps))
            selected = dict(selected)
            selected["frame_idx"] = max(selected["frame_idx"], min_frame)
            selected["timestamp_sec"] = selected["frame_idx"] / fps
            selected["delta_sec"] = selected["timestamp_sec"] - sec
        optimized.append(float(selected["timestamp_sec"]))
        word = (
            segments[i]["word"]
            if i < len(segments)
            else segments[-1]["word"] + "_final_end"
        )
        repeat = segments[i]["repeat_index"] if i < len(segments) else "end"
        boundary_rows.append(
            {
                "boundary_index": i + 1,
                "boundary_type": "segment_start" if i < len(segments) else "final_end",
                "word": word,
                "repeat_index": repeat,
                "original_sec": round(sec, 4),
                "optimized_sec": round(float(selected["timestamp_sec"]), 4),
                "shift_sec": round(float(selected["timestamp_sec"] - sec), 4),
                "optimized_frame_idx": int(selected["frame_idx"]),
                "rest_score": round(float(selected["rest_score"]), 6),
                "combined_score": round(float(selected["combined_score"]), 6),
                "pose_valid": bool(selected["pose_valid"]),
                "visibility_min": round(float(selected["visibility_min"]), 6),
                "visibility_mean": round(float(selected["visibility_mean"]), 6),
                "left_arm_score": round(float(selected["left_score"]), 6),
                "right_arm_score": round(float(selected["right_score"]), 6),
                "missing": selected.get("missing", ""),
            }
        )

    optimized_starts = optimized[:-1]
    optimized_final_end = min(max(optimized[-1], optimized_starts[-1] + 1.0 / fps), duration)
    optimized_ends = optimized_starts[1:] + [optimized_final_end]

    optimized_segments = []
    for idx, row in enumerate(segments):
        out = dict(row)
        out["audio_migrated_start_sec"] = row["start_sec"]
        out["audio_migrated_end_sec"] = row["end_sec"]
        out["start_sec"] = round(float(optimized_starts[idx]), 4)
        out["end_sec"] = round(float(optimized_ends[idx]), 4)
        out["duration_sec"] = round(float(optimized_ends[idx] - optimized_starts[idx]), 4)
        out["boundary_refinement"] = "holistic_pose_rest_nearest_frame"
        out["start_shift_sec"] = boundary_rows[idx]["shift_sec"]
        out["end_shift_sec"] = boundary_rows[idx + 1]["shift_sec"]
        optimized_segments.append(out)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "segments_pose_rest_optimized.csv", optimized_segments)
    write_csv(args.output_dir / "boundary_pose_rest_diagnostics.csv", boundary_rows)
    render_contact_sheet(
        args.video,
        boundary_rows,
        args.output_dir / "preview_pose_rest_optimized_boundaries.jpg",
    )

    shifts = np.asarray([float(row["shift_sec"]) for row in boundary_rows], dtype=np.float64)
    valid_count = sum(1 for row in boundary_rows if row["pose_valid"])
    manifest = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S %z"),
        "method": "holistic_pose_rest_nearest_frame_boundary_refinement",
        "video": str(args.video),
        "input_segments": str(args.segments),
        "window_sec": args.window_sec,
        "time_weight": args.time_weight,
        "fps": fps,
        "total_frames": total_frames,
        "duration_sec": duration,
        "boundary_count": len(boundary_rows),
        "segment_count": len(optimized_segments),
        "pose_valid_boundary_count": valid_count,
        "evaluated_unique_frame_count": len(all_frames),
        "processing_sec": round(time.time() - t0, 3),
        "shift_summary_sec": {
            "mean": float(np.mean(shifts)),
            "mean_abs": float(np.mean(np.abs(shifts))),
            "max_abs": float(np.max(np.abs(shifts))),
            "min": float(np.min(shifts)),
            "max": float(np.max(shifts)),
        },
        "outputs": {
            "optimized_segments_csv": str(args.output_dir / "segments_pose_rest_optimized.csv"),
            "boundary_diagnostics_csv": str(args.output_dir / "boundary_pose_rest_diagnostics.csv"),
            "preview": str(args.output_dir / "preview_pose_rest_optimized_boundaries.jpg"),
        },
    }
    (args.output_dir / "pose_rest_optimization_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

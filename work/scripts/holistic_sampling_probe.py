#!/usr/bin/env python3
"""
MediaPipe Holistic 采样探针。

对应 worklog_sign.md 里的第二个 TODO：
“针对标准样本 demo，看看 Holistic 模型的特征采样效果，是否能有效覆盖手语语义的关键信息。”

脚本设计目标：
1. 尽量直接跑出每个视频的关键点覆盖率和时间序列特征
2. 如果当前环境没有 mediapipe / opencv，也能生成视频探测和采样计划
3. 以后装好依赖后，不需要改脚本即可获得真实 Holistic 结果
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import statistics
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from signlanguage_common import find_demo_videos, probe_video_metadata


DEFAULT_REPO_ROOT = Path("/data/WYC/signLanguage")
DEFAULT_VIDEO_ROOT = DEFAULT_REPO_ROOT / "data" / "Demo词汇视频"
DEFAULT_OUTPUT_DIR = DEFAULT_REPO_ROOT / "work" / "generated" / "holistic_probe"


def _import_optional_backends():
    """延迟导入可选依赖，避免脚本在无依赖环境中直接崩掉。"""

    cv2 = None
    mp = None
    try:
        import cv2 as _cv2  # type: ignore

        cv2 = _cv2
    except Exception:
        cv2 = None

    try:
        import mediapipe as _mp  # type: ignore

        mp = _mp
    except Exception:
        mp = None

    return cv2, mp


def _mean_or_none(values: Sequence[float]) -> Optional[float]:
    return float(statistics.mean(values)) if values else None


def _bbox_from_landmarks(landmarks, width: int, height: int) -> Optional[Dict[str, float]]:
    """把归一化关键点转成像素级包围框。"""

    xs: List[float] = []
    ys: List[float] = []
    vis: List[float] = []
    for lm in landmarks:
        xs.append(float(lm.x) * width)
        ys.append(float(lm.y) * height)
        vis.append(float(getattr(lm, "visibility", 1.0)))
    if not xs or not ys:
        return None
    return {
        "x_min": min(xs),
        "x_max": max(xs),
        "y_min": min(ys),
        "y_max": max(ys),
        "visibility_mean": _mean_or_none(vis) or 0.0,
    }


def _landmark_presence(landmarks) -> bool:
    return landmarks is not None and len(landmarks.landmark) > 0


def _frame_motion(prev: Optional[Dict[str, Any]], current: Dict[str, Any]) -> Dict[str, float]:
    """计算相邻帧的简单运动指标。"""

    if not prev:
        return {"motion_energy": 0.0, "bbox_shift": 0.0}

    total_energy = 0.0
    total_shift = 0.0
    for group in ["pose", "left_hand", "right_hand", "face"]:
        prev_box = prev.get(group, {}).get("bbox")
        curr_box = current.get(group, {}).get("bbox")
        if not prev_box or not curr_box:
            continue
        dx = ((curr_box["x_min"] + curr_box["x_max"]) / 2) - ((prev_box["x_min"] + prev_box["x_max"]) / 2)
        dy = ((curr_box["y_min"] + curr_box["y_max"]) / 2) - ((prev_box["y_min"] + prev_box["y_max"]) / 2)
        total_shift += math.hypot(dx, dy)
        total_energy += abs(dx) + abs(dy)
    return {"motion_energy": total_energy, "bbox_shift": total_shift}


def probe_video_with_holistic(
    video_path: Path,
    sample_every_n_frames: int,
    max_frames: Optional[int],
    cv2,
    mp,
) -> Dict[str, Any]:
    """
    对单个视频执行 Holistic 采样。

    如果 mediapipe / opencv 不可用，返回 dry-run 元数据，不做关键点提取。
    """

    meta = probe_video_metadata(video_path)
    sample_rows: List[Dict[str, Any]] = []
    summary: Dict[str, Any] = {
        "video": str(video_path),
        "probe_backend": "dry_run",
        "sample_every_n_frames": sample_every_n_frames,
        "max_frames": max_frames,
        "samples": 0,
        "valid_pose_frames": 0,
        "valid_left_hand_frames": 0,
        "valid_right_hand_frames": 0,
        "valid_face_frames": 0,
        "frame_gap_mean": None,
        "motion_energy_mean": None,
        "motion_energy_max": None,
        "hand_visibility_mean": None,
        "body_visibility_mean": None,
        "face_visibility_mean": None,
    }

    if cv2 is None or mp is None:
        summary["probe_backend"] = "dry_run_no_dependencies"
        return {"meta": meta, "summary": summary, "frames": sample_rows}

    mp_holistic = mp.solutions.holistic

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        summary["probe_backend"] = "cv2_open_failed"
        return {"meta": meta, "summary": summary, "frames": sample_rows}

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    if fps <= 0 and isinstance(meta.get("fps"), (int, float)):
        fps = float(meta["fps"])
    if fps <= 0:
        fps = 25.0

    processed = 0
    sampled_indices: List[int] = []
    prev_row: Optional[Dict[str, Any]] = None
    frame_idx = 0

    with mp_holistic.Holistic(
        static_image_mode=False,
        model_complexity=1,
        smooth_landmarks=True,
        enable_segmentation=False,
        refine_face_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as holistic:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if frame_idx % sample_every_n_frames != 0:
                frame_idx += 1
                continue
            if max_frames is not None and processed >= max_frames:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = holistic.process(rgb)

            height, width = frame.shape[:2]
            pose_landmarks = result.pose_landmarks.landmark if result.pose_landmarks else None
            left_landmarks = result.left_hand_landmarks.landmark if result.left_hand_landmarks else None
            right_landmarks = result.right_hand_landmarks.landmark if result.right_hand_landmarks else None
            face_landmarks = result.face_landmarks.landmark if result.face_landmarks else None

            row: Dict[str, Any] = {
                "frame_idx": frame_idx,
                "timestamp_sec": frame_idx / fps,
                "pose_present": _landmark_presence(result.pose_landmarks),
                "left_hand_present": _landmark_presence(result.left_hand_landmarks),
                "right_hand_present": _landmark_presence(result.right_hand_landmarks),
                "face_present": _landmark_presence(result.face_landmarks),
                "pose": {},
                "left_hand": {},
                "right_hand": {},
                "face": {},
            }

            if pose_landmarks:
                row["pose"] = {
                    "bbox": _bbox_from_landmarks(pose_landmarks, width, height),
                    "visibility_mean": _mean_or_none([float(getattr(lm, "visibility", 1.0)) for lm in pose_landmarks]),
                }
            if left_landmarks:
                row["left_hand"] = {
                    "bbox": _bbox_from_landmarks(left_landmarks, width, height),
                    "visibility_mean": _mean_or_none([float(getattr(lm, "visibility", 1.0)) for lm in left_landmarks]),
                }
            if right_landmarks:
                row["right_hand"] = {
                    "bbox": _bbox_from_landmarks(right_landmarks, width, height),
                    "visibility_mean": _mean_or_none([float(getattr(lm, "visibility", 1.0)) for lm in right_landmarks]),
                }
            if face_landmarks:
                row["face"] = {
                    "bbox": _bbox_from_landmarks(face_landmarks, width, height),
                    "visibility_mean": _mean_or_none([float(getattr(lm, "visibility", 1.0)) for lm in face_landmarks]),
                }

            row.update(_frame_motion(prev_row, row))
            sample_rows.append(row)
            sampled_indices.append(frame_idx)
            prev_row = row
            processed += 1
            frame_idx += 1

    cap.release()

    pose_vis = [float(r["pose"]["visibility_mean"]) for r in sample_rows if r.get("pose_present") and r["pose"].get("visibility_mean") is not None]
    left_vis = [float(r["left_hand"]["visibility_mean"]) for r in sample_rows if r.get("left_hand_present") and r["left_hand"].get("visibility_mean") is not None]
    right_vis = [float(r["right_hand"]["visibility_mean"]) for r in sample_rows if r.get("right_hand_present") and r["right_hand"].get("visibility_mean") is not None]
    face_vis = [float(r["face"]["visibility_mean"]) for r in sample_rows if r.get("face_present") and r["face"].get("visibility_mean") is not None]
    motions = [float(r["motion_energy"]) for r in sample_rows]
    gaps = [sample_rows[i]["timestamp_sec"] - sample_rows[i - 1]["timestamp_sec"] for i in range(1, len(sample_rows))]

    summary.update(
        {
            "probe_backend": "mediapipe_holistic",
            "video_total_frames": total_frames,
            "video_fps": fps,
            "samples": len(sample_rows),
            "sampled_frame_indices": sampled_indices,
            "valid_pose_frames": sum(1 for r in sample_rows if r.get("pose_present")),
            "valid_left_hand_frames": sum(1 for r in sample_rows if r.get("left_hand_present")),
            "valid_right_hand_frames": sum(1 for r in sample_rows if r.get("right_hand_present")),
            "valid_face_frames": sum(1 for r in sample_rows if r.get("face_present")),
            "frame_gap_mean": _mean_or_none(gaps),
            "motion_energy_mean": _mean_or_none(motions),
            "motion_energy_max": max(motions) if motions else None,
            "hand_visibility_mean": _mean_or_none([v for v in left_vis + right_vis if v is not None]),
            "body_visibility_mean": _mean_or_none(pose_vis),
            "face_visibility_mean": _mean_or_none(face_vis),
            "left_hand_presence_ratio": (sum(1 for r in sample_rows if r.get("left_hand_present")) / len(sample_rows)) if sample_rows else None,
            "right_hand_presence_ratio": (sum(1 for r in sample_rows if r.get("right_hand_present")) / len(sample_rows)) if sample_rows else None,
            "pose_presence_ratio": (sum(1 for r in sample_rows if r.get("pose_present")) / len(sample_rows)) if sample_rows else None,
            "face_presence_ratio": (sum(1 for r in sample_rows if r.get("face_present")) / len(sample_rows)) if sample_rows else None,
        }
    )

    return {"meta": meta, "summary": summary, "frames": sample_rows}


def build_report(result: Dict[str, Any]) -> str:
    """生成 Markdown 汇总。"""

    lines = []
    lines.append("# Holistic 采样探针报告")
    lines.append("")
    lines.append(f"- 生成时间：{result['generated_at']}")
    lines.append(f"- 视频数量：{len(result['videos'])}")
    lines.append(f"- 输出目录：{result['output_dir']}")
    lines.append("")
    for item in result["videos"]:
        summary = item["summary"]
        lines.append(f"## {Path(item['meta']['path']).name}")
        lines.append(f"- 探针后端：{summary['probe_backend']}")
        lines.append(f"- 采样帧数：{summary['samples']}")
        lines.append(f"- 人体检测占比：{summary.get('pose_presence_ratio')}")
        lines.append(f"- 左手检测占比：{summary.get('left_hand_presence_ratio')}")
        lines.append(f"- 右手检测占比：{summary.get('right_hand_presence_ratio')}")
        lines.append(f"- 面部检测占比：{summary.get('face_presence_ratio')}")
        lines.append(f"- 平均运动能量：{summary.get('motion_energy_mean')}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="运行 MediaPipe Holistic 采样探针")
    parser.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT), help="仓库根目录")
    parser.add_argument("--video-root", default=str(DEFAULT_VIDEO_ROOT), help="视频根目录")
    parser.add_argument("--video", default=None, help="只处理单个视频")
    parser.add_argument("--sample-every-n-frames", type=int, default=5, help="每隔多少帧采样一次")
    parser.add_argument("--max-frames", type=int, default=120, help="单个视频最多处理多少个采样帧")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="输出目录")
    parser.add_argument("--no-report", action="store_true", help="只输出 JSON，不生成 Markdown")
    args = parser.parse_args(argv)

    # 在无头环境里默认关闭 Qt/X11 依赖，避免 OpenCV/MediaPipe 误连图形会话。
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ.setdefault("DISPLAY", "")

    repo_root = Path(args.repo_root)
    video_root = Path(args.video_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cv2, mp = _import_optional_backends()

    if args.video:
        videos = [Path(args.video)]
    else:
        videos = find_demo_videos(video_root)

    all_results: List[Dict[str, Any]] = []
    for video_path in videos:
        result = probe_video_with_holistic(
            video_path=video_path,
            sample_every_n_frames=args.sample_every_n_frames,
            max_frames=args.max_frames,
            cv2=cv2,
            mp=mp,
        )
        all_results.append(result)

        stem = video_path.stem
        video_dir = output_dir / stem
        video_dir.mkdir(parents=True, exist_ok=True)
        (video_dir / f"{stem}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

        with (video_dir / f"{stem}_frames.jsonl").open("w", encoding="utf-8") as f:
            for frame in result["frames"]:
                f.write(json.dumps(frame, ensure_ascii=False) + "\n")

        with (video_dir / f"{stem}_frames.csv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["frame_idx", "timestamp_sec", "pose_present", "left_hand_present", "right_hand_present", "face_present", "motion_energy", "bbox_shift"])
            for frame in result["frames"]:
                writer.writerow([
                    frame.get("frame_idx"),
                    frame.get("timestamp_sec"),
                    frame.get("pose_present"),
                    frame.get("left_hand_present"),
                    frame.get("right_hand_present"),
                    frame.get("face_present"),
                    frame.get("motion_energy"),
                    frame.get("bbox_shift"),
                ])

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "repo_root": str(repo_root),
        "video_root": str(video_root),
        "output_dir": str(output_dir),
        "sample_every_n_frames": args.sample_every_n_frames,
        "max_frames": args.max_frames,
        "videos": all_results,
    }

    json_path = output_dir / "holistic_probe_summary.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if not args.no_report:
        md_path = output_dir / "holistic_probe_summary.md"
        md_path.write_text(build_report(payload), encoding="utf-8")

    print(f"已生成 Holistic 探针汇总：{json_path}")
    if not args.no_report:
        print(f"已生成 Markdown 报告：{output_dir / 'holistic_probe_summary.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

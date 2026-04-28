#!/usr/bin/env python3
"""
关键帧采样策略公共工具。

这个模块给三种采样方式复用：
1. 全视频均匀采样
2. 两阶段采样
3. 自适应采样

核心职责：
- 读取视频元数据
- 构造采样帧序列
- 在选定帧上运行 MediaPipe Holistic
- 汇总采样覆盖范围、尾部覆盖和基础关键点统计
"""

from __future__ import annotations

import json
import math
import os
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from signlanguage_common import probe_video_metadata


DEFAULT_REPO_ROOT = Path("/data/WYC/signLanguage")
DEFAULT_VIDEO_ROOT = DEFAULT_REPO_ROOT / "data" / "Demo词汇视频"


def configure_headless() -> None:
    """在服务器/无头环境里关闭 Qt/X11 依赖。"""

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ.setdefault("DISPLAY", "")


def import_optional_backends():
    """按需导入 OpenCV 和 MediaPipe。"""

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
    """计算相邻关键帧之间的简单运动量。"""

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


def normalize_total_frames(meta: Dict[str, Any]) -> int:
    """从元数据中推断总帧数。"""

    frame_count = meta.get("frame_count")
    if isinstance(frame_count, int) and frame_count > 0:
        return frame_count

    duration = meta.get("duration_sec")
    fps = meta.get("fps")
    if isinstance(duration, (int, float)) and isinstance(fps, (int, float)) and duration > 0 and fps > 0:
        return max(1, int(round(duration * fps)))

    return 1


def normalized_video_duration(meta: Dict[str, Any], total_frames: int) -> float:
    """从元数据推断总时长。"""

    duration = meta.get("duration_sec")
    fps = meta.get("fps")
    if isinstance(duration, (int, float)) and duration > 0:
        return float(duration)
    if isinstance(fps, (int, float)) and fps > 0 and total_frames > 0:
        return float(total_frames / fps)
    return float(total_frames)


def even_frame_indices(total_frames: int, count: int) -> List[int]:
    """在整段视频上均匀取帧。"""

    if total_frames <= 1:
        return [0]

    count = max(1, min(count, total_frames))
    if count == 1:
        return [0]
    if count == total_frames:
        return list(range(total_frames))

    raw = [int(round(i * (total_frames - 1) / (count - 1))) for i in range(count)]
    indices: List[int] = []
    for idx in raw:
        if idx not in indices:
            indices.append(idx)
    return indices


def interior_frame_indices(start: int, end: int, count: int) -> List[int]:
    """在一个区间内部均匀取帧，不包含端点。"""

    if end - start <= 1 or count <= 0:
        return []

    span = end - start
    raw = [int(round(start + (i + 1) * span / (count + 1))) for i in range(count)]
    result: List[int] = []
    for idx in raw:
        idx = max(start + 1, min(end - 1, idx))
        if idx not in result:
            result.append(idx)
    return result


def _open_holistic():
    """构造 Holistic 模型。"""

    cv2, mp = import_optional_backends()
    if cv2 is None or mp is None:
        return cv2, mp, None
    holistic = mp.solutions.holistic
    return cv2, mp, holistic


def _build_row_from_frame(frame_idx: int, fps: float, frame, holistic, cv2) -> Dict[str, Any]:
    """把单帧转换成统一的关键点统计结构。"""

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

    return row


def extract_holistic_rows(video_path: Path, frame_indices: Sequence[int]) -> Dict[str, Any]:
    """
    在指定帧上运行 Holistic。

    返回结构：
    - meta: 视频元数据
    - rows: 帧级结果
    - summary: 采样统计
    """

    meta = probe_video_metadata(video_path)
    total_frames = normalize_total_frames(meta)
    fps = float(meta.get("fps") or 25.0)

    cv2, mp, holistic_cls = _open_holistic()
    selected = sorted({idx for idx in frame_indices if isinstance(idx, int) and idx >= 0})
    if not selected:
        return {
            "meta": meta,
            "rows": [],
            "summary": {
                "samples": 0,
                "sampled_frame_indices": [],
                "video_total_frames": total_frames,
                "video_fps": fps,
                "video_duration_sec": normalized_video_duration(meta, total_frames),
                "pose_presence_ratio": None,
                "left_hand_presence_ratio": None,
                "right_hand_presence_ratio": None,
                "face_presence_ratio": None,
                "motion_energy_mean": None,
                "motion_energy_max": None,
                "frame_span_ratio": None,
                "tail_coverage_ratio": None,
                "late_half_fraction": None,
                "late_75_fraction": None,
                "first_sample_frame": None,
                "last_sample_frame": None,
            },
        }

    if cv2 is None or mp is None or holistic_cls is None:
        raise RuntimeError("需要安装 mediapipe 和 opencv-python 才能运行关键帧采样实验")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"无法打开视频：{video_path}")

    processed: List[Dict[str, Any]] = []
    prev_row: Optional[Dict[str, Any]] = None
    selected_set = set(selected)
    target_idx = 0
    target = selected[target_idx]
    max_target = selected[-1]
    frame_idx = 0

    with holistic_cls.Holistic(
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
            if frame_idx > max_target:
                break
            if frame_idx < target:
                frame_idx += 1
                continue

            if frame_idx == target and frame_idx in selected_set:
                row = _build_row_from_frame(frame_idx, fps, frame, holistic, cv2)
                row.update(_frame_motion(prev_row, row))
                processed.append(row)
                prev_row = row

                if target_idx + 1 < len(selected):
                    target_idx += 1
                    target = selected[target_idx]
                else:
                    target = max_target + 1

            frame_idx += 1

    cap.release()

    pose_vis = [float(r["pose"]["visibility_mean"]) for r in processed if r.get("pose_present") and r["pose"].get("visibility_mean") is not None]
    left_vis = [float(r["left_hand"]["visibility_mean"]) for r in processed if r.get("left_hand_present") and r["left_hand"].get("visibility_mean") is not None]
    right_vis = [float(r["right_hand"]["visibility_mean"]) for r in processed if r.get("right_hand_present") and r["right_hand"].get("visibility_mean") is not None]
    face_vis = [float(r["face"]["visibility_mean"]) for r in processed if r.get("face_present") and r["face"].get("visibility_mean") is not None]
    motions = [float(r["motion_energy"]) for r in processed]
    frame_span_ratio = None
    tail_coverage_ratio = None
    late_half_fraction = None
    late_75_fraction = None
    first_sample_frame = processed[0]["frame_idx"] if processed else None
    last_sample_frame = processed[-1]["frame_idx"] if processed else None
    if processed and total_frames > 1:
        frame_span_ratio = (last_sample_frame - first_sample_frame) / (total_frames - 1)
        tail_coverage_ratio = last_sample_frame / (total_frames - 1)
        late_half_fraction = sum(1 for r in processed if r["frame_idx"] >= 0.5 * (total_frames - 1)) / len(processed)
        late_75_fraction = sum(1 for r in processed if r["frame_idx"] >= 0.75 * (total_frames - 1)) / len(processed)

    summary = {
        "samples": len(processed),
        "sampled_frame_indices": [r["frame_idx"] for r in processed],
        "video_total_frames": total_frames,
        "video_fps": fps,
        "video_duration_sec": normalized_video_duration(meta, total_frames),
        "first_sample_sec": processed[0]["timestamp_sec"] if processed else None,
        "last_sample_sec": processed[-1]["timestamp_sec"] if processed else None,
        "pose_presence_ratio": (sum(1 for r in processed if r.get("pose_present")) / len(processed)) if processed else None,
        "left_hand_presence_ratio": (sum(1 for r in processed if r.get("left_hand_present")) / len(processed)) if processed else None,
        "right_hand_presence_ratio": (sum(1 for r in processed if r.get("right_hand_present")) / len(processed)) if processed else None,
        "face_presence_ratio": (sum(1 for r in processed if r.get("face_present")) / len(processed)) if processed else None,
        "motion_energy_mean": _mean_or_none(motions),
        "motion_energy_max": max(motions) if motions else None,
        "body_visibility_mean": _mean_or_none(pose_vis),
        "hand_visibility_mean": _mean_or_none(left_vis + right_vis),
        "face_visibility_mean": _mean_or_none(face_vis),
        "frame_span_ratio": frame_span_ratio,
        "tail_coverage_ratio": tail_coverage_ratio,
        "late_half_fraction": late_half_fraction,
        "late_75_fraction": late_75_fraction,
        "first_sample_frame": first_sample_frame,
        "last_sample_frame": last_sample_frame,
    }

    return {"meta": meta, "rows": processed, "summary": summary}


def extract_single_holistic_row(video_path: Path, frame_idx: int) -> Dict[str, Any]:
    """提取单帧的 Holistic 结果。"""

    meta = probe_video_metadata(video_path)
    fps = float(meta.get("fps") or 25.0)
    cv2, mp, holistic_cls = _open_holistic()
    if cv2 is None or mp is None or holistic_cls is None:
        raise RuntimeError("需要安装 mediapipe 和 opencv-python 才能运行关键帧采样实验")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"无法打开视频：{video_path}")

    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise RuntimeError(f"无法读取帧：{video_path} @ {frame_idx}")

    with holistic_cls.Holistic(
        static_image_mode=False,
        model_complexity=1,
        smooth_landmarks=True,
        enable_segmentation=False,
        refine_face_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as holistic:
        row = _build_row_from_frame(frame_idx, fps, frame, holistic, cv2)
        row.update({"motion_energy": 0.0, "bbox_shift": 0.0})
        return row


def rows_to_map(rows: Sequence[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """把帧列表转成以 frame_idx 为键的字典。"""

    return {int(row["frame_idx"]): dict(row) for row in rows}


def segment_score(left_idx: int, right_idx: int, row_map: Dict[int, Dict[str, Any]], total_frames: int) -> float:
    """
    给一个区间打分。

    打分越高，表示越值得在该区间内继续加密采样。
    """

    if right_idx <= left_idx:
        return 0.0

    left_row = row_map[left_idx]
    right_row = row_map[right_idx]
    span_ratio = (right_idx - left_idx) / max(1, total_frames - 1)
    center_ratio = ((left_idx + right_idx) / 2) / max(1, total_frames - 1)
    max_motion = max((float(r.get("motion_energy", 0.0)) for r in row_map.values()), default=0.0)
    motion_peak = max(float(left_row.get("motion_energy", 0.0)), float(right_row.get("motion_energy", 0.0)))
    motion_norm = motion_peak / max_motion if max_motion > 0 else 0.0

    left_presence = sum(
        1 for key in ["pose_present", "left_hand_present", "right_hand_present", "face_present"]
        if left_row.get(key)
    ) / 4.0
    right_presence = sum(
        1 for key in ["pose_present", "left_hand_present", "right_hand_present", "face_present"]
        if right_row.get(key)
    ) / 4.0
    presence_score = max(left_presence, right_presence)
    return 0.42 * span_ratio + 0.33 * motion_norm + 0.15 * presence_score + 0.10 * center_ratio


def choose_interior_frame(left_idx: int, right_idx: int, selected: Iterable[int]) -> Optional[int]:
    """在区间内部选择一个尚未采样的帧。"""

    if right_idx - left_idx <= 1:
        return None

    selected_set = set(selected)
    mid = (left_idx + right_idx) // 2
    if mid not in selected_set and left_idx < mid < right_idx:
        return mid

    # 如果整数中点已经被占用，向两侧寻找最近的空位。
    for offset in range(1, right_idx - left_idx):
        candidates = [mid - offset, mid + offset]
        for cand in candidates:
            if left_idx < cand < right_idx and cand not in selected_set:
                return cand
    return None


def build_report(payload: Dict[str, Any], title: str) -> str:
    """生成便于汇报的 Markdown 报告。"""

    rows = payload["videos"]
    lines: List[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"- 生成时间：{payload.get('generated_at')}")
    lines.append(f"- 视频数量：{len(rows)}")
    lines.append(f"- 采样预算：{payload.get('sample_budget')}")
    lines.append("")

    metrics = ["frame_span_ratio", "tail_coverage_ratio", "late_half_fraction", "late_75_fraction"]
    lines.append("## 总体统计")
    lines.append("")
    for key in metrics:
        vals = [r["evaluation"].get(key) for r in rows if isinstance(r["evaluation"].get(key), (int, float))]
        lines.append(f"- `{key}` 均值：{_mean_or_none([float(v) for v in vals])}")
    lines.append("")

    lines.append("## 视频级结果")
    lines.append("")
    for row in rows:
        eval_ = row["evaluation"]
        lines.append(f"### {row['video']}")
        lines.append(f"- 采样帧：{', '.join(str(x) for x in row['sampled_frame_indices'])}")
        lines.append(f"- 时间覆盖：{eval_.get('first_sample_sec')}s -> {eval_.get('last_sample_sec')}s")
        lines.append(f"- 帧覆盖比例：{eval_.get('frame_span_ratio')}")
        lines.append(f"- 尾部覆盖比例：{eval_.get('tail_coverage_ratio')}")
        lines.append(f"- 后半段采样占比：{eval_.get('late_half_fraction')}")
        lines.append(f"- 后 75% 采样占比：{eval_.get('late_75_fraction')}")
        lines.append(f"- pose/left/right/face：{eval_.get('pose_presence_ratio')}/{eval_.get('left_hand_presence_ratio')}/{eval_.get('right_hand_presence_ratio')}/{eval_.get('face_presence_ratio')}")
        lines.append(f"- 平均运动能量：{eval_.get('motion_energy_mean')}")
        if row.get("processing_sec") is not None:
            lines.append(f"- 处理耗时：{row.get('processing_sec')}s")
        for tip in row.get("strategy_notes", []):
            lines.append(f"- 建议：{tip}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"

#!/usr/bin/env python3
"""
Holistic 常驻 worker。

协议：
- stdin 输入 JSON 行
- stdout 输出 JSON 行

支持命令：
- `process`：处理一个视频的一组帧
- `ping`：心跳
- `shutdown`：退出

worker 在启动时只初始化一次 Holistic，随后可反复处理多个请求。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from keyframe_sampling_common import (
    configure_headless,
    decode_frame_payload,
    import_optional_backends,
    normalize_total_frames,
    probe_video_metadata,
    _process_frame,
    _serialize_holistic_result,
    _frame_motion,
)


DEFAULT_MODEL_COMPLEXITY = 1
DEFAULT_STATIC_IMAGE_MODE = True


def _json_print(payload: Dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _read_frames(
    cv2,
    video_path: Path,
    frame_indices: Sequence[int],
    max_width: int = 0,
) -> Dict[str, Any]:
    """按帧号升序连续解码，避免对密集目标逐帧随机 seek。"""

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"无法打开视频：{video_path}")

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    targets = sorted({int(value) for value in frame_indices if int(value) >= 0})
    frames: List[Dict[str, Any]] = []
    if not targets:
        cap.release()
        return {"fps": fps, "total_frames": total_frames, "frames": frames}

    target_set = set(targets)
    first_idx, last_idx = targets[0], targets[-1]
    cap.set(cv2.CAP_PROP_POS_FRAMES, first_idx)
    frame_idx = first_idx
    while frame_idx <= last_idx:
        ok, frame = cap.read()
        if not ok:
            break
        if frame_idx in target_set:
            if max_width > 0 and frame.shape[1] > max_width:
                scale = max_width / frame.shape[1]
                frame = cv2.resize(
                    frame,
                    (max_width, max(1, int(round(frame.shape[0] * scale)))),
                    interpolation=cv2.INTER_AREA,
                )
            frames.append({"frame_idx": frame_idx, "frame": frame, "fps": fps})
        frame_idx += 1
    cap.release()
    found = {item["frame_idx"] for item in frames}
    missing = sorted(target_set - found)
    if missing:
        retry_cap = cv2.VideoCapture(str(video_path))
        if retry_cap.isOpened():
            for target in missing:
                retry_cap.set(cv2.CAP_PROP_POS_FRAMES, target)
                ok, frame = retry_cap.read()
                if not ok:
                    continue
                if max_width > 0 and frame.shape[1] > max_width:
                    scale = max_width / frame.shape[1]
                    frame = cv2.resize(
                        frame,
                        (max_width, max(1, int(round(frame.shape[0] * scale)))),
                        interpolation=cv2.INTER_AREA,
                    )
                frames.append({"frame_idx": target, "frame": frame, "fps": fps})
            retry_cap.release()
    frames.sort(key=lambda item: item["frame_idx"])
    found = {item["frame_idx"] for item in frames}
    missing = sorted(target_set - found)
    return {
        "fps": fps,
        "total_frames": total_frames,
        "frames": frames,
        "missing_frame_indices": missing,
    }


def _process_video_request(
    holistic,
    cv2,
    request: Dict[str, Any],
    static_image_mode: bool,
) -> Dict[str, Any]:
    request_id = request.get("request_id") or f"req-{int(time.time() * 1000)}"
    video_path = Path(request["video_path"])
    raw_indices = request.get("frame_indices") or []
    raw_weights = request.get("frame_weights") or []
    weight_by_index: Dict[int, float] = {}
    for idx, value in zip(raw_indices, raw_weights):
        try:
            weight_by_index[int(idx)] = max(0.05, float(value))
        except (TypeError, ValueError):
            continue
    frame_indices = sorted({int(idx) for idx in raw_indices if int(idx) >= 0})

    started = time.perf_counter()
    probe_start = time.perf_counter()
    meta = probe_video_metadata(video_path)
    probe_sec = round(time.perf_counter() - probe_start, 3)

    read_start = time.perf_counter()
    frame_bundle = _read_frames(
        cv2,
        video_path,
        frame_indices,
        max_width=int(request.get("max_width") or 0),
    )
    ingest_sec = round(time.perf_counter() - read_start, 3)

    processed: List[Dict[str, Any]] = []
    result_records: List[Dict[str, Any]] = []
    prev_row: Optional[Dict[str, Any]] = None
    process_secs: List[float] = []

    for item in frame_bundle["frames"]:
        frame_idx = int(item["frame_idx"])
        frame = item["frame"]
        fps = float(item["fps"])
        row_start = time.perf_counter()
        row, result = _process_frame(frame_idx, fps, frame, holistic, cv2)
        frame_eval_sec = round(time.perf_counter() - row_start, 3)
        frame_weight = float(weight_by_index.get(frame_idx, 1.0))
        row["frame_weight"] = frame_weight
        row.update(_frame_motion(prev_row, row))
        prev_row = row
        processed.append(row)
        process_secs.append(frame_eval_sec)
        result_records.append(
            {
                "frame_idx": frame_idx,
                "timestamp_sec": frame_idx / fps,
                "row": row,
                "result_data": _serialize_holistic_result(result),
                "frame_eval_sec": frame_eval_sec,
                "frame_weight": frame_weight,
            }
        )

    result_dir = request.get("result_dir")
    result_file: Optional[str] = None
    if result_dir:
        out_dir = Path(result_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        result_file_path = out_dir / f"{video_path.stem}_holistic_results.json"
        result_payload = {
            "video": str(video_path),
            "video_stem": video_path.stem,
            "fps": frame_bundle["fps"],
            "total_frames": frame_bundle["total_frames"] or normalize_total_frames(meta),
            "sampled_frame_indices": frame_indices,
            "frame_weights": [float(weight_by_index.get(idx, 1.0)) for idx in frame_indices],
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "static_image_mode": static_image_mode,
            "input_mode": "video",
            "records": result_records,
        }
        result_file_path.write_text(json.dumps(result_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        result_file = str(result_file_path)

    total_sec = round(time.perf_counter() - started, 3)
    response = {
        "type": "result",
        "request_id": request_id,
        "input_mode": "video",
        "video": video_path.name,
        "video_path": str(video_path),
        "frame_indices": frame_indices,
        "static_image_mode": static_image_mode,
        "probe_sec": probe_sec,
        "read_sec": ingest_sec,
        "ingest_sec": ingest_sec,
        "holistic_eval_sec": round(sum(process_secs), 3),
        "process_secs": process_secs,
        "request_total_sec": total_sec,
        "result_file": result_file,
        "samples": len(processed),
        "missing_frame_indices": frame_bundle.get("missing_frame_indices", []),
        "rows": processed,
        "meta": meta,
    }
    if request.get("include_records"):
        response["records"] = result_records
    return response


def _process_frame_slice_request(
    holistic,
    cv2,
    request: Dict[str, Any],
    static_image_mode: bool,
) -> Dict[str, Any]:
    """处理前端直接传入的帧切片，不再读取视频。"""

    request_id = request.get("request_id") or f"req-{int(time.time() * 1000)}"
    video_stem = request.get("video_stem") or request.get("video") or request_id
    raw_frames = request.get("frames") or []
    fps = float(request.get("fps") or request.get("video_meta", {}).get("fps") or 25.0)
    total_frames_value = request.get("total_frames")
    if not isinstance(total_frames_value, int) or total_frames_value <= 0:
        total_frames_value = 0

    raw_indices = request.get("frame_indices") or []
    raw_weights = request.get("frame_weights") or []
    weight_by_index: Dict[int, float] = {}
    for idx, value in zip(raw_indices, raw_weights):
        try:
            weight_by_index[int(idx)] = max(0.05, float(value))
        except (TypeError, ValueError):
            continue
    frame_pairs: List[Tuple[int, Dict[str, Any]]] = []
    for idx, payload in zip(raw_indices, raw_frames):
        frame_idx = int(idx)
        if frame_idx >= 0:
            frame_pairs.append((frame_idx, payload))
    unique_pairs: List[Tuple[int, Dict[str, Any]]] = []
    seen_indices = set()
    for item in frame_pairs:
        if item[0] in seen_indices:
            continue
        unique_pairs.append(item)
        seen_indices.add(item[0])
    frame_pairs = sorted(unique_pairs, key=lambda item: item[0])
    frame_indices = [idx for idx, _ in frame_pairs]

    if len(raw_frames) != len(raw_indices):
        raise RuntimeError("帧切片请求需要 frames 和 frame_indices 一一对应")

    started = time.perf_counter()
    decode_start = time.perf_counter()
    decoded_frames: List[Dict[str, Any]] = []
    for idx, payload in frame_pairs:
        frame = decode_frame_payload(cv2, payload)
        decoded_frames.append({"frame_idx": int(idx), "frame": frame, "fps": fps})
    ingest_sec = round(time.perf_counter() - decode_start, 3)

    processed: List[Dict[str, Any]] = []
    result_records: List[Dict[str, Any]] = []
    prev_row: Optional[Dict[str, Any]] = None
    process_secs: List[float] = []

    for item in decoded_frames:
        frame_idx = int(item["frame_idx"])
        frame = item["frame"]
        row_fps = float(item["fps"])
        row_start = time.perf_counter()
        row, result = _process_frame(frame_idx, row_fps, frame, holistic, cv2)
        frame_eval_sec = round(time.perf_counter() - row_start, 3)
        frame_weight = float(weight_by_index.get(frame_idx, 1.0))
        row["frame_weight"] = frame_weight
        row.update(_frame_motion(prev_row, row))
        prev_row = row
        processed.append(row)
        process_secs.append(frame_eval_sec)
        result_records.append(
            {
                "frame_idx": frame_idx,
                "timestamp_sec": frame_idx / row_fps,
                "row": row,
                "result_data": _serialize_holistic_result(result),
                "frame_eval_sec": frame_eval_sec,
                "frame_weight": frame_weight,
            }
        )

    result_dir = request.get("result_dir")
    result_file: Optional[str] = None
    if result_dir:
        out_dir = Path(result_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        result_file_path = out_dir / f"{video_stem}_holistic_results.json"
        result_payload = {
            "video": request.get("video_path") or video_stem,
            "video_stem": video_stem,
            "fps": fps,
            "total_frames": total_frames_value,
            "sampled_frame_indices": frame_indices,
            "frame_weights": [float(weight_by_index.get(idx, 1.0)) for idx in frame_indices],
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "static_image_mode": static_image_mode,
            "input_mode": "frame_slices",
            "records": result_records,
        }
        result_file_path.write_text(json.dumps(result_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        result_file = str(result_file_path)

    total_sec = round(time.perf_counter() - started, 3)
    return {
        "type": "result",
        "request_id": request_id,
        "input_mode": "frame_slices",
        "video": video_stem,
        "video_path": request.get("video_path"),
        "frame_indices": frame_indices,
        "static_image_mode": static_image_mode,
        "probe_sec": 0.0,
        "read_sec": ingest_sec,
        "ingest_sec": ingest_sec,
        "holistic_eval_sec": round(sum(process_secs), 3),
        "process_secs": process_secs,
        "request_total_sec": total_sec,
        "result_file": result_file,
        "samples": len(processed),
        "rows": processed,
        "meta": {
            "fps": fps,
            "total_frames": total_frames_value or None,
            "video_stem": video_stem,
        },
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    configure_headless()
    parser = argparse.ArgumentParser(description="Holistic 常驻 worker")
    parser.add_argument("--model-complexity", type=int, default=DEFAULT_MODEL_COMPLEXITY, help="Holistic 模型复杂度")
    parser.add_argument(
        "--static-image-mode",
        action="store_true",
        default=DEFAULT_STATIC_IMAGE_MODE,
        help="使用静态图像模式；对跨请求复用更安全",
    )
    args = parser.parse_args(argv)

    cv2, mp = import_optional_backends()
    if cv2 is None or mp is None:
        raise RuntimeError("需要安装 mediapipe 和 opencv-python 才能启动 worker")

    holistic_module = mp.solutions.holistic
    init_start = time.perf_counter()
    with holistic_module.Holistic(
        static_image_mode=args.static_image_mode,
        model_complexity=args.model_complexity,
        smooth_landmarks=True,
        enable_segmentation=False,
        refine_face_landmarks=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as holistic:
        init_sec = round(time.perf_counter() - init_start, 3)
        _json_print(
            {
                "type": "ready",
                "pid": os.getpid(),
                "started_at": datetime.now().isoformat(timespec="seconds"),
                "holistic_init_sec": init_sec,
                "model_complexity": args.model_complexity,
                "static_image_mode": args.static_image_mode,
            }
        )

        while True:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
            except Exception as exc:
                _json_print({"type": "error", "error": f"invalid_json: {exc}"})
                continue

            cmd = request.get("cmd", "process")
            if cmd == "shutdown":
                _json_print({"type": "shutdown_ok", "pid": os.getpid()})
                break
            if cmd == "ping":
                _json_print({"type": "pong", "pid": os.getpid(), "ts": datetime.now().isoformat(timespec="seconds")})
                continue

            try:
                if "frames" in request:
                    response = _process_frame_slice_request(holistic, cv2, request, args.static_image_mode)
                else:
                    response = _process_video_request(holistic, cv2, request, args.static_image_mode)
                _json_print(response)
            except Exception as exc:
                _json_print({"type": "error", "request_id": request.get("request_id"), "error": str(exc)})

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

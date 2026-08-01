#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""使用多个常驻 Holistic daemon 构建词汇优先的原始 Landmark 数据库。"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import cv2

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import build_raw_holistic_landmark_database as rawdb


def read_json_line(stream):
    line = stream.readline()
    if not line:
        raise RuntimeError("Holistic worker exited before response")
    return json.loads(line)


def send_json_line(stream, payload):
    stream.write(json.dumps(payload, ensure_ascii=False) + "\n")
    stream.flush()


def launch_worker(python: str, worker_script: Path):
    process = subprocess.Popen(
        [python, str(worker_script), "--model-complexity", "1", "--static-image-mode"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        bufsize=1,
    )
    if process.stdin is None or process.stdout is None:
        process.kill()
        raise RuntimeError("worker pipes unavailable")
    ready = read_json_line(process.stdout)
    if ready.get("type") != "ready":
        process.kill()
        raise RuntimeError(f"worker not ready: {ready}")
    return process, ready


def compatible_points(
    points: list[dict],
    fields: list[str],
    source_ids: list[int] | None = None,
) -> list[dict[str, float]]:
    """保存与旧 worker result_data 一致的坐标对象格式。"""
    source = points or []
    selected = source if source_ids is None else [source[index] for index in source_ids if index < len(source)]
    rows = []
    for point in selected:
        row = {}
        for field in fields:
            default = 1.0 if field in {"visibility", "presence"} else 0.0
            row[field] = round(float(point.get(field, default)), 7)
        rows.append(row)
    return rows


def safe_word_dir(word_index: int, word: str) -> str:
    cleaned = word.replace("/", "_ ").replace("\\", "_").strip()
    return f"{word_index:02d}_{cleaned}"


def shard_path_v2(output_root: Path, segment: dict, user_id: int, view: str) -> Path:
    word_index = int(segment["word_index"])
    repeat_index = int(segment["repeat_index"])
    return (
        output_root
        / "landmarks"
        / safe_word_dir(word_index, segment["word"])
        / f"用户_{user_id:02d}"
        / view
        / f"重复_{repeat_index:02d}.json"
    )


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def video_meta(path: Path) -> tuple[float, int, float]:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"cannot open video: {path}")
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    cap.release()
    return fps, total_frames, total_frames / fps if fps else 0.0


def frame_indices_for_item(item: dict, sample_fps: float) -> tuple[list[int], float, int, float, int]:
    fps, total_frames, duration = video_meta(item["video"])
    step = max(1, int(round(fps / max(sample_fps, 1.0))))
    first = max(0, int(math.ceil(float(item["segments"][0]["start_sec"]) * fps)))
    final_exclusive = min(total_frames, int(math.ceil(float(item["segments"][-1]["end_sec"]) * fps)))
    indices = list(range(first, final_exclusive, step))
    return indices, fps, total_frames, duration, step


def write_item_shards(item: dict, response: dict, output_root: Path, sample_fps: float, max_width: int) -> list[dict]:
    user_id, view = item["user_id"], item["view"]
    indices, fps, total_frames, duration, step = frame_indices_for_item(item, sample_fps)
    records = response.get("records") or []
    record_by_index = {int(record["frame_idx"]): record for record in records}
    missing = sorted(set(indices) - set(record_by_index))
    missing_rate = len(missing) / max(len(indices), 1)
    if missing_rate > 0.05:
        raise RuntimeError(
            f"worker response missing {len(missing)}/{len(indices)} frames "
            f"({missing_rate:.1%}): {missing[:5]}"
        )
    source_id = rawdb.source_video_id(item["video"])
    summaries = []
    for segment in item["segments"]:
        start, end = float(segment["start_sec"]), float(segment["end_sec"])
        frames = []
        present = dict.fromkeys(rawdb.LANDMARK_GROUPS, 0)
        requested_in_segment = [
            frame_idx for frame_idx in indices
            if start <= frame_idx / fps < end
        ]
        missing_in_segment = [frame_idx for frame_idx in requested_in_segment if frame_idx not in record_by_index]
        for frame_idx in requested_in_segment:
            if frame_idx not in record_by_index:
                continue
            timestamp = frame_idx / fps
            result_data = record_by_index[frame_idx]["result_data"]
            groups = {
                "pose_landmarks": compatible_points(
                    result_data.get("pose_landmarks") or [],
                    rawdb.LANDMARK_GROUPS["pose"]["fields"],
                    rawdb.LANDMARK_GROUPS["pose"]["source_ids"],
                ),
                "left_hand_landmarks": compatible_points(
                    result_data.get("left_hand_landmarks") or [],
                    rawdb.LANDMARK_GROUPS["left_hand"]["fields"],
                    rawdb.LANDMARK_GROUPS["left_hand"]["source_ids"],
                ),
                "right_hand_landmarks": compatible_points(
                    result_data.get("right_hand_landmarks") or [],
                    rawdb.LANDMARK_GROUPS["right_hand"]["fields"],
                    rawdb.LANDMARK_GROUPS["right_hand"]["source_ids"],
                ),
                "face_landmarks": compatible_points(
                    result_data.get("face_landmarks") or [],
                    rawdb.LANDMARK_GROUPS["face"]["fields"],
                    rawdb.LANDMARK_GROUPS["face"]["source_ids"],
                ),
            }
            presence_map = {
                "pose": bool(groups["pose_landmarks"]),
                "left_hand": bool(groups["left_hand_landmarks"]),
                "right_hand": bool(groups["right_hand_landmarks"]),
                "face": bool(groups["face_landmarks"]),
            }
            for name, value in presence_map.items():
                if value:
                    present[name] += 1
            frames.append({
                "frame_idx": frame_idx,
                "timestamp_sec": round(timestamp, 7),
                "segment_timestamp_sec": round(timestamp - start, 7),
                "frame_weight": 1.0,
                "row": {
                    "frame_idx": frame_idx,
                    "timestamp_sec": round(timestamp, 7),
                    "pose_present": presence_map["pose"],
                    "left_hand_present": presence_map["left_hand"],
                    "right_hand_present": presence_map["right_hand"],
                    "face_present": presence_map["face"],
                    "frame_weight": 1.0,
                },
                "result_data": groups,
            })
        sample_id = rawdb.segment_id(segment, user_id, view)
        shard = shard_path_v2(output_root, segment, user_id, view)
        count = len(frames)
        summary = {
            "sample_id": sample_id,
            "word": segment["word"],
            "word_index": int(segment["word_index"]),
            "user_id": user_id,
            "view": view,
            "repeat_index": int(segment["repeat_index"]),
            "start_sec": start,
            "end_sec": end,
            "duration_sec": end - start,
            "requested_frame_count": len(requested_in_segment),
            "sampled_frame_count": count,
            "missing_frame_count": len(missing_in_segment),
            "missing_frame_indices": missing_in_segment,
            "presence_rate": {
                name: round(value / count, 6) if count else 0.0
                for name, value in present.items()
            },
            "landmark_shard": str(shard.relative_to(output_root)),
            "review_status": "pending_manual_cutpoint_review",
            "source_integrity": segment.get("source_integrity", "available"),
        }
        payload = {
            "schema_version": "slu-raw-holistic-segment-v2-legacy-coordinate-compatible",
            "sample_id": sample_id,
            "video": source_id,
            "video_stem": sample_id,
            "fps": fps,
            "total_frames": total_frames,
            "sampled_frame_indices": [record["frame_idx"] for record in frames],
            "frame_weights": [1.0] * len(frames),
            "static_image_mode": True,
            "input_mode": "video_segment",
            "review_status": "pending_manual_cutpoint_review",
            "privacy": {
                "classification": "private_biometric_motion_data",
                "raw_pixels_included": False,
                "source_video_embedded": False,
                "face_landmarks_included": True,
                "public_release_allowed": False,
            },
            "label": {
                "standard_word": segment["word"],
                "word_index": int(segment["word_index"]),
                "repeat_index": int(segment["repeat_index"]),
            },
            "hierarchy": {"user_id": user_id, "view": view},
            "cutpoint": {
                "start_sec": start,
                "end_sec": end,
                "cutpoint_source": segment.get("boundary_source", ""),
                "refinement": segment.get("boundary_refinement", ""),
                "review_status": "pending_manual_cutpoint_review",
            },
            "source": {
                "source_video_id": source_id,
                "reported_fps": fps,
                "reported_duration_sec": duration,
            },
            "sampling": {
                "requested_sample_fps": sample_fps,
                "source_frame_step": step,
                "effective_sample_fps": fps / step,
                "max_processing_width": max_width,
                "holistic_static_image_mode": True,
            },
            "landmark_schema": {
                **rawdb.LANDMARK_GROUPS,
                "coordinate_format": "legacy_result_data_objects",
                "record_path": "records[].result_data.*_landmarks[]",
                "sparse_face_note": "face_landmarks contains only landmark_schema.face.source_ids, not a dense 468/478 array",
            },
            "summary": summary,
            "records": frames,
        }
        write_json(shard, payload)
        summaries.append(summary)
    return summaries


def process_partition(worker_id: int, items: list[dict], args) -> list[dict]:
    process, ready = launch_worker(args.python, args.worker_script)
    results = []
    try:
        for item in items:
            paths = [shard_path_v2(args.output_root, segment, item["user_id"], item["view"]) for segment in item["segments"]]
            if args.resume and all(path.exists() and path.stat().st_size > 0 for path in paths):
                summaries = [
                    json.loads(path.read_text(encoding="utf-8"))["summary"]
                    for path in paths
                ]
                results.append({"status": "ok", "execution": "resumed_existing", "item": item, "summaries": summaries})
                continue
            indices, fps, total_frames, duration, step = frame_indices_for_item(item, args.sample_fps)
            request = {
                "cmd": "process",
                "request_id": f"u{item['user_id']:02d}_{item['view']}",
                "video_path": str(item["video"]),
                "frame_indices": indices,
                "max_width": args.max_width,
                "include_records": True,
            }
            started = time.perf_counter()
            send_json_line(process.stdin, request)
            response = read_json_line(process.stdout)
            if response.get("type") == "error":
                raise RuntimeError(response.get("error"))
            summaries = write_item_shards(item, response, args.output_root, args.sample_fps, args.max_width)
            results.append({
                "status": "ok",
                "execution": "computed_worker_pool",
                "worker_id": worker_id,
                "worker_pid": ready["pid"],
                "worker_init_sec": ready["holistic_init_sec"],
                "item": item,
                "summaries": summaries,
                "processing_sec": round(time.perf_counter() - started, 3),
                "source_video_id": rawdb.source_video_id(item["video"]),
                "source_video_path": str(item["video"]),
                "source_video_sha256": rawdb.sha256_file(item["video"]),
                "reported_fps": fps,
                "reported_duration_sec": duration,
            })
    finally:
        if process.poll() is None:
            try:
                send_json_line(process.stdin, {"cmd": "shutdown"})
                read_json_line(process.stdout)
                process.wait(timeout=10)
            except Exception:
                process.kill()
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cutpoint-root", type=Path, required=True)
    parser.add_argument("--vocabulary-csv", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--worker-script", type=Path, required=True)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--sample-fps", type=float, default=12.0)
    parser.add_argument("--max-width", type=int, default=640)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--only-ids", default="")
    parser.add_argument("--only-views", default="")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    only_ids = {int(value) for value in args.only_ids.split(",") if value.strip()}
    only_views = {value.strip() for value in args.only_views.split(",") if value.strip()}
    vocabulary = rawdb.read_csv(args.vocabulary_csv)
    items = rawdb.load_work_items(args.cutpoint_root, only_ids, only_views)
    args.output_root.mkdir(parents=True, exist_ok=True)
    partitions = [[] for _ in range(min(args.workers, max(1, len(items))))]
    for index, item in enumerate(items):
        partitions[index % len(partitions)].append(item)

    results, failures = [], []
    with ThreadPoolExecutor(max_workers=len(partitions)) as executor:
        future_map = {
            executor.submit(process_partition, worker_id, partition, args): worker_id
            for worker_id, partition in enumerate(partitions, start=1)
        }
        for future in as_completed(future_map):
            worker_id = future_map[future]
            try:
                partition_results = future.result()
                results.extend(partition_results)
                print(f"worker={worker_id} completed videos={len(partition_results)}", flush=True)
            except Exception as exc:
                failures.append({"worker_id": worker_id, "error": f"{type(exc).__name__}: {exc}"})
                print(f"worker={worker_id} failed error={exc}", flush=True)

    database, samples, sources = rawdb.build_index(
        results, vocabulary, args.output_root, args.cutpoint_root, args.sample_fps
    )
    database["build_backend"] = "persistent_holistic_worker_pool"
    database["worker_count"] = len(partitions)
    database["build_scope"] = {
        "only_ids": sorted(only_ids),
        "only_views": sorted(only_views),
        "video_count": len(items),
    }
    database["failed_worker_count"] = len(failures)
    database["failed_workers"] = failures
    (args.output_root / "database_index.json").write_text(json.dumps(database, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.output_root / "word_database.json").write_text(json.dumps(database["words"], ensure_ascii=False, indent=2), encoding="utf-8")
    if samples:
        rawdb.write_sample_manifest(args.output_root / "sample_manifest.csv", samples)
    (args.output_root / "private_provenance_manifest.json").write_text(
        json.dumps({"privacy": "private_biometric_motion_data", "sources": sorted(sources, key=lambda row: (row["user_id"], rawdb.VIEW_ORDER[row["view"]]))}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({
        "video_count": len(items),
        "sample_count": len(samples),
        "missing_sample_count": len(database["missing_samples"]),
        "failed_worker_count": len(failures),
        "output_root": str(args.output_root),
    }, ensure_ascii=False), flush=True)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

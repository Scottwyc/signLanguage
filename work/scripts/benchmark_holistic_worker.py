#!/usr/bin/env python3
"""
Holistic 常驻 worker 实验。

流程：
1. 启动常驻 worker。
2. 等待一次初始化完成。
3. 依次发送多个视频请求。
4. 统计每个请求耗时和整体墙钟耗时。
5. 输出 Markdown / JSON 报告，便于汇报和归档。
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from keyframe_sampling_common import (
    DEFAULT_VIDEO_ROOT,
    configure_headless,
    encode_frame_payload,
    import_optional_backends,
    normalize_total_frames,
    probe_video_metadata,
    select_energy_coverage_keyframes,
    summarize_rows,
)
from signlanguage_common import find_demo_videos


DEFAULT_OUTPUT_DIR = Path("/data/WYC/signLanguage/work/generated/holistic_worker_benchmark")
DEFAULT_FRAME_OUTPUT_DIR = Path("/data/WYC/signLanguage/work/generated/holistic_worker_frame_slice_benchmark")
DEFAULT_WORKER_SCRIPT = Path("/data/WYC/signLanguage/work/scripts/holistic_worker_daemon.py")


def _default_videos(video_root: Path) -> List[Path]:
    videos = find_demo_videos(video_root)
    wanted = ["花.mp4", "唱歌.mp4", "跳.mp4"]
    picked: List[Path] = []
    for name in wanted:
        for video in videos:
            if video.name == name:
                picked.append(video)
                break
    if picked:
        return picked
    return videos[:3]


def _read_json_line(stream) -> Dict[str, Any]:
    line = stream.readline()
    if not line:
        raise RuntimeError("worker 进程已提前退出")
    return json.loads(line)


def _send_json_line(stream, payload: Dict[str, Any]) -> None:
    stream.write(json.dumps(payload, ensure_ascii=False) + "\n")
    stream.flush()


def _run_worker(worker_script: Path, model_complexity: int) -> subprocess.Popen:
    cmd = [sys.executable, str(worker_script), "--model-complexity", str(model_complexity)]
    return subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        bufsize=1,
    )


def _load_frame_slices(video_path: Path, frame_indices: Sequence[int]) -> Dict[str, Any]:
    """在客户端侧读取并编码帧切片。"""

    cv2, _ = import_optional_backends()
    if cv2 is None:
        raise RuntimeError("需要安装 opencv-python 才能编码帧切片")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"无法打开视频：{video_path}")
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if total_frames <= 0:
        meta = probe_video_metadata(video_path)
        total_frames = normalize_total_frames(meta)

    started = time.perf_counter()
    frames: List[Dict[str, Any]] = []
    targets = {int(idx) for idx in frame_indices}
    max_target = max(targets) if targets else -1
    frame_idx = 0
    while frame_idx <= max_target:
        ok, frame = cap.read()
        if not ok:
            break
        if frame_idx in targets:
            payload = encode_frame_payload(cv2, frame, image_format="jpg", jpeg_quality=92)
            payload["frame_idx"] = int(frame_idx)
            frames.append(payload)
        frame_idx += 1

    cap.release()
    if len(frames) != len(targets):
        missing = sorted(targets - {int(item["frame_idx"]) for item in frames})
        raise RuntimeError(f"无法读取帧：{video_path}，缺失帧 {missing[:5]}")
    return {
        "fps": fps,
        "total_frames": total_frames,
        "frames": frames,
        "client_prepare_sec": round(time.perf_counter() - started, 3),
    }


def _dense_indices_from_video(video_path: Path, dense_step: int) -> List[int]:
    cv2, _ = import_optional_backends()
    if cv2 is None:
        meta = probe_video_metadata(video_path)
        total_frames = normalize_total_frames(meta)
    else:
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise RuntimeError(f"无法打开视频：{video_path}")
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        cap.release()
        if total_frames <= 0:
            meta = probe_video_metadata(video_path)
            total_frames = normalize_total_frames(meta)

    selected_indices = list(range(0, max(1, total_frames), max(1, dense_step)))
    if total_frames > 1 and selected_indices[-1] != total_frames - 1:
        selected_indices.append(total_frames - 1)
    return sorted(dict.fromkeys(selected_indices))


def run_experiment(
    video_paths: Sequence[Path],
    frame_indices: Sequence[int],
    model_complexity: int,
    worker_script: Path,
    output_dir: Path,
    input_mode: str,
    dense_step: int,
    sample_budget: int,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    worker = _run_worker(worker_script, model_complexity)
    if worker.stdin is None or worker.stdout is None:
        worker.kill()
        raise RuntimeError("worker 管道初始化失败")

    started = time.perf_counter()
    ready = _read_json_line(worker.stdout)
    if ready.get("type") != "ready":
        worker.kill()
        raise RuntimeError(f"worker 启动异常：{ready}")
    startup_ready_sec = round(time.perf_counter() - started, 3)

    requests: List[Dict[str, Any]] = []
    for idx, video_path in enumerate(video_paths):
        request_id = f"{video_path.stem}_{idx}"
        result_dir = output_dir / "results" / video_path.stem
        selected_indices = list(dict.fromkeys(int(i) for i in frame_indices))
        client_prepare_sec = None
        dense_meta = None
        if input_mode == "frame_slices":
            selected_indices = _dense_indices_from_video(video_path, dense_step)
            dense_meta = _load_frame_slices(video_path, selected_indices)
            req = {
                "cmd": "process_frames",
                "request_id": request_id,
                "video_stem": video_path.stem,
                "video_path": str(video_path),
                "fps": dense_meta["fps"],
                "total_frames": dense_meta["total_frames"],
                "frame_indices": selected_indices,
                "frames": dense_meta["frames"],
                "result_dir": str(result_dir),
            }
            client_prepare_sec = dense_meta["client_prepare_sec"]
        else:
            req = {
                "cmd": "process",
                "request_id": request_id,
                "video_path": str(video_path),
                "frame_indices": selected_indices,
                "result_dir": str(result_dir),
            }
        req_start = time.perf_counter()
        _send_json_line(worker.stdin, req)
        resp = _read_json_line(worker.stdout)
        req_wall_sec = round(time.perf_counter() - req_start, 3)
        if resp.get("type") == "error":
            worker.kill()
            raise RuntimeError(f"请求失败：{resp}")

        selected_summary = None
        selected_indices_out: List[int] = []
        dense_rows = resp.get("rows", [])
        if input_mode == "frame_slices":
            selected_indices_out = select_energy_coverage_keyframes(dense_rows, sample_budget)
            dense_rows_map = {int(row["frame_idx"]): row for row in dense_rows}
            selected_rows = [dense_rows_map[idx] for idx in selected_indices_out if idx in dense_rows_map]
            selected_summary = summarize_rows(
                {
                    "fps": resp.get("meta", {}).get("fps"),
                    "duration_sec": None,
                },
                int(resp.get("meta", {}).get("total_frames") or 0),
                selected_rows,
            )

        requests.append(
            {
                "request_id": request_id,
                "video": video_path.name,
                "video_path": str(video_path),
                "frame_indices": selected_indices,
                "client_prepare_sec": client_prepare_sec,
                "worker_response": resp,
                "client_wall_sec": req_wall_sec,
                "selected_indices": selected_indices_out,
                "selected_summary": selected_summary,
                "dense_frame_count": len(dense_rows) if isinstance(dense_rows, list) else None,
                "dense_step": dense_step if input_mode == "frame_slices" else None,
            }
        )

    _send_json_line(worker.stdin, {"cmd": "shutdown"})
    shutdown_resp = _read_json_line(worker.stdout)
    worker.wait(timeout=30)

    total_sec = round(time.perf_counter() - started, 3)
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "worker_ready": ready,
        "startup_ready_sec": startup_ready_sec,
        "requests": requests,
        "shutdown": shutdown_resp,
        "total_sec": total_sec,
        "video_count": len(video_paths),
        "frame_indices": list(dict.fromkeys(int(i) for i in frame_indices)),
        "model_complexity": model_complexity,
        "input_mode": input_mode,
        "dense_step": dense_step if input_mode == "frame_slices" else None,
        "sample_budget": sample_budget if input_mode == "frame_slices" else None,
        "worker_script": str(worker_script),
        "output_dir": str(output_dir),
    }


def build_report(payload: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# Holistic 常驻 worker 实验")
    lines.append("")
    lines.append("本次实验验证：worker 只初始化一次 Holistic，之后连续接收多个视频请求，能否稳定常驻并返回结果。")
    lines.append("")
    lines.append("## 启动信息")
    lines.append("")
    lines.append(f"- worker PID：{payload['worker_ready'].get('pid')}")
    lines.append(f"- 模型复杂度：{payload['model_complexity']}")
    lines.append(f"- 输入模式：{payload.get('input_mode')}")
    lines.append(f"- static_image_mode：{payload['worker_ready'].get('static_image_mode')}")
    lines.append(f"- worker 初始化耗时：{payload['worker_ready'].get('holistic_init_sec')}s")
    lines.append(f"- 客户端等待 worker ready 耗时：{payload['startup_ready_sec']}s")
    if payload.get("input_mode") == "frame_slices":
        lines.append(f"- 密采样步长：每 {payload.get('dense_step')} 帧取 1 帧")
        lines.append(f"- 目标筛选帧数：{payload.get('sample_budget')}")
    lines.append("")
    lines.append("## 顺序请求结果")
    lines.append("")
    for idx, req in enumerate(payload["requests"], start=1):
        resp = req["worker_response"]
        lines.append(f"### 请求 {idx}")
        lines.append(f"- 视频：`{req['video']}`")
        lines.append(f"- 帧索引：{', '.join(str(x) for x in req['frame_indices'])}")
        if req.get("client_prepare_sec") is not None:
            lines.append(f"- 客户端帧切片准备耗时：{req.get('client_prepare_sec')}s")
        lines.append(f"- worker 返回样本数：{resp.get('samples')}")
        lines.append(f"- worker 输入模式：{resp.get('input_mode')}")
        lines.append(f"- worker 内部总耗时：{resp.get('request_total_sec')}s")
        lines.append(f"- worker 输入耗时：{resp.get('ingest_sec')}s")
        lines.append(f"- 识别耗时：{resp.get('holistic_eval_sec')}s")
        lines.append(f"- 客户端墙钟耗时：{req.get('client_wall_sec')}s")
        lines.append(f"- 结果文件：{resp.get('result_file')}")
        if req.get("selected_indices"):
            lines.append(f"- 最终筛选帧：{', '.join(str(x) for x in req['selected_indices'])}")
            lines.append(f"- 最终筛选帧数：{len(req['selected_indices'])}")
            if req.get("selected_summary"):
                s = req["selected_summary"]
                lines.append(f"- 最终帧覆盖比例：{s.get('frame_span_ratio')}")
                lines.append(f"- 最终尾部覆盖比例：{s.get('tail_coverage_ratio')}")
                lines.append(f"- 最终后半段采样占比：{s.get('late_half_fraction')}")
                lines.append(f"- 最终后 75% 采样占比：{s.get('late_75_fraction')}")
        lines.append("")
    lines.append("## 结论")
    lines.append("")
    lines.append("- worker 只在启动时初始化一次 Holistic，后续多个视频请求可以连续处理。")
    lines.append("- 这条路径避免了每个视频请求都重新支付初始化成本。")
    lines.append("- 对当前场景，worker 适合做成常驻服务，再由前端按需下发帧块或视频请求。")
    if payload.get("input_mode") == "frame_slices":
        lines.append("- 帧切片模式下，后端不再加载视频文件，只做帧切片解码和 Holistic 识别。")
    lines.append("")
    lines.append(f"- 全流程总耗时：{payload['total_sec']}s")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    configure_headless()
    parser = argparse.ArgumentParser(description="Holistic 常驻 worker 实验")
    parser.add_argument("--video-root", default=str(DEFAULT_VIDEO_ROOT), help="视频目录")
    parser.add_argument("--video", action="append", help="要顺序请求的视频，可重复传入")
    parser.add_argument("--frame-idx", action="append", type=int, default=None, help="每个视频请求的帧索引，可重复传入")
    parser.add_argument("--input-mode", choices=["video", "frame_slices"], default="video", help="请求输入模式")
    parser.add_argument("--dense-step", type=int, default=4, help="帧切片模式下的密采样步长")
    parser.add_argument("--sample-budget", type=int, default=12, help="帧切片模式下最终筛选帧数")
    parser.add_argument("--model-complexity", type=int, default=1, help="Holistic 模型复杂度")
    parser.add_argument("--worker-script", default=str(DEFAULT_WORKER_SCRIPT), help="worker 脚本路径")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="输出目录")
    args = parser.parse_args(argv)

    video_root = Path(args.video_root)
    if args.video:
        videos = [Path(v) for v in args.video]
    else:
        videos = _default_videos(video_root)
    if not videos:
        raise RuntimeError("未找到可用视频")

    frame_indices = list(dict.fromkeys(args.frame_idx or [0, 4]))

    output_dir = Path(args.output_dir)
    if args.input_mode == "frame_slices" and output_dir == DEFAULT_OUTPUT_DIR:
        output_dir = DEFAULT_FRAME_OUTPUT_DIR
    worker_script = Path(args.worker_script)

    if args.input_mode == "frame_slices":
        # 密采样模式下默认使用整段视频的候选帧，不再只请求少数几帧。
        frame_indices = _dense_indices_from_video(videos[0], args.dense_step)

    payload = run_experiment(
        videos,
        frame_indices,
        args.model_complexity,
        worker_script,
        output_dir,
        args.input_mode,
        args.dense_step,
        args.sample_budget,
    )
    json_path = output_dir / "holistic_worker_benchmark.json"
    md_path = output_dir / "holistic_worker_benchmark.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(build_report(payload), encoding="utf-8")
    print(f"已生成 worker 基准 JSON：{json_path}")
    print(f"已生成 worker 基准报告：{md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

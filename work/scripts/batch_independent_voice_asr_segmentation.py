#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Independently segment and ASR-check every sign-language video.

Unlike the earlier volunteer-level pilot, this script never copies prompt
times or ASR labels from the front view to side views. Every source video gets:

    local audio prompt detection -> local Whisper -> A-Z constrained matching

The large Whisper model is loaded once per worker process. Raw videos remain
read-only; only manifests, CSV/TXT records and preview images are written.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import csv
import json
import multiprocessing as mp
import os
import re
import time
from pathlib import Path

import cv2

SCRIPT_DIR = Path(__file__).resolve().parent
import sys
sys.path.insert(0, str(SCRIPT_DIR))
import auto_cut_voice_prompt_segments as core

MODEL = None
MODEL_NAME = "large-v3-turbo"


def parse_volunteer(folder: str):
    m = re.match(r"^(\d+)(.*)$", folder)
    return (m.group(1), m.group(2) or folder) if m else (folder, folder)


def infer_view(path: Path) -> str:
    stem = path.stem
    if "正" in stem:
        return "正"
    if "左" in stem:
        return "左30"
    if "右" in stem:
        return "右30"
    return "unknown"


def worker_init(model_name: str):
    global MODEL, MODEL_NAME
    MODEL_NAME = model_name
    import whisper
    MODEL = whisper.load_model(model_name)


def build_rows(source_path, view, starts, labels, duration, status):
    rows = []
    ends = starts[1:] + [duration]
    for i, (start, end) in enumerate(zip(starts, ends)):
        label = labels[i] if i < len(labels) else {}
        expected = core.PINYIN_ORDER[i // 2]
        raw = label.get("pre_constraint_word")
        consistency = "一致" if raw == expected else "未识别" if not raw else "不一致"
        rows.append({
            "view": view,
            "source_path": str(source_path),
            "word_index": i // 2 + 1,
            "word": expected,
            "word_by_ordinal_fallback": expected,
            "expected_standard_word": expected,
            "asr_raw_matched_word": raw or "",
            "asr_consistency": consistency,
            "transcript_text": label.get("transcript_text", ""),
            "word_match_score": label.get("match_score", 0.0),
            "word_match_method": label.get("match_method", ""),
            "repeat_index": i % 2 + 1,
            "start_sec": round(float(start), 4),
            "end_sec": round(float(end), 4),
            "duration_sec": round(float(end - start), 4),
            "segment_rule": "independent_word_prompt_start_to_next_word_prompt_start",
            "countdown_rule": "drop_initial_recording_countdown_and_keep_first_word_burst",
            "view_alignment_status": "independent_no_cross_view_mapping",
            "inferred_boundary_count_for_view": 0,
            "processing_status": status,
            "manual_status": "candidate",
        })
    return rows


def write_rows(path: Path, rows):
    if not rows:
        return
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def process_one(source_path_str: str, output_root_str: str):
    source_path = Path(source_path_str)
    output_root = Path(output_root_str)
    volunteer_id, volunteer_name = parse_volunteer(source_path.parent.name)
    view = infer_view(source_path)
    out = output_root / source_path.parent.name / view
    out.mkdir(parents=True, exist_ok=True)
    duration = core.video_duration(source_path)
    record = {
        "source_path": str(source_path),
        "volunteer_id": volunteer_id,
        "volunteer_name": volunteer_name,
        "view": view,
        "model": MODEL_NAME,
        "independent_processing": True,
        "duration_sec": duration,
        "status": "ok",
    }
    try:
        detected = core.detect_prompts(source_path, drop_leading_countdown=True)
        starts = detected["prompt_starts"]
        transcription = core.transcribe_prompt_words(
            source_path,
            starts,
            MODEL_NAME,
            leading_word_override="谗（羡慕）",
            enforce_pinyin_order=True,
            model=MODEL,
        )
        labels = transcription["labels"]
        rows = build_rows(source_path, view, starts, labels, duration, "ok")
        fake_results = {
            "正": {
                "prompt_labels": labels,
                "aligned_prompt_starts": starts,
                "prompt_starts": starts,
            }
        }
        core.write_preview(source_path, starts, out / "preview.jpg", labels)
        core.write_word_list(out / "recognized_standard_vocabulary_list.txt", fake_results, MODEL_NAME)
        consistency_rows = core.write_consistency_csv(out / "asr_consistency.csv", fake_results)
        write_rows(out / "segments.csv", rows)
        record.update({
            "status": "ok" if len(starts) == core.EXPECTED_PROMPTS else "wrong_prompt_count",
            "prompt_count": len(starts),
            "segment_count": len(rows),
            "consistency": dict(__import__("collections").Counter(x["consistency"] for x in consistency_rows)),
            "detected": detected,
            "transcription": transcription,
        })
    except Exception as exc:
        record.update({
            "status": "failed",
            "error": f"{type(exc).__name__}: {exc}",
            "prompt_count": 0,
            "segment_count": 0,
        })
    (out / "manifest.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return record


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-root", type=Path, required=True)
    ap.add_argument("--output-root", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--model", default="large-v3-turbo")
    args = ap.parse_args()
    direct = sorted(args.input_root.glob("*.mov"))
    nested = sorted(args.input_root.glob("*/*.mov"))
    paths = direct or nested
    args.output_root.mkdir(parents=True, exist_ok=True)
    ctx = mp.get_context("spawn")
    results = []
    with concurrent.futures.ProcessPoolExecutor(
        max_workers=args.workers,
        mp_context=ctx,
        initializer=worker_init,
        initargs=(args.model,),
    ) as executor:
        futures = [executor.submit(process_one, str(p), str(args.output_root)) for p in paths]
        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            result = future.result()
            results.append(result)
            print(
                f"[{i}/{len(paths)}] {result['volunteer_name']} {result['view']} "
                f"{result['status']} segments={result.get('segment_count', 0)}",
                flush=True,
            )
    results.sort(key=lambda x: (int(x["volunteer_id"]) if x["volunteer_id"].isdigit() else 999, x["view"]))
    summary = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S %z"),
        "model": args.model,
        "workers": args.workers,
        "independent_per_video": True,
        "input_root": str(args.input_root),
        "video_count": len(paths),
        "success_count": sum(r["status"] == "ok" for r in results),
        "failed_count": sum(r["status"] == "failed" for r in results),
        "total_segments": sum(r.get("segment_count", 0) for r in results),
        "results": results,
    }
    (args.output_root / "batch_manifest.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    with (args.output_root / "batch_summary.csv").open("w", encoding="utf-8-sig", newline="") as f:
        fields = ["volunteer_id", "volunteer_name", "view", "status", "prompt_count", "segment_count", "error"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in results:
            writer.writerow({k: r.get(k, "") for k in fields})
    print(json.dumps({
        "videos": len(paths),
        "success": summary["success_count"],
        "failed": summary["failed_count"],
        "segments": summary["total_segments"],
        "output": str(args.output_root),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pilot automatic segmentation for one volunteer's three synchronized views.

Recording protocol used by this pilot:

    word announcement -> countdown ("3 2 1 开始") -> one sign demonstration

The segment start is the first audio activity in each prompt cluster. Later
audio bursts inside the same cluster are deliberately excluded as countdown
speech. The end is the next word-announcement start; the final segment ends at
the source video duration. Source videos are read-only. This pilot writes only
JSON/CSV/preview images, not encoded clips.
"""
from __future__ import annotations

import argparse
import csv
import collections
import json
import math
import re
import statistics
import subprocess
from pathlib import Path

import av
import cv2
import numpy as np
from scipy.optimize import linear_sum_assignment

VOCABULARY = [
    "香蕉", "花", "汽车", "虎", "月亮", "跳", "朋友", "指示", "唱歌", "谗（羡慕）",
    "公交车", "船（轮船）", "牛奶", "鸡蛋", "烤串", "森林", "超市", "勇敢", "科学", "人们（人民）",
]

# The recording protocol for this batch follows the first pinyin letter A→Z.
# This is the authoritative block order for constrained decoding.
PINYIN_ORDER = [
    "谗（羡慕）", "唱歌", "超市", "船（轮船）", "公交车",
    "虎", "花", "鸡蛋", "烤串", "科学", "牛奶", "朋友",
    "汽车（一）", "汽车二", "人们（人民）", "森林", "跳", "香蕉",
    "勇敢", "月亮", "指示",
]
EXPECTED_PROMPTS = len(PINYIN_ORDER) * 2

VOCAB_ALIASES = {
    "香蕉": ["香蕉", "香交"],
    "汽车（一）": ["汽车（一）", "汽车一", "汽车1", "汽車一", "汽车"],
    "汽车二": ["汽车二", "汽车2", "汽車二", "汽车"],
    "月亮": ["月亮", "越量"],
    "指示": ["指示", "指导", "直到"],
    "唱歌": ["唱歌"],
    "公交车": ["公交车", "公交", "公車"],
    "鸡蛋": ["鸡蛋", "雞蛋"],
    "烤串": ["烤串", "烤判"],
    "科学": ["科学", "科學"],
    "谗（羡慕）": ["谗", "馋", "羡慕", "馋嘴"],
    "人们（人民）": ["人们", "人民", "人"],
    "船（轮船）": ["船", "轮船"],
}


def view_name(path: Path) -> str:
    stem = path.stem
    if "正" in stem:
        return "正"
    if "左" in stem:
        return "左30"
    return "右30"


def audio_energy(path: Path, frame_sec: float = 0.02, hop_sec: float = 0.01):
    try:
        with av.open(str(path)) as container:
            stream = next(s for s in container.streams if s.type == "audio")
            audio = _decode_audio_packets(container, stream)
            sample_rate = int(stream.sample_rate or 48000)
    except Exception:
        # Some camera MOV files contain damaged packets that PyAV rejects but
        # ffmpeg can recover. Keep the raw video read-only and decode only a
        # temporary in-memory 16 kHz mono stream.
        audio = _decode_audio_ffmpeg(path, sample_rate=16000)
        sample_rate = 16000
    win = max(1, int(sample_rate * frame_sec))
    hop = max(1, int(sample_rate * hop_sec))
    energies = np.asarray(
        [np.sqrt(np.mean(audio[i:i + win] ** 2)) for i in range(0, len(audio) - win, hop)],
        dtype=np.float32,
    )
    times = np.arange(len(energies), dtype=np.float32) * hop_sec
    return times, energies


def contiguous_intervals(times, energy, threshold, min_duration=0.08):
    mask = energy >= threshold
    # Bridge short within-word gaps but do not bridge the long gap after a
    # prompt/countdown cluster.
    bridge = max(1, int(round(0.08 / (times[1] - times[0]))))
    mask = mask | (np.convolve(mask.astype(np.int32), np.ones(bridge), mode="same") >= bridge * 0.5)
    intervals = []
    start = None
    for i, active in enumerate(mask):
        if active and start is None:
            start = i
        if start is not None and (not active or i == len(mask) - 1):
            end = i if not active else i + 1
            if (end - start) * (times[1] - times[0]) >= min_duration:
                intervals.append((float(times[start]), float(times[end - 1] + 0.02)))
            start = None
    return intervals


def prompt_clusters(intervals, merge_gap_sec=1.20):
    clusters = []
    for interval in intervals:
        if not clusters or interval[0] - clusters[-1][-1][1] > merge_gap_sec:
            clusters.append([interval])
        else:
            clusters[-1].append(interval)
    return clusters


def detect_prompts(path: Path, expected=EXPECTED_PROMPTS, drop_leading_countdown=True):
    times, energy = audio_energy(path)
    q50, q95 = float(np.quantile(energy, 0.50)), float(np.quantile(energy, 0.95))
    # The audio gain differs across cameras. This adaptive threshold preserves
    # the spoken prompts while ignoring the low-level room floor.
    # Keep the threshold permissive enough for the quieter left camera. The
    # fixed-format prompt clustering below removes the countdown bursts.
    threshold = max(q50 * 1.50, q95 * 0.50)
    intervals = contiguous_intervals(times, energy, threshold)
    clusters = prompt_clusters(intervals)
    starts = [c[0][0] for c in clusters]
    raw_cluster_count = len(starts)
    excluded = [item for c in clusters for item in c[1:]]
    leading_countdown_excluded = None
    if drop_leading_countdown and len(starts) >= expected + 1:
        # The first cluster contains the recording-start “3 2 1 开始” and,
        # in this dataset, the first vocabulary announcement immediately after
        # it. Keep the final audio burst in that cluster as vocabulary prompt
        # 01; discard only the earlier countdown bursts.
        leading_countdown_excluded = clusters[0]
        first_word_start = clusters[0][-1][0] if len(clusters[0]) > 1 else None
        starts = ([first_word_start] if first_word_start is not None else []) + starts[1:]
    # Any terminal announcement/noise after the 40 word prompts is ignored.
    trimmed = starts[:expected]
    return {
        "threshold": threshold,
        "q50": q50,
        "q95": q95,
        "active_intervals": intervals,
        "clusters": clusters,
        "prompt_starts": trimmed,
        "excluded_countdown_intervals": excluded,
        "leading_countdown_excluded": leading_countdown_excluded,
        "raw_cluster_count": raw_cluster_count,
        "post_leading_exclusion_cluster_count": len(starts),
        "expected_count": expected,
        "count_match": len(trimmed) == expected,
    }


def video_duration(path: Path) -> float:
    cap = cv2.VideoCapture(str(path))
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    cap.release()
    return n / fps if fps else 0.0


def load_audio_16k(path: Path) -> np.ndarray:
    """Decode a private MOV audio track to Whisper's expected 16 kHz mono array."""
    from scipy.signal import resample_poly

    try:
        with av.open(str(path)) as container:
            stream = next(s for s in container.streams if s.type == "audio")
            audio = _decode_audio_packets(container, stream)
            source_rate = int(stream.sample_rate or 48000)
    except Exception:
        return np.clip(_decode_audio_ffmpeg(path, sample_rate=16000), -1.0, 1.0)
    if source_rate != 16000:
        audio = resample_poly(audio, 16000, source_rate).astype(np.float32)
    return np.clip(audio, -1.0, 1.0)


def _decode_audio_packets(container, stream) -> np.ndarray:
    """Decode recoverable audio packets while skipping isolated corrupt ones."""
    chunks = []
    for packet in container.demux(stream):
        try:
            frames = packet.decode()
        except Exception:
            continue
        for frame in frames:
            arr = frame.to_ndarray()
            if arr.ndim == 2:
                arr = arr.mean(axis=0)
            chunks.append(arr.astype(np.float32, copy=False))
    if not chunks:
        raise RuntimeError("PyAV decoded no recoverable audio frames")
    return np.concatenate(chunks)


def _decode_audio_ffmpeg(path: Path, sample_rate: int = 16000) -> np.ndarray:
    completed = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-err_detect",
            "ignore_err",
            "-i",
            str(path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            str(sample_rate),
            "-f",
            "f32le",
            "pipe:1",
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    audio = np.frombuffer(completed.stdout, dtype="<f4").astype(np.float32, copy=True)
    if not len(audio):
        raise RuntimeError(f"ffmpeg decoded no audio samples: {path}")
    return audio


def normalize_text(text: str) -> str:
    return re.sub(r"[\s，。！？、：；,.!?;:\"'（）()【】\[\]·\-]", "", text or "")


def levenshtein(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(cur[-1] + 1, prev[j] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def match_standard_word(text: str):
    clean = normalize_text(text)
    candidates = []
    for standard in VOCABULARY:
        aliases = VOCAB_ALIASES.get(standard, [standard])
        for alias in aliases:
            alias_clean = normalize_text(alias)
            pos = clean.find(alias_clean)
            if pos >= 0:
                candidates.append((pos, -len(alias_clean), 1.0, standard, alias))
    if candidates:
        candidates.sort()
        _, _, score, standard, alias = candidates[0]
        return standard, score, alias, "substring"
    # Whisper may return a minor homophone/character error. Use a conservative
    # normalized edit-distance fallback over the short prompt text.
    best = None
    for standard in VOCABULARY:
        for alias in VOCAB_ALIASES.get(standard, [standard]):
            alias_clean = normalize_text(alias)
            distance = levenshtein(clean, alias_clean)
            score = 1.0 - distance / max(len(clean), len(alias_clean), 1)
            item = (score, standard, alias)
            if best is None or item[0] > best[0]:
                best = item
    if best and best[0] >= 0.45:
        return best[1], round(float(best[0]), 4), best[2], "edit_distance"
    return None, 0.0, None, "unmatched"


def alias_window_similarity(text: str, alias: str) -> float:
    """Best normalized similarity between an alias and a short ASR text."""
    text = normalize_text(text)
    alias = normalize_text(alias)
    if not text or not alias:
        return 0.0
    if alias in text:
        return 1.0
    lengths = range(max(1, len(alias) - 1), min(len(text), len(alias) + 2) + 1)
    best = 0.0
    for n in lengths:
        for i in range(0, len(text) - n + 1):
            part = text[i:i + n]
            distance = levenshtein(part, alias)
            best = max(best, 1.0 - distance / max(len(part), len(alias), 1))
    return best


def constrained_pair_assignment(
    prompt_labels,
    forced_block_words=None,
    enforce_pinyin_order=True,
):
    """Assign each pinyin-order block exactly twice using ASR evidence."""
    if len(prompt_labels) != EXPECTED_PROMPTS:
        return prompt_labels, {"status": "disabled_wrong_prompt_count"}
    block_count = len(PINYIN_ORDER)
    pair_texts = [
        " ".join(
            str(prompt_labels[i + j].get("transcript_text", ""))
            for j in (0, 1)
        )
        for i in range(0, EXPECTED_PROMPTS, 2)
    ]
    score = np.zeros((block_count, block_count), dtype=np.float64)
    evidence = [[None for _ in range(block_count)] for _ in range(block_count)]
    for block_i, text in enumerate(pair_texts):
        for word_i, standard in enumerate(PINYIN_ORDER):
            aliases = VOCAB_ALIASES.get(standard, [standard])
            sims = [alias_window_similarity(text, alias) for alias in aliases]
            best = max(sims) if sims else 0.0
            exact_count = sum(
                normalize_text(alias) in normalize_text(text) for alias in aliases
            )
            raw_known = sum(
                1
                for j in (0, 1)
                if prompt_labels[block_i * 2 + j].get("recognized_standard_word") == standard
            )
            value = best * 20.0 + exact_count * 45.0 + raw_known * 25.0
            score[block_i, word_i] = value
            evidence[block_i][word_i] = {
                "similarity": round(float(best), 4),
                "exact_alias_count": exact_count,
                "raw_known_count": raw_known,
            }
    forced_block_words = forced_block_words or {}
    assignment = {}
    if enforce_pinyin_order:
        for block_i in range(block_count):
            assignment[block_i] = block_i
    else:
        forced = {
            int(block): PINYIN_ORDER.index(word)
            for block, word in forced_block_words.items()
            if word in PINYIN_ORDER
        }
        assignment.update(forced)
        free_blocks = [i for i in range(block_count) if i not in assignment]
        free_words = [i for i in range(block_count) if i not in assignment.values()]
        if free_blocks:
            rows, cols = linear_sum_assignment(-score[np.ix_(free_blocks, free_words)])
            for row, col in zip(rows, cols):
                assignment[free_blocks[int(row)]] = free_words[int(col)]
    updated = [dict(item) for item in prompt_labels]
    assigned_blocks = []
    for block_i, word_i in assignment.items():
        standard = PINYIN_ORDER[word_i]
        value = float(score[block_i, word_i])
        forced = forced_block_words.get(block_i) == standard
        ordered = enforce_pinyin_order
        confidence = (
            "manual" if forced
            else "high" if value >= 60
            else "medium" if value >= 25
            else "low"
        )
        assigned_blocks.append({
            "block_index": block_i + 1,
            "word": standard,
            "score": round(value, 4),
            "confidence": confidence,
            "pinyin_order_enforced": ordered,
            "evidence": evidence[block_i][word_i],
        })
        for j in (0, 1):
            idx = block_i * 2 + j
            updated[idx]["pre_constraint_word"] = updated[idx].get("recognized_standard_word")
            updated[idx]["recognized_standard_word"] = standard
            updated[idx]["match_score"] = round(value / 100.0, 4)
            updated[idx]["matched_alias"] = None
            updated[idx]["match_method"] = (
                "manual_leading_word_override" if forced
                else "constrained_pair_assignment"
            )
            updated[idx]["assignment_confidence"] = confidence
    return updated, {
        "status": "ok",
        "pair_count": block_count,
        "each_word_count": 2,
        "forced_block_words": forced_block_words,
        "pinyin_order_enforced": enforce_pinyin_order,
        "assigned_blocks": assigned_blocks,
    }


def transcribe_prompt_words(
    path,
    prompt_starts,
    model_name="tiny",
    leading_word_override=None,
    enforce_pinyin_order=True,
    model=None,
):
    import whisper

    audio = load_audio_16k(path)
    if model is None:
        model = whisper.load_model(model_name)
    result = model.transcribe(
        audio,
        language="zh",
        task="transcribe",
        fp16=False,
        temperature=0,
        word_timestamps=True,
        verbose=False,
        condition_on_previous_text=False,
        beam_size=5,
        best_of=5,
        initial_prompt=(
            "手语词汇播报：" + "、".join(PINYIN_ORDER)
            + "。馋也可能被识别为谗；指导属于指示。"
        ),
    )
    segments = result.get("segments", [])
    words = []
    for segment in segments:
        for word in segment.get("words", []):
            words.append({
                "start": float(word.get("start", 0.0)),
                "end": float(word.get("end", word.get("start", 0.0))),
                "text": str(word.get("word", "")),
            })
    labels = []
    for i, start in enumerate(prompt_starts):
        end = prompt_starts[i + 1] if i + 1 < len(prompt_starts) else float("inf")
        # The first prompt syllables can be slightly before the energy onset;
        # keep the window short so the following countdown is not confused
        # with the next word. If Whisper recognized a standard alias in the
        # narrow window, it is preferred over a broad fallback window.
        narrow = [
            w for w in words
            if w["end"] >= start - 0.65 and w["start"] <= min(end, start + 1.60)
        ]
        transcript_text = "".join(w["text"] for w in narrow).strip()
        standard, score, alias, method = match_standard_word(transcript_text)
        if standard is None:
            broad = [
                w for w in words
                if w["end"] >= start - 0.65 and w["start"] <= min(end, start + 2.50)
            ]
            broad_text = "".join(w["text"] for w in broad).strip()
            b_standard, b_score, b_alias, b_method = match_standard_word(broad_text)
            if b_standard is not None:
                transcript_text = broad_text
                standard, score, alias, method = b_standard, b_score, b_alias, "broad_" + b_method
        labels.append({
            "transcript_text": transcript_text,
            "recognized_standard_word": standard,
            "match_score": score,
            "matched_alias": alias,
            "match_method": method,
        })
    forced = {0: leading_word_override} if leading_word_override else {}
    constrained_labels, constraint_info = constrained_pair_assignment(
        labels,
        forced,
        enforce_pinyin_order=enforce_pinyin_order,
    )
    return {
        "model": model_name,
        "segments": segments,
        "word_timestamps": words,
        "raw_labels": labels,
        "labels": constrained_labels,
        "constraint_assignment": constraint_info,
        "leading_word_override": leading_word_override,
        "pinyin_order_enforced": enforce_pinyin_order,
    }


def nearest_monotonic(reference, candidates, expected_count):
    """Map reference prompt times to candidate view times monotonically."""
    if not candidates:
        return [], {"status": "no_candidates"}
    ref = np.asarray(reference, dtype=np.float64)
    cand = np.asarray(candidates, dtype=np.float64)
    # Estimate the dominant fixed camera offset from all near pairwise
    # differences. This is robust to one or two missing/false audio prompts.
    diffs = []
    for r in ref:
        local = cand[np.abs(cand - r) <= 0.60] - r
        diffs.extend(float(x) for x in local)
    if diffs:
        bins = {}
        for d in diffs:
            key = round(d / 0.05) * 0.05
            bins[key] = bins.get(key, 0) + 1
        offset = max(bins, key=bins.get)
    else:
        offset = float(cand[0] - ref[0])
    scale = 1.0
    predicted = ref + offset
    chosen = []
    used = -1
    errors = []
    inferred = 0
    for p in predicted[:expected_count]:
        eligible = np.arange(used + 1, len(cand))
        if len(eligible) == 0:
            chosen.append(float(p))
            inferred += 1
            continue
        j = int(eligible[np.argmin(np.abs(cand[eligible] - p))])
        distance = abs(float(cand[j] - p))
        if distance <= 0.60:
            chosen.append(float(cand[j]))
            errors.append(float(cand[j] - p))
            used = j
        else:
            # A missing audio burst in one camera is reconstructed from the
            # canonical front-view cue plus the estimated camera offset.
            chosen.append(float(p))
            inferred += 1
    return chosen, {
        "status": "ok" if len(chosen) == expected_count and inferred == 0 else "ok_with_inferred_boundaries",
        "scale": float(scale),
        "offset_sec": float(offset),
        "mean_abs_error_sec": float(np.mean(np.abs(errors))) if errors else None,
        "max_abs_error_sec": float(np.max(np.abs(errors))) if errors else None,
        "inferred_boundary_count": inferred,
        "matched_candidate_count": len(errors),
    }


def write_preview(path: Path, starts, output: Path, labels=None):
    from PIL import Image, ImageDraw, ImageFont

    cap = cv2.VideoCapture(str(path))
    thumbs = []
    font_path = "/home/wuyangcheng/.fonts/SimHei.ttf"
    font = ImageFont.truetype(font_path, 16) if Path(font_path).exists() else None
    for idx, sec in enumerate(starts):
        cap.set(cv2.CAP_PROP_POS_MSEC, sec * 1000)
        ok, frame = cap.read()
        if not ok:
            continue
        frame = cv2.resize(frame, (320, 180))
        label = ""
        if labels and idx < len(labels):
            label = labels[idx].get("recognized_standard_word") or "未匹配"
            confidence = labels[idx].get("assignment_confidence")
            if confidence == "low":
                label = "?" + label
            elif confidence == "medium":
                label = "~" + label
        canvas = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(canvas)
        draw.rectangle((0, 0, 320, 25), fill=(0, 0, 0, 170))
        text = f"{idx + 1:02d} {label} {sec:.2f}s"
        if font:
            draw.text((6, 3), text, font=font, fill=(255, 240, 0))
        else:
            draw.text((6, 3), text, fill=(255, 240, 0))
        frame = cv2.cvtColor(np.asarray(canvas), cv2.COLOR_RGB2BGR)
        thumbs.append(frame)
    cap.release()
    if not thumbs:
        return
    cols = 4
    rows = math.ceil(len(thumbs) / cols)
    canvas = np.zeros((rows * 180, cols * 320, 3), np.uint8)
    for i, frame in enumerate(thumbs):
        r, c = divmod(i, cols)
        canvas[r * 180:(r + 1) * 180, c * 320:(c + 1) * 320] = frame
    output.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output), canvas)


def write_word_list(path: Path, results, model_name):
    labels = results["正"].get("prompt_labels", [])
    lines = [
        "# 手语小宇宙编号1标准词汇播报识别列表",
        f"# 生成模型：Whisper {model_name}",
        "# 说明：第一个“3 2 1 开始”只是录制示意，不计入标准词汇；以下按视频中的实际次序排列。",
        "# 每个标准词汇应连续出现两次；[?] 表示由全局重复约束补全，仍需人工确认。",
        "# 一致性：直接识别词与 A-Z 标准词一致=一致；无稳定识别=未识别；识别到其他标准词=不一致。",
        "",
        "## 按视频次序",
        "",
    ]
    for i, item in enumerate(labels, 1):
        expected = PINYIN_ORDER[(i - 1) // 2]
        raw = item.get("pre_constraint_word")
        consistency = "一致" if raw == expected else "未识别" if not raw else "不一致"
        confidence = item.get("assignment_confidence", "unmatched")
        if confidence == "manual":
            marker = "[人工] "
        elif confidence == "high":
            marker = ""
        else:
            marker = "[?] "
        word = item.get("recognized_standard_word") or "未匹配"
        transcript = item.get("transcript_text") or "（无稳定转写）"
        lines.append(
            f"{i:02d}. {marker}{word}\t"
            f"期望={expected}\tWhisper={transcript}\t"
            f"原始匹配={raw or '—'}\t一致性={consistency}\tconfidence={confidence}"
        )
    lines += ["", "## 按重复块", ""]
    for i in range(0, len(labels), 2):
        expected = PINYIN_ORDER[i // 2]
        a = labels[i].get("recognized_standard_word") or "未匹配"
        b = labels[i + 1].get("recognized_standard_word") if i + 1 < len(labels) else "未匹配"
        raw_a = labels[i].get("pre_constraint_word")
        raw_b = labels[i + 1].get("pre_constraint_word") if i + 1 < len(labels) else None
        direct = "一致" if raw_a == expected and raw_b == expected else "未识别" if not raw_a and not raw_b else "不一致"
        conf = labels[i].get("assignment_confidence", "unmatched")
        lines.append(f"{i // 2 + 1:02d}. {a} / {b}\t期望={expected}\t一致性={direct}\tconfidence={conf}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_consistency_csv(path: Path, results):
    rows = []
    labels = results["正"].get("prompt_labels", [])
    starts = results["正"].get("aligned_prompt_starts", results["正"].get("prompt_starts", []))
    for i in range(EXPECTED_PROMPTS):
        item = labels[i] if i < len(labels) else {}
        expected = PINYIN_ORDER[i // 2]
        raw = item.get("pre_constraint_word")
        consistency = "一致" if raw == expected else "未识别" if not raw else "不一致"
        rows.append({
            "node_index": i + 1,
            "word_index": i // 2 + 1,
            "repeat_index": i % 2 + 1,
            "expected_standard_word": expected,
            "asr_raw_matched_word": raw or "",
            "asr_final_assigned_word": item.get("recognized_standard_word") or "",
            "transcript_text": item.get("transcript_text", ""),
            "consistency": consistency,
            "assignment_confidence": item.get("assignment_confidence", ""),
            "start_sec_front": round(float(starts[i]), 4) if i < len(starts) else "",
            "match_method": item.get("match_method", ""),
        })
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--volunteer-dir", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--transcribe", action="store_true", help="use local Whisper to recognize front-view word prompts")
    ap.add_argument("--whisper-model", default="tiny")
    ap.add_argument(
        "--keep-leading-countdown",
        action="store_true",
        help="保留最开始的录制示意“3 2 1 开始”（默认排除）",
    )
    ap.add_argument(
        "--known-leading-word",
        default=None,
        help="可选：人工确认的第一个标准词汇，例如“谗（羡慕）”；会固定前两次重复",
    )
    ap.add_argument(
        "--allow-free-order",
        action="store_true",
        help="关闭本批次按中文拼音首字母 A-Z 的固定顺序约束",
    )
    args = ap.parse_args()
    files = sorted(args.volunteer_dir.glob("*.mov"))
    if len(files) != 3:
        raise SystemExit(f"expected 3 .mov files, found {len(files)}")
    by_view = {view_name(p): p for p in files}
    if "正" not in by_view:
        raise SystemExit("front view is required as canonical reference")
    results = {}
    for view, path in by_view.items():
        try:
            detected = detect_prompts(
                path,
                drop_leading_countdown=not args.keep_leading_countdown,
            )
        except Exception as exc:
            # A damaged/unreadable audio stream in one camera must not block
            # the three-view batch. The front view remains canonical and the
            # affected view is aligned by its video-duration ratio below.
            detected = {
                "threshold": None,
                "q50": None,
                "q95": None,
                "active_intervals": [],
                "clusters": [],
                "prompt_starts": [],
                "excluded_countdown_intervals": [],
                "leading_countdown_excluded": None,
                "raw_cluster_count": 0,
                "post_leading_exclusion_cluster_count": 0,
                "expected_count": EXPECTED_PROMPTS,
                "count_match": False,
                "audio_error": f"{type(exc).__name__}: {exc}",
            }
        detected["path"] = str(path)
        detected["view"] = view
        detected["duration_sec"] = video_duration(path)
        results[view] = detected

    front = results["正"]["prompt_starts"]
    transcription = None
    if args.transcribe:
        transcription = transcribe_prompt_words(
            by_view["正"],
            front,
            args.whisper_model,
            args.known_leading_word,
            not args.allow_free_order,
        )
        results["正"]["transcription"] = transcription
        for i, label in enumerate(transcription["labels"]):
            if i < len(results["正"]["prompt_starts"]):
                results["正"]["prompt_labels"] = results["正"].get("prompt_labels", [])
                results["正"]["prompt_labels"].append(label)
    if transcription is None:
        results["正"]["prompt_labels"] = [
            {
                "transcript_text": "",
                "recognized_standard_word": None,
                "match_score": 0.0,
                "matched_alias": None,
                "match_method": "disabled",
            }
            for _ in front
        ]
    else:
        results["正"]["prompt_labels"] = transcription["labels"]
    for view, item in results.items():
        if view == "正":
            item["aligned_prompt_starts"] = front
            item["alignment"] = {"status": "canonical_front"}
            item["aligned_prompt_labels"] = item["prompt_labels"]
        else:
            if not item["prompt_starts"]:
                scale = item["duration_sec"] / max(results["正"]["duration_sec"], 1e-6)
                aligned = [float(t * scale) for t in front]
                alignment = {
                    "status": "all_inferred_from_front_duration_scale",
                    "scale": scale,
                    "offset_sec": 0.0,
                    "mean_abs_error_sec": None,
                    "max_abs_error_sec": None,
                    "inferred_boundary_count": len(aligned),
                    "matched_candidate_count": 0,
                }
            else:
                aligned, alignment = nearest_monotonic(
                    front, item["prompt_starts"], EXPECTED_PROMPTS
                )
            item["aligned_prompt_starts"] = aligned
            item["alignment"] = alignment
            item["aligned_prompt_labels"] = results["正"]["prompt_labels"]

    rows = []
    for view, item in results.items():
        starts = item["aligned_prompt_starts"]
        if len(starts) != EXPECTED_PROMPTS:
            continue
        ends = starts[1:] + [item["duration_sec"]]
        alignment_status = item["alignment"].get("status", "")
        inferred_count = int(item["alignment"].get("inferred_boundary_count", 0) or 0)
        labels = item.get("aligned_prompt_labels", [])
        for i, (start, end) in enumerate(zip(starts, ends)):
            label = labels[i] if i < len(labels) else {}
            expected_word = PINYIN_ORDER[i // 2]
            raw_asr_word = label.get("pre_constraint_word")
            asr_consistency = (
                "一致" if raw_asr_word == expected_word
                else "未识别" if not raw_asr_word
                else "不一致"
            )
            rows.append({
                "view": view,
                "source_path": item["path"],
                "word_index": i // 2 + 1,
                "word": label.get("recognized_standard_word") or PINYIN_ORDER[i // 2],
                "word_by_ordinal_fallback": PINYIN_ORDER[i // 2],
                "expected_standard_word": expected_word,
                "asr_raw_matched_word": raw_asr_word or "",
                "asr_consistency": asr_consistency,
                "transcript_text": label.get("transcript_text", ""),
                "word_match_score": label.get("match_score", 0.0),
                "word_match_method": label.get("match_method", "disabled"),
                "repeat_index": i % 2 + 1,
                "start_sec": round(float(start), 4),
                "end_sec": round(float(end), 4),
                "duration_sec": round(float(end - start), 4),
                "segment_rule": "word_prompt_start_to_next_word_prompt_start",
                "countdown_rule": "ignore_later_audio_bursts_in_same_prompt_cluster",
                "view_alignment_status": alignment_status,
                "inferred_boundary_count_for_view": inferred_count,
                "manual_status": "candidate",
            })
        if args.preview:
            write_preview(item["path"], starts, args.output_dir / "previews" / f"{view}.jpg", labels)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "voice_prompt_manifest.json").write_text(
        json.dumps({
            "schema_version": "slu-voice-prompt-segments-v1",
            "volunteer_dir": str(args.volunteer_dir),
            "recording_rule": "word announcement -> countdown 3 2 1 开始 -> one demonstration",
            "leading_countdown_rule": "initial 3 2 1 开始 is a recording-start cue and is not vocabulary prompt 01",
            "pinyin_order_rule": f"{len(PINYIN_ORDER)} vocabulary blocks are ordered by Chinese pronunciation initial A-Z",
            "segment_rule": "start at word announcement; end immediately before next word announcement",
            "countdown_excluded": True,
            "transcription_enabled": bool(args.transcribe),
            "transcription_model": args.whisper_model if args.transcribe else None,
            "expected_words": VOCABULARY,
            "expected_pinyin_order": PINYIN_ORDER,
            "views": results,
            "segments": rows,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
    if transcription is not None:
        write_word_list(
            args.output_dir / "recognized_standard_vocabulary_list.txt",
            results,
            args.whisper_model,
        )
        consistency_rows = write_consistency_csv(
            args.output_dir / "asr_consistency.csv",
            results,
        )
    else:
        consistency_rows = []
    with (args.output_dir / "voice_prompt_segments.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    report = [
        "# 编号1志愿者语音口令自动切割试验",
        "",
        f"- 输入目录：`{args.volunteer_dir}`",
        "- 切片起点：每个词语的画外音播报开始。",
        "- 切片终点：下一次词语画外音开始之前。",
        "- `3 2 1 开始`：视为同一提示簇中的后续音频，明确排除，不作为切片起点。",
        "- 开头独立的 `3 2 1 开始`：只是整段录制的示意开始提示，已整体排除，不计入第1个标准词汇。",
        "- 本批次词汇块按中文发音首字母 A-Z 约束；最后的“指导”作为 `指示` 的语音别名处理。",
        f"- 正面参考口令数：{len(front)}/{EXPECTED_PROMPTS}。",
        f"- 输出候选切片：{len(rows)} 条（应为 3 机位 × {EXPECTED_PROMPTS} 段 = {EXPECTED_PROMPTS * 3} 条）。",
        "",
        "## 视角探测摘要",
        "",
        "| 视角 | 原始音频簇 | 保留口令 | 候选是否40个 | 对齐误差 |",
        "|---|---:|---:|---|---:|",
    ]
    for view, item in results.items():
        err = item["alignment"].get("mean_abs_error_sec")
        match = "是" if len(item["prompt_starts"]) == EXPECTED_PROMPTS else "否"
        err_text = f"{err:.3f}s" if err is not None else "—"
        report.append(
            f'| {view} | {item["raw_cluster_count"]} | {len(item["prompt_starts"])} | '
            f'{match} | {err_text} |'
        )
        if item["alignment"].get("inferred_boundary_count"):
            report.append(
                f'- `{view}` 视角有 {item["alignment"]["inferred_boundary_count"]} 个边界由正面口令节点加相机偏移推断，'
                "需要人工核对对应画面。"
            )
    report += [
        "",
        "## 重要说明",
        "",
        "本试验利用统一录制模式，不把每一个音频活动都当成新词。一个提示簇的第一个音频活动作为词语播报，"
        "同一簇内后续的“3/2/1/开始”等音频活动被排除。当前仍然是候选切割，正式写入加权数据库前应人工检查"
        f"正面视角的 {EXPECTED_PROMPTS} 个口令节点，并检查左30/右30的映射。",
    ]
    if transcription is not None:
        matched = [
            x for x in results["正"]["prompt_labels"]
            if x.get("recognized_standard_word")
        ]
        confidence_counts = {}
        for item in results["正"]["prompt_labels"]:
            key = item.get("assignment_confidence", "unmatched")
            confidence_counts[key] = confidence_counts.get(key, 0) + 1
        report += [
            "",
            "## Whisper 词语识别与标准词汇匹配",
            "",
            f"- 模型：`{args.whisper_model}`",
            f"- 识别入口：正面音频；识别结果映射到左30/右30相同序号。",
            f"- 受“每个词恰好重复两次”约束后，{EXPECTED_PROMPTS}/{EXPECTED_PROMPTS} 个节点均获得标准词汇候选。",
            f"- 其中直接/高置信度证据：{confidence_counts.get('high', 0)}/{EXPECTED_PROMPTS}；"
            f"约束补全的低置信度候选：{confidence_counts.get('low', 0)}/{EXPECTED_PROMPTS}。",
            "- 预览图中普通文字表示高置信度匹配，`?词汇` 表示利用“每个词两次且每个词只占一组”的全局约束补全，"
            "必须人工核验；这不是 Whisper 直接确认的结果。",
            f"- 当前识别结果仍受到 `{args.whisper_model}` 模型、现场混响、画外音与倒计时连读影响；"
            "正式数据库仍需人工确认。",
            "",
            "| 节点 | Whisper 片段 | 标准词汇 | 匹配方式 |",
            "|---:|---|---|---|",
        ]
        for i, label in enumerate(results["正"]["prompt_labels"], 1):
            report.append(
                f'| {i} | {label.get("transcript_text", "") or "—"} | '
                f'{label.get("recognized_standard_word") or "未匹配"} | '
                f'{label.get("match_method", "—")} |'
            )
        counts = collections.Counter(row["consistency"] for row in consistency_rows)
        report += [
            "",
            "## A-Z 标准词汇一致性统计",
            "",
            f"- 一致：{counts.get('一致', 0)}/{EXPECTED_PROMPTS}",
            f"- 未识别：{counts.get('未识别', 0)}/{EXPECTED_PROMPTS}",
            f"- 不一致：{counts.get('不一致', 0)}/{EXPECTED_PROMPTS}",
            "- 详细结果见 `asr_consistency.csv`；该文件比较的是 Whisper 原始匹配词与固定 A-Z 标准词，"
            "不把全局约束补全误计为 ASR 直接识别。",
        ]
    (args.output_dir / "voice_prompt_segment_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"wrote {args.output_dir} with {len(rows)} candidate segments")


if __name__ == "__main__":
    main()

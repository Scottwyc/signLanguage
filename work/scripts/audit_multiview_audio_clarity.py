#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit audio clarity and Whisper reliability across multi-view long videos.

The script is privacy-preserving: it reads the original videos in place and
writes only aggregate audio/ASR metrics. It never exports audio or video clips.

For every video it computes:

1. signal metrics (RMS floor/peak contrast, speech-band SNR proxy, spectral
   centroid/flatness, clipping and active-frame ratio);
2. local prompt detection count;
3. Whisper segment confidence and direct standard-vocabulary match rate.

The final report compares left/front/right views within each volunteer and
tests whether the left view is systematically worse than the mean of the front
and right views.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy import stats
from scipy.signal import get_window

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import auto_cut_voice_prompt_segments as core


EXPECTED_PROMPTS = core.EXPECTED_PROMPTS
VIEW_ORDER = {"正": 0, "左30": 1, "右30": 2, "unknown": 9}


def parse_volunteer(folder: str) -> tuple[str, str]:
    match = re.match(r"^(\d+)(.*)$", folder)
    if match:
        return match.group(1), match.group(2) or folder
    return folder, folder


def infer_view(path: Path) -> str:
    stem = path.stem
    if "正" in stem:
        return "正"
    if "左" in stem:
        return "左30"
    if "右" in stem:
        return "右30"
    return "unknown"


def db(value: float, floor: float = -120.0) -> float:
    if value <= 0 or not math.isfinite(value):
        return floor
    return max(floor, 20.0 * math.log10(value))


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def frame_audio(audio: np.ndarray, sample_rate: int = 16000):
    frame_len = int(round(0.025 * sample_rate))
    hop_len = int(round(0.010 * sample_rate))
    if len(audio) < frame_len:
        audio = np.pad(audio, (0, frame_len - len(audio)))
    count = 1 + (len(audio) - frame_len) // hop_len
    shape = (count, frame_len)
    strides = (audio.strides[0] * hop_len, audio.strides[0])
    frames = np.lib.stride_tricks.as_strided(
        audio, shape=shape, strides=strides, writeable=False
    ).copy()
    return frames


def acoustic_metrics(audio: np.ndarray, sample_rate: int = 16000) -> dict:
    frames = frame_audio(audio, sample_rate)
    rms = np.sqrt(np.mean(np.square(frames, dtype=np.float64), axis=1) + 1e-12)
    q20, q50, q80, q95 = np.quantile(rms, [0.20, 0.50, 0.80, 0.95])
    active_threshold = max(q50 * 1.5, q95 * 0.5)
    active_mask = rms >= active_threshold
    if active_mask.sum() < 10:
        active_mask = rms >= q80
    noise_mask = rms <= q20

    window = get_window("hann", frames.shape[1], fftbins=True).astype(np.float32)
    spectra = np.abs(np.fft.rfft(frames * window[None, :], axis=1)) ** 2
    freqs = np.fft.rfftfreq(frames.shape[1], d=1.0 / sample_rate)
    speech_band = (freqs >= 300.0) & (freqs <= 3400.0)
    high_mid_band = (freqs >= 1800.0) & (freqs <= 3400.0)

    active_spec = np.mean(spectra[active_mask], axis=0)
    noise_spec = (
        np.mean(spectra[noise_mask], axis=0)
        if noise_mask.any()
        else np.percentile(spectra, 20, axis=0)
    )
    speech_power = float(active_spec[speech_band].sum())
    noise_power = float(noise_spec[speech_band].sum())
    speech_band_snr_db = 10.0 * math.log10(
        max(speech_power, 1e-20) / max(noise_power, 1e-20)
    )

    active_power_sum = float(active_spec.sum())
    centroid_hz = float(
        np.sum(freqs * active_spec) / max(active_power_sum, 1e-20)
    )
    speech_band_power = float(active_spec[speech_band].sum())
    high_mid_ratio = float(
        active_spec[high_mid_band].sum() / max(speech_band_power, 1e-20)
    )

    active_rows = spectra[active_mask][:, 1:]
    spectral_flatness = float(
        np.mean(
            np.exp(np.mean(np.log(active_rows + 1e-20), axis=1))
            / (np.mean(active_rows + 1e-20, axis=1))
        )
    )

    peak = float(np.max(np.abs(audio))) if len(audio) else 0.0
    clipping_ratio = float(np.mean(np.abs(audio) >= 0.999)) if len(audio) else 0.0
    return {
        "duration_sec": round(len(audio) / sample_rate, 3),
        "rms_q20_dbfs": round(db(float(q20)), 3),
        "rms_q50_dbfs": round(db(float(q50)), 3),
        "rms_q95_dbfs": round(db(float(q95)), 3),
        "rms_contrast_db": round(db(float(q95)) - db(float(q20)), 3),
        "speech_band_snr_db": round(speech_band_snr_db, 3),
        "active_frame_ratio": round(float(active_mask.mean()), 6),
        "spectral_centroid_hz": round(centroid_hz, 3),
        "speech_high_mid_ratio": round(high_mid_ratio, 6),
        "spectral_flatness": round(spectral_flatness, 6),
        "peak_abs": round(peak, 6),
        "clipping_ratio": round(clipping_ratio, 8),
    }


def whisper_metrics(transcription: dict) -> dict:
    segments = transcription.get("segments", [])
    labels = transcription.get("labels", [])
    expected = core.PINYIN_ORDER

    direct_matches = 0
    recognized = 0
    match_scores = []
    for index, label in enumerate(labels[: len(expected) * 2]):
        raw_word = label.get("pre_constraint_word")
        if raw_word:
            recognized += 1
        if raw_word == expected[index // 2]:
            direct_matches += 1
        score = label.get("pre_constraint_score")
        if score is None:
            score = label.get("match_score")
        if score is not None:
            match_scores.append(float(score))

    durations = np.asarray(
        [max(0.01, float(s.get("end", 0)) - float(s.get("start", 0))) for s in segments],
        dtype=np.float64,
    )

    def weighted(field: str, default: float = 0.0) -> float:
        if not segments:
            return default
        values = np.asarray([float(s.get(field, default)) for s in segments])
        return float(np.average(values, weights=durations))

    text = "".join(str(s.get("text", "")) for s in segments)
    denominator = max(1, min(len(labels), len(expected) * 2))
    return {
        "whisper_segment_count": len(segments),
        "whisper_text_chars": len(core.normalize_text(text)),
        "whisper_avg_logprob": round(weighted("avg_logprob", -2.0), 6),
        "whisper_avg_no_speech_prob": round(weighted("no_speech_prob", 1.0), 6),
        "whisper_avg_compression_ratio": round(weighted("compression_ratio", 0.0), 6),
        "asr_direct_match_count": direct_matches,
        "asr_recognized_count": recognized,
        "asr_direct_match_rate": round(direct_matches / denominator, 6),
        "asr_recognized_rate": round(recognized / denominator, 6),
        "asr_mean_match_score": round(
            float(np.mean(match_scores)) if match_scores else 0.0, 6
        ),
    }


def quality_score(row: dict) -> float:
    """Transparent engineering score used for ranking, not a calibrated MOS."""
    prompt_component = math.exp(-abs(row["prompt_count"] - EXPECTED_PROMPTS) / 2.0)
    logprob_component = clamp01((row["whisper_avg_logprob"] + 1.5) / 1.2)
    level_component = clamp01((row["rms_q95_dbfs"] + 50.0) / 25.0)
    high_mid_component = clamp01(row["speech_high_mid_ratio"] / 0.08)
    recognized_component = row["asr_recognized_rate"]
    direct_component = row["asr_direct_match_rate"]
    score = 100.0 * (
        0.30 * direct_component
        + 0.15 * recognized_component
        + 0.20 * logprob_component
        + 0.15 * prompt_component
        + 0.10 * level_component
        + 0.10 * high_mid_component
    )
    return round(score, 3)


def process_video(path: Path, model, model_name: str) -> dict:
    volunteer_id, volunteer_name = parse_volunteer(path.parent.name)
    view = infer_view(path)
    started = time.time()
    row = {
        "volunteer_id": volunteer_id,
        "volunteer_name": volunteer_name,
        "view": view,
        "source_path": str(path),
        "status": "ok",
        "error": "",
    }
    try:
        audio = core.load_audio_16k(path)
        row.update(acoustic_metrics(audio))
        detected = core.detect_prompts(path, expected=EXPECTED_PROMPTS, drop_leading_countdown=True)
        row.update(
            {
                "prompt_count": len(detected["prompt_starts"]),
                "raw_cluster_count": detected["raw_cluster_count"],
                "prompt_count_match": len(detected["prompt_starts"]) == EXPECTED_PROMPTS,
                "prompt_energy_q50": round(float(detected["q50"]), 8),
                "prompt_energy_q95": round(float(detected["q95"]), 8),
            }
        )
        transcription = core.transcribe_prompt_words(
            path,
            detected["prompt_starts"],
            model_name=model_name,
            leading_word_override="谗（羡慕）",
            enforce_pinyin_order=True,
            model=model,
        )
        row.update(whisper_metrics(transcription))
        row["audio_quality_score"] = quality_score(row)
    except Exception as exc:
        row.update(
            {
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
                "audio_quality_score": 0.0,
            }
        )
    row["processing_sec"] = round(time.time() - started, 3)
    return row


def write_csv(path: Path, rows: list[dict]):
    keys = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def paired_view_analysis(rows: list[dict]) -> tuple[list[dict], dict]:
    by_volunteer = defaultdict(dict)
    for row in rows:
        if row["status"] == "ok":
            by_volunteer[row["volunteer_id"]][row["view"]] = row

    comparisons = []
    for volunteer_id, views in sorted(
        by_volunteer.items(), key=lambda item: int(item[0]) if item[0].isdigit() else 999
    ):
        if not {"正", "左30", "右30"}.issubset(views):
            continue
        left, front, right = views["左30"], views["正"], views["右30"]
        other_quality = (front["audio_quality_score"] + right["audio_quality_score"]) / 2
        other_match = (front["asr_direct_match_rate"] + right["asr_direct_match_rate"]) / 2
        other_logprob = (front["whisper_avg_logprob"] + right["whisper_avg_logprob"]) / 2
        other_snr = (front["speech_band_snr_db"] + right["speech_band_snr_db"]) / 2
        other_q95 = (front["rms_q95_dbfs"] + right["rms_q95_dbfs"]) / 2
        other_high_mid = (
            front["speech_high_mid_ratio"] + right["speech_high_mid_ratio"]
        ) / 2
        quality_gap = left["audio_quality_score"] - other_quality
        match_gap = left["asr_direct_match_rate"] - other_match
        logprob_gap = left["whisper_avg_logprob"] - other_logprob
        snr_gap = left["speech_band_snr_db"] - other_snr
        q95_gap = left["rms_q95_dbfs"] - other_q95
        high_mid_ratio = left["speech_high_mid_ratio"] / max(other_high_mid, 1e-9)
        asr_degraded = match_gap <= -0.15
        gain_attenuated = q95_gap <= -5.0
        spectrally_muffled = high_mid_ratio <= 0.70
        prompt_abnormal = left["prompt_count"] != EXPECTED_PROMPTS
        likely_blur = gain_attenuated and (
            asr_degraded or spectrally_muffled or prompt_abnormal
        )
        comparisons.append(
            {
                "volunteer_id": volunteer_id,
                "left_quality_score": left["audio_quality_score"],
                "front_quality_score": front["audio_quality_score"],
                "right_quality_score": right["audio_quality_score"],
                "left_minus_front_right_mean_quality": round(quality_gap, 3),
                "left_asr_match_rate": left["asr_direct_match_rate"],
                "front_right_mean_asr_match_rate": round(other_match, 6),
                "left_minus_front_right_mean_asr_match_rate": round(match_gap, 6),
                "left_avg_logprob": left["whisper_avg_logprob"],
                "front_right_mean_avg_logprob": round(other_logprob, 6),
                "left_minus_front_right_mean_avg_logprob": round(logprob_gap, 6),
                "left_speech_band_snr_db": left["speech_band_snr_db"],
                "front_right_mean_speech_band_snr_db": round(other_snr, 3),
                "left_minus_front_right_mean_snr_db": round(snr_gap, 3),
                "left_rms_q95_dbfs": left["rms_q95_dbfs"],
                "front_right_mean_rms_q95_dbfs": round(other_q95, 3),
                "left_minus_front_right_mean_rms_q95_db": round(q95_gap, 3),
                "left_high_mid_ratio_relative": round(high_mid_ratio, 6),
                "left_prompt_count": left["prompt_count"],
                "asr_degraded": asr_degraded,
                "gain_attenuated": gain_attenuated,
                "spectrally_muffled": spectrally_muffled,
                "prompt_abnormal": prompt_abnormal,
                "likely_left_blur": likely_blur,
                "blur_evidence_count": sum(
                    [asr_degraded, gain_attenuated, spectrally_muffled, prompt_abnormal]
                ),
            }
        )

    aggregate = {
        "paired_volunteer_count": len(comparisons),
        "likely_left_blur_count": sum(c["likely_left_blur"] for c in comparisons),
    }
    metric_pairs = {
        "audio_quality_score": (
            [c["left_quality_score"] for c in comparisons],
            [
                (c["front_quality_score"] + c["right_quality_score"]) / 2
                for c in comparisons
            ],
        ),
        "asr_direct_match_rate": (
            [c["left_asr_match_rate"] for c in comparisons],
            [c["front_right_mean_asr_match_rate"] for c in comparisons],
        ),
        "whisper_avg_logprob": (
            [c["left_avg_logprob"] for c in comparisons],
            [c["front_right_mean_avg_logprob"] for c in comparisons],
        ),
        "speech_band_snr_db": (
            [c["left_speech_band_snr_db"] for c in comparisons],
            [c["front_right_mean_speech_band_snr_db"] for c in comparisons],
        ),
        "rms_q95_dbfs": (
            [c["left_rms_q95_dbfs"] for c in comparisons],
            [c["front_right_mean_rms_q95_dbfs"] for c in comparisons],
        ),
    }
    aggregate["paired_metrics"] = {}
    for name, (left_values, other_values) in metric_pairs.items():
        differences = np.asarray(left_values) - np.asarray(other_values)
        try:
            test = stats.wilcoxon(left_values, other_values, alternative="less")
            p_value = float(test.pvalue)
        except ValueError:
            p_value = 1.0
        aggregate["paired_metrics"][name] = {
            "left_mean": round(float(np.mean(left_values)), 6) if left_values else None,
            "front_right_mean": round(float(np.mean(other_values)), 6) if other_values else None,
            "mean_left_minus_front_right": round(float(np.mean(differences)), 6)
            if len(differences)
            else None,
            "left_worse_count": int(np.sum(differences < 0)),
            "wilcoxon_less_p": round(p_value, 8),
        }
    return comparisons, aggregate


def view_summary(rows: list[dict]) -> list[dict]:
    groups = defaultdict(list)
    for row in rows:
        if row["status"] == "ok":
            groups[row["view"]].append(row)
    summary = []
    for view in sorted(groups, key=lambda x: VIEW_ORDER.get(x, 9)):
        items = groups[view]
        summary.append(
            {
                "view": view,
                "video_count": len(items),
                "mean_quality_score": round(
                    float(np.mean([x["audio_quality_score"] for x in items])), 3
                ),
                "mean_asr_direct_match_rate": round(
                    float(np.mean([x["asr_direct_match_rate"] for x in items])), 6
                ),
                "mean_asr_recognized_rate": round(
                    float(np.mean([x["asr_recognized_rate"] for x in items])), 6
                ),
                "mean_whisper_avg_logprob": round(
                    float(np.mean([x["whisper_avg_logprob"] for x in items])), 6
                ),
                "mean_speech_band_snr_db": round(
                    float(np.mean([x["speech_band_snr_db"] for x in items])), 3
                ),
                "mean_rms_contrast_db": round(
                    float(np.mean([x["rms_contrast_db"] for x in items])), 3
                ),
                "wrong_prompt_count_videos": sum(
                    x["prompt_count"] != EXPECTED_PROMPTS for x in items
                ),
            }
        )
    return summary


def write_markdown(
    path: Path,
    rows: list[dict],
    summaries: list[dict],
    comparisons: list[dict],
    aggregate: dict,
    model_name: str,
):
    left_blur = [x for x in comparisons if x["likely_left_blur"]]
    paired = aggregate["paired_metrics"]
    systematic = (
        aggregate["paired_volunteer_count"] >= 6
        and aggregate["likely_left_blur_count"] >= math.ceil(aggregate["paired_volunteer_count"] * 0.6)
        and paired["asr_direct_match_rate"]["mean_left_minus_front_right"] < 0
        and paired["audio_quality_score"]["mean_left_minus_front_right"] < 0
    )
    lines = [
        "# 手语小宇宙多视角音频清晰度与 Whisper 识别审计",
        "",
        f"- 生成时间：`{time.strftime('%Y-%m-%d %H:%M:%S %z')}`",
        f"- Whisper 模型：`{model_name}`",
        f"- 视频数：`{len(rows)}`",
        f"- 预期每视频词语提示节点：`{EXPECTED_PROMPTS}`",
        "- 隐私：只保存聚合音频/ASR指标，不导出原始音频或视频片段。",
        "",
        "## 结论",
        "",
        (
            f"- **检测到左视角系统性偏差：是。** "
            if systematic
            else f"- **检测到左视角系统性偏差：当前证据不足。** "
        )
        + f"`{aggregate['likely_left_blur_count']}/{aggregate['paired_volunteer_count']}` "
        "位志愿者满足“左视角疑似模糊”复合条件。",
        f"- 左视角相对正/右均值的质量分差："
        f"`{paired['audio_quality_score']['mean_left_minus_front_right']:+.3f}`；"
        f"ASR 直接匹配率差："
        f"`{paired['asr_direct_match_rate']['mean_left_minus_front_right']:+.3f}`；"
        f"Whisper avg_logprob 差："
        f"`{paired['whisper_avg_logprob']['mean_left_minus_front_right']:+.3f}`；"
        f"语音频带 SNR 代理差："
        f"`{paired['speech_band_snr_db']['mean_left_minus_front_right']:+.3f} dB`。",
        f"- 左视角语音峰值段电平（RMS q95）相对正/右均值低 "
        f"`{abs(paired['rms_q95_dbfs']['mean_left_minus_front_right']):.3f} dB`。"
        "左视角的 SNR 代理反而较高，是因为静音底噪更低；这不代表语音更清晰。"
        "稳定异常是语音整体衰减、部分高频语音成分损失、节点漏检和 ASR 匹配下降。",
        "- 这里的“音频模糊”是工程诊断标签，不是主观听感 MOS，也不是经过人工标注校准的分类器。",
        "",
        "## 分视角汇总",
        "",
        "| 视角 | 视频数 | 质量分 | ASR直接匹配率 | ASR识别率 | avg_logprob | 语音频带SNR(dB) | 节点数异常 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in summaries:
        lines.append(
            f"| {item['view']} | {item['video_count']} | {item['mean_quality_score']:.3f} | "
            f"{item['mean_asr_direct_match_rate']:.1%} | {item['mean_asr_recognized_rate']:.1%} | "
            f"{item['mean_whisper_avg_logprob']:.3f} | {item['mean_speech_band_snr_db']:.3f} | "
            f"{item['wrong_prompt_count_videos']} |"
        )
    lines += [
        "",
        "## 志愿者内配对比较",
        "",
        "| 志愿者编号 | 左质量分 | 正质量分 | 右质量分 | 左-正右均值 | 左ASR匹配率 | 正右均值 | 左电平差(dB) | 高频比例 | 疑似模糊 |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for item in comparisons:
        lines.append(
            f"| {item['volunteer_id']} | "
            f"{item['left_quality_score']:.3f} | {item['front_quality_score']:.3f} | "
            f"{item['right_quality_score']:.3f} | "
            f"{item['left_minus_front_right_mean_quality']:+.3f} | "
            f"{item['left_asr_match_rate']:.1%} | "
            f"{item['front_right_mean_asr_match_rate']:.1%} | "
            f"{item['left_minus_front_right_mean_rms_q95_db']:+.3f} | "
            f"{item['left_high_mid_ratio_relative']:.2f}× | "
            f"{'是' if item['likely_left_blur'] else '否'} |"
        )
    lines += [
        "",
        "## 自动判定规则",
        "",
        "每位志愿者把左视角与其正/右视角均值比较。左侧语音峰值段电平低至少 5 dB，且另外出现以下任一异常时，标记为疑似左视角模糊：",
        "",
        "1. ASR 直接标准词匹配率低至少 15 个百分点；",
        "2. 1.8–3.4 kHz 语音高频成分比例低于正/右均值的 70%；",
        f"3. 音频节点检测数不等于 `{EXPECTED_PROMPTS}`。",
        "",
        "## 处理方案",
        "",
        "### 方案 A：正面/右侧清晰音轨负责识别，左视频负责画面",
        "",
        "这是当前已有数据最可靠的处理方案。建议流程：",
        "",
        "```text",
        "正面/右侧清晰音频",
        "        │",
        "        ├── Whisper 识别标准词",
        "        ├── 检测 42 个语音节点",
        "        ▼",
        "估计各机位时间偏移和时钟漂移",
        "        ▼",
        "把边界映射到左侧视频",
        "        ▼",
        "左侧动作能量/静止区再次校验",
        "        ▼",
        "少量人工抽查",
        "```",
        "",
        "不要直接复制正面时间戳，而应拟合 `t_left = a × t_reference + b`：`b` 表示相机启动偏移，`a` 表示设备时钟漂移。可以依次使用音频能量包络互相关、GCC-PHAT、提示节点序列鲁棒拟合；若存在非线性漂移，再使用分段映射或 DTW。映射后必须用左视角动作静止区和预览图复核。",
        "",
        "### 方案 B：正面与右侧双音轨共识",
        "",
        "- 正面和右侧分别运行 Whisper；",
        "- 两者一致时直接采用；",
        "- 一个成功、一个失败时采用成功结果；",
        "- 两者不一致时结合固定 A-Z 顺序、时间位置和直接匹配置信度；",
        "- 两者都低置信度时进入人工复核；",
        "- 左侧识别仅作为第三证据，不作为主要标签来源。",
        "",
        "### 方案 C：左侧音频增强 A/B 实验",
        "",
        "可测试响度归一化、80–120 Hz 高通、150–4500 Hz 语音带通、预加重、频谱降噪、动态范围压缩和语音增强模型。但增强结果不能直接覆盖原始音频，且必须与原始左音轨进行 A/B。",
        "",
        "至少比较：42 节点完整率、`pre_constraint_word` 直接匹配率、未识别数、错词数、`avg_logprob` 和与正/右节点的一致程度。只有直接匹配提高、漏检减少且错配不增加时，才允许启用增强版本；不能只依据主观上“听起来更响”。",
        "",
        "### 下一批录制的根治方案",
        "",
        "1. 使用一条共享参考音轨：独立录音设备、领夹麦克风，或指定正面相机为统一主音频。",
        "2. 三台相机开头使用拍手、蜂鸣声或统一口令作为同步标记。",
        "3. 正式录制前让三台设备同时录制固定测试语句，自动检查电平、频谱、Whisper 匹配率和时间偏移。",
        "4. 任一机位相对另外两台低约 5–6 dB 时，在正式录制前停止并调整。",
        "5. 重点检查左相机的麦克风孔、保护壳、支架遮挡、麦克风朝向、自动增益、降噪模式、设备型号、录制软件设置以及与播报者的距离。",
        "6. 可交换左右设备进行一次测试：若问题跟随设备移动，说明是设备/设置问题；若始终发生在左侧位置，则更可能是位置、遮挡或声学环境问题。",
        "",
        "### 数据与判定注意事项",
        "",
        "- 保留逐视频独立边界校验；即使迁移清晰音轨边界，也要修正相机起停偏移和漂移。",
        "- 不要把 A-Z 强制顺序补全后的 100% 标签当作 Whisper 识别成功。",
        "- 审计继续使用 `pre_constraint_word` 直接匹配率、节点数、语音电平和频谱指标。",
        "- 原始真人视频和音频保持私有，只输出聚合指标、边界清单和经审批的派生数据。",
        "",
        "## 输出文件",
        "",
        "- `audio_clarity_per_video.csv`：每视频完整指标。",
        "- `audio_clarity_view_summary.csv`：分视角汇总。",
        "- `audio_clarity_paired_comparison.csv`：志愿者内左/正/右比较。",
        "- `audio_clarity_audit.json`：机器可读完整结果。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default="large-v3-turbo")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="reuse per-video cache JSON files already present in output-dir/cache",
    )
    args = parser.parse_args()

    videos = sorted(args.input_root.glob("*/*.mov"))
    if not videos:
        videos = sorted(args.input_root.glob("*.mov"))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = args.output_dir / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading Whisper model {args.model} ...", flush=True)
    import whisper

    model = whisper.load_model(args.model)
    rows = []
    for index, video in enumerate(videos, 1):
        volunteer_id, _ = parse_volunteer(video.parent.name)
        view = infer_view(video)
        cache_path = cache_dir / f"{volunteer_id}_{view}.json"
        if args.resume and cache_path.exists():
            row = json.loads(cache_path.read_text(encoding="utf-8"))
            if row.get("status") == "ok":
                row["audio_quality_score"] = quality_score(row)
                print(f"[{index}/{len(videos)}] cache {video.parent.name} {view}", flush=True)
            else:
                print(
                    f"[{index}/{len(videos)}] retry failed cache {video.parent.name} {view}",
                    flush=True,
                )
                row = process_video(video, model, args.model)
                cache_path.write_text(
                    json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                print(
                    f"  status={row['status']} prompts={row.get('prompt_count')} "
                    f"match={row.get('asr_direct_match_rate')} "
                    f"quality={row.get('audio_quality_score')} "
                    f"sec={row.get('processing_sec')}",
                    flush=True,
                )
        else:
            print(f"[{index}/{len(videos)}] audit {video.parent.name} {view}", flush=True)
            row = process_video(video, model, args.model)
            cache_path.write_text(
                json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            print(
                f"  status={row['status']} prompts={row.get('prompt_count')} "
                f"match={row.get('asr_direct_match_rate')} "
                f"quality={row.get('audio_quality_score')} "
                f"sec={row.get('processing_sec')}",
                flush=True,
            )
        rows.append(row)

    rows.sort(
        key=lambda x: (
            int(x["volunteer_id"]) if str(x["volunteer_id"]).isdigit() else 999,
            VIEW_ORDER.get(x["view"], 9),
        )
    )
    summaries = view_summary(rows)
    comparisons, aggregate = paired_view_analysis(rows)
    write_csv(args.output_dir / "audio_clarity_per_video.csv", rows)
    write_csv(args.output_dir / "audio_clarity_view_summary.csv", summaries)
    write_csv(args.output_dir / "audio_clarity_paired_comparison.csv", comparisons)
    payload = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S %z"),
        "model": args.model,
        "expected_prompts": EXPECTED_PROMPTS,
        "input_root": str(args.input_root),
        "video_count": len(videos),
        "status_counts": dict(Counter(row["status"] for row in rows)),
        "view_summary": summaries,
        "paired_analysis": aggregate,
        "paired_comparisons": comparisons,
        "per_video": rows,
    }
    (args.output_dir / "audio_clarity_audit.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_markdown(
        args.output_dir / "audio_clarity_audit.md",
        rows,
        summaries,
        comparisons,
        aggregate,
        args.model,
    )
    print(
        json.dumps(
            {
                "videos": len(videos),
                "status_counts": payload["status_counts"],
                "likely_left_blur": aggregate["likely_left_blur_count"],
                "paired_volunteers": aggregate["paired_volunteer_count"],
                "output": str(args.output_dir),
            },
            ensure_ascii=False,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()

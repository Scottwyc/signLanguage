#!/usr/bin/env python3
"""Analyze phase-order metrics for flower/jump without changing scoring.

The current semantic-DTW scorer intentionally tolerates speed changes,
sampling jitter, sitting posture, and short browser captures. A hard
start/end-order guard can reject synthetic phase disorder, but it previously
hurt real saved web samples. This script tests candidate order metrics against
both synthetic sequence disorder and saved browser/API samples before any
metric is promoted into scoring.

It only reads cached Holistic JSON and scoring results. It does not call
``/api/score``, run Holistic, move the web marker, or restart 5080.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

import analyze_web_scoring_diagnostics as webdiag
from run_flower_jump_phase_order_robustness_gate import _template_json, _variant_specs
from score_holistic_sequence_mvp import (
    DEFAULT_SEMANTIC_PROFILE_JSON,
    FrameFeature,
    SemanticProfile,
    SequenceData,
    _phase_anchor_frame,
    _presence_ratio,
    _profile_summary,
    _semantic_action_window,
    _slice_sequence_window,
    frame_distance,
    load_semantic_profile,
    load_sequence,
    run_pair,
    with_dynamic_frame_weights,
)


REPO_ROOT = Path("/data/WYC/signLanguage")
DEFAULT_WEB_ROOT = REPO_ROOT / "work/generated/web_scoring_mvp"
DEFAULT_TEMPLATE_ROOT = REPO_ROOT / "work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results"
DEFAULT_OUTPUT_BASE = REPO_ROOT / "work/generated/scoring_mvp_run3"
DEFAULT_BACKEND_URL = "http://127.0.0.1:5080"
DEFAULT_WORDS = ["花", "跳"]
DEFAULT_ANCHORS = [0.10, 0.25, 0.50, 0.75, 0.90]
RELIABLE_CAPTURE_STATUSES = {"score_valid", "semantic_mismatch"}
KEEP_CATEGORIES = {"synthetic_positive", "web_reliable_nonlow"}
REJECT_CATEGORIES = {"synthetic_disordered"}


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _load_backend_status(backend_url: str, timeout_sec: float) -> Dict[str, Any]:
    url = backend_url.rstrip("/") + "/api/status"
    try:
        with urllib.request.urlopen(url, timeout=timeout_sec) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return {"ok": True, "url": url, "payload": payload, "error": ""}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"ok": False, "url": url, "payload": {}, "error": str(exc)}


def _safe_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _fmt(value: Any, digits: int = 3) -> str:
    number = _safe_float(value)
    if number is None:
        return "-"
    return f"{number:.{digits}f}"


def _score_band(score: Optional[float]) -> str:
    if score is None:
        return "error"
    if score >= 75.0:
        return "normal_like"
    if score >= 60.0:
        return "borderline"
    return "low"


def _as_metric_sequence(
    seq: SequenceData,
    profile: SemanticProfile,
    mode: str,
) -> Tuple[SequenceData, Dict[str, Any]]:
    full = with_dynamic_frame_weights(seq, profile)
    if mode == "full":
        return full, {"mode": "full", "used": False}
    if mode == "action_window":
        window = _semantic_action_window(full)
        sliced = _slice_sequence_window(full, window, "phase_order_metric_action_window")
        return sliced, {"mode": "action_window", "used": True, "window": window}
    raise RuntimeError(f"unknown phase metric mode: {mode}")


def _nearest_query_frame(
    anchor: FrameFeature,
    query: SequenceData,
    profile: SemanticProfile,
) -> Tuple[int, FrameFeature, float]:
    best_idx = 0
    best_frame = query.features[0]
    best_dist = float("inf")
    for idx, candidate in enumerate(query.features):
        dist, metrics = frame_distance(anchor, candidate, profile)
        weighted = float(metrics.get("weighted", dist))
        if weighted < best_dist:
            best_dist = weighted
            best_idx = idx
            best_frame = candidate
    return best_idx, best_frame, best_dist


def _kendall_metrics(indices: Sequence[int], max_index: int) -> Dict[str, float]:
    pair_count = 0
    concordant = 0
    discordant = 0
    ties = 0
    inversions = 0
    for a in range(len(indices)):
        for b in range(a + 1, len(indices)):
            pair_count += 1
            delta = int(indices[b]) - int(indices[a])
            if delta > 0:
                concordant += 1
            elif delta < 0:
                discordant += 1
                inversions += 1
            else:
                ties += 1
    adjacent_count = max(0, len(indices) - 1)
    adjacent_backtracks = 0
    max_backtrack = 0.0
    for a, b in zip(indices[:-1], indices[1:]):
        delta = int(b) - int(a)
        if delta < 0:
            adjacent_backtracks += 1
            max_backtrack = max(max_backtrack, abs(delta) / max(float(max_index), 1.0))
    inversion_rate = inversions / pair_count if pair_count else 0.0
    adjacent_backtrack_rate = adjacent_backtracks / adjacent_count if adjacent_count else 0.0
    tau = (concordant - discordant) / pair_count if pair_count else 0.0
    span = (max(indices) - min(indices)) / max(float(max_index), 1.0) if indices else 0.0
    unique_ratio = len(set(indices)) / max(float(len(indices)), 1.0)
    large_span = min(span / 0.45, 1.0)
    disorder_span_score = inversion_rate * large_span * unique_ratio
    adjacent_disorder_span_score = adjacent_backtrack_rate * large_span * unique_ratio
    backtrack_span_score = max_backtrack * large_span * unique_ratio
    order_score = max(
        0.0,
        min(
            1.0,
            0.48 * ((tau + 1.0) / 2.0)
            + 0.27 * (1.0 - inversion_rate)
            + 0.15 * (1.0 - adjacent_backtrack_rate)
            + 0.10 * min(span / 0.45, 1.0),
        ),
    )
    return {
        "pair_count": float(pair_count),
        "concordant": float(concordant),
        "discordant": float(discordant),
        "ties": float(ties),
        "inversions": float(inversions),
        "inversion_rate": float(inversion_rate),
        "kendall_tau": float(tau),
        "adjacent_backtracks": float(adjacent_backtracks),
        "adjacent_backtrack_rate": float(adjacent_backtrack_rate),
        "max_backtrack_norm": float(max_backtrack),
        "span_norm": float(span),
        "large_span_norm": float(large_span),
        "unique_index_ratio": float(unique_ratio),
        "disorder_span_score": float(disorder_span_score),
        "adjacent_disorder_span_score": float(adjacent_disorder_span_score),
        "backtrack_span_score": float(backtrack_span_score),
        "content_order_score": float(order_score),
    }


def _anchor_order_metrics(
    standard: SequenceData,
    query: SequenceData,
    profile: SemanticProfile,
    anchors: Sequence[float],
) -> Dict[str, Any]:
    if not standard.features or not query.features:
        return {"enabled": False, "reason": "empty_sequence"}
    rows: List[Dict[str, Any]] = []
    best_indices: List[int] = []
    distances: List[float] = []
    for phase in anchors:
        anchor = _phase_anchor_frame(standard, float(phase))
        if anchor is None:
            continue
        best_idx, best_frame, best_dist = _nearest_query_frame(anchor, query, profile)
        best_indices.append(best_idx)
        distances.append(best_dist)
        rows.append(
            {
                "target_phase": float(phase),
                "standard_frame_idx": int(anchor.frame_idx),
                "standard_semantic_phase": float(anchor.semantic_phase),
                "query_local_index": int(best_idx),
                "query_frame_idx": int(best_frame.frame_idx),
                "query_semantic_phase": float(best_frame.semantic_phase),
                "nearest_distance": float(best_dist),
            }
        )
    if len(best_indices) < 3:
        return {
            "enabled": False,
            "reason": "too_few_anchor_matches",
            "anchors": rows,
            "anchor_count": len(best_indices),
        }
    order = _kendall_metrics(best_indices, len(query.features) - 1)
    mean_distance = float(np.mean(distances)) if distances else 0.0
    max_distance = float(np.max(distances)) if distances else 0.0
    return {
        "enabled": True,
        "anchor_count": int(len(best_indices)),
        "query_length": int(len(query.features)),
        "best_query_indices": [int(idx) for idx in best_indices],
        "mean_nearest_distance": mean_distance,
        "max_nearest_distance": max_distance,
        "anchors": rows,
        **order,
    }


def _extract_metric_values(prefix: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
    fields = [
        "enabled",
        "anchor_count",
        "query_length",
        "inversion_rate",
        "kendall_tau",
        "adjacent_backtrack_rate",
        "max_backtrack_norm",
        "span_norm",
        "large_span_norm",
        "unique_index_ratio",
        "disorder_span_score",
        "adjacent_disorder_span_score",
        "backtrack_span_score",
        "content_order_score",
        "mean_nearest_distance",
        "max_nearest_distance",
    ]
    return {f"{prefix}_{field}": metrics.get(field) for field in fields}


def _score_scale_fields(result: Dict[str, Any]) -> Dict[str, Any]:
    score_scale = result.get("score_scale") or {}
    capture_quality = score_scale.get("capture_quality") or {}
    semantic_floor = score_scale.get("semantic_floor") or {}
    flower_guard = score_scale.get("flower_opening_guard") or {}
    flower_best = flower_guard.get("best") or {}
    fallback_from = semantic_floor.get("fallback_from") or {}
    two_finger_shape = semantic_floor.get("right_two_finger_shape") or {}
    return {
        "score_scale_reason": score_scale.get("reason"),
        "capture_quality_status": capture_quality.get("status"),
        "capture_quality_reason": capture_quality.get("reason"),
        "semantic_floor_used": semantic_floor.get("used"),
        "semantic_floor_source": semantic_floor.get("source"),
        "semantic_floor_reason": semantic_floor.get("reason"),
        "semantic_floor_score": _safe_float(score_scale.get("semantic_floor_score")),
        "semantic_floor_direction_cosine": _safe_float(semantic_floor.get("direction_cosine")),
        "semantic_floor_amplitude_ratio": _safe_float(semantic_floor.get("amplitude_ratio")),
        "semantic_floor_query_segment_coverage": _safe_float(semantic_floor.get("query_segment_coverage")),
        "semantic_floor_fallback_from_reason": fallback_from.get("reason"),
        "jump_two_finger_shape_mean": _safe_float(two_finger_shape.get("mean")),
        "flower_opening_passed": flower_guard.get("passed"),
        "flower_opening_score": _safe_float(flower_guard.get("best_score")),
        "flower_opening_delta_score": _safe_float(flower_best.get("delta_score")),
        "flower_opening_range_score": _safe_float(flower_best.get("range_score")),
        "flower_opening_delta": _safe_float(flower_best.get("delta")),
    }


def _analyze_pair(
    *,
    word: str,
    sample_id: str,
    category: str,
    source_kind: str,
    standard: SequenceData,
    query: SequenceData,
    profile: SemanticProfile,
    anchors: Sequence[float],
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    result = run_pair(standard, query, semantic_profile=profile, enable_cross_check=False)
    score = _safe_float(result.get("prototype_score"))
    score_value = 0.0 if score is None else score
    full_standard, full_standard_window = _as_metric_sequence(standard, profile, "full")
    full_query, full_query_window = _as_metric_sequence(query, profile, "full")
    action_standard, action_standard_window = _as_metric_sequence(standard, profile, "action_window")
    action_query, action_query_window = _as_metric_sequence(query, profile, "action_window")
    full_metrics = _anchor_order_metrics(full_standard, full_query, profile, anchors)
    action_metrics = _anchor_order_metrics(action_standard, action_query, profile, anchors)
    query_presence = _presence_ratio(query)
    row: Dict[str, Any] = {
        "word": word,
        "sample_id": sample_id,
        "category": category,
        "source_kind": source_kind,
        "score": score,
        "band": _score_band(score),
        "dtw_distance": _safe_float(result.get("dtw_distance")),
        "normalized_distance": _safe_float(result.get("normalized_distance")),
        "alignment_mode": (result.get("alignment_policy") or {}).get("mode"),
        "used_action_window": (result.get("action_window") or {}).get("used_for_scoring"),
        "standard_length": len(standard.features),
        "query_length": len(query.features),
        "full_metric_standard_window": full_standard_window,
        "full_metric_query_window": full_query_window,
        "action_metric_standard_window": action_standard_window,
        "action_metric_query_window": action_query_window,
        "left_hand_presence": _safe_float(query_presence.get("left_hand")),
        "right_hand_presence": _safe_float(query_presence.get("right_hand")),
        "two_hand_presence": min(float(query_presence.get("left_hand", 0.0)), float(query_presence.get("right_hand", 0.0))),
        **_score_scale_fields(result),
        **_extract_metric_values("full", full_metrics),
        **_extract_metric_values("action", action_metrics),
    }
    if extra:
        row.update(extra)
    row["full_anchor_indices"] = ",".join(str(idx) for idx in full_metrics.get("best_query_indices") or [])
    row["action_anchor_indices"] = ",".join(str(idx) for idx in action_metrics.get("best_query_indices") or [])
    row["full_anchor_detail"] = full_metrics.get("anchors") or []
    row["action_anchor_detail"] = action_metrics.get("anchors") or []
    row["score_value_for_sort"] = score_value
    return row


def _load_standard(template_root: Path, word: str, feature_mode: str) -> SequenceData:
    return load_sequence(_template_json(template_root, word), feature_mode, force_bbox=False)


def _synthetic_rows(
    words: Sequence[str],
    template_root: Path,
    semantic_profile_json: Path,
    feature_mode: str,
    anchors: Sequence[float],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for word in words:
        standard = _load_standard(template_root, word, feature_mode)
        profile = load_semantic_profile(word, semantic_profile_json)
        for spec in _variant_specs(standard):
            category = "synthetic_positive" if spec["kind"] == "positive" else "synthetic_disordered"
            rows.append(
                _analyze_pair(
                    word=word,
                    sample_id=str(spec["variant"]),
                    category=category,
                    source_kind="synthetic_phase_order",
                    standard=standard,
                    query=spec["query"],
                    profile=profile,
                    anchors=anchors,
                    extra={
                        "variant_kind": spec["kind"],
                        "expected": spec["expected"],
                        "rationale": spec["rationale"],
                    },
                )
            )
    return rows


def _template_path(template_root: Path, word: str, fallback: Path) -> Path:
    direct = template_root / word / f"{word}_holistic_results.json"
    if direct.exists():
        return direct
    folder = template_root / word
    matches = sorted(folder.glob("*_holistic_results.json")) if folder.exists() else []
    if matches:
        return matches[0]
    return fallback


def _iter_web_result_paths(
    web_root: Path,
    words: Sequence[str],
    *,
    latest: int,
    since_request_id: str,
    request_ids: Sequence[str],
) -> List[Path]:
    word_set = {str(word) for word in words if str(word)}
    paths: List[Path] = []
    for path in webdiag._iter_result_paths(web_root):
        stored = json.loads(path.read_text(encoding="utf-8"))
        target_word = str(stored.get("target_word") or "")
        if word_set and target_word not in word_set:
            continue
        paths.append(path)
    return webdiag.filter_result_paths(paths, request_ids=request_ids, since_request_id=since_request_id, latest=latest)


def _web_category(score: Optional[float], capture_quality_status: str) -> str:
    if capture_quality_status == "needs_recapture":
        return "web_needs_recapture"
    if capture_quality_status not in RELIABLE_CAPTURE_STATUSES:
        return "web_other"
    if score is not None and score >= 60.0:
        return "web_reliable_nonlow"
    return "web_reliable_low"


def _web_rows(
    words: Sequence[str],
    web_root: Path,
    template_root: Path,
    semantic_profile_json: Path,
    feature_mode: str,
    anchors: Sequence[float],
    *,
    latest: int,
    since_request_id: str,
    request_ids: Sequence[str],
    skip_web: bool,
) -> List[Dict[str, Any]]:
    if skip_web:
        return []
    rows: List[Dict[str, Any]] = []
    paths = _iter_web_result_paths(
        web_root,
        words,
        latest=latest,
        since_request_id=since_request_id,
        request_ids=request_ids,
    )
    for path in paths:
        stored = json.loads(path.read_text(encoding="utf-8"))
        request_id = str(stored.get("request_id") or path.parent.name)
        word = str(stored.get("target_word") or "")
        saved_standard_json = Path(stored.get("standard_json") or "")
        query_json = Path(stored.get("query_json") or "")
        if not query_json.exists():
            rows.append(
                {
                    "word": word,
                    "sample_id": request_id,
                    "category": "web_error",
                    "source_kind": "saved_web",
                    "error": f"missing query_json: {query_json}",
                }
            )
            continue
        standard_json = _template_path(template_root, word, saved_standard_json)
        try:
            standard = load_sequence(standard_json, feature_mode, force_bbox=False)
            query = load_sequence(query_json, feature_mode, force_bbox=False)
            profile = load_semantic_profile(word, semantic_profile_json)
            probe = run_pair(standard, query, semantic_profile=profile, enable_cross_check=False)
            score = _safe_float(probe.get("prototype_score"))
            quality = ((probe.get("score_scale") or {}).get("capture_quality") or {}).get("status") or ""
            category = _web_category(score, str(quality))
            rows.append(
                _analyze_pair(
                    word=word,
                    sample_id=request_id,
                    category=category,
                    source_kind="saved_web",
                    standard=standard,
                    query=query,
                    profile=profile,
                    anchors=anchors,
                    extra={
                        "request_id": request_id,
                        "saved_result_path": str(path),
                        "query_json": str(query_json),
                        "standard_json": str(standard_json),
                        "saved_standard_json": str(saved_standard_json),
                        "frame_count": stored.get("frame_count"),
                        "capture_fps": stored.get("capture_fps"),
                    },
                )
            )
        except Exception as exc:
            rows.append(
                {
                    "word": word,
                    "sample_id": request_id,
                    "category": "web_error",
                    "source_kind": "saved_web",
                    "error": str(exc),
                }
            )
    return rows


def _numeric_values(rows: Sequence[Dict[str, Any]], key: str) -> List[float]:
    values: List[float] = []
    for row in rows:
        value = _safe_float(row.get(key))
        if value is not None:
            values.append(value)
    return values


def _describe(values: Sequence[float]) -> Dict[str, Any]:
    if not values:
        return {"count": 0}
    arr = np.asarray(values, dtype=np.float32)
    return {
        "count": int(arr.size),
        "min": float(arr.min()),
        "p10": float(np.percentile(arr, 10)),
        "median": float(np.percentile(arr, 50)),
        "p90": float(np.percentile(arr, 90)),
        "max": float(arr.max()),
        "mean": float(arr.mean()),
    }


def _summarize_rows(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    by_word: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_word[str(row.get("word") or "unknown")].append(row)
    summary: Dict[str, Any] = {
        "rows": len(rows),
        "by_category": dict(Counter(str(row.get("category") or "unknown") for row in rows)),
        "by_word": {},
    }
    metric_keys = [
        "score",
        "full_inversion_rate",
        "full_kendall_tau",
        "full_adjacent_backtrack_rate",
        "full_max_backtrack_norm",
        "full_disorder_span_score",
        "full_adjacent_disorder_span_score",
        "full_backtrack_span_score",
        "full_content_order_score",
        "action_inversion_rate",
        "action_kendall_tau",
        "action_adjacent_backtrack_rate",
        "action_max_backtrack_norm",
        "action_disorder_span_score",
        "action_adjacent_disorder_span_score",
        "action_backtrack_span_score",
        "action_content_order_score",
        "flower_opening_delta_score",
        "flower_opening_range_score",
        "semantic_floor_direction_cosine",
        "semantic_floor_amplitude_ratio",
    ]
    for word, items in sorted(by_word.items()):
        by_category: Dict[str, Dict[str, Any]] = {}
        category_map: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for row in items:
            category_map[str(row.get("category") or "unknown")].append(row)
        for category, category_rows in sorted(category_map.items()):
            by_category[category] = {
                "count": len(category_rows),
                "metrics": {key: _describe(_numeric_values(category_rows, key)) for key in metric_keys},
                "score_scale_reasons": dict(Counter(str(row.get("score_scale_reason") or "") for row in category_rows)),
                "capture_quality": dict(Counter(str(row.get("capture_quality_status") or "") for row in category_rows)),
                "semantic_floor_sources": dict(Counter(str(row.get("semantic_floor_source") or "") for row in category_rows)),
            }
        summary["by_word"][word] = {
            "count": len(items),
            "by_category": by_category,
        }
    return summary


def _threshold_scan(rows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    metric_specs = [
        ("full_inversion_rate", "high"),
        ("full_adjacent_backtrack_rate", "high"),
        ("full_max_backtrack_norm", "high"),
        ("full_disorder_span_score", "high"),
        ("full_adjacent_disorder_span_score", "high"),
        ("full_backtrack_span_score", "high"),
        ("full_kendall_tau", "low"),
        ("full_content_order_score", "low"),
        ("action_inversion_rate", "high"),
        ("action_adjacent_backtrack_rate", "high"),
        ("action_max_backtrack_norm", "high"),
        ("action_disorder_span_score", "high"),
        ("action_adjacent_disorder_span_score", "high"),
        ("action_backtrack_span_score", "high"),
        ("action_kendall_tau", "low"),
        ("action_content_order_score", "low"),
    ]
    scanned: List[Dict[str, Any]] = []
    by_word: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_word[str(row.get("word") or "unknown")].append(row)
    for word, word_rows in sorted(by_word.items()):
        keep_rows = [row for row in word_rows if row.get("category") in KEEP_CATEGORIES]
        reject_rows = [row for row in word_rows if row.get("category") in REJECT_CATEGORIES]
        if not keep_rows or not reject_rows:
            continue
        for metric, direction in metric_specs:
            candidates = sorted({value for value in _numeric_values(word_rows, metric)})
            if not candidates:
                continue
            best: Optional[Dict[str, Any]] = None
            for threshold in candidates:
                if direction == "high":
                    rejected_keep = [row for row in keep_rows if _safe_float(row.get(metric)) is not None and float(row[metric]) >= threshold]
                    rejected_negative = [row for row in reject_rows if _safe_float(row.get(metric)) is not None and float(row[metric]) >= threshold]
                else:
                    rejected_keep = [row for row in keep_rows if _safe_float(row.get(metric)) is not None and float(row[metric]) <= threshold]
                    rejected_negative = [row for row in reject_rows if _safe_float(row.get(metric)) is not None and float(row[metric]) <= threshold]
                kept_negative = len(reject_rows) - len(rejected_negative)
                item = {
                    "word": word,
                    "metric": metric,
                    "direction": direction,
                    "threshold": float(threshold),
                    "keep_total": len(keep_rows),
                    "reject_total": len(reject_rows),
                    "keep_rejected": len(rejected_keep),
                    "reject_rejected": len(rejected_negative),
                    "reject_kept": kept_negative,
                    "keep_rejected_ids": [str(row.get("sample_id") or "") for row in rejected_keep[:10]],
                    "reject_kept_ids": [str(row.get("sample_id") or "") for row in reject_rows if row not in rejected_negative][:10],
                }
                rank = (
                    -1000 * int(item["keep_rejected"])
                    + 100 * int(item["reject_rejected"])
                    - 10 * int(item["reject_kept"])
                )
                item["rank"] = rank
                if best is None or rank > int(best["rank"]):
                    best = item
            if best is not None:
                best["safe_candidate"] = bool(best["keep_rejected"] == 0 and best["reject_rejected"] > 0)
                best["perfect_candidate"] = bool(best["keep_rejected"] == 0 and best["reject_kept"] == 0)
                scanned.append(best)
    return sorted(
        scanned,
        key=lambda item: (
            not bool(item.get("perfect_candidate")),
            not bool(item.get("safe_candidate")),
            int(item.get("keep_rejected") or 0),
            -int(item.get("reject_rejected") or 0),
            str(item.get("word") or ""),
            str(item.get("metric") or ""),
        ),
    )


def _short_sample_list(rows: Sequence[Dict[str, Any]], category: str, metric: str, reverse: bool = True, limit: int = 8) -> List[Dict[str, Any]]:
    selected = [row for row in rows if row.get("category") == category and _safe_float(row.get(metric)) is not None]
    selected = sorted(selected, key=lambda row: float(row.get(metric) or 0.0), reverse=reverse)
    out = []
    for row in selected[:limit]:
        out.append(
            {
                "word": row.get("word"),
                "sample_id": row.get("sample_id"),
                "score": row.get("score"),
                "metric": row.get(metric),
                "category": row.get("category"),
                "score_scale_reason": row.get("score_scale_reason"),
                "capture_quality_status": row.get("capture_quality_status"),
                "semantic_floor_source": row.get("semantic_floor_source"),
                "full_anchor_indices": row.get("full_anchor_indices"),
                "action_anchor_indices": row.get("action_anchor_indices"),
            }
        )
    return out


def _build_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# 花/跳相位顺序候选指标诊断")
    lines.append("")
    lines.append(f"- 生成时间：`{payload['generated_at']}`")
    lines.append(f"- 标准库：`{payload['template_root']}`")
    lines.append(f"- Web 样本根目录：`{payload['web_root']}`")
    lines.append(f"- 语义 profile：`{payload['semantic_profile_json']}`")
    lines.append(f"- 目标词：`{', '.join(payload['words'])}`")
    lines.append(f"- 语义锚点：`{payload['anchors']}`")
    lines.append("- 口径：只读缓存 Holistic JSON；不调用 `/api/score`，不运行 Holistic，不重启 5080。")
    lines.append("")
    backend = payload.get("backend_status") or {}
    if backend.get("ok"):
        backend_payload = backend.get("payload") or {}
        worker = backend_payload.get("worker") or {}
        scoring = backend_payload.get("scoring_module") or {}
        lines.append(
            f"- 5080 状态：worker=`{worker.get('status')}`，pid=`{((worker.get('process') or {}).get('pid'))}`，"
            f"reload_count=`{scoring.get('reload_count')}`，last_reload_error=`{scoring.get('last_reload_error')}`"
        )
    else:
        lines.append(f"- 5080 状态：读取失败 `{backend.get('error') or '-'}`")
    lines.append("")
    lines.append("## 结论")
    lines.append("")
    safe = [item for item in payload["threshold_scan"] if item.get("safe_candidate")]
    perfect = [item for item in payload["threshold_scan"] if item.get("perfect_candidate")]
    lines.append(f"- 总样本行：`{payload['summary']['rows']}`，类别计数：`{payload['summary']['by_category']}`")
    lines.append(f"- 零误伤 keep 样本且能拒绝部分乱序的候选规则：`{len(safe)}`")
    lines.append(f"- 零误伤且合成乱序全拒绝的候选规则：`{len(perfect)}`")
    if perfect:
        lines.append("- 诊断结论：存在可进一步验证的完美候选规则，但仍需跑正式质量门后才能接入 scorer。")
    elif safe:
        lines.append("- 诊断结论：存在可辅助诊断的安全候选，但不能单独覆盖全部乱序；暂不直接改线上评分。")
    else:
        lines.append("- 诊断结论：当前候选指标没有形成零误伤分离，不能接入线上评分，只能作为下一轮特征设计依据。")
    lines.append("")
    lines.append("## 最优候选阈值")
    lines.append("")
    lines.append("| 词条 | 指标 | 方向 | 阈值 | keep误拒 | 乱序拒绝 | 乱序漏过 | safe | perfect | 漏过样本 |")
    lines.append("|---|---|---|---:|---:|---:|---:|---|---|---|")
    for item in payload["threshold_scan"][:24]:
        direction = ">=" if item["direction"] == "high" else "<="
        lines.append(
            f"| {item['word']} | {item['metric']} | {direction} | {_fmt(item['threshold'])} | "
            f"{item['keep_rejected']}/{item['keep_total']} | {item['reject_rejected']}/{item['reject_total']} | "
            f"{item['reject_kept']} | {'Y' if item.get('safe_candidate') else 'N'} | "
            f"{'Y' if item.get('perfect_candidate') else 'N'} | {', '.join(item.get('reject_kept_ids') or []) or '-'} |"
        )
    lines.append("")
    lines.append("## 分词条分布")
    lines.append("")
    for word, word_summary in payload["summary"]["by_word"].items():
        lines.append(f"### {word}")
        lines.append("")
        lines.append("| 类别 | 数量 | 分数中位 | 分数范围 | full反序率中位/最大 | full跨度反序中位/最大 | full tau中位/最小 | action反序率中位/最大 | action跨度反序中位/最大 | action tau中位/最小 | 花delta中位 | 跳方向中位 |")
        lines.append("|---|---:|---:|---|---|---|---|---|---|---|---:|---:|")
        for category, item in word_summary["by_category"].items():
            metrics = item["metrics"]
            score = metrics.get("score") or {}
            full_inv = metrics.get("full_inversion_rate") or {}
            full_disorder = metrics.get("full_disorder_span_score") or {}
            full_tau = metrics.get("full_kendall_tau") or {}
            action_inv = metrics.get("action_inversion_rate") or {}
            action_disorder = metrics.get("action_disorder_span_score") or {}
            action_tau = metrics.get("action_kendall_tau") or {}
            flower_delta = metrics.get("flower_opening_delta_score") or {}
            jump_dir = metrics.get("semantic_floor_direction_cosine") or {}
            lines.append(
                f"| {category} | {item['count']} | {_fmt(score.get('median'))} | "
                f"{_fmt(score.get('min'))}-{_fmt(score.get('max'))} | "
                f"{_fmt(full_inv.get('median'))}/{_fmt(full_inv.get('max'))} | "
                f"{_fmt(full_disorder.get('median'))}/{_fmt(full_disorder.get('max'))} | "
                f"{_fmt(full_tau.get('median'))}/{_fmt(full_tau.get('min'))} | "
                f"{_fmt(action_inv.get('median'))}/{_fmt(action_inv.get('max'))} | "
                f"{_fmt(action_disorder.get('median'))}/{_fmt(action_disorder.get('max'))} | "
                f"{_fmt(action_tau.get('median'))}/{_fmt(action_tau.get('min'))} | "
                f"{_fmt(flower_delta.get('median'))} | {_fmt(jump_dir.get('median'))} |"
            )
        lines.append("")
    lines.append("## 高风险样本摘录")
    lines.append("")
    lines.append("### 合成乱序中 full_inversion_rate 最高")
    lines.append("")
    lines.append("| 词条 | 样本 | 分数 | metric | capture | floor | full锚点 | action锚点 |")
    lines.append("|---|---|---:|---:|---|---|---|---|")
    for row in payload["sample_lists"]["synthetic_disordered_full_inversion_high"]:
        lines.append(
            f"| {row['word']} | {row['sample_id']} | {_fmt(row['score'])} | {_fmt(row['metric'])} | "
            f"{row.get('capture_quality_status') or '-'} | {row.get('semantic_floor_source') or '-'} | "
            f"{row.get('full_anchor_indices') or '-'} | {row.get('action_anchor_indices') or '-'} |"
        )
    lines.append("")
    lines.append("### 网页可评分样本中 full_inversion_rate 最高")
    lines.append("")
    lines.append("| 词条 | 样本 | 分数 | metric | capture | floor | full锚点 | action锚点 |")
    lines.append("|---|---|---:|---:|---|---|---|---|")
    for row in payload["sample_lists"]["web_keep_full_inversion_high"]:
        lines.append(
            f"| {row['word']} | {row['sample_id']} | {_fmt(row['score'])} | {_fmt(row['metric'])} | "
            f"{row.get('capture_quality_status') or '-'} | {row.get('semantic_floor_source') or '-'} | "
            f"{row.get('full_anchor_indices') or '-'} | {row.get('action_anchor_indices') or '-'} |"
        )
    lines.append("")
    lines.append("## 下一步约束")
    lines.append("")
    lines.append("- 任何相位顺序规则接入 scorer 前，必须先在本报告的 `web_reliable_nonlow` 样本上零误伤，再跑完整 `flower_jump_quality_gate`。")
    lines.append("- 对 `跳`，不能再使用全序列端点硬规则；若要接入，应优先约束语义 floor 的局部 segment 与标准锚点顺序。")
    lines.append("- 对 `花`，张开 delta 比 range 更接近语义顺序，但需要以真实网页通过样本的 delta 分布设阈值。")
    return "\n".join(lines) + "\n"


def _csv_fields(rows: Sequence[Dict[str, Any]]) -> List[str]:
    preferred = [
        "word",
        "sample_id",
        "category",
        "source_kind",
        "score",
        "band",
        "score_scale_reason",
        "capture_quality_status",
        "capture_quality_reason",
        "semantic_floor_used",
        "semantic_floor_source",
        "semantic_floor_reason",
        "semantic_floor_direction_cosine",
        "semantic_floor_amplitude_ratio",
        "semantic_floor_query_segment_coverage",
        "jump_two_finger_shape_mean",
        "flower_opening_passed",
        "flower_opening_score",
        "flower_opening_delta_score",
        "flower_opening_range_score",
        "flower_opening_delta",
        "full_inversion_rate",
        "full_kendall_tau",
        "full_adjacent_backtrack_rate",
        "full_max_backtrack_norm",
        "full_span_norm",
        "full_large_span_norm",
        "full_unique_index_ratio",
        "full_disorder_span_score",
        "full_adjacent_disorder_span_score",
        "full_backtrack_span_score",
        "full_content_order_score",
        "full_mean_nearest_distance",
        "full_anchor_indices",
        "action_inversion_rate",
        "action_kendall_tau",
        "action_adjacent_backtrack_rate",
        "action_max_backtrack_norm",
        "action_span_norm",
        "action_large_span_norm",
        "action_unique_index_ratio",
        "action_disorder_span_score",
        "action_adjacent_disorder_span_score",
        "action_backtrack_span_score",
        "action_content_order_score",
        "action_mean_nearest_distance",
        "action_anchor_indices",
        "left_hand_presence",
        "right_hand_presence",
        "two_hand_presence",
        "alignment_mode",
        "used_action_window",
        "standard_length",
        "query_length",
        "variant_kind",
        "expected",
        "request_id",
        "query_json",
        "standard_json",
        "error",
    ]
    all_keys = set(preferred)
    for row in rows:
        all_keys.update(row.keys())
    excluded = {
        "full_anchor_detail",
        "action_anchor_detail",
        "full_metric_standard_window",
        "full_metric_query_window",
        "action_metric_standard_window",
        "action_metric_query_window",
        "score_value_for_sort",
    }
    return [key for key in preferred if key in all_keys and key not in excluded] + sorted(all_keys - set(preferred) - excluded)


def write_outputs(
    rows: Sequence[Dict[str, Any]],
    output_dir: Path,
    payload_base: Dict[str, Any],
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    threshold_scan = _threshold_scan(rows)
    sample_lists = {
        "synthetic_disordered_full_inversion_high": _short_sample_list(
            rows, "synthetic_disordered", "full_inversion_rate", reverse=True
        ),
        "web_keep_full_inversion_high": _short_sample_list(
            rows, "web_reliable_nonlow", "full_inversion_rate", reverse=True
        ),
    }
    payload = {
        **payload_base,
        "summary": _summarize_rows(rows),
        "threshold_scan": threshold_scan,
        "sample_lists": sample_lists,
        "rows": list(rows),
    }
    json_path = output_dir / "flower_jump_phase_order_metric_analysis.json"
    md_path = output_dir / "flower_jump_phase_order_metric_analysis.md"
    csv_path = output_dir / "flower_jump_phase_order_metric_rows.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    fields = _csv_fields(rows)
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    payload["json_path"] = str(json_path)
    payload["md_path"] = str(md_path)
    payload["csv_path"] = str(csv_path)
    return payload


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze flower/jump phase-order candidate metrics.")
    parser.add_argument("--web-root", default=str(DEFAULT_WEB_ROOT))
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_phase_order_metric_analysis_current"))
    parser.add_argument("--words", nargs="+", default=DEFAULT_WORDS)
    parser.add_argument("--feature-mode", choices=["auto", "landmark", "bbox"], default="auto")
    parser.add_argument("--anchors", nargs="*", type=float, default=DEFAULT_ANCHORS)
    parser.add_argument("--latest", type=int, default=0, help="Only analyze the latest N matching web samples.")
    parser.add_argument("--since-request-id", default="", help="Only analyze web request_id greater than this value.")
    parser.add_argument("--request-ids", nargs="*", default=[], help="Only analyze listed web request ids.")
    parser.add_argument("--skip-web", action="store_true", help="Only analyze synthetic phase-order variants.")
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--status-timeout-sec", type=float, default=3.0)
    args = parser.parse_args(argv)

    words = [str(word) for word in args.words]
    anchors = [float(value) for value in args.anchors] if args.anchors else DEFAULT_ANCHORS
    template_root = Path(args.template_root)
    web_root = Path(args.web_root)
    semantic_profile_json = Path(args.semantic_profile_json)
    output_dir = Path(args.output_dir)

    rows = []
    rows.extend(_synthetic_rows(words, template_root, semantic_profile_json, args.feature_mode, anchors))
    rows.extend(
        _web_rows(
            words,
            web_root,
            template_root,
            semantic_profile_json,
            args.feature_mode,
            anchors,
            latest=args.latest,
            since_request_id=args.since_request_id,
            request_ids=args.request_ids,
            skip_web=bool(args.skip_web),
        )
    )
    payload = write_outputs(
        rows,
        output_dir,
        {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "claim_policy": "phase-order metric analysis only; not promoted to calibrated scoring",
            "web_root": str(web_root),
            "template_root": str(template_root),
            "semantic_profile_json": str(semantic_profile_json),
            "words": words,
            "anchors": anchors,
            "filters": {
                "latest": args.latest,
                "since_request_id": args.since_request_id,
                "request_ids": list(args.request_ids),
                "skip_web": bool(args.skip_web),
            },
            "backend_status": _load_backend_status(args.backend_url, args.status_timeout_sec),
            "semantic_profiles": {
                word: _profile_summary(load_semantic_profile(word, semantic_profile_json)) for word in words
            },
        },
    )
    print(f"已生成相位顺序候选指标 JSON：{payload['json_path']}")
    print(f"已生成相位顺序候选指标报告：{payload['md_path']}")
    print(f"已生成相位顺序候选指标 CSV：{payload['csv_path']}")
    print(f"类别计数：{payload['summary']['by_category']}")
    safe = [item for item in payload["threshold_scan"] if item.get("safe_candidate")]
    perfect = [item for item in payload["threshold_scan"] if item.get("perfect_candidate")]
    print(f"safe候选：{len(safe)}，perfect候选：{len(perfect)}")
    for item in payload["threshold_scan"][:8]:
        direction = ">=" if item["direction"] == "high" else "<="
        print(
            f"- {item['word']} {item['metric']} {direction} {_fmt(item['threshold'])}: "
            f"keep_rejected={item['keep_rejected']}/{item['keep_total']}, "
            f"reject_rejected={item['reject_rejected']}/{item['reject_total']}, "
            f"safe={item.get('safe_candidate')}, perfect={item.get('perfect_candidate')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

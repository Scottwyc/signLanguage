#!/usr/bin/env python3
"""Build semantic diagnostics for saved web scoring samples.

This script reuses saved Holistic JSON from the web backend. It does not
restart or call the persistent Holistic worker, so it is safe to run after a
scoring-module hot reload.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Any, Dict, Iterable, List, Optional, Sequence

from score_holistic_sequence_mvp import (
    DEFAULT_SEMANTIC_PROFILE_JSON,
    _presence_ratio,
    load_semantic_profile,
    load_sequence,
    run_pair,
)


REPO_ROOT = Path("/data/WYC/signLanguage")
DEFAULT_WEB_ROOT = REPO_ROOT / "work/generated/web_scoring_mvp"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "work/generated/scoring_mvp_run3/web_semantic_diagnostics_current"
DEFAULT_TEMPLATE_ROOT = REPO_ROOT / "work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results"


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_result_paths(web_root: Path) -> List[Path]:
    return sorted(web_root.glob("web_*/scoring_result.json"), key=lambda path: path.parent.name)


def filter_result_paths(
    paths: Iterable[Path],
    *,
    request_ids: Optional[Sequence[str]] = None,
    since_request_id: str = "",
    latest: int = 0,
) -> List[Path]:
    selected = sorted(paths, key=lambda path: path.parent.name)
    request_id_set = {str(item) for item in (request_ids or []) if str(item)}
    if request_id_set:
        selected = [path for path in selected if path.parent.name in request_id_set]
    if since_request_id:
        selected = [path for path in selected if path.parent.name > since_request_id]
    if latest > 0:
        selected = selected[-latest:]
    return selected


def _score_band(score: Optional[float]) -> str:
    if score is None:
        return "error"
    if score >= 75.0:
        return "normal_like"
    if score >= 60.0:
        return "borderline"
    return "low"


def _template_path(template_root: Optional[Path], word: str, fallback: Path) -> tuple[Path, str]:
    if template_root is None:
        return fallback, "saved_standard_json"
    direct = template_root / word / f"{word}_holistic_results.json"
    if direct.exists():
        return direct, "template_root"
    folder = template_root / word
    matches = sorted(folder.glob("*_holistic_results.json")) if folder.exists() else []
    if matches:
        return matches[0], "template_root"
    return fallback, "saved_standard_json_fallback"


def _safe_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def _float_or(value: Any, default: float = 0.0) -> float:
    parsed = _safe_float(value)
    return default if parsed is None else float(parsed)


def _mean(values: Iterable[Any]) -> Optional[float]:
    clean = [_safe_float(value) for value in values]
    clean = [value for value in clean if value is not None]
    return sum(clean) / len(clean) if clean else None


def _median(values: Iterable[Any]) -> Optional[float]:
    clean = [_safe_float(value) for value in values]
    clean = [value for value in clean if value is not None]
    return float(median(clean)) if clean else None


def _min(values: Iterable[Any]) -> Optional[float]:
    clean = [_safe_float(value) for value in values]
    clean = [value for value in clean if value is not None]
    return min(clean) if clean else None


def _max(values: Iterable[Any]) -> Optional[float]:
    clean = [_safe_float(value) for value in values]
    clean = [value for value in clean if value is not None]
    return max(clean) if clean else None


def _top_counts(values: Iterable[Any], limit: int = 3) -> str:
    counter = Counter(str(value or "unknown") for value in values)
    return ", ".join(f"{name}:{count}" for name, count in counter.most_common(limit))


def _reliable_for_scoring(row: Dict[str, Any]) -> bool:
    return str(row.get("capture_quality_status") or "") in {"score_valid", "semantic_mismatch"}


def _effective_summary(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    reliable = [row for row in rows if _reliable_for_scoring(row)]
    non_low = [row for row in reliable if row.get("band") in {"normal_like", "borderline"}]
    low = [row for row in reliable if row.get("band") == "low"]
    recapture = [row for row in rows if str(row.get("capture_quality_status") or "") == "needs_recapture"]
    semantic_mismatch = [row for row in rows if str(row.get("capture_quality_status") or "") == "semantic_mismatch"]
    reliable_count = len(reliable)
    return {
        "reliable_samples": reliable_count,
        "normal_or_borderline": len(non_low),
        "low": len(low),
        "needs_recapture": len(recapture),
        "semantic_mismatch": len(semantic_mismatch),
        "normal_or_borderline_rate": (len(non_low) / reliable_count) if reliable_count else None,
        "score_mean": _mean(row.get("score") for row in reliable),
        "score_median": _median(row.get("score") for row in reliable),
    }


def _triage_priority(score: Optional[float], capture_quality: Dict[str, Any], error: str = "") -> str:
    if error:
        return "error"
    status = str(capture_quality.get("status") or "")
    if status == "needs_recapture":
        return "recapture"
    if score is None:
        return "error"
    if score >= 75.0:
        return "normal"
    if score >= 60.0:
        return "borderline_review"
    if status == "semantic_mismatch":
        return "semantic_mismatch"
    return "low_review"


def build_sample_advice(
    word: str,
    score: float,
    score_scale: Dict[str, Any],
    sequence_penalty: Dict[str, Any],
    query_presence: Dict[str, float],
) -> str:
    """Return a concise operator-facing next step for one web sample."""

    capture_quality = score_scale.get("capture_quality") or {}
    floor = score_scale.get("semantic_floor") or {}
    flower_guard = score_scale.get("flower_opening_guard") or {}
    left = _float_or(query_presence.get("left_hand"))
    right = _float_or(query_presence.get("right_hand"))
    core_full = _float_or(
        score_scale.get("semantic_core_query_hand_presence_full"),
        _float_or(score_scale.get("semantic_core_query_hand_presence")),
    )
    core_window = _float_or(
        score_scale.get("semantic_core_query_hand_presence_window"),
        _float_or(score_scale.get("semantic_core_query_hand_presence")),
    )
    reason = str(capture_quality.get("reason") or floor.get("reason") or "")

    if word == "花":
        if reason == "flower_core_hand_presence_low" or core_window < 0.58:
            return f"让开花手保持在画面中央，完整露出手腕和五指；当前窗口核心手覆盖 {core_window:.2f}。"
        if (
            reason in {"flower_opening_guard_failed", "opening_guard_too_weak"}
            or (bool(flower_guard.get("enabled")) and _float_or(flower_guard.get("best_score")) < 0.60)
        ):
            return f"从撮合状态开始，慢慢张开五指并保持约 0.5 秒；当前张开分数 {_float_or(flower_guard.get('best_score')):.2f}。"
        if score < 75.0:
            return f"保持手部靠近摄像头，完整覆盖撮合到张开；全段覆盖 {core_full:.2f}、窗口覆盖 {core_window:.2f}。"
        return "开花核心段可评分；继续保持手部完整入画和清晰张开动态。"

    if word == "跳":
        floor_reason = str(floor.get("reason") or "")
        if reason == "jump_two_hand_presence_low" or floor_reason == "insufficient_two_hand_presence":
            return f"左手“地面”和右手“两指小人”需要同时入画；当前左手覆盖 {left:.2f}、右手覆盖 {right:.2f}。"
        if floor_reason == "relation_direction_mismatch":
            return "右手两指需要在左手上方向上弹起，避免只做横向摆动或单手移动。"
        if floor_reason in {"relation_jump_amplitude_too_small", "weak_same_direction_vertical_jump"}:
            return "右手两指弹跳幅度偏小；请先弯曲再向上弹起，动作稍微明显一些。"
        if score < 75.0:
            return f"保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 {left:.2f}/{right:.2f}。"
        return "双手弹跳核心语义可评分；继续保持两只手同时稳定入画。"

    if str(capture_quality.get("status") or "") == "needs_recapture":
        return str(capture_quality.get("message") or "核心手部覆盖不足，请让关键手部完整入画后重采。")
    return "查看参考动作，保持关键手形、移动方向和动作起止完整入画。"


def _jump_diagnosis(score: float, score_scale: Dict[str, Any], query_presence: Dict[str, float]) -> str:
    floor = score_scale.get("semantic_floor") or {}
    capture_quality = score_scale.get("capture_quality") or {}
    reason = str(floor.get("reason") or "")
    if (
        str(capture_quality.get("reason") or "") == "phase_order_disorder"
        or str(score_scale.get("reason") or "") == "semantic_phase_order_guard"
    ):
        return "jump_phase_order_disorder"
    if score >= 60.0 or reason == "used":
        return "jump_core_accepted"
    mapping = {
        "insufficient_two_hand_presence": "jump_two_hand_presence_low",
        "required_presence_penalty_too_high": "jump_required_presence_low",
        "right_hand_geometry_too_far": "jump_right_hand_geometry_far",
        "relation_direction_mismatch": "jump_relation_direction_mismatch",
        "weak_same_direction_vertical_jump": "jump_vertical_jump_weak",
        "relation_jump_amplitude_too_small": "jump_amplitude_small",
        "relation_motion_too_horizontal": "jump_motion_too_horizontal",
        "missing_relation_delta": "jump_relation_delta_missing",
        "weak_relation_delta": "jump_relation_delta_weak",
    }
    if reason in mapping:
        return mapping[reason]
    if min(float(query_presence.get("left_hand", 0.0)), float(query_presence.get("right_hand", 0.0))) < 0.65:
        return "jump_two_hand_presence_low"
    return "jump_low_other"


def _flower_diagnosis(
    score: float,
    score_scale: Dict[str, Any],
    group_mean: Dict[str, float],
    query_presence: Dict[str, float],
) -> str:
    guard = score_scale.get("flower_opening_guard") or {}
    capture_quality = score_scale.get("capture_quality") or {}
    if (
        str(capture_quality.get("reason") or "") == "phase_order_disorder"
        or str(score_scale.get("reason") or "") == "semantic_phase_order_guard"
    ):
        return "flower_phase_order_disorder"
    if score >= 60.0:
        return "flower_core_accepted"
    if bool(guard.get("enabled")) and not bool(guard.get("passed", True)):
        return "flower_opening_guard_failed"
    if max(float(query_presence.get("left_hand", 0.0)), float(query_presence.get("right_hand", 0.0))) < 0.58:
        return "flower_core_hand_presence_low"
    if float(group_mean.get("right_hand_shape", 0.0)) > 0.30:
        return "flower_right_hand_shape_far"
    if float(group_mean.get("right_hand", 0.0)) > 0.30:
        return "flower_right_hand_motion_far"
    return "flower_low_other"


def _generic_diagnosis(score: float, score_scale: Dict[str, Any], query_presence: Dict[str, float]) -> str:
    if score >= 60.0:
        return "accepted"
    if max(float(query_presence.get("left_hand", 0.0)), float(query_presence.get("right_hand", 0.0))) < 0.50:
        return "hand_presence_low"
    return str(score_scale.get("reason") or "low_other")


def classify_diagnosis(
    word: str,
    score: float,
    score_scale: Dict[str, Any],
    group_mean: Dict[str, float],
    query_presence: Dict[str, float],
) -> str:
    if word == "跳":
        return _jump_diagnosis(score, score_scale, query_presence)
    if word == "花":
        return _flower_diagnosis(score, score_scale, group_mean, query_presence)
    return _generic_diagnosis(score, score_scale, query_presence)


def analyze_one(path: Path, semantic_profile_json: Path, template_root: Optional[Path] = None) -> Dict[str, Any]:
    stored = _load_json(path)
    request_id = str(stored.get("request_id") or path.parent.name)
    target_word = str(stored.get("target_word") or "")
    saved_standard_json = Path(stored.get("standard_json") or "")
    standard_json, standard_source = _template_path(template_root, target_word, saved_standard_json)
    query_json = Path(stored.get("query_json") or "")
    base: Dict[str, Any] = {
        "request_id": request_id,
        "generated_at": stored.get("generated_at"),
        "target_word": target_word,
        "frame_count": stored.get("frame_count"),
        "timeline_frame_count": stored.get("timeline_frame_count"),
        "capture_fps": stored.get("capture_fps"),
        "standard_json": str(standard_json),
        "saved_standard_json": str(saved_standard_json),
        "standard_source": standard_source,
        "query_json": str(query_json),
        "error": "",
    }
    try:
        standard = load_sequence(standard_json, requested_mode="landmark")
        query = load_sequence(query_json, requested_mode="landmark")
        profile = load_semantic_profile(target_word, semantic_profile_json)
        result = run_pair(standard, query, semantic_profile=profile, enable_cross_check=False)
        score = float(result["prototype_score"])
        score_scale = result.get("score_scale") or {}
        capture_quality = score_scale.get("capture_quality") or {}
        sequence_penalty = result.get("sequence_penalty") or {}
        group_mean = result.get("group_mean_distance") or {}
        query_presence = _presence_ratio(query)
        flower_guard = score_scale.get("flower_opening_guard") or {}
        flower_best = flower_guard.get("best") or {}
        semantic_floor = score_scale.get("semantic_floor") or {}
        fallback_from = semantic_floor.get("fallback_from") or {}
        two_finger_shape = semantic_floor.get("right_two_finger_shape") or {}
        row = {
            **base,
            "score": score,
            "band": _score_band(score),
            "diagnosis": classify_diagnosis(target_word, score, score_scale, group_mean, query_presence),
            "triage_priority": _triage_priority(score, capture_quality),
            "sample_advice": build_sample_advice(target_word, score, score_scale, sequence_penalty, query_presence),
            "dtw_distance": _safe_float(result.get("dtw_distance")),
            "normalized_distance": _safe_float(result.get("normalized_distance")),
            "score_distance": _safe_float(score_scale.get("score_distance")),
            "alignment_mode": (result.get("alignment_policy") or {}).get("mode"),
            "used_action_window": (result.get("action_window") or {}).get("used_for_scoring"),
            "score_scale_reason": score_scale.get("reason"),
            "capture_quality_status": capture_quality.get("status"),
            "capture_quality_reason": capture_quality.get("reason"),
            "capture_quality_message": capture_quality.get("message"),
            "capture_quality_reliable": capture_quality.get("reliable_for_scoring"),
            "semantic_core_presence": _safe_float(score_scale.get("semantic_core_query_hand_presence")),
            "semantic_core_presence_full": _safe_float(score_scale.get("semantic_core_query_hand_presence_full")),
            "semantic_core_presence_window": _safe_float(score_scale.get("semantic_core_query_hand_presence_window")),
            "semantic_core_guard_passed": score_scale.get("semantic_core_guard_passed"),
            "semantic_floor_reason": semantic_floor.get("reason"),
            "semantic_floor_source": semantic_floor.get("source"),
            "semantic_floor_score": _safe_float(score_scale.get("semantic_floor_score")),
            "semantic_floor_used": semantic_floor.get("used"),
            "semantic_floor_direction_cosine": _safe_float(semantic_floor.get("direction_cosine")),
            "semantic_floor_vertical_score": _safe_float(semantic_floor.get("vertical_score")),
            "semantic_floor_amplitude_ratio": _safe_float(semantic_floor.get("amplitude_ratio")),
            "semantic_floor_horizontal_to_vertical": _safe_float(semantic_floor.get("query_horizontal_to_vertical")),
            "semantic_floor_relation_presence": _safe_float(semantic_floor.get("relation_presence")),
            "semantic_floor_query_segment_start": semantic_floor.get("query_segment_start_frame_idx"),
            "semantic_floor_query_segment_end": semantic_floor.get("query_segment_end_frame_idx"),
            "semantic_floor_query_segment_coverage": _safe_float(semantic_floor.get("query_segment_coverage")),
            "semantic_floor_fallback_from_reason": fallback_from.get("reason"),
            "semantic_floor_fallback_from_direction_cosine": _safe_float(fallback_from.get("direction_cosine")),
            "jump_two_finger_shape_mean": _safe_float(two_finger_shape.get("mean")),
            "jump_two_finger_shape_range": _safe_float(two_finger_shape.get("range")),
            "jump_two_finger_shape_valid_count": two_finger_shape.get("valid_count"),
            "flower_opening_passed": flower_guard.get("passed"),
            "flower_opening_score": _safe_float(flower_guard.get("best_score")),
            "flower_opening_hand": flower_best.get("group"),
            "left_hand_presence": _safe_float(query_presence.get("left_hand")),
            "right_hand_presence": _safe_float(query_presence.get("right_hand")),
            "two_hand_presence": min(float(query_presence.get("left_hand", 0.0)), float(query_presence.get("right_hand", 0.0))),
            "pose_presence": _safe_float(query_presence.get("pose")),
            "face_presence": _safe_float(query_presence.get("face")),
            "presence_penalty": _safe_float(sequence_penalty.get("presence_penalty")),
            "required_presence_penalty": _safe_float(sequence_penalty.get("required_presence_penalty")),
            "semantic_delta_penalty": _safe_float(sequence_penalty.get("semantic_delta_penalty")),
            "semantic_anchor_penalty": _safe_float(sequence_penalty.get("semantic_anchor_penalty")),
            "group_left_hand": _safe_float(group_mean.get("left_hand")),
            "group_right_hand": _safe_float(group_mean.get("right_hand")),
            "group_left_hand_shape": _safe_float(group_mean.get("left_hand_shape")),
            "group_right_hand_shape": _safe_float(group_mean.get("right_hand_shape")),
            "group_two_hand_relation": _safe_float(group_mean.get("two_hand_relation")),
        }
    except Exception as exc:
        row = {
            **base,
            "score": None,
            "band": "error",
            "diagnosis": "error",
            "triage_priority": "error",
            "sample_advice": "诊断脚本复算失败；先检查保存的 query/standard Holistic JSON 是否存在且格式正确。",
            "dtw_distance": None,
            "normalized_distance": None,
            "score_distance": None,
            "alignment_mode": "",
            "used_action_window": "",
            "score_scale_reason": "",
            "capture_quality_status": "",
            "capture_quality_reason": "",
            "capture_quality_message": "",
            "capture_quality_reliable": "",
            "semantic_core_presence": None,
            "semantic_core_presence_full": None,
            "semantic_core_presence_window": None,
            "semantic_core_guard_passed": "",
            "semantic_floor_reason": "",
            "semantic_floor_source": "",
            "semantic_floor_score": None,
            "semantic_floor_used": "",
            "semantic_floor_direction_cosine": None,
            "semantic_floor_vertical_score": None,
            "semantic_floor_amplitude_ratio": None,
            "semantic_floor_horizontal_to_vertical": None,
            "semantic_floor_relation_presence": None,
            "semantic_floor_query_segment_start": None,
            "semantic_floor_query_segment_end": None,
            "semantic_floor_query_segment_coverage": None,
            "semantic_floor_fallback_from_reason": None,
            "semantic_floor_fallback_from_direction_cosine": None,
            "jump_two_finger_shape_mean": None,
            "jump_two_finger_shape_range": None,
            "jump_two_finger_shape_valid_count": None,
            "flower_opening_passed": "",
            "flower_opening_score": None,
            "flower_opening_hand": "",
            "left_hand_presence": None,
            "right_hand_presence": None,
            "two_hand_presence": None,
            "pose_presence": None,
            "face_presence": None,
            "presence_penalty": None,
            "required_presence_penalty": None,
            "semantic_delta_penalty": None,
            "semantic_anchor_penalty": None,
            "group_left_hand": None,
            "group_right_hand": None,
            "group_left_hand_shape": None,
            "group_right_hand_shape": None,
            "group_two_hand_relation": None,
            "error": str(exc),
        }
    return row


def summarize(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    by_word: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_word[str(row.get("target_word") or "unknown")].append(row)
    summary: Dict[str, Any] = {
        "samples": len(rows),
        "errors": sum(1 for row in rows if row.get("error")),
        "bands": dict(Counter(str(row.get("band") or "unknown") for row in rows)),
        "diagnoses": dict(Counter(str(row.get("diagnosis") or "unknown") for row in rows)),
        "triage_priority": dict(Counter(str(row.get("triage_priority") or "unknown") for row in rows)),
        "capture_quality": dict(Counter(str(row.get("capture_quality_status") or "unknown") for row in rows)),
        "effective": _effective_summary(rows),
        "score_mean": _mean(row.get("score") for row in rows),
        "score_median": _median(row.get("score") for row in rows),
        "by_word": {},
    }
    for word, items in sorted(by_word.items()):
        summary["by_word"][word] = {
            "samples": len(items),
            "bands": dict(Counter(str(row.get("band") or "unknown") for row in items)),
            "diagnoses": dict(Counter(str(row.get("diagnosis") or "unknown") for row in items)),
            "triage_priority": dict(Counter(str(row.get("triage_priority") or "unknown") for row in items)),
            "capture_quality": dict(Counter(str(row.get("capture_quality_status") or "unknown") for row in items)),
            "effective": _effective_summary(items),
            "score_mean": _mean(row.get("score") for row in items),
            "score_median": _median(row.get("score") for row in items),
            "score_min": _min(row.get("score") for row in items),
            "score_max": _max(row.get("score") for row in items),
            "semantic_core_presence_mean": _mean(row.get("semantic_core_presence") for row in items),
            "semantic_core_presence_full_mean": _mean(row.get("semantic_core_presence_full") for row in items),
            "semantic_core_presence_window_mean": _mean(row.get("semantic_core_presence_window") for row in items),
            "two_hand_presence_mean": _mean(row.get("two_hand_presence") for row in items),
            "left_hand_presence_mean": _mean(row.get("left_hand_presence") for row in items),
            "right_hand_presence_mean": _mean(row.get("right_hand_presence") for row in items),
        }
    return summary


def build_markdown(payload: Dict[str, Any]) -> str:
    rows = payload["rows"]
    summary = payload["summary"]
    lines: List[str] = []
    lines.append("# 网页样本语义诊断")
    lines.append("")
    lines.append(f"- 生成时间：`{payload['generated_at']}`")
    lines.append(f"- Web 样本根目录：`{payload['web_root']}`")
    lines.append(f"- 语义 profile：`{payload['semantic_profile_json']}`")
    lines.append(f"- 词条过滤：`{', '.join(payload['words']) if payload['words'] else 'ALL'}`")
    filters = payload.get("filters") or {}
    if any(filters.values()):
        lines.append(
            f"- 样本过滤：latest=`{filters.get('latest') or 0}`，"
            f"since_request_id=`{filters.get('since_request_id') or ''}`，"
            f"request_ids=`{', '.join(filters.get('request_ids') or []) or '-'}`"
        )
    if payload.get("template_root"):
        lines.append(f"- 标准库覆盖：`{payload['template_root']}`")
        lines.append("- 口径：query 复用保存的网页/API Holistic JSON，standard 改用当前标准库，模拟当前后端在线评分；不重新运行 Holistic。")
    else:
        lines.append("- 口径：复用保存的 `standard_json/query_json` 复算，不重新运行 Holistic。")
    lines.append("- 分段：`normal_like >= 75`，`60 <= borderline < 75`，`low < 60`；仍是工程诊断口径，不是正式用户阈值。")
    lines.append("")
    lines.append("## 总览")
    lines.append("")
    lines.append(f"- 样本数：`{summary['samples']}`")
    lines.append(f"- 错误数：`{summary['errors']}`")
    lines.append(f"- 均分：`{_fmt(summary['score_mean'])}`")
    lines.append(f"- 中位数：`{_fmt(summary['score_median'])}`")
    lines.append(f"- 分段计数：`{summary['bands']}`")
    lines.append(f"- 诊断计数：`{summary['diagnoses']}`")
    lines.append(f"- 处置计数：`{summary['triage_priority']}`")
    lines.append(f"- 采集质量计数：`{summary['capture_quality']}`")
    effective = summary["effective"]
    lines.append(
        f"- 有效采集口径：可评分样本 `{effective['reliable_samples']}`，"
        f"正常+边界 `{effective['normal_or_borderline']}`，低分 `{effective['low']}`，"
        f"正常+边界率 `{_fmt(effective['normal_or_borderline_rate'] * 100 if effective['normal_or_borderline_rate'] is not None else None, 1)}%`。"
    )
    lines.append("")
    lines.append("## 分词条")
    lines.append("")
    lines.append("| 词条 | 样本数 | 正常 | 边界 | 低分 | 均分 | 中位数 | 最低 | 最高 | 核心覆盖均值 | 全段/窗口覆盖 | L/R 覆盖均值 | 采集质量 | 处置 | 主要诊断 |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|")
    for word, item in summary["by_word"].items():
        bands = item["bands"]
        diagnosis_text = _top_counts(row.get("diagnosis") for row in rows if row.get("target_word") == word)
        quality_text = _top_counts(row.get("capture_quality_status") for row in rows if row.get("target_word") == word)
        triage_text = _top_counts(row.get("triage_priority") for row in rows if row.get("target_word") == word)
        lines.append(
            f"| {word} | {item['samples']} | {bands.get('normal_like', 0)} | {bands.get('borderline', 0)} | "
            f"{bands.get('low', 0)} | {_fmt(item['score_mean'])} | {_fmt(item['score_median'])} | "
            f"{_fmt(item['score_min'])} | {_fmt(item['score_max'])} | {_fmt(item['semantic_core_presence_mean'])} | "
            f"{_fmt(item['semantic_core_presence_full_mean'])}/{_fmt(item['semantic_core_presence_window_mean'])} | "
            f"{_fmt(item['left_hand_presence_mean'])}/{_fmt(item['right_hand_presence_mean'])} | "
            f"{quality_text} | {triage_text} | {diagnosis_text} |"
        )
    lines.append("")
    lines.append("## 有效采集口径")
    lines.append("")
    lines.append("- 这里排除 `needs_recapture`，只看核心关键点已经足够入画、可以解释为动作语义评分的样本。")
    lines.append("")
    lines.append("| 词条 | 原始样本 | 建议重采 | 有效采集 | 正常+边界 | 低分 | 正常+边界率 | 有效均分 | 语义不匹配 |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for word, item in summary["by_word"].items():
        eff = item["effective"]
        lines.append(
            f"| {word} | {item['samples']} | {eff['needs_recapture']} | {eff['reliable_samples']} | "
            f"{eff['normal_or_borderline']} | {eff['low']} | "
            f"{_fmt(eff['normal_or_borderline_rate'] * 100 if eff['normal_or_borderline_rate'] is not None else None, 1)}% | "
            f"{_fmt(eff['score_mean'])} | {eff['semantic_mismatch']} |"
        )
    lines.append("")
    mismatch_rows = [row for row in rows if str(row.get("capture_quality_status") or "") == "semantic_mismatch"]
    if mismatch_rows:
        lines.append("## 语义不匹配明细")
        lines.append("")
        lines.append("- 这些样本核心关键点已足够入画，但未满足词条核心语义；通常不应通过放宽阈值抬高。")
        lines.append("")
        lines.append("| request | 词条 | 分数 | 诊断 | floor 原因 | 方向余弦 | 纵向分数 | 幅度比 | 水平/纵向 | 关系覆盖 | 建议 |")
        lines.append("|---|---|---:|---|---|---:|---:|---:|---:|---:|---|")
        for row in sorted(mismatch_rows, key=lambda item: (str(item.get("target_word") or ""), float(item.get("score") or 0.0))):
            lines.append(
                f"| {row['request_id']} | {row['target_word']} | {_fmt(row.get('score'))} | {row.get('diagnosis')} | "
                f"{row.get('semantic_floor_reason') or '-'} | {_fmt(row.get('semantic_floor_direction_cosine'))} | "
                f"{_fmt(row.get('semantic_floor_vertical_score'))} | {_fmt(row.get('semantic_floor_amplitude_ratio'))} | "
                f"{_fmt(row.get('semantic_floor_horizontal_to_vertical'))} | {_fmt(row.get('semantic_floor_relation_presence'))} | "
                f"{row.get('sample_advice') or '-'} |"
            )
        lines.append("")
    jump_floor_rows = [
        row
        for row in rows
        if row.get("target_word") == "跳" and str(row.get("semantic_floor_used") or "") == "True"
    ]
    if jump_floor_rows:
        source_counts = Counter(str(row.get("semantic_floor_source") or "unknown") for row in jump_floor_rows)
        lines.append("## 跳语义 floor 接收明细")
        lines.append("")
        lines.append("- `action_window_net` 表示动作窗口起止净方向直接通过；`full_sequence_local_relation_segment` 表示完整序列中检测到局部双手弹跳段，并通过右手食指/中指手形守卫。")
        lines.append(f"- 来源分布：`{dict(source_counts)}`")
        lines.append("")
        lines.append("| request | 分数 | 分段 | 来源 | 方向余弦 | 幅度比 | 水平/纵向 | 段覆盖 | 段帧 | 两指手形 | fallback 原因 |")
        lines.append("|---|---:|---|---|---:|---:|---:|---:|---|---:|---|")
        for row in sorted(jump_floor_rows, key=lambda item: (str(item.get("semantic_floor_source") or ""), float(item.get("score") or 0.0))):
            segment = "-"
            if row.get("semantic_floor_query_segment_start") is not None or row.get("semantic_floor_query_segment_end") is not None:
                segment = f"{row.get('semantic_floor_query_segment_start')}-{row.get('semantic_floor_query_segment_end')}"
            lines.append(
                f"| {row['request_id']} | {_fmt(row.get('score'))} | {row.get('band')} | "
                f"{row.get('semantic_floor_source') or '-'} | {_fmt(row.get('semantic_floor_direction_cosine'))} | "
                f"{_fmt(row.get('semantic_floor_amplitude_ratio'))} | {_fmt(row.get('semantic_floor_horizontal_to_vertical'))} | "
                f"{_fmt(row.get('semantic_floor_query_segment_coverage'))} | {segment} | "
                f"{_fmt(row.get('jump_two_finger_shape_mean'))} | {row.get('semantic_floor_fallback_from_reason') or '-'} |"
            )
        lines.append("")
    lines.append("## 低分原因")
    lines.append("")
    by_word: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("band") == "low":
            by_word[str(row.get("target_word") or "unknown")].append(row)
    if not by_word:
        lines.append("- 无低分样本。")
    for word, items in sorted(by_word.items()):
        lines.append(f"### {word}")
        lines.append("")
        lines.append(f"- 低分数：`{len(items)}`")
        lines.append(f"- 诊断分布：`{dict(Counter(str(row.get('diagnosis') or 'unknown') for row in items))}`")
        lines.append("")
        lines.append("| request | 分数 | 采集质量 | 处置 | 诊断 | floor 原因 | L/R 覆盖 | 核心全段/窗口 | 花-张开 | 双手关系 | 右手形 | 建议 |")
        lines.append("|---|---:|---|---|---|---|---:|---:|---:|---:|---:|---|")
        for row in sorted(items, key=lambda item: float(item.get("score") or 0.0))[:20]:
            lines.append(
                f"| {row['request_id']} | {_fmt(row.get('score'))} | {row.get('capture_quality_status') or '-'} | "
                f"{row.get('triage_priority') or '-'} | {row.get('diagnosis')} | "
                f"{row.get('semantic_floor_reason') or '-'} | {_fmt(row.get('left_hand_presence'))}/"
                f"{_fmt(row.get('right_hand_presence'))} | {_fmt(row.get('semantic_core_presence_full'))}/"
                f"{_fmt(row.get('semantic_core_presence_window'))} | {_fmt(row.get('flower_opening_score'))} | "
                f"{_fmt(row.get('group_two_hand_relation'))} | {_fmt(row.get('group_right_hand_shape'))} | "
                f"{row.get('sample_advice') or '-'} |"
            )
        lines.append("")
    lines.append("## 最新样本")
    lines.append("")
    lines.append("| request | 词条 | 帧数 | 分数 | 分段 | 处置 | 采集质量 | 诊断 | L/R 覆盖 | 核心全段/窗口 | 对齐 | 建议 |")
    lines.append("|---|---|---:|---:|---|---|---|---|---:|---:|---|---|")
    for row in rows[-30:]:
        lines.append(
            f"| {row['request_id']} | {row['target_word']} | {row.get('frame_count')} | {_fmt(row.get('score'))} | "
            f"{row.get('band')} | {row.get('triage_priority') or '-'} | {row.get('capture_quality_status') or '-'} | "
            f"{row.get('diagnosis')} | {_fmt(row.get('left_hand_presence'))}/{_fmt(row.get('right_hand_presence'))} | "
            f"{_fmt(row.get('semantic_core_presence_full'))}/{_fmt(row.get('semantic_core_presence_window'))} | "
            f"{row.get('alignment_mode')} | {row.get('sample_advice') or '-'} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_outputs(
    rows: Sequence[Dict[str, Any]],
    output_dir: Path,
    web_root: Path,
    semantic_profile_json: Path,
    words: Sequence[str],
    template_root: Optional[Path] = None,
    filters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "web_root": str(web_root),
        "semantic_profile_json": str(semantic_profile_json),
        "words": list(words),
        "template_root": str(template_root) if template_root is not None else "",
        "filters": filters or {},
        "summary": summarize(rows),
        "rows": list(rows),
    }
    json_path = output_dir / "web_semantic_diagnostics.json"
    md_path = output_dir / "web_semantic_diagnostics.md"
    csv_path = output_dir / "web_semantic_diagnostics.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(build_markdown(payload), encoding="utf-8")
    fields = list(rows[0].keys()) if rows else []
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    payload["json_path"] = str(json_path)
    payload["md_path"] = str(md_path)
    payload["csv_path"] = str(csv_path)
    return payload


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="分析已保存网页样本的语义打分诊断")
    parser.add_argument("--web-root", default=str(DEFAULT_WEB_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--words", nargs="*", default=[], help="只分析指定词条，例如：--words 花 跳")
    parser.add_argument(
        "--template-root",
        default="",
        help="可选：用指定标准库替换历史 scoring_result.json 里的 standard_json，模拟当前后端评分。",
    )
    parser.add_argument("--latest", type=int, default=0, help="只分析筛选后的最近 N 条样本。")
    parser.add_argument("--since-request-id", default="", help="只分析 request_id 字典序大于该值的样本。")
    parser.add_argument("--request-ids", nargs="*", default=[], help="只分析指定 request_id。")
    args = parser.parse_args(argv)

    web_root = Path(args.web_root)
    semantic_profile_json = Path(args.semantic_profile_json)
    template_root = Path(args.template_root) if args.template_root else None
    words = [str(item) for item in args.words]
    word_set = set(words)
    paths = []
    for path in _iter_result_paths(web_root):
        stored = _load_json(path)
        target_word = str(stored.get("target_word") or "")
        if word_set and target_word not in word_set:
            continue
        paths.append(path)
    paths = filter_result_paths(
        paths,
        request_ids=args.request_ids,
        since_request_id=args.since_request_id,
        latest=args.latest,
    )
    filters = {"latest": args.latest, "since_request_id": args.since_request_id, "request_ids": list(args.request_ids)}
    rows = []
    for path in paths:
        rows.append(analyze_one(path, semantic_profile_json, template_root=template_root))
    payload = write_outputs(rows, Path(args.output_dir), web_root, semantic_profile_json, words, template_root=template_root, filters=filters)
    print(f"已生成语义诊断 JSON：{payload['json_path']}")
    print(f"已生成语义诊断报告：{payload['md_path']}")
    print(f"已生成语义诊断 CSV：{payload['csv_path']}")
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

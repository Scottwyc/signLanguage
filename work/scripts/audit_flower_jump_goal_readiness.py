#!/usr/bin/env python3
"""Audit whether the flower/jump web-scoring goal is ready to close.

This is intentionally a fast evidence audit. It does not run Holistic and does
not rerun DTW gates unless the caller has already generated reports. It checks
the current runtime, watcher/marker state, the latest combined quality gate,
and whether there is a fresh real webcam-sample diagnosis after the current
marker. The last item is the current completion blocker.
"""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


REPO_ROOT = Path("/data/WYC/signLanguage")
DEFAULT_OUTPUT_BASE = REPO_ROOT / "work/generated/scoring_mvp_run3"
DEFAULT_WEB_ROOT = REPO_ROOT / "work/generated/web_scoring_mvp"
DEFAULT_BACKEND_URL = "http://127.0.0.1:5080"
DEFAULT_WATCH_STATUS_URL = "http://127.0.0.1:5080/static/watch_status.json"
DEFAULT_REQUIRED_WORDS = ["花", "跳"]


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _http_json(url: str, timeout_sec: float = 3.0) -> Dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout_sec) as response:
            return {"ok": True, "url": url, "payload": json.loads(response.read().decode("utf-8")), "error": ""}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"ok": False, "url": url, "payload": {}, "error": str(exc)}


def _file_json(path: str) -> Dict[str, Any]:
    try:
        return {"ok": True, "url": str(path), "payload": _load_json(Path(path)), "error": ""}
    except Exception as exc:  # noqa: BLE001 - evidence audit should report read failures.
        return {"ok": False, "url": str(path), "payload": {}, "error": str(exc)}


def _find_latest_quality_gate(base: Path) -> Optional[Path]:
    candidates = sorted(base.glob("flower_jump_quality_gate_*/flower_jump_quality_gate.json"))
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _fmt_bool(value: bool) -> str:
    return "PASS" if value else "MISSING"


def _fmt_num(value: Any, digits: int = 3) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "-"


def _gate(name: str, passed: bool, detail: str) -> Dict[str, Any]:
    return {"name": name, "passed": bool(passed), "detail": detail}


def _returncode_ok(value: Any) -> bool:
    if value is None:
        return False
    try:
        return int(value) == 0
    except (TypeError, ValueError):
        return False


def _diagnosis_scope_matches_current_marker(
    diagnosed_request_ids: Sequence[str],
    target_request_ids: Sequence[str],
    current_marker_id: str,
) -> Dict[str, Any]:
    diagnosed = [str(item) for item in diagnosed_request_ids if str(item)]
    current_targets = [str(item) for item in target_request_ids if str(item)]
    if not diagnosed:
        return {
            "passed": False,
            "mode": "missing_diagnosis_ids",
            "diagnosed_request_ids": [],
            "target_request_ids": current_targets,
            "current_marker_id": current_marker_id,
        }

    diagnosed_set = set(diagnosed)
    target_set = set(current_targets)
    if target_set:
        passed = diagnosed_set == target_set
        mode = "marker_after_target_set"
    else:
        latest_diagnosed_id = max(diagnosed)
        passed = bool(current_marker_id) and latest_diagnosed_id == current_marker_id
        mode = "marker_updated_to_latest_diagnosis"

    return {
        "passed": bool(passed),
        "mode": mode,
        "diagnosed_request_ids": diagnosed,
        "target_request_ids": current_targets,
        "current_marker_id": current_marker_id,
        "latest_diagnosed_id": max(diagnosed),
    }


def _browser_capture_evidence(
    web_root: Path,
    request_ids: Sequence[str],
    *,
    allow_legacy_browser_evidence: bool = False,
) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for request_id in request_ids:
        path = web_root / str(request_id) / "scoring_result.json"
        row: Dict[str, Any] = {
            "request_id": str(request_id),
            "path": str(path),
            "exists": path.exists(),
            "passed": False,
            "reason": "",
        }
        if not path.exists():
            row["reason"] = "missing_scoring_result"
            rows.append(row)
            continue
        try:
            stored = _load_json(path)
        except Exception as exc:  # noqa: BLE001 - evidence audit should report read failures.
            row["reason"] = f"read_error:{exc}"
            rows.append(row)
            continue

        client_source = str(stored.get("client_source") or (stored.get("client") or {}).get("source") or "")
        worker_mode = str((stored.get("worker") or {}).get("input_mode") or "")
        target_word = str(stored.get("target_word") or "")
        frame_count = int(stored.get("frame_count") or 0)
        timeline_count = int(stored.get("timeline_frame_count") or 0)
        duration_sec = float(stored.get("duration_sec") or 0.0)
        capture_fps = float(stored.get("capture_fps") or 0.0)
        frame_weights = stored.get("frame_weights")
        has_weights = isinstance(frame_weights, list) and len(frame_weights) == frame_count and frame_count > 0
        nonuniform_weights = False
        if has_weights:
            try:
                nonuniform_weights = (max(float(x) for x in frame_weights) - min(float(x) for x in frame_weights)) > 1e-6
            except (TypeError, ValueError):
                nonuniform_weights = False
        frame_indices = stored.get("frame_indices")
        has_indices = isinstance(frame_indices, list) and len(frame_indices) == frame_count and frame_count > 0
        min_required_frames = 12 if target_word == "花" else 6 if target_word == "跳" else 10
        explicit_source_ok = client_source in {"browser_camera", "web_frontend_camera"}
        weighted_source_ok = has_weights and nonuniform_weights
        strong_source_ok = explicit_source_ok or weighted_source_ok
        # The live 5080 backend may still be an older process that ignores the
        # frontend's client_source/frame_weights fields. Keep a weaker but
        # explicit compatibility path for diagnostics, but do not let it close
        # the final completion gate unless explicitly requested.
        legacy_source_ok = (
            not client_source
            and not has_weights
            and has_indices
            and timeline_count > frame_count
            and capture_fps > 0.0
        )
        common_ok = (
            target_word in {"花", "跳"}
            and worker_mode == "frame_slices"
            and frame_count >= min_required_frames
            and timeline_count >= frame_count
            and duration_sec > 0.0
            and has_indices
        )
        completion_source_ok = strong_source_ok or (allow_legacy_browser_evidence and legacy_source_ok)
        diagnostic_compatible = common_ok and legacy_source_ok
        capture_like = common_ok and completion_source_ok
        if capture_like:
            if explicit_source_ok:
                evidence_level = "strong_client_source"
            elif weighted_source_ok:
                evidence_level = "strong_nonuniform_frame_weights"
            else:
                evidence_level = "legacy_frame_slice_metadata"
            reason = evidence_level
        elif diagnostic_compatible:
            evidence_level = "legacy_frame_slice_metadata"
            reason = "legacy_frame_slice_metadata_not_completion_evidence"
        else:
            missing_reasons = []
            if target_word not in {"花", "跳"}:
                missing_reasons.append("target_not_flower_jump")
            if worker_mode != "frame_slices":
                missing_reasons.append("worker_not_frame_slices")
            if frame_count < min_required_frames:
                missing_reasons.append("frame_count_below_recommended")
            if timeline_count < frame_count:
                missing_reasons.append("timeline_lt_frame_count")
            if duration_sec <= 0.0:
                missing_reasons.append("duration_missing")
            if not has_indices:
                missing_reasons.append("frame_indices_missing")
            if legacy_source_ok and not allow_legacy_browser_evidence:
                missing_reasons.append("strong_source_metadata_missing")
            elif not (strong_source_ok or legacy_source_ok):
                missing_reasons.append("source_metadata_missing")
            evidence_level = "none"
            reason = ",".join(missing_reasons) or "not_browser_capture_like"
        row.update(
            {
                "target_word": target_word,
                "client_source": client_source,
                "worker_mode": worker_mode,
                "frame_count": frame_count,
                "min_required_frames": min_required_frames,
                "timeline_frame_count": timeline_count,
                "duration_sec": duration_sec,
                "capture_fps": capture_fps,
                "has_frame_weights": has_weights,
                "nonuniform_frame_weights": nonuniform_weights,
                "has_frame_indices": has_indices,
                "explicit_source_ok": explicit_source_ok,
                "weighted_source_ok": weighted_source_ok,
                "legacy_source_ok": legacy_source_ok,
                "diagnostic_compatible": diagnostic_compatible,
                "completion_source_ok": completion_source_ok,
                "evidence_level": evidence_level,
                "passed": capture_like,
                "reason": reason,
            }
        )
        rows.append(row)
    observed_words = sorted(
        {
            str(row.get("target_word") or "")
            for row in rows
            if row.get("passed") and str(row.get("target_word") or "") in set(DEFAULT_REQUIRED_WORDS)
        }
    )
    missing_required_words = [word for word in DEFAULT_REQUIRED_WORDS if word not in set(observed_words)]
    sample_evidence_passed = bool(rows) and all(bool(row.get("passed")) for row in rows)
    required_words_covered = not missing_required_words
    return {
        "request_ids": [str(item) for item in request_ids],
        "passed": sample_evidence_passed and required_words_covered,
        "sample_evidence_passed": sample_evidence_passed,
        "allow_legacy_browser_evidence": allow_legacy_browser_evidence,
        "required_words": list(DEFAULT_REQUIRED_WORDS),
        "observed_words": observed_words,
        "required_words_covered": required_words_covered,
        "missing_required_words": missing_required_words,
        "rows": rows,
    }


def _build_gates(
    backend_status: Dict[str, Any],
    watch_status: Dict[str, Any],
    marker_status: Dict[str, Any],
    quality_gate_path: Optional[Path],
    quality_payload: Dict[str, Any],
    browser_evidence: Dict[str, Any],
) -> List[Dict[str, Any]]:
    backend_payload = backend_status.get("payload") or {}
    worker = backend_payload.get("worker") or {}
    scoring = backend_payload.get("scoring_module") or {}
    worker_ready = bool(backend_status.get("ok")) and worker.get("status") == "ready" and scoring.get("last_reload_error") is None

    watch_payload = watch_status.get("payload") or {}
    watcher_pid = watch_payload.get("watcher_pid")
    watcher_online = bool(watch_status.get("ok")) and bool(watcher_pid) and bool(watch_payload.get("generated_at"))

    marker_payload = marker_status.get("payload") or {}
    new_summary = marker_payload.get("new_summary") or {}
    target_summary = marker_payload.get("target_summary") or {}
    marker_ok = int(marker_status.get("returncode") or 0) == 0 and marker_payload.get("marker_last_request_id")

    quality_ok = bool(quality_gate_path and quality_gate_path.exists() and quality_payload.get("passed"))
    subgates = quality_payload.get("subgates") or []
    all_quality_subgates = bool(subgates) and all(bool(item.get("passed")) for item in subgates)

    latest_diagnosis = watch_payload.get("latest_diagnosis") or {}
    latest_regression_ok = False
    latest_visual_ok = False
    latest_confusion_ok = False
    if latest_diagnosis:
        latest_regression_ok = _returncode_ok(latest_diagnosis.get("regression_returncode"))
        latest_visual_ok = _returncode_ok(latest_diagnosis.get("visual_returncode"))
        latest_confusion_ok = _returncode_ok(latest_diagnosis.get("confusion_returncode"))

    # A current final proof needs a fresh real target sample diagnosis. If the
    # watcher has no latest diagnosis and the marker-after target count is 0,
    # the engineering gates are ready but final real-webcam completion is not.
    target_new_count = int(target_summary.get("count") or 0)
    current_marker_id = str(
        marker_payload.get("marker_last_request_id")
        or watch_payload.get("status", {}).get("marker_last_request_id")
        or ""
    )
    target_request_ids = [str(item) for item in (watch_payload.get("status", {}).get("target_request_ids") or [])]
    diagnosed_request_ids = [str(item) for item in (latest_diagnosis.get("diagnosed_request_ids") or [])]
    diagnosis_scope = _diagnosis_scope_matches_current_marker(
        diagnosed_request_ids,
        target_request_ids,
        current_marker_id,
    )
    fresh_target_evidence = bool(
        latest_diagnosis
        and latest_regression_ok
        and latest_confusion_ok
        and latest_visual_ok
        and diagnosis_scope.get("passed")
        and browser_evidence.get("passed")
    )

    return [
        _gate(
            "backend_ready",
            worker_ready,
            f"worker={worker.get('status') or '-'}, pid={(worker.get('ready_payload') or {}).get('pid')}, "
            f"reload_count={scoring.get('reload_count')}, last_reload_error={scoring.get('last_reload_error')}",
        ),
        _gate(
            "watcher_online",
            watcher_online,
            f"event={watch_payload.get('event') or '-'}, watcher_pid={watcher_pid or '-'}, generated_at={watch_payload.get('generated_at') or '-'}",
        ),
        _gate(
            "marker_available",
            bool(marker_ok),
            f"last_request_id={marker_payload.get('marker_last_request_id') or '-'}, marker_after_new={new_summary.get('count')}, target_new={target_new_count}",
        ),
        _gate(
            "combined_quality_gate_passed",
            quality_ok and all_quality_subgates,
            f"quality_gate={quality_gate_path or '-'}, subgates={[(item.get('name'), item.get('passed')) for item in subgates]}",
        ),
        _gate(
            "fresh_real_webcam_target_samples_diagnosed",
            fresh_target_evidence,
            f"marker_after_target_count={target_new_count}, latest_diagnosis={latest_diagnosis or '-'}, "
            f"diagnosis_scope={diagnosis_scope}, browser_capture_evidence={browser_evidence}",
        ),
    ]


def _build_readiness_summary(gates: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    by_name = {str(gate.get("name")): bool(gate.get("passed")) for gate in gates}
    runtime_gates = ["backend_ready", "watcher_online", "marker_available"]
    algorithm_gates = ["combined_quality_gate_passed"]
    real_sample_gates = ["fresh_real_webcam_target_samples_diagnosed"]
    runtime_ready = all(by_name.get(name, False) for name in runtime_gates)
    algorithm_ready = all(by_name.get(name, False) for name in algorithm_gates)
    real_sample_ready = all(by_name.get(name, False) for name in real_sample_gates)
    missing_runtime = [name for name in runtime_gates if not by_name.get(name, False)]
    missing_algorithm = [name for name in algorithm_gates if not by_name.get(name, False)]
    missing_real_sample = [name for name in real_sample_gates if not by_name.get(name, False)]
    if runtime_ready and algorithm_ready and not real_sample_ready:
        status_explanation = "算法质量门和运行态已就绪，仍缺 marker 后真实网页摄像头花/跳样本诊断。"
        completion_blocker = "fresh_real_webcam_target_samples_diagnosed"
    elif not runtime_ready:
        status_explanation = "运行态证据未就绪，需要先恢复后端、watcher 或 marker。"
        completion_blocker = ",".join(missing_runtime)
    elif not algorithm_ready:
        status_explanation = "算法质量门未通过，需要先复查综合质量门。"
        completion_blocker = ",".join(missing_algorithm)
    elif real_sample_ready:
        status_explanation = "运行态、算法质量门和真实网页复测证据均已就绪。"
        completion_blocker = ""
    else:
        status_explanation = "仍有完成证据缺失。"
        completion_blocker = ",".join(missing_real_sample)
    return {
        "runtime_ready": runtime_ready,
        "algorithm_ready": algorithm_ready,
        "real_sample_ready": real_sample_ready,
        "ready_to_complete": runtime_ready and algorithm_ready and real_sample_ready,
        "runtime_gates": runtime_gates,
        "algorithm_gates": algorithm_gates,
        "real_sample_gates": real_sample_gates,
        "missing_runtime_gates": missing_runtime,
        "missing_algorithm_gates": missing_algorithm,
        "missing_real_sample_gates": missing_real_sample,
        "completion_blocker": completion_blocker,
        "status_explanation": status_explanation,
    }


def _build_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# 花/跳网页评分目标完成度审计")
    lines.append("")
    lines.append(f"- 生成时间：`{payload['generated_at']}`")
    lines.append(f"- 目标完成状态：`{'READY_TO_COMPLETE' if payload['ready_to_complete'] else 'NOT_READY'}`")
    summary = payload.get("readiness_summary") or {}
    if summary:
        lines.append(f"- 分层状态：运行态 `{'PASS' if summary.get('runtime_ready') else 'MISSING'}`；算法质量 `{'PASS' if summary.get('algorithm_ready') else 'MISSING'}`；真实复测 `{'PASS' if summary.get('real_sample_ready') else 'MISSING'}`。")
        lines.append(f"- 当前阻塞：`{summary.get('completion_blocker') or '-'}`")
        lines.append(f"- 状态说明：{summary.get('status_explanation') or '-'}")
    lines.append("- 口径：快速审计，不重新运行 Holistic，不重跑 DTW gate；读取当前运行态和最新质量门报告。")
    lines.append("")
    if summary:
        lines.append("## 分层就绪状态")
        lines.append("")
        lines.append("| 层级 | 状态 | 相关证据门 | 缺失项 |")
        lines.append("|---|---|---|---|")
        lines.append(
            f"| 运行态 | {'PASS' if summary.get('runtime_ready') else 'MISSING'} | "
            f"`{', '.join(summary.get('runtime_gates') or [])}` | "
            f"`{', '.join(summary.get('missing_runtime_gates') or []) or '-'}` |"
        )
        lines.append(
            f"| 算法质量 | {'PASS' if summary.get('algorithm_ready') else 'MISSING'} | "
            f"`{', '.join(summary.get('algorithm_gates') or [])}` | "
            f"`{', '.join(summary.get('missing_algorithm_gates') or []) or '-'}` |"
        )
        lines.append(
            f"| 真实网页复测 | {'PASS' if summary.get('real_sample_ready') else 'MISSING'} | "
            f"`{', '.join(summary.get('real_sample_gates') or [])}` | "
            f"`{', '.join(summary.get('missing_real_sample_gates') or []) or '-'}` |"
        )
        lines.append("")
    lines.append("## 证据门")
    lines.append("")
    lines.append("| gate | 状态 | 说明 |")
    lines.append("|---|---|---|")
    for gate in payload["gates"]:
        lines.append(f"| {gate['name']} | {_fmt_bool(gate['passed'])} | {gate['detail']} |")
    lines.append("")

    quality = payload.get("quality_summary") or {}
    if quality:
        lines.append("## 最新质量门摘要")
        lines.append("")
        lines.append(f"- 报告：`{payload.get('quality_gate_md') or quality.get('md_path') or '-'}`")
        lines.append(f"- 综合状态：`{'PASS' if quality.get('passed') else 'FAIL'}`")
        subgates = quality.get("subgates") or []
        if subgates:
            lines.append(
                "- 子门："
                + "，".join(
                    f"`{item.get('name')}`={'PASS' if item.get('passed') else 'FAIL'}"
                    for item in subgates
                )
                + "。"
            )
        web = quality.get("web_summary") or {}
        rate = web.get("effective_rate")
        try:
            rate_text = f"{float(rate) * 100:.1f}%"
        except (TypeError, ValueError):
            rate_text = "-"
        lines.append(
            f"- 网页回归：replay `{web.get('samples')}` / diagnostics `{web.get('diagnostics_samples')}`，"
            f"有效 `{web.get('effective_reliable')}`，正常+边界 `{web.get('effective_normal_or_borderline')}`，"
            f"有效低分 `{web.get('effective_low')}`，有效率 `{rate_text}`。"
        )
        confusion = quality.get("confusion_summary") or {}
        if confusion:
            lines.append(
                f"- 交叉混淆：samples `{confusion.get('samples')}`，eligible `{confusion.get('eligible')}`，"
                f"pass `{confusion.get('pass')}`，fail `{confusion.get('fail')}`。"
            )
            for word, row in (confusion.get("by_word") or {}).items():
                lines.append(
                    f"- 交叉混淆 `{word}`：other_score_max `{_fmt_num(row.get('other_score_max'))}`，"
                    f"margin_min `{_fmt_num(row.get('margin_min'))}`。"
                )
        disc = quality.get("discrimination_summary") or {}
        pose = quality.get("pose_summary") or {}
        frame = quality.get("frame_summary") or {}
        missing_mask = quality.get("missing_mask_summary") or {}
        temporal_padding = quality.get("temporal_padding_summary") or {}
        phase_order = quality.get("phase_order_summary") or {}
        for row in disc.get("rows") or []:
            lines.append(
                f"- 负例判别 `{row.get('word')}`：min_positive `{_fmt_num(row.get('min_positive_score'))}`，"
                f"max_negative `{_fmt_num(row.get('max_negative_score'))}`，margin `{_fmt_num(row.get('margin'))}`。"
            )
        for row in pose.get("rows") or []:
            lines.append(
                f"- 坐姿扰动 `{row.get('word')}`：min `{_fmt_num(row.get('min_observed_score'))}`，"
                f"weakest `{row.get('weakest_variant')}`。"
            )
        for row in frame.get("rows") or []:
            lines.append(
                f"- 帧数采样 `{row.get('word')}`：min_valid_frames `{row.get('min_valid_frames')}`，"
                f"min `{_fmt_num(row.get('min_observed_score'))}`，weakest `{row.get('weakest_variant') or '-'}`。"
            )
        for row in missing_mask.get("rows") or []:
            lines.append(
                f"- 缺失/mask `{row.get('word')}`：positive_min `{_fmt_num(row.get('weakest_positive_score'))}`，"
                f"critical_missing_max `{_fmt_num(row.get('strongest_negative_score'))}`。"
            )
        for row in temporal_padding.get("rows") or []:
            lines.append(
                f"- 静止 padding `{row.get('word')}`：positive_min `{_fmt_num(row.get('weakest_positive_score'))}`，"
                f"static_max `{_fmt_num(row.get('strongest_negative_score'))}`。"
            )
        for row in phase_order.get("rows") or []:
            lines.append(
                f"- 相位顺序 `{row.get('word')}`：positive_min `{_fmt_num(row.get('weakest_positive_score'))}`，"
                f"disordered_max `{_fmt_num(row.get('strongest_negative_score'))}`。"
            )
        lines.append("")

    marker_payload = (payload.get("marker_status") or {}).get("payload") or {}
    if marker_payload:
        lines.append("## 当前 marker")
        lines.append("")
        lines.append(f"- last_request_id：`{marker_payload.get('marker_last_request_id')}`")
        lines.append(f"- marker 后新增样本：`{(marker_payload.get('new_summary') or {}).get('count')}`")
        lines.append(f"- marker 后新增花/跳样本：`{(marker_payload.get('target_summary') or {}).get('count')}`")
        lines.append("")

    browser_evidence = payload.get("browser_capture_evidence") or {}
    if browser_evidence:
        lines.append("## 真实网页采集证据")
        lines.append("")
        lines.append(f"- 综合状态：`{'PASS' if browser_evidence.get('passed') else 'MISSING'}`")
        lines.append(f"- 样本证据状态：`{'PASS' if browser_evidence.get('sample_evidence_passed') else 'MISSING'}`")
        lines.append(f"- 要求覆盖词条：`{', '.join(browser_evidence.get('required_words') or [])}`")
        lines.append(f"- 已覆盖词条：`{', '.join(browser_evidence.get('observed_words') or []) or '-'}`")
        lines.append(f"- 缺失词条：`{', '.join(browser_evidence.get('missing_required_words') or []) or '-'}`")
        rows = browser_evidence.get("rows") or []
        if rows:
            lines.append("")
            lines.append("| request | 词条 | 状态 | 证据等级 | 原因 | source | 帧数 | 权重 | fps | duration |")
            lines.append("|---|---|---|---|---|---|---:|---|---:|---:|")
            for row in rows:
                weight_label = "nonuniform" if row.get("nonuniform_frame_weights") else ("present" if row.get("has_frame_weights") else "-")
                lines.append(
                    f"| {row.get('request_id') or '-'} | {row.get('target_word') or '-'} | "
                    f"{'PASS' if row.get('passed') else 'MISSING'} | {row.get('evidence_level') or '-'} | "
                    f"{row.get('reason') or '-'} | "
                    f"{row.get('client_source') or '-'} | {row.get('frame_count') or 0} | "
                    f"{weight_label} | {_fmt_num(row.get('capture_fps'), 2)} | {_fmt_num(row.get('duration_sec'), 2)} |"
                )
            if any(str(row.get("evidence_level") or "").startswith("legacy_") for row in rows):
                lines.append("")
                if browser_evidence.get("allow_legacy_browser_evidence"):
                    lines.append(
                        "- 注：本次显式允许 `legacy_frame_slice_metadata` 作为完成证据；该模式仅用于旧后端兼容复核，"
                        "正式 live 复测应优先使用 `client_source=browser_camera` 或非均匀 `frame_weights` strong 证据。"
                    )
                else:
                    lines.append(
                        "- 注：`legacy_frame_slice_metadata` 只作为诊断兼容信息展示，默认不能关闭最终完成门；"
                        "正式 live 复测必须提供 `client_source=browser_camera` 或非均匀 `frame_weights` strong 证据。"
                    )
        else:
            lines.append("- 当前没有 latest diagnosis request_id 可用于判定真实网页采集来源。")
        lines.append("")

    lines.append("## 结论")
    lines.append("")
    if payload["ready_to_complete"]:
        lines.append("- 当前证据满足目标完成审计，可以进入人工最终确认和 goal completion。")
    else:
        if summary.get("runtime_ready") and summary.get("algorithm_ready") and not summary.get("real_sample_ready"):
            lines.append("- 当前运行态和算法质量门已经通过，但还没有新的真实网页摄像头 `花/跳` 样本诊断证据。")
        else:
            lines.append(f"- 当前仍未满足完成审计：{summary.get('status_explanation') or '仍有完成证据缺失。'}")
        lines.append("- 下一步仍需用户通过 5080 页面实际采集 `花/跳`，由 watcher 自动生成增量回归和骨架可视化后再复查。")
    return "\n".join(lines) + "\n"


def _load_marker_status() -> Dict[str, Any]:
    import subprocess
    import sys

    cmd = [sys.executable, str(REPO_ROOT / "work/scripts/manage_web_sample_marker.py"), "status"]
    completed = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    result: Dict[str, Any] = {
        "command": cmd,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    if completed.returncode == 0:
        try:
            result["payload"] = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            result["parse_error"] = str(exc)
    return result


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Audit flower/jump goal readiness.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_goal_readiness_audit_current"))
    parser.add_argument("--quality-gate-json", default="", help="Optional explicit combined quality gate JSON.")
    parser.add_argument("--web-root", default=str(DEFAULT_WEB_ROOT), help="Saved web scoring sample root for browser-capture evidence audit.")
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--watch-status-url", default=DEFAULT_WATCH_STATUS_URL)
    parser.add_argument("--watch-status-json", default="", help="Prefer this local watcher status JSON over --watch-status-url.")
    parser.add_argument("--status-timeout-sec", type=float, default=3.0)
    parser.add_argument(
        "--allow-legacy-browser-evidence",
        action="store_true",
        help=(
            "Allow old frame-slice-only samples without client_source/frame_weights to close the final evidence gate. "
            "Use only for historical compatibility audits, not formal live completion."
        ),
    )
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    quality_path = Path(args.quality_gate_json) if args.quality_gate_json else _find_latest_quality_gate(DEFAULT_OUTPUT_BASE)
    quality_payload: Dict[str, Any] = {}
    if quality_path and quality_path.exists():
        quality_payload = _load_json(quality_path)
    quality_gate_md = ""
    if quality_path:
        candidate = quality_path.with_suffix(".md")
        if candidate.exists():
            quality_gate_md = str(candidate)

    backend_status = _http_json(args.backend_url.rstrip("/") + "/api/status", args.status_timeout_sec)
    watch_status = _file_json(args.watch_status_json) if args.watch_status_json else _http_json(args.watch_status_url, args.status_timeout_sec)
    marker_status = _load_marker_status()
    latest_diagnosis = (watch_status.get("payload") or {}).get("latest_diagnosis") or {}
    diagnosed_request_ids = [str(item) for item in (latest_diagnosis.get("diagnosed_request_ids") or [])]
    browser_capture_evidence = _browser_capture_evidence(
        Path(args.web_root),
        diagnosed_request_ids,
        allow_legacy_browser_evidence=bool(args.allow_legacy_browser_evidence),
    )
    gates = _build_gates(backend_status, watch_status, marker_status, quality_path, quality_payload, browser_capture_evidence)
    readiness_summary = _build_readiness_summary(gates)
    ready = bool(readiness_summary.get("ready_to_complete"))
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "ready_to_complete": ready,
        "readiness_summary": readiness_summary,
        "backend_status": backend_status,
        "watch_status": watch_status,
        "marker_status": marker_status,
        "web_root": str(Path(args.web_root)),
        "browser_capture_evidence": browser_capture_evidence,
        "allow_legacy_browser_evidence": bool(args.allow_legacy_browser_evidence),
        "quality_gate_json": str(quality_path) if quality_path else "",
        "quality_gate_md": quality_gate_md,
        "quality_summary": quality_payload,
        "gates": gates,
    }
    json_path = output_dir / "flower_jump_goal_readiness_audit.json"
    md_path = output_dir / "flower_jump_goal_readiness_audit.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    print(f"已生成目标完成度审计 JSON：{json_path}")
    print(f"已生成目标完成度审计报告：{md_path}")
    print(f"目标完成状态：{'READY_TO_COMPLETE' if ready else 'NOT_READY'}")
    for gate in gates:
        print(f"- {gate['name']}: {_fmt_bool(gate['passed'])} ({gate['detail']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

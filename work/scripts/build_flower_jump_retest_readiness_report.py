#!/usr/bin/env python3
"""Build a read-only flower/jump web retest readiness report.

This script does not call /api/score, move the formal marker, rerun Holistic, or
restart the 5080 backend. It refreshes the lightweight frontend contract check
and the goal-readiness audit, then summarizes whether the system is ready for a
real browser retest and which required word still needs to be captured.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


REPO_ROOT = Path("/data/WYC/signLanguage")
SCRIPTS_DIR = REPO_ROOT / "work/scripts"
DEFAULT_OUTPUT_BASE = REPO_ROOT / "work/generated/scoring_mvp_run3"
DEFAULT_WATCH_STATUS_JSON = REPO_ROOT / "work/web/static/watch_status.json"
DEFAULT_BACKEND_URL = "http://127.0.0.1:5080"
DEFAULT_REQUIRED_WORDS = ["花", "跳"]


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _http_json(url: str, timeout_sec: float = 3.0) -> Dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout_sec) as response:
            return {"ok": True, "payload": json.loads(response.read().decode("utf-8")), "error": ""}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"ok": False, "payload": {}, "error": str(exc)}


def _find_latest(pattern: str) -> Optional[Path]:
    candidates = sorted(DEFAULT_OUTPUT_BASE.glob(pattern))
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _run_command(name: str, cmd: Sequence[str], cwd: Path) -> Dict[str, Any]:
    started_at = datetime.now().isoformat(timespec="seconds")
    completed = subprocess.run(
        list(cmd),
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        "name": name,
        "command": list(cmd),
        "started_at": started_at,
        "finished_at": datetime.now().isoformat(timespec="seconds"),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def _as_percent(value: Any) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "-"


def _fmt(value: Any, digits: int = 3) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "-"


def _word_list(words: Sequence[str]) -> str:
    return "、".join([word for word in words if word]) or "-"


def _quality_metrics(quality: Dict[str, Any]) -> Dict[str, Any]:
    summaries = quality.get("summaries") or {}
    web = quality.get("web_summary") or summaries.get("web_regression") or {}
    confusion = quality.get("confusion_summary") or summaries.get("web_confusion_gate") or {}
    synthetic_confusion = quality.get("synthetic_confusion_summary") or summaries.get("synthetic_confusion_robustness_gate") or {}
    discrimination = quality.get("discrimination_summary") or summaries.get("discrimination_gate") or {}
    pose = quality.get("pose_summary") or summaries.get("pose_robustness_gate") or {}
    framing = quality.get("framing_summary") or summaries.get("framing_robustness_gate") or {}
    aspect_ratio = quality.get("aspect_ratio_summary") or summaries.get("aspect_ratio_robustness_gate") or {}
    camera_roll = quality.get("camera_roll_summary") or summaries.get("camera_roll_robustness_gate") or {}
    body_anchor = quality.get("body_anchor_summary") or summaries.get("body_anchor_robustness_gate") or {}
    depth = quality.get("depth_summary") or summaries.get("depth_robustness_gate") or {}
    z_flicker = quality.get("z_flicker_summary") or summaries.get("z_flicker_robustness_gate") or {}
    hand_trajectory_interpolation = (
        quality.get("hand_trajectory_interpolation_summary")
        or summaries.get("hand_trajectory_interpolation_robustness_gate")
        or {}
    )
    edge_clipping = quality.get("edge_clipping_summary") or summaries.get("edge_clipping_robustness_gate") or {}
    mirror = quality.get("mirror_summary") or summaries.get("mirror_robustness_gate") or {}
    hand_role = quality.get("hand_role_summary") or summaries.get("hand_role_robustness_gate") or {}
    noncore_hand_distractor = quality.get("noncore_hand_distractor_summary") or summaries.get("noncore_hand_distractor_robustness_gate") or {}
    relation_geometry = quality.get("relation_geometry_summary") or summaries.get("relation_geometry_robustness_gate") or {}
    core_shape_amplitude = quality.get("core_shape_amplitude_summary") or summaries.get("core_shape_amplitude_robustness_gate") or {}
    perspective_shear = quality.get("perspective_shear_summary") or summaries.get("perspective_shear_robustness_gate") or {}
    interhand_temporal_desync = quality.get("interhand_temporal_desync_summary") or summaries.get("interhand_temporal_desync_robustness_gate") or {}
    temporal_order_jitter = quality.get("temporal_order_jitter_summary") or summaries.get("temporal_order_jitter_robustness_gate") or {}
    finger_identity_jitter = quality.get("finger_identity_jitter_summary") or summaries.get("finger_identity_jitter_robustness_gate") or {}
    hand_scale_flicker = quality.get("hand_scale_flicker_summary") or summaries.get("hand_scale_flicker_robustness_gate") or {}
    hand_center_flicker = quality.get("hand_center_flicker_summary") or summaries.get("hand_center_flicker_robustness_gate") or {}
    global_framing_flicker = quality.get("global_framing_flicker_summary") or summaries.get("global_framing_flicker_robustness_gate") or {}
    finger_mid_joint_occlusion = quality.get("finger_mid_joint_occlusion_summary") or summaries.get("finger_mid_joint_occlusion_robustness_gate") or {}
    hand_label_flicker = quality.get("hand_label_flicker_summary") or summaries.get("hand_label_flicker_robustness_gate") or {}
    hand_dropout_burst = quality.get("hand_dropout_burst_summary") or summaries.get("hand_dropout_burst_robustness_gate") or {}
    frame = quality.get("frame_summary") or summaries.get("frame_count_robustness_gate") or {}
    temporal_stutter = quality.get("temporal_stutter_summary") or summaries.get("temporal_stutter_robustness_gate") or {}
    temporal_rate = quality.get("temporal_rate_summary") or summaries.get("temporal_rate_robustness_gate") or {}
    temporal_metadata = quality.get("temporal_metadata_summary") or summaries.get("temporal_metadata_robustness_gate") or {}
    composite_browser = quality.get("composite_browser_summary") or summaries.get("composite_browser_robustness_gate") or {}
    frame_weight = quality.get("frame_weight_summary") or summaries.get("frame_weight_robustness_gate") or {}
    coordinate_precision = quality.get("coordinate_precision_summary") or summaries.get("coordinate_precision_robustness_gate") or {}
    motion_blur = quality.get("motion_blur_summary") or summaries.get("motion_blur_robustness_gate") or {}
    landmark_noise = quality.get("landmark_noise_summary") or summaries.get("landmark_noise_robustness_gate") or {}
    landmark_spike = quality.get("landmark_spike_summary") or summaries.get("landmark_spike_robustness_gate") or {}
    fingertip_occlusion = quality.get("fingertip_occlusion_summary") or summaries.get("fingertip_occlusion_robustness_gate") or {}
    palm_anchor_occlusion = quality.get("palm_anchor_occlusion_summary") or summaries.get("palm_anchor_occlusion_robustness_gate") or {}
    hand_shape_scale = quality.get("hand_shape_scale_summary") or summaries.get("hand_shape_scale_robustness_gate") or {}
    hand_orientation = quality.get("hand_orientation_summary") or summaries.get("hand_orientation_robustness_gate") or {}
    hand_z_tilt = quality.get("hand_z_tilt_summary") or summaries.get("hand_z_tilt_robustness_gate") or {}
    finger_curl_style = quality.get("finger_curl_style_summary") or summaries.get("finger_curl_style_robustness_gate") or {}
    finger_length_style = quality.get("finger_length_style_summary") or summaries.get("finger_length_style_robustness_gate") or {}
    moving_setup_exit = quality.get("moving_setup_exit_summary") or summaries.get("moving_setup_exit_robustness_gate") or {}
    core_phase_speed = quality.get("core_phase_speed_summary") or summaries.get("core_phase_speed_robustness_gate") or {}
    hand_confidence_attenuation = (
        quality.get("hand_confidence_attenuation_summary")
        or summaries.get("hand_confidence_attenuation_robustness_gate")
        or {}
    )
    energy_sampling = quality.get("energy_sampling_summary") or summaries.get("energy_sampling_robustness_gate") or {}
    rolling_shutter = quality.get("rolling_shutter_summary") or summaries.get("rolling_shutter_robustness_gate") or {}
    hand_detail_loss = quality.get("hand_detail_loss_summary") or summaries.get("hand_detail_loss_robustness_gate") or {}
    hand_stream_latency = quality.get("hand_stream_latency_summary") or summaries.get("hand_stream_latency_robustness_gate") or {}
    ghost_hand_duplicate = quality.get("ghost_hand_duplicate_summary") or summaries.get("ghost_hand_duplicate_robustness_gate") or {}
    hand_overlap_merge = quality.get("hand_overlap_merge_summary") or summaries.get("hand_overlap_merge_robustness_gate") or {}
    wrist_anchor_drift = quality.get("wrist_anchor_drift_summary") or summaries.get("wrist_anchor_drift_robustness_gate") or {}
    finger_chain_latency = quality.get("finger_chain_latency_summary") or summaries.get("finger_chain_latency_robustness_gate") or {}
    finger_fan_geometry = quality.get("finger_fan_geometry_summary") or summaries.get("finger_fan_geometry_robustness_gate") or {}
    finger_base_geometry = quality.get("finger_base_geometry_summary") or summaries.get("finger_base_geometry_robustness_gate") or {}
    finger_chain_confidence = quality.get("finger_chain_confidence_summary") or summaries.get("finger_chain_confidence_robustness_gate") or {}
    finger_chain_smoothing = quality.get("finger_chain_smoothing_summary") or summaries.get("finger_chain_smoothing_robustness_gate") or {}
    finite_coordinate = quality.get("finite_coordinate_summary") or summaries.get("finite_coordinate_robustness_gate") or {}
    bounded_coordinate = quality.get("bounded_coordinate_summary") or summaries.get("bounded_coordinate_robustness_gate") or {}
    missing_mask = quality.get("missing_mask_summary") or summaries.get("missing_mask_robustness_gate") or {}
    temporal_padding = quality.get("temporal_padding_summary") or summaries.get("temporal_padding_robustness_gate") or {}
    phase_order = quality.get("phase_order_summary") or summaries.get("phase_order_robustness_gate") or {}
    action_crop = quality.get("action_crop_summary") or summaries.get("action_crop_robustness_gate") or {}
    action_repeat = quality.get("action_repeat_summary") or summaries.get("action_repeat_robustness_gate") or {}
    return {
        "web": web,
        "confusion": confusion,
        "synthetic_confusion": synthetic_confusion,
        "discrimination": discrimination,
        "pose": pose,
        "framing": framing,
        "aspect_ratio": aspect_ratio,
        "camera_roll": camera_roll,
        "body_anchor": body_anchor,
        "depth": depth,
        "z_flicker": z_flicker,
        "hand_trajectory_interpolation": hand_trajectory_interpolation,
        "edge_clipping": edge_clipping,
        "mirror": mirror,
        "hand_role": hand_role,
        "noncore_hand_distractor": noncore_hand_distractor,
        "relation_geometry": relation_geometry,
        "core_shape_amplitude": core_shape_amplitude,
        "perspective_shear": perspective_shear,
        "interhand_temporal_desync": interhand_temporal_desync,
        "temporal_order_jitter": temporal_order_jitter,
        "finger_identity_jitter": finger_identity_jitter,
        "hand_scale_flicker": hand_scale_flicker,
        "hand_center_flicker": hand_center_flicker,
        "global_framing_flicker": global_framing_flicker,
        "finger_mid_joint_occlusion": finger_mid_joint_occlusion,
        "hand_label_flicker": hand_label_flicker,
        "hand_dropout_burst": hand_dropout_burst,
        "frame": frame,
        "temporal_stutter": temporal_stutter,
        "temporal_rate": temporal_rate,
        "temporal_metadata": temporal_metadata,
        "composite_browser": composite_browser,
        "frame_weight": frame_weight,
        "coordinate_precision": coordinate_precision,
        "motion_blur": motion_blur,
        "landmark_noise": landmark_noise,
        "landmark_spike": landmark_spike,
        "fingertip_occlusion": fingertip_occlusion,
        "palm_anchor_occlusion": palm_anchor_occlusion,
        "hand_shape_scale": hand_shape_scale,
        "hand_orientation": hand_orientation,
        "hand_z_tilt": hand_z_tilt,
        "finger_curl_style": finger_curl_style,
        "finger_length_style": finger_length_style,
        "moving_setup_exit": moving_setup_exit,
        "core_phase_speed": core_phase_speed,
        "hand_confidence_attenuation": hand_confidence_attenuation,
        "energy_sampling": energy_sampling,
        "rolling_shutter": rolling_shutter,
        "hand_detail_loss": hand_detail_loss,
        "hand_stream_latency": hand_stream_latency,
        "ghost_hand_duplicate": ghost_hand_duplicate,
        "hand_overlap_merge": hand_overlap_merge,
        "wrist_anchor_drift": wrist_anchor_drift,
        "finger_chain_latency": finger_chain_latency,
        "finger_fan_geometry": finger_fan_geometry,
        "finger_base_geometry": finger_base_geometry,
        "finger_chain_confidence": finger_chain_confidence,
        "finger_chain_smoothing": finger_chain_smoothing,
        "finite_coordinate": finite_coordinate,
        "bounded_coordinate": bounded_coordinate,
        "missing_mask": missing_mask,
        "temporal_padding": temporal_padding,
        "phase_order": phase_order,
        "action_crop": action_crop,
        "action_repeat": action_repeat,
    }


def _next_step(browser_evidence: Dict[str, Any], fallback_words: Sequence[str]) -> str:
    rows = browser_evidence.get("rows") if isinstance(browser_evidence.get("rows"), list) else []
    failed_words = sorted(
        {
            str(row.get("target_word") or "")
            for row in rows
            if row.get("target_word") and not row.get("passed")
        }
    )
    if failed_words:
        return f"复查 {_word_list(failed_words)}"
    missing = [str(word) for word in (browser_evidence.get("missing_required_words") or []) if word]
    if missing:
        return f"采集 {_word_list(missing)}"
    required = [str(word) for word in (browser_evidence.get("required_words") or fallback_words) if word]
    observed = {str(word) for word in (browser_evidence.get("observed_words") or [])}
    if required and all(word in observed for word in required):
        return f"{_word_list(required)} 覆盖完成，等待完成度审计"
    if required:
        return f"采集 {_word_list(required)}"
    return "等待 watcher 刷新"


def _sampling_guidance(words: Sequence[str]) -> List[Dict[str, Any]]:
    guidance: List[Dict[str, Any]] = []
    for word in words:
        if word == "花":
            guidance.append(
                {
                    "word": word,
                    "min_frames": 12,
                    "duration_sec": 2.5,
                    "fps": 5,
                    "cue": "从撮合状态开始，手指张开/绽放过程完整入画。",
                }
            )
        elif word == "跳":
            guidance.append(
                {
                    "word": word,
                    "min_frames": 6,
                    "duration_sec": 2.0,
                    "fps": 5,
                    "cue": "左手地面和右手两指小人同时入画，右手在左手基础上完成弹跳。",
                }
            )
    return guidance


def _score_upload_contract(backend_url: str, timeout_sec: float) -> Dict[str, Any]:
    openapi = _http_json(backend_url.rstrip("/") + "/openapi.json", timeout_sec=timeout_sec)
    payload = openapi.get("payload") if isinstance(openapi.get("payload"), dict) else {}
    schemas = payload.get("components", {}).get("schemas", {}) if isinstance(payload, dict) else {}
    score_schema = schemas.get("ScoreRequest") if isinstance(schemas, dict) else {}
    props = score_schema.get("properties", {}) if isinstance(score_schema, dict) else {}
    required_fields = ["target_word", "fps", "duration_sec", "frames", "frame_indices", "frame_weights"]
    optional_client_fields = ["client_source", "client_session_id", "client_capture_id"]
    missing_required = [name for name in required_fields if name not in props]
    missing_optional = [name for name in optional_client_fields if name not in props]
    return {
        "ok": bool(openapi.get("ok") and props and not missing_required),
        "openapi_ok": bool(openapi.get("ok")),
        "error": openapi.get("error") or "",
        "required_fields": required_fields,
        "missing_required_fields": missing_required,
        "optional_client_fields": optional_client_fields,
        "missing_optional_client_fields": missing_optional,
        "score_request_properties": sorted(props.keys()) if props else [],
        "strong_evidence_path": "frame_weights" if "frame_weights" in props else "",
    }


def _browser_upload_weight_contract(contract_payload: Dict[str, Any]) -> Dict[str, Any]:
    checks = [
        row
        for row in (contract_payload.get("checks") or [])
        if isinstance(row, dict) and str(row.get("name") or "").startswith("frontend_upload_")
    ]
    failed = [row for row in checks if not row.get("passed") and row.get("severity", "fail") == "fail"]
    return {
        "ok": bool(checks and not failed),
        "check_count": len(checks),
        "failed_checks": [str(row.get("name") or "") for row in failed],
    }


def _build_markdown(payload: Dict[str, Any]) -> str:
    readiness = payload.get("goal_readiness") or {}
    browser = readiness.get("browser_capture_evidence") or {}
    quality = payload.get("quality_gate") or {}
    contract = payload.get("frontend_contract") or {}
    browser_gate = payload.get("browser_evidence_gate") or {}
    upload_sim = payload.get("browser_upload_weight_simulation_gate") or {}
    metrics = _quality_metrics(quality)
    next_step = payload.get("next_step") or "-"
    missing_words = browser.get("missing_required_words") or []
    observed_words = browser.get("observed_words") or []
    required_words = browser.get("required_words") or DEFAULT_REQUIRED_WORDS

    lines = [
        "# 花/跳网页复测前就绪报告",
        "",
        f"- 生成时间：`{payload.get('generated_at')}`",
        f"- 复测就绪：`{'PASS' if payload.get('ready_for_retest') else 'CHECK_NEEDED'}`",
        f"- 目标完成度：`{readiness.get('status_label') or 'UNKNOWN'}`",
        f"- 下一步：`{next_step}`",
        f"- 要求覆盖词条：`{_word_list(required_words)}`",
        f"- 已覆盖词条：`{_word_list(observed_words)}`",
        f"- 缺失词条：`{_word_list(missing_words)}`",
        "- 口径：只读检查；不调用 `/api/score`，不移动 marker，不重启 5080/Holistic。",
        "",
        "## 运行态",
        "",
        "| 项 | 状态 | 细节 |",
        "|---|---|---|",
    ]
    runtime = payload.get("runtime") or {}
    upload_contract = payload.get("score_upload_contract") or {}
    upload_weight_contract = payload.get("browser_upload_weight_contract") or {}
    lines.append(
        f"| 5080/Holistic | `{'PASS' if runtime.get('backend_ready') else 'FAIL'}` | "
        f"worker=`{runtime.get('worker_status')}`，pid=`{runtime.get('worker_pid')}`，"
        f"reload_count=`{runtime.get('reload_count')}`，last_reload_error=`{runtime.get('last_reload_error')}` |"
    )
    lines.append(
        f"| watcher | `{'PASS' if runtime.get('watcher_online') else 'FAIL'}` | "
        f"event=`{runtime.get('watch_event')}`，pid=`{runtime.get('watcher_pid')}`，"
        f"target_count=`{runtime.get('target_count')}` |"
    )
    lines.append(
        f"| 前端契约 | `{'PASS' if contract.get('status') == 'PASS' else 'FAIL'}` | "
        f"failed=`{contract.get('failed_count')}`，warning=`{contract.get('warning_count')}` |"
    )
    lines.append(
        f"| 综合质量门 | `{'PASS' if quality.get('passed') else 'FAIL'}` | "
        f"报告 `{payload.get('quality_gate_md') or '-'}` |"
    )
    lines.append(
        f"| 浏览器证据门 | `{'PASS' if browser_gate.get('passed') else 'FAIL'}` | "
        f"报告 `{payload.get('browser_evidence_gate_md') or '-'}` |"
    )
    lines.append(
        f"| 网页上传权重语义 | `{'PASS' if upload_weight_contract.get('ok') else 'FAIL'}` | "
        f"checks=`{upload_weight_contract.get('check_count')}`，"
        f"failed=`{_word_list(upload_weight_contract.get('failed_checks') or [])}` |"
    )
    lines.append(
        f"| 网页上传权重仿真 | `{'PASS' if upload_sim.get('passed') else 'FAIL'}` | "
        f"cases=`{upload_sim.get('case_count')}`，报告 `{payload.get('browser_upload_weight_simulation_gate_md') or '-'}` |"
    )
    optional_missing = upload_contract.get("missing_optional_client_fields") or []
    optional_note = f"，client metadata pending `{_word_list(optional_missing)}`" if optional_missing else ""
    lines.append(
        f"| 网页上传强证据 | `{'PASS' if upload_contract.get('ok') else 'FAIL'}` | "
        f"strong path=`{upload_contract.get('strong_evidence_path') or '-'}`，"
        f"missing_required=`{_word_list(upload_contract.get('missing_required_fields') or [])}`{optional_note} |"
    )
    lines.append("")

    web = metrics.get("web") or {}
    effective = web.get("by_word_effective") or {}
    lines.extend(
        [
            "## 当前质量门关键指标",
            "",
            f"- 保存网页/API 回归：样本 `{web.get('samples')}`，错误 `{web.get('replay_errors')}`；"
            f"有效正常+边界率 `{_as_percent(web.get('effective_rate'))}`。",
            "",
            "| 词条 | 有效采集 | 正常+边界 | 有效低分 | 有效率 | 有效均分 |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for word in DEFAULT_REQUIRED_WORDS:
        row = effective.get(word) or {}
        lines.append(
            f"| {word} | {row.get('reliable_samples', '-')} | {row.get('normal_or_borderline', '-')} | "
            f"{row.get('low', '-')} | {_as_percent(row.get('normal_or_borderline_rate'))} | "
            f"{_fmt(row.get('score_mean'))} |"
        )

    confusion = metrics.get("confusion") or {}
    lines.extend(
        [
            "",
            f"- 花/跳交叉混淆：eligible `{confusion.get('eligible')}`，pass `{confusion.get('pass')}`，fail `{confusion.get('fail')}`。",
        ]
    )
    synthetic_confusion = metrics.get("synthetic_confusion") or {}
    synthetic_rows = synthetic_confusion.get("rows") or []
    if synthetic_rows:
        lines.extend(
            [
                "",
                "| 词条 | 合成鲁棒 cases | pass | fail | 目标最低 | 交叉最高 | margin 最低 | 最弱变体 |",
                "|---|---:|---:|---:|---:|---:|---:|---|",
            ]
        )
        for row in synthetic_rows:
            lines.append(
                f"| {row.get('word')} | {row.get('samples')} | {row.get('pass')} | {row.get('fail')} | "
                f"{_fmt(row.get('target_score_min'))} | {_fmt(row.get('cross_score_max'))} | "
                f"{_fmt(row.get('margin_min'))} | {row.get('weakest_variant') or '-'} |"
            )
    temporal_stutter = metrics.get("temporal_stutter") or {}
    temporal_stutter_rows = temporal_stutter.get("rows") or []
    if temporal_stutter_rows:
        lines.extend(
            [
                "",
                "| 词条 | stutter 正向最低分 | 最弱正向 stutter | 持续冻结最高分 | 最强持续冻结 | stutter 诊断最低分 | 最弱诊断边界 |",
                "|---|---:|---|---:|---|---:|---|",
            ]
        )
        for row in temporal_stutter_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('strongest_negative_score'))} | "
                f"{row.get('strongest_negative_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    hand_trajectory_interpolation = metrics.get("hand_trajectory_interpolation") or {}
    hand_trajectory_interpolation_rows = hand_trajectory_interpolation.get("rows") or []
    if hand_trajectory_interpolation_rows:
        lines.extend(
            [
                "",
                "| 词条 | 插值补洞正向最低分 | 最弱正向插值 | 插值补洞诊断最低分 | 最弱诊断插值 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in hand_trajectory_interpolation_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    temporal_rate = metrics.get("temporal_rate") or {}
    temporal_rate_rows = temporal_rate.get("rows") or []
    if temporal_rate_rows:
        lines.extend(
            [
                "",
                "| 词条 | 速率正向最低分 | 最弱正向速率扰动 | 速率诊断最低分 | 最弱诊断边界 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in temporal_rate_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    temporal_metadata = metrics.get("temporal_metadata") or {}
    temporal_metadata_rows = temporal_metadata.get("rows") or []
    if temporal_metadata_rows:
        lines.extend(
            [
                "",
                "| 词条 | 时间元数据清洗正向最低分 | 最弱时间元数据变体 |",
                "|---|---:|---|",
            ]
        )
        for row in temporal_metadata_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} |"
            )

    composite_browser = metrics.get("composite_browser") or {}
    composite_rows = composite_browser.get("rows") or []
    if composite_rows:
        lines.extend(
            [
                "",
                "| 词条 | 组合正向最低分 | 最弱正向组合 | 组合诊断最低分 | 最弱诊断组合 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in composite_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    frame_weight = metrics.get("frame_weight") or {}
    frame_weight_rows = frame_weight.get("rows") or []
    if frame_weight_rows:
        lines.extend(
            [
                "",
                "| 词条 | frame_weights/异常权重清洗正向最低分 | 最弱正向权重 | 反向权重诊断最低分 | 最弱诊断权重 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in frame_weight_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    coordinate_precision = metrics.get("coordinate_precision") or {}
    coordinate_rows = coordinate_precision.get("rows") or []
    if coordinate_rows:
        lines.extend(
            [
                "",
                "| 词条 | 坐标精度正向最低分 | 最弱正向精度扰动 | 粗量化诊断最低分 | 最弱诊断精度扰动 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in coordinate_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    motion_blur = metrics.get("motion_blur") or {}
    motion_rows = motion_blur.get("rows") or []
    if motion_rows:
        lines.extend(
            [
                "",
                "| 词条 | 运动幅度正向最低分 | 最弱正向幅度变体 | 平滑/模糊诊断最低分 | 最弱诊断平滑/模糊 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in motion_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    landmark_noise = metrics.get("landmark_noise") or {}
    landmark_rows = landmark_noise.get("rows") or []
    if landmark_rows:
        lines.extend(
            [
                "",
                "| 词条 | landmark 噪声正向最低分 | 最弱正向噪声 | 严重噪声诊断最低分 | 最弱诊断噪声 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in landmark_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    landmark_spike = metrics.get("landmark_spike") or {}
    landmark_spike_rows = landmark_spike.get("rows") or []
    if landmark_spike_rows:
        lines.extend(
            [
                "",
                "| 词条 | landmark 跳点正向最低分 | 最弱正向跳点 | 跳点诊断最低分 | 最弱诊断跳点 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in landmark_spike_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    fingertip_occlusion = metrics.get("fingertip_occlusion") or {}
    fingertip_rows = fingertip_occlusion.get("rows") or []
    if fingertip_rows:
        lines.extend(
            [
                "",
                "| 词条 | 指尖遮挡正向最低分 | 最弱正向遮挡 | 核心指尖缺失最高分 | 最强核心缺失 | 遮挡诊断最低分 | 最弱诊断遮挡 |",
                "|---|---:|---|---:|---|---:|---|",
            ]
        )
        for row in fingertip_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('strongest_negative_score'))} | "
                f"{row.get('strongest_negative_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    palm_anchor_occlusion = metrics.get("palm_anchor_occlusion") or {}
    palm_anchor_rows = palm_anchor_occlusion.get("rows") or []
    if palm_anchor_rows:
        lines.extend(
            [
                "",
                "| 词条 | 掌根锚点正向最低分 | 最弱正向锚点缺失 | 核心锚点全缺最高分 | 最强核心锚点缺失 | 锚点诊断最低分 | 最弱诊断锚点缺失 |",
                "|---|---:|---|---:|---|---:|---|",
            ]
        )
        for row in palm_anchor_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('strongest_negative_score'))} | "
                f"{row.get('strongest_negative_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    finger_mid_joint_occlusion = metrics.get("finger_mid_joint_occlusion") or {}
    finger_mid_joint_rows = finger_mid_joint_occlusion.get("rows") or []
    if finger_mid_joint_rows:
        lines.extend(
            [
                "",
                "| 词条 | 中段指节遮挡正向最低分 | 最弱正向中段指节遮挡 | 中段指节诊断最低分 | 最弱诊断遮挡 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in finger_mid_joint_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    hand_shape_scale = metrics.get("hand_shape_scale") or {}
    hand_shape_rows = hand_shape_scale.get("rows") or []
    if hand_shape_rows:
        lines.extend(
            [
                "",
                "| 词条 | 手形尺度正向最低分 | 最弱正向手形尺度 | 极端尺度诊断最低分 | 最弱诊断尺度 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in hand_shape_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    hand_scale_flicker = metrics.get("hand_scale_flicker") or {}
    hand_scale_flicker_rows = hand_scale_flicker.get("rows") or []
    if hand_scale_flicker_rows:
        lines.extend(
            [
                "",
                "| 词条 | 手部尺度呼吸正向最低分 | 最弱正向尺度呼吸 | 尺度呼吸诊断最低分 | 最弱诊断尺度呼吸 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in hand_scale_flicker_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    hand_center_flicker = metrics.get("hand_center_flicker") or {}
    hand_center_flicker_rows = hand_center_flicker.get("rows") or []
    if hand_center_flicker_rows:
        lines.extend(
            [
                "",
                "| 词条 | 手部中心漂移正向最低分 | 最弱正向中心漂移 | 中心漂移诊断最低分 | 最弱诊断中心漂移 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in hand_center_flicker_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    global_framing_flicker = metrics.get("global_framing_flicker") or {}
    global_framing_flicker_rows = global_framing_flicker.get("rows") or []
    if global_framing_flicker_rows:
        lines.extend(
            [
                "",
                "| 词条 | 全局取景漂移正向最低分 | 最弱正向全局取景漂移 | 全局取景诊断最低分 | 最弱诊断全局取景漂移 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in global_framing_flicker_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    hand_orientation = metrics.get("hand_orientation") or {}
    hand_orientation_rows = hand_orientation.get("rows") or []
    if hand_orientation_rows:
        lines.extend(
            [
                "",
                "| 词条 | 手部旋转正向最低分 | 最弱正向旋转 | 极端旋转诊断最低分 | 最弱诊断旋转 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in hand_orientation_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    hand_z_tilt = metrics.get("hand_z_tilt") or {}
    hand_z_tilt_rows = hand_z_tilt.get("rows") or []
    if hand_z_tilt_rows:
        lines.extend(
            [
                "",
                "| 词条 | z 倾角正向最低分 | 最弱正向 z 倾角 | z 倾角诊断最低分 | 最弱诊断 z 倾角 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in hand_z_tilt_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    finger_curl_style = metrics.get("finger_curl_style") or {}
    finger_curl_style_rows = finger_curl_style.get("rows") or []
    if finger_curl_style_rows:
        lines.extend(
            [
                "",
                "| 词条 | 手指弯曲正向最低分 | 最弱正向弯曲 | 手指弯曲诊断最低分 | 最弱诊断弯曲 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in finger_curl_style_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    finger_length_style = metrics.get("finger_length_style") or {}
    finger_length_style_rows = finger_length_style.get("rows") or []
    if finger_length_style_rows:
        lines.extend(
            [
                "",
                "| 词条 | 手指比例正向最低分 | 最弱正向比例 | 手指比例诊断最低分 | 最弱诊断比例 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in finger_length_style_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    moving_setup_exit = metrics.get("moving_setup_exit") or {}
    moving_setup_exit_rows = moving_setup_exit.get("rows") or []
    if moving_setup_exit_rows:
        lines.extend(
            [
                "",
                "| 词条 | 动态入退场正向最低分 | 最弱正向动态污染 | 入场-only 最高分 | 最强入场-only | 诊断最低分 | 最弱诊断 |",
                "|---|---:|---|---:|---|---:|---|",
            ]
        )
        for row in moving_setup_exit_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('strongest_negative_score'))} | "
                f"{row.get('strongest_negative_variant') or '-'} | "
                f"{_fmt(row.get('diagnostic_lowest_score'))} | "
                f"{row.get('diagnostic_lowest_variant') or '-'} |"
            )

    core_phase_speed = metrics.get("core_phase_speed") or {}
    core_phase_speed_rows = core_phase_speed.get("rows") or []
    if core_phase_speed_rows:
        lines.extend(
            [
                "",
                "| 词条 | 核心速度正向最低分 | 最弱正向核心速度 | 核心速度诊断最低分 | 最弱诊断边界 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in core_phase_speed_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    hand_confidence_attenuation = metrics.get("hand_confidence_attenuation") or {}
    hand_confidence_rows = hand_confidence_attenuation.get("rows") or []
    if hand_confidence_rows:
        lines.extend(
            [
                "",
                "| 词条 | 手部置信度正向最低分 | 最弱正向低置信 | 手部置信度诊断最低分 | 最弱诊断边界 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in hand_confidence_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    energy_sampling = metrics.get("energy_sampling") or {}
    energy_sampling_rows = energy_sampling.get("rows") or []
    if energy_sampling_rows:
        lines.extend(
            [
                "",
                "| 词条 | 能量选帧正向最低分 | 最弱正向选帧 | 能量选帧诊断最低分 | 最弱诊断边界 | 推荐帧 |",
                "|---|---:|---|---:|---|---:|",
            ]
        )
        for row in energy_sampling_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} | "
                f"{row.get('min_upload_frames') or '-'} |"
            )

    rolling_shutter = metrics.get("rolling_shutter") or {}
    rolling_shutter_rows = rolling_shutter.get("rows") or []
    if rolling_shutter_rows:
        lines.extend(
            [
                "",
                "| 词条 | rolling-shutter 正向最低分 | 最弱正向 rolling-shutter | rolling-shutter 诊断最低分 | 最弱诊断边界 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in rolling_shutter_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    hand_detail_loss = metrics.get("hand_detail_loss") or {}
    hand_detail_rows = hand_detail_loss.get("rows") or []
    if hand_detail_rows:
        lines.extend(
            [
                "",
                "| 词条 | 手部细节损失正向最低分 | 最弱正向细节损失 | 手部细节损失诊断最低分 | 最弱诊断边界 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in hand_detail_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    hand_stream_latency = metrics.get("hand_stream_latency") or {}
    hand_stream_rows = hand_stream_latency.get("rows") or []
    if hand_stream_rows:
        lines.extend(
            [
                "",
                "| 词条 | 手部流延迟正向最低分 | 最弱正向手部流延迟 | 手部流延迟诊断最低分 | 最弱诊断边界 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in hand_stream_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    ghost_hand_duplicate = metrics.get("ghost_hand_duplicate") or {}
    ghost_hand_rows = ghost_hand_duplicate.get("rows") or []
    if ghost_hand_rows:
        lines.extend(
            [
                "",
                "| 词条 | 幽灵手正向最低分 | 最弱正向幽灵手 | 幽灵手诊断最低分 | 最弱诊断边界 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in ghost_hand_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    hand_overlap_merge = metrics.get("hand_overlap_merge") or {}
    hand_overlap_rows = hand_overlap_merge.get("rows") or []
    if hand_overlap_rows:
        lines.extend(
            [
                "",
                "| 词条 | 手部融合正向最低分 | 最弱正向融合 | 手部融合诊断最低分 | 最弱诊断边界 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in hand_overlap_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    wrist_anchor_drift = metrics.get("wrist_anchor_drift") or {}
    wrist_anchor_rows = wrist_anchor_drift.get("rows") or []
    if wrist_anchor_rows:
        lines.extend(
            [
                "",
                "| 词条 | 手腕掌根漂移正向最低分 | 最弱正向漂移 | 手腕掌根漂移诊断最低分 | 最弱诊断边界 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in wrist_anchor_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    finger_chain_latency = metrics.get("finger_chain_latency") or {}
    finger_chain_rows = finger_chain_latency.get("rows") or []
    if finger_chain_rows:
        lines.extend(
            [
                "",
                "| 词条 | 手指链延迟正向最低分 | 最弱正向延迟 | 手指链延迟诊断最低分 | 最弱诊断边界 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in finger_chain_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    finger_fan_geometry = metrics.get("finger_fan_geometry") or {}
    finger_fan_rows = finger_fan_geometry.get("rows") or []
    if finger_fan_rows:
        lines.extend(
            [
                "",
                "| 词条 | 手指扇形几何正向最低分 | 最弱正向扇形漂移 | 手指扇形几何诊断最低分 | 最弱诊断边界 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in finger_fan_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    finger_base_geometry = metrics.get("finger_base_geometry") or {}
    finger_base_rows = finger_base_geometry.get("rows") or []
    if finger_base_rows:
        lines.extend(
            [
                "",
                "| 词条 | 手指基座几何正向最低分 | 最弱正向基座漂移 | 手指基座几何诊断最低分 | 最弱诊断边界 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in finger_base_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    finger_chain_confidence = metrics.get("finger_chain_confidence") or {}
    finger_conf_rows = finger_chain_confidence.get("rows") or []
    if finger_conf_rows:
        lines.extend(
            [
                "",
                "| 词条 | 手指链软置信正向最低分 | 最弱正向低置信 | 手指链软置信诊断最低分 | 最弱诊断边界 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in finger_conf_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    finger_chain_smoothing = metrics.get("finger_chain_smoothing") or {}
    finger_smoothing_rows = finger_chain_smoothing.get("rows") or []
    if finger_smoothing_rows:
        lines.extend(
            [
                "",
                "| 词条 | 手指链时间平滑正向最低分 | 最弱正向平滑 | 手指链时间平滑诊断最低分 | 最弱诊断边界 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in finger_smoothing_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    finite_coordinate = metrics.get("finite_coordinate") or {}
    finite_coordinate_rows = finite_coordinate.get("rows") or []
    if finite_coordinate_rows:
        lines.extend(
            [
                "",
                "| 词条 | 非有限坐标正向最低分 | 最弱正向坏点 | 非有限坐标诊断最低分 | 最弱诊断边界 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in finite_coordinate_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    bounded_coordinate = metrics.get("bounded_coordinate") or {}
    bounded_coordinate_rows = bounded_coordinate.get("rows") or []
    if bounded_coordinate_rows:
        lines.extend(
            [
                "",
                "| 词条 | 有限异常/退化坐标正向最低分 | 最弱正向坏点 | 有限异常/退化坐标诊断最低分 | 最弱诊断边界 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in bounded_coordinate_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    missing_mask = metrics.get("missing_mask") or {}
    missing_rows = missing_mask.get("rows") or []
    if missing_rows:
        lines.extend(
            [
                "",
                "| 词条 | 非关键缺失最低分 | 最弱非关键缺失 | 关键缺失最高分 | 最强关键缺失 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in missing_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('strongest_negative_score'))} | "
                f"{row.get('strongest_negative_variant') or '-'} |"
            )

    mirror = metrics.get("mirror") or {}
    mirror_rows = mirror.get("rows") or []
    hand_role = metrics.get("hand_role") or {}
    hand_role_rows = hand_role.get("rows") or []
    noncore_hand_distractor = metrics.get("noncore_hand_distractor") or {}
    noncore_hand_distractor_rows = noncore_hand_distractor.get("rows") or []
    relation_geometry = metrics.get("relation_geometry") or {}
    relation_geometry_rows = relation_geometry.get("rows") or []
    core_shape_amplitude = metrics.get("core_shape_amplitude") or {}
    core_shape_amplitude_rows = core_shape_amplitude.get("rows") or []
    perspective_shear = metrics.get("perspective_shear") or {}
    perspective_shear_rows = perspective_shear.get("rows") or []
    interhand_temporal_desync = metrics.get("interhand_temporal_desync") or {}
    interhand_temporal_desync_rows = interhand_temporal_desync.get("rows") or []
    temporal_order_jitter = metrics.get("temporal_order_jitter") or {}
    temporal_order_jitter_rows = temporal_order_jitter.get("rows") or []
    finger_identity_jitter = metrics.get("finger_identity_jitter") or {}
    finger_identity_jitter_rows = finger_identity_jitter.get("rows") or []
    hand_label_flicker = metrics.get("hand_label_flicker") or {}
    hand_label_flicker_rows = hand_label_flicker.get("rows") or []
    hand_dropout_burst = metrics.get("hand_dropout_burst") or {}
    hand_dropout_rows = hand_dropout_burst.get("rows") or []
    framing = metrics.get("framing") or {}
    framing_rows = framing.get("rows") or []
    aspect_ratio = metrics.get("aspect_ratio") or {}
    aspect_ratio_rows = aspect_ratio.get("rows") or []
    camera_roll = metrics.get("camera_roll") or {}
    camera_roll_rows = camera_roll.get("rows") or []
    body_anchor = metrics.get("body_anchor") or {}
    body_anchor_rows = body_anchor.get("rows") or []
    depth = metrics.get("depth") or {}
    depth_rows = depth.get("rows") or []
    z_flicker = metrics.get("z_flicker") or {}
    z_flicker_rows = z_flicker.get("rows") or []
    edge_clipping = metrics.get("edge_clipping") or {}
    edge_rows = edge_clipping.get("rows") or []
    if framing_rows:
        lines.extend(
            [
                "",
                "| 词条 | 取景正向最低分 | 最弱取景扰动 | 极端诊断最低分 | 最弱诊断扰动 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in framing_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    if aspect_ratio_rows:
        lines.extend(
            [
                "",
                "| 词条 | 宽高比正向最低分 | 最弱正向宽高比 | 极端宽高比诊断最低分 | 最弱诊断宽高比 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in aspect_ratio_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    if camera_roll_rows:
        lines.extend(
            [
                "",
                "| 词条 | 整体倾斜正向最低分 | 最弱正向倾斜 | 极端倾斜诊断最低分 | 最弱诊断倾斜 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in camera_roll_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    if body_anchor_rows:
        lines.extend(
            [
                "",
                "| 词条 | 身体锚点正向最低分 | 最弱正向锚点漂移 | 诊断最低分 | 最弱诊断漂移 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in body_anchor_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    if depth_rows:
        lines.extend(
            [
                "",
                "| 词条 | depth 正向最低分 | 最弱 depth 扰动 | depth 诊断最低分 | 最弱诊断扰动 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in depth_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    if z_flicker_rows:
        lines.extend(
            [
                "",
                "| 词条 | z 时序抖动正向最低分 | 最弱正向 z 抖动 | z 时序诊断最低分 | 最弱诊断 z 抖动 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in z_flicker_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    if edge_rows:
        lines.extend(
            [
                "",
                "| 词条 | 边缘裁切正向最低分 | 最弱正向边缘裁切 | 核心裁切最高分 | 最强核心裁切 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in edge_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('strongest_negative_score'))} | "
                f"{row.get('strongest_negative_variant') or '-'} |"
            )

    if mirror_rows:
        lines.extend(
            [
                "",
                "| 词条 | 镜像正向最低分 | 最弱镜像变体 | 左右标签诊断最低分 | 最弱诊断变体 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in mirror_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    if hand_role_rows:
        lines.extend(
            [
                "",
                "| 词条 | 手角色正向最低分 | 最弱正向角色变体 | 角色互换最高分 | 最强角色互换负例 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in hand_role_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('strongest_negative_score'))} | "
                f"{row.get('strongest_negative_variant') or '-'} |"
            )

    if noncore_hand_distractor_rows:
        lines.extend(
            [
                "",
                "| 词条 | 非核心手/手指正向最低分 | 最弱正向干扰 | 诊断最低分 | 最弱诊断核心扰动 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in noncore_hand_distractor_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    if relation_geometry_rows:
        lines.extend(
            [
                "",
                "| 词条 | 关系几何正向最低分 | 最弱正向关系扰动 | 关系负向最高分 | 最强负向关系 | 关系诊断最低分 | 最弱诊断关系 |",
                "|---|---:|---|---:|---|---:|---|",
            ]
        )
        for row in relation_geometry_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('strongest_negative_score'))} | "
                f"{row.get('strongest_negative_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    if core_shape_amplitude_rows:
        lines.extend(
            [
                "",
                "| 词条 | 核心手形正向最低分 | 最弱正向核心形变 | 核心形变负向最高分 | 最强负向核心形变 | 核心形变诊断最低分 | 最弱诊断形变 |",
                "|---|---:|---|---:|---|---:|---|",
            ]
        )
        for row in core_shape_amplitude_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('strongest_negative_score'))} | "
                f"{row.get('strongest_negative_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    if perspective_shear_rows:
        lines.extend(
            [
                "",
                "| 词条 | 斜拍透视正向最低分 | 最弱正向透视/剪切 | 斜拍透视诊断最低分 | 最弱诊断透视/剪切 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in perspective_shear_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    if interhand_temporal_desync_rows:
        lines.extend(
            [
                "",
                "| 词条 | 手间时序错位正向最低分 | 最弱正向错位 | 手间错位诊断最低分 | 最弱诊断错位 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in interhand_temporal_desync_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    if temporal_order_jitter_rows:
        lines.extend(
            [
                "",
                "| 词条 | 帧序抖动正向最低分 | 最弱正向帧序抖动 | 帧序抖动诊断最低分 | 最弱诊断帧序抖动 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in temporal_order_jitter_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    if finger_identity_jitter_rows:
        lines.extend(
            [
                "",
                "| 词条 | 手指身份抖动正向最低分 | 最弱正向指链抖动 | 手指身份诊断最低分 | 最弱诊断指链抖动 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in finger_identity_jitter_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('weakest_diagnostic_score'))} | "
                f"{row.get('weakest_diagnostic_variant') or '-'} |"
            )

    if hand_label_flicker_rows:
        lines.extend(
            [
                "",
                "| 词条 | 标签 flicker 正向最低分 | 最弱正向 flicker | 严重 flicker 最高分 | 最强严重 flicker |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in hand_label_flicker_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('strongest_negative_score'))} | "
                f"{row.get('strongest_negative_variant') or '-'} |"
            )

    if hand_dropout_rows:
        lines.extend(
            [
                "",
                "| 词条 | 连续手部空洞正向最低分 | 最弱正向空洞 | 持续空洞最高分 | 最强持续空洞 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in hand_dropout_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('strongest_negative_score'))} | "
                f"{row.get('strongest_negative_variant') or '-'} |"
            )

    temporal_padding = metrics.get("temporal_padding") or {}
    temporal_rows = temporal_padding.get("rows") or []
    if temporal_rows:
        lines.extend(
            [
                "",
                "| 词条 | padding 正向最低分 | 最弱正向 padding | 静态最高分 | 最强静态变体 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in temporal_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('strongest_negative_score'))} | "
                f"{row.get('strongest_negative_variant') or '-'} |"
            )

    phase_order = metrics.get("phase_order") or {}
    phase_rows = phase_order.get("rows") or []
    if phase_rows:
        lines.extend(
            [
                "",
                "| 词条 | 相位单调最低分 | 最弱单调变形 | 相位错序最高分 | 最强错序变体 |",
                "|---|---:|---|---:|---|",
            ]
        )
        for row in phase_rows:
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('strongest_negative_score'))} | "
                f"{row.get('strongest_negative_variant') or '-'} |"
            )

    action_crop = metrics.get("action_crop") or {}
    action_rows = action_crop.get("rows") or []
    if action_rows:
        lines.extend(
            [
                "",
                "| 词条 | 起止裁剪正向最低分 | 最弱正向裁剪 | 缺核心最高分 | 最强缺核心裁剪 | 诊断分数范围 |",
                "|---|---:|---|---:|---|---|",
            ]
        )
        for row in action_rows:
            diagnostic_range = "-"
            if row.get("diagnostic_lowest_score") is not None:
                diagnostic_range = f"{_fmt(row.get('diagnostic_lowest_score'))} - {_fmt(row.get('diagnostic_highest_score'))}"
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('strongest_negative_score'))} | "
                f"{row.get('strongest_negative_variant') or '-'} | {diagnostic_range} |"
            )

    action_repeat = metrics.get("action_repeat") or {}
    repeat_rows = action_repeat.get("rows") or []
    if repeat_rows:
        lines.extend(
            [
                "",
                "| 词条 | 重复动作正向最低分 | 最弱正向重复 | 不完整最高分 | 最强不完整负例 | 诊断分数范围 |",
                "|---|---:|---|---:|---|---|",
            ]
        )
        for row in repeat_rows:
            diagnostic_range = "-"
            if row.get("diagnostic_lowest_score") is not None:
                diagnostic_range = f"{_fmt(row.get('diagnostic_lowest_score'))} - {_fmt(row.get('diagnostic_highest_score'))}"
            lines.append(
                f"| {row.get('word')} | {_fmt(row.get('weakest_positive_score'))} | "
                f"{row.get('weakest_positive_variant') or '-'} | "
                f"{_fmt(row.get('strongest_negative_score'))} | "
                f"{row.get('strongest_negative_variant') or '-'} | {diagnostic_range} |"
            )

    lines.extend(["", "## 下一步采集建议", ""])
    guidance = payload.get("sampling_guidance") or []
    if guidance:
        lines.extend(["| 词条 | 推荐最少上传帧 | 推荐采集 | 动作重点 |", "|---|---:|---|---|"])
        for row in guidance:
            lines.append(
                f"| {row['word']} | {row['min_frames']} | {row['duration_sec']}s / {row['fps']}fps | {row['cue']} |"
            )
    else:
        lines.append("- 当前没有缺失词条；等待 watcher 完成诊断或检查完成度审计。")

    lines.extend(
        [
            "",
            "## 关联报告",
            "",
            f"- 完成度审计：`{payload.get('goal_readiness_md') or '-'}`",
            f"- 前端契约：`{payload.get('frontend_contract_md') or '-'}`",
            f"- 浏览器证据门：`{payload.get('browser_evidence_gate_md') or '-'}`",
            f"- 网页上传权重仿真：`{payload.get('browser_upload_weight_simulation_gate_md') or '-'}`",
            f"- 综合质量门：`{payload.get('quality_gate_md') or '-'}`",
            "",
            "## 结论",
            "",
        ]
    )
    if readiness.get("status_label") == "READY_TO_COMPLETE":
        lines.append("- 当前证据显示目标可结项。")
    elif payload.get("ready_for_retest"):
        lines.append(f"- 算法、运行态和前端链路已就绪；还需要真实网页摄像头样本：`{next_step}`。")
    else:
        lines.append("- 复测前仍有运行态、质量门或前端契约检查项需要处理。")
    return "\n".join(lines) + "\n"


def build_report(args: argparse.Namespace) -> Dict[str, Any]:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    contract_dir = output_dir / "frontend_contract"
    contract_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "check_watch_status_frontend_contract.py"),
        "--watch-status-json",
        str(args.watch_status_json),
        "--output-dir",
        str(contract_dir),
        "--base-url",
        args.backend_url,
    ]
    contract_run = _run_command("frontend_contract", contract_cmd, REPO_ROOT)
    contract_json_path = contract_dir / "watch_status_frontend_contract.json"
    contract_payload = _load_json(contract_json_path) if contract_json_path.exists() else {}

    quality_json_path = Path(args.quality_gate_json) if args.quality_gate_json else _find_latest("flower_jump_quality_gate_*/flower_jump_quality_gate.json")
    quality_payload = _load_json(quality_json_path) if quality_json_path and quality_json_path.exists() else {}

    browser_gate_dir = output_dir / "browser_evidence_gate"
    browser_gate_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_flower_jump_browser_evidence_gate.py"),
        "--output-dir",
        str(browser_gate_dir),
    ]
    if quality_json_path:
        browser_gate_cmd.extend(["--quality-gate-json", str(quality_json_path)])
    browser_gate_run = _run_command("browser_evidence_gate", browser_gate_cmd, REPO_ROOT)
    browser_gate_json_path = browser_gate_dir / "flower_jump_browser_evidence_gate.json"
    browser_gate_payload = _load_json(browser_gate_json_path) if browser_gate_json_path.exists() else {}

    upload_sim_dir = output_dir / "browser_upload_weight_simulation_gate"
    upload_sim_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run_browser_upload_weight_simulation_gate.py"),
        "--output-dir",
        str(upload_sim_dir),
    ]
    upload_sim_run = _run_command("browser_upload_weight_simulation_gate", upload_sim_cmd, REPO_ROOT)
    upload_sim_json_path = upload_sim_dir / "browser_upload_weight_simulation_gate.json"
    upload_sim_payload = _load_json(upload_sim_json_path) if upload_sim_json_path.exists() else {}

    readiness_dir = output_dir / "goal_readiness"
    readiness_cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "audit_flower_jump_goal_readiness.py"),
        "--output-dir",
        str(readiness_dir),
        "--watch-status-json",
        str(args.watch_status_json),
        "--backend-url",
        args.backend_url,
    ]
    if quality_json_path:
        readiness_cmd.extend(["--quality-gate-json", str(quality_json_path)])
    readiness_run = _run_command("goal_readiness", readiness_cmd, REPO_ROOT)
    readiness_json_path = readiness_dir / "flower_jump_goal_readiness_audit.json"
    readiness_payload = _load_json(readiness_json_path) if readiness_json_path.exists() else {}

    backend = _http_json(args.backend_url.rstrip("/") + "/api/status", timeout_sec=args.http_timeout_sec)
    score_upload_contract = _score_upload_contract(args.backend_url, timeout_sec=args.http_timeout_sec)
    backend_payload = backend.get("payload") or {}
    worker = backend_payload.get("worker") or {}
    scoring = backend_payload.get("scoring_module") or {}
    watch_payload = _load_json(Path(args.watch_status_json)) if Path(args.watch_status_json).exists() else {}
    watch_status = watch_payload.get("status") or {}
    target_summary = watch_status.get("target_summary") or {}
    readiness_summary = readiness_payload.get("readiness_summary") or {}
    browser_evidence = readiness_payload.get("browser_capture_evidence") or {}
    missing_words = [str(word) for word in (browser_evidence.get("missing_required_words") or []) if word]

    runtime = {
        "backend_ready": bool(worker.get("status") == "ready" and scoring.get("last_reload_error") in (None, "")),
        "worker_status": worker.get("status"),
        "worker_pid": (worker.get("process") or {}).get("pid") or (worker.get("ready_payload") or {}).get("pid"),
        "reload_count": scoring.get("reload_count"),
        "last_reload_error": scoring.get("last_reload_error"),
        "watcher_online": bool(watch_payload.get("watcher_pid")),
        "watch_event": watch_payload.get("event"),
        "watcher_pid": watch_payload.get("watcher_pid"),
        "target_count": target_summary.get("count"),
    }
    frontend_contract_passed = contract_payload.get("status") == "PASS"
    upload_weight_contract = _browser_upload_weight_contract(contract_payload)
    quality_passed = bool(quality_payload.get("passed"))
    browser_gate_passed = bool(browser_gate_payload.get("passed"))
    upload_sim_passed = bool(upload_sim_payload.get("passed"))
    runtime_ready = bool(runtime["backend_ready"] and runtime["watcher_online"])
    ready_for_retest = bool(runtime_ready and frontend_contract_passed and quality_passed)
    ready_for_retest = bool(ready_for_retest and score_upload_contract.get("ok"))
    ready_for_retest = bool(ready_for_retest and browser_gate_passed)
    ready_for_retest = bool(ready_for_retest and upload_sim_passed)

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "ready_for_retest": ready_for_retest,
        "next_step": _next_step(browser_evidence, DEFAULT_REQUIRED_WORDS),
        "runtime": runtime,
        "score_upload_contract": score_upload_contract,
        "browser_upload_weight_contract": upload_weight_contract,
        "goal_readiness": {
            "status_label": "READY_TO_COMPLETE" if readiness_payload.get("ready_to_complete") else "NOT_READY",
            "ready_to_complete": bool(readiness_payload.get("ready_to_complete")),
            "readiness_summary": readiness_summary,
            "browser_capture_evidence": browser_evidence,
        },
        "frontend_contract": {
            "status": contract_payload.get("status"),
            "failed_count": contract_payload.get("failed_count"),
            "warning_count": contract_payload.get("warning_count"),
        },
        "browser_evidence_gate": {
            "passed": browser_gate_payload.get("passed"),
            "case_count": len(browser_gate_payload.get("cases") or []),
            "cases": [
                {
                    "name": item.get("name"),
                    "passed": item.get("passed"),
                    "actual_ready": item.get("actual_ready"),
                    "actual_evidence_passed": item.get("actual_evidence_passed"),
                    "row_levels": item.get("row_levels"),
                }
                for item in (browser_gate_payload.get("cases") or [])
            ],
        },
        "browser_upload_weight_simulation_gate": {
            "passed": upload_sim_payload.get("passed"),
            "case_count": len(upload_sim_payload.get("cases") or []),
            "cases": [
                {
                    "name": item.get("name"),
                    "word": item.get("word"),
                    "passed": item.get("passed"),
                    "selected_count": item.get("selected_count"),
                    "target_frames": (item.get("plan") or {}).get("targetFrames")
                    if isinstance(item.get("plan"), dict)
                    else None,
                    "candidate_frames": (item.get("plan") or {}).get("candidateFrames")
                    if isinstance(item.get("plan"), dict)
                    else None,
                    "weights_range": item.get("weights_range"),
                    "selected_top_energy_count": item.get("selected_top_energy_count"),
                }
                for item in (upload_sim_payload.get("cases") or [])
            ],
        },
        "quality_gate": quality_payload,
        "sampling_guidance": _sampling_guidance(missing_words or DEFAULT_REQUIRED_WORDS),
        "commands": {
            "frontend_contract": contract_run,
            "browser_evidence_gate": browser_gate_run,
            "browser_upload_weight_simulation_gate": upload_sim_run,
            "goal_readiness": readiness_run,
        },
        "watch_status_json": str(args.watch_status_json),
        "frontend_contract_json": str(contract_json_path),
        "frontend_contract_md": str(contract_dir / "watch_status_frontend_contract.md"),
        "browser_evidence_gate_json": str(browser_gate_json_path),
        "browser_evidence_gate_md": str(browser_gate_dir / "flower_jump_browser_evidence_gate.md"),
        "browser_upload_weight_simulation_gate_json": str(upload_sim_json_path),
        "browser_upload_weight_simulation_gate_md": str(upload_sim_dir / "browser_upload_weight_simulation_gate.md"),
        "goal_readiness_json": str(readiness_json_path),
        "goal_readiness_md": str(readiness_dir / "flower_jump_goal_readiness_audit.md"),
        "quality_gate_json": str(quality_json_path) if quality_json_path else "",
        "quality_gate_md": str(quality_json_path.with_suffix(".md")) if quality_json_path else "",
    }
    json_path = output_dir / "flower_jump_retest_readiness.json"
    md_path = output_dir / "flower_jump_retest_readiness.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    payload["json_path"] = str(json_path)
    payload["md_path"] = str(md_path)
    return payload


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / f"flower_jump_retest_readiness_{stamp}"))
    parser.add_argument("--watch-status-json", default=str(DEFAULT_WATCH_STATUS_JSON))
    parser.add_argument("--quality-gate-json", default="")
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--http-timeout-sec", type=float, default=3.0)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    payload = build_report(args)
    print(f"已生成花/跳复测前就绪 JSON：{payload['json_path']}")
    print(f"已生成花/跳复测前就绪报告：{payload['md_path']}")
    print(f"复测就绪：{'PASS' if payload['ready_for_retest'] else 'CHECK_NEEDED'}")
    print(f"目标完成度：{payload['goal_readiness']['status_label']}")
    print(f"下一步：{payload['next_step']}")
    return 0 if payload["ready_for_retest"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

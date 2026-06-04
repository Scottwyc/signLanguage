#!/usr/bin/env python3
"""Stress-test flower/jump scoring against motion amplitude changes and blur.

Low FPS capture, camera motion blur, browser frame selection, and Holistic's
own temporal stability can smooth hand trajectories or slightly reduce/expand
the apparent motion amplitude. Mild amplitude changes should keep the core
flower/jump semantics scoreable. Temporal low-pass smoothing is kept as
diagnostic-only because it can remove genuine phase and opening evidence,
especially for flower.

This script edits cached skeleton sequences in memory only. It does not call
/api/score, run Holistic, move marker, or restart 5080.
"""

from __future__ import annotations

import argparse
import csv
import json
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

import numpy as np

from score_holistic_sequence_mvp import (
    DEFAULT_SEMANTIC_PROFILE_JSON,
    FrameFeature,
    SequenceData,
    _clone_frame,
    _clone_sequence,
    _hand_shape_feature,
    _profile_summary,
    load_semantic_profile,
    load_sequence,
    run_pair,
)


REPO_ROOT = Path("/data/WYC/signLanguage")
DEFAULT_TEMPLATE_ROOT = REPO_ROOT / "work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results"
DEFAULT_OUTPUT_BASE = REPO_ROOT / "work/generated/scoring_mvp_run3"
DEFAULT_BACKEND_URL = "http://127.0.0.1:5080"
DEFAULT_WORDS = ["花", "跳"]
COORD_GROUPS = ["pose", "left_hand", "right_hand", "face"]
HAND_GROUPS = ["left_hand", "right_hand"]


def _json_default(value: Any) -> Any:
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _load_backend_status(backend_url: str, timeout_sec: float) -> Dict[str, Any]:
    url = backend_url.rstrip("/") + "/api/status"
    try:
        with urllib.request.urlopen(url, timeout=timeout_sec) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return {"ok": True, "url": url, "payload": payload, "error": ""}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"ok": False, "url": url, "payload": {}, "error": str(exc)}


def _template_json(template_root: Path, word: str) -> Path:
    path = template_root / word / f"{word}_holistic_results.json"
    if not path.exists():
        raise FileNotFoundError(f"missing template json for {word}: {path}")
    return path


def _fmt(value: Any, digits: int = 3) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "-"


def _group_array(frame: FrameFeature, group: str) -> tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    if group not in frame.groups:
        return None, None
    sl = frame.groups[group]
    values = frame.vector[sl]
    masks = frame.mask[sl]
    if values.size % 3 != 0 or masks.size % 3 != 0:
        return None, None
    return values.reshape(-1, 3).copy(), masks.reshape(-1, 3).mean(axis=1) > 0.5


def _set_group(
    frame: FrameFeature,
    vector: np.ndarray,
    mask: np.ndarray,
    group: str,
    coords: np.ndarray,
    valid: np.ndarray,
) -> None:
    sl = frame.groups[group]
    vector[sl] = coords.reshape(-1)
    mask[sl] = np.repeat(valid.astype(np.float32), 3)
    shape_group = f"{group}_shape"
    if group not in HAND_GROUPS or shape_group not in frame.groups:
        return
    shape, shape_mask = _hand_shape_feature(coords, valid.astype(np.float32))
    shape_sl = frame.groups[shape_group]
    if vector[shape_sl].size == shape.size:
        vector[shape_sl] = shape.reshape(-1)
        mask[shape_sl] = shape_mask.reshape(-1)


def _collect_group(seq: SequenceData, group: str) -> tuple[List[Optional[np.ndarray]], List[Optional[np.ndarray]]]:
    coords_list: List[Optional[np.ndarray]] = []
    valid_list: List[Optional[np.ndarray]] = []
    for frame in seq.features:
        coords, valid = _group_array(frame, group)
        coords_list.append(coords)
        valid_list.append(valid)
    return coords_list, valid_list


def _smooth_group_arrays(
    coords_list: Sequence[Optional[np.ndarray]],
    valid_list: Sequence[Optional[np.ndarray]],
    weights: Sequence[float],
) -> List[Optional[np.ndarray]]:
    n = len(coords_list)
    radius = len(weights) // 2
    weights_arr = np.asarray(weights, dtype=np.float32)
    out: List[Optional[np.ndarray]] = []
    for t, coords in enumerate(coords_list):
        valid = valid_list[t]
        if coords is None or valid is None or not valid.any():
            out.append(coords.copy() if coords is not None else None)
            continue
        num = np.zeros_like(coords, dtype=np.float32)
        den = np.zeros((coords.shape[0], 1), dtype=np.float32)
        for k, weight in enumerate(weights_arr):
            src = t + k - radius
            if src < 0 or src >= n or weight <= 0:
                continue
            src_coords = coords_list[src]
            src_valid = valid_list[src]
            if src_coords is None or src_valid is None:
                continue
            ok = valid & src_valid
            if not ok.any():
                continue
            num[ok] += float(weight) * src_coords[ok]
            den[ok] += float(weight)
        item = coords.copy()
        ok = valid & (den[:, 0] > 1e-8)
        item[ok] = num[ok] / np.maximum(den[ok], 1e-8)
        out.append(item.astype(np.float32))
    return out


def _exponential_group_arrays(
    coords_list: Sequence[Optional[np.ndarray]],
    valid_list: Sequence[Optional[np.ndarray]],
    alpha: float,
) -> List[Optional[np.ndarray]]:
    out: List[Optional[np.ndarray]] = []
    previous: Optional[np.ndarray] = None
    previous_valid: Optional[np.ndarray] = None
    for coords, valid in zip(coords_list, valid_list):
        if coords is None or valid is None or not valid.any():
            out.append(coords.copy() if coords is not None else None)
            continue
        item = coords.copy()
        if previous is not None and previous_valid is not None:
            ok = valid & previous_valid
            item[ok] = float(alpha) * coords[ok] + (1.0 - float(alpha)) * previous[ok]
        out.append(item.astype(np.float32))
        previous = item
        previous_valid = valid.copy()
    return out


def _amplitude_group_arrays(
    coords_list: Sequence[Optional[np.ndarray]],
    valid_list: Sequence[Optional[np.ndarray]],
    factor: float,
) -> List[Optional[np.ndarray]]:
    valid_coords = [coords for coords, valid in zip(coords_list, valid_list) if coords is not None and valid is not None and valid.any()]
    if not valid_coords:
        return [coords.copy() if coords is not None else None for coords in coords_list]
    shape = valid_coords[0].shape
    center = np.zeros(shape, dtype=np.float32)
    counts = np.zeros((shape[0], 1), dtype=np.float32)
    for coords, valid in zip(coords_list, valid_list):
        if coords is None or valid is None or coords.shape != shape:
            continue
        center[valid] += coords[valid]
        counts[valid] += 1.0
    center = np.divide(center, np.maximum(counts, 1.0), out=np.zeros_like(center), where=counts > 0)
    out: List[Optional[np.ndarray]] = []
    for coords, valid in zip(coords_list, valid_list):
        if coords is None or valid is None:
            out.append(coords.copy() if coords is not None else None)
            continue
        item = coords.copy()
        ok = valid & (counts[:, 0] > 0)
        item[ok] = center[ok] + float(factor) * (coords[ok] - center[ok])
        out.append(item.astype(np.float32))
    return out


def _apply_group_series(
    seq: SequenceData,
    name: str,
    *,
    groups: Sequence[str],
    transform: Callable[[Sequence[Optional[np.ndarray]], Sequence[Optional[np.ndarray]]], List[Optional[np.ndarray]]],
) -> SequenceData:
    transformed: Dict[str, List[Optional[np.ndarray]]] = {}
    valid_by_group: Dict[str, List[Optional[np.ndarray]]] = {}
    for group in groups:
        coords_list, valid_list = _collect_group(seq, group)
        transformed[group] = transform(coords_list, valid_list)
        valid_by_group[group] = list(valid_list)

    items: List[FrameFeature] = []
    for idx, frame in enumerate(seq.features):
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        presence = dict(frame.presence)
        for group in groups:
            coords = transformed[group][idx]
            valid = valid_by_group[group][idx]
            if coords is None or valid is None:
                continue
            _set_group(frame, vector, mask, group, coords, valid)
            presence[group] = bool(valid.any())
        item = _clone_frame(frame, vector=vector, mask=mask)
        item.presence = presence
        items.append(item)
    return _clone_sequence(seq, name, items)


QueryFactory = Callable[[SequenceData], SequenceData]


def _spec(
    variant: str,
    kind: str,
    query: QueryFactory,
    rationale: str,
    min_score: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": kind,
        "query": query,
        "min_score": min_score,
        "gated": kind == "positive",
        "rationale": rationale,
    }


def _smooth(seq: SequenceData, name: str, groups: Sequence[str], weights: Sequence[float]) -> SequenceData:
    return _apply_group_series(
        seq,
        name,
        groups=groups,
        transform=lambda coords, valid: _smooth_group_arrays(coords, valid, weights),
    )


def _exponential(seq: SequenceData, name: str, groups: Sequence[str], alpha: float) -> SequenceData:
    return _apply_group_series(
        seq,
        name,
        groups=groups,
        transform=lambda coords, valid: _exponential_group_arrays(coords, valid, alpha),
    )


def _amplitude(seq: SequenceData, name: str, groups: Sequence[str], factor: float) -> SequenceData:
    return _apply_group_series(
        seq,
        name,
        groups=groups,
        transform=lambda coords, valid: _amplitude_group_arrays(coords, valid, factor),
    )


def _variant_specs(min_score: float) -> List[Dict[str, Any]]:
    return [
        _spec(
            "self",
            "positive",
            lambda seq: _clone_sequence(seq, "self", seq.features),
            "同一骨架重算基线。",
            min_score=95.0,
        ),
        _spec(
            "hand_motion_blur_3tap",
            "diagnostic",
            lambda seq: _smooth(seq, "hand_motion_blur_3tap", HAND_GROUPS, [0.20, 0.60, 0.20]),
            "手部轨迹 3 帧低通会削弱花的 opening 动态，只记录诊断边界。",
        ),
        _spec(
            "all_keypoint_blur_3tap_light",
            "diagnostic",
            lambda seq: _smooth(seq, "all_keypoint_blur_3tap_light", COORD_GROUPS, [0.15, 0.70, 0.15]),
            "全身关键点轻度 3 帧平滑，作为模糊/低通诊断边界。",
        ),
        _spec(
            "hand_motion_blur_5tap_light",
            "diagnostic",
            lambda seq: _smooth(seq, "hand_motion_blur_5tap_light", HAND_GROUPS, [0.08, 0.17, 0.50, 0.17, 0.08]),
            "手部轨迹 5 帧低通会抹掉短时手形变化，只记录诊断边界。",
        ),
        _spec(
            "hand_exponential_smooth_alpha_0.70",
            "diagnostic",
            lambda seq: _exponential(seq, "hand_exponential_smooth_alpha_0.70", HAND_GROUPS, 0.70),
            "手部轨迹指数平滑可能滞后手形 opening，只记录诊断边界。",
        ),
        _spec(
            "all_keypoint_motion_amplitude_0.90",
            "positive",
            lambda seq: _amplitude(seq, "all_keypoint_motion_amplitude_0.90", COORD_GROUPS, 0.90),
            "全身关键点运动幅度轻微衰减到 90%，模拟保守动作或模型轨迹收缩。",
            min_score=min_score,
        ),
        _spec(
            "all_keypoint_motion_amplitude_1.10",
            "positive",
            lambda seq: _amplitude(seq, "all_keypoint_motion_amplitude_1.10", COORD_GROUPS, 1.10),
            "全身关键点运动幅度轻微增强到 110%，模拟动作更夸张或模型轨迹外扩。",
            min_score=min_score,
        ),
        _spec(
            "hand_motion_amplitude_0.85",
            "positive",
            lambda seq: _amplitude(seq, "hand_motion_amplitude_0.85", HAND_GROUPS, 0.85),
            "手部运动幅度轻微衰减到 85%，模拟运动模糊或保守动作。",
            min_score=min_score,
        ),
        _spec(
            "hand_motion_amplitude_1.15",
            "positive",
            lambda seq: _amplitude(seq, "hand_motion_amplitude_1.15", HAND_GROUPS, 1.15),
            "手部运动幅度轻微增强到 115%，模拟动作更夸张或模型轨迹外扩。",
            min_score=min_score,
        ),
        _spec(
            "hand_motion_blur_5tap_heavy_diagnostic",
            "diagnostic",
            lambda seq: _smooth(seq, "hand_motion_blur_5tap_heavy_diagnostic", HAND_GROUPS, [0.16, 0.22, 0.24, 0.22, 0.16]),
            "更强手部轨迹低通，只记录诊断边界。",
        ),
        _spec(
            "hand_exponential_smooth_alpha_0.35_diagnostic",
            "diagnostic",
            lambda seq: _exponential(seq, "hand_exponential_smooth_alpha_0.35_diagnostic", HAND_GROUPS, 0.35),
            "强指数平滑会滞后并削弱动作相位，只记录诊断边界。",
        ),
        _spec(
            "hand_motion_amplitude_0.55_diagnostic",
            "diagnostic",
            lambda seq: _amplitude(seq, "hand_motion_amplitude_0.55_diagnostic", HAND_GROUPS, 0.55),
            "手部运动幅度严重衰减，可能需要重采，只记录诊断边界。",
        ),
        _spec(
            "hand_motion_amplitude_1.60_diagnostic",
            "diagnostic",
            lambda seq: _amplitude(seq, "hand_motion_amplitude_1.60_diagnostic", HAND_GROUPS, 1.60),
            "手部运动幅度过度放大，作为过度动作边界诊断。",
        ),
    ]


def _run_word(
    word: str,
    template_root: Path,
    semantic_profile_json: Path,
    feature_mode: str,
    min_score: float,
) -> Dict[str, Any]:
    standard_json = _template_json(template_root, word)
    standard = load_sequence(standard_json, feature_mode, force_bbox=False)
    profile = load_semantic_profile(word, semantic_profile_json)
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(min_score):
        query = spec["query"](standard)
        result = run_pair(standard, query, semantic_profile=profile, enable_cross_check=False)
        score_scale = result.get("score_scale") or {}
        row = {
            "variant": spec["variant"],
            "kind": spec["kind"],
            "gated": bool(spec["gated"]),
            "min_score": spec.get("min_score"),
            "rationale": spec["rationale"],
            "score": float(result["prototype_score"]),
            "dtw_distance": float(result["dtw_distance"]),
            "normalized_distance": float(result["normalized_distance"]),
            "query_length": len(query.features),
            "alignment_policy": result.get("alignment_policy"),
            "capture_quality": score_scale.get("capture_quality"),
            "semantic_floor": score_scale.get("semantic_floor"),
        }
        row["passed"] = row["kind"] != "positive" or float(row["score"]) >= float(row["min_score"])
        rows.append(row)
    positive_rows = [row for row in rows if row["kind"] == "positive"]
    diagnostic_rows = [row for row in rows if row["kind"] == "diagnostic"]
    weakest_positive = min(positive_rows, key=lambda row: float(row["score"])) if positive_rows else None
    weakest_diagnostic = min(diagnostic_rows, key=lambda row: float(row["score"])) if diagnostic_rows else None
    return {
        "word": word,
        "standard_json": str(standard_json),
        "standard_length": len(standard.features),
        "semantic_profile": _profile_summary(profile),
        "min_required_score": min_score,
        "gate_pass": all(bool(row["passed"]) for row in positive_rows),
        "weakest_positive_score": float(weakest_positive["score"]) if weakest_positive else None,
        "weakest_positive_variant": weakest_positive["variant"] if weakest_positive else "",
        "weakest_diagnostic_score": float(weakest_diagnostic["score"]) if weakest_diagnostic else None,
        "weakest_diagnostic_variant": weakest_diagnostic["variant"] if weakest_diagnostic else "",
        "variants": rows,
    }


def _write_rows_csv(path: Path, results: Sequence[Dict[str, Any]]) -> None:
    fields = [
        "word",
        "variant",
        "kind",
        "gated",
        "passed",
        "score",
        "min_score",
        "dtw_distance",
        "normalized_distance",
        "query_length",
        "alignment_mode",
        "capture_quality_status",
        "capture_quality_reason",
        "semantic_floor_source",
        "semantic_floor_reason",
        "rationale",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in results:
            for row in item["variants"]:
                quality = row.get("capture_quality") or {}
                floor = row.get("semantic_floor") or {}
                policy = row.get("alignment_policy") or {}
                writer.writerow(
                    {
                        "word": item["word"],
                        "variant": row.get("variant"),
                        "kind": row.get("kind"),
                        "gated": row.get("gated"),
                        "passed": row.get("passed"),
                        "score": row.get("score"),
                        "min_score": row.get("min_score"),
                        "dtw_distance": row.get("dtw_distance"),
                        "normalized_distance": row.get("normalized_distance"),
                        "query_length": row.get("query_length"),
                        "alignment_mode": policy.get("mode"),
                        "capture_quality_status": quality.get("status"),
                        "capture_quality_reason": quality.get("reason"),
                        "semantic_floor_source": floor.get("source"),
                        "semantic_floor_reason": floor.get("reason"),
                        "rationale": row.get("rationale"),
                    }
                )


def _build_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# 花/跳运动模糊与轨迹平滑鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，在基础骨架坐标层合成手部/全身运动幅度变化，并把轨迹低通/指数平滑作为诊断；手部坐标变化后重算 `left_hand_shape/right_hand_shape`；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：手部/全身轨迹幅度轻微变化时，`花/跳` 仍保持正常或边界以上得分；低通平滑和重度幅度异常只作为诊断边界，因为它们可能抹掉真实语义相位证据。",
        "",
    ]
    backend = payload.get("backend_status") or {}
    if backend.get("ok"):
        data = backend.get("payload") or {}
        worker = data.get("worker") or {}
        scoring = data.get("scoring_module") or {}
        lines.append(
            f"- 5080 状态：worker=`{worker.get('status')}`，worker_pid=`{((worker.get('ready_payload') or {}).get('pid'))}`，"
            f"reload_count=`{scoring.get('reload_count')}`，last_reload_error=`{scoring.get('last_reload_error')}`"
        )
    else:
        lines.append(f"- 5080 状态：读取失败 `{backend.get('error') or '-'}`")
    lines.extend(["", "## 结论", "", f"- 综合状态：`{'PASS' if payload['passed'] else 'FAIL'}`", ""])
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向幅度变体 | 诊断最低分 | 最弱诊断平滑/模糊 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for item in payload["results"]:
        lines.append(
            f"| {item['word']} | {'PASS' if item['gate_pass'] else 'FAIL'} | "
            f"{_fmt(item['weakest_positive_score'])} | {item['weakest_positive_variant']} | "
            f"{_fmt(item['weakest_diagnostic_score'])} | {item['weakest_diagnostic_variant']} | "
            f"{_fmt(item['min_required_score'])} |"
        )
    lines.append("")
    lines.append("## 分项明细")
    for item in payload["results"]:
        lines.extend(["", f"### {item['word']}", "", f"- 标准序列：`{item['standard_json']}`", ""])
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | normalized_distance | alignment | capture_quality | semantic_floor | 说明 |")
        lines.append("|---|---|---|---:|---|---:|---|---|---|---|")
        for row in sorted(item["variants"], key=lambda x: (x["kind"], float(x["score"]))):
            quality = row.get("capture_quality") or {}
            floor = row.get("semantic_floor") or {}
            policy = row.get("alignment_policy") or {}
            if row["kind"] == "positive":
                threshold = f">= {row.get('min_score')}"
                status = "PASS" if row["passed"] else "FAIL"
            else:
                threshold = "diagnostic"
                status = "DIAG"
            lines.append(
                f"| {row['variant']} | {row['kind']} | {status} | {_fmt(row['score'])} | "
                f"{threshold} | {_fmt(row['normalized_distance'], 6)} | {policy.get('mode') or '-'} | "
                f"{quality.get('status') or '-'} | {floor.get('source') or '-'} | {row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 正向变体覆盖 10%-15% 左右的全身/手部运动幅度变化。",
            "- 低通平滑或严重幅度压缩可能真实移除语义相位和花的 opening 证据，因此只作为诊断，不作为正常采集通过条件。",
            "- 该门是合成轨迹压力测试，不能替代正式网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run motion-blur robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_motion_blur_robustness_gate_current"))
    parser.add_argument("--words", nargs="+", default=DEFAULT_WORDS)
    parser.add_argument("--feature-mode", choices=["auto", "landmark", "bbox"], default="auto")
    parser.add_argument("--min-score", type=float, default=70.0)
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--status-timeout-sec", type=float, default=3.0)
    args = parser.parse_args(argv)

    template_root = Path(args.template_root)
    semantic_profile_json = Path(args.semantic_profile_json)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = [
        _run_word(
            word=word,
            template_root=template_root,
            semantic_profile_json=semantic_profile_json,
            feature_mode=args.feature_mode,
            min_score=args.min_score,
        )
        for word in args.words
    ]
    backend_status = _load_backend_status(args.backend_url, args.status_timeout_sec)
    passed = all(bool(item["gate_pass"]) for item in results)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "claim_policy": "synthetic motion-blur robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "min_score": args.min_score,
        "backend_status": backend_status,
        "passed": passed,
        "results": results,
    }

    json_path = output_dir / "flower_jump_motion_blur_robustness_gate.json"
    md_path = output_dir / "flower_jump_motion_blur_robustness_gate.md"
    csv_path = output_dir / "flower_jump_motion_blur_robustness_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳运动模糊鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳运动模糊鲁棒性报告：{md_path}")
    print(f"已生成花/跳运动模糊鲁棒性 CSV：{csv_path}")
    print(f"综合状态：{'PASS' if passed else 'FAIL'}")
    for item in results:
        print(
            f"- {item['word']}: {'PASS' if item['gate_pass'] else 'FAIL'} "
            f"positive_min={_fmt(item['weakest_positive_score'])} "
            f"weakest={item['weakest_positive_variant']} "
            f"diagnostic_min={_fmt(item['weakest_diagnostic_score'])}"
        )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

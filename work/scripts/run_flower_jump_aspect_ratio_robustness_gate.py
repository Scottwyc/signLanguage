#!/usr/bin/env python3
"""Stress-test flower/jump scoring against camera aspect-ratio distortion.

Browser camera capture or canvas resizing can introduce mild non-uniform x/y
stretching if the source aspect ratio is mishandled. Mild image-plane aspect
distortion should keep flower/jump scoreable; extreme distortion is recorded
as a diagnostic boundary, not as a normal capture case.

This script edits cached skeleton sequences in memory only. It does not call
/api/score, run Holistic, move marker, or restart 5080.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from run_flower_jump_landmark_noise_robustness_gate import (
    _fmt,
    _hand_array,
    _json_default,
    _load_backend_status,
    _set_hand_group,
)
from run_flower_jump_mirror_robustness_gate import _strip_to_base_groups, _template_json
from score_holistic_sequence_mvp import (
    DEFAULT_SEMANTIC_PROFILE_JSON,
    FrameFeature,
    SequenceData,
    _clone_frame,
    _profile_summary,
    _sequence_with_relative_motion_features,
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
HAND_GROUPS = {"left_hand", "right_hand"}


def _group_coords_and_valid(frame: FrameFeature, group: str) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    if group not in frame.groups:
        return None, None
    sl = frame.groups[group]
    values = frame.vector[sl]
    masks = frame.mask[sl]
    if values.size % 3 != 0 or masks.size % 3 != 0:
        return None, None
    return values.reshape(-1, 3).copy(), masks.reshape(-1, 3).mean(axis=1) > 0.5


def _set_coord_group(frame: FrameFeature, vector: np.ndarray, group: str, coords: np.ndarray) -> None:
    if group not in frame.groups:
        return
    sl = frame.groups[group]
    if vector[sl].size == coords.size:
        vector[sl] = coords.reshape(-1)


def _visible_center(seq: SequenceData) -> np.ndarray:
    points: List[np.ndarray] = []
    for frame in seq.features:
        for group in COORD_GROUPS:
            coords, valid = _group_coords_and_valid(frame, group)
            if coords is None or valid is None or not valid.any():
                continue
            points.append(coords[valid, :2])
    if not points:
        return np.zeros(2, dtype=np.float32)
    return np.concatenate(points, axis=0).mean(axis=0).astype(np.float32)


def _aspect_sequence(
    seq: SequenceData,
    name: str,
    *,
    sx: float,
    sy: float,
    profile: Any,
) -> SequenceData:
    base = _strip_to_base_groups(seq)
    center = _visible_center(base)
    items: List[FrameFeature] = []
    for frame in base.features:
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        presence = dict(frame.presence)
        for group in COORD_GROUPS:
            coords, valid = _group_coords_and_valid(frame, group)
            if coords is None or valid is None or not valid.any():
                continue
            coords = coords.copy()
            coords[valid, 0] = center[0] + (coords[valid, 0] - center[0]) * float(sx)
            coords[valid, 1] = center[1] + (coords[valid, 1] - center[1]) * float(sy)
            if group in HAND_GROUPS:
                _set_hand_group(frame, vector, mask, group, coords, valid)
                presence[group] = bool(valid.any())
            else:
                _set_coord_group(frame, vector, group, coords)
        item = _clone_frame(frame, vector=vector, mask=mask)
        item.presence = presence
        items.append(item)
    transformed = SequenceData(
        source=f"{base.source}::{name}",
        mode=base.mode,
        fps=base.fps,
        total_frames=base.total_frames,
        features=items,
    )
    return _sequence_with_relative_motion_features(transformed, profile)


def _variant_specs(min_score: float) -> List[Dict[str, Any]]:
    return [
        {
            "variant": "self_recomputed",
            "kind": "positive",
            "sx": 1.0,
            "sy": 1.0,
            "min_score": 95.0,
            "rationale": "标准序列剥离基础组后重建 motion/relation/hand-shape，应保持近满分。",
        },
        {
            "variant": "aspect_x1.10_y0.92",
            "kind": "positive",
            "sx": 1.10,
            "sy": 0.92,
            "min_score": min_score,
            "rationale": "轻微横向拉宽、纵向压缩，模拟 canvas 或摄像头宽高比轻度失配。",
        },
        {
            "variant": "aspect_x0.92_y1.10",
            "kind": "positive",
            "sx": 0.92,
            "sy": 1.10,
            "min_score": min_score,
            "rationale": "轻微横向压缩、纵向拉高，模拟反向宽高比轻度失配。",
        },
        {
            "variant": "aspect_x1.18_y0.85",
            "kind": "positive",
            "sx": 1.18,
            "sy": 0.85,
            "min_score": min_score,
            "rationale": "中度横向拉宽、纵向压缩，仍应保持可评分。",
        },
        {
            "variant": "aspect_x0.85_y1.18",
            "kind": "positive",
            "sx": 0.85,
            "sy": 1.18,
            "min_score": min_score,
            "rationale": "中度横向压缩、纵向拉高，仍应保持可评分。",
        },
        {
            "variant": "diagnostic_x1.35_y0.70",
            "kind": "diagnostic",
            "sx": 1.35,
            "sy": 0.70,
            "rationale": "强横向拉宽和纵向压缩，只记录诊断边界。",
        },
        {
            "variant": "diagnostic_x0.70_y1.35",
            "kind": "diagnostic",
            "sx": 0.70,
            "sy": 1.35,
            "rationale": "强横向压缩和纵向拉高，只记录诊断边界。",
        },
        {
            "variant": "diagnostic_x1.55_y0.55",
            "kind": "diagnostic",
            "sx": 1.55,
            "sy": 0.55,
            "rationale": "极端横向拉宽，会真实破坏跳的方向关系，只记录诊断。",
        },
        {
            "variant": "diagnostic_x0.55_y1.55",
            "kind": "diagnostic",
            "sx": 0.55,
            "sy": 1.55,
            "rationale": "极端横向压缩和纵向拉高，只记录诊断。",
        },
    ]


def _run_word(
    word: str,
    template_root: Path,
    semantic_profile_json: Path,
    feature_mode: str,
    min_score: float,
) -> Dict[str, Any]:
    standard_json = _template_json(template_root, word)
    loaded_standard = load_sequence(standard_json, feature_mode, force_bbox=False)
    profile = load_semantic_profile(word, semantic_profile_json)
    standard = _aspect_sequence(loaded_standard, "standard_base", sx=1.0, sy=1.0, profile=profile)
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(min_score):
        query = _aspect_sequence(
            loaded_standard,
            str(spec["variant"]),
            sx=float(spec["sx"]),
            sy=float(spec["sy"]),
            profile=profile,
        )
        result = run_pair(standard, query, semantic_profile=profile, enable_cross_check=False)
        score_scale = result.get("score_scale") or {}
        row = {
            **spec,
            "score": float(result["prototype_score"]),
            "dtw_distance": float(result["dtw_distance"]),
            "normalized_distance": float(result["normalized_distance"]),
            "alignment_policy": result.get("alignment_policy"),
            "capture_quality": score_scale.get("capture_quality"),
            "semantic_floor": score_scale.get("semantic_floor"),
            "score_scale_reason": score_scale.get("reason"),
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
        "passed",
        "score",
        "min_score",
        "sx",
        "sy",
        "dtw_distance",
        "normalized_distance",
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
                        "passed": row.get("passed"),
                        "score": row.get("score"),
                        "min_score": row.get("min_score"),
                        "sx": row.get("sx"),
                        "sy": row.get("sy"),
                        "dtw_distance": row.get("dtw_distance"),
                        "normalized_distance": row.get("normalized_distance"),
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
        "# 花/跳宽高比失真鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，先剥离基础骨架组，对整幅骨架做 x/y 非等比拉伸，并重建 motion/relation/hand-shape 特征；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：轻中度宽高比失真仍可评分；极端失真只记录诊断边界。",
        "",
    ]
    backend = payload.get("backend_status") or {}
    if backend.get("ok"):
        data = backend.get("payload") or {}
        worker = data.get("worker") or {}
        scoring = data.get("scoring_module") or {}
        process = worker.get("process") or {}
        lines.append(
            f"- 后端：`{backend.get('url')}`，worker=`{worker.get('status')}`，"
            f"pid=`{process.get('pid')}`，scoring reload=`{scoring.get('reload_count')}`，"
            f"last_reload_error=`{scoring.get('last_reload_error')}`"
        )
    else:
        lines.append(f"- 后端状态读取失败：`{backend.get('error')}`")
    lines.append("")
    lines.append("## 汇总")
    lines.append("")
    lines.append(f"- 总体：`{'PASS' if payload.get('passed') else 'FAIL'}`")
    lines.append("")
    lines.append("| 词条 | 状态 | 正向最低分 | 最弱正向宽高比 | 诊断最低分 | 最弱诊断宽高比 |")
    lines.append("|---|---|---:|---|---:|---|")
    for item in payload.get("results") or []:
        lines.append(
            f"| {item.get('word')} | {'PASS' if item.get('gate_pass') else 'FAIL'} | "
            f"{_fmt(item.get('weakest_positive_score'))} | {item.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(item.get('weakest_diagnostic_score'))} | {item.get('weakest_diagnostic_variant') or '-'} |"
        )
    lines.append("")
    for item in payload.get("results") or []:
        lines.append(f"## {item.get('word')} 明细")
        lines.append("")
        lines.append("| 变体 | 类型 | 状态 | 分数 | sx | sy | 质量 | 语义 floor | 说明 |")
        lines.append("|---|---|---|---:|---:|---:|---|---|---|")
        for row in item.get("variants") or []:
            quality = row.get("capture_quality") or {}
            floor = row.get("semantic_floor") or {}
            lines.append(
                f"| {row.get('variant')} | {row.get('kind')} | {'PASS' if row.get('passed') else 'FAIL'} | "
                f"{_fmt(row.get('score'))} | {_fmt(row.get('sx'), 2)} | {_fmt(row.get('sy'), 2)} | "
                f"{quality.get('status') or '-'}:{quality.get('reason') or '-'} | "
                f"{floor.get('source') or '-'}:{floor.get('reason') or '-'} | "
                f"{row.get('rationale')} |"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def _default_output_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return DEFAULT_OUTPUT_BASE / f"flower_jump_aspect_ratio_robustness_gate_{stamp}"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run flower/jump aspect-ratio robustness gate.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--backend-timeout-sec", type=float, default=5.0)
    parser.add_argument("--feature-mode", choices=["auto", "landmark", "bbox"], default="auto")
    parser.add_argument("--min-score", type=float, default=75.0)
    parser.add_argument("--words", nargs="+", default=DEFAULT_WORDS)
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir) if args.output_dir else _default_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    template_root = Path(args.template_root)
    semantic_profile_json = Path(args.semantic_profile_json)
    results = [
        _run_word(word, template_root, semantic_profile_json, args.feature_mode, args.min_score)
        for word in args.words
    ]
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "claim_policy": "engineering robustness gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_url": args.backend_url,
        "backend_status": _load_backend_status(args.backend_url, args.backend_timeout_sec),
        "min_score": args.min_score,
        "results": results,
        "passed": all(bool(item.get("gate_pass")) for item in results),
    }
    json_path = output_dir / "flower_jump_aspect_ratio_robustness_gate.json"
    md_path = output_dir / "flower_jump_aspect_ratio_robustness_gate.md"
    csv_path = output_dir / "flower_jump_aspect_ratio_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    _write_rows_csv(csv_path, results)
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    print(f"aspect ratio gate: {'PASS' if payload['passed'] else 'FAIL'}")
    print(f"json: {json_path}")
    print(f"md: {md_path}")
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

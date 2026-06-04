#!/usr/bin/env python3
"""Stress-test flower/jump scoring against pose and camera-like perturbations.

The user-facing issue behind this gate is that a seated webcam user can have a
very different torso and global hand position from the standing demo. For
hand-dominant signs such as flower and jump, these non-semantic changes should
not dominate the score. This script creates positive skeleton variants from
the cached templates and verifies that scores remain in a normal/borderline
range while reusing the current scorer unchanged.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
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
HAND_GROUPS = ["left_hand", "right_hand"]
POSE_LIKE_GROUPS = ["pose", "face", "left_hand", "right_hand"]


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


def _group_coords(frame: FrameFeature, group: str) -> Optional[np.ndarray]:
    if group not in frame.groups:
        return None
    values = frame.vector[frame.groups[group]]
    if values.size % 3 != 0:
        return None
    return values.reshape(-1, 3).copy()


def _group_mask(frame: FrameFeature, group: str) -> Optional[np.ndarray]:
    if group not in frame.groups:
        return None
    mask = frame.mask[frame.groups[group]]
    if mask.size % 3 != 0:
        return None
    return mask.reshape(-1, 3).mean(axis=1) > 0.5


def _set_group_coords(frame: FrameFeature, vector: np.ndarray, group: str, coords: np.ndarray) -> None:
    if group not in frame.groups:
        return
    sl = frame.groups[group]
    if vector[sl].size != coords.size:
        return
    vector[sl] = coords.reshape(-1)


def _visible_center(frame: FrameFeature, groups: Sequence[str]) -> np.ndarray:
    points: List[np.ndarray] = []
    for group in groups:
        coords = _group_coords(frame, group)
        mask = _group_mask(frame, group)
        if coords is None or mask is None or not mask.any():
            continue
        points.append(coords[mask, :2])
    if not points:
        return np.zeros(2, dtype=np.float32)
    merged = np.concatenate(points, axis=0)
    return merged.mean(axis=0).astype(np.float32)


def _translate_groups(seq: SequenceData, name: str, groups: Sequence[str], dx: float, dy: float, dz: float = 0.0) -> SequenceData:
    delta = np.asarray([dx, dy, dz], dtype=np.float32)
    items: List[FrameFeature] = []
    for frame in seq.features:
        vector = frame.vector.copy()
        for group in groups:
            coords = _group_coords(frame, group)
            mask = _group_mask(frame, group)
            if coords is None or mask is None:
                continue
            coords[mask] = coords[mask] + delta
            _set_group_coords(frame, vector, group, coords)
        items.append(_clone_frame(frame, vector=vector))
    return _clone_sequence(seq, name, items)


def _scale_hand_local(seq: SequenceData, name: str, factor: float) -> SequenceData:
    items: List[FrameFeature] = []
    for frame in seq.features:
        vector = frame.vector.copy()
        for group in HAND_GROUPS:
            coords = _group_coords(frame, group)
            mask = _group_mask(frame, group)
            if coords is None or mask is None or not mask.any():
                continue
            center = coords[0].copy() if mask[0] else coords[mask].mean(axis=0)
            coords[mask] = center + factor * (coords[mask] - center)
            _set_group_coords(frame, vector, group, coords)
        items.append(_clone_frame(frame, vector=vector))
    return _clone_sequence(seq, name, items)


def _rotate_hands(seq: SequenceData, name: str, degrees: float) -> SequenceData:
    theta = math.radians(degrees)
    rot = np.asarray(
        [[math.cos(theta), -math.sin(theta)], [math.sin(theta), math.cos(theta)]],
        dtype=np.float32,
    )
    items: List[FrameFeature] = []
    for frame in seq.features:
        vector = frame.vector.copy()
        center = _visible_center(frame, HAND_GROUPS)
        for group in HAND_GROUPS:
            coords = _group_coords(frame, group)
            mask = _group_mask(frame, group)
            if coords is None or mask is None or not mask.any():
                continue
            xy = coords[mask, :2] - center
            coords[mask, :2] = xy @ rot.T + center
            _set_group_coords(frame, vector, group, coords)
        items.append(_clone_frame(frame, vector=vector))
    return _clone_sequence(seq, name, items)


def _jitter_hands(seq: SequenceData, name: str, scale: float, seed: int) -> SequenceData:
    rng = np.random.default_rng(seed)
    items: List[FrameFeature] = []
    for frame in seq.features:
        vector = frame.vector.copy()
        for group in HAND_GROUPS:
            coords = _group_coords(frame, group)
            mask = _group_mask(frame, group)
            if coords is None or mask is None or not mask.any():
                continue
            noise = rng.normal(0.0, scale, size=coords.shape).astype(np.float32)
            noise[:, 2] *= 0.35
            coords[mask] = coords[mask] + noise[mask]
            _set_group_coords(frame, vector, group, coords)
        items.append(_clone_frame(frame, vector=vector))
    return _clone_sequence(seq, name, items)


def _compress_pose_only(seq: SequenceData, name: str) -> SequenceData:
    """Simulate a seated/closer torso without changing hand semantics."""

    items: List[FrameFeature] = []
    for frame in seq.features:
        vector = frame.vector.copy()
        for group in ["pose", "face"]:
            coords = _group_coords(frame, group)
            mask = _group_mask(frame, group)
            if coords is None or mask is None or not mask.any():
                continue
            center = coords[mask].mean(axis=0)
            coords[mask, 0] = center[0] + 0.80 * (coords[mask, 0] - center[0])
            coords[mask, 1] = center[1] + 0.55 * (coords[mask, 1] - center[1]) + 0.70
            coords[mask, 2] = center[2] + 0.75 * (coords[mask, 2] - center[2])
            _set_group_coords(frame, vector, group, coords)
        items.append(_clone_frame(frame, vector=vector))
    return _clone_sequence(seq, name, items)


def _variant_builders() -> Dict[str, Callable[[SequenceData], SequenceData]]:
    return {
        "self": lambda seq: _clone_sequence(seq, "self", seq.features),
        "hands_shift_down": lambda seq: _translate_groups(seq, "hands_shift_down", HAND_GROUPS, 0.00, 0.55),
        "hands_shift_left": lambda seq: _translate_groups(seq, "hands_shift_left", HAND_GROUPS, -0.55, 0.00),
        "hands_shift_diag": lambda seq: _translate_groups(seq, "hands_shift_diag", HAND_GROUPS, 0.38, -0.42),
        "whole_person_shift": lambda seq: _translate_groups(seq, "whole_person_shift", POSE_LIKE_GROUPS, 0.45, 0.35),
        "pose_sitting_compress": lambda seq: _compress_pose_only(seq, "pose_sitting_compress"),
        "hand_local_scale_0.90": lambda seq: _scale_hand_local(seq, "hand_local_scale_0.90", 0.90),
        "hand_local_scale_1.10": lambda seq: _scale_hand_local(seq, "hand_local_scale_1.10", 1.10),
        "hands_rotate_10deg": lambda seq: _rotate_hands(seq, "hands_rotate_10deg", 10.0),
        "hand_jitter_small": lambda seq: _jitter_hands(seq, "hand_jitter_small", 0.020, 20260603),
    }


def _fmt(value: Any, digits: int = 3) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "-"


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
    for variant_name, builder in _variant_builders().items():
        query = builder(standard)
        result = run_pair(standard, query, semantic_profile=profile)
        rows.append(
            {
                "variant": variant_name,
                "score": float(result["prototype_score"]),
                "dtw_distance": float(result["dtw_distance"]),
                "normalized_distance": float(result["normalized_distance"]),
                "query_length": len(query.features),
                "capture_quality": (result.get("score_scale") or {}).get("capture_quality"),
                "semantic_floor": (result.get("score_scale") or {}).get("semantic_floor"),
                "alignment_policy": result.get("alignment_policy"),
            }
        )
    weakest = min(rows, key=lambda row: float(row["score"]))
    return {
        "word": word,
        "standard_json": str(standard_json),
        "standard_length": len(standard.features),
        "semantic_profile": _profile_summary(profile),
        "min_required_score": min_score,
        "min_observed_score": float(weakest["score"]),
        "weakest_variant": weakest["variant"],
        "gate_pass": float(weakest["score"]) >= min_score,
        "variants": rows,
    }


def _write_rows_csv(path: Path, results: Sequence[Dict[str, Any]]) -> None:
    fields = [
        "word",
        "variant",
        "score",
        "dtw_distance",
        "normalized_distance",
        "query_length",
        "alignment_policy",
        "capture_quality_status",
        "semantic_floor_source",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in results:
            for row in item["variants"]:
                capture_quality = row.get("capture_quality") or {}
                semantic_floor = row.get("semantic_floor") or {}
                writer.writerow(
                    {
                        "word": item["word"],
                        "variant": row.get("variant"),
                        "score": row.get("score"),
                        "dtw_distance": row.get("dtw_distance"),
                        "normalized_distance": row.get("normalized_distance"),
                        "query_length": row.get("query_length"),
                        "alignment_policy": row.get("alignment_policy"),
                        "capture_quality_status": capture_quality.get("status"),
                        "semantic_floor_source": semantic_floor.get("source"),
                    }
                )


def _build_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# 花/跳坐姿与镜头扰动鲁棒性门")
    lines.append("")
    lines.append(f"- 生成时间：`{payload['generated_at']}`")
    lines.append(f"- 标准库：`{payload['template_root']}`")
    lines.append(f"- 语义 profile：`{payload['semantic_profile_json']}`")
    lines.append("- 口径：只读缓存 Holistic JSON，基于标准骨架生成正例扰动，不调用 `/api/score`，不重启 Holistic。")
    lines.append("- 目标：验证坐姿、镜头位置、手部局部尺度、轻微旋转和手指小抖动不会压垮 `花/跳` 的核心语义得分。")
    lines.append("")
    backend = payload.get("backend_status") or {}
    if backend.get("ok"):
        data = backend.get("payload") or {}
        worker = data.get("worker") or {}
        scoring = data.get("scoring_module") or {}
        lines.append(
            f"- 5080 状态：worker=`{worker.get('status')}`，"
            f"worker_pid=`{((worker.get('ready_payload') or {}).get('pid'))}`，"
            f"reload_count=`{scoring.get('reload_count')}`，"
            f"last_reload_error=`{scoring.get('last_reload_error')}`"
        )
    else:
        lines.append(f"- 5080 状态：未读取或读取失败 `{backend.get('error') or '-'}`")
    lines.append("")
    lines.append("## 结论")
    lines.append("")
    lines.append(f"- 综合状态：`{'PASS' if payload['passed'] else 'FAIL'}`")
    lines.append(f"- 变体最低分门槛：`{payload['min_score']}`")
    lines.append("")
    lines.append("| 目标词 | 状态 | 最低分 | 最弱扰动 | 标准帧数 |")
    lines.append("|---|---|---:|---|---:|")
    for item in payload["results"]:
        lines.append(
            f"| {item['word']} | {'PASS' if item['gate_pass'] else 'FAIL'} | "
            f"{_fmt(item['min_observed_score'])} | {item['weakest_variant']} | {item['standard_length']} |"
        )
    lines.append("")
    lines.append("## 分项明细")
    for item in payload["results"]:
        lines.append("")
        lines.append(f"### {item['word']}")
        lines.append("")
        lines.append(f"- 标准序列：`{item['standard_json']}`")
        lines.append(f"- gate：`{'PASS' if item['gate_pass'] else 'FAIL'}`")
        lines.append(f"- 最低分：`{_fmt(item['min_observed_score'])}`，最弱扰动：`{item['weakest_variant']}`")
        lines.append("")
        lines.append("| 扰动 | 分数 | normalized_distance | alignment | capture_quality | semantic_floor |")
        lines.append("|---|---:|---:|---|---|---|")
        for row in sorted(item["variants"], key=lambda r: float(r["score"])):
            capture_quality = row.get("capture_quality") or {}
            semantic_floor = row.get("semantic_floor") or {}
            lines.append(
                f"| {row['variant']} | {_fmt(row['score'])} | {_fmt(row['normalized_distance'], 6)} | "
                f"{row.get('alignment_policy') or '-'} | {capture_quality.get('status') or '-'} | "
                f"{semantic_floor.get('source') or '-'} |"
            )
    lines.append("")
    lines.append("## 说明")
    lines.append("")
    lines.append("- 本门只验证核心语义对非关键姿态扰动的稳定性，不替代真实摄像头样本。")
    lines.append("- 若该门失败，优先检查 profile 中 `pose/face` 权重、`hand_global_position_weight`、以及手部局部几何和 two-hand relation 的相对特征是否被全局位置主导。")
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run pose/camera robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_pose_robustness_gate_current"))
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
        "claim_policy": "synthetic pose/camera robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "min_score": args.min_score,
        "backend_status": backend_status,
        "passed": passed,
        "results": results,
    }

    json_path = output_dir / "flower_jump_pose_robustness_gate.json"
    md_path = output_dir / "flower_jump_pose_robustness_gate.md"
    csv_path = output_dir / "flower_jump_pose_robustness_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳姿态鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳姿态鲁棒性报告：{md_path}")
    print(f"已生成花/跳姿态鲁棒性 CSV：{csv_path}")
    print(f"综合状态：{'PASS' if passed else 'FAIL'}")
    for item in results:
        print(
            f"- {item['word']}: {'PASS' if item['gate_pass'] else 'FAIL'} "
            f"min_score={_fmt(item['min_observed_score'])} weakest={item['weakest_variant']}"
        )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

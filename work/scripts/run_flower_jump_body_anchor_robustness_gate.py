#!/usr/bin/env python3
"""Stress-test flower/jump scoring against non-core body-anchor drift.

Real webcam Holistic output can keep pose/face landmarks present while placing
them noisily or inconsistently. For the current `花/跳` profiles, these
non-core body anchors should not drag down otherwise clear hand semantics.

This script edits cached skeleton sequences in memory only. It does not call
/api/score, run Holistic, move the web marker, or restart 5080.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from run_flower_jump_camera_roll_robustness_gate import _group_coords_and_valid, _set_coord_group
from run_flower_jump_landmark_noise_robustness_gate import _fmt, _json_default, _load_backend_status
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
BODY_ANCHOR_GROUPS = {"pose", "face"}


def _copy_op(op: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in op.items()}


def _valid_center(coords: np.ndarray, valid: np.ndarray) -> np.ndarray:
    if valid.any():
        return coords[valid, :2].mean(axis=0).astype(np.float32)
    return np.zeros(2, dtype=np.float32)


def _apply_body_ops(
    coords: np.ndarray,
    valid: np.ndarray,
    group: str,
    frame_index: int,
    ops: Sequence[Dict[str, Any]],
    rng: np.random.Generator,
) -> np.ndarray:
    if not valid.any():
        return coords
    for op in ops:
        groups = set(op.get("groups") or [])
        if group not in groups:
            continue
        if op.get("scale_x") is not None or op.get("scale_y") is not None:
            center = _valid_center(coords, valid)
            sx = float(op.get("scale_x", 1.0))
            sy = float(op.get("scale_y", 1.0))
            coords[valid, 0] = center[0] + sx * (coords[valid, 0] - center[0])
            coords[valid, 1] = center[1] + sy * (coords[valid, 1] - center[1])
        dx = float(op.get("dx", 0.0))
        dy = float(op.get("dy", 0.0))
        dz = float(op.get("dz", 0.0))
        if dx or dy or dz:
            coords[valid, 0] += dx
            coords[valid, 1] += dy
            coords[valid, 2] += dz
        jitter = float(op.get("jitter", 0.0))
        if jitter:
            noise = rng.normal(0.0, jitter, size=coords.shape).astype(np.float32)
            noise[:, 2] *= float(op.get("jitter_z_scale", 0.25))
            coords[valid] += noise[valid]
        sinusoidal = float(op.get("sinusoidal", 0.0))
        if sinusoidal:
            phase = math.sin(float(frame_index) * float(op.get("frequency", 0.9)))
            coords[valid, 0] += sinusoidal * phase
            coords[valid, 1] += float(op.get("sinusoidal_y_factor", -0.7)) * sinusoidal * phase
    return coords


def _body_anchor_variant(
    seq: SequenceData,
    name: str,
    *,
    profile: Any,
    ops: Sequence[Dict[str, Any]],
    seed: int,
) -> SequenceData:
    base = _strip_to_base_groups(seq)
    rng = np.random.default_rng(seed)
    items: List[FrameFeature] = []
    for frame_index, frame in enumerate(base.features):
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        presence = dict(frame.presence)
        for group in BODY_ANCHOR_GROUPS:
            coords, valid = _group_coords_and_valid(frame, group)
            if coords is None or valid is None:
                continue
            coords = _apply_body_ops(coords.copy(), valid.copy(), group, frame_index, ops, rng)
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


def _spec(
    variant: str,
    kind: str,
    ops: Sequence[Dict[str, Any]],
    rationale: str,
    *,
    min_score: Optional[float] = None,
    seed: int = 20260603,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": kind,
        "ops": [_copy_op(op) for op in ops],
        "min_score": min_score,
        "seed": seed,
        "rationale": rationale,
    }


def _variant_specs(min_score: float) -> List[Dict[str, Any]]:
    return [
        _spec(
            "self_recomputed",
            "positive",
            [],
            "标准序列剥离基础组后重建派生特征，应保持近满分。",
            min_score=95.0,
        ),
        _spec(
            "pose_shift_right_up",
            "positive",
            [{"groups": ["pose"], "dx": 0.65, "dy": -0.45, "dz": 0.10}],
            "躯干/身体关键点整体偏右上，但核心手部语义不变。",
            min_score=min_score,
        ),
        _spec(
            "face_shift_left_down",
            "positive",
            [{"groups": ["face"], "dx": -0.55, "dy": 0.35, "dz": -0.08}],
            "面部关键点整体偏左下，不应影响手部词评分。",
            min_score=min_score,
        ),
        _spec(
            "pose_face_opposite_shift",
            "positive",
            [
                {"groups": ["pose"], "dx": 0.55, "dy": -0.45, "dz": 0.10},
                {"groups": ["face"], "dx": -0.45, "dy": 0.35, "dz": -0.10},
            ],
            "pose 与 face 锚点彼此不一致，模拟非核心检测漂移。",
            min_score=min_score,
        ),
        _spec(
            "pose_face_jitter_0.12",
            "positive",
            [{"groups": ["pose", "face"], "jitter": 0.12, "jitter_z_scale": 0.20}],
            "pose/face 存在轻中度逐帧抖动。",
            min_score=min_score,
            seed=12345,
        ),
        _spec(
            "pose_face_scale_x0.65_y1.45",
            "positive",
            [{"groups": ["pose", "face"], "scale_x": 0.65, "scale_y": 1.45}],
            "身体/脸部局部比例异常，但手部核心不变。",
            min_score=min_score,
        ),
        _spec(
            "pose_face_sinusoidal_drift_0.30",
            "positive",
            [{"groups": ["pose", "face"], "sinusoidal": 0.30, "frequency": 0.9}],
            "非核心身体/脸部锚点随时间漂移。",
            min_score=min_score,
        ),
        _spec(
            "pose_face_jitter_0.35_diagnostic",
            "diagnostic",
            [{"groups": ["pose", "face"], "jitter": 0.35, "jitter_z_scale": 0.20}],
            "严重 pose/face 抖动只记录诊断边界。",
            seed=67890,
        ),
        _spec(
            "pose_face_shift_1.50_diagnostic",
            "diagnostic",
            [{"groups": ["pose", "face"], "dx": 1.50, "dy": -1.20, "dz": 0.30}],
            "极端非核心锚点整体偏移只记录诊断边界。",
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
    loaded_standard = load_sequence(standard_json, feature_mode, force_bbox=False)
    profile = load_semantic_profile(word, semantic_profile_json)
    standard = _body_anchor_variant(
        loaded_standard,
        "standard_base",
        profile=profile,
        ops=[],
        seed=20260603,
    )
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(min_score):
        query = _body_anchor_variant(
            loaded_standard,
            str(spec["variant"]),
            profile=profile,
            ops=spec["ops"],
            seed=int(spec["seed"]),
        )
        result = run_pair(standard, query, semantic_profile=profile, target_word=word, enable_cross_check=False)
        score_scale = result.get("score_scale") or {}
        row = {
            **spec,
            "score": float(result["prototype_score"]),
            "dtw_distance": float(result["dtw_distance"]),
            "normalized_distance": float(result["normalized_distance"]),
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


def _ops_summary(ops: Sequence[Dict[str, Any]]) -> str:
    if not ops:
        return "-"
    chunks: List[str] = []
    for op in ops:
        groups = ",".join(op.get("groups") or [])
        parts = [groups]
        for key in ["dx", "dy", "dz", "jitter", "scale_x", "scale_y", "sinusoidal"]:
            if op.get(key) is not None:
                parts.append(f"{key}={op[key]}")
        chunks.append(" ".join(parts))
    return "; ".join(chunks)


def _write_rows_csv(path: Path, results: Sequence[Dict[str, Any]]) -> None:
    fields = [
        "word",
        "variant",
        "kind",
        "passed",
        "score",
        "min_score",
        "dtw_distance",
        "normalized_distance",
        "alignment_mode",
        "capture_quality_status",
        "capture_quality_reason",
        "semantic_floor_source",
        "ops",
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
                        "dtw_distance": row.get("dtw_distance"),
                        "normalized_distance": row.get("normalized_distance"),
                        "alignment_mode": policy.get("mode"),
                        "capture_quality_status": quality.get("status"),
                        "capture_quality_reason": quality.get("reason"),
                        "semantic_floor_source": floor.get("source"),
                        "ops": _ops_summary(row.get("ops") or []),
                        "rationale": row.get("rationale"),
                    }
                )


def _build_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# 花/跳非核心身体锚点漂移鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，剥离到基础骨架组后仅扰动 `pose/face`，保留手部核心语义，并重建 motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：pose/face 存在漂移、抖动或比例异常时，`花/跳` 不应被非核心身体锚点拖低。",
        "",
    ]
    backend = payload.get("backend_status") or {}
    if backend.get("ok"):
        data = backend.get("payload") or {}
        worker = data.get("worker") or {}
        scoring = data.get("scoring_module") or {}
        process = worker.get("process") or {}
        lines.append(
            f"- 5080 状态：worker=`{worker.get('status')}`，pid=`{process.get('pid') or ((worker.get('ready_payload') or {}).get('pid'))}`，"
            f"reload_count=`{scoring.get('reload_count')}`，last_reload_error=`{scoring.get('last_reload_error')}`"
        )
    else:
        lines.append(f"- 5080 状态：读取失败 `{backend.get('error') or '-'}`")
    lines.extend(["", "## 结论", "", f"- 综合状态：`{'PASS' if payload['passed'] else 'FAIL'}`", ""])
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向漂移 | 诊断最低分 | 最弱诊断漂移 | 门槛 |")
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
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | alignment | capture_quality | semantic_floor | 扰动 | 说明 |")
        lines.append("|---|---|---|---:|---|---|---|---|---|---|")
        for row in sorted(item["variants"], key=lambda value: (value["kind"], float(value["score"]))):
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
                f"| {row['variant']} | {row['kind']} | {status} | {_fmt(row['score'])} | {threshold} | "
                f"{policy.get('mode') or '-'} | {quality.get('status') or '-'} | "
                f"{floor.get('source') or '-'} | {_ops_summary(row.get('ops') or [])} | {row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 正向变体覆盖 pose/face 整体偏移、相互不一致、逐帧抖动、局部比例异常和随时间漂移。",
            "- 该门证明当前 `花/跳` 评分以核心手部语义为主，不因非核心身体锚点噪声降低网页正常得分。",
            "- 这是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run body-anchor drift robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_body_anchor_robustness_gate_current"))
    parser.add_argument("--words", nargs="+", default=DEFAULT_WORDS)
    parser.add_argument("--feature-mode", choices=["auto", "landmark", "bbox"], default="auto")
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--status-timeout-sec", type=float, default=3.0)
    parser.add_argument("--min-score", type=float, default=90.0)
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
        "claim_policy": "synthetic body-anchor robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": backend_status,
        "passed": passed,
        "min_score": args.min_score,
        "results": results,
    }

    json_path = output_dir / "flower_jump_body_anchor_robustness_gate.json"
    md_path = output_dir / "flower_jump_body_anchor_robustness_gate.md"
    csv_path = output_dir / "flower_jump_body_anchor_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳非核心身体锚点鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳非核心身体锚点鲁棒性报告：{md_path}")
    print(f"已生成花/跳非核心身体锚点鲁棒性 CSV：{csv_path}")
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

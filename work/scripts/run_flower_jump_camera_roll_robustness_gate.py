#!/usr/bin/env python3
"""Stress-test flower/jump scoring against camera roll and body tilt.

Browser users can sit at a tilted camera or lean so the entire skeleton is
rotated in the image plane. The older framing gate includes a light rotation,
but this gate strips cached sequences to base skeleton groups, applies the
roll, then rebuilds hand-shape, motion, and two-hand relation features so the
derived scoring inputs are tested after the geometric change.

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

from run_flower_jump_landmark_noise_robustness_gate import (
    _fmt,
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


def _roll_sequence(
    seq: SequenceData,
    name: str,
    *,
    degrees: float,
    profile: Any,
) -> SequenceData:
    base = _strip_to_base_groups(seq)
    center = _visible_center(base)
    theta = math.radians(float(degrees))
    rot = np.asarray(
        [[math.cos(theta), -math.sin(theta)], [math.sin(theta), math.cos(theta)]],
        dtype=np.float32,
    )
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
            coords[valid, :2] = (coords[valid, :2] - center) @ rot.T + center
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
            "degrees": 0.0,
            "min_score": 95.0,
            "rationale": "标准序列剥离基础组后重建派生特征，应保持近满分。",
        },
        {
            "variant": "camera_roll_pos5deg",
            "kind": "positive",
            "degrees": 5.0,
            "min_score": min_score,
            "rationale": "摄像头或身体轻微顺时针倾斜 5 度。",
        },
        {
            "variant": "camera_roll_neg5deg",
            "kind": "positive",
            "degrees": -5.0,
            "min_score": min_score,
            "rationale": "摄像头或身体轻微逆时针倾斜 5 度。",
        },
        {
            "variant": "camera_roll_pos10deg",
            "kind": "positive",
            "degrees": 10.0,
            "min_score": min_score,
            "rationale": "摄像头或身体中等顺时针倾斜 10 度。",
        },
        {
            "variant": "camera_roll_neg10deg",
            "kind": "positive",
            "degrees": -10.0,
            "min_score": min_score,
            "rationale": "摄像头或身体中等逆时针倾斜 10 度。",
        },
        {
            "variant": "camera_roll_pos15deg",
            "kind": "positive",
            "degrees": 15.0,
            "min_score": min_score,
            "rationale": "较明显顺时针倾斜 15 度，仍应保持可评分。",
        },
        {
            "variant": "camera_roll_neg15deg",
            "kind": "positive",
            "degrees": -15.0,
            "min_score": min_score,
            "rationale": "较明显逆时针倾斜 15 度，仍应保持可评分。",
        },
        {
            "variant": "camera_roll_pos20deg",
            "kind": "positive",
            "degrees": 20.0,
            "min_score": min_score,
            "rationale": "明显顺时针倾斜 20 度，作为正向鲁棒边界。",
        },
        {
            "variant": "camera_roll_neg20deg",
            "kind": "positive",
            "degrees": -20.0,
            "min_score": min_score,
            "rationale": "明显逆时针倾斜 20 度，作为正向鲁棒边界。",
        },
        {
            "variant": "camera_roll_pos35deg_diagnostic",
            "kind": "diagnostic",
            "degrees": 35.0,
            "rationale": "35 度整体倾斜已偏离正常网页取景，只记录诊断边界。",
        },
        {
            "variant": "camera_roll_neg35deg_diagnostic",
            "kind": "diagnostic",
            "degrees": -35.0,
            "rationale": "负 35 度整体倾斜已偏离正常网页取景，只记录诊断边界。",
        },
        {
            "variant": "camera_roll_pos45deg_diagnostic",
            "kind": "diagnostic",
            "degrees": 45.0,
            "rationale": "45 度极端倾斜只作为诊断，不代表正常采集。",
        },
        {
            "variant": "camera_roll_neg45deg_diagnostic",
            "kind": "diagnostic",
            "degrees": -45.0,
            "rationale": "负 45 度极端倾斜只作为诊断，不代表正常采集。",
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
    standard = _roll_sequence(loaded_standard, "standard_base", degrees=0.0, profile=profile)
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(min_score):
        query = _roll_sequence(
            loaded_standard,
            str(spec["variant"]),
            degrees=float(spec["degrees"]),
            profile=profile,
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


def _write_rows_csv(path: Path, results: Sequence[Dict[str, Any]]) -> None:
    fields = [
        "word",
        "variant",
        "kind",
        "passed",
        "score",
        "min_score",
        "degrees",
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
                        "degrees": row.get("degrees"),
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
        "# 花/跳摄像头整体倾斜鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，先剥离到基础骨架组，再做 image-plane roll 并重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：用户身体或摄像头整体倾斜时，`花/跳` 的相对手部语义仍保持可评分；35/45 度极端倾斜只记录诊断边界。",
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
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向倾斜 | 诊断最低分 | 最弱诊断倾斜 | 门槛 |")
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
        lines.append("| 变体 | 类型 | 状态 | 角度 | 分数 | 阈值 | alignment | capture_quality | semantic_floor | 说明 |")
        lines.append("|---|---|---|---:|---:|---|---|---|---|---|")
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
                f"| {row['variant']} | {row['kind']} | {status} | {_fmt(row['degrees'], 1)} | "
                f"{_fmt(row['score'])} | {threshold} | {policy.get('mode') or '-'} | "
                f"{quality.get('status') or '-'} | {floor.get('source') or '-'} | {row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 正向变体覆盖 ±5/±10/±15/±20 度整体倾斜，验证真实派生特征重建后的得分稳定性。",
            "- 35/45 度是极端取景诊断，不作为正常网页采集要求。",
            "- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run camera-roll robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_camera_roll_robustness_gate_current"))
    parser.add_argument("--words", nargs="+", default=DEFAULT_WORDS)
    parser.add_argument("--feature-mode", choices=["auto", "landmark", "bbox"], default="auto")
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--status-timeout-sec", type=float, default=3.0)
    parser.add_argument("--min-score", type=float, default=75.0)
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
        "claim_policy": "synthetic camera-roll robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": backend_status,
        "passed": passed,
        "min_score": args.min_score,
        "results": results,
    }

    json_path = output_dir / "flower_jump_camera_roll_robustness_gate.json"
    md_path = output_dir / "flower_jump_camera_roll_robustness_gate.md"
    csv_path = output_dir / "flower_jump_camera_roll_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳摄像头整体倾斜鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳摄像头整体倾斜鲁棒性报告：{md_path}")
    print(f"已生成花/跳摄像头整体倾斜鲁棒性 CSV：{csv_path}")
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

#!/usr/bin/env python3
"""Stress-test flower/jump scoring against camera perspective/shear distortion.

Browser webcam captures are not always front-facing. A phone or laptop camera
can be slightly off-axis, which appears in Holistic landmarks as image-plane
shear or as x/y drift correlated with z. Aspect-ratio and camera-roll gates
cover stretch and rotation; this gate covers the remaining oblique-view
distortion family.

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

from run_flower_jump_camera_roll_robustness_gate import _group_coords_and_valid, _set_coord_group
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


def _visible_center_3d(seq: SequenceData) -> np.ndarray:
    points: List[np.ndarray] = []
    for frame in seq.features:
        for group in COORD_GROUPS:
            coords, valid = _group_coords_and_valid(frame, group)
            if coords is None or valid is None or not valid.any():
                continue
            points.append(coords[valid])
    if not points:
        return np.zeros(3, dtype=np.float32)
    return np.concatenate(points, axis=0).mean(axis=0).astype(np.float32)


def _apply_perspective_shear(
    seq: SequenceData,
    name: str,
    *,
    profile: Any,
    xy_shear: float = 0.0,
    yx_shear: float = 0.0,
    z_to_x: float = 0.0,
    z_to_y: float = 0.0,
    local_hands_only: bool = False,
) -> Tuple[SequenceData, Dict[str, Any]]:
    base = _strip_to_base_groups(seq)
    center = _visible_center_3d(base)
    groups = ["left_hand", "right_hand"] if local_hands_only else COORD_GROUPS
    items: List[FrameFeature] = []
    changed_visible_points = 0
    selected_visible_points = 0
    has_transform = any(abs(value) > 1e-9 for value in [xy_shear, yx_shear, z_to_x, z_to_y])
    for frame in base.features:
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        presence = dict(frame.presence)
        for group in groups:
            coords, valid = _group_coords_and_valid(frame, group)
            if coords is None or valid is None or not valid.any():
                continue
            coords = coords.copy()
            rel = coords[valid] - center
            selected_visible_points += int(valid.sum())
            coords[valid, 0] += float(xy_shear) * rel[:, 1] + float(z_to_x) * rel[:, 2]
            coords[valid, 1] += float(yx_shear) * rel[:, 0] + float(z_to_y) * rel[:, 2]
            if has_transform:
                changed_visible_points += int(valid.sum())
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
    detail = {
        "xy_shear": float(xy_shear),
        "yx_shear": float(yx_shear),
        "z_to_x": float(z_to_x),
        "z_to_y": float(z_to_y),
        "local_hands_only": bool(local_hands_only),
        "changed_visible_points": changed_visible_points,
        "selected_visible_points": selected_visible_points,
        "total_frames": len(base.features),
        "center": [float(value) for value in center.tolist()],
    }
    return _sequence_with_relative_motion_features(transformed, profile), detail


def _spec(
    variant: str,
    kind: str,
    *,
    rationale: str,
    min_score: Optional[float] = None,
    xy_shear: float = 0.0,
    yx_shear: float = 0.0,
    z_to_x: float = 0.0,
    z_to_y: float = 0.0,
    local_hands_only: bool = False,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": kind,
        "xy_shear": float(xy_shear),
        "yx_shear": float(yx_shear),
        "z_to_x": float(z_to_x),
        "z_to_y": float(z_to_y),
        "local_hands_only": bool(local_hands_only),
        "min_score": min_score,
        "gated": kind == "positive",
        "rationale": rationale,
    }


def _variant_specs(min_score: float) -> List[Dict[str, Any]]:
    return [
        _spec(
            "self_recomputed",
            "positive",
            min_score=95.0,
            rationale="标准序列剥离基础组后重建 hand-shape/motion/relation 特征，应保持近满分。",
        ),
        _spec(
            "global_shear_x_from_y_0.08",
            "positive",
            xy_shear=0.08,
            min_score=min_score,
            rationale="轻微 x<-y 剪切，模拟摄像头水平斜拍。",
        ),
        _spec(
            "global_shear_x_from_y_neg0.08",
            "positive",
            xy_shear=-0.08,
            min_score=min_score,
            rationale="反向轻微 x<-y 剪切，覆盖相反斜拍方向。",
        ),
        _spec(
            "global_shear_y_from_x_0.08",
            "positive",
            yx_shear=0.08,
            min_score=min_score,
            rationale="轻微 y<-x 剪切，模拟摄像头垂直方向斜拍。",
        ),
        _spec(
            "global_shear_y_from_x_neg0.08",
            "positive",
            yx_shear=-0.08,
            min_score=min_score,
            rationale="反向轻微 y<-x 剪切，覆盖相反斜拍方向。",
        ),
        _spec(
            "global_shear_x_from_y_0.15",
            "positive",
            xy_shear=0.15,
            min_score=min_score,
            rationale="中度 x<-y 剪切，仍应保持可评分。",
        ),
        _spec(
            "global_shear_y_from_x_0.15",
            "positive",
            yx_shear=0.15,
            min_score=min_score,
            rationale="中度 y<-x 剪切，仍应保持可评分。",
        ),
        _spec(
            "perspective_z_to_x_0.35",
            "positive",
            z_to_x=0.35,
            min_score=min_score,
            rationale="x 坐标随 z 轻中度漂移，模拟非正面视角的透视偏移。",
        ),
        _spec(
            "perspective_z_to_x_neg0.35",
            "positive",
            z_to_x=-0.35,
            min_score=min_score,
            rationale="反向 x-z 透视偏移，覆盖另一侧斜拍。",
        ),
        _spec(
            "perspective_z_to_y_0.35",
            "positive",
            z_to_y=0.35,
            min_score=min_score,
            rationale="y 坐标随 z 轻中度漂移，模拟上下方向非正面视角。",
        ),
        _spec(
            "combo_shear_0.08_zx_0.25",
            "positive",
            xy_shear=0.08,
            z_to_x=0.25,
            min_score=min_score,
            rationale="轻微 image-plane 剪切叠加 z-to-x 透视偏移。",
        ),
        _spec(
            "local_hand_shear_x_from_y_0.12",
            "positive",
            xy_shear=0.12,
            local_hands_only=True,
            min_score=min_score,
            rationale="只在双手局部出现轻中度剪切，模拟手掌相对镜头有斜角。",
        ),
        _spec(
            "diagnostic_shear_x_from_y_0.30",
            "diagnostic",
            xy_shear=0.30,
            rationale="强 x<-y 剪切只记录诊断边界，不代表正常网页采集。",
        ),
        _spec(
            "diagnostic_shear_y_from_x_0.30",
            "diagnostic",
            yx_shear=0.30,
            rationale="强 y<-x 剪切只记录诊断边界。",
        ),
        _spec(
            "diagnostic_z_to_x_0.80",
            "diagnostic",
            z_to_x=0.80,
            rationale="强 z-to-x 透视偏移只记录诊断边界。",
        ),
        _spec(
            "diagnostic_combo_shear_0.18_zx_0.60",
            "diagnostic",
            xy_shear=0.18,
            z_to_x=0.60,
            rationale="较强剪切和透视组合只记录边界，不作为正常通过要求。",
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
    standard, standard_detail = _apply_perspective_shear(loaded_standard, "standard_base", profile=profile)
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(min_score):
        query, detail = _apply_perspective_shear(
            loaded_standard,
            str(spec["variant"]),
            profile=profile,
            xy_shear=float(spec["xy_shear"]),
            yx_shear=float(spec["yx_shear"]),
            z_to_x=float(spec["z_to_x"]),
            z_to_y=float(spec["z_to_y"]),
            local_hands_only=bool(spec["local_hands_only"]),
        )
        result = run_pair(standard, query, semantic_profile=profile, target_word=word, enable_cross_check=False)
        score_scale = result.get("score_scale") or {}
        row = {
            "variant": spec["variant"],
            "kind": spec["kind"],
            "gated": bool(spec["gated"]),
            "min_score": spec.get("min_score"),
            "rationale": spec["rationale"],
            **detail,
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
        "standard_transform_detail": standard_detail,
        "semantic_profile": _profile_summary(profile),
        "gate_pass": all(bool(row["passed"]) for row in positive_rows),
        "weakest_positive_score": float(weakest_positive["score"]) if weakest_positive else None,
        "weakest_positive_variant": weakest_positive["variant"] if weakest_positive else "",
        "weakest_diagnostic_score": float(weakest_diagnostic["score"]) if weakest_diagnostic else None,
        "weakest_diagnostic_variant": weakest_diagnostic["variant"] if weakest_diagnostic else "",
        "min_required_score": min_score,
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
        "xy_shear",
        "yx_shear",
        "z_to_x",
        "z_to_y",
        "local_hands_only",
        "changed_visible_points",
        "selected_visible_points",
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
                        "xy_shear": row.get("xy_shear"),
                        "yx_shear": row.get("yx_shear"),
                        "z_to_x": row.get("z_to_x"),
                        "z_to_y": row.get("z_to_y"),
                        "local_hands_only": row.get("local_hands_only"),
                        "changed_visible_points": row.get("changed_visible_points"),
                        "selected_visible_points": row.get("selected_visible_points"),
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
        "# 花/跳斜拍透视剪切鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，先剥离到基础骨架组，再合成 image-plane shear、z-to-x/y 透视偏移或局部手部剪切，并重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：轻中度斜拍/透视扭曲仍可正常评分；强剪切和强 z 透视只记录诊断边界。",
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
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向透视/剪切 | 诊断最低分 | 最弱诊断透视/剪切 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for item in payload["results"]:
        lines.append(
            f"| {item['word']} | {'PASS' if item['gate_pass'] else 'FAIL'} | "
            f"{_fmt(item['weakest_positive_score'])} | {item['weakest_positive_variant']} | "
            f"{_fmt(item['weakest_diagnostic_score'])} | {item['weakest_diagnostic_variant'] or '-'} | "
            f"{_fmt(item['min_required_score'])} |"
        )
    lines.append("")
    lines.append("## 分项明细")
    for item in payload["results"]:
        lines.extend(["", f"### {item['word']}", "", f"- 标准序列：`{item['standard_json']}`", ""])
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | xy | yx | z->x | z->y | 局部手 | capture_quality | semantic_floor | 说明 |")
        lines.append("|---|---|---|---:|---|---:|---:|---:|---:|---|---|---|---|")
        for row in sorted(item["variants"], key=lambda value: (value["kind"], float(value["score"]))):
            quality = row.get("capture_quality") or {}
            floor = row.get("semantic_floor") or {}
            if row["kind"] == "positive":
                threshold = f">= {row.get('min_score')}"
                status = "PASS" if row["passed"] else "FAIL"
            else:
                threshold = "diagnostic"
                status = "DIAG"
            lines.append(
                f"| {row['variant']} | {row['kind']} | {status} | {_fmt(row['score'])} | "
                f"{threshold} | {_fmt(row.get('xy_shear'))} | {_fmt(row.get('yx_shear'))} | "
                f"{_fmt(row.get('z_to_x'))} | {_fmt(row.get('z_to_y'))} | "
                f"{'yes' if row.get('local_hands_only') else 'no'} | "
                f"{quality.get('status') or '-'}:{quality.get('reason') or '-'} | "
                f"{floor.get('source') or '-'}:{floor.get('reason') or '-'} | {row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 该门补充的是斜拍/透视扭曲，不替代已有宽高比、roll、depth、framing 或局部手形门。",
            "- 强剪切和强 z 透视不作为正常网页采集条件，只用于观察当前评分边界。",
            "- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run perspective/shear robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_perspective_shear_robustness_gate_current"))
    parser.add_argument("--words", nargs="+", default=DEFAULT_WORDS)
    parser.add_argument("--feature-mode", choices=["auto", "landmark", "bbox"], default="auto")
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--status-timeout-sec", type=float, default=3.0)
    parser.add_argument("--min-score", type=float, default=70.0)
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
        "claim_policy": "synthetic perspective/shear robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": backend_status,
        "passed": passed,
        "min_score": args.min_score,
        "results": results,
    }

    json_path = output_dir / "flower_jump_perspective_shear_robustness_gate.json"
    md_path = output_dir / "flower_jump_perspective_shear_robustness_gate.md"
    csv_path = output_dir / "flower_jump_perspective_shear_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳斜拍透视剪切鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳斜拍透视剪切鲁棒性报告：{md_path}")
    print(f"已生成花/跳斜拍透视剪切鲁棒性 CSV：{csv_path}")
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

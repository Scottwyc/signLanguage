#!/usr/bin/env python3
"""Stress-test flower/jump scoring against out-of-plane hand z-tilt.

Users often pitch or yaw the palm relative to the camera. Existing gates cover
image-plane hand rotation, global z/depth drift, and perspective shear; this
gate targets local hand x-z/y-z tilt around the wrist while preserving the
semantic action. Mild local z-tilt should remain scoreable, while stronger
tilts are recorded as diagnostic boundaries.

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
HAND_GROUPS = ["left_hand", "right_hand"]


def _rotation_matrix(axis: str, degrees: float) -> np.ndarray:
    theta = math.radians(float(degrees))
    c = math.cos(theta)
    s = math.sin(theta)
    if axis == "xz":
        return np.asarray([[c, 0.0, -s], [0.0, 1.0, 0.0], [s, 0.0, c]], dtype=np.float32)
    if axis == "yz":
        return np.asarray([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]], dtype=np.float32)
    raise ValueError(f"unknown z-tilt axis: {axis}")


def _tilt_hands(
    seq: SequenceData,
    name: str,
    *,
    groups: Sequence[str],
    axis: str,
    degrees: float,
    profile: Any,
) -> Tuple[SequenceData, Dict[str, Any]]:
    base = _strip_to_base_groups(seq)
    rot = _rotation_matrix(axis, degrees)
    items: List[FrameFeature] = []
    changed_visible_points = 0
    changed_frames = 0
    z_delta_values: List[float] = []

    for frame in base.features:
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        presence = dict(frame.presence)
        frame_changed = False
        for group in groups:
            coords, valid = _hand_array(frame, group)
            if coords is None or valid is None or not valid.any():
                continue
            coords = coords.copy()
            anchor = coords[0].copy() if bool(valid[0]) else coords[valid].mean(axis=0)
            before_z = coords[valid, 2].copy()
            local = coords[valid] - anchor
            coords[valid] = local @ rot.T + anchor
            z_delta_values.extend((coords[valid, 2] - before_z).astype(float).tolist())
            changed_visible_points += int(valid.sum())
            frame_changed = True
            _set_hand_group(frame, vector, mask, group, coords, valid)
            presence[group] = bool(valid.any())
        if frame_changed:
            changed_frames += 1
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
        "operation": "hand_z_tilt",
        "groups": list(groups),
        "axis": axis,
        "degrees": degrees,
        "changed_frames": changed_frames,
        "changed_visible_points": changed_visible_points,
        "z_delta_min": min(z_delta_values) if z_delta_values else None,
        "z_delta_max": max(z_delta_values) if z_delta_values else None,
    }
    return _sequence_with_relative_motion_features(transformed, profile), detail


def _spec(
    variant: str,
    kind: str,
    *,
    groups: Sequence[str],
    axis: str,
    degrees: float,
    rationale: str,
    min_score: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": kind,
        "groups": list(groups),
        "axis": axis,
        "degrees": degrees,
        "min_score": min_score,
        "gated": kind == "positive",
        "rationale": rationale,
    }


def _variant_specs(min_score: float) -> List[Dict[str, Any]]:
    return [
        _spec(
            "self_recomputed",
            "positive",
            groups=HAND_GROUPS,
            axis="xz",
            degrees=0.0,
            min_score=95.0,
            rationale="标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。",
        ),
        _spec(
            "both_hands_pitch_xz_neg8deg",
            "positive",
            groups=HAND_GROUPS,
            axis="xz",
            degrees=-8.0,
            min_score=min_score,
            rationale="双手围绕手腕做轻微 x-z 出平面俯仰，模拟掌面角度小偏差。",
        ),
        _spec(
            "both_hands_pitch_xz_pos8deg",
            "positive",
            groups=HAND_GROUPS,
            axis="xz",
            degrees=8.0,
            min_score=min_score,
            rationale="双手围绕手腕做轻微反向 x-z 出平面俯仰。",
        ),
        _spec(
            "both_hands_yaw_yz_neg8deg",
            "positive",
            groups=HAND_GROUPS,
            axis="yz",
            degrees=-8.0,
            min_score=min_score,
            rationale="双手围绕手腕做轻微 y-z 出平面侧倾，语义轨迹保持。",
        ),
        _spec(
            "both_hands_yaw_yz_pos8deg",
            "positive",
            groups=HAND_GROUPS,
            axis="yz",
            degrees=8.0,
            min_score=min_score,
            rationale="双手围绕手腕做轻微反向 y-z 出平面侧倾。",
        ),
        _spec(
            "right_hand_pitch_xz_neg12deg",
            "positive",
            groups=["right_hand"],
            axis="xz",
            degrees=-12.0,
            min_score=min_score,
            rationale="右手核心手掌轻中度 x-z 俯仰，覆盖常见手腕前后倾。",
        ),
        _spec(
            "right_hand_pitch_xz_pos12deg",
            "positive",
            groups=["right_hand"],
            axis="xz",
            degrees=12.0,
            min_score=min_score,
            rationale="右手核心手掌轻中度反向 x-z 俯仰。",
        ),
        _spec(
            "left_hand_yaw_yz_neg12deg",
            "positive",
            groups=["left_hand"],
            axis="yz",
            degrees=-12.0,
            min_score=min_score,
            rationale="左手局部 y-z 侧倾，验证双手词的地面手轻微出平面变化。",
        ),
        _spec(
            "left_hand_yaw_yz_pos12deg",
            "positive",
            groups=["left_hand"],
            axis="yz",
            degrees=12.0,
            min_score=min_score,
            rationale="左手局部反向 y-z 侧倾。",
        ),
        _spec(
            "both_hands_pitch_xz_neg25deg_diagnostic",
            "diagnostic",
            groups=HAND_GROUPS,
            axis="xz",
            degrees=-25.0,
            rationale="双手较强出平面俯仰只记录诊断边界。",
        ),
        _spec(
            "both_hands_yaw_yz_pos25deg_diagnostic",
            "diagnostic",
            groups=HAND_GROUPS,
            axis="yz",
            degrees=25.0,
            rationale="双手较强出平面侧倾只记录诊断边界。",
        ),
        _spec(
            "right_hand_pitch_xz_pos35deg_diagnostic",
            "diagnostic",
            groups=["right_hand"],
            axis="xz",
            degrees=35.0,
            rationale="右手核心强出平面俯仰可能改变手形语义，只作诊断。",
        ),
        _spec(
            "right_hand_yaw_yz_neg35deg_diagnostic",
            "diagnostic",
            groups=["right_hand"],
            axis="yz",
            degrees=-35.0,
            rationale="右手核心强出平面侧倾可能改变手形语义，只作诊断。",
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
    standard, standard_detail = _tilt_hands(
        loaded_standard,
        "standard_base",
        groups=HAND_GROUPS,
        axis="xz",
        degrees=0.0,
        profile=profile,
    )
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(min_score):
        query, tilt_detail = _tilt_hands(
            loaded_standard,
            str(spec["variant"]),
            groups=spec["groups"],
            axis=str(spec["axis"]),
            degrees=float(spec["degrees"]),
            profile=profile,
        )
        result = run_pair(standard, query, semantic_profile=profile, enable_cross_check=False)
        score_scale = result.get("score_scale") or {}
        row = {
            **spec,
            **tilt_detail,
            "score": float(result["prototype_score"]),
            "dtw_distance": float(result["dtw_distance"]),
            "normalized_distance": float(result["normalized_distance"]),
            "query_length": len(query.features),
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
        "standard_tilt_detail": standard_detail,
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
        "axis",
        "degrees",
        "groups",
        "z_delta_min",
        "z_delta_max",
        "changed_frames",
        "changed_visible_points",
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
                        "axis": row.get("axis"),
                        "degrees": row.get("degrees"),
                        "groups": ",".join(str(value) for value in (row.get("groups") or [])),
                        "z_delta_min": row.get("z_delta_min"),
                        "z_delta_max": row.get("z_delta_max"),
                        "changed_frames": row.get("changed_frames"),
                        "changed_visible_points": row.get("changed_visible_points"),
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
        "# 花/跳手部 z 倾角鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，剥离基础骨架组后围绕手腕做 x-z/y-z 局部 3D 旋转，并重建 hand-shape、motion、two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：用户手掌轻微朝向/背向摄像头或侧倾时，`花/跳` 核心语义仍保持可评分；强出平面倾角只记录诊断边界。",
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
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向 z 倾角 | 诊断最低分 | 最弱诊断 z 倾角 | 门槛 |")
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
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | 轴 | 角度 | z_delta | normalized_distance | alignment | capture_quality | semantic_floor | 说明 |")
        lines.append("|---|---|---|---:|---|---|---:|---|---:|---|---|---|---|")
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
            z_delta = f"{_fmt(row.get('z_delta_min'))}..{_fmt(row.get('z_delta_max'))}"
            lines.append(
                f"| {row['variant']} | {row['kind']} | {status} | {_fmt(row['score'])} | "
                f"{threshold} | {row.get('axis') or '-'} | {_fmt(row.get('degrees'), 1)} | {z_delta} | "
                f"{_fmt(row['normalized_distance'], 6)} | {policy.get('mode') or '-'} | "
                f"{quality.get('status') or '-'} | {floor.get('source') or '-'} | {row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 正向扰动覆盖轻微手掌出平面俯仰/侧倾，并强制重算派生手形、动作和双手关系特征。",
            "- 强倾角不作为硬门，避免把真实手形/朝向语义变化错误推广为正常采集。",
            "- 该门是合成鲁棒性压力测试，不能替代真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run local hand z-tilt robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_hand_z_tilt_robustness_gate_current"))
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
        "claim_policy": "synthetic local hand z-tilt robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "min_score": args.min_score,
        "backend_status": backend_status,
        "passed": passed,
        "results": results,
    }

    json_path = output_dir / "flower_jump_hand_z_tilt_robustness_gate.json"
    md_path = output_dir / "flower_jump_hand_z_tilt_robustness_gate.md"
    csv_path = output_dir / "flower_jump_hand_z_tilt_robustness_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳手部 z 倾角鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳手部 z 倾角鲁棒性报告：{md_path}")
    print(f"已生成花/跳手部 z 倾角鲁棒性 CSV：{csv_path}")
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

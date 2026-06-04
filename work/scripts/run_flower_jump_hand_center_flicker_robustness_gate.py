#!/usr/bin/env python3
"""Stress-test flower/jump scoring against temporal hand-center flicker.

Webcam hand detectors can wobble the whole hand crop center from frame to frame.
That is different from per-landmark coordinate noise and from hand-box scale
breathing: the local hand shape stays plausible, but the entire detected hand
center moves slightly over time. This gate edits cached skeleton sequences in
memory and rebuilds derived motion/relation features.

This script does not call /api/score, run Holistic, move the web marker, or
restart 5080.
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


def _signal(pattern: str, idx: int, length: int, period: int) -> float:
    if pattern == "none":
        return 0.0
    if pattern == "smooth":
        if length <= 1:
            return 0.0
        return math.sin(2.0 * math.pi * idx / float(length - 1))
    if pattern == "sparse":
        if idx <= 0 or idx >= length - 1 or period <= 1:
            return 0.0
        if idx % period != period // 2:
            return 0.0
        return 1.0 if (idx // period) % 2 == 0 else -1.0
    raise ValueError(f"unknown hand-center flicker pattern: {pattern}")


def _offset(mode: str, signal: float, amplitude: float) -> Tuple[float, float, float]:
    value = float(amplitude) * float(signal)
    if mode == "x":
        return value, 0.0, 0.0
    if mode == "y":
        return 0.0, value, 0.0
    if mode == "diag":
        return value, -0.65 * value, 0.0
    raise ValueError(f"unknown hand-center flicker mode: {mode}")


def _mutated_sequence(
    seq: SequenceData,
    name: str,
    *,
    groups: Sequence[str],
    pattern: str,
    mode: str,
    amplitude: float,
    period: int,
    profile: Any,
) -> Tuple[SequenceData, Dict[str, Any]]:
    base = _strip_to_base_groups(seq)
    items: List[FrameFeature] = []
    changed_frames = 0
    changed_visible_points = 0
    dx_values: List[float] = []
    dy_values: List[float] = []
    total_frames = len(base.features)

    for idx, frame in enumerate(base.features):
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        presence = dict(frame.presence)
        dx, dy, dz = _offset(mode, _signal(pattern, idx, total_frames, period), amplitude)
        dx_values.append(float(dx))
        dy_values.append(float(dy))
        delta = np.asarray([dx, dy, dz], dtype=np.float32)
        frame_changed = np.linalg.norm(delta) > 1e-8

        for group in groups:
            coords, valid = _hand_array(frame, group)
            if coords is None or valid is None or not valid.any():
                continue
            if frame_changed:
                coords[valid] = coords[valid] + delta
                changed_visible_points += int(valid.sum())
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
        "operation": "hand_center_flicker",
        "groups": list(groups),
        "pattern": pattern,
        "mode": mode,
        "amplitude": amplitude,
        "period": period,
        "changed_frames": changed_frames,
        "changed_visible_points": changed_visible_points,
        "total_frames": total_frames,
        "dx_min": min(dx_values) if dx_values else None,
        "dx_max": max(dx_values) if dx_values else None,
        "dy_min": min(dy_values) if dy_values else None,
        "dy_max": max(dy_values) if dy_values else None,
    }
    return _sequence_with_relative_motion_features(transformed, profile), detail


def _spec(
    variant: str,
    kind: str,
    *,
    groups: Sequence[str],
    pattern: str,
    mode: str,
    amplitude: float,
    period: int,
    rationale: str,
    min_score: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": kind,
        "groups": list(groups),
        "pattern": pattern,
        "mode": mode,
        "amplitude": amplitude,
        "period": period,
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
            pattern="none",
            mode="x",
            amplitude=0.0,
            period=1,
            min_score=95.0,
            rationale="标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。",
        ),
        _spec(
            "both_hands_smooth_center_x_0.04",
            "positive",
            groups=HAND_GROUPS,
            pattern="smooth",
            mode="x",
            amplitude=0.04,
            period=1,
            min_score=min_score,
            rationale="双手检测中心随时间平滑横向漂移 4%，模拟 detector crop center wobble。",
        ),
        _spec(
            "both_hands_smooth_center_y_0.04",
            "positive",
            groups=HAND_GROUPS,
            pattern="smooth",
            mode="y",
            amplitude=0.04,
            period=1,
            min_score=min_score,
            rationale="双手检测中心随时间平滑纵向漂移 4%，整体手势仍应可评分。",
        ),
        _spec(
            "both_hands_sparse_center_diag_0.035_every_5f",
            "positive",
            groups=HAND_GROUPS,
            pattern="sparse",
            mode="diag",
            amplitude=0.035,
            period=5,
            min_score=min_score,
            rationale="少量帧双手检测中心出现轻微对角跳点，模拟网页帧级 detector center flicker。",
        ),
        _spec(
            "right_hand_smooth_center_y_0.03",
            "positive",
            groups=["right_hand"],
            pattern="smooth",
            mode="y",
            amplitude=0.03,
            period=1,
            min_score=min_score,
            rationale="右手核心手检测中心平滑纵向漂移 3%，验证右手 motion/relation 对中心抖动的吸收。",
        ),
        _spec(
            "right_hand_sparse_center_diag_0.025_every_5f",
            "positive",
            groups=["right_hand"],
            pattern="sparse",
            mode="diag",
            amplitude=0.025,
            period=5,
            min_score=min_score,
            rationale="少量帧右手检测中心轻微跳点，覆盖单手局部 detector flicker。",
        ),
        _spec(
            "left_hand_smooth_center_y_0.03",
            "positive",
            groups=["left_hand"],
            pattern="smooth",
            mode="y",
            amplitude=0.03,
            period=1,
            min_score=min_score,
            rationale="左手检测中心平滑纵向漂移 3%，覆盖跳的地面手和花的非核心手。",
        ),
        _spec(
            "left_hand_sparse_center_diag_0.025_every_5f",
            "positive",
            groups=["left_hand"],
            pattern="sparse",
            mode="diag",
            amplitude=0.025,
            period=5,
            min_score=min_score,
            rationale="少量帧左手检测中心轻微跳点，不应破坏完整动作评分。",
        ),
        _spec(
            "both_hands_strong_smooth_center_y_0.18_diagnostic",
            "diagnostic",
            groups=HAND_GROUPS,
            pattern="smooth",
            mode="y",
            amplitude=0.18,
            period=1,
            rationale="双手检测中心平滑大幅漂移 18% 属于强边界，只记录诊断分数。",
        ),
        _spec(
            "right_hand_strong_sparse_center_diag_0.12_every_4f_diagnostic",
            "diagnostic",
            groups=["right_hand"],
            pattern="sparse",
            mode="diag",
            amplitude=0.12,
            period=4,
            rationale="右手检测中心少量帧大幅跳点不是正常轻微 detector wobble，只记录诊断分数。",
        ),
        _spec(
            "left_hand_strong_sparse_center_diag_0.12_every_4f_diagnostic",
            "diagnostic",
            groups=["left_hand"],
            pattern="sparse",
            mode="diag",
            amplitude=0.12,
            period=4,
            rationale="左手检测中心少量帧大幅跳点不是正常轻微 detector wobble，只记录诊断分数。",
        ),
    ]


def _row_passed(row: Dict[str, Any]) -> bool:
    if row["kind"] == "positive":
        return float(row["score"]) >= float(row["min_score"])
    return True


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
    standard, standard_detail = _mutated_sequence(
        loaded_standard,
        "standard_base",
        groups=HAND_GROUPS,
        pattern="none",
        mode="x",
        amplitude=0.0,
        period=1,
        profile=profile,
    )
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(min_score):
        query, detail = _mutated_sequence(
            loaded_standard,
            str(spec["variant"]),
            groups=spec["groups"],
            pattern=str(spec["pattern"]),
            mode=str(spec["mode"]),
            amplitude=float(spec["amplitude"]),
            period=int(spec["period"]),
            profile=profile,
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
            "action_window": result.get("action_window"),
        }
        row["passed"] = _row_passed(row)
        rows.append(row)
    positive_rows = [row for row in rows if row["kind"] == "positive"]
    diagnostic_rows = [row for row in rows if row["kind"] == "diagnostic"]
    weakest_positive = min(positive_rows, key=lambda row: float(row["score"])) if positive_rows else None
    weakest_diagnostic = min(diagnostic_rows, key=lambda row: float(row["score"])) if diagnostic_rows else None
    return {
        "word": word,
        "standard_json": str(standard_json),
        "standard_length": len(standard.features),
        "standard_mutation_detail": standard_detail,
        "semantic_profile": _profile_summary(profile),
        "gate_pass": all(bool(row["passed"]) for row in rows if row["gated"]),
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
        "groups",
        "pattern",
        "mode",
        "amplitude",
        "period",
        "dx_min",
        "dx_max",
        "dy_min",
        "dy_max",
        "changed_frames",
        "changed_visible_points",
        "total_frames",
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
                        "groups": json.dumps(row.get("groups") or [], ensure_ascii=False),
                        "pattern": row.get("pattern"),
                        "mode": row.get("mode"),
                        "amplitude": row.get("amplitude"),
                        "period": row.get("period"),
                        "dx_min": row.get("dx_min"),
                        "dx_max": row.get("dx_max"),
                        "dy_min": row.get("dy_min"),
                        "dy_max": row.get("dy_max"),
                        "changed_frames": row.get("changed_frames"),
                        "changed_visible_points": row.get("changed_visible_points"),
                        "total_frames": row.get("total_frames"),
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
        "# 花/跳手部中心时序漂移鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，逐帧平移手部局部坐标后重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：轻微平滑 detector center wobble、少量帧级 hand-center flicker 仍保持可评分；强中心跳点只记录诊断边界。",
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
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向中心漂移 | 诊断最低分 | 最弱诊断中心漂移 | 门槛 |")
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
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | 手 | pattern | mode | amp | dx | dy | 改动帧 | capture_quality | semantic_floor | 说明 |")
        lines.append("|---|---|---|---:|---|---|---|---|---:|---|---|---:|---|---|---|")
        for row in sorted(item["variants"], key=lambda value: (value["kind"], float(value["score"]))):
            quality = row.get("capture_quality") or {}
            floor = row.get("semantic_floor") or {}
            if row["kind"] == "positive":
                threshold = f">= {row.get('min_score')}"
                status = "PASS" if row["passed"] else "FAIL"
            else:
                threshold = "diagnostic"
                status = "DIAG"
            groups = json.dumps(row.get("groups") or [], ensure_ascii=False)
            lines.append(
                f"| {row['variant']} | {row['kind']} | {status} | {_fmt(row['score'])} | "
                f"{threshold} | `{groups}` | {row.get('pattern') or '-'} | {row.get('mode') or '-'} | "
                f"{_fmt(row.get('amplitude'))} | {_fmt(row.get('dx_min'))}-{_fmt(row.get('dx_max'))} | "
                f"{_fmt(row.get('dy_min'))}-{_fmt(row.get('dy_max'))} | {row.get('changed_frames')} | "
                f"{quality.get('status') or '-'}:{quality.get('reason') or '-'} | "
                f"{floor.get('source') or '-'}:{floor.get('reason') or '-'} | {row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 该门补充的是 hand detector 中心的时间漂移，不替代静态 pose shift、relation-geometry、landmark-noise 或 hand-scale-flicker 门。",
            "- 正向变体只覆盖 2.5%-4% 的平滑或稀疏手中心漂移，强 12%-18% 漂移/跳点不是正常网页采集要求。",
            "- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run temporal hand-center flicker robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_hand_center_flicker_robustness_gate_current"))
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
        "claim_policy": "synthetic temporal hand-center flicker robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": backend_status,
        "passed": passed,
        "min_score": args.min_score,
        "results": results,
    }

    json_path = output_dir / "flower_jump_hand_center_flicker_robustness_gate.json"
    md_path = output_dir / "flower_jump_hand_center_flicker_robustness_gate.md"
    csv_path = output_dir / "flower_jump_hand_center_flicker_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳手部中心时序漂移鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳手部中心时序漂移鲁棒性报告：{md_path}")
    print(f"已生成花/跳手部中心时序漂移鲁棒性 CSV：{csv_path}")
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

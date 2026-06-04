#!/usr/bin/env python3
"""Stress-test flower/jump scoring against wrist/palm-root anchor drift.

Browser Holistic can keep hand landmarks visible while the wrist or MCP palm
anchors briefly slide away from the visible fingers. That differs from
palm-anchor occlusion: masks remain valid, but the local hand-root coordinates
are wrong and can corrupt hand-shape and two-hand relation features. Mild,
short anchor drift should not break an otherwise clear flower/jump sequence;
longer or stronger root drift is kept as a diagnostic boundary.

This script edits cached skeleton sequences in memory only. It does not call
/api/score, run Holistic, move the web marker, or restart 5080.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

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

PALM_ANCHORS = [0, 1, 5, 9, 13, 17]
WRIST_MCP_ANCHORS = [0, 5, 9, 13, 17]
MCP_ANCHORS = [5, 9, 13, 17]
WRIST_ONLY = [0]


def _active_indices(pattern: str, length: int) -> Set[int]:
    if length <= 0:
        return set()
    if pattern == "none":
        return set()
    if pattern == "single_mid":
        return {length // 2}
    if pattern == "sparse_every_6f":
        return {idx for idx in range(length) if idx % 6 == 3}
    if pattern == "middle_20pct":
        start = int(round(length * 0.40))
        end = max(start + 1, int(round(length * 0.60)))
        return set(range(max(0, start), min(length, end)))
    if pattern == "middle_35pct":
        start = int(round(length * 0.325))
        end = max(start + 1, int(round(length * 0.675)))
        return set(range(max(0, start), min(length, end)))
    if pattern == "full":
        return set(range(length))
    raise ValueError(f"unknown wrist-anchor drift pattern: {pattern}")


def _drift_sequence(
    seq: SequenceData,
    name: str,
    *,
    groups: Sequence[str],
    landmarks: Sequence[int],
    pattern: str,
    drift_xyz: Sequence[float],
    profile: Any,
) -> Tuple[SequenceData, Dict[str, Any]]:
    base = _strip_to_base_groups(seq)
    active = _active_indices(pattern, len(base.features))
    drift = np.asarray(list(drift_xyz), dtype=np.float32)
    if drift.shape != (3,):
        raise ValueError(f"drift_xyz must have exactly 3 values, got {drift_xyz}")

    features: List[FrameFeature] = []
    changed_frames = 0
    changed_points = 0
    skipped_points = 0

    for idx, frame in enumerate(base.features):
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        presence = dict(frame.presence)
        frame_changed = False
        if idx in active:
            for group in groups:
                coords, valid = _hand_array(frame, group)
                if coords is None or valid is None:
                    continue
                coords = coords.copy()
                valid = valid.copy()
                for landmark_idx in landmarks:
                    point_idx = int(landmark_idx)
                    if not 0 <= point_idx < len(valid):
                        skipped_points += 1
                        continue
                    if bool(valid[point_idx]):
                        coords[point_idx] = coords[point_idx] + drift
                        changed_points += 1
                        frame_changed = True
                    else:
                        skipped_points += 1
                _set_hand_group(frame, vector, mask, group, coords, valid)
                presence[group] = bool(valid.any())
        if frame_changed:
            changed_frames += 1
        item = _clone_frame(frame, vector=vector, mask=mask)
        item.presence = presence
        features.append(item)

    transformed = SequenceData(
        source=f"{base.source}::{name}",
        mode=base.mode,
        fps=base.fps,
        total_frames=base.total_frames,
        features=features,
    )
    detail = {
        "operation": "wrist_anchor_drift",
        "drift_groups": list(groups),
        "drift_landmarks": [int(item) for item in landmarks],
        "pattern": pattern,
        "drift_xyz": [float(item) for item in drift],
        "drift_magnitude_xy": float(np.linalg.norm(drift[:2])),
        "active_frame_count": len(active),
        "changed_frames": changed_frames,
        "changed_points": changed_points,
        "skipped_points": skipped_points,
        "total_frames": len(base.features),
    }
    return _sequence_with_relative_motion_features(transformed, profile), detail


def _spec(
    variant: str,
    kind: str,
    *,
    groups: Sequence[str],
    landmarks: Sequence[int],
    pattern: str,
    drift_xyz: Sequence[float],
    rationale: str,
    min_score: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": kind,
        "groups": list(groups),
        "landmarks": [int(item) for item in landmarks],
        "pattern": pattern,
        "drift_xyz": [float(item) for item in drift_xyz],
        "min_score": min_score,
        "gated": kind == "positive",
        "rationale": rationale,
    }


def _variant_specs(word: str, min_score: float) -> List[Dict[str, Any]]:
    specs = [
        _spec(
            "self_recomputed",
            "positive",
            groups=[],
            landmarks=[],
            pattern="none",
            drift_xyz=(0.0, 0.0, 0.0),
            min_score=95.0,
            rationale="标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。",
        )
    ]
    if word == "花":
        specs.extend(
            [
                _spec(
                    "flower_single_right_wrist_xy_0.055",
                    "positive",
                    groups=["right_hand"],
                    landmarks=WRIST_ONLY,
                    pattern="single_mid",
                    drift_xyz=(0.045, -0.032, 0.0),
                    min_score=min_score,
                    rationale="开花核心右手 wrist 单帧漂移，但指尖和 MCP 仍可见。",
                ),
                _spec(
                    "flower_sparse_right_wrist_y_0.040_every_6f",
                    "positive",
                    groups=["right_hand"],
                    landmarks=WRIST_ONLY,
                    pattern="sparse_every_6f",
                    drift_xyz=(0.0, 0.040, 0.0),
                    min_score=min_score,
                    rationale="开花核心右手 wrist 稀疏帧纵向跳动，模拟短时根点估计漂移。",
                ),
                _spec(
                    "flower_middle20_right_mcp_anchor_xy_0.029",
                    "positive",
                    groups=["right_hand"],
                    landmarks=MCP_ANCHORS,
                    pattern="middle_20pct",
                    drift_xyz=(0.024, -0.016, 0.0),
                    min_score=min_score,
                    rationale="开花核心右手 MCP 根点在短核心窗口轻度偏移，手指末端仍保留。",
                ),
                _spec(
                    "flower_middle20_right_palm_anchor_y_0.022",
                    "positive",
                    groups=["right_hand"],
                    landmarks=PALM_ANCHORS,
                    pattern="middle_20pct",
                    drift_xyz=(0.0, 0.022, 0.0),
                    min_score=min_score,
                    rationale="开花核心右手 palm anchors 短窗口同向轻漂移，验证根点坐标容错。",
                ),
                _spec(
                    "flower_middle35_right_wrist_xy_0.145_diagnostic",
                    "diagnostic",
                    groups=["right_hand"],
                    landmarks=WRIST_ONLY,
                    pattern="middle_35pct",
                    drift_xyz=(0.115, -0.088, 0.0),
                    rationale="诊断记录：核心右手 wrist 较长窗口大幅漂移时的边界分。",
                ),
                _spec(
                    "flower_middle35_right_palm_anchor_xy_0.090_diagnostic",
                    "diagnostic",
                    groups=["right_hand"],
                    landmarks=PALM_ANCHORS,
                    pattern="middle_35pct",
                    drift_xyz=(0.072, -0.054, 0.0),
                    rationale="诊断记录：核心右手多个 palm anchors 较强漂移时的边界分。",
                ),
            ]
        )
    elif word == "跳":
        specs.extend(
            [
                _spec(
                    "jump_single_left_ground_wrist_y_0.055",
                    "positive",
                    groups=["left_hand"],
                    landmarks=WRIST_ONLY,
                    pattern="single_mid",
                    drift_xyz=(0.0, 0.055, 0.0),
                    min_score=min_score,
                    rationale="跳的左手地面 wrist 单帧漂移，右手小人和双手关系仍可见。",
                ),
                _spec(
                    "jump_single_right_person_wrist_y_0.055",
                    "positive",
                    groups=["right_hand"],
                    landmarks=WRIST_ONLY,
                    pattern="single_mid",
                    drift_xyz=(0.0, -0.055, 0.0),
                    min_score=min_score,
                    rationale="跳的右手两指小人 wrist 单帧漂移，核心手指动作仍可见。",
                ),
                _spec(
                    "jump_sparse_left_ground_wrist_xy_0.038_every_6f",
                    "positive",
                    groups=["left_hand"],
                    landmarks=WRIST_ONLY,
                    pattern="sparse_every_6f",
                    drift_xyz=(-0.030, 0.024, 0.0),
                    min_score=min_score,
                    rationale="跳的左手地面 wrist 稀疏漂移，模拟地面手根点追踪跳动。",
                ),
                _spec(
                    "jump_sparse_right_person_wrist_xy_0.038_every_6f",
                    "positive",
                    groups=["right_hand"],
                    landmarks=WRIST_ONLY,
                    pattern="sparse_every_6f",
                    drift_xyz=(0.030, -0.024, 0.0),
                    min_score=min_score,
                    rationale="跳的右手小人 wrist 稀疏漂移，动作轨迹仍应可评分。",
                ),
                _spec(
                    "jump_middle20_left_ground_palm_anchor_x_0.020",
                    "positive",
                    groups=["left_hand"],
                    landmarks=PALM_ANCHORS,
                    pattern="middle_20pct",
                    drift_xyz=(-0.020, 0.0, 0.0),
                    min_score=min_score,
                    rationale="跳的左手地面 palm anchors 短窗口轻度横向漂移，关系证据仍保留。",
                ),
                _spec(
                    "jump_middle20_right_person_mcp_anchor_y_0.020",
                    "positive",
                    groups=["right_hand"],
                    landmarks=MCP_ANCHORS,
                    pattern="middle_20pct",
                    drift_xyz=(0.0, -0.020, 0.0),
                    min_score=min_score,
                    rationale="跳的右手两指小人 MCP 根点短窗口轻度漂移，食指/中指证据仍保留。",
                ),
                _spec(
                    "jump_middle35_left_ground_wrist_xy_0.150_diagnostic",
                    "diagnostic",
                    groups=["left_hand"],
                    landmarks=WRIST_ONLY,
                    pattern="middle_35pct",
                    drift_xyz=(-0.120, 0.090, 0.0),
                    rationale="诊断记录：左手地面 wrist 较长窗口大幅漂移时的边界分。",
                ),
                _spec(
                    "jump_middle35_right_person_palm_anchor_xy_0.090_diagnostic",
                    "diagnostic",
                    groups=["right_hand"],
                    landmarks=PALM_ANCHORS,
                    pattern="middle_35pct",
                    drift_xyz=(0.072, -0.054, 0.0),
                    rationale="诊断记录：右手小人 palm anchors 较强漂移时的边界分。",
                ),
            ]
        )
    return specs


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
    standard, standard_detail = _drift_sequence(
        loaded_standard,
        "standard_base",
        groups=[],
        landmarks=[],
        pattern="none",
        drift_xyz=(0.0, 0.0, 0.0),
        profile=profile,
    )
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(word, min_score):
        query, detail = _drift_sequence(
            loaded_standard,
            str(spec["variant"]),
            groups=spec["groups"],
            landmarks=spec["landmarks"],
            pattern=str(spec["pattern"]),
            drift_xyz=spec["drift_xyz"],
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
        "drift_groups",
        "drift_landmarks",
        "pattern",
        "drift_xyz",
        "drift_magnitude_xy",
        "active_frame_count",
        "changed_frames",
        "changed_points",
        "skipped_points",
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
                        "drift_groups": row.get("drift_groups"),
                        "drift_landmarks": row.get("drift_landmarks"),
                        "pattern": row.get("pattern"),
                        "drift_xyz": row.get("drift_xyz"),
                        "drift_magnitude_xy": row.get("drift_magnitude_xy"),
                        "active_frame_count": row.get("active_frame_count"),
                        "changed_frames": row.get("changed_frames"),
                        "changed_points": row.get("changed_points"),
                        "skipped_points": row.get("skipped_points"),
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
        "# 花/跳手腕掌根锚点漂移鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，在 hand mask 仍有效的前提下偏移 wrist/MCP/palm anchors 坐标，模拟手腕/掌根局部追踪漂移；随后重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：单帧、稀疏和轻度短窗口根点漂移仍可正常评分；持续核心漂移只记录诊断边界。",
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
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向漂移 | 诊断最低分 | 最弱诊断边界 | 门槛 |")
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
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | groups | landmarks | pattern | drift_xy | 改动帧 | 改动点 | capture_quality | semantic_floor | 说明 |")
        lines.append("|---|---|---|---:|---|---|---|---|---:|---:|---:|---|---|---|")
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
                f"{threshold} | {row.get('drift_groups')} | {row.get('drift_landmarks')} | "
                f"{row.get('pattern')} | {_fmt(row.get('drift_magnitude_xy'))} | {row.get('changed_frames')} | "
                f"{row.get('changed_points')} | {quality.get('status') or '-'}:{quality.get('reason') or '-'} | "
                f"{floor.get('source') or '-'}:{floor.get('reason') or '-'} | {row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 该门补充的是 wrist/MCP/palm anchors 坐标仍可见但短时偏移的情况，不替代 palm-anchor occlusion、hand-center flicker、hand-scale flicker 或 hand-overlap merge 门。",
            "- 持续核心根点漂移可能改变真实语义，本轮只作为诊断边界；是否升级硬负例需要真实网页样本或人工标签。",
            "- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run wrist-anchor drift robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_wrist_anchor_drift_robustness_gate_current"))
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
        "claim_policy": "synthetic wrist-anchor drift robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": backend_status,
        "passed": passed,
        "min_score": args.min_score,
        "results": results,
    }

    json_path = output_dir / "flower_jump_wrist_anchor_drift_robustness_gate.json"
    md_path = output_dir / "flower_jump_wrist_anchor_drift_robustness_gate.md"
    csv_path = output_dir / "flower_jump_wrist_anchor_drift_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳手腕掌根锚点漂移鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳手腕掌根锚点漂移鲁棒性报告：{md_path}")
    print(f"已生成花/跳手腕掌根锚点漂移鲁棒性 CSV：{csv_path}")
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

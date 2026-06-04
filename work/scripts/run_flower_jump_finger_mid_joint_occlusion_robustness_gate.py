#!/usr/bin/env python3
"""Stress-test flower/jump scoring against finger mid-joint mask loss.

Holistic can keep fingertips and palm anchors visible while briefly losing PIP,
DIP, or thumb IP joints when fingers overlap or blur. The scorer should tolerate
short or sparse mid-joint mask loss, while stronger sustained losses are kept as
diagnostic boundaries instead of being treated as normal capture requirements.

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

THUMB_INNER = [2, 3]
INDEX_MIDDLE_INNER = [6, 7, 10, 11]
RING_PINKY_INNER = [14, 15, 18, 19]
ALL_INNER_JOINTS = THUMB_INNER + INDEX_MIDDLE_INNER + RING_PINKY_INNER


def _indices_for_pattern(pattern: str, length: int) -> Set[int]:
    if length <= 0:
        return set()
    if pattern == "none":
        return set()
    if pattern == "single_mid":
        return {length // 2}
    if pattern == "sparse_every_7th":
        return {idx for idx in range(length) if idx % 7 == 3}
    if pattern == "middle_20pct":
        start = int(round(length * 0.40))
        end = max(start + 1, int(round(length * 0.60)))
        return set(range(max(0, start), min(length, end)))
    if pattern == "core_40pct":
        start = int(round(length * 0.30))
        end = max(start + 1, int(round(length * 0.70)))
        return set(range(max(0, start), min(length, end)))
    if pattern == "all":
        return set(range(length))
    raise ValueError(f"unknown occlusion pattern: {pattern}")


def _occlude_sequence(
    seq: SequenceData,
    name: str,
    *,
    groups: Sequence[str],
    landmarks: Sequence[int],
    pattern: str,
    profile: Any,
) -> Tuple[SequenceData, Dict[str, Any]]:
    base = _strip_to_base_groups(seq)
    selected = _indices_for_pattern(pattern, len(base.features))
    features: List[FrameFeature] = []
    occluded_visible_points = 0
    for idx, frame in enumerate(base.features):
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        presence = dict(frame.presence)
        if idx in selected:
            for group in groups:
                coords, valid = _hand_array(frame, group)
                if coords is None or valid is None:
                    continue
                coords = coords.copy()
                valid = valid.copy()
                for landmark_idx in landmarks:
                    if 0 <= int(landmark_idx) < len(valid):
                        if bool(valid[int(landmark_idx)]):
                            occluded_visible_points += 1
                        valid[int(landmark_idx)] = False
                        coords[int(landmark_idx)] = 0.0
                _set_hand_group(frame, vector, mask, group, coords, valid)
                presence[group] = bool(valid.any())
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
        "occlusion_pattern": pattern,
        "occluded_groups": list(groups),
        "occluded_landmarks": [int(item) for item in landmarks],
        "occlusion_frame_count": len(selected),
        "total_frames": len(base.features),
        "occlusion_ratio": (len(selected) / len(base.features)) if base.features else 0.0,
        "occluded_visible_points": occluded_visible_points,
        "occlusion_indices": sorted(selected),
    }
    return _sequence_with_relative_motion_features(transformed, profile), detail


def _spec(
    variant: str,
    kind: str,
    *,
    groups: Sequence[str],
    landmarks: Sequence[int],
    pattern: str,
    rationale: str,
    min_score: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": kind,
        "groups": list(groups),
        "landmarks": [int(item) for item in landmarks],
        "pattern": pattern,
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
            min_score=95.0,
            rationale="标准序列剥离基础组后重建 motion/relation 特征，应保持近满分。",
        )
    ]
    if word == "花":
        return specs + [
            _spec(
                "right_single_all_inner_joints",
                "positive",
                groups=["right_hand"],
                landmarks=ALL_INNER_JOINTS,
                pattern="single_mid",
                min_score=min_score,
                rationale="开花核心手单帧 PIP/DIP/thumb-IP 等中段指节丢失，模拟短时遮挡。",
            ),
            _spec(
                "right_sparse_index_middle_inner_joints",
                "positive",
                groups=["right_hand"],
                landmarks=INDEX_MIDDLE_INNER,
                pattern="sparse_every_7th",
                min_score=min_score,
                rationale="开花右手食指/中指中段指节稀疏闪断，指尖和掌根仍可见。",
            ),
            _spec(
                "right_sparse_all_inner_joints",
                "positive",
                groups=["right_hand"],
                landmarks=ALL_INNER_JOINTS,
                pattern="sparse_every_7th",
                min_score=min_score,
                rationale="开花右手所有中段指节稀疏闪断，验证 hand-shape mask 的时序冗余。",
            ),
            _spec(
                "right_middle20_index_middle_inner_joints",
                "positive",
                groups=["right_hand"],
                landmarks=INDEX_MIDDLE_INNER,
                pattern="middle_20pct",
                min_score=min_score,
                rationale="开花动作中段 20% 食指/中指中段指节不可见，开合语义仍应可恢复。",
            ),
            _spec(
                "right_middle20_ring_pinky_inner_joints",
                "positive",
                groups=["right_hand"],
                landmarks=RING_PINKY_INNER,
                pattern="middle_20pct",
                min_score=min_score,
                rationale="开花动作中段 20% 无名指/小指中段指节不可见，整体绽放仍应可评分。",
            ),
            _spec(
                "right_middle20_all_inner_joints_diagnostic",
                "diagnostic",
                groups=["right_hand"],
                landmarks=ALL_INNER_JOINTS,
                pattern="middle_20pct",
                rationale="中段 20% 全中段指节缺失偏强，记录边界但不作为正常网页采集要求。",
            ),
            _spec(
                "right_core40_all_inner_joints_diagnostic",
                "diagnostic",
                groups=["right_hand"],
                landmarks=ALL_INNER_JOINTS,
                pattern="core_40pct",
                rationale="核心段 40% 全中段指节缺失属于强遮挡边界，只作诊断记录。",
            ),
            _spec(
                "right_all_inner_joints_diagnostic",
                "diagnostic",
                groups=["right_hand"],
                landmarks=ALL_INNER_JOINTS,
                pattern="all",
                rationale="全程中段指节缺失时仍有指尖/掌根可见，记录模型解释边界而非硬负例。",
            ),
        ]
    if word == "跳":
        return specs + [
            _spec(
                "right_single_index_middle_inner_joints",
                "positive",
                groups=["right_hand"],
                landmarks=INDEX_MIDDLE_INNER,
                pattern="single_mid",
                min_score=min_score,
                rationale="右手两指小人单帧食指/中指中段指节丢失，跳跃关系仍应可评分。",
            ),
            _spec(
                "right_sparse_index_middle_inner_joints",
                "positive",
                groups=["right_hand"],
                landmarks=INDEX_MIDDLE_INNER,
                pattern="sparse_every_7th",
                min_score=min_score,
                rationale="右手两指小人食指/中指中段指节稀疏闪断，应由时序和指尖/掌根补偿。",
            ),
            _spec(
                "right_middle20_index_middle_inner_joints",
                "positive",
                groups=["right_hand"],
                landmarks=INDEX_MIDDLE_INNER,
                pattern="middle_20pct",
                min_score=min_score,
                rationale="右手动作中段 20% 两指中段指节不可见，双手关系和两指轮廓仍应保留。",
            ),
            _spec(
                "left_single_all_inner_joints",
                "positive",
                groups=["left_hand"],
                landmarks=ALL_INNER_JOINTS,
                pattern="single_mid",
                min_score=min_score,
                rationale="左手地面单帧中段指节丢失，地面手仍应通过掌根/指尖维持。",
            ),
            _spec(
                "left_sparse_all_inner_joints",
                "positive",
                groups=["left_hand"],
                landmarks=ALL_INNER_JOINTS,
                pattern="sparse_every_7th",
                min_score=min_score,
                rationale="左手地面中段指节稀疏闪断，不应导致跳跃双手关系整体失败。",
            ),
            _spec(
                "left_middle20_all_inner_joints",
                "positive",
                groups=["left_hand"],
                landmarks=ALL_INNER_JOINTS,
                pattern="middle_20pct",
                min_score=min_score,
                rationale="左手地面中段 20% 指节不可见，右手弹跳语义仍应正常。",
            ),
            _spec(
                "right_core40_index_middle_inner_joints_diagnostic",
                "diagnostic",
                groups=["right_hand"],
                landmarks=INDEX_MIDDLE_INNER,
                pattern="core_40pct",
                rationale="右手两指中段指节核心段 40% 缺失偏强，只记录诊断边界。",
            ),
            _spec(
                "left_core40_all_inner_joints_diagnostic",
                "diagnostic",
                groups=["left_hand"],
                landmarks=ALL_INNER_JOINTS,
                pattern="core_40pct",
                rationale="左手地面核心段 40% 中段指节缺失偏强，只记录诊断边界。",
            ),
            _spec(
                "right_all_index_middle_inner_joints_diagnostic",
                "diagnostic",
                groups=["right_hand"],
                landmarks=INDEX_MIDDLE_INNER,
                pattern="all",
                rationale="右手两指中段指节全程缺失时仍有指尖/掌根可见，记录解释边界。",
            ),
        ]
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
    standard, standard_detail = _occlude_sequence(
        loaded_standard,
        "standard_base",
        groups=[],
        landmarks=[],
        pattern="none",
        profile=profile,
    )
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(word, min_score):
        query, detail = _occlude_sequence(
            loaded_standard,
            str(spec["variant"]),
            groups=spec["groups"],
            landmarks=spec["landmarks"],
            pattern=str(spec["pattern"]),
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
        "standard_occlusion_detail": standard_detail,
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
        "occlusion_pattern",
        "occluded_groups",
        "occluded_landmarks",
        "occlusion_frame_count",
        "occlusion_ratio",
        "occluded_visible_points",
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
                        "occlusion_pattern": row.get("occlusion_pattern"),
                        "occluded_groups": ",".join(row.get("occluded_groups") or []),
                        "occluded_landmarks": ",".join(str(value) for value in (row.get("occluded_landmarks") or [])),
                        "occlusion_frame_count": row.get("occlusion_frame_count"),
                        "occlusion_ratio": row.get("occlusion_ratio"),
                        "occluded_visible_points": row.get("occluded_visible_points"),
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
        "# 花/跳手指中段关节遮挡鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，在 hand landmark mask 层合成 PIP/DIP/thumb-IP 等中段指节遮挡，并重建 motion/relation/hand-shape 特征；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：短时/稀疏中段指节不可见仍可正常评分；更强的持续核心指节缺失只作为诊断边界，不把它提升为正常网页采集要求。",
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
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向中段指节遮挡 | 诊断最低分 | 最弱诊断遮挡 | 门槛 |")
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
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | 遮挡帧 | landmark | capture_quality | 说明 |")
        lines.append("|---|---|---|---:|---|---:|---|---|---|")
        for row in sorted(item["variants"], key=lambda value: (value["kind"], float(value["score"]))):
            quality = row.get("capture_quality") or {}
            if row["kind"] == "positive":
                threshold = f">= {row.get('min_score')}"
                status = "PASS" if row["passed"] else "FAIL"
            else:
                threshold = "diagnostic"
                status = "DIAG"
            landmarks = ",".join(str(value) for value in (row.get("occluded_landmarks") or [])) or "-"
            lines.append(
                f"| {row['variant']} | {row['kind']} | {status} | {_fmt(row['score'])} | "
                f"{threshold} | {row.get('occlusion_frame_count')}/{row.get('total_frames')} | "
                f"{landmarks} | {quality.get('status') or '-'}:{quality.get('reason') or '-'} | "
                f"{row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 正向遮挡只覆盖单帧、稀疏或中段局部的 finger mid-joint mask 丢失，保持与真实轻量 detector 闪断一致。",
            "- 持续核心段或全程中段指节缺失只记录诊断边界，因为指尖和掌根仍可能保留足够语义，不能简单当作硬负例。",
            "- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run finger mid-joint occlusion robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_finger_mid_joint_occlusion_robustness_gate_current"))
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
        "claim_policy": "synthetic finger-mid-joint occlusion robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": backend_status,
        "passed": passed,
        "min_score": args.min_score,
        "results": results,
    }

    json_path = output_dir / "flower_jump_finger_mid_joint_occlusion_robustness_gate.json"
    md_path = output_dir / "flower_jump_finger_mid_joint_occlusion_robustness_gate.md"
    csv_path = output_dir / "flower_jump_finger_mid_joint_occlusion_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳手指中段关节遮挡鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳手指中段关节遮挡鲁棒性报告：{md_path}")
    print(f"已生成花/跳手指中段关节遮挡鲁棒性 CSV：{csv_path}")
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

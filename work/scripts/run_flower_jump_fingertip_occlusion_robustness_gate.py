#!/usr/bin/env python3
"""Stress-test flower/jump scoring against fingertip occlusion masks.

Webcam hand tracking can temporarily lose fingertip landmarks when fingers
overlap, blur, or move close to the camera. The scorer should tolerate short
or sparse fingertip mask loss, while sustained missing semantic-core fingertips
should remain low or be diagnosed as recapture/semantic failures.

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
TIP_LANDMARKS = [4, 8, 12, 16, 20]
INDEX_MIDDLE_TIPS = [8, 12]
ACCEPTED_NEGATIVE_QUALITY = {"needs_recapture", "semantic_mismatch"}


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
    max_score: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": kind,
        "groups": list(groups),
        "landmarks": [int(item) for item in landmarks],
        "pattern": pattern,
        "min_score": min_score,
        "max_score": max_score,
        "gated": kind in {"positive", "negative"},
        "rationale": rationale,
    }


def _variant_specs(word: str, min_score: float, negative_max_score: float) -> List[Dict[str, Any]]:
    specs = [
        _spec(
            "self_recomputed",
            "positive",
            groups=[],
            landmarks=[],
            pattern="none",
            min_score=95.0,
            rationale="标准序列剥离基础组后重建 motion/relation 特征，应保持近满分。",
        ),
        _spec(
            "single_mid_all_tips",
            "positive",
            groups=["right_hand"],
            landmarks=TIP_LANDMARKS,
            pattern="single_mid",
            min_score=min_score,
            rationale="单帧右手五个 fingertip mask 丢失，模拟短时遮挡/检测抖动。",
        ),
        _spec(
            "sparse_index_middle",
            "positive",
            groups=["right_hand"],
            landmarks=INDEX_MIDDLE_TIPS,
            pattern="sparse_every_7th",
            min_score=min_score,
            rationale="稀疏食指/中指 tip mask 丢失，应靠时序冗余保持可评分。",
        ),
        _spec(
            "sparse_all_tips",
            "positive",
            groups=["right_hand"],
            landmarks=TIP_LANDMARKS,
            pattern="sparse_every_7th",
            min_score=min_score,
            rationale="稀疏全 fingertip mask 丢失，覆盖网页帧间 tip 闪断。",
        ),
        _spec(
            "middle20_index_middle",
            "positive",
            groups=["right_hand"],
            landmarks=INDEX_MIDDLE_TIPS,
            pattern="middle_20pct",
            min_score=min_score,
            rationale="动作中段 20% 食指/中指 tip 短时不可见，仍应保持边界以上。",
        ),
        _spec(
            "middle20_all_tips",
            "positive",
            groups=["right_hand"],
            landmarks=TIP_LANDMARKS,
            pattern="middle_20pct",
            min_score=min_score,
            rationale="动作中段 20% 全 tip 短时不可见，作为正向遮挡鲁棒门。",
        ),
        _spec(
            "core40_all_tips_diagnostic",
            "diagnostic",
            groups=["right_hand"],
            landmarks=TIP_LANDMARKS,
            pattern="core_40pct",
            rationale="核心段 40% 全 tip 缺失属于遮挡边界，记录分数但不设硬门。",
        ),
    ]
    if word == "花":
        specs.append(
            _spec(
                "all_right_tips_negative",
                "negative",
                groups=["right_hand"],
                landmarks=TIP_LANDMARKS,
                pattern="all",
                max_score=negative_max_score,
                rationale="花的右手绽放指尖全程不可见，不能当作完整语义通过。",
            )
        )
    else:
        specs.append(
            _spec(
                "all_right_index_middle_negative",
                "negative",
                groups=["right_hand"],
                landmarks=INDEX_MIDDLE_TIPS,
                pattern="all",
                max_score=negative_max_score,
                rationale="跳的右手两指小人食指/中指 tip 全程不可见，应重采或语义失败。",
            )
        )
    return specs


def _row_passed(row: Dict[str, Any]) -> bool:
    score = float(row["score"])
    if row["kind"] == "positive":
        return score >= float(row["min_score"])
    if row["kind"] == "negative":
        quality = (row.get("capture_quality") or {}).get("status")
        return score <= float(row["max_score"]) or quality in ACCEPTED_NEGATIVE_QUALITY
    return True


def _run_word(
    word: str,
    template_root: Path,
    semantic_profile_json: Path,
    feature_mode: str,
    min_score: float,
    negative_max_score: float,
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
    for spec in _variant_specs(word, min_score, negative_max_score):
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
            "max_score": spec.get("max_score"),
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
    negative_rows = [row for row in rows if row["kind"] == "negative"]
    diagnostic_rows = [row for row in rows if row["kind"] == "diagnostic"]
    weakest_positive = min(positive_rows, key=lambda row: float(row["score"])) if positive_rows else None
    strongest_negative = max(negative_rows, key=lambda row: float(row["score"])) if negative_rows else None
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
        "strongest_negative_score": float(strongest_negative["score"]) if strongest_negative else None,
        "strongest_negative_variant": strongest_negative["variant"] if strongest_negative else "",
        "weakest_diagnostic_score": float(weakest_diagnostic["score"]) if weakest_diagnostic else None,
        "weakest_diagnostic_variant": weakest_diagnostic["variant"] if weakest_diagnostic else "",
        "min_required_score": min_score,
        "negative_max_score": negative_max_score,
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
        "max_score",
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
                        "max_score": row.get("max_score"),
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
        "# 花/跳指尖遮挡鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，在 hand landmark mask 层合成 fingertip 遮挡并重建 motion/relation/hand-shape 特征；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：短时/稀疏指尖不可见仍可正常评分；关键指尖全程不可见必须低分或进入重采/语义失败解释。",
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
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向遮挡 | 核心缺失最高分 | 最强核心缺失负例 | 诊断最低分 | 最弱诊断遮挡 |")
    lines.append("|---|---|---:|---|---:|---|---:|---|")
    for item in payload["results"]:
        lines.append(
            f"| {item['word']} | {'PASS' if item['gate_pass'] else 'FAIL'} | "
            f"{_fmt(item['weakest_positive_score'])} | {item['weakest_positive_variant']} | "
            f"{_fmt(item['strongest_negative_score'])} | {item['strongest_negative_variant']} | "
            f"{_fmt(item['weakest_diagnostic_score'])} | {item['weakest_diagnostic_variant']} |"
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
            elif row["kind"] == "negative":
                threshold = f"<= {row.get('max_score')} 或重采/语义失败"
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
            "- 正向遮挡只覆盖短时、稀疏或中段 20% 的 fingertip mask 丢失，避免把持续大面积缺失误判为正常。",
            "- `core40_all_tips_diagnostic` 是边界记录：当前模型可能仍能从其他手部结构和时序关系恢复语义，因此不作为硬失败门。",
            "- 全程关键指尖缺失用于验证 capture quality 或低分语义能阻止不完整网页样本通过。",
            "- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run fingertip occlusion robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_fingertip_occlusion_robustness_gate_current"))
    parser.add_argument("--words", nargs="+", default=DEFAULT_WORDS)
    parser.add_argument("--feature-mode", choices=["auto", "landmark", "bbox"], default="auto")
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--status-timeout-sec", type=float, default=3.0)
    parser.add_argument("--min-score", type=float, default=70.0)
    parser.add_argument("--negative-max-score", type=float, default=45.0)
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
            negative_max_score=args.negative_max_score,
        )
        for word in args.words
    ]
    backend_status = _load_backend_status(args.backend_url, args.status_timeout_sec)
    passed = all(bool(item["gate_pass"]) for item in results)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "claim_policy": "synthetic fingertip-occlusion robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": backend_status,
        "passed": passed,
        "min_score": args.min_score,
        "negative_max_score": args.negative_max_score,
        "accepted_negative_quality": sorted(ACCEPTED_NEGATIVE_QUALITY),
        "results": results,
    }

    json_path = output_dir / "flower_jump_fingertip_occlusion_robustness_gate.json"
    md_path = output_dir / "flower_jump_fingertip_occlusion_robustness_gate.md"
    csv_path = output_dir / "flower_jump_fingertip_occlusion_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳指尖遮挡鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳指尖遮挡鲁棒性报告：{md_path}")
    print(f"已生成花/跳指尖遮挡鲁棒性 CSV：{csv_path}")
    print(f"综合状态：{'PASS' if passed else 'FAIL'}")
    for item in results:
        print(
            f"- {item['word']}: {'PASS' if item['gate_pass'] else 'FAIL'} "
            f"positive_min={_fmt(item['weakest_positive_score'])} "
            f"core_missing_max={_fmt(item['strongest_negative_score'])}"
        )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

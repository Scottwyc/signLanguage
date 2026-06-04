#!/usr/bin/env python3
"""Stress-test flower/jump scoring against non-core hand/finger distractors.

Real browser users often move a non-dominant/support hand or curl non-semantic
fingers while still performing the core sign correctly. This gate edits cached
Holistic skeletons in memory and verifies these distractors do not drag down
clear flower/jump semantics.

The diagnostic core-damage variants are recorded only as observability rows.
They are not used as hard pass/fail gates because other promoted gates already
cover sustained semantic-core missing masks, clipping, and phase failures.

This script does not call /api/score, run Holistic, move marker, or restart
5080.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

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

RIGHT_NONCORE_FINGERS = [1, 2, 3, 4, 13, 14, 15, 16, 17, 18, 19, 20]
RIGHT_INDEX_MIDDLE_FINGERS = [5, 6, 7, 8, 9, 10, 11, 12]
RIGHT_FLOWER_OPENING_TIPS = [4, 8, 12, 16, 20]


def _operation_groups(operations: Sequence[Dict[str, Any]]) -> List[str]:
    return sorted({str(item.get("group") or "") for item in operations if item.get("group")})


def _operation_landmarks(operations: Sequence[Dict[str, Any]]) -> List[int]:
    values: set[int] = set()
    for item in operations:
        landmarks = item.get("landmarks")
        if landmarks is None:
            continue
        for value in landmarks:
            values.add(int(value))
    return sorted(values)


def _operation_types(operations: Sequence[Dict[str, Any]]) -> List[str]:
    return sorted({str(item.get("type") or "") for item in operations if item.get("type")})


def _transform_sequence(
    seq: SequenceData,
    name: str,
    *,
    profile: Any,
    operations: Sequence[Dict[str, Any]],
    seed: int = 17,
) -> tuple[SequenceData, Dict[str, Any]]:
    base = _strip_to_base_groups(seq)
    rng = np.random.default_rng(seed)
    items: List[FrameFeature] = []
    changed_visible_points = 0
    total_selected_points = 0
    for frame_idx, frame in enumerate(base.features):
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        presence = dict(frame.presence)
        for op in operations:
            group = str(op["group"])
            coords, valid = _hand_array(frame, group)
            if coords is None or valid is None or not valid.any():
                continue
            coords = coords.copy()
            valid = valid.copy()
            landmarks = op.get("landmarks")
            indices = list(range(len(valid))) if landmarks is None else [int(idx) for idx in landmarks if 0 <= int(idx) < len(valid)]
            visible = [idx for idx in indices if bool(valid[idx])]
            if not visible:
                continue
            selected = np.asarray(visible, dtype=int)
            total_selected_points += int(len(selected))
            kind = str(op["type"])
            if kind == "shift":
                delta = np.asarray(op["delta"], dtype=np.float32)
                coords[selected] = coords[selected] + delta
            elif kind == "jitter":
                sigma = float(op["sigma"])
                noise = rng.normal(0.0, sigma, size=(len(selected), 3)).astype(np.float32)
                noise[:, 2] *= 0.35
                coords[selected] = coords[selected] + noise
            elif kind == "motion_drift":
                amplitude = np.asarray(op["amplitude"], dtype=np.float32)
                phase = (frame_idx / max(len(base.features) - 1, 1)) * 2.0 * np.pi
                coords[selected] = coords[selected] + np.sin(phase) * amplitude
            elif kind == "scramble":
                values = coords[selected].copy()
                coords[selected] = values[rng.permutation(len(values))]
            elif kind == "collapse_to_wrist":
                wrist = coords[0].copy() if bool(valid[0]) else coords[valid].mean(axis=0)
                coords[selected] = wrist
            else:
                raise ValueError(f"unknown operation type: {kind}")
            changed_visible_points += int(len(selected))
            _set_hand_group(frame, vector, mask, group, coords, valid)
            presence[group] = bool(valid.any())
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
        "operation_groups": _operation_groups(operations),
        "operation_landmarks": _operation_landmarks(operations),
        "operation_types": _operation_types(operations),
        "operation_count": len(operations),
        "changed_visible_points": changed_visible_points,
        "total_selected_points": total_selected_points,
        "total_frames": len(base.features),
    }
    return _sequence_with_relative_motion_features(transformed, profile), detail


def _spec(
    variant: str,
    kind: str,
    *,
    operations: Sequence[Dict[str, Any]],
    rationale: str,
    min_score: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": kind,
        "operations": list(operations),
        "min_score": min_score,
        "gated": kind == "positive",
        "rationale": rationale,
    }


def _variant_specs(word: str, min_score: float) -> List[Dict[str, Any]]:
    specs = [
        _spec(
            "self_recomputed",
            "positive",
            operations=[],
            min_score=95.0,
            rationale="剥离基础组后重建 motion/relation 特征，应保持近满分。",
        )
    ]
    if word == "花":
        specs.extend(
            [
                _spec(
                    "flower_left_hand_shift_large",
                    "positive",
                    operations=[{"group": "left_hand", "type": "shift", "delta": [0.80, -0.60, 0.0]}],
                    min_score=min_score,
                    rationale="花的左手不是当前核心绽放手，大幅静态偏移不应拖低右手开花语义。",
                ),
                _spec(
                    "flower_left_hand_jitter_0.18",
                    "positive",
                    operations=[{"group": "left_hand", "type": "jitter", "sigma": 0.18}],
                    min_score=min_score,
                    rationale="非核心左手 landmark 大幅抖动，模拟另一只手在画面内干扰。",
                ),
                _spec(
                    "flower_left_hand_motion_drift",
                    "positive",
                    operations=[{"group": "left_hand", "type": "motion_drift", "amplitude": [0.35, -0.25, 0.0]}],
                    min_score=min_score,
                    rationale="非核心左手出现连续漂移运动，不应遮蔽右手绽放主语义。",
                ),
                _spec(
                    "flower_left_hand_shape_scramble",
                    "positive",
                    operations=[{"group": "left_hand", "type": "scramble"}],
                    min_score=min_score,
                    rationale="非核心左手手形结构异常，应被低权重路径吸收而不是拉低清晰右手动作。",
                ),
                _spec(
                    "flower_right_opening_tips_collapse_diagnostic",
                    "diagnostic",
                    operations=[{"group": "right_hand", "type": "collapse_to_wrist", "landmarks": RIGHT_FLOWER_OPENING_TIPS}],
                    rationale="诊断记录：右手绽放指尖塌缩会触发 opening guard 或显著低分。",
                ),
            ]
        )
    else:
        specs.extend(
            [
                _spec(
                    "jump_right_noncore_fingers_jitter_0.12",
                    "positive",
                    operations=[{"group": "right_hand", "type": "jitter", "sigma": 0.12, "landmarks": RIGHT_NONCORE_FINGERS}],
                    min_score=min_score,
                    rationale="跳的右手食指/中指小人保持稳定时，拇指/无名指/小指抖动不应破坏评分。",
                ),
                _spec(
                    "jump_right_noncore_fingers_shift",
                    "positive",
                    operations=[
                        {"group": "right_hand", "type": "shift", "delta": [0.35, -0.25, 0.0], "landmarks": RIGHT_NONCORE_FINGERS}
                    ],
                    min_score=min_score,
                    rationale="非语义手指整体偏移，模拟用户自然蜷曲或张开无关手指。",
                ),
                _spec(
                    "jump_right_noncore_fingers_motion_drift",
                    "positive",
                    operations=[
                        {"group": "right_hand", "type": "motion_drift", "amplitude": [0.22, -0.18, 0.0], "landmarks": RIGHT_NONCORE_FINGERS}
                    ],
                    min_score=min_score,
                    rationale="非语义手指连续漂移，核心两指小人和左手地面仍应保持可评分。",
                ),
                _spec(
                    "jump_right_noncore_fingers_scramble",
                    "positive",
                    operations=[{"group": "right_hand", "type": "scramble", "landmarks": RIGHT_NONCORE_FINGERS}],
                    min_score=min_score,
                    rationale="非语义手指局部顺序异常，不能盖过右手食指/中指与左手地面的核心关系。",
                ),
                _spec(
                    "jump_right_index_middle_collapse_diagnostic",
                    "diagnostic",
                    operations=[{"group": "right_hand", "type": "collapse_to_wrist", "landmarks": RIGHT_INDEX_MIDDLE_FINGERS}],
                    rationale="诊断记录：右手食指/中指结构破坏的当前边界；硬负例由遮挡/裁切/相位门覆盖。",
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
    standard, standard_detail = _transform_sequence(
        loaded_standard,
        "standard_base",
        profile=profile,
        operations=[],
    )
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(word, min_score):
        query, detail = _transform_sequence(
            loaded_standard,
            str(spec["variant"]),
            profile=profile,
            operations=spec["operations"],
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
        "standard_transform_detail": standard_detail,
        "semantic_profile": _profile_summary(profile),
        "gate_pass": all(bool(row["passed"]) for row in positive_rows),
        "weakest_positive_score": float(weakest_positive["score"]) if weakest_positive else None,
        "weakest_positive_variant": weakest_positive["variant"] if weakest_positive else "",
        "strongest_negative_score": None,
        "strongest_negative_variant": "",
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
        "operation_groups",
        "operation_landmarks",
        "operation_types",
        "changed_visible_points",
        "total_selected_points",
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
                        "operation_groups": ",".join(row.get("operation_groups") or []),
                        "operation_landmarks": ",".join(str(value) for value in (row.get("operation_landmarks") or [])),
                        "operation_types": ",".join(row.get("operation_types") or []),
                        "changed_visible_points": row.get("changed_visible_points"),
                        "total_selected_points": row.get("total_selected_points"),
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
        "# 花/跳非核心手与非语义手指干扰鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，在手部坐标层合成非核心手/非语义手指干扰并重建 hand-shape/motion/relation 特征；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：`花` 的非核心左手干扰不应拖低右手绽放；`跳` 的右手非语义手指干扰不应拖低左手地面+右手两指小人的核心语义。",
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
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向干扰 | 诊断最低分 | 最弱诊断核心扰动 | 门槛 |")
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
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | 操作组 | landmark | capture_quality | semantic_floor | 说明 |")
        lines.append("|---|---|---|---:|---|---|---|---|---|---|")
        for row in sorted(item["variants"], key=lambda value: (value["kind"], float(value["score"]))):
            quality = row.get("capture_quality") or {}
            floor = row.get("semantic_floor") or {}
            if row["kind"] == "positive":
                threshold = f">= {row.get('min_score')}"
                status = "PASS" if row["passed"] else "FAIL"
            else:
                threshold = "diagnostic"
                status = "DIAG"
            groups = ",".join(row.get("operation_groups") or []) or "-"
            landmarks = ",".join(str(value) for value in (row.get("operation_landmarks") or [])) or "-"
            lines.append(
                f"| {row['variant']} | {row['kind']} | {status} | {_fmt(row['score'])} | "
                f"{threshold} | {groups} | {landmarks} | "
                f"{quality.get('status') or '-'}:{quality.get('reason') or '-'} | "
                f"{floor.get('source') or '-'}:{floor.get('reason') or '-'} | {row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 正向门只覆盖非核心手或非语义手指干扰，不会放宽 `花` 的右手绽放核心或 `跳` 的双手关系要求。",
            "- 诊断行用于记录核心手形破坏的当前边界；正式负向保护仍由 fingertip-occlusion、edge-clipping、hand-role、phase-order 等已推广子门承担。",
            "- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run non-core hand/finger distractor robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_noncore_hand_distractor_robustness_gate_current"))
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
        "claim_policy": "synthetic non-core hand/finger distractor robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": backend_status,
        "passed": passed,
        "min_score": args.min_score,
        "results": results,
    }

    json_path = output_dir / "flower_jump_noncore_hand_distractor_robustness_gate.json"
    md_path = output_dir / "flower_jump_noncore_hand_distractor_robustness_gate.md"
    csv_path = output_dir / "flower_jump_noncore_hand_distractor_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳非核心手干扰鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳非核心手干扰鲁棒性报告：{md_path}")
    print(f"已生成花/跳非核心手干扰鲁棒性 CSV：{csv_path}")
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

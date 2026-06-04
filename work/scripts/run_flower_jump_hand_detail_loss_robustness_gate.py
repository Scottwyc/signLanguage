#!/usr/bin/env python3
"""Stress-test flower/jump scoring against low-detail hand landmarks.

Low-resolution or low-light browser capture can preserve coarse hand centers
and fingertip extent while simplifying the small bends between MCP/PIP/DIP/tip
landmarks. Existing gates cover coordinate precision, landmark noise, finger
curl style, and finger-length style; this gate targets detector detail loss by
straightening inner finger joints toward their MCP-to-tip axis. Strong fingertip
collapse is recorded only as a diagnostic boundary.

This script edits cached skeleton sequences in memory only. It does not call
/api/score, run Holistic, move the web marker, or restart 5080.
"""

from __future__ import annotations

import argparse
import csv
import json
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
PALM_ANCHOR_INDICES = [0, 5, 9, 13, 17]
FINGER_CHAINS: Dict[str, List[int]] = {
    "thumb": [1, 2, 3, 4],
    "index": [5, 6, 7, 8],
    "middle": [9, 10, 11, 12],
    "ring": [13, 14, 15, 16],
    "pinky": [17, 18, 19, 20],
}


def _all_fingers() -> List[str]:
    return list(FINGER_CHAINS)


def _palm_anchor(coords: np.ndarray, valid: np.ndarray) -> Optional[np.ndarray]:
    anchor_indices = [idx for idx in PALM_ANCHOR_INDICES if idx < len(valid) and bool(valid[idx])]
    if not anchor_indices:
        anchor_indices = [int(idx) for idx in np.where(valid)[0]]
    if not anchor_indices:
        return None
    return coords[anchor_indices].mean(axis=0)


def _axis_smooth_coords(
    coords: np.ndarray,
    valid: np.ndarray,
    fingers: Sequence[str],
    amount: float,
) -> Tuple[np.ndarray, int]:
    coords = coords.copy()
    changed = 0
    for finger in fingers:
        chain = FINGER_CHAINS.get(str(finger))
        if not chain:
            continue
        base_idx = chain[0]
        tip_idx = chain[-1]
        if base_idx >= len(valid) or tip_idx >= len(valid):
            continue
        if not bool(valid[base_idx]) or not bool(valid[tip_idx]):
            continue
        base = coords[base_idx].copy()
        axis = coords[tip_idx] - base
        denominator = float(len(chain) - 1)
        for position, landmark_idx in enumerate(chain[1:-1], start=1):
            if landmark_idx >= len(valid) or not bool(valid[landmark_idx]):
                continue
            target = base + axis * (float(position) / denominator)
            coords[landmark_idx] = coords[landmark_idx] + float(amount) * (target - coords[landmark_idx])
            changed += 1
    return coords, changed


def _tip_anchor_blend_coords(
    coords: np.ndarray,
    valid: np.ndarray,
    fingers: Sequence[str],
    amount: float,
) -> Tuple[np.ndarray, int]:
    coords = coords.copy()
    anchor = _palm_anchor(coords, valid)
    if anchor is None:
        return coords, 0
    changed = 0
    for finger in fingers:
        chain = FINGER_CHAINS.get(str(finger))
        if not chain:
            continue
        denominator = float(max(1, len(chain) - 1))
        for position, landmark_idx in enumerate(chain[1:], start=1):
            if landmark_idx >= len(valid) or not bool(valid[landmark_idx]):
                continue
            distal_weight = float(position) / denominator
            coords[landmark_idx] = coords[landmark_idx] + float(amount) * distal_weight * (anchor - coords[landmark_idx])
            changed += 1
    return coords, changed


def _apply_operation(
    coords: np.ndarray,
    valid: np.ndarray,
    operation: Dict[str, Any],
) -> Tuple[np.ndarray, int]:
    fingers = operation.get("fingers") or _all_fingers()
    if operation["operation"] == "axis_smooth":
        return _axis_smooth_coords(coords, valid, fingers, float(operation["amount"]))
    if operation["operation"] == "tip_anchor_blend":
        return _tip_anchor_blend_coords(coords, valid, fingers, float(operation["amount"]))
    raise ValueError(f"unknown hand-detail operation: {operation['operation']}")


def _mutated_sequence(
    seq: SequenceData,
    name: str,
    *,
    operations: Sequence[Dict[str, Any]],
    profile: Any,
) -> Tuple[SequenceData, Dict[str, Any]]:
    base = _strip_to_base_groups(seq)
    items: List[FrameFeature] = []
    changed_visible_points = 0
    changed_frames = 0
    operation_counts: Dict[str, int] = {}

    for frame_position, frame in enumerate(base.features):
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        presence = dict(frame.presence)
        frame_changed = False

        for operation in operations:
            every_n = int(operation.get("every_n") or 1)
            if every_n > 1 and frame_position % every_n != 0:
                continue
            for group in operation.get("groups") or HAND_GROUPS:
                coords, valid = _hand_array(frame, str(group))
                if coords is None or valid is None or not valid.any():
                    continue
                updated, changed = _apply_operation(coords, valid, operation)
                if changed:
                    changed_visible_points += changed
                    frame_changed = True
                    operation_counts[str(operation["operation"])] = operation_counts.get(str(operation["operation"]), 0) + changed
                _set_hand_group(frame, vector, mask, str(group), updated, valid)
                presence[str(group)] = bool(valid.any())

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
        "operation": "hand_detail_loss",
        "operations": [dict(operation) for operation in operations],
        "operation_counts": operation_counts,
        "changed_frames": changed_frames,
        "changed_visible_points": changed_visible_points,
        "total_frames": len(base.features),
    }
    return _sequence_with_relative_motion_features(transformed, profile), detail


def _op(
    operation: str,
    *,
    groups: Sequence[str],
    fingers: Sequence[str],
    amount: float,
    every_n: int = 1,
) -> Dict[str, Any]:
    return {
        "operation": operation,
        "groups": list(groups),
        "fingers": list(fingers),
        "amount": float(amount),
        "every_n": int(every_n),
    }


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
        "operations": [dict(operation) for operation in operations],
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
            rationale="标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。",
        ),
        _spec(
            "both_hands_inner_axis_smooth_0.30",
            "positive",
            operations=[
                _op("axis_smooth", groups=HAND_GROUPS, fingers=_all_fingers(), amount=0.30),
            ],
            min_score=min_score,
            rationale="双手内关节向 MCP-tip 轴轻微线性化，模拟低分辨率下细小关节弯折被平滑。",
        ),
        _spec(
            "right_hand_inner_axis_smooth_0.45",
            "positive",
            operations=[
                _op("axis_smooth", groups=["right_hand"], fingers=_all_fingers(), amount=0.45),
            ],
            min_score=min_score,
            rationale="右手内关节中等线性化，覆盖主导手局部细节损失但保留指尖伸展。",
        ),
        _spec(
            "sparse_both_hands_inner_axis_smooth_0.70_every_5f",
            "positive",
            operations=[
                _op("axis_smooth", groups=HAND_GROUPS, fingers=_all_fingers(), amount=0.70, every_n=5),
            ],
            min_score=min_score,
            rationale="每 5 帧一次较强内关节线性化，模拟偶发低细节关键帧。",
        ),
    ]
    if word == "花":
        return specs + [
            _spec(
                "flower_opening_right_inner_axis_smooth_0.60",
                "positive",
                operations=[
                    _op("axis_smooth", groups=["right_hand"], fingers=_all_fingers(), amount=0.60),
                ],
                min_score=min_score,
                rationale="花的右手绽放手形保留指尖外展，只压低 PIP/DIP 细节。",
            ),
            _spec(
                "flower_opening_right_tip_anchor_blend_0.30_diagnostic",
                "diagnostic",
                operations=[
                    _op("tip_anchor_blend", groups=["right_hand"], fingers=_all_fingers(), amount=0.30),
                ],
                rationale="花的绽放指尖明显向掌心塌缩可能破坏手形，只作为诊断边界。",
            ),
            _spec(
                "both_hands_tip_anchor_blend_0.38_diagnostic",
                "diagnostic",
                operations=[
                    _op("tip_anchor_blend", groups=HAND_GROUPS, fingers=_all_fingers(), amount=0.38),
                ],
                rationale="双手强细节塌缩不代表正常网页低细节采集，只记录分数。",
            ),
        ]
    if word == "跳":
        return specs + [
            _spec(
                "jump_right_person_index_middle_axis_smooth_0.65",
                "positive",
                operations=[
                    _op("axis_smooth", groups=["right_hand"], fingers=["index", "middle"], amount=0.65),
                ],
                min_score=min_score,
                rationale="跳的右手小人两指保留指尖和基座，只压低两指内关节细节。",
            ),
            _spec(
                "jump_right_person_tip_anchor_blend_0.32_diagnostic",
                "diagnostic",
                operations=[
                    _op("tip_anchor_blend", groups=["right_hand"], fingers=["index", "middle"], amount=0.32),
                ],
                rationale="跳的右手小人两指明显向掌心塌缩可能改变手形，只作为诊断边界。",
            ),
            _spec(
                "both_hands_tip_anchor_blend_0.38_diagnostic",
                "diagnostic",
                operations=[
                    _op("tip_anchor_blend", groups=HAND_GROUPS, fingers=_all_fingers(), amount=0.38),
                ],
                rationale="双手强细节塌缩不代表正常网页低细节采集，只记录分数。",
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
    standard, standard_detail = _mutated_sequence(
        loaded_standard,
        "standard_base",
        operations=[],
        profile=profile,
    )
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(word, min_score):
        query, detail = _mutated_sequence(
            loaded_standard,
            str(spec["variant"]),
            operations=spec["operations"],
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
        "operations",
        "operation_counts",
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
                        "operations": json.dumps(row.get("operations") or [], ensure_ascii=False),
                        "operation_counts": json.dumps(row.get("operation_counts") or {}, ensure_ascii=False),
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
        "# 花/跳手部细节损失鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，合成低分辨率/低细节下的手部内关节线性化后重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：低细节下保留手中心、MCP 和指尖范围时仍可正常评分；明显指尖塌缩只记录诊断边界。",
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
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向细节损失 | 诊断最低分 | 最弱诊断边界 | 门槛 |")
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
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | 改动帧 | 改动点 | 操作 | capture_quality | semantic_floor | 说明 |")
        lines.append("|---|---|---|---:|---|---:|---:|---|---|---|---|")
        for row in sorted(item["variants"], key=lambda value: (value["kind"], float(value["score"]))):
            quality = row.get("capture_quality") or {}
            floor = row.get("semantic_floor") or {}
            if row["kind"] == "positive":
                threshold = f">= {row.get('min_score')}"
                status = "PASS" if row["passed"] else "FAIL"
            else:
                threshold = "diagnostic"
                status = "DIAG"
            operations = ",".join(
                [
                    f"{operation.get('operation')}:{operation.get('groups')}:{operation.get('fingers')}:{operation.get('amount')}"
                    for operation in row.get("operations") or []
                ]
            )
            lines.append(
                f"| {row['variant']} | {row['kind']} | {status} | {_fmt(row['score'])} | "
                f"{threshold} | {row.get('changed_frames')} | {row.get('changed_visible_points')} | "
                f"{operations or '-'} | {quality.get('status') or '-'}:{quality.get('reason') or '-'} | "
                f"{floor.get('source') or '-'}:{floor.get('reason') or '-'} | {row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 该门补充的是低分辨率/低细节下的 hand landmark 简化，不替代已有 coordinate-precision、landmark-noise、finger-curl-style 或 finger-length-style 门。",
            "- 正向变体只线性化 PIP/DIP 等内关节，保留 MCP、指尖位置和粗手形；强指尖向掌心塌缩只观察诊断边界。",
            "- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run hand-detail-loss robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_hand_detail_loss_robustness_gate_current"))
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
        "claim_policy": "synthetic hand-detail-loss robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": backend_status,
        "passed": passed,
        "min_score": args.min_score,
        "results": results,
    }

    json_path = output_dir / "flower_jump_hand_detail_loss_robustness_gate.json"
    md_path = output_dir / "flower_jump_hand_detail_loss_robustness_gate.md"
    csv_path = output_dir / "flower_jump_hand_detail_loss_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳手部细节损失鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳手部细节损失鲁棒性报告：{md_path}")
    print(f"已生成花/跳手部细节损失鲁棒性 CSV：{csv_path}")
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

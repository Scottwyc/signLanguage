#!/usr/bin/env python3
"""Stress-test flower/jump scoring against mild finger-curl style changes.

Different users keep fingers more or less straight while preserving the same
sign semantics. Existing gates cover finger opening amplitude, local hand
scale, image-plane rotation, and out-of-plane palm tilt; this gate targets
finger articulation style by bending selected finger chains toward their MCP
anchors. Mild curl should remain scoreable, while strong curl is recorded as a
diagnostic boundary.

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
FINGER_CHAINS: Dict[str, List[int]] = {
    "thumb": [1, 2, 3, 4],
    "index": [5, 6, 7, 8],
    "middle": [9, 10, 11, 12],
    "ring": [13, 14, 15, 16],
    "pinky": [17, 18, 19, 20],
}
DISTAL_STRENGTHS = [0.20, 0.45, 0.70]


def _curl_coords(coords: np.ndarray, valid: np.ndarray, fingers: Sequence[str], amount: float) -> Tuple[np.ndarray, int]:
    coords = coords.copy()
    changed = 0
    for finger in fingers:
        chain = FINGER_CHAINS.get(str(finger))
        if not chain:
            continue
        base_idx = chain[0]
        if base_idx >= len(valid) or not bool(valid[base_idx]):
            continue
        base = coords[base_idx].copy()
        for strength, landmark_idx in zip(DISTAL_STRENGTHS, chain[1:]):
            if landmark_idx >= len(valid) or not bool(valid[landmark_idx]):
                continue
            coords[landmark_idx] = coords[landmark_idx] + float(amount) * float(strength) * (base - coords[landmark_idx])
            changed += 1
    return coords, changed


def _curl_sequence(
    seq: SequenceData,
    name: str,
    *,
    group_fingers: Dict[str, Sequence[str]],
    amount: float,
    profile: Any,
) -> Tuple[SequenceData, Dict[str, Any]]:
    base = _strip_to_base_groups(seq)
    items: List[FrameFeature] = []
    changed_visible_points = 0
    changed_frames = 0
    for frame in base.features:
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        presence = dict(frame.presence)
        frame_changed = False
        for group, fingers in group_fingers.items():
            coords, valid = _hand_array(frame, group)
            if coords is None or valid is None or not valid.any():
                continue
            updated, changed = _curl_coords(coords, valid, fingers, amount)
            if changed:
                changed_visible_points += changed
                frame_changed = True
            _set_hand_group(frame, vector, mask, group, updated, valid)
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
        "operation": "finger_curl_style",
        "group_fingers": {group: list(fingers) for group, fingers in group_fingers.items()},
        "amount": float(amount),
        "changed_frames": changed_frames,
        "changed_visible_points": changed_visible_points,
        "total_frames": len(base.features),
    }
    return _sequence_with_relative_motion_features(transformed, profile), detail


def _spec(
    variant: str,
    kind: str,
    *,
    group_fingers: Dict[str, Sequence[str]],
    amount: float,
    rationale: str,
    min_score: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": kind,
        "group_fingers": {group: list(fingers) for group, fingers in group_fingers.items()},
        "amount": float(amount),
        "min_score": min_score,
        "gated": kind == "positive",
        "rationale": rationale,
    }


def _variant_specs(word: str, min_score: float) -> List[Dict[str, Any]]:
    specs = [
        _spec(
            "self_recomputed",
            "positive",
            group_fingers={},
            amount=0.0,
            min_score=95.0,
            rationale="标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。",
        )
    ]
    if word == "花":
        return specs + [
            _spec(
                "right_opening_all_fingers_curl_0.10",
                "positive",
                group_fingers={"right_hand": ["thumb", "index", "middle", "ring", "pinky"]},
                amount=0.10,
                min_score=min_score,
                rationale="开花手五指轻微弯曲，但仍保持绽放开合轨迹。",
            ),
            _spec(
                "right_opening_index_middle_curl_0.16",
                "positive",
                group_fingers={"right_hand": ["index", "middle"]},
                amount=0.16,
                min_score=min_score,
                rationale="开花手食指/中指轻微弯曲，覆盖用户手指不完全伸直。",
            ),
            _spec(
                "right_opening_ring_pinky_curl_0.16",
                "positive",
                group_fingers={"right_hand": ["ring", "pinky"]},
                amount=0.16,
                min_score=min_score,
                rationale="开花手无名指/小指轻微弯曲，核心开花语义仍应保留。",
            ),
            _spec(
                "right_opening_all_fingers_curl_0.24_diagnostic",
                "diagnostic",
                group_fingers={"right_hand": ["thumb", "index", "middle", "ring", "pinky"]},
                amount=0.24,
                rationale="开花手整体较强弯曲只记录诊断边界。",
            ),
            _spec(
                "right_opening_all_fingers_curl_0.38_diagnostic",
                "diagnostic",
                group_fingers={"right_hand": ["thumb", "index", "middle", "ring", "pinky"]},
                amount=0.38,
                rationale="开花手强弯曲可能破坏开放手形，只作诊断。",
            ),
        ]
    if word == "跳":
        return specs + [
            _spec(
                "right_person_index_middle_curl_0.10",
                "positive",
                group_fingers={"right_hand": ["index", "middle"]},
                amount=0.10,
                min_score=min_score,
                rationale="右手两指小人轻微弯曲，但仍保持跳跃角色和双手关系。",
            ),
            _spec(
                "right_person_index_middle_curl_0.16",
                "positive",
                group_fingers={"right_hand": ["index", "middle"]},
                amount=0.16,
                min_score=min_score,
                rationale="右手两指小人中等轻微弯曲，覆盖用户两指不完全伸直。",
            ),
            _spec(
                "right_nonsemantic_fingers_curl_0.22",
                "positive",
                group_fingers={"right_hand": ["thumb", "ring", "pinky"]},
                amount=0.22,
                min_score=min_score,
                rationale="右手非语义手指弯曲不应影响两指小人核心。",
            ),
            _spec(
                "left_ground_all_fingers_curl_0.22",
                "positive",
                group_fingers={"left_hand": ["thumb", "index", "middle", "ring", "pinky"]},
                amount=0.22,
                min_score=min_score,
                rationale="左手地面手指弯曲风格变化，手部位置和双手关系保持。",
            ),
            _spec(
                "right_person_index_middle_curl_0.32_diagnostic",
                "diagnostic",
                group_fingers={"right_hand": ["index", "middle"]},
                amount=0.32,
                rationale="两指小人明显弯曲只记录诊断边界。",
            ),
            _spec(
                "right_person_index_middle_curl_0.50_diagnostic",
                "diagnostic",
                group_fingers={"right_hand": ["index", "middle"]},
                amount=0.50,
                rationale="两指小人强弯曲可能破坏手形语义，只作诊断。",
            ),
        ]
    return specs


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
    standard, standard_detail = _curl_sequence(
        loaded_standard,
        "standard_base",
        group_fingers={},
        amount=0.0,
        profile=profile,
    )
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(word, min_score):
        query, curl_detail = _curl_sequence(
            loaded_standard,
            str(spec["variant"]),
            group_fingers=spec["group_fingers"],
            amount=float(spec["amount"]),
            profile=profile,
        )
        result = run_pair(standard, query, semantic_profile=profile, enable_cross_check=False)
        score_scale = result.get("score_scale") or {}
        row = {
            **spec,
            **curl_detail,
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
        "standard_curl_detail": standard_detail,
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
        "amount",
        "group_fingers",
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
                        "amount": row.get("amount"),
                        "group_fingers": json.dumps(row.get("group_fingers") or {}, ensure_ascii=False, sort_keys=True),
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
        "# 花/跳手指弯曲风格鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，剥离基础骨架组后将选定手指链向 MCP 锚点轻微弯曲，并重建 hand-shape、motion、two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：用户手指不完全伸直但语义动作仍正确时，`花/跳` 保持可评分；强弯曲只记录诊断边界。",
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
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向弯曲 | 诊断最低分 | 最弱诊断弯曲 | 门槛 |")
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
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | 弯曲量 | 改动帧 | normalized_distance | alignment | capture_quality | semantic_floor | 说明 |")
        lines.append("|---|---|---|---:|---|---:|---:|---:|---|---|---|---|")
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
            lines.append(
                f"| {row['variant']} | {row['kind']} | {status} | {_fmt(row['score'])} | "
                f"{threshold} | {_fmt(row.get('amount'), 2)} | {row.get('changed_frames')} | "
                f"{_fmt(row['normalized_distance'], 6)} | {policy.get('mode') or '-'} | "
                f"{quality.get('status') or '-'} | {floor.get('source') or '-'} | {row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 正向扰动只覆盖轻微手指弯曲风格差异，并保持手部位置、时序和核心动作关系不变。",
            "- 强弯曲不作为硬门，避免把真实手形语义错误推广为正常采集。",
            "- 该门是合成鲁棒性压力测试，不能替代真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run finger-curl style robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_finger_curl_style_robustness_gate_current"))
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
        "claim_policy": "synthetic finger-curl style robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "min_score": args.min_score,
        "backend_status": backend_status,
        "passed": passed,
        "results": results,
    }

    json_path = output_dir / "flower_jump_finger_curl_style_robustness_gate.json"
    md_path = output_dir / "flower_jump_finger_curl_style_robustness_gate.md"
    csv_path = output_dir / "flower_jump_finger_curl_style_robustness_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳手指弯曲风格鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳手指弯曲风格鲁棒性报告：{md_path}")
    print(f"已生成花/跳手指弯曲风格鲁棒性 CSV：{csv_path}")
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

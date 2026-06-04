#!/usr/bin/env python3
"""Stress-test flower/jump scoring against missing landmark masks.

This gate targets a practical webcam issue: seated users or partial occlusion
can make non-semantic pose/face landmarks unreliable, while the core hand
semantics must still be enforced. Positive variants drop non-critical groups
and should remain high. Negative variants drop required hand semantics and
should not be accepted as normal scores.

The script only reads cached Holistic JSON and edits skeleton masks in memory.
It does not call /api/score, run Holistic, move marker, or restart 5080.
"""

from __future__ import annotations

import argparse
import csv
import json
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from score_holistic_sequence_mvp import (
    DEFAULT_SEMANTIC_PROFILE_JSON,
    FrameFeature,
    SequenceData,
    _clone_frame,
    _clone_sequence,
    _profile_summary,
    load_semantic_profile,
    load_sequence,
    run_pair,
)


REPO_ROOT = Path("/data/WYC/signLanguage")
DEFAULT_TEMPLATE_ROOT = REPO_ROOT / "work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results"
DEFAULT_OUTPUT_BASE = REPO_ROOT / "work/generated/scoring_mvp_run3"
DEFAULT_BACKEND_URL = "http://127.0.0.1:5080"
DEFAULT_WORDS = ["花", "跳"]
HAND_SHAPE_GROUPS = {
    "left_hand": ["left_hand", "left_hand_shape"],
    "right_hand": ["right_hand", "right_hand_shape"],
}
ACCEPTED_NEGATIVE_QUALITY = {"needs_recapture", "semantic_mismatch"}


def _json_default(value: Any) -> Any:
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _load_backend_status(backend_url: str, timeout_sec: float) -> Dict[str, Any]:
    url = backend_url.rstrip("/") + "/api/status"
    try:
        with urllib.request.urlopen(url, timeout=timeout_sec) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return {"ok": True, "url": url, "payload": payload, "error": ""}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"ok": False, "url": url, "payload": {}, "error": str(exc)}


def _template_json(template_root: Path, word: str) -> Path:
    path = template_root / word / f"{word}_holistic_results.json"
    if not path.exists():
        raise FileNotFoundError(f"missing template json for {word}: {path}")
    return path


def _fmt(value: Any, digits: int = 3) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "-"


def _presence_ratio(seq: SequenceData) -> Dict[str, float]:
    if not seq.features:
        return {"pose": 0.0, "left_hand": 0.0, "right_hand": 0.0, "face": 0.0}
    return {
        group: sum(1 for item in seq.features if item.presence.get(group)) / len(seq.features)
        for group in ["pose", "left_hand", "right_hand", "face"]
    }


def _expand_groups(groups: Sequence[str]) -> List[str]:
    expanded: List[str] = []
    for group in groups:
        for item in HAND_SHAPE_GROUPS.get(group, [group]):
            if item not in expanded:
                expanded.append(item)
    return expanded


def _mask_groups(seq: SequenceData, name: str, groups: Sequence[str]) -> SequenceData:
    expanded = _expand_groups(groups)
    items: List[FrameFeature] = []
    for frame in seq.features:
        mask = frame.mask.copy()
        vector = frame.vector.copy()
        for group in expanded:
            if group not in frame.groups:
                continue
            sl = frame.groups[group]
            mask[sl] = 0.0
            vector[sl] = 0.0
        item = _clone_frame(frame, vector=vector, mask=mask)
        presence = dict(item.presence)
        if "pose" in expanded:
            presence["pose"] = False
        if "face" in expanded:
            presence["face"] = False
        if "left_hand" in expanded or "left_hand_shape" in expanded:
            presence["left_hand"] = False
        if "right_hand" in expanded or "right_hand_shape" in expanded:
            presence["right_hand"] = False
        item.presence = presence
        items.append(item)
    return _clone_sequence(seq, name, items)


def _variant_specs(word: str) -> List[Dict[str, Any]]:
    common_positive = [
        {
            "variant": "drop_face",
            "groups": ["face"],
            "kind": "positive",
            "expected": "score_high",
            "min_score": 70.0,
            "rationale": "面部不是花/跳核心语义。",
        },
        {
            "variant": "drop_pose",
            "groups": ["pose"],
            "kind": "positive",
            "expected": "score_high",
            "min_score": 70.0,
            "rationale": "坐姿或躯干不完整不应主导手部语义评分。",
        },
        {
            "variant": "drop_pose_face",
            "groups": ["pose", "face"],
            "kind": "positive",
            "expected": "score_high",
            "min_score": 70.0,
            "rationale": "只保留手部语义时应仍可打出正常/边界分。",
        },
    ]
    if word == "花":
        return common_positive + [
            {
                "variant": "drop_left_noncore_hand",
                "groups": ["left_hand"],
                "kind": "positive",
                "expected": "score_high",
                "min_score": 65.0,
                "rationale": "花的核心是开花手的张开动作，非核心手缺失不应严重扣分。",
            },
            {
                "variant": "drop_right_core_hand",
                "groups": ["right_hand"],
                "kind": "negative",
                "expected": "not_accepted",
                "max_score": 45.0,
                "rationale": "开花手缺失时不能被当作正确花动作。",
            },
            {
                "variant": "drop_both_hands",
                "groups": ["left_hand", "right_hand"],
                "kind": "negative",
                "expected": "not_accepted",
                "max_score": 35.0,
                "rationale": "双手缺失时必须低分或建议重采。",
            },
        ]
    if word == "跳":
        return common_positive + [
            {
                "variant": "drop_left_ground_hand",
                "groups": ["left_hand"],
                "kind": "negative",
                "expected": "not_accepted",
                "max_score": 45.0,
                "rationale": "跳需要左手地面，左手缺失不能通过。",
            },
            {
                "variant": "drop_right_jumping_hand",
                "groups": ["right_hand"],
                "kind": "negative",
                "expected": "not_accepted",
                "max_score": 45.0,
                "rationale": "跳需要右手两指小人，右手缺失不能通过。",
            },
            {
                "variant": "drop_both_hands",
                "groups": ["left_hand", "right_hand"],
                "kind": "negative",
                "expected": "not_accepted",
                "max_score": 35.0,
                "rationale": "双手关系完全缺失时必须低分或建议重采。",
            },
        ]
    return common_positive


def _row_passed(row: Dict[str, Any]) -> bool:
    score = float(row["score"])
    if row["kind"] == "positive":
        return score >= float(row["min_score"])
    quality = (row.get("capture_quality") or {}).get("status")
    return score <= float(row["max_score"]) or quality in ACCEPTED_NEGATIVE_QUALITY


def _run_word(
    word: str,
    template_root: Path,
    semantic_profile_json: Path,
    feature_mode: str,
) -> Dict[str, Any]:
    standard_json = _template_json(template_root, word)
    standard = load_sequence(standard_json, feature_mode, force_bbox=False)
    profile = load_semantic_profile(word, semantic_profile_json)
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(word):
        query = _mask_groups(standard, spec["variant"], spec["groups"])
        result = run_pair(standard, query, semantic_profile=profile, enable_cross_check=False)
        score_scale = result.get("score_scale") or {}
        row = {
            **spec,
            "score": float(result["prototype_score"]),
            "dtw_distance": float(result["dtw_distance"]),
            "normalized_distance": float(result["normalized_distance"]),
            "alignment_policy": result.get("alignment_policy"),
            "query_presence": _presence_ratio(query),
            "capture_quality": score_scale.get("capture_quality"),
            "semantic_floor": score_scale.get("semantic_floor"),
            "required_presence_penalty": (result.get("sequence_penalty") or {}).get("required_presence_penalty"),
        }
        row["passed"] = _row_passed(row)
        rows.append(row)
    positive_rows = [row for row in rows if row["kind"] == "positive"]
    negative_rows = [row for row in rows if row["kind"] == "negative"]
    weakest_positive = min(positive_rows, key=lambda row: float(row["score"])) if positive_rows else None
    strongest_negative = max(negative_rows, key=lambda row: float(row["score"])) if negative_rows else None
    return {
        "word": word,
        "standard_json": str(standard_json),
        "standard_length": len(standard.features),
        "standard_presence": _presence_ratio(standard),
        "semantic_profile": _profile_summary(profile),
        "gate_pass": all(bool(row["passed"]) for row in rows),
        "weakest_positive_score": float(weakest_positive["score"]) if weakest_positive else None,
        "weakest_positive_variant": weakest_positive["variant"] if weakest_positive else "",
        "strongest_negative_score": float(strongest_negative["score"]) if strongest_negative else None,
        "strongest_negative_variant": strongest_negative["variant"] if strongest_negative else "",
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
        "max_score",
        "capture_quality_status",
        "capture_quality_reason",
        "semantic_floor_reason",
        "required_presence_penalty",
        "query_left_presence",
        "query_right_presence",
        "query_pose_presence",
        "query_face_presence",
        "rationale",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in results:
            for row in item["variants"]:
                quality = row.get("capture_quality") or {}
                floor = row.get("semantic_floor") or {}
                presence = row.get("query_presence") or {}
                writer.writerow(
                    {
                        "word": item["word"],
                        "variant": row.get("variant"),
                        "kind": row.get("kind"),
                        "passed": row.get("passed"),
                        "score": row.get("score"),
                        "min_score": row.get("min_score"),
                        "max_score": row.get("max_score"),
                        "capture_quality_status": quality.get("status"),
                        "capture_quality_reason": quality.get("reason"),
                        "semantic_floor_reason": floor.get("reason"),
                        "required_presence_penalty": row.get("required_presence_penalty"),
                        "query_left_presence": presence.get("left_hand"),
                        "query_right_presence": presence.get("right_hand"),
                        "query_pose_presence": presence.get("pose"),
                        "query_face_presence": presence.get("face"),
                        "rationale": row.get("rationale"),
                    }
                )


def _build_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# 花/跳缺失与关键 mask 鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，在骨架特征层面修改 mask；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：非关键 `pose/face` 或花的非核心手缺失时不应明显扣分；关键手部语义缺失时必须低分或进入重采/语义失败诊断。",
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
    lines.append("| 目标词 | 状态 | 最弱正向变体 | 正向最低分 | 最强关键缺失变体 | 关键缺失最高分 |")
    lines.append("|---|---|---|---:|---|---:|")
    for item in payload["results"]:
        lines.append(
            f"| {item['word']} | {'PASS' if item['gate_pass'] else 'FAIL'} | "
            f"{item['weakest_positive_variant']} | {_fmt(item['weakest_positive_score'])} | "
            f"{item['strongest_negative_variant']} | {_fmt(item['strongest_negative_score'])} |"
        )
    lines.append("")
    lines.append("## 分项明细")
    for item in payload["results"]:
        lines.extend(["", f"### {item['word']}", "", f"- 标准序列：`{item['standard_json']}`", ""])
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | capture_quality | reason | 说明 |")
        lines.append("|---|---|---|---:|---|---|---|---|")
        for row in sorted(item["variants"], key=lambda x: (x["kind"], float(x["score"]))):
            quality = row.get("capture_quality") or {}
            floor = row.get("semantic_floor") or {}
            threshold = f">= {row.get('min_score')}" if row["kind"] == "positive" else f"<= {row.get('max_score')} 或重采/语义失败"
            reason = quality.get("reason") or floor.get("reason") or "-"
            lines.append(
                f"| {row['variant']} | {row['kind']} | {'PASS' if row['passed'] else 'FAIL'} | "
                f"{_fmt(row['score'])} | {threshold} | {quality.get('status') or '-'} | {reason} | {row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 正向变体验证非关键特征不会盖过核心手语语义。",
            "- 负向变体验证核心手部语义缺失时不会被 DTW 或语义 floor 误抬成正常分。",
            "- 该门仍是合成 mask 压力测试，不能替代真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run missing/mask robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_missing_mask_robustness_gate_current"))
    parser.add_argument("--words", nargs="+", default=DEFAULT_WORDS)
    parser.add_argument("--feature-mode", choices=["auto", "landmark", "bbox"], default="auto")
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
        )
        for word in args.words
    ]
    backend_status = _load_backend_status(args.backend_url, args.status_timeout_sec)
    passed = all(bool(item["gate_pass"]) for item in results)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "claim_policy": "synthetic missing-mask robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": backend_status,
        "passed": passed,
        "accepted_negative_quality": sorted(ACCEPTED_NEGATIVE_QUALITY),
        "results": results,
    }

    json_path = output_dir / "flower_jump_missing_mask_robustness_gate.json"
    md_path = output_dir / "flower_jump_missing_mask_robustness_gate.md"
    csv_path = output_dir / "flower_jump_missing_mask_robustness_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳缺失 mask 鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳缺失 mask 鲁棒性报告：{md_path}")
    print(f"已生成花/跳缺失 mask 鲁棒性 CSV：{csv_path}")
    print(f"综合状态：{'PASS' if passed else 'FAIL'}")
    for item in results:
        print(
            f"- {item['word']}: {'PASS' if item['gate_pass'] else 'FAIL'} "
            f"positive_min={_fmt(item['weakest_positive_score'])} "
            f"negative_max={_fmt(item['strongest_negative_score'])}"
        )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

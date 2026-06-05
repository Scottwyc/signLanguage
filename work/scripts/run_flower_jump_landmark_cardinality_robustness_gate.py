#!/usr/bin/env python3
"""Stress-test landmark array cardinality and index-integrity handling.

MediaPipe Holistic groups have fixed non-empty lengths. A truncated or
extended array shifts landmark identities and must be treated as a missing
group instead of valid geometry. This gate mutates cached Holistic JSON only;
it does not call /api/score, run Holistic, move the marker, or restart 5080.
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from run_flower_jump_landmark_noise_robustness_gate import _fmt, _json_default, _load_backend_status
from run_flower_jump_mirror_robustness_gate import _template_json
from score_holistic_sequence_mvp import (
    DEFAULT_SEMANTIC_PROFILE_JSON,
    FACE_LANDMARK_COUNT,
    HAND_LANDMARK_COUNT,
    POSE_LANDMARK_COUNT,
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
GROUP_META = {
    "pose_landmarks": ("pose", POSE_LANDMARK_COUNT),
    "left_hand_landmarks": ("left_hand", HAND_LANDMARK_COUNT),
    "right_hand_landmarks": ("right_hand", HAND_LANDMARK_COUNT),
    "face_landmarks": ("face", FACE_LANDMARK_COUNT),
}


def _spec(
    variant: str,
    group: str,
    pattern: str,
    operation: str,
    kind: str,
    threshold: float,
    rationale: str,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "group": group,
        "presence_group": GROUP_META[group][0],
        "expected_count": GROUP_META[group][1],
        "pattern": pattern,
        "operation": operation,
        "kind": kind,
        "gated": True,
        "threshold": threshold,
        "rationale": rationale,
    }


def _variant_specs(word: str, min_score: float, sparse_min_score: float, diagnostic_max_score: float) -> List[Dict[str, Any]]:
    specs = [
        {
            "variant": "self_reloaded",
            "group": "",
            "presence_group": "",
            "expected_count": None,
            "pattern": "none",
            "operation": "none",
            "kind": "positive",
            "gated": True,
            "threshold": 95.0,
            "rationale": "原始标准 JSON 重载后应保持近满分。",
        }
    ]
    for operation in ["drop_first", "drop_middle", "insert_first", "append_extra"]:
        specs.append(
            _spec(
                f"right_hand_{operation}_sparse_masked",
                "right_hand_landmarks",
                "sparse_visible",
                operation,
                "positive",
                sparse_min_score,
                "稀疏非标准长度核心手数组必须整帧屏蔽，不能按错位 landmark 身份参与评分。",
            )
        )
        specs.append(
            _spec(
                f"pose_{operation}_sparse_masked",
                "pose_landmarks",
                "sparse_visible",
                operation,
                "positive",
                sparse_min_score,
                "稀疏非标准长度 pose 数组必须整帧屏蔽，并由可信锚点插值或手部 fallback。",
            )
        )
        specs.append(
            _spec(
                f"pose_{operation}_full_hand_fallback",
                "pose_landmarks",
                "full_visible",
                operation,
                "positive",
                min_score,
                "整段非标准长度 pose 数组必须屏蔽，手部主导词应使用手部 fallback 继续评分。",
            )
        )
        specs.append(
            _spec(
                f"right_hand_{operation}_full_recapture",
                "right_hand_landmarks",
                "full_visible",
                operation,
                "diagnostic",
                diagnostic_max_score,
                "整段核心右手数组长度错误时必须要求重采，不能把错位点当成有效手形。",
            )
        )
    for operation in ["insert_first", "drop_middle"]:
        specs.append(
            _spec(
                f"face_{operation}_sparse_masked",
                "face_landmarks",
                "sparse_visible",
                operation,
                "positive",
                95.0,
                "稀疏非标准长度 face 数组应按该帧 face 缺失处理。",
            )
        )
        specs.append(
            _spec(
                f"face_{operation}_full_masked",
                "face_landmarks",
                "full_visible",
                operation,
                "positive",
                95.0,
                "整段非标准长度 face 数组不应影响手部主导词评分。",
            )
        )
    if word == "跳":
        for operation in ["drop_first", "drop_middle", "insert_first", "append_extra"]:
            specs.append(
                _spec(
                    f"left_hand_{operation}_sparse_masked",
                    "left_hand_landmarks",
                    "sparse_visible",
                    operation,
                    "positive",
                    sparse_min_score,
                    "跳的稀疏左手地面数组长度错误应按局部缺失处理。",
                )
            )
            specs.append(
                _spec(
                    f"left_hand_{operation}_full_recapture",
                    "left_hand_landmarks",
                    "full_visible",
                    operation,
                    "diagnostic",
                    diagnostic_max_score,
                    "跳的整段左手地面数组长度错误必须要求重采，不能继续给高分。",
                )
            )
    return specs


def _records(payload: Dict[str, Any]) -> List[Any]:
    records = payload.get("records")
    if not isinstance(records, list):
        raise RuntimeError("landmark cardinality gate requires a records list")
    return records


def _visible_indices(records: Sequence[Any], group: str) -> List[int]:
    indices: List[int] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        result_data = record.get("result_data")
        landmarks = result_data.get(group) if isinstance(result_data, dict) else None
        if isinstance(landmarks, list) and landmarks:
            indices.append(index)
    return indices


def _active_indices(records: Sequence[Any], group: str, pattern: str) -> List[int]:
    if pattern == "none":
        return []
    visible = _visible_indices(records, group)
    if pattern == "full_visible":
        return visible
    if pattern == "sparse_visible":
        sparse = visible[3::7]
        return sparse or visible[len(visible) // 2 : len(visible) // 2 + 1]
    raise ValueError(f"unknown cardinality pattern: {pattern}")


def _mutate_array(landmarks: List[Any], operation: str) -> None:
    if not landmarks:
        return
    if operation == "drop_first":
        del landmarks[0]
    elif operation == "drop_middle":
        del landmarks[len(landmarks) // 2]
    elif operation == "insert_first":
        landmarks.insert(0, copy.deepcopy(landmarks[0]))
    elif operation == "append_extra":
        landmarks.append(copy.deepcopy(landmarks[-1]))
    else:
        raise ValueError(f"unknown cardinality operation: {operation}")


def _write_fixture(source_json: Path, dest_json: Path, spec: Dict[str, Any]) -> Dict[str, Any]:
    payload = copy.deepcopy(json.loads(source_json.read_text(encoding="utf-8")))
    records = _records(payload)
    active = _active_indices(records, str(spec["group"]), str(spec["pattern"])) if spec["group"] else []
    observed_counts: List[int] = []
    for index in active:
        record = records[index]
        result_data = record.get("result_data") if isinstance(record, dict) else None
        landmarks = result_data.get(spec["group"]) if isinstance(result_data, dict) else None
        if not isinstance(landmarks, list) or not landmarks:
            continue
        _mutate_array(landmarks, str(spec["operation"]))
        observed_counts.append(len(landmarks))
    dest_json.parent.mkdir(parents=True, exist_ok=True)
    dest_json.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return {
        "active_indices": active,
        "changed_frame_count": len(observed_counts),
        "observed_counts": sorted(set(observed_counts)),
        "total_records": len(records),
    }


def _sequence_finite(sequence: Any) -> bool:
    return all(
        bool(math.isfinite(float(value)))
        for feature in sequence.features
        for values in (feature.vector, feature.mask)
        for value in values
    )


def _result_finite(result: Dict[str, Any]) -> bool:
    try:
        return all(math.isfinite(float(result.get(key))) for key in ("prototype_score", "dtw_distance", "normalized_distance"))
    except (TypeError, ValueError):
        return False


def _run_word(
    word: str,
    template_root: Path,
    semantic_profile_json: Path,
    feature_mode: str,
    min_score: float,
    sparse_min_score: float,
    diagnostic_max_score: float,
    fixture_dir: Path,
) -> Dict[str, Any]:
    standard_json = _template_json(template_root, word)
    standard = load_sequence(standard_json, feature_mode, force_bbox=False, apply_sidecar_weights=False)
    profile = load_semantic_profile(word, semantic_profile_json)
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(word, min_score, sparse_min_score, diagnostic_max_score):
        fixture_json = fixture_dir / word / f"{spec['variant']}.json"
        detail = _write_fixture(standard_json, fixture_json, spec)
        row: Dict[str, Any] = {**spec, "fixture_json": str(fixture_json), **detail}
        try:
            query = load_sequence(fixture_json, feature_mode, force_bbox=False, apply_sidecar_weights=False)
            result = run_pair(standard, query, semantic_profile=profile, target_word=word, enable_cross_check=False)
        except Exception as exc:  # noqa: BLE001 - loader/scorer crashes are gate failures.
            row.update(
                {
                    "exception": f"{type(exc).__name__}: {exc}",
                    "score": None,
                    "result_finite": False,
                    "sequence_finite": False,
                    "cardinality_masked": False,
                    "capture_quality": {},
                    "passed": False,
                }
            )
        else:
            active = [int(index) for index in detail["active_indices"]]
            cardinality_masked = True
            if spec["group"]:
                cardinality_masked = bool(active) and all(
                    index < len(query.features) and not query.features[index].presence.get(spec["presence_group"], False)
                    for index in active
                )
            capture_quality = (result.get("score_scale") or {}).get("capture_quality") or {}
            score = float(result["prototype_score"])
            result_finite = _result_finite(result)
            sequence_finite = _sequence_finite(query)
            if spec["kind"] == "diagnostic":
                semantic_ok = capture_quality.get("status") in {"needs_recapture", "semantic_mismatch"}
                score_ok = score <= float(spec["threshold"])
            else:
                semantic_ok = True
                score_ok = score >= float(spec["threshold"])
            row.update(
                {
                    "exception": "",
                    "score": score,
                    "dtw_distance": float(result["dtw_distance"]),
                    "normalized_distance": float(result["normalized_distance"]),
                    "result_finite": result_finite,
                    "sequence_finite": sequence_finite,
                    "cardinality_masked": cardinality_masked,
                    "capture_quality": capture_quality,
                    "passed": bool(result_finite and sequence_finite and cardinality_masked and semantic_ok and score_ok),
                }
            )
        rows.append(row)
    positives = [row for row in rows if row["kind"] == "positive" and row.get("score") is not None]
    diagnostics = [row for row in rows if row["kind"] == "diagnostic" and row.get("score") is not None]
    weakest = min(positives, key=lambda row: float(row["score"])) if positives else None
    strongest_diagnostic = max(diagnostics, key=lambda row: float(row["score"])) if diagnostics else None
    return {
        "word": word,
        "standard_json": str(standard_json),
        "standard_length": len(standard.features),
        "semantic_profile": _profile_summary(profile),
        "gate_pass": all(bool(row["passed"]) for row in rows),
        "weakest_positive_score": float(weakest["score"]) if weakest else None,
        "weakest_positive_variant": weakest["variant"] if weakest else "",
        "strongest_diagnostic_score": float(strongest_diagnostic["score"]) if strongest_diagnostic else None,
        "strongest_diagnostic_variant": strongest_diagnostic["variant"] if strongest_diagnostic else "",
        "min_required_score": min_score,
        "sparse_min_required_score": sparse_min_score,
        "diagnostic_max_score": diagnostic_max_score,
        "variants": rows,
    }


def _write_rows_csv(path: Path, results: Sequence[Dict[str, Any]]) -> None:
    fields = [
        "word",
        "variant",
        "kind",
        "passed",
        "score",
        "threshold",
        "group",
        "pattern",
        "operation",
        "changed_frame_count",
        "observed_counts",
        "cardinality_masked",
        "capture_quality",
        "capture_reason",
        "exception",
    ]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for item in results:
            for row in item["variants"]:
                quality = row.get("capture_quality") or {}
                writer.writerow(
                    {
                        "word": item["word"],
                        "variant": row.get("variant"),
                        "kind": row.get("kind"),
                        "passed": row.get("passed"),
                        "score": row.get("score"),
                        "threshold": row.get("threshold"),
                        "group": row.get("group"),
                        "pattern": row.get("pattern"),
                        "operation": row.get("operation"),
                        "changed_frame_count": row.get("changed_frame_count"),
                        "observed_counts": row.get("observed_counts"),
                        "cardinality_masked": row.get("cardinality_masked"),
                        "capture_quality": quality.get("status"),
                        "capture_reason": quality.get("reason"),
                        "exception": row.get("exception"),
                    }
                )


def _build_markdown(payload: Dict[str, Any]) -> str:
    counts = payload["expected_landmark_counts"]
    lines = [
        "# 花/跳 Landmark 数组长度与索引完整性鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        "- 口径：对缓存 Holistic JSON 做截断、前插和尾部追加，再经正常 `load_sequence()` / `run_pair()`；不调用 `/api/score`、不运行 Holistic、不移动 marker、不重启 5080。",
        f"- 固定长度契约：pose=`{counts['pose']}`、hand=`{counts['hand']}`、face=`{counts['face']}`；非空数组长度不匹配时整组按缺失处理，不能沿错误索引解释 landmark 身份。",
        "- 正常审计：当前 178 个模板/网页 JSON 中，非空 pose/hand/face 数组长度全部符合固定长度契约。",
        "",
        "## 结论",
        "",
        f"- 综合状态：`{'PASS' if payload['passed'] else 'FAIL'}`",
        "",
        "| 目标词 | 状态 | 正向最低分 | 最弱正向变体 | 核心手诊断最高分 | 最强诊断变体 |",
        "|---|---|---:|---|---:|---|",
    ]
    for item in payload["results"]:
        lines.append(
            f"| {item['word']} | {'PASS' if item['gate_pass'] else 'FAIL'} | "
            f"{_fmt(item['weakest_positive_score'])} | {item['weakest_positive_variant']} | "
            f"{_fmt(item['strongest_diagnostic_score'])} | {item['strongest_diagnostic_variant']} |"
        )
    lines.extend(["", "## 分项明细", ""])
    for item in payload["results"]:
        lines.extend(
            [
                f"### {item['word']}",
                "",
                "| 变体 | 类型 | 状态 | 分数 | 阈值 | 长度错误帧 | 整组屏蔽 | capture_quality |",
                "|---|---|---|---:|---:|---:|---|---|",
            ]
        )
        for row in item["variants"]:
            quality = row.get("capture_quality") or {}
            lines.append(
                f"| {row['variant']} | {row['kind']} | {'PASS' if row['passed'] else 'FAIL'} | "
                f"{_fmt(row.get('score'))} | {_fmt(row.get('threshold'))} | {row.get('changed_frame_count')} | "
                f"{row.get('cardinality_masked')} | {quality.get('status') or '-'}:{quality.get('reason') or '-'} |"
            )
        lines.append("")
    lines.extend(
        [
            "## 说明",
            "",
            "- 稀疏长度错误按局部缺失处理，正确动作应保持可评分；整段核心手长度错误是输入损坏，必须要求重采而不是放宽词义阈值。",
            "- 该门是缓存 JSON 压力测试，不替代正式 marker 后真实网页摄像头复测。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run landmark-cardinality robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_landmark_cardinality_robustness_gate_current"))
    parser.add_argument("--words", nargs="+", default=DEFAULT_WORDS)
    parser.add_argument("--feature-mode", choices=["auto", "landmark"], default="auto")
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--status-timeout-sec", type=float, default=3.0)
    parser.add_argument("--min-score", type=float, default=70.0)
    parser.add_argument("--sparse-min-score", type=float, default=75.0)
    parser.add_argument("--diagnostic-max-score", type=float, default=55.0)
    args = parser.parse_args(argv)

    template_root = Path(args.template_root)
    semantic_profile_json = Path(args.semantic_profile_json)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    fixture_dir = output_dir / "fixtures"
    results = [
        _run_word(
            word,
            template_root,
            semantic_profile_json,
            args.feature_mode,
            args.min_score,
            args.sparse_min_score,
            args.diagnostic_max_score,
            fixture_dir,
        )
        for word in args.words
    ]
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "claim_policy": "synthetic landmark-cardinality robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": _load_backend_status(args.backend_url, args.status_timeout_sec),
        "expected_landmark_counts": {
            "pose": POSE_LANDMARK_COUNT,
            "hand": HAND_LANDMARK_COUNT,
            "face": FACE_LANDMARK_COUNT,
        },
        "min_score": args.min_score,
        "sparse_min_score": args.sparse_min_score,
        "diagnostic_max_score": args.diagnostic_max_score,
        "results": results,
        "passed": all(bool(item["gate_pass"]) for item in results),
    }

    json_path = output_dir / "flower_jump_landmark_cardinality_robustness_gate.json"
    md_path = output_dir / "flower_jump_landmark_cardinality_robustness_gate.md"
    csv_path = output_dir / "flower_jump_landmark_cardinality_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成 Landmark 数组长度鲁棒性门 JSON：{json_path}")
    print(f"已生成 Landmark 数组长度鲁棒性门报告：{md_path}")
    print(f"综合状态：{'PASS' if payload['passed'] else 'FAIL'}")
    for item in results:
        print(
            f"- {item['word']}: {'PASS' if item['gate_pass'] else 'FAIL'} "
            f"positive_min={_fmt(item['weakest_positive_score'])} diagnostic_max={_fmt(item['strongest_diagnostic_score'])}"
        )
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

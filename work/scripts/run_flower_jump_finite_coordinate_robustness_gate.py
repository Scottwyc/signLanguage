#!/usr/bin/env python3
"""Stress-test flower/jump scoring against NaN/Inf landmark coordinates.

Browser, serialization, or upstream tracker faults can occasionally leave a
visible landmark with a non-finite coordinate. The scorer should treat those
points as missing instead of letting NaN/Inf contaminate normalization, DTW
distances, or score diagnostics. Mild isolated bad points should remain
scoreable; sustained core-hand bad coordinates are diagnostic boundaries.

This script writes mutated cached Holistic JSON fixtures under its output
directory, then reloads them through the normal ``load_sequence`` path. It does
not call /api/score, run Holistic, move the web marker, or restart 5080.
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from run_flower_jump_landmark_noise_robustness_gate import _fmt, _json_default, _load_backend_status
from run_flower_jump_mirror_robustness_gate import _template_json
from score_holistic_sequence_mvp import (
    DEFAULT_SEMANTIC_PROFILE_JSON,
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

RIGHT_DISTAL = [2, 3, 4, 6, 7, 8, 10, 11, 12, 14, 15, 16, 18, 19, 20]
RIGHT_PERSON_DISTAL = [6, 7, 8, 10, 11, 12]
OUTER_TIPS = [16, 20]
POSE_CORE_RAW = [0, 11, 12, 23, 24]
FACE_STABLE_RAW = [33, 133, 61, 291]
LEFT_GROUND_RAW = [0, 5, 9, 13, 17]


def _active_indices(pattern: str, length: int) -> List[int]:
    if length <= 0:
        return []
    if pattern == "none":
        return []
    if pattern == "single_mid":
        return [length // 2]
    if pattern == "first_3":
        return list(range(min(3, length)))
    if pattern == "sparse_every_7f":
        return [idx for idx in range(1, length - 1) if idx % 7 == 3]
    if pattern == "sparse_every_5f":
        return [idx for idx in range(1, length - 1) if idx % 5 == 2]
    if pattern == "middle_20pct":
        start = int(round(length * 0.40))
        end = max(start + 1, int(round(length * 0.60)))
        return list(range(max(1, start), min(length - 1, end)))
    if pattern == "middle_35pct":
        start = int(round(length * 0.325))
        end = max(start + 1, int(round(length * 0.675)))
        return list(range(max(1, start), min(length - 1, end)))
    if pattern == "full":
        return list(range(length))
    raise ValueError(f"unknown finite-coordinate pattern: {pattern}")


def _poison_value(kind: str) -> float:
    if kind == "nan":
        return float("nan")
    if kind == "pos_inf":
        return float("inf")
    if kind == "neg_inf":
        return float("-inf")
    raise ValueError(f"unknown poison value: {kind}")


def _spec(
    variant: str,
    kind: str,
    *,
    pattern: str,
    mutations: Sequence[Dict[str, Any]],
    rationale: str,
    min_score: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": kind,
        "pattern": pattern,
        "mutations": [dict(item) for item in mutations],
        "min_score": min_score,
        "gated": kind == "positive",
        "rationale": rationale,
    }


def _mut(group: str, indices: Sequence[int], axes: Sequence[str], poison: str) -> Dict[str, Any]:
    return {
        "group": group,
        "indices": [int(item) for item in indices],
        "axes": [str(axis) for axis in axes],
        "poison": poison,
    }


def _variant_specs(word: str, min_score: float) -> List[Dict[str, Any]]:
    specs = [
        _spec(
            "self_reloaded",
            "positive",
            pattern="none",
            mutations=[],
            min_score=95.0,
            rationale="原始标准 JSON 经正常 load_sequence 重载，应保持近满分且所有距离有限。",
        ),
        _spec(
            "pose_face_sparse_nan_inf",
            "positive",
            pattern="sparse_every_7f",
            mutations=[
                _mut("pose_landmarks", POSE_CORE_RAW, ["x"], "nan"),
                _mut("face_landmarks", FACE_STABLE_RAW, ["y"], "pos_inf"),
            ],
            min_score=min_score,
            rationale="非核心 pose/face 稀疏坏点应被当作缺失，不应污染手部语义评分。",
        ),
        _spec(
            "pose_shoulder_first3_inf",
            "positive",
            pattern="first_3",
            mutations=[
                _mut("pose_landmarks", [11, 12], ["x", "y"], "pos_inf"),
            ],
            min_score=min_score,
            rationale="起始几帧肩部归一化锚点异常时，应回退到有限 pose 点或默认归一化。",
        ),
    ]
    if word == "花":
        specs.extend(
            [
                _spec(
                    "flower_right_index_tip_single_nan",
                    "positive",
                    pattern="single_mid",
                    mutations=[
                        _mut("right_hand_landmarks", [8], ["x"], "nan"),
                    ],
                    min_score=min_score,
                    rationale="开花核心手单帧 index tip NaN 应被视为该点缺失，完整开合证据仍应保留。",
                ),
                _spec(
                    "flower_right_outer_tips_sparse_inf",
                    "positive",
                    pattern="sparse_every_5f",
                    mutations=[
                        _mut("right_hand_landmarks", OUTER_TIPS, ["x", "z"], "neg_inf"),
                    ],
                    min_score=min_score,
                    rationale="开花 ring/pinky tip 稀疏帧 Inf 坏点应被局部 mask 掉。",
                ),
                _spec(
                    "flower_right_all_distal_middle35_nan_diagnostic",
                    "diagnostic",
                    pattern="middle_35pct",
                    mutations=[
                        _mut("right_hand_landmarks", RIGHT_DISTAL, ["x", "y"], "nan"),
                    ],
                    rationale="诊断记录：开花核心手较长窗口所有 distal finger-chain 坐标坏掉时的边界分。",
                ),
            ]
        )
    elif word == "跳":
        specs.extend(
            [
                _spec(
                    "jump_right_person_tip_single_nan",
                    "positive",
                    pattern="single_mid",
                    mutations=[
                        _mut("right_hand_landmarks", [8, 12], ["x"], "nan"),
                    ],
                    min_score=min_score,
                    rationale="跳的右手两指单帧 tip NaN 应被局部 mask，不应破坏完整弹跳轨迹。",
                ),
                _spec(
                    "jump_left_ground_sparse_inf",
                    "positive",
                    pattern="sparse_every_7f",
                    mutations=[
                        _mut("left_hand_landmarks", LEFT_GROUND_RAW, ["y"], "pos_inf"),
                    ],
                    min_score=min_score,
                    rationale="跳的左手地面手稀疏帧锚点 Inf 应被当作缺失，右手小人和多数关系帧仍可评分。",
                ),
                _spec(
                    "jump_right_person_middle35_nan_diagnostic",
                    "diagnostic",
                    pattern="middle_35pct",
                    mutations=[
                        _mut("right_hand_landmarks", RIGHT_PERSON_DISTAL, ["x", "y"], "nan"),
                    ],
                    rationale="诊断记录：右手两指小人较长窗口 distal 坐标坏掉时的边界分。",
                ),
            ]
        )
    specs.append(
        _spec(
            "all_pose_full_nan_diagnostic",
            "diagnostic",
            pattern="full",
            mutations=[
                _mut("pose_landmarks", list(range(33)), ["x", "y", "z"], "nan"),
            ],
            rationale="诊断记录：全段 pose 归一化信息不可用时，打分应保持有限并依靠手部证据或重采诊断。",
        )
    )
    return specs


def _records(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    if isinstance(payload.get("records"), list):
        return payload["records"]
    if isinstance(payload.get("frames"), list):
        return [{"row": row, "result_data": row.get("result_data") or {}} for row in payload["frames"]]
    raise RuntimeError("finite-coordinate gate requires records or frames with result_data")


def _write_mutated_json(source_json: Path, dest_json: Path, spec: Dict[str, Any]) -> Dict[str, Any]:
    payload = copy.deepcopy(json.loads(source_json.read_text(encoding="utf-8")))
    records = _records(payload)
    active = _active_indices(str(spec["pattern"]), len(records))
    changed_values = 0
    skipped_values = 0
    for frame_idx in active:
        record = records[frame_idx]
        result_data = record.get("result_data") or {}
        for mutation in spec["mutations"]:
            landmarks = result_data.get(str(mutation["group"])) or []
            poison = _poison_value(str(mutation["poison"]))
            for landmark_idx in mutation["indices"]:
                if not 0 <= int(landmark_idx) < len(landmarks):
                    skipped_values += len(mutation["axes"])
                    continue
                point = landmarks[int(landmark_idx)]
                if not isinstance(point, dict):
                    skipped_values += len(mutation["axes"])
                    continue
                for axis in mutation["axes"]:
                    point[str(axis)] = poison
                    changed_values += 1
    dest_json.parent.mkdir(parents=True, exist_ok=True)
    dest_json.write_text(json.dumps(payload, ensure_ascii=False, allow_nan=True), encoding="utf-8")
    return {
        "active_frame_count": len(active),
        "changed_values": changed_values,
        "skipped_values": skipped_values,
        "total_records": len(records),
    }


def _sequence_finite_summary(seq: Any) -> Dict[str, Any]:
    vector_nonfinite = 0
    mask_nonfinite = 0
    vector_values = 0
    mask_values = 0
    zero_mask_values = 0
    for item in seq.features:
        vector_values += int(item.vector.size)
        mask_values += int(item.mask.size)
        vector_nonfinite += int((~np.isfinite(item.vector)).sum())
        mask_nonfinite += int((~np.isfinite(item.mask)).sum())
        zero_mask_values += int((item.mask <= 0).sum())
    return {
        "vector_values": vector_values,
        "mask_values": mask_values,
        "vector_nonfinite": vector_nonfinite,
        "mask_nonfinite": mask_nonfinite,
        "zero_mask_values": zero_mask_values,
    }


def _result_finite(result: Dict[str, Any]) -> bool:
    keys = ["prototype_score", "dtw_distance", "normalized_distance"]
    try:
        return all(math.isfinite(float(result.get(key))) for key in keys)
    except (TypeError, ValueError):
        return False


def _row_passed(row: Dict[str, Any]) -> bool:
    if row.get("exception"):
        return False
    if not row.get("result_finite"):
        return False
    finite_summary = row.get("query_finite_summary") or {}
    if int(finite_summary.get("vector_nonfinite") or 0) != 0:
        return False
    if int(finite_summary.get("mask_nonfinite") or 0) != 0:
        return False
    if row["kind"] == "positive":
        return float(row["score"]) >= float(row["min_score"])
    return True


def _run_word(
    word: str,
    template_root: Path,
    semantic_profile_json: Path,
    feature_mode: str,
    min_score: float,
    fixture_dir: Path,
) -> Dict[str, Any]:
    standard_json = _template_json(template_root, word)
    standard = load_sequence(standard_json, feature_mode, force_bbox=False, apply_sidecar_weights=False)
    profile = load_semantic_profile(word, semantic_profile_json)
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(word, min_score):
        fixture_json = fixture_dir / word / f"{spec['variant']}.json"
        mutation_detail = _write_mutated_json(standard_json, fixture_json, spec)
        row: Dict[str, Any] = {
            "variant": spec["variant"],
            "kind": spec["kind"],
            "gated": bool(spec["gated"]),
            "min_score": spec.get("min_score"),
            "pattern": spec["pattern"],
            "mutations": spec["mutations"],
            "fixture_json": str(fixture_json),
            "rationale": spec["rationale"],
            **mutation_detail,
        }
        try:
            query = load_sequence(fixture_json, feature_mode, force_bbox=False, apply_sidecar_weights=False)
            result = run_pair(standard, query, semantic_profile=profile, target_word=word, enable_cross_check=False)
        except Exception as exc:  # noqa: BLE001 - the gate reports loader/scorer crashes as failures.
            row.update(
                {
                    "exception": f"{type(exc).__name__}: {exc}",
                    "score": None,
                    "dtw_distance": None,
                    "normalized_distance": None,
                    "result_finite": False,
                    "query_finite_summary": {},
                }
            )
        else:
            row.update(
                {
                    "exception": "",
                    "score": float(result["prototype_score"]),
                    "dtw_distance": float(result["dtw_distance"]),
                    "normalized_distance": float(result["normalized_distance"]),
                    "result_finite": _result_finite(result),
                    "query_finite_summary": _sequence_finite_summary(query),
                    "alignment_policy": result.get("alignment_policy"),
                    "capture_quality": (result.get("score_scale") or {}).get("capture_quality"),
                    "semantic_floor": (result.get("score_scale") or {}).get("semantic_floor"),
                    "action_window": result.get("action_window"),
                }
            )
        row["passed"] = _row_passed(row)
        rows.append(row)
    positive_rows = [row for row in rows if row["kind"] == "positive" and row.get("score") is not None]
    diagnostic_rows = [row for row in rows if row["kind"] == "diagnostic" and row.get("score") is not None]
    weakest_positive = min(positive_rows, key=lambda row: float(row["score"])) if positive_rows else None
    weakest_diagnostic = min(diagnostic_rows, key=lambda row: float(row["score"])) if diagnostic_rows else None
    return {
        "word": word,
        "standard_json": str(standard_json),
        "standard_length": len(standard.features),
        "semantic_profile": _profile_summary(profile),
        "gate_pass": all(bool(row["passed"]) for row in rows),
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
        "dtw_distance",
        "normalized_distance",
        "result_finite",
        "vector_nonfinite",
        "mask_nonfinite",
        "zero_mask_values",
        "pattern",
        "active_frame_count",
        "changed_values",
        "skipped_values",
        "total_records",
        "fixture_json",
        "capture_quality_status",
        "capture_quality_reason",
        "semantic_floor_source",
        "semantic_floor_reason",
        "exception",
        "rationale",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in results:
            for row in item["variants"]:
                quality = row.get("capture_quality") or {}
                floor = row.get("semantic_floor") or {}
                finite_summary = row.get("query_finite_summary") or {}
                writer.writerow(
                    {
                        "word": item["word"],
                        "variant": row.get("variant"),
                        "kind": row.get("kind"),
                        "gated": row.get("gated"),
                        "passed": row.get("passed"),
                        "score": row.get("score"),
                        "min_score": row.get("min_score"),
                        "dtw_distance": row.get("dtw_distance"),
                        "normalized_distance": row.get("normalized_distance"),
                        "result_finite": row.get("result_finite"),
                        "vector_nonfinite": finite_summary.get("vector_nonfinite"),
                        "mask_nonfinite": finite_summary.get("mask_nonfinite"),
                        "zero_mask_values": finite_summary.get("zero_mask_values"),
                        "pattern": row.get("pattern"),
                        "active_frame_count": row.get("active_frame_count"),
                        "changed_values": row.get("changed_values"),
                        "skipped_values": row.get("skipped_values"),
                        "total_records": row.get("total_records"),
                        "fixture_json": row.get("fixture_json"),
                        "capture_quality_status": quality.get("status"),
                        "capture_quality_reason": quality.get("reason"),
                        "semantic_floor_source": floor.get("source"),
                        "semantic_floor_reason": floor.get("reason"),
                        "exception": row.get("exception"),
                        "rationale": row.get("rationale"),
                    }
                )


def _build_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# 花/跳非有限坐标清洗鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：写入带 `NaN/Inf` 的临时 Holistic JSON fixture，再经正常 `load_sequence()` 和 `run_pair()` 评分；不调用 `/api/score`，不运行 Holistic，不移动 marker，不重启 5080。",
        "- 目标：孤立或稀疏非有限坐标被视为缺失点，DTW/normalized distance/score 必须保持有限；持续核心手坏点只记录诊断边界。",
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
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向坏点 | 诊断最低分 | 最弱诊断边界 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for item in payload["results"]:
        lines.append(
            f"| {item['word']} | {'PASS' if item['gate_pass'] else 'FAIL'} | "
            f"{_fmt(item['weakest_positive_score'])} | {item['weakest_positive_variant'] or '-'} | "
            f"{_fmt(item['weakest_diagnostic_score'])} | {item['weakest_diagnostic_variant'] or '-'} | "
            f"{_fmt(item['min_required_score'])} |"
        )
    lines.append("")
    lines.append("## 分项明细")
    for item in payload["results"]:
        lines.extend(["", f"### {item['word']}", "", f"- 标准序列：`{item['standard_json']}`", ""])
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | finite | vector/mask 非有限 | 改动值 | pattern | capture_quality | semantic_floor | 异常 | 说明 |")
        lines.append("|---|---|---|---:|---|---|---|---:|---|---|---|---|---|")
        for row in sorted(item["variants"], key=lambda value: (value["kind"], float(value["score"] if value.get("score") is not None else -1.0))):
            quality = row.get("capture_quality") or {}
            floor = row.get("semantic_floor") or {}
            finite_summary = row.get("query_finite_summary") or {}
            if row["kind"] == "positive":
                threshold = f">= {row.get('min_score')}"
                status = "PASS" if row["passed"] else "FAIL"
            else:
                threshold = "diagnostic"
                status = "DIAG" if row["passed"] else "FAIL"
            nonfinite = f"{finite_summary.get('vector_nonfinite', '-')}/{finite_summary.get('mask_nonfinite', '-')}"
            lines.append(
                f"| {row['variant']} | {row['kind']} | {status} | {_fmt(row.get('score'))} | "
                f"{threshold} | {row.get('result_finite')} | {nonfinite} | {row.get('changed_values')} | "
                f"{row.get('pattern')} | {quality.get('status') or '-'}:{quality.get('reason') or '-'} | "
                f"{floor.get('source') or '-'}:{floor.get('reason') or '-'} | {row.get('exception') or '-'} | "
                f"{row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 该门补充的是 JSON 入口和距离计算的数值清洗，不替代 missing/mask、landmark spike、coordinate precision 或 occlusion 门。",
            "- 非有限坐标在本口径中不是“正常动作证据”，只是不能污染全局距离或导致 NaN 诊断；持续核心坏点仍需要重采或人工复核。",
            "- 该门是缓存 JSON fixture 压力测试，不能替代正式 marker 后的真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run finite-coordinate robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_finite_coordinate_robustness_gate_current"))
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
    fixture_dir = output_dir / "fixtures"
    results = [
        _run_word(
            word=word,
            template_root=template_root,
            semantic_profile_json=semantic_profile_json,
            feature_mode=args.feature_mode,
            min_score=args.min_score,
            fixture_dir=fixture_dir,
        )
        for word in args.words
    ]
    backend_status = _load_backend_status(args.backend_url, args.status_timeout_sec)
    passed = all(bool(item["gate_pass"]) for item in results)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "claim_policy": "synthetic finite-coordinate robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": backend_status,
        "passed": passed,
        "min_score": args.min_score,
        "results": results,
    }

    json_path = output_dir / "flower_jump_finite_coordinate_robustness_gate.json"
    md_path = output_dir / "flower_jump_finite_coordinate_robustness_gate.md"
    csv_path = output_dir / "flower_jump_finite_coordinate_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳非有限坐标清洗鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳非有限坐标清洗鲁棒性报告：{md_path}")
    print(f"已生成花/跳非有限坐标清洗鲁棒性 CSV：{csv_path}")
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

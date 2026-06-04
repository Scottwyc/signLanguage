#!/usr/bin/env python3
"""Stress-test flower/jump scoring against malformed temporal metadata.

Browser serialization and upstream preprocessing can leave invalid ``fps``,
``total_frames``, ``frame_idx``, or ``timestamp_sec`` values around otherwise
valid Holistic landmarks. The loader must sanitize those values without
reordering the action, emitting non-finite diagnostics, or failing scoring.

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
from typing import Any, Dict, List, Optional, Sequence

from run_flower_jump_landmark_noise_robustness_gate import _fmt, _json_default, _load_backend_status
from run_flower_jump_mirror_robustness_gate import _template_json
from score_holistic_sequence_mvp import (
    DEFAULT_SEMANTIC_PROFILE_JSON,
    FPS_MAX,
    FPS_MIN,
    TOTAL_FRAMES_MAX,
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


def _records(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    if isinstance(payload.get("records"), list):
        return payload["records"]
    if isinstance(payload.get("frames"), list):
        return payload["frames"]
    if isinstance(payload.get("rows"), list):
        return payload["rows"]
    raise RuntimeError("temporal metadata gate requires records, frames, or rows")


def _set_record_metadata(record: Dict[str, Any], key: str, value: Any) -> None:
    record[key] = value
    row = record.get("row")
    if isinstance(row, dict):
        row[key] = value


def _spec(
    variant: str,
    rationale: str,
    min_score: Optional[float],
    *,
    feature_mode: str = "configured",
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": "positive" if min_score is not None else "compatibility",
        "gated": True,
        "min_score": min_score,
        "score_required": min_score is not None,
        "feature_mode": feature_mode,
        "rationale": rationale,
    }


def _variant_specs(min_score: float) -> List[Dict[str, Any]]:
    return [
        _spec("self_reloaded", "原始标准 JSON 经正常加载后应保持近满分且时间元数据有限。", 95.0),
        _spec("fps_nan_sanitized", "顶层 fps=NaN 时应回退到安全默认帧率。", min_score),
        _spec("fps_string_sanitized", "顶层 fps 为非数值字符串时应回退到安全默认帧率。", min_score),
        _spec("fps_extreme_sanitized", "顶层 fps 为极大离群值时应回退到安全默认帧率。", min_score),
        _spec("total_frames_inf_recovered", "total_frames=Inf 时应从可靠帧索引恢复总帧数。", min_score),
        _spec("total_frames_extreme_recovered", "total_frames 极大离群时应从可靠帧索引恢复总帧数。", min_score),
        _spec("mid_frame_idx_nan_both_fallback", "单帧 record/row frame_idx 均为 NaN 时应保持原有动作顺序。", min_score),
        _spec("mid_frame_idx_negative_both_fallback", "单帧负 frame_idx 不应被排序到动作开头。", min_score),
        _spec("mid_frame_idx_extreme_both_fallback", "单帧极大 frame_idx 不应被排序到动作末尾。", min_score),
        _spec("all_frame_idx_invalid_order_fallback", "整段 frame_idx 不可用时应按总帧数做顺序保持回退。", min_score),
        _spec("all_timestamp_nonfinite_fallback", "整段 timestamp_sec 非有限时应生成有限非负时间戳。", min_score),
        _spec("mixed_timestamp_invalid_fallback", "稀疏负数/字符串/极大/非有限时间戳应逐帧回退。", min_score),
        _spec("combined_temporal_metadata_corruption", "fps、总帧数、帧索引和时间戳同时损坏时仍应正常评分。", min_score),
        _spec(
            "bbox_combined_temporal_metadata_finite",
            "旧 bbox 兼容模式遇到组合时间元数据损坏时应保持有限评分，不强求缺少指尖语义的 bbox 得到高分。",
            None,
            feature_mode="bbox",
        ),
    ]


def _apply_variant(payload: Dict[str, Any], variant: str) -> Dict[str, Any]:
    records = _records(payload)
    changed = 0

    def set_top(key: str, value: Any) -> None:
        nonlocal changed
        payload[key] = value
        changed += 1

    def set_frame(index: int, key: str, value: Any) -> None:
        nonlocal changed
        if not records:
            return
        _set_record_metadata(records[max(0, min(len(records) - 1, index))], key, value)
        changed += 1

    if variant == "self_reloaded":
        pass
    elif variant == "fps_nan_sanitized":
        set_top("fps", float("nan"))
    elif variant == "fps_string_sanitized":
        set_top("fps", "not-a-number")
    elif variant == "fps_extreme_sanitized":
        set_top("fps", 1.0e12)
    elif variant == "total_frames_inf_recovered":
        set_top("total_frames", float("inf"))
    elif variant == "total_frames_extreme_recovered":
        set_top("total_frames", 1.0e12)
    elif variant == "mid_frame_idx_nan_both_fallback":
        set_frame(len(records) // 2, "frame_idx", float("nan"))
    elif variant == "mid_frame_idx_negative_both_fallback":
        set_frame(len(records) // 2, "frame_idx", -7)
    elif variant == "mid_frame_idx_extreme_both_fallback":
        set_frame(len(records) // 2, "frame_idx", 1.0e12)
    elif variant == "all_frame_idx_invalid_order_fallback":
        for record in records:
            _set_record_metadata(record, "frame_idx", float("nan"))
            changed += 1
    elif variant == "all_timestamp_nonfinite_fallback":
        for record in records:
            _set_record_metadata(record, "timestamp_sec", float("inf"))
            changed += 1
    elif variant == "mixed_timestamp_invalid_fallback":
        values = [float("nan"), float("inf"), -5.0, 1.0e12, "not-a-time"]
        for offset, value in enumerate(values):
            set_frame((offset + 1) * len(records) // (len(values) + 1), "timestamp_sec", value)
    elif variant in {"combined_temporal_metadata_corruption", "bbox_combined_temporal_metadata_finite"}:
        set_top("fps", -5.0)
        set_top("total_frames", float("inf"))
        timestamp_values = [float("nan"), -3.0, 1.0e12, "not-a-time"]
        for idx, record in enumerate(records):
            if idx % 5 == 2:
                _set_record_metadata(record, "frame_idx", float("nan"))
                changed += 1
            if idx % 4 == 1:
                _set_record_metadata(record, "timestamp_sec", timestamp_values[idx % len(timestamp_values)])
                changed += 1
    else:
        raise ValueError(f"unknown temporal metadata variant: {variant}")
    return {"changed_metadata_values": changed, "total_records": len(records)}


def _write_fixture(source_json: Path, dest_json: Path, variant: str) -> Dict[str, Any]:
    payload = copy.deepcopy(json.loads(source_json.read_text(encoding="utf-8")))
    detail = _apply_variant(payload, variant)
    dest_json.parent.mkdir(parents=True, exist_ok=True)
    dest_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return detail


def _sequence_temporal_summary(seq: Any) -> Dict[str, Any]:
    frame_indices = [int(feature.frame_idx) for feature in seq.features]
    timestamps = [float(feature.timestamp_sec) for feature in seq.features]
    metadata_valid = bool(
        math.isfinite(float(seq.fps))
        and FPS_MIN <= float(seq.fps) <= FPS_MAX
        and 0 < int(seq.total_frames) <= TOTAL_FRAMES_MAX
        and int(seq.total_frames) >= len(seq.features)
        and all(0 <= value < int(seq.total_frames) for value in frame_indices)
        and all(left <= right for left, right in zip(frame_indices, frame_indices[1:]))
        and all(math.isfinite(value) and value >= 0.0 for value in timestamps)
    )
    return {
        "metadata_valid": metadata_valid,
        "fps": float(seq.fps),
        "total_frames": int(seq.total_frames),
        "feature_count": len(seq.features),
        "frame_idx_min": min(frame_indices) if frame_indices else None,
        "frame_idx_max": max(frame_indices) if frame_indices else None,
        "frame_idx_nonmonotonic": sum(left > right for left, right in zip(frame_indices, frame_indices[1:])),
        "timestamp_min": min(timestamps) if timestamps else None,
        "timestamp_max": max(timestamps) if timestamps else None,
        "timestamp_nonfinite": sum(not math.isfinite(value) for value in timestamps),
        "timestamp_negative": sum(value < 0.0 for value in timestamps if math.isfinite(value)),
    }


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
    bbox_standard = load_sequence(standard_json, "bbox", force_bbox=True, apply_sidecar_weights=False)
    profile = load_semantic_profile(word, semantic_profile_json)
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(min_score):
        fixture_json = fixture_dir / word / spec["variant"] / "query.json"
        mutation_detail = _write_fixture(standard_json, fixture_json, spec["variant"])
        row: Dict[str, Any] = {
            "variant": spec["variant"],
            "kind": spec["kind"],
            "gated": spec["gated"],
            "min_score": spec["min_score"],
            "score_required": spec["score_required"],
            "feature_mode": spec["feature_mode"],
            "rationale": spec["rationale"],
            "fixture_json": str(fixture_json),
            **mutation_detail,
        }
        try:
            use_bbox = spec["feature_mode"] == "bbox"
            active_standard = bbox_standard if use_bbox else standard
            query = load_sequence(
                fixture_json,
                "bbox" if use_bbox else feature_mode,
                force_bbox=use_bbox,
                apply_sidecar_weights=False,
            )
            result = run_pair(active_standard, query, semantic_profile=profile, target_word=word, enable_cross_check=False)
        except Exception as exc:  # noqa: BLE001 - loader/scorer crashes are gate failures.
            row.update(
                {
                    "exception": f"{type(exc).__name__}: {exc}",
                    "score": None,
                    "dtw_distance": None,
                    "normalized_distance": None,
                    "result_finite": False,
                    "temporal_summary": {},
                    "passed": False,
                }
            )
        else:
            temporal_summary = _sequence_temporal_summary(query)
            values = [
                float(result["prototype_score"]),
                float(result["dtw_distance"]),
                float(result["normalized_distance"]),
            ]
            result_finite = all(math.isfinite(value) for value in values)
            row.update(
                {
                    "exception": "",
                    "score": values[0],
                    "dtw_distance": values[1],
                    "normalized_distance": values[2],
                    "result_finite": result_finite,
                    "temporal_summary": temporal_summary,
                    "alignment_policy": result.get("alignment_policy"),
                    "capture_quality": (result.get("score_scale") or {}).get("capture_quality"),
                    "semantic_floor": (result.get("score_scale") or {}).get("semantic_floor"),
                    "passed": bool(
                        result_finite
                        and temporal_summary["metadata_valid"]
                        and (not spec["score_required"] or values[0] >= float(spec["min_score"]))
                    ),
                }
            )
        rows.append(row)
    weakest = min(
        (row for row in rows if row.get("score") is not None and row.get("score_required")),
        key=lambda row: float(row["score"]),
        default=None,
    )
    return {
        "word": word,
        "standard_json": str(standard_json),
        "standard_length": len(standard.features),
        "semantic_profile": _profile_summary(profile),
        "min_required_score": min_score,
        "gate_pass": all(bool(row["passed"]) for row in rows),
        "weakest_positive_score": float(weakest["score"]) if weakest else None,
        "weakest_positive_variant": weakest["variant"] if weakest else "",
        "variants": rows,
    }


def _write_rows_csv(path: Path, results: Sequence[Dict[str, Any]]) -> None:
    fields = [
        "word",
        "variant",
        "feature_mode",
        "passed",
        "score",
        "min_score",
        "dtw_distance",
        "normalized_distance",
        "result_finite",
        "metadata_valid",
        "fps",
        "total_frames",
        "frame_idx_min",
        "frame_idx_max",
        "frame_idx_nonmonotonic",
        "timestamp_nonfinite",
        "timestamp_negative",
        "changed_metadata_values",
        "exception",
        "fixture_json",
        "rationale",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in results:
            for row in item["variants"]:
                summary = row.get("temporal_summary") or {}
                writer.writerow(
                    {
                        "word": item["word"],
                        "variant": row.get("variant"),
                        "feature_mode": row.get("feature_mode"),
                        "passed": row.get("passed"),
                        "score": row.get("score"),
                        "min_score": row.get("min_score"),
                        "dtw_distance": row.get("dtw_distance"),
                        "normalized_distance": row.get("normalized_distance"),
                        "result_finite": row.get("result_finite"),
                        "metadata_valid": summary.get("metadata_valid"),
                        "fps": summary.get("fps"),
                        "total_frames": summary.get("total_frames"),
                        "frame_idx_min": summary.get("frame_idx_min"),
                        "frame_idx_max": summary.get("frame_idx_max"),
                        "frame_idx_nonmonotonic": summary.get("frame_idx_nonmonotonic"),
                        "timestamp_nonfinite": summary.get("timestamp_nonfinite"),
                        "timestamp_negative": summary.get("timestamp_negative"),
                        "changed_metadata_values": row.get("changed_metadata_values"),
                        "exception": row.get("exception"),
                        "fixture_json": row.get("fixture_json"),
                        "rationale": row.get("rationale"),
                    }
                )


def _build_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# 花/跳时间元数据清洗鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只写临时畸形 JSON 并走正常 `load_sequence`；不调用 `/api/score`，不运行 Holistic，不移动 marker，不重启 5080。",
        "- 目标：畸形 `fps/total_frames/frame_idx/timestamp_sec` 被清洗后，不改变动作顺序、不产生非有限诊断，并保持正常得分。",
        "",
        "## 结论",
        "",
        f"- 综合状态：`{'PASS' if payload['passed'] else 'FAIL'}`",
        "",
        "| 目标词 | 状态 | 正向最低分 | 最弱时间元数据变体 | 门槛 |",
        "|---|---|---:|---|---:|",
    ]
    for item in payload["results"]:
        lines.append(
            f"| {item['word']} | {'PASS' if item['gate_pass'] else 'FAIL'} | "
            f"{_fmt(item['weakest_positive_score'])} | {item['weakest_positive_variant']} | "
            f"{_fmt(item['min_required_score'])} |"
        )
    lines.append("")
    lines.append("## 分项明细")
    for item in payload["results"]:
        lines.extend(["", f"### {item['word']}", "", f"- 标准序列：`{item['standard_json']}`", ""])
        lines.append("| 变体 | 模式 | 状态 | 分数 | 阈值 | fps | total_frames | frame_idx 范围 | 时间戳异常 | 输出有限 | 元数据有效 | 说明 |")
        lines.append("|---|---|---|---:|---:|---:|---:|---|---|---|---|---|")
        for row in sorted(item["variants"], key=lambda value: float(value["score"]) if value.get("score") is not None else -1.0):
            summary = row.get("temporal_summary") or {}
            timestamp_anomaly = (
                f"nonfinite={summary.get('timestamp_nonfinite', '-')}, "
                f"negative={summary.get('timestamp_negative', '-')}"
            )
            threshold = _fmt(row.get("min_score")) if row.get("score_required") else "finite-only"
            lines.append(
                f"| {row['variant']} | {row.get('feature_mode') or 'configured'} | "
                f"{'PASS' if row.get('passed') else 'FAIL'} | {_fmt(row.get('score'))} | "
                f"{threshold} | {_fmt(summary.get('fps'))} | {summary.get('total_frames', '-')} | "
                f"{summary.get('frame_idx_min', '-')}-{summary.get('frame_idx_max', '-')} | {timestamp_anomaly} | "
                f"{'yes' if row.get('result_finite') else 'no'} | {'yes' if summary.get('metadata_valid') else 'no'} | "
                f"{row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- `frame_idx` 的安全回退保持记录顺序，并优先使用同帧 record/row 中仍有效的副本。",
            "- 无效 `total_frames` 从可靠帧索引恢复；异常时间戳回退为 `frame_idx/fps`。",
            "- 该门是缓存 JSON 压力测试，不能替代真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run temporal metadata robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_temporal_metadata_robustness_gate_current"))
    parser.add_argument("--words", nargs="+", default=DEFAULT_WORDS)
    parser.add_argument("--feature-mode", choices=["auto", "landmark", "bbox"], default="auto")
    parser.add_argument("--min-score", type=float, default=70.0)
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--status-timeout-sec", type=float, default=3.0)
    args = parser.parse_args(argv)

    template_root = Path(args.template_root)
    semantic_profile_json = Path(args.semantic_profile_json)
    output_dir = Path(args.output_dir)
    fixture_dir = output_dir / "fixtures"
    output_dir.mkdir(parents=True, exist_ok=True)
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
        "claim_policy": "synthetic malformed temporal metadata robustness gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "min_score": args.min_score,
        "backend_status": backend_status,
        "passed": passed,
        "results": results,
    }

    json_path = output_dir / "flower_jump_temporal_metadata_robustness_gate.json"
    md_path = output_dir / "flower_jump_temporal_metadata_robustness_gate.md"
    csv_path = output_dir / "flower_jump_temporal_metadata_robustness_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default, allow_nan=False), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳时间元数据鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳时间元数据鲁棒性报告：{md_path}")
    print(f"已生成花/跳时间元数据鲁棒性 CSV：{csv_path}")
    print(f"综合状态：{'PASS' if passed else 'FAIL'}")
    for item in results:
        print(
            f"- {item['word']}: {'PASS' if item['gate_pass'] else 'FAIL'} "
            f"positive_min={_fmt(item['weakest_positive_score'])} "
            f"weakest={item['weakest_positive_variant']}"
        )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

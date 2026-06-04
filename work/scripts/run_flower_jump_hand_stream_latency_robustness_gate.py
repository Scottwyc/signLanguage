#!/usr/bin/env python3
"""Stress-test flower/jump scoring against hand-stream frame latency.

Browser/Holistic pipelines can report hand landmarks one or two frames behind
the current video frame because of model or worker latency. Existing gates cover
one-hand phase desync, whole-sequence temporal rate changes, frame order jitter,
and tracker interpolation. This gate targets both-hand stream latency: both hand
groups are shifted together relative to pose/face and the current frame index.

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


def _active_indices(pattern: str, length: int) -> List[int]:
    if pattern == "full":
        return list(range(length))
    if pattern == "middle_35pct":
        start = int(round(length * 0.325))
        end = max(start + 1, int(round(length * 0.675)))
        return list(range(max(0, start), min(length, end)))
    if pattern == "sparse_every_5f":
        return [idx for idx in range(length) if idx % 5 == 2]
    raise ValueError(f"unknown latency pattern: {pattern}")


def _shifted_hand_stream_sequence(
    seq: SequenceData,
    name: str,
    *,
    shift_frames: int,
    pattern: str,
    profile: Any,
) -> Tuple[SequenceData, Dict[str, Any]]:
    base = _strip_to_base_groups(seq)
    n = len(base.features)
    active = set(_active_indices(pattern, n))
    features: List[FrameFeature] = []
    changed_hand_frames = 0
    changed_groups = 0

    for idx, frame in enumerate(base.features):
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        presence = dict(frame.presence)
        source_idx = idx
        if idx in active and n > 0:
            source_idx = max(0, min(n - 1, idx - int(shift_frames)))
        for group in HAND_GROUPS:
            source_frame = base.features[source_idx]
            coords, valid = _hand_array(source_frame, group)
            if coords is None or valid is None:
                continue
            if source_idx != idx:
                changed_groups += 1
            _set_hand_group(frame, vector, mask, group, coords.copy(), valid.copy())
            presence[group] = bool(valid.any())
        if source_idx != idx:
            changed_hand_frames += 1
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
        "operation": "hand_stream_latency",
        "shift_frames": int(shift_frames),
        "pattern": pattern,
        "active_frame_count": len(active),
        "changed_hand_frames": changed_hand_frames,
        "changed_hand_groups": changed_groups,
        "total_frames": n,
    }
    return _sequence_with_relative_motion_features(transformed, profile), detail


def _spec(
    variant: str,
    kind: str,
    *,
    shift_frames: int,
    pattern: str,
    rationale: str,
    min_score: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": kind,
        "shift_frames": int(shift_frames),
        "pattern": pattern,
        "min_score": min_score,
        "gated": kind == "positive",
        "rationale": rationale,
    }


def _variant_specs(word: str, min_score: float) -> List[Dict[str, Any]]:
    word_note = "开花手部流" if word == "花" else "跳跃双手流"
    return [
        _spec(
            "self_recomputed",
            "positive",
            shift_frames=0,
            pattern="full",
            min_score=95.0,
            rationale="标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。",
        ),
        _spec(
            "both_hands_delay_1f",
            "positive",
            shift_frames=1,
            pattern="full",
            min_score=min_score,
            rationale=f"{word_note}整体滞后 1 帧，模拟模型/worker 手部流轻微延迟。",
        ),
        _spec(
            "both_hands_advance_1f",
            "positive",
            shift_frames=-1,
            pattern="full",
            min_score=min_score,
            rationale=f"{word_note}整体提前 1 帧，模拟帧切片和结果对齐轻微偏移。",
        ),
        _spec(
            "both_hands_delay_2f",
            "positive",
            shift_frames=2,
            pattern="full",
            min_score=min_score,
            rationale=f"{word_note}整体滞后 2 帧，验证语义 DTW 对小型检测延迟的吸收。",
        ),
        _spec(
            "both_hands_advance_2f",
            "positive",
            shift_frames=-2,
            pattern="full",
            min_score=min_score,
            rationale=f"{word_note}整体提前 2 帧，仍应保留完整动作可评分性。",
        ),
        _spec(
            "middle35_both_hands_delay_2f",
            "positive",
            shift_frames=2,
            pattern="middle_35pct",
            min_score=min_score,
            rationale=f"{word_note}中段约 35% 出现 2 帧手部流滞后，模拟核心段短暂处理延迟。",
        ),
        _spec(
            "sparse_both_hands_delay_2f_every_5f",
            "positive",
            shift_frames=2,
            pattern="sparse_every_5f",
            min_score=min_score,
            rationale="每 5 帧一次 2 帧手部流滞后，模拟偶发结果对齐抖动。",
        ),
        _spec(
            "both_hands_delay_4f_diagnostic",
            "diagnostic",
            shift_frames=4,
            pattern="full",
            rationale="全程 4 帧手部流滞后已接近明显对齐错误，只记录诊断边界。",
        ),
        _spec(
            "both_hands_advance_4f_diagnostic",
            "diagnostic",
            shift_frames=-4,
            pattern="full",
            rationale="全程 4 帧提前属于明显结果对齐错误，只记录诊断边界。",
        ),
        _spec(
            "middle35_both_hands_delay_5f_diagnostic",
            "diagnostic",
            shift_frames=5,
            pattern="middle_35pct",
            rationale="核心中段 5 帧延迟可能破坏真实相位证据，只记录诊断分数。",
        ),
    ]


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
    standard, standard_detail = _shifted_hand_stream_sequence(
        loaded_standard,
        "standard_base",
        shift_frames=0,
        pattern="full",
        profile=profile,
    )
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(word, min_score):
        query, detail = _shifted_hand_stream_sequence(
            loaded_standard,
            str(spec["variant"]),
            shift_frames=int(spec["shift_frames"]),
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
        "shift_frames",
        "pattern",
        "active_frame_count",
        "changed_hand_frames",
        "changed_hand_groups",
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
                        "shift_frames": row.get("shift_frames"),
                        "pattern": row.get("pattern"),
                        "active_frame_count": row.get("active_frame_count"),
                        "changed_hand_frames": row.get("changed_hand_frames"),
                        "changed_hand_groups": row.get("changed_hand_groups"),
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
        "# 花/跳手部流帧级延迟鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，将双手坐标整体滞后/提前 1-2 帧或局部短暂滞后，然后重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：轻微模型/worker 手部流延迟仍可正常评分；4-5 帧明显对齐错误只记录诊断边界。",
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
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向手部流延迟 | 诊断最低分 | 最弱诊断边界 | 门槛 |")
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
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | shift | pattern | 改动帧 | 改动组 | capture_quality | semantic_floor | 说明 |")
        lines.append("|---|---|---|---:|---|---:|---|---:|---:|---|---|---|")
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
                f"{threshold} | {row.get('shift_frames')} | {row.get('pattern')} | "
                f"{row.get('changed_hand_frames')} | {row.get('changed_hand_groups')} | "
                f"{quality.get('status') or '-'}:{quality.get('reason') or '-'} | "
                f"{floor.get('source') or '-'}:{floor.get('reason') or '-'} | {row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 该门补充的是手部结果流相对当前帧的轻微延迟/提前，不替代 inter-hand temporal desync、temporal-rate、temporal-order-jitter、stutter 或 interpolation 门。",
            "- 正向变体保持双手同时偏移，避免把左右手相位差和单手语义变化混入本门；强延迟只观察诊断边界。",
            "- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run hand-stream-latency robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_hand_stream_latency_robustness_gate_current"))
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
        "claim_policy": "synthetic hand-stream-latency robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": backend_status,
        "passed": passed,
        "min_score": args.min_score,
        "results": results,
    }

    json_path = output_dir / "flower_jump_hand_stream_latency_robustness_gate.json"
    md_path = output_dir / "flower_jump_hand_stream_latency_robustness_gate.md"
    csv_path = output_dir / "flower_jump_hand_stream_latency_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳手部流延迟鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳手部流延迟鲁棒性报告：{md_path}")
    print(f"已生成花/跳手部流延迟鲁棒性 CSV：{csv_path}")
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

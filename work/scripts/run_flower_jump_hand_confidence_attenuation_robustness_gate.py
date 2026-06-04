#!/usr/bin/env python3
"""Stress-test flower/jump scoring against soft hand confidence attenuation.

Binary missing-mask and occlusion gates cover hard landmark loss. Browser
Holistic output can also keep hand coordinates while landmark confidence drops.
This gate preserves coordinates, attenuates hand/hand-shape masks in selected
frames, then rebuilds motion and two-hand relation features from cached
skeleton sequences.

It does not call /api/score, run Holistic, move the marker, or restart 5080.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

from run_flower_jump_mirror_robustness_gate import _strip_to_base_groups
from run_flower_jump_temporal_rate_robustness_gate import (
    _fmt,
    _json_default,
    _load_backend_status,
    _rebuild_derived_groups,
    _template_json,
)
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

QueryFactory = Callable[[SequenceData, Any], SequenceData]


def _core_bounds(word: str) -> Tuple[float, float]:
    if word == "花":
        return 0.34, 0.78
    return 0.22, 0.76


def _frame_indices(seq: SequenceData, start_ratio: float, end_ratio: float, *, step: int = 1) -> List[int]:
    n = len(seq.features)
    if n <= 0:
        return []
    start = max(0, min(n - 1, int(round((n - 1) * float(start_ratio)))))
    end = max(start, min(n - 1, int(round((n - 1) * float(end_ratio)))))
    return list(range(start, end + 1, max(1, int(step))))


def _presence_from_mask(frame: FrameFeature) -> Dict[str, bool]:
    presence = dict(frame.presence)
    for group in ["pose", "left_hand", "right_hand", "face"]:
        if group not in frame.groups:
            presence[group] = False
            continue
        sl = frame.groups[group]
        presence[group] = bool(float(frame.mask[sl].mean()) >= 0.35)
    return presence


def _scale_group_mask(mask: np.ndarray, frame: FrameFeature, group: str, scale: float) -> None:
    if group not in frame.groups:
        return
    sl = frame.groups[group]
    mask[sl] = np.clip(mask[sl] * float(scale), 0.0, 1.0).astype(np.float32)
    shape_group = f"{group}_shape"
    if shape_group in frame.groups:
        shape_sl = frame.groups[shape_group]
        mask[shape_sl] = np.clip(mask[shape_sl] * float(scale), 0.0, 1.0).astype(np.float32)


def _attenuate_confidence(
    seq: SequenceData,
    profile: Any,
    name: str,
    *,
    groups: Sequence[str],
    scale: float,
    start_ratio: float = 0.0,
    end_ratio: float = 1.0,
    step: int = 1,
) -> SequenceData:
    base = _strip_to_base_groups(seq)
    selected = set(_frame_indices(base, start_ratio, end_ratio, step=step))
    items: List[FrameFeature] = []
    for idx, frame in enumerate(base.features):
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        if idx in selected:
            for group in groups:
                _scale_group_mask(mask, frame, group, scale)
        item = _clone_frame(frame, vector=vector, mask=mask)
        item.presence = _presence_from_mask(item)
        items.append(item)
    attenuated = _clone_sequence(base, name, items)
    return _rebuild_derived_groups(attenuated, profile)


def _spec(
    variant: str,
    kind: str,
    query: QueryFactory,
    rationale: str,
    *,
    min_score: Optional[float] = None,
    groups: Optional[Sequence[str]] = None,
    scale: Optional[float] = None,
    frame_span: str = "",
    step: int = 1,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": kind,
        "query": query,
        "min_score": min_score,
        "gated": kind == "positive",
        "groups": list(groups or []),
        "scale": scale,
        "frame_span": frame_span,
        "step": step,
        "rationale": rationale,
    }


def _variant_specs(word: str, min_score: float) -> List[Dict[str, Any]]:
    core_start, core_end = _core_bounds(word)
    if word == "花":
        core_groups = ["right_hand"]
        all_groups = ["left_hand", "right_hand"]
        specs = [
            _spec(
                "self_recomputed",
                "positive",
                lambda seq, profile: _attenuate_confidence(
                    seq, profile, "self_recomputed", groups=[], scale=1.0
                ),
                "标准序列剥离派生组后重建，应保持近满分。",
                min_score=95.0,
                scale=1.0,
                frame_span="all",
            ),
            _spec(
                "flower_all_hands_confidence_0.85",
                "positive",
                lambda seq, profile: _attenuate_confidence(
                    seq, profile, "flower_all_hands_confidence_0.85", groups=all_groups, scale=0.85
                ),
                "全程双手 landmark 置信度轻度下降，但坐标仍可用。",
                min_score=min_score,
                groups=all_groups,
                scale=0.85,
                frame_span="all",
            ),
            _spec(
                "flower_bloom_core_right_confidence_0.65",
                "positive",
                lambda seq, profile: _attenuate_confidence(
                    seq,
                    profile,
                    "flower_bloom_core_right_confidence_0.65",
                    groups=core_groups,
                    scale=0.65,
                    start_ratio=core_start,
                    end_ratio=core_end,
                ),
                "开花手核心段置信度下降到仍高于形状/关系有效阈值。",
                min_score=min_score,
                groups=core_groups,
                scale=0.65,
                frame_span=f"{core_start:.2f}-{core_end:.2f}",
            ),
            _spec(
                "flower_bloom_core_sparse_confidence_0.55",
                "positive",
                lambda seq, profile: _attenuate_confidence(
                    seq,
                    profile,
                    "flower_bloom_core_sparse_confidence_0.55",
                    groups=core_groups,
                    scale=0.55,
                    start_ratio=core_start,
                    end_ratio=core_end,
                    step=2,
                ),
                "开花核心段隔帧低置信，仍应通过时序冗余正常评分。",
                min_score=min_score,
                groups=core_groups,
                scale=0.55,
                frame_span=f"{core_start:.2f}-{core_end:.2f}/step2",
                step=2,
            ),
            _spec(
                "flower_noncore_left_confidence_0.52",
                "positive",
                lambda seq, profile: _attenuate_confidence(
                    seq, profile, "flower_noncore_left_confidence_0.52", groups=["left_hand"], scale=0.52
                ),
                "非核心左手接近有效阈值的低置信不应拖垮右手绽放语义。",
                min_score=min_score,
                groups=["left_hand"],
                scale=0.52,
                frame_span="all",
            ),
            _spec(
                "flower_bloom_core_right_confidence_0.51_diagnostic",
                "diagnostic",
                lambda seq, profile: _attenuate_confidence(
                    seq,
                    profile,
                    "flower_bloom_core_right_confidence_0.51_diagnostic",
                    groups=core_groups,
                    scale=0.51,
                    start_ratio=core_start,
                    end_ratio=core_end,
                ),
                "核心开花手置信度贴近有效阈值，作为 near-threshold 边界诊断。",
                groups=core_groups,
                scale=0.51,
                frame_span=f"{core_start:.2f}-{core_end:.2f}",
            ),
            _spec(
                "flower_all_hands_effective_missing_diagnostic",
                "diagnostic",
                lambda seq, profile: _attenuate_confidence(
                    seq, profile, "flower_all_hands_effective_missing_diagnostic", groups=all_groups, scale=0.0
                ),
                "低于有效阈值的极端情况按有效缺失记录，不作为软置信正向门。",
                groups=all_groups,
                scale=0.0,
                frame_span="all",
            ),
        ]
        return specs

    core_groups = ["left_hand", "right_hand"]
    return [
        _spec(
            "self_recomputed",
            "positive",
            lambda seq, profile: _attenuate_confidence(seq, profile, "self_recomputed", groups=[], scale=1.0),
            "标准序列剥离派生组后重建，应保持近满分。",
            min_score=95.0,
            scale=1.0,
            frame_span="all",
        ),
        _spec(
            "jump_all_hands_confidence_0.85",
            "positive",
            lambda seq, profile: _attenuate_confidence(
                seq, profile, "jump_all_hands_confidence_0.85", groups=core_groups, scale=0.85
            ),
            "双手全程轻度低置信，地面手/小人手关系仍完整。",
            min_score=min_score,
            groups=core_groups,
            scale=0.85,
            frame_span="all",
        ),
        _spec(
            "jump_relation_core_both_confidence_0.65",
            "positive",
            lambda seq, profile: _attenuate_confidence(
                seq,
                profile,
                "jump_relation_core_both_confidence_0.65",
                groups=core_groups,
                scale=0.65,
                start_ratio=core_start,
                end_ratio=core_end,
            ),
            "起跳/双手关系核心段双手低置信，但仍高于关系特征有效阈值。",
            min_score=min_score,
            groups=core_groups,
            scale=0.65,
            frame_span=f"{core_start:.2f}-{core_end:.2f}",
        ),
        _spec(
            "jump_relation_core_sparse_confidence_0.55",
            "positive",
            lambda seq, profile: _attenuate_confidence(
                seq,
                profile,
                "jump_relation_core_sparse_confidence_0.55",
                groups=core_groups,
                scale=0.55,
                start_ratio=core_start,
                end_ratio=core_end,
                step=2,
            ),
            "起跳核心隔帧低置信，仍应保留双手关系方向。",
            min_score=min_score,
            groups=core_groups,
            scale=0.55,
            frame_span=f"{core_start:.2f}-{core_end:.2f}/step2",
            step=2,
        ),
        _spec(
            "jump_right_person_hand_confidence_0.60",
            "positive",
            lambda seq, profile: _attenuate_confidence(
                seq,
                profile,
                "jump_right_person_hand_confidence_0.60",
                groups=["right_hand"],
                scale=0.60,
                start_ratio=core_start,
                end_ratio=core_end,
            ),
            "右手两指小人核心段轻中度低置信，仍应可评分。",
            min_score=min_score,
            groups=["right_hand"],
            scale=0.60,
            frame_span=f"{core_start:.2f}-{core_end:.2f}",
        ),
        _spec(
            "jump_relation_core_both_confidence_0.51_diagnostic",
            "diagnostic",
            lambda seq, profile: _attenuate_confidence(
                seq,
                profile,
                "jump_relation_core_both_confidence_0.51_diagnostic",
                groups=core_groups,
                scale=0.51,
                start_ratio=core_start,
                end_ratio=core_end,
            ),
            "双手关系核心置信度贴近有效阈值，作为 near-threshold 边界诊断。",
            groups=core_groups,
            scale=0.51,
            frame_span=f"{core_start:.2f}-{core_end:.2f}",
        ),
        _spec(
            "jump_all_hands_effective_missing_diagnostic",
            "diagnostic",
            lambda seq, profile: _attenuate_confidence(
                seq, profile, "jump_all_hands_effective_missing_diagnostic", groups=core_groups, scale=0.0
            ),
            "低于有效阈值的极端情况按有效缺失记录，不作为软置信正向门。",
            groups=core_groups,
            scale=0.0,
            frame_span="all",
        ),
    ]


def _presence_ratio(seq: SequenceData) -> Dict[str, float]:
    if not seq.features:
        return {"pose": 0.0, "left_hand": 0.0, "right_hand": 0.0, "face": 0.0}
    return {
        group: sum(1 for item in seq.features if item.presence.get(group)) / len(seq.features)
        for group in ["pose", "left_hand", "right_hand", "face"]
    }


def _mean_group_mask(seq: SequenceData, group: str) -> Optional[float]:
    values: List[float] = []
    for item in seq.features:
        if group not in item.groups:
            continue
        sl = item.groups[group]
        values.append(float(item.mask[sl].mean()))
    if not values:
        return None
    return float(np.mean(values))


def _run_word(
    word: str,
    template_root: Path,
    semantic_profile_json: Path,
    feature_mode: str,
    min_score: float,
) -> Dict[str, Any]:
    standard_json = _template_json(template_root, word)
    standard = load_sequence(standard_json, feature_mode, force_bbox=False)
    profile = load_semantic_profile(word, semantic_profile_json)
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(word, min_score):
        query = spec["query"](standard, profile)
        result = run_pair(standard, query, semantic_profile=profile, target_word=word, enable_cross_check=False)
        score_scale = result.get("score_scale") or {}
        row = {
            "variant": spec["variant"],
            "kind": spec["kind"],
            "gated": bool(spec["gated"]),
            "min_score": spec.get("min_score"),
            "groups": spec.get("groups") or [],
            "scale": spec.get("scale"),
            "frame_span": spec.get("frame_span"),
            "step": spec.get("step"),
            "rationale": spec["rationale"],
            "score": float(result["prototype_score"]),
            "dtw_distance": float(result["dtw_distance"]),
            "normalized_distance": float(result["normalized_distance"]),
            "query_presence": _presence_ratio(query),
            "mean_left_hand_mask": _mean_group_mask(query, "left_hand"),
            "mean_right_hand_mask": _mean_group_mask(query, "right_hand"),
            "mean_left_shape_mask": _mean_group_mask(query, "left_hand_shape"),
            "mean_right_shape_mask": _mean_group_mask(query, "right_hand_shape"),
            "alignment_policy": result.get("alignment_policy"),
            "capture_quality": score_scale.get("capture_quality"),
            "semantic_floor": score_scale.get("semantic_floor"),
            "semantic_phase_order_guard": score_scale.get("semantic_phase_order_guard"),
            "action_window": result.get("action_window"),
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
        "standard_presence": _presence_ratio(standard),
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
        "groups",
        "scale",
        "frame_span",
        "step",
        "left_hand_presence",
        "right_hand_presence",
        "mean_left_hand_mask",
        "mean_right_hand_mask",
        "mean_left_shape_mask",
        "mean_right_shape_mask",
        "alignment_mode",
        "capture_quality_status",
        "capture_quality_reason",
        "semantic_floor_source",
        "semantic_floor_reason",
        "phase_order_blocked",
        "phase_order_reason",
        "rationale",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in results:
            for row in item["variants"]:
                quality = row.get("capture_quality") or {}
                floor = row.get("semantic_floor") or {}
                phase_order = row.get("semantic_phase_order_guard") or {}
                policy = row.get("alignment_policy") or {}
                presence = row.get("query_presence") or {}
                writer.writerow(
                    {
                        "word": item["word"],
                        "variant": row.get("variant"),
                        "kind": row.get("kind"),
                        "gated": row.get("gated"),
                        "passed": row.get("passed"),
                        "score": row.get("score"),
                        "min_score": row.get("min_score"),
                        "groups": "+".join(row.get("groups") or []),
                        "scale": row.get("scale"),
                        "frame_span": row.get("frame_span"),
                        "step": row.get("step"),
                        "left_hand_presence": presence.get("left_hand"),
                        "right_hand_presence": presence.get("right_hand"),
                        "mean_left_hand_mask": row.get("mean_left_hand_mask"),
                        "mean_right_hand_mask": row.get("mean_right_hand_mask"),
                        "mean_left_shape_mask": row.get("mean_left_shape_mask"),
                        "mean_right_shape_mask": row.get("mean_right_shape_mask"),
                        "alignment_mode": policy.get("mode"),
                        "capture_quality_status": quality.get("status"),
                        "capture_quality_reason": quality.get("reason"),
                        "semantic_floor_source": floor.get("source"),
                        "semantic_floor_reason": floor.get("reason"),
                        "phase_order_blocked": phase_order.get("blocked"),
                        "phase_order_reason": phase_order.get("reason"),
                        "rationale": row.get("rationale"),
                    }
                )


def _build_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# 花/跳手部置信度衰减鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，保留手部坐标，只降低手部/手形 mask 权重并重建 motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：覆盖网页摄像头中手部可见但置信度偏低的软 mask 场景；严重低置信只作为诊断边界。",
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
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向低置信 | 诊断最低分 | 最弱诊断边界 | 门槛 |")
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
        lines.append(
            "| 变体 | 类型 | 状态 | 分数 | 阈值 | 组 | scale | 帧范围 | L/R presence | L/R mask | capture_quality | reason | 说明 |"
        )
        lines.append("|---|---|---|---:|---|---|---:|---|---|---|---|---|---|")
        for row in sorted(item["variants"], key=lambda value: (value["kind"], float(value["score"]))):
            quality = row.get("capture_quality") or {}
            floor = row.get("semantic_floor") or {}
            phase_order = row.get("semantic_phase_order_guard") or {}
            threshold = f">= {row.get('min_score')}" if row["kind"] == "positive" else "diagnostic"
            status = "PASS" if row["passed"] else "FAIL"
            if row["kind"] == "diagnostic":
                status = "DIAG"
            reason = quality.get("reason") or phase_order.get("reason") or floor.get("reason") or "-"
            presence = row.get("query_presence") or {}
            lr_presence = f"{_fmt(presence.get('left_hand'))}/{_fmt(presence.get('right_hand'))}"
            lr_mask = f"{_fmt(row.get('mean_left_hand_mask'))}/{_fmt(row.get('mean_right_hand_mask'))}"
            lines.append(
                f"| {row['variant']} | {row['kind']} | {status} | {_fmt(row['score'])} | {threshold} | "
                f"{'+'.join(row.get('groups') or []) or '-'} | {_fmt(row.get('scale'))} | {row.get('frame_span') or '-'} | "
                f"{lr_presence} | {lr_mask} | {quality.get('status') or '-'} | {reason} | {row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 该门不同于 missing/mask、fingertip occlusion、dropout burst：它保留坐标，只下调 mask 置信权重。",
            "- 正向变体只覆盖 mild/near-threshold 低置信，严重核心低置信应进入重采或语义失败诊断。",
            "- 该门是合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run hand-confidence attenuation robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_hand_confidence_attenuation_robustness_gate_current"))
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
        "claim_policy": "synthetic hand-confidence attenuation sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": backend_status,
        "passed": passed,
        "min_score": args.min_score,
        "results": results,
    }

    json_path = output_dir / "flower_jump_hand_confidence_attenuation_robustness_gate.json"
    md_path = output_dir / "flower_jump_hand_confidence_attenuation_robustness_gate.md"
    csv_path = output_dir / "flower_jump_hand_confidence_attenuation_robustness_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳手部置信度衰减鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳手部置信度衰减鲁棒性报告：{md_path}")
    print(f"已生成花/跳手部置信度衰减鲁棒性 CSV：{csv_path}")
    print(f"综合状态：{'PASS' if passed else 'FAIL'}")
    for item in results:
        print(
            f"- {item['word']}: {'PASS' if item['gate_pass'] else 'FAIL'} "
            f"positive_min={_fmt(item['weakest_positive_score'])} "
            f"diagnostic_min={_fmt(item['weakest_diagnostic_score'])}"
        )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

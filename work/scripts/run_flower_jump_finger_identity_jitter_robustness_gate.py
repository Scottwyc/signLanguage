#!/usr/bin/env python3
"""Stress-test flower/jump scoring against finger landmark identity jitter.

MediaPipe Holistic can occasionally confuse neighboring finger chains when the
hand is small, blurred, or partly self-occluded. This is distinct from generic
coordinate noise: the coordinates remain plausible, but labels such as
index/middle or middle/ring are locally swapped. The scorer should tolerate
adjacent-chain swaps that preserve the intended hand shape, while stronger
non-adjacent or multi-chain swaps are recorded as diagnostic boundaries.

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

FINGER_CHAINS = {
    "thumb": [1, 2, 3, 4],
    "index": [5, 6, 7, 8],
    "middle": [9, 10, 11, 12],
    "ring": [13, 14, 15, 16],
    "pinky": [17, 18, 19, 20],
}


def _pattern_applies(pattern: str, idx: int, length: int) -> bool:
    if pattern == "all":
        return True
    if pattern == "single_mid":
        return idx == length // 2
    if pattern == "sparse_every_6th":
        return idx > 1 and idx < length - 2 and idx % 6 == 2
    if pattern == "middle_25pct":
        return int(length * 0.375) <= idx < int(length * 0.625)
    raise ValueError(f"unknown finger jitter pattern: {pattern}")


def _swap_finger_chains(
    coords: np.ndarray,
    valid: np.ndarray,
    pairs: Sequence[Tuple[str, str]],
) -> Tuple[np.ndarray, np.ndarray, int]:
    out = coords.copy()
    out_valid = valid.copy()
    changed_visible = 0
    for left_name, right_name in pairs:
        left_chain = FINGER_CHAINS[left_name]
        right_chain = FINGER_CHAINS[right_name]
        for left_idx, right_idx in zip(left_chain, right_chain):
            if left_idx >= len(out_valid) or right_idx >= len(out_valid):
                continue
            if bool(out_valid[left_idx]) or bool(out_valid[right_idx]):
                changed_visible += int(bool(out_valid[left_idx])) + int(bool(out_valid[right_idx]))
            out[[left_idx, right_idx]] = out[[right_idx, left_idx]]
            out_valid[[left_idx, right_idx]] = out_valid[[right_idx, left_idx]]
    return out, out_valid, changed_visible


def _mutated_sequence(
    seq: SequenceData,
    name: str,
    *,
    group: str,
    pairs: Sequence[Tuple[str, str]],
    pattern: str,
    profile: Any,
) -> Tuple[SequenceData, Dict[str, Any]]:
    base = _strip_to_base_groups(seq)
    items: List[FrameFeature] = []
    changed_frames = 0
    changed_visible_points = 0
    total_frames = len(base.features)
    for idx, frame in enumerate(base.features):
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        presence = dict(frame.presence)
        if _pattern_applies(pattern, idx, total_frames):
            coords, valid = _hand_array(frame, group)
            if coords is not None and valid is not None and valid.any():
                coords, valid, changed = _swap_finger_chains(coords, valid, pairs)
                _set_hand_group(frame, vector, mask, group, coords, valid)
                presence[group] = bool(valid.any())
                changed_frames += 1
                changed_visible_points += changed
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
        "operation": "finger_identity_jitter",
        "group": group,
        "pairs": [list(pair) for pair in pairs],
        "pattern": pattern,
        "changed_frames": changed_frames,
        "changed_visible_points": changed_visible_points,
        "total_frames": total_frames,
    }
    return _sequence_with_relative_motion_features(transformed, profile), detail


def _spec(
    variant: str,
    kind: str,
    *,
    group: str,
    pairs: Sequence[Tuple[str, str]],
    pattern: str,
    rationale: str,
    min_score: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": kind,
        "group": group,
        "pairs": [tuple(pair) for pair in pairs],
        "pattern": pattern,
        "min_score": min_score,
        "gated": kind == "positive",
        "rationale": rationale,
    }


def _variant_specs(word: str, min_score: float) -> List[Dict[str, Any]]:
    specs = [
        _spec(
            "self_recomputed",
            "positive",
            group="right_hand",
            pairs=[],
            pattern="all",
            min_score=95.0,
            rationale="标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。",
        )
    ]
    if word == "花":
        return specs + [
            _spec(
                "right_index_middle_chain_swap",
                "positive",
                group="right_hand",
                pairs=[("index", "middle")],
                pattern="all",
                min_score=min_score,
                rationale="开花核心手 index/middle 相邻指链全程交换，模拟手小或重叠时的相邻手指身份混淆。",
            ),
            _spec(
                "right_middle_ring_chain_swap",
                "positive",
                group="right_hand",
                pairs=[("middle", "ring")],
                pattern="all",
                min_score=min_score,
                rationale="开花核心手 middle/ring 相邻指链全程交换，整体绽放手形仍应可评分。",
            ),
            _spec(
                "right_ring_pinky_chain_swap",
                "positive",
                group="right_hand",
                pairs=[("ring", "pinky")],
                pattern="all",
                min_score=min_score,
                rationale="开花核心手 ring/pinky 相邻指链交换，覆盖外侧手指标签混淆。",
            ),
            _spec(
                "right_index_middle_sparse_jitter",
                "positive",
                group="right_hand",
                pairs=[("index", "middle")],
                pattern="sparse_every_6th",
                min_score=min_score,
                rationale="少量帧 index/middle 指链身份抖动，属于可容忍的 detector 局部不稳定。",
            ),
            _spec(
                "right_middle_ring_sparse_jitter",
                "positive",
                group="right_hand",
                pairs=[("middle", "ring")],
                pattern="sparse_every_6th",
                min_score=min_score,
                rationale="少量帧 middle/ring 指链身份抖动，绽放动态仍应保留。",
            ),
            _spec(
                "right_index_middle_middle_25pct",
                "positive",
                group="right_hand",
                pairs=[("index", "middle")],
                pattern="middle_25pct",
                min_score=min_score,
                rationale="核心中段 25% index/middle 身份抖动，验证手形/DTW 对短时拓扑标签抖动的吸收。",
            ),
            _spec(
                "right_adjacent_wave_diagnostic",
                "diagnostic",
                group="right_hand",
                pairs=[("index", "middle"), ("ring", "pinky")],
                pattern="all",
                rationale="两组相邻指链全程交换属于强边界，仅记录诊断分数。",
            ),
            _spec(
                "right_index_ring_diagnostic",
                "diagnostic",
                group="right_hand",
                pairs=[("index", "ring")],
                pattern="all",
                rationale="非相邻 index/ring 指链交换不是正常轻微混淆，仅记录边界。",
            ),
            _spec(
                "right_thumb_index_diagnostic",
                "diagnostic",
                group="right_hand",
                pairs=[("thumb", "index")],
                pattern="all",
                rationale="thumb/index 交换会改变手形拓扑，仅记录诊断边界。",
            ),
        ]
    if word == "跳":
        return specs + [
            _spec(
                "right_index_middle_chain_swap",
                "positive",
                group="right_hand",
                pairs=[("index", "middle")],
                pattern="all",
                min_score=min_score,
                rationale="右手两指小人的 index/middle 互换不应破坏两指语义。",
            ),
            _spec(
                "right_middle_ring_chain_swap",
                "positive",
                group="right_hand",
                pairs=[("middle", "ring")],
                pattern="all",
                min_score=min_score,
                rationale="右手 middle/ring 相邻指链混淆仍应保留跳跃主关系。",
            ),
            _spec(
                "right_ring_pinky_chain_swap",
                "positive",
                group="right_hand",
                pairs=[("ring", "pinky")],
                pattern="all",
                min_score=min_score,
                rationale="右手非核心外侧相邻指链混淆应保持高分。",
            ),
            _spec(
                "right_index_middle_sparse_jitter",
                "positive",
                group="right_hand",
                pairs=[("index", "middle")],
                pattern="sparse_every_6th",
                min_score=min_score,
                rationale="短序列中少量帧 index/middle 身份抖动，仍应保留可评分跳跃证据。",
            ),
            _spec(
                "right_middle_ring_sparse_jitter",
                "positive",
                group="right_hand",
                pairs=[("middle", "ring")],
                pattern="sparse_every_6th",
                min_score=min_score,
                rationale="短序列中少量帧 middle/ring 身份抖动，作为 `跳` 的弱边界正向门。",
            ),
            _spec(
                "right_index_middle_middle_25pct",
                "positive",
                group="right_hand",
                pairs=[("index", "middle")],
                pattern="middle_25pct",
                min_score=min_score,
                rationale="核心中段 25% index/middle 身份抖动，local relation fallback 仍应可恢复。",
            ),
            _spec(
                "left_index_middle_chain_swap",
                "positive",
                group="left_hand",
                pairs=[("index", "middle")],
                pattern="all",
                min_score=min_score,
                rationale="左手地面手形的 index/middle 标签互换不应破坏地面支撑语义。",
            ),
            _spec(
                "left_middle_ring_sparse_jitter",
                "positive",
                group="left_hand",
                pairs=[("middle", "ring")],
                pattern="sparse_every_6th",
                min_score=min_score,
                rationale="左手地面少量帧 middle/ring 身份抖动仍应保持高分。",
            ),
            _spec(
                "right_adjacent_wave_diagnostic",
                "diagnostic",
                group="right_hand",
                pairs=[("index", "middle"), ("ring", "pinky")],
                pattern="all",
                rationale="两组相邻指链全程交换属于强边界，仅记录诊断分数。",
            ),
            _spec(
                "right_index_ring_diagnostic",
                "diagnostic",
                group="right_hand",
                pairs=[("index", "ring")],
                pattern="all",
                rationale="右手 index/ring 非相邻交换会改变两指小人拓扑，仅记录诊断边界。",
            ),
            _spec(
                "right_thumb_index_diagnostic",
                "diagnostic",
                group="right_hand",
                pairs=[("thumb", "index")],
                pattern="all",
                rationale="thumb/index 交换不是正常轻微相邻手指混淆，仅记录边界。",
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
        group="right_hand",
        pairs=[],
        pattern="all",
        profile=profile,
    )
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(word, min_score):
        query, detail = _mutated_sequence(
            loaded_standard,
            str(spec["variant"]),
            group=str(spec["group"]),
            pairs=spec["pairs"],
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
        "group",
        "pairs",
        "pattern",
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
                        "group": row.get("group"),
                        "pairs": json.dumps(row.get("pairs") or [], ensure_ascii=False),
                        "pattern": row.get("pattern"),
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
        "# 花/跳手指身份抖动鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，交换相邻或非相邻 finger chain 的 landmark 身份后重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：相邻手指链标签混淆和少量帧级身份抖动仍保持可评分；非相邻或多链强交换只记录诊断边界。",
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
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向指链抖动 | 诊断最低分 | 最弱诊断抖动 | 门槛 |")
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
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | 手 | pairs | pattern | 改动帧 | 改动可见点 | capture_quality | semantic_floor | 说明 |")
        lines.append("|---|---|---|---:|---|---|---|---|---:|---:|---|---|---|")
        for row in sorted(item["variants"], key=lambda value: (value["kind"], float(value["score"]))):
            quality = row.get("capture_quality") or {}
            floor = row.get("semantic_floor") or {}
            if row["kind"] == "positive":
                threshold = f">= {row.get('min_score')}"
                status = "PASS" if row["passed"] else "FAIL"
            else:
                threshold = "diagnostic"
                status = "DIAG"
            pairs = json.dumps(row.get("pairs") or [], ensure_ascii=False)
            lines.append(
                f"| {row['variant']} | {row['kind']} | {status} | {_fmt(row['score'])} | "
                f"{threshold} | {row.get('group') or '-'} | `{pairs}` | {row.get('pattern') or '-'} | "
                f"{row.get('changed_frames')} | {row.get('changed_visible_points')} | "
                f"{quality.get('status') or '-'}:{quality.get('reason') or '-'} | "
                f"{floor.get('source') or '-'}:{floor.get('reason') or '-'} | {row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 该门补充的是 hand landmark 拓扑标签混淆，不替代 landmark-noise、fingertip-occlusion、hand-orientation 或 core-shape-amplitude 门。",
            "- `跳` 的最低正向边界来自短序列中的少量 middle/ring 指链身份抖动，当前要求保留在 `70` 分以上。",
            "- 非相邻和多链交换不是正常网页采集要求，只记录诊断分数。",
            "- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run finger identity jitter robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_finger_identity_jitter_robustness_gate_current"))
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
        "claim_policy": "synthetic finger-identity-jitter robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": backend_status,
        "passed": passed,
        "min_score": args.min_score,
        "results": results,
    }

    json_path = output_dir / "flower_jump_finger_identity_jitter_robustness_gate.json"
    md_path = output_dir / "flower_jump_finger_identity_jitter_robustness_gate.md"
    csv_path = output_dir / "flower_jump_finger_identity_jitter_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳手指身份抖动鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳手指身份抖动鲁棒性报告：{md_path}")
    print(f"已生成花/跳手指身份抖动鲁棒性 CSV：{csv_path}")
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

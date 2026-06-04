#!/usr/bin/env python3
"""Stress-test flower/jump scoring against palm/wrist anchor mask loss.

Browser Holistic can briefly lose wrist or MCP palm-anchor landmarks while
fingertips remain visible. The scorer should not turn those short anchor
dropouts into a whole-action failure, but sustained loss of the semantic palm
anchors must stay low or be diagnosed as a recapture/semantic failure.

This script edits cached skeleton sequences in memory only. It does not call
/api/score, run Holistic, move the web marker, or restart 5080.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

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
PALM_ANCHORS = [0, 1, 5, 9, 13, 17]
WRIST_MCP_ANCHORS = [0, 5, 9, 13, 17]
MCP_ANCHORS = [5, 9, 13, 17]
WRIST_ONLY = [0]
ACCEPTED_NEGATIVE_QUALITY = {"needs_recapture", "semantic_mismatch"}


def _indices_for_pattern(pattern: str, length: int) -> Set[int]:
    if length <= 0:
        return set()
    if pattern == "none":
        return set()
    if pattern == "single_mid":
        return {length // 2}
    if pattern == "sparse_every_7th":
        return {idx for idx in range(length) if idx % 7 == 3}
    if pattern == "middle_20pct":
        start = int(round(length * 0.40))
        end = max(start + 1, int(round(length * 0.60)))
        return set(range(max(0, start), min(length, end)))
    if pattern == "core_40pct":
        start = int(round(length * 0.30))
        end = max(start + 1, int(round(length * 0.70)))
        return set(range(max(0, start), min(length, end)))
    if pattern == "all":
        return set(range(length))
    raise ValueError(f"unknown occlusion pattern: {pattern}")


def _occlude_sequence(
    seq: SequenceData,
    name: str,
    *,
    groups: Sequence[str],
    landmarks: Sequence[int],
    pattern: str,
    profile: Any,
) -> Tuple[SequenceData, Dict[str, Any]]:
    base = _strip_to_base_groups(seq)
    selected = _indices_for_pattern(pattern, len(base.features))
    features: List[FrameFeature] = []
    occluded_visible_points = 0
    for idx, frame in enumerate(base.features):
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        presence = dict(frame.presence)
        if idx in selected:
            for group in groups:
                coords, valid = _hand_array(frame, group)
                if coords is None or valid is None:
                    continue
                coords = coords.copy()
                valid = valid.copy()
                for landmark_idx in landmarks:
                    if 0 <= int(landmark_idx) < len(valid):
                        if bool(valid[int(landmark_idx)]):
                            occluded_visible_points += 1
                        valid[int(landmark_idx)] = False
                        coords[int(landmark_idx)] = 0.0
                _set_hand_group(frame, vector, mask, group, coords, valid)
                presence[group] = bool(valid.any())
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
        "occlusion_pattern": pattern,
        "occluded_groups": list(groups),
        "occluded_landmarks": [int(item) for item in landmarks],
        "occlusion_frame_count": len(selected),
        "total_frames": len(base.features),
        "occlusion_ratio": (len(selected) / len(base.features)) if base.features else 0.0,
        "occluded_visible_points": occluded_visible_points,
        "occlusion_indices": sorted(selected),
    }
    return _sequence_with_relative_motion_features(transformed, profile), detail


def _spec(
    variant: str,
    kind: str,
    *,
    groups: Sequence[str],
    landmarks: Sequence[int],
    pattern: str,
    rationale: str,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": kind,
        "groups": list(groups),
        "landmarks": [int(item) for item in landmarks],
        "pattern": pattern,
        "min_score": min_score,
        "max_score": max_score,
        "gated": kind in {"positive", "negative"},
        "rationale": rationale,
    }


def _variant_specs(word: str, min_score: float, negative_max_score: float) -> List[Dict[str, Any]]:
    specs = [
        _spec(
            "self_recomputed",
            "positive",
            groups=[],
            landmarks=[],
            pattern="none",
            min_score=95.0,
            rationale="标准序列剥离基础组后重建 motion/relation 特征，应保持近满分。",
        )
    ]
    if word == "花":
        return specs + [
            _spec(
                "right_single_palm_anchor",
                "positive",
                groups=["right_hand"],
                landmarks=PALM_ANCHORS,
                pattern="single_mid",
                min_score=min_score,
                rationale="开花核心手单帧 wrist/MCP palm anchors 丢失，模拟网页短时追踪断点。",
            ),
            _spec(
                "right_sparse_palm_anchor",
                "positive",
                groups=["right_hand"],
                landmarks=PALM_ANCHORS,
                pattern="sparse_every_7th",
                min_score=min_score,
                rationale="开花核心手稀疏 palm-anchor mask 闪断，指尖和开合过程仍可见。",
            ),
            _spec(
                "right_middle20_mcp_anchor",
                "positive",
                groups=["right_hand"],
                landmarks=MCP_ANCHORS,
                pattern="middle_20pct",
                min_score=min_score,
                rationale="开花核心手中段 20% MCP 锚点不可见，仍应由可见指尖/时序恢复。",
            ),
            _spec(
                "right_middle20_wrist_mcp_anchor",
                "positive",
                groups=["right_hand"],
                landmarks=WRIST_MCP_ANCHORS,
                pattern="middle_20pct",
                min_score=min_score,
                rationale="开花核心手中段 20% wrist+MCP 锚点不可见，作为强正向容错门。",
            ),
            _spec(
                "right_core40_palm_anchor_diagnostic",
                "diagnostic",
                groups=["right_hand"],
                landmarks=PALM_ANCHORS,
                pattern="core_40pct",
                rationale="核心段 40% palm anchors 缺失属于边界情况，记录分数但不设硬门。",
            ),
            _spec(
                "right_all_palm_anchor_negative",
                "negative",
                groups=["right_hand"],
                landmarks=PALM_ANCHORS,
                pattern="all",
                max_score=negative_max_score,
                rationale="开花核心掌根/手指根部全程不可见，不能被当作完整花动作。",
            ),
            _spec(
                "right_all_mcp_anchor_negative",
                "negative",
                groups=["right_hand"],
                landmarks=MCP_ANCHORS,
                pattern="all",
                max_score=negative_max_score,
                rationale="开花核心 MCP 全程不可见时，开合语义不可靠，必须低分或语义失败。",
            ),
        ]
    if word == "跳":
        return specs + [
            _spec(
                "right_single_palm_anchor",
                "positive",
                groups=["right_hand"],
                landmarks=PALM_ANCHORS,
                pattern="single_mid",
                min_score=min_score,
                rationale="右手两指小人单帧 palm anchors 丢失，跳跃关系仍应可评分。",
            ),
            _spec(
                "right_sparse_palm_anchor",
                "positive",
                groups=["right_hand"],
                landmarks=PALM_ANCHORS,
                pattern="sparse_every_7th",
                min_score=min_score,
                rationale="右手两指小人稀疏掌根锚点闪断，双手关系仍保留。",
            ),
            _spec(
                "right_middle20_mcp_anchor",
                "positive",
                groups=["right_hand"],
                landmarks=MCP_ANCHORS,
                pattern="middle_20pct",
                min_score=min_score,
                rationale="右手中段 20% MCP 锚点不可见，但食指/中指和相对运动仍可见。",
            ),
            _spec(
                "right_middle20_wrist_mcp_anchor",
                "positive",
                groups=["right_hand"],
                landmarks=WRIST_MCP_ANCHORS,
                pattern="middle_20pct",
                min_score=min_score,
                rationale="右手中段 20% wrist+MCP 锚点不可见，验证关系 fallback 的稳定性。",
            ),
            _spec(
                "left_single_palm_anchor",
                "positive",
                groups=["left_hand"],
                landmarks=PALM_ANCHORS,
                pattern="single_mid",
                min_score=min_score,
                rationale="左手地面单帧 palm anchors 丢失，地面关系不应整体失败。",
            ),
            _spec(
                "left_sparse_palm_anchor",
                "positive",
                groups=["left_hand"],
                landmarks=PALM_ANCHORS,
                pattern="sparse_every_7th",
                min_score=min_score,
                rationale="左手地面稀疏 palm-anchor mask 闪断，双手关系仍应通过。",
            ),
            _spec(
                "left_middle20_wrist_mcp_anchor",
                "positive",
                groups=["left_hand"],
                landmarks=WRIST_MCP_ANCHORS,
                pattern="middle_20pct",
                min_score=min_score,
                rationale="左手地面中段 20% wrist+MCP 锚点不可见，地面语义仍可由可见点恢复。",
            ),
            _spec(
                "both_sparse_wrist_anchor",
                "positive",
                groups=["left_hand", "right_hand"],
                landmarks=WRIST_ONLY,
                pattern="sparse_every_7th",
                min_score=min_score,
                rationale="双手 wrist 稀疏闪断，覆盖网页手腕点短时漂移/缺失。",
            ),
            _spec(
                "both_middle20_mcp_anchor",
                "positive",
                groups=["left_hand", "right_hand"],
                landmarks=MCP_ANCHORS,
                pattern="middle_20pct",
                min_score=min_score,
                rationale="双手中段 20% MCP 锚点不可见，验证仍可从核心双手关系评分。",
            ),
            _spec(
                "right_core40_palm_anchor_diagnostic",
                "diagnostic",
                groups=["right_hand"],
                landmarks=PALM_ANCHORS,
                pattern="core_40pct",
                rationale="右手核心段 40% palm anchors 缺失属于强边界，仅记录分数。",
            ),
            _spec(
                "left_core40_palm_anchor_diagnostic",
                "diagnostic",
                groups=["left_hand"],
                landmarks=PALM_ANCHORS,
                pattern="core_40pct",
                rationale="左手地面核心段 40% palm anchors 缺失属于强边界，仅记录分数。",
            ),
            _spec(
                "right_all_palm_anchor_negative",
                "negative",
                groups=["right_hand"],
                landmarks=PALM_ANCHORS,
                pattern="all",
                max_score=negative_max_score,
                rationale="右手两指小人掌根/指根全程不可见，双手关系不可靠。",
            ),
            _spec(
                "left_all_palm_anchor_negative",
                "negative",
                groups=["left_hand"],
                landmarks=PALM_ANCHORS,
                pattern="all",
                max_score=negative_max_score,
                rationale="左手地面掌根/指根全程不可见，跳的支撑关系缺失。",
            ),
        ]
    return specs


def _row_passed(row: Dict[str, Any]) -> bool:
    score = float(row["score"])
    if row["kind"] == "positive":
        return score >= float(row["min_score"])
    if row["kind"] == "negative":
        quality = (row.get("capture_quality") or {}).get("status")
        return score <= float(row["max_score"]) or quality in ACCEPTED_NEGATIVE_QUALITY
    return True


def _run_word(
    word: str,
    template_root: Path,
    semantic_profile_json: Path,
    feature_mode: str,
    min_score: float,
    negative_max_score: float,
) -> Dict[str, Any]:
    standard_json = _template_json(template_root, word)
    loaded_standard = load_sequence(standard_json, feature_mode, force_bbox=False)
    profile = load_semantic_profile(word, semantic_profile_json)
    standard, standard_detail = _occlude_sequence(
        loaded_standard,
        "standard_base",
        groups=[],
        landmarks=[],
        pattern="none",
        profile=profile,
    )
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(word, min_score, negative_max_score):
        query, detail = _occlude_sequence(
            loaded_standard,
            str(spec["variant"]),
            groups=spec["groups"],
            landmarks=spec["landmarks"],
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
            "max_score": spec.get("max_score"),
            "rationale": spec["rationale"],
            **detail,
            "score": float(result["prototype_score"]),
            "dtw_distance": float(result["dtw_distance"]),
            "normalized_distance": float(result["normalized_distance"]),
            "alignment_policy": result.get("alignment_policy"),
            "capture_quality": score_scale.get("capture_quality"),
            "semantic_floor": score_scale.get("semantic_floor"),
            "flower_opening_guard": score_scale.get("flower_opening_guard"),
            "action_window": result.get("action_window"),
        }
        row["passed"] = _row_passed(row)
        rows.append(row)
    positive_rows = [row for row in rows if row["kind"] == "positive"]
    negative_rows = [row for row in rows if row["kind"] == "negative"]
    diagnostic_rows = [row for row in rows if row["kind"] == "diagnostic"]
    weakest_positive = min(positive_rows, key=lambda row: float(row["score"])) if positive_rows else None
    strongest_negative = max(negative_rows, key=lambda row: float(row["score"])) if negative_rows else None
    weakest_diagnostic = min(diagnostic_rows, key=lambda row: float(row["score"])) if diagnostic_rows else None
    return {
        "word": word,
        "standard_json": str(standard_json),
        "standard_length": len(standard.features),
        "standard_occlusion_detail": standard_detail,
        "semantic_profile": _profile_summary(profile),
        "gate_pass": all(bool(row["passed"]) for row in rows if row["gated"]),
        "weakest_positive_score": float(weakest_positive["score"]) if weakest_positive else None,
        "weakest_positive_variant": weakest_positive["variant"] if weakest_positive else "",
        "strongest_negative_score": float(strongest_negative["score"]) if strongest_negative else None,
        "strongest_negative_variant": strongest_negative["variant"] if strongest_negative else "",
        "weakest_diagnostic_score": float(weakest_diagnostic["score"]) if weakest_diagnostic else None,
        "weakest_diagnostic_variant": weakest_diagnostic["variant"] if weakest_diagnostic else "",
        "min_required_score": min_score,
        "negative_max_score": negative_max_score,
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
        "max_score",
        "occlusion_pattern",
        "occluded_groups",
        "occluded_landmarks",
        "occlusion_frame_count",
        "occlusion_ratio",
        "occluded_visible_points",
        "alignment_mode",
        "capture_quality_status",
        "capture_quality_reason",
        "semantic_floor_source",
        "semantic_floor_reason",
        "flower_opening_score",
        "flower_opening_passed",
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
                opening = row.get("flower_opening_guard") or {}
                writer.writerow(
                    {
                        "word": item["word"],
                        "variant": row.get("variant"),
                        "kind": row.get("kind"),
                        "gated": row.get("gated"),
                        "passed": row.get("passed"),
                        "score": row.get("score"),
                        "min_score": row.get("min_score"),
                        "max_score": row.get("max_score"),
                        "occlusion_pattern": row.get("occlusion_pattern"),
                        "occluded_groups": ",".join(row.get("occluded_groups") or []),
                        "occluded_landmarks": ",".join(str(value) for value in (row.get("occluded_landmarks") or [])),
                        "occlusion_frame_count": row.get("occlusion_frame_count"),
                        "occlusion_ratio": row.get("occlusion_ratio"),
                        "occluded_visible_points": row.get("occluded_visible_points"),
                        "alignment_mode": policy.get("mode"),
                        "capture_quality_status": quality.get("status"),
                        "capture_quality_reason": quality.get("reason"),
                        "semantic_floor_source": floor.get("source"),
                        "semantic_floor_reason": floor.get("reason"),
                        "flower_opening_score": opening.get("best_score"),
                        "flower_opening_passed": opening.get("passed"),
                        "rationale": row.get("rationale"),
                    }
                )


def _build_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# 花/跳掌根锚点遮挡鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，在 hand landmark mask 层合成 wrist/MCP/palm-anchor 丢失并重建 motion/relation/hand-shape 特征；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：短时或稀疏掌根锚点不可见仍可正常评分；核心掌根/指根全程不可见必须低分或进入重采/语义失败解释。",
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
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向锚点缺失 | 核心全缺最高分 | 最强负例 | 诊断最低分 | 最弱诊断锚点缺失 |")
    lines.append("|---|---|---:|---|---:|---|---:|---|")
    for item in payload["results"]:
        lines.append(
            f"| {item['word']} | {'PASS' if item['gate_pass'] else 'FAIL'} | "
            f"{_fmt(item['weakest_positive_score'])} | {item['weakest_positive_variant']} | "
            f"{_fmt(item['strongest_negative_score'])} | {item['strongest_negative_variant']} | "
            f"{_fmt(item['weakest_diagnostic_score'])} | {item['weakest_diagnostic_variant']} |"
        )
    lines.append("")
    lines.append("## 分项明细")
    for item in payload["results"]:
        lines.extend(["", f"### {item['word']}", "", f"- 标准序列：`{item['standard_json']}`", ""])
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | 遮挡帧 | landmark | capture_quality | semantic_floor | 说明 |")
        lines.append("|---|---|---|---:|---|---:|---|---|---|---|")
        for row in sorted(item["variants"], key=lambda value: (value["kind"], float(value["score"]))):
            quality = row.get("capture_quality") or {}
            floor = row.get("semantic_floor") or {}
            if row["kind"] == "positive":
                threshold = f">= {row.get('min_score')}"
                status = "PASS" if row["passed"] else "FAIL"
            elif row["kind"] == "negative":
                threshold = f"<= {row.get('max_score')} 或重采/语义失败"
                status = "PASS" if row["passed"] else "FAIL"
            else:
                threshold = "diagnostic"
                status = "DIAG"
            landmarks = ",".join(str(value) for value in (row.get("occluded_landmarks") or [])) or "-"
            lines.append(
                f"| {row['variant']} | {row['kind']} | {status} | {_fmt(row['score'])} | "
                f"{threshold} | {row.get('occlusion_frame_count')}/{row.get('total_frames')} | "
                f"{landmarks} | {quality.get('status') or '-'}:{quality.get('reason') or '-'} | "
                f"{floor.get('source') or '-'}:{floor.get('reason') or '-'} | {row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 该门补充的是 wrist/MCP 掌根锚点短时丢失，不替代 fingertip、edge clipping 或整手 missing-mask 门。",
            "- hand-shape 派生特征在 palm scale 不可靠时应标为缺失，避免 `1e-3` 兜底造成形状值爆炸。",
            "- `core40_*_diagnostic` 是强边界记录：当前模型可能仍能从可见指尖和双手关系恢复语义，因此不作为硬失败门。",
            "- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run palm/wrist anchor occlusion robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_palm_anchor_occlusion_robustness_gate_current"))
    parser.add_argument("--words", nargs="+", default=DEFAULT_WORDS)
    parser.add_argument("--feature-mode", choices=["auto", "landmark", "bbox"], default="auto")
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--status-timeout-sec", type=float, default=3.0)
    parser.add_argument("--min-score", type=float, default=70.0)
    parser.add_argument("--negative-max-score", type=float, default=45.0)
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
            negative_max_score=args.negative_max_score,
        )
        for word in args.words
    ]
    backend_status = _load_backend_status(args.backend_url, args.status_timeout_sec)
    passed = all(bool(item["gate_pass"]) for item in results)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "claim_policy": "synthetic palm-anchor occlusion robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": backend_status,
        "passed": passed,
        "min_score": args.min_score,
        "negative_max_score": args.negative_max_score,
        "accepted_negative_quality": sorted(ACCEPTED_NEGATIVE_QUALITY),
        "results": results,
    }

    json_path = output_dir / "flower_jump_palm_anchor_occlusion_robustness_gate.json"
    md_path = output_dir / "flower_jump_palm_anchor_occlusion_robustness_gate.md"
    csv_path = output_dir / "flower_jump_palm_anchor_occlusion_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳掌根锚点遮挡鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳掌根锚点遮挡鲁棒性报告：{md_path}")
    print(f"已生成花/跳掌根锚点遮挡鲁棒性 CSV：{csv_path}")
    print(f"综合状态：{'PASS' if passed else 'FAIL'}")
    for item in results:
        print(
            f"- {item['word']}: {'PASS' if item['gate_pass'] else 'FAIL'} "
            f"positive_min={_fmt(item['weakest_positive_score'])} "
            f"core_anchor_missing_max={_fmt(item['strongest_negative_score'])} "
            f"diagnostic_min={_fmt(item['weakest_diagnostic_score'])}"
        )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

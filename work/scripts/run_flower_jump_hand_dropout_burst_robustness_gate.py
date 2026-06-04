#!/usr/bin/env python3
"""Stress-test flower/jump scoring against contiguous hand detection gaps.

Webcam Holistic can briefly lose one hand for adjacent frames. Short gaps
should remain scoreable, while sustained core-hand gaps should trigger
recapture or semantic-failure diagnostics. This script edits cached skeleton
sequences in memory only; it does not call /api/score, run Holistic, move the
web marker, or restart 5080.
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

import numpy as np

from score_holistic_sequence_mvp import (
    DEFAULT_SEMANTIC_PROFILE_JSON,
    FrameFeature,
    SequenceData,
    _clone_frame,
    _clone_sequence,
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
HAND_SHAPE_GROUPS = {
    "left_hand": ["left_hand", "left_hand_shape"],
    "right_hand": ["right_hand", "right_hand_shape"],
}
DERIVED_GROUPS = {"two_hand_relation", "two_hand_relation_motion"}
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


def _center_start(length: int, burst_len: int) -> int:
    return max(0, int(length // 2) - int(burst_len // 2))


def _expand_groups(groups: Sequence[str]) -> List[str]:
    expanded: List[str] = []
    for group in groups:
        for item in HAND_SHAPE_GROUPS.get(group, [group]):
            if item not in expanded:
                expanded.append(item)
    return expanded


def _presence_ratio(seq: SequenceData) -> Dict[str, float]:
    if not seq.features:
        return {"pose": 0.0, "left_hand": 0.0, "right_hand": 0.0, "face": 0.0}
    return {
        group: sum(1 for item in seq.features if item.presence.get(group)) / len(seq.features)
        for group in ["pose", "left_hand", "right_hand", "face"]
    }


def _mask_hand_burst(seq: SequenceData, name: str, groups: Sequence[str], start: int, length: int) -> SequenceData:
    expanded = _expand_groups(groups)
    stop = min(len(seq.features), max(0, start) + max(0, length))
    items: List[FrameFeature] = []
    for idx, frame in enumerate(seq.features):
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        presence = dict(frame.presence)
        if start <= idx < stop:
            for group in expanded:
                if group not in frame.groups:
                    continue
                sl = frame.groups[group]
                vector[sl] = 0.0
                mask[sl] = 0.0
            if "left_hand" in expanded or "left_hand_shape" in expanded:
                presence["left_hand"] = False
            if "right_hand" in expanded or "right_hand_shape" in expanded:
                presence["right_hand"] = False
        item = _clone_frame(frame, vector=vector, mask=mask)
        item.presence = presence
        items.append(item)
    return _clone_sequence(seq, name, items)


def _rebuild_derived_groups(seq: SequenceData, profile: Any) -> SequenceData:
    items: List[FrameFeature] = []
    for frame in seq.features:
        vectors: List[np.ndarray] = []
        masks: List[np.ndarray] = []
        groups: Dict[str, slice] = {}
        pos = 0
        for name, sl in frame.groups.items():
            if name in DERIVED_GROUPS or name.endswith("_motion"):
                continue
            vector = frame.vector[sl].copy()
            mask = frame.mask[sl].copy()
            vectors.append(vector)
            masks.append(mask)
            groups[name] = slice(pos, pos + len(vector))
            pos += len(vector)
        item = _clone_frame(
            frame,
            vector=np.concatenate(vectors).astype(np.float32),
            mask=np.concatenate(masks).astype(np.float32),
        )
        item.groups = groups
        items.append(item)
    stripped = _clone_sequence(seq, f"{seq.source}::base_groups_only", items)
    return _sequence_with_relative_motion_features(stripped, profile)


def _spec(
    variant: str,
    kind: str,
    groups: Sequence[str],
    start: int,
    length: int,
    rationale: str,
    *,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": kind,
        "groups": list(groups),
        "start": int(start),
        "length": int(length),
        "min_score": min_score,
        "max_score": max_score,
        "rationale": rationale,
    }


def _variant_specs(word: str, seq_len: int, min_score: float) -> List[Dict[str, Any]]:
    if word == "花":
        mid_5 = _center_start(seq_len, 5)
        mid_15 = _center_start(seq_len, max(1, round(seq_len * 0.15)))
        mid_25 = _center_start(seq_len, max(1, round(seq_len * 0.25)))
        mid_35 = _center_start(seq_len, max(1, round(seq_len * 0.35)))
        return [
            _spec("right_core_1f_mid", "positive", ["right_hand"], seq_len // 2, 1, "开花手单帧短空洞。", min_score=min_score),
            _spec("right_core_3f_mid", "positive", ["right_hand"], _center_start(seq_len, 3), 3, "开花手连续 3 帧短空洞。", min_score=min_score),
            _spec("right_core_5f_mid", "positive", ["right_hand"], mid_5, 5, "开花手连续 5 帧短空洞。", min_score=min_score),
            _spec(
                "right_core_15pct_mid",
                "positive",
                ["right_hand"],
                mid_15,
                max(1, round(seq_len * 0.15)),
                "开花手约 15% 中段短空洞，仍应可评分。",
                min_score=min_score,
            ),
            _spec(
                "left_noncore_15pct_mid",
                "positive",
                ["left_hand"],
                mid_15,
                max(1, round(seq_len * 0.15)),
                "非核心手约 15% 中段空洞，不应影响开花语义。",
                min_score=min_score,
            ),
            _spec(
                "right_core_25pct_mid_negative",
                "negative",
                ["right_hand"],
                mid_25,
                max(1, round(seq_len * 0.25)),
                "开花手约 25% 中段缺失，应进入重采或明显降分。",
                max_score=45.0,
            ),
            _spec(
                "right_core_35pct_mid_negative",
                "negative",
                ["right_hand"],
                mid_35,
                max(1, round(seq_len * 0.35)),
                "开花手约 35% 中段缺失，应稳定拒绝。",
                max_score=45.0,
            ),
        ]
    if word == "跳":
        return [
            _spec("right_jump_1f_mid", "positive", ["right_hand"], seq_len // 2, 1, "跳跃手单帧短空洞。", min_score=min_score),
            _spec("right_jump_2f_mid", "positive", ["right_hand"], _center_start(seq_len, 2), 2, "跳跃手连续 2 帧短空洞。", min_score=min_score),
            _spec("right_jump_3f_mid", "positive", ["right_hand"], _center_start(seq_len, 3), 3, "跳跃手连续 3 帧短空洞。", min_score=min_score),
            _spec("left_ground_1f_mid", "positive", ["left_hand"], seq_len // 2, 1, "地面手单帧短空洞。", min_score=min_score),
            _spec("left_ground_2f_mid", "positive", ["left_hand"], _center_start(seq_len, 2), 2, "地面手连续 2 帧短空洞。", min_score=min_score),
            _spec("both_hands_1f_mid", "positive", ["left_hand", "right_hand"], seq_len // 2, 1, "双手同帧短空洞 1 帧。", min_score=min_score),
            _spec(
                "both_hands_2f_mid_negative",
                "negative",
                ["left_hand", "right_hand"],
                _center_start(seq_len, 2),
                2,
                "双手连续 2 帧同时缺失，应进入重采或明显降分。",
                max_score=45.0,
            ),
            _spec(
                "right_jump_4f_mid_negative",
                "negative",
                ["right_hand"],
                _center_start(seq_len, 4),
                4,
                "跳跃手连续 4 帧缺失，应进入重采或明显降分。",
                max_score=45.0,
            ),
        ]
    return []


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
    min_score: float,
) -> Dict[str, Any]:
    standard_json = _template_json(template_root, word)
    standard = load_sequence(standard_json, feature_mode, force_bbox=False)
    profile = load_semantic_profile(word, semantic_profile_json)
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(word, len(standard.features), min_score):
        masked = _mask_hand_burst(standard, spec["variant"], spec["groups"], spec["start"], spec["length"])
        query = _rebuild_derived_groups(masked, profile)
        result = run_pair(standard, query, semantic_profile=profile, enable_cross_check=False)
        score_scale = result.get("score_scale") or {}
        row = {
            **spec,
            "score": float(result["prototype_score"]),
            "dtw_distance": float(result["dtw_distance"]),
            "normalized_distance": float(result["normalized_distance"]),
            "query_length": len(query.features),
            "query_presence": _presence_ratio(query),
            "alignment_policy": result.get("alignment_policy"),
            "capture_quality": score_scale.get("capture_quality"),
            "semantic_floor": score_scale.get("semantic_floor"),
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
        "accepted_negative_quality": sorted(ACCEPTED_NEGATIVE_QUALITY),
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
        "start",
        "length",
        "groups",
        "capture_quality_status",
        "capture_quality_reason",
        "semantic_floor_source",
        "semantic_floor_reason",
        "query_left_presence",
        "query_right_presence",
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
                        "start": row.get("start"),
                        "length": row.get("length"),
                        "groups": "+".join(row.get("groups") or []),
                        "capture_quality_status": quality.get("status"),
                        "capture_quality_reason": quality.get("reason"),
                        "semantic_floor_source": floor.get("source"),
                        "semantic_floor_reason": floor.get("reason"),
                        "query_left_presence": presence.get("left_hand"),
                        "query_right_presence": presence.get("right_hand"),
                        "rationale": row.get("rationale"),
                    }
                )


def _build_markdown(payload: Dict[str, Any]) -> str:
    lines = [
        "# 花/跳连续手部检出空洞鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 总体：`{'PASS' if payload.get('passed') else 'FAIL'}`",
        f"- 模板根目录：`{payload['template_root']}`",
        f"- 语义权重：`{payload['semantic_profile_json']}`",
        f"- 门槛：正向短空洞最低分 `>= {payload['min_score']}`；持续核心空洞需低分或进入 `{', '.join(payload['accepted_negative_quality'])}`。",
        "- 口径：只读缓存 Holistic JSON，在基础手部/手形 mask 层面合成连续空洞，并重建 motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "",
        "## 汇总",
        "",
        "| 词条 | 状态 | 正向最低分 | 最弱正向空洞 | 持续空洞最高分 | 最强持续空洞 |",
        "|---|---|---:|---|---:|---|",
    ]
    for item in payload["results"]:
        lines.append(
            f"| {item['word']} | {'PASS' if item['gate_pass'] else 'FAIL'} | "
            f"{_fmt(item['weakest_positive_score'])} | {item['weakest_positive_variant']} | "
            f"{_fmt(item['strongest_negative_score'])} | {item['strongest_negative_variant']} |"
        )
    lines.extend(["", "## 明细", ""])
    for item in payload["results"]:
        lines.extend(
            [
                f"### {item['word']}",
                "",
                "| 变体 | 类型 | 状态 | 分数 | 帧段 | 组 | quality | floor | 说明 |",
                "|---|---|---|---:|---|---|---|---|---|",
            ]
        )
        for row in item["variants"]:
            quality = row.get("capture_quality") or {}
            floor = row.get("semantic_floor") or {}
            threshold = f">= {row.get('min_score')}" if row["kind"] == "positive" else f"<= {row.get('max_score')} 或重采/语义失败"
            lines.append(
                f"| {row['variant']} | {row['kind']} | {'PASS' if row['passed'] else 'FAIL'} ({threshold}) | "
                f"{_fmt(row['score'])} | {row['start']}+{row['length']} | "
                f"{'+'.join(row.get('groups') or [])} | "
                f"{quality.get('status') or '-'}:{quality.get('reason') or '-'} | "
                f"{floor.get('source') or '-'}:{floor.get('reason') or '-'} | "
                f"{row['rationale']} |"
            )
        lines.append("")
    lines.extend(
        [
            "## 结论",
            "",
            "- 短 burst 检出空洞用于验证网页端偶发 detector 丢帧不会直接打崩正常动作。",
            "- 持续核心手空洞是重采边界，不能用鲁棒性门把这种样本抬成正常高分。",
            "- 该门仍是合成压力测试，不能替代正式 marker 后真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def _default_output_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return DEFAULT_OUTPUT_BASE / f"flower_jump_hand_dropout_burst_robustness_gate_{stamp}"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run flower/jump contiguous hand-dropout burst robustness gate.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--backend-timeout-sec", type=float, default=5.0)
    parser.add_argument("--feature-mode", choices=["auto", "landmark", "bbox"], default="auto")
    parser.add_argument("--min-score", type=float, default=70.0)
    parser.add_argument("--words", nargs="+", default=DEFAULT_WORDS)
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir) if args.output_dir else _default_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    template_root = Path(args.template_root)
    semantic_profile_json = Path(args.semantic_profile_json)
    results = [
        _run_word(word, template_root, semantic_profile_json, args.feature_mode, args.min_score)
        for word in args.words
    ]
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "claim_policy": "synthetic contiguous hand-dropout robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": _load_backend_status(args.backend_url, args.backend_timeout_sec),
        "feature_mode": args.feature_mode,
        "min_score": args.min_score,
        "accepted_negative_quality": sorted(ACCEPTED_NEGATIVE_QUALITY),
        "results": results,
        "passed": all(bool(item.get("gate_pass")) for item in results),
    }
    json_path = output_dir / "flower_jump_hand_dropout_burst_robustness_gate.json"
    md_path = output_dir / "flower_jump_hand_dropout_burst_robustness_gate.md"
    csv_path = output_dir / "flower_jump_hand_dropout_burst_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    _write_rows_csv(csv_path, results)
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    print(f"hand dropout burst gate: {'PASS' if payload['passed'] else 'FAIL'}")
    print(f"json: {json_path}")
    print(f"md: {md_path}")
    print(f"csv: {csv_path}")
    for item in results:
        print(
            f"- {item['word']}: gate={item['gate_pass']} "
            f"positive_min={_fmt(item['weakest_positive_score'])} "
            f"weakest={item['weakest_positive_variant']} "
            f"negative_max={_fmt(item['strongest_negative_score'])}"
        )
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

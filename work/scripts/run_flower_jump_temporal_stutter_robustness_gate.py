#!/usr/bin/env python3
"""Stress-test flower/jump scoring against temporal frame stutter.

Browser camera capture can briefly freeze and upload repeated skeleton frames
while keeping the total frame count unchanged. Short freezes should remain
scoreable, while sustained core-action freezes should be treated as recapture
or semantic-failure evidence. This script edits cached skeleton sequences in
memory only; it does not call /api/score, run Holistic, move the web marker, or
restart 5080.
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


def _strip_derived_groups(seq: SequenceData, name: str) -> SequenceData:
    items: List[FrameFeature] = []
    for frame in seq.features:
        vectors: List[np.ndarray] = []
        masks: List[np.ndarray] = []
        groups: Dict[str, slice] = {}
        pos = 0
        for group, sl in frame.groups.items():
            if group in DERIVED_GROUPS or group.endswith("_motion"):
                continue
            vector = frame.vector[sl].copy()
            mask = frame.mask[sl].copy()
            vectors.append(vector)
            masks.append(mask)
            groups[group] = slice(pos, pos + len(vector))
            pos += len(vector)
        item = _clone_frame(
            frame,
            vector=np.concatenate(vectors).astype(np.float32),
            mask=np.concatenate(masks).astype(np.float32),
        )
        item.groups = groups
        items.append(item)
    return _clone_sequence(seq, name, items)


def _rebuild_derived_groups(seq: SequenceData, profile: Any) -> SequenceData:
    stripped = _strip_derived_groups(seq, f"{seq.source}::base_groups_only")
    return _sequence_with_relative_motion_features(stripped, profile)


def _freeze_burst(seq: SequenceData, name: str, start: int, length: int, anchor: str = "first") -> SequenceData:
    items = list(seq.features)
    if not items:
        return _clone_sequence(seq, name, [])
    n = len(items)
    start = max(0, min(n - 1, int(start)))
    stop = min(n, start + max(1, int(length)))
    if anchor == "middle":
        replacement = items[(start + stop - 1) // 2]
    elif anchor == "last":
        replacement = items[stop - 1]
    else:
        replacement = items[start]
    selected = [replacement if start <= idx < stop else item for idx, item in enumerate(items)]
    return _clone_sequence(seq, name, selected)


def _sparse_freeze(seq: SequenceData, name: str, every: int, paired: bool = False) -> SequenceData:
    items = list(seq.features)
    selected: List[FrameFeature] = []
    for idx, item in enumerate(items):
        should_freeze = idx > 0 and idx < len(items) - 1 and idx % int(every) == 0
        if paired:
            should_freeze = should_freeze or (idx > 1 and idx < len(items) - 1 and idx % int(every) == 1)
        selected.append(items[idx - 1] if should_freeze else item)
    return _clone_sequence(seq, name, selected)


def _spec(
    variant: str,
    kind: str,
    start: int = 0,
    length: int = 0,
    rationale: str = "",
    *,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    sparse_every: Optional[int] = None,
    sparse_paired: bool = False,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": kind,
        "start": int(start),
        "length": int(length),
        "sparse_every": sparse_every,
        "sparse_paired": bool(sparse_paired),
        "min_score": min_score,
        "max_score": max_score,
        "rationale": rationale,
    }


def _variant_specs(word: str, seq_len: int, min_score: float) -> List[Dict[str, Any]]:
    if word == "花":
        len_15 = max(1, round(seq_len * 0.15))
        len_25 = max(1, round(seq_len * 0.25))
        len_35 = max(1, round(seq_len * 0.35))
        len_50 = max(1, round(seq_len * 0.50))
        return [
            _spec("freeze_mid_3f", "positive", _center_start(seq_len, 3), 3, "中段短帧冻结 3 帧。", min_score=min_score),
            _spec("freeze_mid_5f", "positive", _center_start(seq_len, 5), 5, "中段短帧冻结 5 帧。", min_score=min_score),
            _spec("freeze_mid_15pct", "positive", _center_start(seq_len, len_15), len_15, "中段约 15% 短冻结。", min_score=min_score),
            _spec("freeze_start_5f", "positive", 0, 5, "开头短冻结，核心开花动作仍在。", min_score=min_score),
            _spec("freeze_end_5f", "positive", max(0, seq_len - 5), 5, "结尾短冻结，核心开花动作已完成。", min_score=min_score),
            _spec("sparse_freeze_every_7th", "positive", rationale="每 7 帧一次微冻结。", min_score=min_score, sparse_every=7),
            _spec("sparse_freeze_every_5th", "positive", rationale="每 5 帧一次微冻结。", min_score=min_score, sparse_every=5),
            _spec("paired_sparse_freeze_every_7th", "positive", rationale="每 7 帧附近出现连续两帧微冻结。", min_score=min_score, sparse_every=7, sparse_paired=True),
            _spec("freeze_mid_25pct_diagnostic", "diagnostic", _center_start(seq_len, len_25), len_25, "中段约 25% 冻结，只记录边界。"),
            _spec("freeze_mid_35pct_negative", "negative", _center_start(seq_len, len_35), len_35, "中段约 35% 核心动作冻结，应明显降分。", max_score=45.0),
            _spec("freeze_mid_50pct_negative", "negative", _center_start(seq_len, len_50), len_50, "中段约 50% 核心动作冻结，应拒绝。", max_score=45.0),
            _spec("freeze_full_negative", "negative", 0, seq_len, "全段静态冻结，缺少动态语义。", max_score=45.0),
        ]
    if word == "跳":
        len_35 = max(1, round(seq_len * 0.35))
        return [
            _spec("freeze_mid_2f", "positive", _center_start(seq_len, 2), 2, "弹跳中段短冻结 2 帧。", min_score=min_score),
            _spec("freeze_mid_3f", "positive", _center_start(seq_len, 3), 3, "弹跳中段短冻结 3 帧。", min_score=min_score),
            _spec("freeze_mid_4f", "positive", _center_start(seq_len, 4), 4, "短动作中段约 4 帧冻结，仍保留足够弹跳证据。", min_score=min_score),
            _spec("freeze_start_2f", "positive", 0, 2, "开头短冻结，弹跳主段仍在。", min_score=min_score),
            _spec("freeze_end_2f", "positive", max(0, seq_len - 2), 2, "结尾短冻结，弹跳主段已完成。", min_score=min_score),
            _spec("sparse_freeze_every_7th", "positive", rationale="每 7 帧一次微冻结。", min_score=min_score, sparse_every=7),
            _spec("sparse_freeze_every_5th", "positive", rationale="每 5 帧一次微冻结。", min_score=min_score, sparse_every=5),
            _spec("paired_sparse_freeze_every_7th", "positive", rationale="每 7 帧附近出现连续两帧微冻结。", min_score=min_score, sparse_every=7, sparse_paired=True),
            _spec("freeze_mid_5f_diagnostic", "diagnostic", _center_start(seq_len, 5), 5, "短动作中段约 5 帧冻结，记录边界。"),
            _spec("freeze_mid_35pct_negative", "negative", _center_start(seq_len, len_35), len_35, "中段约 35% 弹跳核心冻结，应重采或明显降分。", max_score=45.0),
            _spec("freeze_full_negative", "negative", 0, seq_len, "全段静态冻结，缺少弹跳动态。", max_score=45.0),
        ]
    return []


def _apply_variant(seq: SequenceData, spec: Dict[str, Any]) -> SequenceData:
    if spec.get("sparse_every"):
        return _sparse_freeze(seq, spec["variant"], int(spec["sparse_every"]), bool(spec.get("sparse_paired")))
    return _freeze_burst(seq, spec["variant"], int(spec["start"]), int(spec["length"]))


def _row_passed(row: Dict[str, Any]) -> bool:
    if row["kind"] == "diagnostic":
        return True
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
        query = _rebuild_derived_groups(_apply_variant(standard, spec), profile)
        result = run_pair(standard, query, semantic_profile=profile, enable_cross_check=False)
        score_scale = result.get("score_scale") or {}
        row = {
            **spec,
            "score": float(result["prototype_score"]),
            "dtw_distance": float(result["dtw_distance"]),
            "normalized_distance": float(result["normalized_distance"]),
            "query_length": len(query.features),
            "length_ratio": len(query.features) / max(len(standard.features), 1),
            "alignment_policy": result.get("alignment_policy"),
            "capture_quality": score_scale.get("capture_quality"),
            "semantic_floor": score_scale.get("semantic_floor"),
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
        "semantic_profile": _profile_summary(profile),
        "accepted_negative_quality": sorted(ACCEPTED_NEGATIVE_QUALITY),
        "gate_pass": all(bool(row["passed"]) for row in rows),
        "weakest_positive_score": float(weakest_positive["score"]) if weakest_positive else None,
        "weakest_positive_variant": weakest_positive["variant"] if weakest_positive else "",
        "strongest_negative_score": float(strongest_negative["score"]) if strongest_negative else None,
        "strongest_negative_variant": strongest_negative["variant"] if strongest_negative else "",
        "weakest_diagnostic_score": float(weakest_diagnostic["score"]) if weakest_diagnostic else None,
        "weakest_diagnostic_variant": weakest_diagnostic["variant"] if weakest_diagnostic else "",
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
        "sparse_every",
        "sparse_paired",
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
                        "sparse_every": row.get("sparse_every"),
                        "sparse_paired": row.get("sparse_paired"),
                        "capture_quality_status": quality.get("status"),
                        "capture_quality_reason": quality.get("reason"),
                        "semantic_floor_source": floor.get("source"),
                        "semantic_floor_reason": floor.get("reason"),
                        "rationale": row.get("rationale"),
                    }
                )


def _build_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# 花/跳时序帧冻结 stutter 鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 总体：`{'PASS' if payload.get('passed') else 'FAIL'}`",
        f"- 模板根目录：`{payload['template_root']}`",
        f"- 语义权重：`{payload['semantic_profile_json']}`",
        f"- 门槛：正向短冻结最低分 `>= {payload['min_score']}`；持续核心冻结需低分或进入 `{', '.join(payload['accepted_negative_quality'])}`。",
        "- 口径：只读缓存 Holistic JSON，在固定长度骨架序列内合成重复/冻结帧，并重建 motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "",
        "## 汇总",
        "",
        "| 词条 | 状态 | 正向最低分 | 最弱正向 stutter | 持续冻结最高分 | 最强持续冻结 | 诊断最低分 | 最弱诊断边界 |",
        "|---|---|---:|---|---:|---|---:|---|",
    ]
    for item in payload["results"]:
        lines.append(
            f"| {item['word']} | {'PASS' if item['gate_pass'] else 'FAIL'} | "
            f"{_fmt(item['weakest_positive_score'])} | {item['weakest_positive_variant']} | "
            f"{_fmt(item['strongest_negative_score'])} | {item['strongest_negative_variant']} | "
            f"{_fmt(item['weakest_diagnostic_score'])} | {item['weakest_diagnostic_variant'] or '-'} |"
        )
    lines.extend(["", "## 明细", ""])
    for item in payload["results"]:
        lines.extend(
            [
                f"### {item['word']}",
                "",
                "| 变体 | 类型 | 状态 | 分数 | 阈值 | 帧段/稀疏 | quality | floor | 说明 |",
                "|---|---|---|---:|---|---|---|---|---|",
            ]
        )
        for row in item["variants"]:
            quality = row.get("capture_quality") or {}
            floor = row.get("semantic_floor") or {}
            if row["kind"] == "positive":
                threshold = f">= {row.get('min_score')}"
            elif row["kind"] == "negative":
                threshold = f"<= {row.get('max_score')} 或重采/语义失败"
            else:
                threshold = "diagnostic"
            span = f"{row.get('start')}+{row.get('length')}"
            if row.get("sparse_every"):
                span = f"every={row.get('sparse_every')}, paired={row.get('sparse_paired')}"
            lines.append(
                f"| {row['variant']} | {row['kind']} | {'PASS' if row['passed'] else 'FAIL'} | "
                f"{_fmt(row['score'])} | {threshold} | {span} | "
                f"{quality.get('status') or '-'}:{quality.get('reason') or '-'} | "
                f"{floor.get('source') or '-'}:{floor.get('reason') or '-'} | "
                f"{row['rationale']} |"
            )
        lines.append("")
    lines.extend(
        [
            "## 结论",
            "",
            "- 短 burst 或稀疏微冻结用于验证浏览器摄像头偶发卡顿不会直接打崩正常动作。",
            "- 持续核心动作冻结是重采边界，不能通过鲁棒性门把这种样本抬成正常高分。",
            "- 该门仍是合成压力测试，不能替代正式 marker 后真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def _default_output_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return DEFAULT_OUTPUT_BASE / f"flower_jump_temporal_stutter_robustness_gate_{stamp}"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run flower/jump temporal stutter robustness gate.")
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
        "claim_policy": "synthetic temporal frame-stutter robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": _load_backend_status(args.backend_url, args.backend_timeout_sec),
        "feature_mode": args.feature_mode,
        "min_score": args.min_score,
        "accepted_negative_quality": sorted(ACCEPTED_NEGATIVE_QUALITY),
        "results": results,
        "passed": all(bool(item.get("gate_pass")) for item in results),
    }
    json_path = output_dir / "flower_jump_temporal_stutter_robustness_gate.json"
    md_path = output_dir / "flower_jump_temporal_stutter_robustness_gate.md"
    csv_path = output_dir / "flower_jump_temporal_stutter_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    _write_rows_csv(csv_path, results)
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    print(f"temporal stutter gate: {'PASS' if payload['passed'] else 'FAIL'}")
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

#!/usr/bin/env python3
"""Stress-test flower/jump scoring against frame-count and sampling changes.

This gate targets a practical web-scoring risk: browser capture can produce
different numbers of useful frames, nonuniform motion coverage, or repeated
near-static frames. A semantic weighted DTW scorer should keep the same target
sign high when the start/middle/end action semantics are still covered.

The script only reads cached Holistic JSON and resamples skeleton sequences in
memory. It does not call /api/score, does not run Holistic, and does not restart
the persistent backend.
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
DEFAULT_MIN_VALID_FRAMES = {"花": 12, "跳": 6}


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


def _resample_by_curve(seq: SequenceData, name: str, length: int, gamma: float = 1.0) -> SequenceData:
    items = seq.features
    if not items:
        return _clone_sequence(seq, name, [])
    if length <= 1:
        selected = [items[len(items) // 2]]
    else:
        t = np.linspace(0.0, 1.0, int(length), dtype=np.float32)
        if gamma != 1.0:
            t = np.power(t, float(gamma))
        indices = np.rint(t * (len(items) - 1)).astype(int)
        indices[0] = 0
        indices[-1] = len(items) - 1
        selected = [items[int(idx)] for idx in indices]
    return _clone_sequence(seq, name, selected)


def _drop_pattern(seq: SequenceData, name: str, keep_every: int, offset: int = 0) -> SequenceData:
    items = seq.features
    selected: List[FrameFeature] = []
    for idx, item in enumerate(items):
        if idx == 0 or idx == len(items) - 1 or (idx + offset) % keep_every == 0:
            selected.append(item)
    if len(selected) < 3:
        selected = [items[0], items[len(items) // 2], items[-1]]
    return _clone_sequence(seq, name, selected)


def _repeat_core(seq: SequenceData, name: str) -> SequenceData:
    items = seq.features
    if len(items) < 4:
        return _clone_sequence(seq, name, items)
    indices = np.rint(np.linspace(0, len(items) - 1, min(16, max(8, len(items) // 2)))).astype(int).tolist()
    mid = len(indices) // 2
    expanded = indices[:mid] + indices[max(0, mid - 2) : min(len(indices), mid + 3)] + indices[mid:]
    selected = [items[idx] for idx in expanded]
    return _clone_sequence(seq, name, selected)


def _variant_lengths(seq: SequenceData) -> List[int]:
    base = len(seq.features)
    raw = [8, 12, 16, 24, 32, 48, 80, max(6, base // 3), max(8, base // 2), base * 2]
    lengths: List[int] = []
    for value in raw:
        value = int(value)
        if value not in lengths:
            lengths.append(value)
    return lengths


def _build_variants(seq: SequenceData) -> List[SequenceData]:
    variants = [_clone_sequence(seq, "self", seq.features)]
    for length in _variant_lengths(seq):
        variants.append(_resample_by_curve(seq, f"uniform_{length}f", length))
    variants.extend(
        [
            _resample_by_curve(seq, "front_dense_16f", 16, gamma=1.65),
            _resample_by_curve(seq, "back_dense_16f", 16, gamma=0.62),
            _resample_by_curve(seq, "front_dense_24f", 24, gamma=1.65),
            _resample_by_curve(seq, "back_dense_24f", 24, gamma=0.62),
            _drop_pattern(seq, "drop_every_2_keep_ends", 2),
            _drop_pattern(seq, "drop_every_3_keep_ends", 3, offset=1),
            _repeat_core(seq, "repeat_mid_core"),
        ]
    )
    deduped: List[SequenceData] = []
    seen = set()
    for item in variants:
        if item.source in seen:
            continue
        seen.add(item.source)
        deduped.append(item)
    return deduped


def _run_word(
    word: str,
    template_root: Path,
    semantic_profile_json: Path,
    feature_mode: str,
    min_score: float,
    min_valid_frames: int,
) -> Dict[str, Any]:
    standard_json = _template_json(template_root, word)
    standard = load_sequence(standard_json, feature_mode, force_bbox=False)
    profile = load_semantic_profile(word, semantic_profile_json)
    rows: List[Dict[str, Any]] = []
    for query in _build_variants(standard):
        variant = query.source.rsplit("::", 1)[-1]
        result = run_pair(standard, query, semantic_profile=profile)
        score_scale = result.get("score_scale") or {}
        capture_quality = score_scale.get("capture_quality") or {}
        semantic_floor = score_scale.get("semantic_floor") or {}
        rows.append(
            {
                "variant": variant,
                "score": float(result["prototype_score"]),
                "dtw_distance": float(result["dtw_distance"]),
                "normalized_distance": float(result["normalized_distance"]),
                "query_length": len(query.features),
                "length_ratio": len(query.features) / max(len(standard.features), 1),
                "alignment_policy": result.get("alignment_policy"),
                "capture_quality_status": capture_quality.get("status"),
                "semantic_floor_source": semantic_floor.get("source"),
                "included_in_gate": len(query.features) >= min_valid_frames,
            }
        )
    gate_rows = [row for row in rows if bool(row.get("included_in_gate"))]
    diagnostic_rows = [row for row in rows if not bool(row.get("included_in_gate"))]
    weakest = min(gate_rows, key=lambda row: float(row["score"])) if gate_rows else None
    weakest_diagnostic = min(diagnostic_rows, key=lambda row: float(row["score"])) if diagnostic_rows else None
    return {
        "word": word,
        "standard_json": str(standard_json),
        "standard_length": len(standard.features),
        "semantic_profile": _profile_summary(profile),
        "min_required_score": min_score,
        "min_valid_frames": min_valid_frames,
        "min_observed_score": float(weakest["score"]) if weakest else None,
        "weakest_variant": weakest["variant"] if weakest else "",
        "diagnostic_min_score": float(weakest_diagnostic["score"]) if weakest_diagnostic else None,
        "diagnostic_weakest_variant": weakest_diagnostic["variant"] if weakest_diagnostic else "",
        "gate_pass": bool(gate_rows) and float(weakest["score"]) >= min_score,
        "variants": rows,
    }


def _write_rows_csv(path: Path, results: Sequence[Dict[str, Any]]) -> None:
    fields = [
        "word",
        "variant",
        "score",
        "dtw_distance",
        "normalized_distance",
        "query_length",
        "standard_length",
        "length_ratio",
        "alignment_policy",
        "capture_quality_status",
        "semantic_floor_source",
        "included_in_gate",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in results:
            for row in item["variants"]:
                writer.writerow(
                    {
                        "word": item["word"],
                        "variant": row.get("variant"),
                        "score": row.get("score"),
                        "dtw_distance": row.get("dtw_distance"),
                        "normalized_distance": row.get("normalized_distance"),
                        "query_length": row.get("query_length"),
                        "standard_length": item.get("standard_length"),
                        "length_ratio": row.get("length_ratio"),
                        "alignment_policy": row.get("alignment_policy"),
                        "capture_quality_status": row.get("capture_quality_status"),
                        "semantic_floor_source": row.get("semantic_floor_source"),
                        "included_in_gate": row.get("included_in_gate"),
                    }
                )


def _build_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# 花/跳帧数与采样密度鲁棒性门")
    lines.append("")
    lines.append(f"- 生成时间：`{payload['generated_at']}`")
    lines.append(f"- 标准库：`{payload['template_root']}`")
    lines.append(f"- 语义 profile：`{payload['semantic_profile_json']}`")
    lines.append("- 口径：只读缓存 Holistic JSON，在骨架序列层面重采样，不调用 `/api/score`，不重启 Holistic。")
    lines.append("- 目标：验证 `花/跳` 在推荐有效帧数内的稀疏/密集抽样和非均匀时间覆盖下仍保持正常或边界以上得分；低于推荐帧数的变体仅作为欠采样风险诊断。")
    lines.append("")
    backend = payload.get("backend_status") or {}
    if backend.get("ok"):
        data = backend.get("payload") or {}
        worker = data.get("worker") or {}
        scoring = data.get("scoring_module") or {}
        lines.append(
            f"- 5080 状态：worker=`{worker.get('status')}`，"
            f"worker_pid=`{((worker.get('ready_payload') or {}).get('pid'))}`，"
            f"reload_count=`{scoring.get('reload_count')}`，"
            f"last_reload_error=`{scoring.get('last_reload_error')}`"
        )
    else:
        lines.append(f"- 5080 状态：未读取或读取失败 `{backend.get('error') or '-'}`")
    lines.append("")
    lines.append("## 结论")
    lines.append("")
    lines.append(f"- 综合状态：`{'PASS' if payload['passed'] else 'FAIL'}`")
    lines.append(f"- 变体最低分门槛：`{payload['min_score']}`")
    lines.append("")
    lines.append("| 目标词 | 状态 | 标准帧数 | 推荐最少帧 | 门控最低分 | 最弱门控采样 | 欠采样最低分 |")
    lines.append("|---|---|---:|---:|---:|---|---:|")
    for item in payload["results"]:
        lines.append(
            f"| {item['word']} | {'PASS' if item['gate_pass'] else 'FAIL'} | "
            f"{item['standard_length']} | {item['min_valid_frames']} | "
            f"{_fmt(item['min_observed_score'])} | {item['weakest_variant'] or '-'} | "
            f"{_fmt(item.get('diagnostic_min_score'))} |"
        )
    lines.append("")
    lines.append("## 分项明细")
    for item in payload["results"]:
        lines.append("")
        lines.append(f"### {item['word']}")
        lines.append("")
        lines.append(f"- 标准序列：`{item['standard_json']}`")
        lines.append(f"- gate：`{'PASS' if item['gate_pass'] else 'FAIL'}`")
        lines.append(f"- 推荐最少帧：`{item['min_valid_frames']}`")
        lines.append(f"- 门控最低分：`{_fmt(item['min_observed_score'])}`，最弱门控采样：`{item['weakest_variant'] or '-'}`")
        if item.get("diagnostic_weakest_variant"):
            lines.append(
                f"- 欠采样诊断最低分：`{_fmt(item.get('diagnostic_min_score'))}`，"
                f"欠采样变体：`{item.get('diagnostic_weakest_variant')}`"
            )
        lines.append("")
        lines.append("| 采样变体 | 分数 | query 帧数 | 门控 | 长度比 | normalized_distance | alignment | quality | floor |")
        lines.append("|---|---:|---:|---|---:|---:|---|---|---|")
        for row in sorted(item["variants"], key=lambda r: float(r["score"])):
            lines.append(
                f"| {row['variant']} | {_fmt(row['score'])} | {row['query_length']} | "
                f"{'yes' if row.get('included_in_gate') else 'undersampled'} | "
                f"{_fmt(row['length_ratio'], 2)} | {_fmt(row['normalized_distance'], 6)} | "
                f"{row.get('alignment_policy') or '-'} | {row.get('capture_quality_status') or '-'} | "
                f"{row.get('semantic_floor_source') or '-'} |"
            )
    lines.append("")
    lines.append("## 说明")
    lines.append("")
    lines.append("- 该门关注同一语义动作在推荐帧数内的采样差异，不代表所有真实用户动作都会通过；真实网页摄像头样本仍需要 watcher 增量诊断。")
    lines.append("- 当前推荐：`花` 至少 12 个有效骨架帧，`跳` 至少 6 个有效骨架帧；前端实际采集仍建议 3 秒、约 24-36 帧，以抵消 Holistic 缺帧和手部遮挡。")
    lines.append("- 若该门失败，优先检查语义相位、start/mid/end 锚点、短视频核心段 floor、opening guard 与 two-hand relation fallback 对帧数变化的兼容性。")
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run frame-count robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_frame_count_robustness_gate_current"))
    parser.add_argument("--words", nargs="+", default=DEFAULT_WORDS)
    parser.add_argument("--feature-mode", choices=["auto", "landmark", "bbox"], default="auto")
    parser.add_argument("--min-score", type=float, default=70.0)
    parser.add_argument("--flower-min-valid-frames", type=int, default=DEFAULT_MIN_VALID_FRAMES["花"])
    parser.add_argument("--jump-min-valid-frames", type=int, default=DEFAULT_MIN_VALID_FRAMES["跳"])
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
            min_score=args.min_score,
            min_valid_frames=args.flower_min_valid_frames if word == "花" else args.jump_min_valid_frames,
        )
        for word in args.words
    ]
    backend_status = _load_backend_status(args.backend_url, args.status_timeout_sec)
    passed = all(bool(item["gate_pass"]) for item in results)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "claim_policy": "synthetic frame-count/sampling robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "min_score": args.min_score,
        "min_valid_frames": {
            "花": args.flower_min_valid_frames,
            "跳": args.jump_min_valid_frames,
        },
        "backend_status": backend_status,
        "passed": passed,
        "results": results,
    }

    json_path = output_dir / "flower_jump_frame_count_robustness_gate.json"
    md_path = output_dir / "flower_jump_frame_count_robustness_gate.md"
    csv_path = output_dir / "flower_jump_frame_count_robustness_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳帧数鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳帧数鲁棒性报告：{md_path}")
    print(f"已生成花/跳帧数鲁棒性 CSV：{csv_path}")
    print(f"综合状态：{'PASS' if passed else 'FAIL'}")
    for item in results:
        print(
            f"- {item['word']}: {'PASS' if item['gate_pass'] else 'FAIL'} "
            f"min_score={_fmt(item['min_observed_score'])} weakest={item['weakest_variant']}"
        )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

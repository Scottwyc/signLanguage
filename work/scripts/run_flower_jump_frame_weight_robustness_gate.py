#!/usr/bin/env python3
"""Stress-test flower/jump scoring against uploaded frame-weight patterns.

The browser upload path sends nonuniform frame_weights derived from motion
energy. The scorer also recomputes semantic frame weights and combines the
browser prior conservatively. This gate verifies that correct browser-like
weights, mild weight noise, one-frame weight shifts, broad front/back emphasis,
and malformed finite/non-finite upload weights keep flower/jump scores high
after sanitization. Pathological inverted weights are kept as diagnostic-only
because they represent a bad upload prior rather than a normal user-signing
variation.

This script edits cached frame_weight values in memory only. It does not call
/api/score, run Holistic, move marker, or restart 5080.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

import numpy as np

from score_holistic_sequence_mvp import (
    DEFAULT_SEMANTIC_PROFILE_JSON,
    SequenceData,
    _clone_frame,
    _clone_sequence,
    _normalize_frame_weights,
    _profile_summary,
    compute_semantic_frame_weight_values,
    load_semantic_profile,
    load_sequence,
    run_pair,
)


REPO_ROOT = Path("/data/WYC/signLanguage")
DEFAULT_TEMPLATE_ROOT = REPO_ROOT / "work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results"
DEFAULT_OUTPUT_BASE = REPO_ROOT / "work/generated/scoring_mvp_run3"
DEFAULT_BACKEND_URL = "http://127.0.0.1:5080"
DEFAULT_WORDS = ["花", "跳"]


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


def _with_frame_weights(seq: SequenceData, name: str, weights: Sequence[float]) -> SequenceData:
    values = np.asarray(weights, dtype=np.float32)
    features = []
    for idx, feature in enumerate(seq.features):
        item = _clone_frame(feature)
        item.frame_weight = float(values[idx]) if idx < values.size else 1.0
        features.append(item)
    return _clone_sequence(seq, name, features)


def _gaussian_weights(n: int, center: float, width: float) -> np.ndarray:
    x = np.arange(n, dtype=np.float32)
    raw = 0.45 + 2.35 * np.exp(-0.5 * ((x - float(center)) / max(float(width), 1e-6)) ** 2)
    return _normalize_frame_weights(raw, low=0.35, high=3.0)


def _ramp_weights(n: int, start: float, end: float) -> np.ndarray:
    return _normalize_frame_weights(np.linspace(float(start), float(end), n, dtype=np.float32), low=0.35, high=3.0)


def _malformed_sparse_weights(seq: SequenceData, profile: Any) -> np.ndarray:
    weights = compute_semantic_frame_weight_values(seq, profile=profile, combine_stored=False).astype(np.float64)
    if weights.size >= 1:
        weights[0] = np.nan
    if weights.size >= 2:
        weights[1] = np.inf
    if weights.size >= 3:
        weights[2] = -np.inf
    if weights.size >= 4:
        weights[3] = -5.0
    if weights.size >= 5:
        weights[4] = 0.0
    if weights.size >= 6:
        weights[5] = 1.0e9
    return weights


def _all_invalid_weights(seq: SequenceData, profile: Any) -> np.ndarray:
    weights = np.full(len(seq.features), np.nan, dtype=np.float64)
    if weights.size:
        weights[::2] = np.inf
    if weights.size >= 3:
        weights[2::3] = -np.inf
    return weights


def _single_extreme_spike(seq: SequenceData, profile: Any) -> np.ndarray:
    weights = np.ones(len(seq.features), dtype=np.float64)
    if weights.size:
        weights[len(weights) // 2] = 1.0e12
    return weights


def _finite_weight_stats(values: np.ndarray) -> Dict[str, Any]:
    finite = values[np.isfinite(values)]
    return {
        "uploaded_weight_min": float(finite.min()) if finite.size else None,
        "uploaded_weight_max": float(finite.max()) if finite.size else None,
        "uploaded_weight_nonfinite": int(values.size - finite.size),
        "uploaded_weight_nonpositive": int(np.sum(finite <= 0.0)) if finite.size else 0,
        "uploaded_weight_extreme": int(np.sum(np.abs(finite) > 10.0)) if finite.size else 0,
    }


WeightFactory = Callable[[SequenceData, Any], np.ndarray]


def _spec(
    variant: str,
    kind: str,
    weights: WeightFactory,
    rationale: str,
    min_score: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": kind,
        "weights": weights,
        "min_score": min_score,
        "gated": kind == "positive",
        "rationale": rationale,
    }


def _variant_specs(min_score: float) -> List[Dict[str, Any]]:
    def dynamic(seq: SequenceData, profile: Any) -> np.ndarray:
        return compute_semantic_frame_weight_values(seq, profile=profile, combine_stored=False)

    def noisy_dynamic(seq: SequenceData, profile: Any) -> np.ndarray:
        base = dynamic(seq, profile)
        rng = np.random.default_rng(20260603)
        return _normalize_frame_weights(base * rng.lognormal(mean=0.0, sigma=0.15, size=base.size), low=0.35, high=3.0)

    return [
        _spec(
            "uniform_1.0",
            "positive",
            lambda seq, profile: np.ones(len(seq.features), dtype=np.float32),
            "浏览器未提供有效非均匀权重时，完整骨架仍应可评分。",
            min_score=min_score,
        ),
        _spec(
            "semantic_dynamic_motion_weights",
            "positive",
            dynamic,
            "按当前语义 motion energy 生成的浏览器式权重。",
            min_score=min_score,
        ),
        _spec(
            "semantic_dynamic_noisy_15pct",
            "positive",
            noisy_dynamic,
            "浏览器 motion 权重有约 15% 乘性噪声。",
            min_score=min_score,
        ),
        _spec(
            "semantic_dynamic_shift_forward_1",
            "positive",
            lambda seq, profile: np.roll(dynamic(seq, profile), 1),
            "上传权重相对骨架轻微错后一帧。",
            min_score=min_score,
        ),
        _spec(
            "semantic_dynamic_shift_backward_1",
            "positive",
            lambda seq, profile: np.roll(dynamic(seq, profile), -1),
            "上传权重相对骨架轻微提前一帧。",
            min_score=min_score,
        ),
        _spec(
            "center_gaussian_emphasis",
            "positive",
            lambda seq, profile: _gaussian_weights(len(seq.features), (len(seq.features) - 1) / 2.0, max(1.0, len(seq.features) * 0.18)),
            "浏览器把中段高运动区域整体加权。",
            min_score=min_score,
        ),
        _spec(
            "front_loaded_broad_emphasis",
            "positive",
            lambda seq, profile: _ramp_weights(len(seq.features), 2.8, 0.45),
            "浏览器权重略偏向动作前段，但不是极端尖峰。",
            min_score=min_score,
        ),
        _spec(
            "back_loaded_broad_emphasis",
            "positive",
            lambda seq, profile: _ramp_weights(len(seq.features), 0.45, 2.8),
            "浏览器权重略偏向动作后段，但不是极端尖峰。",
            min_score=min_score,
        ),
        _spec(
            "malformed_sparse_sanitized",
            "positive",
            _malformed_sparse_weights,
            "稀疏 NaN/Inf/负数/零/极大上传权重应被清洗成安全权重，不污染评分。",
            min_score=min_score,
        ),
        _spec(
            "single_extreme_spike_sanitized",
            "positive",
            _single_extreme_spike,
            "单帧极大上传权重应被上限裁剪并重新归一化，不让一帧主导评分。",
            min_score=min_score,
        ),
        _spec(
            "all_invalid_fallback",
            "positive",
            _all_invalid_weights,
            "整段上传权重不可用时，应回退到语义动态权重/均匀安全先验而不是失败。",
            min_score=min_score,
        ),
        _spec(
            "inverted_dynamic_diagnostic",
            "diagnostic",
            lambda seq, profile: _normalize_frame_weights(1.0 / np.maximum(dynamic(seq, profile), 0.05), low=0.35, high=3.0),
            "反向 motion 权重是坏上传先验，只记录诊断边界。",
        ),
    ]


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
    for spec in _variant_specs(min_score):
        weights = np.asarray(spec["weights"](standard, profile), dtype=np.float32)
        query = _with_frame_weights(standard, spec["variant"], weights)
        result = run_pair(standard, query, semantic_profile=profile, enable_cross_check=False)
        score_scale = result.get("score_scale") or {}
        frame_summary = result.get("frame_weight_summary") or {}
        query_full = frame_summary.get("query_full") or {}
        finite_stats = _finite_weight_stats(weights)
        row = {
            "variant": spec["variant"],
            "kind": spec["kind"],
            "gated": bool(spec["gated"]),
            "min_score": spec.get("min_score"),
            "rationale": spec["rationale"],
            "score": float(result["prototype_score"]),
            "dtw_distance": float(result["dtw_distance"]),
            "normalized_distance": float(result["normalized_distance"]),
            "query_length": len(query.features),
            **finite_stats,
            "scoring_weight_min": query_full.get("min"),
            "scoring_weight_max": query_full.get("max"),
            "alignment_policy": result.get("alignment_policy"),
            "action_window": result.get("action_window"),
            "capture_quality": score_scale.get("capture_quality"),
            "semantic_floor": score_scale.get("semantic_floor"),
        }
        finite_result_values = [
            row["score"],
            row["dtw_distance"],
            row["normalized_distance"],
            row.get("scoring_weight_min"),
            row.get("scoring_weight_max"),
        ]
        row["result_finite"] = all(
            value is not None and math.isfinite(float(value))
            for value in finite_result_values
        )
        row["passed"] = row["kind"] != "positive" or (row["result_finite"] and float(row["score"]) >= float(row["min_score"]))
        rows.append(row)
    positive_rows = [row for row in rows if row["kind"] == "positive"]
    diagnostic_rows = [row for row in rows if row["kind"] == "diagnostic"]
    weakest_positive = min(positive_rows, key=lambda row: float(row["score"])) if positive_rows else None
    weakest_diagnostic = min(diagnostic_rows, key=lambda row: float(row["score"])) if diagnostic_rows else None
    return {
        "word": word,
        "standard_json": str(standard_json),
        "standard_length": len(standard.features),
        "semantic_profile": _profile_summary(profile),
        "min_required_score": min_score,
        "gate_pass": all(bool(row["passed"]) for row in positive_rows),
        "weakest_positive_score": float(weakest_positive["score"]) if weakest_positive else None,
        "weakest_positive_variant": weakest_positive["variant"] if weakest_positive else "",
        "weakest_diagnostic_score": float(weakest_diagnostic["score"]) if weakest_diagnostic else None,
        "weakest_diagnostic_variant": weakest_diagnostic["variant"] if weakest_diagnostic else "",
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
        "uploaded_weight_min",
        "uploaded_weight_max",
        "scoring_weight_min",
        "scoring_weight_max",
        "uploaded_weight_nonfinite",
        "uploaded_weight_nonpositive",
        "uploaded_weight_extreme",
        "result_finite",
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
                        "gated": row.get("gated"),
                        "passed": row.get("passed"),
                        "score": row.get("score"),
                        "min_score": row.get("min_score"),
                        "dtw_distance": row.get("dtw_distance"),
                        "normalized_distance": row.get("normalized_distance"),
                        "uploaded_weight_min": row.get("uploaded_weight_min"),
                        "uploaded_weight_max": row.get("uploaded_weight_max"),
                        "scoring_weight_min": row.get("scoring_weight_min"),
                        "scoring_weight_max": row.get("scoring_weight_max"),
                        "uploaded_weight_nonfinite": row.get("uploaded_weight_nonfinite"),
                        "uploaded_weight_nonpositive": row.get("uploaded_weight_nonpositive"),
                        "uploaded_weight_extreme": row.get("uploaded_weight_extreme"),
                        "result_finite": row.get("result_finite"),
                        "capture_quality_status": quality.get("status"),
                        "capture_quality_reason": quality.get("reason"),
                        "semantic_floor_source": floor.get("source"),
                        "semantic_floor_reason": floor.get("reason"),
                        "rationale": row.get("rationale"),
                    }
                )


def _build_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# 花/跳 frame_weights 鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，只修改 query 的 `frame_weight`，不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：浏览器上传 motion 权重、轻微权重噪声/错位、宽泛前后段加权、无非均匀权重或异常上传权重被清洗后，`花/跳` 仍保持正常或边界以上得分；反向 motion 权重仅作为坏上传先验诊断。",
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
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向权重 | 诊断最低分 | 最弱诊断权重 | 门槛 |")
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
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | 上传权重范围 | 异常权重 | 评分权重范围 | 输出有限 | capture_quality | semantic_floor | 说明 |")
        lines.append("|---|---|---|---:|---|---|---|---|---|---|---|---|")
        for row in sorted(item["variants"], key=lambda x: (x["kind"], float(x["score"]))):
            quality = row.get("capture_quality") or {}
            floor = row.get("semantic_floor") or {}
            if row["kind"] == "positive":
                threshold = f">= {row.get('min_score')}"
                status = "PASS" if row["passed"] else "FAIL"
            else:
                threshold = "diagnostic"
                status = "DIAG"
            uploaded_range = f"{_fmt(row.get('uploaded_weight_min'))}-{_fmt(row.get('uploaded_weight_max'))}"
            scoring_range = f"{_fmt(row.get('scoring_weight_min'))}-{_fmt(row.get('scoring_weight_max'))}"
            anomaly = (
                f"nonfinite={row.get('uploaded_weight_nonfinite', 0)}, "
                f"nonpositive={row.get('uploaded_weight_nonpositive', 0)}, "
                f"extreme={row.get('uploaded_weight_extreme', 0)}"
            )
            lines.append(
                f"| {row['variant']} | {row['kind']} | {status} | {_fmt(row['score'])} | "
                f"{threshold} | {uploaded_range} | {anomaly} | {scoring_range} | "
                f"{'yes' if row.get('result_finite') else 'no'} | "
                f"{quality.get('status') or '-'} | {floor.get('source') or '-'} | {row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 正向变体覆盖真实网页 motion 权重、常见轻微错位/噪声和异常上传权重清洗。",
            "- `inverted_dynamic_diagnostic` 是坏上传先验诊断，不代表正常浏览器行为。",
            "- 该门是合成 frame_weights 压力测试，不能替代真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run frame_weights robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_frame_weight_robustness_gate_current"))
    parser.add_argument("--words", nargs="+", default=DEFAULT_WORDS)
    parser.add_argument("--feature-mode", choices=["auto", "landmark", "bbox"], default="auto")
    parser.add_argument("--min-score", type=float, default=70.0)
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
        )
        for word in args.words
    ]
    backend_status = _load_backend_status(args.backend_url, args.status_timeout_sec)
    passed = all(bool(item["gate_pass"]) for item in results)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "claim_policy": "synthetic frame_weights robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "min_score": args.min_score,
        "backend_status": backend_status,
        "passed": passed,
        "results": results,
    }

    json_path = output_dir / "flower_jump_frame_weight_robustness_gate.json"
    md_path = output_dir / "flower_jump_frame_weight_robustness_gate.md"
    csv_path = output_dir / "flower_jump_frame_weight_robustness_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳 frame_weights 鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳 frame_weights 鲁棒性报告：{md_path}")
    print(f"已生成花/跳 frame_weights 鲁棒性 CSV：{csv_path}")
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

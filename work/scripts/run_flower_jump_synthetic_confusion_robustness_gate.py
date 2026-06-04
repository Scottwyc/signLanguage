#!/usr/bin/env python3
"""Check cross-word separation on synthetic flower/jump robustness variants.

Saved web cross-confusion proves that existing browser samples score higher
against their target word than the other word. This gate covers the synthetic
robustness surface: representative positive perturbations that should remain
high for the target must still score clearly lower against the other template.

The script edits cached skeleton sequences in memory only. It does not call
/api/score, run Holistic, move marker, or restart 5080.
"""

from __future__ import annotations

import argparse
import csv
import json
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

from score_holistic_sequence_mvp import (
    DEFAULT_SEMANTIC_PROFILE_JSON,
    SequenceData,
    _clone_sequence,
    load_semantic_profile,
    load_sequence,
    run_pair,
)

from run_flower_jump_action_crop_robustness_gate import _crop_sequence
from run_flower_jump_framing_robustness_gate import COORD_GROUPS, _transform_geometry
from run_flower_jump_landmark_noise_robustness_gate import _mutate_hands
from run_flower_jump_mirror_robustness_gate import _transform_sequence as _mirror_transform_sequence
from run_flower_jump_temporal_padding_robustness_gate import _pad_sequence, _repeat_each


REPO_ROOT = Path("/data/WYC/signLanguage")
DEFAULT_TEMPLATE_ROOT = REPO_ROOT / "work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results"
DEFAULT_OUTPUT_BASE = REPO_ROOT / "work/generated/scoring_mvp_run3"
DEFAULT_BACKEND_URL = "http://127.0.0.1:5080"
DEFAULT_WORDS = ["花", "跳"]


QueryFactory = Callable[[SequenceData, Any], SequenceData]


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


def _score_band(score: Optional[float]) -> str:
    if score is None:
        return "error"
    if score >= 75.0:
        return "normal_like"
    if score >= 60.0:
        return "borderline"
    return "low"


def _spec(
    variant: str,
    family: str,
    query: QueryFactory,
    rationale: str,
    *,
    min_target_score: Optional[float] = None,
    max_cross_score: Optional[float] = None,
    min_margin: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "family": family,
        "query": query,
        "rationale": rationale,
        "min_target_score": min_target_score,
        "max_cross_score": max_cross_score,
        "min_margin": min_margin,
    }


def _variant_specs(args: argparse.Namespace) -> List[Dict[str, Any]]:
    min_target = float(args.min_target_score)
    max_cross = float(args.max_cross_score)
    min_margin = float(args.min_margin)
    return [
        _spec(
            "self_recomputed",
            "baseline",
            lambda seq, profile: _clone_sequence(seq, "self_recomputed", seq.features),
            "同一模板序列作为基线，目标高分且错词低分。",
            min_target_score=95.0,
            max_cross_score=max_cross,
            min_margin=min_margin,
        ),
        _spec(
            "framing_shift_zoom_out",
            "framing",
            lambda seq, profile: _transform_geometry(
                seq,
                "framing_shift_zoom_out",
                groups=COORD_GROUPS,
                scale=0.88,
                dx=-0.25,
                dy=0.20,
            ),
            "代表性取景偏移/略远扰动。",
            min_target_score=min_target,
            max_cross_score=max_cross,
            min_margin=min_margin,
        ),
        _spec(
            "global_rotate_8deg",
            "framing",
            lambda seq, profile: _transform_geometry(seq, "global_rotate_8deg", groups=COORD_GROUPS, rotate_deg=8.0),
            "轻微摄像头或身体倾斜。",
            min_target_score=min_target,
            max_cross_score=max_cross,
            min_margin=min_margin,
        ),
        _spec(
            "mirror_x",
            "mirror",
            lambda seq, profile: _mirror_transform_sequence(seq, "mirror_x", mirror_x=True, swap_labels=False, profile=profile),
            "浏览器镜像/前置摄像头预览方向扰动。",
            min_target_score=min_target,
            max_cross_score=max_cross,
            min_margin=min_margin,
        ),
        _spec(
            "hand_noise_0.010_seed1",
            "landmark_noise",
            lambda seq, profile: _mutate_hands(seq, "hand_noise_0.010_seed1", seed=1, noise_sigma=0.010),
            "小幅连续手部 landmark 抖动。",
            min_target_score=min_target,
            max_cross_score=max_cross,
            min_margin=min_margin,
        ),
        _spec(
            "hand_frame_dropout_0.03_seed1",
            "landmark_noise",
            lambda seq, profile: _mutate_hands(seq, "hand_frame_dropout_0.03_seed1", seed=1, frame_dropout_rate=0.03),
            "少量整帧手部检出不稳定。",
            min_target_score=min_target,
            max_cross_score=max_cross,
            min_margin=min_margin,
        ),
        _spec(
            "prefix_hold_25pct",
            "temporal_padding",
            lambda seq, profile: _pad_sequence(seq, "prefix_hold_25pct", prefix_ratio=0.25),
            "动作前准备静止帧。",
            min_target_score=min_target,
            max_cross_score=max_cross,
            min_margin=min_margin,
        ),
        _spec(
            "slow_repeat_each_2x",
            "temporal_padding",
            lambda seq, profile: _repeat_each(seq, "slow_repeat_each_2x", repeats=2),
            "动作整体变慢但相位完整。",
            min_target_score=min_target,
            max_cross_score=max_cross,
            min_margin=min_margin,
        ),
        _spec(
            "trim_start_15pct",
            "action_crop",
            lambda seq, profile: _crop_sequence(seq, "trim_start_15pct", 0.15, 1.0),
            "录制略晚开始，核心动作仍在。",
            min_target_score=min_target,
            max_cross_score=max_cross,
            min_margin=min_margin,
        ),
        _spec(
            "center_70pct",
            "action_crop",
            lambda seq, profile: _crop_sequence(seq, "center_70pct", 0.15, 0.85),
            "保留中间动作窗口，模拟起止边界不精确。",
            min_target_score=min_target,
            max_cross_score=max_cross,
            min_margin=min_margin,
        ),
    ]


def _confusion_reason(row: Dict[str, Any]) -> str:
    if row.get("error"):
        return "error"
    if float(row["target_score"]) < float(row["min_target_score"]):
        return "target_score_low"
    cross_high = float(row["cross_score"]) > float(row["max_cross_score"])
    margin_low = float(row["margin"]) < float(row["min_margin"])
    if cross_high and margin_low:
        return "cross_score_high_and_margin_low"
    if cross_high:
        return "cross_score_high"
    if margin_low:
        return "margin_low"
    return "passed"


def _score_row(
    word: str,
    other_word: str,
    variant: Dict[str, Any],
    standard: SequenceData,
    target_profile: Any,
    other_standard: SequenceData,
    other_profile: Any,
) -> Dict[str, Any]:
    base = {
        "word": word,
        "other_word": other_word,
        "variant": variant["variant"],
        "family": variant["family"],
        "rationale": variant["rationale"],
        "min_target_score": float(variant["min_target_score"]),
        "max_cross_score": float(variant["max_cross_score"]),
        "min_margin": float(variant["min_margin"]),
        "error": "",
    }
    try:
        query = variant["query"](standard, target_profile)
        target_result = run_pair(standard, query, semantic_profile=target_profile, enable_cross_check=False)
        cross_result = run_pair(other_standard, query, semantic_profile=other_profile, enable_cross_check=False)
        target_quality = (target_result.get("score_scale") or {}).get("capture_quality") or {}
        cross_quality = (cross_result.get("score_scale") or {}).get("capture_quality") or {}
        target_score = float(target_result["prototype_score"])
        cross_score = float(cross_result["prototype_score"])
        row = {
            **base,
            "target_score": target_score,
            "cross_score": cross_score,
            "margin": target_score - cross_score,
            "target_band": _score_band(target_score),
            "cross_band": _score_band(cross_score),
            "query_length": len(query.features),
            "target_capture_quality_status": target_quality.get("status"),
            "target_capture_quality_reason": target_quality.get("reason"),
            "cross_capture_quality_status": cross_quality.get("status"),
            "cross_capture_quality_reason": cross_quality.get("reason"),
            "target_score_scale_reason": (target_result.get("score_scale") or {}).get("reason"),
            "cross_score_scale_reason": (cross_result.get("score_scale") or {}).get("reason"),
            "target_semantic_floor_source": ((target_result.get("score_scale") or {}).get("semantic_floor") or {}).get("source"),
            "cross_semantic_floor_source": ((cross_result.get("score_scale") or {}).get("semantic_floor") or {}).get("source"),
        }
        row["passed"] = _confusion_reason(row) == "passed"
        row["reason"] = _confusion_reason(row)
        return row
    except Exception as exc:  # noqa: BLE001 - serialize any variant failure into the gate report.
        row = {
            **base,
            "target_score": None,
            "cross_score": None,
            "margin": None,
            "target_band": "error",
            "cross_band": "error",
            "query_length": None,
            "target_capture_quality_status": "",
            "target_capture_quality_reason": "",
            "cross_capture_quality_status": "",
            "cross_capture_quality_reason": "",
            "target_score_scale_reason": "",
            "cross_score_scale_reason": "",
            "target_semantic_floor_source": "",
            "cross_semantic_floor_source": "",
            "passed": False,
            "reason": "error",
            "error": str(exc),
        }
        return row


def _mean(values: Sequence[Any]) -> Optional[float]:
    clean: List[float] = []
    for value in values:
        try:
            clean.append(float(value))
        except (TypeError, ValueError):
            continue
    return sum(clean) / len(clean) if clean else None


def _summarize_word(word: str, rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    items = [row for row in rows if row.get("word") == word]
    failing = [row for row in items if not row.get("passed")]
    return {
        "word": word,
        "samples": len(items),
        "pass": sum(1 for row in items if row.get("passed")),
        "fail": len(failing),
        "target_score_min": min((float(row["target_score"]) for row in items if row.get("target_score") is not None), default=None),
        "target_score_mean": _mean([row.get("target_score") for row in items]),
        "cross_score_max": max((float(row["cross_score"]) for row in items if row.get("cross_score") is not None), default=None),
        "cross_score_mean": _mean([row.get("cross_score") for row in items]),
        "margin_min": min((float(row["margin"]) for row in items if row.get("margin") is not None), default=None),
        "margin_mean": _mean([row.get("margin") for row in items]),
        "weakest_variant": min(items, key=lambda row: float(row.get("margin") or 0.0)).get("variant") if items else "",
        "failure_reasons": {reason: sum(1 for row in failing if row.get("reason") == reason) for reason in sorted({row.get("reason") for row in failing})},
    }


def _build_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# 花/跳合成鲁棒变体交叉混淆门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，在骨架层生成代表性正向扰动；同一 query 先按目标词评分，再按另一个词模板评分；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：网页鲁棒性提高后，`花` 的正向扰动不应被 `跳` 高分接收，`跳` 的正向扰动也不应被 `花` 高分接收。",
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
    lines.append("| 目标词 | 状态 | cases | pass | fail | 目标最低 | 交叉最高 | margin 最低 | 最弱变体 |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---|")
    for item in payload["summary_by_word"]:
        lines.append(
            f"| {item['word']} | {'PASS' if item['fail'] == 0 else 'FAIL'} | {item['samples']} | {item['pass']} | {item['fail']} | "
            f"{_fmt(item['target_score_min'])} | {_fmt(item['cross_score_max'])} | {_fmt(item['margin_min'])} | {item.get('weakest_variant') or '-'} |"
        )
    lines.extend(["", "## 分项明细", ""])
    lines.append("| 目标词 | 交叉词 | family | variant | pass | 目标分 | 交叉分 | margin | 目标状态 | 交叉状态 | 原因 |")
    lines.append("|---|---|---|---|---|---:|---:|---:|---|---|---|")
    for row in sorted(payload["rows"], key=lambda item: (item["word"], float(item.get("margin") or -999.0))):
        lines.append(
            f"| {row.get('word')} | {row.get('other_word')} | {row.get('family')} | {row.get('variant')} | "
            f"{'PASS' if row.get('passed') else 'FAIL'} | {_fmt(row.get('target_score'))} | {_fmt(row.get('cross_score'))} | "
            f"{_fmt(row.get('margin'))} | {row.get('target_capture_quality_status') or '-'} | "
            f"{row.get('cross_capture_quality_status') or '-'} | {row.get('reason')} |"
        )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 该门只证明合成正向扰动仍有跨词区分度，不能替代 marker 后真实网页摄像头样本。",
            "- 如果该门失败，不应直接抬高鲁棒性 floor；应先检查是哪类扰动导致错词模板高分。",
        ]
    )
    return "\n".join(lines) + "\n"


def _write_rows_csv(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run_gate(args: argparse.Namespace) -> Dict[str, Any]:
    template_root = Path(args.template_root)
    semantic_profile_json = Path(args.semantic_profile_json)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    words = [str(word) for word in args.words]
    if len(words) != 2:
        raise ValueError("synthetic confusion gate currently requires exactly two words")

    standards: Dict[str, SequenceData] = {}
    profiles: Dict[str, Any] = {}
    for word in words:
        standards[word] = load_sequence(_template_json(template_root, word), args.feature_mode, force_bbox=False)
        profiles[word] = load_semantic_profile(word, semantic_profile_json)

    variants = _variant_specs(args)
    rows: List[Dict[str, Any]] = []
    for word in words:
        other_word = [item for item in words if item != word][0]
        for variant in variants:
            rows.append(
                _score_row(
                    word=word,
                    other_word=other_word,
                    variant=variant,
                    standard=standards[word],
                    target_profile=profiles[word],
                    other_standard=standards[other_word],
                    other_profile=profiles[other_word],
                )
            )

    summary_by_word = [_summarize_word(word, rows) for word in words]
    backend_status = _load_backend_status(args.backend_url, args.status_timeout_sec)
    passed = all(bool(row.get("passed")) for row in rows)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "claim_policy": "synthetic robustness cross-confusion sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "words": words,
        "min_target_score": args.min_target_score,
        "max_cross_score": args.max_cross_score,
        "min_margin": args.min_margin,
        "backend_status": backend_status,
        "passed": passed,
        "summary_by_word": summary_by_word,
        "rows": rows,
    }
    json_path = output_dir / "flower_jump_synthetic_confusion_robustness_gate.json"
    md_path = output_dir / "flower_jump_synthetic_confusion_robustness_gate.md"
    csv_path = output_dir / "flower_jump_synthetic_confusion_robustness_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, rows)
    payload["json_path"] = str(json_path)
    payload["md_path"] = str(md_path)
    payload["csv_path"] = str(csv_path)
    return payload


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run synthetic cross-confusion robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_synthetic_confusion_robustness_gate_current"))
    parser.add_argument("--words", nargs="+", default=DEFAULT_WORDS)
    parser.add_argument("--feature-mode", choices=["auto", "landmark", "bbox"], default="auto")
    parser.add_argument("--min-target-score", type=float, default=70.0)
    parser.add_argument("--max-cross-score", type=float, default=55.0)
    parser.add_argument("--min-margin", type=float, default=15.0)
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--status-timeout-sec", type=float, default=3.0)
    args = parser.parse_args(argv)

    payload = run_gate(args)
    print(f"已生成花/跳合成混淆鲁棒性 JSON：{payload['json_path']}")
    print(f"已生成花/跳合成混淆鲁棒性报告：{payload['md_path']}")
    print(f"已生成花/跳合成混淆鲁棒性 CSV：{payload['csv_path']}")
    print(f"综合状态：{'PASS' if payload['passed'] else 'FAIL'}")
    for item in payload["summary_by_word"]:
        print(
            f"- {item['word']}: {'PASS' if item['fail'] == 0 else 'FAIL'} "
            f"cases={item['samples']} target_min={_fmt(item['target_score_min'])} "
            f"cross_max={_fmt(item['cross_score_max'])} margin_min={_fmt(item['margin_min'])}"
        )
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

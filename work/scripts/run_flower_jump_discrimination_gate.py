#!/usr/bin/env python3
"""Run the offline discrimination gate for the current flower/jump scorer.

This is a cached-Holistic gate. It does not call /api/score and does not
restart the persistent Holistic backend. The purpose is to verify that the
current semantic floors which make web flower/jump samples score normally do
not also lift other demo actions or synthetic fake actions.
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

from score_holistic_sequence_mvp import (
    DEFAULT_SEMANTIC_PROFILE_JSON,
    _infer_word_from_source,
    _profile_summary,
    load_semantic_profile,
    load_sequence,
    run_discrimination_suite,
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


def _negative_specs(template_root: Path, target_word: str) -> List[str]:
    specs: List[str] = []
    for item in sorted(template_root.iterdir(), key=lambda p: p.name):
        if not item.is_dir() or item.name == target_word:
            continue
        candidate = item / f"{item.name}_holistic_results.json"
        if candidate.exists():
            specs.append(f"{item.name}={candidate}")
    return specs


def _fmt(value: Any, digits: int = 3) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "-"


def _case_sort_key(row: Dict[str, Any]) -> float:
    try:
        return float(row.get("prototype_score") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _run_one(
    word: str,
    template_root: Path,
    semantic_profile_json: Path,
    feature_mode: str,
    positive_threshold: float,
    negative_threshold: float,
) -> Dict[str, Any]:
    standard_json = _template_json(template_root, word)
    negative_jsons = _negative_specs(template_root, word)
    standard = load_sequence(standard_json, feature_mode, force_bbox=False)
    profile = load_semantic_profile(word or _infer_word_from_source(standard.source), semantic_profile_json)
    suite = run_discrimination_suite(
        standard=standard,
        negative_jsons=negative_jsons,
        feature_mode=feature_mode,
        force_bbox=standard.mode == "bbox",
        positive_threshold=positive_threshold,
        negative_threshold=negative_threshold,
        profile=profile,
    )
    negative_cases = [row for row in suite["cases"] if row.get("case_type") != "target_positive_variant"]
    positive_cases = [row for row in suite["cases"] if row.get("case_type") == "target_positive_variant"]
    top_negative = max(negative_cases, key=_case_sort_key) if negative_cases else None
    weakest_positive = min(positive_cases, key=_case_sort_key) if positive_cases else None
    return {
        "word": word,
        "standard_json": str(standard_json),
        "negative_jsons": negative_jsons,
        "feature_mode": standard.mode,
        "standard_length": len(standard.features),
        "semantic_profile": _profile_summary(profile),
        "suite": suite,
        "top_negative": top_negative,
        "weakest_positive": weakest_positive,
    }


def _write_cases_csv(path: Path, results: Sequence[Dict[str, Any]]) -> None:
    fields = [
        "target_word",
        "case_id",
        "case_type",
        "expected",
        "query_length",
        "prototype_score",
        "dtw_distance",
        "normalized_distance",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in results:
            for row in item["suite"]["cases"]:
                writer.writerow(
                    {
                        "target_word": item["word"],
                        "case_id": row.get("case_id"),
                        "case_type": row.get("case_type"),
                        "expected": row.get("expected"),
                        "query_length": row.get("query_length"),
                        "prototype_score": row.get("prototype_score"),
                        "dtw_distance": row.get("dtw_distance"),
                        "normalized_distance": row.get("normalized_distance"),
                    }
                )


def _build_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# 花/跳离线判别鲁棒性门")
    lines.append("")
    lines.append(f"- 生成时间：`{payload['generated_at']}`")
    lines.append(f"- 标准库：`{payload['template_root']}`")
    lines.append(f"- 语义 profile：`{payload['semantic_profile_json']}`")
    lines.append("- 口径：只读已缓存 Holistic JSON，不调用 `/api/score`，不重启 Holistic。")
    lines.append("- 目标：确认当前让 `花/跳` 网页样本得分正常的语义 floor 没有把其他 demo 或合成假动作误抬高。")
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
    lines.append(f"- 正例最低分门槛：`{payload['positive_threshold']}`")
    lines.append(f"- 负例最高分门槛：`{payload['negative_threshold']}`")
    lines.append(f"- margin 门槛：`{payload['required_margin']}`")
    lines.append("")
    lines.append("| 目标词 | 状态 | 正例最低 | 最弱正例 | 负例最高 | 最强负例 | margin |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for item in payload["results"]:
        suite = item["suite"]
        weak = item.get("weakest_positive") or {}
        top = item.get("top_negative") or {}
        lines.append(
            f"| {item['word']} | {'PASS' if suite.get('gate_pass') else 'FAIL'} | "
            f"{_fmt(suite.get('min_positive_score'))} | {weak.get('case_id') or '-'} | "
            f"{_fmt(suite.get('max_negative_score'))} | {top.get('case_id') or '-'} | "
            f"{_fmt(suite.get('margin'))} |"
        )
    lines.append("")
    lines.append("## 分项明细")
    for item in payload["results"]:
        suite = item["suite"]
        lines.append("")
        lines.append(f"### {item['word']}")
        lines.append("")
        lines.append(f"- 标准序列：`{item['standard_json']}`")
        lines.append(f"- 标准帧数：`{item['standard_length']}`")
        lines.append(f"- gate：`{'PASS' if suite.get('gate_pass') else 'FAIL'}`")
        lines.append(f"- 正例最低分：`{_fmt(suite.get('min_positive_score'))}`")
        lines.append(f"- 负例最高分：`{_fmt(suite.get('max_negative_score'))}`")
        lines.append(f"- margin：`{_fmt(suite.get('margin'))}`")
        lines.append("")
        lines.append("| case | 类型 | 期望 | 分数 | query 帧数 |")
        lines.append("|---|---|---|---:|---:|")
        for row in sorted(suite.get("cases") or [], key=_case_sort_key, reverse=True):
            lines.append(
                f"| {row.get('case_id')} | {row.get('case_type')} | {row.get('expected')} | "
                f"{_fmt(row.get('prototype_score'))} | {row.get('query_length')} |"
            )
    lines.append("")
    lines.append("## 使用说明")
    lines.append("")
    lines.append("- 若该门失败，优先查看“最强负例”是否来自其他 demo，尤其是 `汽车/谗（羡慕）` 这类局部动作可能与 `跳` 的局部上升段相似的样本。")
    lines.append("- 该门是 demo-only 工程 sanity gate，不能替代真实用户网页摄像头样本和人工标签校准。")
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run the flower/jump offline discrimination gate.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_discrimination_gate_current"))
    parser.add_argument("--words", nargs="+", default=DEFAULT_WORDS)
    parser.add_argument("--feature-mode", choices=["auto", "landmark", "bbox"], default="auto")
    parser.add_argument("--positive-threshold", type=float, default=75.0)
    parser.add_argument("--negative-threshold", type=float, default=50.0)
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--status-timeout-sec", type=float, default=3.0)
    args = parser.parse_args(argv)

    template_root = Path(args.template_root)
    semantic_profile_json = Path(args.semantic_profile_json)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = [
        _run_one(
            word=word,
            template_root=template_root,
            semantic_profile_json=semantic_profile_json,
            feature_mode=args.feature_mode,
            positive_threshold=args.positive_threshold,
            negative_threshold=args.negative_threshold,
        )
        for word in args.words
    ]
    backend_status = _load_backend_status(args.backend_url, args.status_timeout_sec)
    passed = all(bool(item["suite"].get("gate_pass")) for item in results)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "claim_policy": "offline demo-only discrimination sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "positive_threshold": args.positive_threshold,
        "negative_threshold": args.negative_threshold,
        "required_margin": 15.0,
        "backend_status": backend_status,
        "passed": passed,
        "results": results,
    }

    json_path = output_dir / "flower_jump_discrimination_gate.json"
    md_path = output_dir / "flower_jump_discrimination_gate.md"
    csv_path = output_dir / "flower_jump_discrimination_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_cases_csv(csv_path, results)

    print(f"已生成花/跳离线判别 JSON：{json_path}")
    print(f"已生成花/跳离线判别报告：{md_path}")
    print(f"已生成花/跳离线判别 CSV：{csv_path}")
    print(f"综合状态：{'PASS' if passed else 'FAIL'}")
    for item in results:
        suite = item["suite"]
        top = item.get("top_negative") or {}
        print(
            f"- {item['word']}: {'PASS' if suite.get('gate_pass') else 'FAIL'} "
            f"min_pos={_fmt(suite.get('min_positive_score'))} "
            f"max_neg={_fmt(suite.get('max_negative_score'))} "
            f"margin={_fmt(suite.get('margin'))} "
            f"top_neg={top.get('case_id') or '-'}"
        )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

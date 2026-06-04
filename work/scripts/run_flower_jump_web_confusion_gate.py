#!/usr/bin/env python3
"""Check flower/jump cross-word confusion on saved web samples.

This gate reuses saved web Holistic JSON and the current dense template root.
It does not call /api/score and does not restart the persistent Holistic
backend. For accepted target samples, it verifies that scoring the same query
against the other word stays clearly lower.
"""

from __future__ import annotations

import argparse
import csv
import json
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from score_holistic_sequence_mvp import (
    DEFAULT_SEMANTIC_PROFILE_JSON,
    load_semantic_profile,
    load_sequence,
    run_pair,
)


REPO_ROOT = Path("/data/WYC/signLanguage")
DEFAULT_WEB_ROOT = REPO_ROOT / "work/generated/web_scoring_mvp"
DEFAULT_TEMPLATE_ROOT = REPO_ROOT / "work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results"
DEFAULT_OUTPUT_BASE = REPO_ROOT / "work/generated/scoring_mvp_run3"
DEFAULT_BACKEND_URL = "http://127.0.0.1:5080"
DEFAULT_WORDS = ["花", "跳"]
RELIABLE_CAPTURE_STATUSES = {"score_valid", "semantic_mismatch"}


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_backend_status(backend_url: str, timeout_sec: float) -> Dict[str, Any]:
    url = backend_url.rstrip("/") + "/api/status"
    try:
        with urllib.request.urlopen(url, timeout=timeout_sec) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return {"ok": True, "url": url, "payload": payload, "error": ""}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"ok": False, "url": url, "payload": {}, "error": str(exc)}


def _iter_result_paths(web_root: Path) -> List[Path]:
    return sorted(web_root.glob("web_*/scoring_result.json"), key=lambda path: path.parent.name)


def _filter_paths(
    paths: Iterable[Path],
    *,
    request_ids: Optional[Sequence[str]] = None,
    since_request_id: str = "",
    latest: int = 0,
) -> List[Path]:
    selected = sorted(paths, key=lambda path: path.parent.name)
    request_set = {str(item) for item in (request_ids or []) if str(item)}
    if request_set:
        selected = [path for path in selected if path.parent.name in request_set]
    if since_request_id:
        selected = [path for path in selected if path.parent.name > since_request_id]
    if latest > 0:
        selected = selected[-latest:]
    return selected


def _safe_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt(value: Any, digits: int = 3) -> str:
    number = _safe_float(value)
    if number is not None:
        return f"{number:.{digits}f}"
    return "-" if value is None or value == "" else str(value)


def _score_band(score: Optional[float]) -> str:
    if score is None:
        return "error"
    if score >= 75.0:
        return "normal_like"
    if score >= 60.0:
        return "borderline"
    return "low"


def _template_json(template_root: Path, word: str) -> Path:
    path = template_root / word / f"{word}_holistic_results.json"
    if not path.exists():
        raise FileNotFoundError(f"missing template json for {word}: {path}")
    return path


def _preload_templates(
    template_root: Path,
    semantic_profile_json: Path,
    words: Sequence[str],
) -> Dict[str, Dict[str, Any]]:
    templates: Dict[str, Dict[str, Any]] = {}
    for word in words:
        standard_json = _template_json(template_root, word)
        templates[word] = {
            "standard_json": standard_json,
            "sequence": load_sequence(standard_json, requested_mode="landmark"),
            "profile": load_semantic_profile(word, semantic_profile_json),
        }
    return templates


def _score_with_template(template: Dict[str, Any], query: Any) -> Dict[str, Any]:
    return run_pair(template["sequence"], query, semantic_profile=template["profile"], enable_cross_check=False)


def _eligible_for_confusion(row: Dict[str, Any], min_target_score: float) -> bool:
    if row.get("error"):
        return False
    status = str(row.get("target_capture_quality_status") or "")
    target_score = _safe_float(row.get("target_score"))
    return (
        status in RELIABLE_CAPTURE_STATUSES
        and target_score is not None
        and target_score >= min_target_score
    )


def analyze_one(
    result_path: Path,
    templates: Dict[str, Dict[str, Any]],
    words: Sequence[str],
    min_target_score: float,
    max_cross_score: float,
    min_margin: float,
) -> Dict[str, Any]:
    stored = _load_json(result_path)
    request_id = str(stored.get("request_id") or result_path.parent.name)
    target_word = str(stored.get("target_word") or "")
    other_words = [word for word in words if word != target_word]
    other_word = other_words[0] if other_words else ""
    base: Dict[str, Any] = {
        "request_id": request_id,
        "target_word": target_word,
        "other_word": other_word,
        "query_json": str(stored.get("query_json") or ""),
        "frame_count": stored.get("frame_count"),
        "timeline_frame_count": stored.get("timeline_frame_count"),
        "capture_fps": stored.get("capture_fps"),
        "error": "",
    }
    try:
        query_json = Path(stored.get("query_json") or "")
        query = load_sequence(query_json, requested_mode="landmark")
        target_result = _score_with_template(templates[target_word], query)
        other_result = _score_with_template(templates[other_word], query) if other_word else {}
        target_score = float(target_result["prototype_score"])
        other_score = float(other_result["prototype_score"]) if other_result else None
        target_quality = (target_result.get("score_scale") or {}).get("capture_quality") or {}
        other_quality = (other_result.get("score_scale") or {}).get("capture_quality") or {}
        margin = target_score - float(other_score) if other_score is not None else None
        row = {
            **base,
            "target_score": target_score,
            "other_score": other_score,
            "margin": margin,
            "target_band": _score_band(target_score),
            "other_band": _score_band(other_score),
            "target_capture_quality_status": target_quality.get("status"),
            "target_capture_quality_reason": target_quality.get("reason"),
            "other_capture_quality_status": other_quality.get("status"),
            "other_capture_quality_reason": other_quality.get("reason"),
            "target_score_scale_reason": (target_result.get("score_scale") or {}).get("reason"),
            "other_score_scale_reason": (other_result.get("score_scale") or {}).get("reason"),
            "target_semantic_floor_reason": ((target_result.get("score_scale") or {}).get("semantic_floor") or {}).get("reason"),
            "other_semantic_floor_reason": ((other_result.get("score_scale") or {}).get("semantic_floor") or {}).get("reason"),
            "target_core_presence": _safe_float((target_result.get("score_scale") or {}).get("semantic_core_query_hand_presence")),
            "other_core_presence": _safe_float((other_result.get("score_scale") or {}).get("semantic_core_query_hand_presence")),
        }
        eligible = _eligible_for_confusion(row, min_target_score=min_target_score)
        row["eligible_for_gate"] = eligible
        row["confusion_pass"] = (
            eligible
            and other_score is not None
            and other_score <= max_cross_score
            and margin is not None
            and margin >= min_margin
        )
        row["confusion_reason"] = _confusion_reason(row, max_cross_score=max_cross_score, min_margin=min_margin)
        return row
    except Exception as exc:
        return {
            **base,
            "target_score": None,
            "other_score": None,
            "margin": None,
            "target_band": "error",
            "other_band": "error",
            "target_capture_quality_status": "",
            "target_capture_quality_reason": "",
            "other_capture_quality_status": "",
            "other_capture_quality_reason": "",
            "target_score_scale_reason": "",
            "other_score_scale_reason": "",
            "target_semantic_floor_reason": "",
            "other_semantic_floor_reason": "",
            "target_core_presence": None,
            "other_core_presence": None,
            "eligible_for_gate": False,
            "confusion_pass": False,
            "confusion_reason": "error",
            "error": str(exc),
        }


def _confusion_reason(row: Dict[str, Any], max_cross_score: float, min_margin: float) -> str:
    if row.get("error"):
        return "error"
    if not row.get("eligible_for_gate"):
        return "not_eligible"
    other_score = _safe_float(row.get("other_score"))
    margin = _safe_float(row.get("margin"))
    if other_score is None or margin is None:
        return "missing_cross_score"
    if other_score > max_cross_score and margin < min_margin:
        return "cross_score_high_and_margin_low"
    if other_score > max_cross_score:
        return "cross_score_high"
    if margin < min_margin:
        return "margin_low"
    return "passed"


def summarize(rows: Sequence[Dict[str, Any]], words: Sequence[str]) -> Dict[str, Any]:
    by_word: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_word[str(row.get("target_word") or "unknown")].append(row)
    summary: Dict[str, Any] = {
        "samples": len(rows),
        "errors": sum(1 for row in rows if row.get("error")),
        "eligible": sum(1 for row in rows if row.get("eligible_for_gate")),
        "pass": sum(1 for row in rows if row.get("eligible_for_gate") and row.get("confusion_pass")),
        "fail": sum(1 for row in rows if row.get("eligible_for_gate") and not row.get("confusion_pass")),
        "confusion_reasons": dict(Counter(str(row.get("confusion_reason") or "unknown") for row in rows)),
        "by_word": {},
    }
    for word in words:
        items = by_word.get(word, [])
        eligible = [row for row in items if row.get("eligible_for_gate")]
        passing = [row for row in eligible if row.get("confusion_pass")]
        failing = [row for row in eligible if not row.get("confusion_pass")]
        summary["by_word"][word] = {
            "samples": len(items),
            "errors": sum(1 for row in items if row.get("error")),
            "eligible": len(eligible),
            "pass": len(passing),
            "fail": len(failing),
            "target_score_mean": _mean(row.get("target_score") for row in eligible),
            "other_score_mean": _mean(row.get("other_score") for row in eligible),
            "margin_min": _min(row.get("margin") for row in eligible),
            "margin_mean": _mean(row.get("margin") for row in eligible),
            "other_score_max": _max(row.get("other_score") for row in eligible),
            "reasons": dict(Counter(str(row.get("confusion_reason") or "unknown") for row in items)),
        }
    return summary


def _mean(values: Iterable[Any]) -> Optional[float]:
    clean = [_safe_float(value) for value in values]
    clean = [value for value in clean if value is not None]
    return sum(clean) / len(clean) if clean else None


def _min(values: Iterable[Any]) -> Optional[float]:
    clean = [_safe_float(value) for value in values]
    clean = [value for value in clean if value is not None]
    return min(clean) if clean else None


def _max(values: Iterable[Any]) -> Optional[float]:
    clean = [_safe_float(value) for value in values]
    clean = [value for value in clean if value is not None]
    return max(clean) if clean else None


def _build_gates(
    backend_status: Dict[str, Any],
    summary: Dict[str, Any],
    words: Sequence[str],
    min_eligible_per_word: int,
) -> List[Dict[str, Any]]:
    backend_payload = backend_status.get("payload") or {}
    worker_status = ((backend_payload.get("worker") or {}).get("status") or "") if backend_status.get("ok") else ""
    reload_error = ((backend_payload.get("scoring_module") or {}).get("last_reload_error")) if backend_status.get("ok") else None
    gates = [
        {
            "name": "backend_ready",
            "passed": bool(backend_status.get("ok")) and worker_status == "ready" and reload_error is None,
            "detail": f"worker={worker_status or '-'}, reload_error={reload_error or '-'}, error={backend_status.get('error') or '-'}",
        },
        {
            "name": "no_errors",
            "passed": int(summary.get("errors") or 0) == 0,
            "detail": f"errors={summary.get('errors')}, samples={summary.get('samples')}",
        },
        {
            "name": "all_eligible_pass",
            "passed": int(summary.get("eligible") or 0) > 0 and int(summary.get("fail") or 0) == 0,
            "detail": f"eligible={summary.get('eligible')}, pass={summary.get('pass')}, fail={summary.get('fail')}",
        },
    ]
    for word in words:
        item = (summary.get("by_word") or {}).get(word) or {}
        gates.append(
            {
                "name": f"eligible_{word}",
                "passed": int(item.get("eligible") or 0) >= min_eligible_per_word,
                "detail": f"eligible={item.get('eligible')}, min={min_eligible_per_word}, samples={item.get('samples')}",
            }
        )
        gates.append(
            {
                "name": f"confusion_pass_{word}",
                "passed": int(item.get("fail") or 0) == 0 and int(item.get("eligible") or 0) >= min_eligible_per_word,
                "detail": f"pass={item.get('pass')}, fail={item.get('fail')}, other_score_max={_fmt(item.get('other_score_max'))}, margin_min={_fmt(item.get('margin_min'))}",
            }
        )
    return gates


def _build_markdown(payload: Dict[str, Any]) -> str:
    summary = payload["summary"]
    lines: List[str] = []
    lines.append("# 花/跳网页样本交叉混淆门")
    lines.append("")
    lines.append(f"- 生成时间：`{payload['generated_at']}`")
    lines.append(f"- Web 样本根目录：`{payload['web_root']}`")
    lines.append(f"- 当前标准库：`{payload['template_root']}`")
    lines.append(f"- 语义 profile：`{payload['semantic_profile_json']}`")
    lines.append("- 口径：只读保存的网页 Holistic JSON；同一 query 分别按 `花` 和 `跳` 当前模板复算；不调用 `/api/score`，不重启 Holistic。")
    lines.append("- 适用范围：只把目标词自身 `score_valid/semantic_mismatch` 且目标分数 `>= min_target_score` 的样本纳入交叉混淆 gate；重采样本和低分语义失败样本不用于证明跨词区分度。")
    filters = payload.get("filters") or {}
    if any(filters.values()):
        lines.append(
            f"- 样本过滤：latest=`{filters.get('latest') or 0}`，"
            f"since_request_id=`{filters.get('since_request_id') or ''}`，"
            f"request_ids=`{', '.join(filters.get('request_ids') or []) or '-'}`"
        )
    lines.append("")
    backend = payload.get("backend_status") or {}
    if backend.get("ok"):
        data = backend.get("payload") or {}
        worker = data.get("worker") or {}
        scoring = data.get("scoring_module") or {}
        lines.append(
            f"- 5080 状态：worker=`{worker.get('status')}`，"
            f"worker_pid=`{((worker.get('process') or {}).get('pid'))}`，"
            f"reload_count=`{scoring.get('reload_count')}`，last_reload_error=`{scoring.get('last_reload_error')}`"
        )
    else:
        lines.append(f"- 5080 状态：读取失败 `{backend.get('error') or '-'}`")
    lines.append("")
    lines.append("## 结论")
    lines.append("")
    lines.append(f"- 综合状态：`{'PASS' if payload['passed'] else 'FAIL'}`")
    lines.append(f"- 目标最低分：`{payload['min_target_score']}`")
    lines.append(f"- 交叉最高分：`{payload['max_cross_score']}`")
    lines.append(f"- 目标-交叉最小 margin：`{payload['min_margin']}`")
    lines.append("")
    lines.append("| gate | 结果 | 说明 |")
    lines.append("|---|---|---|")
    for gate in payload["gates"]:
        lines.append(f"| {gate['name']} | {'PASS' if gate['passed'] else 'FAIL'} | {gate['detail']} |")
    lines.append("")
    lines.append("## 分词条")
    lines.append("")
    lines.append("| 词条 | 样本 | eligible | pass | fail | 目标均分 | 交叉最高 | margin 最低 | margin 均值 | 原因 |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    for word, item in (summary.get("by_word") or {}).items():
        lines.append(
            f"| {word} | {item.get('samples')} | {item.get('eligible')} | {item.get('pass')} | {item.get('fail')} | "
            f"{_fmt(item.get('target_score_mean'))} | {_fmt(item.get('other_score_max'))} | "
            f"{_fmt(item.get('margin_min'))} | {_fmt(item.get('margin_mean'))} | {item.get('reasons')} |"
        )
    lines.append("")
    failing = [row for row in payload["rows"] if row.get("eligible_for_gate") and not row.get("confusion_pass")]
    lines.append("## 失败样本")
    lines.append("")
    if not failing:
        lines.append("- 无 eligible 失败样本。")
    else:
        lines.append("| request | 目标 | 目标分 | 交叉词 | 交叉分 | margin | 原因 | 目标诊断 | 交叉诊断 |")
        lines.append("|---|---|---:|---|---:|---:|---|---|---|")
        for row in sorted(failing, key=lambda item: float(item.get("margin") or 0.0)):
            lines.append(
                f"| {row.get('request_id')} | {row.get('target_word')} | {_fmt(row.get('target_score'))} | "
                f"{row.get('other_word')} | {_fmt(row.get('other_score'))} | {_fmt(row.get('margin'))} | "
                f"{row.get('confusion_reason')} | {row.get('target_capture_quality_reason') or '-'} | "
                f"{row.get('other_capture_quality_reason') or '-'} |"
            )
    lines.append("")
    lines.append("## Eligible 明细")
    lines.append("")
    lines.append("| request | 目标 | 目标分 | 交叉词 | 交叉分 | margin | pass | 目标状态 | 目标原因 | 交叉原因 |")
    lines.append("|---|---|---:|---|---:|---:|---|---|---|---|")
    eligible_rows = [row for row in payload["rows"] if row.get("eligible_for_gate")]
    for row in sorted(eligible_rows, key=lambda item: (str(item.get("target_word") or ""), float(item.get("margin") or 0.0))):
        lines.append(
            f"| {row.get('request_id')} | {row.get('target_word')} | {_fmt(row.get('target_score'))} | "
            f"{row.get('other_word')} | {_fmt(row.get('other_score'))} | {_fmt(row.get('margin'))} | "
            f"{row.get('confusion_pass')} | {row.get('target_capture_quality_status') or '-'} | "
            f"{row.get('target_capture_quality_reason') or '-'} | {row.get('other_capture_quality_reason') or '-'} |"
        )
    lines.append("")
    return "\n".join(lines)


def _write_outputs(payload: Dict[str, Any], output_dir: Path) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "flower_jump_web_confusion_gate.json"
    md_path = output_dir / "flower_jump_web_confusion_gate.md"
    csv_path = output_dir / "flower_jump_web_confusion_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    fields = list(payload["rows"][0].keys()) if payload["rows"] else []
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(payload["rows"])
    payload["json_path"] = str(json_path)
    payload["md_path"] = str(md_path)
    payload["csv_path"] = str(csv_path)
    return payload


def _default_output_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return DEFAULT_OUTPUT_BASE / f"flower_jump_web_confusion_gate_{stamp}"


def run_gate(args: argparse.Namespace) -> Dict[str, Any]:
    web_root = Path(args.web_root)
    template_root = Path(args.template_root)
    semantic_profile_json = Path(args.semantic_profile_json)
    words = [str(word) for word in args.words]
    output_dir = Path(args.output_dir) if args.output_dir else _default_output_dir()
    backend_status = _load_backend_status(args.backend_url, args.status_timeout_sec)
    templates = _preload_templates(template_root, semantic_profile_json, words)

    paths: List[Path] = []
    word_set = set(words)
    for path in _iter_result_paths(web_root):
        stored = _load_json(path)
        if str(stored.get("target_word") or "") in word_set:
            paths.append(path)
    paths = _filter_paths(
        paths,
        request_ids=args.request_ids,
        since_request_id=args.since_request_id,
        latest=args.latest,
    )
    rows = [
        analyze_one(
            path,
            templates,
            words,
            min_target_score=args.min_target_score,
            max_cross_score=args.max_cross_score,
            min_margin=args.min_margin,
        )
        for path in paths
    ]
    summary = summarize(rows, words)
    gates = _build_gates(
        backend_status,
        summary,
        words,
        min_eligible_per_word=args.min_eligible_per_word,
    )
    payload: Dict[str, Any] = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "web_root": str(web_root),
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "words": words,
        "filters": {"latest": args.latest, "since_request_id": args.since_request_id, "request_ids": list(args.request_ids)},
        "min_target_score": args.min_target_score,
        "max_cross_score": args.max_cross_score,
        "min_margin": args.min_margin,
        "min_eligible_per_word": args.min_eligible_per_word,
        "backend_status": backend_status,
        "summary": summary,
        "gates": gates,
        "rows": rows,
        "passed": all(gate["passed"] for gate in gates),
    }
    return _write_outputs(payload, output_dir)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="运行花/跳保存网页样本交叉混淆门")
    parser.add_argument("--web-root", default=str(DEFAULT_WEB_ROOT))
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--status-timeout-sec", type=float, default=5.0)
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--words", nargs="*", default=list(DEFAULT_WORDS))
    parser.add_argument("--latest", type=int, default=0)
    parser.add_argument("--since-request-id", default="")
    parser.add_argument("--request-ids", nargs="*", default=[])
    parser.add_argument("--min-target-score", type=float, default=60.0)
    parser.add_argument("--max-cross-score", type=float, default=55.0)
    parser.add_argument("--min-margin", type=float, default=15.0)
    parser.add_argument("--min-eligible-per-word", type=int, default=1)
    args = parser.parse_args(argv)
    payload = run_gate(args)
    print(f"已生成花/跳网页交叉混淆 JSON：{payload['json_path']}")
    print(f"已生成花/跳网页交叉混淆报告：{payload['md_path']}")
    print(f"已生成花/跳网页交叉混淆 CSV：{payload['csv_path']}")
    print(f"综合状态：{'PASS' if payload['passed'] else 'FAIL'}")
    for gate in payload["gates"]:
        print(f"- {gate['name']}: {'PASS' if gate['passed'] else 'FAIL'} ({gate['detail']})")
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

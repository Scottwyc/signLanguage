#!/usr/bin/env python3
"""Run the current web-sample regression gate for flower/jump scoring.

This wrapper is intentionally Holistic-worker free by default. It reuses saved
web/API Holistic JSON, overrides historical standards with the active dense
template root, and summarizes whether the current scoring module still behaves
reasonably for the two heavily tested signs: ``花`` and ``跳``.
"""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

import analyze_web_scoring_diagnostics as diagnostics
import replay_web_scoring_samples as replay
from score_holistic_sequence_mvp import DEFAULT_SEMANTIC_PROFILE_JSON


REPO_ROOT = Path("/data/WYC/signLanguage")
DEFAULT_WEB_ROOT = REPO_ROOT / "work/generated/web_scoring_mvp"
DEFAULT_TEMPLATE_ROOT = REPO_ROOT / "work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results"
DEFAULT_OUTPUT_BASE = REPO_ROOT / "work/generated/scoring_mvp_run3"
DEFAULT_BACKEND_URL = "http://127.0.0.1:5080"
DEFAULT_WORDS = ["花", "跳"]
RELIABLE_CAPTURE_STATUSES = {"score_valid", "semantic_mismatch"}


def _load_backend_status(backend_url: str, timeout_sec: float) -> Dict[str, Any]:
    url = backend_url.rstrip("/") + "/api/status"
    try:
        with urllib.request.urlopen(url, timeout=timeout_sec) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return {"ok": True, "url": url, "payload": payload, "error": ""}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"ok": False, "url": url, "payload": {}, "error": str(exc)}


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
    if value is None or value == "":
        return "-"
    return str(value)


def _gate(name: str, passed: bool, detail: str) -> Dict[str, Any]:
    return {"name": name, "passed": bool(passed), "detail": detail}


def _effective_low_rows(rows: Iterable[Dict[str, Any]], word: str) -> List[Dict[str, Any]]:
    return [
        row
        for row in rows
        if row.get("target_word") == word
        and row.get("band") == "low"
        and str(row.get("capture_quality_status") or "") in RELIABLE_CAPTURE_STATUSES
    ]


def _word_effective(summary: Dict[str, Any], word: str) -> Dict[str, Any]:
    return (((summary.get("by_word") or {}).get(word) or {}).get("effective") or {})


def _build_gates(
    backend_status: Dict[str, Any],
    replay_payload: Dict[str, Any],
    diagnostics_payload: Dict[str, Any],
    target_words: Sequence[str],
    min_effective_rate: float,
    max_flower_effective_low: int,
    allowed_flower_low_diagnoses: Sequence[str],
) -> List[Dict[str, Any]]:
    gates: List[Dict[str, Any]] = []
    backend_payload = backend_status.get("payload") or {}
    worker_status = ((backend_payload.get("worker") or {}).get("status") or "") if backend_status.get("ok") else ""
    reload_error = ((backend_payload.get("scoring_module") or {}).get("last_reload_error")) if backend_status.get("ok") else None
    gates.append(
        _gate(
            "backend_ready",
            bool(backend_status.get("ok")) and worker_status == "ready" and reload_error is None,
            f"url={backend_status.get('url')}, worker={worker_status or '-'}, reload_error={reload_error or '-'}, error={backend_status.get('error') or '-'}",
        )
    )

    replay_summary = replay_payload["summary"]
    diagnostics_summary = diagnostics_payload["summary"]
    gates.append(
        _gate(
            "replay_no_errors",
            int(replay_summary.get("errors") or 0) == 0,
            f"samples={replay_summary.get('samples')}, errors={replay_summary.get('errors')}",
        )
    )
    gates.append(
        _gate(
            "diagnostics_no_errors",
            int(diagnostics_summary.get("errors") or 0) == 0,
            f"samples={diagnostics_summary.get('samples')}, errors={diagnostics_summary.get('errors')}",
        )
    )

    total_effective = diagnostics_summary.get("effective") or {}
    total_rate = _safe_float(total_effective.get("normal_or_borderline_rate"))
    gates.append(
        _gate(
            "effective_rate_total",
            total_rate is not None and total_rate >= min_effective_rate,
            f"rate={_fmt((total_rate or 0.0) * 100, 1)}%, threshold={min_effective_rate * 100:.1f}%",
        )
    )

    requested_words = [word for word in target_words if word]
    for word in requested_words:
        effective = _word_effective(diagnostics_summary, word)
        rate = _safe_float(effective.get("normal_or_borderline_rate"))
        gates.append(
            _gate(
                f"effective_rate_{word}",
                rate is not None and rate >= min_effective_rate,
                f"rate={_fmt((rate or 0.0) * 100, 1)}%, reliable={effective.get('reliable_samples')}, "
                f"normal_or_borderline={effective.get('normal_or_borderline')}, low={effective.get('low')}",
            )
        )

    if "跳" in requested_words:
        jump_effective_low = _effective_low_rows(diagnostics_payload["rows"], "跳")
        gates.append(
            _gate(
                "jump_effective_low_zero",
                len(jump_effective_low) == 0,
                f"effective_low={len(jump_effective_low)}",
            )
        )

    if "花" in requested_words:
        flower_effective_low = _effective_low_rows(diagnostics_payload["rows"], "花")
        flower_low_diagnoses = Counter(str(row.get("diagnosis") or "unknown") for row in flower_effective_low)
        allowed = set(allowed_flower_low_diagnoses)
        gates.append(
            _gate(
                "flower_effective_low_bounded",
                len(flower_effective_low) <= max_flower_effective_low,
                f"effective_low={len(flower_effective_low)}, max={max_flower_effective_low}, diagnoses={dict(flower_low_diagnoses)}",
            )
        )
        gates.append(
            _gate(
                "flower_effective_low_explained",
                all(str(row.get("diagnosis") or "") in allowed for row in flower_effective_low),
                f"allowed={sorted(allowed)}, observed={dict(flower_low_diagnoses)}",
            )
        )
    return gates


def _build_markdown(payload: Dict[str, Any]) -> str:
    replay_summary = payload["replay"]["summary"]
    diagnostics_summary = payload["diagnostics"]["summary"]
    gates = payload["gates"]
    backend = payload["backend_status"]
    lines: List[str] = []
    title_words = "/".join(payload.get("words") or DEFAULT_WORDS)
    lines.append(f"# {title_words}网页打分回归")
    lines.append("")
    lines.append(f"- 生成时间：`{payload['generated_at']}`")
    lines.append(f"- Web 样本根目录：`{payload['web_root']}`")
    lines.append(f"- 当前标准库：`{payload['template_root']}`")
    lines.append(f"- 语义 profile：`{payload['semantic_profile_json']}`")
    lines.append(f"- 目标词：`{', '.join(payload.get('words') or [])}`")
    filters = payload.get("filters") or {}
    if any(filters.values()):
        lines.append(
            f"- 样本过滤：latest=`{filters.get('latest') or 0}`，"
            f"latest_per_word=`{filters.get('latest_per_word') or 0}`，"
            f"since_request_id=`{filters.get('since_request_id') or ''}`，"
            f"request_ids=`{', '.join(filters.get('request_ids') or []) or '-'}`"
        )
    lines.append(f"- 后端状态接口：`{backend.get('url')}`")
    if backend.get("ok"):
        backend_payload = backend.get("payload") or {}
        worker = backend_payload.get("worker") or {}
        scoring_module = backend_payload.get("scoring_module") or {}
        lines.append(
            f"- 5080 状态：worker=`{worker.get('status')}`，worker_pid=`{((worker.get('process') or {}).get('pid'))}`，"
            f"reload_count=`{scoring_module.get('reload_count')}`，last_reload_error=`{scoring_module.get('last_reload_error')}`"
        )
    else:
        lines.append(f"- 5080 状态：读取失败 `{backend.get('error')}`")
    lines.append("- 口径：不重新运行 Holistic；query 使用已保存网页/API Holistic JSON，standard 使用当前标准库。")
    lines.append("")
    lines.append("## 结论")
    lines.append("")
    status = "PASS" if payload["passed"] else "FAIL"
    lines.append(f"- 回归状态：`{status}`")
    lines.append(f"- replay 报告：`{payload['replay']['md_path']}`")
    lines.append(f"- diagnostics 报告：`{payload['diagnostics']['md_path']}`")
    lines.append("")
    lines.append("| gate | 结果 | 说明 |")
    lines.append("|---|---|---|")
    for gate in gates:
        lines.append(f"| {gate['name']} | {'PASS' if gate['passed'] else 'FAIL'} | {gate['detail']} |")
    lines.append("")
    lines.append("## 网页回放")
    lines.append("")
    lines.append(
        f"- 样本数 `{replay_summary.get('samples')}`，错误 `{replay_summary.get('errors')}`，"
        f"正常 `{replay_summary.get('normal_like')}`，边界 `{replay_summary.get('borderline')}`，低分 `{replay_summary.get('low')}`。"
    )
    lines.append(f"- 旧均分 `{_fmt(replay_summary.get('old_score_mean'))}`，当前均分 `{_fmt(replay_summary.get('new_score_mean'))}`。")
    lines.append("")
    lines.append("| 词条 | 样本数 | 正常 | 边界 | 低分 | 当前均分 | 手部覆盖均值 |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for word, item in (replay_summary.get("by_word") or {}).items():
        lines.append(
            f"| {word} | {item.get('samples')} | {item.get('normal_like')} | {item.get('borderline')} | "
            f"{item.get('low')} | {_fmt(item.get('new_score_mean'))} | {_fmt(item.get('hand_presence_mean'))} |"
        )
    lines.append("")
    lines.append("## 目标词语义诊断")
    lines.append("")
    effective = diagnostics_summary.get("effective") or {}
    rate = _safe_float(effective.get("normal_or_borderline_rate"))
    lines.append(
        f"- 目标词样本 `{diagnostics_summary.get('samples')}`，错误 `{diagnostics_summary.get('errors')}`，"
        f"有效采集 `{effective.get('reliable_samples')}`，有效正常+边界 `{effective.get('normal_or_borderline')}`，"
        f"有效低分 `{effective.get('low')}`，有效正常+边界率 `{_fmt((rate or 0.0) * 100, 1)}%`。"
    )
    lines.append("")
    lines.append("| 词条 | 原始样本 | 建议重采 | 有效采集 | 有效正常+边界 | 有效低分 | 有效率 | 有效均分 | 处置 | 诊断 |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---|---|")
    for word, item in (diagnostics_summary.get("by_word") or {}).items():
        eff = item.get("effective") or {}
        word_rate = _safe_float(eff.get("normal_or_borderline_rate"))
        lines.append(
            f"| {word} | {item.get('samples')} | {eff.get('needs_recapture')} | {eff.get('reliable_samples')} | "
            f"{eff.get('normal_or_borderline')} | {eff.get('low')} | {_fmt((word_rate or 0.0) * 100, 1)}% | "
            f"{_fmt(eff.get('score_mean'))} | {item.get('triage_priority')} | {item.get('diagnoses')} |"
        )
    lines.append("")
    lines.append("## 有效低分样本")
    lines.append("")
    low_rows = [
        row
        for row in payload["diagnostics"]["rows"]
        if row.get("band") == "low" and str(row.get("capture_quality_status") or "") in RELIABLE_CAPTURE_STATUSES
    ]
    if not low_rows:
        lines.append("- 无有效低分样本。")
    else:
        lines.append("| request | 词条 | 分数 | 采集质量 | 处置 | 诊断 | floor 原因 | L/R 覆盖 | 花张开 | 建议 |")
        lines.append("|---|---|---:|---|---|---|---|---:|---:|---|")
        for row in sorted(low_rows, key=lambda item: (str(item.get("target_word") or ""), float(item.get("score") or 0.0))):
            lines.append(
                f"| {row.get('request_id')} | {row.get('target_word')} | {_fmt(row.get('score'))} | "
                f"{row.get('capture_quality_status')} | {row.get('triage_priority') or '-'} | "
                f"{row.get('diagnosis')} | {row.get('semantic_floor_reason') or '-'} | "
                f"{_fmt(row.get('left_hand_presence'))}/{_fmt(row.get('right_hand_presence'))} | "
                f"{_fmt(row.get('flower_opening_score'))} | {row.get('sample_advice') or '-'} |"
            )
    lines.append("")
    return "\n".join(lines)


def _default_output_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return DEFAULT_OUTPUT_BASE / f"web_regression_flower_jump_{stamp}"


def _select_latest_target_request_ids(
    web_root: Path,
    words: Sequence[str],
    latest_per_word: int,
    since_request_id: str = "",
) -> List[str]:
    if latest_per_word <= 0:
        return []
    word_set = set(words)
    by_word: Dict[str, List[Path]] = {word: [] for word in words}
    for path in diagnostics._iter_result_paths(web_root):
        if since_request_id and path.parent.name <= since_request_id:
            continue
        stored = diagnostics._load_json(path)
        target_word = str(stored.get("target_word") or "")
        if target_word in word_set:
            by_word.setdefault(target_word, []).append(path)

    selected: List[str] = []
    seen = set()
    for word in words:
        paths = sorted(by_word.get(word) or [], key=lambda item: item.parent.name)
        for path in paths[-latest_per_word:]:
            request_id = path.parent.name
            if request_id not in seen:
                selected.append(request_id)
                seen.add(request_id)
    return selected


def run_regression(args: argparse.Namespace) -> Dict[str, Any]:
    output_dir = Path(args.output_dir) if args.output_dir else _default_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    web_root = Path(args.web_root)
    semantic_profile_json = Path(args.semantic_profile_json)
    template_root = Path(args.template_root)

    backend_status = _load_backend_status(args.backend_url, args.status_timeout_sec)

    selected_request_ids = list(args.request_ids)
    if not selected_request_ids and args.latest_per_word > 0:
        selected_request_ids = _select_latest_target_request_ids(
            web_root,
            args.words,
            args.latest_per_word,
            since_request_id=args.since_request_id,
        )
    effective_latest = 0 if selected_request_ids else args.latest
    filters = {
        "latest": effective_latest,
        "latest_per_word": args.latest_per_word,
        "since_request_id": args.since_request_id,
        "request_ids": selected_request_ids,
    }
    replay_paths = replay.filter_result_paths(
        replay._iter_result_paths(web_root),
        request_ids=selected_request_ids,
        since_request_id=args.since_request_id,
        latest=effective_latest,
    )
    replay_rows = [
        replay.replay_one(path, semantic_profile_json, template_root=template_root)
        for path in replay_paths
    ]
    replay_payload = replay.write_outputs(
        replay_rows,
        output_dir / "active_template_replay",
        web_root,
        semantic_profile_json,
        template_root=template_root,
        filters=filters,
    )

    word_set = set(args.words)
    diagnostics_paths = []
    for path in diagnostics._iter_result_paths(web_root):
        stored = diagnostics._load_json(path)
        target_word = str(stored.get("target_word") or "")
        if target_word in word_set:
            diagnostics_paths.append(path)
    diagnostics_paths = diagnostics.filter_result_paths(
        diagnostics_paths,
        request_ids=selected_request_ids,
        since_request_id=args.since_request_id,
        latest=effective_latest,
    )
    diagnostics_rows = [
        diagnostics.analyze_one(path, semantic_profile_json, template_root=template_root)
        for path in diagnostics_paths
    ]
    diagnostics_payload = diagnostics.write_outputs(
        diagnostics_rows,
        output_dir / "flower_jump_diagnostics",
        web_root,
        semantic_profile_json,
        args.words,
        template_root=template_root,
        filters=filters,
    )

    gates = _build_gates(
        backend_status,
        replay_payload,
        diagnostics_payload,
        target_words=args.words,
        min_effective_rate=args.min_effective_rate,
        max_flower_effective_low=args.max_flower_effective_low,
        allowed_flower_low_diagnoses=args.allowed_flower_low_diagnosis,
    )
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "web_root": str(web_root),
        "semantic_profile_json": str(semantic_profile_json),
        "template_root": str(template_root),
        "words": list(args.words),
        "filters": filters,
        "backend_status": backend_status,
        "replay": {
            "summary": replay_payload["summary"],
            "json_path": replay_payload["json_path"],
            "md_path": replay_payload["md_path"],
            "csv_path": replay_payload["csv_path"],
        },
        "diagnostics": {
            "summary": diagnostics_payload["summary"],
            "rows": diagnostics_payload["rows"],
            "json_path": diagnostics_payload["json_path"],
            "md_path": diagnostics_payload["md_path"],
            "csv_path": diagnostics_payload["csv_path"],
        },
        "gates": gates,
        "passed": all(gate["passed"] for gate in gates),
    }
    json_path = output_dir / "flower_jump_web_regression.json"
    md_path = output_dir / "flower_jump_web_regression.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    payload["json_path"] = str(json_path)
    payload["md_path"] = str(md_path)
    return payload


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="运行花/跳网页打分当前模板口径回归")
    parser.add_argument("--web-root", default=str(DEFAULT_WEB_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--output-dir", default="", help="默认生成 date-stamped web_regression_flower_jump_* 目录")
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--status-timeout-sec", type=float, default=5.0)
    parser.add_argument("--words", nargs="*", default=list(DEFAULT_WORDS))
    parser.add_argument("--latest", type=int, default=0, help="只分析筛选后的最近 N 条样本；0 表示全量。")
    parser.add_argument(
        "--latest-per-word",
        type=int,
        default=0,
        help="每个目标词各取最近 N 条样本；适合网页现场快诊断。若指定 --request-ids，则忽略该参数。",
    )
    parser.add_argument("--since-request-id", default="", help="只分析 request_id 字典序大于该值的样本。")
    parser.add_argument("--request-ids", nargs="*", default=[], help="只分析指定 request_id。")
    parser.add_argument("--min-effective-rate", type=float, default=0.95)
    parser.add_argument("--max-flower-effective-low", type=int, default=5)
    parser.add_argument("--allowed-flower-low-diagnosis", nargs="*", default=["flower_opening_guard_failed"])
    args = parser.parse_args(argv)

    payload = run_regression(args)
    target_words = "/".join(payload.get("words") or DEFAULT_WORDS)
    print(f"已生成{target_words}网页回归 JSON：{payload['json_path']}")
    print(f"已生成{target_words}网页回归报告：{payload['md_path']}")
    print(f"回归状态：{'PASS' if payload['passed'] else 'FAIL'}")
    for gate in payload["gates"]:
        print(f"- {gate['name']}: {'PASS' if gate['passed'] else 'FAIL'} ({gate['detail']})")
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

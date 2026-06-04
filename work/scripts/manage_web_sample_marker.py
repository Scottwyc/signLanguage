#!/usr/bin/env python3
"""Track and diagnose newly saved web scoring samples.

Use this helper around real browser retests:

1. Run ``mark`` before the user starts a new test round.
2. After testing, run ``diagnose`` to rescore only new ``花/跳`` samples.

The script only reads saved ``scoring_result.json`` and Holistic JSON. It does
not call the browser, does not call ``/api/score``, and does not restart
Holistic.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence


REPO_ROOT = Path("/data/WYC/signLanguage")
DEFAULT_WEB_ROOT = REPO_ROOT / "work/generated/web_scoring_mvp"
DEFAULT_MARKER = REPO_ROOT / "work/generated/scoring_mvp_run3/web_sample_marker_current.json"
DEFAULT_OUTPUT_BASE = REPO_ROOT / "work/generated/scoring_mvp_run3"
DEFAULT_WORDS = ["花", "跳"]
REGRESSION_SCRIPT = REPO_ROOT / "work/scripts/run_flower_jump_web_regression.py"
CONFUSION_SCRIPT = REPO_ROOT / "work/scripts/run_flower_jump_web_confusion_gate.py"
VISUAL_SCRIPT = REPO_ROOT / "work/scripts/render_web_holistic_cache_visuals.py"


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_result_paths(web_root: Path) -> List[Path]:
    return sorted(web_root.glob("web_*/scoring_result.json"), key=lambda path: path.parent.name)


def _request_id(path: Path) -> str:
    return path.parent.name


def _target_word(path: Path) -> str:
    try:
        return str(_load_json(path).get("target_word") or "")
    except Exception:
        return ""


def _summarize_paths(paths: Sequence[Path]) -> Dict[str, Any]:
    words = Counter(_target_word(path) or "unknown" for path in paths)
    return {
        "count": len(paths),
        "first_request_id": _request_id(paths[0]) if paths else "",
        "last_request_id": _request_id(paths[-1]) if paths else "",
        "by_word": dict(sorted(words.items())),
    }


def _safe_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt_score(value: Any) -> str:
    number = _safe_float(value)
    return "-" if number is None else f"{number:.1f}"


def _load_semantic_sample_summaries(json_path: Path, request_ids: Sequence[str], limit: int = 8) -> List[Dict[str, Any]]:
    if not json_path.exists():
        return []
    try:
        payload = _load_json(json_path)
    except Exception:
        return []
    request_set = {str(item) for item in request_ids}
    rows = payload.get("rows") or []
    summaries: List[Dict[str, Any]] = []
    for row in rows:
        request_id = str(row.get("request_id") or "")
        if request_set and request_id not in request_set:
            continue
        summaries.append(
            {
                "request_id": request_id,
                "target_word": row.get("target_word"),
                "score": _safe_float(row.get("score")),
                "band": row.get("band"),
                "triage_priority": row.get("triage_priority"),
                "capture_quality_status": row.get("capture_quality_status"),
                "diagnosis": row.get("diagnosis"),
                "sample_advice": row.get("sample_advice"),
                "left_hand_presence": _safe_float(row.get("left_hand_presence")),
                "right_hand_presence": _safe_float(row.get("right_hand_presence")),
                "semantic_core_presence_full": _safe_float(row.get("semantic_core_presence_full")),
                "semantic_core_presence_window": _safe_float(row.get("semantic_core_presence_window")),
            }
        )
        if len(summaries) >= limit:
            break
    return summaries


def _load_confusion_sample_summaries(json_path: Path, request_ids: Sequence[str], limit: int = 8) -> List[Dict[str, Any]]:
    if not json_path.exists():
        return []
    try:
        payload = _load_json(json_path)
    except Exception:
        return []
    request_set = {str(item) for item in request_ids}
    rows = payload.get("rows") or []
    summaries: List[Dict[str, Any]] = []
    for row in rows:
        request_id = str(row.get("request_id") or "")
        if request_set and request_id not in request_set:
            continue
        summaries.append(
            {
                "request_id": request_id,
                "target_word": row.get("target_word"),
                "other_word": row.get("other_word"),
                "target_score": _safe_float(row.get("target_score")),
                "other_score": _safe_float(row.get("other_score")),
                "margin": _safe_float(row.get("margin")),
                "eligible_for_gate": bool(row.get("eligible_for_gate")),
                "confusion_pass": bool(row.get("confusion_pass")),
                "confusion_reason": row.get("confusion_reason"),
                "target_capture_quality_status": row.get("target_capture_quality_status"),
                "target_capture_quality_reason": row.get("target_capture_quality_reason"),
                "other_capture_quality_status": row.get("other_capture_quality_status"),
                "other_capture_quality_reason": row.get("other_capture_quality_reason"),
            }
        )
        if len(summaries) >= limit:
            break
    return summaries


def _count_by_key(rows: Sequence[Dict[str, Any]], key: str) -> Dict[str, int]:
    return dict(Counter(str(row.get(key) or "unknown") for row in rows))


def write_marker(web_root: Path, marker_path: Path) -> Dict[str, Any]:
    paths = _iter_result_paths(web_root)
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "web_root": str(web_root),
        "summary": _summarize_paths(paths),
        "last_request_id": _request_id(paths[-1]) if paths else "",
    }
    marker_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def read_marker(marker_path: Path) -> Dict[str, Any]:
    if not marker_path.exists():
        return {}
    return _load_json(marker_path)


def paths_after_marker(web_root: Path, marker: Dict[str, Any]) -> List[Path]:
    last_request_id = str(marker.get("last_request_id") or "")
    return [path for path in _iter_result_paths(web_root) if _request_id(path) > last_request_id]


def _default_output_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return DEFAULT_OUTPUT_BASE / f"web_new_samples_since_marker_{stamp}"


def _markdown_noop(payload: Dict[str, Any]) -> str:
    lines = [
        "# 新增网页样本诊断",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- marker：`{payload['marker_path']}`",
        f"- marker last_request_id：`{payload['marker_last_request_id'] or '-'}`",
        f"- Web 样本根目录：`{payload['web_root']}`",
        f"- 新增样本数：`{payload['new_summary']['count']}`",
        f"- 新增目标词：`{payload['new_summary']['by_word']}`",
        f"- 诊断词条：`{', '.join(payload['words'])}`",
        f"- 实际诊断词条：`{', '.join(payload.get('diagnosed_words') or []) or '-'}`",
        "",
        "## 结论",
        "",
    ]
    if payload["diagnosed_request_ids"]:
        lines.append(f"- 已诊断 request_id：`{', '.join(payload['diagnosed_request_ids'])}`")
        lines.append(f"- 回归报告：`{payload['regression_report']}`")
        if payload.get("semantic_diagnostics_report"):
            lines.append(f"- 语义诊断报告：`{payload['semantic_diagnostics_report']}`")
        if payload.get("confusion_report"):
            lines.append(f"- 交叉混淆报告：`{payload['confusion_report']}`")
        if payload.get("semantic_sample_summaries"):
            lines.extend(["", "## 样本建议", ""])
            lines.append("| request | 词条 | 分数 | 处置 | 采集质量 | 诊断 | 建议 |")
            lines.append("|---|---|---:|---|---|---|---|")
            for row in payload.get("semantic_sample_summaries") or []:
                lines.append(
                    f"| {row.get('request_id') or '-'} | {row.get('target_word') or '-'} | "
                    f"{_fmt_score(row.get('score'))} | {row.get('triage_priority') or '-'} | "
                    f"{row.get('capture_quality_status') or '-'} | {row.get('diagnosis') or '-'} | "
                    f"{row.get('sample_advice') or '-'} |"
                )
        if payload.get("confusion_sample_summaries"):
            lines.extend(["", "## 花/跳交叉混淆", ""])
            lines.append("| request | 目标 | 目标分 | 交叉词 | 交叉分 | margin | gate | 原因 |")
            lines.append("|---|---|---:|---|---:|---:|---|---|")
            for row in payload.get("confusion_sample_summaries") or []:
                gate = "PASS" if row.get("confusion_pass") else ("SKIP" if not row.get("eligible_for_gate") else "FAIL")
                lines.append(
                    f"| {row.get('request_id') or '-'} | {row.get('target_word') or '-'} | "
                    f"{_fmt_score(row.get('target_score'))} | {row.get('other_word') or '-'} | "
                    f"{_fmt_score(row.get('other_score'))} | {_fmt_score(row.get('margin'))} | "
                    f"{gate} | {row.get('confusion_reason') or '-'} |"
                )
        if payload.get("confusion_returncode") not in {None, 0}:
            lines.append(f"- 交叉混淆返回码：`{payload['confusion_returncode']}`")
        if payload.get("visual_report"):
            lines.append(f"- 骨架可视化报告：`{payload['visual_report']}`")
        if payload.get("visual_returncode") not in {None, 0}:
            lines.append(f"- 骨架可视化返回码：`{payload['visual_returncode']}`")
    else:
        lines.append("- 没有 marker 之后新增的目标词样本需要诊断。")
    lines.append("")
    return "\n".join(lines)


def write_status_report(payload: Dict[str, Any], output_dir: Path) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "new_web_samples_status.json"
    md_path = output_dir / "new_web_samples_status.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_markdown_noop(payload), encoding="utf-8")
    payload["json_path"] = str(json_path)
    payload["md_path"] = str(md_path)
    return payload


def diagnose_new(args: argparse.Namespace) -> Dict[str, Any]:
    web_root = Path(args.web_root)
    marker_path = Path(args.marker)
    output_dir = Path(args.output_dir) if args.output_dir else _default_output_dir()
    marker = read_marker(marker_path)
    if not marker:
        marker = write_marker(web_root, marker_path)

    new_paths = paths_after_marker(web_root, marker)
    words = [str(word) for word in args.words]
    word_set = set(words)
    target_paths = [path for path in new_paths if _target_word(path) in word_set]
    target_request_ids = [_request_id(path) for path in target_paths]
    diagnosed_words = [word for word in words if any(_target_word(path) == word for path in target_paths)]

    payload: Dict[str, Any] = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "web_root": str(web_root),
        "marker_path": str(marker_path),
        "marker_last_request_id": str(marker.get("last_request_id") or ""),
        "new_summary": _summarize_paths(new_paths),
        "target_summary": _summarize_paths(target_paths),
        "words": words,
        "diagnosed_words": diagnosed_words,
        "diagnosed_request_ids": target_request_ids,
        "regression_report": "",
        "semantic_diagnostics_report": "",
        "semantic_diagnostics_json": "",
        "semantic_diagnostics_csv": "",
        "semantic_sample_summaries": [],
        "semantic_triage_counts": {},
        "regression_returncode": None,
        "confusion_report": "",
        "confusion_json": "",
        "confusion_csv": "",
        "confusion_sample_summaries": [],
        "confusion_reason_counts": {},
        "confusion_returncode": None,
        "visual_report": "",
        "visual_returncode": None,
    }

    if target_request_ids:
        output_dir.mkdir(parents=True, exist_ok=True)
        cmd = [
            sys.executable,
            str(REGRESSION_SCRIPT),
            "--words",
            *diagnosed_words,
            "--request-ids",
            *target_request_ids,
            "--output-dir",
            str(output_dir / "flower_jump_regression"),
        ]
        completed = subprocess.run(cmd, cwd=str(REPO_ROOT), text=True, capture_output=True, check=False)
        payload["regression_returncode"] = completed.returncode
        payload["regression_stdout"] = completed.stdout
        payload["regression_stderr"] = completed.stderr
        payload["regression_report"] = str(output_dir / "flower_jump_regression/flower_jump_web_regression.md")
        payload["semantic_diagnostics_report"] = str(output_dir / "flower_jump_regression/flower_jump_diagnostics/web_semantic_diagnostics.md")
        payload["semantic_diagnostics_json"] = str(output_dir / "flower_jump_regression/flower_jump_diagnostics/web_semantic_diagnostics.json")
        payload["semantic_diagnostics_csv"] = str(output_dir / "flower_jump_regression/flower_jump_diagnostics/web_semantic_diagnostics.csv")
        semantic_json_path = Path(payload["semantic_diagnostics_json"])
        payload["semantic_sample_summaries"] = _load_semantic_sample_summaries(semantic_json_path, target_request_ids)
        payload["semantic_triage_counts"] = _count_by_key(payload["semantic_sample_summaries"], "triage_priority")
        if completed.returncode != 0:
            payload = write_status_report(payload, output_dir)
            raise SystemExit(completed.returncode)

        confusion_cmd = [
            sys.executable,
            str(CONFUSION_SCRIPT),
            "--request-ids",
            *target_request_ids,
            "--output-dir",
            str(output_dir / "flower_jump_confusion"),
            "--min-eligible-per-word",
            "0",
        ]
        confusion = subprocess.run(confusion_cmd, cwd=str(REPO_ROOT), text=True, capture_output=True, check=False)
        payload["confusion_returncode"] = confusion.returncode
        payload["confusion_stdout"] = confusion.stdout
        payload["confusion_stderr"] = confusion.stderr
        payload["confusion_report"] = str(output_dir / "flower_jump_confusion/flower_jump_web_confusion_gate.md")
        payload["confusion_json"] = str(output_dir / "flower_jump_confusion/flower_jump_web_confusion_gate.json")
        payload["confusion_csv"] = str(output_dir / "flower_jump_confusion/flower_jump_web_confusion_cases.csv")
        confusion_json_path = Path(payload["confusion_json"])
        payload["confusion_sample_summaries"] = _load_confusion_sample_summaries(confusion_json_path, target_request_ids)
        payload["confusion_reason_counts"] = _count_by_key(payload["confusion_sample_summaries"], "confusion_reason")
        if confusion.returncode != 0:
            payload = write_status_report(payload, output_dir)
            raise SystemExit(confusion.returncode)

        if not args.skip_visuals:
            visual_dir = output_dir / "holistic_visuals"
            visual_cmd = [
                sys.executable,
                str(VISUAL_SCRIPT),
                "--requests",
                *target_request_ids,
                "--output-dir",
                str(visual_dir),
                "--rescore-current",
            ]
            visual = subprocess.run(visual_cmd, cwd=str(REPO_ROOT), text=True, capture_output=True, check=False)
            payload["visual_returncode"] = visual.returncode
            payload["visual_stdout"] = visual.stdout
            payload["visual_stderr"] = visual.stderr
            payload["visual_report"] = str(visual_dir / "web_holistic_visual_recovery_summary.md")
            if visual.returncode != 0:
                payload = write_status_report(payload, output_dir)
                raise SystemExit(visual.returncode)

    payload = write_status_report(payload, output_dir)
    if args.update_marker:
        payload["updated_marker"] = write_marker(web_root, marker_path)
        payload["json_path"] = str(Path(payload["json_path"]))
        Path(payload["json_path"]).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def print_summary(payload: Dict[str, Any]) -> None:
    print(json.dumps({k: payload.get(k) for k in ["marker_last_request_id", "new_summary", "target_summary", "diagnosed_request_ids", "regression_report", "semantic_diagnostics_report", "confusion_report", "md_path"]}, ensure_ascii=False, indent=2))


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="记录并诊断网页端新增打分样本")
    parser.add_argument("--web-root", default=str(DEFAULT_WEB_ROOT))
    parser.add_argument("--marker", default=str(DEFAULT_MARKER))
    subparsers = parser.add_subparsers(dest="command", required=True)

    mark_parser = subparsers.add_parser("mark", help="把当前最后一个 web sample 记录为 marker")
    mark_parser.add_argument("--print-json", action="store_true")

    status_parser = subparsers.add_parser("status", help="查看 marker 之后新增样本概况")
    status_parser.add_argument("--words", nargs="*", default=list(DEFAULT_WORDS))

    diagnose_parser = subparsers.add_parser("diagnose", help="诊断 marker 之后新增的花/跳样本")
    diagnose_parser.add_argument("--words", nargs="*", default=list(DEFAULT_WORDS))
    diagnose_parser.add_argument("--output-dir", default="")
    diagnose_parser.add_argument("--update-marker", action="store_true", help="诊断成功后把 marker 更新到当前最后样本")
    diagnose_parser.add_argument("--skip-visuals", action="store_true", help="只跑评分诊断，不生成骨架可视化")

    args = parser.parse_args(argv)
    web_root = Path(args.web_root)
    marker_path = Path(args.marker)

    if args.command == "mark":
        payload = write_marker(web_root, marker_path)
        if args.print_json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"已记录 marker：{marker_path}")
            print(f"last_request_id={payload['last_request_id'] or '-'}")
            print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))
        return 0

    if args.command == "status":
        marker = read_marker(marker_path)
        if not marker:
            marker = write_marker(web_root, marker_path)
        new_paths = paths_after_marker(web_root, marker)
        word_set = set(str(word) for word in args.words)
        target_paths = [path for path in new_paths if _target_word(path) in word_set]
        payload = {
            "marker_last_request_id": str(marker.get("last_request_id") or ""),
            "new_summary": _summarize_paths(new_paths),
            "target_summary": _summarize_paths(target_paths),
            "diagnosed_request_ids": [_request_id(path) for path in target_paths],
        }
        print_summary(payload)
        return 0

    if args.command == "diagnose":
        payload = diagnose_new(args)
        print_summary(payload)
        return int(payload.get("regression_returncode") or 0)

    return 2


if __name__ == "__main__":
    raise SystemExit(main())

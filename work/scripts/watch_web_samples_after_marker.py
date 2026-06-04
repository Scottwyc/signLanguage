#!/usr/bin/env python3
"""Watch for new web scoring samples and run marker diagnostics.

This is a lightweight companion to ``manage_web_sample_marker.py``. It does not
call the browser, does not submit scoring requests, and does not restart
Holistic. It only watches the saved web sample directory and runs the existing
incremental diagnosis once new target-word samples appear after the marker.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Optional, Sequence

import manage_web_sample_marker as marker


REPO_ROOT = Path("/data/WYC/signLanguage")
DEFAULT_OUTPUT_BASE = REPO_ROOT / "work/generated/scoring_mvp_run3"
DEFAULT_LOG = REPO_ROOT / "work/logs/web_sample_marker_watch.log"
DEFAULT_STATUS_JSON = DEFAULT_OUTPUT_BASE / "web_sample_marker_watch_status.json"
DEFAULT_STATUS_MD = DEFAULT_OUTPUT_BASE / "web_sample_marker_watch_status.md"
DEFAULT_READINESS_OUTPUT_DIR = DEFAULT_OUTPUT_BASE / "flower_jump_goal_readiness_watch_current"
DEFAULT_STATIC_ARTIFACT_DIR = REPO_ROOT / "work/web/static/latest_watch"
DEFAULT_STATIC_ARTIFACT_URL = "/static/latest_watch"
DEFAULT_FRONTEND_CONTRACT_OUTPUT_DIR = DEFAULT_OUTPUT_BASE / "watch_status_frontend_contract_watch_current"


def _timestamp() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _print_event(event: str, payload: Optional[Dict[str, Any]] = None) -> None:
    record = {"time": _timestamp(), "event": event}
    if payload:
        record.update(payload)
    print(json.dumps(record, ensure_ascii=False), flush=True)


def _target_status(args: argparse.Namespace) -> Dict[str, Any]:
    web_root = Path(args.web_root)
    marker_path = Path(args.marker)
    current_marker = marker.read_marker(marker_path)
    if not current_marker:
        current_marker = marker.write_marker(web_root, marker_path)
    new_paths = marker.paths_after_marker(web_root, current_marker)
    word_set = set(str(word) for word in args.words)
    target_paths = [path for path in new_paths if marker._target_word(path) in word_set]
    return {
        "checked_at": _timestamp(),
        "marker_last_request_id": str(current_marker.get("last_request_id") or ""),
        "new_summary": marker._summarize_paths(new_paths),
        "target_summary": marker._summarize_paths(target_paths),
        "target_request_ids": [marker._request_id(path) for path in target_paths],
    }


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _resolve_artifact_path(value: Any) -> Optional[Path]:
    if not value:
        return None
    path = Path(str(value))
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path if path.exists() else None


def _copy_static_artifact(src: Path, root: Path, rel_path: str, label: str, kind: str, base_url: str) -> Dict[str, Any]:
    dest = root / rel_path
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    url = f"{base_url.rstrip('/')}/{rel_path.replace(os.sep, '/')}"
    return {
        "label": label,
        "kind": kind,
        "url": url,
        "source_path": str(src),
        "static_path": str(dest),
    }


def _write_artifact_index(root: Path, result: Dict[str, Any]) -> None:
    reports = result.get("reports") or []
    visuals = result.get("visuals") or []
    visual_rows = [item for item in visuals if item.get("kind") != "visual_summary"]
    grouped: Dict[str, Dict[str, Any]] = {}
    for item in visual_rows:
        request_id = str(item.get("request_id") or "unknown")
        group = grouped.setdefault(
            request_id,
            {
                "request_id": request_id,
                "target_word": item.get("target_word") or "",
                "items": [],
            },
        )
        group["items"].append(item)

    def esc(value: Any) -> str:
        return html.escape(str(value or ""), quote=True)

    lines = [
        "<!doctype html>",
        "<html lang=\"zh-CN\">",
        "<head>",
        "  <meta charset=\"utf-8\">",
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
        "  <title>最近网页样本自动诊断</title>",
        "  <style>",
        "    body { margin: 0; font-family: system-ui, -apple-system, Segoe UI, sans-serif; color: #18212f; background: #f6f8fb; }",
        "    main { max-width: 1180px; margin: 0 auto; padding: 20px; }",
        "    h1 { margin: 0 0 4px; font-size: 24px; }",
        "    h2 { margin: 22px 0 10px; font-size: 18px; }",
        "    p { margin: 6px 0; color: #526070; }",
        "    .links, .grid { display: grid; gap: 10px; }",
        "    .links { grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); }",
        "    .card { background: #fff; border: 1px solid #dbe2ea; border-radius: 6px; padding: 12px; }",
        "    a { color: #2563eb; text-decoration: underline; text-underline-offset: 2px; overflow-wrap: anywhere; }",
        "    .grid { grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); }",
        "    figure { margin: 0; background: #fff; border: 1px solid #dbe2ea; border-radius: 6px; padding: 10px; }",
        "    img { width: 100%; height: auto; display: block; border: 1px solid #edf1f5; background: #fff; }",
        "    figcaption { margin-top: 8px; font-size: 13px; color: #344256; overflow-wrap: anywhere; }",
        "    .muted { color: #697789; font-size: 13px; }",
        "  </style>",
        "</head>",
        "<body>",
        "<main>",
        "  <h1>最近网页样本自动诊断</h1>",
        f"  <p class=\"muted\">生成时间：{esc(result.get('generated_at'))}</p>",
        "  <h2>报告</h2>",
        "  <section class=\"links\">",
    ]
    if reports:
        for item in reports:
            lines.append(
                "    <div class=\"card\">"
                f"<strong>{esc(item.get('label'))}</strong><br>"
                f"<a href=\"{esc(item.get('url'))}\" target=\"_blank\" rel=\"noopener\">打开报告</a>"
                "</div>"
            )
    else:
        lines.append("    <div class=\"card muted\">暂无报告镜像。</div>")
    lines.extend(["  </section>", "  <h2>骨架可视化</h2>"])
    if grouped:
        for group in grouped.values():
            title = f"{group.get('target_word') or ''} {group.get('request_id')}".strip()
            lines.append(f"  <h3>{esc(title)}</h3>")
            lines.append("  <section class=\"grid\">")
            for item in group.get("items") or []:
                lines.append(
                    "    <figure>"
                    f"<a href=\"{esc(item.get('url'))}\" target=\"_blank\" rel=\"noopener\">"
                    f"<img src=\"{esc(item.get('url'))}\" alt=\"{esc(item.get('label'))}\">"
                    "</a>"
                    f"<figcaption>{esc(item.get('label'))}</figcaption>"
                    "</figure>"
                )
            lines.append("  </section>")
    else:
        lines.append("  <div class=\"card muted\">暂无骨架图镜像。</div>")
    lines.extend(["</main>", "</body>", "</html>", ""])
    (root / "index.html").write_text("\n".join(lines), encoding="utf-8")
    result["index_url"] = f"{str(result.get('base_url') or '').rstrip('/')}/index.html"


def _mirror_latest_artifacts(args: argparse.Namespace, diagnosis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not args.static_artifact_dir:
        return None

    root = Path(args.static_artifact_dir)
    if not root.is_absolute():
        root = REPO_ROOT / root
    root = root.resolve()
    static_root = (REPO_ROOT / "work/web/static").resolve()
    if not _is_relative_to(root, static_root):
        return {
            "error": "static_artifact_dir_outside_static_root",
            "static_artifact_dir": str(root),
            "static_root": str(static_root),
        }

    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    base_url = str(args.static_artifact_url or DEFAULT_STATIC_ARTIFACT_URL).rstrip("/")
    result: Dict[str, Any] = {
        "generated_at": _timestamp(),
        "base_url": base_url,
        "manifest_url": f"{base_url}/artifacts.json",
        "reports": [],
        "visuals": [],
        "errors": [],
    }

    report_specs = [
        ("状态报告", "status", diagnosis.get("md_path"), "reports/status.md"),
        ("网页回归", "regression", diagnosis.get("regression_report"), "reports/regression.md"),
        ("语义诊断", "semantic", diagnosis.get("semantic_diagnostics_report"), "reports/semantic.md"),
        ("交叉混淆", "confusion", diagnosis.get("confusion_report"), "reports/confusion.md"),
        ("骨架可视化", "visual", diagnosis.get("visual_report"), "reports/visual.md"),
    ]
    for label, kind, source, rel_path in report_specs:
        src = _resolve_artifact_path(source)
        if not src:
            continue
        try:
            result["reports"].append(_copy_static_artifact(src, root, rel_path, label, kind, base_url))
        except Exception as exc:  # pragma: no cover - diagnostics should not stop watcher.
            result["errors"].append({"source": str(src), "error": repr(exc)})

    visual_report = _resolve_artifact_path(diagnosis.get("visual_report"))
    visual_root = visual_report.parent if visual_report else None
    if visual_root and visual_root.exists():
        for summary_path in sorted(visual_root.glob("*/visual_summary.json")):
            try:
                summary = json.loads(summary_path.read_text(encoding="utf-8"))
            except Exception as exc:  # pragma: no cover - visual metadata is best-effort.
                result["errors"].append({"source": str(summary_path), "error": repr(exc)})
                continue
            request_id = str(summary.get("request_id") or summary_path.parent.name)
            word = str(summary.get("target_word") or "")
            try:
                result["visuals"].append(
                    _copy_static_artifact(
                        summary_path,
                        root,
                        f"visuals/{request_id}/visual_summary.json",
                        f"{word or request_id} 视觉摘要",
                        "visual_summary",
                        base_url,
                    )
                )
            except Exception as exc:  # pragma: no cover
                result["errors"].append({"source": str(summary_path), "error": repr(exc)})
            for side in ("query", "standard"):
                side_payload = summary.get(side) or {}
                side_label = "测试" if side == "query" else "标准"
                image_specs = [
                    ("骨架联系表", "skeleton_contact_sheet", side_payload.get("skeleton_contact_sheet_path")),
                    ("识别时间线", "presence_timeline", side_payload.get("presence_timeline")),
                    ("完整时间线", "timeline", side_payload.get("timeline_path")),
                ]
                for label_suffix, kind_suffix, source in image_specs:
                    src = _resolve_artifact_path(source)
                    if not src:
                        continue
                    rel = f"visuals/{request_id}/{side}_{kind_suffix}{src.suffix}"
                    try:
                        item = _copy_static_artifact(
                            src,
                            root,
                            rel,
                            f"{word or request_id} {side_label}{label_suffix}",
                            f"{side}_{kind_suffix}",
                            base_url,
                        )
                        item["request_id"] = request_id
                        item["target_word"] = word
                        result["visuals"].append(item)
                    except Exception as exc:  # pragma: no cover
                        result["errors"].append({"source": str(src), "error": repr(exc)})

    manifest_path = root / "artifacts.json"
    _write_artifact_index(root, result)
    manifest_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def _build_watch_payload(
    args: argparse.Namespace,
    status: Dict[str, Any],
    event: str,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "generated_at": _timestamp(),
        "event": event,
        "watcher_pid": os.getpid(),
        "web_root": args.web_root,
        "marker": args.marker,
        "words": list(args.words),
        "poll_sec": args.poll_sec,
        "update_marker": bool(args.update_marker),
        "status": status,
    }
    if extra:
        payload.update(extra)
    return payload


def _write_watch_status(
    args: argparse.Namespace,
    status: Dict[str, Any],
    event: str,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    status_json = Path(args.status_json) if args.status_json else None
    if not status_json:
        return
    payload = _build_watch_payload(args, status, event, extra)
    status_json.parent.mkdir(parents=True, exist_ok=True)
    status_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 网页样本自动诊断 Watcher 状态",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 当前事件：`{event}`",
        f"- watcher PID：`{payload['watcher_pid']}`",
        f"- Web 样本根目录：`{args.web_root}`",
        f"- marker：`{args.marker}`",
        f"- marker last_request_id：`{status.get('marker_last_request_id') or '-'}`",
        f"- 监听词条：`{', '.join(args.words)}`",
        f"- 轮询间隔：`{args.poll_sec}` 秒",
        f"- 新增样本：`{status.get('new_summary', {}).get('count', 0)}`，分布 `{status.get('new_summary', {}).get('by_word', {})}`",
        f"- 新增目标样本：`{status.get('target_summary', {}).get('count', 0)}`，request_id `{', '.join(status.get('target_request_ids') or []) or '-'}`",
    ]
    if payload.get("latest_diagnosis"):
        diagnosis = payload["latest_diagnosis"]
        lines.extend(
            [
                "",
                "## 最近诊断",
                "",
                f"- request_id：`{', '.join(diagnosis.get('diagnosed_request_ids') or []) or '-'}`",
                f"- 回归报告：`{diagnosis.get('regression_report') or '-'}`",
                f"- 语义诊断：`{diagnosis.get('semantic_diagnostics_report') or '-'}`",
                f"- 交叉混淆：`{diagnosis.get('confusion_report') or '-'}`",
                f"- 骨架可视化：`{diagnosis.get('visual_report') or '-'}`",
                f"- 状态报告：`{diagnosis.get('md_path') or '-'}`",
                f"- regression_returncode：`{diagnosis.get('regression_returncode')}`",
                f"- confusion_returncode：`{diagnosis.get('confusion_returncode')}`",
                f"- visual_returncode：`{diagnosis.get('visual_returncode')}`",
            ]
        )
        static_artifacts = diagnosis.get("static_artifacts") or {}
        if static_artifacts:
            reports = static_artifacts.get("reports") or []
            visuals = static_artifacts.get("visuals") or []
            lines.extend(
                [
                    "",
                    "## 浏览器可访问报告镜像",
                    "",
                    f"- manifest：`{static_artifacts.get('manifest_url') or '-'}`",
                    f"- 报告数：`{len(reports)}`，可视化文件数：`{len(visuals)}`",
                ]
            )
        if diagnosis.get("semantic_sample_summaries"):
            lines.extend(
                [
                    "",
                    "## 最新样本建议",
                    "",
                    "| request | 词条 | 分数 | 处置 | 采集质量 | 诊断 | 建议 |",
                    "|---|---|---:|---|---|---|---|",
                ]
            )
            for row in diagnosis.get("semantic_sample_summaries") or []:
                score = row.get("score")
                score_text = f"{float(score):.1f}" if isinstance(score, (int, float)) else "-"
                lines.append(
                    f"| {row.get('request_id') or '-'} | {row.get('target_word') or '-'} | {score_text} | "
                    f"{row.get('triage_priority') or '-'} | {row.get('capture_quality_status') or '-'} | "
                    f"{row.get('diagnosis') or '-'} | {row.get('sample_advice') or '-'} |"
                )
        if diagnosis.get("confusion_sample_summaries"):
            lines.extend(
                [
                    "",
                    "## 花/跳交叉混淆",
                    "",
                    "| request | 目标 | 目标分 | 交叉词 | 交叉分 | margin | gate | 原因 |",
                    "|---|---|---:|---|---:|---:|---|---|",
                ]
            )
            for row in diagnosis.get("confusion_sample_summaries") or []:
                score = row.get("target_score")
                other_score = row.get("other_score")
                margin = row.get("margin")
                score_text = f"{float(score):.1f}" if isinstance(score, (int, float)) else "-"
                other_text = f"{float(other_score):.1f}" if isinstance(other_score, (int, float)) else "-"
                margin_text = f"{float(margin):.1f}" if isinstance(margin, (int, float)) else "-"
                gate = "PASS" if row.get("confusion_pass") else ("SKIP" if not row.get("eligible_for_gate") else "FAIL")
                lines.append(
                    f"| {row.get('request_id') or '-'} | {row.get('target_word') or '-'} | {score_text} | "
                    f"{row.get('other_word') or '-'} | {other_text} | {margin_text} | "
                    f"{gate} | {row.get('confusion_reason') or '-'} |"
                )
    if payload.get("retry_suppressed"):
        lines.extend(
            [
                "",
                "## 重试节流",
                "",
                f"- request_id：`{', '.join(payload.get('retry_suppressed', {}).get('request_ids') or [])}`",
                f"- 下次最早重试：`{payload.get('retry_suppressed', {}).get('retry_after_sec')}` 秒后",
            ]
        )
    if payload.get("goal_readiness"):
        readiness = payload["goal_readiness"]
        missing_gates = readiness.get("missing_gates") or []
        readiness_summary = readiness.get("readiness_summary") or {}
        browser_evidence = readiness.get("browser_capture_evidence") or {}
        evidence_rows = browser_evidence.get("rows") or []
        evidence_state = "PASS" if browser_evidence.get("passed") else "MISSING"
        lines.extend(
            [
                "",
                "## 目标完成度",
                "",
                f"- 状态：`{readiness.get('status_label') or '-'}`",
                f"- 审计报告：`{readiness.get('md_path') or '-'}`",
                f"- 缺失证据：`{', '.join(missing_gates) if missing_gates else '-'}`",
                f"- 分层状态：运行态 `{'PASS' if readiness_summary.get('runtime_ready') else 'MISSING'}`；"
                f"算法质量 `{'PASS' if readiness_summary.get('algorithm_ready') else 'MISSING'}`；"
                f"真实复测 `{'PASS' if readiness_summary.get('real_sample_ready') else 'MISSING'}`",
                f"- 当前阻塞：`{readiness_summary.get('completion_blocker') or '-'}`",
                f"- 真实网页采集证据：`{evidence_state}`，样本数 `{len(evidence_rows)}`",
            ]
        )
        if evidence_rows:
            lines.extend(
                [
                    "",
                    "| request | 词条 | 帧数 | 时长 | 证据等级 | 证据 |",
                    "|---|---|---:|---:|---|---|",
                ]
            )
            for row in evidence_rows[:8]:
                duration = row.get("duration_sec")
                duration_text = f"{float(duration):.2f}" if isinstance(duration, (int, float)) else "-"
                lines.append(
                    f"| {row.get('request_id') or '-'} | {row.get('target_word') or '-'} | "
                    f"{row.get('frame_count') or '-'} | {duration_text} | "
                    f"{row.get('evidence_level') or '-'} | {row.get('reason') or '-'} |"
                )
        gates = readiness.get("gates") or []
        if gates:
            lines.append("- 证据门：")
            for gate in gates:
                state = "PASS" if gate.get("passed") else "MISSING"
                lines.append(f"  - `{gate.get('name')}`：`{state}`")
    if payload.get("frontend_contract_check"):
        contract = payload["frontend_contract_check"]
        lines.extend(
            [
                "",
                "## 前端契约检查",
                "",
                f"- 状态：`{contract.get('status') or '-'}`",
                f"- 报告：`{contract.get('md_path') or '-'}`",
                f"- failed_count：`{contract.get('failed_count')}`",
                f"- warning_count：`{contract.get('warning_count')}`",
                f"- artifact_url_failed_count：`{contract.get('artifact_url_failed_count')}`",
            ]
        )
    lines.append("")
    markdown_text = "\n".join(lines)

    if args.status_md:
        status_md = Path(args.status_md)
        status_md.parent.mkdir(parents=True, exist_ok=True)
        status_md.write_text(markdown_text, encoding="utf-8")

    if args.status_json_mirror:
        mirror_json = Path(args.status_json_mirror)
        mirror_json.parent.mkdir(parents=True, exist_ok=True)
        mirror_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.status_md_mirror:
        mirror_md = Path(args.status_md_mirror)
        mirror_md.parent.mkdir(parents=True, exist_ok=True)
        mirror_md.write_text(markdown_text, encoding="utf-8")


def _contract_watch_status_json_path(args: argparse.Namespace) -> Optional[Path]:
    candidate = Path(args.status_json_mirror) if args.status_json_mirror else Path(args.status_json)
    return candidate if candidate else None


def _run_frontend_contract_check(args: argparse.Namespace, event: str) -> Optional[Dict[str, Any]]:
    if args.skip_frontend_contract_check:
        return None
    if event not in {"diagnose_done", "diagnose_failed", "diagnose_exception"}:
        return None

    watch_status_json = _contract_watch_status_json_path(args)
    if not watch_status_json:
        return None
    output_dir = Path(args.frontend_contract_output_dir)
    cmd = [
        sys.executable,
        str(REPO_ROOT / "work/scripts/check_watch_status_frontend_contract.py"),
        "--watch-status-json",
        str(watch_status_json),
        "--base-url",
        args.frontend_contract_base_url,
        "--output-dir",
        str(output_dir),
        "--http-timeout-sec",
        str(args.frontend_contract_timeout_sec),
        "--max-artifact-checks",
        str(args.frontend_contract_max_artifact_checks),
        "--require-fresh",
        "--max-watch-age-sec",
        str(args.frontend_contract_max_watch_age_sec),
    ]
    completed = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    json_path = output_dir / "watch_status_frontend_contract.json"
    md_path = output_dir / "watch_status_frontend_contract.md"
    report: Dict[str, Any] = {}
    if json_path.exists():
        try:
            report = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - diagnostic guard
            report = {"read_error": repr(exc)}
    artifact_results = report.get("artifact_url_results") or []
    artifact_failed = [
        row for row in artifact_results
        if isinstance(row, dict) and not row.get("ok")
    ]
    result: Dict[str, Any] = {
        "generated_at": report.get("generated_at") or _timestamp(),
        "returncode": completed.returncode,
        "status": report.get("status") or ("PASS" if completed.returncode == 0 else "FAIL"),
        "json_path": str(json_path),
        "md_path": str(md_path),
        "watch_status_json": str(watch_status_json),
        "base_url": args.frontend_contract_base_url,
        "failed_count": report.get("failed_count"),
        "warning_count": report.get("warning_count"),
        "artifact_url_count": len(artifact_results),
        "artifact_url_failed_count": len(artifact_failed),
        "stdout": completed.stdout[-2000:],
        "stderr": completed.stderr[-2000:],
    }
    if not report and completed.returncode != 0:
        result["error"] = "frontend contract check did not produce JSON"
    return result


def _run_readiness_audit(args: argparse.Namespace, watch_status_json: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    if args.skip_readiness_audit:
        return None

    output_dir = Path(args.readiness_output_dir)
    cmd = [
        sys.executable,
        str(REPO_ROOT / "work/scripts/audit_flower_jump_goal_readiness.py"),
        "--output-dir",
        str(output_dir),
        "--watch-status-url",
        args.readiness_watch_status_url,
        "--status-timeout-sec",
        str(args.readiness_timeout_sec),
    ]
    if watch_status_json:
        cmd.extend(["--watch-status-json", str(watch_status_json)])
    if args.readiness_quality_gate_json:
        cmd.extend(["--quality-gate-json", args.readiness_quality_gate_json])

    completed = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    json_path = output_dir / "flower_jump_goal_readiness_audit.json"
    md_path = output_dir / "flower_jump_goal_readiness_audit.md"
    payload: Dict[str, Any] = {}
    if json_path.exists():
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - diagnostic guard
            payload = {"read_error": repr(exc)}
    gates = payload.get("gates") or []
    missing_gates = [str(gate.get("name")) for gate in gates if not gate.get("passed")]
    ready = bool(payload.get("ready_to_complete"))
    result: Dict[str, Any] = {
        "generated_at": payload.get("generated_at") or _timestamp(),
        "returncode": completed.returncode,
        "ready_to_complete": ready,
        "status_label": "READY_TO_COMPLETE" if ready else "NOT_READY",
        "json_path": str(json_path),
        "md_path": str(md_path),
        "quality_gate_json": payload.get("quality_gate_json") or "",
        "quality_gate_md": payload.get("quality_gate_md") or "",
        "web_root": payload.get("web_root") or "",
        "readiness_summary": payload.get("readiness_summary") or {},
        "browser_capture_evidence": payload.get("browser_capture_evidence") or {},
        "gates": gates,
        "missing_gates": missing_gates,
        "stdout": completed.stdout[-2000:],
        "stderr": completed.stderr[-2000:],
    }
    if not payload and completed.returncode != 0:
        result["error"] = "readiness audit did not produce JSON"
    return result


def _readiness_source_path(args: argparse.Namespace) -> Path:
    status_json = Path(args.status_json) if args.status_json else DEFAULT_STATUS_JSON
    return status_json.with_name(f"{status_json.stem}_readiness_source.json")


def _write_watch_status_with_readiness(
    args: argparse.Namespace,
    status: Dict[str, Any],
    event: str,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    base_extra = dict(extra or {})
    if args.skip_readiness_audit:
        _write_watch_status(args, status, event, base_extra)
        return
    source_path = _readiness_source_path(args)
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(
        json.dumps(_build_watch_payload(args, status, event, base_extra), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    readiness = _run_readiness_audit(args, source_path)
    if readiness is None:
        _write_watch_status(args, status, event, base_extra)
        return
    final_extra = dict(base_extra)
    final_extra["goal_readiness"] = readiness
    _write_watch_status(args, status, event, final_extra)
    contract = _run_frontend_contract_check(args, event)
    if contract is not None:
        final_extra["frontend_contract_check"] = contract
        _write_watch_status(args, status, event, final_extra)


def _diagnose(args: argparse.Namespace, request_ids: Sequence[str]) -> Dict[str, Any]:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(args.output_base) / f"web_new_samples_watch_{stamp}"
    diagnose_args = SimpleNamespace(
        web_root=args.web_root,
        marker=args.marker,
        words=list(args.words),
        output_dir=str(output_dir),
        update_marker=args.update_marker,
        skip_visuals=args.skip_visuals,
    )
    _print_event(
        "diagnose_start",
        {
            "request_ids": list(request_ids),
            "output_dir": str(output_dir),
            "update_marker": bool(args.update_marker),
            "skip_visuals": bool(args.skip_visuals),
        },
    )
    try:
        payload = marker.diagnose_new(diagnose_args)
    except SystemExit as exc:
        status_path = output_dir / "new_web_samples_status.json"
        payload: Dict[str, Any] = {
            "diagnosed_request_ids": list(request_ids),
            "regression_report": str(output_dir / "flower_jump_regression/flower_jump_web_regression.md"),
            "semantic_diagnostics_report": str(output_dir / "flower_jump_regression/flower_jump_diagnostics/web_semantic_diagnostics.md"),
            "confusion_report": str(output_dir / "flower_jump_confusion/flower_jump_web_confusion_gate.md"),
            "visual_report": "",
            "md_path": str(output_dir / "new_web_samples_status.md"),
            "regression_returncode": int(exc.code or 1),
            "confusion_returncode": None,
            "visual_returncode": None,
        }
        if status_path.exists():
            try:
                payload.update(json.loads(status_path.read_text(encoding="utf-8")))
            except Exception as read_exc:  # pragma: no cover - diagnostic logging path
                payload["status_read_error"] = str(read_exc)
        _print_event(
            "diagnose_failed",
            {
                "request_ids": list(request_ids),
                "output_dir": str(output_dir),
                "returncode": int(exc.code or 1),
                "regression_report": payload.get("regression_report", ""),
                "confusion_report": payload.get("confusion_report", ""),
                "md_path": payload.get("md_path", ""),
            },
        )
        if args.stop_on_error:
            raise
        return payload
    except Exception as exc:  # pragma: no cover - defensive long-running watcher guard
        _print_event(
            "diagnose_exception",
            {
                "request_ids": list(request_ids),
                "output_dir": str(output_dir),
                "error": repr(exc),
            },
        )
        if args.stop_on_error:
            raise
        return {
            "diagnosed_request_ids": list(request_ids),
            "regression_report": str(output_dir / "flower_jump_regression/flower_jump_web_regression.md"),
            "semantic_diagnostics_report": str(output_dir / "flower_jump_regression/flower_jump_diagnostics/web_semantic_diagnostics.md"),
            "confusion_report": str(output_dir / "flower_jump_confusion/flower_jump_web_confusion_gate.md"),
            "visual_report": "",
            "md_path": str(output_dir / "new_web_samples_status.md"),
            "regression_returncode": 1,
            "confusion_returncode": None,
            "visual_returncode": None,
            "error": repr(exc),
        }
    _print_event(
        "diagnose_done",
        {
            "request_ids": payload.get("diagnosed_request_ids", []),
            "regression_report": payload.get("regression_report", ""),
            "semantic_diagnostics_report": payload.get("semantic_diagnostics_report", ""),
            "confusion_report": payload.get("confusion_report", ""),
            "visual_report": payload.get("visual_report", ""),
            "md_path": payload.get("md_path", ""),
            "regression_returncode": payload.get("regression_returncode"),
            "confusion_returncode": payload.get("confusion_returncode"),
            "visual_returncode": payload.get("visual_returncode"),
        },
    )
    return payload


def run(args: argparse.Namespace) -> int:
    loops = 0
    last_failed_key: tuple[str, ...] = ()
    last_failed_at = 0.0
    latest_diagnosis: Optional[Dict[str, Any]] = None
    _print_event(
        "watch_start",
        {
            "web_root": args.web_root,
            "marker": args.marker,
            "words": list(args.words),
            "poll_sec": args.poll_sec,
            "update_marker": bool(args.update_marker),
        },
    )
    while True:
        loops += 1
        status = _target_status(args)
        target_ids = status["target_request_ids"]
        if target_ids:
            target_key = tuple(target_ids)
            now = time.monotonic()
            if (
                last_failed_key == target_key
                and args.failed_retry_sec > 0
                and now - last_failed_at < args.failed_retry_sec
            ):
                retry_after = max(0.0, args.failed_retry_sec - (now - last_failed_at))
                retry_payload = {"request_ids": target_ids, "retry_after_sec": round(retry_after, 1)}
                if args.verbose:
                    _print_event("diagnose_retry_suppressed", retry_payload)
                _write_watch_status_with_readiness(
                    args,
                    status,
                    "diagnose_retry_suppressed",
                    {"latest_diagnosis": latest_diagnosis, "retry_suppressed": retry_payload},
                )
                if args.once:
                    return 0
                if args.max_loops and loops >= args.max_loops:
                    _print_event("watch_stop", {"reason": "max_loops", "loops": loops})
                    return 0
                time.sleep(max(1.0, float(args.poll_sec)))
                continue
            _print_event(
                "new_target_samples",
                {
                    "marker_last_request_id": status["marker_last_request_id"],
                    "new_summary": status["new_summary"],
                    "target_summary": status["target_summary"],
                    "target_request_ids": target_ids,
                },
            )
            latest_diagnosis = _diagnose(args, target_ids)
            try:
                latest_diagnosis["static_artifacts"] = _mirror_latest_artifacts(args, latest_diagnosis)
            except Exception as exc:  # pragma: no cover - watcher must keep running.
                latest_diagnosis["static_artifacts"] = {"error": repr(exc)}
            failed = (
                bool(latest_diagnosis.get("error"))
                or int(latest_diagnosis.get("regression_returncode") or 0) != 0
                or int(latest_diagnosis.get("confusion_returncode") or 0) != 0
                or int(latest_diagnosis.get("visual_returncode") or 0) != 0
            )
            if failed:
                last_failed_key = target_key
                last_failed_at = time.monotonic()
            else:
                last_failed_key = ()
                last_failed_at = 0.0
                status = _target_status(args)
            _write_watch_status_with_readiness(
                args,
                status,
                "diagnose_failed" if failed else "diagnose_done",
                {"latest_diagnosis": latest_diagnosis},
            )
            if args.once:
                return 0
        else:
            _write_watch_status_with_readiness(args, status, "no_target_samples", {"latest_diagnosis": latest_diagnosis})
            if args.verbose or args.once:
                _print_event(
                    "no_target_samples",
                    {
                        "marker_last_request_id": status["marker_last_request_id"],
                        "new_summary": status["new_summary"],
                    },
                )
            if args.once:
                return 0

        if args.max_loops and loops >= args.max_loops:
            _print_event("watch_stop", {"reason": "max_loops", "loops": loops})
            return 0
        time.sleep(max(1.0, float(args.poll_sec)))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="监听 marker 后新增网页样本并自动诊断")
    parser.add_argument("--web-root", default=str(marker.DEFAULT_WEB_ROOT))
    parser.add_argument("--marker", default=str(marker.DEFAULT_MARKER))
    parser.add_argument("--words", nargs="*", default=list(marker.DEFAULT_WORDS))
    parser.add_argument("--output-base", default=str(DEFAULT_OUTPUT_BASE))
    parser.add_argument("--poll-sec", type=float, default=20.0)
    parser.add_argument("--failed-retry-sec", type=float, default=300.0, help="同一批样本诊断失败后的最短重试间隔")
    parser.add_argument("--once", action="store_true", help="只检查一次；若有目标样本则诊断后退出")
    parser.add_argument("--max-loops", type=int, default=0, help="最多轮询次数，0 表示不限")
    parser.add_argument("--update-marker", action="store_true", default=True, help="诊断成功后更新 marker，避免重复诊断")
    parser.add_argument("--no-update-marker", dest="update_marker", action="store_false")
    parser.add_argument("--skip-visuals", action="store_true", help="只跑评分诊断，不生成骨架可视化")
    parser.add_argument("--stop-on-error", action="store_true", help="诊断失败时退出 watcher；默认记录错误并继续监听")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--log-file", default=str(DEFAULT_LOG), help="仅用于 tmux 启动说明；脚本自身写 stdout")
    parser.add_argument("--status-json", default=str(DEFAULT_STATUS_JSON), help="覆盖写入的 watcher 状态 JSON")
    parser.add_argument("--status-md", default=str(DEFAULT_STATUS_MD), help="覆盖写入的 watcher 状态 Markdown")
    parser.add_argument("--status-json-mirror", default="", help="可选的状态 JSON 镜像路径，例如前端静态目录")
    parser.add_argument("--status-md-mirror", default="", help="可选的状态 Markdown 镜像路径，例如前端静态目录")
    parser.add_argument("--static-artifact-dir", default=str(DEFAULT_STATIC_ARTIFACT_DIR), help="将最近诊断报告/关键骨架图镜像到此前端静态目录")
    parser.add_argument("--static-artifact-url", default=DEFAULT_STATIC_ARTIFACT_URL, help="static-artifact-dir 对应的浏览器 URL 前缀")
    parser.add_argument("--skip-readiness-audit", action="store_true", help="不运行目标完成度快速审计")
    parser.add_argument("--readiness-output-dir", default=str(DEFAULT_READINESS_OUTPUT_DIR), help="目标完成度审计输出目录")
    parser.add_argument(
        "--readiness-watch-status-url",
        default="http://127.0.0.1:5080/static/watch_status.json",
        help="目标完成度审计读取的 watcher 状态 URL",
    )
    parser.add_argument("--readiness-timeout-sec", type=float, default=3.0, help="目标完成度审计 HTTP 超时")
    parser.add_argument("--readiness-quality-gate-json", default="", help="可选指定综合质量门 JSON")
    parser.add_argument("--skip-frontend-contract-check", action="store_true", help="诊断完成后不运行前端 watcher 状态契约检查")
    parser.add_argument("--frontend-contract-output-dir", default=str(DEFAULT_FRONTEND_CONTRACT_OUTPUT_DIR), help="前端契约检查输出目录")
    parser.add_argument("--frontend-contract-base-url", default="http://127.0.0.1:5080", help="前端契约检查使用的 5080 base URL")
    parser.add_argument("--frontend-contract-timeout-sec", type=float, default=3.0, help="前端契约检查 HTTP 超时")
    parser.add_argument("--frontend-contract-max-artifact-checks", type=int, default=24, help="最多检查的诊断报告/骨架图 URL 数")
    parser.add_argument("--frontend-contract-max-watch-age-sec", type=float, default=180.0, help="watch_status 新鲜度阈值")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except KeyboardInterrupt:
        _print_event("watch_stop", {"reason": "keyboard_interrupt"})
        return 130


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate the browser-facing watcher status contract.

This script is intentionally read-only: it does not call /api/score, move the
formal marker, or restart the Holistic backend.  It checks that the frontend can
still consume watcher status payloads and, when a diagnosis artifact mirror is
present, that the browser-visible links are reachable.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


PROJECT_ROOT = Path("/data/WYC/signLanguage")
DEFAULT_STATUS_JSON = PROJECT_ROOT / "work/web/static/watch_status.json"
DEFAULT_INDEX_HTML = PROJECT_ROOT / "work/web/static/index.html"
DEFAULT_APP_JS = PROJECT_ROOT / "work/web/static/app.js"
DEFAULT_STYLES_CSS = PROJECT_ROOT / "work/web/static/styles.css"
DEFAULT_OUTPUT_BASE = PROJECT_ROOT / "work/generated/scoring_mvp_run3"
DEFAULT_BASE_URL = "http://127.0.0.1:5080"

REQUIRED_APP_JS_TOKENS = [
    "WATCH_REFRESH_AFTER_SCORE_DELAYS_MS",
    "refreshWatchStatus",
    "formatBrowserCaptureEvidence",
    "formatReadinessSummary",
    "formatFrontendContractCheck",
    "renderWatchArtifactLinks",
    "readiness_summary",
    "frontend_contract_check",
    "static_artifacts",
    "/static/watch_status.json",
    "scheduleWatchRefreshAfterScore",
    "renderWatchWordCoverage",
    "renderWatchNextRetestStep",
    "watchWordCoverage",
    "watchNextStep",
    "frame_indices",
    "frame_weights",
    "client_source",
    "client_session_id",
    "client_capture_id",
    "browser_camera",
    "phase_order_disorder",
    "semantic_phase_order_guard",
    "相位顺序守卫",
    "相位乱序指标",
]

REQUIRED_INDEX_HTML_TOKENS = [
    "watchWordCoverage",
    "watch-word-coverage",
    "watchNextStep",
    "watch-next-step",
]

REQUIRED_STYLES_CSS_TOKENS = [
    "watch-word-coverage",
    "watch-word-chip",
    "watch-word-chip-covered",
    "watch-word-chip-missing",
    "watch-word-chip-failed",
    "watch-next-step",
]

ALLOWED_EVENTS = {
    "no_target_samples",
    "diagnose_done",
    "diagnose_failed",
    "diagnose_exception",
    "diagnose_retry_suppressed",
    "missing",
    "unknown",
}


@dataclass
class Check:
    name: str
    passed: bool
    detail: str
    severity: str = "fail"


@dataclass
class CheckContext:
    checks: list[Check] = field(default_factory=list)

    def add(self, name: str, passed: bool, detail: str, severity: str = "fail") -> None:
        self.checks.append(Check(name=name, passed=passed, detail=detail, severity=severity))

    @property
    def failed(self) -> list[Check]:
        return [row for row in self.checks if not row.passed and row.severity == "fail"]

    @property
    def warnings(self) -> list[Check]:
        return [row for row in self.checks if not row.passed and row.severity == "warn"]


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def fetch_url(url: str, timeout_sec: float) -> tuple[bool, int | None, str]:
    req = Request(url, headers={"User-Agent": "signlanguage-contract-check/1.0"})
    try:
        with urlopen(req, timeout=timeout_sec) as resp:
            status = int(getattr(resp, "status", 200))
            # Read a tiny prefix so servers that lazily fail on body are caught.
            resp.read(256)
        return 200 <= status < 300, status, "ok"
    except HTTPError as exc:
        return False, int(exc.code), str(exc)
    except (URLError, TimeoutError, OSError) as exc:
        return False, None, str(exc)


def fetch_json_url(url: str, timeout_sec: float) -> tuple[bool, int | None, Any, str]:
    req = Request(url, headers={"User-Agent": "signlanguage-contract-check/1.0"})
    try:
        with urlopen(req, timeout=timeout_sec) as resp:
            status = int(getattr(resp, "status", 200))
            raw = resp.read()
        payload = json.loads(raw.decode("utf-8"))
        return 200 <= status < 300, status, payload, "ok"
    except HTTPError as exc:
        return False, int(exc.code), {}, str(exc)
    except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return False, None, {}, str(exc)


def parse_iso_seconds(value: str) -> float | None:
    if not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        return datetime.fromisoformat(text).timestamp()
    except ValueError:
        return None


def as_payload(data: Any) -> dict[str, Any]:
    if isinstance(data, dict) and isinstance(data.get("payload"), dict):
        return data["payload"]
    if isinstance(data, dict):
        return data
    return {}


def normalize_url(base_url: str, raw_url: str) -> str:
    if raw_url.startswith("http://") or raw_url.startswith("https://"):
        return raw_url
    return urljoin(base_url.rstrip("/") + "/", raw_url.lstrip("/"))


def validate_status_contract(ctx: CheckContext, payload: dict[str, Any], require_fresh: bool, max_age_sec: float) -> None:
    ctx.add("watch_status_is_object", isinstance(payload, dict), f"type={type(payload).__name__}")
    if not isinstance(payload, dict):
        return

    generated_at = str(payload.get("generated_at") or "")
    event = str(payload.get("event") or "")
    status = payload.get("status") if isinstance(payload.get("status"), dict) else {}
    readiness = payload.get("goal_readiness") if isinstance(payload.get("goal_readiness"), dict) else {}

    ctx.add("watch_status_generated_at", bool(generated_at), generated_at or "missing")
    ctx.add("watch_status_event_known", event in ALLOWED_EVENTS, event or "missing")
    ctx.add("watcher_pid_present", bool(payload.get("watcher_pid")), f"watcher_pid={payload.get('watcher_pid')}")
    ctx.add("watch_status_has_status_block", bool(status), f"keys={sorted(status.keys()) if status else []}")

    if require_fresh:
        ts = parse_iso_seconds(generated_at)
        age = None if ts is None else max(0.0, time.time() - ts)
        ctx.add(
            "watch_status_fresh",
            age is not None and age <= max_age_sec,
            "age_sec={:.1f}, max_age_sec={:.1f}".format(age if age is not None else -1, max_age_sec),
        )

    target_summary = status.get("target_summary") if isinstance(status.get("target_summary"), dict) else {}
    ctx.add("target_summary_present", bool(target_summary), f"target_summary={target_summary}")
    if target_summary:
        ctx.add(
            "target_summary_count_numeric",
            isinstance(target_summary.get("count"), (int, float)),
            f"count={target_summary.get('count')}",
        )

    ctx.add("goal_readiness_present", bool(readiness), f"keys={sorted(readiness.keys()) if readiness else []}")
    if readiness:
        ctx.add(
            "goal_readiness_status_label_present",
            bool(readiness.get("status_label")),
            f"status_label={readiness.get('status_label')}",
        )
        ctx.add(
            "goal_readiness_missing_gates_list",
            isinstance(readiness.get("missing_gates"), list),
            f"missing_gates={readiness.get('missing_gates')}",
        )
        evidence = readiness.get("browser_capture_evidence")
        ctx.add(
            "browser_capture_evidence_present",
            isinstance(evidence, dict),
            f"type={type(evidence).__name__}",
        )
        if isinstance(evidence, dict):
            ctx.add(
                "browser_capture_evidence_rows_list",
                isinstance(evidence.get("rows"), list),
                f"rows_type={type(evidence.get('rows')).__name__}",
            )

    latest = payload.get("latest_diagnosis")
    target_count = int(target_summary.get("count") or 0) if isinstance(target_summary.get("count"), (int, float, str)) else 0
    if latest is None:
        ctx.add(
            "latest_diagnosis_optional_when_no_targets",
            target_count == 0,
            f"target_count={target_count}, latest_diagnosis=null",
            severity="warn",
        )
    elif isinstance(latest, dict):
        event_requires_diagnosis = event == "diagnose_done"
        ctx.add(
            "latest_diagnosis_object",
            True,
            f"keys={sorted(latest.keys())}",
        )
        if event_requires_diagnosis:
            for key in ("regression_returncode", "confusion_returncode", "visual_returncode"):
                ctx.add(
                    f"latest_diagnosis_{key}_zero",
                    latest.get(key) in (0, "0"),
                    f"{key}={latest.get(key)}",
                )
    else:
        ctx.add("latest_diagnosis_shape", False, f"type={type(latest).__name__}")


def collect_artifact_urls(artifacts: dict[str, Any], max_checks: int) -> list[tuple[str, str]]:
    urls: list[tuple[str, str]] = []
    if artifacts.get("index_url"):
        urls.append(("diagnosis_index", str(artifacts["index_url"])))
    if artifacts.get("manifest_url"):
        urls.append(("artifact_manifest", str(artifacts["manifest_url"])))
    for item in artifacts.get("reports") or []:
        if isinstance(item, dict) and item.get("url"):
            label = str(item.get("label") or item.get("kind") or "report")
            urls.append((f"report:{label}", str(item["url"])))
    for item in artifacts.get("visuals") or []:
        if isinstance(item, dict) and item.get("url"):
            label = str(item.get("label") or item.get("kind") or "visual")
            urls.append((f"visual:{label}", str(item["url"])))
    return urls[:max_checks]


def validate_artifact_links(
    ctx: CheckContext,
    payload: dict[str, Any],
    base_url: str,
    timeout_sec: float,
    max_checks: int,
) -> list[dict[str, Any]]:
    latest = payload.get("latest_diagnosis") if isinstance(payload.get("latest_diagnosis"), dict) else {}
    artifacts = latest.get("static_artifacts") if isinstance(latest.get("static_artifacts"), dict) else {}
    if not artifacts:
        ctx.add("static_artifacts_optional", True, "no static_artifacts in current payload")
        return []

    ctx.add("static_artifacts_index_url_present", bool(artifacts.get("index_url")), f"index_url={artifacts.get('index_url')}")
    ctx.add(
        "static_artifacts_manifest_url_present",
        bool(artifacts.get("manifest_url")),
        f"manifest_url={artifacts.get('manifest_url')}",
    )
    urls = collect_artifact_urls(artifacts, max_checks=max_checks)
    ctx.add("static_artifact_urls_present", bool(urls), f"checked_count={len(urls)}")

    results: list[dict[str, Any]] = []
    for label, raw_url in urls:
        full_url = normalize_url(base_url, raw_url)
        ok, status, detail = fetch_url(full_url, timeout_sec=timeout_sec)
        ctx.add(f"artifact_url_200:{label}", ok, f"{full_url} status={status} detail={detail}")
        results.append({"label": label, "url": full_url, "ok": ok, "status": status, "detail": detail})
    return results


def validate_frontend_js(ctx: CheckContext, app_js_path: Path, base_url: str, timeout_sec: float) -> None:
    ctx.add("frontend_app_js_file_exists", app_js_path.exists(), str(app_js_path))
    text = read_text(app_js_path) if app_js_path.exists() else ""
    for token in REQUIRED_APP_JS_TOKENS:
        ctx.add(f"frontend_js_token:{token}", token in text, f"token={token}")

    app_js_url = normalize_url(base_url, "/static/app.js")
    ok, status, detail = fetch_url(app_js_url, timeout_sec=timeout_sec)
    ctx.add("frontend_app_js_http_200", ok, f"{app_js_url} status={status} detail={detail}")


def validate_browser_upload_weight_semantics(ctx: CheckContext, app_js_path: Path) -> None:
    """Guard the browser-camera strong evidence path against token-only regressions."""

    text = read_text(app_js_path) if app_js_path.exists() else ""
    checks = {
        "frontend_upload_motion_signature_pipeline": [
            "buildMotionSignature(ctx, width, height)",
            "signatureMotion(prevSignature, captured.signature)",
            "normalizeFrameWeights(energies)",
            "selectEnergyCoverageFrames(candidates, targetFrames)",
        ],
        "frontend_upload_weight_normalization_nonuniform": [
            "baseline * 0.2",
            "Math.max(0.45",
            "Math.min(2.75",
            "toFixed(4)",
        ],
        "frontend_upload_energy_coverage_selection": [
            "coverageRatio",
            "0.25 + target / 32",
            "coverageCount",
            "energySmooth",
            ".sort((a, b) => b.score - a.score)",
        ],
        "frontend_upload_selected_weight_from_frame_weight": [
            "uploadWeight: item.frameWeight",
            "uploadWeight: candidates[idx].frameWeight",
        ],
        "frontend_upload_frame_weights_from_selected": [
            "const frameWeights = selected.map((item) => item.uploadWeight);",
        ],
        "frontend_upload_frame_indices_from_selected": [
            "const frameIndices = selected.map((item) => item.candidateIndex);",
        ],
        "frontend_upload_strong_evidence_payload": [
            "frame_indices: frameIndices",
            "frame_weights: frameWeights",
            'client_source: "browser_camera"',
            "client_session_id: ensureClientSessionId()",
            "client_capture_id: `capture_${Date.now()}`",
        ],
    }
    for name, snippets in checks.items():
        missing = [snippet for snippet in snippets if snippet not in text]
        ctx.add(name, not missing, f"missing={missing or []}")

    forbidden_constant_patterns = [
        "frame_weights: new Array",
        "frame_weights: Array(",
        "frame_weights: frames.map(() => 1",
        "frame_weights: selected.map(() => 1",
        "const frameWeights = frames.map(() => 1",
        "const frameWeights = selected.map(() => 1",
        "const frameWeights = new Array",
        "const frameWeights = Array(",
    ]
    present_forbidden = [pattern for pattern in forbidden_constant_patterns if pattern in text]
    ctx.add(
        "frontend_upload_no_constant_frame_weights",
        not present_forbidden,
        f"forbidden_patterns={present_forbidden or []}",
    )


def validate_frontend_static_assets(
    ctx: CheckContext,
    index_html_path: Path,
    styles_css_path: Path,
    base_url: str,
    timeout_sec: float,
) -> None:
    ctx.add("frontend_index_html_file_exists", index_html_path.exists(), str(index_html_path))
    html_text = read_text(index_html_path) if index_html_path.exists() else ""
    for token in REQUIRED_INDEX_HTML_TOKENS:
        ctx.add(f"frontend_html_token:{token}", token in html_text, f"token={token}")

    index_url = normalize_url(base_url, "/")
    ok, status, detail = fetch_url(index_url, timeout_sec=timeout_sec)
    ctx.add("frontend_index_http_200", ok, f"{index_url} status={status} detail={detail}")

    ctx.add("frontend_styles_css_file_exists", styles_css_path.exists(), str(styles_css_path))
    css_text = read_text(styles_css_path) if styles_css_path.exists() else ""
    for token in REQUIRED_STYLES_CSS_TOKENS:
        ctx.add(f"frontend_css_token:{token}", token in css_text, f"token={token}")

    styles_url = normalize_url(base_url, "/static/styles.css")
    ok, status, detail = fetch_url(styles_url, timeout_sec=timeout_sec)
    ctx.add("frontend_styles_css_http_200", ok, f"{styles_url} status={status} detail={detail}")


def validate_live_score_upload_contract(ctx: CheckContext, base_url: str, timeout_sec: float) -> None:
    openapi_url = normalize_url(base_url, "/openapi.json")
    ok, status, payload, detail = fetch_json_url(openapi_url, timeout_sec=timeout_sec)
    ctx.add("live_openapi_http_200", ok, f"{openapi_url} status={status} detail={detail}")
    schemas = payload.get("components", {}).get("schemas", {}) if isinstance(payload, dict) else {}
    score_schema = schemas.get("ScoreRequest") if isinstance(schemas, dict) else {}
    props = score_schema.get("properties", {}) if isinstance(score_schema, dict) else {}
    ctx.add("live_score_request_schema_present", bool(props), f"properties={sorted(props.keys()) if props else []}")
    for token in ("target_word", "fps", "duration_sec", "frames", "frame_indices", "frame_weights"):
        ctx.add(f"live_score_request_field:{token}", token in props, f"field={token}")
    for token in ("client_source", "client_session_id", "client_capture_id"):
        ctx.add(
            f"live_score_request_field:{token}",
            token in props,
            f"field={token}",
            severity="warn",
        )


def write_reports(
    output_dir: Path,
    payload: dict[str, Any],
    ctx: CheckContext,
    artifact_results: list[dict[str, Any]],
    args: argparse.Namespace,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    status = "PASS" if not ctx.failed else "FAIL"
    json_path = output_dir / "watch_status_frontend_contract.json"
    md_path = output_dir / "watch_status_frontend_contract.md"

    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "base_url": args.base_url,
        "watch_status_json": str(args.watch_status_json),
        "index_html": str(args.index_html),
        "app_js": str(args.app_js),
        "styles_css": str(args.styles_css),
        "failed_count": len(ctx.failed),
        "warning_count": len(ctx.warnings),
        "checks": [row.__dict__ for row in ctx.checks],
        "artifact_url_results": artifact_results,
        "payload_summary": {
            "event": payload.get("event"),
            "generated_at": payload.get("generated_at"),
            "watcher_pid": payload.get("watcher_pid"),
            "target_count": (payload.get("status") or {}).get("target_summary", {}).get("count")
            if isinstance(payload.get("status"), dict)
            else None,
            "goal_status": (payload.get("goal_readiness") or {}).get("status_label")
            if isinstance(payload.get("goal_readiness"), dict)
            else None,
            "missing_gates": (payload.get("goal_readiness") or {}).get("missing_gates")
            if isinstance(payload.get("goal_readiness"), dict)
            else None,
        },
    }
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Watch Status Frontend Contract Check",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- status: **{status}**",
        f"- base_url: `{args.base_url}`",
        f"- watch_status_json: `{args.watch_status_json}`",
        f"- index_html: `{args.index_html}`",
        f"- app_js: `{args.app_js}`",
        f"- styles_css: `{args.styles_css}`",
        f"- failed_count: `{len(ctx.failed)}`",
        f"- warning_count: `{len(ctx.warnings)}`",
        "",
        "## Payload Summary",
        "",
        f"- event: `{report['payload_summary']['event']}`",
        f"- generated_at: `{report['payload_summary']['generated_at']}`",
        f"- watcher_pid: `{report['payload_summary']['watcher_pid']}`",
        f"- target_count: `{report['payload_summary']['target_count']}`",
        f"- goal_status: `{report['payload_summary']['goal_status']}`",
        f"- missing_gates: `{report['payload_summary']['missing_gates']}`",
        "",
        "## Checks",
        "",
        "| check | result | severity | detail |",
        "| --- | --- | --- | --- |",
    ]
    for row in ctx.checks:
        result = "PASS" if row.passed else "FAIL"
        detail = row.detail.replace("|", "\\|").replace("\n", " ")
        lines.append(f"| `{row.name}` | {result} | `{row.severity}` | {detail} |")

    if artifact_results:
        lines.extend(["", "## Artifact URLs", "", "| label | ok | status | url |", "| --- | --- | --- | --- |"])
        for row in artifact_results:
            lines.append(
                f"| `{row['label']}` | `{row['ok']}` | `{row['status']}` | {row['url']} |"
            )

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--watch-status-json", type=Path, default=DEFAULT_STATUS_JSON)
    parser.add_argument("--index-html", type=Path, default=DEFAULT_INDEX_HTML)
    parser.add_argument("--app-js", type=Path, default=DEFAULT_APP_JS)
    parser.add_argument("--styles-css", type=Path, default=DEFAULT_STYLES_CSS)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--http-timeout-sec", type=float, default=3.0)
    parser.add_argument("--max-artifact-checks", type=int, default=20)
    parser.add_argument("--require-fresh", action="store_true")
    parser.add_argument("--max-watch-age-sec", type=float, default=180.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir or (
        DEFAULT_OUTPUT_BASE / f"watch_status_frontend_contract_{now_stamp()}"
    )
    ctx = CheckContext()

    ctx.add("watch_status_json_exists", args.watch_status_json.exists(), str(args.watch_status_json))
    try:
        data = load_json(args.watch_status_json) if args.watch_status_json.exists() else {}
        payload = as_payload(data)
    except Exception as exc:  # noqa: BLE001 - report malformed status payload cleanly.
        payload = {}
        ctx.add("watch_status_json_loadable", False, repr(exc))
    else:
        ctx.add("watch_status_json_loadable", True, str(args.watch_status_json))

    validate_status_contract(
        ctx,
        payload,
        require_fresh=args.require_fresh,
        max_age_sec=args.max_watch_age_sec,
    )
    artifact_results = validate_artifact_links(
        ctx,
        payload,
        base_url=args.base_url,
        timeout_sec=args.http_timeout_sec,
        max_checks=args.max_artifact_checks,
    )
    validate_frontend_js(ctx, args.app_js, args.base_url, timeout_sec=args.http_timeout_sec)
    validate_browser_upload_weight_semantics(ctx, args.app_js)
    validate_frontend_static_assets(
        ctx,
        args.index_html,
        args.styles_css,
        args.base_url,
        timeout_sec=args.http_timeout_sec,
    )
    validate_live_score_upload_contract(ctx, args.base_url, timeout_sec=args.http_timeout_sec)

    json_path, md_path = write_reports(output_dir, payload, ctx, artifact_results, args)
    status = "PASS" if not ctx.failed else "FAIL"
    print(f"watch-status/frontend contract: {status}")
    print(f"JSON: {json_path}")
    print(f"MD: {md_path}")
    if ctx.failed:
        for row in ctx.failed:
            print(f"- FAIL {row.name}: {row.detail}", file=sys.stderr)
    if ctx.warnings:
        for row in ctx.warnings:
            print(f"- WARN {row.name}: {row.detail}", file=sys.stderr)
    return 0 if not ctx.failed else 1


if __name__ == "__main__":
    raise SystemExit(main())

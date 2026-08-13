#!/usr/bin/env python3
"""独立 daemon v1 消息中心。

本脚本只使用 daemon 的 HTTP session API，不读取或写入旧 TUI/team 消息协议。
每次投递先记录 queued，再记录 sent 或 failed，便于离线审计。
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("/data/WYC/signLanguage")
MANIFEST_DEFAULT = ROOT / ".team/daemon_migration_4194_manifest.json"
MAILBOX_DEFAULT = ROOT / ".team/daemon_v1/mailbox.jsonl"
ALLOWED_STATES = {"queued", "sent", "failed"}

# 可供 shell/监控程序稳定判断的错误码。
EXIT_OK = 0
EXIT_USAGE = 2
EXIT_MANIFEST = 3
EXIT_TARGET = 4
EXIT_NETWORK = 5
EXIT_HTTP = 6
EXIT_SCHEMA = 7


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"无法读取 manifest {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("manifest 顶层必须是 JSON object")
    if not isinstance(value.get("daemon_url"), str) or not value["daemon_url"]:
        raise ValueError("manifest 缺少 daemon_url")
    if not isinstance(value.get("workspace"), str) or not value["workspace"]:
        raise ValueError("manifest 缺少 workspace")
    return value


def role_sessions(manifest: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for container_name in ("roles", "copied"):
        entries = manifest.get(container_name, {})
        if not isinstance(entries, dict):
            continue
        for role, item in entries.items():
            if not isinstance(item, dict):
                continue
            sid = item.get("session_id")
            if isinstance(sid, str) and sid:
                result[role] = sid
            target = item.get("target_session_id")
            if isinstance(target, str) and target:
                result[role] = target
            stable_id = role.split("-", 1)[0]
            if stable_id in {"signL2", "signL4", "signL5", "signL6", "signL7", "signL8", "signL9"} and isinstance(sid, str) and sid:
                result[stable_id] = sid
    migrated = manifest.get("supervisor_migrated_target")
    if isinstance(migrated, str) and migrated:
        result["supervisor"] = migrated
        result["SignL3"] = migrated
    return result


def validate_localhost(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "http" or parsed.hostname != "127.0.0.1":
        raise ValueError("daemon URL 必须使用 http://127.0.0.1（禁止访问非本机地址）")


def append_record(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()


def post_prompt(base: str, session_id: str, prompt: str, timeout: float) -> dict[str, Any]:
    payload = json.dumps({"prompt": prompt}, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        f"{base.rstrip('/')}/session/{urllib.parse.quote(session_id, safe='')}/prompt",
        data=payload,
        method="POST",
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            value: Any = json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(f"daemon HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ConnectionError(f"daemon 请求失败: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError("daemon 响应不是 JSON object")
    return value


def check_schema(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"mailbox 文件不存在（首次运行正常）：{path}"]
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [f"无法读取 mailbox：{exc}"]
    for line_no, line in enumerate(lines, 1):
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"第 {line_no} 行不是 JSON：{exc}")
            continue
        if not isinstance(record, dict):
            errors.append(f"第 {line_no} 行不是 object")
            continue
        for field in ("message_id", "recorded_at", "state", "to_session", "prompt"):
            if field not in record:
                errors.append(f"第 {line_no} 行缺少字段 {field}")
        if record.get("state") not in ALLOWED_STATES:
            errors.append(f"第 {line_no} 行 state 无效：{record.get('state')}")
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="向 daemon v1 session 投递消息并写入 mailbox/archive JSONL")
    destination = parser.add_mutually_exclusive_group()
    destination.add_argument("--to-role", help="manifest 中的角色名")
    destination.add_argument("--to-session", help="目标 daemon session ID")
    parser.add_argument("--prompt", help="要投递的文本")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_DEFAULT)
    parser.add_argument("--mailbox", type=Path, default=MAILBOX_DEFAULT)
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--offline-schema-check", action="store_true", help="只检查 mailbox JSONL schema，不访问 daemon")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.offline_schema_check:
        errors = check_schema(args.mailbox)
        if errors and not (len(errors) == 1 and "首次运行正常" in errors[0]):
            for error in errors:
                print(f"schema-error: {error}", file=sys.stderr)
            return EXIT_SCHEMA
        print(json.dumps({"schema": "ok", "mailbox": str(args.mailbox)}, ensure_ascii=False))
        return EXIT_OK
    if not args.prompt:
        print("error: 必须提供 --prompt", file=sys.stderr)
        return EXIT_USAGE
    try:
        manifest = load_manifest(args.manifest)
        daemon_url = manifest["daemon_url"]
        validate_localhost(daemon_url)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_MANIFEST
    if args.to_role:
        session_id = role_sessions(manifest).get(args.to_role)
        if not session_id:
            print(f"error: manifest 中找不到角色或 session_id：{args.to_role}", file=sys.stderr)
            return EXIT_TARGET
        role = args.to_role
    elif args.to_session:
        session_id, role = args.to_session, None
    else:
        print("error: 必须提供 --to-role 或 --to-session（二选一）", file=sys.stderr)
        return EXIT_USAGE
    message_id = str(uuid.uuid4())
    common = {"message_id": message_id, "to_role": role, "to_session": session_id, "prompt": args.prompt}
    append_record(args.mailbox, {**common, "state": "queued", "recorded_at": now()})
    try:
        response = post_prompt(daemon_url, session_id, args.prompt, args.timeout)
    except ConnectionError as exc:
        append_record(args.mailbox, {**common, "state": "failed", "recorded_at": now(), "error": str(exc)})
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_NETWORK
    except RuntimeError as exc:
        append_record(args.mailbox, {**common, "state": "failed", "recorded_at": now(), "error": str(exc)})
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_HTTP
    response_recorded_at = now()
    sent = {**common, "state": "sent", "recorded_at": response_recorded_at, "response": response,
            "stop_reason": response.get("stopReason"),
            "response_time": response.get("time") or response.get("timestamp") or response_recorded_at}
    append_record(args.mailbox, sent)
    print(json.dumps(sent, ensure_ascii=False))
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())

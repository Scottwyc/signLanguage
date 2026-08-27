#!/usr/bin/env python3
"""自动同步 team_topology.json 的角色→本地模型映射（从 daemon 4194 实时读取）。

背景（2026-08-27）：成员与本地模型卡的映射原先手工维护在 team_topology.json 的
roles[*].model / local_service，成员切换模型后容易过时（如 g02→g29 迁移后仍写旧值）。
本脚本每轮从 daemon 枚举各角色会话的 currentModelId，按 local_model_services.aliases
匹配出服务 id，回写 roles[*].model / local_service（其余字段不动），并节流写盘（默认
60s 窗口 + 内容变化才写），避免高频磁盘 IO。

用法:
  python3 sync_team_topology_models_v1.py [--dry-run] [--force] [--only signL3]
依赖:
  - daemon 4194（token 读 .team/daemon_v1/.daemon_token）
  - registry.json（角色→session_id 映射，refresher 维护）
  - team_topology.json（被更新目标）
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path("/data/WYC/signLanguage")
TEAM = ROOT / ".team"
DAEMON_V1 = TEAM / "daemon_v1"
REGISTRY = DAEMON_V1 / "registry.json"
TOKEN_FILE = DAEMON_V1 / ".daemon_token"
TOPOLOGY = TEAM / "team_topology.json"
STATE_FILE = DAEMON_V1 / "topology_sync_state.json"   # 记录上次写盘时间/指纹
DAEMON_URL = "http://127.0.0.1:4194"
WRITE_COOLDOWN = 60.0    # 两次写盘最小间隔（秒）


def load_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def daemon_headers() -> dict:
    token = ""
    try:
        token = TOKEN_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        pass
    return {"Authorization": f"Bearer {token}"} if token else {}


def http_get(path: str, timeout: float = 6.0):
    req = urllib.request.Request(DAEMON_URL + path, headers=daemon_headers())
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def current_model(session_id: str) -> str | None:
    """返回会话 currentModelId（去 (provider) 后缀），失败返回 None。"""
    try:
        ctx = http_get(f"/session/{urllib.parse.quote(session_id, safe='')}/context")
        mid = str(((ctx.get("state") or {}).get("models") or {}).get("currentModelId") or "")
        return mid.split("(")[0].strip() or None
    except (urllib.error.HTTPError, urllib.error.URLError, OSError, ValueError):
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="只打印不写盘")
    ap.add_argument("--force", action="store_true", help="忽略 60s 节流窗口强制写盘")
    ap.add_argument("--only", default=None, help="只同步指定角色（如 signL3）")
    args = ap.parse_args()

    reg = load_json(REGISTRY)
    topo = load_json(TOPOLOGY)
    if not isinstance(reg, dict) or not isinstance(topo, dict):
        print("registry 或 topology 读取失败", file=sys.stderr)
        return 1

    roles_cfg = topo.get("roles") or {}
    services = (topo.get("local_model_services") or {}).get("services") or []
    # aliases → service id 映射（含 id 本身）
    alias_to_sid: dict[str, str] = {}
    for s in services:
        sid = s.get("id")
        if not sid:
            continue
        alias_to_sid[str(sid).lower()] = str(sid)
        for a in s.get("aliases") or []:
            alias_to_sid[str(a).lower()] = str(sid)

    # 角色 → session_id（registry roles + 手工 roles 兜底）
    updates: dict[str, tuple[str | None, str | None]] = {}
    for role, cfg in roles_cfg.items():
        if args.only and role.lower() != args.only.lower():
            continue
        sid = ((reg.get("roles") or {}).get(role) or {}).get("session_id")
        if not sid:
            continue
        mid = current_model(sid)
        if mid is None:
            print(f"[{role}] 会话模型读取失败（{sid[:8]}），跳过")
            continue
        sid_svc = alias_to_sid.get(mid.lower())
        updates[role] = (mid, sid_svc)
        print(f"[{role}] {cfg.get('name', role):10s} model={mid} local_service={sid_svc or 'None'}")

    if not updates:
        print("无更新项", file=sys.stderr)
        return 0

    # 节流：内容未变化或未到窗口不写盘
    prev_state = load_json(STATE_FILE, {})
    changed = False
    for role, (mid, svc) in updates.items():
        if roles_cfg.get(role, {}).get("model") != mid or roles_cfg.get(role, {}).get("local_service") != svc:
            changed = True
    now = time.time()
    last_write = float(prev_state.get("last_write_at") or 0)
    if not changed:
        print("无变化，跳过写盘")
        return 0
    if not args.force and not args.dry_run and now - last_write < WRITE_COOLDOWN:
        print(f"节流：距上次写盘 {now - last_write:.0f}s < {WRITE_COOLDOWN:.0f}s，跳过（--force 可绕过）")
        return 0

    # 应用更新
    for role, (mid, svc) in updates.items():
        if role in roles_cfg:
            roles_cfg[role]["model"] = mid
            roles_cfg[role]["local_service"] = svc
    topo["roles"] = roles_cfg
    (topo.get("local_model_services") or {})["_updated_at"] = time.strftime("%Y-%m-%dT%H:%M+08:00")

    if args.dry_run:
        print("dry-run：以上为待写盘内容")
        return 0
    TOPOLOGY.write_text(json.dumps(topo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    STATE_FILE.write_text(json.dumps({"last_write_at": now}, ensure_ascii=False), encoding="utf-8")
    print(f"已写盘 team_topology.json（{len(updates)} 个角色更新）")
    return 0


if __name__ == "__main__":
    sys.exit(main())

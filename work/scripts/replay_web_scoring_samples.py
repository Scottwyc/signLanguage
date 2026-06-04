#!/usr/bin/env python3
"""Replay saved web scoring samples with the current scoring module.

The web backend stores both request metadata and the generated Holistic JSON.
This script re-scores those saved samples without rerunning MediaPipe, so every
scoring algorithm change can be checked against real browser/API captures.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from score_holistic_sequence_mvp import (
    DEFAULT_SEMANTIC_PROFILE_JSON,
    _presence_ratio,
    load_semantic_profile,
    load_sequence,
    run_pair,
)


REPO_ROOT = Path("/data/WYC/signLanguage")
DEFAULT_WEB_ROOT = REPO_ROOT / "work/generated/web_scoring_mvp"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "work/generated/scoring_mvp_run3/web_replay_current"
DEFAULT_TEMPLATE_ROOT = REPO_ROOT / "work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results"


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _score_band(score: Optional[float]) -> str:
    if score is None:
        return "error"
    if score >= 75.0:
        return "normal_like"
    if score >= 60.0:
        return "borderline"
    return "low"


def _request_sort_key(path: Path) -> str:
    return path.parent.name


def _iter_result_paths(web_root: Path) -> List[Path]:
    return sorted(web_root.glob("web_*/scoring_result.json"), key=_request_sort_key)


def filter_result_paths(
    paths: Iterable[Path],
    *,
    request_ids: Optional[Sequence[str]] = None,
    since_request_id: str = "",
    latest: int = 0,
) -> List[Path]:
    selected = sorted(paths, key=_request_sort_key)
    request_id_set = {str(item) for item in (request_ids or []) if str(item)}
    if request_id_set:
        selected = [path for path in selected if path.parent.name in request_id_set]
    if since_request_id:
        selected = [path for path in selected if path.parent.name > since_request_id]
    if latest > 0:
        selected = selected[-latest:]
    return selected


def _template_path(template_root: Optional[Path], word: str, fallback: Path) -> tuple[Path, str]:
    if template_root is None:
        return fallback, "saved_standard_json"
    direct = template_root / word / f"{word}_holistic_results.json"
    if direct.exists():
        return direct, "template_root"
    folder = template_root / word
    matches = sorted(folder.glob("*_holistic_results.json")) if folder.exists() else []
    if matches:
        return matches[0], "template_root"
    return fallback, "saved_standard_json_fallback"


def replay_one(path: Path, semantic_profile_json: Path, template_root: Optional[Path] = None) -> Dict[str, Any]:
    stored = _load_json(path)
    request_id = str(stored.get("request_id") or path.parent.name)
    target_word = str(stored.get("target_word") or "")
    old_score = (((stored.get("score") or {}).get("prototype_score")))
    saved_standard_json = Path(stored.get("standard_json") or "")
    standard_json, standard_source = _template_path(template_root, target_word, saved_standard_json)
    query_json = Path(stored.get("query_json") or "")
    row: Dict[str, Any] = {
        "request_id": request_id,
        "generated_at": stored.get("generated_at"),
        "target_word": target_word,
        "frame_count": stored.get("frame_count"),
        "timeline_frame_count": stored.get("timeline_frame_count"),
        "capture_fps": stored.get("capture_fps"),
        "old_score": float(old_score) if old_score is not None else None,
        "old_band": _score_band(float(old_score) if old_score is not None else None),
        "standard_json": str(standard_json),
        "saved_standard_json": str(saved_standard_json),
        "standard_source": standard_source,
        "query_json": str(query_json),
        "error": "",
    }
    try:
        standard = load_sequence(standard_json, requested_mode="landmark")
        query = load_sequence(query_json, requested_mode="landmark")
        profile = load_semantic_profile(target_word, semantic_profile_json)
        result = run_pair(standard, query, semantic_profile=profile, enable_cross_check=False)
        query_presence = _presence_ratio(query)
        row.update(
            {
                "new_score": float(result["prototype_score"]),
                "new_band": _score_band(float(result["prototype_score"])),
                "score_delta": float(result["prototype_score"]) - float(old_score) if old_score is not None else None,
                "dtw_distance": float(result["dtw_distance"]),
                "normalized_distance": float(result["normalized_distance"]),
                "alignment_mode": (result.get("alignment_policy") or {}).get("mode"),
                "score_scale_reason": (result.get("score_scale") or {}).get("reason"),
                "query_left_hand_presence": float(query_presence.get("left_hand", 0.0)),
                "query_right_hand_presence": float(query_presence.get("right_hand", 0.0)),
                "query_pose_presence": float(query_presence.get("pose", 0.0)),
                "query_face_presence": float(query_presence.get("face", 0.0)),
                "query_hand_presence_max": max(float(query_presence.get("left_hand", 0.0)), float(query_presence.get("right_hand", 0.0))),
            }
        )
    except Exception as exc:
        row.update(
            {
                "new_score": None,
                "new_band": "error",
                "score_delta": None,
                "dtw_distance": None,
                "normalized_distance": None,
                "alignment_mode": "",
                "score_scale_reason": "",
                "query_left_hand_presence": None,
                "query_right_hand_presence": None,
                "query_pose_presence": None,
                "query_face_presence": None,
                "query_hand_presence_max": None,
                "error": str(exc),
            }
        )
    return row


def _mean(values: Sequence[float]) -> Optional[float]:
    clean = [float(value) for value in values if value is not None]
    return sum(clean) / len(clean) if clean else None


def summarize(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    by_word: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_word[str(row.get("target_word") or "unknown")].append(row)
    summary: Dict[str, Any] = {
        "samples": len(rows),
        "errors": sum(1 for row in rows if row.get("error")),
        "normal_like": sum(1 for row in rows if row.get("new_band") == "normal_like"),
        "borderline": sum(1 for row in rows if row.get("new_band") == "borderline"),
        "low": sum(1 for row in rows if row.get("new_band") == "low"),
        "old_score_mean": _mean([row.get("old_score") for row in rows if row.get("old_score") is not None]),
        "new_score_mean": _mean([row.get("new_score") for row in rows if row.get("new_score") is not None]),
        "by_word": {},
    }
    for word, items in sorted(by_word.items()):
        summary["by_word"][word] = {
            "samples": len(items),
            "normal_like": sum(1 for row in items if row.get("new_band") == "normal_like"),
            "borderline": sum(1 for row in items if row.get("new_band") == "borderline"),
            "low": sum(1 for row in items if row.get("new_band") == "low"),
            "old_score_mean": _mean([row.get("old_score") for row in items if row.get("old_score") is not None]),
            "new_score_mean": _mean([row.get("new_score") for row in items if row.get("new_score") is not None]),
            "hand_presence_mean": _mean([row.get("query_hand_presence_max") for row in items if row.get("query_hand_presence_max") is not None]),
        }
    return summary


def _fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def build_markdown(payload: Dict[str, Any]) -> str:
    summary = payload["summary"]
    rows = payload["rows"]
    lines: List[str] = []
    lines.append("# 网页测试样本当前算法回放")
    lines.append("")
    lines.append(f"- 生成时间：`{payload['generated_at']}`")
    lines.append(f"- Web 样本根目录：`{payload['web_root']}`")
    lines.append(f"- 语义 profile：`{payload['semantic_profile_json']}`")
    filters = payload.get("filters") or {}
    if any(filters.values()):
        lines.append(
            f"- 样本过滤：latest=`{filters.get('latest') or 0}`，"
            f"since_request_id=`{filters.get('since_request_id') or ''}`，"
            f"request_ids=`{', '.join(filters.get('request_ids') or []) or '-'}`"
        )
    if payload.get("template_root"):
        lines.append(f"- 标准库覆盖：`{payload['template_root']}`")
        lines.append("- 口径：query 复用保存的网页/API Holistic JSON，standard 改用当前标准库，模拟当前后端在线评分。")
    else:
        lines.append("- 口径：复用保存的 `standard_json/query_json`，不重新运行浏览器采集。")
    lines.append("- 分段：`normal_like >= 75`，`60 <= borderline < 75`，`low < 60`；这仍不是正式用户阈值。")
    lines.append("")
    lines.append("## 总览")
    lines.append("")
    lines.append(f"- 样本数：`{summary['samples']}`")
    lines.append(f"- 错误数：`{summary['errors']}`")
    lines.append(f"- 当前正常区间：`{summary['normal_like']}`")
    lines.append(f"- 当前边界区间：`{summary['borderline']}`")
    lines.append(f"- 当前低分区间：`{summary['low']}`")
    lines.append(f"- 旧均分：`{_fmt(summary['old_score_mean'])}`")
    lines.append(f"- 新均分：`{_fmt(summary['new_score_mean'])}`")
    lines.append("")
    lines.append("## 分词条")
    lines.append("")
    lines.append("| 词条 | 样本数 | 正常 | 边界 | 低分 | 旧均分 | 新均分 | 手部覆盖均值 |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for word, item in summary["by_word"].items():
        lines.append(
            f"| {word} | {item['samples']} | {item['normal_like']} | {item['borderline']} | {item['low']} | "
            f"{_fmt(item['old_score_mean'])} | {_fmt(item['new_score_mean'])} | {_fmt(item['hand_presence_mean'])} |"
        )
    lines.append("")
    lines.append("## 最新样本")
    lines.append("")
    lines.append("| request | 词条 | 帧数 | 旧分 | 新分 | 分段 | 手部覆盖 | 对齐 |")
    lines.append("|---|---|---:|---:|---:|---|---:|---|")
    for row in rows[-20:]:
        lines.append(
            f"| {row['request_id']} | {row['target_word']} | {row.get('frame_count')} | "
            f"{_fmt(row.get('old_score'))} | {_fmt(row.get('new_score'))} | {row.get('new_band')} | "
            f"{_fmt(row.get('query_hand_presence_max'))} | {row.get('alignment_mode')} |"
        )
    lines.append("")
    lines.append("## 低分样本排查")
    lines.append("")
    low_rows = sorted(
        [row for row in rows if row.get("new_band") == "low" and not row.get("error")],
        key=lambda row: float(row.get("new_score") or 0.0),
    )[:20]
    if not low_rows:
        lines.append("- 无低分样本。")
    else:
        for row in low_rows:
            lines.append(
                f"- `{row['request_id']}` / {row['target_word']}: score=`{_fmt(row.get('new_score'))}`, "
                f"frames=`{row.get('frame_count')}`, hand_presence=`{_fmt(row.get('query_hand_presence_max'))}`, "
                f"mode=`{row.get('alignment_mode')}`"
            )
    lines.append("")
    return "\n".join(lines)


def write_outputs(
    rows: Sequence[Dict[str, Any]],
    output_dir: Path,
    web_root: Path,
    semantic_profile_json: Path,
    template_root: Optional[Path] = None,
    filters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "web_root": str(web_root),
        "semantic_profile_json": str(semantic_profile_json),
        "template_root": str(template_root) if template_root is not None else "",
        "filters": filters or {},
        "summary": summarize(rows),
        "rows": list(rows),
    }
    json_path = output_dir / "web_replay_current.json"
    md_path = output_dir / "web_replay_current.md"
    csv_path = output_dir / "web_replay_current.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(build_markdown(payload), encoding="utf-8")
    fields = list(rows[0].keys()) if rows else []
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    payload["json_path"] = str(json_path)
    payload["md_path"] = str(md_path)
    payload["csv_path"] = str(csv_path)
    return payload


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="用当前评分模块回放已保存的网页样本")
    parser.add_argument("--web-root", default=str(DEFAULT_WEB_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument(
        "--template-root",
        default="",
        help="可选：用指定标准库替换历史 scoring_result.json 里的 standard_json，模拟当前后端评分。",
    )
    parser.add_argument("--latest", type=int, default=0, help="只回放排序后的最近 N 条样本。")
    parser.add_argument("--since-request-id", default="", help="只回放 request_id 字典序大于该值的样本。")
    parser.add_argument("--request-ids", nargs="*", default=[], help="只回放指定 request_id。")
    args = parser.parse_args(argv)

    web_root = Path(args.web_root)
    semantic_profile_json = Path(args.semantic_profile_json)
    template_root = Path(args.template_root) if args.template_root else None
    paths = filter_result_paths(
        _iter_result_paths(web_root),
        request_ids=args.request_ids,
        since_request_id=args.since_request_id,
        latest=args.latest,
    )
    filters = {"latest": args.latest, "since_request_id": args.since_request_id, "request_ids": list(args.request_ids)}
    rows = [replay_one(path, semantic_profile_json, template_root=template_root) for path in paths]
    payload = write_outputs(rows, Path(args.output_dir), web_root, semantic_profile_json, template_root=template_root, filters=filters)
    print(f"已生成网页回放 JSON：{payload['json_path']}")
    print(f"已生成网页回放报告：{payload['md_path']}")
    print(f"已生成网页回放 CSV：{payload['csv_path']}")
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

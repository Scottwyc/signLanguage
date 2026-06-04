#!/usr/bin/env python3
"""Stress-test flower/jump scoring against webcam framing geometry changes.

The pose robustness gate already covers seated posture, hand shifts, local hand
scale, and small hand jitter. This gate targets a different browser-camera
risk: the whole person can appear closer/farther from the camera, slightly
tilted, or framed off-center. Mild versions of those changes should keep the
core flower/jump semantics scoreable.

This script edits cached skeleton sequences in memory only. It does not call
/api/score, run Holistic, move marker, or restart 5080.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

import numpy as np

from score_holistic_sequence_mvp import (
    DEFAULT_SEMANTIC_PROFILE_JSON,
    FrameFeature,
    SequenceData,
    _clone_frame,
    _clone_sequence,
    _profile_summary,
    load_semantic_profile,
    load_sequence,
    run_pair,
)


REPO_ROOT = Path("/data/WYC/signLanguage")
DEFAULT_TEMPLATE_ROOT = REPO_ROOT / "work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results"
DEFAULT_OUTPUT_BASE = REPO_ROOT / "work/generated/scoring_mvp_run3"
DEFAULT_BACKEND_URL = "http://127.0.0.1:5080"
DEFAULT_WORDS = ["花", "跳"]
COORD_GROUPS = ["pose", "left_hand", "right_hand", "face"]
HAND_COORD_GROUPS = ["left_hand", "right_hand"]


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


def _group_coords(frame: FrameFeature, group: str) -> Optional[np.ndarray]:
    if group not in frame.groups:
        return None
    values = frame.vector[frame.groups[group]]
    if values.size % 3 != 0:
        return None
    return values.reshape(-1, 3).copy()


def _group_mask(frame: FrameFeature, group: str) -> Optional[np.ndarray]:
    if group not in frame.groups:
        return None
    mask = frame.mask[frame.groups[group]]
    if mask.size % 3 != 0:
        return None
    return mask.reshape(-1, 3).mean(axis=1) > 0.5


def _set_group_coords(frame: FrameFeature, vector: np.ndarray, group: str, coords: np.ndarray) -> None:
    if group not in frame.groups:
        return
    sl = frame.groups[group]
    if vector[sl].size != coords.size:
        return
    vector[sl] = coords.reshape(-1)


def _visible_center(seq: SequenceData, groups: Sequence[str]) -> np.ndarray:
    points: List[np.ndarray] = []
    for frame in seq.features:
        for group in groups:
            coords = _group_coords(frame, group)
            mask = _group_mask(frame, group)
            if coords is None or mask is None or not mask.any():
                continue
            points.append(coords[mask, :2])
    if not points:
        return np.zeros(2, dtype=np.float32)
    return np.concatenate(points, axis=0).mean(axis=0).astype(np.float32)


def _transform_geometry(
    seq: SequenceData,
    name: str,
    *,
    groups: Sequence[str],
    scale: float = 1.0,
    rotate_deg: float = 0.0,
    dx: float = 0.0,
    dy: float = 0.0,
) -> SequenceData:
    center = _visible_center(seq, groups)
    theta = math.radians(float(rotate_deg))
    rot = np.asarray(
        [[math.cos(theta), -math.sin(theta)], [math.sin(theta), math.cos(theta)]],
        dtype=np.float32,
    )
    delta = np.asarray([dx, dy], dtype=np.float32)
    items: List[FrameFeature] = []
    for frame in seq.features:
        vector = frame.vector.copy()
        for group in groups:
            coords = _group_coords(frame, group)
            mask = _group_mask(frame, group)
            if coords is None or mask is None or not mask.any():
                continue
            xy = (coords[mask, :2] - center) * float(scale)
            coords[mask, :2] = xy @ rot.T + center + delta
            coords[mask, 2] = coords[mask, 2] * float(scale)
            _set_group_coords(frame, vector, group, coords)
        items.append(_clone_frame(frame, vector=vector))
    return _clone_sequence(seq, name, items)


QueryFactory = Callable[[SequenceData], SequenceData]


def _spec(
    variant: str,
    kind: str,
    query: QueryFactory,
    rationale: str,
    min_score: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": kind,
        "query": query,
        "min_score": min_score,
        "gated": kind == "positive",
        "rationale": rationale,
    }


def _variant_specs(min_score: float) -> List[Dict[str, Any]]:
    return [
        _spec(
            "self",
            "positive",
            lambda seq: _clone_sequence(seq, "self", seq.features),
            "同一骨架重算基线。",
            min_score=95.0,
        ),
        _spec(
            "global_zoom_out_0.75",
            "positive",
            lambda seq: _transform_geometry(seq, "global_zoom_out_0.75", groups=COORD_GROUPS, scale=0.75),
            "用户离镜头更远，整人骨架约缩小到 75%。",
            min_score=min_score,
        ),
        _spec(
            "global_zoom_in_1.25",
            "positive",
            lambda seq: _transform_geometry(seq, "global_zoom_in_1.25", groups=COORD_GROUPS, scale=1.25),
            "用户离镜头更近，整人骨架约放大到 125%。",
            min_score=min_score,
        ),
        _spec(
            "global_rotate_8deg",
            "positive",
            lambda seq: _transform_geometry(seq, "global_rotate_8deg", groups=COORD_GROUPS, rotate_deg=8.0),
            "摄像头或身体轻微倾斜约 8 度。",
            min_score=min_score,
        ),
        _spec(
            "framing_shift_zoom_in",
            "positive",
            lambda seq: _transform_geometry(
                seq,
                "framing_shift_zoom_in",
                groups=COORD_GROUPS,
                scale=1.12,
                dx=0.20,
                dy=-0.18,
            ),
            "画面偏右上且略近。",
            min_score=min_score,
        ),
        _spec(
            "framing_shift_zoom_out",
            "positive",
            lambda seq: _transform_geometry(
                seq,
                "framing_shift_zoom_out",
                groups=COORD_GROUPS,
                scale=0.88,
                dx=-0.25,
                dy=0.20,
            ),
            "画面偏左下且略远。",
            min_score=min_score,
        ),
        _spec(
            "hand_region_zoom_in_1.18",
            "positive",
            lambda seq: _transform_geometry(seq, "hand_region_zoom_in_1.18", groups=HAND_COORD_GROUPS, scale=1.18),
            "手部区域因取景略近而放大。",
            min_score=min_score,
        ),
        _spec(
            "hand_region_zoom_out_0.82",
            "positive",
            lambda seq: _transform_geometry(seq, "hand_region_zoom_out_0.82", groups=HAND_COORD_GROUPS, scale=0.82),
            "手部区域因取景略远而缩小。",
            min_score=min_score,
        ),
        _spec(
            "extreme_zoom_in_1.40_diag",
            "diagnostic",
            lambda seq: _transform_geometry(
                seq,
                "extreme_zoom_in_1.40_diag",
                groups=COORD_GROUPS,
                scale=1.40,
                dx=0.35,
                dy=-0.30,
            ),
            "极端近距离和偏移，只记录诊断，不作为通过条件。",
        ),
        _spec(
            "extreme_zoom_out_0.60_diag",
            "diagnostic",
            lambda seq: _transform_geometry(
                seq,
                "extreme_zoom_out_0.60_diag",
                groups=COORD_GROUPS,
                scale=0.60,
                dx=-0.40,
                dy=0.35,
            ),
            "极端远距离和偏移，只记录诊断，不作为通过条件。",
        ),
    ]


def _run_word(
    word: str,
    template_root: Path,
    semantic_profile_json: Path,
    feature_mode: str,
    min_score: float,
) -> Dict[str, Any]:
    standard_json = _template_json(template_root, word)
    standard = load_sequence(standard_json, feature_mode, force_bbox=False)
    profile = load_semantic_profile(word, semantic_profile_json)
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(min_score):
        query = spec["query"](standard)
        result = run_pair(standard, query, semantic_profile=profile, enable_cross_check=False)
        score_scale = result.get("score_scale") or {}
        row = {
            "variant": spec["variant"],
            "kind": spec["kind"],
            "gated": bool(spec["gated"]),
            "min_score": spec.get("min_score"),
            "rationale": spec["rationale"],
            "score": float(result["prototype_score"]),
            "dtw_distance": float(result["dtw_distance"]),
            "normalized_distance": float(result["normalized_distance"]),
            "query_length": len(query.features),
            "alignment_policy": result.get("alignment_policy"),
            "capture_quality": score_scale.get("capture_quality"),
            "semantic_floor": score_scale.get("semantic_floor"),
        }
        row["passed"] = row["kind"] != "positive" or float(row["score"]) >= float(row["min_score"])
        rows.append(row)
    positive_rows = [row for row in rows if row["kind"] == "positive"]
    diagnostic_rows = [row for row in rows if row["kind"] == "diagnostic"]
    weakest_positive = min(positive_rows, key=lambda row: float(row["score"])) if positive_rows else None
    weakest_diagnostic = min(diagnostic_rows, key=lambda row: float(row["score"])) if diagnostic_rows else None
    return {
        "word": word,
        "standard_json": str(standard_json),
        "standard_length": len(standard.features),
        "semantic_profile": _profile_summary(profile),
        "min_required_score": min_score,
        "gate_pass": all(bool(row["passed"]) for row in positive_rows),
        "weakest_positive_score": float(weakest_positive["score"]) if weakest_positive else None,
        "weakest_positive_variant": weakest_positive["variant"] if weakest_positive else "",
        "weakest_diagnostic_score": float(weakest_diagnostic["score"]) if weakest_diagnostic else None,
        "weakest_diagnostic_variant": weakest_diagnostic["variant"] if weakest_diagnostic else "",
        "variants": rows,
    }


def _write_rows_csv(path: Path, results: Sequence[Dict[str, Any]]) -> None:
    fields = [
        "word",
        "variant",
        "kind",
        "gated",
        "passed",
        "score",
        "min_score",
        "dtw_distance",
        "normalized_distance",
        "query_length",
        "alignment_mode",
        "capture_quality_status",
        "capture_quality_reason",
        "semantic_floor_source",
        "semantic_floor_reason",
        "rationale",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in results:
            for row in item["variants"]:
                quality = row.get("capture_quality") or {}
                floor = row.get("semantic_floor") or {}
                policy = row.get("alignment_policy") or {}
                writer.writerow(
                    {
                        "word": item["word"],
                        "variant": row.get("variant"),
                        "kind": row.get("kind"),
                        "gated": row.get("gated"),
                        "passed": row.get("passed"),
                        "score": row.get("score"),
                        "min_score": row.get("min_score"),
                        "dtw_distance": row.get("dtw_distance"),
                        "normalized_distance": row.get("normalized_distance"),
                        "query_length": row.get("query_length"),
                        "alignment_mode": policy.get("mode"),
                        "capture_quality_status": quality.get("status"),
                        "capture_quality_reason": quality.get("reason"),
                        "semantic_floor_source": floor.get("source"),
                        "semantic_floor_reason": floor.get("reason"),
                        "rationale": row.get("rationale"),
                    }
                )


def _build_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# 花/跳取景尺度与轻微旋转鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，在骨架坐标层面模拟整人 zoom、轻微旋转和画面偏移；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：用户离镜头略远/略近、画面偏移或轻微倾斜时，`花/跳` 核心语义仍保持可评分。",
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
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向取景扰动 | 诊断最低分 | 最弱诊断扰动 | 门槛 |")
    lines.append("|---|---|---:|---|---:|---|---:|")
    for item in payload["results"]:
        lines.append(
            f"| {item['word']} | {'PASS' if item['gate_pass'] else 'FAIL'} | "
            f"{_fmt(item['weakest_positive_score'])} | {item['weakest_positive_variant']} | "
            f"{_fmt(item['weakest_diagnostic_score'])} | {item['weakest_diagnostic_variant']} | "
            f"{_fmt(item['min_required_score'])} |"
        )
    lines.append("")
    lines.append("## 分项明细")
    for item in payload["results"]:
        lines.extend(["", f"### {item['word']}", "", f"- 标准序列：`{item['standard_json']}`", ""])
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | normalized_distance | alignment | capture_quality | semantic_floor | 说明 |")
        lines.append("|---|---|---|---:|---|---:|---|---|---|---|")
        for row in sorted(item["variants"], key=lambda x: (x["kind"], float(x["score"]))):
            quality = row.get("capture_quality") or {}
            floor = row.get("semantic_floor") or {}
            policy = row.get("alignment_policy") or {}
            if row["kind"] == "positive":
                threshold = f">= {row.get('min_score')}"
                status = "PASS" if row["passed"] else "FAIL"
            else:
                threshold = "diagnostic"
                status = "DIAG"
            lines.append(
                f"| {row['variant']} | {row['kind']} | {status} | {_fmt(row['score'])} | "
                f"{threshold} | {_fmt(row['normalized_distance'], 6)} | {policy.get('mode') or '-'} | "
                f"{quality.get('status') or '-'} | {floor.get('source') or '-'} | {row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 正向扰动覆盖轻中度取景变化；极端 zoom/pan 只作为诊断，不替代真实网页摄像头样本。",
            "- 若该门失败，优先检查全局坐标是否重新主导了手部局部几何、two-hand relation 或语义 floor。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run framing geometry robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_framing_robustness_gate_current"))
    parser.add_argument("--words", nargs="+", default=DEFAULT_WORDS)
    parser.add_argument("--feature-mode", choices=["auto", "landmark", "bbox"], default="auto")
    parser.add_argument("--min-score", type=float, default=70.0)
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--status-timeout-sec", type=float, default=3.0)
    args = parser.parse_args(argv)

    template_root = Path(args.template_root)
    semantic_profile_json = Path(args.semantic_profile_json)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = [
        _run_word(
            word=word,
            template_root=template_root,
            semantic_profile_json=semantic_profile_json,
            feature_mode=args.feature_mode,
            min_score=args.min_score,
        )
        for word in args.words
    ]
    backend_status = _load_backend_status(args.backend_url, args.status_timeout_sec)
    passed = all(bool(item["gate_pass"]) for item in results)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "claim_policy": "synthetic framing geometry robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "min_score": args.min_score,
        "backend_status": backend_status,
        "passed": passed,
        "results": results,
    }

    json_path = output_dir / "flower_jump_framing_robustness_gate.json"
    md_path = output_dir / "flower_jump_framing_robustness_gate.md"
    csv_path = output_dir / "flower_jump_framing_robustness_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳取景鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳取景鲁棒性报告：{md_path}")
    print(f"已生成花/跳取景鲁棒性 CSV：{csv_path}")
    print(f"综合状态：{'PASS' if passed else 'FAIL'}")
    for item in results:
        print(
            f"- {item['word']}: {'PASS' if item['gate_pass'] else 'FAIL'} "
            f"positive_min={_fmt(item['weakest_positive_score'])} "
            f"weakest={item['weakest_positive_variant']} "
            f"diagnostic_min={_fmt(item['weakest_diagnostic_score'])}"
        )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Stress-test flower/jump scoring against local hand-shape scale changes.

Different browser users have different hand sizes, hand-camera distances, and
slight perspective distortion. Earlier pose/framing gates moved hand landmarks
but did not recompute the derived hand-shape groups, so they did not directly
stress the local hand-shape path. This gate edits cached hand landmarks in
memory, recomputes left/right hand-shape features, and verifies mild local hand
scale/aspect changes remain scoreable.

This script does not call /api/score, run Holistic, move marker, or restart
5080.
"""

from __future__ import annotations

import argparse
import csv
import json
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
    _hand_shape_feature,
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
HAND_GROUPS = ["left_hand", "right_hand"]


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


def _hand_array(frame: FrameFeature, group: str) -> tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    if group not in frame.groups:
        return None, None
    sl = frame.groups[group]
    values = frame.vector[sl]
    masks = frame.mask[sl]
    if values.size % 3 != 0 or masks.size % 3 != 0:
        return None, None
    return values.reshape(-1, 3).copy(), masks.reshape(-1, 3).mean(axis=1) > 0.5


def _set_hand_group(
    frame: FrameFeature,
    vector: np.ndarray,
    mask: np.ndarray,
    group: str,
    coords: np.ndarray,
    valid: np.ndarray,
) -> None:
    sl = frame.groups[group]
    vector[sl] = coords.reshape(-1)
    mask[sl] = np.repeat(valid.astype(np.float32), 3)
    shape_group = f"{group}_shape"
    if shape_group not in frame.groups:
        return
    shape, shape_mask = _hand_shape_feature(coords, valid.astype(np.float32))
    shape_sl = frame.groups[shape_group]
    if vector[shape_sl].size == shape.size:
        vector[shape_sl] = shape.reshape(-1)
        mask[shape_sl] = shape_mask.reshape(-1)


def _scale_hands(
    seq: SequenceData,
    name: str,
    *,
    groups: Sequence[str],
    sx: float = 1.0,
    sy: float = 1.0,
    sz: float = 1.0,
) -> SequenceData:
    factors = np.asarray([sx, sy, sz], dtype=np.float32)
    items: List[FrameFeature] = []
    for frame in seq.features:
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        presence = dict(frame.presence)
        for group in groups:
            coords, valid = _hand_array(frame, group)
            if coords is None or valid is None or not valid.any():
                continue
            center = coords[0].copy() if valid[0] else coords[valid].mean(axis=0)
            coords[valid] = center + factors * (coords[valid] - center)
            _set_hand_group(frame, vector, mask, group, coords, valid)
            presence[group] = bool(valid.any())
        item = _clone_frame(frame, vector=vector, mask=mask)
        item.presence = presence
        items.append(item)
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
            "both_hands_uniform_scale_0.75",
            "positive",
            lambda seq: _scale_hands(seq, "both_hands_uniform_scale_0.75", groups=HAND_GROUPS, sx=0.75, sy=0.75, sz=0.75),
            "双手局部大小缩小到 75%，并重算 hand-shape。",
            min_score=min_score,
        ),
        _spec(
            "both_hands_uniform_scale_1.30",
            "positive",
            lambda seq: _scale_hands(seq, "both_hands_uniform_scale_1.30", groups=HAND_GROUPS, sx=1.30, sy=1.30, sz=1.30),
            "双手局部大小放大到 130%，并重算 hand-shape。",
            min_score=min_score,
        ),
        _spec(
            "both_hands_aspect_x1.15_y0.90",
            "positive",
            lambda seq: _scale_hands(seq, "both_hands_aspect_x1.15_y0.90", groups=HAND_GROUPS, sx=1.15, sy=0.90),
            "轻微横向拉宽/纵向压缩，模拟手掌角度或透视变化。",
            min_score=min_score,
        ),
        _spec(
            "both_hands_aspect_x0.90_y1.15",
            "positive",
            lambda seq: _scale_hands(seq, "both_hands_aspect_x0.90_y1.15", groups=HAND_GROUPS, sx=0.90, sy=1.15),
            "轻微横向压缩/纵向拉长，模拟手掌角度或透视变化。",
            min_score=min_score,
        ),
        _spec(
            "right_hand_aspect_x1.20_y0.85",
            "positive",
            lambda seq: _scale_hands(seq, "right_hand_aspect_x1.20_y0.85", groups=["right_hand"], sx=1.20, sy=0.85),
            "右手核心手形轻微透视变化。",
            min_score=min_score,
        ),
        _spec(
            "right_hand_aspect_x0.85_y1.20",
            "positive",
            lambda seq: _scale_hands(seq, "right_hand_aspect_x0.85_y1.20", groups=["right_hand"], sx=0.85, sy=1.20),
            "右手核心手形轻微反向透视变化。",
            min_score=min_score,
        ),
        _spec(
            "left_hand_uniform_scale_0.80",
            "positive",
            lambda seq: _scale_hands(seq, "left_hand_uniform_scale_0.80", groups=["left_hand"], sx=0.80, sy=0.80, sz=0.80),
            "左手局部大小略小；对跳的地面手和花的非核心手都不应破坏评分。",
            min_score=min_score,
        ),
        _spec(
            "left_hand_uniform_scale_1.25",
            "positive",
            lambda seq: _scale_hands(seq, "left_hand_uniform_scale_1.25", groups=["left_hand"], sx=1.25, sy=1.25, sz=1.25),
            "左手局部大小略大；对跳的地面手和花的非核心手都不应破坏评分。",
            min_score=min_score,
        ),
        _spec(
            "both_hands_uniform_scale_0.55_diagnostic",
            "diagnostic",
            lambda seq: _scale_hands(seq, "both_hands_uniform_scale_0.55_diagnostic", groups=HAND_GROUPS, sx=0.55, sy=0.55, sz=0.55),
            "极端手部缩小，只记录诊断边界。",
        ),
        _spec(
            "both_hands_uniform_scale_1.60_diagnostic",
            "diagnostic",
            lambda seq: _scale_hands(seq, "both_hands_uniform_scale_1.60_diagnostic", groups=HAND_GROUPS, sx=1.60, sy=1.60, sz=1.60),
            "极端手部放大，只记录诊断边界。",
        ),
        _spec(
            "both_hands_aspect_x1.60_y0.55_diagnostic",
            "diagnostic",
            lambda seq: _scale_hands(seq, "both_hands_aspect_x1.60_y0.55_diagnostic", groups=HAND_GROUPS, sx=1.60, sy=0.55),
            "强透视形变，只记录诊断边界。",
        ),
        _spec(
            "both_hands_aspect_x0.55_y1.60_diagnostic",
            "diagnostic",
            lambda seq: _scale_hands(seq, "both_hands_aspect_x0.55_y1.60_diagnostic", groups=HAND_GROUPS, sx=0.55, sy=1.60),
            "强反向透视形变，只记录诊断边界。",
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
        "# 花/跳手形局部尺度鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，在手部局部坐标层面缩放/拉伸并重算 `left_hand_shape/right_hand_shape`；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：不同用户手掌大小、手离镜头远近或轻微透视变化时，`花/跳` 核心手形仍保持可评分；极端形变只记录诊断边界。",
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
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向手形尺度 | 诊断最低分 | 最弱诊断尺度 | 门槛 |")
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
            "- 正向扰动覆盖轻中度手掌大小和透视变化，并强制重算派生手形特征。",
            "- 该门补足了旧 pose/framing 门只改 hand 坐标、不直接验证 hand-shape 派生特征的盲点。",
            "- 该门是合成鲁棒性压力测试，不能替代真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run local hand-shape scale robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_hand_shape_scale_robustness_gate_current"))
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
        "claim_policy": "synthetic local hand-shape scale robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "min_score": args.min_score,
        "backend_status": backend_status,
        "passed": passed,
        "results": results,
    }

    json_path = output_dir / "flower_jump_hand_shape_scale_robustness_gate.json"
    md_path = output_dir / "flower_jump_hand_shape_scale_robustness_gate.md"
    csv_path = output_dir / "flower_jump_hand_shape_scale_robustness_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳手形尺度鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳手形尺度鲁棒性报告：{md_path}")
    print(f"已生成花/跳手形尺度鲁棒性 CSV：{csv_path}")
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

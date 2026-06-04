#!/usr/bin/env python3
"""Stress-test flower/jump scoring against browser mirror-like x flips.

The gate targets a webcam-specific risk: user-facing cameras and previews often
look mirrored. A pure horizontal coordinate flip should not break flower/jump
scoring. Full left/right role swaps are reported as diagnostics because they
change word-specific hand roles for signs such as jump.

This script only reads cached Holistic JSON and edits skeleton features in
memory. It does not call /api/score, run Holistic, move marker, or restart 5080.
"""

from __future__ import annotations

import argparse
import csv
import json
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import numpy as np

from score_holistic_sequence_mvp import (
    DEFAULT_SEMANTIC_PROFILE_JSON,
    FrameFeature,
    SequenceData,
    _profile_summary,
    _sequence_with_relative_motion_features,
    load_semantic_profile,
    load_sequence,
    run_pair,
)


REPO_ROOT = Path("/data/WYC/signLanguage")
DEFAULT_TEMPLATE_ROOT = REPO_ROOT / "work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results"
DEFAULT_OUTPUT_BASE = REPO_ROOT / "work/generated/scoring_mvp_run3"
DEFAULT_BACKEND_URL = "http://127.0.0.1:5080"
DEFAULT_WORDS = ["花", "跳"]
BASE_GROUPS = ["pose", "left_hand", "right_hand", "left_hand_shape", "right_hand_shape", "face"]
COORD_GROUPS = ["pose", "left_hand", "right_hand", "face"]
SWAP_PAIRS = [("left_hand", "right_hand"), ("left_hand_shape", "right_hand_shape")]


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


def _strip_to_base_groups(seq: SequenceData) -> SequenceData:
    items: List[FrameFeature] = []
    for frame in seq.features:
        parts: List[np.ndarray] = []
        masks: List[np.ndarray] = []
        groups: Dict[str, slice] = {}
        start = 0
        for group in BASE_GROUPS:
            if group not in frame.groups:
                continue
            sl = frame.groups[group]
            vector = frame.vector[sl].copy()
            mask = frame.mask[sl].copy()
            groups[group] = slice(start, start + vector.size)
            start += vector.size
            parts.append(vector)
            masks.append(mask)
        items.append(
            FrameFeature(
                frame_idx=frame.frame_idx,
                timestamp_sec=frame.timestamp_sec,
                vector=np.concatenate(parts).astype(np.float32),
                mask=np.concatenate(masks).astype(np.float32),
                groups=groups,
                presence=dict(frame.presence),
                frame_weight=float(frame.frame_weight),
                semantic_phase=float(frame.semantic_phase),
            )
        )
    return SequenceData(seq.source, seq.mode, seq.fps, seq.total_frames, items)


def _mirror_x_group(vector: np.ndarray, mask: np.ndarray, sl: slice) -> None:
    values = vector[sl]
    if values.size % 3 != 0:
        return
    coords = values.reshape(-1, 3).copy()
    coord_mask = mask[sl].reshape(-1, 3).mean(axis=1) > 0.5
    coords[coord_mask, 0] *= -1.0
    vector[sl] = coords.reshape(-1)


def _transform_sequence(
    seq: SequenceData,
    name: str,
    *,
    mirror_x: bool,
    swap_labels: bool,
    profile: Any,
) -> SequenceData:
    base = _strip_to_base_groups(seq)
    items: List[FrameFeature] = []
    for frame in base.features:
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        groups = dict(frame.groups)
        presence = dict(frame.presence)
        if mirror_x:
            for group in COORD_GROUPS:
                if group in groups:
                    _mirror_x_group(vector, mask, groups[group])
        if swap_labels:
            for left, right in SWAP_PAIRS:
                if left not in groups or right not in groups:
                    continue
                left_sl = groups[left]
                right_sl = groups[right]
                left_vector = vector[left_sl].copy()
                right_vector = vector[right_sl].copy()
                left_mask = mask[left_sl].copy()
                right_mask = mask[right_sl].copy()
                vector[left_sl] = right_vector
                vector[right_sl] = left_vector
                mask[left_sl] = right_mask
                mask[right_sl] = left_mask
            presence["left_hand"], presence["right_hand"] = (
                bool(presence.get("right_hand", False)),
                bool(presence.get("left_hand", False)),
            )
        items.append(
            FrameFeature(
                frame_idx=frame.frame_idx,
                timestamp_sec=frame.timestamp_sec,
                vector=vector,
                mask=mask,
                groups=groups,
                presence=presence,
                frame_weight=float(frame.frame_weight),
                semantic_phase=float(frame.semantic_phase),
            )
        )
    transformed = SequenceData(
        source=f"{base.source}::{name}",
        mode=base.mode,
        fps=base.fps,
        total_frames=base.total_frames,
        features=items,
    )
    return _sequence_with_relative_motion_features(transformed, profile)


def _variant_specs() -> List[Dict[str, Any]]:
    return [
        {
            "variant": "self_recomputed",
            "kind": "positive",
            "mirror_x": False,
            "swap_labels": False,
            "min_score": 95.0,
            "expected": "same sequence should stay near perfect after feature recomputation",
        },
        {
            "variant": "mirror_x",
            "kind": "positive",
            "mirror_x": True,
            "swap_labels": False,
            "min_score": 70.0,
            "expected": "horizontal camera/previews should not break the sign semantics",
        },
        {
            "variant": "swap_labels_diagnostic",
            "kind": "diagnostic",
            "mirror_x": False,
            "swap_labels": True,
            "expected": "left/right role swap diagnostic; not used as a pass/fail gate",
        },
        {
            "variant": "mirror_x_swap_labels_diagnostic",
            "kind": "diagnostic",
            "mirror_x": True,
            "swap_labels": True,
            "expected": "combined mirror and role swap diagnostic; not used as a pass/fail gate",
        },
    ]


def _run_word(
    word: str,
    template_root: Path,
    semantic_profile_json: Path,
    feature_mode: str,
) -> Dict[str, Any]:
    standard_json = _template_json(template_root, word)
    loaded_standard = load_sequence(standard_json, feature_mode, force_bbox=False)
    profile = load_semantic_profile(word, semantic_profile_json)
    standard = _transform_sequence(loaded_standard, "standard_base", mirror_x=False, swap_labels=False, profile=profile)
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs():
        query = _transform_sequence(
            loaded_standard,
            spec["variant"],
            mirror_x=bool(spec["mirror_x"]),
            swap_labels=bool(spec["swap_labels"]),
            profile=profile,
        )
        result = run_pair(standard, query, semantic_profile=profile, enable_cross_check=False)
        score_scale = result.get("score_scale") or {}
        row = {
            **spec,
            "score": float(result["prototype_score"]),
            "dtw_distance": float(result["dtw_distance"]),
            "normalized_distance": float(result["normalized_distance"]),
            "alignment_policy": result.get("alignment_policy"),
            "capture_quality": score_scale.get("capture_quality"),
            "semantic_floor": score_scale.get("semantic_floor"),
            "score_scale_reason": score_scale.get("reason"),
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
        "score",
        "dtw_distance",
        "normalized_distance",
        "min_score",
        "passed",
        "capture_quality_status",
        "capture_quality_reason",
        "semantic_floor_source",
        "semantic_floor_reason",
        "score_scale_reason",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in results:
            for row in item["variants"]:
                capture_quality = row.get("capture_quality") or {}
                semantic_floor = row.get("semantic_floor") or {}
                writer.writerow(
                    {
                        "word": item["word"],
                        "variant": row.get("variant"),
                        "kind": row.get("kind"),
                        "score": row.get("score"),
                        "dtw_distance": row.get("dtw_distance"),
                        "normalized_distance": row.get("normalized_distance"),
                        "min_score": row.get("min_score"),
                        "passed": row.get("passed"),
                        "capture_quality_status": capture_quality.get("status"),
                        "capture_quality_reason": capture_quality.get("reason"),
                        "semantic_floor_source": semantic_floor.get("source"),
                        "semantic_floor_reason": semantic_floor.get("reason"),
                        "score_scale_reason": row.get("score_scale_reason"),
                    }
                )


def _build_markdown(payload: Dict[str, Any]) -> str:
    lines = [
        "# 花/跳浏览器镜像鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 综合状态：`{'PASS' if payload['passed'] else 'FAIL'}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，在骨架特征层面做 x 轴镜像和左右标签诊断；不调用 `/api/score`，不重启 Holistic。",
        "- 门控：`mirror_x` 是正向鲁棒门；左右标签互换只记录诊断边界，因为它会改变 `跳` 的左右手角色语义。",
        "",
    ]
    backend = payload.get("backend_status") or {}
    if backend.get("ok"):
        data = backend.get("payload") or {}
        worker = data.get("worker") or {}
        scoring = data.get("scoring_module") or {}
        lines.append(
            f"- 5080 状态：worker=`{worker.get('status')}`，"
            f"worker_pid=`{((worker.get('ready_payload') or {}).get('pid'))}`，"
            f"reload_count=`{scoring.get('reload_count')}`，"
            f"last_reload_error=`{scoring.get('last_reload_error')}`"
        )
    else:
        lines.append(f"- 5080 状态：未读取或读取失败 `{backend.get('error') or '-'}`")
    lines.extend(
        [
            "",
            "## 结论",
            "",
            "| 目标词 | 状态 | 正向最低分 | 最弱正向变体 | 左右标签诊断最低分 | 最弱诊断变体 |",
            "|---|---|---:|---|---:|---|",
        ]
    )
    for item in payload["results"]:
        lines.append(
            f"| {item['word']} | {'PASS' if item['gate_pass'] else 'FAIL'} | "
            f"{_fmt(item.get('weakest_positive_score'))} | {item.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(item.get('weakest_diagnostic_score'))} | {item.get('weakest_diagnostic_variant') or '-'} |"
        )
    lines.extend(
        [
            "",
            "## 明细",
            "",
            "| 目标词 | 变体 | 类型 | 状态 | 分数 | normalized | 采集质量 | semantic floor |",
            "|---|---|---|---|---:|---:|---|---|",
        ]
    )
    for item in payload["results"]:
        for row in item["variants"]:
            capture_quality = row.get("capture_quality") or {}
            semantic_floor = row.get("semantic_floor") or {}
            lines.append(
                f"| {item['word']} | `{row.get('variant')}` | `{row.get('kind')}` | "
                f"{'PASS' if row.get('passed') else 'FAIL'} | {_fmt(row.get('score'))} | "
                f"{_fmt(row.get('normalized_distance'))} | "
                f"{capture_quality.get('status') or '-'} / {capture_quality.get('reason') or '-'} | "
                f"{semantic_floor.get('source') or '-'} / {semantic_floor.get('reason') or '-'} |"
            )
    return "\n".join(lines) + "\n"


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template-root", type=Path, default=DEFAULT_TEMPLATE_ROOT)
    parser.add_argument("--semantic-profile-json", type=Path, default=DEFAULT_SEMANTIC_PROFILE_JSON)
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--http-timeout-sec", type=float, default=3.0)
    parser.add_argument("--feature-mode", default="auto", choices=["auto", "landmark", "bbox"])
    parser.add_argument("--words", nargs="+", default=DEFAULT_WORDS)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_BASE / f"flower_jump_mirror_robustness_gate_{stamp}",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    backend_status = _load_backend_status(args.backend_url, args.http_timeout_sec)
    results = [
        _run_word(
            word,
            args.template_root,
            args.semantic_profile_json,
            args.feature_mode,
        )
        for word in args.words
    ]
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "passed": all(bool(item["gate_pass"]) for item in results),
        "template_root": str(args.template_root),
        "semantic_profile_json": str(args.semantic_profile_json),
        "backend_status": backend_status,
        "words": args.words,
        "results": results,
    }
    json_path = args.output_dir / "flower_jump_mirror_robustness_gate.json"
    md_path = args.output_dir / "flower_jump_mirror_robustness_gate.md"
    csv_path = args.output_dir / "flower_jump_mirror_robustness_gate.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)
    print(f"mirror robustness gate: {'PASS' if payload['passed'] else 'FAIL'}")
    print(f"JSON: {json_path}")
    print(f"MD: {md_path}")
    print(f"CSV: {csv_path}")
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

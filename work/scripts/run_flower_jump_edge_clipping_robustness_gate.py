#!/usr/bin/env python3
"""Stress-test flower/jump scoring against edge-of-frame landmark clipping.

Webcam recordings can place hands or upper body close to the frame boundary.
Some landmarks may disappear while the semantic core remains visible; those
cases should stay scoreable. If the clipped landmarks remove the flower opening
hand or the jump two-hand relation, the scorer should reject or recapture.

This script edits cached skeleton masks in memory only. It does not call
/api/score, run Holistic, move marker, or restart 5080.
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
ACCEPTED_NEGATIVE_QUALITY = {"needs_recapture", "semantic_mismatch"}
HAND_GROUPS = {"left_hand", "right_hand"}


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


def _presence_ratio(seq: SequenceData) -> Dict[str, float]:
    if not seq.features:
        return {"pose": 0.0, "left_hand": 0.0, "right_hand": 0.0, "face": 0.0}
    return {
        group: sum(1 for item in seq.features if item.presence.get(group)) / len(seq.features)
        for group in ["pose", "left_hand", "right_hand", "face"]
    }


def _group_arrays(frame: FrameFeature, group: str) -> tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    if group not in frame.groups:
        return None, None
    sl = frame.groups[group]
    values = frame.vector[sl]
    masks = frame.mask[sl]
    if values.size % 3 != 0 or masks.size % 3 != 0:
        return None, None
    return values.reshape(-1, 3).copy(), masks.reshape(-1, 3).mean(axis=1) > 0.5


def _set_group(
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
    if group not in HAND_GROUPS:
        return
    shape_group = f"{group}_shape"
    if shape_group not in frame.groups:
        return
    shape, shape_mask = _hand_shape_feature(coords, valid.astype(np.float32))
    shape_sl = frame.groups[shape_group]
    if vector[shape_sl].size == shape.size:
        vector[shape_sl] = shape.reshape(-1)
        mask[shape_sl] = shape_mask.reshape(-1)


def _clip_groups(seq: SequenceData, name: str, clips: Dict[str, Sequence[int]]) -> SequenceData:
    items: List[FrameFeature] = []
    for frame in seq.features:
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        presence = dict(frame.presence)
        for group, indices in clips.items():
            coords, valid = _group_arrays(frame, group)
            if coords is None or valid is None:
                continue
            coords = coords.copy()
            valid = valid.copy()
            for idx in indices:
                if 0 <= int(idx) < len(valid):
                    valid[int(idx)] = False
                    coords[int(idx)] = 0.0
            _set_group(frame, vector, mask, group, coords, valid)
            if group in {"pose", "face", "left_hand", "right_hand"}:
                presence[group] = bool(valid.any())
        item = _clone_frame(frame, vector=vector, mask=mask)
        item.presence = presence
        items.append(item)
    return _clone_sequence(seq, name, items)


def _all_indices(seq: SequenceData, group: str) -> List[int]:
    if not seq.features or group not in seq.features[0].groups:
        return []
    sl = seq.features[0].groups[group]
    return list(range(max(0, seq.features[0].vector[sl].size // 3)))


def _variant_specs(word: str, seq: SequenceData) -> List[Dict[str, Any]]:
    face_all = _all_indices(seq, "face")
    pose_all = _all_indices(seq, "pose")
    common_positive = [
        {
            "variant": "face_edge_out_of_frame",
            "kind": "positive",
            "clips": {"face": face_all},
            "min_score": 70.0,
            "rationale": "脸部出画面边缘，双手核心仍完整。",
        },
        {
            "variant": "upper_body_edge_out_of_frame",
            "kind": "positive",
            "clips": {"pose": pose_all, "face": face_all},
            "min_score": 70.0,
            "rationale": "上半身/脸部关键点不可见，但手部动作完整。",
        },
    ]
    if word == "花":
        return common_positive + [
            {
                "variant": "left_noncore_hand_edge_clip",
                "kind": "positive",
                "clips": {"left_hand": [0, 4, 8, 12, 16, 20]},
                "min_score": 70.0,
                "rationale": "非核心手靠近画面边缘，部分点不可见。",
            },
            {
                "variant": "right_opening_wrist_edge_clip",
                "kind": "positive",
                "clips": {"right_hand": [0]},
                "min_score": 70.0,
                "rationale": "开花手腕部边缘点不可见，但指尖张开过程仍可见。",
            },
            {
                "variant": "right_opening_outer_tips_edge_clip",
                "kind": "positive",
                "clips": {"right_hand": [4, 20]},
                "min_score": 70.0,
                "rationale": "开花手最外侧指尖边缘点不可见，核心开合仍保留。",
            },
            {
                "variant": "right_opening_all_tips_edge_clip",
                "kind": "negative",
                "clips": {"right_hand": [4, 8, 12, 16, 20]},
                "max_score": 45.0,
                "rationale": "开花手全部指尖出画面，无法验证张开/绽放核心。",
            },
            {
                "variant": "right_opening_outer_half_edge_clip",
                "kind": "negative",
                "clips": {"right_hand": [0, 1, 2, 3, 4, 13, 14, 15, 16, 17, 18, 19, 20]},
                "max_score": 45.0,
                "rationale": "开花手外半部分被画面裁掉，核心手形不可靠。",
            },
        ]
    if word == "跳":
        return common_positive + [
            {
                "variant": "left_ground_tips_edge_clip",
                "kind": "positive",
                "clips": {"left_hand": [4, 8, 12, 16, 20]},
                "min_score": 70.0,
                "rationale": "左手地面部分指尖靠近边缘，但地面关系仍可见。",
            },
            {
                "variant": "right_jumper_ring_pinky_edge_clip",
                "kind": "positive",
                "clips": {"right_hand": [13, 14, 15, 16, 17, 18, 19, 20]},
                "min_score": 70.0,
                "rationale": "右手非核心无名指/小指边缘点不可见，食指/中指小人仍可见。",
            },
            {
                "variant": "right_jumper_wrist_edge_clip",
                "kind": "positive",
                "clips": {"right_hand": [0]},
                "min_score": 70.0,
                "rationale": "右手腕部边缘点不可见，但食指/中指跳跃核心仍保留。",
            },
            {
                "variant": "left_ground_wrist_edge_clip",
                "kind": "negative",
                "clips": {"left_hand": [0]},
                "max_score": 45.0,
                "rationale": "左手地面支点出画面，双手关系不可靠。",
            },
            {
                "variant": "right_jumper_index_middle_tips_edge_clip",
                "kind": "negative",
                "clips": {"right_hand": [8, 12]},
                "max_score": 45.0,
                "rationale": "右手食指/中指小人的关键指尖出画面，跳跃语义缺失。",
            },
        ]
    return common_positive


def _row_passed(row: Dict[str, Any]) -> bool:
    score = float(row["score"])
    if row["kind"] == "positive":
        return score >= float(row["min_score"])
    quality = (row.get("capture_quality") or {}).get("status")
    return score <= float(row["max_score"]) or quality in ACCEPTED_NEGATIVE_QUALITY


def _run_word(
    word: str,
    template_root: Path,
    semantic_profile_json: Path,
    feature_mode: str,
) -> Dict[str, Any]:
    standard_json = _template_json(template_root, word)
    standard = load_sequence(standard_json, feature_mode, force_bbox=False)
    profile = load_semantic_profile(word, semantic_profile_json)
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(word, standard):
        query = _clip_groups(standard, spec["variant"], spec["clips"])
        result = run_pair(standard, query, semantic_profile=profile, enable_cross_check=False)
        score_scale = result.get("score_scale") or {}
        row = {
            **spec,
            "score": float(result["prototype_score"]),
            "dtw_distance": float(result["dtw_distance"]),
            "normalized_distance": float(result["normalized_distance"]),
            "alignment_policy": result.get("alignment_policy"),
            "query_presence": _presence_ratio(query),
            "capture_quality": score_scale.get("capture_quality"),
            "semantic_floor": score_scale.get("semantic_floor"),
            "required_presence_penalty": (result.get("sequence_penalty") or {}).get("required_presence_penalty"),
        }
        row["passed"] = _row_passed(row)
        rows.append(row)
    positive_rows = [row for row in rows if row["kind"] == "positive"]
    negative_rows = [row for row in rows if row["kind"] == "negative"]
    weakest_positive = min(positive_rows, key=lambda row: float(row["score"])) if positive_rows else None
    strongest_negative = max(negative_rows, key=lambda row: float(row["score"])) if negative_rows else None
    return {
        "word": word,
        "standard_json": str(standard_json),
        "standard_length": len(standard.features),
        "standard_presence": _presence_ratio(standard),
        "semantic_profile": _profile_summary(profile),
        "gate_pass": all(bool(row["passed"]) for row in rows),
        "weakest_positive_score": float(weakest_positive["score"]) if weakest_positive else None,
        "weakest_positive_variant": weakest_positive["variant"] if weakest_positive else "",
        "strongest_negative_score": float(strongest_negative["score"]) if strongest_negative else None,
        "strongest_negative_variant": strongest_negative["variant"] if strongest_negative else "",
        "variants": rows,
    }


def _write_rows_csv(path: Path, results: Sequence[Dict[str, Any]]) -> None:
    fields = [
        "word",
        "variant",
        "kind",
        "passed",
        "score",
        "min_score",
        "max_score",
        "capture_quality_status",
        "capture_quality_reason",
        "semantic_floor_reason",
        "required_presence_penalty",
        "query_left_presence",
        "query_right_presence",
        "query_pose_presence",
        "query_face_presence",
        "rationale",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in results:
            for row in item["variants"]:
                quality = row.get("capture_quality") or {}
                floor = row.get("semantic_floor") or {}
                presence = row.get("query_presence") or {}
                writer.writerow(
                    {
                        "word": item["word"],
                        "variant": row.get("variant"),
                        "kind": row.get("kind"),
                        "passed": row.get("passed"),
                        "score": row.get("score"),
                        "min_score": row.get("min_score"),
                        "max_score": row.get("max_score"),
                        "capture_quality_status": quality.get("status"),
                        "capture_quality_reason": quality.get("reason"),
                        "semantic_floor_reason": floor.get("reason"),
                        "required_presence_penalty": row.get("required_presence_penalty"),
                        "query_left_presence": presence.get("left_hand"),
                        "query_right_presence": presence.get("right_hand"),
                        "query_pose_presence": presence.get("pose"),
                        "query_face_presence": presence.get("face"),
                        "rationale": row.get("rationale"),
                    }
                )


def _build_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# 花/跳画面边缘裁切鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，在骨架 mask 层模拟画面边缘导致的 landmark 不可见；手部裁切会重算 hand-shape 特征；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：非关键边缘裁切仍可评分；裁掉 `花` 开花手核心或 `跳` 双手关系核心时必须低分或进入重采/语义失败。",
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
    lines.append("| 目标词 | 状态 | 最弱正向裁切 | 正向最低分 | 最强核心裁切 | 核心裁切最高分 |")
    lines.append("|---|---|---|---:|---|---:|")
    for item in payload["results"]:
        lines.append(
            f"| {item['word']} | {'PASS' if item['gate_pass'] else 'FAIL'} | "
            f"{item['weakest_positive_variant']} | {_fmt(item['weakest_positive_score'])} | "
            f"{item['strongest_negative_variant']} | {_fmt(item['strongest_negative_score'])} |"
        )
    lines.append("")
    lines.append("## 分项明细")
    for item in payload["results"]:
        lines.extend(["", f"### {item['word']}", "", f"- 标准序列：`{item['standard_json']}`", ""])
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | capture_quality | reason | 说明 |")
        lines.append("|---|---|---|---:|---|---|---|---|")
        for row in sorted(item["variants"], key=lambda x: (x["kind"], float(x["score"]))):
            quality = row.get("capture_quality") or {}
            floor = row.get("semantic_floor") or {}
            threshold = f">= {row.get('min_score')}" if row["kind"] == "positive" else f"<= {row.get('max_score')} 或重采/语义失败"
            reason = quality.get("reason") or floor.get("reason") or "-"
            lines.append(
                f"| {row['variant']} | {row['kind']} | {'PASS' if row['passed'] else 'FAIL'} | "
                f"{_fmt(row['score'])} | {threshold} | {quality.get('status') or '-'} | {reason} | {row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 正向场景只覆盖非关键或轻度边缘裁切；核心手语信息出画面不能靠鲁棒性抬分。",
            "- 该门是合成 edge-clipping 压力测试，不能替代真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def run_gate(args: argparse.Namespace) -> Dict[str, Any]:
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
        )
        for word in args.words
    ]
    backend_status = _load_backend_status(args.backend_url, args.status_timeout_sec)
    passed = all(bool(item["gate_pass"]) for item in results)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "claim_policy": "synthetic edge-clipping robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": backend_status,
        "passed": passed,
        "accepted_negative_quality": sorted(ACCEPTED_NEGATIVE_QUALITY),
        "results": results,
    }
    json_path = output_dir / "flower_jump_edge_clipping_robustness_gate.json"
    md_path = output_dir / "flower_jump_edge_clipping_robustness_gate.md"
    csv_path = output_dir / "flower_jump_edge_clipping_robustness_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)
    payload["json_path"] = str(json_path)
    payload["md_path"] = str(md_path)
    payload["csv_path"] = str(csv_path)
    return payload


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run edge-clipping robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_edge_clipping_robustness_gate_current"))
    parser.add_argument("--words", nargs="+", default=DEFAULT_WORDS)
    parser.add_argument("--feature-mode", choices=["auto", "landmark", "bbox"], default="auto")
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--status-timeout-sec", type=float, default=3.0)
    args = parser.parse_args(argv)

    payload = run_gate(args)
    print(f"已生成花/跳画面边缘裁切鲁棒性 JSON：{payload['json_path']}")
    print(f"已生成花/跳画面边缘裁切鲁棒性报告：{payload['md_path']}")
    print(f"已生成花/跳画面边缘裁切鲁棒性 CSV：{payload['csv_path']}")
    print(f"综合状态：{'PASS' if payload['passed'] else 'FAIL'}")
    for item in payload["results"]:
        print(
            f"- {item['word']}: {'PASS' if item['gate_pass'] else 'FAIL'} "
            f"positive_min={_fmt(item['weakest_positive_score'])} "
            f"negative_max={_fmt(item['strongest_negative_score'])}"
        )
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

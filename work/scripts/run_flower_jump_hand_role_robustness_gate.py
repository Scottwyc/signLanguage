#!/usr/bin/env python3
"""Stress-test flower/jump scoring against hand-role changes.

This gate targets two different webcam/user risks:

- Flower is a single-dominant-hand sign, so a user performing it with the
  opposite hand should still score normally.
- Jump has role-specific hands: one hand is the ground and the other is the
  two-finger jumper. A role swap should remain low or semantic-mismatch.

The script only reads cached Holistic JSON and edits skeleton features in
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
from typing import Any, Dict, List, Optional

from run_flower_jump_mirror_robustness_gate import _template_json, _transform_sequence
from score_holistic_sequence_mvp import (
    DEFAULT_SEMANTIC_PROFILE_JSON,
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
ACCEPTED_NEGATIVE_QUALITY = {"semantic_mismatch", "needs_recapture"}


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


def _fmt(value: Any, digits: int = 3) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "-"


def _variant_specs(word: str, min_score: float, max_role_swap_score: float) -> List[Dict[str, Any]]:
    base = [
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
            "min_score": min_score,
            "expected": "horizontal camera/previews should not break sign semantics",
        },
    ]
    if word == "花":
        return base + [
            {
                "variant": "dominant_hand_swap",
                "kind": "positive",
                "mirror_x": False,
                "swap_labels": True,
                "min_score": min_score,
                "expected": "single-hand flower should accept left/right dominant-hand choice",
            },
            {
                "variant": "mirror_x_dominant_hand_swap",
                "kind": "positive",
                "mirror_x": True,
                "swap_labels": True,
                "min_score": min_score,
                "expected": "single-hand flower should accept dominant-hand choice under mirrored camera geometry",
            },
        ]
    if word == "跳":
        return base + [
            {
                "variant": "role_swap_negative",
                "kind": "negative",
                "mirror_x": False,
                "swap_labels": True,
                "max_score": max_role_swap_score,
                "expected": "jump ground/jumper role swap should not be accepted as normal",
            },
            {
                "variant": "mirror_x_role_swap_negative",
                "kind": "negative",
                "mirror_x": True,
                "swap_labels": True,
                "max_score": max_role_swap_score,
                "expected": "jump role swap should stay rejected even under mirrored camera geometry",
            },
        ]
    return base


def _row_passed(row: Dict[str, Any]) -> bool:
    score = float(row["score"])
    if row["kind"] == "positive":
        return score >= float(row["min_score"])
    quality = (row.get("capture_quality") or {}).get("status")
    return score <= float(row["max_score"]) and quality in ACCEPTED_NEGATIVE_QUALITY


def _run_word(
    word: str,
    template_root: Path,
    semantic_profile_json: Path,
    feature_mode: str,
    min_score: float,
    max_role_swap_score: float,
) -> Dict[str, Any]:
    standard_json = _template_json(template_root, word)
    loaded_standard = load_sequence(standard_json, feature_mode, force_bbox=False)
    profile = load_semantic_profile(word, semantic_profile_json)
    standard = _transform_sequence(loaded_standard, "standard_base", mirror_x=False, swap_labels=False, profile=profile)
    variants: List[Dict[str, Any]] = []
    for spec in _variant_specs(word, min_score, max_role_swap_score):
        query = _transform_sequence(
            loaded_standard,
            spec["variant"],
            mirror_x=bool(spec["mirror_x"]),
            swap_labels=bool(spec["swap_labels"]),
            profile=profile,
        )
        result = run_pair(standard, query, semantic_profile=profile, enable_cross_check=False)
        score_scale = result.get("score_scale") or {}
        sequence_penalty = result.get("sequence_penalty") or {}
        row = {
            **spec,
            "score": float(result["prototype_score"]),
            "dtw_distance": float(result["dtw_distance"]),
            "normalized_distance": float(result["normalized_distance"]),
            "alignment_policy": result.get("alignment_policy"),
            "capture_quality": score_scale.get("capture_quality"),
            "semantic_floor": score_scale.get("semantic_floor"),
            "score_scale_reason": score_scale.get("reason"),
            "presence_hand_side_swapped": sequence_penalty.get("presence_hand_side_swapped"),
            "motion_hand_side_swapped": sequence_penalty.get("motion_hand_side_swapped"),
            "roughness_hand_side_swapped": sequence_penalty.get("roughness_hand_side_swapped"),
        }
        row["passed"] = _row_passed(row)
        variants.append(row)
    positive_rows = [row for row in variants if row["kind"] == "positive"]
    negative_rows = [row for row in variants if row["kind"] == "negative"]
    weakest_positive = min(positive_rows, key=lambda row: float(row["score"])) if positive_rows else None
    strongest_negative = max(negative_rows, key=lambda row: float(row["score"])) if negative_rows else None
    return {
        "word": word,
        "standard_json": str(standard_json),
        "standard_length": len(standard.features),
        "semantic_profile": _profile_summary(profile),
        "gate_pass": all(bool(row["passed"]) for row in variants),
        "weakest_positive_score": float(weakest_positive["score"]) if weakest_positive else None,
        "weakest_positive_variant": weakest_positive["variant"] if weakest_positive else "",
        "strongest_negative_score": float(strongest_negative["score"]) if strongest_negative else None,
        "strongest_negative_variant": strongest_negative["variant"] if strongest_negative else "",
        "variants": variants,
    }


def _write_csv(path: Path, results: List[Dict[str, Any]]) -> None:
    fields = [
        "word",
        "variant",
        "kind",
        "score",
        "passed",
        "min_score",
        "max_score",
        "capture_quality_status",
        "capture_quality_reason",
        "semantic_floor_reason",
        "presence_hand_side_swapped",
        "motion_hand_side_swapped",
        "roughness_hand_side_swapped",
        "expected",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in results:
            for row in item["variants"]:
                quality = row.get("capture_quality") or {}
                floor = row.get("semantic_floor") or {}
                writer.writerow(
                    {
                        "word": item["word"],
                        "variant": row.get("variant"),
                        "kind": row.get("kind"),
                        "score": row.get("score"),
                        "passed": row.get("passed"),
                        "min_score": row.get("min_score", ""),
                        "max_score": row.get("max_score", ""),
                        "capture_quality_status": quality.get("status", ""),
                        "capture_quality_reason": quality.get("reason", ""),
                        "semantic_floor_reason": floor.get("reason", ""),
                        "presence_hand_side_swapped": row.get("presence_hand_side_swapped"),
                        "motion_hand_side_swapped": row.get("motion_hand_side_swapped"),
                        "roughness_hand_side_swapped": row.get("roughness_hand_side_swapped"),
                        "expected": row.get("expected"),
                    }
                )


def _build_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# 花/跳手角色鲁棒性门")
    lines.append("")
    lines.append(f"- 生成时间：`{payload['generated_at']}`")
    lines.append(f"- 综合状态：`{'PASS' if payload['passed'] else 'FAIL'}`")
    lines.append(f"- 标准库：`{payload['template_root']}`")
    lines.append(f"- 语义 profile：`{payload['semantic_profile_json']}`")
    lines.append("- 口径：只读缓存 Holistic JSON；不调用 `/api/score`，不移动 marker，不运行 Holistic，不重启 5080。")
    lines.append("")
    lines.append("## 判定口径")
    lines.append("")
    lines.append(f"- `花`：单手主导词，左右惯用手互换和镜像下互换都必须不低于 `{_fmt(payload['min_score'])}`。")
    lines.append(f"- `跳`：双手角色词，地面手/跳跃手互换必须不高于 `{_fmt(payload['max_role_swap_score'])}` 且进入 `semantic_mismatch/needs_recapture`。")
    lines.append("")
    lines.append("## 摘要")
    lines.append("")
    lines.append("| 词条 | 状态 | 正向最低分 | 最弱正向角色变体 | 角色互换最高分 | 最强角色互换负例 |")
    lines.append("|---|---|---:|---|---:|---|")
    for item in payload["results"]:
        lines.append(
            f"| {item['word']} | {'PASS' if item['gate_pass'] else 'FAIL'} | "
            f"{_fmt(item.get('weakest_positive_score'))} | {item.get('weakest_positive_variant') or '-'} | "
            f"{_fmt(item.get('strongest_negative_score'))} | {item.get('strongest_negative_variant') or '-'} |"
        )
    lines.append("")
    lines.append("## 明细")
    lines.append("")
    lines.append("| 词条 | 变体 | 类型 | 分数 | 状态 | 质量状态 | floor 原因 | 序列级左右手匹配 |")
    lines.append("|---|---|---|---:|---|---|---|---|")
    for item in payload["results"]:
        for row in item["variants"]:
            quality = row.get("capture_quality") or {}
            floor = row.get("semantic_floor") or {}
            swapped = any(
                bool(row.get(key))
                for key in ["presence_hand_side_swapped", "motion_hand_side_swapped", "roughness_hand_side_swapped"]
            )
            lines.append(
                f"| {item['word']} | {row.get('variant')} | {row.get('kind')} | {_fmt(row.get('score'))} | "
                f"{'PASS' if row.get('passed') else 'FAIL'} | {quality.get('status') or '-'} | "
                f"{floor.get('reason') or '-'} | {'swapped' if swapped else 'direct'} |"
            )
    lines.append("")
    lines.append("## 结论")
    lines.append("")
    if payload["passed"]:
        lines.append("- 手角色边界通过：`花` 支持左右惯用手，`跳` 仍保持角色语义约束。")
    else:
        lines.append("- 手角色边界未通过；需要复查 scorer 的左右手互换或双手角色 guard。")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_hand_role_robustness_gate_current"))
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--backend-timeout-sec", type=float, default=3.0)
    parser.add_argument("--feature-mode", default="auto", choices=["auto", "landmark", "bbox"])
    parser.add_argument("--words", nargs="+", default=DEFAULT_WORDS)
    parser.add_argument("--min-score", type=float, default=70.0)
    parser.add_argument("--max-role-swap-score", type=float, default=50.0)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    template_root = Path(args.template_root)
    semantic_profile_json = Path(args.semantic_profile_json)
    results = [
        _run_word(
            word,
            template_root,
            semantic_profile_json,
            args.feature_mode,
            args.min_score,
            args.max_role_swap_score,
        )
        for word in args.words
    ]
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "claim_policy": "hand-role robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "feature_mode": args.feature_mode,
        "backend_status": _load_backend_status(args.backend_url, args.backend_timeout_sec),
        "min_score": args.min_score,
        "max_role_swap_score": args.max_role_swap_score,
        "accepted_negative_quality": sorted(ACCEPTED_NEGATIVE_QUALITY),
        "passed": all(bool(item["gate_pass"]) for item in results),
        "results": results,
    }
    json_path = output_dir / "flower_jump_hand_role_robustness_gate.json"
    md_path = output_dir / "flower_jump_hand_role_robustness_gate.md"
    csv_path = output_dir / "flower_jump_hand_role_robustness_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_csv(csv_path, results)

    print(f"已生成花/跳手角色鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳手角色鲁棒性报告：{md_path}")
    print(f"已生成花/跳手角色鲁棒性 CSV：{csv_path}")
    print(f"综合状态：{'PASS' if payload['passed'] else 'FAIL'}")
    for item in results:
        print(
            f"- {item['word']}: {'PASS' if item['gate_pass'] else 'FAIL'} "
            f"positive_min={_fmt(item.get('weakest_positive_score'))} "
            f"weakest={item.get('weakest_positive_variant') or '-'} "
            f"role_swap_max={_fmt(item.get('strongest_negative_score'))}"
        )
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

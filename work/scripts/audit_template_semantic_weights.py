#!/usr/bin/env python3
"""Audit and materialize semantic dynamic frame weights for template caches."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import numpy as np

from score_holistic_sequence_mvp import (
    DEFAULT_SEMANTIC_PROFILE_JSON,
    _presence_ratio,
    _profile_summary,
    _sequence_motion_by_group,
    compute_semantic_frame_weight_values,
    load_semantic_profile,
    load_sequence,
)


REPO_ROOT = Path("/data/WYC/signLanguage")
DEFAULT_TEMPLATE_ROOT = REPO_ROOT / "work/generated/scoring_mvp_run2/all_demo_step4_worker_cache_v2/results"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "work/generated/scoring_mvp_run3/template_semantic_weight_audit"


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _template_jsons(root: Path) -> List[Path]:
    result: List[Path] = []
    if not root.exists():
        return result
    for folder in sorted([item for item in root.iterdir() if item.is_dir()], key=lambda p: p.name):
        direct = folder / f"{folder.name}_holistic_results.json"
        if direct.exists():
            result.append(direct)
            continue
        matches = sorted(folder.glob("*_holistic_results.json"))
        if matches:
            result.append(matches[0])
    return result


def _weight_stats(values: np.ndarray) -> Dict[str, float]:
    if values.size == 0:
        return {"count": 0.0, "mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0, "max_min_ratio": 0.0}
    min_value = float(values.min())
    return {
        "count": float(values.size),
        "mean": float(values.mean()),
        "min": min_value,
        "max": float(values.max()),
        "std": float(values.std()),
        "max_min_ratio": float(values.max() / max(min_value, 1e-6)),
    }


def _top_frames(seq, weights: np.ndarray, limit: int = 12) -> List[Dict[str, Any]]:
    if weights.size == 0:
        return []
    top_indices = list(np.argsort(weights)[-min(limit, len(weights)) :][::-1])
    return [
        {
            "rank": rank + 1,
            "frame_idx": int(seq.features[idx].frame_idx),
            "timestamp_sec": float(seq.features[idx].timestamp_sec),
            "semantic_frame_weight": float(weights[idx]),
        }
        for rank, idx in enumerate(top_indices)
    ]


def _frame_rows(seq, weights: np.ndarray) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for idx, feature in enumerate(seq.features):
        rows.append(
            {
                "frame_idx": int(feature.frame_idx),
                "timestamp_sec": float(feature.timestamp_sec),
                "semantic_frame_weight": float(weights[idx]) if idx < len(weights) else 1.0,
                "source_frame_weight": float(feature.frame_weight),
                "presence": dict(feature.presence),
            }
        )
    return rows


def _audit_one(template_json: Path, semantic_profile_json: Path, write_manifest: bool) -> Dict[str, Any]:
    word = template_json.parent.name
    seq = load_sequence(template_json, requested_mode="landmark", apply_sidecar_weights=False)
    profile = load_semantic_profile(word, semantic_profile_json)
    weights = compute_semantic_frame_weight_values(seq, profile=profile, combine_stored=True)
    presence = _presence_ratio(seq)
    motion = _sequence_motion_by_group(seq)
    focus_presence = {
        group: presence.get(group.replace("_shape", ""), 0.0)
        for group in profile.focus_groups
        if group in motion or group.replace("_shape", "") in presence
    }
    stats = _weight_stats(weights)
    top_frames = _top_frames(seq, weights)
    frame_rows = _frame_rows(seq, weights)

    issues: List[str] = []
    if profile.word == "generic" and word != "generic":
        issues.append("missing_word_specific_profile")
    if len(seq.features) < 12:
        issues.append("low_template_frame_count")
    if stats["max_min_ratio"] < 1.15 and len(seq.features) >= 6:
        issues.append("weak_dynamic_frame_contrast")
    for group, ratio in focus_presence.items():
        if ratio < 0.20:
            issues.append(f"low_focus_presence:{group}")

    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "template_json": str(template_json),
        "word": word,
        "version": "semantic_dynamic_frame_weights_v1",
        "strategy": "semantic_focus_motion_energy_density",
        "semantic_profile": _profile_summary(profile),
        "records": len(seq.features),
        "fps": seq.fps,
        "total_frames": seq.total_frames,
        "presence_ratio": presence,
        "motion_by_group": motion,
        "weight_stats": stats,
        "top_weighted_frames": top_frames,
        "frame_weights": frame_rows,
        "issues": issues,
    }

    manifest_path = template_json.parent / "semantic_frame_weights.json"
    if write_manifest:
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "word": word,
        "template_json": str(template_json),
        "manifest_path": str(manifest_path),
        "records": len(seq.features),
        "fps": seq.fps,
        "profile_word": profile.word,
        "focus_groups": profile.focus_groups,
        "group_weights": profile.group_weights,
        "presence_ratio": presence,
        "motion_by_group": motion,
        "weight_stats": stats,
        "top_weighted_frames": top_frames,
        "issues": issues,
        "status": "ok" if not issues else "review",
    }


def _build_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# 模板库语义权重与动态帧权重审计")
    lines.append("")
    lines.append(f"- 生成时间：`{payload['generated_at']}`")
    lines.append(f"- 模板根目录：`{payload['template_root']}`")
    lines.append(f"- 语义 profile：`{payload['semantic_profile_json']}`")
    lines.append(f"- 样本数：`{payload['summary']['templates']}`")
    lines.append(f"- 完全通过：`{payload['summary']['ok']}`")
    lines.append(f"- 需复核：`{payload['summary']['review']}`")
    lines.append("")
    lines.append("## 总览")
    lines.append("")
    lines.append("| 词条 | 帧数 | profile | 重要组 | 权重峰值 | 峰谷比 | 状态 | 问题 |")
    lines.append("|---|---:|---|---|---:|---:|---|---|")
    for item in payload["items"]:
        stats = item["weight_stats"]
        issues = ", ".join(item["issues"]) if item["issues"] else "-"
        lines.append(
            f"| {item['word']} | {item['records']} | {item['profile_word']} | "
            f"{','.join(item['focus_groups'])} | {stats['max']:.3f} | "
            f"{stats['max_min_ratio']:.3f} | {item['status']} | {issues} |"
        )
    lines.append("")
    lines.append("## 重要帧")
    for item in payload["items"]:
        lines.append("")
        lines.append(f"### {item['word']}")
        lines.append("")
        for frame in item["top_weighted_frames"][:6]:
            lines.append(
                f"- rank {frame['rank']}: frame `{frame['frame_idx']}`, "
                f"t=`{frame['timestamp_sec']:.3f}s`, weight=`{frame['semantic_frame_weight']:.3f}`"
            )
    lines.append("")
    lines.append("## 说明")
    lines.append("")
    lines.append("- `semantic_frame_weights.json` 已写回每个模板目录，作为数据库侧的逐帧动态权重 manifest。")
    lines.append("- 评分时仍会根据当前语义 profile 重新计算动态权重；若目录中存在 manifest，会作为数据库侧先验加载，并与实时动态权重归一化合并。")
    lines.append("- `review` 不等于失败，表示帧数过低、重要组检出率低或动态峰值不明显，需要后续补采或人工复核。")
    lines.append("")
    return "\n".join(lines)


def run_audit(template_root: Path, semantic_profile_json: Path, output_dir: Path, write_manifest: bool = True) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    items = [_audit_one(path, semantic_profile_json, write_manifest=write_manifest) for path in _template_jsons(template_root)]
    summary = {
        "templates": len(items),
        "ok": sum(1 for item in items if item["status"] == "ok"),
        "review": sum(1 for item in items if item["status"] != "ok"),
        "missing_profile": sum(1 for item in items if "missing_word_specific_profile" in item["issues"]),
        "low_template_frame_count": sum(1 for item in items if "low_template_frame_count" in item["issues"]),
        "weak_dynamic_frame_contrast": sum(1 for item in items if "weak_dynamic_frame_contrast" in item["issues"]),
    }
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "write_manifest": write_manifest,
        "summary": summary,
        "items": items,
    }
    json_path = output_dir / "template_semantic_weight_audit.json"
    md_path = output_dir / "template_semantic_weight_audit.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    payload["json_path"] = str(json_path)
    payload["md_path"] = str(md_path)
    return payload


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="审计并落盘模板库语义/动态帧权重")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--no-write-manifest", action="store_true", help="只审计，不写回各模板目录")
    args = parser.parse_args(argv)

    payload = run_audit(
        template_root=Path(args.template_root),
        semantic_profile_json=Path(args.semantic_profile_json),
        output_dir=Path(args.output_dir),
        write_manifest=not args.no_write_manifest,
    )
    print(f"已生成审计 JSON：{payload['json_path']}")
    print(f"已生成审计报告：{payload['md_path']}")
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

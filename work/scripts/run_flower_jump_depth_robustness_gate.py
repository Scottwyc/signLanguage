#!/usr/bin/env python3
"""Stress-test flower/jump scoring against Holistic z/depth drift.

Holistic landmark z values can drift across webcams, lighting, and user-camera
distance. Flower/jump semantics should not be dominated by moderate depth
offsets, z scaling, or light z noise. Strong z noise is kept as a diagnostic
boundary because it can corrupt local hand geometry.

This script edits cached skeleton sequences in memory only. It does not call
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
COORD_GROUPS = ["pose", "left_hand", "right_hand", "face"]
HAND_GROUPS = ["left_hand", "right_hand"]


QueryFactory = Callable[[SequenceData], SequenceData]


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


def _group_array(frame: FrameFeature, group: str) -> tuple[Optional[np.ndarray], Optional[np.ndarray]]:
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


def _mutate_depth(
    seq: SequenceData,
    name: str,
    *,
    groups: Sequence[str],
    z_scale: float = 1.0,
    z_offset: float = 0.0,
    z_noise: float = 0.0,
    seed: int = 1,
) -> SequenceData:
    rng = np.random.default_rng(seed)
    items: List[FrameFeature] = []
    for frame in seq.features:
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        for group in groups:
            coords, valid = _group_array(frame, group)
            if coords is None or valid is None or not valid.any():
                continue
            coords = coords.copy()
            coords[valid, 2] = coords[valid, 2] * float(z_scale) + float(z_offset)
            if z_noise > 0.0:
                coords[valid, 2] += rng.normal(0.0, float(z_noise), size=int(valid.sum())).astype(np.float32)
            _set_group(frame, vector, mask, group, coords, valid)
        items.append(_clone_frame(frame, vector=vector, mask=mask))
    return _clone_sequence(seq, name, items)


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
            "global_z_offset_pos_0.10",
            "positive",
            lambda seq: _mutate_depth(seq, "global_z_offset_pos_0.10", groups=COORD_GROUPS, z_offset=0.10),
            "整个人的 Holistic z 坐标出现轻微正向漂移。",
            min_score=min_score,
        ),
        _spec(
            "global_z_offset_neg_0.10",
            "positive",
            lambda seq: _mutate_depth(seq, "global_z_offset_neg_0.10", groups=COORD_GROUPS, z_offset=-0.10),
            "整个人的 Holistic z 坐标出现轻微负向漂移。",
            min_score=min_score,
        ),
        _spec(
            "global_z_scale_0.50",
            "positive",
            lambda seq: _mutate_depth(seq, "global_z_scale_0.50", groups=COORD_GROUPS, z_scale=0.50),
            "整体深度动态被压缩到一半。",
            min_score=min_score,
        ),
        _spec(
            "global_z_scale_2.00",
            "positive",
            lambda seq: _mutate_depth(seq, "global_z_scale_2.00", groups=COORD_GROUPS, z_scale=2.00),
            "整体深度动态被放大到两倍。",
            min_score=min_score,
        ),
        _spec(
            "hand_z_scale_0.75",
            "positive",
            lambda seq: _mutate_depth(seq, "hand_z_scale_0.75", groups=HAND_GROUPS, z_scale=0.75),
            "手部深度动态略收缩，并重算手形特征。",
            min_score=min_score,
        ),
        _spec(
            "hand_z_scale_1.50",
            "positive",
            lambda seq: _mutate_depth(seq, "hand_z_scale_1.50", groups=HAND_GROUPS, z_scale=1.50),
            "手部深度动态略放大，并重算手形特征。",
            min_score=min_score,
        ),
        _spec(
            "global_z_noise_0.10_diagnostic",
            "diagnostic",
            lambda seq: _mutate_depth(seq, "global_z_noise_0.10_diagnostic", groups=COORD_GROUPS, z_noise=0.10, seed=7),
            "中等逐点 z 噪声会改变重算后的局部手形，只记录诊断边界。",
        ),
        _spec(
            "hand_z_noise_0.10_diagnostic",
            "diagnostic",
            lambda seq: _mutate_depth(seq, "hand_z_noise_0.10_diagnostic", groups=HAND_GROUPS, z_noise=0.10, seed=11),
            "中等手部逐点 z 噪声会破坏局部手形，只记录诊断边界。",
        ),
        _spec(
            "global_z_noise_0.20_diagnostic",
            "diagnostic",
            lambda seq: _mutate_depth(seq, "global_z_noise_0.20_diagnostic", groups=COORD_GROUPS, z_noise=0.20, seed=17),
            "强整体 z 噪声，只记录诊断边界。",
        ),
        _spec(
            "hand_z_noise_0.20_diagnostic",
            "diagnostic",
            lambda seq: _mutate_depth(seq, "hand_z_noise_0.20_diagnostic", groups=HAND_GROUPS, z_noise=0.20, seed=19),
            "强手部 z 噪声会破坏局部手形，只记录诊断边界。",
        ),
        _spec(
            "global_z_scale_0.25_diagnostic",
            "diagnostic",
            lambda seq: _mutate_depth(seq, "global_z_scale_0.25_diagnostic", groups=COORD_GROUPS, z_scale=0.25),
            "极端深度压缩，只记录诊断边界。",
        ),
        _spec(
            "global_z_scale_3.00_diagnostic",
            "diagnostic",
            lambda seq: _mutate_depth(seq, "global_z_scale_3.00_diagnostic", groups=COORD_GROUPS, z_scale=3.00),
            "极端深度放大，只记录诊断边界。",
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
        "# 花/跳 z/depth 深度鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，在骨架 z 坐标层面模拟深度偏移、缩放和噪声；手部 z 改动会重算 hand-shape 特征；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：不同摄像头/距离导致 Holistic 深度漂移时，`花/跳` 仍主要由 2D 手形、相位和双手关系决定。",
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
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向深度扰动 | 诊断最低分 | 最弱诊断深度扰动 | 门槛 |")
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
            "- 正向扰动覆盖中等深度漂移；强 z 噪声和极端深度缩放只作为诊断边界。",
            "- 该门是合成 depth 压力测试，不能替代正式网页摄像头样本。",
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
            min_score=args.min_score,
        )
        for word in args.words
    ]
    backend_status = _load_backend_status(args.backend_url, args.status_timeout_sec)
    passed = all(bool(item["gate_pass"]) for item in results)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "claim_policy": "synthetic z/depth robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "min_score": args.min_score,
        "backend_status": backend_status,
        "passed": passed,
        "results": results,
    }
    json_path = output_dir / "flower_jump_depth_robustness_gate.json"
    md_path = output_dir / "flower_jump_depth_robustness_gate.md"
    csv_path = output_dir / "flower_jump_depth_robustness_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)
    payload["json_path"] = str(json_path)
    payload["md_path"] = str(md_path)
    payload["csv_path"] = str(csv_path)
    return payload


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run z/depth robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_depth_robustness_gate_current"))
    parser.add_argument("--words", nargs="+", default=DEFAULT_WORDS)
    parser.add_argument("--feature-mode", choices=["auto", "landmark", "bbox"], default="auto")
    parser.add_argument("--min-score", type=float, default=70.0)
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--status-timeout-sec", type=float, default=3.0)
    args = parser.parse_args(argv)

    payload = run_gate(args)
    print(f"已生成花/跳深度鲁棒性 JSON：{payload['json_path']}")
    print(f"已生成花/跳深度鲁棒性报告：{payload['md_path']}")
    print(f"已生成花/跳深度鲁棒性 CSV：{payload['csv_path']}")
    print(f"综合状态：{'PASS' if payload['passed'] else 'FAIL'}")
    for item in payload["results"]:
        print(
            f"- {item['word']}: {'PASS' if item['gate_pass'] else 'FAIL'} "
            f"positive_min={_fmt(item['weakest_positive_score'])} "
            f"weakest={item['weakest_positive_variant']} "
            f"diagnostic_min={_fmt(item['weakest_diagnostic_score'])}"
        )
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Stress-test flower/jump scoring against malformed cached-JSON structure.

The browser/backend normally writes valid Holistic JSON, but a partially
serialized record, group, landmark point, bbox, or sidecar must not crash the
saved-web scoring path or emit non-finite diagnostics. This gate writes
temporary malformed fixtures and reloads them through the normal scorer.

It does not call /api/score, run Holistic, move the web marker, or restart 5080.
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import numpy as np

from run_flower_jump_landmark_noise_robustness_gate import _fmt, _json_default, _load_backend_status
from run_flower_jump_mirror_robustness_gate import _template_json
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


def _spec(
    variant: str,
    rationale: str,
    min_score: Optional[float],
    *,
    feature_mode: str = "landmark",
    malformed_sidecar: bool = False,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": "positive" if min_score is not None else "compatibility",
        "gated": True,
        "min_score": min_score,
        "score_required": min_score is not None,
        "feature_mode": feature_mode,
        "malformed_sidecar": malformed_sidecar,
        "rationale": rationale,
    }


def _variant_specs(min_score: float) -> List[Dict[str, Any]]:
    return [
        _spec("self_reloaded", "原始标准 JSON 经正常加载后应保持近满分。", 95.0),
        _spec("first_result_data_string", "首帧 result_data 错类型不应让整段自动误切到 bbox。", min_score),
        _spec("mid_record_null", "单个 null record 应按缺失帧保留时序，不应崩溃。", min_score),
        _spec("mid_record_string", "单个字符串 record 应按缺失帧保留时序，不应崩溃。", min_score),
        _spec("mid_result_data_string", "单帧 result_data 错类型应按该帧 landmarks 缺失处理。", min_score),
        _spec("mid_right_hand_group_string", "单帧核心手 landmark 组错类型应按该组缺失处理。", min_score),
        _spec("mid_right_hand_group_dict", "landmark 组误写成字典时应按该组缺失处理。", min_score),
        _spec("mid_right_hand_point_null", "单个 landmark point=null 应按该点缺失处理。", min_score),
        _spec("mid_right_hand_point_list", "单个 landmark point 为数组而非对象时应按该点缺失处理。", min_score),
        _spec("mid_pose_group_number", "单帧 pose landmark 组为数字时应回退到手部语义评分。", min_score),
        _spec(
            "malformed_sidecar_ignored",
            "semantic_frame_weights.json 顶层错类型时应忽略 sidecar 并保持正常评分。",
            95.0,
            malformed_sidecar=True,
        ),
        _spec(
            "bbox_combined_structure_finite",
            "旧 bbox 模式遇到错类型 group/bbox 和非有限 bbox 数值时应保持有限，不强求 bbox 语义高分。",
            None,
            feature_mode="bbox",
        ),
    ]


def _records(payload: Dict[str, Any]) -> List[Any]:
    records = payload.get("records")
    if not isinstance(records, list):
        raise RuntimeError("structural JSON gate requires a records list")
    return records


def _record(records: List[Any], index: int) -> Dict[str, Any]:
    item = records[max(0, min(len(records) - 1, index))]
    if not isinstance(item, dict):
        raise RuntimeError("fixture mutation expected a dictionary record")
    return item


def _row(record: Dict[str, Any]) -> Dict[str, Any]:
    row = record.get("row")
    if not isinstance(row, dict):
        raise RuntimeError("fixture mutation expected a dictionary row")
    return row


def _result_data(record: Dict[str, Any]) -> Dict[str, Any]:
    result_data = record.get("result_data")
    if not isinstance(result_data, dict):
        raise RuntimeError("fixture mutation expected dictionary result_data")
    return result_data


def _apply_variant(payload: Dict[str, Any], variant: str) -> Dict[str, Any]:
    records = _records(payload)
    mid = len(records) // 2
    changed = 0
    if variant in {"self_reloaded", "malformed_sidecar_ignored"}:
        pass
    elif variant == "first_result_data_string":
        _record(records, 0)["result_data"] = "bad-result-data"
        changed = 1
    elif variant == "mid_record_null":
        records[mid] = None
        changed = 1
    elif variant == "mid_record_string":
        records[mid] = "bad-record"
        changed = 1
    elif variant == "mid_result_data_string":
        _record(records, mid)["result_data"] = "bad-result-data"
        changed = 1
    elif variant == "mid_right_hand_group_string":
        _result_data(_record(records, mid))["right_hand_landmarks"] = "bad-landmark-group"
        changed = 1
    elif variant == "mid_right_hand_group_dict":
        _result_data(_record(records, mid))["right_hand_landmarks"] = {"bad": "landmark-group"}
        changed = 1
    elif variant in {"mid_right_hand_point_null", "mid_right_hand_point_list"}:
        landmarks = _result_data(_record(records, mid)).get("right_hand_landmarks")
        if not isinstance(landmarks, list) or len(landmarks) <= 8:
            raise RuntimeError("fixture mutation requires right hand landmark 8")
        landmarks[8] = None if variant.endswith("_null") else [0.1, 0.2, 0.3]
        changed = 1
    elif variant == "mid_pose_group_number":
        _result_data(_record(records, mid))["pose_landmarks"] = 123
        changed = 1
    elif variant == "bbox_combined_structure_finite":
        if len(records) < 3:
            raise RuntimeError("bbox combined fixture requires at least three records")
        _row(_record(records, len(records) // 3))["right_hand"] = "bad-group"
        _row(_record(records, len(records) // 2))["pose"]["bbox"] = "bad-bbox"
        _row(_record(records, (2 * len(records)) // 3))["right_hand"]["bbox"]["x_min"] = float("nan")
        changed = 3
    else:
        raise ValueError(f"unknown structural JSON variant: {variant}")
    return {"changed_structure_values": changed, "total_records": len(records)}


def _write_fixture(source_json: Path, dest_json: Path, spec: Dict[str, Any]) -> Dict[str, Any]:
    payload = copy.deepcopy(json.loads(source_json.read_text(encoding="utf-8")))
    detail = _apply_variant(payload, str(spec["variant"]))
    dest_json.parent.mkdir(parents=True, exist_ok=True)
    dest_json.write_text(json.dumps(payload, ensure_ascii=False, allow_nan=True), encoding="utf-8")
    if spec["malformed_sidecar"]:
        (dest_json.parent / "semantic_frame_weights.json").write_text(
            json.dumps(["bad-sidecar-top-level", None], ensure_ascii=False),
            encoding="utf-8",
        )
    return detail


def _sequence_summary(seq: Any, expected_records: int) -> Dict[str, Any]:
    vector_nonfinite = sum(int((~np.isfinite(item.vector)).sum()) for item in seq.features)
    mask_nonfinite = sum(int((~np.isfinite(item.mask)).sum()) for item in seq.features)
    return {
        "mode": seq.mode,
        "feature_count": len(seq.features),
        "expected_records": expected_records,
        "feature_count_preserved": len(seq.features) == expected_records,
        "vector_nonfinite": vector_nonfinite,
        "mask_nonfinite": mask_nonfinite,
        "finite": vector_nonfinite == 0 and mask_nonfinite == 0,
    }


def _result_finite(result: Dict[str, Any]) -> bool:
    try:
        return all(
            math.isfinite(float(result.get(key)))
            for key in ("prototype_score", "dtw_distance", "normalized_distance")
        )
    except (TypeError, ValueError):
        return False


def _run_word(
    word: str,
    template_root: Path,
    semantic_profile_json: Path,
    feature_mode: str,
    min_score: float,
    fixture_dir: Path,
) -> Dict[str, Any]:
    standard_json = _template_json(template_root, word)
    standard = load_sequence(standard_json, feature_mode, force_bbox=False, apply_sidecar_weights=False)
    bbox_standard = load_sequence(standard_json, "bbox", force_bbox=True, apply_sidecar_weights=False)
    profile = load_semantic_profile(word, semantic_profile_json)
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(min_score):
        fixture_json = fixture_dir / word / spec["variant"] / "query.json"
        mutation_detail = _write_fixture(standard_json, fixture_json, spec)
        row: Dict[str, Any] = {
            "variant": spec["variant"],
            "kind": spec["kind"],
            "gated": spec["gated"],
            "min_score": spec["min_score"],
            "score_required": spec["score_required"],
            "feature_mode": spec["feature_mode"],
            "malformed_sidecar": spec["malformed_sidecar"],
            "fixture_json": str(fixture_json),
            "rationale": spec["rationale"],
            **mutation_detail,
        }
        try:
            use_bbox = spec["feature_mode"] == "bbox"
            query = load_sequence(
                fixture_json,
                "bbox" if use_bbox else feature_mode,
                force_bbox=use_bbox,
                apply_sidecar_weights=bool(spec["malformed_sidecar"]),
            )
            result = run_pair(
                bbox_standard if use_bbox else standard,
                query,
                semantic_profile=profile,
                target_word=word,
                enable_cross_check=False,
            )
        except Exception as exc:  # noqa: BLE001 - loader/scorer crashes are gate failures.
            row.update(
                {
                    "exception": f"{type(exc).__name__}: {exc}",
                    "score": None,
                    "dtw_distance": None,
                    "normalized_distance": None,
                    "result_finite": False,
                    "sequence_summary": {},
                    "passed": False,
                }
            )
        else:
            summary = _sequence_summary(query, int(mutation_detail["total_records"]))
            result_finite = _result_finite(result)
            score = float(result["prototype_score"])
            row.update(
                {
                    "exception": "",
                    "score": score,
                    "dtw_distance": float(result["dtw_distance"]),
                    "normalized_distance": float(result["normalized_distance"]),
                    "result_finite": result_finite,
                    "sequence_summary": summary,
                    "alignment_policy": result.get("alignment_policy"),
                    "capture_quality": (result.get("score_scale") or {}).get("capture_quality"),
                    "passed": bool(
                        result_finite
                        and summary["finite"]
                        and summary["feature_count_preserved"]
                        and summary["mode"] == spec["feature_mode"]
                        and (not spec["score_required"] or score >= float(spec["min_score"]))
                    ),
                }
            )
        rows.append(row)
    scored = [row for row in rows if row.get("score") is not None and row["score_required"]]
    weakest = min(scored, key=lambda row: float(row["score"])) if scored else None
    return {
        "word": word,
        "standard_json": str(standard_json),
        "standard_length": len(standard.features),
        "semantic_profile": _profile_summary(profile),
        "gate_pass": all(bool(row["passed"]) for row in rows),
        "weakest_positive_score": float(weakest["score"]) if weakest else None,
        "weakest_positive_variant": weakest["variant"] if weakest else "",
        "min_required_score": min_score,
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
        "feature_mode",
        "result_finite",
        "sequence_finite",
        "feature_count_preserved",
        "changed_structure_values",
        "total_records",
        "exception",
        "rationale",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in results:
            for row in item["variants"]:
                summary = row.get("sequence_summary") or {}
                writer.writerow(
                    {
                        "word": item["word"],
                        "variant": row.get("variant"),
                        "kind": row.get("kind"),
                        "passed": row.get("passed"),
                        "score": row.get("score"),
                        "min_score": row.get("min_score"),
                        "feature_mode": row.get("feature_mode"),
                        "result_finite": row.get("result_finite"),
                        "sequence_finite": summary.get("finite"),
                        "feature_count_preserved": summary.get("feature_count_preserved"),
                        "changed_structure_values": row.get("changed_structure_values"),
                        "total_records": row.get("total_records"),
                        "exception": row.get("exception"),
                        "rationale": row.get("rationale"),
                    }
                )


def _build_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# 花/跳缓存 JSON 结构鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：写入错类型 record/result_data/landmark group/point/bbox/sidecar fixture，再走正常 `load_sequence()` 和 `run_pair()`；不调用 `/api/score`，不运行 Holistic，不移动 marker，不重启 5080。",
        "- 目标：局部结构损坏按缺失证据处理，保留帧数与 landmark 模式；landmark/bbox 输出和评分诊断必须有限。",
        "",
        "## 结论",
        "",
        f"- 综合状态：`{'PASS' if payload['passed'] else 'FAIL'}`",
        "",
        "| 目标词 | 状态 | 正向最低分 | 最弱正向结构损坏 | 门槛 |",
        "|---|---|---:|---|---:|",
    ]
    for item in payload["results"]:
        lines.append(
            f"| {item['word']} | {'PASS' if item['gate_pass'] else 'FAIL'} | "
            f"{_fmt(item['weakest_positive_score'])} | {item['weakest_positive_variant'] or '-'} | "
            f"{_fmt(item['min_required_score'])} |"
        )
    lines.extend(["", "## 分项明细"])
    for item in payload["results"]:
        lines.extend(
            [
                "",
                f"### {item['word']}",
                "",
                "| 变体 | 类型 | 状态 | 分数 | 阈值 | 模式 | result/sequence finite | 帧数保留 | 异常 | 说明 |",
                "|---|---|---|---:|---|---|---|---|---|---|",
            ]
        )
        for row in item["variants"]:
            summary = row.get("sequence_summary") or {}
            threshold = f">= {row['min_score']}" if row["score_required"] else "finite-only"
            lines.append(
                f"| {row['variant']} | {row['kind']} | {'PASS' if row['passed'] else 'FAIL'} | "
                f"{_fmt(row.get('score'))} | {threshold} | {summary.get('mode') or row.get('feature_mode')} | "
                f"{row.get('result_finite')}/{summary.get('finite')} | {summary.get('feature_count_preserved')} | "
                f"{row.get('exception') or '-'} | {row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 该门只允许局部损坏退化为缺失证据，不会把结构损坏当作新的有效动作证据。",
            "- bbox 用例只要求兼容路径有限；bbox 缺少完整指尖语义，因此不要求得到 landmark 级高分。",
            "- 该门不能替代正式 marker 后的真实网页摄像头 `花/跳` 样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run structural cached-JSON robustness gate for flower/jump.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_structural_json_robustness_gate_current"))
    parser.add_argument("--words", nargs="+", default=DEFAULT_WORDS)
    parser.add_argument("--feature-mode", choices=["auto", "landmark"], default="auto")
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--status-timeout-sec", type=float, default=3.0)
    parser.add_argument("--min-score", type=float, default=70.0)
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
            fixture_dir=output_dir / "fixtures",
        )
        for word in args.words
    ]
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "claim_policy": "synthetic cached-JSON structure robustness gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": _load_backend_status(args.backend_url, args.status_timeout_sec),
        "min_score": args.min_score,
        "passed": all(bool(item["gate_pass"]) for item in results),
        "results": results,
    }
    json_path = output_dir / "flower_jump_structural_json_robustness_gate.json"
    md_path = output_dir / "flower_jump_structural_json_robustness_gate.md"
    csv_path = output_dir / "flower_jump_structural_json_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳缓存 JSON 结构鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳缓存 JSON 结构鲁棒性报告：{md_path}")
    print(f"已生成花/跳缓存 JSON 结构鲁棒性 CSV：{csv_path}")
    print(f"综合状态：{'PASS' if payload['passed'] else 'FAIL'}")
    for item in results:
        print(
            f"- {item['word']}: {'PASS' if item['gate_pass'] else 'FAIL'} "
            f"positive_min={_fmt(item['weakest_positive_score'])} "
            f"weakest={item['weakest_positive_variant']}"
        )
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

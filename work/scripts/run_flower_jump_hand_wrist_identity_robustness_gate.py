#!/usr/bin/env python3
"""Stress-test exact-length hand arrays whose wrist identity was displaced.

MediaPipe hand landmark z coordinates are wrist-relative, so landmark index 0
must remain at the z origin. Exact-length arrays that are cyclically shifted,
reversed, or swap the wrist with another point must be treated as a missing
whole hand instead of plausible geometry. Adjacent whole-finger-chain swaps
keep the wrist at index 0 and remain covered by the finger-identity tolerance.

This gate edits cached Holistic JSON only. It does not call /api/score, run
Holistic, move the formal marker, or restart 5080.
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

from run_flower_jump_landmark_noise_robustness_gate import _fmt, _json_default, _load_backend_status
from run_flower_jump_mirror_robustness_gate import _template_json
from score_holistic_sequence_mvp import (
    DEFAULT_SEMANTIC_PROFILE_JSON,
    HAND_WRIST_Z_ORIGIN_MAX,
    _profile_summary,
    load_semantic_profile,
    load_sequence,
    run_pair,
)


REPO_ROOT = Path("/data/WYC/signLanguage")
DEFAULT_TEMPLATE_ROOT = REPO_ROOT / "work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results"
DEFAULT_WEB_ROOT = REPO_ROOT / "work/generated/web_scoring_mvp"
DEFAULT_OUTPUT_BASE = REPO_ROOT / "work/generated/scoring_mvp_run3"
DEFAULT_BACKEND_URL = "http://127.0.0.1:5080"
DEFAULT_WORDS = ["花", "跳"]
HAND_GROUPS = {
    "left_hand_landmarks": "left_hand",
    "right_hand_landmarks": "right_hand",
}
CORRUPTING_OPERATIONS = [
    "rotate_left_1",
    "rotate_left_5",
    "reverse",
    "swap_wrist_thumb_tip",
    "swap_wrist_index_mcp",
]


def _audit_normal_wrist_origins(template_root: Path, web_root: Path) -> Dict[str, Any]:
    paths = sorted(set(template_root.rglob("*holistic_results.json")) | set(web_root.rglob("*holistic_results.json")))
    hand_frames = 0
    violations = 0
    wrist_z_abs: List[float] = []
    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 - malformed files are covered by the structural gate.
            continue
        records = payload.get("records") or payload.get("frames") or payload.get("rows") or []
        if not isinstance(records, list):
            continue
        for record in records:
            if not isinstance(record, dict):
                continue
            result_data = record.get("result_data") if isinstance(record.get("result_data"), dict) else record
            for group in HAND_GROUPS:
                landmarks = result_data.get(group) if isinstance(result_data, dict) else None
                if not isinstance(landmarks, list) or len(landmarks) != 21 or not landmarks:
                    continue
                wrist = landmarks[0] if isinstance(landmarks[0], dict) else {}
                try:
                    value = abs(float(wrist.get("z", math.inf)))
                except (TypeError, ValueError):
                    value = math.inf
                hand_frames += 1
                wrist_z_abs.append(value)
                if not math.isfinite(value) or value > HAND_WRIST_Z_ORIGIN_MAX:
                    violations += 1
    return {
        "file_count": len(paths),
        "hand_frame_count": hand_frames,
        "violation_count": violations,
        "max_wrist_z_abs": max(wrist_z_abs) if wrist_z_abs else None,
        "passed": bool(hand_frames > 0 and violations == 0),
    }


def _spec(
    variant: str,
    group: str,
    pattern: str,
    operation: str,
    kind: str,
    threshold: float,
    expected_masked: bool,
    rationale: str,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "group": group,
        "presence_group": HAND_GROUPS[group],
        "pattern": pattern,
        "operation": operation,
        "kind": kind,
        "gated": True,
        "threshold": threshold,
        "expected_masked": expected_masked,
        "rationale": rationale,
    }


def _variant_specs(word: str, sparse_min_score: float, diagnostic_max_score: float) -> List[Dict[str, Any]]:
    specs: List[Dict[str, Any]] = [
        {
            "variant": "self_reloaded",
            "group": "",
            "presence_group": "",
            "pattern": "none",
            "operation": "none",
            "kind": "positive",
            "gated": True,
            "threshold": 95.0,
            "expected_masked": False,
            "rationale": "原始标准 JSON 重载后应保持近满分。",
        }
    ]
    groups = ["right_hand_landmarks"]
    if word == "跳":
        groups.append("left_hand_landmarks")
    for group in groups:
        for operation in CORRUPTING_OPERATIONS:
            specs.append(
                _spec(
                    f"{group}_{operation}_sparse_masked",
                    group,
                    "sparse_visible",
                    operation,
                    "positive",
                    sparse_min_score,
                    True,
                    "稀疏 exact-length wrist 身份损坏必须整帧屏蔽，正确动作其余帧仍应可评分。",
                )
            )
            specs.append(
                _spec(
                    f"{group}_{operation}_full_recapture",
                    group,
                    "full_visible",
                    operation,
                    "diagnostic",
                    diagnostic_max_score,
                    True,
                    "整段核心手 wrist 身份损坏必须要求重采，不能继续给高分。",
                )
            )
        specs.append(
            _spec(
                f"{group}_adjacent_chain_swap_preserved",
                group,
                "full_visible",
                "swap_index_middle_chain",
                "positive",
                70.0,
                False,
                "相邻整指链交换保留 wrist index 0，应继续由 finger-identity 容错评分而不是整手屏蔽。",
            )
        )
    return specs


def _records(payload: Dict[str, Any]) -> List[Any]:
    records = payload.get("records")
    if not isinstance(records, list):
        raise RuntimeError("hand wrist identity gate requires a records list")
    return records


def _visible_indices(records: Sequence[Any], group: str) -> List[int]:
    indices: List[int] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        result_data = record.get("result_data")
        landmarks = result_data.get(group) if isinstance(result_data, dict) else None
        if isinstance(landmarks, list) and landmarks:
            indices.append(index)
    return indices


def _active_indices(records: Sequence[Any], group: str, pattern: str) -> List[int]:
    if pattern == "none":
        return []
    visible = _visible_indices(records, group)
    if pattern == "full_visible":
        return visible
    if pattern == "sparse_visible":
        sparse = visible[3::7]
        return sparse or visible[len(visible) // 2 : len(visible) // 2 + 1]
    raise ValueError(f"unknown hand wrist identity pattern: {pattern}")


def _mutate_array(landmarks: List[Any], operation: str) -> None:
    if not landmarks:
        return
    if operation == "rotate_left_1":
        landmarks[:] = landmarks[1:] + landmarks[:1]
    elif operation == "rotate_left_5":
        landmarks[:] = landmarks[5:] + landmarks[:5]
    elif operation == "reverse":
        landmarks.reverse()
    elif operation == "swap_wrist_thumb_tip":
        landmarks[0], landmarks[4] = landmarks[4], landmarks[0]
    elif operation == "swap_wrist_index_mcp":
        landmarks[0], landmarks[5] = landmarks[5], landmarks[0]
    elif operation == "swap_index_middle_chain":
        for left, right in zip(range(5, 9), range(9, 13)):
            landmarks[left], landmarks[right] = landmarks[right], landmarks[left]
    elif operation != "none":
        raise ValueError(f"unknown hand wrist identity operation: {operation}")


def _write_fixture(source_json: Path, dest_json: Path, spec: Dict[str, Any]) -> Dict[str, Any]:
    payload = copy.deepcopy(json.loads(source_json.read_text(encoding="utf-8")))
    records = _records(payload)
    active = _active_indices(records, str(spec["group"]), str(spec["pattern"])) if spec["group"] else []
    wrist_z_abs: List[float] = []
    for index in active:
        record = records[index]
        result_data = record.get("result_data") if isinstance(record, dict) else None
        landmarks = result_data.get(spec["group"]) if isinstance(result_data, dict) else None
        if not isinstance(landmarks, list) or not landmarks:
            continue
        _mutate_array(landmarks, str(spec["operation"]))
        wrist = landmarks[0] if landmarks and isinstance(landmarks[0], dict) else {}
        try:
            wrist_z_abs.append(abs(float(wrist.get("z", 0.0))))
        except (TypeError, ValueError):
            wrist_z_abs.append(math.inf)
    dest_json.parent.mkdir(parents=True, exist_ok=True)
    dest_json.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return {
        "active_indices": active,
        "changed_frame_count": len(wrist_z_abs),
        "wrist_z_abs_min": min(wrist_z_abs) if wrist_z_abs else None,
        "wrist_z_abs_max": max(wrist_z_abs) if wrist_z_abs else None,
        "total_records": len(records),
    }


def _sequence_finite(sequence: Any) -> bool:
    return all(
        bool(math.isfinite(float(value)))
        for feature in sequence.features
        for values in (feature.vector, feature.mask)
        for value in values
    )


def _result_finite(result: Dict[str, Any]) -> bool:
    try:
        return all(math.isfinite(float(result.get(key))) for key in ("prototype_score", "dtw_distance", "normalized_distance"))
    except (TypeError, ValueError):
        return False


def _run_word(
    word: str,
    template_root: Path,
    semantic_profile_json: Path,
    feature_mode: str,
    sparse_min_score: float,
    diagnostic_max_score: float,
    fixture_dir: Path,
) -> Dict[str, Any]:
    standard_json = _template_json(template_root, word)
    standard = load_sequence(standard_json, feature_mode, force_bbox=False, apply_sidecar_weights=False)
    profile = load_semantic_profile(word, semantic_profile_json)
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(word, sparse_min_score, diagnostic_max_score):
        fixture_json = fixture_dir / word / f"{spec['variant']}.json"
        detail = _write_fixture(standard_json, fixture_json, spec)
        row: Dict[str, Any] = {**spec, "fixture_json": str(fixture_json), **detail}
        try:
            query = load_sequence(fixture_json, feature_mode, force_bbox=False, apply_sidecar_weights=False)
            result = run_pair(standard, query, semantic_profile=profile, target_word=word, enable_cross_check=False)
        except Exception as exc:  # noqa: BLE001 - loader/scorer crashes are gate failures.
            row.update(
                {
                    "exception": f"{type(exc).__name__}: {exc}",
                    "score": None,
                    "result_finite": False,
                    "sequence_finite": False,
                    "wrist_identity_handling_ok": False,
                    "capture_quality": {},
                    "passed": False,
                }
            )
        else:
            active = [int(index) for index in detail["active_indices"]]
            if spec["group"]:
                active_presence = [
                    bool(index < len(query.features) and query.features[index].presence.get(spec["presence_group"], False))
                    for index in active
                ]
                if spec["expected_masked"]:
                    wrist_identity_handling_ok = bool(active) and not any(active_presence)
                else:
                    wrist_identity_handling_ok = bool(active) and all(active_presence)
            else:
                wrist_identity_handling_ok = True
            capture_quality = (result.get("score_scale") or {}).get("capture_quality") or {}
            score = float(result["prototype_score"])
            result_finite = _result_finite(result)
            sequence_finite = _sequence_finite(query)
            if spec["kind"] == "diagnostic":
                semantic_ok = capture_quality.get("status") in {"needs_recapture", "semantic_mismatch"}
                score_ok = score <= float(spec["threshold"])
            else:
                semantic_ok = True
                score_ok = score >= float(spec["threshold"])
            row.update(
                {
                    "exception": "",
                    "score": score,
                    "dtw_distance": float(result["dtw_distance"]),
                    "normalized_distance": float(result["normalized_distance"]),
                    "result_finite": result_finite,
                    "sequence_finite": sequence_finite,
                    "wrist_identity_handling_ok": wrist_identity_handling_ok,
                    "capture_quality": capture_quality,
                    "passed": bool(
                        result_finite
                        and sequence_finite
                        and wrist_identity_handling_ok
                        and semantic_ok
                        and score_ok
                    ),
                }
            )
        rows.append(row)
    positives = [row for row in rows if row["kind"] == "positive" and row.get("score") is not None]
    diagnostics = [row for row in rows if row["kind"] == "diagnostic" and row.get("score") is not None]
    weakest = min(positives, key=lambda row: float(row["score"])) if positives else None
    strongest_diagnostic = max(diagnostics, key=lambda row: float(row["score"])) if diagnostics else None
    return {
        "word": word,
        "standard_json": str(standard_json),
        "standard_length": len(standard.features),
        "semantic_profile": _profile_summary(profile),
        "gate_pass": all(bool(row["passed"]) for row in rows),
        "weakest_positive_score": float(weakest["score"]) if weakest else None,
        "weakest_positive_variant": weakest["variant"] if weakest else "",
        "strongest_diagnostic_score": float(strongest_diagnostic["score"]) if strongest_diagnostic else None,
        "strongest_diagnostic_variant": strongest_diagnostic["variant"] if strongest_diagnostic else "",
        "sparse_min_required_score": sparse_min_score,
        "diagnostic_max_score": diagnostic_max_score,
        "variants": rows,
    }


def _write_rows_csv(path: Path, results: Sequence[Dict[str, Any]]) -> None:
    fields = [
        "word",
        "variant",
        "kind",
        "passed",
        "score",
        "threshold",
        "group",
        "pattern",
        "operation",
        "changed_frame_count",
        "wrist_z_abs_min",
        "wrist_z_abs_max",
        "expected_masked",
        "wrist_identity_handling_ok",
        "capture_quality",
        "capture_reason",
        "exception",
    ]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for item in results:
            for row in item["variants"]:
                quality = row.get("capture_quality") or {}
                writer.writerow(
                    {
                        "word": item["word"],
                        "variant": row.get("variant"),
                        "kind": row.get("kind"),
                        "passed": row.get("passed"),
                        "score": row.get("score"),
                        "threshold": row.get("threshold"),
                        "group": row.get("group"),
                        "pattern": row.get("pattern"),
                        "operation": row.get("operation"),
                        "changed_frame_count": row.get("changed_frame_count"),
                        "wrist_z_abs_min": row.get("wrist_z_abs_min"),
                        "wrist_z_abs_max": row.get("wrist_z_abs_max"),
                        "expected_masked": row.get("expected_masked"),
                        "wrist_identity_handling_ok": row.get("wrist_identity_handling_ok"),
                        "capture_quality": quality.get("status"),
                        "capture_reason": quality.get("reason"),
                        "exception": row.get("exception"),
                    }
                )


def _build_markdown(payload: Dict[str, Any]) -> str:
    audit = payload["normal_wrist_origin_audit"]
    lines = [
        "# 花/跳 Hand Wrist 身份完整性鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- wrist-z 原点阈值：`{payload['hand_wrist_z_origin_max']}`",
        f"- 正常证据审计：`{audit['file_count']}` 个模板/网页 JSON、`{audit['hand_frame_count']}` 个非空手帧，违规 `z0`=`{audit['violation_count']}`，最大 `|z0|`=`{audit['max_wrist_z_abs']}`。",
        "- 固定契约：MediaPipe hand landmark `z` 以 wrist 为原点，因此 index `0` 的绝对 z 必须接近零；等长数组若把 wrist 移到其它 index，整手按缺失处理。",
        "- 控制组：相邻整指链交换不移动 wrist index `0`，必须保留并继续由 finger-identity 容错评分。",
        "- 口径：只写缓存 Holistic JSON fixture；不调用 `/api/score`、不运行 Holistic、不移动 marker、不重启 5080。",
        "",
        "## 结论",
        "",
        f"- 综合状态：`{'PASS' if payload['passed'] else 'FAIL'}`",
        "",
        "| 目标词 | 状态 | 正向最低分 | 最弱正向变体 | 整段损坏诊断最高分 | 最强诊断变体 |",
        "|---|---|---:|---|---:|---|",
    ]
    for item in payload["results"]:
        lines.append(
            f"| {item['word']} | {'PASS' if item['gate_pass'] else 'FAIL'} | "
            f"{_fmt(item['weakest_positive_score'])} | {item['weakest_positive_variant']} | "
            f"{_fmt(item['strongest_diagnostic_score'])} | {item['strongest_diagnostic_variant']} |"
        )
    lines.extend(["", "## 分项明细", ""])
    for item in payload["results"]:
        lines.extend(
            [
                f"### {item['word']}",
                "",
                "| 变体 | 类型 | 状态 | 分数 | 阈值 | 损坏帧 | 预期屏蔽 | 身份处理正确 | capture_quality |",
                "|---|---|---|---:|---:|---:|---|---|---|",
            ]
        )
        for row in item["variants"]:
            quality = row.get("capture_quality") or {}
            lines.append(
                f"| {row['variant']} | {row['kind']} | {'PASS' if row['passed'] else 'FAIL'} | "
                f"{_fmt(row.get('score'))} | {_fmt(row.get('threshold'))} | {row.get('changed_frame_count')} | "
                f"{row.get('expected_masked')} | {row.get('wrist_identity_handling_ok')} | "
                f"{quality.get('status') or '-'}:{quality.get('reason') or '-'} |"
            )
        lines.append("")
    lines.extend(
        [
            "## 说明",
            "",
            "- 正常证据审计是硬门：当前缓存中的任何非空手帧若违反 wrist-z 原点契约，该门都会失败并要求重新审计阈值或输入格式。",
            "- 该门补充 exact-length 数组的 wrist 根身份损坏，不替代允许相邻 finger-chain 标签混淆的 finger-identity-jitter 门。",
            "- 该门是缓存 JSON 压力测试，不替代正式 marker 后真实网页摄像头复测。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run hand wrist identity robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--web-root", default=str(DEFAULT_WEB_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_hand_wrist_identity_robustness_gate_current"))
    parser.add_argument("--words", nargs="+", default=DEFAULT_WORDS)
    parser.add_argument("--feature-mode", choices=["auto", "landmark"], default="auto")
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--status-timeout-sec", type=float, default=3.0)
    parser.add_argument("--sparse-min-score", type=float, default=75.0)
    parser.add_argument("--diagnostic-max-score", type=float, default=55.0)
    args = parser.parse_args(argv)

    template_root = Path(args.template_root)
    web_root = Path(args.web_root)
    semantic_profile_json = Path(args.semantic_profile_json)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    fixture_dir = output_dir / "fixtures"
    results = [
        _run_word(
            word,
            template_root,
            semantic_profile_json,
            args.feature_mode,
            args.sparse_min_score,
            args.diagnostic_max_score,
            fixture_dir,
        )
        for word in args.words
    ]
    normal_wrist_origin_audit = _audit_normal_wrist_origins(template_root, web_root)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "claim_policy": "synthetic hand-wrist-identity robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "web_root": str(web_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": _load_backend_status(args.backend_url, args.status_timeout_sec),
        "hand_wrist_z_origin_max": HAND_WRIST_Z_ORIGIN_MAX,
        "normal_wrist_origin_audit": normal_wrist_origin_audit,
        "sparse_min_score": args.sparse_min_score,
        "diagnostic_max_score": args.diagnostic_max_score,
        "results": results,
        "passed": bool(normal_wrist_origin_audit["passed"] and all(bool(item["gate_pass"]) for item in results)),
    }

    json_path = output_dir / "flower_jump_hand_wrist_identity_robustness_gate.json"
    md_path = output_dir / "flower_jump_hand_wrist_identity_robustness_gate.md"
    csv_path = output_dir / "flower_jump_hand_wrist_identity_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成 Hand Wrist 身份完整性 JSON：{json_path}")
    print(f"已生成 Hand Wrist 身份完整性报告：{md_path}")
    print(f"综合状态：{'PASS' if payload['passed'] else 'FAIL'}")
    for item in results:
        print(
            f"- {item['word']}: {'PASS' if item['gate_pass'] else 'FAIL'} "
            f"positive_min={_fmt(item['weakest_positive_score'])} "
            f"diagnostic_max={_fmt(item['strongest_diagnostic_score'])}"
        )
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

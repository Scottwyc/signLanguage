#!/usr/bin/env python3
"""Stress-test exact-length hand arrays with impossible internal joint order.

This gate targets severe hand-landmark permutations that keep wrist index 0
intact but make multiple finger chains anatomically impossible. It edits cached
Holistic JSON only and does not call /api/score, run Holistic, move the formal
marker, or restart 5080.
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

from run_flower_jump_hand_wrist_identity_robustness_gate import (
    _active_indices,
    _records,
    _result_finite,
    _sequence_finite,
)
from run_flower_jump_landmark_noise_robustness_gate import _fmt, _json_default, _load_backend_status
from run_flower_jump_mirror_robustness_gate import _template_json
from score_holistic_sequence_mvp import (
    DEFAULT_SEMANTIC_PROFILE_JSON,
    HAND_FINGER_CHAINS,
    HAND_INTERNAL_TOPOLOGY_BACKTRACK_TURN_MIN,
    HAND_INTERNAL_TOPOLOGY_PROXIMAL_DISTAL_RATIO_MIN,
    HAND_INTERNAL_TOPOLOGY_REVERSED_CHAIN_MIN,
    HAND_INTERNAL_TOPOLOGY_REVERSED_RATIO_MAX,
    _hand_internal_topology_metrics,
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
    "reverse_internal_all",
    "rotate_internal_1",
    "rotate_internal_2",
    "rotate_internal_5",
    "reverse_each_chain",
    "swap_base_tip_each_chain",
    "swap_pip_dip_each_chain",
]


def _parse_hand(landmarks: Any) -> Optional[np.ndarray]:
    if not isinstance(landmarks, list) or len(landmarks) != 21:
        return None
    try:
        hand = np.asarray(
            [[float(item["x"]), float(item["y"]), float(item["z"])] for item in landmarks],
            dtype=np.float32,
        )
    except (KeyError, TypeError, ValueError):
        return None
    return hand if hand.shape == (21, 3) and bool(np.isfinite(hand).all()) else None


def _audit_normal_topology(template_root: Path, web_root: Path) -> Dict[str, Any]:
    paths = sorted(set(template_root.rglob("*holistic_results.json")) | set(web_root.rglob("*holistic_results.json")))
    hand_frames = 0
    violations = 0
    max_backtrack_turn_count = 0
    max_reversed_chain_count = 0
    min_median_proximal_distal_ratio = math.inf
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
                hand = _parse_hand(result_data.get(group) if isinstance(result_data, dict) else None)
                if hand is None:
                    continue
                metrics = _hand_internal_topology_metrics(hand, np.ones(21, dtype=np.float32))
                if not metrics:
                    continue
                hand_frames += 1
                violations += int(bool(metrics["corrupted"]))
                max_backtrack_turn_count = max(max_backtrack_turn_count, int(metrics["backtrack_turn_count"]))
                max_reversed_chain_count = max(max_reversed_chain_count, int(metrics["reversed_chain_count"]))
                min_median_proximal_distal_ratio = min(
                    min_median_proximal_distal_ratio,
                    float(metrics["median_proximal_distal_ratio"]),
                )
    return {
        "file_count": len(paths),
        "hand_frame_count": hand_frames,
        "violation_count": violations,
        "max_backtrack_turn_count": max_backtrack_turn_count,
        "max_reversed_chain_count": max_reversed_chain_count,
        "min_median_proximal_distal_ratio": (
            min_median_proximal_distal_ratio if math.isfinite(min_median_proximal_distal_ratio) else None
        ),
        "passed": bool(hand_frames > 0 and violations == 0),
    }


def _spec(
    variant: str,
    group: str,
    pattern: str,
    operation: str,
    kind: str,
    threshold: float,
    expected_masked_min_rate: float,
    expected_masked_max_rate: float,
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
        "expected_masked_min_rate": expected_masked_min_rate,
        "expected_masked_max_rate": expected_masked_max_rate,
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
            "expected_masked_min_rate": 0.0,
            "expected_masked_max_rate": 0.0,
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
                    0.8,
                    1.0,
                    "稀疏 exact-length 内部拓扑损坏应被屏蔽，正确动作其余帧仍应可评分。",
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
                    0.8,
                    1.0,
                    "整段核心手内部拓扑损坏必须要求重采，不能继续给高分。",
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
                0.0,
                0.0,
                "相邻整指链交换保持各链内部顺序，应继续由 finger-identity 容错评分。",
            )
        )
    return specs


def _mutate_array(landmarks: List[Any], operation: str) -> None:
    if not landmarks:
        return
    original = list(landmarks)
    if operation == "reverse_internal_all":
        landmarks[:] = [original[0], *reversed(original[1:])]
    elif operation.startswith("rotate_internal_"):
        shift = int(operation.rsplit("_", 1)[1])
        internal = original[1:]
        landmarks[:] = [original[0], *internal[shift:], *internal[:shift]]
    elif operation == "reverse_each_chain":
        for chain in HAND_FINGER_CHAINS:
            for target, source in zip(chain, reversed(chain)):
                landmarks[target] = original[source]
    elif operation == "swap_base_tip_each_chain":
        for chain in HAND_FINGER_CHAINS:
            landmarks[chain[0]], landmarks[chain[3]] = original[chain[3]], original[chain[0]]
    elif operation == "swap_pip_dip_each_chain":
        for chain in HAND_FINGER_CHAINS:
            landmarks[chain[1]], landmarks[chain[2]] = original[chain[2]], original[chain[1]]
    elif operation == "swap_index_middle_chain":
        for left, right in zip(HAND_FINGER_CHAINS[1], HAND_FINGER_CHAINS[2]):
            landmarks[left], landmarks[right] = original[right], original[left]
    elif operation != "none":
        raise ValueError(f"unknown hand internal topology operation: {operation}")


def _write_fixture(source_json: Path, dest_json: Path, spec: Dict[str, Any]) -> Dict[str, Any]:
    payload = copy.deepcopy(json.loads(source_json.read_text(encoding="utf-8")))
    records = _records(payload)
    active = _active_indices(records, str(spec["group"]), str(spec["pattern"])) if spec["group"] else []
    corrupted_before_load_count = 0
    backtrack_counts: List[int] = []
    reversed_chain_counts: List[int] = []
    ratios: List[float] = []
    for index in active:
        record = records[index]
        result_data = record.get("result_data") if isinstance(record, dict) else None
        landmarks = result_data.get(spec["group"]) if isinstance(result_data, dict) else None
        if not isinstance(landmarks, list) or len(landmarks) != 21:
            continue
        _mutate_array(landmarks, str(spec["operation"]))
        hand = _parse_hand(landmarks)
        metrics = (
            _hand_internal_topology_metrics(hand, np.ones(21, dtype=np.float32))
            if hand is not None
            else None
        )
        if not metrics:
            continue
        corrupted_before_load_count += int(bool(metrics["corrupted"]))
        backtrack_counts.append(int(metrics["backtrack_turn_count"]))
        reversed_chain_counts.append(int(metrics["reversed_chain_count"]))
        ratios.append(float(metrics["median_proximal_distal_ratio"]))
    dest_json.parent.mkdir(parents=True, exist_ok=True)
    dest_json.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return {
        "active_indices": active,
        "changed_frame_count": len(backtrack_counts),
        "corrupted_before_load_count": corrupted_before_load_count,
        "corrupted_before_load_rate": (
            corrupted_before_load_count / len(active) if active else 0.0
        ),
        "backtrack_turn_count_min": min(backtrack_counts) if backtrack_counts else None,
        "backtrack_turn_count_max": max(backtrack_counts) if backtrack_counts else None,
        "reversed_chain_count_min": min(reversed_chain_counts) if reversed_chain_counts else None,
        "reversed_chain_count_max": max(reversed_chain_counts) if reversed_chain_counts else None,
        "median_proximal_distal_ratio_min": min(ratios) if ratios else None,
        "median_proximal_distal_ratio_max": max(ratios) if ratios else None,
        "total_records": len(records),
    }


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
                    "masked_count": 0,
                    "masked_rate": 0.0,
                    "topology_handling_ok": False,
                    "capture_quality": {},
                    "passed": False,
                }
            )
        else:
            active = [int(index) for index in detail["active_indices"]]
            if spec["group"]:
                masked_count = sum(
                    not bool(
                        index < len(query.features)
                        and query.features[index].presence.get(spec["presence_group"], False)
                    )
                    for index in active
                )
                masked_rate = masked_count / len(active) if active else 0.0
                topology_handling_ok = bool(active) and (
                    float(spec["expected_masked_min_rate"])
                    <= masked_rate
                    <= float(spec["expected_masked_max_rate"])
                )
            else:
                masked_count = 0
                masked_rate = 0.0
                topology_handling_ok = True
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
                    "masked_count": masked_count,
                    "masked_rate": masked_rate,
                    "topology_handling_ok": topology_handling_ok,
                    "capture_quality": capture_quality,
                    "passed": bool(
                        result_finite
                        and sequence_finite
                        and topology_handling_ok
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
        "corrupted_before_load_count",
        "masked_count",
        "masked_rate",
        "topology_handling_ok",
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
                        "corrupted_before_load_count": row.get("corrupted_before_load_count"),
                        "masked_count": row.get("masked_count"),
                        "masked_rate": row.get("masked_rate"),
                        "topology_handling_ok": row.get("topology_handling_ok"),
                        "capture_quality": quality.get("status"),
                        "capture_reason": quality.get("reason"),
                        "exception": row.get("exception"),
                    }
                )


def _build_markdown(payload: Dict[str, Any]) -> str:
    audit = payload["normal_topology_audit"]
    lines = [
        "# 花/跳 Hand 内部拓扑完整性鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        (
            "- 硬边界：backtrack turns "
            f"`>={payload['topology_thresholds']['backtrack_turn_min']}`，或非拇指 proximal/distal "
            f"中位比 `<{payload['topology_thresholds']['proximal_distal_ratio_min']}`，或全部指链反向且该比值 "
            f"`<{payload['topology_thresholds']['reversed_ratio_max']}`。"
        ),
        (
            f"- 正常证据审计：`{audit['file_count']}` 个模板/网页 JSON、`{audit['hand_frame_count']}` 个非空手帧，"
            f"违规 `{audit['violation_count']}`；正常最大 backtrack `{audit['max_backtrack_turn_count']}`，"
            f"最大反向链 `{audit['max_reversed_chain_count']}`，最小 proximal/distal 中位比 "
            f"`{audit['min_median_proximal_distal_ratio']}`。"
        ),
        "- 控制组：相邻整指链交换保持各指链内部顺序，必须保留并继续由 finger-identity 容错评分。",
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
                "| 变体 | 类型 | 状态 | 分数 | 阈值 | 损坏帧 | 屏蔽率 | 拓扑处理正确 | capture_quality |",
                "|---|---|---|---:|---:|---:|---:|---|---|",
            ]
        )
        for row in item["variants"]:
            quality = row.get("capture_quality") or {}
            lines.append(
                f"| {row['variant']} | {row['kind']} | {'PASS' if row['passed'] else 'FAIL'} | "
                f"{_fmt(row.get('score'))} | {_fmt(row.get('threshold'))} | {row.get('changed_frame_count')} | "
                f"{_fmt(row.get('masked_rate'))} | {row.get('topology_handling_ok')} | "
                f"{quality.get('status') or '-'}:{quality.get('reason') or '-'} |"
            )
        lines.append("")
    lines.extend(
        [
            "## 说明",
            "",
            "- 该门只屏蔽具有强解剖矛盾的内部索引损坏，不声称识别所有可能的等长 permutation。",
            "- 正常证据审计是硬门；阈值若命中当前任一正常手帧，该门失败并要求重新审计。",
            "- 该门补充 wrist 根身份门和 finger-identity-jitter 门，不替代正式 marker 后真实网页摄像头复测。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run hand internal topology robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--web-root", default=str(DEFAULT_WEB_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_hand_internal_topology_robustness_gate_current"))
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
    normal_topology_audit = _audit_normal_topology(template_root, web_root)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "claim_policy": "synthetic hand-internal-topology robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "web_root": str(web_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": _load_backend_status(args.backend_url, args.status_timeout_sec),
        "topology_thresholds": {
            "backtrack_turn_min": HAND_INTERNAL_TOPOLOGY_BACKTRACK_TURN_MIN,
            "proximal_distal_ratio_min": HAND_INTERNAL_TOPOLOGY_PROXIMAL_DISTAL_RATIO_MIN,
            "reversed_chain_min": HAND_INTERNAL_TOPOLOGY_REVERSED_CHAIN_MIN,
            "reversed_ratio_max": HAND_INTERNAL_TOPOLOGY_REVERSED_RATIO_MAX,
        },
        "normal_topology_audit": normal_topology_audit,
        "sparse_min_score": args.sparse_min_score,
        "diagnostic_max_score": args.diagnostic_max_score,
        "results": results,
        "passed": bool(normal_topology_audit["passed"] and all(bool(item["gate_pass"]) for item in results)),
    }

    json_path = output_dir / "flower_jump_hand_internal_topology_robustness_gate.json"
    md_path = output_dir / "flower_jump_hand_internal_topology_robustness_gate.md"
    csv_path = output_dir / "flower_jump_hand_internal_topology_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成 Hand 内部拓扑完整性 JSON：{json_path}")
    print(f"已生成 Hand 内部拓扑完整性报告：{md_path}")
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

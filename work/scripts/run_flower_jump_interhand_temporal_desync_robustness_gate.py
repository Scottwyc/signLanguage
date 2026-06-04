#!/usr/bin/env python3
"""Stress-test flower/jump scoring against one-hand temporal desync.

Real browser captures can include slight left/right hand phase offsets from
user style, sampling jitter, or brief detector instability. The scorer should
tolerate one or two frames of hand-specific lead/lag, especially for the
two-hand relation in "跳", while stronger offsets are recorded as diagnostic
boundaries.

This script edits cached skeleton sequences in memory only. It does not call
/api/score, run Holistic, move the web marker, or restart 5080.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from run_flower_jump_landmark_noise_robustness_gate import (
    _fmt,
    _hand_array,
    _json_default,
    _load_backend_status,
    _set_hand_group,
)
from run_flower_jump_mirror_robustness_gate import _strip_to_base_groups, _template_json
from score_holistic_sequence_mvp import (
    DEFAULT_SEMANTIC_PROFILE_JSON,
    FrameFeature,
    SequenceData,
    _clone_frame,
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
HAND_GROUPS = {"left_hand", "right_hand"}


def _shifted_hand_sequence(
    seq: SequenceData,
    name: str,
    *,
    shifts: Dict[str, int],
    profile: Any,
) -> Tuple[SequenceData, Dict[str, Any]]:
    base = _strip_to_base_groups(seq)
    features: List[FrameFeature] = []
    changed_hand_frames = 0
    n = len(base.features)
    for idx, frame in enumerate(base.features):
        vector = frame.vector.copy()
        mask = frame.mask.copy()
        presence = dict(frame.presence)
        for group, shift in shifts.items():
            if group not in HAND_GROUPS or n <= 0:
                continue
            source_idx = max(0, min(n - 1, idx - int(shift)))
            source_frame = base.features[source_idx]
            coords, valid = _hand_array(source_frame, group)
            if coords is None or valid is None:
                continue
            if source_idx != idx:
                changed_hand_frames += 1
            _set_hand_group(frame, vector, mask, group, coords.copy(), valid.copy())
            presence[group] = bool(valid.any())
        item = _clone_frame(frame, vector=vector, mask=mask)
        item.presence = presence
        features.append(item)
    transformed = SequenceData(
        source=f"{base.source}::{name}",
        mode=base.mode,
        fps=base.fps,
        total_frames=base.total_frames,
        features=features,
    )
    detail = {
        "shifts": {str(key): int(value) for key, value in shifts.items()},
        "max_abs_shift_frames": max((abs(int(value)) for value in shifts.values()), default=0),
        "changed_hand_frames": changed_hand_frames,
        "total_frames": n,
    }
    return _sequence_with_relative_motion_features(transformed, profile), detail


def _spec(
    variant: str,
    kind: str,
    *,
    shifts: Dict[str, int],
    rationale: str,
    min_score: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "variant": variant,
        "kind": kind,
        "shifts": {str(key): int(value) for key, value in shifts.items()},
        "min_score": min_score,
        "gated": kind == "positive",
        "rationale": rationale,
    }


def _variant_specs(word: str, min_score: float) -> List[Dict[str, Any]]:
    specs = [
        _spec(
            "self_recomputed",
            "positive",
            shifts={},
            min_score=95.0,
            rationale="标准序列剥离基础组后重建 motion/relation 特征，应保持近满分。",
        )
    ]
    if word == "花":
        return specs + [
            _spec(
                "right_hand_delay_1f",
                "positive",
                shifts={"right_hand": 1},
                min_score=min_score,
                rationale="开花核心手滞后 1 帧，模拟轻微采样/检测延迟。",
            ),
            _spec(
                "right_hand_advance_1f",
                "positive",
                shifts={"right_hand": -1},
                min_score=min_score,
                rationale="开花核心手提前 1 帧，模拟动作窗口轻微错位。",
            ),
            _spec(
                "right_hand_delay_2f",
                "positive",
                shifts={"right_hand": 2},
                min_score=min_score,
                rationale="开花核心手滞后 2 帧，验证 DTW 对轻度相位偏移的吸收。",
            ),
            _spec(
                "right_hand_advance_2f",
                "positive",
                shifts={"right_hand": -2},
                min_score=min_score,
                rationale="开花核心手提前 2 帧，仍应保持正常评分。",
            ),
            _spec(
                "right_hand_delay_4f_diagnostic",
                "diagnostic",
                shifts={"right_hand": 4},
                rationale="开花核心手滞后 4 帧属于强边界，仅记录诊断分数。",
            ),
            _spec(
                "right_hand_advance_4f_diagnostic",
                "diagnostic",
                shifts={"right_hand": -4},
                rationale="开花核心手提前 4 帧属于强边界，仅记录诊断分数。",
            ),
        ]
    if word == "跳":
        return specs + [
            _spec(
                "right_hand_delay_1f",
                "positive",
                shifts={"right_hand": 1},
                min_score=min_score,
                rationale="右手两指小人相对左手地面滞后 1 帧，双手关系仍应可评分。",
            ),
            _spec(
                "right_hand_advance_1f",
                "positive",
                shifts={"right_hand": -1},
                min_score=min_score,
                rationale="右手两指小人相对左手地面提前 1 帧，双手关系仍应可评分。",
            ),
            _spec(
                "left_hand_delay_1f",
                "positive",
                shifts={"left_hand": 1},
                min_score=min_score,
                rationale="左手地面滞后 1 帧，验证关系 fallback 不因轻微支撑相位差失败。",
            ),
            _spec(
                "left_hand_advance_1f",
                "positive",
                shifts={"left_hand": -1},
                min_score=min_score,
                rationale="左手地面提前 1 帧，仍应保持跳跃关系可评分。",
            ),
            _spec(
                "right_hand_delay_2f",
                "positive",
                shifts={"right_hand": 2},
                min_score=min_score,
                rationale="右手两指小人滞后 2 帧，模拟较明显但可接受的手间相位差。",
            ),
            _spec(
                "right_hand_advance_2f",
                "positive",
                shifts={"right_hand": -2},
                min_score=min_score,
                rationale="右手两指小人提前 2 帧，仍应保持正常/边界分。",
            ),
            _spec(
                "left_hand_delay_2f",
                "positive",
                shifts={"left_hand": 2},
                min_score=min_score,
                rationale="左手地面滞后 2 帧，双手关系仍应能被局部段恢复。",
            ),
            _spec(
                "left_hand_advance_2f",
                "positive",
                shifts={"left_hand": -2},
                min_score=min_score,
                rationale="左手地面提前 2 帧，作为轻中度手间相位差正向门。",
            ),
            _spec(
                "both_hands_opposite_1f",
                "positive",
                shifts={"right_hand": 1, "left_hand": -1},
                min_score=min_score,
                rationale="左右手相反方向各错 1 帧，覆盖两手采样相位差叠加。",
            ),
            _spec(
                "both_hands_opposite_2f_diagnostic",
                "diagnostic",
                shifts={"right_hand": 2, "left_hand": -2},
                rationale="左右手相反方向各错 2 帧属于强边界，仅记录诊断分数。",
            ),
            _spec(
                "right_hand_delay_4f_diagnostic",
                "diagnostic",
                shifts={"right_hand": 4},
                rationale="右手滞后 4 帧属于强边界，仅记录诊断分数。",
            ),
            _spec(
                "left_hand_delay_4f_diagnostic",
                "diagnostic",
                shifts={"left_hand": 4},
                rationale="左手滞后 4 帧属于强边界，仅记录诊断分数。",
            ),
        ]
    return specs


def _row_passed(row: Dict[str, Any]) -> bool:
    if row["kind"] == "positive":
        return float(row["score"]) >= float(row["min_score"])
    return True


def _run_word(
    word: str,
    template_root: Path,
    semantic_profile_json: Path,
    feature_mode: str,
    min_score: float,
) -> Dict[str, Any]:
    standard_json = _template_json(template_root, word)
    loaded_standard = load_sequence(standard_json, feature_mode, force_bbox=False)
    profile = load_semantic_profile(word, semantic_profile_json)
    standard, standard_detail = _shifted_hand_sequence(
        loaded_standard,
        "standard_base",
        shifts={},
        profile=profile,
    )
    rows: List[Dict[str, Any]] = []
    for spec in _variant_specs(word, min_score):
        query, detail = _shifted_hand_sequence(
            loaded_standard,
            str(spec["variant"]),
            shifts=spec["shifts"],
            profile=profile,
        )
        result = run_pair(standard, query, semantic_profile=profile, target_word=word, enable_cross_check=False)
        score_scale = result.get("score_scale") or {}
        row = {
            "variant": spec["variant"],
            "kind": spec["kind"],
            "gated": bool(spec["gated"]),
            "min_score": spec.get("min_score"),
            "rationale": spec["rationale"],
            **detail,
            "score": float(result["prototype_score"]),
            "dtw_distance": float(result["dtw_distance"]),
            "normalized_distance": float(result["normalized_distance"]),
            "alignment_policy": result.get("alignment_policy"),
            "capture_quality": score_scale.get("capture_quality"),
            "semantic_floor": score_scale.get("semantic_floor"),
            "action_window": result.get("action_window"),
        }
        row["passed"] = _row_passed(row)
        rows.append(row)
    positive_rows = [row for row in rows if row["kind"] == "positive"]
    diagnostic_rows = [row for row in rows if row["kind"] == "diagnostic"]
    weakest_positive = min(positive_rows, key=lambda row: float(row["score"])) if positive_rows else None
    weakest_diagnostic = min(diagnostic_rows, key=lambda row: float(row["score"])) if diagnostic_rows else None
    return {
        "word": word,
        "standard_json": str(standard_json),
        "standard_length": len(standard.features),
        "standard_shift_detail": standard_detail,
        "semantic_profile": _profile_summary(profile),
        "gate_pass": all(bool(row["passed"]) for row in rows if row["gated"]),
        "weakest_positive_score": float(weakest_positive["score"]) if weakest_positive else None,
        "weakest_positive_variant": weakest_positive["variant"] if weakest_positive else "",
        "weakest_diagnostic_score": float(weakest_diagnostic["score"]) if weakest_diagnostic else None,
        "weakest_diagnostic_variant": weakest_diagnostic["variant"] if weakest_diagnostic else "",
        "min_required_score": min_score,
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
        "max_abs_shift_frames",
        "changed_hand_frames",
        "total_frames",
        "shifts",
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
                        "max_abs_shift_frames": row.get("max_abs_shift_frames"),
                        "changed_hand_frames": row.get("changed_hand_frames"),
                        "total_frames": row.get("total_frames"),
                        "shifts": json.dumps(row.get("shifts") or {}, ensure_ascii=False, sort_keys=True),
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
        "# 花/跳手间时序错位鲁棒性门",
        "",
        f"- 生成时间：`{payload['generated_at']}`",
        f"- 标准库：`{payload['template_root']}`",
        f"- 语义 profile：`{payload['semantic_profile_json']}`",
        "- 口径：只读缓存 Holistic JSON，将单只手的 landmark 序列相对其它骨架组前后错开，并重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。",
        "- 目标：`花` 的核心手轻微动作窗口错位、`跳` 的左右手轻微相位差仍保持可评分；强错位只记录诊断边界。",
        "",
    ]
    backend = payload.get("backend_status") or {}
    if backend.get("ok"):
        data = backend.get("payload") or {}
        worker = data.get("worker") or {}
        scoring = data.get("scoring_module") or {}
        process = worker.get("process") or {}
        lines.append(
            f"- 5080 状态：worker=`{worker.get('status')}`，pid=`{process.get('pid') or ((worker.get('ready_payload') or {}).get('pid'))}`，"
            f"reload_count=`{scoring.get('reload_count')}`，last_reload_error=`{scoring.get('last_reload_error')}`"
        )
    else:
        lines.append(f"- 5080 状态：读取失败 `{backend.get('error') or '-'}`")
    lines.extend(["", "## 结论", "", f"- 综合状态：`{'PASS' if payload['passed'] else 'FAIL'}`", ""])
    lines.append("| 目标词 | 状态 | 正向最低分 | 最弱正向错位 | 诊断最低分 | 最弱诊断错位 | 门槛 |")
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
        lines.append("| 变体 | 类型 | 状态 | 分数 | 阈值 | 最大错位帧 | shifts | capture_quality | semantic_floor | 说明 |")
        lines.append("|---|---|---|---:|---|---:|---|---|---|---|")
        for row in sorted(item["variants"], key=lambda value: (value["kind"], float(value["score"]))):
            quality = row.get("capture_quality") or {}
            floor = row.get("semantic_floor") or {}
            if row["kind"] == "positive":
                threshold = f">= {row.get('min_score')}"
                status = "PASS" if row["passed"] else "FAIL"
            else:
                threshold = "diagnostic"
                status = "DIAG"
            shifts = json.dumps(row.get("shifts") or {}, ensure_ascii=False, sort_keys=True)
            lines.append(
                f"| {row['variant']} | {row['kind']} | {status} | {_fmt(row['score'])} | "
                f"{threshold} | {row.get('max_abs_shift_frames')} | `{shifts}` | "
                f"{quality.get('status') or '-'}:{quality.get('reason') or '-'} | "
                f"{floor.get('source') or '-'}:{floor.get('reason') or '-'} | {row['rationale']} |"
            )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 该门补充的是手间相位差，不替代整体 temporal-rate、frame stutter、action crop/repeat 或 two-hand relation geometry 门。",
            "- `跳` 的轻度错位可以由语义 DTW 与 guarded local relation fallback 吸收，后续 scorer 改动不能破坏该能力。",
            "- 强错位不作为正常网页采集要求，只记录当前诊断边界。",
            "- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run inter-hand temporal desync robustness gate for flower/jump scoring.")
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--semantic-profile-json", default=str(DEFAULT_SEMANTIC_PROFILE_JSON))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_BASE / "flower_jump_interhand_temporal_desync_robustness_gate_current"))
    parser.add_argument("--words", nargs="+", default=DEFAULT_WORDS)
    parser.add_argument("--feature-mode", choices=["auto", "landmark", "bbox"], default="auto")
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
        )
        for word in args.words
    ]
    backend_status = _load_backend_status(args.backend_url, args.status_timeout_sec)
    passed = all(bool(item["gate_pass"]) for item in results)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "claim_policy": "synthetic inter-hand temporal-desync robustness sanity gate; not calibrated real-user scoring",
        "template_root": str(template_root),
        "semantic_profile_json": str(semantic_profile_json),
        "backend_status": backend_status,
        "passed": passed,
        "min_score": args.min_score,
        "results": results,
    }

    json_path = output_dir / "flower_jump_interhand_temporal_desync_robustness_gate.json"
    md_path = output_dir / "flower_jump_interhand_temporal_desync_robustness_gate.md"
    csv_path = output_dir / "flower_jump_interhand_temporal_desync_cases.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    md_path.write_text(_build_markdown(payload), encoding="utf-8")
    _write_rows_csv(csv_path, results)

    print(f"已生成花/跳手间时序错位鲁棒性 JSON：{json_path}")
    print(f"已生成花/跳手间时序错位鲁棒性报告：{md_path}")
    print(f"已生成花/跳手间时序错位鲁棒性 CSV：{csv_path}")
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

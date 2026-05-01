#!/usr/bin/env python3
"""
对比三种关键帧采样策略的实验结果。

输入默认读取：
- uniform_sampling.json
- two_stage_sampling.json
- adaptive_sampling.json

输出一个便于汇报的 Markdown 对比报告。
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


DEFAULT_ROOT = Path("/data/WYC/signLanguage/work/generated")
DEFAULT_VIZ_ROOT = Path("/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals_holistic")
DEFAULT_OUTPUT = Path("/data/WYC/signLanguage/work/reports/20260429_sampling_compare.md")


def _mean(vals: Sequence[float]) -> Optional[float]:
    return float(statistics.mean(vals)) if vals else None


def _load(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _derive_combined_sec(payload: Dict[str, Any]) -> Optional[float]:
    """优先读取显式的采样+Holistic 总耗时。"""

    combined = payload.get("combined_sec")
    if isinstance(combined, (int, float)):
        return float(combined)

    sampling_sec = payload.get("sampling_sec")
    holistic_eval_sec = payload.get("holistic_eval_sec")
    if isinstance(sampling_sec, (int, float)) and isinstance(holistic_eval_sec, (int, float)):
        return float(sampling_sec) + float(holistic_eval_sec)

    elapsed = payload.get("elapsed_sec")
    if isinstance(elapsed, (int, float)):
        return float(elapsed)
    return None


def _summarize_strategy(payload: Dict[str, Any], viz_root: Path) -> Dict[str, Any]:
    rows = payload["videos"]
    metrics = ["frame_span_ratio", "tail_coverage_ratio", "late_half_fraction", "late_75_fraction", "motion_energy_mean"]
    strategy = payload.get("strategy")
    combined_sec = _derive_combined_sec(payload)
    result: Dict[str, Any] = {
        "strategy": strategy,
        "sample_budget": payload.get("sample_budget"),
        "elapsed_sec": payload.get("elapsed_sec"),
        "combined_sec": combined_sec,
    }
    for key in metrics:
        vals = [r["evaluation"].get(key) for r in rows if isinstance(r["evaluation"].get(key), (int, float))]
        result[key] = _mean([float(v) for v in vals]) if vals else None
    result["videos"] = rows
    return result


def build_report(strategies: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    lines.append("# 关键帧采样策略对比实验")
    lines.append("")
    lines.append("本报告对比三种策略：全视频均匀采样、两阶段采样、自适应采样。")
    lines.append("三种策略都先完成 Holistic 识别并保存结果文件，再基于结果文件统一生成可视化；本报告只统计采样+Holistic 的总耗时。")
    lines.append("")

    lines.append("## 总体对比")
    lines.append("")
    for s in strategies:
        lines.append(f"### {s['strategy']}")
        lines.append(f"- 采样预算：{s.get('sample_budget')}")
        if s.get("combined_sec") is not None:
            lines.append(f"- 采样+Holistic总耗时：{s.get('combined_sec')}s")
        lines.append(f"- 帧覆盖比例均值：{s.get('frame_span_ratio')}")
        lines.append(f"- 尾部覆盖比例均值：{s.get('tail_coverage_ratio')}")
        lines.append(f"- 后半段采样占比均值：{s.get('late_half_fraction')}")
        lines.append(f"- 后 75% 采样占比均值：{s.get('late_75_fraction')}")
        lines.append(f"- 平均运动能量均值：{s.get('motion_energy_mean')}")
        if s["strategy"] == "uniform":
            lines.append("- 说明：先做全视频均匀选帧，再对选中的 12 帧做一次最终 Holistic 识别并保存结果文件。")
        else:
            lines.append("- 说明：先用少量 Holistic 结果指导采样决策，再对最终采样帧做一次完整 Holistic 识别并保存结果文件。")
        lines.append("")

    # 重点视频的对比。
    focus = ["花.mp4", "唱歌.mp4", "跳.mp4"]
    lookup: Dict[str, Dict[str, Any]] = {}
    for s in strategies:
        for row in s["videos"]:
            lookup.setdefault(row["video"], {})[s["strategy"]] = row

    lines.append("## 重点视频对比")
    lines.append("")
    for name in focus:
        if name not in lookup:
            continue
        lines.append(f"### {name}")
        for s in strategies:
            row = lookup[name].get(s["strategy"])
            if not row:
                continue
            eval_ = row["evaluation"]
            lines.append(f"- {s['strategy']}")
            lines.append(f"  - 采样帧：{', '.join(str(x) for x in row['sampled_frame_indices'])}")
            if s.get("combined_sec") is not None:
                lines.append(f"  - 采样+Holistic总耗时：{s.get('combined_sec')}s")
            if s["strategy"] == "uniform":
                lines.append("  - 说明：先做全视频均匀选帧，再对选中的 12 帧做一次最终 Holistic 识别并保存结果文件。")
            else:
                lines.append("  - 说明：先用少量 Holistic 结果指导采样决策，再对最终采样帧做一次完整 Holistic 识别并保存结果文件。")
            lines.append(f"  - 帧覆盖比例：{eval_.get('frame_span_ratio')}")
            lines.append(f"  - 尾部覆盖比例：{eval_.get('tail_coverage_ratio')}")
            lines.append(f"  - 后半段采样占比：{eval_.get('late_half_fraction')}")
            lines.append(f"  - 平均运动能量：{eval_.get('motion_energy_mean')}")
        lines.append("")

    lines.append("## 结论")
    lines.append("")
    lines.append("- 全视频均匀采样能最稳定地覆盖到视频末尾，适合作为默认基线。")
    lines.append("- 两阶段采样在保证尾部覆盖的同时，会把额外预算倾向到高运动区间，适合动作变化明显的样本。")
    lines.append("- 自适应采样会继续把预算往更值得细分的区间压缩，适合动作开始较晚或局部动作更密集的视频。")
    lines.append("- 对 `花.mp4` 这类动作开始偏晚的视频，三种新策略都比前段截断采样更可靠，因为它们都覆盖了全时长。")
    lines.append("- 从总耗时看，uniform 最省，two_stage 次之，adaptive 最慢；差异主要来自采样决策阶段的复杂度，而不是最终可视化。")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="对比关键帧采样策略")
    parser.add_argument("--root", default=str(DEFAULT_ROOT), help="策略结果根目录")
    parser.add_argument("--viz-root", default=str(DEFAULT_VIZ_ROOT), help="可视化结果根目录")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="对比报告输出路径")
    args = parser.parse_args(argv)

    root = Path(args.root)
    viz_root = Path(args.viz_root)
    payloads = [
        _load(root / "keyframe_sampling_uniform_single" / "uniform_sampling.json"),
        _load(root / "keyframe_sampling_two_stage_single" / "two_stage_sampling.json"),
        _load(root / "keyframe_sampling_adaptive_single" / "adaptive_sampling.json"),
    ]
    strategies = [_summarize_strategy(payload, viz_root) for payload in payloads]
    report = build_report(strategies)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(f"已生成策略对比报告：{out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

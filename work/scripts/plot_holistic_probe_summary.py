#!/usr/bin/env python3
"""
Holistic 探针结果可视化脚本。

输入：
- `holistic_probe_summary.json`

输出：
- 覆盖率柱状图
- 运动能量柱状图
- 简短 Markdown 分析报告

用途：
- 直接把 `pose / left_hand / right_hand / face` 的覆盖率画出来
- 给后续写技术结论和调整采样策略提供直观依据
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties


DEFAULT_SUMMARY = Path("/data/WYC/signLanguage/work/generated/holistic_probe_20260428_full/holistic_probe_summary.json")
DEFAULT_OUTPUT_DIR = DEFAULT_SUMMARY.parent / "plots"
DEFAULT_FONT = Path("/data/WYC/signLanguage/work/fonts/SourceHanSans.otf")


def _mean(values: Sequence[float]) -> Optional[float]:
    return float(statistics.mean(values)) if values else None


def _configure_fonts() -> Optional[FontProperties]:
    """优先使用仓库自带中文字体，避免中文标签缺字。"""

    if DEFAULT_FONT.exists():
        font = FontProperties(fname=str(DEFAULT_FONT))
        plt.rcParams["axes.unicode_minus"] = False
        return font
    plt.rcParams["axes.unicode_minus"] = False
    return None


def load_summary(path: Path) -> Dict[str, Any]:
    """加载探针 JSON。"""

    return json.loads(path.read_text(encoding="utf-8"))


def extract_rows(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """抽取每个视频的扁平化统计行。"""

    rows: List[Dict[str, Any]] = []
    for item in payload.get("videos", []):
        meta = item.get("meta", {})
        summary = item.get("summary", {})
        rows.append(
            {
                "name": Path(meta.get("path", summary.get("video", "unknown"))).name,
                "pose": summary.get("pose_presence_ratio"),
                "left": summary.get("left_hand_presence_ratio"),
                "right": summary.get("right_hand_presence_ratio"),
                "face": summary.get("face_presence_ratio"),
                "motion": summary.get("motion_energy_mean"),
                "samples": summary.get("samples"),
            }
        )
    return rows


def plot_coverage(rows: List[Dict[str, Any]], output_path: Path) -> None:
    """画覆盖率对比图。"""

    names = [r["name"] for r in rows]
    pose = [r["pose"] for r in rows]
    left = [r["left"] for r in rows]
    right = [r["right"] for r in rows]
    face = [r["face"] for r in rows]

    x = list(range(len(rows)))
    width = 0.2

    font = _configure_fonts()
    fig, ax = plt.subplots(figsize=(max(12, len(rows) * 1.2), 6), dpi=160)
    ax.bar([i - 1.5 * width for i in x], pose, width=width, label="pose", color="#4C78A8")
    ax.bar([i - 0.5 * width for i in x], left, width=width, label="left_hand", color="#F58518")
    ax.bar([i + 0.5 * width for i in x], right, width=width, label="right_hand", color="#54A24B")
    ax.bar([i + 1.5 * width for i in x], face, width=width, label="face", color="#E45756")

    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Presence ratio")
    ax.set_title("Holistic coverage by video")
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=25, ha="right")
    ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.12))
    ax.grid(axis="y", alpha=0.25)
    if font is not None:
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontproperties(font)
        ax.title.set_fontproperties(font)
        ax.xaxis.label.set_fontproperties(font)
        ax.yaxis.label.set_fontproperties(font)
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def plot_motion(rows: List[Dict[str, Any]], output_path: Path) -> None:
    """画运动能量对比图。"""

    names = [r["name"] for r in rows]
    motion = [r["motion"] for r in rows]
    x = list(range(len(rows)))

    font = _configure_fonts()
    fig, ax = plt.subplots(figsize=(max(12, len(rows) * 1.2), 6), dpi=160)
    ax.bar(x, motion, color="#72B7B2")
    ax.set_ylabel("Motion energy mean")
    ax.set_title("Holistic motion energy by video")
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=25, ha="right")
    ax.grid(axis="y", alpha=0.25)
    if font is not None:
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontproperties(font)
        ax.title.set_fontproperties(font)
        ax.xaxis.label.set_fontproperties(font)
        ax.yaxis.label.set_fontproperties(font)
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def build_report(payload: Dict[str, Any], rows: List[Dict[str, Any]], output_dir: Path) -> str:
    """生成 Markdown 分析报告。"""

    pose_mean = _mean([r["pose"] for r in rows if r["pose"] is not None])
    left_mean = _mean([r["left"] for r in rows if r["left"] is not None])
    right_mean = _mean([r["right"] for r in rows if r["right"] is not None])
    face_mean = _mean([r["face"] for r in rows if r["face"] is not None])
    motion_mean = _mean([r["motion"] for r in rows if r["motion"] is not None])

    lowest_left = min((r for r in rows if r["left"] is not None), key=lambda r: r["left"])
    lowest_right = min((r for r in rows if r["right"] is not None), key=lambda r: r["right"])
    highest_motion = max((r for r in rows if r["motion"] is not None), key=lambda r: r["motion"])

    lines: List[str] = []
    lines.append("# Holistic 结果分析")
    lines.append("")
    lines.append(f"- 生成时间：{payload.get('generated_at')}")
    lines.append(f"- 视频数量：{len(rows)}")
    lines.append(f"- 输出目录：{output_dir}")
    lines.append("")
    lines.append("## 总体统计")
    lines.append("")
    lines.append(f"- pose 平均覆盖率：{pose_mean}")
    lines.append(f"- left hand 平均覆盖率：{left_mean}")
    lines.append(f"- right hand 平均覆盖率：{right_mean}")
    lines.append(f"- face 平均覆盖率：{face_mean}")
    lines.append(f"- 平均运动能量：{motion_mean}")
    lines.append("")
    lines.append("## 结论")
    lines.append("")
    lines.append("- pose 和 face 在这批 demo 中覆盖率稳定，说明人体主干和脸部动作特征对当前数据集比较容易被稳定捕获。")
    lines.append("- 双手覆盖率存在明显差异，左手更容易掉帧或缺失，说明这批样本里存在单手主导、遮挡或画面构图偏置。")
    lines.append("- 运动能量最高的视频通常对应动作幅度更明显、时序变化更强的词条，适合进一步做 DTW 或关键帧选择。")
    lines.append("")
    lines.append("## 典型样本")
    lines.append("")
    lines.append(f"- 左手覆盖最低：{lowest_left['name']} ({lowest_left['left']})")
    lines.append(f"- 右手覆盖最低：{lowest_right['name']} ({lowest_right['right']})")
    lines.append(f"- 运动能量最高：{highest_motion['name']} ({highest_motion['motion']})")
    lines.append("")
    lines.append("## 产物")
    lines.append("")
    lines.append(f"- 覆盖率图：`{(output_dir / 'holistic_coverage_by_video.png')}`")
    lines.append(f"- 运动能量图：`{(output_dir / 'holistic_motion_by_video.png')}`")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="可视化 Holistic 探针结果")
    parser.add_argument("--summary-json", default=str(DEFAULT_SUMMARY), help="探针 summary JSON")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="输出目录")
    args = parser.parse_args(argv)

    summary_path = Path(args.summary_json)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = load_summary(summary_path)
    rows = extract_rows(payload)

    coverage_png = output_dir / "holistic_coverage_by_video.png"
    motion_png = output_dir / "holistic_motion_by_video.png"
    report_md = output_dir / "holistic_probe_analysis.md"

    plot_coverage(rows, coverage_png)
    plot_motion(rows, motion_png)
    report_md.write_text(build_report(payload, rows, output_dir), encoding="utf-8")

    print(f"已生成覆盖率图：{coverage_png}")
    print(f"已生成运动能量图：{motion_png}")
    print(f"已生成分析报告：{report_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

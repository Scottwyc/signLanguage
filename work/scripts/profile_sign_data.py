#!/usr/bin/env python3
"""
手语资料结构化盘点脚本。

对应 worklog_sign.md 里的第一个 TODO：
“对手语资料进行结构化描述，形成量化的特征指标（手部、肢体、面部，时序）”

这个脚本会：
1. 读取 `data/Demo词汇.docx` 里的文本说明
2. 扫描 demo 视频目录
3. 生成一个资料清单 JSON 和 Markdown 报告
4. 形成一份“特征指标模板”，为后续 Holistic 采样结果预留字段

说明：
- 当前脚本不依赖 mediapipe / opencv
- 真正的关键点特征会由 `holistic_sampling_probe.py` 补充
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from signlanguage_common import find_demo_videos, probe_video_metadata, read_docx_text, split_semantic_sections


DEFAULT_REPO_ROOT = Path("/data/WYC/signLanguage")
DEFAULT_DOCX = DEFAULT_REPO_ROOT / "data" / "Demo词汇.docx"
DEFAULT_VIDEO_ROOT = DEFAULT_REPO_ROOT / "data" / "Demo词汇视频"
DEFAULT_OUTPUT_DIR = DEFAULT_REPO_ROOT / "work" / "generated" / "sign_data_profile"


def build_feature_template() -> Dict[str, Any]:
    """给后续关键点采样预留一份量化指标模板。"""

    return {
        "hand": {
            "left_hand_presence_ratio": "左手在样本中被成功检测到的帧占比",
            "right_hand_presence_ratio": "右手在样本中被成功检测到的帧占比",
            "hand_visibility_mean": "双手可见度均值",
            "hand_motion_energy": "相邻帧手部位移能量",
            "left_right_symmetry_score": "左右手运动对称性",
        },
        "body": {
            "pose_presence_ratio": "人体骨架成功检测到的帧占比",
            "pose_visibility_mean": "躯干和四肢关键点可见度均值",
            "pose_motion_energy": "相邻帧身体位移能量",
            "upper_body_span_ratio": "上半身关键点覆盖范围归一化比例",
        },
        "face": {
            "face_presence_ratio": "人脸成功检测到的帧占比",
            "face_visibility_mean": "面部关键点可见度均值",
            "mouth_activity_score": "嘴部活动强度",
            "eyebrow_activity_score": "眉眼区域活动强度",
        },
        "temporal": {
            "sampled_frame_count": "采样帧数",
            "effective_span_sec": "有效动作跨度（秒）",
            "motion_peak_count": "运动峰值数量",
            "motion_smoothness": "动作平滑度",
            "coverage_stability": "关键点覆盖稳定性",
        },
    }


def pair_sections_and_videos(sections, videos: Sequence[Path]) -> List[Dict[str, Any]]:
    """
    把文档片段和视频文件配对。

    规则：
    - 如果数量一致，就按排序顺序一一配对
    - 若不一致，则只尽量按位置配对，并保留未匹配项
    """

    rows: List[Dict[str, Any]] = []
    max_len = max(len(sections), len(videos))
    for idx in range(max_len):
        section = sections[idx] if idx < len(sections) else None
        video = videos[idx] if idx < len(videos) else None
        rows.append(
            {
                "pair_index": idx,
                "doc_index": section.index if section else None,
                "doc_summary": section.summary if section else None,
                "doc_lines": section.lines if section else [],
                "video_path": str(video) if video else None,
                "video_name": video.name if video else None,
            }
        )
    return rows


def summarize_profile(video_rows: List[Dict[str, Any]], output_dir: Path) -> Dict[str, Any]:
    """生成汇总统计。"""

    durations = [row.get("duration_sec") for row in video_rows if isinstance(row.get("duration_sec"), (int, float))]
    sizes = [row.get("size_bytes") for row in video_rows if isinstance(row.get("size_bytes"), int)]
    widths = [row.get("width") for row in video_rows if isinstance(row.get("width"), int)]
    heights = [row.get("height") for row in video_rows if isinstance(row.get("height"), int)]

    def _safe_mean(values: Sequence[float]) -> Optional[float]:
        return float(statistics.mean(values)) if values else None

    def _safe_median(values: Sequence[float]) -> Optional[float]:
        return float(statistics.median(values)) if values else None

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "output_dir": str(output_dir),
        "video_count": len(video_rows),
        "duration_sec": {
            "mean": _safe_mean(durations),
            "median": _safe_median(durations),
            "min": float(min(durations)) if durations else None,
            "max": float(max(durations)) if durations else None,
        },
        "size_bytes": {
            "mean": _safe_mean(sizes),
            "median": _safe_median(sizes),
            "min": int(min(sizes)) if sizes else None,
            "max": int(max(sizes)) if sizes else None,
        },
        "resolution": {
            "width_modes": Counter(widths).most_common(5),
            "height_modes": Counter(heights).most_common(5),
        },
    }


def build_report(result: Dict[str, Any]) -> str:
    """生成便于人工阅读的 Markdown 报告。"""

    summary = result["summary"]
    rows = result["samples"]
    lines = []
    lines.append("# 手语资料结构化盘点报告")
    lines.append("")
    lines.append(f"- 生成时间：{summary['generated_at']}")
    lines.append(f"- 视频数量：{summary['video_count']}")
    lines.append(f"- 输出目录：{summary['output_dir']}")
    lines.append("")
    lines.append("## 量化指标模板")
    lines.append("")
    for group_name, metrics in result["feature_template"].items():
        lines.append(f"### {group_name}")
        for key, desc in metrics.items():
            lines.append(f"- `{key}`: {desc}")
        lines.append("")
    lines.append("## 资料样本清单")
    lines.append("")
    for row in rows:
        lines.append(f"### {row['pair_index'] + 1}. {row.get('video_name') or '(未匹配视频)'}")
        lines.append(f"- DOCX片段：{row.get('doc_summary') or '(无)'}")
        lines.append(f"- 视频路径：{row.get('video_path') or '(无)'}")
        lines.append(f"- 视频元数据：{json.dumps(row.get('video_meta', {}), ensure_ascii=False)}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="生成手语资料结构化盘点结果")
    parser.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT), help="仓库根目录")
    parser.add_argument("--docx", default=str(DEFAULT_DOCX), help="Demo 词汇 DOCX 路径")
    parser.add_argument("--video-root", default=str(DEFAULT_VIDEO_ROOT), help="Demo 视频目录")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="输出目录")
    parser.add_argument("--no-report", action="store_true", help="只输出 JSON，不生成 Markdown 报告")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root)
    docx_path = Path(args.docx)
    video_root = Path(args.video_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    texts = read_docx_text(docx_path)
    sections = split_semantic_sections(texts)
    videos = find_demo_videos(video_root)

    paired = pair_sections_and_videos(sections, videos)

    enriched_rows: List[Dict[str, Any]] = []
    for row in paired:
        video_path = row.get("video_path")
        video_meta = probe_video_metadata(video_path) if video_path else {}
        enriched = dict(row)
        enriched["video_meta"] = video_meta
        enriched_rows.append(enriched)

    result = {
        "repo_root": str(repo_root),
        "docx_path": str(docx_path),
        "video_root": str(video_root),
        "feature_template": build_feature_template(),
        "sections": [
            {
                "index": s.index,
                "marker": s.marker,
                "lines": s.lines,
                "summary": s.summary,
            }
            for s in sections
        ],
        "samples": enriched_rows,
        "summary": summarize_profile(enriched_rows, output_dir),
    }

    json_path = output_dir / "sign_data_profile.json"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    if not args.no_report:
        md_path = output_dir / "sign_data_profile.md"
        md_path.write_text(build_report(result), encoding="utf-8")

    print(f"已生成结构化盘点结果：{json_path}")
    if not args.no_report:
        print(f"已生成 Markdown 报告：{output_dir / 'sign_data_profile.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

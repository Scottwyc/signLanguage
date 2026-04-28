#!/usr/bin/env python3
"""
基于 Holistic 探针结果推荐关键帧和采样策略。

输入：
- `holistic_probe_summary.json`
- 每个视频目录下的 `*_frames.jsonl`

输出：
- `keyframe_recommendations.json`
- `keyframe_recommendations.md`

推荐逻辑：
1. 找出每个视频中 motion_energy / bbox_shift 最高的帧
2. 找出双手出现或消失的边界帧
3. 如果某一侧手覆盖过低，提示后续加密采样或检查构图
4. 输出一份能直接用于后续二次采样的帧号清单
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


DEFAULT_SUMMARY = Path("/data/WYC/signLanguage/work/generated/holistic_probe_20260428_full/holistic_probe_summary.json")
DEFAULT_OUTPUT_DIR = DEFAULT_SUMMARY.parent / "keyframe_recommendation"


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_frames(video_dir: Path, stem: str) -> List[Dict[str, Any]]:
    """加载单个视频的帧级 JSONL。"""

    jsonl = video_dir / f"{stem}_frames.jsonl"
    frames: List[Dict[str, Any]] = []
    if not jsonl.exists():
        return frames
    with jsonl.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            frames.append(json.loads(line))
    return frames


def _top_frames(frames: List[Dict[str, Any]], field: str, k: int = 3) -> List[Dict[str, Any]]:
    """按字段大小返回 top-k 帧。"""

    valid = [fr for fr in frames if isinstance(fr.get(field), (int, float))]
    return sorted(valid, key=lambda fr: fr.get(field, 0.0), reverse=True)[:k]


def _boundary_frames(frames: List[Dict[str, Any]], key: str) -> List[Dict[str, Any]]:
    """找出某个布尔字段发生变化的位置。"""

    result: List[Dict[str, Any]] = []
    prev = None
    for fr in frames:
        cur = fr.get(key)
        if prev is None:
            prev = cur
            continue
        if cur != prev:
            result.append(fr)
            prev = cur
    return result[:3]


def _frame_label(fr: Dict[str, Any]) -> str:
    return f"{fr.get('frame_idx')}@{round(float(fr.get('timestamp_sec', 0.0)), 3)}s"


def analyze_video(item: Dict[str, Any], base_dir: Path) -> Dict[str, Any]:
    """生成单视频的关键帧推荐。"""

    meta = item.get("meta", {})
    summary = item.get("summary", {})
    path = Path(meta.get("path", summary.get("video", "")))
    stem = path.stem
    video_dir = base_dir / stem
    frames = load_frames(video_dir, stem)

    pose_ratio = summary.get("pose_presence_ratio")
    left_ratio = summary.get("left_hand_presence_ratio")
    right_ratio = summary.get("right_hand_presence_ratio")
    face_ratio = summary.get("face_presence_ratio")
    motion_mean = summary.get("motion_energy_mean")

    top_motion = _top_frames(frames, "motion_energy", 3)
    top_shift = _top_frames(frames, "bbox_shift", 3)
    left_switch = _boundary_frames(frames, "left_hand_present")
    right_switch = _boundary_frames(frames, "right_hand_present")

    candidate_frames: List[int] = []
    for fr in top_motion + top_shift + left_switch + right_switch:
        idx = fr.get("frame_idx")
        if isinstance(idx, int) and idx not in candidate_frames:
            candidate_frames.append(idx)

    candidate_frames = sorted(candidate_frames)

    suggestions: List[str] = []
    if isinstance(left_ratio, (int, float)) and left_ratio < 0.7:
        suggestions.append("左手覆盖偏低，建议提高采样密度，优先检查左侧遮挡、镜像和构图偏置。")
    if isinstance(right_ratio, (int, float)) and right_ratio < 0.7:
        suggestions.append("右手覆盖偏低，建议提高采样密度，优先检查右侧遮挡与动作是否在画面边缘。")
    if isinstance(pose_ratio, (int, float)) and pose_ratio < 0.95:
        suggestions.append("pose 覆盖不稳定，建议扩大人物在画面中的占比或降低拍摄抖动。")
    if isinstance(face_ratio, (int, float)) and face_ratio < 0.95:
        suggestions.append("脸部覆盖不稳定，建议确保上半身和头部始终处于完整画面内。")
    if isinstance(motion_mean, (int, float)) and motion_mean > 40:
        suggestions.append("动作幅度较大，建议在动作转折点附近加密采样，避免只抓到平稳段。")
    if not suggestions:
        suggestions.append("当前覆盖较稳定，可维持当前采样密度，更多关注动作转折帧。")

    return {
        "video": path.name,
        "video_path": str(path),
        "summary": {
            "pose_presence_ratio": pose_ratio,
            "left_hand_presence_ratio": left_ratio,
            "right_hand_presence_ratio": right_ratio,
            "face_presence_ratio": face_ratio,
            "motion_energy_mean": motion_mean,
            "samples": summary.get("samples"),
        },
        "top_motion_frames": [_frame_label(fr) for fr in top_motion],
        "top_shift_frames": [_frame_label(fr) for fr in top_shift],
        "boundary_frames": {
            "left_hand": [_frame_label(fr) for fr in left_switch],
            "right_hand": [_frame_label(fr) for fr in right_switch],
        },
        "recommended_frame_indices": candidate_frames,
        "suggestions": suggestions,
    }


def build_report(payload: Dict[str, Any]) -> str:
    """生成 Markdown 报告。"""

    rows = payload["videos"]
    left_ratios = [r["summary"]["left_hand_presence_ratio"] for r in rows if isinstance(r["summary"].get("left_hand_presence_ratio"), (int, float))]
    right_ratios = [r["summary"]["right_hand_presence_ratio"] for r in rows if isinstance(r["summary"].get("right_hand_presence_ratio"), (int, float))]
    pose_ratios = [r["summary"]["pose_presence_ratio"] for r in rows if isinstance(r["summary"].get("pose_presence_ratio"), (int, float))]
    face_ratios = [r["summary"]["face_presence_ratio"] for r in rows if isinstance(r["summary"].get("face_presence_ratio"), (int, float))]

    def _mean(vals: Sequence[float]) -> Optional[float]:
        return float(statistics.mean(vals)) if vals else None

    lines: List[str] = []
    lines.append("# 关键帧与采样建议")
    lines.append("")
    lines.append(f"- 生成时间：{payload.get('generated_at')}")
    lines.append(f"- 视频数量：{len(rows)}")
    lines.append("")
    lines.append("## 总体统计")
    lines.append("")
    lines.append(f"- pose 平均覆盖率：{_mean(pose_ratios)}")
    lines.append(f"- left hand 平均覆盖率：{_mean(left_ratios)}")
    lines.append(f"- right hand 平均覆盖率：{_mean(right_ratios)}")
    lines.append(f"- face 平均覆盖率：{_mean(face_ratios)}")
    lines.append("")
    lines.append("## 视频级建议")
    lines.append("")
    for row in rows:
        lines.append(f"### {row['video']}")
        s = row["summary"]
        lines.append(f"- 覆盖率：pose={s['pose_presence_ratio']}, left={s['left_hand_presence_ratio']}, right={s['right_hand_presence_ratio']}, face={s['face_presence_ratio']}")
        lines.append(f"- 平均运动能量：{s['motion_energy_mean']}")
        lines.append(f"- 推荐关键帧：{', '.join(str(x) for x in row['recommended_frame_indices']) if row['recommended_frame_indices'] else '(无)'}")
        lines.append(f"- 最高运动帧：{', '.join(row['top_motion_frames']) if row['top_motion_frames'] else '(无)'}")
        lines.append(f"- 左手边界帧：{', '.join(row['boundary_frames']['left_hand']) if row['boundary_frames']['left_hand'] else '(无)'}")
        lines.append(f"- 右手边界帧：{', '.join(row['boundary_frames']['right_hand']) if row['boundary_frames']['right_hand'] else '(无)'}")
        for tip in row["suggestions"]:
            lines.append(f"- 建议：{tip}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="推荐关键帧和采样策略")
    parser.add_argument("--summary-json", default=str(DEFAULT_SUMMARY), help="Holistic summary JSON")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="输出目录")
    args = parser.parse_args(argv)

    summary_path = Path(args.summary_json)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = load_json(summary_path)
    base_dir = summary_path.parent
    rows = [analyze_video(item, base_dir) for item in payload.get("videos", [])]

    result = {
        "generated_at": payload.get("generated_at"),
        "source_summary_json": str(summary_path),
        "videos": rows,
    }

    json_path = output_dir / "keyframe_recommendations.json"
    md_path = output_dir / "keyframe_recommendations.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(build_report(result), encoding="utf-8")

    print(f"已生成关键帧建议 JSON：{json_path}")
    print(f"已生成关键帧建议报告：{md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

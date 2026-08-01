#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""复验全部姿态微调产物并生成匿名化人工审核索引。"""
from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path

VIEW_ORDER = {"正": 0, "左30": 1, "右30": 2}


def read_csv(path: Path) -> list[dict]:
    return list(csv.DictReader(path.open(encoding="utf-8-sig")))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()

    rows = []
    errors = []
    for volunteer_id in range(1, 12):
        for view in ("正", "左30", "右30"):
            folder = args.root / f"{volunteer_id:02d}" / view
            segments_path = folder / "segments_pose_rest_optimized.csv"
            diagnostics_path = folder / "boundary_pose_rest_diagnostics.csv"
            manifest_path = folder / "pose_rest_optimization_manifest.json"
            preview_path = folder / "preview_pose_rest_optimized_boundaries.jpg"
            required = (segments_path, diagnostics_path, manifest_path, preview_path)
            missing = [str(path) for path in required if not path.exists() or path.stat().st_size == 0]
            if missing:
                errors.append({"volunteer_id": volunteer_id, "view": view, "missing": missing})
                continue

            segments = read_csv(segments_path)
            diagnostics = read_csv(diagnostics_path)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            truncated = volunteer_id == 11 and view == "左30"
            expected_segments = 40 if truncated else 42
            expected_boundaries = expected_segments + 1
            local_errors = []
            if len(segments) != expected_segments:
                local_errors.append(f"segments={len(segments)} expected={expected_segments}")
            if len(diagnostics) != expected_boundaries:
                local_errors.append(f"boundaries={len(diagnostics)} expected={expected_boundaries}")
            for index, segment in enumerate(segments):
                start, end = float(segment["start_sec"]), float(segment["end_sec"])
                if end <= start:
                    local_errors.append(f"segment_{index + 1}_nonpositive")
                if index + 1 < len(segments):
                    next_start = float(segments[index + 1]["start_sec"])
                    if abs(end - next_start) > 1e-4:
                        local_errors.append(f"segment_{index + 1}_discontinuous")
            if local_errors:
                errors.append({
                    "volunteer_id": volunteer_id,
                    "view": view,
                    "errors": local_errors,
                })

            pose_valid = int(manifest["pose_valid_boundary_count"])
            boundary_count = int(manifest["boundary_count"])
            valid_rate = pose_valid / boundary_count if boundary_count else 0.0
            mean_abs_shift = float(manifest["shift_summary_sec"]["mean_abs"])
            max_abs_shift = float(manifest["shift_summary_sec"]["max_abs"])
            flags = []
            if truncated:
                flags.append("源视频尾部截断_缺失指示两次")
            if valid_rate < 0.8:
                flags.append("姿态有效率低_优先复核")
            if mean_abs_shift > 0.25:
                flags.append("平均微调位移较大_优先复核")
            if max_abs_shift > 0.65:
                flags.append("存在接近搜索窗边缘的边界")
            rows.append({
                "志愿者编号": volunteer_id,
                "视角": view,
                "状态": "源视频尾部截断" if truncated else "完整候选",
                "片段数": len(segments),
                "边界数": len(diagnostics),
                "姿态有效边界数": pose_valid,
                "姿态有效率": f"{valid_rate:.4f}",
                "平均绝对微调秒": f"{mean_abs_shift:.4f}",
                "最大绝对微调秒": f"{max_abs_shift:.4f}",
                "重点复核标记": ";".join(flags) if flags else "常规审核",
                "时间点CSV": str(segments_path.resolve()),
                "边界诊断CSV": str(diagnostics_path.resolve()),
                "Preview": str(preview_path.resolve()),
                "Manifest": str(manifest_path.resolve()),
            })

    rows.sort(key=lambda row: (int(row["志愿者编号"]), VIEW_ORDER[row["视角"]]))
    csv_path = args.root / "全体视频_姿态微调人工审核索引.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    priority = [row for row in rows if row["重点复核标记"] != "常规审核"]
    timestamp = time.strftime("%Y-%m-%d %H:%M %z")
    lines = [
        "# 全体视频姿态微调切割人工审核索引",
        "",
        f"- 生成时间：{timestamp}",
        f"- 审核根目录：`{args.root.resolve()}`",
        f"- 视频总数：{len(rows)}",
        f"- 完整 42 段视频：{sum(int(row['片段数']) == 42 for row in rows)}",
        f"- 源视频尾部截断视频：{sum(row['状态'] != '完整候选' for row in rows)}",
        f"- 自动结构校验错误：{len(errors)}",
        "",
        "## 审核方法",
        "",
        "每个编号/视角目录中优先查看 `preview_pose_rest_optimized_boundaries.jpg`。如发现边界异常，再对照 `segments_pose_rest_optimized.csv` 和 `boundary_pose_rest_diagnostics.csv`。",
        "",
        "## 优先复核项",
        "",
    ]
    for row in priority:
        lines.extend([
            f"- 编号 {int(row['志愿者编号']):02d} / {row['视角']}：{row['重点复核标记']}",
            f"  - Preview：`{row['Preview']}`",
            f"  - 时间点：`{row['时间点CSV']}`",
        ])
    lines.extend(["", "## 全部视频", ""])
    for row in rows:
        lines.extend([
            f"- 编号 {int(row['志愿者编号']):02d} / {row['视角']}：{row['片段数']} 段，{row['重点复核标记']}",
            f"  - Preview：`{row['Preview']}`",
            f"  - 时间点：`{row['时间点CSV']}`",
        ])
    if errors:
        lines.extend(["", "## 自动校验错误", "", "```json", json.dumps(errors, ensure_ascii=False, indent=2), "```"])
    report_path = args.root / "全体视频_姿态微调人工审核说明.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    summary = {
        "generated_at": timestamp,
        "video_count": len(rows),
        "complete_42_segment_video_count": sum(int(row["片段数"]) == 42 for row in rows),
        "truncated_video_count": sum(row["状态"] != "完整候选" for row in rows),
        "priority_review_count": len(priority),
        "validation_error_count": len(errors),
        "review_index_csv": str(csv_path.resolve()),
        "review_guide_md": str(report_path.resolve()),
        "errors": errors,
    }
    (args.root / "全体视频_姿态微调最终汇总.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build word-level semantic scoring profiles from the demo text document.

The generated JSON is intentionally explicit and reviewable. It turns the
natural-language action description into scoring weights for broad feature
groups (hands, pose, face) plus hand-shape and key-node emphasis.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from signlanguage_common import read_docx_text, split_semantic_sections


REPO_ROOT = Path("/data/WYC/signLanguage")
DEFAULT_DOCX = REPO_ROOT / "data/Demo词汇.docx"
DEFAULT_TEMPLATE_ROOT = REPO_ROOT / "work/generated/scoring_mvp_run2/all_demo_step4_worker_cache_v2/results"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "work/generated/scoring_semantic_profiles"


WORD_RULES = [
    ("香蕉", ["香蕉", "剥皮"]),
    ("花", ["花朵", "含苞", "开花", "张开"]),
    ("汽车", ["开车", "方向盘"]),
    ("虎", ["老虎", "王", "兽爪"]),
    ("月亮", ["弯月", "月"]),
    ("跳", ["弹跳", "两条腿", "弯曲后伸直"]),
    ("朋友", ["两个人", "亲密", "朋友"]),
    ("指示", ["指挥", "食指表示另一个人"]),
    ("唱歌", ["唱歌", "喉部", "音符"]),
    ("谗（羡慕）", ["口水", "舌头", "嘴角", "馋"]),
]


PROFILE_PRESETS: Dict[str, Dict[str, Any]] = {
    "generic": {
        "group_weights": {
            "left_hand": 0.26,
            "right_hand": 0.26,
            "left_hand_shape": 0.16,
            "right_hand_shape": 0.16,
            "pose": 0.09,
            "face": 0.02,
            "missing": 0.05,
        },
        "focus_groups": ["left_hand", "right_hand", "left_hand_shape", "right_hand_shape"],
        "allow_hand_swap": True,
        "keypoint_weights": {
            "hand": {"4": 1.25, "8": 1.35, "12": 1.35, "16": 1.20, "20": 1.20, "opening": 1.35, "spread": 1.30},
            "pose": {"15": 1.15, "16": 1.15},
            "face": {},
        },
    },
    "花": {
        "group_weights": {
            "left_hand": 0.12,
            "right_hand": 0.32,
            "left_hand_shape": 0.18,
            "right_hand_shape": 0.35,
            "pose": 0.00,
            "face": 0.00,
            "missing": 0.03,
        },
        "focus_groups": ["right_hand_shape", "left_hand_shape", "right_hand", "left_hand"],
        "allow_hand_swap": True,
        "keypoint_weights": {
            "hand": {"4": 1.25, "8": 1.80, "12": 1.80, "16": 1.55, "20": 1.55, "opening": 2.20, "spread": 2.00},
            "pose": {"15": 1.05, "16": 1.05},
            "face": {},
        },
        "semantic_notes": ["重点是一手从撮合/含苞到张开，脸部基本不参与评分。", "手指张开由 fingertip spread、tip-to-wrist、finger straightness 等相对特征刻画。"],
    },
    "跳": {
        "group_weights": {
            "left_hand": 0.14,
            "right_hand": 0.34,
            "left_hand_shape": 0.10,
            "right_hand_shape": 0.28,
            "pose": 0.09,
            "face": 0.00,
            "missing": 0.05,
        },
        "focus_groups": ["right_hand_shape", "right_hand", "left_hand"],
        "allow_hand_swap": True,
        "keypoint_weights": {
            "hand": {"8": 1.90, "12": 1.90, "5": 1.35, "9": 1.35, "index": 1.80, "middle": 1.80},
            "pose": {"15": 1.10, "16": 1.10},
            "face": {},
        },
    },
    "唱歌": {
        "group_weights": {
            "left_hand": 0.22,
            "right_hand": 0.22,
            "left_hand_shape": 0.12,
            "right_hand_shape": 0.12,
            "pose": 0.10,
            "face": 0.17,
            "missing": 0.05,
        },
        "focus_groups": ["left_hand", "right_hand", "face", "pose"],
        "allow_hand_swap": True,
        "keypoint_weights": {
            "hand": {"4": 1.45, "8": 1.45},
            "pose": {"0": 1.40, "11": 1.15, "12": 1.15},
            "face": {"13": 1.80, "14": 1.80, "61": 1.35, "291": 1.35},
        },
    },
    "谗（羡慕）": {
        "group_weights": {
            "left_hand": 0.16,
            "right_hand": 0.24,
            "left_hand_shape": 0.08,
            "right_hand_shape": 0.12,
            "pose": 0.05,
            "face": 0.30,
            "missing": 0.05,
        },
        "focus_groups": ["face", "right_hand", "left_hand"],
        "allow_hand_swap": True,
        "keypoint_weights": {
            "hand": {"8": 1.75, "4": 1.30},
            "pose": {},
            "face": {"13": 1.75, "14": 1.75, "61": 1.60, "291": 1.60},
        },
    },
    "汽车": {
        "group_weights": {
            "left_hand": 0.28,
            "right_hand": 0.28,
            "left_hand_shape": 0.16,
            "right_hand_shape": 0.16,
            "pose": 0.07,
            "face": 0.00,
            "missing": 0.05,
        },
        "focus_groups": ["left_hand", "right_hand", "left_hand_shape", "right_hand_shape"],
        "allow_hand_swap": True,
        "keypoint_weights": {"hand": {"4": 1.35, "8": 1.35, "12": 1.25, "opening": 1.25}, "pose": {}, "face": {}},
    },
    "月亮": {
        "group_weights": {
            "left_hand": 0.25,
            "right_hand": 0.25,
            "left_hand_shape": 0.20,
            "right_hand_shape": 0.20,
            "pose": 0.05,
            "face": 0.00,
            "missing": 0.05,
        },
        "focus_groups": ["left_hand_shape", "right_hand_shape", "left_hand", "right_hand"],
        "allow_hand_swap": True,
        "keypoint_weights": {"hand": {"8": 1.70, "12": 1.55, "spread": 1.80, "opening": 1.60}, "pose": {}, "face": {}},
    },
    "朋友": {
        "group_weights": {
            "left_hand": 0.30,
            "right_hand": 0.30,
            "left_hand_shape": 0.16,
            "right_hand_shape": 0.16,
            "pose": 0.03,
            "face": 0.00,
            "missing": 0.05,
        },
        "focus_groups": ["left_hand", "right_hand", "left_hand_shape", "right_hand_shape"],
        "allow_hand_swap": True,
        "keypoint_weights": {"hand": {"4": 2.00, "thumb": 2.00}, "pose": {}, "face": {}},
    },
    "指示": {
        "group_weights": {
            "left_hand": 0.22,
            "right_hand": 0.32,
            "left_hand_shape": 0.12,
            "right_hand_shape": 0.18,
            "pose": 0.11,
            "face": 0.00,
            "missing": 0.05,
        },
        "focus_groups": ["right_hand", "right_hand_shape", "left_hand"],
        "allow_hand_swap": True,
        "keypoint_weights": {"hand": {"4": 1.50, "8": 1.90, "index": 1.80, "thumb": 1.50}, "pose": {}, "face": {}},
    },
    "虎": {
        "group_weights": {
            "left_hand": 0.24,
            "right_hand": 0.24,
            "left_hand_shape": 0.18,
            "right_hand_shape": 0.18,
            "pose": 0.06,
            "face": 0.05,
            "missing": 0.05,
        },
        "focus_groups": ["left_hand_shape", "right_hand_shape", "left_hand", "right_hand"],
        "allow_hand_swap": True,
        "keypoint_weights": {"hand": {"8": 1.50, "12": 1.35, "16": 1.50, "20": 1.50, "opening": 1.60}, "pose": {"0": 1.20}, "face": {}},
    },
    "香蕉": {
        "group_weights": {
            "left_hand": 0.24,
            "right_hand": 0.30,
            "left_hand_shape": 0.14,
            "right_hand_shape": 0.16,
            "pose": 0.11,
            "face": 0.00,
            "missing": 0.05,
        },
        "focus_groups": ["right_hand", "left_hand", "right_hand_shape", "left_hand_shape"],
        "allow_hand_swap": True,
        "keypoint_weights": {"hand": {"8": 1.90, "index": 1.80, "4": 1.30}, "pose": {}, "face": {}},
    },
}


def infer_word(lines: Sequence[str]) -> Optional[str]:
    text = "；".join(lines)
    scores: Dict[str, int] = {}
    for word, keywords in WORD_RULES:
        scores[word] = sum(1 for keyword in keywords if keyword in text)
    best_word, best_score = max(scores.items(), key=lambda item: item[1])
    return best_word if best_score > 0 else None


def normalize_weights(raw: Dict[str, float]) -> Dict[str, float]:
    missing = max(0.0, min(float(raw.get("missing", 0.05)), 0.35))
    groups = [key for key in raw if key != "missing" and float(raw.get(key, 0.0)) > 0]
    total = sum(float(raw[key]) for key in groups)
    if total <= 1e-8:
        return dict(PROFILE_PRESETS["generic"]["group_weights"])
    scale = (1.0 - missing) / total
    result = {key: float(raw.get(key, 0.0)) * scale for key in raw if key != "missing"}
    result["missing"] = missing
    return result


def build_profiles(docx_path: Path, template_root: Path) -> Dict[str, Any]:
    sections = split_semantic_sections(read_docx_text(docx_path))
    section_by_word: Dict[str, List[str]] = {}
    unmatched: List[List[str]] = []
    for section in sections:
        word = infer_word(section.lines)
        if word:
            section_by_word[word] = section.lines
        else:
            unmatched.append(section.lines)

    template_words = sorted([item.name for item in template_root.iterdir() if item.is_dir()]) if template_root.exists() else sorted(section_by_word)
    profiles: Dict[str, Any] = {}
    for word in template_words:
        preset = PROFILE_PRESETS.get(word, PROFILE_PRESETS["generic"])
        lines = section_by_word.get(word, [])
        profile = {
            "word": word,
            "description": "；".join(lines) if lines else f"{word}：未从 DOCX 匹配到说明，使用 generic 权重。",
            "source_lines": lines,
            "group_weights": normalize_weights(dict(preset["group_weights"])),
            "keypoint_weights": preset.get("keypoint_weights", {}),
            "focus_groups": preset.get("focus_groups", PROFILE_PRESETS["generic"]["focus_groups"]),
            "allow_hand_swap": bool(preset.get("allow_hand_swap", True)),
            "semantic_notes": list(preset.get("semantic_notes", [])),
        }
        if not profile["semantic_notes"]:
            profile["semantic_notes"] = [
                "由 DOCX 动作说明中的手/脸/身体语义自动选择组权重。",
                "手部关键语义优先用相对手形特征和重点指尖/拇指节点刻画。",
            ]
        profiles[word] = profile

    profiles["generic"] = {
        "word": "generic",
        "description": "未命中特定词条时使用的通用手部优先 profile。",
        "source_lines": [],
        "group_weights": normalize_weights(dict(PROFILE_PRESETS["generic"]["group_weights"])),
        "keypoint_weights": PROFILE_PRESETS["generic"].get("keypoint_weights", {}),
        "focus_groups": PROFILE_PRESETS["generic"].get("focus_groups", []),
        "allow_hand_swap": True,
        "semantic_notes": ["fallback profile"],
    }

    return {
        "version": "semantic_weights_v1_20260523",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "docx_path": str(docx_path),
        "template_root": str(template_root),
        "claim_policy": "Text-derived engineering profile; not human-label calibrated.",
        "profiles": profiles,
        "docx_section_mapping": {word: lines for word, lines in section_by_word.items()},
        "unmatched_sections": unmatched,
    }


def build_report(payload: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# 手语文本语义权重 profile")
    lines.append("")
    lines.append(f"- 生成时间：`{payload['generated_at']}`")
    lines.append(f"- DOCX：`{payload['docx_path']}`")
    lines.append(f"- 模板库：`{payload['template_root']}`")
    lines.append("- 口径：文本语义工程权重，不是人工标注校准权重。")
    lines.append("")
    for word, profile in payload["profiles"].items():
        if word == "generic":
            continue
        lines.append(f"## {word}")
        lines.append("")
        lines.append(f"- 说明：{profile['description']}")
        lines.append(f"- 允许左右手互换匹配：`{profile['allow_hand_swap']}`")
        lines.append(f"- 重点组：`{', '.join(profile['focus_groups'])}`")
        lines.append("- 组权重：")
        for key, value in profile["group_weights"].items():
            lines.append(f"  - `{key}`: `{value:.4f}`")
        lines.append("- 语义说明：")
        for note in profile["semantic_notes"]:
            lines.append(f"  - {note}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="从 Demo 词汇 DOCX 生成语义加权评分 profile")
    parser.add_argument("--docx", default=str(DEFAULT_DOCX))
    parser.add_argument("--template-root", default=str(DEFAULT_TEMPLATE_ROOT))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = build_profiles(Path(args.docx), Path(args.template_root))

    json_path = output_dir / "sign_semantic_weights.json"
    md_path = output_dir / "sign_semantic_weights.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(build_report(payload), encoding="utf-8")
    print(f"已生成语义权重 JSON：{json_path}")
    print(f"已生成语义权重报告：{md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

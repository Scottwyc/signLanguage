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

DEFAULT_SEMANTIC_DTW = {
    "enabled": True,
    "local_phase_weight": 0.018,
    "anchor_penalty_weight": 0.10,
    "anchor_phases": [0.10, 0.50, 0.90],
    "pose_robust_hand_position": True,
    "hand_global_position_weight": 0.18,
    "relative_motion_enabled": False,
    "relative_motion_weight": 0.14,
    "two_hand_relation_weight": 0.14,
    "group_missing_distance_weight": 0.00,
    "focus_missing_distance_weight": 0.00,
    "relation_missing_distance_weight": 0.00,
    "required_presence_groups": [],
    "required_presence_weight": 0.08,
    "visible_core_tolerance_cap": 0.034,
    "core_visible_score_scale": 0.120,
    "core_visible_dtw_threshold": 0.045,
    "core_visible_presence_threshold": 0.65,
    "core_visible_max_normalized_distance": 0.080,
    "short_core_capture_tolerance_cap": 0.000,
    "short_core_capture_max_length_ratio": 0.70,
    "flower_opening_guard_enabled": False,
    "flower_opening_min_score": 0.30,
    "flower_visible_core_floor_enabled": False,
    "flower_visible_core_floor_min_score": 72.0,
    "flower_visible_core_floor_max_score": 80.0,
    "flower_visible_core_floor_max_length_ratio": 0.32,
    "flower_visible_core_floor_min_presence": 0.62,
    "flower_visible_core_floor_min_opening_score": 0.60,
    "flower_visible_core_floor_max_dtw": 0.042,
    "flower_visible_core_floor_min_action_coverage": 0.62,
    "flower_jump_confusion_guard_enabled": False,
    "flower_jump_confusion_min_two_hand_presence": 0.58,
    "flower_jump_confusion_min_relation_valid_count": 3,
    "flower_jump_confusion_max_opening_score": 0.45,
    "flower_jump_confusion_min_two_finger_shape_mean": 1.05,
    "jump_relation_semantic_floor_enabled": False,
    "jump_relation_semantic_max_score": 0.0,
    "jump_relation_semantic_min_presence": 0.65,
    "jump_relation_semantic_min_direction": 0.55,
    "jump_relation_local_fallback_enabled": False,
    "jump_relation_local_min_direction": 0.92,
    "jump_relation_local_min_amplitude_ratio": 0.80,
    "jump_relation_local_max_horizontal_to_vertical": 0.60,
    "jump_relation_local_min_coverage": 0.48,
    "jump_relation_local_max_coverage": 0.78,
    "jump_relation_local_min_two_finger_shape_mean": 0.95,
    "phase_order_guard_enabled": False,
    "phase_order_guard_anchor_phases": [0.10, 0.25, 0.50, 0.75, 0.90],
    "phase_order_guard_min_disorder_span_score": 0.0,
    "phase_order_guard_min_adjacent_disorder_span_score": 0.0,
    "phase_order_guard_max_score": 45.0,
    "description": "Use semantic energy progress, not frame index, to softly align start/mid/end action phases.",
}


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
        "semantic_dtw": DEFAULT_SEMANTIC_DTW,
    },
    "花": {
        "group_weights": {
            "left_hand": 0.08,
            "right_hand": 0.34,
            "left_hand_shape": 0.10,
            "right_hand_shape": 0.44,
            "pose": 0.00,
            "face": 0.00,
            "missing": 0.04,
        },
        "focus_groups": ["right_hand_shape", "right_hand"],
        "allow_hand_swap": True,
        "keypoint_weights": {
            "hand": {"4": 1.20, "8": 2.20, "12": 2.20, "16": 1.90, "20": 1.90, "opening": 2.90, "spread": 2.70},
            "pose": {},
            "face": {},
        },
        "semantic_dtw": {
            **DEFAULT_SEMANTIC_DTW,
            "local_phase_weight": 0.020,
            "anchor_penalty_weight": 0.11,
            "hand_global_position_weight": 0.06,
            "relative_motion_weight": 0.12,
            "two_hand_relation_weight": 0.05,
            "visible_core_tolerance_cap": 0.045,
            "core_visible_score_scale": 0.145,
            "core_visible_dtw_threshold": 0.060,
            "core_visible_presence_threshold": 0.58,
            "core_visible_max_normalized_distance": 0.105,
            "short_core_capture_tolerance_cap": 0.145,
            "short_core_capture_max_length_ratio": 0.70,
            "flower_opening_guard_enabled": True,
            "flower_opening_min_score": 0.30,
            "flower_visible_core_floor_enabled": True,
            "flower_visible_core_floor_min_score": 72.0,
            "flower_visible_core_floor_max_score": 80.0,
            "flower_visible_core_floor_max_length_ratio": 0.32,
            "flower_visible_core_floor_min_presence": 0.62,
            "flower_visible_core_floor_min_opening_score": 0.60,
            "flower_visible_core_floor_max_dtw": 0.042,
            "flower_visible_core_floor_min_action_coverage": 0.62,
            "flower_jump_confusion_guard_enabled": True,
            "flower_jump_confusion_min_two_hand_presence": 0.58,
            "flower_jump_confusion_min_relation_valid_count": 3,
            "flower_jump_confusion_max_opening_score": 0.45,
            "flower_jump_confusion_min_two_finger_shape_mean": 1.05,
            "phase_order_guard_enabled": True,
            "phase_order_guard_min_disorder_span_score": 0.40,
            "phase_order_guard_min_adjacent_disorder_span_score": 0.00,
            "phase_order_guard_max_score": 45.0,
            "description": "Main-hand opening/spread semantic phases should align even when frame count differs.",
        },
        "semantic_notes": [
            "DOCX 语义是一手撮合/含苞并缓慢张开；评分只看主手手形和主手运动。",
            "脸、身体、主手相对躯干位置不参与主距离；另一只手只作为手势完整性约束，用于惩罚额外双手动作。",
            "允许左右手互换：用户用左手或右手完成时，都映射到模板主手。",
            "动态重要帧由主手 opening/spread、指尖相对腕部距离和手指伸直度驱动。",
        ],
    },
    "跳": {
        "group_weights": {
            "left_hand": 0.20,
            "right_hand": 0.28,
            "left_hand_shape": 0.10,
            "right_hand_shape": 0.30,
            "pose": 0.00,
            "face": 0.00,
            "missing": 0.06,
        },
        "focus_groups": ["two_hand_relation", "right_hand_shape", "right_hand", "left_hand"],
        "allow_hand_swap": True,
        "keypoint_weights": {
            "hand": {"8": 2.25, "12": 2.25, "5": 1.45, "9": 1.45, "index": 2.05, "middle": 2.05},
            "left_hand": {"0": 1.20, "5": 1.25, "9": 1.25, "13": 1.15, "17": 1.15},
            "right_hand": {"8": 2.45, "12": 2.45, "5": 1.55, "9": 1.55, "index": 2.25, "middle": 2.25},
            "pose": {},
            "face": {},
        },
        "semantic_dtw": {
            **DEFAULT_SEMANTIC_DTW,
            "local_phase_weight": 0.016,
            "anchor_penalty_weight": 0.09,
            "hand_global_position_weight": 0.08,
            "relative_motion_weight": 0.14,
            "two_hand_relation_weight": 0.90,
            "group_missing_distance_weight": 0.20,
            "focus_missing_distance_weight": 0.34,
            "relation_missing_distance_weight": 0.78,
            "required_presence_groups": ["left_hand", "right_hand", "two_hand_relation"],
            "required_presence_weight": 0.24,
            "jump_relation_semantic_floor_enabled": True,
            "jump_relation_semantic_max_score": 85.0,
            "jump_relation_semantic_min_presence": 0.58,
            "jump_relation_semantic_min_direction": 0.55,
            "jump_relation_local_fallback_enabled": True,
            "jump_relation_local_min_direction": 0.92,
            "jump_relation_local_min_amplitude_ratio": 0.80,
            "jump_relation_local_max_horizontal_to_vertical": 0.60,
            "jump_relation_local_min_coverage": 0.48,
            "jump_relation_local_max_coverage": 0.78,
            "jump_relation_local_min_two_finger_shape_mean": 0.95,
            "phase_order_guard_enabled": True,
            "phase_order_guard_min_disorder_span_score": 0.60,
            "phase_order_guard_min_adjacent_disorder_span_score": 0.25,
            "phase_order_guard_max_score": 45.0,
            "description": "Short two-hand jump requires the right jumping hand relative to the left ground hand; relation missing is a hard semantic error.",
        },
        "semantic_notes": [
            "DOCX 语义是右手食指/中指模拟两条腿，先弯曲后伸直并向上弹跳；评分主导项是右手两指手形动态。",
            "左手模拟地面，必须进入评分；单手动作缺少左手地面或双手相对关系时应明显扣分。",
            "脸、躯干和手-躯干相对位置不参与主距离，核心是右手在左手基础上的相对跳跃。",
            "动态重要帧主要由 two_hand_relation、跳跃手食指/中指相对运动和弯曲-伸直变化驱动。",
        ],
    },
    "唱歌": {
        "group_weights": {
            "left_hand": 0.20,
            "right_hand": 0.20,
            "left_hand_shape": 0.10,
            "right_hand_shape": 0.10,
            "pose": 0.14,
            "face": 0.21,
            "missing": 0.05,
        },
        "focus_groups": ["left_hand", "right_hand", "face", "pose"],
        "allow_hand_swap": True,
        "keypoint_weights": {
            "hand": {"4": 1.45, "8": 1.45},
            "pose": {"0": 1.40, "11": 1.15, "12": 1.15},
            "face": {"13": 1.80, "14": 1.80, "61": 1.35, "291": 1.35},
        },
        "semantic_notes": [
            "DOCX 语义同时包含双手从喉部向外移出、头部左右晃动和嘴巴张开。",
            "双手拇指/食指、嘴唇张合、头部/肩部运动都参与主评分；这类词不是纯手势动作。",
            "动态重要帧由双手外移、嘴部开合和头部晃动共同决定。",
        ],
    },
    "谗（羡慕）": {
        "group_weights": {
            "left_hand": 0.10,
            "right_hand": 0.24,
            "left_hand_shape": 0.05,
            "right_hand_shape": 0.12,
            "pose": 0.00,
            "face": 0.44,
            "missing": 0.05,
        },
        "focus_groups": ["face", "right_hand", "right_hand_shape"],
        "allow_hand_swap": True,
        "keypoint_weights": {
            "hand": {"8": 1.75, "4": 1.30},
            "pose": {},
            "face": {"13": 1.75, "14": 1.75, "61": 1.60, "291": 1.60},
        },
        "semantic_notes": [
            "DOCX 语义是食指从嘴角向下滑动模拟口水，同时舌头/嘴巴表现馋嘴。",
            "脸部嘴唇/嘴角是主语义之一，手部食指下滑是另一主语义；躯干不参与主距离。",
            "保留少量非主手约束，用于惩罚额外双手动作；动态帧由嘴部和食指下滑共同驱动。",
        ],
    },
    "汽车": {
        "group_weights": {
            "left_hand": 0.30,
            "right_hand": 0.30,
            "left_hand_shape": 0.17,
            "right_hand_shape": 0.17,
            "pose": 0.00,
            "face": 0.00,
            "missing": 0.06,
        },
        "focus_groups": ["left_hand", "right_hand", "left_hand_shape", "right_hand_shape"],
        "allow_hand_swap": True,
        "keypoint_weights": {"hand": {"4": 1.35, "8": 1.35, "12": 1.25, "opening": 1.25}, "pose": {}, "face": {}},
        "semantic_notes": [
            "DOCX 语义是双手虚握并左右转动方向盘；评分只看双手位置、手形和双手协同转动。",
            "脸、嘴和躯干相对位置不参与主距离。",
            "动态重要帧由双手同步旋转/转向动作驱动。",
        ],
    },
    "月亮": {
        "group_weights": {
            "left_hand": 0.24,
            "right_hand": 0.24,
            "left_hand_shape": 0.24,
            "right_hand_shape": 0.24,
            "pose": 0.00,
            "face": 0.00,
            "missing": 0.04,
        },
        "focus_groups": ["left_hand_shape", "right_hand_shape", "left_hand", "right_hand"],
        "allow_hand_swap": True,
        "keypoint_weights": {"hand": {"8": 1.70, "12": 1.55, "spread": 1.90, "opening": 1.75}, "pose": {}, "face": {}},
        "semantic_notes": [
            "DOCX 语义是双手向两边移动时，两根手指距离逐渐变窄，形成弯月形状。",
            "主语义是双手相对运动和指间形状变化；脸、身体和手-躯干关系不参与主距离。",
            "动态重要帧由双手分离过程和双手手指间距变化驱动。",
        ],
    },
    "朋友": {
        "group_weights": {
            "left_hand": 0.30,
            "right_hand": 0.30,
            "left_hand_shape": 0.17,
            "right_hand_shape": 0.17,
            "pose": 0.00,
            "face": 0.00,
            "missing": 0.06,
        },
        "focus_groups": ["left_hand", "right_hand", "left_hand_shape", "right_hand_shape"],
        "allow_hand_swap": True,
        "keypoint_weights": {"hand": {"4": 2.10, "thumb": 2.10}, "pose": {}, "face": {}},
        "semantic_notes": [
            "DOCX 语义是两根大拇指模拟两个人的头，并互相碰两下表示亲密。",
            "主语义是左右拇指位置、碰撞节奏和双手相对运动；脸和躯干不参与主距离。",
            "动态重要帧由两拇指靠近/接触的重复动作驱动。",
        ],
    },
    "指示": {
        "group_weights": {
            "left_hand": 0.24,
            "right_hand": 0.36,
            "left_hand_shape": 0.14,
            "right_hand_shape": 0.21,
            "pose": 0.00,
            "face": 0.00,
            "missing": 0.05,
        },
        "focus_groups": ["right_hand", "right_hand_shape", "left_hand"],
        "allow_hand_swap": True,
        "keypoint_weights": {"hand": {"4": 1.55, "8": 2.05, "index": 1.95, "thumb": 1.55}, "pose": {}, "face": {}},
        "semantic_notes": [
            "DOCX 语义是左手拇指模拟人头，右手食指左右指挥前面的人。",
            "主语义是右手食指的左右摆动和左手拇指参照；脸、身体和真实头部位置不参与主距离。",
            "动态重要帧主要由右手食指摆动驱动，左手拇指作为手部参照。",
        ],
    },
    "虎": {
        "group_weights": {
            "left_hand": 0.24,
            "right_hand": 0.24,
            "left_hand_shape": 0.20,
            "right_hand_shape": 0.20,
            "pose": 0.03,
            "face": 0.04,
            "missing": 0.05,
        },
        "focus_groups": ["left_hand_shape", "right_hand_shape", "left_hand", "right_hand"],
        "allow_hand_swap": True,
        "keypoint_weights": {"hand": {"8": 1.60, "12": 1.45, "16": 1.60, "20": 1.60, "opening": 1.75}, "pose": {"0": 1.20}, "face": {}},
        "semantic_notes": [
            "DOCX 语义包含两段：先在前额比出“王”字，再双手五指弯曲向前下方按动模拟兽爪。",
            "主语义是双手手形和兽爪按动；额头位置只作小权重定位参照，不让脸/躯干主导评分。",
            "动态重要帧由双手从王字过渡到兽爪按动、五指弯曲开合变化驱动。",
        ],
    },
    "香蕉": {
        "group_weights": {
            "left_hand": 0.26,
            "right_hand": 0.34,
            "left_hand_shape": 0.15,
            "right_hand_shape": 0.20,
            "pose": 0.00,
            "face": 0.00,
            "missing": 0.05,
        },
        "focus_groups": ["right_hand", "left_hand", "right_hand_shape", "left_hand_shape"],
        "allow_hand_swap": True,
        "keypoint_weights": {"hand": {"8": 2.00, "index": 1.90, "4": 1.35}, "pose": {}, "face": {}},
        "semantic_notes": [
            "DOCX 语义是左手竖食指表示香蕉，右手沿左手食指向下做剥皮动作。",
            "主语义是左手食指稳定参照和右手剥皮轨迹；脸、身体和手-躯干关系不参与主距离。",
            "动态重要帧主要由右手沿左手食指下滑/剥开的相对运动驱动。",
        ],
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
            "semantic_dtw": dict(preset.get("semantic_dtw", DEFAULT_SEMANTIC_DTW)),
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
        "semantic_dtw": dict(PROFILE_PRESETS["generic"].get("semantic_dtw", DEFAULT_SEMANTIC_DTW)),
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
        semantic_dtw = profile.get("semantic_dtw") or {}
        lines.append(
            "- 语义相位 DTW："
            f"`enabled={semantic_dtw.get('enabled', True)}`, "
            f"`local_phase_weight={float(semantic_dtw.get('local_phase_weight', 0.018)):.3f}`, "
            f"`anchor_penalty_weight={float(semantic_dtw.get('anchor_penalty_weight', 0.10)):.3f}`, "
            f"`phase_order_guard={semantic_dtw.get('phase_order_guard_enabled', False)}`, "
            f"`phase_order_disorder_span={float(semantic_dtw.get('phase_order_guard_min_disorder_span_score', 0.0)):.3f}`, "
            f"`phase_order_adjacent_span={float(semantic_dtw.get('phase_order_guard_min_adjacent_disorder_span_score', 0.0)):.3f}`"
        )
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

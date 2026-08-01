#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""基于最新 21 词 DOCX 与旧评分 Profile 生成完整语义加权配置。"""
from __future__ import annotations

import argparse
import copy
import json
import time
from pathlib import Path


def normalize(weights: dict[str, float]) -> dict[str, float]:
    total = sum(weights.values())
    if total <= 0:
        raise ValueError("empty weights")
    return {key: round(value / total, 8) for key, value in weights.items()}


def profile(weights, focus, hand=None, pose=None, face=None, notes=None, required=None, relation=0.14, phases=None):
    semantic_dtw = {
        "enabled": True,
        "local_phase_weight": 0.018,
        "anchor_penalty_weight": 0.10,
        "anchor_phases": [0.10, 0.50, 0.90],
        "pose_robust_hand_position": True,
        "hand_global_position_weight": 0.12,
        "relative_motion_enabled": False,
        "relative_motion_weight": 0.14,
        "two_hand_relation_weight": relation,
        "required_presence_groups": required or [],
        "required_presence_weight": 0.20 if required else 0.08,
        "phase_order_guard_enabled": bool(phases and len(phases) > 1),
        "phase_order_guard_anchor_phases": [0.10, 0.25, 0.50, 0.75, 0.90],
        "phase_order_guard_max_score": 45.0,
        "description": "按语义能量阶段而非绝对帧号进行软 DTW 对齐。",
    }
    return {
        "group_weights": normalize(weights),
        "keypoint_weights": {"hand": hand or {}, "pose": pose or {}, "face": face or {}},
        "focus_groups": focus,
        "allow_hand_swap": True,
        "semantic_dtw": semantic_dtw,
        "semantic_phases": phases or [],
        "semantic_notes": notes or [],
        "profile_status": "text_derived_pending_empirical_calibration",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--legacy-profile", type=Path, required=True)
    parser.add_argument("--semantic-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    legacy = json.loads(args.legacy_profile.read_text(encoding="utf-8"))
    source = json.loads(args.semantic_source.read_text(encoding="utf-8"))
    source_by_word = {entry["acquisition_word"]: entry for entry in source["entries"]}
    acquisition_order = [
        "谗（羡慕）", "唱歌", "超市", "船（轮船）", "公交车", "虎", "花", "鸡蛋",
        "烤串", "科学", "牛奶", "朋友", "汽车（一）", "汽车二", "人们（人民）",
        "森林", "跳", "香蕉", "勇敢", "月亮", "指示",
    ]

    profiles = {}
    legacy_map = {
        "谗（羡慕）": "谗（羡慕）", "唱歌": "唱歌", "虎": "虎", "花": "花",
        "朋友": "朋友", "跳": "跳", "香蕉": "香蕉", "月亮": "月亮", "指示": "指示",
        "汽车（一）": "汽车",
    }
    for word, old_word in legacy_map.items():
        item = copy.deepcopy(legacy["profiles"][old_word])
        item["word"] = word
        item["profile_origin"] = f"legacy_calibrated:{old_word}"
        if word == "汽车（一）":
            item["semantic_id"] = "汽车_方向盘"
            item["semantic_notes"] = [
                "汽车（一）为双手虚握方向盘并左右转动；已由用户确认并通过切片尾部密集帧复核。",
                "双手相对位置、虚握手形和协同旋转是主语义；脸与躯干不参与主距离。",
            ]
        profiles[word] = item

    profiles["超市"] = profile(
        {"left_hand": .23, "right_hand": .23, "left_hand_shape": .20, "right_hand_shape": .20, "pose": .05, "face": 0, "missing": .09},
        ["left_hand", "right_hand", "left_hand_shape", "right_hand_shape", "two_hand_relation"],
        hand={"0": 1.3, "4": 1.4, "8": 1.35, "opening": 1.7}, relation=.55,
        required=["left_hand", "right_hand", "two_hand_relation"],
        phases=["双手虚握购物车把手", "双手向前推动", "双手交替向两边抓取", "回到虚握"],
        notes=["双手购物车把手关系和前推动作为第一阶段；交替抓取商品并回位作为第二阶段。"],
    )
    profiles["船（轮船）"] = profile(
        {"left_hand": .28, "right_hand": .28, "left_hand_shape": .17, "right_hand_shape": .17, "pose": .03, "face": 0, "missing": .07},
        ["left_hand", "right_hand", "two_hand_relation"], hand={"8": 1.65, "12": 1.35, "opening": 1.25}, relation=.65,
        required=["left_hand", "right_hand", "two_hand_relation"], phases=["双手斜立指尖相抵形成船头", "双手整体向前航行"],
        notes=["船头几何关系和双手同步向前轨迹共同主导。"],
    )
    profiles["公交车"] = profile(
        {"left_hand": .10, "right_hand": .38, "left_hand_shape": .08, "right_hand_shape": .29, "pose": .08, "face": 0, "missing": .07},
        ["right_hand", "right_hand_shape"], hand={"0": 1.2, "4": 1.6, "8": 1.55, "opening": 1.7},
        phases=["主手虚握虎口朝内", "虚握手前后晃动两次"], notes=["主手虚握和前后重复晃动是核心；允许主辅手镜像。"],
    )
    profiles["鸡蛋"] = profile(
        {"left_hand": .20, "right_hand": .27, "left_hand_shape": .18, "right_hand_shape": .25, "pose": .03, "face": .02, "missing": .05},
        ["right_hand_shape", "right_hand", "left_hand", "two_hand_relation"], hand={"4": 1.9, "8": 1.9, "opening": 1.7}, relation=.45,
        phases=["单手拇食指撮合放嘴前表示鸡嘴", "双手拇食指形成椭圆", "双手分开表示打蛋"],
        notes=["鸡与蛋为有序两阶段动作，必须保留阶段顺序。"],
    )
    profiles["烤串"] = profile(
        {"left_hand": .22, "right_hand": .22, "left_hand_shape": .24, "right_hand_shape": .24, "pose": .01, "face": 0, "missing": .07},
        ["left_hand_shape", "right_hand_shape", "left_hand", "right_hand"],
        hand={"4": 1.5, "8": 1.45, "12": 1.45, "16": 1.45, "20": 1.45, "spread": 1.5}, relation=.35,
        required=["left_hand", "right_hand"], phases=["双手收拇指平摊四指", "双手左右翻转烤串"],
        notes=["八指平摊手形与双手反复翻转是核心。"],
    )
    profiles["科学"] = profile(
        {"left_hand": .19, "right_hand": .27, "left_hand_shape": .20, "right_hand_shape": .24, "pose": .04, "face": 0, "missing": .06},
        ["left_hand_shape", "right_hand_shape", "left_hand", "right_hand"],
        hand={"4": 1.5, "8": 1.8, "12": 1.8, "opening": 1.5}, relation=.38,
        phases=["双手K手形交替向前绕圈", "单手五指撮合从外向前额并按下"],
        notes=["科学交流与学习为有序两阶段；K手形和前额方向轨迹分别加权。"],
    )
    profiles["牛奶"] = profile(
        {"left_hand": .08, "right_hand": .38, "left_hand_shape": .08, "right_hand_shape": .27, "pose": .13, "face": 0, "missing": .06},
        ["right_hand", "right_hand_shape", "pose"], hand={"4": 1.45, "8": 1.5, "opening": 1.8}, pose={"0": 1.3, "11": 1.25, "12": 1.25},
        phases=["单手牛角手形抵太阳穴", "单手五指弯曲挤压并下移"], notes=["牛与奶为有序两阶段，太阳穴定位和挤压下移均保留。"],
    )
    profiles["汽车二"] = profile(
        {"left_hand": .08, "right_hand": .42, "left_hand_shape": .08, "right_hand_shape": .34, "pose": .02, "face": 0, "missing": .06},
        ["right_hand", "right_hand_shape"], hand={"0": 1.25, "4": 1.4, "8": 1.45, "12": 1.35, "16": 1.3, "20": 1.3, "opening": 1.6},
        phases=["单手五指形成方块车身", "该手整体向前移动"], notes=["汽车二为单手车身前行；已由用户确认并通过切片密集帧复核。"],
    )
    profiles["人们（人民）"] = profile(
        {"left_hand": .27, "right_hand": .27, "left_hand_shape": .18, "right_hand_shape": .18, "pose": .03, "face": 0, "missing": .07},
        ["left_hand", "right_hand", "two_hand_relation"], hand={"8": 1.9, "index": 1.8}, relation=.65,
        required=["left_hand", "right_hand", "two_hand_relation"], phases=["双手食指形成人字", "人字从胸前顺时针转动一圈"],
        notes=["双食指人字关系和整体顺时针环绕轨迹共同主导。"],
    )
    profiles["森林"] = profile(
        {"left_hand": .24, "right_hand": .24, "left_hand_shape": .19, "right_hand_shape": .19, "pose": .06, "face": 0, "missing": .08},
        ["left_hand", "right_hand", "left_hand_shape", "right_hand_shape", "two_hand_relation"],
        hand={"4": 1.7, "8": 1.7, "opening": 1.55}, relation=.48,
        phases=["双手拇食指形成大圆树干", "在三个不同位置自下而上移动"], notes=["大圆树干手形和三处上移的重复空间轨迹是核心。"],
    )
    profiles["勇敢"] = profile(
        {"left_hand": .22, "right_hand": .22, "left_hand_shape": .17, "right_hand_shape": .17, "pose": .14, "face": .03, "missing": .05},
        ["left_hand", "right_hand", "pose", "two_hand_relation"], hand={"4": 1.55, "8": 1.7, "opening": 1.5}, pose={"0": 1.2, "11": 1.4, "12": 1.4, "23": 1.2, "24": 1.2}, relation=.42,
        phases=["双手贴腹伸拇食指", "双手向两边用力拉开", "抬头挺胸并保持坚毅表情"],
        notes=["双手横向拉开是主动作，抬头挺胸为辅助语义；面部只给小权重。"],
    )

    output_profiles = {}
    for acquisition_index, word in enumerate(acquisition_order, start=1):
        item = profiles[word]
        source_entry = source_by_word[word]
        item["word"] = word
        item["acquisition_word_index"] = acquisition_index
        item["document_order"] = source_entry["document_order"]
        item["semantic_id"] = source_entry["semantic_id"]
        item["source_lines"] = source_entry["key_semantics"]
        item["docx_source"] = source["source_docx"]
        output_profiles[word] = item

    payload = {
        "version": "demo21_semantic_weights_v2_20260801",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S %z"),
        "docx_path": source["source_docx"],
        "claim_policy": "Text-derived engineering weights; legacy-calibrated profiles preserved where available; new profiles require empirical calibration.",
        "handedness_policy": "原始左右 landmark 保留；评分时按用户惯用手或 best-of hand swap 归一化主辅手。",
        "face_policy": "仅使用12个核心眼口面部点；只有文档明确包含口型、头部或表情语义时赋非零权重。",
        "profiles": output_profiles,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "profile_count": len(output_profiles)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

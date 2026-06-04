# 花/跳左右手标签抖动鲁棒性门

- 生成时间：`2026-06-04T06:04:50`
- 综合状态：`PASS`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON；在部分帧交换 left/right hand 与 hand-shape 标签后复算相对运动；不调用 `/api/score`，不移动 marker，不运行 Holistic，不重启 5080。

## 判定口径

- 单帧或稀疏左右手标签 flicker 是正向鲁棒性门；这模拟 Holistic 短暂 handedness 抖动。
- 持续核心段 flicker 或交替 flicker 是负向边界；这类采集太不稳定，应低分并进入 `needs_recapture/semantic_mismatch`。

## 摘要

| 词条 | 状态 | 正向最低分 | 最弱正向 flicker | 负向最高分 | 最强负向 flicker |
|---|---|---:|---|---:|---|
| 花 | PASS | 96.804 | sparse_label_flicker | 27.593 | sustained_core_label_flicker_negative |
| 跳 | PASS | 70.469 | single_frame_label_flicker | 14.618 | alternating_label_flicker_negative |

## 明细

| 词条 | 变体 | 类型 | flicker 帧 | 分数 | 状态 | 采集质量 | floor 原因 | 说明 |
|---|---|---|---:|---:|---|---|---|---|
| 花 | self_recomputed | positive | 0/53 | 100.000 | PASS | score_valid / score_valid | query_not_short_core_capture | same sequence should stay near perfect after feature recomputation |
| 花 | single_frame_label_flicker | positive | 1/53 | 98.991 | PASS | score_valid / score_valid | query_not_short_core_capture | one-frame detector side flicker should not break an otherwise correct sign |
| 花 | sparse_label_flicker | positive | 11/53 | 96.804 | PASS | score_valid / score_valid | query_not_short_core_capture | sparse detector side flicker should remain scoreable |
| 花 | sustained_core_label_flicker_negative | negative | 11/53 | 27.593 | PASS | needs_recapture / flower_core_hand_presence_low | query_not_short_core_capture | sustained core-side instability should become recapture/semantic-failure evidence |
| 花 | alternating_label_flicker_negative | negative | 26/53 | 1.797 | PASS | needs_recapture / flower_core_hand_presence_low | query_not_short_core_capture | alternating label flicker is too unstable to accept as a normal web capture |
| 跳 | self_recomputed | positive | 0/19 | 100.000 | PASS | score_valid / score_valid | used | same sequence should stay near perfect after feature recomputation |
| 跳 | single_frame_label_flicker | positive | 1/19 | 70.469 | PASS | score_valid / score_valid | used | one-frame detector side flicker should not break an otherwise correct sign |
| 跳 | sparse_label_flicker | positive | 4/19 | 84.587 | PASS | score_valid / score_valid | used | sparse detector side flicker should remain scoreable |
| 跳 | short_contiguous_role_flicker | positive | 3/19 | 72.905 | PASS | score_valid / score_valid | used | short role-label flicker should not erase the local jump segment |
| 跳 | alternating_label_flicker_negative | negative | 9/19 | 14.618 | PASS | semantic_mismatch / relation_direction_mismatch | relation_direction_mismatch | alternating label flicker is too unstable to accept as a normal web capture |

## 结论

- 左右手标签抖动边界通过：短暂 flicker 不破坏 `花/跳` 正常评分，持续/交替 flicker 不会被误接收为正常动作。

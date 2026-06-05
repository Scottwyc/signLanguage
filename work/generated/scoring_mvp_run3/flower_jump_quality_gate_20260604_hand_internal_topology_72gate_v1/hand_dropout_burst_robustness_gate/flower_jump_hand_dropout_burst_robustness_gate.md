# 花/跳连续手部检出空洞鲁棒性门

- 生成时间：`2026-06-04T16:08:28`
- 总体：`PASS`
- 模板根目录：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义权重：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 门槛：正向短空洞最低分 `>= 70.0`；持续核心空洞需低分或进入 `needs_recapture, semantic_mismatch`。
- 口径：只读缓存 Holistic JSON，在基础手部/手形 mask 层面合成连续空洞，并重建 motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。

## 汇总

| 词条 | 状态 | 正向最低分 | 最弱正向空洞 | 持续空洞最高分 | 最强持续空洞 |
|---|---|---:|---|---:|---|
| 花 | PASS | 95.170 | right_core_15pct_mid | 55.975 | right_core_25pct_mid_negative |
| 跳 | PASS | 74.629 | right_jump_3f_mid | 18.484 | both_hands_2f_mid_negative |

## 明细

### 花

| 变体 | 类型 | 状态 | 分数 | 帧段 | 组 | quality | floor | 说明 |
|---|---|---|---:|---|---|---|---|---|
| right_core_1f_mid | positive | PASS (>= 70.0) | 99.040 | 26+1 | right_hand | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花手单帧短空洞。 |
| right_core_3f_mid | positive | PASS (>= 70.0) | 97.950 | 25+3 | right_hand | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花手连续 3 帧短空洞。 |
| right_core_5f_mid | positive | PASS (>= 70.0) | 97.083 | 24+5 | right_hand | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花手连续 5 帧短空洞。 |
| right_core_15pct_mid | positive | PASS (>= 70.0) | 95.170 | 22+8 | right_hand | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花手约 15% 中段短空洞，仍应可评分。 |
| left_noncore_15pct_mid | positive | PASS (>= 70.0) | 100.000 | 22+8 | left_hand | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 非核心手约 15% 中段空洞，不应影响开花语义。 |
| right_core_25pct_mid_negative | negative | PASS (<= 45.0 或重采/语义失败) | 55.975 | 20+13 | right_hand | needs_recapture:flower_core_hand_presence_low | short_visible_core:query_not_short_core_capture | 开花手约 25% 中段缺失，应进入重采或明显降分。 |
| right_core_35pct_mid_negative | negative | PASS (<= 45.0 或重采/语义失败) | 37.752 | 17+19 | right_hand | needs_recapture:flower_core_hand_presence_low | short_visible_core:query_not_short_core_capture | 开花手约 35% 中段缺失，应稳定拒绝。 |

### 跳

| 变体 | 类型 | 状态 | 分数 | 帧段 | 组 | quality | floor | 说明 |
|---|---|---|---:|---|---|---|---|---|
| right_jump_1f_mid | positive | PASS (>= 70.0) | 81.566 | 9+1 | right_hand | score_valid:score_valid | full_sequence_local_relation_segment:used | 跳跃手单帧短空洞。 |
| right_jump_2f_mid | positive | PASS (>= 70.0) | 78.525 | 8+2 | right_hand | score_valid:score_valid | full_sequence_local_relation_segment:used | 跳跃手连续 2 帧短空洞。 |
| right_jump_3f_mid | positive | PASS (>= 70.0) | 74.629 | 8+3 | right_hand | score_valid:score_valid | full_sequence_local_relation_segment:used | 跳跃手连续 3 帧短空洞。 |
| left_ground_1f_mid | positive | PASS (>= 70.0) | 81.563 | 9+1 | left_hand | score_valid:score_valid | action_window_net:used | 地面手单帧短空洞。 |
| left_ground_2f_mid | positive | PASS (>= 70.0) | 76.905 | 8+2 | left_hand | score_valid:score_valid | action_window_net:used | 地面手连续 2 帧短空洞。 |
| both_hands_1f_mid | positive | PASS (>= 70.0) | 78.545 | 9+1 | left_hand+right_hand | score_valid:score_valid | full_sequence_local_relation_segment:used | 双手同帧短空洞 1 帧。 |
| both_hands_2f_mid_negative | negative | PASS (<= 45.0 或重采/语义失败) | 18.484 | 8+2 | left_hand+right_hand | needs_recapture:jump_two_hand_presence_low | -:insufficient_two_hand_presence | 双手连续 2 帧同时缺失，应进入重采或明显降分。 |
| right_jump_4f_mid_negative | negative | PASS (<= 45.0 或重采/语义失败) | 13.199 | 7+4 | right_hand | needs_recapture:jump_two_hand_presence_low | -:required_presence_penalty_too_high | 跳跃手连续 4 帧缺失，应进入重采或明显降分。 |

## 结论

- 短 burst 检出空洞用于验证网页端偶发 detector 丢帧不会直接打崩正常动作。
- 持续核心手空洞是重采边界，不能用鲁棒性门把这种样本抬成正常高分。
- 该门仍是合成压力测试，不能替代正式 marker 后真实网页摄像头样本。

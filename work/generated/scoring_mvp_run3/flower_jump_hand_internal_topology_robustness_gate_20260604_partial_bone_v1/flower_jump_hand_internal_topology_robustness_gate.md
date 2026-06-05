# 花/跳 Hand 内部拓扑完整性鲁棒性门

- 生成时间：`2026-06-04T19:03:00`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 硬边界：backtrack turns `>=6`，或非拇指 proximal/distal 中位比 `<0.5`，或全部指链反向且该比值 `<0.8`。
- 正常证据审计：`178` 个模板/网页 JSON、`4750` 个非空手帧，违规 `0`；正常最大 backtrack `5`，最大反向链 `4`，最小 proximal/distal 中位比 `0.5209601104389956`。
- 控制组：相邻整指链交换保持各指链内部顺序，必须保留并继续由 finger-identity 容错评分。
- 口径：只写缓存 Holistic JSON fixture；不调用 `/api/score`、不运行 Holistic、不移动 marker、不重启 5080。

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向变体 | 整段损坏诊断最高分 | 最强诊断变体 |
|---|---|---:|---|---:|---|
| 花 | PASS | 79.773 | right_hand_landmarks_adjacent_chain_swap_preserved | 1.164 | right_hand_landmarks_rotate_internal_1_full_recapture |
| 跳 | PASS | 81.642 | right_hand_landmarks_reverse_internal_all_sparse_masked | 2.161 | left_hand_landmarks_reverse_internal_all_full_recapture |

## 分项明细

### 花

| 变体 | 类型 | 状态 | 分数 | 阈值 | 损坏帧 | 屏蔽率 | 拓扑处理正确 | capture_quality |
|---|---|---|---:|---:|---:|---:|---|---|
| self_reloaded | positive | PASS | 100.000 | 95.000 | 0 | 0.000 | True | score_valid:score_valid |
| right_hand_landmarks_reverse_internal_all_sparse_masked | positive | PASS | 96.952 | 75.000 | 6 | 0.833 | True | score_valid:score_valid |
| right_hand_landmarks_reverse_internal_all_full_recapture | diagnostic | PASS | 0.628 | 55.000 | 40 | 0.950 | True | needs_recapture:flower_core_hand_presence_low |
| right_hand_landmarks_rotate_internal_1_sparse_masked | positive | PASS | 98.112 | 75.000 | 6 | 1.000 | True | score_valid:score_valid |
| right_hand_landmarks_rotate_internal_1_full_recapture | diagnostic | PASS | 1.164 | 55.000 | 40 | 1.000 | True | needs_recapture:flower_core_hand_presence_low |
| right_hand_landmarks_rotate_internal_2_sparse_masked | positive | PASS | 96.493 | 75.000 | 6 | 0.833 | True | score_valid:score_valid |
| right_hand_landmarks_rotate_internal_2_full_recapture | diagnostic | PASS | 0.953 | 55.000 | 40 | 0.950 | True | needs_recapture:flower_core_hand_presence_low |
| right_hand_landmarks_rotate_internal_5_sparse_masked | positive | PASS | 98.112 | 75.000 | 6 | 1.000 | True | score_valid:score_valid |
| right_hand_landmarks_rotate_internal_5_full_recapture | diagnostic | PASS | 1.164 | 55.000 | 40 | 1.000 | True | needs_recapture:flower_core_hand_presence_low |
| right_hand_landmarks_reverse_each_chain_sparse_masked | positive | PASS | 97.351 | 75.000 | 6 | 0.833 | True | score_valid:score_valid |
| right_hand_landmarks_reverse_each_chain_full_recapture | diagnostic | PASS | 0.773 | 55.000 | 40 | 0.950 | True | needs_recapture:flower_core_hand_presence_low |
| right_hand_landmarks_swap_base_tip_each_chain_sparse_masked | positive | PASS | 98.112 | 75.000 | 6 | 1.000 | True | score_valid:score_valid |
| right_hand_landmarks_swap_base_tip_each_chain_full_recapture | diagnostic | PASS | 1.164 | 55.000 | 40 | 1.000 | True | needs_recapture:flower_core_hand_presence_low |
| right_hand_landmarks_swap_pip_dip_each_chain_sparse_masked | positive | PASS | 98.112 | 75.000 | 6 | 1.000 | True | score_valid:score_valid |
| right_hand_landmarks_swap_pip_dip_each_chain_full_recapture | diagnostic | PASS | 1.164 | 55.000 | 40 | 1.000 | True | needs_recapture:flower_core_hand_presence_low |
| right_hand_landmarks_adjacent_chain_swap_preserved | positive | PASS | 79.773 | 70.000 | 40 | 0.000 | True | score_valid:score_valid |

### 跳

| 变体 | 类型 | 状态 | 分数 | 阈值 | 损坏帧 | 屏蔽率 | 拓扑处理正确 | capture_quality |
|---|---|---|---:|---:|---:|---:|---|---|
| self_reloaded | positive | PASS | 100.000 | 95.000 | 0 | 0.000 | True | score_valid:score_valid |
| right_hand_landmarks_reverse_internal_all_sparse_masked | positive | PASS | 81.642 | 75.000 | 2 | 1.000 | True | score_valid:score_valid |
| right_hand_landmarks_reverse_internal_all_full_recapture | diagnostic | PASS | 0.303 | 55.000 | 17 | 0.941 | True | needs_recapture:jump_two_hand_presence_low |
| right_hand_landmarks_rotate_internal_1_sparse_masked | positive | PASS | 81.642 | 75.000 | 2 | 1.000 | True | score_valid:score_valid |
| right_hand_landmarks_rotate_internal_1_full_recapture | diagnostic | PASS | 0.236 | 55.000 | 17 | 1.000 | True | needs_recapture:jump_two_hand_presence_low |
| right_hand_landmarks_rotate_internal_2_sparse_masked | positive | PASS | 81.642 | 75.000 | 2 | 1.000 | True | score_valid:score_valid |
| right_hand_landmarks_rotate_internal_2_full_recapture | diagnostic | PASS | 0.236 | 55.000 | 17 | 1.000 | True | needs_recapture:jump_two_hand_presence_low |
| right_hand_landmarks_rotate_internal_5_sparse_masked | positive | PASS | 81.642 | 75.000 | 2 | 1.000 | True | score_valid:score_valid |
| right_hand_landmarks_rotate_internal_5_full_recapture | diagnostic | PASS | 0.236 | 55.000 | 17 | 1.000 | True | needs_recapture:jump_two_hand_presence_low |
| right_hand_landmarks_reverse_each_chain_sparse_masked | positive | PASS | 81.642 | 75.000 | 2 | 1.000 | True | score_valid:score_valid |
| right_hand_landmarks_reverse_each_chain_full_recapture | diagnostic | PASS | 0.236 | 55.000 | 17 | 1.000 | True | needs_recapture:jump_two_hand_presence_low |
| right_hand_landmarks_swap_base_tip_each_chain_sparse_masked | positive | PASS | 81.642 | 75.000 | 2 | 1.000 | True | score_valid:score_valid |
| right_hand_landmarks_swap_base_tip_each_chain_full_recapture | diagnostic | PASS | 0.236 | 55.000 | 17 | 1.000 | True | needs_recapture:jump_two_hand_presence_low |
| right_hand_landmarks_swap_pip_dip_each_chain_sparse_masked | positive | PASS | 81.642 | 75.000 | 2 | 1.000 | True | score_valid:score_valid |
| right_hand_landmarks_swap_pip_dip_each_chain_full_recapture | diagnostic | PASS | 0.236 | 55.000 | 17 | 1.000 | True | needs_recapture:jump_two_hand_presence_low |
| right_hand_landmarks_adjacent_chain_swap_preserved | positive | PASS | 85.000 | 70.000 | 17 | 0.000 | True | score_valid:score_valid |
| left_hand_landmarks_reverse_internal_all_sparse_masked | positive | PASS | 84.678 | 75.000 | 2 | 1.000 | True | score_valid:score_valid |
| left_hand_landmarks_reverse_internal_all_full_recapture | diagnostic | PASS | 2.161 | 55.000 | 16 | 1.000 | True | needs_recapture:jump_two_hand_presence_low |
| left_hand_landmarks_rotate_internal_1_sparse_masked | positive | PASS | 84.678 | 75.000 | 2 | 1.000 | True | score_valid:score_valid |
| left_hand_landmarks_rotate_internal_1_full_recapture | diagnostic | PASS | 2.161 | 55.000 | 16 | 1.000 | True | needs_recapture:jump_two_hand_presence_low |
| left_hand_landmarks_rotate_internal_2_sparse_masked | positive | PASS | 84.678 | 75.000 | 2 | 1.000 | True | score_valid:score_valid |
| left_hand_landmarks_rotate_internal_2_full_recapture | diagnostic | PASS | 2.161 | 55.000 | 16 | 1.000 | True | needs_recapture:jump_two_hand_presence_low |
| left_hand_landmarks_rotate_internal_5_sparse_masked | positive | PASS | 84.678 | 75.000 | 2 | 1.000 | True | score_valid:score_valid |
| left_hand_landmarks_rotate_internal_5_full_recapture | diagnostic | PASS | 2.161 | 55.000 | 16 | 1.000 | True | needs_recapture:jump_two_hand_presence_low |
| left_hand_landmarks_reverse_each_chain_sparse_masked | positive | PASS | 84.678 | 75.000 | 2 | 1.000 | True | score_valid:score_valid |
| left_hand_landmarks_reverse_each_chain_full_recapture | diagnostic | PASS | 2.161 | 55.000 | 16 | 1.000 | True | needs_recapture:jump_two_hand_presence_low |
| left_hand_landmarks_swap_base_tip_each_chain_sparse_masked | positive | PASS | 84.678 | 75.000 | 2 | 1.000 | True | score_valid:score_valid |
| left_hand_landmarks_swap_base_tip_each_chain_full_recapture | diagnostic | PASS | 2.161 | 55.000 | 16 | 1.000 | True | needs_recapture:jump_two_hand_presence_low |
| left_hand_landmarks_swap_pip_dip_each_chain_sparse_masked | positive | PASS | 84.678 | 75.000 | 2 | 1.000 | True | score_valid:score_valid |
| left_hand_landmarks_swap_pip_dip_each_chain_full_recapture | diagnostic | PASS | 2.161 | 55.000 | 16 | 1.000 | True | needs_recapture:jump_two_hand_presence_low |
| left_hand_landmarks_adjacent_chain_swap_preserved | positive | PASS | 98.468 | 70.000 | 16 | 0.000 | True | score_valid:score_valid |

## 说明

- 该门只屏蔽具有强解剖矛盾的内部索引损坏，不声称识别所有可能的等长 permutation。
- 正常证据审计是硬门；阈值若命中当前任一正常手帧，该门失败并要求重新审计。
- 该门补充 wrist 根身份门和 finger-identity-jitter 门，不替代正式 marker 后真实网页摄像头复测。

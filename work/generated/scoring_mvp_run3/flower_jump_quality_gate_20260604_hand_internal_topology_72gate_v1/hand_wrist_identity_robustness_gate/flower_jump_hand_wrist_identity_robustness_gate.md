# 花/跳 Hand Wrist 身份完整性鲁棒性门

- 生成时间：`2026-06-04T16:31:21`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- wrist-z 原点阈值：`2e-06`
- 正常证据审计：`178` 个模板/网页 JSON、`4750` 个非空手帧，违规 `z0`=`0`，最大 `|z0|`=`9.218072136718547e-07`。
- 固定契约：MediaPipe hand landmark `z` 以 wrist 为原点，因此 index `0` 的绝对 z 必须接近零；等长数组若把 wrist 移到其它 index，整手按缺失处理。
- 控制组：相邻整指链交换不移动 wrist index `0`，必须保留并继续由 finger-identity 容错评分。
- 口径：只写缓存 Holistic JSON fixture；不调用 `/api/score`、不运行 Holistic、不移动 marker、不重启 5080。

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向变体 | 整段损坏诊断最高分 | 最强诊断变体 |
|---|---|---:|---|---:|---|
| 花 | PASS | 79.773 | right_hand_landmarks_adjacent_chain_swap_preserved | 1.164 | right_hand_landmarks_rotate_left_1_full_recapture |
| 跳 | PASS | 81.642 | right_hand_landmarks_rotate_left_1_sparse_masked | 2.161 | left_hand_landmarks_rotate_left_1_full_recapture |

## 分项明细

### 花

| 变体 | 类型 | 状态 | 分数 | 阈值 | 损坏帧 | 预期屏蔽 | 身份处理正确 | capture_quality |
|---|---|---|---:|---:|---:|---|---|---|
| self_reloaded | positive | PASS | 100.000 | 95.000 | 0 | False | True | score_valid:score_valid |
| right_hand_landmarks_rotate_left_1_sparse_masked | positive | PASS | 98.112 | 75.000 | 6 | True | True | score_valid:score_valid |
| right_hand_landmarks_rotate_left_1_full_recapture | diagnostic | PASS | 1.164 | 55.000 | 40 | True | True | needs_recapture:flower_core_hand_presence_low |
| right_hand_landmarks_rotate_left_5_sparse_masked | positive | PASS | 98.112 | 75.000 | 6 | True | True | score_valid:score_valid |
| right_hand_landmarks_rotate_left_5_full_recapture | diagnostic | PASS | 1.164 | 55.000 | 40 | True | True | needs_recapture:flower_core_hand_presence_low |
| right_hand_landmarks_reverse_sparse_masked | positive | PASS | 98.112 | 75.000 | 6 | True | True | score_valid:score_valid |
| right_hand_landmarks_reverse_full_recapture | diagnostic | PASS | 1.164 | 55.000 | 40 | True | True | needs_recapture:flower_core_hand_presence_low |
| right_hand_landmarks_swap_wrist_thumb_tip_sparse_masked | positive | PASS | 98.112 | 75.000 | 6 | True | True | score_valid:score_valid |
| right_hand_landmarks_swap_wrist_thumb_tip_full_recapture | diagnostic | PASS | 1.164 | 55.000 | 40 | True | True | needs_recapture:flower_core_hand_presence_low |
| right_hand_landmarks_swap_wrist_index_mcp_sparse_masked | positive | PASS | 98.112 | 75.000 | 6 | True | True | score_valid:score_valid |
| right_hand_landmarks_swap_wrist_index_mcp_full_recapture | diagnostic | PASS | 1.164 | 55.000 | 40 | True | True | needs_recapture:flower_core_hand_presence_low |
| right_hand_landmarks_adjacent_chain_swap_preserved | positive | PASS | 79.773 | 70.000 | 40 | False | True | score_valid:score_valid |

### 跳

| 变体 | 类型 | 状态 | 分数 | 阈值 | 损坏帧 | 预期屏蔽 | 身份处理正确 | capture_quality |
|---|---|---|---:|---:|---:|---|---|---|
| self_reloaded | positive | PASS | 100.000 | 95.000 | 0 | False | True | score_valid:score_valid |
| right_hand_landmarks_rotate_left_1_sparse_masked | positive | PASS | 81.642 | 75.000 | 2 | True | True | score_valid:score_valid |
| right_hand_landmarks_rotate_left_1_full_recapture | diagnostic | PASS | 0.236 | 55.000 | 17 | True | True | needs_recapture:jump_two_hand_presence_low |
| right_hand_landmarks_rotate_left_5_sparse_masked | positive | PASS | 81.642 | 75.000 | 2 | True | True | score_valid:score_valid |
| right_hand_landmarks_rotate_left_5_full_recapture | diagnostic | PASS | 0.236 | 55.000 | 17 | True | True | needs_recapture:jump_two_hand_presence_low |
| right_hand_landmarks_reverse_sparse_masked | positive | PASS | 81.642 | 75.000 | 2 | True | True | score_valid:score_valid |
| right_hand_landmarks_reverse_full_recapture | diagnostic | PASS | 0.236 | 55.000 | 17 | True | True | needs_recapture:jump_two_hand_presence_low |
| right_hand_landmarks_swap_wrist_thumb_tip_sparse_masked | positive | PASS | 81.642 | 75.000 | 2 | True | True | score_valid:score_valid |
| right_hand_landmarks_swap_wrist_thumb_tip_full_recapture | diagnostic | PASS | 0.236 | 55.000 | 17 | True | True | needs_recapture:jump_two_hand_presence_low |
| right_hand_landmarks_swap_wrist_index_mcp_sparse_masked | positive | PASS | 81.642 | 75.000 | 2 | True | True | score_valid:score_valid |
| right_hand_landmarks_swap_wrist_index_mcp_full_recapture | diagnostic | PASS | 0.236 | 55.000 | 17 | True | True | needs_recapture:jump_two_hand_presence_low |
| right_hand_landmarks_adjacent_chain_swap_preserved | positive | PASS | 85.000 | 70.000 | 17 | False | True | score_valid:score_valid |
| left_hand_landmarks_rotate_left_1_sparse_masked | positive | PASS | 84.678 | 75.000 | 2 | True | True | score_valid:score_valid |
| left_hand_landmarks_rotate_left_1_full_recapture | diagnostic | PASS | 2.161 | 55.000 | 16 | True | True | needs_recapture:jump_two_hand_presence_low |
| left_hand_landmarks_rotate_left_5_sparse_masked | positive | PASS | 84.678 | 75.000 | 2 | True | True | score_valid:score_valid |
| left_hand_landmarks_rotate_left_5_full_recapture | diagnostic | PASS | 2.161 | 55.000 | 16 | True | True | needs_recapture:jump_two_hand_presence_low |
| left_hand_landmarks_reverse_sparse_masked | positive | PASS | 84.678 | 75.000 | 2 | True | True | score_valid:score_valid |
| left_hand_landmarks_reverse_full_recapture | diagnostic | PASS | 2.161 | 55.000 | 16 | True | True | needs_recapture:jump_two_hand_presence_low |
| left_hand_landmarks_swap_wrist_thumb_tip_sparse_masked | positive | PASS | 84.678 | 75.000 | 2 | True | True | score_valid:score_valid |
| left_hand_landmarks_swap_wrist_thumb_tip_full_recapture | diagnostic | PASS | 2.161 | 55.000 | 16 | True | True | needs_recapture:jump_two_hand_presence_low |
| left_hand_landmarks_swap_wrist_index_mcp_sparse_masked | positive | PASS | 84.678 | 75.000 | 2 | True | True | score_valid:score_valid |
| left_hand_landmarks_swap_wrist_index_mcp_full_recapture | diagnostic | PASS | 2.161 | 55.000 | 16 | True | True | needs_recapture:jump_two_hand_presence_low |
| left_hand_landmarks_adjacent_chain_swap_preserved | positive | PASS | 98.468 | 70.000 | 16 | False | True | score_valid:score_valid |

## 说明

- 正常证据审计是硬门：当前缓存中的任何非空手帧若违反 wrist-z 原点契约，该门都会失败并要求重新审计阈值或输入格式。
- 该门补充 exact-length 数组的 wrist 根身份损坏，不替代允许相邻 finger-chain 标签混淆的 finger-identity-jitter 门。
- 该门是缓存 JSON 压力测试，不替代正式 marker 后真实网页摄像头复测。

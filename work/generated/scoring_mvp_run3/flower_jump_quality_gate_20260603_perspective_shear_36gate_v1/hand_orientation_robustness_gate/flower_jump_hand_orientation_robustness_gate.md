# 花/跳手部局部旋转鲁棒性门

- 生成时间：`2026-06-03T20:03:32`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，在手部局部坐标层面围绕手腕旋转并重算 `left_hand_shape/right_hand_shape`；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：用户手腕角度与 demo 略有差异时，`花/跳` 核心语义仍保持可评分；极端手部旋转只记录诊断边界。

- 5080 状态：worker=`ready`，worker_pid=`811485`，reload_count=`14`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向旋转 | 诊断最低分 | 最弱诊断旋转 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 81.336 | both_hands_rotate_pos20deg | 81.162 | both_hands_rotate_pos45deg_diagnostic | 70.000 |
| 跳 | PASS | 84.409 | both_hands_rotate_neg20deg | 81.149 | both_hands_rotate_pos45deg_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | normalized_distance | alignment | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---:|---|---|---|---|
| both_hands_rotate_pos45deg_diagnostic | diagnostic | DIAG | 81.162 | diagnostic | 0.030264 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 双手极端反向局部旋转，只记录诊断边界。 |
| both_hands_rotate_neg45deg_diagnostic | diagnostic | DIAG | 81.204 | diagnostic | 0.030190 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 双手极端局部旋转，只记录诊断边界。 |
| right_hand_rotate_pos30deg_diagnostic | diagnostic | DIAG | 81.269 | diagnostic | 0.030074 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 右手较强反向局部旋转，只记录诊断边界。 |
| right_hand_rotate_neg30deg_diagnostic | diagnostic | DIAG | 81.299 | diagnostic | 0.030020 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 右手较强局部旋转，只记录诊断边界。 |
| both_hands_rotate_pos20deg | positive | PASS | 81.336 | >= 70.0 | 0.029954 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 双手局部顺时针约 20 度，模拟较明显但仍自然的手腕角度差异。 |
| both_hands_rotate_neg20deg | positive | PASS | 81.357 | >= 70.0 | 0.029917 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 双手局部逆时针约 20 度，模拟较明显但仍自然的手腕角度差异。 |
| right_hand_rotate_pos15deg | positive | PASS | 81.368 | >= 70.0 | 0.029897 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 右手核心手腕角度轻微反向偏差。 |
| right_hand_rotate_neg15deg | positive | PASS | 81.382 | >= 70.0 | 0.029873 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 右手核心手腕角度轻微偏差。 |
| both_hands_rotate_pos10deg | positive | PASS | 81.399 | >= 70.0 | 0.029842 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 双手局部顺时针约 10 度，手语语义顺序和角色保持。 |
| both_hands_rotate_neg10deg | positive | PASS | 81.406 | >= 70.0 | 0.029830 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 双手局部逆时针约 10 度，手语语义顺序和角色保持。 |
| self | positive | PASS | 100.000 | >= 95.0 | 0.000000 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 同一骨架重算基线。 |
| left_hand_rotate_neg15deg | positive | PASS | 100.000 | >= 70.0 | 0.000000 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 左手局部角度轻微偏差。 |
| left_hand_rotate_pos15deg | positive | PASS | 100.000 | >= 70.0 | 0.000000 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 左手局部角度轻微反向偏差。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | normalized_distance | alignment | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---:|---|---|---|---|
| both_hands_rotate_pos45deg_diagnostic | diagnostic | DIAG | 81.149 | diagnostic | 0.095937 | semantic_action_window | score_valid | action_window_net | 双手极端反向局部旋转，只记录诊断边界。 |
| both_hands_rotate_neg45deg_diagnostic | diagnostic | DIAG | 81.859 | diagnostic | 0.109898 | semantic_action_window | score_valid | action_window_net | 双手极端局部旋转，只记录诊断边界。 |
| right_hand_rotate_neg30deg_diagnostic | diagnostic | DIAG | 87.135 | diagnostic | 0.034461 | semantic_action_window | score_valid | action_window_net | 右手较强局部旋转，只记录诊断边界。 |
| right_hand_rotate_pos30deg_diagnostic | diagnostic | DIAG | 89.032 | diagnostic | 0.029449 | semantic_action_window | score_valid | action_window_net | 右手较强反向局部旋转，只记录诊断边界。 |
| both_hands_rotate_neg20deg | positive | PASS | 84.409 | >= 70.0 | 0.042932 | semantic_action_window | score_valid | action_window_net | 双手局部逆时针约 20 度，模拟较明显但仍自然的手腕角度差异。 |
| both_hands_rotate_pos20deg | positive | PASS | 85.342 | >= 70.0 | 0.040120 | semantic_action_window | score_valid | action_window_net | 双手局部顺时针约 20 度，模拟较明显但仍自然的手腕角度差异。 |
| both_hands_rotate_neg10deg | positive | PASS | 92.081 | >= 70.0 | 0.020968 | semantic_action_window | score_valid | action_window_net | 双手局部逆时针约 10 度，手语语义顺序和角色保持。 |
| both_hands_rotate_pos10deg | positive | PASS | 92.330 | >= 70.0 | 0.020198 | semantic_action_window | score_valid | action_window_net | 双手局部顺时针约 10 度，手语语义顺序和角色保持。 |
| right_hand_rotate_neg15deg | positive | PASS | 93.688 | >= 70.0 | 0.016402 | semantic_action_window | score_valid | action_window_net | 右手核心手腕角度轻微偏差。 |
| left_hand_rotate_neg15deg | positive | PASS | 93.892 | >= 70.0 | 0.016049 | semantic_action_window | score_valid | action_window_net | 左手局部角度轻微偏差。 |
| left_hand_rotate_pos15deg | positive | PASS | 93.979 | >= 70.0 | 0.015816 | semantic_action_window | score_valid | action_window_net | 左手局部角度轻微反向偏差。 |
| right_hand_rotate_pos15deg | positive | PASS | 94.169 | >= 70.0 | 0.015151 | semantic_action_window | score_valid | action_window_net | 右手核心手腕角度轻微反向偏差。 |
| self | positive | PASS | 100.000 | >= 95.0 | 0.000000 | semantic_action_window | score_valid | action_window_net | 同一骨架重算基线。 |

## 说明

- 正向扰动覆盖常见手腕角度偏差，并强制重算派生手形特征。
- 极端旋转不作为硬门，避免把真实语义方向变化错误推广为正常采集。
- 该门是合成鲁棒性压力测试，不能替代真实网页摄像头样本。

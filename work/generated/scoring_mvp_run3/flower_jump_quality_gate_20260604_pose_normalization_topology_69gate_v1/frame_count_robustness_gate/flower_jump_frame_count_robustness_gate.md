# 花/跳帧数与采样密度鲁棒性门

- 生成时间：`2026-06-04T12:50:51`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，在骨架序列层面重采样，不调用 `/api/score`，不重启 Holistic。
- 目标：验证 `花/跳` 在推荐有效帧数内的稀疏/密集抽样和非均匀时间覆盖下仍保持正常或边界以上得分；低于推荐帧数的变体仅作为欠采样风险诊断。

- 5080 状态：worker=`ready`，worker_pid=`811485`，reload_count=`25`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`
- 变体最低分门槛：`70.0`

| 目标词 | 状态 | 标准帧数 | 推荐最少帧 | 门控最低分 | 最弱门控采样 | 欠采样最低分 |
|---|---|---:|---:|---:|---|---:|
| 花 | PASS | 53 | 12 | 78.482 | uniform_12f | 32.284 |
| 跳 | PASS | 19 | 6 | 70.488 | drop_every_3_keep_ends | - |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`
- gate：`PASS`
- 推荐最少帧：`12`
- 门控最低分：`78.482`，最弱门控采样：`uniform_12f`
- 欠采样诊断最低分：`32.284`，欠采样变体：`uniform_8f`

| 采样变体 | 分数 | query 帧数 | 门控 | 长度比 | normalized_distance | alignment | quality | floor |
|---|---:|---:|---|---:|---:|---|---|---|
| uniform_8f | 32.284 | 8 | undersampled | 0.15 | 0.135672 | {'mode': 'full_sequence_with_action_window_diagnostics', 'used_action_window_for_scoring': False, 'reason': 'long_or_context_sensitive_action_keep_full_sequence', 'word': '花', 'standard_full_length': 53, 'standard_action_length': 15, 'standard_action_ratio': 0.2830188679245283} | semantic_mismatch | short_visible_core |
| uniform_12f | 78.482 | 12 | yes | 0.23 | 0.086707 | {'mode': 'full_sequence_with_action_window_diagnostics', 'used_action_window_for_scoring': False, 'reason': 'long_or_context_sensitive_action_keep_full_sequence', 'word': '花', 'standard_full_length': 53, 'standard_action_length': 15, 'standard_action_ratio': 0.2830188679245283} | score_valid | short_visible_core |
| front_dense_16f | 92.509 | 16 | yes | 0.30 | 0.027014 | {'mode': 'full_sequence_with_action_window_diagnostics', 'used_action_window_for_scoring': False, 'reason': 'long_or_context_sensitive_action_keep_full_sequence', 'word': '花', 'standard_full_length': 53, 'standard_action_length': 15, 'standard_action_ratio': 0.2830188679245283} | score_valid | short_visible_core |
| back_dense_16f | 93.569 | 16 | yes | 0.30 | 0.023722 | {'mode': 'full_sequence_with_action_window_diagnostics', 'used_action_window_for_scoring': False, 'reason': 'long_or_context_sensitive_action_keep_full_sequence', 'word': '花', 'standard_full_length': 53, 'standard_action_length': 15, 'standard_action_ratio': 0.2830188679245283} | score_valid | short_visible_core |
| repeat_mid_core | 94.018 | 21 | yes | 0.40 | 0.023463 | {'mode': 'full_sequence_with_action_window_diagnostics', 'used_action_window_for_scoring': False, 'reason': 'long_or_context_sensitive_action_keep_full_sequence', 'word': '花', 'standard_full_length': 53, 'standard_action_length': 15, 'standard_action_ratio': 0.2830188679245283} | score_valid | short_visible_core |
| uniform_17f | 94.065 | 17 | yes | 0.32 | 0.023556 | {'mode': 'full_sequence_with_action_window_diagnostics', 'used_action_window_for_scoring': False, 'reason': 'long_or_context_sensitive_action_keep_full_sequence', 'word': '花', 'standard_full_length': 53, 'standard_action_length': 15, 'standard_action_ratio': 0.2830188679245283} | score_valid | short_visible_core |
| uniform_16f | 94.273 | 16 | yes | 0.30 | 0.023300 | {'mode': 'full_sequence_with_action_window_diagnostics', 'used_action_window_for_scoring': False, 'reason': 'long_or_context_sensitive_action_keep_full_sequence', 'word': '花', 'standard_full_length': 53, 'standard_action_length': 15, 'standard_action_ratio': 0.2830188679245283} | score_valid | short_visible_core |
| front_dense_24f | 94.313 | 24 | yes | 0.45 | 0.021072 | {'mode': 'full_sequence_with_action_window_diagnostics', 'used_action_window_for_scoring': False, 'reason': 'long_or_context_sensitive_action_keep_full_sequence', 'word': '花', 'standard_full_length': 53, 'standard_action_length': 15, 'standard_action_ratio': 0.2830188679245283} | score_valid | short_visible_core |
| drop_every_3_keep_ends | 94.685 | 19 | yes | 0.36 | 0.021328 | {'mode': 'full_sequence_with_action_window_diagnostics', 'used_action_window_for_scoring': False, 'reason': 'long_or_context_sensitive_action_keep_full_sequence', 'word': '花', 'standard_full_length': 53, 'standard_action_length': 15, 'standard_action_ratio': 0.2830188679245283} | score_valid | short_visible_core |
| back_dense_24f | 95.070 | 24 | yes | 0.45 | 0.017912 | {'mode': 'full_sequence_with_action_window_diagnostics', 'used_action_window_for_scoring': False, 'reason': 'long_or_context_sensitive_action_keep_full_sequence', 'word': '花', 'standard_full_length': 53, 'standard_action_length': 15, 'standard_action_ratio': 0.2830188679245283} | score_valid | short_visible_core |
| uniform_32f | 95.168 | 32 | yes | 0.60 | 0.015248 | {'mode': 'full_sequence_with_action_window_diagnostics', 'used_action_window_for_scoring': False, 'reason': 'long_or_context_sensitive_action_keep_full_sequence', 'word': '花', 'standard_full_length': 53, 'standard_action_length': 15, 'standard_action_ratio': 0.2830188679245283} | score_valid | short_visible_core |
| uniform_26f | 95.544 | 26 | yes | 0.49 | 0.016823 | {'mode': 'full_sequence_with_action_window_diagnostics', 'used_action_window_for_scoring': False, 'reason': 'long_or_context_sensitive_action_keep_full_sequence', 'word': '花', 'standard_full_length': 53, 'standard_action_length': 15, 'standard_action_ratio': 0.2830188679245283} | score_valid | short_visible_core |
| uniform_24f | 95.700 | 24 | yes | 0.45 | 0.017350 | {'mode': 'full_sequence_with_action_window_diagnostics', 'used_action_window_for_scoring': False, 'reason': 'long_or_context_sensitive_action_keep_full_sequence', 'word': '花', 'standard_full_length': 53, 'standard_action_length': 15, 'standard_action_ratio': 0.2830188679245283} | score_valid | short_visible_core |
| drop_every_2_keep_ends | 95.777 | 27 | yes | 0.51 | 0.016265 | {'mode': 'full_sequence_with_action_window_diagnostics', 'used_action_window_for_scoring': False, 'reason': 'long_or_context_sensitive_action_keep_full_sequence', 'word': '花', 'standard_full_length': 53, 'standard_action_length': 15, 'standard_action_ratio': 0.2830188679245283} | score_valid | short_visible_core |
| uniform_80f | 97.376 | 80 | yes | 1.51 | 0.003982 | {'mode': 'full_sequence_with_action_window_diagnostics', 'used_action_window_for_scoring': False, 'reason': 'long_or_context_sensitive_action_keep_full_sequence', 'word': '花', 'standard_full_length': 53, 'standard_action_length': 15, 'standard_action_ratio': 0.2830188679245283} | score_valid | short_visible_core |
| uniform_48f | 97.898 | 48 | yes | 0.91 | 0.005149 | {'mode': 'full_sequence_with_action_window_diagnostics', 'used_action_window_for_scoring': False, 'reason': 'long_or_context_sensitive_action_keep_full_sequence', 'word': '花', 'standard_full_length': 53, 'standard_action_length': 15, 'standard_action_ratio': 0.2830188679245283} | score_valid | short_visible_core |
| uniform_106f | 99.588 | 106 | yes | 2.00 | 0.000708 | {'mode': 'full_sequence_with_action_window_diagnostics', 'used_action_window_for_scoring': False, 'reason': 'long_or_context_sensitive_action_keep_full_sequence', 'word': '花', 'standard_full_length': 53, 'standard_action_length': 15, 'standard_action_ratio': 0.2830188679245283} | score_valid | short_visible_core |
| self | 100.000 | 53 | yes | 1.00 | 0.000000 | {'mode': 'full_sequence_with_action_window_diagnostics', 'used_action_window_for_scoring': False, 'reason': 'long_or_context_sensitive_action_keep_full_sequence', 'word': '花', 'standard_full_length': 53, 'standard_action_length': 15, 'standard_action_ratio': 0.2830188679245283} | score_valid | short_visible_core |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`
- gate：`PASS`
- 推荐最少帧：`6`
- 门控最低分：`70.488`，最弱门控采样：`drop_every_3_keep_ends`

| 采样变体 | 分数 | query 帧数 | 门控 | 长度比 | normalized_distance | alignment | quality | floor |
|---|---:|---:|---|---:|---:|---|---|---|
| drop_every_3_keep_ends | 70.488 | 8 | yes | 0.42 | 0.098559 | {'mode': 'semantic_action_window', 'used_action_window_for_scoring': True, 'reason': 'short_standard_action_window', 'word': '跳', 'standard_full_length': 19, 'standard_action_length': 9, 'standard_action_ratio': 0.47368421052631576} | score_valid | action_window_net |
| uniform_80f | 74.962 | 80 | yes | 4.21 | 0.104526 | {'mode': 'semantic_action_window', 'used_action_window_for_scoring': True, 'reason': 'short_standard_action_window', 'word': '跳', 'standard_full_length': 19, 'standard_action_length': 9, 'standard_action_ratio': 0.47368421052631576} | score_valid | action_window_net |
| uniform_32f | 76.364 | 32 | yes | 1.68 | 0.170808 | {'mode': 'semantic_action_window', 'used_action_window_for_scoring': True, 'reason': 'short_standard_action_window', 'word': '跳', 'standard_full_length': 19, 'standard_action_length': 9, 'standard_action_ratio': 0.47368421052631576} | score_valid | full_sequence_local_relation_segment |
| uniform_24f | 77.682 | 24 | yes | 1.26 | 0.075205 | {'mode': 'semantic_action_window', 'used_action_window_for_scoring': True, 'reason': 'short_standard_action_window', 'word': '跳', 'standard_full_length': 19, 'standard_action_length': 9, 'standard_action_ratio': 0.47368421052631576} | score_valid | full_sequence_local_relation_segment |
| uniform_9f | 77.693 | 9 | yes | 0.47 | 0.061749 | {'mode': 'semantic_action_window', 'used_action_window_for_scoring': True, 'reason': 'short_standard_action_window', 'word': '跳', 'standard_full_length': 19, 'standard_action_length': 9, 'standard_action_ratio': 0.47368421052631576} | score_valid | action_window_net |
| repeat_mid_core | 78.187 | 14 | yes | 0.74 | 0.085703 | {'mode': 'semantic_action_window', 'used_action_window_for_scoring': True, 'reason': 'short_standard_action_window', 'word': '跳', 'standard_full_length': 19, 'standard_action_length': 9, 'standard_action_ratio': 0.47368421052631576} | score_valid | action_window_net |
| uniform_16f | 78.767 | 16 | yes | 0.84 | 0.058111 | {'mode': 'semantic_action_window', 'used_action_window_for_scoring': True, 'reason': 'short_standard_action_window', 'word': '跳', 'standard_full_length': 19, 'standard_action_length': 9, 'standard_action_ratio': 0.47368421052631576} | score_valid | action_window_net |
| uniform_38f | 79.124 | 38 | yes | 2.00 | 0.050303 | {'mode': 'semantic_action_window', 'used_action_window_for_scoring': True, 'reason': 'short_standard_action_window', 'word': '跳', 'standard_full_length': 19, 'standard_action_length': 9, 'standard_action_ratio': 0.47368421052631576} | score_valid | action_window_net |
| front_dense_24f | 80.767 | 24 | yes | 1.26 | 0.051769 | {'mode': 'semantic_action_window', 'used_action_window_for_scoring': True, 'reason': 'short_standard_action_window', 'word': '跳', 'standard_full_length': 19, 'standard_action_length': 9, 'standard_action_ratio': 0.47368421052631576} | score_valid | action_window_net |
| drop_every_2_keep_ends | 81.486 | 10 | yes | 0.53 | 0.046296 | {'mode': 'semantic_action_window', 'used_action_window_for_scoring': True, 'reason': 'short_standard_action_window', 'word': '跳', 'standard_full_length': 19, 'standard_action_length': 9, 'standard_action_ratio': 0.47368421052631576} | score_valid | action_window_net |
| uniform_48f | 81.528 | 48 | yes | 2.53 | 0.043671 | {'mode': 'semantic_action_window', 'used_action_window_for_scoring': True, 'reason': 'short_standard_action_window', 'word': '跳', 'standard_full_length': 19, 'standard_action_length': 9, 'standard_action_ratio': 0.47368421052631576} | score_valid | action_window_net |
| uniform_8f | 82.100 | 8 | yes | 0.42 | 0.056003 | {'mode': 'semantic_action_window', 'used_action_window_for_scoring': True, 'reason': 'short_standard_action_window', 'word': '跳', 'standard_full_length': 19, 'standard_action_length': 9, 'standard_action_ratio': 0.47368421052631576} | score_valid | action_window_net |
| uniform_6f | 82.538 | 6 | yes | 0.32 | 0.266416 | {'mode': 'semantic_action_window', 'used_action_window_for_scoring': True, 'reason': 'short_standard_action_window', 'word': '跳', 'standard_full_length': 19, 'standard_action_length': 9, 'standard_action_ratio': 0.47368421052631576} | score_valid | full_sequence_local_relation_segment |
| uniform_12f | 84.444 | 12 | yes | 0.63 | 0.048135 | {'mode': 'semantic_action_window', 'used_action_window_for_scoring': True, 'reason': 'short_standard_action_window', 'word': '跳', 'standard_full_length': 19, 'standard_action_length': 9, 'standard_action_ratio': 0.47368421052631576} | score_valid | action_window_net |
| back_dense_16f | 84.444 | 16 | yes | 0.84 | 0.043357 | {'mode': 'semantic_action_window', 'used_action_window_for_scoring': True, 'reason': 'short_standard_action_window', 'word': '跳', 'standard_full_length': 19, 'standard_action_length': 9, 'standard_action_ratio': 0.47368421052631576} | score_valid | action_window_net |
| front_dense_16f | 86.046 | 16 | yes | 0.84 | 0.032022 | {'mode': 'semantic_action_window', 'used_action_window_for_scoring': True, 'reason': 'short_standard_action_window', 'word': '跳', 'standard_full_length': 19, 'standard_action_length': 9, 'standard_action_ratio': 0.47368421052631576} | score_valid | action_window_net |
| back_dense_24f | 96.217 | 24 | yes | 1.26 | 0.006662 | {'mode': 'semantic_action_window', 'used_action_window_for_scoring': True, 'reason': 'short_standard_action_window', 'word': '跳', 'standard_full_length': 19, 'standard_action_length': 9, 'standard_action_ratio': 0.47368421052631576} | score_valid | action_window_net |
| self | 100.000 | 19 | yes | 1.00 | 0.000000 | {'mode': 'semantic_action_window', 'used_action_window_for_scoring': True, 'reason': 'short_standard_action_window', 'word': '跳', 'standard_full_length': 19, 'standard_action_length': 9, 'standard_action_ratio': 0.47368421052631576} | score_valid | action_window_net |

## 说明

- 该门关注同一语义动作在推荐帧数内的采样差异，不代表所有真实用户动作都会通过；真实网页摄像头样本仍需要 watcher 增量诊断。
- 当前推荐：`花` 至少 12 个有效骨架帧，`跳` 至少 6 个有效骨架帧；前端实际采集仍建议 3 秒、约 24-36 帧，以抵消 Holistic 缺帧和手部遮挡。
- 若该门失败，优先检查语义相位、start/mid/end 锚点、短视频核心段 floor、opening guard 与 two-hand relation fallback 对帧数变化的兼容性。

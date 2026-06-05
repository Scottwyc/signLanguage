# 花/跳坐姿与镜头扰动鲁棒性门

- 生成时间：`2026-06-04T19:18:58`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，基于标准骨架生成正例扰动，不调用 `/api/score`，不重启 Holistic。
- 目标：验证坐姿、镜头位置、手部局部尺度、轻微旋转和手指小抖动不会压垮 `花/跳` 的核心语义得分。

- 5080 状态：worker=`ready`，worker_pid=`811485`，reload_count=`31`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`
- 变体最低分门槛：`70.0`

| 目标词 | 状态 | 最低分 | 最弱扰动 | 标准帧数 |
|---|---|---:|---|---:|
| 花 | PASS | 80.446 | hand_jitter_small | 53 |
| 跳 | PASS | 93.015 | hand_jitter_small | 19 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`
- gate：`PASS`
- 最低分：`80.446`，最弱扰动：`hand_jitter_small`

| 扰动 | 分数 | normalized_distance | alignment | capture_quality | semantic_floor |
|---|---:|---:|---|---|---|
| hand_jitter_small | 80.446 | 0.031549 | {'mode': 'full_sequence_with_action_window_diagnostics', 'used_action_window_for_scoring': False, 'reason': 'long_or_context_sensitive_action_keep_full_sequence', 'word': '花', 'standard_full_length': 53, 'standard_action_length': 15, 'standard_action_ratio': 0.2830188679245283} | score_valid | short_visible_core |
| hand_local_scale_1.10 | 81.303 | 0.030013 | {'mode': 'full_sequence_with_action_window_diagnostics', 'used_action_window_for_scoring': False, 'reason': 'long_or_context_sensitive_action_keep_full_sequence', 'word': '花', 'standard_full_length': 53, 'standard_action_length': 15, 'standard_action_ratio': 0.2830188679245283} | score_valid | short_visible_core |
| hand_local_scale_0.90 | 81.320 | 0.029983 | {'mode': 'full_sequence_with_action_window_diagnostics', 'used_action_window_for_scoring': False, 'reason': 'long_or_context_sensitive_action_keep_full_sequence', 'word': '花', 'standard_full_length': 53, 'standard_action_length': 15, 'standard_action_ratio': 0.2830188679245283} | score_valid | short_visible_core |
| hands_rotate_10deg | 81.426 | 0.029794 | {'mode': 'full_sequence_with_action_window_diagnostics', 'used_action_window_for_scoring': False, 'reason': 'long_or_context_sensitive_action_keep_full_sequence', 'word': '花', 'standard_full_length': 53, 'standard_action_length': 15, 'standard_action_ratio': 0.2830188679245283} | score_valid | short_visible_core |
| hands_shift_left | 81.457 | 0.029739 | {'mode': 'full_sequence_with_action_window_diagnostics', 'used_action_window_for_scoring': False, 'reason': 'long_or_context_sensitive_action_keep_full_sequence', 'word': '花', 'standard_full_length': 53, 'standard_action_length': 15, 'standard_action_ratio': 0.2830188679245283} | score_valid | short_visible_core |
| hands_shift_down | 81.457 | 0.029739 | {'mode': 'full_sequence_with_action_window_diagnostics', 'used_action_window_for_scoring': False, 'reason': 'long_or_context_sensitive_action_keep_full_sequence', 'word': '花', 'standard_full_length': 53, 'standard_action_length': 15, 'standard_action_ratio': 0.2830188679245283} | score_valid | short_visible_core |
| whole_person_shift | 81.457 | 0.029739 | {'mode': 'full_sequence_with_action_window_diagnostics', 'used_action_window_for_scoring': False, 'reason': 'long_or_context_sensitive_action_keep_full_sequence', 'word': '花', 'standard_full_length': 53, 'standard_action_length': 15, 'standard_action_ratio': 0.2830188679245283} | score_valid | short_visible_core |
| hands_shift_diag | 81.457 | 0.029739 | {'mode': 'full_sequence_with_action_window_diagnostics', 'used_action_window_for_scoring': False, 'reason': 'long_or_context_sensitive_action_keep_full_sequence', 'word': '花', 'standard_full_length': 53, 'standard_action_length': 15, 'standard_action_ratio': 0.2830188679245283} | score_valid | short_visible_core |
| self | 100.000 | 0.000000 | {'mode': 'full_sequence_with_action_window_diagnostics', 'used_action_window_for_scoring': False, 'reason': 'long_or_context_sensitive_action_keep_full_sequence', 'word': '花', 'standard_full_length': 53, 'standard_action_length': 15, 'standard_action_ratio': 0.2830188679245283} | score_valid | short_visible_core |
| pose_sitting_compress | 100.000 | 0.000000 | {'mode': 'full_sequence_with_action_window_diagnostics', 'used_action_window_for_scoring': False, 'reason': 'long_or_context_sensitive_action_keep_full_sequence', 'word': '花', 'standard_full_length': 53, 'standard_action_length': 15, 'standard_action_ratio': 0.2830188679245283} | score_valid | short_visible_core |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`
- gate：`PASS`
- 最低分：`93.015`，最弱扰动：`hand_jitter_small`

| 扰动 | 分数 | normalized_distance | alignment | capture_quality | semantic_floor |
|---|---:|---:|---|---|---|
| hand_jitter_small | 93.015 | 0.016105 | {'mode': 'semantic_action_window', 'used_action_window_for_scoring': True, 'reason': 'short_standard_action_window', 'word': '跳', 'standard_full_length': 19, 'standard_action_length': 9, 'standard_action_ratio': 0.47368421052631576} | score_valid | action_window_net |
| whole_person_shift | 93.296 | 0.017813 | {'mode': 'semantic_action_window', 'used_action_window_for_scoring': True, 'reason': 'short_standard_action_window', 'word': '跳', 'standard_full_length': 19, 'standard_action_length': 9, 'standard_action_ratio': 0.47368421052631576} | score_valid | action_window_net |
| hands_shift_diag | 93.338 | 0.017698 | {'mode': 'semantic_action_window', 'used_action_window_for_scoring': True, 'reason': 'short_standard_action_window', 'word': '跳', 'standard_full_length': 19, 'standard_action_length': 9, 'standard_action_ratio': 0.47368421052631576} | score_valid | action_window_net |
| hands_shift_down | 93.525 | 0.017186 | {'mode': 'semantic_action_window', 'used_action_window_for_scoring': True, 'reason': 'short_standard_action_window', 'word': '跳', 'standard_full_length': 19, 'standard_action_length': 9, 'standard_action_ratio': 0.47368421052631576} | score_valid | action_window_net |
| hands_shift_left | 93.525 | 0.017186 | {'mode': 'semantic_action_window', 'used_action_window_for_scoring': True, 'reason': 'short_standard_action_window', 'word': '跳', 'standard_full_length': 19, 'standard_action_length': 9, 'standard_action_ratio': 0.47368421052631576} | score_valid | action_window_net |
| hands_rotate_10deg | 95.841 | 0.010718 | {'mode': 'semantic_action_window', 'used_action_window_for_scoring': True, 'reason': 'short_standard_action_window', 'word': '跳', 'standard_full_length': 19, 'standard_action_length': 9, 'standard_action_ratio': 0.47368421052631576} | score_valid | action_window_net |
| hand_local_scale_0.90 | 97.578 | 0.006068 | {'mode': 'semantic_action_window', 'used_action_window_for_scoring': True, 'reason': 'short_standard_action_window', 'word': '跳', 'standard_full_length': 19, 'standard_action_length': 9, 'standard_action_ratio': 0.47368421052631576} | score_valid | action_window_net |
| hand_local_scale_1.10 | 97.665 | 0.005860 | {'mode': 'semantic_action_window', 'used_action_window_for_scoring': True, 'reason': 'short_standard_action_window', 'word': '跳', 'standard_full_length': 19, 'standard_action_length': 9, 'standard_action_ratio': 0.47368421052631576} | score_valid | action_window_net |
| self | 100.000 | 0.000000 | {'mode': 'semantic_action_window', 'used_action_window_for_scoring': True, 'reason': 'short_standard_action_window', 'word': '跳', 'standard_full_length': 19, 'standard_action_length': 9, 'standard_action_ratio': 0.47368421052631576} | score_valid | action_window_net |
| pose_sitting_compress | 100.000 | 0.000000 | {'mode': 'semantic_action_window', 'used_action_window_for_scoring': True, 'reason': 'short_standard_action_window', 'word': '跳', 'standard_full_length': 19, 'standard_action_length': 9, 'standard_action_ratio': 0.47368421052631576} | score_valid | action_window_net |

## 说明

- 本门只验证核心语义对非关键姿态扰动的稳定性，不替代真实摄像头样本。
- 若该门失败，优先检查 profile 中 `pose/face` 权重、`hand_global_position_weight`、以及手部局部几何和 two-hand relation 的相对特征是否被全局位置主导。

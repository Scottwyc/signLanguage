# 花/跳 landmark 噪声鲁棒性门

- 生成时间：`2026-06-03T12:41:49`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，在手部 landmark 坐标和 mask 层面合成小幅抖动/少量不稳定，并重算手形特征；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：小幅连续 landmark 抖动和稀少整帧手部不稳定仍能保持正常/边界分；更强噪声和逐点丢失只作为诊断边界。

- 5080 状态：worker=`ready`，worker_pid=`811485`，reload_count=`14`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向噪声 | 诊断最低分 | 最弱诊断噪声 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 76.064 | hand_noise_0.010_seed2 | 11.118 | severe_shuffle_diagnostic | 70.000 |
| 跳 | PASS | 72.810 | hand_noise_0.010_seed1 | 8.825 | severe_point_dropout_0.25_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | normalized_distance | alignment | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---:|---|---|---|---|
| severe_shuffle_diagnostic | diagnostic | DIAG | 11.118 | diagnostic | 0.263592 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 严重手部 landmark 顺序破坏，应表现为低分或语义失败。 |
| severe_noise_0.060_diagnostic | diagnostic | DIAG | 23.137 | diagnostic | 0.175649 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 严重坐标抖动，作为不可接受噪声边界。 |
| hand_noise_0.015_diagnostic | diagnostic | DIAG | 68.135 | diagnostic | 0.055634 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 更强坐标抖动，作为边界诊断。 |
| severe_point_dropout_0.25_diagnostic | diagnostic | DIAG | 89.290 | diagnostic | 0.031109 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 严重逐点随机丢失，作为重采/语义失败边界。 |
| hand_point_dropout_0.05_diagnostic | diagnostic | DIAG | 96.687 | diagnostic | 0.011360 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 逐点随机丢失会破坏手形/相位，作为诊断而非正向门。 |
| hand_frame_dropout_0.05_diagnostic | diagnostic | DIAG | 98.429 | diagnostic | 0.002781 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 更高整帧手部缺失率，作为重采边界诊断。 |
| hand_noise_0.010_seed2 | positive | PASS | 76.064 | >= 70.0 | 0.039672 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 小幅连续 hand landmark 坐标抖动，重算手形特征。 |
| hand_noise_0.010_seed5 | positive | PASS | 76.248 | >= 70.0 | 0.039320 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 小幅连续 hand landmark 坐标抖动，重算手形特征。 |
| hand_noise_0.010_seed3 | positive | PASS | 76.596 | >= 70.0 | 0.038660 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 小幅连续 hand landmark 坐标抖动，重算手形特征。 |
| hand_noise_0.010_seed1 | positive | PASS | 76.727 | >= 70.0 | 0.038413 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 小幅连续 hand landmark 坐标抖动，重算手形特征。 |
| hand_noise_0.010_seed4 | positive | PASS | 77.153 | >= 70.0 | 0.037609 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 小幅连续 hand landmark 坐标抖动，重算手形特征。 |
| hand_frame_dropout_0.03_seed7 | positive | PASS | 98.369 | >= 70.0 | 0.003622 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 少量整帧手部检出不稳定，属于可容忍的网页采集噪声。 |
| hand_frame_dropout_0.03_seed6 | positive | PASS | 98.440 | >= 70.0 | 0.002892 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 少量整帧手部检出不稳定，属于可容忍的网页采集噪声。 |
| hand_frame_dropout_0.03_seed1 | positive | PASS | 98.599 | >= 70.0 | 0.002589 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 少量整帧手部检出不稳定，属于可容忍的网页采集噪声。 |
| hand_frame_dropout_0.03_seed5 | positive | PASS | 98.885 | >= 70.0 | 0.002333 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 少量整帧手部检出不稳定，属于可容忍的网页采集噪声。 |
| hand_frame_dropout_0.03_seed3 | positive | PASS | 99.224 | >= 70.0 | 0.001372 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 少量整帧手部检出不稳定，属于可容忍的网页采集噪声。 |
| hand_frame_dropout_0.03_seed2 | positive | PASS | 100.000 | >= 70.0 | 0.000000 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 少量整帧手部检出不稳定，属于可容忍的网页采集噪声。 |
| hand_frame_dropout_0.03_seed4 | positive | PASS | 100.000 | >= 70.0 | 0.000000 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 少量整帧手部检出不稳定，属于可容忍的网页采集噪声。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | normalized_distance | alignment | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---:|---|---|---|---|
| severe_point_dropout_0.25_diagnostic | diagnostic | DIAG | 8.825 | diagnostic | 0.411966 | semantic_action_window | semantic_mismatch | action_window_net | 严重逐点随机丢失，作为重采/语义失败边界。 |
| severe_noise_0.060_diagnostic | diagnostic | DIAG | 71.516 | diagnostic | 0.285732 | semantic_action_window | score_valid | action_window_net | 严重坐标抖动，作为不可接受噪声边界。 |
| severe_shuffle_diagnostic | diagnostic | DIAG | 76.323 | diagnostic | 0.309733 | semantic_action_window | score_valid | action_window_net | 严重手部 landmark 顺序破坏，应表现为低分或语义失败。 |
| hand_point_dropout_0.05_diagnostic | diagnostic | DIAG | 76.758 | diagnostic | 0.125118 | semantic_action_window | score_valid | full_sequence_local_relation_segment | 逐点随机丢失会破坏手形/相位，作为诊断而非正向门。 |
| hand_noise_0.015_diagnostic | diagnostic | DIAG | 82.263 | diagnostic | 0.058104 | semantic_action_window | score_valid | action_window_net | 更强坐标抖动，作为边界诊断。 |
| hand_frame_dropout_0.05_diagnostic | diagnostic | DIAG | 99.684 | diagnostic | 0.000588 | semantic_action_window | score_valid | action_window_net | 更高整帧手部缺失率，作为重采边界诊断。 |
| hand_noise_0.010_seed1 | positive | PASS | 72.810 | >= 70.0 | 0.106389 | semantic_action_window | score_valid | action_window_net | 小幅连续 hand landmark 坐标抖动，重算手形特征。 |
| hand_noise_0.010_seed4 | positive | PASS | 75.893 | >= 70.0 | 0.062936 | semantic_action_window | score_valid | full_sequence_local_relation_segment | 小幅连续 hand landmark 坐标抖动，重算手形特征。 |
| hand_frame_dropout_0.03_seed6 | positive | PASS | 78.545 | >= 70.0 | 0.148103 | semantic_action_window | score_valid | full_sequence_local_relation_segment | 少量整帧手部检出不稳定，属于可容忍的网页采集噪声。 |
| hand_frame_dropout_0.03_seed7 | positive | PASS | 79.251 | >= 70.0 | 0.055327 | semantic_action_window | score_valid | action_window_net | 少量整帧手部检出不稳定，属于可容忍的网页采集噪声。 |
| hand_noise_0.010_seed2 | positive | PASS | 84.244 | >= 70.0 | 0.040408 | semantic_action_window | score_valid | action_window_net | 小幅连续 hand landmark 坐标抖动，重算手形特征。 |
| hand_noise_0.010_seed3 | positive | PASS | 85.665 | >= 70.0 | 0.036552 | semantic_action_window | score_valid | action_window_net | 小幅连续 hand landmark 坐标抖动，重算手形特征。 |
| hand_noise_0.010_seed5 | positive | PASS | 86.077 | >= 70.0 | 0.035394 | semantic_action_window | score_valid | action_window_net | 小幅连续 hand landmark 坐标抖动，重算手形特征。 |
| hand_frame_dropout_0.03_seed1 | positive | PASS | 89.463 | >= 70.0 | 0.022763 | semantic_action_window | score_valid | action_window_net | 少量整帧手部检出不稳定，属于可容忍的网页采集噪声。 |
| hand_frame_dropout_0.03_seed3 | positive | PASS | 99.699 | >= 70.0 | 0.000548 | semantic_action_window | score_valid | action_window_net | 少量整帧手部检出不稳定，属于可容忍的网页采集噪声。 |
| hand_frame_dropout_0.03_seed5 | positive | PASS | 99.722 | >= 70.0 | 0.000487 | semantic_action_window | score_valid | action_window_net | 少量整帧手部检出不稳定，属于可容忍的网页采集噪声。 |
| hand_frame_dropout_0.03_seed2 | positive | PASS | 100.000 | >= 70.0 | 0.000000 | semantic_action_window | score_valid | action_window_net | 少量整帧手部检出不稳定，属于可容忍的网页采集噪声。 |
| hand_frame_dropout_0.03_seed4 | positive | PASS | 100.000 | >= 70.0 | 0.000000 | semantic_action_window | score_valid | action_window_net | 少量整帧手部检出不稳定，属于可容忍的网页采集噪声。 |

## 说明

- 正向噪声只覆盖小幅坐标抖动和稀少整帧手部检出不稳定；逐点随机丢失会破坏手形和相位，不能当作正常采集通过。
- 该门是合成 landmark 压力测试，不能替代正式网页摄像头样本。

# 花/跳 z/depth 深度鲁棒性门

- 生成时间：`2026-06-04T13:47:43`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，在骨架 z 坐标层面模拟深度偏移、缩放和噪声；手部 z 改动会重算 hand-shape 特征；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：不同摄像头/距离导致 Holistic 深度漂移时，`花/跳` 仍主要由 2D 手形、相位和双手关系决定。

- 5080 状态：worker=`ready`，worker_pid=`811485`，reload_count=`26`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向深度扰动 | 诊断最低分 | 最弱诊断深度扰动 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 73.923 | global_z_scale_0.50 | 13.117 | hand_z_noise_0.20_diagnostic | 70.000 |
| 跳 | PASS | 70.469 | global_z_scale_0.50 | 30.536 | hand_z_noise_0.10_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | normalized_distance | alignment | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---:|---|---|---|---|
| hand_z_noise_0.20_diagnostic | diagnostic | DIAG | 13.117 | diagnostic | 0.243748 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 强手部 z 噪声会破坏局部手形，只记录诊断边界。 |
| global_z_noise_0.20_diagnostic | diagnostic | DIAG | 14.689 | diagnostic | 0.230171 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 强整体 z 噪声，只记录诊断边界。 |
| hand_z_noise_0.10_diagnostic | diagnostic | DIAG | 23.733 | diagnostic | 0.172598 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 中等手部逐点 z 噪声会破坏局部手形，只记录诊断边界。 |
| global_z_noise_0.10_diagnostic | diagnostic | DIAG | 24.158 | diagnostic | 0.170467 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 中等逐点 z 噪声会改变重算后的局部手形，只记录诊断边界。 |
| global_z_scale_0.25_diagnostic | diagnostic | DIAG | 55.190 | diagnostic | 0.086187 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 极端深度压缩，只记录诊断边界。 |
| global_z_scale_3.00_diagnostic | diagnostic | DIAG | 55.845 | diagnostic | 0.084474 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 极端深度放大，只记录诊断边界。 |
| global_z_scale_0.50 | positive | PASS | 73.923 | >= 70.0 | 0.043811 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 整体深度动态被压缩到一半。 |
| global_z_scale_2.00 | positive | PASS | 75.644 | >= 70.0 | 0.040473 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 整体深度动态被放大到两倍。 |
| hand_z_scale_1.50 | positive | PASS | 78.241 | >= 70.0 | 0.035579 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 手部深度动态略放大，并重算手形特征。 |
| hand_z_scale_0.75 | positive | PASS | 79.136 | >= 70.0 | 0.033931 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 手部深度动态略收缩，并重算手形特征。 |
| global_z_offset_pos_0.10 | positive | PASS | 81.457 | >= 70.0 | 0.029739 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 整个人的 Holistic z 坐标出现轻微正向漂移。 |
| global_z_offset_neg_0.10 | positive | PASS | 81.457 | >= 70.0 | 0.029739 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 整个人的 Holistic z 坐标出现轻微负向漂移。 |
| self | positive | PASS | 100.000 | >= 95.0 | 0.000000 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 同一骨架重算基线。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | normalized_distance | alignment | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---:|---|---|---|---|
| hand_z_noise_0.10_diagnostic | diagnostic | DIAG | 30.536 | diagnostic | 0.201315 | semantic_action_window | semantic_mismatch | action_window_net | 中等手部逐点 z 噪声会破坏局部手形，只记录诊断边界。 |
| global_z_noise_0.20_diagnostic | diagnostic | DIAG | 70.469 | diagnostic | 0.284818 | semantic_action_window | score_valid | action_window_net | 强整体 z 噪声，只记录诊断边界。 |
| global_z_scale_0.25_diagnostic | diagnostic | DIAG | 70.469 | diagnostic | 0.145845 | semantic_action_window | score_valid | action_window_net | 极端深度压缩，只记录诊断边界。 |
| hand_z_noise_0.20_diagnostic | diagnostic | DIAG | 81.566 | diagnostic | 0.222256 | semantic_action_window | score_valid | full_sequence_local_relation_segment | 强手部 z 噪声会破坏局部手形，只记录诊断边界。 |
| global_z_noise_0.10_diagnostic | diagnostic | DIAG | 82.302 | diagnostic | 0.163525 | semantic_action_window | score_valid | action_window_net | 中等逐点 z 噪声会改变重算后的局部手形，只记录诊断边界。 |
| global_z_scale_3.00_diagnostic | diagnostic | DIAG | 82.302 | diagnostic | 0.188000 | semantic_action_window | score_valid | action_window_net | 极端深度放大，只记录诊断边界。 |
| global_z_scale_0.50 | positive | PASS | 70.469 | >= 70.0 | 0.118846 | semantic_action_window | score_valid | action_window_net | 整体深度动态被压缩到一半。 |
| hand_z_scale_0.75 | positive | PASS | 70.469 | >= 70.0 | 0.092679 | semantic_action_window | score_valid | action_window_net | 手部深度动态略收缩，并重算手形特征。 |
| global_z_scale_2.00 | positive | PASS | 82.302 | >= 70.0 | 0.105271 | semantic_action_window | score_valid | action_window_net | 整体深度动态被放大到两倍。 |
| hand_z_scale_1.50 | positive | PASS | 84.747 | >= 70.0 | 0.037857 | semantic_action_window | score_valid | action_window_net | 手部深度动态略放大，并重算手形特征。 |
| global_z_offset_pos_0.10 | positive | PASS | 98.790 | >= 70.0 | 0.003125 | semantic_action_window | score_valid | action_window_net | 整个人的 Holistic z 坐标出现轻微正向漂移。 |
| global_z_offset_neg_0.10 | positive | PASS | 98.790 | >= 70.0 | 0.003125 | semantic_action_window | score_valid | action_window_net | 整个人的 Holistic z 坐标出现轻微负向漂移。 |
| self | positive | PASS | 100.000 | >= 95.0 | 0.000000 | semantic_action_window | score_valid | action_window_net | 同一骨架重算基线。 |

## 说明

- 正向扰动覆盖中等深度漂移；强 z 噪声和极端深度缩放只作为诊断边界。
- 该门是合成 depth 压力测试，不能替代正式网页摄像头样本。

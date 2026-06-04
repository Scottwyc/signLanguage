# 花/跳评分统一质量门

- 生成时间：`2026-06-03T10:12:20`
- 综合状态：`PASS`
- Web 样本根目录：`/data/WYC/signLanguage/work/generated/web_scoring_mvp`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：不重新运行 Holistic，不重启 5080；只读保存的 web/API Holistic JSON 和模板 Holistic JSON。

## 子门状态

| 子门 | 状态 | 返回码 | 报告 |
|---|---|---:|---|
| web_regression | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_edge_clipping_15gate_v1/web_regression/flower_jump_web_regression.md` |
| web_confusion_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_edge_clipping_15gate_v1/web_confusion_gate/flower_jump_web_confusion_gate.md` |
| synthetic_confusion_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_edge_clipping_15gate_v1/synthetic_confusion_robustness_gate/flower_jump_synthetic_confusion_robustness_gate.md` |
| discrimination_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_edge_clipping_15gate_v1/discrimination_gate/flower_jump_discrimination_gate.md` |
| pose_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_edge_clipping_15gate_v1/pose_robustness_gate/flower_jump_pose_robustness_gate.md` |
| framing_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_edge_clipping_15gate_v1/framing_robustness_gate/flower_jump_framing_robustness_gate.md` |
| depth_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_edge_clipping_15gate_v1/depth_robustness_gate/flower_jump_depth_robustness_gate.md` |
| edge_clipping_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_edge_clipping_15gate_v1/edge_clipping_robustness_gate/flower_jump_edge_clipping_robustness_gate.md` |
| mirror_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_edge_clipping_15gate_v1/mirror_robustness_gate/flower_jump_mirror_robustness_gate.md` |
| frame_count_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_edge_clipping_15gate_v1/frame_count_robustness_gate/flower_jump_frame_count_robustness_gate.md` |
| landmark_noise_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_edge_clipping_15gate_v1/landmark_noise_robustness_gate/flower_jump_landmark_noise_robustness_gate.md` |
| missing_mask_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_edge_clipping_15gate_v1/missing_mask_robustness_gate/flower_jump_missing_mask_robustness_gate.md` |
| temporal_padding_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_edge_clipping_15gate_v1/temporal_padding_robustness_gate/flower_jump_temporal_padding_robustness_gate.md` |
| action_crop_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_edge_clipping_15gate_v1/action_crop_robustness_gate/flower_jump_action_crop_robustness_gate.md` |
| phase_order_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_edge_clipping_15gate_v1/phase_order_robustness_gate/flower_jump_phase_order_robustness_gate.md` |

## 网页保存样本回归

- replay 样本 `168`，错误 `0`；花/跳 diagnostics `149`，错误 `0`。
- 有效采集 `128`，有效正常+边界 `124`，有效低分 `4`，有效正常+边界率 `96.9%`。

| 词条 | 有效采集 | 正常+边界 | 有效低分 | 有效率 | 有效均分 |
|---|---:|---:|---:|---:|---:|
| 花 | 91 | 87 | 4 | 95.6% | 75.762 |
| 跳 | 37 | 37 | 0 | 100.0% | 76.677 |

## 网页保存样本花/跳交叉混淆门

- 样本 `149`，错误 `0`；eligible `124`，pass `124`，fail `0`。

| 目标词 | 样本 | eligible | pass | fail | 交叉最高 | margin 最低 | margin 均值 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 花 | 93 | 87 | 87 | 0 | 8.218 | 59.840 | 75.492 |
| 跳 | 56 | 37 | 37 | 0 | 41.535 | 29.317 | 55.519 |

## 合成鲁棒变体花/跳交叉混淆门

- 代表性正向扰动需保持目标词高分，同时按另一个词模板复评仍低分且 margin 足够。

| 目标词 | 状态 | cases | pass | fail | 目标最低 | 交叉最高 | margin 最低 | 最弱变体 |
|---|---|---:|---:|---:|---:|---:|---:|---|
| 花 | PASS | 10 | 10 | 0 | 76.727 | 8.506 | 70.776 | hand_noise_0.010_seed1 |
| 跳 | PASS | 10 | 10 | 0 | 70.708 | 25.551 | 55.668 | framing_shift_zoom_out |

## 负例判别门

| 目标词 | 状态 | 正例最低 | 最弱正例 | 负例最高 | 最强负例 | margin |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 80.311 | amplitude_0.85 | 32.047 | other_demo_谗_羡慕 | 48.263 |
| 跳 | PASS | 76.823 | amplitude_0.85 | 31.418 | fake_static_hold | 45.406 |

## 坐姿与镜头扰动门

| 目标词 | 状态 | 最低分 | 最弱扰动 | 门槛 |
|---|---|---:|---|---:|
| 花 | PASS | 80.446 | hand_jitter_small | 70.000 |
| 跳 | PASS | 93.015 | hand_jitter_small | 70.000 |

## 取景尺度与轻微旋转鲁棒性门

- 整人 zoom、画面偏移和轻微倾斜需保持高分；极端 zoom/pan 仅记录诊断边界。

| 目标词 | 状态 | 正向最低分 | 最弱正向取景扰动 | 诊断最低分 | 最弱诊断扰动 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 79.448 | global_zoom_out_0.75 | 77.954 | extreme_zoom_out_0.60_diag | 70.000 |
| 跳 | PASS | 70.708 | framing_shift_zoom_out | 70.509 | extreme_zoom_out_0.60_diag | 70.000 |

## z/depth 深度鲁棒性门

- 中等 Holistic z 坐标偏移/缩放需保持高分；逐点 z 噪声和极端缩放仅记录诊断边界。

| 目标词 | 状态 | 正向最低分 | 最弱正向深度扰动 | 诊断最低分 | 最弱诊断深度扰动 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 73.923 | global_z_scale_0.50 | 13.117 | hand_z_noise_0.20_diagnostic | 70.000 |
| 跳 | PASS | 70.469 | global_z_scale_0.50 | 30.536 | hand_z_noise_0.10_diagnostic | 70.000 |

## 画面边缘裁切鲁棒性门

- 非关键或轻度边缘裁切需保持高分；核心手语信息出画面需低分或重采/语义失败。

| 目标词 | 状态 | 正向最低分 | 最弱正向边缘裁切 | 核心裁切最高分 | 最强核心裁切 |
|---|---|---:|---|---:|---|
| 花 | PASS | 76.689 | right_opening_wrist_edge_clip | 11.133 | right_opening_all_tips_edge_clip |
| 跳 | PASS | 78.545 | right_jumper_ring_pinky_edge_clip | 10.489 | left_ground_wrist_edge_clip |

## 浏览器镜像鲁棒性门

- `mirror_x` 是正向门；左右标签互换仅记录诊断边界，不作为通过条件。

| 目标词 | 状态 | 正向最低分 | 最弱正向变体 | 左右标签诊断最低分 | 最弱诊断变体 |
|---|---|---:|---|---:|---|
| 花 | PASS | 80.533 | mirror_x | 0.919 | swap_labels_diagnostic |
| 跳 | PASS | 80.843 | mirror_x | 31.053 | mirror_x_swap_labels_diagnostic |

## 帧数与采样密度扰动门

| 目标词 | 状态 | 推荐最少帧 | 最低分 | 最弱采样 | 门槛 | 欠采样最低分 |
|---|---|---:|---:|---|---:|---:|
| 花 | PASS | 12 | 78.482 | uniform_12f | 70.000 | 32.284 |
| 跳 | PASS | 6 | 70.488 | drop_every_3_keep_ends | 70.000 | - |

## Landmark 噪声鲁棒性门

- 小幅连续手部关键点抖动和稀少整帧手部不稳定需保持高分；严重噪声/逐点丢失仅记录诊断边界。

| 目标词 | 状态 | 正向最低分 | 最弱正向噪声 | 诊断最低分 | 最弱诊断噪声 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 76.064 | hand_noise_0.010_seed2 | 11.118 | severe_shuffle_diagnostic | 70.000 |
| 跳 | PASS | 72.810 | hand_noise_0.010_seed1 | 8.825 | severe_point_dropout_0.25_diagnostic | 70.000 |

## 静止 padding 与时序鲁棒性门

| 目标词 | 状态 | 正向最低分 | 最弱正向变体 | 静态最高分 | 最强静态变体 |
|---|---|---:|---|---:|---|
| 花 | PASS | 97.862 | suffix_hold_25pct | 1.460 | static_hold_mid |
| 跳 | PASS | 79.124 | slow_repeat_each_2x | 31.418 | static_hold_mid |

## 语义相位顺序鲁棒性门

- 负向样本质量口径：`['needs_recapture', 'semantic_mismatch']`；单调变速/采样抖动需保持高分，倒放/半段交换/三相位乱序需低分。

| 目标词 | 状态 | 正向最低分 | 最弱正向变体 | 乱序最高分 | 最强乱序变体 |
|---|---|---:|---|---:|---|
| 花 | PASS | 79.410 | ordered_jitter | 33.723 | scramble_three_phases |
| 跳 | PASS | 69.389 | ordered_jitter | 45.000 | swap_halves |

## 录制起止裁剪鲁棒性门

- 轻度起录/停录裁剪需保持高分；词条专属缺核心半段需低分或语义失败；不稳定半段仅诊断。

| 目标词 | 状态 | 正向最低分 | 最弱正向裁剪 | 缺核心最高分 | 最强缺核心裁剪 | 诊断分数范围 |
|---|---|---:|---|---:|---|---|
| 花 | PASS | 97.958 | trim_end_15pct | 41.949 | early_60pct_missing_bloom | 81.209 - 81.209 |
| 跳 | PASS | 80.750 | trim_start_15pct | 45.000 | early_half_missing_landing | 82.538 - 82.538 |

## 缺失与关键 mask 鲁棒性门

| 目标词 | 状态 | 正向最低分 | 最弱正向变体 | 关键缺失最高分 | 最强关键缺失变体 |
|---|---|---:|---|---:|---|
| 花 | PASS | 100.000 | drop_face | 1.171 | drop_right_core_hand |
| 跳 | PASS | 100.000 | drop_face | 3.037 | drop_left_ground_hand |

## Marker 状态

- marker last_request_id：`web_20260602_233348_53e3df5d`
- marker 后新增样本：`0`
- marker 后新增花/跳样本：`0`

## 使用说明

- 修改 `score_holistic_sequence_mvp.py`、语义 profile、模板权重、score scaling 或对齐策略后，优先运行本脚本。
- 若本脚本 PASS，只能说明当前保存样本与合成鲁棒性门没有回退；真实用户网页测试仍需要新的摄像头样本和人工复核。

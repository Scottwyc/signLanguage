# 花/跳网页复测前就绪报告

- 生成时间：`2026-06-04T01:16:20`
- 复测就绪：`PASS`
- 目标完成度：`NOT_READY`
- 下一步：`采集 花、跳`
- 要求覆盖词条：`花、跳`
- 已覆盖词条：`-`
- 缺失词条：`花、跳`
- 口径：只读检查；不调用 `/api/score`，不移动 marker，不重启 5080/Holistic。

## 运行态

| 项 | 状态 | 细节 |
|---|---|---|
| 5080/Holistic | `PASS` | worker=`ready`，pid=`811485`，reload_count=`15`，last_reload_error=`None` |
| watcher | `PASS` | event=`no_target_samples`，pid=`1371327`，target_count=`0` |
| 前端契约 | `PASS` | failed=`0`，warning=`3` |
| 综合质量门 | `PASS` | 报告 `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_hand_stream_latency_56gate_v1/flower_jump_quality_gate.md` |
| 浏览器证据门 | `PASS` | 报告 `work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_hand_stream_latency_56gate_v1/browser_evidence_gate/flower_jump_browser_evidence_gate.md` |
| 网页上传权重语义 | `PASS` | checks=`8`，failed=`-` |
| 网页上传权重仿真 | `PASS` | cases=`3`，报告 `work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_hand_stream_latency_56gate_v1/browser_upload_weight_simulation_gate/browser_upload_weight_simulation_gate.md` |
| 网页上传强证据 | `PASS` | strong path=`frame_weights`，missing_required=`-`，client metadata pending `client_source、client_session_id、client_capture_id` |

## 当前质量门关键指标

- 保存网页/API 回归：样本 `168`，错误 `0`；有效正常+边界率 `96.9%`。

| 词条 | 有效采集 | 正常+边界 | 有效低分 | 有效率 | 有效均分 |
|---|---:|---:|---:|---:|---:|
| 花 | 91 | 87 | 4 | 95.6% | 75.775 |
| 跳 | 37 | 37 | 0 | 100.0% | 76.677 |

- 花/跳交叉混淆：eligible `124`，pass `124`，fail `0`。

| 词条 | 合成鲁棒 cases | pass | fail | 目标最低 | 交叉最高 | margin 最低 | 最弱变体 |
|---|---:|---:|---:|---:|---:|---:|---|
| 花 | 10 | 10 | 0 | 76.727 | 8.506 | 70.776 | hand_noise_0.010_seed1 |
| 跳 | 10 | 10 | 0 | 70.708 | 25.551 | 55.428 | framing_shift_zoom_out |

| 词条 | stutter 正向最低分 | 最弱正向 stutter | 持续冻结最高分 | 最强持续冻结 | stutter 诊断最低分 | 最弱诊断边界 |
|---|---:|---|---:|---|---:|---|
| 花 | 93.869 | freeze_mid_15pct | 41.635 | freeze_mid_50pct_negative | 87.915 | freeze_mid_25pct_diagnostic |
| 跳 | 72.011 | freeze_mid_4f | 12.747 | freeze_mid_35pct_negative | 73.224 | freeze_mid_5f_diagnostic |

| 词条 | 插值补洞正向最低分 | 最弱正向插值 | 插值补洞诊断最低分 | 最弱诊断插值 |
|---|---:|---|---:|---|
| 花 | 93.731 | right_hand_middle12_interp | 74.445 | right_hand_middle25_interp_diagnostic |
| 跳 | 82.672 | right_hand_middle12_interp | 77.316 | both_hands_middle25_interp_diagnostic |

| 词条 | 速率正向最低分 | 最弱正向速率扰动 | 速率诊断最低分 | 最弱诊断边界 |
|---|---:|---|---:|---|
| 花 | 92.730 | same_count_micro_rate_jitter | 94.439 | bloom_core_gap_diagnostic |
| 跳 | 77.195 | global_slow_1.50x | 80.007 | global_slow_2.25x_diagnostic |

| 词条 | 组合正向最低分 | 最弱正向组合 | 组合诊断最低分 | 最弱诊断组合 |
|---|---:|---|---:|---|
| 花 | 77.955 | combo_slow_sparse_freeze_lowres | 69.472 | diagnostic_quantized_micro_jitter |
| 跳 | 73.632 | combo_fast_aspect_hand_quant | 74.006 | diagnostic_dropout_rate_stack |

| 词条 | frame_weights 正向最低分 | 最弱正向权重 | 反向权重诊断最低分 | 最弱诊断权重 |
|---|---:|---|---:|---|
| 花 | 99.161 | back_loaded_broad_emphasis | 99.347 | inverted_dynamic_diagnostic |
| 跳 | 76.297 | back_loaded_broad_emphasis | 10.120 | inverted_dynamic_diagnostic |

| 词条 | 坐标精度正向最低分 | 最弱正向精度扰动 | 粗量化诊断最低分 | 最弱诊断精度扰动 |
|---|---:|---|---:|---|
| 花 | 80.805 | hand_xy_quantize_1_128 | 78.075 | severe_hand_xy_quantize_1_32_diagnostic |
| 跳 | 96.833 | hand_xy_quantize_1_128 | 84.267 | severe_hand_xy_quantize_1_32_diagnostic |

| 词条 | 运动幅度正向最低分 | 最弱正向幅度变体 | 平滑/模糊诊断最低分 | 最弱诊断平滑/模糊 |
|---|---:|---|---:|---|
| 花 | 79.074 | hand_motion_amplitude_0.85 | 10.092 | hand_motion_blur_5tap_heavy_diagnostic |
| 跳 | 75.662 | hand_motion_amplitude_0.85 | 70.351 | hand_motion_amplitude_0.55_diagnostic |

| 词条 | landmark 噪声正向最低分 | 最弱正向噪声 | 严重噪声诊断最低分 | 最弱诊断噪声 |
|---|---:|---|---:|---|
| 花 | 76.064 | hand_noise_0.010_seed2 | 11.118 | severe_shuffle_diagnostic |
| 跳 | 72.810 | hand_noise_0.010_seed1 | 8.825 | severe_point_dropout_0.25_diagnostic |

| 词条 | landmark 跳点正向最低分 | 最弱正向跳点 | 跳点诊断最低分 | 最弱诊断跳点 |
|---|---:|---|---:|---|
| 花 | 92.772 | sparse_tip_spike_every_7th | 21.400 | alternating_tip_spike_diagnostic |
| 跳 | 70.469 | single_frame_tip_spike | 82.302 | alternating_tip_spike_diagnostic |

| 词条 | 指尖遮挡正向最低分 | 最弱正向遮挡 | 核心指尖缺失最高分 | 最强核心缺失 | 遮挡诊断最低分 | 最弱诊断遮挡 |
|---|---:|---|---:|---|---:|---|
| 花 | 95.829 | middle20_all_tips | 11.133 | all_right_tips_negative | 75.986 | core40_all_tips_diagnostic |
| 跳 | 70.469 | sparse_all_tips | 10.010 | all_right_index_middle_negative | 76.758 | core40_all_tips_diagnostic |

| 词条 | 掌根锚点正向最低分 | 最弱正向锚点缺失 | 核心锚点全缺最高分 | 最强核心锚点缺失 | 锚点诊断最低分 | 最弱诊断锚点缺失 |
|---|---:|---|---:|---|---:|---|
| 花 | 95.791 | right_middle20_wrist_mcp_anchor | 11.140 | right_all_mcp_anchor_negative | 76.069 | right_core40_palm_anchor_diagnostic |
| 跳 | 70.469 | right_sparse_palm_anchor | 10.158 | left_all_palm_anchor_negative | 76.758 | right_core40_palm_anchor_diagnostic |

| 词条 | 中段指节遮挡正向最低分 | 最弱正向中段指节遮挡 | 中段指节诊断最低分 | 最弱诊断遮挡 |
|---|---:|---|---:|---|
| 花 | 99.437 | right_sparse_all_inner_joints | 97.559 | right_all_inner_joints_diagnostic |
| 跳 | 76.638 | right_middle20_index_middle_inner_joints | 70.469 | right_core40_index_middle_inner_joints_diagnostic |

| 词条 | 手形尺度正向最低分 | 最弱正向手形尺度 | 极端尺度诊断最低分 | 最弱诊断尺度 |
|---|---:|---|---:|---|
| 花 | 80.339 | right_hand_aspect_x0.85_y1.20 | 76.902 | both_hands_aspect_x0.55_y1.60_diagnostic |
| 跳 | 86.403 | right_hand_aspect_x0.85_y1.20 | 69.697 | both_hands_uniform_scale_0.55_diagnostic |

| 词条 | 手部尺度呼吸正向最低分 | 最弱正向尺度呼吸 | 尺度呼吸诊断最低分 | 最弱诊断尺度呼吸 |
|---|---:|---|---:|---|
| 花 | 81.932 | both_hands_smooth_aspect_breathing_0.10 | 81.395 | both_hands_strong_smooth_aspect_breathing_0.35_diagnostic |
| 跳 | 78.452 | both_hands_sparse_aspect_flicker_0.10_every_6f | 74.623 | both_hands_strong_smooth_uniform_breathing_0.35_diagnostic |

| 词条 | 手部中心漂移正向最低分 | 最弱正向中心漂移 | 中心漂移诊断最低分 | 最弱诊断中心漂移 |
|---|---:|---|---:|---|
| 花 | 82.112 | both_hands_smooth_center_y_0.04 | 81.773 | both_hands_strong_smooth_center_y_0.18_diagnostic |
| 跳 | 98.551 | right_hand_smooth_center_y_0.03 | 77.083 | both_hands_strong_smooth_center_y_0.18_diagnostic |

| 词条 | 全局取景漂移正向最低分 | 最弱正向全局取景漂移 | 全局取景诊断最低分 | 最弱诊断全局取景漂移 |
|---|---:|---|---:|---|
| 花 | 81.919 | smooth_global_zoom_0.08 | 80.909 | strong_smooth_global_zoom_0.35_diagnostic |
| 跳 | 97.598 | sparse_global_zoom_0.06_every_6f | 76.830 | strong_smooth_global_pan_y_0.22_diagnostic |

| 词条 | 手部旋转正向最低分 | 最弱正向旋转 | 极端旋转诊断最低分 | 最弱诊断旋转 |
|---|---:|---|---:|---|
| 花 | 81.336 | both_hands_rotate_pos20deg | 81.162 | both_hands_rotate_pos45deg_diagnostic |
| 跳 | 84.409 | both_hands_rotate_neg20deg | 81.149 | both_hands_rotate_pos45deg_diagnostic |

| 词条 | z 倾角正向最低分 | 最弱正向 z 倾角 | z 倾角诊断最低分 | 最弱诊断 z 倾角 |
|---|---:|---|---:|---|
| 花 | 81.396 | right_hand_pitch_xz_pos12deg | 81.165 | right_hand_yaw_yz_neg35deg_diagnostic |
| 跳 | 98.093 | right_hand_pitch_xz_neg12deg | 92.212 | right_hand_yaw_yz_neg35deg_diagnostic |

| 词条 | 手指弯曲正向最低分 | 最弱正向弯曲 | 手指弯曲诊断最低分 | 最弱诊断弯曲 |
|---|---:|---|---:|---|
| 花 | 80.887 | right_opening_ring_pinky_curl_0.16 | 79.541 | right_opening_all_fingers_curl_0.38_diagnostic |
| 跳 | 92.938 | right_person_index_middle_curl_0.16 | 82.206 | right_person_index_middle_curl_0.50_diagnostic |

| 词条 | 手指比例正向最低分 | 最弱正向比例 | 手指比例诊断最低分 | 最弱诊断比例 |
|---|---:|---|---:|---|
| 花 | 80.849 | right_opening_ring_pinky_length_1.12 | 79.378 | right_opening_all_finger_length_1.30_diagnostic |
| 跳 | 93.587 | right_person_index_middle_length_1.10 | 70.331 | right_person_index_middle_length_1.35_diagnostic |

| 词条 | 动态入退场正向最低分 | 最弱正向动态污染 | 入场-only 最高分 | 最强入场-only | 诊断最低分 | 最弱诊断 |
|---|---:|---|---:|---|---:|---|
| 花 | 96.727 | suffix_moving_exit_25pct | 21.271 | moving_entry_only_35pct_negative | 21.959 | moving_exit_only_35pct_diagnostic |
| 跳 | 99.998 | entry_exit_moving_18pct | 0.016 | moving_entry_only_35pct_negative | 4.284 | moving_exit_only_35pct_diagnostic |

| 词条 | 核心速度正向最低分 | 最弱正向核心速度 | 核心速度诊断最低分 | 最弱诊断边界 |
|---|---:|---|---:|---|
| 花 | 95.085 | bloom_core_fast_then_slow | 95.509 | bloom_core_fast_0.45x_diagnostic |
| 跳 | 75.484 | jump_relation_core_slow_1.40x | 23.502 | jump_relation_core_slow_1.55x_diagnostic |

| 词条 | 手部置信度正向最低分 | 最弱正向低置信 | 手部置信度诊断最低分 | 最弱诊断边界 |
|---|---:|---|---:|---|
| 花 | 100.000 | flower_all_hands_confidence_0.85 | 1.171 | flower_all_hands_effective_missing_diagnostic |
| 跳 | 99.856 | jump_relation_core_sparse_confidence_0.55 | 0.125 | jump_all_hands_effective_missing_diagnostic |

| 词条 | 能量选帧正向最低分 | 最弱正向选帧 | 能量选帧诊断最低分 | 最弱诊断边界 | 推荐帧 |
|---|---:|---|---:|---|---:|
| 花 | 78.766 | frontend_energy_coverage_12f | 4.901 | top_energy_no_endpoints_12f_diagnostic | 12 |
| 跳 | 74.690 | frontend_energy_coverage_6f | 6.558 | low_energy_with_endpoints_6f_diagnostic | 6 |

| 词条 | rolling-shutter 正向最低分 | 最弱正向 rolling-shutter | rolling-shutter 诊断最低分 | 最弱诊断边界 |
|---|---:|---|---:|---|
| 花 | 81.782 | ramp_rolling_x_from_y_0.06 | 81.602 | strong_smooth_rolling_x_from_y_0.22_diagnostic |
| 跳 | 97.367 | local_hands_smooth_rolling_x_from_y_0.10 | 94.343 | strong_smooth_rolling_x_from_y_0.22_diagnostic |

| 词条 | 手部细节损失正向最低分 | 最弱正向细节损失 | 手部细节损失诊断最低分 | 最弱诊断边界 |
|---|---:|---|---:|---|
| 花 | 80.339 | flower_opening_right_inner_axis_smooth_0.60 | 77.727 | both_hands_tip_anchor_blend_0.38_diagnostic |
| 跳 | 77.234 | right_hand_inner_axis_smooth_0.45 | 79.899 | both_hands_tip_anchor_blend_0.38_diagnostic |

| 词条 | 手部流延迟正向最低分 | 最弱正向手部流延迟 | 手部流延迟诊断最低分 | 最弱诊断边界 |
|---|---:|---|---:|---|
| 花 | 97.237 | sparse_both_hands_delay_2f_every_5f | 97.406 | middle35_both_hands_delay_5f_diagnostic |
| 跳 | 76.036 | sparse_both_hands_delay_2f_every_5f | 76.890 | both_hands_advance_4f_diagnostic |

| 词条 | 非关键缺失最低分 | 最弱非关键缺失 | 关键缺失最高分 | 最强关键缺失 |
|---|---:|---|---:|---|
| 花 | 100.000 | drop_face | 1.171 | drop_right_core_hand |
| 跳 | 100.000 | drop_face | 3.037 | drop_left_ground_hand |

| 词条 | 取景正向最低分 | 最弱取景扰动 | 极端诊断最低分 | 最弱诊断扰动 |
|---|---:|---|---:|---|
| 花 | 79.448 | global_zoom_out_0.75 | 77.954 | extreme_zoom_out_0.60_diag |
| 跳 | 70.708 | framing_shift_zoom_out | 70.509 | extreme_zoom_out_0.60_diag |

| 词条 | 宽高比正向最低分 | 最弱正向宽高比 | 极端宽高比诊断最低分 | 最弱诊断宽高比 |
|---|---:|---|---:|---|
| 花 | 80.345 | aspect_x0.85_y1.18 | 76.940 | diagnostic_x0.55_y1.55 |
| 跳 | 85.975 | aspect_x0.85_y1.18 | 55.282 | diagnostic_x1.55_y0.55 |

| 词条 | 整体倾斜正向最低分 | 最弱正向倾斜 | 极端倾斜诊断最低分 | 最弱诊断倾斜 |
|---|---:|---|---:|---|
| 花 | 81.180 | camera_roll_pos20deg | 80.849 | camera_roll_pos45deg_diagnostic |
| 跳 | 89.634 | camera_roll_neg20deg | 75.140 | camera_roll_neg45deg_diagnostic |

| 词条 | 身体锚点正向最低分 | 最弱正向锚点漂移 | 诊断最低分 | 最弱诊断漂移 |
|---|---:|---|---:|---|
| 花 | 100.000 | self_recomputed | 100.000 | pose_face_jitter_0.35_diagnostic |
| 跳 | 100.000 | self_recomputed | 100.000 | pose_face_jitter_0.35_diagnostic |

| 词条 | depth 正向最低分 | 最弱 depth 扰动 | depth 诊断最低分 | 最弱诊断扰动 |
|---|---:|---|---:|---|
| 花 | 73.923 | global_z_scale_0.50 | 13.117 | hand_z_noise_0.20_diagnostic |
| 跳 | 70.469 | global_z_scale_0.50 | 30.536 | hand_z_noise_0.10_diagnostic |

| 词条 | z 时序抖动正向最低分 | 最弱正向 z 抖动 | z 时序诊断最低分 | 最弱诊断 z 抖动 |
|---|---:|---|---:|---|
| 花 | 81.408 | smooth_global_z_scale_0.20 | 79.869 | strong_hand_z_scale_0.55_diagnostic |
| 跳 | 79.288 | smooth_global_z_offset_0.08 | 78.276 | strong_global_z_offset_0.25_diagnostic |

| 词条 | 边缘裁切正向最低分 | 最弱正向边缘裁切 | 核心裁切最高分 | 最强核心裁切 |
|---|---:|---|---:|---|
| 花 | 76.689 | right_opening_wrist_edge_clip | 11.133 | right_opening_all_tips_edge_clip |
| 跳 | 78.545 | right_jumper_ring_pinky_edge_clip | 10.489 | left_ground_wrist_edge_clip |

| 词条 | 镜像正向最低分 | 最弱镜像变体 | 左右标签诊断最低分 | 最弱诊断变体 |
|---|---:|---|---:|---|
| 花 | 80.533 | mirror_x | 82.267 | swap_labels_diagnostic |
| 跳 | 80.843 | mirror_x | 31.053 | mirror_x_swap_labels_diagnostic |

| 词条 | 手角色正向最低分 | 最弱正向角色变体 | 角色互换最高分 | 最强角色互换负例 |
|---|---:|---|---:|---|
| 花 | 80.533 | mirror_x | - | - |
| 跳 | 80.843 | mirror_x | 36.324 | role_swap_negative |

| 词条 | 非核心手/手指正向最低分 | 最弱正向干扰 | 诊断最低分 | 最弱诊断核心扰动 |
|---|---:|---|---:|---|
| 花 | 100.000 | self_recomputed | 25.938 | flower_right_opening_tips_collapse_diagnostic |
| 跳 | 73.032 | jump_right_noncore_fingers_motion_drift | 81.460 | jump_right_index_middle_collapse_diagnostic |

| 词条 | 关系几何正向最低分 | 最弱正向关系扰动 | 关系负向最高分 | 最强负向关系 | 关系诊断最低分 | 最弱诊断关系 |
|---|---:|---|---:|---|---:|---|
| 花 | 79.772 | right_relation_jitter_0.035 | - | - | 79.250 | flower_relation_reverse_y_diagnostic |
| 跳 | 70.469 | right_relation_offset_x_0.15 | 93.960 | jump_relation_y_amplitude_0.45_negative | 74.458 | right_relation_y_amplitude_1.75_diagnostic |

| 词条 | 核心手形正向最低分 | 最弱正向核心形变 | 核心形变负向最高分 | 最强负向核心形变 | 核心形变诊断最低分 | 最弱诊断形变 |
|---|---:|---|---:|---|---:|---|
| 花 | 79.334 | flower_opening_dynamic_0.75 | 49.353 | flower_opening_dynamic_0.45_negative | 77.639 | flower_opening_dynamic_0.60_diagnostic |
| 跳 | 77.830 | jump_two_finger_dynamic_1.15 | - | - | 82.090 | jump_two_finger_radial_0.45_diagnostic |

| 词条 | 斜拍透视正向最低分 | 最弱正向透视/剪切 | 斜拍透视诊断最低分 | 最弱诊断透视/剪切 |
|---|---:|---|---:|---|
| 花 | 80.018 | perspective_z_to_y_0.35 | 78.288 | diagnostic_z_to_x_0.80 |
| 跳 | 88.573 | perspective_z_to_x_0.35 | 77.705 | diagnostic_combo_shear_0.18_zx_0.60 |

| 词条 | 手间时序错位正向最低分 | 最弱正向错位 | 手间错位诊断最低分 | 最弱诊断错位 |
|---|---:|---|---:|---|
| 花 | 99.023 | right_hand_delay_2f | 97.824 | right_hand_delay_4f_diagnostic |
| 跳 | 75.688 | left_hand_advance_1f | 75.809 | left_hand_delay_4f_diagnostic |

| 词条 | 帧序抖动正向最低分 | 最弱正向帧序抖动 | 帧序抖动诊断最低分 | 最弱诊断帧序抖动 |
|---|---:|---|---:|---|
| 花 | 97.035 | adjacent_swap_every_6f | 97.068 | block_reverse_25pct_diagnostic |
| 跳 | 71.379 | adjacent_swap_every_6f | 45.000 | block_reverse_25pct_diagnostic |

| 词条 | 手指身份抖动正向最低分 | 最弱正向指链抖动 | 手指身份诊断最低分 | 最弱诊断指链抖动 |
|---|---:|---|---:|---|
| 花 | 79.043 | right_index_middle_chain_swap | 77.035 | right_index_ring_diagnostic |
| 跳 | 71.892 | right_middle_ring_sparse_jitter | 81.108 | right_thumb_index_diagnostic |

| 词条 | 标签 flicker 正向最低分 | 最弱正向 flicker | 严重 flicker 最高分 | 最强严重 flicker |
|---|---:|---|---:|---|
| 花 | 96.804 | sparse_label_flicker | 27.593 | sustained_core_label_flicker_negative |
| 跳 | 70.469 | single_frame_label_flicker | 14.618 | alternating_label_flicker_negative |

| 词条 | 连续手部空洞正向最低分 | 最弱正向空洞 | 持续空洞最高分 | 最强持续空洞 |
|---|---:|---|---:|---|
| 花 | 95.170 | right_core_15pct_mid | 55.975 | right_core_25pct_mid_negative |
| 跳 | 74.629 | right_jump_3f_mid | 18.484 | both_hands_2f_mid_negative |

| 词条 | padding 正向最低分 | 最弱正向 padding | 静态最高分 | 最强静态变体 |
|---|---:|---|---:|---|
| 花 | 97.862 | suffix_hold_25pct | 1.460 | static_hold_mid |
| 跳 | 79.124 | slow_repeat_each_2x | 31.418 | static_hold_mid |

| 词条 | 相位单调最低分 | 最弱单调变形 | 相位错序最高分 | 最强错序变体 |
|---|---:|---|---:|---|
| 花 | 79.410 | ordered_jitter | 33.723 | scramble_three_phases |
| 跳 | 69.389 | ordered_jitter | 45.000 | swap_halves |

| 词条 | 起止裁剪正向最低分 | 最弱正向裁剪 | 缺核心最高分 | 最强缺核心裁剪 | 诊断分数范围 |
|---|---:|---|---:|---|---|
| 花 | 97.958 | trim_end_15pct | 41.949 | early_60pct_missing_bloom | 81.209 - 81.209 |
| 跳 | 80.750 | trim_start_15pct | 45.000 | early_half_missing_landing | 82.538 - 82.538 |

| 词条 | 重复动作正向最低分 | 最弱正向重复 | 不完整最高分 | 最强不完整负例 | 诊断分数范围 |
|---|---:|---|---:|---|---|
| 花 | 96.505 | repeat_full_2x_mid_pause | 21.902 | setup_only_35pct_negative | 77.686 - 95.417 |
| 跳 | 81.950 | core_repeat_middle | 12.239 | landing_only_35pct_negative | 77.868 - 77.868 |

## 下一步采集建议

| 词条 | 推荐最少上传帧 | 推荐采集 | 动作重点 |
|---|---:|---|---|
| 花 | 12 | 2.5s / 5fps | 从撮合状态开始，手指张开/绽放过程完整入画。 |
| 跳 | 6 | 2.0s / 5fps | 左手地面和右手两指小人同时入画，右手在左手基础上完成弹跳。 |

## 关联报告

- 完成度审计：`work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_hand_stream_latency_56gate_v1/goal_readiness/flower_jump_goal_readiness_audit.md`
- 前端契约：`work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_hand_stream_latency_56gate_v1/frontend_contract/watch_status_frontend_contract.md`
- 浏览器证据门：`work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_hand_stream_latency_56gate_v1/browser_evidence_gate/flower_jump_browser_evidence_gate.md`
- 网页上传权重仿真：`work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_hand_stream_latency_56gate_v1/browser_upload_weight_simulation_gate/browser_upload_weight_simulation_gate.md`
- 综合质量门：`work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_hand_stream_latency_56gate_v1/flower_jump_quality_gate.md`

## 结论

- 算法、运行态和前端链路已就绪；还需要真实网页摄像头样本：`采集 花、跳`。

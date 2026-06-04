# 花/跳网页复测前就绪报告

- 生成时间：`2026-06-03T11:39:50`
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
| 5080/Holistic | `PASS` | worker=`ready`，pid=`811485`，reload_count=`14`，last_reload_error=`None` |
| watcher | `PASS` | event=`no_target_samples`，pid=`4021854`，target_count=`0` |
| 前端契约 | `PASS` | failed=`0`，warning=`3` |
| 综合质量门 | `PASS` | 报告 `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_hand_role_21gate_v1/flower_jump_quality_gate.md` |
| 浏览器证据门 | `PASS` | 报告 `work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_hand_role_21gate_reload_v1/browser_evidence_gate/flower_jump_browser_evidence_gate.md` |
| 网页上传权重语义 | `PASS` | checks=`8`，failed=`-` |
| 网页上传权重仿真 | `PASS` | cases=`3`，报告 `work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_hand_role_21gate_reload_v1/browser_upload_weight_simulation_gate/browser_upload_weight_simulation_gate.md` |
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

| 词条 | 手形尺度正向最低分 | 最弱正向手形尺度 | 极端尺度诊断最低分 | 最弱诊断尺度 |
|---|---:|---|---:|---|
| 花 | 80.339 | right_hand_aspect_x0.85_y1.20 | 76.902 | both_hands_aspect_x0.55_y1.60_diagnostic |
| 跳 | 86.403 | right_hand_aspect_x0.85_y1.20 | 69.697 | both_hands_uniform_scale_0.55_diagnostic |

| 词条 | 手部旋转正向最低分 | 最弱正向旋转 | 极端旋转诊断最低分 | 最弱诊断旋转 |
|---|---:|---|---:|---|
| 花 | 81.336 | both_hands_rotate_pos20deg | 81.162 | both_hands_rotate_pos45deg_diagnostic |
| 跳 | 84.409 | both_hands_rotate_neg20deg | 81.149 | both_hands_rotate_pos45deg_diagnostic |

| 词条 | 非关键缺失最低分 | 最弱非关键缺失 | 关键缺失最高分 | 最强关键缺失 |
|---|---:|---|---:|---|
| 花 | 100.000 | drop_face | 1.171 | drop_right_core_hand |
| 跳 | 100.000 | drop_face | 3.037 | drop_left_ground_hand |

| 词条 | 取景正向最低分 | 最弱取景扰动 | 极端诊断最低分 | 最弱诊断扰动 |
|---|---:|---|---:|---|
| 花 | 79.448 | global_zoom_out_0.75 | 77.954 | extreme_zoom_out_0.60_diag |
| 跳 | 70.708 | framing_shift_zoom_out | 70.509 | extreme_zoom_out_0.60_diag |

| 词条 | depth 正向最低分 | 最弱 depth 扰动 | depth 诊断最低分 | 最弱诊断扰动 |
|---|---:|---|---:|---|
| 花 | 73.923 | global_z_scale_0.50 | 13.117 | hand_z_noise_0.20_diagnostic |
| 跳 | 70.469 | global_z_scale_0.50 | 30.536 | hand_z_noise_0.10_diagnostic |

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

## 下一步采集建议

| 词条 | 推荐最少上传帧 | 推荐采集 | 动作重点 |
|---|---:|---|---|
| 花 | 12 | 2.5s / 5fps | 从撮合状态开始，手指张开/绽放过程完整入画。 |
| 跳 | 6 | 2.0s / 5fps | 左手地面和右手两指小人同时入画，右手在左手基础上完成弹跳。 |

## 关联报告

- 完成度审计：`work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_hand_role_21gate_reload_v1/goal_readiness/flower_jump_goal_readiness_audit.md`
- 前端契约：`work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_hand_role_21gate_reload_v1/frontend_contract/watch_status_frontend_contract.md`
- 浏览器证据门：`work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_hand_role_21gate_reload_v1/browser_evidence_gate/flower_jump_browser_evidence_gate.md`
- 网页上传权重仿真：`work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_hand_role_21gate_reload_v1/browser_upload_weight_simulation_gate/browser_upload_weight_simulation_gate.md`
- 综合质量门：`work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_hand_role_21gate_v1/flower_jump_quality_gate.md`

## 结论

- 算法、运行态和前端链路已就绪；还需要真实网页摄像头样本：`采集 花、跳`。

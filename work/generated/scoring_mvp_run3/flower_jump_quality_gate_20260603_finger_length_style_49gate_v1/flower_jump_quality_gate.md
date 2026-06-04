# 花/跳评分统一质量门

- 生成时间：`2026-06-03T23:46:54`
- 综合状态：`PASS`
- Web 样本根目录：`/data/WYC/signLanguage/work/generated/web_scoring_mvp`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：不重新运行 Holistic，不重启 5080；只读保存的 web/API Holistic JSON 和模板 Holistic JSON。

## 子门状态

| 子门 | 状态 | 返回码 | 报告 |
|---|---|---:|---|
| web_regression | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/web_regression/flower_jump_web_regression.md` |
| web_confusion_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/web_confusion_gate/flower_jump_web_confusion_gate.md` |
| synthetic_confusion_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/synthetic_confusion_robustness_gate/flower_jump_synthetic_confusion_robustness_gate.md` |
| discrimination_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/discrimination_gate/flower_jump_discrimination_gate.md` |
| pose_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/pose_robustness_gate/flower_jump_pose_robustness_gate.md` |
| framing_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/framing_robustness_gate/flower_jump_framing_robustness_gate.md` |
| aspect_ratio_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/aspect_ratio_robustness_gate/flower_jump_aspect_ratio_robustness_gate.md` |
| camera_roll_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/camera_roll_robustness_gate/flower_jump_camera_roll_robustness_gate.md` |
| body_anchor_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/body_anchor_robustness_gate/flower_jump_body_anchor_robustness_gate.md` |
| depth_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/depth_robustness_gate/flower_jump_depth_robustness_gate.md` |
| edge_clipping_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/edge_clipping_robustness_gate/flower_jump_edge_clipping_robustness_gate.md` |
| mirror_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/mirror_robustness_gate/flower_jump_mirror_robustness_gate.md` |
| hand_role_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/hand_role_robustness_gate/flower_jump_hand_role_robustness_gate.md` |
| hand_label_flicker_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/hand_label_flicker_robustness_gate/flower_jump_hand_label_flicker_robustness_gate.md` |
| hand_dropout_burst_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/hand_dropout_burst_robustness_gate/flower_jump_hand_dropout_burst_robustness_gate.md` |
| frame_count_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/frame_count_robustness_gate/flower_jump_frame_count_robustness_gate.md` |
| temporal_stutter_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/temporal_stutter_robustness_gate/flower_jump_temporal_stutter_robustness_gate.md` |
| temporal_rate_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/temporal_rate_robustness_gate/flower_jump_temporal_rate_robustness_gate.md` |
| composite_browser_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/composite_browser_robustness_gate/flower_jump_composite_browser_robustness_gate.md` |
| frame_weight_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/frame_weight_robustness_gate/flower_jump_frame_weight_robustness_gate.md` |
| coordinate_precision_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/coordinate_precision_robustness_gate/flower_jump_coordinate_precision_robustness_gate.md` |
| motion_blur_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/motion_blur_robustness_gate/flower_jump_motion_blur_robustness_gate.md` |
| landmark_noise_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/landmark_noise_robustness_gate/flower_jump_landmark_noise_robustness_gate.md` |
| landmark_spike_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/landmark_spike_robustness_gate/flower_jump_landmark_spike_robustness_gate.md` |
| fingertip_occlusion_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/fingertip_occlusion_robustness_gate/flower_jump_fingertip_occlusion_robustness_gate.md` |
| palm_anchor_occlusion_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/palm_anchor_occlusion_robustness_gate/flower_jump_palm_anchor_occlusion_robustness_gate.md` |
| hand_shape_scale_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/hand_shape_scale_robustness_gate/flower_jump_hand_shape_scale_robustness_gate.md` |
| hand_orientation_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/hand_orientation_robustness_gate/flower_jump_hand_orientation_robustness_gate.md` |
| missing_mask_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/missing_mask_robustness_gate/flower_jump_missing_mask_robustness_gate.md` |
| temporal_padding_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/temporal_padding_robustness_gate/flower_jump_temporal_padding_robustness_gate.md` |
| action_crop_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/action_crop_robustness_gate/flower_jump_action_crop_robustness_gate.md` |
| action_repeat_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/action_repeat_robustness_gate/flower_jump_action_repeat_robustness_gate.md` |
| phase_order_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/phase_order_robustness_gate/flower_jump_phase_order_robustness_gate.md` |
| noncore_hand_distractor_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/noncore_hand_distractor_robustness_gate/flower_jump_noncore_hand_distractor_robustness_gate.md` |
| relation_geometry_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/relation_geometry_robustness_gate/flower_jump_relation_geometry_robustness_gate.md` |
| core_shape_amplitude_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/core_shape_amplitude_robustness_gate/flower_jump_core_shape_amplitude_robustness_gate.md` |
| perspective_shear_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/perspective_shear_robustness_gate/flower_jump_perspective_shear_robustness_gate.md` |
| interhand_temporal_desync_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/interhand_temporal_desync_robustness_gate/flower_jump_interhand_temporal_desync_robustness_gate.md` |
| temporal_order_jitter_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/temporal_order_jitter_robustness_gate/flower_jump_temporal_order_jitter_robustness_gate.md` |
| finger_identity_jitter_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/finger_identity_jitter_robustness_gate/flower_jump_finger_identity_jitter_robustness_gate.md` |
| hand_scale_flicker_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/hand_scale_flicker_robustness_gate/flower_jump_hand_scale_flicker_robustness_gate.md` |
| hand_center_flicker_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/hand_center_flicker_robustness_gate/flower_jump_hand_center_flicker_robustness_gate.md` |
| global_framing_flicker_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/global_framing_flicker_robustness_gate/flower_jump_global_framing_flicker_robustness_gate.md` |
| finger_mid_joint_occlusion_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/finger_mid_joint_occlusion_robustness_gate/flower_jump_finger_mid_joint_occlusion_robustness_gate.md` |
| z_flicker_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/z_flicker_robustness_gate/flower_jump_z_flicker_robustness_gate.md` |
| hand_trajectory_interpolation_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/hand_trajectory_interpolation_robustness_gate/flower_jump_hand_trajectory_interpolation_robustness_gate.md` |
| hand_z_tilt_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/hand_z_tilt_robustness_gate/flower_jump_hand_z_tilt_robustness_gate.md` |
| finger_curl_style_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/finger_curl_style_robustness_gate/flower_jump_finger_curl_style_robustness_gate.md` |
| finger_length_style_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/finger_length_style_robustness_gate/flower_jump_finger_length_style_robustness_gate.md` |

## 网页保存样本回归

- replay 样本 `168`，错误 `0`；花/跳 diagnostics `149`，错误 `0`。
- 有效采集 `128`，有效正常+边界 `124`，有效低分 `4`，有效正常+边界率 `96.9%`。

| 词条 | 有效采集 | 正常+边界 | 有效低分 | 有效率 | 有效均分 |
|---|---:|---:|---:|---:|---:|
| 花 | 91 | 87 | 4 | 95.6% | 75.775 |
| 跳 | 37 | 37 | 0 | 100.0% | 76.677 |

## 网页保存样本花/跳交叉混淆门

- 样本 `149`，错误 `0`；eligible `124`，pass `124`，fail `0`。

| 目标词 | 样本 | eligible | pass | fail | 交叉最高 | margin 最低 | margin 均值 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 花 | 93 | 87 | 87 | 0 | 8.218 | 59.840 | 75.492 |
| 跳 | 56 | 37 | 37 | 0 | 41.535 | 29.317 | 54.894 |

## 合成鲁棒变体花/跳交叉混淆门

- 代表性正向扰动需保持目标词高分，同时按另一个词模板复评仍低分且 margin 足够。

| 目标词 | 状态 | cases | pass | fail | 目标最低 | 交叉最高 | margin 最低 | 最弱变体 |
|---|---|---:|---:|---:|---:|---:|---:|---|
| 花 | PASS | 10 | 10 | 0 | 76.727 | 8.506 | 70.776 | hand_noise_0.010_seed1 |
| 跳 | PASS | 10 | 10 | 0 | 70.708 | 25.551 | 55.428 | framing_shift_zoom_out |

## 负例判别门

| 目标词 | 状态 | 正例最低 | 最弱正例 | 负例最高 | 最强负例 | margin |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 80.311 | amplitude_0.85 | 33.735 | other_demo_谗_羡慕 | 46.575 |
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

## 宽高比失真鲁棒性门

- 轻中度非等比摄像头/画布拉伸需保持高分；极端拉伸仅记录诊断边界。

| 目标词 | 状态 | 正向最低分 | 最弱正向宽高比 | 诊断最低分 | 最弱诊断宽高比 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 80.345 | aspect_x0.85_y1.18 | 76.940 | diagnostic_x0.55_y1.55 | 75.000 |
| 跳 | PASS | 85.975 | aspect_x0.85_y1.18 | 55.282 | diagnostic_x1.55_y0.55 | 75.000 |

## 摄像头整体倾斜鲁棒性门

- 全身骨架 image-plane roll 后重建派生特征；±20 度内需保持高分，35/45 度极端倾斜仅记录诊断边界。

| 目标词 | 状态 | 正向最低分 | 最弱正向倾斜 | 诊断最低分 | 最弱诊断倾斜 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 81.180 | camera_roll_pos20deg | 80.849 | camera_roll_pos45deg_diagnostic | 75.000 |
| 跳 | PASS | 89.634 | camera_roll_neg20deg | 75.140 | camera_roll_neg45deg_diagnostic | 75.000 |

## 非核心身体锚点漂移鲁棒性门

- 仅扰动 pose/face 并保留手部核心语义；非核心身体/脸部锚点漂移、抖动或比例异常不应拖低 `花/跳`。

| 目标词 | 状态 | 正向最低分 | 最弱正向锚点漂移 | 诊断最低分 | 最弱诊断漂移 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 100.000 | self_recomputed | 100.000 | pose_face_jitter_0.35_diagnostic | 90.000 |
| 跳 | PASS | 100.000 | self_recomputed | 100.000 | pose_face_jitter_0.35_diagnostic | 90.000 |

## z/depth 深度鲁棒性门

- 中等 Holistic z 坐标偏移/缩放需保持高分；逐点 z 噪声和极端缩放仅记录诊断边界。

| 目标词 | 状态 | 正向最低分 | 最弱正向深度扰动 | 诊断最低分 | 最弱诊断深度扰动 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 73.923 | global_z_scale_0.50 | 13.117 | hand_z_noise_0.20_diagnostic | 70.000 |
| 跳 | PASS | 70.469 | global_z_scale_0.50 | 30.536 | hand_z_noise_0.10_diagnostic | 70.000 |

## z 深度时序抖动鲁棒性门

- 逐帧 Holistic z offset/scale breathing 和少量手部 z 跳动需保持高分；强 z 漂移只记录诊断边界。

| 目标词 | 状态 | 正向最低分 | 最弱正向 z 抖动 | 诊断最低分 | 最弱诊断 z 抖动 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 81.408 | smooth_global_z_scale_0.20 | 79.869 | strong_hand_z_scale_0.55_diagnostic | 70.000 |
| 跳 | PASS | 79.288 | smooth_global_z_offset_0.08 | 78.276 | strong_global_z_offset_0.25_diagnostic | 70.000 |

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
| 花 | PASS | 80.533 | mirror_x | 82.267 | swap_labels_diagnostic |
| 跳 | PASS | 80.843 | mirror_x | 31.053 | mirror_x_swap_labels_diagnostic |

## 手角色鲁棒性门

- `花` 作为单手主导词需支持左右惯用手；`跳` 作为双手角色词的地面手/跳跃手互换需低分或语义失败。负向质量口径：`['needs_recapture', 'semantic_mismatch']`。

| 目标词 | 状态 | 正向最低分 | 最弱正向角色变体 | 角色互换最高分 | 最强角色互换负例 |
|---|---|---:|---|---:|---|
| 花 | PASS | 80.533 | mirror_x | - | - |
| 跳 | PASS | 80.843 | mirror_x | 36.324 | role_swap_negative |

## 非核心手与非语义手指干扰鲁棒性门

- `花` 的非核心左手干扰、`跳` 的右手非语义手指干扰需保持高分；核心破坏仅记录诊断边界。

| 目标词 | 状态 | 正向最低分 | 最弱正向干扰 | 诊断最低分 | 最弱诊断核心扰动 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 100.000 | self_recomputed | 25.938 | flower_right_opening_tips_collapse_diagnostic | 70.000 |
| 跳 | PASS | 73.032 | jump_right_noncore_fingers_motion_drift | 81.460 | jump_right_index_middle_collapse_diagnostic | 70.000 |

## 双手关系几何鲁棒性门

- 温和右手相对位置、跳跃高度、横向轨迹和关系抖动需保持高分；`跳` 的过小高度/强水平化/反向关系需低分或语义失败。负向质量口径：`['needs_recapture', 'semantic_mismatch']`。

| 目标词 | 状态 | 正向最低分 | 最弱正向关系扰动 | 负向最高分 | 最强负向关系 | 诊断最低分 | 最弱诊断关系 | 门槛 |
|---|---|---:|---|---:|---|---:|---|---:|
| 花 | PASS | 79.772 | right_relation_jitter_0.035 | - | - | 79.250 | flower_relation_reverse_y_diagnostic | 70.000 |
| 跳 | PASS | 70.469 | right_relation_offset_x_0.15 | 93.960 | jump_relation_y_amplitude_0.45_negative | 74.458 | right_relation_y_amplitude_1.75_diagnostic | 70.000 |

## 核心手形幅度鲁棒性门

- `花` 的温和开花开合幅度变化需保持高分，严重不开花需低分或语义失败；`跳` 的两指小人温和局部形变需保持高分。负向质量口径：`['needs_recapture', 'semantic_mismatch']`。

| 目标词 | 状态 | 正向最低分 | 最弱正向核心形变 | 负向最高分 | 最强负向核心形变 | 诊断最低分 | 最弱诊断形变 | 门槛 |
|---|---|---:|---|---:|---|---:|---|---:|
| 花 | PASS | 79.334 | flower_opening_dynamic_0.75 | 49.353 | flower_opening_dynamic_0.45_negative | 77.639 | flower_opening_dynamic_0.60_diagnostic | 70.000 |
| 跳 | PASS | 77.830 | jump_two_finger_dynamic_1.15 | - | - | 82.090 | jump_two_finger_radial_0.45_diagnostic | 70.000 |

## 斜拍透视剪切鲁棒性门

- 轻中度 image-plane shear、z-to-x/y 透视偏移和局部手部剪切需保持高分；强剪切/强透视只记录诊断边界。

| 目标词 | 状态 | 正向最低分 | 最弱正向透视/剪切 | 诊断最低分 | 最弱诊断透视/剪切 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 80.018 | perspective_z_to_y_0.35 | 78.288 | diagnostic_z_to_x_0.80 | 70.000 |
| 跳 | PASS | 88.573 | perspective_z_to_x_0.35 | 77.705 | diagnostic_combo_shear_0.18_zx_0.60 | 70.000 |

## 左右手标签抖动鲁棒性门

- 单帧或稀疏 handedness flicker 需保持可评分；持续或交替 flicker 需低分并进入重采/语义失败。负向质量口径：`['needs_recapture', 'semantic_mismatch']`。

| 目标词 | 状态 | 正向最低分 | 最弱正向 flicker | 负向最高分 | 最强负向 flicker |
|---|---|---:|---|---:|---|
| 花 | PASS | 96.804 | sparse_label_flicker | 27.593 | sustained_core_label_flicker_negative |
| 跳 | PASS | 70.469 | single_frame_label_flicker | 14.618 | alternating_label_flicker_negative |

## 连续手部检出空洞鲁棒性门

- 短 burst hand detector 空洞需保持可评分；持续核心手空洞需低分并进入重采/语义失败。负向质量口径：`['needs_recapture', 'semantic_mismatch']`。

| 目标词 | 状态 | 正向最低分 | 最弱正向空洞 | 持续空洞最高分 | 最强持续空洞 |
|---|---|---:|---|---:|---|
| 花 | PASS | 95.170 | right_core_15pct_mid | 55.975 | right_core_25pct_mid_negative |
| 跳 | PASS | 74.629 | right_jump_3f_mid | 18.484 | both_hands_2f_mid_negative |

## 帧数与采样密度扰动门

| 目标词 | 状态 | 推荐最少帧 | 最低分 | 最弱采样 | 门槛 | 欠采样最低分 |
|---|---|---:|---:|---|---:|---:|
| 花 | PASS | 12 | 78.482 | uniform_12f | 70.000 | 32.284 |
| 跳 | PASS | 6 | 70.488 | drop_every_3_keep_ends | 70.000 | - |

## 时序帧冻结 stutter 鲁棒性门

- 固定上传帧数内的短 burst 或稀疏重复帧需保持可评分；持续核心动作冻结需低分并进入重采/语义失败。负向质量口径：`['needs_recapture', 'semantic_mismatch']`。

| 目标词 | 状态 | 正向最低分 | 最弱正向 stutter | 持续冻结最高分 | 最强持续冻结 | 诊断最低分 | 最弱诊断边界 |
|---|---|---:|---|---:|---|---:|---|
| 花 | PASS | 93.869 | freeze_mid_15pct | 41.635 | freeze_mid_50pct_negative | 87.915 | freeze_mid_25pct_diagnostic |
| 跳 | PASS | 72.011 | freeze_mid_4f | 12.747 | freeze_mid_35pct_negative | 73.224 | freeze_mid_5f_diagnostic |

## 手部轨迹插值补洞鲁棒性门

- 短 tracker 插值补洞和稀疏插值帧需保持高分；更长连续补洞仅记录诊断边界。

| 目标词 | 状态 | 正向最低分 | 最弱正向插值 | 诊断最低分 | 最弱诊断插值 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 93.731 | right_hand_middle12_interp | 74.445 | right_hand_middle25_interp_diagnostic | 70.000 |
| 跳 | PASS | 82.672 | right_hand_middle12_interp | 77.316 | both_hands_middle25_interp_diagnostic | 70.000 |

## 时序速率鲁棒性门

- 同样帧数内局部速度变化、整体快慢变化和轻微采样间隔不均需保持高分；极端速率/内部缺口仅记录诊断边界。

| 目标词 | 状态 | 正向最低分 | 最弱正向速率扰动 | 诊断最低分 | 最弱诊断边界 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 92.730 | same_count_micro_rate_jitter | 94.439 | bloom_core_gap_diagnostic | 70.000 |
| 跳 | PASS | 77.195 | global_slow_1.50x | 80.007 | global_slow_2.25x_diagnostic | 70.000 |

## 组合网页扰动鲁棒性门

- 轻微宽高比、坐标量化、速率变化、短 stutter 和短手部检出缺口组合出现时需保持高分；强组合扰动仅记录诊断边界。

| 目标词 | 状态 | 正向最低分 | 最弱正向组合 | 诊断最低分 | 最弱诊断组合 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 77.955 | combo_slow_sparse_freeze_lowres | 69.472 | diagnostic_quantized_micro_jitter | 70.000 |
| 跳 | PASS | 73.632 | combo_fast_aspect_hand_quant | 74.006 | diagnostic_dropout_rate_stack | 70.000 |

## frame_weights 上传权重鲁棒性门

- 浏览器上传 motion 权重、轻微错位/噪声、宽泛前后段加权和无非均匀权重需保持高分；反向 motion 权重仅记录诊断。

| 目标词 | 状态 | 正向最低分 | 最弱正向权重 | 诊断最低分 | 最弱诊断权重 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 99.161 | back_loaded_broad_emphasis | 99.347 | inverted_dynamic_diagnostic | 70.000 |
| 跳 | PASS | 76.297 | back_loaded_broad_emphasis | 10.120 | inverted_dynamic_diagnostic | 70.000 |

## 坐标精度量化鲁棒性门

- 常见摄像头像素网格、归一化坐标精度和低分辨率取整需保持高分；极粗网格只记录诊断边界。

| 目标词 | 状态 | 正向最低分 | 最弱正向精度扰动 | 诊断最低分 | 最弱诊断精度扰动 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 80.805 | hand_xy_quantize_1_128 | 78.075 | severe_hand_xy_quantize_1_32_diagnostic | 70.000 |
| 跳 | PASS | 96.833 | hand_xy_quantize_1_128 | 84.267 | severe_hand_xy_quantize_1_32_diagnostic | 70.000 |

## 运动幅度与模糊诊断鲁棒性门

- 10%-15% 全身/手部运动幅度变化需保持高分；低通平滑可能抹掉 `花` 的 opening 动态，只记录诊断边界。

| 目标词 | 状态 | 正向最低分 | 最弱正向幅度变体 | 诊断最低分 | 最弱诊断平滑/模糊 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 79.074 | hand_motion_amplitude_0.85 | 10.092 | hand_motion_blur_5tap_heavy_diagnostic | 70.000 |
| 跳 | PASS | 75.662 | hand_motion_amplitude_0.85 | 70.351 | hand_motion_amplitude_0.55_diagnostic | 70.000 |

## Landmark 噪声鲁棒性门

- 小幅连续手部关键点抖动和稀少整帧手部不稳定需保持高分；严重噪声/逐点丢失仅记录诊断边界。

| 目标词 | 状态 | 正向最低分 | 最弱正向噪声 | 诊断最低分 | 最弱诊断噪声 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 76.064 | hand_noise_0.010_seed2 | 11.118 | severe_shuffle_diagnostic | 70.000 |
| 跳 | PASS | 72.810 | hand_noise_0.010_seed1 | 8.825 | severe_point_dropout_0.25_diagnostic | 70.000 |

## Landmark 跳点鲁棒性门

- 单帧或稀疏 hand landmark 大跳点需保持可评分；连续核心跳点和 landmark 顺序扰动仅记录诊断边界。

| 目标词 | 状态 | 正向最低分 | 最弱正向跳点 | 诊断最低分 | 最弱诊断跳点 |
|---|---|---:|---|---:|---|
| 花 | PASS | 92.772 | sparse_tip_spike_every_7th | 21.400 | alternating_tip_spike_diagnostic |
| 跳 | PASS | 70.469 | single_frame_tip_spike | 82.302 | alternating_tip_spike_diagnostic |

## 指尖遮挡鲁棒性门

- 负向样本质量口径：`['needs_recapture', 'semantic_mismatch']`；短时/稀疏 fingertip mask 丢失需保持高分，关键指尖全程缺失需低分或重采/语义失败。

| 目标词 | 状态 | 正向最低分 | 最弱正向遮挡 | 核心缺失最高分 | 最强核心缺失负例 | 诊断最低分 | 门槛 |
|---|---|---:|---|---:|---|---:|---:|
| 花 | PASS | 95.829 | middle20_all_tips | 11.133 | all_right_tips_negative | 75.986 | 70.000 |
| 跳 | PASS | 70.469 | sparse_all_tips | 10.010 | all_right_index_middle_negative | 76.758 | 70.000 |

## 掌根锚点遮挡鲁棒性门

- 负向样本质量口径：`['needs_recapture', 'semantic_mismatch']`；短时/稀疏 wrist/MCP palm-anchor mask 丢失需保持高分，核心掌根锚点全程缺失需低分或重采/语义失败。

| 目标词 | 状态 | 正向最低分 | 最弱正向锚点缺失 | 核心锚点全缺最高分 | 最强负例 | 诊断最低分 | 最弱诊断锚点缺失 | 门槛 |
|---|---|---:|---|---:|---|---:|---|---:|
| 花 | PASS | 95.791 | right_middle20_wrist_mcp_anchor | 11.140 | right_all_mcp_anchor_negative | 76.069 | right_core40_palm_anchor_diagnostic | 70.000 |
| 跳 | PASS | 70.469 | right_sparse_palm_anchor | 10.158 | left_all_palm_anchor_negative | 76.758 | right_core40_palm_anchor_diagnostic | 70.000 |

## 手指中段关节遮挡鲁棒性门

- 单帧、稀疏或局部中段 PIP/DIP/thumb-IP mask 丢失需保持高分；持续强缺失只记录诊断边界。

| 目标词 | 状态 | 正向最低分 | 最弱正向中段指节遮挡 | 诊断最低分 | 最弱诊断遮挡 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 99.437 | right_sparse_all_inner_joints | 97.559 | right_all_inner_joints_diagnostic | 70.000 |
| 跳 | PASS | 76.638 | right_middle20_index_middle_inner_joints | 70.469 | right_core40_index_middle_inner_joints_diagnostic | 70.000 |

## 手间时序错位鲁棒性门

- 单只手相对其它骨架组轻微提前/滞后需保持高分，强错位只记录诊断边界。

| 目标词 | 状态 | 正向最低分 | 最弱正向错位 | 诊断最低分 | 最弱诊断错位 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 99.023 | right_hand_delay_2f | 97.824 | right_hand_delay_4f_diagnostic | 70.000 |
| 跳 | PASS | 75.688 | left_hand_advance_1f | 75.809 | left_hand_delay_4f_diagnostic | 70.000 |

## 时序顺序抖动鲁棒性门

- 相邻帧交换和局部三帧错序需保持高分；块状倒序只记录诊断边界，硬拒绝由 phase-order 门覆盖。

| 目标词 | 状态 | 正向最低分 | 最弱正向抖动 | 诊断最低分 | 最弱诊断抖动 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 97.035 | adjacent_swap_every_6f | 97.068 | block_reverse_25pct_diagnostic | 70.000 |
| 跳 | PASS | 71.379 | adjacent_swap_every_6f | 45.000 | block_reverse_25pct_diagnostic | 70.000 |

## 手指身份抖动鲁棒性门

- 相邻 finger-chain 标签混淆和少量帧级手指身份抖动需保持高分；非相邻或多链强交换只记录诊断边界。

| 目标词 | 状态 | 正向最低分 | 最弱正向指链抖动 | 诊断最低分 | 最弱诊断抖动 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 79.043 | right_index_middle_chain_swap | 77.035 | right_index_ring_diagnostic | 70.000 |
| 跳 | PASS | 71.892 | right_middle_ring_sparse_jitter | 81.108 | right_thumb_index_diagnostic | 70.000 |

## 手部尺度时序呼吸鲁棒性门

- 逐帧 hand-box scale/aspect breathing 和少量 detector scale flicker 需保持高分；强尺度尖峰只记录诊断边界。

| 目标词 | 状态 | 正向最低分 | 最弱正向尺度呼吸 | 诊断最低分 | 最弱诊断尺度呼吸 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 81.932 | both_hands_smooth_aspect_breathing_0.10 | 81.395 | both_hands_strong_smooth_aspect_breathing_0.35_diagnostic | 70.000 |
| 跳 | PASS | 78.452 | both_hands_sparse_aspect_flicker_0.10_every_6f | 74.623 | both_hands_strong_smooth_uniform_breathing_0.35_diagnostic | 70.000 |

## 手部中心时序漂移鲁棒性门

- 逐帧 hand-box center wobble 和少量 detector center flicker 需保持高分；强中心跳点只记录诊断边界。

| 目标词 | 状态 | 正向最低分 | 最弱正向中心漂移 | 诊断最低分 | 最弱诊断中心漂移 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 82.112 | both_hands_smooth_center_y_0.04 | 81.773 | both_hands_strong_smooth_center_y_0.18_diagnostic | 70.000 |
| 跳 | PASS | 98.551 | right_hand_smooth_center_y_0.03 | 77.083 | both_hands_strong_smooth_center_y_0.18_diagnostic | 70.000 |

## 全局取景时序漂移鲁棒性门

- 整人画面级 pan/zoom 随时间漂移和少量自动取景跳点需保持高分；强 pan/zoom 跳点只记录诊断边界。

| 目标词 | 状态 | 正向最低分 | 最弱正向全局取景漂移 | 诊断最低分 | 最弱诊断全局取景漂移 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 81.919 | smooth_global_zoom_0.08 | 80.909 | strong_smooth_global_zoom_0.35_diagnostic | 70.000 |
| 跳 | PASS | 97.598 | sparse_global_zoom_0.06_every_6f | 76.830 | strong_smooth_global_pan_y_0.22_diagnostic | 70.000 |

## 手形局部尺度鲁棒性门

- 手部局部大小和轻微透视变化会重算 `*_hand_shape`；正向变体需保持高分，极端形变只记录诊断边界。

| 目标词 | 状态 | 正向最低分 | 最弱正向手形尺度 | 诊断最低分 | 最弱诊断尺度 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 80.339 | right_hand_aspect_x0.85_y1.20 | 76.902 | both_hands_aspect_x0.55_y1.60_diagnostic | 70.000 |
| 跳 | PASS | 86.403 | right_hand_aspect_x0.85_y1.20 | 69.697 | both_hands_uniform_scale_0.55_diagnostic | 70.000 |

## 手部局部旋转鲁棒性门

- 手腕/手部局部角度变化会重算 `*_hand_shape`；正向变体需保持高分，极端旋转只记录诊断边界。

| 目标词 | 状态 | 正向最低分 | 最弱正向旋转 | 诊断最低分 | 最弱诊断旋转 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 81.336 | both_hands_rotate_pos20deg | 81.162 | both_hands_rotate_pos45deg_diagnostic | 70.000 |
| 跳 | PASS | 84.409 | both_hands_rotate_neg20deg | 81.149 | both_hands_rotate_pos45deg_diagnostic | 70.000 |

## 手部 z 倾角鲁棒性门

- 手掌轻微出平面俯仰/侧倾会重算 hand-shape、motion 和 two-hand relation；强倾角只记录诊断边界。

| 目标词 | 状态 | 正向最低分 | 最弱正向 z 倾角 | 诊断最低分 | 最弱诊断 z 倾角 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 81.396 | right_hand_pitch_xz_pos12deg | 81.165 | right_hand_yaw_yz_neg35deg_diagnostic | 70.000 |
| 跳 | PASS | 98.093 | right_hand_pitch_xz_neg12deg | 92.212 | right_hand_yaw_yz_neg35deg_diagnostic | 70.000 |

## 手指弯曲风格鲁棒性门

- 轻微手指弯曲风格会重算 hand-shape、motion 和 two-hand relation；强弯曲只记录诊断边界。

| 目标词 | 状态 | 正向最低分 | 最弱正向弯曲 | 诊断最低分 | 最弱诊断弯曲 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 80.887 | right_opening_ring_pinky_curl_0.16 | 79.541 | right_opening_all_fingers_curl_0.38_diagnostic | 70.000 |
| 跳 | PASS | 92.938 | right_person_index_middle_curl_0.16 | 82.206 | right_person_index_middle_curl_0.50_diagnostic | 70.000 |

## 手指长度比例鲁棒性门

- 轻微手指长度/比例风格会重算 hand-shape、motion 和 two-hand relation；强比例变化只记录诊断边界。

| 目标词 | 状态 | 正向最低分 | 最弱正向比例 | 诊断最低分 | 最弱诊断比例 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 80.849 | right_opening_ring_pinky_length_1.12 | 79.378 | right_opening_all_finger_length_1.30_diagnostic | 70.000 |
| 跳 | PASS | 93.587 | right_person_index_middle_length_1.10 | 70.331 | right_person_index_middle_length_1.35_diagnostic | 70.000 |

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

## 重复动作录制鲁棒性门

- 一次网页录制里多做一遍、先试半遍再完整做、或完整后又开始下一遍时需保持高分；setup-only 极短片段需低分或重采/语义失败。

| 目标词 | 状态 | 正向最低分 | 最弱正向重复 | 不完整最高分 | 最强不完整负例 | 诊断分数范围 | 门槛 |
|---|---|---:|---|---:|---|---|---:|
| 花 | PASS | 96.505 | repeat_full_2x_mid_pause | 21.902 | setup_only_35pct_negative | 77.686 - 95.417 | 70.000 |
| 跳 | PASS | 81.950 | core_repeat_middle | 12.239 | landing_only_35pct_negative | 77.868 - 77.868 | 70.000 |

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

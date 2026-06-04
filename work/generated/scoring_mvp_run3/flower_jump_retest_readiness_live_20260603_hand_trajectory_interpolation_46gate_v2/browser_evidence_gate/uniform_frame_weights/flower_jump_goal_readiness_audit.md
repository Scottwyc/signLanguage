# 花/跳网页评分目标完成度审计

- 生成时间：`2026-06-03T23:11:32`
- 目标完成状态：`NOT_READY`
- 分层状态：运行态 `PASS`；算法质量 `PASS`；真实复测 `MISSING`。
- 当前阻塞：`fresh_real_webcam_target_samples_diagnosed`
- 状态说明：算法质量门和运行态已就绪，仍缺 marker 后真实网页摄像头花/跳样本诊断。
- 口径：快速审计，不重新运行 Holistic，不重跑 DTW gate；读取当前运行态和最新质量门报告。

## 分层就绪状态

| 层级 | 状态 | 相关证据门 | 缺失项 |
|---|---|---|---|
| 运行态 | PASS | `backend_ready, watcher_online, marker_available` | `-` |
| 算法质量 | PASS | `combined_quality_gate_passed` | `-` |
| 真实网页复测 | MISSING | `fresh_real_webcam_target_samples_diagnosed` | `fresh_real_webcam_target_samples_diagnosed` |

## 证据门

| gate | 状态 | 说明 |
|---|---|---|
| backend_ready | PASS | worker=ready, pid=811485, reload_count=15, last_reload_error=None |
| watcher_online | PASS | event=diagnose_done, watcher_pid=1, generated_at=2026-06-03T23:11:30 |
| marker_available | PASS | last_request_id=web_20260602_233348_53e3df5d, marker_after_new=0, target_new=0 |
| combined_quality_gate_passed | PASS | quality_gate=work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_hand_trajectory_interpolation_46gate_v1/flower_jump_quality_gate.json, subgates=[('web_regression', True), ('web_confusion_gate', True), ('synthetic_confusion_robustness_gate', True), ('discrimination_gate', True), ('pose_robustness_gate', True), ('framing_robustness_gate', True), ('aspect_ratio_robustness_gate', True), ('camera_roll_robustness_gate', True), ('body_anchor_robustness_gate', True), ('depth_robustness_gate', True), ('edge_clipping_robustness_gate', True), ('mirror_robustness_gate', True), ('hand_role_robustness_gate', True), ('hand_label_flicker_robustness_gate', True), ('hand_dropout_burst_robustness_gate', True), ('frame_count_robustness_gate', True), ('temporal_stutter_robustness_gate', True), ('temporal_rate_robustness_gate', True), ('composite_browser_robustness_gate', True), ('frame_weight_robustness_gate', True), ('coordinate_precision_robustness_gate', True), ('motion_blur_robustness_gate', True), ('landmark_noise_robustness_gate', True), ('landmark_spike_robustness_gate', True), ('fingertip_occlusion_robustness_gate', True), ('palm_anchor_occlusion_robustness_gate', True), ('hand_shape_scale_robustness_gate', True), ('hand_orientation_robustness_gate', True), ('missing_mask_robustness_gate', True), ('temporal_padding_robustness_gate', True), ('action_crop_robustness_gate', True), ('action_repeat_robustness_gate', True), ('phase_order_robustness_gate', True), ('noncore_hand_distractor_robustness_gate', True), ('relation_geometry_robustness_gate', True), ('core_shape_amplitude_robustness_gate', True), ('perspective_shear_robustness_gate', True), ('interhand_temporal_desync_robustness_gate', True), ('temporal_order_jitter_robustness_gate', True), ('finger_identity_jitter_robustness_gate', True), ('hand_scale_flicker_robustness_gate', True), ('hand_center_flicker_robustness_gate', True), ('global_framing_flicker_robustness_gate', True), ('finger_mid_joint_occlusion_robustness_gate', True), ('z_flicker_robustness_gate', True), ('hand_trajectory_interpolation_robustness_gate', True)] |
| fresh_real_webcam_target_samples_diagnosed | MISSING | marker_after_target_count=0, latest_diagnosis={'generated_at': '2026-06-03T23:11:30', 'web_root': '', 'diagnosed_request_ids': ['web_20260602_233343_899e6970', 'web_20260602_233348_53e3df5d'], 'regression_returncode': 0, 'confusion_returncode': 0, 'visual_returncode': 0}, diagnosis_scope={'passed': True, 'mode': 'marker_after_target_set', 'diagnosed_request_ids': ['web_20260602_233343_899e6970', 'web_20260602_233348_53e3df5d'], 'target_request_ids': ['web_20260602_233343_899e6970', 'web_20260602_233348_53e3df5d'], 'current_marker_id': 'web_20260602_233348_53e3df5d', 'latest_diagnosed_id': 'web_20260602_233348_53e3df5d'}, browser_capture_evidence={'request_ids': ['web_20260602_233343_899e6970', 'web_20260602_233348_53e3df5d'], 'passed': False, 'sample_evidence_passed': False, 'allow_legacy_browser_evidence': False, 'required_words': ['花', '跳'], 'observed_words': [], 'required_words_covered': False, 'missing_required_words': ['花', '跳'], 'rows': [{'request_id': 'web_20260602_233343_899e6970', 'path': 'work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_hand_trajectory_interpolation_46gate_v2/browser_evidence_gate/fixtures/uniform_frame_weights/web_20260602_233343_899e6970/scoring_result.json', 'exists': True, 'passed': False, 'reason': 'source_metadata_missing', 'target_word': '花', 'client_source': '', 'worker_mode': 'frame_slices', 'frame_count': 53, 'min_required_frames': 12, 'timeline_frame_count': 105, 'duration_sec': 5.3, 'capture_fps': 10.0, 'has_frame_weights': True, 'nonuniform_frame_weights': False, 'has_frame_indices': True, 'explicit_source_ok': False, 'weighted_source_ok': False, 'legacy_source_ok': False, 'diagnostic_compatible': False, 'completion_source_ok': False, 'evidence_level': 'none'}, {'request_id': 'web_20260602_233348_53e3df5d', 'path': 'work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_hand_trajectory_interpolation_46gate_v2/browser_evidence_gate/fixtures/uniform_frame_weights/web_20260602_233348_53e3df5d/scoring_result.json', 'exists': True, 'passed': False, 'reason': 'source_metadata_missing', 'target_word': '跳', 'client_source': '', 'worker_mode': 'frame_slices', 'frame_count': 19, 'min_required_frames': 6, 'timeline_frame_count': 37, 'duration_sec': 1.9, 'capture_fps': 10.0, 'has_frame_weights': True, 'nonuniform_frame_weights': False, 'has_frame_indices': True, 'explicit_source_ok': False, 'weighted_source_ok': False, 'legacy_source_ok': False, 'diagnostic_compatible': False, 'completion_source_ok': False, 'evidence_level': 'none'}]} |

## 最新质量门摘要

- 报告：`work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_hand_trajectory_interpolation_46gate_v1/flower_jump_quality_gate.md`
- 综合状态：`PASS`
- 子门：`web_regression`=PASS，`web_confusion_gate`=PASS，`synthetic_confusion_robustness_gate`=PASS，`discrimination_gate`=PASS，`pose_robustness_gate`=PASS，`framing_robustness_gate`=PASS，`aspect_ratio_robustness_gate`=PASS，`camera_roll_robustness_gate`=PASS，`body_anchor_robustness_gate`=PASS，`depth_robustness_gate`=PASS，`edge_clipping_robustness_gate`=PASS，`mirror_robustness_gate`=PASS，`hand_role_robustness_gate`=PASS，`hand_label_flicker_robustness_gate`=PASS，`hand_dropout_burst_robustness_gate`=PASS，`frame_count_robustness_gate`=PASS，`temporal_stutter_robustness_gate`=PASS，`temporal_rate_robustness_gate`=PASS，`composite_browser_robustness_gate`=PASS，`frame_weight_robustness_gate`=PASS，`coordinate_precision_robustness_gate`=PASS，`motion_blur_robustness_gate`=PASS，`landmark_noise_robustness_gate`=PASS，`landmark_spike_robustness_gate`=PASS，`fingertip_occlusion_robustness_gate`=PASS，`palm_anchor_occlusion_robustness_gate`=PASS，`hand_shape_scale_robustness_gate`=PASS，`hand_orientation_robustness_gate`=PASS，`missing_mask_robustness_gate`=PASS，`temporal_padding_robustness_gate`=PASS，`action_crop_robustness_gate`=PASS，`action_repeat_robustness_gate`=PASS，`phase_order_robustness_gate`=PASS，`noncore_hand_distractor_robustness_gate`=PASS，`relation_geometry_robustness_gate`=PASS，`core_shape_amplitude_robustness_gate`=PASS，`perspective_shear_robustness_gate`=PASS，`interhand_temporal_desync_robustness_gate`=PASS，`temporal_order_jitter_robustness_gate`=PASS，`finger_identity_jitter_robustness_gate`=PASS，`hand_scale_flicker_robustness_gate`=PASS，`hand_center_flicker_robustness_gate`=PASS，`global_framing_flicker_robustness_gate`=PASS，`finger_mid_joint_occlusion_robustness_gate`=PASS，`z_flicker_robustness_gate`=PASS，`hand_trajectory_interpolation_robustness_gate`=PASS。
- 网页回归：replay `168` / diagnostics `149`，有效 `128`，正常+边界 `124`，有效低分 `4`，有效率 `96.9%`。
- 交叉混淆：samples `149`，eligible `124`，pass `124`，fail `0`。
- 交叉混淆 `花`：other_score_max `8.218`，margin_min `59.840`。
- 交叉混淆 `跳`：other_score_max `41.535`，margin_min `29.317`。
- 负例判别 `花`：min_positive `80.311`，max_negative `33.735`，margin `46.575`。
- 负例判别 `跳`：min_positive `76.823`，max_negative `31.418`，margin `45.406`。
- 坐姿扰动 `花`：min `80.446`，weakest `hand_jitter_small`。
- 坐姿扰动 `跳`：min `93.015`，weakest `hand_jitter_small`。
- 帧数采样 `花`：min_valid_frames `12`，min `78.482`，weakest `uniform_12f`。
- 帧数采样 `跳`：min_valid_frames `6`，min `70.488`，weakest `drop_every_3_keep_ends`。
- 缺失/mask `花`：positive_min `100.000`，critical_missing_max `1.171`。
- 缺失/mask `跳`：positive_min `100.000`，critical_missing_max `3.037`。
- 静止 padding `花`：positive_min `97.862`，static_max `1.460`。
- 静止 padding `跳`：positive_min `79.124`，static_max `31.418`。
- 相位顺序 `花`：positive_min `79.410`，disordered_max `33.723`。
- 相位顺序 `跳`：positive_min `69.389`，disordered_max `45.000`。

## 当前 marker

- last_request_id：`web_20260602_233348_53e3df5d`
- marker 后新增样本：`0`
- marker 后新增花/跳样本：`0`

## 真实网页采集证据

- 综合状态：`MISSING`
- 样本证据状态：`MISSING`
- 要求覆盖词条：`花, 跳`
- 已覆盖词条：`-`
- 缺失词条：`花, 跳`

| request | 词条 | 状态 | 证据等级 | 原因 | source | 帧数 | 权重 | fps | duration |
|---|---|---|---|---|---|---:|---|---:|---:|
| web_20260602_233343_899e6970 | 花 | MISSING | none | source_metadata_missing | - | 53 | present | 10.00 | 5.30 |
| web_20260602_233348_53e3df5d | 跳 | MISSING | none | source_metadata_missing | - | 19 | present | 10.00 | 1.90 |

## 结论

- 当前运行态和算法质量门已经通过，但还没有新的真实网页摄像头 `花/跳` 样本诊断证据。
- 下一步仍需用户通过 5080 页面实际采集 `花/跳`，由 watcher 自动生成增量回归和骨架可视化后再复查。

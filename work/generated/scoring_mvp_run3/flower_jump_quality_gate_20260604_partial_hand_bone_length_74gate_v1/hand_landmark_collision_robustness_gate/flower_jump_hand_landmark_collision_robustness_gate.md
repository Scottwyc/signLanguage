# 花/跳 Hand Landmark 碰撞完整性鲁棒性门

- 生成时间：`2026-06-04T19:46:54`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 碰撞边界：三维距离 `<= 1e-05` 的参与点按歧义点局部屏蔽；完整手若符合已知全局量化网格则保留。
- 正常证据审计：`178` 个模板/网页 JSON、`4750` 个非空手帧，原始碰撞帧 `0`，最小正常点间距 `0.00014560438285116106`。
- 全局量化签名：原始误命中 `0`；候选步长 `(0.0009765625, 0.0015625, 0.001953125, 0.0020833333333333333, 0.003125, 0.00390625, 0.004166666666666667)`，归一残差上限 `0.0005`。
- 量化兼容审计：`{'camera_640x480_z1024': {'collision_frame_count': 105, 'max_collision_participant_count': 8, 'max_collision_cluster_size': 3, 'quantization_signature_violation_count': 0, 'quantization_bypass_violation_count': 0}, 'camera_320x240_z512': {'collision_frame_count': 444, 'max_collision_participant_count': 13, 'max_collision_cluster_size': 4, 'quantization_signature_violation_count': 0, 'quantization_bypass_violation_count': 0}, 'xyz_1_256': {'collision_frame_count': 689, 'max_collision_participant_count': 15, 'max_collision_cluster_size': 4, 'quantization_signature_violation_count': 0, 'quantization_bypass_violation_count': 0}}`。
- 口径：只写缓存 Holistic JSON fixture；不调用 `/api/score`、不运行 Holistic、不移动 marker、不重启 5080。

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向变体 | 核心碰撞诊断最高分 | 最强诊断变体 |
|---|---|---:|---|---:|---|
| 花 | PASS | 78.512 | right_hand_landmarks_xyz_1_256_raw_quantized | 10.731 | right_hand_landmarks_tip_to_dip_all_full_semantic_mismatch |
| 跳 | PASS | 70.714 | right_hand_landmarks_single_index_tip_to_dip_sparse_preserved | 9.307 | left_hand_landmarks_index_middle_to_index_mcp_full_semantic_mismatch |

## 分项明细

### 花

| 变体 | 类型 | 状态 | 分数 | 阈值 | 碰撞帧 | 参与点范围 | 最大簇 | 屏蔽处理率 | 最少剩余点 | capture_quality |
|---|---|---|---:|---:|---:|---|---:|---:|---:|---|
| self_reloaded | positive | PASS | 100.000 | 95.000 | 0 | - | None | - | None | score_valid:score_valid |
| right_hand_landmarks_tip_to_dip_all_sparse_preserved | positive | PASS | 98.833 | 75.000 | 6 | 10-10 | 2 | 1.000 | 11 | score_valid:score_valid |
| right_hand_landmarks_tip_to_dip_all_full_semantic_mismatch | diagnostic | PASS | 10.731 | 55.000 | 40 | 10-10 | 2 | 1.000 | 11 | semantic_mismatch:flower_opening_guard_failed |
| right_hand_landmarks_dip_tip_to_pip_all_sparse_preserved | positive | PASS | 98.713 | 75.000 | 6 | 15-15 | 3 | 1.000 | 6 | score_valid:score_valid |
| right_hand_landmarks_dip_tip_to_pip_all_full_semantic_mismatch | diagnostic | PASS | 10.529 | 55.000 | 40 | 15-15 | 3 | 1.000 | 6 | semantic_mismatch:flower_opening_guard_failed |
| right_hand_landmarks_distal_to_mcp_all_sparse_preserved | positive | PASS | 98.507 | 75.000 | 6 | 20-20 | 4 | 1.000 | 1 | score_valid:score_valid |
| right_hand_landmarks_distal_to_mcp_all_full_semantic_mismatch | diagnostic | PASS | 10.076 | 55.000 | 40 | 20-20 | 4 | 1.000 | 1 | semantic_mismatch:flower_opening_guard_failed |
| right_hand_landmarks_index_middle_to_index_mcp_sparse_preserved | positive | PASS | 97.852 | 75.000 | 6 | 8-8 | 8 | 1.000 | 13 | score_valid:score_valid |
| right_hand_landmarks_index_middle_to_index_mcp_full_noncore_preserved | positive | PASS | 80.961 | 75.000 | 40 | 8-8 | 8 | 1.000 | 13 | score_valid:score_valid |
| right_hand_landmarks_all_tips_to_wrist_full_local_mask | handling | PASS | 10.902 | - | 40 | 6-6 | 6 | 1.000 | 15 | semantic_mismatch:flower_opening_guard_failed |
| right_hand_landmarks_all_mcps_to_wrist_full_local_mask | handling | PASS | 10.937 | - | 40 | 6-6 | 6 | 1.000 | 15 | semantic_mismatch:flower_opening_guard_failed |
| right_hand_landmarks_single_index_tip_to_dip_sparse_preserved | positive | PASS | 99.484 | 70.000 | 6 | 2-2 | 2 | 1.000 | 19 | score_valid:score_valid |
| right_hand_landmarks_camera_640x480_z1024_raw_quantized | positive | PASS | 80.857 | 70.000 | 1 | 0-4 | 2 | 1.000 | 21 | score_valid:score_valid |
| right_hand_landmarks_camera_320x240_z512_raw_quantized | positive | PASS | 78.809 | 70.000 | 5 | 0-7 | 3 | 1.000 | 21 | score_valid:score_valid |
| right_hand_landmarks_xyz_1_256_raw_quantized | positive | PASS | 78.512 | 70.000 | 7 | 0-11 | 3 | 1.000 | 21 | score_valid:score_valid |

### 跳

| 变体 | 类型 | 状态 | 分数 | 阈值 | 碰撞帧 | 参与点范围 | 最大簇 | 屏蔽处理率 | 最少剩余点 | capture_quality |
|---|---|---|---:|---:|---:|---|---:|---:|---:|---|
| self_reloaded | positive | PASS | 100.000 | 95.000 | 0 | - | None | - | None | score_valid:score_valid |
| right_hand_landmarks_tip_to_dip_all_sparse_preserved | positive | PASS | 81.642 | 75.000 | 2 | 10-10 | 2 | 1.000 | 11 | score_valid:score_valid |
| right_hand_landmarks_tip_to_dip_all_full_semantic_mismatch | diagnostic | PASS | 1.535 | 55.000 | 17 | 10-10 | 2 | 1.000 | 11 | semantic_mismatch:missing_relation_delta |
| right_hand_landmarks_dip_tip_to_pip_all_sparse_preserved | positive | PASS | 81.642 | 75.000 | 2 | 15-15 | 3 | 1.000 | 6 | score_valid:score_valid |
| right_hand_landmarks_dip_tip_to_pip_all_full_semantic_mismatch | diagnostic | PASS | 1.255 | 55.000 | 17 | 15-15 | 3 | 1.000 | 6 | semantic_mismatch:missing_relation_delta |
| right_hand_landmarks_distal_to_mcp_all_sparse_preserved | positive | PASS | 81.642 | 75.000 | 2 | 20-20 | 4 | 1.000 | 1 | score_valid:score_valid |
| right_hand_landmarks_distal_to_mcp_all_full_semantic_mismatch | diagnostic | PASS | 0.972 | 55.000 | 17 | 20-20 | 4 | 1.000 | 1 | semantic_mismatch:phase_order_disorder |
| right_hand_landmarks_index_middle_to_index_mcp_sparse_preserved | positive | PASS | 81.367 | 75.000 | 2 | 8-8 | 8 | 1.000 | 13 | score_valid:score_valid |
| right_hand_landmarks_index_middle_to_index_mcp_full_semantic_mismatch | diagnostic | PASS | 4.589 | 55.000 | 17 | 8-8 | 8 | 1.000 | 13 | semantic_mismatch:missing_relation_delta |
| right_hand_landmarks_all_tips_to_wrist_full_local_mask | handling | PASS | 1.779 | - | 17 | 6-6 | 6 | 1.000 | 15 | semantic_mismatch:missing_relation_delta |
| right_hand_landmarks_all_mcps_to_wrist_full_local_mask | handling | PASS | 1.770 | - | 17 | 6-6 | 6 | 1.000 | 15 | semantic_mismatch:missing_relation_delta |
| right_hand_landmarks_single_index_tip_to_dip_sparse_preserved | positive | PASS | 70.714 | 70.000 | 2 | 2-2 | 2 | 1.000 | 19 | score_valid:score_valid |
| right_hand_landmarks_camera_640x480_z1024_raw_quantized | positive | PASS | 74.783 | 70.000 | 1 | 0-2 | 2 | 1.000 | 21 | score_valid:score_valid |
| right_hand_landmarks_camera_320x240_z512_raw_quantized | positive | PASS | 89.623 | 70.000 | 9 | 0-2 | 2 | 1.000 | 21 | score_valid:score_valid |
| right_hand_landmarks_xyz_1_256_raw_quantized | positive | PASS | 78.551 | 70.000 | 10 | 0-6 | 2 | 1.000 | 21 | score_valid:score_valid |
| left_hand_landmarks_tip_to_dip_all_sparse_preserved | positive | PASS | 97.503 | 75.000 | 2 | 10-10 | 2 | 1.000 | 11 | score_valid:score_valid |
| left_hand_landmarks_tip_to_dip_all_full_noncore_preserved | positive | PASS | 85.000 | 75.000 | 16 | 10-10 | 2 | 1.000 | 11 | score_valid:score_valid |
| left_hand_landmarks_dip_tip_to_pip_all_sparse_preserved | positive | PASS | 96.845 | 75.000 | 2 | 15-15 | 3 | 1.000 | 6 | score_valid:score_valid |
| left_hand_landmarks_dip_tip_to_pip_all_full_noncore_preserved | positive | PASS | 85.000 | 75.000 | 16 | 15-15 | 3 | 1.000 | 6 | score_valid:score_valid |
| left_hand_landmarks_distal_to_mcp_all_sparse_preserved | positive | PASS | 88.903 | 75.000 | 2 | 20-20 | 4 | 1.000 | 1 | score_valid:score_valid |
| left_hand_landmarks_distal_to_mcp_all_full_semantic_mismatch | diagnostic | PASS | 6.762 | 55.000 | 16 | 20-20 | 4 | 1.000 | 1 | semantic_mismatch:missing_relation_delta |
| left_hand_landmarks_index_middle_to_index_mcp_sparse_preserved | positive | PASS | 89.922 | 75.000 | 2 | 8-8 | 8 | 1.000 | 13 | score_valid:score_valid |
| left_hand_landmarks_index_middle_to_index_mcp_full_semantic_mismatch | diagnostic | PASS | 9.307 | 55.000 | 16 | 8-8 | 8 | 1.000 | 13 | semantic_mismatch:missing_relation_delta |
| left_hand_landmarks_all_tips_to_wrist_full_local_mask | handling | PASS | 8.710 | - | 16 | 6-6 | 6 | 1.000 | 15 | semantic_mismatch:missing_relation_delta |
| left_hand_landmarks_all_mcps_to_wrist_full_local_mask | handling | PASS | 8.685 | - | 16 | 6-6 | 6 | 1.000 | 15 | semantic_mismatch:missing_relation_delta |
| left_hand_landmarks_single_index_tip_to_dip_sparse_preserved | positive | PASS | 99.436 | 70.000 | 2 | 2-2 | 2 | 1.000 | 19 | score_valid:score_valid |
| left_hand_landmarks_camera_640x480_z1024_raw_quantized | positive | PASS | 75.419 | 70.000 | 2 | 0-2 | 2 | 1.000 | 21 | score_valid:score_valid |
| left_hand_landmarks_camera_320x240_z512_raw_quantized | positive | PASS | 96.505 | 70.000 | 12 | 0-11 | 3 | 1.000 | 21 | score_valid:score_valid |
| left_hand_landmarks_xyz_1_256_raw_quantized | positive | PASS | 96.132 | 70.000 | 15 | 0-13 | 3 | 1.000 | 21 | score_valid:score_valid |

## 说明

- 非量化手只屏蔽碰撞参与点；不能按碰撞参与点总数丢弃整手，因为合理坐标量化也会产生多个重复点。
- 正常原始证据零碰撞和零全局量化签名误命中是硬门；量化审计验证已知网格完整保留。
- 该门补充 wrist 身份、内部拓扑和坐标精度门，不替代正式 marker 后真实网页摄像头复测。

# 花/跳 Hand 骨段长度完整性鲁棒性门

- 生成时间：`2026-06-04T17:51:34`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 保守边界：相邻指骨长度 / 掌尺度必须在 `[0.003, 2.0]`；只屏蔽异常骨段参与点。
- 正常证据审计：`178` 个模板/网页 JSON、`4750` 个完整手帧、`71250` 条骨段，违反帧 `0`，正常范围 `0.00709768606550895`–`1.665053336757409`。
- 全局量化兼容：原始误命中 `0`；量化审计 `{'camera_640x480_z1024': {'hand_frame_count': 4750, 'quantization_signature_violation_count': 0, 'would_violate_without_bypass_count': 19, 'quantization_bypass_violation_count': 0}, 'camera_320x240_z512': {'hand_frame_count': 4750, 'quantization_signature_violation_count': 0, 'would_violate_without_bypass_count': 172, 'quantization_bypass_violation_count': 0}, 'xyz_1_256': {'hand_frame_count': 4750, 'quantization_signature_violation_count': 0, 'would_violate_without_bypass_count': 336, 'quantization_bypass_violation_count': 0}}`。
- 口径：只写缓存 Holistic JSON fixture；不调用 `/api/score`、不运行 Holistic、不移动 marker、不重启 5080。

## 结论

- 综合状态：`FAIL`

| 目标词 | 状态 | 正向最低分 | 最弱正向变体 | 整段损坏诊断最高分 | 最强诊断变体 |
|---|---|---:|---|---:|---|
| 花 | PASS | 78.512 | right_hand_landmarks_xyz_1_256_quantized_preserved | 10.731 | right_hand_landmarks_all_distal_long_full_recapture |
| 跳 | FAIL | 70.714 | right_hand_landmarks_single_index_tip_short_sparse_preserved | 85.000 | left_hand_landmarks_all_distal_long_full_recapture |

## 分项明细

### 花

| 变体 | 类型 | 状态 | 分数 | 阈值 | 损坏帧 | 量化旁路帧 | 最短比 | 最长比 | 处理率 | 最少剩余点 | capture_quality |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| self_reloaded | positive | PASS | 100.000 | 95.000 | 0 | 0 | - | - | - | None | score_valid:score_valid |
| right_hand_landmarks_all_edges_short_sparse_preserved | positive | PASS | 98.507 | 75.000 | 6 | 0 | 0.001 | 0.002 | 1.000 | 1 | score_valid:score_valid |
| right_hand_landmarks_all_edges_short_full_recapture | diagnostic | PASS | 10.076 | 55.000 | 40 | 0 | 0.001 | 0.002 | 1.000 | 1 | semantic_mismatch:flower_opening_guard_failed |
| right_hand_landmarks_all_distal_long_sparse_preserved | positive | PASS | 98.833 | 75.000 | 6 | 0 | 0.153 | 2.200 | 1.000 | 11 | score_valid:score_valid |
| right_hand_landmarks_all_distal_long_full_recapture | diagnostic | PASS | 10.731 | 55.000 | 40 | 0 | 0.097 | 2.200 | 1.000 | 11 | semantic_mismatch:flower_opening_guard_failed |
| right_hand_landmarks_single_index_tip_short_sparse_preserved | positive | PASS | 99.484 | 75.000 | 6 | 0 | 0.001 | 0.611 | 1.000 | 19 | score_valid:score_valid |
| right_hand_landmarks_xyz_1_256_quantized_preserved | positive | PASS | 78.512 | 70.000 | 0 | 40 | - | - | 1.000 | 21 | score_valid:score_valid |

### 跳

| 变体 | 类型 | 状态 | 分数 | 阈值 | 损坏帧 | 量化旁路帧 | 最短比 | 最长比 | 处理率 | 最少剩余点 | capture_quality |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| self_reloaded | positive | PASS | 100.000 | 95.000 | 0 | 0 | - | - | - | None | score_valid:score_valid |
| right_hand_landmarks_all_edges_short_sparse_preserved | positive | PASS | 81.642 | 75.000 | 2 | 0 | 0.001 | 0.001 | 1.000 | 1 | score_valid:score_valid |
| right_hand_landmarks_all_edges_short_full_recapture | diagnostic | PASS | 0.972 | 55.000 | 17 | 0 | 0.001 | 0.002 | 1.000 | 1 | semantic_mismatch:phase_order_disorder |
| right_hand_landmarks_all_distal_long_sparse_preserved | positive | PASS | 81.642 | 75.000 | 2 | 0 | 0.075 | 2.200 | 1.000 | 11 | score_valid:score_valid |
| right_hand_landmarks_all_distal_long_full_recapture | diagnostic | PASS | 1.535 | 55.000 | 17 | 0 | 0.067 | 2.200 | 1.000 | 11 | semantic_mismatch:missing_relation_delta |
| right_hand_landmarks_single_index_tip_short_sparse_preserved | positive | FAIL | 70.714 | 75.000 | 2 | 0 | 0.001 | 0.457 | 1.000 | 19 | score_valid:score_valid |
| right_hand_landmarks_xyz_1_256_quantized_preserved | positive | PASS | 78.551 | 70.000 | 0 | 17 | - | - | 1.000 | 21 | score_valid:score_valid |
| left_hand_landmarks_all_edges_short_sparse_preserved | positive | PASS | 88.903 | 75.000 | 2 | 0 | 0.001 | 0.002 | 1.000 | 1 | score_valid:score_valid |
| left_hand_landmarks_all_edges_short_full_recapture | diagnostic | PASS | 6.762 | 55.000 | 16 | 0 | 0.001 | 0.002 | 1.000 | 1 | semantic_mismatch:missing_relation_delta |
| left_hand_landmarks_all_distal_long_sparse_preserved | positive | PASS | 97.503 | 75.000 | 2 | 0 | 0.320 | 2.200 | 1.000 | 11 | score_valid:score_valid |
| left_hand_landmarks_all_distal_long_full_recapture | diagnostic | FAIL | 85.000 | 55.000 | 16 | 0 | 0.222 | 2.200 | 1.000 | 11 | score_valid:score_valid |
| left_hand_landmarks_single_index_tip_short_sparse_preserved | positive | PASS | 99.436 | 75.000 | 2 | 0 | 0.001 | 0.633 | 1.000 | 19 | score_valid:score_valid |
| left_hand_landmarks_xyz_1_256_quantized_preserved | positive | PASS | 96.132 | 70.000 | 0 | 16 | - | - | 1.000 | 21 | score_valid:score_valid |

## 说明

- 该规则只处理远离正常证据范围的极端局部伸缩；轻微 finger-length 风格变化继续由现有鲁棒性门覆盖。
- 完整全局量化手直接旁路，避免把坐标精度造成的零长度骨段误判为 tracker 损坏。
- 该门补充 landmark 碰撞和内部拓扑门，不替代正式 marker 后真实网页摄像头复测。

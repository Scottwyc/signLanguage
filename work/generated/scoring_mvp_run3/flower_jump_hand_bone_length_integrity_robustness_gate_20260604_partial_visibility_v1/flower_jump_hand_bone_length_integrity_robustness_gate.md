# 花/跳 Hand 骨段长度完整性鲁棒性门

- 生成时间：`2026-06-04T19:01:32`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 保守边界：相邻指骨长度 / 掌尺度必须在 `[0.003, 2.0]`；至少 `16` 个可见点、wrist 可见且至少 `3` 个掌参考时，按 median 掌尺度只屏蔽异常骨段参与点。
- 正常证据审计：`178` 个模板/网页 JSON、`4750` 个完整手帧、`71250` 条骨段，违反帧 `0`，正常范围 `0.006013596835018576`–`1.7403748621373394`。
- 部分可见手零误伤审计：`{'patterns': {'single_missing': {'pattern_count': 21, 'evaluated_case_count': 95000, 'skipped_case_count': 4750, 'violation_count': 0, 'mask_violation_count': 0, 'minimum_bone_length_ratio': 0.006002826351681463, 'maximum_bone_length_ratio': 1.8311995705984159, 'passed': True}, 'pair_missing': {'pattern_count': 210, 'evaluated_case_count': 878750, 'skipped_case_count': 118750, 'violation_count': 0, 'mask_violation_count': 0, 'minimum_bone_length_ratio': 0.006002826351681463, 'maximum_bone_length_ratio': 1.8311995705984159, 'passed': True}, 'common_multi_missing': {'pattern_count': 8, 'evaluated_case_count': 23750, 'skipped_case_count': 14250, 'violation_count': 0, 'mask_violation_count': 0, 'minimum_bone_length_ratio': 0.006013596835018576, 'maximum_bone_length_ratio': 1.7403748621373394, 'passed': True}}, 'passed': True}`。
- 全局量化兼容：原始误命中 `0`；量化审计 `{'camera_640x480_z1024': {'hand_frame_count': 4750, 'quantization_signature_violation_count': 0, 'would_violate_without_bypass_count': 19, 'quantization_bypass_violation_count': 0, 'partial_quantization_signature_violation_count': 0, 'partial_quantization_bypass_violation_count': 0}, 'camera_320x240_z512': {'hand_frame_count': 4750, 'quantization_signature_violation_count': 0, 'would_violate_without_bypass_count': 172, 'quantization_bypass_violation_count': 0, 'partial_quantization_signature_violation_count': 0, 'partial_quantization_bypass_violation_count': 0}, 'xyz_1_256': {'hand_frame_count': 4750, 'quantization_signature_violation_count': 0, 'would_violate_without_bypass_count': 336, 'quantization_bypass_violation_count': 0, 'partial_quantization_signature_violation_count': 0, 'partial_quantization_bypass_violation_count': 0}}`。
- 口径：只写缓存 Holistic JSON fixture；不调用 `/api/score`、不运行 Holistic、不移动 marker、不重启 5080。

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向变体 | 整段损坏诊断最高分 | 最强诊断变体 |
|---|---|---:|---|---:|---|
| 花 | PASS | 78.512 | right_hand_landmarks_xyz_1_256_quantized_preserved | 10.759 | right_hand_landmarks_all_distal_long_plus_thumb_tip_out_of_bounds_full_recapture |
| 跳 | PASS | 70.714 | right_hand_landmarks_single_index_tip_short_sparse_preserved | 6.762 | left_hand_landmarks_all_edges_short_full_recapture |

## 分项明细

### 花

| 变体 | 类型 | 状态 | 分数 | 阈值 | 损坏帧 | 量化旁路帧 | 最短比 | 最长比 | 处理率 | 最少剩余点 | capture_quality |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| self_reloaded | positive | PASS | 100.000 | 95.000 | 0 | 0 | - | - | - | None | score_valid:score_valid |
| right_hand_landmarks_all_edges_short_sparse_preserved | positive | PASS | 98.507 | 75.000 | 6 | 0 | 0.001 | 0.002 | 1.000 | 1 | score_valid:score_valid |
| right_hand_landmarks_all_edges_short_full_recapture | diagnostic | PASS | 10.076 | 55.000 | 40 | 0 | 0.001 | 0.002 | 1.000 | 1 | semantic_mismatch:flower_opening_guard_failed |
| right_hand_landmarks_all_distal_long_sparse_preserved | positive | PASS | 98.833 | 75.000 | 6 | 0 | 0.158 | 2.200 | 1.000 | 11 | score_valid:score_valid |
| right_hand_landmarks_all_distal_long_full_recapture | diagnostic | PASS | 10.731 | 55.000 | 40 | 0 | 0.103 | 2.200 | 1.000 | 11 | semantic_mismatch:flower_opening_guard_failed |
| right_hand_landmarks_single_index_tip_short_sparse_preserved | positive | PASS | 99.484 | 70.000 | 6 | 0 | 0.001 | 0.613 | 1.000 | 19 | score_valid:score_valid |
| right_hand_landmarks_xyz_1_256_quantized_preserved | positive | PASS | 78.512 | 70.000 | 0 | 40 | - | - | 1.000 | 21 | score_valid:score_valid |
| right_hand_landmarks_all_distal_long_plus_thumb_tip_out_of_bounds_full_recapture | diagnostic | PASS | 10.759 | 55.000 | 40 | 0 | 0.103 | 2.200 | 1.000 | 12 | semantic_mismatch:flower_opening_guard_failed |

### 跳

| 变体 | 类型 | 状态 | 分数 | 阈值 | 损坏帧 | 量化旁路帧 | 最短比 | 最长比 | 处理率 | 最少剩余点 | capture_quality |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| self_reloaded | positive | PASS | 100.000 | 95.000 | 0 | 0 | - | - | - | None | score_valid:score_valid |
| right_hand_landmarks_all_edges_short_sparse_preserved | positive | PASS | 81.642 | 75.000 | 2 | 0 | 0.002 | 0.002 | 1.000 | 1 | score_valid:score_valid |
| right_hand_landmarks_all_edges_short_full_recapture | diagnostic | PASS | 0.972 | 55.000 | 17 | 0 | 0.001 | 0.002 | 1.000 | 1 | semantic_mismatch:phase_order_disorder |
| right_hand_landmarks_all_distal_long_sparse_preserved | positive | PASS | 81.642 | 75.000 | 2 | 0 | 0.072 | 2.200 | 1.000 | 11 | score_valid:score_valid |
| right_hand_landmarks_all_distal_long_full_recapture | diagnostic | PASS | 1.535 | 55.000 | 17 | 0 | 0.062 | 2.200 | 1.000 | 11 | semantic_mismatch:missing_relation_delta |
| right_hand_landmarks_single_index_tip_short_sparse_preserved | positive | PASS | 70.714 | 70.000 | 2 | 0 | 0.001 | 0.439 | 1.000 | 19 | score_valid:score_valid |
| right_hand_landmarks_xyz_1_256_quantized_preserved | positive | PASS | 78.551 | 70.000 | 0 | 17 | - | - | 1.000 | 21 | score_valid:score_valid |
| right_hand_landmarks_all_distal_long_plus_thumb_tip_out_of_bounds_full_recapture | diagnostic | PASS | 1.584 | 55.000 | 17 | 0 | 0.062 | 2.200 | 1.000 | 12 | semantic_mismatch:missing_relation_delta |
| left_hand_landmarks_all_edges_short_sparse_preserved | positive | PASS | 88.903 | 75.000 | 2 | 0 | 0.002 | 0.002 | 1.000 | 1 | score_valid:score_valid |
| left_hand_landmarks_all_edges_short_full_recapture | diagnostic | PASS | 6.762 | 55.000 | 16 | 0 | 0.001 | 0.002 | 1.000 | 1 | semantic_mismatch:missing_relation_delta |
| left_hand_landmarks_all_distal_long_sparse_preserved | positive | PASS | 97.503 | 75.000 | 2 | 0 | 0.266 | 2.200 | 1.000 | 11 | score_valid:score_valid |
| left_hand_landmarks_all_distal_long_full_recapture | positive | PASS | 85.000 | 75.000 | 16 | 0 | 0.217 | 2.200 | 1.000 | 11 | score_valid:score_valid |
| left_hand_landmarks_single_index_tip_short_sparse_preserved | positive | PASS | 99.436 | 70.000 | 2 | 0 | 0.001 | 0.517 | 1.000 | 19 | score_valid:score_valid |
| left_hand_landmarks_xyz_1_256_quantized_preserved | positive | PASS | 96.132 | 70.000 | 0 | 16 | - | - | 1.000 | 21 | score_valid:score_valid |

## 说明

- 该规则只处理远离正常证据范围的极端局部伸缩；轻微 finger-length 风格变化继续由现有鲁棒性门覆盖。
- 至少 16 点可见的完整/部分全局量化手直接旁路，避免把坐标精度造成的零长度骨段误判为 tracker 损坏。
- 该门补充 landmark 碰撞和内部拓扑门，不替代正式 marker 后真实网页摄像头复测。

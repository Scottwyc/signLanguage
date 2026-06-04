# Holistic 序列打分 MVP 结果

## 口径说明

- 本结果是 prototype sanity check，不是已校准的真实用户评分。
- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。
- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。

## 输入

- 标准序列：`work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`
- 查询序列：`work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/谗（羡慕）/谗（羡慕）_holistic_results.json`
- 特征模式：`landmark`

## 主对齐结果

- prototype_score：`71.428`
- dtw_distance：`0.039156`
- normalized_distance：`0.048790`
- DTW path length：`74`
- sequence_penalty：`0.097400`

### 分组平均距离

- left_hand: `0.000000`
- right_hand: `0.000000`
- left_hand_shape: `0.000000`
- right_hand_shape: `0.000000`
- left_hand_motion: `0.000000`
- right_hand_motion: `0.000000`
- left_hand_shape_motion: `0.000000`
- right_hand_shape_motion: `0.000000`
- two_hand_relation: `0.000000`
- two_hand_relation_motion: `0.000000`
- pose: `0.381681`
- face: `0.237686`
- missing: `0.841090`
- base_weighted: `0.033644`
- semantic_phase_gap: `0.335282`
- semantic_phase_penalty: `0.005512`
- weighted: `0.039156`
- hand_side_swapped: `0.012300`

### 最差对齐点

- standard frame 38 vs query frame 61: weighted=0.050907, left=0.000000, right=0.000000, pose=0.464911, missing=0.990712
- standard frame 32 vs query frame 58: weighted=0.056176, left=0.000000, right=0.000000, pose=0.291738, missing=0.990712
- standard frame 30 vs query frame 56: weighted=0.057916, left=0.000000, right=0.000000, pose=0.251566, missing=0.990712
- standard frame 36 vs query frame 61: weighted=0.052815, left=0.000000, right=0.000000, pose=0.452605, missing=0.990712
- standard frame 34 vs query frame 60: weighted=0.054498, left=0.000000, right=0.000000, pose=0.493646, missing=0.990712

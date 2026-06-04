# Holistic 序列打分 MVP 结果

## 口径说明

- 本结果是 prototype sanity check，不是已校准的真实用户评分。
- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。
- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。

## 输入

- 标准序列：`work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`
- 查询序列：`work/generated/web_scoring_mvp/web_20260523_071212_4547d033/holistic/user_花_web_20260523_071212_4547d033_holistic_results.json`
- 特征模式：`landmark`

## 主对齐结果

- prototype_score：`45.047`
- dtw_distance：`0.030202`
- normalized_distance：`0.095696`
- DTW path length：`59`
- sequence_penalty：`0.065494`

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
- pose: `0.433837`
- face: `0.431455`
- missing: `0.745214`
- base_weighted: `0.029809`
- semantic_phase_gap: `0.046621`
- semantic_phase_penalty: `0.000394`
- weighted: `0.030202`
- hand_side_swapped: `0.682491`

### 最差对齐点

- standard frame 38 vs query frame 18: weighted=0.039762, left=0.000000, right=0.000000, pose=0.411945, missing=0.990712
- standard frame 36 vs query frame 17: weighted=0.040251, left=0.000000, right=0.000000, pose=0.423312, missing=0.990712
- standard frame 48 vs query frame 23: weighted=0.040061, left=0.000000, right=0.000000, pose=0.419604, missing=0.990712
- standard frame 40 vs query frame 19: weighted=0.039684, left=0.000000, right=0.000000, pose=0.418821, missing=0.990712
- standard frame 34 vs query frame 16: weighted=0.040855, left=0.000000, right=0.000000, pose=0.434032, missing=0.990712

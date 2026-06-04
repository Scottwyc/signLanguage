# Holistic 序列打分 MVP 结果

## 口径说明

- 本结果是 prototype sanity check，不是已校准的真实用户评分。
- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。
- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。

## 输入

- 标准序列：`work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`
- 查询序列：`work/generated/web_scoring_mvp/web_20260523_071320_415e2975/holistic/user_花_web_20260523_071320_415e2975_holistic_results.json`
- 特征模式：`landmark`

## 主对齐结果

- prototype_score：`30.132`
- dtw_distance：`0.033402`
- normalized_distance：`0.143948`
- DTW path length：`53`
- sequence_penalty：`0.155546`

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
- pose: `0.425181`
- face: `0.431204`
- missing: `0.794410`
- base_weighted: `0.031776`
- semantic_phase_gap: `0.141184`
- semantic_phase_penalty: `0.001626`
- weighted: `0.033402`
- hand_side_swapped: `0.654941`

### 最差对齐点

- standard frame 40 vs query frame 8: weighted=0.045061, left=0.000000, right=0.000000, pose=0.383006, missing=0.990712
- standard frame 46 vs query frame 11: weighted=0.040787, left=0.000000, right=0.000000, pose=0.404732, missing=0.990712
- standard frame 48 vs query frame 12: weighted=0.040058, left=0.000000, right=0.000000, pose=0.378406, missing=0.990712
- standard frame 42 vs query frame 9: weighted=0.043950, left=0.000000, right=0.000000, pose=0.396021, missing=0.990712
- standard frame 44 vs query frame 10: weighted=0.042188, left=0.000000, right=0.000000, pose=0.387280, missing=0.990712

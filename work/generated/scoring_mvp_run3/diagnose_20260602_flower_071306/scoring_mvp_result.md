# Holistic 序列打分 MVP 结果

## 口径说明

- 本结果是 prototype sanity check，不是已校准的真实用户评分。
- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。
- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。

## 输入

- 标准序列：`work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`
- 查询序列：`work/generated/web_scoring_mvp/web_20260523_071306_071a2172/holistic/user_花_web_20260523_071306_071a2172_holistic_results.json`
- 特征模式：`landmark`

## 主对齐结果

- prototype_score：`19.958`
- dtw_distance：`0.037068`
- normalized_distance：`0.193382`
- DTW path length：`53`
- sequence_penalty：`0.156314`

### 分组平均距离

- left_hand: `0.000000`
- right_hand: `0.002243`
- left_hand_shape: `0.000000`
- right_hand_shape: `0.003512`
- left_hand_motion: `0.000000`
- right_hand_motion: `0.000000`
- left_hand_shape_motion: `0.000000`
- right_hand_shape_motion: `0.000000`
- two_hand_relation: `0.000000`
- two_hand_relation_motion: `0.000000`
- pose: `0.534681`
- face: `0.422940`
- missing: `0.705145`
- base_weighted: `0.030492`
- semantic_phase_gap: `0.384053`
- semantic_phase_penalty: `0.006576`
- weighted: `0.037068`
- hand_side_swapped: `0.245421`

### 最差对齐点

- standard frame 104 vs query frame 29: weighted=0.156183, left=0.000000, right=0.145543, pose=0.494305, missing=0.195046
- standard frame 48 vs query frame 0: weighted=0.044312, left=0.000000, right=0.000000, pose=0.657353, missing=0.804954
- standard frame 50 vs query frame 0: weighted=0.046008, left=0.000000, right=0.000000, pose=0.619355, missing=0.804954
- standard frame 46 vs query frame 0: weighted=0.042574, left=0.000000, right=0.000000, pose=0.636723, missing=0.804954
- standard frame 38 vs query frame 0: weighted=0.036967, left=0.000000, right=0.000000, pose=0.636928, missing=0.804954

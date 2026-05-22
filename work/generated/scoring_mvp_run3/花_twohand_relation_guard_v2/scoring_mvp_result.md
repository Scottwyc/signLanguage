# Holistic 序列打分 MVP 结果

## 口径说明

- 本结果是 prototype sanity check，不是已校准的真实用户评分。
- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。
- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。

## 输入

- 标准序列：`work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`
- 查询序列：`work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`
- 特征模式：`landmark`

## 主对齐结果

- prototype_score：`100.000`
- dtw_distance：`0.000000`
- normalized_distance：`0.000000`
- DTW path length：`64`
- sequence_penalty：`0.000000`

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
- pose: `0.022274`
- face: `0.036170`
- missing: `0.000000`
- base_weighted: `0.000000`
- semantic_phase_gap: `0.000000`
- semantic_phase_penalty: `0.000000`
- weighted: `0.000000`
- hand_side_swapped: `0.000000`

### 最差对齐点

- standard frame 0 vs query frame 0: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 0 vs query frame 2: weighted=0.000000, left=0.000000, right=0.000000, pose=0.012657, missing=0.000000
- standard frame 0 vs query frame 4: weighted=0.000000, left=0.000000, right=0.000000, pose=0.032251, missing=0.000000
- standard frame 0 vs query frame 6: weighted=0.000000, left=0.000000, right=0.000000, pose=0.117032, missing=0.000000
- standard frame 0 vs query frame 8: weighted=0.000000, left=0.000000, right=0.000000, pose=0.171810, missing=0.000000

## 判别性套件

- 正例最低分：`90.917`
- 负例最高分：`15.133`
- 分离 margin：`75.784`
- 门控是否通过：`True`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`98.991`, dtw=`0.000152`, total_dist=`0.001316`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`98.895`, dtw=`0.000177`, total_dist=`0.001448`, expected=high
- trim_both_10pct [target_positive_variant]: score=`98.419`, dtw=`0.000434`, total_dist=`0.002194`, expected=high
- trim_start_20pct [target_positive_variant]: score=`98.077`, dtw=`0.001286`, total_dist=`0.003165`, expected=high
- trim_end_20pct [target_positive_variant]: score=`95.477`, dtw=`0.000764`, total_dist=`0.006051`, expected=high
- subsample_even [target_positive_variant]: score=`90.917`, dtw=`0.021407`, total_dist=`0.025342`, expected=high
- fake_shuffle_frames [synthetic_fake_action]: score=`15.133`, dtw=`0.045390`, total_dist=`0.226595`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`13.737`, dtw=`0.146896`, total_dist=`0.238206`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`9.760`, dtw=`0.064521`, total_dist=`0.279222`, expected=low
- other_demo_跳 [other_demo_action]: score=`9.491`, dtw=`0.118137`, total_dist=`0.282582`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`6.811`, dtw=`0.123704`, total_dist=`0.322404`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`1.254`, dtw=`0.090892`, total_dist=`0.525440`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`0.999`, dtw=`0.054608`, total_dist=`0.552727`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.449`, dtw=`0.091958`, total_dist=`0.648823`, expected=low

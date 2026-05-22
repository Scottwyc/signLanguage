# Holistic 序列打分 MVP 结果

## 口径说明

- 本结果是 prototype sanity check，不是已校准的真实用户评分。
- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。
- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。

## 输入

- 标准序列：`work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`
- 查询序列：`work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`
- 特征模式：`landmark`

## 主对齐结果

- prototype_score：`100.000`
- dtw_distance：`0.000000`
- normalized_distance：`0.000000`
- DTW path length：`8`
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
- pose: `0.000000`
- face: `0.000000`
- missing: `0.000000`
- base_weighted: `0.000000`
- semantic_phase_gap: `0.000000`
- semantic_phase_penalty: `0.000000`
- weighted: `0.000000`
- hand_side_swapped: `0.000000`

### 最差对齐点

- standard frame 12 vs query frame 12: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 14 vs query frame 14: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 16 vs query frame 16: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 18 vs query frame 18: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 20 vs query frame 20: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000

## 判别性套件

- 正例最低分：`87.772`
- 负例最高分：`41.936`
- 分离 margin：`45.836`
- 门控是否通过：`True`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`99.337`, dtw=`0.000321`, total_dist=`0.001309`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`99.178`, dtw=`0.000380`, total_dist=`0.001618`, expected=high
- trim_end_20pct [target_positive_variant]: score=`97.738`, dtw=`0.004524`, total_dist=`0.005701`, expected=high
- trim_both_10pct [target_positive_variant]: score=`97.719`, dtw=`0.004579`, total_dist=`0.005756`, expected=high
- trim_start_20pct [target_positive_variant]: score=`97.430`, dtw=`0.005076`, total_dist=`0.006462`, expected=high
- subsample_even [target_positive_variant]: score=`87.772`, dtw=`0.030510`, total_dist=`0.034155`, expected=high
- other_demo_花 [other_demo_action]: score=`41.936`, dtw=`0.079042`, total_dist=`0.156426`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`35.729`, dtw=`0.030766`, total_dist=`0.123506`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`23.500`, dtw=`0.168768`, total_dist=`0.260671`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`19.274`, dtw=`0.083758`, total_dist=`0.296354`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`12.114`, dtw=`0.164575`, total_dist=`0.379940`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`11.657`, dtw=`0.067923`, total_dist=`0.386865`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`0.431`, dtw=`0.575535`, total_dist=`0.980322`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.227`, dtw=`0.371834`, total_dist=`1.096169`, expected=low

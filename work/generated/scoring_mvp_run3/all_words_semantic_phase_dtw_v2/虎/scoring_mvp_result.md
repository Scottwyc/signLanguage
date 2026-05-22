# Holistic 序列打分 MVP 结果

## 口径说明

- 本结果是 prototype sanity check，不是已校准的真实用户评分。
- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。
- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。

## 输入

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/虎/虎_holistic_results.json`
- 查询序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/虎/虎_holistic_results.json`
- 特征模式：`landmark`

## 主对齐结果

- prototype_score：`100.000`
- dtw_distance：`0.000000`
- normalized_distance：`0.000000`
- DTW path length：`54`
- sequence_penalty：`0.000000`

### 分组平均距离

- left_hand: `0.000000`
- right_hand: `0.000000`
- left_hand_shape: `0.000000`
- right_hand_shape: `0.000000`
- pose: `0.000000`
- face: `0.000000`
- missing: `0.000000`
- base_weighted: `0.000000`
- semantic_phase_gap: `0.000000`
- semantic_phase_penalty: `0.000000`
- weighted: `0.000000`
- hand_side_swapped: `0.000000`

### 最差对齐点

- standard frame 0 vs query frame 0: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 2 vs query frame 2: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 4 vs query frame 4: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 6 vs query frame 6: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 8 vs query frame 8: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000

## 判别性套件

- 正例最低分：`63.005`
- 负例最高分：`17.611`
- 分离 margin：`45.394`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`95.048`, dtw=`0.000225`, total_dist=`0.006095`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`94.412`, dtw=`0.000263`, total_dist=`0.006900`, expected=high
- trim_both_10pct [target_positive_variant]: score=`84.209`, dtw=`0.001157`, total_dist=`0.020624`, expected=high
- trim_start_20pct [target_positive_variant]: score=`77.522`, dtw=`0.000996`, total_dist=`0.030553`, expected=high
- trim_end_20pct [target_positive_variant]: score=`76.701`, dtw=`0.000884`, total_dist=`0.031830`, expected=high
- subsample_even [target_positive_variant]: score=`63.005`, dtw=`0.035054`, total_dist=`0.055435`, expected=high
- other_demo_汽车 [other_demo_action]: score=`17.611`, dtw=`0.082555`, total_dist=`0.208398`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`12.609`, dtw=`0.080527`, total_dist=`0.248493`, expected=low
- other_demo_谗_羡慕 [other_demo_action]: score=`6.571`, dtw=`0.173965`, total_dist=`0.326695`, expected=low
- other_demo_月亮 [other_demo_action]: score=`5.831`, dtw=`0.137843`, total_dist=`0.341033`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`5.190`, dtw=`0.192534`, total_dist=`0.355007`, expected=low
- other_demo_跳 [other_demo_action]: score=`4.679`, dtw=`0.182086`, total_dist=`0.367442`, expected=low
- other_demo_朋友 [other_demo_action]: score=`4.456`, dtw=`0.241604`, total_dist=`0.373323`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`3.652`, dtw=`0.074947`, total_dist=`0.397200`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`3.417`, dtw=`0.292047`, total_dist=`0.405181`, expected=low
- other_demo_指示 [other_demo_action]: score=`3.113`, dtw=`0.272662`, total_dist=`0.416368`, expected=low
- other_demo_花 [other_demo_action]: score=`1.760`, dtw=`0.129085`, total_dist=`0.484778`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`0.130`, dtw=`0.268478`, total_dist=`0.797349`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.001`, dtw=`0.579297`, total_dist=`1.384580`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`0.000`, dtw=`0.857087`, total_dist=`1.639031`, expected=low

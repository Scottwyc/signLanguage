# Holistic 序列打分 MVP 结果

## 口径说明

- 本结果是 prototype sanity check，不是已校准的真实用户评分。
- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。
- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。

## 输入

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/月亮/月亮_holistic_results.json`
- 查询序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/月亮/月亮_holistic_results.json`
- 特征模式：`landmark`

## 主对齐结果

- prototype_score：`100.000`
- dtw_distance：`0.000000`
- normalized_distance：`0.000000`
- DTW path length：`49`
- sequence_penalty：`0.000000`

### 分组平均距离

- left_hand: `0.000000`
- right_hand: `0.000000`
- left_hand_shape: `0.000000`
- right_hand_shape: `0.000000`
- pose: `0.001792`
- face: `0.002001`
- missing: `0.000000`
- base_weighted: `0.000000`
- semantic_phase_gap: `0.000000`
- semantic_phase_penalty: `0.000000`
- weighted: `0.000000`
- hand_side_swapped: `0.000000`

### 最差对齐点

- standard frame 0 vs query frame 0: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 0 vs query frame 2: weighted=0.000000, left=0.000000, right=0.000000, pose=0.029648, missing=0.000000
- standard frame 0 vs query frame 4: weighted=0.000000, left=0.000000, right=0.000000, pose=0.063905, missing=0.000000
- standard frame 2 vs query frame 4: weighted=0.000000, left=0.000000, right=0.000000, pose=0.058882, missing=0.000000
- standard frame 4 vs query frame 4: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000

## 判别性套件

- 正例最低分：`32.052`
- 负例最高分：`23.901`
- 分离 margin：`8.150`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`93.856`, dtw=`0.000241`, total_dist=`0.007766`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`91.832`, dtw=`0.000280`, total_dist=`0.010407`, expected=high
- subsample_even [target_positive_variant]: score=`49.213`, dtw=`0.046707`, total_dist=`0.085083`, expected=high
- trim_both_10pct [target_positive_variant]: score=`47.783`, dtw=`0.001995`, total_dist=`0.088620`, expected=high
- trim_end_20pct [target_positive_variant]: score=`36.132`, dtw=`0.001937`, total_dist=`0.122158`, expected=high
- trim_start_20pct [target_positive_variant]: score=`32.052`, dtw=`0.003109`, total_dist=`0.136539`, expected=high
- other_demo_谗_羡慕 [other_demo_action]: score=`23.901`, dtw=`0.064025`, total_dist=`0.171748`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`14.053`, dtw=`0.042944`, total_dist=`0.235482`, expected=low
- other_demo_朋友 [other_demo_action]: score=`12.805`, dtw=`0.112856`, total_dist=`0.246643`, expected=low
- other_demo_跳 [other_demo_action]: score=`11.420`, dtw=`0.084826`, total_dist=`0.260378`, expected=low
- other_demo_汽车 [other_demo_action]: score=`7.293`, dtw=`0.041841`, total_dist=`0.314193`, expected=low
- other_demo_指示 [other_demo_action]: score=`7.290`, dtw=`0.105929`, total_dist=`0.314248`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`7.078`, dtw=`0.120714`, total_dist=`0.317780`, expected=low
- other_demo_虎 [other_demo_action]: score=`3.935`, dtw=`0.105792`, total_dist=`0.388227`, expected=low
- other_demo_花 [other_demo_action]: score=`3.893`, dtw=`0.040125`, total_dist=`0.389518`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`2.824`, dtw=`0.283583`, total_dist=`0.428054`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`1.817`, dtw=`0.121445`, total_dist=`0.480944`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`0.044`, dtw=`0.270616`, total_dist=`0.927619`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.021`, dtw=`0.273555`, total_dist=`1.018768`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`0.012`, dtw=`0.458333`, total_dist=`1.082241`, expected=low

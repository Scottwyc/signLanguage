# Holistic 序列打分 MVP 结果

## 口径说明

- 本结果是 prototype sanity check，不是已校准的真实用户评分。
- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。
- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。

## 输入

- 标准序列：`/data/WYC/signLanguage/work/generated/parallel_sampling_strategies_three_layer_run1/candidate_cache/花/花_holistic_results.json`
- 查询序列：`/data/WYC/signLanguage/work/generated/parallel_sampling_strategies_three_layer_run1/candidate_cache/花/花_holistic_results.json`
- 特征模式：`landmark`

## 主对齐结果

- prototype_score：`100.000`
- dtw_distance：`0.000000`
- normalized_distance：`0.000000`
- DTW path length：`28`
- sequence_penalty：`0.000000`

### 分组平均距离

- left_hand: `0.000000`
- right_hand: `0.000000`
- pose: `0.000000`
- face: `0.000000`
- missing: `0.000000`
- weighted: `0.000000`

### 最差对齐点

- standard frame 0 vs query frame 0: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 4 vs query frame 4: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 8 vs query frame 8: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 12 vs query frame 12: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 16 vs query frame 16: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000

## 伪用户 sanity check

- self: score=`100.000`, distance=`0.000000`, query_length=`28`
- subsample_even: score=`92.573`, distance=`0.007718`, query_length=`14`
- trim_start_20pct: score=`74.870`, distance=`0.028942`, query_length=`22`
- trim_end_20pct: score=`87.011`, distance=`0.013913`, query_length=`22`
- middle_60pct: score=`75.690`, distance=`0.027852`, query_length=`16`
- amplitude_0.85: score=`92.707`, distance=`0.007572`, query_length=`28`
- amplitude_1.15: score=`93.693`, distance=`0.006514`, query_length=`28`

## 判别性套件

- 正例最低分：`74.870`
- 负例最高分：`47.636`
- 分离 margin：`27.234`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`93.693`, dtw=`0.000268`, total_dist=`0.006514`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`92.707`, dtw=`0.000312`, total_dist=`0.007572`, expected=high
- subsample_even [target_positive_variant]: score=`92.573`, dtw=`0.006118`, total_dist=`0.007718`, expected=high
- trim_end_20pct [target_positive_variant]: score=`87.011`, dtw=`0.004750`, total_dist=`0.013913`, expected=high
- middle_60pct [target_positive_variant]: score=`75.690`, dtw=`0.017538`, total_dist=`0.027852`, expected=high
- trim_start_20pct [target_positive_variant]: score=`74.870`, dtw=`0.012788`, total_dist=`0.028942`, expected=high
- fake_reverse_time [synthetic_fake_action]: score=`47.636`, dtw=`0.074158`, total_dist=`0.074158`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`29.024`, dtw=`0.040420`, total_dist=`0.123706`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`14.111`, dtw=`0.035819`, total_dist=`0.195819`, expected=low
- other_demo_jump_sparse [other_demo_action]: score=`0.585`, dtw=`0.102895`, total_dist=`0.514095`, expected=low
- other_demo_singing_sparse [other_demo_action]: score=`0.214`, dtw=`0.158864`, total_dist=`0.614864`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.122`, dtw=`0.522228`, total_dist=`0.671028`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`0.003`, dtw=`0.910923`, total_dist=`1.032991`, expected=low

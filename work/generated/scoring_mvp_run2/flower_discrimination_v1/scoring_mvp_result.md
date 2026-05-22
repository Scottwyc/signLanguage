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
- subsample_even: score=`85.889`, distance=`0.015211`, query_length=`14`
- trim_start_20pct: score=`77.032`, distance=`0.026095`, query_length=`22`
- trim_end_20pct: score=`87.877`, distance=`0.012924`, query_length=`22`
- middle_60pct: score=`72.194`, distance=`0.032581`, query_length=`16`
- amplitude_0.85: score=`62.923`, distance=`0.046326`, query_length=`28`
- amplitude_1.15: score=`63.123`, distance=`0.046009`, query_length=`28`

## 判别性套件

- 正例最低分：`62.923`
- 负例最高分：`51.858`
- 分离 margin：`11.065`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- trim_end_20pct [target_positive_variant]: score=`87.877`, dtw=`0.007515`, total_dist=`0.012924`, expected=high
- subsample_even [target_positive_variant]: score=`85.889`, dtw=`0.006908`, total_dist=`0.015211`, expected=high
- trim_start_20pct [target_positive_variant]: score=`77.032`, dtw=`0.014190`, total_dist=`0.026095`, expected=high
- middle_60pct [target_positive_variant]: score=`72.194`, dtw=`0.021705`, total_dist=`0.032581`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`63.123`, dtw=`0.044058`, total_dist=`0.046009`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`62.923`, dtw=`0.044058`, total_dist=`0.046326`, expected=high
- fake_shuffle_frames [synthetic_fake_action]: score=`51.858`, dtw=`0.044445`, total_dist=`0.065666`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`45.364`, dtw=`0.079046`, total_dist=`0.079046`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`35.432`, dtw=`0.046055`, total_dist=`0.103755`, expected=low
- other_demo_sparse [other_demo_action]: score=`0.269`, dtw=`0.137705`, total_dist=`0.591814`, expected=low
- other_demo_sparse [other_demo_action]: score=`0.105`, dtw=`0.162017`, total_dist=`0.685851`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.103`, dtw=`0.641355`, total_dist=`0.687855`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`0.000`, dtw=`1.222737`, total_dist=`1.258896`, expected=low

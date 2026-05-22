# Holistic 序列打分 MVP 结果

## 口径说明

- 本结果是 prototype sanity check，不是已校准的真实用户评分。
- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。
- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。

## 输入

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache_v2/results/花/花_holistic_results.json`
- 查询序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache_v2/results/花/花_holistic_results.json`
- 特征模式：`landmark`

## 主对齐结果

- prototype_score：`100.000`
- dtw_distance：`0.000000`
- normalized_distance：`0.000000`
- DTW path length：`34`
- sequence_penalty：`0.000000`

### 分组平均距离

- left_hand: `0.000000`
- right_hand: `0.000000`
- left_hand_shape: `0.000000`
- right_hand_shape: `0.000000`
- pose: `0.075657`
- face: `0.090204`
- missing: `0.000000`
- weighted: `0.000000`
- hand_side_swapped: `0.000000`

### 最差对齐点

- standard frame 0 vs query frame 0: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 0 vs query frame 4: weighted=0.000000, left=0.000000, right=0.000000, pose=0.054787, missing=0.000000
- standard frame 0 vs query frame 8: weighted=0.000000, left=0.000000, right=0.000000, pose=0.160658, missing=0.000000
- standard frame 0 vs query frame 12: weighted=0.000000, left=0.000000, right=0.000000, pose=0.121142, missing=0.000000
- standard frame 0 vs query frame 16: weighted=0.000000, left=0.000000, right=0.000000, pose=0.126856, missing=0.000000

## 判别性套件

- 正例最低分：`83.367`
- 负例最高分：`58.603`
- 分离 margin：`24.764`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- trim_start_20pct [target_positive_variant]: score=`92.648`, dtw=`0.000000`, total_dist=`0.009164`, expected=high
- trim_both_10pct [target_positive_variant]: score=`90.089`, dtw=`0.001935`, total_dist=`0.012525`, expected=high
- subsample_even [target_positive_variant]: score=`88.844`, dtw=`0.006774`, total_dist=`0.014194`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`87.227`, dtw=`0.012353`, total_dist=`0.016399`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`86.805`, dtw=`0.012353`, total_dist=`0.016980`, expected=high
- trim_end_20pct [target_positive_variant]: score=`83.367`, dtw=`0.003529`, total_dist=`0.021830`, expected=high
- fake_shuffle_frames [synthetic_fake_action]: score=`58.603`, dtw=`0.008500`, total_dist=`0.064125`, expected=low
- other_demo_case [other_demo_action]: score=`46.510`, dtw=`0.010714`, total_dist=`0.091859`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`32.569`, dtw=`0.011429`, total_dist=`0.134617`, expected=low
- other_demo_case [other_demo_action]: score=`31.939`, dtw=`0.010800`, total_dist=`0.136960`, expected=low
- other_demo_case [other_demo_action]: score=`29.531`, dtw=`0.016735`, total_dist=`0.146367`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`24.105`, dtw=`0.012353`, total_dist=`0.170729`, expected=low
- other_demo_case [other_demo_action]: score=`21.589`, dtw=`0.067058`, total_dist=`0.183956`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`19.000`, dtw=`0.011190`, total_dist=`0.199285`, expected=low
- other_demo_case [other_demo_action]: score=`18.895`, dtw=`0.152438`, total_dist=`0.199953`, expected=low
- other_demo_case [other_demo_action]: score=`17.702`, dtw=`0.127909`, total_dist=`0.207777`, expected=low
- other_demo_case [other_demo_action]: score=`16.320`, dtw=`0.078388`, total_dist=`0.217530`, expected=low
- other_demo_case [other_demo_action]: score=`15.765`, dtw=`0.157246`, total_dist=`0.221684`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`14.683`, dtw=`0.012353`, total_dist=`0.230219`, expected=low
- other_demo_case [other_demo_action]: score=`10.380`, dtw=`0.079194`, total_dist=`0.271833`, expected=low

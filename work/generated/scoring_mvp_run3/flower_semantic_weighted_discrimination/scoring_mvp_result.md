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
- DTW path length：`28`
- sequence_penalty：`0.000000`

### 分组平均距离

- left_hand: `0.000000`
- right_hand: `0.000000`
- left_hand_shape: `0.000000`
- right_hand_shape: `0.000000`
- pose: `0.000000`
- face: `0.000000`
- missing: `0.000000`
- weighted: `0.000000`
- hand_side_swapped: `0.000000`

### 最差对齐点

- standard frame 0 vs query frame 0: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 4 vs query frame 4: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 8 vs query frame 8: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 12 vs query frame 12: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 16 vs query frame 16: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000

## 判别性套件

- 正例最低分：`78.413`
- 负例最高分：`70.295`
- 分离 margin：`8.117`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- trim_both_10pct [target_positive_variant]: score=`91.343`, dtw=`0.005068`, total_dist=`0.010866`, expected=high
- trim_start_20pct [target_positive_variant]: score=`90.154`, dtw=`0.003602`, total_dist=`0.012439`, expected=high
- subsample_even [target_positive_variant]: score=`87.657`, dtw=`0.014409`, total_dist=`0.015809`, expected=high
- trim_end_20pct [target_positive_variant]: score=`87.518`, dtw=`0.008035`, total_dist=`0.015998`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`78.796`, dtw=`0.025022`, total_dist=`0.028597`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`78.413`, dtw=`0.025026`, total_dist=`0.029182`, expected=high
- fake_reverse_time [synthetic_fake_action]: score=`70.295`, dtw=`0.036565`, total_dist=`0.042296`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`56.594`, dtw=`0.026358`, total_dist=`0.068313`, expected=low
- other_demo_case [other_demo_action]: score=`52.762`, dtw=`0.035982`, total_dist=`0.076726`, expected=low
- other_demo_case [other_demo_action]: score=`37.356`, dtw=`0.043300`, total_dist=`0.118162`, expected=low
- other_demo_case [other_demo_action]: score=`31.901`, dtw=`0.046753`, total_dist=`0.137104`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`30.308`, dtw=`0.073971`, total_dist=`0.143250`, expected=low
- other_demo_case [other_demo_action]: score=`24.674`, dtw=`0.098288`, total_dist=`0.167928`, expected=low
- other_demo_case [other_demo_action]: score=`22.473`, dtw=`0.150640`, total_dist=`0.179145`, expected=low
- other_demo_case [other_demo_action]: score=`20.383`, dtw=`0.091539`, total_dist=`0.190859`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`19.744`, dtw=`0.024013`, total_dist=`0.194679`, expected=low
- other_demo_case [other_demo_action]: score=`19.714`, dtw=`0.172262`, total_dist=`0.194862`, expected=low
- other_demo_case [other_demo_action]: score=`17.618`, dtw=`0.176490`, total_dist=`0.208352`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`12.798`, dtw=`0.087353`, total_dist=`0.246709`, expected=low
- other_demo_case [other_demo_action]: score=`10.689`, dtw=`0.133892`, total_dist=`0.268317`, expected=low

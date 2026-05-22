# Holistic 序列打分 MVP 结果

## 口径说明

- 本结果是 prototype sanity check，不是已校准的真实用户评分。
- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。
- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。

## 输入

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`
- 查询序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`
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
- pose: `0.022196`
- face: `0.036042`
- missing: `0.000000`
- weighted: `0.000000`
- hand_side_swapped: `0.000000`

### 最差对齐点

- standard frame 0 vs query frame 0: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 0 vs query frame 2: weighted=0.000000, left=0.000000, right=0.000000, pose=0.012657, missing=0.000000
- standard frame 0 vs query frame 4: weighted=0.000000, left=0.000000, right=0.000000, pose=0.032251, missing=0.000000
- standard frame 0 vs query frame 6: weighted=0.000000, left=0.000000, right=0.000000, pose=0.117032, missing=0.000000
- standard frame 0 vs query frame 8: weighted=0.000000, left=0.000000, right=0.000000, pose=0.171810, missing=0.000000

## 判别性套件

- 正例最低分：`71.411`
- 负例最高分：`57.222`
- 分离 margin：`14.188`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- trim_both_10pct [target_positive_variant]: score=`84.409`, dtw=`0.000419`, total_dist=`0.020340`, expected=high
- trim_start_20pct [target_positive_variant]: score=`84.403`, dtw=`0.000256`, total_dist=`0.020348`, expected=high
- subsample_even [target_positive_variant]: score=`83.744`, dtw=`0.007514`, total_dist=`0.021289`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`80.777`, dtw=`0.014513`, total_dist=`0.025617`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`79.730`, dtw=`0.014474`, total_dist=`0.027183`, expected=high
- trim_end_20pct [target_positive_variant]: score=`71.411`, dtw=`0.000429`, total_dist=`0.040407`, expected=high
- other_demo_谗_羡慕 [other_demo_action]: score=`57.222`, dtw=`0.015754`, total_dist=`0.066987`, expected=low
- other_demo_月亮 [other_demo_action]: score=`45.651`, dtw=`0.016937`, total_dist=`0.094097`, expected=low
- other_demo_汽车 [other_demo_action]: score=`26.796`, dtw=`0.015544`, total_dist=`0.158029`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`26.145`, dtw=`0.049293`, total_dist=`0.160983`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`20.493`, dtw=`0.015296`, total_dist=`0.190211`, expected=low
- other_demo_指示 [other_demo_action]: score=`20.189`, dtw=`0.156648`, total_dist=`0.192003`, expected=low
- other_demo_跳 [other_demo_action]: score=`18.267`, dtw=`0.068263`, total_dist=`0.204006`, expected=low
- other_demo_朋友 [other_demo_action]: score=`17.196`, dtw=`0.162920`, total_dist=`0.211258`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`17.080`, dtw=`0.019493`, total_dist=`0.212069`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`13.029`, dtw=`0.191064`, total_dist=`0.244563`, expected=low
- other_demo_虎 [other_demo_action]: score=`4.994`, dtw=`0.074751`, total_dist=`0.359637`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`2.225`, dtw=`0.014710`, total_dist=`0.456660`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`0.687`, dtw=`0.011967`, total_dist=`0.597619`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.476`, dtw=`0.014706`, total_dist=`0.641668`, expected=low

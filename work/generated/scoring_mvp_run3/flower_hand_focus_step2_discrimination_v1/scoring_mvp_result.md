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

- 正例最低分：`79.564`
- 负例最高分：`68.135`
- 分离 margin：`11.429`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- subsample_even [target_positive_variant]: score=`88.932`, dtw=`0.004925`, total_dist=`0.014076`, expected=high
- trim_both_10pct [target_positive_variant]: score=`88.700`, dtw=`0.000419`, total_dist=`0.014389`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`87.926`, dtw=`0.008276`, total_dist=`0.015440`, expected=high
- trim_start_20pct [target_positive_variant]: score=`87.277`, dtw=`0.000085`, total_dist=`0.016330`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`87.189`, dtw=`0.008252`, total_dist=`0.016452`, expected=high
- trim_end_20pct [target_positive_variant]: score=`79.564`, dtw=`0.000429`, total_dist=`0.027434`, expected=high
- other_demo_谗_羡慕 [other_demo_action]: score=`68.135`, dtw=`0.011130`, total_dist=`0.046042`, expected=low
- other_demo_月亮 [other_demo_action]: score=`59.139`, dtw=`0.011434`, total_dist=`0.063034`, expected=low
- other_demo_汽车 [other_demo_action]: score=`43.261`, dtw=`0.007250`, total_dist=`0.100551`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`37.263`, dtw=`0.005612`, total_dist=`0.118460`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`36.963`, dtw=`0.046339`, total_dist=`0.119432`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`33.585`, dtw=`0.006687`, total_dist=`0.130930`, expected=low
- other_demo_指示 [other_demo_action]: score=`22.687`, dtw=`0.153084`, total_dist=`0.178007`, expected=low
- other_demo_跳 [other_demo_action]: score=`21.802`, dtw=`0.064444`, total_dist=`0.182782`, expected=low
- other_demo_朋友 [other_demo_action]: score=`20.813`, dtw=`0.155904`, total_dist=`0.188349`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`14.677`, dtw=`0.191818`, total_dist=`0.230264`, expected=low
- other_demo_虎 [other_demo_action]: score=`10.122`, dtw=`0.070862`, total_dist=`0.274857`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`8.663`, dtw=`0.008398`, total_dist=`0.293528`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`3.888`, dtw=`0.007190`, total_dist=`0.389660`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`3.204`, dtw=`0.008396`, total_dist=`0.412888`, expected=low

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

- 正例最低分：`68.899`
- 负例最高分：`39.509`
- 分离 margin：`29.390`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`95.002`, dtw=`0.001397`, total_dist=`0.006152`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`94.606`, dtw=`0.001409`, total_dist=`0.006654`, expected=high
- trim_both_10pct [target_positive_variant]: score=`94.029`, dtw=`0.000434`, total_dist=`0.007388`, expected=high
- trim_start_20pct [target_positive_variant]: score=`94.026`, dtw=`0.000240`, total_dist=`0.007391`, expected=high
- trim_end_20pct [target_positive_variant]: score=`85.514`, dtw=`0.000764`, total_dist=`0.018779`, expected=high
- subsample_even [target_positive_variant]: score=`68.899`, dtw=`0.029347`, total_dist=`0.044704`, expected=high
- other_demo_谗_羡慕 [other_demo_action]: score=`39.509`, dtw=`0.036987`, total_dist=`0.111437`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`31.923`, dtw=`0.028628`, total_dist=`0.137022`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`27.064`, dtw=`0.028036`, total_dist=`0.156837`, expected=low
- other_demo_指示 [other_demo_action]: score=`25.449`, dtw=`0.106443`, total_dist=`0.164220`, expected=low
- other_demo_月亮 [other_demo_action]: score=`21.244`, dtw=`0.039911`, total_dist=`0.185891`, expected=low
- other_demo_朋友 [other_demo_action]: score=`20.820`, dtw=`0.119922`, total_dist=`0.188310`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`19.713`, dtw=`0.055838`, total_dist=`0.194867`, expected=low
- other_demo_汽车 [other_demo_action]: score=`18.097`, dtw=`0.033894`, total_dist=`0.205134`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`17.990`, dtw=`0.135310`, total_dist=`0.205841`, expected=low
- other_demo_跳 [other_demo_action]: score=`15.007`, dtw=`0.083810`, total_dist=`0.227599`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`6.098`, dtw=`0.061894`, total_dist=`0.335661`, expected=low
- other_demo_虎 [other_demo_action]: score=`5.761`, dtw=`0.069094`, total_dist=`0.342488`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`4.826`, dtw=`0.052604`, total_dist=`0.363736`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.573`, dtw=`0.188953`, total_dist=`0.619359`, expected=low

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
- pose: `0.022287`
- face: `0.036191`
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

- 正例最低分：`82.365`
- 负例最高分：`48.734`
- 分离 margin：`33.631`
- 门控是否通过：`True`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- trim_both_10pct [target_positive_variant]: score=`90.530`, dtw=`0.001317`, total_dist=`0.011938`, expected=high
- trim_start_20pct [target_positive_variant]: score=`88.364`, dtw=`0.000129`, total_dist=`0.014845`, expected=high
- subsample_even [target_positive_variant]: score=`87.421`, dtw=`0.007380`, total_dist=`0.016132`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`85.530`, dtw=`0.012412`, total_dist=`0.018756`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`84.942`, dtw=`0.012368`, total_dist=`0.019584`, expected=high
- trim_end_20pct [target_positive_variant]: score=`82.365`, dtw=`0.002996`, total_dist=`0.023281`, expected=high
- other_demo_谗_羡慕 [other_demo_action]: score=`48.734`, dtw=`0.015855`, total_dist=`0.086256`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`47.549`, dtw=`0.008419`, total_dist=`0.089210`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`32.896`, dtw=`0.010027`, total_dist=`0.133420`, expected=low
- other_demo_朋友 [other_demo_action]: score=`26.522`, dtw=`0.110638`, total_dist=`0.159263`, expected=low
- other_demo_月亮 [other_demo_action]: score=`24.628`, dtw=`0.017147`, total_dist=`0.168155`, expected=low
- other_demo_指示 [other_demo_action]: score=`22.951`, dtw=`0.124914`, total_dist=`0.176615`, expected=low
- other_demo_跳 [other_demo_action]: score=`20.599`, dtw=`0.061345`, total_dist=`0.189593`, expected=low
- other_demo_汽车 [other_demo_action]: score=`20.543`, dtw=`0.010882`, total_dist=`0.189916`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`19.632`, dtw=`0.141380`, total_dist=`0.195358`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`18.462`, dtw=`0.058715`, total_dist=`0.202734`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`11.970`, dtw=`0.012596`, total_dist=`0.254736`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`9.763`, dtw=`0.010797`, total_dist=`0.279182`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`7.321`, dtw=`0.012593`, total_dist=`0.313730`, expected=low
- other_demo_虎 [other_demo_action]: score=`5.498`, dtw=`0.063601`, total_dist=`0.348101`, expected=low

# Holistic 序列打分 MVP 结果

## 口径说明

- 本结果是 prototype sanity check，不是已校准的真实用户评分。
- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。
- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。

## 输入

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`
- 查询序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`
- 特征模式：`landmark`

## 主对齐结果

- prototype_score：`100.000`
- dtw_distance：`0.000000`
- normalized_distance：`0.000000`
- DTW path length：`19`
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
- standard frame 2 vs query frame 2: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 4 vs query frame 4: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 6 vs query frame 6: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 8 vs query frame 8: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000

## 判别性套件

- 正例最低分：`71.408`
- 负例最高分：`32.141`
- 分离 margin：`39.267`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`87.856`, dtw=`0.005094`, total_dist=`0.015537`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`86.786`, dtw=`0.005146`, total_dist=`0.017006`, expected=high
- trim_both_10pct [target_positive_variant]: score=`84.245`, dtw=`0.006898`, total_dist=`0.020573`, expected=high
- trim_end_20pct [target_positive_variant]: score=`82.157`, dtw=`0.006721`, total_dist=`0.023584`, expected=high
- subsample_even [target_positive_variant]: score=`77.297`, dtw=`0.022005`, total_dist=`0.030902`, expected=high
- trim_start_20pct [target_positive_variant]: score=`71.408`, dtw=`0.019050`, total_dist=`0.040411`, expected=high
- other_demo_谗_羡慕 [other_demo_action]: score=`32.141`, dtw=`0.054959`, total_dist=`0.136203`, expected=low
- other_demo_月亮 [other_demo_action]: score=`30.028`, dtw=`0.052676`, total_dist=`0.144365`, expected=low
- other_demo_汽车 [other_demo_action]: score=`27.121`, dtw=`0.026581`, total_dist=`0.156582`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`25.687`, dtw=`0.030647`, total_dist=`0.163101`, expected=low
- other_demo_花 [other_demo_action]: score=`22.946`, dtw=`0.041207`, total_dist=`0.176644`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`22.344`, dtw=`0.130129`, total_dist=`0.179833`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`16.563`, dtw=`0.170258`, total_dist=`0.215761`, expected=low
- other_demo_朋友 [other_demo_action]: score=`15.263`, dtw=`0.155917`, total_dist=`0.225570`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`13.560`, dtw=`0.037598`, total_dist=`0.239763`, expected=low
- other_demo_虎 [other_demo_action]: score=`9.894`, dtw=`0.114506`, total_dist=`0.277588`, expected=low
- other_demo_指示 [other_demo_action]: score=`8.161`, dtw=`0.251753`, total_dist=`0.300700`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`1.971`, dtw=`0.083240`, total_dist=`0.471190`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.007`, dtw=`0.575162`, total_dist=`1.141010`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`0.001`, dtw=`0.914910`, total_dist=`1.449420`, expected=low

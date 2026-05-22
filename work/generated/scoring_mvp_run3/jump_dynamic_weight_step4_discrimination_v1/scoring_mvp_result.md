# Holistic 序列打分 MVP 结果

## 口径说明

- 本结果是 prototype sanity check，不是已校准的真实用户评分。
- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。
- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。

## 输入

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache_v2/results/跳/跳_holistic_results.json`
- 查询序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache_v2/results/跳/跳_holistic_results.json`
- 特征模式：`landmark`

## 主对齐结果

- prototype_score：`100.000`
- dtw_distance：`0.000000`
- normalized_distance：`0.000000`
- DTW path length：`10`
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

- 正例最低分：`73.988`
- 负例最高分：`30.334`
- 分离 margin：`43.655`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`88.868`, dtw=`0.003195`, total_dist=`0.014162`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`87.700`, dtw=`0.003229`, total_dist=`0.015750`, expected=high
- trim_both_10pct [target_positive_variant]: score=`81.311`, dtw=`0.010164`, total_dist=`0.024827`, expected=high
- trim_end_20pct [target_positive_variant]: score=`78.824`, dtw=`0.010367`, total_dist=`0.028554`, expected=high
- trim_start_20pct [target_positive_variant]: score=`76.806`, dtw=`0.015764`, total_dist=`0.031667`, expected=high
- subsample_even [target_positive_variant]: score=`73.988`, dtw=`0.027833`, total_dist=`0.036152`, expected=high
- other_demo_谗_羡慕 [other_demo_action]: score=`30.334`, dtw=`0.071294`, total_dist=`0.143149`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`28.890`, dtw=`0.058698`, total_dist=`0.149003`, expected=low
- other_demo_月亮 [other_demo_action]: score=`23.048`, dtw=`0.100115`, total_dist=`0.176113`, expected=low
- other_demo_汽车 [other_demo_action]: score=`20.584`, dtw=`0.079975`, total_dist=`0.189676`, expected=low
- other_demo_花 [other_demo_action]: score=`17.682`, dtw=`0.070014`, total_dist=`0.207913`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`16.926`, dtw=`0.162854`, total_dist=`0.213160`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`15.383`, dtw=`0.080507`, total_dist=`0.224629`, expected=low
- other_demo_朋友 [other_demo_action]: score=`9.986`, dtw=`0.231751`, total_dist=`0.276474`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`9.817`, dtw=`0.186190`, total_dist=`0.278531`, expected=low
- other_demo_指示 [other_demo_action]: score=`7.159`, dtw=`0.286391`, total_dist=`0.316420`, expected=low
- other_demo_虎 [other_demo_action]: score=`4.802`, dtw=`0.185118`, total_dist=`0.364330`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`2.223`, dtw=`0.072295`, total_dist=`0.456755`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.002`, dtw=`0.715261`, total_dist=`1.320836`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`0.001`, dtw=`0.940800`, total_dist=`1.420864`, expected=low

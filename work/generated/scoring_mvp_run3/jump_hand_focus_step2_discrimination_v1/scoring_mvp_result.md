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
- DTW path length：`8`
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

- standard frame 12 vs query frame 12: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 14 vs query frame 14: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 16 vs query frame 16: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 18 vs query frame 18: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 20 vs query frame 20: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000

## 判别性套件

- 正例最低分：`77.016`
- 负例最高分：`78.418`
- 分离 margin：`-1.402`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`94.691`, dtw=`0.001850`, total_dist=`0.010467`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`94.020`, dtw=`0.001889`, total_dist=`0.011760`, expected=high
- trim_start_20pct [target_positive_variant]: score=`93.525`, dtw=`0.004500`, total_dist=`0.013625`, expected=high
- trim_end_20pct [target_positive_variant]: score=`93.525`, dtw=`0.004500`, total_dist=`0.013625`, expected=high
- trim_both_10pct [target_positive_variant]: score=`93.525`, dtw=`0.004500`, total_dist=`0.013625`, expected=high
- other_demo_花 [other_demo_action]: score=`78.418`, dtw=`0.019484`, total_dist=`0.050581`, expected=low
- subsample_even [target_positive_variant]: score=`77.016`, dtw=`0.026320`, total_dist=`0.056220`, expected=high
- fake_static_hold [synthetic_fake_action]: score=`44.528`, dtw=`0.038095`, total_dist=`0.097085`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`28.631`, dtw=`0.180534`, total_dist=`0.225121`, expected=low
- other_demo_虎 [other_demo_action]: score=`26.383`, dtw=`0.165659`, total_dist=`0.239840`, expected=low
- other_demo_谗_羡慕 [other_demo_action]: score=`23.281`, dtw=`0.111085`, total_dist=`0.262356`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`22.894`, dtw=`0.054534`, total_dist=`0.265373`, expected=low
- other_demo_月亮 [other_demo_action]: score=`17.959`, dtw=`0.257403`, total_dist=`0.309077`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`16.351`, dtw=`0.145420`, total_dist=`0.325956`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`16.182`, dtw=`0.134065`, total_dist=`0.327829`, expected=low
- other_demo_指示 [other_demo_action]: score=`12.786`, dtw=`0.198663`, total_dist=`0.370230`, expected=low
- other_demo_朋友 [other_demo_action]: score=`6.448`, dtw=`0.352242`, total_dist=`0.493441`, expected=low
- other_demo_汽车 [other_demo_action]: score=`4.866`, dtw=`0.515063`, total_dist=`0.544138`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`0.018`, dtw=`0.895098`, total_dist=`1.556998`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.001`, dtw=`1.273884`, total_dist=`2.002577`, expected=low

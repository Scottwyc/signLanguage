# Holistic 序列打分 MVP 结果

## 口径说明

- 本结果是 prototype sanity check，不是已校准的真实用户评分。
- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。
- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。

## 输入

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/指示/指示_holistic_results.json`
- 查询序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/指示/指示_holistic_results.json`
- 特征模式：`landmark`

## 主对齐结果

- prototype_score：`100.000`
- dtw_distance：`0.000000`
- normalized_distance：`0.000000`
- DTW path length：`32`
- sequence_penalty：`0.000000`

### 分组平均距离

- left_hand: `0.000000`
- right_hand: `0.000000`
- left_hand_shape: `0.000000`
- right_hand_shape: `0.000000`
- pose: `0.005371`
- face: `0.005534`
- missing: `0.000000`
- weighted: `0.000000`
- hand_side_swapped: `0.000000`

### 最差对齐点

- standard frame 0 vs query frame 0: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 0 vs query frame 2: weighted=0.000000, left=0.000000, right=0.000000, pose=0.053985, missing=0.000000
- standard frame 0 vs query frame 4: weighted=0.000000, left=0.000000, right=0.000000, pose=0.093839, missing=0.000000
- standard frame 2 vs query frame 4: weighted=0.000000, left=0.000000, right=0.000000, pose=0.083168, missing=0.000000
- standard frame 4 vs query frame 4: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000

## 判别性套件

- 正例最低分：`50.255`
- 负例最高分：`22.855`
- 分离 margin：`27.400`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- trim_both_10pct [target_positive_variant]: score=`85.511`, dtw=`0.001500`, total_dist=`0.018783`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`85.339`, dtw=`0.000275`, total_dist=`0.019024`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`83.528`, dtw=`0.000320`, total_dist=`0.021599`, expected=high
- trim_end_20pct [target_positive_variant]: score=`81.566`, dtw=`0.000750`, total_dist=`0.024451`, expected=high
- subsample_even [target_positive_variant]: score=`80.363`, dtw=`0.016170`, total_dist=`0.026233`, expected=high
- trim_start_20pct [target_positive_variant]: score=`50.255`, dtw=`0.000750`, total_dist=`0.082566`, expected=high
- other_demo_汽车 [other_demo_action]: score=`22.855`, dtw=`0.039624`, total_dist=`0.177121`, expected=low
- other_demo_花 [other_demo_action]: score=`18.038`, dtw=`0.118641`, total_dist=`0.205522`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`14.811`, dtw=`0.137741`, total_dist=`0.229178`, expected=low
- other_demo_月亮 [other_demo_action]: score=`14.613`, dtw=`0.102663`, total_dist=`0.230794`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`11.811`, dtw=`0.046950`, total_dist=`0.256341`, expected=low
- other_demo_跳 [other_demo_action]: score=`8.451`, dtw=`0.222306`, total_dist=`0.296500`, expected=low
- other_demo_谗_羡慕 [other_demo_action]: score=`5.998`, dtw=`0.097939`, total_dist=`0.337647`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`5.519`, dtw=`0.052728`, total_dist=`0.347643`, expected=low
- other_demo_朋友 [other_demo_action]: score=`4.521`, dtw=`0.176714`, total_dist=`0.371583`, expected=low
- other_demo_虎 [other_demo_action]: score=`4.414`, dtw=`0.238653`, total_dist=`0.374438`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`0.545`, dtw=`0.349481`, total_dist=`0.625403`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`0.486`, dtw=`0.058097`, total_dist=`0.639094`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.004`, dtw=`0.482771`, total_dist=`1.217166`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`0.000`, dtw=`1.055775`, total_dist=`1.895398`, expected=low

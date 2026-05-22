# Holistic 序列打分 MVP 结果

## 口径说明

- 本结果是 prototype sanity check，不是已校准的真实用户评分。
- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。
- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。

## 输入

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/谗（羡慕）/谗（羡慕）_holistic_results.json`
- 查询序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/谗（羡慕）/谗（羡慕）_holistic_results.json`
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
- pose: `0.000000`
- face: `0.000000`
- missing: `0.000000`
- base_weighted: `0.000000`
- semantic_phase_gap: `0.000000`
- semantic_phase_penalty: `0.000000`
- weighted: `0.000000`
- hand_side_swapped: `0.000000`

### 最差对齐点

- standard frame 0 vs query frame 0: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 2 vs query frame 2: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 4 vs query frame 4: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 6 vs query frame 6: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 8 vs query frame 8: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000

## 判别性套件

- 正例最低分：`56.750`
- 负例最高分：`23.188`
- 分离 margin：`33.562`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`97.270`, dtw=`0.000145`, total_dist=`0.003321`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`96.838`, dtw=`0.000168`, total_dist=`0.003856`, expected=high
- trim_end_20pct [target_positive_variant]: score=`88.932`, dtw=`0.000959`, total_dist=`0.014075`, expected=high
- subsample_even [target_positive_variant]: score=`75.307`, dtw=`0.024289`, total_dist=`0.034032`, expected=high
- trim_both_10pct [target_positive_variant]: score=`67.174`, dtw=`0.001116`, total_dist=`0.047746`, expected=high
- trim_start_20pct [target_positive_variant]: score=`56.750`, dtw=`0.001089`, total_dist=`0.067981`, expected=high
- other_demo_花 [other_demo_action]: score=`23.188`, dtw=`0.105132`, total_dist=`0.175382`, expected=low
- other_demo_朋友 [other_demo_action]: score=`21.482`, dtw=`0.107243`, total_dist=`0.184554`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`19.625`, dtw=`0.081693`, total_dist=`0.195406`, expected=low
- other_demo_跳 [other_demo_action]: score=`14.492`, dtw=`0.154147`, total_dist=`0.231787`, expected=low
- other_demo_虎 [other_demo_action]: score=`11.553`, dtw=`0.174123`, total_dist=`0.258983`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`10.777`, dtw=`0.191006`, total_dist=`0.267329`, expected=low
- other_demo_汽车 [other_demo_action]: score=`10.274`, dtw=`0.163149`, total_dist=`0.273063`, expected=low
- other_demo_月亮 [other_demo_action]: score=`9.686`, dtw=`0.160968`, total_dist=`0.280143`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`8.130`, dtw=`0.064571`, total_dist=`0.301149`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`7.615`, dtw=`0.199114`, total_dist=`0.309004`, expected=low
- other_demo_指示 [other_demo_action]: score=`4.630`, dtw=`0.228979`, total_dist=`0.368720`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`2.262`, dtw=`0.065714`, total_dist=`0.454661`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`0.015`, dtw=`0.525947`, total_dist=`1.059043`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.005`, dtw=`0.552060`, total_dist=`1.195151`, expected=low

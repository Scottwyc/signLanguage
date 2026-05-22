# Holistic 序列打分 MVP 结果

## 口径说明

- 本结果是 prototype sanity check，不是已校准的真实用户评分。
- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。
- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。

## 输入

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/香蕉/香蕉_holistic_results.json`
- 查询序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/香蕉/香蕉_holistic_results.json`
- 特征模式：`landmark`

## 主对齐结果

- prototype_score：`100.000`
- dtw_distance：`0.000000`
- normalized_distance：`0.000000`
- DTW path length：`45`
- sequence_penalty：`0.000000`

### 分组平均距离

- left_hand: `0.000000`
- right_hand: `0.000000`
- left_hand_shape: `0.000000`
- right_hand_shape: `0.000000`
- pose: `0.005353`
- face: `0.005138`
- missing: `0.000000`
- weighted: `0.000000`
- hand_side_swapped: `0.000000`

### 最差对齐点

- standard frame 0 vs query frame 0: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 0 vs query frame 2: weighted=0.000000, left=0.000000, right=0.000000, pose=0.064373, missing=0.000000
- standard frame 0 vs query frame 4: weighted=0.000000, left=0.000000, right=0.000000, pose=0.039270, missing=0.000000
- standard frame 0 vs query frame 6: weighted=0.000000, left=0.000000, right=0.000000, pose=0.066311, missing=0.000000
- standard frame 2 vs query frame 6: weighted=0.000000, left=0.000000, right=0.000000, pose=0.073333, missing=0.000000

## 判别性套件

- 正例最低分：`51.975`
- 负例最高分：`26.551`
- 分离 margin：`25.424`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- trim_both_10pct [target_positive_variant]: score=`85.783`, dtw=`0.001059`, total_dist=`0.018720`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`85.625`, dtw=`0.000274`, total_dist=`0.018705`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`83.816`, dtw=`0.000318`, total_dist=`0.021280`, expected=high
- trim_end_20pct [target_positive_variant]: score=`81.870`, dtw=`0.001059`, total_dist=`0.024322`, expected=high
- subsample_even [target_positive_variant]: score=`78.416`, dtw=`0.022647`, total_dist=`0.035971`, expected=high
- trim_start_20pct [target_positive_variant]: score=`51.975`, dtw=`0.001059`, total_dist=`0.078530`, expected=high
- other_demo_朋友 [other_demo_action]: score=`26.551`, dtw=`0.084120`, total_dist=`0.159135`, expected=low
- other_demo_跳 [other_demo_action]: score=`19.770`, dtw=`0.110738`, total_dist=`0.194521`, expected=low
- other_demo_指示 [other_demo_action]: score=`17.340`, dtw=`0.113417`, total_dist=`0.210257`, expected=low
- other_demo_汽车 [other_demo_action]: score=`16.727`, dtw=`0.040121`, total_dist=`0.214578`, expected=low
- other_demo_谗_羡慕 [other_demo_action]: score=`15.786`, dtw=`0.099288`, total_dist=`0.221522`, expected=low
- other_demo_月亮 [other_demo_action]: score=`12.118`, dtw=`0.101006`, total_dist=`0.253257`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`11.462`, dtw=`0.046380`, total_dist=`0.259933`, expected=low
- other_demo_虎 [other_demo_action]: score=`8.063`, dtw=`0.106084`, total_dist=`0.302144`, expected=low
- other_demo_花 [other_demo_action]: score=`8.054`, dtw=`0.049229`, total_dist=`0.302282`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`5.183`, dtw=`0.243457`, total_dist=`0.355178`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`5.105`, dtw=`0.049511`, total_dist=`0.357005`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`0.179`, dtw=`0.140923`, total_dist=`0.758876`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.016`, dtw=`0.331155`, total_dist=`1.048978`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`0.000`, dtw=`0.738358`, total_dist=`1.557158`, expected=low

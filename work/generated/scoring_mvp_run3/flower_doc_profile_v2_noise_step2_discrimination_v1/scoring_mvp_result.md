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
- pose: `0.022443`
- face: `0.036443`
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

- 正例最低分：`75.347`
- 负例最高分：`39.430`
- 分离 margin：`35.917`
- 门控是否通过：`True`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`91.763`, dtw=`0.000137`, total_dist=`0.010357`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`90.660`, dtw=`0.000159`, total_dist=`0.011814`, expected=high
- trim_both_10pct [target_positive_variant]: score=`86.745`, dtw=`0.000419`, total_dist=`0.017189`, expected=high
- trim_start_20pct [target_positive_variant]: score=`85.103`, dtw=`0.000421`, total_dist=`0.019483`, expected=high
- subsample_even [target_positive_variant]: score=`84.039`, dtw=`0.010682`, total_dist=`0.024071`, expected=high
- trim_end_20pct [target_positive_variant]: score=`75.347`, dtw=`0.000429`, total_dist=`0.034097`, expected=high
- other_demo_谗_羡慕 [other_demo_action]: score=`39.430`, dtw=`0.030698`, total_dist=`0.111678`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`26.294`, dtw=`0.016264`, total_dist=`0.160300`, expected=low
- other_demo_朋友 [other_demo_action]: score=`19.522`, dtw=`0.136050`, total_dist=`0.196033`, expected=low
- other_demo_月亮 [other_demo_action]: score=`18.910`, dtw=`0.033975`, total_dist=`0.199860`, expected=low
- other_demo_指示 [other_demo_action]: score=`17.558`, dtw=`0.151833`, total_dist=`0.208757`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`16.946`, dtw=`0.021144`, total_dist=`0.213014`, expected=low
- other_demo_跳 [other_demo_action]: score=`14.915`, dtw=`0.086491`, total_dist=`0.228338`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`14.636`, dtw=`0.057014`, total_dist=`0.230600`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`14.187`, dtw=`0.170118`, total_dist=`0.234341`, expected=low
- other_demo_汽车 [other_demo_action]: score=`13.020`, dtw=`0.027215`, total_dist=`0.244638`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`2.820`, dtw=`0.028685`, total_dist=`0.428192`, expected=low
- other_demo_虎 [other_demo_action]: score=`2.469`, dtw=`0.082839`, total_dist=`0.444167`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`1.623`, dtw=`0.021044`, total_dist=`0.494495`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`1.000`, dtw=`0.028678`, total_dist=`0.552612`, expected=low

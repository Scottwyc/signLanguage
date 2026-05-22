# Holistic 序列打分 MVP 结果

## 口径说明

- 本结果是 prototype sanity check，不是已校准的真实用户评分。
- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。
- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。

## 输入

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/月亮/月亮_holistic_results.json`
- 查询序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/月亮/月亮_holistic_results.json`
- 特征模式：`landmark`

## 主对齐结果

- prototype_score：`100.000`
- dtw_distance：`0.000000`
- normalized_distance：`0.000000`
- DTW path length：`49`
- sequence_penalty：`0.000000`

### 分组平均距离

- left_hand: `0.000000`
- right_hand: `0.000000`
- left_hand_shape: `0.000000`
- right_hand_shape: `0.000000`
- pose: `0.001792`
- face: `0.002000`
- missing: `0.000000`
- weighted: `0.000000`
- hand_side_swapped: `0.000000`

### 最差对齐点

- standard frame 0 vs query frame 0: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 0 vs query frame 2: weighted=0.000000, left=0.000000, right=0.000000, pose=0.029648, missing=0.000000
- standard frame 0 vs query frame 4: weighted=0.000000, left=0.000000, right=0.000000, pose=0.063905, missing=0.000000
- standard frame 2 vs query frame 4: weighted=0.000000, left=0.000000, right=0.000000, pose=0.058882, missing=0.000000
- standard frame 4 vs query frame 4: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000

## 判别性套件

- 正例最低分：`38.963`
- 负例最高分：`36.878`
- 分离 margin：`2.085`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`89.128`, dtw=`0.000237`, total_dist=`0.013883`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`87.615`, dtw=`0.000276`, total_dist=`0.015949`, expected=high
- subsample_even [target_positive_variant]: score=`58.905`, dtw=`0.045157`, total_dist=`0.063508`, expected=high
- trim_both_10pct [target_positive_variant]: score=`51.173`, dtw=`0.001459`, total_dist=`0.080395`, expected=high
- trim_end_20pct [target_positive_variant]: score=`45.534`, dtw=`0.000474`, total_dist=`0.094404`, expected=high
- trim_start_20pct [target_positive_variant]: score=`38.963`, dtw=`0.000947`, total_dist=`0.113106`, expected=high
- other_demo_谗_羡慕 [other_demo_action]: score=`36.878`, dtw=`0.056245`, total_dist=`0.119706`, expected=low
- other_demo_朋友 [other_demo_action]: score=`21.263`, dtw=`0.103924`, total_dist=`0.185784`, expected=low
- other_demo_跳 [other_demo_action]: score=`19.669`, dtw=`0.075295`, total_dist=`0.195137`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`16.471`, dtw=`0.037344`, total_dist=`0.216429`, expected=low
- other_demo_汽车 [other_demo_action]: score=`14.034`, dtw=`0.033537`, total_dist=`0.235640`, expected=low
- other_demo_指示 [other_demo_action]: score=`12.932`, dtw=`0.097985`, total_dist=`0.245455`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`10.342`, dtw=`0.112118`, total_dist=`0.272270`, expected=low
- other_demo_虎 [other_demo_action]: score=`7.480`, dtw=`0.097848`, total_dist=`0.311155`, expected=low
- other_demo_花 [other_demo_action]: score=`5.293`, dtw=`0.034187`, total_dist=`0.352659`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`5.053`, dtw=`0.276096`, total_dist=`0.358231`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`2.915`, dtw=`0.103649`, total_dist=`0.424252`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`0.144`, dtw=`0.181770`, total_dist=`0.784782`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.087`, dtw=`0.265319`, total_dist=`0.845394`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`0.084`, dtw=`0.456814`, total_dist=`0.849318`, expected=low

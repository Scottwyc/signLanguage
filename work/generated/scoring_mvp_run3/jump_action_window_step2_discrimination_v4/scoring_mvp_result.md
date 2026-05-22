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
- DTW path length：`9`
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

- standard frame 6 vs query frame 6: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 8 vs query frame 8: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 10 vs query frame 10: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 12 vs query frame 12: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 14 vs query frame 14: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000

## 判别性套件

- 正例最低分：`70.263`
- 负例最高分：`45.759`
- 分离 margin：`24.504`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`89.268`, dtw=`0.003335`, total_dist=`0.013623`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`88.179`, dtw=`0.003392`, total_dist=`0.015097`, expected=high
- trim_both_10pct [target_positive_variant]: score=`74.921`, dtw=`0.021927`, total_dist=`0.034648`, expected=high
- trim_end_20pct [target_positive_variant]: score=`74.918`, dtw=`0.021933`, total_dist=`0.034653`, expected=high
- trim_start_20pct [target_positive_variant]: score=`74.892`, dtw=`0.021974`, total_dist=`0.034695`, expected=high
- subsample_even [target_positive_variant]: score=`70.263`, dtw=`0.027526`, total_dist=`0.042351`, expected=high
- fake_static_hold [synthetic_fake_action]: score=`45.759`, dtw=`0.057992`, total_dist=`0.093814`, expected=low
- other_demo_花 [other_demo_action]: score=`33.027`, dtw=`0.061896`, total_dist=`0.132943`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`10.981`, dtw=`0.093833`, total_dist=`0.265083`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`8.715`, dtw=`0.108708`, total_dist=`0.292814`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`8.093`, dtw=`0.248136`, total_dist=`0.301701`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`6.589`, dtw=`0.217463`, total_dist=`0.326369`, expected=low
- other_demo_月亮 [other_demo_action]: score=`5.861`, dtw=`0.279193`, total_dist=`0.340417`, expected=low
- other_demo_虎 [other_demo_action]: score=`5.742`, dtw=`0.257187`, total_dist=`0.342886`, expected=low
- other_demo_谗_羡慕 [other_demo_action]: score=`3.623`, dtw=`0.188401`, total_dist=`0.398158`, expected=low
- other_demo_指示 [other_demo_action]: score=`3.413`, dtw=`0.328094`, total_dist=`0.405312`, expected=low
- other_demo_汽车 [other_demo_action]: score=`1.195`, dtw=`0.491852`, total_dist=`0.531204`, expected=low
- other_demo_朋友 [other_demo_action]: score=`0.417`, dtw=`0.364709`, total_dist=`0.657685`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.000`, dtw=`1.183352`, total_dist=`1.531036`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`0.000`, dtw=`1.578682`, total_dist=`2.294889`, expected=low

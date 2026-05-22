# Holistic 序列打分 MVP 结果

## 口径说明

- 本结果是 prototype sanity check，不是已校准的真实用户评分。
- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。
- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。

## 输入

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache_v2/results/花/花_holistic_results.json`
- 查询序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache_v2/results/花/花_holistic_results.json`
- 特征模式：`landmark`

## 主对齐结果

- prototype_score：`100.000`
- dtw_distance：`0.000000`
- normalized_distance：`0.000000`
- DTW path length：`34`
- sequence_penalty：`0.000000`

### 分组平均距离

- left_hand: `0.000000`
- right_hand: `0.000000`
- left_hand_shape: `0.000000`
- right_hand_shape: `0.000000`
- pose: `0.075657`
- face: `0.090204`
- missing: `0.000000`
- weighted: `0.000000`
- hand_side_swapped: `0.000000`

### 最差对齐点

- standard frame 0 vs query frame 0: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 0 vs query frame 4: weighted=0.000000, left=0.000000, right=0.000000, pose=0.054787, missing=0.000000
- standard frame 0 vs query frame 8: weighted=0.000000, left=0.000000, right=0.000000, pose=0.160658, missing=0.000000
- standard frame 0 vs query frame 12: weighted=0.000000, left=0.000000, right=0.000000, pose=0.121142, missing=0.000000
- standard frame 0 vs query frame 16: weighted=0.000000, left=0.000000, right=0.000000, pose=0.126856, missing=0.000000

## 判别性套件

- 正例最低分：`81.437`
- 负例最高分：`49.049`
- 分离 margin：`32.388`
- 门控是否通过：`True`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- trim_start_20pct [target_positive_variant]: score=`92.648`, dtw=`0.000000`, total_dist=`0.009164`, expected=high
- trim_both_10pct [target_positive_variant]: score=`88.871`, dtw=`0.001935`, total_dist=`0.014158`, expected=high
- subsample_even [target_positive_variant]: score=`88.844`, dtw=`0.006774`, total_dist=`0.014194`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`85.937`, dtw=`0.012353`, total_dist=`0.018186`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`85.315`, dtw=`0.012353`, total_dist=`0.019058`, expected=high
- trim_end_20pct [target_positive_variant]: score=`81.437`, dtw=`0.003529`, total_dist=`0.024641`, expected=high
- fake_shuffle_frames [synthetic_fake_action]: score=`49.049`, dtw=`0.008500`, total_dist=`0.085481`, expected=low
- other_demo_谗_羡慕 [other_demo_action]: score=`42.245`, dtw=`0.010714`, total_dist=`0.103402`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`32.569`, dtw=`0.011429`, total_dist=`0.134617`, expected=low
- other_demo_汽车 [other_demo_action]: score=`24.769`, dtw=`0.010800`, total_dist=`0.167471`, expected=low
- other_demo_月亮 [other_demo_action]: score=`21.942`, dtw=`0.016735`, total_dist=`0.182013`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`18.793`, dtw=`0.012353`, total_dist=`0.200603`, expected=low
- other_demo_指示 [other_demo_action]: score=`17.971`, dtw=`0.152438`, total_dist=`0.205973`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`17.316`, dtw=`0.067058`, total_dist=`0.210425`, expected=low
- other_demo_朋友 [other_demo_action]: score=`17.210`, dtw=`0.127909`, total_dist=`0.211164`, expected=low
- other_demo_跳 [other_demo_action]: score=`16.320`, dtw=`0.078388`, total_dist=`0.217530`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`15.765`, dtw=`0.157246`, total_dist=`0.221684`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`9.723`, dtw=`0.011190`, total_dist=`0.279685`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`7.934`, dtw=`0.012353`, total_dist=`0.304087`, expected=low
- other_demo_虎 [other_demo_action]: score=`7.347`, dtw=`0.079194`, total_dist=`0.313312`, expected=low

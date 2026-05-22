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
- pose: `0.050419`
- face: `0.060113`
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

- 正例最低分：`81.714`
- 负例最高分：`48.356`
- 分离 margin：`33.357`
- 门控是否通过：`True`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- trim_start_20pct [target_positive_variant]: score=`92.648`, dtw=`0.000000`, total_dist=`0.009164`, expected=high
- trim_both_10pct [target_positive_variant]: score=`89.257`, dtw=`0.001416`, total_dist=`0.013638`, expected=high
- subsample_even [target_positive_variant]: score=`88.149`, dtw=`0.007717`, total_dist=`0.015137`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`84.875`, dtw=`0.013845`, total_dist=`0.019678`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`83.542`, dtw=`0.014873`, total_dist=`0.021578`, expected=high
- trim_end_20pct [target_positive_variant]: score=`81.714`, dtw=`0.003123`, total_dist=`0.024234`, expected=high
- fake_shuffle_frames [synthetic_fake_action]: score=`48.356`, dtw=`0.010208`, total_dist=`0.087189`, expected=low
- other_demo_谗_羡慕 [other_demo_action]: score=`42.139`, dtw=`0.011014`, total_dist=`0.103702`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`33.044`, dtw=`0.009691`, total_dist=`0.132880`, expected=low
- other_demo_汽车 [other_demo_action]: score=`24.697`, dtw=`0.011149`, total_dist=`0.167820`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`22.838`, dtw=`0.112771`, total_dist=`0.177209`, expected=low
- other_demo_指示 [other_demo_action]: score=`22.332`, dtw=`0.126364`, total_dist=`0.179898`, expected=low
- other_demo_月亮 [other_demo_action]: score=`21.801`, dtw=`0.017506`, total_dist=`0.182783`, expected=low
- other_demo_朋友 [other_demo_action]: score=`21.383`, dtw=`0.101853`, total_dist=`0.185109`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`19.598`, dtw=`0.052204`, total_dist=`0.195572`, expected=low
- other_demo_跳 [other_demo_action]: score=`18.641`, dtw=`0.062437`, total_dist=`0.201579`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`18.547`, dtw=`0.013933`, total_dist=`0.202183`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`9.796`, dtw=`0.010294`, total_dist=`0.278788`, expected=low
- other_demo_虎 [other_demo_action]: score=`8.161`, dtw=`0.066581`, total_dist=`0.300699`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`7.830`, dtw=`0.013935`, total_dist=`0.305670`, expected=low

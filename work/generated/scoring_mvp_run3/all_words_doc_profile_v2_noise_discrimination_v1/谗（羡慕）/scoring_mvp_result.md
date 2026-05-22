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
- weighted: `0.000000`
- hand_side_swapped: `0.000000`

### 最差对齐点

- standard frame 0 vs query frame 0: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 2 vs query frame 2: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 4 vs query frame 4: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 6 vs query frame 6: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 8 vs query frame 8: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000

## 判别性套件

- 正例最低分：`51.900`
- 负例最高分：`30.676`
- 分离 margin：`21.224`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`95.204`, dtw=`0.000140`, total_dist=`0.005898`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`94.454`, dtw=`0.000163`, total_dist=`0.006847`, expected=high
- trim_end_20pct [target_positive_variant]: score=`86.312`, dtw=`0.000692`, total_dist=`0.017665`, expected=high
- subsample_even [target_positive_variant]: score=`78.578`, dtw=`0.024172`, total_dist=`0.028929`, expected=high
- trim_both_10pct [target_positive_variant]: score=`57.819`, dtw=`0.001111`, total_dist=`0.065742`, expected=high
- trim_start_20pct [target_positive_variant]: score=`51.900`, dtw=`0.000692`, total_dist=`0.078703`, expected=high
- other_demo_花 [other_demo_action]: score=`30.676`, dtw=`0.091195`, total_dist=`0.141805`, expected=low
- other_demo_朋友 [other_demo_action]: score=`27.696`, dtw=`0.101603`, total_dist=`0.154067`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`21.148`, dtw=`0.080269`, total_dist=`0.186433`, expected=low
- other_demo_跳 [other_demo_action]: score=`18.569`, dtw=`0.148988`, total_dist=`0.202039`, expected=low
- other_demo_汽车 [other_demo_action]: score=`15.062`, dtw=`0.145433`, total_dist=`0.227156`, expected=low
- other_demo_虎 [other_demo_action]: score=`14.694`, dtw=`0.169234`, total_dist=`0.230128`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`13.971`, dtw=`0.187285`, total_dist=`0.236185`, expected=low
- other_demo_月亮 [other_demo_action]: score=`11.712`, dtw=`0.156488`, total_dist=`0.257349`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`9.690`, dtw=`0.061051`, total_dist=`0.280086`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`9.466`, dtw=`0.195060`, total_dist=`0.282893`, expected=low
- other_demo_指示 [other_demo_action]: score=`5.586`, dtw=`0.233460`, total_dist=`0.346184`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`2.808`, dtw=`0.046523`, total_dist=`0.428711`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`0.039`, dtw=`0.520727`, total_dist=`0.942711`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.010`, dtw=`0.546019`, total_dist=`1.108362`, expected=low

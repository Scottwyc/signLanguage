# Holistic 序列打分 MVP 结果

## 口径说明

- 本结果是 prototype sanity check，不是已校准的真实用户评分。
- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。
- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。

## 输入

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/汽车/汽车_holistic_results.json`
- 查询序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/汽车/汽车_holistic_results.json`
- 特征模式：`landmark`

## 主对齐结果

- prototype_score：`100.000`
- dtw_distance：`0.000000`
- normalized_distance：`0.000000`
- DTW path length：`50`
- sequence_penalty：`0.000000`

### 分组平均距离

- left_hand: `0.000000`
- right_hand: `0.000000`
- left_hand_shape: `0.000000`
- right_hand_shape: `0.000000`
- pose: `0.009821`
- face: `0.005811`
- missing: `0.000000`
- base_weighted: `0.000000`
- semantic_phase_gap: `0.000000`
- semantic_phase_penalty: `0.000000`
- weighted: `0.000000`
- hand_side_swapped: `0.000000`

### 最差对齐点

- standard frame 0 vs query frame 0: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 0 vs query frame 2: weighted=0.000000, left=0.000000, right=0.000000, pose=0.049538, missing=0.000000
- standard frame 2 vs query frame 2: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 4 vs query frame 4: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 6 vs query frame 6: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000

## 判别性套件

- 正例最低分：`39.347`
- 负例最高分：`15.975`
- 分离 margin：`23.372`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`90.960`, dtw=`0.000314`, total_dist=`0.011574`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`90.345`, dtw=`0.000269`, total_dist=`0.012359`, expected=high
- trim_both_10pct [target_positive_variant]: score=`62.857`, dtw=`0.003082`, total_dist=`0.057720`, expected=high
- trim_start_20pct [target_positive_variant]: score=`60.085`, dtw=`0.000695`, total_dist=`0.061129`, expected=high
- subsample_even [target_positive_variant]: score=`57.507`, dtw=`0.020584`, total_dist=`0.066392`, expected=high
- trim_end_20pct [target_positive_variant]: score=`39.347`, dtw=`0.000896`, total_dist=`0.111930`, expected=high
- other_demo_虎 [other_demo_action]: score=`15.975`, dtw=`0.055464`, total_dist=`0.220094`, expected=low
- other_demo_谗_羡慕 [other_demo_action]: score=`15.768`, dtw=`0.058200`, total_dist=`0.221664`, expected=low
- other_demo_朋友 [other_demo_action]: score=`14.220`, dtw=`0.058767`, total_dist=`0.234059`, expected=low
- other_demo_指示 [other_demo_action]: score=`13.973`, dtw=`0.057568`, total_dist=`0.236161`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`13.700`, dtw=`0.054624`, total_dist=`0.238536`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`10.897`, dtw=`0.057183`, total_dist=`0.265999`, expected=low
- other_demo_跳 [other_demo_action]: score=`10.485`, dtw=`0.059222`, total_dist=`0.270631`, expected=low
- other_demo_月亮 [other_demo_action]: score=`6.878`, dtw=`0.058788`, total_dist=`0.321226`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`6.061`, dtw=`0.165492`, total_dist=`0.336400`, expected=low
- other_demo_花 [other_demo_action]: score=`2.550`, dtw=`0.040873`, total_dist=`0.440299`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`2.515`, dtw=`0.050631`, total_dist=`0.441970`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`0.312`, dtw=`0.101434`, total_dist=`0.692379`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`0.163`, dtw=`0.052525`, total_dist=`0.770552`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.124`, dtw=`0.052541`, total_dist=`0.802763`, expected=low

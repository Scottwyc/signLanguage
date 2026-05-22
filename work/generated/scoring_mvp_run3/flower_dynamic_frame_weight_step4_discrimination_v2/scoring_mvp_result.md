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
- pose: `0.049287`
- face: `0.058763`
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

- 正例最低分：`77.119`
- 负例最高分：`56.571`
- 分离 margin：`20.547`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- trim_start_20pct [target_positive_variant]: score=`91.549`, dtw=`0.000000`, total_dist=`0.010595`, expected=high
- subsample_even [target_positive_variant]: score=`87.935`, dtw=`0.007762`, total_dist=`0.015428`, expected=high
- trim_both_10pct [target_positive_variant]: score=`86.873`, dtw=`0.001377`, total_dist=`0.016886`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`84.309`, dtw=`0.013905`, total_dist=`0.020481`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`83.634`, dtw=`0.013861`, total_dist=`0.021446`, expected=high
- trim_end_20pct [target_positive_variant]: score=`77.119`, dtw=`0.003079`, total_dist=`0.031179`, expected=high
- other_demo_谗_羡慕 [other_demo_action]: score=`56.571`, dtw=`0.011006`, total_dist=`0.068360`, expected=low
- other_demo_汽车 [other_demo_action]: score=`52.540`, dtw=`0.011148`, total_dist=`0.077232`, expected=low
- other_demo_月亮 [other_demo_action]: score=`44.234`, dtw=`0.017533`, total_dist=`0.097881`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`37.312`, dtw=`0.010260`, total_dist=`0.118302`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`32.093`, dtw=`0.009692`, total_dist=`0.136384`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`30.816`, dtw=`0.071883`, total_dist=`0.141255`, expected=low
- other_demo_朋友 [other_demo_action]: score=`19.273`, dtw=`0.128160`, total_dist=`0.197575`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`17.582`, dtw=`0.162641`, total_dist=`0.208592`, expected=low
- other_demo_虎 [other_demo_action]: score=`15.713`, dtw=`0.090453`, total_dist=`0.222082`, expected=low
- other_demo_跳 [other_demo_action]: score=`15.524`, dtw=`0.091478`, total_dist=`0.223534`, expected=low
- other_demo_指示 [other_demo_action]: score=`14.049`, dtw=`0.211081`, total_dist=`0.235517`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`13.554`, dtw=`0.013735`, total_dist=`0.239817`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`3.873`, dtw=`0.010134`, total_dist=`0.390130`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`3.583`, dtw=`0.013738`, total_dist=`0.399460`, expected=low

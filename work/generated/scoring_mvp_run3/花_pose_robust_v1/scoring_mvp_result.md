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
- left_hand_motion: `0.000000`
- right_hand_motion: `0.000000`
- left_hand_shape_motion: `0.000000`
- right_hand_shape_motion: `0.000000`
- two_hand_relation: `0.000000`
- two_hand_relation_motion: `0.000000`
- pose: `0.022274`
- face: `0.036170`
- missing: `0.000000`
- base_weighted: `0.000000`
- semantic_phase_gap: `0.000000`
- semantic_phase_penalty: `0.000000`
- weighted: `0.000000`
- hand_side_swapped: `0.000000`

### 最差对齐点

- standard frame 0 vs query frame 0: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 0 vs query frame 2: weighted=0.000000, left=0.000000, right=0.000000, pose=0.012657, missing=0.000000
- standard frame 0 vs query frame 4: weighted=0.000000, left=0.000000, right=0.000000, pose=0.032251, missing=0.000000
- standard frame 0 vs query frame 6: weighted=0.000000, left=0.000000, right=0.000000, pose=0.117032, missing=0.000000
- standard frame 0 vs query frame 8: weighted=0.000000, left=0.000000, right=0.000000, pose=0.171810, missing=0.000000

## 判别性套件

- 正例最低分：`83.213`
- 负例最高分：`31.147`
- 分离 margin：`52.066`
- 门控是否通过：`True`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`94.671`, dtw=`0.000154`, total_dist=`0.006672`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`94.120`, dtw=`0.000178`, total_dist=`0.007388`, expected=high
- trim_both_10pct [target_positive_variant]: score=`91.958`, dtw=`0.000434`, total_dist=`0.010343`, expected=high
- trim_start_20pct [target_positive_variant]: score=`91.523`, dtw=`0.000417`, total_dist=`0.010902`, expected=high
- subsample_even [target_positive_variant]: score=`83.667`, dtw=`0.011139`, total_dist=`0.028639`, expected=high
- trim_end_20pct [target_positive_variant]: score=`83.213`, dtw=`0.000764`, total_dist=`0.022548`, expected=high
- other_demo_谗_羡慕 [other_demo_action]: score=`31.147`, dtw=`0.037848`, total_dist=`0.139973`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`23.204`, dtw=`0.025327`, total_dist=`0.175302`, expected=low
- other_demo_指示 [other_demo_action]: score=`19.452`, dtw=`0.117068`, total_dist=`0.196469`, expected=low
- other_demo_朋友 [other_demo_action]: score=`16.272`, dtw=`0.124852`, total_dist=`0.217887`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`15.324`, dtw=`0.029562`, total_dist=`0.225087`, expected=low
- other_demo_月亮 [other_demo_action]: score=`12.560`, dtw=`0.040569`, total_dist=`0.248962`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`12.546`, dtw=`0.149540`, total_dist=`0.249094`, expected=low
- other_demo_跳 [other_demo_action]: score=`12.233`, dtw=`0.080212`, total_dist=`0.252120`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`11.256`, dtw=`0.060673`, total_dist=`0.262114`, expected=low
- other_demo_汽车 [other_demo_action]: score=`9.091`, dtw=`0.034749`, total_dist=`0.287741`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`2.707`, dtw=`0.027672`, total_dist=`0.433119`, expected=low
- other_demo_虎 [other_demo_action]: score=`2.072`, dtw=`0.074802`, total_dist=`0.465211`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`1.482`, dtw=`0.025274`, total_dist=`0.505401`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.960`, dtw=`0.027656`, total_dist=`0.557530`, expected=low

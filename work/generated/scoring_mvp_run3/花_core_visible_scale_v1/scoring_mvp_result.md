# Holistic 序列打分 MVP 结果

## 口径说明

- 本结果是 prototype sanity check，不是已校准的真实用户评分。
- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。
- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。

## 输入

- 标准序列：`work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`
- 查询序列：`work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`
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

- 正例最低分：`80.311`
- 负例最高分：`31.323`
- 分离 margin：`48.987`
- 门控是否通过：`True`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- trim_both_10pct [target_positive_variant]: score=`98.643`, dtw=`0.000434`, total_dist=`0.002263`, expected=high
- trim_start_20pct [target_positive_variant]: score=`98.614`, dtw=`0.000414`, total_dist=`0.002293`, expected=high
- trim_end_20pct [target_positive_variant]: score=`97.167`, dtw=`0.000764`, total_dist=`0.004663`, expected=high
- subsample_even [target_positive_variant]: score=`94.288`, dtw=`0.015397`, total_dist=`0.018537`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`80.406`, dtw=`0.028738`, total_dist=`0.031622`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`80.311`, dtw=`0.028654`, total_dist=`0.031794`, expected=high
- fake_shuffle_frames [synthetic_fake_action]: score=`31.323`, dtw=`0.031855`, total_dist=`0.139297`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`21.673`, dtw=`0.098171`, total_dist=`0.183490`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`20.405`, dtw=`0.036575`, total_dist=`0.190726`, expected=low
- other_demo_跳 [other_demo_action]: score=`15.090`, dtw=`0.064321`, total_dist=`0.226938`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`12.562`, dtw=`0.052070`, total_dist=`0.248943`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`3.894`, dtw=`0.030750`, total_dist=`0.389480`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`2.125`, dtw=`0.028345`, total_dist=`0.462179`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`1.405`, dtw=`0.030774`, total_dist=`0.511821`, expected=low

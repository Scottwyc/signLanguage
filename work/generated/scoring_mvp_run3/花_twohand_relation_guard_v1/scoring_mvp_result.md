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

- 正例最低分：`90.736`
- 负例最高分：`14.810`
- 分离 margin：`75.927`
- 门控是否通过：`True`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`98.991`, dtw=`0.000152`, total_dist=`0.001316`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`98.895`, dtw=`0.000177`, total_dist=`0.001448`, expected=high
- trim_both_10pct [target_positive_variant]: score=`98.419`, dtw=`0.000434`, total_dist=`0.002194`, expected=high
- trim_start_20pct [target_positive_variant]: score=`98.077`, dtw=`0.001286`, total_dist=`0.003165`, expected=high
- trim_end_20pct [target_positive_variant]: score=`95.477`, dtw=`0.000764`, total_dist=`0.006051`, expected=high
- subsample_even [target_positive_variant]: score=`90.736`, dtw=`0.022088`, total_dist=`0.026022`, expected=high
- fake_shuffle_frames [synthetic_fake_action]: score=`14.810`, dtw=`0.049801`, total_dist=`0.229187`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`11.641`, dtw=`0.163980`, total_dist=`0.258072`, expected=low
- other_demo_跳 [other_demo_action]: score=`9.115`, dtw=`0.119843`, total_dist=`0.287425`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`6.645`, dtw=`0.089437`, total_dist=`0.325359`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`5.882`, dtw=`0.138144`, total_dist=`0.339983`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`0.981`, dtw=`0.053810`, total_dist=`0.554877`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`0.428`, dtw=`0.177675`, total_dist=`0.654453`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.154`, dtw=`0.177974`, total_dist=`0.777069`, expected=low

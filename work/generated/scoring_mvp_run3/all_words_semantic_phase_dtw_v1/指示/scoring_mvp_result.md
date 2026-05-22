# Holistic 序列打分 MVP 结果

## 口径说明

- 本结果是 prototype sanity check，不是已校准的真实用户评分。
- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。
- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。

## 输入

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/指示/指示_holistic_results.json`
- 查询序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/指示/指示_holistic_results.json`
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
- pose: `0.005283`
- face: `0.005443`
- missing: `0.000000`
- base_weighted: `0.000000`
- semantic_phase_gap: `0.000000`
- semantic_phase_penalty: `0.000000`
- weighted: `0.000000`
- hand_side_swapped: `0.000000`

### 最差对齐点

- standard frame 0 vs query frame 0: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 0 vs query frame 2: weighted=0.000000, left=0.000000, right=0.000000, pose=0.053985, missing=0.000000
- standard frame 0 vs query frame 4: weighted=0.000000, left=0.000000, right=0.000000, pose=0.093839, missing=0.000000
- standard frame 2 vs query frame 4: weighted=0.000000, left=0.000000, right=0.000000, pose=0.083168, missing=0.000000
- standard frame 4 vs query frame 4: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000

## 判别性套件

- 正例最低分：`49.757`
- 负例最高分：`13.847`
- 分离 margin：`35.910`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`91.596`, dtw=`0.000282`, total_dist=`0.010618`, expected=high
- trim_both_10pct [target_positive_variant]: score=`91.577`, dtw=`0.001505`, total_dist=`0.011011`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`90.514`, dtw=`0.000325`, total_dist=`0.012058`, expected=high
- trim_end_20pct [target_positive_variant]: score=`89.313`, dtw=`0.000754`, total_dist=`0.013790`, expected=high
- subsample_even [target_positive_variant]: score=`79.325`, dtw=`0.017055`, total_dist=`0.032910`, expected=high
- trim_start_20pct [target_positive_variant]: score=`49.757`, dtw=`0.001721`, total_dist=`0.083763`, expected=high
- other_demo_花 [other_demo_action]: score=`13.847`, dtw=`0.120445`, total_dist=`0.237251`, expected=low
- other_demo_汽车 [other_demo_action]: score=`12.416`, dtw=`0.049002`, total_dist=`0.250338`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`8.872`, dtw=`0.146592`, total_dist=`0.290671`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`8.679`, dtw=`0.050904`, total_dist=`0.293315`, expected=low
- other_demo_月亮 [other_demo_action]: score=`8.370`, dtw=`0.109894`, total_dist=`0.297661`, expected=low
- other_demo_跳 [other_demo_action]: score=`4.689`, dtw=`0.230237`, total_dist=`0.367185`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`4.340`, dtw=`0.057958`, total_dist=`0.376483`, expected=low
- other_demo_谗_羡慕 [other_demo_action]: score=`3.985`, dtw=`0.100375`, total_dist=`0.386714`, expected=low
- other_demo_朋友 [other_demo_action]: score=`2.533`, dtw=`0.189528`, total_dist=`0.441073`, expected=low
- other_demo_虎 [other_demo_action]: score=`2.181`, dtw=`0.240179`, total_dist=`0.459067`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`0.348`, dtw=`0.072934`, total_dist=`0.679206`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`0.285`, dtw=`0.362679`, total_dist=`0.703314`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.001`, dtw=`0.497038`, total_dist=`1.341573`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`0.000`, dtw=`1.046991`, total_dist=`2.116230`, expected=low

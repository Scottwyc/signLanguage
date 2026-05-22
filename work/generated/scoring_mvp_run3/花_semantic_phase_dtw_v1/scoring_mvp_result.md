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

- 正例最低分：`71.568`
- 负例最高分：`29.534`
- 分离 margin：`42.034`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`90.515`, dtw=`0.000154`, total_dist=`0.012005`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`89.559`, dtw=`0.000178`, total_dist=`0.013286`, expected=high
- trim_both_10pct [target_positive_variant]: score=`85.718`, dtw=`0.000434`, total_dist=`0.018624`, expected=high
- trim_start_20pct [target_positive_variant]: score=`85.105`, dtw=`0.000417`, total_dist=`0.019479`, expected=high
- subsample_even [target_positive_variant]: score=`80.918`, dtw=`0.011296`, total_dist=`0.028797`, expected=high
- trim_end_20pct [target_positive_variant]: score=`71.568`, dtw=`0.000764`, total_dist=`0.040372`, expected=high
- other_demo_谗_羡慕 [other_demo_action]: score=`29.534`, dtw=`0.037848`, total_dist=`0.146354`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`23.161`, dtw=`0.025548`, total_dist=`0.175524`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`15.308`, dtw=`0.029687`, total_dist=`0.225213`, expected=low
- other_demo_朋友 [other_demo_action]: score=`12.268`, dtw=`0.147128`, total_dist=`0.251777`, expected=low
- other_demo_跳 [other_demo_action]: score=`11.878`, dtw=`0.083459`, total_dist=`0.255653`, expected=low
- other_demo_指示 [other_demo_action]: score=`11.595`, dtw=`0.164676`, total_dist=`0.258551`, expected=low
- other_demo_月亮 [other_demo_action]: score=`11.094`, dtw=`0.040569`, total_dist=`0.263851`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`9.867`, dtw=`0.063419`, total_dist=`0.277917`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`8.912`, dtw=`0.181495`, total_dist=`0.290127`, expected=low
- other_demo_汽车 [other_demo_action]: score=`7.435`, dtw=`0.034749`, total_dist=`0.311871`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`2.707`, dtw=`0.027672`, total_dist=`0.433119`, expected=low
- other_demo_虎 [other_demo_action]: score=`1.808`, dtw=`0.084585`, total_dist=`0.481570`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`1.479`, dtw=`0.025489`, total_dist=`0.505616`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.960`, dtw=`0.027656`, total_dist=`0.557530`, expected=low

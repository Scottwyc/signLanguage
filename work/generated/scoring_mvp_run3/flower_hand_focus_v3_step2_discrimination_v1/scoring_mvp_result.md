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
- pose: `0.022443`
- face: `0.036443`
- missing: `0.000000`
- weighted: `0.000000`
- hand_side_swapped: `0.000000`

### 最差对齐点

- standard frame 0 vs query frame 0: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 0 vs query frame 2: weighted=0.000000, left=0.000000, right=0.000000, pose=0.012657, missing=0.000000
- standard frame 0 vs query frame 4: weighted=0.000000, left=0.000000, right=0.000000, pose=0.032251, missing=0.000000
- standard frame 0 vs query frame 6: weighted=0.000000, left=0.000000, right=0.000000, pose=0.117032, missing=0.000000
- standard frame 0 vs query frame 8: weighted=0.000000, left=0.000000, right=0.000000, pose=0.171810, missing=0.000000

## 判别性套件

- 正例最低分：`71.371`
- 负例最高分：`38.415`
- 分离 margin：`32.956`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- trim_both_10pct [target_positive_variant]: score=`86.654`, dtw=`0.000419`, total_dist=`0.017189`, expected=high
- trim_start_20pct [target_positive_variant]: score=`85.014`, dtw=`0.000421`, total_dist=`0.019483`, expected=high
- subsample_even [target_positive_variant]: score=`79.007`, dtw=`0.014887`, total_dist=`0.028276`, expected=high
- trim_end_20pct [target_positive_variant]: score=`75.266`, dtw=`0.000429`, total_dist=`0.034097`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`72.176`, dtw=`0.028908`, total_dist=`0.039128`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`71.371`, dtw=`0.028819`, total_dist=`0.040474`, expected=high
- other_demo_谗_羡慕 [other_demo_action]: score=`38.415`, dtw=`0.033826`, total_dist=`0.114807`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`23.119`, dtw=`0.027957`, total_dist=`0.175743`, expected=low
- other_demo_朋友 [other_demo_action]: score=`18.982`, dtw=`0.139419`, total_dist=`0.199402`, expected=low
- other_demo_月亮 [other_demo_action]: score=`18.619`, dtw=`0.035832`, total_dist=`0.201718`, expected=low
- other_demo_指示 [other_demo_action]: score=`17.563`, dtw=`0.151802`, total_dist=`0.208726`, expected=low
- other_demo_跳 [other_demo_action]: score=`14.915`, dtw=`0.086491`, total_dist=`0.228338`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`14.637`, dtw=`0.057008`, total_dist=`0.230594`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`14.487`, dtw=`0.036206`, total_dist=`0.231826`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`14.097`, dtw=`0.170886`, total_dist=`0.235109`, expected=low
- other_demo_汽车 [other_demo_action]: score=`12.968`, dtw=`0.027702`, total_dist=`0.245125`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`2.806`, dtw=`0.029323`, total_dist=`0.428830`, expected=low
- other_demo_虎 [other_demo_action]: score=`2.342`, dtw=`0.089156`, total_dist=`0.450483`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`1.545`, dtw=`0.023208`, total_dist=`0.500409`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.995`, dtw=`0.029316`, total_dist=`0.553250`, expected=low

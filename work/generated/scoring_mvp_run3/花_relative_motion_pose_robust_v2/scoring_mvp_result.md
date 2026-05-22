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

- 正例最低分：`47.986`
- 负例最高分：`26.316`
- 分离 margin：`21.669`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`93.708`, dtw=`0.000138`, total_dist=`0.007888`, expected=high
- trim_start_20pct [target_positive_variant]: score=`91.944`, dtw=`0.000332`, total_dist=`0.010294`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`91.577`, dtw=`0.000160`, total_dist=`0.010662`, expected=high
- trim_both_10pct [target_positive_variant]: score=`89.396`, dtw=`0.000434`, total_dist=`0.013733`, expected=high
- trim_end_20pct [target_positive_variant]: score=`71.376`, dtw=`0.000764`, total_dist=`0.040961`, expected=high
- subsample_even [target_positive_variant]: score=`47.986`, dtw=`0.057900`, total_dist=`0.088112`, expected=high
- other_demo_谗_羡慕 [other_demo_action]: score=`26.316`, dtw=`0.035373`, total_dist=`0.160197`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`19.698`, dtw=`0.031154`, total_dist=`0.194961`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`14.228`, dtw=`0.026709`, total_dist=`0.233995`, expected=low
- other_demo_月亮 [other_demo_action]: score=`9.805`, dtw=`0.040079`, total_dist=`0.278670`, expected=low
- other_demo_指示 [other_demo_action]: score=`9.501`, dtw=`0.178938`, total_dist=`0.282448`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`8.271`, dtw=`0.079859`, total_dist=`0.299085`, expected=low
- other_demo_朋友 [other_demo_action]: score=`7.697`, dtw=`0.183870`, total_dist=`0.307723`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`7.120`, dtw=`0.196394`, total_dist=`0.317074`, expected=low
- other_demo_汽车 [other_demo_action]: score=`7.003`, dtw=`0.034190`, total_dist=`0.319063`, expected=low
- other_demo_跳 [other_demo_action]: score=`6.833`, dtw=`0.128284`, total_dist=`0.322004`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`1.471`, dtw=`0.084535`, total_dist=`0.506346`, expected=low
- other_demo_虎 [other_demo_action]: score=`1.164`, dtw=`0.099492`, total_dist=`0.534402`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`0.710`, dtw=`0.096048`, total_dist=`0.593680`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.651`, dtw=`0.084901`, total_dist=`0.604207`, expected=low

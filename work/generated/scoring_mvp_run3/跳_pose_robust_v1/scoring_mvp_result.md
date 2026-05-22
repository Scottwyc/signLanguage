# Holistic 序列打分 MVP 结果

## 口径说明

- 本结果是 prototype sanity check，不是已校准的真实用户评分。
- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。
- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。

## 输入

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`
- 查询序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`
- 特征模式：`landmark`

## 主对齐结果

- prototype_score：`100.000`
- dtw_distance：`0.000000`
- normalized_distance：`0.000000`
- DTW path length：`8`
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
- pose: `0.000000`
- face: `0.000000`
- missing: `0.000000`
- base_weighted: `0.000000`
- semantic_phase_gap: `0.000000`
- semantic_phase_penalty: `0.000000`
- weighted: `0.000000`
- hand_side_swapped: `0.000000`

### 最差对齐点

- standard frame 12 vs query frame 12: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 14 vs query frame 14: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 16 vs query frame 16: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 18 vs query frame 18: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 20 vs query frame 20: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000

## 判别性套件

- 正例最低分：`80.088`
- 负例最高分：`39.639`
- 分离 margin：`40.448`
- 门控是否通过：`True`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`96.884`, dtw=`0.000321`, total_dist=`0.005810`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`96.087`, dtw=`0.000380`, total_dist=`0.007318`, expected=high
- trim_end_20pct [target_positive_variant]: score=`94.856`, dtw=`0.004524`, total_dist=`0.011089`, expected=high
- trim_both_10pct [target_positive_variant]: score=`94.837`, dtw=`0.004579`, total_dist=`0.011144`, expected=high
- trim_start_20pct [target_positive_variant]: score=`93.862`, dtw=`0.005076`, total_dist=`0.013179`, expected=high
- subsample_even [target_positive_variant]: score=`80.088`, dtw=`0.031138`, total_dist=`0.050867`, expected=high
- other_demo_花 [other_demo_action]: score=`39.639`, dtw=`0.086428`, total_dist=`0.166563`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`36.881`, dtw=`0.035056`, total_dist=`0.119698`, expected=low
- other_demo_虎 [other_demo_action]: score=`19.478`, dtw=`0.155203`, total_dist=`0.294463`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`17.394`, dtw=`0.100035`, total_dist=`0.314825`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`15.757`, dtw=`0.227351`, total_dist=`0.332614`, expected=low
- other_demo_谗_羡慕 [other_demo_action]: score=`12.443`, dtw=`0.133651`, total_dist=`0.375122`, expected=low
- other_demo_月亮 [other_demo_action]: score=`11.352`, dtw=`0.273310`, total_dist=`0.391635`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`11.256`, dtw=`0.074206`, total_dist=`0.393165`, expected=low
- other_demo_汽车 [other_demo_action]: score=`9.610`, dtw=`0.337302`, total_dist=`0.421620`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`8.748`, dtw=`0.211687`, total_dist=`0.438543`, expected=low
- other_demo_指示 [other_demo_action]: score=`6.772`, dtw=`0.305511`, total_dist=`0.484624`, expected=low
- other_demo_朋友 [other_demo_action]: score=`3.220`, dtw=`0.320540`, total_dist=`0.618459`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`0.066`, dtw=`0.862502`, total_dist=`1.316893`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.034`, dtw=`0.657335`, total_dist=`1.438925`, expected=low

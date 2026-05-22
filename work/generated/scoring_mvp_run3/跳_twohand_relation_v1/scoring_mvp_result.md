# Holistic 序列打分 MVP 结果

## 口径说明

- 本结果是 prototype sanity check，不是已校准的真实用户评分。
- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。
- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。

## 输入

- 标准序列：`work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`
- 查询序列：`work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`
- 特征模式：`landmark`

## 主对齐结果

- prototype_score：`100.000`
- dtw_distance：`0.000000`
- normalized_distance：`0.000000`
- DTW path length：`9`
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

- standard frame 6 vs query frame 6: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 8 vs query frame 8: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 10 vs query frame 10: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 12 vs query frame 12: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 14 vs query frame 14: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000

## 判别性套件

- 正例最低分：`76.823`
- 负例最高分：`31.418`
- 分离 margin：`45.406`
- 门控是否通过：`True`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`95.519`, dtw=`0.005318`, total_dist=`0.009642`, expected=high
- subsample_even [target_positive_variant]: score=`81.486`, dtw=`0.033001`, total_dist=`0.046296`, expected=high
- trim_end_20pct [target_positive_variant]: score=`81.001`, dtw=`0.045784`, total_dist=`0.051782`, expected=high
- trim_both_10pct [target_positive_variant]: score=`80.985`, dtw=`0.045835`, total_dist=`0.051833`, expected=high
- trim_start_20pct [target_positive_variant]: score=`80.586`, dtw=`0.046248`, total_dist=`0.052818`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`76.823`, dtw=`0.049949`, total_dist=`0.062227`, expected=high
- fake_static_hold [synthetic_fake_action]: score=`31.418`, dtw=`0.051539`, total_dist=`0.138935`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`21.538`, dtw=`0.070912`, total_dist=`0.260559`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`20.525`, dtw=`0.113888`, total_dist=`0.268735`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`18.058`, dtw=`0.196868`, total_dist=`0.290469`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`9.019`, dtw=`0.277684`, total_dist=`0.408287`, expected=low
- other_demo_花 [other_demo_action]: score=`6.227`, dtw=`0.221525`, total_dist=`0.471140`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.146`, dtw=`0.694568`, total_dist=`1.108469`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`0.122`, dtw=`0.872543`, total_dist=`1.139125`, expected=low

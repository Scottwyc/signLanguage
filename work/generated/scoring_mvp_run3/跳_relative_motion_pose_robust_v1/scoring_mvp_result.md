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

- 正例最低分：`52.988`
- 负例最高分：`42.773`
- 分离 margin：`10.215`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- trim_end_20pct [target_positive_variant]: score=`95.650`, dtw=`0.004624`, total_dist=`0.009624`, expected=high
- trim_both_10pct [target_positive_variant]: score=`95.629`, dtw=`0.004685`, total_dist=`0.009685`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`95.207`, dtw=`0.007727`, total_dist=`0.011546`, expected=high
- trim_start_20pct [target_positive_variant]: score=`94.712`, dtw=`0.005236`, total_dist=`0.011613`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`94.426`, dtw=`0.007769`, total_dist=`0.013043`, expected=high
- subsample_even [target_positive_variant]: score=`52.988`, dtw=`0.065433`, total_dist=`0.114319`, expected=high
- other_demo_花 [other_demo_action]: score=`42.773`, dtw=`0.097775`, total_dist=`0.152869`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`35.663`, dtw=`0.052285`, total_dist=`0.123727`, expected=low
- other_demo_虎 [other_demo_action]: score=`22.743`, dtw=`0.168187`, total_dist=`0.266564`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`21.376`, dtw=`0.135542`, total_dist=`0.277721`, expected=low
- other_demo_谗_羡慕 [other_demo_action]: score=`19.949`, dtw=`0.132365`, total_dist=`0.290157`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`18.604`, dtw=`0.230955`, total_dist=`0.302726`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`14.778`, dtw=`0.130394`, total_dist=`0.344163`, expected=low
- other_demo_月亮 [other_demo_action]: score=`12.884`, dtw=`0.288177`, total_dist=`0.368853`, expected=low
- other_demo_汽车 [other_demo_action]: score=`12.116`, dtw=`0.323672`, total_dist=`0.379921`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`11.981`, dtw=`0.239147`, total_dist=`0.381939`, expected=low
- other_demo_指示 [other_demo_action]: score=`10.546`, dtw=`0.280148`, total_dist=`0.404904`, expected=low
- other_demo_朋友 [other_demo_action]: score=`5.397`, dtw=`0.329677`, total_dist=`0.525467`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`0.299`, dtw=`0.750518`, total_dist=`1.046014`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.051`, dtw=`0.816436`, total_dist=`1.366067`, expected=low

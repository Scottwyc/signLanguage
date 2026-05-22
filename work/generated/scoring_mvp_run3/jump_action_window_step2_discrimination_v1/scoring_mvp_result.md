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
- DTW path length：`13`
- sequence_penalty：`0.000000`

### 分组平均距离

- left_hand: `0.000000`
- right_hand: `0.000000`
- left_hand_shape: `0.000000`
- right_hand_shape: `0.000000`
- pose: `0.000000`
- face: `0.000000`
- missing: `0.000000`
- weighted: `0.000000`
- hand_side_swapped: `0.000000`

### 最差对齐点

- standard frame 2 vs query frame 2: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 4 vs query frame 4: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 6 vs query frame 6: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 8 vs query frame 8: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 10 vs query frame 10: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000

## 判别性套件

- 正例最低分：`45.689`
- 负例最高分：`30.294`
- 分离 margin：`15.395`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- trim_end_20pct [target_positive_variant]: score=`93.564`, dtw=`0.001385`, total_dist=`0.007983`, expected=high
- trim_both_10pct [target_positive_variant]: score=`89.054`, dtw=`0.002769`, total_dist=`0.013911`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`85.748`, dtw=`0.006652`, total_dist=`0.018450`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`81.901`, dtw=`0.008934`, total_dist=`0.023959`, expected=high
- subsample_even [target_positive_variant]: score=`68.477`, dtw=`0.026404`, total_dist=`0.045441`, expected=high
- trim_start_20pct [target_positive_variant]: score=`45.689`, dtw=`0.023863`, total_dist=`0.093996`, expected=high
- other_demo_谗_羡慕 [other_demo_action]: score=`30.294`, dtw=`0.084909`, total_dist=`0.143305`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`25.793`, dtw=`0.138591`, total_dist=`0.162607`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`24.041`, dtw=`0.078875`, total_dist=`0.171047`, expected=low
- other_demo_花 [other_demo_action]: score=`21.844`, dtw=`0.052672`, total_dist=`0.182551`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`15.087`, dtw=`0.060356`, total_dist=`0.226960`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`12.573`, dtw=`0.088773`, total_dist=`0.248836`, expected=low
- other_demo_月亮 [other_demo_action]: score=`9.419`, dtw=`0.123333`, total_dist=`0.283498`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`8.260`, dtw=`0.268130`, total_dist=`0.299244`, expected=low
- other_demo_朋友 [other_demo_action]: score=`6.964`, dtw=`0.255870`, total_dist=`0.319738`, expected=low
- other_demo_汽车 [other_demo_action]: score=`6.893`, dtw=`0.126070`, total_dist=`0.320959`, expected=low
- other_demo_指示 [other_demo_action]: score=`4.042`, dtw=`0.331392`, total_dist=`0.385007`, expected=low
- other_demo_虎 [other_demo_action]: score=`3.207`, dtw=`0.204951`, total_dist=`0.412791`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.060`, dtw=`0.596843`, total_dist=`0.890455`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`0.008`, dtw=`0.951052`, total_dist=`1.126613`, expected=low

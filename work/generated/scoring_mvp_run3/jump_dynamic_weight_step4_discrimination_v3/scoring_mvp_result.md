# Holistic 序列打分 MVP 结果

## 口径说明

- 本结果是 prototype sanity check，不是已校准的真实用户评分。
- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。
- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。

## 输入

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache_v2/results/跳/跳_holistic_results.json`
- 查询序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache_v2/results/跳/跳_holistic_results.json`
- 特征模式：`landmark`

## 主对齐结果

- prototype_score：`100.000`
- dtw_distance：`0.000000`
- normalized_distance：`0.000000`
- DTW path length：`10`
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

- standard frame 0 vs query frame 0: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 4 vs query frame 4: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 8 vs query frame 8: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 12 vs query frame 12: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 16 vs query frame 16: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000

## 判别性套件

- 正例最低分：`76.754`
- 负例最高分：`41.452`
- 分离 margin：`35.302`
- 门控是否通过：`True`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`89.805`, dtw=`0.002876`, total_dist=`0.012904`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`88.726`, dtw=`0.002909`, total_dist=`0.014354`, expected=high
- trim_both_10pct [target_positive_variant]: score=`84.087`, dtw=`0.006218`, total_dist=`0.020798`, expected=high
- trim_end_20pct [target_positive_variant]: score=`79.433`, dtw=`0.008288`, total_dist=`0.027631`, expected=high
- trim_start_20pct [target_positive_variant]: score=`78.986`, dtw=`0.011848`, total_dist=`0.028309`, expected=high
- subsample_even [target_positive_variant]: score=`76.754`, dtw=`0.023420`, total_dist=`0.031748`, expected=high
- other_demo_谗_羡慕 [other_demo_action]: score=`41.452`, dtw=`0.033260`, total_dist=`0.105677`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`37.732`, dtw=`0.038298`, total_dist=`0.116961`, expected=low
- other_demo_汽车 [other_demo_action]: score=`33.004`, dtw=`0.027091`, total_dist=`0.133026`, expected=low
- other_demo_月亮 [other_demo_action]: score=`32.284`, dtw=`0.056993`, total_dist=`0.135673`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`26.616`, dtw=`0.031537`, total_dist=`0.158840`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`25.733`, dtw=`0.111639`, total_dist=`0.162886`, expected=low
- other_demo_花 [other_demo_action]: score=`20.733`, dtw=`0.042977`, total_dist=`0.188812`, expected=low
- other_demo_朋友 [other_demo_action]: score=`13.276`, dtw=`0.195632`, total_dist=`0.242302`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`11.258`, dtw=`0.168201`, total_dist=`0.262087`, expected=low
- other_demo_指示 [other_demo_action]: score=`9.095`, dtw=`0.256030`, total_dist=`0.287687`, expected=low
- other_demo_虎 [other_demo_action]: score=`8.698`, dtw=`0.113895`, total_dist=`0.293048`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`2.322`, dtw=`0.072582`, total_dist=`0.451533`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.005`, dtw=`0.593475`, total_dist=`1.181747`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`0.001`, dtw=`0.923482`, total_dist=`1.408516`, expected=low

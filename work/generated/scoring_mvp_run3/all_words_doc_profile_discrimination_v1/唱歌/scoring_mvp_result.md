# Holistic 序列打分 MVP 结果

## 口径说明

- 本结果是 prototype sanity check，不是已校准的真实用户评分。
- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。
- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。

## 输入

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/唱歌/唱歌_holistic_results.json`
- 查询序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/唱歌/唱歌_holistic_results.json`
- 特征模式：`landmark`

## 主对齐结果

- prototype_score：`100.000`
- dtw_distance：`0.000000`
- normalized_distance：`0.000000`
- DTW path length：`27`
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
- standard frame 2 vs query frame 2: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 4 vs query frame 4: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 6 vs query frame 6: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 8 vs query frame 8: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000

## 判别性套件

- 正例最低分：`58.725`
- 负例最高分：`13.352`
- 分离 margin：`45.374`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`91.614`, dtw=`0.000291`, total_dist=`0.010510`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`90.461`, dtw=`0.000339`, total_dist=`0.012030`, expected=high
- trim_end_20pct [target_positive_variant]: score=`88.476`, dtw=`0.001636`, total_dist=`0.014693`, expected=high
- subsample_even [target_positive_variant]: score=`68.722`, dtw=`0.037516`, total_dist=`0.045011`, expected=high
- trim_both_10pct [target_positive_variant]: score=`64.695`, dtw=`0.001714`, total_dist=`0.052258`, expected=high
- trim_start_20pct [target_positive_variant]: score=`58.725`, dtw=`0.000818`, total_dist=`0.063876`, expected=high
- other_demo_花 [other_demo_action]: score=`13.352`, dtw=`0.189949`, total_dist=`0.241625`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`8.331`, dtw=`0.112959`, total_dist=`0.298220`, expected=low
- other_demo_跳 [other_demo_action]: score=`7.655`, dtw=`0.268495`, total_dist=`0.308380`, expected=low
- other_demo_月亮 [other_demo_action]: score=`7.621`, dtw=`0.236523`, total_dist=`0.308913`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`7.464`, dtw=`0.247241`, total_dist=`0.311417`, expected=low
- other_demo_汽车 [other_demo_action]: score=`7.308`, dtw=`0.217285`, total_dist=`0.313938`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`6.322`, dtw=`0.160152`, total_dist=`0.331334`, expected=low
- other_demo_虎 [other_demo_action]: score=`5.095`, dtw=`0.323585`, total_dist=`0.357240`, expected=low
- other_demo_谗_羡慕 [other_demo_action]: score=`4.460`, dtw=`0.277501`, total_dist=`0.373210`, expected=low
- other_demo_朋友 [other_demo_action]: score=`2.884`, dtw=`0.251101`, total_dist=`0.425501`, expected=low
- other_demo_指示 [other_demo_action]: score=`1.644`, dtw=`0.309038`, total_dist=`0.493000`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`0.934`, dtw=`0.115805`, total_dist=`0.560829`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`0.000`, dtw=`1.160323`, total_dist=`1.634616`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.000`, dtw=`1.098319`, total_dist=`1.714468`, expected=low

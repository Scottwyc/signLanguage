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
- DTW path length：`15`
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

- standard frame 30 vs query frame 30: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 32 vs query frame 32: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 34 vs query frame 34: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 36 vs query frame 36: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 38 vs query frame 38: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000

## 判别性套件

- 正例最低分：`24.732`
- 负例最高分：`41.971`
- 分离 margin：`-17.239`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- trim_start_20pct [target_positive_variant]: score=`90.760`, dtw=`0.001385`, total_dist=`0.011634`, expected=high
- trim_end_20pct [target_positive_variant]: score=`90.760`, dtw=`0.001385`, total_dist=`0.011634`, expected=high
- trim_both_10pct [target_positive_variant]: score=`90.760`, dtw=`0.001385`, total_dist=`0.011634`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`80.775`, dtw=`0.020000`, total_dist=`0.025620`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`80.190`, dtw=`0.020000`, total_dist=`0.026492`, expected=high
- fake_shuffle_frames [synthetic_fake_action]: score=`41.971`, dtw=`0.013032`, total_dist=`0.104183`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`36.728`, dtw=`0.017495`, total_dist=`0.120195`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`33.604`, dtw=`0.005478`, total_dist=`0.130862`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`30.740`, dtw=`0.020000`, total_dist=`0.141552`, expected=low
- subsample_even [target_positive_variant]: score=`24.732`, dtw=`0.010874`, total_dist=`0.167650`, expected=high
- other_demo_香蕉 [other_demo_action]: score=`13.604`, dtw=`0.079249`, total_dist=`0.239374`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`10.692`, dtw=`0.020000`, total_dist=`0.268282`, expected=low
- other_demo_月亮 [other_demo_action]: score=`9.158`, dtw=`0.119056`, total_dist=`0.286868`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`4.652`, dtw=`0.100621`, total_dist=`0.368153`, expected=low
- other_demo_谗_羡慕 [other_demo_action]: score=`3.650`, dtw=`0.068182`, total_dist=`0.397251`, expected=low
- other_demo_指示 [other_demo_action]: score=`3.046`, dtw=`0.101308`, total_dist=`0.418977`, expected=low
- other_demo_跳 [other_demo_action]: score=`2.903`, dtw=`0.110148`, total_dist=`0.424733`, expected=low
- other_demo_虎 [other_demo_action]: score=`1.901`, dtw=`0.103254`, total_dist=`0.475547`, expected=low
- other_demo_汽车 [other_demo_action]: score=`1.720`, dtw=`0.325646`, total_dist=`0.487573`, expected=low
- other_demo_朋友 [other_demo_action]: score=`1.359`, dtw=`0.231201`, total_dist=`0.515854`, expected=low

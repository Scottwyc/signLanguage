# Holistic 序列打分 MVP 结果

## 口径说明

- 本结果是 prototype sanity check，不是已校准的真实用户评分。
- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。
- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。

## 输入

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache_v2/results/花/花_holistic_results.json`
- 查询序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache_v2/results/花/花_holistic_results.json`
- 特征模式：`landmark`

## 主对齐结果

- prototype_score：`100.000`
- dtw_distance：`0.000000`
- normalized_distance：`0.000000`
- DTW path length：`28`
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

- 正例最低分：`66.782`
- 负例最高分：`37.109`
- 分离 margin：`29.673`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- trim_start_20pct [target_positive_variant]: score=`90.154`, dtw=`0.003602`, total_dist=`0.012439`, expected=high
- trim_both_10pct [target_positive_variant]: score=`81.236`, dtw=`0.005068`, total_dist=`0.024937`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`77.815`, dtw=`0.025022`, total_dist=`0.030101`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`77.436`, dtw=`0.025026`, total_dist=`0.030686`, expected=high
- subsample_even [target_positive_variant]: score=`74.819`, dtw=`0.014409`, total_dist=`0.034812`, expected=high
- trim_end_20pct [target_positive_variant]: score=`66.782`, dtw=`0.008035`, total_dist=`0.048448`, expected=high
- fake_shuffle_frames [synthetic_fake_action]: score=`37.109`, dtw=`0.026358`, total_dist=`0.118956`, expected=low
- other_demo_case [other_demo_action]: score=`33.746`, dtw=`0.035982`, total_dist=`0.130357`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`28.962`, dtw=`0.036565`, total_dist=`0.148704`, expected=low
- other_demo_case [other_demo_action]: score=`23.570`, dtw=`0.043300`, total_dist=`0.173423`, expected=low
- other_demo_case [other_demo_action]: score=`17.606`, dtw=`0.046753`, total_dist=`0.208433`, expected=low
- other_demo_case [other_demo_action]: score=`14.046`, dtw=`0.098288`, total_dist=`0.235538`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`12.673`, dtw=`0.024013`, total_dist=`0.247884`, expected=low
- other_demo_case [other_demo_action]: score=`12.363`, dtw=`0.172262`, total_dist=`0.250854`, expected=low
- other_demo_case [other_demo_action]: score=`11.653`, dtw=`0.176490`, total_dist=`0.257951`, expected=low
- other_demo_case [other_demo_action]: score=`11.295`, dtw=`0.150640`, total_dist=`0.261701`, expected=low
- other_demo_case [other_demo_action]: score=`11.045`, dtw=`0.091539`, total_dist=`0.264384`, expected=low
- other_demo_case [other_demo_action]: score=`5.132`, dtw=`0.133892`, total_dist=`0.356369`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`3.957`, dtw=`0.073971`, total_dist=`0.387565`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`2.797`, dtw=`0.087353`, total_dist=`0.429177`, expected=low

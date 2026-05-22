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

- 正例最低分：`78.112`
- 负例最高分：`49.732`
- 分离 margin：`28.380`
- 门控是否通过：`True`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- trim_start_20pct [target_positive_variant]: score=`90.154`, dtw=`0.003602`, total_dist=`0.012439`, expected=high
- trim_both_10pct [target_positive_variant]: score=`88.121`, dtw=`0.005068`, total_dist=`0.015175`, expected=high
- subsample_even [target_positive_variant]: score=`83.507`, dtw=`0.014409`, total_dist=`0.021628`, expected=high
- trim_end_20pct [target_positive_variant]: score=`80.563`, dtw=`0.008035`, total_dist=`0.025936`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`78.494`, dtw=`0.025022`, total_dist=`0.029058`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`78.112`, dtw=`0.025026`, total_dist=`0.029643`, expected=high
- fake_shuffle_frames [synthetic_fake_action]: score=`49.732`, dtw=`0.026358`, total_dist=`0.083822`, expected=low
- other_demo_case [other_demo_action]: score=`38.024`, dtw=`0.035982`, total_dist=`0.116036`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`25.099`, dtw=`0.036565`, total_dist=`0.165883`, expected=low
- other_demo_case [other_demo_action]: score=`24.629`, dtw=`0.043300`, total_dist=`0.168150`, expected=low
- other_demo_case [other_demo_action]: score=`23.191`, dtw=`0.046753`, total_dist=`0.175368`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`17.237`, dtw=`0.024013`, total_dist=`0.210973`, expected=low
- other_demo_case [other_demo_action]: score=`16.613`, dtw=`0.098288`, total_dist=`0.215398`, expected=low
- other_demo_case [other_demo_action]: score=`15.523`, dtw=`0.176490`, total_dist=`0.223542`, expected=low
- other_demo_case [other_demo_action]: score=`14.678`, dtw=`0.150640`, total_dist=`0.230255`, expected=low
- other_demo_case [other_demo_action]: score=`14.655`, dtw=`0.091539`, total_dist=`0.230445`, expected=low
- other_demo_case [other_demo_action]: score=`14.082`, dtw=`0.172262`, total_dist=`0.235229`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`13.418`, dtw=`0.073971`, total_dist=`0.241027`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`7.098`, dtw=`0.087353`, total_dist=`0.317445`, expected=low
- other_demo_case [other_demo_action]: score=`6.355`, dtw=`0.133892`, total_dist=`0.330707`, expected=low

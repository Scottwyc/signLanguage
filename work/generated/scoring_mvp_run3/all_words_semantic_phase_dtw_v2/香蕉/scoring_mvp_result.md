# Holistic 序列打分 MVP 结果

## 口径说明

- 本结果是 prototype sanity check，不是已校准的真实用户评分。
- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。
- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。

## 输入

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/香蕉/香蕉_holistic_results.json`
- 查询序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/香蕉/香蕉_holistic_results.json`
- 特征模式：`landmark`

## 主对齐结果

- prototype_score：`100.000`
- dtw_distance：`0.000000`
- normalized_distance：`0.000000`
- DTW path length：`45`
- sequence_penalty：`0.000000`

### 分组平均距离

- left_hand: `0.000000`
- right_hand: `0.000000`
- left_hand_shape: `0.000000`
- right_hand_shape: `0.000000`
- pose: `0.005251`
- face: `0.005040`
- missing: `0.000000`
- base_weighted: `0.000000`
- semantic_phase_gap: `0.000000`
- semantic_phase_penalty: `0.000000`
- weighted: `0.000000`
- hand_side_swapped: `0.000000`

### 最差对齐点

- standard frame 0 vs query frame 0: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 0 vs query frame 2: weighted=0.000000, left=0.000000, right=0.000000, pose=0.064373, missing=0.000000
- standard frame 0 vs query frame 4: weighted=0.000000, left=0.000000, right=0.000000, pose=0.039270, missing=0.000000
- standard frame 0 vs query frame 6: weighted=0.000000, left=0.000000, right=0.000000, pose=0.066311, missing=0.000000
- standard frame 2 vs query frame 6: weighted=0.000000, left=0.000000, right=0.000000, pose=0.073333, missing=0.000000

## 判别性套件

- 正例最低分：`46.612`
- 负例最高分：`18.503`
- 分离 margin：`28.108`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`91.804`, dtw=`0.000296`, total_dist=`0.010454`, expected=high
- trim_both_10pct [target_positive_variant]: score=`90.682`, dtw=`0.001064`, total_dist=`0.012429`, expected=high
- trim_end_20pct [target_positive_variant]: score=`89.608`, dtw=`0.001065`, total_dist=`0.013860`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`89.496`, dtw=`0.000346`, total_dist=`0.013542`, expected=high
- subsample_even [target_positive_variant]: score=`69.925`, dtw=`0.023287`, total_dist=`0.058067`, expected=high
- trim_start_20pct [target_positive_variant]: score=`46.612`, dtw=`0.002638`, total_dist=`0.091599`, expected=high
- other_demo_朋友 [other_demo_action]: score=`18.503`, dtw=`0.093980`, total_dist=`0.202465`, expected=low
- other_demo_跳 [other_demo_action]: score=`13.908`, dtw=`0.115053`, total_dist=`0.236724`, expected=low
- other_demo_指示 [other_demo_action]: score=`11.126`, dtw=`0.121728`, total_dist=`0.263509`, expected=low
- other_demo_谗_羡慕 [other_demo_action]: score=`11.120`, dtw=`0.104864`, total_dist=`0.263571`, expected=low
- other_demo_汽车 [other_demo_action]: score=`10.719`, dtw=`0.048309`, total_dist=`0.267981`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`8.641`, dtw=`0.050218`, total_dist=`0.293841`, expected=low
- other_demo_月亮 [other_demo_action]: score=`8.028`, dtw=`0.106561`, total_dist=`0.302673`, expected=low
- other_demo_花 [other_demo_action]: score=`6.857`, dtw=`0.053316`, total_dist=`0.321587`, expected=low
- other_demo_虎 [other_demo_action]: score=`4.872`, dtw=`0.112011`, total_dist=`0.362611`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`3.833`, dtw=`0.054227`, total_dist=`0.391388`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`3.231`, dtw=`0.256626`, total_dist=`0.411878`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`0.105`, dtw=`0.168577`, total_dist=`0.823575`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.006`, dtw=`0.340434`, total_dist=`1.171704`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`0.000`, dtw=`0.730649`, total_dist=`1.775179`, expected=low

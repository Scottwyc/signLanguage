# Holistic 序列打分 MVP 结果

## 口径说明

- 本结果是 prototype sanity check，不是已校准的真实用户评分。
- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。
- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。

## 输入

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/朋友/朋友_holistic_results.json`
- 查询序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/朋友/朋友_holistic_results.json`
- 特征模式：`landmark`

## 主对齐结果

- prototype_score：`100.000`
- dtw_distance：`0.000000`
- normalized_distance：`0.000000`
- DTW path length：`30`
- sequence_penalty：`0.000000`

### 分组平均距离

- left_hand: `0.000000`
- right_hand: `0.000000`
- left_hand_shape: `0.000000`
- right_hand_shape: `0.000000`
- pose: `0.005467`
- face: `0.008267`
- missing: `0.000000`
- base_weighted: `0.000000`
- semantic_phase_gap: `0.000000`
- semantic_phase_penalty: `0.000000`
- weighted: `0.000000`
- hand_side_swapped: `0.000000`

### 最差对齐点

- standard frame 0 vs query frame 0: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 2 vs query frame 2: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 4 vs query frame 4: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 6 vs query frame 6: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 6 vs query frame 8: weighted=0.000000, left=0.000000, right=0.000000, pose=0.097297, missing=0.000000

## 判别性套件

- 正例最低分：`58.372`
- 负例最高分：`17.573`
- 分离 margin：`40.799`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`92.264`, dtw=`0.000294`, total_dist=`0.009853`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`91.184`, dtw=`0.000342`, total_dist=`0.011297`, expected=high
- trim_both_10pct [target_positive_variant]: score=`87.931`, dtw=`0.002330`, total_dist=`0.016949`, expected=high
- trim_end_20pct [target_positive_variant]: score=`87.903`, dtw=`0.001830`, total_dist=`0.016662`, expected=high
- trim_start_20pct [target_positive_variant]: score=`86.090`, dtw=`0.001036`, total_dist=`0.018646`, expected=high
- subsample_even [target_positive_variant]: score=`58.372`, dtw=`0.043279`, total_dist=`0.064600`, expected=high
- other_demo_花 [other_demo_action]: score=`17.573`, dtw=`0.100538`, total_dist=`0.208658`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`16.392`, dtw=`0.054908`, total_dist=`0.217007`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`16.312`, dtw=`0.110295`, total_dist=`0.217591`, expected=low
- other_demo_汽车 [other_demo_action]: score=`13.629`, dtw=`0.063188`, total_dist=`0.239156`, expected=low
- other_demo_月亮 [other_demo_action]: score=`12.479`, dtw=`0.129717`, total_dist=`0.249731`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`11.476`, dtw=`0.064299`, total_dist=`0.259792`, expected=low
- other_demo_谗_羡慕 [other_demo_action]: score=`11.353`, dtw=`0.120443`, total_dist=`0.261087`, expected=low
- other_demo_跳 [other_demo_action]: score=`9.475`, dtw=`0.134382`, total_dist=`0.282786`, expected=low
- other_demo_虎 [other_demo_action]: score=`3.744`, dtw=`0.218253`, total_dist=`0.394216`, expected=low
- other_demo_指示 [other_demo_action]: score=`1.688`, dtw=`0.246147`, total_dist=`0.489772`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`1.504`, dtw=`0.188169`, total_dist=`0.503642`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`0.336`, dtw=`0.094396`, total_dist=`0.683461`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.004`, dtw=`0.416063`, total_dist=`1.230965`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`0.000`, dtw=`0.846227`, total_dist=`1.839109`, expected=low

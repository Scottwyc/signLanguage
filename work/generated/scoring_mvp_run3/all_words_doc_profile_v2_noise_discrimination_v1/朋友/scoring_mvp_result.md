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
- pose: `0.005667`
- face: `0.008569`
- missing: `0.000000`
- weighted: `0.000000`
- hand_side_swapped: `0.000000`

### 最差对齐点

- standard frame 0 vs query frame 0: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 2 vs query frame 2: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 4 vs query frame 4: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 6 vs query frame 6: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 6 vs query frame 8: weighted=0.000000, left=0.000000, right=0.000000, pose=0.097297, missing=0.000000

## 判别性套件

- 正例最低分：`65.334`
- 负例最高分：`24.093`
- 分离 margin：`41.241`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- trim_end_20pct [target_positive_variant]: score=`87.304`, dtw=`0.000818`, total_dist=`0.016539`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`86.403`, dtw=`0.000289`, total_dist=`0.017624`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`84.578`, dtw=`0.000335`, total_dist=`0.020200`, expected=high
- trim_both_10pct [target_positive_variant]: score=`83.085`, dtw=`0.002204`, total_dist=`0.022898`, expected=high
- trim_start_20pct [target_positive_variant]: score=`80.048`, dtw=`0.000818`, total_dist=`0.026951`, expected=high
- subsample_even [target_positive_variant]: score=`65.334`, dtw=`0.039325`, total_dist=`0.051080`, expected=high
- other_demo_香蕉 [other_demo_action]: score=`24.093`, dtw=`0.097392`, total_dist=`0.170789`, expected=low
- other_demo_汽车 [other_demo_action]: score=`21.783`, dtw=`0.048614`, total_dist=`0.182886`, expected=low
- other_demo_花 [other_demo_action]: score=`21.574`, dtw=`0.099020`, total_dist=`0.184043`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`19.352`, dtw=`0.050184`, total_dist=`0.197083`, expected=low
- other_demo_月亮 [other_demo_action]: score=`19.339`, dtw=`0.117546`, total_dist=`0.197168`, expected=low
- other_demo_谗_羡慕 [other_demo_action]: score=`16.106`, dtw=`0.117881`, total_dist=`0.219119`, expected=low
- other_demo_跳 [other_demo_action]: score=`13.604`, dtw=`0.134797`, total_dist=`0.239379`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`13.544`, dtw=`0.053425`, total_dist=`0.239908`, expected=low
- other_demo_虎 [other_demo_action]: score=`7.159`, dtw=`0.203203`, total_dist=`0.316418`, expected=low
- other_demo_指示 [other_demo_action]: score=`2.689`, dtw=`0.236356`, total_dist=`0.433898`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`2.200`, dtw=`0.186280`, total_dist=`0.458028`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`0.452`, dtw=`0.074636`, total_dist=`0.647954`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.012`, dtw=`0.403652`, total_dist=`1.085942`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`0.000`, dtw=`0.832103`, total_dist=`1.558267`, expected=low

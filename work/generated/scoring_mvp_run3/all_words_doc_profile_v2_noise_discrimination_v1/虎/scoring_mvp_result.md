# Holistic 序列打分 MVP 结果

## 口径说明

- 本结果是 prototype sanity check，不是已校准的真实用户评分。
- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。
- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。

## 输入

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/虎/虎_holistic_results.json`
- 查询序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/虎/虎_holistic_results.json`
- 特征模式：`landmark`

## 主对齐结果

- prototype_score：`100.000`
- dtw_distance：`0.000000`
- normalized_distance：`0.000000`
- DTW path length：`54`
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

- 正例最低分：`68.901`
- 负例最高分：`32.339`
- 分离 margin：`36.562`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`91.344`, dtw=`0.000215`, total_dist=`0.010865`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`90.266`, dtw=`0.000250`, total_dist=`0.012289`, expected=high
- trim_both_10pct [target_positive_variant]: score=`85.350`, dtw=`0.000693`, total_dist=`0.019009`, expected=high
- trim_end_20pct [target_positive_variant]: score=`78.119`, dtw=`0.000419`, total_dist=`0.029632`, expected=high
- subsample_even [target_positive_variant]: score=`70.128`, dtw=`0.034538`, total_dist=`0.042582`, expected=high
- trim_start_20pct [target_positive_variant]: score=`68.901`, dtw=`0.000837`, total_dist=`0.044699`, expected=high
- other_demo_汽车 [other_demo_action]: score=`32.339`, dtw=`0.075137`, total_dist=`0.135467`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`15.132`, dtw=`0.073759`, total_dist=`0.226600`, expected=low
- other_demo_谗_羡慕 [other_demo_action]: score=`10.272`, dtw=`0.167949`, total_dist=`0.273087`, expected=low
- other_demo_月亮 [other_demo_action]: score=`10.236`, dtw=`0.129489`, total_dist=`0.273508`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`7.964`, dtw=`0.179950`, total_dist=`0.303622`, expected=low
- other_demo_朋友 [other_demo_action]: score=`7.692`, dtw=`0.235450`, total_dist=`0.307800`, expected=low
- other_demo_跳 [other_demo_action]: score=`6.963`, dtw=`0.178322`, total_dist=`0.319748`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`6.119`, dtw=`0.070774`, total_dist=`0.335261`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`5.949`, dtw=`0.284038`, total_dist=`0.338641`, expected=low
- other_demo_指示 [other_demo_action]: score=`5.823`, dtw=`0.267821`, total_dist=`0.341199`, expected=low
- other_demo_花 [other_demo_action]: score=`2.193`, dtw=`0.126391`, total_dist=`0.458403`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`0.315`, dtw=`0.215234`, total_dist=`0.691317`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.003`, dtw=`0.581392`, total_dist=`1.252274`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`0.000`, dtw=`0.848399`, total_dist=`1.481309`, expected=low

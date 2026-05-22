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
- standard frame 8 vs query frame 8: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000

## 判别性套件

- 正例最低分：`58.672`
- 负例最高分：`10.296`
- 分离 margin：`48.376`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`95.179`, dtw=`0.000295`, total_dist=`0.005930`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`94.497`, dtw=`0.000345`, total_dist=`0.006793`, expected=high
- trim_end_20pct [target_positive_variant]: score=`90.770`, dtw=`0.001828`, total_dist=`0.011622`, expected=high
- trim_both_10pct [target_positive_variant]: score=`65.762`, dtw=`0.003766`, total_dist=`0.050295`, expected=high
- subsample_even [target_positive_variant]: score=`63.063`, dtw=`0.038559`, total_dist=`0.055324`, expected=high
- trim_start_20pct [target_positive_variant]: score=`58.672`, dtw=`0.002981`, total_dist=`0.063985`, expected=high
- other_demo_花 [other_demo_action]: score=`10.296`, dtw=`0.194154`, total_dist=`0.272811`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`6.524`, dtw=`0.117364`, total_dist=`0.327567`, expected=low
- other_demo_汽车 [other_demo_action]: score=`6.023`, dtw=`0.224358`, total_dist=`0.337154`, expected=low
- other_demo_跳 [other_demo_action]: score=`5.974`, dtw=`0.270395`, total_dist=`0.338132`, expected=low
- other_demo_月亮 [other_demo_action]: score=`5.730`, dtw=`0.243066`, total_dist=`0.343134`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`5.675`, dtw=`0.256503`, total_dist=`0.344294`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`5.236`, dtw=`0.168051`, total_dist=`0.353962`, expected=low
- other_demo_虎 [other_demo_action]: score=`3.941`, dtw=`0.325382`, total_dist=`0.388058`, expected=low
- other_demo_谗_羡慕 [other_demo_action]: score=`3.390`, dtw=`0.280389`, total_dist=`0.406128`, expected=low
- other_demo_朋友 [other_demo_action]: score=`2.276`, dtw=`0.257818`, total_dist=`0.453925`, expected=low
- other_demo_指示 [other_demo_action]: score=`1.227`, dtw=`0.315960`, total_dist=`0.528116`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`0.619`, dtw=`0.148506`, total_dist=`0.610147`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`0.000`, dtw=`1.163263`, total_dist=`1.747824`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.000`, dtw=`1.108934`, total_dist=`1.833473`, expected=low

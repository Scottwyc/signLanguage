# Holistic 序列打分 MVP 结果

## 口径说明

- 本结果是 prototype sanity check，不是已校准的真实用户评分。
- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。
- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。

## 输入

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`
- 查询序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`
- 特征模式：`landmark`

## 主对齐结果

- prototype_score：`100.000`
- dtw_distance：`0.000000`
- normalized_distance：`0.000000`
- DTW path length：`8`
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

- standard frame 12 vs query frame 12: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 14 vs query frame 14: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 16 vs query frame 16: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 18 vs query frame 18: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 20 vs query frame 20: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000

## 判别性套件

- 正例最低分：`81.017`
- 负例最高分：`43.731`
- 分离 margin：`37.286`
- 门控是否通过：`True`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`96.902`, dtw=`0.000288`, total_dist=`0.005766`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`96.456`, dtw=`0.000335`, total_dist=`0.006612`, expected=high
- trim_start_20pct [target_positive_variant]: score=`95.463`, dtw=`0.004500`, total_dist=`0.009933`, expected=high
- trim_end_20pct [target_positive_variant]: score=`95.463`, dtw=`0.004500`, total_dist=`0.009933`, expected=high
- trim_both_10pct [target_positive_variant]: score=`94.447`, dtw=`0.004500`, total_dist=`0.011859`, expected=high
- subsample_even [target_positive_variant]: score=`81.017`, dtw=`0.030912`, total_dist=`0.048712`, expected=high
- fake_static_hold [synthetic_fake_action]: score=`43.731`, dtw=`0.030253`, total_dist=`0.099254`, expected=low
- other_demo_花 [other_demo_action]: score=`42.245`, dtw=`0.088080`, total_dist=`0.155103`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`18.124`, dtw=`0.238588`, total_dist=`0.307424`, expected=low
- other_demo_虎 [other_demo_action]: score=`17.081`, dtw=`0.204763`, total_dist=`0.318094`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`16.280`, dtw=`0.123668`, total_dist=`0.326740`, expected=low
- other_demo_谗_羡慕 [other_demo_action]: score=`12.724`, dtw=`0.155483`, total_dist=`0.371097`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`11.485`, dtw=`0.076104`, total_dist=`0.389535`, expected=low
- other_demo_月亮 [other_demo_action]: score=`10.994`, dtw=`0.318047`, total_dist=`0.397407`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`9.409`, dtw=`0.230452`, total_dist=`0.425431`, expected=low
- other_demo_指示 [other_demo_action]: score=`7.880`, dtw=`0.313526`, total_dist=`0.457341`, expected=low
- other_demo_汽车 [other_demo_action]: score=`6.259`, dtw=`0.457040`, total_dist=`0.498803`, expected=low
- other_demo_朋友 [other_demo_action]: score=`5.255`, dtw=`0.316846`, total_dist=`0.530264`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`0.025`, dtw=`1.180764`, total_dist=`1.494506`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.005`, dtw=`1.168663`, total_dist=`1.788096`, expected=low

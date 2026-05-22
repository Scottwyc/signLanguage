# Holistic 序列打分 MVP 结果

## 口径说明

- 本结果是 prototype sanity check，不是已校准的真实用户评分。
- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。
- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。

## 输入

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache_v2/results/跳/跳_holistic_results.json`
- 查询序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache_v2/results/跳/跳_holistic_results.json`
- 特征模式：`landmark`

## 主对齐结果

- prototype_score：`100.000`
- dtw_distance：`0.000000`
- normalized_distance：`0.000000`
- DTW path length：`10`
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

- 正例最低分：`77.012`
- 负例最高分：`41.513`
- 分离 margin：`35.499`
- 门控是否通过：`True`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`89.621`, dtw=`0.003122`, total_dist=`0.013149`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`88.546`, dtw=`0.003152`, total_dist=`0.014597`, expected=high
- trim_both_10pct [target_positive_variant]: score=`83.608`, dtw=`0.006904`, total_dist=`0.021484`, expected=high
- trim_end_20pct [target_positive_variant]: score=`78.851`, dtw=`0.009169`, total_dist=`0.028513`, expected=high
- trim_start_20pct [target_positive_variant]: score=`78.532`, dtw=`0.012539`, total_dist=`0.029000`, expected=high
- subsample_even [target_positive_variant]: score=`77.012`, dtw=`0.023017`, total_dist=`0.031345`, expected=high
- other_demo_谗_羡慕 [other_demo_action]: score=`41.513`, dtw=`0.033083`, total_dist=`0.105501`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`35.075`, dtw=`0.047059`, total_dist=`0.125722`, expected=low
- other_demo_汽车 [other_demo_action]: score=`33.104`, dtw=`0.026728`, total_dist=`0.132663`, expected=low
- other_demo_月亮 [other_demo_action]: score=`32.674`, dtw=`0.055552`, total_dist=`0.134232`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`26.632`, dtw=`0.031462`, total_dist=`0.158765`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`21.674`, dtw=`0.132238`, total_dist=`0.183486`, expected=low
- other_demo_花 [other_demo_action]: score=`21.029`, dtw=`0.041275`, total_dist=`0.187110`, expected=low
- other_demo_朋友 [other_demo_action]: score=`13.920`, dtw=`0.189954`, total_dist=`0.236624`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`11.835`, dtw=`0.162208`, total_dist=`0.256094`, expected=low
- other_demo_指示 [other_demo_action]: score=`9.442`, dtw=`0.251546`, total_dist=`0.283203`, expected=low
- other_demo_虎 [other_demo_action]: score=`9.086`, dtw=`0.108658`, total_dist=`0.287811`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`2.342`, dtw=`0.071563`, total_dist=`0.450514`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.005`, dtw=`0.609472`, total_dist=`1.197745`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`0.001`, dtw=`0.951551`, total_dist=`1.436585`, expected=low

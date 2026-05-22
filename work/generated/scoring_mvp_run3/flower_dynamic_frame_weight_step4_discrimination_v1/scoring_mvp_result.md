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
- DTW path length：`34`
- sequence_penalty：`0.000000`

### 分组平均距离

- left_hand: `0.000000`
- right_hand: `0.000000`
- left_hand_shape: `0.000000`
- right_hand_shape: `0.000000`
- pose: `0.065807`
- face: `0.078460`
- missing: `0.000000`
- weighted: `0.000000`
- hand_side_swapped: `0.000000`

### 最差对齐点

- standard frame 0 vs query frame 0: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 0 vs query frame 4: weighted=0.000000, left=0.000000, right=0.000000, pose=0.054787, missing=0.000000
- standard frame 0 vs query frame 8: weighted=0.000000, left=0.000000, right=0.000000, pose=0.160658, missing=0.000000
- standard frame 0 vs query frame 12: weighted=0.000000, left=0.000000, right=0.000000, pose=0.121142, missing=0.000000
- standard frame 0 vs query frame 16: weighted=0.000000, left=0.000000, right=0.000000, pose=0.126856, missing=0.000000

## 判别性套件

- 正例最低分：`81.656`
- 负例最高分：`48.823`
- 分离 margin：`32.832`
- 门控是否通过：`True`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- trim_start_20pct [target_positive_variant]: score=`92.648`, dtw=`0.000000`, total_dist=`0.009164`, expected=high
- trim_both_10pct [target_positive_variant]: score=`89.074`, dtw=`0.001662`, total_dist=`0.013885`, expected=high
- subsample_even [target_positive_variant]: score=`88.591`, dtw=`0.007117`, total_dist=`0.014537`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`85.205`, dtw=`0.013380`, total_dist=`0.019213`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`84.634`, dtw=`0.013315`, total_dist=`0.020020`, expected=high
- trim_end_20pct [target_positive_variant]: score=`81.656`, dtw=`0.003208`, total_dist=`0.024319`, expected=high
- fake_shuffle_frames [synthetic_fake_action]: score=`48.823`, dtw=`0.009054`, total_dist=`0.086035`, expected=low
- other_demo_谗_羡慕 [other_demo_action]: score=`42.151`, dtw=`0.010981`, total_dist=`0.103669`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`33.032`, dtw=`0.009734`, total_dist=`0.132923`, expected=low
- other_demo_汽车 [other_demo_action]: score=`24.720`, dtw=`0.011034`, total_dist=`0.167705`, expected=low
- other_demo_月亮 [other_demo_action]: score=`21.882`, dtw=`0.017064`, total_dist=`0.182342`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`18.582`, dtw=`0.013708`, total_dist=`0.201958`, expected=low
- other_demo_朋友 [other_demo_action]: score=`18.286`, dtw=`0.120628`, total_dist=`0.203883`, expected=low
- other_demo_指示 [other_demo_action]: score=`18.162`, dtw=`0.151167`, total_dist=`0.204701`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`17.908`, dtw=`0.063022`, total_dist=`0.206389`, expected=low
- other_demo_跳 [other_demo_action]: score=`16.427`, dtw=`0.077607`, total_dist=`0.216748`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`16.296`, dtw=`0.153273`, total_dist=`0.217710`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`9.767`, dtw=`0.010642`, total_dist=`0.279136`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`7.844`, dtw=`0.013711`, total_dist=`0.305445`, expected=low
- other_demo_虎 [other_demo_action]: score=`7.281`, dtw=`0.080267`, total_dist=`0.314385`, expected=low

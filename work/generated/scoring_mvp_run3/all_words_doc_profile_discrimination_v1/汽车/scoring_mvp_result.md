# Holistic 序列打分 MVP 结果

## 口径说明

- 本结果是 prototype sanity check，不是已校准的真实用户评分。
- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。
- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。

## 输入

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/汽车/汽车_holistic_results.json`
- 查询序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/汽车/汽车_holistic_results.json`
- 特征模式：`landmark`

## 主对齐结果

- prototype_score：`100.000`
- dtw_distance：`0.000000`
- normalized_distance：`0.000000`
- DTW path length：`50`
- sequence_penalty：`0.000000`

### 分组平均距离

- left_hand: `0.000000`
- right_hand: `0.000000`
- left_hand_shape: `0.000000`
- right_hand_shape: `0.000000`
- pose: `0.009865`
- face: `0.005837`
- missing: `0.000000`
- weighted: `0.000000`
- hand_side_swapped: `0.000000`

### 最差对齐点

- standard frame 0 vs query frame 0: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 0 vs query frame 2: weighted=0.000000, left=0.000000, right=0.000000, pose=0.049538, missing=0.000000
- standard frame 2 vs query frame 2: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 4 vs query frame 4: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 6 vs query frame 6: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000

## 判别性套件

- 正例最低分：`36.120`
- 负例最高分：`32.110`
- 分离 margin：`4.010`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`86.688`, dtw=`0.000231`, total_dist=`0.017143`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`84.852`, dtw=`0.000266`, total_dist=`0.019712`, expected=high
- trim_both_10pct [target_positive_variant]: score=`62.767`, dtw=`0.002955`, total_dist=`0.055890`, expected=high
- subsample_even [target_positive_variant]: score=`61.750`, dtw=`0.019680`, total_dist=`0.057849`, expected=high
- trim_start_20pct [target_positive_variant]: score=`55.675`, dtw=`0.000514`, total_dist=`0.070278`, expected=high
- trim_end_20pct [target_positive_variant]: score=`36.120`, dtw=`0.000514`, total_dist=`0.122197`, expected=high
- other_demo_虎 [other_demo_action]: score=`32.110`, dtw=`0.044320`, total_dist=`0.136319`, expected=low
- other_demo_谗_羡慕 [other_demo_action]: score=`26.342`, dtw=`0.044436`, total_dist=`0.160081`, expected=low
- other_demo_指示 [other_demo_action]: score=`23.306`, dtw=`0.047929`, total_dist=`0.174773`, expected=low
- other_demo_朋友 [other_demo_action]: score=`21.914`, dtw=`0.047892`, total_dist=`0.182164`, expected=low
- other_demo_跳 [other_demo_action]: score=`20.287`, dtw=`0.047967`, total_dist=`0.191420`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`15.932`, dtw=`0.048659`, total_dist=`0.220421`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`15.242`, dtw=`0.051215`, total_dist=`0.225735`, expected=low
- other_demo_月亮 [other_demo_action]: score=`11.891`, dtw=`0.049729`, total_dist=`0.255528`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`9.891`, dtw=`0.157192`, total_dist=`0.277621`, expected=low
- other_demo_花 [other_demo_action]: score=`3.604`, dtw=`0.034418`, total_dist=`0.398782`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`2.963`, dtw=`0.043858`, total_dist=`0.422291`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`1.423`, dtw=`0.045541`, total_dist=`0.510273`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`0.391`, dtw=`0.088299`, total_dist=`0.665418`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.380`, dtw=`0.045550`, total_dist=`0.668615`, expected=low

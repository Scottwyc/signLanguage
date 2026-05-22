# Holistic 序列打分 MVP 结果

## 口径说明

- 本结果是 prototype sanity check，不是已校准的真实用户评分。
- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。
- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。

## 输入

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`
- 查询序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`
- 特征模式：`landmark`

## 主对齐结果

- prototype_score：`100.000`
- dtw_distance：`0.000000`
- normalized_distance：`0.000000`
- DTW path length：`39`
- sequence_penalty：`0.000000`

### 分组平均距离

- left_hand: `0.000000`
- right_hand: `0.000000`
- left_hand_shape: `0.000000`
- right_hand_shape: `0.000000`
- pose: `0.007337`
- face: `0.007189`
- missing: `0.000000`
- weighted: `0.000000`
- hand_side_swapped: `0.000000`

### 最差对齐点

- standard frame 22 vs query frame 22: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 22 vs query frame 24: weighted=0.000000, left=0.000000, right=0.000000, pose=0.182820, missing=0.000000
- standard frame 22 vs query frame 26: weighted=0.000000, left=0.000000, right=0.000000, pose=0.164688, missing=0.000000
- standard frame 24 vs query frame 26: weighted=0.000000, left=0.000000, right=0.000000, pose=0.105250, missing=0.000000
- standard frame 26 vs query frame 26: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000

## 判别性套件

- 正例最低分：`62.362`
- 负例最高分：`65.125`
- 分离 margin：`-2.763`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- trim_start_20pct [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- trim_both_10pct [target_positive_variant]: score=`96.838`, dtw=`0.000435`, total_dist=`0.003855`, expected=high
- subsample_even [target_positive_variant]: score=`85.223`, dtw=`0.009435`, total_dist=`0.019188`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`83.851`, dtw=`0.015305`, total_dist=`0.021135`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`81.125`, dtw=`0.015204`, total_dist=`0.025101`, expected=high
- fake_shuffle_frames [synthetic_fake_action]: score=`65.125`, dtw=`0.009596`, total_dist=`0.051463`, expected=low
- trim_end_20pct [target_positive_variant]: score=`62.362`, dtw=`0.006345`, total_dist=`0.056667`, expected=high
- other_demo_谗_羡慕 [other_demo_action]: score=`41.756`, dtw=`0.018203`, total_dist=`0.104800`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`35.696`, dtw=`0.009807`, total_dist=`0.123615`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`33.872`, dtw=`0.008683`, total_dist=`0.129908`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`29.401`, dtw=`0.019053`, total_dist=`0.146898`, expected=low
- other_demo_月亮 [other_demo_action]: score=`28.478`, dtw=`0.018871`, total_dist=`0.150723`, expected=low
- other_demo_指示 [other_demo_action]: score=`25.754`, dtw=`0.121899`, total_dist=`0.162789`, expected=low
- other_demo_跳 [other_demo_action]: score=`20.122`, dtw=`0.056993`, total_dist=`0.192404`, expected=low
- other_demo_朋友 [other_demo_action]: score=`18.626`, dtw=`0.124769`, total_dist=`0.201673`, expected=low
- other_demo_汽车 [other_demo_action]: score=`15.498`, dtw=`0.012505`, total_dist=`0.223738`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`14.247`, dtw=`0.017896`, total_dist=`0.233833`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`11.258`, dtw=`0.145871`, total_dist=`0.262091`, expected=low
- other_demo_虎 [other_demo_action]: score=`9.845`, dtw=`0.054088`, total_dist=`0.278179`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`8.714`, dtw=`0.017889`, total_dist=`0.292826`, expected=low

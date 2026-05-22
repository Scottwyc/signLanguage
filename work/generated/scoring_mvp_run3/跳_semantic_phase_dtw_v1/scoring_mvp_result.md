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
- base_weighted: `0.000000`
- semantic_phase_gap: `0.000000`
- semantic_phase_penalty: `0.000000`
- weighted: `0.000000`
- hand_side_swapped: `0.000000`

### 最差对齐点

- standard frame 12 vs query frame 12: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 14 vs query frame 14: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 16 vs query frame 16: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 18 vs query frame 18: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 20 vs query frame 20: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000

## 判别性套件

- 正例最低分：`79.579`
- 负例最高分：`39.639`
- 分离 margin：`39.940`
- 门控是否通过：`True`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`96.884`, dtw=`0.000321`, total_dist=`0.005810`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`96.055`, dtw=`0.000380`, total_dist=`0.007377`, expected=high
- trim_end_20pct [target_positive_variant]: score=`94.750`, dtw=`0.004624`, total_dist=`0.011326`, expected=high
- trim_both_10pct [target_positive_variant]: score=`94.729`, dtw=`0.004685`, total_dist=`0.011387`, expected=high
- trim_start_20pct [target_positive_variant]: score=`93.565`, dtw=`0.005236`, total_dist=`0.013806`, expected=high
- subsample_even [target_positive_variant]: score=`79.579`, dtw=`0.032691`, total_dist=`0.052557`, expected=high
- other_demo_花 [other_demo_action]: score=`39.639`, dtw=`0.086428`, total_dist=`0.166563`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`34.417`, dtw=`0.040869`, total_dist=`0.127996`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`15.236`, dtw=`0.121762`, total_dist=`0.338672`, expected=low
- other_demo_虎 [other_demo_action]: score=`13.954`, dtw=`0.200001`, total_dist=`0.354492`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`11.546`, dtw=`0.276701`, total_dist=`0.388587`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`10.865`, dtw=`0.079487`, total_dist=`0.399538`, expected=low
- other_demo_谗_羡慕 [other_demo_action]: score=`10.383`, dtw=`0.159916`, total_dist=`0.407695`, expected=low
- other_demo_月亮 [other_demo_action]: score=`8.213`, dtw=`0.321934`, total_dist=`0.449906`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`6.843`, dtw=`0.246833`, total_dist=`0.482739`, expected=low
- other_demo_指示 [other_demo_action]: score=`5.666`, dtw=`0.325201`, total_dist=`0.516722`, expected=low
- other_demo_汽车 [other_demo_action]: score=`3.895`, dtw=`0.479848`, total_dist=`0.584185`, expected=low
- other_demo_朋友 [other_demo_action]: score=`2.809`, dtw=`0.340587`, total_dist=`0.643050`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.034`, dtw=`0.657335`, total_dist=`1.438925`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`0.009`, dtw=`1.178428`, total_dist=`1.682590`, expected=low

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
- left_hand_motion: `0.000000`
- right_hand_motion: `0.000000`
- left_hand_shape_motion: `0.000000`
- right_hand_shape_motion: `0.000000`
- two_hand_relation: `0.000000`
- two_hand_relation_motion: `0.000000`
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

- 正例最低分：`22.145`
- 负例最高分：`20.943`
- 分离 margin：`1.202`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`96.149`, dtw=`0.004391`, total_dist=`0.008607`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`93.310`, dtw=`0.004442`, total_dist=`0.014019`, expected=high
- trim_end_20pct [target_positive_variant]: score=`92.482`, dtw=`0.004624`, total_dist=`0.015686`, expected=high
- trim_both_10pct [target_positive_variant]: score=`92.462`, dtw=`0.004685`, total_dist=`0.015747`, expected=high
- trim_start_20pct [target_positive_variant]: score=`91.633`, dtw=`0.005236`, total_dist=`0.017561`, expected=high
- subsample_even [target_positive_variant]: score=`22.145`, dtw=`0.197611`, total_dist=`0.271361`, expected=high
- other_demo_花 [other_demo_action]: score=`20.943`, dtw=`0.202017`, total_dist=`0.281409`, expected=low
- other_demo_虎 [other_demo_action]: score=`9.942`, dtw=`0.279518`, total_dist=`0.415512`, expected=low
- other_demo_谗_羡慕 [other_demo_action]: score=`8.295`, dtw=`0.227447`, total_dist=`0.448117`, expected=low
- fake_shuffle_frames [synthetic_fake_action]: score=`8.046`, dtw=`0.193785`, total_dist=`0.453604`, expected=low
- other_demo_香蕉 [other_demo_action]: score=`6.855`, dtw=`0.372289`, total_dist=`0.482434`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`6.213`, dtw=`0.306259`, total_dist=`0.500142`, expected=low
- other_demo_唱歌 [other_demo_action]: score=`5.594`, dtw=`0.324100`, total_dist=`0.519037`, expected=low
- other_demo_月亮 [other_demo_action]: score=`4.411`, dtw=`0.437633`, total_dist=`0.561792`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`4.083`, dtw=`0.286416`, total_dist=`0.383797`, expected=low
- other_demo_指示 [other_demo_action]: score=`3.194`, dtw=`0.451619`, total_dist=`0.619898`, expected=low
- other_demo_汽车 [other_demo_action]: score=`2.614`, dtw=`0.558813`, total_dist=`0.655997`, expected=low
- other_demo_朋友 [other_demo_action]: score=`1.089`, dtw=`0.552258`, total_dist=`0.813590`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`0.062`, dtw=`0.954156`, total_dist=`1.329983`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.048`, dtw=`0.748418`, total_dist=`1.376116`, expected=low

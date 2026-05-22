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
- DTW path length：`28`
- sequence_penalty：`0.000000`

### 分组平均距离

- left_hand: `0.000000`
- right_hand: `0.000000`
- pose: `0.000000`
- face: `0.000000`
- missing: `0.000000`
- weighted: `0.000000`

### 最差对齐点

- standard frame 0 vs query frame 0: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 4 vs query frame 4: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 8 vs query frame 8: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 12 vs query frame 12: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000
- standard frame 16 vs query frame 16: weighted=0.000000, left=0.000000, right=0.000000, pose=0.000000, missing=0.000000

## 伪用户 sanity check

- self: score=`100.000`, distance=`0.000000`, query_length=`28`
- subsample_even: score=`86.859`, distance=`0.014792`, query_length=`14`
- trim_start_20pct: score=`72.522`, distance=`0.033735`, query_length=`22`
- trim_end_20pct: score=`88.383`, distance=`0.012966`, query_length=`22`
- middle_60pct: score=`70.789`, distance=`0.036273`, query_length=`16`
- amplitude_0.85: score=`93.030`, distance=`0.007586`, query_length=`28`
- amplitude_1.15: score=`93.975`, distance=`0.006524`, query_length=`28`

## 判别性套件

- 正例最低分：`70.789`
- 负例最高分：`42.144`
- 分离 margin：`28.646`
- 门控是否通过：`False`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`93.975`, dtw=`0.000268`, total_dist=`0.006524`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`93.030`, dtw=`0.000312`, total_dist=`0.007586`, expected=high
- trim_end_20pct [target_positive_variant]: score=`88.383`, dtw=`0.007360`, total_dist=`0.012966`, expected=high
- subsample_even [target_positive_variant]: score=`86.859`, dtw=`0.013192`, total_dist=`0.014792`, expected=high
- trim_start_20pct [target_positive_variant]: score=`72.522`, dtw=`0.019658`, total_dist=`0.033735`, expected=high
- middle_60pct [target_positive_variant]: score=`70.789`, dtw=`0.027018`, total_dist=`0.036273`, expected=high
- fake_shuffle_frames [synthetic_fake_action]: score=`42.144`, dtw=`0.051555`, total_dist=`0.090729`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`41.130`, dtw=`0.093284`, total_dist=`0.093284`, expected=low
- other_demo_envy [other_demo_action]: score=`16.403`, dtw=`0.126882`, total_dist=`0.189810`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`14.427`, dtw=`0.043287`, total_dist=`0.203287`, expected=low
- other_demo_friend [other_demo_action]: score=`11.424`, dtw=`0.174096`, total_dist=`0.227792`, expected=low
- other_demo_jump [other_demo_action]: score=`10.306`, dtw=`0.116046`, total_dist=`0.238606`, expected=low
- other_demo_singing [other_demo_action]: score=`9.665`, dtw=`0.195746`, total_dist=`0.245346`, expected=low
- other_demo_car [other_demo_action]: score=`8.744`, dtw=`0.154270`, total_dist=`0.255868`, expected=low
- other_demo_zhishi [other_demo_action]: score=`8.479`, dtw=`0.200715`, total_dist=`0.259096`, expected=low
- other_demo_banana [other_demo_action]: score=`5.813`, dtw=`0.198028`, total_dist=`0.298738`, expected=low
- other_demo_moon [other_demo_action]: score=`4.552`, dtw=`0.208556`, total_dist=`0.324410`, expected=low
- other_demo_tiger [other_demo_action]: score=`1.780`, dtw=`0.285456`, total_dist=`0.422979`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.063`, dtw=`0.629568`, total_dist=`0.773783`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`0.011`, dtw=`0.895822`, total_dist=`0.959421`, expected=low

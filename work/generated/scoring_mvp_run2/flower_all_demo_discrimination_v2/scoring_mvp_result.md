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
- subsample_even: score=`88.403`, distance=`0.014792`, query_length=`14`
- trim_start_20pct: score=`75.494`, distance=`0.033735`, query_length=`22`
- trim_end_20pct: score=`89.758`, distance=`0.012966`, query_length=`22`
- trim_both_10pct: score=`88.129`, distance=`0.015165`, query_length=`22`
- amplitude_0.85: score=`93.874`, distance=`0.007586`, query_length=`28`
- amplitude_1.15: score=`94.708`, distance=`0.006524`, query_length=`28`

## 判别性套件

- 正例最低分：`75.494`
- 负例最高分：`41.495`
- 分离 margin：`33.999`
- 门控是否通过：`True`

- self [target_positive_variant]: score=`100.000`, dtw=`0.000000`, total_dist=`0.000000`, expected=high
- amplitude_1.15 [target_positive_variant]: score=`94.708`, dtw=`0.000268`, total_dist=`0.006524`, expected=high
- amplitude_0.85 [target_positive_variant]: score=`93.874`, dtw=`0.000312`, total_dist=`0.007586`, expected=high
- trim_end_20pct [target_positive_variant]: score=`89.758`, dtw=`0.007360`, total_dist=`0.012966`, expected=high
- subsample_even [target_positive_variant]: score=`88.403`, dtw=`0.013192`, total_dist=`0.014792`, expected=high
- trim_both_10pct [target_positive_variant]: score=`88.129`, dtw=`0.010058`, total_dist=`0.015165`, expected=high
- trim_start_20pct [target_positive_variant]: score=`75.494`, dtw=`0.019658`, total_dist=`0.033735`, expected=high
- fake_shuffle_frames [synthetic_fake_action]: score=`41.495`, dtw=`0.051555`, total_dist=`0.105552`, expected=low
- fake_reverse_time [synthetic_fake_action]: score=`33.240`, dtw=`0.093284`, total_dist=`0.132169`, expected=low
- other_demo_envy [other_demo_action]: score=`20.562`, dtw=`0.126882`, total_dist=`0.189810`, expected=low
- fake_static_hold [synthetic_fake_action]: score=`15.658`, dtw=`0.043287`, total_dist=`0.222506`, expected=low
- other_demo_friend [other_demo_action]: score=`14.983`, dtw=`0.174096`, total_dist=`0.227792`, expected=low
- other_demo_jump [other_demo_action]: score=`13.692`, dtw=`0.116046`, total_dist=`0.238606`, expected=low
- other_demo_singing [other_demo_action]: score=`12.944`, dtw=`0.195746`, total_dist=`0.245346`, expected=low
- other_demo_car [other_demo_action]: score=`11.857`, dtw=`0.154270`, total_dist=`0.255868`, expected=low
- other_demo_zhishi [other_demo_action]: score=`11.543`, dtw=`0.200715`, total_dist=`0.259096`, expected=low
- other_demo_banana [other_demo_action]: score=`8.295`, dtw=`0.198028`, total_dist=`0.298738`, expected=low
- other_demo_moon [other_demo_action]: score=`6.698`, dtw=`0.208556`, total_dist=`0.324410`, expected=low
- other_demo_tiger [other_demo_action]: score=`1.766`, dtw=`0.285456`, total_dist=`0.484360`, expected=low
- fake_random_landmarks [synthetic_fake_action]: score=`0.046`, dtw=`0.629568`, total_dist=`0.921948`, expected=low
- fake_random_walk [synthetic_fake_action]: score=`0.006`, dtw=`0.895822`, total_dist=`1.158704`, expected=low

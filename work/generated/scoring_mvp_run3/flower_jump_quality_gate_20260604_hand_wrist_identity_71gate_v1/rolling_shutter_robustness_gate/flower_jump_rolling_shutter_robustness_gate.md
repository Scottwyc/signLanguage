# 花/跳滚动快门时变斜切鲁棒性门

- 生成时间：`2026-06-04T15:22:23`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，逐帧合成 rolling-shutter-like line shear 后重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：轻微时变斜切和偶发快门行扭曲仍可正常评分；强 skew 只记录诊断边界。

- 5080 状态：worker=`ready`，pid=`811485`，reload_count=`27`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向 rolling-shutter | 诊断最低分 | 最弱诊断 rolling-shutter | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 81.782 | ramp_rolling_x_from_y_0.06 | 81.602 | strong_smooth_rolling_x_from_y_0.22_diagnostic | 70.000 |
| 跳 | PASS | 97.367 | local_hands_smooth_rolling_x_from_y_0.10 | 94.343 | strong_smooth_rolling_x_from_y_0.22_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | pattern | mode | amp | shear | 局部手 | 改动帧 | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---|---:|---|---|---:|---|---|---|
| strong_smooth_rolling_x_from_y_0.22_diagnostic | diagnostic | DIAG | 81.602 | diagnostic | smooth | x_from_y | 0.220 | -0.220-0.220 | no | 50 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 强 rolling-shutter skew 只记录诊断边界，不代表正常网页采集。 |
| strong_local_hands_rolling_x_from_y_0.22_diagnostic | diagnostic | DIAG | 81.602 | diagnostic | smooth | x_from_y | 0.220 | -0.220-0.220 | yes | 50 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 强局部手部斜切可能真实破坏手形语义，只作为诊断边界。 |
| strong_sparse_rolling_xy_combo_0.18_every_4f_diagnostic | diagnostic | DIAG | 97.819 | diagnostic | sparse | xy_combo | 0.180 | -0.180-0.180 | no | 13 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 少量帧强组合斜切不是正常轻微快门失真，只记录诊断分数。 |
| ramp_rolling_x_from_y_0.06 | positive | PASS | 81.782 | >= 70.0 | ramp | x_from_y | 0.060 | -0.060-0.060 | no | 52 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 斜切量随录制过程缓慢从反向过渡到正向，模拟用户或相机持续移动。 |
| local_hands_smooth_rolling_x_from_y_0.10 | positive | PASS | 81.920 | >= 70.0 | smooth | x_from_y | 0.100 | -0.100-0.100 | yes | 50 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 仅双手局部出现轻微时变斜切，模拟快速手部运动带来的局部 rolling-shutter 形变。 |
| smooth_rolling_x_from_y_0.08 | positive | PASS | 81.975 | >= 70.0 | smooth | x_from_y | 0.080 | -0.080-0.080 | no | 50 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 整帧逐行 x<-y 时变斜切 8%，模拟轻微 rolling-shutter skew。 |
| smooth_rolling_y_from_x_0.06 | positive | PASS | 82.055 | >= 70.0 | smooth | y_from_x | 0.060 | -0.060-0.060 | no | 50 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 整帧逐行 y<-x 时变斜切 6%，覆盖垂直方向滚动快门失真。 |
| smooth_rolling_xy_combo_0.055 | positive | PASS | 82.103 | >= 70.0 | smooth | xy_combo | 0.055 | -0.055-0.055 | no | 50 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | x/y 组合时变斜切，覆盖轻微斜向 rolling-shutter wobble。 |
| sparse_rolling_x_from_y_0.08_every_5f | positive | PASS | 98.726 | >= 70.0 | sparse | x_from_y | 0.080 | -0.080-0.080 | no | 10 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 少量帧出现轻微 rolling-shutter skew，模拟偶发快门行扭曲。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | none | x_from_y | 0.000 | 0.000-0.000 | no | 0 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | pattern | mode | amp | shear | 局部手 | 改动帧 | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---|---:|---|---|---:|---|---|---|
| strong_smooth_rolling_x_from_y_0.22_diagnostic | diagnostic | DIAG | 94.343 | diagnostic | smooth | x_from_y | 0.220 | -0.217-0.217 | no | 16 | score_valid:score_valid | action_window_net:used | 强 rolling-shutter skew 只记录诊断边界，不代表正常网页采集。 |
| strong_local_hands_rolling_x_from_y_0.22_diagnostic | diagnostic | DIAG | 94.343 | diagnostic | smooth | x_from_y | 0.220 | -0.217-0.217 | yes | 16 | score_valid:score_valid | action_window_net:used | 强局部手部斜切可能真实破坏手形语义，只作为诊断边界。 |
| strong_sparse_rolling_xy_combo_0.18_every_4f_diagnostic | diagnostic | DIAG | 97.662 | diagnostic | sparse | xy_combo | 0.180 | -0.180-0.180 | no | 4 | score_valid:score_valid | action_window_net:used | 少量帧强组合斜切不是正常轻微快门失真，只记录诊断分数。 |
| local_hands_smooth_rolling_x_from_y_0.10 | positive | PASS | 97.367 | >= 70.0 | smooth | x_from_y | 0.100 | -0.098-0.098 | yes | 16 | score_valid:score_valid | action_window_net:used | 仅双手局部出现轻微时变斜切，模拟快速手部运动带来的局部 rolling-shutter 形变。 |
| smooth_rolling_x_from_y_0.08 | positive | PASS | 97.886 | >= 70.0 | smooth | x_from_y | 0.080 | -0.079-0.079 | no | 16 | score_valid:score_valid | action_window_net:used | 整帧逐行 x<-y 时变斜切 8%，模拟轻微 rolling-shutter skew。 |
| smooth_rolling_y_from_x_0.06 | positive | PASS | 98.168 | >= 70.0 | smooth | y_from_x | 0.060 | -0.059-0.059 | no | 16 | score_valid:score_valid | action_window_net:used | 整帧逐行 y<-x 时变斜切 6%，覆盖垂直方向滚动快门失真。 |
| smooth_rolling_xy_combo_0.055 | positive | PASS | 98.703 | >= 70.0 | smooth | xy_combo | 0.055 | -0.054-0.054 | no | 16 | score_valid:score_valid | action_window_net:used | x/y 组合时变斜切，覆盖轻微斜向 rolling-shutter wobble。 |
| ramp_rolling_x_from_y_0.06 | positive | PASS | 99.212 | >= 70.0 | ramp | x_from_y | 0.060 | -0.060-0.060 | no | 18 | score_valid:score_valid | action_window_net:used | 斜切量随录制过程缓慢从反向过渡到正向，模拟用户或相机持续移动。 |
| sparse_rolling_x_from_y_0.08_every_5f | positive | PASS | 99.389 | >= 70.0 | sparse | x_from_y | 0.080 | -0.080-0.080 | no | 4 | score_valid:score_valid | action_window_net:used | 少量帧出现轻微 rolling-shutter skew，模拟偶发快门行扭曲。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | none | x_from_y | 0.000 | 0.000-0.000 | no | 0 | score_valid:score_valid | action_window_net:used | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

## 说明

- 该门补充的是时变 rolling-shutter-like skew，不替代已有静态 perspective/shear、camera-roll、global-framing-flicker 或 hand-center/scale flicker 门。
- 正向变体覆盖 5.5%-10% 的平滑、缓变、稀疏和局部手部斜切；强 18%-22% 斜切只观察诊断边界。
- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。

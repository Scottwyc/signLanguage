# 花/跳全局取景时序漂移鲁棒性门

- 生成时间：`2026-06-04T07:02:55`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，对整人 pose/face/双手逐帧做全局 pan/zoom 后重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：轻微自动取景漂移、电子防抖中心修正和用户前后晃动仍保持可评分；强 pan/zoom 跳点只记录诊断边界。

- 5080 状态：worker=`ready`，pid=`811485`，reload_count=`19`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向全局取景漂移 | 诊断最低分 | 最弱诊断全局取景漂移 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 81.919 | smooth_global_zoom_0.08 | 80.909 | strong_smooth_global_zoom_0.35_diagnostic | 70.000 |
| 跳 | PASS | 97.598 | sparse_global_zoom_0.06_every_6f | 76.830 | strong_smooth_global_pan_y_0.22_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | pattern | mode | amp | scale | dx | dy | 改动帧 | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---|---:|---|---|---|---:|---|---|---|
| strong_smooth_global_zoom_0.35_diagnostic | diagnostic | DIAG | 80.909 | diagnostic | smooth | zoom | 0.350 | 0.650-1.350 | 0.000-0.000 | 0.000-0.000 | 50 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 整人画面 0.65-1.35 倍平滑 zoom 属于强边界，只记录诊断分数。 |
| strong_smooth_global_pan_y_0.22_diagnostic | diagnostic | DIAG | 81.671 | diagnostic | smooth | pan_y | 0.220 | 1.000-1.000 | 0.000-0.000 | -0.220-0.220 | 50 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 整人画面平滑大幅纵向漂移 22% 属于强边界，只记录诊断分数。 |
| strong_sparse_global_zoom_pan_0.18_every_4f_diagnostic | diagnostic | DIAG | 95.668 | diagnostic | sparse | zoom_pan_diag | 0.180 | 0.820-1.180 | -0.099-0.099 | -0.063-0.063 | 13 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 少量帧大幅 zoom+pan 跳点不是正常轻微自动取景，只记录诊断分数。 |
| smooth_global_zoom_0.08 | positive | PASS | 81.919 | >= 70.0 | smooth | zoom | 0.080 | 0.920-1.080 | 0.000-0.000 | 0.000-0.000 | 50 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 整人画面随时间 0.92-1.08 倍平滑缩放，模拟用户前后轻微移动或自动取景 zoom。 |
| smooth_global_zoom_pan_diag_0.06 | positive | PASS | 81.995 | >= 70.0 | smooth | zoom_pan_diag | 0.060 | 0.940-1.060 | -0.033-0.033 | -0.021-0.021 | 50 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 整人画面同时有轻微缩放和对角漂移，模拟自动取景合成扰动。 |
| smooth_global_pan_y_0.06 | positive | PASS | 82.066 | >= 70.0 | smooth | pan_y | 0.060 | 1.000-1.000 | 0.000-0.000 | -0.060-0.060 | 50 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 整人画面随时间平滑纵向漂移 6%，模拟自动取景中心慢漂。 |
| smooth_global_pan_x_0.06 | positive | PASS | 82.070 | >= 70.0 | smooth | pan_x | 0.060 | 1.000-1.000 | -0.060-0.060 | 0.000-0.000 | 50 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 整人画面随时间平滑横向漂移 6%，模拟电子防抖或用户身体轻微平移。 |
| sparse_global_zoom_0.06_every_6f | positive | PASS | 98.033 | >= 70.0 | sparse | zoom | 0.060 | 0.940-1.060 | 0.000-0.000 | 0.000-0.000 | 9 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 少量帧整人画面出现 6% zoom 跳点，完整动作语义仍应可评分。 |
| sparse_global_pan_diag_0.05_every_5f | positive | PASS | 98.275 | >= 70.0 | sparse | pan_diag | 0.050 | 1.000-1.000 | -0.050-0.050 | -0.033-0.033 | 10 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 少量帧整人画面中心出现 5% 对角跳动，模拟防抖/裁剪中心短时修正。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | none | pan_x | 0.000 | 1.000-1.000 | 0.000-0.000 | 0.000-0.000 | 0 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | pattern | mode | amp | scale | dx | dy | 改动帧 | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---|---:|---|---|---|---:|---|---|---|
| strong_smooth_global_pan_y_0.22_diagnostic | diagnostic | DIAG | 76.830 | diagnostic | smooth | pan_y | 0.220 | 1.000-1.000 | 0.000-0.000 | -0.217-0.217 | 16 | score_valid:score_valid | action_window_net:used | 整人画面平滑大幅纵向漂移 22% 属于强边界，只记录诊断分数。 |
| strong_smooth_global_zoom_0.35_diagnostic | diagnostic | DIAG | 90.879 | diagnostic | smooth | zoom | 0.350 | 0.655-1.345 | 0.000-0.000 | 0.000-0.000 | 16 | semantic_mismatch:relation_motion_too_horizontal | action_window_net:relation_motion_too_horizontal | 整人画面 0.65-1.35 倍平滑 zoom 属于强边界，只记录诊断分数。 |
| strong_sparse_global_zoom_pan_0.18_every_4f_diagnostic | diagnostic | DIAG | 94.726 | diagnostic | sparse | zoom_pan_diag | 0.180 | 0.820-1.180 | -0.099-0.099 | -0.063-0.063 | 4 | score_valid:score_valid | action_window_net:used | 少量帧大幅 zoom+pan 跳点不是正常轻微自动取景，只记录诊断分数。 |
| sparse_global_zoom_0.06_every_6f | positive | PASS | 97.598 | >= 70.0 | sparse | zoom | 0.060 | 0.940-1.060 | 0.000-0.000 | 0.000-0.000 | 3 | score_valid:score_valid | action_window_net:used | 少量帧整人画面出现 6% zoom 跳点，完整动作语义仍应可评分。 |
| smooth_global_zoom_0.08 | positive | PASS | 97.911 | >= 70.0 | smooth | zoom | 0.080 | 0.921-1.079 | 0.000-0.000 | 0.000-0.000 | 16 | score_valid:score_valid | action_window_net:used | 整人画面随时间 0.92-1.08 倍平滑缩放，模拟用户前后轻微移动或自动取景 zoom。 |
| smooth_global_zoom_pan_diag_0.06 | positive | PASS | 98.320 | >= 70.0 | smooth | zoom_pan_diag | 0.060 | 0.941-1.059 | -0.032-0.032 | -0.021-0.021 | 16 | score_valid:score_valid | action_window_net:used | 整人画面同时有轻微缩放和对角漂移，模拟自动取景合成扰动。 |
| smooth_global_pan_y_0.06 | positive | PASS | 99.256 | >= 70.0 | smooth | pan_y | 0.060 | 1.000-1.000 | 0.000-0.000 | -0.059-0.059 | 16 | score_valid:score_valid | action_window_net:used | 整人画面随时间平滑纵向漂移 6%，模拟自动取景中心慢漂。 |
| smooth_global_pan_x_0.06 | positive | PASS | 99.272 | >= 70.0 | smooth | pan_x | 0.060 | 1.000-1.000 | -0.059-0.059 | 0.000-0.000 | 16 | score_valid:score_valid | action_window_net:used | 整人画面随时间平滑横向漂移 6%，模拟电子防抖或用户身体轻微平移。 |
| sparse_global_pan_diag_0.05_every_5f | positive | PASS | 99.565 | >= 70.0 | sparse | pan_diag | 0.050 | 1.000-1.000 | -0.050-0.050 | -0.033-0.033 | 4 | score_valid:score_valid | action_window_net:used | 少量帧整人画面中心出现 5% 对角跳动，模拟防抖/裁剪中心短时修正。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | none | pan_x | 0.000 | 1.000-1.000 | 0.000-0.000 | 0.000-0.000 | 0 | score_valid:score_valid | action_window_net:used | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

## 说明

- 该门补充的是整人画面级的时间漂移，不替代静态 framing、aspect-ratio、hand-center-flicker 或 hand-scale-flicker 门。
- 正向变体覆盖 5%-8% 的平滑/稀疏 pan/zoom，强 18%-35% pan/zoom 不是正常网页采集要求。
- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。

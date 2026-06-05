# 花/跳手部中心时序漂移鲁棒性门

- 生成时间：`2026-06-04T10:44:49`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，逐帧平移手部局部坐标后重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：轻微平滑 detector center wobble、少量帧级 hand-center flicker 仍保持可评分；强中心跳点只记录诊断边界。

- 5080 状态：worker=`ready`，pid=`811485`，reload_count=`23`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向中心漂移 | 诊断最低分 | 最弱诊断中心漂移 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 82.112 | both_hands_smooth_center_y_0.04 | 81.773 | both_hands_strong_smooth_center_y_0.18_diagnostic | 70.000 |
| 跳 | PASS | 98.551 | right_hand_smooth_center_y_0.03 | 77.083 | both_hands_strong_smooth_center_y_0.18_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 手 | pattern | mode | amp | dx | dy | 改动帧 | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---|---|---:|---|---|---:|---|---|---|
| both_hands_strong_smooth_center_y_0.18_diagnostic | diagnostic | DIAG | 81.773 | diagnostic | `["left_hand", "right_hand"]` | smooth | y | 0.180 | 0.000-0.000 | -0.180-0.180 | 50 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 双手检测中心平滑大幅漂移 18% 属于强边界，只记录诊断分数。 |
| right_hand_strong_sparse_center_diag_0.12_every_4f_diagnostic | diagnostic | DIAG | 96.117 | diagnostic | `["right_hand"]` | sparse | diag | 0.120 | -0.120-0.120 | -0.078-0.078 | 13 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 右手检测中心少量帧大幅跳点不是正常轻微 detector wobble，只记录诊断分数。 |
| left_hand_strong_sparse_center_diag_0.12_every_4f_diagnostic | diagnostic | DIAG | 100.000 | diagnostic | `["left_hand"]` | sparse | diag | 0.120 | -0.120-0.120 | -0.078-0.078 | 13 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 左手检测中心少量帧大幅跳点不是正常轻微 detector wobble，只记录诊断分数。 |
| both_hands_smooth_center_y_0.04 | positive | PASS | 82.112 | >= 70.0 | `["left_hand", "right_hand"]` | smooth | y | 0.040 | 0.000-0.000 | -0.040-0.040 | 50 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 双手检测中心随时间平滑纵向漂移 4%，整体手势仍应可评分。 |
| both_hands_smooth_center_x_0.04 | positive | PASS | 82.115 | >= 70.0 | `["left_hand", "right_hand"]` | smooth | x | 0.040 | -0.040-0.040 | 0.000-0.000 | 50 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 双手检测中心随时间平滑横向漂移 4%，模拟 detector crop center wobble。 |
| right_hand_smooth_center_y_0.03 | positive | PASS | 82.135 | >= 70.0 | `["right_hand"]` | smooth | y | 0.030 | 0.000-0.000 | -0.030-0.030 | 50 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 右手核心手检测中心平滑纵向漂移 3%，验证右手 motion/relation 对中心抖动的吸收。 |
| both_hands_sparse_center_diag_0.035_every_5f | positive | PASS | 98.573 | >= 70.0 | `["left_hand", "right_hand"]` | sparse | diag | 0.035 | -0.035-0.035 | -0.023-0.023 | 10 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 少量帧双手检测中心出现轻微对角跳点，模拟网页帧级 detector center flicker。 |
| right_hand_sparse_center_diag_0.025_every_5f | positive | PASS | 98.674 | >= 70.0 | `["right_hand"]` | sparse | diag | 0.025 | -0.025-0.025 | -0.016-0.016 | 10 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 少量帧右手检测中心轻微跳点，覆盖单手局部 detector flicker。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | `["left_hand", "right_hand"]` | none | x | 0.000 | 0.000-0.000 | 0.000-0.000 | 0 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |
| left_hand_smooth_center_y_0.03 | positive | PASS | 100.000 | >= 70.0 | `["left_hand"]` | smooth | y | 0.030 | 0.000-0.000 | -0.030-0.030 | 50 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 左手检测中心平滑纵向漂移 3%，覆盖跳的地面手和花的非核心手。 |
| left_hand_sparse_center_diag_0.025_every_5f | positive | PASS | 100.000 | >= 70.0 | `["left_hand"]` | sparse | diag | 0.025 | -0.025-0.025 | -0.016-0.016 | 10 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 少量帧左手检测中心轻微跳点，不应破坏完整动作评分。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 手 | pattern | mode | amp | dx | dy | 改动帧 | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---|---|---:|---|---|---:|---|---|---|
| both_hands_strong_smooth_center_y_0.18_diagnostic | diagnostic | DIAG | 77.083 | diagnostic | `["left_hand", "right_hand"]` | smooth | y | 0.180 | 0.000-0.000 | -0.177-0.177 | 16 | score_valid:score_valid | action_window_net:used | 双手检测中心平滑大幅漂移 18% 属于强边界，只记录诊断分数。 |
| left_hand_strong_sparse_center_diag_0.12_every_4f_diagnostic | diagnostic | DIAG | 77.348 | diagnostic | `["left_hand"]` | sparse | diag | 0.120 | -0.120-0.120 | -0.078-0.078 | 4 | score_valid:score_valid | action_window_net:used | 左手检测中心少量帧大幅跳点不是正常轻微 detector wobble，只记录诊断分数。 |
| right_hand_strong_sparse_center_diag_0.12_every_4f_diagnostic | diagnostic | DIAG | 94.155 | diagnostic | `["right_hand"]` | sparse | diag | 0.120 | -0.120-0.120 | -0.078-0.078 | 4 | score_valid:score_valid | action_window_net:used | 右手检测中心少量帧大幅跳点不是正常轻微 detector wobble，只记录诊断分数。 |
| right_hand_smooth_center_y_0.03 | positive | PASS | 98.551 | >= 70.0 | `["right_hand"]` | smooth | y | 0.030 | 0.000-0.000 | -0.030-0.030 | 16 | score_valid:score_valid | action_window_net:used | 右手核心手检测中心平滑纵向漂移 3%，验证右手 motion/relation 对中心抖动的吸收。 |
| left_hand_smooth_center_y_0.03 | positive | PASS | 98.646 | >= 70.0 | `["left_hand"]` | smooth | y | 0.030 | 0.000-0.000 | -0.030-0.030 | 16 | score_valid:score_valid | action_window_net:used | 左手检测中心平滑纵向漂移 3%，覆盖跳的地面手和花的非核心手。 |
| right_hand_sparse_center_diag_0.025_every_5f | positive | PASS | 99.408 | >= 70.0 | `["right_hand"]` | sparse | diag | 0.025 | -0.025-0.025 | -0.016-0.016 | 4 | score_valid:score_valid | action_window_net:used | 少量帧右手检测中心轻微跳点，覆盖单手局部 detector flicker。 |
| both_hands_smooth_center_y_0.04 | positive | PASS | 99.504 | >= 70.0 | `["left_hand", "right_hand"]` | smooth | y | 0.040 | 0.000-0.000 | -0.039-0.039 | 16 | score_valid:score_valid | action_window_net:used | 双手检测中心随时间平滑纵向漂移 4%，整体手势仍应可评分。 |
| both_hands_smooth_center_x_0.04 | positive | PASS | 99.517 | >= 70.0 | `["left_hand", "right_hand"]` | smooth | x | 0.040 | -0.039-0.039 | 0.000-0.000 | 16 | score_valid:score_valid | action_window_net:used | 双手检测中心随时间平滑横向漂移 4%，模拟 detector crop center wobble。 |
| both_hands_sparse_center_diag_0.035_every_5f | positive | PASS | 99.720 | >= 70.0 | `["left_hand", "right_hand"]` | sparse | diag | 0.035 | -0.035-0.035 | -0.023-0.023 | 4 | score_valid:score_valid | action_window_net:used | 少量帧双手检测中心出现轻微对角跳点，模拟网页帧级 detector center flicker。 |
| left_hand_sparse_center_diag_0.025_every_5f | positive | PASS | 99.721 | >= 70.0 | `["left_hand"]` | sparse | diag | 0.025 | -0.025-0.025 | -0.016-0.016 | 4 | score_valid:score_valid | action_window_net:used | 少量帧左手检测中心轻微跳点，不应破坏完整动作评分。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | `["left_hand", "right_hand"]` | none | x | 0.000 | 0.000-0.000 | 0.000-0.000 | 0 | score_valid:score_valid | action_window_net:used | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

## 说明

- 该门补充的是 hand detector 中心的时间漂移，不替代静态 pose shift、relation-geometry、landmark-noise 或 hand-scale-flicker 门。
- 正向变体只覆盖 2.5%-4% 的平滑或稀疏手中心漂移，强 12%-18% 漂移/跳点不是正常网页采集要求。
- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。

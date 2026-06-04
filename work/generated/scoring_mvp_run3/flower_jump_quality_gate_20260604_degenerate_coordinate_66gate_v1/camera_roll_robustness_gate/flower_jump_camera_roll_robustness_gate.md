# 花/跳摄像头整体倾斜鲁棒性门

- 生成时间：`2026-06-04T06:03:13`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，先剥离到基础骨架组，再做 image-plane roll 并重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：用户身体或摄像头整体倾斜时，`花/跳` 的相对手部语义仍保持可评分；35/45 度极端倾斜只记录诊断边界。

- 5080 状态：worker=`ready`，pid=`811485`，reload_count=`18`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向倾斜 | 诊断最低分 | 最弱诊断倾斜 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 81.180 | camera_roll_pos20deg | 80.849 | camera_roll_pos45deg_diagnostic | 75.000 |
| 跳 | PASS | 89.634 | camera_roll_neg20deg | 75.140 | camera_roll_neg45deg_diagnostic | 75.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 角度 | 分数 | 阈值 | alignment | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---:|---|---|---|---|---|
| camera_roll_pos45deg_diagnostic | diagnostic | DIAG | 45.0 | 80.849 | diagnostic | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 45 度极端倾斜只作为诊断，不代表正常采集。 |
| camera_roll_neg45deg_diagnostic | diagnostic | DIAG | -45.0 | 80.849 | diagnostic | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 负 45 度极端倾斜只作为诊断，不代表正常采集。 |
| camera_roll_pos35deg_diagnostic | diagnostic | DIAG | 35.0 | 80.979 | diagnostic | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 35 度整体倾斜已偏离正常网页取景，只记录诊断边界。 |
| camera_roll_neg35deg_diagnostic | diagnostic | DIAG | -35.0 | 80.979 | diagnostic | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 负 35 度整体倾斜已偏离正常网页取景，只记录诊断边界。 |
| camera_roll_pos20deg | positive | PASS | 20.0 | 81.180 | >= 75.0 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 明显顺时针倾斜 20 度，作为正向鲁棒边界。 |
| camera_roll_neg20deg | positive | PASS | -20.0 | 81.180 | >= 75.0 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 明显逆时针倾斜 20 度，作为正向鲁棒边界。 |
| camera_roll_pos15deg | positive | PASS | 15.0 | 81.249 | >= 75.0 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 较明显顺时针倾斜 15 度，仍应保持可评分。 |
| camera_roll_neg15deg | positive | PASS | -15.0 | 81.249 | >= 75.0 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 较明显逆时针倾斜 15 度，仍应保持可评分。 |
| camera_roll_pos10deg | positive | PASS | 10.0 | 81.318 | >= 75.0 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 摄像头或身体中等顺时针倾斜 10 度。 |
| camera_roll_neg10deg | positive | PASS | -10.0 | 81.318 | >= 75.0 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 摄像头或身体中等逆时针倾斜 10 度。 |
| camera_roll_neg5deg | positive | PASS | -5.0 | 81.387 | >= 75.0 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 摄像头或身体轻微逆时针倾斜 5 度。 |
| camera_roll_pos5deg | positive | PASS | 5.0 | 81.387 | >= 75.0 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 摄像头或身体轻微顺时针倾斜 5 度。 |
| self_recomputed | positive | PASS | 0.0 | 100.000 | >= 95.0 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 标准序列剥离基础组后重建派生特征，应保持近满分。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 角度 | 分数 | 阈值 | alignment | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---:|---|---|---|---|---|
| camera_roll_neg45deg_diagnostic | diagnostic | DIAG | -45.0 | 75.140 | diagnostic | semantic_action_window | score_valid | action_window_net | 负 45 度极端倾斜只作为诊断，不代表正常采集。 |
| camera_roll_pos45deg_diagnostic | diagnostic | DIAG | 45.0 | 76.586 | diagnostic | semantic_action_window | score_valid | full_sequence_local_relation_segment | 45 度极端倾斜只作为诊断，不代表正常采集。 |
| camera_roll_neg35deg_diagnostic | diagnostic | DIAG | -35.0 | 82.567 | diagnostic | semantic_action_window | score_valid | action_window_net | 负 35 度整体倾斜已偏离正常网页取景，只记录诊断边界。 |
| camera_roll_pos35deg_diagnostic | diagnostic | DIAG | 35.0 | 83.333 | diagnostic | semantic_action_window | score_valid | full_sequence_local_relation_segment | 35 度整体倾斜已偏离正常网页取景，只记录诊断边界。 |
| camera_roll_neg20deg | positive | PASS | -20.0 | 89.634 | >= 75.0 | semantic_action_window | score_valid | action_window_net | 明显逆时针倾斜 20 度，作为正向鲁棒边界。 |
| camera_roll_pos20deg | positive | PASS | 20.0 | 89.922 | >= 75.0 | semantic_action_window | score_valid | full_sequence_local_relation_segment | 明显顺时针倾斜 20 度，作为正向鲁棒边界。 |
| camera_roll_neg15deg | positive | PASS | -15.0 | 92.132 | >= 75.0 | semantic_action_window | score_valid | action_window_net | 较明显逆时针倾斜 15 度，仍应保持可评分。 |
| camera_roll_pos15deg | positive | PASS | 15.0 | 92.300 | >= 75.0 | semantic_action_window | score_valid | action_window_net | 较明显顺时针倾斜 15 度，仍应保持可评分。 |
| camera_roll_neg10deg | positive | PASS | -10.0 | 94.695 | >= 75.0 | semantic_action_window | score_valid | action_window_net | 摄像头或身体中等逆时针倾斜 10 度。 |
| camera_roll_pos10deg | positive | PASS | 10.0 | 94.773 | >= 75.0 | semantic_action_window | score_valid | action_window_net | 摄像头或身体中等顺时针倾斜 10 度。 |
| camera_roll_neg5deg | positive | PASS | -5.0 | 97.319 | >= 75.0 | semantic_action_window | score_valid | action_window_net | 摄像头或身体轻微逆时针倾斜 5 度。 |
| camera_roll_pos5deg | positive | PASS | 5.0 | 97.339 | >= 75.0 | semantic_action_window | score_valid | action_window_net | 摄像头或身体轻微顺时针倾斜 5 度。 |
| self_recomputed | positive | PASS | 0.0 | 100.000 | >= 95.0 | semantic_action_window | score_valid | action_window_net | 标准序列剥离基础组后重建派生特征，应保持近满分。 |

## 说明

- 正向变体覆盖 ±5/±10/±15/±20 度整体倾斜，验证真实派生特征重建后的得分稳定性。
- 35/45 度是极端取景诊断，不作为正常网页采集要求。
- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。

# 花/跳手部流帧级延迟鲁棒性门

- 生成时间：`2026-06-04T09:57:14`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，将双手坐标整体滞后/提前 1-2 帧或局部短暂滞后，然后重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：轻微模型/worker 手部流延迟仍可正常评分；4-5 帧明显对齐错误只记录诊断边界。

- 5080 状态：worker=`ready`，pid=`811485`，reload_count=`22`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向手部流延迟 | 诊断最低分 | 最弱诊断边界 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 97.237 | sparse_both_hands_delay_2f_every_5f | 97.406 | middle35_both_hands_delay_5f_diagnostic | 70.000 |
| 跳 | PASS | 76.036 | sparse_both_hands_delay_2f_every_5f | 76.890 | both_hands_advance_4f_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | shift | pattern | 改动帧 | 改动组 | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---:|---|---:|---:|---|---|---|
| middle35_both_hands_delay_5f_diagnostic | diagnostic | DIAG | 97.406 | diagnostic | 5 | middle_35pct | 19 | 38 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 核心中段 5 帧延迟可能破坏真实相位证据，只记录诊断分数。 |
| both_hands_delay_4f_diagnostic | diagnostic | DIAG | 97.824 | diagnostic | 4 | full | 52 | 104 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 全程 4 帧手部流滞后已接近明显对齐错误，只记录诊断边界。 |
| both_hands_advance_4f_diagnostic | diagnostic | DIAG | 98.283 | diagnostic | -4 | full | 52 | 104 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 全程 4 帧提前属于明显结果对齐错误，只记录诊断边界。 |
| sparse_both_hands_delay_2f_every_5f | positive | PASS | 97.237 | >= 70.0 | 2 | sparse_every_5f | 11 | 22 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 每 5 帧一次 2 帧手部流滞后，模拟偶发结果对齐抖动。 |
| middle35_both_hands_delay_2f | positive | PASS | 98.485 | >= 70.0 | 2 | middle_35pct | 19 | 38 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花手部流中段约 35% 出现 2 帧手部流滞后，模拟核心段短暂处理延迟。 |
| both_hands_delay_2f | positive | PASS | 99.023 | >= 70.0 | 2 | full | 52 | 104 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花手部流整体滞后 2 帧，验证语义 DTW 对小型检测延迟的吸收。 |
| both_hands_advance_2f | positive | PASS | 99.046 | >= 70.0 | -2 | full | 52 | 104 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花手部流整体提前 2 帧，仍应保留完整动作可评分性。 |
| both_hands_advance_1f | positive | PASS | 99.398 | >= 70.0 | -1 | full | 52 | 104 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花手部流整体提前 1 帧，模拟帧切片和结果对齐轻微偏移。 |
| both_hands_delay_1f | positive | PASS | 99.473 | >= 70.0 | 1 | full | 52 | 104 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花手部流整体滞后 1 帧，模拟模型/worker 手部流轻微延迟。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | 0 | full | 0 | 0 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | shift | pattern | 改动帧 | 改动组 | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---:|---|---:|---:|---|---|---|
| both_hands_advance_4f_diagnostic | diagnostic | DIAG | 76.890 | diagnostic | -4 | full | 18 | 36 | score_valid:score_valid | action_window_net:used | 全程 4 帧提前属于明显结果对齐错误，只记录诊断边界。 |
| middle35_both_hands_delay_5f_diagnostic | diagnostic | DIAG | 81.545 | diagnostic | 5 | middle_35pct | 7 | 14 | score_valid:score_valid | full_sequence_local_relation_segment:used | 核心中段 5 帧延迟可能破坏真实相位证据，只记录诊断分数。 |
| both_hands_delay_4f_diagnostic | diagnostic | DIAG | 95.937 | diagnostic | 4 | full | 18 | 36 | score_valid:score_valid | full_sequence_local_relation_segment:used | 全程 4 帧手部流滞后已接近明显对齐错误，只记录诊断边界。 |
| sparse_both_hands_delay_2f_every_5f | positive | PASS | 76.036 | >= 70.0 | 2 | sparse_every_5f | 4 | 8 | score_valid:score_valid | action_window_net:used | 每 5 帧一次 2 帧手部流滞后，模拟偶发结果对齐抖动。 |
| middle35_both_hands_delay_2f | positive | PASS | 78.545 | >= 70.0 | 2 | middle_35pct | 7 | 14 | score_valid:score_valid | full_sequence_local_relation_segment:used | 跳跃双手流中段约 35% 出现 2 帧手部流滞后，模拟核心段短暂处理延迟。 |
| both_hands_delay_1f | positive | PASS | 78.754 | >= 70.0 | 1 | full | 18 | 36 | score_valid:score_valid | action_window_net:used | 跳跃双手流整体滞后 1 帧，模拟模型/worker 手部流轻微延迟。 |
| both_hands_advance_2f | positive | PASS | 92.305 | >= 70.0 | -2 | full | 18 | 36 | score_valid:score_valid | action_window_net:used | 跳跃双手流整体提前 2 帧，仍应保留完整动作可评分性。 |
| both_hands_delay_2f | positive | PASS | 94.652 | >= 70.0 | 2 | full | 18 | 36 | score_valid:score_valid | full_sequence_local_relation_segment:used | 跳跃双手流整体滞后 2 帧，验证语义 DTW 对小型检测延迟的吸收。 |
| both_hands_advance_1f | positive | PASS | 99.934 | >= 70.0 | -1 | full | 18 | 36 | score_valid:score_valid | action_window_net:used | 跳跃双手流整体提前 1 帧，模拟帧切片和结果对齐轻微偏移。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | 0 | full | 0 | 0 | score_valid:score_valid | action_window_net:used | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

## 说明

- 该门补充的是手部结果流相对当前帧的轻微延迟/提前，不替代 inter-hand temporal desync、temporal-rate、temporal-order-jitter、stutter 或 interpolation 门。
- 正向变体保持双手同时偏移，避免把左右手相位差和单手语义变化混入本门；强延迟只观察诊断边界。
- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。

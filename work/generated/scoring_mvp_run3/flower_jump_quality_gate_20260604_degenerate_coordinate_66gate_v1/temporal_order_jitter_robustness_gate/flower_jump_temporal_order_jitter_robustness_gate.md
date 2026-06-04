# 花/跳时序顺序抖动鲁棒性门

- 生成时间：`2026-06-04T06:14:23`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，重排基础骨架帧后重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：轻微相邻帧交换、小范围局部错序仍可评分；块状倒序只作为诊断边界，硬拒绝仍由 phase-order 门覆盖。

- 5080 状态：worker=`ready`，pid=`811485`，reload_count=`18`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向抖动 | 诊断最低分 | 最弱诊断抖动 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 97.035 | adjacent_swap_every_6f | 97.068 | block_reverse_25pct_diagnostic | 70.000 |
| 跳 | PASS | 71.379 | adjacent_swap_every_6f | 45.000 | block_reverse_25pct_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 改动位置 | 最大位移 | 逆序数 | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---:|---:|---:|---|---|---|
| block_reverse_25pct_diagnostic | diagnostic | DIAG | 97.068 | diagnostic | 12 | 12 | 78 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 中段约 25% 块状倒序，phase-order 门负责硬拒绝；这里仅记录分数。 |
| block_reverse_15pct_diagnostic | diagnostic | DIAG | 98.284 | diagnostic | 8 | 7 | 28 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 中段约 15% 块状倒序，不作为正常网页采集要求，仅记录边界。 |
| center_triplet_120_diagnostic | diagnostic | DIAG | 99.275 | diagnostic | 3 | 2 | 2 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 核心三帧循环错序，作为比相邻交换更强的诊断边界。 |
| adjacent_swap_every_6f | positive | PASS | 97.035 | >= 70.0 | 18 | 1 | 9 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 更密集的轻微相邻帧交换，覆盖短浏览器采集中的局部到达顺序抖动。 |
| core_two_adjacent_swaps | positive | PASS | 97.505 | >= 70.0 | 4 | 1 | 2 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 核心动作附近两处相邻帧交换，仍应保留可评分的语义轨迹。 |
| adjacent_swap_every_8f | positive | PASS | 97.511 | >= 70.0 | 14 | 1 | 7 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 每约 8 帧出现一次相邻帧交换，整体动作顺序仍基本保留。 |
| center_triplet_102 | positive | PASS | 99.511 | >= 70.0 | 2 | 1 | 1 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 核心三帧中的前两帧局部错序，相当于单个 ±1 帧 jitter。 |
| single_center_adjacent_swap | positive | PASS | 99.560 | >= 70.0 | 2 | 1 | 1 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花核心序列中间相邻两帧交换，模拟一次上传/时间戳抖动。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | 0 | 0 | 0 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 标准序列剥离基础组后重建 motion/relation 特征，应保持近满分。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 改动位置 | 最大位移 | 逆序数 | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---:|---:|---:|---|---|---|
| block_reverse_25pct_diagnostic | diagnostic | DIAG | 45.000 | diagnostic | 4 | 4 | 10 | semantic_mismatch:phase_order_disorder | action_window_net:used | 中段约 25% 块状倒序，phase-order 门负责硬拒绝；这里仅记录分数。 |
| block_reverse_15pct_diagnostic | diagnostic | DIAG | 73.562 | diagnostic | 2 | 2 | 3 | score_valid:score_valid | action_window_net:used | 中段约 15% 块状倒序，不作为正常网页采集要求，仅记录边界。 |
| center_triplet_120_diagnostic | diagnostic | DIAG | 73.963 | diagnostic | 3 | 2 | 2 | score_valid:score_valid | action_window_net:used | 核心三帧循环错序，作为比相邻交换更强的诊断边界。 |
| adjacent_swap_every_6f | positive | PASS | 71.379 | >= 70.0 | 6 | 1 | 3 | score_valid:score_valid | action_window_net:used | 更密集的轻微相邻帧交换，覆盖短浏览器采集中的局部到达顺序抖动。 |
| single_center_adjacent_swap | positive | PASS | 73.032 | >= 70.0 | 2 | 1 | 1 | score_valid:score_valid | action_window_net:used | 弹跳核心序列中间相邻两帧交换，模拟一次上传/时间戳抖动。 |
| adjacent_swap_every_8f | positive | PASS | 74.527 | >= 70.0 | 4 | 1 | 2 | score_valid:score_valid | action_window_net:used | 每约 8 帧出现一次相邻帧交换，整体动作顺序仍基本保留。 |
| core_two_adjacent_swaps | positive | PASS | 82.302 | >= 70.0 | 4 | 1 | 2 | score_valid:score_valid | action_window_net:used | 核心动作附近两处相邻帧交换，仍应保留可评分的语义轨迹。 |
| center_triplet_102 | positive | PASS | 90.758 | >= 70.0 | 2 | 1 | 1 | score_valid:score_valid | action_window_net:used | 核心三帧中的前两帧局部错序，相当于单个 ±1 帧 jitter。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | 0 | 0 | 0 | score_valid:score_valid | action_window_net:used | 标准序列剥离基础组后重建 motion/relation 特征，应保持近满分。 |

## 说明

- 该门补充的是帧到达顺序的局部抖动，不替代 temporal-stutter、temporal-rate、inter-hand desync 或 phase-order 门。
- `跳` 的短序列对局部错序更敏感，因此正向阈值保留在工程 sanity gate 的 `70` 分。
- 块状倒序不是正常网页采集要求；本门只记录其诊断分，真实硬拒绝仍看 phase-order/semantic-mismatch。
- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。

# 花/跳手指身份抖动鲁棒性门

- 生成时间：`2026-06-04T14:50:09`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，交换相邻或非相邻 finger chain 的 landmark 身份后重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：相邻手指链标签混淆和少量帧级身份抖动仍保持可评分；非相邻或多链强交换只记录诊断边界。

- 5080 状态：worker=`ready`，pid=`811485`，reload_count=`27`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向指链抖动 | 诊断最低分 | 最弱诊断抖动 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 79.043 | right_index_middle_chain_swap | 77.035 | right_index_ring_diagnostic | 70.000 |
| 跳 | PASS | 71.892 | right_middle_ring_sparse_jitter | 81.108 | right_thumb_index_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 手 | pairs | pattern | 改动帧 | 改动可见点 | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---|---|---:|---:|---|---|---|
| right_index_ring_diagnostic | diagnostic | DIAG | 77.035 | diagnostic | right_hand | `[["index", "ring"]]` | all | 40 | 320 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 非相邻 index/ring 指链交换不是正常轻微混淆，仅记录边界。 |
| right_adjacent_wave_diagnostic | diagnostic | DIAG | 78.401 | diagnostic | right_hand | `[["index", "middle"], ["ring", "pinky"]]` | all | 40 | 640 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 两组相邻指链全程交换属于强边界，仅记录诊断分数。 |
| right_thumb_index_diagnostic | diagnostic | DIAG | 79.095 | diagnostic | right_hand | `[["thumb", "index"]]` | all | 40 | 320 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | thumb/index 交换会改变手形拓扑，仅记录诊断边界。 |
| right_index_middle_chain_swap | positive | PASS | 79.043 | >= 70.0 | right_hand | `[["index", "middle"]]` | all | 40 | 320 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花核心手 index/middle 相邻指链全程交换，模拟手小或重叠时的相邻手指身份混淆。 |
| right_middle_ring_chain_swap | positive | PASS | 80.385 | >= 70.0 | right_hand | `[["middle", "ring"]]` | all | 40 | 320 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花核心手 middle/ring 相邻指链全程交换，整体绽放手形仍应可评分。 |
| right_ring_pinky_chain_swap | positive | PASS | 80.660 | >= 70.0 | right_hand | `[["ring", "pinky"]]` | all | 40 | 320 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花核心手 ring/pinky 相邻指链交换，覆盖外侧手指标签混淆。 |
| right_index_middle_sparse_jitter | positive | PASS | 93.647 | >= 70.0 | right_hand | `[["index", "middle"]]` | sparse_every_6th | 7 | 56 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 少量帧 index/middle 指链身份抖动，属于可容忍的 detector 局部不稳定。 |
| right_index_middle_middle_25pct | positive | PASS | 96.087 | >= 70.0 | right_hand | `[["index", "middle"]]` | middle_25pct | 14 | 112 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 核心中段 25% index/middle 身份抖动，验证手形/DTW 对短时拓扑标签抖动的吸收。 |
| right_middle_ring_sparse_jitter | positive | PASS | 96.260 | >= 70.0 | right_hand | `[["middle", "ring"]]` | sparse_every_6th | 7 | 56 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 少量帧 middle/ring 指链身份抖动，绽放动态仍应保留。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | right_hand | `[]` | all | 40 | 0 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 手 | pairs | pattern | 改动帧 | 改动可见点 | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---|---|---:|---:|---|---|---|
| right_thumb_index_diagnostic | diagnostic | DIAG | 81.108 | diagnostic | right_hand | `[["thumb", "index"]]` | all | 17 | 136 | score_valid:score_valid | action_window_net:used | thumb/index 交换不是正常轻微相邻手指混淆，仅记录边界。 |
| right_index_ring_diagnostic | diagnostic | DIAG | 81.654 | diagnostic | right_hand | `[["index", "ring"]]` | all | 17 | 136 | score_valid:score_valid | action_window_net:used | 右手 index/ring 非相邻交换会改变两指小人拓扑，仅记录诊断边界。 |
| right_adjacent_wave_diagnostic | diagnostic | DIAG | 82.302 | diagnostic | right_hand | `[["index", "middle"], ["ring", "pinky"]]` | all | 17 | 272 | score_valid:score_valid | action_window_net:used | 两组相邻指链全程交换属于强边界，仅记录诊断分数。 |
| right_middle_ring_sparse_jitter | positive | PASS | 71.892 | >= 70.0 | right_hand | `[["middle", "ring"]]` | sparse_every_6th | 3 | 24 | score_valid:score_valid | action_window_net:used | 短序列中少量帧 middle/ring 身份抖动，作为 `跳` 的弱边界正向门。 |
| right_index_middle_middle_25pct | positive | PASS | 73.032 | >= 70.0 | right_hand | `[["index", "middle"]]` | middle_25pct | 4 | 32 | score_valid:score_valid | action_window_net:used | 核心中段 25% index/middle 身份抖动，local relation fallback 仍应可恢复。 |
| right_index_middle_sparse_jitter | positive | PASS | 76.211 | >= 70.0 | right_hand | `[["index", "middle"]]` | sparse_every_6th | 3 | 24 | score_valid:score_valid | action_window_net:used | 短序列中少量帧 index/middle 身份抖动，仍应保留可评分跳跃证据。 |
| right_middle_ring_chain_swap | positive | PASS | 81.785 | >= 70.0 | right_hand | `[["middle", "ring"]]` | all | 17 | 136 | score_valid:score_valid | action_window_net:used | 右手 middle/ring 相邻指链混淆仍应保留跳跃主关系。 |
| right_index_middle_chain_swap | positive | PASS | 82.302 | >= 70.0 | right_hand | `[["index", "middle"]]` | all | 17 | 136 | score_valid:score_valid | action_window_net:used | 右手两指小人的 index/middle 互换不应破坏两指语义。 |
| right_ring_pinky_chain_swap | positive | PASS | 84.372 | >= 70.0 | right_hand | `[["ring", "pinky"]]` | all | 17 | 136 | score_valid:score_valid | action_window_net:used | 右手非核心外侧相邻指链混淆应保持高分。 |
| left_index_middle_chain_swap | positive | PASS | 98.227 | >= 70.0 | left_hand | `[["index", "middle"]]` | all | 16 | 128 | score_valid:score_valid | action_window_net:used | 左手地面手形的 index/middle 标签互换不应破坏地面支撑语义。 |
| left_middle_ring_sparse_jitter | positive | PASS | 99.269 | >= 70.0 | left_hand | `[["middle", "ring"]]` | sparse_every_6th | 2 | 16 | score_valid:score_valid | action_window_net:used | 左手地面少量帧 middle/ring 身份抖动仍应保持高分。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | right_hand | `[]` | all | 17 | 0 | score_valid:score_valid | action_window_net:used | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

## 说明

- 该门补充的是 hand landmark 拓扑标签混淆，不替代 landmark-noise、fingertip-occlusion、hand-orientation 或 core-shape-amplitude 门。
- `跳` 的最低正向边界来自短序列中的少量 middle/ring 指链身份抖动，当前要求保留在 `70` 分以上。
- 非相邻和多链交换不是正常网页采集要求，只记录诊断分数。
- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。

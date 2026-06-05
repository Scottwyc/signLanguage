# 花/跳手间时序错位鲁棒性门

- 生成时间：`2026-06-04T17:21:36`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，将单只手的 landmark 序列相对其它骨架组前后错开，并重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：`花` 的核心手轻微动作窗口错位、`跳` 的左右手轻微相位差仍保持可评分；强错位只记录诊断边界。

- 5080 状态：worker=`ready`，pid=`811485`，reload_count=`29`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向错位 | 诊断最低分 | 最弱诊断错位 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 99.023 | right_hand_delay_2f | 97.824 | right_hand_delay_4f_diagnostic | 70.000 |
| 跳 | PASS | 75.688 | left_hand_advance_1f | 75.809 | left_hand_delay_4f_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 最大错位帧 | shifts | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---:|---|---|---|---|
| right_hand_delay_4f_diagnostic | diagnostic | DIAG | 97.824 | diagnostic | 4 | `{"right_hand": 4}` | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花核心手滞后 4 帧属于强边界，仅记录诊断分数。 |
| right_hand_advance_4f_diagnostic | diagnostic | DIAG | 98.283 | diagnostic | 4 | `{"right_hand": -4}` | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花核心手提前 4 帧属于强边界，仅记录诊断分数。 |
| right_hand_delay_2f | positive | PASS | 99.023 | >= 70.0 | 2 | `{"right_hand": 2}` | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花核心手滞后 2 帧，验证 DTW 对轻度相位偏移的吸收。 |
| right_hand_advance_2f | positive | PASS | 99.046 | >= 70.0 | 2 | `{"right_hand": -2}` | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花核心手提前 2 帧，仍应保持正常评分。 |
| right_hand_advance_1f | positive | PASS | 99.398 | >= 70.0 | 1 | `{"right_hand": -1}` | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花核心手提前 1 帧，模拟动作窗口轻微错位。 |
| right_hand_delay_1f | positive | PASS | 99.473 | >= 70.0 | 1 | `{"right_hand": 1}` | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花核心手滞后 1 帧，模拟轻微采样/检测延迟。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | 0 | `{}` | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 标准序列剥离基础组后重建 motion/relation 特征，应保持近满分。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 最大错位帧 | shifts | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---:|---|---|---|---|
| left_hand_delay_4f_diagnostic | diagnostic | DIAG | 75.809 | diagnostic | 4 | `{"left_hand": 4}` | score_valid:score_valid | action_window_net:used | 左手滞后 4 帧属于强边界，仅记录诊断分数。 |
| both_hands_opposite_2f_diagnostic | diagnostic | DIAG | 83.138 | diagnostic | 2 | `{"left_hand": -2, "right_hand": 2}` | score_valid:score_valid | action_window_net:used | 左右手相反方向各错 2 帧属于强边界，仅记录诊断分数。 |
| right_hand_delay_4f_diagnostic | diagnostic | DIAG | 83.138 | diagnostic | 4 | `{"right_hand": 4}` | score_valid:score_valid | action_window_net:used | 右手滞后 4 帧属于强边界，仅记录诊断分数。 |
| left_hand_advance_1f | positive | PASS | 75.688 | >= 70.0 | 1 | `{"left_hand": -1}` | score_valid:score_valid | full_sequence_local_relation_segment:used | 左手地面提前 1 帧，仍应保持跳跃关系可评分。 |
| left_hand_delay_2f | positive | PASS | 75.822 | >= 70.0 | 2 | `{"left_hand": 2}` | score_valid:score_valid | full_sequence_local_relation_segment:used | 左手地面滞后 2 帧，双手关系仍应能被局部段恢复。 |
| right_hand_delay_1f | positive | PASS | 75.988 | >= 70.0 | 1 | `{"right_hand": 1}` | score_valid:score_valid | full_sequence_local_relation_segment:used | 右手两指小人相对左手地面滞后 1 帧，双手关系仍应可评分。 |
| both_hands_opposite_1f | positive | PASS | 76.442 | >= 70.0 | 1 | `{"left_hand": -1, "right_hand": 1}` | score_valid:score_valid | action_window_net:used | 左右手相反方向各错 1 帧，覆盖两手采样相位差叠加。 |
| left_hand_advance_2f | positive | PASS | 76.910 | >= 70.0 | 2 | `{"left_hand": -2}` | score_valid:score_valid | action_window_net:used | 左手地面提前 2 帧，作为轻中度手间相位差正向门。 |
| right_hand_advance_1f | positive | PASS | 78.086 | >= 70.0 | 1 | `{"right_hand": -1}` | score_valid:score_valid | action_window_net:used | 右手两指小人相对左手地面提前 1 帧，双手关系仍应可评分。 |
| left_hand_delay_1f | positive | PASS | 78.086 | >= 70.0 | 1 | `{"left_hand": 1}` | score_valid:score_valid | action_window_net:used | 左手地面滞后 1 帧，验证关系 fallback 不因轻微支撑相位差失败。 |
| right_hand_advance_2f | positive | PASS | 80.145 | >= 70.0 | 2 | `{"right_hand": -2}` | score_valid:score_valid | action_window_net:used | 右手两指小人提前 2 帧，仍应保持正常/边界分。 |
| right_hand_delay_2f | positive | PASS | 81.400 | >= 70.0 | 2 | `{"right_hand": 2}` | score_valid:score_valid | action_window_net:used | 右手两指小人滞后 2 帧，模拟较明显但可接受的手间相位差。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | 0 | `{}` | score_valid:score_valid | action_window_net:used | 标准序列剥离基础组后重建 motion/relation 特征，应保持近满分。 |

## 说明

- 该门补充的是手间相位差，不替代整体 temporal-rate、frame stutter、action crop/repeat 或 two-hand relation geometry 门。
- `跳` 的轻度错位可以由语义 DTW 与 guarded local relation fallback 吸收，后续 scorer 改动不能破坏该能力。
- 强错位不作为正常网页采集要求，只记录当前诊断边界。
- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。

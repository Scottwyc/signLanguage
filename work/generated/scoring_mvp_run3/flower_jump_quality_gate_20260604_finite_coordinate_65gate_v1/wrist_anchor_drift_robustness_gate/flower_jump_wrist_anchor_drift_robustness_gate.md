# 花/跳手腕掌根锚点漂移鲁棒性门

- 生成时间：`2026-06-04T03:41:44`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，在 hand mask 仍有效的前提下偏移 wrist/MCP/palm anchors 坐标，模拟手腕/掌根局部追踪漂移；随后重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：单帧、稀疏和轻度短窗口根点漂移仍可正常评分；持续核心漂移只记录诊断边界。

- 5080 状态：worker=`ready`，pid=`811485`，reload_count=`15`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向漂移 | 诊断最低分 | 最弱诊断边界 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 97.283 | flower_middle20_right_mcp_anchor_xy_0.029 | 94.444 | flower_middle35_right_wrist_xy_0.145_diagnostic | 70.000 |
| 跳 | PASS | 76.497 | jump_middle20_right_person_mcp_anchor_y_0.020 | 84.692 | jump_middle35_right_person_palm_anchor_xy_0.090_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | groups | landmarks | pattern | drift_xy | 改动帧 | 改动点 | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---|---|---:|---:|---:|---|---|---|
| flower_middle35_right_wrist_xy_0.145_diagnostic | diagnostic | DIAG | 94.444 | diagnostic | ['right_hand'] | [0] | middle_35pct | 0.145 | 19 | 19 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 诊断记录：核心右手 wrist 较长窗口大幅漂移时的边界分。 |
| flower_middle35_right_palm_anchor_xy_0.090_diagnostic | diagnostic | DIAG | 94.787 | diagnostic | ['right_hand'] | [0, 1, 5, 9, 13, 17] | middle_35pct | 0.090 | 19 | 114 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 诊断记录：核心右手多个 palm anchors 较强漂移时的边界分。 |
| flower_middle20_right_mcp_anchor_xy_0.029 | positive | PASS | 97.283 | >= 70.0 | ['right_hand'] | [5, 9, 13, 17] | middle_20pct | 0.029 | 11 | 44 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花核心右手 MCP 根点在短核心窗口轻度偏移，手指末端仍保留。 |
| flower_middle20_right_palm_anchor_y_0.022 | positive | PASS | 97.444 | >= 70.0 | ['right_hand'] | [0, 1, 5, 9, 13, 17] | middle_20pct | 0.022 | 11 | 66 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花核心右手 palm anchors 短窗口同向轻漂移，验证根点坐标容错。 |
| flower_sparse_right_wrist_y_0.040_every_6f | positive | PASS | 97.651 | >= 70.0 | ['right_hand'] | [0] | sparse_every_6f | 0.040 | 8 | 8 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花核心右手 wrist 稀疏帧纵向跳动，模拟短时根点估计漂移。 |
| flower_single_right_wrist_xy_0.055 | positive | PASS | 99.778 | >= 70.0 | ['right_hand'] | [0] | single_mid | 0.055 | 1 | 1 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花核心右手 wrist 单帧漂移，但指尖和 MCP 仍可见。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | [] | [] | none | 0.000 | 0 | 0 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | groups | landmarks | pattern | drift_xy | 改动帧 | 改动点 | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---|---|---:|---:|---:|---|---|---|
| jump_middle35_right_person_palm_anchor_xy_0.090_diagnostic | diagnostic | DIAG | 84.692 | diagnostic | ['right_hand'] | [0, 1, 5, 9, 13, 17] | middle_35pct | 0.090 | 7 | 42 | score_valid:score_valid | action_window_net:used | 诊断记录：右手小人 palm anchors 较强漂移时的边界分。 |
| jump_middle35_left_ground_wrist_xy_0.150_diagnostic | diagnostic | DIAG | 93.338 | diagnostic | ['left_hand'] | [0] | middle_35pct | 0.150 | 6 | 6 | score_valid:score_valid | action_window_net:used | 诊断记录：左手地面 wrist 较长窗口大幅漂移时的边界分。 |
| jump_middle20_right_person_mcp_anchor_y_0.020 | positive | PASS | 76.497 | >= 70.0 | ['right_hand'] | [5, 9, 13, 17] | middle_20pct | 0.020 | 3 | 12 | score_valid:score_valid | action_window_net:used | 跳的右手两指小人 MCP 根点短窗口轻度漂移，食指/中指证据仍保留。 |
| jump_sparse_left_ground_wrist_xy_0.038_every_6f | positive | PASS | 97.490 | >= 70.0 | ['left_hand'] | [0] | sparse_every_6f | 0.038 | 3 | 3 | score_valid:score_valid | action_window_net:used | 跳的左手地面 wrist 稀疏漂移，模拟地面手根点追踪跳动。 |
| jump_single_right_person_wrist_y_0.055 | positive | PASS | 98.464 | >= 70.0 | ['right_hand'] | [0] | single_mid | 0.055 | 1 | 1 | score_valid:score_valid | action_window_net:used | 跳的右手两指小人 wrist 单帧漂移，核心手指动作仍可见。 |
| jump_middle20_left_ground_palm_anchor_x_0.020 | positive | PASS | 98.478 | >= 70.0 | ['left_hand'] | [0, 1, 5, 9, 13, 17] | middle_20pct | 0.020 | 3 | 18 | score_valid:score_valid | action_window_net:used | 跳的左手地面 palm anchors 短窗口轻度横向漂移，关系证据仍保留。 |
| jump_sparse_right_person_wrist_xy_0.038_every_6f | positive | PASS | 98.547 | >= 70.0 | ['right_hand'] | [0] | sparse_every_6f | 0.038 | 3 | 3 | score_valid:score_valid | action_window_net:used | 跳的右手小人 wrist 稀疏漂移，动作轨迹仍应可评分。 |
| jump_single_left_ground_wrist_y_0.055 | positive | PASS | 99.404 | >= 70.0 | ['left_hand'] | [0] | single_mid | 0.055 | 1 | 1 | score_valid:score_valid | action_window_net:used | 跳的左手地面 wrist 单帧漂移，右手小人和双手关系仍可见。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | [] | [] | none | 0.000 | 0 | 0 | score_valid:score_valid | action_window_net:used | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

## 说明

- 该门补充的是 wrist/MCP/palm anchors 坐标仍可见但短时偏移的情况，不替代 palm-anchor occlusion、hand-center flicker、hand-scale flicker 或 hand-overlap merge 门。
- 持续核心根点漂移可能改变真实语义，本轮只作为诊断边界；是否升级硬负例需要真实网页样本或人工标签。
- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。

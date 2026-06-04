# 花/跳手指链软置信鲁棒性门

- 生成时间：`2026-06-04T05:20:08`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，保留坐标和 landmark 身份，只降低选定 finger-chain 的 hand mask 权重，并重建 motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：覆盖网页摄像头中特定手指链可见但置信度 near-threshold 的软 mask 场景；严重低置信只记录诊断边界。

- 5080 状态：worker=`ready`，pid=`811485`，reload_count=`17`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向低置信 | 诊断最低分 | 最弱诊断边界 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 100.000 | flower_right_all_fingers_confidence_0p85_full | 100.000 | flower_right_all_fingers_confidence_0p51_middle35_diagnostic | 70.000 |
| 跳 | PASS | 99.987 | jump_left_ground_fingers_confidence_0p65_middle20 | 100.000 | jump_right_person_fingers_confidence_0p51_middle35_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | group | fingers | scale | pattern | 改动帧 | 衰减点 | L/R mask | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---|---:|---|---:|---:|---|---|---|---|
| flower_right_all_fingers_confidence_0p51_middle35_diagnostic | diagnostic | DIAG | 100.000 | diagnostic | right_hand | ['thumb', 'index', 'middle', 'ring', 'pinky'] | 0.510 | middle_35pct | 19 | 380 | 0.000/0.587 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 诊断记录：开花核心手所有手指链较长窗口接近有效阈值时的边界分。 |
| flower_right_all_fingers_confidence_0p85_full | positive | PASS | 100.000 | >= 70.0 | right_hand | ['thumb', 'index', 'middle', 'ring', 'pinky'] | 0.850 | full | 40 | 800 | 0.000/0.647 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花核心手所有手指链全程轻度低置信，但坐标完整。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | right_hand | [] | 1.000 | none | 0 | 0 | 0.000/0.755 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 标准序列剥离基础组后重建 motion/relation，应保持近满分。 |
| flower_right_all_fingers_confidence_0p65_middle20 | positive | PASS | 100.000 | >= 70.0 | right_hand | ['thumb', 'index', 'middle', 'ring', 'pinky'] | 0.650 | middle_20pct | 11 | 220 | 0.000/0.686 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花核心窗口所有手指链中度低置信，仍高于有效阈值。 |
| flower_right_outer_fingers_confidence_0p55_sparse | positive | PASS | 100.000 | >= 70.0 | right_hand | ['ring', 'pinky'] | 0.550 | sparse_every_5f | 7 | 56 | 0.000/0.732 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花 ring/pinky 指链稀疏帧 near-threshold 低置信，完整绽放证据仍应保留。 |
| flower_right_index_middle_confidence_0p55_single_mid | positive | PASS | 100.000 | >= 70.0 | right_hand | ['index', 'middle'] | 0.550 | single_mid | 1 | 8 | 0.000/0.751 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花 index/middle 指链单帧 near-threshold 低置信，模拟瞬时手指置信跳变。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | group | fingers | scale | pattern | 改动帧 | 衰减点 | L/R mask | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---|---:|---|---:|---:|---|---|---|---|
| jump_right_person_fingers_confidence_0p51_middle35_diagnostic | diagnostic | DIAG | 100.000 | diagnostic | right_hand | ['index', 'middle'] | 0.510 | middle_35pct | 7 | 56 | 0.842/0.826 | score_valid:score_valid | action_window_net:used | 诊断记录：右手两指小人较长窗口接近有效阈值时的边界分。 |
| jump_left_ground_fingers_confidence_0p65_middle20 | positive | PASS | 99.987 | >= 70.0 | left_hand | ['thumb', 'index', 'middle', 'ring', 'pinky'] | 0.650 | middle_20pct | 3 | 60 | 0.789/0.895 | score_valid:score_valid | action_window_net:used | 跳的左手地面手核心短窗口手指链中度低置信，右手小人和双手关系仍应稳定。 |
| jump_right_person_fingers_confidence_0p85_full | positive | PASS | 100.000 | >= 70.0 | right_hand | ['index', 'middle'] | 0.850 | full | 17 | 136 | 0.842/0.844 | score_valid:score_valid | action_window_net:used | 跳的右手两指小人 index/middle 全程轻度低置信，双手关系和坐标仍完整。 |
| jump_right_person_fingers_confidence_0p65_full | positive | PASS | 100.000 | >= 70.0 | right_hand | ['index', 'middle'] | 0.650 | full | 17 | 136 | 0.842/0.775 | score_valid:score_valid | action_window_net:used | 跳的右手两指小人全程中度低置信，仍高于关系/手形有效阈值。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | right_hand | [] | 1.000 | none | 0 | 0 | 0.842/0.895 | score_valid:score_valid | action_window_net:used | 标准序列剥离基础组后重建 motion/relation，应保持近满分。 |
| jump_right_person_fingers_confidence_0p55_sparse | positive | PASS | 100.000 | >= 70.0 | right_hand | ['index', 'middle'] | 0.550 | sparse_every_5f | 4 | 32 | 0.842/0.859 | score_valid:score_valid | action_window_net:used | 跳的右手两指小人稀疏帧 near-threshold 低置信，跳跃轨迹仍应保留。 |

## 说明

- 该门补充的是 finger-chain 级软置信衰减，不替代整手置信度衰减、missing/mask、fingertip/mid-joint occlusion 或 hand dropout burst 门。
- 正向变体只覆盖 mild/near-threshold 低置信；低于有效阈值的严重情况应由缺失/重采诊断处理。
- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。

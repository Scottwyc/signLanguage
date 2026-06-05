# 花/跳手指链时间平滑鲁棒性门

- 生成时间：`2026-06-04T15:25:34`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，只对选定 distal finger chains 做短窗口时间低通，wrist/MCP/palm anchors 保持当前帧，mask 和 landmark 身份不变；随后重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：轻度、稀疏或短窗口 finger-chain smoothing 仍可正常评分；持续强低通只记录诊断边界，因为它可能真实抹掉手形相位。

- 5080 状态：worker=`ready`，pid=`811485`，reload_count=`27`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向平滑 | 诊断最低分 | 最弱诊断边界 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 80.010 | flower_right_all_distal_3tap_strength_0p35_full | 55.790 | flower_right_all_distal_heavy5_strength_1p00_full_diagnostic | 70.000 |
| 跳 | PASS | 77.745 | jump_left_ground_distal_3tap_strength_0p35_full | 72.654 | jump_right_person_distal_heavy5_strength_0p85_middle35_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | group | landmarks | strength | pattern | 改动帧 | 改动点 | source均值 | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---|---:|---|---:|---:|---:|---|---|---|
| flower_right_all_distal_heavy5_strength_1p00_full_diagnostic | diagnostic | DIAG | 55.790 | diagnostic | right_hand | [2, 3, 4, 6, 7, 8, 10, 11, 12, 14, 15, 16, 18, 19, 20] | 1.000 | full | 39 | 585 | 4.750 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 诊断记录：开花核心手所有 distal finger chains 全程强低通时的边界分。 |
| flower_right_all_distal_3tap_strength_0p35_full | positive | PASS | 80.010 | >= 70.0 | right_hand | [2, 3, 4, 6, 7, 8, 10, 11, 12, 14, 15, 16, 18, 19, 20] | 0.350 | full | 39 | 585 | 2.900 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花核心手所有 distal finger chains 全程轻度 3 帧平滑，模拟 tracker 稳定化但保留开合轨迹。 |
| flower_right_all_distal_3tap_strength_0p50_middle20 | positive | PASS | 96.332 | >= 70.0 | right_hand | [2, 3, 4, 6, 7, 8, 10, 11, 12, 14, 15, 16, 18, 19, 20] | 0.500 | middle_20pct | 11 | 165 | 3.000 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花短核心窗口所有 distal finger chains 中度平滑，覆盖较明显但局部的 tracker smoothing。 |
| flower_right_outer_distal_3tap_strength_0p55_middle20 | positive | PASS | 97.065 | >= 70.0 | right_hand | [14, 15, 16, 18, 19, 20] | 0.550 | middle_20pct | 11 | 66 | 3.000 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花右手外侧 ring/pinky distal chains 短核心窗口平滑，完整开花证据仍应可评分。 |
| flower_right_all_distal_5tap_strength_0p45_sparse | positive | PASS | 98.334 | >= 70.0 | right_hand | [2, 3, 4, 6, 7, 8, 10, 11, 12, 14, 15, 16, 18, 19, 20] | 0.450 | sparse_every_5f | 7 | 105 | 5.000 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花核心手稀疏帧 5 帧平滑，模拟低 FPS 选帧处的局部 finger-chain 黏连。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | right_hand | [] | 0.000 | none | 0 | 0 | - | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | group | landmarks | strength | pattern | 改动帧 | 改动点 | source均值 | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---|---:|---|---:|---:|---:|---|---|---|
| jump_right_person_distal_heavy5_strength_0p85_middle35_diagnostic | diagnostic | DIAG | 72.654 | diagnostic | right_hand | [6, 7, 8, 10, 11, 12] | 0.850 | middle_35pct | 7 | 42 | 5.000 | score_valid:score_valid | action_window_net:used | 诊断记录：右手两指小人较长核心窗口强平滑时的边界分。 |
| jump_right_person_distal_heavy5_strength_1p00_full_diagnostic | diagnostic | DIAG | 80.029 | diagnostic | right_hand | [6, 7, 8, 10, 11, 12] | 1.000 | full | 17 | 102 | 4.647 | score_valid:score_valid | action_window_net:used | 诊断记录：右手两指小人全程强低通时的边界分。 |
| jump_left_ground_distal_3tap_strength_0p35_full | positive | PASS | 77.745 | >= 70.0 | left_hand | [2, 3, 4, 6, 7, 8, 10, 11, 12, 14, 15, 16, 18, 19, 20] | 0.350 | full | 15 | 225 | 2.625 | score_valid:score_valid | action_window_net:used | 跳的左手地面手 distal chains 全程轻度平滑，右手小人和关系语义仍应稳定。 |
| jump_right_person_distal_3tap_strength_0p35_full | positive | PASS | 94.767 | >= 70.0 | right_hand | [6, 7, 8, 10, 11, 12] | 0.350 | full | 17 | 102 | 2.882 | score_valid:score_valid | action_window_net:used | 跳的右手两指小人 distal chains 全程轻度 3 帧平滑，跳跃轨迹和双手关系仍完整。 |
| jump_right_person_distal_3tap_strength_0p50_middle20 | positive | PASS | 97.644 | >= 70.0 | right_hand | [6, 7, 8, 10, 11, 12] | 0.500 | middle_20pct | 3 | 18 | 3.000 | score_valid:score_valid | action_window_net:used | 跳的右手两指核心短窗口中度平滑，仍应保留弹跳语义。 |
| jump_right_person_distal_5tap_strength_0p45_sparse | positive | PASS | 97.983 | >= 70.0 | right_hand | [6, 7, 8, 10, 11, 12] | 0.450 | sparse_every_5f | 4 | 24 | 4.250 | score_valid:score_valid | action_window_net:used | 跳的右手两指小人稀疏帧 5 帧平滑，模拟 tracker 局部时间黏连。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | right_hand | [] | 0.000 | none | 0 | 0 | - | score_valid:score_valid | action_window_net:used | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

## 说明

- 该门补充的是同一手内部 distal finger-chain 坐标被时间平滑，不替代 motion-blur、finger-chain latency、confidence attenuation、occlusion、stutter 或 interpolation 门。
- 持续强平滑可能真实移除 `花` 的开合或 `跳` 的两指弹跳相位，本轮只作为诊断边界；是否升级硬负例需要真实网页样本或人工标签。
- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。

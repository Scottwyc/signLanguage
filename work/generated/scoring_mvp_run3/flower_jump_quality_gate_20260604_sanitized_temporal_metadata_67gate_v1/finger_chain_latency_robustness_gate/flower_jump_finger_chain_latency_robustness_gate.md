# 花/跳手指链帧级延迟鲁棒性门

- 生成时间：`2026-06-04T08:57:36`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，只把选定 distal finger chains 从前/后帧复制到当前帧，wrist/MCP/palm anchors 保持当前帧，模拟手指链相对掌根的短时延迟；随后重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：单帧、稀疏和短窗口 1-2 帧 finger-chain latency 仍可正常评分；持续强延迟只记录诊断边界。

- 5080 状态：worker=`ready`，pid=`811485`，reload_count=`21`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向延迟 | 诊断最低分 | 最弱诊断边界 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 94.483 | flower_right_all_distal_sparse_delay_2f_every_5f | 40.342 | flower_right_all_distal_advance_1f_diagnostic | 70.000 |
| 跳 | PASS | 71.202 | jump_right_person_distal_delay_2f | 74.355 | jump_right_person_distal_delay_4f_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | group | landmarks | shift | pattern | 改动帧 | 改动点 | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---|---:|---|---:|---:|---|---|---|
| flower_right_all_distal_advance_1f_diagnostic | diagnostic | DIAG | 40.342 | diagnostic | right_hand | [2, 3, 4, 6, 7, 8, 10, 11, 12, 14, 15, 16, 18, 19, 20] | -1 | full | 38 | 570 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 诊断记录：开花核心手所有 distal finger joints 全程提前 1 帧会改变开合相位。 |
| flower_right_all_distal_delay_4f_diagnostic | diagnostic | DIAG | 48.553 | diagnostic | right_hand | [2, 3, 4, 6, 7, 8, 10, 11, 12, 14, 15, 16, 18, 19, 20] | 4 | full | 35 | 525 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 诊断记录：开花核心手 finger chains 全程滞后 4 帧时的边界分。 |
| flower_right_all_distal_delay_1f_diagnostic | diagnostic | DIAG | 51.292 | diagnostic | right_hand | [2, 3, 4, 6, 7, 8, 10, 11, 12, 14, 15, 16, 18, 19, 20] | 1 | full | 38 | 570 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 诊断记录：开花核心手所有 distal finger joints 全程滞后 1 帧会改变开合相位。 |
| flower_right_all_distal_middle35_delay_3f_diagnostic | diagnostic | DIAG | 77.488 | diagnostic | right_hand | [2, 3, 4, 6, 7, 8, 10, 11, 12, 14, 15, 16, 18, 19, 20] | 3 | middle_35pct | 19 | 285 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 诊断记录：开花核心窗口较长 distal finger latency 的边界分。 |
| flower_right_all_distal_sparse_delay_2f_every_5f | positive | PASS | 94.483 | >= 70.0 | right_hand | [2, 3, 4, 6, 7, 8, 10, 11, 12, 14, 15, 16, 18, 19, 20] | 2 | sparse_every_5f | 7 | 105 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花核心手稀疏帧指尖链滞后 2 帧，完整开合证据仍应保留。 |
| flower_right_all_distal_middle20_delay_2f | positive | PASS | 95.100 | >= 70.0 | right_hand | [2, 3, 4, 6, 7, 8, 10, 11, 12, 14, 15, 16, 18, 19, 20] | 2 | middle_20pct | 11 | 165 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花核心手短窗口所有 distal finger chains 滞后 2 帧，作为强正向容错门。 |
| flower_right_outer_distal_middle20_delay_2f | positive | PASS | 95.476 | >= 70.0 | right_hand | [14, 15, 16, 18, 19, 20] | 2 | middle_20pct | 11 | 66 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花右手外侧 ring/pinky distal joints 在短核心窗口滞后，验证非中心指链延迟容错。 |
| flower_right_all_distal_single_mid_delay_2f | positive | PASS | 99.528 | >= 70.0 | right_hand | [2, 3, 4, 6, 7, 8, 10, 11, 12, 14, 15, 16, 18, 19, 20] | 2 | single_mid | 1 | 15 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花核心手单帧 distal finger chains 滞后 2 帧，模拟瞬时指尖追踪延迟。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | right_hand | [] | 0 | none | 0 | 0 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | group | landmarks | shift | pattern | 改动帧 | 改动点 | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---|---:|---|---:|---:|---|---|---|
| jump_right_person_distal_delay_4f_diagnostic | diagnostic | DIAG | 74.355 | diagnostic | right_hand | [6, 7, 8, 10, 11, 12] | 4 | full | 13 | 78 | score_valid:score_valid | action_window_net:used | 诊断记录：右手两指小人 distal joints 全程滞后 4 帧时的边界分。 |
| jump_right_person_distal_middle35_delay_3f_diagnostic | diagnostic | DIAG | 81.566 | diagnostic | right_hand | [6, 7, 8, 10, 11, 12] | 3 | middle_35pct | 7 | 42 | score_valid:score_valid | full_sequence_local_relation_segment:used | 诊断记录：右手两指小人核心窗口较长 finger-chain latency 的边界分。 |
| jump_right_person_distal_delay_2f | positive | PASS | 71.202 | >= 70.0 | right_hand | [6, 7, 8, 10, 11, 12] | 2 | full | 15 | 90 | score_valid:score_valid | full_sequence_local_relation_segment:used | 跳的右手两指小人 distal joints 滞后 2 帧，模拟较明显但仍可接受的 finger-chain latency。 |
| jump_right_person_distal_sparse_delay_2f_every_5f | positive | PASS | 72.545 | >= 70.0 | right_hand | [6, 7, 8, 10, 11, 12] | 2 | sparse_every_5f | 3 | 18 | score_valid:score_valid | action_window_net:used | 跳的右手小人稀疏帧 distal finger latency，跳跃轨迹仍应保持。 |
| jump_right_person_distal_delay_1f | positive | PASS | 73.359 | >= 70.0 | right_hand | [6, 7, 8, 10, 11, 12] | 1 | full | 16 | 96 | score_valid:score_valid | full_sequence_local_relation_segment:used | 跳的右手两指小人 distal joints 相对掌根滞后 1 帧，双手关系和两指手形仍应可评分。 |
| jump_right_person_distal_middle20_delay_2f | positive | PASS | 73.367 | >= 70.0 | right_hand | [6, 7, 8, 10, 11, 12] | 2 | middle_20pct | 3 | 18 | score_valid:score_valid | action_window_net:used | 跳的右手两指核心短窗口滞后 2 帧，验证局部段关系恢复。 |
| jump_left_ground_distal_delay_1f | positive | PASS | 74.682 | >= 70.0 | left_hand | [2, 3, 4, 6, 7, 8, 10, 11, 12, 14, 15, 16, 18, 19, 20] | 1 | full | 13 | 195 | score_valid:score_valid | action_window_net:used | 跳的左手地面 distal joints 滞后 1 帧，地面手语义仍应稳定。 |
| jump_right_person_distal_advance_1f | positive | PASS | 77.613 | >= 70.0 | right_hand | [6, 7, 8, 10, 11, 12] | -1 | full | 16 | 96 | score_valid:score_valid | action_window_net:used | 跳的右手两指小人 distal joints 提前 1 帧，覆盖相反对齐误差。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | right_hand | [] | 0 | none | 0 | 0 | score_valid:score_valid | action_window_net:used | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

## 说明

- 该门补充的是同一手内部 finger chains 与 palm anchors 的帧级不同步，不替代 hand-stream latency、inter-hand temporal desync、trajectory interpolation、motion blur 或 finger identity jitter 门。
- 持续核心 finger-chain latency 可能改变真实语义，本轮只作为诊断边界；是否升级硬负例需要真实网页样本或人工标签。
- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。

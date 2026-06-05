# 花/跳手部重叠融合鲁棒性门

- 生成时间：`2026-06-04T13:08:01`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，将一只手的 landmarks 按比例拉向另一只手，模拟双手重叠/遮挡时的局部 merge；随后重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：单帧、稀疏和轻度短窗口融合仍可正常评分；持续核心手融合只记录诊断边界。

- 5080 状态：worker=`ready`，pid=`811485`，reload_count=`25`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向融合 | 诊断最低分 | 最弱诊断边界 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 81.343 | flower_right_hand_self_overlap_0.12 | 95.607 | flower_middle35_right_self_overlap_0.45_diagnostic | 70.000 |
| 跳 | PASS | 70.469 | single_mid_right_blend_toward_left_0.45 | 81.566 | jump_middle35_right_person_blend_left_0.55_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | source->target | pattern | alpha | 改动帧 | 改动点 | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---|---:|---:|---:|---|---|---|
| flower_middle35_right_self_overlap_0.45_diagnostic | diagnostic | DIAG | 95.607 | diagnostic | self_center->right_hand | middle_35pct | 0.450 | 19 | 399 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 诊断记录：开花核心手较强自遮挡融合时的边界分。 |
| flower_middle35_right_core_blend_left_0.60_diagnostic | diagnostic | DIAG | 100.000 | diagnostic | left_hand->right_hand | middle_35pct | 0.600 | 0 | 0 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 诊断记录：开花核心手中段向非核心手融合时的边界分。 |
| flower_right_hand_self_overlap_0.12 | positive | PASS | 81.343 | >= 70.0 | self_center->right_hand | full | 0.120 | 40 | 840 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 花的开花手 landmarks 轻微向掌心融合，模拟单手自遮挡/手指重叠但开花语义仍清晰。 |
| flower_middle20_right_self_overlap_0.20 | positive | PASS | 97.574 | >= 70.0 | self_center->right_hand | middle_20pct | 0.200 | 11 | 231 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 花的开花手中段轻度向掌心融合，验证核心片段轻微自遮挡仍可评分。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | left_hand->right_hand | none | 0.000 | 0 | 0 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |
| single_mid_left_blend_toward_right_0.45 | positive | PASS | 100.000 | >= 70.0 | right_hand->left_hand | single_mid | 0.450 | 0 | 0 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 单帧左手 landmark 被右手局部吸引，模拟双手短暂重叠。 |
| single_mid_right_blend_toward_left_0.45 | positive | PASS | 100.000 | >= 70.0 | left_hand->right_hand | single_mid | 0.450 | 0 | 0 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 单帧右手 landmark 被左手局部吸引，模拟双手短暂重叠。 |
| sparse_left_blend_toward_right_0.35_every_6f | positive | PASS | 100.000 | >= 70.0 | right_hand->left_hand | sparse_every_6f | 0.350 | 0 | 0 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 稀疏帧左手向右手融合，完整动作证据仍应可评分。 |
| sparse_right_blend_toward_left_0.35_every_6f | positive | PASS | 100.000 | >= 70.0 | left_hand->right_hand | sparse_every_6f | 0.350 | 0 | 0 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 稀疏帧右手向左手融合，完整动作证据仍应可评分。 |
| flower_middle20_left_noncore_blend_right_0.55 | positive | PASS | 100.000 | >= 70.0 | right_hand->left_hand | middle_20pct | 0.550 | 0 | 0 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 花的非核心左手中段向开花手融合，不应拖低右手核心开花语义。 |
| flower_full_left_noncore_blend_right_0.45 | positive | PASS | 100.000 | >= 65.0 | right_hand->left_hand | full | 0.450 | 0 | 0 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 花的非核心左手全程轻度向开花手融合，按非核心手干扰局部门槛处理。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | source->target | pattern | alpha | 改动帧 | 改动点 | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---|---:|---:|---:|---|---|---|
| jump_middle35_right_person_blend_left_0.55_diagnostic | diagnostic | DIAG | 81.566 | diagnostic | left_hand->right_hand | middle_35pct | 0.550 | 6 | 126 | score_valid:score_valid | full_sequence_local_relation_segment:used | 诊断记录：右手小人较长核心段向左手融合时的边界分。 |
| jump_middle35_left_ground_blend_right_0.55_diagnostic | diagnostic | DIAG | 83.288 | diagnostic | right_hand->left_hand | middle_35pct | 0.550 | 6 | 126 | score_valid:score_valid | full_sequence_local_relation_segment:used | 诊断记录：左手地面较长核心段向右手融合时的边界分。 |
| jump_right_person_self_overlap_0.30_diagnostic | diagnostic | DIAG | 97.709 | diagnostic | self_center->right_hand | middle_35pct | 0.300 | 7 | 147 | score_valid:score_valid | action_window_net:used | 诊断记录：右手两指小人较强自遮挡融合时的边界分。 |
| single_mid_right_blend_toward_left_0.45 | positive | PASS | 70.469 | >= 70.0 | left_hand->right_hand | single_mid | 0.450 | 1 | 21 | score_valid:score_valid | action_window_net:used | 单帧右手 landmark 被左手局部吸引，模拟双手短暂重叠。 |
| sparse_right_blend_toward_left_0.35_every_6f | positive | PASS | 72.107 | >= 70.0 | left_hand->right_hand | sparse_every_6f | 0.350 | 3 | 63 | score_valid:score_valid | action_window_net:used | 稀疏帧右手向左手融合，完整动作证据仍应可评分。 |
| jump_middle20_left_ground_blend_right_0.25 | positive | PASS | 74.210 | >= 70.0 | right_hand->left_hand | middle_20pct | 0.250 | 3 | 63 | score_valid:score_valid | action_window_net:used | 跳的左手地面在短核心窗口内轻微向右手融合，双手关系仍应保留。 |
| jump_middle20_right_person_blend_left_0.25 | positive | PASS | 74.432 | >= 70.0 | left_hand->right_hand | middle_20pct | 0.250 | 3 | 63 | score_valid:score_valid | action_window_net:used | 跳的右手小人在短核心窗口内轻微向左手融合，双手关系仍应保留。 |
| single_mid_left_blend_toward_right_0.45 | positive | PASS | 74.769 | >= 70.0 | right_hand->left_hand | single_mid | 0.450 | 1 | 21 | score_valid:score_valid | action_window_net:used | 单帧左手 landmark 被右手局部吸引，模拟双手短暂重叠。 |
| sparse_left_blend_toward_right_0.35_every_6f | positive | PASS | 75.067 | >= 70.0 | right_hand->left_hand | sparse_every_6f | 0.350 | 3 | 63 | score_valid:score_valid | action_window_net:used | 稀疏帧左手向右手融合，完整动作证据仍应可评分。 |
| jump_right_person_self_overlap_0.08 | positive | PASS | 99.109 | >= 70.0 | self_center->right_hand | full | 0.080 | 17 | 357 | score_valid:score_valid | action_window_net:used | 跳的右手两指小人轻微自遮挡融合，手形仍应保持可识别。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | left_hand->right_hand | none | 0.000 | 0 | 0 | score_valid:score_valid | action_window_net:used | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

## 说明

- 该门补充的是双手接近/遮挡时的局部 landmark 融合，不替代 ghost-hand duplicate、hand-label-flicker、relation-geometry 或 inter-hand temporal desync 门。
- 持续核心融合可能改变真实语义，本轮只作为诊断边界；是否升级硬负例需要真实网页样本或人工标签。
- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。

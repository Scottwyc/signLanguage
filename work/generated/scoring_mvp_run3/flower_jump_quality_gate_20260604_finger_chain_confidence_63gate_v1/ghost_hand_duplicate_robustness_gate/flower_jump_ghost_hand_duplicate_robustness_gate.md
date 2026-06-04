# 花/跳幽灵手重复鲁棒性门

- 生成时间：`2026-06-04T01:30:37`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，将一只手的 21 点复制到另一只手，模拟单手被检测成双手的幽灵手；随后重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：短暂或稀疏幽灵手不应破坏正常分数；`花` 的非核心左手幽灵副本不应拖低开花手核心语义；持续核心重复只记录诊断边界。

- 5080 状态：worker=`ready`，pid=`811485`，reload_count=`15`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向幽灵手 | 诊断最低分 | 最弱诊断边界 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 69.388 | flower_full_left_ghost_from_right_offset | 29.506 | flower_middle45_right_core_ghost_from_left_diagnostic | 70.000 |
| 跳 | PASS | 70.469 | single_mid_left_duplicates_right | 19.222 | jump_full_right_ghost_from_left_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | source->target | pattern | 改动帧 | 改动点 | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---|---:|---:|---|---|---|
| flower_middle45_right_core_ghost_from_left_diagnostic | diagnostic | DIAG | 29.506 | diagnostic | left_hand->right_hand | middle_45pct | 23 | 0 | needs_recapture:flower_core_hand_presence_low | short_visible_core:query_not_short_core_capture | 诊断记录：开花核心手被非核心手副本替代时的边界分。 |
| flower_full_left_ghost_from_right_offset | positive | PASS | 69.388 | >= 65.0 | right_hand->left_hand | full | 53 | 840 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 花的非核心左手全程成为右手开花手的幽灵副本，不应拖低清晰开花语义。 |
| flower_middle30_left_ghost_from_right | positive | PASS | 72.838 | >= 70.0 | right_hand->left_hand | middle_30pct | 15 | 315 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 花的非核心左手核心中段被右手副本替代，应仍由开花手主语义评分。 |
| sparse_right_duplicates_left_every_6f | positive | PASS | 95.573 | >= 70.0 | left_hand->right_hand | sparse_every_6f | 9 | 0 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 稀疏帧右手变成左手幽灵副本，完整动作证据仍应可评分。 |
| single_mid_right_duplicates_left | positive | PASS | 99.040 | >= 70.0 | left_hand->right_hand | single_mid | 1 | 0 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 单帧右手被左手幽灵副本替代，模拟偶发双手检测误报。 |
| sparse_left_duplicates_right_every_6f | positive | PASS | 99.608 | >= 70.0 | right_hand->left_hand | sparse_every_6f | 9 | 168 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 稀疏帧左手变成右手幽灵副本，完整动作证据仍应可评分。 |
| single_mid_left_duplicates_right | positive | PASS | 99.945 | >= 70.0 | right_hand->left_hand | single_mid | 1 | 21 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 单帧左手被右手幽灵副本替代，模拟偶发双手检测误报。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | left_hand->right_hand | none | 0 | 0 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | source->target | pattern | 改动帧 | 改动点 | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---|---:|---:|---|---|---|
| jump_full_right_ghost_from_left_diagnostic | diagnostic | DIAG | 19.222 | diagnostic | left_hand->right_hand | full | 19 | 336 | semantic_mismatch:relation_direction_mismatch | action_window_net:relation_direction_mismatch | 全程右手是左手幽灵副本，属于明显双手关系失真，只记录诊断边界。 |
| jump_full_left_ghost_from_right_diagnostic | diagnostic | DIAG | 27.929 | diagnostic | right_hand->left_hand | full | 19 | 357 | semantic_mismatch:relation_direction_mismatch | action_window_net:relation_direction_mismatch | 全程左手是右手幽灵副本，属于明显双手关系失真，只记录诊断边界。 |
| jump_middle30_right_ghost_from_left_diagnostic | diagnostic | DIAG | 81.566 | diagnostic | left_hand->right_hand | middle_30pct | 5 | 105 | score_valid:score_valid | full_sequence_local_relation_segment:used | 诊断记录：右手小人核心段被左手地面副本替代时的边界分。 |
| jump_middle30_left_ghost_from_right_diagnostic | diagnostic | DIAG | 84.587 | diagnostic | right_hand->left_hand | middle_30pct | 5 | 105 | score_valid:score_valid | full_sequence_local_relation_segment:used | 诊断记录：左手地面核心段被右手小人副本替代时的边界分。 |
| single_mid_left_duplicates_right | positive | PASS | 70.469 | >= 70.0 | right_hand->left_hand | single_mid | 1 | 21 | score_valid:score_valid | action_window_net:used | 单帧左手被右手幽灵副本替代，模拟偶发双手检测误报。 |
| single_mid_right_duplicates_left | positive | PASS | 70.469 | >= 70.0 | left_hand->right_hand | single_mid | 1 | 21 | score_valid:score_valid | action_window_net:used | 单帧右手被左手幽灵副本替代，模拟偶发双手检测误报。 |
| sparse_left_duplicates_right_every_6f | positive | PASS | 70.469 | >= 70.0 | right_hand->left_hand | sparse_every_6f | 3 | 63 | score_valid:score_valid | action_window_net:used | 稀疏帧左手变成右手幽灵副本，完整动作证据仍应可评分。 |
| sparse_right_duplicates_left_every_6f | positive | PASS | 73.032 | >= 70.0 | left_hand->right_hand | sparse_every_6f | 3 | 63 | score_valid:score_valid | action_window_net:used | 稀疏帧右手变成左手幽灵副本，完整动作证据仍应可评分。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | left_hand->right_hand | none | 0 | 0 | score_valid:score_valid | action_window_net:used | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

## 说明

- 该门补充的是单手检测被误复制成双手的网页跟踪风险，不替代 hand-label-flicker、hand-dropout、missing-mask 或 inter-hand temporal desync 门。
- 强持续幽灵手会改变真实双手语义，本轮仅作为诊断边界记录；是否升级为硬负例需结合真实摄像头样本和人工标注。
- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。

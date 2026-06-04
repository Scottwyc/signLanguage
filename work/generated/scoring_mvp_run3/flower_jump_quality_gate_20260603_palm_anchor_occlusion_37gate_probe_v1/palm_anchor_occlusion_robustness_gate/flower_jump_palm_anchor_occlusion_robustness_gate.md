# 花/跳掌根锚点遮挡鲁棒性门

- 生成时间：`2026-06-03T20:40:22`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，在 hand landmark mask 层合成 wrist/MCP/palm-anchor 丢失并重建 motion/relation/hand-shape 特征；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：短时或稀疏掌根锚点不可见仍可正常评分；核心掌根/指根全程不可见必须低分或进入重采/语义失败解释。

- 5080 状态：worker=`ready`，pid=`811485`，reload_count=`14`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向锚点缺失 | 核心全缺最高分 | 最强负例 | 诊断最低分 | 最弱诊断锚点缺失 |
|---|---|---:|---|---:|---|---:|---|
| 花 | PASS | 95.791 | right_middle20_wrist_mcp_anchor | 11.140 | right_all_mcp_anchor_negative | 76.069 | right_core40_palm_anchor_diagnostic |
| 跳 | PASS | 70.469 | right_sparse_palm_anchor | 10.158 | left_all_palm_anchor_negative | 76.758 | right_core40_palm_anchor_diagnostic |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 遮挡帧 | landmark | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---:|---|---|---|---|
| right_core40_palm_anchor_diagnostic | diagnostic | DIAG | 76.069 | diagnostic | 21/53 | 0,1,5,9,13,17 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 核心段 40% palm anchors 缺失属于边界情况，记录分数但不设硬门。 |
| right_all_palm_anchor_negative | negative | PASS | 11.048 | <= 45.0 或重采/语义失败 | 53/53 | 0,1,5,9,13,17 | semantic_mismatch:flower_opening_guard_failed | short_visible_core:query_not_short_core_capture | 开花核心掌根/手指根部全程不可见，不能被当作完整花动作。 |
| right_all_mcp_anchor_negative | negative | PASS | 11.140 | <= 45.0 或重采/语义失败 | 53/53 | 5,9,13,17 | semantic_mismatch:flower_opening_guard_failed | short_visible_core:query_not_short_core_capture | 开花核心 MCP 全程不可见时，开合语义不可靠，必须低分或语义失败。 |
| right_middle20_wrist_mcp_anchor | positive | PASS | 95.791 | >= 70.0 | 11/53 | 0,5,9,13,17 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花核心手中段 20% wrist+MCP 锚点不可见，作为强正向容错门。 |
| right_middle20_mcp_anchor | positive | PASS | 95.853 | >= 70.0 | 11/53 | 5,9,13,17 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花核心手中段 20% MCP 锚点不可见，仍应由可见指尖/时序恢复。 |
| right_sparse_palm_anchor | positive | PASS | 98.645 | >= 70.0 | 8/53 | 0,1,5,9,13,17 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花核心手稀疏 palm-anchor mask 闪断，指尖和开合过程仍可见。 |
| right_single_palm_anchor | positive | PASS | 99.232 | >= 70.0 | 1/53 | 0,1,5,9,13,17 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花核心手单帧 wrist/MCP palm anchors 丢失，模拟网页短时追踪断点。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | 0/53 | - | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 标准序列剥离基础组后重建 motion/relation 特征，应保持近满分。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 遮挡帧 | landmark | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---:|---|---|---|---|
| right_core40_palm_anchor_diagnostic | diagnostic | DIAG | 76.758 | diagnostic | 7/19 | 0,1,5,9,13,17 | score_valid:score_valid | full_sequence_local_relation_segment:used | 右手核心段 40% palm anchors 缺失属于强边界，仅记录分数。 |
| left_core40_palm_anchor_diagnostic | diagnostic | DIAG | 80.038 | diagnostic | 7/19 | 0,1,5,9,13,17 | score_valid:score_valid | full_sequence_local_relation_segment:used | 左手地面核心段 40% palm anchors 缺失属于强边界，仅记录分数。 |
| right_all_palm_anchor_negative | negative | PASS | 3.217 | <= 45.0 或重采/语义失败 | 19/19 | 0,1,5,9,13,17 | semantic_mismatch:missing_relation_delta | action_window_net:missing_relation_delta | 右手两指小人掌根/指根全程不可见，双手关系不可靠。 |
| left_all_palm_anchor_negative | negative | PASS | 10.158 | <= 45.0 或重采/语义失败 | 19/19 | 0,1,5,9,13,17 | semantic_mismatch:missing_relation_delta | action_window_net:missing_relation_delta | 左手地面掌根/指根全程不可见，跳的支撑关系缺失。 |
| right_sparse_palm_anchor | positive | PASS | 70.469 | >= 70.0 | 3/19 | 0,1,5,9,13,17 | score_valid:score_valid | action_window_net:used | 右手两指小人稀疏掌根锚点闪断，双手关系仍保留。 |
| left_sparse_palm_anchor | positive | PASS | 70.469 | >= 70.0 | 3/19 | 0,1,5,9,13,17 | score_valid:score_valid | action_window_net:used | 左手地面稀疏 palm-anchor mask 闪断，双手关系仍应通过。 |
| both_sparse_wrist_anchor | positive | PASS | 70.469 | >= 70.0 | 3/19 | 0 | score_valid:score_valid | action_window_net:used | 双手 wrist 稀疏闪断，覆盖网页手腕点短时漂移/缺失。 |
| right_middle20_mcp_anchor | positive | PASS | 74.629 | >= 70.0 | 3/19 | 5,9,13,17 | score_valid:score_valid | full_sequence_local_relation_segment:used | 右手中段 20% MCP 锚点不可见，但食指/中指和相对运动仍可见。 |
| right_middle20_wrist_mcp_anchor | positive | PASS | 74.629 | >= 70.0 | 3/19 | 0,5,9,13,17 | score_valid:score_valid | full_sequence_local_relation_segment:used | 右手中段 20% wrist+MCP 锚点不可见，验证关系 fallback 的稳定性。 |
| both_middle20_mcp_anchor | positive | PASS | 74.629 | >= 70.0 | 3/19 | 5,9,13,17 | score_valid:score_valid | full_sequence_local_relation_segment:used | 双手中段 20% MCP 锚点不可见，验证仍可从核心双手关系评分。 |
| right_single_palm_anchor | positive | PASS | 81.566 | >= 70.0 | 1/19 | 0,1,5,9,13,17 | score_valid:score_valid | full_sequence_local_relation_segment:used | 右手两指小人单帧 palm anchors 丢失，跳跃关系仍应可评分。 |
| left_middle20_wrist_mcp_anchor | positive | PASS | 81.570 | >= 70.0 | 3/19 | 0,5,9,13,17 | score_valid:score_valid | action_window_net:used | 左手地面中段 20% wrist+MCP 锚点不可见，地面语义仍可由可见点恢复。 |
| left_single_palm_anchor | positive | PASS | 87.420 | >= 70.0 | 1/19 | 0,1,5,9,13,17 | score_valid:score_valid | action_window_net:used | 左手地面单帧 palm anchors 丢失，地面关系不应整体失败。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | 0/19 | - | score_valid:score_valid | action_window_net:used | 标准序列剥离基础组后重建 motion/relation 特征，应保持近满分。 |

## 说明

- 该门补充的是 wrist/MCP 掌根锚点短时丢失，不替代 fingertip、edge clipping 或整手 missing-mask 门。
- hand-shape 派生特征在 palm scale 不可靠时应标为缺失，避免 `1e-3` 兜底造成形状值爆炸。
- `core40_*_diagnostic` 是强边界记录：当前模型可能仍能从可见指尖和双手关系恢复语义，因此不作为硬失败门。
- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。

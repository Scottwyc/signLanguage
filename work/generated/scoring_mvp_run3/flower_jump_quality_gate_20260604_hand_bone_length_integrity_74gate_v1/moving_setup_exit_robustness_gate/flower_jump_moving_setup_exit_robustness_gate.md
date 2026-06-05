# 花/跳动态入场退场鲁棒性门

- 生成时间：`2026-06-04T18:28:46`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，在骨架层合成手部移动入场/退场并重建 hand-shape、motion、two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：真实网页录制出现开始前移动手到位或结束后放下手时，只要完整核心动作仍在，评分保持正常；只有入场片段不能通过。

- 5080 状态：worker=`ready`，worker_pid=`811485`，reload_count=`30`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向动态污染 | 入场-only 最高分 | 最强入场-only | 诊断分数范围 |
|---|---|---:|---|---:|---|---|
| 花 | PASS | 96.727 | suffix_moving_exit_25pct | 21.271 | moving_entry_only_35pct_negative | 21.959 - 96.954 |
| 跳 | PASS | 99.998 | entry_exit_moving_18pct | 0.016 | moving_entry_only_35pct_negative | 4.284 - 98.052 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 长度比 | alignment | capture_quality | reason | 说明 |
|---|---|---|---:|---|---:|---|---|---|---|
| moving_exit_only_35pct_diagnostic | diagnostic | DIAG | 21.959 | diagnostic | 0.358 | full_sequence_with_action_window_diagnostics | semantic_mismatch | flower_opening_guard_failed | 只有移动离场可能保留结束姿态，不作为负向硬门，仅记录边界。 |
| strong_entry_exit_45pct_diagnostic | diagnostic | DIAG | 96.954 | diagnostic | 1.906 | full_sequence_with_action_window_diagnostics | score_valid | score_valid | 更长且更大幅的动态入场/退场，只记录诊断边界。 |
| moving_entry_only_35pct_negative | negative | PASS | 21.271 | <= 45.0 或重采/语义失败 | 0.358 | full_sequence_with_action_window_diagnostics | needs_recapture | flower_core_hand_presence_low | 只有移动入场，没有完整手语核心，不能当作目标通过。 |
| suffix_moving_exit_25pct | positive | PASS | 96.727 | >= 70.0 | 1.245 | full_sequence_with_action_window_diagnostics | score_valid | score_valid | 动作后有手部移动离场，但完整核心动作仍在。 |
| entry_exit_moving_18pct | positive | PASS | 98.276 | >= 70.0 | 1.377 | full_sequence_with_action_window_diagnostics | score_valid | score_valid | 录制前后都有动态手部污染，核心手语完整。 |
| long_prefix_moving_entry_35pct | positive | PASS | 99.361 | >= 70.0 | 1.358 | full_sequence_with_action_window_diagnostics | score_valid | score_valid | 较长移动入场，验证 action-window 能聚焦真实核心。 |
| prefix_moving_entry_25pct | positive | PASS | 99.522 | >= 70.0 | 1.245 | full_sequence_with_action_window_diagnostics | score_valid | score_valid | 动作前有手部移动入场，但完整核心动作仍在。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | 1.000 | full_sequence_with_action_window_diagnostics | score_valid | score_valid | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 长度比 | alignment | capture_quality | reason | 说明 |
|---|---|---|---:|---|---:|---|---|---|---|
| moving_exit_only_35pct_diagnostic | diagnostic | DIAG | 4.284 | diagnostic | 0.368 | semantic_action_window | semantic_mismatch | phase_order_disorder | 只有移动离场可能保留结束姿态，不作为负向硬门，仅记录边界。 |
| strong_entry_exit_45pct_diagnostic | diagnostic | DIAG | 98.052 | diagnostic | 1.947 | semantic_action_window | score_valid | score_valid | 更长且更大幅的动态入场/退场，只记录诊断边界。 |
| moving_entry_only_35pct_negative | negative | PASS | 0.016 | <= 45.0 或重采/语义失败 | 0.368 | semantic_action_window | needs_recapture | jump_two_hand_presence_low | 只有移动入场，没有完整手语核心，不能当作目标通过。 |
| entry_exit_moving_18pct | positive | PASS | 99.998 | >= 70.0 | 1.316 | semantic_action_window | score_valid | score_valid | 录制前后都有动态手部污染，核心手语完整。 |
| suffix_moving_exit_25pct | positive | PASS | 99.999 | >= 70.0 | 1.263 | semantic_action_window | score_valid | score_valid | 动作后有手部移动离场，但完整核心动作仍在。 |
| long_prefix_moving_entry_35pct | positive | PASS | 100.000 | >= 70.0 | 1.368 | semantic_action_window | score_valid | score_valid | 较长移动入场，验证 action-window 能聚焦真实核心。 |
| prefix_moving_entry_25pct | positive | PASS | 100.000 | >= 70.0 | 1.263 | semantic_action_window | score_valid | score_valid | 动作前有手部移动入场，但完整核心动作仍在。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | 1.000 | semantic_action_window | score_valid | score_valid | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

## 说明

- 该门补充静止 padding 门：这里额外帧是移动手部，不是重复第一帧或最后一帧。
- 该门补充重复动作门：这里不是完整动作重复，而是非语义入场/退场污染。
- 该门是合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。

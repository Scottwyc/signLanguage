# 花/跳录制起止裁剪鲁棒性门

- 生成时间：`2026-06-03T17:20:07`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，在骨架序列层面裁剪起止片段；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：轻度起录/停录偏差仍高分；明确缺少核心动作的词条半段样本不能通过。

- 5080 状态：worker=`ready`，worker_pid=`811485`，reload_count=`14`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向裁剪 | 缺核心最高分 | 最强缺核心裁剪 | 诊断分数范围 |
|---|---|---:|---|---:|---|---|
| 花 | PASS | 97.958 | trim_end_15pct | 41.949 | early_60pct_missing_bloom | 81.209 - 81.209 |
| 跳 | PASS | 80.750 | trim_start_15pct | 45.000 | early_half_missing_landing | 82.538 - 82.538 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 长度比 | alignment | capture_quality | reason | 说明 |
|---|---|---|---:|---|---:|---|---|---|---|
| late_half_diagnostic | diagnostic | DIAG | 81.209 | diagnostic | 0.509 | full_sequence_with_action_window_diagnostics | score_valid | score_valid | 花的后半段可能仍包含绽放核心，仅诊断记录，不作为负向门。 |
| early_half_missing_bloom | negative | PASS | 39.368 | <= 45.0 或重采/语义失败 | 0.491 | full_sequence_with_action_window_diagnostics | semantic_mismatch | phase_order_disorder | 只录到前半段，缺少花手张开/绽放核心变化。 |
| early_60pct_missing_bloom | negative | PASS | 41.949 | <= 45.0 或重采/语义失败 | 0.604 | full_sequence_with_action_window_diagnostics | semantic_mismatch | phase_order_disorder | 结束过早，绽放动作不完整。 |
| trim_end_15pct | positive | PASS | 97.958 | >= 70.0 | 0.849 | full_sequence_with_action_window_diagnostics | score_valid | score_valid | 录制略早结束，核心动作仍完整。 |
| center_70pct | positive | PASS | 98.013 | >= 70.0 | 0.698 | full_sequence_with_action_window_diagnostics | score_valid | score_valid | 仅保留中间约 70% 的动作窗口，仍应保留主要语义相位。 |
| trim_both_10pct | positive | PASS | 98.643 | >= 70.0 | 0.811 | full_sequence_with_action_window_diagnostics | score_valid | score_valid | 起止边界同时轻度裁剪，动作主段仍在。 |
| trim_start_15pct | positive | PASS | 99.569 | >= 70.0 | 0.849 | full_sequence_with_action_window_diagnostics | score_valid | score_valid | 录制略晚开始，核心动作仍完整。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 长度比 | alignment | capture_quality | reason | 说明 |
|---|---|---|---:|---|---:|---|---|---|---|
| keyframes_6_diagnostic | diagnostic | DIAG | 82.538 | diagnostic | 0.316 | semantic_action_window | score_valid | score_valid | 跳在少量关键帧下通常仍可表达动作，仅诊断采样边界。 |
| late_half_missing_takeoff | negative | PASS | 25.478 | <= 45.0 或重采/语义失败 | 0.474 | semantic_action_window | semantic_mismatch | relation_direction_mismatch | 开始过晚，缺少左手地面与右手起跳的核心关系。 |
| early_half_missing_landing | negative | PASS | 45.000 | <= 45.0 或重采/语义失败 | 0.526 | semantic_action_window | semantic_mismatch | phase_order_disorder | 只录到前半段，缺少完整弹跳落点/关系方向。 |
| trim_start_15pct | positive | PASS | 80.750 | >= 70.0 | 0.842 | semantic_action_window | score_valid | score_valid | 录制略晚开始，核心动作仍完整。 |
| trim_both_10pct | positive | PASS | 80.985 | >= 70.0 | 0.789 | semantic_action_window | score_valid | score_valid | 起止边界同时轻度裁剪，动作主段仍在。 |
| trim_end_15pct | positive | PASS | 80.991 | >= 70.0 | 0.842 | semantic_action_window | score_valid | score_valid | 录制略早结束，核心动作仍完整。 |
| center_70pct | positive | PASS | 81.045 | >= 70.0 | 0.684 | semantic_action_window | score_valid | score_valid | 仅保留中间约 70% 的动作窗口，仍应保留主要语义相位。 |

## 说明

- 正向裁剪验证网页录制起点或终点略有偏差时，完整核心动作仍可被高分识别。
- 负向裁剪只选择经当前模板验证且语义明确缺核心的词条半段；不稳定半段只作为诊断输出。
- 该门是合成裁剪压力测试，不能替代真实网页摄像头样本。

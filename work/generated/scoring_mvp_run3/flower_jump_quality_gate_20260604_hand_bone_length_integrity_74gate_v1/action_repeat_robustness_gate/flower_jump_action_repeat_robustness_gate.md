# 花/跳重复动作录制鲁棒性门

- 生成时间：`2026-06-04T18:22:00`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，在骨架序列层面拼接/重复动作片段并重建派生特征；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：用户在一次网页录制中多做一遍或停止偏晚时，完整动作实例仍可被高分识别；setup-only 片段不能通过。

- 5080 状态：worker=`ready`，worker_pid=`811485`，reload_count=`30`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向重复 | 不完整最高分 | 最强不完整负例 | 诊断分数范围 |
|---|---|---:|---|---:|---|---|
| 花 | PASS | 96.505 | repeat_full_2x_mid_pause | 21.902 | setup_only_35pct_negative | 77.686 - 95.417 |
| 跳 | PASS | 81.950 | core_repeat_middle | 12.239 | landing_only_35pct_negative | 77.868 - 77.868 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 长度比 | alignment | capture_quality | reason | 说明 |
|---|---|---|---:|---|---:|---|---|---|---|
| late_bloom_only_diagnostic | diagnostic | DIAG | 77.686 | diagnostic | 0.358 | full_sequence_with_action_window_diagnostics | score_valid | score_valid | 花的后段可能仍包含绽放核心，作为诊断边界记录，不设负向门。 |
| repeat_full_3x_diagnostic | diagnostic | DIAG | 95.417 | diagnostic | 3.000 | full_sequence_with_action_window_diagnostics | score_valid | score_valid | 连续做三遍属于长录制诊断边界，记录分数但不作为硬门。 |
| setup_only_35pct_negative | negative | PASS | 21.902 | <= 45.0 或重采/语义失败 | 0.358 | full_sequence_with_action_window_diagnostics | semantic_mismatch | flower_opening_guard_failed | 只录到动作开头 setup，不能当作完整手语通过。 |
| repeat_full_2x_mid_pause | positive | PASS | 96.505 | >= 70.0 | 2.094 | full_sequence_with_action_window_diagnostics | score_valid | score_valid | 两遍动作之间有短暂停顿，模拟用户重做一次后才停止。 |
| core_repeat_middle | positive | PASS | 96.657 | >= 70.0 | 1.585 | full_sequence_with_action_window_diagnostics | score_valid | score_valid | 核心动作段重复一次，完整起止仍可见。 |
| repeat_full_2x | positive | PASS | 96.707 | >= 70.0 | 2.000 | full_sequence_with_action_window_diagnostics | score_valid | score_valid | 完整动作连续做两遍，录制应能匹配其中一个完整实例。 |
| full_then_suffix_partial | positive | PASS | 97.025 | >= 70.0 | 1.358 | full_sequence_with_action_window_diagnostics | score_valid | score_valid | 完整动作后又开始下一遍的后段/收尾，停止偏晚。 |
| prefix_partial_then_full | positive | PASS | 98.255 | >= 70.0 | 1.358 | full_sequence_with_action_window_diagnostics | score_valid | score_valid | 先做了不完整开头，然后补做一遍完整动作。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 长度比 | alignment | capture_quality | reason | 说明 |
|---|---|---|---:|---|---:|---|---|---|---|
| repeat_full_3x_diagnostic | diagnostic | DIAG | 77.868 | diagnostic | 3.000 | semantic_action_window | score_valid | score_valid | 连续做三遍属于长录制诊断边界，记录分数但不作为硬门。 |
| setup_only_35pct_negative | negative | PASS | 9.428 | <= 45.0 或重采/语义失败 | 0.368 | semantic_action_window | semantic_mismatch | weak_same_direction_vertical_jump | 只录到动作开头 setup，不能当作完整手语通过。 |
| landing_only_35pct_negative | negative | PASS | 12.239 | <= 45.0 或重采/语义失败 | 0.368 | semantic_action_window | semantic_mismatch | relation_direction_mismatch | 跳只录到后段落点/收尾，缺少完整起跳关系。 |
| core_repeat_middle | positive | PASS | 81.950 | >= 70.0 | 1.579 | semantic_action_window | score_valid | score_valid | 核心动作段重复一次，完整起止仍可见。 |
| repeat_full_2x | positive | PASS | 93.716 | >= 70.0 | 2.000 | semantic_action_window | score_valid | score_valid | 完整动作连续做两遍，录制应能匹配其中一个完整实例。 |
| repeat_full_2x_mid_pause | positive | PASS | 93.717 | >= 70.0 | 2.158 | semantic_action_window | score_valid | score_valid | 两遍动作之间有短暂停顿，模拟用户重做一次后才停止。 |
| prefix_partial_then_full | positive | PASS | 98.831 | >= 70.0 | 1.368 | semantic_action_window | score_valid | score_valid | 先做了不完整开头，然后补做一遍完整动作。 |
| full_then_suffix_partial | positive | PASS | 99.939 | >= 70.0 | 1.368 | semantic_action_window | score_valid | score_valid | 完整动作后又开始下一遍的后段/收尾，停止偏晚。 |

## 说明

- 正向重复验证网页录制里出现“先试一次、再完整做一次”或“完整做完后又开始下一遍”时，评分仍能落在正常区间。
- 负向不完整样本只验证 setup-only 或缺核心的极短片段不能关闭目标；不稳定半段保留为诊断输出。
- 该门是合成重复压力测试，不能替代正式 marker 后的真实网页摄像头样本。

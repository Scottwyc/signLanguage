# 花/跳核心相位速度鲁棒性门

- 生成时间：`2026-06-04T00:07:16`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，只改变词义核心窗口内的帧密度/速度曲线，并重建 motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：`花` 的绽放核心和 `跳` 的起跳/双手关系核心快慢不同仍可评分；核心中段被跳过只记录诊断边界。

- 5080 状态：worker=`ready`，worker_pid=`811485`，reload_count=`15`，last_reload_error=`None`

## 结论

- 综合状态：`FAIL`

| 目标词 | 状态 | 正向最低分 | 最弱正向核心速度 | 诊断最低分 | 最弱诊断边界 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 95.085 | bloom_core_fast_then_slow | 95.509 | bloom_core_fast_0.45x_diagnostic | 70.000 |
| 跳 | FAIL | 23.502 | jump_relation_core_slow_1.55x | 80.128 | jump_relation_core_fast_0.45x_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 长度比 | alignment | capture_quality | reason | 说明 |
|---|---|---|---:|---|---:|---|---|---|---|
| bloom_core_fast_0.45x_diagnostic | diagnostic | DIAG | 95.509 | diagnostic | 0.755 | full_sequence_with_action_window_diagnostics | score_valid | score_valid | 核心段极度压缩，作为快动作/欠采样边界。 |
| bloom_core_gap_0.45_diagnostic | diagnostic | DIAG | 96.809 | diagnostic | 0.792 | full_sequence_with_action_window_diagnostics | score_valid | score_valid | 核心段中部被跳过，记录缺核心边界，不作为普通速率鲁棒性。 |
| bloom_core_fast_then_slow | positive | PASS | 95.085 | >= 70.0 | 1.000 | full_sequence_with_action_window_diagnostics | score_valid | score_valid | 核心段前半快、后半慢，模拟用户在关键姿态附近减速。 |
| bloom_core_fast_0.70x | positive | PASS | 97.372 | >= 70.0 | 0.868 | full_sequence_with_action_window_diagnostics | score_valid | score_valid | 词义核心段更快，但核心过程仍完整可见。 |
| bloom_core_slow_1.55x | positive | PASS | 97.967 | >= 70.0 | 1.245 | full_sequence_with_action_window_diagnostics | score_valid | score_valid | 词义核心段更慢，局部帧更密但语义顺序不变。 |
| bloom_core_pause_0.25 | positive | PASS | 98.685 | >= 70.0 | 1.113 | full_sequence_with_action_window_diagnostics | score_valid | score_valid | 核心段有短暂停顿，但动作起止和关键形态完整。 |
| bloom_core_slow_then_fast | positive | PASS | 99.177 | >= 70.0 | 1.000 | full_sequence_with_action_window_diagnostics | score_valid | score_valid | 核心段前半慢、后半快，模拟用户完成核心动作时加速。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | 1.000 | full_sequence_with_action_window_diagnostics | score_valid | score_valid | 标准序列剥离派生组后重建 motion/relation，应保持近满分。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 长度比 | alignment | capture_quality | reason | 说明 |
|---|---|---|---:|---|---:|---|---|---|---|
| jump_relation_core_fast_0.45x_diagnostic | diagnostic | DIAG | 80.128 | diagnostic | 0.684 | semantic_action_window | score_valid | score_valid | 核心段极度压缩，作为快动作/欠采样边界。 |
| jump_relation_core_gap_0.45_diagnostic | diagnostic | DIAG | 80.303 | diagnostic | 0.737 | semantic_action_window | score_valid | score_valid | 核心段中部被跳过，记录缺核心边界，不作为普通速率鲁棒性。 |
| jump_relation_core_slow_1.55x | positive | FAIL | 23.502 | >= 70.0 | 1.316 | semantic_action_window | needs_recapture | jump_two_hand_presence_low | 词义核心段更慢，局部帧更密但语义顺序不变。 |
| jump_relation_core_slow_then_fast | positive | PASS | 76.001 | >= 70.0 | 1.000 | semantic_action_window | score_valid | score_valid | 核心段前半慢、后半快，模拟用户完成核心动作时加速。 |
| jump_relation_core_fast_0.70x | positive | PASS | 85.000 | >= 70.0 | 0.842 | semantic_action_window | score_valid | score_valid | 词义核心段更快，但核心过程仍完整可见。 |
| jump_relation_core_pause_0.25 | positive | PASS | 87.934 | >= 70.0 | 1.158 | semantic_action_window | score_valid | score_valid | 核心段有短暂停顿，但动作起止和关键形态完整。 |
| jump_relation_core_fast_then_slow | positive | PASS | 88.816 | >= 70.0 | 1.000 | semantic_action_window | score_valid | score_valid | 核心段前半快、后半慢，模拟用户在关键姿态附近减速。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | 1.000 | semantic_action_window | score_valid | score_valid | 标准序列剥离派生组后重建 motion/relation，应保持近满分。 |

## 说明

- 该门补充一般 temporal-rate gate：这里只变核心语义窗口，不做整段全局速率重采样。
- 诊断核心缺口用于观察 scorer 对缺核心样本的边界，不能作为正常快慢风格放宽。
- 该门是合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。

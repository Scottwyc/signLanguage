# 花/跳时序速率鲁棒性门

- 生成时间：`2026-06-03T14:33:04`
- 总体：`FAIL`
- 模板根目录：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义权重：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 门槛：正向速率变化最低分 `>= 70.0`；内部核心采样跳过需低分或进入 `needs_recapture, semantic_mismatch`。
- 口径：只读缓存 Holistic JSON，在骨架序列层面做单调时间轴压缩/拉伸/局部速率变化，并重建 motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。

## 汇总

| 词条 | 状态 | 正向最低分 | 最弱正向速率扰动 | 内部核心缺口最高分 | 最强核心缺口 | 诊断最低分 | 最弱诊断边界 |
|---|---|---:|---|---:|---|---:|---|
| 花 | FAIL | 45.000 | same_count_front_slow_back_fast | 94.439 | bloom_core_gap_negative | 95.544 | global_fast_0.50x_diagnostic |
| 跳 | FAIL | 21.338 | same_count_micro_rate_jitter | 84.149 | jump_relation_core_gap_negative | 80.007 | global_slow_2.25x_diagnostic |

## 明细

### 花

| 变体 | 类型 | 状态 | 分数 | 阈值 | 帧数/比例 | quality | floor | 说明 |
|---|---|---|---:|---|---|---|---|---|
| same_count_front_slow_back_fast | positive | FAIL | 45.000 | >= 70.0 | 53 / len_ratio=1.00 | semantic_mismatch:phase_order_disorder | short_visible_core:phase_order_disorder | 同样帧数内前段慢、后段快，完整语义相位仍在。 |
| same_count_front_fast_back_slow | positive | PASS | 95.406 | >= 70.0 | 53 / len_ratio=1.00 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 同样帧数内前段快、后段慢，完整语义相位仍在。 |
| same_count_core_slow | positive | PASS | 97.411 | >= 70.0 | 53 / len_ratio=1.00 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 同样帧数内核心动作被采得更密，起止顺序不变。 |
| same_count_core_fast | positive | PASS | 92.883 | >= 70.0 | 53 / len_ratio=1.00 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 同样帧数内核心动作被采得更稀，仍保留核心过程。 |
| same_count_micro_rate_jitter | positive | FAIL | 62.560 | >= 70.0 | 53 / len_ratio=1.00 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 浏览器采样间隔轻微不均匀，但时间顺序单调。 |
| global_fast_0.75x | positive | PASS | 97.818 | >= 70.0 | 40 / rate=0.75 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 用户动作整体更快，保留约 75% 帧数并重建运动特征。 |
| global_slow_1.50x | positive | PASS | 97.376 | >= 70.0 | 80 / rate=1.50 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 用户动作整体更慢，约 1.5 倍采样帧并重建运动特征。 |
| bloom_core_hold_2x | positive | PASS | 96.557 | >= 70.0 | 73 / rate=1.35 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花核心阶段停留更久，但撮合到绽放过程完整。 |
| global_fast_0.50x_diagnostic | diagnostic | PASS | 95.544 | diagnostic | 26 / rate=0.50 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 极快采样只保留约半数帧，作为欠采样边界诊断。 |
| global_slow_2.25x_diagnostic | diagnostic | PASS | 99.588 | diagnostic | 119 / rate=2.25 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 极慢动作或高频重复采样，作为过采样边界诊断。 |
| bloom_core_gap_negative | negative | FAIL | 94.439 | <= 45.0 或重采/语义失败 | 53 / len_ratio=1.00 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 内部绽放核心被采样跳过，不能靠时间轴鲁棒性抬高。 |

### 跳

| 变体 | 类型 | 状态 | 分数 | 阈值 | 帧数/比例 | quality | floor | 说明 |
|---|---|---|---:|---|---|---|---|---|
| same_count_front_slow_back_fast | positive | PASS | 73.877 | >= 70.0 | 19 / len_ratio=1.00 | score_valid:score_valid | action_window_net:used | 同样帧数内前段慢、后段快，完整语义相位仍在。 |
| same_count_front_fast_back_slow | positive | PASS | 89.453 | >= 70.0 | 19 / len_ratio=1.00 | score_valid:score_valid | action_window_net:used | 同样帧数内前段快、后段慢，完整语义相位仍在。 |
| same_count_core_slow | positive | PASS | 86.090 | >= 70.0 | 19 / len_ratio=1.00 | score_valid:score_valid | full_sequence_local_relation_segment:used | 同样帧数内核心动作被采得更密，起止顺序不变。 |
| same_count_core_fast | positive | PASS | 85.421 | >= 70.0 | 19 / len_ratio=1.00 | score_valid:score_valid | action_window_net:used | 同样帧数内核心动作被采得更稀，仍保留核心过程。 |
| same_count_micro_rate_jitter | positive | FAIL | 21.338 | >= 70.0 | 19 / len_ratio=1.00 | needs_recapture:jump_two_hand_presence_low | -:insufficient_two_hand_presence | 浏览器采样间隔轻微不均匀，但时间顺序单调。 |
| global_fast_0.75x | positive | PASS | 89.383 | >= 70.0 | 14 / rate=0.75 | score_valid:score_valid | action_window_net:used | 用户动作整体更快，保留约 75% 帧数并重建运动特征。 |
| global_slow_1.50x | positive | PASS | 77.195 | >= 70.0 | 28 / rate=1.50 | score_valid:score_valid | action_window_net:used | 用户动作整体更慢，约 1.5 倍采样帧并重建运动特征。 |
| jump_core_hold_2x | positive | PASS | 80.314 | >= 70.0 | 29 / rate=1.45 | score_valid:score_valid | full_sequence_local_relation_segment:used | 弹跳核心阶段稍慢，左右手关系和两指手形仍完整。 |
| global_fast_0.50x_diagnostic | diagnostic | PASS | 81.486 | diagnostic | 10 / rate=0.50 | score_valid:score_valid | action_window_net:used | 极快弹跳只保留约半数帧，记录采样边界。 |
| global_slow_2.25x_diagnostic | diagnostic | PASS | 80.007 | diagnostic | 43 / rate=2.25 | score_valid:score_valid | action_window_net:used | 极慢弹跳或高频重复采样，记录过采样边界。 |
| jump_relation_core_gap_negative | negative | FAIL | 84.149 | <= 45.0 或重采/语义失败 | 19 / len_ratio=1.00 | score_valid:score_valid | action_window_net:used | 内部弹跳关系变化被采样跳过，应降分或进入重采/语义失败。 |

## 结论

- 单调局部速度变化和整体快慢变化用于验证网页摄像头帧率/用户动作速度差异不会直接打崩正常动作。
- 内部核心语义被采样跳过是重采或语义失败边界，不能用速率鲁棒性把缺核心动作样本抬成正常高分。
- 该门仍是合成压力测试，不能替代正式 marker 后真实网页摄像头样本。

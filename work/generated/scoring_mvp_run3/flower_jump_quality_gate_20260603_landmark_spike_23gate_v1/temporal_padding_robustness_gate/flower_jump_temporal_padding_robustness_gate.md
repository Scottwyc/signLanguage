# 花/跳静止 padding 与时序鲁棒性门

- 生成时间：`2026-06-03T12:43:45`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，在骨架序列层面加入前后静止帧或静态假动作；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：完整动作被前后静止帧包围或整体变慢时仍高分；纯静态起始/中段/结束姿态不能通过。

- 5080 状态：worker=`ready`，worker_pid=`811485`，reload_count=`14`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向变体 | 静态最高分 | 最强静态变体 |
|---|---|---:|---|---:|---|
| 花 | PASS | 97.862 | suffix_hold_25pct | 1.460 | static_hold_mid |
| 跳 | PASS | 79.124 | slow_repeat_each_2x | 31.418 | static_hold_mid |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 长度比 | capture_quality | reason | 说明 |
|---|---|---|---:|---|---:|---|---|---|
| static_hold_start | negative | PASS | 1.156 | <= 45.0 或重采/语义失败 | 1.000 | needs_recapture | flower_core_hand_presence_low | 只有起始静止姿态，缺少动作语义。 |
| static_hold_end | negative | PASS | 1.387 | <= 45.0 或重采/语义失败 | 1.000 | semantic_mismatch | flower_opening_guard_failed | 只有结束静止姿态，缺少完整动作过程。 |
| static_hold_mid | negative | PASS | 1.460 | <= 45.0 或重采/语义失败 | 1.000 | semantic_mismatch | flower_opening_guard_failed | 只有中间静止姿态，缺少起止动态。 |
| suffix_hold_25pct | positive | PASS | 97.862 | >= 70.0 | 1.245 | score_valid | score_valid | 动作后有结束静止帧，但完整动作仍在。 |
| prefix_hold_50pct | positive | PASS | 98.556 | >= 65.0 | 1.491 | score_valid | score_valid | 较长准备静止帧，仍应主要由核心动作决定。 |
| both_hold_20pct | positive | PASS | 98.570 | >= 70.0 | 1.415 | score_valid | score_valid | 采集窗口前后都有静止帧，但核心动作完整。 |
| prefix_hold_25pct | positive | PASS | 99.522 | >= 70.0 | 1.245 | score_valid | score_valid | 动作前有准备静止帧，但完整动作仍在。 |
| slow_repeat_each_2x | positive | PASS | 99.588 | >= 70.0 | 2.000 | score_valid | score_valid | 动作速度变慢但语义相位完整。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 长度比 | capture_quality | reason | 说明 |
|---|---|---|---:|---|---:|---|---|---|
| static_hold_start | negative | PASS | 0.211 | <= 45.0 或重采/语义失败 | 1.000 | needs_recapture | jump_two_hand_presence_low | 只有起始静止姿态，缺少动作语义。 |
| static_hold_end | negative | PASS | 21.721 | <= 45.0 或重采/语义失败 | 1.000 | semantic_mismatch | weak_relation_delta | 只有结束静止姿态，缺少完整动作过程。 |
| static_hold_mid | negative | PASS | 31.418 | <= 45.0 或重采/语义失败 | 1.000 | semantic_mismatch | weak_relation_delta | 只有中间静止姿态，缺少起止动态。 |
| slow_repeat_each_2x | positive | PASS | 79.124 | >= 70.0 | 2.000 | score_valid | score_valid | 动作速度变慢但语义相位完整。 |
| both_hold_20pct | positive | PASS | 99.999 | >= 70.0 | 1.421 | score_valid | score_valid | 采集窗口前后都有静止帧，但核心动作完整。 |
| suffix_hold_25pct | positive | PASS | 99.999 | >= 70.0 | 1.263 | score_valid | score_valid | 动作后有结束静止帧，但完整动作仍在。 |
| prefix_hold_50pct | positive | PASS | 100.000 | >= 65.0 | 1.526 | score_valid | score_valid | 较长准备静止帧，仍应主要由核心动作决定。 |
| prefix_hold_25pct | positive | PASS | 100.000 | >= 70.0 | 1.263 | score_valid | score_valid | 动作前有准备静止帧，但完整动作仍在。 |

## 说明

- 正向 padding 变体验证真实采集窗口含准备/结束静止帧时仍可对齐核心动作。
- 负向静态变体验证仅有手形或姿态、没有动态语义时不会被误判为通过。
- 该门是合成时序压力测试，不能替代真实网页摄像头样本。

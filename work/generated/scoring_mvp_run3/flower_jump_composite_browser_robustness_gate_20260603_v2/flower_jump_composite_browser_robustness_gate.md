# 花/跳组合网页扰动鲁棒性门

- 生成时间：`2026-06-03T15:07:55`
- 总体：`FAIL`
- 模板根目录：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义权重：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 门槛：正向组合扰动最低分 `>= 70.0`；强组合扰动只记录诊断边界。
- 口径：只读缓存 Holistic JSON，在骨架序列层组合轻微 aspect/坐标/速率/stutter/手部检出扰动，并重建 motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。

## 汇总

| 词条 | 状态 | 正向最低分 | 最弱正向组合 | 诊断最低分 | 最弱诊断组合 |
|---|---|---:|---|---:|---|
| 花 | FAIL | 69.472 | combo_aspect_lowres_rate | 80.313 | diagnostic_strong_browser_stack |
| 跳 | PASS | 73.632 | combo_fast_aspect_hand_quant | 74.006 | diagnostic_dropout_rate_stack |

## 明细

### 花

| 变体 | 类型 | 状态 | 分数 | 阈值 | 帧数/比例 | quality | floor | 说明 |
|---|---|---|---:|---|---|---|---|---|
| combo_aspect_lowres_rate | positive | FAIL | 69.472 | >= 70.0 | 53 / 1.00 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 轻微宽高比失真、低分辨率坐标取整和轻微采样间隔不均叠加。 |
| combo_slow_sparse_freeze_lowres | positive | PASS | 77.955 | >= 70.0 | 64 / 1.21 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 动作稍慢、偶发微冻结和常见 640x480 网格取整同时出现。 |
| combo_fast_aspect_hand_quant | positive | PASS | 80.300 | >= 70.0 | 45 / 0.85 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 动作稍快、轻微反向宽高比失真和手部坐标量化同时出现。 |
| combo_flower_short_dropout_stutter | positive | PASS | 79.860 | >= 70.0 | 53 / 1.00 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花手 2 帧短检出空洞、3 帧中段冻结和轻微宽高比叠加。 |
| diagnostic_strong_browser_stack | diagnostic | PASS | 80.313 | diagnostic | 29 / 0.55 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 强组合压力：极快采样、强宽高比、粗网格和中段冻结，只记录边界。 |
| diagnostic_dropout_rate_stack | diagnostic | PASS | 80.777 | diagnostic | 95 / 1.79 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 较慢动作、核心手短空洞和粗手部坐标量化叠加，只记录边界。 |

### 跳

| 变体 | 类型 | 状态 | 分数 | 阈值 | 帧数/比例 | quality | floor | 说明 |
|---|---|---|---:|---|---|---|---|---|
| combo_aspect_lowres_rate | positive | PASS | 97.115 | >= 70.0 | 19 / 1.00 | score_valid:score_valid | action_window_net:used | 轻微宽高比失真、低分辨率坐标取整和轻微采样间隔不均叠加。 |
| combo_slow_sparse_freeze_lowres | positive | PASS | 77.991 | >= 70.0 | 23 / 1.21 | score_valid:score_valid | action_window_net:used | 动作稍慢、偶发微冻结和常见 640x480 网格取整同时出现。 |
| combo_fast_aspect_hand_quant | positive | PASS | 73.632 | >= 70.0 | 16 / 0.84 | score_valid:score_valid | action_window_net:used | 动作稍快、轻微反向宽高比失真和手部坐标量化同时出现。 |
| combo_jump_short_dropout_stutter | positive | PASS | 92.493 | >= 70.0 | 19 / 1.00 | score_valid:score_valid | action_window_net:used | 跳跃手 1 帧短检出空洞、2 帧中段冻结和轻微宽高比叠加。 |
| diagnostic_strong_browser_stack | diagnostic | PASS | 74.845 | diagnostic | 10 / 0.53 | score_valid:score_valid | action_window_net:used | 强组合压力：极快采样、强宽高比、粗网格和中段冻结，只记录边界。 |
| diagnostic_dropout_rate_stack | diagnostic | PASS | 74.006 | diagnostic | 34 / 1.79 | score_valid:score_valid | full_sequence_local_relation_segment:used | 较慢动作、核心手短空洞和粗手部坐标量化叠加，只记录边界。 |

## 结论

- 轻微组合扰动用于验证真实网页摄像头中多个小问题同时出现时，`花/跳` 仍能保持正常或边界以上得分。
- 强组合扰动是采集质量边界，当前仅作为诊断记录，不能替代真实 marker 后网页摄像头样本。

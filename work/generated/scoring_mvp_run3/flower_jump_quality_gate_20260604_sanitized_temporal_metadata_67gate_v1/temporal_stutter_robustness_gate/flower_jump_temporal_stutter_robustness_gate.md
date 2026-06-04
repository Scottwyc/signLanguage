# 花/跳时序帧冻结 stutter 鲁棒性门

- 生成时间：`2026-06-04T08:41:48`
- 总体：`PASS`
- 模板根目录：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义权重：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 门槛：正向短冻结最低分 `>= 70.0`；持续核心冻结需低分或进入 `needs_recapture, semantic_mismatch`。
- 口径：只读缓存 Holistic JSON，在固定长度骨架序列内合成重复/冻结帧，并重建 motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。

## 汇总

| 词条 | 状态 | 正向最低分 | 最弱正向 stutter | 持续冻结最高分 | 最强持续冻结 | 诊断最低分 | 最弱诊断边界 |
|---|---|---:|---|---:|---|---:|---|
| 花 | PASS | 93.869 | freeze_mid_15pct | 41.635 | freeze_mid_50pct_negative | 87.915 | freeze_mid_25pct_diagnostic |
| 跳 | PASS | 72.011 | freeze_mid_4f | 12.747 | freeze_mid_35pct_negative | 73.224 | freeze_mid_5f_diagnostic |

## 明细

### 花

| 变体 | 类型 | 状态 | 分数 | 阈值 | 帧段/稀疏 | quality | floor | 说明 |
|---|---|---|---:|---|---|---|---|---|
| freeze_mid_3f | positive | PASS | 99.115 | >= 70.0 | 25+3 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 中段短帧冻结 3 帧。 |
| freeze_mid_5f | positive | PASS | 97.315 | >= 70.0 | 24+5 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 中段短帧冻结 5 帧。 |
| freeze_mid_15pct | positive | PASS | 93.869 | >= 70.0 | 22+8 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 中段约 15% 短冻结。 |
| freeze_start_5f | positive | PASS | 100.000 | >= 70.0 | 0+5 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开头短冻结，核心开花动作仍在。 |
| freeze_end_5f | positive | PASS | 99.210 | >= 70.0 | 48+5 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 结尾短冻结，核心开花动作已完成。 |
| sparse_freeze_every_7th | positive | PASS | 97.350 | >= 70.0 | every=7, paired=False | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 每 7 帧一次微冻结。 |
| sparse_freeze_every_5th | positive | PASS | 94.182 | >= 70.0 | every=5, paired=False | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 每 5 帧一次微冻结。 |
| paired_sparse_freeze_every_7th | positive | PASS | 96.882 | >= 70.0 | every=7, paired=True | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 每 7 帧附近出现连续两帧微冻结。 |
| freeze_mid_25pct_diagnostic | diagnostic | PASS | 87.915 | diagnostic | 20+13 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 中段约 25% 冻结，只记录边界。 |
| freeze_mid_35pct_negative | negative | PASS | 39.622 | <= 45.0 或重采/语义失败 | 17+19 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 中段约 35% 核心动作冻结，应明显降分。 |
| freeze_mid_50pct_negative | negative | PASS | 41.635 | <= 45.0 或重采/语义失败 | 13+26 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 中段约 50% 核心动作冻结，应拒绝。 |
| freeze_full_negative | negative | PASS | 1.156 | <= 45.0 或重采/语义失败 | 0+53 | needs_recapture:flower_core_hand_presence_low | short_visible_core:query_not_short_core_capture | 全段静态冻结，缺少动态语义。 |

### 跳

| 变体 | 类型 | 状态 | 分数 | 阈值 | 帧段/稀疏 | quality | floor | 说明 |
|---|---|---|---:|---|---|---|---|---|
| freeze_mid_2f | positive | PASS | 94.959 | >= 70.0 | 8+2 | score_valid:score_valid | action_window_net:used | 弹跳中段短冻结 2 帧。 |
| freeze_mid_3f | positive | PASS | 87.813 | >= 70.0 | 8+3 | score_valid:score_valid | action_window_net:used | 弹跳中段短冻结 3 帧。 |
| freeze_mid_4f | positive | PASS | 72.011 | >= 70.0 | 7+4 | score_valid:score_valid | action_window_net:used | 短动作中段约 4 帧冻结，仍保留足够弹跳证据。 |
| freeze_start_2f | positive | PASS | 100.000 | >= 70.0 | 0+2 | score_valid:score_valid | action_window_net:used | 开头短冻结，弹跳主段仍在。 |
| freeze_end_2f | positive | PASS | 99.993 | >= 70.0 | 17+2 | score_valid:score_valid | action_window_net:used | 结尾短冻结，弹跳主段已完成。 |
| sparse_freeze_every_7th | positive | PASS | 73.884 | >= 70.0 | every=7, paired=False | score_valid:score_valid | full_sequence_local_relation_segment:used | 每 7 帧一次微冻结。 |
| sparse_freeze_every_5th | positive | PASS | 73.559 | >= 70.0 | every=5, paired=False | score_valid:score_valid | action_window_net:used | 每 5 帧一次微冻结。 |
| paired_sparse_freeze_every_7th | positive | PASS | 77.510 | >= 70.0 | every=7, paired=True | score_valid:score_valid | action_window_net:used | 每 7 帧附近出现连续两帧微冻结。 |
| freeze_mid_5f_diagnostic | diagnostic | PASS | 73.224 | diagnostic | 7+5 | score_valid:score_valid | action_window_net:used | 短动作中段约 5 帧冻结，记录边界。 |
| freeze_mid_35pct_negative | negative | PASS | 12.747 | <= 45.0 或重采/语义失败 | 6+7 | needs_recapture:jump_two_hand_presence_low | -:insufficient_two_hand_presence | 中段约 35% 弹跳核心冻结，应重采或明显降分。 |
| freeze_full_negative | negative | PASS | 0.211 | <= 45.0 或重采/语义失败 | 0+19 | needs_recapture:jump_two_hand_presence_low | -:insufficient_two_hand_presence | 全段静态冻结，缺少弹跳动态。 |

## 结论

- 短 burst 或稀疏微冻结用于验证浏览器摄像头偶发卡顿不会直接打崩正常动作。
- 持续核心动作冻结是重采边界，不能通过鲁棒性门把这种样本抬成正常高分。
- 该门仍是合成压力测试，不能替代正式 marker 后真实网页摄像头样本。

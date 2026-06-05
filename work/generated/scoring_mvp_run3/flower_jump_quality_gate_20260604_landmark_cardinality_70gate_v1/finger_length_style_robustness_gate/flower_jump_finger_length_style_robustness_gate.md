# 花/跳手指长度比例鲁棒性门

- 生成时间：`2026-06-04T14:02:07`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，剥离基础骨架组后从 MCP 锚点按比例缩放选定手指链长度，并重建 hand-shape、motion、two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：用户手指长短比例或伸展长度略有差异时，`花/跳` 保持可评分；强比例变化只记录诊断边界。

- 5080 状态：worker=`ready`，worker_pid=`811485`，reload_count=`26`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向比例 | 诊断最低分 | 最弱诊断比例 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 80.849 | right_opening_ring_pinky_length_1.12 | 79.378 | right_opening_all_finger_length_1.30_diagnostic | 70.000 |
| 跳 | PASS | 93.587 | right_person_index_middle_length_1.10 | 70.331 | right_person_index_middle_length_1.35_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 改动帧 | normalized_distance | alignment | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---:|---:|---|---|---|---|
| right_opening_all_finger_length_1.30_diagnostic | diagnostic | DIAG | 79.378 | diagnostic | 40 | 0.033487 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 开花手整体手指明显拉长，只记录诊断边界。 |
| right_opening_all_finger_length_0.75_diagnostic | diagnostic | DIAG | 79.677 | diagnostic | 40 | 0.032942 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 开花手整体手指明显缩短，只记录诊断边界。 |
| right_opening_ring_pinky_length_1.12 | positive | PASS | 80.849 | >= 70.0 | 40 | 0.030825 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 开花手无名指/小指略长，核心开花语义仍应保留。 |
| right_opening_all_finger_length_1.08 | positive | PASS | 80.886 | >= 70.0 | 40 | 0.030759 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 开花手整体手指长度略长，仍保留绽放语义。 |
| right_opening_all_finger_length_0.92 | positive | PASS | 80.904 | >= 70.0 | 40 | 0.030726 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 开花手整体手指长度略短，模拟用户手指比例差异。 |
| right_opening_index_middle_length_0.88 | positive | PASS | 81.122 | >= 70.0 | 40 | 0.030337 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 开花手食指/中指略短，覆盖局部手指比例变化。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | 0 | 0.000000 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 改动帧 | normalized_distance | alignment | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---:|---:|---|---|---|---|
| right_person_index_middle_length_1.35_diagnostic | diagnostic | DIAG | 70.331 | diagnostic | 17 | 0.125066 | semantic_action_window | score_valid | action_window_net | 两指小人明显拉长只记录诊断边界。 |
| right_person_index_middle_length_0.72_diagnostic | diagnostic | DIAG | 83.383 | diagnostic | 17 | 0.046087 | semantic_action_window | score_valid | action_window_net | 两指小人明显缩短只记录诊断边界。 |
| right_person_index_middle_length_1.10 | positive | PASS | 93.587 | >= 70.0 | 17 | 0.016806 | semantic_action_window | score_valid | action_window_net | 右手两指小人长度略长，仍保持跳跃语义。 |
| right_person_index_middle_length_0.90 | positive | PASS | 93.649 | >= 70.0 | 17 | 0.016641 | semantic_action_window | score_valid | action_window_net | 右手两指小人长度略短，双手关系和角色保持。 |
| left_ground_all_finger_length_1.15 | positive | PASS | 95.142 | >= 70.0 | 16 | 0.012533 | semantic_action_window | score_valid | action_window_net | 左手地面手指比例略长，手部位置和双手关系保持。 |
| right_nonsemantic_finger_length_0.85 | positive | PASS | 96.306 | >= 70.0 | 17 | 0.009198 | semantic_action_window | score_valid | action_window_net | 右手非语义手指略短，不应影响两指小人核心。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | 0 | 0.000000 | semantic_action_window | score_valid | action_window_net | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

## 说明

- 正向扰动只覆盖轻微手指长度/比例风格差异，并保持手部位置、弯曲方向和时序关系不变。
- 强比例变化不作为硬门，避免把真实手形语义错误推广为正常采集。
- 该门是合成鲁棒性压力测试，不能替代真实网页摄像头样本。

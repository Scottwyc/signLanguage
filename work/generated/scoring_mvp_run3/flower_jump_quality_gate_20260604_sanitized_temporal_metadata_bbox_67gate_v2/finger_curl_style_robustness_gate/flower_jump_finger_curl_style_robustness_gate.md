# 花/跳手指弯曲风格鲁棒性门

- 生成时间：`2026-06-04T09:54:48`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，剥离基础骨架组后将选定手指链向 MCP 锚点轻微弯曲，并重建 hand-shape、motion、two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：用户手指不完全伸直但语义动作仍正确时，`花/跳` 保持可评分；强弯曲只记录诊断边界。

- 5080 状态：worker=`ready`，worker_pid=`811485`，reload_count=`22`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向弯曲 | 诊断最低分 | 最弱诊断弯曲 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 80.887 | right_opening_ring_pinky_curl_0.16 | 79.541 | right_opening_all_fingers_curl_0.38_diagnostic | 70.000 |
| 跳 | PASS | 92.938 | right_person_index_middle_curl_0.16 | 82.206 | right_person_index_middle_curl_0.50_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 弯曲量 | 改动帧 | normalized_distance | alignment | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---:|---:|---:|---|---|---|---|
| right_opening_all_fingers_curl_0.38_diagnostic | diagnostic | DIAG | 79.541 | diagnostic | 0.38 | 40 | 0.033191 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 开花手强弯曲可能破坏开放手形，只作诊断。 |
| right_opening_all_fingers_curl_0.24_diagnostic | diagnostic | DIAG | 80.288 | diagnostic | 0.24 | 40 | 0.031834 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 开花手整体较强弯曲只记录诊断边界。 |
| right_opening_ring_pinky_curl_0.16 | positive | PASS | 80.887 | >= 70.0 | 0.16 | 40 | 0.030757 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 开花手无名指/小指轻微弯曲，核心开花语义仍应保留。 |
| right_opening_all_fingers_curl_0.10 | positive | PASS | 80.982 | >= 70.0 | 0.10 | 40 | 0.030586 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 开花手五指轻微弯曲，但仍保持绽放开合轨迹。 |
| right_opening_index_middle_curl_0.16 | positive | PASS | 81.167 | >= 70.0 | 0.16 | 40 | 0.030256 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 开花手食指/中指轻微弯曲，覆盖用户手指不完全伸直。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | 0.00 | 0 | 0.000000 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 弯曲量 | 改动帧 | normalized_distance | alignment | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---:|---:|---:|---|---|---|---|
| right_person_index_middle_curl_0.50_diagnostic | diagnostic | DIAG | 82.206 | diagnostic | 0.50 | 17 | 0.062319 | semantic_action_window | score_valid | action_window_net | 两指小人强弯曲可能破坏手形语义，只作诊断。 |
| right_person_index_middle_curl_0.32_diagnostic | diagnostic | DIAG | 86.430 | diagnostic | 0.32 | 17 | 0.037118 | semantic_action_window | score_valid | action_window_net | 两指小人明显弯曲只记录诊断边界。 |
| right_person_index_middle_curl_0.16 | positive | PASS | 92.938 | >= 70.0 | 0.16 | 17 | 0.018612 | semantic_action_window | score_valid | action_window_net | 右手两指小人中等轻微弯曲，覆盖用户两指不完全伸直。 |
| left_ground_all_fingers_curl_0.22 | positive | PASS | 94.827 | >= 70.0 | 0.22 | 16 | 0.013379 | semantic_action_window | score_valid | action_window_net | 左手地面手指弯曲风格变化，手部位置和双手关系保持。 |
| right_person_index_middle_curl_0.10 | positive | PASS | 95.518 | >= 70.0 | 0.10 | 17 | 0.011648 | semantic_action_window | score_valid | action_window_net | 右手两指小人轻微弯曲，但仍保持跳跃角色和双手关系。 |
| right_nonsemantic_fingers_curl_0.22 | positive | PASS | 95.895 | >= 70.0 | 0.22 | 17 | 0.010128 | semantic_action_window | score_valid | action_window_net | 右手非语义手指弯曲不应影响两指小人核心。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | 0.00 | 0 | 0.000000 | semantic_action_window | score_valid | action_window_net | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

## 说明

- 正向扰动只覆盖轻微手指弯曲风格差异，并保持手部位置、时序和核心动作关系不变。
- 强弯曲不作为硬门，避免把真实手形语义错误推广为正常采集。
- 该门是合成鲁棒性压力测试，不能替代真实网页摄像头样本。

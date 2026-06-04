# 花/跳取景尺度与轻微旋转鲁棒性门

- 生成时间：`2026-06-03T21:41:00`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，在骨架坐标层面模拟整人 zoom、轻微旋转和画面偏移；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：用户离镜头略远/略近、画面偏移或轻微倾斜时，`花/跳` 核心语义仍保持可评分。

- 5080 状态：worker=`ready`，worker_pid=`811485`，reload_count=`15`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向取景扰动 | 诊断最低分 | 最弱诊断扰动 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 79.448 | global_zoom_out_0.75 | 77.954 | extreme_zoom_out_0.60_diag | 70.000 |
| 跳 | PASS | 70.708 | framing_shift_zoom_out | 70.509 | extreme_zoom_out_0.60_diag | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | normalized_distance | alignment | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---:|---|---|---|---|
| extreme_zoom_out_0.60_diag | diagnostic | DIAG | 77.954 | diagnostic | 0.036112 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 极端远距离和偏移，只记录诊断，不作为通过条件。 |
| extreme_zoom_in_1.40_diag | diagnostic | DIAG | 78.899 | diagnostic | 0.034365 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 极端近距离和偏移，只记录诊断，不作为通过条件。 |
| global_zoom_out_0.75 | positive | PASS | 79.448 | >= 70.0 | 0.033360 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 用户离镜头更远，整人骨架约缩小到 75%。 |
| global_zoom_in_1.25 | positive | PASS | 79.771 | >= 70.0 | 0.032771 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 用户离镜头更近，整人骨架约放大到 125%。 |
| hand_region_zoom_out_0.82 | positive | PASS | 80.061 | >= 70.0 | 0.032245 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 手部区域因取景略远而缩小。 |
| hand_region_zoom_in_1.18 | positive | PASS | 80.211 | >= 70.0 | 0.031975 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 手部区域因取景略近而放大。 |
| framing_shift_zoom_out | positive | PASS | 80.553 | >= 70.0 | 0.031357 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 画面偏左下且略远。 |
| framing_shift_zoom_in | positive | PASS | 80.606 | >= 70.0 | 0.031261 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 画面偏右上且略近。 |
| global_rotate_8deg | positive | PASS | 81.346 | >= 70.0 | 0.029937 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 摄像头或身体轻微倾斜约 8 度。 |
| self | positive | PASS | 100.000 | >= 95.0 | 0.000000 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 同一骨架重算基线。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | normalized_distance | alignment | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---:|---|---|---|---|
| extreme_zoom_out_0.60_diag | diagnostic | DIAG | 70.509 | diagnostic | 0.141027 | semantic_action_window | score_valid | action_window_net | 极端远距离和偏移，只记录诊断，不作为通过条件。 |
| extreme_zoom_in_1.40_diag | diagnostic | DIAG | 83.012 | diagnostic | 0.042592 | semantic_action_window | score_valid | action_window_net | 极端近距离和偏移，只记录诊断，不作为通过条件。 |
| framing_shift_zoom_out | positive | PASS | 70.708 | >= 70.0 | 0.090787 | semantic_action_window | score_valid | action_window_net | 画面偏左下且略远。 |
| global_zoom_out_0.75 | positive | PASS | 70.936 | >= 70.0 | 0.102910 | semantic_action_window | score_valid | action_window_net | 用户离镜头更远，整人骨架约缩小到 75%。 |
| hand_region_zoom_out_0.82 | positive | PASS | 74.999 | >= 70.0 | 0.068016 | semantic_action_window | score_valid | action_window_net | 手部区域因取景略远而缩小。 |
| global_zoom_in_1.25 | positive | PASS | 90.199 | >= 70.0 | 0.023056 | semantic_action_window | score_valid | action_window_net | 用户离镜头更近，整人骨架约放大到 125%。 |
| hand_region_zoom_in_1.18 | positive | PASS | 92.776 | >= 70.0 | 0.016720 | semantic_action_window | score_valid | action_window_net | 手部区域因取景略近而放大。 |
| framing_shift_zoom_in | positive | PASS | 93.128 | >= 70.0 | 0.016554 | semantic_action_window | score_valid | action_window_net | 画面偏右上且略近。 |
| global_rotate_8deg | positive | PASS | 95.788 | >= 70.0 | 0.010911 | semantic_action_window | score_valid | action_window_net | 摄像头或身体轻微倾斜约 8 度。 |
| self | positive | PASS | 100.000 | >= 95.0 | 0.000000 | semantic_action_window | score_valid | action_window_net | 同一骨架重算基线。 |

## 说明

- 正向扰动覆盖轻中度取景变化；极端 zoom/pan 只作为诊断，不替代真实网页摄像头样本。
- 若该门失败，优先检查全局坐标是否重新主导了手部局部几何、two-hand relation 或语义 floor。

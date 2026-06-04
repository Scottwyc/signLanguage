# 花/跳手形局部尺度鲁棒性门

- 生成时间：`2026-06-04T06:10:04`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，在手部局部坐标层面缩放/拉伸并重算 `left_hand_shape/right_hand_shape`；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：不同用户手掌大小、手离镜头远近或轻微透视变化时，`花/跳` 核心手形仍保持可评分；极端形变只记录诊断边界。

- 5080 状态：worker=`ready`，worker_pid=`811485`，reload_count=`18`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向手形尺度 | 诊断最低分 | 最弱诊断尺度 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 80.339 | right_hand_aspect_x0.85_y1.20 | 76.902 | both_hands_aspect_x0.55_y1.60_diagnostic | 70.000 |
| 跳 | PASS | 86.403 | right_hand_aspect_x0.85_y1.20 | 69.697 | both_hands_uniform_scale_0.55_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | normalized_distance | alignment | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---:|---|---|---|---|
| both_hands_aspect_x0.55_y1.60_diagnostic | diagnostic | DIAG | 76.902 | diagnostic | 0.038083 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 强反向透视形变，只记录诊断边界。 |
| both_hands_aspect_x1.60_y0.55_diagnostic | diagnostic | DIAG | 80.021 | diagnostic | 0.032318 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 强透视形变，只记录诊断边界。 |
| both_hands_uniform_scale_1.60_diagnostic | diagnostic | DIAG | 80.435 | diagnostic | 0.031569 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 极端手部放大，只记录诊断边界。 |
| both_hands_uniform_scale_0.55_diagnostic | diagnostic | DIAG | 80.959 | diagnostic | 0.030628 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 极端手部缩小，只记录诊断边界。 |
| right_hand_aspect_x0.85_y1.20 | positive | PASS | 80.339 | >= 70.0 | 0.031743 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 右手核心手形轻微反向透视变化。 |
| both_hands_aspect_x0.90_y1.15 | positive | PASS | 80.691 | >= 70.0 | 0.031109 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 轻微横向压缩/纵向拉长，模拟手掌角度或透视变化。 |
| right_hand_aspect_x1.20_y0.85 | positive | PASS | 80.836 | >= 70.0 | 0.030849 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 右手核心手形轻微透视变化。 |
| both_hands_uniform_scale_1.30 | positive | PASS | 80.970 | >= 70.0 | 0.030608 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 双手局部大小放大到 130%，并重算 hand-shape。 |
| both_hands_aspect_x1.15_y0.90 | positive | PASS | 80.984 | >= 70.0 | 0.030583 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 轻微横向拉宽/纵向压缩，模拟手掌角度或透视变化。 |
| both_hands_uniform_scale_0.75 | positive | PASS | 81.141 | >= 70.0 | 0.030302 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 双手局部大小缩小到 75%，并重算 hand-shape。 |
| self | positive | PASS | 100.000 | >= 95.0 | 0.000000 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 同一骨架重算基线。 |
| left_hand_uniform_scale_0.80 | positive | PASS | 100.000 | >= 70.0 | 0.000000 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 左手局部大小略小；对跳的地面手和花的非核心手都不应破坏评分。 |
| left_hand_uniform_scale_1.25 | positive | PASS | 100.000 | >= 70.0 | 0.000000 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 左手局部大小略大；对跳的地面手和花的非核心手都不应破坏评分。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | normalized_distance | alignment | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---:|---|---|---|---|
| both_hands_uniform_scale_0.55_diagnostic | diagnostic | DIAG | 69.697 | diagnostic | 0.107647 | semantic_action_window | score_valid | action_window_net | 极端手部缩小，只记录诊断边界。 |
| both_hands_aspect_x0.55_y1.60_diagnostic | diagnostic | DIAG | 81.526 | diagnostic | 0.146407 | semantic_action_window | score_valid | action_window_net | 强反向透视形变，只记录诊断边界。 |
| both_hands_aspect_x1.60_y0.55_diagnostic | diagnostic | DIAG | 81.907 | diagnostic | 0.109363 | semantic_action_window | score_valid | action_window_net | 强透视形变，只记录诊断边界。 |
| both_hands_uniform_scale_1.60_diagnostic | diagnostic | DIAG | 86.431 | diagnostic | 0.035990 | semantic_action_window | score_valid | action_window_net | 极端手部放大，只记录诊断边界。 |
| right_hand_aspect_x0.85_y1.20 | positive | PASS | 86.403 | >= 70.0 | 0.036728 | semantic_action_window | score_valid | action_window_net | 右手核心手形轻微反向透视变化。 |
| right_hand_aspect_x1.20_y0.85 | positive | PASS | 88.359 | >= 70.0 | 0.031283 | semantic_action_window | score_valid | action_window_net | 右手核心手形轻微透视变化。 |
| both_hands_aspect_x0.90_y1.15 | positive | PASS | 89.071 | >= 70.0 | 0.028982 | semantic_action_window | score_valid | action_window_net | 轻微横向压缩/纵向拉长，模拟手掌角度或透视变化。 |
| both_hands_aspect_x1.15_y0.90 | positive | PASS | 89.859 | >= 70.0 | 0.026947 | semantic_action_window | score_valid | action_window_net | 轻微横向拉宽/纵向压缩，模拟手掌角度或透视变化。 |
| both_hands_uniform_scale_1.30 | positive | PASS | 93.506 | >= 70.0 | 0.016328 | semantic_action_window | score_valid | action_window_net | 双手局部大小放大到 130%，并重算 hand-shape。 |
| both_hands_uniform_scale_0.75 | positive | PASS | 94.028 | >= 70.0 | 0.015270 | semantic_action_window | score_valid | action_window_net | 双手局部大小缩小到 75%，并重算 hand-shape。 |
| left_hand_uniform_scale_1.25 | positive | PASS | 97.596 | >= 70.0 | 0.005976 | semantic_action_window | score_valid | action_window_net | 左手局部大小略大；对跳的地面手和花的非核心手都不应破坏评分。 |
| left_hand_uniform_scale_0.80 | positive | PASS | 97.904 | >= 70.0 | 0.005191 | semantic_action_window | score_valid | action_window_net | 左手局部大小略小；对跳的地面手和花的非核心手都不应破坏评分。 |
| self | positive | PASS | 100.000 | >= 95.0 | 0.000000 | semantic_action_window | score_valid | action_window_net | 同一骨架重算基线。 |

## 说明

- 正向扰动覆盖轻中度手掌大小和透视变化，并强制重算派生手形特征。
- 该门补足了旧 pose/framing 门只改 hand 坐标、不直接验证 hand-shape 派生特征的盲点。
- 该门是合成鲁棒性压力测试，不能替代真实网页摄像头样本。

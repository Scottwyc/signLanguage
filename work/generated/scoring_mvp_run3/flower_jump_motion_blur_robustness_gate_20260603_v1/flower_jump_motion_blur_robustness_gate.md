# 花/跳运动模糊与轨迹平滑鲁棒性门

- 生成时间：`2026-06-03T11:05:12`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，在基础骨架坐标层合成手部/全身轨迹低通、指数平滑和运动幅度变化；手部坐标变化后重算 `left_hand_shape/right_hand_shape`；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：轻度运动模糊、低帧率平滑和手部轨迹幅度轻微变化时，`花/跳` 仍保持正常或边界以上得分；重度平滑/幅度异常只作为诊断边界。

- 5080 状态：worker=`ready`，worker_pid=`811485`，reload_count=`13`，last_reload_error=`None`

## 结论

- 综合状态：`FAIL`

| 目标词 | 状态 | 正向最低分 | 最弱正向平滑/模糊 | 诊断最低分 | 最弱诊断平滑/模糊 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | FAIL | 30.905 | hand_motion_blur_5tap_light | 10.092 | hand_motion_blur_5tap_heavy_diagnostic | 70.000 |
| 跳 | PASS | 70.690 | all_keypoint_blur_3tap_light | 70.351 | hand_motion_amplitude_0.55_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | normalized_distance | alignment | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---:|---|---|---|---|
| hand_motion_blur_5tap_heavy_diagnostic | diagnostic | DIAG | 10.092 | diagnostic | 0.275216 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 更强手部轨迹低通，只记录诊断边界。 |
| hand_exponential_smooth_alpha_0.35_diagnostic | diagnostic | DIAG | 22.581 | diagnostic | 0.178568 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 强指数平滑会滞后并削弱动作相位，只记录诊断边界。 |
| hand_motion_amplitude_0.55_diagnostic | diagnostic | DIAG | 57.412 | diagnostic | 0.080463 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 手部运动幅度严重衰减，可能需要重采，只记录诊断边界。 |
| hand_motion_amplitude_1.60_diagnostic | diagnostic | DIAG | 64.230 | diagnostic | 0.064192 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 手部运动幅度过度放大，作为过度动作边界诊断。 |
| hand_motion_blur_5tap_light | positive | FAIL | 30.905 | >= 70.0 | 0.140912 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 手部轨迹轻度 5 帧低通，保留中心帧主导。 |
| hand_motion_blur_3tap | positive | FAIL | 32.995 | >= 70.0 | 0.133056 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 手部轨迹 3 帧轻度低通，模拟轻微运动模糊。 |
| all_keypoint_blur_3tap_light | positive | FAIL | 56.529 | >= 70.0 | 0.082710 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 全身关键点轻度 3 帧平滑，模拟浏览器/模型输出稳定化。 |
| hand_exponential_smooth_alpha_0.70 | positive | FAIL | 64.660 | >= 70.0 | 0.063224 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 手部轨迹轻度指数平滑，当前帧权重 0.70。 |
| hand_motion_amplitude_0.85 | positive | PASS | 79.074 | >= 70.0 | 0.034045 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 手部运动幅度轻微衰减到 85%，模拟运动模糊或保守动作。 |
| hand_motion_amplitude_1.15 | positive | PASS | 79.286 | >= 70.0 | 0.033655 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 手部运动幅度轻微增强到 115%，模拟动作更夸张或模型轨迹外扩。 |
| self | positive | PASS | 100.000 | >= 95.0 | 0.000000 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 同一骨架重算基线。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | normalized_distance | alignment | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---:|---|---|---|---|
| hand_motion_amplitude_0.55_diagnostic | diagnostic | DIAG | 70.351 | diagnostic | 0.154444 | semantic_action_window | score_valid | action_window_net | 手部运动幅度严重衰减，可能需要重采，只记录诊断边界。 |
| hand_motion_blur_5tap_heavy_diagnostic | diagnostic | DIAG | 71.480 | diagnostic | 0.251584 | semantic_action_window | score_valid | action_window_net | 更强手部轨迹低通，只记录诊断边界。 |
| hand_exponential_smooth_alpha_0.35_diagnostic | diagnostic | DIAG | 78.524 | diagnostic | 0.205107 | semantic_action_window | score_valid | full_sequence_local_relation_segment | 强指数平滑会滞后并削弱动作相位，只记录诊断边界。 |
| hand_motion_amplitude_1.60_diagnostic | diagnostic | DIAG | 81.428 | diagnostic | 0.072633 | semantic_action_window | score_valid | action_window_net | 手部运动幅度过度放大，作为过度动作边界诊断。 |
| all_keypoint_blur_3tap_light | positive | PASS | 70.690 | >= 70.0 | 0.086080 | semantic_action_window | score_valid | action_window_net | 全身关键点轻度 3 帧平滑，模拟浏览器/模型输出稳定化。 |
| hand_motion_blur_3tap | positive | PASS | 70.769 | >= 70.0 | 0.115014 | semantic_action_window | score_valid | action_window_net | 手部轨迹 3 帧轻度低通，模拟轻微运动模糊。 |
| hand_motion_blur_5tap_light | positive | PASS | 71.001 | >= 70.0 | 0.173283 | semantic_action_window | score_valid | action_window_net | 手部轨迹轻度 5 帧低通，保留中心帧主导。 |
| hand_motion_amplitude_0.85 | positive | PASS | 75.662 | >= 70.0 | 0.065004 | semantic_action_window | score_valid | action_window_net | 手部运动幅度轻微衰减到 85%，模拟运动模糊或保守动作。 |
| hand_exponential_smooth_alpha_0.70 | positive | PASS | 78.291 | >= 70.0 | 0.052772 | semantic_action_window | score_valid | full_sequence_local_relation_segment | 手部轨迹轻度指数平滑，当前帧权重 0.70。 |
| hand_motion_amplitude_1.15 | positive | PASS | 91.311 | >= 70.0 | 0.020023 | semantic_action_window | score_valid | action_window_net | 手部运动幅度轻微增强到 115%，模拟动作更夸张或模型轨迹外扩。 |
| self | positive | PASS | 100.000 | >= 95.0 | 0.000000 | semantic_action_window | score_valid | action_window_net | 同一骨架重算基线。 |

## 说明

- 正向变体覆盖轻度低通、轻度指数平滑和 15% 左右的手部运动幅度变化。
- 重度平滑或严重幅度压缩可能真实移除语义相位证据，因此只作为诊断，不作为正常采集通过条件。
- 该门是合成轨迹压力测试，不能替代正式网页摄像头样本。

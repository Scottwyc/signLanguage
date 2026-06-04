# 花/跳坐标精度鲁棒性门

- 生成时间：`2026-06-03T20:00:48`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，在骨架坐标层面做像素网格/归一化坐标量化；手部坐标量化后重算 `left_hand_shape/right_hand_shape`；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：常见浏览器摄像头分辨率、压缩和模型输出精度带来的坐标取整不应让 `花/跳` 掉到低分；过粗网格只作为诊断边界。

- 5080 状态：worker=`ready`，worker_pid=`811485`，reload_count=`14`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向精度扰动 | 诊断最低分 | 最弱诊断精度扰动 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 80.805 | hand_xy_quantize_1_128 | 78.075 | severe_hand_xy_quantize_1_32_diagnostic | 70.000 |
| 跳 | PASS | 96.833 | hand_xy_quantize_1_128 | 84.267 | severe_hand_xy_quantize_1_32_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | normalized_distance | alignment | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---:|---|---|---|---|
| severe_hand_xy_quantize_1_32_diagnostic | diagnostic | DIAG | 78.075 | diagnostic | 0.035888 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 手部核心坐标严重量化，会破坏手形细节，只记录诊断边界。 |
| coarse_xy_quantize_1_64_diagnostic | diagnostic | DIAG | 79.866 | diagnostic | 0.032599 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 过粗归一化 x/y 量化，只记录诊断边界。 |
| coarse_camera_grid_160x120_diagnostic | diagnostic | DIAG | 81.042 | diagnostic | 0.030480 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 过低分辨率网格，只记录诊断边界。 |
| hand_xy_quantize_1_128 | positive | PASS | 80.805 | >= 70.0 | 0.030904 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 只对手部做较粗 x/y 量化，并重算 hand-shape。 |
| xyz_quantize_1_256_offset_half | positive | PASS | 81.168 | >= 70.0 | 0.030254 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | x/y/z 同时按 1/256 网格量化，网格原点偏半格。 |
| normalized_xy_quantize_1_256 | positive | PASS | 81.183 | >= 70.0 | 0.030227 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 归一化 x/y 坐标约 1/256 精度。 |
| camera_grid_320x240 | positive | PASS | 81.257 | >= 70.0 | 0.030096 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 较低分辨率或强压缩后的 320x240 网格取整。 |
| camera_grid_640x480 | positive | PASS | 81.361 | >= 70.0 | 0.029909 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 常见网页摄像头/上传路径的 640x480 像素网格取整。 |
| normalized_xy_quantize_1_512 | positive | PASS | 81.428 | >= 70.0 | 0.029791 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 归一化 x/y 坐标约 1/512 精度。 |
| self | positive | PASS | 100.000 | >= 95.0 | 0.000000 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 同一骨架重算基线。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | normalized_distance | alignment | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---:|---|---|---|---|
| severe_hand_xy_quantize_1_32_diagnostic | diagnostic | DIAG | 84.267 | diagnostic | 0.039576 | semantic_action_window | score_valid | action_window_net | 手部核心坐标严重量化，会破坏手形细节，只记录诊断边界。 |
| coarse_xy_quantize_1_64_diagnostic | diagnostic | DIAG | 92.470 | diagnostic | 0.018341 | semantic_action_window | score_valid | action_window_net | 过粗归一化 x/y 量化，只记录诊断边界。 |
| coarse_camera_grid_160x120_diagnostic | diagnostic | DIAG | 97.253 | diagnostic | 0.006881 | semantic_action_window | score_valid | action_window_net | 过低分辨率网格，只记录诊断边界。 |
| hand_xy_quantize_1_128 | positive | PASS | 96.833 | >= 70.0 | 0.007834 | semantic_action_window | score_valid | action_window_net | 只对手部做较粗 x/y 量化，并重算 hand-shape。 |
| xyz_quantize_1_256_offset_half | positive | PASS | 98.273 | >= 70.0 | 0.004231 | semantic_action_window | score_valid | action_window_net | x/y/z 同时按 1/256 网格量化，网格原点偏半格。 |
| normalized_xy_quantize_1_256 | positive | PASS | 98.491 | >= 70.0 | 0.003673 | semantic_action_window | score_valid | action_window_net | 归一化 x/y 坐标约 1/256 精度。 |
| camera_grid_320x240 | positive | PASS | 98.540 | >= 70.0 | 0.003646 | semantic_action_window | score_valid | action_window_net | 较低分辨率或强压缩后的 320x240 网格取整。 |
| camera_grid_640x480 | positive | PASS | 99.214 | >= 70.0 | 0.001918 | semantic_action_window | score_valid | action_window_net | 常见网页摄像头/上传路径的 640x480 像素网格取整。 |
| normalized_xy_quantize_1_512 | positive | PASS | 99.215 | >= 70.0 | 0.001941 | semantic_action_window | score_valid | action_window_net | 归一化 x/y 坐标约 1/512 精度。 |
| self | positive | PASS | 100.000 | >= 95.0 | 0.000000 | semantic_action_window | score_valid | action_window_net | 同一骨架重算基线。 |

## 说明

- 正向变体覆盖正常网页摄像头和较低分辨率/压缩带来的坐标量化。
- 诊断变体表示极低分辨率或严重手部坐标取整，不能替代真实网页摄像头样本。

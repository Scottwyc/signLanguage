# 花/跳手部尺度时序呼吸鲁棒性门

- 生成时间：`2026-06-04T15:18:02`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，逐帧缩放手部局部坐标后重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：轻微平滑 hand-box breathing、少量帧级 scale/aspect flicker 仍保持可评分；强尖峰只记录诊断边界。

- 5080 状态：worker=`ready`，pid=`811485`，reload_count=`27`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向尺度呼吸 | 诊断最低分 | 最弱诊断尺度呼吸 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 81.932 | both_hands_smooth_aspect_breathing_0.10 | 81.395 | both_hands_strong_smooth_aspect_breathing_0.35_diagnostic | 70.000 |
| 跳 | PASS | 78.452 | both_hands_sparse_aspect_flicker_0.10_every_6f | 74.623 | both_hands_strong_smooth_uniform_breathing_0.35_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 手 | pattern | mode | amp | sx | sy | 改动帧 | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---|---|---:|---|---|---:|---|---|---|
| both_hands_strong_smooth_aspect_breathing_0.35_diagnostic | diagnostic | DIAG | 81.395 | diagnostic | `["left_hand", "right_hand"]` | smooth | aspect_xy | 0.350 | 0.650-1.350 | 0.650-1.350 | 50 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 双手 x/y 尺度反向平滑漂移 35% 属于强透视边界，只记录诊断分数。 |
| both_hands_strong_smooth_uniform_breathing_0.35_diagnostic | diagnostic | DIAG | 81.770 | diagnostic | `["left_hand", "right_hand"]` | smooth | uniform_xy | 0.350 | 0.650-1.350 | 0.650-1.350 | 50 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 双手平滑尺度呼吸 35% 属于强边界，只记录诊断分数。 |
| both_hands_sparse_aspect_spike_0.45_every_4f_diagnostic | diagnostic | DIAG | 88.176 | diagnostic | `["left_hand", "right_hand"]` | sparse | aspect_xy | 0.450 | 0.550-1.450 | 0.550-1.450 | 13 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 双手少量帧宽高强尖峰属于 detector 严重不稳定，只记录诊断分数。 |
| right_hand_sparse_scale_spike_0.45_every_4f_diagnostic | diagnostic | DIAG | 95.723 | diagnostic | `["right_hand"]` | sparse | uniform_xy | 0.450 | 0.550-1.450 | 0.550-1.450 | 13 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 右手少量帧尺度正负 45% 尖峰不是正常轻微抖动，只记录诊断分数。 |
| both_hands_smooth_aspect_breathing_0.10 | positive | PASS | 81.932 | >= 70.0 | `["left_hand", "right_hand"]` | smooth | aspect_xy | 0.100 | 0.900-1.100 | 0.900-1.100 | 50 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 双手局部 x/y 尺度反向平滑漂移 10%，模拟透视和检测框宽高抖动。 |
| right_hand_smooth_uniform_breathing_0.12 | positive | PASS | 82.052 | >= 70.0 | `["right_hand"]` | smooth | uniform_xy | 0.120 | 0.880-1.120 | 0.880-1.120 | 50 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 右手核心手局部检测框平滑呼吸 12%，不应破坏花开或跳跃核心证据。 |
| both_hands_smooth_uniform_breathing_0.10 | positive | PASS | 82.077 | >= 70.0 | `["left_hand", "right_hand"]` | smooth | uniform_xy | 0.100 | 0.900-1.100 | 0.900-1.100 | 50 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 双手局部检测框随时间平滑放大/缩小 10%，模拟 detector box breathing。 |
| both_hands_sparse_aspect_flicker_0.10_every_6f | positive | PASS | 98.078 | >= 70.0 | `["left_hand", "right_hand"]` | sparse | aspect_xy | 0.100 | 0.900-1.100 | 0.900-1.100 | 9 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 双手少量帧 x/y 宽高反向 flicker 10%，模拟网页上传帧中的检测框宽高抖动。 |
| right_hand_sparse_scale_flicker_0.12_every_5f | positive | PASS | 98.490 | >= 70.0 | `["right_hand"]` | sparse | uniform_xy | 0.120 | 0.880-1.120 | 0.880-1.120 | 10 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 少量帧右手局部尺度正负 12% 尖峰，模拟短时 detector scale flicker。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | `["left_hand", "right_hand"]` | none | uniform_xy | 0.000 | 1.000-1.000 | 1.000-1.000 | 0 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |
| left_hand_sparse_scale_flicker_0.12_every_5f | positive | PASS | 100.000 | >= 70.0 | `["left_hand"]` | sparse | uniform_xy | 0.120 | 0.880-1.120 | 0.880-1.120 | 10 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 少量帧左手局部尺度正负 12% 尖峰，覆盖跳的地面手和花的非核心手。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 手 | pattern | mode | amp | sx | sy | 改动帧 | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---|---|---:|---|---|---:|---|---|---|
| both_hands_strong_smooth_uniform_breathing_0.35_diagnostic | diagnostic | DIAG | 74.623 | diagnostic | `["left_hand", "right_hand"]` | smooth | uniform_xy | 0.350 | 0.655-1.345 | 0.655-1.345 | 16 | score_valid:score_valid | full_sequence_local_relation_segment:used | 双手平滑尺度呼吸 35% 属于强边界，只记录诊断分数。 |
| both_hands_strong_smooth_aspect_breathing_0.35_diagnostic | diagnostic | DIAG | 83.607 | diagnostic | `["left_hand", "right_hand"]` | smooth | aspect_xy | 0.350 | 0.655-1.345 | 0.655-1.345 | 16 | score_valid:score_valid | action_window_net:used | 双手 x/y 尺度反向平滑漂移 35% 属于强透视边界，只记录诊断分数。 |
| both_hands_sparse_aspect_spike_0.45_every_4f_diagnostic | diagnostic | DIAG | 84.394 | diagnostic | `["left_hand", "right_hand"]` | sparse | aspect_xy | 0.450 | 0.550-1.450 | 0.550-1.450 | 4 | score_valid:score_valid | action_window_net:used | 双手少量帧宽高强尖峰属于 detector 严重不稳定，只记录诊断分数。 |
| right_hand_sparse_scale_spike_0.45_every_4f_diagnostic | diagnostic | DIAG | 95.007 | diagnostic | `["right_hand"]` | sparse | uniform_xy | 0.450 | 0.550-1.450 | 0.550-1.450 | 4 | score_valid:score_valid | action_window_net:used | 右手少量帧尺度正负 45% 尖峰不是正常轻微抖动，只记录诊断分数。 |
| both_hands_sparse_aspect_flicker_0.10_every_6f | positive | PASS | 78.452 | >= 70.0 | `["left_hand", "right_hand"]` | sparse | aspect_xy | 0.100 | 0.900-1.100 | 0.900-1.100 | 3 | score_valid:score_valid | action_window_net:used | 双手少量帧 x/y 宽高反向 flicker 10%，模拟网页上传帧中的检测框宽高抖动。 |
| both_hands_smooth_aspect_breathing_0.10 | positive | PASS | 94.622 | >= 70.0 | `["left_hand", "right_hand"]` | smooth | aspect_xy | 0.100 | 0.902-1.098 | 0.902-1.098 | 16 | score_valid:score_valid | action_window_net:used | 双手局部 x/y 尺度反向平滑漂移 10%，模拟透视和检测框宽高抖动。 |
| both_hands_smooth_uniform_breathing_0.10 | positive | PASS | 97.407 | >= 70.0 | `["left_hand", "right_hand"]` | smooth | uniform_xy | 0.100 | 0.902-1.098 | 0.902-1.098 | 16 | score_valid:score_valid | action_window_net:used | 双手局部检测框随时间平滑放大/缩小 10%，模拟 detector box breathing。 |
| right_hand_smooth_uniform_breathing_0.12 | positive | PASS | 97.866 | >= 70.0 | `["right_hand"]` | smooth | uniform_xy | 0.120 | 0.882-1.118 | 0.882-1.118 | 16 | score_valid:score_valid | action_window_net:used | 右手核心手局部检测框平滑呼吸 12%，不应破坏花开或跳跃核心证据。 |
| right_hand_sparse_scale_flicker_0.12_every_5f | positive | PASS | 99.255 | >= 70.0 | `["right_hand"]` | sparse | uniform_xy | 0.120 | 0.880-1.120 | 0.880-1.120 | 4 | score_valid:score_valid | action_window_net:used | 少量帧右手局部尺度正负 12% 尖峰，模拟短时 detector scale flicker。 |
| left_hand_sparse_scale_flicker_0.12_every_5f | positive | PASS | 99.398 | >= 70.0 | `["left_hand"]` | sparse | uniform_xy | 0.120 | 0.880-1.120 | 0.880-1.120 | 4 | score_valid:score_valid | action_window_net:used | 少量帧左手局部尺度正负 12% 尖峰，覆盖跳的地面手和花的非核心手。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | `["left_hand", "right_hand"]` | none | uniform_xy | 0.000 | 1.000-1.000 | 1.000-1.000 | 0 | score_valid:score_valid | action_window_net:used | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

## 说明

- 该门补充的是时间维度的 hand detector 尺度漂移，不替代静态 hand-shape scale、perspective/shear 或 landmark-noise 门。
- 正向变体只覆盖 10%-12% 的平滑或稀疏尺度变化，强 35%-45% 漂移/尖峰不是正常网页采集要求。
- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。

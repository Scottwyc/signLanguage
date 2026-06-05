# 花/跳 frame_weights 鲁棒性门

- 生成时间：`2026-06-04T12:20:34`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，只修改 query 的 `frame_weight`，不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：浏览器上传 motion 权重、轻微权重噪声/错位、宽泛前后段加权、无非均匀权重或异常上传权重被清洗后，`花/跳` 仍保持正常或边界以上得分；反向 motion 权重仅作为坏上传先验诊断。

- 5080 状态：worker=`ready`，worker_pid=`811485`，reload_count=`25`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向权重 | 诊断最低分 | 最弱诊断权重 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 99.161 | back_loaded_broad_emphasis | 99.347 | inverted_dynamic_diagnostic | 70.000 |
| 跳 | PASS | 76.297 | back_loaded_broad_emphasis | 10.120 | inverted_dynamic_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 上传权重范围 | 异常权重 | 评分权重范围 | 输出有限 | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---|---|---|---|---|---|
| inverted_dynamic_diagnostic | diagnostic | DIAG | 99.347 | diagnostic | 0.350-1.315 | nonfinite=0, nonpositive=0, extreme=0 | 0.998-1.068 | yes | score_valid | short_visible_core | 反向 motion 权重是坏上传先验，只记录诊断边界。 |
| back_loaded_broad_emphasis | positive | PASS | 99.161 | >= 70.0 | 0.349-1.719 | nonfinite=0, nonpositive=0, extreme=0 | 0.488-1.569 | yes | score_valid | short_visible_core | 浏览器权重略偏向动作后段，但不是极端尖峰。 |
| front_loaded_broad_emphasis | positive | PASS | 99.282 | >= 70.0 | 0.349-1.719 | nonfinite=0, nonpositive=0, extreme=0 | 0.482-1.843 | yes | score_valid | short_visible_core | 浏览器权重略偏向动作前段，但不是极端尖峰。 |
| malformed_sparse_sanitized | positive | PASS | 99.548 | >= 70.0 | -5.000-1000000000.000 | nonfinite=3, nonpositive=2, extreme=1 | 0.486-2.512 | yes | score_valid | short_visible_core | 稀疏 NaN/Inf/负数/零/极大上传权重应被清洗成安全权重，不污染评分。 |
| semantic_dynamic_shift_backward_1 | positive | PASS | 99.570 | >= 70.0 | 0.597-2.568 | nonfinite=0, nonpositive=0, extreme=0 | 0.599-2.407 | yes | score_valid | short_visible_core | 上传权重相对骨架轻微提前一帧。 |
| center_gaussian_emphasis | positive | PASS | 99.617 | >= 70.0 | 0.350-1.860 | nonfinite=0, nonpositive=0, extreme=0 | 0.472-2.114 | yes | score_valid | short_visible_core | 浏览器把中段高运动区域整体加权。 |
| semantic_dynamic_noisy_15pct | positive | PASS | 99.747 | >= 70.0 | 0.512-2.847 | nonfinite=0, nonpositive=0, extreme=0 | 0.554-2.711 | yes | score_valid | short_visible_core | 浏览器 motion 权重有约 15% 乘性噪声。 |
| single_extreme_spike_sanitized | positive | PASS | 99.818 | >= 70.0 | 1.000-999999995904.000 | nonfinite=0, nonpositive=0, extreme=1 | 0.786-2.252 | yes | score_valid | short_visible_core | 单帧极大上传权重应被上限裁剪并重新归一化，不让一帧主导评分。 |
| semantic_dynamic_motion_weights | positive | PASS | 99.870 | >= 70.0 | 0.597-2.568 | nonfinite=0, nonpositive=0, extreme=0 | 0.597-2.568 | yes | score_valid | short_visible_core | 按当前语义 motion energy 生成的浏览器式权重。 |
| uniform_1.0 | positive | PASS | 99.870 | >= 70.0 | 1.000-1.000 | nonfinite=0, nonpositive=0, extreme=0 | 0.802-1.663 | yes | score_valid | short_visible_core | 浏览器未提供有效非均匀权重时，完整骨架仍应可评分。 |
| all_invalid_fallback | positive | PASS | 99.870 | >= 70.0 | --- | nonfinite=53, nonpositive=0, extreme=0 | 0.802-1.663 | yes | score_valid | short_visible_core | 整段上传权重不可用时，应回退到语义动态权重/均匀安全先验而不是失败。 |
| semantic_dynamic_shift_forward_1 | positive | PASS | 99.984 | >= 70.0 | 0.597-2.568 | nonfinite=0, nonpositive=0, extreme=0 | 0.599-2.407 | yes | score_valid | short_visible_core | 上传权重相对骨架轻微错后一帧。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 上传权重范围 | 异常权重 | 评分权重范围 | 输出有限 | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---|---|---|---|---|---|
| inverted_dynamic_diagnostic | diagnostic | DIAG | 10.120 | diagnostic | 0.540-1.413 | nonfinite=0, nonpositive=0, extreme=0 | 0.933-1.050 | yes | needs_recapture | - | 反向 motion 权重是坏上传先验，只记录诊断边界。 |
| back_loaded_broad_emphasis | positive | PASS | 76.297 | >= 70.0 | 0.349-1.716 | nonfinite=0, nonpositive=0, extreme=0 | 0.522-1.246 | yes | score_valid | action_window_net | 浏览器权重略偏向动作后段，但不是极端尖峰。 |
| single_extreme_spike_sanitized | positive | PASS | 77.723 | >= 70.0 | 1.000-999999995904.000 | nonfinite=0, nonpositive=0, extreme=1 | 0.795-2.366 | yes | score_valid | action_window_net | 单帧极大上传权重应被上限裁剪并重新归一化，不让一帧主导评分。 |
| semantic_dynamic_shift_forward_1 | positive | PASS | 77.880 | >= 70.0 | 0.631-1.650 | nonfinite=0, nonpositive=0, extreme=0 | 0.672-1.538 | yes | score_valid | action_window_net | 上传权重相对骨架轻微错后一帧。 |
| uniform_1.0 | positive | PASS | 78.072 | >= 70.0 | 1.000-1.000 | nonfinite=0, nonpositive=0, extreme=0 | 0.851-1.253 | yes | score_valid | action_window_net | 浏览器未提供有效非均匀权重时，完整骨架仍应可评分。 |
| all_invalid_fallback | positive | PASS | 78.072 | >= 70.0 | --- | nonfinite=19, nonpositive=0, extreme=0 | 0.851-1.253 | yes | score_valid | action_window_net | 整段上传权重不可用时，应回退到语义动态权重/均匀安全先验而不是失败。 |
| semantic_dynamic_shift_backward_1 | positive | PASS | 78.545 | >= 70.0 | 0.631-1.650 | nonfinite=0, nonpositive=0, extreme=0 | 0.674-1.488 | yes | score_valid | full_sequence_local_relation_segment | 上传权重相对骨架轻微提前一帧。 |
| front_loaded_broad_emphasis | positive | PASS | 79.217 | >= 70.0 | 0.349-1.716 | nonfinite=0, nonpositive=0, extreme=0 | 0.510-1.500 | yes | score_valid | full_sequence_local_relation_segment | 浏览器权重略偏向动作前段，但不是极端尖峰。 |
| malformed_sparse_sanitized | positive | PASS | 90.120 | >= 70.0 | -5.000-1000000000.000 | nonfinite=3, nonpositive=2, extreme=1 | 0.668-2.068 | yes | score_valid | action_window_net | 稀疏 NaN/Inf/负数/零/极大上传权重应被清洗成安全权重，不污染评分。 |
| center_gaussian_emphasis | positive | PASS | 91.997 | >= 70.0 | 0.350-1.860 | nonfinite=0, nonpositive=0, extreme=0 | 0.510-1.702 | yes | score_valid | action_window_net | 浏览器把中段高运动区域整体加权。 |
| semantic_dynamic_noisy_15pct | positive | PASS | 99.962 | >= 70.0 | 0.516-1.477 | nonfinite=0, nonpositive=0, extreme=0 | 0.606-1.502 | yes | score_valid | action_window_net | 浏览器 motion 权重有约 15% 乘性噪声。 |
| semantic_dynamic_motion_weights | positive | PASS | 99.985 | >= 70.0 | 0.631-1.650 | nonfinite=0, nonpositive=0, extreme=0 | 0.669-1.593 | yes | score_valid | action_window_net | 按当前语义 motion energy 生成的浏览器式权重。 |

## 说明

- 正向变体覆盖真实网页 motion 权重、常见轻微错位/噪声和异常上传权重清洗。
- `inverted_dynamic_diagnostic` 是坏上传先验诊断，不代表正常浏览器行为。
- 该门是合成 frame_weights 压力测试，不能替代真实网页摄像头样本。

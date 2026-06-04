# 花/跳双手关系几何鲁棒性门

- 生成时间：`2026-06-04T08:48:47`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，调整右手相对左手的固定偏移、运动高度、横向分量和逐帧关系抖动，并重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：温和关系几何变化仍可正常评分；`跳` 的高度过小、强水平化、反向跳跃必须低分或进入重采/语义失败解释。

- 5080 状态：worker=`ready`，pid=`811485`，reload_count=`21`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向关系扰动 | 负向最高分 | 最强负向关系 | 诊断最低分 | 最弱诊断关系 | 门槛 |
|---|---|---:|---|---:|---|---:|---|---:|
| 花 | PASS | 79.772 | right_relation_jitter_0.035 | - | - | 79.250 | flower_relation_reverse_y_diagnostic | 70.000 |
| 跳 | PASS | 70.469 | right_relation_offset_x_0.15 | 93.960 | jump_relation_y_amplitude_0.45_negative | 74.458 | right_relation_y_amplitude_1.75_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | offset | y_amp | x_from_y | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---:|---:|---|---|---|
| flower_relation_reverse_y_diagnostic | diagnostic | DIAG | 79.250 | diagnostic | 0.0,0.0,0.0 | - | 0.000 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 花不是双手关系核心词，反向关系轨迹只记录诊断边界。 |
| flower_relation_x_from_y_0.90_diagnostic | diagnostic | DIAG | 80.877 | diagnostic | 0.0,0.0,0.0 | - | 0.900 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 花不是双手关系核心词，强横向关系扰动只记录对右手开花主语义的边界。 |
| right_relation_y_amplitude_1.75_diagnostic | diagnostic | DIAG | 80.925 | diagnostic | 0.0,0.0,0.0 | 1.750 | 0.000 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 更大相对运动高度只记录边界，不作为通过条件。 |
| right_relation_jitter_0.035 | positive | PASS | 79.772 | >= 70.0 | 0.0,0.0,0.0 | - | 0.000 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 右手相对左手的逐帧关系有小幅抖动，模拟网页关键点不稳。 |
| right_relation_y_amplitude_1.35 | positive | PASS | 81.211 | >= 70.0 | 0.0,0.0,0.0 | 1.350 | 0.000 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 右手相对运动高度放大到 135%，仍应保持可评分。 |
| right_relation_x_from_y_0.35 | positive | PASS | 81.228 | >= 70.0 | 0.0,0.0,0.0 | - | 0.350 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 右手跳跃轨迹带轻微横向分量，垂直关系仍清晰。 |
| right_relation_y_amplitude_0.70 | positive | PASS | 81.252 | >= 70.0 | 0.0,0.0,0.0 | 0.700 | 0.000 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 右手相对运动高度缩小到 70%，仍应保持可评分。 |
| right_relation_offset_down_0.15 | positive | PASS | 81.457 | >= 70.0 | 0.0,0.15,0.0 | - | 0.000 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 右手整体相对左手略低，模拟手势位置差异。 |
| right_relation_offset_x_0.15 | positive | PASS | 81.457 | >= 70.0 | 0.15,0.0,0.0 | - | 0.000 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 右手整体横向间距略变，核心动作和手形仍保留。 |
| right_relation_offset_up_0.15 | positive | PASS | 81.457 | >= 70.0 | 0.0,-0.15,0.0 | - | 0.000 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 右手整体相对左手略高，模拟用户起手/镜头位置差异。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | 0.0,0.0,0.0 | - | 0.000 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 剥离基础组后重建 relation/motion 特征，应保持近满分。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | offset | y_amp | x_from_y | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---:|---:|---|---|---|
| right_relation_y_amplitude_1.75_diagnostic | diagnostic | DIAG | 74.458 | diagnostic | 0.0,0.0,0.0 | 1.750 | 0.000 | score_valid:score_valid | action_window_net:used | 更大相对运动高度只记录边界，不作为通过条件。 |
| jump_relation_x_from_y_0.90_negative | negative | PASS | 63.776 | <= 45.0 或重采/语义失败 | 0.0,0.0,0.0 | - | 0.900 | semantic_mismatch:relation_direction_mismatch | action_window_net:relation_direction_mismatch | 跳跃关系过度水平化，应低分或进入语义失败解释。 |
| jump_relation_reverse_y_negative | negative | PASS | 81.302 | <= 45.0 或重采/语义失败 | 0.0,0.0,0.0 | - | 0.000 | semantic_mismatch:relation_direction_mismatch | action_window_net:relation_direction_mismatch | 右手相对左手的跳跃方向反向，应低分或进入语义失败解释。 |
| jump_relation_y_amplitude_0.45_negative | negative | PASS | 93.960 | <= 45.0 或重采/语义失败 | 0.0,0.0,0.0 | 0.450 | 0.000 | semantic_mismatch:relation_jump_amplitude_too_small | action_window_net:relation_jump_amplitude_too_small | 跳跃相对高度过小，应低分或进入语义失败解释。 |
| right_relation_offset_x_0.15 | positive | PASS | 70.469 | >= 70.0 | 0.15,0.0,0.0 | - | 0.000 | score_valid:score_valid | action_window_net:used | 右手整体横向间距略变，核心动作和手形仍保留。 |
| right_relation_jitter_0.035 | positive | PASS | 76.554 | >= 70.0 | 0.0,0.0,0.0 | - | 0.000 | score_valid:score_valid | action_window_net:used | 右手相对左手的逐帧关系有小幅抖动，模拟网页关键点不稳。 |
| right_relation_x_from_y_0.35 | positive | PASS | 79.784 | >= 70.0 | 0.0,0.0,0.0 | - | 0.350 | score_valid:score_valid | full_sequence_local_relation_segment:used | 右手跳跃轨迹带轻微横向分量，垂直关系仍清晰。 |
| right_relation_offset_up_0.15 | positive | PASS | 90.202 | >= 70.0 | 0.0,-0.15,0.0 | - | 0.000 | score_valid:score_valid | action_window_net:used | 右手整体相对左手略高，模拟用户起手/镜头位置差异。 |
| right_relation_offset_down_0.15 | positive | PASS | 90.892 | >= 70.0 | 0.0,0.15,0.0 | - | 0.000 | score_valid:score_valid | action_window_net:used | 右手整体相对左手略低，模拟手势位置差异。 |
| right_relation_y_amplitude_1.35 | positive | PASS | 95.963 | >= 70.0 | 0.0,0.0,0.0 | 1.350 | 0.000 | score_valid:score_valid | action_window_net:used | 右手相对运动高度放大到 135%，仍应保持可评分。 |
| right_relation_y_amplitude_0.70 | positive | PASS | 96.549 | >= 70.0 | 0.0,0.0,0.0 | 0.700 | 0.000 | score_valid:score_valid | action_window_net:used | 右手相对运动高度缩小到 70%，仍应保持可评分。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | 0.0,0.0,0.0 | - | 0.000 | score_valid:score_valid | action_window_net:used | 剥离基础组后重建 relation/motion 特征，应保持近满分。 |

## 说明

- 正向门覆盖不同用户常见的右手位置、跳跃高度和轻微横向轨迹差异。
- `跳` 的负向关系门允许 capture_quality 证明语义失败，因为当前 score 值本身可能仍由其它相似证据托住。
- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。

# 花/跳非核心手与非语义手指干扰鲁棒性门

- 生成时间：`2026-06-03T21:50:58`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，在手部坐标层合成非核心手/非语义手指干扰并重建 hand-shape/motion/relation 特征；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：`花` 的非核心左手干扰不应拖低右手绽放；`跳` 的右手非语义手指干扰不应拖低左手地面+右手两指小人的核心语义。

- 5080 状态：worker=`ready`，pid=`811485`，reload_count=`15`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向干扰 | 诊断最低分 | 最弱诊断核心扰动 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 100.000 | self_recomputed | 25.938 | flower_right_opening_tips_collapse_diagnostic | 70.000 |
| 跳 | PASS | 73.032 | jump_right_noncore_fingers_motion_drift | 81.460 | jump_right_index_middle_collapse_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 操作组 | landmark | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---|---|---|---|
| flower_right_opening_tips_collapse_diagnostic | diagnostic | DIAG | 25.938 | diagnostic | right_hand | 4,8,12,16,20 | semantic_mismatch:flower_opening_guard_failed | short_visible_core:query_not_short_core_capture | 诊断记录：右手绽放指尖塌缩会触发 opening guard 或显著低分。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | - | - | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 剥离基础组后重建 motion/relation 特征，应保持近满分。 |
| flower_left_hand_shift_large | positive | PASS | 100.000 | >= 70.0 | left_hand | - | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 花的左手不是当前核心绽放手，大幅静态偏移不应拖低右手开花语义。 |
| flower_left_hand_jitter_0.18 | positive | PASS | 100.000 | >= 70.0 | left_hand | - | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 非核心左手 landmark 大幅抖动，模拟另一只手在画面内干扰。 |
| flower_left_hand_motion_drift | positive | PASS | 100.000 | >= 70.0 | left_hand | - | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 非核心左手出现连续漂移运动，不应遮蔽右手绽放主语义。 |
| flower_left_hand_shape_scramble | positive | PASS | 100.000 | >= 70.0 | left_hand | - | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 非核心左手手形结构异常，应被低权重路径吸收而不是拉低清晰右手动作。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 操作组 | landmark | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---|---|---|---|
| jump_right_index_middle_collapse_diagnostic | diagnostic | DIAG | 81.460 | diagnostic | right_hand | 5,6,7,8,9,10,11,12 | score_valid:score_valid | action_window_net:used | 诊断记录：右手食指/中指结构破坏的当前边界；硬负例由遮挡/裁切/相位门覆盖。 |
| jump_right_noncore_fingers_motion_drift | positive | PASS | 73.032 | >= 70.0 | right_hand | 1,2,3,4,13,14,15,16,17,18,19,20 | score_valid:score_valid | action_window_net:used | 非语义手指连续漂移，核心两指小人和左手地面仍应保持可评分。 |
| jump_right_noncore_fingers_jitter_0.12 | positive | PASS | 82.302 | >= 70.0 | right_hand | 1,2,3,4,13,14,15,16,17,18,19,20 | score_valid:score_valid | action_window_net:used | 跳的右手食指/中指小人保持稳定时，拇指/无名指/小指抖动不应破坏评分。 |
| jump_right_noncore_fingers_shift | positive | PASS | 82.302 | >= 70.0 | right_hand | 1,2,3,4,13,14,15,16,17,18,19,20 | score_valid:score_valid | action_window_net:used | 非语义手指整体偏移，模拟用户自然蜷曲或张开无关手指。 |
| jump_right_noncore_fingers_scramble | positive | PASS | 82.302 | >= 70.0 | right_hand | 1,2,3,4,13,14,15,16,17,18,19,20 | score_valid:score_valid | action_window_net:used | 非语义手指局部顺序异常，不能盖过右手食指/中指与左手地面的核心关系。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | - | - | score_valid:score_valid | action_window_net:used | 剥离基础组后重建 motion/relation 特征，应保持近满分。 |

## 说明

- 正向门只覆盖非核心手或非语义手指干扰，不会放宽 `花` 的右手绽放核心或 `跳` 的双手关系要求。
- 诊断行用于记录核心手形破坏的当前边界；正式负向保护仍由 fingertip-occlusion、edge-clipping、hand-role、phase-order 等已推广子门承担。
- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。

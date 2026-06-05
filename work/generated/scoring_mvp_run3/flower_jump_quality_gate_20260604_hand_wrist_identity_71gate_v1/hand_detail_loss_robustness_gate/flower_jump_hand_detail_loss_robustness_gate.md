# 花/跳手部细节损失鲁棒性门

- 生成时间：`2026-06-04T15:22:40`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，合成低分辨率/低细节下的手部内关节线性化后重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：低细节下保留手中心、MCP 和指尖范围时仍可正常评分；明显指尖塌缩只记录诊断边界。

- 5080 状态：worker=`ready`，pid=`811485`，reload_count=`27`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向细节损失 | 诊断最低分 | 最弱诊断边界 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 80.339 | flower_opening_right_inner_axis_smooth_0.60 | 77.727 | both_hands_tip_anchor_blend_0.38_diagnostic | 70.000 |
| 跳 | PASS | 77.234 | right_hand_inner_axis_smooth_0.45 | 79.899 | both_hands_tip_anchor_blend_0.38_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 改动帧 | 改动点 | 操作 | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---:|---:|---|---|---|---|
| both_hands_tip_anchor_blend_0.38_diagnostic | diagnostic | DIAG | 77.727 | diagnostic | 40 | 600 | tip_anchor_blend:['left_hand', 'right_hand']:['thumb', 'index', 'middle', 'ring', 'pinky']:0.38 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 双手强细节塌缩不代表正常网页低细节采集，只记录分数。 |
| flower_opening_right_tip_anchor_blend_0.30_diagnostic | diagnostic | DIAG | 78.493 | diagnostic | 40 | 600 | tip_anchor_blend:['right_hand']:['thumb', 'index', 'middle', 'ring', 'pinky']:0.3 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 花的绽放指尖明显向掌心塌缩可能破坏手形，只作为诊断边界。 |
| flower_opening_right_inner_axis_smooth_0.60 | positive | PASS | 80.339 | >= 70.0 | 40 | 400 | axis_smooth:['right_hand']:['thumb', 'index', 'middle', 'ring', 'pinky']:0.6 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 花的右手绽放手形保留指尖外展，只压低 PIP/DIP 细节。 |
| right_hand_inner_axis_smooth_0.45 | positive | PASS | 80.547 | >= 70.0 | 40 | 400 | axis_smooth:['right_hand']:['thumb', 'index', 'middle', 'ring', 'pinky']:0.45 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 右手内关节中等线性化，覆盖主导手局部细节损失但保留指尖伸展。 |
| both_hands_inner_axis_smooth_0.30 | positive | PASS | 80.846 | >= 70.0 | 40 | 400 | axis_smooth:['left_hand', 'right_hand']:['thumb', 'index', 'middle', 'ring', 'pinky']:0.3 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 双手内关节向 MCP-tip 轴轻微线性化，模拟低分辨率下细小关节弯折被平滑。 |
| sparse_both_hands_inner_axis_smooth_0.70_every_5f | positive | PASS | 97.872 | >= 70.0 | 8 | 80 | axis_smooth:['left_hand', 'right_hand']:['thumb', 'index', 'middle', 'ring', 'pinky']:0.7 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 每 5 帧一次较强内关节线性化，模拟偶发低细节关键帧。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | 0 | 0 | - | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 改动帧 | 改动点 | 操作 | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---:|---:|---|---|---|---|
| both_hands_tip_anchor_blend_0.38_diagnostic | diagnostic | DIAG | 79.899 | diagnostic | 18 | 495 | tip_anchor_blend:['left_hand', 'right_hand']:['thumb', 'index', 'middle', 'ring', 'pinky']:0.38 | score_valid:score_valid | action_window_net:used | 双手强细节塌缩不代表正常网页低细节采集，只记录分数。 |
| jump_right_person_tip_anchor_blend_0.32_diagnostic | diagnostic | DIAG | 82.203 | diagnostic | 17 | 102 | tip_anchor_blend:['right_hand']:['index', 'middle']:0.32 | score_valid:score_valid | action_window_net:used | 跳的右手小人两指明显向掌心塌缩可能改变手形，只作为诊断边界。 |
| right_hand_inner_axis_smooth_0.45 | positive | PASS | 77.234 | >= 70.0 | 17 | 170 | axis_smooth:['right_hand']:['thumb', 'index', 'middle', 'ring', 'pinky']:0.45 | score_valid:score_valid | action_window_net:used | 右手内关节中等线性化，覆盖主导手局部细节损失但保留指尖伸展。 |
| both_hands_inner_axis_smooth_0.30 | positive | PASS | 78.069 | >= 70.0 | 18 | 330 | axis_smooth:['left_hand', 'right_hand']:['thumb', 'index', 'middle', 'ring', 'pinky']:0.3 | score_valid:score_valid | action_window_net:used | 双手内关节向 MCP-tip 轴轻微线性化，模拟低分辨率下细小关节弯折被平滑。 |
| jump_right_person_index_middle_axis_smooth_0.65 | positive | PASS | 78.895 | >= 70.0 | 17 | 68 | axis_smooth:['right_hand']:['index', 'middle']:0.65 | score_valid:score_valid | action_window_net:used | 跳的右手小人两指保留指尖和基座，只压低两指内关节细节。 |
| sparse_both_hands_inner_axis_smooth_0.70_every_5f | positive | PASS | 97.087 | >= 70.0 | 3 | 60 | axis_smooth:['left_hand', 'right_hand']:['thumb', 'index', 'middle', 'ring', 'pinky']:0.7 | score_valid:score_valid | action_window_net:used | 每 5 帧一次较强内关节线性化，模拟偶发低细节关键帧。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | 0 | 0 | - | score_valid:score_valid | action_window_net:used | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

## 说明

- 该门补充的是低分辨率/低细节下的 hand landmark 简化，不替代已有 coordinate-precision、landmark-noise、finger-curl-style 或 finger-length-style 门。
- 正向变体只线性化 PIP/DIP 等内关节，保留 MCP、指尖位置和粗手形；强指尖向掌心塌缩只观察诊断边界。
- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。

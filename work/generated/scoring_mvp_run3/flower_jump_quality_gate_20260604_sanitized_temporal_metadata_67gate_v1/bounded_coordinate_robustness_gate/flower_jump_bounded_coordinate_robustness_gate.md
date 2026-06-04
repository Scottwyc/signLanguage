# 花/跳有限异常/退化坐标鲁棒性门

- 生成时间：`2026-06-04T08:59:40`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- hand/face 可见坐标边界：x/y `[-0.15, 1.15]`，z `[-1.0, 1.0]`；pose 不套边界，因为网页样本常有非语义 pose 点出画面。
- exact-zero 占位阈值：`1e-07`；整手退化检测：可见点数 `>= 8` 且 x/y 跨度 `<= 0.012`。
- 口径：写入有限 out-of-frame、z-depth 离群、exact-zero 占位和整手极小跨度塌缩的临时 Holistic JSON fixture，再经正常 `load_sequence()` 和 `run_pair()` 评分；不调用 `/api/score`，不运行 Holistic，不移动 marker，不重启 5080。
- 目标：手部/face 稀疏有限坏点被视为缺失点，DTW/normalized distance/score 必须保持有限；持续核心手越界、离群或塌缩必须低分或触发重采/语义失败诊断。

- 5080 状态：worker=`ready`，pid=`811485`，reload_count=`21`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向越界点 | 诊断最低分 | 最弱诊断边界 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 99.312 | flower_right_outer_tips_sparse_out_of_frame | 37.624 | flower_right_core_hand_middle35_out_diagnostic | 70.000 |
| 跳 | PASS | 70.714 | jump_right_person_tips_single_out_of_frame | 0.236 | jump_right_core_hand_full_duplicate_wrist_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | finite | vector/mask 非有限 | 改动值 | pattern | capture_quality | semantic_floor | 异常 | 说明 |
|---|---|---|---:|---|---|---|---:|---|---|---|---|---|
| flower_right_core_hand_middle35_out_diagnostic | diagnostic | PASS | 37.624 | <= 55.0; quality in needs_recapture,semantic_mismatch | True | 0/0 | 399 | middle_35pct | needs_recapture:flower_core_hand_presence_low | short_visible_core:query_not_short_core_capture | - | 诊断记录：开花核心手较长窗口整手出画面时应触发重采/低分边界。 |
| flower_right_core_hand_middle35_z_outlier_diagnostic | diagnostic | PASS | 37.624 | <= 55.0; quality in needs_recapture,semantic_mismatch | True | 0/0 | 399 | middle_35pct | needs_recapture:flower_core_hand_presence_low | short_visible_core:query_not_short_core_capture | - | 诊断记录：开花核心手较长窗口整手 z 离群应触发重采/低分边界。 |
| flower_right_core_hand_middle35_zero_placeholder_diagnostic | diagnostic | PASS | 37.624 | <= 55.0; quality in needs_recapture,semantic_mismatch | True | 0/0 | 1197 | middle_35pct | needs_recapture:flower_core_hand_presence_low | short_visible_core:query_not_short_core_capture | - | 诊断记录：开花核心手较长窗口整手 exact-zero 占位应触发重采/低分边界。 |
| flower_right_core_hand_middle35_duplicate_wrist_diagnostic | diagnostic | PASS | 37.624 | <= 55.0; quality in needs_recapture,semantic_mismatch | True | 0/0 | 1197 | middle_35pct | needs_recapture:flower_core_hand_presence_low | short_visible_core:query_not_short_core_capture | - | 诊断记录：开花核心手较长窗口所有点塌缩到手腕时应触发重采/低分边界。 |
| flower_right_core_hand_middle35_tiny_span_diagnostic | diagnostic | PASS | 37.624 | <= 55.0; quality in needs_recapture,semantic_mismatch | True | 0/0 | 1197 | middle_35pct | needs_recapture:flower_core_hand_presence_low | short_visible_core:query_not_short_core_capture | - | 诊断记录：开花核心手较长窗口整手极小跨度塌缩时应触发重采/低分边界。 |
| flower_right_outer_tips_sparse_out_of_frame | positive | PASS | 99.312 | >= 70.0 | True | 0/0 | 28 | sparse_every_5f | score_valid:score_valid | short_visible_core:query_not_short_core_capture | - | 开花 ring/pinky 外侧指尖稀疏有限越界，应被局部 mask 掉。 |
| flower_right_outer_tips_sparse_z_outlier | positive | PASS | 99.312 | >= 70.0 | True | 0/0 | 14 | sparse_every_5f | score_valid:score_valid | short_visible_core:query_not_short_core_capture | - | 开花 ring/pinky 外侧指尖稀疏有限 z 离群，应被局部 mask 掉。 |
| flower_right_outer_tips_sparse_zero_placeholder | positive | PASS | 99.312 | >= 70.0 | True | 0/0 | 42 | sparse_every_5f | score_valid:score_valid | short_visible_core:query_not_short_core_capture | - | 开花 ring/pinky 外侧指尖稀疏 exact-zero 占位点，应被局部 mask 掉。 |
| flower_right_index_middle_tip_single_z_outlier | positive | PASS | 99.767 | >= 70.0 | True | 0/0 | 2 | single_mid | score_valid:score_valid | short_visible_core:query_not_short_core_capture | - | 开花核心手单帧 index/middle tip 有限 z 离群应按局部缺失处理，不能把正确开合动作打成低分。 |
| flower_right_index_middle_tip_single_zero_placeholder | positive | PASS | 99.767 | >= 70.0 | True | 0/0 | 6 | single_mid | score_valid:score_valid | short_visible_core:query_not_short_core_capture | - | 开花核心手单帧 index/middle tip exact-zero 占位点应按局部缺失处理。 |
| flower_right_index_tip_single_out_of_frame | positive | PASS | 99.947 | >= 70.0 | True | 0/0 | 1 | single_mid | score_valid:score_valid | short_visible_core:query_not_short_core_capture | - | 开花核心手单帧 index tip 有限越界应按该点缺失处理，完整开合证据仍应保留。 |
| self_reloaded | positive | PASS | 100.000 | >= 95.0 | True | 0/0 | 0 | none | score_valid:score_valid | short_visible_core:query_not_short_core_capture | - | 原始标准 JSON 经正常 load_sequence 重载，应保持近满分且所有距离有限。 |
| face_core_sparse_out_of_frame | positive | PASS | 100.000 | >= 70.0 | True | 0/0 | 28 | sparse_every_7f | score_valid:score_valid | short_visible_core:query_not_short_core_capture | - | face core 稀疏有限越界点应被视为缺失，不能污染手部语义评分。 |
| face_core_sparse_z_outlier | positive | PASS | 100.000 | >= 70.0 | True | 0/0 | 28 | sparse_every_7f | score_valid:score_valid | short_visible_core:query_not_short_core_capture | - | face core 稀疏有限 z 离群点应被视为缺失，不能污染手部语义评分。 |
| face_core_sparse_zero_placeholder | positive | PASS | 100.000 | >= 70.0 | True | 0/0 | 84 | sparse_every_7f | score_valid:score_valid | short_visible_core:query_not_short_core_capture | - | face core 稀疏 exact-zero 占位点应被视为缺失，不能污染手部语义评分。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | finite | vector/mask 非有限 | 改动值 | pattern | capture_quality | semantic_floor | 异常 | 说明 |
|---|---|---|---:|---|---|---|---:|---|---|---|---|---|
| jump_right_core_hand_full_duplicate_wrist_diagnostic | diagnostic | PASS | 0.236 | <= 55.0; quality in needs_recapture,semantic_mismatch | True | 0/0 | 1071 | full | needs_recapture:jump_two_hand_presence_low | -:insufficient_two_hand_presence | - | 诊断记录：右手小人全程所有点塌缩到手腕时应触发重采/低分边界。 |
| jump_right_core_hand_full_tiny_span_diagnostic | diagnostic | PASS | 0.236 | <= 55.0; quality in needs_recapture,semantic_mismatch | True | 0/0 | 1071 | full | needs_recapture:jump_two_hand_presence_low | -:insufficient_two_hand_presence | - | 诊断记录：右手小人全程整手极小跨度塌缩时应触发重采/低分边界。 |
| jump_right_core_hand_middle35_out_diagnostic | diagnostic | PASS | 6.189 | <= 55.0; quality in needs_recapture,semantic_mismatch | True | 0/0 | 294 | middle_35pct | needs_recapture:jump_two_hand_presence_low | -:insufficient_two_hand_presence | - | 诊断记录：右手小人较长窗口整手出画面时应触发重采/低分边界。 |
| jump_right_core_hand_middle35_z_outlier_diagnostic | diagnostic | PASS | 6.189 | <= 55.0; quality in needs_recapture,semantic_mismatch | True | 0/0 | 147 | middle_35pct | needs_recapture:jump_two_hand_presence_low | -:insufficient_two_hand_presence | - | 诊断记录：右手小人较长窗口整手 z 离群应触发重采/低分边界。 |
| jump_right_core_hand_middle35_zero_placeholder_diagnostic | diagnostic | PASS | 6.189 | <= 55.0; quality in needs_recapture,semantic_mismatch | True | 0/0 | 441 | middle_35pct | needs_recapture:jump_two_hand_presence_low | -:insufficient_two_hand_presence | - | 诊断记录：右手小人较长窗口整手 exact-zero 占位应触发重采/低分边界。 |
| jump_left_ground_hand_middle35_tiny_span_diagnostic | diagnostic | PASS | 9.425 | <= 55.0; quality in needs_recapture,semantic_mismatch | True | 0/0 | 378 | middle_35pct | needs_recapture:jump_two_hand_presence_low | -:insufficient_two_hand_presence | - | 诊断记录：左手地面手较长窗口整手极小跨度塌缩时应触发重采/低分边界。 |
| jump_right_person_tips_single_out_of_frame | positive | PASS | 70.714 | >= 70.0 | True | 0/0 | 2 | single_mid | score_valid:score_valid | action_window_net:used | - | 跳的右手两指单帧 tip 有限越界应按局部缺失处理，不应破坏完整弹跳轨迹。 |
| jump_right_person_tips_single_z_outlier | positive | PASS | 70.714 | >= 70.0 | True | 0/0 | 2 | single_mid | score_valid:score_valid | action_window_net:used | - | 跳的右手两指单帧 tip 有限 z 离群应按局部缺失处理，不应破坏完整弹跳轨迹。 |
| jump_right_person_tips_single_zero_placeholder | positive | PASS | 70.714 | >= 70.0 | True | 0/0 | 6 | single_mid | score_valid:score_valid | action_window_net:used | - | 跳的右手两指单帧 tip exact-zero 占位点应按局部缺失处理，不应破坏完整弹跳轨迹。 |
| jump_left_ground_sparse_out_of_frame | positive | PASS | 81.958 | >= 70.0 | True | 0/0 | 15 | sparse_every_7f | score_valid:score_valid | action_window_net:used | - | 跳的左手地面手稀疏有限越界应按缺失处理，多数双手关系帧仍可评分。 |
| jump_left_ground_sparse_z_outlier | positive | PASS | 81.958 | >= 70.0 | True | 0/0 | 15 | sparse_every_7f | score_valid:score_valid | action_window_net:used | - | 跳的左手地面手稀疏有限 z 离群应按缺失处理，多数双手关系帧仍可评分。 |
| jump_left_ground_sparse_zero_placeholder | positive | PASS | 81.958 | >= 70.0 | True | 0/0 | 45 | sparse_every_7f | score_valid:score_valid | action_window_net:used | - | 跳的左手地面手稀疏 exact-zero 占位点应按缺失处理，多数双手关系帧仍可评分。 |
| self_reloaded | positive | PASS | 100.000 | >= 95.0 | True | 0/0 | 0 | none | score_valid:score_valid | action_window_net:used | - | 原始标准 JSON 经正常 load_sequence 重载，应保持近满分且所有距离有限。 |
| face_core_sparse_out_of_frame | positive | PASS | 100.000 | >= 70.0 | True | 0/0 | 12 | sparse_every_7f | score_valid:score_valid | action_window_net:used | - | face core 稀疏有限越界点应被视为缺失，不能污染手部语义评分。 |
| face_core_sparse_z_outlier | positive | PASS | 100.000 | >= 70.0 | True | 0/0 | 12 | sparse_every_7f | score_valid:score_valid | action_window_net:used | - | face core 稀疏有限 z 离群点应被视为缺失，不能污染手部语义评分。 |
| face_core_sparse_zero_placeholder | positive | PASS | 100.000 | >= 70.0 | True | 0/0 | 36 | sparse_every_7f | score_valid:score_valid | action_window_net:used | - | face core 稀疏 exact-zero 占位点应被视为缺失，不能污染手部语义评分。 |

## 说明

- 该门补充的是手部/face 有限异常和退化坐标的加载清洗，不替代 edge clipping、missing/mask、landmark spike 或 finite-coordinate 门。
- out-of-frame、z-depth 离群、exact-zero 占位和整手极小跨度塌缩都不是有效动作证据；稀疏局部坏点应局部缺失，持续核心手退化应重采或人工复核。
- 该门是缓存 JSON fixture 压力测试，不能替代正式 marker 后的真实网页摄像头样本。

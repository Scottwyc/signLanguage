# 花/跳非有限坐标清洗鲁棒性门

- 生成时间：`2026-06-04T15:25:53`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：写入带 `NaN/Inf` 的临时 Holistic JSON fixture，再经正常 `load_sequence()` 和 `run_pair()` 评分；不调用 `/api/score`，不运行 Holistic，不移动 marker，不重启 5080。
- 目标：孤立或稀疏非有限坐标被视为缺失点，DTW/normalized distance/score 必须保持有限；持续核心手坏点只记录诊断边界。

- 5080 状态：worker=`ready`，pid=`811485`，reload_count=`27`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向坏点 | 诊断最低分 | 最弱诊断边界 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 98.946 | pose_face_sparse_nan_inf | 78.039 | all_pose_full_nan_diagnostic | 70.000 |
| 跳 | PASS | 70.714 | jump_right_person_tip_single_nan | 78.935 | all_pose_full_nan_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | finite | vector/mask 非有限 | 改动值 | pattern | capture_quality | semantic_floor | 异常 | 说明 |
|---|---|---|---:|---|---|---|---:|---|---|---|---|---|
| all_pose_full_nan_diagnostic | diagnostic | DIAG | 78.039 | diagnostic | True | 0/0 | 5247 | full | score_valid:score_valid | short_visible_core:query_not_short_core_capture | - | 诊断记录：全段 pose 归一化信息不可用时，打分应保持有限并依靠手部证据或重采诊断。 |
| flower_right_all_distal_middle35_nan_diagnostic | diagnostic | DIAG | 82.954 | diagnostic | True | 0/0 | 570 | middle_35pct | score_valid:score_valid | short_visible_core:query_not_short_core_capture | - | 诊断记录：开花核心手较长窗口所有 distal finger-chain 坐标坏掉时的边界分。 |
| pose_face_sparse_nan_inf | positive | PASS | 98.946 | >= 70.0 | True | 0/0 | 63 | sparse_every_7f | score_valid:score_valid | short_visible_core:query_not_short_core_capture | - | 非核心 pose/face 稀疏坏点应被当作缺失，不应污染手部语义评分。 |
| flower_right_outer_tips_sparse_inf | positive | PASS | 99.312 | >= 70.0 | True | 0/0 | 28 | sparse_every_5f | score_valid:score_valid | short_visible_core:query_not_short_core_capture | - | 开花 ring/pinky tip 稀疏帧 Inf 坏点应被局部 mask 掉。 |
| flower_right_index_tip_single_nan | positive | PASS | 99.947 | >= 70.0 | True | 0/0 | 1 | single_mid | score_valid:score_valid | short_visible_core:query_not_short_core_capture | - | 开花核心手单帧 index tip NaN 应被视为该点缺失，完整开合证据仍应保留。 |
| self_reloaded | positive | PASS | 100.000 | >= 95.0 | True | 0/0 | 0 | none | score_valid:score_valid | short_visible_core:query_not_short_core_capture | - | 原始标准 JSON 经正常 load_sequence 重载，应保持近满分且所有距离有限。 |
| pose_shoulder_first3_inf | positive | PASS | 100.000 | >= 70.0 | True | 0/0 | 12 | first_3 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | - | 起始几帧肩部归一化锚点异常时，应回退到有限 pose 点或默认归一化。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | finite | vector/mask 非有限 | 改动值 | pattern | capture_quality | semantic_floor | 异常 | 说明 |
|---|---|---|---:|---|---|---|---:|---|---|---|---|---|
| all_pose_full_nan_diagnostic | diagnostic | DIAG | 78.935 | diagnostic | True | 0/0 | 1881 | full | score_valid:score_valid | full_sequence_local_relation_segment:used | - | 诊断记录：全段 pose 归一化信息不可用时，打分应保持有限并依靠手部证据或重采诊断。 |
| jump_right_person_middle35_nan_diagnostic | diagnostic | DIAG | 79.710 | diagnostic | True | 0/0 | 84 | middle_35pct | score_valid:score_valid | full_sequence_local_relation_segment:used | - | 诊断记录：右手两指小人较长窗口 distal 坐标坏掉时的边界分。 |
| jump_right_person_tip_single_nan | positive | PASS | 70.714 | >= 70.0 | True | 0/0 | 2 | single_mid | score_valid:score_valid | action_window_net:used | - | 跳的右手两指单帧 tip NaN 应被局部 mask，不应破坏完整弹跳轨迹。 |
| pose_face_sparse_nan_inf | positive | PASS | 76.227 | >= 70.0 | True | 0/0 | 27 | sparse_every_7f | score_valid:score_valid | action_window_net:used | - | 非核心 pose/face 稀疏坏点应被当作缺失，不应污染手部语义评分。 |
| jump_left_ground_sparse_inf | positive | PASS | 81.958 | >= 70.0 | True | 0/0 | 15 | sparse_every_7f | score_valid:score_valid | action_window_net:used | - | 跳的左手地面手稀疏帧锚点 Inf 应被当作缺失，右手小人和多数关系帧仍可评分。 |
| pose_shoulder_first3_inf | positive | PASS | 99.402 | >= 70.0 | True | 0/0 | 12 | first_3 | score_valid:score_valid | action_window_net:used | - | 起始几帧肩部归一化锚点异常时，应回退到有限 pose 点或默认归一化。 |
| self_reloaded | positive | PASS | 100.000 | >= 95.0 | True | 0/0 | 0 | none | score_valid:score_valid | action_window_net:used | - | 原始标准 JSON 经正常 load_sequence 重载，应保持近满分且所有距离有限。 |

## 说明

- 该门补充的是 JSON 入口和距离计算的数值清洗，不替代 missing/mask、landmark spike、coordinate precision 或 occlusion 门。
- 非有限坐标在本口径中不是“正常动作证据”，只是不能污染全局距离或导致 NaN 诊断；持续核心坏点仍需要重采或人工复核。
- 该门是缓存 JSON fixture 压力测试，不能替代正式 marker 后的真实网页摄像头样本。

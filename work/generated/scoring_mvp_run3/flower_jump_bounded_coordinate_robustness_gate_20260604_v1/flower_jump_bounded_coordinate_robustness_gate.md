# 花/跳有限越界坐标鲁棒性门

- 生成时间：`2026-06-04T04:05:54`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- hand/face 可见坐标边界：`[-0.15, 1.15]`；pose 不套边界，因为网页样本常有非语义 pose 点出画面。
- 口径：写入有限 out-of-frame 坐标的临时 Holistic JSON fixture，再经正常 `load_sequence()` 和 `run_pair()` 评分；不调用 `/api/score`，不运行 Holistic，不移动 marker，不重启 5080。
- 目标：手部/face 稀疏有限越界点被视为缺失点，DTW/normalized distance/score 必须保持有限；持续核心手越界只记录诊断边界。

- 5080 状态：worker=`ready`，pid=`811485`，reload_count=`16`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向越界点 | 诊断最低分 | 最弱诊断边界 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 99.312 | flower_right_outer_tips_sparse_out_of_frame | 82.954 | flower_right_all_distal_middle35_out_diagnostic | 70.000 |
| 跳 | PASS | 70.714 | jump_right_person_tips_single_out_of_frame | 79.710 | jump_right_person_middle35_out_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | finite | vector/mask 非有限 | 改动值 | pattern | capture_quality | semantic_floor | 异常 | 说明 |
|---|---|---|---:|---|---|---|---:|---|---|---|---|---|
| flower_right_all_distal_middle35_out_diagnostic | diagnostic | DIAG | 82.954 | diagnostic | True | 0/0 | 285 | middle_35pct | score_valid:score_valid | short_visible_core:query_not_short_core_capture | - | 诊断记录：开花核心手较长窗口所有 distal finger-chain 出画面时应触发重采/低分边界。 |
| flower_right_outer_tips_sparse_out_of_frame | positive | PASS | 99.312 | >= 70.0 | True | 0/0 | 28 | sparse_every_5f | score_valid:score_valid | short_visible_core:query_not_short_core_capture | - | 开花 ring/pinky 外侧指尖稀疏有限越界，应被局部 mask 掉。 |
| flower_right_index_tip_single_out_of_frame | positive | PASS | 99.947 | >= 70.0 | True | 0/0 | 1 | single_mid | score_valid:score_valid | short_visible_core:query_not_short_core_capture | - | 开花核心手单帧 index tip 有限越界应按该点缺失处理，完整开合证据仍应保留。 |
| self_reloaded | positive | PASS | 100.000 | >= 95.0 | True | 0/0 | 0 | none | score_valid:score_valid | short_visible_core:query_not_short_core_capture | - | 原始标准 JSON 经正常 load_sequence 重载，应保持近满分且所有距离有限。 |
| face_core_sparse_out_of_frame | positive | PASS | 100.000 | >= 70.0 | True | 0/0 | 28 | sparse_every_7f | score_valid:score_valid | short_visible_core:query_not_short_core_capture | - | face core 稀疏有限越界点应被视为缺失，不能污染手部语义评分。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | finite | vector/mask 非有限 | 改动值 | pattern | capture_quality | semantic_floor | 异常 | 说明 |
|---|---|---|---:|---|---|---|---:|---|---|---|---|---|
| jump_right_person_middle35_out_diagnostic | diagnostic | DIAG | 79.710 | diagnostic | True | 0/0 | 84 | middle_35pct | score_valid:score_valid | full_sequence_local_relation_segment:used | - | 诊断记录：右手两指小人较长窗口出画面时应触发重采/低分边界。 |
| jump_right_person_tips_single_out_of_frame | positive | PASS | 70.714 | >= 70.0 | True | 0/0 | 2 | single_mid | score_valid:score_valid | action_window_net:used | - | 跳的右手两指单帧 tip 有限越界应按局部缺失处理，不应破坏完整弹跳轨迹。 |
| jump_left_ground_sparse_out_of_frame | positive | PASS | 81.958 | >= 70.0 | True | 0/0 | 15 | sparse_every_7f | score_valid:score_valid | action_window_net:used | - | 跳的左手地面手稀疏有限越界应按缺失处理，多数双手关系帧仍可评分。 |
| self_reloaded | positive | PASS | 100.000 | >= 95.0 | True | 0/0 | 0 | none | score_valid:score_valid | action_window_net:used | - | 原始标准 JSON 经正常 load_sequence 重载，应保持近满分且所有距离有限。 |
| face_core_sparse_out_of_frame | positive | PASS | 100.000 | >= 70.0 | True | 0/0 | 12 | sparse_every_7f | score_valid:score_valid | action_window_net:used | - | face core 稀疏有限越界点应被视为缺失，不能污染手部语义评分。 |

## 说明

- 该门补充的是手部/face 有限越界坐标的加载清洗，不替代 edge clipping、missing/mask、landmark spike 或 finite-coordinate 门。
- out-of-frame 坐标不是有效动作证据；稀疏局部坏点应局部缺失，持续核心手越界仍应重采或人工复核。
- 该门是缓存 JSON fixture 压力测试，不能替代正式 marker 后的真实网页摄像头样本。

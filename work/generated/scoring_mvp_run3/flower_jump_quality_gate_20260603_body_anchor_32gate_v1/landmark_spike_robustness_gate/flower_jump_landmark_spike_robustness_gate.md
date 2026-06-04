# 花/跳 landmark 跳点鲁棒性门

- 生成时间：`2026-06-03T17:51:05`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，先剥离到基础骨架组，再在手部坐标层合成单帧/稀疏 landmark 跳点并重建 motion/relation/hand-shape 特征；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：单帧和稀疏跳点仍保持正常或边界分；连续核心跳点和 landmark 顺序扰动只作为诊断边界。

- 后端：`http://127.0.0.1:5080/api/status`，worker=`ready`，pid=`811485`，scoring reload=`14`，last_reload_error=`None`

## 汇总

- 总体：`PASS`

| 词条 | 状态 | 正向最低分 | 最弱正向跳点 | 诊断最低分 | 最弱诊断跳点 |
|---|---|---:|---|---:|---|
| 花 | PASS | 92.772 | sparse_tip_spike_every_7th | 21.400 | alternating_tip_spike_diagnostic |
| 跳 | PASS | 70.469 | single_frame_tip_spike | 82.302 | alternating_tip_spike_diagnostic |

## 花 明细

| 变体 | 类型 | 状态 | 分数 | 帧数 | 质量 | 语义 floor | 说明 |
|---|---|---|---:|---:|---|---|---|
| self_recomputed | positive | PASS | 100.000 | 0/53 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 标准序列剥离基础组后重建 motion/relation 特征，应保持近满分。 |
| single_frame_whole_hand_spike | positive | PASS | 99.430 | 1/53 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 单帧整手跳点属于 Holistic 短时检测抖动，应保持可评分。 |
| single_frame_tip_spike | positive | PASS | 98.887 | 1/53 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 单帧食指/中指 tip 跳点不应破坏完整正确动作。 |
| sparse_tip_spike_every_7th | positive | PASS | 92.772 | 8/53 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 稀疏 fingertip 跳点应靠 DTW/时序冗余保持正常或边界评分。 |
| middle_20pct_all_tip_spike_diagnostic | diagnostic | PASS | 96.477 | 11/53 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 连续核心片段多 fingertip 跳点属于边界诊断，不作为正向门。 |
| alternating_tip_spike_diagnostic | diagnostic | PASS | 21.400 | 26/53 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 交替半数帧 tip 跳点过强，只记录评分边界。 |
| middle_20pct_visible_shuffle_diagnostic | diagnostic | PASS | 75.259 | 11/53 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 连续片段 landmark 顺序扰动是严重检测错误，只作诊断。 |

## 跳 明细

| 变体 | 类型 | 状态 | 分数 | 帧数 | 质量 | 语义 floor | 说明 |
|---|---|---|---:|---:|---|---|---|
| self_recomputed | positive | PASS | 100.000 | 0/19 | score_valid:score_valid | action_window_net:used | 标准序列剥离基础组后重建 motion/relation 特征，应保持近满分。 |
| single_frame_whole_hand_spike | positive | PASS | 78.215 | 1/19 | score_valid:score_valid | action_window_net:used | 单帧整手跳点属于 Holistic 短时检测抖动，应保持可评分。 |
| single_frame_tip_spike | positive | PASS | 70.469 | 1/19 | score_valid:score_valid | action_window_net:used | 单帧食指/中指 tip 跳点不应破坏完整正确动作。 |
| sparse_tip_spike_every_7th | positive | PASS | 76.256 | 3/19 | score_valid:score_valid | full_sequence_local_relation_segment:used | 稀疏 fingertip 跳点应靠 DTW/时序冗余保持正常或边界评分。 |
| middle_20pct_all_tip_spike_diagnostic | diagnostic | PASS | 84.587 | 3/19 | score_valid:score_valid | full_sequence_local_relation_segment:used | 连续核心片段多 fingertip 跳点属于边界诊断，不作为正向门。 |
| alternating_tip_spike_diagnostic | diagnostic | PASS | 82.302 | 9/19 | score_valid:score_valid | action_window_net:used | 交替半数帧 tip 跳点过强，只记录评分边界。 |
| middle_20pct_visible_shuffle_diagnostic | diagnostic | PASS | 84.587 | 3/19 | score_valid:score_valid | full_sequence_local_relation_segment:used | 连续片段 landmark 顺序扰动是严重检测错误，只作诊断。 |


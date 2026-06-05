# 花/跳 Landmark 数组长度与索引完整性鲁棒性门

- 生成时间：`2026-06-04T16:30:44`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 口径：对缓存 Holistic JSON 做截断、前插和尾部追加，再经正常 `load_sequence()` / `run_pair()`；不调用 `/api/score`、不运行 Holistic、不移动 marker、不重启 5080。
- 固定长度契约：pose=`33`、hand=`21`、face=`478`；非空数组长度不匹配时整组按缺失处理，不能沿错误索引解释 landmark 身份。
- 正常审计：当前 178 个模板/网页 JSON 中，非空 pose/hand/face 数组长度全部符合固定长度契约。

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向变体 | 核心手诊断最高分 | 最强诊断变体 |
|---|---|---:|---|---:|---|
| 花 | PASS | 78.039 | pose_drop_first_full_hand_fallback | 1.164 | right_hand_drop_first_full_recapture |
| 跳 | PASS | 76.227 | pose_drop_first_sparse_masked | 2.161 | left_hand_drop_first_full_recapture |

## 分项明细

### 花

| 变体 | 类型 | 状态 | 分数 | 阈值 | 长度错误帧 | 整组屏蔽 | capture_quality |
|---|---|---|---:|---:|---:|---|---|
| self_reloaded | positive | PASS | 100.000 | 95.000 | 0 | True | score_valid:score_valid |
| right_hand_drop_first_sparse_masked | positive | PASS | 98.112 | 75.000 | 6 | True | score_valid:score_valid |
| pose_drop_first_sparse_masked | positive | PASS | 98.760 | 75.000 | 8 | True | score_valid:score_valid |
| pose_drop_first_full_hand_fallback | positive | PASS | 78.039 | 70.000 | 53 | True | score_valid:score_valid |
| right_hand_drop_first_full_recapture | diagnostic | PASS | 1.164 | 55.000 | 40 | True | needs_recapture:flower_core_hand_presence_low |
| right_hand_drop_middle_sparse_masked | positive | PASS | 98.112 | 75.000 | 6 | True | score_valid:score_valid |
| pose_drop_middle_sparse_masked | positive | PASS | 98.760 | 75.000 | 8 | True | score_valid:score_valid |
| pose_drop_middle_full_hand_fallback | positive | PASS | 78.039 | 70.000 | 53 | True | score_valid:score_valid |
| right_hand_drop_middle_full_recapture | diagnostic | PASS | 1.164 | 55.000 | 40 | True | needs_recapture:flower_core_hand_presence_low |
| right_hand_insert_first_sparse_masked | positive | PASS | 98.112 | 75.000 | 6 | True | score_valid:score_valid |
| pose_insert_first_sparse_masked | positive | PASS | 98.760 | 75.000 | 8 | True | score_valid:score_valid |
| pose_insert_first_full_hand_fallback | positive | PASS | 78.039 | 70.000 | 53 | True | score_valid:score_valid |
| right_hand_insert_first_full_recapture | diagnostic | PASS | 1.164 | 55.000 | 40 | True | needs_recapture:flower_core_hand_presence_low |
| right_hand_append_extra_sparse_masked | positive | PASS | 98.112 | 75.000 | 6 | True | score_valid:score_valid |
| pose_append_extra_sparse_masked | positive | PASS | 98.760 | 75.000 | 8 | True | score_valid:score_valid |
| pose_append_extra_full_hand_fallback | positive | PASS | 78.039 | 70.000 | 53 | True | score_valid:score_valid |
| right_hand_append_extra_full_recapture | diagnostic | PASS | 1.164 | 55.000 | 40 | True | needs_recapture:flower_core_hand_presence_low |
| face_insert_first_sparse_masked | positive | PASS | 100.000 | 95.000 | 8 | True | score_valid:score_valid |
| face_insert_first_full_masked | positive | PASS | 100.000 | 95.000 | 53 | True | score_valid:score_valid |
| face_drop_middle_sparse_masked | positive | PASS | 100.000 | 95.000 | 8 | True | score_valid:score_valid |
| face_drop_middle_full_masked | positive | PASS | 100.000 | 95.000 | 53 | True | score_valid:score_valid |

### 跳

| 变体 | 类型 | 状态 | 分数 | 阈值 | 长度错误帧 | 整组屏蔽 | capture_quality |
|---|---|---|---:|---:|---:|---|---|
| self_reloaded | positive | PASS | 100.000 | 95.000 | 0 | True | score_valid:score_valid |
| right_hand_drop_first_sparse_masked | positive | PASS | 81.642 | 75.000 | 2 | True | score_valid:score_valid |
| pose_drop_first_sparse_masked | positive | PASS | 76.227 | 75.000 | 3 | True | score_valid:score_valid |
| pose_drop_first_full_hand_fallback | positive | PASS | 78.935 | 70.000 | 19 | True | score_valid:score_valid |
| right_hand_drop_first_full_recapture | diagnostic | PASS | 0.236 | 55.000 | 17 | True | needs_recapture:jump_two_hand_presence_low |
| right_hand_drop_middle_sparse_masked | positive | PASS | 81.642 | 75.000 | 2 | True | score_valid:score_valid |
| pose_drop_middle_sparse_masked | positive | PASS | 76.227 | 75.000 | 3 | True | score_valid:score_valid |
| pose_drop_middle_full_hand_fallback | positive | PASS | 78.935 | 70.000 | 19 | True | score_valid:score_valid |
| right_hand_drop_middle_full_recapture | diagnostic | PASS | 0.236 | 55.000 | 17 | True | needs_recapture:jump_two_hand_presence_low |
| right_hand_insert_first_sparse_masked | positive | PASS | 81.642 | 75.000 | 2 | True | score_valid:score_valid |
| pose_insert_first_sparse_masked | positive | PASS | 76.227 | 75.000 | 3 | True | score_valid:score_valid |
| pose_insert_first_full_hand_fallback | positive | PASS | 78.935 | 70.000 | 19 | True | score_valid:score_valid |
| right_hand_insert_first_full_recapture | diagnostic | PASS | 0.236 | 55.000 | 17 | True | needs_recapture:jump_two_hand_presence_low |
| right_hand_append_extra_sparse_masked | positive | PASS | 81.642 | 75.000 | 2 | True | score_valid:score_valid |
| pose_append_extra_sparse_masked | positive | PASS | 76.227 | 75.000 | 3 | True | score_valid:score_valid |
| pose_append_extra_full_hand_fallback | positive | PASS | 78.935 | 70.000 | 19 | True | score_valid:score_valid |
| right_hand_append_extra_full_recapture | diagnostic | PASS | 0.236 | 55.000 | 17 | True | needs_recapture:jump_two_hand_presence_low |
| face_insert_first_sparse_masked | positive | PASS | 100.000 | 95.000 | 3 | True | score_valid:score_valid |
| face_insert_first_full_masked | positive | PASS | 100.000 | 95.000 | 19 | True | score_valid:score_valid |
| face_drop_middle_sparse_masked | positive | PASS | 100.000 | 95.000 | 3 | True | score_valid:score_valid |
| face_drop_middle_full_masked | positive | PASS | 100.000 | 95.000 | 19 | True | score_valid:score_valid |
| left_hand_drop_first_sparse_masked | positive | PASS | 84.678 | 75.000 | 2 | True | score_valid:score_valid |
| left_hand_drop_first_full_recapture | diagnostic | PASS | 2.161 | 55.000 | 16 | True | needs_recapture:jump_two_hand_presence_low |
| left_hand_drop_middle_sparse_masked | positive | PASS | 84.678 | 75.000 | 2 | True | score_valid:score_valid |
| left_hand_drop_middle_full_recapture | diagnostic | PASS | 2.161 | 55.000 | 16 | True | needs_recapture:jump_two_hand_presence_low |
| left_hand_insert_first_sparse_masked | positive | PASS | 84.678 | 75.000 | 2 | True | score_valid:score_valid |
| left_hand_insert_first_full_recapture | diagnostic | PASS | 2.161 | 55.000 | 16 | True | needs_recapture:jump_two_hand_presence_low |
| left_hand_append_extra_sparse_masked | positive | PASS | 84.678 | 75.000 | 2 | True | score_valid:score_valid |
| left_hand_append_extra_full_recapture | diagnostic | PASS | 2.161 | 55.000 | 16 | True | needs_recapture:jump_two_hand_presence_low |

## 说明

- 稀疏长度错误按局部缺失处理，正确动作应保持可评分；整段核心手长度错误是输入损坏，必须要求重采而不是放宽词义阈值。
- 该门是缓存 JSON 压力测试，不替代正式 marker 后真实网页摄像头复测。

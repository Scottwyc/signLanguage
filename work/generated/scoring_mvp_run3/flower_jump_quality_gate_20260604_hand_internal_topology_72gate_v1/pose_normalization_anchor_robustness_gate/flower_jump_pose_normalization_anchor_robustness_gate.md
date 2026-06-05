# 花/跳 Pose 归一化锚点鲁棒性门

- 生成时间：`2026-06-04T16:29:49`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 口径：污染缓存 JSON 中的肩部/pose 锚点，再经正常 `load_sequence()` 和 `run_pair()` 评分；不调用 `/api/score`、不运行 Holistic、不移动 marker、不重启 5080。
- 目标：肩部需同时满足绝对边界、pose 拓扑和 pose-hand 流一致性；稀疏坏肩点使用相邻可信锚点插值，整段肩部或 pose 不可信时从有效手部中心与掌尺度回退。
- 正常审计：`178` 个模板/网页 JSON、`4776` 个 pose 帧，肩宽范围 `0.105884-0.571933`；当前门使用 shoulder scale `[0.06, 0.85]`。

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱变体 | 基础门槛 | 稀疏门槛 |
|---|---|---:|---|---:|---:|
| 花 | PASS | 78.039 | left_shoulder_xy_outlier_full_hand_fallback | 70.000 | 75.000 |
| 跳 | PASS | 76.227 | left_shoulder_xy_outlier_sparse_interpolated | 70.000 | 75.000 |

## 分项明细

### 花

| 变体 | 状态 | 分数 | 门槛 | finite | 改动值 | capture_quality | 说明 |
|---|---|---:|---:|---|---:|---|---|
| self_reloaded | PASS | 100.000 | 95.000 | True | 0 | score_valid:score_valid | 原始标准 JSON 重载后应保持近满分。 |
| left_shoulder_xy_outlier_sparse_interpolated | PASS | 98.760 | 75.000 | True | 16 | score_valid:score_valid | 稀疏有限肩部 x/y 离群应由相邻可信肩锚点插值，不能制造归一化抖动。 |
| left_shoulder_z_outlier_sparse_interpolated | PASS | 98.760 | 75.000 | True | 8 | score_valid:score_valid | 稀疏有限肩部 z 离群应由相邻可信肩锚点插值。 |
| duplicate_shoulders_sparse_interpolated | PASS | 98.760 | 75.000 | True | 24 | score_valid:score_valid | 稀疏肩点塌缩不能把 shoulder scale 压到近零。 |
| extreme_shoulder_span_sparse_interpolated | PASS | 98.760 | 75.000 | True | 16 | score_valid:score_valid | 稀疏异常肩宽不能缩放手部与双手关系特征。 |
| vertical_shoulder_shift_sparse_interpolated | PASS | 98.760 | 75.000 | True | 16 | score_valid:score_valid | 稀疏肩部 +0.7 边界漂移应由可信相邻帧插值。 |
| left_shoulder_xy_outlier_full_hand_fallback | PASS | 78.039 | 70.000 | True | 106 | score_valid:score_valid | 整段肩部 x/y 离群时，应使用有效手部中心/掌尺度 fallback。 |
| left_shoulder_z_outlier_full_hand_fallback | PASS | 78.039 | 70.000 | True | 53 | score_valid:score_valid | 整段肩部 z 离群时，应使用有效手部中心/掌尺度 fallback。 |
| duplicate_shoulders_full_hand_fallback | PASS | 78.039 | 70.000 | True | 159 | score_valid:score_valid | 整段肩点塌缩时，应拒绝近零 shoulder scale 并使用手部 fallback。 |
| extreme_shoulder_span_full_hand_fallback | PASS | 78.039 | 70.000 | True | 106 | score_valid:score_valid | 整段异常肩宽时，应拒绝离群 shoulder scale 并使用手部 fallback。 |
| vertical_shoulder_shift_full_hand_fallback | PASS | 78.039 | 70.000 | True | 106 | score_valid:score_valid | 整段肩部 +0.7 边界漂移时，应由 pose 拓扑一致性拒绝并使用手部 fallback。 |
| both_shoulders_z_positive_full_hand_fallback | PASS | 78.039 | 70.000 | True | 106 | score_valid:score_valid | 整段双肩 z 正向漂移时，应由 pose 拓扑或肩手流一致性拒绝。 |
| both_shoulders_z_negative_full_hand_fallback | PASS | 78.039 | 70.000 | True | 106 | score_valid:score_valid | 整段双肩 z 负向漂移时，应由 pose 拓扑或肩手流一致性拒绝。 |
| all_pose_xy_shift_full_hand_fallback | PASS | 78.039 | 70.000 | True | 3498 | score_valid:score_valid | 整段 pose 流与 hand 流发生 x/y 偏移时，应由 pose-hand wrist 一致性拒绝肩锚点。 |
| all_pose_z_positive_full_hand_fallback | PASS | 78.039 | 70.000 | True | 1749 | score_valid:score_valid | 整段 pose 流与 hand 流发生正向 z 偏移时，应由序列级肩手 z 一致性拒绝肩锚点。 |
| all_pose_z_negative_full_hand_fallback | PASS | 78.039 | 70.000 | True | 1749 | score_valid:score_valid | 整段 pose 流与 hand 流发生负向 z 偏移时，应由序列级肩手 z 一致性拒绝肩锚点。 |
| all_pose_nonfinite_full_hand_fallback | PASS | 78.039 | 70.000 | True | 5247 | score_valid:score_valid | 整段 pose 非有限但手部完整时，手部主导词仍应可评分。 |
| all_pose_zero_full_hand_fallback | PASS | 78.039 | 70.000 | True | 5247 | score_valid:score_valid | 整段 pose exact-zero 占位但手部完整时，不能使用零肩宽归一化。 |
| pose_group_removed_full_hand_fallback | PASS | 78.039 | 70.000 | True | 1749 | score_valid:score_valid | 整段 pose group 缺失但手部完整时，手部主导词仍应可评分。 |

### 跳

| 变体 | 状态 | 分数 | 门槛 | finite | 改动值 | capture_quality | 说明 |
|---|---|---:|---:|---|---:|---|---|
| self_reloaded | PASS | 100.000 | 95.000 | True | 0 | score_valid:score_valid | 原始标准 JSON 重载后应保持近满分。 |
| left_shoulder_xy_outlier_sparse_interpolated | PASS | 76.227 | 75.000 | True | 6 | score_valid:score_valid | 稀疏有限肩部 x/y 离群应由相邻可信肩锚点插值，不能制造归一化抖动。 |
| left_shoulder_z_outlier_sparse_interpolated | PASS | 76.227 | 75.000 | True | 3 | score_valid:score_valid | 稀疏有限肩部 z 离群应由相邻可信肩锚点插值。 |
| duplicate_shoulders_sparse_interpolated | PASS | 76.227 | 75.000 | True | 9 | score_valid:score_valid | 稀疏肩点塌缩不能把 shoulder scale 压到近零。 |
| extreme_shoulder_span_sparse_interpolated | PASS | 76.227 | 75.000 | True | 6 | score_valid:score_valid | 稀疏异常肩宽不能缩放手部与双手关系特征。 |
| vertical_shoulder_shift_sparse_interpolated | PASS | 76.227 | 75.000 | True | 6 | score_valid:score_valid | 稀疏肩部 +0.7 边界漂移应由可信相邻帧插值。 |
| left_shoulder_xy_outlier_full_hand_fallback | PASS | 78.935 | 70.000 | True | 38 | score_valid:score_valid | 整段肩部 x/y 离群时，应使用有效手部中心/掌尺度 fallback。 |
| left_shoulder_z_outlier_full_hand_fallback | PASS | 78.935 | 70.000 | True | 19 | score_valid:score_valid | 整段肩部 z 离群时，应使用有效手部中心/掌尺度 fallback。 |
| duplicate_shoulders_full_hand_fallback | PASS | 78.935 | 70.000 | True | 57 | score_valid:score_valid | 整段肩点塌缩时，应拒绝近零 shoulder scale 并使用手部 fallback。 |
| extreme_shoulder_span_full_hand_fallback | PASS | 78.935 | 70.000 | True | 38 | score_valid:score_valid | 整段异常肩宽时，应拒绝离群 shoulder scale 并使用手部 fallback。 |
| vertical_shoulder_shift_full_hand_fallback | PASS | 78.935 | 70.000 | True | 38 | score_valid:score_valid | 整段肩部 +0.7 边界漂移时，应由 pose 拓扑一致性拒绝并使用手部 fallback。 |
| both_shoulders_z_positive_full_hand_fallback | PASS | 78.935 | 70.000 | True | 38 | score_valid:score_valid | 整段双肩 z 正向漂移时，应由 pose 拓扑或肩手流一致性拒绝。 |
| both_shoulders_z_negative_full_hand_fallback | PASS | 78.935 | 70.000 | True | 38 | score_valid:score_valid | 整段双肩 z 负向漂移时，应由 pose 拓扑或肩手流一致性拒绝。 |
| all_pose_xy_shift_full_hand_fallback | PASS | 78.935 | 70.000 | True | 1254 | score_valid:score_valid | 整段 pose 流与 hand 流发生 x/y 偏移时，应由 pose-hand wrist 一致性拒绝肩锚点。 |
| all_pose_z_positive_full_hand_fallback | PASS | 78.935 | 70.000 | True | 627 | score_valid:score_valid | 整段 pose 流与 hand 流发生正向 z 偏移时，应由序列级肩手 z 一致性拒绝肩锚点。 |
| all_pose_z_negative_full_hand_fallback | PASS | 78.935 | 70.000 | True | 627 | score_valid:score_valid | 整段 pose 流与 hand 流发生负向 z 偏移时，应由序列级肩手 z 一致性拒绝肩锚点。 |
| all_pose_nonfinite_full_hand_fallback | PASS | 78.935 | 70.000 | True | 1881 | score_valid:score_valid | 整段 pose 非有限但手部完整时，手部主导词仍应可评分。 |
| all_pose_zero_full_hand_fallback | PASS | 78.935 | 70.000 | True | 1881 | score_valid:score_valid | 整段 pose exact-zero 占位但手部完整时，不能使用零肩宽归一化。 |
| pose_group_removed_full_hand_fallback | PASS | 78.935 | 70.000 | True | 627 | score_valid:score_valid | 整段 pose group 缺失但手部完整时，手部主导词仍应可评分。 |

## 说明

- 该门验证的是归一化入口，不通过放宽 `花/跳` 词义阈值抬分。
- pose 缺失但手部完整时可继续做手部主导词的原型相似度评分；这不等于真实用户分数已校准。
- 该门是缓存 JSON 压力测试，不能替代正式 marker 后真实网页摄像头复测。

# 花/跳缺失与关键 mask 鲁棒性门

- 生成时间：`2026-06-03T16:07:50`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，在骨架特征层面修改 mask；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：非关键 `pose/face` 或花的非核心手缺失时不应明显扣分；关键手部语义缺失时必须低分或进入重采/语义失败诊断。

- 5080 状态：worker=`ready`，worker_pid=`811485`，reload_count=`14`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 最弱正向变体 | 正向最低分 | 最强关键缺失变体 | 关键缺失最高分 |
|---|---|---|---:|---|---:|
| 花 | PASS | drop_face | 100.000 | drop_right_core_hand | 1.171 |
| 跳 | PASS | drop_face | 100.000 | drop_left_ground_hand | 3.037 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | capture_quality | reason | 说明 |
|---|---|---|---:|---|---|---|---|
| drop_right_core_hand | negative | PASS | 1.171 | <= 45.0 或重采/语义失败 | needs_recapture | flower_core_hand_presence_low | 开花手缺失时不能被当作正确花动作。 |
| drop_both_hands | negative | PASS | 1.171 | <= 35.0 或重采/语义失败 | needs_recapture | flower_core_hand_presence_low | 双手缺失时必须低分或建议重采。 |
| drop_face | positive | PASS | 100.000 | >= 70.0 | score_valid | score_valid | 面部不是花/跳核心语义。 |
| drop_pose | positive | PASS | 100.000 | >= 70.0 | score_valid | score_valid | 坐姿或躯干不完整不应主导手部语义评分。 |
| drop_pose_face | positive | PASS | 100.000 | >= 70.0 | score_valid | score_valid | 只保留手部语义时应仍可打出正常/边界分。 |
| drop_left_noncore_hand | positive | PASS | 100.000 | >= 65.0 | score_valid | score_valid | 花的核心是开花手的张开动作，非核心手缺失不应严重扣分。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | capture_quality | reason | 说明 |
|---|---|---|---:|---|---|---|---|
| drop_both_hands | negative | PASS | 0.125 | <= 35.0 或重采/语义失败 | needs_recapture | jump_two_hand_presence_low | 双手关系完全缺失时必须低分或建议重采。 |
| drop_right_jumping_hand | negative | PASS | 0.771 | <= 45.0 或重采/语义失败 | needs_recapture | jump_two_hand_presence_low | 跳需要右手两指小人，右手缺失不能通过。 |
| drop_left_ground_hand | negative | PASS | 3.037 | <= 45.0 或重采/语义失败 | needs_recapture | jump_two_hand_presence_low | 跳需要左手地面，左手缺失不能通过。 |
| drop_face | positive | PASS | 100.000 | >= 70.0 | score_valid | score_valid | 面部不是花/跳核心语义。 |
| drop_pose | positive | PASS | 100.000 | >= 70.0 | score_valid | score_valid | 坐姿或躯干不完整不应主导手部语义评分。 |
| drop_pose_face | positive | PASS | 100.000 | >= 70.0 | score_valid | score_valid | 只保留手部语义时应仍可打出正常/边界分。 |

## 说明

- 正向变体验证非关键特征不会盖过核心手语语义。
- 负向变体验证核心手部语义缺失时不会被 DTW 或语义 floor 误抬成正常分。
- 该门仍是合成 mask 压力测试，不能替代真实网页摄像头样本。

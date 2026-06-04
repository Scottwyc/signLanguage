# 花/跳画面边缘裁切鲁棒性门

- 生成时间：`2026-06-03T16:02:02`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，在骨架 mask 层模拟画面边缘导致的 landmark 不可见；手部裁切会重算 hand-shape 特征；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：非关键边缘裁切仍可评分；裁掉 `花` 开花手核心或 `跳` 双手关系核心时必须低分或进入重采/语义失败。

- 5080 状态：worker=`ready`，worker_pid=`811485`，reload_count=`14`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 最弱正向裁切 | 正向最低分 | 最强核心裁切 | 核心裁切最高分 |
|---|---|---|---:|---|---:|
| 花 | PASS | right_opening_wrist_edge_clip | 76.689 | right_opening_all_tips_edge_clip | 11.133 |
| 跳 | PASS | right_jumper_ring_pinky_edge_clip | 78.545 | left_ground_wrist_edge_clip | 10.489 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | capture_quality | reason | 说明 |
|---|---|---|---:|---|---|---|---|
| right_opening_outer_half_edge_clip | negative | PASS | 9.760 | <= 45.0 或重采/语义失败 | semantic_mismatch | flower_opening_guard_failed | 开花手外半部分被画面裁掉，核心手形不可靠。 |
| right_opening_all_tips_edge_clip | negative | PASS | 11.133 | <= 45.0 或重采/语义失败 | semantic_mismatch | flower_opening_guard_failed | 开花手全部指尖出画面，无法验证张开/绽放核心。 |
| right_opening_wrist_edge_clip | positive | PASS | 76.689 | >= 70.0 | score_valid | score_valid | 开花手腕部边缘点不可见，但指尖张开过程仍可见。 |
| right_opening_outer_tips_edge_clip | positive | PASS | 97.813 | >= 70.0 | score_valid | score_valid | 开花手最外侧指尖边缘点不可见，核心开合仍保留。 |
| face_edge_out_of_frame | positive | PASS | 100.000 | >= 70.0 | score_valid | score_valid | 脸部出画面边缘，双手核心仍完整。 |
| upper_body_edge_out_of_frame | positive | PASS | 100.000 | >= 70.0 | score_valid | score_valid | 上半身/脸部关键点不可见，但手部动作完整。 |
| left_noncore_hand_edge_clip | positive | PASS | 100.000 | >= 70.0 | score_valid | score_valid | 非核心手靠近画面边缘，部分点不可见。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | capture_quality | reason | 说明 |
|---|---|---|---:|---|---|---|---|
| right_jumper_index_middle_tips_edge_clip | negative | PASS | 10.010 | <= 45.0 或重采/语义失败 | semantic_mismatch | missing_relation_delta | 右手食指/中指小人的关键指尖出画面，跳跃语义缺失。 |
| left_ground_wrist_edge_clip | negative | PASS | 10.489 | <= 45.0 或重采/语义失败 | semantic_mismatch | missing_relation_delta | 左手地面支点出画面，双手关系不可靠。 |
| right_jumper_ring_pinky_edge_clip | positive | PASS | 78.545 | >= 70.0 | score_valid | score_valid | 右手非核心无名指/小指边缘点不可见，食指/中指小人仍可见。 |
| left_ground_tips_edge_clip | positive | PASS | 82.302 | >= 70.0 | score_valid | score_valid | 左手地面部分指尖靠近边缘，但地面关系仍可见。 |
| right_jumper_wrist_edge_clip | positive | PASS | 82.302 | >= 70.0 | score_valid | score_valid | 右手腕部边缘点不可见，但食指/中指跳跃核心仍保留。 |
| face_edge_out_of_frame | positive | PASS | 100.000 | >= 70.0 | score_valid | score_valid | 脸部出画面边缘，双手核心仍完整。 |
| upper_body_edge_out_of_frame | positive | PASS | 100.000 | >= 70.0 | score_valid | score_valid | 上半身/脸部关键点不可见，但手部动作完整。 |

## 说明

- 正向场景只覆盖非关键或轻度边缘裁切；核心手语信息出画面不能靠鲁棒性抬分。
- 该门是合成 edge-clipping 压力测试，不能替代真实网页摄像头样本。

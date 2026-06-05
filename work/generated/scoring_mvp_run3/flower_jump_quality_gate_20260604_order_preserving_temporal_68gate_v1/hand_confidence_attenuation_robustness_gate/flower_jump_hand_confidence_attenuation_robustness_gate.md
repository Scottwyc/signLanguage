# 花/跳手部置信度衰减鲁棒性门

- 生成时间：`2026-06-04T11:36:31`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，保留手部坐标，只降低手部/手形 mask 权重并重建 motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：覆盖网页摄像头中手部可见但置信度偏低的软 mask 场景；严重低置信只作为诊断边界。

- 5080 状态：worker=`ready`，worker_pid=`811485`，reload_count=`24`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向低置信 | 诊断最低分 | 最弱诊断边界 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 100.000 | flower_all_hands_confidence_0.85 | 1.171 | flower_all_hands_effective_missing_diagnostic | 70.000 |
| 跳 | PASS | 99.856 | jump_relation_core_sparse_confidence_0.55 | 0.125 | jump_all_hands_effective_missing_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 组 | scale | 帧范围 | L/R presence | L/R mask | capture_quality | reason | 说明 |
|---|---|---|---:|---|---|---:|---|---|---|---|---|---|
| flower_all_hands_effective_missing_diagnostic | diagnostic | DIAG | 1.171 | diagnostic | left_hand+right_hand | 0.000 | all | 0.000/0.000 | 0.000/0.000 | needs_recapture | flower_core_hand_presence_low | 低于有效阈值的极端情况按有效缺失记录，不作为软置信正向门。 |
| flower_bloom_core_right_confidence_0.51_diagnostic | diagnostic | DIAG | 100.000 | diagnostic | right_hand | 0.510 | 0.34-0.78 | 0.000/0.755 | 0.000/0.533 | score_valid | score_valid | 核心开花手置信度贴近有效阈值，作为 near-threshold 边界诊断。 |
| flower_all_hands_confidence_0.85 | positive | PASS | 100.000 | >= 70.0 | left_hand+right_hand | 0.850 | all | 0.000/0.755 | 0.000/0.642 | score_valid | score_valid | 全程双手 landmark 置信度轻度下降，但坐标仍可用。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | - | 1.000 | all | 0.000/0.755 | 0.000/0.755 | score_valid | score_valid | 标准序列剥离派生组后重建，应保持近满分。 |
| flower_bloom_core_right_confidence_0.65 | positive | PASS | 100.000 | >= 70.0 | right_hand | 0.650 | 0.34-0.78 | 0.000/0.755 | 0.000/0.596 | score_valid | score_valid | 开花手核心段置信度下降到仍高于形状/关系有效阈值。 |
| flower_bloom_core_sparse_confidence_0.55 | positive | PASS | 100.000 | >= 70.0 | right_hand | 0.550 | 0.34-0.78/step2 | 0.000/0.755 | 0.000/0.653 | score_valid | score_valid | 开花核心段隔帧低置信，仍应通过时序冗余正常评分。 |
| flower_noncore_left_confidence_0.52 | positive | PASS | 100.000 | >= 70.0 | left_hand | 0.520 | all | 0.000/0.755 | 0.000/0.755 | score_valid | score_valid | 非核心左手接近有效阈值的低置信不应拖垮右手绽放语义。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 组 | scale | 帧范围 | L/R presence | L/R mask | capture_quality | reason | 说明 |
|---|---|---|---:|---|---|---:|---|---|---|---|---|---|
| jump_all_hands_effective_missing_diagnostic | diagnostic | DIAG | 0.125 | diagnostic | left_hand+right_hand | 0.000 | all | 0.000/0.000 | 0.000/0.000 | needs_recapture | jump_two_hand_presence_low | 低于有效阈值的极端情况按有效缺失记录，不作为软置信正向门。 |
| jump_relation_core_both_confidence_0.51_diagnostic | diagnostic | DIAG | 99.881 | diagnostic | left_hand+right_hand | 0.510 | 0.22-0.76 | 0.842/0.895 | 0.584/0.611 | score_valid | score_valid | 双手关系核心置信度贴近有效阈值，作为 near-threshold 边界诊断。 |
| jump_relation_core_sparse_confidence_0.55 | positive | PASS | 99.856 | >= 70.0 | left_hand+right_hand | 0.550 | 0.22-0.76/step2 | 0.842/0.895 | 0.724/0.753 | score_valid | score_valid | 起跳核心隔帧低置信，仍应保留双手关系方向。 |
| jump_relation_core_both_confidence_0.65 | positive | PASS | 99.922 | >= 70.0 | left_hand+right_hand | 0.650 | 0.22-0.76 | 0.842/0.895 | 0.658/0.692 | score_valid | score_valid | 起跳/双手关系核心段双手低置信，但仍高于关系特征有效阈值。 |
| jump_right_person_hand_confidence_0.60 | positive | PASS | 99.932 | >= 70.0 | right_hand | 0.600 | 0.22-0.76 | 0.842/0.895 | 0.842/0.663 | score_valid | score_valid | 右手两指小人核心段轻中度低置信，仍应可评分。 |
| jump_all_hands_confidence_0.85 | positive | PASS | 100.000 | >= 70.0 | left_hand+right_hand | 0.850 | all | 0.842/0.895 | 0.716/0.761 | score_valid | score_valid | 双手全程轻度低置信，地面手/小人手关系仍完整。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | - | 1.000 | all | 0.842/0.895 | 0.842/0.895 | score_valid | score_valid | 标准序列剥离派生组后重建，应保持近满分。 |

## 说明

- 该门不同于 missing/mask、fingertip occlusion、dropout burst：它保留坐标，只下调 mask 置信权重。
- 正向变体只覆盖 mild/near-threshold 低置信，严重核心低置信应进入重采或语义失败诊断。
- 该门是合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。

# 花/跳手指中段关节遮挡鲁棒性门

- 生成时间：`2026-06-04T10:45:33`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，在 hand landmark mask 层合成 PIP/DIP/thumb-IP 等中段指节遮挡，并重建 motion/relation/hand-shape 特征；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：短时/稀疏中段指节不可见仍可正常评分；更强的持续核心指节缺失只作为诊断边界，不把它提升为正常网页采集要求。

- 5080 状态：worker=`ready`，pid=`811485`，reload_count=`23`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向中段指节遮挡 | 诊断最低分 | 最弱诊断遮挡 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 99.437 | right_sparse_all_inner_joints | 97.559 | right_all_inner_joints_diagnostic | 70.000 |
| 跳 | PASS | 76.638 | right_middle20_index_middle_inner_joints | 70.469 | right_core40_index_middle_inner_joints_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 遮挡帧 | landmark | capture_quality | 说明 |
|---|---|---|---:|---|---:|---|---|---|
| right_all_inner_joints_diagnostic | diagnostic | DIAG | 97.559 | diagnostic | 53/53 | 2,3,6,7,10,11,14,15,18,19 | score_valid:score_valid | 全程中段指节缺失时仍有指尖/掌根可见，记录模型解释边界而非硬负例。 |
| right_core40_all_inner_joints_diagnostic | diagnostic | DIAG | 98.497 | diagnostic | 21/53 | 2,3,6,7,10,11,14,15,18,19 | score_valid:score_valid | 核心段 40% 全中段指节缺失属于强遮挡边界，只作诊断记录。 |
| right_middle20_all_inner_joints_diagnostic | diagnostic | DIAG | 99.119 | diagnostic | 11/53 | 2,3,6,7,10,11,14,15,18,19 | score_valid:score_valid | 中段 20% 全中段指节缺失偏强，记录边界但不作为正常网页采集要求。 |
| right_sparse_all_inner_joints | positive | PASS | 99.437 | >= 70.0 | 8/53 | 2,3,6,7,10,11,14,15,18,19 | score_valid:score_valid | 开花右手所有中段指节稀疏闪断，验证 hand-shape mask 的时序冗余。 |
| right_middle20_index_middle_inner_joints | positive | PASS | 99.675 | >= 70.0 | 11/53 | 6,7,10,11 | score_valid:score_valid | 开花动作中段 20% 食指/中指中段指节不可见，开合语义仍应可恢复。 |
| right_middle20_ring_pinky_inner_joints | positive | PASS | 99.706 | >= 70.0 | 11/53 | 14,15,18,19 | score_valid:score_valid | 开花动作中段 20% 无名指/小指中段指节不可见，整体绽放仍应可评分。 |
| right_sparse_index_middle_inner_joints | positive | PASS | 99.854 | >= 70.0 | 8/53 | 6,7,10,11 | score_valid:score_valid | 开花右手食指/中指中段指节稀疏闪断，指尖和掌根仍可见。 |
| right_single_all_inner_joints | positive | PASS | 99.918 | >= 70.0 | 1/53 | 2,3,6,7,10,11,14,15,18,19 | score_valid:score_valid | 开花核心手单帧 PIP/DIP/thumb-IP 等中段指节丢失，模拟短时遮挡。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | 0/53 | - | score_valid:score_valid | 标准序列剥离基础组后重建 motion/relation 特征，应保持近满分。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 遮挡帧 | landmark | capture_quality | 说明 |
|---|---|---|---:|---|---:|---|---|---|
| right_core40_index_middle_inner_joints_diagnostic | diagnostic | DIAG | 70.469 | diagnostic | 7/19 | 6,7,10,11 | score_valid:score_valid | 右手两指中段指节核心段 40% 缺失偏强，只记录诊断边界。 |
| right_all_index_middle_inner_joints_diagnostic | diagnostic | DIAG | 70.469 | diagnostic | 19/19 | 6,7,10,11 | score_valid:score_valid | 右手两指中段指节全程缺失时仍有指尖/掌根可见，记录解释边界。 |
| left_core40_all_inner_joints_diagnostic | diagnostic | DIAG | 91.733 | diagnostic | 7/19 | 2,3,6,7,10,11,14,15,18,19 | score_valid:score_valid | 左手地面核心段 40% 中段指节缺失偏强，只记录诊断边界。 |
| right_middle20_index_middle_inner_joints | positive | PASS | 76.638 | >= 70.0 | 3/19 | 6,7,10,11 | score_valid:score_valid | 右手动作中段 20% 两指中段指节不可见，双手关系和两指轮廓仍应保留。 |
| left_middle20_all_inner_joints | positive | PASS | 94.892 | >= 70.0 | 3/19 | 2,3,6,7,10,11,14,15,18,19 | score_valid:score_valid | 左手地面中段 20% 指节不可见，右手弹跳语义仍应正常。 |
| left_sparse_all_inner_joints | positive | PASS | 96.246 | >= 70.0 | 3/19 | 2,3,6,7,10,11,14,15,18,19 | score_valid:score_valid | 左手地面中段指节稀疏闪断，不应导致跳跃双手关系整体失败。 |
| right_sparse_index_middle_inner_joints | positive | PASS | 97.174 | >= 70.0 | 3/19 | 6,7,10,11 | score_valid:score_valid | 右手两指小人食指/中指中段指节稀疏闪断，应由时序和指尖/掌根补偿。 |
| left_single_all_inner_joints | positive | PASS | 98.198 | >= 70.0 | 1/19 | 2,3,6,7,10,11,14,15,18,19 | score_valid:score_valid | 左手地面单帧中段指节丢失，地面手仍应通过掌根/指尖维持。 |
| right_single_index_middle_inner_joints | positive | PASS | 98.599 | >= 70.0 | 1/19 | 6,7,10,11 | score_valid:score_valid | 右手两指小人单帧食指/中指中段指节丢失，跳跃关系仍应可评分。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | 0/19 | - | score_valid:score_valid | 标准序列剥离基础组后重建 motion/relation 特征，应保持近满分。 |

## 说明

- 正向遮挡只覆盖单帧、稀疏或中段局部的 finger mid-joint mask 丢失，保持与真实轻量 detector 闪断一致。
- 持续核心段或全程中段指节缺失只记录诊断边界，因为指尖和掌根仍可能保留足够语义，不能简单当作硬负例。
- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。

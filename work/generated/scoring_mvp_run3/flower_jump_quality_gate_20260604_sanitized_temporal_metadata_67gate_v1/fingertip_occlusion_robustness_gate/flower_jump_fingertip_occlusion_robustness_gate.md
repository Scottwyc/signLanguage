# 花/跳指尖遮挡鲁棒性门

- 生成时间：`2026-06-04T08:45:11`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，在 hand landmark mask 层合成 fingertip 遮挡并重建 motion/relation/hand-shape 特征；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：短时/稀疏指尖不可见仍可正常评分；关键指尖全程不可见必须低分或进入重采/语义失败解释。

- 5080 状态：worker=`ready`，pid=`811485`，reload_count=`21`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向遮挡 | 核心缺失最高分 | 最强核心缺失负例 | 诊断最低分 | 最弱诊断遮挡 |
|---|---|---:|---|---:|---|---:|---|
| 花 | PASS | 95.829 | middle20_all_tips | 11.133 | all_right_tips_negative | 75.986 | core40_all_tips_diagnostic |
| 跳 | PASS | 70.469 | sparse_all_tips | 10.010 | all_right_index_middle_negative | 76.758 | core40_all_tips_diagnostic |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 遮挡帧 | landmark | capture_quality | 说明 |
|---|---|---|---:|---|---:|---|---|---|
| core40_all_tips_diagnostic | diagnostic | DIAG | 75.986 | diagnostic | 21/53 | 4,8,12,16,20 | score_valid:score_valid | 核心段 40% 全 tip 缺失属于遮挡边界，记录分数但不设硬门。 |
| all_right_tips_negative | negative | PASS | 11.133 | <= 45.0 或重采/语义失败 | 53/53 | 4,8,12,16,20 | semantic_mismatch:flower_opening_guard_failed | 花的右手绽放指尖全程不可见，不能当作完整语义通过。 |
| middle20_all_tips | positive | PASS | 95.829 | >= 70.0 | 11/53 | 4,8,12,16,20 | score_valid:score_valid | 动作中段 20% 全 tip 短时不可见，作为正向遮挡鲁棒门。 |
| sparse_all_tips | positive | PASS | 98.575 | >= 70.0 | 8/53 | 4,8,12,16,20 | score_valid:score_valid | 稀疏全 fingertip mask 丢失，覆盖网页帧间 tip 闪断。 |
| middle20_index_middle | positive | PASS | 99.230 | >= 70.0 | 11/53 | 8,12 | score_valid:score_valid | 动作中段 20% 食指/中指 tip 短时不可见，仍应保持边界以上。 |
| single_mid_all_tips | positive | PASS | 99.256 | >= 70.0 | 1/53 | 4,8,12,16,20 | score_valid:score_valid | 单帧右手五个 fingertip mask 丢失，模拟短时遮挡/检测抖动。 |
| sparse_index_middle | positive | PASS | 99.677 | >= 70.0 | 8/53 | 8,12 | score_valid:score_valid | 稀疏食指/中指 tip mask 丢失，应靠时序冗余保持可评分。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | 0/53 | - | score_valid:score_valid | 标准序列剥离基础组后重建 motion/relation 特征，应保持近满分。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 遮挡帧 | landmark | capture_quality | 说明 |
|---|---|---|---:|---|---:|---|---|---|
| core40_all_tips_diagnostic | diagnostic | DIAG | 76.758 | diagnostic | 7/19 | 4,8,12,16,20 | score_valid:score_valid | 核心段 40% 全 tip 缺失属于遮挡边界，记录分数但不设硬门。 |
| all_right_index_middle_negative | negative | PASS | 10.010 | <= 45.0 或重采/语义失败 | 19/19 | 8,12 | semantic_mismatch:missing_relation_delta | 跳的右手两指小人食指/中指 tip 全程不可见，应重采或语义失败。 |
| sparse_all_tips | positive | PASS | 70.469 | >= 70.0 | 3/19 | 4,8,12,16,20 | score_valid:score_valid | 稀疏全 fingertip mask 丢失，覆盖网页帧间 tip 闪断。 |
| middle20_all_tips | positive | PASS | 74.629 | >= 70.0 | 3/19 | 4,8,12,16,20 | score_valid:score_valid | 动作中段 20% 全 tip 短时不可见，作为正向遮挡鲁棒门。 |
| sparse_index_middle | positive | PASS | 79.149 | >= 70.0 | 3/19 | 8,12 | score_valid:score_valid | 稀疏食指/中指 tip mask 丢失，应靠时序冗余保持可评分。 |
| single_mid_all_tips | positive | PASS | 81.566 | >= 70.0 | 1/19 | 4,8,12,16,20 | score_valid:score_valid | 单帧右手五个 fingertip mask 丢失，模拟短时遮挡/检测抖动。 |
| middle20_index_middle | positive | PASS | 81.570 | >= 70.0 | 3/19 | 8,12 | score_valid:score_valid | 动作中段 20% 食指/中指 tip 短时不可见，仍应保持边界以上。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | 0/19 | - | score_valid:score_valid | 标准序列剥离基础组后重建 motion/relation 特征，应保持近满分。 |

## 说明

- 正向遮挡只覆盖短时、稀疏或中段 20% 的 fingertip mask 丢失，避免把持续大面积缺失误判为正常。
- `core40_all_tips_diagnostic` 是边界记录：当前模型可能仍能从其他手部结构和时序关系恢复语义，因此不作为硬失败门。
- 全程关键指尖缺失用于验证 capture quality 或低分语义能阻止不完整网页样本通过。
- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。

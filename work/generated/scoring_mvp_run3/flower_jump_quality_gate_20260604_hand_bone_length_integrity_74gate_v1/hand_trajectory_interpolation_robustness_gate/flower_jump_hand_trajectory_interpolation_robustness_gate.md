# 花/跳手部轨迹插值补洞鲁棒性门

- 生成时间：`2026-06-04T18:27:21`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，把短片段手部 landmark 线性插值到前后帧之间，并重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：短时 tracker 补洞或平滑线性化不应压低 `花/跳` 网页评分；较长核心段线性化只作诊断边界。

- 5080 状态：worker=`ready`，pid=`811485`，reload_count=`30`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向插值 | 诊断最低分 | 最弱诊断插值 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 93.731 | right_hand_middle12_interp | 74.445 | right_hand_middle25_interp_diagnostic | 70.000 |
| 跳 | PASS | 82.672 | right_hand_middle12_interp | 77.316 | both_hands_middle25_interp_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 组 | 插值帧 | capture_quality | 说明 |
|---|---|---|---:|---|---|---:|---|---|
| right_hand_middle25_interp_diagnostic | diagnostic | DIAG | 74.445 | diagnostic | right_hand | 13/53 | score_valid:score_valid | 开花核心段约 25% 轨迹线性化属于强边界，只作诊断。 |
| right_hand_middle18_interp_diagnostic | diagnostic | DIAG | 92.215 | diagnostic | right_hand | 9/53 | score_valid:score_valid | 开花核心段约 18% 轨迹线性化偏强，只记录诊断边界。 |
| right_hand_middle12_interp | positive | PASS | 93.731 | >= 70.0 | right_hand | 7/53 | score_valid:score_valid | 开花核心段约 12% 手部轨迹线性化，作为正常短补洞正向门。 |
| both_hands_middle12_interp | positive | PASS | 93.731 | >= 70.0 | left_hand,right_hand | 7/53 | score_valid:score_valid | 双手约 12% 轨迹线性化，验证非核心手同时受平滑影响仍可评分。 |
| right_hand_sparse_interp_every_6th | positive | PASS | 96.271 | >= 70.0 | right_hand | 9/53 | score_valid:score_valid | 开花核心手稀疏帧被线性插值，短时开合证据仍应保留。 |
| right_hand_single_mid_interp | positive | PASS | 99.614 | >= 70.0 | right_hand | 1/53 | score_valid:score_valid | 开花核心手单帧轨迹被前后帧线性插值，模拟 tracker 短补洞。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | left_hand,right_hand | 0/53 | score_valid:score_valid | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 组 | 插值帧 | capture_quality | 说明 |
|---|---|---|---:|---|---|---:|---|---|
| both_hands_middle25_interp_diagnostic | diagnostic | DIAG | 77.316 | diagnostic | left_hand,right_hand | 5/19 | score_valid:score_valid | 双手核心约 25% 轨迹线性化属于强边界，只作诊断。 |
| both_hands_middle12_interp_diagnostic | diagnostic | DIAG | 78.545 | diagnostic | left_hand,right_hand | 3/19 | score_valid:score_valid | 短动作双手同时线性化约 12% 偏强，只记录诊断边界。 |
| right_hand_middle18_interp_diagnostic | diagnostic | DIAG | 82.672 | diagnostic | right_hand | 3/19 | score_valid:score_valid | 右手弹跳核心约 18% 线性化偏强，只记录诊断边界。 |
| right_hand_middle12_interp | positive | PASS | 82.672 | >= 70.0 | right_hand | 3/19 | score_valid:score_valid | 右手约 12% 弹跳轨迹线性化，作为短补洞正向门。 |
| left_hand_middle12_interp | positive | PASS | 93.003 | >= 70.0 | left_hand | 3/19 | score_valid:score_valid | 左手地面约 12% 轨迹线性化，双手关系仍应可恢复。 |
| right_hand_sparse_interp_every_6th | positive | PASS | 94.305 | >= 70.0 | right_hand | 3/19 | score_valid:score_valid | 右手稀疏帧线性补洞，弹跳主方向仍应保留。 |
| right_hand_single_mid_interp | positive | PASS | 96.494 | >= 70.0 | right_hand | 1/19 | score_valid:score_valid | 右手两指小人单帧轨迹补洞，双手关系仍应可评分。 |
| left_hand_sparse_interp_every_6th | positive | PASS | 97.607 | >= 70.0 | left_hand | 3/19 | score_valid:score_valid | 左手地面稀疏帧线性补洞，右手弹跳关系仍应稳定。 |
| left_hand_single_mid_interp | positive | PASS | 97.611 | >= 70.0 | left_hand | 1/19 | score_valid:score_valid | 左手地面单帧轨迹补洞，不应导致跳跃关系失败。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | left_hand,right_hand | 0/19 | score_valid:score_valid | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

## 说明

- 正向门只覆盖单帧、稀疏或约 12% 的短片段手部轨迹插值补洞。
- 较长核心段插值会线性化关键动作轨迹，只作为诊断边界，不提升为正常网页采集要求。
- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。

# 花/跳 z 深度时序抖动鲁棒性门

- 生成时间：`2026-06-04T04:34:08`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，合成逐帧 z offset/scale breathing 和稀疏 z 跳动，并重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：轻微 z 深度呼吸或闪断不应压低 `花/跳` 网页评分；强 z 漂移只记录诊断边界。

- 5080 状态：worker=`ready`，pid=`811485`，reload_count=`16`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向 z 抖动 | 诊断最低分 | 最弱诊断 z 抖动 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 81.408 | smooth_global_z_scale_0.20 | 79.869 | strong_hand_z_scale_0.55_diagnostic | 70.000 |
| 跳 | PASS | 79.288 | smooth_global_z_offset_0.08 | 78.276 | strong_global_z_offset_0.25_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 组 | 模式 | 幅度 | 变化帧 | capture_quality | 说明 |
|---|---|---|---:|---|---|---|---:|---:|---|---|
| strong_hand_z_scale_0.55_diagnostic | diagnostic | DIAG | 79.869 | diagnostic | left_hand,right_hand | smooth/scale | 0.550 | 50/53 | score_valid:score_valid | 强手部 z 动态缩放会改变局部手形，只记录诊断边界。 |
| strong_global_z_offset_0.25_diagnostic | diagnostic | DIAG | 81.634 | diagnostic | pose,left_hand,right_hand,face | smooth/offset | 0.250 | 50/53 | score_valid:score_valid | 强整人 z 零点漂移不作为正常网页要求，只记录诊断边界。 |
| strong_sparse_hand_z_offset_0.18_every_4f_diagnostic | diagnostic | DIAG | 96.312 | diagnostic | left_hand,right_hand | sparse/offset | 0.180 | 13/53 | score_valid:score_valid | 强稀疏手部 z 跳点只记录诊断边界。 |
| smooth_global_z_scale_0.20 | positive | PASS | 81.408 | >= 70.0 | pose,left_hand,right_hand,face | smooth/scale | 0.200 | 50/53 | score_valid:score_valid | 整人 z 动态随时间在 0.8-1.2 倍之间平滑变化。 |
| smooth_hand_z_scale_0.20 | positive | PASS | 81.408 | >= 70.0 | left_hand,right_hand | smooth/scale | 0.200 | 50/53 | score_valid:score_valid | 双手局部 z 动态随时间平滑缩放，并重建手形特征。 |
| smooth_global_z_offset_0.08 | positive | PASS | 82.026 | >= 70.0 | pose,left_hand,right_hand,face | smooth/offset | 0.080 | 50/53 | score_valid:score_valid | 整人 z 坐标随时间平滑呼吸 8%，模拟 webcam/Holistic 深度零点漂移。 |
| smooth_hand_z_offset_0.06 | positive | PASS | 82.071 | >= 70.0 | left_hand,right_hand | smooth/offset | 0.060 | 50/53 | score_valid:score_valid | 双手 z 坐标随时间平滑漂移，模拟手离镜头距离估计轻微波动。 |
| right_hand_smooth_z_offset_0.05 | positive | PASS | 82.093 | >= 70.0 | right_hand | smooth/offset | 0.050 | 50/53 | score_valid:score_valid | 右手核心手随时间轻微 z 漂移，验证单手深度抖动不压低语义分。 |
| sparse_hand_z_offset_0.06_every_5f | positive | PASS | 98.021 | >= 70.0 | left_hand,right_hand | sparse/offset | 0.060 | 10/53 | score_valid:score_valid | 少量帧出现手部 z 跳动，模拟 tracker 深度闪断。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | pose,left_hand,right_hand,face | none/offset | 0.000 | 0/53 | score_valid:score_valid | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 组 | 模式 | 幅度 | 变化帧 | capture_quality | 说明 |
|---|---|---|---:|---|---|---|---:|---:|---|---|
| strong_global_z_offset_0.25_diagnostic | diagnostic | DIAG | 78.276 | diagnostic | pose,left_hand,right_hand,face | smooth/offset | 0.250 | 16/19 | score_valid:score_valid | 强整人 z 零点漂移不作为正常网页要求，只记录诊断边界。 |
| strong_hand_z_scale_0.55_diagnostic | diagnostic | DIAG | 87.976 | diagnostic | left_hand,right_hand | smooth/scale | 0.550 | 16/19 | score_valid:score_valid | 强手部 z 动态缩放会改变局部手形，只记录诊断边界。 |
| strong_sparse_hand_z_offset_0.18_every_4f_diagnostic | diagnostic | DIAG | 96.713 | diagnostic | left_hand,right_hand | sparse/offset | 0.180 | 4/19 | score_valid:score_valid | 强稀疏手部 z 跳点只记录诊断边界。 |
| smooth_global_z_offset_0.08 | positive | PASS | 79.288 | >= 70.0 | pose,left_hand,right_hand,face | smooth/offset | 0.080 | 16/19 | score_valid:score_valid | 整人 z 坐标随时间平滑呼吸 8%，模拟 webcam/Holistic 深度零点漂移。 |
| smooth_global_z_scale_0.20 | positive | PASS | 95.317 | >= 70.0 | pose,left_hand,right_hand,face | smooth/scale | 0.200 | 16/19 | score_valid:score_valid | 整人 z 动态随时间在 0.8-1.2 倍之间平滑变化。 |
| smooth_hand_z_scale_0.20 | positive | PASS | 95.317 | >= 70.0 | left_hand,right_hand | smooth/scale | 0.200 | 16/19 | score_valid:score_valid | 双手局部 z 动态随时间平滑缩放，并重建手形特征。 |
| sparse_hand_z_offset_0.06_every_5f | positive | PASS | 99.138 | >= 70.0 | left_hand,right_hand | sparse/offset | 0.060 | 4/19 | score_valid:score_valid | 少量帧出现手部 z 跳动，模拟 tracker 深度闪断。 |
| smooth_hand_z_offset_0.06 | positive | PASS | 99.260 | >= 70.0 | left_hand,right_hand | smooth/offset | 0.060 | 16/19 | score_valid:score_valid | 双手 z 坐标随时间平滑漂移，模拟手离镜头距离估计轻微波动。 |
| right_hand_smooth_z_offset_0.05 | positive | PASS | 99.639 | >= 70.0 | right_hand | smooth/offset | 0.050 | 16/19 | score_valid:score_valid | 右手核心手随时间轻微 z 漂移，验证单手深度抖动不压低语义分。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | pose,left_hand,right_hand,face | none/offset | 0.000 | 0/19 | score_valid:score_valid | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

## 说明

- 正向门只覆盖轻微平滑 z 呼吸、轻微手部 z 漂移和少量稀疏 z 跳动。
- 强 z scale/offset 或强稀疏跳点仅作诊断边界，因为它们可能真实破坏局部手形或双手关系。
- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。

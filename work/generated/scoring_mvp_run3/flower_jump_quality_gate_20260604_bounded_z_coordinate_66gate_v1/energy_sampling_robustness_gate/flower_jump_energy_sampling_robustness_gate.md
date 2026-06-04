# 花/跳运动能量选帧鲁棒性门

- 生成时间：`2026-06-04T05:16:51`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，按语义运动能量选择实际 query 帧集合并重建 motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：模拟前端高频候选帧经过 `selectEnergyCoverageFrames` 上传后的骨架帧集合，而不只是修改 frame_weights。

- 5080 状态：worker=`ready`，worker_pid=`811485`，reload_count=`17`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向选帧 | 诊断最低分 | 最弱诊断边界 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 78.766 | frontend_energy_coverage_12f | 4.901 | top_energy_no_endpoints_12f_diagnostic | 70.000 |
| 跳 | PASS | 74.690 | frontend_energy_coverage_6f | 6.558 | low_energy_with_endpoints_6f_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | query 帧 | 相位覆盖 | alignment | capture_quality | reason | 说明 |
|---|---|---|---:|---|---:|---:|---|---|---|---|
| top_energy_no_endpoints_12f_diagnostic | diagnostic | DIAG | 4.901 | diagnostic | 12 | 0.212 | full_sequence_with_action_window_diagnostics | semantic_mismatch | phase_order_disorder | 只取高运动峰值而不保证起止覆盖，记录前端选择失误边界。 |
| low_energy_with_endpoints_12f_diagnostic | diagnostic | DIAG | 5.314 | diagnostic | 12 | 1.000 | full_sequence_with_action_window_diagnostics | needs_recapture | flower_core_hand_presence_low | 只取低运动帧会丢失核心动态，作为坏选帧诊断边界。 |
| top_energy_with_endpoints_16f | diagnostic | DIAG | 26.639 | diagnostic | 16 | 1.000 | full_sequence_with_action_window_diagnostics | semantic_mismatch | phase_order_disorder | 只保留端点再偏向高运动峰值，记录缺相位覆盖的坏选帧边界。 |
| frontend_energy_coverage_12f | positive | PASS | 78.766 | >= 70.0 | 12 | 1.000 | full_sequence_with_action_window_diagnostics | score_valid | score_valid | 模拟前端推荐上传帧数：覆盖采样加高运动帧补齐。 |
| frontend_energy_coverage_16f | positive | PASS | 94.479 | >= 70.0 | 16 | 1.000 | full_sequence_with_action_window_diagnostics | score_valid | score_valid | 比最低推荐多少量帧的前端能量覆盖选择。 |
| frontend_energy_weighted_16f | positive | PASS | 94.516 | >= 70.0 | 16 | 1.000 | full_sequence_with_action_window_diagnostics | score_valid | score_valid | 同时模拟前端选帧和对应 upload frame_weights。 |
| frontend_energy_coverage_20f | positive | PASS | 95.232 | >= 70.0 | 20 | 1.000 | full_sequence_with_action_window_diagnostics | score_valid | score_valid | 帧数更充足时的前端能量覆盖选择。 |
| self_rebuilt | positive | PASS | 100.000 | >= 95.0 | 53 | 1.000 | full_sequence_with_action_window_diagnostics | score_valid | score_valid | 剥离基础组后重建完整序列，应保持近满分。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | query 帧 | 相位覆盖 | alignment | capture_quality | reason | 说明 |
|---|---|---|---:|---|---:|---:|---|---|---|---|
| low_energy_with_endpoints_6f_diagnostic | diagnostic | DIAG | 6.558 | diagnostic | 6 | 1.000 | semantic_action_window | semantic_mismatch | relation_direction_mismatch | 只取低运动帧会丢失核心动态，作为坏选帧诊断边界。 |
| top_energy_no_endpoints_6f_diagnostic | diagnostic | DIAG | 73.555 | diagnostic | 6 | 0.389 | semantic_action_window | score_valid | score_valid | 只取高运动峰值而不保证起止覆盖，记录前端选择失误边界。 |
| top_energy_with_endpoints_8f | diagnostic | DIAG | 80.525 | diagnostic | 8 | 1.000 | semantic_action_window | score_valid | score_valid | 只保留端点再偏向高运动峰值，记录缺相位覆盖的坏选帧边界。 |
| frontend_energy_coverage_6f | positive | PASS | 74.690 | >= 70.0 | 6 | 1.000 | semantic_action_window | score_valid | score_valid | 模拟前端推荐上传帧数：覆盖采样加高运动帧补齐。 |
| frontend_energy_coverage_8f | positive | PASS | 81.530 | >= 70.0 | 8 | 1.000 | semantic_action_window | score_valid | score_valid | 比最低推荐多少量帧的前端能量覆盖选择。 |
| frontend_energy_weighted_8f | positive | PASS | 81.561 | >= 70.0 | 8 | 1.000 | semantic_action_window | score_valid | score_valid | 同时模拟前端选帧和对应 upload frame_weights。 |
| frontend_energy_coverage_10f | positive | PASS | 83.198 | >= 70.0 | 10 | 1.000 | semantic_action_window | score_valid | score_valid | 帧数更充足时的前端能量覆盖选择。 |
| self_rebuilt | positive | PASS | 100.000 | >= 95.0 | 19 | 1.000 | semantic_action_window | score_valid | score_valid | 剥离基础组后重建完整序列，应保持近满分。 |

## 说明

- 该门补充 frame-count 和 frame_weights：它改变上传帧集合本身，再重新计算派生运动/关系特征。
- 诊断变体覆盖只取高运动峰值或低运动帧的坏选帧边界，不作为正常网页采样口径。
- 该门是合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。

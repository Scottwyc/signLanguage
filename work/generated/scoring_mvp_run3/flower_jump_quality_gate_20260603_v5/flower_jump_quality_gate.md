# 花/跳评分统一质量门

- 生成时间：`2026-06-03T03:40:50`
- 综合状态：`PASS`
- Web 样本根目录：`/data/WYC/signLanguage/work/generated/web_scoring_mvp`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：不重新运行 Holistic，不重启 5080；只读保存的 web/API Holistic JSON 和模板 Holistic JSON。

## 子门状态

| 子门 | 状态 | 返回码 | 报告 |
|---|---|---:|---|
| web_regression | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_v5/web_regression/flower_jump_web_regression.md` |
| web_confusion_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_v5/web_confusion_gate/flower_jump_web_confusion_gate.md` |
| discrimination_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_v5/discrimination_gate/flower_jump_discrimination_gate.md` |
| pose_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_v5/pose_robustness_gate/flower_jump_pose_robustness_gate.md` |
| frame_count_robustness_gate | PASS | 0 | `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_v5/frame_count_robustness_gate/flower_jump_frame_count_robustness_gate.md` |

## 网页保存样本回归

- replay 样本 `168`，错误 `0`；花/跳 diagnostics `149`，错误 `0`。
- 有效采集 `128`，有效正常+边界 `124`，有效低分 `4`，有效正常+边界率 `96.9%`。

| 词条 | 有效采集 | 正常+边界 | 有效低分 | 有效率 | 有效均分 |
|---|---:|---:|---:|---:|---:|
| 花 | 91 | 87 | 4 | 95.6% | 75.762 |
| 跳 | 37 | 37 | 0 | 100.0% | 76.677 |

## 网页保存样本花/跳交叉混淆门

- 样本 `149`，错误 `0`；eligible `124`，pass `124`，fail `0`。

| 目标词 | 样本 | eligible | pass | fail | 交叉最高 | margin 最低 | margin 均值 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 花 | 93 | 87 | 87 | 0 | 8.218 | 59.840 | 75.492 |
| 跳 | 56 | 37 | 37 | 0 | 41.535 | 29.317 | 55.519 |

## 负例判别门

| 目标词 | 状态 | 正例最低 | 最弱正例 | 负例最高 | 最强负例 | margin |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 80.311 | amplitude_0.85 | 32.047 | other_demo_谗_羡慕 | 48.263 |
| 跳 | PASS | 76.823 | amplitude_0.85 | 31.418 | fake_static_hold | 45.406 |

## 坐姿与镜头扰动门

| 目标词 | 状态 | 最低分 | 最弱扰动 | 门槛 |
|---|---|---:|---|---:|
| 花 | PASS | 80.446 | hand_jitter_small | 70.000 |
| 跳 | PASS | 93.015 | hand_jitter_small | 70.000 |

## 帧数与采样密度扰动门

| 目标词 | 状态 | 推荐最少帧 | 最低分 | 最弱采样 | 门槛 | 欠采样最低分 |
|---|---|---:|---:|---|---:|---:|
| 花 | PASS | 12 | 78.482 | uniform_12f | 70.000 | 32.284 |
| 跳 | PASS | 6 | 70.488 | drop_every_3_keep_ends | 70.000 | - |

## Marker 状态

- marker last_request_id：`web_20260602_233348_53e3df5d`
- marker 后新增样本：`0`
- marker 后新增花/跳样本：`0`

## 使用说明

- 修改 `score_holistic_sequence_mvp.py`、语义 profile、模板权重、score scaling 或对齐策略后，优先运行本脚本。
- 若本脚本 PASS，只能说明当前保存样本与合成鲁棒性门没有回退；真实用户网页测试仍需要新的摄像头样本和人工复核。

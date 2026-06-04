# 花/跳离线判别鲁棒性门

- 生成时间：`2026-06-03T18:46:26`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读已缓存 Holistic JSON，不调用 `/api/score`，不重启 Holistic。
- 目标：确认当前让 `花/跳` 网页样本得分正常的语义 floor 没有把其他 demo 或合成假动作误抬高。

- 5080 状态：worker=`ready`，worker_pid=`811485`，reload_count=`14`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`
- 正例最低分门槛：`75.0`
- 负例最高分门槛：`50.0`
- margin 门槛：`15.0`

| 目标词 | 状态 | 正例最低 | 最弱正例 | 负例最高 | 最强负例 | margin |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 80.311 | amplitude_0.85 | 33.735 | other_demo_谗_羡慕 | 46.575 |
| 跳 | PASS | 76.823 | amplitude_0.85 | 31.418 | fake_static_hold | 45.406 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`
- 标准帧数：`53`
- gate：`PASS`
- 正例最低分：`80.311`
- 负例最高分：`33.735`
- margin：`46.575`

| case | 类型 | 期望 | 分数 | query 帧数 |
|---|---|---|---:|---:|
| self | target_positive_variant | high | 100.000 | 53 |
| trim_both_10pct | target_positive_variant | high | 98.643 | 43 |
| trim_start_20pct | target_positive_variant | high | 98.614 | 42 |
| subsample_even | target_positive_variant | high | 95.777 | 27 |
| trim_end_20pct | target_positive_variant | high | 83.296 | 42 |
| amplitude_1.15 | target_positive_variant | high | 80.406 | 53 |
| amplitude_0.85 | target_positive_variant | high | 80.311 | 53 |
| other_demo_谗_羡慕 | other_demo_action | low | 33.735 | 32 |
| other_demo_指示 | other_demo_action | low | 27.200 | 30 |
| other_demo_朋友 | other_demo_action | low | 25.745 | 28 |
| other_demo_唱歌 | other_demo_action | low | 21.673 | 27 |
| fake_shuffle_frames | synthetic_fake_action | low | 21.528 | 53 |
| other_demo_跳 | other_demo_action | low | 15.330 | 19 |
| other_demo_香蕉 | other_demo_action | low | 14.613 | 42 |
| other_demo_汽车 | other_demo_action | low | 14.359 | 44 |
| fake_reverse_time | synthetic_fake_action | low | 14.024 | 53 |
| other_demo_月亮 | other_demo_action | low | 13.907 | 47 |
| other_demo_虎 | other_demo_action | low | 5.050 | 54 |
| fake_random_walk | synthetic_fake_action | low | 3.894 | 53 |
| fake_static_hold | synthetic_fake_action | low | 1.460 | 53 |
| fake_random_landmarks | synthetic_fake_action | low | 1.405 | 53 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`
- 标准帧数：`19`
- gate：`PASS`
- 正例最低分：`76.823`
- 负例最高分：`31.418`
- margin：`45.406`

| case | 类型 | 期望 | 分数 | query 帧数 |
|---|---|---|---:|---:|
| self | target_positive_variant | high | 100.000 | 19 |
| amplitude_1.15 | target_positive_variant | high | 95.519 | 19 |
| subsample_even | target_positive_variant | high | 81.486 | 10 |
| trim_end_20pct | target_positive_variant | high | 81.001 | 15 |
| trim_both_10pct | target_positive_variant | high | 80.985 | 15 |
| trim_start_20pct | target_positive_variant | high | 80.586 | 15 |
| amplitude_0.85 | target_positive_variant | high | 76.823 | 19 |
| fake_static_hold | synthetic_fake_action | low | 31.418 | 19 |
| fake_shuffle_frames | synthetic_fake_action | low | 21.538 | 19 |
| fake_reverse_time | synthetic_fake_action | low | 20.525 | 19 |
| other_demo_香蕉 | other_demo_action | low | 18.058 | 42 |
| other_demo_指示 | other_demo_action | low | 15.333 | 30 |
| other_demo_月亮 | other_demo_action | low | 13.834 | 47 |
| other_demo_朋友 | other_demo_action | low | 10.689 | 28 |
| other_demo_汽车 | other_demo_action | low | 9.384 | 44 |
| other_demo_唱歌 | other_demo_action | low | 9.019 | 27 |
| other_demo_虎 | other_demo_action | low | 7.760 | 54 |
| other_demo_花 | other_demo_action | low | 6.227 | 53 |
| other_demo_谗_羡慕 | other_demo_action | low | 4.844 | 32 |
| fake_random_landmarks | synthetic_fake_action | low | 0.146 | 19 |
| fake_random_walk | synthetic_fake_action | low | 0.122 | 19 |

## 使用说明

- 若该门失败，优先查看“最强负例”是否来自其他 demo，尤其是 `汽车/谗（羡慕）` 这类局部动作可能与 `跳` 的局部上升段相似的样本。
- 该门是 demo-only 工程 sanity gate，不能替代真实用户网页摄像头样本和人工标签校准。

# 花/跳核心手形幅度鲁棒性门

- 生成时间：`2026-06-04T04:30:24`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，调整右手核心手指的局部开合/展开幅度并重建 hand-shape/motion/relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：`花` 的温和开花幅度变化保持高分，严重不开花低分或语义失败；`跳` 的两指小人温和局部形变保持高分，严重形变只记录诊断边界。

- 5080 状态：worker=`ready`，pid=`811485`，reload_count=`16`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向核心形变 | 负向最高分 | 最强负向核心形变 | 诊断最低分 | 最弱诊断形变 | 门槛 |
|---|---|---:|---|---:|---|---:|---|---:|
| 花 | PASS | 79.334 | flower_opening_dynamic_0.75 | 49.353 | flower_opening_dynamic_0.45_negative | 77.639 | flower_opening_dynamic_0.60_diagnostic | 70.000 |
| 跳 | PASS | 77.830 | jump_two_finger_dynamic_1.15 | - | - | 82.090 | jump_two_finger_radial_0.45_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 操作 | factor | 改动点数 | opening | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---:|---:|---:|---|---|---|
| flower_opening_dynamic_0.60_diagnostic | diagnostic | DIAG | 77.639 | diagnostic | dynamic_local_amplitude | 0.600 | 600 | 0.387 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 接近不开花的边界只记录诊断，避免把边界幅度当成正式正例。 |
| flower_opening_dynamic_0.25_negative | negative | PASS | 31.541 | <= 45.0 或重采/语义失败 | dynamic_local_amplitude | 0.250 | 600 | 0.000 | semantic_mismatch:flower_opening_guard_failed | short_visible_core:query_not_short_core_capture | 几乎没有手指张开/绽放动态，不能当作完整“花”通过。 |
| flower_opening_dynamic_0.45_negative | negative | PASS | 49.353 | <= 45.0 或重采/语义失败 | dynamic_local_amplitude | 0.450 | 600 | 0.089 | semantic_mismatch:flower_opening_guard_failed | short_visible_core:query_not_short_core_capture | 绽放动态大幅塌缩，应低分或进入 flower_opening_guard_failed。 |
| flower_opening_dynamic_0.75 | positive | PASS | 79.334 | >= 70.0 | dynamic_local_amplitude | 0.750 | 600 | 0.752 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 右手绽放局部动态幅度压缩到 75%，覆盖用户开合偏小但清晰的情况。 |
| flower_tip_spread_radial_1.20 | positive | PASS | 79.576 | >= 70.0 | radial_local_spread | 1.200 | 200 | 1.000 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 五个指尖展开半径略大，仍应保持正常或边界评分。 |
| flower_tip_spread_radial_0.85 | positive | PASS | 79.977 | >= 70.0 | radial_local_spread | 0.850 | 200 | 0.903 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 五个指尖展开半径略小，仍保留手指张开/绽放语义。 |
| flower_opening_dynamic_1.20 | positive | PASS | 80.071 | >= 70.0 | dynamic_local_amplitude | 1.200 | 600 | 1.000 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 右手绽放局部动态幅度放大到 120%，覆盖开合偏大的情况。 |
| flower_opening_dynamic_0.85 | positive | PASS | 80.380 | >= 70.0 | dynamic_local_amplitude | 0.850 | 600 | 0.854 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 右手绽放局部动态幅度压缩到 85%，仍应保持可评分。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | dynamic_local_amplitude | 1.000 | 0 | 0.985 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 剥离基础组后重建 hand-shape/motion/relation 特征，应保持近满分。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 操作 | factor | 改动点数 | opening | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---:|---:|---:|---|---|---|
| jump_two_finger_radial_0.45_diagnostic | diagnostic | DIAG | 82.090 | diagnostic | radial_local_spread | 0.450 | 136 | - | score_valid:score_valid | action_window_net:used | 严重两指局部展开压缩只记录诊断，不作为当前硬负门。 |
| jump_two_finger_dynamic_0.45_diagnostic | diagnostic | DIAG | 89.036 | diagnostic | dynamic_local_amplitude | 0.450 | 136 | - | score_valid:score_valid | action_window_net:used | 严重两指局部动态压缩只记录当前边界；硬负例由遮挡/裁切/关系门覆盖。 |
| jump_two_finger_dynamic_1.15 | positive | PASS | 77.830 | >= 70.0 | dynamic_local_amplitude | 1.150 | 136 | - | score_valid:score_valid | action_window_net:used | 右手食指/中指小人的局部动态幅度略大，仍应保持可评分。 |
| jump_two_finger_radial_1.15 | positive | PASS | 91.510 | >= 70.0 | radial_local_spread | 1.150 | 136 | - | score_valid:score_valid | action_window_net:used | 两指小人局部展开略放，核心关系仍应保持正常。 |
| jump_two_finger_radial_0.90 | positive | PASS | 93.881 | >= 70.0 | radial_local_spread | 0.900 | 136 | - | score_valid:score_valid | action_window_net:used | 两指小人局部展开略收，核心两指和左手地面关系仍保留。 |
| jump_two_finger_dynamic_0.80 | positive | PASS | 95.888 | >= 70.0 | dynamic_local_amplitude | 0.800 | 136 | - | score_valid:score_valid | action_window_net:used | 右手食指/中指小人的局部动态幅度略小，双手跳跃关系仍清晰。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | dynamic_local_amplitude | 1.000 | 0 | - | score_valid:score_valid | action_window_net:used | 剥离基础组后重建 hand-shape/motion/relation 特征，应保持近满分。 |

## 说明

- `花` 的负向门允许 capture_quality 证明 `flower_opening_guard_failed`，因为语义失败比单一分数阈值更可靠。
- `跳` 的严重两指形变目前只作诊断，不放宽也不新增硬负例；硬保护仍由遮挡、裁切、手角色、关系几何和相位顺序等门承担。
- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。

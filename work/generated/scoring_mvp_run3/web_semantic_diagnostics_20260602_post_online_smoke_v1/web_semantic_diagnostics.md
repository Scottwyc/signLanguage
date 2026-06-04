# 网页样本语义诊断

- 生成时间：`2026-06-02T23:35:40`
- Web 样本根目录：`work/generated/web_scoring_mvp`
- 语义 profile：`work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 词条过滤：`花, 跳`
- 标准库覆盖：`work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 口径：query 复用保存的网页/API Holistic JSON，standard 改用当前标准库，模拟当前后端在线评分；不重新运行 Holistic。
- 分段：`normal_like >= 75`，`60 <= borderline < 75`，`low < 60`；仍是工程诊断口径，不是正式用户阈值。

## 总览

- 样本数：`149`
- 错误数：`0`
- 均分：`64.865`
- 中位数：`77.610`
- 分段计数：`{'borderline': 23, 'normal_like': 97, 'low': 29}`
- 诊断计数：`{'flower_core_accepted': 83, 'flower_core_hand_presence_low': 5, 'flower_opening_guard_failed': 5, 'jump_core_accepted': 37, 'jump_two_hand_presence_low': 19}`
- 采集质量计数：`{'score_valid': 120, 'needs_recapture': 25, 'semantic_mismatch': 4}`
- 有效采集口径：可评分样本 `124`，正常+边界 `120`，低分 `4`，正常+边界率 `96.8%`。

## 分词条

| 词条 | 样本数 | 正常 | 边界 | 低分 | 均分 | 中位数 | 最低 | 最高 | 核心覆盖均值 | L/R 覆盖均值 | 采集质量 | 主要诊断 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| 花 | 93 | 76 | 7 | 10 | 72.611 | 78.392 | 2.913 | 80.784 | 0.708 | 0.016/0.702 | score_valid:83, needs_recapture:6, semantic_mismatch:4 | flower_core_accepted:83, flower_core_hand_presence_low:5, flower_opening_guard_failed:5 |
| 跳 | 56 | 21 | 16 | 19 | 52.002 | 71.809 | 0.833 | 88.577 | 0.697 | 0.617/0.728 | score_valid:37, needs_recapture:19 | jump_core_accepted:37, jump_two_hand_presence_low:19 |

## 有效采集口径

- 这里排除 `needs_recapture`，只看核心关键点已经足够入画、可以解释为动作语义评分的样本。

| 词条 | 原始样本 | 建议重采 | 有效采集 | 正常+边界 | 低分 | 正常+边界率 | 有效均分 | 语义不匹配 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 花 | 93 | 6 | 87 | 83 | 4 | 95.4% | 75.550 | 4 |
| 跳 | 56 | 19 | 37 | 37 | 0 | 100.0% | 76.677 | 0 |

## 语义不匹配明细

- 这些样本核心关键点已足够入画，但未满足词条核心语义；通常不应通过放宽阈值抬高。

| request | 词条 | 分数 | 诊断 | floor 原因 | 方向余弦 | 纵向分数 | 幅度比 | 水平/纵向 | 关系覆盖 |
|---|---|---:|---|---|---:|---:|---:|---:|---:|
| web_20260602_233301_233b8215 | 花 | 2.913 | flower_opening_guard_failed | opening_guard_too_weak | - | - | - | - | - |
| web_20260523_062341_afa8c368 | 花 | 14.572 | flower_opening_guard_failed | query_not_short_core_capture | - | - | - | - | - |
| web_20260522_232244_45d260ed | 花 | 48.531 | flower_opening_guard_failed | query_not_short_core_capture | - | - | - | - | - |
| web_20260523_031345_3b07a113 | 花 | 54.425 | flower_opening_guard_failed | query_not_short_core_capture | - | - | - | - | - |

## 跳语义 floor 接收明细

- `action_window_net` 表示动作窗口起止净方向直接通过；`full_sequence_local_relation_segment` 表示完整序列中检测到局部双手弹跳段，并通过右手食指/中指手形守卫。
- 来源分布：`{'full_sequence_local_relation_segment': 7, 'action_window_net': 30}`

| request | 分数 | 分段 | 来源 | 方向余弦 | 幅度比 | 水平/纵向 | 段覆盖 | 段帧 | 两指手形 | fallback 原因 |
|---|---:|---|---|---:|---:|---:|---:|---|---:|---|
| web_20260523_063109_8727dac1 | 65.191 | borderline | action_window_net | 0.699 | 3.814 | 0.192 | - | 14-23 | - | - |
| web_20260523_031219_0da0bd96 | 66.510 | borderline | action_window_net | 0.723 | 4.748 | 0.158 | - | 19-29 | - | - |
| web_20260523_044358_00db9d4d | 68.517 | borderline | action_window_net | 0.762 | 5.442 | 0.098 | - | 26-32 | - | - |
| web_20260523_021622_26666615 | 70.084 | borderline | action_window_net | 0.696 | 4.597 | 0.185 | - | 28-37 | - | - |
| web_20260602_233302_d92c0ce2 | 70.661 | borderline | action_window_net | 0.681 | 1.291 | 0.222 | - | 14-22 | - | - |
| web_20260523_044336_5d15d099 | 70.853 | borderline | action_window_net | 0.820 | 3.250 | 0.003 | - | 31-40 | - | - |
| web_20260523_063026_c2f04725 | 71.075 | borderline | action_window_net | 0.740 | 4.613 | 0.130 | - | 34-40 | - | - |
| web_20260523_031235_d0de0d44 | 72.543 | borderline | action_window_net | 0.680 | 3.461 | 0.218 | - | 8-16 | - | - |
| web_20260523_021006_aef545ce | 72.870 | borderline | action_window_net | 0.747 | 5.501 | 0.117 | - | 41-57 | - | - |
| web_20260523_010234_e2d59e5e | 73.052 | borderline | action_window_net | 0.814 | 4.978 | 0.003 | - | 32-44 | - | - |
| web_20260523_041735_ea1bbaa6 | 73.255 | borderline | action_window_net | 0.714 | 4.625 | 0.171 | - | 33-49 | - | - |
| web_20260523_063052_fc94e4f7 | 75.147 | normal_like | action_window_net | 0.764 | 3.728 | 0.097 | - | 36-44 | - | - |
| web_20260602_214010_3f951c51 | 75.325 | normal_like | action_window_net | 0.771 | 3.924 | 0.062 | - | 33-40 | - | - |
| web_20260523_044323_2eb9eb7e | 75.484 | normal_like | action_window_net | 0.778 | 4.065 | 0.073 | - | 29-40 | - | - |
| web_20260523_052731_8f51941f | 75.933 | normal_like | action_window_net | 0.790 | 3.925 | 0.044 | - | 30-40 | - | - |
| web_20260523_053241_5fbbf9c7 | 75.983 | normal_like | action_window_net | 0.801 | 4.951 | 0.037 | - | 33-44 | - | - |
| web_20260523_031134_8688f93f | 77.610 | normal_like | action_window_net | 0.989 | 1.268 | 0.672 | - | 21-37 | - | - |
| web_20260523_052715_1ad3c2d2 | 78.026 | normal_like | action_window_net | 0.816 | 1.725 | 0.018 | - | 32-44 | - | - |
| web_20260523_031247_f927176a | 82.062 | normal_like | action_window_net | 0.971 | 3.184 | 0.420 | - | 8-24 | - | - |
| web_20260523_005941_0ec0ccab | 82.064 | normal_like | action_window_net | 0.974 | 3.443 | 1.093 | - | 7-13 | - | - |
| web_20260523_010004_7eaf7ee3 | 83.040 | normal_like | action_window_net | 0.982 | 2.111 | 0.452 | - | 7-13 | - | - |
| web_20260523_015650_c394e067 | 84.923 | normal_like | action_window_net | 0.999 | 0.976 | 0.642 | - | 6-22 | - | - |
| web_20260523_015727_2cb1fbe6 | 84.948 | normal_like | action_window_net | 0.999 | 1.016 | 0.724 | - | 6-22 | - | - |
| web_20260523_020555_09843ad1 | 84.948 | normal_like | action_window_net | 0.999 | 1.016 | 0.724 | - | 6-22 | - | - |
| web_20260523_030625_c3f72e11 | 84.965 | normal_like | action_window_net | 0.999 | 1.009 | 0.648 | - | 6-22 | - | - |
| web_20260523_031129_bd3988e8 | 84.974 | normal_like | action_window_net | 1.000 | 1.008 | 0.669 | - | 6-22 | - | - |
| web_20260523_041350_ad02e9e5 | 84.974 | normal_like | action_window_net | 1.000 | 1.008 | 0.669 | - | 6-22 | - | - |
| web_20260523_041447_f7341789 | 84.974 | normal_like | action_window_net | 1.000 | 1.008 | 0.669 | - | 6-22 | - | - |
| web_20260523_043446_cbecd916 | 84.974 | normal_like | action_window_net | 1.000 | 1.008 | 0.669 | - | 6-22 | - | - |
| web_20260602_233348_53e3df5d | 88.577 | normal_like | action_window_net | 0.993 | 1.006 | 0.534 | - | 6-22 | - | - |
| web_20260523_011122_fb34e3e5 | 69.526 | borderline | full_sequence_local_relation_segment | 0.954 | 2.862 | 0.345 | 0.500 | 10-20 | 1.103 | weak_same_direction_vertical_jump |
| web_20260523_044018_960618af | 71.072 | borderline | full_sequence_local_relation_segment | 0.983 | 3.881 | 0.013 | 0.800 | 9-45 | 1.391 | relation_direction_mismatch |
| web_20260523_024000_dd35e1bb | 72.943 | borderline | full_sequence_local_relation_segment | 0.976 | 3.485 | 0.009 | 0.714 | 19-47 | 1.483 | relation_direction_mismatch |
| web_20260523_001048_5bcb9948 | 74.194 | borderline | full_sequence_local_relation_segment | 0.999 | 5.710 | 0.177 | 0.667 | 5-10 | 1.237 | relation_direction_mismatch |
| web_20260523_022509_a44cb853 | 74.915 | borderline | full_sequence_local_relation_segment | 0.983 | 2.045 | 0.019 | 0.737 | 23-44 | 1.492 | relation_direction_mismatch |
| web_20260523_044135_12fbd5bc | 75.212 | normal_like | full_sequence_local_relation_segment | 0.976 | 5.152 | 0.038 | 0.700 | 11-37 | 1.342 | relation_direction_mismatch |
| web_20260523_001152_83546751 | 75.663 | normal_like | full_sequence_local_relation_segment | 0.955 | 1.959 | 0.103 | 0.857 | 7-13 | 1.403 | relation_direction_mismatch |

## 低分原因

### 花

- 低分数：`10`
- 诊断分布：`{'flower_core_hand_presence_low': 5, 'flower_opening_guard_failed': 5}`

| request | 分数 | 采集质量 | 诊断 | floor 原因 | L/R 覆盖 | 花-张开 | 双手关系 | 右手形 |
|---|---:|---|---|---|---:|---:|---:|---:|
| web_20260602_233301_233b8215 | 2.913 | semantic_mismatch | flower_opening_guard_failed | opening_guard_too_weak | 0.000/1.000 | 0.052 | 0.000 | 0.000 |
| web_20260522_231259_51a8c719 | 4.202 | needs_recapture | flower_core_hand_presence_low | insufficient_core_hand_presence | 0.000/0.500 | 0.450 | 0.000 | 0.000 |
| web_20260522_225823_46498d30 | 13.248 | needs_recapture | flower_core_hand_presence_low | insufficient_core_hand_presence | 0.000/0.467 | 1.000 | 0.000 | 0.000 |
| web_20260523_062341_afa8c368 | 14.572 | semantic_mismatch | flower_opening_guard_failed | query_not_short_core_capture | 1.000/0.450 | 0.000 | 0.000 | 0.000 |
| web_20260602_212933_7ad54f26 | 14.863 | needs_recapture | flower_opening_guard_failed | insufficient_core_hand_presence | 0.000/0.000 | 0.000 | 0.000 | 0.000 |
| web_20260602_213030_368950ee | 44.503 | needs_recapture | flower_core_hand_presence_low | query_not_short_core_capture | 0.040/0.480 | 1.000 | 0.000 | 0.004 |
| web_20260522_232244_45d260ed | 48.531 | semantic_mismatch | flower_opening_guard_failed | query_not_short_core_capture | 0.000/0.633 | 0.122 | 0.000 | 0.000 |
| web_20260523_032325_7e7b2476 | 51.245 | needs_recapture | flower_core_hand_presence_low | query_not_short_core_capture | 0.000/0.500 | 1.000 | 0.000 | 0.000 |
| web_20260523_052801_95c97bce | 51.950 | needs_recapture | flower_core_hand_presence_low | query_not_short_core_capture | 0.033/0.567 | 0.873 | 0.000 | 0.000 |
| web_20260523_031345_3b07a113 | 54.425 | semantic_mismatch | flower_opening_guard_failed | query_not_short_core_capture | 0.000/0.767 | 0.086 | 0.000 | 0.000 |

### 跳

- 低分数：`19`
- 诊断分布：`{'jump_two_hand_presence_low': 19}`

| request | 分数 | 采集质量 | 诊断 | floor 原因 | L/R 覆盖 | 花-张开 | 双手关系 | 右手形 |
|---|---:|---|---|---|---:|---:|---:|---:|
| web_20260523_031147_55d51ab9 | 0.833 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.500/0.600 | - | 0.268 | 0.164 |
| web_20260602_214656_3fae071b | 1.354 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.040/0.480 | - | 0.000 | 0.214 |
| web_20260523_053940_f86fc279 | 2.202 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.440/0.760 | - | 0.286 | 0.283 |
| web_20260523_053345_da4d1ec9 | 2.366 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.000/0.760 | - | 0.000 | 0.266 |
| web_20260523_001113_b486eb41 | 2.501 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.200/0.600 | - | 0.000 | 0.288 |
| web_20260523_053254_bd7f1d1c | 3.045 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.520/0.880 | - | 0.501 | 0.270 |
| web_20260523_011135_5967dd5a | 3.111 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.467/0.700 | - | 0.481 | 0.288 |
| web_20260523_053309_28821cfd | 3.491 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.440/0.840 | - | 0.428 | 0.278 |
| web_20260523_053401_8934d89a | 3.643 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.000/0.840 | - | 0.000 | 0.264 |
| web_20260523_010014_049faf7d | 3.680 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.467/0.200 | - | 0.320 | 0.280 |
| web_20260523_024025_9c6cf572 | 3.769 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.300/0.600 | - | 0.353 | 0.271 |
| web_20260523_044203_20778933 | 4.186 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.633/0.767 | - | 0.238 | 0.256 |
| web_20260523_063002_0aa1419e | 4.240 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.480/0.840 | - | 0.124 | 0.282 |
| web_20260523_005953_cdf0697d | 4.450 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.400/0.400 | - | 0.298 | 0.282 |
| web_20260523_021604_9c415199 | 4.784 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.133/0.717 | - | 0.000 | 0.265 |
| web_20260523_001100_dea381ee | 4.973 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.467/0.533 | - | 0.445 | 0.289 |
| web_20260523_024037_ff5b3fb5 | 6.227 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.500/0.833 | - | 0.265 | 0.273 |
| web_20260523_020951_6ff2657c | 7.283 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.267/0.667 | - | 0.093 | 0.283 |
| web_20260523_063015_4017237e | 8.919 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.640/0.840 | - | 0.151 | 0.282 |

## 最新样本

| request | 词条 | 帧数 | 分数 | 分段 | 采集质量 | 诊断 | L/R 覆盖 | 对齐 |
|---|---|---:|---:|---|---|---|---:|---|
| web_20260523_062353_2b6f64cd | 花 | 25 | 79.530 | normal_like | score_valid | flower_core_accepted | 0.000/0.760 | full_sequence_with_action_window_diagnostics |
| web_20260523_062406_09525c5f | 花 | 25 | 80.022 | normal_like | score_valid | flower_core_accepted | 0.000/0.720 | full_sequence_with_action_window_diagnostics |
| web_20260523_062420_5aea4dd9 | 花 | 25 | 78.624 | normal_like | score_valid | flower_core_accepted | 0.000/0.800 | full_sequence_with_action_window_diagnostics |
| web_20260523_062433_e3e870b6 | 花 | 25 | 80.007 | normal_like | score_valid | flower_core_accepted | 0.000/0.680 | full_sequence_with_action_window_diagnostics |
| web_20260523_062644_9a457871 | 花 | 25 | 79.941 | normal_like | score_valid | flower_core_accepted | 0.000/0.680 | full_sequence_with_action_window_diagnostics |
| web_20260523_063002_0aa1419e | 跳 | 25 | 4.240 | low | needs_recapture | jump_two_hand_presence_low | 0.480/0.840 | semantic_action_window |
| web_20260523_063015_4017237e | 跳 | 25 | 8.919 | low | needs_recapture | jump_two_hand_presence_low | 0.640/0.840 | semantic_action_window |
| web_20260523_063026_c2f04725 | 跳 | 25 | 71.075 | borderline | score_valid | jump_core_accepted | 0.640/0.920 | semantic_action_window |
| web_20260523_063052_fc94e4f7 | 跳 | 25 | 75.147 | normal_like | score_valid | jump_core_accepted | 0.720/0.840 | semantic_action_window |
| web_20260523_063109_8727dac1 | 跳 | 25 | 65.191 | borderline | score_valid | jump_core_accepted | 0.600/1.000 | semantic_action_window |
| web_20260523_063159_324827f7 | 花 | 15 | 78.463 | normal_like | score_valid | flower_core_accepted | 0.000/0.667 | full_sequence_with_action_window_diagnostics |
| web_20260523_063217_bd40ee0c | 花 | 30 | 79.244 | normal_like | score_valid | flower_core_accepted | 0.000/0.733 | full_sequence_with_action_window_diagnostics |
| web_20260523_063230_6a3bad1f | 花 | 25 | 79.674 | normal_like | score_valid | flower_core_accepted | 0.000/0.680 | full_sequence_with_action_window_diagnostics |
| web_20260523_071212_4547d033 | 花 | 25 | 79.560 | normal_like | score_valid | flower_core_accepted | 0.000/0.600 | full_sequence_with_action_window_diagnostics |
| web_20260523_071306_071a2172 | 花 | 15 | 76.178 | normal_like | score_valid | flower_core_accepted | 0.067/0.600 | full_sequence_with_action_window_diagnostics |
| web_20260523_071320_415e2975 | 花 | 15 | 78.392 | normal_like | score_valid | flower_core_accepted | 0.000/0.800 | full_sequence_with_action_window_diagnostics |
| web_20260523_071339_f3f432d2 | 花 | 25 | 79.410 | normal_like | score_valid | flower_core_accepted | 0.000/0.680 | full_sequence_with_action_window_diagnostics |
| web_20260523_071415_2505a91e | 花 | 25 | 79.116 | normal_like | score_valid | flower_core_accepted | 0.040/0.800 | full_sequence_with_action_window_diagnostics |
| web_20260602_212933_7ad54f26 | 花 | 15 | 14.863 | low | needs_recapture | flower_opening_guard_failed | 0.000/0.000 | full_sequence_with_action_window_diagnostics |
| web_20260602_212951_e1173da1 | 花 | 15 | 77.625 | normal_like | score_valid | flower_core_accepted | 0.000/0.800 | full_sequence_with_action_window_diagnostics |
| web_20260602_213015_411a2ecd | 花 | 30 | 78.861 | normal_like | score_valid | flower_core_accepted | 0.000/0.633 | full_sequence_with_action_window_diagnostics |
| web_20260602_213030_368950ee | 花 | 25 | 44.503 | low | needs_recapture | flower_core_hand_presence_low | 0.040/0.480 | full_sequence_with_action_window_diagnostics |
| web_20260602_213050_ec3d0907 | 花 | 25 | 79.517 | normal_like | score_valid | flower_core_accepted | 0.000/0.720 | full_sequence_with_action_window_diagnostics |
| web_20260602_213918_4947c25e | 花 | 25 | 79.707 | normal_like | score_valid | flower_core_accepted | 0.000/0.720 | full_sequence_with_action_window_diagnostics |
| web_20260602_214010_3f951c51 | 跳 | 25 | 75.325 | normal_like | score_valid | jump_core_accepted | 0.600/0.880 | semantic_action_window |
| web_20260602_214656_3fae071b | 跳 | 25 | 1.354 | low | needs_recapture | jump_two_hand_presence_low | 0.040/0.480 | semantic_action_window |
| web_20260602_233301_233b8215 | 花 | 6 | 2.913 | low | semantic_mismatch | flower_opening_guard_failed | 0.000/1.000 | full_sequence_with_action_window_diagnostics |
| web_20260602_233302_d92c0ce2 | 跳 | 9 | 70.661 | borderline | score_valid | jump_core_accepted | 0.889/1.000 | semantic_action_window |
| web_20260602_233343_899e6970 | 花 | 53 | 76.899 | normal_like | score_valid | flower_core_accepted | 0.000/0.792 | full_sequence_with_action_window_diagnostics |
| web_20260602_233348_53e3df5d | 跳 | 19 | 88.577 | normal_like | score_valid | jump_core_accepted | 0.842/0.895 | semantic_action_window |

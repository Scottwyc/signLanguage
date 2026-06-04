# 网页样本语义诊断

- 生成时间：`2026-06-02T22:19:53`
- Web 样本根目录：`/data/WYC/signLanguage/work/generated/web_scoring_mvp`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 词条过滤：`花, 跳`
- 口径：复用保存的 `standard_json/query_json` 复算，不重新运行 Holistic。
- 分段：`normal_like >= 75`，`60 <= borderline < 75`，`low < 60`；仍是工程诊断口径，不是正式用户阈值。

## 总览

- 样本数：`145`
- 错误数：`0`
- 均分：`61.815`
- 中位数：`78.026`
- 分段计数：`{'normal_like': 92, 'low': 35, 'borderline': 18}`
- 诊断计数：`{'flower_core_accepted': 81, 'flower_core_hand_presence_low': 5, 'flower_opening_guard_failed': 4, 'jump_core_accepted': 29, 'jump_two_hand_presence_low': 19, 'jump_relation_direction_mismatch': 6, 'flower_low_other': 1}`
- 采集质量计数：`{'score_valid': 111, 'needs_recapture': 25, 'semantic_mismatch': 9}`

## 分词条

| 词条 | 样本数 | 正常 | 边界 | 低分 | 均分 | 中位数 | 最低 | 最高 | 核心覆盖均值 | L/R 覆盖均值 | 采集质量 | 主要诊断 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| 花 | 91 | 74 | 7 | 10 | 72.825 | 78.648 | 7.289 | 80.367 | 0.704 | 0.017/0.698 | score_valid:82, needs_recapture:6, semantic_mismatch:3 | flower_core_accepted:81, flower_core_hand_presence_low:5, flower_opening_guard_failed:4 |
| 跳 | 54 | 18 | 11 | 25 | 43.261 | 66.206 | 0.833 | 84.974 | 0.691 | 0.608/0.720 | score_valid:29, needs_recapture:19, semantic_mismatch:6 | jump_core_accepted:29, jump_two_hand_presence_low:19, jump_relation_direction_mismatch:6 |

## 低分原因

### 花

- 低分数：`10`
- 诊断分布：`{'flower_core_hand_presence_low': 5, 'flower_opening_guard_failed': 4, 'flower_low_other': 1}`

| request | 分数 | 采集质量 | 诊断 | floor 原因 | L/R 覆盖 | 花-张开 | 双手关系 | 右手形 |
|---|---:|---|---|---|---:|---:|---:|---:|
| web_20260522_231259_51a8c719 | 7.289 | needs_recapture | flower_core_hand_presence_low | - | 0.000/0.500 | 0.450 | 0.000 | 0.000 |
| web_20260523_062341_afa8c368 | 14.572 | semantic_mismatch | flower_opening_guard_failed | - | 1.000/0.450 | 0.000 | 0.000 | 0.000 |
| web_20260602_212933_7ad54f26 | 14.863 | needs_recapture | flower_opening_guard_failed | - | 0.000/0.000 | 0.000 | 0.000 | 0.000 |
| web_20260523_010203_88bdaf53 | 17.462 | score_valid | flower_low_other | - | 0.133/0.633 | 1.000 | 0.000 | 0.000 |
| web_20260522_225823_46498d30 | 35.284 | needs_recapture | flower_core_hand_presence_low | - | 0.000/0.467 | 1.000 | 0.000 | 0.000 |
| web_20260522_232244_45d260ed | 40.392 | semantic_mismatch | flower_opening_guard_failed | - | 0.000/0.633 | 0.122 | 0.000 | 0.000 |
| web_20260602_213030_368950ee | 44.503 | needs_recapture | flower_core_hand_presence_low | - | 0.040/0.480 | 1.000 | 0.000 | 0.004 |
| web_20260523_032325_7e7b2476 | 51.245 | needs_recapture | flower_core_hand_presence_low | - | 0.000/0.500 | 1.000 | 0.000 | 0.000 |
| web_20260523_052801_95c97bce | 51.950 | needs_recapture | flower_core_hand_presence_low | - | 0.033/0.567 | 0.873 | 0.000 | 0.000 |
| web_20260523_031345_3b07a113 | 54.425 | semantic_mismatch | flower_opening_guard_failed | - | 0.000/0.767 | 0.086 | 0.000 | 0.000 |

### 跳

- 低分数：`25`
- 诊断分布：`{'jump_two_hand_presence_low': 19, 'jump_relation_direction_mismatch': 6}`

| request | 分数 | 采集质量 | 诊断 | floor 原因 | L/R 覆盖 | 花-张开 | 双手关系 | 右手形 |
|---|---:|---|---|---|---:|---:|---:|---:|
| web_20260523_031147_55d51ab9 | 0.833 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.500/0.600 | - | 0.268 | 0.164 |
| web_20260523_010014_049faf7d | 1.070 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.467/0.200 | - | 0.139 | 0.179 |
| web_20260523_001113_b486eb41 | 1.239 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.200/0.600 | - | 0.000 | 0.286 |
| web_20260523_005953_cdf0697d | 1.346 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.400/0.400 | - | 0.101 | 0.178 |
| web_20260602_214656_3fae071b | 1.354 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.040/0.480 | - | 0.000 | 0.214 |
| web_20260523_053940_f86fc279 | 2.202 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.440/0.760 | - | 0.286 | 0.283 |
| web_20260523_053345_da4d1ec9 | 2.366 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.000/0.760 | - | 0.000 | 0.266 |
| web_20260523_053254_bd7f1d1c | 3.045 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.520/0.880 | - | 0.501 | 0.270 |
| web_20260523_011135_5967dd5a | 3.176 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.467/0.700 | - | 0.497 | 0.289 |
| web_20260523_053309_28821cfd | 3.491 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.440/0.840 | - | 0.428 | 0.278 |
| web_20260523_053401_8934d89a | 3.643 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.000/0.840 | - | 0.000 | 0.264 |
| web_20260523_024025_9c6cf572 | 3.769 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.300/0.600 | - | 0.353 | 0.271 |
| web_20260523_001100_dea381ee | 3.844 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.467/0.533 | - | 0.407 | 0.282 |
| web_20260523_024000_dd35e1bb | 4.123 | semantic_mismatch | jump_relation_direction_mismatch | relation_direction_mismatch | 0.900/0.700 | - | 0.457 | 0.239 |
| web_20260523_044203_20778933 | 4.186 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.633/0.767 | - | 0.238 | 0.256 |
| web_20260523_063002_0aa1419e | 4.240 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.480/0.840 | - | 0.124 | 0.282 |
| web_20260523_044018_960618af | 4.328 | semantic_mismatch | jump_relation_direction_mismatch | relation_direction_mismatch | 0.767/0.767 | - | 0.552 | 0.235 |
| web_20260523_021604_9c415199 | 4.784 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.133/0.717 | - | 0.000 | 0.265 |
| web_20260523_044135_12fbd5bc | 4.983 | semantic_mismatch | jump_relation_direction_mismatch | relation_direction_mismatch | 0.700/0.767 | - | 0.448 | 0.245 |
| web_20260523_024037_ff5b3fb5 | 6.227 | needs_recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.500/0.833 | - | 0.265 | 0.273 |

## 最新样本

| request | 词条 | 帧数 | 分数 | 分段 | 采集质量 | 诊断 | L/R 覆盖 | 对齐 |
|---|---|---:|---:|---|---|---|---:|---|
| web_20260523_053345_da4d1ec9 | 跳 | 25 | 2.366 | low | needs_recapture | jump_two_hand_presence_low | 0.000/0.760 | semantic_action_window |
| web_20260523_053401_8934d89a | 跳 | 25 | 3.643 | low | needs_recapture | jump_two_hand_presence_low | 0.000/0.840 | semantic_action_window |
| web_20260523_053940_f86fc279 | 跳 | 25 | 2.202 | low | needs_recapture | jump_two_hand_presence_low | 0.440/0.760 | semantic_action_window |
| web_20260523_062341_afa8c368 | 花 | 20 | 14.572 | low | semantic_mismatch | flower_opening_guard_failed | 1.000/0.450 | full_sequence_with_action_window_diagnostics |
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

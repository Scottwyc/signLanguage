# 网页样本语义诊断

- 生成时间：`2026-06-03T06:54:00`
- Web 样本根目录：`/data/WYC/signLanguage/work/generated/web_scoring_mvp`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 词条过滤：`花, 跳`
- 标准库覆盖：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 口径：query 复用保存的网页/API Holistic JSON，standard 改用当前标准库，模拟当前后端在线评分；不重新运行 Holistic。
- 分段：`normal_like >= 75`，`60 <= borderline < 75`，`low < 60`；仍是工程诊断口径，不是正式用户阈值。

## 总览

- 样本数：`149`
- 错误数：`0`
- 均分：`53.264`
- 中位数：`77.239`
- 分段计数：`{'borderline': 5, 'normal_like': 87, 'low': 57}`
- 诊断计数：`{'flower_core_accepted': 83, 'flower_core_hand_presence_low': 1, 'flower_opening_guard_failed': 9, 'jump_two_hand_presence_low': 37, 'jump_core_accepted': 9, 'jump_low_other': 10}`
- 处置计数：`{'borderline_review': 5, 'normal': 87, 'recapture': 21, 'semantic_mismatch': 36}`
- 采集质量计数：`{'score_valid': 92, 'needs_recapture': 21, 'semantic_mismatch': 36}`
- 有效采集口径：可评分样本 `128`，正常+边界 `92`，低分 `36`，正常+边界率 `71.9%`。

## 分词条

| 词条 | 样本数 | 正常 | 边界 | 低分 | 均分 | 中位数 | 最低 | 最高 | 核心覆盖均值 | 全段/窗口覆盖 | L/R 覆盖均值 | 采集质量 | 处置 | 主要诊断 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 花 | 93 | 78 | 5 | 10 | 72.954 | 78.392 | 2.913 | 80.784 | 0.943 | 0.708/0.940 | 0.016/0.702 | score_valid:83, semantic_mismatch:8, needs_recapture:2 | normal:78, semantic_mismatch:8, borderline_review:5 | flower_core_accepted:83, flower_opening_guard_failed:9, flower_core_hand_presence_low:1 |
| 跳 | 56 | 9 | 0 | 47 | 20.563 | 7.838 | 0.833 | 88.577 | 0.717 | 0.697/0.257 | 0.617/0.728 | semantic_mismatch:28, needs_recapture:19, score_valid:9 | semantic_mismatch:28, recapture:19, normal:9 | jump_two_hand_presence_low:37, jump_low_other:10, jump_core_accepted:9 |

## 有效采集口径

- 这里排除 `needs_recapture`，只看核心关键点已经足够入画、可以解释为动作语义评分的样本。

| 词条 | 原始样本 | 建议重采 | 有效采集 | 正常+边界 | 低分 | 正常+边界率 | 有效均分 | 语义不匹配 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 花 | 93 | 2 | 91 | 83 | 8 | 91.2% | 74.169 | 8 |
| 跳 | 56 | 19 | 37 | 9 | 28 | 24.3% | 29.094 | 28 |

## 语义不匹配明细

- 这些样本核心关键点已足够入画，但未满足词条核心语义；通常不应通过放宽阈值抬高。

| request | 词条 | 分数 | 诊断 | floor 原因 | 方向余弦 | 纵向分数 | 幅度比 | 水平/纵向 | 关系覆盖 | 建议 |
|---|---|---:|---|---|---:|---:|---:|---:|---:|---|
| web_20260602_233301_233b8215 | 花 | 2.913 | flower_opening_guard_failed | opening_guard_too_weak | - | - | - | - | - | 从撮合状态开始，慢慢张开五指并保持约 0.5 秒；当前张开分数 0.05。 |
| web_20260523_062341_afa8c368 | 花 | 14.572 | flower_opening_guard_failed | query_not_short_core_capture | - | - | - | - | - | 从撮合状态开始，慢慢张开五指并保持约 0.5 秒；当前张开分数 0.00。 |
| web_20260523_020807_c15e8c2b | 花 | 18.227 | flower_opening_guard_failed | opening_guard_too_weak | - | - | - | - | - | 从撮合状态开始，慢慢张开五指并保持约 0.5 秒；当前张开分数 0.55。 |
| web_20260523_020843_6ba8acd9 | 花 | 42.253 | flower_opening_guard_failed | query_not_short_core_capture | - | - | - | - | - | 从撮合状态开始，慢慢张开五指并保持约 0.5 秒；当前张开分数 0.56。 |
| web_20260523_053102_e1ff4324 | 花 | 46.712 | flower_opening_guard_failed | query_not_short_core_capture | - | - | - | - | - | 从撮合状态开始，慢慢张开五指并保持约 0.5 秒；当前张开分数 0.32。 |
| web_20260522_232244_45d260ed | 花 | 48.531 | flower_opening_guard_failed | query_not_short_core_capture | - | - | - | - | - | 从撮合状态开始，慢慢张开五指并保持约 0.5 秒；当前张开分数 0.12。 |
| web_20260523_062433_e3e870b6 | 花 | 53.008 | flower_opening_guard_failed | query_not_short_core_capture | - | - | - | - | - | 从撮合状态开始，慢慢张开五指并保持约 0.5 秒；当前张开分数 0.55。 |
| web_20260523_031345_3b07a113 | 花 | 54.425 | flower_opening_guard_failed | query_not_short_core_capture | - | - | - | - | - | 从撮合状态开始，慢慢张开五指并保持约 0.5 秒；当前张开分数 0.09。 |
| web_20260523_024000_dd35e1bb | 跳 | 4.123 | jump_low_other | phase_endpoint_order_mismatch | - | - | - | - | 0.750 | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.90/0.70。 |
| web_20260523_044018_960618af | 跳 | 4.328 | jump_low_other | phase_endpoint_order_mismatch | - | - | - | - | 0.625 | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.77/0.77。 |
| web_20260523_044135_12fbd5bc | 跳 | 4.983 | jump_low_other | phase_endpoint_order_mismatch | - | - | - | - | 0.875 | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.70/0.77。 |
| web_20260523_001048_5bcb9948 | 跳 | 5.354 | jump_two_hand_presence_low | phase_endpoint_order_mismatch | - | - | - | - | 0.667 | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.40/0.60。 |
| web_20260523_031219_0da0bd96 | 跳 | 6.132 | jump_low_other | phase_endpoint_order_mismatch | - | - | - | - | 0.667 | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.73/0.67。 |
| web_20260523_044336_5d15d099 | 跳 | 6.183 | jump_two_hand_presence_low | phase_endpoint_order_mismatch | - | - | - | - | 0.714 | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.48/0.72。 |
| web_20260523_044358_00db9d4d | 跳 | 7.175 | jump_two_hand_presence_low | phase_endpoint_order_mismatch | - | - | - | - | 0.714 | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.64/0.80。 |
| web_20260523_011122_fb34e3e5 | 跳 | 7.259 | jump_two_hand_presence_low | phase_endpoint_order_mismatch | - | - | - | - | 0.750 | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.53/0.57。 |
| web_20260523_031134_8688f93f | 跳 | 7.390 | jump_two_hand_presence_low | phase_endpoint_order_mismatch | - | - | - | - | 0.727 | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.70/0.60。 |
| web_20260523_021622_26666615 | 跳 | 7.832 | jump_two_hand_presence_low | phase_endpoint_order_mismatch | - | - | - | - | 0.875 | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.60/0.50。 |
| web_20260602_214010_3f951c51 | 跳 | 7.844 | jump_two_hand_presence_low | phase_endpoint_order_mismatch | - | - | - | - | 1.000 | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.60/0.88。 |
| web_20260523_041735_ea1bbaa6 | 跳 | 8.391 | jump_two_hand_presence_low | phase_endpoint_order_mismatch | - | - | - | - | 1.000 | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.83/0.63。 |
| web_20260523_053241_5fbbf9c7 | 跳 | 8.459 | jump_low_other | phase_endpoint_order_mismatch | - | - | - | - | 1.000 | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.80/0.92。 |
| web_20260523_022509_a44cb853 | 跳 | 8.690 | jump_low_other | phase_endpoint_order_mismatch | - | - | - | - | 0.750 | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.77/0.67。 |
| web_20260523_052731_8f51941f | 跳 | 8.706 | jump_low_other | phase_endpoint_order_mismatch | - | - | - | - | 1.000 | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.84/0.92。 |
| web_20260523_010234_e2d59e5e | 跳 | 8.937 | jump_two_hand_presence_low | phase_endpoint_order_mismatch | - | - | - | - | 0.846 | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.67/0.42。 |
| web_20260523_021006_aef545ce | 跳 | 9.028 | jump_two_hand_presence_low | phase_endpoint_order_mismatch | - | - | - | - | 0.941 | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.73/0.60。 |
| web_20260523_005941_0ec0ccab | 跳 | 9.233 | jump_two_hand_presence_low | phase_endpoint_order_mismatch | - | - | - | - | 1.000 | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.80/0.53。 |
| web_20260523_063109_8727dac1 | 跳 | 9.551 | jump_two_hand_presence_low | phase_endpoint_order_mismatch | - | - | - | - | 0.625 | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.60/1.00。 |
| web_20260523_031247_f927176a | 跳 | 10.543 | jump_two_hand_presence_low | phase_endpoint_order_mismatch | - | - | - | - | 1.000 | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.93/0.53。 |
| web_20260523_010004_7eaf7ee3 | 跳 | 11.213 | jump_two_hand_presence_low | phase_endpoint_order_mismatch | - | - | - | - | 1.000 | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.80/0.53。 |
| web_20260523_044323_2eb9eb7e | 跳 | 11.645 | jump_low_other | phase_endpoint_order_mismatch | - | - | - | - | 1.000 | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.76/0.80。 |
| web_20260523_063026_c2f04725 | 跳 | 12.248 | jump_two_hand_presence_low | phase_endpoint_order_mismatch | - | - | - | - | 0.857 | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.64/0.92。 |
| web_20260523_031235_d0de0d44 | 跳 | 15.226 | jump_two_hand_presence_low | phase_endpoint_order_mismatch | - | - | - | - | 1.000 | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.53/0.60。 |
| web_20260523_001152_83546751 | 跳 | 15.534 | jump_two_hand_presence_low | phase_endpoint_order_mismatch | - | - | - | - | 1.000 | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.67/0.60。 |
| web_20260523_063052_fc94e4f7 | 跳 | 17.520 | jump_low_other | phase_endpoint_order_mismatch | - | - | - | - | 1.000 | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.72/0.84。 |
| web_20260523_052715_1ad3c2d2 | 跳 | 19.379 | jump_two_hand_presence_low | phase_endpoint_order_mismatch | - | - | - | - | 1.000 | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.64/0.76。 |
| web_20260602_233302_d92c0ce2 | 跳 | 55.326 | jump_low_other | phase_endpoint_order_mismatch | - | - | - | - | 0.833 | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.89/1.00。 |

## 跳语义 floor 接收明细

- `action_window_net` 表示动作窗口起止净方向直接通过；`full_sequence_local_relation_segment` 表示完整序列中检测到局部双手弹跳段，并通过右手食指/中指手形守卫。
- 来源分布：`{'action_window_net': 9}`

| request | 分数 | 分段 | 来源 | 方向余弦 | 幅度比 | 水平/纵向 | 段覆盖 | 段帧 | 两指手形 | fallback 原因 |
|---|---:|---|---|---:|---:|---:|---:|---|---:|---|
| web_20260523_015650_c394e067 | 84.923 | normal_like | action_window_net | 0.999 | 0.976 | 0.642 | - | 6-22 | - | - |
| web_20260523_015727_2cb1fbe6 | 84.948 | normal_like | action_window_net | 0.999 | 1.016 | 0.724 | - | 6-22 | - | - |
| web_20260523_020555_09843ad1 | 84.948 | normal_like | action_window_net | 0.999 | 1.016 | 0.724 | - | 6-22 | - | - |
| web_20260523_030625_c3f72e11 | 84.965 | normal_like | action_window_net | 0.999 | 1.009 | 0.648 | - | 6-22 | - | - |
| web_20260523_031129_bd3988e8 | 84.974 | normal_like | action_window_net | 1.000 | 1.008 | 0.669 | - | 6-22 | - | - |
| web_20260523_041350_ad02e9e5 | 84.974 | normal_like | action_window_net | 1.000 | 1.008 | 0.669 | - | 6-22 | - | - |
| web_20260523_041447_f7341789 | 84.974 | normal_like | action_window_net | 1.000 | 1.008 | 0.669 | - | 6-22 | - | - |
| web_20260523_043446_cbecd916 | 84.974 | normal_like | action_window_net | 1.000 | 1.008 | 0.669 | - | 6-22 | - | - |
| web_20260602_233348_53e3df5d | 88.577 | normal_like | action_window_net | 0.993 | 1.006 | 0.534 | - | 6-22 | - | - |

## 低分原因

### 花

- 低分数：`10`
- 诊断分布：`{'flower_core_hand_presence_low': 1, 'flower_opening_guard_failed': 9}`

| request | 分数 | 采集质量 | 处置 | 诊断 | floor 原因 | L/R 覆盖 | 核心全段/窗口 | 花-张开 | 双手关系 | 右手形 | 建议 |
|---|---:|---|---|---|---|---:|---:|---:|---:|---:|---|
| web_20260602_233301_233b8215 | 2.913 | semantic_mismatch | semantic_mismatch | flower_opening_guard_failed | opening_guard_too_weak | 0.000/1.000 | 1.000/1.000 | 0.052 | 0.000 | 0.000 | 从撮合状态开始，慢慢张开五指并保持约 0.5 秒；当前张开分数 0.05。 |
| web_20260523_062341_afa8c368 | 14.572 | semantic_mismatch | semantic_mismatch | flower_opening_guard_failed | query_not_short_core_capture | 1.000/0.450 | 1.000/1.000 | 0.000 | 0.000 | 0.000 | 从撮合状态开始，慢慢张开五指并保持约 0.5 秒；当前张开分数 0.00。 |
| web_20260602_212933_7ad54f26 | 14.863 | needs_recapture | recapture | flower_opening_guard_failed | insufficient_core_hand_presence | 0.000/0.000 | 0.000/0.000 | 0.000 | 0.000 | 0.000 | 让开花手保持在画面中央，完整露出手腕和五指；当前窗口核心手覆盖 0.00。 |
| web_20260523_020807_c15e8c2b | 18.227 | semantic_mismatch | semantic_mismatch | flower_opening_guard_failed | opening_guard_too_weak | 0.000/0.667 | 0.667/0.667 | 0.550 | 0.000 | 0.000 | 从撮合状态开始，慢慢张开五指并保持约 0.5 秒；当前张开分数 0.55。 |
| web_20260522_231259_51a8c719 | 20.468 | needs_recapture | recapture | flower_core_hand_presence_low | opening_guard_too_weak | 0.000/0.500 | 0.500/0.750 | 0.450 | 0.000 | 0.000 | 让开花手保持在画面中央，完整露出手腕和五指；当前窗口核心手覆盖 0.75。 |
| web_20260523_020843_6ba8acd9 | 42.253 | semantic_mismatch | semantic_mismatch | flower_opening_guard_failed | query_not_short_core_capture | 0.000/0.717 | 0.717/0.824 | 0.556 | 0.000 | 0.000 | 从撮合状态开始，慢慢张开五指并保持约 0.5 秒；当前张开分数 0.56。 |
| web_20260523_053102_e1ff4324 | 46.712 | semantic_mismatch | semantic_mismatch | flower_opening_guard_failed | query_not_short_core_capture | 0.000/0.720 | 0.720/1.000 | 0.317 | 0.000 | 0.000 | 从撮合状态开始，慢慢张开五指并保持约 0.5 秒；当前张开分数 0.32。 |
| web_20260522_232244_45d260ed | 48.531 | semantic_mismatch | semantic_mismatch | flower_opening_guard_failed | query_not_short_core_capture | 0.000/0.633 | 0.633/1.000 | 0.122 | 0.000 | 0.000 | 从撮合状态开始，慢慢张开五指并保持约 0.5 秒；当前张开分数 0.12。 |
| web_20260523_062433_e3e870b6 | 53.008 | semantic_mismatch | semantic_mismatch | flower_opening_guard_failed | query_not_short_core_capture | 0.000/0.680 | 0.680/0.857 | 0.550 | 0.000 | 0.000 | 从撮合状态开始，慢慢张开五指并保持约 0.5 秒；当前张开分数 0.55。 |
| web_20260523_031345_3b07a113 | 54.425 | semantic_mismatch | semantic_mismatch | flower_opening_guard_failed | query_not_short_core_capture | 0.000/0.767 | 0.767/0.750 | 0.086 | 0.000 | 0.000 | 从撮合状态开始，慢慢张开五指并保持约 0.5 秒；当前张开分数 0.09。 |

### 跳

- 低分数：`47`
- 诊断分布：`{'jump_two_hand_presence_low': 37, 'jump_low_other': 10}`

| request | 分数 | 采集质量 | 处置 | 诊断 | floor 原因 | L/R 覆盖 | 核心全段/窗口 | 花-张开 | 双手关系 | 右手形 | 建议 |
|---|---:|---|---|---|---|---:|---:|---:|---:|---:|---|
| web_20260523_031147_55d51ab9 | 0.833 | needs_recapture | recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.500/0.600 | 0.250/0.000 | - | 0.268 | 0.164 | 左手“地面”和右手“两指小人”需要同时入画；当前左手覆盖 0.50、右手覆盖 0.60。 |
| web_20260602_214656_3fae071b | 1.354 | needs_recapture | recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.040/0.480 | 0.143/0.250 | - | 0.000 | 0.214 | 左手“地面”和右手“两指小人”需要同时入画；当前左手覆盖 0.04、右手覆盖 0.48。 |
| web_20260523_053940_f86fc279 | 2.202 | needs_recapture | recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.440/0.760 | 0.429/0.000 | - | 0.286 | 0.283 | 左手“地面”和右手“两指小人”需要同时入画；当前左手覆盖 0.44、右手覆盖 0.76。 |
| web_20260523_053345_da4d1ec9 | 2.366 | needs_recapture | recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.000/0.760 | 0.000/0.000 | - | 0.000 | 0.266 | 左手“地面”和右手“两指小人”需要同时入画；当前左手覆盖 0.00、右手覆盖 0.76。 |
| web_20260523_001113_b486eb41 | 2.501 | needs_recapture | recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.200/0.600 | 0.000/0.000 | - | 0.000 | 0.288 | 左手“地面”和右手“两指小人”需要同时入画；当前左手覆盖 0.20、右手覆盖 0.60。 |
| web_20260523_053254_bd7f1d1c | 3.045 | needs_recapture | recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.520/0.880 | 0.429/0.000 | - | 0.501 | 0.270 | 左手“地面”和右手“两指小人”需要同时入画；当前左手覆盖 0.52、右手覆盖 0.88。 |
| web_20260523_011135_5967dd5a | 3.111 | needs_recapture | recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.467/0.700 | 0.500/0.000 | - | 0.481 | 0.288 | 左手“地面”和右手“两指小人”需要同时入画；当前左手覆盖 0.47、右手覆盖 0.70。 |
| web_20260523_053309_28821cfd | 3.491 | needs_recapture | recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.440/0.840 | 0.571/0.000 | - | 0.428 | 0.278 | 左手“地面”和右手“两指小人”需要同时入画；当前左手覆盖 0.44、右手覆盖 0.84。 |
| web_20260523_053401_8934d89a | 3.643 | needs_recapture | recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.000/0.840 | 0.000/0.000 | - | 0.000 | 0.264 | 左手“地面”和右手“两指小人”需要同时入画；当前左手覆盖 0.00、右手覆盖 0.84。 |
| web_20260523_010014_049faf7d | 3.680 | needs_recapture | recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.467/0.200 | 0.333/0.000 | - | 0.320 | 0.280 | 左手“地面”和右手“两指小人”需要同时入画；当前左手覆盖 0.47、右手覆盖 0.20。 |
| web_20260523_024025_9c6cf572 | 3.769 | needs_recapture | recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.300/0.600 | 0.500/0.000 | - | 0.353 | 0.271 | 左手“地面”和右手“两指小人”需要同时入画；当前左手覆盖 0.30、右手覆盖 0.60。 |
| web_20260523_024000_dd35e1bb | 4.123 | semantic_mismatch | semantic_mismatch | jump_low_other | phase_endpoint_order_mismatch | 0.900/0.700 | 0.750/0.000 | - | 0.457 | 0.239 | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.90/0.70。 |
| web_20260523_044203_20778933 | 4.186 | needs_recapture | recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.633/0.767 | 0.500/0.000 | - | 0.238 | 0.256 | 左手“地面”和右手“两指小人”需要同时入画；当前左手覆盖 0.63、右手覆盖 0.77。 |
| web_20260523_063002_0aa1419e | 4.240 | needs_recapture | recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.480/0.840 | 0.286/0.000 | - | 0.124 | 0.282 | 左手“地面”和右手“两指小人”需要同时入画；当前左手覆盖 0.48、右手覆盖 0.84。 |
| web_20260523_044018_960618af | 4.328 | semantic_mismatch | semantic_mismatch | jump_low_other | phase_endpoint_order_mismatch | 0.767/0.767 | 0.625/0.000 | - | 0.552 | 0.235 | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.77/0.77。 |
| web_20260523_005953_cdf0697d | 4.450 | needs_recapture | recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.400/0.400 | 0.333/0.000 | - | 0.298 | 0.282 | 左手“地面”和右手“两指小人”需要同时入画；当前左手覆盖 0.40、右手覆盖 0.40。 |
| web_20260523_021604_9c415199 | 4.784 | needs_recapture | recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.133/0.717 | 0.118/0.000 | - | 0.000 | 0.265 | 左手“地面”和右手“两指小人”需要同时入画；当前左手覆盖 0.13、右手覆盖 0.72。 |
| web_20260523_001100_dea381ee | 4.973 | needs_recapture | recapture | jump_two_hand_presence_low | insufficient_two_hand_presence | 0.467/0.533 | 0.500/0.000 | - | 0.445 | 0.289 | 左手“地面”和右手“两指小人”需要同时入画；当前左手覆盖 0.47、右手覆盖 0.53。 |
| web_20260523_044135_12fbd5bc | 4.983 | semantic_mismatch | semantic_mismatch | jump_low_other | phase_endpoint_order_mismatch | 0.700/0.767 | 0.875/0.000 | - | 0.448 | 0.245 | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.70/0.77。 |
| web_20260523_001048_5bcb9948 | 5.354 | semantic_mismatch | semantic_mismatch | jump_two_hand_presence_low | phase_endpoint_order_mismatch | 0.400/0.600 | 0.667/0.000 | - | 0.675 | 0.287 | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.40/0.60。 |

## 最新样本

| request | 词条 | 帧数 | 分数 | 分段 | 处置 | 采集质量 | 诊断 | L/R 覆盖 | 核心全段/窗口 | 对齐 | 建议 |
|---|---|---:|---:|---|---|---|---|---:|---:|---|---|
| web_20260523_062353_2b6f64cd | 花 | 25 | 79.530 | normal_like | normal | score_valid | flower_core_accepted | 0.000/0.760 | 0.760/1.000 | full_sequence_with_action_window_diagnostics | 开花核心段可评分；继续保持手部完整入画和清晰张开动态。 |
| web_20260523_062406_09525c5f | 花 | 25 | 80.022 | normal_like | normal | score_valid | flower_core_accepted | 0.000/0.720 | 0.720/1.000 | full_sequence_with_action_window_diagnostics | 开花核心段可评分；继续保持手部完整入画和清晰张开动态。 |
| web_20260523_062420_5aea4dd9 | 花 | 25 | 78.624 | normal_like | normal | score_valid | flower_core_accepted | 0.000/0.800 | 0.800/1.000 | full_sequence_with_action_window_diagnostics | 开花核心段可评分；继续保持手部完整入画和清晰张开动态。 |
| web_20260523_062433_e3e870b6 | 花 | 25 | 53.008 | low | semantic_mismatch | semantic_mismatch | flower_opening_guard_failed | 0.000/0.680 | 0.680/0.857 | full_sequence_with_action_window_diagnostics | 从撮合状态开始，慢慢张开五指并保持约 0.5 秒；当前张开分数 0.55。 |
| web_20260523_062644_9a457871 | 花 | 25 | 79.941 | normal_like | normal | score_valid | flower_core_accepted | 0.000/0.680 | 0.680/1.000 | full_sequence_with_action_window_diagnostics | 开花核心段可评分；继续保持手部完整入画和清晰张开动态。 |
| web_20260523_063002_0aa1419e | 跳 | 25 | 4.240 | low | recapture | needs_recapture | jump_two_hand_presence_low | 0.480/0.840 | 0.286/0.000 | semantic_action_window | 左手“地面”和右手“两指小人”需要同时入画；当前左手覆盖 0.48、右手覆盖 0.84。 |
| web_20260523_063015_4017237e | 跳 | 25 | 8.919 | low | recapture | needs_recapture | jump_two_hand_presence_low | 0.640/0.840 | 0.429/1.000 | semantic_action_window | 左手“地面”和右手“两指小人”需要同时入画；当前左手覆盖 0.64、右手覆盖 0.84。 |
| web_20260523_063026_c2f04725 | 跳 | 25 | 12.248 | low | semantic_mismatch | semantic_mismatch | jump_two_hand_presence_low | 0.640/0.920 | 0.857/0.000 | semantic_action_window | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.64/0.92。 |
| web_20260523_063052_fc94e4f7 | 跳 | 25 | 17.520 | low | semantic_mismatch | semantic_mismatch | jump_low_other | 0.720/0.840 | 1.000/0.000 | semantic_action_window | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.72/0.84。 |
| web_20260523_063109_8727dac1 | 跳 | 25 | 9.551 | low | semantic_mismatch | semantic_mismatch | jump_two_hand_presence_low | 0.600/1.000 | 0.625/0.000 | semantic_action_window | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.60/1.00。 |
| web_20260523_063159_324827f7 | 花 | 15 | 78.463 | normal_like | normal | score_valid | flower_core_accepted | 0.000/0.667 | 0.667/1.000 | full_sequence_with_action_window_diagnostics | 开花核心段可评分；继续保持手部完整入画和清晰张开动态。 |
| web_20260523_063217_bd40ee0c | 花 | 30 | 79.244 | normal_like | normal | score_valid | flower_core_accepted | 0.000/0.733 | 0.733/1.000 | full_sequence_with_action_window_diagnostics | 开花核心段可评分；继续保持手部完整入画和清晰张开动态。 |
| web_20260523_063230_6a3bad1f | 花 | 25 | 79.674 | normal_like | normal | score_valid | flower_core_accepted | 0.000/0.680 | 0.680/1.000 | full_sequence_with_action_window_diagnostics | 开花核心段可评分；继续保持手部完整入画和清晰张开动态。 |
| web_20260523_071212_4547d033 | 花 | 25 | 79.560 | normal_like | normal | score_valid | flower_core_accepted | 0.000/0.600 | 0.600/1.000 | full_sequence_with_action_window_diagnostics | 开花核心段可评分；继续保持手部完整入画和清晰张开动态。 |
| web_20260523_071306_071a2172 | 花 | 15 | 76.923 | normal_like | normal | score_valid | flower_core_accepted | 0.067/0.600 | 0.600/1.000 | full_sequence_with_action_window_diagnostics | 开花核心段可评分；继续保持手部完整入画和清晰张开动态。 |
| web_20260523_071320_415e2975 | 花 | 15 | 78.392 | normal_like | normal | score_valid | flower_core_accepted | 0.000/0.800 | 0.800/1.000 | full_sequence_with_action_window_diagnostics | 开花核心段可评分；继续保持手部完整入画和清晰张开动态。 |
| web_20260523_071339_f3f432d2 | 花 | 25 | 79.410 | normal_like | normal | score_valid | flower_core_accepted | 0.000/0.680 | 0.680/1.000 | full_sequence_with_action_window_diagnostics | 开花核心段可评分；继续保持手部完整入画和清晰张开动态。 |
| web_20260523_071415_2505a91e | 花 | 25 | 79.116 | normal_like | normal | score_valid | flower_core_accepted | 0.040/0.800 | 0.800/0.857 | full_sequence_with_action_window_diagnostics | 开花核心段可评分；继续保持手部完整入画和清晰张开动态。 |
| web_20260602_212933_7ad54f26 | 花 | 15 | 14.863 | low | recapture | needs_recapture | flower_opening_guard_failed | 0.000/0.000 | 0.000/0.000 | full_sequence_with_action_window_diagnostics | 让开花手保持在画面中央，完整露出手腕和五指；当前窗口核心手覆盖 0.00。 |
| web_20260602_212951_e1173da1 | 花 | 15 | 77.625 | normal_like | normal | score_valid | flower_core_accepted | 0.000/0.800 | 0.800/1.000 | full_sequence_with_action_window_diagnostics | 开花核心段可评分；继续保持手部完整入画和清晰张开动态。 |
| web_20260602_213015_411a2ecd | 花 | 30 | 78.861 | normal_like | normal | score_valid | flower_core_accepted | 0.000/0.633 | 0.633/1.000 | full_sequence_with_action_window_diagnostics | 开花核心段可评分；继续保持手部完整入画和清晰张开动态。 |
| web_20260602_213030_368950ee | 花 | 25 | 78.355 | normal_like | normal | score_valid | flower_core_accepted | 0.040/0.480 | 0.480/1.000 | full_sequence_with_action_window_diagnostics | 开花核心段可评分；继续保持手部完整入画和清晰张开动态。 |
| web_20260602_213050_ec3d0907 | 花 | 25 | 79.517 | normal_like | normal | score_valid | flower_core_accepted | 0.000/0.720 | 0.720/1.000 | full_sequence_with_action_window_diagnostics | 开花核心段可评分；继续保持手部完整入画和清晰张开动态。 |
| web_20260602_213918_4947c25e | 花 | 25 | 79.707 | normal_like | normal | score_valid | flower_core_accepted | 0.000/0.720 | 0.720/0.889 | full_sequence_with_action_window_diagnostics | 开花核心段可评分；继续保持手部完整入画和清晰张开动态。 |
| web_20260602_214010_3f951c51 | 跳 | 25 | 7.844 | low | semantic_mismatch | semantic_mismatch | jump_two_hand_presence_low | 0.600/0.880 | 1.000/0.000 | semantic_action_window | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.60/0.88。 |
| web_20260602_214656_3fae071b | 跳 | 25 | 1.354 | low | recapture | needs_recapture | jump_two_hand_presence_low | 0.040/0.480 | 0.143/0.250 | semantic_action_window | 左手“地面”和右手“两指小人”需要同时入画；当前左手覆盖 0.04、右手覆盖 0.48。 |
| web_20260602_233301_233b8215 | 花 | 6 | 2.913 | low | semantic_mismatch | semantic_mismatch | flower_opening_guard_failed | 0.000/1.000 | 1.000/1.000 | full_sequence_with_action_window_diagnostics | 从撮合状态开始，慢慢张开五指并保持约 0.5 秒；当前张开分数 0.05。 |
| web_20260602_233302_d92c0ce2 | 跳 | 9 | 55.326 | low | semantic_mismatch | semantic_mismatch | jump_low_other | 0.889/1.000 | 0.833/1.000 | semantic_action_window | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.89/1.00。 |
| web_20260602_233343_899e6970 | 花 | 53 | 76.899 | normal_like | normal | score_valid | flower_core_accepted | 0.000/0.792 | 0.792/1.000 | full_sequence_with_action_window_diagnostics | 开花核心段可评分；继续保持手部完整入画和清晰张开动态。 |
| web_20260602_233348_53e3df5d | 跳 | 19 | 88.577 | normal_like | normal | score_valid | jump_core_accepted | 0.842/0.895 | 0.889/0.833 | semantic_action_window | 双手弹跳核心语义可评分；继续保持两只手同时稳定入画。 |

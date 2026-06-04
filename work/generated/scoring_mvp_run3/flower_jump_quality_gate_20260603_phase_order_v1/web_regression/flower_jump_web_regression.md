# 花/跳网页打分回归

- 生成时间：`2026-06-03T06:54:00`
- Web 样本根目录：`/data/WYC/signLanguage/work/generated/web_scoring_mvp`
- 当前标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 目标词：`花, 跳`
- 后端状态接口：`http://127.0.0.1:5080/api/status`
- 5080 状态：worker=`ready`，worker_pid=`811485`，reload_count=`11`，last_reload_error=`None`
- 口径：不重新运行 Holistic；query 使用已保存网页/API Holistic JSON，standard 使用当前标准库。

## 结论

- 回归状态：`FAIL`
- replay 报告：`work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_phase_order_v1/web_regression/active_template_replay/web_replay_current.md`
- diagnostics 报告：`work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_phase_order_v1/web_regression/flower_jump_diagnostics/web_semantic_diagnostics.md`

| gate | 结果 | 说明 |
|---|---|---|
| backend_ready | PASS | url=http://127.0.0.1:5080/api/status, worker=ready, reload_error=-, error=- |
| replay_no_errors | PASS | samples=168, errors=0 |
| diagnostics_no_errors | PASS | samples=149, errors=0 |
| effective_rate_total | FAIL | rate=71.9%, threshold=95.0% |
| effective_rate_花 | FAIL | rate=91.2%, reliable=91, normal_or_borderline=83, low=8 |
| effective_rate_跳 | FAIL | rate=24.3%, reliable=37, normal_or_borderline=9, low=28 |
| jump_effective_low_zero | FAIL | effective_low=28 |
| flower_effective_low_bounded | FAIL | effective_low=8, max=5, diagnoses={'flower_opening_guard_failed': 8} |
| flower_effective_low_explained | PASS | allowed=['flower_opening_guard_failed'], observed={'flower_opening_guard_failed': 8} |

## 网页回放

- 样本数 `168`，错误 `0`，正常 `87`，边界 `5`，低分 `76`。
- 旧均分 `35.442`，当前均分 `49.067`。

| 词条 | 样本数 | 正常 | 边界 | 低分 | 当前均分 | 手部覆盖均值 |
|---|---:|---:|---:|---:|---:|---:|
| 月亮 | 1 | 0 | 0 | 1 | 21.343 | 0.800 |
| 汽车 | 3 | 0 | 0 | 3 | 16.905 | 0.833 |
| 花 | 93 | 78 | 5 | 10 | 72.954 | 0.708 |
| 虎 | 2 | 0 | 0 | 2 | 17.755 | 0.780 |
| 跳 | 56 | 9 | 0 | 47 | 20.563 | 0.771 |
| 香蕉 | 13 | 0 | 0 | 13 | 15.340 | 0.601 |

## 目标词语义诊断

- 目标词样本 `149`，错误 `0`，有效采集 `128`，有效正常+边界 `92`，有效低分 `36`，有效正常+边界率 `71.9%`。

| 词条 | 原始样本 | 建议重采 | 有效采集 | 有效正常+边界 | 有效低分 | 有效率 | 有效均分 | 处置 | 诊断 |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 花 | 93 | 2 | 91 | 83 | 8 | 91.2% | 74.169 | {'borderline_review': 5, 'normal': 78, 'recapture': 2, 'semantic_mismatch': 8} | {'flower_core_accepted': 83, 'flower_core_hand_presence_low': 1, 'flower_opening_guard_failed': 9} |
| 跳 | 56 | 19 | 37 | 9 | 28 | 24.3% | 29.094 | {'semantic_mismatch': 28, 'recapture': 19, 'normal': 9} | {'jump_two_hand_presence_low': 37, 'jump_core_accepted': 9, 'jump_low_other': 10} |

## 有效低分样本

| request | 词条 | 分数 | 采集质量 | 处置 | 诊断 | floor 原因 | L/R 覆盖 | 花张开 | 建议 |
|---|---|---:|---|---|---|---|---:|---:|---|
| web_20260602_233301_233b8215 | 花 | 2.913 | semantic_mismatch | semantic_mismatch | flower_opening_guard_failed | opening_guard_too_weak | 0.000/1.000 | 0.052 | 从撮合状态开始，慢慢张开五指并保持约 0.5 秒；当前张开分数 0.05。 |
| web_20260523_062341_afa8c368 | 花 | 14.572 | semantic_mismatch | semantic_mismatch | flower_opening_guard_failed | query_not_short_core_capture | 1.000/0.450 | 0.000 | 从撮合状态开始，慢慢张开五指并保持约 0.5 秒；当前张开分数 0.00。 |
| web_20260523_020807_c15e8c2b | 花 | 18.227 | semantic_mismatch | semantic_mismatch | flower_opening_guard_failed | opening_guard_too_weak | 0.000/0.667 | 0.550 | 从撮合状态开始，慢慢张开五指并保持约 0.5 秒；当前张开分数 0.55。 |
| web_20260523_020843_6ba8acd9 | 花 | 42.253 | semantic_mismatch | semantic_mismatch | flower_opening_guard_failed | query_not_short_core_capture | 0.000/0.717 | 0.556 | 从撮合状态开始，慢慢张开五指并保持约 0.5 秒；当前张开分数 0.56。 |
| web_20260523_053102_e1ff4324 | 花 | 46.712 | semantic_mismatch | semantic_mismatch | flower_opening_guard_failed | query_not_short_core_capture | 0.000/0.720 | 0.317 | 从撮合状态开始，慢慢张开五指并保持约 0.5 秒；当前张开分数 0.32。 |
| web_20260522_232244_45d260ed | 花 | 48.531 | semantic_mismatch | semantic_mismatch | flower_opening_guard_failed | query_not_short_core_capture | 0.000/0.633 | 0.122 | 从撮合状态开始，慢慢张开五指并保持约 0.5 秒；当前张开分数 0.12。 |
| web_20260523_062433_e3e870b6 | 花 | 53.008 | semantic_mismatch | semantic_mismatch | flower_opening_guard_failed | query_not_short_core_capture | 0.000/0.680 | 0.550 | 从撮合状态开始，慢慢张开五指并保持约 0.5 秒；当前张开分数 0.55。 |
| web_20260523_031345_3b07a113 | 花 | 54.425 | semantic_mismatch | semantic_mismatch | flower_opening_guard_failed | query_not_short_core_capture | 0.000/0.767 | 0.086 | 从撮合状态开始，慢慢张开五指并保持约 0.5 秒；当前张开分数 0.09。 |
| web_20260523_024000_dd35e1bb | 跳 | 4.123 | semantic_mismatch | semantic_mismatch | jump_low_other | phase_endpoint_order_mismatch | 0.900/0.700 | - | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.90/0.70。 |
| web_20260523_044018_960618af | 跳 | 4.328 | semantic_mismatch | semantic_mismatch | jump_low_other | phase_endpoint_order_mismatch | 0.767/0.767 | - | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.77/0.77。 |
| web_20260523_044135_12fbd5bc | 跳 | 4.983 | semantic_mismatch | semantic_mismatch | jump_low_other | phase_endpoint_order_mismatch | 0.700/0.767 | - | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.70/0.77。 |
| web_20260523_001048_5bcb9948 | 跳 | 5.354 | semantic_mismatch | semantic_mismatch | jump_two_hand_presence_low | phase_endpoint_order_mismatch | 0.400/0.600 | - | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.40/0.60。 |
| web_20260523_031219_0da0bd96 | 跳 | 6.132 | semantic_mismatch | semantic_mismatch | jump_low_other | phase_endpoint_order_mismatch | 0.733/0.667 | - | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.73/0.67。 |
| web_20260523_044336_5d15d099 | 跳 | 6.183 | semantic_mismatch | semantic_mismatch | jump_two_hand_presence_low | phase_endpoint_order_mismatch | 0.480/0.720 | - | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.48/0.72。 |
| web_20260523_044358_00db9d4d | 跳 | 7.175 | semantic_mismatch | semantic_mismatch | jump_two_hand_presence_low | phase_endpoint_order_mismatch | 0.640/0.800 | - | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.64/0.80。 |
| web_20260523_011122_fb34e3e5 | 跳 | 7.259 | semantic_mismatch | semantic_mismatch | jump_two_hand_presence_low | phase_endpoint_order_mismatch | 0.533/0.567 | - | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.53/0.57。 |
| web_20260523_031134_8688f93f | 跳 | 7.390 | semantic_mismatch | semantic_mismatch | jump_two_hand_presence_low | phase_endpoint_order_mismatch | 0.700/0.600 | - | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.70/0.60。 |
| web_20260523_021622_26666615 | 跳 | 7.832 | semantic_mismatch | semantic_mismatch | jump_two_hand_presence_low | phase_endpoint_order_mismatch | 0.600/0.500 | - | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.60/0.50。 |
| web_20260602_214010_3f951c51 | 跳 | 7.844 | semantic_mismatch | semantic_mismatch | jump_two_hand_presence_low | phase_endpoint_order_mismatch | 0.600/0.880 | - | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.60/0.88。 |
| web_20260523_041735_ea1bbaa6 | 跳 | 8.391 | semantic_mismatch | semantic_mismatch | jump_two_hand_presence_low | phase_endpoint_order_mismatch | 0.833/0.633 | - | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.83/0.63。 |
| web_20260523_053241_5fbbf9c7 | 跳 | 8.459 | semantic_mismatch | semantic_mismatch | jump_low_other | phase_endpoint_order_mismatch | 0.800/0.920 | - | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.80/0.92。 |
| web_20260523_022509_a44cb853 | 跳 | 8.690 | semantic_mismatch | semantic_mismatch | jump_low_other | phase_endpoint_order_mismatch | 0.767/0.667 | - | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.77/0.67。 |
| web_20260523_052731_8f51941f | 跳 | 8.706 | semantic_mismatch | semantic_mismatch | jump_low_other | phase_endpoint_order_mismatch | 0.840/0.920 | - | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.84/0.92。 |
| web_20260523_010234_e2d59e5e | 跳 | 8.937 | semantic_mismatch | semantic_mismatch | jump_two_hand_presence_low | phase_endpoint_order_mismatch | 0.667/0.422 | - | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.67/0.42。 |
| web_20260523_021006_aef545ce | 跳 | 9.028 | semantic_mismatch | semantic_mismatch | jump_two_hand_presence_low | phase_endpoint_order_mismatch | 0.733/0.600 | - | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.73/0.60。 |
| web_20260523_005941_0ec0ccab | 跳 | 9.233 | semantic_mismatch | semantic_mismatch | jump_two_hand_presence_low | phase_endpoint_order_mismatch | 0.800/0.533 | - | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.80/0.53。 |
| web_20260523_063109_8727dac1 | 跳 | 9.551 | semantic_mismatch | semantic_mismatch | jump_two_hand_presence_low | phase_endpoint_order_mismatch | 0.600/1.000 | - | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.60/1.00。 |
| web_20260523_031247_f927176a | 跳 | 10.543 | semantic_mismatch | semantic_mismatch | jump_two_hand_presence_low | phase_endpoint_order_mismatch | 0.933/0.533 | - | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.93/0.53。 |
| web_20260523_010004_7eaf7ee3 | 跳 | 11.213 | semantic_mismatch | semantic_mismatch | jump_two_hand_presence_low | phase_endpoint_order_mismatch | 0.800/0.533 | - | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.80/0.53。 |
| web_20260523_044323_2eb9eb7e | 跳 | 11.645 | semantic_mismatch | semantic_mismatch | jump_low_other | phase_endpoint_order_mismatch | 0.760/0.800 | - | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.76/0.80。 |
| web_20260523_063026_c2f04725 | 跳 | 12.248 | semantic_mismatch | semantic_mismatch | jump_two_hand_presence_low | phase_endpoint_order_mismatch | 0.640/0.920 | - | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.64/0.92。 |
| web_20260523_031235_d0de0d44 | 跳 | 15.226 | semantic_mismatch | semantic_mismatch | jump_two_hand_presence_low | phase_endpoint_order_mismatch | 0.533/0.600 | - | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.53/0.60。 |
| web_20260523_001152_83546751 | 跳 | 15.534 | semantic_mismatch | semantic_mismatch | jump_two_hand_presence_low | phase_endpoint_order_mismatch | 0.667/0.600 | - | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.67/0.60。 |
| web_20260523_063052_fc94e4f7 | 跳 | 17.520 | semantic_mismatch | semantic_mismatch | jump_low_other | phase_endpoint_order_mismatch | 0.720/0.840 | - | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.72/0.84。 |
| web_20260523_052715_1ad3c2d2 | 跳 | 19.379 | semantic_mismatch | semantic_mismatch | jump_two_hand_presence_low | phase_endpoint_order_mismatch | 0.640/0.760 | - | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.64/0.76。 |
| web_20260602_233302_d92c0ce2 | 跳 | 55.326 | semantic_mismatch | semantic_mismatch | jump_low_other | phase_endpoint_order_mismatch | 0.889/1.000 | - | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.89/1.00。 |

# 花/跳网页评分目标完成度审计

- 生成时间：`2026-06-03T01:28:57`
- 目标完成状态：`NOT_READY`
- 口径：快速审计，不重新运行 Holistic，不重跑 DTW gate；读取当前运行态和最新质量门报告。

## 证据门

| gate | 状态 | 说明 |
|---|---|---|
| backend_ready | PASS | worker=ready, pid=811485, reload_count=7, last_reload_error=None |
| watcher_online | PASS | event=no_target_samples, watcher_pid=2553122, generated_at=2026-06-03T01:28:55 |
| marker_available | PASS | last_request_id=web_20260602_233348_53e3df5d, marker_after_new=0, target_new=0 |
| combined_quality_gate_passed | PASS | quality_gate=/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_v1/flower_jump_quality_gate.json, subgates=[('web_regression', True), ('discrimination_gate', True), ('pose_robustness_gate', True)] |
| fresh_real_webcam_target_samples_diagnosed | MISSING | marker_after_target_count=0, latest_diagnosis=- |

## 最新质量门摘要

- 报告：`-`
- 综合状态：`PASS`
- 网页回归：replay `168` / diagnostics `149`，有效 `124`，正常+边界 `120`，有效低分 `4`，有效率 `96.8%`。
- 负例判别 `花`：min_positive `80.311`，max_negative `32.047`，margin `48.263`。
- 负例判别 `跳`：min_positive `76.823`，max_negative `31.418`，margin `45.406`。
- 坐姿扰动 `花`：min `80.446`，weakest `hand_jitter_small`。
- 坐姿扰动 `跳`：min `93.015`，weakest `hand_jitter_small`。

## 当前 marker

- last_request_id：`web_20260602_233348_53e3df5d`
- marker 后新增样本：`0`
- marker 后新增花/跳样本：`0`

## 结论

- 当前工程质量门已经通过，但还没有新的真实网页摄像头 `花/跳` 样本诊断证据。
- 下一步仍需用户通过 5080 页面实际采集 `花/跳`，由 watcher 自动生成增量回归和骨架可视化后再复查。

# 花/跳网页评分目标完成度审计

- 生成时间：`2026-06-03T04:30:36`
- 目标完成状态：`NOT_READY`
- 口径：快速审计，不重新运行 Holistic，不重跑 DTW gate；读取当前运行态和最新质量门报告。

## 证据门

| gate | 状态 | 说明 |
|---|---|---|
| backend_ready | PASS | worker=ready, pid=811485, reload_count=11, last_reload_error=None |
| watcher_online | PASS | event=no_target_samples, watcher_pid=3638423, generated_at=2026-06-03T04:30:35 |
| marker_available | PASS | last_request_id=web_20260602_233348_53e3df5d, marker_after_new=0, target_new=0 |
| combined_quality_gate_passed | PASS | quality_gate=/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_v5/flower_jump_quality_gate.json, subgates=[('web_regression', True), ('web_confusion_gate', True), ('discrimination_gate', True), ('pose_robustness_gate', True), ('frame_count_robustness_gate', True)] |
| fresh_real_webcam_target_samples_diagnosed | MISSING | marker_after_target_count=0, latest_diagnosis=-, browser_capture_evidence={'request_ids': [], 'passed': False, 'rows': []} |

## 最新质量门摘要

- 报告：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_v5/flower_jump_quality_gate.md`
- 综合状态：`PASS`
- 子门：`web_regression`=PASS，`web_confusion_gate`=PASS，`discrimination_gate`=PASS，`pose_robustness_gate`=PASS，`frame_count_robustness_gate`=PASS。
- 网页回归：replay `168` / diagnostics `149`，有效 `128`，正常+边界 `124`，有效低分 `4`，有效率 `96.9%`。
- 交叉混淆：samples `149`，eligible `124`，pass `124`，fail `0`。
- 交叉混淆 `花`：other_score_max `8.218`，margin_min `59.840`。
- 交叉混淆 `跳`：other_score_max `41.535`，margin_min `29.317`。
- 负例判别 `花`：min_positive `80.311`，max_negative `32.047`，margin `48.263`。
- 负例判别 `跳`：min_positive `76.823`，max_negative `31.418`，margin `45.406`。
- 坐姿扰动 `花`：min `80.446`，weakest `hand_jitter_small`。
- 坐姿扰动 `跳`：min `93.015`，weakest `hand_jitter_small`。
- 帧数采样 `花`：min_valid_frames `12`，min `78.482`，weakest `uniform_12f`。
- 帧数采样 `跳`：min_valid_frames `6`，min `70.488`，weakest `drop_every_3_keep_ends`。

## 当前 marker

- last_request_id：`web_20260602_233348_53e3df5d`
- marker 后新增样本：`0`
- marker 后新增花/跳样本：`0`

## 真实网页采集证据

- 综合状态：`MISSING`
- 当前没有 latest diagnosis request_id 可用于判定真实网页采集来源。

## 结论

- 当前工程质量门已经通过，但还没有新的真实网页摄像头 `花/跳` 样本诊断证据。
- 下一步仍需用户通过 5080 页面实际采集 `花/跳`，由 watcher 自动生成增量回归和骨架可视化后再复查。

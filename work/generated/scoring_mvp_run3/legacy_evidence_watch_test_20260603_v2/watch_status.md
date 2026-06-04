# 网页样本自动诊断 Watcher 状态

- 生成时间：`2026-06-03T04:16:46`
- 当前事件：`diagnose_done`
- watcher PID：`3576132`
- Web 样本根目录：`/data/WYC/signLanguage/work/generated/web_scoring_mvp`
- marker：`work/generated/scoring_mvp_run3/web_sample_marker_legacy_evidence_test_20260603.json`
- marker last_request_id：`web_20260602_233302_d92c0ce2`
- 监听词条：`花, 跳`
- 轮询间隔：`20.0` 秒
- 新增样本：`2`，分布 `{'花': 1, '跳': 1}`
- 新增目标样本：`2`，request_id `web_20260602_233343_899e6970, web_20260602_233348_53e3df5d`

## 最近诊断

- request_id：`web_20260602_233343_899e6970, web_20260602_233348_53e3df5d`
- 回归报告：`work/generated/scoring_mvp_run3/legacy_evidence_watch_test_20260603_v2/web_new_samples_watch_20260603_041629/flower_jump_regression/flower_jump_web_regression.md`
- 语义诊断：`work/generated/scoring_mvp_run3/legacy_evidence_watch_test_20260603_v2/web_new_samples_watch_20260603_041629/flower_jump_regression/flower_jump_diagnostics/web_semantic_diagnostics.md`
- 交叉混淆：`work/generated/scoring_mvp_run3/legacy_evidence_watch_test_20260603_v2/web_new_samples_watch_20260603_041629/flower_jump_confusion/flower_jump_web_confusion_gate.md`
- 骨架可视化：`work/generated/scoring_mvp_run3/legacy_evidence_watch_test_20260603_v2/web_new_samples_watch_20260603_041629/holistic_visuals/web_holistic_visual_recovery_summary.md`
- 状态报告：`work/generated/scoring_mvp_run3/legacy_evidence_watch_test_20260603_v2/web_new_samples_watch_20260603_041629/new_web_samples_status.md`
- regression_returncode：`0`
- confusion_returncode：`0`
- visual_returncode：`0`

## 最新样本建议

| request | 词条 | 分数 | 处置 | 采集质量 | 诊断 | 建议 |
|---|---|---:|---|---|---|---|
| web_20260602_233343_899e6970 | 花 | 76.9 | normal | score_valid | flower_core_accepted | 开花核心段可评分；继续保持手部完整入画和清晰张开动态。 |
| web_20260602_233348_53e3df5d | 跳 | 88.6 | normal | score_valid | jump_core_accepted | 双手弹跳核心语义可评分；继续保持两只手同时稳定入画。 |

## 花/跳交叉混淆

| request | 目标 | 目标分 | 交叉词 | 交叉分 | margin | gate | 原因 |
|---|---|---:|---|---:|---:|---|---|
| web_20260602_233343_899e6970 | 花 | 76.9 | 跳 | 7.5 | 69.4 | PASS | passed |
| web_20260602_233348_53e3df5d | 跳 | 88.6 | 花 | 14.6 | 74.0 | PASS | passed |

## 目标完成度

- 状态：`READY_TO_COMPLETE`
- 审计报告：`work/generated/scoring_mvp_run3/legacy_evidence_watch_test_20260603_v2/readiness/flower_jump_goal_readiness_audit.md`
- 缺失证据：`-`
- 真实网页采集证据：`PASS`，样本数 `2`

| request | 词条 | 帧数 | 时长 | 证据等级 | 证据 |
|---|---|---:|---:|---|---|
| web_20260602_233343_899e6970 | 花 | 53 | 5.30 | legacy_frame_slice_metadata | legacy_frame_slice_metadata |
| web_20260602_233348_53e3df5d | 跳 | 19 | 1.90 | legacy_frame_slice_metadata | legacy_frame_slice_metadata |
- 证据门：
  - `backend_ready`：`PASS`
  - `watcher_online`：`PASS`
  - `marker_available`：`PASS`
  - `combined_quality_gate_passed`：`PASS`
  - `fresh_real_webcam_target_samples_diagnosed`：`PASS`

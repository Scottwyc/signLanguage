# 网页样本自动诊断 Watcher 状态

- 生成时间：`2026-06-03T02:23:48`
- 当前事件：`diagnose_done`
- watcher PID：`3000857`
- Web 样本根目录：`/data/WYC/signLanguage/work/generated/web_scoring_mvp`
- marker：`work/generated/scoring_mvp_run3/web_sample_marker_test_after_233301.json`
- marker last_request_id：`web_20260602_233301_233b8215`
- 监听词条：`花, 跳`
- 轮询间隔：`20.0` 秒
- 新增样本：`3`，分布 `{'花': 1, '跳': 2}`
- 新增目标样本：`3`，request_id `web_20260602_233302_d92c0ce2, web_20260602_233343_899e6970, web_20260602_233348_53e3df5d`

## 最近诊断

- request_id：`web_20260602_233302_d92c0ce2, web_20260602_233343_899e6970, web_20260602_233348_53e3df5d`
- 回归报告：`work/generated/scoring_mvp_run3/web_sample_watch_advice_payload_test_20260603_v1/web_new_samples_watch_20260603_022333/flower_jump_regression/flower_jump_web_regression.md`
- 语义诊断：`work/generated/scoring_mvp_run3/web_sample_watch_advice_payload_test_20260603_v1/web_new_samples_watch_20260603_022333/flower_jump_regression/flower_jump_diagnostics/web_semantic_diagnostics.md`
- 骨架可视化：`work/generated/scoring_mvp_run3/web_sample_watch_advice_payload_test_20260603_v1/web_new_samples_watch_20260603_022333/holistic_visuals/web_holistic_visual_recovery_summary.md`
- 状态报告：`work/generated/scoring_mvp_run3/web_sample_watch_advice_payload_test_20260603_v1/web_new_samples_watch_20260603_022333/new_web_samples_status.md`
- regression_returncode：`0`
- visual_returncode：`0`

## 最新样本建议

| request | 词条 | 分数 | 处置 | 采集质量 | 诊断 | 建议 |
|---|---|---:|---|---|---|---|
| web_20260602_233302_d92c0ce2 | 跳 | 70.7 | borderline_review | score_valid | jump_core_accepted | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.89/1.00。 |
| web_20260602_233343_899e6970 | 花 | 76.9 | normal | score_valid | flower_core_accepted | 开花核心段可评分；继续保持手部完整入画和清晰张开动态。 |
| web_20260602_233348_53e3df5d | 跳 | 88.6 | normal | score_valid | jump_core_accepted | 双手弹跳核心语义可评分；继续保持两只手同时稳定入画。 |

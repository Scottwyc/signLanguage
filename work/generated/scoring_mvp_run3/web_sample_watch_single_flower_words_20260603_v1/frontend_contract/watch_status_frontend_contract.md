# Watch Status Frontend Contract Check

- generated_at: `2026-06-03T05:39:00`
- status: **PASS**
- base_url: `http://127.0.0.1:5080`
- watch_status_json: `work/generated/scoring_mvp_run3/web_sample_watch_single_flower_words_20260603_v1/watch_status.json`
- app_js: `/data/WYC/signLanguage/work/web/static/app.js`
- failed_count: `0`
- warning_count: `0`

## Payload Summary

- event: `diagnose_done`
- generated_at: `2026-06-03T05:39:00`
- watcher_pid: `4000112`
- target_count: `1`
- goal_status: `READY_TO_COMPLETE`
- missing_gates: `[]`

## Checks

| check | result | severity | detail |
| --- | --- | --- | --- |
| `watch_status_json_exists` | PASS | `fail` | work/generated/scoring_mvp_run3/web_sample_watch_single_flower_words_20260603_v1/watch_status.json |
| `watch_status_json_loadable` | PASS | `fail` | work/generated/scoring_mvp_run3/web_sample_watch_single_flower_words_20260603_v1/watch_status.json |
| `watch_status_is_object` | PASS | `fail` | type=dict |
| `watch_status_generated_at` | PASS | `fail` | 2026-06-03T05:39:00 |
| `watch_status_event_known` | PASS | `fail` | diagnose_done |
| `watcher_pid_present` | PASS | `fail` | watcher_pid=4000112 |
| `watch_status_has_status_block` | PASS | `fail` | keys=['checked_at', 'marker_last_request_id', 'new_summary', 'target_request_ids', 'target_summary'] |
| `watch_status_fresh` | PASS | `fail` | age_sec=0.4, max_age_sec=180.0 |
| `target_summary_present` | PASS | `fail` | target_summary={'count': 1, 'first_request_id': 'web_20260602_233343_899e6970', 'last_request_id': 'web_20260602_233343_899e6970', 'by_word': {'花': 1}} |
| `target_summary_count_numeric` | PASS | `fail` | count=1 |
| `goal_readiness_present` | PASS | `fail` | keys=['browser_capture_evidence', 'gates', 'generated_at', 'json_path', 'md_path', 'missing_gates', 'quality_gate_json', 'quality_gate_md', 'readiness_summary', 'ready_to_complete', 'returncode', 'status_label', 'stderr', 'stdout', 'web_root'] |
| `goal_readiness_status_label_present` | PASS | `fail` | status_label=READY_TO_COMPLETE |
| `goal_readiness_missing_gates_list` | PASS | `fail` | missing_gates=[] |
| `browser_capture_evidence_present` | PASS | `fail` | type=dict |
| `browser_capture_evidence_rows_list` | PASS | `fail` | rows_type=list |
| `latest_diagnosis_object` | PASS | `fail` | keys=['confusion_csv', 'confusion_json', 'confusion_reason_counts', 'confusion_report', 'confusion_returncode', 'confusion_sample_summaries', 'confusion_stderr', 'confusion_stdout', 'diagnosed_request_ids', 'diagnosed_words', 'generated_at', 'json_path', 'marker_last_request_id', 'marker_path', 'md_path', 'new_summary', 'regression_report', 'regression_returncode', 'regression_stderr', 'regression_stdout', 'semantic_diagnostics_csv', 'semantic_diagnostics_json', 'semantic_diagnostics_report', 'semantic_sample_summaries', 'semantic_triage_counts', 'static_artifacts', 'target_summary', 'visual_report', 'visual_returncode', 'visual_stderr', 'visual_stdout', 'web_root', 'words'] |
| `latest_diagnosis_regression_returncode_zero` | PASS | `fail` | regression_returncode=0 |
| `latest_diagnosis_confusion_returncode_zero` | PASS | `fail` | confusion_returncode=0 |
| `latest_diagnosis_visual_returncode_zero` | PASS | `fail` | visual_returncode=0 |
| `static_artifacts_index_url_present` | PASS | `fail` | index_url=/static/latest_watch_single_flower_words_test/index.html |
| `static_artifacts_manifest_url_present` | PASS | `fail` | manifest_url=/static/latest_watch_single_flower_words_test/artifacts.json |
| `static_artifact_urls_present` | PASS | `fail` | checked_count=14 |
| `artifact_url_200:diagnosis_index` | PASS | `fail` | http://127.0.0.1:5080/static/latest_watch_single_flower_words_test/index.html status=200 detail=ok |
| `artifact_url_200:artifact_manifest` | PASS | `fail` | http://127.0.0.1:5080/static/latest_watch_single_flower_words_test/artifacts.json status=200 detail=ok |
| `artifact_url_200:report:状态报告` | PASS | `fail` | http://127.0.0.1:5080/static/latest_watch_single_flower_words_test/reports/status.md status=200 detail=ok |
| `artifact_url_200:report:网页回归` | PASS | `fail` | http://127.0.0.1:5080/static/latest_watch_single_flower_words_test/reports/regression.md status=200 detail=ok |
| `artifact_url_200:report:语义诊断` | PASS | `fail` | http://127.0.0.1:5080/static/latest_watch_single_flower_words_test/reports/semantic.md status=200 detail=ok |
| `artifact_url_200:report:交叉混淆` | PASS | `fail` | http://127.0.0.1:5080/static/latest_watch_single_flower_words_test/reports/confusion.md status=200 detail=ok |
| `artifact_url_200:report:骨架可视化` | PASS | `fail` | http://127.0.0.1:5080/static/latest_watch_single_flower_words_test/reports/visual.md status=200 detail=ok |
| `artifact_url_200:visual:花 视觉摘要` | PASS | `fail` | http://127.0.0.1:5080/static/latest_watch_single_flower_words_test/visuals/web_20260602_233343_899e6970/visual_summary.json status=200 detail=ok |
| `artifact_url_200:visual:花 测试骨架联系表` | PASS | `fail` | http://127.0.0.1:5080/static/latest_watch_single_flower_words_test/visuals/web_20260602_233343_899e6970/query_skeleton_contact_sheet.png status=200 detail=ok |
| `artifact_url_200:visual:花 测试识别时间线` | PASS | `fail` | http://127.0.0.1:5080/static/latest_watch_single_flower_words_test/visuals/web_20260602_233343_899e6970/query_presence_timeline.png status=200 detail=ok |
| `artifact_url_200:visual:花 测试完整时间线` | PASS | `fail` | http://127.0.0.1:5080/static/latest_watch_single_flower_words_test/visuals/web_20260602_233343_899e6970/query_timeline.png status=200 detail=ok |
| `artifact_url_200:visual:花 标准骨架联系表` | PASS | `fail` | http://127.0.0.1:5080/static/latest_watch_single_flower_words_test/visuals/web_20260602_233343_899e6970/standard_skeleton_contact_sheet.png status=200 detail=ok |
| `artifact_url_200:visual:花 标准识别时间线` | PASS | `fail` | http://127.0.0.1:5080/static/latest_watch_single_flower_words_test/visuals/web_20260602_233343_899e6970/standard_presence_timeline.png status=200 detail=ok |
| `artifact_url_200:visual:花 标准完整时间线` | PASS | `fail` | http://127.0.0.1:5080/static/latest_watch_single_flower_words_test/visuals/web_20260602_233343_899e6970/standard_timeline.png status=200 detail=ok |
| `frontend_app_js_file_exists` | PASS | `fail` | /data/WYC/signLanguage/work/web/static/app.js |
| `frontend_js_token:WATCH_REFRESH_AFTER_SCORE_DELAYS_MS` | PASS | `fail` | token=WATCH_REFRESH_AFTER_SCORE_DELAYS_MS |
| `frontend_js_token:refreshWatchStatus` | PASS | `fail` | token=refreshWatchStatus |
| `frontend_js_token:formatBrowserCaptureEvidence` | PASS | `fail` | token=formatBrowserCaptureEvidence |
| `frontend_js_token:formatReadinessSummary` | PASS | `fail` | token=formatReadinessSummary |
| `frontend_js_token:formatFrontendContractCheck` | PASS | `fail` | token=formatFrontendContractCheck |
| `frontend_js_token:renderWatchArtifactLinks` | PASS | `fail` | token=renderWatchArtifactLinks |
| `frontend_js_token:readiness_summary` | PASS | `fail` | token=readiness_summary |
| `frontend_js_token:frontend_contract_check` | PASS | `fail` | token=frontend_contract_check |
| `frontend_js_token:static_artifacts` | PASS | `fail` | token=static_artifacts |
| `frontend_js_token:/static/watch_status.json` | PASS | `fail` | token=/static/watch_status.json |
| `frontend_js_token:scheduleWatchRefreshAfterScore` | PASS | `fail` | token=scheduleWatchRefreshAfterScore |
| `frontend_app_js_http_200` | PASS | `fail` | http://127.0.0.1:5080/static/app.js status=200 detail=ok |

## Artifact URLs

| label | ok | status | url |
| --- | --- | --- | --- |
| `diagnosis_index` | `True` | `200` | http://127.0.0.1:5080/static/latest_watch_single_flower_words_test/index.html |
| `artifact_manifest` | `True` | `200` | http://127.0.0.1:5080/static/latest_watch_single_flower_words_test/artifacts.json |
| `report:状态报告` | `True` | `200` | http://127.0.0.1:5080/static/latest_watch_single_flower_words_test/reports/status.md |
| `report:网页回归` | `True` | `200` | http://127.0.0.1:5080/static/latest_watch_single_flower_words_test/reports/regression.md |
| `report:语义诊断` | `True` | `200` | http://127.0.0.1:5080/static/latest_watch_single_flower_words_test/reports/semantic.md |
| `report:交叉混淆` | `True` | `200` | http://127.0.0.1:5080/static/latest_watch_single_flower_words_test/reports/confusion.md |
| `report:骨架可视化` | `True` | `200` | http://127.0.0.1:5080/static/latest_watch_single_flower_words_test/reports/visual.md |
| `visual:花 视觉摘要` | `True` | `200` | http://127.0.0.1:5080/static/latest_watch_single_flower_words_test/visuals/web_20260602_233343_899e6970/visual_summary.json |
| `visual:花 测试骨架联系表` | `True` | `200` | http://127.0.0.1:5080/static/latest_watch_single_flower_words_test/visuals/web_20260602_233343_899e6970/query_skeleton_contact_sheet.png |
| `visual:花 测试识别时间线` | `True` | `200` | http://127.0.0.1:5080/static/latest_watch_single_flower_words_test/visuals/web_20260602_233343_899e6970/query_presence_timeline.png |
| `visual:花 测试完整时间线` | `True` | `200` | http://127.0.0.1:5080/static/latest_watch_single_flower_words_test/visuals/web_20260602_233343_899e6970/query_timeline.png |
| `visual:花 标准骨架联系表` | `True` | `200` | http://127.0.0.1:5080/static/latest_watch_single_flower_words_test/visuals/web_20260602_233343_899e6970/standard_skeleton_contact_sheet.png |
| `visual:花 标准识别时间线` | `True` | `200` | http://127.0.0.1:5080/static/latest_watch_single_flower_words_test/visuals/web_20260602_233343_899e6970/standard_presence_timeline.png |
| `visual:花 标准完整时间线` | `True` | `200` | http://127.0.0.1:5080/static/latest_watch_single_flower_words_test/visuals/web_20260602_233343_899e6970/standard_timeline.png |

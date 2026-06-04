# Watch Status Frontend Contract Check

- generated_at: `2026-06-03T06:04:46`
- status: **PASS**
- base_url: `http://127.0.0.1:5080`
- watch_status_json: `/data/WYC/signLanguage/work/web/static/watch_status.json`
- index_html: `/data/WYC/signLanguage/work/web/static/index.html`
- app_js: `/data/WYC/signLanguage/work/web/static/app.js`
- styles_css: `/data/WYC/signLanguage/work/web/static/styles.css`
- failed_count: `0`
- warning_count: `0`

## Payload Summary

- event: `no_target_samples`
- generated_at: `2026-06-03T06:04:34`
- watcher_pid: `4021854`
- target_count: `0`
- goal_status: `NOT_READY`
- missing_gates: `['fresh_real_webcam_target_samples_diagnosed']`

## Checks

| check | result | severity | detail |
| --- | --- | --- | --- |
| `watch_status_json_exists` | PASS | `fail` | /data/WYC/signLanguage/work/web/static/watch_status.json |
| `watch_status_json_loadable` | PASS | `fail` | /data/WYC/signLanguage/work/web/static/watch_status.json |
| `watch_status_is_object` | PASS | `fail` | type=dict |
| `watch_status_generated_at` | PASS | `fail` | 2026-06-03T06:04:34 |
| `watch_status_event_known` | PASS | `fail` | no_target_samples |
| `watcher_pid_present` | PASS | `fail` | watcher_pid=4021854 |
| `watch_status_has_status_block` | PASS | `fail` | keys=['checked_at', 'marker_last_request_id', 'new_summary', 'target_request_ids', 'target_summary'] |
| `target_summary_present` | PASS | `fail` | target_summary={'count': 0, 'first_request_id': '', 'last_request_id': '', 'by_word': {}} |
| `target_summary_count_numeric` | PASS | `fail` | count=0 |
| `goal_readiness_present` | PASS | `fail` | keys=['browser_capture_evidence', 'gates', 'generated_at', 'json_path', 'md_path', 'missing_gates', 'quality_gate_json', 'quality_gate_md', 'readiness_summary', 'ready_to_complete', 'returncode', 'status_label', 'stderr', 'stdout', 'web_root'] |
| `goal_readiness_status_label_present` | PASS | `fail` | status_label=NOT_READY |
| `goal_readiness_missing_gates_list` | PASS | `fail` | missing_gates=['fresh_real_webcam_target_samples_diagnosed'] |
| `browser_capture_evidence_present` | PASS | `fail` | type=dict |
| `browser_capture_evidence_rows_list` | PASS | `fail` | rows_type=list |
| `latest_diagnosis_optional_when_no_targets` | PASS | `warn` | target_count=0, latest_diagnosis=null |
| `static_artifacts_optional` | PASS | `fail` | no static_artifacts in current payload |
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
| `frontend_js_token:renderWatchWordCoverage` | PASS | `fail` | token=renderWatchWordCoverage |
| `frontend_js_token:renderWatchNextRetestStep` | PASS | `fail` | token=renderWatchNextRetestStep |
| `frontend_js_token:watchWordCoverage` | PASS | `fail` | token=watchWordCoverage |
| `frontend_js_token:watchNextStep` | PASS | `fail` | token=watchNextStep |
| `frontend_app_js_http_200` | PASS | `fail` | http://127.0.0.1:5080/static/app.js status=200 detail=ok |
| `frontend_index_html_file_exists` | PASS | `fail` | /data/WYC/signLanguage/work/web/static/index.html |
| `frontend_html_token:watchWordCoverage` | PASS | `fail` | token=watchWordCoverage |
| `frontend_html_token:watch-word-coverage` | PASS | `fail` | token=watch-word-coverage |
| `frontend_html_token:watchNextStep` | PASS | `fail` | token=watchNextStep |
| `frontend_html_token:watch-next-step` | PASS | `fail` | token=watch-next-step |
| `frontend_index_http_200` | PASS | `fail` | http://127.0.0.1:5080/ status=200 detail=ok |
| `frontend_styles_css_file_exists` | PASS | `fail` | /data/WYC/signLanguage/work/web/static/styles.css |
| `frontend_css_token:watch-word-coverage` | PASS | `fail` | token=watch-word-coverage |
| `frontend_css_token:watch-word-chip` | PASS | `fail` | token=watch-word-chip |
| `frontend_css_token:watch-word-chip-covered` | PASS | `fail` | token=watch-word-chip-covered |
| `frontend_css_token:watch-word-chip-missing` | PASS | `fail` | token=watch-word-chip-missing |
| `frontend_css_token:watch-word-chip-failed` | PASS | `fail` | token=watch-word-chip-failed |
| `frontend_css_token:watch-next-step` | PASS | `fail` | token=watch-next-step |
| `frontend_styles_css_http_200` | PASS | `fail` | http://127.0.0.1:5080/static/styles.css status=200 detail=ok |

# 花/跳网页评分目标完成度审计

- 生成时间：`2026-06-03T08:31:05`
- 目标完成状态：`NOT_READY`
- 分层状态：运行态 `PASS`；算法质量 `PASS`；真实复测 `MISSING`。
- 当前阻塞：`fresh_real_webcam_target_samples_diagnosed`
- 状态说明：算法质量门和运行态已就绪，仍缺 marker 后真实网页摄像头花/跳样本诊断。
- 口径：快速审计，不重新运行 Holistic，不重跑 DTW gate；读取当前运行态和最新质量门报告。

## 分层就绪状态

| 层级 | 状态 | 相关证据门 | 缺失项 |
|---|---|---|---|
| 运行态 | PASS | `backend_ready, watcher_online, marker_available` | `-` |
| 算法质量 | PASS | `combined_quality_gate_passed` | `-` |
| 真实网页复测 | MISSING | `fresh_real_webcam_target_samples_diagnosed` | `fresh_real_webcam_target_samples_diagnosed` |

## 证据门

| gate | 状态 | 说明 |
|---|---|---|
| backend_ready | PASS | worker=ready, pid=811485, reload_count=13, last_reload_error=None |
| watcher_online | PASS | event=diagnose_done, watcher_pid=3576132, generated_at=2026-06-03T04:16:46 |
| marker_available | PASS | last_request_id=web_20260602_233348_53e3df5d, marker_after_new=0, target_new=0 |
| combined_quality_gate_passed | PASS | quality_gate=/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_composite_phase_guard_8gate_v1/flower_jump_quality_gate.json, subgates=[('web_regression', True), ('web_confusion_gate', True), ('discrimination_gate', True), ('pose_robustness_gate', True), ('frame_count_robustness_gate', True), ('missing_mask_robustness_gate', True), ('temporal_padding_robustness_gate', True), ('phase_order_robustness_gate', True)] |
| fresh_real_webcam_target_samples_diagnosed | MISSING | marker_after_target_count=0, latest_diagnosis={'generated_at': '2026-06-03T04:16:29', 'web_root': '/data/WYC/signLanguage/work/generated/scoring_mvp_run3/strong_browser_evidence_fixture_20260603_v1/strong_nonuniform_web_root', 'marker_path': 'work/generated/scoring_mvp_run3/web_sample_marker_legacy_evidence_test_20260603.json', 'marker_last_request_id': 'web_20260602_233302_d92c0ce2', 'new_summary': {'count': 2, 'first_request_id': 'web_20260602_233343_899e6970', 'last_request_id': 'web_20260602_233348_53e3df5d', 'by_word': {'花': 1, '跳': 1}}, 'target_summary': {'count': 2, 'first_request_id': 'web_20260602_233343_899e6970', 'last_request_id': 'web_20260602_233348_53e3df5d', 'by_word': {'花': 1, '跳': 1}}, 'words': ['花', '跳'], 'diagnosed_request_ids': ['web_20260602_233343_899e6970', 'web_20260602_233348_53e3df5d'], 'regression_report': 'work/generated/scoring_mvp_run3/legacy_evidence_watch_test_20260603_v2/web_new_samples_watch_20260603_041629/flower_jump_regression/flower_jump_web_regression.md', 'semantic_diagnostics_report': 'work/generated/scoring_mvp_run3/legacy_evidence_watch_test_20260603_v2/web_new_samples_watch_20260603_041629/flower_jump_regression/flower_jump_diagnostics/web_semantic_diagnostics.md', 'semantic_diagnostics_json': 'work/generated/scoring_mvp_run3/legacy_evidence_watch_test_20260603_v2/web_new_samples_watch_20260603_041629/flower_jump_regression/flower_jump_diagnostics/web_semantic_diagnostics.json', 'semantic_diagnostics_csv': 'work/generated/scoring_mvp_run3/legacy_evidence_watch_test_20260603_v2/web_new_samples_watch_20260603_041629/flower_jump_regression/flower_jump_diagnostics/web_semantic_diagnostics.csv', 'semantic_sample_summaries': [{'request_id': 'web_20260602_233343_899e6970', 'target_word': '花', 'score': 76.89925771288746, 'band': 'normal_like', 'triage_priority': 'normal', 'capture_quality_status': 'score_valid', 'diagnosis': 'flower_core_accepted', 'sample_advice': '开花核心段可评分；继续保持手部完整入画和清晰张开动态。', 'left_hand_presence': 0.0, 'right_hand_presence': 0.7924528301886793, 'semantic_core_presence_full': 0.7924528301886793, 'semantic_core_presence_window': 1.0}, {'request_id': 'web_20260602_233348_53e3df5d', 'target_word': '跳', 'score': 88.57686551142223, 'band': 'normal_like', 'triage_priority': 'normal', 'capture_quality_status': 'score_valid', 'diagnosis': 'jump_core_accepted', 'sample_advice': '双手弹跳核心语义可评分；继续保持两只手同时稳定入画。', 'left_hand_presence': 0.8421052631578947, 'right_hand_presence': 0.8947368421052632, 'semantic_core_presence_full': 0.8888888888888888, 'semantic_core_presence_window': 0.8333333333333334}], 'semantic_triage_counts': {'normal': 2}, 'regression_returncode': 0, 'confusion_report': 'work/generated/scoring_mvp_run3/legacy_evidence_watch_test_20260603_v2/web_new_samples_watch_20260603_041629/flower_jump_confusion/flower_jump_web_confusion_gate.md', 'confusion_json': 'work/generated/scoring_mvp_run3/legacy_evidence_watch_test_20260603_v2/web_new_samples_watch_20260603_041629/flower_jump_confusion/flower_jump_web_confusion_gate.json', 'confusion_csv': 'work/generated/scoring_mvp_run3/legacy_evidence_watch_test_20260603_v2/web_new_samples_watch_20260603_041629/flower_jump_confusion/flower_jump_web_confusion_cases.csv', 'confusion_sample_summaries': [{'request_id': 'web_20260602_233343_899e6970', 'target_word': '花', 'other_word': '跳', 'target_score': 76.89925771288746, 'other_score': 7.473900153605198, 'margin': 69.42535755928226, 'eligible_for_gate': True, 'confusion_pass': True, 'confusion_reason': 'passed', 'target_capture_quality_status': 'score_valid', 'target_capture_quality_reason': 'score_valid', 'other_capture_quality_status': 'needs_recapture', 'other_capture_quality_reason': 'jump_two_hand_presence_low'}, {'request_id': 'web_20260602_233348_53e3df5d', 'target_word': '跳', 'other_word': '花', 'target_score': 88.57686551142223, 'other_score': 14.588278097991585, 'margin': 73.98858741343064, 'eligible_for_gate': True, 'confusion_pass': True, 'confusion_reason': 'passed', 'target_capture_quality_status': 'score_valid', 'target_capture_quality_reason': 'score_valid', 'other_capture_quality_status': 'semantic_mismatch', 'other_capture_quality_reason': 'flower_jump_like_two_hand_confusion'}], 'confusion_reason_counts': {'passed': 2}, 'confusion_returncode': 0, 'visual_report': 'work/generated/scoring_mvp_run3/legacy_evidence_watch_test_20260603_v2/web_new_samples_watch_20260603_041629/holistic_visuals/web_holistic_visual_recovery_summary.md', 'visual_returncode': 0, 'regression_stdout': "已生成花/跳网页回归 JSON：work/generated/scoring_mvp_run3/legacy_evidence_watch_test_20260603_v2/web_new_samples_watch_20260603_041629/flower_jump_regression/flower_jump_web_regression.json\n已生成花/跳网页回归报告：work/generated/scoring_mvp_run3/legacy_evidence_watch_test_20260603_v2/web_new_samples_watch_20260603_041629/flower_jump_regression/flower_jump_web_regression.md\n回归状态：PASS\n- backend_ready: PASS (url=http://127.0.0.1:5080/api/status, worker=ready, reload_error=-, error=-)\n- replay_no_errors: PASS (samples=2, errors=0)\n- diagnostics_no_errors: PASS (samples=2, errors=0)\n- effective_rate_total: PASS (rate=100.0%, threshold=95.0%)\n- effective_rate_花: PASS (rate=100.0%, reliable=1, normal_or_borderline=1, low=0)\n- effective_rate_跳: PASS (rate=100.0%, reliable=1, normal_or_borderline=1, low=0)\n- jump_effective_low_zero: PASS (effective_low=0)\n- flower_effective_low_bounded: PASS (effective_low=0, max=5, diagnoses={})\n- flower_effective_low_explained: PASS (allowed=['flower_opening_guard_failed'], observed={})\n", 'regression_stderr': '', 'confusion_stdout': '已生成花/跳网页交叉混淆 JSON：work/generated/scoring_mvp_run3/legacy_evidence_watch_test_20260603_v2/web_new_samples_watch_20260603_041629/flower_jump_confusion/flower_jump_web_confusion_gate.json\n已生成花/跳网页交叉混淆报告：work/generated/scoring_mvp_run3/legacy_evidence_watch_test_20260603_v2/web_new_samples_watch_20260603_041629/flower_jump_confusion/flower_jump_web_confusion_gate.md\n已生成花/跳网页交叉混淆 CSV：work/generated/scoring_mvp_run3/legacy_evidence_watch_test_20260603_v2/web_new_samples_watch_20260603_041629/flower_jump_confusion/flower_jump_web_confusion_cases.csv\n综合状态：PASS\n- backend_ready: PASS (worker=ready, reload_error=-, error=-)\n- no_errors: PASS (errors=0, samples=2)\n- all_eligible_pass: PASS (eligible=2, pass=2, fail=0)\n- eligible_花: PASS (eligible=1, min=0, samples=1)\n- confusion_pass_花: PASS (pass=1, fail=0, other_score_max=7.474, margin_min=69.425)\n- eligible_跳: PASS (eligible=1, min=0, samples=1)\n- confusion_pass_跳: PASS (pass=1, fail=0, other_score_max=14.588, margin_min=73.989)\n', 'confusion_stderr': '', 'visual_stdout': '已生成汇总：work/generated/scoring_mvp_run3/legacy_evidence_watch_test_20260603_v2/web_new_samples_watch_20260603_041629/holistic_visuals/web_holistic_visual_recovery_summary.md\nweb_20260602_233343_899e6970 花 score=76.899 source=current_scoring_module\n  query_contact=work/generated/scoring_mvp_run3/legacy_evidence_watch_test_20260603_v2/web_new_samples_watch_20260603_041629/holistic_visuals/web_20260602_233343_899e6970/query/web_20260602_233343_899e6970_花_query_skeleton_contact_sheet.png\n  query_timeline=work/generated/scoring_mvp_run3/legacy_evidence_watch_test_20260603_v2/web_new_samples_watch_20260603_041629/holistic_visuals/web_20260602_233343_899e6970/query/web_20260602_233343_899e6970_花_query_presence_timeline.png\nweb_20260602_233348_53e3df5d 跳 score=88.577 source=current_scoring_module\n  query_contact=work/generated/scoring_mvp_run3/legacy_evidence_watch_test_20260603_v2/web_new_samples_watch_20260603_041629/holistic_visuals/web_20260602_233348_53e3df5d/query/web_20260602_233348_53e3df5d_跳_query_skeleton_contact_sheet.png\n  query_timeline=work/generated/scoring_mvp_run3/legacy_evidence_watch_test_20260603_v2/web_new_samples_watch_20260603_041629/holistic_visuals/web_20260602_233348_53e3df5d/query/web_20260602_233348_53e3df5d_跳_query_presence_timeline.png\n', 'visual_stderr': '', 'json_path': 'work/generated/scoring_mvp_run3/legacy_evidence_watch_test_20260603_v2/web_new_samples_watch_20260603_041629/new_web_samples_status.json', 'md_path': 'work/generated/scoring_mvp_run3/legacy_evidence_watch_test_20260603_v2/web_new_samples_watch_20260603_041629/new_web_samples_status.md'}, browser_capture_evidence={'request_ids': ['web_20260602_233343_899e6970', 'web_20260602_233348_53e3df5d'], 'passed': False, 'sample_evidence_passed': False, 'allow_legacy_browser_evidence': False, 'required_words': ['花', '跳'], 'observed_words': [], 'required_words_covered': False, 'missing_required_words': ['花', '跳'], 'rows': [{'request_id': 'web_20260602_233343_899e6970', 'path': 'work/generated/scoring_mvp_run3/strong_browser_evidence_fixture_20260603_v1/uniform_weights_web_root/web_20260602_233343_899e6970/scoring_result.json', 'exists': True, 'passed': False, 'reason': 'source_metadata_missing', 'target_word': '花', 'client_source': '', 'worker_mode': 'frame_slices', 'frame_count': 53, 'min_required_frames': 12, 'timeline_frame_count': 105, 'duration_sec': 5.3, 'capture_fps': 10.0, 'has_frame_weights': True, 'nonuniform_frame_weights': False, 'has_frame_indices': True, 'explicit_source_ok': False, 'weighted_source_ok': False, 'legacy_source_ok': False, 'diagnostic_compatible': False, 'completion_source_ok': False, 'evidence_level': 'none'}, {'request_id': 'web_20260602_233348_53e3df5d', 'path': 'work/generated/scoring_mvp_run3/strong_browser_evidence_fixture_20260603_v1/uniform_weights_web_root/web_20260602_233348_53e3df5d/scoring_result.json', 'exists': True, 'passed': False, 'reason': 'source_metadata_missing', 'target_word': '跳', 'client_source': '', 'worker_mode': 'frame_slices', 'frame_count': 19, 'min_required_frames': 6, 'timeline_frame_count': 37, 'duration_sec': 1.9, 'capture_fps': 10.0, 'has_frame_weights': True, 'nonuniform_frame_weights': False, 'has_frame_indices': True, 'explicit_source_ok': False, 'weighted_source_ok': False, 'legacy_source_ok': False, 'diagnostic_compatible': False, 'completion_source_ok': False, 'evidence_level': 'none'}]} |

## 最新质量门摘要

- 报告：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_composite_phase_guard_8gate_v1/flower_jump_quality_gate.md`
- 综合状态：`PASS`
- 子门：`web_regression`=PASS，`web_confusion_gate`=PASS，`discrimination_gate`=PASS，`pose_robustness_gate`=PASS，`frame_count_robustness_gate`=PASS，`missing_mask_robustness_gate`=PASS，`temporal_padding_robustness_gate`=PASS，`phase_order_robustness_gate`=PASS。
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
- 缺失/mask `花`：positive_min `100.000`，critical_missing_max `1.171`。
- 缺失/mask `跳`：positive_min `100.000`，critical_missing_max `3.037`。
- 静止 padding `花`：positive_min `97.862`，static_max `1.460`。
- 静止 padding `跳`：positive_min `79.124`，static_max `31.418`。
- 相位顺序 `花`：positive_min `79.410`，disordered_max `33.723`。
- 相位顺序 `跳`：positive_min `69.389`，disordered_max `45.000`。

## 当前 marker

- last_request_id：`web_20260602_233348_53e3df5d`
- marker 后新增样本：`0`
- marker 后新增花/跳样本：`0`

## 真实网页采集证据

- 综合状态：`MISSING`
- 样本证据状态：`MISSING`
- 要求覆盖词条：`花, 跳`
- 已覆盖词条：`-`
- 缺失词条：`花, 跳`

| request | 词条 | 状态 | 证据等级 | 原因 | source | 帧数 | 权重 | fps | duration |
|---|---|---|---|---|---|---:|---|---:|---:|
| web_20260602_233343_899e6970 | 花 | MISSING | none | source_metadata_missing | - | 53 | present | 10.00 | 5.30 |
| web_20260602_233348_53e3df5d | 跳 | MISSING | none | source_metadata_missing | - | 19 | present | 10.00 | 1.90 |

## 结论

- 当前运行态和算法质量门已经通过，但还没有新的真实网页摄像头 `花/跳` 样本诊断证据。
- 下一步仍需用户通过 5080 页面实际采集 `花/跳`，由 watcher 自动生成增量回归和骨架可视化后再复查。

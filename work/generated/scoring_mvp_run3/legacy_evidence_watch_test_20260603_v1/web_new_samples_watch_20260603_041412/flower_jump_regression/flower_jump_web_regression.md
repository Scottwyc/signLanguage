# 花/跳网页打分回归

- 生成时间：`2026-06-03T04:14:17`
- Web 样本根目录：`/data/WYC/signLanguage/work/generated/web_scoring_mvp`
- 当前标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 样本过滤：latest=`0`，since_request_id=``，request_ids=`web_20260602_233343_899e6970, web_20260602_233348_53e3df5d`
- 后端状态接口：`http://127.0.0.1:5080/api/status`
- 5080 状态：worker=`ready`，worker_pid=`811485`，reload_count=`11`，last_reload_error=`None`
- 口径：不重新运行 Holistic；query 使用已保存网页/API Holistic JSON，standard 使用当前标准库。

## 结论

- 回归状态：`PASS`
- replay 报告：`work/generated/scoring_mvp_run3/legacy_evidence_watch_test_20260603_v1/web_new_samples_watch_20260603_041412/flower_jump_regression/active_template_replay/web_replay_current.md`
- diagnostics 报告：`work/generated/scoring_mvp_run3/legacy_evidence_watch_test_20260603_v1/web_new_samples_watch_20260603_041412/flower_jump_regression/flower_jump_diagnostics/web_semantic_diagnostics.md`

| gate | 结果 | 说明 |
|---|---|---|
| backend_ready | PASS | url=http://127.0.0.1:5080/api/status, worker=ready, reload_error=-, error=- |
| replay_no_errors | PASS | samples=2, errors=0 |
| diagnostics_no_errors | PASS | samples=2, errors=0 |
| effective_rate_total | PASS | rate=100.0%, threshold=95.0% |
| effective_rate_花 | PASS | rate=100.0%, reliable=1, normal_or_borderline=1, low=0 |
| effective_rate_跳 | PASS | rate=100.0%, reliable=1, normal_or_borderline=1, low=0 |
| jump_effective_low_zero | PASS | effective_low=0 |
| flower_effective_low_bounded | PASS | effective_low=0, max=5, diagnoses={} |
| flower_effective_low_explained | PASS | allowed=['flower_opening_guard_failed'], observed={} |

## 全量网页回放

- 样本数 `2`，错误 `0`，正常 `2`，边界 `0`，低分 `0`。
- 旧均分 `82.738`，当前均分 `82.738`。

| 词条 | 样本数 | 正常 | 边界 | 低分 | 当前均分 | 手部覆盖均值 |
|---|---:|---:|---:|---:|---:|---:|
| 花 | 1 | 1 | 0 | 0 | 76.899 | 0.792 |
| 跳 | 1 | 1 | 0 | 0 | 88.577 | 0.895 |

## 花/跳语义诊断

- 花/跳样本 `2`，错误 `0`，有效采集 `2`，有效正常+边界 `2`，有效低分 `0`，有效正常+边界率 `100.0%`。

| 词条 | 原始样本 | 建议重采 | 有效采集 | 有效正常+边界 | 有效低分 | 有效率 | 有效均分 | 处置 | 诊断 |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 花 | 1 | 0 | 1 | 1 | 0 | 100.0% | 76.899 | {'normal': 1} | {'flower_core_accepted': 1} |
| 跳 | 1 | 0 | 1 | 1 | 0 | 100.0% | 88.577 | {'normal': 1} | {'jump_core_accepted': 1} |

## 有效低分样本

- 无有效低分样本。

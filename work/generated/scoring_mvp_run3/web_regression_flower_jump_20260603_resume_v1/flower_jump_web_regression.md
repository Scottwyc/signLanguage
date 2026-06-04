# 花/跳网页打分回归

- 生成时间：`2026-06-03T00:16:13`
- Web 样本根目录：`/data/WYC/signLanguage/work/generated/web_scoring_mvp`
- 当前标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 后端状态接口：`http://127.0.0.1:5080/api/status`
- 5080 状态：worker=`ready`，worker_pid=`811485`，reload_count=`7`，last_reload_error=`None`
- 口径：不重新运行 Holistic；query 使用已保存网页/API Holistic JSON，standard 使用当前标准库。

## 结论

- 回归状态：`PASS`
- replay 报告：`work/generated/scoring_mvp_run3/web_regression_flower_jump_20260603_resume_v1/active_template_replay/web_replay_current.md`
- diagnostics 报告：`work/generated/scoring_mvp_run3/web_regression_flower_jump_20260603_resume_v1/flower_jump_diagnostics/web_semantic_diagnostics.md`

| gate | 结果 | 说明 |
|---|---|---|
| backend_ready | PASS | url=http://127.0.0.1:5080/api/status, worker=ready, reload_error=-, error=- |
| replay_no_errors | PASS | samples=168, errors=0 |
| diagnostics_no_errors | PASS | samples=149, errors=0 |
| effective_rate_total | PASS | rate=96.8%, threshold=95.0% |
| effective_rate_花 | PASS | rate=95.4%, reliable=87, normal_or_borderline=83, low=4 |
| effective_rate_跳 | PASS | rate=100.0%, reliable=37, normal_or_borderline=37, low=0 |
| jump_effective_low_zero | PASS | effective_low=0 |
| flower_effective_low_bounded | PASS | effective_low=4, max=5, diagnoses={'flower_opening_guard_failed': 4} |
| flower_effective_low_explained | PASS | allowed=['flower_opening_guard_failed'], observed={'flower_opening_guard_failed': 4} |

## 全量网页回放

- 样本数 `168`，错误 `0`，正常 `97`，边界 `23`，低分 `48`。
- 旧均分 `35.442`，当前均分 `59.296`。

| 词条 | 样本数 | 正常 | 边界 | 低分 | 当前均分 | 手部覆盖均值 |
|---|---:|---:|---:|---:|---:|---:|
| 月亮 | 1 | 0 | 0 | 1 | 21.343 | 0.800 |
| 汽车 | 3 | 0 | 0 | 3 | 16.905 | 0.833 |
| 花 | 93 | 76 | 7 | 10 | 72.611 | 0.708 |
| 虎 | 2 | 0 | 0 | 2 | 17.755 | 0.780 |
| 跳 | 56 | 21 | 16 | 19 | 52.002 | 0.771 |
| 香蕉 | 13 | 0 | 0 | 13 | 14.558 | 0.601 |

## 花/跳语义诊断

- 花/跳样本 `149`，错误 `0`，有效采集 `124`，有效正常+边界 `120`，有效低分 `4`，有效正常+边界率 `96.8%`。

| 词条 | 原始样本 | 建议重采 | 有效采集 | 有效正常+边界 | 有效低分 | 有效率 | 有效均分 | 诊断 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 花 | 93 | 6 | 87 | 83 | 4 | 95.4% | 75.550 | {'flower_core_accepted': 83, 'flower_core_hand_presence_low': 5, 'flower_opening_guard_failed': 5} |
| 跳 | 56 | 19 | 37 | 37 | 0 | 100.0% | 76.677 | {'jump_core_accepted': 37, 'jump_two_hand_presence_low': 19} |

## 有效低分样本

| request | 词条 | 分数 | 采集质量 | 诊断 | floor 原因 | L/R 覆盖 | 花张开 |
|---|---|---:|---|---|---|---:|---:|
| web_20260602_233301_233b8215 | 花 | 2.913 | semantic_mismatch | flower_opening_guard_failed | opening_guard_too_weak | 0.000/1.000 | 0.052 |
| web_20260523_062341_afa8c368 | 花 | 14.572 | semantic_mismatch | flower_opening_guard_failed | query_not_short_core_capture | 1.000/0.450 | 0.000 |
| web_20260522_232244_45d260ed | 花 | 48.531 | semantic_mismatch | flower_opening_guard_failed | query_not_short_core_capture | 0.000/0.633 | 0.122 |
| web_20260523_031345_3b07a113 | 花 | 54.425 | semantic_mismatch | flower_opening_guard_failed | query_not_short_core_capture | 0.000/0.767 | 0.086 |

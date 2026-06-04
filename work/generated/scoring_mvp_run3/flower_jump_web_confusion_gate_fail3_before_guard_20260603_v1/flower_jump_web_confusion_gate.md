# 花/跳网页样本交叉混淆门

- 生成时间：`2026-06-03T02:40:35`
- Web 样本根目录：`/data/WYC/signLanguage/work/generated/web_scoring_mvp`
- 当前标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读保存的网页 Holistic JSON；同一 query 分别按 `花` 和 `跳` 当前模板复算；不调用 `/api/score`，不重启 Holistic。
- 适用范围：只把目标词自身 `score_valid/semantic_mismatch` 且目标分数 `>= min_target_score` 的样本纳入交叉混淆 gate；重采样本和低分语义失败样本不用于证明跨词区分度。
- 样本过滤：latest=`0`，since_request_id=``，request_ids=`web_20260523_044358_00db9d4d, web_20260523_022509_a44cb853, web_20260523_044135_12fbd5bc`

- 5080 状态：worker=`ready`，worker_pid=`811485`，reload_count=`9`，last_reload_error=`None`

## 结论

- 综合状态：`FAIL`
- 目标最低分：`60.0`
- 交叉最高分：`55.0`
- 目标-交叉最小 margin：`15.0`

| gate | 结果 | 说明 |
|---|---|---|
| backend_ready | PASS | worker=ready, reload_error=-, error=- |
| no_errors | PASS | errors=0, samples=3 |
| all_eligible_pass | FAIL | eligible=3, pass=0, fail=3 |
| eligible_花 | FAIL | eligible=0, min=1, samples=0 |
| confusion_pass_花 | FAIL | pass=0, fail=0, other_score_max=-, margin_min=- |
| eligible_跳 | PASS | eligible=3, min=1, samples=3 |
| confusion_pass_跳 | FAIL | pass=0, fail=3, other_score_max=75.244, margin_min=-6.727 |

## 分词条

| 词条 | 样本 | eligible | pass | fail | 目标均分 | 交叉最高 | margin 最低 | margin 均值 | 原因 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 花 | 0 | 0 | 0 | 0 | - | - | - | - | {} |
| 跳 | 3 | 3 | 0 | 3 | 72.881 | 75.244 | -6.727 | -1.274 | {'cross_score_high_and_margin_low': 3} |

## 失败样本

| request | 目标 | 目标分 | 交叉词 | 交叉分 | margin | 原因 | 目标诊断 | 交叉诊断 |
|---|---|---:|---|---:|---:|---|---|---|
| web_20260523_044358_00db9d4d | 跳 | 68.517 | 花 | 75.244 | -6.727 | cross_score_high_and_margin_low | score_valid | score_valid |
| web_20260523_022509_a44cb853 | 跳 | 74.915 | 花 | 73.663 | 1.252 | cross_score_high_and_margin_low | score_valid | score_valid |
| web_20260523_044135_12fbd5bc | 跳 | 75.212 | 花 | 73.560 | 1.652 | cross_score_high_and_margin_low | score_valid | score_valid |

## Eligible 明细

| request | 目标 | 目标分 | 交叉词 | 交叉分 | margin | pass | 目标状态 | 目标原因 | 交叉原因 |
|---|---|---:|---|---:|---:|---|---|---|---|
| web_20260523_044358_00db9d4d | 跳 | 68.517 | 花 | 75.244 | -6.727 | False | score_valid | score_valid | score_valid |
| web_20260523_022509_a44cb853 | 跳 | 74.915 | 花 | 73.663 | 1.252 | False | score_valid | score_valid | score_valid |
| web_20260523_044135_12fbd5bc | 跳 | 75.212 | 花 | 73.560 | 1.652 | False | score_valid | score_valid | score_valid |

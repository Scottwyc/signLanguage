# 花/跳网页样本交叉混淆门

- 生成时间：`2026-06-03T02:34:20`
- Web 样本根目录：`/data/WYC/signLanguage/work/generated/web_scoring_mvp`
- 当前标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读保存的网页 Holistic JSON；同一 query 分别按 `花` 和 `跳` 当前模板复算；不调用 `/api/score`，不重启 Holistic。
- 适用范围：只把目标词自身 `score_valid/semantic_mismatch` 且目标分数 `>= min_target_score` 的样本纳入交叉混淆 gate；重采样本和低分语义失败样本不用于证明跨词区分度。
- 样本过滤：latest=`3`，since_request_id=``，request_ids=`-`

- 5080 状态：worker=`ready`，worker_pid=`811485`，reload_count=`9`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`
- 目标最低分：`60.0`
- 交叉最高分：`55.0`
- 目标-交叉最小 margin：`15.0`

| gate | 结果 | 说明 |
|---|---|---|
| backend_ready | PASS | worker=ready, reload_error=-, error=- |
| no_errors | PASS | errors=0, samples=3 |
| all_eligible_pass | PASS | eligible=3, pass=3, fail=0 |
| eligible_花 | PASS | eligible=1, min=1, samples=1 |
| confusion_pass_花 | PASS | pass=1, fail=0, other_score_max=7.474, margin_min=69.425 |
| eligible_跳 | PASS | eligible=2, min=1, samples=2 |
| confusion_pass_跳 | PASS | pass=2, fail=0, other_score_max=14.588, margin_min=67.225 |

## 分词条

| 词条 | 样本 | eligible | pass | fail | 目标均分 | 交叉最高 | margin 最低 | margin 均值 | 原因 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 花 | 1 | 1 | 1 | 0 | 76.899 | 7.474 | 69.425 | 69.425 | {'passed': 1} |
| 跳 | 2 | 2 | 2 | 0 | 79.619 | 14.588 | 67.225 | 70.607 | {'passed': 2} |

## 失败样本

- 无 eligible 失败样本。

## Eligible 明细

| request | 目标 | 目标分 | 交叉词 | 交叉分 | margin | pass | 目标状态 | 目标原因 | 交叉原因 |
|---|---|---:|---|---:|---:|---|---|---|---|
| web_20260602_233343_899e6970 | 花 | 76.899 | 跳 | 7.474 | 69.425 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260602_233302_d92c0ce2 | 跳 | 70.661 | 花 | 3.435 | 67.225 | True | score_valid | score_valid | flower_opening_guard_failed |
| web_20260602_233348_53e3df5d | 跳 | 88.577 | 花 | 14.588 | 73.989 | True | score_valid | score_valid | flower_opening_guard_failed |

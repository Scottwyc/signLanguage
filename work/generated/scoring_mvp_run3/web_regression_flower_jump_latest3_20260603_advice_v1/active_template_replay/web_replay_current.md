# 网页测试样本当前算法回放

- 生成时间：`2026-06-03T02:14:51`
- Web 样本根目录：`/data/WYC/signLanguage/work/generated/web_scoring_mvp`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 样本过滤：latest=`3`，since_request_id=``，request_ids=`-`
- 标准库覆盖：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 口径：query 复用保存的网页/API Holistic JSON，standard 改用当前标准库，模拟当前后端在线评分。
- 分段：`normal_like >= 75`，`60 <= borderline < 75`，`low < 60`；这仍不是正式用户阈值。

## 总览

- 样本数：`3`
- 错误数：`0`
- 当前正常区间：`2`
- 当前边界区间：`1`
- 当前低分区间：`0`
- 旧均分：`78.712`
- 新均分：`78.712`

## 分词条

| 词条 | 样本数 | 正常 | 边界 | 低分 | 旧均分 | 新均分 | 手部覆盖均值 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 花 | 1 | 1 | 0 | 0 | 76.899 | 76.899 | 0.792 |
| 跳 | 2 | 1 | 1 | 0 | 79.619 | 79.619 | 0.947 |

## 最新样本

| request | 词条 | 帧数 | 旧分 | 新分 | 分段 | 手部覆盖 | 对齐 |
|---|---|---:|---:|---:|---|---:|---|
| web_20260602_233302_d92c0ce2 | 跳 | 9 | 70.661 | 70.661 | borderline | 1.000 | semantic_action_window |
| web_20260602_233343_899e6970 | 花 | 53 | 76.899 | 76.899 | normal_like | 0.792 | full_sequence_with_action_window_diagnostics |
| web_20260602_233348_53e3df5d | 跳 | 19 | 88.577 | 88.577 | normal_like | 0.895 | semantic_action_window |

## 低分样本排查

- 无低分样本。

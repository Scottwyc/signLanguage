# 网页样本语义诊断

- 生成时间：`2026-06-03T02:23:38`
- Web 样本根目录：`/data/WYC/signLanguage/work/generated/web_scoring_mvp`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 词条过滤：`花, 跳`
- 样本过滤：latest=`0`，since_request_id=``，request_ids=`web_20260602_233302_d92c0ce2, web_20260602_233343_899e6970, web_20260602_233348_53e3df5d`
- 标准库覆盖：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 口径：query 复用保存的网页/API Holistic JSON，standard 改用当前标准库，模拟当前后端在线评分；不重新运行 Holistic。
- 分段：`normal_like >= 75`，`60 <= borderline < 75`，`low < 60`；仍是工程诊断口径，不是正式用户阈值。

## 总览

- 样本数：`3`
- 错误数：`0`
- 均分：`78.712`
- 中位数：`76.899`
- 分段计数：`{'borderline': 1, 'normal_like': 2}`
- 诊断计数：`{'jump_core_accepted': 2, 'flower_core_accepted': 1}`
- 处置计数：`{'borderline_review': 1, 'normal': 2}`
- 采集质量计数：`{'score_valid': 3}`
- 有效采集口径：可评分样本 `3`，正常+边界 `3`，低分 `0`，正常+边界率 `100.0%`。

## 分词条

| 词条 | 样本数 | 正常 | 边界 | 低分 | 均分 | 中位数 | 最低 | 最高 | 核心覆盖均值 | 全段/窗口覆盖 | L/R 覆盖均值 | 采集质量 | 处置 | 主要诊断 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 花 | 1 | 1 | 0 | 0 | 76.899 | 76.899 | 76.899 | 76.899 | 1.000 | 0.792/1.000 | 0.000/0.792 | score_valid:1 | normal:1 | flower_core_accepted:1 |
| 跳 | 2 | 1 | 1 | 0 | 79.619 | 79.619 | 70.661 | 88.577 | 0.944 | 0.861/0.917 | 0.865/0.947 | score_valid:2 | borderline_review:1, normal:1 | jump_core_accepted:2 |

## 有效采集口径

- 这里排除 `needs_recapture`，只看核心关键点已经足够入画、可以解释为动作语义评分的样本。

| 词条 | 原始样本 | 建议重采 | 有效采集 | 正常+边界 | 低分 | 正常+边界率 | 有效均分 | 语义不匹配 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 花 | 1 | 0 | 1 | 1 | 0 | 100.0% | 76.899 | 0 |
| 跳 | 2 | 0 | 2 | 2 | 0 | 100.0% | 79.619 | 0 |

## 跳语义 floor 接收明细

- `action_window_net` 表示动作窗口起止净方向直接通过；`full_sequence_local_relation_segment` 表示完整序列中检测到局部双手弹跳段，并通过右手食指/中指手形守卫。
- 来源分布：`{'action_window_net': 2}`

| request | 分数 | 分段 | 来源 | 方向余弦 | 幅度比 | 水平/纵向 | 段覆盖 | 段帧 | 两指手形 | fallback 原因 |
|---|---:|---|---|---:|---:|---:|---:|---|---:|---|
| web_20260602_233302_d92c0ce2 | 70.661 | borderline | action_window_net | 0.681 | 1.291 | 0.222 | - | 14-22 | - | - |
| web_20260602_233348_53e3df5d | 88.577 | normal_like | action_window_net | 0.993 | 1.006 | 0.534 | - | 6-22 | - | - |

## 低分原因

- 无低分样本。
## 最新样本

| request | 词条 | 帧数 | 分数 | 分段 | 处置 | 采集质量 | 诊断 | L/R 覆盖 | 核心全段/窗口 | 对齐 | 建议 |
|---|---|---:|---:|---|---|---|---|---:|---:|---|---|
| web_20260602_233302_d92c0ce2 | 跳 | 9 | 70.661 | borderline | borderline_review | score_valid | jump_core_accepted | 0.889/1.000 | 0.833/1.000 | semantic_action_window | 保持双手关系清楚：左手稳定作为地面，右手食指/中指完成弹跳；当前左/右覆盖 0.89/1.00。 |
| web_20260602_233343_899e6970 | 花 | 53 | 76.899 | normal_like | normal | score_valid | flower_core_accepted | 0.000/0.792 | 0.792/1.000 | full_sequence_with_action_window_diagnostics | 开花核心段可评分；继续保持手部完整入画和清晰张开动态。 |
| web_20260602_233348_53e3df5d | 跳 | 19 | 88.577 | normal_like | normal | score_valid | jump_core_accepted | 0.842/0.895 | 0.889/0.833 | semantic_action_window | 双手弹跳核心语义可评分；继续保持两只手同时稳定入画。 |

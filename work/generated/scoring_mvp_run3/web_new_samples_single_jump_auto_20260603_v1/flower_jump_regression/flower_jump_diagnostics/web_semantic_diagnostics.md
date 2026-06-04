# 网页样本语义诊断

- 生成时间：`2026-06-03T05:37:26`
- Web 样本根目录：`/data/WYC/signLanguage/work/generated/web_scoring_mvp`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 词条过滤：`跳`
- 样本过滤：latest=`0`，since_request_id=``，request_ids=`web_20260602_233348_53e3df5d`
- 标准库覆盖：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 口径：query 复用保存的网页/API Holistic JSON，standard 改用当前标准库，模拟当前后端在线评分；不重新运行 Holistic。
- 分段：`normal_like >= 75`，`60 <= borderline < 75`，`low < 60`；仍是工程诊断口径，不是正式用户阈值。

## 总览

- 样本数：`1`
- 错误数：`0`
- 均分：`88.577`
- 中位数：`88.577`
- 分段计数：`{'normal_like': 1}`
- 诊断计数：`{'jump_core_accepted': 1}`
- 处置计数：`{'normal': 1}`
- 采集质量计数：`{'score_valid': 1}`
- 有效采集口径：可评分样本 `1`，正常+边界 `1`，低分 `0`，正常+边界率 `100.0%`。

## 分词条

| 词条 | 样本数 | 正常 | 边界 | 低分 | 均分 | 中位数 | 最低 | 最高 | 核心覆盖均值 | 全段/窗口覆盖 | L/R 覆盖均值 | 采集质量 | 处置 | 主要诊断 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 跳 | 1 | 1 | 0 | 0 | 88.577 | 88.577 | 88.577 | 88.577 | 0.889 | 0.889/0.833 | 0.842/0.895 | score_valid:1 | normal:1 | jump_core_accepted:1 |

## 有效采集口径

- 这里排除 `needs_recapture`，只看核心关键点已经足够入画、可以解释为动作语义评分的样本。

| 词条 | 原始样本 | 建议重采 | 有效采集 | 正常+边界 | 低分 | 正常+边界率 | 有效均分 | 语义不匹配 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 跳 | 1 | 0 | 1 | 1 | 0 | 100.0% | 88.577 | 0 |

## 跳语义 floor 接收明细

- `action_window_net` 表示动作窗口起止净方向直接通过；`full_sequence_local_relation_segment` 表示完整序列中检测到局部双手弹跳段，并通过右手食指/中指手形守卫。
- 来源分布：`{'action_window_net': 1}`

| request | 分数 | 分段 | 来源 | 方向余弦 | 幅度比 | 水平/纵向 | 段覆盖 | 段帧 | 两指手形 | fallback 原因 |
|---|---:|---|---|---:|---:|---:|---:|---|---:|---|
| web_20260602_233348_53e3df5d | 88.577 | normal_like | action_window_net | 0.993 | 1.006 | 0.534 | - | 6-22 | - | - |

## 低分原因

- 无低分样本。
## 最新样本

| request | 词条 | 帧数 | 分数 | 分段 | 处置 | 采集质量 | 诊断 | L/R 覆盖 | 核心全段/窗口 | 对齐 | 建议 |
|---|---|---:|---:|---|---|---|---|---:|---:|---|---|
| web_20260602_233348_53e3df5d | 跳 | 19 | 88.577 | normal_like | normal | score_valid | jump_core_accepted | 0.842/0.895 | 0.889/0.833 | semantic_action_window | 双手弹跳核心语义可评分；继续保持两只手同时稳定入画。 |

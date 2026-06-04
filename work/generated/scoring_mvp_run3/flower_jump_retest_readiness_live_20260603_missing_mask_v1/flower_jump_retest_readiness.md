# 花/跳网页复测前就绪报告

- 生成时间：`2026-06-03T06:19:47`
- 复测就绪：`PASS`
- 目标完成度：`NOT_READY`
- 下一步：`采集 花、跳`
- 要求覆盖词条：`花、跳`
- 已覆盖词条：`-`
- 缺失词条：`花、跳`
- 口径：只读检查；不调用 `/api/score`，不移动 marker，不重启 5080/Holistic。

## 运行态

| 项 | 状态 | 细节 |
|---|---|---|
| 5080/Holistic | `PASS` | worker=`ready`，pid=`811485`，reload_count=`11`，last_reload_error=`None` |
| watcher | `PASS` | event=`no_target_samples`，pid=`4021854`，target_count=`0` |
| 前端契约 | `PASS` | failed=`0`，warning=`0` |
| 综合质量门 | `PASS` | 报告 `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_missing_mask_v1/flower_jump_quality_gate.md` |

## 当前质量门关键指标

- 保存网页/API 回归：样本 `168`，错误 `0`；有效正常+边界率 `96.9%`。

| 词条 | 有效采集 | 正常+边界 | 有效低分 | 有效率 | 有效均分 |
|---|---:|---:|---:|---:|---:|
| 花 | 91 | 87 | 4 | 95.6% | 75.762 |
| 跳 | 37 | 37 | 0 | 100.0% | 76.677 |

- 花/跳交叉混淆：eligible `124`，pass `124`，fail `0`。

## 下一步采集建议

| 词条 | 推荐最少上传帧 | 推荐采集 | 动作重点 |
|---|---:|---|---|
| 花 | 12 | 2.5s / 5fps | 从撮合状态开始，手指张开/绽放过程完整入画。 |
| 跳 | 6 | 2.0s / 5fps | 左手地面和右手两指小人同时入画，右手在左手基础上完成弹跳。 |

## 关联报告

- 完成度审计：`work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_missing_mask_v1/goal_readiness/flower_jump_goal_readiness_audit.md`
- 前端契约：`work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_missing_mask_v1/frontend_contract/watch_status_frontend_contract.md`
- 综合质量门：`work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_missing_mask_v1/flower_jump_quality_gate.md`

## 结论

- 算法、运行态和前端链路已就绪；还需要真实网页摄像头样本：`采集 花、跳`。

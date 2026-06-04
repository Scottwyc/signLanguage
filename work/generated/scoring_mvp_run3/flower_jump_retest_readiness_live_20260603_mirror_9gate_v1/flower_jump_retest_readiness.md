# 花/跳网页复测前就绪报告

- 生成时间：`2026-06-03T09:08:31`
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
| 5080/Holistic | `PASS` | worker=`ready`，pid=`811485`，reload_count=`13`，last_reload_error=`None` |
| watcher | `PASS` | event=`no_target_samples`，pid=`4021854`，target_count=`0` |
| 前端契约 | `PASS` | failed=`0`，warning=`3` |
| 综合质量门 | `PASS` | 报告 `work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_mirror_9gate_v1/flower_jump_quality_gate.md` |
| 浏览器证据门 | `PASS` | 报告 `work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_mirror_9gate_v1/browser_evidence_gate/flower_jump_browser_evidence_gate.md` |
| 网页上传权重语义 | `PASS` | checks=`8`，failed=`-` |
| 网页上传权重仿真 | `PASS` | cases=`3`，报告 `work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_mirror_9gate_v1/browser_upload_weight_simulation_gate/browser_upload_weight_simulation_gate.md` |
| 网页上传强证据 | `PASS` | strong path=`frame_weights`，missing_required=`-`，client metadata pending `client_source、client_session_id、client_capture_id` |

## 当前质量门关键指标

- 保存网页/API 回归：样本 `168`，错误 `0`；有效正常+边界率 `96.9%`。

| 词条 | 有效采集 | 正常+边界 | 有效低分 | 有效率 | 有效均分 |
|---|---:|---:|---:|---:|---:|
| 花 | 91 | 87 | 4 | 95.6% | 75.762 |
| 跳 | 37 | 37 | 0 | 100.0% | 76.677 |

- 花/跳交叉混淆：eligible `124`，pass `124`，fail `0`。

| 词条 | 非关键缺失最低分 | 最弱非关键缺失 | 关键缺失最高分 | 最强关键缺失 |
|---|---:|---|---:|---|
| 花 | 100.000 | drop_face | 1.171 | drop_right_core_hand |
| 跳 | 100.000 | drop_face | 3.037 | drop_left_ground_hand |

| 词条 | 镜像正向最低分 | 最弱镜像变体 | 左右标签诊断最低分 | 最弱诊断变体 |
|---|---:|---|---:|---|
| 花 | 80.533 | mirror_x | 0.919 | swap_labels_diagnostic |
| 跳 | 80.843 | mirror_x | 31.053 | mirror_x_swap_labels_diagnostic |

| 词条 | padding 正向最低分 | 最弱正向 padding | 静态最高分 | 最强静态变体 |
|---|---:|---|---:|---|
| 花 | 97.862 | suffix_hold_25pct | 1.460 | static_hold_mid |
| 跳 | 79.124 | slow_repeat_each_2x | 31.418 | static_hold_mid |

| 词条 | 相位单调最低分 | 最弱单调变形 | 相位错序最高分 | 最强错序变体 |
|---|---:|---|---:|---|
| 花 | 79.410 | ordered_jitter | 33.723 | scramble_three_phases |
| 跳 | 69.389 | ordered_jitter | 45.000 | swap_halves |

## 下一步采集建议

| 词条 | 推荐最少上传帧 | 推荐采集 | 动作重点 |
|---|---:|---|---|
| 花 | 12 | 2.5s / 5fps | 从撮合状态开始，手指张开/绽放过程完整入画。 |
| 跳 | 6 | 2.0s / 5fps | 左手地面和右手两指小人同时入画，右手在左手基础上完成弹跳。 |

## 关联报告

- 完成度审计：`work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_mirror_9gate_v1/goal_readiness/flower_jump_goal_readiness_audit.md`
- 前端契约：`work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_mirror_9gate_v1/frontend_contract/watch_status_frontend_contract.md`
- 浏览器证据门：`work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_mirror_9gate_v1/browser_evidence_gate/flower_jump_browser_evidence_gate.md`
- 网页上传权重仿真：`work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_mirror_9gate_v1/browser_upload_weight_simulation_gate/browser_upload_weight_simulation_gate.md`
- 综合质量门：`work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_mirror_9gate_v1/flower_jump_quality_gate.md`

## 结论

- 算法、运行态和前端链路已就绪；还需要真实网页摄像头样本：`采集 花、跳`。

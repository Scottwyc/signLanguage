# 网页花/跳打分当前状态总览

- 生成时间：`2026-06-03 00:57:28 CST`
- 项目路径：`/data/WYC/signLanguage`
- 当前目标：继续验证并提升 `花/跳` 网页真实测试打分鲁棒性。

## 运行状态

- 5080 后端：`ready`
- Holistic worker PID：`811485`
- scoring reload_count：`7`
- scoring last_reload_error：`None`
- 当前标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 当前网页入口：`http://127.0.0.1:5080/`

## 自动诊断状态

- 正式 marker：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_sample_marker_current.json`
- marker last_request_id：`web_20260602_233348_53e3df5d`
- marker 后新增样本：`0`
- marker 后新增 `花/跳` 目标样本：`0`
- watcher tmux：`signlanguage-web-sample-watch`
- watcher PID：`2553122`
- watcher 状态：`no_target_samples`
- watcher 状态文件：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_sample_marker_watch_status.md`
- 前端静态状态镜像：`/data/WYC/signLanguage/work/web/static/watch_status.json`

网页右侧结果区已经显示“自动诊断”状态。该区块会显示 watcher 事件、marker 后新增目标样本数、最后检查时间、watcher PID，并在诊断完成后显示最近回归报告和骨架可视化报告路径。

## 当前回归基线

- 全量花/跳网页回归报告：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_regression_flower_jump_20260603_resume_v1/flower_jump_web_regression.md`
- 回归状态：`PASS`
- 全量 replay：`168` 条，错误 `0`
- 花/跳 diagnostics：`149` 条，错误 `0`
- 有效采集：`124` 条
- 有效正常+边界：`120` 条
- 有效正常+边界率：`96.8%`
- `跳` 有效低分：`0`
- `花` 有效低分：`4`，均为 `flower_opening_guard_failed`

## 自动诊断链路验证

- watcher e2e 模拟报告：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_sample_watch_e2e_test_20260603_v1/watch_status.md`
- 自动 marker 更新验证：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_sample_watch_update_marker_test_20260603_v1/watch_status.md`
- 模拟新增 `花/跳` 样本：`3` 条
- 自动回归返回码：`0`
- 自动骨架可视化返回码：`0`
- 模拟回归：`PASS`
- 模拟分数：`花=76.899`，`跳=70.661/88.577`
- 骨架 contact sheet：query/standard 均已生成。

## 真实测试后的预期闭环

1. 用户在 `http://127.0.0.1:5080/` 进行 `花` 或 `跳` 测试。
2. `/api/score` 保存新的 web sample 到 `/data/WYC/signLanguage/work/generated/web_scoring_mvp/web_*`。
3. watcher 在 20 秒内发现 marker 后新增 `花/跳` 样本。
4. watcher 自动运行增量花/跳回归与语义诊断。
5. watcher 自动生成 query/standard 骨架 contact sheet 和 presence timeline。
6. 回归和可视化都成功后，watcher 更新正式 marker，避免重复诊断。
7. 网页“自动诊断”区显示最近回归报告和骨架可视化报告路径。

## 当前结论

截至本报告时间，没有新的真实网页摄像头测试样本，因此还不能把“真实用户网页测试已经最终正常”作为完成结论。当前可以确认的是：

- 后端与 Holistic 常驻 worker 正常。
- 花/跳保存样本回归基线通过。
- 自动增量诊断、骨架可视化、状态镜像和网页状态展示均已验证。
- 下一步需要新的真实 `花/跳` 摄像头样本来完成目标的最终实测确认。

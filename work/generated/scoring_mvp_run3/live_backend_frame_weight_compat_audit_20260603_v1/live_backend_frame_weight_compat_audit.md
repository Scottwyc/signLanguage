# Live 旧后端 frame_weights 兼容性审计

- 时间：`2026-06-03 04:08 CST`
- 目的：确认当前 live 5080 后端尚未重启到新版 `backend.py` 时，真实网页 `花/跳` 打分不会因为 `scoring_result.json` 缺少前端上传的 `frame_weights/client_source` 而失去语义动态帧权重。
- 口径：只读 `/data/WYC/signLanguage/work/generated/web_scoring_mvp/web_*/scoring_result.json` 与当前 v5 五子门质量门，不调用 `/api/score`，不新增样本，不重启 Holistic。

## 运行态事实

- live 5080 仍是旧后端进程：`/api/watch-status` 返回 `404`。
- 当前 `backend.py` 文件已支持保存 `client_source/client_capture_id/frame_weights`，但 live 进程未加载该版本。
- 旧在线 smoke 样本示例：
  - `web_20260602_233343_899e6970`：`花`，53 帧，`client_source=None`，`frame_weights=None`，score `76.899`。
  - `web_20260602_233348_53e3df5d`：`跳`，19 帧，`client_source=None`，`frame_weights=None`，score `88.577`。

## 保存样本统计

| 指标 | 数值 |
|---|---:|
| 保存样本总数 | 168 |
| `花/跳` 样本数 | 149 |
| worker input_mode=`frame_slices` | 168 |
| 持久化 `client_source` 的样本 | 0 |
| 持久化 `frame_weights` 的样本 | 123 |
| `花/跳` 中持久化 `frame_weights` 的样本 | 111 |

## 无前端 frame_weights 时的动态权重证据

评分模块的 `with_dynamic_frame_weights()` 会从 Holistic 骨架序列的关键语义运动密度重新计算帧权重；前端 `frame_weights` 是附加提示，不是唯一来源。即使旧后端没有保存前端权重，查询序列仍会得到非恒定的 `score.frame_weight_summary.query_full`。

| request | 词条 | score | 持久化 frame_weights | query weight min | query weight max | 说明 |
|---|---|---:|---|---:|---:|---|
| `web_20260602_233343_899e6970` | 花 | 76.899 | no | 0.751 | 1.547 | 动态权重峰值集中在 3.0s-5.2s 的开花动作段。 |
| `web_20260602_233348_53e3df5d` | 跳 | 88.577 | no | 0.857 | 1.302 | 动态权重峰值覆盖右手相对左手弹跳阶段。 |
| `web_20260602_233302_d92c0ce2` | 跳 | 70.661 | no | 0.868 | 1.147 | 短 `跳` 仍有骨架动态权重，并保持边界以上。 |

## 与质量门关系

最新五子门质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_v5/flower_jump_quality_gate.md` 已在当前保存样本口径下通过：

- web regression：168 replay 样本错误 `0`，149 个 `花/跳` diagnostics 错误 `0`。
- `花/跳` 有效采集 128，正常+边界 124，有效率 `96.9%`。
- `跳` 有效低分 `0`。
- `花` 4 个有效低分均为 `flower_opening_guard_failed`，已在 `flower_remaining_low_visual_audit_20260603_v1` 复查为语义不足，不应通过放宽 guard 抬分。

## 结论

当前 live 旧后端不会保存 `client_source`，部分样本也没有保存 `frame_weights`，但这不等于评分失去动态帧权重。当前评分模块会从骨架运动密度重建查询侧语义权重，且 v5 质量门和在线 smoke 已覆盖该运行态。

因此，在不重启 5080/Holistic 的前提下，可以继续让用户通过当前 5080 页面采集真实 `花/跳`；完成度审计会以 `legacy_frame_slice_metadata` 接受旧后端真实样本证据。未来在合适维护窗口重启后端后，样本会升级为 strong 证据：显式 `client_source` 或非均匀前端 `frame_weights`。

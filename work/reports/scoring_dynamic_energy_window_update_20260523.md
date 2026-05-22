# 语义动态帧权重与动作窗口 DTW 更新报告

- 时间：2026-05-23 01:52:19 CST
- 项目：`/data/WYC/signLanguage`
- 阶段声明：当前仍是 demo/template 工程验证，不是已校准的真实用户评分阈值。

## 本轮目标

本轮围绕“重要特征的相对运动”继续优化三层链路：

1. 数据库模板：增加 demo dense cache 帧数，并为每个模板落盘语义 profile 和逐帧动态重要性权重。
2. 用户视频流：网页端从均匀抽帧改为候选高频采样，再按像素运动能量覆盖选择上传帧，并上传 `frame_weights`。
3. 打分算法：从整段死板 DTW 改为语义动作窗口 DTW。先用文本语义权重和视频动态能量找动作核心起点/终点，再在窗口内做加权 DTW。

## 数据库更新

新增 dense cache：

- 路径：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 构建方式：复用 5080 的唯一常驻 Holistic worker，通过 `/api/admin/build-template-cache` 构建。
- 抽样策略：`dense_step=2`，并验证抽样帧可读；不可读尾帧跳过并记录。
- 当前模板数：10 个，均已进入 step2 dense 根目录。

模板帧数：

| 词条 | dense 帧数 |
|---|---:|
| 唱歌 | 27 |
| 指示 | 30 |
| 月亮 | 47 |
| 朋友 | 28 |
| 汽车 | 44 |
| 花 | 53 |
| 虎 | 54 |
| 谗（羡慕） | 32 |
| 跳 | 19 |
| 香蕉 | 42 |

不可读尾帧处理：

- `花.mp4`：OpenCV 报告 107 帧，但 `106` 不可读，已跳过。
- `虎.mp4`：OpenCV 报告 110 帧，但 `108/109` 不可读，已跳过。

全量审计：

- 审计脚本：`/data/WYC/signLanguage/work/scripts/audit_template_semantic_weights.py`
- 审计输出：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/template_semantic_weight_audit_step2_v1/template_semantic_weight_audit.md`
- 结果：10/10 模板通过；无缺失 profile、无低帧数、无动态帧权重弱对比。
- 每个模板目录均已写回 `semantic_frame_weights.json`，包含文本语义 profile、逐帧权重、top weighted frames、presence/motion 审计。

## 算法策略

当前评分流程：

1. 读取模板和用户 Holistic JSON。
2. 加载目标词条文本语义 profile，确定手/手形/脸/pose 权重和关键节点权重。
3. 对标准序列和查询序列分别计算语义动态帧权重。
4. 从动态权重曲线中找“包含主峰的连续高能量连通段”，作为动作核心窗口诊断。
5. 按标准模板动作长度选择混合对齐策略：长动作使用完整序列语义加权 DTW；短促动作使用动作窗口加权 DTW。
6. 输出 per-group 距离、missing penalty、semantic delta、roughness、alignment policy、action window 边界和 score scale 诊断。

关键变化：

- `花` 的动态窗口只由主手开合决定；距离评分仍保留少量另一手约束，用于压低相似手形但语义不同的负例。
- `跳` 的语义重点为右手食/中指先弯后伸和左手地面；pose/face 不参与核心评分。
- 实测回归修正后，`花` 不再使用动作窗口作为主评分输入，而是使用完整序列语义加权 DTW；动作窗口只作为诊断字段返回。这样避免真实用户视频中手部开合能量峰位置不稳定时被过度裁剪。
- 对短促动作窗口，如果查询也存在明确能量峰，使用轻微短窗口 score scale 和重提取噪声底噪补偿，避免低 FPS/隔帧采样或 JPEG 帧切片重跑 Holistic 时过度扣分；静态假动作没有能量峰，不获得补偿。

## 前端采样更新

文件：`/data/WYC/signLanguage/work/web/static/app.js`

前端现在不是只按上传 FPS 均匀采样，而是：

- 使用 `candidateFps = min(18, uploadFps * 2)` 做候选采样。
- 对候选帧计算低分辨率灰度运动能量。
- 保留一部分均匀覆盖帧，再加入能量最高帧，避免只抓峰值而丢掉全程。
- 上传字段新增 `frame_weights`，后端写入 Holistic JSON，评分时与语义动态权重合并。

## 离线验证

最终采用 step2 dense 模板和混合对齐策略。

| 目标词 | 正例最低 | 负例最高 | margin | 门控 |
|---|---:|---:|---:|---|
| 花 | 84.146 | 48.734 | 35.412 | 通过 |
| 跳 | 82.466 | 45.759 | 36.707 | 通过 |

`花` 典型结果：

- self: 100.000
- trim_both_10pct: 91.211
- trim_start_20pct: 88.364
- subsample_even: 87.421
- amplitude_0.85: 84.942
- trim_end_20pct: 84.146
- fake_shuffle_frames: 47.549
- fake_reverse_time: 32.896

`跳` 典型结果：

- self: 100.000
- amplitude_1.15: 92.924
- amplitude_0.85: 92.131
- trim_start_20pct: 85.289
- trim_end_20pct: 85.303
- trim_both_10pct: 85.305
- subsample_even: 82.466
- fake_static_hold: 45.759
- fake_shuffle_frames: 17.014

## 历史网页样本回放

回放输出：

- `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_replay_action_window_step2_final_v1/web_replay_action_window_step2_final.csv`
- `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_replay_hybrid_policy_step2_v1/web_replay_hybrid_policy_step2.csv`

历史样本结论：

- `花`：无条件动作窗口会导致真实网页样本过度裁剪。混合策略回放 37 条历史 `花` 样本，均值从 30.633 提升到 58.563；最新 10 条从 30.232 提升到 46.174。较完整的 30-60 帧采集恢复到约 64-69。
- `跳`：11 条历史网页样本最高约 35.49，平均约 12.92。主要原因是这些样本来自旧均匀抽帧流程，右手/左手 Holistic 检出率多在 0.4-0.7，且动作窗口只有约 6 帧，不能代表新前端能量采样效果。
- 因此，旧 web 样本只能用于诊断“为什么低”，不能作为新采样流程的真实校准结果。

## 当前服务状态

- 端口：`127.0.0.1:5080`
- 运行策略：只保留一个 Web/Holistic backend。
- 模板根目录：step2 dense cache。
- `/api/score` 已返回 `alignment_policy`、`action_window`、`frame_weight_summary`、`score_scale`、`temporal_resample` 等诊断字段。
- 2026-05-23 02:05 CST 复核：5080 worker ready，Holistic init `260.111s`。用 `跳.mp4` 按帧切片重新经网页 API 跑 Holistic 的 smoke test 返回 request `web_20260523_020555_09843ad1`，score `77.209`，确认后端已加载 action-window 和短动作重提取噪声补偿。
- 网页进度条已调整为只表示采集阶段的时间进度；采集完成进入后端处理时清空/淡化，不再显示伪进度。
- 2026-05-23 02:35 CST 复核：后端新增 `ScoringModuleService`，`POST /api/admin/reload-scoring` 已验证可用；后续只改评分脚本时不再重启常驻 Holistic worker。

## 后续建议

1. 用新前端采样流程重新采 `跳`、`花` 等动作，每个词至少 5-10 条真实用户样本。
2. 对真实样本保存原始视频或至少保存上传帧缩略审计，便于判断低分来自动作错误还是 Holistic 检出失败。
3. 继续把文本语义 profile 从规则生成升级为可人工审核/编辑的数据库表。
4. 加入分段语义：例如 `跳` 可明确分为“食/中指弯曲准备”和“向上伸直弹跳”两个阶段，而不是只用一个主窗口。

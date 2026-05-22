# 手语打分 MVP 阶段总结

## 任务定义

本阶段目标是为 `/data/WYC/signLanguage` 建立可继续迭代的手语打分 MVP 闭环：

- 明确标准数据采集方案。
- 明确标准样本库和 dense `Holistic` 序列存储规范。
- 设计打分机制，包括关键帧选取、时序对齐、逐关节差异分析和相似度评分。
- 在没有真实用户视频流样本的前提下，用 demo 视频完成离线 sanity check 原型设计。

## 当前基础

项目已有基础：

- 已用 `MediaPipe Holistic` 跑通 demo 视频关键点识别。
- 已确认性能瓶颈主要是 `Holistic` 初始化，而不是逐帧推理。
- 已实现常驻 worker，并支持 `video_path` 和 `frame_slices` 两种请求模式。
- 已完成三层关键帧采样重构：
  - 候选生成层输出 raw `Holistic` JSON。
  - 选择策略层只读缓存。
  - 可视化层只读缓存，不重复跑识别。

## 数据现状与限制

当前可用数据主要是 demo 词汇视频：

- 目录：`/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/`
- 示例：`花.mp4`、`唱歌.mp4`、`跳.mp4` 等。

当前缺失：

- 真实用户视频流样本。
- 同一词汇多名用户、多次录制样本。
- 人工评分标签或专家标注。
- 明确动作起止标签。

因此，本阶段输出只能作为方法设计和流程验证，不能作为真实用户评分效果证明。

## 标准数据采集方案方向

后续采集规范应覆盖：

- 每个词汇的标准样本数量、用户测试样本数量和复录次数。
- 拍摄条件：正面视角、稳定机位、无遮挡上半身、统一光照、简洁背景、固定帧率和分辨率。
- 动作标注：动作准备段、动作开始、动作结束、收尾段。
- 保存内容：原视频、元信息 JSON、dense `Holistic` JSON、关键帧结果、质量控制报告和可视化抽检图。
- 质量控制：双手覆盖率、pose 稳定性、关键点缺失率、动作时长、动作完整性。

## 打分机制方向

建议第一版打分机制采用“dense 序列主线 + 关键帧诊断支线”：

- dense 主线：
  - 标准样本和待测样本都保存 dense 或 step-dense `Holistic` 时间序列。
  - 通过归一化、缺失处理、时序对齐和逐关节距离计算整体相似度。
- 关键帧支线：
  - 用 `uniform_select`、`two_stage_select`、`adaptive_select`、能量覆盖率筛选压缩序列。
  - 用于生成可解释的关键帧对齐图和诊断报告。

核心模块：

- 坐标归一化：以肩宽、躯干尺度或 pose bounding box 归一化。
- 缺失处理：区分真实动作缺失和模型检测失败，缺失过高时降低置信度。
- 时序对齐：优先从 DTW 开始，再比较分段 DTW 和关键帧锚点对齐。
- 逐关节误差：手指、手腕、肘肩、躯干、面部表情分别统计。
- 评分输出：整体分、手部动作分、姿态稳定分、节奏分、完成度分和诊断提示。

## 第一阶段验证口径

由于没有真实用户样本，第一阶段只做离线 sanity check：

- 同一视频自身对齐应得到高相似度。
- 同一视频的截断、降采样、轻微扰动版本应得到中高相似度，并在诊断中暴露扰动位置。
- 不同词汇之间应得到较低相似度或明显诊断差异。
- 不输出正式 pass/fail 阈值。

## 当前结论

本阶段已启动，并已完成第一版离线原型 sanity check。当前明确的是：

- 缺少真实用户样本不阻塞方案设计和原型搭建。
- 真实评分校准必须等用户样本和人工标签补齐。
- dense `Holistic` 序列匹配是最直接的 MVP 主路线。
- raw landmark + mask + DTW 可以跑通第一版离线评分链路；`花` 自身对齐为 `100.000`，`花` 的裁剪/降采样伪用户样本约 `93.987-98.046`，`花` vs 稀疏 `唱歌` raw landmark 负例约 `62.945`。
- 旧 bbox probe 结果区分度偏弱，`花` vs `唱歌` bbox 负例仍有 `85.837`，因此 bbox 只能用于兼容诊断，不能作为主打分特征。

## 初始原型产物

- 脚本：`/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py`
- 闭环方案：`/data/WYC/signLanguage/work/reports/scoring_mvp_integrated_plan_20260520.md`
- 初始实验报告：`/data/WYC/signLanguage/work/reports/scoring_mvp_initial_experiment_20260520.md`
- 标准采集协议草案：`/data/WYC/signLanguage/work/reports/standard_data_collection_protocol_20260520_draft.md`
- 数据/缓存审计草案：`/data/WYC/signLanguage/work/reports/scoring_data_cache_audit_20260520_draft.md`
- 打分机制草案：`/data/WYC/signLanguage/work/reports/scoring_mechanism_design_20260520_draft.md`
- 原型实施计划草案：`/data/WYC/signLanguage/work/reports/scoring_mvp_prototype_plan_20260520_draft.md`
- `花` raw landmark sanity 输出：`/data/WYC/signLanguage/work/generated/scoring_mvp_run1/flower_landmark_sanity/`
- `花` vs 稀疏 `唱歌` raw landmark 负例输出：`/data/WYC/signLanguage/work/generated/scoring_mvp_run1/flower_vs_singing_landmark_sparse_negative/`
- `花` vs `唱歌` bbox 旧 probe 负例输出：`/data/WYC/signLanguage/work/generated/scoring_mvp_run1/flower_vs_singing_bbox_negative/`

## 下一步

- 完成标准采集规范草案。
- 完成评分机制设计草案。
- 审计现有 demo 缓存，确定可直接复用的数据。
- 为更多词生成或复用 dense / step-dense raw landmark 缓存，补足不同词负例。
- 增加 confidence 分数、关键帧对齐诊断图和逐组误差曲线。

## 2026-05-20 18:25:00 CST 判别性优化更新

本阶段已经进一步完成 `花` 目标动作的判别性门控实验。

新增报告：

- `/data/WYC/signLanguage/work/reports/scoring_mvp_discrimination_optimization_20260520.md`

新增/更新脚本：

- `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py`
- `/data/WYC/signLanguage/work/scripts/benchmark_holistic_worker.py`

新增缓存：

- `/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache_v2/`

最终判别结果：

- 目标动作正例最低分：`75.494`
- 负例最高分：`41.495`
- 分离 margin：`33.999`
- 门控通过。

这说明当前 raw landmark + DTW + 序列级惩罚的评分模块，已经能在 `花` 目标动作上把合理目标变体和其他 demo / 随机假动作明显区分开。该结果仍是 demo-only sanity gate，不是用户评分阈值。

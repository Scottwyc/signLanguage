# 手语打分 MVP 标准采集与评分机制闭环方案

## 1. 本轮结论

2026-05-20 本轮已经完成一个可继续迭代的闭环起点：

- 派生自主探索 skill：`/home/wuyangcheng/.codex/skills/new/signlanguage-scoring-autonomous/SKILL.md`
- 建立标准数据采集协议草案。
- 建立现有 demo / cache 审计草案。
- 建立评分机制设计草案。
- 建立最小原型实施计划草案。
- 新增并实跑离线评分 MVP 脚本。
- 更新项目日志、全局记忆和阶段报告。

当前没有真实用户视频流样本和人工评分标签，因此本轮结论只证明“方法链路可以跑通”，不能证明真实用户评分有效。

## 2. 现有数据与可复用缓存

当前 demo 视频目录：

- `/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/`

现有 demo 可作为离线 sanity check seed，但不能作为正式标准库。

当前最有价值的 raw landmark 缓存：

- `/data/WYC/signLanguage/work/generated/parallel_sampling_strategies_three_layer_run1/candidate_cache/花/花_holistic_results.json`

该文件包含 `28` 个 step-4 records，并带有 `records[].result_data` 原始 landmark，可直接用于 landmark-mode scoring。

其他缓存类型：

- `/data/WYC/signLanguage/work/generated/holistic_probe_20260428_full/`：旧 probe 摘要，主要是 bbox / 覆盖率 / 运动能量，适合诊断，不适合作为主评分特征。
- `/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals_holistic/*/花/花_holistic_results.json`：关键帧 raw landmark 输出，适合关键帧诊断，不是 dense 标准模板。
- `/data/WYC/signLanguage/work/generated/holistic_worker_benchmark_run1/results/`：少量帧 raw landmark 输出，可做稀疏负例 smoke test。

## 3. 标准数据采集方案

标准样本库建议分阶段建设：

- MVP 最低线：每词 `2` 名标准示范者，每人 `3` 次合格重复，共 `6` 条。
- 推荐线：每词 `3` 名标准示范者，每人 `5` 次合格重复，共 `15` 条。
- 稳定线：每词 `5-8` 名标准示范者，每人 `5` 次合格重复，共 `25-40` 条。

用户/验证样本建议：

- 单次练习：每词每用户 `3` 次尝试。
- MVP 内测：每词每用户 `5` 次尝试。
- 阈值校准：每词至少 `20` 名用户 x `3` 次，推荐 `30` 名用户 x `3` 次，并配人工评分或通过/不通过标签。

采集要求：

- 正面固定机位，头、肩、肘、双手完整入画。
- 推荐 `1920x1080`、`30 fps`、横屏、H.264 MP4；最低 `1280x720`、`25 fps`。
- 背景简洁、光照稳定、避免遮挡和其他人体干扰。
- 原视频永久保留，不允许只保存裁剪版本。
- 每条样本标注 `prep_start_frame`、`action_start_frame`、`action_end_frame`、`recovery_end_frame`。

每条样本保存：

- raw video
- metadata JSON
- dense `Holistic` JSON
- quality JSON / Markdown
- keyframe selection JSON，作为可选诊断视图
- preview / overlay 可视化，作为人工抽检材料

详细草案：

- `/data/WYC/signLanguage/work/reports/standard_data_collection_protocol_20260520_draft.md`

## 4. 打分机制设计

主路线：

- 标准样本和待测样本都保存 dense 或 step-dense raw `Holistic` 时间序列。
- 读取缓存后做坐标归一化、缺失 mask、DTW 对齐、逐组误差统计。
- dense 序列匹配作为 MVP 主打分路线。

诊断路线：

- 使用 `uniform_select`、`two_stage_select`、`adaptive_select`、能量覆盖率筛选生成关键帧。
- 关键帧对齐用于可解释报告，不替代 dense 主评分。

评分组成建议：

- `overall_score`：总体相似度。
- `hand_score`：左右手动作与手型为主。
- `pose_score`：肩、肘、腕、躯干姿态。
- `tempo_score`：动作节奏和时序拉伸程度。
- `completion_score`：动作起止和完整性。
- `confidence_score`：检测覆盖率、缺失率和样本质量，不应和动作相似度混成一个黑盒分数。

当前必须避免：

- 直接宣称 pass/fail。
- 用旧 bbox probe 结果当主评分。
- 在没有真实用户样本时校准阈值。

详细草案：

- `/data/WYC/signLanguage/work/reports/scoring_mechanism_design_20260520_draft.md`

## 5. 初始原型脚本与实验

新增脚本：

- `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py`

脚本特点：

- 只读取已有 JSON，不重新运行 `Holistic`。
- 优先读取 `records[].result_data` raw landmark。
- 旧 JSON 缺 raw landmark 时可退回 bbox 兼容模式。
- 使用固定维度特征和 mask 处理缺失关键点。
- 使用 DTW 进行时序对齐。
- 输出 JSON、Markdown 和 alignment CSV。

实验结果：

- `花` raw landmark 自身对齐：`prototype_score = 100.000`。
- `花` raw landmark 降采样 / 裁剪伪用户样本：约 `93.987-98.046`。
- `花` vs 稀疏 `唱歌` raw landmark 负例：`62.945`。
- `花` vs `唱歌` bbox 旧 probe 负例：`85.837`，区分度偏弱。

结果说明：

- raw landmark + mask + DTW 链路可以作为 MVP 主路线继续推进。
- bbox 兼容模式只能用于旧缓存诊断，不适合主评分。
- 当前不同词 raw landmark 负例仍太稀疏，需要为更多词生成统一 step-dense 缓存。

初始实验报告：

- `/data/WYC/signLanguage/work/reports/scoring_mvp_initial_experiment_20260520.md`

结果目录：

- `/data/WYC/signLanguage/work/generated/scoring_mvp_run1/flower_landmark_sanity/`
- `/data/WYC/signLanguage/work/generated/scoring_mvp_run1/flower_vs_singing_landmark_sparse_negative/`
- `/data/WYC/signLanguage/work/generated/scoring_mvp_run1/flower_vs_singing_bbox_negative/`

## 6. 风险与限制

- 当前没有真实用户视频流样本。
- 当前没有人工评分标签。
- 当前没有动作起止标注。
- 当前只有 `花.mp4` 有较完整 step-dense raw landmark 缓存。
- `花.mp4` 左手覆盖率为 `0.0`，手部评分需要区分“词汇不需要左手”和“检测失败”。
- 旧 probe 名称中的 `full` 容易误读，它是多视频稀疏探针，不是逐帧 raw landmark dense 缓存。
- demo 词汇说明与视频文件名映射需要人工复核。

## 7. 下一阶段任务

优先级 1：

- 已完成其余 demo 视频的统一 step-4 raw landmark JSON，路径为 `/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache_v2/`。
- 已完成 `花` 目标动作判别性门控，路径为 `/data/WYC/signLanguage/work/generated/scoring_mvp_run2/flower_all_demo_discrimination_v2/`。
- 下一步建立 demo seed manifest，明确哪些样本是临时模板、哪些只是负例或调试样本。
- 下一步在评分脚本中加入 `confidence_score`，把检测覆盖率从动作相似度中拆出。

优先级 2：

- 增加 DTW 对齐图、逐帧误差曲线、分组误差条形图。
- 增加多模板匹配逻辑：一个词对应多个标准样本，取最近模板或模板簇距离。
- 增加关键帧对齐诊断报告。

优先级 3：

- 按采集协议补真实用户样本。
- 补人工评分或专家通过/不通过标签。
- 用真实数据校准分数阈值和等级解释。

## 8. 本轮产物清单

- `/home/wuyangcheng/.codex/skills/new/signlanguage-scoring-autonomous/SKILL.md`
- `/data/WYC/signLanguage/work/reports/scoring_mvp_followup_20260520.md`
- `/data/WYC/signLanguage/work/reports/scoring_mvp_phase_summary_20260520.md`
- `/data/WYC/signLanguage/work/reports/scoring_mvp_integrated_plan_20260520.md`
- `/data/WYC/signLanguage/work/reports/scoring_mvp_initial_experiment_20260520.md`
- `/data/WYC/signLanguage/work/reports/scoring_data_cache_audit_20260520_draft.md`
- `/data/WYC/signLanguage/work/reports/standard_data_collection_protocol_20260520_draft.md`
- `/data/WYC/signLanguage/work/reports/scoring_mechanism_design_20260520_draft.md`
- `/data/WYC/signLanguage/work/reports/scoring_mvp_prototype_plan_20260520_draft.md`
- `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py`
- `/data/WYC/signLanguage/work/generated/scoring_mvp_run1/`
- `/data/WYC/signLanguage/.codex/tmux-workers/COORDINATOR_SCHEDULE.md`

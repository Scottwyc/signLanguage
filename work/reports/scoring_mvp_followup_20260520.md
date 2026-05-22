# 手语打分 MVP 自主探索跟进记录

## 目标

本轮自主探索目标是沿着已有 `MediaPipe Holistic`、常驻 worker、三层采样架构继续推进两个方向：

- 建立标准数据采集方案，保证后续标准样本库和用户样本可复现、可质控、可比较。
- 设计手语动作打分机制，覆盖关键帧选取、时序对齐、逐关节差异分析与相似度评分。

## 当前约束

- 当前还没有真实用户视频流样本，也没有人工评分标签。
- 因此第一阶段只做“采集规范 + 数据结构 + 评分算法原型 + 离线 sanity check”。
- 第一阶段不宣称真实用户评分准确性、不校准合格阈值、不证明跨用户泛化。

## 工作原则

- 项目路径：`/data/WYC/signLanguage`
- Python 环境：`/home/wuyangcheng/myenv`
- 识别结果优先复用 raw `Holistic` JSON 缓存。
- 重型识别优先复用常驻 worker，避免重复支付 `Holistic` 初始化成本。
- dense `Holistic` 时间序列匹配作为主路线，关键帧路线作为压缩版或诊断路线。

## 阶段交付物

- 派生 skill：`/home/wuyangcheng/.codex/skills/new/signlanguage-scoring-autonomous/SKILL.md`
- 阶段总结：`/data/WYC/signLanguage/work/reports/scoring_mvp_phase_summary_20260520.md`
- worker 调度：`/data/WYC/signLanguage/.codex/tmux-workers/COORDINATOR_SCHEDULE.md`
- 项目工作日志：`/data/WYC/signLanguage/work/worklog_sign.md`
- 全局记忆：`/home/wuyangcheng/.codex/memories/projects/signLanguage/work_log.md`

### 2026-05-20 17:20:00 CST Update: autonomous scoring line started

已正式启动 `signLanguage` 打分 MVP 自主探索线，并派生专用 skill `signlanguage-scoring-autonomous`。

当前任务边界已经收敛为：

- 第一阶段先完成标准采集方案、标准样本库字段设计、打分机制方案和离线原型验证。
- 因为暂无真实用户视频流样本，原型实验使用现有 demo 视频、伪用户扰动样本和不同词汇负例做流程 sanity check。
- 后续等真实用户样本和人工评分标签补齐后，再进入阈值校准、评分等级和前端实时闭环验证。

下一步：

- 启动 tmux Codex worker 做并行支线探索。
- coordinator 负责整合 worker 结果，形成正式采集规范、打分机制设计和最小原型计划。

### 2026-05-20 17:35:00 CST Update: first scoring prototype sanity check completed

coordinator 已新增并运行离线评分 MVP 脚本：

- 脚本：`/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py`
- 初始实验报告：`/data/WYC/signLanguage/work/reports/scoring_mvp_initial_experiment_20260520.md`
- 结果根目录：`/data/WYC/signLanguage/work/generated/scoring_mvp_run1/`

关键结果：

- `花` raw landmark 自身对齐：`prototype_score = 100.000`。
- `花` raw landmark 的降采样/裁剪伪用户样本仍保持高分，约 `93.987-98.046`。
- `花` vs 稀疏 `唱歌` raw landmark 负例降到 `62.945`，方向符合 sanity 预期。
- 旧 probe 的 bbox 负例只有 `85.837`，区分度偏弱，因此 bbox 只能作为兼容诊断，不能作为主评分特征。

已修正一个缺失点处理问题：双方同时缺失同一组关键点时不再扣相似度分；单边缺失才计入 missing penalty。后续需要把覆盖率单独进入 confidence 分数。

### 2026-05-20 17:45:00 CST Update: worker drafts integrated into closed-loop plan

四个 tmux Codex worker 已完成：

- `data-cache-audit`：输出 `/data/WYC/signLanguage/work/reports/scoring_data_cache_audit_20260520_draft.md`
- `collection-spec`：输出 `/data/WYC/signLanguage/work/reports/standard_data_collection_protocol_20260520_draft.md`
- `scoring-design`：输出 `/data/WYC/signLanguage/work/reports/scoring_mechanism_design_20260520_draft.md`
- `prototype-plan`：输出 `/data/WYC/signLanguage/work/reports/scoring_mvp_prototype_plan_20260520_draft.md`

coordinator 已整合 worker 草案和实跑原型结果，形成闭环方案：

- `/data/WYC/signLanguage/work/reports/scoring_mvp_integrated_plan_20260520.md`

worker 运行中发现 `.codex/tmux-workers/progress` 和 `.codex/tmux-workers/reports` 在 worker sandbox 内不可写，但 owned project report 路径可写；本轮结果已通过项目报告和 manager capture 保留证据。

### 2026-05-20 18:25:00 CST Update: discrimination gate passed for flower target

根据用户反馈“`花` vs `唱歌` 区分度仍弱”，coordinator 已继续优化评分模块，并把目标更新为：

- 目标动作合理变体高分。
- 其他 demo 动作显著低分。
- 随机假动作低分。

脚本更新：

- `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py`

新增能力：

- `--run-discrimination-suite`
- `--negative-json label=path`
- 自动生成目标动作裁剪、降采样、幅度调整正例。
- 自动生成反向、乱序、静态保持、随机 landmark、随机游走假动作负例。
- 评分加入序列级惩罚、端点一致性和幅度缩放鲁棒性。

同时修复了 `/data/WYC/signLanguage/work/scripts/benchmark_holistic_worker.py` 在无 `ffprobe` 环境下总帧数退化为 `1` 的问题，改为帧切片模式下用 OpenCV 读取 `CAP_PROP_FRAME_COUNT/FPS`。

最终实验：

- 报告：`/data/WYC/signLanguage/work/reports/scoring_mvp_discrimination_optimization_20260520.md`
- 10 个 demo step-4 raw landmark 缓存：`/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache_v2/`
- `花` 全 demo 判别结果：`/data/WYC/signLanguage/work/generated/scoring_mvp_run2/flower_all_demo_discrimination_v2/`

门控结果：

- 正例最低分：`75.494`
- 负例最高分：`41.495`
- 分离 margin：`33.999`
- 门控：通过

其他 9 个 demo 对 `花` 的得分全部低于 `21`，随机假动作最高 `41.495`，目标动作裁剪/降采样/幅度调整变体均高于 `75`。

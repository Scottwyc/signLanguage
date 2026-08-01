# signLanguage

手语打分与手语识别技术资料仓库。

## 当前方向

- 目标：围绕手语动作打分、关键点提取、模板匹配和可视化评测构建可复用技术链路。
- 主线：先用 `MediaPipe Holistic` 做关键点级评测，再逐步补充时序建模、模板检索和误差分析。

## 目录结构

- `data/`: 示例词汇、视频与原始素材。
- `references/`: 论文和外部资料。
- `work/`: 当前技术文档、脚本、工作记录和生成物。
- `work/past/`: 早期版本和工具脚本，保留作为历史实现。
- `work/fonts/`: 本地字体资源。
- `work/tools/`: 辅助工具。
- `docs/`: 仓库级说明和索引。

## 手语宇宙数据库链路

- 先按音频节点和跨视角迁移生成候选切割点，再使用 `MediaPipe Holistic` 将边界微调到手臂贴身静止姿态。
- 原始层按“标准词汇 → 用户编号 → 视角 → 重复次数”组织普通 JSON Landmark，坐标兼容历史 `records[].result_data.*_landmarks` 格式。
- 派生层根据最新 21 词语义资料生成局部特征、缺失 mask、关键点权重和阶段语义，用于后续加权 DTW。
- 原始视频、Landmark 分片、批处理 Preview 和本地 Pilot 体积较大，仅保存在本地数据目录，不纳入 Git。
- 当前数据库仍属于待审核/待校准状态：切割点需人工复核，新词工程权重需用正负样本进一步校准。

## 关键文件

- `work/worklog_sign.md`: 项目工作日志。
- `docs/project_index.md`: 项目结构与脚本索引。
- `work/手语宇宙_原始与语义加权数据库技术报告_20260801.md`: 手语宇宙数据库结构、验证与限制。
- `work/generated/demo21_semantic_profiles_20260801/demo21_semantic_weights_v2.json`: 21 词语义加权 Profile。
- `work/手语识别与翻译技术调研报告_20260402.md`: 调研报告。
- `work/手语动作准确度评测方案_20260402.md`: 评测方案。
- `work/手语识别技术路线推荐_20260402.md`: 技术路线建议。
- `work/past/draw_architecture.py`: 架构图生成脚本。
- `work/past/md2pdf.py`: Markdown 转 PDF 脚本。
- `work/past/ascii_to_word.py`: ASCII 框图转 Word 流程脚本。
- `work/past/parse_ascii_diagram_final.py`: ASCII 框图解析脚本。

## 版本控制范围

- 记录脚本、Markdown、论文资料和项目文档。
- 忽略缓存类产物，如 `__pycache__` 和 Python 字节码。

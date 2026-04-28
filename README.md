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

## 关键文件

- `work/worklog_sign.md`: 项目工作日志。
- `docs/project_index.md`: 项目结构与脚本索引。
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

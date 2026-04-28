# 项目索引

## 仓库定位

`signLanguage` 目前是一个以“手语打分 / 手语识别”为中心的资料与脚本仓库，包含以下几类内容：

- 技术路线与调研文档
- 文档生成和格式转换脚本
- 手语素材与参考论文
- 工作日志和阶段性产物

## 主要脚本

- `work/past/draw_architecture.py`: 生成手语识别系统架构图，并把图片插入 Markdown / Word。
- `work/past/md2pdf.py`: 将 Markdown 报告转换为 PDF。
- `work/past/ascii_to_word.py`: 将 Markdown 内的 ASCII 框图解析为图片并写回 Word 流程。
- `work/past/parse_ascii_diagram_final.py`: ASCII 框图解析的最终版实现。
- `work/past/draw_diagram.py`: 框图绘制工具。
- `work/past/generate_pdf.py`: PDF 生成工具。
- `work/past/md2latex.py`: Markdown 到 LaTeX 的转换脚本。
- `work/past/ascii_diagram_v3.py`: ASCII 框图解析与绘制的早期版本。
- `work/scripts/signlanguage_common.py`: DOCX 解析、视频探测等通用工具。
- `work/scripts/profile_sign_data.py`: 手语资料结构化盘点脚本。
- `work/scripts/holistic_sampling_probe.py`: Holistic 关键点采样探针脚本。
- `work/scripts/plot_holistic_probe_summary.py`: Holistic 探针结果可视化和分析脚本。
- `work/scripts/recommend_keyframes_from_probe.py`: 基于探针结果推荐关键帧和采样策略的脚本。
- `work/scripts/visualize_holistic_features.py`: Holistic 特征检测结果可视化脚本，输出骨骼图、三联图和联系表。

## 主要文档

- `work/worklog_sign.md`: 当前项目日志，记录阶段目标与待办。
- `work/手语识别与翻译技术调研报告_20260402.md`: 调研结论与背景资料。
- `work/手语识别技术路线推荐_20260402.md`: 技术路线推荐。
- `work/手语识别技术路线推荐_v2_20260402.md`: 技术路线推荐迭代版。
- `work/手语动作准确度评测方案_20260402.md`: 评测方案。
- `work/手语动作准确度评测技术路线_20260423.md`: 技术路线深化版。
- `work/手语动作准确度评测技术路线_20260423_ppt.md`: 对应演示稿文本版。

## 资料目录

- `data/`: 示例词汇与视频素材。
- `references/`: 论文与综述 PDF。

## 维护原则

- 新脚本优先放在 `work/` 下，历史版本放在 `work/past/`。
- 技术文档优先使用 Markdown 作为可追踪源文件。
- 生成的缓存与字节码不纳入版本控制。

# 手语打分技术实践
## 项目整体
技术目标：进行手语动作打分。
模型能够进行行为识别，提取图片序列（视频）中的手势、肢体、面部等特征。我们能自行制作或从别处收集标准手语数据库，其中包含文标准手语的视频和对应的语义，同时用模型提取其中的行为特征，然后构建相应的键值对：手语语义-手语行为。同时，这一键值对应该要有足够的鲁棒性：一定程度的行为偏差/视频偏差下，仍能匹配正确的手语语义。
测评时，用模型识别摄像头实时采集的视频中的行为特征，将其识别到已经存在的手语语义或者是未知语义，并给出相似度。
目前粗略调查到可能合适的模型有MediaPipe Holistic等。可以先直接复现已有的模型，测试其是否符合需求；不够好再微调或设计。
中文手语也开源数据集可以使用。手语还有区分孤立词和连续语句，目前先处理孤立词的场景。

先尝试完成网页端手语测评的demo。

## 目前技术路线
目前以 MediaPipe Holistic 为核心，先做可解释的关键点级评测，再逐步引入更强的时序建模。
摄像头/视频
  -> MediaPipe Holistic 提取关键点
  -> 关键点清洗、归一化、时序对齐
  -> 标准动作库匹配
  -> 细粒度差异分析
  -> 评分与反馈输出
系统分两层：
•MVP 层：模板库 + 相似度检索 + 基础评分
•增强层：DTW 对齐 + 逐关节误差分析 + 错误定位

## 目前整体架构流程
1. 标准动作库：每个语义保留 3-5 个标准样本，覆盖不同录制人和角度。
2. MediaPipe Holistic 关键点提取：提取手部、身体、面部关键点，并统一到同一坐标系。
3. 关键点预处理与时序标准化：进行去噪、缺失补全、尺度归一化和固定帧数对齐。
4. 粗匹配与精细比对：先用 FAISS 召回候选模板，再结合 DTW 对齐和逐关节差异分析。
5. 评分与反馈输出：输出总分、分项分、等级、差异关节和纠错建议。
## 前端相关问题
网页获取摄像头权限，进行视频录制，关键帧采集等。
web端传输视频流可能存在问题：万一多个用户一起用，视频流并发可能会卡。所以，尽量轻量化：比如前端进行预处理。
## 数据采集
关键帧采样如何实施？
ps 通过蒙版提示统一用户使用的个体远近。
都采集上半身数据；还是更细化到局部？（待确定）
或许参考体育领域，进行模型的特化处理。

# workEpoch1 ~26/5/1
TODO: 对手语资料（/home/wuyangcheng/signLanguage/data）进行结构化描述，形成量化的特征指标（手部、肢体、面部，时序）
TODO：针对标准样本demo，看看Holistic模型的特征采样效果，是否能有效覆盖手语语义的关键信息。

## 2026-04-28
### git整理
- 已将 `/home/wuyangcheng/signLanguage` 初始化为 git 仓库，并采用 `main` 作为主分支。
- 已补充仓库级说明文件：`README.md`、`docs/project_index.md`。
- 当前版本控制范围以脚本、Markdown、论文资料和项目文档为主，缓存类文件由 `.gitignore` 排除。
- 后续如果继续扩展资料库，优先沿用现有目录结构，不直接打散历史产物。

### 结构化描述
- 新增 `work/scripts/signlanguage_common.py`，用于解析 `DOCX`、切分语义片段和读取视频元数据。
- 新增 `work/scripts/profile_sign_data.py`，用于把 `data/Demo词汇.docx` 与 demo 视频整理成结构化清单，并输出 JSON / Markdown 报告。
- 盘点脚本会同时生成一份“手部 / 肢体 / 面部 / 时序”量化指标模板，作为后续关键点特征的标准输出结构。

### 特征采样尝试
- 新增 `work/scripts/holistic_sampling_probe.py`，用于在安装 `mediapipe` 和 `opencv` 后执行 Holistic 关键点采样，并输出帧级和视频级统计。
- 当前环境里 `mediapipe`、`opencv`、`python-docx` 尚未安装，因此脚本支持 dry-run / metadata-only 降级，不会卡死在依赖缺失上。
- 后续在具备依赖的环境中直接运行探针脚本，即可得到手、身、脸与时间序列的覆盖率、运动能量和采样清单。


P： 使用myenv环境，安装mediapipe、opencv-python、python-docx等依赖后，运行 `holistic_sampling_probe.py`，观察输出的关键点采样统计和视频级特征覆盖情况。

### 运行结果
- 已在 `/home/wuyangcheng/myenv` 环境中安装 `mediapipe==0.10.20`、`opencv-python`、`python-docx`，并将 `protobuf` 降到 `4.25.8` 以兼容旧版 MediaPipe 接口。
- 已成功运行 `work/scripts/holistic_sampling_probe.py`，结果输出到：
  - `/home/wuyangcheng/signLanguage/work/generated/holistic_probe_20260428_single/`
  - `/home/wuyangcheng/signLanguage/work/generated/holistic_probe_20260428_full/`
- 单视频验证 `唱歌.mp4` 的视频级覆盖率：pose 1.0、left hand 1.0、right hand 0.8333、face 1.0，平均运动能量约 78.83。
- 全量 10 个 demo 视频的平均覆盖率：pose 1.0、left hand 0.6383、right hand 0.7067、face 1.0。
- 已将 `holistic_sampling_probe.py` 改成默认无头模式，自动设置 `QT_QPA_PLATFORM=offscreen` 和空 `DISPLAY`，避免在服务器环境里误连 X11。

### 结果分析
- 新增 `work/scripts/plot_holistic_probe_summary.py`，用于把 Holistic 探针结果直接可视化并生成分析报告。
- 已生成可视化产物：
  - `/home/wuyangcheng/signLanguage/work/generated/holistic_probe_20260428_full/analysis/holistic_coverage_by_video.png`
  - `/home/wuyangcheng/signLanguage/work/generated/holistic_probe_20260428_full/analysis/holistic_motion_by_video.png`
  - `/home/wuyangcheng/signLanguage/work/generated/holistic_probe_20260428_full/analysis/holistic_probe_analysis.md`
- 分析结论：
  - `pose` 和 `face` 覆盖率均稳定为 1.0，说明当前 demo 数据里主干和脸部特征都比较容易稳定捕获。
  - 双手覆盖有明显差异，平均值分别为 `left = 0.6383`、`right = 0.7067`，左手更容易掉帧。
- 覆盖最低的样本是 `花.mp4`，左手为 0.0、右手为 0.4167，适合后续重点检查遮挡与构图。
- 运动能量最高的是 `唱歌.mp4`，均值约 78.83，适合进一步做时序对齐或关键帧抽取。

P：可不可以给出关键帧的特征检测结果的可视化，骨骼图等。

### 关键帧建议
- 新增 `work/scripts/recommend_keyframes_from_probe.py`，把每个视频的高运动帧、双手出现/消失边界帧和采样建议直接算出来。
- 已生成关键帧建议产物：
  - `/home/wuyangcheng/signLanguage/work/generated/holistic_probe_20260428_full/keyframe_recommendation/keyframe_recommendations.json`
  - `/home/wuyangcheng/signLanguage/work/generated/holistic_probe_20260428_full/keyframe_recommendation/keyframe_recommendations.md`
- `花.mp4` 的推荐关键帧是 `4, 28, 32, 36`，同时给出左手和右手覆盖偏低的提示，说明这类样本更适合检查镜像、遮挡和画面边缘裁切问题。
- `唱歌.mp4` 的推荐关键帧集中在 `4, 8, 24, 32, 36`，说明这类高运动样本更值得在动作转折点做密采样。

Q: 现在的关键帧检测的部分，相对于视频总长度，覆盖了多少？比如花的视频中，人实际开始动作的时刻比较晚。所以，关键帧采样要尽可能按照视频总长度进行；目前是这样的吗？
A: 当前的没有。 
  - 采样规则是 每 4 帧取 1 帧
  - 但 max_frames=12，所以最多只会处理 12 个采样点
  - 这意味着最长只扫到第 44 帧左右，不会继续往后看整段视频

### 可视化结果
- 新增 `work/scripts/visualize_holistic_features.py`，可以把 pose / hand / face 关键点直接叠加在原图上，同时输出黑底骨骼图、三联图和多帧联系表。
- 已生成两组示例可视化结果：
  - `/home/wuyangcheng/signLanguage/work/generated/holistic_viz_20260428/唱歌/`
  - `/home/wuyangcheng/signLanguage/work/generated/holistic_viz_20260428/花/`
- 主要文件类型：
  - `*_annotated.png`：原图叠加关键点
  - `*_skeleton.png`：黑底骨骼图
  - `*_triptych.png`：原图 / 关键点图 / 骨骼图三联图
- `*_contact_sheet.png`：多帧拼图
- 直观上，`唱歌.mp4` 的双手和头部动作更连续，`花.mp4` 的左手几乎长期缺失，适合用骨骼图区分“动作难捕获”还是“拍摄构图不利于检测”。

### 4.28 汇总整理
- 已将当天工作整理为专门的 Markdown 报告：`/data/WYC/signLanguage/work/reports/20260428_todo_summary.md`
- 已使用 `pandoc` 导出带图 Word 文档：`/data/WYC/signLanguage/work/reports/20260428_todo_summary.docx`
- 报告围绕两个 TODO 展开：`sign_data_profile.py` 的结构化盘点结果，以及 `Holistic` 全量探针、关键帧建议和可视化结论。
- 另外补充生成了汇报简化版：`/data/WYC/signLanguage/work/reports/20260428_todo_summary_brief.md` 和 `/data/WYC/signLanguage/work/reports/20260428_todo_summary_brief.docx`，内容只保留关键工作、关键结果和结果图。
- 2026-04-28 23:56 后已按最新可视化结果重新导出上述两份报告，中文标题与状态栏已修正，文档内嵌图也已刷新。

### 迁移记录
- 已将仓库实体迁移到 `/data/WYC/signLanguage`。
- `/home/wuyangcheng/signLanguage` 现在是指向新位置的软链接，用于兼容旧脚本路径。
- 新增脚本的默认根路径已切换为 `/data/WYC/signLanguage`，后续新增代码优先使用新路径作为 canonical path。

### GPU加速（TODO）？cpu多进程加速
Q：GPU能加速holistic的推理吗？如果能的话，后续可以使用GPU里跑一遍探针，看看性能和结果上有什么差异。

P: 如果是cpu批量重跑，也可以进行多进程加速。可以吃满cpu核数。

## 2026-04-29

### 关键帧采样方式
目前推荐：
  1. 按整段视频均匀采样
  - 例如按 0%, 10%, 20%, ... 100% 的时间位置取帧
  - 这样不管动作早还是晚，都能扫到
  2. 两阶段采样
  - 第一阶段：整段视频粗采样，保证全局覆盖
  - 第二阶段：在运动峰值附近加密采样
  3. 自适应采样
  - 先找动作开始点或运动峰值
  - 再围绕这些位置密采样

P: 请你持续跟进，直到完成这三种采样方式的实践，你可以多进程加速，保存各自的可视化结果（包含视频样本采样的可视化，叠加hollistic检测的特征结果），并给出结果的总结分析报告，我们希望对于同一视频样本，整体采样的效果越好则采样方式越好。如果现在有不清楚的，可以立即提问，一旦明确后，请你自行工作，直至完成目标任务。

running





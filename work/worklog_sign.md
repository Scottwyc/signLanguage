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

DONE

### 三种采样策略实验完成
- 已完成 `uniform`、`two_stage`、`adaptive` 三种采样方式在 `花.mp4` 上的实践。
- 已保存各自的 Holistic 叠加可视化结果，包含联系表、时间轴和逐帧三联图。
- 已导出总结分析报告：
  - `/data/WYC/signLanguage/work/reports/20260429_sampling_compare_summary.md`
  - `/data/WYC/signLanguage/work/reports/20260429_sampling_compare_summary.docx`
- 当前结论：
  - `adaptive` 最贴近动作开始较晚的视频样本，采样有效性最好，但耗时最高。
  - `two_stage` 在效果和耗时之间更均衡。
  - `uniform` 作为稳定基线仍然有价值。
- 后续处理此类批量任务时，优先采用 CPU 多进程并行，再评估是否值得引入更复杂的 GPU 路线。

### 耗时拆分口径
- 后续所有关键帧采样相关报告固定拆成三段：
  - 采样耗时
  - Holistic 识别耗时
  - 可视化耗时
- 不再把三段混成一个“总耗时”写法，避免把不同阶段的成本混在一起。

### 三层采样重构
- 已开始把关键帧采样重构成三层：
  - 候选生成层直接产出 raw Holistic 结果 JSON 作为缓存
  - 选择策略层只读取这份 JSON 做 `uniform_select / two_stage_select / adaptive_select / 能量覆盖率筛选`
  - 可视化层继续独立基于结果文件渲染，不再重复跑 Holistic
- 相关脚本已经同步改造，并用 `花.mp4` 的原始 Holistic 结果 JSON 做过 smoke test，确认四个选择器都能直接从缓存里出结果。
- 三层架构正式总结已导出为 `/data/WYC/signLanguage/work/reports/20260429_three_layer_sampling_summary.md` 和对应 Word。
- 进一步思路：如果数据压力不大，可以直接把 dense Holistic 结果入库，跳过关键帧选择层，未来实时检测时直接拿“标准样本 Holistic 结果 vs 当前视频密采样 Holistic 结果”做相似度计算与匹配。

### 时间统计和流程优化
P: 之前统计三种采样方式的耗时，应该区分采样本身的耗时和之后进行holistic识别的耗时还有最后可视化的耗时，我们首先关心的是采样耗时，当然后者也要统计。把reports中对应部分的耗时写清楚，不要混在一起。按理说，同样的采样帧数，holistic处理耗时应该近似。请更新。
采样耗时，holistic识别耗时，可视化耗时要分别拆开统计，报告中写清楚。最好你重新进行一下实验，确保数据准确，然后更新报告。

DONE

Q: 有一个问题，三种采样方式中，后面两种选择采样时是已经使用了holistic识别吗？如果是的话，它们采样完成不久也同步得到了holistic识别结果？

A:   - uniform 不会用 Holistic 来决定采样帧，只是在最后对已经选好的帧做一次 Holistic
    评估。看 signLanguage/work/scripts/sample_keyframes_uniform.py:38 和
    signLanguage/work/scripts/sample_keyframes_uniform.py:43。
  - two_stage 会先对粗采样帧跑一次 Holistic，用这些结果来给区间打分，再决定最后补哪
    些帧；最后还会再跑一次 Holistic，把最终采样帧的结果补齐。看 signLanguage/work/
    scripts/sample_keyframes_two_stage.py:46 和 signLanguage/work/scripts/
    sample_keyframes_two_stage.py:86。
  - adaptive 也会先跑一次 pilot Holistic，但后面的递归选帧主要用的是代理行，不会每
    加一个点都重新跑 Holistic；最后同样会对最终采样帧再做一次 Holistic 评估。看
    signLanguage/work/scripts/sample_keyframes_adaptive.py:63 和 signLanguage/work/
    scripts/sample_keyframes_adaptive.py:95。

Q: 那么后两种方式，它们完成采样同时就能得到holistic识别结果的话，那么就不用再对采样帧单独再进行holistic了吧？对于它们来说，应该直接在采样完成的同时保存holistic结果。另外，三种方式，应该都在得到holistic结果后，也可以由识别结果直接得到holistic可视化结果，而不是可视化时再跑一次holitstic识别吧。从结果上看，似乎12帧的holitstic识别大致就是260s左右。
你如果觉得我分析的对，就可以调整三种后两种方式的代码，让他们的流程更紧凑。同时分析报告也说清楚，后两者是采样和识别一起完成的。

P: 耗时统计方式要调整，由于two_stage和adaptive的采样和holistic识别其实是一起完成的，不能拆开统计了，所以三者都把采样和holistic耗时放在一起统计，只是在报告中要说明它们三者耗时过程的区别。可视化部分其实是在得到holistic结果后独立进行的，所以也不重要了，不再计时了，报告中也不需要提了。请更新相应脚本，并进行实验，得到结果后，更新报告。

P: 我发现，从urniform来看，仅仅对各帧视频进行holistic识别和评估其实很快？选定的12帧，其实holistic识别总共只用了0.5s？如果是这样的花，那么我们直接用更密的均匀采样，计算结果，然后直接从中选取目标数量的关键帧和对应的holistic结果不就行了。这样就可以又快又好了。毕竟我们不需要把采样和识别分割开来的，我们的目的仅仅是得到高质量、覆盖面广的关键帧上的holistic结果。你可以把这个新思路“密采样筛选”实现一下，看看效果和效率怎么样。这个思路的好处是，完全不需要设计复杂的采样策略了，直接暴力均匀密采样，然后从结果里选就好了。你可以先试试在花的视频上，看看如果每4帧采样一次，得到的holistic结果和最终选出来的12帧的结果是什么样子的；同时时间上是不是也比之前的两个好很多。

P: 关键是怎么从密采样的结果里选出目标数量的关键帧来？你可以设计一个简单的规则，比如先按照运动能量排序，选前N/2；再按照双手覆盖率排序，选前N/2；如果有重复的，就继续往后选。总之，设计一个简单的规则，从密采样的结果里选出12帧作为最终的关键帧。注意，选出了关键帧任务就结束了，因为holistic的结果已经都有了；后续再根据holistic结果独立进行可视化即可。所以计时部分就是密采样holistic总耗时。你可以先试试这个思路，看看效果和效率怎么样。

P：既然现在主要就是简单的密采样，那么各帧之间其实可以并行处理，多进程加速；你可以优化脚本，试验一下。

### 性能瓶颈关键：holistic初始化
Q: 所以目前holistic识别过程的性能瓶颈是什么？初始化比较慢吗？
A: 是，当前瓶颈主要在 Holistic 的初始化和首次图加载，不在单帧 process()。

  我做了两类测试：

  - probe_video_metadata 很快，几乎不耗时。
  - 只要进入 with holistic_cls.Holistic(...)，新进程里就会卡很久；我做的单帧上下文
    进入测试在 60 秒窗口内都没有返回。

  这说明：

  - 真正慢的是初始化 / 建图 / 模型加载。
  - 单视频、少量密采样帧的场景，不适合默认把每帧拆成很多进程。
  - 我已经把能量覆盖率筛选路线改成默认单进程，--workers 只作为显式实验项保留。


Q: 初始化完成后，为什么不能对各帧分别处理，多进程并行化呢
A: 1. 进程之间不共享内存
  - Holistic 不是可共享的 Python 对象。
  - 多进程里，每个 worker 都必须自己 import mediapipe，自己创建 Holistic 实例。

    2. 你现在的瓶颈在初始化
  - 我刚才测到，probe_video_metadata 很快。
  - 但一旦进入 with holistic_cls.Holistic(...)，新进程里会卡很久，60 秒窗口都没返
    回。
  - 所以如果你把任务拆得太细，比如“每帧一个进程”或“每几帧一个新进程”，初始化成本会
    被重复放大，反而更慢。

  3. Holistic 本身带有一定时序/跟踪语义
  - 你现在用的是 static_image_mode=False，它会尝试利用前后帧关系做跟踪和稳定。
  - 如果把帧拆到多个进程里，每个进程只处理很少几帧，这种跟踪状态会被不断重置。
  - 对“密采样后独立选帧”这种任务，反而更适合 static_image_mode=True。

更合理的并行方式是：
  - 启动 2 到 4 个常驻 worker
  - 每个 worker 自己初始化一次 Holistic
  - 每个 worker 处理一段连续或半连续的帧块
  - 主进程最后合并结果、排序、落盘

P: 试试你的分块并行方案，每个进程都启动holistic，处理一段连续的帧块；最后主进程合并结果，选出目标数量的关键帧。注意进行全过程的时间统计，内部包括完成初始化的用时统计和后续识别的用时统计，看看多进程的加速效果。


P: 按理说，并行进程之间完全是独立初始化，独立处理一部分视频分块，它们并不会带来很大的资源争抢吧，我们的cpu资源完全足够的。关键的时间瓶颈可能就是holistic自身的初始化？一定要进行严格的分段计时，看看holistic初始化到底要多久。

DONE: - Holistic 的主要瓶颈是初始化和图构建，不是逐帧识别。
  - 严格分段基准里，花.mp4 的结果是：
      - 元数据读取：0.027s
      - 帧读取：0.096s
      - Holistic 初始化：260.108s
      - Holistic 识别总耗时：0.267s
      - 全流程总耗时：260.885s

所以，holistic后续处理其实都很快，关键就是初始化成本。

Q: 能不能用序列化等方案，存储holistic的内存加载形式，方便之后快速完成该模型的初始化加载

A: 不能直接序列化成一个“已加载好的 Holistic 内存对象”再下次反序列化复用。官方文档里
  没有给这种能力，反而是把图的生命周期定义成“初始化 -> Open() -> Process() ->
  Close() -> 销毁”，也就是说每次 graph run 都会重新构建一套运行时状态。

  依据有两点：

  - MediaPipe 计算图的生命周期里，Open() 负责准备每次运行的状态，Process() 负责逐次
    处理，Close() 后对象就销毁了。
    参考：Calculators - Google AI Edge
    (https://ai.google.dev/edge/mediapipe/framework/framework_concepts/calculators)
  - Holistic 的官方 Python/solutions 文档只提供创建和使用方式，没有提供保存/恢复已
    初始化图状态的接口。
    参考：MediaPipe in Python (https://developers.google.com/mediapipe)
    参考：MediaPipe Holistic

  (https://github.com/google-ai-edge/mediapipe/blob/master/docs/solutions/holistic.md)

  所以结论是：

  - Holistic 的“初始化状态”不能像普通 Python 对象那样序列化后直接恢复。
  - 能缓存的是：
      - 模型文件本身
      - 你自己的结果文件
      - 常驻进程里的已创建实例
  - 不能缓存的是：
      - 已经初始化完成的 MediaPipe graph runtime state

  更可行的提速方式是这几种：

  1. 长驻 worker

  - 启动少量常驻进程
  - 每个进程只初始化一次 Holistic
  - 后续连续处理很多块帧
  - 这是最贴近你这个任务的方案

  2. 预热复用

  - 先让 worker 在启动时完成一次初始化
  - 后面所有视频共用这个 worker
  - 适合批量任务

  3. 降低初始化成本

  - 看能否切更轻的配置，比如 model_complexity=0
  - 或者换更轻的任务接口，如果业务允许

  4. 直接缓存结果，不缓存模型状态

  - 你现在这条线里，真正有价值的是保存 Holistic 的结果文件
  - 后续选帧、可视化都从结果文件读，而不是重复跑模型

### 解决方案：后台常驻worker
Q: 能不能在后台让一个worker常驻，保持holistic的初始化状态，然后前端每次需要识别时，就把视频帧发给这个worker，让它直接处理并返回结果？这样就完全不需要重复初始化了。

A: 可以，这就是最合理的方向。

  结论很直接：

  - 可以做成一个后台常驻 worker。
  - worker 启动时只初始化一次 Holistic。
  - 之后前端每次把帧或帧块发给它，它直接处理并返回结果。
  - 这样在 worker 生命周期内，确实不会重复初始化。

我建议的结构是：

  - 启动一个 holistic_worker 常驻进程
  - worker 内部：
      - import mediapipe
      - 创建 Holistic 实例
      - 监听队列 / socket / RPC 请求
  - 前端：
      - 提交任务
      - 等待返回 result.json
      - 后续可视化单独读结果文件

  这样做的收益是：

  - 避免每次任务都支付 260s 级别的初始化成本
  - 初始化成本被摊薄到很多次请求上
  - 这是你现在这条线最该做的优化

  实际落地时我建议再加两个机制：

  - 长驻复用
      - worker 只要不退出，就一直保留初始化状态
  - 预热
      - worker 启动后先跑一个小样本，确保模型和图完全进入稳定状态

如果你愿意，我下一步可以直接把它落成一个后台 worker 版本，给你两套接口：

  1. 命令行式 worker

  - 适合本地调试
  - 一个进程常驻接任务

  2. 简单 RPC / socket 版

  - 适合前端反复提交识别请求
  - worker 常驻，前端发请求拿结果

  这样就能真正实现你说的：
  “前端每次需要识别时，把视频帧发给这个 worker，它直接处理并返回结果。”

P: 可以，请完成相应脚本，补充相应文档说明，并进行实验，看看多个视频依次请求后台能不能稳定常驻和处理。

DONE：成功实现常驻后台的worker

P：能不能前端直接发送视频的帧切片给后台，也就是后台不再加载视频，而是直接处理视频帧；比如从原视频中每4帧切一个片段，直接发给后台处理；这样就完全不需要在后台加载视频了，直接处理帧片段就好了。

DONE：成功。


多后台常驻，并行加速，空闲灵活调度；灵活模式
P：既然确定后台worker稳定可用，以后你就让一个后台端口（比如tmux）一直存活，运行
  着worker，后面我们再实验有需要的时候就发给它；这种后台worker还可以并行保留多个（比如10个），反正cpu充足，这样以后实验可以让多个worker并行处理，加快实验。
  或许还要设置一个调度后台，前端每次发请求时，调度后台把请求分发给空闲的worker，这样就能实现更高效的并行处理了。 
  另外，应该让后台能够根据前台传入的参数，直接切换视频源模式还是视频帧模式，而不是重新又启动新workder。

DONE



P：现在基于后台多窗口启动多个worker，比如4个，再并行实践一下之前的4个关键帧采样方案，worker采用视频源模式，每个worker对应一种方案，并行进行。这次我们也分别统计各进程中worker启动时间和后续实际完成关键帧采样的时间，也统计一下全部完成的总用时。把这次实验结果也进行分析总结。

DONE

### 关键帧采样重构
Q: 采样策略two_stage和adaptive它们的completion_sec为什么会那么大？即使dense直接遍历全部的帧然后进行分析计算，应该时间也会远远小吧？holistic做识别实际是很快就完成的；为什么它们要那么久？

A:的，two_stage 和 adaptive 的 completion_sec 大，根因不是“逐帧识别慢”，而是它们
  当前实现里做了两次 Holistic 评估流程， 而 extract_holistic_rows() 每调用一次，都会在函数内部重新创建一个新的 Holistic，这个初始化恰恰是最耗时的。



P：既然所有帧全部处理一遍时间成本也不大，实际上完全可以直接用dense的方式遍历所有帧（或者带上step如果视频过长），然后只是不同的策略去从这些结果里选关键帧即可。不同的策略只是关键帧选取不同。基于此，two_stage 和 adaptive或许可以重新设计，或者直接合并不同的策略。
这样的话，原来的dense也要重命名其对应的策略，比如“能量覆盖率筛选”。

A：我同意，这样的架构更合理。
  你现在这个判断本质上是在把问题拆成两层：

  - 先做一次统一的候选帧计算
  - 再在候选结果上做不同的关键帧选择

  这样一来，two_stage 和 adaptive 就不应该再被理解成“各自重新跑一遍 Holistic 的采样
  策略”，而应该改成“基于同一份 Holistic 候选缓存的选择策略”。

  更准确地说，推荐 采样重构成三层： 

  1. 候选生成层
  - 这一步只做一次 Holistic
  - 结果落成缓存文件
  2. 选择策略层
  3. 可视化层  
  - 只读结果文件，不再跑 Holistic

  - 报告口径会更干净
  - 代码也更容易维护

  我建议你把 two_stage 和 adaptive 重新定义成：
  - two_stage_select
  - adaptive_select

  它们都只对同一份 dense cache 做选择，不再各自重新评估视频。

  如果视频很长，再加一层控制：

  - 短视频：全量 dense 候选
  - 长视频：按步长 dense 候选，比如 step=4/8/16
  - 策略只在候选上工作

  这会比现在“每种策略自己各跑一遍 Holistic”更符合你的目标：

  - 我们要的是高质量关键帧上的 Holistic 结果
  - 不是为了让策略本身再次触发昂贵的模型初始化



P: 现在采样重构成三层： 
  1. 候选生成层（设置step的密采样； 短视频：全量 dense 候选；长视频：按步长 dense 候选，比如 step=4/8/16）
  - 这一步只做一次 Holistic
  - 结果落成缓存文件（json）
  2. 选择策略层
    比如uniform_select、two_stage_select、adaptive_select、能量覆盖率筛选 等
  3. 可视化层  
  请调整相关脚本

DONE

P: 再在报告中补充说明一下，实际上如果数据压力不大的话，完全可以存直接存储动作开始到结尾对应的密采样的holistic结果，都不用进行关键帧选择了，把标准样本的结果放进数据库，而实时检测时，直接对比数据库里标准样本的holistic结果和当前视频的密采样结果，对整体的时间序列进行相似度计算和匹配或许就行。

TODO：
这里面最大的难点可能就是进行有鲁棒性的时许匹配。



TODO
P：可以统计一下一个后台worker初始化和运行时分别需要的cpu资源和内存资源。

TODO
P:下一步可以继续把这条线升级成真正的“端口池”版 worker，这样前端就能直接
  按端口把帧切片或视频请求打到不同常驻实例上。




### 后续检测打分阶段
和目前建立标准样本库中的打分

- **signLanguage 后台 worker 池与可视化更新**：已启动 10 个常驻 `Holistic` 后台 worker（`tmux` session 方式），并在 `花.mp4` 上用 4 个策略并行跑出新一轮选择结果；随后补生成四策略联系表与时间轴可视化，已嵌入 `20260429_three_layer_sampling_summary.md/docx`，可视化输出目录为 `/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals_run2/`

- **signLanguage 策略可视化修正**：策略可视化阶段确认只读 `Holistic` JSON，不再重新跑识别；公共渲染函数改为直接按 JSON 里的 landmark 坐标手工绘制关键点和骨架，避免 `drawing_utils` 在反序列化结果上的空绘制问题
- **signLanguage workflow skill**：已创建本地 skill `signlanguage-workflow`，后续 signLanguage 的采样、worker、可视化和报告工作流默认按该 skill 的三层架构、常驻 worker 和 JSON 读写口径执行


# workEpoch2 26/5/20~

## 2026-05-20

P: 现在，根据已有结果，沿着后续计划继续探索，一是建立标准数据采集方案，二是设计打分机制（关键帧选取、时序对齐、逐关节差异分析与相似度评分等）。请把相关探索更新到工作日志里，形成一个完整的工作闭环。请你启动skill中的自主探索模式，派生具体的skill。请你说明工作计划，我确认后正式启动

A: 下面是确认版工作计划。

  派生 Skill

  拟派生专用 skill：

  - 名称：signlanguage-scoring-autonomous
  - 路径：/home/wuyangcheng/.codex/skills/new/signlanguage-scoring-autonomous/
    SKILL.md
  - 来源：从 long-running-autonomous-project-management 派生，并叠加 signlanguage-
    workflow 的项目规则
  - 目标：持续推进 /data/WYC/signLanguage 的“标准数据采集方案 + 手语动作打分 MVP”闭
    环，直到形成可复用方案、原型脚本、实验结果和报告

  这个 skill 会固化以下规则：

  - 继续使用 /home/wuyangcheng/myenv
  - Holistic 计算优先复用常驻 worker / 缓存 JSON
  - 打分探索优先基于 dense Holistic 时间序列，关键帧策略作为压缩版方案
  - 所有报告明确区分：候选生成、选择、时序对齐、逐关节误差、总分计算
  - 每次阶段进展更新项目日志和全局记忆

  启动后的执行计划

  1. 建立任务闭环文档
     我会补充并维护：
      - /data/WYC/signLanguage/work/worklog_sign.md
      - /home/wuyangcheng/.codex/memories/projects/signLanguage/work_log.md
      - /data/WYC/signLanguage/work/reports/scoring_mvp_followup_20260520.md
      - /data/WYC/signLanguage/work/reports/scoring_mvp_phase_summary_20260520.md

     另外我会把 worklog_sign.md 里当前 2025/5/20 修正为实际日期 2026-05-20。
  2. 标准数据采集方案设计
     输出一份可执行采集规范，覆盖：
      - 每个词汇需要多少标准样本、多少用户测试样本
      - 拍摄角度、距离、光照、背景、帧率、分辨率
      - 动作起止标注规则
      - 是否保留原视频、dense Holistic JSON、关键帧结果、可视化图
      - 标准样本库字段设计和版本管理
      - 质量控制指标，比如手部覆盖率、pose 稳定性、缺帧率、动作完整性
  3. 打分机制设计
     形成 MVP 打分框架：
      - 输入：标准样本 dense Holistic 序列 + 用户视频 dense Holistic 序列
      - 预处理：坐标归一化、尺度对齐、左右手/pose/face 权重、缺失点处理
      - 关键帧方案：uniform_select、two_stage_select、adaptive_select、能量覆盖率筛
        选
      - 时序对齐：优先探索 DTW / 分段 DTW / 关键帧锚点对齐
      - 逐关节差异：手部、手腕、肘肩、躯干、面部可分组统计
      - 相似度评分：整体分、手部动作分、姿态稳定分、节奏分、完成度分
      - 诊断输出：指出哪个时间段、哪个关节组偏差最大
  4. 原型实验
     基于现有 demo 视频先做可运行验证：
      - 复用已有 Holistic JSON 缓存，缺失时再通过 worker 生成
      - 先做“标准样本 vs 查询样本”的模板匹配原型
      - 在当前 demo 只有少量样本的前提下，先验证流程正确性，不虚假声称评分泛化可靠
      - 输出 JSON 指标、可视化对齐图、逐关节误差图和中文分析报告
  5. 自主探索模式组织
     正式启动后，我会按 skill 的自治流程运行：
      - 当前会话作为 coordinator
      - 如需要并行，会使用 skill 里的 tmux Codex worker，不使用内置 subagent
      - 维护 .codex/tmux-workers/COORDINATOR_SCHEDULE.md
      - 让分支任务分别处理：资料审计、采集方案草案、评分原型、报告整合
  6. 完整闭环交付
     阶段结束时应至少形成：
      - 派生 skill
      - 标准数据采集方案
      - 打分机制设计文档
      - 可运行评分原型或最小实验脚本
      - 实验结果目录
      - 更新后的项目 worklog
      - 更新后的全局 signLanguage memory


Q: 当前其实还没有用户视频流样本，会影响你的计划吗

A: • 不会阻塞，但会影响验证口径。

  当前没有用户视频流样本，意味着我们暂时不能做这几件事：

  - 不能可靠校准“多少分算好 / 合格 / 不合格”
  - 不能验证真实用户动作偏差类型，比如左右手不到位、节奏慢、动作漏做
  - 不能证明评分对不同人、不同拍摄环境有泛化性
  - 不能做真实的“标准样本 vs 用户样本”闭环评测

  但不影响继续推进这两条主线：

  1. 标准数据采集方案
     反而更应该先做。因为现在缺的正是未来打分系统需要的数据规范：每个词采几条、怎么
     拍、怎么标动作起止、怎么保存 dense Holistic JSON、怎么做质量控制。
  2. 打分机制原型
     可以先用现有 demo 视频做方法验证，而不是最终性能评估。具体方式：
      - 用现有 demo 当标准样本库雏形
      - 用同一视频的不同采样密度、截断片段、轻微扰动版本做“伪用户样本”
      - 用不同词汇之间的对比做负例 sanity check
      - 先验证：坐标归一化、DTW 时序对齐、逐关节误差、总分计算、诊断输出是否跑通

  所以我会把计划修订为：

  - 第一阶段：不宣称真实评分效果，只完成“采集规范 + 数据结构 + 评分算法原型 + 离线
    sanity check”
  - 第二阶段：等有真实用户样本后，再做阈值校准、评分等级、泛化评估和前端实时流闭环

  实时视频流本身也不是阻塞点，因为已有 frame_slices worker 路径可以模拟“前端逐帧/分
  片发送”。当前真正缺的是真实用户动作样本和人工评分标签。

  确认后我会按这个修订版启动。

P: 好，请正式启动

STATUS 2026-05-20 17:20:00 CST：

- 已正式启动 `signLanguage` 标准数据采集与打分 MVP 自主探索线。
- 已派生专用 skill：`/home/wuyangcheng/.codex/skills/new/signlanguage-scoring-autonomous/SKILL.md`。
- 本轮任务基于 `signlanguage-workflow` 和 `long-running-autonomous-project-management`，后续默认按常驻 worker、raw `Holistic` JSON 缓存、dense 时间序列匹配和 tmux Codex worker 协作推进。
- 已明确当前缺少真实用户视频流样本和人工评分标签，因此第一阶段只做“标准采集规范 + 数据结构 + 打分算法原型 + 离线 sanity check”，不宣称真实用户评分准确性、阈值有效性或泛化能力。
- 已建立阶段跟进文档：`/data/WYC/signLanguage/work/reports/scoring_mvp_followup_20260520.md`。
- 已建立阶段总结文档：`/data/WYC/signLanguage/work/reports/scoring_mvp_phase_summary_20260520.md`。
- 下一步通过 tmux Codex worker 并行推进资料/缓存审计、标准采集方案草案、打分机制设计和最小评分原型计划，coordinator 负责最终整合。

STATUS 2026-05-20 17:50:00 CST：

- 四个 tmux Codex worker 已完成并输出草案：
  - 数据/缓存审计：`/data/WYC/signLanguage/work/reports/scoring_data_cache_audit_20260520_draft.md`
  - 标准采集协议：`/data/WYC/signLanguage/work/reports/standard_data_collection_protocol_20260520_draft.md`
  - 打分机制设计：`/data/WYC/signLanguage/work/reports/scoring_mechanism_design_20260520_draft.md`
  - 原型实施计划：`/data/WYC/signLanguage/work/reports/scoring_mvp_prototype_plan_20260520_draft.md`
- coordinator 已新增离线评分 MVP 脚本：`/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py`。该脚本只读已有 `Holistic` JSON，不重新运行 MediaPipe；支持 raw landmark 模式和旧 bbox 兼容模式。
- 已完成初始 sanity check，结果目录为 `/data/WYC/signLanguage/work/generated/scoring_mvp_run1/`，报告为 `/data/WYC/signLanguage/work/reports/scoring_mvp_initial_experiment_20260520.md`。
- 关键结果：`花` raw landmark 自身对齐 `prototype_score=100.000`；`花` 降采样/裁剪伪用户样本约 `93.987-98.046`；`花` vs 稀疏 `唱歌` raw landmark 负例约 `62.945`；旧 bbox `花` vs `唱歌` 负例仍有 `85.837`，说明 bbox 只适合兼容诊断，不能作为主评分特征。
- 已形成闭环整合方案：`/data/WYC/signLanguage/work/reports/scoring_mvp_integrated_plan_20260520.md`。
- worker 运行中发现 `.codex/tmux-workers/progress` 和 `.codex/tmux-workers/reports` 在 worker sandbox 内不可写，但项目 owned report 路径可写；本轮证据已通过项目报告和 manager capture 保留。
- 下一步优先为其余 demo 视频生成统一 step-4 raw landmark 缓存，补充不同词负例，并在评分脚本中拆出 `confidence_score`、对齐图和逐组误差曲线。

STATUS 2026-05-20 18:25:00 CST：

- 根据“当前 `花` vs `唱歌` 区分度仍弱”的反馈，已继续优化打分模块，目标改为：目标动作合理变体高分，其他 demo 动作和随机假动作显著低分。
- 已更新 skill：`/home/wuyangcheng/.codex/skills/new/signlanguage-scoring-autonomous/SKILL.md`，补充判别性门控目标和当前参考结果。
- 已更新评分脚本：`/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py`，新增 `--run-discrimination-suite`、`--negative-json label=path`、目标动作裁剪/降采样/幅度调整正例、随机假动作负例、序列级惩罚、端点一致性和幅度缩放鲁棒性。
- 已修复 `/data/WYC/signLanguage/work/scripts/benchmark_holistic_worker.py`：当前环境没有 `ffprobe` 时，帧切片模式改用 OpenCV `CAP_PROP_FRAME_COUNT/FPS` 读取总帧数和 fps，避免所有视频只采第 0 帧。
- 已用一个常驻 Holistic worker 生成 10 个 demo 的 step-4 raw landmark 缓存：`/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache_v2/`；worker 初始化 `260.107s`，全流程 `274.915s`。
- 已完成 `花` 目标动作全 demo 判别实验：`/data/WYC/signLanguage/work/generated/scoring_mvp_run2/flower_all_demo_discrimination_v2/`。
- 最终门控结果：目标动作正例最低分 `75.494`，负例最高分 `41.495`，分离 margin `33.999`，门控通过。其他 9 个 demo 对 `花` 的得分全部低于 `21`，随机假动作最高 `41.495`，目标动作裁剪/降采样/幅度调整变体均高于 `75`。
- 新增报告：`/data/WYC/signLanguage/work/reports/scoring_mvp_discrimination_optimization_20260520.md`。
- 当前结论仍是 demo-only sanity gate，不是用户评分阈值；下一步可把同样套件推广到其他 demo 词，并补 `confidence_score`、对齐图和逐组误差曲线。

### 打分区分度实验
Q: 你实验的用唱歌和话交叉打分是个不错的方式，不过当前的区分度似乎还是太弱了？你看看怎么优化。你当前的目标可以设置为，在目标动作场景下，其他demo动作打分显著低；同时你可以基于demo视频生成随机假动作，来进行打分测试，要求打分低；而基于目标动作的裁剪和动作幅度调整，应该对应较高分数。请让打分模块实现这样的功能。请你更新相应skill。请你继续自主探索模式，完成所有目标。


P: 先总结一个当前完整打分方案的md工作报告，说明采用的策略，目前的实验场景，同时导出word版




## 2026-05-22



STATUS 2026-05-22 21:45:00 CST：

- 已按当前打分 MVP 进展整理完整方案工作报告，路径为 `/data/WYC/signLanguage/work/reports/scoring_scheme_current_report_20260522.md`。
- 已导出同名 Word 版本：`/data/WYC/signLanguage/work/reports/scoring_scheme_current_report_20260522.docx`。
- 报告覆盖当前采用策略、数据/缓存路线、评分机制、`花` 目标动作 demo-only 判别性实验场景、正例/假动作/其他 demo 负例结果、工程可用性判断和后续工作。
- 报告继续明确当前没有真实用户视频流样本和人工评分标签，因此 `75/50` 只作为离线工程 sanity gate，不作为正式用户评分阈值。

STATUS 2026-05-22 22:25:00 CST：

- 已实现基础网页前端和常驻 Holistic 后端 MVP：
  - 后端：`/data/WYC/signLanguage/work/web/backend.py`
  - 前端：`/data/WYC/signLanguage/work/web/static/index.html`
  - 样式：`/data/WYC/signLanguage/work/web/static/styles.css`
  - 交互脚本：`/data/WYC/signLanguage/work/web/static/app.js`
  - 运行说明：`/data/WYC/signLanguage/work/docs/web_scoring_mvp.md`
- 后端采用 FastAPI，当前绑定 `127.0.0.1:5080`，启动时异步初始化一个常驻 `holistic_worker_daemon.py` 子进程；网页和 API 在同一个服务下，Windows 本地浏览器可通过 SSH local tunnel 访问 `http://127.0.0.1:5080` 并申请本机摄像头权限。
- 前端已支持：选择目标 demo 模板、开启摄像头、按时长/FPS/帧宽采集 JPEG 帧、POST 到 `/api/score`、展示 `prototype_score`、DTW 距离、normalized distance、Holistic 耗时、分组平均距离和 sequence penalty。
- 后端已接入当前 10 个 demo step-4 raw landmark 模板库 `/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache_v2/results/`，并复用 `score_holistic_sequence_mvp.py` 中的 `load_sequence/run_pair` 评分逻辑。
- 已在 tmux session `signlanguage-web` 启动服务，日志 `/data/WYC/signLanguage/work/logs/web_scoring_backend.log`；`/api/status` 显示 worker ready，Holistic 初始化耗时 `260.116s`。
- 已用服务器端 `花.mp4` 抽帧模拟浏览器上传跑通 `/api/score`，返回 request `web_20260522_222243_a23d679c`，12 帧测试 `prototype_score=57.392`、`dtw_distance=0.026631`、`normalized_distance=0.066631`、`holistic_eval_sec=0.597`、`api_total_sec=0.796`，输出 JSON 位于 `/data/WYC/signLanguage/work/generated/web_scoring_mvp/web_20260522_222243_a23d679c/`。
- 当前网页输出仍是 demo-only prototype similarity，不是正式用户评分；下一步应补动作起止检测、多模板匹配、`confidence_score`、对齐图和真实用户样本校准。

STATUS 2026-05-22 22:40:00 CST：

- 已根据四位数端口要求，把 Web 打分 MVP 默认端口从 `18080` 调整为 `8080`。
- 已同步更新 `/data/WYC/signLanguage/work/web/backend.py`、前端提示 `/data/WYC/signLanguage/work/web/static/index.html` 和运行说明 `/data/WYC/signLanguage/work/docs/web_scoring_mvp.md`。

STATUS 2026-05-22 22:50:00 CST：

- 已按“5 开头四位数端口”要求，把 Web 打分 MVP 默认端口从 `8080` 调整为 `5080`。
- 已同步更新后端监听端口、前端提示、运行说明、项目 memory 和全局 memory。
- Windows 本地访问方式改为 `ssh -N -L 5080:127.0.0.1:5080 ...` 后打开 `http://127.0.0.1:5080`。
- 已重启 tmux session `signlanguage-web` 并确认当前仅监听 `127.0.0.1:5080`；`/api/status` 显示 worker ready，模板数 `10`，本次 Holistic 初始化耗时 `260.121s`。

STATUS 2026-05-22 23:00:00 CST：

- 已按“保留旧版、派生新版本方便对比”的要求新增参考视频版 Web MVP v2，旧版 `5080` 不动，新版监听 `127.0.0.1:5081`。
- v2 后端入口：`/data/WYC/signLanguage/work/web/backend_v2.py`；v2 前端目录：`/data/WYC/signLanguage/work/web/static_v2/`；v2 运行说明：`/data/WYC/signLanguage/work/docs/web_scoring_mvp_v2.md`。
- v2 页面在采集区增加“查看参考”按钮，参考动作视频默认隐藏；用户点击后才展开右侧小参考视频，再点击“隐藏参考”可收起。参考视频随目标动作下拉框切换，来源为 `/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/`。
- 已启动 tmux session `signlanguage-web-v2`，当前 `5080` 和 `5081` 同时监听；`/api/status` 显示 v2 worker ready，模板数 `10`，本次 Holistic 初始化耗时 `260.126s`。已验证 `/api/reference-video/香蕉` 返回 MP4。

STATUS 2026-05-22 23:10:00 CST：

- 已按“v1/v2 保留、在 v3 上增加倒计时”的要求派生 Web MVP v3，端口为 `127.0.0.1:5082`。
- v3 后端入口：`/data/WYC/signLanguage/work/web/backend_v3.py`；v3 前端目录：`/data/WYC/signLanguage/work/web/static_v3/`；v3 运行说明：`/data/WYC/signLanguage/work/docs/web_scoring_mvp_v3.md`。
- v3 保留 v2 的“查看参考”按钮和默认隐藏参考视频逻辑，同时在用户摄像头画面上新增 3 秒倒计时覆盖层。点击“采集并打分”后先显示 `3、2、1、开始`，倒计时结束后才正式采集帧并提交评分。
- 已启动 tmux session `signlanguage-web-v3`，当前 `5080/5081/5082` 同时监听；`/api/status` 显示 v3 worker ready，模板数 `10`，本次 Holistic 初始化耗时 `260.116s`。已验证 v3 页面包含倒计时元素，参考视频接口可返回 MP4。

STATUS 2026-05-22 23:15:00 CST：

- 根据“前端版本应复用同一个 Holistic 后端”的反馈，已调整 Web 架构：`5080` 作为唯一共享评分/Holistic 常驻后端，`5081` v2 和 `5082` v3 只保留静态前端、参考视频接口和轻量 API 代理。
- 已改造 `/data/WYC/signLanguage/work/web/backend_v2.py` 和 `/data/WYC/signLanguage/work/web/backend_v3.py`，移除各自的 `HolisticWorkerService` 启动逻辑；其 `/api/status`、`/api/templates`、`/api/score` 统一代理到 `http://127.0.0.1:5080`。
- 已重启 tmux session `signlanguage-web-v2` 和 `signlanguage-web-v3`。当前 `5080/5081/5082` 均监听，但 `holistic_worker_daemon.py` 只有 `1` 个进程，即 `5080` 共享后端持有的 worker。
- 已验证 v2/v3 `/api/status` 均显示 shared backend ready；已通过 v3 `/api/score` 代理完成一次 6 帧 smoke test，返回 `frontend_proxy.version=v3_countdown_reference_video`，说明前端版本代理到共享后端的链路可用。


### 实现简单前端网页demo和对应常驻后端
P: 现在，实现基础的网页前端和对应的常驻holistic后端，从而能够实现基础的功能：网页前端申请电脑的摄像头权限，从而能获取用户几秒的视频流，然后发送视频帧给服务器常驻后端，基于已有方案，根据目前已经建立的基础数据库进行打分。你codex现在在远端服务器上，我希望我能够在本地windows电脑上运行网页前端，你看看如何实现？

不错，网页端可以再补充一个版面展示demo的参考视频动作，这个参考动作的界面可以小一些，页面其他的部分仍然保留，请你调整出合适位置。之前建议的网页端口仍然保留，你可以派生新版本，使用新端口，方便对比调整。请你实现。

这个参考视频版面可以设置按钮，选择开启还是不开启，因为是测评，所以默认不开启；如果用户需要可以“查看参考”。


P: 网页端点击“采集并打分”后，可以在用户视频界面增加一个3s倒计时，方便用户准备和开始。请你在v3上调整。v1，v2的端口和脚本都保留，方便比较。

P: 实际上前端可以复用同样的holistic后端吧？不用每启动一个新的前端就也要启动一个新的后端吧，请改进逻辑。



P: 所以现在的工作流中，前端网页通过摄像头采集视频流后，传输了什么给服务器后端？可以写一个当前前后端实现的具体报告md吗

STATUS 2026-05-22 23:25:00 CST：

- 已整理当前 Web 前后端实现报告：`/data/WYC/signLanguage/work/reports/web_frontend_backend_current_implementation_20260522.md`。
- 报告明确当前前端不是上传完整视频文件，也不是上传 `MediaStream`；实际上传的是按固定 FPS 从摄像头画面抽取、经 canvas 缩放并 JPEG 压缩后的多帧 base64 JSON。
- 报告覆盖字段级请求体：`target_word`、`fps`、`duration_sec`、`frame_indices`、`frames[].image_format`、`frames[].image_b64`、`wait_for_ready_sec`，并说明不上传音频、不上传 MP4/WebM、不上传未压缩原始帧。
- 报告也说明当前共享后端架构：`5080` 唯一持有 Holistic worker，`5081/5082` 只做代理和参考视频；后端将帧切片解码为 OpenCV 图像，走 `frame_slices` worker 路径生成 raw Holistic JSON，再调用现有 DTW 打分。



P: 网页还有一些细节可以调整：1.增加摄像头关闭的逻辑，可以在同一个按钮上 2. 左边的视频实时视频显式版面可以更宽一些，右边的结果版面可以调窄一些。 改动后让5080端口加载这个新版本

网页的视频板块高度要小一些，可以保持为显示参考时候的视频板块大小，只是那个小的参考视频板块在不显示参考时候就隐藏；这个大小刚好能让下方的按钮和文字能在不滚动页面的情况下露出来，方便查看。


Q: holistic后端和前端的调整应该是独立的吧，启动不同端口的前端，按理说和固定后端不冲突？所以你更新页面设计后，启动新的端口，只需要继续和之前的常驻后端发消息即可吧（不用总是重新初始化后端？），目前我们先只建一个常驻后端，未来可以扩充成为后端池，方便处理前端高并发的操作。
请你完善后，更新前后端设计的报告文档，然后导出word

STATUS 2026-05-22 23:55:00 CST：

- 已按“前端与 Holistic 后端独立”的架构口径新增 v4 前端代理：`/data/WYC/signLanguage/work/web/backend_v4.py`，静态目录 `/data/WYC/signLanguage/work/web/static_v4/`，端口 `127.0.0.1:5083`。
- `5083` 只服务页面、参考视频和轻量 API 代理；`/api/status`、`/api/templates`、`/api/score` 均转发到共享后端 `http://127.0.0.1:5080`，不会启动新的 `HolisticWorkerService`。
- v4 页面保留默认隐藏参考视频、3 秒倒计时和同按钮开关摄像头；同时调整参考隐藏时的用户视频宽度，保持接近参考开启时的紧凑高度，避免按钮和提示文本被挤出首屏。
- 已启动 tmux session `signlanguage-web-v4`；当前 `5080/5081/5082/5083` 均监听 `127.0.0.1`，但 `holistic_worker_daemon.py` 仍只有 1 个进程，属于 `5080` 共享评分后端。
- 已更新前后端设计报告 `/data/WYC/signLanguage/work/reports/web_frontend_backend_current_implementation_20260522.md`，并导出 Word 版 `/data/WYC/signLanguage/work/reports/web_frontend_backend_current_implementation_20260522.docx`。报告补充了固定评分后端、多前端代理、浏览器上传帧格式、当前 v4 页面、运维策略和未来后端池扩展方案。

STATUS 2026-05-23 00:20:00 CST：

- 已按“Holistic 后端保留一个，其他 tmux 后端关闭”的要求收敛运行态：关闭 `signlanguage-web-v2`、`signlanguage-web-v3`、`signlanguage-web-v4`，只保留 `signlanguage-web`。
- 当前仅 `127.0.0.1:5080` 在监听；`5081/5082/5083` 已不再监听。`holistic_worker_daemon.py` 仍只有 1 个进程，PID `3570432`，归属 `5080` 后端。
- 已把 v4 的紧凑用户视频布局同步到 `5080` 静态页面，用户继续通过 `http://127.0.0.1:5080` 使用摄像头开关、默认隐藏参考、3 秒倒计时和当前新版布局。
- 已同步更新运行说明 `/data/WYC/signLanguage/work/docs/web_scoring_mvp.md` 以及前后端设计报告 `/data/WYC/signLanguage/work/reports/web_frontend_backend_current_implementation_20260522.md`，并重新导出 Word 版。






### 安全访问端口
Q: 关于安全访问服务器网页，能不能设置成内网（校园网）ip用户就可以正常访问服务器上面的端口？这样应该也算安全？




## 2026-05-23
### 打分优化：提高打分准确性



P: 经过实际测试，目前打分的鲁棒性还不够，测试评分明显偏低。
关键在于，要根据资料的文本参考给出对应样本中各个特征（脸/手/手臂等）的加权（或mask），体现动作正确性的重点，比如“花”这个动作，其实重点就是手部的张开的动作，其他的面部等特征都不重要。
另外，动作本身的关键语义，也只在于关键特征中的关键节点的相对移动，比如“花”的手部张开，其实只是手指关节“张开”的相对移动，看看当前的DTW等算法是不是能有效捕捉其中的正确性。

那么，你需要根据data里面的文本说明，补充数据库中的权重信息，并且优化打分算法。请你补充实现。


？根据文档说明自动提取重点特征并给出具体特征权重，这一步可以用大模型快速完成吧？

### 语义特征的简化？
P: 或许，具体的手语动作语义可以简化成各种“相对运动”，比如手指关节的张开/合并，比如手部相对躯干向左/向右/向上/向下的移动，比如手和手之间相对移动。这些重要特征中的相对运动，一部分可以从文档资料中提取出来，另外就需要从视频原本的密集采样中识别出来，并保存到相应的语义数据中。对于用户的输入视频流，由于其实只是针对目标词汇的动作识别，所以可以直接分析重要特征的相对运动，来和数据库进行语义相似度比较，从而打分。

当然，上述这套流程非常“手工化”，未来或许可以用深度学习来自动抓取“重要特征的相对运动”信息。

P: 另外，既然关键看的是 “重要特征的相对运动”，所以数据库也应该采取类似能量密度覆盖的方式，强调关键的动态部分，或者说，给密集采样的时间序列附上权重，不同帧的权重不一样，关键动作上面的权重要显著高，这对于后续进行DTW对齐等计算很重要。


NEW:!!
• 回放已有网页测试结果后，花 的旧分数大多在 15-30，语义加权后多数提升到 60-80，
  其中较完整的几次提升到 75-80；质量较差或动作不完整的样本仍保持偏低。现在我会生
  成一份实现记录，然后重启唯一的 5080 服务使网页端真正加载新代码。

STATUS 2026-05-23 00:50:00 CST：

- 已实现文本语义加权评分更新，新增 profile 生成脚本 `/data/WYC/signLanguage/work/scripts/build_semantic_weight_profiles.py`，读取 `/data/WYC/signLanguage/data/Demo词汇.docx` 并按动作语义关键词为 10 个模板词生成权重配置。
- 已生成语义权重库 `/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json` 和可读报告 `/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.md`。其中 `花` 的 profile 主要权重为 `right_hand_shape=0.35`、`right_hand=0.32`、`left_hand_shape=0.18`、`left_hand=0.12`，`pose/face=0`。
- 已优化 `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py`：新增左右手 shape 特征、关键指尖/拇指节点加权、左右手互换匹配、语义起止变化惩罚和更强 roughness penalty，用于抑制倒放/乱序假动作。
- `花` 目标动作离线判别实验输出 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_semantic_weighted_discrimination_v6/`：正例最低 `81.437`，负例最高 `49.049`，margin `32.388`，工程门控通过。
- 已回放已有网页采集样本，`花` 的若干旧低分样本明显回升，例如 `web_20260522_232642_fe440fb9` 从 `30.093` 升到 `79.683`，`web_20260523_000852_b2c2f1de` 从 `27.923` 升到 `75.351`，同时明显质量差/动作不完整样本仍保持偏低。
- 已在 `/data/WYC/signLanguage/work/web/backend.py` 接入语义 profile，`/api/status` 和 `/api/templates` 返回 profile 信息，`/api/score` 的 `score.semantic_profile` 返回本次使用的权重配置。
- 已整理实现报告 `/data/WYC/signLanguage/work/reports/scoring_semantic_weighted_update_20260523.md`，并导出 Word 版 `/data/WYC/signLanguage/work/reports/scoring_semantic_weighted_update_20260523.docx`。
- 已重启唯一的 `5080` 常驻 Web/Holistic 后端以加载新评分代码；重启过程中仍只保留一个 `signlanguage-web` tmux 服务和一个 Holistic worker。
- 2026-05-23 00:55 CST 复核：`5080` worker 已 ready，本次 Holistic 初始化 `389.252s`；当前只监听 `127.0.0.1:5080`，没有 `5081/5082/5083`。网页默认上传帧宽已从 `480` 改为 `960`，以提高小手部区域的 Holistic 检测稳定性。`5080/api/score` 使用 `花.mp4` 标准采样帧 smoke test 返回 request `web_20260523_005320_4bd5e0a3`，语义加权 score `79.347`，`score.semantic_profile.word=花`。





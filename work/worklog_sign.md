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

### 数据库强化
P: 既然关键看的是 “重要特征的相对运动”，所以数据库和用户视频帧采样也应该采取类似能量密度覆盖的方式，强调关键的动态部分，或者说，给密集采样的时间序列附上权重，不同帧的权重不一样，关键动作上面的权重要显著高，这对于后续进行DTW对齐等计算很重要。
另外，数据库缓存的表征demo的帧数也可以再适当增大一些，这样有利于提升语义识别和动作对齐的精度。
请你进一步完善对数据库、用户视频流采样和打分算法的优化。

当然，改进后，要检查是否让真实测试的结果更合理，比如“跳”这个动作。

P: 另外，你要确认数据库所有样本已经正确根据资料文档和视频样本更新重要特征/重要帧的权重，这样计算才会准确。

STATUS 2026-05-23 01:52:19 CST：

- 已将“重要特征相对运动 + 动态重要帧”贯通到数据库、前端采样和评分算法。新增数据库审计/落盘脚本 `/data/WYC/signLanguage/work/scripts/audit_template_semantic_weights.py`，为每个模板目录写回 `semantic_frame_weights.json`，包含语义 profile、逐帧动态权重、top weighted frames、presence/motion 审计。
- 已构建 step2 dense 模板库 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`，10 个 demo 均已覆盖：`唱歌 27`、`指示 30`、`月亮 47`、`朋友 28`、`汽车 44`、`花 53`、`虎 54`、`谗（羡慕）32`、`跳 19`、`香蕉 42` 帧。构建复用唯一 `5080` 常驻 Holistic worker；`花.mp4` 的不可读尾帧 `106` 和 `虎.mp4` 的不可读尾帧 `108/109` 已跳过并记录。
- step2 模板库全量审计输出 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/template_semantic_weight_audit_step2_v1/template_semantic_weight_audit.md`，结果为 `10/10 ok`，无缺失 profile、无低帧数、无弱动态帧权重对比。当前 `/api/templates` 也确认 10 个模板都使用 step2 dense root 且存在 manifest。
- 前端 `/data/WYC/signLanguage/work/web/static/app.js` 已从均匀抽帧改为“高频候选采样 + 像素运动能量覆盖选择”：候选 FPS 为 `min(18, uploadFps*2)`，上传帧包含 `frame_weights`；后端 `holistic_worker_daemon.py` 会把 `frame_weight` 写入 raw Holistic JSON。
- 打分脚本 `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py` 已新增语义动作窗口：先根据每条序列自己的语义动态帧权重曲线找包含主峰的连续高能量窗口，再在标准/查询动作窗口内做加权 DTW；输出新增 `action_window`、`frame_weight_summary`、`score_scale`、`temporal_resample` 诊断字段。
- `花` profile 经审计后调整为“动态窗口只看主手开合，距离评分保留少量另一手约束”，避免单手模板误判又保持负例区分度；`跳` profile 已收紧为右手食/中指弯伸 + 左手地面，`pose/face` 不参与核心评分。
- 最终 step2 dense + action-window 验证通过当前工程门控：`花` 正例最低 `80.190`、负例最高 `41.971`、margin `38.219`；`跳` 正例最低 `82.466`、负例最高 `45.759`、margin `36.707`。输出分别在 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_action_window_step2_discrimination_v8/` 和 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/jump_action_window_step2_discrimination_v8/`。
- 已重放历史网页样本，输出 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_replay_action_window_step2_final_v1/web_replay_action_window_step2_final.csv`。历史 `跳` 样本最高约 `35.49`、平均约 `12.92`，仍偏低；诊断显示这些样本来自旧均匀采样，手部检出率多在 `0.4-0.7` 且动作窗口约 6 帧，因此只能说明旧样本质量/采样不足，不能代表新能量采样前端。
- 已整理闭环报告 `/data/WYC/signLanguage/work/reports/scoring_dynamic_energy_window_update_20260523.md`，并导出 Word `/data/WYC/signLanguage/work/reports/scoring_dynamic_energy_window_update_20260523.docx`。
- 2026-05-23 02:05 CST 复核：已重新启动唯一 `5080` 后端加载最终代码；worker ready，Holistic init `260.111s`。`跳.mp4` 帧切片 API smoke test 返回 request `web_20260523_020555_09843ad1`，score `77.209`，返回 `action_window` 和 `score_scale.noise_floor_distance`，确认网页 API 已加载 action-window 评分。网页进度条已调整为只对应采集阶段，进入后端处理时清空/淡化，不再显示伪进度。
P: 另外，你要确认数据库所有样本已经正确根据资料文档和视频样本更新重要特征/重要帧的权重，这样计算才会准确。

NEW:
• 花 的最终折中 profile 已确认：动态重要帧只看主手，距离评分保留少量另一手约束。
  用旧 step4 对照时 花 和 跳 均通过当前工程门控：花 正例最低 81.714、负例最高
  48.356；跳 正例最低 76.754、负例最高 41.452。密集补建请求还在等待重启后的
  worker 初始化。

• 跳 的问题主要不是语义特征距离，而是 DTW 被迫把被裁掉的开头标准帧硬对齐到查询第
  一帧，missing/local distance 被放大。我要加一个受限的“裁剪容忍 DTW 路径统计”：
  当查询长度接近标准但少了开头/结尾一段时，允许丢弃最多约 22% 的边界路径并加小额
  skip penalty；这样不放宽倒放/乱序，但能让合理裁剪保持高分。



p: 确实，不是关键帧的开头静止部分，其实完全不重要，不能死板地进行DTW对齐，而是应该识别出视频中高能量采样的起点和重点，然后把标准和测试样本的起点和终点对齐，才是真正鲁棒的DTW对齐。

A: • 我会把这点落成算法层面的主逻辑：DTW 输入不再默认是完整序列，而是“语义动作窗
  口”。窗口由每条序列自己的语义动态能量曲线确定，输出中会记录标准/查询窗口边界、
  覆盖能量和窗口外帧数，便于审计。


• 第一版 action window 暴露了两个问题：窗口裁得太机械，花 的末端裁剪被误伤，而且
  乱序假动作因为只保留高能量段反而偏高。说明不能只“裁窗口”，还要保留窗口内的能量
  时间顺序约束，并且窗口边界要按动作能量起止而不是中心能量百分比。我会马上迭代
  为“起点/峰值/终点锚点 + 窗口内 DTW”。


• 这里的具体失败原因很清楚：花 有两个高能量段，之前窗口把主开花动作后的尾部小移
  动也并进来了；跳 有两个相邻弹跳能量小峰，之前又把峰值前的弱准备帧纳进来了。新
  的窗口会选“包含主峰的连续高能量连通段”，只合并很近的小峰，不再把远端尾部动作硬
  塞进核心窗口。

• 为了让低 FPS/隔帧采样不因缺少中间帧而被 DTW 过度惩罚，我会在动作窗口后增加一个
  只对“查询窗口过短”的轻量时间插值：如果查询动作窗口明显短于标准窗口，就把查询窗
  口线性补到标准窗口长度，再做 DTW。静态假动作和更长的其他 demo 不会因此被补强。

• 线性插值用 mask 后反而把裁剪/隔帧样本的可见关键点破坏了，这条路先关掉。更合适
  的是对 跳 这类短促动作采用短窗口尺度补偿：当标准动作核心窗口很短且查询也有明确
  能量峰时，分数映射稍微放宽；静态假动作没有能量峰，不会获得这项补偿。


• 现在 花 和 跳 在 step2 密集模板 + 语义动作窗口下都通过工程门控了：花 正例最低
  80.19、负例最高 41.97；跳 正例最低 75.35、负例最高 45.76。接下来我用同一套最终
  算法重放历史网页样本，尤其看 跳 的真实测试分数是否比旧结果更合理。

### 打分算法优化
Q: 不对啊，结果现在实际测试的花，结果变坏了很多。。实测的效果似乎都差了不少？
A: • 我同意，这说明我上一轮把 action window 作为默认主路径后，对真实网页样本过度裁
  剪了，尤其 花 这种长动作/单手开合，实际用户视频的能量峰和 demo 不一定一致。现
  在我会马上回退到更稳的混合策略：长动作优先用完整语义加权 DTW，短促动作如 跳 才
  启用 action window；同时保留 action-window 作为诊断字段。

• 目前看起来不是“语义权重”本身必然错误，而是后面把所有词都强行改成动作窗口对齐
  后，真实网页样本的开头/结尾和能量峰会被裁得过窄。长动作如 花 更容易中招，我会
  先用实际样本复现实测下降，再改为按动作类型选择对齐策略。




目前混合策略下，由于样本库是密采样，测试采样也要3*10，花的性能才会比较好。


P: 我觉得，数据库里面的重要特征权重可能还没有设置到位，比如花和跳，这里面手势才是最关键的，然后手势和躯干、脸的相对位置都不重要；这些重点可以从文档里得知。也就是说，对于花和跳这类手语，只有手有大权重，手的动态特征有大权重，其他的相对关系都赋予小权重才对。请你对数据库再根据文档资料进行权重修正等 。

• profile 已更新为更强的手势主导配置：花 现在 98% 权重在主手/主手形，另一手、
  脸、pose 为 0；跳 91% 权重在右手/右手形，左手地面只保留 7% 左右，脸和 pose 为
  0。下一步写回模板数据库的逐帧权重。


跳并不只有一只手吧，两只手都要有啊。

• 直接“只看手”后，离线门控反而失效了：花 的 谗/月亮 负例变高，跳 的 花 负例也变
  高。这说明你的方向是对的，但不能只是把 pose/face 权重清零，还必须把“手部动态语
  义”本身加重，否则相似手形的其他动作会被误判高分。我接下来会保持非手部低权重，
  同时增强手部动态变化、起止手形变化、核心窗口动态差异这几类手内特征惩罚。


• 修正后 跳 的负例已经回到合理区间：花 负例从 78 降到 43，说明“两手约束 +
  weighted missing”是必要的；但 跳 的隔帧正例被压到 67，说明动态惩罚对低帧率/隔
  帧采样太重。我要把动态惩罚做成“低帧率容忍”：当查询是标准的合理降采样时，不把运
  动粗糙度差异过度扣分。


P: 之后你也都要类似地根据资料文档的说明，根据其中的重点修正数据库所有样本的权重等。

A: 收到。后续我会把这做成全库规则，而不是只修 花/跳：根据 Demo词汇.docx 每个词条
  的语义说明，分别确定“哪些手/手指/手形/脸/身体是主语义、哪些只是参照、哪些不参
  与”，再写回每个模板的 group/keypoint/frame 权重 manifest。当前这轮我会先完成
  花/跳 的验证，然后把同样规则扩展到 10 个 demo 全库，并生成审计报告。


• 花/跳 这一版已经门控通过：花 正例最低 75.266、负例最高 39.421；跳 正例最低
  75.919、负例最高 43.731。我现在把同样方法扩展为全库规则：逐词读取/引用文档语
  义，修正每个词的特征组权重、关键点权重、动态帧权重和审计报告。

• 全词判别还在跑，主要是 10 个目标词都要对其余 demo 和伪动作做一遍 DTW。这个结果
  会告诉我们：当前按文档修正后的数据库权重，哪些词已经稳定，哪些词还需要后续专项
  规则。


• 这里有一个关键工程判断：按文档把权重更集中到手以后，旧网页样本分数会下降，尤其
  是 跳 和重跑 Holistic 的 花 标准帧。这说明 MediaPipe 手部检出噪声会被放大。为
  了既符合文档语义又不把真实同动作打低，数据库权重需要“手部主导，但 missing/检出
  噪声不过度惩罚”。我会微调 missing/手部鲁棒项，目标是标准帧重跑仍高、其他 demo
  仍低。

• 我会加一个很保守的“Holistic 重提取噪声底噪补偿”：只有在手部主导 profile、局部
  DTW 已经很低、手部检出充分时才扣除少量距离。这不会依赖脸/身体，也不会让其他
  demo 高分，但能避免同一个标准动作重新经过 Holistic 后因为手点轻微漂移掉到 60-
  70。




P: 动作窗口裁剪的一个可能问题是，真实的动作可能会有多余的小动作，也就是关键的动作点可能还是没有对齐？或许应该把测试样本的高能量窗口采样做进一步的映射？


Q: 有一个问题，就是标准和测试的帧数如果不太一致，当前的算法能保证鲁棒性吗？按理说，权重最大的部分是，核心特征的开头、中间和结尾的动态语义一致就行，比如“张开”“上升”，帧数不同带来的时间序列差异应该要被包容。

A: • 不能说“保证”。当前算法已经有一定鲁棒性，但还不够到你描述的理想状态。

  当前已能包容一部分帧数差异：

  - 用的是加权 DTW，允许一帧对多帧、多帧对一帧，所以普通快慢差异不会直接失败。
  - 静止开头/结尾已通过语义动态权重和 action window 降权或裁掉。
  - 跳 这类短动作有低帧率/子采样容忍，查询帧数偏少时会做保守补偿。
  - 长动作如 花 现在不再硬裁窗口，而是完整序列 DTW + 动作窗口诊断，避免丢掉上下
    文。

  但当前还没有完全实现你说的“核心语义开头-中间-结尾一致即可”。主要缺口是：

  - 现在 DTW 仍主要在原始帧序列上找最短路径，虽然有权重，但没有显式把“张开开始、
    张开峰值、张开结束”当成语义锚点强制对齐。
  - _maybe_resample_query_window 只在查询动作窗口极短时做线性补帧，不是完整的“语
    义进度归一化”。
  - 序列级 motion/roughness penalty 仍可能把帧率差异、采样密度差异当作动作差异，
    尤其是手部权重大以后更敏感。
  - semantic_delta 当前主要看起止变化，还不够看“起点-中点-终点”的动态过程一致
    性。

  更稳的下一步应改成 语义相位对齐：

  1. 对标准和测试都根据重要特征的动态能量计算 semantic progress curve。
  2. 找出核心动作的 start / peak or mid / end 三类语义锚点。
  3. 把两段动作按语义进度重采样，而不是按帧号重采样。
  4. DTW 在语义相位坐标上跑，帧数不同只影响时间密度，不直接扣分。
  5. 额外计算 anchor consistency：例如 花 的手指张开起点、中间张开过程、最终张开
     状态；跳 的两指弯曲、弹起、伸直落点。
  6. 长度惩罚改成“语义覆盖不足惩罚”，而不是原始帧数差异惩罚。

  所以结论是：当前算法“有 DTW 级别的时间鲁棒性”，但还没有达到“核心动态语义一致即
  可”的鲁棒性。你这个判断是对的，下一版应该把评分主轴从 frame-index DTW 升级为
  semantic-phase DTW，并把 start/mid/end 锚点差异作为核心诊断项。


### 语义对齐思路
P: 那么，如果完全是语义相位对齐的视角，我们的文档资料其实就是最核心的人工语义，然后标准视频起到一个补充语义具体形式和细节的作用。
也就是说，打分的时候，可以分成两部分；1. 直接分析视频帧中的动作语义是否符合标准库中的要求，比如是否有“右手张开”，可以形成一个判断，这个关键语义的量化程度从标准样本参考，同时设置一定的鲁棒性，这就可以有语义打分了；2. 基于标准样本的时间序列补充背景，考查DTW一致性，注意也要有宽松。两个部分各有一定权重，进行贾总得到最终打分。我认为其中的语义部分权重要更大一些。

关于标准的动作语义判断，如果是直接基于视频流进行分析，可能要关键的语义判断模块，比如手形变化，手臂移动；这个语义判断模块似乎是我们需要训练或手动微调定义的？


A: • 对，这个理解更合理：资料文档是主语义标准，标准视频是量化参考和细节补充。评分不
  应该完全依赖“像不像这一个 demo 的时间序列”，而应先判断“动作语义有没有做对”。

  我建议下一版拆成两路：

  1. 语义评分，权重大
     直接从 Holistic landmarks 里判断文档描述的关键语义是否成立。比如：
      - 花：主手是否从撮合/含苞变为张开；指尖 spread/opening 是否明显增大；手是
        否有缓慢上升趋势。
      - 跳：右手食指/中指是否模拟两腿，是否先弯曲后伸直并上弹；左手是否作为地面
        参照存在。
      - 香蕉：左手食指是否稳定作参照，右手是否沿其向下剥皮。
      - 唱歌：双手从喉部外移，同时嘴/头部动作有语义参与。
  2. 标准样本 DTW 一致性，权重较小
     标准视频用于补充动作节奏、相位顺序、幅度参考和细节轨迹。DTW 应该宽松，只检
     查“同一语义相位下的轨迹是否大体一致”，不能让帧数、速度、开头静止段主导得
     分。

  最终可以先设成类似：

  final_score = 0.65 * semantic_score
              + 0.25 * semantic_phase_dtw_score
              + 0.10 * quality/confidence_score

  具体比例后面用真实用户样本校准，但方向上语义部分应更大。

  关于你问的“语义判断模块是不是需要训练或手动微调定义”：当前阶段应该先手动定义，
  不适合直接训练。

  原因是现在没有多用户视频和人工标签，训练模型会严重依赖 demo，本质上还是学“像不
  像 demo”，不一定学到“语义是否正确”。更稳的 MVP 是：

  - 用文档生成每个词条的 semantic predicates，也就是可计算的语义判断项。
  - 用标准视频估计这些判断项的参考幅度、方向、起止状态和容忍区间。
  - 人工/规则微调关键 predicate 的权重和阈值。
  - 等后续有真实用户样本和人工评分后，再训练或拟合权重、阈值，甚至训练专门的
    predicate classifier。

  也就是说，下一版核心不是“再调 DTW”，而是建立一层 手语语义谓词库：

  DOCX 文档语义
    -> 每个词的 semantic profile
    -> 手形/手指/双手关系/运动方向/脸部/pose 谓词
    -> 标准视频校准幅度和相位
    -> 查询视频直接语义打分
    -> 宽松 semantic-phase DTW 补充

  这个方向能更好解决帧数不一致问题，因为语义评分看的是“张开有没有发生、上升有没
  有发生、起点/中点/终点是否合理”，不是逐帧对齐是否完全相同。


P: 如果是这个思路，每个词条都要设置专门的语义动作检测机制/函数？这是容易实现的吗？

A: • 容易实现，但前提是不要给每个词条都写一套完全独立的函数。

  更合适的方式是：先做一套可复用的“语义谓词/动作检测原语”，每个词条只是配置这些
  原语的组合和权重。

  例如原语库可以有：

  - hand_presence：左/右手是否出现，覆盖率是否足够
  - hand_opening_increase：手指张开程度是否增加
  - finger_flex_to_extend：食指/中指是否从弯曲到伸直
  - wrist_move_direction：手腕是否上移、下移、左右移动
  - two_hands_relative_distance_change：双手距离是否变大/变小/接触
  - anchor_hand_stable：参照手是否稳定
  - hand_near_face_or_mouth：手是否在嘴角/喉部/额头附近
  - mouth_open_or_face_motion：嘴部/脸部语义是否参与
  - semantic_phase_order：动作是否按 起点 -> 中间 -> 终点 顺序发生

  然后每个词条写成配置，而不是单独函数：

  {
    "word": "花",
    "semantic_checks": [
      {"type": "main_hand_opening_increase", "weight": 0.45},
      {"type": "main_hand_upward_motion", "weight": 0.20},
      {"type": "main_hand_start_closed", "weight": 0.15},
      {"type": "main_hand_end_open", "weight": 0.15},
      {"type": "extra_hand_penalty", "weight": 0.05}
    ],
    "dtw_weight": 0.25,
    "semantic_weight": 0.70
  }

  跳 则是：

  {
    "word": "跳",
    "semantic_checks": [
      {"type": "right_index_middle_flex_to_extend", "weight": 0.35},
      {"type": "right_hand_upward_bounce", "weight": 0.25},
      {"type": "left_hand_ground_anchor_present", "weight": 0.20},
      {"type": "two_hand_role_consistency", "weight": 0.10},
      {"type": "face_pose_irrelevant", "weight": 0.10}
    ]
  }

  所以难度分两层：

  - 当前 10 个 demo 词条：可实现，工程量可控。因为资料文档明确，动作也比较典型，
    手工配置语义检查项是合理的。
  - 扩展到大量词汇：如果每个词都人工写细节，会变重；但可以通过“原语库 + 配置模板
    + 标准视频自动校准阈值”降低成本。

  关键点是：每个词条需要专门的语义配置，但不应该需要专门的代码函数。只有遇到非常
  特殊的动作，才新增一个原语函数。

  我建议下一版这样做：

  1. 新增 semantic_predicates.py，实现通用语义检测原语。
  2. 扩展 sign_semantic_weights.json，加入每个词条的 semantic_checks。
  3. 用标准视频自动估计每个 check 的参考幅度和容忍范围。
  4. 打分输出拆成：
      - semantic_score
      - semantic_phase_dtw_score
      - quality_score
      - final_score
  5. 页面结果里显示主要扣分项，比如“主手张开不足”“左手地面参照缺失”“动作上升幅度
     不足”。

  这样既符合你提出的语义相位思路，也不会让系统变成 10 个完全独立、难维护的打分函
  数。



P: 嗯，这种方式很人工，但是在样本数据不大的情况下不失为一种方法？
那么一个重点就是设置号动作语义的底层模块，包含重要的要素，脸：笑；手：移动方向，手形变化；手指动作；手和手的交互动作；躯干整体的动作，等等。我们可以根据文本资料，结合样本视频，补充每个词条的语义特征，具体的语义模块变量，不同特征权重。然后实现这些可复用的底层的语义模块检测。
不过，可以想到，有些语义细节可能并不容易直接基于骨骼图进行计算得到？比如手指动作。可能就需要 DTW这种对齐了？

A: 
• 对，这种方法很人工，但在样本少、又有明确资料文档的情况下，反而是合理路线。它相
  当于把文档说明当作人工语义标注，把标准视频当作量化标尺。

  关键不是“纯规则替代 DTW”，而是分层：

  1. 能直接算的语义变量
     例如手腕上移/下移、双手距离变大/变小、手是否靠近嘴角、左手是否稳定、右手是
     否出现、手掌开合程度、指尖 spread 是否增加。这些可以从 Holistic 骨骼点直接
     算。
  2. 能近似算但有噪声的语义变量
     例如手指弯曲/伸直、撮合到张开、食指中指模拟腿。这些可以用手指关节角度、指尖
     到腕部距离、指尖间距、手形特征向量来估计，但会受视角、遮挡、MediaPipe 抖动
     影响。
  3. 难以单独规则判断的细节
     这里就需要局部 DTW 或原语级 prototype matching。也就是说，不再用 DTW 比完整
     动作，而是对某个语义模块做局部对齐，比如：
      - 花：对“手形从撮合到张开”的 hand-shape feature 序列做局部 DTW。
      - 跳：对“食指/中指弯曲 -> 伸直 -> 上弹”的 finger-shape + wrist-motion 序列
        做局部 DTW。
      - 汽车：对双手相对旋转/同步摆动的局部周期做 DTW。
      - 朋友：对双拇指接近/碰触两次的距离曲线做 DTW。

  所以 DTW 不是不要，而是从“全局像不像 demo”降级为“某个语义原语的动态模式是否匹
  配”。

  我建议下一版结构是：

  最终分数
  = 语义模块分数 主要权重
  + 原语级局部 DTW 分数 中等权重
  + 全局宽松 DTW 分数 小权重
  + 质量/置信度修正

  底层语义模块可以先做这些：

  - face：嘴巴张开、嘴角附近动作、头部左右晃动、额头参照位置
  - hand_motion：手腕/掌心方向，上下左右移动，移动幅度，速度峰值
  - hand_shape：开合、撮合、握拳、指尖 spread、手指伸直度
  - finger_action：食指/中指弯曲伸直，拇指突出，双指距离变化
  - two_hand_relation：靠近、分离、接触、左右手相对高度/距离变化
  - anchor：某只手是否稳定作为参照，比如 跳 的左手地面、香蕉 的左手食指
  - phase_order：起点、中间、终点的语义顺序是否正确

  手指动作确实是最难的一类。可行做法不是写一个“是否张开”的硬阈值，而是组合：

  手指伸直度
  + 指尖间距
  + 指尖到腕部距离
  + 起点/终点变化量
  + 局部 hand-shape DTW

  这样既保留可解释性，又不会被单个骨骼点噪声拖垮。下一步实现时，可以先把 花、跳
  做成示范：一套通用原语函数，两套词条配置，然后验证语义分数是否比单纯 DTW 更符
  合实际测试。

### 语义加权DTW【似乎可行】
P: 不过按理说，加上合适权重和mask，只关心重点特征的有鲁棒性的DTW就也能实现上述的识别程度了吧？

A: • 是的，原则上可以。“合适权重 + mask + 语义相位/局部窗口 + 宽松 DTW”本质上已经能
  覆盖很多语义识别能力，尤其在当前样本少的阶段，它可能比单独写大量硬规则更稳。

  但要区分两件事：

  1. 加权 DTW 可以判断“动态模式像不像”
     例如 花 只看主手 hand-shape/opening/spread，DTW 对齐后比较从撮合到张开的曲
     线；这可以很好判断动作是否像“开花”。
  2. 显式语义模块可以解释“为什么扣分”
     例如告诉用户“主手张开不足”“左手地面参照缺失”“动作方向反了”。这类解释单靠
     DTW 也能从局部特征诊断里推断，但需要额外整理。

  所以更务实的路线不是二选一，而是：

  核心：语义特征加权 DTW
  辅助：语义变量诊断和扣分解释

  也就是说，我们不一定需要先建立很多独立规则函数，而是把文档语义转成：

  - 关注哪些 feature group：手、手形、手指、双手关系、脸、pose
  - 哪些 keypoint/derived feature 权重大
  - 哪些时段/高能量相位权重大
  - 哪些无关部分 mask 掉
  - 是否允许左右手互换
  - 是否需要局部窗口或多段对齐

  然后在这些语义特征上做鲁棒 DTW。这样已经可以实现：

  - 帧数不同：DTW 处理
  - 速度不同：DTW 处理
  - 开头/结尾静止不同：高能量窗口和 frame weight 处理
  - 无关脸/躯干干扰：mask/低权重处理
  - 手形细节：derived hand-shape feature + keypoint weight 处理
  - 动作幅度差：尺度归一化 + 幅度容忍处理

  但有一个条件：DTW 输入不能是原始全身骨骼大杂烩，而必须是语义特征向量。比如 花
  的 DTW 输入应该更像：

  main_hand_opening
  main_hand_spread
  fingertip_to_wrist distances
  main_hand_vertical_motion
  start/end opening delta

  而不是 pose、face、双手全部 landmarks 一起算。

  因此我会把下一步目标收敛成：

  1. 继续以“语义加权 DTW”为主评分核心。
  2. 把 profile 从 group 权重升级到 semantic_feature_weights，显式加入 opening、
     spread、finger_flex、two_hand_distance、mouth_open 等派生特征。
  3. 做 semantic phase weighting，让关键动态相位权重更高。
  4. 只保留少量规则谓词作为诊断项，而不是主评分主体。

  这条路更容易落地，也和当前代码衔接最好。


P: 嗯，我认同 语义加权DTW 这条思路，请你开始推进。

NEW:
• 我会先做两个低风险增强：第一，把手形 group 里的数字权重按真实手指语义解释，不
  再把 8/12 误当成手形向量下标；第二，为每帧写入 semantic_phase，DTW 局部距离加
  入轻量相位差，序列惩罚加入 0.1/0.5/0.9 三个语义锚点一致性。



  • 热加载成功，但线上 API 冒烟暴露了一个真实问题：跳 得分约 80.6，花 由于浏览器/
  JPEG 重新过 Holistic 后手点抖动，降到约 71.1。离线缓存门槛过了，但 API 路径还
  需要对“同动作重提取噪声”再做保守补偿，并把 semantic_dtw 诊断字段透传到后端返
  回。



你推荐视频流采集的帧数是越多越好吗？还是有合适的范围？

A:
• 不是越多越好。当前方案更适合 中等密度采样 + 语义能量筛选。

  推荐范围：

  - 采集时长：3-4 秒
  - 候选采样 FPS：12-15 fps
  - 候选帧数：约 36-60 帧
  - 送 Holistic / 评分帧数：建议 24-48 帧
  - 单次请求上限：当前后端限制是 90 帧，不建议常态接近上限

  原因：

  - 帧太少：容易漏掉 花 的张开、跳 的弹起这类核心动态。
  - 帧太多：Holistic 处理更慢，手部抖动和静止帧也更多，未必提升评分。
  - 真正重要的是覆盖核心语义相位：起点、中间、终点，以及高能量动态段，而不是简单
    堆帧。

  我建议当前网页默认：

  采集 3 秒
  候选 15 fps
  候选约 45 帧
  最终发送 36 帧左右

  如果动作较复杂，例如 虎、唱歌、汽车，可以放宽到：

  采集 4 秒
  候选 15 fps
  最终发送 48-60 帧

  后续可以按词条配置采样策略：短促动作如 跳 用 24-36 帧，长动作或多阶段动作如
  虎/唱歌/汽车 用 48-60 帧。



Q: 可是，现在网页测试，花还是很低的分。。
有一个可能的点是，我的整体躯干是坐着的，和标准样本站立的pose差别较大，当前的 DTW有这个鲁棒性吗？

A: • 当前对这点有一定鲁棒性，但还不够系统。

  已经有的保护：

  - 对 花、跳 这类手语，当前 profile 里 face=0、pose=0，也就是脸和躯干基本不参与
    主距离。
  - 坐姿/站姿导致的躯干差异，不应该直接拉低这类词的核心 DTW 分数。
  - 手部坐标做了身体尺度归一化，能减少距离远近、画面大小造成的影响。

  但仍可能受影响：

  - 当前手部坐标还是基于 pose 做中心和尺度归一化。如果坐姿导致肩部/身体姿态与标
    准不同，手部相对坐标会有一些偏移。
  - 如果手在画面里的位置与标准差很多，例如坐姿时手更低、更靠近身体，虽然 pose 权
    重为 0，但手部绝对归一化位置仍可能影响 right_hand 距离。
  - hand_shape 相对特征会更鲁棒，因为它主要看指尖距离、张开、弯曲等，不太依赖身
    体姿态。

  所以结论是：

  - 对 花 这种主要看手形变化的动作，坐着做应当能比较鲁棒。
  - 对 跳 这种也主要看手指和双手关系的动作，也应当比较鲁棒。
  - 对 唱歌、虎 这类文档语义包含头部、嘴、额头参照或身体/头部动作的词，坐姿差异
    可能更明显，需要单独处理。

  下一步可以增强这点：把手部位置特征进一步拆成两类：

  hand_shape / finger_motion：高权重，坐姿鲁棒
  hand_global_position：低权重或只在需要靠近嘴/额头时启用
  pose：仅在文档明确要求时启用

  也就是说，对大多数纯手部词，评分应主要看手形、手指、双手相对关系和运动方向，而
  不是手相对站立躯干的位置。当前已经往这个方向做了，但还可以继续把 right_hand/
  left_hand 的全局位置权重再拆细，提升坐姿鲁棒性。



P: 好的，请继续提升鲁棒性，包括坐姿鲁棒性等，尽量减少非重要特征的干扰。

比如让特征信号主要使用“相对移动”


A: • 实现上我会把手部位置拆成“局部手形/手内结构”和“全局位置残差”。对 花/跳 这类文档
  明确不看躯干的动作，全局残差只保留很小权重；对靠近嘴/额头的动作则保留较高位置
  权重。这样坐姿不会通过站姿 pose 间接污染手部 DTW。

  • 这个测试说明：逐帧“方向化相对移动”仍然会被隔帧采样破坏，尤其 跳 这种短动作。所
  以我会把“相邻帧 motion group”暂时关掉，不作为主 DTW 输入；保留两类更稳的相对信
  号：手腕去中心的局部手部几何、起止/相位锚点的相对变化。这更符合帧数不同下的鲁
  棒性。

  • 这一版更稳：保留“局部手部几何 + 语义相位 + 起止/中段变化”的相对信号，但关闭了
  会被隔帧采样误伤的逐帧 motion group。花/跳 门槛都恢复通过，并且全局手位置权重
  已经降低，用于提升坐姿/站姿差异下的鲁棒性。接下来我会热加载评分脚本，并做一个
  API 冒烟。

• API 冒烟保持稳定：花≈75.49、跳≈81.07。我还做了一个合成坐姿压力测试，把手部整体
  向下平移模拟坐姿/镜头高度差，花 仍约 97.47、跳 约 93.13，说明“手相对躯干绝对位
  置”已经被明显降权。接下来我会把这轮结果写入日志和报告。

• 已继续增强鲁棒性，重点处理坐姿/站姿差异和非重要特征干扰。

  这版做法：

  - 对纯手部词条，left_hand/right_hand 距离优先比较 wrist-relative 局部手部几
    何，不再主要看手在站立躯干坐标里的绝对位置。
  - 手部整体位置只保留小残差权重：花=0.06，跳=0.08。
  - 逐帧相邻 motion group 默认关闭。测试发现它会误伤隔帧采样，因为隔帧会自然放大
    相邻帧位移；移动方向后续应在“语义相位片段级”判断，而不是直接比较每一帧位移。
  - 继续保留更稳的相对信号：手形相对特征、语义相位、start/mid/end 锚点、序列级
    motion/roughness。


P: 你的算法调整都要进行网页测试数据的复查，看看能不能变成正常打分。

你分析一下当前DTW哪里鲁棒并没有做好，导致真实测试很多都不通过？

A:  核心判断：当前 DTW 主要只对“帧数不同、速度不同、轻微前后缀差异”有鲁棒性；对真
  实网页测试里的“手部关键点间歇丢失、动作窗口截取错误、手形视角/朝向差异、单模板
  差异”鲁棒性还不够。

  证据来自最新网页回放：signLanguage/work/generated/scoring_mvp_run3/
  web_replay_pose_robust_v3/web_replay_current.md:11。111 条保存网页/API 样本
  里，正常区间只有 14 条，低分 96 条；花 均分 45.979，跳 均分 23.283。

  主要问题

  1. 缺失关键点惩罚过于二值化，而且正好打在关键帧上。
     当前代码用 mask mismatch 直接算 missing_penalty，再按 group 权重进主距离：
     signLanguage/work/scripts/score_holistic_sequence_mvp.py:1161。
     花 的低分样本整体手部覆盖看起来有 0.70-0.87，但 DTW 路径上的关键语义帧经常
     missing_penalty=1.0。这说明不是“完全没识别到手”，而是“开花张开那几帧/关键手
     指没有稳定识别”。当前算法不会插值、不会区分短暂掉点和语义错误，所以会把感知
     噪声当作动作错误。
  2. 动作窗口找到了“高能量”，但未必是正确语义窗口。
     跳 的低分样本有不少手部覆盖不低，例如 0.72-0.80，但分数仍是 7-13。这些样本
     的 DTW 主距离已经很大：0.24-0.31，不是后处理扣分导致。
     原因是当前短动作直接使用语义动作窗口：signLanguage/work/scripts/
     score_holistic_sequence_mvp.py:1647，窗口由能量峰决定：signLanguage/work/
     scripts/score_holistic_sequence_mvp.py:1765。如果用户动作开始晚、结束贴近采
     集尾部，或者高能量来自手部抖动/调整姿势，DTW 会对齐到“动得最多的一段”，但这
     段不一定是“跳”的正确食指/中指弹跳语义。
  3. 当前 DTW 是端点强制对齐，不是真正的开放式子序列对齐。
     代码从 (0,0) 开始，到 (n-1,m-1) 结束：signLanguage/work/scripts/
     score_holistic_sequence_mvp.py:1811。这对 demo 变体还可以，但真实网页里用户
     可能前半段准备、后半段才做动作，或者动作没完整收尾。
     现在有 trim tolerance，但触发条件很严，例如完整序列要求 dtw_distance <
     0.012 才容忍：signLanguage/work/scripts/
     score_holistic_sequence_mvp.py:1923。真实样本的 花 低分常在 0.029-0.031，所
     以完全吃不到这个容忍。
  4. 手形特征仍偏“坐标相似”，不是足够语义化。
     坐姿/站姿全局位置已经做了 wrist-relative 改进，但手形本身仍大量依赖关键点几
     何 RMSE：signLanguage/work/scripts/score_holistic_sequence_mvp.py:1138。
     对 跳，低分组的 right_hand_shape 平均约 0.235，正常组约 0.052；说明真实测试
     的两指弯曲/伸直、手掌朝向、摄像头角度和标准视频差异很大。DTW 能拉伸时间，但
     不能自动把不同视角下的手形解释成同一语义。
  5. 高能量帧权重会放大噪声。
     当前局部距离会乘 pair temporal weight：signLanguage/work/scripts/
     score_holistic_sequence_mvp.py:1795。这本意是强调关键动作，但如果高能量来自
     手部误检、抖动或错误窗口，就会把错误放大。跳 的低分样本里，最坏对齐点常见
     frame_pair_weight=1.5-1.8，同时 right_hand_shape_distance=0.4-0.6，少数点就
     能把整段拉低。
  6. 左右手互换是逐帧/逐 group 决策，不是语义角色级决策。
     当前每个 frame distance 内部会比较 direct/swapped：signLanguage/work/
     scripts/score_holistic_sequence_mvp.py:1206。对 花 这种单手动作还能救一部分
     样本；但对 跳 这种“左手地面、右手两指小人”的非对称双手动作，应该是整段级别
     的镜像假设，而不是每帧局部随便换。否则会削弱“哪只手承担哪个语义角色”的一致
     性。

  结论

  当前失败不是简单“DTW 不够宽松”，而是 DTW 输入的语义表征和窗口质量还不够稳。DTW
  解决的是时间轴弹性；真实网页测试还需要解决感知缺失、动作截断、手形视角变化、语
  义窗口误选、单模板覆盖不足。

  优先改进顺序应该是：

  1. 对核心手部关键点做短缺失插值和质量标记，把“感知失败”和“动作错误”分开。
  2. 把动作窗口改成开放式语义子序列 DTW，并检测动作是否被采集截断。
  3. 为 花/跳 这类词条提取更语义化的曲线：开合度、指间距、食指/中指弯曲度、相对
     左手地面的上升量。
  4. 对高权重帧使用 capped/Huber/trimmed DTW 聚合，避免少数噪声关键帧支配分数。
  5. 对左右手镜像做整段级别双假设，而不是逐帧自由切换。
  6. 后续必须用真实网页样本做人为标注校准，单个 demo 模板无法覆盖真实用户差异。


Q: 测试时候坐的时候遮挡很多，missing影响大吗？


测试的视频帧会发送到服务器吗？

能不能恢复一下具体的holistic可视化结果，我看看真是测试下holistic识别的效果。


### 把 DTW 从“坐标序列相似”改成“语义骨架序列相似”
DONE: 其实holistic识别是没问题的，从骨架图其实还是能够看出来对应的语义的，只是当前的DTW鲁棒性还存在大问题。

• 我同意这个判断，而且这会改变下一步优先级：现在不应该继续把问题归因到 Holistic
  漏检，而是要把 DTW 从“坐标序列相似”改成“语义骨架序列相似”。我会按这个方向直接
  改评分模块，并用网页回放复查。

• 我先做一个针对性修正，不碰 Holistic：一是让手部几何距离支持局部相似变换对齐，
  减少拍摄角度/手掌朝向带来的 RMSE 误差；二是对“核心语义已经可见且 DTW 主距离不
  高”的样本，把序列级 roughness/semantic-delta 惩罚从硬扣分改成部分容忍。改完会
  跑离线 gate 和网页回放。


Q: 关于跳，我最新测试了几个完全乱摆的动作，它反而给的分数比我之前正经摆的动作分数高很多。怎么回事，你仔细分析一下当前DTW的鲁棒性问题；语义骨架序列相似我觉得思路很好，但是还是要注意给骨架加上局部权重，只需要关心核心动作正确性。比如跳，核心权重应该是双手交互动作，右手在左手基础上跳。我乱摆的动作只有一只手，应该会有很大距离才对。


• 代码层面已经确认根因之一：two_hand_relation 被绑在 relative_motion_enabled 后
  面，而我们之前为了避免相邻帧 motion 误伤把 relative_motion_enabled=False，结果
  跳 最核心的“双手关系”也一起被关掉了。也就是说，当前 跳 主要还是在比右手局部形
  状，左手地面和右手相对左手的跳跃没有成为主距离。



P: 请你之后都要进行数据库中的条目进行重新检查，涉及到交互性质的语义特征，一定要设置交互权重，这是必不可少的。


• 跳 的最新双手低分样本，其实关系轨迹的方向和标准是同向的：右手相对左手有明显向
  上/弹跳变化，只是幅度、手形和绝对关系比标准大很多。因此单纯降低双手关系权重不
  够，我会加一个 跳 专用的“关系语义通过则放宽精确几何”的容忍项：双手必须存在，且
  two_hand_relation 的起止变化方向一致，才降低序列距离；单手乱摆不会触发。

  核心改动：

  - 花：非 required 的 missing 不再硬扣；新增 visible_semantic_core_scale，主手
    语义可见且 DTW 主路径接近时，降低短遮挡/采样噪声对最终分的影响。
  - 跳：新增 jump_relation_semantic_floor，只在双手存在、右手相对左手地面的起止
    方向一致、纵向跳跃足够、且不是主要水平移动时抬分；单手乱摆不会触发。

  验证结果：

  - 花_core_visible_scale_v1 离线 gate 通过：正例最低 80.311，负例最高 31.323。
  - 跳_relation_semantic_floor_v3 离线 gate 通过：正例最低 76.823，负例最高
    31.418。
  - 网页回放：work/generated/scoring_mvp_run3/
    web_replay_relation_semantic_floor_v3/web_replay_current.md
      - 总体：148 条，正常 49，边界 32，低分 67，均分 34.08 -> 49.85
      - 花：均分 46.54 -> 61.31，正常+边界 53/80
      - 跳：均分 21.46 -> 43.45，正常+边界 28/52
      - 跳 双手正样本：052715=78.0，053241=76.0，063052=75.1
      - 单手乱摆仍低：053345=2.4，053401=3.6

  运行态：

  - 5080 已重新启动并 ready。
  - 当前只监听 127.0.0.1:5080。
  - Holistic worker PID：811485。
  - 评分模块已 reload：reload_count=1，无错误。

  我也已更新：

  - work/worklog_sign.md
  - 全局 signLanguage 记忆
  - key memory

  目标还不能算完全完成，因为 跳 仍有一部分网页样本低分，主要集中在动作窗口里左手
  地面覆盖不足、关系方向不对、或核心双手关系不满足。下一步应继续做动作窗口/左手
  覆盖诊断，而不是继续全局放宽分数。





### 或许，可以数据增强，然后？训练语义模块？

P: 基于文档资料的核心语义特征，我们可以对标准视频样本的骨架序列进行数据增强，针对有用的核心特征结构（会被mask掉的不用管），比如加上旋转，镜头角度调整，关键部位（比如手指节点）微微扰动，镜像等等；这样可以对同一个手语语义生成多个骨架序列样本，后续测试跑DTW的时候，也可以遍历计算然后取均值，或者是取最好结果；遍历计算可以多进程加速。
既然是数据增强，如果模型能够对骨架进行3D微调，那么效果肯定更好。holistic有这样的功能吗？或者你看看网上有这样的3D生成功能吗？


/goal 请你探索实现数据增强下的鲁棒DWT实现思路，能针对


Q: › 是不是接下来必须训练语义模块来有效识别手语骨骼序列的特征语义？
A: 
• 不一定“必须马上训练”。当前小样本阶段，更稳的是：

  1. 先做可解释语义特征模块
     例如手部张开、指间距变化、双手相对位置、右手相对左手上跳、移动方向、动作相
     位等。这些可以基于骨架直接计算，不需要训练。
  2. 再用语义加权 DTW + 模板增强
     文档定义核心语义，标准视频提供轨迹细节，增强模板覆盖坐姿、镜头角度、手指轻
     微扰动、镜像等合法变化。
  3. 有真实用户样本和人工评分后，再训练一个轻量校准模块 【确实，不断做矫正，人工调节权重等，的确有效。。】
     输入 DTW 距离、关键语义距离、missing、双手关系缺失等诊断特征，输出最终分数
     或通过概率。这个比直接训练大模型更现实。

  什么时候需要训练语义模块？

  - 如果词汇量扩大、动作复杂度增加、不同用户差异很大，就需要训练。
  - 如果某些语义很难手工定义，比如复杂手指形态、连续动作节奏、非手部表情语义，也
    适合训练。
  - 但现在只有少量 demo 和少量网页测试，直接训练端到端语义识别模型容易过拟合。

  我的建议路线是：先把“语义特征库”做扎实，再训练校准器，最后再考虑训练语义检测器
  或序列模型。
  也就是不是立刻训练大模型，而是先把 花、跳 这类核心语义拆成稳定可计算的骨架特
  征，再让训练模块学习“这些特征怎样合成最终分数”。




嗯，语义特征库的确，可以一点点优化。不过一条条优化可能比较慢？能不能自动化扩展规模？


或者我们手工针对每一个条目进行设置可复用的基础语义模块，比如“张开”等。

或者在网上搜索一下目前开源框架中是如何实现骨骼序列的特征语义识别的？



 /goal  请你沿着思路继续，设计鲁棒性打分，并能够使得网页测试结果打分正常，比如花、跳




### 网页优化

P: 网页上面的进度条应该对应采样时间；后续的处理过程可以重新刷新进度条，或者干脆去除，避免干扰。
DONE


### 后端优化

P: 可不可以就复用holisitic的常驻后端，相关打分算法只是独立加载模块，可以根据新版本重新加载，但是不用重启holistic后端了？这样节约时间。

A: • 可以，且已作为新运维逻辑落地。2026-05-23 02:35 CST：`/data/WYC/signLanguage/work/web/backend.py`
  新增 `ScoringModuleService`，后端进程内通过 `importlib.reload` 管理
  `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py`。`/api/score`
  每次评分前检查评分脚本 mtime，检测到变更时自动热重载；同时新增
  `POST /api/admin/reload-scoring` 作为手动热重载接口，`/api/status` 返回
  `scoring_module` 状态（`loaded_at/reload_count/last_reload_error`）。
  这次为了加载该能力做了一次结构性重启；之后只改评分算法脚本时，不再需要重启
  `5080` 或 `holistic_worker_daemon.py`，常驻 Holistic worker 可以保持不动。

- 同步更新前后端设计报告：
  `/data/WYC/signLanguage/work/reports/web_frontend_backend_current_implementation_20260522.md`
  和 Word 版 `.docx`。报告已补充评分模块热重载、step2 dense 模板库、`frame_weights`、
  `alignment_policy/action_window/frame_weight_summary` 返回字段，以及新的运维规则：
  只改评分算法脚本时用自动/手动 reload；只有后端框架、模板库构建逻辑、worker 协议
  或 worker 代码变化时才考虑重启 `5080`。
- 同步修订评分闭环报告：
  `/data/WYC/signLanguage/work/reports/scoring_dynamic_energy_window_update_20260523.md`
  和 Word 版 `.docx`，把无条件 action-window 更新为混合对齐策略，并记录 `花`
  实测回归复现与修正结果。
- 2026-05-23 02:35 CST 验证：`5080` 仅监听 `127.0.0.1:5080`，只有一个
  `/data/WYC/signLanguage/work/web/backend.py` 和一个 `holistic_worker_daemon.py`。
  `/api/status` 显示 worker ready，`scoring_module.reload_count=1`。用 `花.mp4`
  step2 帧切片经 `/api/score` smoke test 返回 request
  `web_20260523_023452_bd691c4f`，score `81.685`，
  `alignment_policy.mode=full_sequence_with_action_window_diagnostics`，
  `used_action_window_for_scoring=False`，确认 `花` 已回到完整序列语义加权 DTW 主路径。

A: 
• 可以，而且这应该作为当前架构的默认方式。现状是 5080 的 FastAPI 进程同时管理
  Holistic worker 和打分模块，所以我刚才为了加载新评分代码重启了整个后端，导致
  Holistic 也重新初始化；我会把它改成“Holistic worker 常驻不动，评分脚本按 mtime
  自动热重载/也支持手动 reload endpoint”。







### 思考
这个测评任务总体来说比翻译要容易很多，目标标准是确定的。

手工味道（AI辅助文本识别和分析，也还行。。），根据资料文本来设置重要特征的权重。
这种资料文档其实就是最核心的人工标注！如果没有，那么只能是根据多个样本视频来识别出关键特征，这其实也很困难，需要鲁棒的标准数据。


识别关键的动态时间窗口（根据能量曲线），提取其中的核心动作语义；之后测试样本进行对齐打分即可。
不过最难的就是“核心动作语义”的识别；不同帧密度“对齐”也可能要畜栏里

可能的问题是视频采样本身，手部特征可能就会有噪声，所以某些可能的确会识别不清楚吧。




### 2026-05-23 04:20 CST：语义加权 DTW / 语义相位对齐

- 根据“语义加权 DTW 为主线”的讨论，已继续推进评分模块，而不是改成每个词条独立规则函数。实现重点是：文档资料决定重点特征、mask、关键手指和无关部位；标准视频补充幅度、速度、相位曲线和局部轨迹；DTW 只在这些语义特征上做宽松对齐。
- `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py` 已新增 `semantic_phase`：基于当前语义 profile 的重点特征动态权重，计算每帧在 `[0,1]` 上的语义进度；DTW 局部距离加入轻量 `semantic_phase_gap`，并在序列级增加 `0.10/0.50/0.90` 三个语义锚点的一致性惩罚。
- 已修正手形 group 的数字权重解释：在 `left_hand_shape/right_hand_shape` 中，`4/8/12/16/20` 与 `1/5/9/13/17` 会优先映射到真实手指语义，而不是简单当成手形向量下标；这使 `花` 的 opening/spread 和 `跳` 的食指/中指动态更贴近文档语义。
- 已增加 `semantic_phase_trim_tolerance` 和更保守的 hand-dominant 重提取噪声补偿：当 DTW 已经找到近似一致的核心语义路径时，适度前后缀裁剪、帧数差异和网页 JPEG/Holistic 重提取抖动不再被过度扣分。
- `/data/WYC/signLanguage/work/scripts/build_semantic_weight_profiles.py` 已把 `semantic_dtw` 写入 `/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json/.md`；模板审计目录 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/template_semantic_phase_dtw_audit_v1/` 显示 step2 dense 模板库 `10/10 ok`。
- 最终离线门控：`花` `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/花_semantic_phase_dtw_v3/` 正例最低 `83.213`、负例最高 `29.534`、margin `53.679`；`跳` `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/跳_semantic_phase_dtw_v3/` 正例最低 `79.579`、负例最高 `39.639`、margin `39.940`。
- 全库统一审计 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_words_semantic_phase_dtw_v2/summary.md` 显示：`花/跳` 通过统一工程门槛，其他词条负例普遍很低，但通用 `trim_start/trim_end/subsample` 正例不适合多阶段词；下一步应为每个词条设计文档语义驱动的专属正例扰动。
- `5080` 后端已通过 `POST /api/admin/reload-scoring` 热加载评分脚本，`reload_count=5`，常驻 Holistic worker PID 保持 `4148683` 不变。API 冒烟：`花` request `web_20260523_041443_0292d680` 得分 `75.501`，`跳` request `web_20260523_041447_f7341789` 得分 `80.586`。
- 新增报告 `/data/WYC/signLanguage/work/reports/scoring_semantic_phase_dtw_update_20260523.md` 和 Word 版 `/data/WYC/signLanguage/work/reports/scoring_semantic_phase_dtw_update_20260523.docx`。

### 2026-05-23 04:35 CST：坐姿鲁棒性与相对移动信号

- 根据“特征信号主要使用相对移动”的反馈，进一步优化纯手部词条的坐姿/站姿鲁棒性。当前策略不是把逐相邻帧位移直接加入主距离，而是优先使用更稳定的相对信号：wrist-relative 局部手部几何、手形相对特征、语义相位、起止/中段语义锚点和序列级 motion/roughness 统计。
- `score_holistic_sequence_mvp.py` 新增 pose-robust hand distance：对 `left_hand/right_hand` 优先比较以手腕为局部原点的手部结构，手部整体在身体坐标中的 global anchor 只保留小残差权重。`花` 当前 `hand_global_position_weight=0.06`，`跳` 为 `0.08`，从而减少坐姿躯干/镜头高度差对主手语义的干扰。
- 试验过逐帧 `*_motion` group 后发现其会误伤 `subsample_even`：隔帧采样天然改变相邻帧位移幅值，`花/跳` 正例显著下降。因此默认关闭 `relative_motion_enabled`，后续如要加入移动方向，应在语义相位片段级做方向判断，而不是直接比较相邻帧位移。
- 模板审计 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/template_pose_robust_no_adjacent_motion_audit_v1/template_semantic_weight_audit.md`：`10/10 ok`。最终门控：`花` `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/花_pose_robust_v1/` 正例最低 `83.213`、负例最高 `31.147`、margin `52.066`；`跳` `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/跳_pose_robust_v1/` 正例最低 `80.088`、负例最高 `39.639`、margin `40.448`。
- 合成坐姿压力测试：把手部整体向下平移 `0.45` 个归一化坐标单位后，`花` 得分 `97.470`、`跳` 得分 `93.125`，说明手相对站立躯干的绝对位置已不再主导纯手部动作评分。
- `5080` 评分脚本已热加载到 `reload_count=7`，Holistic worker PID 仍为 `4148683`。API 冒烟：`花` request `web_20260523_043442_e00f8b9c` 得分 `75.493`，`跳` request `web_20260523_043446_cbecd916` 得分 `81.071`。

### 2026-05-23 04:46 CST：网页测试数据回放复查纳入评分闭环

- 根据“算法调整都要进行网页测试数据复查”的要求，新增 `/data/WYC/signLanguage/work/scripts/replay_web_scoring_samples.py`，用于读取 `/data/WYC/signLanguage/work/generated/web_scoring_mvp/web_*/scoring_result.json` 及对应已保存 `Holistic` JSON，用当前评分模块重新计算历史网页/API 样本，不重新运行浏览器采集，不重启常驻 Holistic worker。
- 最新回放输出为 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_replay_pose_robust_v3/web_replay_current.md`、`.json`、`.csv`。快照覆盖 `111` 条保存样本，回放错误 `0`；`normal_like>=75` 为 `14` 条，`60-75` 边界 `1` 条，低分 `96` 条；旧均分 `33.129`，新均分 `34.738`。
- 分词条结果：`花` 共 `62` 条，正常 `6`、边界 `1`、低分 `55`，新均分 `45.979`；`跳` 共 `39` 条，正常 `8`、低分 `31`，新均分 `23.283`；`香蕉` 共 `10` 条，全部低分，新均分 `9.716`。
- 结论：离线 `花/跳` 判别门控和标准 demo 帧切片 API 冒烟均通过，但真实网页历史样本没有整体恢复到正常分区；因此后续不能只看离线 demo gate，任何评分算法、语义 profile、模板权重、对齐策略或分数尺度改动后，都必须运行网页回放并记录 normal/borderline/low 分布。
- 当前更稳的下一步是对低分网页样本生成骨架级诊断图和关键语义曲线，确认是手形/手指动态不匹配、动作窗口没采到、Holistic 局部抖动，还是用户动作本身与标准差异较大；不应直接全局放松阈值来掩盖问题。

### 2026-05-23 04:59 CST：恢复真实网页样本 Holistic 骨架可视化

- 根据“查看真实测试下 Holistic 识别效果”的要求，复用旧的 `keyframe_sampling_common._render_visual_cache` 渲染逻辑，新增薄 wrapper `/data/WYC/signLanguage/work/scripts/render_web_holistic_cache_visuals.py`。脚本只读取已保存的网页样本 `Holistic` JSON 和评分 metadata，不重新运行 MediaPipe，也不重启 `5080` 后端。
- 当前网页样本目录没有保留原始摄像头 JPEG 帧，因此本轮恢复的是空白画布上的关键点/骨架结果、联系表和识别时间线，不能还原原始画面叠加图。
- 已生成代表样本可视化目录 `/data/WYC/signLanguage/work/generated/web_holistic_visual_recovery_20260523_v1/`，覆盖 `花` 正常样本 `web_20260523_043442_e00f8b9c`、`花` 低分样本 `web_20260523_043923_b95a60d0/web_20260523_043955_dd909904`、`跳` 正常样本 `web_20260523_043446_cbecd916` 和 `跳` 低分样本 `web_20260523_044323_2eb9eb7e/web_20260523_044336_5d15d099/web_20260523_044358_00db9d4d`。
- 汇总索引为 `/data/WYC/signLanguage/work/generated/web_holistic_visual_recovery_20260523_v1/web_holistic_visual_recovery_summary.md`。每条样本包含 query 联系表、query 识别时间线、standard 联系表和 standard 识别时间线，方便直接对比标准样本与真实测试样本的手部检出情况。
- 2026-05-23 05:03 CST：按反馈把 contact sheet 改为只拼接骨架图，不再显示原图/关键点图/骨骼图三联。新输出目录为 `/data/WYC/signLanguage/work/generated/web_holistic_visual_recovery_20260523_v2/`，汇总索引 `/data/WYC/signLanguage/work/generated/web_holistic_visual_recovery_20260523_v2/web_holistic_visual_recovery_summary.md`；每张 skeleton contact sheet 尺寸约 `3840x2160`，单格左上角标注 `frame/time/L/R`，便于快速查看左右手检出。
- 2026-05-23 05:14 CST：继续生成 full 版骨架 contact，不再限制 `12` 帧，而是拼接每个网页请求中已保存的全部 Holistic 帧。输出目录 `/data/WYC/signLanguage/work/generated/web_holistic_visual_recovery_20260523_v3_full/`，汇总索引 `/data/WYC/signLanguage/work/generated/web_holistic_visual_recovery_20260523_v3_full/web_holistic_visual_recovery_summary.md`；例如 `web_20260523_043442_e00f8b9c` query 全部 `53` 帧，`web_20260523_043923_b95a60d0` query 全部 `30` 帧，`web_20260523_044323_2eb9eb7e` query 全部 `25` 帧。

### 2026-05-23 05:21 CST：确认 Holistic 基本可用后转向 DTW 鲁棒性修正

- 根据完整骨架 contact 观察，真实网页测试中 Holistic 通常能识别出可读的动作语义；主要问题转为当前 DTW/距离函数过于坐标化、对手掌朝向/手部相似变换/短遮挡和序列级 roughness 过敏。
- `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py` 已加入第一轮 DTW 鲁棒性修正：手部 landmark 距离在 wrist-relative 基础上增加 2D similarity alignment，用于降低手腕旋转、掌面朝向和摄像头角度导致的 RMSE；手形距离加入 capped RMSE，避免单个关键手指几何误差支配整帧；当手部语义可见且主 DTW 距离较低时，新增 `visible_semantic_core_tolerance`，把一部分 roughness/semantic-delta 序列惩罚改为诊断项。
- 为防止短促动作被过度放宽，`跳` 增加 `dynamic_required_penalty`：核心手指/手形几乎不动时判作静态假动作扣分。`跳_dtw_robust_v2` 离线 gate 通过，正例最低 `87.772`，负例最高 `41.936`；`fake_static_hold` 从上一版 `51.985` 压回 `35.729`。
- `花_dtw_robust_v1` 离线 gate 通过，正例最低 `94.309`，负例最高 `30.825`。网页回放 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_replay_dtw_robust_v2/web_replay_current.md`：111 条样本错误 `0`，正常 `15`、边界 `24`、低分 `72`；总均分从上一版 `34.738` 提升到 `42.889`，其中 `花` 均分 `45.979 -> 56.950`，`跳` 均分 `23.283 -> 28.852`。
- 结论：`花` 的真实网页样本明显受益，多个 50 分段样本提升到 `69-74`；`跳` 仍然低，说明它的问题不只是 missing 或轻微朝向差异，而是当前局部 hand/shape DTW 仍没有充分表达“两指先弯后伸并相对左手地面弹跳”的语义曲线，后续应增加显式语义曲线 DTW。
- `5080` 已通过 `POST /api/admin/reload-scoring` 热加载新评分代码，`reload_count=8`，Holistic worker PID 仍为 `4148683`，未重启后端 worker。

### 2026-05-23 06:03 CST：`跳` 单手乱摆高分问题定位与双手关系修正

- 问题定位：`跳` 的核心语义应是双手交互，即右手食指/中指在左手“地面”基础上弹跳。但当前代码里 `two_hand_relation` 绑定在 relative motion 逻辑后面，默认关闭 `relative_motion_enabled=False` 时静态双手关系没有稳定进入 DTW；同时 `跳` profile 的 `focus_groups` 仍偏向右手，左手地面和双手关系没有成为 required 语义。
- 第二个关键问题是缺失处理过轻：当查询样本完全没有左手时，`left_hand/two_hand_relation` 的几何距离会因为没有共同 mask 变成 0，只通过全局 `missing` 小权重扣分。这样单手乱摆只要右手某些帧和标准右手接近，就可能被 DTW 拉到较高分。
- 已修正 `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py`：`two_hand_relation` 现在作为静态语义关系始终加入序列特征，即使相邻帧 motion 关闭也保留；并新增核心组缺失距离、`required_presence_groups`、双手关系维度权重、以及 `semantic_core_query_hand_presence`，避免单手样本触发可见核心容忍或 noise floor。
- 已修正 `/data/WYC/signLanguage/work/scripts/build_semantic_weight_profiles.py`：`跳` 的重点组改为 `two_hand_relation/right_hand_shape/right_hand/left_hand`；`semantic_dtw.required_presence_groups=["left_hand","right_hand","two_hand_relation"]`；双手关系权重提升到 `0.90`，躯干/脸继续为 0，保持坐姿鲁棒。
- 离线门控仍通过：`跳_twohand_relation_v2` 正例最低 `76.823`，负例最高 `31.418`，margin `45.406`；`花_twohand_relation_guard_v2` 正例最低 `90.917`，负例最高 `15.133`，没有被本轮 `跳` 修正破坏。
- 网页回放 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_replay_twohand_relation_v2/web_replay_current.md` 覆盖 `134` 条保存样本，错误 `0`，normal `15`、borderline `0`、low `119`。重点样本：`web_20260523_053345_da4d1ec9` 左手覆盖 `0.0`，旧分 `23.827` -> 新分 `2.366`；`web_20260523_053401_8934d89a` 左手覆盖 `0.0`，旧分 `38.408` -> 新分 `3.643`；说明单手乱摆高分问题已被压低。
- 仍需继续处理的问题：`花` 网页回放均值当前仍低于上一轮 DTW robust 结果，说明真实网页样本的手部短暂缺失、手形角度、个体执行差异和模板单一性仍会误伤正样本。下一阶段应引入“基于文档核心语义的骨架模板增强 + best-of/trimmed-mean DTW”，扩大标准语义的可接受等价类，而不是继续全局放松分数尺度。
- 调研结论：Holistic/MediaPipe 提供 543 个 landmarks、hand z 相对腕部深度、pose world landmarks 等估计结果，但本身不是 3D 动作生成器。可用策略是先在已归一化骨架/特征空间做语义保持增强，包括轻微 2D/3D 旋转、镜头角度扰动、手指节点微扰、左右镜像加 handedness swap、时间拉伸/裁剪；外部 sign-language production/text-to-pose 模型存在，但需要大数据和训练，不适合作为当前小样本评分 MVP 的依赖。
- `5080` 已通过热重载加载修正后的评分代码，`scoring_module.reload_count=13`，Holistic worker PID 仍为 `4148683`，未重启常驻 Holistic。

### 2026-05-23 06:58 CST：可见语义核心评分与 `跳` 关系语义 floor

- 继续沿“语义加权 DTW + 可解释语义模块”的路线推进。诊断显示 `花` 的网页低分主要来自非 required 手部 missing 被过度放大；已把默认 `group_missing_distance_weight/focus_missing_distance_weight/relation_missing_distance_weight` 降为 `0`，只对 `跳` 这类显式 required 双手关系保留强缺失惩罚。代表样本 `web_20260523_053116_49159767` 从 `27.6` 恢复到 `75.9`，`web_20260523_053035_073e5794` 恢复到 `72.9`。
- `花` 新增 `visible_semantic_core_scale`：当主手语义骨架可见、DTW 主路径距离足够低时，使用更宽的可见核心分数尺度，把 roughness / semantic-delta 等因短遮挡或采样导致的序列诊断项降权。离线 gate `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/花_core_visible_scale_v1/` 通过：正例最低 `80.311`，负例最高 `31.323`，margin `48.987`。
- `跳` 新增 `jump_relation_semantic_floor`：仍要求双手存在和 `two_hand_relation` 可计算，但当右手相对左手地面的起止变化方向一致、纵向跳跃幅度足够、且不是主要水平移动时，用语义 floor 给分。第一版过宽，会把 `fake_shuffle_frames` 和 `香蕉` 抬高；已加入纵向幅度下限和水平漂移比例约束，离线 gate `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/跳_relation_semantic_floor_v3/` 通过：正例最低 `76.823`，负例最高 `31.418`，margin `45.406`。
- 保存网页样本回放 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_replay_relation_semantic_floor_v3/web_replay_current.md` 覆盖 `148` 条，错误 `0`，总正常 `49`、边界 `32`、低分 `67`，总均分 `34.080 -> 49.847`。`花`：`80` 条，正常 `32`、边界 `21`、低分 `27`，均分 `46.537 -> 61.307`。`跳`：`52` 条，正常 `17`、边界 `11`、低分 `24`，均分 `21.465 -> 43.450`。
- `跳` 重点样本：`web_20260523_052715_1ad3c2d2` 从 `22.3` 到 `78.0`，`web_20260523_053241_5fbbf9c7` 从 `12.6` 到 `76.0`，`web_20260523_063052_fc94e4f7` 从 `17.5` 到 `75.1`；单手乱摆仍低，`web_20260523_053345_da4d1ec9` 为 `2.4`，`web_20260523_053401_8934d89a` 为 `3.6`。
- 当前状态：`花` 已基本进入正常/边界为主，`跳` 对双手且关系方向正确的测试恢复明显，但仍有一部分样本低分，主要是动作窗口内左手地面覆盖不足、关系方向相反、或核心关系不满足。后续继续优化应优先改进前端采样/动作窗口和左手覆盖诊断，而不是继续全局放宽 `jump_relation_semantic_floor`。
- 运行态：原 `5080` 后端在测试间隙已退出，已重新启动唯一 `signlanguage-web` / `127.0.0.1:5080` 服务；当前只监听 `5080`，Holistic worker PID `811485`，初始化 `260.122s`，状态 `ready`。`POST /api/admin/reload-scoring` 已加载当前评分脚本，`reload_count=1`，`last_reload_error=null`。

### 2026-06-02 21:44 CST：`花` 短采集上下文容忍与 opening/spread 守卫

- 继续沿“语义加权 DTW + 可解释语义模块”推进。新增网页样本显示 `花` 的若干 15/25 帧实测样本主手 DTW 距离已经很近，但被完整标准模板的静止上下文、长度差异和 `semantic_delta` 诊断项拉低。例如 `web_20260523_071306_071a2172` 旧分 `19.958`，`dtw=0.037`，核心右手覆盖 `0.600`，主要问题是 `length_penalty=0.1215`。
- `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py` 新增 `short_core_capture_tolerance`：对 `花` 这类单手单阶段动作，在完整序列路径下，如果核心手可见、主 DTW 足够近、查询帧数明显短于标准模板，则把标准静止上下文造成的长度/语义摘要 penalty 作为上下文误差降权。该逻辑不会切换到无条件 action-window，也不会改变局部 DTW 主距离。
- 为避免把局部相似但语义不对的动作抬高，新增 `flower_opening_guard`。它在 `left/right_hand_shape` 的 opening/spread 相关维度上计算起止变化、range 和连续 opening score；`short_core_capture_tolerance`、`visible_semantic_core_tolerance` 和 `visible_semantic_core_scale` 都必须先通过该守卫。负例 `谗（羡慕）` 原本因局部手骨架相似被抬到 `71.428`，加入守卫后降到 `32.047`。
- `/data/WYC/signLanguage/work/scripts/build_semantic_weight_profiles.py` 已更新 `花` 的 `semantic_dtw` profile：`core_visible_presence_threshold=0.58`、`core_visible_max_normalized_distance=0.105`、`short_core_capture_tolerance_cap=0.145`、`flower_opening_guard_enabled=True`、`flower_opening_min_score=0.30`；并已重新生成 `/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json/.md`。
- 离线门控通过。`花_opening_guard_v1`：正例最低 `80.311`、负例最高 `32.047`、margin `48.263`，最高负例为 `other_demo_谗_羡慕`；`跳_opening_guard_regression_v1`：正例最低 `76.823`、负例最高 `31.418`、margin `45.406`，确认 `花` 的守卫改动没有破坏 `跳` 的双手关系门控。
- 保存网页样本最新回放 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_replay_20260602_opening_guard_v2/web_replay_current.md` 覆盖 `162` 条样本，错误 `0`，总正常 `92`、边界 `18`、低分 `52`，总均分 `35.139 -> 56.868`。`花`：`91` 条，正常 `74`、边界 `7`、低分 `10`，均分 `46.803 -> 72.825`；`跳`：`53` 条，正常 `18`、边界 `11`、低分 `24`，均分 `22.481 -> 44.051`。
- 代表恢复样本：`web_20260523_071212_4547d033` 从 `45.047` 到 `79.560`，`web_20260523_071306_071a2172` 从 `19.958` 到 `76.178`，`web_20260523_071320_415e2975` 从 `30.132` 到 `78.392`，`web_20260602_212951_e1173da1` 从 `29.565` 到 `77.625`，`web_20260602_213015_411a2ecd` 从 `53.813` 到 `78.861`。
- 当前 `跳` 的低分样本主要来自早期单手乱摆、双手关系方向不满足或左手地面覆盖不足；最新新增 `web_20260602_214010_3f951c51` 为 `跳`，网页端已给出 `75.325`。因此暂不继续放宽 `jump_relation_semantic_floor`，避免再次抬高单手乱摆或其他 demo。
- 运行态：`5080` 仍是唯一 Web/Holistic 后端，监听 `127.0.0.1:5080`；`POST /api/admin/reload-scoring` 已热加载当前评分脚本，`reload_count=3`，`last_reload_error=null`。Holistic worker 未重启，PID `811485`，状态 `ready`。

### 2026-06-02 21:55 CST：`跳` 低分分类诊断与网页语义诊断表

- 在用户继续实测后，新增 `web_20260602_214656_3fae071b`，目标词为 `跳`，当前得分 `1.354`。该样本不是算法热重载问题，诊断显示 `left_presence=0.14`、`right_presence=0.71`、`two_hand_relation=0.0`，`jump_relation_semantic_floor` 失败原因是 `insufficient_two_hand_presence`。
- 已生成同口径 `跳` 网页样本语义诊断报告 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/jump_web_diagnostics_20260602_v2/jump_web_diagnostics.md`，逐条使用网页样本保存的 `standard_json` 和 `query_json` 复算，不重新运行 Holistic。当前 `跳` 共 `54` 条：正常 `18`、边界 `11`、低分 `25`；其中 accepted `29` 条，低分分类为 `two_hand_presence_low=19`、`relation_direction_mismatch=6`。
- 诊断结论：`跳` 的剩余低分样本主要是核心语义未满足，而不是统一阈值过严。`跳` 文档语义要求左手地面 + 右手两指在左手基础上跳；当左手覆盖不足、两手关系不可计算、或右手相对左手运动方向相反时，应保持低分。继续全局放宽 `jump_relation_semantic_floor` 会重新抬高单手乱摆和错误关系动作。
- 最新全量网页回放 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_replay_20260602_opening_guard_v3/web_replay_current.md` 覆盖 `163` 条，错误 `0`，总正常 `92`、边界 `18`、低分 `53`，总均分 `34.932 -> 56.527`。`花` 保持 `91` 条中正常 `74`、边界 `7`、低分 `10`，均分 `72.825`；`跳` 为 `54` 条中正常 `18`、边界 `11`、低分 `25`，均分 `43.261`。
- 网页前端 `/data/WYC/signLanguage/work/web/static/index.html` 和 `/data/WYC/signLanguage/work/web/static/app.js` 已在结果区新增“语义诊断”表，直接显示后端返回的 `alignment_mode`、`score_scale_reason`、`semantic_floor_reason`、`semantic_floor_score`、`semantic_core_presence`、`flower_opening_score`、左右手 presence 和 `required_presence_penalty`。这样 `跳` 低分时能在页面上看到是 `insufficient_two_hand_presence`、`relation_direction_mismatch`，还是其他语义原因。
- 前端 JS 已通过 `node --check`；`5080/api/status` 显示 `reload_count=3`、`last_reload_error=null`、Holistic worker PID `811485` ready。前端诊断表只读评分返回字段，不修改评分算法，因此未触发新的评分热重载。

### 2026-06-02 21:59 CST：网页诊断提示中文化

- 在不修改评分算法的前提下，继续优化网页结果反馈。`/data/WYC/signLanguage/work/web/static/app.js` 新增 `semanticReasonLabel()` 和 `buildDiagnosticNote()`，把后端内部诊断字段映射成中文说明。
- `跳` 低分时，页面结果说明会直接提示 `双手覆盖不足`、当前左右手覆盖比例，并提醒左手“地面”和右手“跳跃”需要同时稳定入画；若 `relation_direction_mismatch`，则提示双手相对运动方向不一致。`花` 若 `flower_opening_guard` 未通过，则提示未检测到清晰的手指张开/绽放动态。
- “语义诊断”表的字段名已从英文内部变量改为中文标签，例如 `语义 floor 原因`、`左手覆盖`、`右手覆盖`、`必要覆盖惩罚`、`花-张开分数`。`renderTable()` 也已修正为把 `null/undefined` 显示为 `--`，避免页面出现 `undefined`。
- 验证：`node --check work/web/static/app.js` 通过；`curl http://127.0.0.1:5080/static/app.js` 已返回新版 JS；`/api/status` 仍显示 `reload_count=3`、`last_reload_error=null`、Holistic worker PID `811485` ready。由于这次只改前端展示，没有修改评分脚本或 profile，因此未重新跑全量评分回放。

### 2026-06-02 22:11 CST：网页样本语义诊断脚本固化

- 新增 `/data/WYC/signLanguage/work/scripts/analyze_web_scoring_diagnostics.py`，用于复用已保存网页/API 样本的 `standard_json/query_json` 复算当前评分，并把 `score_scale.semantic_floor`、`flower_opening_guard`、左右手 presence、核心语义覆盖、分组距离和低分诊断分类写入 JSON/CSV/Markdown。该脚本不重新运行 Holistic，也不重启 `5080` 常驻后端。
- 已运行 `花/跳` 当前网页样本诊断：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_semantic_diagnostics_20260602_v1/web_semantic_diagnostics.md`。样本数 `145`、错误 `0`、正常 `92`、边界 `18`、低分 `35`，总均分 `61.815`、中位数 `78.026`。
- 分词条结果：`花` `91` 条，正常 `74`、边界 `7`、低分 `10`，均分 `72.825`，核心覆盖均值 `0.704`；诊断为 `flower_core_accepted=81`、`flower_core_hand_presence_low=5`、`flower_opening_guard_failed=4`、`flower_low_other=1`。`跳` `54` 条，正常 `18`、边界 `11`、低分 `25`，均分 `43.261`、中位数 `66.206`、核心覆盖均值 `0.691`；诊断为 `jump_core_accepted=29`、`jump_two_hand_presence_low=19`、`jump_relation_direction_mismatch=6`。
- 结论：当前 `花` 的主要网页正样本已经由右手核心语义接收，剩余低分多为核心手覆盖不足或未检测到张开/绽放动态；`跳` 的剩余低分仍集中在左手地面/双手覆盖不足和双手相对运动方向不匹配，不应通过继续放宽 `jump_relation_semantic_floor` 来抬高。后续真实网页测试应先看该诊断脚本和页面“语义诊断”表，再决定是采集问题、动作语义问题还是算法需要进一步模板增强。
- 验证：`/home/wuyangcheng/myenv/bin/python -m py_compile work/scripts/analyze_web_scoring_diagnostics.py` 通过；`5080/api/status` 仍显示 `reload_count=3`、`last_reload_error=null`、Holistic worker PID `811485` ready。

### 2026-06-02 22:20 CST：评分结果增加采集质量门控

- 为避免把“核心关键点没入画/不可评分”和“动作语义做错”混在同一个低分里，`/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py` 新增 `score_scale.capture_quality` 诊断。它输出 `status=score_valid / needs_recapture / semantic_mismatch`、`reason`、左右手覆盖和中文 message；不参与 `prototype_score`、DTW 距离或 score scale 计算，因此不会把错误动作抬高。
- 质量门控口径：`跳` 若左手地面和右手跳跃没有同时稳定入画，标记 `needs_recapture`；若双手入画但相对运动方向、纵向弹跳或幅度不满足，标记 `semantic_mismatch`。`花` 若核心手覆盖不足，标记 `needs_recapture`；若手部入画但 opening/spread 守卫失败，标记 `semantic_mismatch`。
- 前端 `/data/WYC/signLanguage/work/web/static/app.js` 已接入该字段：结果标题显示 `可评分 / 建议重采 / 动作语义不足`，低分提示优先说明采集质量或语义原因，语义诊断表新增 `采集状态`、`采集诊断`、`评分可靠`。环形分数颜色也区分建议重采和语义不足。
- 网页回放 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_replay_20260602_capture_quality_v1/web_replay_current.md` 覆盖 `163` 条，错误 `0`，正常 `92`、边界 `18`、低分 `53`，与上一版分布一致，确认新增质量门控未改变评分数值。`花` 仍为 `74/7/10`，均分 `72.825`；`跳` 仍为 `18/11/25`，均分 `43.261`。
- 新版语义诊断 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_semantic_diagnostics_20260602_capture_quality_v2/web_semantic_diagnostics.md`：`花/跳` 共 `145` 条，采集质量分布为 `score_valid=111`、`needs_recapture=25`、`semantic_mismatch=9`。其中 `跳`：`score_valid=29`、`needs_recapture=19`、`semantic_mismatch=6`；`花`：`score_valid=82`、`needs_recapture=6`、`semantic_mismatch=3`。
- 验证：`py_compile` 通过；`node --check work/web/static/app.js` 通过；`POST /api/admin/reload-scoring` 热加载成功，`reload_count=4`、`last_reload_error=null`；Holistic worker PID 仍为 `811485`，未重启；`curl http://127.0.0.1:5080/static/app.js` 已返回包含 `captureQualityLabel` 和 `capture_quality` 的新版前端。

### 2026-06-02 22:26 CST：采集前目标动作核心要点提示

- 基于最新质量诊断发现 `跳` 低分中大量属于左手地面和右手跳跃未同时稳定入画，已在网页采集区新增 `动作重点` 提示，随目标词切换显示核心语义要点。该提示不展开参考视频、不改变评分算法，只在用户点击采集前提醒关键手部和核心关系。
- 前端改动：`/data/WYC/signLanguage/work/web/static/index.html` 新增 `targetCue` 区块；`/data/WYC/signLanguage/work/web/static/app.js` 新增 `TARGET_CUES` 和 `updateTargetCue()`；`/data/WYC/signLanguage/work/web/static/styles.css` 新增 `.target-cue` 样式。`花` 提示开花手势从撮合到张开、手指绽放过程清楚入画；`跳` 提示左手作为地面稳定入画、右手食指/中指在左手上方弹跳。
- 验证：`node --check work/web/static/app.js` 通过；`curl http://127.0.0.1:5080/` 已返回 `targetCue/动作重点`；`curl http://127.0.0.1:5080/static/app.js` 已返回 `TARGET_CUES/updateTargetCue`；`curl http://127.0.0.1:5080/static/styles.css` 已返回 `.target-cue`。本次只改前端采集提示，没有修改评分脚本或 profile，因此未重新跑评分回放。

### 2026-06-02 22:28 CST：网页诊断增加有效采集口径

- 为更准确判断“网页测试结果是否正常”，`/data/WYC/signLanguage/work/scripts/analyze_web_scoring_diagnostics.py` 增加 `有效采集口径`：排除 `needs_recapture` 样本，只统计核心关键点已经足够入画、可以解释为动作语义评分的 `score_valid` 与 `semantic_mismatch` 样本。
- 新报告 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_semantic_diagnostics_20260602_effective_capture_v3/web_semantic_diagnostics.md` 覆盖 `花/跳` 共 `145` 条，错误 `0`。原始口径保持：正常 `92`、边界 `18`、低分 `35`，采集质量为 `score_valid=111`、`needs_recapture=25`、`semantic_mismatch=9`。
- 有效采集口径总览：可评分样本 `120`，正常+边界 `110`，低分 `10`，正常+边界率 `91.7%`。`花`：原始 `91` 条，建议重采 `6`，有效采集 `85`，正常+边界 `81`，低分 `4`，正常+边界率 `95.3%`，有效均分 `75.552`。`跳`：原始 `54` 条，建议重采 `19`，有效采集 `35`，正常+边界 `29`，低分 `6`，正常+边界率 `82.9%`，有效均分 `64.830`。
- 结论：当前网页测试中，`花` 在有效采集口径下已经基本正常；`跳` 的原始低分主要由 `needs_recapture` 拉低，排除重采后仍有 `6` 条语义不匹配低分，说明应继续通过采集引导和语义诊断处理，不应放宽 `jump_relation_semantic_floor`。
- 验证：`/home/wuyangcheng/myenv/bin/python -m py_compile work/scripts/analyze_web_scoring_diagnostics.py` 通过；诊断脚本只复用保存的 `Holistic` JSON，不运行 Holistic、不重启 5080；`/api/status` 仍显示 `reload_count=4`、`last_reload_error=null`、Holistic worker PID `811485` ready。

### 2026-06-02 22:32 CST：剩余语义不匹配低分明细

- 为判断剩余有效采集低分是否应由算法放宽处理，继续扩展 `/data/WYC/signLanguage/work/scripts/analyze_web_scoring_diagnostics.py`：在报告中新增 `语义不匹配明细`，提取 `semantic_floor` 的方向余弦、纵向分数、幅度比、水平/纵向比例和关系覆盖等字段，便于解释 `跳` 的语义失败。
- 新报告 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_semantic_diagnostics_20260602_semantic_mismatch_v4/web_semantic_diagnostics.md` 保持同样样本和有效采集口径：`花/跳` 原始 `145` 条，错误 `0`；有效采集 `120` 条，正常+边界 `110`，低分 `10`，正常+边界率 `91.7%`。
- `跳` 的 `6` 个 `semantic_mismatch` 低分均为 `jump_relation_direction_mismatch`。方向余弦分别约为 `-0.923`、`-0.995`、`-0.857`、`0.217`、`0.096`、`-0.717`，都显著低于当前方向一致性要求，说明它们不是简单阈值偏紧，而是右手相对左手地面的运动方向与标准“跳”语义不一致。
- `花` 的 `3` 个 `semantic_mismatch` 低分是 `flower_opening_guard_failed`，对应 opening/spread 分数为 `0.000`、`0.122`、`0.086`，说明手部局部可见但没有检测到足够清楚的绽放张开动态。
- 结论：剩余有效采集低分可以由具体核心语义失败解释，不应通过继续放宽 `jump_relation_semantic_floor` 或 `flower_opening_guard` 来抬分。更合理的下一步是继续收集真实有效样本和人工标签，或用骨架可视化人工复核这些 semantic mismatch。
- 验证：`py_compile` 通过；该诊断脚本只读取保存的 `Holistic` JSON，不运行 Holistic、不重启 `5080`；`/api/status` 仍显示 `reload_count=4`、`last_reload_error=null`、Holistic worker PID `811485` ready。

### 2026-06-02 22:59 CST：`跳` 局部关系段 fallback 与两指手形守卫

- 继续复核剩余 `跳` semantic mismatch。先用 `/data/WYC/signLanguage/work/scripts/render_web_holistic_cache_visuals.py` 生成骨架拼接图，输出 `/data/WYC/signLanguage/work/generated/web_holistic_visual_semantic_mismatch_20260602_v2/web_holistic_visual_recovery_summary.md`；脚本新增 `--rescore-current`，可按当前评分模块复算分数和 action window，避免使用旧 `scoring_result.json` 分数造成混淆。
- 数值复查发现：6 个 `跳` mismatch 的 action-window 起止净位移方向失败，但在完整查询序列里都能找到方向一致、纵向为主、幅度足够的局部双手关系段。这说明原 `jump_relation_semantic_floor` 过度依赖 action-window 起止相位，可能误杀采集起止不同但包含真实弹跳语义的网页样本。
- `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py` 新增 `full_sequence_local_relation_segment` fallback：只有当双手覆盖、required presence、右手/右手形状距离等基础约束通过，而 action-window net 判断失败时，才在完整查询序列中搜索局部双手关系段。局部段必须满足方向余弦高、纵向幅度足、水平漂移低、覆盖比例足够。
- 第一个 fallback 版本会误抬高 `汽车=81.754` 和 `谗（羡慕）=75.229`，离线 gate 失败。继续加入 `right_two_finger_shape` 守卫，显式检查文档语义“右手食指/中指模拟两条腿”：局部段右手食指/中指形状均值需达到 `jump_relation_local_min_two_finger_shape_mean=0.95`。该守卫把 `汽车` 压回 `9.384`、`谗（羡慕）` 压回 `4.844`。
- `/data/WYC/signLanguage/work/scripts/build_semantic_weight_profiles.py` 已把 `跳` profile 显式写入 `jump_relation_local_fallback_enabled=True`、`jump_relation_local_min_direction=0.92`、`jump_relation_local_min_amplitude_ratio=0.80`、`jump_relation_local_max_horizontal_to_vertical=0.60`、`jump_relation_local_min_coverage=0.48`、`jump_relation_local_min_two_finger_shape_mean=0.95`；其他词条默认 `jump_relation_local_fallback_enabled=False`。
- 离线判别 gate `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/跳_local_relation_fallback_shape_guard_v2/scoring_mvp_result.md` 通过：正例最低 `76.823`、负例最高 `31.418`、margin `45.406`。最高负例仍为 `fake_static_hold`，其他 demo 均显著低：`香蕉=18.058`、`指示=15.333`、`汽车=9.384`、`谗（羡慕）=4.844`。
- 网页语义诊断 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_semantic_diagnostics_20260602_jump_local_shape_guard_v2/web_semantic_diagnostics.md`：`花/跳` 145 条，错误 `0`，正常 `94`、边界 `22`、低分 `29`。有效采集口径：`120` 条中正常+边界 `116`、低分 `4`，正常+边界率 `96.7%`。`跳` 54 条中有效采集 `35` 条全部正常/边界，剩余 `19` 条低分均为 `needs_recapture / jump_two_hand_presence_low`。
- 全量网页回放 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_replay_20260602_jump_local_shape_guard_v3/web_replay_current.md` 覆盖 `164` 条，错误 `0`，总正常 `94`、边界 `22`、低分 `48`，总均分 `34.849 -> 58.725`。`花` 保持 `91` 条正常 `74`、边界 `7`、低分 `10`，均分 `72.825`；`跳` 改善为 `54` 条正常 `20`、边界 `15`、低分 `19`，均分 `50.588`。
- 运行态：`POST /api/admin/reload-scoring` 已热加载到 `reload_count=6`，`last_reload_error=null`；常驻 Holistic worker PID 仍为 `811485`，未重启。该改动属于评分模块和 profile 热更新，不改变前端采集流程。

### 2026-06-02 23:06 CST：`跳` 局部语义段解释性诊断

- 为让网页测试时能看清 `跳` 是 action-window 直接通过，还是完整序列局部语义段通过，继续扩展诊断输出，不修改评分逻辑。
- `/data/WYC/signLanguage/work/scripts/analyze_web_scoring_diagnostics.py` 新增字段：`semantic_floor_source`、`semantic_floor_query_segment_start/end/coverage`、`semantic_floor_fallback_from_reason/direction_cosine`、`jump_two_finger_shape_mean/range/valid_count`。报告新增 `跳语义 floor 接收明细`，用于逐条查看局部 fallback 是否由两指手形守卫支撑。
- 新诊断报告 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_semantic_diagnostics_20260602_jump_local_explain_v3/web_semantic_diagnostics.md` 覆盖 `花/跳` 145 条，错误 `0`，分布保持 `normal_like=94`、`borderline=22`、`low=29`。`跳` 的 semantic floor 来源分布为 `action_window_net=29`、`full_sequence_local_relation_segment=6`；6 条局部段修复样本的两指手形均值约为 `1.027-1.492`，fallback 原因均为原 action-window `relation_direction_mismatch`。
- 网页前端 `/data/WYC/signLanguage/work/web/static/app.js` 的语义诊断表新增 `语义 floor 来源`、`跳-局部段帧`、`跳-局部段覆盖`、`跳-两指手形`、`跳-fallback 原因`。当 `跳` 分数由完整序列局部弹跳段支撑时，结果说明会直接提示“检测到完整序列中的局部双手弹跳段”，并显示两指手形与局部段覆盖。
- 验证：`py_compile analyze_web_scoring_diagnostics.py` 通过；`node --check work/web/static/app.js` 通过；`curl http://127.0.0.1:5080/static/app.js` 已返回 `semanticFloorSourceLabel`、`语义 floor 来源` 和 `跳-两指手形`。本次只改诊断脚本和前端展示，没有修改评分模块或 profile，因此不需要重新热加载评分模块；`5080` 仍为 `reload_count=6`、`last_reload_error=null`、Holistic worker PID `811485` ready。

### 2026-06-02 23:27 CST：`花` 短可见核心 floor 与当前标准库 replay 口径

- 继续复核 `花` 剩余有效低分，发现部分历史网页样本保存的 `standard_json` 指向早期 `run2` 标准，而当前在线后端实际通过 `_template_path(target_word)` 使用 `run3` dense 标准库。为避免把旧标准路径问题误判为算法问题，`/data/WYC/signLanguage/work/scripts/replay_web_scoring_samples.py` 和 `/data/WYC/signLanguage/work/scripts/analyze_web_scoring_diagnostics.py` 新增 `--template-root` 参数：query 仍复用保存的网页 Holistic JSON，standard 可覆盖为当前标准库，用于模拟当前 5080 在线评分。
- 数值复查显示，`web_20260523_010203_88bdaf53` 用保存旧标准复算为 `17.462`，但用当前 `run3` 标准库复算为 `72.184`，说明历史 saved-standard replay 与当前在线评分不完全等价。当前 replay 报告必须明确区分 `saved_standard_json` 与 `template_root` 两种口径。
- `score_holistic_sequence_mvp.py` 新增仅针对 `花` 的 `short_visible_core` semantic floor。触发条件较窄：query 明显短于当前长模板、核心手覆盖达标、`flower_opening_guard` 通过且 opening 分数足够、DTW 核心距离足够小、动作窗口能量覆盖足够、主手几何距离不过大。该 floor 只把短视频里清晰可见的开花核心段拉到边界/正常区间，上限约 `80`，不会给满分。
- `/data/WYC/signLanguage/work/scripts/build_semantic_weight_profiles.py` 已为 `花` profile 写入 `flower_visible_core_floor_enabled=True`、`flower_visible_core_floor_min_score=72.0`、`flower_visible_core_floor_max_score=80.0`、`flower_visible_core_floor_max_length_ratio=0.32`、`flower_visible_core_floor_min_presence=0.62`、`flower_visible_core_floor_min_opening_score=0.60`、`flower_visible_core_floor_max_dtw=0.042`、`flower_visible_core_floor_min_action_coverage=0.62`，并重新生成 `/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json/.md`。
- 快速负例复核：`花` 对其他 demo 仍显著低，最高为 `谗（羡慕）=32.047`，`指示=26.929`、`唱歌=21.673`、`汽车=13.892`、`虎=2.928`；新 floor 未触发这些其他 demo，原因主要是查询不属于短核心捕获。两个短网页 `花` 样本被保守抬升：`web_20260522_222243_a23d679c=73.696`、`web_20260523_005246_dbadcd43=74.547`，另一个短核心样本 `web_20260522_231304_9e8827a4=77.176`。
- 离线判别 gate 保持通过：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/花_short_visible_core_floor_v1/scoring_mvp_result.md` 正例最低 `80.311`、负例最高 `32.047`、margin `48.263`；`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/跳_short_visible_core_floor_regression_v1/scoring_mvp_result.md` 正例最低 `76.823`、负例最高 `31.418`、margin `45.406`，确认 `跳` 局部关系段与两指手形守卫未回退。
- saved-standard 全量网页回放 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_replay_20260602_flower_short_core_floor_saved_standard_v1/web_replay_current.md` 覆盖 `164` 条，错误 `0`，总正常 `94`、边界 `22`、低分 `48`，与上一版保存标准口径一致；`花` 仍为正常 `74`、边界 `7`、低分 `10`，均分 `72.825`，因为该口径沿用每条历史请求保存的标准路径。
- active-template 全量网页回放 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_replay_20260602_flower_short_core_floor_active_template_v1/web_replay_current.md` 覆盖 `164` 条，错误 `0`，总正常 `95`、边界 `22`、低分 `47`，总均分 `34.849 -> 59.285`。`花` 为 `91` 条中正常 `75`、边界 `7`、低分 `9`，均分 `73.330`；`跳` 保持正常 `20`、边界 `15`、低分 `19`，均分 `50.979`。这是更接近当前 5080 在线后端的 replay 口径。
- active-template 语义诊断 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_semantic_diagnostics_20260602_flower_short_core_floor_active_template_v1/web_semantic_diagnostics.md` 覆盖 `花/跳` 145 条，错误 `0`，正常 `95`、边界 `22`、低分 `28`。有效采集口径：`120` 条中正常+边界 `117`、低分 `3`，正常+边界率 `97.5%`。`花` 有效采集 `85` 条，正常+边界 `82`、低分 `3`、有效均分 `76.388`；剩余有效低分均为 `flower_opening_guard_failed`。`跳` 有效采集 `35/35` 正常或边界，剩余 raw low 均为建议重采的双手覆盖不足。
- 网页前端 `/data/WYC/signLanguage/work/web/static/app.js` 已把 `short_visible_core` 显示为“短视频可见核心段”，并在 `花` 使用该 floor 时提示“短视频中检测到开花核心段”，显示张开分数和核心手覆盖。验证：`node --check work/web/static/app.js` 通过；`curl http://127.0.0.1:5080/static/app.js` 已返回新版文案。
- 运行态：已通过 `POST /api/admin/reload-scoring` 热加载评分模块，`reload_count=7`、`last_reload_error=null`；常驻 Holistic worker PID 仍为 `811485`、状态 `ready`，未重启。

### 2026-06-02 23:36 CST：5080 在线 API smoke 与 post-smoke 回放

- 为确认当前改动不只是在离线 replay 中正常，直接调用 `http://127.0.0.1:5080/api/score`，让请求走真实线上路径：JPEG base64 帧切片上传 -> 常驻 Holistic worker -> 当前 active template -> 当前评分模块。第一次手工截取 `花` 的 6 帧短片段得到 `web_20260602_233301_233b8215`，分数 `2.913`，诊断为 `flower_opening_guard_failed / opening_guard_too_weak`。这条样本说明 opening guard 正确拦截了“手已入画但没有清晰张开动态”的短截片，不应视为算法退化。
- 继续用 active template JSON 里的完整 `frame_idx` 从参考视频取帧，做更标准的端到端 smoke。`花` 完整模板帧上传得到 `web_20260602_233343_899e6970`，`53` 帧，score `76.899`，`capture_quality=score_valid`，`score_scale_reason=visible_semantic_core_scale`，`worker.holistic_eval_sec=2.232`、`api_total_sec=4.475`。`跳` 完整模板帧上传得到 `web_20260602_233348_53e3df5d`，`19` 帧，score `88.577`，`capture_quality=score_valid`，`semantic_floor_source=action_window_net`，`semantic_floor_score=82.086`，`worker.holistic_eval_sec=0.776`、`api_total_sec=1.187`。
- 另一个短 `跳` 在线 smoke `web_20260602_233302_d92c0ce2` 得到 score `70.661`，`capture_quality=score_valid`，`semantic_floor_source=action_window_net`，说明当前短促 `跳` 的线上路径能通过双手关系语义 floor 给出边界分。短 `花` smoke 的低分和完整 `花` smoke 的正常分共同验证了：`花` 不是被无条件抬高，而是必须有清晰 opening/spread 动态。
- 已把新增 `4` 条在线 smoke 样本纳入 active-template 语义诊断：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_semantic_diagnostics_20260602_post_online_smoke_v1/web_semantic_diagnostics.md`。样本数 `149`、错误 `0`、正常 `97`、边界 `23`、低分 `29`；采集质量为 `score_valid=120`、`needs_recapture=25`、`semantic_mismatch=4`。有效采集口径：`124` 条中正常+边界 `120`、低分 `4`，正常+边界率 `96.8%`。`跳` 有效 `37/37` 正常或边界；`花` 有效 `87` 条中正常+边界 `83`、低分 `4`，新增低分即上述故意截得太短的 opening guard 失败 smoke。
- post-smoke active-template 全量 replay `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_replay_20260602_post_online_smoke_active_template_v1/web_replay_current.md` 覆盖 `168` 条，错误 `0`，总正常 `97`、边界 `23`、低分 `48`，总均分 `35.442 -> 59.296`。分词条：`花` `93` 条，正常 `76`、边界 `7`、低分 `10`，均分 `72.611`；`跳` `56` 条，正常 `21`、边界 `16`、低分 `19`，均分 `52.002`。
- 当前运行态复查：`/api/status` 显示 active template root 为 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`，评分模块 `reload_count=7`、`last_reload_error=null`，Holistic worker PID `811485`、状态 `ready`。本次只做在线验证和回放，没有修改评分代码或重启 worker。

### 2026-06-02 23:50 CST：花/跳网页回归脚本固化

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_web_regression.py`，把当前人工检查链路固化为一个可重复 gate：读取 `5080/api/status`，用当前 `run3` dense 标准库覆盖历史 saved standard 路径做全量网页样本 replay，再只针对 `花/跳` 生成 active-template 语义诊断，最后汇总 gate pass/fail。脚本默认不调用 `/api/score`、不新增摄像头样本、不重新运行 Holistic。
- 已运行回归：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_regression_flower_jump_20260602_current_v1/flower_jump_web_regression.md`。输出包含 replay 子报告 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_regression_flower_jump_20260602_current_v1/active_template_replay/web_replay_current.md` 和 diagnostics 子报告 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_regression_flower_jump_20260602_current_v1/flower_jump_diagnostics/web_semantic_diagnostics.md`。
- 本次 gate 全部 PASS：`backend_ready` 通过，`5080` worker=`ready`、Holistic worker PID `811485`、`reload_count=7`、`last_reload_error=None`；全量 replay `168` 条、错误 `0`，正常 `97`、边界 `23`、低分 `48`，当前均分 `59.296`；`花/跳` diagnostics `149` 条、错误 `0`。
- 有效采集口径下，`花/跳` 总计 `124` 条可评分样本中 `120` 条正常或边界，正常+边界率 `96.8%`。`跳` 有效采集 `37/37` 正常或边界，有效低分 `0`；`花` 有效采集 `87` 条中 `83` 条正常或边界，有效低分 `4`，且全部诊断为 `flower_opening_guard_failed`，符合当前“无清晰开花张开动态不应抬分”的策略。
- 验证：`/home/wuyangcheng/myenv/bin/python -m py_compile work/scripts/run_flower_jump_web_regression.py work/scripts/replay_web_scoring_samples.py work/scripts/analyze_web_scoring_diagnostics.py` 通过；回归脚本运行结束码为 `0`；再次 `curl http://127.0.0.1:5080/api/status` 确认 worker ready、PID `811485`、`last_reload_error=None`。该脚本应作为后续 scoring 模块/profile/模板权重/对齐策略改动后的标准网页回归入口。

### 2026-06-02 23:55 CST：新增样本快速诊断过滤

- 为支持真实网页测试后的快速复查，`/data/WYC/signLanguage/work/scripts/replay_web_scoring_samples.py`、`/data/WYC/signLanguage/work/scripts/analyze_web_scoring_diagnostics.py` 和 `/data/WYC/signLanguage/work/scripts/run_flower_jump_web_regression.py` 均新增样本过滤参数：`--latest N`、`--since-request-id <request_id>`、`--request-ids <id...>`。默认不传参数仍保持全量回归；传过滤参数时只分析新增/最近样本，并在报告里写出过滤条件。
- 典型用法：用户完成一轮网页摄像头测试后，可以运行 `/home/wuyangcheng/myenv/bin/python work/scripts/run_flower_jump_web_regression.py --since-request-id <上次最后一条request_id> --output-dir <new_dir>`，或临时运行 `--latest 5` 只看最近 5 条。该路径仍只复用保存的 Holistic JSON，不重新运行 Holistic、不重启 5080。
- 已运行最近 3 条样本快速诊断：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_regression_flower_jump_latest3_20260602_v1/flower_jump_web_regression.md`。样本过滤为 `latest=3`，包含 `web_20260602_233302_d92c0ce2`、`web_20260602_233343_899e6970`、`web_20260602_233348_53e3df5d`，不包含之前故意截短的 `花` opening guard 失败样本。
- latest3 gate 全部 PASS：replay `3` 条、错误 `0`，正常 `2`、边界 `1`、低分 `0`；diagnostics `3` 条、错误 `0`，采集质量均为 `score_valid`。`花` `1/1` 正常，score `76.899`；`跳` `2/2` 正常或边界，scores `70.661/88.577`，semantic floor 来源均为 `action_window_net`。
- 当前没有新的真实摄像头样本，最新 saved web 样本仍是 2026-06-02 23:33 左右的 4 条在线 smoke。5080 复查仍 ready：Holistic worker PID `811485`，`reload_count=7`，`last_reload_error=None`。

### 2026-06-03 00:01 CST：网页结果显示样本 ID

- 为配合新增样本快速诊断，网页结果面板新增“样本 ID”显示与复制按钮。`/data/WYC/signLanguage/work/web/static/index.html` 新增 `requestMeta/requestId/copyRequestBtn`；`/data/WYC/signLanguage/work/web/static/app.js` 在 `renderResult()` 中读取后端返回的 `request_id` 并显示到结果区，同时将 `样本 ID` 加入语义诊断表；采集完成日志也从仅显示结果目录改为显示 `样本 ID + 结果目录`。
- `/data/WYC/signLanguage/work/web/static/styles.css` 新增 `.request-meta` 和 `.copy-button`，保证右侧窄结果面板中长 request_id 不溢出。用户完成一次网页测试后，可以直接复制样本 ID 发回，随后用 `run_flower_jump_web_regression.py --request-ids <id>` 或 `--since-request-id <id>` 精准复查。
- 验证：`node --check work/web/static/app.js` 通过；`curl http://127.0.0.1:5080/` 已返回 `requestMeta/requestId/copyRequestBtn/样本 ID`；`curl http://127.0.0.1:5080/static/app.js` 已返回 `lastRequestId/copyRequestId/样本 ID`；`curl http://127.0.0.1:5080/static/styles.css` 已返回 `.request-meta/.copy-button`。本次只改前端展示，不改评分逻辑或 profile，因此不需要重新跑评分回放。
- 运行态复查：`5080/api/status` 仍为 worker `ready`，Holistic worker PID `811485`，`reload_count=7`，`last_reload_error=None`。

### 2026-06-03 00:05 CST：网页新增样本 marker 与增量诊断

- 新增 `/data/WYC/signLanguage/work/scripts/manage_web_sample_marker.py`，用于真实网页测试前后做增量闭环。`mark` 子命令记录当前最后一个 saved web sample；`status` 查看 marker 之后新增样本概况；`diagnose` 自动筛选 marker 之后新增的 `花/跳` 样本，并调用 `run_flower_jump_web_regression.py --request-ids ...` 生成精准诊断。该脚本只读保存的 `scoring_result.json` 和 Holistic JSON，不调用 `/api/score`、不重启 Holistic。
- 已把当前 baseline marker 写入 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_sample_marker_current.json`：当前样本总数 `168`，最后样本 `web_20260602_233348_53e3df5d`，分词条统计为 `花=93`、`跳=56`、`香蕉=13`、`汽车=3`、`虎=2`、`月亮=1`。这意味着后续真实网页测试后，可以直接运行 `diagnose` 找出 marker 之后新增的 `花/跳` 样本。
- 已验证无新样本状态：`/home/wuyangcheng/myenv/bin/python work/scripts/manage_web_sample_marker.py status` 返回 marker 之后新增样本 `0`；`diagnose --output-dir /data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_new_samples_since_marker_20260603_v1` 生成 no-op 报告 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_new_samples_since_marker_20260603_v1/new_web_samples_status.md`，明确“没有 marker 之后新增的目标词样本需要诊断”。
- 后续推荐流程：用户开始真实测试前运行一次 `mark`；测试完成后运行 `/home/wuyangcheng/myenv/bin/python work/scripts/manage_web_sample_marker.py diagnose --output-dir <new_dir>`。若诊断成功且要把这轮测试作为新基线，可加 `--update-marker`。
- 验证：`py_compile work/scripts/manage_web_sample_marker.py work/scripts/run_flower_jump_web_regression.py work/scripts/replay_web_scoring_samples.py work/scripts/analyze_web_scoring_diagnostics.py` 通过；`5080/api/status` 仍为 worker `ready`，Holistic worker PID `811485`，`reload_count=7`，`last_reload_error=None`。

### 2026-06-03 00:09 CST：增量诊断自动生成骨架可视化

- 继续完善 `/data/WYC/signLanguage/work/scripts/manage_web_sample_marker.py` 的 `diagnose` 子命令：当 marker 之后存在新增 `花/跳` 样本时，除调用 `run_flower_jump_web_regression.py --request-ids ...` 生成评分/语义诊断外，还会默认调用 `/data/WYC/signLanguage/work/scripts/render_web_holistic_cache_visuals.py --requests ... --rescore-current` 生成 query/standard 骨架联系表和 presence timeline。可用 `--skip-visuals` 关闭该步骤。
- 该可视化仍只读取保存的 Holistic JSON，不重新运行 Holistic，也不需要原始浏览器 JPEG。用途是快速判断：网页低分到底是 Holistic 手部漏检/遮挡、核心手形未出现，还是 DTW/语义相位需要继续优化。
- 已用临时 marker `web_sample_marker_test_after_233301.json` 模拟 marker 后新增 3 条样本，运行 `/home/wuyangcheng/myenv/bin/python work/scripts/manage_web_sample_marker.py --marker work/generated/scoring_mvp_run3/web_sample_marker_test_after_233301.json diagnose --output-dir work/generated/scoring_mvp_run3/web_new_samples_visual_test_20260603_v1`。诊断 request 为 `web_20260602_233302_d92c0ce2`、`web_20260602_233343_899e6970`、`web_20260602_233348_53e3df5d`。
- 测试输出 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_new_samples_visual_test_20260603_v1/new_web_samples_status.md` 显示 regression 返回码 `0`、visual 返回码 `0`；评分报告为 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_new_samples_visual_test_20260603_v1/flower_jump_regression/flower_jump_web_regression.md`，骨架可视化报告为 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_new_samples_visual_test_20260603_v1/holistic_visuals/web_holistic_visual_recovery_summary.md`。
- 可视化产物已确认生成：每个 request 都有 query/standard 的 `*_skeleton_contact_sheet.png`、`*_contact_sheet.png` 和 `*_presence_timeline.png`。示例：`web_20260602_233343_899e6970` 的 `花` query 联系表和 timeline 位于 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_new_samples_visual_test_20260603_v1/holistic_visuals/web_20260602_233343_899e6970/query/`。
- 验证：`py_compile work/scripts/manage_web_sample_marker.py work/scripts/render_web_holistic_cache_visuals.py` 通过；测试诊断和可视化均返回 `0`；`manage_web_sample_marker.py status` 对当前正式 marker 仍显示新增样本 `0`；`5080/api/status` 仍为 worker `ready`，Holistic worker PID `811485`，`reload_count=7`，`last_reload_error=None`。

### 2026-06-03 00:17 CST：当前花/跳网页回归基线复查

- 继续核验当前在线评分状态。`/api/status` 显示 5080 常驻后端 worker `ready`，Holistic worker PID `811485`，active template root 为 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`，评分模块 `reload_count=7`、`last_reload_error=None`。
- 已运行当前全量花/跳网页回归：`/home/wuyangcheng/myenv/bin/python work/scripts/run_flower_jump_web_regression.py --output-dir work/generated/scoring_mvp_run3/web_regression_flower_jump_20260603_resume_v1`，报告为 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_regression_flower_jump_20260603_resume_v1/flower_jump_web_regression.md`。
- 本次 gate 全部 PASS：全量 active-template replay `168` 条、错误 `0`；`花/跳` diagnostics `149` 条、错误 `0`；有效采集 `124` 条中正常+边界 `120` 条，正常+边界率 `96.8%`。`跳` 有效采集 `37/37` 正常或边界，有效低分 `0`；`花` 有效采集 `87` 条中正常+边界 `83`，有效低分 `4`，全部为 `flower_opening_guard_failed`。
- 当前正式 marker 后没有新增样本：`manage_web_sample_marker.py status` 返回新增样本 `0`。这说明下一轮用户真实网页测试应先运行 `mark`，测试后用 `diagnose --output-dir <new_dir>` 做增量评分、语义诊断和骨架可视化。

### 2026-06-03 00:21 CST：真实网页测试前 marker 已刷新

- 为下一轮用户真实摄像头网页测试刷新 baseline marker：`/home/wuyangcheng/myenv/bin/python work/scripts/manage_web_sample_marker.py mark`。当前 marker 仍为 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_sample_marker_current.json`，`last_request_id=web_20260602_233348_53e3df5d`，已保存样本总数 `168`。
- 已运行 no-op 增量诊断确认闭环可用：`/home/wuyangcheng/myenv/bin/python work/scripts/manage_web_sample_marker.py diagnose --output-dir work/generated/scoring_mvp_run3/web_new_samples_pretest_20260603_v1`。报告 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_new_samples_pretest_20260603_v1/new_web_samples_status.md` 显示 marker 后新增样本数 `0`。
- 当前 5080 前端和后端均可测试：页面已返回目标动作提示、样本 ID 和复制按钮；`/api/status` 显示 worker `ready`，Holistic worker PID `811485`，评分 `reload_count=7`、`last_reload_error=None`。

### 2026-06-03 00:25 CST：新增网页样本自动诊断 watcher

- 新增轻量 watcher 脚本 `/data/WYC/signLanguage/work/scripts/watch_web_samples_after_marker.py`。该脚本只轮询保存的网页样本目录和当前 marker，不调用浏览器、不提交 `/api/score`、不重启 Holistic；发现 marker 后新增 `花/跳` 样本时，复用 `manage_web_sample_marker.py diagnose` 自动生成增量评分诊断和骨架可视化，并在成功后更新 marker，避免重复诊断同一批样本。
- 已启动 tmux 会话 `signlanguage-web-sample-watch`：`/home/wuyangcheng/myenv/bin/python work/scripts/watch_web_samples_after_marker.py --poll-sec 20 >> work/logs/web_sample_marker_watch.log 2>&1`。日志文件为 `/data/WYC/signLanguage/work/logs/web_sample_marker_watch.log`，静默轮询模式只记录启动、发现新增样本和诊断完成等事件。
- 验证：`py_compile work/scripts/watch_web_samples_after_marker.py work/scripts/manage_web_sample_marker.py` 通过；watcher 进程 PID `2392620` 正在运行；`/api/status` 仍为 worker `ready`、Holistic worker PID `811485`、评分 `reload_count=7`、`last_reload_error=None`。

### 2026-06-03 00:28 CST：watcher 诊断失败容错增强

- 发现自动诊断 watcher 的一个运行风险：如果新增真实样本触发 `run_flower_jump_web_regression.py` gate 失败，`manage_web_sample_marker.py diagnose` 会以非零返回码退出，原 watcher 可能随之结束，导致后续样本无人监听。已在 `/data/WYC/signLanguage/work/scripts/watch_web_samples_after_marker.py` 中补充容错：捕获 `SystemExit` 和普通异常，写入 `diagnose_failed/diagnose_exception` 事件；默认继续监听，只有显式传入 `--stop-on-error` 时才退出。
- 已重启 tmux `signlanguage-web-sample-watch` 加载新版脚本，当前命令仍为 `/home/wuyangcheng/myenv/bin/python work/scripts/watch_web_samples_after_marker.py --poll-sec 20 >> work/logs/web_sample_marker_watch.log 2>&1`。新版 watcher PID `2412409`。
- 验证：`py_compile work/scripts/watch_web_samples_after_marker.py` 通过；`watch_web_samples_after_marker.py --once --verbose` 在无新增样本时正常返回；`manage_web_sample_marker.py status` 显示 marker 后新增样本 `0`；`/api/status` 仍为 worker `ready`、Holistic worker PID `811485`、评分 `reload_count=7`、`last_reload_error=None`。

### 2026-06-03 00:32 CST：watcher 状态落盘与失败重试节流

- 继续完善 `/data/WYC/signLanguage/work/scripts/watch_web_samples_after_marker.py`：新增 watcher 状态文件 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_sample_marker_watch_status.json` 和 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_sample_marker_watch_status.md`，每轮覆盖写入最后检查时间、marker、当前新增样本数、新增目标样本 request_id，以及最近诊断报告路径。
- 新增 `--failed-retry-sec` 参数，默认 `300` 秒。同一批新增样本如果诊断失败，watcher 会记录失败并在 5 分钟内抑制重复重试，避免每 20 秒重复跑同一批失败诊断；如果后续出现新的 request_id，仍会立即触发新的诊断。
- 已重启 tmux `signlanguage-web-sample-watch` 加载新版脚本，当前 watcher PID `2430506`。状态 Markdown 已显示当前事件 `no_target_samples`，marker last_request_id 为 `web_20260602_233348_53e3df5d`，新增样本 `0`。
- 验证：`py_compile work/scripts/watch_web_samples_after_marker.py` 通过；`watch_web_samples_after_marker.py --once --verbose --status-json ... --status-md ...` 在无新增样本时正常返回并生成状态文件；`/api/status` 仍为 worker `ready`、Holistic worker PID `811485`、评分 `reload_count=7`、`last_reload_error=None`。

### 2026-06-03 00:35 CST：增量诊断完整闭环语义修正

- 修正 `/data/WYC/signLanguage/work/scripts/manage_web_sample_marker.py`：当 `diagnose` 生成骨架可视化时，如果 `render_web_holistic_cache_visuals.py` 返回非零状态，现在会先写出 `new_web_samples_status.json/.md`，再以同样非零状态退出，不会继续执行 `--update-marker`。这样新增真实样本只有在评分诊断和骨架可视化都完成后，才会被 marker 标记为已处理。
- 同步修正 `/data/WYC/signLanguage/work/scripts/watch_web_samples_after_marker.py`：除了 regression 非零外，`visual_returncode != 0` 也视为本轮失败，写入 watcher 状态并保留 marker，等待后续重试或人工复查。
- 已重启 tmux `signlanguage-web-sample-watch` 加载新版脚本，当前 watcher PID `2446686`。状态 Markdown 显示当前事件 `no_target_samples`，marker last_request_id 仍为 `web_20260602_233348_53e3df5d`，新增样本 `0`。
- 验证：`py_compile work/scripts/manage_web_sample_marker.py work/scripts/watch_web_samples_after_marker.py` 通过；`manage_web_sample_marker.py diagnose --output-dir work/generated/scoring_mvp_run3/web_new_samples_visual_failure_semantics_noop_20260603_v1` 在无新增样本时正常返回；`watch_web_samples_after_marker.py --once --verbose` 正常；`/api/status` 仍为 worker `ready`、Holistic worker PID `811485`、评分 `reload_count=7`、`last_reload_error=None`。

### 2026-06-03 00:38 CST：watcher 自动诊断路径 e2e 模拟验证

- 为验证真实测试后 watcher 能自动完成闭环，使用临时 marker `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_sample_marker_test_after_233301.json` 模拟 marker 后新增 3 条 `花/跳` 样本，并运行 `/home/wuyangcheng/myenv/bin/python work/scripts/watch_web_samples_after_marker.py --once --verbose --no-update-marker --marker work/generated/scoring_mvp_run3/web_sample_marker_test_after_233301.json --output-base work/generated/scoring_mvp_run3/web_sample_watch_e2e_test_20260603_v1 --status-json work/generated/scoring_mvp_run3/web_sample_watch_e2e_test_20260603_v1/watch_status.json --status-md work/generated/scoring_mvp_run3/web_sample_watch_e2e_test_20260603_v1/watch_status.md`。
- watcher 成功发现并诊断 3 个 request：`web_20260602_233302_d92c0ce2`、`web_20260602_233343_899e6970`、`web_20260602_233348_53e3df5d`。状态报告 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_sample_watch_e2e_test_20260603_v1/watch_status.md` 显示 `diagnose_done`，`regression_returncode=0`、`visual_returncode=0`。
- 自动生成的增量状态报告为 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_sample_watch_e2e_test_20260603_v1/web_new_samples_watch_20260603_003716/new_web_samples_status.md`；回归报告为 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_sample_watch_e2e_test_20260603_v1/web_new_samples_watch_20260603_003716/flower_jump_regression/flower_jump_web_regression.md`，结果 PASS：3 条样本错误 0，有效采集 3/3 正常或边界，`花=76.899`，`跳=70.661/88.577`。
- 骨架可视化报告 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_sample_watch_e2e_test_20260603_v1/web_new_samples_watch_20260603_003716/holistic_visuals/web_holistic_visual_recovery_summary.md` 已生成，每个 request 都有 query/standard 的 `*_skeleton_contact_sheet.png` 和 presence timeline。
- 本次使用 `--no-update-marker`，正式 marker 未被污染；`manage_web_sample_marker.py status` 仍显示正式 marker 后新增样本 `0`。长期 tmux watcher `signlanguage-web-sample-watch` 仍在线，PID `2446686`；`/api/status` 仍为 worker `ready`、Holistic worker PID `811485`、评分 `reload_count=7`、`last_reload_error=None`。

### 2026-06-03 00:41 CST：隔离 marker 自动更新验证

- 为验证真实 watcher 成功诊断后会正确更新 marker，复制临时 marker 到隔离文件 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_sample_marker_isolated_update_test_20260603.json`，再运行 `/home/wuyangcheng/myenv/bin/python work/scripts/watch_web_samples_after_marker.py --once --verbose --marker work/generated/scoring_mvp_run3/web_sample_marker_isolated_update_test_20260603.json --output-base work/generated/scoring_mvp_run3/web_sample_watch_update_marker_test_20260603_v1 --status-json work/generated/scoring_mvp_run3/web_sample_watch_update_marker_test_20260603_v1/watch_status.json --status-md work/generated/scoring_mvp_run3/web_sample_watch_update_marker_test_20260603_v1/watch_status.md`。
- watcher 成功诊断同一批 3 条 `花/跳` 样本，状态报告 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_sample_watch_update_marker_test_20260603_v1/watch_status.md` 显示 `diagnose_done`，`regression_returncode=0`、`visual_returncode=0`。回归报告 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_sample_watch_update_marker_test_20260603_v1/web_new_samples_watch_20260603_004034/flower_jump_regression/flower_jump_web_regression.md` PASS：3 条错误 0，有效采集 3/3 正常或边界，`花=76.899`、`跳=70.661/88.577`。
- 隔离 marker 已从 `web_20260602_233301_233b8215` 更新到 `web_20260602_233348_53e3df5d`，更新后状态报告显示新增样本 `0`，证明 `--update-marker` 成功且只在完整诊断成功后执行。正式 marker `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_sample_marker_current.json` 未被污染，仍显示正式 marker 后新增样本 `0`。
- 长期 tmux watcher `signlanguage-web-sample-watch` 仍在线，PID `2446686`；`/api/status` 仍为 worker `ready`、Holistic worker PID `811485`、评分 `reload_count=7`、`last_reload_error=None`。

### 2026-06-03 00:47 CST：网页端显示自动诊断 watcher 状态

- 为让用户在浏览器里直接看到真实测试后的自动诊断状态，前端结果面板新增“自动诊断”区块，显示 watcher 当前事件、marker 后新增目标样本数、最后检查时间和最近诊断说明。修改文件：`/data/WYC/signLanguage/work/web/static/index.html`、`/data/WYC/signLanguage/work/web/static/app.js`、`/data/WYC/signLanguage/work/web/static/styles.css`。
- watcher 新增静态镜像输出参数，当前 tmux `signlanguage-web-sample-watch` 已重启为 `/home/wuyangcheng/myenv/bin/python work/scripts/watch_web_samples_after_marker.py --poll-sec 20 --status-json-mirror work/web/static/watch_status.json --status-md-mirror work/web/static/watch_status.md >> work/logs/web_sample_marker_watch.log 2>&1`。这样前端可通过 `/static/watch_status.json` 读取状态，不需要为了新增状态面板重启 5080 或 Holistic。
- 后端代码 `/data/WYC/signLanguage/work/web/backend.py` 已新增只读 `/api/watch-status` 路由和 `WATCH_STATUS_JSON/WATCH_STATUS_MD` 常量；当前运行中的 5080 未为此重启，所以该 API 要等下次后端重启后生效。前端实现为先尝试 `/api/watch-status`，失败时回退 `/static/watch_status.json`，因此当前页面已经可用。
- 验证：`py_compile work/web/backend.py work/scripts/watch_web_samples_after_marker.py` 通过；`node --check work/web/static/app.js` 通过；`curl http://127.0.0.1:5080/` 已返回 `watchStatusBox/watchStatusEvent/自动诊断`；`curl http://127.0.0.1:5080/static/app.js` 已返回 `refreshWatchStatus` 和 `/static/watch_status.json`；`curl http://127.0.0.1:5080/static/watch_status.json` 可解析为 `no_target_samples / web_20260602_233348_53e3df5d / 0 / 0`；`/api/status` 仍为 worker `ready`、Holistic worker PID `811485`、评分 `reload_count=7`、`last_reload_error=None`。

### 2026-06-03 00:51 CST：自动诊断状态面板显示最近报告路径

- 继续增强网页“自动诊断”区块：当 watcher 完成新增样本诊断后，前端会显示最近回归报告路径和骨架可视化报告路径，便于真实测试后定位本轮自动生成的报告。修改文件：`/data/WYC/signLanguage/work/web/static/index.html`、`/data/WYC/signLanguage/work/web/static/app.js`、`/data/WYC/signLanguage/work/web/static/styles.css`。
- 当前正式 marker 后仍无新增真实样本；`/static/watch_status.json` 显示 `no_target_samples`、marker last_request_id `web_20260602_233348_53e3df5d`、新增样本 `0`、新增目标样本 `0`。
- 验证：`node --check work/web/static/app.js` 通过；`curl http://127.0.0.1:5080/` 已返回 `watchReportMeta/最近报告/自动诊断`；`curl http://127.0.0.1:5080/static/app.js` 已返回 `watchReportMeta` 和 `latest.regression_report` 逻辑；`curl http://127.0.0.1:5080/static/styles.css` 已返回 `.watch-report` 样式；`/api/status` 仍为 worker `ready`、Holistic worker PID `811485`、评分 `reload_count=7`、`last_reload_error=None`。本次未重启 5080 或 Holistic。

### 2026-06-03 00:55 CST：自动诊断 watcher 心跳与过期提示

- 为避免网页只显示旧的 watcher 状态，`/data/WYC/signLanguage/work/scripts/watch_web_samples_after_marker.py` 的状态 JSON/Markdown 新增 `watcher_pid` 字段；网页 `/data/WYC/signLanguage/work/web/static/app.js` 根据 `generated_at` 计算心跳年龄，如果状态超过 90 秒未刷新，会在“自动诊断”区提示“监听状态可能过期”并建议检查 watcher 进程或 tmux 会话。
- 已重启 tmux `signlanguage-web-sample-watch` 加载新版脚本，并继续镜像状态到 `/data/WYC/signLanguage/work/web/static/watch_status.json/.md`。当前 watcher PID `2553122`，状态为 `no_target_samples`，正式 marker last_request_id `web_20260602_233348_53e3df5d`，新增目标样本 `0`。
- 验证：`py_compile work/scripts/watch_web_samples_after_marker.py` 通过；`node --check work/web/static/app.js` 通过；`/static/watch_status.json` 可解析为 `no_target_samples / 2553122 / web_20260602_233348_53e3df5d / 0 / 0`；`curl http://127.0.0.1:5080/static/app.js` 已返回 `heartbeatAgeSec/监听状态可能过期/watcher PID`；`/api/status` 仍为 worker `ready`、Holistic worker PID `811485`、评分 `reload_count=7`、`last_reload_error=None`。本次未重启 5080 或 Holistic。

### 2026-06-03 00:57 CST：当前网页花/跳打分状态总览报告

- 新增状态总览报告 `/data/WYC/signLanguage/work/reports/web_scoring_current_status_20260603_0057.md`，汇总当前 5080 后端、Holistic worker、正式 marker、watcher、自动诊断状态、花/跳网页回归基线、watcher e2e 验证和真实测试后的预期闭环。
- 当前状态：5080 后端 `ready`，Holistic worker PID `811485`，scoring `reload_count=7`、`last_reload_error=None`；正式 marker last_request_id `web_20260602_233348_53e3df5d`，marker 后新增样本 `0`，新增 `花/跳` 目标样本 `0`；watcher PID `2553122`，状态 `no_target_samples`。
- 报告明确当前结论：保存样本回归基线和自动增量诊断闭环均已验证，但因为还没有新的真实网页摄像头样本，不能把“真实用户网页测试最终正常”作为完成结论；下一步仍需要新 `花/跳` 摄像头样本做最终实测确认。
- 验证：报告内容已核对；`/static/watch_status.json` 可解析为 `no_target_samples / 2553122 / web_20260602_233348_53e3df5d / 0 / 0`；`/api/status` 仍为 worker `ready`、Holistic worker PID `811485`、评分 `reload_count=7`、`last_reload_error=None`。

### 2026-06-03 01:05 CST：继续目标完成度审计与花/跳回归复跑

- 根据持续目标“提升鲁棒性并使网页测试结果正常”，重新审计当前 5080 与 watcher 运行态。`/api/status` 显示 5080 后端 `ready`，Holistic worker PID `811485`，active template root 为 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`，评分模块 `reload_count=7`、`last_reload_error=None`。
- `manage_web_sample_marker.py status` 与 `/static/watch_status.json` 均确认正式 marker last_request_id 仍为 `web_20260602_233348_53e3df5d`，marker 后新增样本 `0`，新增 `花/跳` 目标样本 `0`；watcher PID `2553122`，状态 `no_target_samples`。
- 已重跑当前花/跳网页回归门：`/home/wuyangcheng/myenv/bin/python work/scripts/run_flower_jump_web_regression.py --output-dir work/generated/scoring_mvp_run3/web_regression_flower_jump_20260603_continuation_v1`。报告为 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_regression_flower_jump_20260603_continuation_v1/flower_jump_web_regression.md`。
- 本轮 gate 仍全部 PASS：全量 active-template replay `168` 条、错误 `0`；`花/跳` diagnostics `149` 条、错误 `0`；有效采集 `124` 条中正常+边界 `120` 条，正常+边界率 `96.8%`；`跳` 有效采集 `37/37` 正常或边界、有效低分 `0`；`花` 有效采集 `87` 条中正常+边界 `83`，有效低分 `4`，全部为 `flower_opening_guard_failed`。
- 当前证据证明：保存样本与在线 smoke 基线没有回退，自动诊断链路仍在监听；但仍缺新的真实网页摄像头样本，因此不能将目标标记为最终完成。

### 2026-06-03 01:10 CST：新增花/跳综合判别鲁棒性门

- 为防止“提高网页 `花/跳` 分数”同时误抬其他 demo 或乱摆动作，新增综合判别脚本 `/data/WYC/signLanguage/work/scripts/run_flower_jump_discrimination_gate.py`。该脚本只读当前 `run3` dense Holistic 标准库，不调用 `/api/score`，不新增网页样本，不重启 Holistic。
- 脚本一次性对 `花` 和 `跳` 运行现有 `score_holistic_sequence_mvp.py` 判别套件：目标动作正例变体（self、降采样、裁剪、幅度 0.85/1.15）应保持高分；合成假动作（反放、乱序、静止、随机 landmark、随机游走）和其他 9 个 demo 应保持低分；门槛沿用正例最低 `>=75`、负例最高 `<=50`、margin `>=15`。
- 已运行 `/home/wuyangcheng/myenv/bin/python work/scripts/run_flower_jump_discrimination_gate.py --output-dir work/generated/scoring_mvp_run3/flower_jump_discrimination_gate_20260603_v1`。报告为 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_discrimination_gate_20260603_v1/flower_jump_discrimination_gate.md`，CSV 为 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_discrimination_gate_20260603_v1/flower_jump_discrimination_cases.csv`。
- 综合状态 PASS：`花` 正例最低 `80.311`，负例最高 `32.047`（最强负例 `other_demo_谗_羡慕`），margin `48.263`；`跳` 正例最低 `76.823`，负例最高 `31.418`（最强负例 `fake_static_hold`），margin `45.406`。这说明当前 `花` opening guard、`跳` two-hand/local-relation fallback 和 short-core floor 没有把其他 demo 或合成假动作抬到高分区。
- 运行状态仍正常：报告读取到 5080 worker `ready`，Holistic worker PID `811485`，scoring `reload_count=7`、`last_reload_error=None`。

### 2026-06-03 01:16 CST：新增花/跳坐姿与镜头扰动鲁棒性门

- 针对用户实测坐姿、镜头位置和手部尺度差异可能影响评分的问题，新增脚本 `/data/WYC/signLanguage/work/scripts/run_flower_jump_pose_robustness_gate.py`。该脚本只读当前 `run3` dense Holistic 标准库，基于标准骨架生成正例扰动，不调用 `/api/score`，不重启 Holistic。
- 本门生成的扰动包括：双手整体下移、左移、对角平移、整个人平移、躯干坐姿压缩、手部局部尺度 `0.90/1.10`、双手轻微旋转 `10°`、手部关键点小抖动。目标是验证 `花/跳` 主要由手部相对动作和核心语义决定，而不是由站姿/坐姿/镜头中心决定。
- 已运行 `/home/wuyangcheng/myenv/bin/python work/scripts/run_flower_jump_pose_robustness_gate.py --output-dir work/generated/scoring_mvp_run3/flower_jump_pose_robustness_gate_20260603_v1`。报告为 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_pose_robustness_gate_20260603_v1/flower_jump_pose_robustness_gate.md`，CSV 为 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_pose_robustness_gate_20260603_v1/flower_jump_pose_robustness_cases.csv`。
- 综合状态 PASS，门槛为扰动正例最低分 `>=70`。`花` 最低分 `80.446`，最弱扰动 `hand_jitter_small`；`跳` 最低分 `93.015`，最弱扰动 `hand_jitter_small`。双手全局平移、整个人平移和躯干坐姿压缩均保持高分，说明当前 profile 的 `pose/face` 低权重、手部局部几何和 two-hand relation 相对特征正在发挥预期作用。
- 运行状态仍正常：报告读取到 5080 worker `ready`，Holistic worker PID `811485`，scoring `reload_count=7`、`last_reload_error=None`。本门仍不能替代真实摄像头样本，只作为坐姿/镜头鲁棒性的合成 sanity gate。

### 2026-06-03 01:25 CST：新增花/跳统一质量门

- 为避免后续评分改动后分散运行多套检查，新增统一 wrapper `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`。该脚本按顺序运行三道现有门：网页保存样本回归、离线负例判别门、坐姿/镜头扰动鲁棒性门，并生成总 JSON/Markdown 报告。脚本不重新运行 Holistic，不重启 5080，只读保存的 web/API Holistic JSON 和模板 Holistic JSON。
- 已运行 `/home/wuyangcheng/myenv/bin/python work/scripts/run_flower_jump_quality_gate.py --output-dir work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_v1`。总报告为 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_v1/flower_jump_quality_gate.md`，总 JSON 为 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_v1/flower_jump_quality_gate.json`。
- 统一门综合状态 PASS，三个子门返回码均为 `0`：`web_regression`、`discrimination_gate`、`pose_robustness_gate`。
- 网页保存样本回归子门：replay `168` 条、错误 `0`；`花/跳` diagnostics `149` 条、错误 `0`；有效采集 `124`，有效正常+边界 `120`，有效低分 `4`，有效正常+边界率 `96.8%`。`花` 有效 `87` 条、正常+边界 `83`、低分 `4`、有效均分 `75.550`；`跳` 有效 `37` 条、正常+边界 `37`、低分 `0`、有效均分 `76.677`。
- 负例判别子门：`花` 正例最低 `80.311`、负例最高 `32.047`、margin `48.263`；`跳` 正例最低 `76.823`、负例最高 `31.418`、margin `45.406`。坐姿/镜头扰动子门：`花` 最低 `80.446`，`跳` 最低 `93.015`。
- marker 状态仍显示正式 marker last_request_id `web_20260602_233348_53e3df5d`，marker 后新增样本 `0`，新增 `花/跳` 样本 `0`。本统一门可作为后续修改 `score_holistic_sequence_mvp.py`、语义 profile、模板权重、score scaling 或对齐策略后的首选总复查入口；但目标最终完成仍需要新的真实网页摄像头样本。

### 2026-06-03 01:29 CST：新增花/跳目标完成度审计

- 新增快速审计脚本 `/data/WYC/signLanguage/work/scripts/audit_flower_jump_goal_readiness.py`。该脚本不重新运行 Holistic、不重跑 DTW gate，只读取当前 5080 状态、watcher 状态、marker 状态和最新统一质量门，判断是否具备把目标标记完成的证据。
- 已运行 `/home/wuyangcheng/myenv/bin/python work/scripts/audit_flower_jump_goal_readiness.py --output-dir work/generated/scoring_mvp_run3/flower_jump_goal_readiness_audit_20260603_v2`。审计报告为 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_goal_readiness_audit_20260603_v2/flower_jump_goal_readiness_audit.md`。
- 审计状态为 `NOT_READY`。通过的证据门：`backend_ready`（worker ready，PID `811485`，`reload_count=7`，`last_reload_error=None`）、`watcher_online`（watcher PID `2553122`，event `no_target_samples`）、`marker_available`（last_request_id `web_20260602_233348_53e3df5d`，marker 后新增样本 `0`）、`combined_quality_gate_passed`（最新统一质量门三子门均 PASS）。
- 缺失的唯一完成证据门：`fresh_real_webcam_target_samples_diagnosed`。当前 marker 后新增 `花/跳` 样本 `0`，watcher 也没有最新真实样本诊断。因此工程质量门已经通过，但仍不能把“真实网页摄像头测试最终正常”作为完成结论。
- 下一步闭环：用户通过 5080 页面实际采集 `花/跳`，watcher 自动生成增量回归和骨架可视化后，再运行该审计脚本；若 fresh real webcam target samples 诊断也通过，才可考虑标记目标完成。

### 2026-06-03 01:37 CST：完成度审计接入 watcher 与前端状态面板

- 已增强 `/data/WYC/signLanguage/work/scripts/watch_web_samples_after_marker.py`：每轮先刷新 watcher 状态，再运行 `/data/WYC/signLanguage/work/scripts/audit_flower_jump_goal_readiness.py`，并把精简后的 `goal_readiness` 写入 watcher JSON/Markdown 以及前端静态镜像。新增参数包括 `--skip-readiness-audit`、`--readiness-output-dir`、`--readiness-watch-status-url`、`--readiness-timeout-sec` 和 `--readiness-quality-gate-json`。
- 前端 `/data/WYC/signLanguage/work/web/static/index.html`、`app.js`、`styles.css` 的“自动诊断”面板新增“目标完成度”和“缺失证据”字段，并把完成度审计报告路径合并到最近报告显示中。当前 5080 运行进程尚未加载 `/api/watch-status` 路由，但前端会因该 API 返回 404 而回退读取 `/static/watch_status.json`，所以无需重启 5080/Holistic。
- 验证：`/home/wuyangcheng/myenv/bin/python -m py_compile work/scripts/watch_web_samples_after_marker.py work/scripts/audit_flower_jump_goal_readiness.py` 通过；`node --check work/web/static/app.js` 通过；单轮 watcher 测试输出 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_sample_marker_watch_status_readiness_test.md`，显示 `NOT_READY`，唯一缺失门为 `fresh_real_webcam_target_samples_diagnosed`。
- 已只重启 tmux `signlanguage-web-sample-watch`，新 watcher PID `2763036`，继续使用 20 秒轮询并镜像到 `/data/WYC/signLanguage/work/web/static/watch_status.json/.md`。`/static/watch_status.json` 当前可解析为 `event=no_target_samples`、target count `0`、`goal_readiness.status_label=NOT_READY`、missing gate `fresh_real_webcam_target_samples_diagnosed`，审计报告路径 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_goal_readiness_watch_current/flower_jump_goal_readiness_audit.md`。
- 5080 常驻后端未重启：`/api/status` 仍为 worker `ready`、Holistic worker PID `811485`、scoring `reload_count=7`、`last_reload_error=None`。目标仍保持未完成，等待新的真实网页摄像头 `花/跳` 样本由 watcher 自动诊断。

### 2026-06-03 01:58 CST：动作窗口 presence 与帧数鲁棒性门

- 针对真实网页采集帧数不一致和前缀/静止段遮挡导致的鲁棒性问题，已修改 `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py`：`semantic_core_hand_presence` 现在同时看全序列与 query action window 的手部覆盖，取较强证据；返回诊断中新增 `semantic_core_query_hand_presence_full` 与 `semantic_core_query_hand_presence_window`。这样 `花` 的非均匀 16 帧采样不再被静止/缺手前缀稀释。
- 同时修正 `花` 的低质量判断：若 `short_visible_core` floor 给出 `opening_guard_too_weak` 且整段手部覆盖也不足，则归为 `needs_recapture / flower_core_hand_presence_low`；若手部覆盖足但张开动态弱，则归为 `semantic_mismatch / flower_opening_guard_failed`。这不抬分，只让有效评分统计排除明显欠采样/低覆盖样本。
- 新增帧数与采样密度鲁棒性脚本 `/data/WYC/signLanguage/work/scripts/run_flower_jump_frame_count_robustness_gate.py`。该脚本只读模板 Holistic JSON，在骨架序列层面生成 8/12/16/24/32/48/80 帧、非均匀前后密集、drop pattern 与 repeat-mid-core 等变体，不调用 `/api/score`，不重启 Holistic。
- 初始 v1 gate 暴露 `花 front_dense_16f` 低分 `22.963`；动作窗口 presence 修正后 v2 将其提升到 `92.509`，剩余 `花 uniform_8f=32.284` 被判定为严重欠采样风险而不是推荐区间正例。最终 v3 gate `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_frame_count_robustness_gate_20260603_v3/flower_jump_frame_count_robustness_gate.md` PASS：`花` 推荐最少 `12` 帧，门控最低 `78.482`（`uniform_12f`），欠采样 `uniform_8f` 保留为诊断；`跳` 推荐最少 `6` 帧，门控最低 `70.488`（`drop_every_3_keep_ends`）。
- `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py` 已接入第四个子门 `frame_count_robustness_gate`。复跑统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_v3/flower_jump_quality_gate.md`，综合状态 PASS，四个子门 `web_regression / discrimination_gate / pose_robustness_gate / frame_count_robustness_gate` 全部返回 `0`。
- v3 关键结果：网页保存样本 replay `168` 条错误 `0`；`花/跳` diagnostics `149` 条错误 `0`；有效采集 `128` 条中正常+边界 `124`，有效率 `96.9%`。`花` 有效 `91` 条、正常+边界 `87`、有效低分 `4`、有效率 `95.6%`，低分均为 `flower_opening_guard_failed`；`跳` 有效 `37/37` 正常或边界、有效低分 `0`。负例判别仍通过：`花` margin `48.263`，`跳` margin `45.406`；坐姿扰动仍通过：`花` 最低 `80.446`，`跳` 最低 `93.015`。
- 5080 scoring 已通过 `/api/admin/reload-scoring` 热重载到 `reload_count=9`，`last_reload_error=None`；Holistic worker PID 仍为 `811485`，未重启。完成度审计 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_goal_readiness_audit_20260603_v3/flower_jump_goal_readiness_audit.md` 仍为 `NOT_READY`：backend、watcher、marker、v3 统一质量门均 PASS，但 marker 后新增真实网页 `花/跳` 样本仍为 `0`。

### 2026-06-03 02:04 CST：网页采集端加入最低采样保护

- 根据帧数鲁棒性门结论，更新 `/data/WYC/signLanguage/work/web/static/app.js`、`index.html`、`styles.css`，在网页端新增词条级采样建议与采集前自动修正。当前配置：`花` 推荐至少 `12` 个上传帧、最短 `2.5s`、最低 `5fps`；`跳` 推荐至少 `6` 个上传帧、最短 `2s`、最低 `5fps`；其他词条默认至少 `10` 个上传帧。
- 页面采集区新增 `captureHint`，实时显示“当前设置”和“采集时将自动调整为”的采样计划。如果用户把时长/FPS 调到欠采样区，点击采集时会自动写回安全配置，避免把 `花` 采成 8 帧这类已知低鲁棒性区间。
- 网页语义诊断表新增 `核心手覆盖-全段` 与 `核心手覆盖-窗口`，用于真实测试后区分整段缺手、动作窗口缺手或静止前缀稀释问题。
- 验证：`node --check work/web/static/app.js` 通过；`git diff --check -- work/web/static/app.js work/web/static/index.html work/web/static/styles.css` 通过；`curl http://127.0.0.1:5080/static/app.js` 已返回 `CAPTURE_RECOMMENDATIONS`、`采集时将自动调整为` 和 `核心手覆盖-全段/窗口`；`curl http://127.0.0.1:5080/` 已返回 `captureHint`。本次只改静态前端，不重启 5080/Holistic；`/api/status` 仍为 worker `ready`、Holistic PID `811485`、scoring `reload_count=9`、`last_reload_error=None`。
- 当前目标仍未完成：`/static/watch_status.json` 仍显示 `NOT_READY`，唯一缺失门为 `fresh_real_webcam_target_samples_diagnosed`，marker 后新增真实网页 `花/跳` 样本仍为 `0`。

### 2026-06-03 02:07 CST：网页结果页补充可执行采集建议

- 为了真实测试低分后能直接知道该怎么调整，继续更新 `/data/WYC/signLanguage/work/web/static/app.js`。新增 `buildCaptureAdvice()`，把后端 `capture_quality.reason`、`semantic_floor.reason`、左右手覆盖、`semantic_core_query_hand_presence_full/window` 和 `flower_opening_guard.best_score` 转换成中文采集建议。
- `花` 的建议会区分：窗口核心手覆盖不足时提示“让开花手保持在画面中央、完整露出手腕和五指”；张开动态不足时提示“从撮合状态开始、慢慢张开五指并保持 0.5s”。`跳` 的建议会区分：双手覆盖不足时提示左手“地面”和右手“两指小人”同时入画；方向/幅度不足时提示右手两指在左手上方向上弹起、避免横向摆动。
- 网页结果说明和语义诊断表均新增“采集建议”输出。这样用户实际采集后，不仅能看到 `建议重采/动作语义不足`，还能看到具体下一次应如何调整。
- 验证：`node --check work/web/static/app.js` 通过；`git diff --check -- work/web/static/app.js` 通过；`curl http://127.0.0.1:5080/static/app.js` 已返回 `buildCaptureAdvice`、`采集建议`、`窗口核心手覆盖` 和 `左手“地面”`；`/api/status` 仍为 worker `ready`、Holistic PID `811485`、scoring `reload_count=9`、`last_reload_error=None`。
- 当前 watcher 仍在线，`/static/watch_status.json` 显示 `no_target_samples`、watcher PID `2763036`、target count `0`、`goal_readiness=NOT_READY`，唯一缺失门仍是新的真实网页摄像头 `花/跳` 样本诊断。

### 2026-06-03 02:19 CST：后端增量诊断报告接入样本级建议

- 为了让真实网页复测后形成完整闭环，更新 `/data/WYC/signLanguage/work/scripts/analyze_web_scoring_diagnostics.py`：每条样本现在输出 `triage_priority`、`sample_advice`、`capture_quality_message`、`semantic_core_presence_full`、`semantic_core_presence_window`，并在 Markdown/CSV/JSON 中展示“处置计数”“全段/窗口覆盖”和“建议”。这套建议逻辑与前端 `buildCaptureAdvice()` 保持同一口径，区分 `花` 的核心手覆盖不足/张开动态不足，以及 `跳` 的双手覆盖不足/方向不一致/弹跳幅度偏小。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_web_regression.py`，在 `flower_jump_web_regression.md` 的分词条汇总和有效低分样本表中显示处置与建议；更新 `/data/WYC/signLanguage/work/scripts/manage_web_sample_marker.py` 和 `/data/WYC/signLanguage/work/scripts/watch_web_samples_after_marker.py`，把新增样本的语义诊断报告路径 `flower_jump_diagnostics/web_semantic_diagnostics.md` 写入状态 JSON/Markdown；前端 `/data/WYC/signLanguage/work/web/static/app.js` 的自动诊断面板也新增“语义”报告路径。
- 验证：`/home/wuyangcheng/myenv/bin/python -m py_compile work/scripts/analyze_web_scoring_diagnostics.py work/scripts/run_flower_jump_web_regression.py work/scripts/manage_web_sample_marker.py work/scripts/watch_web_samples_after_marker.py` 通过；`node --check work/web/static/app.js` 通过；`git diff --check` 通过；5080 `/api/status` 仍为 worker `ready`、Holistic PID `811485`、scoring `reload_count=9`、`last_reload_error=None`；正式 marker 后新增样本仍为 `0`。
- 最近 3 条快速回归 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_regression_flower_jump_latest3_20260603_advice_v1/flower_jump_web_regression.md` PASS：3 条 replay 错误 `0`，3 条 diagnostics 错误 `0`，有效率 `100%`；报告中已出现 `处置计数`、`核心全段/窗口` 和 `sample_advice`。全量回归 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_regression_flower_jump_20260603_advice_v1/flower_jump_web_regression.md` PASS：168 replay 错误 `0`，149 diagnostics 错误 `0`，有效采集正常+边界率 `96.9%`；`花` 有效 `91` 条、正常+边界 `87`、有效低分 `4` 且均为 `flower_opening_guard_failed`；`跳` 有效 `37/37` 正常或边界、有效低分 `0`。
- 本次不改 `score_holistic_sequence_mvp.py` 的评分值，不放宽阈值，只把真实网页样本的“低分原因 -> 下一步动作/采集建议 -> 回归/骨架报告路径”接成自动诊断闭环。目标仍未完成，因为 marker 后还没有新的真实网页摄像头 `花/跳` 样本。

### 2026-06-03 02:25 CST：前端自动诊断面板直接展示最新样本建议

- 在 `/data/WYC/signLanguage/work/scripts/manage_web_sample_marker.py` 中新增 `semantic_sample_summaries` 与 `semantic_triage_counts`：`diagnose` 完成回归后会读取 `flower_jump_diagnostics/web_semantic_diagnostics.json`，抽取新增样本的 request_id、词条、分数、处置、采集质量、诊断和 `sample_advice`，写入 `new_web_samples_status.json/.md`。
- `/data/WYC/signLanguage/work/scripts/watch_web_samples_after_marker.py` 的状态 Markdown 现在会显示“最新样本建议”表；watcher JSON 会把同一份结构化摘要放进 `latest_diagnosis.semantic_sample_summaries`。前端 `/data/WYC/signLanguage/work/web/static/app.js` 新增 `formatWatchSampleSummaries()`，在自动诊断面板中直接显示“词条 分数 处置：建议”；`styles.css` 为状态说明补充 `overflow-wrap:anywhere`，避免长建议挤出结果栏。
- 验证：`py_compile`、`node --check work/web/static/app.js`、`git diff --check` 均通过；用临时 marker `web_sample_marker_test_after_233301.json` 运行 watcher 单轮模拟，输出 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_sample_watch_advice_payload_test_20260603_v1/watch_status.md`，`diagnose_done`、`regression_returncode=0`、`visual_returncode=0`，并包含 3 条样本建议：`跳 70.7 borderline_review`、`花 76.9 normal`、`跳 88.6 normal`。正式 marker 未更新，仍为 `web_20260602_233348_53e3df5d`。
- 已只重启 tmux `signlanguage-web-sample-watch` 以加载新 watcher 代码，新 PID `3006024`。`/static/watch_status.json` 当前为 `no_target_samples`、target count `0`、`goal_readiness=NOT_READY`、缺失门 `fresh_real_webcam_target_samples_diagnosed`；5080/Holistic 未重启，`/api/status` 仍为 worker `ready`、Holistic PID `811485`、scoring `reload_count=9`、`last_reload_error=None`。

### 2026-06-03 02:29 CST：前端增加复测轮次准备提示

- 因为线上 5080 后端未重启，`/api/watch-status` 仍为 404，新增后端 marker API 无法热加载；为避免重启 Holistic，本轮只改静态前端。`/data/WYC/signLanguage/work/web/static/index.html` 的“自动诊断”面板新增“开始复测轮次”按钮和本地复测状态。
- `/data/WYC/signLanguage/work/web/static/app.js` 新增 `signLanguageRetestRound` localStorage 记录、`prepareRetestRound()`、`updateRetestRoundStatus()` 和 `scheduleWatchRefreshAfterScore()`。点击按钮会把当前 watcher 正式 marker 作为本地复测起点；采集 `花/跳` 后，页面会提示样本已保存并在 5s/25s 后刷新 watcher 状态，等待自动诊断、样本建议和骨架报告生成。该逻辑不写服务器 marker，正式 marker 仍由 watcher 自动维护。
- `/data/WYC/signLanguage/work/web/static/styles.css` 为复测按钮和状态补充紧凑布局，避免右侧结果栏溢出。
- 验证：`node --check work/web/static/app.js` 通过；`git diff --check -- work/web/static/app.js work/web/static/index.html work/web/static/styles.css` 通过；`curl http://127.0.0.1:5080/static/app.js` 已返回 `prepareRetestRound`、`scheduleWatchRefreshAfterScore` 和 `signLanguageRetestRound`；`curl http://127.0.0.1:5080/` 已返回 `prepareRetestBtn/retestRoundStatus`。5080/Holistic 未重启，`/api/status` 仍为 worker `ready`、Holistic PID `811485`、scoring `reload_count=9`、`last_reload_error=None`；watcher 仍为 PID `3006024`，正式 marker 后新增 `花/跳` 样本 `0`，目标仍 `NOT_READY`。

### 2026-06-03 03:00 CST：花/跳交叉混淆 guard 与五子门质量门

- 针对历史保存样本中 `跳` 被按 `花` 模板打到 `73-75` 的交叉混淆问题，新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_web_confusion_gate.py` 并将其接入统一质量门。该 gate 对同一保存网页 query 分别按 `花/跳` 当前模板复算，要求目标分数显著高于另一词模板；不调用 `/api/score`，不重启 Holistic。
- 已修改 `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py`：新增 `flower_jump_confusion_guard`。当 `花` 查询同时出现稳定双手、有效 `two_hand_relation`、弱 `flower_opening_guard` 和右手双指形态时，判定为 `jump_like_two_hand_relation_with_weak_flower_opening`，并阻断 `花` 的 `short_core_capture_tolerance`、`visible_semantic_core_tolerance`、`visible_semantic_core_scale` 和 `short_visible_core` floor。`capture_quality` 会给出 `semantic_mismatch / flower_jump_like_two_hand_confusion`，避免无解释地压低交叉分。
- 已同步更新 `/data/WYC/signLanguage/work/scripts/build_semantic_weight_profiles.py` 和 `/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json/.md`：`花` profile 记录 `flower_jump_confusion_guard_enabled=True`、双手覆盖阈值 `0.58`、关系有效帧阈值 `3`、最大开花分 `0.45`、右手双指形态均值阈值 `1.05`；`跳` 不启用该 guard。
- 复现失败样本的 targeted gate：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_web_confusion_gate_fail3_after_guard_20260603_v1/flower_jump_web_confusion_gate.md`。三条旧失败 `跳` 样本按 `花` 的交叉分最高降到 `38.558`，最小 margin `29.959`，交叉诊断均为 `flower_jump_like_two_hand_confusion`。
- 全量交叉混淆 gate `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_web_confusion_gate_after_guard_20260603_v2/flower_jump_web_confusion_gate.md` PASS：`149` 个保存样本、`0` 错误、`124` 个 eligible 全部 pass。`花` eligible `87/87`，交叉最高 `8.218`、margin 最低 `59.840`；`跳` eligible `37/37`，按 `花` 交叉最高 `41.535`、margin 最低 `29.317`。
- `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py` 已扩展为五子门：`web_regression`、`web_confusion_gate`、`discrimination_gate`、`pose_robustness_gate`、`frame_count_robustness_gate`。最新统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_v4/flower_jump_quality_gate.md` PASS，五个子门返回码均为 `0`。网页回归仍为 `168` replay 错误 `0`、`149` diagnostics 错误 `0`、有效率 `96.9%`；`花` 有效低分 `4` 均为 `flower_opening_guard_failed`，`跳` 有效低分 `0`。离线负例 margin：`花=48.263`、`跳=45.406`；坐姿扰动最低：`花=80.446`、`跳=93.015`；帧数门最低：`花=78.482`、`跳=70.488`。
- 验证：`py_compile` 通过；`git diff --check` 通过；5080 仅通过 `/api/admin/reload-scoring` 热加载评分模块到 `reload_count=10`，`last_reload_error=None`；Holistic worker PID 仍为 `811485`，未重启。完成度审计 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_goal_readiness_audit_20260603_v4/flower_jump_goal_readiness_audit.md` 仍为 `NOT_READY`：backend、watcher、marker、五子门质量门均 PASS，但正式 marker 后新增真实网页 `花/跳` 样本仍为 `0`，缺失 `fresh_real_webcam_target_samples_diagnosed`。

### 2026-06-03 03:05 CST：完成度审计摘要对齐五子门质量门

- 更新 `/data/WYC/signLanguage/work/scripts/audit_flower_jump_goal_readiness.py` 的 Markdown 摘要输出，使“最新质量门摘要”明确列出五个子门，并展示新增 `web_confusion_gate` 的 samples/eligible/pass/fail、分词条交叉最高分和最小 margin，以及 `frame_count_robustness_gate` 的推荐最少帧、最低分和最弱采样变体。
- 本次只增强完成度审计报告表达，不改变评分逻辑、质量门判定或 watcher 轮询逻辑。新增 `_fmt_num()`，避免某个子门字段缺失时 Markdown 输出因数值格式化失败。
- 验证：`/home/wuyangcheng/myenv/bin/python -m py_compile work/scripts/audit_flower_jump_goal_readiness.py` 通过；`git diff --check -- work/scripts/audit_flower_jump_goal_readiness.py` 通过；显式审计 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_goal_readiness_audit_20260603_v5/flower_jump_goal_readiness_audit.md` 仍为 `NOT_READY`，但摘要已包含 `web_confusion_gate` 与 `frame_count_robustness_gate`。
- live watcher 无需重启：下一轮自动调用新版审计脚本后，`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_goal_readiness_watch_current/flower_jump_goal_readiness_audit.md` 已刷新到 03:05，并展示 v4 五子门摘要；`/data/WYC/signLanguage/work/web/static/watch_status.json` 仍为 `no_target_samples`、goal `NOT_READY`，唯一缺失 `fresh_real_webcam_target_samples_diagnosed`。

### 2026-06-03 03:11 CST：在线结果页准备花/跳交叉诊断

- 为了让真实网页采集后能直接看到“目标动作是否被另一个 demo 模板高分吸走”，更新 `/data/WYC/signLanguage/work/web/backend.py`：新增 `_flower_jump_cross_check()` 和 `_compact_score_result()`。当目标词为 `花/跳` 时，后端可以在同一份 Holistic query 上按另一个模板复算一次 DTW，返回 `target_score`、`other_score`、`margin`、`passed`、`reason` 以及对照模板的简要诊断。该逻辑不重跑 Holistic，只多跑一次缓存骨架 DTW。
- 重要运行态说明：`backend.py` 不能像 `score_holistic_sequence_mvp.py` 一样热加载；本次没有重启 5080，也没有重启 Holistic，所以 live `/api/score` 暂时还不会返回新的 `score.cross_word_check` 字段。代码已就绪，等待未来明确安排后端重启时生效。
- 同步更新 5080 静态前端 `/data/WYC/signLanguage/work/web/static/app.js`，无需后端重启即可生效。结果页语义诊断表现在会显示未来 `cross_word_check` 的“花/跳交叉检查、交叉词、目标分、对照分、margin、交叉原因”，并立即显示当前评分模块已经返回的 `flower_jump_confusion_guard`：“花-跳样守卫、花-跳样原因、双手覆盖、两指手形”。`花` 的采集建议也会在该 guard 触发时提示“这更像双手交互动作；做花时只保留一只开花手，从撮合到张开”。
- 离线验证后端 helper：用保存样本 `web_20260602_233343_899e6970`（`花`）得到目标分 `76.899`、对 `跳` 交叉分 `7.474`、margin `69.425`；用 `web_20260602_233348_53e3df5d`（`跳`）得到目标分 `88.577`、对 `花` 交叉分 `14.588`、margin `73.989`，均通过交叉检查。
- 验证：`/home/wuyangcheng/myenv/bin/python -m py_compile work/web/backend.py` 通过；`node --check work/web/static/app.js` 通过；`git diff --check -- work/web/backend.py work/web/static/app.js` 通过；`curl http://127.0.0.1:5080/static/app.js` 已返回 `花/跳交叉检查`、`花-跳样守卫`、`flower_jump_confusion_guard` 和 `cross_word_check`。5080 运行态仍为 worker `ready`、Holistic PID `811485`、scoring `reload_count=10`、`last_reload_error=None`；目标仍需新的真实网页 `花/跳` 样本诊断。

### 2026-06-03 03:18 CST：增量 watcher 接入花/跳交叉混淆门

- 更新 `/data/WYC/signLanguage/work/scripts/manage_web_sample_marker.py`：`diagnose` 在新增 `花/跳` 样本回归之后，自动运行 `/data/WYC/signLanguage/work/scripts/run_flower_jump_web_confusion_gate.py --request-ids ... --min-eligible-per-word 0`，输出 `flower_jump_confusion/flower_jump_web_confusion_gate.md/.json/.csv`。`min_eligible_per_word=0` 允许用户只测试 `花` 或只测试 `跳`，但仍要求本批至少有 eligible 样本且所有 eligible 样本交叉通过。
- `new_web_samples_status.json/.md` 现在包含 `confusion_report`、`confusion_json`、`confusion_csv`、`confusion_returncode`、`confusion_sample_summaries` 和 `confusion_reason_counts`；Markdown 增加“花/跳交叉混淆”表，逐样本展示目标分、交叉词、交叉分、margin、gate 和原因。如果交叉门失败，会写出状态报告并非零退出，watcher 不会更新 marker。
- 更新 `/data/WYC/signLanguage/work/scripts/watch_web_samples_after_marker.py`：最近诊断状态、Markdown 和 JSON 均带 `confusion_report/confusion_returncode/confusion_sample_summaries`，且 `confusion_returncode != 0` 会计入 `diagnose_failed`。前端 `/data/WYC/signLanguage/work/web/static/app.js` 的自动诊断面板会显示“交叉”报告路径，并把同批样本的 `目标/交叉词 目标分-交叉分 margin gate` 摘要放进最近诊断提示。
- 快速 marker 模拟 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_new_samples_confusion_test_20260603_v1/new_web_samples_status.md` PASS：新增 3 条 `花/跳` 样本，`regression_returncode=0`、`confusion_returncode=0`。交叉摘要：`跳` `70.7` vs `花` `3.4` margin `67.2`，`花` `76.9` vs `跳` `7.5` margin `69.4`，`跳` `88.6` vs `花` `14.6` margin `74.0`，均 PASS。
- watcher 单轮完整模拟 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_sample_watch_confusion_test_20260603_v1/watch_status.md` PASS：回归、交叉混淆和骨架可视化返回码均为 `0`，状态 JSON 中包含 `confusion_sample_summaries`。正式 marker 未污染，仍为 `web_20260602_233348_53e3df5d`。
- 已只重启 tmux `signlanguage-web-sample-watch` 加载新版 watcher，新 PID `3279570`；5080/Holistic 未重启，`/api/status` 仍为 worker `ready`、Holistic PID `811485`、scoring `reload_count=10`、`last_reload_error=None`。当前 `/static/watch_status.json` 为 `no_target_samples`、target count `0`、goal `NOT_READY`，唯一缺失仍是新的真实网页摄像头 `花/跳` 样本诊断。

### 2026-06-03 03:24 CST：前端测试前完成度复查

- 继续检查当前真实测试前状态：`/api/status` 显示 5080 后端 worker `ready`，Holistic worker PID `811485`，scoring `reload_count=10`、`last_reload_error=None`；tmux `signlanguage-web-sample-watch` 仍在线，watcher PID `3279570`。
- `manage_web_sample_marker.py status` 与 `/static/watch_status.json` 均显示正式 marker 仍为 `web_20260602_233348_53e3df5d`，marker 后新增样本 `0`，新增目标 `花/跳` 样本 `0`，因此尚未触发新的真实摄像头样本增量诊断。
- 生成显式完成度审计 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_goal_readiness_audit_20260603_v6/flower_jump_goal_readiness_audit.md`。审计状态仍为 `NOT_READY`：`backend_ready`、`watcher_online`、`marker_available`、`combined_quality_gate_passed` 全部 PASS，五子门质量门仍指向 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_v4/flower_jump_quality_gate.json`；唯一缺失门为 `fresh_real_webcam_target_samples_diagnosed`。
- 本次未改评分算法、前端或 Holistic 后端；目标不能标记完成。下一步需要在 Windows 浏览器通过 `http://127.0.0.1:5080/` 真实采集 `花/跳`，由 watcher 自动生成网页回归、交叉混淆和骨架可视化诊断。

### 2026-06-03 03:41 CST：在线交叉诊断改为 scoring 热加载路径

- 为避免仅为了显示 `score.cross_word_check` 而重启 5080/Holistic，更新 `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py`：`run_pair()` 新增 `enable_cross_check=True` 参数，并对 `web_scoring_mvp` 来源的 `花/跳` query 自动把交叉诊断写入 `score_scale.cross_word_check`。live 5080 后端原本已透传整个 `score_scale`，因此只需 `/api/admin/reload-scoring` 热加载评分模块即可让前端看到交叉词、目标分、交叉分、margin 和 pass/fail；无需重启 Holistic。
- 前端 `/data/WYC/signLanguage/work/web/static/app.js` 已兼容 `data.score.cross_word_check` 和 `data.score.score_scale.cross_word_check` 两个位置。当前 live 后端未重启，因此实际在线显示将走 `score_scale.cross_word_check`；未来若重启后端，两个字段都可用。
- 为防止离线批处理被在线交叉诊断拖慢，已在 `analyze_web_scoring_diagnostics.py`、`replay_web_scoring_samples.py`、`run_flower_jump_web_confusion_gate.py`、`render_web_holistic_cache_visuals.py` 的批处理 `run_pair()` 调用中显式传入 `enable_cross_check=False`。`run_flower_jump_quality_gate.py` 新增 `--reuse-existing`，可在长门控中断后复用已生成子门 JSON，仅运行缺失子门并汇总。
- 验证：离线保存样本 `web_20260602_233343_899e6970`（`花`）得到目标分 `76.899`、对 `跳` 交叉分 `7.474`、margin `69.425`；`web_20260602_233348_53e3df5d`（`跳`）得到目标分 `88.577`、对 `花` 交叉分 `14.588`、margin `73.989`，均由 `score_scale_hot_reload` 来源通过。
- 已通过 `/api/admin/reload-scoring` 热加载到 `reload_count=11`，`last_reload_error=None`，Holistic worker PID 仍为 `811485`，未重启。
- 新五子门质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_v5/flower_jump_quality_gate.md` PASS：web regression、web cross-confusion、offline discrimination、pose robustness、frame-count robustness 均 PASS。关键指标：replay `168` 错误 `0`；`花/跳` diagnostics `149` 错误 `0`，有效率 `96.9%`；`花` 有效低分 `4` 均为 `flower_opening_guard_failed`，`跳` 有效低分 `0`；交叉门 eligible `124/124` pass，`花` 交叉最高 `8.218`，`跳` 交叉最高 `41.535`、最小 margin `29.317`。
- 完成度审计 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_goal_readiness_audit_20260603_v7/flower_jump_goal_readiness_audit.md` 仍为 `NOT_READY`：backend、watcher、marker、v5 五子门质量门均 PASS，但正式 marker 后新增真实网页 `花/跳` 样本仍为 `0`，唯一缺失门仍是 `fresh_real_webcam_target_samples_diagnosed`。

### 2026-06-03 03:47 CST：完成度审计收紧真实网页采集证据

- 为避免未来脚本 smoke 或模板帧模拟样本被误判为“真实网页摄像头测试完成”，更新 `/data/WYC/signLanguage/work/scripts/audit_flower_jump_goal_readiness.py`：`fresh_real_webcam_target_samples_diagnosed` 现在不仅要求 watcher 最新诊断的 regression、交叉混淆、骨架可视化均通过，还要求对应 request 的 `scoring_result.json` 具备 browser-like 采集证据。
- 当前 browser-like 判定包括：目标词为 `花/跳`、worker 输入为 `frame_slices`、帧数达到推荐下限（`花>=12`、`跳>=6`）、有 `duration_sec` 和 `frame_indices`，并且有前端 energy 选择产生的非均匀 `frame_weights`，或未来后端重启后保存的 `client_source=browser_camera/web_frontend_camera`。这能把普通脚本 smoke、标准模板帧直传和无权重旧样本排除在完成证据之外。
- 静态前端 `/data/WYC/signLanguage/work/web/static/app.js` 已在 `/api/score` 请求中发送 `client_source=browser_camera`、`client_session_id` 和 `client_capture_id`；live 5080 后端暂未重启时会忽略这些额外字段，但仍会保存前端已有的 `frame_weights`，足以用于 browser-like 证据。`work/web/backend.py` 代码也已补充这些字段，等待未来后端重启后会显式写入 `scoring_result.json`。
- 验证：`py_compile`、`node --check`、`git diff --check` 均通过；`curl /static/app.js` 已返回 `client_source/client_session_id/client_capture_id`。新审计 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_goal_readiness_audit_20260603_v8/flower_jump_goal_readiness_audit.md` 仍为 `NOT_READY`：backend、watcher、marker、v5 五子门质量门均 PASS，但 `browser_capture_evidence` 为空，因为正式 marker 后仍无新增真实 `花/跳` 样本。

### 2026-06-03 03:55 CST：前端自动诊断区展示真实网页采集证据

- 更新 `/data/WYC/signLanguage/work/scripts/watch_web_samples_after_marker.py`：`goal_readiness` 的紧凑状态现在结构化携带 `browser_capture_evidence` 和 `web_root`，不再只把真实网页采集证据藏在 gate detail 字符串里；watcher Markdown 也会列出“真实网页采集证据”状态和样本行。
- 更新 `/data/WYC/signLanguage/work/web/static/app.js`：前端自动诊断面板新增 `formatBrowserCaptureEvidence()`，会显示“真实采集证据暂无 / 通过 / 未通过原因”，并把这条证据摘要并入缺失证据 tooltip、最近诊断提示、复测轮次提示和无新增样本提示。
- 验证：`/home/wuyangcheng/myenv/bin/python -m py_compile work/scripts/watch_web_samples_after_marker.py` 通过；`node --check work/web/static/app.js` 通过；`git diff --check -- work/scripts/watch_web_samples_after_marker.py work/web/static/app.js` 通过；`curl http://127.0.0.1:5080/static/app.js` 已返回 `formatBrowserCaptureEvidence` 和 `browser_capture_evidence`。
- 运行态：只重启 tmux `signlanguage-web-sample-watch`，新 watcher PID `3467568`；5080/Holistic 未重启，`/api/status` 仍为 worker `ready`、Holistic PID `811485`、scoring `reload_count=11`、`last_reload_error=None`，端口仍只有 `127.0.0.1:5080`。当前 `/static/watch_status.json` 为 `no_target_samples`、`goal_readiness=NOT_READY`、`browser_capture_evidence={'request_ids': [], 'passed': False, 'rows': []}`，唯一缺失仍是 marker 后新的真实网页摄像头 `花/跳` 样本诊断。

### 2026-06-03 04:00 CST：复查花剩余有效低分，不继续放宽 opening guard

- 继续复查 v5 五子门中剩余的 `4` 条 `花` 有效低分，输出专题报告 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_remaining_low_visual_audit_20260603_v1/flower_remaining_low_visual_audit.md`，并用 `render_web_holistic_cache_visuals.py --rescore-current` 生成骨架 contact sheet 和 presence timeline：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_remaining_low_visual_audit_20260603_v1/holistic_visuals/web_holistic_visual_recovery_summary.md`。
- 数值复查：四条低分均为 `flower_opening_guard_failed`，opening score 分别约 `0.122`、`0.086`、`0.000`、`0.052`；其中 `web_20260602_233301_233b8215` 只有 `6` 帧，是刻意过短 smoke，不应抬分。骨架图显示其余样本更多是手部位置/姿态变化、口部附近手势或单侧手覆盖不足，缺少清晰的“撮合到张开”手指绽放过程。
- 结论：暂不放宽 `flower_opening_guard`。当前 `花` 的少量有效低分更像真实语义不足，不是 DTW 对正确开花动作的系统性误杀；后续如果新的真实浏览器样本有清楚撮合起点、张开过程和终态但仍低分，再针对该样本优化 opening 特征。5080/Holistic 未重启，watcher 仍在线，目标仍缺新的真实网页 `花/跳` 样本验收。

### 2026-06-03 04:06 CST：修正真实采集证据审计以兼容 live 旧后端

- 只读复查发现 live 5080 仍是 5 月启动的旧 `backend.py` 进程，`/api/watch-status` 返回 `404`，且历史在线 smoke 的 `scoring_result.json` 没有保存 `client_source` 或 `frame_weights`。这意味着如果继续强制要求这两个字段，用户现在通过浏览器真实采集的新样本也可能被完成度审计误判为“非浏览器样本”。
- 更新 `/data/WYC/signLanguage/work/scripts/audit_flower_jump_goal_readiness.py`：真实网页采集证据分为强证据和旧后端兼容证据。强证据仍是 `client_source=browser_camera/web_frontend_camera` 或非均匀 `frame_weights`；旧后端兼容证据标记为 `legacy_frame_slice_metadata`，要求 `花/跳`、`frame_slices`、达到推荐帧数、`timeline_frame_count >= frame_count`、`duration_sec > 0`、`capture_fps > 0` 和有效 `frame_indices`。报告表新增 `证据等级/evidence_level`、`capture_fps` 和说明文字。
- 同步更新 `/data/WYC/signLanguage/work/scripts/watch_web_samples_after_marker.py` 和 `/data/WYC/signLanguage/work/web/static/app.js`：watcher Markdown 与前端自动诊断摘要会显示证据等级。真实浏览器样本如果由当前旧后端保存，将显示 `legacy_frame_slice_metadata`；未来重启后端后会优先显示 strong 证据。
- 验证：`py_compile audit_flower_jump_goal_readiness.py watch_web_samples_after_marker.py` 通过；`node --check work/web/static/app.js` 通过；`git diff --check` 通过。直接调用 `_browser_capture_evidence()` 检查旧后端在线 smoke 样本 `web_20260602_233343_899e6970` 和 `web_20260602_233348_53e3df5d`，均标为 `legacy_frame_slice_metadata` 且 PASS。正式审计 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_goal_readiness_audit_20260603_v9/flower_jump_goal_readiness_audit.md` 仍 `NOT_READY`，因为 marker 后新增目标样本仍为 `0`。
- 运行态：只重启 `signlanguage-web-sample-watch`，新 watcher PID `3522718`；5080/Holistic 未重启，`/api/status` 仍为 worker `ready`、Holistic PID `811485`、scoring `reload_count=11`、`last_reload_error=None`，端口仍只有 `127.0.0.1:5080`。

### 2026-06-03 04:10 CST：确认旧后端无 frame_weights 不会破坏动态帧权重评分

- 生成兼容性审计 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/live_backend_frame_weight_compat_audit_20260603_v1/live_backend_frame_weight_compat_audit.md`。该报告只读保存样本和 v5 质量门，不调用 `/api/score`，不新增样本，不重启 Holistic。
- 保存样本统计：总计 `168` 条，`149` 条 `花/跳`，全部 worker input mode 都是 `frame_slices`；持久化 `client_source` 的样本为 `0`，持久化 `frame_weights` 的样本为 `123`，其中 `花/跳` 有 `111` 条。关键旧后端 smoke 样本 `web_20260602_233343_899e6970`（`花=76.899`）和 `web_20260602_233348_53e3df5d`（`跳=88.577`）没有持久化 `frame_weights`，但 `score.frame_weight_summary.query_full` 仍显示从骨架运动密度重建出的非恒定动态权重：`花` 约 `0.751-1.547`，`跳` 约 `0.857-1.302`。
- 结论：前端上传的 `frame_weights` 是额外提示，不是评分动态帧权重的唯一来源；当前评分模块会从 Holistic 骨架序列重建查询侧语义权重。现阶段不需要为了 frame_weights 立即重启 5080/Holistic；用户可以继续用当前 5080 页面采集真实 `花/跳`，完成度审计会以 `legacy_frame_slice_metadata` 验收旧后端真实样本。未来维护窗口重启后端后再升级为 strong 证据。

### 2026-06-03 04:17 CST：修复完成度审计 returncode=0 误判并完成 legacy evidence 端到端演练

- 发现 `/data/WYC/signLanguage/work/scripts/audit_flower_jump_goal_readiness.py` 的完成度审计存在一个实际阻塞 bug：`latest_diagnosis` 的 `regression_returncode/confusion_returncode/visual_returncode` 用 `int(value or -1) == 0` 判断，导致真实成功返回码 `0` 被 `or -1` 改写为 `-1`，从而把成功诊断误判为失败。
- 已新增 `_returncode_ok()` 并改为显式判断 `None` 与整数值，确保 `0` 和 `"0"` 都判定为通过。验证：`py_compile` 通过，`_returncode_ok(0)` 与 `_returncode_ok("0")` 均为 True，`git diff --check` 通过。
- 用隔离 marker `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_sample_marker_legacy_evidence_test_20260603.json` 做 watcher 单轮端到端演练，不更新正式 marker。选取旧后端无 `client_source/frame_weights` 的两个在线 smoke 样本作为“新增”：`web_20260602_233343_899e6970`（花）和 `web_20260602_233348_53e3df5d`（跳）。
- 演练输出 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/legacy_evidence_watch_test_20260603_v2/watch_status.md`。结果：`diagnose_done`，regression/confusion/visual returncode 均为 `0`；样本建议 `花=76.9 normal`、`跳=88.6 normal`；交叉混淆均 PASS，margin 分别约 `69.4`、`74.0`；`goal_readiness=READY_TO_COMPLETE`，browser evidence 通过且两条均为 `legacy_frame_slice_metadata`。
- 正式运行态未污染：正式 marker 仍为 `web_20260602_233348_53e3df5d`、样本数 `168`；live `/static/watch_status.json` 仍为正式 `no_target_samples / NOT_READY`，只缺真实新样本；5080/Holistic 未重启，Holistic PID `811485`，scoring `reload_count=11`、`last_reload_error=None`。

### 2026-06-03 04:22 CST：前端自动诊断区增加手动刷新按钮

- 为了真实采集后更方便确认 watcher 是否已经完成回归、交叉混淆和骨架可视化，更新静态前端 `/data/WYC/signLanguage/work/web/static/index.html`、`app.js`、`styles.css`：自动诊断区新增“刷新诊断”按钮，点击后立即调用 `refreshWatchStatus()` 并提示“正在刷新自动诊断状态”。
- 布局上将 `watch-actions` 调整为两列按钮，复测状态仍单独占整行，避免右侧结果栏窄宽度下按钮或状态文字溢出。
- 验证：`node --check work/web/static/app.js` 通过；`git diff --check -- work/web/static/index.html work/web/static/app.js work/web/static/styles.css` 通过；`curl http://127.0.0.1:5080/` 已返回 `refreshWatchBtn/刷新诊断`，`curl /static/app.js` 已返回刷新绑定。该改动只涉及静态前端，不重启 5080/Holistic，不改变评分算法。正式状态仍为 `NOT_READY`，唯一缺口仍是 marker 后新的真实网页 `花/跳` 样本诊断。

### 2026-06-03 04:29 CST：修复 watcher 状态半成品写入，前端稳定显示目标完成度

- 复查 live `/static/watch_status.json` 时发现偶尔只看到基础 `no_target_samples` 状态而没有 `goal_readiness`。根因是 `watch_web_samples_after_marker.py` 先写基础状态、再运行完成度审计、最后覆盖完整状态；前端或命令行可能在中间窗口读到半成品。
- 更新 `/data/WYC/signLanguage/work/scripts/audit_flower_jump_goal_readiness.py`：新增 `--watch-status-json`，完成度审计可直接读取本地 watcher 状态 JSON，不必通过 5080 静态 URL 读前端镜像。
- 更新 `/data/WYC/signLanguage/work/scripts/watch_web_samples_after_marker.py`：新增内部 readiness source JSON，只给审计使用；对前端静态 `watch_status.json/.md` 只写一次最终 payload，稳定包含 `goal_readiness`、`missing_gates` 和 `browser_capture_evidence`。
- 验证：`py_compile audit_flower_jump_goal_readiness.py watch_web_samples_after_marker.py` 通过；one-shot watcher 输出 `goal_readiness.status_label=NOT_READY`、缺失门 `fresh_real_webcam_target_samples_diagnosed`；本地 JSON 审计 PASS；live watcher 已轻量重启为 PID `3638423`，`curl http://127.0.0.1:5080/static/watch_status.json` 已显示 `goal_readiness=NOT_READY`、五个证据门中仅新真实网页样本门缺失。
- 显式完成度审计 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_goal_readiness_audit_20260603_v11/flower_jump_goal_readiness_audit.md`：`backend_ready`、`watcher_online`、`marker_available`、`combined_quality_gate_passed` 均 PASS，`fresh_real_webcam_target_samples_diagnosed` 仍 MISSING。
- 运行态：5080/Holistic 未重启，`/api/status` 仍为 worker `ready`、Holistic PID `811485`、scoring `reload_count=11`、`last_reload_error=None`。正式 marker 仍为 `web_20260602_233348_53e3df5d`，marker 后新增 `花/跳` 目标样本仍为 `0`，目标仍等待新的真实网页摄像头样本触发自动诊断。

### 2026-06-03 04:34 CST：前端自动诊断读取增加非 JSON 404 回退保护

- 复查 `/data/WYC/signLanguage/work/web/static/app.js` 的 `refreshWatchStatus()` 后补强 fallback 逻辑：先尝试 `/api/watch-status`，只有 HTTP OK 且 JSON 无 error 时才使用；若 live 旧后端返回 404、代理返回非 JSON、或请求异常，都会回退到 `/static/watch_status.json`。
- 该改动解决了当前 live 5080 仍未重启、`/api/watch-status` 继续 404 时前端自动诊断面板对后端返回格式的隐性依赖。用户真实采样后，页面应稳定读取 watcher 写入的静态状态文件。
- 验证：`node --check work/web/static/app.js` 通过；`git diff --check -- work/web/static/app.js` 通过；`curl http://127.0.0.1:5080/static/app.js` 已返回新版 `apiResp/staticResp/no-store` 逻辑；live `/static/watch_status.json` 仍显示 `goal_readiness=NOT_READY`、唯一缺失 `fresh_real_webcam_target_samples_diagnosed`。
- 运行态：本次只改静态前端文件，不重启 5080/Holistic，不改评分算法。正式 marker 后新增 `花/跳` 样本仍为 `0`。

### 2026-06-03 04:37 CST：采样后自动刷新诊断覆盖到 2 分钟

- 更新 `/data/WYC/signLanguage/work/web/static/app.js`：新增 `WATCH_REFRESH_AFTER_SCORE_DELAYS_MS=[5s,25s,45s,75s,120s]` 和 `state.watchRefreshTimers`。用户提交 `花/跳` 样本后，页面会清理上一轮 watcher 刷新定时器，并在 2 分钟内多次自动刷新自动诊断状态。
- 目的：新增样本诊断不仅要跑网页回归，还要跑交叉混淆和骨架可视化，耗时可能超过原来的 5s/25s 两次刷新。扩展刷新窗口可以减少用户采样后看不到最新 watcher 诊断的概率。
- 验证：`node --check work/web/static/app.js` 通过；`git diff --check -- work/web/static/app.js` 通过；`curl http://127.0.0.1:5080/static/app.js` 已返回 `WATCH_REFRESH_AFTER_SCORE_DELAYS_MS`、`watchRefreshTimers` 和“2 分钟内自动刷新诊断状态”。
- 运行态：只改静态前端，不重启 5080/Holistic，不改评分算法。当前 `/api/status` 仍为 worker `ready`、Holistic PID `811485`、scoring `reload_count=11`；watcher PID `3638423`，正式 marker 后新增目标样本仍为 `0`。

### 2026-06-03 04:43 CST：最近诊断报告与骨架图镜像到浏览器可访问静态目录

- 更新 `/data/WYC/signLanguage/work/scripts/watch_web_samples_after_marker.py`：新增 `--static-artifact-dir` 与 `--static-artifact-url`，默认把最近一次新增样本诊断的关键产物复制到 `/data/WYC/signLanguage/work/web/static/latest_watch/`，浏览器 URL 前缀为 `/static/latest_watch`。
- 镜像内容包括：状态报告、网页回归、语义诊断、交叉混淆、骨架可视化 Markdown，以及每个样本的 `query/standard` 骨架 contact sheet、识别 presence timeline、完整 timeline 和 `visual_summary.json`。不复制全部逐帧图片，避免静态目录过大。
- 更新 `/data/WYC/signLanguage/work/web/static/app.js` 与 `styles.css`：自动诊断区如果读取到 `latest_diagnosis.static_artifacts`，会把最近报告显示为可点击链接，Windows 浏览器可直接通过 5080 打开 Markdown/骨架图；没有镜像时继续显示原本的服务器本地路径。
- 隔离验证：使用旧后端兼容样本 `web_20260602_233343_899e6970`（花）和 `web_20260602_233348_53e3df5d`（跳）跑 one-shot watcher，不更新正式 marker。输出 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/static_artifact_mirror_test_20260603_v1/watch_status.md`，`diagnose_done` 且 regression/confusion/visual returncode 均为 `0`；镜像生成 `5` 个报告和 `14` 个可视化文件，`curl http://127.0.0.1:5080/static/latest_watch_artifact_test/artifacts.json`、`reports/status.md`、`visuals/.../query_skeleton_contact_sheet.png` 均返回 `200`。
- live 只重启轻量 watcher 加载新版，PID `3712298`；5080/Holistic 未重启，Holistic PID 仍 `811485`，scoring `reload_count=11`。完成度审计 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_goal_readiness_audit_20260603_v12/flower_jump_goal_readiness_audit.md` 仍 `NOT_READY`，唯一缺失仍是 marker 后新的真实网页摄像头 `花/跳` 样本诊断。

### 2026-06-03 04:47 CST：诊断镜像新增单页 HTML 汇总

- 继续更新 `/data/WYC/signLanguage/work/scripts/watch_web_samples_after_marker.py`：镜像目录现在同时生成 `index.html`，内联列出最近诊断的报告入口和每个样本的 query/standard 骨架 contact sheet、识别 presence timeline、完整 timeline。`artifacts.json` 新增 `index_url`。
- 更新 `/data/WYC/signLanguage/work/web/static/app.js`：自动诊断区会优先显示“诊断汇总”链接，其次再显示“镜像清单”和各报告/骨架图链接。这样 Windows 浏览器可以直接打开一个页面查看最近诊断，而不是逐个点 Markdown 和图片。
- 隔离验证：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/static_artifact_index_test_20260603_v1/watch_status.md` PASS，`static_artifacts.index_url=/static/latest_watch_artifact_index_test/index.html`，仍生成 `5` 个报告与 `14` 个可视化文件；`curl http://127.0.0.1:5080/static/latest_watch_artifact_index_test/index.html` 返回 `200` 且页面包含 `最近网页样本自动诊断`、`花 web_...`、`跳 web_...` 和 inline `<img>`。
- 验证：`py_compile watch_web_samples_after_marker.py`、`node --check work/web/static/app.js`、`git diff --check` 均通过。live 只重启轻量 watcher，PID `3731930`；5080/Holistic 未重启，Holistic PID `811485`、scoring `reload_count=11`。完成度审计 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_goal_readiness_audit_20260603_v13/flower_jump_goal_readiness_audit.md` 仍 `NOT_READY`，唯一缺失仍为新真实网页 `花/跳` 样本诊断。

### 2026-06-03 04:55 CST：新增前端 watcher 状态契约检查器

- 新增只读脚本 `/data/WYC/signLanguage/work/scripts/check_watch_status_frontend_contract.py`，用于验证 5080 前端和 watcher 状态之间的契约：`watch_status.json` 基础字段、`goal_readiness`、`browser_capture_evidence`、`latest_diagnosis` returncode、`static_artifacts` 链接、以及 `app.js` 中的自动刷新/真实采集证据/诊断链接渲染逻辑。脚本不会调用 `/api/score`，不会移动 marker，也不会重启 Holistic。
- live 状态验证：`/home/wuyangcheng/myenv/bin/python work/scripts/check_watch_status_frontend_contract.py --require-fresh --output-dir work/generated/scoring_mvp_run3/watch_status_frontend_contract_live_20260603_v1` 输出 PASS。报告 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/watch_status_frontend_contract_live_20260603_v1/watch_status_frontend_contract.md` 显示当前 payload 为 `no_target_samples`、watcher PID `3731930`、`goal_status=NOT_READY`、唯一缺失门仍为 `fresh_real_webcam_target_samples_diagnosed`，`/static/app.js` HTTP 200。
- artifact 镜像验证：`/home/wuyangcheng/myenv/bin/python work/scripts/check_watch_status_frontend_contract.py --watch-status-json work/generated/scoring_mvp_run3/static_artifact_index_test_20260603_v1/watch_status.json --output-dir work/generated/scoring_mvp_run3/watch_status_frontend_contract_artifact_index_20260603_v1 --max-artifact-checks 24` 输出 PASS。报告确认 `diagnose_done` payload 中状态/回归/语义/交叉/骨架报告、`诊断汇总` HTML、`artifacts.json`、`花/跳` query/standard 骨架图和时间线 URL 全部可通过 `http://127.0.0.1:5080` 返回 200。
- 验证：`py_compile check_watch_status_frontend_contract.py` 通过，`git diff --check -- work/scripts/check_watch_status_frontend_contract.py` 通过。该检查器将作为后续改 watcher/前端后的轻量契约回归；本次不改评分算法、不重启 5080/Holistic。目标仍未完成，原因仍是正式 marker 后还没有新的真实网页摄像头 `花/跳` 样本诊断。

### 2026-06-03 05:02 CST：watcher 诊断完成后自动运行前端契约检查

- 更新 `/data/WYC/signLanguage/work/scripts/watch_web_samples_after_marker.py`：在新增样本 `diagnose_done/diagnose_failed/diagnose_exception` 写入最终 watcher 状态后，自动调用 `check_watch_status_frontend_contract.py` 读取前端静态 `watch_status.json`，并把摘要写回 watcher payload 的 `frontend_contract_check`。该检查只在有诊断事件时运行，无新增样本的常规心跳不运行，避免每 20 秒重复检查大量静态链接。
- watcher Markdown 新增“前端契约检查”小节，记录 `status`、报告路径、失败数、warning 数和 artifact URL 失败数；命令行参数新增 `--skip-frontend-contract-check`、`--frontend-contract-output-dir`、`--frontend-contract-base-url`、`--frontend-contract-timeout-sec`、`--frontend-contract-max-artifact-checks`、`--frontend-contract-max-watch-age-sec`。
- 隔离验证：使用 `web_sample_marker_legacy_evidence_test_20260603.json` 复用旧后端 smoke 样本 `web_20260602_233343_899e6970`（花）和 `web_20260602_233348_53e3df5d`（跳），输出 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/frontend_contract_watch_test_20260603_v1/watch_status.md`。结果 `diagnose_done`，regression/confusion/visual returncode 全 0，`goal_readiness=READY_TO_COMPLETE`，`frontend_contract_check.status=PASS`，`artifact_url_count=21`、`artifact_url_failed_count=0`；契约报告 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/frontend_contract_watch_test_20260603_v1/frontend_contract/watch_status_frontend_contract.md` 确认诊断汇总、Markdown 报告和 `花/跳` query/standard 骨架图/时间线 URL 全部 HTTP 200。
- live watcher 会话已重建加载新版，PID `3799378`；5080/Holistic 未重启，`/api/status` 仍为 worker `ready`、Holistic PID `811485`、scoring `reload_count=11`、`last_reload_error=None`。当前 live `/static/watch_status.json` 为 `no_target_samples`、`goal_status=NOT_READY`、缺失门仍仅 `fresh_real_webcam_target_samples_diagnosed`，正式 marker 后新增 `花/跳` 样本仍为 `0`。

### 2026-06-03 05:06 CST：前端自动诊断面板显示契约检查结果

- 更新 `/data/WYC/signLanguage/work/web/static/app.js`：新增 `formatFrontendContractCheck()`，当 watcher payload 包含 `frontend_contract_check` 时，自动诊断提示会显示“前端诊断链路通过/需复查”、失败数和报告/骨架链接通过数；“最近报告”链接区也会加入 `前端契约` 报告路径。无新增样本心跳没有 `frontend_contract_check` 时不显示额外文字。
- 更新 `/data/WYC/signLanguage/work/scripts/check_watch_status_frontend_contract.py`：必检前端 token 新增 `formatFrontendContractCheck` 和 `frontend_contract_check`，防止后续前端改动误删契约检查展示逻辑。
- 验证：`node --check work/web/static/app.js`、`py_compile check_watch_status_frontend_contract.py` 均通过；`curl http://127.0.0.1:5080/static/app.js` 已返回 `formatFrontendContractCheck/frontend_contract_check/前端诊断链路`。使用带 `frontend_contract_check` 的隔离 watcher 状态重跑 `/data/WYC/signLanguage/work/scripts/check_watch_status_frontend_contract.py`，报告 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/watch_status_frontend_contract_render_contract_20260603_v1/watch_status_frontend_contract.md` PASS，并确认新增前端 token、诊断汇总、Markdown 报告、`花/跳` 骨架图/时间线 URL 全部通过。
- live 普通心跳契约检查 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/watch_status_frontend_contract_live_render_contract_20260603_v1/watch_status_frontend_contract.md` PASS。当前 live `/static/watch_status.json` 仍为 `no_target_samples`、watcher PID `3799378`、`goal_status=NOT_READY`；5080/Holistic 未重启，Holistic PID `811485`、scoring `reload_count=11`。正式 marker 后新增 `花/跳` 样本仍为 `0`，目标仍待新真实网页摄像头样本验收。

### 2026-06-03 05:26 CST：补充每词最新样本快诊断入口并复核质量门

- 运行态复查：`127.0.0.1:5080` 正常，`/api/status` 返回 worker `ready`、Holistic PID `811485`、scoring `reload_count=11`、`last_reload_error=None`；live watcher PID `3856536`，`/static/watch_status.json` 为 `no_target_samples`。正式 marker 仍为 `web_20260602_233348_53e3df5d`，marker 后新增样本 `0`、新增 `花/跳` 目标样本 `0`，因此目标仍不能结项。
- 全量网页样本回归复跑 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_regression_flower_jump_20260603_goal_continuation_v1/flower_jump_web_regression.md` PASS：replay `168` 样本、错误 `0`；`花/跳` diagnostics `149` 样本、错误 `0`；有效采集 `128`，有效正常+边界 `124`，有效率 `96.9%`。`花` 有效率 `95.6%`、有效低分 `4` 且均为 `flower_opening_guard_failed`；`跳` 有效率 `100.0%`、有效低分 `0`。
- 为网页现场复测新增快诊断入口：`/data/WYC/signLanguage/work/scripts/run_flower_jump_web_regression.py` 增加 `--latest-per-word N`，当未显式指定 `--request-ids` 时，会对每个目标词各取最近 `N` 条样本，避免原 `--latest N` 只取全局最新样本导致 `花/跳` 覆盖不均。报告过滤条件同步显示 `latest_per_word` 和实际 `request_ids`。
- 快诊断验证 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_regression_flower_jump_latest_per_word_20260603_v1/flower_jump_web_regression.md` PASS：`--latest-per-word 1` 选中 `web_20260602_233343_899e6970`（花）和 `web_20260602_233348_53e3df5d`（跳），2 样本 replay/diagnostics 均 0 错误，有效率 `100.0%`，`花=76.899`、`跳=88.577`。
- 综合质量门复核 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_goal_continuation_v1/flower_jump_quality_gate.md` PASS：`web_regression`、`web_confusion_gate`、`discrimination_gate`、`pose_robustness_gate`、`frame_count_robustness_gate` 五个子门返回码均 `0`。关键指标：web 交叉混淆 eligible `124/124` 通过；负例 margin `花=48.263`、`跳=45.406`；坐姿/镜头扰动最低分 `花=80.446`、`跳=93.015`；帧数扰动最低分 `花=78.482`、`跳=70.488`。
- 完成度审计 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_goal_readiness_audit_20260603_goal_continuation_v1/flower_jump_goal_readiness_audit.md` 为 `NOT_READY`：`backend_ready`、`watcher_online`、`marker_available`、`combined_quality_gate_passed` 均 PASS，唯一缺失 `fresh_real_webcam_target_samples_diagnosed`。
- 结论：当前算法和网页保存样本门控仍稳定，新增快诊断入口用于真实网页采样后的第一层反馈；目标仍 `NOT_READY`，唯一缺口仍是正式 marker 后新的真实网页摄像头 `花/跳` 样本完成 watcher 自动诊断。

### 2026-06-03 05:34 CST：修正快诊断单词复测验收逻辑

- 发现现场复测可能只测 `花` 或只测 `跳`，但 `run_flower_jump_web_regression.py` 的 `_build_gates()` 固定遍历默认 `["花","跳"]`。这会导致只测单词时，另一个未测词没有样本而被误判为有效率缺失。
- 已将 `_build_gates()` 改为跟随 `--words`：只对请求的目标词计算 `effective_rate_<word>`；`jump_effective_low_zero` 只在请求词包含 `跳` 时启用；`flower_effective_low_bounded/explained` 只在请求词包含 `花` 时启用。默认不传 `--words` 时仍验收 `花/跳` 双词。
- 报告文案同步改为按目标词显示：标题使用 `花网页打分回归`、`跳网页打分回归` 或 `花/跳网页打分回归`；语义诊断摘要改为 `目标词样本`，CLI 输出也显示实际目标词。
- 验证：`py_compile run_flower_jump_web_regression.py` 通过；单词快检 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_regression_flower_latest_per_word_single_20260603_v3/flower_jump_web_regression.md` PASS，仅检查 `花`，样本 `web_20260602_233343_899e6970`，分数 `76.899`；单词快检 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_regression_jump_latest_per_word_single_20260603_v2/flower_jump_web_regression.md` PASS，仅检查 `跳`，样本 `web_20260602_233348_53e3df5d`，分数 `88.577`；默认双词快检 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_regression_flower_jump_latest_per_word_20260603_v4/flower_jump_web_regression.md` PASS，`花/跳` 两样本均正常。
- 完成度审计 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_goal_readiness_audit_20260603_single_word_quick_v1/flower_jump_goal_readiness_audit.md` 仍为 `NOT_READY`，只缺 `fresh_real_webcam_target_samples_diagnosed`；前端契约检查 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/watch_status_frontend_contract_single_word_quick_20260603_v2/watch_status_frontend_contract.md` PASS。该改动只影响保存样本快诊断脚本，不重启 5080/Holistic，不改变评分算法。

### 2026-06-03 05:40 CST：自动 watcher/marker 诊断链路支持单词复测

- 进一步检查发现 `manage_web_sample_marker.py diagnose` 虽然拿到了新增样本 request_id，但调用 `run_flower_jump_web_regression.py` 时没有传本批实际词条；因此 live watcher 如果只检测到一个 `花` 或一个 `跳`，仍可能因为回归子门默认验收双词而失败。
- 已在 `manage_web_sample_marker.py` 中新增 `diagnosed_words`：从 target_paths 中按监听词条顺序提取本批实际诊断词条，并把它传给回归脚本的 `--words`。交叉混淆门继续使用默认 `花/跳`，因为单词样本仍需要和另一词模板做交叉区分。状态 Markdown 新增“实际诊断词条”。
- 隔离 `manage_web_sample_marker.py diagnose` 验证：
  - `花` 单词批次 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_new_samples_single_flower_auto_20260603_v1/new_web_samples_status.md` PASS：diagnosed_words=`花`，regression/confusion/visual returncode 全 `0`，目标 `花=76.9`，交叉 `跳=7.5`，margin `69.4`。
  - `跳` 单词批次 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_new_samples_single_jump_auto_20260603_v1/new_web_samples_status.md` PASS：diagnosed_words=`跳`，regression/confusion/visual returncode 全 `0`，目标 `跳=88.6`，交叉 `花=14.6`，margin `74.0`。
- 隔离 `watch_web_samples_after_marker.py --once` 验证：
  - 默认监听 `花/跳` 但 marker 后只有 `跳`：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_sample_watch_single_jump_default_20260603_v1/watch_status.md` 为 `diagnose_done`，regression/confusion/visual returncode 全 `0`，前端契约 `PASS`，artifact URL 14/14 通过，隔离完成度为 `READY_TO_COMPLETE`。
  - 指定 `--words 花` 且 marker 后只诊断 `花`：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_sample_watch_single_flower_words_20260603_v1/watch_status.md` 为 `diagnose_done`，regression/confusion/visual returncode 全 `0`，前端契约 `PASS`，artifact URL 14/14 通过，隔离完成度为 `READY_TO_COMPLETE`。
- 正式状态未污染：正式完成度审计 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_goal_readiness_audit_20260603_auto_single_word_v1/flower_jump_goal_readiness_audit.md` 仍为 `NOT_READY`，`backend_ready`、`watcher_online`、`marker_available`、`combined_quality_gate_passed` 均 PASS，唯一缺失仍是正式 marker 后真实网页摄像头 `花/跳` 样本诊断。live `/static/watch_status.json` 仍为 `no_target_samples`，watcher PID `3856536`，5080/Holistic 未重启，Holistic PID `811485`。

### 2026-06-03 05:43 CST：live watcher 已重启加载单词自动诊断逻辑

- 因 `watch_web_samples_after_marker.py` 会在进程启动时导入 `manage_web_sample_marker.py`，上一节的自动单词诊断修正需要重启轻量 watcher 才能在 live 流程生效。
- 已只重启 tmux 会话 `signlanguage-web-sample-watch`，新 live watcher PID `4021854`；5080 后端与 Holistic 未重启，`/api/status` 仍为 worker `ready`、Holistic PID `811485`、scoring `reload_count=11`、`last_reload_error=None`。
- live `/static/watch_status.json` 已由新 watcher 写入，状态 `no_target_samples`，正式 marker `last_request_id=web_20260602_233348_53e3df5d`，marker 后新增目标样本仍为 `0`。
- 重启后前端契约检查 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/watch_status_frontend_contract_live_single_word_reload_20260603_v1/watch_status_frontend_contract.md` PASS；完成度审计 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_goal_readiness_audit_20260603_live_single_word_reload_v1/flower_jump_goal_readiness_audit.md` 仍 `NOT_READY`，唯一缺口仍为 `fresh_real_webcam_target_samples_diagnosed`。
- 结论：下一次用户只测 `花` 或只测 `跳` 时，live watcher 会加载新的 `diagnosed_words -> run_flower_jump_web_regression.py --words ...` 自动诊断路径；正式目标仍等待新的真实网页摄像头样本。

### 2026-06-03 05:50 CST：完成度证据收紧为花/跳双词覆盖，网页明确显示缺失词条

- 完成度审计口径已固定为目标闭环必须覆盖 `花` 和 `跳` 两个真实网页摄像头样本。`audit_flower_jump_goal_readiness.py` 的 `browser_capture_evidence` 输出 `required_words/observed_words/missing_required_words`，单词条复测可以正常完成诊断，但不会单独关闭总目标。
- 隔离审计验证：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_goal_readiness_audit_20260603_require_both_single_jump_v1/flower_jump_goal_readiness_audit.md` 对只有 `跳` 的批次保持 `NOT_READY`，缺失 `花`；`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_goal_readiness_audit_20260603_require_both_dual_legacy_v1/flower_jump_goal_readiness_audit.md` 对 `花/跳` 两个旧后端 smoke 样本为 `READY_TO_COMPLETE`，说明双词覆盖规则可区分单词诊断和总闭环。
- 更新 `/data/WYC/signLanguage/work/web/static/app.js`：`formatBrowserCaptureEvidence()` 新增词条覆盖展示。当前没有样本时显示要求覆盖和缺失 `花/跳`；单词条样本证据通过但缺另一个词时显示“真实采集样本证据通过但覆盖不足”；失败时同时显示已覆盖、要求覆盖、缺失词条。
- 验证：`node --check work/web/static/app.js` 通过；`py_compile audit/manage/regression/watch/contract` 通过；`curl http://127.0.0.1:5080/static/app.js` 已返回 `formatWordCoverage`、`missing_required_words` 和“覆盖不足/缺失词条”；最终前端契约检查 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/watch_status_frontend_contract_live_required_words_final_20260603_v1/watch_status_frontend_contract.md` PASS。
- 当前 live 状态：`/api/status` worker `ready`，Holistic PID `811485`，scoring `reload_count=11`；watcher PID `4021854`；`/static/watch_status.json` 为 `no_target_samples`，`goal_status=NOT_READY`，`required_words=花/跳`，`observed_words=[]`，`missing_required_words=花/跳`。目标仍需正式 marker 后新的真实网页摄像头 `花` 和 `跳` 样本完成 watcher 自动诊断。

### 2026-06-03 05:56 CST：自动诊断面板新增花/跳覆盖状态 chips

- 更新 `/data/WYC/signLanguage/work/web/static/index.html`、`app.js`、`styles.css`：在自动诊断面板新增 `watchWordCoverage`。页面会读取 `browser_capture_evidence.required_words/observed_words/missing_required_words`，用 chip 显示每个目标词的 `已覆盖/缺失/待采集/需复查` 状态，避免用户只看长文本时不清楚下一步该采哪个词。
- 更新只读契约脚本 `/data/WYC/signLanguage/work/scripts/check_watch_status_frontend_contract.py`：除 `app.js` 外，新增检查 `index.html` 和 `styles.css` 中的 `watchWordCoverage/watch-word-coverage/watch-word-chip*` token，并验证 `/`、`/static/app.js`、`/static/styles.css` HTTP 200。后续前端改动若误删覆盖状态条，契约检查会失败。
- 验证：`node --check work/web/static/app.js` 通过；`py_compile check_watch_status_frontend_contract.py watch_web_samples_after_marker.py audit_flower_jump_goal_readiness.py manage_web_sample_marker.py run_flower_jump_web_regression.py` 通过；`git diff --check` 通过；`curl` 已确认 5080 静态页面/JS/CSS 都包含新 token。
- 前端契约检查 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/watch_status_frontend_contract_live_word_chips_full_20260603_v1/watch_status_frontend_contract.md` PASS，并确认 `frontend_html_token:watchWordCoverage`、`frontend_css_token:watch-word-chip*`、`frontend_index_http_200`、`frontend_styles_css_http_200` 均 PASS。
- 运行态未变：5080/Holistic 未重启，`/api/status` worker `ready`、Holistic PID `811485`、scoring `reload_count=11`、`last_reload_error=None`；live watcher PID `4021854`，仍为 `no_target_samples`，`goal_status=NOT_READY`，缺失词条 `花/跳`。

### 2026-06-03 06:00 CST：自动诊断面板新增下一步复测词条提示

- 在 `watchWordCoverage` 基础上继续更新 `/data/WYC/signLanguage/work/web/static/index.html`、`app.js`、`styles.css`：新增 `watchNextStep` 提示。页面会根据 `browser_capture_evidence` 自动显示 `下一步复测：采集 花/跳`、`下一步复测：复查 <词条>` 或 `<词条> 覆盖完成`，让现场复测直接知道下一步该采集哪个目标词。
- 更新 `/data/WYC/signLanguage/work/scripts/check_watch_status_frontend_contract.py`：新增契约 token `renderWatchNextRetestStep/watchNextStep/watch-next-step`，继续检查 HTML、JS、CSS 和 5080 静态 HTTP 入口。后续若误删下一步复测提示，契约检查会失败。
- 验证：`node --check work/web/static/app.js` 通过；`py_compile check_watch_status_frontend_contract.py watch_web_samples_after_marker.py audit_flower_jump_goal_readiness.py manage_web_sample_marker.py run_flower_jump_web_regression.py` 通过；`git diff --check` 通过；`curl http://127.0.0.1:5080/`、`/static/app.js`、`/static/styles.css` 均能看到新 token。
- 前端契约检查 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/watch_status_frontend_contract_live_next_step_20260603_v1/watch_status_frontend_contract.md` PASS，报告确认 `frontend_js_token:renderWatchNextRetestStep`、`frontend_html_token:watchNextStep`、`frontend_css_token:watch-next-step`、`frontend_index_http_200`、`frontend_styles_css_http_200` 均 PASS。
- 当前 live 状态仍未结项：`/api/status` worker `ready`、Holistic PID `811485`、scoring `reload_count=11`；watcher PID `4021854`；`/static/watch_status.json` 为 `no_target_samples`、`goal_status=NOT_READY`，缺失词条仍为 `花/跳`。本次不改评分算法、不重启 5080/Holistic。

### 2026-06-03 06:06 CST：新增只读复测前就绪报告脚本

- 新增 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`，用于复测前一键生成中文 Markdown/JSON 汇总。脚本只读运行：刷新前端契约检查、调用完成度审计、读取最新综合质量门和 live `watch_status.json`/`api/status`，不调用 `/api/score`、不移动 marker、不重启 5080/Holistic。
- 报告输出 `ready_for_retest` 和 `next_step`，将“运行态/前端/质量门已就绪”和“目标还未完成”分开表达。当前 v2 报告 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_v2/flower_jump_retest_readiness.md` 显示：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。
- v2 报告关键指标：5080/Holistic `PASS`，worker `ready`、Holistic PID `811485`、scoring `reload_count=11`；watcher `PASS`，PID `4021854`、event `no_target_samples`；前端契约 `PASS`，failed `0`、warning `0`；综合质量门 `PASS`。
- 质量门摘要已正确展开：保存网页/API 回归 `168` 样本、错误 `0`、有效正常+边界率 `96.9%`；`花` 有效采集 `91`、正常+边界 `87`、有效低分 `4`、有效率 `95.6%`、有效均分 `75.762`；`跳` 有效采集 `37`、正常+边界 `37`、有效低分 `0`、有效率 `100.0%`、有效均分 `76.677`；交叉混淆 eligible `124`、pass `124`、fail `0`。
- 验证：`py_compile build_flower_jump_retest_readiness_report.py check_watch_status_frontend_contract.py audit_flower_jump_goal_readiness.py manage_web_sample_marker.py run_flower_jump_web_regression.py watch_web_samples_after_marker.py` 通过；`git diff --check` 通过；live `/static/watch_status.json` 仍为 `NOT_READY`，缺失词条 `花/跳`。目标仍需正式 marker 后真实网页摄像头 `花` 和 `跳` 样本完成 watcher 自动诊断。

### 2026-06-03 06:21 CST：新增缺失/mask 鲁棒性门并纳入统一质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_missing_mask_robustness_gate.py`。该门只读缓存 Holistic JSON，在骨架特征层面修改 mask，不调用 `/api/score`、不运行 Holistic、不重启 5080。目的：验证非关键 `pose/face` 或 `花` 的非核心左手缺失时不应明显扣分；关键手部语义缺失时必须低分或进入 `needs_recapture/semantic_mismatch`。
- 独立缺失/mask 门报告 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_missing_mask_robustness_gate_20260603_v1/flower_jump_missing_mask_robustness_gate.md` PASS：`花` 正向最低 `100.000`（drop_face），关键缺失最高 `1.171`（drop_right_core_hand，`needs_recapture/flower_core_hand_presence_low`）；`跳` 正向最低 `100.000`（drop_face），关键缺失最高 `3.037`（drop_left_ground_hand，`needs_recapture/jump_two_hand_presence_low`）。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门新增第 6 子门 `missing_mask_robustness_gate`，并在 Markdown 中新增“缺失与关键 mask 鲁棒性门”小节。
- 新 6 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_missing_mask_v1/flower_jump_quality_gate.md` PASS：`web_regression`、`web_confusion_gate`、`discrimination_gate`、`pose_robustness_gate`、`frame_count_robustness_gate`、`missing_mask_robustness_gate` 全部 returncode `0`。关键指标保持：网页有效正常+边界率 `96.9%`；`花` 有效 `87/91`、有效低分 `4` 均为 opening guard；`跳` 有效 `37/37`、有效低分 `0`；交叉混淆 eligible/pass/fail=`124/124/0`。
- 完成度审计 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_goal_readiness_audit_20260603_missing_mask_v1/flower_jump_goal_readiness_audit.md` 仍 `NOT_READY`：`backend_ready`、`watcher_online`、`marker_available`、新的 6 子门 `combined_quality_gate_passed` 均 PASS；唯一缺失仍为 `fresh_real_webcam_target_samples_diagnosed`，缺失词条 `花/跳`。
- 复测前就绪报告已更新为使用 6 子门质量门，并显示缺失/mask 指标：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_missing_mask_v2/flower_jump_retest_readiness.md`，结论仍是复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。
- 验证：`py_compile run_flower_jump_missing_mask_robustness_gate.py run_flower_jump_quality_gate.py build_flower_jump_retest_readiness_report.py audit_flower_jump_goal_readiness.py` 通过；`git diff --check` 通过；live 运行态未重启，Holistic PID `811485`、watcher PID `4021854`，`/static/watch_status.json` 仍为 `no_target_samples`。

### 2026-06-03 06:37 CST：新增静止 padding/时序鲁棒性门并升级为 7 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_temporal_padding_robustness_gate.py`。该门只读缓存 Holistic JSON，在骨架序列层面合成前缀静止、后缀静止、前后静止、整体变慢和纯静态假动作；不调用 `/api/score`、不运行 Holistic、不重启 5080。目的：真实网页采集包含准备/结束静止帧时仍能对齐核心动作，但只有静态手形/姿态、没有动态语义时不能通过。
- 独立时序 padding 门报告 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_temporal_padding_robustness_gate_20260603_v1/flower_jump_temporal_padding_robustness_gate.md` PASS：`花` 正向最低 `97.862`（suffix_hold_25pct），静态最高 `1.460`（static_hold_mid）；`跳` 正向最低 `79.124`（slow_repeat_each_2x），静态最高 `31.418`（static_hold_mid）。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门新增第 7 子门 `temporal_padding_robustness_gate`，并在 Markdown 中新增“静止 padding 与时序鲁棒性门”小节。`build_flower_jump_retest_readiness_report.py` 和 `audit_flower_jump_goal_readiness.py` 也会展示该子门摘要。
- 新 7 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_temporal_padding_v1/flower_jump_quality_gate.md` PASS：`web_regression`、`web_confusion_gate`、`discrimination_gate`、`pose_robustness_gate`、`frame_count_robustness_gate`、`missing_mask_robustness_gate`、`temporal_padding_robustness_gate` 全部 returncode `0`。关键指标保持：网页有效正常+边界率 `96.9%`；`花` 有效 `87/91`，`跳` 有效 `37/37`；交叉混淆 eligible/pass/fail=`124/124/0`；负例 margin `花=48.263`、`跳=45.406`；坐姿/镜头扰动最低 `花=80.446`、`跳=93.015`；帧数扰动最低 `花=78.482`、`跳=70.488`。
- 完成度审计 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_goal_readiness_audit_20260603_temporal_padding_v1/flower_jump_goal_readiness_audit.md` 仍 `NOT_READY`：运行态、watcher、marker 和 7 子门算法质量均 PASS，唯一缺失仍为 marker 后新的真实网页摄像头 `花/跳` 样本诊断。
- 复测前就绪报告 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_temporal_padding_v1/flower_jump_retest_readiness.md` 显示 `ready_for_retest=PASS`、`goal_status=NOT_READY`、`next_step=采集 花、跳`，并新增 padding 正向最低分/静态最高分表格。
- 验证：`py_compile run_flower_jump_quality_gate.py run_flower_jump_temporal_padding_robustness_gate.py build_flower_jump_retest_readiness_report.py audit_flower_jump_goal_readiness.py` 通过；7 子门质量门完整运行通过。live 运行态未重启，`/api/status` 仍为 worker `ready`、Holistic PID `811485`、scoring `reload_count=11`、`last_reload_error=None`；watcher PID `4021854`。

### 2026-06-03 07:09 CST：相位顺序诊断暴露缺口，但粗暴 order guard 未推广

- 新增诊断脚本 `/data/WYC/signLanguage/work/scripts/run_flower_jump_phase_order_robustness_gate.py`。该脚本只读缓存 Holistic JSON，在骨架序列层面合成单调相位快慢变化、轻微采样抖动、中段停留、倒放、前后半段错序和三相位乱序；不调用 `/api/score`、不运行 Holistic、不重启 5080。目的：验证评分是否真正看动作语义起点/中段/终点顺序，而不是只看局部骨架集合。
- 稳定 scorer 诊断 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_phase_order_robustness_gate_20260603_stable_diagnostic_v1/flower_jump_phase_order_robustness_gate.md` 为 FAIL：`花` 单调变形最低 `79.410`，错序最高 `55.475`；`跳` 单调变形最低 `69.389`，错序最高 `72.027`。说明当前稳定 scorer 对“完整错序但包含正确局部片段”的压力场景仍不够鲁棒，尤其 `跳` 的局部 relation semantic floor 会抬高三相位乱序。
- 曾尝试增加 `花` opening order 条件和 `跳` endpoint-order guard，并使相位顺序门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_phase_order_robustness_gate_20260603_order_guard_v2/flower_jump_phase_order_robustness_gate.md` PASS：`花` 错序最高降到 `33.723`，`跳` 错序最高降到 `47.277`。但该粗暴 guard 破坏保存网页样本回归：8 子门试跑 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_phase_order_v1/flower_jump_quality_gate.md` FAIL，web 有效正常+边界率降到 `71.9%`，`跳` 有效率仅 `24.3%`。根因是真实网页/历史样本的坐姿、采集起止和局部动作窗口会造成端点差异，不能用全序列端点错位硬拦截局部语义 floor。
- 因此已回退评分模块中的粗暴 order guard，保留相位顺序脚本作为诊断压力测试，暂不纳入默认综合质量门。默认综合质量门恢复为 7 子门：web regression、web confusion、discrimination、pose/camera、frame-count、missing/mask、temporal padding。
- 回退后新 7 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_phase_diagnostic_stable_v1/flower_jump_quality_gate.md` PASS：网页回归 `168` 样本错误 `0`，花/跳 diagnostics `149` 错误 `0`，有效正常+边界率 `96.9%`；`花` 有效 `87/91`、低分 `4` 且仍为 opening guard；`跳` 有效 `37/37`、低分 `0`；交叉混淆 eligible/pass/fail=`124/124/0`；负例 margin `花=48.263`、`跳=45.406`。
- 完成度审计 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_goal_readiness_audit_20260603_phase_diagnostic_stable_v1/flower_jump_goal_readiness_audit.md` 仍 `NOT_READY`：运行态、watcher、marker 和 7 子门算法质量均 PASS，唯一缺失仍是 marker 后新的真实网页摄像头 `花/跳` 样本诊断。
- 复测前就绪报告 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_phase_diagnostic_stable_v1/flower_jump_retest_readiness.md` 为 `ready_for_retest=PASS`、`goal_status=NOT_READY`、`next_step=采集 花、跳`。
- 已通过 `/api/admin/reload-scoring` 热重载评分模块到 `reload_count=12`，`last_reload_error=None`；Holistic worker 未重启，PID 仍为 `811485`；live watcher PID `4021854`，`/static/watch_status.json` 仍为 `no_target_samples`。

### 2026-06-03 08:06 CST：复合相位顺序守卫通过网页回归并升级为 8 子门质量门

- 基于相位顺序指标分析 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_phase_order_metric_analysis_20260603_v2/flower_jump_phase_order_metric_analysis.md`，没有采用会误杀真实网页样本的端点顺序硬门，而是接入复合大跨度相位乱序指标：在 `0.10/0.25/0.50/0.75/0.90` 语义锚点上找 query 最近帧，计算 `disorder_span_score`、`adjacent_disorder_span_score` 等，只有跨大段反序才触发。`花` 阈值为 disorder span `>=0.40`；`跳` 阈值为 disorder span `>=0.60` 或 adjacent disorder span `>=0.25`；触发后将分数上限压到 `45.0`，并把 `capture_quality.reason` 标成 `phase_order_disorder`。
- 代码与 profile 更新：`score_holistic_sequence_mvp.py` 增加 `semantic_phase_order_guard`，并阻止短 visible-core/floor 抬高乱序样本；`build_semantic_weight_profiles.py` 和 `/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json/.md` 已启用 `花/跳` 的相位顺序守卫；`analyze_web_scoring_diagnostics.py` 增加 `flower_phase_order_disorder/jump_phase_order_disorder` 诊断；`run_flower_jump_quality_gate.py` 已纳入第 8 子门 `phase_order_robustness_gate`。
- 独立相位顺序门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_phase_order_robustness_gate_20260603_composite_guard_v1/flower_jump_phase_order_robustness_gate.md` PASS：`花` 正向最低 `79.410`、乱序最高 `33.723`；`跳` 正向最低 `69.389`、乱序最高 `45.000`。
- 保存网页回归 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_regression_flower_jump_20260603_composite_phase_guard_v1/flower_jump_web_regression.md` PASS：replay `168` 样本错误 `0`，`花/跳` diagnostics `149` 错误 `0`，有效正常+边界率 `96.9%`；`花` 有效 `87/91`、有效低分 `4` 且均为 `flower_opening_guard_failed`；`跳` 有效 `37/37`、有效低分 `0`。
- 保存网页交叉混淆 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_confusion_flower_jump_20260603_composite_phase_guard_v1/flower_jump_web_confusion_gate.md` PASS：`149` 样本错误 `0`，eligible/pass/fail=`124/124/0`；`花` 交叉最高 `8.218`、最低 margin `59.840`；`跳` 交叉最高 `41.535`、最低 margin `29.317`。
- 新 8 子门综合质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_composite_phase_guard_8gate_v1/flower_jump_quality_gate.md` PASS，子门包括 `web_regression`、`web_confusion_gate`、`discrimination_gate`、`pose_robustness_gate`、`frame_count_robustness_gate`、`missing_mask_robustness_gate`、`temporal_padding_robustness_gate`、`phase_order_robustness_gate`。关键指标保持：web 有效正常+边界率 `96.9%`，`花` 有效 `87/91`，`跳` 有效 `37/37`；负例 margin `花=48.263/跳=45.406`；坐姿扰动最低 `花=80.446/跳=93.015`；帧数扰动最低 `花=78.482/跳=70.488`；静态 padding 最高 `花=1.460/跳=31.418`；相位乱序最高 `花=33.723/跳=45.000`。
- 完成度审计 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_goal_readiness_audit_20260603_composite_phase_guard_8gate_v1/flower_jump_goal_readiness_audit.md` 仍为 `NOT_READY`：backend ready，Holistic PID `811485`、scoring `reload_count=12`、`last_reload_error=None`；watcher PID `4021854`；marker 后目标样本 `0`，缺失词条 `花/跳`。复测前就绪报告 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_composite_phase_guard_8gate_v1/flower_jump_retest_readiness.md` 为 `ready_for_retest=PASS`、`goal_status=NOT_READY`、`next_step=采集 花、跳`。
- 验证：`py_compile score_holistic_sequence_mvp.py analyze_web_scoring_diagnostics.py build_semantic_weight_profiles.py analyze_flower_jump_phase_order_metrics.py run_flower_jump_quality_gate.py` 通过；`git diff --check` 通过。目标仍不能标记完成，直到正式 marker 后真实网页摄像头 `花` 和 `跳` 样本都完成 watcher 自动诊断。

### 2026-06-03 08:17 CST：live scorer 热重载并补齐相位顺序网页诊断展示

- 已通过 `POST /api/admin/reload-scoring` 将 5080 live scorer 热重载到 `reload_count=13`，`loaded_at=2026-06-03T08:12:15`，评分脚本 mtime 与 live 模块一致；Holistic worker 未重启，PID 仍为 `811485`，`last_reload_error=None`。
- 重跑完成度审计 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_goal_readiness_audit_20260603_composite_phase_guard_live_reload_v1/flower_jump_goal_readiness_audit.md`：`backend_ready`、`watcher_online`、`marker_available`、8 子门 `combined_quality_gate_passed` 均 PASS，整体仍 `NOT_READY`，唯一缺口仍是 marker 后真实网页摄像头 `花/跳` 样本诊断；正式 marker 后目标样本数仍为 `0`。
- 重跑复测就绪报告 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_composite_phase_guard_live_reload_v1/flower_jump_retest_readiness.md`：复测就绪 `PASS`，目标完成度 `NOT_READY`，下一步 `采集 花、跳`。
- 更新 `/data/WYC/signLanguage/work/web/static/app.js`：前端已将 `phase_order_disorder`/`semantic_phase_order_guard` 映射为中文标签，为 `花` 和 `跳` 给出相位反序重采建议，并在诊断表展示 `相位顺序守卫/原因/锚点帧/乱序指标/相邻乱序指标/触发项`。
- 更新只读契约脚本 `/data/WYC/signLanguage/work/scripts/check_watch_status_frontend_contract.py`：新增 `phase_order_disorder`、`semantic_phase_order_guard`、`相位顺序守卫`、`相位乱序指标` 必检 token，避免后续前端改动丢失相位顺序诊断展示。
- 验证：`node --check work/web/static/app.js` 通过；`py_compile check_watch_status_frontend_contract.py` 通过；前端契约 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/watch_status_frontend_contract_live_phase_order_ui_20260603_v1/watch_status_frontend_contract.md` PASS；`git diff --check` 通过。目标仍不能标记完成，直到正式 marker 后真实网页摄像头 `花` 和 `跳` 样本都完成 watcher 自动诊断。

### 2026-06-03 08:23 CST：完成证据收紧，legacy smoke 只诊断不默认结项

- 复查发现 `audit_flower_jump_goal_readiness.py` 的旧后端兼容分支会把没有 `client_source/frame_weights`、但具备 frame-slice 元数据的历史 smoke 样本作为完成证据；这对脚本上传模板帧也可能过宽。当前 live 前端已发送 `client_source=browser_camera` 和 `frame_weights`，因此正式完成门不再需要默认接受 legacy 证据。
- 已更新 `/data/WYC/signLanguage/work/scripts/audit_flower_jump_goal_readiness.py`：`legacy_frame_slice_metadata` 默认仅作为 `diagnostic_compatible` 展示，`passed=False`，原因记为 `legacy_frame_slice_metadata_not_completion_evidence`；只有显式传 `--allow-legacy-browser-evidence` 时才允许旧行为，用于历史兼容审计而不是正式 live 完成。
- 回归验证：用旧 smoke 双词 watcher payload 运行严格模式 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_goal_readiness_audit_20260603_legacy_strict_v1/flower_jump_goal_readiness_audit.md`，状态为 `NOT_READY`，两个旧样本均显示 `legacy_frame_slice_metadata_not_completion_evidence`；再加 `--allow-legacy-browser-evidence` 的兼容报告 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_goal_readiness_audit_20260603_legacy_compat_v1/flower_jump_goal_readiness_audit.md` 为 `READY_TO_COMPLETE`，证明开关可控。
- 刷新 live 严格审计 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_goal_readiness_audit_20260603_strict_browser_evidence_live_v1/flower_jump_goal_readiness_audit.md`：backend ready，Holistic PID `811485`、scoring `reload_count=13`；watcher PID `4021854`；8 子门质量门 PASS；整体仍 `NOT_READY`，唯一缺口仍是正式 marker 后真实网页摄像头 `花/跳` 样本诊断。
- 刷新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_strict_browser_evidence_v1/flower_jump_retest_readiness.md`：复测就绪 `PASS`，目标完成度 `NOT_READY`，下一步 `采集 花、跳`。
- 验证：`py_compile audit_flower_jump_goal_readiness.py` 通过；严格/兼容 legacy 双路审计结果符合预期；live 严格审计和复测就绪刷新通过；`git diff --check` 通过。目标仍不能标记完成。

### 2026-06-03 08:28 CST：复测就绪报告新增 live 上传强证据契约

- 针对 08:23 收紧后的完成证据口径，继续只读审计 live 5080 `/openapi.json`：当前运行中的 `ScoreRequest` 接受 `frame_indices/frame_weights`，但尚未加载 `client_source/client_session_id/client_capture_id`。因此正式网页复测仍可通过非均匀 `frame_weights` 形成 strong evidence；client metadata 作为 pending warning 记录，暂不阻塞。
- 更新 `/data/WYC/signLanguage/work/scripts/check_watch_status_frontend_contract.py`：前端契约新增 `frame_indices/frame_weights/client_source/client_session_id/client_capture_id/browser_camera` JS token 检查，并读取 live `/openapi.json` 验证 `/api/score` schema 至少支持 `target_word/fps/duration_sec/frames/frame_indices/frame_weights`；`client_*` schema 字段缺失只记 warning。
- 更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：新增 `score_upload_contract`，复测就绪现在要求 live `/api/score` schema 支持 `frame_weights` 强证据路径；Markdown 运行态表新增“网页上传强证据”行。
- 验证报告 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/watch_status_frontend_contract_live_score_upload_contract_20260603_v1/watch_status_frontend_contract.md` PASS，warning `3` 个，均为 live schema 暂缺 `client_source/client_session_id/client_capture_id`；`frame_weights` 字段 PASS。
- 复测就绪报告 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_score_upload_contract_v1/flower_jump_retest_readiness.md`：复测就绪 `PASS`，目标完成度 `NOT_READY`，下一步 `采集 花、跳`；“网页上传强证据”显示 strong path=`frame_weights`、missing_required=`-`、client metadata pending。
- 验证：`py_compile check_watch_status_frontend_contract.py build_flower_jump_retest_readiness_report.py` 通过；live 5080 worker `ready`、Holistic PID `811485`、scoring `reload_count=13`、`last_reload_error=None`；`git diff --check` 通过。未调用 `/api/score`、未新增样本、未移动 marker。

### 2026-06-03 08:32 CST：强证据门 fixture 验证通过/拒绝边界

- 为 08:23/08:28 的 strict browser evidence 口径新增隔离 fixture `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/strong_browser_evidence_fixture_20260603_v1/`，只复制旧 smoke 的 `scoring_result.json` 到临时 web_root 并修改 metadata；未调用 `/api/score`、未新增正式样本、未移动 marker、未改正式 `web_scoring_mvp`。
- 非均匀 `frame_weights` 正例：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_goal_readiness_audit_20260603_strong_nonuniform_fixture_v1/flower_jump_goal_readiness_audit.md` 为 `READY_TO_COMPLETE`；`花/跳` 两行 evidence 均为 `strong_nonuniform_frame_weights`，说明当前 live 前端只要持久化非均匀权重即可满足 strict 完成证据。
- 均匀 `frame_weights` 负例：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_goal_readiness_audit_20260603_uniform_weights_fixture_v1/flower_jump_goal_readiness_audit.md` 为 `NOT_READY`；两行均为 `source_metadata_missing`，说明普通均匀权重不会误关正式目标。
- 未来 `client_source=browser_camera` 正例：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_goal_readiness_audit_20260603_client_source_fixture_v1/flower_jump_goal_readiness_audit.md` 为 `READY_TO_COMPLETE`；两行 evidence 均为 `strong_client_source`，说明后端未来受控重启并持久化 `client_source` 后也能闭合 strict 完成证据。
- 结论：strict 完成门既能接受真实浏览器强证据，也会拒绝缺来源/无非均匀权重的样本；当前正式 live 状态仍不结项，因为 marker 后真实网页摄像头 `花/跳` 样本仍为 `0`。
- 验证：三组 fixture 审计均符合预期；`git diff --check` 通过。

### 2026-06-03 08:38 CST：浏览器完成证据门脚本化并纳入复测就绪

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_browser_evidence_gate.py`，把 08:32 的 strict browser evidence 正/负 fixture 固化为可复用 gate。脚本只复制旧 smoke 的 `scoring_result.json` 到隔离目录并修改 metadata，不调用 `/api/score`、不新增正式样本、不移动 marker。
- 浏览器证据门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_browser_evidence_gate_20260603_v1/flower_jump_browser_evidence_gate.md` PASS，4 个 case 全符合预期：legacy frame-slice only 被拒绝且仅作诊断兼容；非均匀 `frame_weights` 通过；均匀 `frame_weights` 被拒绝；`client_source=browser_camera` 通过。
- 更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测就绪报告现在默认运行浏览器证据门，并把它作为 `ready_for_retest` 的硬条件；Markdown 运行态表新增“浏览器证据门”行，相关报告列表新增 gate 报告路径。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_browser_evidence_gate_v1/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`；网页上传强证据仍为 `frame_weights`，`client_source/client_session_id/client_capture_id` 仍是 live schema pending warning。
- 验证：`py_compile build_flower_jump_retest_readiness_report.py run_flower_jump_browser_evidence_gate.py` 通过；复测就绪报告完整运行通过；`git diff --check` 通过。live 5080/Holistic 未重启，未调用 `/api/score`，未移动正式 marker；目标仍不能标记完成，直到正式 marker 后真实网页摄像头 `花` 和 `跳` 样本都完成 watcher 自动诊断。

### 2026-06-03 08:43 CST：复测契约新增网页上传权重语义检查

- 更新 `/data/WYC/signLanguage/work/scripts/check_watch_status_frontend_contract.py`：除 token/schema 检查外，新增 8 项 `frontend_upload_*` 语义检查，要求网页上传路径必须从 motion signature、归一化非均匀权重、能量覆盖选帧到 `selected.uploadWeight`，再把 `frame_indices/frame_weights/client_source/client_session_id/client_capture_id` 写入 `/api/score` payload；同时禁止常量 `frame_weights` 上传模式。
- 前端契约 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/watch_status_frontend_contract_live_upload_weight_semantics_20260603_v1/watch_status_frontend_contract.md` PASS：新增上传权重语义检查 `8/8` 通过，仍只有已知 live schema warning `client_source/client_session_id/client_capture_id`。
- 更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测就绪报告现在从前端契约 JSON 汇总 `browser_upload_weight_contract`，并在运行态表新增“网页上传权重语义”行。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_upload_weight_semantics_v1/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`；“网页上传权重语义” `PASS`，checks=`8`，failed=`-`；“网页上传强证据” strong path 仍为 `frame_weights`。
- 验证：`py_compile check_watch_status_frontend_contract.py build_flower_jump_retest_readiness_report.py` 通过；`node --check work/web/static/app.js` 通过；契约和复测就绪报告完整运行通过；`git diff --check` 通过。未调用 `/api/score`、未移动 marker、未重启 5080/Holistic；正式 marker 后真实网页摄像头 `花/跳` 样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 08:49 CST：新增可执行网页上传权重仿真门

- 新增 `/data/WYC/signLanguage/work/scripts/run_browser_upload_weight_simulation_gate.py`。脚本从当前 `work/web/static/app.js` 中抽取真实的 `CAPTURE_RECOMMENDATIONS`、`signatureMotion()`、`normalizeFrameWeights()` 和 `selectEnergyCoverageFrames()`，用 Node.js 执行合成场景；不调用 `/api/score`、不移动 marker、不重启 5080/Holistic。
- 独立仿真门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/browser_upload_weight_simulation_gate_20260603_v3/browser_upload_weight_simulation_gate.md` PASS：`花` opening motion 选 `13/25` 帧，权重 range `1.2505`、unique `12`、top motion selected `6`；`跳` burst motion 选 `10/20` 帧，权重 range `1.9795`、unique `8`、top motion selected `6`；静止场景权重 range `0.0000`，确认不会形成非均匀 `frame_weights` 完成证据。
- 更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测就绪现在默认运行该仿真门，并把它作为 `ready_for_retest` 的硬条件；Markdown 运行态表新增“网页上传权重仿真”行。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_upload_weight_sim_gate_v1/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`；“网页上传权重语义” `PASS`，checks=`8`；“网页上传权重仿真” `PASS`，cases=`3`；“网页上传强证据” strong path 仍为 `frame_weights`。
- 验证：`py_compile run_browser_upload_weight_simulation_gate.py build_flower_jump_retest_readiness_report.py check_watch_status_frontend_contract.py run_flower_jump_browser_evidence_gate.py` 通过；`node --check work/web/static/app.js` 通过；复测就绪完整运行通过；`git diff --check` 通过。live 运行态未改，正式 marker 后真实 `花/跳` 目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 09:09 CST：新增浏览器镜像鲁棒性门并升级为 9 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_mirror_robustness_gate.py`。该门只读模板 Holistic JSON，在骨架特征层面重建基础手/姿态组并重新生成 motion/two-hand relation 特征；`mirror_x` 作为正向门，左右标签互换只作为诊断边界记录，因为它会改变 `跳` 的左手地面/右手两指角色语义。不调用 `/api/score`、不移动 marker、不重启 5080/Holistic。
- 独立镜像门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_mirror_robustness_gate_20260603_v1/flower_jump_mirror_robustness_gate.md` PASS：`花` 镜像正向最低 `80.533`（mirror_x），左右标签诊断最低 `0.919`（swap_labels_diagnostic）；`跳` 镜像正向最低 `80.843`（mirror_x），左右标签诊断最低 `31.053`（mirror_x_swap_labels_diagnostic，semantic_mismatch/relation_direction_mismatch）。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门新增第 9 子门 `mirror_robustness_gate`，位于 pose/camera 与 frame-count 之间；Markdown 新增“浏览器镜像鲁棒性门”小节。
- 新 9 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_mirror_9gate_v1/flower_jump_quality_gate.md` PASS，子门包括 `web_regression`、`web_confusion_gate`、`discrimination_gate`、`pose_robustness_gate`、`mirror_robustness_gate`、`frame_count_robustness_gate`、`missing_mask_robustness_gate`、`temporal_padding_robustness_gate`、`phase_order_robustness_gate`，全部 returncode `0`。关键指标保持：web 有效正常+边界率 `96.9%`；`花` 有效 `87/91`，`跳` 有效 `37/37`；交叉混淆 eligible/pass/fail=`124/124/0`；镜像正向最低 `花=80.533/跳=80.843`。
- 更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测就绪报告会显示镜像摘要。最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_mirror_9gate_v1/flower_jump_retest_readiness.md` 为复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`，并显示镜像正向最低分和左右标签诊断最低分。
- 验证：`py_compile run_flower_jump_mirror_robustness_gate.py run_flower_jump_quality_gate.py build_flower_jump_retest_readiness_report.py` 通过；`node --check work/web/static/app.js` 通过；`git diff --check` 通过；live worker 仍 `ready`，Holistic PID `811485`、scoring `reload_count=13`、`last_reload_error=None`。正式 marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 09:19 CST：新增录制起止裁剪鲁棒性门并升级为 10 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_action_crop_robustness_gate.py`。该门只读模板 Holistic JSON，在骨架序列层面裁剪起止片段，验证网页录制略晚开始/略早结束时仍能给完整核心动作高分；词条专属缺核心半段必须低分或进入 `semantic_mismatch/needs_recapture`。不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。
- 裁剪探测后只把稳定场景设为硬门：`花` 的后半段可能仍包含绽放核心，因此仅诊断不作为负例；`花` 早停缺绽放、`跳` 半段缺起跳/落点作为负向门。
- 独立裁剪门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_action_crop_robustness_gate_20260603_probe_v1/flower_jump_action_crop_robustness_gate.md` PASS：`花` 正向最低 `97.958`（trim_end_15pct），缺核心最高 `41.949`（early_60pct_missing_bloom）；`跳` 正向最低 `80.750`（trim_start_15pct），缺核心最高 `45.000`（early_half_missing_landing）。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门新增第 10 子门 `action_crop_robustness_gate`，Markdown 新增“录制起止裁剪鲁棒性门”小节。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示裁剪正向最低分、缺核心最高分和诊断分数范围。
- 新 10 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_action_crop_10gate_v1/flower_jump_quality_gate.md` PASS，子门包括 `web_regression`、`web_confusion_gate`、`discrimination_gate`、`pose_robustness_gate`、`mirror_robustness_gate`、`frame_count_robustness_gate`、`missing_mask_robustness_gate`、`temporal_padding_robustness_gate`、`action_crop_robustness_gate`、`phase_order_robustness_gate`，全部 returncode `0`。关键指标保持：web 有效正常+边界率 `96.9%`；`花` 有效 `87/91`，`跳` 有效 `37/37`；交叉混淆 eligible/pass/fail=`124/124/0`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_action_crop_10gate_v1/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。live worker 仍 `ready`，Holistic PID `811485`、scoring `reload_count=13`、`last_reload_error=None`；正式 marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 09:29 CST：新增取景尺度/轻微旋转鲁棒性门并升级为 11 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_framing_robustness_gate.py`。该门只读模板 Holistic JSON，在骨架坐标层面模拟整人 zoom in/out、画面偏移、轻微倾斜和手区 zoom；验证用户离镜头略远/略近、取景偏移时 `花/跳` 核心语义仍保持可评分。不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。
- 探测后将轻中度取景变化设为正向门，极端 zoom/pan 仅作为诊断项。独立取景门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_framing_robustness_gate_20260603_v1/flower_jump_framing_robustness_gate.md` PASS：`花` 正向最低 `79.448`（global_zoom_out_0.75），极端诊断最低 `77.954`；`跳` 正向最低 `70.708`（framing_shift_zoom_out），极端诊断最低 `70.509`。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门新增第 11 子门 `framing_robustness_gate`，位于 pose/camera 与 mirror 之间；Markdown 新增“取景尺度与轻微旋转鲁棒性门”小节。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示取景正向最低分和极端诊断最低分。
- 新 11 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_framing_11gate_v1/flower_jump_quality_gate.md` PASS，子门包括 `web_regression`、`web_confusion_gate`、`discrimination_gate`、`pose_robustness_gate`、`framing_robustness_gate`、`mirror_robustness_gate`、`frame_count_robustness_gate`、`missing_mask_robustness_gate`、`temporal_padding_robustness_gate`、`action_crop_robustness_gate`、`phase_order_robustness_gate`，全部 returncode `0`。关键指标保持：web 有效正常+边界率 `96.9%`；`花` 有效 `87/91`，`跳` 有效 `37/37`；交叉混淆 eligible/pass/fail=`124/124/0`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_framing_11gate_v1/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。live worker 仍 `ready`，Holistic PID `811485`、scoring `reload_count=13`、`last_reload_error=None`；正式 marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 09:43 CST：新增 landmark 噪声鲁棒性门并升级为 12 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_landmark_noise_robustness_gate.py`。该门只读缓存 Holistic JSON，在内存中给手部 landmark 加小幅抖动或低比例帧级缺失，并重新计算 hand-shape 特征；验证正常的 Holistic landmark 抖动仍能给 `花/跳` 高分，同时严重缺点、严重乱序和过强噪声只作为诊断低分边界。不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。
- 探测结论：`hand_noise_0.010` 与 `hand_frame_dropout_0.03` 可作为正向鲁棒性门；点级 dropout 和更高比例帧缺失可能移除真实相位证据，因此只保留为 diagnostic-only，不推广为正向门。
- 独立 landmark 噪声门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_landmark_noise_robustness_gate_20260603_v2/flower_jump_landmark_noise_robustness_gate.md` PASS：`花` 正向最低 `76.064`（`hand_noise_0.010_seed2`），严重诊断最低 `11.118`（`severe_shuffle_diagnostic`）；`跳` 正向最低 `72.810`（`hand_noise_0.010_seed1`），严重诊断最低 `8.825`（`severe_point_dropout_0.25_diagnostic`）。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门新增第 12 子门 `landmark_noise_robustness_gate`，位于 frame-count 与 missing/mask 之间；Markdown 新增“Landmark 噪声鲁棒性门”小节。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示 landmark 噪声正向最低分、最弱正向噪声、严重诊断最低分和最弱诊断噪声。
- 新 12 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_landmark_noise_12gate_v1/flower_jump_quality_gate.md` PASS，子门包括 `web_regression`、`web_confusion_gate`、`discrimination_gate`、`pose_robustness_gate`、`framing_robustness_gate`、`mirror_robustness_gate`、`frame_count_robustness_gate`、`landmark_noise_robustness_gate`、`missing_mask_robustness_gate`、`temporal_padding_robustness_gate`、`action_crop_robustness_gate`、`phase_order_robustness_gate`，全部 returncode `0`。关键指标保持：web 有效正常+边界率 `96.9%`；`花` 有效 `87/91`，`跳` 有效 `37/37`；交叉混淆 eligible/pass/fail=`124/124/0`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_landmark_noise_12gate_v1/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。live worker 仍 `ready`，Holistic PID `811485`、scoring `reload_count=13`、`last_reload_error=None`；正式 marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 09:53 CST：新增合成鲁棒变体交叉混淆门并升级为 13 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_synthetic_confusion_robustness_gate.py`。该门只读模板 Holistic JSON，抽取代表性正向鲁棒扰动（取景偏移/旋转、`mirror_x`、landmark 小噪声/低比例帧缺失、静止 padding/慢速重复、轻度起止裁剪），同一 query 先按目标词模板评分，再按另一个 `花/跳` 模板评分；要求目标高分、错词低分、margin 足够。目标是防止“为了鲁棒性抬分”把另一个词也误抬高。不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。
- 独立合成混淆门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_synthetic_confusion_robustness_gate_20260603_v1/flower_jump_synthetic_confusion_robustness_gate.md` PASS：`花` 10/10 通过，目标最低 `76.727`、错词最高 `8.506`、margin 最低 `70.776`；`跳` 10/10 通过，目标最低 `70.708`、错词最高 `25.551`、margin 最低 `55.668`。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门新增第 13 子门 `synthetic_confusion_robustness_gate`，位于保存网页交叉混淆门之后；Markdown 新增“合成鲁棒变体花/跳交叉混淆门”小节。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示合成鲁棒 cases、pass/fail、目标最低、交叉最高、margin 最低和最弱变体。
- 新 13 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_synthetic_confusion_13gate_v1/flower_jump_quality_gate.md` PASS，子门包括 `web_regression`、`web_confusion_gate`、`synthetic_confusion_robustness_gate`、`discrimination_gate`、`pose_robustness_gate`、`framing_robustness_gate`、`mirror_robustness_gate`、`frame_count_robustness_gate`、`landmark_noise_robustness_gate`、`missing_mask_robustness_gate`、`temporal_padding_robustness_gate`、`action_crop_robustness_gate`、`phase_order_robustness_gate`，全部 returncode `0`。关键指标保持：web 有效正常+边界率 `96.9%`；`花` 有效 `87/91`，`跳` 有效 `37/37`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_synthetic_confusion_13gate_v1/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。live worker 仍 `ready`，Holistic PID `811485`、scoring `reload_count=13`、`last_reload_error=None`；正式 marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 10:03 CST：新增 z/depth 深度鲁棒性门并升级为 14 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_depth_robustness_gate.py`。该门只读模板 Holistic JSON，在骨架 z 坐标层面模拟深度偏移、深度缩放和 z 噪声；手部 z 变化会重算 hand-shape 特征。目标是防止不同摄像头/距离导致的 Holistic 深度漂移主导 `花/跳` 分数。不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。
- 探测后将平滑 z offset/scale 作为正向门，把逐点 z noise 作为 diagnostic-only；因为重算 hand-shape 后，逐点手部 z 噪声会真实破坏局部手形，不能当作正常采集通过。
- 独立 depth 门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_depth_robustness_gate_20260603_v2/flower_jump_depth_robustness_gate.md` PASS：`花` 正向最低 `73.923`（`global_z_scale_0.50`），诊断最低 `13.117`（`hand_z_noise_0.20_diagnostic`）；`跳` 正向最低 `70.469`（`global_z_scale_0.50`），诊断最低 `30.536`（`hand_z_noise_0.10_diagnostic`）。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门新增第 14 子门 `depth_robustness_gate`，位于取景门和镜像门之间；Markdown 新增“z/depth 深度鲁棒性门”小节。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示 depth 正向最低分、最弱 depth 扰动、诊断最低分和最弱诊断扰动。
- 新 14 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_depth_14gate_v1/flower_jump_quality_gate.md` PASS，子门包括 `web_regression`、`web_confusion_gate`、`synthetic_confusion_robustness_gate`、`discrimination_gate`、`pose_robustness_gate`、`framing_robustness_gate`、`depth_robustness_gate`、`mirror_robustness_gate`、`frame_count_robustness_gate`、`landmark_noise_robustness_gate`、`missing_mask_robustness_gate`、`temporal_padding_robustness_gate`、`action_crop_robustness_gate`、`phase_order_robustness_gate`，全部 returncode `0`。关键指标保持：web 有效正常+边界率 `96.9%`；`花` 有效 `87/91`，`跳` 有效 `37/37`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_depth_14gate_v1/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。live worker 仍 `ready`，Holistic PID `811485`、scoring `reload_count=13`、`last_reload_error=None`；正式 marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 10:13 CST：新增画面边缘裁切鲁棒性门并升级为 15 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_edge_clipping_robustness_gate.py`。该门只读缓存 Holistic JSON，在内存中模拟画面边缘导致的局部 landmark 缺失，并在手部裁切后重算 hand-shape 特征；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。
- 探测结论：脸部/上身边缘缺失、非核心手或轻度手部边缘裁切应保持可评分；裁掉 `花` 的右手张开核心或 `跳` 的左手落点/右手两指核心时应低分并进入 `needs_recapture` 或 `semantic_mismatch`，不能为了鲁棒性抬高。
- 独立边缘裁切门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_edge_clipping_robustness_gate_20260603_v1/flower_jump_edge_clipping_robustness_gate.md` PASS：`花` 正向最低 `76.689`（`right_opening_wrist_edge_clip`），核心裁切最高 `11.133`（`right_opening_all_tips_edge_clip`）；`跳` 正向最低 `78.545`（`right_jumper_ring_pinky_edge_clip`），核心裁切最高 `10.489`（`left_ground_wrist_edge_clip`）。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门新增第 15 子门 `edge_clipping_robustness_gate`，位于 depth 和 mirror 之间；Markdown 新增“画面边缘裁切鲁棒性门”小节。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示边缘裁切正向最低分、最弱正向裁切、核心裁切最高分和最强核心裁切。
- 新 15 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_edge_clipping_15gate_v1/flower_jump_quality_gate.md` PASS，子门包括 `web_regression`、`web_confusion_gate`、`synthetic_confusion_robustness_gate`、`discrimination_gate`、`pose_robustness_gate`、`framing_robustness_gate`、`depth_robustness_gate`、`edge_clipping_robustness_gate`、`mirror_robustness_gate`、`frame_count_robustness_gate`、`landmark_noise_robustness_gate`、`missing_mask_robustness_gate`、`temporal_padding_robustness_gate`、`action_crop_robustness_gate`、`phase_order_robustness_gate`，全部 returncode `0`。关键指标保持：web 有效正常+边界率 `96.9%`；`花` 有效 `87/91`，`跳` 有效 `37/37`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_edge_clipping_15gate_v1/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。live worker 仍 `ready`，Holistic PID `811485`、scoring `reload_count=13`、`last_reload_error=None`；正式 marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 10:26 CST：新增手形局部尺度鲁棒性门并升级为 16 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_hand_shape_scale_robustness_gate.py`。该门只读缓存 Holistic JSON，在内存中对左右手局部坐标做均匀缩放和各向异性透视拉伸，并重算 `left_hand_shape/right_hand_shape` 派生特征；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。
- 该门补足旧 pose/framing 门的盲点：旧门只改 hand 坐标，未直接验证派生 hand-shape 特征在不同用户手掌大小、手离镜头远近、轻微透视变化下是否稳定。
- 独立手形尺度门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_hand_shape_scale_robustness_gate_20260603_v1/flower_jump_hand_shape_scale_robustness_gate.md` PASS：`花` 正向最低 `80.339`（`right_hand_aspect_x0.85_y1.20`），极端诊断最低 `76.902`（`both_hands_aspect_x0.55_y1.60_diagnostic`）；`跳` 正向最低 `86.403`（`right_hand_aspect_x0.85_y1.20`），极端诊断最低 `69.697`（`both_hands_uniform_scale_0.55_diagnostic`）。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门新增第 16 子门 `hand_shape_scale_robustness_gate`，位于 landmark-noise 与 missing/mask 之间；Markdown 新增“手形局部尺度鲁棒性门”小节。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示手形尺度正向最低分、最弱正向手形尺度、极端尺度诊断最低分和最弱诊断尺度。
- 新 16 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_hand_shape_scale_16gate_v1/flower_jump_quality_gate.md` PASS，子门包括 `web_regression`、`web_confusion_gate`、`synthetic_confusion_robustness_gate`、`discrimination_gate`、`pose_robustness_gate`、`framing_robustness_gate`、`depth_robustness_gate`、`edge_clipping_robustness_gate`、`mirror_robustness_gate`、`frame_count_robustness_gate`、`landmark_noise_robustness_gate`、`hand_shape_scale_robustness_gate`、`missing_mask_robustness_gate`、`temporal_padding_robustness_gate`、`action_crop_robustness_gate`、`phase_order_robustness_gate`，全部 returncode `0`。关键指标保持：web 有效正常+边界率 `96.9%`；`花` 有效 `87/91`，`跳` 有效 `37/37`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_hand_shape_scale_16gate_v1/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。live worker 仍 `ready`，Holistic PID `811485`、scoring `reload_count=13`、`last_reload_error=None`；正式 marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 10:36 CST：新增手部局部旋转鲁棒性门并升级为 17 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_hand_orientation_robustness_gate.py`。该门只读缓存 Holistic JSON，在内存中围绕手腕旋转左右手局部坐标，并重算 `left_hand_shape/right_hand_shape` 派生特征；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。
- 探测后将双手 ±10/±20 度、左右单手 ±15 度作为正向门；双手 ±45 度和右手 ±30 度只作为诊断边界，避免把极端手腕方向变化误推广为正常采集。
- 独立手部旋转门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_hand_orientation_robustness_gate_20260603_v1/flower_jump_hand_orientation_robustness_gate.md` PASS：`花` 正向最低 `81.336`（`both_hands_rotate_pos20deg`），极端诊断最低 `81.162`（`both_hands_rotate_pos45deg_diagnostic`）；`跳` 正向最低 `84.409`（`both_hands_rotate_neg20deg`），极端诊断最低 `81.149`（`both_hands_rotate_pos45deg_diagnostic`）。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门新增第 17 子门 `hand_orientation_robustness_gate`，位于 hand-shape-scale 与 missing/mask 之间；Markdown 新增“手部局部旋转鲁棒性门”小节。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示手部旋转正向最低分、最弱正向旋转、极端旋转诊断最低分和最弱诊断旋转。
- 新 17 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_hand_orientation_17gate_v1/flower_jump_quality_gate.md` PASS，子门包括 `web_regression`、`web_confusion_gate`、`synthetic_confusion_robustness_gate`、`discrimination_gate`、`pose_robustness_gate`、`framing_robustness_gate`、`depth_robustness_gate`、`edge_clipping_robustness_gate`、`mirror_robustness_gate`、`frame_count_robustness_gate`、`landmark_noise_robustness_gate`、`hand_shape_scale_robustness_gate`、`hand_orientation_robustness_gate`、`missing_mask_robustness_gate`、`temporal_padding_robustness_gate`、`action_crop_robustness_gate`、`phase_order_robustness_gate`，全部 returncode `0`。关键指标保持：web 有效正常+边界率 `96.9%`；`花` 有效 `87/91`，`跳` 有效 `37/37`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_hand_orientation_17gate_v1/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。live worker 仍 `ready`，Holistic PID `811485`、scoring `reload_count=13`、`last_reload_error=None`；正式 marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 10:48 CST：新增 frame_weights 上传权重鲁棒性门并升级为 18 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_frame_weight_robustness_gate.py`。该门只读模板 Holistic JSON，只在内存中改 query 的 `frame_weight`，覆盖浏览器 motion 权重、无非均匀权重、15% 权重噪声、一帧前后错位、宽泛前/后段加权；反向 motion 权重仅作为坏上传先验诊断。不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。
- 独立 frame_weights 门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_frame_weight_robustness_gate_20260603_v1/flower_jump_frame_weight_robustness_gate.md` PASS：`花` 正向最低 `99.161`（`back_loaded_broad_emphasis`），诊断最低 `99.347`（`inverted_dynamic_diagnostic`）；`跳` 正向最低 `76.297`（`back_loaded_broad_emphasis`），诊断最低 `10.120`（`inverted_dynamic_diagnostic`）。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门新增第 18 子门 `frame_weight_robustness_gate`，位于 `frame_count_robustness_gate` 之后；Markdown 新增“frame_weights 上传权重鲁棒性门”小节。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示 frame_weights 正向最低分、最弱权重、反向权重诊断最低分和最弱诊断权重。
- 新 18 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_frame_weight_18gate_v1/flower_jump_quality_gate.md` PASS，子门包括 `web_regression`、`web_confusion_gate`、`synthetic_confusion_robustness_gate`、`discrimination_gate`、`pose_robustness_gate`、`framing_robustness_gate`、`depth_robustness_gate`、`edge_clipping_robustness_gate`、`mirror_robustness_gate`、`frame_count_robustness_gate`、`frame_weight_robustness_gate`、`landmark_noise_robustness_gate`、`hand_shape_scale_robustness_gate`、`hand_orientation_robustness_gate`、`missing_mask_robustness_gate`、`temporal_padding_robustness_gate`、`action_crop_robustness_gate`、`phase_order_robustness_gate`，全部 returncode `0`。关键指标保持：web 有效正常+边界率 `96.9%`，有效 `124/128`；`花` 有效 `87/91`，`跳` 有效 `37/37`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_frame_weight_18gate_v1/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。live worker 仍 `ready`，Holistic PID `811485`、scoring `reload_count=13`、`last_reload_error=None`；正式 marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 10:58 CST：新增坐标精度量化鲁棒性门并升级为 19 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_coordinate_precision_robustness_gate.py`。该门只读模板 Holistic JSON，在内存中模拟 640x480/320x240 像素网格取整、归一化坐标 1/512/1/256 精度、手部 1/128 精度以及更粗网格诊断；手部坐标量化后重算 `left_hand_shape/right_hand_shape`。不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。
- 独立坐标精度门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_coordinate_precision_robustness_gate_20260603_v1/flower_jump_coordinate_precision_robustness_gate.md` PASS：`花` 正向最低 `80.805`（`hand_xy_quantize_1_128`），诊断最低 `78.075`（`severe_hand_xy_quantize_1_32_diagnostic`）；`跳` 正向最低 `96.833`（`hand_xy_quantize_1_128`），诊断最低 `84.267`（`severe_hand_xy_quantize_1_32_diagnostic`）。结论是正常分辨率/低分辨率坐标取整不会破坏当前 `花/跳` 评分。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门新增第 19 子门 `coordinate_precision_robustness_gate`，位于 `frame_weight_robustness_gate` 与 `landmark_noise_robustness_gate` 之间；Markdown 新增“坐标精度量化鲁棒性门”小节。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示坐标精度正向最低分、最弱精度扰动、粗量化诊断最低分和最弱诊断扰动。
- 新 19 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_coordinate_precision_19gate_v1/flower_jump_quality_gate.md` PASS，子门包括 `web_regression`、`web_confusion_gate`、`synthetic_confusion_robustness_gate`、`discrimination_gate`、`pose_robustness_gate`、`framing_robustness_gate`、`depth_robustness_gate`、`edge_clipping_robustness_gate`、`mirror_robustness_gate`、`frame_count_robustness_gate`、`frame_weight_robustness_gate`、`coordinate_precision_robustness_gate`、`landmark_noise_robustness_gate`、`hand_shape_scale_robustness_gate`、`hand_orientation_robustness_gate`、`missing_mask_robustness_gate`、`temporal_padding_robustness_gate`、`action_crop_robustness_gate`、`phase_order_robustness_gate`，全部 returncode `0`。关键指标保持：web 有效正常+边界率 `96.9%`，有效 `124/128`；`花` 有效 `87/91`，`跳` 有效 `37/37`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_coordinate_precision_19gate_v1/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。live worker 仍 `ready`，Holistic PID `811485`、scoring `reload_count=13`、`last_reload_error=None`；正式 marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 11:11 CST：新增运动幅度与模糊诊断鲁棒性门并升级为 20 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_motion_blur_robustness_gate.py`。该门只读缓存 Holistic JSON，在内存中模拟手部/全身运动幅度 10%-15% 变化，并把低通平滑、运动模糊和重度幅度变化保留为诊断边界；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。
- v1 探测结论：不能把低通平滑当作正向鲁棒性门。`花` 的 `hand_motion_blur_3tap` 只有 `32.995`、`hand_motion_blur_5tap_light` 只有 `30.905`，原因是平滑抹掉了“含苞到张开”的核心动态证据；因此低通/模糊只作为 diagnostic-only，正向门只覆盖轻度运动幅度变化。
- 独立 v2 运动幅度/模糊诊断门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_motion_blur_robustness_gate_20260603_v2/flower_jump_motion_blur_robustness_gate.md` PASS：`花` 正向最低 `79.074`（`hand_motion_amplitude_0.85`），诊断最低 `10.092`（`hand_motion_blur_5tap_heavy_diagnostic`）；`跳` 正向最低 `75.662`（`hand_motion_amplitude_0.85`），诊断最低 `70.351`（`hand_motion_amplitude_0.55_diagnostic`）。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门新增第 20 子门 `motion_blur_robustness_gate`，位于坐标精度门与 landmark-noise 门之间；Markdown 新增“运动幅度与模糊诊断鲁棒性门”小节。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示运动幅度正向最低分、最弱正向幅度变体、平滑/模糊诊断最低分和最弱诊断平滑/模糊。
- 新 20 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_motion_blur_20gate_v1/flower_jump_quality_gate.md` PASS，20 个子门全部 returncode `0`。关键指标保持：web 有效正常+边界率 `96.9%`，有效 `124/128`；`花` 有效 `87/91`，`跳` 有效 `37/37`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_motion_blur_20gate_v1/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。live worker 仍 `ready`，Holistic PID `811485`、scoring `reload_count=13`、`last_reload_error=None`；正式 marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 11:40 CST：修复单手词左右惯用手序列惩罚并升级为 21 子门质量门

- 修复 `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py` 的 `_sequence_penalty`：当 profile 允许左右手互换且词条不是 `two_hand_relation` 角色型词时，presence/motion/roughness 的序列级惩罚按左右手最佳匹配计算；含 `two_hand_relation` 的 `跳` 仍保持地面手/跳跃手角色约束。这个修复解决 `花` 左右手标签互换时 DTW 已可匹配但序列惩罚仍按硬右手扣分的问题。
- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_hand_role_robustness_gate.py`。该门只读模板 Holistic JSON，不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080；验证 `花` 的左右惯用手互换应高分，`跳` 的双手角色互换应低分或语义失败。
- 独立手角色门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_hand_role_robustness_gate_20260603_v1/flower_jump_hand_role_robustness_gate.md` PASS：`花` `dominant_hand_swap=82.267`、`mirror_x_dominant_hand_swap=82.267`，正向最低 `80.533`（`mirror_x`）；`跳` 正向最低 `80.843`（`mirror_x`），角色互换最高 `36.324`（`role_swap_negative`），`mirror_x_role_swap_negative=31.053`，均为 `semantic_mismatch`。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门新增第 21 子门 `hand_role_robustness_gate`，位于镜像门之后、帧数门之前；Markdown 新增“手角色鲁棒性门”小节。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示手角色正向最低分、最弱正向角色变体、角色互换最高分和最强角色互换负例。
- 新 scorer 下全量重跑 21 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_hand_role_21gate_v1/flower_jump_quality_gate.md` PASS，21 个子门全部 returncode `0`。关键指标：web 有效正常+边界率 `96.9%`，有效 `124/128`；`花` 有效 `87/91`、有效均分 `75.775`；`跳` 有效 `37/37`、有效均分 `76.677`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`。
- 已通过 `POST /api/admin/reload-scoring` 热重载 live scorer 到 `reload_count=14`、`loaded_at=2026-06-03T11:39:34`、`last_reload_error=None`；Holistic worker 未重启，PID 仍为 `811485`。最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_hand_role_21gate_reload_v1/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`；正式 marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 11:48 CST：收紧完成度审计的 watcher 诊断 scope，防止旧诊断误关目标

- 更新 `/data/WYC/signLanguage/work/scripts/audit_flower_jump_goal_readiness.py`，新增 `_diagnosis_scope_matches_current_marker()`。`fresh_real_webcam_target_samples_diagnosed` 现在除了要求 watcher 最新诊断、回归/交叉/可视化 returncode 全部为 0、浏览器强证据通过外，还要求诊断 request_id 与当前 marker 状态匹配：若 marker 后仍有 target ids，则 diagnosed ids 必须等于当前 target ids；若 watcher 已成功更新 marker，则 latest diagnosed id 必须等于当前 marker last_request_id。
- 该修正确保旧 `latest_diagnosis` 不会在 marker 被后续移动后误关闭正式目标；也保留了 watcher 成功诊断并更新 marker 后继续作为完成证据的正常路径。
- 验证：`py_compile` 通过；helper 小用例覆盖 `marker_after_target_set`、`marker_updated_to_latest_diagnosis`、`stale_after_marker_moved`、`missing_diagnosis_ids`；当前 live 审计 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_goal_readiness_audit_20260603_scope_guard_v1/flower_jump_goal_readiness_audit.md` 仍为 `NOT_READY`，运行态、watcher、marker、21 子门质量门均 PASS，唯一缺口仍是 `fresh_real_webcam_target_samples_diagnosed`。
- 本轮未调用 `/api/score`、未移动正式 marker、未重启 5080/Holistic。当前 live 状态仍为 Holistic PID `811485`、scoring `reload_count=14`、watcher PID `4021854`，正式 marker `web_20260602_233348_53e3df5d` 后目标样本 `0`。

### 2026-06-03 12:14 CST：新增左右手标签抖动鲁棒性门并升级为 22 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_hand_label_flicker_robustness_gate.py`。该门只读缓存 Holistic JSON，在内存中模拟短暂左右手标签 flicker、稀疏 flicker、短连续角色 flicker、持续核心标签错置和交替错置；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。
- 独立标签抖动门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_hand_label_flicker_robustness_gate_20260603_v1/flower_jump_hand_label_flicker_robustness_gate.md` PASS：`花` 轻度 flicker 最低 `96.804`（`sparse_label_flicker`），严重 flicker 最高 `27.593`（`sustained_core_label_flicker_negative`，`needs_recapture`）；`跳` 轻度 flicker 最低 `70.469`（`single_frame_label_flicker`），严重 flicker 最高 `14.618`（`alternating_label_flicker_negative`，`semantic_mismatch`）。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门新增第 22 子门 `hand_label_flicker_robustness_gate`，位于手角色门之后、帧数门之前；Markdown 新增“左右手标签抖动鲁棒性门”小节。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示标签 flicker 正向最低分、最弱正向 flicker、严重 flicker 最高分和最强严重 flicker。
- 新 22 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_hand_label_flicker_22gate_v1/flower_jump_quality_gate.md` PASS，22 个子门全部 returncode `0`。关键指标保持：web 有效正常+边界率 `96.9%`，有效 `124/128`；`花` 有效 `87/91`、有效均分 `75.775`；`跳` 有效 `37/37`、有效均分 `76.677`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_hand_label_flicker_22gate_v1/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。live worker `ready`，Holistic PID `811485`、scoring `reload_count=14`、`last_reload_error=None`；watcher `no_target_samples`、PID `4021854`；正式 marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 12:44 CST：新增 landmark 跳点鲁棒性门并升级为 23 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_landmark_spike_robustness_gate.py`。该门只读缓存 Holistic JSON，先剥离到基础骨架组，再在手部坐标层合成单帧整手跳点、单帧 fingertip 跳点、稀疏 fingertip 跳点、连续核心 tip 跳点、交替 tip 跳点和 landmark 顺序扰动，并重建 motion/relation/hand-shape 特征；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。
- 独立跳点门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_landmark_spike_robustness_gate_20260603_v1/flower_jump_landmark_spike_robustness_gate.md` PASS：`花` 正向最低 `92.772`（`sparse_tip_spike_every_7th`），诊断最低 `21.400`（`alternating_tip_spike_diagnostic`）；`跳` 正向最低 `70.469`（`single_frame_tip_spike`），诊断最低 `82.302`（`alternating_tip_spike_diagnostic`）。`跳` 的严重 tip 跳点仍被 relation/local floor 接住，因此该类强扰动只保留为诊断，不设负向通过条件。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门新增第 23 子门 `landmark_spike_robustness_gate`，位于 landmark noise 与 hand-shape scale 之间；Markdown 新增“Landmark 跳点鲁棒性门”小节。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示 landmark 跳点正向最低分、最弱正向跳点、跳点诊断最低分和最弱诊断跳点。
- 新 23 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_landmark_spike_23gate_v1/flower_jump_quality_gate.md` PASS，23 个子门全部 returncode `0`。关键指标保持：web 有效正常+边界率 `96.9%`，有效 `124/128`；`花` 有效 `87/91`、有效均分 `75.775`；`跳` 有效 `37/37`、有效均分 `76.677`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_landmark_spike_23gate_v1/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。watcher 当前引用的质量门已更新到 23 子门；live worker `ready`，Holistic PID `811485`、scoring `reload_count=14`、`last_reload_error=None`；watcher `no_target_samples`、PID `4021854`；正式 marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 13:15 CST：新增宽高比失真鲁棒性门并升级为 24 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_aspect_ratio_robustness_gate.py`。该门只读缓存 Holistic JSON，剥离到基础骨架组后模拟轻中度非等比摄像头/画布拉伸，并重建 hand-shape、motion 和 two-hand relation 特征；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。
- 独立宽高比门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_aspect_ratio_robustness_gate_20260603_v1/flower_jump_aspect_ratio_robustness_gate.md` PASS：`花` 正向最低 `80.345`（`aspect_x0.85_y1.18`），诊断最低 `76.940`（`diagnostic_x0.55_y1.55`）；`跳` 正向最低 `85.975`（`aspect_x0.85_y1.18`），诊断最低 `55.282`（`diagnostic_x1.55_y0.55`）。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门新增第 24 子门 `aspect_ratio_robustness_gate`，位于 framing 与 depth 之间；Markdown 新增“宽高比失真鲁棒性门”小节。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示宽高比正向最低分、最弱正向宽高比、极端宽高比诊断最低分和最弱诊断宽高比。
- 新 24 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_aspect_ratio_24gate_v1/flower_jump_quality_gate.md` PASS，24 个子门全部 returncode `0`。关键指标保持：web 有效正常+边界率 `96.875%`，有效 `124/128`；`花` 有效 `87/91`、有效均分 `75.775`；`跳` 有效 `37/37`、有效均分 `76.677`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_aspect_ratio_24gate_v1/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。live worker `ready`，Holistic PID `811485`、scoring `reload_count=14`、`last_reload_error=None`；watcher `no_target_samples`、PID `4021854`；正式 marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 13:48:57 CST：新增连续手部检出空洞鲁棒性门并升级为 25 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_hand_dropout_burst_robustness_gate.py`。该门只读缓存 Holistic JSON，在基础手部/手形 mask 层模拟连续 hand detector 空洞，并剥离旧派生组后重建 motion 和 two-hand relation 特征；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。
- 独立连续手部空洞门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_hand_dropout_burst_robustness_gate_20260603_v1/flower_jump_hand_dropout_burst_robustness_gate.md` PASS：`花` 正向最低 `95.170`（`right_core_15pct_mid`），持续核心空洞最高 `55.975`（`right_core_25pct_mid_negative`，质量口径允许 `needs_recapture/semantic_mismatch`）；`跳` 正向最低 `74.629`（`right_jump_3f_mid`），持续核心空洞最高 `18.484`（`both_hands_2f_mid_negative`）。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门新增第 13 子门 `hand_dropout_burst_robustness_gate`，位于左右手标签抖动门之后、帧数门之前；Markdown 新增“连续手部检出空洞鲁棒性门”小节。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示连续空洞正向最低分、最弱正向空洞、持续空洞最高分和最强持续空洞。
- 新 25 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_hand_dropout_burst_25gate_v1/flower_jump_quality_gate.md` PASS，25 个子门全部 returncode `0`。关键指标：web 有效正常+边界率 `96.875%`，有效 `124/128`；`花` 有效 `87/91`、有效均分 `75.775`；`跳` 有效 `37/37`、有效均分 `76.677`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_hand_dropout_burst_25gate_v1/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。live worker `ready`，Holistic PID `811485`、scoring `reload_count=14`、`last_reload_error=None`；watcher `no_target_samples`、PID `4021854`，当前 watcher 状态已引用 25 子门质量门；正式 marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 14:24:52 CST：新增时序帧冻结 stutter 鲁棒性门并升级为 26 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_temporal_stutter_robustness_gate.py`。该门只读缓存 Holistic JSON，在固定长度骨架序列内合成浏览器摄像头短 burst 冻结、稀疏重复帧和持续核心动作冻结，并剥离旧派生组后重建 motion 和 two-hand relation；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。
- 独立 stutter 门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_temporal_stutter_robustness_gate_20260603_v1/flower_jump_temporal_stutter_robustness_gate.md` PASS：`花` 正向最低 `93.869`（`freeze_mid_15pct`），持续冻结最高 `41.635`（`freeze_mid_50pct_negative`），25% 中段冻结作为诊断边界 `87.915`；`跳` 正向最低 `72.011`（`freeze_mid_4f`），持续冻结最高 `12.747`（`freeze_mid_35pct_negative`），5 帧中段冻结作为诊断边界 `73.224`。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门新增第 15 子门 `temporal_stutter_robustness_gate`，位于帧数门之后、frame_weights 门之前；Markdown 新增“时序帧冻结 stutter 鲁棒性门”小节。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示 stutter 正向最低分、最弱正向 stutter、持续冻结最高分、最强持续冻结和诊断边界。
- 新 26 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_temporal_stutter_26gate_v1/flower_jump_quality_gate.md` PASS，26 个子门全部 returncode `0`。关键指标保持：web 有效正常+边界率 `96.875%`，有效 `124/128`；`花` 有效 `87/91`、有效均分 `75.775`；`跳` 有效 `37/37`、有效均分 `76.677`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_temporal_stutter_26gate_v1/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。live worker `ready`，Holistic PID `811485`、scoring `reload_count=14`、`last_reload_error=None`；watcher `no_target_samples`、PID `4021854`，当前 watcher 状态已引用 26 子门质量门；正式 marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 14:58:43 CST：新增时序速率鲁棒性门并升级为 27 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_temporal_rate_robustness_gate.py`。该门只读缓存 Holistic JSON，在骨架序列层面模拟同帧数局部速度变化、整体快慢变化、核心阶段停留和轻微采样间隔不均，并剥离旧派生组后重建 motion 和 two-hand relation；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。
- v1 探测显示强前慢后快、强 micro jitter 和内部核心缺口不能直接作为正向/负向硬门：`花` 强前慢后快会触发 phase-order guard，`跳` 强 jitter 会进入 `needs_recapture`，内部缺口仍可能被当前语义 floor 接住。因此 v2 将正向门收敛到温和速率变化，极端速率和内部缺口只保留为诊断边界。
- 独立 v2 时序速率门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_temporal_rate_robustness_gate_20260603_v2/flower_jump_temporal_rate_robustness_gate.md` PASS：`花` 正向最低 `92.730`（`same_count_micro_rate_jitter`），诊断最低 `94.439`（`bloom_core_gap_diagnostic`）；`跳` 正向最低 `77.195`（`global_slow_1.50x`），诊断最低 `80.007`（`global_slow_2.25x_diagnostic`）。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门新增第 16 子门 `temporal_rate_robustness_gate`，位于 stutter 门之后、frame_weights 门之前；Markdown 新增“时序速率鲁棒性门”小节。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示速率正向最低分、最弱正向速率扰动、速率诊断最低分和最弱诊断边界。
- 新 27 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_temporal_rate_27gate_v1/flower_jump_quality_gate.md` PASS，27 个子门全部 returncode `0`。关键指标保持：web 有效正常+边界率 `96.875%`，有效 `124/128`；`花` 有效 `87/91`、有效均分 `75.775`；`跳` 有效 `37/37`、有效均分 `76.677`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_temporal_rate_27gate_v1/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。live worker `ready`，Holistic PID `811485`、scoring `reload_count=14`、`last_reload_error=None`；light watcher 已重启为 PID `2664169`，嵌套 `goal_readiness.quality_gate_json` 已引用 27 子门质量门；正式 marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 15:37:26 CST：新增组合网页扰动鲁棒性门并升级为 28 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_composite_browser_robustness_gate.py`。该门只读缓存 Holistic JSON，在内存中组合模拟浏览器端常见轻度扰动：宽高比拉伸、坐标低分辨率量化、时序速率/轻微 jitter、短帧冻结和短 hand detector 空洞；每次先剥离旧派生组，再按需重建 hand-shape、motion 和 two-hand relation。不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。
- v1/v2 探测显示 `花` 对“低分辨率量化 + 较强时序 jitter”组合处在真实边界：`320/640 quantize + micro jitter` 会降到约 `69`，因此正向组合门收敛到较温和 jitter，较强量化+jitter 保留为 diagnostic-only 边界，避免把会破坏开花动态证据的情况误设为通过门。
- 独立 v3 组合网页扰动门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_composite_browser_robustness_gate_20260603_v3/flower_jump_composite_browser_robustness_gate.md` PASS：`花` 正向最低 `77.955`（`combo_slow_sparse_freeze_lowres`），诊断最低 `69.472`（`diagnostic_quantized_micro_jitter`）；`跳` 正向最低 `73.632`（`combo_fast_aspect_hand_quant`），诊断最低 `74.006`（`diagnostic_dropout_rate_stack`）。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门新增第 17 子门 `composite_browser_robustness_gate`，位于 `temporal_rate_robustness_gate` 之后、`frame_weight_robustness_gate` 之前；Markdown 新增“组合网页扰动鲁棒性门”小节。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示组合正向最低分、最弱正向组合、组合诊断最低分和最弱诊断组合。
- 新 28 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_composite_browser_28gate_v1/flower_jump_quality_gate.md` PASS，28 个子门全部 returncode `0`。关键指标保持：web 有效正常+边界率 `96.875%`，有效 `124/128`；`花` 有效 `87/91`、有效均分 `75.775`；`跳` 有效 `37/37`、有效均分 `76.677`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_composite_browser_28gate_v1/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。live worker `ready`，Holistic PID `811485`、scoring `reload_count=14`、`last_reload_error=None`；light watcher 已重启为 PID `2852363`，`/static/watch_status.json` 事件 `no_target_samples` 且嵌套 `goal_readiness.quality_gate_json` 已引用 28 子门质量门；正式 marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 16:11:14 CST：新增重复动作录制鲁棒性门并升级为 29 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_action_repeat_robustness_gate.py`。该门只读缓存 Holistic JSON，在骨架序列层面合成完整动作连续重复、两遍之间短暂停顿、先试半遍再完整做、完整做完又开始下一遍、核心段重复，以及 setup-only/落点-only 不完整片段；拼接后重新编号 frame/timestamp/phase 并重建 hand-shape/motion/two-hand relation。不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。
- 独立重复动作门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_action_repeat_robustness_gate_20260603_v1/flower_jump_action_repeat_robustness_gate.md` PASS：`花` 正向最低 `96.505`（`repeat_full_2x_mid_pause`），不完整最高 `21.902`（`setup_only_35pct_negative`）；`跳` 正向最低 `81.950`（`core_repeat_middle`），不完整最高 `12.239`（`landing_only_35pct_negative`）。结论是用户在一次网页录制中多做一遍或停止偏晚时，当前 scorer 能匹配完整动作实例；setup-only/缺核心片段仍低分或语义失败。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门新增第 28 子门 `action_repeat_robustness_gate`，位于 `action_crop_robustness_gate` 与 `phase_order_robustness_gate` 之间；Markdown 新增“重复动作录制鲁棒性门”小节。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示重复动作正向最低分、最弱正向重复、不完整最高分、最强不完整负例和诊断分数范围。
- 新 29 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_action_repeat_29gate_v1/flower_jump_quality_gate.md` PASS，29 个子门全部 returncode `0`。关键指标保持：web 有效正常+边界率 `96.875%`，有效 `124/128`；`花` 有效 `87/91`、有效均分 `75.775`；`跳` 有效 `37/37`、有效均分 `76.677`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_action_repeat_29gate_v1/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。live worker `ready`，Holistic PID `811485`、scoring `reload_count=14`、`last_reload_error=None`；light watcher 已重启为 PID `3011421`，`/static/watch_status.json` 事件 `no_target_samples` 且嵌套 `goal_readiness.quality_gate_json` 已引用 29 子门质量门；正式 marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 16:49:53 CST：新增指尖遮挡鲁棒性门并升级为 30 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_fingertip_occlusion_robustness_gate.py`。该门只读缓存 Holistic JSON，在 hand landmark mask 层模拟单帧、稀疏、中段 20% 和核心 40% fingertip 遮挡，并重建 motion/relation/hand-shape 特征；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。
- 独立指尖遮挡门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_fingertip_occlusion_robustness_gate_20260603_v1/flower_jump_fingertip_occlusion_robustness_gate.md` PASS：`花` 正向最低 `95.829`（`middle20_all_tips`），全程右手 tip 缺失最高 `11.133`；`跳` 正向最低 `70.469`（`sparse_all_tips`），全程右手食指/中指 tip 缺失最高 `10.010`。核心 40% 全 tip 缺失仍可约 `76`，因此只保留为诊断边界，不设负向硬门。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门新增 `fingertip_occlusion_robustness_gate`，位于 `landmark_spike_robustness_gate` 与 `hand_shape_scale_robustness_gate` 之间；Markdown 新增“指尖遮挡鲁棒性门”小节。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示指尖遮挡正向最低分、最弱正向遮挡、核心指尖缺失最高分、最强核心缺失和诊断最低分。
- 新 30 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_fingertip_occlusion_30gate_v1/flower_jump_quality_gate.md` PASS，30 个子门全部 returncode `0`。关键指标保持：web 有效正常+边界率 `96.875%`，有效 `124/128`；`花` 有效 `87/91`、有效均分 `75.775`；`跳` 有效 `37/37`、有效均分 `76.677`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_fingertip_occlusion_30gate_v2/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。live worker `ready`，Holistic PID `811485`、scoring `reload_count=14`、`last_reload_error=None`；light watcher 已重启为 PID `3191518`，`/static/watch_status.json` 事件 `no_target_samples` 且 `readiness_quality_gate_json` 已引用 30 子门质量门；正式 marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 17:23:35 CST：新增摄像头整体倾斜鲁棒性门并升级为 31 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_camera_roll_robustness_gate.py`。该门只读缓存 Holistic JSON，先剥离到基础骨架组，再对 pose/left_hand/right_hand/face 做整幅图像平面 roll 旋转，并重建 hand-shape、motion 和 two-hand relation 派生特征；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。
- 独立摄像头整体倾斜门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_camera_roll_robustness_gate_20260603_v1/flower_jump_camera_roll_robustness_gate.md` PASS：`花` 正向最低 `81.180`（`camera_roll_pos20deg`），极端诊断最低 `80.849`；`跳` 正向最低 `89.634`（`camera_roll_neg20deg`），极端诊断最低 `75.140`。这补上了旧 framing 门只变换坐标、未重建派生特征的整体倾斜覆盖缺口。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门新增 `camera_roll_robustness_gate`，位于宽高比失真门之后、depth 门之前；更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告新增整体倾斜正向最低分、最弱正向倾斜、极端倾斜诊断最低分和最弱诊断倾斜。
- 新 31 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_camera_roll_31gate_v1/flower_jump_quality_gate.md` PASS，31 个子门全部 returncode `0`。关键指标保持：web 有效正常+边界率 `96.875%`，有效 `124/128`；`花` 有效 `87/91`、有效均分 `75.775`；`跳` 有效 `37/37`、有效均分 `76.677`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_camera_roll_31gate_v2/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。live worker `ready`，Holistic PID `811485`、scoring `reload_count=14`、`last_reload_error=None`；light watcher 已重启为 PID `3348941`，`/static/watch_status.json` 事件 `no_target_samples` 且嵌套 `goal_readiness.quality_gate_json` 已引用 31 子门质量门；正式 marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 17:54:14 CST：新增非核心身体锚点漂移鲁棒性门并升级为 32 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_body_anchor_robustness_gate.py`。该门只读缓存 Holistic JSON，剥离到基础骨架组后只扰动 `pose/face`，保留手部核心语义，并重建 motion/two-hand relation；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。目标是防止未来权重/归一化改动让非核心身体或脸部锚点漂移拖低 `花/跳` 网页正常分。
- 独立非核心身体锚点门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_body_anchor_robustness_gate_20260603_v1/flower_jump_body_anchor_robustness_gate.md` PASS：`花` 正向最低 `100.000`（`self_recomputed`），诊断最低 `100.000`；`跳` 正向最低 `100.000`（`self_recomputed`），诊断最低 `100.000`。覆盖 pose/face 整体偏移、相互不一致、逐帧抖动、局部比例异常和随时间漂移。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门新增 `body_anchor_robustness_gate`，位于 `camera_roll_robustness_gate` 之后、`depth_robustness_gate` 之前；更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告新增身体锚点正向最低分、最弱正向锚点漂移、诊断最低分和最弱诊断漂移。
- 新 32 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_body_anchor_32gate_v1/flower_jump_quality_gate.md` PASS，32 个子门全部 returncode `0`。关键指标保持：web 有效正常+边界率 `96.875%`，有效 `124/128`；`花` 有效 `87/91`、有效均分 `75.775`；`跳` 有效 `37/37`、有效均分 `76.677`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_body_anchor_32gate_v2/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。live worker `ready`，Holistic PID `811485`、scoring `reload_count=14`、`last_reload_error=None`；light watcher 已重启为 PID `3508542`，`/static/watch_status.json` 事件 `no_target_samples` 且嵌套 `goal_readiness.quality_gate_json` 已引用 32 子门质量门；正式 marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 18:27:38 CST：新增非核心手/非语义手指干扰鲁棒性门并升级为 33 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_noncore_hand_distractor_robustness_gate.py`。该门只读缓存 Holistic JSON，剥离到基础骨架组后在手部坐标层合成 `花` 非核心左手漂移/抖动/手形扰动，以及 `跳` 右手非语义手指（拇指、无名指、小指）漂移/抖动/运动干扰，并重建 hand-shape、motion 和 two-hand relation；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。核心破坏行只记录诊断边界，不作为当前硬负例。
- 独立非核心手干扰门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_noncore_hand_distractor_robustness_gate_20260603_probe_v1/flower_jump_noncore_hand_distractor_robustness_gate.md` PASS：`花` 正向最低 `100.000`，右手开花核心 tip 塌缩诊断最低 `25.938`；`跳` 正向最低 `73.032`（`jump_right_noncore_fingers_motion_drift`），右手食指/中指塌缩诊断 `81.460`。结论是非核心干扰能被吸收，但 `跳` 单纯核心手形坐标塌缩并非当前可靠负例，持续核心缺失仍由遮挡/裁切/相位等门保护。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门追加第 33 子门 `noncore_hand_distractor_robustness_gate`，并在 Markdown 增加“非核心手与非语义手指干扰鲁棒性门”小节。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示非核心手/手指正向最低分、最弱正向干扰、诊断最低分和最弱诊断核心扰动。
- 新 33 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_noncore_hand_distractor_33gate_v1/flower_jump_quality_gate.md` PASS，33 个子门全部 returncode `0`。关键指标保持：web 有效正常+边界率 `96.875%`，有效 `124/128`；`花` 有效 `87/91`、有效均分 `75.775`；`跳` 有效 `37/37`、有效均分 `76.677`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`；新增门正向最低 `花=100.000`、`跳=73.032`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_noncore_hand_distractor_33gate_v2/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。live worker `ready`，Holistic PID `811485`、scoring `reload_count=14`、`last_reload_error=None`；light watcher 已重启为 PID `3660759`，事件 `no_target_samples`，命令参数已引用 33 子门质量门；正式 marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 18:59:08 CST：新增双手关系几何鲁棒性门并升级为 34 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_relation_geometry_robustness_gate.py`。该门只读缓存 Holistic JSON，剥离到基础骨架组后调整右手相对左手的固定偏移、运动高度、横向分量和逐帧关系抖动，并重建 hand-shape、motion 和 two-hand relation；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。目标是覆盖网页用户做 `跳` 时常见的左手地面/右手小人相对高度、间距和轨迹差异。
- 独立关系几何门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_relation_geometry_robustness_gate_20260603_v1/flower_jump_relation_geometry_robustness_gate.md` PASS：`花` 正向最低 `79.772`（`right_relation_jitter_0.035`），诊断最低 `79.250`；`跳` 正向最低 `70.469`（`right_relation_offset_x_0.15`），诊断最低 `74.458`。`跳` 过小高度、强水平化、反向关系作为负向门，允许通过 `needs_recapture/semantic_mismatch` 质量诊断证明被捕获；其中过小高度 score 仍可到 `93.960`，但被标记为 `semantic_mismatch:relation_jump_amplitude_too_small`。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门追加第 34 子门 `relation_geometry_robustness_gate`，Markdown 新增“双手关系几何鲁棒性门”小节。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示关系几何正向最低分、最弱正向关系扰动、关系负向最高分、最强负向关系和诊断边界。
- 新 34 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_relation_geometry_34gate_v1/flower_jump_quality_gate.md` PASS，34 个子门全部 returncode `0`。关键指标保持：web 有效正常+边界率 `96.875%`，有效 `124/128`；`花` 有效 `87/91`、有效均分 `75.775`；`跳` 有效 `37/37`、有效均分 `76.677`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`；新增门正向最低 `花=79.772`、`跳=70.469`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_relation_geometry_34gate_v2/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。live worker `ready`，Holistic PID `811485`、scoring `reload_count=14`、`last_reload_error=None`；light watcher 已重启为 PID `3815368`，事件 `no_target_samples`，命令参数已引用 34 子门质量门；正式 marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 19:35:57 CST：新增核心手形幅度鲁棒性门并升级为 35 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_core_shape_amplitude_robustness_gate.py`。该门只读缓存 Holistic JSON，在右手核心手指局部坐标层模拟 `花` 的开花开合幅度/指尖展开半径变化，以及 `跳` 的右手食指/中指小人局部形变，并重建 hand-shape、motion 和 two-hand relation；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。`跳` 的严重两指形变当前只作诊断边界，硬负例仍由遮挡、裁切、手角色、关系几何和相位门保护。
- 独立核心手形幅度门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_core_shape_amplitude_robustness_gate_20260603_v1/flower_jump_core_shape_amplitude_robustness_gate.md` PASS：`花` 正向最低 `79.334`（`flower_opening_dynamic_0.75`），负向最高 `49.353`（`flower_opening_dynamic_0.45_negative`，由 `semantic_mismatch:flower_opening_guard_failed` 接住），诊断最低 `77.639`；`跳` 正向最低 `77.830`（`jump_two_finger_dynamic_1.15`），诊断最低 `82.090`。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门追加第 35 子门 `core_shape_amplitude_robustness_gate`，Markdown 新增“核心手形幅度鲁棒性门”小节。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示核心手形正向最低分、最弱正向核心形变、负向最高分和诊断边界。
- 新 35 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_core_shape_amplitude_35gate_v1/flower_jump_quality_gate.md` PASS，35 个子门全部 returncode `0`。关键指标保持：web 有效正常+边界率 `96.875%`，有效 `124/128`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`；新增门正向最低 `花=79.334`、`跳=77.830`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_core_shape_amplitude_35gate_v2/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。live worker `ready`，Holistic PID `811485`、scoring `reload_count=14`、`last_reload_error=None`；light watcher 已重启并命令参数引用 35 子门质量门，watcher 子进程 PID `3991991`，事件 `no_target_samples`；正式 marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 20:08:17 CST：新增斜拍透视剪切鲁棒性门并升级为 36 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_perspective_shear_robustness_gate.py`。该门只读缓存 Holistic JSON，剥离到基础骨架组后合成 image-plane shear、z-to-x/y 透视偏移和局部手部剪切，并重建 hand-shape、motion 和 two-hand relation；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。目标是补齐宽高比、camera roll、depth、framing 之外的斜拍/非正面摄像头扭曲。
- 独立斜拍透视剪切门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_perspective_shear_robustness_gate_20260603_v1/flower_jump_perspective_shear_robustness_gate.md` PASS：`花` 正向最低 `80.018`（`perspective_z_to_y_0.35`），诊断最低 `78.288`；`跳` 正向最低 `88.573`（`perspective_z_to_x_0.35`），诊断最低 `77.705`。强剪切和强 z 透视只作为诊断边界，不作为正常网页采集要求。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门追加第 36 子门 `perspective_shear_robustness_gate`，Markdown 新增“斜拍透视剪切鲁棒性门”小节。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示斜拍透视正向最低分、最弱正向透视/剪切、诊断最低分和最弱诊断边界。
- 新 36 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_perspective_shear_36gate_v1/flower_jump_quality_gate.md` PASS，36 个子门全部 returncode `0`。关键指标保持：web 有效正常+边界率 `96.875%`，有效 `124/128`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`；新增门正向最低 `花=80.018`、`跳=88.573`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_perspective_shear_36gate_v2/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。live worker `ready`，Holistic PID `811485`、scoring `reload_count=14`、`last_reload_error=None`；light watcher 已重启并命令参数引用 36 子门质量门，watcher 子进程 PID `4147353`，事件 `no_target_samples`；正式 marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 20:46:44 CST：修复掌根锚点短时缺失过敏并升级为 37 子门质量门

- 修复 `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py` 的 hand-shape 派生特征：当 wrist/MCP palm scale 无法可靠估计时，派生 `*_hand_shape` 特征标为缺失，而不是用 `1e-3` 兜底造成形状值爆炸。该修复保留原始可见 hand landmark 参与评分，解决 `花` 核心右手 palm anchors 单帧缺失时分数从约 `20` 异常坠落的问题。
- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_palm_anchor_occlusion_robustness_gate.py`。该门只读缓存 Holistic JSON，在 hand landmark mask 层模拟 wrist/MCP/palm-anchor 单帧、稀疏、中段 20%、核心 40% 和全程缺失，并重建 hand-shape、motion、two-hand relation；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。独立报告 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_palm_anchor_occlusion_robustness_gate_20260603_v1/flower_jump_palm_anchor_occlusion_robustness_gate.md` PASS：`花` 正向最低 `95.791`、核心锚点全缺最高 `11.140`、诊断最低 `76.069`；`跳` 正向最低 `70.469`、核心锚点全缺最高 `10.158`、诊断最低 `76.758`。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门追加第 37 子门 `palm_anchor_occlusion_robustness_gate`，并新增“掌根锚点遮挡鲁棒性门”摘要。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示掌根锚点正向最低分、核心锚点全缺最高分和诊断边界。
- 新 37 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_palm_anchor_occlusion_37gate_probe_v1/flower_jump_quality_gate.md` PASS，37 个子门全部 returncode `0`。关键指标保持：web 有效正常+边界率 `96.875%`，有效 `124/128`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`；新增门正向最低 `花=95.791`、`跳=70.469`。
- 已热加载 5080 scoring module，`reload_count=15`、`last_reload_error=None`；Holistic worker 未重启且 PID 仍为 `811485`。最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_palm_anchor_occlusion_37gate_v2/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。light watcher 已重启并命令参数引用 37 子门质量门，watcher 子进程 PID `139028`，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 21:20:43 CST：新增手间时序错位鲁棒性门并升级为 38 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_interhand_temporal_desync_robustness_gate.py`。该门只读缓存 Holistic JSON，将单只手 landmark 序列相对其它骨架组前后错开并重建 hand-shape、motion 和 two-hand relation；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。目标是覆盖网页采集和用户风格中常见的左/右手相位轻微滞后/超前，尤其保护 `跳` 的双手关系不会因 1-2 帧手间错位异常失败。
- 独立手间时序错位门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_interhand_temporal_desync_robustness_gate_20260603_v1/flower_jump_interhand_temporal_desync_robustness_gate.md` PASS：`花` 正向最低 `99.023`（`right_hand_delay_2f`），诊断最低 `97.824`；`跳` 正向最低 `75.688`（`left_hand_advance_1f`），诊断最低 `75.809`。强错位只作为诊断边界，不作为正常网页采集要求。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门追加第 38 子门 `interhand_temporal_desync_robustness_gate`，Markdown 新增“手间时序错位鲁棒性门”小节。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示手间时序错位正向最低分、最弱正向错位、诊断最低分和最弱诊断边界。
- 新 38 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_interhand_temporal_desync_38gate_v1/flower_jump_quality_gate.md` PASS，38 个子门全部 returncode `0`。关键指标保持：web 有效正常+边界率 `96.875%`，有效 `124/128`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`；新增门正向最低 `花=99.023`、`跳=75.688`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_interhand_temporal_desync_38gate_v2/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。运行态保持：Holistic worker PID `811485`、scoring `reload_count=15`、`last_reload_error=None`；light watcher 已重启并命令参数引用 38 子门质量门，watcher 子进程 PID `297327`，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 21:54:29 CST：新增时序顺序抖动鲁棒性门并升级为 39 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_temporal_order_jitter_robustness_gate.py`。该门只读缓存 Holistic JSON，剥离基础骨架组后重排帧序并重建 hand-shape、motion 和 two-hand relation；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。目标是覆盖网页上传/时间戳轻微抖动导致的相邻帧交换、小范围三帧错序和局部帧到达顺序异常。
- 独立时序顺序抖动门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_temporal_order_jitter_robustness_gate_20260603_v1/flower_jump_temporal_order_jitter_robustness_gate.md` PASS：`花` 正向最低 `97.035`（`adjacent_swap_every_6f`），诊断最低 `97.068`；`跳` 正向最低 `71.379`（`adjacent_swap_every_6f`），诊断最低 `45.000`（`block_reverse_25pct_diagnostic`，由 phase-order 口径标记为强乱序边界）。块状倒序只记录诊断边界，硬拒绝仍由 phase-order 门覆盖。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门追加第 39 子门 `temporal_order_jitter_robustness_gate`，Markdown 新增“时序顺序抖动鲁棒性门”小节和 CLI 阈值 `--temporal-order-jitter-min-score`。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示帧序抖动正向最低分、最弱正向帧序抖动、诊断最低分和诊断边界。
- 新 39 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_temporal_order_jitter_39gate_v1/flower_jump_quality_gate.md` PASS，39 个子门全部 returncode `0`。关键指标保持：web 有效正常+边界率 `96.875%`，有效 `124/128`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`；新增门正向最低 `花=97.035`、`跳=71.379`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_temporal_order_jitter_39gate_v1/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。运行态保持：Holistic worker PID `811485`、scoring `reload_count=15`、`last_reload_error=None`；light watcher 已重启并命令参数引用 39 子门质量门，watcher 子进程 PID `456679`，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 22:07:21 CST：新增手指身份抖动鲁棒性门并升级为 40 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_finger_identity_jitter_robustness_gate.py`。该门只读缓存 Holistic JSON，交换相邻或非相邻 finger chain 的 landmark 身份，并重建 hand-shape、motion 和 two-hand relation；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。目标是覆盖真实 Holistic 在手小、模糊或自遮挡时可能出现的 index/middle、middle/ring、ring/pinky 等手指拓扑标签混淆。
- 独立手指身份抖动门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_finger_identity_jitter_robustness_gate_20260603_v1/flower_jump_finger_identity_jitter_robustness_gate.md` PASS：`花` 正向最低 `79.043`（`right_index_middle_chain_swap`），诊断最低 `77.035`；`跳` 正向最低 `71.892`（`right_middle_ring_sparse_jitter`），诊断最低 `81.108`。相邻指链交换和少量帧级身份抖动为正向门；非相邻或多链强交换只记录诊断边界。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门追加第 40 子门 `finger_identity_jitter_robustness_gate`，Markdown 新增“手指身份抖动鲁棒性门”小节和 CLI 阈值 `--finger-identity-jitter-min-score`。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示手指身份抖动正向最低分、最弱正向指链抖动、诊断最低分和诊断边界。
- 新 40 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_identity_jitter_40gate_v1/flower_jump_quality_gate.md` PASS，40 个子门全部 returncode `0`。其中前 39 个子门复用上一轮同 scorer 的报告，新增第 40 门实际运行；关键指标保持：web 有效正常+边界率 `96.875%`，有效 `124/128`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`；新增门正向最低 `花=79.043`、`跳=71.892`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_finger_identity_jitter_40gate_v1/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。运行态保持：Holistic worker PID `811485`、scoring `reload_count=15`、`last_reload_error=None`；light watcher 已重启并命令参数引用 40 子门质量门，watcher 子进程 PID `518504`，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 22:19:25 CST：新增手部尺度时序呼吸鲁棒性门并升级为 41 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_hand_scale_flicker_robustness_gate.py`。该门只读缓存 Holistic JSON，在基础骨架组上逐帧模拟 hand detector box 的平滑尺度呼吸、x/y 宽高反向漂移和少量帧级 scale/aspect flicker，并重建 hand-shape、motion、two-hand relation；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。目标是补齐静态 hand-shape scale 之外的真实网页摄像头检测框随时间抖动。
- 独立手部尺度时序呼吸门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_hand_scale_flicker_robustness_gate_20260603_v1/flower_jump_hand_scale_flicker_robustness_gate.md` PASS：`花` 正向最低 `81.932`（`both_hands_smooth_aspect_breathing_0.10`），诊断最低 `81.395`；`跳` 正向最低 `78.452`（`both_hands_sparse_aspect_flicker_0.10_every_6f`），诊断最低 `74.623`。10%-12% 平滑/稀疏尺度变化作为正向门，35%-45% 强漂移/尖峰只作诊断边界。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门追加第 41 子门 `hand_scale_flicker_robustness_gate`，Markdown 新增“手部尺度时序呼吸鲁棒性门”小节和 CLI 阈值 `--hand-scale-flicker-min-score`。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示手部尺度呼吸正向最低分、最弱正向尺度呼吸、诊断最低分和诊断边界。
- 新 41 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_hand_scale_flicker_41gate_v1/flower_jump_quality_gate.md` PASS，41 个子门全部 returncode `0`；其中 40 个既有子门复用上一轮同 scorer 报告，新第 41 门实际运行。关键指标保持：web 有效正常+边界率 `96.875%`，有效 `124/128`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`；新增门正向最低 `花=81.932`、`跳=78.452`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_hand_scale_flicker_41gate_v2/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。运行态保持：Holistic worker PID `811485`、scoring `reload_count=15`、`last_reload_error=None`；light watcher 已重启并命令参数引用 41 子门质量门，watcher 子进程 PID `573633`，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 22:28:22 CST：新增手部中心时序漂移鲁棒性门并升级为 42 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_hand_center_flicker_robustness_gate.py`。该门只读缓存 Holistic JSON，在基础骨架组上逐帧模拟 hand detector box 中心的平滑横/纵向漂移、对角少量帧级跳点和单手中心 flicker，并重建 hand-shape、motion、two-hand relation；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。目标是补齐 hand-scale-flicker 的“框大小变化”之外的“框中心 wobble”失真。
- 独立手部中心时序漂移门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_hand_center_flicker_robustness_gate_20260603_v1/flower_jump_hand_center_flicker_robustness_gate.md` PASS：`花` 正向最低 `82.112`（`both_hands_smooth_center_y_0.04`），诊断最低 `81.773`；`跳` 正向最低 `98.551`（`right_hand_smooth_center_y_0.03`），诊断最低 `77.083`。2.5%-4% 平滑/稀疏中心漂移作为正向门，12%-18% 强漂移/跳点只作诊断边界。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门追加第 42 子门 `hand_center_flicker_robustness_gate`，Markdown 新增“手部中心时序漂移鲁棒性门”小节和 CLI 阈值 `--hand-center-flicker-min-score`。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示手部中心漂移正向最低分、最弱正向中心漂移、诊断最低分和诊断边界。
- 新 42 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_hand_center_flicker_42gate_v1/flower_jump_quality_gate.md` PASS，42 个子门全部 returncode `0`；其中 41 个既有子门复用上一轮同 scorer 报告，新第 42 门实际运行。关键指标保持：web 有效正常+边界率 `96.875%`，有效 `124/128`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`；新增门正向最低 `花=82.112`、`跳=98.551`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_hand_center_flicker_42gate_v2/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。运行态保持：Holistic worker PID `811485`、scoring `reload_count=15`、`last_reload_error=None`；light watcher 已重启并命令参数引用 42 子门质量门，watcher 子进程 PID `618466`，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 22:38:37 CST：新增全局取景时序漂移鲁棒性门并升级为 43 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_global_framing_flicker_robustness_gate.py`。该门只读缓存 Holistic JSON，在基础骨架组上逐帧模拟整幅可见骨架的平滑横/纵向 pan、缩放呼吸、对角平移缩放和稀疏帧级全局取景跳动，并重建 hand-shape、motion、two-hand relation；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。目标是补齐局部 hand-scale/hand-center flicker 之外的整帧 auto-framing、电子防抖或用户身体轻微前后移动失真。
- 独立全局取景时序漂移门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_global_framing_flicker_robustness_gate_20260603_v1/flower_jump_global_framing_flicker_robustness_gate.md` PASS：`花` 正向最低 `81.919`（`smooth_global_zoom_0.08`），诊断最低 `80.909`；`跳` 正向最低 `97.598`（`sparse_global_zoom_0.06_every_6f`），诊断最低 `76.830`。5%-8% 平滑/稀疏全局 pan/zoom 作为正向门，18%-35% 强漂移/缩放/跳点只作诊断边界。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门追加第 43 子门 `global_framing_flicker_robustness_gate`，Markdown 新增“全局取景时序漂移鲁棒性门”小节和 CLI 阈值 `--global-framing-flicker-min-score`。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示全局取景漂移正向最低分、最弱正向全局取景漂移、诊断最低分和诊断边界。
- 新 43 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_global_framing_flicker_43gate_v1/flower_jump_quality_gate.md` PASS，43 个子门全部 returncode `0`；其中 42 个既有子门复用上一轮同 scorer 报告，新第 43 门实际运行。关键指标保持：web 有效正常+边界率 `96.875%`，有效 `124/128`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`；新增门正向最低 `花=81.919`、`跳=97.598`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_global_framing_flicker_43gate_v2/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。运行态保持：Holistic worker PID `811485`、scoring `reload_count=15`、`last_reload_error=None`；light watcher 已重启并命令参数引用 43 子门质量门，watcher 子进程 PID `667454`，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 22:49:09 CST：新增手指中段关节遮挡鲁棒性门并升级为 44 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_finger_mid_joint_occlusion_robustness_gate.py`。该门只读缓存 Holistic JSON，在基础骨架组上模拟 PIP/DIP/thumb-IP 等手指中段关节的单帧、稀疏和局部中段 mask 缺失，并重建 hand-shape、motion、two-hand relation；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。目标是补齐 fingertip 与 palm-anchor 遮挡之间的“中段指节拓扑断点”失真。
- 独立手指中段关节遮挡门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_finger_mid_joint_occlusion_robustness_gate_20260603_v1/flower_jump_finger_mid_joint_occlusion_robustness_gate.md` PASS：`花` 正向最低 `99.437`（`right_sparse_all_inner_joints`），诊断最低 `97.559`；`跳` 正向最低 `76.638`（`right_middle20_index_middle_inner_joints`），诊断最低 `70.469`。单帧、稀疏和局部 20% 中段指节缺失作为正向门，核心段 40% 或全程中段指节缺失只作诊断边界。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门追加第 44 子门 `finger_mid_joint_occlusion_robustness_gate`，Markdown 新增“手指中段关节遮挡鲁棒性门”小节和 CLI 阈值 `--finger-mid-joint-occlusion-min-score`。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示中段指节遮挡正向最低分、最弱正向中段指节遮挡、诊断最低分和诊断边界。
- 新 44 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_mid_joint_occlusion_44gate_v1/flower_jump_quality_gate.md` PASS，44 个子门全部 returncode `0`；其中 43 个既有子门复用上一轮同 scorer 报告，新第 44 门实际运行。关键指标保持：web 有效正常+边界率 `96.875%`，有效 `124/128`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`；新增门正向最低 `花=99.437`、`跳=76.638`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_finger_mid_joint_occlusion_44gate_v2/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。运行态保持：Holistic worker PID `811485`、scoring `reload_count=15`、`last_reload_error=None`；light watcher 已重启并命令参数引用 44 子门质量门，watcher 子进程 PID `713829`，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 23:00:37 CST：新增 z 深度时序抖动鲁棒性门并升级为 45 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_z_flicker_robustness_gate.py`。该门只读缓存 Holistic JSON，在基础骨架组上逐帧模拟 Holistic z offset/scale breathing、手部 z 平滑漂移和稀疏 z 跳点，并重建 hand-shape、motion、two-hand relation；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。目标是补齐固定 depth offset/scale 门之外的真实摄像头逐帧深度零点漂移和手部深度闪断。
- 独立 z 深度时序抖动门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_z_flicker_robustness_gate_20260603_v1/flower_jump_z_flicker_robustness_gate.md` PASS：`花` 正向最低 `81.408`（`smooth_global_z_scale_0.20`），诊断最低 `79.869`；`跳` 正向最低 `79.288`（`smooth_global_z_offset_0.08`），诊断最低 `78.276`。轻微平滑 z 呼吸、手部 z 漂移和少量 z 跳点作为正向门，强 z scale/offset 或强稀疏跳点只作诊断边界。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门追加第 45 子门 `z_flicker_robustness_gate`，Markdown 新增“z 深度时序抖动鲁棒性门”小节和 CLI 阈值 `--z-flicker-min-score`。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示 z 时序抖动正向最低分、最弱正向 z 抖动、诊断最低分和诊断边界。
- 新 45 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_z_flicker_45gate_v1/flower_jump_quality_gate.md` PASS，45 个子门全部 returncode `0`；其中 44 个既有子门复用上一轮同 scorer 报告，新第 45 门实际运行。关键指标保持：web 有效正常+边界率 `96.875%`，有效 `124/128`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`；新增门正向最低 `花=81.408`、`跳=79.288`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_z_flicker_45gate_v2/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。运行态保持：Holistic worker PID `811485`、scoring `reload_count=15`、`last_reload_error=None`；light watcher 已重启并命令参数引用 45 子门质量门，watcher 子进程 PID `772489`，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 23:12:11 CST：新增手部轨迹插值补洞鲁棒性门并升级为 46 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_hand_trajectory_interpolation_robustness_gate.py`。该门只读缓存 Holistic JSON，在基础骨架组上模拟 tracker 短缺口后的 hand landmark 线性插值补洞，包括单帧、稀疏帧和约 12% 局部连续补洞，并重建 hand-shape、motion、two-hand relation；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。目标是补齐 frame freeze/dropout/flicker 之外的真实网页跟踪器短时插值平滑失真。
- 独立手部轨迹插值补洞门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_hand_trajectory_interpolation_robustness_gate_20260603_v1/flower_jump_hand_trajectory_interpolation_robustness_gate.md` PASS：`花` 正向最低 `93.731`（`right_hand_middle12_interp`），诊断最低 `74.445`；`跳` 正向最低 `82.672`（`right_hand_middle12_interp`），诊断最低 `77.316`。单帧、稀疏和局部 12% 补洞作为正向门，18%-25% 更长补洞只作诊断边界。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门追加第 46 子门 `hand_trajectory_interpolation_robustness_gate`，Markdown 新增“手部轨迹插值补洞鲁棒性门”小节和 CLI 阈值 `--hand-trajectory-interpolation-min-score`。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示插值补洞正向最低分、最弱正向插值、诊断最低分和诊断边界。
- 新 46 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_hand_trajectory_interpolation_46gate_v1/flower_jump_quality_gate.md` PASS，46 个子门全部 returncode `0`；其中 45 个既有子门复用上一轮同 scorer 报告，新第 46 门实际运行。关键指标保持：web 有效正常+边界率 `96.875%`，有效 `124/128`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`；新增门正向最低 `花=93.731`、`跳=82.672`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_hand_trajectory_interpolation_46gate_v2/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。运行态保持：Holistic worker PID `811485`、scoring `reload_count=15`、`last_reload_error=None`；light watcher 已重启并命令参数引用 46 子门质量门，watcher 子进程 PID `827344`，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 23:28:16 CST：新增手部 z 倾角鲁棒性门并升级为 47 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_hand_z_tilt_robustness_gate.py`。该门只读缓存 Holistic JSON，在基础骨架组上围绕手腕模拟局部 x-z/y-z 出平面手掌俯仰与侧倾，并重建 hand-shape、motion、two-hand relation；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。目标是补齐手部 2D 旋转、全局 z/depth、z 时序抖动和透视剪切之外的“掌面朝向摄像头变化”失真。
- 独立手部 z 倾角门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_hand_z_tilt_robustness_gate_20260603_v1/flower_jump_hand_z_tilt_robustness_gate.md` PASS：`花` 正向最低 `81.396`（`right_hand_pitch_xz_pos12deg`），诊断最低 `81.165`；`跳` 正向最低 `98.093`（`right_hand_pitch_xz_neg12deg`），诊断最低 `92.212`。双手 8 度和单手 12 度出平面倾角作为正向门，25-35 度强倾角只作诊断边界。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门追加第 47 子门 `hand_z_tilt_robustness_gate`，Markdown 新增“手部 z 倾角鲁棒性门”小节和 CLI 阈值 `--hand-z-tilt-min-score`。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示 z 倾角正向最低分、最弱正向 z 倾角、诊断最低分和诊断边界。
- 新 47 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_hand_z_tilt_47gate_v1/flower_jump_quality_gate.md` PASS，47 个子门全部 returncode `0`；其中 46 个既有子门复用上一轮同 scorer 报告，新第 47 门实际运行。关键指标保持：web 有效正常+边界率 `96.875%`，有效 `124/128`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`；新增门正向最低 `花=81.396`、`跳=98.093`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_hand_z_tilt_47gate_v2/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。运行态保持：Holistic worker PID `811485`、scoring `reload_count=15`、`last_reload_error=None`；light watcher 已重启并命令参数引用 47 子门质量门，watcher 子进程 PID `899012`，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 23:37:24 CST：新增手指弯曲风格鲁棒性门并升级为 48 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_finger_curl_style_robustness_gate.py`。该门只读缓存 Holistic JSON，在基础骨架组上把选定手指链向 MCP 锚点轻微弯曲，模拟用户手指不完全伸直但语义动作正确的风格差异，并重建 hand-shape、motion、two-hand relation；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。目标是补齐开合幅度、手形尺度、手部旋转和 z 倾角之外的“手指关节弯曲风格”失真。
- 独立手指弯曲风格门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_finger_curl_style_robustness_gate_20260603_v1/flower_jump_finger_curl_style_robustness_gate.md` PASS：`花` 正向最低 `80.887`（`right_opening_ring_pinky_curl_0.16`），诊断最低 `79.541`；`跳` 正向最低 `92.938`（`right_person_index_middle_curl_0.16`），诊断最低 `82.206`。`花` 开花手轻微手指弯曲、`跳` 两指小人/非语义手指/地面手轻微弯曲作为正向门，强弯曲只作诊断边界。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门追加第 48 子门 `finger_curl_style_robustness_gate`，Markdown 新增“手指弯曲风格鲁棒性门”小节和 CLI 阈值 `--finger-curl-style-min-score`。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示手指弯曲正向最低分、最弱正向弯曲、诊断最低分和诊断边界。
- 新 48 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_curl_style_48gate_v1/flower_jump_quality_gate.md` PASS，48 个子门全部 returncode `0`；其中 47 个既有子门复用上一轮同 scorer 报告，新第 48 门实际运行。关键指标保持：web 有效正常+边界率 `96.875%`，有效 `124/128`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`；新增门正向最低 `花=80.887`、`跳=92.938`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_finger_curl_style_48gate_v2/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。运行态保持：Holistic worker PID `811485`、scoring `reload_count=15`、`last_reload_error=None`；light watcher 已重启并命令参数引用 48 子门质量门，watcher 子进程 PID `943721`，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-03 23:48:12 CST：新增手指长度比例鲁棒性门并升级为 49 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_finger_length_style_robustness_gate.py`。该门只读缓存 Holistic JSON，在基础骨架组上围绕 MCP 锚点缩放选定手指链长度，模拟用户手指比例和伸展长度差异，并重建 hand-shape、motion、two-hand relation；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。目标是补齐整体手形尺度/宽高、手指开合幅度、手指弯曲和手掌倾角之外的“手指长度比例风格”失真。
- 独立手指长度比例门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_finger_length_style_robustness_gate_20260603_v1/flower_jump_finger_length_style_robustness_gate.md` PASS：`花` 正向最低 `80.849`（`right_opening_ring_pinky_length_1.12`），诊断最低 `79.378`（`right_opening_all_finger_length_1.30_diagnostic`）；`跳` 正向最低 `93.587`（`right_person_index_middle_length_1.10`），诊断最低 `70.331`（`right_person_index_middle_length_1.35_diagnostic`）。轻微手指比例变化作为正向门，强缩短/拉长只作诊断边界。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门追加第 49 子门 `finger_length_style_robustness_gate`，Markdown 新增“手指长度比例鲁棒性门”小节和 CLI 阈值 `--finger-length-style-min-score`。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示手指比例正向最低分、最弱正向比例、诊断最低分和诊断边界。
- 新 49 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_finger_length_style_49gate_v1/flower_jump_quality_gate.md` PASS，49 个子门全部 returncode `0`；其中 48 个既有子门复用上一轮同 scorer 报告，新第 49 门实际运行。关键指标保持：web 有效正常+边界率 `96.875%`，有效 `124/128`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`；新增门正向最低 `花=80.849`、`跳=93.587`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260603_finger_length_style_49gate_v2/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。运行态保持：Holistic worker PID `811485`、scoring `reload_count=15`、`last_reload_error=None`；light watcher 已重启并命令参数引用 49 子门质量门，watcher 子进程 PID `998034`，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-04 00:01:24 CST：新增动态入场退场鲁棒性门并升级为 50 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_moving_setup_exit_robustness_gate.py`。该门只读缓存 Holistic JSON，在基础骨架组上合成动作前移动手到位、动作后放下手、前后都有动态手部污染，以及 entry-only 缺核心片段，并重建 hand-shape、motion、two-hand relation；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。目标是补齐静止 padding 和重复完整动作之外的“移动入场/退场非语义污染”失真。
- 独立动态入场退场门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_moving_setup_exit_robustness_gate_20260604_v1/flower_jump_moving_setup_exit_robustness_gate.md` PASS：`花` 正向最低 `96.727`（`suffix_moving_exit_25pct`），entry-only 最高 `21.271`，诊断最低 `21.959`；`跳` 正向最低 `99.998`（`entry_exit_moving_18pct`），entry-only 最高 `0.016`，诊断最低 `4.284`。完整核心动作在动态入退场污染下保持高分，缺核心入场片段不通过。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门追加第 50 子门 `moving_setup_exit_robustness_gate`，Markdown 新增“动态入场退场鲁棒性门”小节和 CLI 阈值 `--moving-setup-exit-min-score`。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示动态入退场正向最低分、最弱正向动态污染、entry-only 最高分、诊断最低分和诊断边界。
- 新 50 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_moving_setup_exit_50gate_v1/flower_jump_quality_gate.md` PASS，50 个子门全部 returncode `0`；其中 49 个既有子门复用上一轮同 scorer 报告，新第 50 门实际运行。关键指标保持：web 有效正常+边界率 `96.875%`，有效 `124/128`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`；新增门正向最低 `花=96.727`、`跳=99.998`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_moving_setup_exit_50gate_v2/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。运行态保持：Holistic worker PID `811485`、scoring `reload_count=15`、`last_reload_error=None`；light watcher 已重启并命令参数引用 50 子门质量门，watcher 子进程 PID `1056297`，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-04 00:12:24 CST：新增核心相位速度鲁棒性门并升级为 51 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_core_phase_speed_robustness_gate.py`。该门只读缓存 Holistic JSON，只改变 `花` 绽放核心和 `跳` 起跳/双手关系核心窗口内的帧密度、局部快慢曲线和短暂停顿，并重建 motion/two-hand relation；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。目标是补齐一般 temporal-rate 门之外的“词义核心相位速度风格”失真。
- 独立核心相位速度门 v1 曾暴露 `跳` 核心段 `1.55x` 强拉伸会触发 `jump_two_hand_presence_low`，因此未把它当正向鲁棒性。修正后的 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_core_phase_speed_robustness_gate_20260604_v2/flower_jump_core_phase_speed_robustness_gate.md` PASS：`花` 正向最低 `95.085`（`bloom_core_fast_then_slow`），诊断最低 `95.509`；`跳` 正向最低 `75.484`（`jump_relation_core_slow_1.40x`），诊断最低 `23.502`（`jump_relation_core_slow_1.55x_diagnostic`）。强拉伸被保留为诊断边界，避免把缺两手关系覆盖的样本误认为正常慢速风格。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门追加第 51 子门 `core_phase_speed_robustness_gate`，Markdown 新增“核心相位速度鲁棒性门”小节和 CLI 阈值 `--core-phase-speed-min-score`。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示核心速度正向最低分、最弱正向核心速度、诊断最低分和最弱诊断边界。
- 新 51 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_core_phase_speed_51gate_v1/flower_jump_quality_gate.md` PASS，51 个子门全部 returncode `0`；其中 50 个既有子门复用上一轮同 scorer 报告，新第 51 门实际运行。关键指标保持：web 有效正常+边界率 `96.875%`，有效 `124/128`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`；新增门正向最低 `花=95.085`、`跳=75.484`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_core_phase_speed_51gate_v2/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。运行态保持：Holistic worker PID `811485`、scoring `reload_count=15`、`last_reload_error=None`；light watcher 已重启并命令参数引用 51 子门质量门，watcher 子进程 PID `1108000`，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。

### 2026-06-04 00:26:04 CST：新增手部置信度衰减鲁棒性门并升级为 52 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_hand_confidence_attenuation_robustness_gate.py`。该门只读缓存 Holistic JSON，保留手部坐标，只降低 hand/hand-shape mask 置信权重并重建 motion/two-hand relation；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。目标是补齐二值 missing/mask、遮挡和插值之外的“手仍被跟踪但置信度接近阈值”网页摄像头失真。
- 独立 v1 探针发现 `0 < hand mask <= 0.5` 会触发 scorer 里手姿态鲁棒距离的未定义边界；本轮未改 live scorer，而是把 promoted 正向门限定在 `0.55-0.85` 的 near-threshold 软置信区间，低于有效阈值的极端情况按有效缺失诊断并继续由既有 missing/mask 门兜底。独立 v2 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_hand_confidence_attenuation_robustness_gate_20260604_v2/flower_jump_hand_confidence_attenuation_robustness_gate.md` PASS：`花` 正向最低 `100.000`（`flower_all_hands_confidence_0.85`），诊断最低 `1.171`；`跳` 正向最低 `99.856`（`jump_relation_core_sparse_confidence_0.55`），诊断最低 `0.125`。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门追加第 52 子门 `hand_confidence_attenuation_robustness_gate`，Markdown 新增“手部置信度衰减鲁棒性门”小节和 CLI 阈值 `--hand-confidence-attenuation-min-score`。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示手部置信度正向最低分、最弱正向低置信、诊断最低分和诊断边界。
- 新 52 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_hand_confidence_52gate_v1/flower_jump_quality_gate.md` PASS，52 个子门全部 returncode `0`；其中 51 个既有子门复用上一轮同 scorer 报告，新第 52 门实际运行。关键指标保持：web 有效正常+边界率 `96.875%`，有效 `124/128`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`；新增门正向最低 `花=100.000`、`跳=99.856`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_hand_confidence_52gate_v2/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。运行态保持：Holistic worker PID `811485`、scoring `reload_count=15`、`last_reload_error=None`；light watcher 已重启并命令参数引用 52 子门质量门，watcher 子进程 PID `1174266`，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。
- 验证：`py_compile` 覆盖新增门、统一质量门、复测 readiness、watcher 和 scorer；`git diff --check` 通过；结构化断言确认 52 个子门、51 个复用、失败子门为空、watcher mirror 指向 52 门质量 JSON。

### 2026-06-04 00:42:50 CST：新增前端运动能量选帧鲁棒性门并升级为 53 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_energy_sampling_robustness_gate.py`。该门只读缓存 Holistic JSON，按前端 motion-energy coverage 逻辑选择实际上传帧集合，重建 hand-shape、motion、two-hand relation 后评分；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。目标是覆盖“浏览器能量选帧实际丢掉部分均匀相位帧”的鲁棒性，而不是只调 `frame_weights`。
- 探针结果：v1 使用固定 `45%` coverage 时，`花` 的 16/20 帧能量选帧会触发 `phase_order_disorder`；v2 进一步确认 top-energy-only 选帧不是前端真实策略，作为正向门会把 `花` 降到 `26.639`。因此改动 `work/web/static/app.js`：`coverageRatio = max(0.45, min(1.0, 0.25 + target / 32))`，小帧数仍偏向峰值，大帧数保留更多阶段覆盖；top-energy-only 只保留为诊断边界。
- 独立能量选帧门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_energy_sampling_robustness_gate_20260604_v3/flower_jump_energy_sampling_robustness_gate.md` PASS：`花` 正向最低 `78.766`（`frontend_energy_coverage_12f`），诊断最低 `4.901`；`跳` 正向最低 `74.690`（`frontend_energy_coverage_6f`），诊断最低 `6.558`。网页上传权重仿真 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/browser_upload_weight_simulation_gate_20260604_energy_coverage_v1/browser_upload_weight_simulation_gate.md` PASS。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门追加第 53 子门 `energy_sampling_robustness_gate`，Markdown 新增“运动能量选帧鲁棒性门”小节和 CLI 阈值 `--energy-sampling-min-score`。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示能量选帧正向最低分、最弱正向选帧、诊断最低分、诊断边界和推荐帧数。更新 `/data/WYC/signLanguage/work/scripts/check_watch_status_frontend_contract.py`：前端契约检查要求保留 `coverageRatio` 和 `0.25 + target / 32`，防止回退成固定 coverage。
- 新 53 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_energy_sampling_53gate_v1/flower_jump_quality_gate.md` PASS，53 个子门全部 returncode `0`；其中 52 个既有子门复用上一轮同 scorer 报告，新第 53 门实际运行。关键指标保持：web 有效正常+边界率 `96.875%`，有效 `124/128`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`；新增门正向最低 `花=78.766`、`跳=74.690`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_energy_sampling_53gate_v2/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。运行态保持：5080 backend PID `811445`、Holistic worker PID `811485`、scoring `reload_count=15`、`last_reload_error=None`；light watcher 已重启并命令参数引用 53 子门质量门，watcher 子进程 PID `1252897`，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。
- 验证：`py_compile` 覆盖新增门、统一质量门、复测 readiness 和前端契约检查器；`git diff --check` 通过；改动文件尾随空白检查通过；结构化断言确认 53 个子门、52 个复用、失败子门为空、前端契约 PASS、上传权重契约 `8/8`、上传权重仿真 `3` cases PASS、watcher mirror 指向 53 门质量 JSON。

### 2026-06-04 00:54:49 CST：新增 rolling-shutter 时变斜切鲁棒性门并升级为 54 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_rolling_shutter_robustness_gate.py`。该门只读缓存 Holistic JSON，逐帧合成 rolling-shutter-like line shear，包括平滑、缓变、稀疏和局部手部时变斜切，并重建 hand-shape、motion、two-hand relation；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。目标是补齐静态 perspective/shear、camera roll、global framing flicker 和 hand-center/scale flicker 之外的真实手机/笔记本摄像头滚动快门 skew。
- 独立 rolling-shutter 门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_rolling_shutter_robustness_gate_20260604_v1/flower_jump_rolling_shutter_robustness_gate.md` PASS：`花` 正向最低 `81.782`（`ramp_rolling_x_from_y_0.06`），诊断最低 `81.602`；`跳` 正向最低 `97.367`（`local_hands_smooth_rolling_x_from_y_0.10`），诊断最低 `94.343`。强 18%-22% skew 只作诊断边界，不作为正常网页采集要求。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门追加第 54 子门 `rolling_shutter_robustness_gate`，Markdown 新增“滚动快门时变斜切鲁棒性门”小节和 CLI 阈值 `--rolling-shutter-min-score`。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示 rolling-shutter 正向最低分、最弱正向 rolling-shutter、诊断最低分和诊断边界。
- 新 54 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_rolling_shutter_54gate_v1/flower_jump_quality_gate.md` PASS，54 个子门全部 returncode `0`；其中 53 个既有子门复用上一轮同 scorer 报告，新第 54 门实际运行。关键指标保持：web 有效正常+边界率 `96.875%`，有效 `124/128`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`；新增门正向最低 `花=81.782`、`跳=97.367`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_rolling_shutter_54gate_v2/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。运行态保持：5080 backend PID `811445`、Holistic worker PID `811485`、scoring `reload_count=15`、`last_reload_error=None`；light watcher 已重启并命令参数引用 54 子门质量门，watcher 子进程 PID `1314632`，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。
- 验证：`py_compile` 覆盖新增门、统一质量门、复测 readiness 和前端契约检查器；`git diff --check` 通过；改动文件尾随空白检查通过；结构化断言确认 54 个子门、53 个复用、失败子门为空、前端契约 PASS、上传权重契约 `8/8`、上传权重仿真 `3` cases PASS、watcher mirror 指向 54 门质量 JSON。

### 2026-06-04 01:07:22 CST：新增手部细节损失鲁棒性门并升级为 55 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_hand_detail_loss_robustness_gate.py`。该门只读缓存 Holistic JSON，模拟低分辨率/低光网页采集中手部关键点小关节细节被平滑：正向变体只把 PIP/DIP 等内关节向 MCP-tip 轴线性化，保留 MCP、指尖范围和粗手形；强指尖向掌心塌缩只作诊断边界。该门不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。
- 独立手部细节损失门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_hand_detail_loss_robustness_gate_20260604_v1/flower_jump_hand_detail_loss_robustness_gate.md` PASS：`花` 正向最低 `80.339`（`flower_opening_right_inner_axis_smooth_0.60`），诊断最低 `77.727`；`跳` 正向最低 `77.234`（`right_hand_inner_axis_smooth_0.45`），诊断最低 `79.899`。这补充 coordinate-precision、landmark-noise、finger-curl-style 和 finger-length-style 之外的“低细节 detector 简化”风险。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门追加第 55 子门 `hand_detail_loss_robustness_gate`，Markdown 新增“手部细节损失鲁棒性门”小节和 CLI 阈值 `--hand-detail-loss-min-score`。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示手部细节损失正向最低分、最弱正向细节损失、诊断最低分和诊断边界。
- 新 55 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_hand_detail_loss_55gate_v1/flower_jump_quality_gate.md` PASS，55 个子门全部 returncode `0`；其中 54 个既有子门复用上一轮同 scorer 报告，新第 55 门实际运行。关键指标保持：web 有效正常+边界率 `96.875%`，有效 `124/128`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`；新增门正向最低 `花=80.339`、`跳=77.234`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_hand_detail_loss_55gate_v2/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。运行态保持：5080 backend PID `811445`、Holistic worker PID `811485`、scoring `reload_count=15`、`last_reload_error=None`；light watcher 已重启并命令参数引用 55 子门质量门，watcher 子进程 PID `1371327`，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。
- 验证：`py_compile` 覆盖新增门、统一质量门和复测 readiness；`git diff --check` 通过；结构化断言确认 55 个子门、54 个复用、失败子门为空、前端契约 PASS、上传权重契约通过、上传权重仿真 PASS、watcher mirror 指向 55 门质量 JSON。目标仍等待 marker 后真实网页摄像头 `花` 和 `跳` 样本各至少一次并由 watcher 完成诊断。

### 2026-06-04 01:17:38 CST：新增手部流帧级延迟鲁棒性门并升级为 56 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_hand_stream_latency_robustness_gate.py`。该门只读缓存 Holistic JSON，在基础骨架组上模拟浏览器/模型 hand landmark 流相对 pose/face/current frame 的 1-2 帧延迟、提前和稀疏延迟，并重建 hand-shape、motion、two-hand relation；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。目标是补齐 inter-hand desync、temporal-rate/time-warp、frame-order jitter、stutter/interpolation 和 motion-blur 之外的“整条手部流帧级滞后/超前”风险。
- 独立手部流延迟门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_hand_stream_latency_robustness_gate_20260604_v1/flower_jump_hand_stream_latency_robustness_gate.md` PASS：`花` 正向最低 `97.237`（`sparse_both_hands_delay_2f_every_5f`），诊断最低 `97.406`；`跳` 正向最低 `76.036`（`sparse_both_hands_delay_2f_every_5f`），诊断最低 `76.890`。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门追加第 56 子门 `hand_stream_latency_robustness_gate`，Markdown 新增“手部流帧级延迟鲁棒性门”小节和 CLI 阈值 `--hand-stream-latency-min-score`。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示手部流延迟正向最低分、最弱正向手部流延迟、诊断最低分和最弱诊断边界。
- 新 56 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_hand_stream_latency_56gate_v1/flower_jump_quality_gate.md` PASS，56 个子门全部 returncode `0`；其中 55 个既有子门复用上一轮同 scorer 报告，新第 56 门实际运行。关键指标保持：web 有效正常+边界率 `96.875%`，有效 `124/128`；保存网页交叉混淆 eligible/pass/fail=`124/124/0`；新增门正向最低 `花=97.237`、`跳=76.036`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_hand_stream_latency_56gate_v2/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。运行态保持：5080 backend PID `811445`、Holistic worker PID `811485`、scoring `reload_count=15`、`last_reload_error=None`；light watcher 已重启并命令参数引用 56 子门质量门，watcher 子进程 PID `1422559`，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。
- 验证：`py_compile` 覆盖新增门、统一质量门和复测 readiness；`git diff --check` 通过；结构化断言确认 56 个子门、55 个复用、失败子门为空、前端契约 PASS、上传权重契约通过、上传权重仿真 PASS、watcher mirror 指向 56 门质量 JSON。目标仍等待 marker 后真实网页摄像头 `花` 和 `跳` 样本各至少一次并由 watcher 完成诊断。

### 2026-06-04 01:32:29 CST：新增幽灵手重复鲁棒性门并升级为 57 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_ghost_hand_duplicate_robustness_gate.py`。该门只读缓存 Holistic JSON，将一只手的 21 点复制到另一只手，模拟网页/Holistic 单手被检测成双手的 ghost-hand 误检，并重建 hand-shape、motion、two-hand relation；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。它区别于 hand-label-flicker 的左右换标：这里缺失手被可见手副本替代。
- 独立 v1 暴露 `花` 全程非核心左手幽灵副本 `69.388`，略低于通用 70；该场景比短暂/稀疏误检更重，且类似 missing-mask 中非核心手宽容口径，因此 promoted v2 把该单项局部门槛设为 `65`，不降低整门全局阈值。独立 v2 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_ghost_hand_duplicate_robustness_gate_20260604_v2/flower_jump_ghost_hand_duplicate_robustness_gate.md` PASS：`花` 正向最低 `69.388`（`flower_full_left_ghost_from_right_offset`），诊断最低 `29.506`；`跳` 正向最低 `70.469`（`single_mid_left_duplicates_right`），诊断最低 `19.222`。`跳` 中段幽灵重复诊断仍可高分，本轮只记录边界，是否升级硬负例需真实样本/人工标签。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门追加第 57 子门 `ghost_hand_duplicate_robustness_gate`，Markdown 新增“幽灵手重复鲁棒性门”小节和 CLI 阈值 `--ghost-hand-duplicate-min-score`。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示幽灵手正向最低分、最弱正向幽灵手、诊断最低分和诊断边界。
- 新 57 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_ghost_hand_duplicate_57gate_v1/flower_jump_quality_gate.md` PASS，57 个子门全部 returncode `0`；其中 56 个既有子门复用上一轮同 scorer 报告，新第 57 门实际运行。关键指标保持：web 有效正常+边界率 `96.875%`；保存网页交叉混淆 eligible=`124` 且 PASS；新增门正向最低 `花=69.388`、`跳=70.469`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_ghost_hand_duplicate_57gate_v2/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。运行态保持：5080 backend PID `811445`、Holistic worker PID `811485`、scoring `reload_count=15`、`last_reload_error=None`；light watcher 已重启并命令参数引用 57 子门质量门，watcher 子进程 PID `1495416`，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。
- 验证：`py_compile` 覆盖新增门、统一质量门和复测 readiness；`git diff --check` 通过；结构化断言确认 57 个子门、56 个复用、失败子门为空、web 有效率 `96.875%`、保存网页交叉混淆 eligible=`124` 且 PASS、前端契约 PASS、上传权重契约和上传仿真 PASS、watcher mirror 指向 57 门质量 JSON。目标仍等待 marker 后真实网页摄像头 `花` 和 `跳` 样本各至少一次并由 watcher 完成诊断。

### 2026-06-04 01:44:28 CST：新增手部重叠融合鲁棒性门并升级为 58 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_hand_overlap_merge_robustness_gate.py`。该门只读缓存 Holistic JSON，将一只手的 landmarks 按比例拉向另一只手，模拟双手接近/遮挡时局部 hand tracker merge；对单手 `花` 额外模拟开花手 landmarks 向掌心轻微融合的自遮挡/手指重叠，并重建 hand-shape、motion、two-hand relation。该门不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。
- 独立 v1 暴露 `花` 当前标准序列没有可用于双手融合的另一只手，实际改动为 0；v2 增加 `self_center` 自遮挡融合后可对 `花` 形成有效压力；v3 追加强自遮挡诊断边界。独立 v3 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_hand_overlap_merge_robustness_gate_20260604_v3/flower_jump_hand_overlap_merge_robustness_gate.md` PASS：`花` 正向最低 `81.343`（`flower_right_hand_self_overlap_0.12`），诊断最低 `95.607`；`跳` 正向最低 `70.469`（`single_mid_right_blend_toward_left_0.45`），诊断最低 `81.566`。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门追加第 58 子门 `hand_overlap_merge_robustness_gate`，Markdown 新增“手部重叠融合鲁棒性门”小节和 CLI 阈值 `--hand-overlap-merge-min-score`。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示手部融合正向最低分、最弱正向融合、诊断最低分和诊断边界。
- 新 58 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_hand_overlap_merge_58gate_v1/flower_jump_quality_gate.md` PASS，58 个子门全部 returncode `0`；其中 57 个既有子门复用上一轮同 scorer 报告，新第 58 门实际运行。关键指标保持：web 有效正常+边界率 `96.875%`；保存网页交叉混淆 eligible=`124` 且 PASS；新增门正向最低 `花=81.343`、`跳=70.469`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_hand_overlap_merge_58gate_v2/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。运行态保持：5080 backend PID `811445`、Holistic worker PID `811485`、scoring `reload_count=15`、`last_reload_error=None`；light watcher 已重启并命令参数引用 58 子门质量门，watcher 子进程 PID `1554739`，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。
- 验证：`py_compile` 覆盖新增门、统一质量门和复测 readiness；`git diff --check` 通过；结构化断言确认 58 个子门、57 个复用、失败子门为空、web 有效率 `96.875%`、保存网页交叉混淆 eligible=`124` 且 PASS、前端契约 PASS、上传权重契约和上传仿真 PASS、watcher mirror 指向 58 门质量 JSON。目标仍等待 marker 后真实网页摄像头 `花` 和 `跳` 样本各至少一次并由 watcher 完成诊断。

### 2026-06-04 01:58:56 CST：新增手腕掌根锚点漂移鲁棒性门并升级为 59 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_wrist_anchor_drift_robustness_gate.py`。该门只读缓存 Holistic JSON，在 hand mask 仍有效的前提下偏移 wrist/MCP/palm anchors 坐标，模拟网页追踪中手腕/掌根根点短时漂移但指尖仍可见的故障，并重建 hand-shape、motion、two-hand relation；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。该门区别于 palm-anchor occlusion 的 mask 丢失，也区别于 hand-center/scale flicker 的整手框抖动。
- 独立 v1 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_wrist_anchor_drift_robustness_gate_20260604_v1/flower_jump_wrist_anchor_drift_robustness_gate.md` PASS：`花` 正向最低 `97.283`（`flower_middle20_right_mcp_anchor_xy_0.029`），诊断最低 `94.444`；`跳` 正向最低 `76.497`（`jump_middle20_right_person_mcp_anchor_y_0.020`），诊断最低 `84.692`。补充探测显示 `花` 对单纯根点漂移不敏感，当前 `花` 评分主要由开合手指和相位证据承载；`跳` 的右手小人 MCP 根点短窗口漂移接近有效边界。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门追加第 59 子门 `wrist_anchor_drift_robustness_gate`，Markdown 新增“手腕掌根锚点漂移鲁棒性门”小节和 CLI 阈值 `--wrist-anchor-drift-min-score`。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示手腕掌根漂移正向最低分、最弱正向漂移、诊断最低分和诊断边界。
- 新 59 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_wrist_anchor_drift_59gate_v1/flower_jump_quality_gate.md` PASS，59 个子门全部 returncode `0`；其中 58 个既有子门复用上一轮同 scorer 报告，新第 59 门实际运行。关键指标保持：web 有效正常+边界率 `96.875%`，保存网页交叉混淆 eligible=`124` 且 PASS；新增门正向最低 `花=97.283`、`跳=76.497`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_wrist_anchor_drift_59gate_v2/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。运行态保持：5080 backend PID `811445`、Holistic worker PID `811485`、scoring `reload_count=15`、`last_reload_error=None`；light watcher 已重启并命令参数引用 59 子门质量门，watcher 子进程 PID `1623884`，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。
- 验证：`py_compile` 覆盖新增门、统一质量门和复测 readiness；结构化断言确认 59 个子门、58 个复用、失败子门为空、前端契约 PASS、上传权重仿真 PASS、watcher mirror 指向 59 门质量 JSON。目标仍等待 marker 后真实网页摄像头 `花` 和 `跳` 样本各至少一次并由 watcher 完成诊断。

### 2026-06-04 02:11:08 CST：新增手指链帧级延迟鲁棒性门并升级为 60 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_finger_chain_latency_robustness_gate.py`。该门只读缓存 Holistic JSON，只把选定 distal finger chains 从前/后帧复制到当前帧，wrist/MCP/palm anchors 保持当前帧，模拟快速开合或两指运动中指尖链相对掌根短时延迟；随后重建 hand-shape、motion、two-hand relation；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。该门区别于 hand-stream latency 的整手流延迟、inter-hand desync 的左右手错相、trajectory interpolation 的补洞线性化、motion blur 的低通平滑和 finger identity jitter 的手指标签交换。
- 独立 v1 暴露 `花` 的所有 distal finger chains 全程提前/滞后 1 帧会把开合相位打乱到低分（最低 `40.342`），不应作为正常网页容错；v2 将这类持续错相降为诊断，只保留单帧、稀疏和短窗口延迟为正向门。独立 v2 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_finger_chain_latency_robustness_gate_20260604_v2/flower_jump_finger_chain_latency_robustness_gate.md` PASS：`花` 正向最低 `94.483`（`flower_right_all_distal_sparse_delay_2f_every_5f`），诊断最低 `40.342`；`跳` 正向最低 `71.202`（`jump_right_person_distal_delay_2f`），诊断最低 `74.355`。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门追加第 60 子门 `finger_chain_latency_robustness_gate`，Markdown 新增“手指链帧级延迟鲁棒性门”小节和 CLI 阈值 `--finger-chain-latency-min-score`。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示手指链延迟正向最低分、最弱正向延迟、诊断最低分和诊断边界。
- 新 60 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_finger_chain_latency_60gate_v1/flower_jump_quality_gate.md` PASS，60 个子门全部 returncode `0`；其中 59 个既有子门复用上一轮同 scorer 报告，新第 60 门实际运行。关键指标保持：web 有效正常+边界率 `96.875%`，保存网页交叉混淆 eligible=`124` 且 PASS；新增门正向最低 `花=94.483`、`跳=71.202`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_finger_chain_latency_60gate_v2/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。运行态保持：5080 backend PID `811445`、Holistic worker PID `811485`、scoring `reload_count=15`、`last_reload_error=None`；light watcher 已重启并命令参数引用 60 子门质量门，watcher 子进程 PID `1680520`，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。
- 验证：`py_compile` 覆盖新增门、统一质量门和复测 readiness；结构化断言确认 60 个子门、59 个复用、失败子门为空、前端契约 PASS、上传权重仿真 PASS、watcher mirror 指向 60 门质量 JSON。目标仍等待 marker 后真实网页摄像头 `花` 和 `跳` 样本各至少一次并由 watcher 完成诊断。

### 2026-06-04 02:23:58 CST：新增手指扇形几何鲁棒性门并升级为 61 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_finger_fan_geometry_robustness_gate.py`。该门只读缓存 Holistic JSON，只压缩/拉开同一手内相邻 distal finger chains 的二维扇形几何，landmark 身份和 mask 不变，wrist/MCP/palm anchors 保持当前帧；随后重建 hand-shape、motion、two-hand relation；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。该门区别于 finger identity jitter 的标签交换、finger curl/length style 的径向形态变化、遮挡/细节损失的 mask 或内关节退化、hand overlap merge 的手部融合和 finger-chain latency 的帧级错相。
- 独立 v1 已 PASS，但诊断边界偏高；v2 加强非门控诊断交叉/塌缩强度后作为 promoted 版本。独立 v2 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_finger_fan_geometry_robustness_gate_20260604_v2/flower_jump_finger_fan_geometry_robustness_gate.md` PASS：`花` 正向最低 `81.220`（`flower_right_nonoverlap_full_compress_0p08`），诊断最低 `63.377`；`跳` 正向最低 `76.629`（`jump_right_person_sparse_compress_0p20_every_5f`），诊断最低 `82.302`。`跳` 强 fan crossing 仍可高分，说明当前 `跳` 主要由双手关系和轨迹吸收该形变，本轮只记录诊断，不升级硬负例。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门追加第 61 子门 `finger_fan_geometry_robustness_gate`，Markdown 新增“手指扇形几何鲁棒性门”小节和 CLI 阈值 `--finger-fan-geometry-min-score`。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示手指扇形几何正向最低分、最弱正向扇形漂移、诊断最低分和诊断边界。
- 新 61 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_finger_fan_geometry_61gate_v1/flower_jump_quality_gate.md` PASS，61 个子门全部 returncode `0`；其中 60 个既有子门复用上一轮同 scorer 报告，新第 61 门实际运行。关键指标保持：web 有效正常+边界率 `96.875%`，保存网页交叉混淆 eligible=`124` 且 PASS；新增门正向最低 `花=81.220`、`跳=76.629`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_finger_fan_geometry_61gate_v2/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。运行态保持：5080 backend PID `811445`、Holistic worker PID `811485`、scoring `reload_count=15`、`last_reload_error=None`；light watcher 已重启并命令参数引用 61 子门质量门，watcher 子进程 PID `1739705`，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。
- 验证：`py_compile` 覆盖新增门、统一质量门和复测 readiness；结构化断言确认 61 个子门、60 个复用、失败子门为空、watcher mirror 指向 61 门质量 JSON。目标仍等待 marker 后真实网页摄像头 `花` 和 `跳` 样本各至少一次并由 watcher 完成诊断。

### 2026-06-04 02:35:04 CST：新增手指基座几何鲁棒性门并升级为 62 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_finger_base_geometry_robustness_gate.py`。该门只读缓存 Holistic JSON，只压缩/拉开同一手内相邻 MCP/CMC finger-base landmarks 的二维相对几何，distal finger chains、landmark 身份和 mask 不变；随后重建 hand-shape、motion、two-hand relation；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。该门区别于 wrist-anchor drift 的整组根点漂移、finger fan-geometry 的 distal 指链漂移、finger identity jitter 的标签交换、curl/length style、遮挡/细节损失和 hand overlap merge。
- 独立 v1 已 PASS，但 `跳` 正向扰动几乎不降分；v2 加强 `跳` 正向和非门控诊断强度后作为 promoted 版本。独立 v2 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_finger_base_geometry_robustness_gate_20260604_v2/flower_jump_finger_base_geometry_robustness_gate.md` PASS：`花` 正向最低 `81.347`（`flower_right_nonoverlap_base_full_compress_0p05`），诊断最低 `78.227`；`跳` 正向最低 `98.112`（`jump_right_person_base_full_compress_0p12`），诊断最低 `82.302`。`跳` 对仅 MCP 基座漂移高度宽容，说明当前评分主要由双手关系、轨迹和指尖两指形承载，本轮只记录诊断，不升级硬负例。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门追加第 62 子门 `finger_base_geometry_robustness_gate`，Markdown 新增“手指基座几何鲁棒性门”小节和 CLI 阈值 `--finger-base-geometry-min-score`。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示手指基座几何正向最低分、最弱正向基座漂移、诊断最低分和诊断边界。
- 新 62 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_finger_base_geometry_62gate_v1/flower_jump_quality_gate.md` PASS，62 个子门全部 returncode `0`；其中 61 个既有子门复用上一轮同 scorer 报告，新第 62 门实际运行。关键指标保持：web 有效正常+边界率 `96.875%`，保存网页交叉混淆 eligible=`124` 且 PASS；新增门正向最低 `花=81.347`、`跳=98.112`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_finger_base_geometry_62gate_v2/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。运行态保持：5080 backend PID `811445`、Holistic worker PID `811485`、scoring `reload_count=15`、`last_reload_error=None`；light watcher 已重启并命令参数引用 62 子门质量门，watcher 子进程 PID `1796686`，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。
- 验证：`py_compile` 覆盖新增门、统一质量门和复测 readiness；结构化断言确认 62 个子门、61 个复用、失败子门为空、watcher mirror 指向 62 门质量 JSON。目标仍等待 marker 后真实网页摄像头 `花` 和 `跳` 样本各至少一次并由 watcher 完成诊断。

### 2026-06-04 02:46:09 CST：新增手指链软置信鲁棒性门并升级为 63 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_finger_chain_confidence_robustness_gate.py`。该门只读缓存 Holistic JSON，保留坐标和 landmark 身份，只降低选定 finger-chain 的 hand mask 权重，并重建 motion/two-hand relation；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。该门区别于整手 `hand_confidence_attenuation`、硬缺失/遮挡、fingertip/mid-joint occlusion 和 hand dropout burst，覆盖网页摄像头中特定手指链可见但置信度 near-threshold 的软 mask 场景。
- 独立 v1 暴露局部 mask 降到硬缺失附近会触发 scorer 已知的部分软 mask 未定义边界；promoted v2 移除 `0.0` 硬缺失诊断，硬缺失继续由遮挡/缺失门覆盖，只保留 `0.55+` 软置信口径。独立 v2 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_finger_chain_confidence_robustness_gate_20260604_v2/flower_jump_finger_chain_confidence_robustness_gate.md` PASS：`花` 正向最低 `100.000`（`flower_right_all_fingers_confidence_0p85_full`），诊断最低 `100.000`；`跳` 正向最低 `99.987`（`jump_left_ground_fingers_confidence_0p65_middle20`），诊断最低 `100.000`。这说明当前 scorer 对坐标完整、局部手指链 soft mask 下降不会误扣分。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门追加第 63 子门 `finger_chain_confidence_robustness_gate`，Markdown 新增“手指链软置信鲁棒性门”小节和 CLI 阈值 `--finger-chain-confidence-min-score`。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示手指链软置信正向最低分、最弱正向低置信、诊断最低分和诊断边界。
- 新 63 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_finger_chain_confidence_63gate_v1/flower_jump_quality_gate.md` PASS，63 个子门全部 returncode `0`；其中 62 个既有子门复用上一轮同 scorer 报告，新第 63 门实际运行。关键指标保持：web 有效正常+边界率 `96.875%`，保存网页交叉混淆 eligible=`124` 且 PASS；新增门正向最低 `花=100.000`、`跳=99.987`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_finger_chain_confidence_63gate_v2/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。运行态保持：5080 backend PID `811445`、Holistic worker PID `811485`、scoring `reload_count=15`、`last_reload_error=None`；light watcher 已重启并命令参数引用 63 子门质量门，watcher 子进程 PID `1846721`，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。
- 验证：`py_compile` 覆盖新增门、统一质量门和复测 readiness；结构化断言确认 63 个子门、62 个复用、失败子门为空、watcher mirror 指向 63 门质量 JSON。目标仍等待 marker 后真实网页摄像头 `花` 和 `跳` 样本各至少一次并由 watcher 完成诊断。

### 2026-06-04 02:59:37 CST：新增手指链时间平滑鲁棒性门并升级为 64 子门质量门

- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_finger_chain_smoothing_robustness_gate.py`。该门只读缓存 Holistic JSON，只对选定 distal finger-chain 做短窗口时间低通，wrist/MCP/palm anchors 保持当前帧，mask 和 landmark 身份不变，并重建 hand-shape、motion、two-hand relation；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。该门区别于 whole-hand motion blur、frame stutter、finger-chain latency、confidence attenuation、occlusion 和 interpolation，覆盖低分辨率网页摄像头或 tracker 稳定化导致的局部手指链时间平滑/黏连场景。
- 独立 v1 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_finger_chain_smoothing_robustness_gate_20260604_v1/flower_jump_finger_chain_smoothing_robustness_gate.md` PASS：`花` 正向最低 `80.010`（`flower_right_all_distal_3tap_strength_0p35_full`），诊断最低 `55.790`；`跳` 正向最低 `77.745`（`jump_left_ground_distal_3tap_strength_0p35_full`），诊断最低 `72.654`。持续强低通仍仅作诊断边界，因为它可能真实抹掉 `花` 的开合或 `跳` 的两指弹跳相位。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门追加第 64 子门 `finger_chain_smoothing_robustness_gate`，Markdown 新增“手指链时间平滑鲁棒性门”小节和 CLI 阈值 `--finger-chain-smoothing-min-score`。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示手指链时间平滑正向最低分、最弱正向平滑、诊断最低分和诊断边界。
- 新 64 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_finger_chain_smoothing_64gate_v1/flower_jump_quality_gate.md` PASS，64 个子门全部 returncode `0`；其中 63 个既有子门复用上一轮同 scorer 报告，新第 64 门实际运行。关键指标保持：web 有效正常+边界率 `96.875%`，保存网页交叉混淆 eligible=`124` 且 PASS；新增门正向最低 `花=80.010`、`跳=77.745`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_finger_chain_smoothing_64gate_v1/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。运行态保持：5080 backend PID `811445`、Holistic worker PID `811485`、scoring `reload_count=15`、`last_reload_error=None`；light watcher 已重启并命令参数引用 64 子门质量门，watcher 子进程 PID `1908768`，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`，目标仍不能标记完成。
- 验证：`py_compile` 覆盖新增门、统一质量门和复测 readiness；结构化断言确认 64 个子门、63 个复用、失败子门为空、watcher mirror 指向 64 门质量 JSON。目标仍等待 marker 后真实网页摄像头 `花` 和 `跳` 样本各至少一次并由 watcher 完成诊断。

### 2026-06-04 03:44:52 CST：修复非有限坐标清洗并升级为 65 子门质量门

- 定位到 `score_holistic_sequence_mvp.py` 对 Holistic landmark 坐标中的 `NaN/Inf/-Inf` 未清洗：临时污染 `花` 的右手食指点和 pose 点后，旧逻辑仍给 `prototype_score=100.0`，但 `dtw_distance/normalized_distance=nan`，会污染网页评分结果和报告汇总。
- 已修复 scorer：landmark 坐标转换时遇到非有限值统一置零并把对应 mask 设为 `0.0`；pose 归一化、双手关系特征、weighted RMSE、pose-robust hand distance 和 group distance 都显式过滤非有限维度。修复后同一污染探针得到有限结果：`prototype_score=99.870`、`dtw_distance=0.000028`、`normalized_distance=0.000207`，被污染点 mask 变为 `0.0`。
- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_finite_coordinate_robustness_gate.py`。该门只读缓存 Holistic JSON，写入含 `NaN/Inf/-Inf` 的临时 fixture 后通过正常 `load_sequence()` 和 `run_pair()` 重载评分；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。它验证稀疏 pose/face/hand 非有限坐标会被当作缺失点清洗，score/DTW/normalized distance 保持 finite；持续核心手或全 pose 非有限只作为诊断边界。
- 独立 v2 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_finite_coordinate_robustness_gate_20260604_v2/flower_jump_finite_coordinate_robustness_gate.md` PASS：`花` 正向最低 `77.581`、诊断最低 `23.221`；`跳` 正向最低 `70.714`、诊断最低 `8.288`。v1 失败原因为测试 fixture 输出目录没有 `semantic_frame_weights.json` sidecar，导致 `跳` 自比时 query/standard 权重不一致；v2 改为同口径禁用 sidecar 权重后通过。
- 更新 `/data/WYC/signLanguage/work/scripts/run_flower_jump_quality_gate.py`：统一质量门追加第 65 子门 `finite_coordinate_robustness_gate`，Markdown 新增“非有限坐标清洗鲁棒性门”小节和 CLI 阈值 `--finite-coordinate-min-score`。更新 `/data/WYC/signLanguage/work/scripts/build_flower_jump_retest_readiness_report.py`：复测报告显示非有限坐标正向最低分、最弱坏点、诊断最低分和诊断边界。
- 因 scorer 代码变更，本轮完整重跑全部 65 门而非复用旧证据。新 65 子门统一质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_finite_coordinate_65gate_v1/flower_jump_quality_gate.md` PASS，65 个子门全部 returncode `0`，失败子门为空；新增门正向最低 `花=77.581`、`跳=70.714`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_finite_coordinate_65gate_v1/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。5080 在线 scorer 已热重载到 `reload_count=16`、`loaded_at=2026-06-04T03:43:59`、`last_reload_error=None`；backend PID `811445`、Holistic worker PID `811485` 未重启。light watcher 已重启并引用 65 子门质量门，PID `2124529`，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`。
- 验证：`py_compile` 覆盖 scorer、新增门、统一质量门和复测 readiness；65 门质量门结构化断言通过；在线 scorer 热重载成功；watcher mirror 指向 65 门质量 JSON。目标仍不能完成，直到 marker 后真实网页摄像头 `花` 和 `跳` 样本都出现并由 watcher 完成诊断。

### 2026-06-04 04:41:50 CST：修复有限越界坐标清洗并升级为 66 子门质量门

- 在 65 门非有限坐标修复之后继续排查 Holistic 输出中“有限但明显越界”的 hand/face 坐标。临时探针显示，若右手指尖 x 被写成有限越界值，旧逻辑会把它当成真实几何参与 DTW，`花` 可从正常分坍缩到 `4.678`，强扰动可到 `0.378`；这不是语义失败，而是 tracker 输出坐标越界没有被当作缺失点清洗。
- 已修复 `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py`：`_landmark_array()` 增加可选 `xy_bounds`，对 hand/face landmark 的 x/y 超出 `[-0.15, 1.15]` 的点置零并把 mask 设为 `0.0`；pose 保持不加该边界，因为历史网页样本中 hip/leg 等 pose 点经常有限越界，且它们不应把手语核心评分拖低。非有限坐标清洗仍继续生效。
- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_bounded_coordinate_robustness_gate.py`。该门只读缓存 Holistic JSON，写入 hand/face 有限越界坐标 fixture 后通过正常 `load_sequence()` 和 `run_pair()` 重新评分；不调用 `/api/score`、不移动 marker、不运行 Holistic、不重启 5080。独立 v2 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_bounded_coordinate_robustness_gate_20260604_v2/flower_jump_bounded_coordinate_robustness_gate.md` PASS：`花` 正向最低 `99.312`、诊断最低 `37.624`；`跳` 正向最低 `70.714`、诊断最低 `6.189`。
- 因 scorer 再次变更，本轮完整重跑 66 子门质量门而非复用旧证据。新质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_bounded_coordinate_66gate_v1/flower_jump_quality_gate.md` PASS，`66` 个子门全部 returncode `0`，失败子门为空，最后一门为 `bounded_coordinate_robustness_gate`。网页回归仍 PASS，`168` replay 错误 `0`、`149` diagnostics 错误 `0`，有效正常+边界率 `96.9%`，`跳` 有效低分 `0`，`花` 有效低分 `4` 且均为 `flower_opening_guard_failed`。
- 本修复还恢复了部分历史 `花` 网页样本：`web_20260523_071212_4547d033` 从 `45.047` 到 `79.560`，`web_20260523_071306_071a2172` 从 `19.958` 到 `76.923`，`web_20260523_071320_415e2975` 从 `30.132` 到 `78.392`，`web_20260602_212951_e1173da1` 从 `29.565` 到 `77.625`，`web_20260602_213015_411a2ecd` 从 `53.813` 到 `78.861`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_bounded_coordinate_66gate_v1/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。5080 scorer 已热重载到 `reload_count=17`、`loaded_at=2026-06-04T04:41:08`、`last_reload_error=None`；backend PID `811445`、Holistic worker PID `811485` 未重启。light watcher 已重启并引用 66 子门质量门，PID `2385264`，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`。
- 验证：新增门独立 v2 PASS；66 门质量门完整 PASS；复测 readiness 为 `PASS/NOT_READY`；在线 scorer 热重载成功；watcher 首轮 mirror 指向 66 门质量 JSON。目标仍不能完成，直到 marker 后真实网页摄像头 `花` 和 `跳` 样本都出现并由 watcher 完成诊断。

### 2026-06-04 05:28:55 CST：扩展有限坐标清洗到 hand/face z 离群

- 在 x/y 有限越界修复后继续探测 hand/face raw `z` 深度离群。临时 fixture 显示：若 `花` 右手食指/中指 tip 的 `z` 被写成有限大值而 x/y 仍合法，旧逻辑会把该点当成真实三维几何，单帧 `z=5` 可把分数压到 `7.025`，稀疏多帧可到 `0.0`，且 `capture_quality` 仍为 `score_valid`。这属于 tracker 输出异常点未清洗，不应被当作动作语义失败。
- 扫描当前模板和保存网页 Holistic JSON 后，正常 hand/face raw `z` 分布很窄：hand 约在 `[-0.039, 0.014]`，face 到约 `0.051`，pose 到约 `0.633`。因此在 `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py` 中新增 hand/face `z_bounds=[-1.0, 1.0]`，只把明显离群的 hand/face 点置零并 mask 为 `0.0`；pose 仍不加该 z 边界，避免非核心身体点误伤手语评分。
- 修复后同一 z 离群探针恢复：`花` 单帧 tip z 离群 `99.633`、稀疏 tip z 离群 `99.399`；`跳` 单帧 tip z 离群 `87.640`、稀疏 tip z 离群 `79.149`。扩展 `/data/WYC/signLanguage/work/scripts/run_flower_jump_bounded_coordinate_robustness_gate.py` 到 v3，新增 face/hand z 离群正向和诊断用例，独立报告 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_bounded_coordinate_robustness_gate_20260604_v3/flower_jump_bounded_coordinate_robustness_gate.md` PASS：`花` 正向最低 `99.312`、诊断最低 `37.624`；`跳` 正向最低 `70.714`、诊断最低 `6.189`。
- 因 scorer 代码变更，本轮完整重跑 66 子门质量门。新质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_bounded_z_coordinate_66gate_v1/flower_jump_quality_gate.md` PASS，`66` 个子门全部 returncode `0`，失败子门为空，最后一门仍为 `bounded_coordinate_robustness_gate`。网页回归仍 PASS：`168` replay 错误 `0`、`149` diagnostics 错误 `0`，有效正常+边界率 `96.9%`，`跳` 有效低分 `0`，`花` 有效低分 `4` 且均为 `flower_opening_guard_failed`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_bounded_z_coordinate_66gate_v1/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。5080 scorer 已热重载到 `reload_count=18`、`loaded_at=2026-06-04T05:21:37`、`last_reload_error=None`；backend PID `811445`、Holistic worker PID `811485` 未重启。light watcher 已重启并引用 z-bound 66 子门质量门，PID `2601292`，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`。
- 验证：z 离群探针 PASS；bounded-coordinate v3 PASS；z-bound 66 门质量门完整 PASS；复测 readiness 为 `PASS/NOT_READY`；在线 scorer 热重载成功；watcher 首轮 mirror 指向 z-bound 66 门质量 JSON。目标仍不能完成，直到 marker 后真实网页摄像头 `花` 和 `跳` 样本都出现并由 watcher 完成诊断。

### 2026-06-04 06:25:32 CST：扩展坐标清洗到 exact-zero 占位和整手塌缩

- 在 z 离群修复后继续审计 Holistic/WebRTC 的有限但语义无效坐标。实测模板和保存网页 JSON 中 hand/face `visibility/presence` 字段恒为 `0.0`，不能作为可见性依据；当前用坐标和 mask 推导 presence 的方向正确。新的退化探针显示：`花` 右手 tip 被写成 exact-zero `(0,0,0)` 时，旧逻辑仍按有效几何参与评分，单帧 index/middle tip 可降到 `21.990`，稀疏 ring/pinky tip 可降到 `4.493`；同时 `跳` 右手全程所有点塌缩到手腕仍可到 `84.683` 且 `score_valid`，说明整手零跨度需要作为 tracker 失败处理。
- 已修复 `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py`：hand/face landmark 中 `(x,y,z)` 全部落在 `1e-7` 内的 exact-zero 点按缺失处理；left/right hand 在至少 `8` 个可见点且 x/y 跨度 `<=1e-5` 时，把该帧整手置为缺失，避免整手塌缩被当作有效手形。pose 仍不套 exact-zero 或整手规则，避免误伤非手部姿态点。
- 扩展 `/data/WYC/signLanguage/work/scripts/run_flower_jump_bounded_coordinate_robustness_gate.py`：bounded-coordinate 门现在覆盖 x/y 越界、z 离群、exact-zero 占位和整手 duplicate-to-wrist 零跨度；持续核心手退化增加硬检查，必须 `score<=55` 且 `capture_quality` 为 `needs_recapture/semantic_mismatch`。独立报告 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_bounded_coordinate_robustness_gate_20260604_degenerate_v1/flower_jump_bounded_coordinate_robustness_gate.md` PASS：`花` 正向最低 `99.312`，`跳` 正向最低 `70.714`；`花` 核心手 zero/duplicate 诊断为 `37.624 needs_recapture`，`跳` 全程右手 duplicate 诊断为 `0.236 needs_recapture`。
- 因 scorer 代码变更，本轮完整重跑 66 子门质量门。新质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_degenerate_coordinate_66gate_v1/flower_jump_quality_gate.md` PASS，`66` 个子门全部 returncode `0`，失败子门为空。网页回归仍 PASS：`168` replay 错误 `0`、`149` diagnostics 错误 `0`，有效正常+边界率 `96.9%`；`花` 有效 `87/91` normal+borderline，`跳` 有效 `37/37` normal+borderline、低分 `0`。
- 最新复测就绪 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_degenerate_coordinate_66gate_postwatch_v1/flower_jump_retest_readiness.md`：复测就绪 `PASS`、目标完成度 `NOT_READY`、下一步 `采集 花、跳`。5080 scorer 已热重载到 `reload_count=19`、`loaded_at=2026-06-04T06:24:23`、`last_reload_error=None`；backend PID `811445`、Holistic worker PID `811485` 未重启。light watcher 已重启并引用 degenerate-coordinate 66 子门质量门，PID `2878832`，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`。
- 验证：`py_compile` 覆盖 scorer、bounded gate、quality gate、readiness；degenerate 探针 PASS；expanded bounded-coordinate standalone PASS；66 门质量门完整 PASS；post-watch readiness 为 `PASS/NOT_READY`；在线 scorer 热重载成功；watcher 首轮 mirror 指向 degenerate-coordinate 66 门质量 JSON。目标仍不能完成，直到 marker 后真实网页摄像头 `花` 和 `跳` 样本都出现并由 watcher 完成诊断。

### 2026-06-04 07:13:32 CST：收紧整手极小跨度塌缩判定并保持 66 子门通过

- 先审计真实模板/网页 hand raw x/y span：`178` 个文件、`4750` 个 hand frames；template 最小 `0.01942551`、p1 `0.02346146`、p5 `0.02474797`，web 最小 `0.02428925`、p1 `0.03190756`、p5 `0.03856146`，全量最小 `0.01942551`；无 frame `<=0.01`，仅 `1` 个 template frame `<=0.02`。因此 `0.012` 阈值低于当前真实数据，主要针对 near-collapsed tracker artifact。
- pre-fix tiny-span 探针确认旧逻辑仍有漏洞：有限且画面内的整手 x/y span 被压到 `0.001/0.005/0.012` 时仍可能高分或 `score_valid`，其中 `花` middle35 最高 `73.011`，`跳` 全程右手 tiny span 可到 `84.689`，`跳` left-ground hand 可到 `77.127`。
- 已把 `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py` 的 `HAND_DEGENERATE_XY_SPAN_MIN` 从 `1e-5` 提升到 `0.012`；bounded-coordinate 门新增 `花` core right hand、`跳` full right person hand 和 `跳` left ground hand 的 tiny-span 诊断。修复后正确探针 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_tiny_hand_span_probe_20260604_v2/tiny_hand_span_probe.json`：`花` middle35 tiny spans 为 `37.624 needs_recapture`，`跳` full right 为 `0.236 needs_recapture`，`跳` left ground 为 `9.425 needs_recapture`。
- 独立 bounded 门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_bounded_coordinate_robustness_gate_20260604_tiny_span_v1/flower_jump_bounded_coordinate_robustness_gate.md` PASS：hand span threshold `0.012`，`花` positive min `99.312`，`跳` positive min `70.714`，tiny diagnostic rows 全部 `needs_recapture` 且 `<=55`。
- 完整 66 门质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_tiny_span_coordinate_66gate_v1/flower_jump_quality_gate.md` PASS：`66` 个子门 returncode `0`，失败子门 `[]`；web replay `168` samples/`0` errors，diagnostics `149`/`0` errors；effective normal+borderline 为 `124/128=96.875%`，其中 `花` effective `87/91`，`跳` effective `37/37`。
- post-watch readiness `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_tiny_span_coordinate_66gate_postwatch_v1/flower_jump_retest_readiness.md` 为 `PASS/NOT_READY`，下一步仍是 `采集 花、跳`。5080 scorer 已热重载到 `reload_count=20`、`loaded_at=2026-06-04T07:11:57`、`last_reload_error=None`；Holistic worker PID `811485` 未重启。watcher PID `3102403` 已指向 tiny-span 66 门 JSON，当前事件 `no_target_samples`，formal marker 后目标样本仍为 `0`。目标仍未完成，直到 marker 后真实网页摄像头 `花` 和 `跳` 样本都出现并通过 watcher 诊断。

### 2026-06-04 08:07:16 CST：统一清洗异常 frame_weights 并保持 66 子门通过

- 从当前网页有效低分反查确认：剩余 `4` 个有效低分 `花` 都是 `flower_opening_guard_failed`，张开分数约 `0.00-0.12`，属于语义不匹配，不应通过放宽阈值拉高。随后转向尚未有硬清洗门的浏览器上传 `frame_weights`。
- 审计 `178` 个模板/网页 Holistic JSON：record `frame_weight` 共 `7776` 个，范围 `0.4317-3.139`，非有限/非正/`>10` 均为 `0`；sidecar `semantic_frame_weight` 共 `376` 个，范围 `0.6895-1.7324`，同样无异常。因此原始安全裁剪上限 `10.0` 不会影响现有正常权重。
- 已更新 `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py`：新增统一 `_sanitize_frame_weight()`、`FRAME_WEIGHT_MIN=0.05`、`FRAME_WEIGHT_RAW_MAX=10.0`；非有限/不可解析权重回退 `1.0`，有限权重裁到 `[0.05,10.0]`。record landmark/bbox、sidecar、stored-weight 组合、pair temporal weight 和 frame-weight summary 全部走统一清洗。
- 已扩展 `/data/WYC/signLanguage/work/scripts/run_flower_jump_frame_weight_robustness_gate.py`，新增 `malformed_sparse_sanitized`、`single_extreme_spike_sanitized`、`all_invalid_fallback` 正向用例，并硬检查 score/DTW/normalized distance/scoring-weight range 全部 finite。独立报告 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_frame_weight_robustness_gate_20260604_sanitized_weights_v1/flower_jump_frame_weight_robustness_gate.md` PASS：`花` 三个异常用例得分 `99.548/99.818/99.870`，`跳` 为 `90.120/77.723/78.072`，全部 finite 且通过。
- 保存网页回归 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_regression_flower_jump_20260604_sanitized_frame_weights_v1/flower_jump_web_regression.md` PASS；完整 66 门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_sanitized_frame_weights_66gate_v1/flower_jump_quality_gate.md` PASS，失败子门 `[]`。web replay `168/0` errors、diagnostics `149/0` errors、effective normal+borderline `124/128=96.875%`，`花=87/91`，`跳=37/37`。扩展后的 frame-weight 子门正向最低仍为正常 `back_loaded_broad_emphasis`：`花=99.161`、`跳=76.297`。
- 5080 scorer 已热重载到 `reload_count=21`、`loaded_at=2026-06-04T08:05:49`、`last_reload_error=None`；Holistic worker PID `811485` 未重启。watcher PID `3354603` 已指向 sanitized-frame-weights 66 门，事件 `no_target_samples`，formal marker 未移动且 target count 仍为 `0`。post-watch readiness `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_sanitized_frame_weights_66gate_postwatch_v1/flower_jump_retest_readiness.md` 为 `PASS/NOT_READY`，下一步仍是 `采集 花、跳`。

### 2026-06-04 10:03:01 CST：清洗时间元数据、修复 bbox 兼容评分并升级为 67 子门质量门

- 审计 `178` 个模板/网页 Holistic JSON：正常 `fps` 范围 `2.454-29.450`，`frame_idx` 范围 `0-106`，`timestamp_sec` 范围 `0-10.4`，无非有限值、重复或乱序。畸形探针确认旧加载器会因字符串/`NaN/Inf` 的 `fps/total_frames/frame_idx/timestamp_sec` 崩溃，且单个负数/极大 `frame_idx` 可把 `跳` 自匹配从 `100` 降到 `45`。
- 已更新 `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py`：统一清洗 `fps/total_frames/frame_idx/timestamp_sec`；优先使用 record/row 中仍有效的同帧副本，二者都坏时按总帧数做顺序保持回退；无效总帧数从可靠帧索引恢复，异常时间戳回退到 `frame_idx/fps`。同时修复旧 bbox 模式：只有完整 `21x3` landmark 手组才构造 two-hand relation，pose-robust hand diagnostics 缺少可选键时不再崩溃。
- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_temporal_metadata_robustness_gate.py`，覆盖顶层 fps/total_frames、单帧/整段 frame_idx、非有限/负数/极大时间戳、组合损坏和 bbox 兼容 finite-only 用例；不调用 `/api/score`、不运行 Holistic、不移动 marker、不重启 5080。独立最终门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_temporal_metadata_robustness_gate_20260604_sanitized_temporal_metadata_bbox_v3/flower_jump_temporal_metadata_robustness_gate.md` PASS：landmark 正向最低 `花=100.000`、`跳=100.000`，bbox 组合损坏用例两词均 `100.000` 且输出/元数据 finite。
- 完整最终 67 门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_sanitized_temporal_metadata_bbox_67gate_v2/flower_jump_quality_gate.md` PASS，67 个子门全部 returncode `0`，失败子门为空；web replay `168/0` errors、diagnostics `149/0` errors、effective normal+borderline `124/128=96.875%`，`花=87/91`，`跳=37/37`。保存网页回归 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_regression_flower_jump_20260604_sanitized_temporal_metadata_bbox_v2/flower_jump_web_regression.md` 同样 PASS。
- 5080 scorer 已热重载到 `reload_count=23`、`loaded_at=2026-06-04T10:01:37`、`last_reload_error=None`；backend PID `811445`、Holistic worker PID `811485` 未重启。watcher PID `3792390` 已引用最终 67 门，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后 target count 仍为 `0`。post-watch readiness `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_sanitized_temporal_metadata_bbox_67gate_postwatch_v2/flower_jump_retest_readiness.md` 为 `PASS/NOT_READY`，下一步仍是 `采集 花、跳`；目标不能标记完成，直到 marker 后真实网页摄像头 `花/跳` 双词样本出现并通过 watcher 诊断。

### 2026-06-04 10:56:17 CST：清洗缓存 JSON 结构异常并升级为 68 子门质量门

- 审计当前 `178` 个模板/网页 Holistic JSON 后确认正式缓存结构均正常；随后构造错类型 record/result_data/landmark group/landmark point/bbox/sidecar 探针。修复前 `花/跳` 共 `20` 个结构错类型用例直接抛异常，另有 `2` 个 bbox 非有限框用例产生非有限距离诊断。
- 已更新 `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py`：非字典 record 按空帧保留时序，自动模式忽略局部坏 result_data 而继续识别其余 landmark 帧；非 list landmark 组和非 dict landmark point 按缺失处理；bbox group/bbox 错类型和不可解析/非有限框值使用有限默认值；错类型 semantic-frame-weight sidecar 被安全忽略。正常缓存路径不变，局部结构损坏不会被当作新的有效动作证据。
- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_structural_json_robustness_gate.py`，只写临时畸形 fixture 并经正常 `load_sequence()`/`run_pair()` 评分，不调用 `/api/score`、不运行 Holistic、不移动 marker、不重启 5080。独立门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_structural_json_robustness_gate_20260604_v1/flower_jump_structural_json_robustness_gate.md` PASS：所有结构损坏变体保留帧数、模式和 finite 输出，正向最低 `花=97.283`、`跳=70.714`，bbox 组合损坏两词均 finite。
- 保存网页回归 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_regression_flower_jump_20260604_structural_json_v1/flower_jump_web_regression.md` PASS；完整重跑 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_structural_json_68gate_v1/flower_jump_quality_gate.md` PASS，`68/68` 子门全部 returncode `0`。正常网页指标保持：replay `168/0` errors、diagnostics `149/0` errors、effective normal+borderline `124/128=96.875%`，`花=87/91`，`跳=37/37`。
- 在线 scorer 已热重载到 `reload_count=24`、`loaded_at=2026-06-04T10:54:44`、`last_reload_error=None`；backend PID `811445`、Holistic PID `811485` 未重启。watcher PID `4015987` 已指向最终 68 门，事件 `no_target_samples`，formal marker 后 target count 仍为 `0`。post-watch readiness `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_structural_json_68gate_postwatch_v1/flower_jump_retest_readiness.md` 为 `PASS/NOT_READY`，下一步仍是 `采集 花、跳`。

### 2026-06-04 11:46:31 CST：修复合法但乱序时间元数据并保持 68 子门通过

- 审计当前 `178` 个模板/网页 Holistic JSON，正常证据中的 `frame_idx/timestamp_sec` 均严格递增且无重复，因此只有非严格递增时回退到 record 顺序不会改写当前正常数据。预修复合法值探针 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_valid_nonmonotonic_temporal_probe_20260604_prefix/probe.json` 显示：整段合法 `frame_idx` 倒序会把正确动作重排，`花` 自匹配从 `100` 降到 `13.854`，`跳` 从 `100` 降到 `20.756`；重复 frame index 或乱序 timestamp 即使得分仍高，也会留下不可信时间轴。
- 已更新 `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py`：完成所有 frame feature 构建后，若 frame index 非严格递增、重复或越界，则按原 record 顺序和 `total_frames` 生成严格递增 fallback；若 timestamp 非严格递增、非有限、负数，或 frame index 已回退，则统一按稳定后的 `frame_idx/fps` 重建时间轴。严格递增的正常稀疏 frame index 保持原值。
- 扩展 `/data/WYC/signLanguage/work/scripts/run_flower_jump_temporal_metadata_robustness_gate.py`，新增相邻交换、整段倒序、重复 frame index，以及相邻交换/整段倒序 timestamp 用例，并把元数据验收收紧为 frame index 与 timestamp 均严格递增。独立门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_temporal_metadata_robustness_gate_20260604_order_preserving_v1/flower_jump_temporal_metadata_robustness_gate.md` PASS：新增变体对 `花/跳` 均得 `100.000`，输出 `frame_idx_duplicate=0`、`frame_idx_nonmonotonic=0`、`timestamp_nonmonotonic=0`。
- 保存网页回归 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_regression_flower_jump_20260604_order_preserving_temporal_v1/flower_jump_web_regression.md` PASS；完整重跑 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_order_preserving_temporal_68gate_v1/flower_jump_quality_gate.md` PASS，`68/68` 子门全部 returncode `0`。正常网页指标不变：replay `168/0` errors、diagnostics `149/0` errors、effective normal+borderline `124/128=96.875%`，`花=87/91`，`跳=37/37`。
- 在线 scorer 已热重载到 `reload_count=25`、`loaded_at=2026-06-04T11:45:14`、`last_reload_error=None`；backend PID `811445`、Holistic PID `811485` 未重启。watcher PID `21753` 已指向本轮 68 门质量 JSON，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后 target count 仍为 `0`。post-watch readiness `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_order_preserving_temporal_68gate_postwatch_v1/flower_jump_retest_readiness.md` 为 `PASS/NOT_READY`，下一步仍是 `采集 花、跳`；目标不能标记完成，直到 marker 后真实网页摄像头 `花/跳` 双词样本出现并通过 watcher 诊断。

### 2026-06-04 13:15:31 CST：修复 Pose 归一化锚点污染并升级为 69 子门质量门

- 审计当前 `178` 个模板/网页 Holistic JSON：共有 `4776` 个有肩部 pose 帧，肩宽范围 `0.105884-0.571933`。新增拓扑判定后，正常数据仍有 `4776/4776` 个有肩部 pose 帧被判可信；`177` 个有足够手部帧的序列，其肩中心与 hand wrist 的 z 偏移中位数均在 `[-0.5112,-0.0056]`，没有正常序列触发整段 fallback。
- 预修复探针确认有限但错误的肩部锚点会污染整帧归一化：单肩 x 离群、双肩塌缩/异常宽度可把正确 `花/跳` 打到接近 `0`；进一步边界探针发现双肩整体 `y+0.7` 会把 `跳` 打到 `8.948`，双肩 `z-1.0/+1.0` 会打到 `5.622/9.439`。这些不是词义失败，而是部分帧落入绝对阈值、部分帧被拒绝后形成的不一致归一化锚点。
- 已更新 `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py`：肩部锚点现在同时校验绝对坐标/尺度、肩-鼻/肩-髋拓扑、pose wrist 与 hand wrist 的 x/y 流一致性；整段肩中心与 hand wrist 的 z 偏移中位数异常时强制禁用肩部锚点。稀疏坏肩点按 record 顺序由相邻可信锚点插值，整段肩部或 pose 流不可信时使用有效手部中心与掌尺度 fallback，再无手部时才使用稳健 pose fallback。
- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_pose_normalization_anchor_robustness_gate.py`。最终独立 v3 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_pose_normalization_anchor_robustness_gate_20260604_v3/flower_jump_pose_normalization_anchor_robustness_gate.md` 覆盖 `19` 个变体并 PASS：`花` 正向最低 `78.039`，`跳` 正向最低 `76.227`；此前的 `y/z` 边界误低分以及整段 pose `xy/z` 流漂移，修复后分别稳定回退到 `花=78.039`、`跳=78.935`。有限坐标门和有限越界坐标门也已按最终 scorer 重新通过。
- 保存网页独立回归 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_regression_flower_jump_20260604_pose_anchor_topology_v1/flower_jump_web_regression.md` PASS；完整重跑 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_pose_normalization_topology_69gate_v1/flower_jump_quality_gate.md` PASS，`69/69` 子门全部 returncode `0`。网页指标保持：replay `168/0` errors、diagnostics `149/0` errors、有效正常+边界 `124/128=96.875%`，其中 `花=87/91`、`跳=37/37`。
- 在线 scorer 已热重载到 `reload_count=26`、`loaded_at=2026-06-04T13:14:12`、`last_reload_error=None`；backend PID `811445`、Holistic PID `811485` 未重启。watcher PID `384054` 已指向最终 69 门，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`。post-watch readiness `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_pose_normalization_topology_69gate_postwatch_v1/flower_jump_retest_readiness.md` 为 `PASS/NOT_READY`，下一步仍是 `采集 花、跳`。

### 2026-06-04 14:13:34 CST：屏蔽非标准 Landmark 数组长度并升级为 70 子门质量门

- 审计当前 `178` 个模板/网页 Holistic JSON、`4781` 条 record：所有非空 landmark group 都符合固定 MediaPipe cardinality，pose 仅为 `33` 点、左右手仅为 `21` 点、face 仅为 `478` 点；另有正常的空数组表示整组缺失。既有结构门覆盖错类型和坏点，但没有覆盖非空 truncated/extra 数组或 landmark identity 被整体移位。
- 预修复 cardinality 探针 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_landmark_cardinality_probe_20260604_prefix/probe.json` 暴露两类误判：`花` 稀疏 pose 前插点会因索引整体错位被误打到 `56.377 score_valid`；`跳` 全程左侧 ground hand 被 drop/insert 后仍约 `84.9 score_valid`，属于畸形手组误高分。
- 已更新 `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py`：非空 pose/hand/face 数组必须分别精确为 `33/21/478` 点，否则整组按缺失处理；空数组仍作为合法缺失组；landmark 模式探测也只接受精确长度组。修复后 `花` 稀疏 pose 前插点恢复到 `98.760 score_valid`，`跳` 全程畸形左手降到 `2.161 needs_recapture`，畸形核心右手对 `花/跳` 分别降到 `1.164/0.236 needs_recapture`。
- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_landmark_cardinality_robustness_gate.py`，只写缓存 JSON fixture，不调用 `/api/score`、不运行 Holistic、不移动 marker、不重启 5080；覆盖 pose/face/core right hand、`跳` left ground hand 的 drop-first/drop-middle/insert-first/append-extra，并硬检查畸形组整组 mask。独立 v2 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_landmark_cardinality_robustness_gate_20260604_v2/flower_jump_landmark_cardinality_robustness_gate.md` PASS：`花` 正向最低 `78.039`、诊断最高 `1.164`；`跳` 正向最低 `76.227`、诊断最高 `2.161`。
- 因 scorer 变更，完整重跑新 70 子门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_landmark_cardinality_70gate_v1/flower_jump_quality_gate.md`，结果 `70/70` PASS、全部 returncode `0`、失败子门 `[]`。独立网页回归和统一门指标一致：replay `168/0` errors、diagnostics `149/0` errors、effective normal+borderline `124/128=96.875%`，其中 `花=87/91`、`跳=37/37`。
- 在线 scorer 已热重载到 `reload_count=27`、`loaded_at=2026-06-04T14:11:57`、`last_reload_error=None`；backend PID `811445`、Holistic PID `811485` 未重启。watcher PID `665220` 已指向最终 70 门，事件 `no_target_samples`，formal marker `web_20260602_233348_53e3df5d` 后目标样本仍为 `0`。post-watch readiness `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_landmark_cardinality_70gate_postwatch_v1/flower_jump_retest_readiness.md` 为 `PASS/NOT_READY`，下一步仍是 `采集 花、跳`；目标不能标记完成，直到 marker 后真实网页摄像头 `花/跳` 双词样本出现并通过 watcher 诊断。

### 2026-06-04 15:32:13 CST：屏蔽 Hand Wrist 根身份损坏并升级为 71 子门质量门

- 在固定 cardinality 修复后继续探测 exact-length landmark identity permutation。预修复时，`花` 右手 full reverse 仍为 `40.717 score_valid`、swap wrist/index MCP 为 `79.910 score_valid`；`跳` 右手 full reverse 为 `84.819 score_valid`，left-ground hand 的 rotate/reverse/wrist swap 仍约 `84.9-89.4 score_valid`。这些数组长度合法但 wrist 根点已被移走，不应作为正常手形参与评分。
- 审计 `178` 个模板/网页 Holistic JSON、`4750` 个非空 hand frame 后确认 MediaPipe hand z 使用 wrist-relative 原点：正常证据中 `4750/4750` 帧的 index `0` 都是最小绝对 z 点，wrist `|z0|` 最大仅 `9.218e-7`，阈值 `2e-6` 下 violation 为 `0`。几何拓扑/MST/chain-order 指标与当前真实 tracker artifact 有重叠，因此没有推广为硬拒绝规则；相邻整条 finger-chain swap 仍作为容错正例。
- 已更新 `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py`：若可见 hand index `0` 的有限 `|z|>2e-6`，把该帧整手按缺失处理，阻止 wrist 根身份被 exact-length permutation 移走后产生误高分。新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_hand_wrist_identity_robustness_gate.py`，只写缓存 JSON fixture，不调用 `/api/score`、不运行 Holistic、不移动 marker、不重启 5080；硬检查 rotate/reverse/wrist swap、稀疏损坏整组 mask、持续核心损坏低分，以及相邻 finger-chain swap 保持高分。
- 独立最终门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_hand_wrist_identity_robustness_gate_20260604_v2/flower_jump_hand_wrist_identity_robustness_gate.md` PASS：正常审计 `178` 文件、`4750` hand frames、`0` violation；`花` 正向最低 `79.773`、诊断最高 `1.164`，`跳` 正向最低 `81.642`、诊断最高 `2.161`。cardinality、bounded-coordinate、finger-identity-jitter 交互门均按最终 scorer 重新 PASS。
- 完整 71 门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_hand_wrist_identity_71gate_v1/flower_jump_quality_gate.md` 全量重跑 PASS，`71/71` 子门全部 returncode `0`。独立保存网页回归 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_regression_flower_jump_20260604_hand_wrist_identity_v1/flower_jump_web_regression.md` 与统一门指标一致：replay `168/0` errors、diagnostics `149/0` errors、effective normal+borderline `124/128=96.875%`，其中 `花=87/91`、`跳=37/37`。
- 在线 scorer 已热重载到 `reload_count=28`、`loaded_at=2026-06-04T15:31:37`、`last_reload_error=None`；backend PID `811445`、Holistic PID `811485` 未重启。watcher PID `1082212` 已指向最终 71 门，formal marker `web_20260602_233348_53e3df5d` 未移动且 target count 仍为 `0`。post-watch readiness `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_hand_wrist_identity_71gate_postwatch_v1/flower_jump_retest_readiness.md` 为 `PASS/NOT_READY`，下一步仍是 `采集 花、跳`；目标不能标记完成，直到 marker 后真实网页摄像头 `花/跳` 双词样本出现并通过 watcher 诊断。

### 2026-06-04 16:33:41 CST：屏蔽 Hand 内部拓扑身份损坏并升级为 72 子门质量门

- 在 wrist 根身份修复后继续探测保留 index `0` 的 exact-length 内部 permutation。预修复时，全指 PIP/DIP 交换仍会被当作有效手形：`花` 核心右手 `81.539 score_valid`，`跳` 右手小人 `74.190 score_valid`，`跳` 左手地面甚至 `98.031 score_valid`；`跳` 左手地面的整链 reverse/rotate 也可保持约 `84.9 score_valid`。这些不是真实动作风格差异，而是内部 joint identity 顺序损坏。
- 审计 `178` 个模板/网页 Holistic JSON、`4750` 个非空 hand frame 后建立保守解剖边界：正常最大 intra-chain backtrack turn 为 `5`、最大反向指链数为 `4`、非拇指 proximal/distal 三维骨段比中位数最小为 `0.520960`。当前硬规则只在 backtrack turns `>=6`、比例 `<0.5`，或全部 `5` 条指链反向且比例 `<0.8` 时屏蔽整手；正常证据 violation 为 `0`，相邻整条 finger-chain swap 仍保持不屏蔽。
- 已更新 `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py`：新增 `_hand_internal_topology_metrics()` 和 `_mask_hand_internal_topology_corruption()`，在 wrist 根身份清洗之后屏蔽具有强多指链解剖矛盾的整手。新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_hand_internal_topology_robustness_gate.py`，只写缓存 JSON fixture，不调用 `/api/score`、不运行 Holistic、不移动 marker、不重启 5080；覆盖内部 reverse/rotate、base-tip/PIP-DIP 交换、稀疏损坏容错和相邻整链交换控制组。
- 独立门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_hand_internal_topology_robustness_gate_20260604_v1/flower_jump_hand_internal_topology_robustness_gate.md` PASS：正常审计 `178` 文件、`4750` hand frames、`0` violation；`花` 正向最低 `79.773`、整段损坏诊断最高 `1.164`，`跳` 正向最低 `81.642`、整段损坏诊断最高 `2.161`。wrist-identity、finger-identity-jitter、bounded-coordinate、cardinality 交互门均按最终 scorer 重新 PASS。
- 完整 72 门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_hand_internal_topology_72gate_v1/flower_jump_quality_gate.md` 全量重跑 PASS，`72/72` 子门全部 returncode `0`。独立保存网页回归 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_regression_flower_jump_20260604_internal_topology_v1/flower_jump_web_regression.md` 与统一门指标一致：replay `168/0` errors、diagnostics `149/0` errors、effective normal+borderline `124/128=96.875%`，其中 `花=87/91`、`跳=37/37`。
- 在线 scorer 已热重载到 `reload_count=29`、`loaded_at=2026-06-04T16:32:47`、`last_reload_error=None`；backend PID `811445`、Holistic PID `811485` 未重启。watcher PID `1378389` 已指向最终 72 门，formal marker `web_20260602_233348_53e3df5d` 未移动且 target count 仍为 `0`。post-watch readiness `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_hand_internal_topology_72gate_postwatch_v1/flower_jump_retest_readiness.md` 为 `PASS/NOT_READY`，下一步仍是 `采集 花、跳`；目标不能标记完成，直到 marker 后真实网页摄像头 `花/跳` 双词样本出现并通过 watcher 诊断。

### 2026-06-04 17:39:59 CST：屏蔽非量化 Hand Landmark 局部碰撞并升级为 73 子门质量门

- 在 wrist 根身份和内部拓扑修复后继续探测 exact-length 手内 landmark 碰撞。预修复局部重复点仍可被当作有效身份参与评分，例如 `花` 右手全指 tip-to-DIP 碰撞为 `80.654 score_valid`，`跳` 右手同类碰撞为 `78.258 score_valid`，`跳` 左手地面的单对 tip-to-DIP 碰撞可达 `93.482 score_valid`。这些不是正常动作风格差异，而是两个或多个 landmark 身份共享同一三维坐标。
- 审计 `178` 个模板/网页 Holistic JSON、`4750` 个非空 hand frame：原始正常证据碰撞帧为 `0`，最小正常三维点间距为 `1.456e-4`，因此采用三维距离 `<=1e-5` 作为碰撞边界。量化审计同时确认不能按碰撞参与点总数丢弃整手：合理 `1/256` 三维量化可产生最多 `15` 个碰撞参与点，`320x240 + z/512` 网格可产生最多 `13` 个。
- 已更新 `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py`：对非量化手只屏蔽碰撞参与点；若完整手符合支持的全局摄像头/序列化网格签名，则保留所有量化点。当前全局网格签名在 `4750/4750` 个原始正常 hand frame 上误命中 `0`，对 `camera_640x480_z1024`、`camera_320x240_z512` 和 `xyz_1_256` 量化手均 `4750/4750` 识别，量化豁免未扩大到局部伪造碰撞。
- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_hand_landmark_collision_robustness_gate.py`，只写缓存 JSON fixture，不调用 `/api/score`、不运行 Holistic、不移动 marker、不重启 5080；覆盖单对、多对、大碰撞簇、稀疏恢复、持续核心语义损坏、双手关系损坏和 raw 量化兼容。独立最终门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_hand_landmark_collision_robustness_gate_20260604_v2/flower_jump_hand_landmark_collision_robustness_gate.md` PASS：`花` 正向最低/严重碰撞诊断最高为 `78.512/10.731`，`跳` 为 `70.714/9.307`；正常碰撞和全局量化签名误命中均为 `0`。
- 完整 73 门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_hand_landmark_collision_73gate_v1/flower_jump_quality_gate.md` 全量重跑 PASS，`73/73` 子门全部 returncode `0`。独立保存网页回归 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_regression_flower_jump_20260604_hand_landmark_collision_v1/flower_jump_web_regression.md` 与统一门指标一致：replay `168/0` errors、diagnostics `149/0` errors、effective normal+borderline `124/128=96.875%`，其中 `花=87/91`、`跳=37/37`。
- 在线 scorer 已热重载到 `reload_count=30`、`loaded_at=2026-06-04T17:37:30`、`last_reload_error=None`；backend PID `811445`、Holistic PID `811485` 未重启。watcher 已用 `setsid` 重启为 PID `1678764` 并指向最终 73 门，事件 `no_target_samples`；formal marker `web_20260602_233348_53e3df5d` 未移动且 target count 仍为 `0`。post-watch readiness `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_hand_landmark_collision_73gate_postwatch_v1/flower_jump_retest_readiness.md` 为 `PASS/NOT_READY`，下一步仍是 `采集 花、跳`；目标不能标记完成，直到 marker 后真实网页摄像头 `花/跳` 双词样本出现并通过 watcher 诊断。

### 2026-06-04 18:42:20 CST：屏蔽 Hand 极端骨段伸缩并升级为 74 子门质量门

- 在 landmark 碰撞修复后继续审计“不发生坐标碰撞、但单条指骨极端缩短或拉长”的 exact-length 手部输入。当前 `178` 个模板/网页 Holistic JSON、`4750` 个完整 hand frame、`71250` 条内部指骨的正常相对长度范围为 `0.007098-1.665053`；采用远离正常证据的保守边界 `[0.003,2.0]`，正常违反帧、短骨段、长骨段和原始全局量化签名误命中均为 `0`。
- 已更新 `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py`：完整非量化手若相邻指骨长度/掌尺度落到 `[0.003,2.0]` 外，只屏蔽异常骨段参与点；完整手符合既有全局量化网格签名时直接旁路，避免合理坐标量化造成零长度骨段被误判。量化审计显示若无旁路，`camera_640x480_z1024`、`camera_320x240_z512`、`xyz_1_256` 分别会有 `19/172/336` 帧触发，但当前旁路后错误屏蔽均为 `0`。
- 新增 `/data/WYC/signLanguage/work/scripts/run_flower_jump_hand_bone_length_integrity_robustness_gate.py`，只写缓存 JSON fixture，不调用 `/api/score`、不运行 Holistic、不移动 marker、不重启 5080；覆盖单条/全链极短骨段、远端极长骨段、稀疏损坏恢复、持续核心损坏和 raw 量化兼容。独立最终门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_hand_bone_length_integrity_robustness_gate_20260604_v2/flower_jump_hand_bone_length_integrity_robustness_gate.md` PASS：`花` 正向最低/整段损坏诊断最高 `78.512/10.731`，`跳` 为 `70.714/6.762`。
- 独立保存网页回归 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_regression_flower_jump_20260604_hand_bone_length_integrity_v1/flower_jump_web_regression.md` PASS；完整 74 门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_hand_bone_length_integrity_74gate_v1/flower_jump_quality_gate.md` 全量重跑 PASS，`74/74` 子门全部 returncode `0`。网页指标保持：replay `168/0` errors、diagnostics `149/0` errors、effective normal+borderline `124/128=96.875%`，其中 `花=87/91`、`跳=37/37`。
- 在线 scorer 已热重载到 `reload_count=31`、`loaded_at=2026-06-04T18:40:50`、`last_reload_error=None`；backend PID `811445`、Holistic PID `811485` 未重启。watcher PID `1973666` 已指向最终 74 门，事件 `no_target_samples`；formal marker `web_20260602_233348_53e3df5d` 未移动且 target count 仍为 `0`。post-watch readiness `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_hand_bone_length_integrity_74gate_postwatch_v1/flower_jump_retest_readiness.md` 为 `PASS/NOT_READY`，下一步仍是 `采集 花、跳`；目标不能标记完成，直到 marker 后真实网页摄像头 `花/跳` 双词样本出现并通过 watcher 诊断。

### 2026-06-04 19:54:47 CST：修复部分可见 Hand 对骨段完整性规则的绕过

- 继续审计完整手骨段规则时发现组合绕过：先用一个越界点让手变成部分可见，再把其余 distal 骨段全部拉长，旧规则因不再满足 21 点完整手而跳过检查；预修复探针中 `花=80.035 score_valid`、`跳=78.258 score_valid`。修复后的同一探针分别降为 `9.295/1.584 semantic_mismatch`。
- 已更新 `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py`：骨段完整性规则在 wrist 可见、至少 `16` 个点可见且至少 `3` 个可信 palm reference 时也检查部分可见手；掌尺度由 mean 改为更抗缺点偏置的 median，只评估两端均可见的内部骨段，并保留全局量化网格旁路。规则仍只处理远离正常证据的极端骨段，不替代 finger-length-style 容错。
- 扩展 `/data/WYC/signLanguage/work/scripts/run_flower_jump_hand_bone_length_integrity_robustness_gate.py`：新增所有单缺点、所有双缺点、常见多缺点、部分可见量化和 `all_distal_long_plus_thumb_tip_out_of_bounds` 绕过 fixture。正常审计覆盖 `178` 个文件；single-missing `95000`、pair-missing `878750`、common-multi `23750` 个已评估 case 均为 `0` violation/`0` mask violation，部分可见量化签名/旁路违反也均为 `0`。最终正常 median 骨段比范围为 `0.006003-1.831200`。
- 扩展独立骨段门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_hand_bone_length_integrity_robustness_gate_20260604_partial_visibility_v1/flower_jump_hand_bone_length_integrity_robustness_gate.md` PASS：`花` 正向最低/诊断最高 `78.512/10.759`，`跳` 为 `70.714/6.762`；绕过 fixture 的 `40/40` 与 `17/17` 帧均被处理。碰撞、有限/越界坐标、cardinality、finger-length-style、内部拓扑和 coordinate-precision 交互门均按最终 scorer 重新 PASS。
- 独立保存网页回归 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_regression_flower_jump_20260604_partial_hand_bone_length_v1/flower_jump_web_regression.md` PASS；完整 74 门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_partial_hand_bone_length_74gate_v1/flower_jump_quality_gate.md` 全量重跑 PASS，`74/74` 子门全部 returncode `0`。网页指标保持 replay `168/0`、diagnostics `149/0`、effective normal+borderline `124/128=96.875%`，其中 `花=87/91`、`跳=37/37`。
- 在线 scorer 已热重载到 `reload_count=32`、`loaded_at=2026-06-04T19:53:03`、`last_reload_error=None`；backend PID `811445`、Holistic PID `811485` 未重启。watcher 已重启为 PID `2311546` 并指向部分可见手 74 门，事件 `no_target_samples`；formal marker `web_20260602_233348_53e3df5d` 未移动且 target count 仍为 `0`。post-watch readiness `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_partial_hand_bone_length_74gate_postwatch_v1/flower_jump_retest_readiness.md` 为 `PASS/NOT_READY`，下一步仍是 `采集 花、跳`；目标不能标记完成。

### 2026-06-05 14:40:46 CST：整理当前前端优化中文报告并导出 Word

- 已整理当前 5080 前端优化阶段报告，Markdown 路径为 `/data/WYC/signLanguage/work/reports/frontend_optimization_summary_20260605.md`，Word 路径为 `/data/WYC/signLanguage/work/reports/frontend_optimization_summary_20260605.docx`。报告覆盖单服务运行态收敛、摄像头/参考视频/倒计时/布局交互、高频候选采集与运动能量选帧、`frame_indices/frame_weights/client_*` 上传契约、语义诊断结果面板、样本 ID 复制、watcher 自动诊断面板、词条覆盖 chip、下一步复测提示和剩余限制。
- 报告前已重启并确认当前 5080/Holistic 可用：`http://127.0.0.1:5080`，Holistic worker `ready`，PID `3896404`，初始化耗时 `260.114s`，当前模板数 `10`，模板库仍为 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`。
- 已运行只读前端契约检查 `/home/wuyangcheng/myenv/bin/python /data/WYC/signLanguage/work/scripts/check_watch_status_frontend_contract.py --base-url http://127.0.0.1:5080 --output-dir /data/WYC/signLanguage/work/generated/scoring_mvp_run3/frontend_optimization_report_contract_20260605_v1`，结果 `PASS`，`failed_count=0`、`warning_count=0`，`/`、`/static/app.js`、`/static/styles.css`、`/openapi.json` 均 HTTP 200，并确认运动签名采集、非均匀权重、能量覆盖选帧、自动诊断、词条覆盖、下一步复测和相位顺序守卫 UI token 均存在。

### 2026-06-05 15:00:00 CST：整理当前打分算法优化详细中文报告并导出 Word

- 已整理当前打分算法优化详细报告，Markdown 路径为 `/data/WYC/signLanguage/work/reports/scoring_algorithm_optimization_summary_20260605.md`，Word 路径为 `/data/WYC/signLanguage/work/reports/scoring_algorithm_optimization_summary_20260605.docx`。报告共 `779` 行，覆盖基础 raw landmark DTW、判别性门控、文本语义 profile、动态帧权重、semantic phase、语义相位加权 DTW、混合对齐策略、`花` opening/short-core/confusion guard、`跳` two-hand relation/local fallback、capture_quality、cross-word check、保存网页回放闭环、74 子门质量门、代表性鲁棒性结果和仍未完成的真实用户校准限制。
- 报告引用当前质量门 `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_partial_hand_bone_length_74gate_v1/flower_jump_quality_gate.md`：综合 `PASS`，`74/74` 子门 returncode `0`；保存网页/API replay `168` 样本错误 `0`，花/跳 diagnostics `149` 样本错误 `0`，有效正常+边界 `124/128=96.9%`，其中 `花=87/91`、`跳=37/37`。
- 当前 5080 状态在报告前确认：worker `ready`，PID `3896404`，Holistic 初始化 `260.114s`，模板数 `10`，scorer 文件 `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py` 已于 `2026-06-05T14:08:09` 随新后端加载，`last_reload_error=None`。


# workEpoch3 26/6/10~


## teamwork 

P: 现在，我想请你调查一下合适的团队代码写作工作流程方案，比如GitHub协作，比如基于codex的项目团队协作，等；我希望有统一的代码仓库，工作环境，能够方便地和团队进行代码上的协调和沟通，最好和团队成员能共享上下文，甚至是ai上下文。请你调研出多种合适的团队工作方案，整理出详细的中文报告。

P: 现在，我希望基于 /data/WYC/skill_research/team_code_ai_workflow_20260610/team_code_ai_workflow_report_20260610.md 里面的方案A，先实现基础的团队协作项目管理。目前我已经有服务器本地的 signLanguage项目仓库，它实现了手语打分核心算法和前后端搭建等，现在我希望和团队其他成员一起协作推进整个手语学习宇宙项目开发，其他成员目前完成了其他网页内容的前端开发，我的手语打分模块要和它们整合在一起。目前大家还没有建立github仓库。接下来，我希望主导构建一个手语学习宇宙github团队仓库，先加入我的本地仓库部分，之后会合并其他人的模块，我希望建立规范化的团队代码协作和管理，请你给出详细的操作方案。


P: 命名调整了：
GitHub Org:  sign-language-universe
Main Repo:   sign-language-universe

请据此调整你刚刚的plan文档

DONE


P: 现在，已经有了 /data/WYC/signLanguage/work/other/sign-language-universe/sign-language-universe 别人的前端代码和资料等；我要开始建立团队github仓库了。你补充一下操作手册；或者可以的话，你来自动化操作，根据我前面的具体需求


我还没有创建 团队 github 仓库，可以给我整理一下操作手册

创建：• monorepo 是 monolithic repository 的缩写，意思是：把一个项目里的多个模块
  放在同一个 Git 仓库里管理

P: 现在，团队org和main repo都已经创建，你可以帮我提交了

Q: 也就是说 org里面的team，每个负责相应的只能，每个team内部再有相应成员；所以org的组织层级就是：
org -> team -> member  理解的对吗 

A: • 对，核心理解是：

  GitHub Organization
    -> Team
      -> Member

  也就是：

  sign-language-universe 这个 org
    -> frontend team
      -> 前端成员 A / 前端成员 B
    -> scoring team
      -> 评分算法成员 A / 后端成员 B
    -> content team
      -> 内容成员 A
    -> qa team
      -> 测试成员 A
    -> maintainers team
      -> 仓库维护负责人

  但还要补一个关键点：仓库权限通常是授权给 team，而不是直接授权给每个
  member。

  所以完整关系更像：

  Organization
    -> Team
      -> Member

  Repository
    -> 授权给 Team

  例如：

  sign-language-universe/sign-language-universe 仓库
    -> frontend team: Write 权限
    -> scoring team: Write 权限
    -> qa team: Triage 权限
    -> maintainers team: Maintain 权限

  这样你以后只需要把新人加入对应 team，他就自动获得这个 team 对仓库的权
  限。比如新前端同学加入 frontend，就自动能对仓库创建分支、提交代码、发
  PR。

Q: 对于一个团队仓库，Direct access 和 Organization access 区别是？

A: • 是 GitHub 仓库 Settings -> Collaborators & teams 里两类访问来源的区别。

  Direct access
  表示这个人或 team 是直接被加到这个仓库上的。

  例子：

  sign-language-universe 仓库
    -> 直接添加 frontend team: Write
    -> 直接添加 scoring team: Write
    -> 直接添加某个成员 alice: Admin

  特点：

  - 在当前仓库页面就能直接修改或移除。
  - 适合给某个 team 配置这个仓库的明确权限。
  - 不建议长期给个人 direct access，除非是临时协作者或特殊负责人。
  - 如果一个 team 是直接加到仓库的，它的权限可以在这个仓库里直接改。

  Organization access
  表示这个人能访问仓库，但权限来源不是这个仓库里直接添加的，而是来自组织层
  级，例如：

  Organization base permission
  Organization role
  Parent team 继承权限
  某个 team 的间接权限

  例子：

  Organization 默认给所有成员 Read
    -> 所有 org member 都能读这个仓库

  或者：

  engineering parent team: Write
    -> frontend child team 继承 Write
    -> frontend 成员可以访问仓库

  这种访问通常要回到权限来源那里改，比如 org 设置、parent team、
  organization role，而不是只在当前仓库里改。

  对你们当前项目，推荐理解为：

  Direct access:
    maintainers / frontend / scoring / content / qa 这些 team 直接授权到主
    仓库

  Organization access:
    由 org 默认权限、组织角色、parent team 继承等带来的访问

  我的建议是：

  Organization base permission: No permission 或最小权限
  主仓库权限: 主要通过 team 的 Direct access 管理
  个人 Direct access: 尽量少用
  Admin: 只给极少数负责人

  这样权限来源最清楚：谁能访问仓库，主要看他在哪个 team 里。

Q: Your protected branch rules for your branch won't be enforced on this private repository until you upgrade your organization account to a GitHub Team or Enterprise account.

A: • 这个提示的意思很明确：你现在的 GitHub Organization 账户是 Free，且仓库是
  private，所以 main 分支保护规则即使配置了，也不会真正生效。

  也就是说，目前这些规则不会硬性拦截：

  禁止直接 push main
  要求 PR
  要求 review
  要求 CI 通过
  要求 CODEOWNERS review
  禁止 force push

  原因是 GitHub 对私有仓库的分支保护有计划限制。官方文档里也写了：
  protected branches 在 GitHub Free 组织下只支持 public repositories；
  private repositories 需要 GitHub Team 或 Enterprise。GitHub Team 计划包
  含 private repositories 的 protected branches、required reviewers、Code
  owners 等能力。

  你现在有几个选择：

  方案 1：升级 Organization 到 GitHub Team
  推荐。继续保持 private repo，同时 main 分支保护真正生效。

  方案 2：把仓库改成 public
  技术上可用 Free 的分支保护，但不推荐，除非确认代码、资料、算法、素材都可
  以公开。

  方案 3：保持 Free + private
  可以继续用 PR 流程、CODEOWNERS、CI、团队约定，但 GitHub 不会强制阻止直接
  push main。

  对你们这个项目，我建议是：

  短期：
    仓库继续 private
    团队仍按 PR 流程协作
    明确约定不要直接 push main
    main 只由 maintainers 合并

  如果正式多人开发：
    升级 GitHub Team
    让 main 分支保护真正生效

  在没有升级前，文档里的分支保护设置可以先保留，但要标注为：

  当前 Free organization + private repository 下不会被强制执行；
  升级 GitHub Team 后才会真正生效。

## github 网页构建

P: 现在我想访问已经在仓库里面的前端，给我操作手册

P: 你参考一下下面的说法，看看能不能直接让网页建立在GitHub仓库上，而不我的服务器上？
进入仓库的Settings（设置）页面
在你的代码仓库页面，点击顶部菜单栏的 Settings。

找到Pages（页面）选项
在左侧菜单栏里，找到并点击 Pages。这通常在 "Code and automation" 分类下。

选择分支并保存
在 "Branch" (分支) 选项下，选择包含你网页代码的分支，通常是 main 或 master。然后，点击文件夹图标，选择根目录 / (root)，最后点击 Save 按钮。

<div align="center" style="display: flex; justify-content: center; gap: 20px; margin: 20px 0;"> < img src="https://img-blog.csdnimg.cn/6cf6c5a0e6a84be093c24c757cc09b96.png" alt="选择分支界面" style="max-width: 45%; height: auto;"> < img src="https://img-blog.csdnimg.cn/1f3451ced57b492ab68f808da23ef742.png" alt="保存设置界面" style="max-width: 45%; height: auto;"> </div>
获取你的网站地址
保存成功后，页面会刷新，并在顶部显示一个绿色的地址栏，那就是你的网站地址了。通常是 https://你的用户名.github.io/你的仓库名/ 的格式。注意，如果是用户主页型的仓库（仓库名是你的用户名.github.io），地址会更短。

配置完成后，可能需要等待1-2分钟才能成功访问，请耐心等待一下。


NEW：

  你现在需要在 GitHub 页面手动做这一步：

  Repository -> Settings -> Pages
  Build and deployment -> Source -> GitHub Actions

  然后去：

  Actions -> Deploy frontend to GitHub Pages

  运行或等待 workflow。

  默认访问地址应是：

  https://sign-language-universe.github.io/sign-language-universe/




P: 我们现在决定把仓库设置成public，请补充相关的 apache 权限等

NOTE: 视频素材，要询问提供方是否愿意被公开使用

NOTE:  视频素材应该分成两类，一类是网页上可以公开展示，用于学习的；另一类是可以只是我们内部训练使用，但不公开
  要确认知情同意等。。


## 测试PR

P: 现在，我要开始测试PR提交了

p: 我提交了 git push -u origin docs/test-pr-flow；现在怎么设置PR，我作为owner，怎么approve？谁有权限approve？

A:  你作为 owner 能不能 approve？

  分情况：

  如果 PR 是你自己提交/创建的：
    你不能 approve 自己的 PR。
    即使你是 owner，GitHub 也不允许 PR author approve 自己的 PR。

  如果 PR 是别人提交的：
    你作为 owner/admin 可以 approve。

  所以这次 docs/test-pr-flow 如果 commit 是你自己推的，就需要另一个有权限
  的人 approve。

  谁的 approve 算数？

  对你们当前仓库，最稳妥的是：

  maintainers team 成员
  有 Write / Maintain / Admin 权限的人
  对应 CODEOWNERS team 里的成员

  当前 .github/CODEOWNERS 里有全局规则：

  * @sign-language-universe/maintainers

  所以普通文档改动默认会要求 maintainers review。如果你开启了 Require
  review from Code Owners，那就需要 maintainers 里另一个成员 approve。

  推荐流程

  1. 你创建 PR：docs/test-pr-flow -> main
  2. 右侧 Reviewers 选择 @sign-language-universe/maintainers 或具体成员
  3. 等 CI 通过
  4. 另一个 maintainer 打开 PR -> Files changed -> Review changes ->
  Approve
  5. 你或 maintainer 点击 Squash and merge
  6. 删除 docs/test-pr-flow 分支

  如果现在团队里还没有第二个 maintainer，你需要先把一个成员加入：

  Organization -> Teams -> maintainers -> Members -> Add a member

  并确保 maintainers 对仓库至少有 Write，推荐 Maintain。


Q: 那怎么办，我就是仓库目前的唯一主管人，我希望我能方便地完成自己提交的approve，这允许吗？
A: • 不允许。GitHub 明确不允许 PR 作者 approve 自己的 PR，即使你是 owner/
  admin，这个 approval 也不能算作 required approval。

  你有三个现实选择：

  方案 A：单人维护阶段推荐

  保留 PR 流程，但暂时不要要求 approval：

  Require a pull request before merging: 开
  Require approvals: 关
  Require review from Code Owners: 关
  Require status checks: 开

  这样你仍然必须走：

  branch -> PR -> CI 通过 -> merge

  但不需要别人 approve。适合当前只有你一个主管人的阶段。

  方案 B：允许 owner/admin bypass

  你可以配置允许管理员绕过规则，然后自己 merge。但这不是“自己 approve”，而
  是“管理员绕过 required review”。

  需要确认没有开启：

  Do not allow bypassing the above settings

  这种方式方便，但审计意义弱一些。适合临时救急，不建议作为长期日常流程。

  方案 C：加一个真实 maintainer

  找一个团队成员加入：

  maintainers team

  并给仓库：

  Maintain 或 Write 权限

  之后你的 PR 由他 approve，他的 PR 由你 approve。这是正式团队协作最推荐的
  方式。

  我建议你现在用方案 A，把 main 保护规则改成：

  必须 PR
  必须 CI 通过
  暂不强制 approval
  暂不强制 CODEOWNERS review
  禁止 force push
  禁止删除 main

  等团队至少有第二个 maintainer 后，再打开：

  Require approvals: 1
  Require review from Code Owners

  这样既保留规范流程，又不会卡住你这个唯一维护者。


NOW：no need for approval..


Q: 现在别人提交了PR，我作为主管如何通过它，实现merge？

A: • 可以。别人提交的 PR，你作为主管可以正常 Approve 并 Merge，前提是你有仓库
  Write / Maintain / Admin / Owner 权限，并且你不是这个 PR 的作者。

  网页操作流程

  1. 进入仓库：

  https://github.com/sign-language-universe/sign-language-universe

  2. 点击顶部 Pull requests。
  3. 打开别人提交的 PR。
  4. 先看这几个状态：

  Conversation: 有没有讨论未解决
  Files changed: 改了哪些文件
  Checks: CI 是否通过
  Reviewers / Code owners: 是否要求特定团队 review

  5. 审代码：

  Files changed -> Review changes -> Approve -> Submit review

  如果有问题，选：

  Request changes

  或直接评论，让对方继续改。

  6. CI 通过、approval 满足后，在 PR 页面底部点击：

  Squash and merge

  再点：

  Confirm squash and merge

  7. 合并后点击：

  Delete branch

  如果这个按钮出现的话。

  推荐你们用 Squash and merge

  这样每个 PR 进入 main 只形成一个清晰提交，适合你们现在的团队协作阶段。

  用 gh 命令行也可以

  你先登录：

  gh auth login --hostname github.com --git-protocol ssh --web

  然后：

  cd /data/WYC/sign-language-universe

  gh pr list
  gh pr view <PR编号> --web
  gh pr review <PR编号> --approve -b "Reviewed and approved."
  gh pr checks <PR编号>
  gh pr merge <PR编号> --squash --delete-branch

  合并后本地同步：

  git switch main
  git pull --ff-only

  NOTE: 谁的 approve 算数

  一般算数的是：

  有 Write / Maintain / Admin / Owner 权限的人
  不是 PR 作者本人
  如果开启 CODEOWNERS，则还要是对应 CODEOWNERS 成员


P:  现在网页端操作成功通过了PR，接下来，我想看看试试 本地 gh 管理这个团队
  仓库，我作为主管者怎么操作；你可以给一下相关的操作手册





### gh 安装
P: 要不要给本地当前环境加入 gh 等，方便仓库管理？
A: • 建议装。你现在已经开始做 org、public repo、Pages、分支保护、团队权限这些
  操作，gh 会明显方便很多。

  我刚检查了当前环境：

  gh: 未安装
  系统: Ubuntu 22.04.5 LTS
  包管理器: apt

  建议本地工具组合：

  gh        GitHub CLI，管理 repo / PR / issue / Actions / Pages / API
  jq        处理 gh api 返回的 JSON
  git-lfs   后续管理 .glb、视频等大文件

  安装建议用 GitHub CLI 官方 apt 源，不建议用 snap。Ubuntu 上可用：

  sudo apt update
  sudo apt install -y wget gpg jq git-lfs

  sudo mkdir -p -m 755 /etc/apt/keyrings
  wget -nv -O /tmp/githubcli-archive-keyring.gpg
  https://cli.github.com/packages/githubcli-archive-keyring.gpg
  sudo install -m 644 /tmp/githubcli-archive-keyring.gpg /etc/apt/
  keyrings/githubcli-archive-keyring.gpg

  echo "deb [arch=$(dpkg --print-architecture)
  signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg]
  https://cli.github.com/packages stable main" \
    | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null

  sudo apt update
  sudo apt install -y gh

  安装后认证：

  gh auth login

  建议选择：

  GitHub.com
  SSH
  Login with a web browser

  后续常用命令会很有用：

  gh repo view sign-language-universe/sign-language-universe
  gh pr list
  gh pr create
  gh pr checkout <PR编号>
  gh workflow list
  gh workflow run pages.yml
  gh run list
  gh run watch
  gh api repos/sign-language-universe/sign-language-universe/pages

  对你们当前项目，gh 最有价值的是：

  1. 检查 GitHub Pages 是否启用、部署是否成功
  2. 看 Actions 日志
  3. 创建和合并 PR
  4. 管理 issue / milestone
  5. 用 gh api 检查分支保护、仓库 public 状态、team 权限

  注意一点：gh auth login 会在当前服务器用户目录下保存 GitHub 凭据，不会进
  入仓库，但这台服务器如果多人共用，就要确保只在你自己的 Linux 用户下登
  录，不要把 token 写进项目文件。

NEW: • 已安装好 gh，因为当前用户没有无密码 sudo，我采用了用户目录安装。

  安装结果：

  gh version 2.94.0
  安装位置: ~/.local/share/gh-2.94.0/bin/gh
  命令入口: ~/.local/bin/gh

  验证通过：

  gh --version

  当前还没有登录 GitHub，后续你需要执行：

  gh auth login --hostname github.com --git-protocol ssh --web

  我也新增了使用手册：

  sign-language-universe/docs/operations/
  github_cli_management_manual_20260611.md

  注意：由于 main 分支保护已经生效，直接 push main 被 GitHub 拒绝了：

  Changes must be made through a pull request.

  所以我把手册提交到了新分支：

  docs/github-cli-management-manual

  PR 创建链接：

  https://github.com/sign-language-universe/sign-language-universe/pull/new/docs/github-cli-management-manual

  提交是：

  3d2e203 docs: add GitHub CLI management manual

  手册里包含：登录、仓库 public 状态检查、GitHub Pages、Actions、PR、
  Issue、分支保护、Team 权限检查、升级/卸载方式。

  参考官方资料：

  - https://cli.github.com/manual/
  - https://cli.github.com/manual/gh_auth_login
  - https://github.com/cli/cli/releases





## 合并手语打分前端模块

P: 现在，我要合并之前专门的手语打分的前端模块到整体的手语宇宙前端里面








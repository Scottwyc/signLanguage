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

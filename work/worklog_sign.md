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

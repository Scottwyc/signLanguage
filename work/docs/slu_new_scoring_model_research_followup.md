# 新版手语打分算法 · 开源模型调研 Followup

> 任务发起：2026-08-09
> 状态：调研中（4 个后台 agent 并行）
> 本文档随任务推进持续更新，最终结论汇总到正式技术报告。

## 1. 任务目标

- 为手语打分项目寻找**开源的手语识别/打分模型**，用现有 21 词词汇数据微调。
- 硬性约束：模型**轻量化**；可**网页部署**（浏览器端推理优先）或至少**魔塔创空间**部署。
- 产出：技术报告（候选模型评估 + 推荐方案 + 落地路径）。

## 2. 本地现状（已梳理 2026-08-09）

### 2.1 数据
- 21 词：谗（羡慕）、唱歌、超市、船（轮船）、公交车、虎、花、鸡蛋、烤串、科学、牛奶、朋友、汽车、汽车（二）、人们（人民）、森林、跳、香蕉、勇敢、月亮、指示
- 21 词 × 11 志愿者 × 3 视角 × 2 重复 = 1,384 条原始视频；受信任正样本 **930 条**（answer=1 且准入），人工负例 71 条
- 数据形态：**MediaPipe Holistic landmark 序列**（pose 33 + 双手 21×2 + face），15fps 采样
  - 前端采集：3s × 10fps = 30 帧，720p，浏览器本地提取关键点
- 特征：237 维/帧（7 静态组：pose 27 / 左右手 63×2 / 左右手形 20×2 / face 36 / 双手关系 8）+ motion 动态组（v4 = 406 维）
- 分析结论：235d 帧均值 + LinearSVC 跨人 21 词分类 **95.6%**；手形+手位置为主干，face 无判别力（谗词除外——嘴形语义）

### 2.2 现有打分算法（v2.1 并集三层）
- 层1 模板并集（每词 6 模板 × top-2 截尾均值）→ 层2 判别力权重 + 动态过程特征（局部加权）→ 层3 包络软化（q50/q90 容差）
- DTW 时序对齐；总分-核心组联动 `min(baseScore, group_composite_score)`
- 验证：21/21 判别（AUC/召回/拒绝 全 1.000），正样本 avg 90-98 分，负样本 avg 46-77 分
- 特点：**纯手工特征工程 + DTW + 人工校准权重**（每词 40+ 超参数键）

### 2.3 部署现状
- GitHub Pages 前端（sign-language-universe.github.io）+ 浏览器本地 MediaPipe Holistic
- 魔塔创空间 lite 后端：`https://scottwyc-sign-language-universe-lite.ms.show`（FastAPI，前端只传 landmark_rows）
- full Docker 版（服务端 Holistic worker）存在但非默认
- 魔塔推送经验：用户名必须 `oauth2` + Access Token

### 2.4 已知痛点（换新版算法的动机候选）
- 手工特征工程 + 人工权重校准工作量大、难扩展到新词/新用户
- 谗词"舌头舔"检测无解（Holistic 无舌头关键点）
- 打分=质量评估（0-100），而开源 SLR 模型多为分类模型 → 需要置信度/相似度映射

## 3. 调研 Agent 清单（2026-08-09 启动，4 个并行）

| # | Agent | 调研主题 | 状态 | 备注 |
|---|-------|---------|------|------|
| 1 | general-purpose-call_01_vwDjl6qJeXVWsmYJ5fyJ1829 | MediaPipe Gesture Recognizer / Model Maker / keypoint 手语项目 | 运行中 | |
| 2 | general-purpose-call_02_3ErJH6Ma6K7c8li3CbnR9847 | HF/ModelScope/学术开源 SLR 模型（SignBERT 等） | 运行中 | |
| 3 | general-purpose-call_01_DnF8mhIRTEgsc300Bye78050 | 魔塔创空间平台能力/已有手语创空间/模型 | 运行中 | |
| 4 | general-purpose-call_02_mzaQsX7ZgCpPT2SkRb5Y9084 | 浏览器推理生态（tfjs/onnx-web/WebGPU）+ 中文手语数据集 | 运行中 | |

## 4. 候选模型方向（agent 1 结果已回填，其余待回）

### ✅ Agent 1 结论（MediaPipe 方案，2026-08-09 完成）
- **官方 Gesture Recognizer（8MB .task）+ Model Maker 路线：淘汰**——仅单帧静态手势（无时序建模）、训练数据必须是图片（不支持 landmark/视频序列）、Model Maker 官方已弃用（deprecated, no longer actively maintained）
- **主推路线：MediaPipe 关键点序列 + 轻量时序分类器**（与我们 235 维特征管线直接兼容）

| 候选 | 来源 | 许可证 | 参数/大小 | 输入 | 小样本表现 | 评估 |
|------|------|--------|-----------|------|-----------|------|
| **SPOTER**（pose Transformer, WACV2022W） | github.com/maty-bohacek/spoter | Apache 2.0 | 5.92M | 108d/帧骨架（可改 235d） | LSA64 10% 数据 88.68% → 100% | **4/5 首选参考架构** |
| **3 层 LSTM（nicknochnack 教程架构）** | github.com/nicknochnack/ActionDetectionforSignLanguage | **无 LICENSE** | ~7MB 权重 | (30,1662) Holistic（可改 235） | 教程级 | 4/5 架构最贴合，仅参考自研 |
| harveyfly/SignLanguageRecognition（Bi-LSTM） | github.com/harveyfly/SignLanguageRecognition | **无 LICENSE** | - | 骨骼关键点 24d×36 帧 | 中科大 500-CSL 中文词 | 3/5 中文对标，仅方法参考 |
| 209sontung/sign-language（1DCNN+Transformer） | github.com/209sontung/sign-language | MIT | fp16 .h5 | 手关键点 192 帧 | ASL 手指拼写 250 类 | 3/5 TF.js 友好 |
| Kaggle ASL 冠军方案 | github.com/ChristofHenkel/kaggle-asl-fingerspelling-1st-place-solution | Apache 2.0 | - | MediaPipe 关键点序列 | 比赛级 | 强参考 |
| rishusiva/Pose-Network（Holistic+LSTM） | github.com/rishusiva/Pose-Network | MIT | - | Holistic | - | 参考 |

- **部署结论**：魔塔空间（Gradio + CPU）均可承载；浏览器端 LSTM/Transformer 可转 TF.js/ONNX（LSTM 生态更成熟）
- 未确认项：tasks-vision WebGPU 支持（官方仅 WASM）、内置分类器架构

### 1. 路线 A：landmark 序列 → 轻量时序分类器（agent1 确认主推）
   - A1: ~~Model Maker Gesture Recognizer~~ **已淘汰**（无时序/图片格式/已弃用）
   - A2: **SPOTER 风格 Transformer**（Apache 2.0，小样本友好）或 3 层 LSTM（自研），吃 235d/帧，ONNX/TFJS 导出
   - A3: 骨骼 GCN（ST-GCN 类）——考虑 235d 是手工特征非裸关键点，需评估（待 agent4 确认）
2. **路线 B：开源 SLR 模型微调**（SignBERT+ / Sign Language Transformer 等）
   - 风险：偏重、预训练数据为外国手语/词汇级、许可证（待 agent2/4 回填）
3. **路线 C：纯前端推理**（tfjs / onnxruntime-web / WebGPU）
   - 打分校验：分类置信度 / 原型距离 / 度量学习（待 agent4 回填）

### ✅ Agent 3 结论（魔塔创空间平台，2026-08-09 完成）
- **免费 CPU 实例：2vCPU/16GB**——跑几 MB 轻量 tflite/onnx 绰绰有余（毫秒级推理）
- **部署框架**：Gradio / Streamlit / **Static（静态页面=纯前端）** 三种官方支持
- **三条部署路径（按推荐排序）**：
  - A. **静态页面 + 浏览器端推理**（ONNX Runtime Web / TF.js）：权重随页面托管，无服务器负载、无休眠影响、与现有前端架构一致 → **最推荐**
  - B. Gradio 创空间（Python 后端跑 tflite/onnx）：官方主路径最稳，但自动休眠（约 15 分钟无访问），首访冷启动 1-2 分钟
  - C. xGPU 创空间：免费 GPU 存在但额度说法冲突（A10 300h/月 等存疑），仅需 GPU 时考虑
- **魔搭站内无现成手语识别模型**（外部检索为空）→ 需自训或移植
- **新候选：SLRNet**（arXiv 2506.11154 / github.com/Khushi-739/SLRNet，**Apache-2.0**）：**MediaPipe Holistic 关键点 → LSTM 分类器**，实时 webcam 识别，验证准确率 86.7% ——与我们的技术栈完全一致，最省事的移植候选
- **魔搭有中文手语数据集**：`sorrymaker04/CSL_Dataset`（CSL500 孤立词 125,000 样本含 Kinect 25 点 3D 骨骼，⚠️ 需科研协议限非商业；CE-CSL 连续 5988 段）
- 坑：免费实例自动休眠不可常驻；运行时外网访问说法冲突 → **权重/依赖提前打进仓库**
- 魔搭 action_recognition 旧模型（TSN/SlowFast/ResNet50）均已 404

| 部署路径 | 优点 | 缺点 | 适合 |
|---------|------|------|------|
| Static + 浏览器推理 | 无休眠/无负载/隐私好 | 模型需转 WASM 兼容格式 | **推荐** |
| Gradio 创空间 | 官方主路径稳 | 冷启动慢、休眠 | 服务端校验/大数据量 |
| xGPU | 可跑大模型 | 额度不确定 | 重模型 |

### ✅ Agent 4 结论（浏览器推理生态 + 中文数据，2026-08-09 完成）
**浏览器端推理——完全可行（核心结论）**
- tfjs：webgl/wasm 后端；Keras `.h5`→tfjs-layers（可加载推理）；**不原生跑 tflite**（tfjs-tflite 实验包不成熟）
- onnxruntime-web：WASM（全算子）/WebGL/WebGPU；ONNX 格式为主
- WebGPU 全球 ~85.6%（Chrome/Edge 113+，Safari 26+ 部分，**Firefox 默认关闭**）→ 只做加速，WASM 兜底
- **21 词级模型（1-5MB）浏览器实时可行**：LSTM/MLP 30-60帧×235d 仅千万级 FLOPs，毫秒级；瓶颈在关键点提取（10-30ms/帧）
- 佐证：SLRNet 78ms/帧实时；KD-MSLRT 量化 12.93MB TFLite 仍 SOTA（AAAI 2025）
- 推荐导出路径：Keras→tfjs-layers（`tf.loadLayersModel`）或 PyTorch→ONNX→onnxruntime-web

**SignBERT/SignBERT+ 纠偏**：为中科大 USTC 出品（非北邮）；**官方代码+预训练权重 GitHub 未公开** → "下载即微调"当前不可行（仅非官方复刻 19★ 无权重）

**中文手语数据集**：
| 数据集 | 规模 | 许可 | 可用性 |
|--------|------|------|--------|
| CSL/SLR500（USTC） | 500 词×250=125,000 条，25 关节骨骼 | 研究用途签协议 | 有镜像，harveyfly 仓库给好 mat 数据 |
| CSL-Daily | 20,654 段视频 | 研究用途签协议 | 需申请 |
| wyr0313/SignLanguage | 200 中文词，MediaPipe 双手 126d | **无许可证** | 百度盘，质量未验证 |
| **同格式 MediaPipe 中文词级数据集：无公认公开版** | | | → 自采+增强更务实 |

**MMAction2 骨架模型**（Apache-2.0）：STGCN++ 1.4M / STGCN 3.1M / PoseC3D 2-3.2M 参数，NTU 预训练；但输入 17/25 关节与我们 235d 格式不匹配需改造；CPU 几十~百 ms/clip，**比 LSTM/MLP 慢一个量级** → 不优先

**工业界**（搜狗小聪/百度曦灵/腾讯聆语/华为 ML Kit）：全部商业闭源，无开源识别模型

**新发现**：魔塔有手语合集 `modelscope.cn/collections/shouyu-21f78076ff4f4c` + "基于词生文的手语识别系统"（Foreveryoung，OpenVINO+sherpa-onnx，源码镜像 gitcode.com/modelscope-org/000068 Apache-2.0，JS 渲染未验证明细）

### ✅ Agent 2 结论（开源 SLR 模型，2026-08-09 最后完成）
**总体：开源生态无"开箱即用、可微调、中文词级、关键点输入"的成熟预训练模型；但 HF 有 2 个与我们管线几乎一致的代码/部署模板**

**⭐ HF 关键点模型三件套（最重要发现）**：
| 模型 | 类型 | 输入 | 效果 | 许可证 | 定位 |
|------|------|------|------|--------|------|
| **Seoyoung07/korean-sign-word-classifier-mediapipe** | PyTorch Transformer（空间 2 层+时序 4 层，d_model 256, 4 头） | Holistic [T,115,4] | 2946 韩语词验证 89.62%，有 best.pt | **Other（商用未确认）** | **代码模板价值最高，与管线几乎一致** |
| **gyann/edge-sign-ksl-mediapipe** | ONNX **INT8** 序列分类 | [1,30,959]（Pose25+Face70+双手21 点） | 2771 韩语词，**ONNX Runtime Web 浏览器运行已验证** | MIT | **浏览器部署范式参考**（无训练代码） |
| katyy2000/arabic-sign-language-recognition | 3 层 MLP | 63d 手部点 | 阿拉伯字母+数字 | MIT | 静态手势轻量范式（.tflite 40KB） |

**辟谣**：Google 搜索 AI 摘要给的手语模型（iic/cv_vit_base-... 等 10 个）经 ModelScope API 逐一验证**全部 record not found 不存在**（搜索引擎幻觉；ModelScope 是 SPA，HTTP 200 不代表页面存在）→ 魔塔无已验证手语模型

**其他学术候选**：SPOTER 首选确认（Apache-2.0 代码、CSV 自定义训练）；WLASL Pose-TGCN（C-UDA **禁商用**）；SAM-SLR（**禁商用**）；MSRA SLRT（连续 SLR 重模型）；0aqz0/SLR（CSL，Skeleton+LSTM 84.3%/100 类）；harveyfly Bi-LSTM（无 LICENSE）

**魔塔 xGPU**：免费共享 GPU（动态调度按请求分配），型号/配额未确认 → 新增部署选项（仅需 GPU 时）

**落地建议（agent 2）**：克隆 SPOTER → 235d 写 CSV → `python -m train` 从头训练 21 类（对比 95.6% 基线）→ 数据扩充用魔塔 CSL_Dataset（Apache-2.0）→ 导出 ONNX → 魔塔 Gradio + ONNX Runtime Web 浏览器双轨

### ✅ VL 辅助方案验证（2026-08-09 实测 qwen3-vl-8b @ zhuhai GPU9）
**用户新想法**：用已部署的 qwen3-vl-8b（zhuhai GPU9，vLLM，http://172.28.17.71:8000/v1）训练轻量模型 / 打标签 / 微调 VL。

**实测（/tmp/vl_sign_probe.py）**：
- 输入 `唱歌_f0012_triptych.png`（原帧+骨架+标注三联图）→ VL 识别"唱歌"，打 95 分，理由含"背景文字标注唱歌" ⚠️（可能有文字泄漏）
- 输入 `唱歌_f0012_skeleton.png`（**纯关键点渲染图，无文字**）→ VL 依然识别"唱歌"，打 **85 分**，并描述动作细节（双手胸前、掌心相对、肘部微屈）→ **确认 VL 真在看骨架动作，不是读文字**
- 结论：**VL 可仅凭关键点渲染图判断手语动作并给程度分** → 标注路线成立，且**隐私友好**（骨架图匿名，不需原始视频帧）

**三个子想法的分析结论**：
1. **给数据打标签 ✅ 最可行**：VL 看关键点渲染图/视频帧 → 语义动作存在性 + 程度（0-100）+ 时序区间标注。正好解决 5.4 节"程度标注"最大痛点。成本：930 条 × 5-8 帧 × ~6s ≈ 8-12h（GPU9 后台批量）
2. **知识蒸馏训练轻量模型 ✅**：VL 作教师输出 soft labels → 蒸馏到 LSTM/Transformer 学生模型（学生模型浏览器/魔塔部署）
3. **直接微调 qwen3-vl-8b ❌（违反轻量约束）**：8B BF16 ~16GB，浏览器不可能、魔塔免费创空间 2vCPU/16GB 跑不动（4bit 勉强但极慢）→ 只能作**离线标注/评测服务**，不是用户端打分模型

**待验证**：① 多帧/动作序列判断能力（单帧已验证）② VL 打分 vs 现有系统分数 vs 人工的一致性（20-50 条小样本）③ 谗词"舌头舔"仅原始帧可见（骨架图无舌头），隐私权衡

## 5. 关键决策点

### 5.0 用户核心想法（2026-08-09 用户提出，最高优先级设计约束）
> "每个词汇里面都有对应的语义动作，可能分权重的多个语义动作。关键想让里面**每个语义动作的识别更准确**——判断用户的 landmark 数据是否做到了某个语义、**做到的程度**。有了这个，整体的综合语义准确度打分自然也有了。"

**解读**：打分粒度从"特征组级"（现有 focus_groups 局部评分）升级为**"语义动作级"**：
- 每词 = 多个语义动作（现有 `semantic_process_contracts` / `ordered_sequence` 已有此清单，如花=撮合含苞+向上张开、馋=食指嘴角下滑+舌头微伸）
- 每个语义动作需要：① 是否做到（存在性判定）② 做到的程度（0-1/0-100）
- 综合分 = 各语义动作程度 × 语义权重 加权合成
- 与开源模型调研**天然互补**：轻量时序模型做特征骨干，语义动作做细粒度多头

**对架构的影响（拟设计）**：
```
输入: landmark 序列 (T×235d)  ← 已有管线
  ↓
共享骨干: 轻量时序模型（LSTM/Transformer，如 SPOTER 风格）→ embedding
  ↓
多任务输出头:
  ├─ 词分类头 (21 类)：判别"是不是这个词"（做错别的词 → 直接拒绝）
  ├─ 语义动作头 × N（每词 1-3 个）：
  │    ├─ 存在性：binary（该动作做了没）
  │    └─ 程度：回归/原型距离（做到什么程度）
  └─ (可选) 时序定位：attention 权重 → 动作发生的帧区间（辅助反馈）
综合分 = Σ w_i × 语义动作程度_i（w_i = 语义重要性/判别力权重）
```

**"程度"数据标注策略（无现成标注时的三方案）**：
- a. **教师蒸馏（推荐起步）**：现有 DTW 局部距离（动作相关特征组距离）作为程度软标签 → 训练模型逼近 → 模型学会连续程度
- b. **对比/度量学习**：正样本程度高（接近动作原型），跨词/负样本程度低 → 用 triplet 让 embedding 学会"接近标准动作=程度高"
- c. **人工校准集**：交互学习收集样本 + 专家标程度（小量，修正分布）

**挑战与对策**：
- 动作时序定位无标注 → 先整段级判断，再用 attention 可视化辅助人工标注
- "程度"定义需操作化 → 以"与标准动作原型的距离/关键子动作完整性"定义
- 小样本（每词 ~44 条正样本）→ SPOTER 已证明关键点时序模型小样本可行；语义动作更细，可用数据增强 + 共享骨干

**关键点**：现有 21 词的 `semantic_process_contracts`（ordered_sequence 每阶段 label/detail）和 `focus_groups` 是现成的"语义动作清单+权重"来源，**语义动作标签可以从现有数据自动生成**（正样本=动作都做了），无需重新标注！

**语义动作数量统计（2026-08-09 实测 contracts JSON）**：
- 21 词共 **47 个 ordered_sequence 有序语义动作**：6 词×1 + 8 词×2 + 6 词×3 + 超市×7 = 47
- 另有 **27 个 simultaneous_features**（15 词×1 + 6 词×2 = 27）
- → 语义动作头总数 ≈ **74 个**，但**每词只激活自己的 1-7 个**（稀疏多任务结构，共享骨干，每样本只算本词动作头）
- 样本量：每词正样本 ~44 条（930/21），每个语义动作头的有效样本 = 对应词的正样本数，小样本但可用增强

### 5.1 打分任务建模（核心设计，2026-08-09 我方分析）
开源 SLR 模型多为**分类模型**，而打分=质量评估（0-100）。可选建模方案：

| 方案 | 机制 | 优点 | 缺点 |
|------|------|------|------|
| A. 分类置信度 | softmax 置信度/logits margin → 分数 | 实现简单 | 对"做对了词但略有偏差"不敏感（都在正确类） |
| B. 原型距离 | 用 embedding 层特征，算与每词原型（正样本均值）的距离 → 分数 | 与现有 DTW 模板距离思路同构，但特征是学习到的 | 需定原型更新策略 |
| C. 度量学习 | triplet/contrastive 训练 embedding（同词近异词远），距离 → 分数 | 最灵活，易扩新词 | 训练更复杂，需负样本挖掘 |
| D. 混合（推荐） | embedding 距离作分数主信号 + 分类 logits 作词判定（拒绝其他词） | 既打分又判词，架构复用分类器 | 两路信号需校准 |

**初步推荐**：D 混合方案——骨干（Transformer/LSTM）→ embedding（如 128d）→ 21 词分类头；打分时用 embedding 与类原型余弦/欧氏距离映射 0-100，分类 logits 做"是不是这个词"的硬判定。与现有"模板距离+包络"架构对应，但特征从手工 235d 换成学习 embedding。

- [ ] 打分任务建模：待 agent2/4 结果回来后最终确认（D 混合为主候选）
- [ ] 输入形态：沿用 landmark 序列（隐私友好，浏览器已有管线）vs RGB 视频（模型现成但重+隐私风险）
- [ ] 部署位：纯浏览器 / GitHub Pages + 魔塔 API / 魔塔创空间承载模型推理
- [ ] 是否与现有 DTW 打分并行（新模型先做识别/判别层，打分层复用）

## 6. 待办

- [x] 4 个调研 agent 全部完成并回填
- [x] 正式技术报告完成：`/data/WYC/signLanguage/work/reports/slu_new_scoring_model_research_report_20260809.md`（2026-08-09 06:24 定稿）
- [x] 用户核心想法（语义动作级打分）已融入报告第 5 节推荐方案

## 7. 训练推进日志（2026-08-09 主进程）

### P0 数据准备 ✅
- 脚本：/data/WYC/signLanguage/work/scripts/slu_model_data_prep_v1.py
- 930 条正样本 → X(930,30,235) + mask + y(21词)；训练 user1-7 (771) / 跨人测试 user8-9 (159)
- 输出：/data/WYC/signLanguage/work/generated/slu_model_dataset_v1_20260809/

### P1 骨干训练 ✅（zhuhai GPU0，gen env，torch 2.8）
- 脚本：/data/WYC/signLanguage/work/scripts/slu_model_train_v1.py（--arch lstm|transformer）
- **BiLSTM 1.17M：跨人 test_acc=98.11% / macroF1=97.45%**（early stop ep32）
- **Transformer 2.18M：跨人 test_acc=97.48% / macroF1=96.90%**（early stop ep30）
- 均超 LinearSVC 基线 95.6%！训练 ~15-25s，权重在 zhuhai /home/wuyangcheng/slu_train_20260809/runs/
- ⚠️ 本地 myenv（无 CUDA）跑 torch 会卡死（初始化慢），必须 zhuhai GPU

### VL 标注管线 ✅（v2 prompt 有效）
- 脚本 v1（保守框架）→ v2（正样本程度评估框架）：/data/WYC/signLanguage/work/scripts/vl_action_labeling_v2.py
- v1 问题：14/14 全 exists=false score=0（VL 对存在性判断过严）
- **v2 改善：14 条 word_judgment 全对，overall 50-90（mean 84.3），有区分度**（还发现 u02_r01 左手动作偏差 → 50 分）
- 全量 930 条标注已后台启动（PID 2398141，~72min），输出 /data/WYC/signLanguage/work/generated/vl_action_labels_20260809_v2/

### 资源协调（zhuhai）
- GPU 1 = liuchang MATLAB（避开）；GPU 9 = vLLM qwen3-vl-8b（标注用，不停）
- wan 服务：slu-wan-animate-resident-7907（GPU 0,2,3,4）已停（通知 signL2 后 systemctl --user stop；transient service 已消失）→ GPU 0,2,3,4 空闲
- **7907 被 supervisor 拉回（2026-08-09 07:01）**：源头 = tmux 会话 `gemma`（zhuhai，PID 275434）内循环调用 `zhuhai_resource_limited_service.sh --unit slu-wan-animate-resident-7907` 自动重启（词16 森林生成需要）
- **决策：不与 supervisor 对抗**（强行停会反复被拉起且影响 signL2 的生成任务）→ **P2 训练改用 GPU 9**（VL 标注完成后 vLLM 空闲；P2 模型 1.19M <200MB 显存，够用）
- 7906（GPU 5,6,7,8）仍在跑词11 牛奶生成（signL2 监督中）
- P1 训练用 GPU 0（已完成，权重在 zhuhai runs/）

## 8. 下一步
- [x] P2 语义动作头训练完成：**冻结骨干 corr 0.79-0.81 / MAE 0.059-0.061**（both+frozen+aug 最优 corr 0.81/0.805）
- [x] 两思路对比：**思路1（蒸馏 soft label MSE）有效 corr≈0.79-0.81；思路2（硬标签 BCE）无效 corr≈0.02**；不冻结骨干也无效（corr 0.06）→ 冻结骨干是关键
- [x] contracts 别名修复（谗/馋、汽车（一）/汽车）→ 21 词动作标签全覆盖
- [x] P3 综合评估：词判定 98.11% + 动作综合分 mean 0.85 [0.51-0.99]（21 词全正常）
- [x] **固定词打分场景验收**：做对词 0.837 / 做错词 0.254（conf 门控）；动作头自身不区分本词/他词（已知特性，依赖门控）
- [x] P4 导出：action_model.onnx 4.76MB + word_model.onnx 4.69MB（onnxruntime-web 可跑），torch 一致性 1e-6
- [x] **前端部署完成**：
  - assets/model/：action_model.onnx + word_model.onnx + action_meta.json（47 动作/21 词映射+建议模板）
  - vendor/onnxruntime/：ort.all.min.js + wasm（1.21.0）
  - js/model-scoring.js：训练版特征构建（对齐 build_weighted_holistic_feature_database.py，scale=max(肩宽,躯干)+sparse_core_12 face）+ onnx 推理 + 打分（composite×门控 + 各动作分 + 建议）
  - scoring.js：submitFrames 附加 model_score + finishChallengeScore 渲染模型块；index.html 引用
  - **特征一致性验证**：py=js 逐位一致；词判定 99.7%+；打分合理（谗 77/唱歌 82/花 83/超市 86）
  - 本地服务：http://127.0.0.1:8117/index.html（restart_web.sh 自动递增端口）
- [x] **全 21 词无头浏览器验证**（21/21 成功，init 615ms，打分 8-45ms）；谗 80 分不低；"更像鸡蛋"提示经 test 集验证**无模型偏置**（误判目标全是"船"）
- [x] **鸡蛋专项修复（用户反馈分低）**：
  - 根因：VL 标签系统性保守（鸡蛋 42 条 overall mean 63.5 vs 全量 84.1；"撮合手指表示鸡" 仅 50 分含 0 分）→ 训练目标被压低
  - 修复：手部特写重标注（整身+双手 bbox 放大双图，scripts/slu_vl_relabel_v1.py 通用版）→ 鸡蛋标签 63.5→94.0（+30.6，"撮合手指" 50→94）
  - 重训 v4（冻结骨干 both+aug，v4 标签）→ test_MAE 0.0499
  - **鸡蛋 composite 0.569→0.931 / 花 0.755→0.868 / 虎 0.746（保留旧标签，特写标注反而 -31.9 不采用）**
  - 已部署前端（action_model.onnx v4），服务 http://127.0.0.1:8120/index.html
- [x] **门控缺陷修复（用户反馈公交车 23 分）**：
  - 问题：词判定对用户实时动作误判（判成鸡蛋 conf 1%）→ 门控 0.3+0.7×conf 把动作分压到 23 分（动作 composite 76% 却得 23 分）
  - 诚实结论：composite（动作程度）可靠；**词判定对实时动作（分布偏移）不可靠**（test 集 98.1% ≠ 真实场景）
  - 修复：温和门控 total = composite×(0.7+0.3×conf)——conf→0 时仍有 70% 动作分兜底；词判定仅作诊断提示
  - 验证：误判场景 23→60 分；正常场景 87 分不变；诊断提示保留
- [x] **帧率：还原 10fps 默认**（subagent 验证 10fps 物理足够：晃动主频 0.4Hz < 奈奎斯特 5Hz；提高帧率反而使词判定 conf 下降 + 浏览器负担）→ DEFAULT_CAPTURE_FPS=10，clamp 1-12（3 处配置还原）
- [x] **双监督架构实验（用户提出：词判定头依赖动作头）**：
  - 架构：BiLSTM（冻结）→ 47 动作头 → 动作程度分 concat → MLP(47→128→21) 词判定头；联合 loss = L_action + λ×L_word
  - 脚本：slu_model_actionword_train_v2.py（含 --neg-all 负样本监督）
  - **结果：词判定 92.5%（依赖动作头的 MLP 头）**；对比纯聚合 91.8%、独立分类头 98.1%
  - 权衡：neg-all 负样本让动作头 Spearman 0.8→0.06（他词→0 与 VL 程度分拉扯）→ 打分能力削弱
  - 结论：用户"词判定=动作头函数"设想**验证可行**（92.5%）；优化方向 = 负样本平衡（margin 形式/更低 neg-weight）
  - 注：训练脚本 bug 修复记录（best["mae"] → best_e["mae"]）
- [ ] （待用户决策）双监督调优（margin 负样本）vs 保持线上 v4 独立双头
- [x] **VL 跨词相似软标注实验（用户想法：他词动作≠0，而是相似度软标签）**：
  - v1 全量 47 项评估 → VL 二值化 ✗；v2 自动聚类组 → 真相似组成功（花撮合类 90/20/10）但泛组失败 ✗；v3 模型初筛 → 候选全中失效 ✗；v4 精选组聚焦 → **VL 对同一输入两次评估不稳定（鸡蛋撮合 20 vs 0）** ✗
  - **结论：qwen3-vl-8b 本词动作打分可靠 ✓，跨词相似度判断不可靠 ✗（需更强 VL 或规则化语义先验）→ 该路线暂缓**
  - 保留资产：本词动作 VL 打分（鸡蛋/花校准有效）；精选组（撮合/虚握/移动/晃动）作为语义先验备用
- [x] **异常负例数据飞轮启动**（subagent 开发中）：幅度异常/时序乱序/手部噪声 3 类破坏性增强 → VL 标注低分 → 补充"离谱→低分"监督（当前高质量负例仅 71 条）
- [x] **线上部署（GitHub Pages）**：模型语义动作打分上线公开仓库
  - PR #39（功能上线）：ModelScorer 纯前端打分 + 综合建议聚焦最差动作 + 模型打分升级为主模块（DTW 降级兜底）
  - PR #40（CI 修复）：check_forbidden_files 允许 assets/model/*.onnx 入库（与视频 allowlist 同理）
  - PR #41（README 更新）：打分主路径说明同步
  - GitHub Pages 部署成功（模型/JS/ort 线上 200），CI 全绿
  - 线上地址：https://sign-language-universe.github.io/sign-language-universe/
- [x] 通知 signL2 窗口（打分模块重构 + 上线）
- [x] **v5 负例混合训练完成（数据飞轮闭环）**：
  - 负例 VL 标注全量完成（2790/2790，VL 分数 mean 28.7 vs 正样本 84.1）
  - v5 训练：正 930 + 增强 2313 + 负例 2790 = 6033 样本（冻结骨干 both）
  - **鲁棒性核心提升**：离谱输入（幅度/时序/噪声异常）分数 v4 0.87 → **v5 0.47**（-0.40，"错得越离谱分数越低"达成）
  - 正样本 0.85 → 0.70（严格化，仍显著高于离谱输入；分离度 0.228）
  - 已部署线上（PR #57，action_model.onnx v5）
- [x] **负例分类诊断（2026-08-10，用户指出负例未分类问题）**：
  - 用户观点："幅度变化但核心语义没错应该算对，只是分数低一些" → 检查确认 v1 负例**无分类**：3 类变体（A 幅度/B 乱序/C 噪声）prompt 预设"错误示范普遍低分"，VL 全打 20-40 分，weight=1 等权训练
  - v5 模型五组打分（slu_neg_class_diagnose_v1.py）：正 0.735 / **A_down 缩小0.3x 0.340（用户判断验证：语义保留被误伤最低）** / A_up 放大2.5x 0.452 / **B 乱序 0.706（新发现：真语义错误识别不出，时间平均池化抹掉顺序信息）** / C 噪声 0.328
  - 特征层面：A_down 手形（38d 手内归一化）+双手关系（8d）完全不受全局缩放影响 → 核心语义保留
- [x] **负例分类重标注完成（2026-08-10）**：
  - 冒烟测试（36 条 v1→v2）：**A 类 VL 分级有效**（A_down 28→62.7 / A_up 28→74.7）；**B/C 类 VL 失效**（B 27→70.3、C 31→71.2——VL 看不出乱序/噪声，之前低分只是顺从 prompt）
  - 方案：A 类 930 条 VL v2 分级标签（全量重标注完成，mean 71.8 范围 30-90，0 解析失败）+ B 规则 0.20（顺序错误）+ C 规则 0.40（手形破坏）
  - v6 训练（slu_model_action_train_v2.py，zhuhai GPU0，early stop ep21，test_MAE 0.1474 < v5 0.1678）
  - **评估结果**：A_down 0.340→**0.732**（用户核心诉求修复 ✅）；正样本 0.735→0.719（保持）；**B 乱序仍 0.706**（架构限制：时间平均池化抹顺序，改标签无效）；A_up 0.452→0.707、C 0.328→0.431（分离度下降）
  - **决策：v6 部分达标不部署**（负例拦截回归 v4 问题），详细分析见 reports/neg_class_relabel_experiment_20260810.md
  - 结论：标签需保留"标准>程度不足>语义错误"完整梯度；B 类需顺序敏感架构；树 v3（负例 27.4/AUC 0.955）仍是负例鲁棒性最优
- [x] **语义树结构路线（用户核心设计）**：
  - 语义树 v1.1：12 手形类 → 20 运动类 → 47 叶子（三维度标签人工修正）；文档 semantic_tree_v11_document_20260809.md
  - 与 DTW 加权数据库融合：叶子 → 特征组权重（group_weights 先验）
  - 树模型训练：三层检测器（手形/运动/叶子）+ 一正一反监督 + 层次约束
  - **关键排障**：v1/v2 失败根因=骨干键名不匹配（lstm.* vs backbone.*）未加载（随机骨干 → 输出全 0）；v3 修复后跨人手形 99.4%/运动 98.1%
  - **v3 评估**：正样本 composite 0.765 / 负例 0.274 / 分离度 0.491（vs v5 扁平 0.703/0.474/0.228——树模型负例鲁棒性 2 倍）
  - 部署：tree_model.onnx 4.80MB（三层输出）+ TreeScorer 前端模块 + **双显示（v5 vs 树）** + 细粒度建议（手形/运动层激活诊断）
  - **face 特征 bug 修复**：sparse 12 点 face 被按 468 索引提取（树模型对部分样本手形误判 u08 超市虚握 19%→84%）
  - 已上线（PR #61），徽标 build PR#61
- [ ] （待用户实测）本地/线上双显示比较（v5 vs 树）+ 细粒度建议体验
- [ ] （待推进）魔塔 Static 部署；双监督架构（词判定依赖动作头）；谗词舌头局部特写
- [ ] （待推进）花/虎 VL 标注保守（同款特写重标注）；魔塔 Static 部署；负样本防混淆；action_composite → 0-100 用户分映射标定；谗词舌头局部特写
- [x] **树 v6.3 训练与部署（2026-08-10）**：
  - A 类打分 VL 校准落地（A3）：σ_ok 0.05→0.25、σ_ref 0.45→0.6（过严 100%→16.7%，报告 a3_score_calibration_20260810.md）
  - A 类新分布 low 11/mid 243/high 1606；新正例（≥0.7）A 1466 + C 769 = 2235，分级负例 1485
  - v6.3 训练（v3 脚本，POS_CUTOFF=0.7）：新正例 2234/分级负例 1486，best_leaf_avg 0.0420
  - **评估：正样本 composite 0.867**（v6.2 0.796 +0.071，A 类宽容化+正例扩充效果）；B 乱序 0.371
  - 部署：tree_model_v63.onnx（路径级版本化文件名）+ version v6.3，已通知 signL2 复测
  - 用户实测待反馈（8147 无缓存端口）
- [x] **signL2 树 v6.3 复测 21 词（2026-08-10）**：
  - 管道验证通过：公交车 composite 0.797 ≈ 评估 0.796（gids 口径正确）
  - 树≥70 高分 6 词：汽车 87 / 唱歌 80 / 公交车 80 / 汽车二 74 / 人们 71 / 森林 70
  - 树<5 不合格 6 词（landmark 失败）：朋友 1 / 香蕉 1 / 勇敢 0 / 船 0 / 指示 0 / 烤串 0
  - 分歧词（模板高→树低，手形细节未达树标准）：花 97→30 / 月亮 87→36 / 馋 67→16
  - 词12 finetune 版视觉通过但树 1——模型矛盾，未视为达标
  - 完整报告：reports/wan_model_retest_report_20260810.md
- [x] **词5/16 参考视频人工 pass 部署（2026-08-10，signL2 协调）**：
  - 词5 公交车 word-05-bus-avatar.mp4（033019 版，用户评"完美"）
  - 词16 森林 word-16-forest-avatar.mp4（073930 版，用户评"还不错，最后一点手部细节模糊"）
  - manifest 已加条目（manually_approved，7 词），8147 前端加载验证 200
  - 注：VL 曾判词5/16 手形不通过，用户人工 pass——VL 对手形细节过苛（见 wan-vl-audit-needs-strengthening 记忆）
- [x] **坐姿裁剪增强（signL5 算法开发者，2026-08-10）**：
  - 背景：收集真实样本全坐姿（髋/膝/踝 vis=0），训练站姿 vs 实际坐姿分布差异（用户实测树模型 0 分根因）
  - 生成：13950 条坐姿增强（pos 2790 + neg 11160，每源 3 级 S1/S2/S3，level 各 4650）
  - 遮挡模式：下半身（髋膝踝脚 vis=0 + 坐标漂移出画幅）+ 肘腕部分帧低可见 + 坐姿手位
  - 分级分数：level1 轻 ~85 / level2 中 ~54 / level3 重（更低）
  - 特征：sit_features_v1.npz（13950×30×235，0 失败）
  - 待：训练集成（signL5 推进中）
- [x] **树 v6.4 坐姿增强版训练完成（signL5 算法开发者，2026-08-10）**：
  - 数据：13950 坐姿样本（pos 2790 + neg 11160，S1/S2/S3 三级分级各 4650），遮挡对齐实测（髋膝踝 vis=0 + 漂移出画幅），手形特征 MAE=0.00001
  - 训练：zhuhai A30 GPU0 ~3 分钟，best_leaf_avg=0.0431（站姿语义未退化）
  - **评测（23 坐姿真实样本）**：pos 坐姿响应 +77%（v6.3 0.0221→v6.4 0.0394）；用户实测 0 分样本 pos_超市_20260810_171257 0.010→0.042（4 倍提升）；neg 保持低分 0.026
  - 注：绝对响应仍偏低（坐姿整体响应弱），相对提升显著——坐姿 0 分根因得到针对性修复
  - 报告：reports/slu_sit_augment_experiment_report_20260810.md；TensorBoard http://127.0.0.1:6006
  - 待：v6.4 部署验证（用户回来实测坐姿动作）

## 9. D6.x 级联模型：conf 门控 + 负例训练日志（2026-08-15~16）

### 9.1 版本谱系
- **D6.1**（基线）：930 纯正例（cascade_train_data_v1.npz）→ 现场 holdout MAE 4.92，能区分乱作（conf 门控有效）
- **D6.2**（弃）：全量 auto_score 增强训练 → overall 虚高（乱作 86-87 分）回退
- **D6.3**：930 + 12486 增强混合（cascade_train_data_v2c.npz，含 neg_samples_v2 3720 + 坐姿 2520，三档标签）→ best_mae 0.0270；conf 分离更强但整体打分偏保守
- **D6.4.1**（实验）：930 + 48 现场 neg（A/Ov 全 0）→ 门控分离好但 overall 崩（见 9.3）

### 9.2 conf 门控机制（前端上线 PR#96，2026-08-15）
- conf = 目标词叶子平均激活度（action_head[word_actions[word]].mean()，47 维独立 sigmoid 非 softmax）
- 总分 = overall × min(1, conf/0.5)；conf<0.1 强提示、0.1-0.5 提示折减（中英双语）
- 依据：正例 conf 0.51-0.82 vs 乱作负例 0.003-0.034（间距 >10 倍，0.5 落在无人区）
- 详见系统文档 v2.4 第 9 章

### 9.3 D6.4.1 实验结果（2026-08-16，已完成）
- 数据：cascade_train_data_v641.npz（930 正 + 48 现场 neg，A/Ov 全 0，te 保持 v1 的 159 不变）
- 训练：zhuhai GPU0，freeze backbone，early stop ep86，best_overall_mae=0.0212（数据内 te 比 D6.1 0.0270 好）
- **门控验证（sample_collection 114 样本）**：
  - 乱作 conf 被显式压到 0.003（训练监督生效），th=0.15 拦截 46/48（96%）
  - **但 overall 崩**：正例 mean 0.292（D6.1 0.857）——48 条 Ov=0 标签占 5% 过强；且 5 个"不完美但动作对"（VL 85 分）被错标 0
  - 结论：负例标签必须精细（不能简单全 0）
- 脚本：work/scripts/slu_d641_data_prep_v1.py / slu_export_dual_cascade_onnx_v2.py / slu_d641_gate_verify_v2.py

### 9.4 D6.4.2 VL 精细负例标注（2026-08-16，已完成）
- 方案：渲染 8 帧骨架网格 → qwen3-vl-8b 判定 47 动作头激活度 + 21 词匹配度 + overall（每样本 3 次取均值，全局并发池 24 线程 ≈ 90s/48 条）
- 规则：47 动作头全未激活（max<15）→ overall 强制 0；否则 VL 均值
- 脚本：work/scripts/slu_neg_action_vl_label_v2.py（v1 串行 → v2 全局并发池）；输出 work/generated/neg_action_vl_labels_v1_20260815.json
- **结果（48 条）**：47 条有动作头标注、仅 1 条纯乱作全 0
- **prompt 迭代**：v1"存在性判断"过严（48 条全 0，同 v1 prompt 历史教训）→ v3"描述引导+稀疏输出"（先 motion_description 再只列出现动作头）修复
- 训练配方（计划）：纯乱作 → A 全 0 + Ov=0；部分包含动作头 → A 用 VL 激活度 + Ov 用 VL 分

### 9.5 词级门控豁免 + 镜像修复（2026-08-15~16 上线）
- **词级豁免（PR#101）**：人们（人民）/汽车（二）conf 阈值=0。根因：两词 D6.1 conf 对 pos/neg 无分离度（汽车二 pos 0.006-0.16 vs neg 0.004-0.007 重叠），全局门控误伤正例（1-28 分）→ 豁免后正例恢复 82-87 分；取舍：乱作负例可能虚高
- **镜像取 max 双修复**：
  - PR#105 严格互换：单手镜像不再假变双手（旧逻辑对侧空时保留原位）
  - PR#106 数组兼容：mirrorFlipPoints 用 p.x 但浏览器 landmark 是数组 [x,y,z,vis,pres] → x 全变 1 → 镜像失效；改 Array.isArray 兼容
- **验证**（新录 3 个"跳"正手/反手样本）：正手原 84 分；反手原 0 → 镜像 84 分；max 全 84 对称 ✓

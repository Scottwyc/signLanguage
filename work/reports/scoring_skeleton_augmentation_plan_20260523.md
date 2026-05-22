# 语义骨架模板增强方案

- 更新时间：`2026-05-23 06:08 CST`
- 适用范围：`/data/WYC/signLanguage` 当前 Holistic + 语义加权 DTW 打分 MVP
- 口径：工程增强方案，不是已校准用户评分方案

## 结论

可以基于文档资料定义的核心语义，对标准视频样本的骨架序列做数据增强，再让查询样本与增强模板库做 `best-of` 或 `trimmed-mean` DTW。

当前不建议把外部 3D sign-language generation 模型作为主依赖。MediaPipe Holistic 本身是关键点估计器，不是 3D 动作生成器；它输出的手部 `z` 是以腕部为深度原点的相对深度，适合做小幅 3D 扰动和鲁棒性增强，但不能当作真实手部三维运动模型直接生成新语义动作。

## 可用增强

1. 几何相机增强
   - 轻微 2D 旋转、缩放、平移。
   - 轻微 `x/y/z` 轴视角扰动，用于模拟镜头角度和坐姿/站姿差异。
   - 只应用于当前 profile 中非零权重或 required 的核心组；被 mask 或低权重的脸/躯干不作为主要增强对象。

2. 手部局部增强
   - 手腕为局部原点，给指尖和中间关节添加小幅 jitter。
   - 保持掌根、MCP 基准点更稳定，避免把核心手形语义破坏掉。
   - 对 `花` 重点保护 opening/spread 的方向；对 `跳` 重点保护右手食指/中指与左手地面的相对关系。

3. 左右镜像增强
   - 仅在 profile `allow_hand_swap=True` 时启用。
   - 镜像必须同时交换 left/right hand group，并重算 `two_hand_relation`，否则会破坏 `跳` 的“右手相对左手地面”语义。

4. 时间增强
   - 轻微时间拉伸、压缩、核心动作窗口前后缀裁剪。
   - 不直接比较相邻帧位移幅值，因为这会误伤不同帧率和 subsample；仍以语义相位 DTW 为主。

## DTW 聚合策略

- 默认先用 `best-of`：查询样本分别和标准原始模板及增强模板计算 DTW，取最高分/最低距离。这能最大化容忍合法几何变化。
- 同时记录 `top_k` 结果和最佳模板名，防止某个过宽增强意外吸收错误动作。
- 对线上稳定版可改为 `trimmed-mean`：取 top 3 或 top 5 距离的截尾均值，降低单个增强模板偶然高分的风险。
- `跳`、`朋友`、`汽车` 等双手交互词必须保留 required relation gate：即使 best-of，也不能允许单手样本通过。

## 实施顺序

1. 增加骨架增强函数，输入 `SequenceData + SemanticProfile`，输出受控增强模板列表。
2. 新增离线评估开关：`--template-augmentation best --augmentation-variants N --augmentation-workers K`。
3. 跑 `花/跳` 离线 gate，并复查保存网页样本 replay。
4. 只有当 `花` 真样本提升、`跳` 单手乱摆仍低时，才接入 5080 后端默认路径。

## 外部资料结论

- MediaPipe Holistic 文档：Holistic 输出 pose、face、left/right hand landmarks；手部 landmarks 的 `z` 是以 wrist 为深度原点的相对深度，pose world landmarks 才是以髋部中心为原点的米制 3D 坐标。来源：https://chuoling.github.io/mediapipe/solutions/holistic.html
- MediaPipe Hand Landmarker 文档：当前任务输出 handedness、image landmarks 和 world-coordinate landmarks，定位仍是检测/估计任务，不是动作生成器。来源：https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker
- Sign-language production 方向已有 pose/VAE/diffusion 等生成研究，例如 Diversity-Aware Sign Language Production、MS2SL 等，但这类方法依赖训练数据和生成模型，不适合直接作为当前小样本评分 MVP 的第一依赖。来源：https://arxiv.org/abs/2405.10423 、https://arxiv.org/abs/2407.12842

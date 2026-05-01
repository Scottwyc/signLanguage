# 三层采样架构实验总结

## 结论先行

- 这次把关键帧采样重构成了三层：
  - 候选生成层：只做一次 `Holistic`，输出 raw 结果 JSON 作为缓存
  - 选择策略层：`uniform_select`、`two_stage_select`、`adaptive_select`、`能量覆盖率筛选` 只读同一份缓存做筛选
  - 可视化层：继续独立基于结果文件渲染，不再重复跑 `Holistic`
- 对 `花.mp4` 来说，候选层是唯一的高成本阶段，选择层本身几乎可以忽略，四个策略的选择耗时四舍五入后都是 `0.0s`。
- 因此，这次实验的重点不再是“谁重复跑得更多”，而是“同一份候选缓存上，谁选出来的关键帧覆盖更好”。

## 架构说明

### 1. 候选生成层

- 候选层直接产出 raw `Holistic` 结果 JSON，文件里保留 `records`。
- 后续选择层直接读取这份 JSON，不再重新初始化模型。
- 对短视频，候选层使用全量 dense 候选；对长视频，使用按步长的 dense 候选。
- 这次 `花.mp4` 的候选模式是 `step_dense`，步长为每 `4` 帧采 `1` 帧。

### 2. 选择策略层

- `uniform_select`
- `two_stage_select`
- `adaptive_select`
- `能量覆盖率筛选`

这四种策略现在都只做一件事：

- 从同一份候选 `Holistic` 结果里，按各自规则选出目标数量的关键帧。

### 四种策略的逻辑

- `uniform_select`
  - 在候选缓存上按位置等间距取帧。
  - 目标是保持首尾覆盖、整体分布均匀、实现最简单。
  - 适合把“稳定全覆盖”作为优先级最高的场景。
- `two_stage_select`
  - 先在候选缓存上做一轮较粗的均匀取样。
  - 再根据区间的运动能量和覆盖情况，把剩余预算补到更值得细看的空隙里。
  - 适合既想保留全段覆盖、又希望对高变化区间稍微加密的场景。
- `adaptive_select`
  - 先放入一批 pilot 点。
  - 再递归拆分当前最值得继续加密的区间。
  - 适合动作开始较晚、或者动作密度前后不均匀的视频。
- `能量覆盖率筛选`
  - 先优先看运动能量高的候选，再补双手覆盖更完整的候选。
  - 本质上是把复杂度前移到候选层，再从候选里做偏动态的筛选。
  - 适合更关心动作变化、而不是绝对均匀分布的场景。

### 3. 可视化层

- 可视化只读取已保存的结果文件。
- 不再在可视化阶段重复跑 `Holistic`。

## 实验设置

- 对象视频：`花.mp4`
- 目标采样帧数：`12`
- 候选步长：每 `4` 帧采 `1` 帧
- 短视频阈值：`48` 帧
- 候选缓存文件：`/data/WYC/signLanguage/work/generated/parallel_sampling_strategies_three_layer_run1/candidate_cache/花/花_holistic_results.json`

## 候选层耗时

- 候选层总墙钟耗时：`262.128s`
- 候选层内部 `candidate_generation_sec`：`262.101s`
- 候选帧数：`28`
- 候选层覆盖：
  - 帧覆盖比例：`1.0`
  - 尾部覆盖比例：`1.0`
  - 后半段采样占比：`0.5`
  - 后 75% 采样占比：`0.2857142857142857`
  - 平均运动能量：`3.3024032626833235`

## 指标说明

### 运动能量是什么

- 这里的“运动能量”不是动作质量分数，也不是越大越好。
- 它只是基于相邻采样帧之间人体、双手、面部包围框中心位移得到的代理量。
- 数值越大，说明这组帧之间的变化越明显；数值越小，说明相邻帧更平稳。
- 它更适合用来回答“这组采样有没有覆盖到动作变化”，不适合单独回答“这个采样好不好”。

### 哪些指标更重要

- 如果目标是“全段都要覆盖”，优先看：
  - `frame_span_ratio`
  - `tail_coverage_ratio`
  - `late_half_fraction`
- 如果目标是“晚起始动作也要覆盖到”，优先看：
  - `tail_coverage_ratio`
  - `late_half_fraction`
  - `late_75_fraction`
- 如果目标是“更关注动态变化”，再看：
  - `motion_energy_mean`
  - `motion_energy_max`

### 什么样的结果算更合适

- 对 `uniform_select` 和 `two_stage_select`：
  - 最合适的结果通常是 `frame_span_ratio = 1.0`，`tail_coverage_ratio = 1.0`
  - 如果同时 `late_half_fraction` 和 `late_75_fraction` 不太低，说明它们既稳又不太偏前段
- 对 `adaptive_select`：
  - 如果 `tail_coverage_ratio = 1.0`，同时后半段占比更高，说明它更适合晚动作视频
  - 若前段和后段差异很大，则更像是“偏向动作密集区”的选择
- 对 `能量覆盖率筛选`：
  - 如果 `motion_energy_mean` 高、但 `frame_span_ratio` / `tail_coverage_ratio` 下降，说明它更偏局部动态而不是全局覆盖
  - 这类结果适合把“动作变化捕捉”放在首位的场景，不适合要求首尾都稳的场景

## 选择层耗时

### `uniform_select`

- 选择耗时：`0.0s`
- 选择结果：`0, 8, 20, 28, 40, 48, 60, 68, 80, 88, 100, 106`
- 帧覆盖比例：`1.0`
- 尾部覆盖比例：`1.0`
- 后半段采样占比：`0.5`
- 后 75% 采样占比：`0.3333333333333333`
- 平均运动能量：`1.4046359062194824`

### `two_stage_select`

- 选择耗时：`0.0s`
- 选择结果：`0, 16, 24, 36, 44, 56, 64, 72, 80, 88, 96, 106`
- 帧覆盖比例：`1.0`
- 尾部覆盖比例：`1.0`
- 后半段采样占比：`0.5833333333333334`
- 后 75% 采样占比：`0.3333333333333333`
- 平均运动能量：`2.4736493031183877`

### `adaptive_select`

- 选择耗时：`0.0s`
- 选择结果：`0, 20, 32, 36, 44, 52, 64, 76, 88, 96, 100, 106`
- 帧覆盖比例：`1.0`
- 尾部覆盖比例：`1.0`
- 后半段采样占比：`0.5`
- 后 75% 采样占比：`0.3333333333333333`
- 平均运动能量：`5.111204107602437`

### `能量覆盖率筛选`

- 选择耗时：`0.0s`
- 选择结果：`4, 32, 36, 40, 44, 56, 60, 68, 72, 84, 88, 96`
- 帧覆盖比例：`0.8679245283018868`
- 尾部覆盖比例：`0.9056603773584906`
- 后半段采样占比：`0.5833333333333334`
- 后 75% 采样占比：`0.25`
- 平均运动能量：`6.510766665140788`

## 分析

- 这次三层重构之后，四个策略的时间差异基本消失了。
- 真正的成本集中在候选层，也就是 raw `Holistic` JSON 的一次性生成。
- 因此，后续要比较采样策略优劣，重点应该放在关键帧覆盖而不是时长。
- 如果把“首尾全覆盖”放在第一位，`uniform_select` 和 `two_stage_select` 更稳。
- 如果把“后半段动作捕捉”放在第一位，`adaptive_select` 和 `能量覆盖率筛选` 更积极。
- `能量覆盖率筛选` 这次的平均运动能量最高，但没有覆盖到首帧，属于更偏局部动态的方案。
- `uniform_select` 和 `two_stage_select` 都做到了首尾全覆盖，适合作为稳定基线。
- 从这次 `花.mp4` 的具体数值看：
  - `uniform_select` 的覆盖最均匀，适合作为稳定基线
  - `two_stage_select` 也保持了全覆盖，同时对后半段稍微更积极
  - `adaptive_select` 依然能覆盖首尾，但更强调区间自适应
  - `能量覆盖率筛选` 的运动能量最高，但牺牲了一部分首段完整覆盖
  - 结合下方联系表和时间轴可以看到，`uniform_select` 的帧间距最均匀，`two_stage_select` 更偏后段，`adaptive_select` 的自适应特征更明显，`能量覆盖率筛选` 则更偏高变化区间

## 可视化结果

- 可视化输出目录：`/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals_run2`
- 每个策略都保留了联系表、时间轴和逐帧三联图；这里先放最适合汇报的联系表与时间轴。

### 均匀采样

- 联系表：`/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals_run2/uniform/花/花_contact_sheet.png`
- 时间轴：`/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals_run2/uniform/花/花_timeline.png`

![](/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals_run2/uniform/花/花_contact_sheet.png)

![](/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals_run2/uniform/花/花_timeline.png)

### 两阶段采样

- 联系表：`/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals_run2/two_stage/花/花_contact_sheet.png`
- 时间轴：`/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals_run2/two_stage/花/花_timeline.png`

![](/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals_run2/two_stage/花/花_contact_sheet.png)

![](/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals_run2/two_stage/花/花_timeline.png)

### 自适应采样

- 联系表：`/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals_run2/adaptive/花/花_contact_sheet.png`
- 时间轴：`/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals_run2/adaptive/花/花_timeline.png`

![](/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals_run2/adaptive/花/花_contact_sheet.png)

![](/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals_run2/adaptive/花/花_timeline.png)

### 能量覆盖率筛选

- 联系表：`/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals_run2/dense_uniform_step4_sampling/花/花_contact_sheet.png`
- 时间轴：`/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals_run2/dense_uniform_step4_sampling/花/花_timeline.png`

![](/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals_run2/dense_uniform_step4_sampling/花/花_contact_sheet.png)

![](/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals_run2/dense_uniform_step4_sampling/花/花_timeline.png)

## 进一步思路

- 如果数据压力不大、存储也允许，其实可以直接保留动作开始到结尾的密采样 raw `Holistic` 结果，不必再做关键帧选择这一层压缩。
- 更进一步地，可以把标准样本的密采样 `Holistic` 结果直接存入数据库，作为参考模板库。
- 实时检测时，直接对比“数据库里的标准样本 `Holistic` 时间序列”和“当前视频的密采样 `Holistic` 时间序列”，对整体序列做相似度计算、对齐和匹配，或许就足够了。
- 这样做的好处是：
  - 省掉关键帧选择的设计成本
  - 保留从动作起始到结束的更多原始动作细节
  - 更适合做检索式匹配、模板对比或时序相似度分析
- 这条路线的核心前提是：
  - 标准样本库要足够稳定
  - 相似度度量要能反映动作差异，并且尽量支持时序对齐
  - 存储和离线计算成本要可接受
- 这目前更像下一阶段的系统化方向，和现在的“关键帧选择”路线并不冲突，前者可以看作后者的更直接版本。

## 文件

- 候选层 JSON：`/data/WYC/signLanguage/work/generated/parallel_sampling_strategies_three_layer_run1/candidate_cache/candidate_cache.json`
- 候选层 raw Holistic 缓存：`/data/WYC/signLanguage/work/generated/parallel_sampling_strategies_three_layer_run1/candidate_cache/花/花_holistic_results.json`
- `uniform_select` 输出：`/data/WYC/signLanguage/work/generated/parallel_sampling_strategies_three_layer_run1/uniform/uniform_sampling.json`
- `two_stage_select` 输出：`/data/WYC/signLanguage/work/generated/parallel_sampling_strategies_three_layer_run1/two_stage/two_stage_sampling.json`
- `adaptive_select` 输出：`/data/WYC/signLanguage/work/generated/parallel_sampling_strategies_three_layer_run1/adaptive/adaptive_sampling.json`
- `能量覆盖率筛选` 输出：`/data/WYC/signLanguage/work/generated/parallel_sampling_strategies_three_layer_run1/dense/dense_uniform_step4_sampling.json`
- 新一轮四策略选择输出：`/data/WYC/signLanguage/work/generated/parallel_sampling_strategies_run2/`
- 新一轮四策略可视化输出：`/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals_run2/`

# 手语动作打分当前完整方案工作报告

更新时间：2026-05-22 21:38:59 CST  
项目路径：`/data/WYC/signLanguage`  
报告性质：当前打分 MVP 方案汇总 / demo-only 离线验证总结  

## 1. 摘要

当前手语动作打分方案采用 `MediaPipe Holistic` dense 或 step-dense 时间序列作为主数据表示，以标准动作模板和待测动作序列之间的归一化关键点轨迹相似度作为核心指标。整体流程已经形成一个可复用的离线闭环：

1. 从视频生成 raw `Holistic` JSON 缓存。
2. 从缓存读取 pose、left hand、right hand、face 关键点。
3. 做身体尺度归一化、缺失 mask、分组特征拼接。
4. 用 DTW 做标准序列和待测序列的时序对齐。
5. 计算逐组关键点差异、presence 差异、运动轨迹差异和序列级惩罚。
6. 输出 0-100 的 `prototype_score`、对齐路径、最差对齐点和判别性实验结果。

当前最重要的实验结论是：在 `花` 作为目标动作的场景下，优化后的评分模块已经能把目标动作的合理变体与其他 demo 动作 / 随机假动作明显区分开。最终工程 sanity gate 结果为：

| 指标 | 结果 |
| --- | ---: |
| 目标动作正例最低分 | `75.494` |
| 负例最高分 | `41.495` |
| 分离 margin | `33.999` |
| 工程门控是否通过 | `True` |

需要强调：当前项目还没有真实用户视频流样本，也没有人工评分标签。因此这里的分数只能解释为“离线原型相似度”和“工程 sanity check”，不能解释为正式用户得分、及格线或泛化效果。

## 2. 当前目标与边界

当前阶段目标不是直接推出正式评分标准，而是先验证打分链路是否具备基本判别能力：

- 目标动作自身或合理扰动版本应保持高分。
- 同一目标动作的适度裁剪、降采样、幅度变化不应被过度扣分。
- 其他 demo 词汇动作应明显低分。
- 由目标 demo 生成的反向、乱序、静态保持、随机 landmark、随机游走等假动作应低分。
- 输出结构化诊断，便于后续接入可视化、人工复核和真实用户校准。

当前阶段明确不做以下声明：

- 不声明 `75` 分就是用户合格线。
- 不声明该分数已经和专家评分一致。
- 不声明该方案已经覆盖真实用户、不同设备、不同环境和不同熟练度。
- 不声明单条 demo 模板可以替代正式标准样本库。

## 3. 总体策略

### 3.1 主路线：dense Holistic 时间序列匹配

当前主路线是 dense 或 step-dense raw `Holistic` 时间序列匹配，而不是只看少量关键帧。原因是手语动作包含连续轨迹、手型变化、姿态变化和节奏信息，只用关键帧容易漏掉过渡动作和时间顺序错误。

主流程如下：

```text
视频 / 前端帧流
  -> 常驻 Holistic worker 生成 raw landmark JSON
  -> 标准序列库 / 待测序列缓存
  -> 坐标归一化 + 缺失 mask + 分组特征
  -> DTW 时序对齐
  -> 逐组误差 + 序列级惩罚
  -> prototype_score + 诊断输出
```

关键帧选择仍然保留，但它的定位是压缩展示和诊断解释，例如生成关键帧对比图、最差时间段截图和人工复核材料；它不替代 dense 主评分。

### 3.2 数据层策略：缓存优先，避免重复跑 Holistic

`Holistic` 初始化在当前环境中非常慢，历史基准显示初始化约 `260s`，而单次帧处理远低于初始化耗时。因此当前工程策略是：

- 使用 `/home/wuyangcheng/myenv` 运行 `mediapipe` / `opencv` 相关脚本。
- 优先使用常驻 worker，避免每次评分重新初始化 `Holistic`。
- 候选生成层只负责生成 raw JSON。
- 评分、选择、可视化都读取已落盘 JSON，不重新跑识别。
- 若环境没有 `ffprobe`，帧切片模式使用 OpenCV `CAP_PROP_FRAME_COUNT/FPS` 获取帧数和帧率，避免退化成只采第 0 帧。

本轮已修复该 fallback，相关脚本为：

- `/data/WYC/signLanguage/work/scripts/benchmark_holistic_worker.py`

### 3.3 评分层策略：相似度与质量诊断分离

当前脚本的主输出是 `prototype_score`，代表标准动作和查询动作之间的相对相似度。质量、缺失、动作完整性目前通过 `sequence_penalty`、presence 统计和 warning 形式进入结果；后续应进一步拆成独立的 `confidence_score`，避免把“动作不像”和“摄像头没看清”混成一个黑盒分数。

长期完整评分建议拆成：

| 组件 | 含义 | 当前状态 |
| --- | --- | --- |
| `overall_score` / `prototype_score` | 总体原型相似度 | 已实现 |
| `hand_score` | 左右手轨迹、手型和双手关系 | 已通过左右手 group distance 间接实现 |
| `pose_score` | 肩、肘、腕和躯干姿态 | 已通过 pose group distance 间接实现 |
| `tempo_score` | 节奏、时长、DTW 拉伸程度 | 已通过长度、motion、roughness 等序列惩罚初步实现 |
| `completion_score` | 动作是否完整、是否被截断 | 已通过长度 / 信息量 / endpoint 惩罚初步实现 |
| `confidence_score` | 检测质量、缺失率、归一化可靠性 | 规划中，当前尚未单独输出 |

## 4. 当前实现的评分机制

当前核心脚本：

- `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py`

### 4.1 输入

脚本只读取已生成的 `Holistic` JSON，不重新运行 MediaPipe。当前支持两类输入：

- raw landmark 模式：优先读取 `records[].result_data` 中的 pose、left hand、right hand、face landmark。
- bbox 兼容模式：当旧缓存没有 raw landmark 时退回 bbox 摘要。该模式只用于旧结果诊断，不作为主评分路线。

当前主实验全部采用 raw landmark 模式。

### 4.2 特征构成

当前每帧特征包含：

- pose 核心点：鼻、双肩、双肘、双腕、双髋等 9 个点。
- left hand：21 个手部关键点。
- right hand：21 个手部关键点。
- face 核心点：眼、嘴等少量稳定点。

每一帧都会同时保存：

- `vector`：拼接后的关键点坐标。
- `mask`：每个坐标是否有效。
- `presence`：pose / left hand / right hand / face 是否被检测到。
- `frame_idx` 和 `timestamp_sec`。

### 4.3 坐标归一化

当前以 pose 中的左右肩中点作为身体中心，优先以肩宽作为尺度。如果肩部不可用，则退化到可见 pose 点的空间范围。所有 pose、hand、face 坐标都会减去身体中心并除以身体尺度，从而降低人物大小、距离和分辨率差异对评分的影响。

后续更完整的版本还应加入：

- 动作有效区间的稳健尺度中位数。
- 肩线水平校正。
- 手部局部坐标系，用于更细的手型评分。
- 词汇级左右手规则，例如是否允许左右互换。

### 4.4 帧间距离

每个标准帧和查询帧之间计算分组距离。当前 group 权重为：

| 分组 | 权重 |
| --- | ---: |
| left hand | `0.32` |
| right hand | `0.32` |
| pose | `0.24` |
| face | `0.06` |
| missing | `0.06` |

对 left hand、right hand、pose 组，当前加入了局部幅度缩放鲁棒性：如果查询动作只是整体幅度略小或略大，会尝试在合理范围内做缩放匹配，再加一个很小的缩放惩罚。这是为了让 `amplitude_0.85` 和 `amplitude_1.15` 这类合理目标动作变体保持高分。

### 4.5 DTW 时序对齐

当前使用 DTW baseline 对齐标准序列和查询序列。DTW 的作用是允许不同动作速度之间做单调时间匹配，避免只因为用户稍快或稍慢就直接低分。

DTW 输出：

- `dtw_distance`
- `alignment_path`
- `path_length`
- `group_mean_distance`
- `worst_alignment_points`

DTW 风险是可能过度拉伸来掩盖错误，因此当前又加入序列级惩罚。

### 4.6 序列级惩罚

当前已实现的序列级惩罚包括：

| 惩罚项 | 作用 |
| --- | --- |
| `length_penalty` | 查询序列过短时扣分，防止严重裁剪仍得高分。 |
| `presence_penalty` | 标准和查询之间的手、pose、face 检测出现率差异过大时扣分。 |
| `motion_penalty` | 运动量分布不一致时扣分。 |
| `roughness_penalty` | 轨迹二阶变化不一致时扣分，用于压低乱序和随机动作。 |
| `info_penalty` | 查询帧数太少、信息量不足时扣分。 |
| `endpoint_penalty` | 首尾动作明显不一致时扣分，防止序列看似中间相似但起止错误。 |
| `confidence_warning_penalty` | 标准或查询手部信息极弱时轻度扣分。 |

最终距离为：

```text
normalized_distance = dtw_distance + total_sequence_penalty
```

最终原型分为：

```text
prototype_score = 100 * exp(-normalized_distance / 0.12)
```

这里的 `0.12` 是当前工程 sanity check 的经验尺度，不是正式校准参数。

## 5. 当前实验场景

### 5.1 数据来源

当前实验使用项目已有 demo 视频，目录为：

- `/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/`

当前没有真实用户视频流样本，也没有人工评分标签。

### 5.2 全 demo step-4 raw landmark 缓存

为验证“其他 demo 动作应低分”，已统一生成 10 个 demo 的 step-4 raw landmark 缓存：

- `/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache_v2/`

缓存统计如下：

| demo 词 | step-4 records |
| --- | ---: |
| 唱歌 | `14` |
| 指示 | `16` |
| 月亮 | `24` |
| 朋友 | `15` |
| 汽车 | `23` |
| 花 | `28` |
| 虎 | `29` |
| 谗（羡慕） | `17` |
| 跳 | `10` |
| 香蕉 | `22` |

生成该缓存时使用单个常驻 `Holistic` worker：

| 指标 | 耗时 |
| --- | ---: |
| worker 初始化 | `260.107s` |
| 全流程总耗时 | `274.915s` |

### 5.3 当前目标动作实验

当前完整判别实验以 `花` 为目标动作：

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache_v2/results/花/花_holistic_results.json`
- 结果目录：`/data/WYC/signLanguage/work/generated/scoring_mvp_run2/flower_all_demo_discrimination_v2/`

验证样本包含三类：

1. 目标动作正例变体。
2. 基于目标动作生成的随机假动作。
3. 其他 9 个 demo 词汇动作。

## 6. 判别性验证设计

### 6.1 目标动作正例

正例用于验证“合理目标动作变化仍应高分”：

| 正例变体 | 设计目的 |
| --- | --- |
| `self` | 标准序列自匹配，应接近满分。 |
| `subsample_even` | 降采样，模拟帧率或发送频率降低。 |
| `trim_start_20pct` | 裁掉开头 20%，模拟起始捕获偏晚。 |
| `trim_end_20pct` | 裁掉结尾 20%，模拟结束捕获偏早。 |
| `trim_both_10pct` | 首尾各裁 10%，模拟轻度裁剪。 |
| `amplitude_0.85` | 动作幅度缩小。 |
| `amplitude_1.15` | 动作幅度放大。 |

### 6.2 随机假动作负例

假动作用于验证“形式上来自目标 demo，但动作时序或轨迹不合理时应低分”：

| 假动作 | 设计目的 |
| --- | --- |
| `fake_reverse_time` | 时间反向，检查时序敏感性。 |
| `fake_shuffle_frames` | 帧乱序，检查局部轨迹和 roughness 惩罚。 |
| `fake_static_hold` | 静态保持，检查运动信息缺失。 |
| `fake_random_landmarks` | 随机坐标，检查空间结构错误。 |
| `fake_random_walk` | 随机游走，检查轨迹随机性。 |

### 6.3 其他 demo 负例

其他 demo 动作用于验证“目标动作场景下，其他词汇不应被打高分”。当前使用除 `花` 外的 9 个 demo：

- `唱歌`
- `指示`
- `月亮`
- `朋友`
- `汽车`
- `虎`
- `谗（羡慕）`
- `跳`
- `香蕉`

### 6.4 工程门控

当前门控仅用于评分模块 sanity check：

| 门控项 | 当前临时标准 |
| --- | ---: |
| 目标动作正例最低分 | `>= 75` |
| 负例最高分 | `<= 50` |
| 分离 margin | `>= 15` |

这些值不是用户评分阈值，后续必须用真实用户样本和人工评分重新校准。

## 7. 当前实验结果

### 7.1 正例结果

| case | 分数 |
| --- | ---: |
| `self` | `100.000` |
| `amplitude_1.15` | `94.708` |
| `amplitude_0.85` | `93.874` |
| `trim_end_20pct` | `89.758` |
| `subsample_even` | `88.403` |
| `trim_both_10pct` | `88.129` |
| `trim_start_20pct` | `75.494` |

结论：目标动作的轻度裁剪、降采样和幅度调整仍然保持较高分。`trim_start_20pct` 是正例中最低分，说明开头动作对 `花` 的序列匹配有明显贡献，但仍通过当前正例门控。

### 7.2 随机假动作结果

| case | 分数 |
| --- | ---: |
| `fake_shuffle_frames` | `41.495` |
| `fake_reverse_time` | `33.240` |
| `fake_static_hold` | `15.658` |
| `fake_random_landmarks` | `0.046` |
| `fake_random_walk` | `0.006` |

结论：随机假动作均被压低。最高的是乱序帧 `fake_shuffle_frames`，仍低于负例门控 `50`，说明序列级 roughness / motion / endpoint 惩罚起到了作用。

### 7.3 其他 demo 动作结果

| 其他 demo | 分数 |
| --- | ---: |
| `谗（羡慕）` | `20.562` |
| `朋友` | `14.983` |
| `跳` | `13.692` |
| `唱歌` | `12.944` |
| `汽车` | `11.857` |
| `指示` | `11.543` |
| `香蕉` | `8.295` |
| `月亮` | `6.698` |
| `虎` | `1.766` |

结论：其他 demo 在 `花` 目标动作场景下全部明显低分，最高也只有 `20.562`。这比早期 `花` vs `唱歌` bbox 兼容模式的 `85.837` 明显更合理，说明 raw landmark + DTW + 序列级惩罚是当前正确主线。

### 7.4 门控汇总

| 指标 | 结果 | 临时要求 | 是否满足 |
| --- | ---: | ---: | --- |
| 目标动作正例最低分 | `75.494` | `>= 75` | 是 |
| 负例最高分 | `41.495` | `<= 50` | 是 |
| 分离 margin | `33.999` | `>= 15` | 是 |

## 8. 当前产物清单

### 8.1 核心脚本

- `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py`
- `/data/WYC/signLanguage/work/scripts/benchmark_holistic_worker.py`

### 8.2 实验缓存与结果

- 全 demo step-4 raw landmark 缓存：`/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache_v2/`
- `花` 目标判别性实验：`/data/WYC/signLanguage/work/generated/scoring_mvp_run2/flower_all_demo_discrimination_v2/`
- 结果 JSON：`/data/WYC/signLanguage/work/generated/scoring_mvp_run2/flower_all_demo_discrimination_v2/scoring_mvp_result.json`
- 结果 Markdown：`/data/WYC/signLanguage/work/generated/scoring_mvp_run2/flower_all_demo_discrimination_v2/scoring_mvp_result.md`
- 判别性 CSV：`/data/WYC/signLanguage/work/generated/scoring_mvp_run2/flower_all_demo_discrimination_v2/discrimination_cases.csv`

### 8.3 设计与阶段报告

- 标准采集协议草案：`/data/WYC/signLanguage/work/reports/standard_data_collection_protocol_20260520_draft.md`
- 评分机制设计草案：`/data/WYC/signLanguage/work/reports/scoring_mechanism_design_20260520_draft.md`
- 初始实验报告：`/data/WYC/signLanguage/work/reports/scoring_mvp_initial_experiment_20260520.md`
- 判别性优化报告：`/data/WYC/signLanguage/work/reports/scoring_mvp_discrimination_optimization_20260520.md`
- 当前完整方案汇总：`/data/WYC/signLanguage/work/reports/scoring_scheme_current_report_20260522.md`

## 9. 当前方案的工程可用性判断

当前方案已经具备以下能力：

- 可以从已有 raw `Holistic` JSON 直接完成离线打分，不重复运行 MediaPipe。
- 可以识别目标动作自身、降采样、裁剪、幅度变化等合理变体。
- 可以压低其他 demo 动作和随机假动作。
- 可以输出 DTW path、分组平均距离、最差对齐点和 sequence penalty。
- 可以作为后续前端视频流打分和标准样本库建设的算法雏形。

当前方案尚不具备以下能力：

- 不能输出已校准的真实用户分数。
- 不能定义正式合格线或等级线。
- 尚未支持多模板标准库匹配。
- 尚未单独输出 `confidence_score`。
- 尚未自动生成 DTW 对齐图、逐组误差曲线和关键帧诊断图。
- 尚未覆盖所有 demo 词作为目标动作的逐词判别性验证。
- 尚未处理词汇级规则，例如左右手是否可交换、表情是否重要、某只手是否为非参与手。

## 10. 后续工作建议

优先级 1：

- 将当前判别性套件推广到其他 9 个 demo 词，逐词验证每个目标动作是否也能满足“目标变体高分、其他动作低分、假动作低分”。
- 在 `score_holistic_sequence_mvp.py` 中显式输出 `confidence_score`，把检测覆盖率、归一化可靠性和动作完整性从动作相似度中拆出来。
- 增加 demo seed manifest，标清每条 demo 当前是临时标准模板、负例样本还是调试样本。

优先级 2：

- 增加多模板匹配：每个词允许多个标准样本，打分时取最近模板或模板簇距离。
- 生成 DTW 对齐路径图、逐组误差时间线、最差片段 contact sheet 和关键帧对比图。
- 加入动作起止标注后，尝试分段 DTW，防止全局 DTW 过度拉伸。

优先级 3：

- 按标准采集协议补充真实用户样本。
- 引入专家人工评分或通过/不通过标签。
- 用真实用户数据重新校准分数尺度、组件权重、词汇级阈值和 UI 解释口径。

## 11. 结论

当前打分方案已经从早期 bbox / 稀疏对比升级为 raw landmark dense 时间序列匹配，并通过 `花` 目标动作的 demo-only 判别性实验验证了基本方向：目标动作合理变体保持高分，其他 demo 和随机假动作显著低分。

下一阶段的关键不是继续调整单个分数阈值，而是扩大验证面和补齐真实数据：先把同一判别性套件推广到所有 demo 词，再建立多模板标准库、置信度输出和可视化诊断；最后用真实用户样本和人工评分完成正式校准。

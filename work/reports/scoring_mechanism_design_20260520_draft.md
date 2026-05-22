# 手语打分 MVP 第一版评分机制设计草案

更新时间：2026-05-20 17:30:00 CST  
适用项目：`/data/WYC/signLanguage`  
输出性质：方法设计草案 / 原型指标说明，不是已校准评分标准。

## 1. 定位与边界

本草案设计第一版手语动作打分机制，用于后续离线原型和 MVP 验证。当前阶段没有真实用户视频流样本，也没有人工评分标签，因此所有分数只能称为“原型相似度”或“流程 sanity check 指标”。本阶段不得声明真实用户打分准确、不得给出已验证的及格线、不得把 0-100 分解释为已校准等级。

第一版主路线采用 dense 或 step-dense `MediaPipe Holistic` 时间序列匹配：标准样本与待测样本都先生成并保存原始 `Holistic` JSON，再在缓存上做归一化、时序对齐、逐关节误差和诊断输出。关键帧打分只作为压缩版或诊断支线，用于降低展示成本、解释差异位置，不能替代 dense 主线。

现有工程已经拆分为候选生成、选择策略和可视化三层。评分模块应继续遵守该边界：

- 候选生成层：负责从视频得到 dense / step-dense `Holistic` JSON 缓存。
- 选择层：从缓存中选关键帧，不重新跑 `Holistic`。
- 评分层：读取缓存中的 `result_data`、帧号、时间戳、可见性和 presence 信息，完成对齐和误差计算。
- 可视化层：读取缓存和评分输出生成图，不重新跑 `Holistic`。

## 2. 输入与基本数据结构

建议第一版评分输入包括两类序列：

- 标准模板序列 `template_sequence`：来自标准样本视频的 dense 或 step-dense `Holistic` JSON。
- 待测序列 `candidate_sequence`：来自用户或伪用户样本的 dense 或 step-dense `Holistic` JSON。

每帧至少需要保留：

- `frame_idx`：原视频帧号。
- `timestamp_sec`：时间戳。
- `result_data.pose_landmarks`：姿态关键点。
- `result_data.left_hand_landmarks`：左手关键点。
- `result_data.right_hand_landmarks`：右手关键点。
- `result_data.face_landmarks`：面部关键点。
- `row.pose_present / left_hand_present / right_hand_present / face_present`：当前帧检测状态。
- `row.*.visibility_mean` 与 bbox 摘要：用于质量诊断。
- 视频元信息：`fps`、`total_frames`、分辨率、是否镜像、采样步长、动作起止标注版本。

第一版不要求实时流式评分，优先做离线批处理。后续接入前端时，可以把相同机制拆成滑窗对齐和增量诊断。

## 3. 预处理设计

### 3.1 坐标统一

`Holistic` 原始坐标通常是图像归一化坐标 `x/y` 和相对深度 `z`。评分前统一转换为身体坐标系，避免不同视频分辨率、人物大小和相机距离直接影响距离。

建议流程：

1. 读取每帧 pose、hand、face 原始 landmark。
2. 以身体中心作为原点。优先使用左右肩中点；若肩不可用，使用左右髋中点；再退化到 pose bbox 中心。
3. 以稳健身体尺度归一化。优先使用整段视频的肩宽中位数；肩宽不可用时使用肩-髋高度中位数；再退化到 pose bbox 对角线中位数。
4. 可选做肩线水平校正。左右肩都稳定可见时，将肩线旋转到水平，以消除轻微相机倾斜；如果肩线不稳定则不旋转，避免引入抖动。
5. `z` 坐标按同一身体尺度缩放，但第一版权重低于 `x/y`，因为单目深度噪声较大。

尺度不要逐帧单独估计后立即使用，否则会把 pose 抖动引入手部轨迹。建议使用整段或动作有效区间的中位尺度，并对异常尺度做上下限裁剪。

### 3.2 局部手型归一化

手部动作同时包含“手在身体前的位置”和“手指形状”。第一版应拆成两类误差：

- 全局手部位置：手腕、掌心、指尖相对身体坐标的位置，使用身体尺度归一化。
- 局部手型：以手腕或掌心为局部原点，以掌宽或腕到中指 MCP 距离为局部尺度，比较手指骨架形状和方向。

这样可以避免大臂位置错误被手型分数吞掉，也避免人物体型差异把手型距离放大。

### 3.3 左右手处理

默认采用严格左右手匹配：标准左手对待测左手，标准右手对待测右手。手语词汇中左右方向、主辅手关系可能有语义，因此第一版不应自动用“左右交换后误差更小”来给高分。

需要在元数据中显式记录：

- `camera_mirror`：视频是否自拍镜像或已经水平翻转。
- `dominant_hand`：标准动作是否有主手要求。
- `allow_handedness_swap`：某个词汇未来是否允许左右手互换。

MVP 默认策略：

- 如果元数据说明视频是镜像，则先统一反镜像映射，再进入评分。
- 如果标准模板某手持续出现而待测同侧手缺失，计入完成度和对应手部误差。
- 如果标准模板只有一只手参与而待测多出另一只手，先不直接判错，但记录“额外手部运动”诊断；未来由词汇级规则决定是否扣分。
- 只有当词汇元数据明确允许左右互换时，才启用左右交换对齐的候选分支。

### 3.4 可见性、缺失点与插值

缺失处理要把“动作没做”和“模型没检测到”分开。建议保留三类 mask：

- `template_visible[g, j, t]`：标准模板在时间 `t` 的组 `g`、关节 `j` 是否可用。
- `candidate_visible[g, j, u]`：待测样本对应点是否可用。
- `joint_weight[g, j, t]`：该点在该帧的有效权重，结合 visibility、presence 和词汇权重。

判断规则：

- pose：优先使用 landmark `visibility`，低于阈值的点降权或视为缺失。
- hands：MediaPipe 手部 landmark 通常没有稳定 visibility，使用 `left_hand_present/right_hand_present`、landmark 数量、手部 bbox 合理性和相邻帧连续性判断。
- face：FaceMesh 的 visibility 可能不可用或不可靠，第一版主要使用 face presence 和少量稳定区域，不把面部作为高权重扣分项。

插值策略：

- 1 到 2 个采样点的短缺口可线性插值，仅用于平滑轨迹和帮助 DTW 计算。
- 长缺口不插值成真实动作，直接保留缺失 mask，并在 completion/confidence 中扣减。
- 标准模板缺失点不参与误差主项，但会产生“标准模板质量不足”警告。
- 待测样本在标准模板可见位置缺失时，计入完成度扣分和对应组缺失警告。
- 双方都缺失时不贡献动作误差，但降低该时间段的信息量和置信度。

### 3.5 平滑与异常值

建议对归一化后的关键点做轻量平滑：

- 对每个关键点的连续可见片段做中值滤波或一阶低通。
- 对单帧跳变大、前后帧又恢复的点标记为 tracking spike，降低权重。
- 不对动作峰值强行抹平，手语中的快速转折可能正是有效动作。

## 4. 时序对齐设计

评分前需要把标准模板时间轴 `t` 和待测时间轴 `u` 对齐。第一版同时保留三种方式，但用途不同。

### 4.1 帧间代价函数

DTW 和分段对齐都需要帧间代价。建议代价由多个组组成：

```text
cost(t, u) = sum_g weight_g * robust_distance(feature_g(template[t]), feature_g(candidate[u]))
             + missing_penalty(t, u)
```

其中 `g` 包括右手、左手、双手关系、手腕轨迹、肘肩姿态、躯干和面部低权重项。距离使用 Huber 或裁剪均值，避免个别手指点飘移主导整帧。缺失惩罚只在标准可见、待测缺失时较高；标准缺失时主要转为模板质量警告。

### 4.2 DTW baseline

DTW 是第一版主基线。它适合当前缺少动作起止精确标注、用户速度可能不同的情况。

建议设置：

- 单调路径：时间只能向前，不允许回退。
- 边界约束：首尾尽量覆盖动作有效区间，允许少量准备段/收尾段跳过。
- 带宽约束：使用 Sakoe-Chiba band 或类似窗口，初始可设为较短序列长度的 15%-25%，避免路径过度扭曲。
- 步长约束：限制连续水平/垂直移动次数，避免一个标准帧匹配过多用户帧。
- 输出完整 path，用于后续节奏和差异定位。

适用场景：

- 第一版离线原型默认使用。
- 标准样本和待测样本都是 dense / step-dense 序列。
- 动作较短、阶段不复杂，或者还没有可靠关键帧锚点。

风险：

- 复杂多阶段动作中，DTW 可能用过度拉伸掩盖顺序或节奏错误。
- 如果一段关键动作缺失，DTW 可能绕开缺失段而让总分偏高。

因此 DTW 分数必须配合 completion、路径斜率异常和最差时间段诊断一起看。

### 4.3 分段 DTW

分段 DTW 在动作被拆成多个阶段后分别对齐，防止全局 DTW 把不同阶段互相错配。

阶段来源可以按优先级使用：

1. 人工动作起止和阶段标注：未来标准采集阶段应补充。
2. 标准模板能量曲线：手腕、掌心和指尖速度峰值、停顿点、方向变化点。
3. 关键帧锚点：由已有选择策略得到的关键动作帧。
4. 均匀分段：没有更好信息时作为兜底，仅用于实验。

适用场景：

- 词汇动作包含明显准备、主动作、收尾，或多个连续子动作。
- 需要单独诊断“哪一段做错”。
- 全局 DTW path 出现长水平/垂直平台、异常折返式压缩或阶段错配。

输出应包含每段的局部分数、局部缺失率、局部节奏偏差和最差帧范围。第一版可以先把分段 DTW作为诊断增强，不强制替代全局 DTW 总分。

### 4.4 关键帧锚点对齐

关键帧锚点对齐是压缩/诊断支线。它读取 dense 缓存后选出的关键帧，不重新跑 `Holistic`。

基本做法：

- 标准模板选出 `K` 个关键帧或阶段锚点。
- 待测序列在同一阶段内寻找最相近帧，或用 DTW path 反查对应帧。
- 输出锚点级误差、关键帧对比图和动作阶段提示。

适用场景：

- 前端或报告需要展示少量可解释帧。
- 存储或计算受限，需要先用关键帧快速诊断。
- dense DTW 已经完成，需要从 path 中抽取代表性错误帧。

限制：

- 关键帧可能漏掉过渡动作、节奏问题和短时手型错误。
- 不应作为第一版唯一评分路线。

## 5. 逐关节与分组误差

第一版评分应先计算细粒度误差，再汇总成组件分。这样即使总分不校准，也能给出有用诊断。

### 5.1 手部误差

手部是主权重。建议拆成：

- 手腕/掌心轨迹误差：手在身体坐标中的位置是否正确。
- 指尖轨迹误差：拇指、食指、中指、无名指、小指尖位置是否正确。
- 手型局部误差：局部坐标下 21 个手部点的距离。
- 骨向量/关节角误差：相邻骨段方向是否接近，减少手大小差异影响。
- 双手关系误差：左右手掌心距离、相对上下左右位置、是否接触或接近。

手部总误差可记录为：

```text
E_hand = w_pos * E_palm_trajectory
       + w_shape * E_local_shape
       + w_angle * E_bone_direction
       + w_relation * E_two_hand_relation
       + w_missing * missing_hand_penalty
```

如果模板某一侧手长期不存在，该侧不进入主动作误差，但待测样本出现持续额外运动时输出警告。

### 5.2 手腕误差

手腕连接手部和手臂，是最重要的动作轨迹点之一。建议同时使用：

- hand landmark 的 wrist 点：手部检测成功时精度更适合手型。
- pose landmark 的 wrist 点：手部缺失时作为弱替代。

当两者同时存在但相差过大时，记录 tracking inconsistency。手腕误差应参与手部动作分，也参与肘肩姿态分。

### 5.3 肘、肩与上肢姿态误差

上肢姿态主要反映动作方向、手臂伸展和身体前空间位置。建议使用 pose landmark：左右肩、左右肘、左右腕。

指标：

- 肩-肘、肘-腕骨向量方向差。
- 肩-肘-腕夹角差。
- 手腕相对肩线的位置。
- 左右肩线稳定性和身体转动提示。

该组权重低于手部，但对“手的位置对、手型对，但手臂姿势明显不对”的场景很关键。

### 5.4 躯干误差

躯干用于归一化和姿态稳定诊断，通常不应高权重扣分。建议指标：

- 肩线角度差。
- 躯干中心偏移。
- 肩-髋方向或上身倾斜差。
- 身体尺度和 bbox 稳定性。

如果躯干剧烈偏移，更多解释为拍摄条件或站位问题，进入 posture 和 confidence，而不是直接当作手语动作错误。

### 5.5 面部误差

当前 demo 和第一版数据未必有可靠的表情标注。面部建议低权重、诊断优先：

- face presence：面部是否持续可见。
- 头部朝向近似：鼻尖、眼角、脸部 bbox 中心。
- 嘴部开合或少量口型点：仅在词汇元数据标记“表情/口型重要”时提高权重。

未标注表情要求前，不应因为 face mesh 噪声给动作主分大幅扣分。

## 6. 组件分设计

所有分数命名必须带 `prototype` 或在报告中明确“未校准”。建议输出 0-100 的相对分只是为了可读性，不代表真实考试分。

### 6.1 误差到原型分的转换

建议每个组件先输出原始误差，再输出原型相似度：

```text
score_component_prototype = 100 * exp(- E_component / tau_component)
```

`tau_component` 第一版可以使用固定经验值或标准样本自扰动实验估计；未来必须用真实用户样本和人工标签校准。报告中必须同时保留 `E_component`，避免只看一个伪校准分。

### 6.2 总分

第一版建议总分是组件加权和：

```text
total_score_prototype =
    0.45 * hand_action_score_prototype
  + 0.20 * posture_score_prototype
  + 0.15 * rhythm_tempo_score_prototype
  + 0.20 * completion_confidence_score_prototype
```

初始权重说明：

- 手部动作 45%：手语动作的主体，含手型、手部轨迹和双手关系。
- 姿态 20%：上肢和躯干辅助动作，避免只看手指。
- 节奏/速度 15%：反映动作快慢、阶段时长和 DTW 形变。
- 完成度/置信度 20%：反映是否拍全、关键点是否足够、动作是否被可靠观察。

未来有标签后，应按词汇和任务目标重新学习或校准权重。对于高度依赖表情的词汇，可加入 face/expression 子权重；对于单手词汇，可降低非参与手权重。

### 6.3 手部动作分

组成：

- 主手轨迹相似度。
- 辅助手轨迹相似度。
- 手型局部相似度。
- 指尖/骨向量相似度。
- 双手相对关系。
- 手部缺失惩罚。

输出字段建议：

- `hand_action_score_prototype`
- `left_hand_score_prototype`
- `right_hand_score_prototype`
- `hand_shape_error_mean`
- `palm_trajectory_error_mean`
- `two_hand_relation_error_mean`
- `hand_missing_rate_template`
- `hand_missing_rate_candidate`

### 6.4 姿态分

组成：

- 肩、肘、腕方向和角度。
- 手腕相对肩线位置。
- 躯干中心和肩线倾斜。
- pose visibility 和稳定性。

输出字段建议：

- `posture_score_prototype`
- `arm_angle_error_mean`
- `wrist_pose_error_mean`
- `shoulder_line_error_mean`
- `torso_stability_warning`

### 6.5 节奏/速度分

节奏不等于动作相似度。它从对齐 path 中计算：

- 总时长比：待测动作有效时长 / 模板动作有效时长。
- 分段时长比：各阶段是否过快或过慢。
- DTW path 斜率：是否存在长时间停顿、跳过或过度拉伸。
- 速度曲线相似度：手腕/掌心速度峰值位置是否接近。

输出字段建议：

- `rhythm_tempo_score_prototype`
- `duration_ratio`
- `phase_duration_ratios`
- `dtw_warping_amount`
- `long_pause_ranges`
- `skipped_motion_ranges`

### 6.6 完成度/置信度分

完成度/置信度不是动作正确性本身，而是“这次结果是否足够可信”。建议由以下因素组成：

- 动作有效区间是否覆盖标准模板的主要阶段。
- 标准需要出现的手是否在待测样本中持续可见。
- pose 是否足够稳定可用于归一化。
- 关键帧/关键阶段是否有对应观测。
- DTW path 是否覆盖完整，是否出现异常压缩。
- 模板自身是否存在严重缺失。

输出字段建议：

- `completion_confidence_score_prototype`
- `candidate_observed_ratio`
- `template_quality_score`
- `required_hand_coverage`
- `normalization_confidence`
- `alignment_confidence`
- `warnings`

如果置信度低，UI 或报告应提示“本次结果不适合解释为动作水平”，而不是简单显示低分。

## 7. 诊断输出设计

第一版的价值不只在总分，而在定位“哪里不像、哪个部位不像、是否因为看不清”。建议输出结构化 JSON 和可视化文件。

### 7.1 最差时间范围

从 DTW path 或分段 DTW 中聚合滑窗代价，输出前 N 个最差范围：

- `template_start_frame / template_end_frame`
- `candidate_start_frame / candidate_end_frame`
- `template_time_sec / candidate_time_sec`
- `dominant_error_groups`
- `error_mean / error_p95`
- `missing_rate`
- `reason_tags`：如 `hand_shape_mismatch`、`right_hand_missing`、`tempo_too_fast`、`alignment_warped`

窗口长度可先设置为 0.3-0.8 秒或 5-15 个采样点，后续按词汇时长调整。

### 7.2 最差关节组与关节

输出组级排序：

- 右手局部手型。
- 左手局部手型。
- 右手腕轨迹。
- 左手腕轨迹。
- 双手相对关系。
- 肘肩姿态。
- 躯干稳定。
- 面部/头部可见性。

每组保留：

- `mean_error`
- `p95_error`
- `visible_pair_count`
- `candidate_missing_rate_when_template_visible`
- `template_missing_rate`
- `example_frames`

对手部可进一步列出指尖或骨段，例如拇指、食指、中指、无名指、小指、掌心。

### 7.3 缺失数据警告

建议标准化 warning code：

- `candidate_right_hand_missing_high`：待测右手缺失率过高。
- `candidate_left_hand_missing_high`：待测左手缺失率过高。
- `template_hand_missing_high`：标准模板手部缺失率过高，模板质量不足。
- `pose_visibility_low`：pose 可见性低，归一化不可靠。
- `face_not_visible`：面部不可见，仅作低权重提示。
- `normalization_scale_unstable`：肩宽或躯干尺度抖动过大。
- `camera_mirror_unknown`：镜像状态未知，左右手解释可能不可靠。
- `alignment_path_degenerate`：DTW path 过度水平/垂直，节奏解释不可靠。
- `action_incomplete`：动作有效区间疑似被截断。

warning 不等于扣分项本身。它们用于解释为什么本次原型分不可靠，或为什么某一组件变低。

### 7.4 可视化产物

可视化应读取已有视频帧和缓存的 `Holistic` JSON，不重新执行识别。建议产物：

- `alignment_path.png`：DTW path 热图，显示标准时间轴与待测时间轴映射。
- `group_error_timeline.png`：按时间显示手部、姿态、节奏和缺失代价。
- `joint_error_heatmap.png`：关节/关节组对时间的误差热力图。
- `worst_ranges_contact_sheet.png`：最差时间段的标准/待测同步对比图。
- `keyframe_anchor_compare.png`：关键帧锚点对比图，作为报告摘要。
- `normalized_skeleton_overlay.png`：归一化后骨架叠加，用于检查尺度和左右映射。
- `score_breakdown.json`：完整结构化评分和诊断。
- `score_report.md`：面向人工检查的简版中文报告。

## 8. 输出 JSON 草案

第一版评分输出可以采用如下结构：

```json
{
  "schema_version": "scoring_prototype_v0.1",
  "generated_at": "2026-05-20T17:30:00+08:00",
  "claim_level": "prototype_similarity_not_calibrated",
  "template": {
    "word": "花",
    "source_json": ".../candidate_cache/花/花_holistic_results.json",
    "fps": 29.45,
    "sample_step": 4,
    "quality_warnings": []
  },
  "candidate": {
    "source_json": "...",
    "fps": 29.45,
    "sample_step": 4,
    "quality_warnings": []
  },
  "alignment": {
    "method": "dtw_baseline",
    "path_length": 0,
    "warping_amount": 0.0,
    "alignment_confidence": 0.0
  },
  "scores": {
    "total_score_prototype": 0.0,
    "hand_action_score_prototype": 0.0,
    "posture_score_prototype": 0.0,
    "rhythm_tempo_score_prototype": 0.0,
    "completion_confidence_score_prototype": 0.0
  },
  "errors": {
    "hand_shape_error_mean": 0.0,
    "palm_trajectory_error_mean": 0.0,
    "arm_angle_error_mean": 0.0,
    "duration_ratio": 1.0
  },
  "diagnostics": {
    "worst_time_ranges": [],
    "worst_joint_groups": [],
    "missing_data_warnings": [],
    "visualization_files": []
  }
}
```

注意：示例中的 0 值只是 schema 占位，不代表真实结果。

## 9. 第一版离线验证口径

在没有真实用户样本和人工标签前，建议只做以下 sanity check：

- 同一视频自匹配：应该得到最低误差和最高原型相似度。
- 同一视频降采样/轻微噪声/时间缩放：应该仍然相近，同时 rhythm 或局部误差能反映扰动。
- 同一视频截断：completion/confidence 应明显下降，并输出动作不完整警告。
- 不同词汇互匹配：多数情况下应比自匹配和轻扰动更差，并能定位手部轨迹或手型差异。
- 手部遮挡模拟：hand missing warning 和完成度应下降，而不是静默给高分。

这些测试只能证明流程和诊断方向是否合理，不能证明真实用户评分有效。

## 10. 后续校准需求

进入正式评分前必须补齐：

- 每个词汇多条标准模板，覆盖不同标准示范者和自然速度变化。
- 真实用户样本，包含初学者、熟练者、不同身高体型、不同拍摄设备。
- 人工评分或专家分项标签，至少覆盖手型、位置、姿态、节奏和完成度。
- 动作起止和阶段标注，用于分段 DTW 与节奏校准。
- 词汇级元数据：单手/双手、主手、是否允许左右互换、表情/口型是否重要、关键阶段权重。

校准后才能确定：

- 组件权重是否合理。
- `tau_component` 如何取值。
- 0-100 分与人工评分的关系。
- 及格线、等级线或学习建议是否可信。
- 不同词汇是否需要不同阈值。

## 11. 建议实现顺序

1. 实现缓存读取和预处理模块，输入现有 dense / step-dense `Holistic` JSON，输出归一化序列和可见性 mask。
2. 实现 DTW baseline，对齐后输出 path、原始误差和基础组件分。
3. 实现诊断 JSON：最差时间段、最差关节组、缺失警告。
4. 接入现有可视化缓存，生成 DTW path、误差时间线和关键帧对比图。
5. 用 demo 视频做自匹配、扰动、截断和不同词汇负例 sanity check。
6. 再加入分段 DTW 和关键帧锚点对齐，作为诊断增强。
7. 等真实用户样本和人工标签可用后，再做权重、阈值和评分等级校准。

## 12. 本草案的关键结论

- 第一版评分主线应是 dense `Holistic` 时间序列匹配，关键帧路线只做压缩和诊断。
- 评分前必须做身体尺度归一化、左右手元数据处理和缺失 mask，否则距离没有可比性。
- DTW baseline 可以先跑通 MVP，但必须配合完成度、路径异常和最差区间诊断，避免过度对齐掩盖错误。
- 总分只能是 prototype similarity，不是已校准 pass/fail 分数。
- 诊断输出应优先服务人工检查：指出最差时间段、最差关节组、缺失原因和可视化证据。

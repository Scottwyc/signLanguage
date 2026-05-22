# 手语评分 MVP 标准数据采集协议草案

更新时间：2026-05-20 17:20:00 CST

## 1. 文档定位

本协议用于 `/data/WYC/signLanguage` 手语动作评分 MVP 的第一阶段数据建设，目标是让后续采集到的标准样本、练习/用户样本和验证样本能够被稳定处理、复现质控、进入 dense `MediaPipe Holistic` 时间序列匹配流程。

当前项目尚无真实用户视频流样本和人工评分标签，因此本文档只定义采集、存储、质控和版本管理规范。本文中的阈值均为**临时草案值**，只能作为采集质控起点，不能作为正式评分合格线、用户能力判断或泛化效果证明。

## 2. 数据类型与每词样本量建议

### 2.1 标准样本

标准样本用于建立每个词的动作模板库，后续 dense `Holistic` 序列匹配和关键帧诊断都以它为参照。

| 阶段 | 每词最低可启动量 | 每词推荐量 | 说明 |
| --- | ---: | ---: | --- |
| 单人临时模板 | 1 名标准示范者 x 8-10 次合格重复 | 不建议长期使用 | 仅用于流程调试和 demo sanity check，不用于校准用户分数。 |
| MVP 标准库最低线 | 2 名标准示范者 x 3 次合格重复 = 6 条 | 3 名标准示范者 x 5 次合格重复 = 15 条 | 可建立初版多模板参照，仍需谨慎解释评分。 |
| 稳定标准库 | 5 名标准示范者 x 5 次合格重复 = 25 条 | 5-8 名标准示范者 x 5 次合格重复 = 25-40 条 | 用于估计标准动作内部差异，支持更稳健的归一化、DTW 和模板聚类。 |

采集时每名标准示范者建议录制 `5` 次原始重复，目标至少保留 `3` 次 PASS 样本。若 PASS 数不足，应补录，而不是用明显缺帧、遮挡或动作不完整的样本凑数。

### 2.2 练习/用户样本

练习/用户样本用于记录学习者的实际动作输入，支持个体练习反馈和后续评分校准。

| 场景 | 每词每用户建议采集量 | 保存策略 |
| --- | ---: | --- |
| 单次练习 | 3 次连续尝试 | 全部保存，分别生成 raw video、metadata、dense Holistic JSON 和质控报告。 |
| MVP 内测 | 5 次尝试 | 保存全部尝试，允许前 1 次作为熟悉界面样本，但不能静默丢弃。 |
| 后续个体进步分析 | 每次训练课 3-5 次 | 按用户、日期、词汇和尝试序号形成时间序列。 |

用户样本不要求全部达到标准样本级别质量，但必须能区分“动作问题”和“采集/识别失败”。低质量样本应保留质量状态，避免被误当成动作错误。

### 2.3 验证样本

验证样本用于后续算法 sanity check、阈值校准和人工评分一致性分析。当前阶段尚未具备验证集，只定义采集目标。

| 阶段 | 每词最低可启动量 | 每词推荐量 | 说明 |
| --- | ---: | ---: | --- |
| MVP 验证最低线 | 10 名用户 x 2 次 = 20 条 | 10 名用户 x 3 次 = 30 条 | 应包含不同熟练度，并保留专家评分或至少专家通过/不通过标签。 |
| 阈值校准线 | 20 名用户 x 3 次 = 60 条 | 30 名用户 x 3 次 = 90 条 | 用于估计分数区间、误差来源和跨用户稳定性。 |
| 负例/混淆样本 | 每词 5-10 条不同词或错误动作 | 每词 10-20 条 | 用于检查不同词汇之间是否被错误判高分。 |

验证样本必须与标准样本分离管理。参与标准模板构建的样本不得同时作为验证样本。

## 3. 录制规则

### 3.1 机位与构图

- 摄像头采用正面视角，水平放置，镜头中心尽量对准胸口到肩部高度。
- 手机或相机固定在支架上，不手持拍摄；拍摄期间不变焦、不移动机位。
- 示范者面对镜头，身体中线接近画面中心，头顶、双肩、双肘、双手完整入画。
- 画面应覆盖从头顶上方约 `10-15 cm` 到腰部或髋部位置；若词汇存在高举手动作，应保证最高点仍不出画。
- 推荐拍摄距离 `1.5-2.5 m`，以双手运动全程不出画为准。儿童或身高差异较大时优先调整距离，而不是裁切画面。

### 3.2 帧率、分辨率和编码

- 推荐：`1920x1080`、`30 fps`、横屏、H.264 MP4。
- 最低：`1280x720`、`25 fps`，低于此规格的样本默认不进入标准库。
- 尽量使用恒定帧率；如设备输出可变帧率，入库前应记录原始帧时间戳，并在 dense JSON 中保留 `frame_index` 与 `timestamp_ms`。
- 单词动作原始 clip 建议时长 `2-8 s`，包含准备段、动作段和收尾段；不为了缩短文件而裁掉准备/收尾。

### 3.3 光照与背景

- 使用稳定、均匀、正面或侧前方光照，避免强背光、频闪、局部强阴影。
- 背景应简洁、静止、与手部和衣物有明显对比；避免镜子、电视、移动人群和高纹理背景。
- 拍摄区域内不出现其他人的手、脸或身体，以免影响 Holistic 检测。

### 3.4 衣着、遮挡与外观

- 衣物颜色应与背景和肤色有区分，推荐纯色上衣。
- 袖口不得覆盖手腕和手掌；避免宽大袖口、手套、夸张饰品、手表反光、长发遮脸。
- 若词汇依赖面部表情或口型，需露出完整面部，不佩戴口罩或遮挡嘴部的物品。
- 眼镜可保留，但应避免强反光导致眼周和面部关键点不稳定。

### 3.5 重复录制规则

- 每个词每名标准示范者一次采集建议录制 `5` 次重复，每次单独成 clip。
- 每次重复之间回到中性准备姿态，停顿约 `1 s` 后再开始下一次。
- 若采集现场发现手出画、明显遮挡、口令打断或动作做错，应立即补录；原错误 clip 可保留为 reject 样本，但不得覆盖。

## 4. 动作起止标注与裁剪策略

### 4.1 标注点定义

每条样本至少标注以下字段：

- `prep_start_frame`：准备段开始，通常为 clip 第 0 帧。
- `action_start_frame`：动作语义开始的第一帧，即手部、身体或面部从中性姿态进入目标动作的第一帧。
- `action_end_frame`：动作语义完成的最后一帧，即目标词核心动作完成、准备返回中性姿态前的最后一帧。
- `recovery_end_frame`：收尾段结束，通常为返回中性姿态并稳定后的最后一帧。

对应时间戳字段使用毫秒：`prep_start_ms`、`action_start_ms`、`action_end_ms`、`recovery_end_ms`。帧号以原始视频解码后的 `0` 起始帧号为准。

### 4.2 标注原则

- 单词样本以完整动作为单位，不把一个词的内部阶段拆成多个独立样本。
- 起点不应标在口令声、眨眼或轻微预备晃动上，而应标在语义动作真实开始处。
- 终点不应标在完全回到放松状态之后，而应标在目标动作表达已经完成的位置。
- 若词汇包含静态定格，`action_end_frame` 应在定格表达完成后，而不是刚到达手型的瞬间。
- 建议首轮由采集员标注，抽样由第二人复核；有分歧时保留两个版本并记录 `annotation_status=needs_review`。

### 4.3 裁剪策略

- 原始视频必须永久保留，不允许只保存裁剪后视频。
- 可生成派生裁剪 clip：`trim_start = max(0, action_start - 0.3 s)`，`trim_end = min(video_end, action_end + 0.3 s)`。
- dense `Holistic` JSON 推荐优先基于原始视频生成，并在 JSON 中记录动作区间；裁剪 clip 可用于人工查看和前端预览。
- 若原始视频已经切掉动作开始或结束，样本应标记为 `REJECT`，不得通过后期裁剪修复。
- 若准备段或收尾段不足 `0.3 s`，标准样本应至少 `WARN`；如果动作段完整且检测稳定，可作为非标准调试样本保留。

## 5. 数据保存内容与目录建议

每条样本至少保存：

- 原始视频：不可覆盖、不可重编码替代原文件。
- 元信息 JSON：采集、示范者/用户、设备、词汇、标注、版本、路径和授权字段。
- dense `Holistic` JSON：逐帧保存 pose、left_hand、right_hand、face 的原始 landmark、可见性、时间戳和检测状态。
- 质量报告 JSON/Markdown：记录覆盖率、缺失率、动作完整性、帧率、分辨率和 PASS/WARN/REJECT 状态。
- 关键帧选择结果：可选，用于诊断和压缩展示；不替代 dense 序列。

建议目录结构：

```text
data/
  standard_library/
    stdlib_20260520_v0.1.0/
      manifest.json
      words/
        <word_id>/
          raw/
            <sample_id>.mp4
          metadata/
            <sample_id>.metadata.json
          holistic_dense/
            <sample_id>.holistic_dense.json
          quality/
            <sample_id>.quality.json
            <sample_id>.quality.md
          keyframes/
            <sample_id>.<selector_name>.keyframes.json
          preview/
            <sample_id>.trimmed.mp4
            <sample_id>.overlay.mp4
```

练习/用户样本和验证样本应使用独立根目录，例如 `data/user_samples/`、`data/validation_samples/`，避免与标准样本混放。

## 6. 元数据字段草案

### 6.1 样本主字段

```json
{
  "schema_version": "sample_metadata_v0.1",
  "protocol_version": "collection_protocol_20260520_v0.1",
  "library_version": "stdlib_20260520_v0.1.0",
  "sample_id": "std_20260520_word0001_signerA_take03",
  "sample_type": "standard",
  "word_id": "word0001",
  "word_text": "花",
  "language_variant": "CSL",
  "take_index": 3,
  "recorded_at": "2026-05-20T17:20:00+08:00",
  "timezone": "Asia/Shanghai",
  "recording_session_id": "session_20260520_001"
}
```

### 6.2 人员与授权字段

- `signer_id`：匿名 ID，不直接使用姓名。
- `signer_role`：`standard_demonstrator`、`practice_user`、`validation_user`、`expert_annotator`。
- `handedness`：`right`、`left`、`ambidextrous`、`unknown`。
- `skill_level`：`expert`、`teacher`、`learner_beginner`、`learner_intermediate`、`unknown`。
- `age_group`：可选，使用区间，不保存精确年龄。
- `consent_id`：授权记录 ID。
- `privacy_level`：例如 `internal_research`、`demo_allowed`、`restricted`。

### 6.3 采集环境与设备字段

- `camera_device`、`camera_position`、`orientation`、`resolution_width`、`resolution_height`、`fps_nominal`、`fps_measured`。
- `codec`、`container`、`duration_ms`、`frame_count`。
- `distance_m_estimated`、`lighting_condition`、`background_type`、`clothing_notes`、`occlusion_notes`。
- `operator_id`、`location_id`、`capture_app_version`。

### 6.4 标注与处理字段

- `prep_start_frame`、`action_start_frame`、`action_end_frame`、`recovery_end_frame`。
- `prep_start_ms`、`action_start_ms`、`action_end_ms`、`recovery_end_ms`。
- `annotation_status`：`draft`、`reviewed`、`needs_review`。
- `annotator_id`、`reviewer_id`、`annotation_notes`。
- `holistic_json_path`、`quality_report_path`、`keyframe_json_paths`、`trimmed_preview_path`。
- `mediapipe_version`、`holistic_config`、`processing_script_version`、`processing_git_commit`。
- `quality_status`：`PASS`、`WARN`、`REJECT`。

## 7. 标准样本库版本管理

### 7.1 版本号规则

标准样本库建议使用：

```text
stdlib_<YYYYMMDD>_v<MAJOR>.<MINOR>.<PATCH>
```

- `MAJOR`：词表、采集协议、关键字段 schema、Holistic 配置或模板选择策略发生不兼容变化。
- `MINOR`：新增词汇、新增标准示范者、新增合格样本、调整非破坏性元数据字段。
- `PATCH`：修正标注、补充质控报告、修复路径或文档，不改变样本语义。

### 7.2 不可变原则

- 原始视频一旦入库不得覆盖；错误样本使用 `quality_status=REJECT` 或 `deprecated=true` 标记。
- 标注修订应保留 `annotation_version` 和变更记录，不能静默覆盖历史结论。
- 每个标准库版本必须有 `manifest.json`，列出词表、样本数量、PASS/WARN/REJECT 计数、Holistic 配置和生成时间。
- 算法实验必须记录所使用的 `library_version`，否则结果不可复现。

## 8. 质量控制指标与临时阈值

以下阈值均为**临时草案值**。后续必须用真实用户样本、标准样本内部差异和专家评分标签重新校准。

### 8.1 基础视频质量

| 指标 | PASS 草案 | WARN 草案 | REJECT 草案 |
| --- | --- | --- | --- |
| 分辨率 | `>=1280x720`，推荐 `1920x1080` | 低于推荐但不低于最低线 | `<1280x720` 进入标准库时拒绝 |
| 帧率 | `>=25 fps` 且稳定 | `20-25 fps` 或轻微可变帧率 | `<20 fps` 或明显丢帧 |
| 动作段时长 | `0.6-6.0 s`，或落在该词模板中位数 `±35%` | 偏离模板中位数 `35%-60%` | 偏离 `>60%`、动作明显过短/过长 |
| 准备/收尾 | 动作前后各 `>=0.3 s` | 任一侧 `<0.3 s` 但动作完整 | 动作开始或结束被切断 |

### 8.2 Holistic 覆盖率

覆盖率只在 `action_start_frame` 到 `action_end_frame` 的动作段内统计。

| 指标 | PASS 草案 | WARN 草案 | REJECT 草案 |
| --- | --- | --- | --- |
| Pose 检测覆盖率 | `>=98%` | `95%-98%` | `<95%` |
| 活跃手检测覆盖率 | `>=97%` | `90%-97%` | `<90%` |
| 双手词汇的任一活跃手覆盖率 | 两只手均 `>=95%` | 任一手 `90%-95%` | 任一必需手 `<90%` |
| Face 检测覆盖率，表情/口型相关词 | `>=95%` | `90%-95%` | `<90%` |
| Face 检测覆盖率，非表情相关词 | `>=85%` | `70%-85%` | `<70%` 记为质控风险，不单独作为拒绝标准 |

活跃手应由词汇元数据指定：`required_hands=left/right/both/either`。如果词汇只需要单手，非活跃手缺失不应直接导致 REJECT。

### 8.3 关键点缺失与出画

| 指标 | PASS 草案 | WARN 草案 | REJECT 草案 |
| --- | --- | --- | --- |
| 活跃手连续缺失 | `<=2` 帧 | `3-5` 帧 | `>5` 帧 |
| 活跃手 landmark 出画比例 | `<2%` | `2%-5%` | `>5%` |
| Pose 躯干关键点缺失率 | `<2%` | `2%-5%` | `>5%` |
| 面部关键点缺失率，表情相关词 | `<5%` | `5%-10%` | `>10%` |

### 8.4 姿态稳定与构图

| 指标 | PASS 草案 | WARN 草案 | REJECT 草案 |
| --- | --- | --- | --- |
| 肩宽归一化尺度波动 | `<10%` | `10%-20%` | `>20%` |
| 肩中心横向漂移 | `<15%` 画面宽度 | `15%-25%` | `>25%` |
| 头/手/肘出画 | 无语义关键点出画 | 偶发边缘出画但 Holistic 稳定 | 动作核心阶段出画 |
| 非目标人体干扰 | 无 | 背景有轻微干扰 | 出现其他人的手/脸/身体并影响检测 |

### 8.5 动作完整性

| 指标 | PASS 草案 | WARN 草案 | REJECT 草案 |
| --- | --- | --- | --- |
| 起止标注完整 | 四个标注点齐全且顺序合法 | 缺少准备/收尾标注 | 缺少动作起点或终点 |
| 动作能量 | 手/腕/肘轨迹存在符合词汇预期的运动或定格 | 运动幅度偏小，需人工复核 | 明显未做动作或做错词 |
| 回到中性姿态 | 收尾可见 | 收尾短但不影响动作段 | 动作结束被截断 |
| 词汇语义一致性 | 采集员确认正确 | 采集员不确定，需专家复核 | 明确做错词或漏掉关键阶段 |

## 9. 质控状态规则

- `PASS`：满足基础视频质量、动作完整性和该词必需模态的 Holistic 覆盖要求，可进入标准模板候选。
- `WARN`：存在轻微质量问题，但动作段完整；可用于调试、诊断或用户练习记录，不建议直接作为标准模板。
- `REJECT`：动作不完整、关键模态严重缺失、核心动作出画、做错词或原始视频不可解码；不得进入标准模板。

标准库构建时建议只使用 `PASS` 样本。`WARN` 样本可保留在库中用于鲁棒性分析，但模板生成和阈值估计应显式排除。

## 10. 实现备注

1. dense `Holistic` JSON 应作为主数据资产保存，关键帧结果只作为压缩诊断视图。后续评分可以从 dense 序列做 DTW、分段 DTW 或关键帧锚点对齐。
2. 质量报告应由视频基础信息、Holistic 检测统计和动作标注共同生成。不要只凭文件是否存在判断可用。
3. 每个词应维护词汇配置：`word_id`、中文词、是否双手、是否依赖面部、预期动作阶段、标准动作时长范围、允许左右手镜像与否。
4. 入库流程建议为：采集原视频 -> 填写 metadata 初稿 -> 运行 Holistic dense 识别 -> 自动质控 -> 人工标注起止 -> 二次质控 -> 生成 manifest。
5. 当前没有真实用户样本，第一阶段验证只能做流程 sanity check：同视频自匹配、轻微扰动匹配、不同词负例匹配。不能声明真实用户评分已经准确。

## 11. 待确认问题

- 词表范围：MVP 第一批应固定多少个词，是否包含明显依赖面部表情/口型的词。
- 专家标准：标准示范者资格、专家复核流程和人工评分维度尚需定义。
- 隐私授权：原视频是否允许用于演示、论文、内部测试，需要在 `consent_id` 和 `privacy_level` 中明确。
- 左右手镜像：某些词是否允许左右手互换，需要在词汇配置层定义，不能由算法默认决定。
- 正式阈值：本文 QC 阈值需要在真实采集后按词、按设备、按人群重新校准。

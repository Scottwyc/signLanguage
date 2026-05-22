# 手语打分 MVP 现有数据与缓存盘点草案

审计时间：2026-05-20 17:16-17:23 CST  
工作目录：`/data/WYC/signLanguage`  
Worker：`data-cache-audit`  
结论口径：当前项目没有真实用户视频流样本，也没有人工评分标签。以下资产只能用于离线 sanity check、管线冒烟测试和数据结构设计，不能用于声明真实用户评分准确性、合格阈值或跨用户泛化。

## 1. 检查范围

本次只读检查以下路径，未修改源码、既有 worklog 或既有生成物：

- `/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频`
- `/data/WYC/signLanguage/data/Demo词汇.docx`
- `/data/WYC/signLanguage/work/generated`
- `/data/WYC/signLanguage/work/reports`
- `/data/WYC/signLanguage/work/scripts`
- `/data/WYC/signLanguage/.codex/tmux-workers/inbox/data-cache-audit`

补充说明：计划要求更新 `.codex/tmux-workers/progress/data-cache-audit.md` 和 worker report，但当前沙箱内 `/data/WYC/signLanguage/.codex` 挂载为只读，写入被系统拒绝。因此 worker 状态更新只能在本文和最终汇报中记录。

## 2. Demo 视频资产

Demo 视频目录为：

`/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频`

共 10 个 `.mp4`，均为竖屏 `592x1280`。可作为离线 sanity check 的标准/伪用户素材，但不能代表正式标准库或用户练习数据。

| 词名文件 | 精确路径 | 帧率 | 帧数 | 时长 | 大小 |
| --- | --- | ---: | ---: | ---: | ---: |
| 唱歌.mp4 | `/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/唱歌.mp4` | 25.000 | 53 | 2.120s | 82,916 B |
| 指示.mp4 | `/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/指示.mp4` | 22.306 | 59 | 2.645s | 56,851 B |
| 月亮.mp4 | `/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/月亮.mp4` | 25.000 | 93 | 3.720s | 96,742 B |
| 朋友.mp4 | `/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/朋友.mp4` | 25.000 | 54 | 2.160s | 50,174 B |
| 汽车.mp4 | `/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/汽车.mp4` | 26.364 | 87 | 3.300s | 101,259 B |
| 花.mp4 | `/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/花.mp4` | 29.450 | 107 | 3.633s | 87,512 B |
| 虎.mp4 | `/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/虎.mp4` | 28.205 | 110 | 3.900s | 144,112 B |
| 谗（羡慕）.mp4 | `/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/谗（羡慕）.mp4` | 26.571 | 62 | 2.333s | 74,757 B |
| 跳.mp4 | `/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/跳.mp4` | 14.683 | 37 | 2.520s | 46,091 B |
| 香蕉.mp4 | `/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/香蕉.mp4` | 25.625 | 82 | 3.200s | 76,530 B |

## 3. Holistic / 缓存 / 结果资产分类

### 3.1 10 个 demo 的稀疏探针缓存，不是 raw dense landmark

路径：

- `/data/WYC/signLanguage/work/generated/holistic_probe_20260428_full`
- 示例：`/data/WYC/signLanguage/work/generated/holistic_probe_20260428_full/唱歌/唱歌.json`
- 示例 JSONL：`/data/WYC/signLanguage/work/generated/holistic_probe_20260428_full/唱歌/唱歌_frames.jsonl`
- 汇总：`/data/WYC/signLanguage/work/generated/holistic_probe_20260428_full/holistic_probe_summary.md`
- 关键帧建议：`/data/WYC/signLanguage/work/generated/holistic_probe_20260428_full/keyframe_recommendation/keyframe_recommendations.json`

证据：

- 每个词只有 `10-12` 条 sampled frames；`跳` 为 10 条，其余多数为 12 条。
- 单帧字段为 `frame_idx/timestamp_sec/pose_present/left_hand_present/right_hand_present/face_present/pose/left_hand/right_hand/face/motion_energy/bbox_shift`。
- `pose/left_hand/right_hand/face` 仅保留 bbox 和 visibility 级摘要，不含 `pose_landmarks`、`left_hand_landmarks`、`right_hand_landmarks`、`face_landmarks` 原始坐标列表。

复用建议：

- 可用于 bbox 模式的快速 DTW/相似度原型、覆盖率统计、关键帧建议。
- 不适合作为正式 dense `Holistic` 模板库主资产。

### 3.2 raw step-dense Holistic landmark 缓存，当前只覆盖 `花.mp4`

最有复用价值的原始 landmark 缓存：

- `/data/WYC/signLanguage/work/generated/parallel_sampling_strategies_three_layer_run1/candidate_cache/花/花_holistic_results.json`
- `/data/WYC/signLanguage/work/generated/holistic_worker_frame_slice_benchmark_run2/results/花/花_holistic_results.json`

证据：

- 两个文件均指向 `/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/花.mp4`。
- `total_frames=107`，`fps=29.44954128440367`，`records=28`。
- 帧索引为 step-4 近似密采样：`[0, 4, 8, 12, ..., 104, 106]`。
- 每条 record 包含 `row` 和 `result_data`；`result_data` 内有 `pose_landmarks`、`left_hand_landmarks`、`right_hand_landmarks`、`face_landmarks`，其中 pose 为 33 点、face 为 478 点、左右手为 0 或 21 点。

复用建议：

- 这是当前最接近 scoring MVP dense 主线的可复用缓存，但只覆盖 `花.mp4`，且是 step-4，不是逐帧 full dense。
- 可先用于 landmark 模式的评分原型冒烟测试，再扩展生成其他 9 个 demo 的同格式缓存。

### 3.3 keyframe 级 raw Holistic landmark 输出，不是 dense 缓存

路径：

- `/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals_holistic/uniform/花/花_holistic_results.json`
- `/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals_holistic/two_stage/花/花_holistic_results.json`
- `/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals_holistic/adaptive/花/花_holistic_results.json`

证据：

- 三个文件均为 `records=12`，均含 raw landmark `result_data`。
- uniform 帧索引：`[0, 10, 19, 29, 39, 48, 58, 67, 77, 87, 96, 106]`。
- two_stage 帧索引：`[0, 18, 26, 35, 44, 53, 62, 71, 79, 88, 97, 106]`。
- adaptive 帧索引：`[0, 21, 31, 42, 53, 58, 64, 74, 79, 85, 95, 106]`。

复用建议：

- 可用于关键帧诊断、可解释截图、压缩版评分对比。
- 不应替代 dense/step-dense 时序主数据。

### 3.4 benchmark 级 Holistic 输出，只能作格式参考

路径：

- `/data/WYC/signLanguage/work/generated/holistic_worker_benchmark_run1/results/唱歌/唱歌_holistic_results.json`
- `/data/WYC/signLanguage/work/generated/holistic_worker_benchmark_run1/results/花/花_holistic_results.json`
- `/data/WYC/signLanguage/work/generated/holistic_worker_benchmark_run1/results/跳/跳_holistic_results.json`

证据：

- 每个文件只有 `records=2`，帧索引为 `[0, 4]`。
- 含 raw landmark `result_data`，但帧数太少。

复用建议：

- 只适合验证 reader/schema 兼容，不适合评分。

### 3.5 keyframe sampling 结果 JSON，主要是选帧结果和评估摘要

路径：

- `/data/WYC/signLanguage/work/generated/keyframe_sampling_uniform_single/uniform_sampling.json`
- `/data/WYC/signLanguage/work/generated/keyframe_sampling_two_stage_single/two_stage_sampling.json`
- `/data/WYC/signLanguage/work/generated/keyframe_sampling_adaptive_single/adaptive_sampling.json`
- `/data/WYC/signLanguage/work/generated/parallel_sampling_strategies_three_layer_run1/{uniform,two_stage,adaptive,dense}/*.json`
- `/data/WYC/signLanguage/work/generated/parallel_sampling_strategies_run2/{uniform,two_stage,adaptive,dense}/*.json`
- `/data/WYC/signLanguage/work/generated/parallel_sampling_strategies_flower_run4/{uniform,two_stage,adaptive,dense}/*.json`

证据：

- 这些文件主要记录 sampled frame indices、coverage 指标、motion energy 和耗时。
- `dense_uniform_step4_sampling.json` 记录从 step-4 candidate cache 里选出的 12 帧，例如 `[4, 32, 36, 40, 44, 56, 60, 68, 72, 84, 88, 96]`，本身不是 raw landmark 缓存。

复用建议：

- 可用于比较选帧策略和生成诊断视图。
- 评分主线仍应读取对应 raw landmark cache 或重新生成 dense cache。

### 3.6 可视化结果，只作人工核查

路径：

- `/data/WYC/signLanguage/work/generated/holistic_viz_20260428`
- `/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals`
- `/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals_holistic`
- `/data/WYC/signLanguage/work/generated/keyframe_sampling_visuals_run2`

证据：

- `holistic_viz_20260428` 下 10 个词均有 annotated/skeleton/triptych/contact_sheet PNG 和 `*_viz_summary.{json,md}`。
- `keyframe_sampling_visuals*` 主要覆盖 `花.mp4` 的不同选帧策略截图、timeline 和 contact sheet。

复用建议：

- 用于检查手、脸、姿态是否被 MediaPipe 检出，以及向非技术人员解释关键帧选择。
- 不作为评分输入主数据。

### 3.7 已有 scoring MVP 结果，属于 bbox sanity check

路径：

- `/data/WYC/signLanguage/work/generated/scoring_mvp_run1/flower_vs_singing_bbox_negative/scoring_mvp_result.json`
- `/data/WYC/signLanguage/work/generated/scoring_mvp_run1/flower_vs_singing_bbox_negative/scoring_mvp_result.md`
- `/data/WYC/signLanguage/work/generated/scoring_mvp_run1/flower_vs_singing_bbox_negative/alignment_path.csv`
- 脚本：`/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py`

证据：

- 结果生成时间：`2026-05-20T17:20:19`。
- 输入标准序列：`/data/WYC/signLanguage/work/generated/holistic_probe_20260428_full/花/花.json`。
- 输入查询序列：`/data/WYC/signLanguage/work/generated/holistic_probe_20260428_full/唱歌/唱歌.json`。
- 特征模式：`bbox`。
- 主对齐结果：`prototype_score=85.53070912462756`，`normalized_distance=0.05470314621925354`，`DTW path length=12`。
- 伪用户 sanity check 分数约 `93.057-93.439`。

复用建议：

- 可作为评分脚本输出格式和声明口径的 smoke test。
- 因输入来自稀疏 bbox probe，不应据此判断真实 landmark scoring 能力；更不能据此设置合格阈值。

### 3.8 资料 profile 与文档关联风险

路径：

- `/data/WYC/signLanguage/work/generated/sign_data_profile/sign_data_profile.json`
- `/data/WYC/signLanguage/work/generated/sign_data_profile/sign_data_profile.md`
- 原始文档：`/data/WYC/signLanguage/data/Demo词汇.docx`

证据：

- profile 中包含 10 个 sample 的视频元数据和 DOCX 片段。
- 但当前 profile 里的 DOCX 片段与文件名疑似错位，例如 `唱歌.mp4` 对应片段描述“香蕉”，`花.mp4` 对应片段描述“跳”。

复用建议：

- 视频文件本身可用；DOCX 片段和词名映射在入库前必须人工复核。
- 不能直接把 profile 中的 doc_summary 当作可靠标签或评分标准描述。

## 4. 当前缺失数据

用于真实评分数据集仍缺少：

- 真实用户视频流样本，包括同一用户多次尝试、不同熟练度用户、不同设备/环境样本。
- 人工评分标签或专家 pass/fail 标签。
- 标准示范者多 take、多人的标准模板库。
- 明确动作起止标注：`action_start_frame/action_end_frame` 及复核状态。
- 每条样本的采集元数据：人员匿名 ID、设备、分辨率、帧率、距离、光照、背景、授权、质量状态。
- 全词汇 raw dense 或 step-dense Holistic landmark cache；目前只有 `花.mp4` 有可复用 step-4 raw landmark 缓存。
- 校准集/验证集/负例集的拆分与不可交叉规则。
- 专家维度评分定义，例如手型、轨迹、节奏、身体姿态、面部/口型、完成度。
- 正式阈值、评分等级和跨用户泛化证据。

## 5. 最小可复用数据布局建议

在不改动现有生成物的前提下，后续可新建一个 MVP seed 数据层，将 demo 资产以“模板”和“伪用户 sanity case”分开管理。

建议结构：

```text
data/
  scoring_mvp_seed/
    manifests/
      demo_seed_manifest_v0.1.json
    standard_templates/
      demo_v0.1/
        <word_id>/
          <sample_id>/
            raw/
              source.mp4
            metadata/
              sample.metadata.json
            holistic/
              sample.holistic_dense.json
              sample.holistic_step4.json
            quality/
              sample.quality.json
              sample.quality.md
            keyframes/
              uniform.keyframes.json
              two_stage.keyframes.json
              adaptive.keyframes.json
            preview/
              contact_sheet.png
              timeline.png
    pseudo_user_cases/
      demo_v0.1/
        <case_id>/
          case.metadata.json
          query_sequence.json
          expected_relation.json
          scoring_result.json
```

关键字段建议：

- `manifest.json`：列出词表、样本 ID、原始视频路径、Holistic cache 路径、质量状态、生成脚本版本和生成时间。
- `sample.metadata.json`：保留 `sample_type=demo_template`、`word_id`、`word_text`、`source_video_path`、`fps`、`frame_count`、`duration_ms`、`resolution`、`label_status`。
- `quality.json`：记录 pose/left/right/face 覆盖率、缺失率、动作起止是否已标注、是否可作为 sanity check。
- `pseudo_user case.metadata.json`：记录 `source_template_sample_id`、扰动类型、裁剪/下采样/噪声参数、期望关系（self/perturbed/different_word_negative）。

注意：现阶段不要把 demo seed 命名为正式 `standard_library`，避免误读为已复核标准库。

## 6. 风险

- 现有 demo 和缓存只支持离线 sanity check，不能支持真实评分结论。
- `holistic_probe_20260428_full` 名称里有 `full`，但实际是“全 10 个 demo 的稀疏探针”，不是全帧 dense landmark。
- `花.mp4` 在多处评估中左手覆盖率为 `0.0`，如果直接做手部评分，缺失处理会显著影响结果。
- 资料 profile 的 DOCX 描述与视频文件名疑似错位，入库前必须复核词名映射。
- step-dense raw landmark 缓存目前只覆盖 `花.mp4`；其余 9 个 demo 若要进入 landmark scoring，需要补生成同格式缓存。
- 已有 bbox scoring 结果分数偏高并不代表不同词负例已被有效拉开，因为输入是 bbox 摘要且没有人工标签。

## 7. 下一步建议

1. 先把 `/data/WYC/signLanguage/work/generated/parallel_sampling_strategies_three_layer_run1/candidate_cache/花/花_holistic_results.json` 作为 landmark mode 的最小输入，跑通 scoring reader、归一化、DTW 和诊断输出。
2. 用已有 worker daemon 或缓存脚本为其余 9 个 demo 生成统一 schema 的 step-4 raw landmark JSON；如果存储压力允许，再生成逐帧 dense JSON。
3. 人工复核 `Demo词汇.docx` 与 10 个视频文件的词名映射，修正 seed manifest 中的 label_status。
4. 保留 `work/generated/scoring_mvp_run1/flower_vs_singing_bbox_negative` 作为 bbox smoke test；后续新增 landmark-mode 结果时应另建日期/版本目录，不覆盖。
5. 等标准模板和真实用户样本采集到位后，再进入阈值校准、评分等级和人工标签一致性分析。

## 8. 本次执行过的只读命令摘要

- `sed -n` 读取 worker plan、skill 文档、既有报告和脚本片段。
- `find` / `rg --files` 盘点 demo 视频、JSON、JSONL、CSV、Markdown、PNG 和 scoring 结果路径。
- `/home/wuyangcheng/myenv/bin/python` + `cv2` 读取 demo 视频元数据。
- `/home/wuyangcheng/myenv/bin/python` + `json` 解析 Holistic/result JSON 的 schema、records 数、帧索引和关键字段。
- `wc -l` 检查 JSONL 和 alignment CSV 行数。
- `find ... inbox/data-cache-audit` 检查 worker inbox；截至报告写入前未发现 queued instruction 文件。

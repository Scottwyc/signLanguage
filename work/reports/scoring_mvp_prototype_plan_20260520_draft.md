# 手语打分 MVP 最小原型实施计划草稿

生成时间：2026-05-20 17:20:45 CST

## 1. 目标与边界

本草稿只规划第一版离线 scoring prototype，不做真实用户评分结论。当前没有真实用户视频流样本，也没有人工评分标签，因此原型目标应限定为：

- 验证已缓存 Holistic JSON 能否支撑标准样本与待测样本的相似度计算。
- 验证时序对齐、缺失关键点处理、逐组误差统计和报告输出链路是否完整。
- 用 demo 视频、伪用户扰动和不同词汇负例做 sanity check。
- 不输出正式 pass/fail 阈值，不宣称真实用户评分准确或跨用户泛化。

默认原则：优先读取已有 `*_holistic_results.json` 或候选缓存 JSON；只有缓存缺失且显式允许时，才调用已有 Holistic 生成脚本补缓存。

## 2. 现有代码可复用点

### 2.1 视频与元数据

- `work/scripts/signlanguage_common.py`
  - `find_demo_videos(data_root)`：扫描 demo 视频。
  - `probe_video_metadata(video_path)`：通过 ffprobe 读取 fps、总帧数、分辨率、时长等信息。

可用于原型 CLI 的视频发现和结果元数据补全。

### 2.2 Holistic 缓存与行结构

- `work/scripts/keyframe_sampling_common.py`
  - `load_candidate_cache(cache_path)`：读取候选缓存，兼容 `rows`、`videos`、`video_result`、`records` 顶层格式。
  - `get_candidate_video_entry(cache_payload, video_name)`：从多视频候选缓存中取单个视频条目，并把 `records[].row` 规范化为 `rows`。
  - `summarize_rows(meta, total_frames, rows)`：统计 pose/hand/face 检出率、运动能量、时间覆盖等摘要。
  - `_serialize_holistic_result(result)` 的落盘格式已经在 `records[].result_data` 中保存了 `pose_landmarks`、`left_hand_landmarks`、`right_hand_landmarks`、`face_landmarks`。

建议原型新增轻量 loader 时直接兼容两类输入：

- 原始结果：`*_holistic_results.json`，含 `records`。
- 候选缓存：`candidate_cache.json` 或策略 JSON，含 `videos[].rows` / `video_result` / `result_file`。

### 2.3 关键帧选择

- `select_uniform_keyframes(rows, sample_budget)`
- `select_energy_coverage_keyframes(rows, sample_budget)`
- `select_two_stage_keyframes(rows, sample_budget)`
- `select_adaptive_keyframes(rows, sample_budget)`
- `select_even_subsample(frame_indices, target_count)`

原型主路线建议使用 dense/step-dense 全序列做 DTW。关键帧选择保留为诊断支线：用相同输入缓存抽取 8-12 个代表帧，输出对齐解释图和逐帧误差表。

### 2.4 可视化

- `work/scripts/visualize_sampling_strategy_results.py`
  - 已明确“直接读取已保存的 Holistic 结果文件，只做统一可视化，不再重复跑识别”。
  - `_render_single_video(...)` 可以从 `holistic_result_file` 读取 `records`，再生成三联图、联系表、时间轴。
- `keyframe_sampling_common.render_holistic_results_from_file(...)`
  - 可按指定 frame index 从已有 result file 生成子集可视化。
- `keyframe_sampling_common._render_visual_cache(...)`
  - 能从序列化 landmark JSON 画 pose/hand/face，不需要重新跑 Holistic。

建议 scoring 原型只新增“对齐诊断图”和“误差热力图”，原视频关键点抽帧复用上述渲染路径。

## 3. 当前可直接使用的数据

demo 视频目录：

`/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/`

已看到的视频包括：`花.mp4`、`唱歌.mp4`、`跳.mp4`、`朋友.mp4`、`汽车.mp4`、`月亮.mp4`、`指示.mp4`、`虎.mp4`、`香蕉.mp4`、`谗（羡慕）.mp4`。

已存在 raw Holistic result JSON 数量：8 个。首轮不重跑 Holistic 时，建议优先用这些缓存：

- `work/generated/parallel_sampling_strategies_three_layer_run1/candidate_cache/花/花_holistic_results.json`
- `work/generated/holistic_worker_benchmark_run1/results/花/花_holistic_results.json`
- `work/generated/holistic_worker_benchmark_run1/results/唱歌/唱歌_holistic_results.json`
- `work/generated/holistic_worker_benchmark_run1/results/跳/跳_holistic_results.json`

其中 `花` 可作为模板和伪用户正例源，`唱歌`、`跳` 可作为不同词汇负例。若需要更多负例，后续应先查缓存；缺失时再显式生成候选缓存。

## 4. 建议的最小脚本布局

### 4.1 `work/scripts/scoring_mvp_common.py`

职责：纯算法和数据结构，便于测试。

建议函数：

- `load_holistic_sequence(path, video_name=None) -> SequenceBundle`
  - 支持 `*_holistic_results.json`、`candidate_cache.json`、策略 JSON。
  - 返回 `records`、`rows`、`result_data`、fps、total_frames、source_path、video_path。
- `extract_landmark_arrays(records, groups=("pose", "left_hand", "right_hand"))`
  - 从 `result_data` 中取 landmark 坐标和 mask。
  - MVP 暂不使用完整 face 478 点做主评分；face 可先只统计 presence 或保留为后续扩展。
- `normalize_frame_landmarks(frame, mode="torso")`
  - 以肩中心或 pose bbox 中心平移。
  - 以肩宽、pose bbox 对角线或上半身尺度归一化。
  - 缺 pose 时回退到手部 bbox 尺度；仍缺失则标记低置信。
- `build_feature_sequence(bundle, config)`
  - 输出 `T x D` 特征矩阵、`T x D` mask、group slices、quality summary。
- `frame_distance(ref_t, usr_t, masks, group_weights)`
  - 按 group 加权 Euclidean / L1。
  - 只在双方均可见的维度上计算，同时记录 missing penalty。
- `dtw_align(ref_seq, usr_seq, band=None)`
  - 用 numpy 实现最小 DP DTW；当前 demo 序列很短，不需要 `fastdtw`。
  - 可选 Sakoe-Chiba band 限制过度扭曲。
- `score_alignment(alignment, distances, quality)`
  - 输出 overall、hand、pose、tempo、completion、confidence。
- `make_pseudo_user(bundle, perturbation_config)`
  - 从模板缓存生成伪用户序列：时间裁剪、降采样、时间拉伸、空间抖动、关键点缺失、左右手缺失模拟。

### 4.2 `work/scripts/run_scoring_mvp_sanity.py`

职责：命令行 runner，只读缓存并输出结果。

建议 CLI：

```bash
/home/wuyangcheng/myenv/bin/python work/scripts/run_scoring_mvp_sanity.py \
  --template-word 花 \
  --template-result work/generated/parallel_sampling_strategies_three_layer_run1/candidate_cache/花/花_holistic_results.json \
  --negative-result 唱歌=work/generated/holistic_worker_benchmark_run1/results/唱歌/唱歌_holistic_results.json \
  --negative-result 跳=work/generated/holistic_worker_benchmark_run1/results/跳/跳_holistic_results.json \
  --output-dir work/generated/scoring_mvp_sanity_20260520
```

默认行为：

- 不调用 MediaPipe。
- 缺缓存时报错并跳过该 case。
- 只有加 `--allow-generate-missing-cache` 时，才调用已有 `sample_keyframe_candidates.py` 或常驻 worker 补缓存。

### 4.3 `work/scripts/visualize_scoring_mvp_alignment.py`（可选）

若保持最小化，也可以先集成在 runner 中。建议输出：

- `alignment_path.png`：DTW 对齐路径。
- `group_score_bars.png`：整体、手部、姿态、节奏、完成度分。
- `per_frame_error.png`：沿用户时间轴的误差曲线。
- `per_joint_error_heatmap.png`：每组关键点误差热力图。
- 关键帧三联图仍复用 `render_holistic_results_from_file(...)`。

## 5. 输出 JSON 结构建议

主文件：`work/generated/scoring_mvp_sanity_<run_id>/scoring_results.json`

```json
{
  "schema_version": "scoring_mvp.v0",
  "generated_at": "2026-05-20T17:20:45+08:00",
  "config": {
    "feature_groups": ["pose", "left_hand", "right_hand"],
    "normalization": "torso_or_pose_bbox",
    "alignment": "dtw_numpy",
    "sample_mode": "cached_step_dense",
    "rerun_holistic": false
  },
  "templates": [
    {
      "word": "花",
      "video_path": ".../花.mp4",
      "holistic_result_file": ".../花_holistic_results.json",
      "frames": 28,
      "fps": 29.4495,
      "quality": {
        "pose_presence_ratio": 1.0,
        "left_hand_presence_ratio": 0.0,
        "right_hand_presence_ratio": 0.75,
        "usable_frame_ratio": 1.0
      }
    }
  ],
  "cases": [
    {
      "case_id": "flower_self",
      "case_type": "self_positive",
      "expected_behavior": "score_high",
      "reference": {"word": "花", "source": ".../花_holistic_results.json"},
      "candidate": {"word": "花", "source": "pseudo:self"},
      "sequence": {
        "reference_frames": 28,
        "candidate_frames": 28,
        "reference_duration_sec": 3.63,
        "candidate_duration_sec": 3.63
      },
      "alignment": {
        "method": "dtw_numpy",
        "normalized_cost": 0.0,
        "path_length": 28,
        "warp_ratio": 1.0,
        "path_file": "cases/flower_self/alignment_path.json"
      },
      "scores": {
        "overall": 99.0,
        "hand": 99.0,
        "pose": 99.0,
        "tempo": 100.0,
        "completion": 100.0,
        "confidence": 0.95
      },
      "quality": {
        "missing_penalty": 0.0,
        "low_visibility_frames": [],
        "notes": []
      },
      "diagnostics": {
        "largest_error_group": null,
        "largest_error_frame_pairs": [],
        "warnings": []
      },
      "artifacts": {
        "case_report_md": "cases/flower_self/report.md",
        "alignment_plot": "cases/flower_self/alignment_path.png",
        "error_curve": "cases/flower_self/per_frame_error.png"
      }
    }
  ],
  "aggregate": {
    "positive_cases": 5,
    "negative_cases": 2,
    "qualitative_pass": true,
    "notes": [
      "仅为流程 sanity check，不代表真实用户评分校准。"
    ]
  }
}
```

配套 Markdown：`scoring_sanity_report.md`

内容建议：

- 输入缓存清单。
- 每个 case 的期望行为、实际相对表现、主要诊断。
- 正例与负例的排序是否符合预期。
- 缺失率、可见度、对齐扭曲程度的风险提示。

## 6. Sanity-check case 设计

### 6.1 正例

1. 自身对齐：`花` vs `花`
   - 期望：总体分最高，DTW cost 接近 0，对齐路径接近对角线。

2. 时间降采样：`花` vs `花` 的隔帧/抽帧版本
   - 期望：总体分仍高，tempo 或 coverage 略降，DTW 能对齐。

3. 时间拉伸/压缩：`花` 的伪用户时间轴重采样
   - 期望：动作形态分高，tempo 分下降，warp ratio 变大。

4. 空间小扰动：对手部和 pose 坐标加小幅 Gaussian noise
   - 期望：总体分中高，per-joint error 能定位到被扰动组。

5. 局部缺失：随机置空若干右手帧或低可见度帧
   - 期望：confidence 降低，missing penalty 上升，hand 分下降；整体不应被误判为完全不同词。

6. 前后裁剪：去掉开头或结尾若干帧
   - 期望：核心动作仍可对齐，但 completion 分下降，报告提示动作不完整。

### 6.2 负例

1. `花` vs `唱歌`
   - 期望：手部/pose 轨迹差异明显，总体分低于任一正例扰动。

2. `花` vs `跳`
   - 期望：pose 运动和节奏差异显著，DTW cost 高，diagnostics 指出姿态/节奏不匹配。

3. 后续可补：`花` vs `香蕉`、`花` vs `朋友`
   - 只有存在缓存时纳入；否则默认跳过，不自动重跑 Holistic。

### 6.3 定性验收口径

首轮只看排序与诊断是否合理：

- self positive > 轻微扰动 positive > 局部缺失/裁剪 positive > different-word negative。
- 缺失严重时 confidence 必须下降。
- 负例不应因为 pose/face 共同存在而获得过高 overall。
- 若某个 demo 的手部检出率低，应在报告中提示“当前缓存不足以验证手部动作评分”。

## 7. 评分公式建议

MVP 不需要复杂模型，先用可解释规则：

```text
overall = 0.50 * hand_score
        + 0.25 * pose_score
        + 0.15 * completion_score
        + 0.10 * tempo_score

confidence = f(usable_frame_ratio, hand_presence_ratio, pose_presence_ratio, missing_rate)
final_score = overall * confidence
```

其中：

- `hand_score`：左右手 landmark 对齐误差转换为 0-100 分，右手/左手按可见 mask 加权。
- `pose_score`：肩、肘、腕、躯干关键点误差。
- `completion_score`：裁剪、尾部缺失、有效帧覆盖率。
- `tempo_score`：DTW 路径相对对角线的偏离程度、warp ratio、时长差。
- `confidence`：不是评分好坏，而是本次评估可信度；低手部检出率应明显降低 confidence。

距离到分数的转换建议用稳定单调函数：

```text
score = 100 * exp(-normalized_distance / sigma)
```

`sigma` 首轮用 sanity check 手调，不作为真实阈值。

## 8. 依赖与环境

使用 `/home/wuyangcheng/myenv` 检查到：

- `numpy` 可用。
- `cv2` 可用。
- `mediapipe` 可用。
- `PIL` 可用。
- `scipy` 可用。
- `matplotlib` 可用，但默认配置目录不可写，建议运行绘图脚本时设置 `MPLCONFIGDIR=/tmp/matplotlib-signlanguage` 或输出目录下的临时 cache。
- `fastdtw` 不存在。

结论：不建议新增 `fastdtw` 依赖。MVP 用 numpy/scipy 自己实现短序列 DTW 足够。

## 9. 实施顺序

1. 新增 `scoring_mvp_common.py`
   - 先实现 loader、feature extraction、normalization、mask、summary。
   - 用现有 `花_holistic_results.json` 做只读单元级 smoke test。

2. 新增 `run_scoring_mvp_sanity.py`
   - 接受 template result 和 negative result。
   - 自动生成 self、time warp、jitter、dropout、crop、different-word cases。
   - 输出 `scoring_results.json` 和 `scoring_sanity_report.md`。

3. 增加最小图表
   - alignment path、group score bar、per-frame error curve。
   - 关键帧原图/骨骼图复用已有 visualization 函数。

4. 跑首轮不重识别 sanity check
   - 使用 `花` 做模板和正例源。
   - 使用 `唱歌`、`跳` 做负例。
   - 只验证排序和诊断，不校准阈值。

5. 根据结果决定是否补缓存
   - 若负例数量不足，再显式为 `香蕉`、`朋友` 等 demo 生成 candidate cache。
   - 补缓存命令必须在报告中标记为“因缓存缺失而生成”。

## 10. 主要风险

- 当前缓存多为 step-dense 或采样帧，未必覆盖完整动作；真实评分前应使用更密的标准模板缓存。
- demo 视频不是多用户、多机位、多次录制数据，不能验证泛化。
- 缺少动作起止标签，裁剪与 completion 只能启发式判断。
- MediaPipe 对手部遮挡、左右手镜像、快速动作可能不稳定；低 hand presence 时需要降低 confidence。
- `花` 的现有缓存中左手检出率可能为 0，不能用它单独证明双手评分有效。
- face 478 点维度高且与手语词汇评分关系不稳定，MVP 不应让 face 主导 overall。
- 不同历史 JSON 格式并存，需要 loader 明确记录 source schema，避免把 strategy summary 当 raw sequence。
- 若后续要补缓存，Holistic 初始化成本仍是瓶颈，应复用已有常驻 worker 或候选生成层。

## 11. 建议的下一步

建议 coordinator 下一步让实现 worker 按上述布局新增两个脚本，首轮只用已有 `花/唱歌/跳` 缓存跑离线 sanity check。验收标准不是分数绝对值，而是 case 排序、confidence 降级、诊断定位和报告产物是否可解释。

## 12. Worker 执行备注

- 已按只读方式检查 `work/scripts` 和现有 generated JSON。
- 未修改源码、既有 worklog、既有 generated artifacts 或其他 scoring report。
- 尝试更新 `.codex/tmux-workers/progress/prototype-plan.md` 时，沙箱返回 `Read-only file system`；因此未能写入该 progress 文件。

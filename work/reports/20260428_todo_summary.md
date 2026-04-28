# 2026-04-28 手语项目工作整理

本报告整理 2026-04-28 的当前工作，围绕 `worklog_sign.md` 中的两个 TODO 展开：

1. 对手语资料进行结构化描述，形成量化的特征指标，覆盖手部、肢体、面部和时序。
2. 针对标准样本 demo 检查 `MediaPipe Holistic` 的特征采样效果，判断是否能有效覆盖手语语义的关键信息。

对应的主产物如下：

- 结构化盘点结果：`/data/WYC/signLanguage/work/generated/sign_data_profile/sign_data_profile.json`
- 结构化盘点 Markdown：`/data/WYC/signLanguage/work/generated/sign_data_profile/sign_data_profile.md`
- Holistic 全量探针结果：`/data/WYC/signLanguage/work/generated/holistic_probe_20260428_full/`
- Holistic 可视化结果：`/data/WYC/signLanguage/work/generated/holistic_viz_20260428/`

## 1. TODO 一：资料结构化描述与量化特征模板

### 1.1 已完成的工作

这条线已经用脚本跑通了“资料盘点 -> 结构化输出”的闭环，核心实现位于：

- `/data/WYC/signLanguage/work/scripts/signlanguage_common.py`
- `/data/WYC/signLanguage/work/scripts/profile_sign_data.py`

`profile_sign_data.py` 完成了三件事：

1. 从 `/data/WYC/signLanguage/data/Demo词汇.docx` 里提取文本。
2. 扫描 `/data/WYC/signLanguage/data/Demo词汇视频/` 下的 demo 视频，并与文档片段按顺序配对。
3. 生成结构化盘点结果，并预留后续关键点采样所需的量化特征字段。

### 1.2 盘点结果

本次盘点覆盖 10 个 demo 视频，已经输出对应的 JSON 和 Markdown 报告。

当前报告里最关键的不是“语义翻译”，而是把每个词条对应的可测特征提前定义出来，形成统一模板。这样后续 `Holistic` 的采样结果可以直接回填到同一套字段里。

### 1.3 量化特征模板

目前预留的模板分为四组：

- `hand`
  - `left_hand_presence_ratio`
  - `right_hand_presence_ratio`
  - `hand_visibility_mean`
  - `hand_motion_energy`
  - `left_right_symmetry_score`
- `body`
  - `pose_presence_ratio`
  - `pose_visibility_mean`
  - `pose_motion_energy`
  - `upper_body_span_ratio`
- `face`
  - `face_presence_ratio`
  - `face_visibility_mean`
  - `mouth_activity_score`
  - `eyebrow_activity_score`
- `temporal`
  - `sampled_frame_count`
  - `effective_span_sec`
  - `motion_peak_count`
  - `motion_smoothness`
  - `coverage_stability`

### 1.4 这条 TODO 的结论

这一步已经把“资料整理”从纯文本描述变成了可计算、可对齐、可回填的结构化数据层。

后续只要 `Holistic` 的关键点结果进入同一套模板，就可以逐词条比较：

- 哪些部位稳定可见
- 哪些部位掉点严重
- 动作是否有明显时序峰值
- 采样窗口是否覆盖到动作转折点

## 2. TODO 二：Holistic 特征采样效果验证

### 2.1 已完成的工作

这一条线已经在 `myenv` 环境中完成依赖补齐和实跑，核心依赖包括：

- `mediapipe==0.10.20`
- `opencv-python`
- `python-docx`
- `protobuf==4.25.8`

探针脚本为：

- `/data/WYC/signLanguage/work/scripts/holistic_sampling_probe.py`

可视化脚本为：

- `/data/WYC/signLanguage/work/scripts/plot_holistic_probe_summary.py`
- `/data/WYC/signLanguage/work/scripts/recommend_keyframes_from_probe.py`
- `/data/WYC/signLanguage/work/scripts/visualize_holistic_features.py`

当前这版探针与关键帧建议的采样范围需要先说明清楚：

- 探针按“每 4 帧采样一次”运行。
- 单视频最多只处理 12 个采样帧。
- 因此当前结果并不是覆盖全视频末尾，而是只覆盖视频前段到中段。
- 具体来说，像 `花.mp4`、`虎.mp4`、`月亮.mp4` 这类较长视频，当前结果通常只覆盖到总时长的约 40% 到 50%。
- `唱歌.mp4` 这类较短视频覆盖更完整，约到总时长的 83% 左右。
- `跳.mp4` 因为视频本身更短，当前采样可以覆盖到末尾。

所以，下面的覆盖率、运动能量和关键帧建议，都是基于“固定间隔 + 固定上限”的前段采样结果，不能直接理解为整段视频的全局统计。

### 2.2 全量探针结论

在 10 个 demo 视频上运行后，得到的总体覆盖率如下：

- `pose` 平均覆盖率：`1.0`
- `face` 平均覆盖率：`1.0`
- `left hand` 平均覆盖率：`0.6383`
- `right hand` 平均覆盖率：`0.7067`

这说明：

- 主干和脸部关键点在当前 demo 数据里比较稳定。
- 双手才是主要的不稳定来源，尤其是左手更容易掉帧。

### 2.3 典型样本

高运动样本：

- `唱歌.mp4`
- 平均运动能量约 `78.83`
- 覆盖率：`pose=1.0, left=1.0, right=0.8333, face=1.0`

低覆盖样本：

- `花.mp4`
- 平均运动能量约 `5.76`
- 覆盖率：`pose=1.0, left=0.0, right=0.4167, face=1.0`

这个对比很重要，因为它说明当前数据中存在两类典型情况：

- 动作本身变化大，适合做时序对齐和关键帧抓取
- 动作可见性差，适合重点检查遮挡、镜像和构图偏置

### 2.4 关键帧建议

`recommend_keyframes_from_probe.py` 已经把高运动帧、双手出现/消失边界帧和推荐采样点算出来了。

需要注意的是：当前推荐关键帧仍然继承了上面的采样范围限制，也就是只基于前段采样帧生成，不是对全视频做完整时间搜索。对于动作开始较晚的视频，这会漏掉后半段动作，因此后续要改成整段视频覆盖或两阶段采样。

两个最有代表性的样本是：

- `唱歌.mp4`
  - 推荐关键帧：`4, 8, 24, 32, 36`
  - 建议：动作幅度较大，采样应优先覆盖转折点
- `花.mp4`
  - 推荐关键帧：`4, 28, 32, 36`
  - 建议：左手覆盖偏低，需要优先检查左侧遮挡、镜像和画面边缘裁切

### 2.5 可视化结果

下面附上本次最关键的结果图。该组可视化已按最新脚本重跑，中文标题与状态栏已修正。

#### 2.5.1 全量覆盖率分布

![Holistic 全量覆盖率分布图](/data/WYC/signLanguage/work/generated/holistic_probe_20260428_full/analysis/holistic_coverage_by_video.png)

#### 2.5.2 全量运动能量分布

![Holistic 全量运动能量分布图](/data/WYC/signLanguage/work/generated/holistic_probe_20260428_full/analysis/holistic_motion_by_video.png)

#### 2.5.3 高运动样本 `唱歌.mp4`

![唱歌样本关键点可视化](/data/WYC/signLanguage/work/generated/holistic_viz_20260428/唱歌/唱歌_contact_sheet.png)

#### 2.5.4 低覆盖样本 `花.mp4`

![花样本关键点可视化](/data/WYC/signLanguage/work/generated/holistic_viz_20260428/花/花_contact_sheet.png)

### 2.6 这条 TODO 的结论

`MediaPipe Holistic` 作为当前评测主线是可行的，原因有两个：

1. `pose` 和 `face` 覆盖率稳定，说明基础骨架和面部信息足够可靠。
2. 双手覆盖差异明显，正好可以作为后续评分和反馈模块的重点修正对象。

当前 demo 已经能支持以下后续动作：

- 按关键帧加密采样
- 按关节统计偏差
- 把低覆盖样本作为构图和遮挡排查样本
- 为后续 `DTW` 对齐和逐点评分预留输入

但要让关键帧采样真正适用于“动作开始较晚”的视频，下一步必须先把采样范围从“前段截断”改成“覆盖全时长”。

## 3. 当前阶段的整体判断

这一天的工作实际上把项目从“想法”推进到了“可复用链路”：

- 资料层：已经有结构化盘点和量化模板
- 视觉层：已经有 `Holistic` 探针、结果分析和可视化
- 策略层：已经能据此给出关键帧建议和采样密度建议

下一步更适合直接往评分闭环推进，而不是继续停留在纯调研。

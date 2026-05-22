# 语义加权 DTW 与语义相位对齐更新

- 时间：`2026-05-23 04:20 CST`
- 项目：`/data/WYC/signLanguage`
- 口径：demo-only 工程验证；仍不是已校准的真实用户评分阈值。

## 背景

本轮确认采用“语义加权 DTW”为主线，而不是为每个词条分别写一套独立规则函数。资料文档仍作为主语义来源，标准视频用于补充具体形态、幅度和相位细节。

核心判断是：只要把 DTW 的输入限制为文档语义指定的关键特征，并对无关脸、躯干、非重点手等做低权重或 mask，再按关键动态帧做相位加权，DTW 本身就可以承担大部分“动作语义是否一致”的识别任务。

## 实现更新

### 1. 手形权重语义化

`score_holistic_sequence_mvp.py` 中修正了手形 group 的数字权重解释：

- 过去在 `left_hand_shape/right_hand_shape` 中，`8`、`12` 等数字可能被当作手形向量下标。
- 现在数字会优先映射为真实手指语义：
  - `4/1` -> 拇指相关手形特征
  - `8/5` -> 食指相关手形特征
  - `12/9` -> 中指相关手形特征
  - `16/13` -> 无名指相关手形特征
  - `20/17` -> 小指相关手形特征
- `opening/spread/index/middle/thumb` 等别名继续保留。

这使 `花` 的张开、`跳` 的食指/中指弯曲伸直等权重更贴近文档语义。

### 2. 语义相位

新增 `semantic_phase`：

- 先基于当前语义 profile 的重点组计算逐帧动态权重。
- 再用动态权重的累计能量把每帧映射到 `[0, 1]` 的语义进度。
- 这个进度不等同于帧号；开头/结尾静止段不会主导语义进度。

DTW 局部距离现在包含轻量 `semantic_phase_gap` 惩罚，使标准和测试更倾向对齐同一语义阶段，而不是机械对齐相近帧号。

### 3. start/mid/end 锚点一致性

新增三个默认语义锚点：

- `0.10`：核心动作起始附近
- `0.50`：核心动作中段
- `0.90`：核心动作结束附近

评分会比较标准和测试在这些语义相位上的关键特征距离，作为 `semantic_anchor_penalty`。这个惩罚比完整规则函数更轻，但能约束“起点、中点、终点动态语义一致”。

### 4. 帧数差异鲁棒性

新增 `semantic_phase_trim_tolerance`：

- 如果完整序列策略下 DTW 已经找到非常接近的核心路径，适度裁剪前后缀不再被当成语义错误。
- 这解决了 `花` 的 `trim_end_20pct` 被相位锚点压低的问题。

同时增强了手部主导动作的重提取噪声补偿：

- 仅在 hand-dominant profile、DTW 距离很低、总距离仍较低、手部检出充分时生效。
- 用于抵消同一 demo 经过网页 JPEG/MediaPipe 重新提取后的轻微手点漂移。

## profile 与数据库

已更新 profile 生成脚本：

- `/data/WYC/signLanguage/work/scripts/build_semantic_weight_profiles.py`
- 输出 JSON：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 输出说明：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.md`

profile 中新增 `semantic_dtw` 配置：

- `enabled`
- `local_phase_weight`
- `anchor_penalty_weight`
- `anchor_phases`

模板库审计已刷新：

- 审计目录：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/template_semantic_phase_dtw_audit_v1`
- 审计结果：`10/10 ok`
- 模板根目录：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`

## 关键验证

### 花

- 结果目录：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/花_semantic_phase_dtw_v3`
- 正例最低：`83.213`
- 负例最高：`29.534`
- margin：`53.679`
- 门控：通过

`花` 当前主逻辑：主手手形 opening/spread 和主手运动高权重，face/pose 为 0，完整序列语义加权 DTW 保留上下文，同时用语义相位减少帧数差异影响。

### 跳

- 结果目录：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/跳_semantic_phase_dtw_v3`
- 正例最低：`79.579`
- 负例最高：`39.639`
- margin：`39.940`
- 门控：通过

`跳` 当前主逻辑：右手食指/中指弹跳为主语义，左手地面为必要参照，face/pose 为 0，使用短动作语义窗口 DTW。

### 5080 API

评分模块已通过热加载更新，不重启常驻 Holistic worker：

- `POST /api/admin/reload-scoring`
- `reload_count=5`
- 常驻 worker PID：`4148683`

API 冒烟测试：

- `花`：request `web_20260523_041443_0292d680`，score `75.501`
- `跳`：request `web_20260523_041447_f7341789`，score `80.586`

说明：这次只热加载评分脚本，未重启 `5080` FastAPI 框架进程，因此框架级返回字段新增项会在下次后端框架重启后完整体现；评分算法本身已经在当前 worker 上生效。

## 全库观察

全库最终摘要：

- `/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_words_semantic_phase_dtw_v2/summary.md`

当前只有 `花` 和 `跳` 通过统一工程门槛。其他词条的负例普遍已经较低，但通用正例扰动仍不合适：

- `唱歌`、`谗（羡慕）` 等含脸/嘴阶段，直接裁开头会破坏语义。
- `月亮`、`汽车`、`虎` 等多阶段或周期动作，统一 `trim_start_20pct/trim_end_20pct/subsample_even` 不能代表合理用户变体。

因此后续全库验证应改为“每词条专属正例扰动”，而不是把同一套裁剪规则套到所有词。

## 当前结论

语义加权 DTW 是当前最适合的主路线：

1. 文档资料决定重点特征、mask、手性、关键手指和动态相位。
2. 标准视频校准幅度、速度范围、相位曲线和局部轨迹。
3. DTW 只在这些语义特征上做宽松对齐。
4. 规则谓词暂时只作为诊断补充，不作为主评分主体。

下一步应补充 `semantic_feature_weights` 的显式字段，把 opening、spread、finger_flex、two_hand_distance、mouth_open 等派生特征从当前 keypoint/alias 机制进一步结构化，并为每个词条建立合理正例扰动方案。

## 2026-05-23 04:35 补充：坐姿与非重要特征鲁棒性

用户实际使用时可能是坐姿，而标准样本更接近站姿。为避免坐姿/站姿差异通过躯干坐标间接影响手部评分，本轮进一步调整：

1. 对纯手部语义动作，手部 landmark 距离优先使用 wrist-relative 的局部手部几何。
2. 手部整体在身体坐标中的全局位置只保留小权重残差，例如 `花` 的 `hand_global_position_weight=0.06`，`跳` 为 `0.08`。
3. 暂时关闭逐相邻帧 motion group 作为主 DTW 输入，因为隔帧采样会天然改变相邻帧位移幅值，容易误伤 `subsample_even` 正例。
4. 继续保留更稳的相对信号：手形相对特征、语义相位、起止/中段语义锚点、序列级 motion/roughness 统计。

最终验证：

- 模板审计：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/template_pose_robust_no_adjacent_motion_audit_v1/template_semantic_weight_audit.md`，`10/10 ok`。
- `花`：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/花_pose_robust_v1/`，正例最低 `83.213`，负例最高 `31.147`，margin `52.066`，通过。
- `跳`：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/跳_pose_robust_v1/`，正例最低 `80.088`，负例最高 `39.639`，margin `40.448`，通过。
- 合成坐姿压力测试：将手部整体向下平移 `0.45` 个归一化坐标单位模拟坐姿/镜头高度差，`花` 得分 `97.470`，`跳` 得分 `93.125`。
- 5080 API 热加载后冒烟：`花` request `web_20260523_043442_e00f8b9c` 得分 `75.493`，`跳` request `web_20260523_043446_cbecd916` 得分 `81.071`；Holistic worker PID 仍为 `4148683`。

结论：当前版本已经明显降低了非重要 pose/躯干和手部全局位置对纯手部词条的干扰。后续如果需要显式使用“移动方向”，应优先做语义相位级、片段级方向判断，而不是把逐相邻帧位移直接加入主 DTW 距离。

## 2026-05-23 04:46 补充：网页测试数据回放复查

根据“算法调整都要进行网页测试数据复查”的要求，本轮已新增并执行保存网页/API 样本回放脚本：

- 脚本：`/data/WYC/signLanguage/work/scripts/replay_web_scoring_samples.py`
- 最新输出：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_replay_pose_robust_v3/web_replay_current.md`
- JSON：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_replay_pose_robust_v3/web_replay_current.json`
- CSV：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_replay_pose_robust_v3/web_replay_current.csv`
- 复查口径：读取已保存的 `work/generated/web_scoring_mvp/web_*/scoring_result.json` 和对应 `Holistic` JSON，用当前评分模块重新计算，不重新运行浏览器采集，也不重新初始化常驻 `Holistic` worker。

执行命令：

```bash
/home/wuyangcheng/myenv/bin/python /data/WYC/signLanguage/work/scripts/replay_web_scoring_samples.py \
  --web-root /data/WYC/signLanguage/work/generated/web_scoring_mvp \
  --semantic-profile-json /data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json \
  --output-dir /data/WYC/signLanguage/work/generated/scoring_mvp_run3/web_replay_pose_robust_v3
```

最新快照结果：

- 保存网页/API 样本数：`111`
- 回放错误数：`0`
- `normal_like >= 75`：`14`
- `60 <= borderline < 75`：`1`
- `low < 60`：`96`
- 旧均分：`33.129`
- 新均分：`34.738`
- `花`：`62` 条，正常 `6`、边界 `1`、低分 `55`，新均分 `45.979`，手部覆盖均值 `0.715`
- `跳`：`39` 条，正常 `8`、边界 `0`、低分 `31`，新均分 `23.283`，手部覆盖均值 `0.738`
- `香蕉`：`10` 条，正常 `0`、边界 `0`、低分 `10`，新均分 `9.716`，手部覆盖均值 `0.553`

代表性观察：

- 标准 demo 帧切片通过 `/api/score` 的网页路径仍可得到正常分：`花` request `web_20260523_043442_e00f8b9c` 得分 `75.493`，`跳` request `web_20260523_043446_cbecd916` 得分 `81.071`。
- 多个真实网页测试样本仍低分。例如 `花` 的 `web_20260523_043923_b95a60d0` 得分 `57.852`，手部覆盖 `0.733`；`跳` 最新几条 `web_20260523_044323_2eb9eb7e`、`web_20260523_044336_5d15d099`、`web_20260523_044358_00db9d4d` 得分分别为 `10.393`、`13.288`、`7.193`，手部覆盖约 `0.720-0.800`。
- 这说明当前问题不能简单归因为 `Holistic` 完全漏手或后端路径未生效；至少一部分样本是关键手形、关键手指动态、动作窗口或实际动作语义与标准样本差异较大。

结论与约束：

- 本轮算法改动通过了离线 `花/跳` demo 判别门控，也通过了标准 demo 帧切片的 5080 API 冒烟。
- 但保存的真实网页测试回放没有整体进入正常分区，因此不能宣称“真实网页测试已经正常打分”。
- 后续任何评分算法、语义 profile、模板权重、对齐策略或分数尺度改动，都必须同步运行 `replay_web_scoring_samples.py`，并在报告中记录网页样本快照的 normal/borderline/low 分布。
- 下一步更合理的排查方向是对低分网页样本生成骨架级诊断图：手部覆盖时间线、语义动态权重曲线、标准/测试关键手指开合曲线、DTW 对齐路径和最大扣分 group，而不是直接全局放松阈值。

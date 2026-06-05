# 手语打分算法优化详细报告

生成时间：`2026-06-05 15:00:00 CST`  
项目路径：`/data/WYC/signLanguage`  
核心脚本：`/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py`  
当前模板库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`  
语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`

## 1. 摘要

当前手语打分算法已经从早期“关键点序列 + 普通 DTW”的原型，演进为“文本语义 profile + dense Holistic 时间序列 + 动态帧权重 + 语义相位加权 DTW + 词条级语义守卫 + 多层鲁棒性质量门”的工程化 MVP。

当前算法主线仍然是可解释的关键点级相似度评分，而不是端到端黑盒分类。它的目标是在缺少真实用户样本和人工评分标签的阶段，先形成一个可复查、可回放、可诊断、可持续加固的原型评分闭环。

截至本报告整理时，当前 5080 运行态为：

| 项目 | 当前值 |
| --- | --- |
| 5080 后端 | `ready` |
| Holistic worker PID | `3896404` |
| Holistic 初始化耗时 | `260.114s` |
| 当前模板数 | `10` |
| 当前 scorer 加载时间 | `2026-06-05T14:08:09` |
| 当前 scorer reload_count | `0`，因为本轮是新启动后端后首次加载 |
| last_reload_error | `null` |

最新完整质量门为：

```text
/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_partial_hand_bone_length_74gate_v1/flower_jump_quality_gate.md
```

关键结果：

| 指标 | 结果 |
| --- | ---: |
| 综合质量门 | `PASS` |
| 子门数量 | `74` |
| 子门失败数 | `0` |
| 保存网页/API replay 样本 | `168` |
| replay 错误 | `0` |
| 花/跳 diagnostics 样本 | `149` |
| diagnostics 错误 | `0` |
| 有效采集 | `128` |
| 有效正常+边界 | `124` |
| 有效低分 | `4` |
| 有效正常+边界率 | `96.9%` |

重要限制：这些结果仍然是工程 sanity check 和保存网页样本回放结果，不能解释为正式真实用户评分准确、阈值已校准或可泛化到所有人群/设备/环境。

## 2. 算法演进总览

当前算法优化大致经历了六个阶段：

| 阶段 | 核心变化 | 解决的问题 |
| --- | --- | --- |
| 基础 landmark DTW | 从 raw Holistic JSON 读取 pose/hand/face，做归一化和 DTW | 形成可运行的相似度评分原型 |
| 判别性门控 | 增加目标正例扰动、其他 demo 负例、随机假动作负例 | 避免 `花` vs 其它动作区分度弱 |
| 文本语义加权 | 从 `Demo词汇.docx` 生成每词 group/keypoint 权重 | 避免无关 pose/face/非重点手拖累评分 |
| 动态帧权重与语义相位 | 模板/查询按关键动作能量生成 frame weight 和 semantic phase | 让 DTW 对齐语义阶段，而不是机械对齐帧号 |
| 词条级语义守卫 | `花` opening guard、`跳` two-hand relation/local fallback、相位顺序守卫等 | 防止局部相似但语义错误的样本被抬高 |
| 鲁棒性质量门 | 74 个子门覆盖取景、时序、坐标、手部拓扑、缺失、抖动、混淆等 | 把算法从 demo-only 试验推进到可复测工程闭环 |

## 3. 当前总体流程

当前评分流程如下：

```text
浏览器上传帧 / demo 模板缓存
  |
  v
raw MediaPipe Holistic JSON
  |
  v
结构清洗、时间元数据清洗、landmark 合法性清洗
  |
  v
pose / left_hand / right_hand / face / hand_shape / two_hand_relation 特征构建
  |
  v
身体尺度归一化 + 手部局部几何鲁棒距离
  |
  v
加载目标词语义 profile，生成 group/keypoint 权重
  |
  v
动态帧权重、语义动作窗口、semantic_phase
  |
  v
语义相位加权 DTW + 序列级惩罚
  |
  v
词条级 semantic floor / guard / cross-word check
  |
  v
prototype_score + capture_quality + 语义诊断字段
```

评分结果的主字段是：

| 字段 | 含义 |
| --- | --- |
| `prototype_score` | 当前 demo 模板原型相似度，0-100 |
| `dtw_distance` | DTW 对齐后的加权局部距离 |
| `normalized_distance` | DTW 距离叠加序列级惩罚后的距离 |
| `group_mean_distance` | 各语义组平均距离 |
| `sequence_penalty` | 长度、presence、motion、roughness、endpoint 等惩罚 |
| `score_scale` | 语义 floor、守卫、capture quality、相位顺序等诊断 |
| `alignment_policy` | 当前使用完整序列、动作窗口或混合对齐的策略信息 |

## 4. 数据表示优化

### 4.1 从 bbox 兼容模式转向 raw landmark 主模式

早期脚本支持旧 bbox 摘要，但 bbox 只能表达粗略位置，无法稳定表达手指形状、开合、双手关系和细粒度语义。实验中旧 bbox 对负例区分度弱，因此当前主路线已明确为 raw landmark。

当前支持：

- pose：`33` 点，当前核心使用 nose、shoulder、elbow、wrist、hip 等关键点。
- hand：左右手各 `21` 点。
- face：`478` 点中选取眼、嘴等核心点。
- bbox：仅作为旧缓存兼容诊断，不作为主评分路线。

### 4.2 step2 dense 模板库

当前标准模板库为 step2 dense Holistic 缓存：

```text
/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results
```

模板帧数：

| 词条 | dense 帧数 |
| --- | ---: |
| 唱歌 | 27 |
| 指示 | 30 |
| 月亮 | 47 |
| 朋友 | 28 |
| 汽车 | 44 |
| 花 | 53 |
| 虎 | 54 |
| 谗（羡慕） | 32 |
| 跳 | 19 |
| 香蕉 | 42 |

相较 step4 缓存，step2 模板保留了更多动作过渡帧，能够更好支持开合、弹跳、轨迹方向和语义相位判断。

### 4.3 缓存优先策略

MediaPipe Holistic 初始化在当前服务器上通常约 `260s`，而单帧处理远低于初始化成本。因此当前算法验证坚持：

- candidate generation 只负责生成 raw Holistic JSON。
- scoring 只读缓存 JSON。
- visualization 只读缓存 JSON。
- 回归和质量门不重新跑 Holistic、不重启 5080。

这使每次算法修改后的验证可以稳定复现，不被 Holistic 初始化和随机实时采集噪声干扰。

## 5. 特征工程优化

### 5.1 group 结构

当前评分中重要 group 包括：

| group | 作用 |
| --- | --- |
| `left_hand` / `right_hand` | 手部 21 点轨迹与几何 |
| `left_hand_shape` / `right_hand_shape` | 手指尖距离、spread、伸直度、MCP-tip 距离等派生手形特征 |
| `pose` | 非重点身体姿态、归一化锚点和少量动作辅助 |
| `face` | 口型/面部相关词条的辅助特征 |
| `two_hand_relation` | 双手相对位置和关系变化，尤其用于 `跳` |
| relative motion groups | 仅在语义 profile 指定时加入，避免隔帧采样误伤 |

### 5.2 手形派生特征

`left_hand_shape/right_hand_shape` 不直接依赖全局位置，而从手部局部结构派生：

- wrist-tip 距离。
- 指间 spread。
- MCP-tip 距离。
- 手指伸直度。
- 拇指、食指、中指、无名指、小指语义映射。

这样可以表达：

- `花`：撮合到张开，opening/spread 过程。
- `跳`：右手食指/中指模拟小人双腿的弯曲伸直。
- `香蕉`：一手竖食指与另一手剥皮动作。

### 5.3 双手关系特征

`two_hand_relation` 用于描述双手之间的相对关系，不只是两只手分别像不像。它对 `跳` 尤其关键：

- 左手是地面。
- 右手食指/中指是小人。
- 右手需要相对左手向上弹跳。

因此 `跳` 的 profile 中 `two_hand_relation` 是 focus/required group。角色互换不被当作正确动作；而 `花` 这种单手主导动作允许左右惯用手互换。

## 6. 坐标归一化与清洗优化

### 6.1 Pose 归一化锚点加固

早期归一化主要依赖肩部中心和肩宽，但有限坏点可能污染肩部锚点，导致正确动作被打到接近 0。当前归一化锚点已经加固：

- 检查肩部绝对 x/y/z 边界。
- 检查肩宽范围。
- 检查肩-鼻、肩-髋拓扑。
- 检查 pose wrist 与 hand wrist 的 x/y 一致性。
- 检查序列级 shoulder-hand z 中位数。
- 稀疏坏肩点按 record 顺序插值。
- 整段肩部不可信时使用 hand center / palm-scale fallback。

最新 pose normalization anchor 门：

| 指标 | 结果 |
| --- | ---: |
| 正常有肩 pose 帧 | `4776/4776` 可信 |
| `花` 正向最低 | `78.039` |
| `跳` 正向最低 | `76.227` |
| 子门状态 | `PASS` |

### 6.2 hand/face 坐标清洗

当前清洗规则包括：

- hand/face `z` 超出 `[-1.0, 1.0]` 的点按缺失处理。
- hand/face exact-zero `(0,0,0)` 占位点按缺失处理。
- hand 整手 x/y span 小于 `0.012` 的 near-collapsed tracker artifact 置为缺失。
- 非标准非空 landmark 数组长度直接按整组缺失处理。

这些规则解决了有限但语义无效的 tracker 输出被当作真实手形参与评分的问题。

### 6.3 hand identity 与解剖拓扑清洗

针对 exact-length 但 landmark 身份损坏的输入，当前新增多类手部完整性检查：

| 清洗类型 | 规则与目的 |
| --- | --- |
| wrist 根身份 | MediaPipe hand 的 wrist index 0 应接近 z 原点，`|z0| > 2e-6` 时整手缺失 |
| 内部拓扑 | 多指链明显反向、backtrack 或 proximal/distal 比例异常时整手缺失 |
| landmark 碰撞 | 非量化手中多个点三维距离 `<=1e-5` 时屏蔽碰撞参与点 |
| 骨段长度 | 相邻指骨长度相对 palm scale 超出 `[0.003, 2.0]` 时屏蔽异常骨段参与点 |
| 部分可见骨段 | wrist 可见、点数足够、palm refs 足够时也检查部分可见手，防止先缺点再绕过完整手规则 |

正常数据审计结果：

| 审计项 | 结果 |
| --- | ---: |
| hand frame 数 | `4750` |
| wrist identity violation | `0` |
| internal topology violation | `0` |
| raw hand landmark collision | `0` |
| hand bone length violation | `0` |
| hand bone segments | `71250` |

## 7. 时间元数据与结构鲁棒性优化

### 7.1 frame_idx / timestamp / fps 清洗

当前已统一清洗：

- `fps`
- `total_frames`
- `frame_idx`
- `timestamp_sec`

规则：

- 非有限、字符串、负数、极大值不再导致崩溃。
- record/row 双来源中优先采用仍有效的同帧副本。
- 无效总帧数从可靠 frame index 恢复。
- timestamp 异常时回退到 `frame_idx/fps`。
- frame index 非严格递增、重复或越界时按原 record 顺序生成稳定时间轴。

时间元数据门最新结果：

| 词条 | 正向最低分 |
| --- | ---: |
| 花 | `100.000` |
| 跳 | `100.000` |

### 7.2 JSON 结构入口清洗

当前 `load_sequence()` 对局部损坏更稳健：

- 非 dict record 按空帧保留时序。
- 非 dict result_data 按局部缺失处理。
- 非 list landmark group 按缺失处理。
- 非 dict landmark point 按缺失处理。
- bbox group/bbox 错类型和非有限框值回退有限默认。
- 错类型 sidecar 被安全忽略。

结构 JSON 门：

| 词条 | 正向最低分 | 最弱结构损坏变体 |
| --- | ---: | --- |
| 花 | `99.016` | `mid_record_null` |
| 跳 | `70.714` | `mid_right_hand_point_null` |

## 8. 语义 profile 与语义加权优化

### 8.1 从文档生成 profile

当前 profile 由脚本从 `Demo词汇.docx` 生成：

```text
/data/WYC/signLanguage/work/scripts/build_semantic_weight_profiles.py
/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json
```

profile 定义：

- group 权重。
- focus groups。
- 是否允许左右手互换。
- 必要 presence groups。
- 关键手指/关键节点权重。
- 语义 DTW 参数。
- 词条级守卫阈值。

### 8.2 `花` 的语义重点

`花` 的核心语义：

- 一只手撮合。
- 手缓慢向上同时张开。
- 重点是手指 opening/spread 过程。
- pose/face 基本不参与核心评分。
- 允许左右惯用手互换。

当前算法通过：

- `right_hand_shape / left_hand_shape`
- opening/spread keypoint 权重
- `flower_opening_guard`
- `short_visible_core` floor
- `flower_jump_confusion_guard`

来共同约束。

### 8.3 `跳` 的语义重点

`跳` 的核心语义：

- 左手是地面。
- 右手食指/中指是小人两条腿。
- 右手需要相对左手完成从下向上的弹跳。
- 双手角色不能随意互换。

当前算法通过：

- `two_hand_relation`
- `right_hand_shape`
- `required_presence_groups=["left_hand","right_hand","two_hand_relation"]`
- `jump_relation_semantic_floor`
- `full_sequence_local_relation_segment` fallback
- two-finger shape guard

来共同约束。

## 9. 动态帧权重与语义相位优化

### 9.1 动态帧权重

当前标准序列和查询序列都会计算动态帧权重：

- 读取前端上传的 `frame_weight`。
- 结合语义 profile 的重点 group。
- 计算关键 group 的运动能量。
- 生成归一化帧权重，范围经过清洗和裁剪。

当前权重清洗：

| 参数 | 当前值 |
| --- | ---: |
| `FRAME_WEIGHT_MIN` | `0.05` |
| `FRAME_WEIGHT_RAW_MAX` | `10.0` |
| pair temporal weight 范围 | `0.20` 到 `3.50` |

异常权重清洗门结果：

| 词条 | 正向最低分 | 反向权重诊断最低分 |
| --- | ---: | ---: |
| 花 | `99.161` | `99.347` |
| 跳 | `76.297` | `10.120` |

`跳` 的反向权重被压低是合理的：它会把错误阶段当成重点，破坏短促动作语义。

### 9.2 semantic_phase

当前每帧都有 `semantic_phase`：

- 根据语义帧权重累计能量映射到 `[0,1]`。
- 静止准备段不会主导语义进度。
- DTW 局部距离加入轻量 semantic phase gap penalty。
- start/mid/end 语义锚点参与序列惩罚。

这解决了“帧号相似但语义阶段错位”的问题。

### 9.3 相位顺序守卫

相位顺序守卫使用语义锚点：

```text
[0.10, 0.25, 0.50, 0.75, 0.90]
```

它会寻找查询序列中最接近标准锚点的帧，并计算大跨度乱序指标。如果动作出现倒放、先做结束姿态再做开始、跳过中段等情况，守卫会把得分封顶。

当前相位顺序守卫的分数上限通常为 `45.0`。

## 10. DTW 与序列级惩罚优化

### 10.1 语义加权 DTW

当前 DTW 不再对所有坐标一视同仁，而是按 profile 权重和 keypoint 权重计算局部距离：

- 无关 group 权重降为 0 或很低。
- 手形关键维度加权。
- `two_hand_relation` 对双手角色词加权。
- hand-dominant 词条弱化非核心 pose/face。

这使 `花` 不再被脸、躯干和非核心手拖低；`跳` 不再只看右手局部形状，而会要求左手地面和右手弹跳关系。

### 10.2 序列级惩罚

当前保留多类序列惩罚：

| 惩罚项 | 作用 |
| --- | --- |
| `length_penalty` | 防止过短样本高分 |
| `presence_penalty` | 防止关键手缺失仍高分 |
| `motion_penalty` | 检查整体运动量 |
| `roughness_penalty` | 抑制乱序、随机游走、异常抖动 |
| `info_penalty` | 样本信息量不足时扣分 |
| `endpoint_penalty` | 起止状态不一致扣分 |
| `semantic_anchor_penalty` | 语义相位锚点不一致扣分 |
| `required_presence_penalty` | 必要手/关系缺失时扣分 |

最终分数仍基于：

```text
normalized_distance = dtw_distance + total_sequence_penalty
prototype_score = 100 * exp(-normalized_distance / SCORE_SCALE)
SCORE_SCALE = 0.12
```

但后续语义 floor 和 guard 可能对 `prototype_score` 做有条件抬高或封顶。

## 11. 混合对齐策略优化

### 11.1 早期 action-window 的问题

早期尝试对所有词条使用动作窗口 DTW。这个策略对 `跳` 有帮助，但对 `花` 的真实网页样本会过度裁剪，因为用户开花动作的能量峰位置不稳定。

### 11.2 当前策略

当前采用混合策略：

| 词条类型 | 当前策略 |
| --- | --- |
| 长动作 / 上下文敏感动作，如 `花` | 使用完整序列语义加权 DTW，动作窗口主要作为诊断 |
| 短促动作，如 `跳` | 使用语义动作窗口 DTW，并允许局部弹跳段 fallback |

这样避免 `花` 被错误裁剪，同时保留 `跳` 对短促核心动作的敏感性。

## 12. 词条级 semantic floor 与 guard

### 12.1 capture_quality

当前 score 中包含：

```text
score_scale.capture_quality
```

状态：

| 状态 | 含义 |
| --- | --- |
| `score_valid` | 核心证据足够，可参考 prototype score |
| `needs_recapture` | 关键点覆盖或采集质量不足，建议重采 |
| `semantic_mismatch` | 采集质量足够但动作语义不匹配 |

这个字段只用于质量解释，不直接改变 `prototype_score`。

### 12.2 `花` opening guard

`flower_opening_guard` 用于确认 `花` 必须有撮合到张开的 opening/spread 动态。它防止局部手形相似但没有开花动作的样本被抬高。

典型逻辑：

- 如果张开动态弱，即使局部手形相似也不能被 `short_visible_core` 或 visible-core tolerance 抬高。
- 如果动作更像双手交互或 `跳`，触发 `flower_jump_confusion_guard`。

最新离线判别门：

| 词条 | 正例最低 | 负例最高 | margin |
| --- | ---: | ---: | ---: |
| 花 | `80.311` | `33.735` | `46.575` |

### 12.3 `花` short visible core

对于浏览器短视频中只捕获到核心开花段的情况，`short_visible_core` semantic floor 可以有限抬分。但必须满足：

- 是 `花`。
- 核心手覆盖足够。
- opening guard 通过。
- core DTW 足够近。
- 动作窗口能量覆盖足够。
- 主手几何不远。
- 相位顺序守卫未阻断。

它最多把清楚的短核心段抬到 borderline/normal 附近，不给满分。

### 12.4 `跳` relation floor 与 local fallback

`跳` 的低分曾主要来自两类：

- 双手覆盖不足。
- 动作窗口起止相位不准，导致 relation_direction_mismatch。

当前策略不是放松全局阈值，而是新增 guarded local fallback：

- 在完整序列中搜索局部双手关系段。
- 要求方向 cosine 高。
- 要求纵向幅度强。
- 要求横向漂移低。
- 要求覆盖率足够。
- 要求右手两指手形通过，避免 `汽车`、`谗（羡慕）` 等被误抬高。

最新 `跳` 判别门：

| 词条 | 正例最低 | 负例最高 | margin |
| --- | ---: | ---: | ---: |
| 跳 | `76.823` | `31.418` | `45.406` |

### 12.5 花/跳交叉检查

当前在线 web scoring 还包含花/跳 cross-word check：

- `花` 样本同时按 `跳` 模板评估。
- `跳` 样本同时按 `花` 模板评估。
- 目标分必须显著高于交叉词分。

保存网页交叉混淆门：

| 目标词 | eligible | pass | fail | 交叉最高 | margin 最低 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 花 | 87 | 87 | 0 | `8.218` | `59.840` |
| 跳 | 37 | 37 | 0 | `41.535` | `29.317` |

## 13. 网页回放闭环优化

当前规则：每次评分算法、语义 profile、score scaling、alignment policy 或 template weight 变化后，都必须回放保存网页/API 样本。

当前回放脚本：

```text
/data/WYC/signLanguage/work/scripts/replay_web_scoring_samples.py
/data/WYC/signLanguage/work/scripts/analyze_web_scoring_diagnostics.py
/data/WYC/signLanguage/work/scripts/run_flower_jump_web_regression.py
```

最新质量门中的网页回放结果：

| 指标 | 结果 |
| --- | ---: |
| replay 样本 | `168` |
| replay 错误 | `0` |
| 花/跳 diagnostics | `149` |
| diagnostics 错误 | `0` |
| 有效采集 | `128` |
| 有效正常+边界 | `124` |
| 有效低分 | `4` |
| 有效正常+边界率 | `96.9%` |

分词结果：

| 词条 | 有效采集 | 正常+边界 | 有效低分 | 有效率 | 有效均分 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 花 | 91 | 87 | 4 | 95.6% | 75.775 |
| 跳 | 37 | 37 | 0 | 100.0% | 76.677 |

剩余 `花` 有效低分主要是 `flower_opening_guard_failed`，属于开花动态不足，不应通过放松 opening guard 直接抬高。

## 14. 统一质量门体系

当前综合质量门包含 `74` 个子门，覆盖：

1. 保存网页回归。
2. 保存网页交叉混淆。
3. 合成鲁棒变体交叉混淆。
4. 离线正负例判别。
5. pose/camera/framing/aspect/camera roll/body anchor/depth/mirror 等取景与姿态扰动。
6. hand role、hand label flicker、hand dropout burst 等手部检测扰动。
7. frame count、stutter、temporal rate、padding、crop、repeat、order jitter 等时间扰动。
8. frame weight、coordinate precision、motion blur、landmark noise/spike 等浏览器/识别噪声。
9. fingertip/palm/mid-joint occlusion、missing mask、edge clipping 等遮挡缺失。
10. two-hand relation、core shape amplitude、noncore hand distractor 等语义扰动。
11. perspective shear、rolling shutter、hand stream latency、interhand desync 等摄像头/流式效应。
12. finite/bounded coordinate、temporal metadata、structural JSON 等输入健壮性。
13. pose normalization anchor、landmark cardinality、hand wrist identity、hand internal topology、hand collision、hand bone length integrity 等结构安全。

质量门输出：

```text
/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260604_partial_hand_bone_length_74gate_v1/flower_jump_quality_gate.md
```

子门全部 PASS：

| 项目 | 结果 |
| --- | ---: |
| 子门数 | `74` |
| 返回码为 0 的子门 | `74` |
| 失败子门 | `0` |

## 15. 代表性鲁棒性结果

### 15.1 负例判别

| 目标词 | 正例最低 | 负例最高 | margin | 最强负例 |
| --- | ---: | ---: | ---: | --- |
| 花 | `80.311` | `33.735` | `46.575` | `other_demo_谗_羡慕` |
| 跳 | `76.823` | `31.418` | `45.406` | `fake_static_hold` |

### 15.2 合成鲁棒变体交叉混淆

| 目标词 | cases | pass | fail | 目标最低 | 交叉最高 | margin 最低 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 花 | 10 | 10 | 0 | `76.727` | `8.506` | `70.776` |
| 跳 | 10 | 10 | 0 | `70.708` | `25.551` | `55.428` |

### 15.3 取景与摄像头扰动

| 门 | 花最低 | 跳最低 | 说明 |
| --- | ---: | ---: | --- |
| pose robustness | `80.446` | `93.015` | 坐姿/手部平移/轻微 jitter |
| framing | `79.448` | `70.708` | zoom、偏移、轻微倾斜 |
| aspect ratio | `80.345` | `85.975` | 轻中度非等比拉伸 |
| camera roll | `81.180` | `89.634` | ±20 度整体倾斜 |
| depth | `73.923` | `70.469` | z offset / scale |
| mirror_x | `80.533` | `80.843` | 浏览器镜像 |

### 15.4 时间扰动

| 门 | 花最低 | 跳最低 | 说明 |
| --- | ---: | ---: | --- |
| frame count | `78.482` | `70.488` | 不同帧数采样 |
| temporal stutter | `93.869` | `72.011` | 短时冻结/重复 |
| temporal rate | `92.730` | `77.195` | 快慢速与局部速率扰动 |
| temporal padding | `97.862` | `79.124` | 前后静止段 |
| action crop | `97.958` | `80.750` | 轻度起止裁剪 |
| phase order | `79.410` | `69.389` | 正向动作保持，乱序封顶 |

### 15.5 手部结构与遮挡

| 门 | 花正向最低 | 跳正向最低 | 核心损坏表现 |
| --- | ---: | ---: | --- |
| landmark cardinality | `78.039` | `76.227` | 核心畸形降到 `1-2` 分级别 |
| wrist identity | `79.773` | `81.642` | 整段身份损坏低分/重采 |
| internal topology | `79.773` | `81.642` | PIP/DIP 等身份乱序低分 |
| landmark collision | `78.512` | `70.714` | 严重碰撞诊断最高约 `10` |
| bone length integrity | `78.512` | `70.714` | 极端骨段伸缩低分/语义失败 |
| edge clipping | `76.689` | `78.545` | 核心裁切最高约 `10-11` |
| fingertip occlusion | `95.829` | `70.469` | 核心指尖全缺低分 |
| palm anchor occlusion | `95.791` | `70.469` | 掌根锚点全缺低分 |

### 15.6 噪声与浏览器上传

| 门 | 花最低 | 跳最低 | 说明 |
| --- | ---: | ---: | --- |
| frame_weights | `99.161` | `76.297` | 前端非均匀权重与异常权重清洗 |
| coordinate precision | `80.805` | `96.833` | 量化/低精度坐标 |
| landmark noise | `76.064` | `72.810` | 小幅 hand landmark 噪声 |
| landmark spike | `92.772` | `70.469` | 单帧/稀疏跳点 |
| motion blur/amplitude | `79.074` | `75.662` | 轻度运动幅度变化，重 blur 仅诊断 |

## 16. 当前算法对 `花` 与 `跳` 的结论

### 16.1 `花`

当前 `花` 已经具备：

- 单手主导、左右惯用手容错。
- opening/spread 为核心语义。
- 非核心 pose/face/另一只手低权重。
- 完整序列语义加权 DTW。
- short visible core 有条件抬分。
- opening guard 防止“只有手形没有张开动态”的误高分。
- flower-jump confusion guard 防止 `跳` 样双手动作被当成 `花`。
- 剩余有效低分主要来自 opening 动态不足，属于合理低分。

当前质量门中的 `花` 网页有效数据：

| 指标 | 结果 |
| --- | ---: |
| 有效采集 | `91` |
| 正常+边界 | `87` |
| 有效低分 | `4` |
| 有效率 | `95.6%` |
| 有效均分 | `75.775` |

### 16.2 `跳`

当前 `跳` 已经具备：

- 左手地面、右手两指小人的角色约束。
- `two_hand_relation` 为核心语义。
- action-window 和 full-sequence local fallback 结合。
- two-finger shape guard 防止其它双手上移类动作被误抬高。
- role swap 作为负向诊断，不被当成正确动作。
- raw 低分主要来自双手 presence 不足时的重采建议，而非全局阈值过严。

当前质量门中的 `跳` 网页有效数据：

| 指标 | 结果 |
| --- | ---: |
| 有效采集 | `37` |
| 正常+边界 | `37` |
| 有效低分 | `0` |
| 有效率 | `100.0%` |
| 有效均分 | `76.677` |

## 17. 当前仍未完成的部分

虽然工程验证已经很强，但仍有明确限制：

1. 还没有真实用户视频流样本库。
2. 还没有人工评分标签。
3. `prototype_score` 还不是正式校准得分。
4. `75` 或 `60` 等当前分段只用于工程分析，不是用户合格线。
5. 目前重点优化和验证集中在 `花/跳`，其它词条还需要词条专属正例扰动和质量门。
6. 当前标准库仍是单 demo 模板为主，后续需要多示范者、多设备、多距离、多光照标准模板。
7. 正式完成门仍要求 marker 后真实网页摄像头 `花/跳` 双词样本出现并通过 watcher 诊断。

最新复测就绪报告仍为：

```text
/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_jump_retest_readiness_live_20260604_partial_hand_bone_length_74gate_postwatch_v1/flower_jump_retest_readiness.md
```

状态：

| 项目 | 结果 |
| --- | --- |
| ready_for_retest | `PASS` |
| goal_status | `NOT_READY` |
| next_step | `采集 花、跳` |
| 缺失词条 | `花、跳` |

## 18. 后续建议

建议下一阶段按以下顺序推进：

1. 使用当前 5080 页面完成 marker 后真实网页摄像头 `花/跳` 双词复测。
2. 对新增样本运行 watcher 自动诊断，查看 query/standard skeleton、presence timeline 和语义诊断。
3. 如果真实样本被判低分，优先区分 `needs_recapture`、`semantic_mismatch` 和算法误伤，不直接放松阈值。
4. 为其它词条建立专属正例扰动，而不是套用 `花/跳` 的通用裁剪/采样策略。
5. 扩展标准模板库到多示范者、多设备和多环境。
6. 引入人工评分标签后，重新校准 `prototype_score` 到用户可解释等级。
7. 将当前语义 profile 从脚本生成升级为可人工审核编辑的数据库表。

## 19. 结论

当前打分算法已经形成一条较稳的工程主线：

- 用 dense Holistic raw landmark 保留动作全过程。
- 用文档语义 profile 决定哪些特征重要。
- 用动态帧权重和 semantic phase 做语义阶段对齐。
- 用 DTW 保留速度差异鲁棒性。
- 用词条级 guard 防止局部相似误高分。
- 用 capture_quality 把动作错误和采集失败分开解释。
- 用 74 个质量子门防止算法在取景、时序、坐标、手部结构、遮挡、噪声和交叉混淆上回退。

因此，当前版本已经适合作为 `花/跳` 网页复测前的算法基线。正式用户评分结论仍需要真实用户样本和人工标签完成校准。

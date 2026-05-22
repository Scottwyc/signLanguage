# 手语评分语义加权更新报告

更新时间：2026-05-23 00:50:00 CST  
项目路径：`/data/WYC/signLanguage`

## 1. 问题

实际网页测试里，当前 prototype score 明显偏低。核心原因不是 Holistic 没有输出关键点，而是旧评分把身体、脸、双手坐标按固定组权重做 DTW，对“动作语义真正关键的局部特征”不够敏感。

例如“花”的文本说明是：

> 一手撮合、指尖朝上模仿花朵含苞的样子；手缓缓向上的同时，慢慢张开，模仿开花的样子。

因此“花”的主要正确性应集中在手部从撮合到张开的相对形态变化，而不是脸部、肩部或全身姿态。旧评分虽然能计算手部坐标距离，但没有显式建模：

- 手指之间是否逐渐张开。
- 指尖相对手腕/掌心的距离变化。
- 关键手指关节伸直/弯曲的相对状态。
- 文本说明里哪些部位应被高权重评分，哪些部位应弱化或忽略。

## 2. 新增数据

新增文本语义权重库：

```text
/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json
/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.md
```

生成脚本：

```text
/data/WYC/signLanguage/work/scripts/build_semantic_weight_profiles.py
```

该脚本读取：

```text
/data/WYC/signLanguage/data/Demo词汇.docx
```

并按关键词把 DOCX 说明和当前 10 个模板词对齐。由于早期 `sign_data_profile` 只是按视频排序硬配对，存在词名与说明错位；本次脚本改为按动作语义关键词匹配，例如“花朵/含苞/开花/张开”映射到 `花`。

## 3. 权重策略

每个词生成一个 `semantic_profile`，包含：

- `group_weights`：脸、手、手形、手臂/pose、缺失惩罚权重。
- `focus_groups`：用于动作语义起止变化检查的重点组。
- `keypoint_weights`：关键指尖、拇指、食指、中指等节点加权。
- `allow_hand_swap`：允许用户镜像或左右手互换时使用更优手侧匹配。
- `semantic_notes`：文本语义解释。

以 `花` 为例：

```json
{
  "left_hand": 0.12,
  "right_hand": 0.32,
  "left_hand_shape": 0.18,
  "right_hand_shape": 0.35,
  "pose": 0.0,
  "face": 0.0,
  "missing": 0.03
}
```

这表示 `花` 基本忽略脸和整体 pose，把主要分数放在手部位置与手形相对变化上。

## 4. 打分算法更新

更新脚本：

```text
/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py
```

新增能力：

1. 自动从标准样本路径推断目标词，并加载对应 `semantic_profile`。
2. 在原有 landmark 坐标特征外，新增 `left_hand_shape/right_hand_shape`。
3. 手形特征包含：
   - 指尖到手腕距离。
   - 相邻指尖间距。
   - 食指/中指等 MCP 到 tip 的长度。
   - 手指弯曲/伸直的角度近似。
4. 每个 group 使用语义权重参与 frame distance。
5. 对手部允许左右手互换匹配，降低摄像头镜像、用户左右手差异带来的误伤。
6. 对 `focus_groups` 增加动作起止语义变化惩罚，防止 DTW 把倒放、乱序动作对齐得过高。
7. roughness penalty 加强，用于压低乱序帧和抖动假动作。

Web 后端也已接入：

```text
/data/WYC/signLanguage/work/web/backend.py
```

`/api/status` 和 `/api/templates` 会返回语义 profile 信息，`/api/score` 的返回结果中包含：

```json
"score": {
  "semantic_profile": {}
}
```

同时，网页前端默认上传帧宽已从 `480` 调整为 `960`。原因是当前 Holistic 手部检测对手部小目标比较敏感；在服务器端用同一 `花.mp4` 做 smoke test 时，低分辨率抽帧更容易漏手，而 `960` 宽度抽取标准帧后能稳定返回更高的语义加权分数。

## 5. 离线判别实验

实验目标词：`花`

标准模板：

```text
/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache_v2/results/花/花_holistic_results.json
```

输出：

```text
/data/WYC/signLanguage/work/generated/scoring_mvp_run3/flower_semantic_weighted_discrimination_v6/
```

判别结果：

| 指标 | 结果 |
| --- | ---: |
| 正例最低分 | `81.437` |
| 负例最高分 | `49.049` |
| margin | `32.388` |
| 门控 | `通过` |

主要 case：

| case | 类型 | 分数 |
| --- | --- | ---: |
| self | 正例 | `100.000` |
| trim_start_20pct | 正例 | `92.648` |
| trim_both_10pct | 正例 | `88.871` |
| subsample_even | 正例 | `88.844` |
| amplitude_1.15 | 正例 | `85.937` |
| amplitude_0.85 | 正例 | `85.315` |
| trim_end_20pct | 正例 | `81.437` |
| fake_shuffle_frames | 假动作 | `49.049` |
| other_demo_谗_羡慕 | 其他 demo | `42.245` |
| fake_reverse_time | 假动作 | `32.569` |
| other_demo_汽车 | 其他 demo | `24.769` |

结论：新算法保留目标动作变体高分，同时把倒放、乱序和其他 demo 压低。与上一版相比，核心改进是负例仍低，而实际网页样本的分数显著回升。

## 6. 旧网页样本回放

用已有网页采集结果回放 `花`：

| request | 旧分数 | 新分数 |
| --- | ---: | ---: |
| `web_20260522_232642_fe440fb9` | `30.093` | `79.683` |
| `web_20260523_000852_b2c2f1de` | `27.923` | `75.351` |
| `web_20260523_000913_d5072c6f` | `30.190` | `76.727` |
| `web_20260523_000903_3123d2db` | `25.822` | `73.224` |
| `web_20260522_232256_781c0807` | `16.632` | `70.087` |

部分质量较差或动作不完整样本仍偏低，例如 `web_20260522_232319_7e3cc881` 新分数 `46.941`。这符合当前策略：降低无关特征误伤，但不把所有低质量样本强行抬高。

此外，使用 `5080/api/score` 直接上传 `花.mp4` 的标准采样帧做 smoke test，返回：

- request：`web_20260523_005320_4bd5e0a3`
- score：`79.347`
- semantic_profile：`花`
- query right_hand presence：`0.741`

## 7. 当前限制

- 文本语义权重仍是工程规则，不是人工标签校准权重。
- `花` 已完成重点验证；其他词已生成 profile，但还需要逐词跑完整判别实验。
- 当前没有真实用户视频和人工评分标签，因此仍不能给出正式合格线。
- 手形特征来自 Holistic 2D/3D landmarks 的相对几何，能表达张开/闭合趋势，但还不是完整的手语语言学特征模型。

## 8. 下一步

1. 对 10 个词分别跑同样的 discrimination suite，检查是否都保持正例高、负例低。
2. 为网页结果增加 `semantic_profile` 展示或诊断说明，告诉用户当前主要看哪些部位。
3. 收集真实用户样本后，用人工评分标签校准 profile 权重和最终分数映射。

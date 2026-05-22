# 手语打分 MVP 判别性优化报告

## 目标

本轮目标是增强评分模块的判别能力：

- 目标动作的合理变体应保持较高分数。
- 其他 demo 动作应显著低分。
- 基于 demo 生成的随机假动作应低分。
- 目标动作的裁剪、降采样和动作幅度调整应仍然较高分。

当前仍无真实用户视频流样本和人工评分标签，因此这里的门控是工程 sanity gate，不是正式用户评分阈值。

## 脚本更新

更新脚本：

- `/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py`

主要改动：

- 新增判别性套件参数：`--run-discrimination-suite`
- 新增其他 demo 负例输入：`--negative-json label=path`
- 新增目标动作正例变体：
  - `self`
  - `subsample_even`
  - `trim_start_20pct`
  - `trim_end_20pct`
  - `trim_both_10pct`
  - `amplitude_0.85`
  - `amplitude_1.15`
- 新增随机假动作负例：
  - `fake_reverse_time`
  - `fake_shuffle_frames`
  - `fake_static_hold`
  - `fake_random_landmarks`
  - `fake_random_walk`
- 将评分从“单纯 DTW 距离”升级为：
  - DTW 局部相似度
  - 长度 / 信息量惩罚
  - presence 差异惩罚
  - motion profile 差异惩罚
  - roughness 差异惩罚
  - endpoint 一致性惩罚
- 对手部 / pose 组加入局部幅度缩放鲁棒性，避免轻度动作幅度调整被过度扣分。

当前工程门控：

- 目标动作正例最低分 `>= 75`
- 负例最高分 `<= 50`
- 分离 margin `>= 15`

## 全 demo raw landmark 缓存

为了验证“其他 demo 动作低分”，本轮补生成了 10 个 demo 的 step-4 raw landmark 缓存。

生成脚本：

- `/data/WYC/signLanguage/work/scripts/benchmark_holistic_worker.py`

本轮修复：

- 当前环境没有 `ffprobe`，旧逻辑会把总帧数退化为 `1`。
- 已在帧切片模式下加入 OpenCV `CAP_PROP_FRAME_COUNT/FPS` fallback。
- 第一次退化的一帧缓存保留在：
  - `/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache/`
- 正确 step-4 缓存保留在：
  - `/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache_v2/`

正确缓存统计：

- `唱歌`：`14` 帧
- `指示`：`16` 帧
- `月亮`：`24` 帧
- `朋友`：`15` 帧
- `汽车`：`23` 帧
- `花`：`28` 帧
- `虎`：`29` 帧
- `谗（羡慕）`：`17` 帧
- `跳`：`10` 帧
- `香蕉`：`22` 帧

worker 初始化耗时：

- `260.107s`

全流程总耗时：

- `274.915s`

## 最终判别性实验

目标动作：

- `花`

标准序列：

- `/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache_v2/results/花/花_holistic_results.json`

负例：

- 其余 9 个 demo 的 step-4 raw landmark 缓存
- 5 个随机假动作

结果目录：

- `/data/WYC/signLanguage/work/generated/scoring_mvp_run2/flower_all_demo_discrimination_v2/`

结果文件：

- `/data/WYC/signLanguage/work/generated/scoring_mvp_run2/flower_all_demo_discrimination_v2/scoring_mvp_result.json`
- `/data/WYC/signLanguage/work/generated/scoring_mvp_run2/flower_all_demo_discrimination_v2/scoring_mvp_result.md`
- `/data/WYC/signLanguage/work/generated/scoring_mvp_run2/flower_all_demo_discrimination_v2/discrimination_cases.csv`

## 最终结果

门控结果：

- 正例最低分：`75.494`
- 负例最高分：`41.495`
- 分离 margin：`33.999`
- 门控是否通过：`True`

目标动作正例：

- `self`：`100.000`
- `amplitude_1.15`：`94.708`
- `amplitude_0.85`：`93.874`
- `trim_end_20pct`：`89.758`
- `subsample_even`：`88.403`
- `trim_both_10pct`：`88.129`
- `trim_start_20pct`：`75.494`

随机假动作：

- `fake_shuffle_frames`：`41.495`
- `fake_reverse_time`：`33.240`
- `fake_static_hold`：`15.658`
- `fake_random_landmarks`：`0.046`
- `fake_random_walk`：`0.006`

其他 demo 动作：

- `谗（羡慕）`：`20.562`
- `朋友`：`14.983`
- `跳`：`13.692`
- `唱歌`：`12.944`
- `汽车`：`11.857`
- `指示`：`11.543`
- `香蕉`：`8.295`
- `月亮`：`6.698`
- `虎`：`1.766`

## 结论

- 当前评分模块已经能在 `花` 目标动作场景下，把合理目标动作变体与其他 demo / 随机假动作明显区分开。
- 幅度调整正例已经恢复到高分区间，说明局部幅度缩放鲁棒性有效。
- 随机打乱、反向、静态保持、随机 landmark 和随机游走均被压低，说明序列级惩罚有效。
- 其他 9 个 demo 动作全部明显低分，说明 raw landmark + DTW + 序列惩罚比旧 bbox 方案具备更强区分度。

## 限制

- 当前只验证了 `花` 作为目标动作的 demo-only sanity gate。
- 当前没有真实用户视频流样本和人工评分标签，不能把 `75/50` 门控解释为用户评分阈值。
- 标准样本仍是单条 demo，不是多示范者标准库。
- 不同词汇是否存在语义近似或允许左右手变化，还需要词汇级规则和人工标注。

## 下一步

- 将同样判别性套件推广到其他 demo 词，逐词检查是否都能通过。
- 增加多模板标准样本匹配，而不是单 demo 模板。
- 生成对齐路径图、逐组误差曲线和关键帧诊断图。
- 收集真实用户样本和人工标签后，重新校准阈值与评分解释。

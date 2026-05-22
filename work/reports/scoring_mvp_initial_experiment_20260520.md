# 手语打分 MVP 初始实验记录

## 结论

本轮已经跑通一个不调用 `Holistic` 的离线评分原型：

- 脚本：`/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py`
- 输入：已有 `Holistic` JSON 缓存
- 方法：固定维度特征 + mask、尺度归一化、DTW 时序对齐、逐组误差统计、prototype score
- 输出：`scoring_mvp_result.json`、`scoring_mvp_result.md`、`alignment_path.csv`

当前结果只用于 sanity check，不是正式用户评分。

## 当前约束

- 当前没有真实用户视频流样本。
- 当前没有人工评分标签。
- 当前没有每词多标准样本库。
- 因此不能校准 pass/fail 阈值，也不能证明真实用户泛化。

## 脚本能力

`score_holistic_sequence_mvp.py` 支持两类输入：

- raw landmark 模式：读取 `records[].result_data` 中的 pose / left hand / right hand / face landmarks。
- bbox 兼容模式：读取旧 probe JSON 中的 pose / hand / face bbox 摘要。

主路线应使用 raw landmark 模式。bbox 模式只用于兼容旧结果和快速诊断，因为它的区分度明显不足。

## 实验 1：`花` raw landmark 自身 sanity check

- 标准序列：`/data/WYC/signLanguage/work/generated/parallel_sampling_strategies_three_layer_run1/candidate_cache/花/花_holistic_results.json`
- 查询序列：同标准序列
- 输出目录：`/data/WYC/signLanguage/work/generated/scoring_mvp_run1/flower_landmark_sanity/`
- 特征模式：`landmark`

结果：

- 自身对齐：`prototype_score = 100.000`，`normalized_distance = 0.000000`
- 降采样伪用户：`98.046`
- 去掉前 20%：`96.027`
- 去掉后 20%：`97.876`
- 中间 60%：`93.987`

解释：

- 自身对齐已经符合预期，说明固定维度、mask、DTW 主链路可用。
- 裁剪和降采样仍然保持高分，符合“同一动作轻微变形/缺段仍相似”的 sanity 预期。
- 这些分数不能作为真实阈值，只说明排序方向合理。

## 实验 2：`花` vs `唱歌` raw landmark 稀疏负例

- 标准序列：`/data/WYC/signLanguage/work/generated/parallel_sampling_strategies_three_layer_run1/candidate_cache/花/花_holistic_results.json`
- 查询序列：`/data/WYC/signLanguage/work/generated/holistic_worker_benchmark_run1/results/唱歌/唱歌_holistic_results.json`
- 输出目录：`/data/WYC/signLanguage/work/generated/scoring_mvp_run1/flower_vs_singing_landmark_sparse_negative/`
- 特征模式：`landmark`

结果：

- `prototype_score = 62.945`
- `normalized_distance = 0.162017`
- 标准序列长度：`28`
- 查询序列长度：`2`
- 主要差异来自 pose 和 face，右手差异较小但缺失惩罚较高。

解释：

- 不同词负例明显低于自身和伪用户正例，方向符合预期。
- 但查询序列只有 2 帧，不能作为稳定负例评估；后续应为更多词生成 dense 或 step-dense raw landmark 缓存。

## 实验 3：`花` vs `唱歌` bbox 旧 probe 负例

- 标准序列：`/data/WYC/signLanguage/work/generated/holistic_probe_20260428_full/花/花.json`
- 查询序列：`/data/WYC/signLanguage/work/generated/holistic_probe_20260428_full/唱歌/唱歌.json`
- 输出目录：`/data/WYC/signLanguage/work/generated/scoring_mvp_run1/flower_vs_singing_bbox_negative/`
- 特征模式：`bbox`

结果：

- `prototype_score = 85.837`
- `normalized_distance = 0.053453`

解释：

- bbox 负例区分度偏弱，不能作为主打分特征。
- 旧 probe 结果可用于覆盖率、运动能量和粗略诊断，但不适合承担最终动作细节评分。

## 已修正的问题

初版脚本曾把“两边同时缺失同一组关键点”也计入 missing penalty，导致自身对齐无法达到 100 分。已修正为：

- 双方同时缺失：不扣相似度分，但会反映在覆盖率 / confidence 中。
- 单边缺失：计入 missing penalty。

## 当前判断

- raw landmark + DTW + mask 的 MVP 方向可继续推进。
- bbox 兼容模式只保留为旧缓存诊断，不作为主评分方案。
- 真实用户评分前必须补齐真实用户样本和人工评分标签。

## 下一步

- 生成更多词的 dense 或 step-dense raw landmark 缓存，用于不同词负例。
- 增加 confidence 分数，把检测覆盖率和缺失率从 prototype score 中拆出来。
- 增加关键帧对齐诊断图和逐组误差曲线。
- 等标准样本库建立后，改为多模板匹配，而不是单模板匹配。

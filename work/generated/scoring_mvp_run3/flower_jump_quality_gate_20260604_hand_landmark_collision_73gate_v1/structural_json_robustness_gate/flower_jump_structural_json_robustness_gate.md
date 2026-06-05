# 花/跳缓存 JSON 结构鲁棒性门

- 生成时间：`2026-06-04T17:32:51`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：写入错类型 record/result_data/landmark group/point/bbox/sidecar fixture，再走正常 `load_sequence()` 和 `run_pair()`；不调用 `/api/score`，不运行 Holistic，不移动 marker，不重启 5080。
- 目标：局部结构损坏按缺失证据处理，保留帧数与 landmark 模式；landmark/bbox 输出和评分诊断必须有限。

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向结构损坏 | 门槛 |
|---|---|---:|---|---:|
| 花 | PASS | 99.016 | mid_record_null | 70.000 |
| 跳 | PASS | 70.714 | mid_right_hand_point_null | 70.000 |

## 分项明细

### 花

| 变体 | 类型 | 状态 | 分数 | 阈值 | 模式 | result/sequence finite | 帧数保留 | 异常 | 说明 |
|---|---|---|---:|---|---|---|---|---|---|
| self_reloaded | positive | PASS | 100.000 | >= 95.0 | landmark | True/True | True | - | 原始标准 JSON 经正常加载后应保持近满分。 |
| first_result_data_string | positive | PASS | 100.000 | >= 70.0 | landmark | True/True | True | - | 首帧 result_data 错类型不应让整段自动误切到 bbox。 |
| mid_record_null | positive | PASS | 99.016 | >= 70.0 | landmark | True/True | True | - | 单个 null record 应按缺失帧保留时序，不应崩溃。 |
| mid_record_string | positive | PASS | 99.016 | >= 70.0 | landmark | True/True | True | - | 单个字符串 record 应按缺失帧保留时序，不应崩溃。 |
| mid_result_data_string | positive | PASS | 99.016 | >= 70.0 | landmark | True/True | True | - | 单帧 result_data 错类型应按该帧 landmarks 缺失处理。 |
| mid_right_hand_group_string | positive | PASS | 99.016 | >= 70.0 | landmark | True/True | True | - | 单帧核心手 landmark 组错类型应按该组缺失处理。 |
| mid_right_hand_group_dict | positive | PASS | 99.016 | >= 70.0 | landmark | True/True | True | - | landmark 组误写成字典时应按该组缺失处理。 |
| mid_right_hand_point_null | positive | PASS | 99.947 | >= 70.0 | landmark | True/True | True | - | 单个 landmark point=null 应按该点缺失处理。 |
| mid_right_hand_point_list | positive | PASS | 99.947 | >= 70.0 | landmark | True/True | True | - | 单个 landmark point 为数组而非对象时应按该点缺失处理。 |
| mid_pose_group_number | positive | PASS | 99.789 | >= 70.0 | landmark | True/True | True | - | 单帧 pose landmark 组为数字时应回退到手部语义评分。 |
| malformed_sidecar_ignored | positive | PASS | 100.000 | >= 95.0 | landmark | True/True | True | - | semantic_frame_weights.json 顶层错类型时应忽略 sidecar 并保持正常评分。 |
| bbox_combined_structure_finite | compatibility | PASS | 3.057 | finite-only | bbox | True/True | True | - | 旧 bbox 模式遇到错类型 group/bbox 和非有限 bbox 数值时应保持有限，不强求 bbox 语义高分。 |

### 跳

| 变体 | 类型 | 状态 | 分数 | 阈值 | 模式 | result/sequence finite | 帧数保留 | 异常 | 说明 |
|---|---|---|---:|---|---|---|---|---|---|
| self_reloaded | positive | PASS | 100.000 | >= 95.0 | landmark | True/True | True | - | 原始标准 JSON 经正常加载后应保持近满分。 |
| first_result_data_string | positive | PASS | 100.000 | >= 70.0 | landmark | True/True | True | - | 首帧 result_data 错类型不应让整段自动误切到 bbox。 |
| mid_record_null | positive | PASS | 78.545 | >= 70.0 | landmark | True/True | True | - | 单个 null record 应按缺失帧保留时序，不应崩溃。 |
| mid_record_string | positive | PASS | 78.545 | >= 70.0 | landmark | True/True | True | - | 单个字符串 record 应按缺失帧保留时序，不应崩溃。 |
| mid_result_data_string | positive | PASS | 78.545 | >= 70.0 | landmark | True/True | True | - | 单帧 result_data 错类型应按该帧 landmarks 缺失处理。 |
| mid_right_hand_group_string | positive | PASS | 81.566 | >= 70.0 | landmark | True/True | True | - | 单帧核心手 landmark 组错类型应按该组缺失处理。 |
| mid_right_hand_group_dict | positive | PASS | 81.566 | >= 70.0 | landmark | True/True | True | - | landmark 组误写成字典时应按该组缺失处理。 |
| mid_right_hand_point_null | positive | PASS | 70.714 | >= 70.0 | landmark | True/True | True | - | 单个 landmark point=null 应按该点缺失处理。 |
| mid_right_hand_point_list | positive | PASS | 70.714 | >= 70.0 | landmark | True/True | True | - | 单个 landmark point 为数组而非对象时应按该点缺失处理。 |
| mid_pose_group_number | positive | PASS | 76.396 | >= 70.0 | landmark | True/True | True | - | 单帧 pose landmark 组为数字时应回退到手部语义评分。 |
| malformed_sidecar_ignored | positive | PASS | 100.000 | >= 95.0 | landmark | True/True | True | - | semantic_frame_weights.json 顶层错类型时应忽略 sidecar 并保持正常评分。 |
| bbox_combined_structure_finite | compatibility | PASS | 0.000 | finite-only | bbox | True/True | True | - | 旧 bbox 模式遇到错类型 group/bbox 和非有限 bbox 数值时应保持有限，不强求 bbox 语义高分。 |

## 说明

- 该门只允许局部损坏退化为缺失证据，不会把结构损坏当作新的有效动作证据。
- bbox 用例只要求兼容路径有限；bbox 缺少完整指尖语义，因此不要求得到 landmark 级高分。
- 该门不能替代正式 marker 后的真实网页摄像头 `花/跳` 样本。

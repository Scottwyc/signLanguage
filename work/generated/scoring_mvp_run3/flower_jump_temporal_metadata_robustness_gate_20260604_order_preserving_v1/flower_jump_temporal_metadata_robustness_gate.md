# 花/跳时间元数据清洗鲁棒性门

- 生成时间：`2026-06-04T11:04:03`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只写临时畸形 JSON 并走正常 `load_sequence`；不调用 `/api/score`，不运行 Holistic，不移动 marker，不重启 5080。
- 目标：畸形 `fps/total_frames/frame_idx/timestamp_sec` 被清洗后，不改变动作顺序、不产生非有限诊断，并保持正常得分。

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱时间元数据变体 | 门槛 |
|---|---|---:|---|---:|
| 花 | PASS | 100.000 | self_reloaded | 70.000 |
| 跳 | PASS | 100.000 | self_reloaded | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 模式 | 状态 | 分数 | 阈值 | fps | total_frames | frame_idx 范围 | 时间戳异常 | 输出有限 | 元数据有效 | 说明 |
|---|---|---|---:|---:|---:|---:|---|---|---|---|---|
| self_reloaded | configured | PASS | 100.000 | 95.000 | 29.450 | 107 | 0-104 | nonfinite=0, negative=0 | yes | yes | 原始标准 JSON 经正常加载后应保持近满分且时间元数据有限。 |
| fps_nan_sanitized | configured | PASS | 100.000 | 70.000 | 25.000 | 107 | 0-104 | nonfinite=0, negative=0 | yes | yes | 顶层 fps=NaN 时应回退到安全默认帧率。 |
| fps_string_sanitized | configured | PASS | 100.000 | 70.000 | 25.000 | 107 | 0-104 | nonfinite=0, negative=0 | yes | yes | 顶层 fps 为非数值字符串时应回退到安全默认帧率。 |
| fps_extreme_sanitized | configured | PASS | 100.000 | 70.000 | 25.000 | 107 | 0-104 | nonfinite=0, negative=0 | yes | yes | 顶层 fps 为极大离群值时应回退到安全默认帧率。 |
| total_frames_inf_recovered | configured | PASS | 100.000 | 70.000 | 29.450 | 105 | 0-104 | nonfinite=0, negative=0 | yes | yes | total_frames=Inf 时应从可靠帧索引恢复总帧数。 |
| total_frames_extreme_recovered | configured | PASS | 100.000 | 70.000 | 29.450 | 105 | 0-104 | nonfinite=0, negative=0 | yes | yes | total_frames 极大离群时应从可靠帧索引恢复总帧数。 |
| mid_frame_idx_nan_both_fallback | configured | PASS | 100.000 | 70.000 | 29.450 | 107 | 0-104 | nonfinite=0, negative=0 | yes | yes | 单帧 record/row frame_idx 均为 NaN 时应保持原有动作顺序。 |
| mid_frame_idx_negative_both_fallback | configured | PASS | 100.000 | 70.000 | 29.450 | 107 | 0-104 | nonfinite=0, negative=0 | yes | yes | 单帧负 frame_idx 不应被排序到动作开头。 |
| mid_frame_idx_extreme_both_fallback | configured | PASS | 100.000 | 70.000 | 29.450 | 107 | 0-104 | nonfinite=0, negative=0 | yes | yes | 单帧极大 frame_idx 不应被排序到动作末尾。 |
| adjacent_frame_idx_swap_order_fallback | configured | PASS | 100.000 | 70.000 | 29.450 | 107 | 0-106 | nonfinite=0, negative=0 | yes | yes | 相邻合法 frame_idx 对调时应保留 record 动作顺序。 |
| reverse_frame_idx_order_fallback | configured | PASS | 100.000 | 70.000 | 29.450 | 107 | 0-106 | nonfinite=0, negative=0 | yes | yes | 整段合法 frame_idx 倒序时不应把正确动作倒放。 |
| duplicate_frame_idx_order_fallback | configured | PASS | 100.000 | 70.000 | 29.450 | 107 | 0-106 | nonfinite=0, negative=0 | yes | yes | 重复合法 frame_idx 应恢复为严格递增帧序。 |
| all_frame_idx_invalid_order_fallback | configured | PASS | 100.000 | 70.000 | 29.450 | 107 | 0-106 | nonfinite=0, negative=0 | yes | yes | 整段 frame_idx 不可用时应按总帧数做顺序保持回退。 |
| all_timestamp_nonfinite_fallback | configured | PASS | 100.000 | 70.000 | 29.450 | 107 | 0-104 | nonfinite=0, negative=0 | yes | yes | 整段 timestamp_sec 非有限时应生成有限非负时间戳。 |
| mixed_timestamp_invalid_fallback | configured | PASS | 100.000 | 70.000 | 29.450 | 107 | 0-104 | nonfinite=0, negative=0 | yes | yes | 稀疏负数/字符串/极大/非有限时间戳应逐帧回退。 |
| adjacent_timestamp_swap_fallback | configured | PASS | 100.000 | 70.000 | 29.450 | 107 | 0-104 | nonfinite=0, negative=0 | yes | yes | 相邻合法 timestamp_sec 对调时应恢复严格递增时间轴。 |
| reverse_timestamp_fallback | configured | PASS | 100.000 | 70.000 | 29.450 | 107 | 0-104 | nonfinite=0, negative=0 | yes | yes | 整段合法 timestamp_sec 倒序时应恢复严格递增时间轴。 |
| combined_temporal_metadata_corruption | configured | PASS | 100.000 | 70.000 | 25.000 | 103 | 0-102 | nonfinite=0, negative=0 | yes | yes | fps、总帧数、帧索引和时间戳同时损坏时仍应正常评分。 |
| bbox_combined_temporal_metadata_finite | bbox | PASS | 100.000 | finite-only | 25.000 | 103 | 0-102 | nonfinite=0, negative=0 | yes | yes | 旧 bbox 兼容模式遇到组合时间元数据损坏时应保持有限评分，不强求缺少指尖语义的 bbox 得到高分。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 模式 | 状态 | 分数 | 阈值 | fps | total_frames | frame_idx 范围 | 时间戳异常 | 输出有限 | 元数据有效 | 说明 |
|---|---|---|---:|---:|---:|---:|---|---|---|---|---|
| self_reloaded | configured | PASS | 100.000 | 95.000 | 14.683 | 37 | 0-36 | nonfinite=0, negative=0 | yes | yes | 原始标准 JSON 经正常加载后应保持近满分且时间元数据有限。 |
| fps_nan_sanitized | configured | PASS | 100.000 | 70.000 | 25.000 | 37 | 0-36 | nonfinite=0, negative=0 | yes | yes | 顶层 fps=NaN 时应回退到安全默认帧率。 |
| fps_string_sanitized | configured | PASS | 100.000 | 70.000 | 25.000 | 37 | 0-36 | nonfinite=0, negative=0 | yes | yes | 顶层 fps 为非数值字符串时应回退到安全默认帧率。 |
| fps_extreme_sanitized | configured | PASS | 100.000 | 70.000 | 25.000 | 37 | 0-36 | nonfinite=0, negative=0 | yes | yes | 顶层 fps 为极大离群值时应回退到安全默认帧率。 |
| total_frames_inf_recovered | configured | PASS | 100.000 | 70.000 | 14.683 | 37 | 0-36 | nonfinite=0, negative=0 | yes | yes | total_frames=Inf 时应从可靠帧索引恢复总帧数。 |
| total_frames_extreme_recovered | configured | PASS | 100.000 | 70.000 | 14.683 | 37 | 0-36 | nonfinite=0, negative=0 | yes | yes | total_frames 极大离群时应从可靠帧索引恢复总帧数。 |
| mid_frame_idx_nan_both_fallback | configured | PASS | 100.000 | 70.000 | 14.683 | 37 | 0-36 | nonfinite=0, negative=0 | yes | yes | 单帧 record/row frame_idx 均为 NaN 时应保持原有动作顺序。 |
| mid_frame_idx_negative_both_fallback | configured | PASS | 100.000 | 70.000 | 14.683 | 37 | 0-36 | nonfinite=0, negative=0 | yes | yes | 单帧负 frame_idx 不应被排序到动作开头。 |
| mid_frame_idx_extreme_both_fallback | configured | PASS | 100.000 | 70.000 | 14.683 | 37 | 0-36 | nonfinite=0, negative=0 | yes | yes | 单帧极大 frame_idx 不应被排序到动作末尾。 |
| adjacent_frame_idx_swap_order_fallback | configured | PASS | 100.000 | 70.000 | 14.683 | 37 | 0-36 | nonfinite=0, negative=0 | yes | yes | 相邻合法 frame_idx 对调时应保留 record 动作顺序。 |
| reverse_frame_idx_order_fallback | configured | PASS | 100.000 | 70.000 | 14.683 | 37 | 0-36 | nonfinite=0, negative=0 | yes | yes | 整段合法 frame_idx 倒序时不应把正确动作倒放。 |
| duplicate_frame_idx_order_fallback | configured | PASS | 100.000 | 70.000 | 14.683 | 37 | 0-36 | nonfinite=0, negative=0 | yes | yes | 重复合法 frame_idx 应恢复为严格递增帧序。 |
| all_frame_idx_invalid_order_fallback | configured | PASS | 100.000 | 70.000 | 14.683 | 37 | 0-36 | nonfinite=0, negative=0 | yes | yes | 整段 frame_idx 不可用时应按总帧数做顺序保持回退。 |
| all_timestamp_nonfinite_fallback | configured | PASS | 100.000 | 70.000 | 14.683 | 37 | 0-36 | nonfinite=0, negative=0 | yes | yes | 整段 timestamp_sec 非有限时应生成有限非负时间戳。 |
| mixed_timestamp_invalid_fallback | configured | PASS | 100.000 | 70.000 | 14.683 | 37 | 0-36 | nonfinite=0, negative=0 | yes | yes | 稀疏负数/字符串/极大/非有限时间戳应逐帧回退。 |
| adjacent_timestamp_swap_fallback | configured | PASS | 100.000 | 70.000 | 14.683 | 37 | 0-36 | nonfinite=0, negative=0 | yes | yes | 相邻合法 timestamp_sec 对调时应恢复严格递增时间轴。 |
| reverse_timestamp_fallback | configured | PASS | 100.000 | 70.000 | 14.683 | 37 | 0-36 | nonfinite=0, negative=0 | yes | yes | 整段合法 timestamp_sec 倒序时应恢复严格递增时间轴。 |
| combined_temporal_metadata_corruption | configured | PASS | 100.000 | 70.000 | 25.000 | 37 | 0-36 | nonfinite=0, negative=0 | yes | yes | fps、总帧数、帧索引和时间戳同时损坏时仍应正常评分。 |
| bbox_combined_temporal_metadata_finite | bbox | PASS | 100.000 | finite-only | 25.000 | 37 | 0-36 | nonfinite=0, negative=0 | yes | yes | 旧 bbox 兼容模式遇到组合时间元数据损坏时应保持有限评分，不强求缺少指尖语义的 bbox 得到高分。 |

## 说明

- `frame_idx` 的安全回退保持记录顺序，并优先使用同帧 record/row 中仍有效的副本。
- 无效 `total_frames` 从可靠帧索引恢复；异常时间戳回退为 `frame_idx/fps`。
- 该门是缓存 JSON 压力测试，不能替代真实网页摄像头样本。

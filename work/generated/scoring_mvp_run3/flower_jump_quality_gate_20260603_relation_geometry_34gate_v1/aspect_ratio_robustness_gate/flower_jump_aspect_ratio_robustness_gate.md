# 花/跳宽高比失真鲁棒性门

- 生成时间：`2026-06-03T18:47:34`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，先剥离基础骨架组，对整幅骨架做 x/y 非等比拉伸，并重建 motion/relation/hand-shape 特征；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：轻中度宽高比失真仍可评分；极端失真只记录诊断边界。

- 后端：`http://127.0.0.1:5080/api/status`，worker=`ready`，pid=`811485`，scoring reload=`14`，last_reload_error=`None`

## 汇总

- 总体：`PASS`

| 词条 | 状态 | 正向最低分 | 最弱正向宽高比 | 诊断最低分 | 最弱诊断宽高比 |
|---|---|---:|---|---:|---|
| 花 | PASS | 80.345 | aspect_x0.85_y1.18 | 76.940 | diagnostic_x0.55_y1.55 |
| 跳 | PASS | 85.975 | aspect_x0.85_y1.18 | 55.282 | diagnostic_x1.55_y0.55 |

## 花 明细

| 变体 | 类型 | 状态 | 分数 | sx | sy | 质量 | 语义 floor | 说明 |
|---|---|---|---:|---:|---:|---|---|---|
| self_recomputed | positive | PASS | 100.000 | 1.00 | 1.00 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 标准序列剥离基础组后重建 motion/relation/hand-shape，应保持近满分。 |
| aspect_x1.10_y0.92 | positive | PASS | 81.047 | 1.10 | 0.92 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 轻微横向拉宽、纵向压缩，模拟 canvas 或摄像头宽高比轻度失配。 |
| aspect_x0.92_y1.10 | positive | PASS | 80.897 | 0.92 | 1.10 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 轻微横向压缩、纵向拉高，模拟反向宽高比轻度失配。 |
| aspect_x1.18_y0.85 | positive | PASS | 80.775 | 1.18 | 0.85 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 中度横向拉宽、纵向压缩，仍应保持可评分。 |
| aspect_x0.85_y1.18 | positive | PASS | 80.345 | 0.85 | 1.18 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 中度横向压缩、纵向拉高，仍应保持可评分。 |
| diagnostic_x1.35_y0.70 | diagnostic | PASS | 80.356 | 1.35 | 0.70 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 强横向拉宽和纵向压缩，只记录诊断边界。 |
| diagnostic_x0.70_y1.35 | diagnostic | PASS | 78.895 | 0.70 | 1.35 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 强横向压缩和纵向拉高，只记录诊断边界。 |
| diagnostic_x1.55_y0.55 | diagnostic | PASS | 79.877 | 1.55 | 0.55 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 极端横向拉宽，会真实破坏跳的方向关系，只记录诊断。 |
| diagnostic_x0.55_y1.55 | diagnostic | PASS | 76.940 | 0.55 | 1.55 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 极端横向压缩和纵向拉高，只记录诊断。 |

## 跳 明细

| 变体 | 类型 | 状态 | 分数 | sx | sy | 质量 | 语义 floor | 说明 |
|---|---|---|---:|---:|---:|---|---|---|
| self_recomputed | positive | PASS | 100.000 | 1.00 | 1.00 | score_valid:score_valid | action_window_net:used | 标准序列剥离基础组后重建 motion/relation/hand-shape，应保持近满分。 |
| aspect_x1.10_y0.92 | positive | PASS | 92.924 | 1.10 | 0.92 | score_valid:score_valid | action_window_net:used | 轻微横向拉宽、纵向压缩，模拟 canvas 或摄像头宽高比轻度失配。 |
| aspect_x0.92_y1.10 | positive | PASS | 92.311 | 0.92 | 1.10 | score_valid:score_valid | action_window_net:used | 轻微横向压缩、纵向拉高，模拟反向宽高比轻度失配。 |
| aspect_x1.18_y0.85 | positive | PASS | 87.803 | 1.18 | 0.85 | score_valid:score_valid | action_window_net:used | 中度横向拉宽、纵向压缩，仍应保持可评分。 |
| aspect_x0.85_y1.18 | positive | PASS | 85.975 | 0.85 | 1.18 | score_valid:score_valid | action_window_net:used | 中度横向压缩、纵向拉高，仍应保持可评分。 |
| diagnostic_x1.35_y0.70 | diagnostic | PASS | 74.277 | 1.35 | 0.70 | score_valid:score_valid | full_sequence_local_relation_segment:used | 强横向拉宽和纵向压缩，只记录诊断边界。 |
| diagnostic_x0.70_y1.35 | diagnostic | PASS | 80.674 | 0.70 | 1.35 | score_valid:score_valid | action_window_net:used | 强横向压缩和纵向拉高，只记录诊断边界。 |
| diagnostic_x1.55_y0.55 | diagnostic | PASS | 55.282 | 1.55 | 0.55 | semantic_mismatch:relation_motion_too_horizontal | action_window_net:relation_motion_too_horizontal | 极端横向拉宽，会真实破坏跳的方向关系，只记录诊断。 |
| diagnostic_x0.55_y1.55 | diagnostic | PASS | 79.435 | 0.55 | 1.55 | score_valid:score_valid | action_window_net:used | 极端横向压缩和纵向拉高，只记录诊断。 |


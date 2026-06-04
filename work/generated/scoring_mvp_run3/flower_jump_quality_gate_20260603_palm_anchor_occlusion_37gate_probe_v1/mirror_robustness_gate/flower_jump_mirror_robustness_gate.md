# 花/跳浏览器镜像鲁棒性门

- 生成时间：`2026-06-03T20:35:20`
- 综合状态：`PASS`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，在骨架特征层面做 x 轴镜像和左右标签诊断；不调用 `/api/score`，不重启 Holistic。
- 门控：`mirror_x` 是正向鲁棒门；左右标签互换只记录诊断边界，因为它会改变 `跳` 的左右手角色语义。

- 5080 状态：worker=`ready`，worker_pid=`811485`，reload_count=`14`，last_reload_error=`None`

## 结论

| 目标词 | 状态 | 正向最低分 | 最弱正向变体 | 左右标签诊断最低分 | 最弱诊断变体 |
|---|---|---:|---|---:|---|
| 花 | PASS | 80.533 | mirror_x | 82.267 | swap_labels_diagnostic |
| 跳 | PASS | 80.843 | mirror_x | 31.053 | mirror_x_swap_labels_diagnostic |

## 明细

| 目标词 | 变体 | 类型 | 状态 | 分数 | normalized | 采集质量 | semantic floor |
|---|---|---|---|---:|---:|---|---|
| 花 | `self_recomputed` | `positive` | PASS | 100.000 | 0.000 | score_valid / score_valid | short_visible_core / query_not_short_core_capture |
| 花 | `mirror_x` | `positive` | PASS | 80.533 | 0.031 | score_valid / score_valid | short_visible_core / query_not_short_core_capture |
| 花 | `swap_labels_diagnostic` | `diagnostic` | PASS | 82.267 | 0.028 | score_valid / score_valid | short_visible_core / query_not_short_core_capture |
| 花 | `mirror_x_swap_labels_diagnostic` | `diagnostic` | PASS | 82.267 | 0.028 | score_valid / score_valid | short_visible_core / query_not_short_core_capture |
| 跳 | `self_recomputed` | `positive` | PASS | 100.000 | 0.000 | score_valid / score_valid | action_window_net / used |
| 跳 | `mirror_x` | `positive` | PASS | 80.843 | 0.088 | score_valid / score_valid | full_sequence_local_relation_segment / used |
| 跳 | `swap_labels_diagnostic` | `diagnostic` | PASS | 36.324 | 0.172 | semantic_mismatch / relation_direction_mismatch | action_window_net / relation_direction_mismatch |
| 跳 | `mirror_x_swap_labels_diagnostic` | `diagnostic` | PASS | 31.053 | 0.198 | semantic_mismatch / relation_direction_mismatch | action_window_net / relation_direction_mismatch |

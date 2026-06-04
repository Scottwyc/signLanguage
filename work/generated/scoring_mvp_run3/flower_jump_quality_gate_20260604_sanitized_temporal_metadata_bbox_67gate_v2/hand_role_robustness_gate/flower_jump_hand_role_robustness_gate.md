# 花/跳手角色鲁棒性门

- 生成时间：`2026-06-04T09:41:17`
- 综合状态：`PASS`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON；不调用 `/api/score`，不移动 marker，不运行 Holistic，不重启 5080。

## 判定口径

- `花`：单手主导词，左右惯用手互换和镜像下互换都必须不低于 `70.000`。
- `跳`：双手角色词，地面手/跳跃手互换必须不高于 `50.000` 且进入 `semantic_mismatch/needs_recapture`。

## 摘要

| 词条 | 状态 | 正向最低分 | 最弱正向角色变体 | 角色互换最高分 | 最强角色互换负例 |
|---|---|---:|---|---:|---|
| 花 | PASS | 80.533 | mirror_x | - | - |
| 跳 | PASS | 80.843 | mirror_x | 36.324 | role_swap_negative |

## 明细

| 词条 | 变体 | 类型 | 分数 | 状态 | 质量状态 | floor 原因 | 序列级左右手匹配 |
|---|---|---|---:|---|---|---|---|
| 花 | self_recomputed | positive | 100.000 | PASS | score_valid | query_not_short_core_capture | direct |
| 花 | mirror_x | positive | 80.533 | PASS | score_valid | query_not_short_core_capture | direct |
| 花 | dominant_hand_swap | positive | 82.267 | PASS | score_valid | query_not_short_core_capture | swapped |
| 花 | mirror_x_dominant_hand_swap | positive | 82.267 | PASS | score_valid | query_not_short_core_capture | swapped |
| 跳 | self_recomputed | positive | 100.000 | PASS | score_valid | used | direct |
| 跳 | mirror_x | positive | 80.843 | PASS | score_valid | used | direct |
| 跳 | role_swap_negative | negative | 36.324 | PASS | semantic_mismatch | relation_direction_mismatch | direct |
| 跳 | mirror_x_role_swap_negative | negative | 31.053 | PASS | semantic_mismatch | relation_direction_mismatch | direct |

## 结论

- 手角色边界通过：`花` 支持左右惯用手，`跳` 仍保持角色语义约束。

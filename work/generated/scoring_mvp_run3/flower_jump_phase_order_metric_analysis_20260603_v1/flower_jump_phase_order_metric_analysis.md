# 花/跳相位顺序候选指标诊断

- 生成时间：`2026-06-03T07:24:42`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- Web 样本根目录：`/data/WYC/signLanguage/work/generated/web_scoring_mvp`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 目标词：`花, 跳`
- 语义锚点：`[0.1, 0.25, 0.5, 0.75, 0.9]`
- 口径：只读缓存 Holistic JSON；不调用 `/api/score`，不运行 Holistic，不重启 5080。

- 5080 状态：worker=`ready`，pid=`811485`，reload_count=`12`，last_reload_error=`None`

## 结论

- 总样本行：`165`，类别计数：`{'synthetic_positive': 10, 'synthetic_disordered': 6, 'web_reliable_nonlow': 124, 'web_needs_recapture': 21, 'web_reliable_low': 4}`
- 零误伤 keep 样本且能拒绝部分乱序的候选规则：`20`
- 零误伤且合成乱序全拒绝的候选规则：`0`
- 诊断结论：存在可辅助诊断的安全候选，但不能单独覆盖全部乱序；暂不直接改线上评分。

## 最优候选阈值

| 词条 | 指标 | 方向 | 阈值 | keep误拒 | 乱序拒绝 | 乱序漏过 | safe | perfect | 漏过样本 |
|---|---|---|---:|---:|---:|---:|---|---|---|
| 花 | full_content_order_score | <= | 0.400 | 0/92 | 2/3 | 1 | Y | N | swap_halves |
| 花 | full_inversion_rate | >= | 0.700 | 0/92 | 2/3 | 1 | Y | N | swap_halves |
| 花 | full_kendall_tau | <= | -0.400 | 0/92 | 2/3 | 1 | Y | N | swap_halves |
| 花 | full_max_backtrack_norm | >= | 0.635 | 0/92 | 2/3 | 1 | Y | N | reverse_full |
| 花 | action_adjacent_backtrack_rate | >= | 0.750 | 0/92 | 1/3 | 2 | Y | N | swap_halves, scramble_three_phases |
| 花 | action_content_order_score | <= | 0.438 | 0/92 | 1/3 | 2 | Y | N | swap_halves, scramble_three_phases |
| 花 | action_inversion_rate | >= | 0.600 | 0/92 | 1/3 | 2 | Y | N | swap_halves, scramble_three_phases |
| 花 | action_kendall_tau | <= | -0.200 | 0/92 | 1/3 | 2 | Y | N | swap_halves, scramble_three_phases |
| 花 | action_max_backtrack_norm | >= | 1.000 | 0/92 | 1/3 | 2 | Y | N | reverse_full, scramble_three_phases |
| 花 | full_adjacent_backtrack_rate | >= | 1.000 | 0/92 | 1/3 | 2 | Y | N | swap_halves, scramble_three_phases |
| 跳 | action_adjacent_backtrack_rate | >= | 0.500 | 0/42 | 1/3 | 2 | Y | N | swap_halves, scramble_three_phases |
| 跳 | action_content_order_score | <= | 0.100 | 0/42 | 1/3 | 2 | Y | N | swap_halves, scramble_three_phases |
| 跳 | action_inversion_rate | >= | 1.000 | 0/42 | 1/3 | 2 | Y | N | swap_halves, scramble_three_phases |
| 跳 | action_kendall_tau | <= | -1.000 | 0/42 | 1/3 | 2 | Y | N | swap_halves, scramble_three_phases |
| 跳 | action_max_backtrack_norm | >= | 0.375 | 0/42 | 1/3 | 2 | Y | N | swap_halves, scramble_three_phases |
| 跳 | full_adjacent_backtrack_rate | >= | 0.500 | 0/42 | 1/3 | 2 | Y | N | swap_halves, scramble_three_phases |
| 跳 | full_content_order_score | <= | 0.099 | 0/42 | 1/3 | 2 | Y | N | swap_halves, scramble_three_phases |
| 跳 | full_inversion_rate | >= | 1.000 | 0/42 | 1/3 | 2 | Y | N | swap_halves, scramble_three_phases |
| 跳 | full_kendall_tau | <= | -1.000 | 0/42 | 1/3 | 2 | Y | N | swap_halves, scramble_three_phases |
| 跳 | full_max_backtrack_norm | >= | 0.944 | 0/42 | 1/3 | 2 | Y | N | reverse_full, scramble_three_phases |

## 分词条分布

### 花

| 类别 | 数量 | 分数中位 | 分数范围 | full反序率中位/最大 | full tau中位/最小 | action反序率中位/最大 | action tau中位/最小 | 花delta中位 | 跳方向中位 |
|---|---:|---:|---|---|---|---|---|---:|---:|
| synthetic_disordered | 3 | 48.880 | 20.405-55.475 | 0.700/1.000 | -0.400/-1.000 | 0.400/0.600 | 0.200/-0.200 | 0.000 | - |
| synthetic_positive | 5 | 94.339 | 79.410-97.464 | 0.200/0.400 | 0.600/-0.100 | 0.200/0.400 | 0.500/-0.100 | 1.000 | - |
| web_needs_recapture | 2 | 17.665 | 14.863-20.468 | 0.000/0.000 | 0.000/0.000 | 0.000/0.000 | 0.000/0.000 | 1.000 | - |
| web_reliable_low | 4 | 31.552 | 2.913-54.425 | 0.000/0.000 | 0.000/0.000 | 0.000/0.000 | 0.000/0.000 | 0.154 | - |
| web_reliable_nonlow | 87 | 78.624 | 63.318-80.784 | 0.000/0.000 | 0.000/0.000 | 0.000/0.000 | 0.000/0.000 | 1.000 | - |

### 跳

| 类别 | 数量 | 分数中位 | 分数范围 | full反序率中位/最大 | full tau中位/最小 | action反序率中位/最大 | action tau中位/最小 | 花delta中位 | 跳方向中位 |
|---|---:|---:|---|---|---|---|---|---:|---:|
| synthetic_disordered | 3 | 47.277 | 20.525-72.027 | 0.600/1.000 | -0.200/-1.000 | 0.000/1.000 | 0.700/-1.000 | - | 0.655 |
| synthetic_positive | 5 | 79.524 | 69.389-96.618 | 0.000/0.000 | 0.900/0.700 | 0.000/0.100 | 0.900/0.400 | - | 0.987 |
| web_needs_recapture | 19 | 3.680 | 0.833-8.919 | 0.100/0.600 | 0.000/-0.600 | 0.000/0.500 | 0.000/-0.400 | - | - |
| web_reliable_nonlow | 37 | 75.325 | 65.191-88.577 | 0.000/0.600 | 0.000/-0.600 | 0.000/0.600 | 0.000/-0.400 | - | 0.955 |

## 高风险样本摘录

### 合成乱序中 full_inversion_rate 最高

| 词条 | 样本 | 分数 | metric | capture | floor | full锚点 | action锚点 |
|---|---|---:|---:|---|---|---|---|
| 花 | reverse_full | 20.405 | 1.000 | score_valid | short_visible_core | 36,34,31,27,11 | 10,8,5,1,13 |
| 跳 | reverse_full | 20.525 | 1.000 | semantic_mismatch | action_window_net | 15,14,11,9,7 | 7,6,3,1,0 |
| 花 | scramble_three_phases | 55.475 | 0.700 | score_valid | short_visible_core | 52,19,22,26,6 | 0,2,5,9,13 |
| 跳 | swap_halves | 47.277 | 0.600 | semantic_mismatch | action_window_net | 13,14,17,0,2 | 2,3,6,7,7 |
| 跳 | scramble_three_phases | 72.027 | 0.600 | score_valid | action_window_net | 16,17,8,10,12 | 1,1,1,3,5 |
| 花 | swap_halves | 48.880 | 0.400 | score_valid | short_visible_core | 43,45,48,52,15 | 5,7,10,14,0 |

### 网页可评分样本中 full_inversion_rate 最高

| 词条 | 样本 | 分数 | metric | capture | floor | full锚点 | action锚点 |
|---|---|---:|---:|---|---|---|---|
| 跳 | web_20260523_021006_aef545ce | 72.870 | 0.600 | score_valid | action_window_net | 43,43,41,41,42 | 2,2,0,0,1 |
| 跳 | web_20260523_022509_a44cb853 | 74.915 | 0.600 | score_valid | full_sequence_local_relation_segment | 28,28,28,11,11 | 6,6,6,6,6 |
| 跳 | web_20260523_063026_c2f04725 | 71.075 | 0.600 | score_valid | action_window_net | 16,16,15,15,15 | 0,0,0,0,1 |
| 跳 | web_20260523_024000_dd35e1bb | 72.943 | 0.400 | score_valid | full_sequence_local_relation_segment | 27,13,13,13,14 | 5,5,5,5,5 |
| 跳 | web_20260523_044323_2eb9eb7e | 75.484 | 0.400 | score_valid | action_window_net | 13,13,13,15,11 | 0,0,0,0,0 |
| 跳 | web_20260523_053241_5fbbf9c7 | 75.983 | 0.400 | score_valid | action_window_net | 18,18,18,18,16 | 0,0,0,0,0 |
| 跳 | web_20260523_063052_fc94e4f7 | 75.147 | 0.400 | score_valid | action_window_net | 18,18,18,18,12 | 0,0,0,0,3 |
| 跳 | web_20260523_044135_12fbd5bc | 75.212 | 0.200 | score_valid | full_sequence_local_relation_segment | 11,11,26,11,11 | 6,6,6,6,6 |

## 下一步约束

- 任何相位顺序规则接入 scorer 前，必须先在本报告的 `web_reliable_nonlow` 样本上零误伤，再跑完整 `flower_jump_quality_gate`。
- 对 `跳`，不能再使用全序列端点硬规则；若要接入，应优先约束语义 floor 的局部 segment 与标准锚点顺序。
- 对 `花`，张开 delta 比 range 更接近语义顺序，但需要以真实网页通过样本的 delta 分布设阈值。

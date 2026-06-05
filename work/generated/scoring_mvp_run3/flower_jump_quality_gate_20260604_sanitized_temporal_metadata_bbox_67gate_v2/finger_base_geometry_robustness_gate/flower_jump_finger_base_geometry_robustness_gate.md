# 花/跳手指基座几何鲁棒性门

- 生成时间：`2026-06-04T09:59:17`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，只压缩/拉开同一手内相邻 MCP/CMC finger-base landmarks 的二维相对几何，distal finger chains、landmark 身份和 mask 不变；随后重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：单帧、稀疏和短窗口 finger-base drift 仍可正常评分；持续强基座交叉或塌缩只记录诊断边界。

- 5080 状态：worker=`ready`，pid=`811485`，reload_count=`22`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向基座漂移 | 诊断最低分 | 最弱诊断边界 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 81.347 | flower_right_nonoverlap_base_full_compress_0p05 | 78.227 | flower_right_full_base_full_cross_1p40_diagnostic | 70.000 |
| 跳 | PASS | 98.112 | jump_right_person_base_full_compress_0p12 | 82.302 | jump_right_person_base_full_cross_1p60_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | group | pairs | alpha | mode | pattern | 改动帧 | 改动点 | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---|---:|---|---|---:|---:|---|---|---|
| flower_right_full_base_full_cross_1p40_diagnostic | diagnostic | DIAG | 78.227 | diagnostic | right_hand | [('thumb', 'index'), ('index', 'middle'), ('middle', 'ring'), ('ring', 'pinky')] | 1.400 | cross | full | 40 | 240 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 诊断记录：全程相邻 MCP/CMC 基座几何交叉时的边界分。 |
| flower_right_full_base_middle35_compress_0p85_diagnostic | diagnostic | DIAG | 94.786 | diagnostic | right_hand | [('thumb', 'index'), ('index', 'middle'), ('middle', 'ring'), ('ring', 'pinky')] | 0.850 | compress | middle_35pct | 19 | 114 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 诊断记录：较长核心窗口所有指根明显塌缩时的边界分。 |
| flower_right_nonoverlap_base_full_compress_0p05 | positive | PASS | 81.347 | >= 70.0 | right_hand | [('index', 'middle'), ('ring', 'pinky')] | 0.050 | compress | full | 40 | 160 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花全程极轻微 MCP 基座压缩，不应破坏开合相位和核心手形。 |
| flower_right_wide_base_middle20_spread_0p14 | positive | PASS | 97.569 | >= 70.0 | right_hand | [('thumb', 'index'), ('middle', 'ring')] | 0.140 | spread | middle_20pct | 11 | 55 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花核心窗口 thumb/index 与 middle/ring 指根轻度拉开，覆盖 palm-base spread 漂移。 |
| flower_right_nonoverlap_base_middle20_compress_0p16 | positive | PASS | 97.600 | >= 70.0 | right_hand | [('index', 'middle'), ('ring', 'pinky')] | 0.160 | compress | middle_20pct | 11 | 44 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花短核心窗口非重叠相邻 MCP 基座压缩，验证局部基座几何容错。 |
| flower_right_nonoverlap_base_sparse_compress_0p22_every_5f | positive | PASS | 98.134 | >= 70.0 | right_hand | [('index', 'middle'), ('ring', 'pinky')] | 0.220 | compress | sparse_every_5f | 7 | 28 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花核心手相邻 MCP 基座稀疏帧压缩，distal 张开证据仍应保留。 |
| flower_right_index_middle_base_single_mid_compress_0p35 | positive | PASS | 99.751 | >= 70.0 | right_hand | [('index', 'middle')] | 0.350 | compress | single_mid | 1 | 2 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花核心手 index/middle MCP 基座单帧压缩，模拟瞬时指根定位漂移。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | right_hand | [] | 0.000 | compress | none | 0 | 0 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | group | pairs | alpha | mode | pattern | 改动帧 | 改动点 | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---|---:|---|---|---:|---:|---|---|---|
| jump_right_person_base_full_cross_1p60_diagnostic | diagnostic | DIAG | 82.302 | diagnostic | right_hand | [('index', 'middle')] | 1.600 | cross | full | 17 | 34 | score_valid:score_valid | action_window_net:used | 诊断记录：右手两指小人 index/middle MCP 基座全程几何交叉时的边界分。 |
| jump_right_person_base_middle35_compress_1p10_diagnostic | diagnostic | DIAG | 87.777 | diagnostic | right_hand | [('index', 'middle')] | 1.100 | compress | middle_35pct | 7 | 14 | score_valid:score_valid | action_window_net:used | 诊断记录：右手两指小人较长核心窗口明显 MCP 基座塌缩时的边界分。 |
| jump_right_person_base_full_compress_0p12 | positive | PASS | 98.112 | >= 70.0 | right_hand | [('index', 'middle')] | 0.120 | compress | full | 17 | 34 | score_valid:score_valid | action_window_net:used | 跳的右手两指小人 index/middle MCP 基座全程轻微压缩，双手关系和指尖两指形仍应稳定。 |
| jump_right_person_base_full_spread_0p12 | positive | PASS | 98.233 | >= 70.0 | right_hand | [('index', 'middle')] | 0.120 | spread | full | 17 | 34 | score_valid:score_valid | action_window_net:used | 跳的右手两指小人 index/middle MCP 基座全程轻微拉大，覆盖相反 palm-base drift。 |
| jump_right_person_base_middle20_compress_0p24 | positive | PASS | 98.760 | >= 70.0 | right_hand | [('index', 'middle')] | 0.240 | compress | middle_20pct | 3 | 6 | score_valid:score_valid | action_window_net:used | 跳的右手两指核心短窗口轻度 MCP 基座压缩，验证局部 palm-base 容错。 |
| jump_right_person_base_sparse_compress_0p32_every_5f | positive | PASS | 99.145 | >= 70.0 | right_hand | [('index', 'middle')] | 0.320 | compress | sparse_every_5f | 4 | 8 | score_valid:score_valid | action_window_net:used | 跳的右手两指小人稀疏帧中度 MCP 基座压缩，跳跃轨迹仍应保持。 |
| jump_left_ground_base_nonoverlap_full_compress_0p14 | positive | PASS | 99.924 | >= 70.0 | left_hand | [('index', 'middle'), ('ring', 'pinky')] | 0.140 | compress | full | 16 | 64 | score_valid:score_valid | action_window_net:used | 跳的左手地面手相邻指根轻度压缩，右手两指语义和双手关系应不受影响。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | right_hand | [] | 0.000 | compress | none | 0 | 0 | score_valid:score_valid | action_window_net:used | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

## 说明

- 该门补充的是 MCP/CMC 指根基座之间的相对几何漂移，不替代 wrist-anchor drift、finger fan-geometry、finger identity jitter、finger curl/length style、遮挡/细节损失或 hand overlap merge 门。
- 持续核心窗口的强基座 collapse/crossing 可能改变真实手形语义，本轮只作为诊断边界；是否升级硬负例需要真实网页样本或人工标签。
- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。

# 花/跳手指扇形几何鲁棒性门

- 生成时间：`2026-06-04T07:08:48`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，只压缩/拉开同一手内相邻 distal finger chains 的二维扇形几何，landmark 身份和 mask 不变，wrist/MCP/palm anchors 保持当前帧；随后重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：单帧、稀疏和短窗口 finger fan drift 仍可正常评分；持续强压缩或几何交叉只记录诊断边界。

- 5080 状态：worker=`ready`，pid=`811485`，reload_count=`19`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向扇形漂移 | 诊断最低分 | 最弱诊断边界 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 81.220 | flower_right_nonoverlap_full_compress_0p08 | 63.377 | flower_right_full_fan_full_cross_1p20_diagnostic | 70.000 |
| 跳 | PASS | 76.629 | jump_right_person_sparse_compress_0p20_every_5f | 82.302 | jump_right_person_full_cross_1p20_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | group | pairs | alpha | mode | pattern | 改动帧 | 改动点 | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---|---:|---|---|---:|---:|---|---|---|
| flower_right_full_fan_full_cross_1p20_diagnostic | diagnostic | DIAG | 63.377 | diagnostic | right_hand | [('thumb', 'index'), ('index', 'middle'), ('middle', 'ring'), ('ring', 'pinky')] | 1.200 | cross | full | 40 | 600 | semantic_mismatch:flower_opening_guard_failed | short_visible_core:query_not_short_core_capture | 诊断记录：全程相邻手指 distal chains 发生几何交叉时的边界分。 |
| flower_right_full_fan_middle35_compress_0p72_diagnostic | diagnostic | DIAG | 95.685 | diagnostic | right_hand | [('thumb', 'index'), ('index', 'middle'), ('middle', 'ring'), ('ring', 'pinky')] | 0.720 | compress | middle_35pct | 19 | 285 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 诊断记录：较长核心窗口全扇形指缝明显塌缩时的边界分。 |
| flower_right_nonoverlap_full_compress_0p08 | positive | PASS | 81.220 | >= 70.0 | right_hand | [('index', 'middle'), ('ring', 'pinky')] | 0.080 | compress | full | 40 | 480 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花全程轻微相邻指缝压缩，不应破坏开合相位和核心手形。 |
| flower_right_nonoverlap_sparse_compress_0p25_every_5f | positive | PASS | 97.497 | >= 70.0 | right_hand | [('index', 'middle'), ('ring', 'pinky')] | 0.250 | compress | sparse_every_5f | 7 | 84 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花核心手相邻指缝稀疏帧轻中度压缩，完整张开证据仍应保留。 |
| flower_right_wide_middle20_spread_0p16 | positive | PASS | 97.536 | >= 70.0 | right_hand | [('thumb', 'index'), ('middle', 'ring')] | 0.160 | spread | middle_20pct | 11 | 132 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花核心窗口 thumb/index 与 middle/ring 指缝轻度拉大，覆盖 fan spread 漂移。 |
| flower_right_nonoverlap_middle20_compress_0p18 | positive | PASS | 97.598 | >= 70.0 | right_hand | [('index', 'middle'), ('ring', 'pinky')] | 0.180 | compress | middle_20pct | 11 | 132 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花短核心窗口非重叠相邻指缝压缩，验证局部扇形几何容错。 |
| flower_right_index_middle_single_mid_compress_0p35 | positive | PASS | 99.755 | >= 70.0 | right_hand | [('index', 'middle')] | 0.350 | compress | single_mid | 1 | 6 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 开花核心手 index/middle 指缝单帧压缩，模拟瞬时手指扇形识别塌缩。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | right_hand | [] | 0.000 | compress | none | 0 | 0 | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | group | pairs | alpha | mode | pattern | 改动帧 | 改动点 | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---|---:|---|---|---:|---:|---|---|---|
| jump_right_person_full_cross_1p20_diagnostic | diagnostic | DIAG | 82.302 | diagnostic | right_hand | [('index', 'middle')] | 1.200 | cross | full | 17 | 102 | score_valid:score_valid | action_window_net:used | 诊断记录：右手两指小人 index/middle distal chains 全程几何交叉时的边界分。 |
| jump_right_person_middle35_compress_0p80_diagnostic | diagnostic | DIAG | 83.273 | diagnostic | right_hand | [('index', 'middle')] | 0.800 | compress | middle_35pct | 7 | 42 | score_valid:score_valid | action_window_net:used | 诊断记录：右手两指小人较长核心窗口明显指缝塌缩时的边界分。 |
| jump_right_person_sparse_compress_0p20_every_5f | positive | PASS | 76.629 | >= 70.0 | right_hand | [('index', 'middle')] | 0.200 | compress | sparse_every_5f | 4 | 24 | score_valid:score_valid | action_window_net:used | 跳的右手两指小人稀疏帧中度指缝压缩，跳跃轨迹仍应保持。 |
| jump_right_person_full_spread_0p08 | positive | PASS | 96.045 | >= 70.0 | right_hand | [('index', 'middle')] | 0.080 | spread | full | 17 | 102 | score_valid:score_valid | action_window_net:used | 跳的右手两指小人 index/middle 指缝全程轻微拉大，覆盖相反 fan drift。 |
| jump_right_person_full_compress_0p08 | positive | PASS | 96.062 | >= 70.0 | right_hand | [('index', 'middle')] | 0.080 | compress | full | 17 | 102 | score_valid:score_valid | action_window_net:used | 跳的右手两指小人 index/middle 指缝全程轻微压缩，双手关系和两指手形仍应稳定。 |
| jump_right_person_middle20_compress_0p14 | positive | PASS | 97.287 | >= 70.0 | right_hand | [('index', 'middle')] | 0.140 | compress | middle_20pct | 3 | 18 | score_valid:score_valid | action_window_net:used | 跳的右手两指核心短窗口轻度指缝压缩，验证局部 fan geometry 容错。 |
| jump_left_ground_nonoverlap_full_compress_0p10 | positive | PASS | 99.709 | >= 70.0 | left_hand | [('index', 'middle'), ('ring', 'pinky')] | 0.100 | compress | full | 16 | 192 | score_valid:score_valid | action_window_net:used | 跳的左手地面手相邻指缝轻度压缩，右手两指语义和双手关系应不受影响。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | right_hand | [] | 0.000 | compress | none | 0 | 0 | score_valid:score_valid | action_window_net:used | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

## 说明

- 该门补充的是相邻手指 distal chains 的扇形间距/指缝几何漂移，不替代 finger identity jitter、finger curl/length style、fingertip/mid-joint occlusion、hand detail loss、hand overlap merge 或 finger-chain latency 门。
- 持续核心窗口的强 fan collapse/crossing 可能改变真实手形语义，本轮只作为诊断边界；是否升级硬负例需要真实网页样本或人工标签。
- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。

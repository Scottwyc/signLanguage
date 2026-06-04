# 花/跳斜拍透视剪切鲁棒性门

- 生成时间：`2026-06-04T08:49:44`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，先剥离到基础骨架组，再合成 image-plane shear、z-to-x/y 透视偏移或局部手部剪切，并重建 hand-shape/motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：轻中度斜拍/透视扭曲仍可正常评分；强剪切和强 z 透视只记录诊断边界。

- 5080 状态：worker=`ready`，pid=`811485`，reload_count=`21`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向透视/剪切 | 诊断最低分 | 最弱诊断透视/剪切 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 80.018 | perspective_z_to_y_0.35 | 78.288 | diagnostic_z_to_x_0.80 | 70.000 |
| 跳 | PASS | 88.573 | perspective_z_to_x_0.35 | 77.705 | diagnostic_combo_shear_0.18_zx_0.60 | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | xy | yx | z->x | z->y | 局部手 | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---:|---:|---:|---:|---|---|---|---|
| diagnostic_z_to_x_0.80 | diagnostic | DIAG | 78.288 | diagnostic | 0.000 | 0.000 | 0.800 | 0.000 | no | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 强 z-to-x 透视偏移只记录诊断边界。 |
| diagnostic_combo_shear_0.18_zx_0.60 | diagnostic | DIAG | 79.119 | diagnostic | 0.180 | 0.000 | 0.600 | 0.000 | no | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 较强剪切和透视组合只记录边界，不作为正常通过要求。 |
| diagnostic_shear_x_from_y_0.30 | diagnostic | DIAG | 80.156 | diagnostic | 0.300 | 0.000 | 0.000 | 0.000 | no | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 强 x<-y 剪切只记录诊断边界，不代表正常网页采集。 |
| diagnostic_shear_y_from_x_0.30 | diagnostic | DIAG | 80.225 | diagnostic | 0.000 | 0.300 | 0.000 | 0.000 | no | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 强 y<-x 剪切只记录诊断边界。 |
| perspective_z_to_y_0.35 | positive | PASS | 80.018 | >= 70.0 | 0.000 | 0.000 | 0.000 | 0.350 | no | score_valid:score_valid | short_visible_core:query_not_short_core_capture | y 坐标随 z 轻中度漂移，模拟上下方向非正面视角。 |
| perspective_z_to_x_neg0.35 | positive | PASS | 80.500 | >= 70.0 | 0.000 | 0.000 | -0.350 | 0.000 | no | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 反向 x-z 透视偏移，覆盖另一侧斜拍。 |
| perspective_z_to_x_0.35 | positive | PASS | 80.502 | >= 70.0 | 0.000 | 0.000 | 0.350 | 0.000 | no | score_valid:score_valid | short_visible_core:query_not_short_core_capture | x 坐标随 z 轻中度漂移，模拟非正面视角的透视偏移。 |
| combo_shear_0.08_zx_0.25 | positive | PASS | 80.583 | >= 70.0 | 0.080 | 0.000 | 0.250 | 0.000 | no | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 轻微 image-plane 剪切叠加 z-to-x 透视偏移。 |
| global_shear_x_from_y_0.15 | positive | PASS | 80.773 | >= 70.0 | 0.150 | 0.000 | 0.000 | 0.000 | no | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 中度 x<-y 剪切，仍应保持可评分。 |
| global_shear_y_from_x_0.15 | positive | PASS | 80.796 | >= 70.0 | 0.000 | 0.150 | 0.000 | 0.000 | no | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 中度 y<-x 剪切，仍应保持可评分。 |
| local_hand_shear_x_from_y_0.12 | positive | PASS | 80.905 | >= 70.0 | 0.120 | 0.000 | 0.000 | 0.000 | yes | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 只在双手局部出现轻中度剪切，模拟手掌相对镜头有斜角。 |
| global_shear_x_from_y_neg0.08 | positive | PASS | 81.055 | >= 70.0 | -0.080 | 0.000 | 0.000 | 0.000 | no | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 反向轻微 x<-y 剪切，覆盖相反斜拍方向。 |
| global_shear_y_from_x_neg0.08 | positive | PASS | 81.074 | >= 70.0 | 0.000 | -0.080 | 0.000 | 0.000 | no | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 反向轻微 y<-x 剪切，覆盖相反斜拍方向。 |
| global_shear_x_from_y_0.08 | positive | PASS | 81.085 | >= 70.0 | 0.080 | 0.000 | 0.000 | 0.000 | no | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 轻微 x<-y 剪切，模拟摄像头水平斜拍。 |
| global_shear_y_from_x_0.08 | positive | PASS | 81.097 | >= 70.0 | 0.000 | 0.080 | 0.000 | 0.000 | no | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 轻微 y<-x 剪切，模拟摄像头垂直方向斜拍。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | 0.000 | 0.000 | 0.000 | 0.000 | no | score_valid:score_valid | short_visible_core:query_not_short_core_capture | 标准序列剥离基础组后重建 hand-shape/motion/relation 特征，应保持近满分。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | xy | yx | z->x | z->y | 局部手 | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---:|---:|---:|---:|---|---|---|---|
| diagnostic_combo_shear_0.18_zx_0.60 | diagnostic | DIAG | 77.705 | diagnostic | 0.180 | 0.000 | 0.600 | 0.000 | no | score_valid:score_valid | full_sequence_local_relation_segment:used | 较强剪切和透视组合只记录边界，不作为正常通过要求。 |
| diagnostic_z_to_x_0.80 | diagnostic | DIAG | 78.389 | diagnostic | 0.000 | 0.000 | 0.800 | 0.000 | no | score_valid:score_valid | full_sequence_local_relation_segment:used | 强 z-to-x 透视偏移只记录诊断边界。 |
| diagnostic_shear_y_from_x_0.30 | diagnostic | DIAG | 87.759 | diagnostic | 0.000 | 0.300 | 0.000 | 0.000 | no | score_valid:score_valid | action_window_net:used | 强 y<-x 剪切只记录诊断边界。 |
| diagnostic_shear_x_from_y_0.30 | diagnostic | DIAG | 88.203 | diagnostic | 0.300 | 0.000 | 0.000 | 0.000 | no | score_valid:score_valid | action_window_net:used | 强 x<-y 剪切只记录诊断边界，不代表正常网页采集。 |
| perspective_z_to_x_0.35 | positive | PASS | 88.573 | >= 70.0 | 0.000 | 0.000 | 0.350 | 0.000 | no | score_valid:score_valid | action_window_net:used | x 坐标随 z 轻中度漂移，模拟非正面视角的透视偏移。 |
| perspective_z_to_x_neg0.35 | positive | PASS | 89.019 | >= 70.0 | 0.000 | 0.000 | -0.350 | 0.000 | no | score_valid:score_valid | action_window_net:used | 反向 x-z 透视偏移，覆盖另一侧斜拍。 |
| perspective_z_to_y_0.35 | positive | PASS | 90.576 | >= 70.0 | 0.000 | 0.000 | 0.000 | 0.350 | no | score_valid:score_valid | action_window_net:used | y 坐标随 z 轻中度漂移，模拟上下方向非正面视角。 |
| combo_shear_0.08_zx_0.25 | positive | PASS | 92.945 | >= 70.0 | 0.080 | 0.000 | 0.250 | 0.000 | no | score_valid:score_valid | action_window_net:used | 轻微 image-plane 剪切叠加 z-to-x 透视偏移。 |
| global_shear_y_from_x_0.15 | positive | PASS | 93.394 | >= 70.0 | 0.000 | 0.150 | 0.000 | 0.000 | no | score_valid:score_valid | action_window_net:used | 中度 y<-x 剪切，仍应保持可评分。 |
| global_shear_x_from_y_0.15 | positive | PASS | 93.872 | >= 70.0 | 0.150 | 0.000 | 0.000 | 0.000 | no | score_valid:score_valid | action_window_net:used | 中度 x<-y 剪切，仍应保持可评分。 |
| local_hand_shear_x_from_y_0.12 | positive | PASS | 95.055 | >= 70.0 | 0.120 | 0.000 | 0.000 | 0.000 | yes | score_valid:score_valid | action_window_net:used | 只在双手局部出现轻中度剪切，模拟手掌相对镜头有斜角。 |
| global_shear_y_from_x_neg0.08 | positive | PASS | 96.164 | >= 70.0 | 0.000 | -0.080 | 0.000 | 0.000 | no | score_valid:score_valid | action_window_net:used | 反向轻微 y<-x 剪切，覆盖相反斜拍方向。 |
| global_shear_y_from_x_0.08 | positive | PASS | 96.339 | >= 70.0 | 0.000 | 0.080 | 0.000 | 0.000 | no | score_valid:score_valid | action_window_net:used | 轻微 y<-x 剪切，模拟摄像头垂直方向斜拍。 |
| global_shear_x_from_y_neg0.08 | positive | PASS | 96.631 | >= 70.0 | -0.080 | 0.000 | 0.000 | 0.000 | no | score_valid:score_valid | action_window_net:used | 反向轻微 x<-y 剪切，覆盖相反斜拍方向。 |
| global_shear_x_from_y_0.08 | positive | PASS | 96.665 | >= 70.0 | 0.080 | 0.000 | 0.000 | 0.000 | no | score_valid:score_valid | action_window_net:used | 轻微 x<-y 剪切，模拟摄像头水平斜拍。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | 0.000 | 0.000 | 0.000 | 0.000 | no | score_valid:score_valid | action_window_net:used | 标准序列剥离基础组后重建 hand-shape/motion/relation 特征，应保持近满分。 |

## 说明

- 该门补充的是斜拍/透视扭曲，不替代已有宽高比、roll、depth、framing 或局部手形门。
- 强剪切和强 z 透视不作为正常网页采集条件，只用于观察当前评分边界。
- 该门是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。

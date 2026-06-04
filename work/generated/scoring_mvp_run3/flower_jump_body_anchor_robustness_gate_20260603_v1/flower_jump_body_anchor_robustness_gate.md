# 花/跳非核心身体锚点漂移鲁棒性门

- 生成时间：`2026-06-03T17:32:08`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，剥离到基础骨架组后仅扰动 `pose/face`，保留手部核心语义，并重建 motion/two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：pose/face 存在漂移、抖动或比例异常时，`花/跳` 不应被非核心身体锚点拖低。

- 5080 状态：worker=`ready`，pid=`811485`，reload_count=`14`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向漂移 | 诊断最低分 | 最弱诊断漂移 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 100.000 | self_recomputed | 100.000 | pose_face_jitter_0.35_diagnostic | 90.000 |
| 跳 | PASS | 100.000 | self_recomputed | 100.000 | pose_face_jitter_0.35_diagnostic | 90.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | alignment | capture_quality | semantic_floor | 扰动 | 说明 |
|---|---|---|---:|---|---|---|---|---|---|
| pose_face_jitter_0.35_diagnostic | diagnostic | DIAG | 100.000 | diagnostic | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | pose,face jitter=0.35 | 严重 pose/face 抖动只记录诊断边界。 |
| pose_face_shift_1.50_diagnostic | diagnostic | DIAG | 100.000 | diagnostic | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | pose,face dx=1.5 dy=-1.2 dz=0.3 | 极端非核心锚点整体偏移只记录诊断边界。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | - | 标准序列剥离基础组后重建派生特征，应保持近满分。 |
| pose_shift_right_up | positive | PASS | 100.000 | >= 90.0 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | pose dx=0.65 dy=-0.45 dz=0.1 | 躯干/身体关键点整体偏右上，但核心手部语义不变。 |
| face_shift_left_down | positive | PASS | 100.000 | >= 90.0 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | face dx=-0.55 dy=0.35 dz=-0.08 | 面部关键点整体偏左下，不应影响手部词评分。 |
| pose_face_opposite_shift | positive | PASS | 100.000 | >= 90.0 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | pose dx=0.55 dy=-0.45 dz=0.1; face dx=-0.45 dy=0.35 dz=-0.1 | pose 与 face 锚点彼此不一致，模拟非核心检测漂移。 |
| pose_face_jitter_0.12 | positive | PASS | 100.000 | >= 90.0 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | pose,face jitter=0.12 | pose/face 存在轻中度逐帧抖动。 |
| pose_face_scale_x0.65_y1.45 | positive | PASS | 100.000 | >= 90.0 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | pose,face scale_x=0.65 scale_y=1.45 | 身体/脸部局部比例异常，但手部核心不变。 |
| pose_face_sinusoidal_drift_0.30 | positive | PASS | 100.000 | >= 90.0 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | pose,face sinusoidal=0.3 | 非核心身体/脸部锚点随时间漂移。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | alignment | capture_quality | semantic_floor | 扰动 | 说明 |
|---|---|---|---:|---|---|---|---|---|---|
| pose_face_jitter_0.35_diagnostic | diagnostic | DIAG | 100.000 | diagnostic | semantic_action_window | score_valid | action_window_net | pose,face jitter=0.35 | 严重 pose/face 抖动只记录诊断边界。 |
| pose_face_shift_1.50_diagnostic | diagnostic | DIAG | 100.000 | diagnostic | semantic_action_window | score_valid | action_window_net | pose,face dx=1.5 dy=-1.2 dz=0.3 | 极端非核心锚点整体偏移只记录诊断边界。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | semantic_action_window | score_valid | action_window_net | - | 标准序列剥离基础组后重建派生特征，应保持近满分。 |
| pose_shift_right_up | positive | PASS | 100.000 | >= 90.0 | semantic_action_window | score_valid | action_window_net | pose dx=0.65 dy=-0.45 dz=0.1 | 躯干/身体关键点整体偏右上，但核心手部语义不变。 |
| face_shift_left_down | positive | PASS | 100.000 | >= 90.0 | semantic_action_window | score_valid | action_window_net | face dx=-0.55 dy=0.35 dz=-0.08 | 面部关键点整体偏左下，不应影响手部词评分。 |
| pose_face_opposite_shift | positive | PASS | 100.000 | >= 90.0 | semantic_action_window | score_valid | action_window_net | pose dx=0.55 dy=-0.45 dz=0.1; face dx=-0.45 dy=0.35 dz=-0.1 | pose 与 face 锚点彼此不一致，模拟非核心检测漂移。 |
| pose_face_jitter_0.12 | positive | PASS | 100.000 | >= 90.0 | semantic_action_window | score_valid | action_window_net | pose,face jitter=0.12 | pose/face 存在轻中度逐帧抖动。 |
| pose_face_scale_x0.65_y1.45 | positive | PASS | 100.000 | >= 90.0 | semantic_action_window | score_valid | action_window_net | pose,face scale_x=0.65 scale_y=1.45 | 身体/脸部局部比例异常，但手部核心不变。 |
| pose_face_sinusoidal_drift_0.30 | positive | PASS | 100.000 | >= 90.0 | semantic_action_window | score_valid | action_window_net | pose,face sinusoidal=0.3 | 非核心身体/脸部锚点随时间漂移。 |

## 说明

- 正向变体覆盖 pose/face 整体偏移、相互不一致、逐帧抖动、局部比例异常和随时间漂移。
- 该门证明当前 `花/跳` 评分以核心手部语义为主，不因非核心身体锚点噪声降低网页正常得分。
- 这是缓存骨架上的合成压力测试，不能替代正式 marker 后的真实网页摄像头样本。

# 花/跳手部 z 倾角鲁棒性门

- 生成时间：`2026-06-04T09:54:33`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，剥离基础骨架组后围绕手腕做 x-z/y-z 局部 3D 旋转，并重建 hand-shape、motion、two-hand relation；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：用户手掌轻微朝向/背向摄像头或侧倾时，`花/跳` 核心语义仍保持可评分；强出平面倾角只记录诊断边界。

- 5080 状态：worker=`ready`，worker_pid=`811485`，reload_count=`22`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | 正向最低分 | 最弱正向 z 倾角 | 诊断最低分 | 最弱诊断 z 倾角 | 门槛 |
|---|---|---:|---|---:|---|---:|
| 花 | PASS | 81.396 | right_hand_pitch_xz_pos12deg | 81.165 | right_hand_yaw_yz_neg35deg_diagnostic | 70.000 |
| 跳 | PASS | 98.093 | right_hand_pitch_xz_neg12deg | 92.212 | right_hand_yaw_yz_neg35deg_diagnostic | 70.000 |

## 分项明细

### 花

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/花/花_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 轴 | 角度 | z_delta | normalized_distance | alignment | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---:|---|---:|---|---|---|---|
| right_hand_yaw_yz_neg35deg_diagnostic | diagnostic | DIAG | 81.165 | diagnostic | yz | -35.0 | -0.105..0.134 | 0.030259 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 右手核心强出平面侧倾可能改变手形语义，只作诊断。 |
| right_hand_pitch_xz_pos35deg_diagnostic | diagnostic | DIAG | 81.176 | diagnostic | xz | 35.0 | -0.047..0.199 | 0.030239 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 右手核心强出平面俯仰可能改变手形语义，只作诊断。 |
| both_hands_yaw_yz_pos25deg_diagnostic | diagnostic | DIAG | 81.251 | diagnostic | yz | 25.0 | -0.070..0.085 | 0.030106 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 双手较强出平面侧倾只记录诊断边界。 |
| both_hands_pitch_xz_neg25deg_diagnostic | diagnostic | DIAG | 81.292 | diagnostic | xz | -25.0 | -0.124..0.057 | 0.030034 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 双手较强出平面俯仰只记录诊断边界。 |
| right_hand_pitch_xz_pos12deg | positive | PASS | 81.396 | >= 70.0 | xz | 12.0 | -0.021..0.068 | 0.029847 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 右手核心手掌轻中度反向 x-z 俯仰。 |
| right_hand_pitch_xz_neg12deg | positive | PASS | 81.400 | >= 70.0 | xz | -12.0 | -0.064..0.025 | 0.029841 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 右手核心手掌轻中度 x-z 俯仰，覆盖常见手腕前后倾。 |
| both_hands_yaw_yz_pos8deg | positive | PASS | 81.407 | >= 70.0 | yz | 8.0 | -0.025..0.027 | 0.029827 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 双手围绕手腕做轻微反向 y-z 出平面侧倾。 |
| both_hands_yaw_yz_neg8deg | positive | PASS | 81.420 | >= 70.0 | yz | -8.0 | -0.027..0.027 | 0.029804 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 双手围绕手腕做轻微 y-z 出平面侧倾，语义轨迹保持。 |
| both_hands_pitch_xz_pos8deg | positive | PASS | 81.422 | >= 70.0 | xz | 8.0 | -0.014..0.045 | 0.029801 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 双手围绕手腕做轻微反向 x-z 出平面俯仰。 |
| both_hands_pitch_xz_neg8deg | positive | PASS | 81.422 | >= 70.0 | xz | -8.0 | -0.043..0.016 | 0.029801 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 双手围绕手腕做轻微 x-z 出平面俯仰，模拟掌面角度小偏差。 |
| left_hand_yaw_yz_neg12deg | positive | PASS | 82.377 | >= 70.0 | yz | -12.0 | -..- | 0.028110 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 左手局部 y-z 侧倾，验证双手词的地面手轻微出平面变化。 |
| left_hand_yaw_yz_pos12deg | positive | PASS | 82.377 | >= 70.0 | yz | 12.0 | -..- | 0.028110 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 左手局部反向 y-z 侧倾。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | xz | 0.0 | 0.000..0.000 | 0.000000 | full_sequence_with_action_window_diagnostics | score_valid | short_visible_core | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

### 跳

- 标准序列：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results/跳/跳_holistic_results.json`

| 变体 | 类型 | 状态 | 分数 | 阈值 | 轴 | 角度 | z_delta | normalized_distance | alignment | capture_quality | semantic_floor | 说明 |
|---|---|---|---:|---|---|---:|---|---:|---|---|---|---|
| right_hand_yaw_yz_neg35deg_diagnostic | diagnostic | DIAG | 92.212 | diagnostic | yz | -35.0 | -0.134..0.000 | 0.019603 | semantic_action_window | score_valid | action_window_net | 右手核心强出平面侧倾可能改变手形语义，只作诊断。 |
| both_hands_pitch_xz_neg25deg_diagnostic | diagnostic | DIAG | 93.809 | diagnostic | xz | -25.0 | -0.137..0.254 | 0.015152 | semantic_action_window | score_valid | action_window_net | 双手较强出平面俯仰只记录诊断边界。 |
| right_hand_pitch_xz_pos35deg_diagnostic | diagnostic | DIAG | 96.421 | diagnostic | xz | 35.0 | -0.010..0.210 | 0.008444 | semantic_action_window | score_valid | action_window_net | 右手核心强出平面俯仰可能改变手形语义，只作诊断。 |
| both_hands_yaw_yz_pos25deg_diagnostic | diagnostic | DIAG | 96.436 | diagnostic | yz | 25.0 | -0.017..0.121 | 0.008333 | semantic_action_window | score_valid | action_window_net | 双手较强出平面侧倾只记录诊断边界。 |
| right_hand_pitch_xz_neg12deg | positive | PASS | 98.093 | >= 70.0 | xz | -12.0 | -0.069..0.010 | 0.004602 | semantic_action_window | score_valid | action_window_net | 右手核心手掌轻中度 x-z 俯仰，覆盖常见手腕前后倾。 |
| both_hands_yaw_yz_neg8deg | positive | PASS | 98.361 | >= 70.0 | yz | -8.0 | -0.036..0.008 | 0.003936 | semantic_action_window | score_valid | action_window_net | 双手围绕手腕做轻微 y-z 出平面侧倾，语义轨迹保持。 |
| both_hands_pitch_xz_neg8deg | positive | PASS | 98.435 | >= 70.0 | xz | -8.0 | -0.047..0.081 | 0.003670 | semantic_action_window | score_valid | action_window_net | 双手围绕手腕做轻微 x-z 出平面俯仰，模拟掌面角度小偏差。 |
| right_hand_pitch_xz_pos12deg | positive | PASS | 98.589 | >= 70.0 | xz | 12.0 | -0.006..0.073 | 0.003335 | semantic_action_window | score_valid | action_window_net | 右手核心手掌轻中度反向 x-z 俯仰。 |
| both_hands_yaw_yz_pos8deg | positive | PASS | 98.619 | >= 70.0 | yz | 8.0 | -0.007..0.038 | 0.003258 | semantic_action_window | score_valid | action_window_net | 双手围绕手腕做轻微反向 y-z 出平面侧倾。 |
| both_hands_pitch_xz_pos8deg | positive | PASS | 98.725 | >= 70.0 | xz | 8.0 | -0.079..0.048 | 0.002940 | semantic_action_window | score_valid | action_window_net | 双手围绕手腕做轻微反向 x-z 出平面俯仰。 |
| left_hand_yaw_yz_pos12deg | positive | PASS | 99.157 | >= 70.0 | yz | 12.0 | -0.009..0.030 | 0.002103 | semantic_action_window | score_valid | action_window_net | 左手局部反向 y-z 侧倾。 |
| left_hand_yaw_yz_neg12deg | positive | PASS | 99.174 | >= 70.0 | yz | -12.0 | -0.031..0.012 | 0.002083 | semantic_action_window | score_valid | action_window_net | 左手局部 y-z 侧倾，验证双手词的地面手轻微出平面变化。 |
| self_recomputed | positive | PASS | 100.000 | >= 95.0 | xz | 0.0 | 0.000..0.000 | 0.000000 | semantic_action_window | score_valid | action_window_net | 标准序列剥离基础组后重建 hand-shape/motion/relation，应保持近满分。 |

## 说明

- 正向扰动覆盖轻微手掌出平面俯仰/侧倾，并强制重算派生手形、动作和双手关系特征。
- 强倾角不作为硬门，避免把真实手形/朝向语义变化错误推广为正常采集。
- 该门是合成鲁棒性压力测试，不能替代真实网页摄像头样本。

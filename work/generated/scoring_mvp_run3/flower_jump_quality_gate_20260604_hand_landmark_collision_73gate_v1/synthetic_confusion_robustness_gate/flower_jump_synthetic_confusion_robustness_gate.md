# 花/跳合成鲁棒变体交叉混淆门

- 生成时间：`2026-06-04T17:07:52`
- 标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读缓存 Holistic JSON，在骨架层生成代表性正向扰动；同一 query 先按目标词评分，再按另一个词模板评分；不调用 `/api/score`，不运行 Holistic，不重启 5080。
- 目标：网页鲁棒性提高后，`花` 的正向扰动不应被 `跳` 高分接收，`跳` 的正向扰动也不应被 `花` 高分接收。

- 5080 状态：worker=`ready`，worker_pid=`811485`，reload_count=`29`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`

| 目标词 | 状态 | cases | pass | fail | 目标最低 | 交叉最高 | margin 最低 | 最弱变体 |
|---|---|---:|---:|---:|---:|---:|---:|---|
| 花 | PASS | 10 | 10 | 0 | 76.727 | 8.506 | 70.776 | hand_noise_0.010_seed1 |
| 跳 | PASS | 10 | 10 | 0 | 70.708 | 25.551 | 55.428 | framing_shift_zoom_out |

## 分项明细

| 目标词 | 交叉词 | family | variant | pass | 目标分 | 交叉分 | margin | 目标状态 | 交叉状态 | 原因 |
|---|---|---|---|---|---:|---:|---:|---|---|---|
| 花 | 跳 | landmark_noise | hand_noise_0.010_seed1 | PASS | 76.727 | 5.950 | 70.776 | score_valid | needs_recapture | passed |
| 花 | 跳 | framing | framing_shift_zoom_out | PASS | 80.553 | 6.221 | 74.331 | score_valid | semantic_mismatch | passed |
| 花 | 跳 | mirror | mirror_x | PASS | 80.533 | 5.879 | 74.654 | score_valid | needs_recapture | passed |
| 花 | 跳 | framing | global_rotate_8deg | PASS | 81.346 | 6.182 | 75.164 | score_valid | needs_recapture | passed |
| 花 | 跳 | temporal_padding | prefix_hold_25pct | PASS | 99.522 | 8.506 | 91.016 | score_valid | needs_recapture | passed |
| 花 | 跳 | landmark_noise | hand_frame_dropout_0.03_seed1 | PASS | 98.599 | 5.633 | 92.966 | score_valid | needs_recapture | passed |
| 花 | 跳 | temporal_padding | slow_repeat_each_2x | PASS | 99.588 | 6.105 | 93.483 | score_valid | needs_recapture | passed |
| 花 | 跳 | action_crop | trim_start_15pct | PASS | 99.569 | 5.871 | 93.698 | score_valid | needs_recapture | passed |
| 花 | 跳 | baseline | self_recomputed | PASS | 100.000 | 6.227 | 93.773 | score_valid | needs_recapture | passed |
| 花 | 跳 | action_crop | center_70pct | PASS | 98.013 | 3.245 | 94.768 | score_valid | needs_recapture | passed |
| 跳 | 花 | framing | framing_shift_zoom_out | PASS | 70.708 | 15.279 | 55.428 | score_valid | semantic_mismatch | passed |
| 跳 | 花 | landmark_noise | hand_noise_0.010_seed1 | PASS | 72.810 | 15.197 | 57.613 | score_valid | semantic_mismatch | passed |
| 跳 | 花 | mirror | mirror_x | PASS | 80.843 | 14.764 | 66.080 | score_valid | semantic_mismatch | passed |
| 跳 | 花 | temporal_padding | slow_repeat_each_2x | PASS | 79.124 | 12.340 | 66.784 | score_valid | semantic_mismatch | passed |
| 跳 | 花 | action_crop | trim_start_15pct | PASS | 80.750 | 11.645 | 69.106 | score_valid | semantic_mismatch | passed |
| 跳 | 花 | landmark_noise | hand_frame_dropout_0.03_seed1 | PASS | 89.463 | 16.591 | 72.872 | score_valid | semantic_mismatch | passed |
| 跳 | 花 | temporal_padding | prefix_hold_25pct | PASS | 100.000 | 25.551 | 74.449 | score_valid | semantic_mismatch | passed |
| 跳 | 花 | action_crop | center_70pct | PASS | 81.045 | 5.117 | 75.928 | score_valid | semantic_mismatch | passed |
| 跳 | 花 | framing | global_rotate_8deg | PASS | 95.788 | 15.490 | 80.298 | score_valid | semantic_mismatch | passed |
| 跳 | 花 | baseline | self_recomputed | PASS | 100.000 | 15.330 | 84.670 | score_valid | semantic_mismatch | passed |

## 说明

- 该门只证明合成正向扰动仍有跨词区分度，不能替代 marker 后真实网页摄像头样本。
- 如果该门失败，不应直接抬高鲁棒性 floor；应先检查是哪类扰动导致错词模板高分。

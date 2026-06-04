# 花剩余有效低分样本骨架复查

- 时间：`2026-06-03 03:58 CST`
- 输入报告：`work/generated/scoring_mvp_run3/flower_jump_quality_gate_20260603_v5/web_regression/flower_jump_diagnostics/web_semantic_diagnostics.csv`
- 可视化输出：`work/generated/scoring_mvp_run3/flower_remaining_low_visual_audit_20260603_v1/holistic_visuals/web_holistic_visual_recovery_summary.md`
- 目的：复查五子门质量门中剩余的 `4` 条 `花` 有效低分，判断是否需要为了真实网页测试继续放宽 `flower_opening_guard`。

## 结论

暂不放宽 `flower_opening_guard`。

这四条低分样本共同特征是：Holistic 能识别到部分手部，但“从撮合到张开”的手指绽放动态证据弱，opening score 仅 `0.00-0.12`。骨架图显示它们更像手部位置/姿态变化、口部附近动作、或帧数过短的 smoke 片段，而不是清晰的开花动作。当前低分更符合语义判定，不是 DTW 将清晰正确动作系统性压低的证据。

## 样本复查

| request | 当前诊断分 | 可视化重算分 | 帧数 | opening | 覆盖 L/R | 判断 |
|---|---:|---:|---:|---:|---|---|
| `web_20260522_232244_45d260ed` | 48.531 | 40.392 | 30 | 0.122 | 0.000/0.633 | 手部出现较晚，主要是位置/姿态变化，缺少稳定撮合起点和清晰张开过程。 |
| `web_20260523_031345_3b07a113` | 54.425 | 54.425 | 30 | 0.086 | 0.000/0.767 | 手部有移动，但手指张开动态不明显，opening guard 保持低分合理。 |
| `web_20260523_062341_afa8c368` | 14.572 | 14.572 | 20 | 0.000 | 1.000/0.450 | 更像手靠近脸/口部并伴随另一只手出现，不是单手花朵绽放。 |
| `web_20260602_233301_233b8215` | 2.913 | 2.913 | 6 | 0.052 | 0.000/1.000 | 仅 6 帧短 smoke，缺少足够语义过程，不应作为正常花动作抬分。 |

## 骨架图

- `web_20260522_232244_45d260ed`：`work/generated/scoring_mvp_run3/flower_remaining_low_visual_audit_20260603_v1/holistic_visuals/web_20260522_232244_45d260ed/query/web_20260522_232244_45d260ed_花_query_skeleton_contact_sheet.png`
- `web_20260523_031345_3b07a113`：`work/generated/scoring_mvp_run3/flower_remaining_low_visual_audit_20260603_v1/holistic_visuals/web_20260523_031345_3b07a113/query/web_20260523_031345_3b07a113_花_query_skeleton_contact_sheet.png`
- `web_20260523_062341_afa8c368`：`work/generated/scoring_mvp_run3/flower_remaining_low_visual_audit_20260603_v1/holistic_visuals/web_20260523_062341_afa8c368/query/web_20260523_062341_afa8c368_花_query_skeleton_contact_sheet.png`
- `web_20260602_233301_233b8215`：`work/generated/scoring_mvp_run3/flower_remaining_low_visual_audit_20260603_v1/holistic_visuals/web_20260602_233301_233b8215/query/web_20260602_233301_233b8215_花_query_skeleton_contact_sheet.png`

## 后续策略

- 如果新的真实网页 `花` 样本有清楚的撮合起点、张开过程和张开终态，但仍被 `flower_opening_guard_failed` 打低，再针对该样本分析 opening 特征是否对手形变化不够鲁棒。
- 在没有这种反例前，继续保持 `flower_opening_guard`，避免把 `谗（羡慕）`、口部附近手势、或局部手形相似片段误抬为 `花`。

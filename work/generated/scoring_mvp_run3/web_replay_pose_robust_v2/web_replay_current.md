# 网页测试样本当前算法回放

- 生成时间：`2026-05-23T04:43:41`
- Web 样本根目录：`work/generated/web_scoring_mvp`
- 语义 profile：`work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：复查已保存网页/API 帧切片样本，不重新运行浏览器采集。
- 分段：`normal_like >= 75`，`60 <= borderline < 75`，`low < 60`；这仍不是正式用户阈值。

## 总览

- 样本数：`108`
- 错误数：`0`
- 当前正常区间：`14`
- 当前边界区间：`1`
- 当前低分区间：`93`
- 旧均分：`33.763`
- 新均分：`35.417`

## 分词条

| 词条 | 样本数 | 正常 | 边界 | 低分 | 旧均分 | 新均分 | 手部覆盖均值 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 花 | 62 | 6 | 1 | 55 | 42.440 | 45.979 | 0.715 |
| 跳 | 36 | 8 | 0 | 28 | 24.351 | 24.365 | 0.735 |
| 香蕉 | 10 | 0 | 0 | 10 | 13.845 | 9.716 | 0.553 |

## 最新样本

| request | 词条 | 帧数 | 旧分 | 新分 | 分段 | 手部覆盖 | 对齐 |
|---|---|---:|---:|---:|---|---:|---|
| web_20260523_041635_7421d5c0 | 花 | 30 | 51.290 | 51.290 | low | 0.700 | full_sequence_with_action_window_diagnostics |
| web_20260523_041652_402b253a | 花 | 30 | 53.505 | 50.890 | low | 0.833 | full_sequence_with_action_window_diagnostics |
| web_20260523_041708_24e7d28a | 花 | 30 | 43.373 | 43.373 | low | 0.600 | full_sequence_with_action_window_diagnostics |
| web_20260523_041735_ea1bbaa6 | 跳 | 30 | 3.703 | 6.757 | low | 0.833 | semantic_action_window |
| web_20260523_041842_85a68d85 | 香蕉 | 30 | 13.189 | 13.189 | low | 0.633 | full_sequence_with_action_window_diagnostics |
| web_20260523_041927_ff5431de | 香蕉 | 30 | 20.993 | 20.993 | low | 0.800 | full_sequence_with_action_window_diagnostics |
| web_20260523_041941_9438151d | 香蕉 | 30 | 15.852 | 16.112 | low | 0.667 | full_sequence_with_action_window_diagnostics |
| web_20260523_041958_068b1181 | 花 | 30 | 50.888 | 50.888 | low | 0.600 | full_sequence_with_action_window_diagnostics |
| web_20260523_042011_9284da87 | 花 | 30 | 56.866 | 56.866 | low | 0.733 | full_sequence_with_action_window_diagnostics |
| web_20260523_042024_ee2fc3da | 花 | 30 | 51.989 | 51.989 | low | 0.800 | full_sequence_with_action_window_diagnostics |
| web_20260523_042222_fac8359d | 花 | 30 | 52.073 | 52.073 | low | 0.867 | full_sequence_with_action_window_diagnostics |
| web_20260523_042235_9431f1a0 | 花 | 30 | 52.224 | 52.224 | low | 0.667 | full_sequence_with_action_window_diagnostics |
| web_20260523_043442_e00f8b9c | 花 | 53 | 75.493 | 75.493 | normal_like | 0.792 | full_sequence_with_action_window_diagnostics |
| web_20260523_043446_cbecd916 | 跳 | 19 | 81.071 | 81.071 | normal_like | 0.895 | semantic_action_window |
| web_20260523_043910_b186b6a6 | 花 | 30 | 56.523 | 56.523 | low | 0.767 | full_sequence_with_action_window_diagnostics |
| web_20260523_043923_b95a60d0 | 花 | 30 | 57.852 | 57.852 | low | 0.733 | full_sequence_with_action_window_diagnostics |
| web_20260523_043955_dd909904 | 花 | 30 | 54.228 | 54.228 | low | 0.700 | full_sequence_with_action_window_diagnostics |
| web_20260523_044018_960618af | 跳 | 30 | 8.276 | 8.276 | low | 0.767 | semantic_action_window |
| web_20260523_044135_12fbd5bc | 跳 | 30 | 5.706 | 5.706 | low | 0.767 | semantic_action_window |
| web_20260523_044203_20778933 | 跳 | 30 | 4.197 | 4.197 | low | 0.767 | semantic_action_window |

## 低分样本排查

- `web_20260523_010014_049faf7d` / 跳: score=`2.905`, frames=`15`, hand_presence=`0.467`, mode=`semantic_action_window`
- `web_20260523_001229_690e6b5a` / 香蕉: score=`3.343`, frames=`30`, hand_presence=`0.700`, mode=`semantic_action_window`
- `web_20260523_010119_d0158d2a` / 香蕉: score=`3.468`, frames=`30`, hand_presence=`0.467`, mode=`semantic_action_window`
- `web_20260523_010145_82035a51` / 香蕉: score=`3.797`, frames=`30`, hand_presence=`0.633`, mode=`semantic_action_window`
- `web_20260523_044203_20778933` / 跳: score=`4.197`, frames=`30`, hand_presence=`0.767`, mode=`semantic_action_window`
- `web_20260523_031247_f927176a` / 跳: score=`4.951`, frames=`15`, hand_presence=`0.933`, mode=`semantic_action_window`
- `web_20260523_005941_0ec0ccab` / 跳: score=`5.320`, frames=`15`, hand_presence=`0.800`, mode=`semantic_action_window`
- `web_20260523_024025_9c6cf572` / 跳: score=`5.433`, frames=`30`, hand_presence=`0.600`, mode=`semantic_action_window`
- `web_20260523_001152_83546751` / 跳: score=`5.439`, frames=`15`, hand_presence=`0.667`, mode=`semantic_action_window`
- `web_20260523_044135_12fbd5bc` / 跳: score=`5.706`, frames=`30`, hand_presence=`0.767`, mode=`semantic_action_window`
- `web_20260523_024000_dd35e1bb` / 跳: score=`5.735`, frames=`30`, hand_presence=`0.900`, mode=`semantic_action_window`
- `web_20260523_001216_53df594b` / 香蕉: score=`6.020`, frames=`15`, hand_presence=`0.533`, mode=`semantic_action_window`
- `web_20260523_011135_5967dd5a` / 跳: score=`6.108`, frames=`30`, hand_presence=`0.700`, mode=`semantic_action_window`
- `web_20260523_001204_d3564a22` / 香蕉: score=`6.151`, frames=`15`, hand_presence=`0.067`, mode=`semantic_action_window`
- `web_20260523_010004_7eaf7ee3` / 跳: score=`6.441`, frames=`15`, hand_presence=`0.800`, mode=`semantic_action_window`
- `web_20260523_024037_ff5b3fb5` / 跳: score=`6.721`, frames=`30`, hand_presence=`0.833`, mode=`semantic_action_window`
- `web_20260523_031147_55d51ab9` / 跳: score=`6.722`, frames=`30`, hand_presence=`0.600`, mode=`semantic_action_window`
- `web_20260523_001048_5bcb9948` / 跳: score=`6.736`, frames=`15`, hand_presence=`0.600`, mode=`semantic_action_window`
- `web_20260523_041735_ea1bbaa6` / 跳: score=`6.757`, frames=`30`, hand_presence=`0.833`, mode=`semantic_action_window`
- `web_20260523_011122_fb34e3e5` / 跳: score=`7.054`, frames=`30`, hand_presence=`0.567`, mode=`semantic_action_window`

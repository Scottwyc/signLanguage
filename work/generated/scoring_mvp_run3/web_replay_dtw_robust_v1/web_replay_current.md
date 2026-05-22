# 网页测试样本当前算法回放

- 生成时间：`2026-05-23T05:18:56`
- Web 样本根目录：`work/generated/web_scoring_mvp`
- 语义 profile：`work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：复查已保存网页/API 帧切片样本，不重新运行浏览器采集。
- 分段：`normal_like >= 75`，`60 <= borderline < 75`，`low < 60`；这仍不是正式用户阈值。

## 总览

- 样本数：`111`
- 错误数：`0`
- 当前正常区间：`15`
- 当前边界区间：`24`
- 当前低分区间：`72`
- 旧均分：`33.129`
- 新均分：`42.889`

## 分词条

| 词条 | 样本数 | 正常 | 边界 | 低分 | 旧均分 | 新均分 | 手部覆盖均值 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 花 | 62 | 7 | 24 | 31 | 42.440 | 56.950 | 0.715 |
| 跳 | 39 | 8 | 0 | 31 | 23.270 | 28.852 | 0.738 |
| 香蕉 | 10 | 0 | 0 | 10 | 13.845 | 10.456 | 0.553 |

## 最新样本

| request | 词条 | 帧数 | 旧分 | 新分 | 分段 | 手部覆盖 | 对齐 |
|---|---|---:|---:|---:|---|---:|---|
| web_20260523_041735_ea1bbaa6 | 跳 | 30 | 3.703 | 14.406 | low | 0.833 | semantic_action_window |
| web_20260523_041842_85a68d85 | 香蕉 | 30 | 13.189 | 14.935 | low | 0.633 | full_sequence_with_action_window_diagnostics |
| web_20260523_041927_ff5431de | 香蕉 | 30 | 20.993 | 22.521 | low | 0.800 | full_sequence_with_action_window_diagnostics |
| web_20260523_041941_9438151d | 香蕉 | 30 | 15.852 | 16.522 | low | 0.667 | full_sequence_with_action_window_diagnostics |
| web_20260523_041958_068b1181 | 花 | 30 | 50.888 | 50.888 | low | 0.600 | full_sequence_with_action_window_diagnostics |
| web_20260523_042011_9284da87 | 花 | 30 | 56.866 | 73.032 | borderline | 0.733 | full_sequence_with_action_window_diagnostics |
| web_20260523_042024_ee2fc3da | 花 | 30 | 51.989 | 69.018 | borderline | 0.800 | full_sequence_with_action_window_diagnostics |
| web_20260523_042222_fac8359d | 花 | 30 | 52.073 | 69.130 | borderline | 0.867 | full_sequence_with_action_window_diagnostics |
| web_20260523_042235_9431f1a0 | 花 | 30 | 52.224 | 69.330 | borderline | 0.667 | full_sequence_with_action_window_diagnostics |
| web_20260523_043442_e00f8b9c | 花 | 53 | 75.493 | 90.561 | normal_like | 0.792 | full_sequence_with_action_window_diagnostics |
| web_20260523_043446_cbecd916 | 跳 | 19 | 81.071 | 88.036 | normal_like | 0.895 | semantic_action_window |
| web_20260523_043910_b186b6a6 | 花 | 30 | 56.523 | 73.226 | borderline | 0.767 | full_sequence_with_action_window_diagnostics |
| web_20260523_043923_b95a60d0 | 花 | 30 | 57.852 | 74.139 | borderline | 0.733 | full_sequence_with_action_window_diagnostics |
| web_20260523_043955_dd909904 | 花 | 30 | 54.228 | 71.991 | borderline | 0.700 | full_sequence_with_action_window_diagnostics |
| web_20260523_044018_960618af | 跳 | 30 | 8.276 | 10.736 | low | 0.767 | semantic_action_window |
| web_20260523_044135_12fbd5bc | 跳 | 30 | 5.706 | 6.283 | low | 0.767 | semantic_action_window |
| web_20260523_044203_20778933 | 跳 | 30 | 4.197 | 5.798 | low | 0.767 | semantic_action_window |
| web_20260523_044323_2eb9eb7e | 跳 | 25 | 10.393 | 21.658 | low | 0.800 | semantic_action_window |
| web_20260523_044336_5d15d099 | 跳 | 25 | 13.288 | 21.419 | low | 0.720 | semantic_action_window |
| web_20260523_044358_00db9d4d | 跳 | 25 | 7.193 | 13.743 | low | 0.800 | semantic_action_window |

## 低分样本排查

- `web_20260523_010014_049faf7d` / 跳: score=`3.779`, frames=`15`, hand_presence=`0.467`, mode=`semantic_action_window`
- `web_20260523_010145_82035a51` / 香蕉: score=`3.915`, frames=`30`, hand_presence=`0.633`, mode=`semantic_action_window`
- `web_20260523_010119_d0158d2a` / 香蕉: score=`4.252`, frames=`30`, hand_presence=`0.467`, mode=`semantic_action_window`
- `web_20260523_001229_690e6b5a` / 香蕉: score=`4.362`, frames=`30`, hand_presence=`0.700`, mode=`semantic_action_window`
- `web_20260523_044203_20778933` / 跳: score=`5.798`, frames=`30`, hand_presence=`0.767`, mode=`semantic_action_window`
- `web_20260523_044135_12fbd5bc` / 跳: score=`6.283`, frames=`30`, hand_presence=`0.767`, mode=`semantic_action_window`
- `web_20260523_001204_d3564a22` / 香蕉: score=`6.372`, frames=`15`, hand_presence=`0.067`, mode=`semantic_action_window`
- `web_20260522_231259_51a8c719` / 花: score=`7.263`, frames=`6`, hand_presence=`0.500`, mode=`full_sequence_with_action_window_diagnostics`
- `web_20260523_031147_55d51ab9` / 跳: score=`7.676`, frames=`30`, hand_presence=`0.600`, mode=`semantic_action_window`
- `web_20260523_001216_53df594b` / 香蕉: score=`8.115`, frames=`15`, hand_presence=`0.533`, mode=`semantic_action_window`
- `web_20260523_001241_e882a59e` / 香蕉: score=`8.917`, frames=`30`, hand_presence=`0.533`, mode=`semantic_action_window`
- `web_20260523_024025_9c6cf572` / 跳: score=`9.551`, frames=`30`, hand_presence=`0.600`, mode=`semantic_action_window`
- `web_20260523_031247_f927176a` / 跳: score=`10.193`, frames=`15`, hand_presence=`0.933`, mode=`semantic_action_window`
- `web_20260523_011135_5967dd5a` / 跳: score=`10.343`, frames=`30`, hand_presence=`0.700`, mode=`semantic_action_window`
- `web_20260523_044018_960618af` / 跳: score=`10.736`, frames=`30`, hand_presence=`0.767`, mode=`semantic_action_window`
- `web_20260523_031219_0da0bd96` / 跳: score=`11.470`, frames=`15`, hand_presence=`0.733`, mode=`semantic_action_window`
- `web_20260523_001113_b486eb41` / 跳: score=`11.520`, frames=`15`, hand_presence=`0.600`, mode=`semantic_action_window`
- `web_20260523_024000_dd35e1bb` / 跳: score=`11.561`, frames=`30`, hand_presence=`0.900`, mode=`semantic_action_window`
- `web_20260523_005941_0ec0ccab` / 跳: score=`11.663`, frames=`15`, hand_presence=`0.800`, mode=`semantic_action_window`
- `web_20260523_001152_83546751` / 跳: score=`11.722`, frames=`15`, hand_presence=`0.667`, mode=`semantic_action_window`

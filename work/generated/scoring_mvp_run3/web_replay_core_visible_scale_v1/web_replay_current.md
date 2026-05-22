# 网页测试样本当前算法回放

- 生成时间：`2026-05-23T06:30:19`
- Web 样本根目录：`work/generated/web_scoring_mvp`
- 语义 profile：`work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：复查已保存网页/API 帧切片样本，不重新运行浏览器采集。
- 分段：`normal_like >= 75`，`60 <= borderline < 75`，`low < 60`；这仍不是正式用户阈值。

## 总览

- 样本数：`140`
- 错误数：`0`
- 当前正常区间：`38`
- 当前边界区间：`21`
- 当前低分区间：`81`
- 旧均分：`34.350`
- 新均分：`41.660`

## 分词条

| 词条 | 样本数 | 正常 | 边界 | 低分 | 旧均分 | 新均分 | 手部覆盖均值 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 汽车 | 3 | 0 | 0 | 3 | 4.487 | 16.905 | 0.833 |
| 花 | 77 | 30 | 21 | 26 | 45.984 | 61.329 | 0.716 |
| 虎 | 2 | 0 | 0 | 2 | 17.753 | 17.755 | 0.780 |
| 跳 | 47 | 8 | 0 | 39 | 22.632 | 19.076 | 0.755 |
| 香蕉 | 11 | 0 | 0 | 11 | 14.152 | 11.564 | 0.576 |

## 最新样本

| request | 词条 | 帧数 | 旧分 | 新分 | 分段 | 手部覆盖 | 对齐 |
|---|---|---:|---:|---:|---|---:|---|
| web_20260523_053128_81d821bf | 花 | 25 | 66.174 | 75.568 | normal_like | 0.680 | full_sequence_with_action_window_diagnostics |
| web_20260523_053203_4ec1e6ab | 花 | 25 | 63.884 | 74.646 | borderline | 0.680 | full_sequence_with_action_window_diagnostics |
| web_20260523_053241_5fbbf9c7 | 跳 | 25 | 12.563 | 8.459 | low | 0.920 | semantic_action_window |
| web_20260523_053254_bd7f1d1c | 跳 | 25 | 11.098 | 3.045 | low | 0.880 | semantic_action_window |
| web_20260523_053309_28821cfd | 跳 | 25 | 12.114 | 3.491 | low | 0.840 | semantic_action_window |
| web_20260523_053345_da4d1ec9 | 跳 | 25 | 23.827 | 2.366 | low | 0.760 | semantic_action_window |
| web_20260523_053401_8934d89a | 跳 | 25 | 38.408 | 3.643 | low | 0.840 | semantic_action_window |
| web_20260523_053940_f86fc279 | 跳 | 25 | 20.724 | 2.202 | low | 0.760 | semantic_action_window |
| web_20260523_054426_114ad88f | 虎 | 25 | 13.139 | 13.139 | low | 0.960 | full_sequence_with_action_window_diagnostics |
| web_20260523_054448_4f0ebbd6 | 虎 | 25 | 22.367 | 22.371 | low | 0.600 | full_sequence_with_action_window_diagnostics |
| web_20260523_054508_865bd606 | 香蕉 | 25 | 17.227 | 18.702 | low | 0.800 | full_sequence_with_action_window_diagnostics |
| web_20260523_054643_16ed6eb8 | 汽车 | 25 | 6.080 | 17.469 | low | 0.800 | full_sequence_with_action_window_diagnostics |
| web_20260523_054658_9edec32b | 汽车 | 20 | 3.969 | 12.794 | low | 0.850 | full_sequence_with_action_window_diagnostics |
| web_20260523_054709_566e6021 | 汽车 | 20 | 3.413 | 20.453 | low | 0.850 | full_sequence_with_action_window_diagnostics |
| web_20260523_062341_afa8c368 | 花 | 20 | 19.344 | 21.202 | low | 1.000 | full_sequence_with_action_window_diagnostics |
| web_20260523_062353_2b6f64cd | 花 | 25 | 64.029 | 74.594 | borderline | 0.760 | full_sequence_with_action_window_diagnostics |
| web_20260523_062406_09525c5f | 花 | 25 | 71.442 | 76.465 | normal_like | 0.720 | full_sequence_with_action_window_diagnostics |
| web_20260523_062420_5aea4dd9 | 花 | 25 | 61.903 | 72.539 | borderline | 0.800 | full_sequence_with_action_window_diagnostics |
| web_20260523_062433_e3e870b6 | 花 | 25 | 70.370 | 76.433 | normal_like | 0.680 | full_sequence_with_action_window_diagnostics |
| web_20260523_062644_9a457871 | 花 | 25 | 75.787 | 75.787 | normal_like | 0.680 | full_sequence_with_action_window_diagnostics |

## 低分样本排查

- `web_20260523_031147_55d51ab9` / 跳: score=`0.833`, frames=`30`, hand_presence=`0.600`, mode=`semantic_action_window`
- `web_20260523_010014_049faf7d` / 跳: score=`1.070`, frames=`15`, hand_presence=`0.467`, mode=`semantic_action_window`
- `web_20260523_001113_b486eb41` / 跳: score=`1.239`, frames=`15`, hand_presence=`0.600`, mode=`semantic_action_window`
- `web_20260523_005953_cdf0697d` / 跳: score=`1.346`, frames=`15`, hand_presence=`0.400`, mode=`semantic_action_window`
- `web_20260523_053940_f86fc279` / 跳: score=`2.202`, frames=`25`, hand_presence=`0.760`, mode=`semantic_action_window`
- `web_20260523_053345_da4d1ec9` / 跳: score=`2.366`, frames=`25`, hand_presence=`0.760`, mode=`semantic_action_window`
- `web_20260523_053254_bd7f1d1c` / 跳: score=`3.045`, frames=`25`, hand_presence=`0.880`, mode=`semantic_action_window`
- `web_20260523_011135_5967dd5a` / 跳: score=`3.176`, frames=`30`, hand_presence=`0.700`, mode=`semantic_action_window`
- `web_20260523_053309_28821cfd` / 跳: score=`3.491`, frames=`25`, hand_presence=`0.840`, mode=`semantic_action_window`
- `web_20260523_001048_5bcb9948` / 跳: score=`3.528`, frames=`15`, hand_presence=`0.600`, mode=`semantic_action_window`
- `web_20260523_053401_8934d89a` / 跳: score=`3.643`, frames=`25`, hand_presence=`0.840`, mode=`semantic_action_window`
- `web_20260523_024025_9c6cf572` / 跳: score=`3.769`, frames=`30`, hand_presence=`0.600`, mode=`semantic_action_window`
- `web_20260523_010145_82035a51` / 香蕉: score=`3.780`, frames=`30`, hand_presence=`0.633`, mode=`semantic_action_window`
- `web_20260523_001100_dea381ee` / 跳: score=`3.844`, frames=`15`, hand_presence=`0.533`, mode=`semantic_action_window`
- `web_20260523_024000_dd35e1bb` / 跳: score=`4.123`, frames=`30`, hand_presence=`0.900`, mode=`semantic_action_window`
- `web_20260523_010119_d0158d2a` / 香蕉: score=`4.141`, frames=`30`, hand_presence=`0.467`, mode=`semantic_action_window`
- `web_20260523_044203_20778933` / 跳: score=`4.186`, frames=`30`, hand_presence=`0.767`, mode=`semantic_action_window`
- `web_20260523_001229_690e6b5a` / 香蕉: score=`4.227`, frames=`30`, hand_presence=`0.700`, mode=`semantic_action_window`
- `web_20260523_044018_960618af` / 跳: score=`4.328`, frames=`30`, hand_presence=`0.767`, mode=`semantic_action_window`
- `web_20260523_021604_9c415199` / 跳: score=`4.784`, frames=`60`, hand_presence=`0.717`, mode=`semantic_action_window`

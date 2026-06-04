# 网页测试样本当前算法回放

- 生成时间：`2026-06-02T21:29:54`
- Web 样本根目录：`/data/WYC/signLanguage/work/generated/web_scoring_mvp`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：复查已保存网页/API 帧切片样本，不重新运行浏览器采集。
- 分段：`normal_like >= 75`，`60 <= borderline < 75`，`low < 60`；这仍不是正式用户阈值。

## 总览

- 样本数：`155`
- 错误数：`0`
- 当前正常区间：`51`
- 当前边界区间：`32`
- 当前低分区间：`72`
- 旧均分：`34.366`
- 新均分：`49.422`

## 分词条

| 词条 | 样本数 | 正常 | 边界 | 低分 | 旧均分 | 新均分 | 手部覆盖均值 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 汽车 | 3 | 0 | 0 | 3 | 4.487 | 16.905 | 0.833 |
| 花 | 85 | 34 | 21 | 30 | 46.690 | 60.591 | 0.714 |
| 虎 | 2 | 0 | 0 | 2 | 17.753 | 17.755 | 0.780 |
| 跳 | 52 | 17 | 11 | 24 | 21.465 | 43.450 | 0.768 |
| 香蕉 | 13 | 0 | 0 | 13 | 14.847 | 12.657 | 0.601 |

## 最新样本

| request | 词条 | 帧数 | 旧分 | 新分 | 分段 | 手部覆盖 | 对齐 |
|---|---|---:|---:|---:|---|---:|---|
| web_20260523_062353_2b6f64cd | 花 | 25 | 64.029 | 74.594 | borderline | 0.760 | full_sequence_with_action_window_diagnostics |
| web_20260523_062406_09525c5f | 花 | 25 | 71.442 | 76.465 | normal_like | 0.720 | full_sequence_with_action_window_diagnostics |
| web_20260523_062420_5aea4dd9 | 花 | 25 | 61.903 | 72.539 | borderline | 0.800 | full_sequence_with_action_window_diagnostics |
| web_20260523_062433_e3e870b6 | 花 | 25 | 70.370 | 76.433 | normal_like | 0.680 | full_sequence_with_action_window_diagnostics |
| web_20260523_062644_9a457871 | 花 | 25 | 75.787 | 75.787 | normal_like | 0.680 | full_sequence_with_action_window_diagnostics |
| web_20260523_063002_0aa1419e | 跳 | 25 | 4.240 | 4.240 | low | 0.840 | semantic_action_window |
| web_20260523_063015_4017237e | 跳 | 25 | 8.919 | 8.919 | low | 0.840 | semantic_action_window |
| web_20260523_063026_c2f04725 | 跳 | 25 | 12.248 | 71.075 | borderline | 0.920 | semantic_action_window |
| web_20260523_063052_fc94e4f7 | 跳 | 25 | 17.520 | 75.147 | normal_like | 0.840 | semantic_action_window |
| web_20260523_063109_8727dac1 | 跳 | 25 | 9.551 | 65.191 | borderline | 1.000 | semantic_action_window |
| web_20260523_063159_324827f7 | 花 | 15 | 29.607 | 29.607 | low | 0.667 | full_sequence_with_action_window_diagnostics |
| web_20260523_063217_bd40ee0c | 花 | 30 | 76.891 | 76.891 | normal_like | 0.733 | full_sequence_with_action_window_diagnostics |
| web_20260523_063230_6a3bad1f | 花 | 25 | 75.760 | 75.760 | normal_like | 0.680 | full_sequence_with_action_window_diagnostics |
| web_20260523_071212_4547d033 | 花 | 25 | 45.047 | 45.047 | low | 0.600 | full_sequence_with_action_window_diagnostics |
| web_20260523_071306_071a2172 | 花 | 15 | 19.958 | 19.958 | low | 0.600 | full_sequence_with_action_window_diagnostics |
| web_20260523_071320_415e2975 | 花 | 15 | 30.132 | 30.132 | low | 0.800 | full_sequence_with_action_window_diagnostics |
| web_20260523_071339_f3f432d2 | 花 | 25 | 75.516 | 75.516 | normal_like | 0.680 | full_sequence_with_action_window_diagnostics |
| web_20260523_071415_2505a91e | 花 | 25 | 75.014 | 75.014 | normal_like | 0.800 | full_sequence_with_action_window_diagnostics |
| web_20260523_071625_56ba01dd | 香蕉 | 25 | 18.958 | 18.958 | low | 0.640 | full_sequence_with_action_window_diagnostics |
| web_20260523_071637_e4994b8c | 香蕉 | 25 | 18.377 | 18.377 | low | 0.840 | full_sequence_with_action_window_diagnostics |

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
- `web_20260523_053401_8934d89a` / 跳: score=`3.643`, frames=`25`, hand_presence=`0.840`, mode=`semantic_action_window`
- `web_20260523_024025_9c6cf572` / 跳: score=`3.769`, frames=`30`, hand_presence=`0.600`, mode=`semantic_action_window`
- `web_20260523_010145_82035a51` / 香蕉: score=`3.780`, frames=`30`, hand_presence=`0.633`, mode=`semantic_action_window`
- `web_20260523_001100_dea381ee` / 跳: score=`3.844`, frames=`15`, hand_presence=`0.533`, mode=`semantic_action_window`
- `web_20260523_024000_dd35e1bb` / 跳: score=`4.123`, frames=`30`, hand_presence=`0.900`, mode=`semantic_action_window`
- `web_20260523_010119_d0158d2a` / 香蕉: score=`4.141`, frames=`30`, hand_presence=`0.467`, mode=`semantic_action_window`
- `web_20260523_044203_20778933` / 跳: score=`4.186`, frames=`30`, hand_presence=`0.767`, mode=`semantic_action_window`
- `web_20260523_001229_690e6b5a` / 香蕉: score=`4.227`, frames=`30`, hand_presence=`0.700`, mode=`semantic_action_window`
- `web_20260523_063002_0aa1419e` / 跳: score=`4.240`, frames=`25`, hand_presence=`0.840`, mode=`semantic_action_window`
- `web_20260523_044018_960618af` / 跳: score=`4.328`, frames=`30`, hand_presence=`0.767`, mode=`semantic_action_window`
- `web_20260523_021604_9c415199` / 跳: score=`4.784`, frames=`60`, hand_presence=`0.717`, mode=`semantic_action_window`

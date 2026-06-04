# 网页测试样本当前算法回放

- 生成时间：`2026-06-03T05:20:30`
- Web 样本根目录：`/data/WYC/signLanguage/work/generated/web_scoring_mvp`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 标准库覆盖：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 口径：query 复用保存的网页/API Holistic JSON，standard 改用当前标准库，模拟当前后端在线评分。
- 分段：`normal_like >= 75`，`60 <= borderline < 75`，`low < 60`；这仍不是正式用户阈值。

## 总览

- 样本数：`168`
- 错误数：`0`
- 当前正常区间：`102`
- 当前边界区间：`22`
- 当前低分区间：`44`
- 旧均分：`35.442`
- 新均分：`60.410`

## 分词条

| 词条 | 样本数 | 正常 | 边界 | 低分 | 旧均分 | 新均分 | 手部覆盖均值 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 月亮 | 1 | 0 | 0 | 1 | 21.343 | 21.343 | 0.800 |
| 汽车 | 3 | 0 | 0 | 3 | 4.487 | 16.905 | 0.833 |
| 花 | 93 | 81 | 6 | 6 | 46.655 | 74.513 | 0.708 |
| 虎 | 2 | 0 | 0 | 2 | 17.753 | 17.755 | 0.780 |
| 跳 | 56 | 21 | 16 | 19 | 24.144 | 52.002 | 0.771 |
| 香蕉 | 13 | 0 | 0 | 13 | 14.847 | 15.340 | 0.601 |

## 最新样本

| request | 词条 | 帧数 | 旧分 | 新分 | 分段 | 手部覆盖 | 对齐 |
|---|---|---:|---:|---:|---|---:|---|
| web_20260523_071212_4547d033 | 花 | 25 | 45.047 | 79.560 | normal_like | 0.600 | full_sequence_with_action_window_diagnostics |
| web_20260523_071306_071a2172 | 花 | 15 | 19.958 | 76.923 | normal_like | 0.600 | full_sequence_with_action_window_diagnostics |
| web_20260523_071320_415e2975 | 花 | 15 | 30.132 | 78.392 | normal_like | 0.800 | full_sequence_with_action_window_diagnostics |
| web_20260523_071339_f3f432d2 | 花 | 25 | 75.516 | 79.410 | normal_like | 0.680 | full_sequence_with_action_window_diagnostics |
| web_20260523_071415_2505a91e | 花 | 25 | 75.014 | 79.116 | normal_like | 0.800 | full_sequence_with_action_window_diagnostics |
| web_20260523_071625_56ba01dd | 香蕉 | 25 | 18.958 | 18.958 | low | 0.640 | full_sequence_with_action_window_diagnostics |
| web_20260523_071637_e4994b8c | 香蕉 | 25 | 18.377 | 18.377 | low | 0.840 | full_sequence_with_action_window_diagnostics |
| web_20260602_212933_7ad54f26 | 花 | 15 | 14.863 | 14.863 | low | 0.000 | full_sequence_with_action_window_diagnostics |
| web_20260602_212951_e1173da1 | 花 | 15 | 29.565 | 77.625 | normal_like | 0.800 | full_sequence_with_action_window_diagnostics |
| web_20260602_213015_411a2ecd | 花 | 30 | 53.813 | 78.861 | normal_like | 0.633 | full_sequence_with_action_window_diagnostics |
| web_20260602_213030_368950ee | 花 | 25 | 44.503 | 78.355 | normal_like | 0.480 | full_sequence_with_action_window_diagnostics |
| web_20260602_213050_ec3d0907 | 花 | 25 | 67.993 | 79.517 | normal_like | 0.720 | full_sequence_with_action_window_diagnostics |
| web_20260602_213918_4947c25e | 花 | 25 | 79.707 | 79.707 | normal_like | 0.720 | full_sequence_with_action_window_diagnostics |
| web_20260602_214010_3f951c51 | 跳 | 25 | 75.325 | 75.325 | normal_like | 0.880 | semantic_action_window |
| web_20260602_214656_3fae071b | 跳 | 25 | 1.354 | 1.354 | low | 0.480 | semantic_action_window |
| web_20260602_223143_ed591b11 | 月亮 | 25 | 21.343 | 21.343 | low | 0.800 | full_sequence_with_action_window_diagnostics |
| web_20260602_233301_233b8215 | 花 | 6 | 2.913 | 2.913 | low | 1.000 | full_sequence_with_action_window_diagnostics |
| web_20260602_233302_d92c0ce2 | 跳 | 9 | 70.661 | 70.661 | borderline | 1.000 | semantic_action_window |
| web_20260602_233343_899e6970 | 花 | 53 | 76.899 | 76.899 | normal_like | 0.792 | full_sequence_with_action_window_diagnostics |
| web_20260602_233348_53e3df5d | 跳 | 19 | 88.577 | 88.577 | normal_like | 0.895 | semantic_action_window |

## 低分样本排查

- `web_20260523_031147_55d51ab9` / 跳: score=`0.833`, frames=`30`, hand_presence=`0.600`, mode=`semantic_action_window`
- `web_20260602_214656_3fae071b` / 跳: score=`1.354`, frames=`25`, hand_presence=`0.480`, mode=`semantic_action_window`
- `web_20260523_053940_f86fc279` / 跳: score=`2.202`, frames=`25`, hand_presence=`0.760`, mode=`semantic_action_window`
- `web_20260523_053345_da4d1ec9` / 跳: score=`2.366`, frames=`25`, hand_presence=`0.760`, mode=`semantic_action_window`
- `web_20260523_001113_b486eb41` / 跳: score=`2.501`, frames=`15`, hand_presence=`0.600`, mode=`semantic_action_window`
- `web_20260602_233301_233b8215` / 花: score=`2.913`, frames=`6`, hand_presence=`1.000`, mode=`full_sequence_with_action_window_diagnostics`
- `web_20260523_053254_bd7f1d1c` / 跳: score=`3.045`, frames=`25`, hand_presence=`0.880`, mode=`semantic_action_window`
- `web_20260523_011135_5967dd5a` / 跳: score=`3.111`, frames=`30`, hand_presence=`0.700`, mode=`semantic_action_window`
- `web_20260523_053309_28821cfd` / 跳: score=`3.491`, frames=`25`, hand_presence=`0.840`, mode=`semantic_action_window`
- `web_20260523_053401_8934d89a` / 跳: score=`3.643`, frames=`25`, hand_presence=`0.840`, mode=`semantic_action_window`
- `web_20260523_010014_049faf7d` / 跳: score=`3.680`, frames=`15`, hand_presence=`0.467`, mode=`semantic_action_window`
- `web_20260523_024025_9c6cf572` / 跳: score=`3.769`, frames=`30`, hand_presence=`0.600`, mode=`semantic_action_window`
- `web_20260523_044203_20778933` / 跳: score=`4.186`, frames=`30`, hand_presence=`0.767`, mode=`semantic_action_window`
- `web_20260523_063002_0aa1419e` / 跳: score=`4.240`, frames=`25`, hand_presence=`0.840`, mode=`semantic_action_window`
- `web_20260523_005953_cdf0697d` / 跳: score=`4.450`, frames=`15`, hand_presence=`0.400`, mode=`semantic_action_window`
- `web_20260523_021604_9c415199` / 跳: score=`4.784`, frames=`60`, hand_presence=`0.717`, mode=`semantic_action_window`
- `web_20260523_001100_dea381ee` / 跳: score=`4.973`, frames=`15`, hand_presence=`0.533`, mode=`semantic_action_window`
- `web_20260523_024037_ff5b3fb5` / 跳: score=`6.227`, frames=`30`, hand_presence=`0.833`, mode=`semantic_action_window`
- `web_20260523_020951_6ff2657c` / 跳: score=`7.283`, frames=`60`, hand_presence=`0.667`, mode=`semantic_action_window`
- `web_20260523_001229_690e6b5a` / 香蕉: score=`7.338`, frames=`30`, hand_presence=`0.700`, mode=`full_sequence_with_action_window_diagnostics`

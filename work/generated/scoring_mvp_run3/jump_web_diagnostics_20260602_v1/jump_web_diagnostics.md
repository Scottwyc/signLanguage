# 跳 网页样本语义诊断

- 生成时间：`2026-06-02T21:49:57`
- 样本数：`54`
- 口径：读取已保存网页 Holistic JSON，用当前评分模块复算，不重新运行 Holistic。

## 分段

- `low`: `26`
- `normal`: `18`
- `borderline`: `10`

## 低分诊断分类

- `accepted`: `28`
- `two_hand_presence_low`: `19`
- `relation_direction_mismatch`: `6`
- `weak_vertical_jump`: `1`

## 最新样本

| request | score | band | diagnosis | floor_reason | L/R presence | relation | dir | vertical | amp |
|---|---:|---|---|---|---:|---:|---:|---:|---:|
| web_20260523_044135_12fbd5bc | 4.983 | low | relation_direction_mismatch | relation_direction_mismatch | 0.88/0.88 | 0.448 | -0.857 |  |  |
| web_20260523_044203_20778933 | 4.186 | low | two_hand_presence_low | insufficient_two_hand_presence | 0.50/0.88 | 0.238 |  |  |  |
| web_20260523_044323_2eb9eb7e | 75.484 | normal | accepted | used | 1.00/1.00 | 0.507 | 0.778 | 1.000 | 4.065 |
| web_20260523_044336_5d15d099 | 70.853 | borderline | accepted | used | 0.71/1.00 | 0.607 | 0.820 | 1.000 | 3.250 |
| web_20260523_044358_00db9d4d | 68.517 | borderline | accepted | used | 0.71/1.00 | 0.614 | 0.762 | 1.000 | 5.442 |
| web_20260523_052715_1ad3c2d2 | 78.026 | normal | accepted | used | 1.00/1.00 | 0.208 | 0.816 | 1.000 | 1.725 |
| web_20260523_052731_8f51941f | 75.933 | normal | accepted | used | 1.00/1.00 | 0.608 | 0.790 | 1.000 | 3.925 |
| web_20260523_053241_5fbbf9c7 | 75.983 | normal | accepted | used | 1.00/1.00 | 0.517 | 0.801 | 1.000 | 4.951 |
| web_20260523_053254_bd7f1d1c | 3.045 | low | two_hand_presence_low | insufficient_two_hand_presence | 0.43/1.00 | 0.501 |  |  |  |
| web_20260523_053309_28821cfd | 3.491 | low | two_hand_presence_low | insufficient_two_hand_presence | 0.57/1.00 | 0.428 |  |  |  |
| web_20260523_053345_da4d1ec9 | 2.366 | low | two_hand_presence_low | insufficient_two_hand_presence | 0.00/1.00 | 0.000 |  |  |  |
| web_20260523_053401_8934d89a | 3.643 | low | two_hand_presence_low | insufficient_two_hand_presence | 0.00/1.00 | 0.000 |  |  |  |
| web_20260523_053940_f86fc279 | 2.202 | low | two_hand_presence_low | insufficient_two_hand_presence | 0.43/0.86 | 0.286 |  |  |  |
| web_20260523_063002_0aa1419e | 4.240 | low | two_hand_presence_low | insufficient_two_hand_presence | 0.29/1.00 | 0.124 |  |  |  |
| web_20260523_063015_4017237e | 8.919 | low | two_hand_presence_low | insufficient_two_hand_presence | 0.43/1.00 | 0.151 |  |  |  |
| web_20260523_063026_c2f04725 | 71.075 | borderline | accepted | used | 0.86/1.00 | 0.545 | 0.740 | 1.000 | 4.613 |
| web_20260523_063052_fc94e4f7 | 75.147 | normal | accepted | used | 1.00/1.00 | 0.275 | 0.764 | 1.000 | 3.728 |
| web_20260523_063109_8727dac1 | 65.191 | borderline | accepted | used | 0.62/1.00 | 0.229 | 0.699 | 1.000 | 3.814 |
| web_20260602_214010_3f951c51 | 75.325 | normal | accepted | used | 1.00/1.00 | 0.577 | 0.771 | 1.000 | 3.924 |
| web_20260602_214656_3fae071b | 1.354 | low | two_hand_presence_low | insufficient_two_hand_presence | 0.14/0.71 | 0.000 |  |  |  |

## 最低分样本

| request | score | diagnosis | floor_reason | L/R presence | right hand/shape | relation |
|---|---:|---|---|---:|---:|---:|
| web_20260523_031147_55d51ab9 | 0.833 | two_hand_presence_low | insufficient_two_hand_presence | 0.25/0.62 | 0.145/0.164 | 0.268 |
| web_20260602_214656_3fae071b | 1.354 | two_hand_presence_low | insufficient_two_hand_presence | 0.14/0.71 | 0.265/0.214 | 0.000 |
| web_20260523_053940_f86fc279 | 2.202 | two_hand_presence_low | insufficient_two_hand_presence | 0.43/0.86 | 0.201/0.283 | 0.286 |
| web_20260523_053345_da4d1ec9 | 2.366 | two_hand_presence_low | insufficient_two_hand_presence | 0.00/1.00 | 0.270/0.266 | 0.000 |
| web_20260523_001113_b486eb41 | 2.501 | two_hand_presence_low | insufficient_two_hand_presence | 0.00/1.00 | 0.150/0.288 | 0.000 |
| web_20260523_053254_bd7f1d1c | 3.045 | two_hand_presence_low | insufficient_two_hand_presence | 0.43/1.00 | 0.207/0.270 | 0.501 |
| web_20260523_011135_5967dd5a | 3.111 | two_hand_presence_low | insufficient_two_hand_presence | 0.50/0.88 | 0.233/0.288 | 0.481 |
| web_20260523_053309_28821cfd | 3.491 | two_hand_presence_low | insufficient_two_hand_presence | 0.57/1.00 | 0.183/0.278 | 0.428 |
| web_20260523_053401_8934d89a | 3.643 | two_hand_presence_low | insufficient_two_hand_presence | 0.00/1.00 | 0.271/0.264 | 0.000 |
| web_20260523_010014_049faf7d | 3.680 | two_hand_presence_low | insufficient_two_hand_presence | 1.00/0.33 | 0.197/0.280 | 0.320 |
| web_20260523_024025_9c6cf572 | 3.769 | two_hand_presence_low | insufficient_two_hand_presence | 0.50/1.00 | 0.197/0.271 | 0.353 |
| web_20260523_024000_dd35e1bb | 4.123 | relation_direction_mismatch | relation_direction_mismatch | 1.00/0.75 | 0.187/0.239 | 0.457 |
| web_20260523_044203_20778933 | 4.186 | two_hand_presence_low | insufficient_two_hand_presence | 0.50/0.88 | 0.163/0.256 | 0.238 |
| web_20260523_063002_0aa1419e | 4.240 | two_hand_presence_low | insufficient_two_hand_presence | 0.29/1.00 | 0.195/0.282 | 0.124 |
| web_20260523_044018_960618af | 4.328 | relation_direction_mismatch | relation_direction_mismatch | 1.00/0.62 | 0.179/0.235 | 0.552 |
| web_20260523_005953_cdf0697d | 4.450 | two_hand_presence_low | insufficient_two_hand_presence | 1.00/0.33 | 0.185/0.282 | 0.298 |
| web_20260523_021604_9c415199 | 4.784 | two_hand_presence_low | insufficient_two_hand_presence | 0.12/1.00 | 0.198/0.265 | 0.000 |
| web_20260523_001100_dea381ee | 4.973 | two_hand_presence_low | insufficient_two_hand_presence | 0.50/1.00 | 0.183/0.289 | 0.445 |
| web_20260523_044135_12fbd5bc | 4.983 | relation_direction_mismatch | relation_direction_mismatch | 0.88/0.88 | 0.222/0.245 | 0.448 |
| web_20260523_001048_5bcb9948 | 5.354 | relation_direction_mismatch | relation_direction_mismatch | 0.67/1.00 | 0.198/0.287 | 0.675 |

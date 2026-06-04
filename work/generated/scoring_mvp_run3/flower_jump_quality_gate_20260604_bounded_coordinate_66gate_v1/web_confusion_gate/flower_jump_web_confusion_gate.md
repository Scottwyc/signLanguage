# 花/跳网页样本交叉混淆门

- 生成时间：`2026-06-04T04:17:22`
- Web 样本根目录：`/data/WYC/signLanguage/work/generated/web_scoring_mvp`
- 当前标准库：`/data/WYC/signLanguage/work/generated/scoring_mvp_run3/all_demo_step2_worker_cache_semantic_v1/results`
- 语义 profile：`/data/WYC/signLanguage/work/generated/scoring_semantic_profiles/sign_semantic_weights.json`
- 口径：只读保存的网页 Holistic JSON；同一 query 分别按 `花` 和 `跳` 当前模板复算；不调用 `/api/score`，不重启 Holistic。
- 适用范围：只把目标词自身 `score_valid/semantic_mismatch` 且目标分数 `>= min_target_score` 的样本纳入交叉混淆 gate；重采样本和低分语义失败样本不用于证明跨词区分度。

- 5080 状态：worker=`ready`，worker_pid=`811485`，reload_count=`16`，last_reload_error=`None`

## 结论

- 综合状态：`PASS`
- 目标最低分：`60.0`
- 交叉最高分：`55.0`
- 目标-交叉最小 margin：`15.0`

| gate | 结果 | 说明 |
|---|---|---|
| backend_ready | PASS | worker=ready, reload_error=-, error=- |
| no_errors | PASS | errors=0, samples=149 |
| all_eligible_pass | PASS | eligible=124, pass=124, fail=0 |
| eligible_花 | PASS | eligible=87, min=1, samples=93 |
| confusion_pass_花 | PASS | pass=87, fail=0, other_score_max=8.218, margin_min=59.840 |
| eligible_跳 | PASS | eligible=37, min=1, samples=56 |
| confusion_pass_跳 | PASS | pass=37, fail=0, other_score_max=41.535, margin_min=29.317 |

## 分词条

| 词条 | 样本 | eligible | pass | fail | 目标均分 | 交叉最高 | margin 最低 | margin 均值 | 原因 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 花 | 93 | 87 | 87 | 0 | 77.862 | 8.218 | 59.840 | 75.514 | {'passed': 87, 'not_eligible': 6} |
| 跳 | 56 | 37 | 37 | 0 | 76.677 | 41.535 | 29.317 | 54.982 | {'passed': 37, 'not_eligible': 19} |

## 失败样本

- 无 eligible 失败样本。

## Eligible 明细

| request | 目标 | 目标分 | 交叉词 | 交叉分 | margin | pass | 目标状态 | 目标原因 | 交叉原因 |
|---|---|---:|---|---:|---:|---|---|---|---|
| web_20260523_041618_e930772c | 花 | 64.610 | 跳 | 4.770 | 59.840 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_020825_2312ad97 | 花 | 63.318 | 跳 | 1.876 | 61.442 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_032344_77c9db0c | 花 | 66.465 | 跳 | 4.569 | 61.896 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_020843_6ba8acd9 | 花 | 66.857 | 跳 | 4.067 | 62.790 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_010203_88bdaf53 | 花 | 72.184 | 跳 | 8.218 | 63.965 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260602_233343_899e6970 | 花 | 76.899 | 跳 | 7.474 | 69.425 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260522_232319_7e3cc881 | 花 | 76.456 | 跳 | 4.500 | 71.956 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_043910_b186b6a6 | 花 | 76.695 | 跳 | 4.606 | 72.089 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260522_222243_a23d679c | 花 | 74.854 | 跳 | 2.599 | 72.256 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_031125_9cc568f2 | 花 | 79.240 | 跳 | 6.307 | 72.933 | True | score_valid | score_valid | phase_order_disorder |
| web_20260523_041345_488a62c3 | 花 | 79.240 | 跳 | 6.307 | 72.933 | True | score_valid | score_valid | phase_order_disorder |
| web_20260523_041443_0292d680 | 花 | 79.240 | 跳 | 6.307 | 72.933 | True | score_valid | score_valid | phase_order_disorder |
| web_20260523_043442_e00f8b9c | 花 | 79.240 | 跳 | 6.307 | 72.933 | True | score_valid | score_valid | phase_order_disorder |
| web_20260523_023716_bb545221 | 花 | 75.533 | 跳 | 1.925 | 73.608 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_005246_dbadcd43 | 花 | 76.232 | 跳 | 2.531 | 73.701 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_023452_bd691c4f | 花 | 79.398 | 跳 | 5.590 | 73.809 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_030621_977512c9 | 花 | 79.398 | 跳 | 5.590 | 73.809 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_000032_5389521b | 花 | 76.168 | 跳 | 1.933 | 74.235 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_053035_073e5794 | 花 | 76.736 | 跳 | 2.311 | 74.425 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_020656_ffa06ed9 | 花 | 77.188 | 跳 | 2.590 | 74.598 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_071306_071a2172 | 花 | 76.923 | 跳 | 2.240 | 74.683 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260522_232420_60da4112 | 花 | 76.966 | 跳 | 1.993 | 74.973 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_020721_d12639c5 | 花 | 77.483 | 跳 | 2.395 | 75.088 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_000913_d5072c6f | 花 | 77.735 | 跳 | 2.382 | 75.352 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_000852_b2c2f1de | 花 | 77.765 | 跳 | 2.252 | 75.513 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_041652_402b253a | 花 | 76.878 | 跳 | 1.303 | 75.575 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260602_212951_e1173da1 | 花 | 77.625 | 跳 | 2.008 | 75.617 | True | score_valid | score_valid | phase_order_disorder |
| web_20260522_225845_b21e0f2e | 花 | 77.612 | 跳 | 1.828 | 75.785 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_015835_2dfac551 | 花 | 78.120 | 跳 | 2.287 | 75.832 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_020734_b9299448 | 花 | 78.082 | 跳 | 2.236 | 75.846 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_063159_324827f7 | 花 | 78.463 | 跳 | 2.541 | 75.922 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_000903_3123d2db | 花 | 78.349 | 跳 | 2.423 | 75.926 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_071320_415e2975 | 花 | 78.392 | 跳 | 2.441 | 75.951 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_023729_fe2e847d | 花 | 78.099 | 跳 | 2.147 | 75.953 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_023814_169a471d | 花 | 77.056 | 跳 | 1.092 | 75.964 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_031333_6c5f7460 | 花 | 77.239 | 跳 | 1.224 | 76.015 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260522_231304_9e8827a4 | 花 | 78.411 | 跳 | 2.288 | 76.123 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_071415_2505a91e | 花 | 79.116 | 跳 | 2.969 | 76.146 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_023751_844be9b0 | 花 | 78.308 | 跳 | 2.134 | 76.174 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_031304_c5ddfa0c | 花 | 78.401 | 跳 | 2.118 | 76.283 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_005533_c97daf95 | 花 | 78.616 | 跳 | 2.274 | 76.342 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260522_225356_550e19fe | 花 | 78.242 | 跳 | 1.834 | 76.408 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260522_232406_cac18708 | 花 | 77.951 | 跳 | 1.509 | 76.442 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260522_225852_a9aa43d6 | 花 | 78.662 | 跳 | 2.183 | 76.479 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260522_225823_46498d30 | 花 | 77.973 | 跳 | 1.366 | 76.607 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_062420_5aea4dd9 | 花 | 78.624 | 跳 | 1.898 | 76.726 | True | score_valid | score_valid | phase_order_disorder |
| web_20260523_020807_c15e8c2b | 花 | 78.768 | 跳 | 1.976 | 76.792 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_015736_2678050f | 花 | 77.843 | 跳 | 1.020 | 76.823 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_015755_80a348dd | 花 | 78.251 | 跳 | 1.167 | 77.084 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_042222_fac8359d | 花 | 78.342 | 跳 | 1.225 | 77.117 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_010215_ab4961d9 | 花 | 79.161 | 跳 | 1.957 | 77.203 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_052817_7ae13ce2 | 花 | 79.050 | 跳 | 1.846 | 77.204 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260522_232642_fe440fb9 | 花 | 79.846 | 跳 | 2.617 | 77.230 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_042024_ee2fc3da | 花 | 78.538 | 跳 | 1.157 | 77.380 | True | score_valid | score_valid | phase_order_disorder |
| web_20260523_062353_2b6f64cd | 花 | 79.530 | 跳 | 2.110 | 77.420 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_053051_a785c84e | 花 | 79.265 | 跳 | 1.809 | 77.456 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_043955_dd909904 | 花 | 79.007 | 跳 | 1.513 | 77.494 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_053116_49159767 | 花 | 79.454 | 跳 | 1.904 | 77.550 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_023830_033d7664 | 花 | 78.827 | 跳 | 1.247 | 77.580 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_071339_f3f432d2 | 花 | 79.410 | 跳 | 1.794 | 77.615 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_032325_7e7b2476 | 花 | 79.186 | 跳 | 1.489 | 77.697 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_041635_7421d5c0 | 花 | 78.940 | 跳 | 1.182 | 77.757 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_071212_4547d033 | 花 | 79.560 | 跳 | 1.791 | 77.769 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_015816_3c06955d | 花 | 78.228 | 跳 | 0.452 | 77.776 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_053102_e1ff4324 | 花 | 79.533 | 跳 | 1.747 | 77.786 | True | score_valid | score_valid | phase_order_disorder |
| web_20260523_041958_068b1181 | 花 | 79.023 | 跳 | 1.231 | 77.792 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_053203_4ec1e6ab | 花 | 79.595 | 跳 | 1.760 | 77.834 | True | score_valid | score_valid | phase_order_disorder |
| web_20260523_053128_81d821bf | 花 | 79.584 | 跳 | 1.722 | 77.862 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_052801_95c97bce | 花 | 79.322 | 跳 | 1.452 | 77.870 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_063230_6a3bad1f | 花 | 79.674 | 跳 | 1.774 | 77.900 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_062406_09525c5f | 花 | 80.022 | 跳 | 2.113 | 77.909 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_063217_bd40ee0c | 花 | 79.244 | 跳 | 1.316 | 77.928 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_052744_427c726a | 花 | 80.058 | 跳 | 2.121 | 77.937 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_043923_b95a60d0 | 花 | 79.204 | 跳 | 1.263 | 77.941 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260602_213050_ec3d0907 | 花 | 79.517 | 跳 | 1.547 | 77.969 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_042235_9431f1a0 | 花 | 79.199 | 跳 | 1.165 | 78.034 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_031317_966d9c05 | 花 | 79.240 | 跳 | 1.171 | 78.070 | True | score_valid | score_valid | phase_order_disorder |
| web_20260602_213030_368950ee | 花 | 78.355 | 跳 | 0.209 | 78.146 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_041708_24e7d28a | 花 | 79.266 | 跳 | 1.092 | 78.174 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_062644_9a457871 | 花 | 79.941 | 跳 | 1.750 | 78.191 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_042011_9284da87 | 花 | 79.815 | 跳 | 1.497 | 78.317 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_062433_e3e870b6 | 花 | 80.007 | 跳 | 1.688 | 78.319 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_005320_4bd5e0a3 | 花 | 80.784 | 跳 | 2.388 | 78.396 | True | score_valid | score_valid | phase_order_disorder |
| web_20260602_213015_411a2ecd | 花 | 78.861 | 跳 | 0.144 | 78.717 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260602_213918_4947c25e | 花 | 79.707 | 跳 | 0.955 | 78.751 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260522_232256_781c0807 | 花 | 79.818 | 跳 | 0.997 | 78.821 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260522_232339_70e4794b | 花 | 79.941 | 跳 | 1.094 | 78.847 | True | score_valid | score_valid | jump_two_hand_presence_low |
| web_20260523_044336_5d15d099 | 跳 | 70.853 | 花 | 41.535 | 29.317 | True | score_valid | score_valid | flower_opening_guard_failed |
| web_20260523_063109_8727dac1 | 跳 | 65.191 | 花 | 35.678 | 29.512 | True | score_valid | score_valid | flower_jump_like_two_hand_confusion |
| web_20260523_044358_00db9d4d | 跳 | 68.517 | 花 | 38.558 | 29.959 | True | score_valid | score_valid | flower_jump_like_two_hand_confusion |
| web_20260523_022509_a44cb853 | 跳 | 74.915 | 花 | 36.955 | 37.961 | True | score_valid | score_valid | flower_jump_like_two_hand_confusion |
| web_20260523_041735_ea1bbaa6 | 跳 | 73.255 | 花 | 34.439 | 38.816 | True | score_valid | score_valid | flower_jump_like_two_hand_confusion |
| web_20260523_011122_fb34e3e5 | 跳 | 69.526 | 花 | 30.115 | 39.411 | True | score_valid | score_valid | flower_opening_guard_failed |
| web_20260523_021622_26666615 | 跳 | 70.084 | 花 | 29.290 | 40.794 | True | score_valid | score_valid | flower_opening_guard_failed |
| web_20260523_044018_960618af | 跳 | 71.072 | 花 | 28.411 | 42.661 | True | score_valid | score_valid | flower_jump_like_two_hand_confusion |
| web_20260523_063026_c2f04725 | 跳 | 71.075 | 花 | 27.629 | 43.445 | True | score_valid | score_valid | flower_jump_like_two_hand_confusion |
| web_20260523_063052_fc94e4f7 | 跳 | 75.147 | 花 | 31.293 | 43.854 | True | score_valid | score_valid | flower_jump_like_two_hand_confusion |
| web_20260523_031134_8688f93f | 跳 | 77.610 | 花 | 32.779 | 44.831 | True | score_valid | score_valid | flower_jump_like_two_hand_confusion |
| web_20260523_044135_12fbd5bc | 跳 | 75.212 | 花 | 29.575 | 45.637 | True | score_valid | score_valid | flower_jump_like_two_hand_confusion |
| web_20260523_024000_dd35e1bb | 跳 | 72.943 | 花 | 24.700 | 48.243 | True | score_valid | score_valid | flower_jump_like_two_hand_confusion |
| web_20260602_214010_3f951c51 | 跳 | 75.325 | 花 | 26.618 | 48.707 | True | score_valid | score_valid | flower_jump_like_two_hand_confusion |
| web_20260523_044323_2eb9eb7e | 跳 | 75.484 | 花 | 25.936 | 49.548 | True | score_valid | score_valid | score_valid |
| web_20260523_052715_1ad3c2d2 | 跳 | 78.026 | 花 | 26.470 | 51.556 | True | score_valid | score_valid | flower_jump_like_two_hand_confusion |
| web_20260523_031219_0da0bd96 | 跳 | 66.510 | 花 | 13.965 | 52.545 | True | score_valid | score_valid | flower_jump_like_two_hand_confusion |
| web_20260523_052731_8f51941f | 跳 | 75.933 | 花 | 21.627 | 54.306 | True | score_valid | score_valid | flower_jump_like_two_hand_confusion |
| web_20260523_053241_5fbbf9c7 | 跳 | 75.983 | 花 | 20.057 | 55.926 | True | score_valid | score_valid | flower_jump_like_two_hand_confusion |
| web_20260523_021006_aef545ce | 跳 | 72.870 | 花 | 15.729 | 57.140 | True | score_valid | score_valid | flower_jump_like_two_hand_confusion |
| web_20260523_010234_e2d59e5e | 跳 | 73.052 | 花 | 15.902 | 57.150 | True | score_valid | score_valid | flower_opening_guard_failed |
| web_20260523_001048_5bcb9948 | 跳 | 74.194 | 花 | 15.672 | 58.522 | True | score_valid | score_valid | flower_opening_guard_failed |
| web_20260523_031235_d0de0d44 | 跳 | 72.543 | 花 | 12.828 | 59.715 | True | score_valid | score_valid | flower_opening_guard_failed |
| web_20260523_001152_83546751 | 跳 | 75.663 | 花 | 13.804 | 61.859 | True | score_valid | score_valid | flower_jump_like_two_hand_confusion |
| web_20260602_233302_d92c0ce2 | 跳 | 70.661 | 花 | 3.552 | 67.109 | True | score_valid | score_valid | flower_jump_like_two_hand_confusion |
| web_20260523_010004_7eaf7ee3 | 跳 | 83.040 | 花 | 14.050 | 68.990 | True | score_valid | score_valid | flower_opening_guard_failed |
| web_20260523_031247_f927176a | 跳 | 82.062 | 花 | 12.312 | 69.749 | True | score_valid | score_valid | flower_opening_guard_failed |
| web_20260523_005941_0ec0ccab | 跳 | 82.064 | 花 | 12.043 | 70.020 | True | score_valid | score_valid | flower_opening_guard_failed |
| web_20260523_031129_bd3988e8 | 跳 | 84.974 | 花 | 14.667 | 70.306 | True | score_valid | score_valid | flower_jump_like_two_hand_confusion |
| web_20260523_041350_ad02e9e5 | 跳 | 84.974 | 花 | 14.667 | 70.306 | True | score_valid | score_valid | flower_jump_like_two_hand_confusion |
| web_20260523_041447_f7341789 | 跳 | 84.974 | 花 | 14.667 | 70.306 | True | score_valid | score_valid | flower_jump_like_two_hand_confusion |
| web_20260523_043446_cbecd916 | 跳 | 84.974 | 花 | 14.667 | 70.306 | True | score_valid | score_valid | flower_jump_like_two_hand_confusion |
| web_20260523_030625_c3f72e11 | 跳 | 84.965 | 花 | 14.644 | 70.321 | True | score_valid | score_valid | flower_jump_like_two_hand_confusion |
| web_20260523_015727_2cb1fbe6 | 跳 | 84.948 | 花 | 14.490 | 70.458 | True | score_valid | score_valid | flower_jump_like_two_hand_confusion |
| web_20260523_020555_09843ad1 | 跳 | 84.948 | 花 | 14.490 | 70.458 | True | score_valid | score_valid | flower_jump_like_two_hand_confusion |
| web_20260523_015650_c394e067 | 跳 | 84.923 | 花 | 14.093 | 70.830 | True | score_valid | score_valid | flower_jump_like_two_hand_confusion |
| web_20260602_233348_53e3df5d | 跳 | 88.577 | 花 | 14.821 | 73.756 | True | score_valid | score_valid | flower_jump_like_two_hand_confusion |

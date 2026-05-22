# 全库 DOCX 语义权重判别审计 v2

| 词条 | 门控 | 正例最低 | 负例最高 | margin | 最低正例 | 最高负例 |
|---|---|---:|---:|---:|---|---|
| 唱歌 | False | 58.725 | 13.352 | 45.374 | trim_start_20pct | other_demo_花 |
| 指示 | False | 50.255 | 22.855 | 27.400 | trim_start_20pct | other_demo_汽车 |
| 月亮 | False | 38.963 | 36.878 | 2.085 | trim_start_20pct | other_demo_谗_羡慕 |
| 朋友 | False | 65.334 | 24.093 | 41.241 | subsample_even | other_demo_香蕉 |
| 汽车 | False | 36.120 | 32.110 | 4.010 | trim_end_20pct | other_demo_虎 |
| 花 | True | 75.347 | 39.430 | 35.917 | trim_end_20pct | other_demo_谗_羡慕 |
| 虎 | False | 68.901 | 32.339 | 36.562 | trim_start_20pct | other_demo_汽车 |
| 谗（羡慕） | False | 51.900 | 30.676 | 21.224 | trim_start_20pct | other_demo_花 |
| 跳 | True | 77.655 | 43.731 | 33.924 | subsample_even | fake_static_hold |
| 香蕉 | False | 51.975 | 26.551 | 25.424 | trim_start_20pct | other_demo_朋友 |

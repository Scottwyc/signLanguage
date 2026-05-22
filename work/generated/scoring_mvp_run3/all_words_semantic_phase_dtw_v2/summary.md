# 全库语义相位 DTW 判别审计 v2

| 词条 | 门控 | 正例最低 | 负例最高 | margin | 最低正例 | 最高负例 |
|---|---|---:|---:|---:|---|---|
| 唱歌 | False | 58.672 | 10.296 | 48.376 | trim_start_20pct | other_demo_花 |
| 指示 | False | 49.757 | 13.847 | 35.910 | trim_start_20pct | other_demo_花 |
| 月亮 | False | 32.052 | 23.901 | 8.150 | trim_start_20pct | other_demo_谗_羡慕 |
| 朋友 | False | 58.372 | 17.573 | 40.799 | subsample_even | other_demo_花 |
| 汽车 | False | 39.347 | 15.975 | 23.372 | trim_end_20pct | other_demo_虎 |
| 花 | True | 83.213 | 29.534 | 53.679 | trim_end_20pct | other_demo_谗_羡慕 |
| 虎 | False | 63.005 | 17.611 | 45.394 | subsample_even | other_demo_汽车 |
| 谗（羡慕） | False | 56.750 | 23.188 | 33.562 | trim_start_20pct | other_demo_花 |
| 跳 | True | 79.579 | 39.639 | 39.940 | subsample_even | other_demo_花 |
| 香蕉 | False | 46.612 | 18.503 | 28.108 | trim_start_20pct | other_demo_朋友 |

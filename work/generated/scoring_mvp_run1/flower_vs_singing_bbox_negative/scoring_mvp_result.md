# Holistic 序列打分 MVP 结果

## 口径说明

- 本结果是 prototype sanity check，不是已校准的真实用户评分。
- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。
- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。

## 输入

- 标准序列：`/data/WYC/signLanguage/work/generated/holistic_probe_20260428_full/花/花.json`
- 查询序列：`/data/WYC/signLanguage/work/generated/holistic_probe_20260428_full/唱歌/唱歌.json`
- 特征模式：`bbox`

## 主对齐结果

- prototype_score：`85.837`
- normalized_distance：`0.053453`
- DTW path length：`12`

### 分组平均距离

- left_hand: `0.000000`
- right_hand: `0.045420`
- pose: `0.058299`
- face: `0.019613`
- missing: `0.395833`
- weighted: `0.053453`

### 最差对齐点

- standard frame 28 vs query frame 28: weighted=0.082611, left=0.000000, right=0.166441, pose=0.056584, missing=0.250000
- standard frame 40 vs query frame 40: weighted=0.074526, left=0.000000, right=0.129768, pose=0.069419, missing=0.250000
- standard frame 36 vs query frame 36: weighted=0.072827, left=0.000000, right=0.125525, pose=0.067946, missing=0.250000
- standard frame 44 vs query frame 44: weighted=0.072340, left=0.000000, right=0.123311, pose=0.069328, missing=0.250000
- standard frame 20 vs query frame 20: weighted=0.047082, left=0.000000, right=0.000000, pose=0.064137, missing=0.500000

## 伪用户 sanity check

- self: score=`100.000`, distance=`0.000000`, query_length=`12`
- subsample_even: score=`99.591`, distance=`0.001436`, query_length=`6`
- trim_start_20pct: score=`99.949`, distance=`0.000180`, query_length=`10`
- trim_end_20pct: score=`99.885`, distance=`0.000402`, query_length=`10`
- middle_60pct: score=`99.834`, distance=`0.000582`, query_length=`8`

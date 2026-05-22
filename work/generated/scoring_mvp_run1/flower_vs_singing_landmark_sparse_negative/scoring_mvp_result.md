# Holistic 序列打分 MVP 结果

## 口径说明

- 本结果是 prototype sanity check，不是已校准的真实用户评分。
- 当前项目尚无真实用户视频流样本和人工评分标签，因此不能据此设定合格阈值。
- 脚本只读取已有 Holistic JSON，不重新运行 MediaPipe。

## 输入

- 标准序列：`/data/WYC/signLanguage/work/generated/parallel_sampling_strategies_three_layer_run1/candidate_cache/花/花_holistic_results.json`
- 查询序列：`/data/WYC/signLanguage/work/generated/holistic_worker_benchmark_run1/results/唱歌/唱歌_holistic_results.json`
- 特征模式：`landmark`

## 主对齐结果

- prototype_score：`62.945`
- normalized_distance：`0.162017`
- DTW path length：`28`

### 分组平均距离

- left_hand: `0.000000`
- right_hand: `0.014764`
- pose: `0.511815`
- face: `0.145715`
- missing: `0.428571`
- weighted: `0.162017`

### 最差对齐点

- standard frame 106 vs query frame 4: weighted=0.314181, left=0.000000, right=0.413404, pose=0.624983, missing=0.250000
- standard frame 80 vs query frame 0: weighted=0.210980, left=0.000000, right=0.000000, pose=0.702946, missing=0.500000
- standard frame 76 vs query frame 0: weighted=0.207298, left=0.000000, right=0.000000, pose=0.688101, missing=0.500000
- standard frame 72 vs query frame 0: weighted=0.206771, left=0.000000, right=0.000000, pose=0.687084, missing=0.500000
- standard frame 84 vs query frame 0: weighted=0.205383, left=0.000000, right=0.000000, pose=0.681919, missing=0.500000

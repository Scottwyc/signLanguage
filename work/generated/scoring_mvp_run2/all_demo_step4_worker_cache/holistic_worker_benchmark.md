# Holistic 常驻 worker 实验

本次实验验证：worker 只初始化一次 Holistic，之后连续接收多个视频请求，能否稳定常驻并返回结果。

## 启动信息

- worker PID：3983556
- 模型复杂度：1
- 输入模式：frame_slices
- static_image_mode：True
- worker 初始化耗时：260.119s
- 客户端等待 worker ready 耗时：260.767s
- 密采样步长：每 4 帧取 1 帧
- 目标筛选帧数：12

## 顺序请求结果

### 请求 1
- 视频：`唱歌.mp4`
- 帧索引：0
- 客户端帧切片准备耗时：0.042s
- worker 返回样本数：1
- worker 输入模式：frame_slices
- worker 内部总耗时：0.08s
- worker 输入耗时：0.008s
- 识别耗时：0.066s
- 客户端墙钟耗时：0.083s
- 结果文件：/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache/results/唱歌/唱歌_holistic_results.json
- 最终筛选帧：0
- 最终筛选帧数：1
- 最终帧覆盖比例：None
- 最终尾部覆盖比例：None
- 最终后半段采样占比：None
- 最终后 75% 采样占比：None

### 请求 2
- 视频：`指示.mp4`
- 帧索引：0
- 客户端帧切片准备耗时：0.024s
- worker 返回样本数：1
- worker 输入模式：frame_slices
- worker 内部总耗时：0.074s
- worker 输入耗时：0.007s
- 识别耗时：0.055s
- 客户端墙钟耗时：0.076s
- 结果文件：/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache/results/指示/指示_holistic_results.json
- 最终筛选帧：0
- 最终筛选帧数：1
- 最终帧覆盖比例：None
- 最终尾部覆盖比例：None
- 最终后半段采样占比：None
- 最终后 75% 采样占比：None

### 请求 3
- 视频：`月亮.mp4`
- 帧索引：0
- 客户端帧切片准备耗时：0.019s
- worker 返回样本数：1
- worker 输入模式：frame_slices
- worker 内部总耗时：0.067s
- worker 输入耗时：0.006s
- 识别耗时：0.053s
- 客户端墙钟耗时：0.069s
- 结果文件：/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache/results/月亮/月亮_holistic_results.json
- 最终筛选帧：0
- 最终筛选帧数：1
- 最终帧覆盖比例：None
- 最终尾部覆盖比例：None
- 最终后半段采样占比：None
- 最终后 75% 采样占比：None

### 请求 4
- 视频：`朋友.mp4`
- 帧索引：0
- 客户端帧切片准备耗时：0.013s
- worker 返回样本数：1
- worker 输入模式：frame_slices
- worker 内部总耗时：0.071s
- worker 输入耗时：0.002s
- 识别耗时：0.059s
- 客户端墙钟耗时：0.072s
- 结果文件：/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache/results/朋友/朋友_holistic_results.json
- 最终筛选帧：0
- 最终筛选帧数：1
- 最终帧覆盖比例：None
- 最终尾部覆盖比例：None
- 最终后半段采样占比：None
- 最终后 75% 采样占比：None

### 请求 5
- 视频：`汽车.mp4`
- 帧索引：0
- 客户端帧切片准备耗时：0.017s
- worker 返回样本数：1
- worker 输入模式：frame_slices
- worker 内部总耗时：0.069s
- worker 输入耗时：0.006s
- 识别耗时：0.053s
- 客户端墙钟耗时：0.071s
- 结果文件：/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache/results/汽车/汽车_holistic_results.json
- 最终筛选帧：0
- 最终筛选帧数：1
- 最终帧覆盖比例：None
- 最终尾部覆盖比例：None
- 最终后半段采样占比：None
- 最终后 75% 采样占比：None

### 请求 6
- 视频：`花.mp4`
- 帧索引：0
- 客户端帧切片准备耗时：0.013s
- worker 返回样本数：1
- worker 输入模式：frame_slices
- worker 内部总耗时：0.069s
- worker 输入耗时：0.004s
- 识别耗时：0.059s
- 客户端墙钟耗时：0.07s
- 结果文件：/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache/results/花/花_holistic_results.json
- 最终筛选帧：0
- 最终筛选帧数：1
- 最终帧覆盖比例：None
- 最终尾部覆盖比例：None
- 最终后半段采样占比：None
- 最终后 75% 采样占比：None

### 请求 7
- 视频：`虎.mp4`
- 帧索引：0
- 客户端帧切片准备耗时：0.013s
- worker 返回样本数：1
- worker 输入模式：frame_slices
- worker 内部总耗时：0.073s
- worker 输入耗时：0.006s
- 识别耗时：0.056s
- 客户端墙钟耗时：0.074s
- 结果文件：/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache/results/虎/虎_holistic_results.json
- 最终筛选帧：0
- 最终筛选帧数：1
- 最终帧覆盖比例：None
- 最终尾部覆盖比例：None
- 最终后半段采样占比：None
- 最终后 75% 采样占比：None

### 请求 8
- 视频：`谗（羡慕）.mp4`
- 帧索引：0
- 客户端帧切片准备耗时：0.009s
- worker 返回样本数：1
- worker 输入模式：frame_slices
- worker 内部总耗时：0.075s
- worker 输入耗时：0.003s
- 识别耗时：0.061s
- 客户端墙钟耗时：0.076s
- 结果文件：/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache/results/谗（羡慕）/谗（羡慕）_holistic_results.json
- 最终筛选帧：0
- 最终筛选帧数：1
- 最终帧覆盖比例：None
- 最终尾部覆盖比例：None
- 最终后半段采样占比：None
- 最终后 75% 采样占比：None

### 请求 9
- 视频：`跳.mp4`
- 帧索引：0
- 客户端帧切片准备耗时：0.016s
- worker 返回样本数：1
- worker 输入模式：frame_slices
- worker 内部总耗时：0.071s
- worker 输入耗时：0.008s
- 识别耗时：0.056s
- 客户端墙钟耗时：0.072s
- 结果文件：/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache/results/跳/跳_holistic_results.json
- 最终筛选帧：0
- 最终筛选帧数：1
- 最终帧覆盖比例：None
- 最终尾部覆盖比例：None
- 最终后半段采样占比：None
- 最终后 75% 采样占比：None

### 请求 10
- 视频：`香蕉.mp4`
- 帧索引：0
- 客户端帧切片准备耗时：0.013s
- worker 返回样本数：1
- worker 输入模式：frame_slices
- worker 内部总耗时：0.055s
- worker 输入耗时：0.002s
- 识别耗时：0.047s
- 客户端墙钟耗时：0.056s
- 结果文件：/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache/results/香蕉/香蕉_holistic_results.json
- 最终筛选帧：0
- 最终筛选帧数：1
- 最终帧覆盖比例：None
- 最终尾部覆盖比例：None
- 最终后半段采样占比：None
- 最终后 75% 采样占比：None

## 结论

- worker 只在启动时初始化一次 Holistic，后续多个视频请求可以连续处理。
- 这条路径避免了每个视频请求都重新支付初始化成本。
- 对当前场景，worker 适合做成常驻服务，再由前端按需下发帧块或视频请求。
- 帧切片模式下，后端不再加载视频文件，只做帧切片解码和 Holistic 识别。

- 全流程总耗时：262.319s

# Holistic 常驻 worker 实验

本次实验验证：worker 只初始化一次 Holistic，之后连续接收多个视频请求，能否稳定常驻并返回结果。

## 启动信息

- worker PID：2122585
- 模型复杂度：1
- static_image_mode：True
- worker 初始化耗时：260.106s
- 客户端等待 worker ready 耗时：260.757s

## 顺序请求结果

### 请求 1
- 视频：`花.mp4`
- 帧索引：0, 4
- worker 返回样本数：2
- worker 内部总耗时：0.276s
- 读取耗时：0.053s
- 识别耗时：0.181s
- 客户端墙钟耗时：0.276s
- 结果文件：/data/WYC/signLanguage/work/generated/holistic_worker_benchmark_run1/results/花/花_holistic_results.json

### 请求 2
- 视频：`唱歌.mp4`
- 帧索引：0, 4
- worker 返回样本数：2
- worker 内部总耗时：0.201s
- 读取耗时：0.051s
- 识别耗时：0.102s
- 客户端墙钟耗时：0.202s
- 结果文件：/data/WYC/signLanguage/work/generated/holistic_worker_benchmark_run1/results/唱歌/唱歌_holistic_results.json

### 请求 3
- 视频：`跳.mp4`
- 帧索引：0, 4
- worker 返回样本数：2
- worker 内部总耗时：0.185s
- 读取耗时：0.036s
- 识别耗时：0.103s
- 客户端墙钟耗时：0.186s
- 结果文件：/data/WYC/signLanguage/work/generated/holistic_worker_benchmark_run1/results/跳/跳_holistic_results.json

## 结论

- worker 只在启动时初始化一次 Holistic，后续多个视频请求可以连续处理。
- 这条路径避免了每个视频请求都重新支付初始化成本。
- 对当前场景，worker 适合做成常驻服务，再由前端按需下发帧块或视频请求。

- 全流程总耗时：261.585s

# Holistic 常驻 Worker 实验

本次实验验证一个问题：`Holistic` 只初始化一次后，能不能在后台常驻，连续处理多个视频请求。

## 配置

- 模型复杂度：`1`
- `static_image_mode`：`true`
- 请求帧：`0, 4`
- 顺序请求视频：
  - `花.mp4`
  - `唱歌.mp4`
  - `跳.mp4`

## 启动结果

- worker PID：`2122585`
- worker 初始化耗时：`260.106s`
- 客户端等待 ready 耗时：`260.757s`

## 顺序请求结果

### 请求 1

- 视频：`花.mp4`
- worker 返回样本数：`2`
- 读取耗时：`0.053s`
- 识别耗时：`0.181s`
- worker 内部总耗时：`0.276s`
- 客户端墙钟耗时：`0.276s`

### 请求 2

- 视频：`唱歌.mp4`
- worker 返回样本数：`2`
- 读取耗时：`0.051s`
- 识别耗时：`0.102s`
- worker 内部总耗时：`0.201s`
- 客户端墙钟耗时：`0.202s`

### 请求 3

- 视频：`跳.mp4`
- worker 返回样本数：`2`
- 读取耗时：`0.036s`
- 识别耗时：`0.103s`
- worker 内部总耗时：`0.185s`
- 客户端墙钟耗时：`0.186s`

## 结论

- worker 只在启动时初始化了一次 `Holistic`
- 后续三个视频请求都稳定返回结果，没有重新初始化
- 从体验上看，worker 常驻模式是可行的
- 对当前这种“多个视频依次请求”的场景，这种方式明显优于每次单独起进程
- 后续如果要继续提速，优先方向是：
  - 前端按帧块发请求
  - worker 常驻复用
  - 结果文件和可视化拆开

## 结果文件

- `花.mp4`：`/data/WYC/signLanguage/work/generated/holistic_worker_benchmark_run1/results/花/花_holistic_results.json`
- `唱歌.mp4`：`/data/WYC/signLanguage/work/generated/holistic_worker_benchmark_run1/results/唱歌/唱歌_holistic_results.json`
- `跳.mp4`：`/data/WYC/signLanguage/work/generated/holistic_worker_benchmark_run1/results/跳/跳_holistic_results.json`


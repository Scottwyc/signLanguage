# 帧切片常驻 Worker 实验

## 结论先行

- 同一个常驻 worker 可以通过请求参数在 `video_path` 模式和 `frame_slices` 模式之间切换，不需要重新启动新 worker。
- 帧切片模式下，后台不再打开视频文件，而是直接接收前端传来的帧切片并做 Holistic 识别。
- 对 `花.mp4` 的实测中，密采样候选 28 帧，最终筛出 12 帧，说明“先密采样、后筛选”的流程可以直接落地。

## 实验设置

- 对象视频：`花.mp4`
- 请求模式：`frame_slices`
- 密采样步长：每 4 帧取 1 帧
- 候选帧数：28
- 最终筛选帧数：12
- worker 模型复杂度：1
- worker 仅初始化一次，之后保持常驻

## 时序与耗时

- worker 初始化耗时：`260.104s`
- 客户端等待 worker ready 耗时：`260.685s`
- 客户端帧切片准备耗时：`0.13s`
- worker 输入解码耗时：`0.08s`
- worker Holistic 识别耗时：`1.421s`
- worker 单次请求总耗时：`1.679s`
- 客户端墙钟耗时：`1.698s`
- 全流程总耗时：`263.15s`

## 结果摘要

- 候选帧索引：
  `0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60, 64, 68, 72, 76, 80, 84, 88, 92, 96, 100, 104, 106`
- 最终筛选帧索引：
  `8, 12, 28, 32, 36, 44, 56, 60, 68, 72, 76, 88`
- 最终帧覆盖比例：`0.7547169811320755`
- 最终尾部覆盖比例：`0.8301886792452831`
- 最终后半段采样占比：`0.5`
- 最终后 75% 采样占比：`0.08333333333333333`

## 说明

- `frame_slices` 请求里只传帧切片，不再传视频路径给 worker 做读取。
- worker 返回的 `rows` 已经包含每个候选帧的 Holistic 结果，后续筛选和可视化都可以基于结果文件独立完成。
- 这条方案的核心价值在于：
  - 省掉后端视频加载
  - 保持 worker 常驻，摊薄初始化成本
  - 同一个 worker 兼容视频模式和帧切片模式

## 文件

- 结果 JSON：`/data/WYC/signLanguage/work/generated/holistic_worker_frame_slice_benchmark_run2/holistic_worker_benchmark.json`
- 报告 Markdown：`/data/WYC/signLanguage/work/generated/holistic_worker_frame_slice_benchmark_run2/holistic_worker_benchmark.md`
- 结果文件：`/data/WYC/signLanguage/work/generated/holistic_worker_frame_slice_benchmark_run2/results/花/花_holistic_results.json`


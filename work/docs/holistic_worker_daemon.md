# Holistic 常驻 Worker 说明

这个 worker 的目标很简单：把 `Holistic` 的初始化成本摊到多个请求上，避免每次识别都重新初始化。

## 设计

- worker 进程启动时只初始化一次 `Holistic`
- 之后一直常驻，等待外部发来请求
- 每个请求传入：
  - `video_path`
  - `frame_indices`
  - 可选的 `result_dir`
- worker 直接读取视频帧，完成识别后返回 JSON 结果

另外，worker 也支持前端直接传入“帧切片”：

- 请求里直接给出 `frames` 列表
- 每个元素包含 `frame_idx` 和 `image_b64`
- worker 不再打开视频文件，而是直接解码帧切片并运行 `Holistic`

## 协议

### 启动完成

worker 初始化完成后，会先输出一条 `ready` 消息：

```json
{
  "type": "ready",
  "pid": 12345,
  "holistic_init_sec": 260.106,
  "model_complexity": 1,
  "static_image_mode": true
}
```

### 处理请求

请求示例：

```json
{
  "cmd": "process",
  "request_id": "花_0",
  "video_path": "/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/花.mp4",
  "frame_indices": [0, 4],
  "result_dir": "/data/WYC/signLanguage/work/generated/holistic_worker_benchmark_run1/results/花"
}
```

worker 返回：

- `probe_sec`
- `read_sec`
- `holistic_eval_sec`
- `process_secs`
- `request_total_sec`
- `result_file`
- `rows`

### 帧切片请求

当前端已经拿到帧切片时，可以直接发这类请求：

```json
{
  "cmd": "process_frames",
  "request_id": "花_0",
  "video_stem": "花",
  "fps": 25.0,
  "total_frames": 108,
  "frame_indices": [0, 4],
  "frames": [
    {
      "frame_idx": 0,
      "image_format": "jpg",
      "image_b64": "..."
    },
    {
      "frame_idx": 4,
      "image_format": "jpg",
      "image_b64": "..."
    }
  ],
  "result_dir": "/data/WYC/signLanguage/work/generated/holistic_worker_benchmark_run1/results/花"
}
```

这条路径的特点是：

- 后端不再加载视频文件
- 前端负责准备帧切片并传输
- worker 只做帧切片解码和 Holistic 识别
- 返回字段里的 `read_sec` / `ingest_sec` 表示帧切片解码耗时

### 心跳与退出

- `cmd = ping`：返回 `pong`
- `cmd = shutdown`：优雅退出

## 使用建议

- 默认适合“多个视频依次请求”的场景
- 不建议把每次请求切得过碎，否则 IPC 和视频读取会重复增加开销
- 如果请求之间需要强独立性，建议使用 `static_image_mode = true`
- 后续如果要高频实验，建议把 worker 放到常驻后台里运行，比如 tmux、守护进程或端口服务；需要并行时可以起多个 worker 实例，分别绑定不同端口
- 同一个 worker 不需要因为输入源变化而重启，直接通过请求里的 `video_path` / `frames` 字段切换模式即可
- 如果后续要做更高吞吐，可在 worker 外再包一层队列或 RPC 服务

## 当前实验结论

- `Holistic` 初始化仍然很重
- worker 常驻可以把这部分成本只支付一次
- 后续多个视频请求都能稳定返回结果

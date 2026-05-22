# 手语打分网页前后端设计与当前实现报告

更新时间：2026-05-23 00:20:00 CST  
项目路径：`/data/WYC/signLanguage`  
报告范围：当前 `5080` 单服务运行态、浏览器帧上传格式、历史多前端代理方案、未来后端池扩展方案

## 1. 当前设计结论

前端页面和 Holistic 评分后端应当解耦。页面设计、交互、布局、端口版本可以频繁迭代，但不应该因此反复重启 `MediaPipe Holistic`。当前已经调整为：

- `5080`：当前唯一保留的常驻服务，同时提供新版页面、评分 API 和唯一 `holistic_worker_daemon.py`。
- `5081/5082/5083`：历史对比前端代理，当前 tmux 会话已关闭。
- 当前 `5080` 页面已同步 v4 交互：摄像头开关、默认隐藏参考视频、3 秒倒计时、左侧大视频区和右侧窄结果区。
- 隐藏参考视频时会保留参考开启时的用户视频宽度，只隐藏右侧参考块，避免用户视频过高导致按钮和提示文本被挤出首屏。
- 如后续继续做页面 AB 对比，可再启动独立前端代理端口，并把评分请求转发到 `http://127.0.0.1:5080`。

因此，当前运行态只有一个 tmux 后端和一个 Holistic worker；启动或重启历史前端代理不是必要条件。

## 2. 服务角色

| 端口 | 当前角色 | 是否启动 Holistic worker | 说明 |
| --- | --- | --- | --- |
| `5080` | 当前唯一服务 | 是 | 新版页面 + FastAPI 评分 API，唯一持有常驻 Holistic worker。 |
| `5081` | 历史 v2 前端代理 | 否 | 已关闭；参考视频版，默认隐藏参考。 |
| `5082` | 历史 v3 前端代理 | 否 | 已关闭；v2 基础上增加 3 秒倒计时。 |
| `5083` | 历史 v4 前端代理 | 否 | 已关闭；其页面交互已同步到 `5080` 静态页面。 |

后续页面改版如果只是替换当前主页面，可直接更新 `5080` 静态文件且不重启后端；如果要保留多个可对比版本，再新增前端代理端口。

## 3. 当前数据流

```text
Windows 浏览器
  |
  | getUserMedia 获取本机摄像头
  | canvas 抽帧并压缩为 JPEG base64
  v
共享评分后端 5080
  |
  | process_frames
  v
常驻 holistic_worker_daemon.py
  |
  | raw Holistic JSON
  v
score_holistic_sequence_mvp.py
  |
  | DTW + 分组误差 + sequence penalty
  v
结构化评分结果返回前端
```

关键点：

- 浏览器只把抽样 JPEG 帧发给服务器，不上传完整 MP4/WebM。
- 服务器不直接访问 Windows 摄像头。
- 参考视频只是浏览器单独播放 demo MP4，不参与评分请求。
- 评分后端只关心标准化后的帧 JSON，不关心前端页面版本。

## 4. Windows 本地访问

浏览器摄像头权限需要安全上下文。`http://127.0.0.1` 和 `http://localhost` 可以申请摄像头权限，因此仍推荐 SSH local tunnel。

当前推荐访问 `5080`：

```bash
ssh -N -L 5080:127.0.0.1:5080 wuyangcheng@<远端服务器地址>
```

如果 SSH 有自定义端口：

```bash
ssh -N -L 5080:127.0.0.1:5080 -p <ssh端口> wuyangcheng@<远端服务器地址>
```

然后在 Windows 浏览器打开：

```text
http://127.0.0.1:5080
```

对比版本：

```text
v2: http://127.0.0.1:5081（当前已关闭）
v3: http://127.0.0.1:5082（当前已关闭）
v4: http://127.0.0.1:5083（当前已关闭，交互已同步到 5080）
```

如果只需要直接访问共享评分后端，可打开：

```text
http://127.0.0.1:5080
```

## 5. 前端采集和上传内容

以当前 `5080` 页面为准，交互脚本：

```text
/data/WYC/signLanguage/work/web/static/app.js
```

摄像头权限：

```javascript
navigator.mediaDevices.getUserMedia({
  video: {
    width: { ideal: 960 },
    height: { ideal: 720 },
    facingMode: "user"
  },
  audio: false
})
```

当前只申请视频，不申请音频。用户点击“采集并打分”后，前端先显示 3 秒倒计时，再按设置的 `durationSec`、`captureFps`、`frameWidth` 抽帧。

单帧 payload：

```json
{
  "image_format": "jpg",
  "image_b64": "<JPEG二进制的base64字符串>"
}
```

完整评分请求：

```json
{
  "target_word": "花",
  "fps": 5,
  "duration_sec": 3,
  "frame_indices": [0, 1, 2, 3, 4],
  "frames": [
    {
      "image_format": "jpg",
      "image_b64": "<第0帧JPEG base64>"
    }
  ],
  "wait_for_ready_sec": 600
}
```

不会发送：

- 不发送音频。
- 不发送完整视频文件。
- 不发送浏览器 `MediaStream` 对象。
- 不发送未压缩 RGB/YUV 原始帧。
- 不把参考 demo 视频并入评分请求。

## 6. 当前 5080 新版页面

当前 5080 页面文件：

```text
/data/WYC/signLanguage/work/web/backend.py
/data/WYC/signLanguage/work/web/static/index.html
/data/WYC/signLanguage/work/web/static/styles.css
/data/WYC/signLanguage/work/web/static/app.js
```

当前 5080 直接处理：

```text
GET /
GET /static/*
GET /api/reference-video/{word}
```

当前页面变化：

- 摄像头按钮在“开启摄像头”和“关闭摄像头”之间切换。
- 关闭摄像头时停止浏览器 `MediaStream` tracks，并禁用“采集并打分”。
- “查看参考”默认关闭，用户需要时再加载参考视频。
- 点击评分后显示 `3、2、1、开始` 倒计时。
- 左侧实时视频/采集区加宽，右侧结果面板收窄。
- 参考视频隐藏时，用户视频保持参考开启时的紧凑宽度，便于首屏看到按钮和日志提示。

## 7. 共享评分后端

共享后端文件：

```text
/data/WYC/signLanguage/work/web/backend.py
```

它负责：

- 启动并维护一个 `HolisticWorkerService`。
- 提供 `/api/status`、`/api/templates`、`/api/reference-video/{word}`、`/api/score`。
- 把前端帧请求转为 worker 的 `process_frames` 请求。
- 读取模板库并调用现有评分逻辑。

模板库：

```text
/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache_v2/results/
```

后端给 worker 的内部请求：

```json
{
  "cmd": "process_frames",
  "request_id": "web_20260522_235500_xxxxxxxx",
  "video_stem": "user_花_web_20260522_235500_xxxxxxxx",
  "fps": 5,
  "total_frames": 15,
  "frame_indices": [0, 1, 2],
  "frames": [
    {
      "image_format": "jpg",
      "image_b64": "<JPEG base64>"
    }
  ],
  "result_dir": "/data/WYC/signLanguage/work/generated/web_scoring_mvp/<request_id>/holistic"
}
```

## 8. Worker 与评分

常驻 worker 文件：

```text
/data/WYC/signLanguage/work/scripts/holistic_worker_daemon.py
```

worker 在启动时初始化一次 `MediaPipe Holistic`。收到 `process_frames` 后：

1. base64 解码每帧 JPEG。
2. 用 OpenCV 恢复图像。
3. 调用常驻 Holistic 逐帧提取 pose、hand、face raw landmarks。
4. 写出用户本次 raw Holistic JSON。

评分模块：

```text
/data/WYC/signLanguage/work/scripts/score_holistic_sequence_mvp.py
```

评分阶段读取标准模板 JSON 和用户 JSON，执行：

- raw landmark 特征整理。
- 身体尺度归一化。
- mask 缺失处理。
- DTW 时序对齐。
- 分组平均距离。
- sequence penalty。
- `prototype_score`。

当前分数仍是 demo-only prototype similarity，不是正式用户评分阈值。

## 9. 后端返回内容

前端主要展示：

| 返回字段 | 页面含义 |
| --- | --- |
| `score.prototype_score` | 圆形总分 |
| `score.dtw_distance` | DTW 距离 |
| `score.normalized_distance` | 归一化距离 |
| `worker.holistic_eval_sec` | Holistic 处理耗时 |
| `frame_count` | 上传帧数 |
| `score.group_mean_distance` | 分组平均距离表 |
| `score.sequence_penalty` | 序列惩罚表 |
| `artifacts.result_dir` | 服务端结果目录 |

历史代理前端会额外补充：

```json
{
  "frontend_proxy": {
    "version": "v4_frontend_only_camera_toggle_wide_capture",
    "port": 5083,
    "shared_backend": "http://127.0.0.1:5080"
  }
}
```

## 10. 运维策略

当前建议：

1. 长期保持 `5080` 常驻，不因页面调整重启。
2. 默认直接更新 `5080` 静态页面，不重启 `5080` 后端进程。
3. 需要 AB 对比时再新增 `static_vN/` 和 `backend_vN.py`，选择一个新端口。
4. 新前端只做代理，不创建 `HolisticWorkerService`。
5. 只有评分代码、模板库、worker 协议变化时，才考虑重启 `5080`。

当前 tmux 会话：

```text
signlanguage-web     -> 5080 shared scoring backend + current frontend
```

## 11. 未来后端池设计

当用户并发增加时，可以把现在的单 `5080` 后端扩展为后端池。推荐演进方式：

```text
前端 5081/5082/5083/...
  |
  v
轻量 API gateway / proxy
  |
  +-- scoring backend A: 5080, worker A
  +-- scoring backend B: 5084, worker B
  +-- scoring backend C: 5085, worker C
```

后端池需要补充：

- worker 健康状态：`ready/startup/error/busy`。
- 请求队列或负载均衡：优先发给 ready 且空闲的 worker。
- 结果目录隔离：按 backend id 或 request id 分目录。
- 超时与失败重试：worker 卡死时切换到其他后端。
- 前端无感：前端仍只请求统一 `/api/score`。

这一步应在有真实并发需求后再做。当前阶段保留一个常驻后端更简单，且避免多 worker 同时初始化 Holistic 带来的资源压力。

## 12. 当前验证

已完成的检查：

- `5080` 监听 `127.0.0.1:5080`。
- `5081/5082/5083` 当前不再监听。
- 当前只剩 `signlanguage-web` 一个 tmux 会话。
- 当前只有一个 `holistic_worker_daemon.py` 进程，属于 `5080`。
- `5080/api/status` 返回 worker `ready`，模板数 `10`。

当前 `5080` worker 状态为 ready。本次重启后 Holistic 初始化时间显示约 `390.501s`，因此后续更应避免为了前端页面改版重启共享后端。

## 13. 当前关键文件

共享评分后端：

```text
/data/WYC/signLanguage/work/web/backend.py
```

历史前端代理：

```text
/data/WYC/signLanguage/work/web/backend_v2.py
/data/WYC/signLanguage/work/web/backend_v3.py
/data/WYC/signLanguage/work/web/backend_v4.py
```

前端静态目录：

```text
/data/WYC/signLanguage/work/web/static/
/data/WYC/signLanguage/work/web/static_v2/
/data/WYC/signLanguage/work/web/static_v3/
/data/WYC/signLanguage/work/web/static_v4/
```

运行说明：

```text
/data/WYC/signLanguage/work/docs/web_scoring_mvp.md
/data/WYC/signLanguage/work/docs/web_scoring_mvp_v2.md
/data/WYC/signLanguage/work/docs/web_scoring_mvp_v3.md
```

本报告：

```text
/data/WYC/signLanguage/work/reports/web_frontend_backend_current_implementation_20260522.md
```

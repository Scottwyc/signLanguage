# 手语打分网页 MVP 运行说明

更新时间：2026-05-23 00:20:00 CST

## 目标

该 MVP 提供一个基础网页前端和远端常驻 Holistic 后端：

1. Windows 本地浏览器打开网页。
2. 网页申请本机摄像头权限。
3. 网页采集几秒视频帧，编码为 JPEG base64。
4. 帧数据通过 HTTP POST 发给远端 FastAPI 服务。
5. FastAPI 服务复用一个常驻 `holistic_worker_daemon.py` 子进程生成 raw `Holistic` JSON。
6. 后端调用 `score_holistic_sequence_mvp.py` 的现有评分逻辑，与 demo 模板库做 DTW 对齐和原型相似度评分。

当前输出仍是 `prototype_score`，不是已校准真实用户评分。

当前已收敛为只保留 `5080` 常驻服务。`5080` 同时提供新版页面和评分 API，并保留以下交互：

- “开启摄像头”按钮同时负责关闭摄像头，关闭时会停止浏览器 `MediaStream` tracks。
- “查看参考”默认关闭；需要时可展开一个小的 demo 参考视频窗口。
- 点击“采集并打分”后先在用户摄像头画面显示 3 秒倒计时，再正式采集帧。
- 页面布局加宽左侧实时视频/采集区，并压缩右侧结果区，便于用户对齐动作入画。

## 为什么通过 localhost 访问

浏览器摄像头权限要求安全上下文。`http://127.0.0.1` / `http://localhost` 被浏览器视为可用安全上下文，但普通远端 `http://server-ip:port` 通常不能直接申请摄像头权限。

因此推荐方式是：

```text
Windows 浏览器 http://127.0.0.1:5080
  -> SSH local tunnel
  -> 远端服务器 127.0.0.1:5080 常驻评分后端
  -> FastAPI + 常驻 Holistic worker
```

## 远端启动服务

在远端服务器 `/data/WYC/signLanguage` 下运行：

```bash
cd /data/WYC/signLanguage
/home/wuyangcheng/myenv/bin/python /data/WYC/signLanguage/work/web/backend.py
```

服务默认监听：

```text
127.0.0.1:5080
```

后端启动后会后台初始化 `MediaPipe Holistic`，当前环境通常需要约 `260s`。页面右上角会显示 `Holistic 初始化中` 或 `后端已就绪`。

当前运行态只保留 `5080` 一个 tmux 后端服务；历史 `5081`、`5082`、`5083` 前端代理已关闭，如需重新对比可再启动对应脚本。

## Windows 本地 SSH 隧道

在 Windows PowerShell / CMD 中建立本地端口转发：

```bash
ssh -N -L 5080:127.0.0.1:5080 wuyangcheng@<远端服务器地址>
```

如果 SSH 不是默认 22 端口，加入：

```bash
ssh -N -L 5080:127.0.0.1:5080 -p <ssh端口> wuyangcheng@<远端服务器地址>
```

保持该窗口不关闭，然后在 Windows 浏览器打开：

```text
http://127.0.0.1:5080
```

## 当前模板库

后端默认读取当前已生成的 10 个 demo step-4 raw landmark 模板：

```text
/data/WYC/signLanguage/work/generated/scoring_mvp_run2/all_demo_step4_worker_cache_v2/results/
```

默认目标动作建议先选 `花`，因为当前完整判别性实验已经以 `花` 作为目标动作通过工程 sanity gate。

## API

### `GET /api/status`

返回服务状态、worker 初始化状态和可用模板列表。

### `GET /api/templates`

返回当前模板词表。

### `GET /api/reference-video/{word}`

返回指定 demo 词的参考动作 MP4。前端只有在用户点击“查看参考”后才加载该视频。

### `POST /api/score`

请求体示例：

```json
{
  "target_word": "花",
  "fps": 5,
  "duration_sec": 3,
  "frame_indices": [0, 1, 2],
  "frames": [
    {"image_format": "jpg", "image_b64": "..."}
  ]
}
```

返回字段包括：

- `score.prototype_score`
- `score.dtw_distance`
- `score.normalized_distance`
- `score.group_mean_distance`
- `score.sequence_penalty`
- `artifacts.holistic_json`
- `artifacts.scoring_json`

## 当前限制

- 当前仍无真实用户视频流样本和人工评分标签，网页分数不能作为正式评分。
- 当前只实现单模板匹配，没有多模板标准库。
- 当前没有单独输出 `confidence_score`。
- 当前没有自动生成对齐图和误差曲线。
- 当前摄像头帧由浏览器按固定 FPS 采集，不做动作起止检测。
- 首次启动 Holistic worker 较慢，应保持服务常驻。

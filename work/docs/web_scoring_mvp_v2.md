# 手语打分网页 MVP V2 运行说明

更新时间：2026-05-22 23:10:00 CST

## 变化

V2 保留原有采集、打分和结果展示区域，并增加一个可选参考动作视频窗。由于当前页面用于测评，参考视频默认不显示；用户需要时点击“查看参考”才在采集区右侧展开小参考视频，再次点击可隐藏。参考视频随目标动作下拉框自动切换，来源为当前 demo 视频：

```text
/data/WYC/signLanguage/data/Demo词汇视频/Demo词汇视频/
```

旧版 `5080` 服务保持不动，并作为唯一共享 Holistic 评分后端。V2 使用新端口：

```text
127.0.0.1:5081
```

## 远端服务

V2 后端入口：

```text
/data/WYC/signLanguage/work/web/backend_v2.py
```

`backend_v2.py` 只负责静态前端、参考视频和轻量 API 代理；它不会再启动新的 `MediaPipe Holistic` worker。`/api/status`、`/api/templates`、`/api/score` 会转发到共享后端：

```text
http://127.0.0.1:5080
```

V2 前端目录：

```text
/data/WYC/signLanguage/work/web/static_v2/
```

## Windows 访问

在 Windows PowerShell / CMD 中建立隧道：

```bash
ssh -N -L 5081:127.0.0.1:5081 wuyangcheng@<远端服务器地址>
```

如果 SSH 有自定义端口：

```bash
ssh -N -L 5081:127.0.0.1:5081 -p <ssh端口> wuyangcheng@<远端服务器地址>
```

然后打开：

```text
http://127.0.0.1:5081
```

对比旧版：

```text
http://127.0.0.1:5080
```

## 口径

V2 只调整前端展示和参考视频 API，评分机制仍复用当前 `score_holistic_sequence_mvp.py` 的 demo-only prototype similarity。当前输出仍不是正式用户评分阈值。

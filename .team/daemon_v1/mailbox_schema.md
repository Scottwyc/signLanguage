# daemon v1 mailbox schema

消息中心只面向 daemon session API，不兼容、不生成废弃的 `{team: ...}` 包协议，也不修改旧 TUI 消息脚本或旧日志。

## 输入

- `--to-role ROLE`：从 `.team/daemon_migration_4194_manifest.json` 的 `roles`/`copied` 解析 `session_id`。
- `--to-session SESSION_ID`：直接指定 daemon session ID；与 `--to-role` 互斥。
- `--prompt TEXT`：投递文本。
- daemon 地址读取 manifest 的 `daemon_url`，且强制为 `http://127.0.0.1`。

请求为：

```http
POST /session/:id/prompt
Content-Type: application/json

{"prompt":"..."}
```

## JSONL 记录

文件：`.team/daemon_v1/mailbox.jsonl`。每次投递追加记录，不覆盖历史；同一 `message_id` 对应 queued 以及最终 sent/failed。

必需字段：

- `message_id`：UUID 字符串
- `recorded_at`：UTC ISO-8601 时间
- `state`：`queued`、`sent` 或 `failed`
- `to_session`：目标 daemon session ID
- `to_role`：角色投递时为角色名，直接 session 投递时为 `null`
- `prompt`：原始投递文本

最终状态字段：

- `response`：daemon JSON 响应（sent 时保留）
- `stop_reason`：从响应 `stopReason` 提取，可为 `null`
- `response_time`：从响应 `time` 或 `timestamp` 提取，可为 `null`
- `error`：失败原因（failed 时保留）

状态流转：`queued -> sent` 或 `queued -> failed`。脚本发生网络、HTTP 或响应 schema 错误时均追加 `failed` 记录，并返回清晰非零错误码。

## 离线检查

```bash
python3 work/scripts/daemon_team_mailbox_v1.py --offline-schema-check
```

该模式只读取 mailbox JSONL，不访问 daemon；首次文件不存在视为空 mailbox 并返回成功。

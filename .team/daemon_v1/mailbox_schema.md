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

## 消息级生命周期（members/<role>/messages.jsonl）

由 `daemon_team_member_helper_v1.py` 在监听成员 session SSE 时，按 `promptId` 把事件聚合为
**消息级状态机**，补上「投递成功之后 LLM 是否读取/处理/完成」的反馈；事件级
`inbox.jsonl`/`events.jsonl`/`helper_health.json` 保持不变（向后兼容）。

状态机：

```text
queued → delivered（SSE user_message_chunk，LLM 已收到/回显）
       → processing（SSE agent_thought_chunk / agent_message_chunk，LLM 读取处理中）
       → completed（SSE turn_complete，LLM 已响应）
       / blocked（SSE permission_request，等人工）
       / failed（SSE error / session_died）
```

- `promptId` 位于事件顶层（`turn_complete` 的 `data` 里也有一份），现不再被脱敏——
  它是不透明关联 ID 而非 prompt 内容；prompt 正文仍按原有规则脱敏。
- 无 `promptId` 的事件（如多数 `session_died`）不进入消息状态机，只保留事件级记录。

记录文件：`.team/daemon_v1/members/<role>/messages.jsonl`（追加式，同一条 `promptId`
后续事件更新记录，追加一行完整记录；读取端按 `promptId` 去重保留最后一行 = 最新状态）。

记录字段：

- `promptId`：SSE 事件关联 ID
- `state`：`delivered` / `processing` / `blocked` / `completed` / `failed`
- `state_at`：最近一次状态变化时间（UTC ISO-8601）
- `transitions`：状态变化历史 `[{state, at}, ...]`
- `text_preview`：脱敏+截断的消息文本摘要（≤240 字符）
- `session_id`、`role`：helper 所在成员上下文
- `error`：`failed` 时保留失败原因（如 `data.reason`）

聚合：`daemon_team_message_supervisor_v1.py` 读取各成员 `messages.jsonl`，输出
`message_supervisor.json`：成员级新增 `msg_state_counts`（五态计数）与 `recent_messages`
（按 `state_at` 倒序最多 5 条），顶层新增 `messages`（全成员最近消息倒序最多 20 条）。

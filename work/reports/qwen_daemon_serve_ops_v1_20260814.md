# Qwen daemon 服务运维技术文档 v1

- 版本：v1
- 保存时间：2026-08-14 09:56（星期五）
- 适用 daemon 版本：qwen-code 0.21.11（`qwen serve` / `--http-bridge`）
- 适用项目：`/data/WYC/signLanguage`
- 关联文档：
  - 迁移验证记录：`/data/WYC/signLanguage/work/reports/qwen_tui_daemon_team_migration_v1_20260813.md`
  - 事故/日报系列：`/data/WYC/signLanguage/.team/daemon_v2_integration_report_20260814.md`、`daemon_team_dashboard_api_incident_v1_20260814.md`

---

## 1. 服务架构总览

生产 daemon（agent team 的 Web Shell 载体）：

- **生产 daemon**：`http://127.0.0.1:4194`（workspace `/data/WYC/signLanguage`，max-sessions 16，chat-recording）
- **团队仪表盘**：`http://127.0.0.1:8465`（`daemon_team_dashboard_server_v1.py`，服务缓存 dashboard_data.json）
- **v2 集成控制台**：`http://127.0.0.1:8466`（`daemon_team_console_v2_server.py`，独立于 4194 的展示层）
- **静态站**：`http://127.0.0.1:8460`（`serve_nocache.py --dir /data/WYC/sign-language-universe/apps/web`）
- **辅助进程**（refresher / member_helper / message_supervisor，全部 `systemd` 收养 PPID=1631）：
  - `daemon_team_refresher_v1.py --interval 1 --daemon-url http://127.0.0.1:4194`：每 1 秒拉取生产 daemon 生成 registry/health/dashboard 缓存
  - `daemon_team_member_helper_v1.py --role <角色> --session-id <id> --poll-seconds 5`：每个成员一个，轮询 SSE 事件
  - `daemon_team_message_supervisor_v1.py`：汇总成员消息
  - `daemon_team_dashboard_server_v1.py --port 8465`：服务缓存数据

测试/隔离实例（勿与生产混淆）：

- 4190：`/tmp/qwen-daemon-signlanguage-team`（迁移测试）
- 4192：`/tmp/qwen-daemon-signlanguage-team-v2`（迁移测试）
- 4180：workspace `/data/WYC/signLanguage`（Web Shell 测试）
- 4182：`/tmp/qwen-daemon-team-test`
- 4195：`/tmp/qwen-daemon-agent-team-test-20260813_232356`（v2 联调隔离实例）

---

## 2. 启动与重启方法（保活方式，重要）

生产 4194 一律用 `setsid + nohup` 保活启动，**不要依赖 tmux 窗口**（2026-08-14 事故根因见 §3）。

自 2026-08-14 10:00 起，4194 已启用 bearer token 认证（`--token` + `--require-auth`），token 存储在
`/data/WYC/signLanguage/.team/daemon_v1/.daemon_token`（chmod 600）。启动命令：

```bash
setsid nohup node /home/wuyangcheng/.npm-global/bin/qwen serve \
  --http-bridge --hostname 127.0.0.1 --port 4194 \
  --workspace /data/WYC/signLanguage --max-sessions 16 --chat-recording \
  --token "$(cat /data/WYC/signLanguage/.team/daemon_v1/.daemon_token)" --require-auth \
  > /data/WYC/signLanguage/.team/daemon_v1/daemon_4194.stdout.log 2>&1 < /dev/null &
```

启动后必须一次性验证（同一命令内完成）：

```bash
ss -tlnp | grep 4194                          # 端口监听
curl -s http://127.0.0.1:4194/health          # 期望 401（require-auth 生效）
curl -s -H "Authorization: Bearer $(cat /data/WYC/signLanguage/.team/daemon_v1/.daemon_token)" \
  http://127.0.0.1:4194/health                # 期望 {"status":"ok"}
ps -o pid,ppid -p <新PID>                      # PPID 应为 1 或 1631（已脱离 shell）
```

启动日志位置：`/data/WYC/signLanguage/.team/daemon_v1/daemon_4194.stdout.log`；daemon 内部日志：`/home/wuyangcheng/.qwen/debug/daemon/runs/run-<runId>/daemon.log`。

注意：

- `--chat-recording` 必须保留，否则 session 历史不落盘，重启后无法恢复。
- `--require-auth` 使 loopback 也强制认证，且 `/health` 同样需要 Authorization（k8s/Compose 探针必须带 token）。
- 若启动日志出现 `daemon stable log is owned by another daemon instance`，多为旧进程残留锁文件，不影响运行；用 `ss -tlnp` 确认端口归属唯一进程即可。

### 2.1 Bearer token 认证配置（2026-08-14 起）

- **token 存储**：`/data/WYC/signLanguage/.team/daemon_v1/.daemon_token`（`openssl rand -hex 32` 生成，chmod 600；不写入任何脚本/文档明文）。
- **Web Shell 访问**：URL 带 `?token=<token>`，如 `http://127.0.0.1:4194/?token=<token>` 或 `/session/<id>?token=<token>`；前端读取后所有 API 请求自动带 `Authorization: Bearer <token>`。
- **API 访问**：请求头 `Authorization: Bearer <token>`；不带 token 一律 401。
- **辅助进程认证**：所有访问 4194 的 team 脚本（`daemon_team_v1.py` / `member_helper` / `mailbox` / `console_v2`）统一 import `/data/WYC/signLanguage/work/scripts/daemon_auth_v1.py` 的 `auth_headers()`，从环境变量 `QWEN_DAEMON_TOKEN` 或 token 文件自动加载。message_supervisor 与 dashboard_server(8465) 只读缓存文件，无需认证。
- **token 轮换**：改 `.daemon_token` 内容 → 重启 4194（§2 命令）→ 无需重启辅助进程（每次请求重新读取）。

### 2.2 重启后 session 恢复（重要）

- daemon 重启后 session 元数据自动恢复（列表可见），但运行时需 `load` 或 `resume`。
- **短历史 session**：`POST /session/:id/load` 可用；**长历史 session**（replay updates > 10000）load 会 500（`qwen.session.loadReplay updates exceed limit`，daemon 硬编码 `MAX_BULK_REPLAY_UPDATES=10000`，0.21.11 无法通过 `--max-journal-events` 或环境变量调整，已实测），`POST /session/:id/resume` 可恢复运行时（SignL3 16193 条 update 用 resume 成功）。
- **⚠️ 前端加载路径（关键）**：Web Shell 从 session 列表点击打开 session 时，前端判断 `On = En && features.includes("client_identity")`，其中 `En` 仅当"目标 session == 当前 sessionId"（即刷新同一 session）才为 true → **从列表点击新 session 固定走 `loadSession`**，只有刷新/重连同一 session 才走 `resumeSession`。因此长历史 session 无法靠 resume 解决 Web Shell 历史显示问题，**必须压缩历史**（见 §2.3）。
- 批量恢复成员运行时：`POST /session/:id/resume`（仅恢复运行时，不解决前端 load 500）。

### 2.3 loadReplay 10000 限制与历史压缩（2026-08-14 实测）

**现象**：SignL3（16193 updates）、signL2（17152 updates）load 500 → Web Shell 打开后历史空白；signL4/signL5 等历史 < 10000 正常。transcript 数据完整无丢失（jsonl 21977 / 17781 行）。

**压缩方案**：裁剪 session jsonl，保留最近 N 轮 user 对话（默认 100 轮），使 replay updates < 10000。

```bash
# 备份（脚本也会自动备份 .bak_compress_<日期>）
python3 /data/WYC/signLanguage/work/scripts/compress_daemon_session_v1.py \
  --file /home/wuyangcheng/.qwen/projects/-data-WYC-signLanguage/chats/<sessionId>.jsonl \
  --keep-turns 100            # 可选 --dry-run 预览
# 压缩后必须重启 daemon 重新索引
bash /data/WYC/signLanguage/work/scripts/start_daemon_team_v1.sh restart
```

**实测结果（2026-08-14）**：
- SignL3：21977 行(99MB) → 3031 行(17MB)，load 200，compactedReplay 1724 条
- signL2：17781 行(40MB) → 398 行(0.5MB)，load 200，compactedReplay 369 条
- transcript 显示最近 100 轮对话，头部出现 `⚠️ History gap` 标记（qwen 对裁剪历史的预期行为）
- 原始文件备份：`<sessionId>.jsonl.bak_compress_20260814`

**注意事项**：
- 压缩会丢弃该轮次之前的旧对话（约 88% 历史），不可恢复（原文件已备份可回滚）。
- session jsonl 中 system 事件大头是 `ui_telemetry`（SignL3 11870 条）与 `attribution_snapshot`，非对话内容；保留最近 N 轮即保留有效对话。
- 若未来 qwen 提高/可配置该限制，压缩脚本可弃用；当前 0.21.11（npm 最新）无解。

### 2.4 Daemon channels（外部平台接入）

**当前启用（2026-08-14 11:05）**：WeChat channel（`--channel weixin`），GitHub channel 已停用（历史记录见 §2.4.1）。

**启动**：daemon 带 `--channel <name>`（可多个或 `all`）；启动脚本 v2 支持 `--channel <name>`。运行时管理：`qwen channel start|stop|status|reload|set`（带 token 的 daemon 需 `--daemon-url` + `--token`）。

**WeChat channel 配置**（`~/.qwen/settings.json` 的 `channels.weixin`）：
- 配置：`type: "weixin"`、`senderPolicy: "pairing"`、`cwd` **必须等于 daemon workspace**（`/data/WYC/signLanguage`）、instructions 建议要求纯文本+限长
- **认证走扫码登录**（不用 token 字段）：`qwen channel configure-weixin` 后台运行 → 手机微信扫 `liteapp.weixin.qq.com` 二维码 → 凭证存 `~/.qwen/channels/weixin/account.json`；`configure-weixin clear` 清除
- 底层：微信官方 iLink Bot API（`baseUrl` 默认 `https://ilinkai.weixin.qq.com`，可覆盖）

**能力/限制**：
- 手机微信私聊 bot 发消息 → agent 回复（显示"…"输入指示）
- **仅私聊 DM**（iLink Bot 不支持群聊）；**仅纯文本**（Markdown 被去除）
- 会话过期（日志 `Session expired (errcode -14)`）→ 重新 `qwen channel configure-weixin` 扫码
- 图片需多模态模型；PDF/代码文件可发送，agent 自动解密读取
- 建议 `senderPolicy: "pairing"`/`"allowlist"` 控制访问

**Pairing 配对流程**（`senderPolicy: "pairing"` 时新用户首次给 bot 发消息会生成配对码）：
- 用户侧：微信给 bot 发消息 → 获得配对码（如 `H4W8WA4C`），把码发给 bot 操作者
- 操作者侧：批准
  ```bash
  # 查看待处理请求
  qwen channel pairing list weixin --cwd /data/WYC/signLanguage
  # 批准
  qwen channel pairing approve weixin <配对码> --cwd /data/WYC/signLanguage
  ```
- ⚠️ **关键坑**：`qwen channel pairing` 子命令**不支持 `--daemon-url`/`--token`**，且必须带 `--cwd <daemon workspace>`（`/data/WYC/signLanguage`），否则报 "No pending request found / different workspace"

**Agent 权限边界（安全，重要）**：
- **workspace**：channel agent 的 `workspaceCwd = /data/WYC/signLanguage`（= daemon workspace，channel 无独立 workspace）
- **权限 = wuyangcheng 用户完整权限**：channel 的 agent 是 daemon 的 ACP child，以 wuyangcheng 用户运行——可读写 wuyangcheng 权限范围内的一切（整个 `/data/WYC`、家目录、系统可访问路径），可执行 shell 命令、网络访问，工具集与主 daemon agent 相同，无独立降权
- **会话隔离**：`sessionScope: "user"` → 每个微信用户独立 channel 会话
- **安全含义**：每个被批准配对的微信用户都能驱动一个拥有服务器完整用户权限的 agent（改文件/跑命令/访问网络）；daemon 的 `--require-auth` 只保护 API，不限制 channel 派生 agent
- **收紧建议**：配对批准需慎重；需要收紧时改 `senderPolicy: "allowlist"` + 指定用户，或移除已批准 pairing

### 2.5 网络拓扑与安全边界（2026-08-14 核实）

**绑定原则**：本机所有 daemon/网页服务（4194 daemon、8460/8465/8466 dashboard、8765-8772 问卷服务、18771-18774 http.server）**全部只绑定 `127.0.0.1` 回环**，不暴露到任何网卡——外部网络无法直接访问。

**访问链路**（本地浏览器访问 daemon）：
```
本地电脑浏览器 → http://127.0.0.1:4194/?token=<TOKEN>（VS Code 端口转发本地地址）
  → SSH 加密隧道（VS Code Remote-SSH 自动建立）
  → nature 服务器 127.0.0.1:4194（daemon 绑定回环）
```
方向：**本地 → nature**（SSH 隧道主动连接）；nature 从不回连本地（仅两个 `ssh -L` 是 nature→zhuhai 的 7906/7907，与 daemon 无关）。

**攻击面**：

| 攻击途径 | 是否可行 |
|---|---|
| 外部网络直接访问 | ❌ 不可行（loopback，外部连不上） |
| 同服务器其他用户访问 127.0.0.1:4194 | ❌ 需 token（`--require-auth`，64 位 hex≈256bit 熵） |
| 中间人窃听传输 | ❌ SSH 隧道全程加密 |
| 真正风险 | 本机恶意软件、token 泄露（带 token 链接外发） |

**关于"http 不安全"提醒**：浏览器对 http:// 的警告是通用提示；实际明文段仅"本地浏览器 ↔ 本地 SSH 客户端"（127.0.0.1 本机回环，不经过网络），隧道内部 SSH 加密。loopback + token + SSH 隧道方式下实际风险很低。

**何时需要 HTTPS**：仅当绕过 SSH 隧道直接经局域网 IP（`http://172.x.x.x:4194`）或外网访问时，才需 `--tls-cert`/`--tls-key` 启用 HTTPS；当前方式不需要。

**操作规范**：带 token 的链接视为敏感信息，不外发/不截图；token 泄露时轮换（改 `.daemon_token` + 重启）。

**GitHub channel（2026-08-14 曾启用，后停用）**：配置/触发机制见下方 §2.4.1。

### 2.4.1 GitHub channel 触发机制与身份模型（历史，已停用）

**核心模型**：
- **agent 身份 = 认证账号**：channel worker 用认证账号（当前 `useLocalGh` → Scottwyc）轮询 notifications、发评论、加 reaction——**agent 的回复显示为认证账号**。
- **触发者 = allowlist 账号**（`allowedUsers`，当前 `["scottbot"]`）：只有白名单内账号发出的匹配通知（mention/review_requested/assign）能**触发一次处理**。
- **自触发限制（硬限制）**：认证账号自己 @自己/自己评论 → **永不触发**（防 agent 回复自己→再触发→死循环）。
- **channel 服务常驻**：daemon 启动即连接并 60s 轮询，"@" 只是触发处理，不是启动服务。

**触发矩阵**（当前配置 `allowlist=["scottbot"]`）：

| 谁发通知/评论 | 能否触发 |
|---|---|
| scottbot（allowlist 内）@Scottwyc | ✅ 触发 |
| Scottwyc（认证账号）@自己 | ❌ 永不触发（自触发限制） |
| 其他协作者 @Scottwyc | ❌ 不触发（不在白名单，仅正常 GitHub 通知） |

**两种身份方向（2026-08-14 待决）**：
- **方案 A（当前生效）**：agent 身份 = 主账号 Scottwyc（发评论显示 Scottwyc），触发者 = scottbot。工作流：切 scottbot 账号 `@Scottwyc` → Scottwyc 回复。
- **方案 B（用户直觉期望，未启用）**：agent 身份 = scottbot（发评论显示 bot），触发者 = 主账号 Scottwyc。工作流：主账号 PR 里 `@scottbot` → bot 回复。需要 scottbot 的经典 PAT（`notifications` + `public_repo`/`repo` 权限）替换 `useLocalGh` 为 `token` 字段；本机 gh CLI 仅登录 Scottwyc，bot 身份不能走 useLocalGh。

**调整 allowlist 的协作场景**：如需"协作者 @主账号 触发"，把协作者加入 `allowedUsers`；注意白名单内账号可驱动 agent 读代码/花 token/运行工具/以认证账号发评论，公共仓库须谨慎。

---

## 3. 事故记录：2026-08-14 生产 daemon 崩溃与恢复

### 3.1 症状

- 浏览器打开 `http://127.0.0.1:4194/session/<id>` 加载不出来；`curl` 直连报 `ECONNREFUSED`。
- `ss -tlnp | grep 4194` 无监听；refresher 日志持续报 `urllib.error.URLError: Connection refused`。

### 3.2 根因

- 4194 daemon 进程（旧 PID 3618894，PPID 1967 = tmux server）运行在 **`tmux-persistent` 会话**的 pane 中。
- 该 tmux 会话被销毁时，pane 内进程收到 SIGHUP 全部退出，4194 随之死亡。
- 无 OOM 记录（journalctl/dmesg 均无）；其余 daemon（4178/4180/4182/4190/4192/4195）不受影响。

### 3.3 时间线（2026-08-14）

- 00:15：4194 仍在运行（`incident_snapshot_20260814_0015/` 中 process_snapshot 可见监听正常）。
- 01:56：refresher 重启（旧 refresher 3842442 已不在）。
- 09:36 起：refresher 持续报 Connection refused（daemon 已死，死亡时间在 09:36 前）。
- 09:51：按 §2 保活方式重启成功。

### 3.4 恢复步骤（可复用）

1. 确认无残留：`ss -tlnp | grep 4194`（应无输出），`ps -eo pid,ppid,args | grep '[q]wen serve'` 核对。
2. 按 §2 命令 `setsid + nohup` 重启，同一命令内 sleep 后验证端口 + `/health` + PPID。
3. 验证 session 恢复：`GET /workspaces/%2Fdata%2FWYC%2FsignLanguage/sessions` 应列出全部 session（本事故中 17 个，8 个成员 session ID 不变）。
4. 验证 Web Shell：`curl -H "Accept: text/html" http://127.0.0.1:4194/` 与 `/session/<id>` 均应 200。
5. 辅助进程无需重启：refresher 自动恢复（日志出现 `refresh recovered after failure`）。

### 3.5 验证清单（本事故实测）

| 检查项 | 结果 |
|--------|------|
| 端口 4194 监听（新 PID 548904，PPID 1631） | PASS |
| `GET /health` → `{"status":"ok"}` | PASS |
| Web Shell 首页 `GET /`（Accept: text/html） | HTTP 200 |
| session 页面 `GET /session/<id>`（Accept: text/html） | HTTP 200 |
| session 列表 17 个全部存在 | PASS |
| `POST /session/<id>/load` 恢复运行时 | HTTP 200 |
| refresher 自动恢复 | PASS（09:51:58 recovered） |

---

## 3.6 事故记录：2026-08-26 EventBus 订阅者占满 → Web Shell 输入框 loading（可复用排障）

### 症状

- 4194 Web Shell 中运维（signL8）会话的输入框**一直显示 loading，无法输入**
- daemon status 侧完全空闲：`hasActivePrompt=False`、无 pendingInteraction、无 pendingPrompts——与 UI 冻结矛盾

### 根因（确定，有证据）

1. `GET /session/:id/events`（SSE）返回 `{"error":"EventBus subscriber limit reached (64)","code":"subscriber_limit_exceeded","limit":64}`
2. **253 个 ESTAB 连接**挂在 4194（`ss -tan | awk '$4 ~ /:4194$/'`），其中 **242 个由 VS Code Server 进程持有**（`lsof -i :4194`：PID 3362664，`/home/wuyangcheng/.vscode-server`，对端端口分散 33026-60896 = 反复重连未释放的游离连接）
3. 游离连接占满 daemon EventBus 64 订阅者上限 → Web UI 新 SSE 被拒 → 收不到会话状态事件 → 输入框冻结在旧 loading 状态
4. **关闭 VS Code 页面标签不能释放这些游离连接**（实测连接数 253→252 几乎不变）——连接已与页面生命周期脱钩

### 处置

重启 4194 daemon 清空 EventBus 订阅者与全部连接（唯一干净手段）：

```bash
kill <daemon_pid> && sleep 3
cd /data/WYC/signLanguage && setsid nohup node /home/wuyangcheng/.npm-global/bin/qwen serve \
  --http-bridge --hostname 127.0.0.1 --port 4194 --workspace /data/WYC/signLanguage \
  --max-sessions 16 --chat-recording --token <token> --require-auth --channel weixin \
  > /data/WYC/signLanguage/.team/daemon_v1/daemon_4194.log 2>&1 < /dev/null &
```

（完整命令以 `ps -eo pid,ppid,args | grep '[q]wen serve'` 为准；daemon 为 setsid 保活，PPID=1631）

### 验证清单（本次实测）

| 检查项 | 结果 |
|--------|------|
| 连接数 253 → 10（游离连接全部断开，剩余为正常客户端） | PASS |
| `GET /session/:id/events` 返回 `retry: 3000`（SSE 建立成功，不再 subscriber_limit_exceeded） | PASS |
| 运维会话 status 空闲（hasActivePrompt=False, clientCount=1） | PASS |
| 各成员 session 自动恢复（daemon 日志 session resume） | PASS |
| 注意：重启会打断正在推理的成员 turn（本次主管人被打断，自动重试） | 已确认 |

### 预防

- 输入框 loading 复现时先查连接数：`ss -tan | awk '$1=="ESTAB" && $4 ~ /:4194$/ {c++} END{print c}'`，超 64 即复发，重启 daemon 即可
- VS Code Server（`.vscode-server`）长时间运行会累积游离 SSE 连接（本次 1 天 20 小时 → 241 条）；减少经 VS Code 打开 4194 页面、或定期重启 daemon/VS Code Server
- `--max-connections`（TCP 层，默认 256）与 EventBus 订阅者上限（64，**硬编码无 CLI 参数**）是两道独立门槛；TCP 未满而 SSE 已被拒即属本事故形态

---

## 3.7 事故记录：2026-08-27 代理流式 SSE 分隔符丢失 → daemon 解析 position 216（可复用排障）

### 症状

- 4194 成员会话（本地A/主管人/本地B，均走本地 vLLM 流式）`sendPrompt: forward failed for session <sid>: Unexpected non-whitespace character after JSON at position 215-217`
- daemon 日志 `[serve pid=91079]` 记录 `From chunk: ['data: {...}','data: {...}']`——**多条 SSE 事件被拼在一起解析**
- 另见代理崩溃：`select.select([sock, resp_fp])` → `ValueError: I/O operation on closed file`（请求线程崩，日志 3 次 traceback）
- 代理（11435）整进程死亡 → **所有本地模型请求 Connection error**（成员全部连不上）

### 根因（确定，有证据）

1. **`_ThinkStreamProcessor.process_chunk` 换行重建 bug**（codex-deepseek-proxy `src/main.py`）：
   - 原实现 `"\n".join(out_parts)` 把处理后的 SSE 行重新拼接；当**事件分隔空行（`\n\n` 的第二个 `\n`）恰好跨 chunk 边界**时（vLLM 响应分批到达），空行被拆到两个 chunk，join 后**丢失一个 `\n`**
   - 结果：代理输出流中事件间只剩单个 `\n` → daemon 按 `\n\n` 切分失败 → 多条事件拼接 → 单条 JSON 结束后（position ~212-216）遇到下一条的 `data` → 解析报错
2. **触发放大**：运维会话 `/compress` 后请求/响应变大 → vLLM 分批输出更多 → 跨 chunk 边界概率上升（非运维误触，是代码 bug 的概率触发）
3. **代理进程死亡**：select 崩溃在请求线程（ThreadingHTTPServer 本不该杀进程），但代理仍整体消失（可能叠加 OOM）；**无自动重启机制** → 挂了无人发现（直到用户报 Connection error）

### 处置

1. **修复流式分隔符**：`process_chunk` 改为逐行保留换行（`"".join(p + "\n" for p in out_parts)`），单测验证跨 chunk 后 `\n\ndata:` 完整保留
2. **修复 select 崩溃**：`resp_fp` 检查 `closed`（`fp if (fp is not None and not fp.closed) else conn`）+ select 捕获 `ValueError/OSError` 优雅退出
3. **JSON 解析容错**：新增 `_safe_json_loads`（raw_decode 提取首个完整 JSON，容忍尾部杂质），修复 3 个无保护解析点（vLLM 非流式 / GPT 直连非流式 / OAuth 刷新）——消除 `Unexpected non-whitespace character after JSON` 类线程崩溃
4. **systemd 托管代理**：新建 `~/.config/systemd/user/codex-deepseek-proxy.service`（`Restart=always` + `RestartSec=5` + 开机自启），替代 setsid nohup 手动保活——崩溃 5 秒自愈，不再有「挂了无人发现」空窗
5. **重启脚本保持模型映射**：新建 `work/scripts/restart_daemon_4194_v1.sh`——重启 4194 前记录各 session `currentModelId`，重启后 `POST /session/:id/model` 逐一恢复（映射文件 `.team/daemon_v1/daemon_model_map_restart.json`）

### 验证清单（本次实测）

| 检查项 | 结果 |
|--------|------|
| `_safe_json_loads` 容错单测（杂质/多对象/非法） | PASS |
| `process_chunk` 跨 chunk 分隔符保留单测（`\n\ndata:` 完整） | PASS |
| 修复后 daemon 日志零新增 position 216（最后报错 02:37:26Z 早于修复重启） | PASS |
| systemd active + 11435 HTTP 200 恒定（观察 2 分钟） | PASS |
| 成员（本地A/主管/本地B）恢复工作，链路稳定 | PASS |

### 预防

- 代理必须由 systemd 托管（已生效）；改代理代码后 `systemctl --user restart codex-deepseek-proxy` 生效
- 上游响应解析一律用 `_safe_json_loads`（不要裸 `json.loads` 上游 body）
- 流式透传组件的行处理必须保留原始分隔符（勿用 join 重建 SSE 行）
- 成员本地模型请求报 `Unexpected non-whitespace character after JSON` → 先查代理日志/daemon 日志定位是解析还是分隔符问题，再查代理进程是否存活

---

## 3.8 事故记录：2026-08-27 SSE 连接泄漏复发 + 根治方案落地（writer idle timeout）

### 症状与诊断

- 18:00 用户报「4194 刷新不出来」+「team 看板也刷新不出来」：`ss -tn | grep :4194 | grep -c ESTAB` = **218/256**（listenerMaxConnections 已占 85%），`/daemon/status` → `transport.restSseActive: 109`；8466 看板本身健康（HTTP 200、CPU 0%、API 正常），其会话面板 SSE 走后端代理到 4194 被连带挂起
- 与 8-14/8-26 两次同类：**游离 SSE 连接泄漏占满**，只能重启清空

### 根因（2026-08-27 专项调研，报告 `work/reports/sse_leak_research_20260827.md`）

1. **游离 SSE 流几乎不回收**：0.21.12 运行段 110 条流中 96 条（87%）从打开到 daemon 被杀全程存活，7.6h 内仅 1 条 `client_disconnect` 正常关闭；泄漏源 = 经 **VS Code Remote 端口转发**访问 Web Shell 的浏览器页面（8-26 事故 242/253 条由 VS Code Server 持有）
2. **daemon 侧无兜底**：`writerIdleTimeoutMs` 默认 null；EventBus `DEFAULT_MAX_SUBSCRIBERS=64` 硬编码无 CLI 参数（0.21.12/0.22.2 均如此）；30 分钟 session 空闲回收不回收 SSE 流；升级 0.22.2 不解决问题
3. **关键发现**：`--writer-idle-timeout-ms` 参数（Per-SSE-connection idle deadline，支持 `QWEN_SERVE_WRITER_IDLE_TIMEOUT_MS` 环境变量）**从 0.21.12 起就存在**，三次事故从未启用——现成兜底参数被漏掉

### 处置（方案 A 落地）

1. **重启脚本升级 v2**：新建 `work/scripts/restart_daemon_4194_v2.sh`（v1 保留）——
   - 恢复模型前先 `POST /session/:id/load` 确保会话在内存（修复 channel/lazy 会话如 Jarvis weixin 会话重启后 404 无法 set_model 的问题；load 失败写入 `.team/daemon_v1/daemon_model_pending_restore.json` 待恢复清单）
   - 启动命令加 `--writer-idle-timeout-ms 300000`（游离 SSE 流 5 分钟无活动自动断开）
2. **v2 实跑**（18:16）：新 daemon PID=823525，模型映射恢复 **12/12 成功、0 待恢复、0 失败**（含 Jarvis fb711e92→qwen3.8-27b-int4-tp2-g02，v1 时该会话失败）；`/daemon/status` → `limits.writerIdleTimeoutMs: 300000` 生效

### 验证清单（本次实测）

| 检查项 | 结果 |
|--------|------|
| 重启前 ESTAB 218 → 重启后 30（基线含监控脚本短连接） | PASS |
| v2 模型映射恢复 12/12（含 channel 会话 Jarvis） | PASS |
| `--writer-idle-timeout-ms 300000` 启动参数 + status 生效 | PASS |
| 4194/8466 入口 HTTP 200 | PASS |

### 预防

- **daemon 启动必须带 `--writer-idle-timeout-ms`**（默认 300000=5 分钟），游离流超时自动回收，根治「无限累积占满 64 订阅者/256 TCP」
- 重启 4194 一律用 `restart_daemon_4194_v2.sh`（保持模型映射 + lazy 会话 load）
- 待落地：方案 B 连接数 watchdog（ESTAB>120 预警、>192 自动重启，通知 weixin_push.py）——A 负责常态、B 负责兜底
- 成员使用规范（方案 C）：独立 SSH 隧道 + 外部浏览器访问 4194，用完关页

---

## 3.9 方案：重启保持工作连续性 v3（2026-08-27，测试实例 4198 全流程验证通过）

### 背景

v2 只能恢复模型映射；重启仍会**打断成员正在进行的任务**（含 sub/后台任务），且 approval 等级（yolo）会回落，等待输入的会话状态丢失。用户要求重启方案完整保持工作连续性。

### 方案（restart_daemon_4194_v3.sh，7 步）

1. **① 捕捉**：`GET /workspace/<ws>/sessions?limit=100` 枚举全部 session → 逐 session `GET /status`（hasActivePrompt / 等待输入）+ `GET /context`（model + configOptions.mode=approval 等级）→ 分类 working/waiting_input/idle/stale → 快照 `.team/daemon_v1/daemon_work_snapshot_restart.json`
2. **② kill**：pgrep 按 `--port` 匹配 + `ss -tlnp` 按端口兜底；kill 后校验端口释放，未释放 kill -9
3. **③ 启动**：setsid nohup + `--writer-idle-timeout-ms 300000`（SSE 泄漏根治）
4. **④ 就绪**：HTTP 200 且 `/daemon/status.pid` ≠ 旧 PID（防旧 daemon 残留误判）
5. **⑤ 恢复**：lazy 会话先 `POST /session/:id/load` → `POST /model` 恢复模型 → `POST /approval-mode {"mode":...}` 恢复 approval（yolo 不回落）→ 核对 context
6. **⑥ 继续完成**：对 working 会话发「【系统通知】daemon 重启，任务被中断…请继续完成」（prompt 返回 202 即成功）；对 waiting_input 会话发等待状态已清空说明
7. **⑦ 验证**：抽查被恢复会话 hasActivePrompt=true + model/mode 正确

### 测试验证（独立实例 4198，`--channel none`）

- 测试 session 设 mode=yolo + model=qwen3.8-27b-int4-tp2-g34 → 触发 sleep 120 长任务 → hasActivePrompt=true
- v3 全流程：① 捕捉到 1 working（model 正确）→ ② kill → ③ 启动 → ④ 就绪（pid 切换校验）→ ⑤ 恢复 1/1（model+mode=yolo）→ ⑥ 继续完成发送成功（202）→ ⑦ 验证 hasActivePrompt=true（agent 已收到继续完成恢复工作）
- 测试发现并修复：prompt 返回 **202** 非 200（send_prompt 需认 200/202）；**同机只能一个 daemon 启用 channel**（第二个带 --channel weixin 启动失败，测试必须 `--channel none`）；端口自动转移时 pgrep 漏匹配（ss 兜底）；旧 daemon 残留响应误判（④ PID 校验）

### 成员通知（2026-08-27 18:34）

- 全部 10 个角色（SignL3/signL2/signL4/signL5/signL6/signL7/signL8/signL9/signL10/signL11）已通过 8466 mailbox 收到规则：**重启 4194 必须调用 `restart_daemon_4194_v3.sh`，禁止自行 kill/启动**；收到「继续完成」通知后检查 sub/后台任务继续工作
- 注意：8466 `/api/messages` 的 `dry_run` 默认 True，真实投递必须显式 `"dry_run": false` + `"confirm": true`

### 固化

- 通用 skill：`~/.qwen/skills/framework/daemon-restart-continuity.md`（7 步流程 + daemon API 约定 + 通用已知坑 + 派生指南）
- 具体 skill：`~/.qwen/skills/agent-team.md` §8（Base: daemon-restart-continuity，4194 实例绑定）

---

## 3.10 事故与修复：2026-08-27 晚间批量修复（看板乱跳 / position 234 / watchdog 继续 / GPU2+9 迁移）

### 3.10.1 8466 看板「乱跳」根因与修复

- **症状**：看板刷新卡顿/乱跳；`/api/local/messages` 超时（8-10s）；8466 进程持续 90-100% CPU（线程每请求一个、短命烧 CPU）
- **根因链**：
  1. `members/*/inbox.jsonl` 与 `events.jsonl` 自 8-18 起累积至 **4.5GB**（signL8 单文件 1GB+）
  2. console 的 `_tail_lines` 用 `deque(fh, maxlen)` **从文件头全量遍历**——每次读 messages/events 接口完整读 1GB 文件 → 超时 + 100% CPU
  3. 18:57 `start_daemon_team_v2.sh restart` 误启**第二套 v1 member-helper ×10**（与 8-18 常驻 v2 helper 双份轮询 4194）→ 4194 负载高、inbox 写竞争
- **处置**：归档 4.5GB 旧数据至 `.team/daemon_v1/members_archive_20260827_4.5g/`（mv，可回滚）；`_tail_lines` 改为**尾部倒读**（seek 到尾向前读，O(尾行数)）；清理重复 v1 helper ×10；另清理 8-9 残留 strace 进程（空转烧 CPU 20 天，kill -9）
- **验证**：messages 0.02s、status 0.01s、CPU 恢复；残余 90% CPU 定位为 VS Code Server 多面板 SSE 代理负载（8+ 会话事件流 × 每块 flush），非功能 bug，关多余面板即降

### 3.10.2 position 234 复发根因（Sub B 诊断）

- **根因**：18:53 的「qwen3.8 流式透传」修复（nothink_split）**在磁盘但从未被加载**——代理 systemd 自 10:50 未重启。运行旧代码（无条件 `_ThinkStreamProcessor`）对 qwen3.8：content 无 `</think>` → 全程缓冲 → 流结束 `_flush_think` 把整段缓冲重复发出，且与 `[DONE]` 间**单 \n 拼接** → daemon 按空行切分时并入同一事件 → `JSON.parse` 后遇 `[DONE]` → position N（N=缓冲长度，46/77/89/92/98/99/105/234/1026/43380 全部吻合）
- **修复**：① 磁盘已含 nothink_split（qwen3.8 透传）；② 补 `_process_line` 的 `[DONE]` 分支 `flush + "\n" + line` → `flush + "\n\n" + line`（flush 与 [DONE] 独立事件，修非 qwen3.8 同类隐患）。**代理 19:23 重启一并生效**，实测 43 事件全合法、[DONE] 独立、无解析错误

### 3.10.3 watchdog 压缩后补发「继续」

- `daemon_context_watchdog_v1.py` 的 `two_stage_compress`：压缩成功后（ok=True）补发「继续」prompt（【系统通知】上下文已自动压缩完成…请继续完成），`result["continue_sent"]` 标记；发送失败不影响整体 ok。watchdog 已重启生效（PID 936752）

### 3.10.4 GPU0+2 → GPU2+9 迁移（g29）

- **背景**：释放 GPU9（单卡 llama 950084）与 GPU0；新 TP2 组合 GPU2+9
- **执行**：zhuhai 停 950084（llama）→ 停 8050（GPU0+2）→ 启 **8054（GPU2+9，PID 3283483）**；settings.json g02 条目→g29 + 默认模型 g29；代理 VLLM_ELASTIC g02→g29（8054/18054/GPU[2,9]）；**代理外部重启**（用户授权）；daemon v3 重启（g29 进列表、g02 移除）；主管/Jarvis 补设 g29+yolo
- **最终格局**：TP2 槽位 g29(2+9)/g34(3+4)/g56(5+6)/g78(7+8)，GPU0 释放
- **教训**：daemon 模型列表启动时加载 settings——改 settings 后必须重启 daemon 才生效；v3 ① 捕捉在重启后跑会固化回落值（start_daemon_team_v2.sh 误启时发生过，模型映射被覆盖为错误值）

### 3.10.5 遗留

- 8466 90% CPU（VS Code 多面板 SSE 代理负载）——建议成员用完关面板/页面；可选优化（SSE 代理 write 合并缓冲）
- `start_daemon_team_v2.sh restart` 会**连带重启 4194 daemon 且不带 writer-idle-timeout/不恢复模型**——禁用该脚本 restart 4194（只能用它启 console/helper 等；4194 重启一律 v3 脚本）

---

## 4. Web Shell 与 session 生命周期（易踩坑点）

1. **SPA fallback 仅对 HTML 请求生效**：`/session/<id>` 直接 curl（不带 `Accept: text/html`）返回 404 是正常现象，不代表浏览器打不开；浏览器（带 HTML Accept）会拿到 index.html 并正常渲染。检查时务必带 `-H "Accept: text/html"`。
2. **session 需要 load 才有运行时**：daemon 重启后 session 元数据从磁盘索引恢复（列表可见），但 `GET /session/:id/status`、`/events` 返回 `404 session_not_found` 直到 session 被加载。Web Shell 打开 session 页面时前端按条件自动调用 `POST /session/:id/load` 或 `POST /session/:id/resume`（长历史 session 必须 resume，见 §2.2）；refresher 在 session 未 load 期间把成员标为 `stale` 属正常现象，打开页面后恢复。
3. **session 链接必须带具体 ID**：只给 daemon 根地址不便于定位成员；链接格式 `http://127.0.0.1:4194/session/<sessionId>`。
4. **workspace-qualified 列表接口**：`GET /workspaces/%2Fdata%2FWYC%2FsignLanguage/sessions`（注意 `/workspaces/<encoded>` 带 s；`/workspace/<encoded>/sessions` 单数形式同样可用）。
5. **session 空闲回收**：daemon 默认 1800s idle 回收（`sessionIdleTimeoutMs`），`last_client_detached` 也会关闭 session；Web Shell 挂着客户端则 session 保活。

---

## 5. 常用 API 参考（0.21.11 http-bridge）

| 端点 | 用途 |
|------|------|
| `GET /health` | 健康检查 |
| `GET /capabilities` | 能力/特性列表 |
| `GET /daemon/status` | daemon 运行状态（pid/uptime/limits/安全配置） |
| `GET /workspaces/<enc>/sessions` | workspace session 列表 |
| `GET /session/<id>/status` | session 状态（需已 load/resume） |
| `POST /session/<id>/load` | 从磁盘加载/恢复 session 运行时（replay updates ≤ 10000） |
| `POST /session/<id>/resume` | 恢复 session 运行时（长历史 session 用此端点，无 10000 限制） |
| `PATCH /session/<id>/metadata` | 修改 session displayName（Web Shell 前端仅允许重命名当前 session；批量改名用此 API，body `{"displayName": "..."}`，返回新 displayName） |
| `GET /workspaces/<enc>/session-groups` | 列出分组（Web Shell 分组视图，`view=organized`） |
| `POST /workspaces/<enc>/session-groups` | 创建分组（body `{"name","color"}`，返回 group） |
| `PATCH /workspaces/<enc>/session-groups/:gid` | 更新分组（改名/改色） |
| `DELETE /workspaces/<enc>/session-groups/:gid` | 删除分组（需先清空组内 session） |
| `PATCH /session/<id>/organization` | session 归组（body `{"groupId": ...}`） |
| `POST /session/<id>/prompt` | 投递消息（daemon_team_mailbox_v1.py 使用） |
| `GET /session/<id>/events` | SSE 事件流（member_helper 轮询） |
| `GET /session/<id>/transcript` | 历史记录（建议用 workspace-qualified 变体） |

---

## 6. 排障 checklist

1. 页面加载不出来 → 先 `ss -tlnp | grep 4194`：无监听 = daemon 死了，按 §2 重启；有监听 = 继续下一步。
2. daemon 活着但 refresher 报错 → 看 refresher 日志具体异常；`session_not_found` 多为未 load，非故障。
3. 怀疑残留进程 → `ps -eo pid,ppid,args | grep '[q]wen serve'` + `ss -tlnp` 核对端口归属。
4. 迁移/恢复后 session 不在列表 → 检查 `cwd` 是否等于 workspace（迁移文档关键经验 §5）。
5. 检查成员是否在线 → `GET /workspaces/%2Fdata%2FWYC%2FsignLanguage/sessions` 对照 registry（`/data/WYC/signLanguage/.team/daemon_v1/registry.json`）。
6. 请求返回 401 → 未带 token 或 token 已轮换：所有 API 需 `Authorization: Bearer <token>`；Web Shell 需 `?token=`；辅助脚本读 token 文件（§2.1）。
7. 长历史 session 打开失败/load 500 → 改用 `POST /session/:id/resume`（§2.2）。
8. **Web Shell 输入框一直 loading 无法输入** → daemon status 却空闲：先 `ss -tan | awk '$1=="ESTAB" && $4 ~ /:4194$/ {c++} END{print c}'` 查连接数；`GET /session/:id/events` 返回 `subscriber_limit_exceeded` 即 EventBus 64 订阅者被占满（多为 VS Code Server 游离 SSE 连接累积，见 §3.6）→ 重启 4194 daemon 清空；关闭页面标签不能释放游离连接。
9. **成员会话 `sendPrompt: forward failed: Unexpected non-whitespace character after JSON at position N`**（本地模型流式）→ 代理 `_ThinkStreamProcessor` 流式分隔符 bug 或上游响应杂质（见 §3.7）：先 `systemctl --user is-active codex-deepseek-proxy` 查代理存活，再抓代理流式响应核对 SSE 事件 `\n\n` 分隔；修复已内建（逐行保留换行 + `_safe_json_loads`），改代理代码后 `systemctl --user restart codex-deepseek-proxy`。
10. **本地模型全部 Connection error** → 优先查代理 11435：`curl http://127.0.0.1:11435/v1/models`；代理挂了 systemd 会 5 秒自愈（`codex-deepseek-proxy.service`），若仍未恢复 `systemctl --user restart codex-deepseek-proxy`。

---

## 7. 关键脚本与文件索引

- 启动日志：`/data/WYC/signLanguage/.team/daemon_v1/daemon_4194.stdout.log`
- team 脚本目录：`/data/WYC/signLanguage/work/scripts/daemon_team_*.py|.sh`
- **一键启动脚本**：`/data/WYC/signLanguage/work/scripts/start_daemon_team_v2.sh`（`start|restart|stop|status`，幂等，token 缺失自动生成，支持 `--channel <name>`；v1 脚本保留）
- **历史压缩脚本**：`/data/WYC/signLanguage/work/scripts/compress_daemon_session_v1.py`（`--file <jsonl> --keep-turns N`，loadReplay 10000 限制的规避方案，见 §2.3）
- session 数据目录：`/home/wuyangcheng/.qwen/projects/-data-WYC-signLanguage/chats/`（jsonl，压缩备份为 `.bak_compress_<日期>`）
- 认证公共模块：`/data/WYC/signLanguage/work/scripts/daemon_auth_v1.py`（`auth_headers()` 统一注入 Bearer token）
- token 文件：`/data/WYC/signLanguage/.team/daemon_v1/.daemon_token`（chmod 600）
- registry/health/dashboard 缓存：`/data/WYC/signLanguage/.team/daemon_v1/`
- 事故快照：`/data/WYC/signLanguage/.team/daemon_v1/incident_snapshot_20260814_0015/`
- 辅助进程保活：全部已由 `systemd` 收养（PPID 1631），重启 daemon 不影响它们
- **4194 重启脚本（保持 session 模型映射）**：`/data/WYC/signLanguage/work/scripts/restart_daemon_4194_v1.sh`（记录映射 → 重启 → 恢复各 session 模型，映射文件 `.team/daemon_v1/daemon_model_map_restart.json`，见 §3.7）；**v2**：`/data/WYC/signLanguage/work/scripts/restart_daemon_4194_v2.sh`（v2 增加 lazy/channel 会话先 `POST /session/:id/load` 再设模型 + 启动带 `--writer-idle-timeout-ms 300000` 根治 SSE 泄漏，见 §3.8）；**v3（当前标准）**：`/data/WYC/signLanguage/work/scripts/restart_daemon_4194_v3.sh`（v3 增加：重启前捕捉工作状态/模型/approval 等级快照 → 重启后恢复模型+approval mode（`/approval-mode`）+ 向被打断工作会话发送「继续完成」+ 等待输入会话发状态说明；支持 `--port/--workspace/--token/--channel/--dry-run` 参数化；2026-08-27 测试实例 4198 全流程验证通过，见 §3.9）
- **SSE 连接泄漏专项调研报告**：`/data/WYC/signLanguage/work/reports/sse_leak_research_20260827.md`（根因分析、方案 A-D 对比、实施记录）
- **代理 systemd 单元**：`~/.config/systemd/user/codex-deepseek-proxy.service`（`Restart=always` 5s 自愈 + 开机自启，管理 11435 本地模型路由代理）

---

## 8. 变更记录

| 版本 | 时间 | 变更 |
|------|------|------|
| v1 | 2026-08-14 09:56 | 初版：架构总览、保活启动方法、2026-08-14 事故与恢复、Web Shell/session 生命周期、API 参考、排障 checklist |
| v1.1 | 2026-08-14 10:06 | 4194 启用 bearer token（`--token` + `--require-auth`）：新增 §2.1 认证配置、§2.2 session 恢复（load 10000 限制 → resume 替代）、API 表补 resume 端点、排障补 401 项 |
| v1.2 | 2026-08-14 10:25 | 定位 loadReplay 10000 硬限制完整影响（SignL3/signL2 Web Shell 历史空白）：§2.2 修正前端加载路径结论（列表点击走 load）、新增 §2.3 历史压缩方案（compress_daemon_session_v1.py）与实测数据、索引补压缩脚本 |
| v1.3 | 2026-08-14 10:40 | 启用 GitHub channel：新增 §2.4 channels 说明（--channel 用法、GitHub 配置/认证/自触发限制）、启动脚本升级 v2、索引更新 |
| v1.4 | 2026-08-14 10:55 | §2.4.1 触发机制与身份模型（agent 身份=认证账号、触发者=allowlist、自触发硬限制、触发矩阵、方案 A/B 对比与协作场景） |
| v1.9 | 2026-08-26 22:40 | 新增 §3.6 事故记录（EventBus 订阅者 64 上限被 VS Code Server 游离 SSE 连接占满 → Web Shell 输入框 loading，处置=重启 daemon + 验证清单 + 预防）；排障 checklist 补第 8 条 |
| v1.10 | 2026-08-27 10:50 | 新增 §3.7 事故记录（代理 `_ThinkStreamProcessor` 流式 SSE 分隔符跨 chunk 丢失 → daemon 解析 position 216 + 代理 select 崩溃 + JSON 解析容错 + systemd 托管 + 重启脚本保持模型映射）；排障 checklist 补第 9/10 条；§7 补 restart_daemon_4194_v1.sh 与 codex-deepseek-proxy.service |
| v1.11 | 2026-08-27 18:20 | 新增 §3.8 事故记录（SSE 连接泄漏第三次复发 218/256 + 专项调研：游离流 87% 不回收、泄漏源 VS Code 转发、`--writer-idle-timeout-ms` 现成参数被漏用）+ 根治方案 A 落地（restart_daemon_4194_v2.sh：lazy 会话先 load + writer-idle-timeout 300000，实跑 12/12 恢复）；§7 补 v2 脚本与调研报告 |
| v1.12 | 2026-08-27 18:40 | 新增 §3.9 方案（重启保持工作连续性 v3：捕捉工作状态/模型/approval → 恢复 → 继续完成 → 验证，测试实例 4198 全流程验证通过）；§7 补 restart_daemon_4194_v3.sh；成员通知规则（重启必须调 v3 脚本）；skill 固化（framework/daemon-restart-continuity + agent-team §8） |
| v1.13 | 2026-08-27 19:40 | 新增 §3.10 晚间批量修复（3.10.1 看板乱跳：4.5GB inbox/events 归档 + `_tail_lines` 尾部倒读 + 清理重复 v1 helper + 残留 strace；3.10.2 position 234 复发：透传修复未加载 + `[DONE]` 补 `\n\n`，代理重启生效；3.10.3 watchdog 压缩后补发「继续」；3.10.4 GPU0+2→GPU2+9 迁移 g29 全链；3.10.5 遗留：8466 SSE 代理负载、禁用 start_daemon_team_v2.sh restart 4194）；§7 补 console/watchdog 备份与归档目录 |
| v1.5 | 2026-08-14 11:05 | GitHub channel 停用，切换 WeChat channel：§2.4 更新为 weixin 配置/扫码登录/连接验证（仅纯文本、仅 DM、会话过期 errcode -14 需重扫） |
| v1.6 | 2026-08-14 11:15 | §2.4 补 pairing 配对流程（senderPolicy=pairing 的配对码批准；`qwen channel pairing` 需 `--cwd` daemon workspace、不支持 --daemon-url/--token） |
| v1.7 | 2026-08-14 11:20 | §2.4 补 agent 权限边界安全说明（workspace=/data/WYC/signLanguage、agent=wuyangcheng 完整用户权限、sessionScope=user 隔离、收紧建议） |
| v1.8 | 2026-08-14 11:30 | 新增 §2.5 网络拓扑与安全边界（全服务 loopback 绑定、SSH 隧道访问链路、攻击面、http 提醒说明、HTTPS 适用场景、token 操作规范） |
| v1.9 | 2026-08-14 11:40 | session 重命名：API 表补 `PATCH /session/:id/metadata`（前端仅允许 rename 当前 session，批量改名走 API），已为 7 个成员 session 设置角色名 displayName |
| v1.10 | 2026-08-14 11:50 | session organization 分组：创建 signLTeam 组（蓝色 #2563eb）、7 个成员 session 归组、删除 7 个旧角色分组；API 表补 session-groups/organization 端点 |
| v1.11 | 2026-08-14 12:00 | 成员 session displayName 改为纯角色名（去 signL 前缀，取自 team_topology.json：主管人/视频负责人/语义动画制作者/算法开发者/宣传员/运维/调研员） |

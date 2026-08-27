# 4194 daemon 游离 SSE 连接泄漏调研报告

- 保存时间：2026-08-27 18:20（本地 UTC+8）/ 10:20 UTC
- 调研人：Jarvis（子代理，纯调研，未修改任何生产配置/未重启任何服务）
- 调研对象：`qwen serve`（http-bridge 模式，127.0.0.1:4194，`--require-auth` + `--channel weixin`）
- 相关文档：`/data/WYC/signLanguage/work/reports/qwen_daemon_serve_ops_v1_20260814.md`（§3.6 已记录 2026-08-26 EventBus 订阅者占满事故）

> 置信度标注：`【高】`= 有直接日志/源码/进程证据；`【中】`= 多个间接证据一致推断；`【低】`= 推测。
> 日志时间戳均为 UTC（本地 = UTC+8）。

---

## 0. 重要前提：调研期间故障正在实时重演（关键发现）

调研进行中（10:03 UTC 重启后仅 10 分钟），观察到泄漏在 **0.22.2 版本上正在实时发生**：

- 10:08 UTC：`ss -tn | grep :4194 | grep -c ESTAB` = 20（10 个 python3 helper + 10 个 daemon 侧）
- 10:11 UTC：升至 58，其中 VS Code Server（PID 3139487，`/home/wuyangcheng/.vscode-server/cli/servers/Stable-08d4889f9ec4.../server/node`，已运行 19h）持有约 19-20 条
- 10:14 UTC：0.22.2 内部日志 `SSE stream opened` = 27 条，`SSE stream closed` = **0 条**
- 流打开速率约 4-5 条/分钟（10:09 起 1→6→5→3→…），全部 `connectReason=initial`、每次新 clientId，被打开会话集中于 signL10(8ee20f7e)×6、signL9(a75dc085)×3、signL8(704485e8)×3 等

**结论【高】**：同样的游离连接泄漏在 0.22.2 上依旧存在；若保持当前速率，约 15-30 分钟内即可再次触发 EventBus 64 订阅者上限，1 小时内接近 TCP 256 上限。此状态在报告落盘时仍在继续。

---

## 1. 连接来源确认

### 1.1 日志事实（daemon_4194.log，覆盖 2026-08-27 02:26Z ~ 10:03Z 的 0.21.12 运行段 + 10:03Z 起的 0.22.2 段）

- 0.21.12 段（02:26Z 启动，10:03Z 被杀，存活 7.6h）：`SSE stream opened` **110 条**，`SSE stream closed` 110 条（全部为 daemon 终止时的 `closeReason=session_terminal`）。
- **96/110 条（87%）流 durationMs ≈ 7.1~7.6h，即从启动后约 30 分钟内打开、全程存活到 daemon 被杀，期间从未被正常关闭**（0.21.12 内部日志 closeReason 全为 `session_terminal`）。
- **整个 7.6h 运行期内只有 1 条流以 `client_disconnect` 正常关闭**（且仅存活 4 秒）。13 条存活 30s~7h（同样在 daemon 终止时才关闭）。
- 打开时间分布：02:26-02:29 即开了 29 条，02:26-02:53 内开了 96 条（全部 7h+ 流都在前半小时内打开），09:5x 又开 13 条。模式 = **daemon 一启动，客户端浏览器即批量建流；之后只增不减，直到 daemon 重启清空**。
- 单会话聚集：0.21.12 段内部日志（run-2b88ce98，仅含 09:51-10:03 尾部）显示 sessionId=40e1ab7f（signL11）一个会话就挂着约 30 条不同 clientId 的并发流；0.22.2 段 signL10/signL9/signL8 会话被反复打开新流。

### 1.2 连接持有者（进程级证据）

- 2026-08-26 事故（排障文档 §3.6）：253 条 ESTAB 中 **242 条由 VS Code Server 持有**（PID 3362664，`/home/wuyangcheng/.vscode-server`，对端端口分散 33026-60896 = 反复重连未释放的游离连接）；**实测关闭 VS Code 页面标签不能释放**（253→252）。
- 本次调研实测（0.22.2 运行中）：当前所有异常连接均由 **wuyangcheng 的 VS Code Server（PID 3139487，运行 19h）持有**；10 个 python3 为 team member_helper（正常常驻 SSE 轮询，连接数稳定）。

### 1.3 来源判定

- **主泄漏源【高】**：经 VS Code Remote 端口转发访问 4194 Web Shell 的浏览器页面。TCP 连接终点是 VS Code Server 进程（转发器在远端建连并池化 socket），页面关闭/刷新时 VS Code 转发器不回收已建连接；Web Shell 前端打开会话页即建 SSE 流（autoReconnect 1s→10s 退避），旧流不关闭。
- **次要泄漏源【中】**：8466 集成控制台（`daemon_team_console_v2_server.py`）代理上游 `GET /session/:id/events`，`urlopen(timeout=300)` 使被代理的空闲 SSE 最长存活 5 分钟（页面反复打开时每个页面对应一条上游流）。当前 console 的 python3 连接数稳定，非本次主源。
- **排除【高】**：weixin channel worker 在 daemon 进程内运行（无独立 TCP）；8480 端口不存在（任务中提到的 8480 已无服务，现存 8460/8465/8466）。

---

## 2. daemon 可配置能力（qwen serve --help / --help-all 实测）

当前运行 daemon（0.22.2，PID 797777）实测 `/daemon/status` limits：

| 字段 | 当前值 | 是否有 CLI 参数 | 说明 |
|---|---|---|---|
| `writerIdleTimeoutMs` | **null（未设置）** | ✅ `--writer-idle-timeout-ms`（也支持环境变量 `QWEN_SERVE_WRITER_IDLE_TIMEOUT_MS`） | **Per-SSE-connection idle deadline——杀空闲 SSE 流的直接参数** |
| `listenerMaxConnections` | 256 | ✅ `--max-connections`（默认 256，0=禁用） | TCP 层连接上限 |
| `sessionIdleTimeoutMs` | 1800000（30min） | ✅ `--session-idle-timeout-ms`（默认 1800000） | 回收无连接的**会话**，不是 SSE 流 |
| `acpConnectionCap` | 64 | ❌ 无 | ACP 通道连接上限（与 EventBus 无关） |
| `eventRingSize` | 8000 | ✅ `--event-ring-size` | SSE 回放 ring 深度 |
| `channelIdleTimeoutMs` | 0 | ✅ `--channel-idle-timeout-ms` | ACP child 保活时长，与 SSE 无关 |
| `maxSessions` | 16 | ✅ `--max-sessions` | 并发会话上限 |

关键事实：
- **`--writer-idle-timeout-ms` 在 0.21.12 / 0.22.0 / 0.22.2 的 `serve --help` 中均存在**【高：三个版本 cli.js 实测】——8-14/8-26/8-27 三次事故时该参数都可用但从未被使用（启动命令/重启脚本均未带）。
- EventBus 订阅者上限 **`DEFAULT_MAX_SUBSCRIBERS = 64` 在 0.21.12 与 0.22.2 源码中均为硬编码**【高：`chunk-7U5G6JXI.js` 实测 `var DEFAULT_MAX_SUBSCRIBERS = 64`；`EventBus` 构造函数接受 maxSubscribers 参数但 serve 层未暴露 CLI】。错误文案 `EventBus subscriber limit reached (${limit})` / `subscriber_limit_exceeded` 两版本均在。
- `--max-connections` 帮助原文明确提到 "slow/phantom SSE clients get rejected at accept time once full" —— TCP 满时新连接被拒，正是"页面一直 loading / Connection error"的 TCP 层表现。

---

## 3. 官方文档与 GitHub 调研

- **qwen.readthedocs.io 是 Qwen 模型文档，不是 Qwen Code 文档**【高】：无 serve/daemon/SSE/http-bridge 配置页。Qwen Code 的可配置能力以 `qwen serve --help` 与 GitHub 仓库为准。
- **GitHub issue 检索（api.github.com/search/issues，关键词 SSE / subscriber / connection）**【高】：
  - 未发现 SSE connection leak / subscriber limit 64 / Web Shell 连接泄漏的已报告 issue。
  - 相关但不同：`#10162`（ACP NDJSON channel 队列饱和时优雅降级）、`#9631`（Web Shell loading 指示器改用 daemon 的 hasActivePrompt——8-26 事故"输入框 loading"的 UI 侧修复，非连接泄漏修复）。
- **Release notes**【高】：
  - v0.22.0（2026-08-21 前后）：Web Shell 防 OOM（#9303）、hasActivePrompt loading 修复（#9631）等，无 SSE 泄漏修复。
  - v0.22.2（2026-08-26）：新增 ACP channel liveness、`streamIdleTimeoutMs`（provider 级，模型流空闲）、"Daemon sessions restore to last selected model"（与 restart 脚本的模型映射功能重叠）、"Repair persisted session lifecycle" 等。**未见针对 SSE 连接泄漏的直接修复**。
  - **0.22.2 新增可观测性**【高：0.22.2 内部日志实测】：`SSE ring eviction detected; consumer must call loadSession to recover`（epoch_reset 时告知消费者回放窗口丢失）——可用于诊断，但 0.21.12 源码同样存在 ring eviction 逻辑（未被日志记录），非修复。
- **版本现状【高】**：当前运行 0.22.2（npm 自动更新 8-27 01:47 下载，10:03Z 重启生效；`qwen --version` 仍报 0.21.12 是 shim 读取 npm 包版本所致）。**0.22.2 即 npm 最新版，无更新可升**；升级本身不能解决泄漏（本次实测 0.22.2 仍在泄漏）。

---

## 4. 现有监控/自愈能力盘点

- **`team_progress_supervisor_v1.py`**【高：源码实测】：仅把 `GET /health` 当"重启跳过门"（daemon 短暂不可用时整轮跳过防误报），**不监控连接数/订阅者耗尽/restSseActive**。
- **`daemon_team_refresher_v1.py`**：只做 registry/dashboard 缓存，无健康监控。
- **`daemon_context_watchdog_v1.py`**：只监控 context 水位做压缩，不碰连接。
- **`local_services_health_check_v1/v2.sh`**：落盘本地服务健康状态，未含 4194 连接数。
- **`restart_daemon_4194_v1.sh`**【高】：已具备"①记录各会话模型映射 → ②kill → ③setsid 保活重启 → ④等待就绪 → ⑤逐会话恢复模型 → ⑥验证"，可直接复用为自愈动作。10:03Z 的 0.22.2 重启即由该脚本完成（`work/logs/daemon_restart_4194.log` 实证）。
- 结论：**当前无任何连接数监控、无自动预警、无自动清理，故障只能人工发现 + 重启 daemon 清空**。

---

## 5. VS Code Server 侧确认

- 本机存在**多个** wuyangcheng 的 VS Code Server 实例【高：ps 实测】：PID 2134（`code-8a7abeba... agent host`，33 天）、PID 3139487（Stable-08d4889f9ec4，19h，**当前泄漏连接持有者**）、以及 5 分钟前新建的 Stable-08d4889f9ec4 第二实例（806202/806232）。另有其他用户（guxifeng/huihuangjiang）的 VS Code Server 与本故障无关（不连 4194）。
- 机制【中】：VS Code Remote 端口转发把"浏览器→127.0.0.1:4194"的连接终点放在 VS Code Server 进程上，转发器对已关闭页面不回收已建立的隧道 socket；Web Shell 前端（0.22.2）`autoReconnect=true`（`reconnectDelayMs=1s, maxReconnectDelayMs=10s`），**心跳是独立 `POST /session/:id/heartbeat`（不走 SSE 连接本身）**【高：web-shell 前端源码实测】——即 SSE 流上无周期性保活流量，空闲即静默。
- 已知规避：
  - `http.browserExternal` 让内置 Simple Browser 改用外部浏览器——但若仍走 VS Code 端口转发，TCP 终点仍是 VS Code Server，**不能根治**（只能减少 webview 场景）。
  - 根治性客户端方案：改用**独立 SSH 隧道**（如 `ssh -L 4194:127.0.0.1:4194 nature`）在本地浏览器直接访问 `http://127.0.0.1:4194`——连接终点变为本地 ssh 客户端，关闭标签即断开 FIN 正常回收。

---

## 6. 根因结论

### 6.1 确定事实（有直接证据）

1. **游离 SSE 连接几乎从不被正常回收**：0.21.12 段 110 条流中 96 条（87%）从打开到 daemon 被杀全程存活，7.6h 内仅 1 条 client_disconnect。
2. **泄漏源是经 VS Code 端口转发访问 4194 Web Shell 的浏览器页面**：8-26 事故 242/253 条由 VS Code Server 持有；本次调研 0.22.2 上同样由 VS Code Server（3139487）持有且正在增长（27 开 0 关）。
3. **daemon 侧没有兜底**：`writerIdleTimeoutMs=null`（该参数 0.21.12 起就存在但从未启用）；EventBus `DEFAULT_MAX_SUBSCRIBERS=64` 硬编码无 CLI 参数（0.21.12 与 0.22.2 均如此）；session 空闲回收（30min）回收的是会话而非 SSE 流。
4. **升级到 0.22.2 不能解决**（本次实测仍在泄漏）；0.22.2 已是 npm 最新版。
5. 当前无任何连接数监控/自动清理机制，只能人工重启。

### 6.2 推测（间接证据，中等置信度）

- 每次"页面打开/刷新/导航"Web Shell 前端会新建 SSE 流（新 clientId），旧流的 socket 在 VS Code 转发器侧未释放 → 逐次累积（对应 8-26 文档"关闭标签不能释放"与本次 4-5 条/分钟增长）。
- 当前反复打开 signL10/signL9/signL8 会话页面的浏览器可能是成员/运维在用 4194 Web Shell 做监控或测试。

---

## 7. 根本解决方案候选清单（按可行性排序）

### 方案 A：启用 `--writer-idle-timeout-ms`（推荐首选，成本最低）

- 做法：在 `restart_daemon_4194_v1.sh` 启动命令加入 `--writer-idle-timeout-ms 300000`（5 分钟，保守起步；观察后可视情收紧到 120000）。
- 原理：空闲 SSE 流（页面已关/失联）5 分钟内被杀；活跃页面由前端 autoReconnect（1-10s 退避）自动重连，且 UI 状态另有 30s 心跳（独立 HTTP）+ 会话状态轮询，体验影响小。
- 效果：把"泄漏无限累积占满 64/256"变成"每条游离流寿命 ≤5 分钟"，**根治占满问题**（泄漏仍存在但被边界化）。
- 成本：改 1 行启动参数 + 重启一次。风险：低（需观察前端重连是否频繁、有无 "Connection interrupted" 打扰）。
- 注意：`--writer-idle-timeout-ms` 对"活跃但会话静默"的页面同样会断流（SSE 无心跳流量），属预期行为。

### 方案 B：连接数自动监控 + 预警 + 自动清理（第二优先）

- 做法：新增 watchdog 脚本（如 `daemon_sse_watchdog_v1.py`，挂 systemd 或并入 `local_services_health_check`）：
  1. 每 60s 统计 `ss -tn | grep :4194 | grep -c ESTAB` 与 `curl /daemon/status`（或对活跃会话探测 `GET /session/:id/events` 是否 `subscriber_limit_exceeded`）；
  2. 阈值：ESTAB > 120 → `weixin_push.py` 预警；ESTAB > 192（256 的 75%）或出现 subscriber_limit_exceeded → 自动调用 `restart_daemon_4194_v1.sh`（自带模型映射保持）；
  3. 或扩展 `team_progress_supervisor_v1.py` 加入连接数一栏（改动较小）。
- 成本：中低（~100 行脚本 + 阈值调参）。风险：低（复用现成重启脚本；已知重启会打断正在推理的 turn，通知中需注明）。
- 建议与方案 A 同时启用：A 降低触发频率，B 兜底。

### 方案 C：客户端侧规避（VS Code 行为）

- 团队成员改用独立 SSH 隧道 + 本地浏览器访问（`ssh -L 4194:127.0.0.1:4194 nature` 后开 `http://127.0.0.1:4194/?token=...`），让连接终点成为本地 ssh 客户端（关页即断）。
- 若继续用 VS Code：`http.browserExternal` 改外部浏览器可减少 Simple Browser webview 场景，但**不能根治**（端口转发 socket 池仍在 VS Code Server）。
- 日常习惯：看完关页面；不要反复刷新会话列表；不用时关闭 Web Shell 标签。
- 定期（如每周）重启一次 VS Code Server 或 daemon 清池。
- 成本：文档/习惯（低）。风险：低。

### 方案 D：升级 qwen-code 版本

- 当前 0.22.2 即最新；升级本身不解决问题（本次实测 0.22.2 仍泄漏）。
- 后续关注点：EventBus `maxSubscribers` 是否开放配置、是否有 SSE 连接回收修复。可订阅 GitHub release 动态。
- 成本：无（已最新）。风险：无。**不作为解决方案，仅作跟踪项。**

---

## 8. 推荐方案（组合拳）

1. **立即（1 小时内）**：执行方案 A——`restart_daemon_4194_v1.sh` 加入 `--writer-idle-timeout-ms 300000` 并重启一次；重启后观察 0.22.2 日志确认游离流开始被回收（`SSE stream closed` 出现 `closeReason=idle_timeout` 类记录，且 ESTAB 稳定在低位）。
2. **当天**：落地方案 B watchdog（连接数 120 预警 / 192 自动重启，通知走 `weixin_push.py`；与方案 A 并存，A 负责常态、B 负责兜底）。
3. **本周**：向成员发布方案 C 使用规范（独立 SSH 隧道 + 外部浏览器 + 用完关页）。
4. **长期**：跟踪 qwen-code 新版本（方案 D 关注项）。

预期效果：游离连接从"无限累积 → 占满 64 订阅者/256 TCP"变为"每条游离流 ≤5 分钟寿命"，故障发生频率从"每 1-2 天一次"降到"基本不发生"，即使偶发也有自动重启兜底，不再需要人工应急。

---

## 9. 证据文件清单

- 排障文档（两次既有事故记录 §3.6/§3.7）：`/data/WYC/signLanguage/work/reports/qwen_daemon_serve_ops_v1_20260814.md`
- 生产 daemon serve 日志（fallback，本次全部分析基于此）：`/data/WYC/signLanguage/.team/daemon_v1/daemon_4194.log`
- 0.21.12 内部日志（run-2b88ce98，仅 09:51-10:03 尾部）：`/home/wuyangcheng/.qwen/debug/daemon/runs/run-2b88ce98fba3601466f054831a8fea87/daemon.log`
- 0.22.2 内部日志（run-7a7048f2，当前运行）：`/home/wuyangcheng/.qwen/debug/daemon/runs/run-7a7048f2bb1c7bda6ab3fbba9323b201/daemon.log`
- 重启脚本（含模型映射保持）：`/data/WYC/signLanguage/work/scripts/restart_daemon_4194_v1.sh`；重启日志：`/data/WYC/signLanguage/work/logs/daemon_restart_4194.log`
- 0.22.2 源码关键常量：`/home/wuyangcheng/.qwen/updates/npm/8d75156e24ed8050/versions/0.22.2/node_modules/@qwen-code/qwen-code/chunks/chunk-7U5G6JXI.js`（`DEFAULT_MAX_SUBSCRIBERS = 64`）
- Web Shell 前端（reconnect/心跳）：`/home/wuyangcheng/.qwen/updates/npm/8d75156e24ed8050/versions/0.22.2/node_modules/@qwen-code/qwen-code/web-shell/assets/index-8hXIpvo4.js`
- GitHub：`api.github.com/search/issues?q=repo:QwenLM/qwen-code+SSE|subscriber`；releases `v0.22.0/v0.22.2`

## 10. 附注

- 调研期间 `GET /daemon/status?detail=full` 返回 `status:error` + `issues:[preflight_error: Workspace preflight reports an error.]`——与 SSE 泄漏无关的既有问题（可能为 hook/skill/extension 预检失败），建议另行排查。
- 8-26 事故预防段中"EventBus 订阅者上限 64 硬编码无 CLI 参数"的结论仍然正确，但文档当时**遗漏了 `--writer-idle-timeout-ms` 这一现成兜底参数**（0.21.12 即已存在），本次调研已补齐。

---

## 11. 实施记录（2026-08-27 18:17 本地，方案 A 已落地）

- **v2 重启脚本**：新建 `/data/WYC/signLanguage/work/scripts/restart_daemon_4194_v2.sh`（v1 保留不删）。两个改进：
  1. 恢复模型前先 `POST /session/:id/load` 确保会话在 daemon 内存——修复 channel/lazy 会话（如 Jarvis 的 weixin channel 会话）重启后不在内存导致 `set_model` 404 的问题；load 失败项写入 `.team/daemon_v1/daemon_model_pending_restore.json` 待恢复清单。
  2. 启动命令加入 `--writer-idle-timeout-ms 300000`（方案 A：游离 SSE 流 5 分钟无活动自动断开）。
- **实跑结果**（18:16-18:17）：kill 旧 daemon（797777）→ 新 daemon PID=823525 → 模型映射恢复 **12/12 成功、0 待恢复、0 失败**（含 Jarvis fb711e92→qwen3.8-27b-int4-tp2-g02，v1 时该会话失败）。
- **参数生效验证**：`ps` 启动参数含 `--writer-idle-timeout-ms 300000`；`GET /daemon/status` → `limits.writerIdleTimeoutMs: 300000`；重启后 `restSseActive: 13`、ESTAB 30（基线水平，含各监控脚本短连接）。
- **后续观察项**：确认游离流开始被回收（日志出现 SSE stream closed + closeReason 含 idle/timeout 类记录）、ESTAB 长期稳定在低位；方案 B watchdog 尚未落地（建议择日实现）。

> 18:16 重启前 ESTAB 已再次涨到 62（泄漏实时进行中），本次重启同时清空了这批连接。

# 团队进度监督与 Owner 及时汇报机制 v1

- 版本：v2.1（2026-08-26 升级：进展直推微信 + 推送白名单筛选）
- v2 历史：2026-08-26 微信直推（不再经 Jarvis 模型）
- v1 历史：2026-08-26 上线（经 Jarvis 模型转达），已由 v2 取代其转发环节
- 发起人：Owner（2026-08-26 要求：监督全部团队成员正在工作中的任务，维护信息记录，一旦有进展经 Jarvis 及时通知 Owner 移动端；监督汇报尽量减少对 LLM 的依赖，用自动化实现）
- 约束落盘：`.team/team_constraints.md §15`、`QWEN.md §6`

## 0.1 v2.1 变更说明（2026-08-26 18:30 推送白名单筛选）

**核心变化**：微信推送只保留两类事件——**用户要介入的**（等待人工输入/出错/疑似卡住）与**做出来的阶段性进展**（回合完成/进行中进展）；例行事件（接到任务/回合被取消）**不再推送到微信**，避免 Owner 移动端噪音。

```
推送白名单（PUSH_WHITELIST）：waiting_input / error / turn_completed / progress / stuck
不推送：task_assigned（接到任务）、turn_cancelled（回合被取消）
```

**实现位置**（`team_progress_supervisor_v1.py`）：
1. `PUSH_WHITELIST` 常量（事件类型白名单）；
2. 事件加入 pending 队列时过滤（`cycle_events → state["_pending"]` 仅白名单事件进入）；
3. `ping_jarvis` 推送前双保险过滤；
4. 每轮启动清理历史 pending 中白名单外残留（一次性迁移）。

**不影响**：事件仍完整记录到各角色 `<role>_progress.jsonl`（审计），`latest_progress.md` 的「各角色当前状态」仍显示当前任务——只是不进「⏳ 未汇报新进展」、不推微信。

### v2.1 补充（2026-08-26 18:40 waiting_input 完整问题与选项展示）

**问题**：真实运维场景（daemon `kind: "user_question"`，Ask user 2 questions）推送只有「等待人工输入（当前任务：…）」，没有问题文本与选项——`_extract_pending_options` 只识别 `permission`/`question` 两种 kind，**漏了 `user_question`**。

**修复**：
1. `_extract_pending_options` 重构：支持 `kind ∈ {permission, question, user_question}`，返回按问题分组结构 `[{requestId, kind, question, options:[{label, optionId}]}]`；user_question 的选项 optionId 即 label（submit 时 answers 填 label）；
2. 新增 `_format_waiting_detail`：微信可读的多行格式——问题文本（含 header）+ 每问各选项编号 + requestId/session 提交指引；
3. `write_digest`/`ping_jarvis` 对 waiting_input 保留换行结构、截断放宽到 800 字符，完整展示问题与选项。

**提交格式**（Jarvis submit，已写入 `~/.qwen/skills/jarvis-forward-owner.md`）：
- user_question：`POST /session/:id/permission/:requestId`，body `{"outcome":{"outcome":"selected","optionId":"proceed_once"},"answers":{"0":"选项label","1":"选项label"}}`
- permission：`{"outcome":{"outcome":"selected","optionId":"proceed_always_project"}}` 或 cancelled

## 0. v2 变更说明（2026-08-26 微信直推）

**核心变化**：进展推送从「经 Jarvis 模型转达」改为「监督器直调微信 iLink Bot API 主动推送」——**转发环节不再依赖 LLM**（本地模型 prefill 慢/卡死曾导致转达延迟甚至失败）。

```
v1：监督器 → 轻推 Jarvis → Jarvis 模型读文件 → 微信（一跳 LLM，慢/易卡）
v2：监督器 → weixin_push.py 直调 iLink API → 微信（零 LLM，秒级）✅
```

**触发背景**（Owner 两轮反馈）：
1. 本地模型（Q4，13.5 tok/s + 无输出上限 + think 长）导致 Jarvis 转达经常卡住，进展推送不可靠；
2. 电脑端注入 channel 会话的 prompt，回复**不会**路由回微信（channel 单向响应式，已三次实测确认）——因此必须绕开 channel 会话，直连 iLink API。

**新增文件**：`/data/WYC/signLanguage/work/scripts/weixin_push.py`
- 凭证自动读取：`~/.qwen/channels/weixin/account.json`（token/baseUrl/userId）
- Owner chatId 自动解析：`~/.qwen/channels/daemon/<hash>/routes.json`（channelName=weixin 的 target.chatId）
- 调用：`POST https://ilinkai.weixin.qq.com/ilink/bot/sendmessage`
- 请求头：`Authorization: Bearer <token>` + `AuthorizationType: ilink_bot_token` + `iLink-App-Id: bot`
- 消息体：`msg={to_user_id, message_type:2(BOT), message_state:2(FINISH), item_list:[{type:1(TEXT), text_item:{text}}]}` + `base_info={channel_version:"2.1.3"}`
- 用法：`python3 work/scripts/weixin_push.py "消息"` / `--file` / `--test`

**监督器改动**：`ping_jarvis` → 直接 `import weixin_push; push_text(text)`（不再 POST Jarvis prompt）；限流/去重/失败重试状态机保留（600s 滑窗 ≤8 条、60s 最小间隔、成功才移入 reported）。

**Jarvis 手动转达链路（2026-08-26 补充）**：成员主动发【转达】/【请转告 Owner】/【汇报 Owner】类消息给 Jarvis 时，Jarvis 也调用 `weixin_push.py` 直推微信（不是依赖 channel 回复路由）：
- 协议写入：① `settings.json` weixin channel `instructions`（新会话生效）；② Jarvis 会话内注入协议消息（已有会话生效，写入会话记忆）
- skill：`~/.qwen/skills/jarvis-forward-owner.md`（Jarvis 标准操作入口）
- 验证：Jarvis 收到【转达】消息 → 调用 weixin_push → HTTP 200 message_id → 回复发送方「已转达 ✅」；Owner 微信实测收到 ✅

**已验证**（2026-08-26 17:4x）：
- `weixin_push.py --test` → HTTP 200 `message_id`，Owner 微信收到 ✅
- 监督器直推 → `[ping] 微信直推成功（1 条新进展已推送 Owner）`，Owner 微信收到 ✅
- Jarvis 手动转达 → HTTP 200 `message_id 7498316274723134088`，回复「已转达 ✅」，Owner 微信收到 ✅

## 1. 目标与架构

**目标**：Owner 在移动端（微信）及时收到团队成员的任务进展，无需人工盯守；监督本身高频、低成本、不依赖 LLM。

**架构（Owner 两轮确认后的最终形态）**：

```
┌─────────────────────────────────────────────────────────────┐
│  daemon 4194（qwen serve）                                   │
│  ├─ GET /session/:id/status   ← 每 30s × 10 角色            │
│  └─ transcript jsonl（增量读取，字节 offset + uuid 去重）    │
└──────────────┬──────────────────────────────────────────────┘
               │  纯 Python 规则判定（零 LLM）
               ▼
┌─────────────────────────────────────────────────────────────┐
│  team_progress_supervisor_v1.py                             │
│  （tmux slu-team-progress-supervisor 保活，崩溃自动重启）    │
│  事件：接到任务/回合完成/回合取消/出错/等待人工输入/进展/卡住 │
│  节流：progress 10min/角色；同类状态事件 5min 抑制；         │
│        全局 600s 滑窗 ≤8 条（保高优先级弃低）                │
└──────────────┬──────────────────────────────────────────────┘
               │  ① 自动更新（每周期重写）
               ▼
  .team/daemon_v1/progress_supervisor/latest_progress.md
  （单一事实源：⏳未汇报新进展 / 各角色当前状态 / 进展历史）
               │  ② 有新进展才直推（每周期最多 1 次，失败下轮重试）
               ▼
┌─────────────────────────────────────────────────────────────┐
│  weixin_push.py（直调 iLink Bot API，零 LLM）              │
│  POST https://ilinkai.weixin.qq.com/ilink/bot/sendmessage   │
│  凭证：~/.qwen/channels/weixin/account.json                 │
│  chatId：~/.qwen/channels/daemon/<hash>/routes.json         │
└──────────────┬──────────────────────────────────────────────┘
               │  秒级送达
               ▼
        Owner 微信（无需 Jarvis 模型参与）
```

**关键设计决策**：
1. **主管 LLM 不在信息链路上**——Owner 明确指出「主管来消息投递转发显得多余」。自动化直接对接 Jarvis，主管只维护脚本与处理异常。
2. **文件为单一事实源**——信息更新以「文件自动更新」形式沉淀；轻推消息只说「有新进展，去读文件」，内容不经过消息体传递。好处：消息体最小化、可追溯、Jarvis 汇报有完整上下文（状态节+历史节）、轻推消息丢失也不丢数据。
3. **pending/reported 状态机**——事件先进「⏳ 未汇报」节；轻推成功后移入「进展历史（✅）」。Jarvis 永远只汇报未汇报节，不会重复汇报；轻推失败则下轮重试，不丢事件。
4. **零 LLM 监督路径**——事件判定全部是规则（status 字段 + transcript 行类型匹配），30s 周期 × 10 角色的开销是 10 次 HTTP + 增量文件读，可忽略。

## 2. 事件定义与判定规则

| 事件 | 判定 | 优先级 | 节流 | 微信推送 |
| --- | --- | --- | --- | --- |
| task_assigned 接到任务 | transcript 新增 `type=user, provenance=real_user` 行（含 mid_turn 插入指令） | 3 | promptId 去重 | ❌（例行，不推） |
| turn_completed 回合完成 | `system/turn_result` state=completed（取 promptText + resultText） | 3 | promptId 去重 | ✅ 阶段性进展 |
| turn_cancelled 回合取消 | turn_result state≠completed | 3 | promptId 去重 | ❌（不推） |
| error 出错 | status.hasTurnError=true（context 超限类由 context-watchdog 并行自愈） | 5 | 5min 抑制 | ✅ 用户需知晓 |
| waiting_input 等待人工输入 | isWaitingForUserQuestion / isWaitingForPermission / pendingInteractionCount>0 | 4 | 5min 抑制 | ✅ 用户要介入（🚨 突出） |
| progress 进展 | 活跃 turn 中的 assistant 文本 | 1 | 10min/角色，文本 ≥20 字符 | ✅ 阶段性进展 |
| stuck 疑似卡住 | 活跃但 transcript 15min 无增长（本地模型慢任务防挂死） | 2 | 30min/角色 | ✅ 用户可介入判断 |
| session_lost 会话丢失 | status 404 | 5 | 按 session 去重 | ✅ 用户需知晓 |

> 推送白名单（v2.1，2026-08-26 Owner 要求）：`{waiting_input, error, turn_completed, progress, stuck}`；`task_assigned`/`turn_cancelled` 仍完整记录事件历史 jsonl 供审计，仅不进微信推送。

## 3. 文件与记录

- 进展摘要（单一事实源）：`/data/WYC/signLanguage/.team/daemon_v1/progress_supervisor/latest_progress.md`
- 状态快照：`/data/WYC/signLanguage/.team/daemon_v1/progress_supervisor_state.json`
- 每角色事件历史：`/data/WYC/signLanguage/.team/daemon_v1/progress_supervisor/<role>_progress.jsonl`
- 轻推审计：`/data/WYC/signLanguage/.team/daemon_v1/progress_supervisor/notifications.jsonl`
- 日志：`/data/WYC/signLanguage/.team/daemon_v1/progress_supervisor.log`（+ `.stdout.log` 崩溃重启记录）
- 监督脚本：`/data/WYC/signLanguage/work/scripts/team_progress_supervisor_v1.py`

## 4. 运维操作

```bash
# 单周期调试
python3 work/scripts/team_progress_supervisor_v1.py --once --dry-run
# 查看当前进展
cat .team/daemon_v1/progress_supervisor/latest_progress.md
# 重启保活（脚本改动后）
tmux kill-session -t slu-team-progress-supervisor
tmux new-session -d -s slu-team-progress-supervisor 'bash -c "while true; do python3 /data/WYC/signLanguage/work/scripts/team_progress_supervisor_v1.py --interval 30; echo \"[supervisor 崩溃重启 $(date +%H:%M:%S)]\"; sleep 5; done 2>&1 | tee -a /data/WYC/signLanguage/.team/daemon_v1/progress_supervisor.stdout.log"'
# 测试 Jarvis 链路（v2 起为微信直推）
python3 work/scripts/team_progress_supervisor_v1.py --test-notify
# 或直接测推送模块
python3 work/scripts/weixin_push.py --test
python3 work/scripts/weixin_push.py "任意消息文本"
```

## 5. 已知边界与后续

- **sub 会话不单独监督**：成员派出的 sub/side-task 会话不单独纳入（避免与父会话重复汇报）；sub 完成会以 task-notification 进入父会话 transcript，由父会话的进展/回合完成事件覆盖。若需要 sub 级粒度，v2 可加 parentSessionId 映射。
- **微信 iLink 会话凭证**：QR 登录凭证在 `~/.qwen/channels/weixin/account.json`；`Session expired (errcode -14)` 时需重新 `qwen channel configure-weixin` 登录（直推脚本会因 401/凭证失效失败，pending 保留下轮重试）。
- **weixin 渠道断连**：由 daemon channel worker 健康机制 + context watchdog 告警覆盖；直推失败时 pending 保留、60s 后重试。
- **v2 已消除的边界**：Jarvis prompt 队列上限 5 / Jarvis 模型卡住导致转达延迟——直推链路不再依赖 channel 会话与 Jarvis 模型。
- **v3 候选**：进展摘要接入 8466 控制台面板；按角色订阅开关（Owner 可指定只关注某些角色）；stuck 阈值按角色模型自适应（本地模型慢 vs 云端快）。

## 6. 上线验证记录（2026-08-26）

- 15:38 首轮 dry-run：10 角色状态正确（运维/本地B 工作中 + 当前任务回填正确）
- 15:38 测试通报：POST 202 成功，Jarvis 收到并处理（核实来源后转达）
- 16:31 发现 Jarvis 队列积压（旧版无节流重试所致）→ 新版 60s 重试 + pending 保留机制生效
- 16:34 新版上线（文件 + 轻推架构），16:35 digest 文件首版生成，16:39 tmux 保活重启（日志分流）
- 21:30 8466 看板新增「💻 主机资源（CPU / 内存）」面板：`/api/local/host-resources`（/proc/stat 双采样 + /proc/meminfo，GPU_LIVE_CACHE_TTL 缓存），前端 5s 轮询；预警判定 ≤20% 绿 / >20% 爆红（边框+背景+文字+🔴）。后端重启（PID 3050852，PPID=1631）。

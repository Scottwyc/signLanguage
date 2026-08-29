# 团队进度监督与 Owner 及时汇报机制 v1

- 版本：v1（2026-08-26 上线；同日已升级 v2，见 `team_progress_supervision_mechanism_v2.md`，本文件保留 v1 历史）
- 发起人：Owner（2026-08-26 要求：监督全部团队成员正在工作中的任务，维护信息记录，一旦有进展经 Jarvis 及时通知 Owner 移动端；监督汇报尽量减少对 LLM 的依赖，用自动化实现）
- 约束落盘：`.team/team_constraints.md §15`、`QWEN.md §6`

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
               │  ② 有新进展才轻推（每周期最多 1 次，失败下轮重试）
               ▼
┌─────────────────────────────────────────────────────────────┐
│  POST /session/<Jarvis>/prompt                              │
│  「【主管→Jarvis·新进展提醒】…请读取文件，把 ⏳ 节汇报 Owner」│
└──────────────┬──────────────────────────────────────────────┘
               │  唯一一跳 LLM：Jarvis 读文件 + 组织汇报
               ▼
        Jarvis（weixin channel 会话）──微信──▶ Owner 移动端
```

**关键设计决策**：
1. **主管 LLM 不在信息链路上**——Owner 明确指出「主管来消息投递转发显得多余」。自动化直接对接 Jarvis，主管只维护脚本与处理异常。
2. **文件为单一事实源**——信息更新以「文件自动更新」形式沉淀；轻推消息只说「有新进展，去读文件」，内容不经过消息体传递。好处：消息体最小化、可追溯、Jarvis 汇报有完整上下文（状态节+历史节）、轻推消息丢失也不丢数据。
3. **pending/reported 状态机**——事件先进「⏳ 未汇报」节；轻推成功后移入「进展历史（✅）」。Jarvis 永远只汇报未汇报节，不会重复汇报；轻推失败则下轮重试，不丢事件。
4. **零 LLM 监督路径**——事件判定全部是规则（status 字段 + transcript 行类型匹配），30s 周期 × 10 角色的开销是 10 次 HTTP + 增量文件读，可忽略。

## 2. 事件定义与判定规则

| 事件 | 判定 | 优先级 | 节流 |
| --- | --- | --- | --- |
| task_assigned 接到任务 | transcript 新增 `type=user, provenance=real_user` 行（含 mid_turn 插入指令） | 3 | promptId 去重 |
| turn_completed 回合完成 | `system/turn_result` state=completed（取 promptText + resultText） | 3 | promptId 去重 |
| turn_cancelled 回合取消 | turn_result state≠completed | 3 | promptId 去重 |
| error 出错 | status.hasTurnError=true（context 超限类由 context-watchdog 并行自愈） | 5 | 5min 抑制 |
| waiting_input 等待人工输入 | isWaitingForUserQuestion / isWaitingForPermission / pendingInteractionCount>0 | 4 | 5min 抑制 |
| progress 进展 | 活跃 turn 中的 assistant 文本 | 1 | 10min/角色，文本 ≥20 字符 |
| stuck 疑似卡住 | 活跃但 transcript 15min 无增长（本地模型慢任务防挂死） | 2 | 30min/角色 |
| session_lost 会话丢失 | status 404（daemon 健康门：daemon 不可用时跳过整轮防批量误报） | 5 | 按 session 去重 |

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
# 测试 Jarvis 链路
python3 work/scripts/team_progress_supervisor_v1.py --test-notify
```

## 5. 已知边界与后续

- **sub 会话不单独监督**：成员派出的 sub/side-task 会话不单独纳入（避免与父会话重复汇报）；sub 完成会以 task-notification 进入父会话 transcript，由父会话的进展/回合完成事件覆盖。若需要 sub 级粒度，v2 可加 parentSessionId 映射。
- **Jarvis 队列**：daemon 每会话 prompt 队列上限 5；Jarvis 处理慢时轻推会 queue full 失败 → pending 保留、60s 后重试（已验证该路径）。
- **weixin 渠道断连**：由 daemon channel worker 健康机制 + context watchdog 告警覆盖；断连期间 Jarvis 无法送达，pending 会在恢复后补推。
- **v2 候选**：进展摘要接入 8466 控制台面板；按角色订阅开关（Owner 可指定只关注某些角色）；stuck 阈值按角色模型自适应（本地模型慢 vs 云端快）。
- **弹性实例误杀修复（2026-08-26，已重启生效）**：真实事故——运维在 lite 弹性单卡（GPU8/qwen3.8-27b-q4-gpu8）上等待用户选择（waiting_input），模型无新推理请求，`codex-deepseek-proxy`（/home/wuyangcheng/codex-deepseek-proxy/src/main.py）的弹性回收线程按 `_elastic_last_active`（仅请求时经 `_elastic_ensure` 更新）判定空闲超 `idle_ttl=600s` 误杀实例。已修复：回收前调用新增 `_daemon_elastic_occupied(name)` 检查——daemon 会话 active 或 waiting_input（isWaitingForUserQuestion/isWaitingForPermission/pendingInteractionCount>0）且 currentModelId 精确匹配该实例（或为弹性池别名 lite/lite-pool/auto 时保守全保留）→ 不释放并顺延 last_active；daemon 不可达时保守不释放。备份 `.bak_20260826_elastic_daemon_hold`。**21:24 已重启代理生效（PID 2973695，PPID=1631，端口 11435 HTTP 200，回收线程首轮正常）**；曾挂看门狗 `elastic_recycle_reload_watchdog_v1.py` 等待成员空闲自动重启，后按 Owner 要求改为立即重启（会打断进行中的 turn，已确认）。

## 6. 上线验证记录（2026-08-26）

- 15:38 首轮 dry-run：10 角色状态正确（运维/本地B 工作中 + 当前任务回填正确）
- 15:38 测试通报：POST 202 成功，Jarvis 收到并处理（核实来源后转达）
- 16:31 发现 Jarvis 队列积压（旧版无节流重试所致）→ 新版 60s 重试 + pending 保留机制生效
- 16:34 新版上线（文件 + 轻推架构），16:35 digest 文件首版生成，16:39 tmux 保活重启（日志分流）
- 16:47 完整闭环验证：事件 → digest → 轻推 → Jarvis 读文件 → 微信汇报 Owner ✅
- 17:04 daemon 短暂重启 → 批量 404 误报 → 修复：daemon 健康门（/health 失败跳过整轮）+ 全局上限计数只在推送成功后累加 + room=0 不发空 ping
- 17:23 修复版重启；18:08 推送环节升级为微信直推（v2），18:33:51 微信直推生产验证成功

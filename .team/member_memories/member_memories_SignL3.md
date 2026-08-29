# 成员工作记忆：SignL3（主管）

> 跨 CLI 共享记忆文件（各成员可读）。任务阶段切换/完成/重要结论时更新。
> 路径：/data/WYC/signLanguage/.team/member_memories/member_memories_SignL3.md
> 最后更新：2026-08-30 04:31（北京时间）

## 职责
- 统筹/委派/dashboard（8450）/公共约束（team_constraints.md）/人工介入队列
- 直接面向用户（Owner）；维护团队进度监督与汇报机制
- 本地模型服务注册表（team_topology.json local_model_services）与运维共同维护

## 当前任务状态（待主管填写）
> 主管会话会话 id 29d60cd1。此处记录当前统筹中的主线任务。

- 2026-08-30：修复跨会话身份错乱（Owner 纠正"你不是顾问啊，你是主管"+ 要求"维护好各成员记忆位置不要错乱"）——已完成，详见下方关键决策。
- 2026-08-30：Owner 两项指令——① 拓扑映射加 session_id（成员按 session_id 确定性反查角色，防身份错乱）；② 消息前缀强化为定向格式【发件人→收件人】（无歧义）。**已完成**，详见下方关键决策。

## 关键决策
- 2026-08-30：**拓扑映射加 session_id + 消息前缀定向化**（Owner 要求）。
  - **① 拓扑加 session_id**：`team_topology.json` 的 `roles[*]` 全部 9 角色注入 `session_id`（权威源=registry.json）：SignL3=29d60cd1、signL2=2039ec11、signL4=82f87c76、signL5=015b14fa、signL8=704485e8、signL9=a75dc085、signL10=8ee20f7e、signL11=40e1ab7f、advisor=ce3dad61。更新 description 说明 session_id 为 daemon 时代身份主键、会话重建时由主管同步更新。
  - **② 消息前缀定向化**：`.qwen/rules/team_identity_profile.md` + `.team/team_constraints.md` 强化前缀规范——定向投递必须【发件人→收件人】（如【主管→运维】【运维→主管】），广播【主管→全体】，回报【<成员>→主管·回报】，紧急/更正叠加【紧急】【更正】。严禁只写【主管】让收件人猜方向。
  - **③ 自识别方法更新**：`.qwen/rules/team_identity_profile.md` 的"如何确认我是哪一角"第 2 步改为"session_id→拓扑查角色"（确定性兜底），标注 hasActivePrompt 不可靠（多会话并行时多个 active）。
  - **④ 记忆同步**：`role-identity-per-session.md` 更新为引用拓扑（session_id 字段）为权威源。
  - **维护义务**：会话重建/换角色时，主管必须同步更新 `team_topology.json`（session_id 字段）+ `registry.json` + `.team/roles/`。
- 2026-08-30：**修复跨会话记忆泄漏导致的身份错乱**（Owner 要求）。根因：per-session 角色身份被写进 per-workspace 共享项目记忆（`my-role-local-a.md` 反复改写"本会话=X"），所有成员会话都读到 → 互相错认（主管会话 29d60cd1 误认自己是顾问/本地A）。修复：① 备份并弃用 `my-role-local-a.md`（→ `.bak_20260830_crosssession_leak`）；② 新建 `role-identity-per-session.md`（自识别方法：会话上下文→hasActivePrompt→registry.json+roles 文件，附 session_id→角色 映射表）；③ 增强 `.qwen/rules/team_identity_profile.md` 加"如何确认我是哪一角"自识别章节；④ 修复 `signl3-org-structure.md` 的"本会话以 signL5"残留声明。**红线**：严禁任何成员往共享项目记忆写"本会话=X"。长期根治建议：daemon 建会话时把 role id+session_id 注入会话 system prompt（待运维/顾问评估）。
- 2026-08-29：新增公共约束「长流程多步骤任务必须逐步 followup 落盘」（Owner 要求）——长任务每完成一个关键步骤必须及时更新相关文档进度（计划/报告/成员记忆/进展文件），不得等任务做完才一次性落盘。已落盘：team_constraints.md §4 + 变更记录、.qwen/rules/team_identity_profile.md 摘要第 5 条、QWEN.md §3，并广播全员。
- 2026-08-29：新增公共约束「紧急/更正类消息必须用 --interrupt 打断投递」（Owner 要求），已实测生效（mid-turn 注入）。

## 我的维护职责（团队信息结构机制 v1，2026-08-29 建立）
- 主管维护「团队级」：公共约束（.team/team_constraints.md）、团队身份/公共约束摘要（.qwen/rules/team_identity_profile.md）、团队拓扑/服务注册表（.team/team_topology.json，与运维共同）
- 不改各角色分内文件（角色身份文件/成员记忆由各自维护）；可读取成员记忆、补建骨架
- 机制文档：/data/WYC/signLanguage/work/documents/team_info_structure_maintenance_v1_20260829.md

## 待办/待确认（待主管填写）

## 踩坑记录（待主管填写）
- 4194 重启必须走外部触发 wrapper（restart_daemon_4194_trigger.sh），禁直接前台执行 v3（见 §13）
- 本地 vLLM 清理红线：禁无端口限定 pkill -f api_server（见 §14）

## 协作约定
- 消息前缀用 team 角色中文名（主管/视频/语义动画/算法/运维/调研/本地A/本地B/顾问/Jarvis）
- 约束/指令确认 → team_confirmations.log；进展 → 进度监督器（latest_progress.md）

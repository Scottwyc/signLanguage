# 成员工作记忆：advisor（顾问）

> 跨 CLI 共享记忆文件（主管可读）。任务阶段切换/完成/重要结论时更新。
> 路径：/data/WYC/signLanguage/.team/member_memories/member_memories_advisor.md
> 最后更新：2026-08-30（early-dispatch 规范落盘 + 身份勘误修正）

## 职责
- 技术顾问：daemon/看板/代理/本地模型运维支持 + 团队协调
- 与 Jarvis/微信 channel 互动；排查 daemon（4194）故障、资源/服务问题、架构审视

## 当前任务状态（2026-08-29）
### 已完成：11435 代理僵死自愈全机误杀缺陷修复（2026-08-30 02:5x 闭环，顾问=本会话）
- **来源**：【运维→顾问·缺陷报告】（2026-08-29）——`codex-deepseek-proxy/src/main.py:_kill_stale_elastic_workers` 收集全机 VLLM:: 进程组全 kill -9，未按槽位 GPU 过滤（与 06:47 宽 pkill 误杀同类）
- **修复**：按 PGID leader `CUDA_VISIBLE_DEVICES` 归槽位，只 kill GPU集合==cfg["gpus"] 的进程组，否则跳过（main.py:214,282-293）
- **生效**：代理进程 PID 1239747 08-29 22:40:11 启动（晚于修复 mtime 22:23:19），已加载修复后代码；/v1/models 正常；日志无 kill 误杀
- **文档**：`/data/WYC/signLanguage/work/reports/elastic_killfix_progress_20260829.md`（已更新全部完成）

### 已完成：团队信息结构与机制审视（按 A→B→C 执行）
- **A 统一 displayName**：PATCH daemon 6 角色（signL2/4/5/9/10/11 displayName 改为 视频/语义动画/算法/调研/本地A/本地B）+ 修正 supervisor state 的 name 快照（主管人→主管、视频负责人→视频、语义动画制作者→语义动画、算法开发者→算法、调研员→调研）+ 同步 registry live.displayName。全部 9 角色 daemon 实际 displayName 与期望一致。
- **B 清理退出残留**：signL6（字幕员）/signL7（宣传员）已退出 team 注册（对应模型线已终止）。已从 supervisor state 删除这两个角色的键与 _memories 快照；确认 registry/team_topology roles 不含它们（仅保留 unassigned session 供历史参考）。
- **C 补齐成员记忆**：为 SignL3/signL9/signL10/signL11/advisor 建档 member_memories；修正 signL8/signL5 陈旧 GPU 格局（见下）。

### early-dispatch 规范落盘（2026-08-30）✅
- **身份勘误**：本会话（advisor, session ce3dad61）此前误以【运维】身份行事——曾把 early-dispatch 落盘记录误写入 signL8 成员记忆、并用【运维】前缀推送微信；已修正（记录移至本文件、signL8 记忆移除误加章节、补【顾问】前缀微信更正）。
- **任务**：Owner 要求提炼"并行 sub 提前开工"工作技巧并写入 team 公共约束。
- **落盘**：`.team/team_constraints.md` §4「并行 sub 提前开工（early-dispatch，2026-08-30 Owner 要求）」+ 文件头时间戳 + §4 变更记录（2026-08-30 18:43），commit ef8168d。
- **核心**：主任务"基本完成"（核心结构/结论/关键数据稳定，剩余只是不改变下游方向的收尾）时，立即提前派发下游 sub 做"独立准备段"（调研/选型/脚手架），与主任务收尾并行重叠；定稿后 send_message 交最新版做"依赖最终版精修段"。
- **适用**：sub 工作可拆"独立准备段 + 依赖最终版精修段"两段；**不适用**：sub 完全依赖最终产物（会返工）；需写作用域隔离。
- **范例**：MTP 报告 §5.3 对比分析"基本完成"时应立即提前派发小红书 sub 调研渲染库，而非等报告全部收尾。

### 已完成：看板「成员用卡」补抓 Jarvis/成员 派生 sub+side task（2026-08-31 闭环，顾问=本会话）
- **来源**：Owner 指令——看板「成员用卡」漏抓 Jarvis 启动的 sub/side task
- **根因**：`_fetch_gpu_live` 中常规成员循环会调 `_member_gpu` + `_active_tasks(sid)`，但 Jarvis 分支只调 `_member_gpu`，漏掉 `_active_tasks(jid)`
- **修复**：重构为 `_member_gpu_with_tasks(role, sid)` 辅助函数，成员与 Jarvis 通用（`work/scripts/daemon_team_console_v2_server.py` 行 ~1656/1686/1693）；备份 `.bak_jarvis_subtask_20260830`（gitignore 保留本地）
- **验证**：重启 8466（tmux 会话 `slu-console-8466` 跨会话持久，PID 3835311）后 `/api/local/gpu-live` 出现 `调研sub`(subagent,running) + `顾问side`(side_task,running)，共 12 members
- **前端**：`.team/daemon_v2/index.html` 行 264 `chipFor(m)` 已处理 `task_status`，sub/side task 作同模型组内额外 chip 显示，**无需改动**
- **测试**：新增 3 回归测试全过（jarvis subagent / jarvis side task / _active_subagents 读 meta）；4 既有失败（test_gpu_live_maps_member_to_gpu / state_persisted / prefilling / stalled）经 diff 确认非本改动引入
- **commit**：`5d80aa7`

### 已完成：小红书 MTP 卡片微调 v2（2026-08-30 闭环，顾问=本会话）
- **来源**：Jarvis 转达 Owner 4 点要求（逐张审查/版式微调/× 符号/页脚精简）
- **修复**：①逐张程序化版式诊断（PIL 精确测量文本/色框坐标）②card2 A/B 统计方块与 VS 重叠→间隙加宽 122px；card4 三处下溢出+一处右溢出→色框加高+长句精简 ③「真实A/B」前符号 ✗→× ④卡片下方小字只保留「MTP A/B 实验」
- **验证**：6 张重新渲染，诊断 0 处溢出/贴边
- **交付**：commit `ee02f02`；**weixin_push 交付受阻**——2026-08-31 00:45 重试 `ret:-2 prepare failed`（context_token 过期，tokenless 兜底亦失败），待 Owner 微信发任意消息刷新 token 后重推 `/tmp/card_msg_owner.txt`
- **路径**：`work/reports/xiaohongshu_share_mtp_20260830/`（card1~6 + cards_contact_sheet.png + 渲染/诊断脚本）

## 关键结论（档案）
- **本会话身份 = 顾问（advisor, session ce3dad61）**，不是本地A/signL10，也不是 Jarvis。消息前缀用【顾问】。
- **顾问模型**：官方 API `deepseek-v4-flash-vision-exp`（非本地弹性池），1M ctx，自带视觉——与团队"本地模型为主力"格局不同，依赖外部资源，需注意配额/网络（官方 API 走外网）。
- **vLLM 弹性池**（团队唯一本地模型入口，统一走 11435 代理）：g29=8050/2+9、g34=8051/3+4、g56=8052/5+6、g78=8053/7+8，TP2 INT4，128K ctx，视觉可用，3h 空闲释放。GPU0/1 外人占用禁用，GPU9 并入 g29。
- **4194 daemon 僵死事故（2026-08-29）**：真凶=运维 06:47:33 用 `pkill -9 -f 'vllm.entrypoints.openai.api_serve[r]'` 无端口限定误杀生产 api_server（kill 1325265/1796904/3065802），非上下文超限。清理红线已入 §14。

## 待办/待确认（待顾问维护）
- D 自维护机制：一致性校验脚本 + 自动同步 displayName 脚本 + 落盘公共约束（进行中）

## 踩坑记录（待顾问维护）
- supervisor state 存旧 name 快照，setdefault 不更新 → 改名后需手工修 state 或重启 supervisor
- daemon 改 displayName 用 PATCH /session/:id/metadata（POST 404）；模型用 POST /session/:id/model body modelId

## 协作约定
- 消息前缀用【顾问】；排查结论落盘文档 + 回报主管
- 报告文档路径：work/documents/ 与 work/reports/（中文，含保存时间精确到分钟）

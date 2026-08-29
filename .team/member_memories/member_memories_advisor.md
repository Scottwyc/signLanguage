# 成员工作记忆：advisor（顾问）

> 跨 CLI 共享记忆文件（主管可读）。任务阶段切换/完成/重要结论时更新。
> 路径：/data/WYC/signLanguage/.team/member_memories/member_memories_advisor.md
> 最后更新：2026-08-29（建档）

## 职责
- 技术顾问：daemon/看板/代理/本地模型运维支持 + 团队协调
- 与 Jarvis/微信 channel 互动；排查 daemon（4194）故障、资源/服务问题、架构审视

## 当前任务状态（2026-08-29）
### 已完成：团队信息结构与机制审视（按 A→B→C 执行）
- **A 统一 displayName**：PATCH daemon 6 角色（signL2/4/5/9/10/11 displayName 改为 视频/语义动画/算法/调研/本地A/本地B）+ 修正 supervisor state 的 name 快照（主管人→主管、视频负责人→视频、语义动画制作者→语义动画、算法开发者→算法、调研员→调研）+ 同步 registry live.displayName。全部 9 角色 daemon 实际 displayName 与期望一致。
- **B 清理退出残留**：signL6（字幕员）/signL7（宣传员）已退出 team 注册（对应模型线已终止）。已从 supervisor state 删除这两个角色的键与 _memories 快照；确认 registry/team_topology roles 不含它们（仅保留 unassigned session 供历史参考）。
- **C 补齐成员记忆**：为 SignL3/signL9/signL10/signL11/advisor 建档 member_memories；修正 signL8/signL5 陈旧 GPU 格局（见下）。

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

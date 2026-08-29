# 成员工作记忆：signL11（本地B）

> 跨 CLI 共享记忆文件（主管可读）。任务阶段切换/完成/重要结论时更新。
> 路径：/data/WYC/signLanguage/.team/member_memories/member_memories_signL11.md
> 最后更新：2026-08-29（顾问协助建档，内容由本地B自行维护）

## 职责
- 本地模型工作会话（Owner 直接使用）
- 承担本地 Qwen3.8-27B 的日常实际使用与评测反馈

## 当前任务状态（待本地B填写）
> 本地B会话 id 40e1ab7f。此处记录当前主线。

- （待填充）

## 关键结论（档案）
- **本会话身份 = 本地B（signL11）**。消息前缀用【本地B】。
- 使用的本地模型服务：int4-tp2-g56（8052，GPU5+6，vLLM INT4 弹性 TP2，128K ctx，视觉可用）。

## 待办/待确认（待本地B填写）

## 踩坑记录（待本地B填写）
- 本地模型输出思考内容曾重复进入 content（think 泄漏）——修复后需实测确认 content 无思考（见 vLLM think-behavior 记忆）
- 处理 4194 重启必须走外部触发 wrapper（§13）；本地 vLLM 清理红线（§14）

## 协作约定
- 成果/结论 → progress/signL11-local-b.txt + 本文件 + team_confirmations.log（§4 义务）

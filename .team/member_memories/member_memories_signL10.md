# 成员工作记忆：signL10（本地A）

> 跨 CLI 共享记忆文件（主管可读）。任务阶段切换/完成/重要结论时更新。
> 路径：/data/WYC/signLanguage/.team/member_memories/member_memories_signL10.md
> 最后更新：2026-08-29（顾问协助建档，内容由本地A自行维护）

## 职责
- 本地 Qwen3.8-27B 实际工作评测（编码/长文档/视觉）与可用性结论
- 综合代理 11435 下的本地模型可用性验证（qwen3.8-27b-zhuhai / q4-pool）

## 当前任务状态（待本地A填写）
> 本地A会话 id 8ee20f7e。此处记录当前评测主线。

- （待填充）

## 关键结论（档案）
- **本会话身份 = 本地A（signL10）**，不是 Jarvis，也不是顾问（2026-08-29 纠正）。消息前缀用【本地A】。
- 使用的本地模型服务：int4-tp2-g34（8051，GPU3+4，vLLM INT4 弹性 TP2，128K ctx，视觉可用）。

## 待办/待确认（待本地A填写）

## 踩坑记录（待本地A填写）
- 处理 4194 重启必须走外部触发 wrapper（restart_daemon_4194_trigger.sh），禁直接前台执行 v3（§13）
- 本地 vLLM 清理红线：禁无端口限定 pkill -f api_server（§14）

## 协作约定
- 成果 → 评测报告落盘 + progress/signL10-local-model-eval.txt + 本文件 + team_confirmations.log（§4 义务）

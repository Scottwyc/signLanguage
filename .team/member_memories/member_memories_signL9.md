# 成员工作记忆：signL9（调研）

> 跨 CLI 共享记忆文件（主管可读）。任务阶段切换/完成/重要结论时更新。
> 路径：/data/WYC/signLanguage/.team/member_memories/member_memories_signL9.md
> 最后更新：2026-08-30 04:24（调研自行维护）

## 职责
- 网络调研/材料搜集/问题问答/来源核验
- 产出调研报告落盘 work/documents/ 与 work/reports/

## 当前任务状态
> 调研会话 id a75dc085。此处记录当前调研主线。

- **主线任务已闭环（2026-08-28）**：Qwen3.8-Flash-Next 性能 + 本地部署可行性调研，并汇总之前全部调研（GLM-5.3-Flash / dsv4flash / Qwen3.5-122B-A10B / Qwen3.8-Flash-Next / Qwen3.8-Flash）产出综合分析报告，已回报主管验收（message_id 2a619c57）。
  - 报告：work/documents/zhuhai_model_research/zhuhai_model_research_comprehensive_20260828_v1.md（16146 bytes，08-28 09:58，已核验完好）
- **daemon 重启后状态核查（2026-08-30 02:28:25 重启）**：本会话存活、helper 正常、交付物报告完好、无被中断的 sub/后台任务；已向主管发送重启后状态核查闭环报告（message_id aace8c9c，08-30 04:24 发送，state=sent）。
- **身份确认（按新 per-session 方法）**：本会话 = 调研（signL9，session a75dc085），依据 registry 权威映射 + 会话上下文 + 主线任务；未往共享项目记忆写"本会话=X"。

## 关键调研结论（档案，供团队复用）
- **论文投稿（2026-08-18）**：arXiv 主分类建议 cs.CV；近期最现实目标 WACV 2027 Round2；中期 CVPR 2027 / ICME 2027；无障碍 ASSETS 2027；期刊 ESWA/CVIU/TMM/PR/TPAMI。卖点排序：①现场 holdout 泛化评估协议 ②数据增强鲁棒性(坐姿) ③级联打分模型。
  - 报告：work/documents/sign_scoring_paper_venue_research_20260818.md
- **Qwen3.8 性能（2026-08-26）**：27B dense 视觉语言 256K 原生 / 1M YaRN；Max 2.4T-A95B MoE 纯文本强制 think。官方分多项超 Opus4.6；自量化 W8A8/INT4 已判死，坚持官方权重。
  - 报告：work/documents/qwen38_performance_benchmark_report_v1_20260826.md
- **DeepSeek-V4-Flash-0731 本地部署可行性（2026-08-26）**：304B / 13B 激活 MoE，官方 FP8+FP4=167GB 主方案；可部署但受 zhuhai 241GB 显存与 /home 189G 限制；最终整线已终止（2026-08-27 清空）。
  - 报告：work/documents/dsv4flash0731_zhuhai_deploy_feasibility_v1_20260826.md
- **Wan2.5 调研（2026-08-26）**：未开源；zhuhai 维持 Wan2.2-Animate-14B；最大冗余可回收=t2v bf16 108G。
  - 报告：work/documents/wan25_research_zhuhai_wan22_audit_v1_20260826.md
- **GSE2026（2026-08-20）**：2026 全球智慧教育大会北师大主办；切入点为下届案例征集/2027 投稿/北师大特教学院合作。
  - 报告：work/documents/gse2026_research/gse2026_research_20260819.md

## 待办/待确认
- **等主管决策**：是否启动 llama.cpp 重建以实测 Qwen3.8-Flash-Next（A30 SM86 稳定性 + 8 卡 decode 吞吐）。若主管指示启动，下一步：从含 PR #27742 的新 master 重建 build-nccl（CUDA 12.8 + NCCL 8 卡）→ 下载 unsloth UD-Q4_K_XL（111GB）→ llama-server 8 卡启动实测。当前未擅自开始。

## 踩坑记录
- **本机 llama.cpp 无 qwen4exp**：zhuhai 三个 llama.cpp 源码树（8-25 / 20260826 / 0.3.0）均无 Qwen4ExpForConditionalGeneration 架构，本地 build-nccl 当前无法运行 Flash-Next；上游 PR #27742 已合入 master（commit 6c84c7d5d），需从新 master 重建。
- **deploy_solution_v2 乐观推断被证伪**：之前报告推断 Flash-Next 可本地跑，实测源码树无该架构，已修正结论。
- **SSH git 命令被 shell guard 拦截**：改用文件 mtime（ls -lt）判断源码快照日期。

## 协作约定
- 成果 → 调研报告落盘 + team_confirmations.log（§4 义务）；仅出结论不代跑实测（实测由运维/执行成员做）

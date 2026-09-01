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

## 2026-09-01 智能路由 / 弹性池关键诊断与修复（顾问参与，重要）
- **事故**：16:30 用卡2+9(35b) 出现 `Model stream ended without a finish reason. Connection error.`，打断本地服务。
- **根因（确诊）**：`_kill_stale_elastic_workers("qwen3.8-27b-int4-tp2-g29")` **只按 GPU 对 {2,9} 匹配 VLLM 进程组**，无法区分同卡组不同模型——g29 卡组 27b(8050,已释放) 与 35b(8070,运行) 共享 GPU2,9，把 35b(PGID 1021461) 误判为"27b 僵死"、反复命中待清、试图 kill -9。这是**按 GPU 对匹配的跨模型误杀 bug**。
- **修复**：`_kill_stale_elastic_workers` 判定处，GPU 对匹配基础上**增加 cmdline `--port == 本槽位端口` 校验**（`re.search(rf"--port[ =]{port}(?!\d)")`）。备份 `main.py.bak_portcheck_20260901`；单测 6/6 PASS；已重启 11435 生效。
- **联动修复**：上游 vLLM 断流 `http.client.IncompleteRead` 时不补 finish_reason → 客户端报错。已给 `_handle_local_backend` 补 finish_reason 防护 4 处（含 `except IncompleteRead` 断流补发）。备份 `main.py.bak_finish_patch_20260901`。
- **知识沉淀**：
  - **端口是区分槽位/实例最可靠字段**（每槽位独占端口；同 GPU 对可跑不同模型）。任何"按 GPU 对匹配进程"的清理逻辑必须加 `--port` 校验。
  - **max_tokens=输出上限，输入上限=ctx−max_tokens**；thinking 计入 max_tokens（reasoning.high 会先耗尽预算再出回答，是"回答一半截断"主因）。
  - 35b 窗口 225280；`samplingParams.max_tokens=32768`（2026-09-01 设，位置在 samplingParams 下）。
- **落盘**：智能路由主题文档第一部分 `work/documents/intelligent_router/intelligent_router_v1_20260901.md`；代理变更记录 `~/.qwen/settings_fix_gpt_models_20260731.md`；team_constraints §3 已补"僵死自愈必须含端口校验"红线。

## 2026-09-01 本地模型"假已下线"看板 bug + 统一代理拉起规范（重要）
- **事故**：8466 看板 local_services 部分在线的 27b-g78/g34 显示"已下线"，疑看板 bug。
- **根因（确诊）**：8096 监控 `infer_model(日志名)` 推 model_id，遇 **logtag 命名漂移**——当前 27b 实例手动启动用 `vllm_g78.log`（logtag g78），STATE_FILE 残留旧别名 `int4-tp2-g78`（log=vllm_int4-tp2-g78.log）；同一端口 8053 两个 model_id，旧别名无活跃进程 → alive=False → 看板"假已下线"。
- **修复**：① 8096 `refresh_models` 用 **port 兜底匹配**翻 alive（`str()` 统一比较——持久化 state["port"] 是字符串 '8053'，find_active_logs 的 port 可能 int）② 清 STATE_FILE 旧别名（删 int4-tp2-g78/g34）③ 重启 8096。备份：`llm_monitor_generic_v2.py.bak_alivefix_20260901`、`llm_monitor_state.json.bak_clean_20260901`。验证 alive=False=0，看板恢复。
- **重要规范**：**本地模型实例一律用综合代理(11435) 拉起**——代理 `_elastic_vllm_cfg` 用标准 logtag（main.py 177-180 行：27b-g78→`int4-tp2-g78`），保证日志名=标准 model_id，8096/看板正确识别。**手动/裸调另起实例会让 logtag 漂移**（g78 vs int4-tp2-g78）→ 8096 误判已下线。维护/重启实例一律走代理（`_elastic_ensure`），勿绕开；测试/临时实例也勿裸调。

## 2026-09-01 本地模型视觉能力实测对比（顾问免前端直测，重要）
- **方法**：经 `127.0.0.1:11435/v1/chat/completions` 直打 OpenAI 兼容 API（**绕过 Qwen Code 前端**），同题同图、temp=0，4 题（颜色/OCR/位置、计数+空间、柱状图读值、中文 OCR）。
- **被测**：35b=`qwen3.6-35b-a3b-tp2-g29`(卡2+9/8070,运行中)；27b=`qwen3.8-27b-int4-tp2-g34`(卡3+4/8051,空闲)。
- **结论**：
  - **两者都有原生视觉**（Qwen3.x GDN 视觉塔），实测图像 token 确实进入（带图 prompt≈250-330 vs 纯文字 ~40），**非 visionBridge 桥接**。
  - 基础能力（颜色/位置/OCR/计数/空间）**强且持平**：fig1/2/4 双模型全对；无图时都诚实拒答。
  - **分水岭=图表/精细数值读取（fig3 柱状图，真值 A150/B300/C220/D380）**：**Qwen3.6-35B-A3B(35b) 完全宕机**（给足 800 token 仍 0 输出）；**Qwen3.8-27B(27b) 有结构化推理但数值上偏**（读成 A≈200/B≈400/C≈300/D>400）。→ 精确读图**两者都不可靠**，27b 至少能出趋势+排序，35b 直接无产出。
  - **风格**：35b 输出直接简洁；27b 需推理的视觉题先长 think 草稿再答 → 正文易溢出截断（与文本"思考超长"同源）。
  - **⚠️ Qwen Code 前端注意**：settings.json 里 **Qwen3.6-35B-A3B(35b) 注释"工具调用可用"、未标"视觉可用"**；Qwen3.8-27B(27b) 标了"视觉可用"。→ 前端对 35b **可能不默认启用本地图像 pipeline（或走 visionBridge）**；本次是绕过前端才测到真实多模态。**成员用 35b 看图前需先确认前端是否把它当视觉模型。**
- **建议分工**：看真实图/图表→优先 Qwen3.8-27B（读数需人工核对）；精确考据→联网核实 / deepseek-v4-flash-vision-exp（官方 API, 1M ctx）；视觉作为 agentic 一环→Qwen3.8-27B 或官方 VL。
- **文档**：`work/documents/intelligent_router/local_vision_capacity_cmp_v1_20260901.md`；`intelligent_router_v1_20260901.md` 新增 §7「本地模型视觉能力实测比较」（§8 引用/关联）。
- **⚠️ 通用规则（Owner 2026-09-01 要求，强制）**：**性能实测/模型对比报告必须写清每个被测模型的完整规格**（品牌型号+架构+量化+model_id+槽位/端口/状态），**禁止只写"27b/35b"简写**。已写入 `team_constraints.md §4`「性能实测/对比必须写清模型型号」+ 项目反馈记忆 `report-must-state-model-full-spec`。凡后续做任何模型实测/对比（视觉/速度/tool-call/长文本等）都要遵守。

## 2026-09-01 死循环监督 watchdog（顾问实现，重要）
- **背景（Owner 要求）**：本地 AWQ4 量化的 Qwen3.6-35B-A3B（35b）Moe 出现"思考循环"——模型在思考/输出陷入无限重复，耗 token/上下文却不产出有效结果，会话像卡死。需监督成员输出，发现死循环及时打断，按 ctx 余量决定是否 /compress，再补发「继续完成」。
- **实现**：新建 `work/scripts/daemon_loop_watchdog_v1.py`（常驻进程，setsid 保活，PID 3395761）。复用 `daemon_auth_v1` + context watchdog 的 HTTP 模式。
- **关键发现**：
  - daemon SSE 事件流**不吐 token 增量**（只有 `git_status_changed` 等离散事件）→ 死循环**不能靠事件流**，改读 **transcript 尾部**（`chats/<sid>.jsonl`）提取 model 消息正文（`message.role=='model'`、文本在 `message.parts[].text`，Qwen Code 不落盘 thinking）。
  - `context-usage` 端点可精确拿 `totalTokens/contextWindowSize` → 算余量占比可靠。
  - `POST /session/:id/cancel`（204）可打断；`mid-turn-message` 只在有 active turn 时接受（`accepted:false` 是空闲态正常）。
- **检测算法（以最后一条为中心）**：连续 3 条 model 文本，最后一条（≥120 字）与其余每条相似度 ≥0.90 判死循环。测试全过（完全重复/逐条累积→True；正常不同/短文本→False）。真实会话 model 文本中位长度 590+，120 阈值合理。
- **恢复流程**：`cancel` 打断 → 查 `context-usage`，余量 <20% 先 `/compress`（等完成）再发「继续完成」，否则直接发「继续完成」。
- **限流**：同会话 120s 冷却；1h 触发 3 次转人工介入队列。
- **落盘**：`team_constraints.md §4`「死循环自动监督机制」+ §16.3 工具目录登记；状态 `.team/daemon_v1/loop_watchdog_state.json` + `loop_watchdog.log`；告警写 `team_messages.log`。

## 2026-09-01 本地引擎思考强度控制调研（重要，回答 Owner「本地能否像官方一样控制 effort」）
- **背景**：35b（Qwen3.6-35B-A3B-AWQ）思考过长→截断/1 turn 停；Owner 问「官方模型能 /effort，我们本地 vLLM/llama.cpp 难道不能吗」。
- **核心区分（baseUrl 决定引擎）**：官方 qwen3.6-plus/qwen-max → `dashscope.aliyuncs.com`（阿里云，供应商原生实现 effort ✅）；本地 27b/35b → `127.0.0.1:11435`（我们 zhuhai vLLM 0.19 ❌）。
- **vLLM 0.19 对 Qwen3 effort 无效**（源码+实测确认）：
  - `--reasoning-parser qwen3` 只做输出解析（拆 `<think>`/`</think>`），**不控思考长度**；无 `--reasoning-effort` 参数。
  - 协议层 `reasoning_effort`（protocol.py:182）**仅对 Harmony/GPT-OSS 模型生效**（harmony_utils 经系统提示词），**对 Qwen3 无作用**。
  - 实测 27b 中性/medium/high completion=81/97/80（随机级）、35b 波动<8% → 均无效。
- **llama.cpp 0.3.0 完整支持 reasoning_effort**（实测有效）：
  - CLI `--reasoning-effort`（minimal/low/medium/high/xhigh/max，arg.cpp:3669）+ **请求级 `inp["reasoning_effort"]`**（chat.cpp:970）+ 模板变量 `reasoning_effort`/`reasoning_strength`（caps.cpp:29）。
  - Qwen3.8-27B 模板**消费**该变量，但机制是**把 effort 翻译成 system 提示词推理指令**（`reasoning_instructions`：xhigh=多想、low=少想），`high` 归一成 `xhigh`（`resolved_reasoning_effort`）。**非硬性 token 限制**，效果依赖模型遵循度。
  - 实测（Qwen3.8-27B-UD-Q4_K_M 单卡 GPU5，高难度逻辑题）：low→reasoning 7533 / medium→5970 / high→3525（**方向反**：low 反而最长；软引导不稳定）。
- **硬性限制思考长度的办法**：
  - **vLLM**：`thinking_token_budget`（logits processor，builtin.py:352-498）解码时计数 `<think>` 达预算强制 `</think>`；**需 `--reasoning-config '{"reasoning_start_str":"<think>","reasoning_end_str":"</think>"}'` 解锁**；字段能从 11435 透传（发 budget=0 返回门控报错）。Owner 决定暂不落地（需改 zhuhai 脚本+重启）。
  - **llama.cpp**：`enable_thinking=False` 彻底关思考（硬开关）。
- **文档**：`work/documents/intelligent_router/local_reasoning_effort_control_v1_20260901.md`（完整调研：背景/引擎区分/源码证据/实测数据/结论/落地步骤）。
- **结论**：本地引擎**能**控制思考强度，但选对引擎/参数——llama.cpp 走模板软引导（支持 effort，但效度依赖遵循度）、vLLM 对 Qwen3 effort 无效、硬限制要用 thinking_token_budget/enable_thinking。

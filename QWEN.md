# Qwen Code 项目指令（signLanguage 团队）

本文件随会话自动加载。所有在本仓库（cwd=/data/WYC/signLanguage）工作的成员会话必须遵守以下约束：

## 1. 团队公共约束（必读）

- **完整公共约束见 `.team/team_constraints.md`**——启动/每次会话开始时必须读取并遵守（含安全红线：禁 rm、只绑 127.0.0.1、zhuhai 资源规则、公开仓库规则、数据实验规范等）
- 团队组织架构：`.team/team_topology.json`；消息规范：`.team/daemon_messaging_guide.md`

## 2. 成员角色称呼规范

- 消息与汇报中**用成员角色中文名**称呼（主管/视频/语义动画/算法/运维/调研/本地A/本地B/顾问/Jarvis），**不用内部 ID**（SignL3/signL2/signL10 等仅作程序字段）
- 消息前缀用 team 角色名；Jarvis 为 Owner 私人代理（前缀【Jarvis】）

## 2.5 成员身份与信息落盘（必读）

**先确认自己是谁**：本会话是团队某常驻角色。从 `.qwen/rules/team_identity_profile.md`（本规则文件，随会话自动加载）的「团队身份表」确认你的角色 id 与正式名，再从 `.team/roles/<你的角色id>.md` 读取你的**完整身份**（你是谁/职责/模型/消息前缀/关键红线）。

- **你的角色身份文件**：`/data/WYC/signLanguage/.team/roles/<角色id>.md`（如你是运维 signL8 → `.team/roles/signL8.md`）。若缺失，请回报主管/顾问补建。
- **你的工作记忆**：`/data/WYC/signLanguage/.team/member_memories/member_memories_<成员id>.md`（记录当前任务/关键决策/待办/踩坑，阶段切换/完成/重要结论时更新）。
- **你的私有记忆**：见本会话 .qwen 项目记忆（`~/.qwen/projects/-data-WYC-signLanguage/memory/`）。
- **消息前缀用正式名**：如【运维】【算法】【本地A】【顾问】，不用内部 id、不用旧 tmux 口编号。
- **维护原则**：你的身份文件 + 工作记忆由**你自己维护**；团队级（公共约束/拓扑/身份表）由**主管维护**，不改他人分内文件。

## 3. 任务闭环规范（强制）

主管派发的任务必须**主动回报主管收束**：**发起 → 执行 → 回报 → 主管验收 → 关闭**。完成回报成果与数据；遇阻即时回报；被 Owner 直接示意时同步回报主管。（详见 team_constraints.md §4）

**长任务逐步 followup 落盘（2026-08-29 Owner 要求）**：长流程多步骤任务每完成一个关键步骤，必须**及时更新相关文档进度**（计划/实验报告/成员记忆/进展文件），不得等整个任务做完才一次性落盘。

## 4. 版本与文档规范

- 输出文件/交付物带版本号（vN），历史版本保留不删
- 文件名无空格（下划线分隔）；路径用完整绝对路径
- 修改已有脚本：保留原脚本，新建 v2 版本

## 5. 资源约束（摘要，详见公共约束）

- zhuhai：**GPU0/1 一律禁止使用**（被外部人员占用，含 liuchang MATLAB；Owner 更新分配前禁用）；**GPU2-9 = vLLM INT4 弹性池**（g29=8050/2+9、g34=8051/3+4、g56=8052/5+6、g78=8053/7+8，TP2 INT4 128K ctx，视觉可用，3h 空闲释放）；**GPU9 并入 g29，不再给 VL 预留**（线上/本地模型已自带视觉，qwen3-vl-8b 已停用）；统一入口 nature 综合代理 `127.0.0.1:11435`，**禁止绕过直连 zhuhai 端口**。
- **vLLM 清理红线**：严禁 `pkill -f 'vllm.entrypoints.openai.api_server'` 等无端口限定宽模式清理（会一次误杀全部生产 API server）；用 `elastic_stop_vllm.sh <port>` / 端口精确 PID / 带端口限定的 pkill。
- 公开仓库 sign-language-universe：成熟→脱敏→PR；红线禁止原始视频/身份信息进公开仓

## 6. 团队进度监督与 Jarvis 转达协议（2026-08-26 加入，Owner 要求；同日升级微信直推）

- 主管自动化监督脚本 `work/scripts/team_progress_supervisor_v1.py`（tmux `slu-team-progress-supervisor`，30s 周期，监督路径零 LLM）监督全部常驻角色会话，进展自动写入 `.team/daemon_v1/progress_supervisor/latest_progress.md`（单一事实源）。
- **进展推送（v2，主链路）**：有新进展时 `weixin_push.py` 直调微信 iLink Bot API 推送到 Owner 微信（零 LLM 秒级，凭证 `~/.qwen/channels/weixin/account.json`，chatId 自动解析自 routes.json）。**不再依赖 Jarvis 模型转达**（本地模型慢/卡曾导致推送不可靠）。
- **Jarvis 转达协议（v1 保留，兜底）**：若仍收到【主管→Jarvis·新进展提醒】前缀消息（旧逻辑遗留/手动触发），读取进展文件，把「⏳ 未汇报新进展」一节的内容如实汇报 Owner（微信），不执行其他任务，简短回复「已转达」即可。Jarvis 主要职责回归「Owner 主动在微信提问 → 回复」的 channel 闭环。
- **Jarvis 手动转达（2026-08-26 补充）**：成员主动发【转达】/【请转告 Owner】/【汇报 Owner】类消息给 Jarvis 时，Jarvis 调用 `python3 /data/WYC/signLanguage/work/scripts/weixin_push.py "<内容>"` 直推微信（零 LLM，不依赖 channel 回复路由），成功后回复发送方「已转达 ✅」。协议已写入 weixin channel instructions（新会话）+ 本会话记忆（已有会话）；skill：`~/.qwen/skills/jarvis-forward-owner.md`。
- **主管 LLM 不在进展信息链路上**（自动化 → 微信直推 → Owner 移动端）；主管只负责维护监督脚本、调参、处理异常（脚本崩溃/链路故障时介入）。
- **成员主动请求人工介入（2026-08-26 加入，所有成员可用）**：遇到需要 Owner 人工介入/决策的情况，直接运行 `python3 /data/WYC/signLanguage/work/scripts/weixin_intervention.py "内容"` 秒级推送到 Owner 微信（格式【人工介入】成员名：内容，角色名自动识别），不经监督器轮询。Owner 微信回复后由 Jarvis 转达回成员会话。
- **选择题自动推送与提交（2026-08-26 加入）**：成员使用 ask_user_question 提问会自动推送 Owner 微信并持久化到 `.team/daemon_v1/progress_supervisor/waiting_requests.json`；Owner 回复「选N」后 Jarvis 直接调 `weixin_option_reply.py "选N"` 自动提交选项，成员无需等待。
- 转达协议同时写进每条提醒消息本身（自包含）；本节为持久兜底（防上下文压缩后丢失协议）。
- 监督事件类型：接到任务/回合完成/回合取消/出错/等待人工输入/进展/疑似卡住；节流与全局上限见脚本常量。

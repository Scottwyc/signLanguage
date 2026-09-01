# 团队公共约束（signLanguage 手语打分项目）

> 维护者：主管（SignL3）｜所有常驻 agent（视频/语义动画/算法/运维/调研/本地A/本地B/顾问）与临时 sub 必须遵守
> 最后更新时间：2026-09-01 19:50（北京时间）
> 变更：经用户确认后由主管更新，变更记录见文末

## 1. 安全约束（最高优先级）

- **禁用删除命令**：`rm` / `rmdir` / `rm -rf` 一律禁止（清理需主管评估后执行）
- **本地服务只绑 127.0.0.1**：http.server / serve_nocache 等严禁 0.0.0.0 暴露
- **不暴露敏感信息**：API Key / 密码 / token 不写入日志或公开仓库（魔塔推送用 oauth2 + Access Token，存 .env 文件）
- **数据隐私**：landmark 骨架数据匿名（无原始视频帧可外传）；公开仓库不含真实人脸视频

## 2. 版本与文件规范

- **改进脚本保留原版本**：新改动建新版本（v1→v2→v3），原脚本不删除（可回滚对比）
- **备份用 `cp`**：修改稳定脚本前备份（如 `xxx.py.bak_<date>_<feature>`）
- **完整绝对路径**：所有工具调用/文档用绝对路径（如 `/data/WYC/signLanguage/work/...`），不用 `...` 截断
- **输出文件无空格**：文件名用下划线（如 `task_report_20260810.md`）
- **数据文件放项目目录**：team 管理数据放 `/data/WYC/signLanguage/.team/`；生成数据放 `/data/WYC/signLanguage/work/generated/`
- **PR 提交更新版本徽标（2026-08-15 Owner 要求，强制）**：每次向开源仓（sign-language-universe）提交 PR，必须把 `apps/web/index.html` 左下角 build-badge 的 PR 编号更新为当前最新 PR 号，方便用户区分版本。PR 分支操作前先 `git branch --show-current` 确认分支（避免误在 main 提交）；误提交 main 时用 `reset --soft origin/main` 撤销 + cherry-pick 到正确分支。

## 3. zhuhai 服务器资源使用规则（GPU/CPU，必须遵守）

- **所有本地模型部署在 zhuhai，不在本机（2026-08-30 Owner 确认）**：团队所有本地模型服务（vLLM INT4 弹性池 g29/g34/g56/g78、llama.cpp 等）均部署在 **zhuhai 服务器**上，**不在 nature 本机**。后续涉及本地模型部署/调研/换卡/速率测试，一律按 zhuhai 上的卡来理解（GPU1 禁用，GPU0 单卡服务，GPU2-9 弹性池）。nature 本机无 GPU 推理能力，仅作为 Qwen Code 主进程 + 代理 + 工作目录。
- **外网下载规范：zhuhai 无外网，须经 nature 中转（2026-08-31 Owner 要求，强制）**：**zhuhai 环境无外网**，**nature 本机可直接访问外网**（实测 2026-08-31：github/huggingface/pypi/npm/google 等直连均通；api.openai.com 直连返回 401 认证错误=连接通，非被墙）。因此**若在 zhuhai 上需要下载外网资源**（模型权重/gguf/onnx、github 仓库、pip/conda 包、外部数据等），**不能直接在 zhuhai 上做**——必须先**在 nature 上下载**（直连即可，无需代理），再通过 **scp/rsync 推送到 zhuhai**（`scp -P 7712 <本地文件> wuyangcheng@172.28.17.71:<目标路径>`，或用 rsync 走 ssh）。**适用场景**：拉取大模型权重、模型仓库、调研/部署所需的 external 资源。相关成员（运维/顾问/调研）在 zhuhai 装包、下模型、拉数据时务必遵循此中转流程，避免在无外网机器上白等/报错。
- **GPU1 一律禁止使用（2026-08-29 Owner 确认，持续有效）**：GPU1 当前**被外部人员占用**（liuchang 的 MATLAB），**任何成员/任务均不得使用 GPU1**（训练/推理/vLLM/llama.cpp/评测一律禁止）。清理/释放 GPU 时绝不动 GPU1 上的进程（那是外人的）。
- **GPU0 恢复可用，仅限单卡服务（2026-08-31 Owner 确认）**：GPU0 经协调后恢复团队使用，**主要用途为单卡（TP=1）模型服务加载**（如 llama.cpp 单卡推理、小模型 vLLM TP1 等）。**现有 TP=2 弹性池布局（g29/g34/g56/g78）不变**，GPU0 不纳入 TP2 弹性池。使用 GPU0 前需报主管协调（确认无冲突），训练/推理/评测均可使用。
- **GPU9 已并入弹性池（2026-08-29 Owner 确认，不再给 VL 预留）**：GPU9 当前属 g29 弹性槽位（GPU2+9），线上/本地模型均已自带视觉能力，**不再需要单独给 VL 视觉模型预留 GPU9**。qwen3-vl-8b VL 服务已停用。GPU9 仅作为弹性池 g29 槽位按需占用。
- **CPU 约束**：控制 CPU 使用，优先保证 liuchang 任务；大计算限核数（如 onnx 推理 intra_op_num_threads=2）
- **显存**：训练前 `nvidia-smi` 确认 GPU 空闲；模型 <200MB 显存占用可与其他任务共存
- **训练规范**：zhuhai `/home/wuyangcheng/slu_train_20260809/`（数据+脚本副本+ runs/）；训练命令 `setsid nohup` 保活 + 日志落盘 + 30-60s 检查
- **资源冲突**：发现 GPU 被占/冲突 → 主管协调（不抢占他人任务）
- **换卡必须经主管协调（2026-08-13 用户确认，强制）**：任何成员（含运维、算法、视频）提出"换卡/换 GPU/换机器调用"建议时，必须先向主管说明理由与目标卡位；**真正执行换卡操作前必须通知主管，由主管协调显卡分配**，避免多任务抢卡、与 liuchang/vLLM/其他成员任务冲突。**严禁成员内部自行换卡**；换卡后回报实际占用卡号与占用情况。此条适用所有 GPU 任务（训练/推理/转绘/视觉服务）。
- **本地 vLLM/模型服务启动强制规范（2026-08-31 Owner 授权，重大安全反例）**：任何成员/子任务在 zhuhai 启动 vLLM 或本地模型 API 服务，必须**同时**满足：
  1. **必设 `CUDA_VISIBLE_DEVICES`**，且为目标弹性槽位卡对（g29=2,9 / g34=3,4 / g56=5,6 / g78=7,8）或 GPU0（单卡 TP1 服务）。**严禁不设该变量**——否则 vLLM 默认按序拿 GPU0/1（2026-08-31 调研任务线 Qwen3-30B-A3B 测速实例即因此**错占 GPU1 禁用卡**，重大事故反例）。
  2. **host 只绑 `127.0.0.1`**，严禁 `0.0.0.0` 暴露。
  3. **绝不动 GPU1**（外部人员占用，一律禁用）；GPU0 仅限单卡服务且需报主管。
  4. **启动前先报主管协调**（端口/卡对/模型/时长），严禁私自启动。
  5. **`served_model_name` 与实际模型一致**，不得伪造（如以 qwen3.8-27b 名头实载 Qwen3-30B-A3B，导致路由到错误模型）。
  6. 停实例用 `bash /tmp/elastic_stop_vllm.sh <port>` 或带端口精确 PID，严禁 pkill 宽匹配（见 signL8 记忆「vLLM 清理红线」）。
  7. **仅用标准模板** `/tmp/elastic_start_vllm_tp2_param.sh`（已含 CUDA_VISIBLE_DEVICES + 127.0.0.1），不得裸调 `vllm serve` / `python -m vllm.entrypoints` 另起炉灶。
- **本地模型实例拉起规范（2026-09-01，生产/测试区分，强制）**：
  - **生产/常驻服务实例：一律由综合代理(11435) `_elastic_ensure`（`_elastic_vllm_cfg`）拉起**，用标准 logtag（main.py 定义，如 27b-g78→`int4-tp2-g78`）→ 日志名=标准 model_id → 8096/看板正确识别。**严禁手动/裸调另起生产实例**——logtag 漂移（`g78` vs `int4-tp2-g78`）会让 8096/看板把**在线实例误判"已下线"**（2026-09-01 bug：当前 27b-g78/g34 手动起 logtag=`g78`，STATE_FILE 残留 `int4-tp2-g78` 旧别名，在线实例显示"已下线"）。
  - **测试/临时实例（POC/测速/评测，运维/调研/顾问常裸调）：允许裸调，但必须**①logtag 用带 `_test` 后缀（如 `g78_test`）与生产隔离 ②**用完立即清理**（kill -9 实例 + 删 `~/.qwen/scripts/llm_monitor_state.json` 里对应残留 entry + 清 `/tmp` 残留日志）——**严禁用完不清理**，否则 STATE_FILE 累积残留别名 → 看板"假已下线"。
  - **通用红线（2026-09-01）**：任何实例（生产/测试）**用完必须清理**，避免 STATE_FILE 累积残留 → 8096 误判"已下线"。若需裸调测试，先确认 logtag 规范 + 用完清理；不确定时走代理 + 临时槽位。
- **僵死自愈判定必须含端口校验（2026-09-01 重大反例）**：任何"按 GPU 对/卡组匹配进程组并清理（kill -9）"的自动化自愈逻辑，必须**同时校验进程 cmdline 的 `--port == 目标槽位端口`**，严禁只按 GPU 对匹配。否则同 GPU 对跑的不同模型实例（如 g29 卡组 27b=8050 已释放 / 35b=8070 运行，共享 GPU2,9）会被误判为彼此僵死、直接误杀运行中的另一实例，导致本地服务瞬断（`Model stream ended without a finish reason. Connection error.`）。修复见 `work/documents/intelligent_router/intelligent_router_v1_20260901.md` §4。
- **智能路由 tool-call 兼容性硬规则（2026-08-31 顾问 live 终验，Owner 待定稿，强制门槛）**：候选模型进智能路由** agentic / coding / 多轮工具调用档**前，必须先过 tool-call 兼容性探针（`work/scripts/tool_call_compat_probe.py`），确认返回**原生 OpenAI `tool_calls`** 结构（Qwen Code 可解析执行）。
  - **30B/35B MoE 快档（2026-08-31 顾问复核修正）**：**两者行为不同**——仅 **30B-A3B（Qwen3-30B-A3B，Qwen3 早系）** 输出 **Hermes `<tool_call>` 文本标记**，须用 vLLM 内置 **`--tool-call-parser hermes`** 部署才转成原生 `tool_calls`（实测 GPU0/8097：`qwen3_xml`=0 工具、`hermes`=✅ 原生 tool_calls、`openai`=501 不支持）。**35B-A3B（Qwen3.6-35B-A3B，Qwen3.6 系）用 `qwen3_xml` 直接输出原生 tool_calls**（实测 GPU3+4/8071，finish=tool_calls），**无需换 hermes**。**部署：仅 30B 用 `hermes`，35B 用 `qwen3_xml` 即可**；严禁把 35B 也一律套 `hermes`。
  - 结论：Qwen3-30B-A3B **能进 agentic 档**（用 `hermes` 部署），仅纯文本档无需此门槛；qwen3.8-27b 原生 tool_calls，质量档首选。
  - 详证见 `work/documents/advisor_toolcall_compat_report_20260831_v1.md`。
- **算法训练 × wan 后端显卡互斥（2026-08-13 用户确认，重点）**：算法（signL5）的训练任务与 wan 后端（signL2）的转绘推理是目前 GPU 占用最大的两条线，必须**内部互相协调显卡使用**：
  1. 各自开训/迁移前，先查对方当前占用与计划（看板/健康状态/确认通道），避免同时抢占同一批卡；
  2. 使用卡位前先向主管报计划（卡号区间+预计时长），主管确认无冲突后执行；
  3. 训练与转绘如需共享卡位，按"短任务让长任务、转绘 job 密集时段让训练错峰"原则协商，协商不成报主管定夺；
  4. 任何一方换卡/扩卡/停卡都必须通知另一方 + 回报主管，防止 GPU5-8（wan）与 GPU0-4（训练/通用）串扰；
  5. 冲突一旦发生，先停新任务、保留进行中任务，立即报告主管协调，不互相强杀。

## 4. 汇报与协作规范

- **本地模型服务说明：视觉可用性 + 智能路由（2026-09-01 顾问实测，供选型参考）**：团队**所有本地模型统一经综合代理（`127.0.0.1:11435`）访问**，**严禁绕过直连 zhuhai 端口**。**如需视觉能力，可用本地这两种模型**（均含原生视觉塔，非 visionBridge 桥接）：
  - **Qwen3.8-27B**（`qwen3.8-27b-int4-tp2-*`，g29/34/56/78 槽位；稠密 27B，AWQ-INT4）：**视觉基础能力强**（颜色/位置/OCR/计数/空间全对），对**图表/精细数值读取**能给出趋势+排序但**数值上偏**（需人工核对）。
  - **Qwen3.6-35B-A3B**（`qwen3.6-35b-a3b-tp2-*`，如 g29；MoE，AWQ-4bit）：视觉基础能力同样强（颜色/位置/OCR/计数/空间全对），但**精确读图/读数值能力弱**（柱状图读值实测**空输出失败**），**仅适合描述/OCR，不适合精确读图**。
  - **组合建议**：看真实图/图表→优先 **Qwen3.8-27B**；精确考据（图表数值、硬事实）→走**联网核实**或 **deepseek-v4-flash-vision-exp（官方 API，顾问在用，1M ctx）**；视觉作为 agentic 一环（需看图决策）→**Qwen3.8-27B** 更稳。
  - ⚠️ **Qwen Code 前端注意**：settings.json 里 **Qwen3.6-35B-A3B 注释为"工具调用可用"、未标"视觉可用"**（Qwen3.8-27B 标了），前端对 35b **可能不默认启用本地图像 pipeline**；用 Qwen3.6-35B-A3B 看图前需先确认前端配置。
  - **详细实测**：`work/documents/intelligent_router/local_vision_capacity_cmp_v1_20260901.md`（含 4 题对比 + 图）；智能路由主题文档：`work/documents/intelligent_router/intelligent_router_v1_20260901.md`（§7 视觉能力实测比较）。
  - **调用方式**：`POST http://127.0.0.1:11435/v1/chat/completions`，`model=qwen3.8-27b-int4-tp2-g29`（或其它本地槽位），user content 用 `[{"type":"text",...},{"type":"image_url","image_url":{"url":"data:image/png;base64,<b64>"}}]`；`message.content`=答案、`message.reasoning`=思考；content 空（thinking 耗尽预算）→加大 `max_tokens` 重试。
- **性能实测/对比必须写清模型型号（2026-09-01 顾问建立，强制）**：凡做**模型性能/能力实测、两及以上模型对比、速测、评测、选型结论**（含视觉能力、推理速度、tool-call、长文本、量化影响等任何维度），**必须以完整型号 + 架构 + 量化 + model_id 标注每个被测模型**，**严禁只写"27b/35b/Qwen 模型"这类简写**。完整规格至少含：品牌型号（如 `Qwen3.8-27B` / `Qwen3.6-35B-A3B`）、架构（稠密/MoE）、量化（AWQ-INT4/AWQ-4bit 等）、model_id（`qwen3.8-27b-int4-tp2-*`）、槽位/端口/卡对、运行状态。
  - **原因**：本地池有多个版本/量化/架构的相近型号（27b 稠密 vs 35b MoE 差距明显），只写参数无歧义，读者无法判断结论属于哪个模型，易误套用。
  - **如何在报告中呈现**：每节开头给被测模型全称；表格/结论处用「全名(简称)」如 `Qwen3.6-35B-A3B(35b)`，**首次出现必给全称**，后续可简称但要能回溯对照；重要对比类结论（如"XX 柱状图读值失败"）必须带全型号。
  - **适用**：本地/官方/外部任意模型，不止本地池；可视化/看板/智能路由文档同样适用。
- **死循环自动监督机制（2026-09-01 新增，全成员自动监督，Owner 要求）**：本地 AWQ4 量化模型（如 Qwen3.6-35B-A3B）会出现"思考/输出死循环"（模型在思考或输出阶段陷入无限重复，耗 token/上下文却不产出有效结果）。团队已上线**常驻死循环监督 watchdog**（`work/scripts/daemon_loop_watchdog_v1.py`，setsid 保活，见 §16.3）自动处理：
  1. **检测**：读 transcript 尾部提取最近 model 消息正文，连续 3 条高度相似（相似度 ≥0.90、最后一条 ≥120 字）判为死循环。
  2. **恢复流程**（由 watchdog 自动执行）：`POST /session/:id/cancel` 打断当前生成 → 查 `context-usage`，**ctx 余量占比 <20% 则先 `/compress`（等完成）再补发『继续完成』；否则直接打断后补发『继续完成』**。
  3. **限流**：同一会话 120s 冷却防反复打断；1h 内触发 3 次转人工介入队列。
  4. **成员须知**：若会话被自动打断并补发「继续完成」，请检查当前进度继续完成原任务，**无需人工干预**，属正常自愈；如频繁被打断（2 次以上）说明上下文或模型状态需调整（如降 reasoning_effort / 加大 max_tokens），请回报主管评估。

- **完成/异常/里程碑主动后台通知主管**（tmux 消息格式：`【主管】...` / `【人工介入请求】窗口: | 任务: | 路径:`）
- **消息前缀辨识规则（2026-08-31 Owner 强调，强制，须无歧义识别交互对象）**：
  - **带【】前缀 = team 成员间交互**：进入团队消息协议，必须写清【发件人→收件人】【来自<来源>】。
  - **不带任何【】前缀的消息 = Owner 直接交互**：默认是 Owner 与当前会话的直接对话，按 Owner 指令/问答处理，**不应当成团队消息**、不应误判为"某成员的内部消息"或"需转发的团队指令"。
- **消息前缀规范（2026-08-30 强化，Owner 要求，必须无歧义）**：成员间/成员对主管的所有消息，前缀必须写清**方向**（谁发给谁）+ **来源**，格式**【发件人→收件人】【来自<来源>】**，不得只写角色名让收件人猜。
  - **自报身份**：自己发言/回复时，开头用正式名前缀表明"我是谁"——【主管】【视频】【语义动画】【算法】【运维】【调研】【本地A】【本地B】【顾问】【Jarvis】。
  - **定向投递（关键）**：发给某个具体成员的消息，前缀必须写清「发件人→收件人」，格式【发件人→收件人】，如【主管→运维】【运维→主管】【视频→主管】。**严禁只写【主管】让收件人猜方向**。
  - **来源标注**：用【来自<来源>】标明指令真实来源——直发（自己负责发给对方）来源=发件人，如【主管→运维】【来自主管】；转达（Jarvis 转达 Owner 指令）来源=Owner，如【Jarvis→运维】【来自Owner】，避免把转述当判断。
  - **广播**：发给全体成员用【主管→全体】。
  - **回报/闭环**：成员向主管回报任务结果用【<成员>→主管·回报】，如【语义动画→主管·回报】。
  - **紧急/更正**：叠加【紧急】【更正】前缀在最前，如【紧急】【主管→运维】。
  - 不用内部 id（SignL3/signL10 等仅作程序字段）、不用旧 tmux 窗口号。
- **成员确认走后台通道**：成员对主管通知/约束/指令的确认，**追加一行到 `/data/WYC/signLanguage/.team/team_confirmations.log`**（格式：`【成员确认】窗口:xxx | 事项:xxx | 内容:xxx`），由 monitor 后台扫描转发到 team_messages.log 并提醒主管；**不通过前台 prompt 消息打扰/打断**（主管后台读取 monitor 日志获知即可）
- **用户在场宽限（人工介入免打扰）**：用户可直接与各成员交互；成员须在**每次收到用户直接输入**（消息不带【】agent 间标志）时，把当前 ISO 时间写入 `/data/WYC/signLanguage/.team/user_last_interaction/<成员id>.txt`（成员 id 从 `team_topology.json` 读取；运行时窗口名由拓扑解析）。成员发【人工介入请求】时，monitor 判断：若距该成员最近一次用户直接输入 **< 8 分钟**（阈值可调 `--user-grace-minutes`，2026-08-11 由 5 调至 8）→ 判定用户正在该成员处交互 → **仅入队、不提醒主管**；超过则正常入队提醒主管
- **主管转达规则（宽限联动）**：monitor 捕获成员消息时，若该成员距用户最近直接输入 < 8 分钟，日志行标注【用户在场-免转达】；主管读到此类标记或查 `user_last_interaction` 确认用户正在该成员处交互时，**不主动转达该成员消息**（用户正与该成员直接交互，从窗口可见），仅记录；宽限期外才转达
- **进度落盘**：`/home/wuyangcheng/.qwen/progress/`（或团队目录）
- **共享事实走 .team/（跨 CLI 记忆互通，2026-08-11 加入，用户确认）**：Qwen Code（`~/.qwen/memories/`）与 Codex（`~/.codex/memories/`）的**私有记忆互不读取**。因此**跨成员/跨 CLI 必须知道的事实一律只写 `/data/WYC/signLanguage/.team/` 共享文件**（公共约束、team_messages.log、队列、user_last_interaction、成员记忆文件），**不依赖各自 CLI 私有记忆**。各成员私有记忆可记录个人工作细节，但关键事实必须同步到共享文件
- **成员记忆文件约定（2026-08-11 加入，用户确认）**：每个成员维护自己的工作记忆文件 `/data/WYC/signLanguage/.team/member_memories/member_memories_<成员id>.md`（成员 id 从 `team_topology.json` 读取）——记录：当前任务状态、关键决策、待办/待确认事项、踩坑记录；**主管可直接读取了解成员记忆**，实现 Qwen/Codex 成员记忆互通。成员在**任务阶段切换/完成/遇到重要结论**时更新该文件；主管定期查看汇总
- **成员进展记录与公共事实维护义务（2026-08-12 加入，用户确认）**：每个成员必须持续维护**自身重要进展记录**（阶段完成/关键结论/产物路径/待确认项），写入**后台确认通道**（team_confirmations.log，monitor 5s 抓取）或**进展文件**（progress/<窗口>.txt），并同步更新**成员记忆文件**（member_memories/）；**公共事实更新**（工作线状态/部署状态/新增产出/资源变化）同步到共享文件（.team/）——主管据此实时维护 dashboard 小目标。**不得只留在各自 CLI 私有记忆或对话里**（主管无法抓取）
- **团队信息结构一致性自维护（2026-08-29 加入，Owner 要求）**：团队命名与展示名必须保持四层一致，任一漂移即视为需修复：

  1. **唯一权威源 = `team_topology.json` 的 `roles[*].name`**（正式中文名：主管/视频/语义动画/算法/运维/调研/本地A/本地B/顾问）。
     - **角色 id 定位（2026-08-29 明确）**：`SignL3`/`signL2` 等 `roles[*]` 的键是**程序稳定标识**（registry/topology/members 目录用），**不用于理解含义**——理解含义看 `name`（中文正式名）或 `name_en`（英文语义名，纯参考）。id 与早期 tmux 窗口名**无绑定**（tmux 窗口已废弃，daemon 时代用 session_id）；**id 不应改成语义化英文**（深嵌 members/ 目录、helper 参数、registry 键等运行逻辑，改名风险大收益低），`name_en` 仅作理解参考、不驱动任何逻辑。
  2. 其余三层（registry `roles[*].name`、daemon 实际 `displayName`、supervisor state `name`）必须与权威源一致。
  3. **审计**：`python3 work/scripts/team_identity_audit.py`（校验四层一致性，发现漂移输出报告；`--write-md` 落盘 `.team/identity_audit_report.md`；exit 0=一致、1=有漂移）。
  4. **修复**：`python3 work/scripts/team_sync_displaynames.py --apply [--sync-registry]`（把 daemon displayName 一键对齐到拓扑正式名；先 `--dry-run` 预览）。
  5. **成员记忆文件**：每个成员必须维护 `member_memories/member_memories_<成员id>.md`（成员 id = registry/topology roles 键，如 `signL10`、`advisor`、`SignL3`）；缺文件的角色由主管/顾问发现后补建骨架。
  6. **改名后必做**：改 `team_topology.json` 的 name 后，必须跑 `team_sync_displaynames.py --apply --sync-registry` 并重启 supervisor（`kill <supervisor_pid>` 让其被 while 循环自动重载），否则 supervisor state 会展示旧名（已修复：check_role 现每次同步 registry name，write_digest 只展示 registry 注册角色，已退出的 signL6/宣传员不再带出）。
  7. **成员退出 team 的处理**：从 `team_topology.json` 的 `roles` **移除**该角色（或标记 `disabled`），并从 supervisor state/`_memories` 清除其键；unassigned session 保留供历史参考。已退出角色（signL6/字幕员、signL7/宣传员）不再提及、不再审计、不再纳入监督。
- **团队信息文件分层维护职责（2026-08-29 加入，Owner 要求）**：所有成员信息统一落盘在项目 `.team/` 目录，分层维护，**各层维护者唯一、不越权**：

  | 信息类型               | 路径                                                       | 维护者                | 内容                                                                                                  |
  | ---------------------- | ---------------------------------------------------------- | --------------------- | ----------------------------------------------------------------------------------------------------- |
  | 公共约束               | `.team/team_constraints.md`                              | **主管**        | 安全/资源/汇报/职责/仓库边界/daemon 管理；变更须经用户确认                                            |
  | 团队身份/公共约束摘要  | `.qwen/rules/team_identity_profile.md`                   | **主管**        | 11 角色身份表 + 公共约束摘要（成员会话自动加载）                                                      |
  | 团队拓扑/服务注册表    | `.team/team_topology.json`                               | **主管+运维**   | roles 稳定 id/窗口、local_model_services 端口/GPU/ctx/状态；服务变更由运维执行、主管确认后 24h 内更新 |
  | 角色身份文件           | `.team/roles/<角色id>.md`                                | **各角色自己**  | 自己的 name/职责/模型/会话id/关键身份（"你是 XX"）；主管/顾问发现缺文件时补建骨架                     |
  | 成员工作记忆           | `.team/member_memories/member_memories_<成员id>.md`      | **各角色自己**  | 当前任务状态/关键决策/待办/踩坑；主管可直接读取                                                       |
  | 团队进展（单一事实源） | `.team/daemon_v1/progress_supervisor/latest_progress.md` | **监督器自动**  | 各角色状态/待汇报进展；监督器重写，勿手改                                                             |
  | 团队信息一致性审计     | `.team/identity_audit_report.md`                         | **监督器/主管** | `team_identity_audit.py --write-md` 产出                                                            |

  **维护原则**：① 主管维护"团队级"（公共约束/拓扑/身份表/进展），**不改各角色分内文件**；② 各角色维护"自己分内"（自己的身份文件 + 工作记忆），**不改公共约束/他人文件**；③ 顾问可协助发现/补建骨架、审计一致性，但不越权代改各角色内容；④ 成员信息都落 `.team/`（含身份/记忆/进展），**不依赖各自 CLI 私有记忆**（跨 CLI 互通）；⑤ 新增文件一律带 frontmatter（`--- description: ... ---`）便于识别。
- **角色自认定（身份确认）规范（2026-08-31 加入，Owner 要求，强制）**：每个成员必须明确"我是谁"，认定方式按优先级：
  1. **首选（系统提示词注入）**：成员会话默认加载的文件（`.qwen/rules/team_identity_profile.md` + `.team/roles/<角色id>.md`）中已包含自己的身份文件（角色 id、正式名、职责、模型、前缀、红线）。**这是最可靠的身份来源**——会话启动时自动注入，无需额外操作。
  2. **兜底（拓扑映射反查）**：若因上下文压缩/会话重建等原因忘记了自身身份，**必须首先根据团队拓扑映射约定，用自己的 daemon session_id 反查身份**：
     - 获取自己的 session_id：`env | grep QWEN_CODE_SESSION_ID`（或从 daemon `/session/:id/context` 接口读取）
     - 在 `.team/team_topology.json` 的 `roles[*].session_id` 中反查对应角色 id
     - 读取 `.team/roles/<角色id>.md` 确认完整身份
     - **严禁**凭消息前缀、任务文本中的收件人、或共享项目记忆中的"本会话=X"声明来认定身份（2026-08-30/31 多次身份错乱根因）
  3. **⚠️ 勿用子进程/后台 sub/side_task 继承的共享 env 认身份（2026-08-31 身份错乱根因，Owner 强调，强制）**：后台 sub / side_task / 模板进程会**继承 daemon 共享或模板值**的 `QWEN_CODE_SESSION_ID`（如显示 ce3dad61，但那是另一个顾问会话的 id），**绝不能把它当成自己的主会话 id**——否则会误判自己为其他角色并误发"身份映射修正/更正"类消息。**正确的主会话核实方法**：
     - 查**主会话**真实 env：在自己**当前实际工作**的主会话终端里执行 `echo $QWEN_CODE_SESSION_ID`（若在后台 sub/side_task 里，此值可能是共享/模板的，不可信）。
     - 或从 daemon 接口读**主会话** displayName：`GET /session/<主会话id>/context`（返回的 displayName 才是 daemon 界面所见的真实角色）；有争议时用主会话 session_id 反查 `team_topology.json` + 读 `.team/roles/<id>.md`。
     - **不要用 `hasActivePrompt` 单点判断身份**（多会话并行时可能有多个 active，2026-08-30 曾同时出现主管+顾问 active）。
     - 若两个会话（如本地A=8ee20f7e、顾问=ce3dad61）因同源误读共享 env 而发来互相矛盾的消息，属正常消歧场景——以「主会话 session_id → 拓扑反查」为准，不要按消息前缀/自称内容去改拓扑。
  4. **红线**：任何回报/落盘/署名前，若不确定自身身份，必须先做 session_id 反查确认；任务前缀里的「收件人」≠「我是谁」。
- **team 文档/状态更新时间戳（2026-08-29 加入，Owner 要求，强制）**：主管定期维护 team 相关文档与当前状态时，**凡有更新，必须在本文件/文档顶部或更新处写清"最后更新时间，精确到分钟"**（如 `> 最后更新时间：2026-08-29 22:10（北京时间）

  - **适用对象**：公共约束（team_constraints.md）、团队拓扑（team_topology.json，fields `_updated_at`）、各角色身份文件（.team/roles/*.md）、成员工作记忆（member_memories/*.md）、团队身份规则（.qwen/rules/team_identity_profile.md）等所有由团队/成员维护的状态文档。
  - **精度**：精确到分钟（`YYYY-MM-DD HH:MM`），注明时区（北京时间）。
  - **更新者义务**：谁改谁更新该文件的时间戳——主管改团队级文档填对应文件的时戳，成员改自己身份/记忆文件时同步更新自己的时戳。避免"改了内容却没标时间"导致无法追溯新旧。
- **用户在线状态自动维护（2026-08-12 加入，用户确认）**：monitor 自动维护 user_online——所有成员窗口距最近用户交互 ≥60 分钟（阈值 `--offline-after-minutes`）→ 自动标记离线；任一窗口出现新鲜交互（< 用户在场宽限）→ 自动恢复在线；中间态尊重手动标记；用户显式声明离线仍以手动为准
- **人工介入**：成员需用户介入 → 后台报主管 → 主管提醒用户去该窗口 → 用户在成员处直接处理 → 成员通知主管完成 → 主管更新队列（不代答、不擅自标记完成；用户离线不催促）
- **临时 sub**：可随时启动，无需常驻；不占常驻名额
- **紧急/更正类消息必须用 `--interrupt` 打断投递（2026-08-29 Owner 要求）**：成员间发送**需要及时操作的消息**（更正、纠错、紧急指令、状态变更通知等），发送方**必须使用 `--interrupt` 标志**投递 mailbox，主动打断目标成员当前工作状态，让消息立即生效。

  - **命令**：`python3 work/scripts/daemon_team_mailbox_v1.py --to-role <角色> --prompt "【紧急】..." --interrupt`
  - **机制**：`--interrupt` 优先走 **mid-turn 注入**（保留当前上下文、不丢弃任务，消息注入到活跃 turn 中立即被模型看到）；mid-turn 不可用时回退 **cancel+prompt**（取消当前 turn 再投递新消息）
  - **实测确认（2026-08-29）**：对活跃会话（算法/本地B）mid-turn 注入 `accepted=true` 生效；对空闲会话自动降级为普通投递（`session_idle`）
  - **前缀规范**：消息中应标注紧急程度（「【紧急】」「【更正】」前缀），接收方看到此类前缀必须优先响应
  - **原因**：本地模型（qwen3.8-27b）运行较慢，若接收方正在执行长任务，不主动打断则消息可能长时间无人处理，导致信息滞后或操作冲突
  - **打断分两种情形（2026-08-30 Owner 要求，强制区分）**：
    - **作废任务（取消 / 推翻目标当前任务）**：**直接打断**即可，无需保留原任务上下文——原任务已作废，接收方直接转向新指令。
    - **插入高优任务（原任务仍需继续，只是优先级更高）**：**先抓目标会话的 todoList 进度，再打断**；打断消息**末尾必须附上「处理完本高优任务后，请继续原任务」+ 抓到的 todoList 进度快照**，确保接收方处理完高优任务后能从断点续做原任务、不丢进度。
      - **抓 todoList 进度**：通过 daemon 会话接口读取目标会话当前 todo 状态（`GET /session/:id/...` 的 todo 字段），或读其 `member_memories/<id>.md` 的「当前任务状态」段；把「第几步已完成 / 第几步进行中 / 下一步计划」写进打断消息末尾。
      - **原因**：`--interrupt` 的 cancel 兜底会丢弃当前 turn 上下文；若不显式带回 todoList 进度，接收方处理完高优任务后不知道原任务进行到哪，会重复劳动或漏步。
- **长流程多步骤任务必须逐步 followup 落盘（2026-08-29 Owner 要求，强制）**：执行**长流程多步骤任务**（多阶段管线、训练+评测、多轮实验、多文件改造等）时，**每完成一个关键步骤，必须及时更新相关文档的进度**，**不得等整个任务做完才一次性落盘**。

  - **适用文档**：任务对应的计划/实验报告/技术文档、成员记忆文件（`member_memories/<id>.md`）、进展文件（progress/）——即任何记录该任务进度的文档。
  - **关键步骤定义**：每个阶段完成（数据就绪/训练启动/训练完成/评测完成/结论得出）、每个重要决策、每个产物生成、每个阻塞点。
  - **更新内容**：当前进度（第几步已完成/第几步进行中）、关键数据（数字/产物路径）、下一步计划；时间戳精确到分钟（遵循「team 文档/状态更新时间戳」规范）。
  - **原因**：本地模型慢、长任务跨时长，会话可能被打断/压缩/重建；若进度不逐步落盘，主管与 Owner 无法掌握实时状态，中断后无法从断点续做，导致重复劳动或进度丢失。
  - **与既有规范关系**：是「成员进展记录与公共事实维护义务」（2026-08-12）的强化落地 + 任务闭环规范的补充——闭环规范要求完成时回报，本条要求**每一步都落盘**，两者并用。

### 任务闭环规范（2026-08-24 主管广播，Owner 确认，全体成员强制）

主管派发的任务必须**主动回报收束**，形成闭环：**发起 → 执行 → 回报 → 主管验收 → 关闭**。

1. **主动回报（必须）**：无论任务进度/结果/决策变化（含 Owner 直接示意），都必须**主动回报主管**收束——不能只执行不汇报，不能让主管/其他成员停留在"不知道任务状态"中。
2. **完成后回报成果与数据**：回报应包含做了什么、产物/输出路径、验证结果（数字/ffprobe/测试等）、失败原因（如未做成）。
3. **遇阻即时回报**：遇到阻塞/异常/需要决策时，**即时回报原因与建议**，不沉默、不搁置。
4. **Owner 直接示意时同步回报主管**：被 Owner 直接示意（新任务/修改/纠正）时，**同步回报主管**，由主管知晓并关闭/更新任务，避免任务状态在团队层面失明。

### 变更记录

- 2026-08-24：§4 新增任务闭环规范（主管派发任务：发起→执行→回报→验收→关闭；完成回报成果数据；遇阻即时回报；Owner 直接示意同步回报主管）
- 2026-08-25：§76 补强 Sub 成果继承（派发 sub 必须附已有成果清单——现成脚本/部署文档/基线数据/已确认结论绝对路径，明确"不要重复做"与增量产出；复查纠正重复劳动；模板见 ~/.qwen/skills/sub_agent.md）
- 2026-08-29：§4 新增「紧急/更正类消息必须用 --interrupt 打断投递」——发送方必须用 `--interrupt` 标志主动打断目标会话（mid-turn 注入优先，cancel 兜底），实测生效（Owner 要求）
- 2026-08-29：§4 新增「长流程多步骤任务必须逐步 followup 落盘」——长任务每完成一个关键步骤必须及时更新相关文档进度（计划/报告/成员记忆/进展文件），不得等任务做完才一次性落盘（Owner 要求）
- 2026-08-29：§4 新增「团队信息结构一致性自维护」——命名四层一致（权威=team_topology roles.name），审计脚本 team_identity_audit.py + 修复脚本 team_sync_displaynames.py + 成员记忆文件义务 + 退出角色处理；统一 displayName 6 角色（signL2/4/5/9/10/11）+ 修正 supervisor state 旧名快照 + 补齐 5 个 member_memories（SignL3/signL9/signL10/signL11/advisor）
- 2026-08-29：§4 新增「团队信息文件分层维护职责」——所有成员信息分层落盘 .team/（公共约束→主管、身份表→主管、拓扑/服务→主管+运维、角色身份/成员记忆→各角色自己、进展→监督器自动、一致性审计→主管/监督器），维护者唯一不越权；新增 .qwen/rules/team_identity_profile.md（成员会话自动加载的团队身份+公共约束摘要）+ .team/roles/*.md（各角色身份文件，含"你是XX"）。另：修复 QWEN.md §5 过时 GPU 格局（GPU0/1 禁用、GPU2-9 弹性池 g29/g34/g56/g78、GPU9 并入 g29、vLLM 清理红线）

- 2026-08-30：§4 新增「并行 sub 提前开工（early-dispatch）」——主任务基本完成时立即提前派发下游 sub 做独立准备段（调研/选型/脚手架），定稿后再 send_message 交最终版做精修段，让 sub 准备与主任务收尾并行（Owner 要求）
- 2026-08-30：§4「--interrupt 打断投递」补强为两种情形——**作废任务直接打断**（无需保留原任务上下文）；**插入高优任务先抓目标会话 todoList 进度再打断**，打断消息末尾附「处理完高优任务后继续原任务 + todoList 进度快照」，防止 cancel 丢上下文导致原任务漏步/重复劳动（Owner 要求）

### 职责优先协作与升级（2026-08-12 用户确认）

- 成员遇到职责外或当前无法解决的问题，先查阅 §8/§9 与 `team_topology.json`，不得停滞或重复造轮子。
- 视觉综合测评中的 API key、OAuth、api_base、模型接入、代理、额度问题，先找 signL8 运维；算法/模型问题找 signL5；overlay 动画找 signL4。
- 成员可以协商转派更适合的子任务；涉及密钥、权限、外部资源、生产部署或公开仓库时，必须由对应负责人执行或明确授权，不得索取或暴露敏感值。
- 协商结果必须写入 `team_confirmations.log`，至少说明：谁负责、谁协助、交付物、下一步和阻塞点；同时更新 progress/member_memories，不能只留在私聊或 CLI 对话中。
- 对应负责人也无法解决时，立即以 `【人工介入请求】` 或 `【成员确认】` 升级主管，附已尝试方法、脱敏错误信息和所需决策；主管负责拆解、协调资源、重新指派或启动临时 sub。
- **运维问题默认路由（2026-08-12 用户确认）**：代理、GPT/DeepSeek/Qwen 模型切换、OAuth、API key/api_base、额度、statusline、Qwen/Codex 配置、tmux/monitor/health、服务保活、网络与环境问题，以及同类运行时异常，默认交由 **signL8 运维**负责调查、协调和修复；其他成员不得各自盲改同一生产配置。
- **切换 GPT 前的上下文检查（2026-08-13 用户确认）**：任何成员从 DS/其他 provider 切换到 GPT ChatGPT 模型前，必须先查看该会话 statusline 的 context 使用比例和绝对窗口；若 context 使用比例 **>=50%**，**必须先在当前模型/provider 下执行 compress**，确认压缩完成且比例回落到 50% 以下后，再切换 GPT；不得先切 GPT 再压缩。若当前模型无法安全 compress，再由 signL8 评估 resume/迁移或新会话方案，并保留旧 session。切换后先做最小真实请求，再恢复长任务。
- **GPT 空响应应急（2026-08-13 用户确认）**：出现 `Upstream returned empty response after 3 attempts`、`Response truncated` 或同类 GPT OAuth 异常时，先保留现场与日志并通知 signL8；不得成员自行反复重试、换 provider 或换 GPU。signL8 负责检查上游响应、tool-call/finish_reason、重试退避和上下文负载，必要时启动 sub；修复验证前 dashboard 保留 API 异常状态。
- **运维并发委派**：问题需要并发调查时，由 signL8 运维按职责启动 sub/临时协作者，并明确每个 sub 的独立范围、输入上下文、禁止修改范围和回报文件；不得让多个 sub 重叠修改同一文件或重复消耗同一生产会话。
- **上下文关联管理**：signL8 必须把主问题、相关公共约束、当前配置/版本、已知错误、任务分工、共享文件路径和验证标准同步给 sub；sub 的结论必须回到 `.team/` 共享文件、progress/member_memories，并由 signL8 汇总确认，不得只留在 sub 私有上下文。
- **Sub 成果继承（2026-08-25，Owner 要求）**：派发 sub 时必须附已有成果清单——相关现成脚本/部署文档/基线数据/已确认结论的**绝对路径**，明确"不要重复做"事项与本次**增量产出**；sub 无父对话历史，看不到主进程已有成果。启动后须复查 sub 输出，发现重复劳动（重写已有脚本、重测已有基线、重新调研已知信息）立即 send_message 纠正。执行细则与模板见 `~/.qwen/skills/sub_agent.md` 已有成果继承规范章节。
- **并行 sub 提前开工（early-dispatch，2026-08-30 Owner 要求）**：主任务**基本完成**（核心结构/结论/关键数据已稳定，剩余只是"收尾/精修/最终数据填充"这类**不改变下游 sub 工作方向**的步骤）时，**立即提前派发下游 sub** 先做其"独立准备段"（调研、工具/库选型、脚手架、模板/初稿框架），让 sub 的准备时间与主任务的收尾时间**并行重叠**；主任务 100% 定稿后再用 `send_message` 把最新版（最终数据/路径/结论）交给 sub 做"依赖最终版的精修段"。
  - **适用**：下游 sub 的工作可拆成"独立准备段 + 依赖最终版精修段"两段（如内容制作/报告排版/代码脚手架/分享物料/调研+落稿）。
  - **不适用**：下游 sub 完全依赖主任务最终产物、无独立准备段——此时必须等主任务完成再派发，否则 sub 拿到半成品会返工。
  - **写作用域隔离**：sub 的独立准备段不得写会覆盖主任务最终产物的文件，避免与主任务收尾冲突。
  - **收益**：sub 准备段（常占其总时长大头，如调研/选型/搭框架）与主任务收尾并行，整体墙钟时间显著缩短。
  - **本次范例（2026-08-30 MTP 报告）**：报告 §5.3 对比分析"基本完成"（核心结论已定）时，本应**立即**提前派发小红书 sub 做"调研渲染库 + 搭卡片框架"独立准备段，报告定稿后再 send_message 交最终数据做卡片精修——而非等报告全部收尾才派发。
- **结果回报与变更纪律**：修复前先备份；报告根因、影响范围、修改文件、回滚点、测试命令和失败降级策略；涉及权限/密钥/生产服务/公开仓库先报主管；验证通过后由 signL8 统一通知主管，避免成员各自报不同结论。
- **常驻成员会话恢复（2026-08-12 用户确认）**：重启常驻成员的 Qwen/Codex 对话后，必须优先使用原会话 `resume` 恢复上下文、任务记录和待办，不得默认新建空白会话导致工作上下文丢失。
- **主管拓扑引用规范（2026-08-12 用户确认）**：主管维护公共约束、dashboard、日志和委派任务时，文档与逻辑必须使用 `team_topology.json` 中的稳定成员 id/角色/职责；不得硬编码可能变化的 tmux 窗口名。运行时窗口名只能由拓扑解析模块读取；窗口变动只修改拓扑文件，不改业务脚本和规范正文。
- **provider 不兼容例外**：若原会话存档绑定了错误或不兼容的 provider（例如旧 DeepSeek 存档不能直接承载 GPT OAuth），由 signL8 先备份并修正 provider/config，再测试原会话 resume；只有确认 resume 会继续错误路由时，才可迁移到新会话。
- **provider 不兼容必须走历史迁移 skill（2026-08-12 用户确认）**：迁移不得只靠手工摘要或复制几条消息，必须使用既有 `qwen-codex-context-migrate` skill，按其检查、规划、迁移、验证流程迁移完整可用的 session 历史/上下文；迁移前保留旧 session，迁移后验证新 provider 路由、任务连续性和待办完整性，并回报旧/新 session ID、skill 流程、迁移范围与验证结果。
- **视觉类产物必须用本地模型视觉自检（2026-08-30 Owner 要求，强制）**：凡产出的**视觉类产物**（前端动画、渲染截图、overlay 语义标注、转绘帧、图像等），交付/汇报前**必须用本地 Qwen3.8-27B 自带的视觉能力自检**，确认画面符合要求（如近大远小、场景正确、人物清晰、无缺失/变形），**不得只生成不核验就交付**。
  - **有本地 qwen3.8-27b 服务时，一律直接用本地服务的视觉能力看图（2026-08-30 Owner 强调，强制）**：本地模型已有原生视觉塔，**不要再走 DeepSeek/外部 vision bridge 看图**。实测（2026-08-30）主管side用 `deepseek-v4-flash-vision-exp` 的 vision bridge 做图片转写，产出是 **garbage**（模型自己都吐槽"bridge 模型在这个任务做得很差"）；而本地 qwen3.8-27b 用 `image_url+base64` 看同一截图能**正确**判出"长发女生/雨夜场景/画面生动"。**结论：本地能力足够且更准，视觉类自检就本地，别绕 DS。**
  - **本地模型视觉调用方式**（OpenAI 兼容多模态）：`POST http://127.0.0.1:11435/v1/chat/completions`，`model=qwen3.8-27b-int4-tp2-g29`（或其它本地槽位），`messages` 里 user content 用 `[{"type":"text","text":<检查要求>},{"type":"image_url","image_url":{"url":"data:image/<type>;base64,<b64>"}}]`。**禁止绕过 11435 直连 zhuhai 端口**。
  - **响应**：`message.content`=答案、`message.reasoning`=思考；若 content 空（thinking 耗尽预算）→ 加大 `max_tokens` 重试，仍空则从 `reasoning` 尾部兜底。
  - **可复用脚本**：`/data/WYC/signLanguage/work/scripts/audit_semantic_overlay_strict_v5.py`（`call_vl()` 函数即完整范本，含 base64 转图 + thinking 模式 + 内容兜底）。
  - **实测背书**（2026-08-30）：本地模型用 `image_url+base64` 看动画渲染截图 `frame_6000ms.png` 能正确判出"有长发女生/雨夜场景/画面生动"（thinking 580-613 字），视觉自检完全可行；动画side（09054c94）此前只产出未自检，正是缺这一步。

## 5. 公开仓库/部署规范

- **PR 流程**：公开仓库（sign-language-universe）改动走分支 + PR（main 受保护，CI 通过后合并）
- **提交前更新 README**（中英）；版本徽标 PR 号制（合并后更新徽标 PR）
- **模型/视频入库**：onnx/mp4 经 CI forbidden-files 检查（assets/model/*.onnx、reference-videos 白名单）
- **通知 signL2**：本地打分模型更新 → 通知 signL2 复测（见记忆 new_model_notify_wan）

## 6. 数据/实验规范

- **synthetic 测试缓存复用**：同 n/k/p/overlap/search_trials/base_seed 组合跨 suite 复用同一测试集；canonical hash 去重排除训练数据
- **真实数据默认目录**：`/data/WYC/diffusion-searcher/data/`（除非用户明确指定）
- **文档同步映射**：工作更新 → 同步对应文档（见记忆 work_doc_mapping）；系统文档（sign_language_scoring_system_documentation）改动须更新版本号 + 变更记录
- **报告规范**：ML 实验后写图文报告（图表嵌入 MD）；保存时间精确到分钟

## 7. 变更记录

- 2026-08-10：初版建立（安全/版本/zhuhai 资源/汇报/部署/数据六类约束）
- 2026-08-10：§8 组织架构加入（signL2/signL4 平级，直接向主管汇报）
- 2026-08-10：§9 职责边界与 dashboard 加入（overlay 审核细节隔离 signL2；主管统一维护 dashboard）
- 2026-08-10：§4 新增成员确认后台通道（team_confirmations.log，monitor 扫描转发，不打扰前台）
- 2026-08-10：§4 新增用户在场宽限（成员记录用户直接输入时间，5 分钟内介入请求免提醒主管）
- 2026-08-11：§4 新增共享事实走 .team/ + 成员记忆文件约定（跨 Qwen/Codex 记忆互通）
- 2026-08-12：§4 新增用户在线状态自动维护（monitor 60min 无交互自动离线，新鲜交互自动恢复）
- 2026-08-12：§4 新增成员进展记录与公共事实维护义务（后台确认通道/进展文件/成员记忆三处同步，主管实时抓取维护 dashboard）
- 2026-08-12：§4 新增职责优先协作、成员协商转派、共享回报与无法解决升级主管规则
- 2026-08-12：§4 新增长驻成员重启优先 resume 原会话；provider 不兼容时备份、修正、测试 resume，必要时必须使用 qwen-codex-context-migrate skill 迁移上下文
- 2026-08-12：§4 新增主管拓扑引用规范，文档与逻辑使用稳定成员 id/角色，运行时窗口名只由 team_topology.json 解析

## 8. 组织架构（公共约束之一，2026-08-11 更新）

- **主管（SignL3）**：统筹/委派/dashboard/公共约束/人工介入队列，直接面向用户
- **平级协作原则**：视频（signL2）与语义动画（signL4）是**平级协作关系，没有上下层级**
- 所有常驻角色（signL2/signL4/signL5）**直接向主管汇报**；角色间协作平级协调（消息机制），不互相指派
- **运维（成员 id `signL8`，2026-08-12 新增）**：外部资源/API 测试与接入（大模型 API 连通性/能力测试、调用模板、.env 管理）；职责见 §9
- 新特化常驻角色：生成前必须询问用户意见
- 临时 sub：随时启动，无需常驻，不占名额
- **成员入队必要条件（2026-08-28 顾问注册时确认）**：每个正式成员进入 team 必须配置 **SSE member helper**（`daemon_team_member_helper_v2.py --role <role> --session-id <sid>`，setsid 保活）——helper 承担会话保活（防 idle 关闭）、事件记录（inbox）、健康上报（helper_health.json，看板/监督器依赖）。**无 helper 的成员视为未完成入队**（会因会话 idle 关闭导致失联）。helper 由 `daemon_team_message_services_v1.sh` 动态从 registry 读取角色启动（新角色注册 registry 后自动覆盖）；新成员入队检查清单：①registry 注册（manifest+topology）②helper 启动且 helper_health.json 正常 ③消息链路可达（mailbox 投递验证）

### 变更记录

- 2026-09-01：§4 新增「死循环自动监督机制」+ §16.3 登记「死循环监督 watchdog」——本地 AWQ4 量化模型（Qwen3.6-35B-A3B 等）易思考/输出死循环，上线常驻 watchdog 自动打断 + 按 ctx 余量（<20% 则 /compress）补发「继续完成」（Owner 要求）
- 2026-09-01：§4 新增「性能实测/对比必须写清模型型号」——凡模型性能/能力实测、两及以上对比、速测、评测、选型结论，必须用完整型号+架构+量化+model_id 标注被测模型，禁用"27b/35b"简写（顾问实测教训，Owner 要求写入，强制）
- 2026-09-01：§4 新增「本地模型服务说明：视觉可用性 + 智能路由」——所有本地模型经 11435 代理访问；视觉可用 27b（图表读值上偏需核对）与 35b（适合描述/OCR，读数值弱）；组合建议 + Qwen Code 前端注意（35b 未标"视觉可用"）+ 调用方式；链接智能路由主题文档与视觉对比记录（顾问实测）
- 2026-08-31：§3 新增「外网下载规范：zhuhai 无外网，须经 nature 中转」——zhuhai 拉外网资源（模型/仓库/pip 包/数据）必须先 nature 下载（**nature 直连外网即可，实测无需代理**）再 scp/rsync 推送，相关成员（运维/顾问/调研）务必遵循（Owner 要求，强制）。更正说明：初版误写"nature 依赖 :18080 代理"，经实测 nature 直连外网全部可达（github/hf/pypi/npm/google 200/301，openai 401=通），:18080 代理已不存在，已修正。
- 2026-08-31：§4「角色自认定规范」补强「主会话核实」机制——勿用子进程/后台 sub/side_task 继承的共享 env（QWEN_CODE_SESSION_ID）认身份（2026-08-31 本地A/顾问身份错乱四轮来回根因）；正确方法=主会话终端 `echo $QWEN_CODE_SESSION_ID` 或 `GET /session/:id/context` 读 displayName，反查 topology；勿用 hasActivePrompt 单点判断；两会话同源误读共享 env 发矛盾消息时以「主会话 session_id→拓扑」为准，不改拓扑（Owner 强调，强制）
- 2026-08-31：§4 新增「消息前缀辨识规则」——带【】前缀=team 成员间交互（须写清【发件人→收件人】【来自<来源>】）；**不带【】前缀的消息=Owner 直接交互**，按 Owner 指令/问答处理，不应当成团队消息（Owner 强调，强制）
- 2026-08-10：初版建立（安全/版本/zhuhai 资源/汇报/部署/数据六类约束）
- 2026-08-10：§8 组织架构加入（signL2/signL4 平级，直接向主管汇报）
- 2026-08-10：§9 职责边界与 dashboard 加入（overlay 审核细节隔离 signL2；主管统一维护 dashboard 全成员进度）
- 2026-08-11：§8 新增字幕员（signL6-subtitle，双语字幕制作）
- 2026-08-12：§8 新增宣传员（signL7-promoter，介绍面板中英双语制作）
- 2026-08-12：§8 新增运维（signL8-resource，外部 API 测试与接入）
- 2026-08-28：§8 新增顾问（advisor，技术顾问：daemon/看板/代理/本地模型运维支持 + 协调）+ 成员入队必要条件（helper 必须配置，无 helper 视为未完成入队）

## 9. 职责边界与 dashboard（2026-08-10 加入，用户确认）

- **语义视频审核细节隔离**：semantic overlay 等语义动画的审核流程细节（VL 审查、人工审核状态、优化反馈）仅在【signL4（制作方）+ 主管（SignL3）+ 用户】三方之间流转；**视频（signL2）不需要知道这些细节**，不参与 overlay 审核决策，也无需在 overlay 相关事项上主动推进/通知
- **部署执行**：overlay 审核通过后如需部署，由主管决定并给出明确指令；signL2 仅按主管指令执行部署动作（如复制文件/更新 manifest），不自行判断审核状态
- **主管维护 dashboard**：主管（SignL3）负责维护团队 dashboard（http://127.0.0.1:8450）记录**所有成员**（signL2/signL4/signL5）的进度状态；各角色按 §4 主动向主管同步进度/完成/异常，由主管统一汇总更新 dashboard；角色之间不得直接改动 dashboard 数据文件
- **运维职责（signL8-resource，2026-08-12 新增）**：负责外部资源/API 测试与接入 + **环境运维（2026-08-12 用户指示）**——模型/代理/服务的环境配置与切换（综合代理、GPT OAuth、模型切换测试、settings/环境维护）——大模型 API 连通性/可用性/能力（如视觉）测试，准备 api_base/api_key/model_name 调用模板（可入 settings.json provider），准备 .env 模板供用户填 key；测试结论落盘报告

### 变更记录

- 2026-08-10：§9 职责边界与 dashboard 加入（overlay 审核细节隔离 signL2；主管统一维护 dashboard 全成员进度）
- 2026-08-11：§9 新增字幕员职责（signL6-subtitle，双语字幕制作 + VL 视觉 QA）
- 2026-08-12：§9 新增宣传员职责（signL7-promoter，介绍面板中英双语 + VL 美化）
- 2026-08-12：§9 新增运维职责（signL8-resource，外部 API 测试与接入模板）

## 10. 部署/网页硬更新：开新端口绕开浏览器缓存（2026-08-11 加入，用户确认）

- **硬更新一律开新端口**：网页/静态资源部署内容发生"硬更新"（用户已打开过旧页面、或资源替换过）时，**必须新开端口**（如 8150 → 8151）提供服务——新端口 = 新 origin，浏览器按 origin 隔离缓存，用户直接访问即可看到最新内容，无需强刷/清缓存
- **配套 no-cache 服务**：新端口一律用无缓存 http.server 启动（/data/WYC/signLanguage/work/scripts/http_serve_no_cache.py，响应带 `Cache-Control: no-store, no-cache`），避免后续再踩缓存坑
- 旧端口可保留（已打开用户不受影响）；新端口地址同步告知用户
- 启动方式：`setsid nohup python3 /data/WYC/signLanguage/work/scripts/http_serve_no_cache.py <PORT> --directory <目录> > /tmp/serve<PORT>.log 2>&1 < /dev/null &`（保活 + 校验端口/标题/数据）

### 变更记录

- 2026-08-11：§10 部署/网页硬更新开新端口规范加入（用户确认）

## 11. 仓库职责边界：signLanguage 私有仓 vs sign-language-universe 公开仓（2026-08-12 加入，用户要求所有成员/sub 知晓）

**两个仓库的联系与区别**：

- **`/data/WYC/signLanguage`（私有研发仓）**：本地维护——处理原始用户视频、构建打分算法所需数据库、算法探索与实验（数据增强/模型训练/负例分类/语义树）、wan 转绘/overlay/字幕等生成管线、实验报告与私有文档。**内容不进公开仓库**
- **`/data/WYC/sign-language-universe`（开源产品仓）**：对应 GitHub `sign-language-universe`——成熟的手语学习应用（前端/后端/学习内容/打分模块/3D avatar），承载线上部署（GitHub Pages）与参考视频、模型（onnx）、介绍文档等公开资产

**联系**：功能/资源从 signLanguage 验证成熟后 → 抽取通用实现或脱敏资源 → 迁入 sign-language-universe → 走 PR 部署上线（含 GitHub Pages）

**区别与红线（所有成员与临时 sub 必须遵守）**：

1. 原始视频、姓名、可识别身份信息、未脱敏生物特征、私有数据库**只留 signLanguage**；禁止进入公开仓库（提交前检查 git 暂存文件与历史）
2. 公开仓库只接收**成熟可复用、经脱敏审计**的资源；实验性算法先本地验证再迁移，不直接同步整个目录
3. 前端演示优先 3D avatar / 合成资源，降低真人视频公开风险
4. 部署动作一律走 PR 流程（main 受保护）；涉及公开仓库的改动必须做脱敏检查后再提交

### 变更记录

- 2026-08-12：§11 仓库职责边界加入（双仓联系与区别 + 脱敏红线，用户要求全员知晓）

## 12. 服务器/环境与资源约束（2026-08-12 加入，用户要求所有成员/sub 知晓，防走弯路）

**服务器**：

- **nature（本机）**：主工作机，/data/WYC 下工作；Qwen Code 主进程 + 各成员 tmux 常驻
- **zhuhai（172.28.17.71:7712，user wuyangcheng，无 sudo）**：GPU 训练/推理服务器，10×A30 / 472G
- **edu（59.64.38.5:9000）**：教育服务器，本地大模型 API（Qwen3.6-27B-Coder 等，OpenAI 兼容 /v1）

**常用路径**：

- `/data/WYC/signLanguage`：私有研发仓（原始数据/算法实验/生成管线/报告）
- `/data/WYC/sign-language-universe`：开源产品仓（GitHub 部署，§11 边界）
- `/data/WYC/signLanguage/work/`：工作目录（`scripts/` 脚本、`reports/` 报告、`generated/` 产物）
- `/data/WYC/signLanguage/work/tools/`：工具包（字幕 skill 等）
- `/data/WYC/signLanguage/.team/`：团队管理（公共约束/日志/队列/dashboard）
- `/home/wuyangcheng/slu_train_20260809/`（zhuhai 训练 runs）、`/home/wuyangcheng/models/`（zhuhai 模型）

**Python 工作环境**：

- nature：conda（/opt/miniconda3）+ `~/.venvs/`；项目专用 venv（如 subtitle 流水线 `work/subtitle/venv/`）
- zhuhai：`miniforge3/envs/gen`（训练环境）；**vLLM INT4 弹性池**（g29=8050/2+9、g34=8051/3+4、g56=8052/5+6、g78=8053/7+8，OpenAI 兼容，自带视觉；qwen3-vl-8b VL 旧服务已停用不再使用 GPU9）
- 通用：`qwen`（Qwen Code）、`codex`（Codex CLI）；**禁止 rm/rmdir**（用 mv / python Path.unlink）

**zhuhai 资源使用约束（严格遵守，违反=踩坑）**：

1. **GPU1 一律禁止使用**（liuchang MATLAB 外部人员占用，任何情况不得使用）；**GPU0 仅限单卡服务（TP=1），需报主管协调**
2. **GPU9 已并入弹性池**（属 g29 槽位 GPU2+9；原 VL 视觉模型保留已取消，线上/本地模型自带视觉，不再单独预留 GPU9）
3. GPU2-9 可用；弹性池槽位 g29=2/9、g34=3/4、g56=5/6、g78=7/8，训练/推理按需使用
4. **CPU 限核（nice/taskset）**，优先保证 liuchang 不受影响
5. 无 sudo；zhuhai 外网直连慢（GitHub ~50KB/s、HuggingFace 更慢且不稳定），**外网资源下载（GitHub/HuggingFace/模型权重等）一律优先用 nature 本机中转**：nature 直连下载（~10MB/s 级；GFW 封锁站点走 `127.0.0.1:18080` 代理），完成后 scp 内网传到 zhuhai（2026-08-30 Owner 指示，由 GitHub 中转规则泛化）

**网络防弯路**：GFW——OpenAI/Google 等需代理 `127.0.0.1:18080`；DeepSeek/DashScope/GitHub 直连；教育网/内网 IP（59.64.x.x、172.28.x.x）直连测试

**GPT 切换规范（2026-08-12 用户确认，运维执行）**：

- 综合代理走通已确认；**统一默认模型 = `gpt-5.6-luna-chatgpt`（gpt-5.6-luna [ChatGPT]，effort=xhigh）**——用之前已有的模型调用 id（settings.json 的 gpt-5.6-luna-chatgpt provider），**不用临时加的『[本地代理] gpt-5.6-luna (GPT OAuth)』**
- 简单任务用 **medium 或 high effort** 即可（不必 xhigh）
- 切换方式：Qwen Code 会话 `/model gpt-5.6-luna-chatgpt`（配合 effort）；注意 envKey OPENAI_API_KEY 须非空占位（代理侧走 ChatGPT OAuth auth.gpt.json）
- 后续成员切换统一按此规范（等 signL2 测试完成统一切换）

**综合代理 stack 仓库（2026-08-12 加入，用户要求记录并告知运维）**：

- `/data/WYC/qwen-codex-gpt-deepseek-stack/`：**综合代理仓库**（Qwen Code / Codex 的 GPT+DeepSeek 综合代理，11435 端口，GPT 走 API key / OAuth，DeepSeek 走官方）
- `/home/wuyangcheng/codex-deepseek-proxy/`：综合代理**部署版**（main.py + service）
- 模型切换路线：综合代理 → gpt-5.6-luna（2026-08-12 恢复验证走通）；Qwen Code provider 的 **id 必须等于模型名**（否则 400）
- 环境运维（signL8）：涉及代理/模型切换先看此仓库与代理文档，不另起炉灶

**无头浏览器截图验证工具（nature 本机，2026-08-30 记录，全员/sub 复用）**：

- **chromium 可执行文件**：`/home/wuyangcheng/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome`（旧路径 `.../chrome-linux/` 已失效，用旧路径 launch 会失败）
- **调用方式**：项目验证脚本用 **subprocess 直接拉起 headless chrome + CDP**（`--remote-debugging-port`），再用 `websocket`（python `websocket-client`）走 CDP 抓取/执行 JS，**不是** playwright python API
- **防崩溃 flags（无 GPU 环境必加）**：`--headless --no-sandbox --disable-gpu --use-gl=swiftshader --disable-software-rasterizer=false --ignore-gpu-blocklist`——否则 WebGL（starCanvas 等）触发 GPU 进程崩溃（`Target page closed`）
- **示例脚本**：`/data/WYC/signLanguage/work/scripts/verify_8466_workstate_20260828.py`（真正可运行的完整模板）
- **常见坑**：无摄像头环境需 `page.addInitScript` 伪造 `navigator.mediaDevices.getUserMedia`；外部域名用 `page.route(/^(?!http:\/\/127\.0\.0\.1).*/, abort)` 拦截
- **依赖**：`websocket-client`（python）、node/playwright cache 在 `/home/wuyangcheng/.local` 与 `/home/wuyangcheng/.cache/ms-playwright`

**实测模型服务工具（skill: model-service-bench，2026-08-30 记录，全员/sub 复用）**：

- **skill 路径**：`/home/wuyangcheng/.qwen/skills/model-service-bench.md`（content.md 已索引，触发词：实测/benchmark/POC/灰度实测/A-B 对照）
- **用途**：验证模型服务配置变更（MTP 投机解码/量化/TP 并行/KV 类型/上下文长度）是否带来**真实收益**，避免"POC 好看但真实场景翻车"
- **核心方法论**：①A/B 对照（独立 daemon 槽位 + 同 prompt）②受控 POC（低熵基准，标注"最优场景非真实"）③真实高熵任务测试（多任务取中位数）④速率采样 + 真实活跃 decode 提取（任务时间窗切片 + decode>2 过滤）⑤POC vs 真实差异归因（MTP 加速比 ≈ (1+k)/(1+β)，k 由输出熵定、β 由上下文长度定）⑥图文并茂报告
- **参考脚本**：A/B 对照 `/data/WYC/mtp_test_tasks/`（start_daemons_4411_4422_v1.sh + analyze_active_decode_v1.py + task_boundaries.json）；受控 POC `/data/WYC/signLanguage/work/documents/zhuhai_qwen3_8_27b_deploy/bench_*.py`
- **3 个已验证案例**：①MTP A/B 对照（08-30，真实活跃 decode 中位数比 0.483）②MTP 灰度 POC（08-29，POC 91.2% vs 真实中文 ~71%）③dflash2/MTP POC（08-30，n=2 达标 + fp8 KV 根因）
- **关键坑**：POC 低熵≠真实高熵；全时段均值被 stale 污染（须任务窗切片+decode>2 过滤）；采样脚本列错位；QWEN_STREAM_MAX_LIFETIME_MS 须走环境变量设 0；分布形态差异大须用中位数
- **报告**：`/data/WYC/signLanguage/work/reports/mtp_ab_comparison_experiment_report_20260830.md` 等

**通用防弯路**：长任务后台运行（setsid nohup 保活 + 校验进程）；大计算必须带进度输出；本地 Web 服务只绑 127.0.0.1

### 变更记录

- 2026-08-12：§12 服务器/环境与资源约束加入（nature/zhuhai/edu、常用路径、Python 环境、zhuhai 资源规则、网络/通用防弯路，用户要求全员知晓）
- 2026-08-30：§12 补充"无头浏览器截图验证工具"小节（chromium 路径 + CDP subprocess 调用 + swiftshader 防崩溃 flags + 示例脚本 verify_8466_workstate），供全员/sub 复用，避免重复踩坑
- 2026-08-30：§12 补充"实测模型服务工具"小节（skill: model-service-bench，A/B 对照 + 受控 POC + 真实活跃 decode 提取 + 机制归因，3 个已验证案例），供全员/sub 复用

## 13. Daemon 团队管理 v1（与旧 TUI/tmux 共存）

- **双链路保留**：旧 TUI/tmux 监控脚本、旧 `team_health.json`、旧 dashboard 输出不删除、不覆盖；daemon 版本独立使用 `/data/WYC/signLanguage/.team/daemon_v1/` 与 `work/scripts/daemon_team_*.py`。
- **生产边界**：生产 daemon 当前以 `http://127.0.0.1:4194`、workspace `/data/WYC/signLanguage` 为准；`4180/4182/4192` 等测试实例不得写入生产 registry 或 dashboard。
- **稳定身份**：业务逻辑使用 `team_topology.json` 的稳定成员 id；daemon session ID 只从 `.team/daemon_migration_4194_manifest.json` 与 daemon API 实时核验。迁移旧 ID 与新 live ID 必须同时保留来源字段，不得把失效旧 ID 当作 live session。
- **session 归属**：workspace session 列表中的测试 session、side task、未登记 session 默认标记为 `unassigned`，不得自动纳入常驻成员卡；新增常驻成员需主管确认后更新 registry。
- **健康检测**：daemon 版使用 `/health`、`/capabilities`、`/daemon/status`、workspace sessions、`/session/:id/status`、`/session/:id/context`、`/session/:id/transcript`、SSE events 等结构化接口；不得复刻 tmux pane、双横线、状态栏文本猜测。
- **消息投递**：daemon 消息中心使用 `POST /session/:id/prompt`，写入独立 mailbox/archive JSONL，记录 queued/sent/failed 与 stopReason；禁止恢复已废弃的 `{team: ...}` 明文包协议。token、API key、完整敏感 prompt 不写入日志。
- **dashboard 适配**：daemon dashboard 只读 registry/health/mailbox 与旧 dashboard 的非 tmux 业务字段，输出独立 `daemon_v1/dashboard_data.json`；不得写旧 `data.json` 或复用旧 tmux runtime 字段。
- **服务与权限**：daemon 只允许 loopback；mutation/prompt 操作先核实 auth 与 session 目标，生产 session 投递需保留审计记录；健康采集默认只读、不得创建空 session 或调用昂贵 disk-scan endpoint 高频轮询。
- **sub 管理**：短期 side task 与长期独立 daemon session 分开记录 `parent_session/sub_session`；side task 不因出现在 workspace session 列表而自动成为常驻团队成员。
- **4194 重启规范（2026-08-29 加入）**：任何成员/主管/运维需要重启 4194 daemon（故障恢复/维护/配置生效），**必须使用外部触发入口** `bash /data/WYC/signLanguage/work/scripts/restart_daemon_4194_trigger.sh`，**禁止直接前台执行 `restart_daemon_4194_v3.sh`**。
  - **原因**：直接前台跑 v3 时，v3 进程跑在成员自己的终端里，一旦 SSH/tmux 断开，v3 会在 `② kill 旧 daemon` 后、`③ 启动新 daemon` 前被杀 → daemon 被杀掉却没重启，4194 挂死（2026-08-28 23:09、2026-08-29 02:11 两次事故根因）。
  - wrapper 用 `setsid --fork` 把 v3 整个脱离到独立会话，调用立即返回、不依赖成员终端存活；即使终端断开 v3 也会完整跑完（kill→启动→恢复模型→继续完成）。
  - 默认仅在 4194 端口未监听（已挂）时补启，不打扰健康运行；`--force` 强制重启（连接数异常堆积 etc.）。
  - 调用后查看执行结果：`tail -50 /data/WYC/signLanguage/work/logs/daemon_restart_4194.log`。

### 变更记录

- 2026-08-13：新增 §13 daemon 团队管理 v1，与旧 TUI/tmux 链路并存；明确生产 4194 边界、session 归属、结构化健康接口、独立消息与 dashboard 输出。
- 2026-08-29：新增「4194 重启规范」条目——成员必须用外部触发 wrapper（`restart_daemon_4194_trigger.sh`，setsid --fork 脱离），禁止直接前台执行 v3，修复"kill 后挂死"事故根因。
- 2026-08-30：§12 zhuhai 资源约束第 5 条泛化——外网资源下载（GitHub/HuggingFace/模型权重等）一律优先用 nature 本机中转（nature 直连 ~10MB/s，GFW 封锁站点走 127.0.0.1:18080 代理，完成后 scp 内网传 zhuhai）；由原「GitHub 中转」规则扩展（Owner 指示）。
- 2026-08-30：新增「消息前缀规范（必须无歧义）」条目——成员间/成员对主管消息前缀必须写清方向【发件人→收件人】（如【主管→运维】【运维→主管】），广播用【主管→全体】，回报用【<成员>→主管·回报】，紧急/更正叠加【紧急】【更正】；同步强化 `.qwen/rules/team_identity_profile.md`。
- 2026-08-30：`team_topology.json` 的 `roles[*]` 新增 `session_id` 字段（权威映射源=registry.json，会话重建时由主管同步更新），作为 daemon 时代身份主键，供成员按 session_id 确定性反查角色，防止跨会话身份错乱。
- 2026-08-30：§3 新增「所有本地模型部署在 zhuhai，不在本机」——团队所有本地模型服务（vLLM INT4 弹性池 g29/g34/g56/g78、llama.cpp 等）均部署在 zhuhai 服务器，不在 nature 本机；后续涉及本地模型部署/调研/换卡/速率测试一律按 zhuhai 卡位理解（Owner 确认）。

## 13.5 小模型（小上下文）场景健康检测规范（2026-08-25 加入，Owner 要求）

**背景**：团队会话切到小上下文模型（如 qwen3.8-27b，256K 窗口）后，context 超限报错（`prompt is too long` / `context length exceeded` / `context overflow` / `context oversized` 等）会让会话卡死在 turn error 状态；旧 tmux 版 `team_health_monitor.py` 只覆盖 tmux 窗口，daemon 迁移后覆盖不到 4194 上的团队会话。

**daemon 版常驻 watchdog（强制保活）**：

- 服务：`/data/WYC/signLanguage/work/scripts/daemon_context_watchdog_v1.py`，tmux 会话 `slu-team-context-watchdog` 运行（与 slu-team-health 同惯例；进程消失需运维重启）
- 监护对象：`.team/daemon_v1/registry.json` 全部团队角色会话（SignL3 + signL2..signL11）；**Jarvis（Owner 私人代理，channel 会话）是 team 外关联角色，不纳入团队健康检测名单**
- 状态/日志：`.team/daemon_v1/context_watchdog_state.json` / `context_watchdog.log`；告警追加 `.team/team_messages.log`（【自动健康告警】前缀）

**自动两级压缩（核心规范）**：

1. **被动自愈**：检测到会话 `hasTurnError` 且 transcript 尾部命中 context 超限标记、会话空闲 → 自动发送 **`/compress-fast`（无 AI 快速压缩）→ 等 turn 完成 → 再发 `/compress`（AI 摘要压缩）→ 等 turn 完成**。顺序不可颠倒：/compress-fast 本地剥离旧 tool 输出不需要模型调用，先把上下文降到 /compress 可执行范围，再让 AI 摘要
2. **主动自愈**：空闲会话 context 水位进入 **hard 档（≈窗口 91%+）** → 不等报错，立即执行同样两级压缩（下一个请求必然失败）
3. **冷却与熔断**：同一会话 10 分钟冷却防压缩死循环；1 小时内 3 次压缩无效 → 停止自愈，写入人工介入队列并告警主管；压缩失败/无效必须告警，不得静默重试
4. **会话失联自愈**：daemon 重启后会话未载入 runtime（status 404 但 workspace 列表仍在）→ 自动 `POST /session/:id/resume` 恢复（2026-08-25 本地B 实例）；列表也没有 → 告警"会话丢失"
5. **helper 失联**：`members/<role>/helper_health.json` 超 90s 未更新 → 告警运维重启 helper

**成员手动切换小模型规范**：

- 切到 qwen3.8-27b 等小上下文模型**前**，先看当前 context 使用量（`/context` 命令或 `GET /session/:id/context-usage`）；使用量 **>=50%** 时，必须先在原模型下完成 `/compress-fast` + `/compress`，确认回落到 50% 以下再切换（与 §4 GPT 切换规范同理，不得先切再压）
- 切换后若出现 `Upstream returned empty response` / 空响应 / context 类报错：保留现场并回报主管（由 watchdog 自动压缩或 signL8 处理），不得自行反复重试
- 小模型会话的长任务（大文件读取/批量工具调用）尽量分批，避免单轮 tool 输出把上下文顶穿

### 变更记录

- 2026-08-25：新增 §13.5 小模型场景健康检测规范（Owner 要求）——daemon 版 context watchdog 常驻、两级压缩顺序（compress-fast → compress）、hard 档主动压缩、冷却熔断、会话失联 resume 自愈、切小模型前 context 检查

## 14. 本地模型服务与 GPU 协调规范（2026-08-26 加入，Owner 要求）

**背景**：团队已切换到本地模型（Qwen3.8-27B Q4_K_M GGUF，llama.cpp，zhuhai 10×A30）为主力。常驻角色各有专属/弹性本地服务，GPU 与 liuchang 任务、训练任务共享，不协调会冲突（如弹性实例占 VL 卡、训练与弹性池抢 GPU0）。

**服务注册表（唯一事实源）**：

- `/data/WYC/signLanguage/.team/team_topology.json` 的 `local_model_services` 是本地模型服务唯一注册表（服务 id/别名/端口/GPU/ctx/类型/归属角色/状态）
- 拓扑中每个常驻角色的 `local_service` 字段标明其对应的本地服务
- **主管 + 运维共同维护**：任何服务变更（启停/换卡/换模型/改 ctx）由运维执行、主管确认后 24h 内更新注册表；成员不得私自改生产服务

**统一入口**：

- 所有本地模型调用走 nature 综合代理 `127.0.0.1:11435`（→ SSH 隧道 → zhuhai），禁止绕过 11435 直连 zhuhai 端口
- 长会话用静态模型名（保 prompt cache）；`qwen3.8-27b-q4-pool`（8018+8017 轮询）只用于临时短请求

**GPU 分配与冲突规则（zhuhai 10×A30 24GB）**：

1. **GPU1 一律禁止使用**（liuchang MATLAB 外部人员占用，任何情况不得使用）；**GPU0 仅限单卡服务（TP=1），需报主管协调**
2. **GPU2-9 = vLLM INT4 弹性池**（4×TP2 固定卡对槽位）：g29=GPU2+9(8050)、g34=GPU3+4(8051)、g56=GPU5+6(8052)、g78=GPU7+8(8053)——按需拉起/3h 空闲自动释放，OpenAI 兼容，**自带视觉**
3. **GPU9 不再给 VL 视觉模型预留**（2026-08-29 Owner 确认）：线上/本地模型均已自带视觉，qwen3-vl-8b VL 旧服务(Q端8000)已停用，GPU9 归入 g29 弹性槽位
4. 弹性实例**互斥保护**：启动时检测 GPU 显存 >500MiB 报 GPU_BUSY（避免抢占他人实例/训练）；训练前先 nvidia-smi 确认目标卡空闲
5. **训练/推理用卡前先查弹性池占用**（看板/健康状态），避免与 g29/g34/g56/g78 冲突；换卡按 §3 换卡规则先报主管
6. **CPU 限核（nice/taskset）**，优先保证 liuchang 不受影响

**槽位调度约束（2026-08-30 Owner 要求，强制）**：成员启动 sub / sub-session（或任何需要本地模型服务的长任务）前，**必须按以下顺序决策用哪个槽**，并用槽位监控工具核对，**不得随手直连某个端口/卡**：

1. **默认用自己的槽**：`team_topology.json` 的 `roles[].local_service` 指定的专属服务，若该服务运行中且有空闲槽 → 直接用。
2. **自己的槽满 / 未运行 → 用其他卡「运行中且有空闲槽」的服务**（负载最低优先）。
3. **都没有 → 找「空闲卡对」拉起新服务**（需经主管协调，遵守换卡纪律 §3）。
4. **全满且无空闲卡 → 等待释放 / 报主管**，不得抢占他人运行中槽位。

- **N=2 槽位模型**：每个 TP2 弹性服务（g29/g34/g56/g78）并发槽数 **N=2**（`--max-num-seqs 2`）；`空闲槽 = N − num_requests_running`（`num_requests_running` 取自 vLLM `/metrics` 真值，非看板缓存）。
- **槽位监控 = 检查工具**：`work/scripts/local_service_slot_monitor.py`（5s 常驻，setsid 保活）是槽位占用的**单一事实源 + 决策建议工具**。成员启动 sub 前**必须**用它核对——`python3 work/scripts/local_service_slot_monitor.py --once --for <成员名>` 直接给出该成员该用哪个槽（step1 自己的槽 / step2 其他卡空闲槽 / step3 空闲卡拉起 / step0 等待）。输出：`.team/daemon_v1/local_service_slot_state.json`（机器消费）+ `local_service_slot_status.md`（人类/看板可读）。
- **禁止**：绕过监控直连某端口/卡；抢占他人运行中槽位；全满时强行拉起（须先报主管协调）。

**维护职责**：

- **运维**：本地服务周期健康检查（弹性池 8050-8053 + GPU 显存 + 8096 监控），常驻实例失联/异常/僵死（端口 DOWN 但 GPU 显存高）即时告警主管；执行服务变更
- **vLLM/弹性服务清理红线（2026-08-29 事故后立，全成员必须遵守）**：清理任何本地 vLLM/弹性服务，**严禁 `pkill -f 'vllm.entrypoints.openai.api_server'` / `pkill -f 'vllm.entrypoints.openai.api_serve[r]'` 等"无端口限定"的宽模式命令**——`api_server` 是全部生产弹性槽位（g29/g34/g56/g78）公共的进程签名，用这种模式会**一次误杀所有生产的 API server**（2026-08-29 06:47 运维用 `pkill -9 -f 'vllm.entrypoints.openai.api_serve[r]'` 清理 POC 测试的 8093，实际 kill 了 g29/g56/g78 三个生产 api_server，导致 4 个槽位僵死、API 全挂、主管播报卡住未处理）。**正确清理方式**：①用 `bash /tmp/elastic_stop_vllm.sh <port>`（按端口精确定位，幂等）；②或用 `ss -tlnp | grep :<port>` 精确取 PID 再 kill；③确需 pkill 时必须**带端口限定**（如 `pkill -f "vllm.entrypoints.openai.api_server.*port 8093"`）且先 `pgrep -f` 核对匹配列表确认只含目标，防止自匹配到 ssh 会话。POC 测试后必须清理 orphaned worker（PPID=1 的 VLLM::Worker，用 `pgrep 'VLLM::Worke[r]' | awk '$2==1'` 定位后按进程组 kill），避免占 GPU 导致对应槽位 GPU_BUSY。**区分"清理"与"停用"**：`kill`/`elastic_stop_vllm.sh` 只是**临时清**（清残留/事后清理），会被僵死自愈重新拉起；若要**长期停用**某槽位（不希望它被再次拉起），必须在 `team_topology.json` / 代理 `LOCAL_ELASTIC` 里把该槽位设为 **`disabled`（或移除）**，而不是只 kill 进程——否则代理下次请求该槽位时会经 `_elastic_ensure` 把它当作"僵死"重新拉起。
- **主管**：冲突协调（训练 vs 弹性池）、维护拓扑注册表、向 Owner 汇报服务格局与异常

### 变更记录

- 2026-08-26：新增 §14 本地模型服务与 GPU 协调规范（Owner 要求）——拓扑加入 local_model_services 注册表 + 角色 local_service 字段；统一入口 11435；GPU 分配与冲突规则（GPU1 严禁 / 5+6 本地A / 7+8 本地B / 9 VL 与弹性互斥 / 0,2,3,4 弹性与训练共享）；主管+运维共同维护
- 2026-08-29：§14 + §3 GPU 格局更新为 vLLM INT4 弹性池（g29=2+9、g34=3+4、g56=5+6、g78=7+8）；**GPU9 不再给 VL 视觉模型预留**（线上/本地模型自带视觉，qwen3-vl-8b 旧服务停用）；GPU0/1 均被外人占用一律禁用；取代旧"GPU5+6/7+8 专属、GPU9=VL、q4-lite 互斥"等过时表述
- 2026-08-29：新增「vLLM/弹性服务清理红线」——严禁 `pkill -f 'vllm.entrypoints.openai.api_server'` 等无端口限定宽模式清理（会一次误杀全部生产 API server，2026-08-29 06:47 真事故）；正确用 `elastic_stop_vllm.sh <port>` / 端口精确 PID / 带端口限定的 pkill；POC 后必须清 orphaned worker（PPID=1 的 VLLM::Worker）。同时修正此前"僵死死因=上下文超限"的错误结论——真根因是运维 pkill 误杀生产 api_server + POC 的 8093 崩溃留 orphaned worker，非上下文超限。
- 2026-08-29（清理红线补充）：新增"清理 vs 停用"语义边界——`kill`/`elastic_stop_vllm.sh` 只是临时清（会被僵死自愈重新拉起）；长期停用某槽位必须设 `disabled`（team_topology/LOCAL_ELASTIC）而非仅 kill 进程。
- 2026-08-30：新增「槽位调度约束」——成员启动 sub/sub-session 前必须按「自己的槽 → 其他卡空闲槽（负载最低优先）→ 空闲卡拉起（需主管协调）→ 等待/报主管」顺序决策用槽，并用 `local_service_slot_monitor.py`（N=2 槽位模型，`--once --for <成员>` 直接给决策）核对；禁止绕过监控直连端口/卡、抢占他人运行中槽位（Owner 要求）。
- 2026-08-31：§14 新增「本地模型服务接入与排障关键细节」子节（运维维护，附 team 维护说明+部署文档链接）——沉淀新增本地模型/排查本地服务问题的操作细节：①新模型必须登记 topology 才进看板 ②综合代理 local_url 不带 /v1（否则 health 打到 /v1/health 永远失败→503）③本地模型统一由综合代理托管不手动拉起 ④daemon 模型清单启动时缓存、新增模型需重启 daemon 才切会话 ⑤走 vLLM reason-parser qwen3 的模型必须流式透传（否则 _ThinkStreamProcessor 缓冲致 decode 有/会话无输出）⑥深度思考默认开的模型（35B）需强制注入 enable_thinking=false ⑦--max-num-seqs 自动显示 ⑧看板 8466 启动必须在 work/scripts 目录（同目录 import daemon_auth_v1）。背景：智能路由切主管到 Qwen3.6-35B-A3B 时踩的坑
- 2026-08-31（tool-call 兼容性复核修正，顾问 live 终验）：§3 原「30B/35B 一律 hermes」表述已更正为**区分两者**——仅 30B-A3B（Qwen3 早系）需 `--tool-call-parser hermes`；**35B-A3B（Qwen3.6-35B-A3B）用 `qwen3_xml` 直接输出原生 tool_calls，无需换 parser**（实测 GPU3+4/8071 finish=tool_calls）。严禁把 35B 也一律套 hermes。详见 `advisor_toolcall_compat_report_20260831_v1.md`。

**本地模型服务接入与排障关键细节（2026-08-31 起累积，运维维护——新增本地模型或排查本地服务问题必读）**：

> **team 维护说明**：本小节由**运维**维护（新增本地模型/排查本地服务问题的操作细节），主管知悉。详细部署方案与架构对比见运维文档：
> - 35B 部署方案：`/data/WYC/signLanguage/work/documents/local_model_eval/local_model_qwen36_35b_a3b_deploy_v1_20260831.md`（含模型/量化/框架/硬件口径、TP=2 下 7.2×128K 槽数、qwen3.6/qwen3.5/qwen3.8 三列架构对比、总参vs激活参辨析）
>
> 运维处理本地模型服务问题时，应及时把新踩坑/新机制**追加到本小节**（边做边记），供主管与其他成员参考。

1. **新增本地模型必须登记 topology 才进看板**：8466「本地模型服务」板块读巡检文件，巡检脚本从 `topology.local_model_services.services`（type=elastic/vl-8b）读端口清单探测。8096 会**自动发现**所有实例，但看板 services 卡片只显示 topology 登记的端口。**新模型不登记 topology → 看板不显示**。

2. **综合代理 local_url 不能带 `/v1`**：`LOCAL_ELASTIC` 条目的 `local_url` 必须不带 `/v1`（`_elastic_health` 拼 `+/health`，转发拼 `+/v1`）。带 `/v1` 会让 health 打到不存在的 `/v1/health` 永远失败 → 反复 503 `elastic instance failed to start`。

3. **本地模型服务统一由综合代理托管，不手动拉起**：手动拉起与综合代理 `_elastic_ensure` 弹性检测会抢卡冲突（它 health 检测失败会 GPU_BUSY/僵死清理并重新拉起 → 循环换进程）。让综合代理自动拉起（它检测 GPU 空闲 → 启动 → 轮询 health 至就绪）。

4. **daemon 模型清单是启动时缓存**：新增模型到 settings.json 后，**daemon（4194）不认识新模型**（`Model 'X' not found`），需重启 daemon（走外部 trigger `restart_daemon_4194_trigger.sh --force`）才注册。**新增本地模型接入后需重启 daemon 才能切会话使用。**

5. **vLLM `--reasoning-parser qwen3` 的模型必须走流式"透传"**（综合代理 `_handle_local_backend`）：综合代理流式分支用一个 `_ThinkStreamProcessor`（把 content 在 `</think>` 处拆分思考/正文），只对**非 qwen3.8/glm** 前缀启用。走 vLLM `reasoning_parser qwen3` 的模型（qwen3.8 / qwen3.6-35b / glm）**原生输出 content、无 `</think>` 标记**，若被 `_ThinkStreamProcessor` 处理会把 content 缓冲到流结束 → **Qwen Code 收不到正文（decode 有、会话无输出）**。**新增走 qwen3 解析器的模型必须在综合代理判断里加前缀透传**（`model.startswith("qwen3.8") or "glm" or "qwen3.6" or "35b"`）。

6. **深度思考模型（如 35B）恢复默认思考 + 保证预算**：35B `chat template enable_thinking` 默认 true（深度思考）。**不要禁 thinking**——开 thinking + 预算够时"思考+正文"都正常（实测 reasoning 3569 + content 1729）；预算不够（<3000）时 thinking 吃光→content 空（这是预算问题，非模型问题）。**只需保证流式透传正确（见第⑤条）+ 预算足够**（Qwen Code 主管请求 max_tokens=64000 足够），即可让 35B 深度思考 + 正常出正文。**教训：此前把"content 空"误判为"35B 思考不受控需禁 thinking"，实际是流式透传 bug 未修 + 测试预算太小所致**。

7. **`--max-num-seqs`（并发槽）自动显示**：8096 监控 `_proc_max_num_seqs` 从 `/proc/cmdline` 解析 `--max-num-seqs` → 看板"并发N=x"小字自动显示，无需手工维护。

8. **看板 8466 启动必须在 `work/scripts` 目录**（`daemon_team_console_v2_server.py` `from daemon_auth_v1 import` 是**同目录 import**）：若用 `/tmp/dbg_*.py` 之类入口跑，PYTHONPATH 不含 scripts → `ModuleNotFoundError: daemon_auth_v1` → 崩。正确启动：`cd work/scripts && setsid nohup python3 -u daemon_team_console_v2_server.py --host 127.0.0.1 --port 8466 ...`。

## 15. 团队进度监督与 Owner 及时汇报机制（2026-08-26 加入，Owner 要求）

**架构（Owner 确认）**：自动化监督 → 进展文件（单一事实源）→ **直调微信 iLink Bot API 推送 Owner**（零 LLM，秒级）。**主管 LLM 不在进展信息链路上**（避免多余中转），只负责维护监督脚本与异常处理。

- **监督脚本**：`work/scripts/team_progress_supervisor_v2.py`（v1 保留便于回滚），tmux 保活 `slu-team-progress-supervisor`（崩溃重启循环 `work/scripts/run_supervisor_v2_loop.sh`），30s 周期，纯规则化（监督路径零 LLM 依赖）。
  - **v2 修复（2026-08-27）**：新增 `PENDING_STALE_TTL=1800s` 陈旧过期——pending 队列中超过 30 分钟未推送成功的事件直接丢弃不补推。根因：iLink 短暂故障（HTTP 200 但 ret=-2）后积压的数小时前旧事件按优先级排在队首被逐条"补推"，GLOBAL_CAP=8/600s 排空 100+ 条积压需数小时，期间新进展被堵、latest_progress.md「⏳ 未汇报新进展」节被旧 error 占满误导 Owner。旧事件审计留痕在 `<role>_progress.jsonl`。
- **监督对象**：registry 全部常驻角色会话（含主管自身，但主管不通报——Owner 与主管直接对话）。
- **事件类型**：接到任务 / 回合完成 / 回合取消 / 出错 / 等待人工输入 / 进展（10 分钟/角色节流）/ 疑似卡住（进行中 15 分钟无输出增长）。
- **进展文件**：`.team/daemon_v1/progress_supervisor/latest_progress.md`（⏳ 未汇报新进展 / 各角色当前状态 / 进展历史）。推送成功后移入历史。
- **推送协议**：有新进展时 `weixin_push.py` 直调 `POST https://ilinkai.weixin.qq.com/ilink/bot/sendmessage` 推送到 Owner 微信（**不经 Jarvis 模型、不经 channel 会话**）。每周期最多 1 次推送；全局上限 600s 内 8 条事件；推送失败 pending 保留下轮重试。
  - 推送模块：`work/scripts/weixin_push.py`；凭证自动读 `~/.qwen/channels/weixin/account.json`（token）；Owner chatId 自动解析自 `~/.qwen/channels/daemon/<hash>/routes.json`。
  - 独立用法：`python3 work/scripts/weixin_push.py "消息"` / `--test`。
  - **微信 iLink 双 token 机制与 ret:-2 根因（2026-08-30 实测落盘，修正 2026-08-28 的"40 分钟/Bot token 过期"表述）**：主动推送涉及**两个不同的 token**，必须区分，否则会误诊（调研曾误判"Bot token 16 天过期需重新扫码"，实测证伪）：
    - **① Bot 鉴权 token**（`~/.qwen/channels/weixin/account.json` 的 `token` 字段，Owner 扫码登录 iLink Bot 时签发）：**长期有效**。2026-08-30 实测——16 天前（2026-08-14）签发的 token 在 23:11/23:21 仍成功推送（ret=None）。**它不是 `ret:-2` 的根因**；出现 ret:-2 时**不要**误判为"Bot token 过期需重新扫码"。
    - **② context_token（会话能力令牌）**（`~/.qwen/channels/weixin/context_tokens.json`）：**短时效**，**仅**从入站用户消息获得（Owner 给微信 channel 发消息时，channel worker 捕获并持久化），**无任何主动刷新/续期端点**（iLink 全部 7 个端点无心跳/保活/刷新类；getconfig/getupdates 均不刷新 token）。**这才是 `ret:-2 prepare failed` 的真正根因**。
    - **宽限窗口（2026-08-30 probe 实测，10min 间隔）**：context_token 于 23:01 捕获（Owner 发消息）后——token_age 10min（23:11）✅成功 / 20min（23:21）✅成功 / 30min（23:31）❌ret:-2 / 40min（23:41）❌ / 49min（23:50 主管手动测试）❌。**结论：可用窗口约 20-30 分钟**（比 2026-08-28 记录的"40 分钟"更紧；官方口径 24h 会话窗口，但实测 context_token 层更短）。
    - **正确处置（出现 ret:-2 prepare failed 时）**：让 **Owner 给微信 channel 发任意一条消息**（刷新 context_token + 会话窗口），之后 ~20-30 分钟内主动推送恢复；**不是**重新扫码刷新 Bot token。属**预期行为**（Owner 长时间未互动），**非链路故障**。
    - **对推送链路的影响**：weixin_push.py / weixin_intervention.py / 监督器自动推送均依赖新鲜 context_token；Owner 长时间（>30min）未给微信 channel 发消息时，主动推送会失败（ret:-2），监督器（`weixin_push_probe_v1.py`）持续探测，Owner 下次发消息后自动恢复。长期方案（可选）：企业微信应用消息 / 群机器人 webhook（无会话窗口限制，详见 `work/reports/ilink_context_token_research_20260828.md` §4）。
    - 详见 `work/reports/ilink_context_token_research_20260828.md`（机制调研）与 `.team/daemon_v1/weixin_push_probe_state.json`（实测证据，逐轮 ret/tokenless_ret）。
- **v1 历史**：2026-08-26 上线时为「轻推 Jarvis → Jarvis 读文件汇报」；因本地模型慢/卡导致转达不可靠，同日升级 v2 直推（Owner 微信实测确认收到）。
- **Jarvis 手动转达（2026-08-26 补充）**：成员主动发【转达】/【请转告 Owner】/【汇报 Owner】类消息给 Jarvis 时，Jarvis 调用 `weixin_push.py` 直推微信（不依赖 channel 回复路由）。协议写入 settings.json weixin `instructions`（新会话）+ Jarvis 会话注入（已有会话）；skill 见 `~/.qwen/skills/jarvis-forward-owner.md`；已验证（HTTP 200 message_id，Owner 收到）。
- **Jarvis 转达协议**：持久化于 `QWEN.md §6`（防上下文压缩丢失）。Jarvis 仍用于「Owner 主动在微信提问 → 回复」的 channel 闭环；**进展推送不再依赖 Jarvis**。
- **选择题/权限自动提交（2026-08-26 加入，免 LLM；2026-08-30 扩展自由文本）**：监督器检测到成员挂起提问（ask_user_question/permission）时，持久化结构化数据到 `.team/daemon_v1/progress_supervisor/waiting_requests.json`（requestId/options/answer_key/submit_option_id）并立即推送微信（新 requestId 不受 5 分钟抑制）；Owner 微信回复 → Jarvis 直接调 `weixin_option_reply.py` 提交，支持三种回复：①「选N」/纯数字（user_question：optionId=proceed_once + answers={answerKey:label}；permission：选项 optionId）②「取消」③**自由文本（2026-08-30 新增，`--text "..."`，仅 user_question 类型，permission 不支持）**——把文本作为自定义答案写入 answers={answerKey: text}。提交前复查 requestId 仍在 pendingInteractions（过期返回 2），成功后置 waiting_requests.json 状态为 submitted。端到端 3/3 实测通过（报告 `work/reports/jarvis_ask_question_auto_reply_test_20260830.md`）。
- **成员主动介入推送（2026-08-26 加入）**：成员需 Owner 人工介入/决策时直接运行 `python3 work/scripts/weixin_intervention.py "内容"` 秒级推送微信（【人工介入】成员名：内容，角色名自动从 tmux 窗口名识别），不经监督器轮询。
- **审计**：`.team/daemon_v1/progress_supervisor/notifications.jsonl`（每次推送的 HTTP 结果与事件清单）；每角色事件历史 `<role>_progress.jsonl`。
- **维护职责**：主管负责脚本维护/调参/异常处理；脚本崩溃由 tmux while 循环自动重启；链路故障（凭证失效/weixin 断连）由 context watchdog 与 daemon channel 健康机制覆盖，主管介入恢复。

### 变更记录

- 2026-08-26：新增 §15 团队进度监督与 Owner 及时汇报机制（Owner 要求）——自动化监督 + 进展文件 + Jarvis 轻推转达；主管 LLM 退出信息链路
- 2026-08-26（同日升级 v2）：进展推送改为 `weixin_push.py` 直调微信 iLink Bot API（零 LLM 秒级），不再经 Jarvis 模型；新增凭证/chatId 自动读取与独立推送脚本；Owner 微信实测确认收到
- 2026-08-26（v2 补充）：Jarvis 手动转达链路——成员【转达】消息经 Jarvis 调用 weixin_push 直推微信；协议写入 channel instructions + Jarvis 会话 + skill；实测 HTTP 200 送达
- 2026-08-26（v3 补充）：微信链路修复（context_token 持久化 + ret 字段判定，18:38-22:00 推送实际失败被误判成功的问题）+ 选择题自动提交（weixin_option_reply.py，免 LLM）+ 成员主动介入推送（weixin_intervention.py）——三项均端到端实测通过
- 2026-08-30：`weixin_option_reply.py` 扩展自由文本回复（v2，`--text "..."`，仅 user_question 类型，permission 不支持）——Owner 微信除「选N/取消」外可直接输入自定义答案；端到端 3/3 实测通过（一次性测试会话，未碰真实成员会话，报告 `work/reports/jarvis_ask_question_auto_reply_test_20260830.md`）
- 2026-08-30：**微信 iLink 双 token 机制实测落盘（公共事实）**——区分 Bot 鉴权 token（account.json，长期有效，16 天前签发仍可用）与 context_token（context_tokens.json，仅入站消息刷新、无主动续期端点、实测宽限约 20-30min）；`ret:-2 prepare failed` 根因是 **context_token 过期**（Owner 长时间未给微信 channel 发消息），**非** Bot token 过期。处置：Owner 发任意一条微信消息即刷新，~20-30min 内推送恢复。修正 2026-08-28 的"40 分钟"与调研误判"Bot token 过期需重新扫码"（实测证伪，probe 逐轮证据见 `.team/daemon_v1/weixin_push_probe_state.json`）

## 16. 团队工具目录（2026-08-31 加入，Owner 要求，全成员必须知晓）

**目的**：把团队共用的自动化工具集中登记在一处，方便任何成员 / sub 快速发现与调用。**新增团队工具必须登记到本目录**（主管维护）。

### 16.1 本地模型服务槽位查询（启动 sub / sub-session 前必查）

- **用途**：查看 zhuhai 本地模型服务（vLLM INT4 弹性池）各槽的实际占用（每 TP2 服务 N=2 并发槽），决定「启动 sub / sub-session 前该用哪个槽」。
- **单一事实源**：`work/scripts/local_service_slot_monitor.py`（5s 高刷新常驻，setsid 保活）。
  - 自动写入：`.team/daemon_v1/local_service_slot_state.json`（机器消费）+ `local_service_slot_status.md`（人类/看板可读）。
- **成员查询方式（三选一）**：
  1. **CLI（推荐，直接给决策）**：`python3 work/scripts/local_service_slot_monitor.py --once --for <成员名>` → 直接输出「该成员该用哪个槽」（step1 自己的槽 / step2 其他卡空闲槽 / step3 空闲卡拉起 / step0 等待）。
  2. **HTTP 接口（8466 看板）**：`curl http://127.0.0.1:8466/api/local/slots` → JSON（`summary` 精简摘要 + `snapshot` 完整快照）。
  3. **看板页面**：8466 控制台「成员用卡 / 槽位」区块（读同一份 `local_service_slot_state.json`）。
- **决策顺序（强制，见 §14 槽位调度约束）**：自己的槽 → 其他卡运行中空闲槽（负载最低优先）→ 空闲卡对拉起（需主管协调）→ 全满等待/报主管。**禁止**绕过监控直连端口/卡、抢占他人运行中槽位。

### 16.2 成员进展文件 + 进展消息队列（自动汇总推送 Owner 微信）

- **用途**：每个成员自维护一份进展文件，轮询器增量抓取新增条目入队，唤醒 Jarvis 时自动把「未推送进展」汇总推送到 Owner 微信（零 LLM），推送后从队列移除（不重复推送）。
- **成员自维护进展文件**：`.team/member_progress/<角色id>.md`（追加式，格式 `- [HH:MM] 内容`）。规范见 `.team/member_progress/README.md`。**每个成员都要维护自己的文件**，关键进展及时追加。
- **轮询器**：`work/scripts/member_progress_poller_v1.py`（30s 轮询，按字节 offset 增量读，`dedup_key` 防重复）。
  - 入队：`.team/daemon_v1/progress_supervisor/progress_queue.jsonl`（未推送项）。
  - 看板快照：`.team/dashboard/progress_queue.json`（8450 看板「进展消息队列」区块读取）。
- **推送脚本**：`work/scripts/push_pending_progress.py`（Owner 唤醒 Jarvis 时触发，`weixin_push.py` 零 LLM 直推，成功后从队列移除并记入 `progress_pushed.jsonl` 审计）。
  - 手动/预览：`python3 work/scripts/push_pending_progress.py --dry-run`。
- **去重**：`dedup_key = sha1(角色|内容)`，队列与已推送审计中已存在的不再入队/推送。
- **与 §15 监督器的关系**：§15 是「自动监督 + 实时直推」（自动事件）；本节是「成员自维护进展文件 + 唤醒时汇总推送」（成员主动记录的重要进展）。两者互补，不重复。

### 16.3 其他团队工具（登记）

- **微信推送**：`work/scripts/weixin_push.py`（零 LLM 直推 Owner 微信，见 §15）。
- **人工介入**：`work/scripts/weixin_intervention.py`（成员需 Owner 决策时秒级推送，见 §15）。
- **选择题/权限自动提交**：`work/scripts/weixin_option_reply.py`（Owner 微信回复「选N/取消/自由文本」自动提交，见 §15）。
- **4194 daemon 重启**：`work/scripts/restart_daemon_4194_trigger.sh`（外部触发入口，见 §13）。
- **弹性 vLLM 清理**：`bash /tmp/elastic_stop_vllm.sh <port>`（按端口精确清理，见 §14 清理红线）。
- **死循环监督 watchdog（2026-09-01 新增，全成员自动监督）**：`work/scripts/daemon_loop_watchdog_v1.py`（常驻进程，setsid 保活）。检测本地 AWQ4 量化模型（如 Qwen3.6-35B-A3B）的"思考/输出死循环"，自动打断 + 按 ctx 余量决定是否 /compress，再补发「继续完成」。
  - 机制：读 transcript 尾部提取最近 model 消息正文（`parts[].text`），连续 `REPEAT_WINDOW=3` 条高度相似（`SIMILARITY_THRESHOLD=0.90`、最后一条 ≥120 字）判为死循环 → `POST /session/:id/cancel` 打断 → 查 `context-usage`，余量 <`CONTEXT_LOW_RATIO=0.20`(20%) 则先 `/compress` 再发「继续完成」，否则直接发「继续完成」。
  - 冷却：同一会话 120s 防反复打断；1h 内触发 3 次转人工介入队列。
  - 状态：`.team/daemon_v1/loop_watchdog_state.json` + `loop_watchdog.log`；告警写 `team_messages.log`。
  - 运维/调试：`python3 work/scripts/daemon_loop_watchdog_v1.py --once`（单周期）/ `--dry-run`（只检测不执行）/ `--only <角色>`（单角色）。

### 变更记录

- 2026-08-31：新增 §16 团队工具目录（Owner 要求）——集中登记团队共用工具（槽位查询 + 进展机制 + 微信推送/介入/提交 + 4194 重启 + 弹性清理），方便全成员/sub 快速发现与调用；8466 看板新增 `/api/local/slots` 槽位查询接口（读 `local_service_slot_monitor.py` 5s 高刷新快照）。
- **2026-08-31：【重大安全反例·存档】** 调研任务线启动 Qwen3-30B-A3B 测速实例，因**漏设 `CUDA_VISIBLE_DEVICES`** 导致 vLLM 默认占用 **GPU0/1（团队禁用卡）**，同时 `host=0.0.0.0` 暴露、**未报主管协调**、`served_model_name` 伪造（名 qwen3.8-27b 实载 Qwen3-30B-A3B）。Owner 判定为重大安全问题，已按「§3 本地 vLLM 启动强制规范」新增 7 条强制条款（必设卡对 / 只绑 127.0.0.1 / 不动 GPU0/1 / 报主管 / served 一致 / 端口精确停 / 仅用标准模板）。**反例特征**：日志 tag=`g34_qwen3_30b_notool`、引擎 pid 2237065、2026-08-31 10:43 启动、本意 g34(3+4) 实落 GPU0/1。已投递调研(signL9) 整改（message_id `2e77a3e3`，2026-08-31 07:42Z）。
- 2026-08-31：§3 + §14 GPU 约束更新——**GPU0 恢复可用（仅限单卡 TP=1 服务，需报主管协调）**，GPU1 仍禁用（liuchang MATLAB）；现有 TP=2 弹性池布局（g29/g34/g56/g78）不变，GPU0 不纳入 TP2 弹性池。Owner 协调确认后生效。
- 2026-08-31：§4 新增「角色自认定（身份确认）规范」——成员身份认定首选系统提示词注入（`.qwen/rules/team_identity_profile.md` + `.team/roles/<id>.md`），兜底用 daemon session_id 在 `team_topology.json` 反查；严禁凭消息前缀/收件人/共享记忆认定身份。同时修复 §13 位置错乱（原在 §15 之后，现移至 §13.5 之前）。
- 2026-09-01：§3 新增「僵死自愈判定必须含端口校验」红线——`_kill_stale_elastic_workers` 仅按 GPU 对匹配进程组，误杀同卡组 35b（g29 卡组 27b=8050 已释放 / 35b=8070 运行，共享 GPU2,9），修复为 GPU 对 + `--port == 槽位端口` 双重校验；联动为代理 `_handle_local_backend` 补 finish_reason 防护（IncompleteRead 断流补发）。详见 `work/documents/intelligent_router/intelligent_router_v1_20260901.md`。

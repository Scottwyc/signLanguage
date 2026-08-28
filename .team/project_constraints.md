# 项目公共约束（signLanguage 手语打分项目）

> 维护者：主管人（SignL3）｜所有常驻 agent（signL2/signL4/signL5）与临时 sub 必须遵守
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

- **GPU1 始终避开**（liuchang 的 MATLAB 在用）
- **GPU9 已腾出**给视觉模型部署（qwen3-vl-8b vLLM http://172.28.17.71:8000）——训练勿占，VL 标注/复核可用
- **GPU0**：训练默认（空闲时）；GPU 2/3/4 按需（wan 服务停用后空闲可复用）
- **CPU 约束**：控制 CPU 使用，优先保证 liuchang 任务；大计算限核数（如 onnx 推理 intra_op_num_threads=2）
- **显存**：训练前 `nvidia-smi` 确认 GPU 空闲；模型 <200MB 显存占用可与其他任务共存
- **训练规范**：zhuhai `/home/wuyangcheng/slu_train_20260809/`（数据+脚本副本+ runs/）；训练命令 `setsid nohup` 保活 + 日志落盘 + 30-60s 检查
- **资源冲突**：发现 GPU 被占/冲突 → 主管协调（不抢占他人任务）
- **换卡必须经主管协调（2026-08-13 用户确认，强制）**：任何成员（含运维、算法员、视频负责人）提出"换卡/换 GPU/换机器调用"建议时，必须先向主管说明理由与目标卡位；**真正执行换卡操作前必须通知主管，由主管协调显卡分配**，避免多任务抢卡、与 liuchang/vLLM/其他成员任务冲突。**严禁成员内部自行换卡**；换卡后回报实际占用卡号与占用情况。此条适用所有 GPU 任务（训练/推理/转绘/视觉服务）。
- **算法员训练 × wan 后端显卡互斥（2026-08-13 用户确认，重点）**：算法员（signL5）的训练任务与 wan 后端（signL2）的转绘推理是目前 GPU 占用最大的两条线，必须**内部互相协调显卡使用**：
  1. 各自开训/迁移前，先查对方当前占用与计划（看板/健康状态/确认通道），避免同时抢占同一批卡；
  2. 使用卡位前先向主管报计划（卡号区间+预计时长），主管确认无冲突后执行；
  3. 训练与转绘如需共享卡位，按"短任务让长任务、转绘 job 密集时段让训练错峰"原则协商，协商不成报主管定夺；
  4. 任何一方换卡/扩卡/停卡都必须通知另一方 + 回报主管，防止 GPU5-8（wan）与 GPU0-4（训练/通用）串扰；
  5. 冲突一旦发生，先停新任务、保留进行中任务，立即报告主管协调，不互相强杀。

## 4. 汇报与协作规范

- **完成/异常/里程碑主动后台通知主管**（tmux 消息格式：`【主管】...` / `【人工介入请求】窗口: | 任务: | 路径:`）
- **成员确认走后台通道**：成员对主管通知/约束/指令的确认，**追加一行到 `/data/WYC/signLanguage/.team/team_confirmations.log`**（格式：`【成员确认】窗口:xxx | 事项:xxx | 内容:xxx`），由 monitor 后台扫描转发到 team_messages.log 并提醒主管；**不通过前台 prompt 消息打扰/打断**（主管后台读取 monitor 日志获知即可）
- **用户在场宽限（人工介入免打扰）**：用户可直接与各成员交互；成员须在**每次收到用户直接输入**（消息不带【】agent 间标志）时，把当前 ISO 时间写入 `/data/WYC/signLanguage/.team/user_last_interaction/<成员id>.txt`（成员 id 从 `team_topology.json` 读取；运行时窗口名由拓扑解析）。成员发【人工介入请求】时，monitor 判断：若距该成员最近一次用户直接输入 **< 8 分钟**（阈值可调 `--user-grace-minutes`，2026-08-11 由 5 调至 8）→ 判定用户正在该成员处交互 → **仅入队、不提醒主管**；超过则正常入队提醒主管
- **主管转达规则（宽限联动）**：monitor 捕获成员消息时，若该成员距用户最近直接输入 < 8 分钟，日志行标注【用户在场-免转达】；主管读到此类标记或查 `user_last_interaction` 确认用户正在该成员处交互时，**不主动转达该成员消息**（用户正与该成员直接交互，从窗口可见），仅记录；宽限期外才转达
- **进度落盘**：`/home/wuyangcheng/.qwen/progress/`（或团队目录）
- **共享事实走 .team/（跨 CLI 记忆互通，2026-08-11 加入，用户确认）**：Qwen Code（`~/.qwen/memories/`）与 Codex（`~/.codex/memories/`）的**私有记忆互不读取**。因此**跨成员/跨 CLI 必须知道的事实一律只写 `/data/WYC/signLanguage/.team/` 共享文件**（公共约束、team_messages.log、队列、user_last_interaction、成员记忆文件），**不依赖各自 CLI 私有记忆**。各成员私有记忆可记录个人工作细节，但关键事实必须同步到共享文件
- **成员记忆文件约定（2026-08-11 加入，用户确认）**：每个成员维护自己的工作记忆文件 `/data/WYC/signLanguage/.team/member_memories/member_memories_<成员id>.md`（成员 id 从 `team_topology.json` 读取）——记录：当前任务状态、关键决策、待办/待确认事项、踩坑记录；**主管可直接读取了解成员记忆**，实现 Qwen/Codex 成员记忆互通。成员在**任务阶段切换/完成/遇到重要结论**时更新该文件；主管定期查看汇总
- **成员进展记录与公共事实维护义务（2026-08-12 加入，用户确认）**：每个成员必须持续维护**自身重要进展记录**（阶段完成/关键结论/产物路径/待确认项），写入**后台确认通道**（team_confirmations.log，monitor 5s 抓取）或**进展文件**（progress/<窗口>.txt），并同步更新**成员记忆文件**（member_memories/）；**公共事实更新**（工作线状态/部署状态/新增产出/资源变化）同步到共享文件（.team/）——主管据此实时维护 dashboard 小目标。**不得只留在各自 CLI 私有记忆或对话里**（主管无法抓取）
- **用户在线状态自动维护（2026-08-12 加入，用户确认）**：monitor 自动维护 user_online——所有成员窗口距最近用户交互 ≥60 分钟（阈值 `--offline-after-minutes`）→ 自动标记离线；任一窗口出现新鲜交互（< 用户在场宽限）→ 自动恢复在线；中间态尊重手动标记；用户显式声明离线仍以手动为准
- **人工介入**：成员需用户介入 → 后台报主管 → 主管提醒用户去该窗口 → 用户在成员处直接处理 → 成员通知主管完成 → 主管更新队列（不代答、不擅自标记完成；用户离线不催促）
- **临时 sub**：可随时启动，无需常驻；不占常驻名额

### 任务闭环规范（2026-08-24 主管广播，Owner 确认，全体成员强制）

主管派发的任务必须**主动回报收束**，形成闭环：**发起 → 执行 → 回报 → 主管验收 → 关闭**。

1. **主动回报（必须）**：无论任务进度/结果/决策变化（含 Owner 直接示意），都必须**主动回报主管**收束——不能只执行不汇报，不能让主管/其他成员停留在"不知道任务状态"中。
2. **完成后回报成果与数据**：回报应包含做了什么、产物/输出路径、验证结果（数字/ffprobe/测试等）、失败原因（如未做成）。
3. **遇阻即时回报**：遇到阻塞/异常/需要决策时，**即时回报原因与建议**，不沉默、不搁置。
4. **Owner 直接示意时同步回报主管**：被 Owner 直接示意（新任务/修改/纠正）时，**同步回报主管**，由主管知晓并关闭/更新任务，避免任务状态在团队层面失明。

### 变更记录
- 2026-08-24：§4 新增任务闭环规范（主管派发任务：发起→执行→回报→验收→关闭；完成回报成果数据；遇阻即时回报；Owner 直接示意同步回报主管）
- 2026-08-25：§76 补强 Sub 成果继承（派发 sub 必须附已有成果清单——现成脚本/部署文档/基线数据/已确认结论绝对路径，明确"不要重复做"与增量产出；复查纠正重复劳动；模板见 ~/.qwen/skills/sub_agent.md）

### 职责优先协作与升级（2026-08-12 用户确认）

- 成员遇到职责外或当前无法解决的问题，先查阅 §8/§9 与 `team_topology.json`，不得停滞或重复造轮子。
- 视觉综合测评中的 API key、OAuth、api_base、模型接入、代理、额度问题，先找 signL8 运维；算法/模型问题找 signL5；字幕流水线找 signL6；介绍面板找 signL7；overlay 动画找 signL4。
- 成员可以协商转派更适合的子任务；涉及密钥、权限、外部资源、生产部署或公开仓库时，必须由对应负责人执行或明确授权，不得索取或暴露敏感值。
- 协商结果必须写入 `team_confirmations.log`，至少说明：谁负责、谁协助、交付物、下一步和阻塞点；同时更新 progress/member_memories，不能只留在私聊或 CLI 对话中。
- 对应负责人也无法解决时，立即以 `【人工介入请求】` 或 `【成员确认】` 升级主管，附已尝试方法、脱敏错误信息和所需决策；主管负责拆解、协调资源、重新指派或启动临时 sub。
- **运维问题默认路由（2026-08-12 用户确认）**：代理、GPT/DeepSeek/Qwen 模型切换、OAuth、API key/api_base、额度、statusline、Qwen/Codex 配置、tmux/monitor/health、服务保活、网络与环境问题，以及同类运行时异常，默认交由 **signL8 运维**负责调查、协调和修复；其他成员不得各自盲改同一生产配置。
- **切换 GPT 前的上下文检查（2026-08-13 用户确认）**：任何成员从 DS/其他 provider 切换到 GPT ChatGPT 模型前，必须先查看该会话 statusline 的 context 使用比例和绝对窗口；若 context 使用比例 **>=50%**，**必须先在当前模型/provider 下执行 compress**，确认压缩完成且比例回落到 50% 以下后，再切换 GPT；不得先切 GPT 再压缩。若当前模型无法安全 compress，再由 signL8 评估 resume/迁移或新会话方案，并保留旧 session。切换后先做最小真实请求，再恢复长任务。
- **GPT 空响应应急（2026-08-13 用户确认）**：出现 `Upstream returned empty response after 3 attempts`、`Response truncated` 或同类 GPT OAuth 异常时，先保留现场与日志并通知 signL8；不得成员自行反复重试、换 provider 或换 GPU。signL8 负责检查上游响应、tool-call/finish_reason、重试退避和上下文负载，必要时启动 sub；修复验证前 dashboard 保留 API 异常状态。
- **运维并发委派**：问题需要并发调查时，由 signL8 运维按职责启动 sub/临时协作者，并明确每个 sub 的独立范围、输入上下文、禁止修改范围和回报文件；不得让多个 sub 重叠修改同一文件或重复消耗同一生产会话。
- **上下文关联管理**：signL8 必须把主问题、相关公共约束、当前配置/版本、已知错误、任务分工、共享文件路径和验证标准同步给 sub；sub 的结论必须回到 `.team/` 共享文件、progress/member_memories，并由 signL8 汇总确认，不得只留在 sub 私有上下文。
- **Sub 成果继承（2026-08-25，Owner 要求）**：派发 sub 时必须附已有成果清单——相关现成脚本/部署文档/基线数据/已确认结论的**绝对路径**，明确"不要重复做"事项与本次**增量产出**；sub 无父对话历史，看不到主进程已有成果。启动后须复查 sub 输出，发现重复劳动（重写已有脚本、重测已有基线、重新调研已知信息）立即 send_message 纠正。执行细则与模板见 `~/.qwen/skills/sub_agent.md` 已有成果继承规范章节。
- **结果回报与变更纪律**：修复前先备份；报告根因、影响范围、修改文件、回滚点、测试命令和失败降级策略；涉及权限/密钥/生产服务/公开仓库先报主管；验证通过后由 signL8 统一通知主管，避免成员各自报不同结论。
- **常驻成员会话恢复（2026-08-12 用户确认）**：重启常驻成员的 Qwen/Codex 对话后，必须优先使用原会话 `resume` 恢复上下文、任务记录和待办，不得默认新建空白会话导致工作上下文丢失。
- **主管拓扑引用规范（2026-08-12 用户确认）**：主管维护公共约束、dashboard、日志和委派任务时，文档与逻辑必须使用 `team_topology.json` 中的稳定成员 id/角色/职责；不得硬编码可能变化的 tmux 窗口名。运行时窗口名只能由拓扑解析模块读取；窗口变动只修改拓扑文件，不改业务脚本和规范正文。
- **provider 不兼容例外**：若原会话存档绑定了错误或不兼容的 provider（例如旧 DeepSeek 存档不能直接承载 GPT OAuth），由 signL8 先备份并修正 provider/config，再测试原会话 resume；只有确认 resume 会继续错误路由时，才可迁移到新会话。
- **provider 不兼容必须走历史迁移 skill（2026-08-12 用户确认）**：迁移不得只靠手工摘要或复制几条消息，必须使用既有 `qwen-codex-context-migrate` skill，按其检查、规划、迁移、验证流程迁移完整可用的 session 历史/上下文；迁移前保留旧 session，迁移后验证新 provider 路由、任务连续性和待办完整性，并回报旧/新 session ID、skill 流程、迁移范围与验证结果。

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

- **主管人（SignL3）**：统筹/委派/dashboard/公共约束/人工介入队列，直接面向用户
- **平级协作原则**：wan 视频制作者（signL2）与语义动画制作者（signL4）是**平级协作关系，没有上下层级**
- 所有常驻角色（signL2/signL4/signL5/signL6）**直接向主管汇报**；角色间协作平级协调（消息机制），不互相指派
- **字幕员（成员 id `signL6`，2026-08-11 新增）**：视频中英双语字幕制作（自动化字幕 skill 工具包 + 本地 VL 视觉 QA）；职责见 §9
- **宣传员（成员 id `signL7`，2026-08-12 新增）**：项目介绍面板制作（中英双语，模板结构 + 实验室排版风格 + VL 美化协作）；职责见 §9
- **运维（成员 id `signL8`，2026-08-12 新增）**：外部资源/API 测试与接入（大模型 API 连通性/能力测试、调用模板、.env 管理）；职责见 §9
- 新特化常驻角色：生成前必须询问用户意见
- 临时 sub：随时启动，无需常驻，不占名额
- **成员入队必要条件（2026-08-28 顾问注册时确认）**：每个正式成员进入 team 必须配置 **SSE member helper**（`daemon_team_member_helper_v2.py --role <role> --session-id <sid>`，setsid 保活）——helper 承担会话保活（防 idle 关闭）、事件记录（inbox）、健康上报（helper_health.json，看板/监督器依赖）。**无 helper 的成员视为未完成入队**（会因会话 idle 关闭导致失联）。helper 由 `daemon_team_message_services_v1.sh` 动态从 registry 读取角色启动（新角色注册 registry 后自动覆盖）；新成员入队检查清单：①registry 注册（manifest+topology）②helper 启动且 helper_health.json 正常 ③消息链路可达（mailbox 投递验证）

### 变更记录
- 2026-08-10：初版建立（安全/版本/zhuhai 资源/汇报/部署/数据六类约束）
- 2026-08-10：§8 组织架构加入（signL2/signL4 平级，直接向主管汇报）
- 2026-08-10：§9 职责边界与 dashboard 加入（overlay 审核细节隔离 signL2；主管统一维护 dashboard 全成员进度）
- 2026-08-11：§8 新增字幕员（signL6-subtitle，双语字幕制作）
- 2026-08-12：§8 新增宣传员（signL7-promoter，介绍面板中英双语制作）
- 2026-08-12：§8 新增运维（signL8-resource，外部 API 测试与接入）
- 2026-08-28：§8 新增顾问（advisor，技术顾问：daemon/看板/代理/本地模型运维支持 + 协调）+ 成员入队必要条件（helper 必须配置，无 helper 视为未完成入队）

## 9. 职责边界与 dashboard（2026-08-10 加入，用户确认）

- **语义视频审核细节隔离**：semantic overlay 等语义动画的审核流程细节（VL 审查、人工审核状态、优化反馈）仅在【signL4（制作方）+ 主管（SignL3）+ 用户】三方之间流转；**wan 负责人（signL2）不需要知道这些细节**，不参与 overlay 审核决策，也无需在 overlay 相关事项上主动推进/通知
- **部署执行**：overlay 审核通过后如需部署，由主管决定并给出明确指令；signL2 仅按主管指令执行部署动作（如复制文件/更新 manifest），不自行判断审核状态
- **主管维护 dashboard**：主管（SignL3）负责维护团队 dashboard（http://127.0.0.1:8450）记录**所有成员**（signL2/signL4/signL5/signL6）的进度状态；各角色按 §4 主动向主管同步进度/完成/异常，由主管统一汇总更新 dashboard；角色之间不得直接改动 dashboard 数据文件
- **运维职责（signL8-resource，2026-08-12 新增）**：负责外部资源/API 测试与接入 + **环境运维（2026-08-12 用户指示）**——模型/代理/服务的环境配置与切换（综合代理、GPT OAuth、模型切换测试、settings/环境维护）——大模型 API 连通性/可用性/能力（如视觉）测试，准备 api_base/api_key/model_name 调用模板（可入 settings.json provider），准备 .env 模板供用户填 key；测试结论落盘报告
- **宣传员职责（signL7-promoter，2026-08-12 新增）**：负责项目介绍面板（产品简介）制作——按模板结构（项目简介/特点/核心功能/应用场景/目标用户）组织，中英双语排版（参考实验室手册风格：双语并排、权威背书），文字充实 + 图比例适中，用本地 VL（zhuhai qwen3-vl-8b）协作检查排版美观；产出 md + word（docx）交付
- **字幕员职责（signL6-subtitle，2026-08-11 新增）**：负责视频中英双语字幕制作——使用自动化字幕 skill 工具包（/data/WYC/signLanguage/work/tools/produce-bilingual-conference-subtitles/，SKILL.md 流程：转写→cue plan→SRT/ASS→QA→渲染样本→烧录），配合本地 VL（zhuhai qwen3-vl-8b）做字幕帧视觉 QA；产物交付 SRT+ASS+烧录 MP4；字幕规范锁定（中文 48px/英文 36px、纯黑描边无阴影、中文无逗号句号、cue 间隔≥2 帧）

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
- zhuhai：`miniforge3/envs/gen`（训练环境）；**vLLM 视觉服务**（GPU9，qwen3-vl-8b，http://172.28.17.71:8000/v1，OpenAI 兼容）
- 通用：`qwen`（Qwen Code）、`codex`（Codex CLI）；**禁止 rm/rmdir**（用 mv / python Path.unlink）

**zhuhai 资源使用约束（严格遵守，违反=踩坑）**：
1. **GPU1 始终避开**（liuchang MATLAB 占用，任何情况下不得使用）
2. **GPU9 留 VL**（qwen3-vl-8b vLLM 视觉服务），不用于训练
3. GPU0-8 训练任务占满时不得抢占；**GPU0 训练默认**
4. **CPU 限核（nice/taskset）**，优先保证 liuchang 不受影响
5. 无 sudo；GitHub 直连慢（~50KB/s），**nature 可作中转**（nature 直连 GitHub ~10MB/s，下载后 scp 内网传）

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

**通用防弯路**：长任务后台运行（setsid nohup 保活 + 校验进程）；大计算必须带进度输出；本地 Web 服务只绑 127.0.0.1

### 变更记录
- 2026-08-12：§12 服务器/环境与资源约束加入（nature/zhuhai/edu、常用路径、Python 环境、zhuhai 资源规则、网络/通用防弯路，用户要求全员知晓）

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
1. **GPU1 严禁**（liuchang MATLAB，任何情况不得占用）
2. **GPU5+6 = 本地A 专属**（8018，TP=2 ctx 448K）——训练/弹性/其他角色不得占用
3. **GPU7+8 = 本地B 专属**（8017，TP=2 ctx 448K，组合 B）——同上；parallel=1，多会话共享时请求串行（当前共享方：本地B 会话/算法开发者/Jarvis）
4. **GPU9 = VL 保留卡**（qwen3-vl-8b vLLM 8000）——与弹性 q4-lite（8029）**互斥**：需要 VL 时先释放弹性实例（空闲 600s 自动停）再启 VL；弹性 lite 占用期间 VL 不可用，字幕员/宣传员/算法开发者的视觉任务需避让
5. **GPU0/2/3/4 = 弹性 lite2-5 与训练共享**（训练默认 GPU0）——训练前必须先查弹性实例是否在跑（弹性启动脚本检测显存 >500MiB 报 BUSY，有自动防护，但仍须事先确认）；弹性空闲 600s 自动释放
6. **弹性 TP2/TP4 槽**（tp2-e/tp4/tp2-x/tp4-x）自动扫描空闲卡——训练进行中不启动；空闲卡 ≤2 张时不启动（避免挤占专属实例或触发 BUSY 空转）
7. **换卡/实例启停/迁移**：按 §3 换卡规则——先报主管、运维协调后执行、回报实际占用卡号

**维护职责**：
- **运维**：本地服务周期健康检查（8017/8018/8000/弹性端口 + GPU 显存），常驻实例失联/异常即时告警主管（可并入 daemon context watchdog 或独立脚本）；执行服务变更
- **主管**：冲突协调（训练 vs 弹性 vs VL）、维护拓扑注册表、向 Owner 汇报服务格局与异常

### 变更记录
- 2026-08-26：新增 §14 本地模型服务与 GPU 协调规范（Owner 要求）——拓扑加入 local_model_services 注册表 + 角色 local_service 字段；统一入口 11435；GPU 分配与冲突规则（GPU1 严禁 / 5+6 本地A / 7+8 本地B / 9 VL 与弹性互斥 / 0,2,3,4 弹性与训练共享）；主管+运维共同维护

## 15. 团队进度监督与 Owner 及时汇报机制（2026-08-26 加入，Owner 要求；同日升级 v2 微信直推）

**架构（Owner 确认，v2）**：自动化监督 → 进展文件（单一事实源）→ **直调微信 iLink Bot API 推送 Owner**（零 LLM，秒级）。**主管 LLM 不在进展信息链路上**（避免多余中转），只负责维护监督脚本与异常处理。

- **监督脚本**：`work/scripts/team_progress_supervisor_v2.py`（v1 保留便于回滚），tmux 保活 `slu-team-progress-supervisor`（崩溃重启循环 `work/scripts/run_supervisor_v2_loop.sh`），30s 周期，纯规则化（监督路径零 LLM 依赖）。
  - **v2 修复（2026-08-27）**：新增 `PENDING_STALE_TTL=1800s` 陈旧过期——pending 队列中超过 30 分钟未推送成功的事件直接丢弃不补推。根因：iLink 短暂故障（HTTP 200 但 ret=-2）后积压的数小时前旧事件按优先级排在队首被逐条"补推"，GLOBAL_CAP=8/600s 排空 100+ 条积压需数小时，期间新进展被堵、latest_progress.md「⏳ 未汇报新进展」节被旧 error 占满误导 Owner。旧事件审计留痕在 `<role>_progress.jsonl`。
- **监督对象**：registry 全部常驻角色会话（含主管自身，但主管不通报——Owner 与主管直接对话）。
- **事件类型**：接到任务 / 回合完成 / 回合取消 / 出错 / 等待人工输入 / 进展（10 分钟/角色节流）/ 疑似卡住（进行中 15 分钟无输出增长）。
- **进展文件**：`.team/daemon_v1/progress_supervisor/latest_progress.md`（⏳ 未汇报新进展 / 各角色当前状态 / 进展历史）。推送成功后移入历史。
- **推送协议（v2）**：有新进展时 `weixin_push.py` 直调 `POST https://ilinkai.weixin.qq.com/ilink/bot/sendmessage` 推送到 Owner 微信（**不经 Jarvis 模型、不经 channel 会话**）。每周期最多 1 次推送；全局上限 600s 内 8 条事件；推送失败 pending 保留下轮重试。
  - 推送模块：`work/scripts/weixin_push.py`；凭证自动读 `~/.qwen/channels/weixin/account.json`（token）；Owner chatId 自动解析自 `~/.qwen/channels/daemon/<hash>/routes.json`。
  - 独立用法：`python3 work/scripts/weixin_push.py "消息"` / `--test`。
  - **context_token 40 分钟宽限（2026-08-28 源码+实测确认）**：主动推送受 iLink context_token 会话宽限限制——token 只在 Owner 发消息时续期（channel worker 持久化到 `~/.qwen/channels/weixin/context_tokens.json`），超 40 分钟无互动则推送返回 `ret:-2 prepare failed`；getconfig/getupdates 均不刷新 token。Owner 与 Jarvis 微信保持互动（间隔 <40 分钟）即可持续可用；推送失败时提示"需 Owner 微信发消息激活"。详见 ops 文档 §2.4 与 `work/reports/ilink_context_token_research_20260828.md`。
- **v1 历史**：2026-08-26 上线时为「轻推 Jarvis → Jarvis 读文件汇报」；因本地模型慢/卡导致转达不可靠，同日升级 v2 直推（Owner 微信实测确认收到）。
- **Jarvis 手动转达（2026-08-26 补充）**：成员主动发【转达】/【请转告 Owner】/【汇报 Owner】类消息给 Jarvis 时，Jarvis 调用 `weixin_push.py` 直推微信（不依赖 channel 回复路由）。协议写入 settings.json weixin `instructions`（新会话）+ Jarvis 会话注入（已有会话）；skill 见 `~/.qwen/skills/jarvis-forward-owner.md`；已验证（HTTP 200 message_id，Owner 收到）。
- **Jarvis 转达协议**：持久化于 `QWEN.md §6`（防上下文压缩丢失）。Jarvis 仍用于「Owner 主动在微信提问 → 回复」的 channel 闭环；**进展推送不再依赖 Jarvis**。
- **选择题/权限自动提交（2026-08-26 加入，免 LLM）**：监督器检测到成员挂起提问（ask_user_question/permission）时，持久化结构化数据到 `.team/daemon_v1/progress_supervisor/waiting_requests.json`（requestId/options/answer_key/submit_option_id）并立即推送微信（新 requestId 不受 5 分钟抑制）；Owner 微信回复「选N」→ Jarvis 直接调 `weixin_option_reply.py "选N"` 提交（user_question：optionId=proceed_once + answers={answerKey:label}；permission：选项 optionId）。
- **成员主动介入推送（2026-08-26 加入）**：成员需 Owner 人工介入/决策时直接运行 `python3 work/scripts/weixin_intervention.py "内容"` 秒级推送微信（【人工介入】成员名：内容，角色名自动从 tmux 窗口名识别），不经监督器轮询。
- **审计**：`.team/daemon_v1/progress_supervisor/notifications.jsonl`（每次推送的 HTTP 结果与事件清单）；每角色事件历史 `<role>_progress.jsonl`。
- **维护职责**：主管负责脚本维护/调参/异常处理；脚本崩溃由 tmux while 循环自动重启；链路故障（凭证失效/weixin 断连）由 context watchdog 与 daemon channel 健康机制覆盖，主管介入恢复。

### 变更记录
- 2026-08-26：新增 §15 团队进度监督与 Owner 及时汇报机制（Owner 要求）——自动化监督 + 进展文件 + Jarvis 轻推转达；主管 LLM 退出信息链路
- 2026-08-26（同日升级 v2）：进展推送改为 `weixin_push.py` 直调微信 iLink Bot API（零 LLM 秒级），不再经 Jarvis 模型；新增凭证/chatId 自动读取与独立推送脚本；Owner 微信实测确认收到
- 2026-08-26（v2 补充）：Jarvis 手动转达链路——成员【转达】消息经 Jarvis 调用 weixin_push 直推微信；协议写入 channel instructions + Jarvis 会话 + skill；实测 HTTP 200 送达
- 2026-08-26（v3 补充）：微信链路修复（context_token 持久化 + ret 字段判定，18:38-22:00 推送实际失败被误判成功的问题）+ 选择题自动提交（weixin_option_reply.py，免 LLM）+ 成员主动介入推送（weixin_intervention.py）——三项均端到端实测通过

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

### 变更记录
- 2026-08-13：新增 §13 daemon 团队管理 v1，与旧 TUI/tmux 链路并存；明确生产 4194 边界、session 归属、结构化健康接口、独立消息与 dashboard 输出。

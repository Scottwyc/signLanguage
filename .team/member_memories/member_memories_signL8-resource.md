# 成员记忆：signL8-resource（运维）

> 2026-08-12 建立。维护者：signL8-resource。角色名 2026-08-12 由『资源管理员』改为【运维】（id 不变）。主管可直接读取本文件了解成员状态。更新：2026-08-29（顾问更新 GPU 格局为 vLLM INT4 弹性池 + GPU0/1 禁用）

## 职责
- 环境运维（2026-08-12 用户指示）：模型/代理/服务的环境配置与切换（综合代理、GPT OAuth、模型切换测试、settings/环境维护）
- 外部资源/API 测试与接入（调用模板/.env、连通性/能力实测、provider 配置）

## 团队称呼规范（2026-08-14 主管广播，强制）
- 团队内称呼/消息/汇报一律使用 team 角色中文名：主管、运维（我）、WAN 负责人、算法、动画、字幕、宣传、调研
- 不使用内部 session 角色 ID（SignL3/signL8 等）作为前缀/称呼；不提旧 tmux 窗口编号（signL2-294 等）
- 消息前缀：【主管 全员广播】【主管】【运维】【WAN 负责人】【算法】等；重要汇报用【主管】，需人工介入用【人工介入请求】格式（窗口: | 任务: | 路径:）
- 成员间平级协作，共享事实写 .team/ 文件；不互相直接 POST prompt
- 运维给成员发消息必须用 daemon mailbox：`python3 work/scripts/daemon_team_mailbox_v1.py --to-role <角色> --prompt "..."`；投递前确认目标 session 非 stale（registry.json 的 session_id_state）
- {team:...} 明文包协议已废弃禁用；完整规范见 /data/WYC/signLanguage/.team/daemon_messaging_guide.md

## 换卡纪律（公共约束强制条款，2026-08-13）
- 换卡/换GPU/换机器调用**必须经主管协调**：①提换卡建议先向主管说明理由与目标卡位；②执行前通知主管协调显卡分配（避免抢卡/liuchang/vLLM/成员冲突）；③严禁自行换卡；④换卡后回报实际卡号与占用
- 适用：GPU 训练/推理/转绘/视觉服务全部

## Wan 后端崩溃排查（2026-08-13，signL2 协作）
- 现象：GPU5/6/7/8 Wan 后端周期性崩溃（11:32/11:55/12:18/12:32/12:45/13:03，20-37 分钟必崩），写盘 VAE decode 阶段 illegal memory access，steps/输入/handfixed 均非根因
- 已排除：GPU 硬件（ECC N/A/温度电源正常/无 Xid）、NCCL 超时、steps、handfixed 输入
- 假设：显存泄漏累积（decode_streaming 的 conv2 全量 latent 常驻 GPU + FSDP 残留）
- 方案：换卡 GPU0-4 验证（已提交主管协调）、job 后主动重启兜底、显存基线日志

## GPT 切换规范（用户确认 2026-08-12；阈值规则 2026-08-13 更新）
- **统一默认模型 = `gpt-5.6-luna-chatgpt`**（gpt-5.6-luna [ChatGPT]，effort=xhigh；简单任务 medium/high）
- 用 settings 原有 `gpt-5.6-luna-chatgpt` provider（envKey=OPENAI_API_KEY，extra_body reasoning_effort=xhigh 已更新）
- **不用**临时加的 `gpt-5.6-luna`（PROXY_API_KEY）作默认（保留备选）
- OPENAI_API_KEY 需非空占位：~/.qwen/.env 已设 not-needed（系统真实 sk-pro key 不影响，代理优先 OAuth）
- codex config.toml：custom + model=gpt-5.6-luna-chatgpt
- 统一切换时机：等 signL2 7 词 handfixed 测试完成（清单 work/reports/proxy_switch_plan_20260812.md）
- **【阈值更新 2026-08-13 用户确认】context 使用比例 >=50% 时切 GPT 的强制顺序**：
  - 任何成员从 DS/其他 provider 切到 GPT ChatGPT 前，必须先看该会话 statusline 的 context 使用比例与绝对窗口
  - **若 context 占比 >=50%**：必须**保持当前模型/provider 先执行 compress**，确认压缩完成且比例回落到 50% 以下，**再切换 GPT**；**不得先切 GPT 再压缩**
  - 若当前模型无法安全 compress，再由 signL8 评估 resume/迁移/新会话方案（用 qwen-codex-context-migrate skill），并**保留旧 session**
  - 切换后先做最小真实请求，再恢复长任务
  - signL8 执行任何成员切换时，把此顺序检查作为前置步骤写入 proxy_switch_plan 清单

## 当前任务状态

### dflash2/MTP 加速方案 POC（2026-08-30）⏸️ 已暂停 + GPU3+4 已释放
- **任务**：Owner 要求评估 dflash2/mtp 加速方案是否应用到当前本地模型服务，验收标准「prefill 保住 vllm 现有效果 + decode 加速」。只动 GPU3+4（8051），严禁动其他槽位。
- **已得结论（MTP 线）**：MTP n=2 已达标——prefill 持平略升 + decode 1.86-1.90×（达 ~100 tok/s 目标），draft token 接受率 85.4%。**MTP n=2 为首选生产配置，n=1 为保守档**。
- **fp8 KV 线（已定位根因，未修复即暂停）**：fp8 POC 触发 flashinfer JIT 编译失败 `cuda_fp8.h: No such file or directory`。根因 = vLLM 因 CUDA 已初始化强制 spawn worker（`_maybe_force_spawn()` 设 `VLLM_WORKER_MULTIPROC_METHOD=spawn`），spawn 的 worker 是全新 Python 进程**不继承 API 进程环境变量**（实测 worker 环境无 CUDA_HOME/FLASHINFER_NVCC）→ flashinfer `get_cuda_path()` 回退 `which nvcc` → `/usr/bin/nvcc`（CUDA 11.5，缺 cuda_fp8.h）→ JIT 失败。设 `FLASHINFER_NVCC` 无效（spawn 不继承）。
- **未来修复方向（未实施）**：需在 worker 进程内注入 FLASHINFER_NVCC/CUDA_HOME——① vLLM multiproc_executor 的 env 注入机制；② wrapper 脚本包裹 worker 启动；③ 改 flashinfer 源码 get_cuda_path() 硬编码 CUDA 12.0 路径。
- **收尾动作（2026-08-30）**：Owner 指示「测试任务先不用做了，可以休息了」。已按 §14 红线用进程组 `kill -9 -- -1380891` 精确清理残留 worker（1420518/1420520 + python3 1407691，均 PP=1 孤儿），GPU3+4 释放至 13 MiB 基线；生产 8050/8052/8053 全部在听未受影响。
- **g29 核对结果（2026-08-30）**：GPU2+9 占用（pid 1451157/1451159）正是 8050 生产实例（PGID=1419879，CUDA_VISIBLE_DEVICES=2,9）的 worker，API 可达。**g29 可用健康，不是残留/泄漏进程**。发现路由日志中 8050 实例以旧名 `qwen3.8-27b-int4-tp2-g02` 注册（代理弹性配置用新名 `g29`，main.py:177），导致代理弹性逻辑误判 g29 未运行→GPU_BUSY 循环（日志 3385-3550 行）。**Owner 确认一切正常，不再跟进**。
- **g34（8051）**：我释放 GPU3+4 后，弹性池已于 02:58:19 自动重启 8051（pid=2718885，CUDA_VISIBLE_DEVICES=3,4）——GPU3+4 已恢复为 8051 生产。
- **g56（8052）**：健康（pid=1993885，CUDA_VISIBLE_DEVICES=5,6）。
- **待报告（恢复测试时）**：8052 生产槽位（GPU5+6）运行 MTP n=2（来源不明，我未触碰）；8051 弹性池自动重启实例也曾带 MTP n=2——疑似共享配置，需向 Owner/顾问确认。
- **POC 脚本/数据**：`/home/wuyangcheng/dflash2_poc/`（zhuhai）——launch_8051_poc.sh（fp8 分支已加 FLASHINFER_NVCC，备份 .bak_*）、bench*.py、lossless_*.jsonl、results_*.jsonl、prompt_*.txt 等。

### DSH nature 环境实测（2026-08-18）⚠️ 阶段 0 完成，阶段 1 阻塞于 inotify
- 任务：Owner 要求评估 DSH（DeepSeek Harness，`@deepseek-ai/dsh` 0.1.0-rc.7，agent 运行时框架）能否在 nature 部署 + 性能测试 + agent team 可行性；调研 signL9 报告 `/data/WYC/signLanguage/work/documents/dsh_research_report_v1_20260818.md`（测试方案第 4 节）。
- **阶段 0 ✅**：Node 24.9.0 隔离安装 `~/node24`（系统 node v20 在 `/home/wuyangcheng/local/node/bin/node`，零污染已核查：shell 配置无 node24 引用、daemon/看板/member-helper 全 python3、Qwen Code 用系统 v20）；pnpm 11.7.0（corepack enable 只写 ~/node24/bin）；DEEPSEEK_API_KEY 已配置；`npx @deepseek-ai/dsh --version` = 0.1.0-rc.7。
- **阶段 1 ❌ 阻塞**：`dsh web`(3080) 与 headless 均 ENOSPC——nature `fs.inotify.max_user_watches=65536` 100% 占满：**VS Code Server（.vscode-server）独占 56331（86%）**，其余 Qwen update 检查器（6-7 个残留）/codex（6+）等占满；DSH 的 chokidar 来自 hmr/credentials/skills 等核心插件（`--patch` 禁 hmr 无效）；无 sudo 无法提升限制。
- **处置**：已回报主管（07-2d6b2f0）等指示（临时关 VS Code / 宿主提限制 / 暂缓）；Node 24 保留 ~/node24 随时重试；测试残留 playwright chrome 已清理。
- 结论倾向：DSH 定位"成员级 agent 运行时"（web UI + subagent 委托 Codex），与现有 daemon 互补非替代（schedule 为 session-local 非 daemon 型）。

### Wan 宿主环境问题（2026-08-14）✅ 已定案 + 单卡 int8 过渡方案恢复（2026-08-15）
- **宿主结论**：宿主（VMware/NCCL 对称内存/FSDP allgather）问题在 VM 内无解（16 项失败），详见 v2 报告；宿主 UVM 方案（enable_uvm=1）需主管批准+宿管执行，Owner 无权限。
- **过渡方案（2026-08-15 主管批准）**：单卡 int8 恢复 7906 队列（GPU5）——denoiser int8（16.5GB）+ 权重驻 CPU + encode/采样/decode 分阶段显存释放，绕过 NCCL。连续 15 次排障后单 job `d74b760d496c` 完全成功（词6/steps20/clip49，MP4 2.23MB，ffprobe 通过 2.83s/704x560/30fps/h264）；VL 质量 overall=9 vs BF16 参考 10（差距源于 20 步 vs 50 步）。
- **关键排障沉淀**（详见 `wan_nccl_fix_ops_log_v3_20260814.md`）：
  - bnb CB/SCB 是普通属性（非注册 buffer），`nn.Module.to()` 不移动 → 需 free/restore_bnb_gpu_buffers 对称管理
  - `has_fp16_weights=False`（8bit 默认）时 bnb matmul 只用 state.CB/SCB，weight.data 可留 CPU（避免双重占用）
  - rope_apply float64→float32 省采样峰值 4-6GB；face_encoder/face_adapter 保持 int8 + 4D flatten 补丁（bnb int8 只支持 2D/3D）
  - CLIPModel 是封装对象（实际模型在 clip.model）；CLIP 采样期 offload + encode 前恢复（跨 chunk）
  - fsdp.free_model 只 to(cpu) 不移 CB/SCB → decode 前需 free_bnb_gpu_buffers
- **队列恢复约束（已过时，2026-08-29 起作废）**：原"仅 GPU5；GPU0 训练/GPU1 liuchang/GPU2-7 VL pool 8001-8005/GPU8 预留/GPU9 VL 8000"为 2026-08-29 前旧格局。**当前 GPU 格局见下"团队 GPU 现状（2026-08-29）"**：GPU0/1 均被外人占用一律禁用，GPU2-9=vLLM INT4 弹性池（g29/g34/g56/g78），GPU9 并入 g29。
- **服务脚本**：`/home/wuyangcheng/video_scripts/serve_zhuhai_wan_animate_resident_backend_v10_int8.py`（v10，多轮备份 .bak_*）；watchdog `watch_zhuhai_wan_backend_7906_v10_int8.sh`。
- 报告：`wan_nccl_fix_ops_log_v1/v2/v3_20260814.md`、`wan_int8_transition_plan_20260815.md`。

### Daemon team dashboard API 异常排查（2026-08-14）✅ 只读定案
- 现场快照：`/data/WYC/signLanguage/.team/daemon_v1/incident_snapshot_20260814_0015/`
- 报告：`/data/WYC/signLanguage/work/reports/daemon_team_dashboard_api_incident_v1_20260814.md`
- 4194 `/health`、`/capabilities`、`/daemon/status` 均 HTTP 200；daemon `status=ok`、`issues=[]`；当前 live session 的 `/status` 均 `hasTurnError=false`，未发现 OAuth/provider/GPT turn 故障。
- 真实异常仅为 signL7/signL9 迁移 manifest 中的旧 session ID 返回 `session_not_found`，根因是 stale registry 引用；workspace 中无可安全自动关联的新 live ID。
- 未重启 daemon、未创建/恢复 session、未改 provider/OAuth/权限、未触碰旧 8450 链路；已通过 `team_confirmations.log` 请求主管确认是否授权重建/完整历史迁移 signL7/signL9。

### 教育服务器大模型 API（edu, 59.64.38.5:9000）✅ 已完成接入
- **后端**：litellm → vllm；模型 `Qwen3.6-27B-Coder`（**id 大小写敏感**，小写 404）
- **能力实测**：连通 ✅ / 对话 ✅ / **视觉 ✅ 支持**（多模态识别准确）/ 深度思考 ✅（`message.reasoning` 字段，vllm 格式，非 OpenAI 标准 reasoning_content）
- **参数**：temperature 0.6 / top_p 0.95 / presence_penalty 0 / top_k 20 / min_p 0.0 / preserve_thinking=true（服务端）
- **配置**：`/data/WYC/.env.remote_edu`（含真实 key，权限 600，勿提交/勿公开）
- **模板**：`/data/WYC/signLanguage/work/tools/remote_edu_api/`（call_template.py / call_template.sh / qwen_provider_config.example.json / README_usage.md）
- **依赖**：用户级 pip 26.2.1 + openai 2.53.0 + matplotlib 3.10.9（阿里云镜像）

### SignL3 三项任务（2026-08-12）✅ 全部完成
1. **接入 Qwen Code**：edu provider 已合并 `~/.qwen/settings.json`（envKey EDU_API_KEY，值在 `~/.qwen/.env` 权限 600）；备份 `settings.json.bak_signL8_20260812_113836`；变更已记录 settings_fix_gpt_models_20260731.md；**需重启 Qwen Code 生效**
2. **VL 复用评估**：结论 = zhuhai qwen3-vl-8b 维持 visionModel 主力（延迟快 2-3 倍）；edu 27B 作备选/补充（128K 上下文 + 深度思考）
3. **视觉对比测试**：24/24 成功；报告 `/data/WYC/signLanguage/work/reports/edu_vs_zhuhai_vision_compare_report_20260812.md`（3 图内嵌）；脚本 work/scripts/run_vision_compare_v1.py 等
   - 准确度：OCR/UI 均 100%，scene zhuhai 92% > edu 85%，real_avatar edu 74% > zhuhai 67%（相当）
   - 延迟：zhuhai 全面快 2-3 倍（ui 5.2s vs 17.3s、ocr 1.3s vs 3.8s、scene 11.7s vs 23.7s、real 9.1s vs 20.1s）
   - 稳定性：受控任务均 1.0；real 图 edu 0.91 vs zhuhai 0.81
- **待办**：主管决定是否切 visionModel（默认保持 zhuhai）；重启后验证 edu provider

## 关键事实（§12 摘要，防走弯路）
- 三服务器：nature（本机主工作）/ zhuhai（172.28.17.71:7712，无 sudo，GPU 训练）/ edu（59.64.38.5:9000，教育网大模型 API）
- zhuhai 资源（2026-08-29 更新）：**GPU0 和 GPU1 一律禁止使用**（均被外部人员占用，含 liuchang MATLAB）；**GPU2-9 = vLLM INT4 弹性池**（g29=8050/2+9、g34=8051/3+4、g56=8052/5+6、g78=8053/7+8，TP2 INT4 128K ctx，视觉可用，3h 空闲释放）；**GPU9 不再给 VL 预留**（归入 g29，线上/本地模型均已自带视觉，qwen3-vl-8b 已停用）；CPU 限核优先 liuchang。统一入口：nature 综合代理 127.0.0.1:11435 → SSH 隧道 → zhuhai，禁止绕过直连。
- 网络：GFW 需代理 127.0.0.1:18080；DeepSeek/DashScope/GitHub 直连；教育网/内网 IP 直连
- 禁 rm/rmdir（用 mv / python Path.unlink）；长任务后台保活+进度输出；本地 Web 只绑 127.0.0.1

## 综合代理 stack（公共约束，2026-08-12）
- **stack 仓库**：/data/WYC/qwen-codex-gpt-deepseek-stack/（Qwen Code/Codex 的 GPT+DeepSeek 综合代理 11435；含 proxy/qwen-code/docs/chatgpt-oauth/tests；README 为权威文档）
- **部署版**：/home/wuyangcheng/codex-deepseek-proxy/（src/main.py 运行中，pid 155582，日志 /tmp/codex-ds-proxy.log）
- **模型切换路线**：综合代理 → gpt-5.6-luna（2026-08-12 已恢复验证走通）；deepseek-* → DeepSeek 官方
- **关键规则**：Qwen Code provider id 必须等于真实模型名（gpt-5.6-luna-proxy 会 400）；代理 GPT 路由读 live auth.json（chatgpt OAuth）
- **环境运维职责**：涉及代理/模型切换先查 stack 仓库 README 与 docs/，再动配置

## 踩坑记录
- 模型 id 大小写敏感：vllm 按 `Qwen3.6-27B-Coder` 注册，客户端用小写会 404
- vllm 思考输出字段是 `message.reasoning`，OpenAI 标准 `reasoning_content` 为 None——检测脚本要兼容两者
- nature 系统无 pip/ensurepip：需 get-pip.py --user 引导 + 阿里云镜像装包

## codex ChatGPT OAuth（2026-08-12 完成）
- `codex login --device-auth` 是稳定路径（直接输出 device code；普通 `codex login` TUI 在无交互环境不渲染）；URL https://auth.openai.com/codex/device + 一次性代码（15 分钟有效）
- 登录后 `~/.codex/auth.json` auth_mode=chatgpt；**model_provider 用 "openai"**（"chatgpt" 报 not found）
- 官方直连启动：`codex -c model_provider="openai"` 或 `codex --profile gpt`（config.gpt.toml 已切 openai，备份 bak_oauth_20260812）
- 启动陷阱：codex 需要 TTY（管道会报 stdout is not a terminal）；勿用 --model 启动
- 文档：/data/WYC/codex_chatgpt_oauth_login_20260812.md
- 验证会话：test-codex-gpt4（gpt-5.6-luna）、test-profile-gpt（gpt-5.5）

# GPT 切换后 Response truncated / empty response 专项调查 v1

- 生成时间：2026-08-13 14:10（初稿，sub 审计结论待并入）
- 执行：signL8-resource 运维
- 触发：主管持续监控任务——全员切换 gpt-5.6-luna-chatgpt 后 signL2/signL5 出现 Response truncated、signL7 出现 Upstream error None
- 版本：v1（后续版本追加修复与回归）

## 一、根因结论（初判，待 sub 审计确认）

### 1. 上游 ChatGPT Plus 配额耗尽（429 usage_limit_reached）是间歇性截断/空响应的主因

- 代理日志确认 **14 条 429**，均为 `usage_limit_reached`，`plan_type=plus`
- `resets_at=1787115101` → **2026-08-19 12:51 重置**（还有约 6 天）
- `resets_in_seconds≈525735`（≈6.08 天）→ 首次 429 约出现在 **2026-08-13 09:29 前后**——即 plus 周配额被 xhigh 大请求快速消耗，今日上午触顶
- 429 时段上游返回空/错误 → 代理空输出重试 3 次耗尽 → 客户端收到
  - `Upstream returned empty response after 3 attempts`（非流式 502）
  - `upstream EOF empty output after 3 attempts`（流式）
- 代理日志 **8 次 empty output exhausted（3 attempts）**、多次 tool call truncated 重试，与 429 时段吻合

### 2. signL5 现场确认（13:44 快照）

- 状态栏：`gpt-5.6-luna [ChatGPT] xhigh · 1.1m Context 38% used`
- 错误行：`● ⚠ Response truncated due to token limits.`（Qwen Code 客户端真实错误）
- 上下文：写报告 write_file 长内容被截断 → 客户端拒绝写入并提示拆小段——**这是上游配额期 EOF 导致工具调用参数未闭合 → toolCallsTruncated → finish_reason=length → 客户端报 truncated**
- context 38% < 50%：**未触发 compress 阈值**，符合新规则（<50% 可直接切）

### 3. signL7 Upstream error None = 修复前历史残留

- 快照 13:44 检测到 `✕ [API Error: Upstream error None]`
- 快照上下文显示其上方即有"代理已修复并重启（EOF重试+upstream错误透传）"通知 → 该行是 v2 修复前的旧错误显示残留，非新复现
- 代理日志尾部 signL7 请求全部 `[USAGE] truncation=disabled` 正常

### 4. 代理 429 处理路径确认（代码核查，main.py）

- `_upstream_status`（main.py:1059）：`status == 429 → return 429`——**429 直接透传，不进入空输出重试**，客户端收到明确 429 错误
- `_upstream_error_message`（main.py:1100+）：429 时提取上游 detail（`usage_limit_reached` + `resets_at`）返回客户端
- 即：**429 配额耗尽 → 客户端明确报错；empty output exhausted（20 次累计）是上游 200 空 body（配额边缘/不稳定）走 `GPT_EMPTY_RETRY_MAX=3` 重试耗尽**，两者是不同路径
- 空响应重试路径：`_handle_gpt_chat_to_stream`（2125 行）/ `_handle_gpt_chat_to_non_stream`（2261 行），attempt 级退避 `GPT_EMPTY_RETRY_BACKOFF=1.5s`；工具调用截断 EOF 同走重试（2209/2355 行）

## 二、复现与测试矩阵（2026-08-13 13:46-13:50 实测）

- 方法：隔离直连 127.0.0.1:11435（不碰生产会话/GPU/wan 任务），脚本 `/home/wuyangcheng/.qwen/scripts/gpt_matrix_runner_v1.py`
- 结果 JSON：`/data/WYC/signLanguage/work/reports/gpt_matrix_results_v1_20260813.json`

| 场景 | stream | context 模拟 | max_tokens | HTTP | finish_reason | 重试增量 | 结论 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T1 非流式小请求 | false | <50% | 64 | 200 | stop | 0 | 正常 |
| T2 非流式大 body（~200KB≈60-80K tokens） | false | >=50% | 64 | 200 | stop | 0 | 正常 |
| T3 tool call | false | <50% | 128 | 200 | **tool_calls** | 0 | 参数 JSON 完整闭合 |
| T4 长输出（3000 字） | true | <50% | 8192 | 200 | **stop** | 0 | 流式 710KB / 3698 tokens 完整 [DONE] |
| T5 流式小请求 | true | <50% | 64 | 200 | stop | 0 | 正常 |
| T6 流式大 body + 工具意图 | true | >=50% | 256 | 200 | stop | 0 | 正常 |

**矩阵结论**：当前时刻（非 429 时段）GPT 链路 6+1 场景全部正常——**截断/空响应为间歇性，与上游 429 配额时段强相关，本地 settings/代理配置在正常时段无诱发截断的问题**。context>=50% 场景在代理层无异常（T2/T6 通过），客户端 compress 流程见第五节。

## 三、监控体系（持续）

- 脚本：`/home/wuyangcheng/.qwen/scripts/team_gpt_error_monitor.py`（每 5 秒）
- 运行：tmux 会话 `slu-gpt-error-monitor`（保活）
- 检测：各拓扑成员窗口输出区真实客户端错误（错误 UI 图标开头 + 客户端错误标记），排除诊断回显 / bash heredoc 噪声 / wan 业务日志
- 记录：model/provider/context 占比/窗口/tool-call/finish_reason/代理重试增量
- 复现动作：现场快照 → `gpt_error_snapshots/` + 事件日志 `gpt_error_events.log` + `team_messages.log` 通知
- 状态：`/data/WYC/signLanguage/.team/dashboard/gpt_error_state.json`
- v1 修复：①错误行必须错误 UI 图标开头（消除 signL8 自身诊断文本误报）；②不向成员窗口 send-keys（消除自触发告警循环）；③NOISE 增加 bash/heredoc/unexpected EOF 等 shell 噪声

## 四、全成员 context/模型现状（13:45 扫描）

| 成员 | 窗口 | 模型 | provider | context 占比 | 状态 |
| --- | --- | --- | --- | --- | --- |
| SignL3 主管 | SignL3-304 | gpt-5.6-luna | chatgpt | 33.2% | 正常 |
| signL2 视频 | signL2-294 | gpt-5.6-luna | chatgpt | 8.9% | 正常 |
| signL4 动画 | signL4-overlay | gpt-5.6-luna | chatgpt | 23.3% | 正常 |
| signL5 算法 | signL5-algo | gpt-5.6-luna | chatgpt | 38.5% | 历史截断残留（已确认） |
| signL6 字幕 | signL6-subtitle | ?（codex） | ? | ? | 状态栏解析受限 |
| signL7 宣传 | signL7-promoter | gpt-5.6-luna | chatgpt | 19.9% | 历史 Upstream None 残留 |
| signL8 运维 | signL8-resource | deepseek-v4-flash | deepseek | 13.6% | 正常 |
| signL9 研究 | signL9-research | gpt-5.6-luna | chatgpt | 14.8% | 正常 |

**全部成员 context < 50%**：当前无成员触发">=50% 先 compress 再切 GPT"阈值。

## 五、context>=50% 先 compress 再切 GPT 的流程（已落实）

- 公共约束：`/data/WYC/signLanguage/.team/team_constraints.md`（2026-08-13 用户确认）
- 切换清单：`/data/WYC/signLanguage/work/reports/proxy_switch_plan_20260812.md` 2.5 节
- 强制顺序：**当前模型/provider 下先 /compress → 确认比例回落 <50% → 再切 GPT**；不得先切再压缩；无法压缩评估 resume/迁移（qwen-codex-context-migrate skill）并保留旧 session
- sub/auto 提示模板：settings.json systemPromptTemplate ×2、tmux-sub-agent.sh、tmux-auto-agent.sh、prepare-sub-agent.sh 均已含纪律段

## 六、本地 settings/context 审计结论（sub-A，2026-08-13 13:53 完成）

审计文档：`/data/WYC/signLanguage/.team/dashboard/sub_settings_audit_v1.md`（只读，未改任何文件）

### 本地无损坏性配置，但有两个放大因素

1. **reasoning_effort=xhigh（最强本地放大因素）**：settings 顶层 + luna-chatgpt extra_body + codex config.toml 三处一致。xhigh 生成链极长、推理 token 消耗大 → 在 plus 配额 429 状态下最先触限、最容易在工具调用中途被上游掐断 → 直接放大截断/空响应频率。**建议：配额恢复前降 effort 为 medium（三处同步）**
2. **max_tokens 预算认知不匹配**：luna-chatgpt 未定义 samplingParams → Qwen Code 自动注入 64K max_tokens（chunk-IIJEYBNH.js:6964）；但代理对 chatgpt.com 后端剥离该参数（main.py:2097），上游实际默认上限 32768（main.py:3097）→ 客户端以为有 64K 预算，实际 32K，截断观感被放大。**建议：显式配 samplingParams 或接受现状**

### 其他发现

- API key 无问题：.env 的 `OPENAI_API_KEY=not-needed` 占位被 settings.json env 真实值覆盖（实测运行中 qwen 进程 env 为真实 sk-proj key）；但为卫生风险，建议改真实值或删行
- 切换纪律（>=50% 先 compress 再切 GPT）**只写入 settings.json tmux 模板，主 QWEN.md 没有**——交互式会话未强制生效，建议补入主 QWEN.md
- context 占比快照均 <50%（signL2 9.7% / signL5 38.5% / signL7 19.9% / SignL3 33.2%），未违反公共约束
- timeout（180s）与代理 GPT_STREAM_MAX_TOTAL_TIME（900s）/ idle（180s）均正常，非报错来源

### 截断/空响应链路（代理源码佐证）

- 截断 = 上游 EOF 中断工具调用 → 参数 JSON 未闭合 → 客户端 toolCallsTruncated → FinishReason.MAX_TOKENS → "Response truncated due to token limits"（startInteractiveUI-YCS6AEPN.js:38183）
- 空响应 = 上游零输出断流 → 代理重试 3 次（1.5s×3 退避）耗尽 → "Upstream returned empty response after 3 attempts"（type=upstream_error）
- 429 = 流式建连期透传 "Upstream error 429"（main.py:2155）
- **两种报错都指向 chatgpt.com 上游断流/空流，与 429 usage_limit_reached（resets 2026-08-19）一致**

## 七、代理链路审计结论（sub-B，2026-08-13 14:05 完成）

审计文档：`/data/WYC/signLanguage/.team/dashboard/sub_proxy_audit_v1.md`（只读，未改任何文件）

### 核心结论
- **空响应/截断与 429 配额时段强相关**（代码+日志双重证实）：L9971-10013 连续 6 次 usage_limit_reached 后，紧接 L10052-10280 最密集空输出失败簇；窗口外（矩阵实测）零失败
- **触发与请求大小无关**（4.6KB 小请求与 1.8MB 大请求同样中招）→ 符合上游软限流（200 连接建立后 1-3s 断流无内容）

### 关键发现
1. 重试逻辑：3 次重试仅覆盖 status=None 与 EOF 空输出/工具截断；**429 不重试**（正确）；62 次重试多数成功，20 次耗尽（流式 12+非流式 8）
2. usage 透传：prompt_tokens 估算 `body_size//3`（代码/英文约高估 33%）；**正常流式完成路径不发 usage chunk**（[DONE] 早退跳过）——成功轮次 Qwen Code Context % 不更新
3. 429 客户端视角：流式=SSE 200+error chunk；**非流式=502（429 被伪装）**；仅 Codex 非流式路径真正透传 429
4. 上游响应：642 条 [USAGE] 全部 `truncation=disabled`（max_output_tokens 被代理剥离，上游无截断语义）

### 隐藏 bug（已修复）
- **流式 `_tc_state` 模块级全局竞态**（main.py L571）：ThreadingHTTPServer 多线程并发下 A 请求的 tool-call 状态被 B 请求 clear() → 工具调用 finish chunk 丢失 → 误判"工具调用截断/空输出"误重试（日志 L10082 交错实证）。非流式用本地 tc_state 无此问题。

## 八、修复与回归（2026-08-13 14:20，signL8 执行）

备份：`/home/wuyangcheng/codex-deepseek-proxy/src/main.py.bak_tcstate_20260813`

| # | 修复 | 位置 | 风险 | 回归验证 |
| --- | --- | --- | --- | --- |
| 1 | `_tc_state` 模块级全局 → 每请求局部 dict（参数传入转换器） | main.py:571-646/2126/2206/2211 | 中（竞态根治） | 流式 tool call finish_reason=tool_calls×2，参数完整闭合 args_len=34 ✅ |
| 2 | 非流式 429 状态码透传（502→429），客户端可识别配额态 | main.py:2303 | 低 | 代码路径确认（上游 429 时实测） |
| 3 | 正常流式 [DONE] 前补发 usage chunk | main.py:2174 | 低 | 正常流式收到 `usage:{prompt_tokens:130,completion_tokens:34}` ✅ |

- 代理已重启（pid 3050555，setsid 保活），端口 11435 监听中
- 矩阵 6 场景回归全部 200 正常（含 tool call / 大 body / 流式）
- 待观察：多成员并发下的流式 tool call 不再出现误判截断；成功轮次 Context % 正常更新

## 九、待办（建议，未执行）

1. **配额恢复前降 effort**：xhigh → medium（settings 顶层 + extra_body + codex config.toml 三处同步）——sub-A 建议，需主管批准
2. 失败风暴熔断：同一 input 前缀连续失败（3 请求内 ≥2 次耗尽）直接透传错误建议切换；429 后窗口 `gpt_empty_retry_max` 动态降 1——sub-B 建议 4
3. 日志时间戳：log.py 统一加 `YYYY-MM-DD HH:MM:SS` 前缀——sub-B 建议 5
4. .env 卫生：OPENAI_API_KEY=not-needed 改真实值或删行——sub-A 建议 3

## 十、降级策略（临时）

1. **429 配额期（至 2026-08-19 12:51）**：GPT xhigh 大请求高概率 429/空响应——建议长任务/大 context 会话暂回 deepseek-v4-flash max（日志尾部已见主管"切回 DS flash"通知）
2. GPT 会话遇到空响应：按公共约束**保留现场通知 signL8，不得自行反复重试/换 provider/换 GPU**
3. 长文件写入被截断：客户端提示"拆小段写"（skeleton + edit 增量）——继续保留该降级
4. 代理故障时回退：config.toml 恢复 bak（deepseek 直连）

## 八、下一步

- sub 审计结论并入 → 定稿根因
- 如需代理侧改进（如 429 不重试直接透传、配额提示）→ 备份后修改 + 真实会话回归
- team_confirmations.log 回报

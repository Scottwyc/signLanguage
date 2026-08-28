# 微信 iLink Bot context_token 机制调研报告

- 调研时间：2026-08-28（UTC+8）
- 调研人：Jarvis（sub-agent，纯网络调研，未调用任何微信 API、未发送任何消息）
- 目标：①确认 context_token 的 40 分钟宽限期是否有官方依据；②寻找主动刷新/续期方法；③评估替代推送通道
- 置信度标注：【高】= 多来源交叉印证 / 官方文档；【中】= 单一来源或实测推断；【低】= 推测

---

## 0. 结论速览（TL;DR）

1. **官方从未公布 "40 分钟" 这个数字**。官方 ClawBot 应用描述的说法是"**24 小时内**"的回复窗口（来源见 §1.3）。"约 40 分钟宽限期"是本团队自己的实测观察，没有官方文档依据；社区实测的有效窗口从"约 110 秒"到"24 小时"不等，说明服务端策略不稳定（§1.4）。
2. **context_token 只能从入站用户消息获得，没有任何主动刷新/续期端点**。iLink 协议全部端点仅 7 个（5 业务 + 2 扫码登录），无心跳/保活/刷新会话类端点（§2.1）。所有主流 SDK（qwen-code、Tencent/openclaw-weixin、epiral/weixin-bot、corespeed-io/wechatbot、photon-hq、cc-connect、openilink-hub、hermes-agent）的实现一致：仅"收到入站消息时缓存 token，回复时原样回传"。
3. **社区最大开源平台 openilink-hub 维护者明确表态**："不能静默自动续期，只能提醒后由用户回复续上窗口"（§2.3）。这是业界唯一可靠的续期手段。
4. **有争议的实测**：cc-connect 实测声称 iLink 发送端**不校验 context_token**（无 token 也能送达），ret=-2 "prepare failed" 实为"每账号 24h 消息预算/突发节流"而非 token 过期（§3.1）。与 QwenPaw/本团队的观察（无新用户消息则推送失败）看似矛盾，最自洽的解释是**双层机制**：context_token 有效期短（分钟~小时级），而"服务端会话窗口"约 24h，窗口内无 token 兜底发送仍可能成功（§3.3）。
5. **替代推送通道**：企业微信应用消息 / 群机器人 webhook 没有此类限制（access_token 2h 可随时重取、webhook 无令牌），是更可靠的主动推送通道（§4）。

---

## 1. context_token 机制与"40 分钟"说法溯源

### 1.1 机制本身（多来源一致确认）【高】

- context_token 是 iLink 协议中"当前对话上下文的会话能力令牌"，语义不是用户 ID，而是"会话能力"。入站 `getupdates` 长轮询返回的用户消息（`message_type=USER`）携带 `context_token`；出站 `sendmessage` 必须（在会话有效期内）回传该 token 才能正确投递。
- 来源：
  - epiral/weixin-bot 逆向协议文档 §5.10「context_token 的作用和生命周期」：https://github.com/epiral/weixin-bot/blob/main/docs/protocol-spec.md
  - qwen-code weixin channel 源码（`contextTokens.set(fromUserId, msg.context_token)` 仅在收到 USER 消息时触发）：本机 `~/.npm-global/lib/node_modules/@qwen-code/qwen-code/chunks/dist-DOLYHMXE.js`（packages/channels/weixin/dist/monitor.js）
  - Tencent/openclaw-weixin（腾讯官方仓）：`src/messaging/inbound.ts` L238-239 同样仅入站时缓存
  - hermes-agent `gateway/platforms/weixin.py`（ContextTokenStore，仅 `set()` 于入站消息）：https://github.com/NousResearch/hermes-agent/blob/main/gateway/platforms/weixin.py

### 1.2 "用户必须发新消息才能刷新 token"——服务端错误信息原文【高】

cc-connect issue #1640（closed）中记录 iLink 服务端返回的日志原文：

> `user must send a new message to peer %q to refresh the session token`

来源：https://github.com/chenhg5/cc-connect/issues/1640

注意：该 issue 后续实测认为这条文案"描述了一个不存在的机制"（见 §3.1 的争议），但**"token 依赖用户新消息"这一服务端行为本身**被 QwenPaw、本团队等独立观察证实。

### 1.3 官方口径：24 小时，不是 40 分钟【高】

- 微信 ClawBot（iLink 的官方产品名）应用页面官方描述原文（被社区引用）：
  > "连接 OpenClaw 与微信。当你发消息后，微信 ClawBot 仅接收 OpenClaw **24 小时**内的回复"
  - 来源：https://github.com/epiral/weixin-bot/issues/7 （引用微信官方 ClawBot 描述）
- openilink-hub（1560★ 开源微信 Bot 管理平台）README 亦写明 context_token"**24 小时过期**"：
  - https://github.com/openilink/openilink-hub README.md（"你还得自己处理 context_token、CDN 加密、24 小时过期、多 Bot 管理……"）
- openilink-hub 代码把 token 新鲜度阈值设为 24h：`internal/api/bot_handler.go` L91 `const contextTokenMaxAge = 24 * time.Hour`
- openilink issue #221：用户实测"微信手机端超过 24 小时没有发送消息会收不到消息；尝试发送会报错 409 (Conflict)"：
  - https://github.com/openilink/openilink-hub/issues/221

**结论：没有任何官方来源提到 40 分钟。"40 分钟"是本团队实测值，官方口径是 24 小时会话窗口。**

### 1.4 社区实测的有效窗口数值（互相矛盾，说明服务端策略不稳定）【中】

| 观察者 | 观察到"无用户消息后推送仍有效"的时长 | 来源 |
| --- | --- | --- |
| 本团队（signLanguage daemon） | 约 40 分钟 | 内部实测 |
| QwenPaw（agentscope-ai） | 约 110 秒（约 1-2 分钟） | https://github.com/agentscope-ai/QwenPaw/issues/6614 |
| openilink-hub 用户 | 约 24 小时 | https://github.com/openilink/openilink-hub/issues/221 |
| 微信官方 ClawBot 描述 | 24 小时 | https://github.com/epiral/weixin-bot/issues/7 |

可能的原因（推测【低】）：
- QwenPaw 的 110 秒观察与其"typing 指示器消耗一次性 token"+"10 条消息 token 上限"的框架 bug 耦合（QwenPaw issue #6696：`message_merge_enabled` 存在意义就是"缓解 10 条消息的 context_token 上限"）：https://github.com/agentscope-ai/QwenPaw/issues/6696
- 本团队 40 分钟与官方 24 小时的差异，可能是服务端按账号/会话状态动态调整，也可能与消息条数/typing 消耗有关，无法从公开资料确定。

---

## 2. 是否有主动刷新/续期方法？

### 2.1 端点全景：没有心跳/保活/刷新端点【高】

汇总 qwen-code、epiral protocol-spec、cc-connect 三处独立逆向，iLink 全部端点只有 7 个：

业务端点（5 个）：
- `/ilink/bot/getupdates` — 长轮询收消息
- `/ilink/bot/sendmessage` — 发消息
- `/ilink/bot/getconfig` — 获取配置（返回 `typing_ticket`，带 context_token 也不刷新它）
- `/ilink/bot/sendtyping` — 打字指示器（status=1 开始/2 取消，用 typing_ticket，不用 context_token）
- `/ilink/bot/getuploadurl` — 媒体上传申请
- （另有 CDN `/upload`、`/download`）

登录端点（2 个）：
- `/ilink/bot/get_bot_qrcode` — 申请二维码
- `/ilink/bot/get_qrcode_status` — 轮询扫码状态

来源：
- 本机 qwen-code chunk：`chunk-GEBV2JGB.js`（`getupdates/sendmessage/getconfig/sendtyping/getuploadurl`）
- epiral 协议文档端点清单：https://github.com/epiral/weixin-bot/blob/main/docs/protocol-spec.md
- cc-connect 实测结论："ilink 全部端点只有 getupdates / sendmessage / getuploadurl / getconfig / sendtyping（外加扫码登录），没有任何能对任意 peer 重新签发 context_token 的端点"：https://github.com/chenhg5/cc-connect/issues/1640（评论）

**没有任何"心跳/保活/刷新会话"端点。getconfig 不刷新 context_token（仅返回 typing_ticket），getupdates 无消息时不返回 token——与任务背景描述一致。**

### 2.2 各 SDK/框架的处理方式：全部"只缓存不刷新"【高】

逐一核实（均为源码级确认）：
- **qwen-code**（本机 0.22.2 最新版也相同）：仅 `contextTokens.set(fromUserId, msg.context_token)`，无任何 refresh 逻辑；0.22.2 新增的 "Typing keepalive backstop" 只是打字指示器保活，与 context_token 无关
- **Tencent/openclaw-weixin**（腾讯官方仓）：`inbound.ts` 仅入站缓存；其 PR #247 明确"没有新鲜 context_token 时微信后端会静默丢弃消息（返回 HTTP 200 空 body）"：https://github.com/Tencent/openclaw-weixin/pull/247
- **hermes-agent**：唯一"变通"是 tokenless fallback（见 §3.2）——收到 ret=-2/-14 后去掉 token 重试一次，但依然**没有刷新机制**
- **epiral/weixin-bot**、**corespeed-io/wechatbot**（618★）、**photon-hq/wechat-ilink-client**、**zongrongjin/weixin-ilink**：均为"入站缓存 + 回传"，错误时直接报"先收一条该用户的消息"
- **fastclaw-ai/weclaw** PR #84：也只是把入站缓存的 token 接到主动推送 API，不刷新：https://github.com/fastclaw-ai/weclaw/pull/84
- **QwenPaw** issue #6614 明确写："**context_token has no proactive refresh**: token comes only from inbound user messages"：https://github.com/agentscope-ai/QwenPaw/issues/6614

### 2.3 openilink-hub：业界最大平台的明确表态【高】

- issue #245「根本无法做到自动续期，但是为什么一直在宣传可以自动续期呢」（closed）：
  - 维护者 awsl233777 回复："当前 Hub 的真实能力不是'后台静默自动续期 24 小时窗口'，而是**在窗口快到期前发送提醒，需要你在微信里回复一条消息后，窗口才会重新开始计时**"；并把宣传文案从"自动续期"改为"到期提醒"、提醒文案改为"回复任意消息"：https://github.com/openilink/openilink-hub/issues/245 （含 #221 评论）
- 即：**业界当前唯一可靠的"续期"方案 = 到期前发提醒，等用户回复一条消息**。没有程序化续期。

### 2.4 QwenLM/qwen-code 仓库内讨论【高（无相关讨论）】

GitHub search `repo:QwenLM/qwen-code weixin OR wechat context_token` 返回 **0 条**。qwen-code 官方对 context_token 仅有内置文档（`qc-helper/docs/features/channels/weixin.md`）一句"会话可能过期，channel 会暂停并打日志"，无续期方案。

---

## 3. 变通方案评估

### 3.1 关键争议：iLink 到底校验不校验 context_token？【中】

cc-connect PR #1643（已合并）实测结论：
- 带伪造 token 的 sendMessage、**完全不带 token** 的 sendMessage 均返回 HTTP 200 且**消息成功送达**
- 因此认为 `ret=-2 "prepare failed"` 是"**每账号 24h 消息预算/突发节流**"（约 5-6 条/24h 触发；节流期每次发送尝试都会升级惩罚，原事故约 1 小时自然恢复，探测式重试可把故障拖到 15h+）
- 并称 "user must send a new message to refresh the session token" 是误导性文案
- 来源：https://github.com/chenhg5/cc-connect/pull/1643 、 https://github.com/chenhg5/cc-connect/issues/1640

与之矛盾但同样真实的其他观察：
- QwenPaw #6614：用户发新消息后 110 秒内推送成功、之后全部失败（**新消息确实恢复了推送能力**）
- 本团队：约 40 分钟无用户消息后推送失败，新用户消息恢复
- Tencent/openclaw-weixin #244：sendmessage 返回 ret=-2 "prepare failed"（全新绑定、无入站消息场景）

### 3.2 最自洽的解释：双层机制（推测，置信度【中】）

1. **服务端会话窗口（约 24h）**：从该用户最近一条入站消息起算。窗口内即使不带 context_token，sendmessage 也可能送达（cc-connect、hermes-agent 的 tokenless fallback 依据）。窗口过期后无 token 发送同样失败。
2. **context_token 有效期（分钟~小时级，不稳定）**：每次入站消息下发新 token，token 本身有效期短（本团队 40 分钟、QwenPaw 110 秒/10 条消息）。带过期 token 发送 → `ret=-2 "prepare failed"`。
3. **ret=-2 是多重原因的兜底错误码**：会话过期、突发节流、24h 预算耗尽都以 ret=-2 呈现，errmsg 不同（"prepare failed" / "rate limited" / "unknown error"），导致各项目归类不一。

### 3.3 方法清单（按可行性排序）

| # | 方法 | 类型 | 可行性 | 风险 |
| --- | --- | --- | --- | --- |
| 1 | **到期提醒 + 用户回复续窗口**（openilink 模式）：在已知 token 快过期前（如提前 5-10 分钟）推一条提醒，用户回复任意消息后获得新 token 与 24h 窗口 | 实测可行（openilink 生产验证） | ✅ 唯一被业界验证的可靠方案 | 依赖用户配合回复；提醒频率过高会打扰；无"静默"续期 |
| 2 | **tokenless fallback**：sendmessage 收到 ret=-2 后去掉 context_token 重试一次（hermes-agent 方案） | 实测可行（hermes-agent 已用） | ⚠️ 在服务端会话窗口（官方 24h）内有效；窗口过期后仍失败 | 可能撞上"每账号 24h 消息预算/节流"（cc-connect 视角），节流期重试会升级惩罚 |
| 3 | **降低发送频率 + 退避**：控制推送节奏（如 ≥1 分钟间隔、每日配额 ≤4-5 条），避免触发 24h 预算/突发节流 | 实测可行（cc-connect PR #1643 修复方向） | ✅ 与 token 无关的稳健手段 | 牺牲推送频率；每日条数上限低 |
| 4 | **重启/重绑 getupdates**（cc-connect #1640 早期观察） | 实测存疑 | ❌ 后续实测证明"重启恢复"其实是节流自然过期（约 1h），并非真正的 token 刷新 | 重启本身不产生新 token；无用户消息时重启也无效 |
| 5 | **bot 给自己发消息 / 模拟收到消息** | 推测 | ❌ 无任何公开证据支持；iLink 无触发入站消息的 API；getupdates 只返回 USER 类型消息，bot 自己发的（BOT 类型）不进入轮询结果 | 若尝试伪造可能触发风控 |
| 6 | **Webhook 模式替代长轮询** | 事实不存在 | ❌ iLink 协议只有 getupdates 长轮询（epiral 协议文档明确"不是 WebSocket，也不是双工流"），无 webhook；且 webhook 也解决不了"token 来自用户消息"的根本约束 | — |
| 7 | **多 bot 账号轮换 / 主动保活心跳（sendtyping 循环）** | 推测 | ❌ sendtyping 用 typing_ticket 而非 context_token，不刷新会话；无证据支持"打字指示器保活能续 token" | 高频 sendtyping 可能被风控 |

### 3.4 对本团队现有实现的直接建议（结合 weixin_push.py / context_tokens.json）

- 现状：`weixin_push.py` 读 `~/.qwen/channels/weixin/context_tokens.json` 中最近一次用户消息的 token；超过宽限期即 ret=-2。
- 建议按优先级落地：
  1. **tokenless 兜底**：sendmessage 收到 ret=-2 时，去掉 context_token 再试一次（对齐 hermes-agent 行为）；若仍失败则明确报"会话窗口过期，需用户回复"。
  2. **到期提醒**：把"距最近用户消息 X 分钟"作为 token 新鲜度指标，接近阈值（建议按团队实测的 40 分钟，保守取 30 分钟）时先推一条提醒，引导 Owner 回复。
  3. **发送限速**：主动推送保持 ≥60s 间隔、日配额 ≤4-5 条，避免触发 24h 预算/节流（cc-connect 教训）。
  4. **不要重试风暴**：ret=-2 后严禁 3×500ms 式猛打重试（cc-connect 实测每次尝试都升级惩罚）。

---

## 4. 替代推送通道（无 40 分钟/24h 限制）

### 4.1 企业微信应用消息（推荐，作为正式通道）【高】

- 接口：`POST https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=ACCESS_TOKEN`
  - 官方文档：https://developer.work.weixin.qq.com/document/path/90236
- 凭证：`GET https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=ID&corpsecret=SECRET`，`expires_in=7200`（2 小时），**过期后随时重新调用即可**，不依赖用户消息、无会话窗口概念
  - 官方文档：https://developer.work.weixin.qq.com/document/path/91039
- 频率：每应用对同一成员 ≤30 次/分钟、1000 次/小时
- 限制：收件人需在企业通讯录（`touser`/`toparty`/`totag` 指定）；消息送达企业微信 App（成员可绑定个人微信接收，属企业微信"微信插件"能力）
- 风险：需要注册企业微信组织 + 把目标用户加为成员；个人微信接收依赖成员主动绑定；属官方正式 API，无封号风险

### 4.2 企业微信群机器人 Webhook（最轻量）【高】

- 接口：`POST https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=KEY`
  - 官方文档：https://developer.work.weixin.qq.com/document/path/91770
- 凭证：webhook URL 自带 key，**无需 access_token、无任何会话/时间窗口限制**，可随时主动推送
- 频率：每个 webhook ≤20 条/分钟
- 限制：只能推到**群聊**（不能单聊）
- 风险：key 泄露即可被任意调用（注意保密）；发群消息有被群成员投诉的可能

### 4.3 微信客服（WeChat Customer Service）——不推荐【高】

- 官方文档：https://developer.work.weixin.qq.com/document/path/94670
- **会话制**：只能在该用户进入会话后 **48 小时**内回复，且每会话 ≤5 条；"会话已过期（超过48小时）"是官方列出的失败类型
- 结论：不适合作为随时主动推送通道，仅适合"客服场景"。

### 4.4 对比小结

| 通道 | 主动推送限制 | 凭证 | 收件方 | 落地成本 |
| --- | --- | --- | --- | --- |
| 微信 iLink bot | 依赖用户消息续窗口（官方 24h / 实测 40 分钟~110 秒） | context_token（无刷新） | 个人微信单聊 | 已落地，有硬伤 |
| 企业微信应用消息 | 无会话窗口；30 次/分钟/成员 | access_token（2h 可重取） | 企业成员（企业微信 App/个人微信） | 需建组织+加成员 |
| 企业微信群机器人 | 20 条/分钟 | webhook key | 群聊 | 最低 |
| 微信客服 | 48h 会话窗口 + 每会话 5 条 | access_token | 外部微信用户 | 需客服账号 |

---

## 5. 风险提示汇总

- **封号/风控风险**：iLink 是对个人微信账号的官方 Bot 通道，任何"伪造入站消息""高频打字保活""高频探测发送"等尝试都可能触发风控（cc-connect 实测节流惩罚会因尝试而升级，最长 15h+）；建议不做任何协议外动作。
- **依赖用户配合**：所有"续期"最终都依赖用户回复消息；自动化程度不可能 100%。
- **多源矛盾**：ret=-2 的归因在社区存在"token 过期"vs"24h 预算/节流"两种结论，本报告采用双层机制解释（§3.2），若后续实测发现纯 token 模型成立（tokenless 也失败），应优先切换企业微信通道。

---

## 6. 关键证据来源清单

1. 微信官方 ClawBot 描述（24h 回复窗口）：https://github.com/epiral/weixin-bot/issues/7
2. epiral/weixin-bot 协议文档（context_token 生命周期、端点清单）：https://github.com/epiral/weixin-bot/blob/main/docs/protocol-spec.md
3. QwenPaw #6614（无主动刷新、110 秒实测）：https://github.com/agentscope-ai/QwenPaw/issues/6614
4. QwenPaw #6696（typing 消耗一次性 token、10 条上限）：https://github.com/agentscope-ai/QwenPaw/issues/6696
5. cc-connect #1640（服务端错误文案、实测争议、重启非恢复机制）：https://github.com/chenhg5/cc-connect/issues/1640
6. cc-connect #1643（token 不校验、24h 预算/节流结论，已合并）：https://github.com/chenhg5/cc-connect/pull/1643
7. openilink-hub #221/#245（维护者确认不能静默续期、到期提醒方案）：https://github.com/openilink/openilink-hub/issues/221 、 https://github.com/openilink/openilink-hub/issues/245
8. openilink-hub README/源码（24h 过期、contextTokenMaxAge=24h）：https://github.com/openilink/openilink-hub
9. Tencent/openclaw-weixin #244（getupdates 空消息、ret=-2）：https://github.com/Tencent/openclaw-weixin/issues/244 ；PR #247（无 token 静默丢弃）：https://github.com/Tencent/openclaw-weixin/pull/247
10. hermes-agent weixin.py（tokenless fallback 实现）：https://github.com/NousResearch/hermes-agent/blob/main/gateway/platforms/weixin.py
11. 企业微信官方文档：gettoken https://developer.work.weixin.qq.com/document/path/91039 ；发送应用消息 https://developer.work.weixin.qq.com/document/path/90236 ；群机器人 webhook https://developer.work.weixin.qq.com/document/path/91770 ；微信客服 https://developer.work.weixin.qq.com/document/path/94670
12. qwen-code 本机源码：`/home/wuyangcheng/.npm-global/lib/node_modules/@qwen-code/qwen-code/chunks/dist-DOLYHMXE.js`、`chunk-GEBV2JGB.js`（0.22.2 版位于 `~/.qwen/updates/npm/8d75156e24ed8050/versions/0.22.2/`）

---

*报告完。本报告为纯网络调研产物，未调用任何微信 API、未发送任何消息。*

# 团队信息结构与身份维护机制 v1

- 版本：v1（2026-08-29 建立）
- 维护者：顾问（advisor）协助建档；主管（SignL3）维护团队级内容
- 最后更新时间：2026-08-29 22:26（北京时间）
- 约束落盘：`.team/team_constraints.md §4`、`QWEN.md §2.5 §5`
- 目的：让「团队成员每次都正确知道：自己是谁、团队规则是什么、自己的信息放哪、如何维护」——机制稳定、可复用、非一次性。

> 📌 **通用 vs 实例**：本文件是 **signLanguage 实例**的落地细节（含本团队的具体文件名/端口/角色值）。**通用标准规范**（可套用到其他 agent team）在 `framework/agent-team-management-daemon.md`（daemon 版，占位符表述）与 `framework/agent-team-management.md`（旧 tmux 版，LEGACY）。新团队起团队时**参照通用规范 + 本文件作实例对照**。

---

## 0. 背景与问题（为什么建这套机制）

2026-08-29 审视团队信息结构时发现若干真实缺陷：

1. **命名不一致**：同一角色在 `team_topology.json`、`registry.json`、daemon 实际 `displayName`、supervisor 展示名四处名字不一（如「视频负责人」「视频」，displayName「本地A 游戏」）。
2. **身份无强制注入**：成员会话**没有**"你是 XX"的 per-role 系统提示词；身份靠记忆 + 消息前缀维持，易混淆（曾发生"本地A 误认 Jarvis""顾问误认本地A"被纠正）。
3. **公共约束非自动**：完整公共约束在 `.team/team_constraints.md`，成员只能通过 QWEN.md §1 一句话得知"需主动读取"，不读则缺失。
4. **member_memories 覆盖不全**：11 角色只有 6 个有记忆文件；主管/调研/本地A/本地B/顾问缺。
5. **QWEN.md §5 过时**：仍写旧 GPU 格局（GPU1 严禁/GPU9 留 VL/GPU0 训练默认），与现行约束冲突，而 QWEN.md 是成员**唯一自动加载**的团队指令。

---

## 1. 核心机制一：命名一致性

**唯一权威源 = `team_topology.json` 的 `roles[*].name`**（正式中文名：主管/视频/语义动画/算法/运维/调研/本地A/本地B/顾问）。

**需一致（正式业务名）的三层**：
- `registry.json` 的 `roles[*].name`
- supervisor state 的 `name`（展示名）

**仅供参考（不参与一致性判定）**：
- daemon 实际 `displayName`（侧边栏标题）——**允许用户自主修改**（如加「游戏」「小说」后缀），不强制与拓扑名一致。
- `roles[*].name_en`（英文语义名）——**纯描述、不驱动任何逻辑**，仅供理解含义。

### 工具脚本
| 脚本 | 用法 | 作用 |
|---|---|---|
| `work/scripts/team_identity_audit.py` | `python3 team_identity_audit.py` 或 `--write-md` | 审计四层一致性，发现漂移输出报告（exit 0=一致、1=有漂移）；写到 `.team/identity_audit_report.md` |
| `work/scripts/team_sync_displaynames.py` | `--dry-run` 预览 / `--apply` 执行 / `--sync-registry` 同步 | 一键把 daemon displayName 对齐到拓扑正式名 |

### 改名后必做（防 supervisor 展示旧名）
```bash
# 1. 改 team_topology.json 的 name
# 2. 同步 daemon + registry
python3 work/scripts/team_sync_displaynames.py --apply --sync-registry
# 3. 重启 supervisor（kill 后由 while 循环自动重载）
pkill -f "team_progress_supervisor_v2.py"
```

> **根因**：supervisor `check_role` 原来用 `state.setdefault(role, {"name": name})`——只在键首次创建时写入，改名后 state 里的 `name` 不更新。
> **修复**：`check_role` 现每次同步 registry 最新 `name`/`session_id`；`write_digest` 状态段只展示 registry **当前注册角色**（已退出的 signL6/宣传员不再带出）。这两处修复已并入 `team_progress_supervisor_v2.py`。

---

## 2. 核心机制二：身份 + 公共约束注入到成员对话

### 2.1 Qwen Code 官方指令注入管线（源码实证）
| 层 | 通道 | 作用域 | 效果 |
|---|---|---|---|
| 项目规则 | `.qwen/rules/*.md`（全局 `~/.qwen/rules/` + 项目 `.qwen/rules/`） | **每成员会话** | `loadRules()` 动态 `readFileSync`，**无缓存、每 turn 生效**，拼进 system prompt 规则层（`--- Rule from: ---`）|
| 默认指令 | 根 `QWEN.md` | 每成员会话 | 自动加载（`getContextFileNames` 默认 `["QWEN.md"]`）|
| 核心身份 | `QWEN_SYSTEM_IDENTITY_MD` env → 身份文件 | 每进程 | 覆盖 `You are Qwen Code...` 身份句 |
| 完整系统指令 | `QWEN_SYSTEM_MD` env → system.md | 每进程 | 完全替换默认 system prompt |
| per-session hint | LSP `initializationOptions.instructions` | 每 session | 需 daemon 深改造，高风险 |

### 2.2 本方案落地（2026-08-29）
- **共享规则**：`.qwen/rules/team_identity_profile.md` —— 11 角色身份表 + 公共约束摘要。**每成员会话自动加载**（这是身份信息落到对话的保证）。
- **各自身份文件**：`.team/roles/<角色id>.md` —— 每个含"你是 signLanguage 团队的 XX"+ 职责/模型/消息前缀/关键红线/维护职责。
- **QWEN.md §2.5**：成员自我识别指引（从规则表确认角色 → 读自己的身份文件 → 维护自己的工作记忆）。

### 2.3 ⚠️ 重要局限（如实说明）
`QWEN_SYSTEM_MD`/`QWEN_SYSTEM_IDENTITY_MD` 是**进程级** env。daemon（4194）是**单进程内嵌 9 个 session**，因此**无法按 session 区分不同身份**——若设置，则整个 daemon 统一一个身份。
- 因此 per-role 身份靠「**共享规则表 + 各自身份文件**」实现（成员从表识别自己 + 主动读自己文件），而非「每 session 独立 system prompt」。
- 若要**真正的 per-role 系统级注入**，需「每角色独立 daemon 进程」（大改）或「per-session `initializationOptions.instructions`」（深改造）。

---

## 3. 核心机制三：分层维护职责（谁维护什么）

所有成员信息统一落盘在项目 `.team/` 目录，**各层维护者唯一、不越权**：

| 信息类型 | 路径 | 维护者 | 内容 |
|---|---|---|---|
| 公共约束 | `.team/team_constraints.md` | **主管** | 安全/资源/汇报/职责/仓库边界/daemon 管理；变更须经用户确认 |
| 团队身份/公共约束摘要 | `.qwen/rules/team_identity_profile.md` | **主管** | 11 角色身份表 + 公共约束摘要（成员会话自动加载）|
| 团队拓扑/服务注册表 | `.team/team_topology.json` | **主管+运维** | roles 稳定 id/窗口、local_model_services 端口/GPU/ctx/状态；服务变更运维执行、主管确认后 24h 内更新 |
| 角色身份文件 | `.team/roles/<角色id>.md` | **各角色自己** | 自己的 name/职责/模型/会话id/关键身份（"你是 XX"）；主管/顾问发现缺文件时补建骨架 |
| 成员工作记忆 | `.team/member_memories/member_memories_<成员id>.md` | **各角色自己** | 当前任务状态/关键决策/待办/踩坑；主管可直接读取 |
| 团队进展（单一事实源） | `.team/daemon_v1/progress_supervisor/latest_progress.md` | **监督器自动** | 各角色状态/待汇报进展；监督器重写，勿手改 |
| 团队信息一致性审计 | `.team/identity_audit_report.md` | **监督器/主管** | `team_identity_audit.py --write-md` 产出 |

**维护原则**：① 主管维护"团队级"，不改各角色分内文件；② 各角色维护"自己分内"，不改公共约束/他人文件；③ 顾问可协助发现/补建骨架、审计一致性，但不越权代改；④ 新增文件一律带 frontmatter（`--- description: ... ---`）。

---

## 4. 工具脚本清单（复用）

| 脚本 | 路径 | 用途 |
|---|---|---|
| 一致性审计 | `work/scripts/team_identity_audit.py` | 四层命名一致性审计（漂移即报）|
| displayName 同步 | `work/scripts/team_sync_displaynames.py` | 对齐 daemon displayName 到拓扑名 |
| 进度监督器 | `work/scripts/team_progress_supervisor_v2.py` | 团队进展自动监督 + 微信直推 |

---

## 5. 新增 / 退出角色标准流程（复用）

### 5.1 新增常驻角色
1. `team_topology.json` 的 `roles` 加条目（id/name/窗口/duty/model/local_service/effort），并设 `_updated_at`。
2. `registry.json` 的 `roles` 加同名条目（含 `session_id`、`live.displayName` 等）。
3. 建 `.team/roles/<id>.md`（身份文件，含"你是 XX"）+ `.team/member_memories/member_memories_<id>.md`（工作记忆骨架）。
4. `.qwen/rules/team_identity_profile.md` 身份表加一行（主管维护）。
5. 配置 SSE member helper（`daemon_team_member_helper_v2.py --role <id> --session-id <sid>`），入队必要条件。
6. 跑 `team_sync_displaynames.py --apply --sync-registry` 对齐 displayName，重启 supervisor。
7. 验证 `team_identity_audit.py` 通过。

### 5.2 退出角色（如 signL6/signL7）
1. 从 `team_topology.json` 的 `roles` 移除或标记 `disabled`。
2. 从 supervisor state / `_memories` 清除该角色键。
3. `.qwen/rules/team_identity_profile.md` 身份表标记"已退出"。
4. 确认 registry/topology `roles` 不再含该角色；unassigned session 保留供历史参考。
5. 不再提及、不再审计、不再纳入监督。

---

## 6. 本次修复记录（2026-08-29）

- **QWEN.md §5**：修复过时 GPU 格局（GPU0/1 禁用、GPU2-9 弹性池 g29/g34/g56/g78、GPU9 并入 g29、vLLM 清理红线）。
- **displayName 统一**：PATCH daemon 6 角色（signL2/4/5/9/10/11 → 视频/语义动画/算法/调研/本地A/本地B）+ 修正 supervisor state 旧名快照 5 处 + 同步 registry。
- **member_memories 补齐**：SignL3/signL9/signL10/signL11/advisor 建档，修正 signL8/signL5 陈旧 GPU 格局。
- **退出清理**：signL6（字幕员）/signL7（宣传员）已退出 team，从 supervisor state/记忆清除。
- **自维护脚本**：新增 `team_identity_audit.py`、`team_sync_displaynames.py`；修复 supervisor 的 `check_role`/`write_digest`。
- **团队资产纳入 git**：根 `QWEN.md`、`.team/roles/`、`.qwen/rules/`、`team_constraints.md` 变更已 `git add`（暂存未提交）。
- **displayName 放开（不强制一致）**：`displayName`（侧边栏标题）允许用户自主修改（如加「游戏」「小说」后缀），**不参与一致性判定**——`team_identity_audit.py` 已把 displayName 降为"仅供参考"，仅校验正式业务名（拓扑名/registry.name/supervisor state name）。
- **角色 id 定位 + name_en**：`roles[*]` 的键（`SignL3`/`signL2`）是**程序稳定标识**（registry/topology/members 目录用），不用于理解含义；理解看 `name`（中文正式名）或新增的 `name_en`（英文语义名 `supervisor/video/algorithm/ops/...`，**纯描述、不驱动任何逻辑**）。id 与早期 tmux 窗口无绑定（tmux 窗口已废弃，daemon 时代用 session_id）；**id 不建议改成语义化英文**（深嵌运行逻辑，风险大收益低）。`team_identity_audit.py` 校验不含 name_en。

---

## 7. 关键文件路径索引

- 公共约束：`/data/WYC/signLanguage/.team/team_constraints.md`
- 团队拓扑/服务注册表：`/data/WYC/signLanguage/.team/team_topology.json`
- 团队身份+公共约束规则：`/data/WYC/signLanguage/.qwen/rules/team_identity_profile.md`
- 各角色身份文件：`/data/WYC/signLanguage/.team/roles/*.md`
- 各成员工作记忆：`/data/WYC/signLanguage/.team/member_memories/*.md`
- 团队进展（单一事实源）：`/data/WYC/signLanguage/.team/daemon_v1/progress_supervisor/latest_progress.md`
- 一致性审计报告：`/data/WYC/signLanguage/.team/identity_audit_report.md`
- 审计脚本：`/data/WYC/signLanguage/work/scripts/team_identity_audit.py`
- displayName 同步脚本：`/data/WYC/signLanguage/work/scripts/team_sync_displaynames.py`
- 进度监督器：`/data/WYC/signLanguage/work/scripts/team_progress_supervisor_v2.py`
- 本机制文档：`/data/WYC/signLanguage/work/documents/team_info_structure_maintenance_v1_20260829.md`

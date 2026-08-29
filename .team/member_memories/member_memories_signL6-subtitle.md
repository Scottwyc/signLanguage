# 成员记忆：signL6-subtitle（字幕员）

> 约定（公共约束 §4，2026-08-11/12）：每个成员维护本文件，记录当前任务状态/关键决策/待办/踩坑；**主管可直接读取**，实现 Qwen/Codex 成员记忆互通。任务阶段切换/完成/重要结论时更新。格式：`日期 | 事项 | 详情`。
> 本文件规范路径（2026-08-12 迁移后）：`/data/WYC/signLanguage/.team/member_memories/member_memories_signL6-subtitle.md`
> 维护义务（§4，2026-08-12）：重要进展持续写 team_confirmations.log（monitor 5s 抓取）或 progress/signL6-subtitle.txt；同步更新本记忆文件；公共事实（工作线/部署/新增产出/资源变化）同步 .team/ 共享文件——不得只留在 CLI 私有记忆或对话里

## 当前任务状态（2026-08-12 更新）

- **派生 skill：稿件驱动中英字幕（2026-08-12）**：✅ 完成
  - 新 skill `produce-bilingual-subtitles-from-script`（Base: produce-bilingual-conference-subtitles v2），位于 work/tools/ + ~/.qwen/skills/
  - 脚本：parse_script_docx.py（DOCX 表格/段落自适应、镜头块英中按序配对、段数不等前缀合并、去括号注释）、align_script_to_asr.py（ASR 词级时间戳↔稿件英文对齐）、build_cue_plan_from_script.py、run_script_subtitle_pipeline.py（复用 v2 下游全链路+片头）
  - 用户确认的关键约定：**ASR 始终运行**（时间轴唯一来源）；字幕文本 100% 取稿件并去括号注释；稿件时间码仅参考
  - 自测：GSE 反向稿件 52/52 精确一致 + 无时间码对齐 52/52；真实分镜稿《智能时代教师如何升级》解析 26 条配对正确括号清洗干净；内容不匹配时对齐不崩溃并报告 unmatched
  - 提取结果：`/data/WYC/signLanguage/work/subtitle/out/教师升级分镜稿_提取字幕.md`
  - **待办：用户提供对应英文视频后一键全流程**（ASR 对齐→cue→SRT/ASS→VL QA→烧录）

- **双语字幕自动化流水线**：✅ 已端到端跑通
  - 编排脚本：`/data/WYC/signLanguage/work/subtitle/scripts/run_subtitle_pipeline.py`（自动转码 → 转写 → cue plan → SRT/ASS → QA → 渲染 → **VL 视觉 QA（可选桥接）** → 烧录）
  - 支持 `--transcode-only` / `--subtitle-only` / `--no-transcode` 分开模式；无 `--cue-plan` 时生成模板并停（翻译环节由字幕员人工提供）
  - 4K 输入端到端测试通过：`/data/WYC/signLanguage/work/subtitle/pipeline_runs/test_4k/test_4k_burned.mp4`（h264 High/1920x1080/yuv420p/30fps/AAC，VL 视觉 QA 复核干净）
- **VL 自动 QA 正式接入（主管确认 2026-08-11）**：✅ 烧录前自动跑；**设计为可选桥接**——主模型无视觉时经本地 qwen3-vl-8b 桥接；桥不可用自动告警跳过不阻断；失败帧聚焦复核降误报；`--skip-vl-qa` / `--vl-qa-max-fail` 控制
  - 已实测两条路径：VL 可用→5 帧全过→烧录；VL 不可用(死端口)→告警跳过→仍完成烧录
- **skill 同步（主管任务 ③）**：✅ 已同步 `~/.qwen/skills/produce-bilingual-conference-subtitles/`（run_subtitle_pipeline.py 更新版 + SKILL.md 补完整工作流/可选 VL QA 桥接说明/用法示例）
- **GSE2026 3min 真实视频**：✅ 用户验收通过（2026-08-12）。产物 out/GSE2026_3min_Fabrizio_{burned.mp4,srt,ass}（h264 High 1080p 30fps AAC 179.63s，52 条双语，VL QA 通过）
- **交互时间自动化（2026-08-12，待修正）**：⚠️ UserPromptSubmit 是 Claude Code 事件名，codex 无此事件——配置已被主管注释（config.toml 现为 [notify] 测试）；脚本 /data/WYC/signLanguage/.team/scripts/touch_interaction_codex.py 本身可用但缺触发；**当前兜底**：每次收到用户直接输入手动写 user_last_interaction/signL6-subtitle.txt；恢复自动写入等主管查清 codex 正确事件/notify 机制后统一配置（不擅自改）
- **v2 片头 title 融入（2026-08-12）**：✅ 官方 v2（work/tools/produce-bilingual-conference-subtitles_v2/）已融入 skill：add_speaker_title.py（Apple 风格左下角 5 元素片头）、speaker-title-standards.md、qa_subtitles v2（SpeakerTitle 单独统计）、render/burn --canvas-size；编排脚本新增 --title-* 参数（build→加片头→QA→渲染→VL QA→烧录）；clip01 带片头端到端实测通过（VL 逐字读出确认），测试产物 out/clip01_title_test_burned.mp4；SKILL.md 已合并同步 skill 与 v2
- **批量视频转码工具**：✅ 完成
  - `/data/WYC/signLanguage/work/subtitle/scripts/transcode_batch.py`（H.264/1080P/30fps，目录批处理，覆盖 720p/1080p/竖屏 webm/4K）
- **音频诊断**（sub Linnaeus 完成，2026-08-11）：文件音轨全部正常（AAC，mean -28~-35dB）
  - 服务器 headless：仅 NVIDIA HDMI 音频且无输出设备，PulseAudio 默认 sink=auto_null（Dummy，未 mute）——服务器侧 mute 路径排除
  - 用户是 Remote-SSH（.vscode-server + DISPLAY 转发）→ 视频在用户**本地** VS Code 客户端播放，声音走本地声卡，服务器不可见客户端静音状态
  - 最可能原因排序：本地标签页/预览静音 → OS 音量合成器条目静音 → 预览播放器限制 → 音轨偏轻（mean -35dB）
  - 定位用测试音：`/data/WYC/signLanguage/work/subtitle/test_in/audio_test_tone.mp4`（5s 440Hz，mean -21dB，等用户试听反馈）

## 待办 / 待确认（等主管/用户指示）

1. **GSE2026 15min 版**（可加片头 title）：15min 版（GSE2026 15min Fabrizio.mp4，≈887MB）到手后可直接跑同一工作流（可带 --title-*）；百度网盘下载仍 BLOCKED 需登录态或用户自行下载
2. **loudnorm 优化**：音频加 `--loudness-normalize`（AAC 编码前 loudnorm 到 -14 LUFS）作默认优化？待用户确认（未写入 SKILL.md）

## 踩坑记录

- **FFmpeg libass**：`render_samples.py` 的 `ass_capable_ffmpeg()` 只查 PATH 和写死路径——需用 `--ffmpeg` 显式指定 conda 环境 ffmpeg
- **29.97fps 间隔取整**：SRT 毫秒取整会吃掉恰好 2 帧的间隔（QA 报 0.066s<0.067s）→ build 用 `--fps 30 --min-gap-frames 3`（QA 仍按 2 帧标准）
- **VL 整帧漏检**：qwen3-vl-8b 在整帧小图上会漏报“无字幕帧”→ 裁剪底部字幕带（crop=1920:360:0:720）后 VL 可逐字读出并判定；部分“遮挡/描边”标记为小图误判，需聚焦放大复核
- **ASR 人名纠错**：Mikowski→Murkowski、Unifair Banks→you, Fairbanks（用 initial-prompt 重转写验证，展示文本用校正后官方拼写并报告）
- **转码策略**：>1080p 等比缩到 1080p 内（4K→1920x1080）；≤1080p 保持原分辨率不放大（无信息增益）
- **.webm 播放兼容**：部分 .webm 源文件在播放器听不到声音（非产物问题）
- **音频定位**：服务器 headless（dummy sink）+ Remote-SSH 客户端本地播放 → 听不到声音先查本地静音/音量合成器，再怀疑音轨偏轻
- **本成员为 codex 会话**（协作试验）：记忆私有存储 `~/.codex/memories/`，与 Qwen 不互通——关键事实已写入本共享文件

## 其他

- 字幕规范锁定：中文 48px / 英文 36px、纯黑描边无阴影、中文无逗号句号（空格+问号保留）、cue 间隔≥2 帧
- 工具包：`/data/WYC/signLanguage/work/tools/produce-bilingual-conference-subtitles/`（SKILL.md）
- **用户不在场约定（2026-08-12）**：完成/异常/里程碑/需用户介入事项 → 一律后台通道通知主管（team_confirmations.log 由 monitor 转发；需介入事项报主管转达用户）；配合 user_last_interaction 在线判定
- **新成员 signL7-promoter（2026-08-12）**：宣传员，中英双语项目介绍面板制作，tmux 窗口 signL7-promoter，平级、直接向主管汇报（§8/§9 已更新）
- **新成员 signL8-resource（2026-08-12）**：资源管理员，外部资源/API 测试与接入，tmux 窗口 signL8-resource，平级、直接向主管汇报；涉及外部资源/API（网盘下载、VL 服务等）可平级协调
- **公共约束 §11 仓库职责边界（2026-08-12）**：/data/WYC/signLanguage=私有研发仓（原始视频/数据库/实验/管线不进公开仓）；/data/WYC/sign-language-universe=开源产品仓（GitHub Pages，走 PR）；红线：原始视频/身份信息/未脱敏生物特征/私有数据库禁止进公开仓，公开仓改动必做脱敏检查；我方字幕产物迁公开仓前必做脱敏评估
- **公共约束 §12 服务器/环境/资源（2026-08-12）**：nature=本机主工作机；zhuhai(172.28.17.71 无sudo)：GPU1永远避开(liuchang)、GPU9留VL(qwen3-vl-8b:8000即我方桥接)、GPU0训练默认、GPU0-8不抢占、CPU限核优先liuchang、GitHub慢用nature中转；edu(59.64.38.5:9000)教育网大模型API(OpenAI兼容/v1)；GFW需代理127.0.0.1:18080(OpenAI/Google)，DeepSeek/GitHub直连；禁rm/rmdir(用mv或Path.unlink)；长任务setsid nohup保活+进度输出；本地Web服务只绑127.0.0.1


## 上下文迁移接续记录（2026-08-12T19:18:59+08:00）

- 旧 Codex 会话 `019fefe1-3254-7112-bfbc-3a4b2f922b5b` 绑定 DeepSeek，按主管批准不 resume；当前继续使用新 GPT 会话 `gpt-5.6-luna-chatgpt` / `xhigh`，路由正常。
- 旧历史备份保留于 `/home/wuyangcheng/.codex/sessions_bak_20260812/`；共享日志记录的两跳 imported-codex 测试会话仅作只读参考，不作为正式工作会话。
- 已按 `qwen-codex-context-migrate` skill 阅读规范并执行 Codex inspect/dry-run；不把 dry-run 或中间会话误报为当前正式会话已完成历史导入。
- `codex_notify_test.py` 的 `[notify]` 测试仍待 signL8 运维确认实际触发时机与 payload；当前不擅自改 `/home/wuyangcheng/.codex/config.toml`，`UserPromptSubmit` 相关自动写入继续手动兜底。
- 调查记录：`/data/WYC/signLanguage/work/reports/codex_notify_hook_research_20260812.md`。


## edu翻译任务记录（2026-08-12T22:16:27+08:00）

- 按signL8协调调用edu `http://59.64.38.5:9000/v1` 的 `Qwen3.6-27B-Coder`，翻译GSE2026_3min模板10条英文长cue。
- 产出：`/data/WYC/signLanguage/work/subtitle/pipeline_runs/GSE2026_3min/GSE2026 3min Fabrizio/GSE2026 3min Fabrizio_cue_plan.edu_qwen3.6-27B-Coder.json`；原始响应与耗时：`/data/WYC/signLanguage/work/subtitle/pipeline_runs/GSE2026_3min/GSE2026 3min Fabrizio/GSE2026 3min Fabrizio_edu_translation_raw.json`。
- 对比：edu保留10条模板边界；基线为52条短cue（平均每条长cue对应5.2条短cue）。edu语义完整度较高但长cue不宜直接烧录；“更宏大”“通过教育融合”等建议人工润色。
- 结论报告：`/data/WYC/signLanguage/work/subtitle/pipeline_runs/GSE2026_3min/GSE2026 3min Fabrizio/GSE2026 3min Fabrizio_edu_vs_baseline_conclusion.md`；结构化对比：`/data/WYC/signLanguage/work/subtitle/pipeline_runs/GSE2026_3min/GSE2026 3min Fabrizio/GSE2026 3min Fabrizio_edu_vs_baseline_comparison.json`。

## 2026-08-26 daemon 重启规则 v3（系统通知）

- 4194 daemon 任何重启必须调用外部脚本 `bash /data/WYC/signLanguage/work/scripts/restart_daemon_4194_v3.sh`，禁止成员自行 kill/启动 daemon
- 重启会中断工作会话，收到「【系统通知】daemon 重启，任务被中断…请继续完成」时：检查 sub/后台任务（list_agents）并继续未完成工作
- 详见 agent-team skill §8 与通用 skill daemon-restart-continuity

## 2026-08-26 主管新增介入推送能力（确认）

- **需 Owner 人工介入/决策** → 直接运行 `python3 /data/WYC/signLanguage/work/scripts/weixin_intervention.py "内容"` 秒级推送 Owner 微信（格式【人工介入】字幕员：内容），不用等监督器轮询
- **ask_user_question 提问**自动推送 Owner 微信，Owner 回复后由 Jarvis 自动提交选项，无需等待

## 2026-08-18 daemon 注册
- session_id=302e296e-0a9d-54d8-9772-ad3d09a206b8（displayName=字幕员，workspace=/data/WYC/signLanguage）
- 已加入 .team/daemon_migration_4194_manifest.json roles.signL6（备份 .bak_pre_signL6_register）
- registry 状态 listed，可通过 mailbox 接收消息（--to-role signL6 或 --to-session 302e296e...）
- 已向主管发送注册通知（message_id d7add260-a2c6-4df9-bde1-fcf07d2522c6）

## 2026-08-27 系统通知三项修复（确认，回执已写 team_confirmations.log 19:34）

- **context 压缩后补发「继续」**：context 超限自动压缩（/compress-fast→/compress）完成后会补发「继续」消息——收到即检查 sub/后台任务（list_agents）并继续未完成工作
- **本地模型 JSON 流式报错已修复**：代理重启生效，与字幕工作无直接关联（字幕 ASR 走 faster-whisper CPU、视觉 QA 走 vl-8b）
- **GPU0+2 实例迁移 GPU2+9**：模型名 qwen3.8-27b-int4-tp2-g29，原 g02 名称停用；主管/Jarvis 已迁移，其余成员模型不变；TP2 槽位现为 g29/g34/g56/g78。本成员字幕链路不使用该实例，仅记录
- **成员↔本地模型映射自动同步**：team_topology.json 角色→模型映射由 refresher 每 5s 从 daemon 自动同步（60s 节流写盘），成员切换模型后拓扑/看板自动对齐，无需手工维护
- 后台 agent 核验：list_agents 显示「稿件驱动字幕全流程」（general-purpose-call_00_hwP6qkrYB8G1loNd7uMc6437）status=completed，与上轮核验同一 agent，已闭环无需继续
- 当前状态：V11（out/xiaohuiFinalV11_zh40_burned.mp4）等待 Owner 验收，无新任务

## 2026-08-29 4194 重启规范 v2（确认，回执已写 team_confirmations.log）

- **4194 daemon 任何重启必须用外部触发入口**：`bash /data/WYC/signLanguage/work/scripts/restart_daemon_4194_trigger.sh`（`--force` 强制重启；不加则仅在 4194 已挂时补启，健康时不打扰）
- **禁止直接前台执行 `restart_daemon_4194_v3.sh`**（也禁止自行 kill/setsid/tmux 重启）
- 原因：直接前台跑 v3 时，SSH/tmux 断开会在 kill 旧 daemon 后、启动新 daemon 前杀掉 v3 → 4194 挂死（8-28 23:09、8-29 02:11 两次事故根因）；wrapper 用 setsid --fork 脱离独立会话，调用立即返回、终端断开也完整跑完（kill→启动→恢复模型→发「继续完成」）
- 调用后查看结果：`tail -50 /data/WYC/signLanguage/work/logs/daemon_restart_4194.log`
- 已同步更新全局 feedback 记忆 daemon-restart-use-tmux.md（v3 → trigger wrapper v2）
- 后台 agent 复核（2026-08-29）：仍是「稿件驱动字幕全流程」（general-purpose-call_00_hwP6qkrYB8G1loNd7uMc6437）status=completed，已闭环无需继续；V11 继续等待 Owner 验收

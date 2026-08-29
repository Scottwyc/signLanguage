# 成员记忆：signL7-promoter（宣传员）

## 角色职责
- 制作『手语小宇宙』（sign-language-universe）项目的介绍面板/宣传文档（中英双语），输出 md + docx
- 排版参考：/data/WYC/signLanguage/docs/2025实验室手册.pdf（中英并排、权威背书、Vision & Mission 风格）
- 模板结构：/data/WYC/signLanguage/docs/特殊教育项目简介模版.docx（5 部分：项目简介/项目特点/核心功能/应用场景/目标用户）
- VL 协作：zhuhai qwen3-vl-8b http://172.28.17.71:8000（GPU9，训练勿占）

## 当前任务（2026-08-15）✅ 已完成 v6（整合版）
- v6 = v5 全部修改整合：语义动作级联打分模型（去D6.1编号）+ 语义头门控 + 完全本地化隐私（无需上传任何数据）+ 综合分/语义头分数与逐条建议 + 联系人占位(xxx) + 用户原图配图
- v6 产出：/data/WYC/sign-language-universe/docs/product/hand_sign_planet_project_intro_v6_{zh,en}.{md,docx,pdf} + intro_figs_20260812_v6/
- VL 复核 9.5/10；v5 及旧版保留
- v5 状态存档如下（供对照）
- v5 产出：/data/WYC/sign-language-universe/docs/product/hand_sign_planet_project_intro_v5_{zh,en}.{md,docx,pdf}
- v5 变更：AI 驱动文本更新为实际架构——**D6.1 级联模型（47 维自然语义动作头 + 总分头双头级联）+ conf 门控**（conf=目标词叶子平均激活度，47 维独立 sigmoid 非 softmax，总分=overall×min(1,conf/0.5)）；中英各更新 4 处；VL 复核 9.5/10
- 关键事实：前端实际评分=D6.1（dual_cascade_v1.onnx，默认）+ conf 门控；互动学习主路径 v5 语义打分；语义树模块已下线
- v4 状态存档如下（供对照）
- v4 产出：/data/WYC/sign-language-universe/docs/product/hand_sign_planet_project_intro_v4_{zh,en}.{md,docx,pdf} + intro_figs_20260812_v4/（7张clean图）
- v4 变更：去掉全部3D语义形象内容/图；3.2=学习宇宙分级星球；配图用主管 use 目录截图（中英配对）；图宽12.5cm；VL 两版 9.5/10
- 经验：分级/空间站界面仅有中文UI（无英文版），英文版沿用同图+英文图注；use 截图含 Holistic 就绪状态条属正常UI
- ⚠️ 重要经验：**用户提供的截图一律不裁剪，保留原图**（v4 曾统一裁 3% 去 build 标记被用户指出；已换回原图，md 引用去 _clean 后缀）
- v3 状态存档如下（供对照）
- v3 产出（/data/WYC/sign-language-universe/docs/product/）：
  - hand_sign_planet_project_intro_20260812_zh.{md,docx,pdf} / _en.{md,docx,pdf}
  - intro_figs_20260812/ 6 张 clean 图（超市语义叠加/汽车一语义叠加/汽车3D/启动页/学习宇宙/个人空间）
- VL 终审：中文 8.5/10、英文 9.5/10
- 关键经验：
  - headless 视频不渲染 → myenv conda ffmpeg 提取首帧做 video poster 最可靠
  - 跳词注入要放在 load()/renderLearning() 内确定性执行（setTimeout 竞态失效）
  - Avatar3D 渲染正常（canvas 线稿风格，VL 判断不稳定时用 PIL 像素对比佐证）
  - interactive-learning 默认英文 locale，需注入 setLocale('zh')
  - 截图需裁剪左下角 build PR 标记（底部 3%）
- 已按后台通道确认完成（team_confirmations.log）
- 已确认公共约束 §11/§12、新成员 signL8-resource
- 2026-08-13 协作机制已恢复原有规则：废弃 `{team:...}` 明文包及嵌套解析；完成/异常/里程碑使用【主管】或【人工介入请求】格式；成员确认写 team_confirmations.log 由后台 monitor 抓取；生产/GPU/权限/部署需主管审批；宣传文档由本成员负责，语义视频审核由 signL4+主管+用户闭环，公开仓部署由对应负责人执行
- 机制恢复确认已同步：.team/team_confirmations.log、.team/progress/signL7-promoter.txt
- **Owner 介入通道（2026-08-15 主管通知）**：①需 Owner 人工介入/决策时直接运行 `python3 /data/WYC/signLanguage/work/scripts/weixin_intervention.py "内容"` 秒级推微信（格式【人工介入】角色名：内容）；②ask_user_question 提问自动推送 Owner 微信，Owner 回复由 Jarvis 自动提交选项，无需等待
- **任务闭环规范（2026-08-15 主管通知）**：主管派发任务无论进度/结果/决策变化（含 Owner 直接示意）必须主动回报主管收束（发起→执行→回报→主管验收→关闭）；完成后回报成果与数据；遇阻即时回报原因与建议不沉默；被 Owner 直接示意时同步回报主管由主管知晓并关闭任务

## 关键事实（2026-08-12）
- 公共约束 §11：signLanguage=私有研发仓；sign-language-universe=开源产品仓；成熟→脱敏→迁入公开仓走 PR；原始视频/身份信息/未脱敏生物特征/私有数据库禁入公开仓
- 已确认：team_confirmations.log 追加【成员确认】signL7-promoter | 公共约束§11
- 模板 5 部分：项目简介(背景/目标/一句话) + 项目特点(3-5关键词) + 核心功能(图标或短语) + 应用场景 + 目标用户
- 前端功能清单（21 词互动学习实验室）：中英切换、主题切换（日间/夜间）、摄像头练习+浏览器 Holistic 匿名关键点、原型评分→树模型打分（tree_model_v64.onnx 语义树三层检测器：手形12+运动20+叶子47）、3D 匿名语义形象、语义过程分阶段动画、录制三视图回看（原始/Holistic 叠加/纯骨架）、星星成就积分、评分 API 预热、词汇检索（关键词/首字母/手形）、测评（理解力输入：选择/连词成句/翻译；表达力输出：动作捕捉评分）、挑战模式、21 词模板库（scoring_templates_v2.json）
- 21 词：谗/唱歌/超市/船/公交车/虎/花/鸡蛋/烤串/科学/牛奶/朋友/汽车一/汽车二/人们/森林/跳/香蕉/勇敢/月亮/指示
- 政策背书：2024-01 中国残联、教育部《关于加快在特殊教育学校推广国家通用手语和国家通用盲文的通知》
- 设计依据：手语语言学五要素（手形/位置/动作/朝向/非手控特征）、CEFR 扩展版手语能力标准、杜威"从做中学"
- 目标用户（设计文档 v3）：听障+健听，12 岁及以上青少年/成人；场景：辅助课堂教学/日常自学/聋人文化宣传
- 后续规划：XR/AR、游戏任务、学习记录、社交互动、多国手语

## 踩坑记录
- 无（任务进行中）

## 待办/待确认
- 生成 md → VL 排版检查 → 生成 docx → 完成汇报

## 交付规范（2026-08-12 用户要求，务必遵守）
- **交付文件必须带版本号**：命名形如 `hand_sign_planet_project_intro_v3_zh.md`（版本号 vN 放文件名中），docx/pdf 同规则；历史版本保留不删（v1/v2/v3 并存便于对比）
- 每次交付都要明确当前版本号（v1→v2→v3…），汇报时列出版本对照

## daemon 重启规范 v2（2026-08-29 系统通知，务必遵守；替代 08-27 v3 规则）
- 4194 daemon 任何重启（故障恢复/维护/配置生效）**必须调用外部触发入口**：`bash /data/WYC/signLanguage/work/scripts/restart_daemon_4194_trigger.sh`（--force 强制重启；不加则仅在 4194 已挂时补启，健康时不打扰）
- **禁止直接前台执行 v3 脚本**：v3 进程跑在成员终端里，SSH/tmux 断开时会在「kill 旧 daemon」之后、「启动新 daemon」之前被杀 → 4194 挂死（8-28 23:09、8-29 02:11 两次事故根因）。wrapper 用 setsid --fork 把 v3 脱离到独立会话，终端断开也能完整跑完 kill→启动→恢复模型→发继续完成
- 脚本自动完成：捕捉各会话工作状态（含 sub/后台任务）→ 重启 → 恢复模型+approval 等级（yolo 不回落）→ 向被打断的工作会话发送「继续完成」
- 若收到「【系统通知】daemon 重启，任务被中断…请继续完成」，应检查 sub/后台任务并继续未完成工作
- 查看广播执行结果：`tail -50 /data/WYC/signLanguage/work/logs/daemon_restart_4194.log`
- 详见 agent-team skill §8、通用 skill daemon-restart-continuity、.team/team_constraints.md §13

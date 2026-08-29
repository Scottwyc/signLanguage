# signL4-overlay 工作记忆（主管可读）

> 语义动画 signL4 跨 CLI 工作记忆。最后更新：2026-08-30 03:35
> 共享事实以 /data/WYC/signLanguage/.team/ 下公共文件为准（team_constraints.md / team_confirmations.log / 队列 / 进度文件）
> 本文件路径：/data/WYC/signLanguage/.team/member_memories/member_memories_signL4-overlay.md（2026-08-12 统一收纳至 member_memories/ 文件夹）

## 角色
- 语义动画（signL4），与 signL2 平级，直接向主管 SignL3 汇报
- 任务：基于人工通过的 wan 原视频制作"语义贴图标注动画"（overlay 视频）→ VL/本地模型审查 → 人工审核 → 部署

## ⚠️ 关键：视觉审查已从 8000 VL 切换为本地模型（2026-08-30）
- **8000 VL 已停用**；改用本地模型视觉统一入口 `127.0.0.1:11435`（综合代理，禁止绕过直连 zhuhai）
- 审查后端：`--model qwen3.8-27b-int4-tp2-g78`（g78 槽位；MTP 测试期间勿用 g34/g56）
- **渲染/审查必须 `PYTHONNOUSERSITE=1` 运行**：~/.local protobuf 7.36.0 遮蔽 myenv 的 4.25.8，导致 mediapipe 崩溃 `AttributeError: 'MessageFactory' object has no attribute 'GetPrototype'`

## ✅ 词16 森林 + 词14 汽车二 本地模型视觉审查通过（2026-08-30）
- 审计脚本：`audit_semantic_overlay_strict_v6_2.py`（v6.2 修正标准对齐批准设计，保留 v6.1）
- **词16 森林 v10**（保留 v10 原版）：全局 score=100，局部 14/14 全 100 → all_pass=true
  - 产出：`semantic_overlay_avatar_word_16_vl_pass_pending_review_v10_h264.mp4`
- **词14 汽车二 v12**（v11 全宽穿行是错误过度修正，已弃用）：全局 score=85，局部 10/10 全 100 → all_pass=true
  - 渲染脚本：`render_semantic_scene_overlay_v12.py`；car_x = w*(0.11+0.18*d)，起点0.11w不裁切/终点0.29w不遮人物，位移127px
  - 产出：`semantic_overlay_avatar_word_14_vl_pass_pending_review_v12_h264.mp4`（+.mp4 原版）
- 状态：`deployed=false`、`manual_review_required=true`，**待用户人工确认后通知主管上线**

## 核心流程（v2，signL2/signL3 多次修正后）
1. 渲染（H.264 双输出 mp4v+_h264.mp4）→ VL 审查（audit_semantic_overlay_v1.py）→ 循环优化
2. VL 通过 → 标 `_vl_pass_pending_review_`（不部署、不更新 manifest）→ pending 清单
3. SignL3 通知用户人工审核通过 → 执行部署（--deploy-words）→ 通知 SignL3 走公开仓库 PR

## 关键文件
- 渲染脚本：/data/WYC/signLanguage/work/scripts/render_semantic_scene_overlay_v4.py（场景化，当前版本）
- 循环脚本：/data/WYC/signLanguage/work/scripts/run_semantic_overlay_loop_v2.py（--deploy-words 部署）
- VL 审查：/data/WYC/signLanguage/work/scripts/audit_semantic_overlay_v1.py
- 产出目录：/data/WYC/signLanguage/work/generated/wan_animate_private_20260806/all21_front_avatar_production_pool_v7_2d5_smile/semantic_overlay_v1_20260810/
- pending 清单：.../semantic_overlay_pending_review_20260810.json
- 进度文件：/data/WYC/signLanguage/.team/progress/signL4-overlay.txt（主管可抓取，2026-08-12 §4 义务后同步路径；CLI 私有镜像：/home/wuyangcheng/.qwen/progress/semantic_overlay.txt）
- 前端部署：/data/WYC/sign-language-universe/apps/web/assets/content/reference-videos/ + reference_media_manifest.json

## 场景设计约定（用户 2026-08-10 反馈）
- 语义卡片：小、放右上角（中英文双语：词名+语义短语）
- 场景化元素 + MediaPipe 手部检测语义驱动动画（动作区渐入渐出 ±0.14/0.10）
- 半透明叠加 ≤0.72，不遮挡脸/手，空白区布局
- 各词：词5 三角把手前后摆动(深度缩放) / 词13 中轴方向盘 / 词16 三树生长 / 词14 左侧小车随手趋势 / 词15 人字形火柴人弧线+指尖椭圆 / 词17 手旁火柴人收腿弹跳

## 协作新规确认（2026-08-12）
- 先查职责边界并找对应负责人；适合子任务可协商转派
- 密钥/权限/外部资源/生产部署/公开仓库由对应负责人执行或明确授权
- 无法解决立即升级 SignL3，附已尝试方法、脱敏错误和所需决策
- 已写入共享 team_confirmations.log 与 progress/signL4-overlay.txt

## 进度快照（2026-08-12）
- ✅ 词5 公交车（PR #81）、词13 汽车一（PR #83）已上线
- 🔄 剩余4词 v5 已完成渲染+VL通过，pending 未部署、待用户复核：词16森林/词14汽车二/词15人们/词17跳
- v5脚本：/data/WYC/signLanguage/work/scripts/render_semantic_scene_overlay_v5.py；共享进度：/data/WYC/signLanguage/.team/progress/signL4-overlay.txt
- 词15的VL `icon_visible=false` 是单一icon字段口径，实际人群/火柴人场景已生成且无遮挡；需用户复核语义清晰度

## 协作约定
- 通知/确认走 /data/WYC/signLanguage/.team/team_confirmations.log（【成员确认】格式）
- 用户直接输入（无【】标志）→ 写时间戳到 /data/WYC/signLanguage/.team/user_last_interaction/signL4-overlay.txt
- 人工介入请求格式：【人工介入请求】窗口: <会话> | 任务: <描述> | 路径: <可选>（tmux 发 SignL3-304）
- 人工介入完成格式：【人工介入完成】窗口: <会话> | 任务: <描述>（monitor 自动移出队列）
- overlay 审核细节仅 signL4+主管+用户三方流转，signL2 不参与（§9）

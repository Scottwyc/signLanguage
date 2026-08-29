# 成员工作记忆：signL2-294（视频）

> 跨 CLI 共享记忆文件（主管可读）。任务阶段切换/完成/重要结论时更新。
> 路径：/data/WYC/signLanguage/.team/member_memories/member_memories_signL2-294.md
> 最后更新：2026-08-12 14:20

## 当前任务状态（2026-08-12）

### 主线：wan 手形瓶颈突破（方案 A/B）
- **方案 B（采样参数）**：steps 50/guide 1.8 已生效（调度器重启），词1/词6 生产采样已用新参数
- **方案一（骨架手部替换）**：DWPose 重跑 + 重建骨架完成 → handfixed 测试中

### handfixed 测试进度（7 词 4/18/19/1/6/20/21）
- ✅ 已生成：**词4 船**（1187KB）、**词1 馋**（942KB）
- ⚠️ 后端 5 次崩溃丢失 → **补跑中**（18/19/6/20/21，崩溃自动重试脚本）
- 后端单槽 + CUDA 崩溃周期（每 ~20-40 分钟）是主要风险

### 词2 唱歌（用户反馈重做）
- 用户反馈：脸部动作不符唱歌语义（关键=**头部晃动**）
- 已标记 queued / user_reject_round_9b_headsway，OPT-ROUND-9+9b 已强化（头部晃动最高优先级）
- 排队在 handfixed 测试后重做

## 关键结论

- **生产骨架手部缺失根因** = preprocess 渲染环节（非 DWPose 检测失败）；驱动视频直接跑 DWPose 手部 100% 检出
- **DWPose 重跑**：词4 船头指尖距 0.022-0.037（精确相抵）
- **重建骨架**：word_*_src_pose_rebuilt.mp4（含精确手部）
- **词2 唱歌是面部语义词**：嘴部开合+头部晃动参与主评分（与默认固定微笑策略不同）

## 待办/待确认

- [ ] handfixed 补跑 5 词完成 → VL+打分对比（重建 vs 生产骨架）
- [ ] 通过后替换生产 src_pose.mp4（主管确认）
- [ ] 词2 唱歌重做（测试后）→ 新版用户复核
- [ ] 词8 鸡蛋第11轮用户复核、词12 朋友 finetune 确认

## 踩坑记录

- 后端 cancel 接口不存在（404）；后端单槽测试需暂停生产调度器
- 后端崩溃频率高（50 steps 长采样更易触发）；补跑脚本需输出文件轮询 + 崩溃重试
- zhuhai 无 ffmpeg（cv2 替代）；Pose2d 返回 dict 非 AAPoseMeta

## 协作约定

- 进展 → progress/signL2-294.txt + 本文件 + team_confirmations.log（§4 义务）
- 报告 → /data/WYC/signLanguage/work/reports/

# 小红书分享：MTP 投机解码「POC 加速 vs 真实拖慢 52%」

> 保存时间：2026-08-30 19:35（北京时间）
> 维护者：运维（signL8）
> 数据来源：`/data/WYC/signLanguage/work/reports/mtp_ab_comparison_experiment_report_20260830.md`（权威报告，已定稿）

## 1. 文件夹说明

本文件夹是把 MTP（Multi-Token Prediction）投机解码 A/B 实验的发现，做成可直接发布到
小红书（REDNOTE）的图文笔记素材包。核心叙事：

- **POC（短上下文 + 低熵）加速 1.3-2×**
- **真实长任务（长上下文 + 高熵）反而拖慢 52%**
- 机制：加速比 ≈ (1+k)/(1+β)，k 由输出熵决定、β 由上下文长度决定
- 结论：全池回退无 MTP（去掉 `--speculative-config`）

## 2. 文件清单

| 文件 | 说明 |
|------|------|
| `正文.md` | 小红书笔记正文（口语化 + emoji + 短段落，约 780 字，结尾带话题标签） |
| `card1_cover.png` | 卡片 1 封面：MTP 加速翻车实录（POC 快 2 倍 vs 真实慢 52%） |
| `card2_phenomenon.png` | 卡片 2 现象：POC 加速 vs 真实拖慢（45.1 vs 21.8 tok/s） |
| `card3_mechanism.png` | 卡片 3 机制：三步流程 + 公式 (1+k)/(1+β) |
| `card4_factors.png` | 卡片 4 两因素叠加：POC vs 真实任务四维度对照 |
| `card5_conclusion.png` | 卡片 5 结论：全池回退无 MTP + 经验教训 |
| `card6_fig6.png` | 卡片 6 数据：fig6 真实活跃 decode 分布 + 点评 |
| `fig6_active_decode_dist.png` | fig6 原始数据图（A/B 真实活跃 decode 密度对比，已嵌入卡片 6） |
| `scripts/render_cards.py` | 卡片渲染脚本（PIL/Pillow 9.0.1，带中文注释与 docstring，可复用） |
| `开源库调研.md` | 渲染库调研记录（调研了哪些库、最终用哪个、为什么） |
| `README.md` | 本文件 |

所有卡片分辨率 **1242x1656（3:4 竖版）**，满足小红书 ≥1080x1440 要求。

## 3. 如何发布到小红书

### 3.1 准备

1. 打开小红书 App（或网页版 creator.xiaohongshu.com）→「发布笔记」→「图文」。
2. 卡片按 **card1 → card6 顺序** 上传（封面用 card1，小红书会取第一张做封面）。
   - 上传顺序：`card1_cover.png` → `card2_phenomenon.png` → `card3_mechanism.png`
     → `card4_factors.png` → `card5_conclusion.png` → `card6_fig6.png`
3. 6 张图均为 1242x1656，无需裁剪，直接上传即可。

### 3.2 填写标题与正文

1. **标题**（≤20 字，建议）：`MTP 加速翻车实录：POC 快 2 倍，真实慢 52%`
2. **正文**：把 `正文.md` 的全文复制粘贴到正文框（含 emoji 与话题标签）。
   - 若 App 对字数/格式有微调，保留「POC 加速 / 真实拖慢 / 公式 / 结论」四段主线即可。
   - 结尾话题标签 `#大模型 #MTP #投机解码 #vLLM #AI性能 #LLM推理 #技术干货 #工程实践` 务必带上，利于流量。
3. **封面**：默认取 card1；如需自定义封面，可单独上传 card1 并加封面标题。

### 3.3 发布前检查清单

- [ ] 6 张卡片按 card1→card6 顺序上传，无错序
- [ ] 标题 ≤20 字，含「MTP / 加速 / 翻车 / 52%」关键词
- [ ] 正文含四段主线 + 8 个话题标签
- [ ] 数据口径统一为 **MTP n=1**（本次 A/B 实测，非 n=2）
- [ ] 关键数字核对：POC 1.3-2.05×、真实 45.1 vs 21.8（慢 52%）、公式 (1+k)/(1+β)

## 4. 重新渲染卡片（可选）

如需改数据/配色/文案后重新出图：

```bash
cd /data/WYC/signLanguage/work/reports/xiaohongshu_share_mtp_20260830
python3 scripts/render_cards.py        # 重新渲染全部 6 张
python3 scripts/render_cards.py 1 3    # 只渲染指定编号
```

- 字体：Noto Sans CJK SC（ttc index=2）；彩色 emoji 不可用（NotoColorEmoji 为 CBDT 位图字体，PIL 9.0.1 无法加载），已用 CJK 等宽符号 + 自绘形状替代。
- fig6 源图：`/data/WYC/signLanguage/work/reports/figs_mtp_ab_20260830/fig6_active_decode_dist.png`（已复制到本文件夹）。

## 5. 数据口径说明（重要）

- 本次 A/B 实测 B 侧 MTP 配置为 **n=1**（`num_speculative_tokens:1`），非 n=2。
- 「POC n=2 推理型 2.05×」为 08-29 冒烟测试（确为 n=2）的历史引用，与本次 A/B（n=1）区分。
- 所有真实拖慢数据基于「真实活跃 decode」（任务时间窗切片 + decode>2 tok/s 过滤），剔除空闲 stale 期污染。

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书（REDNOTE）MTP 投机解码实验分享卡片渲染脚本
====================================================

把 MTP A/B 对照实验（POC 加速 vs 真实拖慢 52%）的发现渲染成 6 张
3:4 竖版小红书风格文字卡片（1242x1656）。

渲染库：PIL/Pillow 9.0.1 直接绘制（本机无 playwright/chromium，
NotoColorEmoji 为 CBDT 位图字体 PIL 9.0.1 无法加载，故用 Noto CJK
SC 的等宽符号 + PIL 自绘形状替代彩色 emoji）。

字体：
  - 标题/强调：Noto Sans CJK SC Bold（ttc index 2）
  - 正文：Noto Sans CJK SC Regular（ttc index 2）
  - 符号：同一 CJK 字体内置的 ★▲●→≈×✓⚠❗❓◆▶ 等

输出：6 张 PNG 到本脚本所在目录的上一级（输出文件夹根目录）。
  card1_cover.png      封面
  card2_phenomenon.png 现象对比
  card3_mechanism.png  核心机制（公式）
  card4_factors.png    两因素叠加
  card5_conclusion.png 结论建议
  card6_fig6.png       fig6 真实活跃 decode 分布 + 点评

用法：
  python3 render_cards.py            # 渲染全部 6 张
  python3 render_cards.py 1 3 5      # 只渲染指定编号的卡片
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

# ============================================================
# 常量配置
# ============================================================

# 卡片尺寸（3:4 竖版，小红书推荐 1242x1656）
W, H = 1242, 1656

# 输出目录：脚本所在目录的上一级（即输出文件夹根目录）
OUT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 字体路径
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_REG = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_INDEX = 2  # ttc 中 SC（简体中文）子字体索引

# fig6 数据图路径（真实活跃 decode 分布 A/B 密度对比）
FIG6_PATH = "/data/WYC/signLanguage/work/reports/figs_mtp_ab_20260830/fig6_active_decode_dist.png"

# 配色（小红书亮色风格：暖奶油底 + 珊瑚红/橙/紫强调）
BG_TOP = (255, 247, 242)      # 顶部暖奶油
BG_BOTTOM = (255, 233, 224)   # 底部浅蜜桃
PANEL = (255, 255, 255)       # 白色内容面板
DARK = (45, 42, 50)           # 深色主文字
GRAY = (107, 101, 112)        # 次要灰文字
LIGHT_GRAY = (235, 230, 238)  # 浅灰分隔
CORAL = (255, 90, 78)         # 珊瑚红（强调/负面）
ORANGE = (255, 159, 67)       # 橙
PURPLE = (108, 92, 231)       # 紫
GREEN = (46, 204, 113)        # 绿（正面/A 侧）
RED = (255, 71, 87)           # 红（负面/B 侧）
BLUE = (52, 152, 219)         # 蓝
CREAM = (255, 245, 235)       # 浅米色块
MINT = (232, 250, 240)        # 浅绿块
ROSE = (255, 236, 234)        # 浅红块
LAVENDER = (238, 234, 252)    # 浅紫块
AMBER = (255, 243, 224)       # 浅橙块


# ============================================================
# 字体缓存
# ============================================================
_font_cache = {}


def get_font(size, bold=True):
    """按大小+粗细取字体（带缓存，避免重复加载 ttc）。"""
    key = (size, bold)
    if key not in _font_cache:
        path = FONT_BOLD if bold else FONT_REG
        _font_cache[key] = ImageFont.truetype(path, size, index=FONT_INDEX)
    return _font_cache[key]


# ============================================================
# 绘图辅助函数
# ============================================================

def make_bg():
    """生成竖向渐变背景图（暖奶油 → 浅蜜桃）。"""
    img = Image.new("RGB", (W, H), BG_TOP)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * t)
        g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * t)
        b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * t)
        d.line([(0, y), (W, y)], fill=(r, g, b))
    return img


def rrect(d, box, radius, fill=None, outline=None, width=1):
    """画圆角矩形（PIL 9.0.1 用 rounded_rectangle）。"""
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def text_w(d, text, font):
    """测量文本宽度。"""
    return d.textlength(text, font=font)


def text_h(font):
    """估算单行文本高度（用 font size 的 1.2 倍行高）。"""
    return int(font.size * 1.25)


def wrap_text(d, text, font, max_width):
    """按像素宽度换行（CJK 可任意断行，逐字符累加）。

    返回行列表。
    """
    lines = []
    cur = ""
    for ch in text:
        if ch == "\n":
            lines.append(cur)
            cur = ""
            continue
        if text_w(d, cur + ch, font) <= max_width:
            cur += ch
        else:
            if cur:
                lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(d, x, y, text, font, max_width, fill, line_gap=1.3):
    """在 (x,y) 处左对齐绘制自动换行文本，返回结束后的 y 坐标。"""
    lines = wrap_text(d, text, font, max_width)
    lh = int(font.size * line_gap)
    for line in lines:
        d.text((x, y), line, font=font, fill=fill)
        y += lh
    return y


def draw_centered(d, cx, y, text, font, fill):
    """在水平中心 cx 处绘制单行文本，返回行高。"""
    w = text_w(d, text, font)
    d.text((cx - w / 2, y), text, font=font, fill=fill)
    return int(font.size * 1.25)


def pill(d, cx, cy, text, font, fill, text_fill=(255, 255, 255), pad_x=28, pad_y=14):
    """绘制胶囊形徽章（居中于 cx,cy），返回其包围盒。"""
    tw = text_w(d, text, font)
    th = font.size
    x0 = cx - tw / 2 - pad_x
    x1 = cx + tw / 2 + pad_x
    y0 = cy - th / 2 - pad_y
    y1 = cy + th / 2 + pad_y
    rrect(d, (x0, y0, x1, y1), radius=int((y1 - y0) / 2), fill=fill)
    d.text((cx - tw / 2, y0 + pad_y - 2), text, font=font, fill=text_fill)
    return (x0, y0, x1, y1)


def header(d, title, subtitle=None, accent=CORAL, top=70):
    """绘制卡片页眉：左侧色条 + 大标题 + 可选副标题。返回内容区起始 y。"""
    # 左侧竖色条
    rrect(d, (80, top, 96, top + 96), radius=8, fill=accent)
    # 标题
    d.text((120, top - 6), title, font=get_font(72, True), fill=DARK)
    y = top + 100
    if subtitle:
        y = draw_wrapped(d, 120, y, subtitle, get_font(40, False), W - 240, GRAY, line_gap=1.3)
    return y + 20


def footer(d, text="MTP A/B 实验"):
    """绘制页脚小字。"""
    f = get_font(30, False)
    w = text_w(d, text, f)
    d.text(((W - w) / 2, H - 70), text, font=f, fill=GRAY)


def arrow_down(d, cx, y0, y1, color=GRAY, width=10):
    """画向下箭头（线 + 三角头）。"""
    d.line([(cx, y0), (cx, y1 - 16)], fill=color, width=width)
    d.polygon([(cx - 22, y1 - 18), (cx + 22, y1 - 18), (cx, y1)], fill=color)


def arrow_right(d, x0, x1, cy, color=GRAY, width=10):
    """画向右箭头。"""
    d.line([(x0, cy), (x1 - 16, cy)], fill=color, width=width)
    d.polygon([(x1 - 18, cy - 22), (x1 - 18, cy + 22), (x1, cy)], fill=color)


def stat_box(d, x, y, w, h, label, value, vcolor, bg, lcolor=GRAY, vsize=64, lsize=36):
    """绘制统计小方块：标签 + 大数字。"""
    rrect(d, (x, y, x + w, y + h), radius=20, fill=bg)
    d.text((x + 24, y + 22), label, font=get_font(lsize, False), fill=lcolor)
    d.text((x + 24, y + 22 + lsize + 10), value, font=get_font(vsize, True), fill=vcolor)


# ============================================================
# 卡片 1：封面
# ============================================================

def card1_cover():
    img = make_bg()
    d = ImageDraw.Draw(img)

    # 顶部小徽章
    pill(d, W / 2, 170, "大模型推理优化 · 踩坑实录", get_font(40, True), PURPLE)

    # 主标题（两行大字）
    d.text((W / 2 - text_w(d, "MTP 加速", get_font(150, True)) / 2, 300),
           "MTP 加速", font=get_font(150, True), fill=DARK)
    d.text((W / 2 - text_w(d, "翻车实录", get_font(150, True)) / 2, 470),
           "翻车实录", font=get_font(150, True), fill=CORAL)

    # 副标题
    draw_centered(d, W / 2, 660, "POC 快 2 倍，真实任务慢 52%", get_font(52, True), DARK)

    # 两个大统计胶囊：POC 加速 vs 真实拖慢
    # 左：POC（右边界 561，为中间 VS 留 120px 空隙）
    rrect(d, (110, 820, 561, 1010), radius=28, fill=MINT)
    draw_centered(d, 335, 850, "POC 短上下文", get_font(40, True), GREEN)
    draw_centered(d, 335, 915, "1.3 - 2.05×", get_font(64, True), GREEN)
    # 右：真实（左边界 681，与左框对称）
    rrect(d, (681, 820, 1132, 1010), radius=28, fill=ROSE)
    draw_centered(d, 906, 850, "真实长任务", get_font(40, True), RED)
    draw_centered(d, 906, 915, "慢 52%", get_font(64, True), RED)

    # 中间对比符号
    draw_centered(d, W / 2, 890, "VS", get_font(56, True), ORANGE)

    # 底部说明
    draw_centered(d, W / 2, 1090, "同一个模型 · 同一个任务 · 唯一区别是开没开 MTP",
                  get_font(40, False), GRAY)

    # 底部信息条
    rrect(d, (110, 1200, 1132, 1330), radius=24, fill=PANEL)
    draw_centered(d, W / 2, 1225, "vLLM · Qwen3.8-27B INT4 · TP2 · MTP n=1",
                  get_font(42, True), DARK)
    draw_centered(d, W / 2, 1278, "A 侧无 MTP 45.1 tok/s  vs  B 侧有 MTP 21.8 tok/s",
                  get_font(36, False), GRAY)

    footer(d)
    img.save(os.path.join(OUT_DIR, "card1_cover.png"))
    print("card1_cover.png 完成")


# ============================================================
# 卡片 2：现象对比
# ============================================================

def card2_phenomenon():
    img = make_bg()
    d = ImageDraw.Draw(img)
    y = header(d, "先看现象", "POC 说加速，真实任务说拖慢，到底谁对？", accent=GREEN)

    # POC 区块（绿）
    rrect(d, (80, y, 1162, y + 360), radius=24, fill=MINT)
    d.text((120, y + 30), "✓ POC 冒烟测试（08-29）", font=get_font(46, True), fill=GREEN)
    lines = [
        "短上下文 128-256 token + 低熵英文重复",
        "decode 加速 1.3 - 2.05×",
        "低熵英文接受率高达 91.2%",
    ]
    ly = y + 110
    for ln in lines:
        d.text((140, ly), "· " + ln, font=get_font(40, False), fill=DARK)
        ly += 68

    # 向下箭头
    arrow_down(d, W / 2, y + 375, y + 435, color=ORANGE)

    # 真实 A/B 区块（红）
    y2 = y + 450
    rrect(d, (80, y2, 1162, y2 + 470), radius=24, fill=ROSE)
    d.text((120, y2 + 30), "× 真实 A/B 对照（08-30）", font=get_font(46, True), fill=RED)
    lines2 = [
        "前端动画绘制任务，上下文一路涨到 131K",
        "真实活跃 decode 中位数：",
    ]
    ly = y2 + 110
    for ln in lines2:
        d.text((140, ly), "· " + ln, font=get_font(40, False), fill=DARK)
        ly += 64

    # 两个统计小方块：A vs B（中间留 122px 空隙给 VS，避免重叠）
    stat_box(d, 140, ly, 420, 150, "A 侧（无 MTP）", "45.1 tok/s", GREEN, PANEL, vsize=56, lsize=34)
    stat_box(d, 682, ly, 420, 150, "B 侧（MTP n=1）", "21.8 tok/s", RED, PANEL, vsize=56, lsize=34)
    draw_centered(d, W / 2, ly + 40, "VS", get_font(48, True), ORANGE)

    # 底部结论条
    y3 = y2 + 490
    rrect(d, (80, y3, 1162, y3 + 120), radius=20, fill=LAVENDER)
    draw_centered(d, W / 2, y3 + 22, "B 侧比 A 侧慢约 52%（中位数比 0.483）",
                  get_font(44, True), PURPLE)
    draw_centered(d, W / 2, y3 + 72, "重叠窗口同时刻对比：42.3 vs 19.8，比值 0.468",
                  get_font(34, False), GRAY)

    footer(d)
    img.save(os.path.join(OUT_DIR, "card2_phenomenon.png"))
    print("card2_phenomenon.png 完成")


# ============================================================
# 卡片 3：核心机制
# ============================================================

def card3_mechanism():
    img = make_bg()
    d = ImageDraw.Draw(img)
    y = header(d, "为什么？看机制", "MTP 投机解码每一步在做什么", accent=PURPLE)

    # 三步流程（三个圆角框 + 向下箭头）
    steps = [
        ("①", "小头 draft n 个 token", "便宜的小模型先猜 n 个", PURPLE, LAVENDER),
        ("②", "主模型一次 forward 验证", "要对【完整上下文】做 attention", ORANGE, AMBER),
        ("③", "接受其中 k 个", "本步产出 (1+k) 个 token", GREEN, MINT),
    ]
    sy = y + 10
    box_h = 150
    for i, (num, title, desc, ac, bg) in enumerate(steps):
        rrect(d, (120, sy, 1122, sy + box_h), radius=22, fill=bg)
        # 序号圆
        d.ellipse((150, sy + 35, 230, sy + 115), fill=ac)
        draw_centered(d, 190, sy + 48, num, get_font(48, True), (255, 255, 255))
        d.text((260, sy + 30), title, font=get_font(46, True), fill=DARK)
        d.text((260, sy + 92), desc, font=get_font(36, False), fill=GRAY)
        if i < 2:
            arrow_down(d, W / 2, sy + box_h + 6, sy + box_h + 56, color=ac)
        sy += box_h + 60

    # 公式大框
    fy = sy + 20
    rrect(d, (80, fy, 1162, fy + 240), radius=26, fill=DARK)
    draw_centered(d, W / 2, fy + 30, "加速比 ≈ (1 + k) / (1 + β)", get_font(72, True), (255, 255, 255))
    draw_centered(d, W / 2, fy + 130, "k = 平均接受的 draft 数（输出熵决定）", get_font(40, False), (220, 216, 230))
    draw_centered(d, W / 2, fy + 180, "β = 验证 forward 额外开销（上下文长度决定）", get_font(40, False), (220, 216, 230))

    # 底部一句话
    by = fy + 270
    rrect(d, (80, by, 1162, by + 130), radius=20, fill=CREAM)
    draw_centered(d, W / 2, by + 24, "k 越大、β 越小 → 加速越多；反之拖慢",
                  get_font(44, True), ORANGE)

    footer(d)
    img.save(os.path.join(OUT_DIR, "card3_mechanism.png"))
    print("card3_mechanism.png 完成")


# ============================================================
# 卡片 4：两因素叠加
# ============================================================

def card4_factors():
    img = make_bg()
    d = ImageDraw.Draw(img)
    y = header(d, "两因素叠加", "POC 和真实任务差在哪？", accent=ORANGE)

    # POC 行（绿）
    rrect(d, (80, y, 1162, y + 420), radius=24, fill=MINT)
    d.text((120, y + 28), "POC（08-29）→ 加速", font=get_font(48, True), fill=GREEN)
    rows = [
        ("上下文短 128-256", "β≈0，验证几乎免费"),
        ("输出低熵（英文重复 91.2%）", "接受率 k 高"),
        ("单轮 256 token burst", "连续 decode 命中稳定"),
    ]
    ry = y + 105
    for a, b in rows:
        d.text((140, ry), "· " + a, font=get_font(40, True), fill=DARK)
        d.text((140, ry + 52), "   → " + b, font=get_font(36, False), fill=GRAY)
        ry += 100

    # 向下箭头
    arrow_down(d, W / 2, y + 435, y + 495, color=ORANGE)

    # 真实长任务行（红）
    y2 = y + 510
    rrect(d, (80, y2, 1162, y2 + 420), radius=24, fill=ROSE)
    d.text((120, y2 + 28), "真实长任务（08-30）→ 拖慢", font=get_font(48, True), fill=RED)
    rows2 = [
        ("上下文长 100K+", "β 大，验证昂贵（每个 draft 位置都对 100K 做 attention）"),
        ("持续高熵（代码+思考+多样内容）", "接受率 k 低"),
        ("多轮迭代 + 连续批处理", "验证开销进一步放大"),
    ]
    ry = y2 + 105
    for a, b in rows2:
        d.text((140, ry), "· " + a, font=get_font(40, True), fill=DARK)
        d.text((140, ry + 52), "   → " + b, font=get_font(36, False), fill=GRAY)
        ry += 100

    # 底部一句话
    y3 = y2 + 440
    rrect(d, (80, y3, 1162, y3 + 260), radius=22, fill=LAVENDER)
    draw_wrapped(d, 120, y3 + 26,
                 "一句话：验证成本随上下文长度增长，接受率随输出熵升高而下降。"
                 "POC 是「短上下文+低熵」（验证便宜+命中高）→ 加速；"
                 "真实长任务是「长上下文+高熵」（验证昂贵+命中低）→ 两个不利因素叠加 → 拖慢。",
                 get_font(38, True), W - 240, PURPLE, line_gap=1.4)

    footer(d)
    img.save(os.path.join(OUT_DIR, "card4_factors.png"))
    print("card4_factors.png 完成")


# ============================================================
# 卡片 5：结论建议
# ============================================================

def card5_conclusion():
    img = make_bg()
    d = ImageDraw.Draw(img)
    y = header(d, "结论：全池回退无 MTP", "三个维度的实测判定", accent=RED)

    findings = [
        ("❌", "Decode 加速", "真实高熵任务上未加速，反而慢 52%", RED, ROSE),
        ("✓", "Prefill 保持", "基本保持（中位数比 1.003，几乎一致）", GREEN, MINT),
        ("❌", "任务完成度", "B 侧崩溃 + 结尾死循环，判失败", RED, ROSE),
    ]
    fy = y + 10
    for icon, title, desc, ac, bg in findings:
        rrect(d, (80, fy, 1162, fy + 150), radius=22, fill=bg)
        d.ellipse((110, fy + 35, 190, fy + 115), fill=ac)
        draw_centered(d, 150, fy + 46, icon, get_font(48, True), (255, 255, 255))
        d.text((220, fy + 28), title, font=get_font(46, True), fill=DARK)
        d.text((220, fy + 88), desc, font=get_font(36, False), fill=GRAY)
        fy += 170

    # 建议大框
    sy = fy + 20
    rrect(d, (80, sy, 1162, sy + 240), radius=26, fill=DARK)
    draw_centered(d, W / 2, sy + 30, "建议：全池回退无 MTP", get_font(60, True), (255, 210, 100))
    draw_centered(d, W / 2, sy + 120, "去掉 --speculative-config，", get_font(42, False), (230, 226, 240))
    draw_centered(d, W / 2, sy + 175, "回到标准 vLLM 推理", get_font(42, False), (230, 226, 240))

    # 经验教训
    ly = sy + 270
    rrect(d, (80, ly, 1162, ly + 230), radius=22, fill=AMBER)
    d.text((120, ly + 24), "⚠ 经验教训", font=get_font(46, True), fill=ORANGE)
    draw_wrapped(d, 120, ly + 86,
                 "POC 加速 ≠ 生产加速。短上下文低熵的冒烟测试结论，"
                 "不能外推到长上下文高熵的真实 agent 任务，必须真实任务 A/B 验证。",
                 get_font(36, True), W - 240, DARK, line_gap=1.4)

    footer(d)
    img.save(os.path.join(OUT_DIR, "card5_conclusion.png"))
    print("card5_conclusion.png 完成")


# ============================================================
# 卡片 6：fig6 数据卡
# ============================================================

def card6_fig6():
    img = make_bg()
    d = ImageDraw.Draw(img)
    y = header(d, "数据说话：活跃 decode 分布", "A/B 真实活跃 decode 瞬时速率密度对比", accent=BLUE)

    # 嵌入 fig6（等比缩放适配内容区宽度）
    content_w = W - 160  # 左右各 80 边距
    fig = Image.open(FIG6_PATH).convert("RGB")
    fw, fh = fig.size
    scale = content_w / fw
    new_w = content_w
    new_h = int(fh * scale)
    # 若过高则按高度限制
    max_h = 620
    if new_h > max_h:
        scale = max_h / fh
        new_h = max_h
        new_w = int(fw * scale)
    fig = fig.resize((new_w, new_h), Image.LANCZOS)
    fx = (W - new_w) // 2
    fy = y + 10
    # 白底衬 + 阴影感边框
    rrect(d, (fx - 10, fy - 10, fx + new_w + 10, fy + new_h + 10),
          radius=16, fill=PANEL, outline=LIGHT_GRAY, width=3)
    img.paste(fig, (fx, fy))

    # 下方点评
    cy = fy + new_h + 40
    rrect(d, (80, cy, 1162, cy + 150), radius=22, fill=MINT)
    d.text((120, cy + 26), "A 侧集中在 40-55 tok/s（窄峰）", font=get_font(42, True), fill=GREEN)
    d.text((120, cy + 84), "B 侧集中在 17-27 tok/s（整体下移约一半）", font=get_font(42, True), fill=RED)

    cy2 = cy + 170
    rrect(d, (80, cy2, 1162, cy2 + 150), radius=22, fill=LAVENDER)
    draw_wrapped(d, 120, cy2 + 26,
                 "「整体平移」而非「尾部截断」→ 说明 MTP n=1 在真实高熵任务是"
                 "持续性的速率拖累，而非偶发。",
                 get_font(38, True), W - 240, PURPLE, line_gap=1.4)

    cy3 = cy2 + 170
    rrect(d, (80, cy3, 1162, cy3 + 130), radius=20, fill=AMBER)
    draw_wrapped(d, 120, cy3 + 24,
                 "⚠ 全时段中位数有严重误导性：A 侧全时段仅 4.8 tok/s（被空闲 stale 拉低），"
                 "真实活跃中位数高达 45.1，相差近 10 倍。",
                 get_font(34, False), W - 240, DARK, line_gap=1.4)

    footer(d)
    img.save(os.path.join(OUT_DIR, "card6_fig6.png"))
    print("card6_fig6.png 完成")


# ============================================================
# 主入口
# ============================================================

CARDS = {
    1: card1_cover,
    2: card2_phenomenon,
    3: card3_mechanism,
    4: card4_factors,
    5: card5_conclusion,
    6: card6_fig6,
}


def main():
    # 解析命令行参数：可指定卡片编号，默认全部
    args = [a for a in sys.argv[1:] if a.isdigit()]
    if args:
        nums = [int(a) for a in args]
    else:
        nums = list(CARDS.keys())

    for n in nums:
        if n in CARDS:
            CARDS[n]()
        else:
            print(f"未知卡片编号 {n}，跳过")
    print(f"\n全部完成，输出目录：{OUT_DIR}")


if __name__ == "__main__":
    main()

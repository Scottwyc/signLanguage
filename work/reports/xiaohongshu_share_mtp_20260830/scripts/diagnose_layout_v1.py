#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
卡片版式诊断脚本（程序化测量，不依赖视觉）
====================================================

视觉桥接（read_file 图片）会产生幻觉转录，zoom_image 当前模型不支持，
故用 PIL 程序化测量：monkeypatch ImageDraw.Draw 的 text / rounded_rectangle，
逐张卡片记录每个文本元素的位置/宽度 与 每个色框的边界，然后检测：
  1. 文本右边缘超出包含它的色框右边界（横向溢出）
  2. 文本下边缘超出包含它的色框下边界（纵向溢出）
  3. 文本与色框内边距不足（贴近边缘）

用法：
  python3 diagnose_layout_v1.py            # 诊断全部 6 张
  python3 diagnose_layout_v1.py 1 3        # 只诊断指定编号
"""

import sys
import os

# 让 render_cards 可被导入
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import render_cards
from PIL import Image, ImageDraw

# ============================================================
# 日志存储
# ============================================================
text_log = []   # (card, x, y, text, font_size, width)
rect_log = []   # (card, x0, y0, x1, y1)
_current_card = [None]

# ImageDraw.Draw 是工厂函数，实际类是 ImageDraw.ImageDraw
_DrawCls = ImageDraw.ImageDraw
_orig_text = _DrawCls.text
_orig_rr = _DrawCls.rounded_rectangle


def patched_text(self, xy, text, font=None, fill=None, **kwargs):
    x, y = xy
    fs = font.size if font is not None else 0
    w = self.textlength(text, font=font) if font is not None else 0
    text_log.append((_current_card[0], x, y, text, fs, w))
    return _orig_text(self, xy, text, font=font, fill=fill, **kwargs)


def patched_rr(self, xy, radius, fill=None, outline=None, width=1):
    rect_log.append((_current_card[0], xy[0], xy[1], xy[2], xy[3]))
    return _orig_rr(self, xy, radius=radius, fill=fill, outline=outline, width=width)


_DrawCls.text = patched_text
_DrawCls.rounded_rectangle = patched_rr

# 诊断时不落盘（避免覆盖当前卡片）
_orig_save = Image.Image.save
Image.Image.save = lambda self, *a, **k: None


# ============================================================
# 溢出检测
# ============================================================
def analyze(card):
    """检测某张卡的文本溢出问题。对每个文本，找包含它左上角的「最小面积」色框
    （最具体的容器），检测横向/纵向溢出与贴边。"""
    texts = [t for t in text_log if t[0] == card]
    rects = [r for r in rect_log if r[0] == card]
    issues = []
    for (c, x, y, text, fs, w) in texts:
        right = x + w
        bottom = y + fs * 1.25
        # 找包含该文本左上角的所有色框，取面积最小（最具体）的
        containing = [(x0, y0, x1, y1) for (c2, x0, y0, x1, y1) in rects
                      if x0 <= x <= x1 and y0 <= y <= y1]
        if not containing:
            continue
        # 取面积最小的包含框
        bx = min(containing, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
        x0, y0, x1, y1 = bx
        # 横向溢出
        if right > x1 + 2:
            issues.append((right - x1, "右溢出", text, x, y, fs, w, (x0, y0, x1, y1)))
        # 纵向溢出
        if bottom > y1 + 2:
            issues.append((bottom - y1, "下溢出", text, x, y, fs, w, (x0, y0, x1, y1)))
        # 横向贴边（内边距 < 12px，仅对非溢出情况）
        elif (x1 - right) < 12:
            issues.append((-(12 - (x1 - right)), "右贴边", text, x, y, fs, w, (x0, y0, x1, y1)))
    return issues


def main():
    args = [a for a in sys.argv[1:] if a.isdigit()]
    nums = [int(a) for a in args] if args else list(render_cards.CARDS.keys())

    for n in nums:
        if n not in render_cards.CARDS:
            continue
        text_log.clear()
        rect_log.clear()
        _current_card[0] = n
        render_cards.CARDS[n]()
        issues = analyze(n)
        print(f"\n{'='*60}\n卡片 {n}：共 {len([t for t in text_log if t[0]==n])} 个文本 / "
              f"{len([r for r in rect_log if r[0]==n])} 个色框，发现 {len(issues)} 处问题")
        # 按严重程度排序（溢出在前，贴边在后）
        issues.sort(key=lambda i: i[0], reverse=True)
        for (sev, kind, text, x, y, fs, w, box) in issues:
            if sev > 0:
                print(f"  [{kind} {sev:.0f}px] \"{text[:30]}\" fs={fs} w={w:.0f} "
                      f"at({x:.0f},{y:.0f}) 框右={box[2]:.0f} 框下={box[3]:.0f}")
            else:
                print(f"  [{kind} 内边距{abs(sev):.0f}px] \"{text[:30]}\" fs={fs} "
                      f"at({x:.0f},{y:.0f}) 框右={box[2]:.0f}")


if __name__ == "__main__":
    main()

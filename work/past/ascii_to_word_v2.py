#!/usr/bin/env python3
"""
从 Markdown 中的 ASCII 框图生成图表并插入 Word 文档
支持嵌套框识别 + 中文字体显示
"""

import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.font_manager import FontProperties
import os
import subprocess

# 加载中文字体
SIMHEI_PATH = '/home/wuyangcheng/.fonts/SimHei.ttf'
chinese_font = FontProperties(fname=SIMHEI_PATH, size=9) if os.path.exists(SIMHEI_PATH) else None


def find_all_boxes(lines):
    """查找所有完整的矩形框（包括嵌套框）"""
    boxes = []
    height = len(lines)
    
    for r in range(height):
        line = lines[r]
        for c in range(len(line)):
            if line[c] == '┌':
                box = find_box(lines, r, c, height)
                if box and box['width'] >= 5 and box['height'] >= 2:
                    boxes.append(box)
    
    return boxes


def find_box(lines, top, left, max_height):
    """从左上角找完整的框"""
    line = lines[top]
    
    # 找右上角
    right = None
    for c in range(left + 1, min(len(line), left + 150)):
        if line[c] == '┐' and all(line[x] in '─┬┼┤' for x in range(left + 1, c)):
            right = c
            break
        elif line[c] not in '─┬┼├':
            break
    
    if right is None:
        return None
    
    # 找底边
    bottom = None
    for r in range(top + 1, min(max_height, top + 50)):
        if r >= len(lines):
            break
        check = lines[r]
        if left >= len(check) or right >= len(check):
            break
        
        lc, rc = check[left], check[right]
        # 检查是否是底边
        if lc == '└' and rc == '┘' and all(check[x] in '─┬┼' for x in range(left + 1, right)):
            bottom = r
            break
        # 允许空格作为侧边（嵌套框的情况）
        if lc not in '│┬┴┼├┤ ' or rc not in '│┬┴┤ ':
            break
    
    if bottom is None:
        return None
    
    # 提取文本
    text_lines = []
    for r in range(top + 1, bottom):
        if r < len(lines):
            t = lines[r][left + 1:right]
            if t.strip() and not all(c in '─═' for c in t.strip()):
                text_lines.append(t)
    
    return {
        'top': top, 'left': left, 'bottom': bottom, 'right': right,
        'width': right - left + 1, 'height': bottom - top + 1,
        'text_lines': text_lines
    }


def find_arrows(lines):
    """查找箭头"""
    arrows = []
    for r, line in enumerate(lines):
        for c, char in enumerate(line):
            if char == '▼':
                arrows.append({'row': r, 'col': c, 'dir': 'down'})
            elif char == '▲':
                arrows.append({'row': r, 'col': c, 'dir': 'up'})
            elif char == '►' or char == '→':
                arrows.append({'row': r, 'col': c, 'dir': 'right'})
    return arrows


def draw_diagram(boxes, arrows, output_path, title="System Architecture"):
    """绘制框图"""
    if not boxes:
        print("  No boxes found")
        return None
    
    # 计算边界
    min_row = min(b['top'] for b in boxes)
    max_row = max(b['bottom'] for b in boxes)
    min_col = min(b['left'] for b in boxes)
    max_col = max(b['right'] for b in boxes)
    
    range_row = max(max_row - min_row + 1, 1)
    range_col = max(max_col - min_col + 1, 1)
    
    fig, ax = plt.subplots(figsize=(14, 10), dpi=100)
    
    def to_x(col):
        return (col - min_col) / range_col * 90 + 5
    
    def to_y(row):
        return 95 - (row - min_row) / range_row * 90
    
    box_color = '#E3F2FD'
    edge_color = '#1976D2'
    
    # 绘制框（按面积排序，先画大的）
    for box in sorted(boxes, key=lambda b: b['width'] * b['height'], reverse=True):
        x1, x2 = to_x(box['left']), to_x(box['right'])
        y1, y2 = to_y(box['top']), to_y(box['bottom'])
        w, h = x2 - x1, y1 - y2
        
        # 大框用虚线（外层容器）
        if box['width'] > 60 and box['height'] > 20:
            rect = patches.Rectangle((x1, y2), w, h, linewidth=1, edgecolor='#90CAF9',
                                      facecolor='none', alpha=0.5, linestyle='--')
        else:
            rect = patches.Rectangle((x1, y2), w, h, linewidth=1.5, edgecolor=edge_color,
                                      facecolor=box_color, alpha=0.7)
        ax.add_patch(rect)
        
        # 添加文本
        if box['text_lines']:
            for i, txt in enumerate(box['text_lines'][:5]):
                ty = y1 - h * 0.15 - i * h / 6
                ax.text((x1 + x2) / 2, ty, txt.strip(), ha='center', va='top',
                        fontsize=8, fontproperties=chinese_font,
                        bbox=dict(boxstyle='round', facecolor='white', alpha=0.5))
    
    # 绘制箭头
    for arrow in arrows:
        x, y = to_x(arrow['col']), to_y(arrow['row'])
        if arrow['dir'] == 'down':
            ax.annotate('', xy=(x, y - 2), xytext=(x, y),
                       arrowprops=dict(arrowstyle='->', color=edge_color, lw=1.5))
        elif arrow['dir'] == 'right':
            ax.annotate('', xy=(x + 3, y), xytext=(x, y),
                       arrowprops=dict(arrowstyle='->', color=edge_color, lw=1.5))
    
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    ax.set_title(title, fontsize=14, pad=20)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=100, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"  ✓ Saved: {output_path} ({len(boxes)} boxes, {len(arrows)} arrows)")
    return output_path


def process_md_file(md_file):
    """处理 Markdown 文件，生成图表并插入 Word"""
    print(f"\nProcessing: {os.path.basename(md_file)}")
    
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找代码块
    blocks = re.findall(r'```\n?([\s\S]*?)```', content)
    
    # 找包含最多框图字符的块
    best_block, best_count = None, 0
    for block in blocks:
        count = sum(1 for c in block if c in '┌┐└│─├┤┬┼▼▲►→')
        if count > best_count:
            best_count, best_block = count, block
    
    if best_count < 10:
        print(f"  ✗ No diagram found ({best_count} chars)")
        return None
    
    print(f"  Found diagram: {best_count} chars")
    
    # 解析
    lines = best_block.split('\n')
    boxes = find_all_boxes(lines)
    arrows = find_arrows(lines)
    
    print(f"  Parsed: {len(boxes)} boxes, {len(arrows)} arrows")
    
    # 绘制
    img_path = md_file.replace('.md', '_chart.png')
    draw_diagram(boxes, arrows, img_path)
    
    # 更新 Markdown 添加图片引用
    img_rel = os.path.basename(img_path)
    img_md = f'\n\n![System Architecture]({img_rel})\n\n*图：系统架构图*\n\n'
    
    # 找插入位置
    markers = ['### 3.1 系统架构图', '### 技术架构', '### 3.1 手语动作评测系统架构', '## 三、推荐架构设计']
    insert_pos = None
    for m in markers:
        idx = content.find(m)
        if idx > 0:
            end_line = content.find('\n', idx)
            insert_pos = end_line + 1
            break
    
    if insert_pos:
        new_content = content[:insert_pos] + img_md + content[insert_pos:]
        out_md = md_file.replace('.md', '_with_chart.md')
        with open(out_md, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  ✓ Updated MD: {out_md}")
        
        # 转 Word
        out_docx = out_md.replace('.md', '.docx')
        result = subprocess.run(['pandoc', out_md, '-o', out_docx,
                       '--toc', '--toc-depth=2', '--number-sections', '-M', 'lang=en'],
                      capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✓ Generated DOCX: {out_docx}")
        else:
            print(f"  ✗ Pandoc error: {result.stderr}")
        return out_docx
    
    return None


if __name__ == '__main__':
    md_files = [
        '/home/wuyangcheng/signLanguage/work/手语动作准确度评测方案_20260402_简化版.md',
        '/home/wuyangcheng/signLanguage/work/手语识别技术路线推荐_20260402_简化版.md',
        '/home/wuyangcheng/signLanguage/work/手语识别技术路线推荐_v2_20260402_简化版.md',
    ]
    
    for md in md_files:
        if os.path.exists(md):
            process_md_file(md)

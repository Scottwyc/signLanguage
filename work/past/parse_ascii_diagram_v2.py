#!/usr/bin/env python3
"""
解析 Markdown 中的 ASCII 框图并转换为 matplotlib 图形
核心思路：
1. 识别完整的矩形框（通过四个角字符 ┌ ┐  ┘）
2. 验证边框（横线 ─ 和竖线 │）
3. 提取框内文本内容
"""

import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.font_manager import FontProperties
import os

# ASCII 框图字符
BOX_CORNER = {'┌', '', '└', ''}
BOX_H = {'─', '┬', '', '┼', '', '┤'}  # 水平线字符
BOX_V = {'│', '┬', '┴', '┼', '├', '┤'}  # 垂直线字符
BOX_LINE_H = {'─', '┬', '', '┼', '', '┤', '', '└'}  # 可用于水平边的字符
BOX_LINE_V = {'│', '┬', '┴', '┼', '├', '┤', '┌', '┐'}  # 可用于垂直边的字符
ARROW_DOWN = '▼'
ARROW_UP = '▲'


def find_complete_boxes(lines):
    """
    查找所有完整的矩形框
    返回：list of {'top': row, 'left': col, 'bottom': row, 'right': col, 'text': str}
    """
    boxes = []
    height = len(lines)
    
    # 找到所有左上角 ┌
    for r in range(height):
        line = lines[r]
        for c in range(len(line)):
            if line[c] == '┌':
                # 尝试找到对应的右下角
                box = find_box_from_topleft(lines, r, c, height)
                if box:
                    boxes.append(box)
    
    return boxes


def find_box_from_topleft(lines, top, left, max_height):
    """从左上角开始寻找完整的矩形框"""
    line = lines[top]
    
    # 向右找右上角 ┐
    right = None
    for c in range(left + 1, len(line)):
        if line[c] == '┐':
            # 检查中间是否都是水平线
            if all(line[x] in BOX_LINE_H for x in range(left + 1, c)):
                right = c
                break
        elif line[c] not in BOX_LINE_H:
            break
    
    if right is None:
        return None
    
    # 向下找左下角 └ 和右下角 ┘
    bottom = None
    for r in range(top + 1, max_height):
        if r >= len(lines):
            break
        check_line = lines[r]
        
        # 检查左边界和右边界
        if left >= len(check_line) or right >= len(check_line):
            break
        
        left_char = check_line[left]
        right_char = check_line[right]
        
        # 检查是否是底边
        if left_char == '└' and right_char == '┘':
            # 验证底边
            if all(check_line[x] in BOX_LINE_H for x in range(left + 1, right)):
                bottom = r
                break
        
        # 检查是否是侧边（继续向下）
        if left_char not in BOX_LINE_V or right_char not in BOX_LINE_V:
            break
    
    if bottom is None:
        return None
    
    # 验证左右侧边
    for r in range(top + 1, bottom):
        check_line = lines[r]
        if left >= len(check_line) or right >= len(check_line):
            return None
        if check_line[left] not in BOX_LINE_V or check_line[right] not in BOX_LINE_V:
            return None
    
    # 提取框内文本
    text_lines = []
    for r in range(top + 1, bottom):
        if r < len(lines):
            text_line = lines[r][left + 1:right]
            text_lines.append(text_line)
    
    box_width = right - left + 1
    box_height = bottom - top + 1
    
    # 过滤掉太小的框
    if box_width < 5 or box_height < 2:
        return None
    
    return {
        'top': top,
        'left': left,
        'bottom': bottom,
        'right': right,
        'width': box_width,
        'height': box_height,
        'text': '\n'.join(text_lines).strip()
    }


def find_arrows(lines, boxes):
    """查找箭头，排除框内的箭头"""
    arrows = []
    box_ranges = set()
    
    # 记录框占据的区域
    for box in boxes:
        for r in range(box['top'], box['bottom'] + 1):
            for c in range(box['left'], box['right'] + 1):
                box_ranges.add((r, c))
    
    # 查找箭头
    for r, line in enumerate(lines):
        for c, char in enumerate(line):
            if char in [ARROW_DOWN, ARROW_UP] and (r, c) not in box_ranges:
                arrows.append({
                    'row': r,
                    'col': c,
                    'direction': 'down' if char == ARROW_DOWN else 'up'
                })
    
    return arrows


def parse_ascii_diagram(ascii_text):
    """解析 ASCII 框图文本"""
    lines = ascii_text.split('\n')
    
    # 找到所有完整的框
    boxes = find_complete_boxes(lines)
    
    # 找到所有箭头
    arrows = find_arrows(lines, boxes)
    
    return boxes, arrows


def draw_parsed_diagram(boxes, arrows, output_path, title="System Architecture"):
    """绘制解析出的框图"""
    
    if not boxes:
        print("No boxes to draw")
        return None
    
    # 创建图形
    fig, ax = plt.subplots(figsize=(14, 10), dpi=100)
    
    # 计算边界
    min_row = min(b['top'] for b in boxes)
    max_row = max(b['bottom'] for b in boxes)
    min_col = min(b['left'] for b in boxes)
    max_col = max(b['right'] for b in boxes)
    
    # 边界处理
    range_row = max(max_row - min_row + 1, 1)
    range_col = max(max_col - min_col + 1, 1)
    
    # 坐标转换函数 (ASCII 坐标 -> 绘图坐标)
    def to_x(col):
        return (col - min_col) / range_col * 90 + 5
    
    def to_y(row):
        return 95 - (row - min_row) / range_row * 90
    
    # 颜色
    box_color = '#E3F2FD'
    edge_color = '#1976D2'
    
    # 绘制框
    for box in boxes:
        x1 = to_x(box['left'])
        x2 = to_x(box['right'])
        y1 = to_y(box['top'])
        y2 = to_y(box['bottom'])
        
        width = x2 - x1
        height = y1 - y2
        
        # 绘制矩形
        rect = patches.Rectangle((x1, y2), width, height, linewidth=1.5,
                                  edgecolor=edge_color, facecolor=box_color, alpha=0.7)
        ax.add_patch(rect)
        
        # 添加文本
        text = box['text']
        if text:
            # 处理多行文本
            text_lines = text.split('\n')
            # 过滤空行和纯装饰行
            content_lines = [l.strip() for l in text_lines if l.strip() and not all(c in '─═' for c in l.strip())]
            
            if content_lines:
                display_text = '\n'.join(content_lines[:5])  # 最多显示 5 行
                ax.text((x1 + x2) / 2, (y1 + y2) / 2, display_text,
                        ha='center', va='center', fontsize=7,
                        bbox=dict(boxstyle='round', facecolor='white', alpha=0.5))
    
    # 绘制箭头
    for arrow in arrows:
        x = to_x(arrow['col'])
        y = to_y(arrow['row'])
        
        if arrow['direction'] == 'down':
            ax.annotate('', xy=(x, y - 2), xytext=(x, y),
                       arrowprops=dict(arrowstyle='->', color=edge_color, lw=1.5))
        else:
            ax.annotate('', xy=(x, y + 2), xytext=(x, y),
                       arrowprops=dict(arrowstyle='->', color=edge_color, lw=1.5))
    
    # 设置
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    ax.set_title(title, fontsize=14, pad=20)
    
    # 保存
    plt.tight_layout()
    plt.savefig(output_path, dpi=100, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"✓ Diagram saved: {output_path}")
    print(f"  Found {len(boxes)} boxes, {len(arrows)} arrows")
    return output_path


def extract_and_draw_from_md(md_file, output_path):
    """从 Markdown 文件中提取并绘制 ASCII 框图"""
    
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找代码块
    code_block_pattern = r'```\n?([\s\S]*?)```'
    code_blocks = re.findall(code_block_pattern, content)
    
    # 找到包含框图字符的最大代码块
    diagram_blocks = []
    for block in code_blocks:
        box_chars = sum(1 for c in block if c in ['┌', '', '└', '', '│', '─', '▼'])
        if box_chars > 10:  # 至少 10 个框图字符
            diagram_blocks.append((block, box_chars))
    
    if not diagram_blocks:
        print(f"✗ No ASCII diagram found in {md_file}")
        return None
    
    # 使用最大的框图块
    diagram_text, char_count = max(diagram_blocks, key=lambda x: x[1])
    print(f"Found diagram with {char_count} box characters")
    
    # 解析
    boxes, arrows = parse_ascii_diagram(diagram_text)
    
    # 绘制
    return draw_parsed_diagram(boxes, arrows, output_path)


if __name__ == '__main__':
    # 测试文件
    md_files = [
        '/home/wuyangcheng/signLanguage/work/手语动作准确度评测方案_20260402_简化版.md',
        '/home/wuyangcheng/signLanguage/work/手语识别技术路线推荐_20260402_简化版.md',
        '/home/wuyangcheng/signLanguage/work/手语识别技术路线推荐_v2_20260402_简化版.md',
    ]
    
    for md_file in md_files:
        if os.path.exists(md_file):
            output = md_file.replace('.md', '_ascii_chart.png')
            extract_and_draw_from_md(md_file, output)

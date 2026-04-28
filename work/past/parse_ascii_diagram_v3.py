#!/usr/bin/env python3
"""
解析 Markdown 中的 ASCII 框图并转换为 matplotlib 图形
改进版：支持嵌套框识别
"""

import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

def find_all_boxes(lines):
    """
    查找所有完整的矩形框（包括嵌套框）
    策略：找到所有 ┌，然后为每个 ┌ 寻找匹配的 ┘
    """
    boxes = []
    height = len(lines)
    used_corners = set()  # 记录已使用的角点
    
    # 找到所有左上角 ┌
    candidates = []
    for r in range(height):
        line = lines[r]
        for c in range(len(line)):
            if line[c] == '┌':
                candidates.append((r, c))
    
    # 为每个左上角找对应的框
    for top, left in candidates:
        if (top, left) in used_corners:
            continue
            
        box = find_box_from_corner(lines, top, left, height)
        if box:
            # 标记已使用的角点
            used_corners.add((box['top'], box['left']))
            used_corners.add((box['top'], box['right']))
            used_corners.add((box['bottom'], box['left']))
            used_corners.add((box['bottom'], box['right']))
            boxes.append(box)
    
    return boxes


def find_box_from_corner(lines, top, left, max_height):
    """从左上角开始寻找完整的矩形框"""
    line = lines[top]
    width = len(line)
    
    # 向右找右上角 ┐
    right = None
    for c in range(left + 1, min(width, left + 150)):  # 限制最大宽度
        if c >= len(line):
            break
        char = line[c]
        if char == '┐':
            # 验证上边框
            if all(lines[top][x] in '─┬┼├┤' for x in range(left + 1, c)):
                right = c
                break
        elif char not in '─┬┼├┤':
            break
    
    if right is None or right - left < 4:  # 最小宽度
        return None
    
    # 向下找底边
    bottom = None
    for r in range(top + 1, min(max_height, top + 50)):  # 限制最大高度
        if r >= len(lines):
            break
        check_line = lines[r]
        
        # 检查左右边界位置
        if left >= len(check_line) or right >= len(check_line):
            break
        
        left_char = check_line[left]
        right_char = check_line[right]
        
        # 检查是否是底边（左下角 + 右下角）
        if left_char == '└' and right_char == '┘':
            # 验证下边框
            if all(check_line[x] in '─┬┼├┤' for x in range(left + 1, right)):
                bottom = r
                break
        
        # 检查是否继续是侧边
        if left_char not in '│┬┴┼├┤' or right_char not in '│┬┴┼├┤':
            # 如果一侧是侧边字符，另一侧是空格，继续
            if (left_char in '│┬┴├┤' and right_char == ' ') or \
               (left_char == ' ' and right_char in '│┬┴┼├┤'):
                continue
            break
    
    if bottom is None or bottom - top < 1:  # 最小高度
        return None
    
    # 提取框内文本
    text_lines = []
    for r in range(top + 1, bottom):
        if r < len(lines):
            text_line = lines[r][left + 1:right]
            text_lines.append(text_line)
    
    return {
        'top': top,
        'left': left,
        'bottom': bottom,
        'right': right,
        'width': right - left + 1,
        'height': bottom - top + 1,
        'text': '\n'.join(text_lines).strip(),
        'text_lines': [l for l in text_lines if l.strip()]
    }


def find_arrows(lines, boxes):
    """查找箭头"""
    arrows = []
    
    for r, line in enumerate(lines):
        for c, char in enumerate(line):
            if char == '▼':
                arrows.append({'row': r, 'col': c, 'direction': 'down'})
            elif char == '▲':
                arrows.append({'row': r, 'col': c, 'direction': 'up'})
            elif char == '►':
                arrows.append({'row': r, 'col': c, 'direction': 'right'})
            elif char == '◄':
                arrows.append({'row': r, 'col': c, 'direction': 'left'})
    
    return arrows


def draw_diagram(boxes, arrows, output_path, title="System Architecture"):
    """绘制框图"""
    
    if not boxes:
        print("No boxes to draw")
        return None
    
    # 计算边界
    min_row = min(b['top'] for b in boxes)
    max_row = max(b['bottom'] for b in boxes)
    min_col = min(b['left'] for b in boxes)
    max_col = max(b['right'] for b in boxes)
    
    range_row = max(max_row - min_row + 1, 1)
    range_col = max(max_col - min_col + 1, 1)
    
    # 创建图形
    fig, ax = plt.subplots(figsize=(14, 10), dpi=100)
    
    # 坐标转换
    def to_x(col):
        return (col - min_col) / range_col * 90 + 5
    
    def to_y(row):
        return 95 - (row - min_row) / range_row * 90
    
    # 颜色
    box_color = '#E3F2FD'
    edge_color = '#1976D2'
    
    # 按面积排序，先画大框（外层），再画小框（内层）
    sorted_boxes = sorted(boxes, key=lambda b: b['width'] * b['height'], reverse=True)
    
    for box in sorted_boxes:
        x1 = to_x(box['left'])
        x2 = to_x(box['right'])
        y1 = to_y(box['top'])
        y2 = to_y(box['bottom'])
        
        width = x2 - x1
        height = y1 - y2
        
        # 跳过太大的外层容器框（只画内部内容框）
        if box['width'] > 60 and box['height'] > 20:
            # 这是外层容器，画但透明度低
            rect = patches.Rectangle((x1, y2), width, height, linewidth=1,
                                      edgecolor='#90CAF9', facecolor='none', alpha=0.5, linestyle='--')
            ax.add_patch(rect)
        else:
            # 内部内容框
            rect = patches.Rectangle((x1, y2), width, height, linewidth=1.5,
                                      edgecolor=edge_color, facecolor=box_color, alpha=0.7)
            ax.add_patch(rect)
            
            # 添加文本
            if box['text_lines']:
                # 取前几行非空文本
                display_lines = box['text_lines'][:4]
                display_text = '\n'.join(display_lines)
                
                # 计算文本位置
                text_y = (y1 + y2) / 2
                text_step = height / (len(display_lines) + 1)
                
                for i, line_text in enumerate(display_lines):
                    line_y = text_y + text_step * (len(display_lines) / 2 - i)
                    ax.text((x1 + x2) / 2, line_y, line_text.strip(),
                            ha='center', va='center', fontsize=7,
                            bbox=dict(boxstyle='round', facecolor='white', alpha=0.3))
    
    # 绘制箭头
    for arrow in arrows:
        x = to_x(arrow['col'])
        y = to_y(arrow['row'])
        
        if arrow['direction'] == 'down':
            ax.annotate('', xy=(x, y - 2), xytext=(x, y),
                       arrowprops=dict(arrowstyle='->', color=edge_color, lw=1.5))
        elif arrow['direction'] == 'up':
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
    """从 Markdown 提取并绘制 ASCII 框图"""
    
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找代码块
    code_blocks = re.findall(r'```\n?([\s\S]*?)```', content)
    
    # 找到包含最多框图字符的代码块
    best_block = None
    best_count = 0
    
    for block in code_blocks:
        count = sum(1 for c in block if c in '┌┐└┘│─├┤┬┴┼▼▲►◄')
        if count > best_count:
            best_count = count
            best_block = block
    
    if best_count < 10:
        print(f"✗ No ASCII diagram found in {md_file}")
        return None
    
    print(f"Found diagram with {best_count} box characters")
    
    # 解析
    lines = best_block.split('\n')
    boxes = find_all_boxes(lines)
    arrows = find_arrows(lines, boxes)
    
    # 绘制
    return draw_diagram(boxes, arrows, output_path)


if __name__ == '__main__':
    md_files = [
        '/home/wuyangcheng/signLanguage/work/手语动作准确度评测方案_20260402_简化版.md',
        '/home/wuyangcheng/signLanguage/work/手语识别技术路线推荐_20260402_简化版.md',
        '/home/wuyangcheng/signLanguage/work/手语识别技术路线推荐_v2_20260402_简化版.md',
    ]
    
    for md_file in md_files:
        if os.path.exists(md_file):
            output = md_file.replace('.md', '_ascii_chart_v2.png')
            extract_and_draw_from_md(md_file, output)

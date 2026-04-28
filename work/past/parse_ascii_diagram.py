#!/usr/bin/env python3
"""
解析 Markdown 中的 ASCII 框图并转换为 matplotlib 图形
支持识别：┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼ │ ─ ┌ ┐ └ ┘ 等字符
"""

import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.font_manager import FontProperties
import os

# ASCII 框图字符
BOX_CHARS = {
    'tl': '┌', 'tr': '┐', 'bl': '└', 'br': '┘',
    'v': '│', 'h': '─',
    'vr': '├', 'vl': '┤', 'hb': '┬', 'ht': '┴', 'cross': '┼',
    'arrow_v': '▼', 'arrow_h': '►'
}

def parse_ascii_diagram(ascii_text):
    """
    解析 ASCII 框图，提取框的位置和内容
    返回：boxes list of (x, y, width, height, text_lines)
    """
    lines = ascii_text.split('\n')
    
    # 找到包含框图的行（至少包含一个框图字符）
    diagram_lines = []
    in_diagram = False
    
    for line in lines:
        # 检查是否包含框图字符
        if any(c in line for c in BOX_CHARS.values()):
            in_diagram = True
            diagram_lines.append(line)
        elif in_diagram and line.strip():
            # 如果已经在框图中，继续收集非空行
            diagram_lines.append(line)
        elif in_diagram and not line.strip():
            # 空行可能表示框图结束
            break
    
    if not diagram_lines:
        return [], []
    
    # 解析框的位置
    boxes = []
    arrows = []
    
    # 查找所有完整的框（通过 ┌ 和 ┘ 定位）
    for row_idx, line in enumerate(diagram_lines):
        for col_idx, char in enumerate(line):
            if char == BOX_CHARS['tl']:  # 找到左上角
                # 寻找对应的右下角
                # 向右找右边界
                right_col = col_idx
                while right_col < len(line) and line[right_col] in [BOX_CHARS['h'], BOX_CHARS['tr'], BOX_CHARS['cross'], BOX_CHARS['vl']]:
                    if line[right_col] == BOX_CHARS['tr']:
                        break
                    right_col += 1
                
                # 向下找下边界
                bottom_row = row_idx
                while bottom_row < len(diagram_lines):
                    check_line = diagram_lines[bottom_row]
                    if col_idx < len(check_line):
                        if check_line[col_idx] == BOX_CHARS['bl']:
                            break
                        if check_line[col_idx] not in [BOX_CHARS['v'], BOX_CHARS['tl'], BOX_CHARS['vr'], BOX_CHARS['cross']]:
                            break
                    bottom_row += 1
                
                # 获取框内容
                box_width = right_col - col_idx + 1
                box_height = bottom_row - row_idx + 1
                
                # 提取框内文本
                text_lines = []
                for r in range(row_idx + 1, bottom_row):
                    if r < len(diagram_lines):
                        text_line = diagram_lines[r][col_idx + 1:right_col]
                        text_lines.append(text_line)
                
                boxes.append({
                    'row': row_idx,
                    'col': col_idx,
                    'width': box_width,
                    'height': box_height,
                    'text': '\n'.join(text_lines).strip()
                })
    
    # 查找箭头
    for row_idx, line in enumerate(diagram_lines):
        for col_idx, char in enumerate(line):
            if char == BOX_CHARS['arrow_v']:
                arrows.append({
                    'row': row_idx,
                    'col': col_idx,
                    'direction': 'down'
                })
            elif char == BOX_CHARS['arrow_h']:
                arrows.append({
                    'row': row_idx,
                    'col': col_idx,
                    'direction': 'right'
                })
    
    return boxes, arrows, diagram_lines


def draw_ascii_diagram(md_file, output_path):
    """从 Markdown 文件中提取并绘制 ASCII 框图"""
    
    # 读取 Markdown 文件
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找 ASCII 框图块（在 ``` 中且包含框图字符）
    code_block_pattern = r'```\n([\s\S]*?)```'
    code_blocks = re.findall(code_block_pattern, content)
    
    # 找到包含框图字符的代码块
    diagram_blocks = []
    for block in code_blocks:
        if any(c in block for c in ['┌', '│', '└', '┘', '─', '▼']):
            diagram_blocks.append(block)
    
    if not diagram_blocks:
        print(f"✗ No ASCII diagram found in {md_file}")
        return None
    
    # 使用第一个最大的框图
    diagram_text = max(diagram_blocks, key=len)
    
    # 解析框图
    boxes, arrows, _ = parse_ascii_diagram(diagram_text)
    
    if not boxes:
        print("✗ Could not parse boxes from ASCII diagram")
        return None
    
    # 创建图形
    fig, ax = plt.subplots(figsize=(14, 10), dpi=100)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    
    # 计算边界
    min_row = min(b['row'] for b in boxes)
    max_row = max(b['row'] + b['height'] for b in boxes)
    min_col = min(b['col'] for b in boxes)
    max_col = max(b['col'] + b['width'] for b in boxes)
    
    # 坐标转换函数
    def to_coords(row, col):
        x = (col - min_col) / (max_col - min_col) * 90 + 5
        y = 95 - (row - min_row) / (max_row - min_row) * 90
        return x, y
    
    # 绘制框
    box_color = '#E3F2FD'
    edge_color = '#1976D2'
    
    for box in boxes:
        x, y = to_coords(box['row'], box['col'])
        w = box['width'] / (max_col - min_col) * 90
        h = box['height'] / (max_row - min_row) * 90
        
        # 绘制矩形
        rect = patches.Rectangle((x, y - h), w, h, linewidth=1.5, 
                                  edgecolor=edge_color, facecolor=box_color, alpha=0.7)
        ax.add_patch(rect)
        
        # 添加文本（简化处理，只显示第一行）
        text = box['text'].split('\n')[0][:20] if box['text'] else ''
        ax.text(x + w/2, y - h/2, text, ha='center', va='center', 
                fontsize=8, wrap=True)
    
    # 绘制箭头
    for arrow in arrows:
        x1, y1 = to_coords(arrow['row'], arrow['col'])
        if arrow['direction'] == 'down':
            x2, y2 = x1, y1 - 3
        else:
            x2, y2 = x1 + 3, y1
        
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                   arrowprops=dict(arrowstyle='->', color=edge_color, lw=1.5))
    
    # 保存
    plt.tight_layout()
    plt.savefig(output_path, dpi=100, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"✓ Diagram saved: {output_path}")
    return output_path


if __name__ == '__main__':
    # 测试文件
    md_files = [
        '/home/wuyangcheng/signLanguage/work/手语动作准确度评测方案_20260402_简化版.md',
    ]
    
    for md_file in md_files:
        if os.path.exists(md_file):
            output = md_file.replace('.md', '_ascii_diagram.png')
            draw_ascii_diagram(md_file, output)

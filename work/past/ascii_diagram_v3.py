#!/usr/bin/env python3
"""
ASCII 框图转 PNG - 改进版
重点改进：
1. 正确识别所有框（包括嵌套）
2. 正确识别箭头位置和方向
3. 合理的框大小和布局
4. 清晰的文字显示
"""

import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.font_manager import FontProperties
import os
import subprocess

# 中文字体
SIMHEI_PATH = '/home/wuyangcheng/.fonts/SimHei.ttf'
cn_font = FontProperties(fname=SIMHEI_PATH, size=10) if os.path.exists(SIMHEI_PATH) else None


class ASCIIParser:
    """ASCII 框图解析器"""
    
    def __init__(self, text):
        self.lines = text.split('\n')
        self.height = len(self.lines)
        self.width = max(len(l) for l in self.lines) if self.lines else 0
        self.boxes = []
        self.arrows = []
        
    def parse(self):
        """解析整个图"""
        self._find_all_boxes()
        self._find_all_arrows()
        self._link_arrows_to_boxes()
        return self.boxes, self.arrows
    
    def _find_all_boxes(self):
        """查找所有完整的框"""
        used = set()
        
        for r in range(self.height):
            line = self.lines[r]
            for c in range(len(line)):
                if line[c] == '┌' and (r, c) not in used:
                    box = self._find_box_from_corner(r, c)
                    if box:
                        self.boxes.append(box)
                        # 标记角点已使用（允许嵌套）
                        for rr in range(box['top'], box['bottom'] + 1):
                            for cc in range(box['left'], box['right'] + 1):
                                used.add((rr, cc))
    
    def _find_box_from_corner(self, top, left):
        """从左上角找完整的框"""
        line = self.lines[top]
        
        # 找右上角 ┐
        right = None
        for c in range(left + 1, min(len(line), left + 200)):
            if line[c] == '┐':
                # 验证上边框
                if all(line[x] in '─┬┼' for x in range(left + 1, c)):
                    right = c
                    break
            elif line[c] not in '─┬┼':
                break
        
        if right is None or right - left < 4:
            return None
        
        # 找底边
        bottom = None
        for r in range(top + 1, min(self.height, top + 60)):
            if r >= len(self.lines):
                break
            check = self.lines[r]
            if left >= len(check) or right >= len(check):
                break
            
            lc, rc = check[left], check[right]
            
            # 检查底边
            if lc == '└' and rc == '┘':
                if all(check[x] in '─┬┼' for x in range(left + 1, right)):
                    bottom = r
                    break
            
            # 检查侧边（允许空格）
            if lc not in '│├┤┴┼ ' or rc not in '│├┤┬┴┼ ':
                break
        
        if bottom is None or bottom - top < 1:
            return None
        
        # 提取文本行
        text_lines = []
        for r in range(top + 1, bottom):
            if r < len(self.lines):
                txt = self.lines[r][left + 1:right]
                # 过滤装饰线
                if txt.strip() and not all(c in '─═' for c in txt.strip()):
                    text_lines.append(txt)
        
        return {
            'top': top, 'left': left, 'bottom': bottom, 'right': right,
            'width': right - left + 1, 'height': bottom - top + 1,
            'text_lines': text_lines,
            'center_row': (top + bottom) / 2,
            'center_col': (left + right) / 2
        }
    
    def _find_all_arrows(self):
        """查找所有箭头"""
        for r in range(self.height):
            line = self.lines[r]
            for c in range(len(line)):
                ch = line[c]
                if ch in '▼▲►→':
                    arrow = {'row': r, 'col': c, 'dir': self._arrow_dir(ch)}
                    self.arrows.append(arrow)
    
    def _arrow_dir(self, ch):
        """箭头方向"""
        if ch == '▼': return 'down'
        if ch == '▲': return 'up'
        if ch in '►→': return 'right'
        return 'down'
    
    def _link_arrows_to_boxes(self):
        """关联箭头到框"""
        for arrow in self.arrows:
            arrow['from_box'] = None
            arrow['to_box'] = None

            ar, ac = arrow['row'], arrow['col']

            # 找箭头来源框（箭头上方/左方的框）- 找最近的
            for i, box in enumerate(self.boxes):
                if arrow['dir'] == 'down':
                    # 向下箭头：来源在上方（框底边在箭头上方）
                    if box['bottom'] < ar and box['left'] <= ac <= box['right']:
                        # 跳过太大的容器框
                        if box['height'] > 30:
                            continue
                        if arrow['from_box'] is None or \
                           ar - box['bottom'] < ar - self.boxes[arrow['from_box']]['bottom']:
                            arrow['from_box'] = i
                elif arrow['dir'] == 'right':
                    if box['right'] < ac and box['top'] <= ar <= box['bottom']:
                        arrow['from_box'] = i

            # 找箭头目标框（箭头下方/右方的框）- 找最近的
            for i, box in enumerate(self.boxes):
                if arrow['dir'] == 'down':
                    # 向下箭头：目标在下方（框顶边在箭头下方）
                    if box['top'] > ar and box['left'] <= ac <= box['right']:
                        # 跳过太大的容器框
                        if box['height'] > 30:
                            continue
                        if arrow['to_box'] is None or \
                           box['top'] - ar < self.boxes[arrow['to_box']]['top'] - ar:
                            arrow['to_box'] = i
                elif arrow['dir'] == 'right':
                    if box['left'] > ac and box['top'] <= ar <= box['bottom']:
                        arrow['to_box'] = i


class DiagramDrawer:
    """图表绘制器"""
    
    def __init__(self, boxes, arrows):
        self.boxes = boxes
        self.arrows = arrows
        
    def draw(self, output_path, title="System Architecture"):
        """绘制图表"""
        if not self.boxes:
            return None
        
        # 计算布局
        self._calc_layout()
        
        # 创建图形
        fig_height = max(8, len(self.boxes) * 1.5)
        fig_width = 14
        fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=100)
        
        # 绘制框
        for i, box in enumerate(self.boxes):
            self._draw_box(ax, box, i)
        
        # 绘制箭头
        for arrow in self.arrows:
            self._draw_arrow(ax, arrow)
        
        # 设置
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        ax.axis('off')
        ax.set_title(title, fontsize=14, pad=10)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"  ✓ Saved: {output_path}")
        return output_path
    
    def _calc_layout(self):
        """计算布局参数"""
        if not self.boxes:
            return
        
        # 找到所有框的边界
        min_row = min(b['top'] for b in self.boxes)
        max_row = max(b['bottom'] for b in self.boxes)
        min_col = min(b['left'] for b in self.boxes)
        max_col = max(b['right'] for b in self.boxes)
        
        self.row_range = max(max_row - min_row + 1, 1)
        self.col_range = max(max_col - min_col + 1, 1)
        self.min_row = min_row
        self.min_col = min_col
        
        # 计算缩放因子，保持纵横比
        scale = min(90 / self.row_range, 90 / self.col_range) * 0.9
        self.scale = scale
        
        # 中心偏移
        self.x_offset = (100 - self.col_range * scale) / 2
        self.y_offset = (100 - self.row_range * scale) / 2 + 5
    
    def _to_coords(self, row, col):
        """ASCII 坐标转绘图坐标（ASCII row 向下增加，绘图 y 向上增加）"""
        x = self.x_offset + (col - self.min_col) * self.scale
        # ASCII 中 row 越大越靠下，绘图中 y 越大越靠上，所以需要翻转
        y = self.y_offset + (self.row_range - (row - self.min_row)) * self.scale
        return x, y
    
    def _draw_box(self, ax, box, idx):
        """绘制一个框"""
        x1, y1 = self._to_coords(box['top'], box['left'])
        x2, y2 = self._to_coords(box['bottom'], box['right'])
        
        width = x2 - x1
        height = y1 - y2
        
        # 跳过太大的外层容器框
        is_container = box['width'] > 60 and box['height'] > 25
        
        if is_container:
            # 外层容器：虚线框，无填充
            rect = patches.Rectangle((x1, y2), width, height,
                                      linewidth=1, edgecolor='#90CAF9',
                                      facecolor='none', alpha=0.3, linestyle='--')
        else:
            # 内容框：实线框，有填充
            rect = patches.Rectangle((x1, y2), width, height,
                                      linewidth=2, edgecolor='#1976D2',
                                      facecolor='#E3F2FD', alpha=0.8)
        
        ax.add_patch(rect)
        
        # 添加文本
        if box['text_lines'] and not is_container:
            self._draw_box_text(ax, box, x1, x2, y1, y2)
    
    def _draw_box_text(self, ax, box, x1, x2, y1, y2):
        """绘制框内文本"""
        cx = (x1 + x2) / 2
        text_height = y1 - y2
        
        # 计算每行文本的位置
        lines = box['text_lines'][:6]  # 最多 6 行
        line_height = text_height / (len(lines) + 1)
        
        for i, txt in enumerate(lines):
            # 计算 y 位置（从上到下）
            ty = y1 - line_height * (i + 0.3)
            
            # 清理文本
            txt = txt.strip()
            if len(txt) > 30:
                txt = txt[:28] + '...'
            
            ax.text(cx, ty, txt, ha='center', va='top',
                    fontsize=11, fontproperties=cn_font,
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
    
    def _draw_arrow(self, ax, arrow):
        """绘制箭头"""
        if arrow['from_box'] is None and arrow['to_box'] is None:
            return  # 不绘制无连接的箭头

        ar, ac = arrow['row'], arrow['col']
        x, y = self._to_coords(ar, ac)

        # 箭头样式
        arrow_style = dict(arrowstyle='->', color='#1976D2', lw=2, mutation_scale=10)

        if arrow['dir'] == 'down':
            # 向下箭头：在绘图坐标中，向下是 y 减小方向
            arrow_len = 10
            
            # 如果有目标框，调整箭头终点
            if arrow['to_box'] is not None:
                target = self.boxes[arrow['to_box']]
                _, ty = self._to_coords(target['top'], target['center_col'])
                # ty 是目标框顶部的 y 坐标，箭头应该指向 ty 下方一点（y 值更小）
                arrow_end_y = ty - 5  # 离目标框顶部一点距离（向下）
            else:
                arrow_end_y = y - arrow_len
            
            # xy 是箭头尖端（终点），xytext 是箭头尾部（起点）
            # 向下箭头：起点在上方（大 y），终点在下方（小 y）
            ax.annotate('', xy=(x, arrow_end_y), xytext=(x, y),
                       arrowprops=arrow_style)
                       
        elif arrow['dir'] == 'right':
            ax.annotate('', xy=(x + 10, y), xytext=(x, y),
                       arrowprops=arrow_style)


def extract_ascii_diagram(md_file):
    """从 Markdown 提取 ASCII 图"""
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找代码块
    blocks = re.findall(r'```\n([\s\S]*?)```', content)
    
    # 找包含最多框图字符的块
    best_block, best_count = None, 0
    for block in blocks:
        count = sum(1 for c in block if c in '┌┐│─├┤┬┴┼▼▲►→')
        if count > best_count:
            best_count = count
            best_block = block
    
    if best_count < 10:
        return None, 0
    
    return best_block, best_count


def process_md_file(md_file):
    """处理 Markdown 文件"""
    print(f"\nProcessing: {os.path.basename(md_file)}")
    
    # 提取 ASCII 图
    diagram_text, char_count = extract_ascii_diagram(md_file)
    if not diagram_text:
        print(f"  ✗ No diagram found")
        return None
    
    print(f"  Found diagram: {char_count} chars")
    
    # 解析
    parser = ASCIIParser(diagram_text)
    boxes, arrows = parser.parse()
    
    print(f"  Parsed: {len(boxes)} boxes, {len(arrows)} arrows")
    
    # 绘制
    img_path = md_file.replace('.md', '_chart.png')
    drawer = DiagramDrawer(boxes, arrows)
    drawer.draw(img_path, "Sign Language Recognition System")
    
    # 更新 Markdown
    img_rel = os.path.basename(img_path)
    img_md = f'\n\n![System Architecture]({img_rel})\n\n*图：系统架构图*\n\n'
    
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找插入位置
    markers = ['### 3.1 系统架构图', '### 技术架构', '### 3.1 手语动作评测系统架构', 
               '## 三、推荐架构设计', '### 系统架构']
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
                                '--toc', '--toc-depth=2', '--number-sections'],
                               capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✓ Generated DOCX: {out_docx}")
        else:
            print(f"  ✗ Pandoc error: {result.stderr[:200]}")
        
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

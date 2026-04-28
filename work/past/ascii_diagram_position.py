#!/usr/bin/env python3
"""
ASCII 框图转 PNG - 改进版
使用网格布局算法，基于原始 ASCII 坐标的相对位置，避免框重叠
参考：https://graphviz.org/ - Graphviz 的 DOT 布局算法思路
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
    """ASCII 框图解析器 - 保持原始位置"""
    
    def __init__(self, text):
        self.lines = text.split('\n')
        self.height = len(self.lines)
        self.boxes = []
        self.arrows = []
        
    def parse(self):
        """解析整个图"""
        self._find_all_boxes()
        self._find_all_arrows()
        self._link_arrows_to_boxes()
        self._build_edges()
        return self.boxes, self.arrows, self.edges
    
    def _find_all_boxes(self):
        """查找所有框（不跳过任何框）"""
        used = set()

        for r in range(self.height):
            line = self.lines[r]
            for c in range(len(line)):
                if line[c] == '┌' and (r, c) not in used:
                    box = self._find_box_from_corner(r, c)
                    if box and box['width'] >= 5 and box['height'] >= 2:
                        self.boxes.append(box)
                        # 只标记角点，允许嵌套
                        used.add((r, c))
                        used.add((r, box['right']))
                        used.add((box['bottom'], c))
                        used.add((box['bottom'], box['right']))
        
        # 检测容器关系：找出哪些框包含其他框
        for i, box in enumerate(self.boxes):
            box['children'] = []
            box['parent'] = None
            for j, other in enumerate(self.boxes):
                if i != j:
                    # 检查 other 是否完全在 box 内部
                    if (other['top'] > box['top'] and other['bottom'] < box['bottom'] and
                        other['left'] > box['left'] and other['right'] < box['right']):
                        # other 在 box 内部
                        # 检查是否直接子节点（没有被其他框包裹）
                        is_direct = True
                        for k, inner in enumerate(self.boxes):
                            if k != i and k != j:
                                if (other['top'] >= inner['top'] and other['bottom'] <= inner['bottom'] and
                                    other['left'] >= inner['left'] and other['right'] <= inner['right'] and
                                    inner['top'] > box['top'] and inner['bottom'] < box['bottom']):
                                    is_direct = False
                                    break
                        if is_direct:
                            box['children'].append(j)
                            self.boxes[j]['parent'] = i
    
    def _find_box_from_corner(self, top, left):
        """从左上角找完整的框"""
        line = self.lines[top]
        
        # 找右上角 ┐
        right = None
        for c in range(left + 1, min(len(line), left + 200)):
            if line[c] == '┐':
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
            
            # 如果行太短，用空格填充
            if len(check) <= right:
                check = check.ljust(right + 1)
            
            lc, rc = check[left], check[right]
            
            if lc == '└' and rc == '┘':
                if all(check[x] in '─┬┼' for x in range(left + 1, right)):
                    bottom = r
                    break
            
            # 侧边检查放宽（允许空格和更多字符）
            if lc not in '│├┤┴┬┼ ' or rc not in '│├┤┬┼ ':
                break
        
        if bottom is None or bottom - top < 1:
            return None
        
        # 提取文本行
        text_lines = []
        for r in range(top + 1, bottom):
            if r < len(self.lines):
                txt = self.lines[r][left + 1:right]
                if txt.strip() and not all(c in '─═' for c in txt.strip()):
                    text_lines.append(txt)
        
        return {
            'top': top, 'left': left, 'bottom': bottom, 'right': right,
            'width': right - left + 1, 'height': bottom - top + 1,
            'text_lines': text_lines,
            'center_col': (left + right) / 2
        }
    
    def _find_all_arrows(self):
        """查找所有箭头"""
        for r in range(self.height):
            line = self.lines[r]
            for c in range(len(line)):
                ch = line[c]
                if ch in '▼▲►→':
                    self.arrows.append({'row': r, 'col': c, 'dir': self._arrow_dir(ch)})
    
    def _arrow_dir(self, ch):
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

            # 找来源框（箭头上方最近的框）
            for i, box in enumerate(self.boxes):
                if arrow['dir'] == 'down':
                    if box['bottom'] < ar and box['left'] <= ac <= box['right']:
                        if arrow['from_box'] is None or \
                           ar - box['bottom'] < ar - self.boxes[arrow['from_box']]['bottom']:
                            arrow['from_box'] = i
                elif arrow['dir'] == 'right':
                    if box['right'] < ac and box['top'] <= ar <= box['bottom']:
                        arrow['from_box'] = i

            # 找目标框（箭头下方最近的框）
            for i, box in enumerate(self.boxes):
                if arrow['dir'] == 'down':
                    if box['top'] > ar and box['left'] <= ac <= box['right']:
                        if arrow['to_box'] is None or \
                           box['top'] - ar < self.boxes[arrow['to_box']]['top'] - ar:
                            arrow['to_box'] = i
                elif arrow['dir'] == 'right':
                    if box['left'] > ac and box['top'] <= ar <= box['bottom']:
                        arrow['to_box'] = i

    def _build_edges(self):
        """构建框之间的边（去重）"""
        self.edges = []
        used_edges = set()
        for arrow in self.arrows:
            if arrow['from_box'] is not None and arrow['to_box'] is not None:
                edge_key = (arrow['from_box'], arrow['to_box'])
                if edge_key not in used_edges:
                    self.edges.append(edge_key)
                    used_edges.add(edge_key)


class DiagramDrawer:
    """图表绘制器 - 保持原始位置关系，避免重叠"""

    def __init__(self, boxes, arrows, edges=None):
        self.boxes = boxes
        self.arrows = arrows
        self.edges = edges if edges else []
        self.box_positions = {}  # 存储调整后的框位置

    def draw(self, output_path, title="System Architecture"):
        """绘制图表"""
        if not self.boxes:
            return None

        self._calc_layout()

        # 根据实际内容调整图形大小
        fig_width = max(14, self.col_range * 0.15)
        fig_height = max(8, self.row_range * 0.15)

        fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=100)

        # 绘制框
        for i, box in enumerate(self.boxes):
            self._draw_box(ax, box, i)

        # 绘制箭头
        for arrow in self.arrows:
            self._draw_arrow(ax, arrow)

        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        ax.axis('off')
        ax.set_title(title, fontsize=14, pad=10)

        plt.tight_layout()
        plt.savefig(output_path, dpi=120, bbox_inches='tight', facecolor='white')
        plt.close()

        print(f"  ✓ Saved: {output_path} ({len(self.boxes)} boxes, {len(self.arrows)} arrows)")
        return output_path

    def _estimate_box_size(self, box):
        """预估框的显示大小（基于文本内容）"""
        min_width = 14   # 最小宽度
        min_height = 7   # 最小高度

        if box['text_lines']:
            # 计算文本需要的宽度
            max_text_width = 0
            for txt in box['text_lines']:
                # 中文每个字约 0.9 单位，英文约 0.45 单位
                width = sum(0.9 if ord(c) > 127 else 0.45 for c in txt)
                max_text_width = max(max_text_width, width)
            
            req_width = max(min_width, max_text_width + 4)
            # 每行文本需要的高度
            req_height = max(min_height, len(box['text_lines']) * 2.2 + 2)
            return req_width, req_height
        
        return min_width, min_height

    def _calc_layout(self):
        """计算布局 - 分层布局算法（类似 Graphviz 的 dot 算法简化版）"""
        if not self.boxes:
            return

        # 第一步：找到所有框的边界
        min_row = min(b['top'] for b in self.boxes)
        max_row = max(b['bottom'] for b in self.boxes)
        min_col = min(b['left'] for b in self.boxes)
        max_col = max(b['right'] for b in self.boxes)

        self.min_row = min_row
        self.max_row = max_row
        self.min_col = min_col
        self.max_col = max_col
        self.row_range = max(max_row - min_row + 1, 1)
        self.col_range = max(max_col - min_col + 1, 1)

        # 第二步：计算每个框的预估大小并初始化位置
        margin_x = 5
        margin_y = 5
        
        for i, box in enumerate(self.boxes):
            box['est_width'], box['est_height'] = self._estimate_box_size(box)
            
            # 基于原始位置的初始坐标
            center_col = (box['left'] + box['right']) / 2
            x = margin_x + (center_col - self.min_col) * 0.5
            y = margin_y + (self.row_range - (box['top'] - self.min_row)) * 0.5
            
            self.box_positions[i] = {
                'x': x,
                'y': y,
                'width': box['est_width'] * 0.5,
                'height': box['est_height'] * 0.5,
                'center_x': x + box['est_width'] * 0.25,
                'bottom_y': y + box['est_height'] * 0.5,
            }

        # 第三步：根据边关系给节点分层（类似 Kahn 算法）
        in_degree = {i: 0 for i in range(len(self.boxes))}
        adj = {i: [] for i in range(len(self.boxes))}
        
        for from_idx, to_idx in self.edges:
            in_degree[to_idx] += 1
            adj[from_idx].append(to_idx)
        
        # 分层
        layers = []
        remaining = set(range(len(self.boxes)))
        
        while remaining:
            # 找入度为 0 的节点
            layer_nodes = [i for i in remaining if in_degree[i] == 0]
            
            if not layer_nodes:
                # 有环，按原始位置分层
                layer_nodes = sorted(remaining, key=lambda i: self.boxes[i]['top'])
            
            layer_nodes.sort(key=lambda i: self.boxes[i]['top'])
            layers.append(layer_nodes)
            
            for node in layer_nodes:
                remaining.discard(node)
                for neighbor in adj.get(node, []):
                    in_degree[neighbor] -= 1
        
        # 第四步：重新放置每一层的框
        layer_spacing = 12
        box_spacing_x = 4
        current_y = 95 - margin_y
        
        for layer_idx, layer in enumerate(layers):
            max_height = max(self.box_positions[i]['height'] for i in layer if i in self.box_positions)
            layer_y = current_y - max_height
            
            current_x = margin_x
            for box_idx in layer:
                if box_idx not in self.box_positions:
                    continue
                    
                pos = self.box_positions[box_idx]
                pos['y'] = layer_y
                pos['x'] = current_x
                pos['center_x'] = current_x + pos['width'] / 2
                pos['bottom_y'] = layer_y + pos['height']
                
                current_x += pos['width'] + box_spacing_x
            
            current_y = layer_y - layer_spacing
        
        # 第五步：确保边界
        self._ensure_bounds(5, 5)

    def _calc_flat_layout(self):
        """扁平布局 - 所有框都是独立的（按原始位置）"""
        # 找到所有框的边界
        min_row = min(b['top'] for b in self.boxes)
        max_row = max(b['bottom'] for b in self.boxes)
        min_col = min(b['left'] for b in self.boxes)
        max_col = max(b['right'] for b in self.boxes)

        self.min_row = min_row
        self.max_row = max_row
        self.min_col = min_col
        self.max_col = max_col

        self.row_range = max(max_row - min_row + 1, 1)
        self.col_range = max(max_col - min_col + 1, 1)

        # 计算缩放因子
        margin_x = 3
        margin_y = 3
        
        available_width = 100 - 2 * margin_x
        available_height = 100 - 2 * margin_y
        
        scale_x = available_width / self.col_range
        scale_y = available_height / self.row_range
        base_scale = min(scale_x, scale_y) * 0.85

        # 计算每个框的初始位置
        for i, box in enumerate(self.boxes):
            center_col = (box['left'] + box['right']) / 2
            x = margin_x + (center_col - self.min_col) * base_scale
            y = margin_y + (self.row_range - (box['top'] - self.min_row)) * base_scale
            
            self.box_positions[i] = {
                'x': x - box['est_width'] * base_scale / 2,
                'y': y - box['est_height'] * base_scale / 2,
                'width': box['est_width'] * base_scale,
                'height': box['est_height'] * base_scale,
                'center_x': x,
                'bottom_y': y - box['est_height'] * base_scale / 2 + box['est_height'] * base_scale,
            }

        # 迭代调整位置，避免重叠
        self._resolve_overlaps(200, 2, 3)
        self._ensure_bounds(3, 3)
        
        self.scale = base_scale
        self.x_offset = margin_x
        self.y_offset = margin_y

    def _resolve_overlaps(self, max_iterations, spacing_x, spacing_y):
        """迭代解决重叠问题"""
        for iteration in range(max_iterations):
            moved = False
            for i in range(len(self.boxes)):
                if i not in self.box_positions:
                    continue
                pos_i = self.box_positions[i]
                
                for j in range(i + 1, len(self.boxes)):
                    if j not in self.box_positions:
                        continue
                    pos_j = self.box_positions[j]
                    
                    overlap_x = not (pos_i['x'] + pos_i['width'] + spacing_x <= pos_j['x'] or
                                    pos_j['x'] + pos_j['width'] + spacing_x <= pos_i['x'])
                    overlap_y = not (pos_i['y'] + pos_i['height'] + spacing_y <= pos_j['y'] or
                                    pos_j['y'] + pos_j['height'] + spacing_y <= pos_i['y'])
                    
                    if overlap_x and overlap_y:
                        inter_left = max(pos_i['x'], pos_j['x'])
                        inter_right = min(pos_i['x'] + pos_i['width'], pos_j['x'] + pos_j['width'])
                        inter_bottom = max(pos_i['y'], pos_j['y'])
                        inter_top = min(pos_i['y'] + pos_i['height'], pos_j['y'] + pos_j['height'])
                        
                        inter_width = inter_right - inter_left
                        inter_height = inter_top - inter_bottom
                        
                        if inter_height > inter_width:
                            if pos_i['y'] < pos_j['y']:
                                pos_j['y'] += inter_height + spacing_y
                            else:
                                pos_i['y'] += inter_height + spacing_y
                        else:
                            if pos_i['x'] < pos_j['x']:
                                pos_j['x'] += inter_width + spacing_x
                            else:
                                pos_i['x'] += inter_width + spacing_x
                        
                        moved = True
                
                if i in self.box_positions:
                    pos_i['center_x'] = pos_i['x'] + pos_i['width'] / 2
                    pos_i['bottom_y'] = pos_i['y'] + pos_i['height']
            
            if not moved:
                break

    def _ensure_bounds(self, margin_x, margin_y):
        """确保所有框在边界内"""
        for i, pos in self.box_positions.items():
            pos['x'] = max(margin_x, min(pos['x'], 100 - margin_x - pos['width']))
            pos['y'] = max(margin_y, min(pos['y'], 100 - margin_y - pos['height']))
            pos['center_x'] = pos['x'] + pos['width'] / 2
            pos['bottom_y'] = pos['y'] + pos['height']

    def _to_coords(self, row, col):
        """ASCII 坐标转绘图坐标 - 保持相对位置"""
        x = self.x_offset + (col - self.min_col) * self.scale
        y = self.y_offset + (self.row_range - (row - self.min_row)) * self.scale
        return x, y

    def _draw_box(self, ax, box, idx):
        """绘制框 - 使用调整后的位置，跳过大型容器框"""
        # 如果是容器框且有子框，只绘制容器边框（不填充背景）
        is_container = len(box.get('children', [])) > 0
        
        if idx in self.box_positions:
            pos = self.box_positions[idx]
            x1, y2 = pos['x'], pos['y']
            width, height = pos['width'], pos['height']
        else:
            # fallback to original method
            x1, y1 = self._to_coords(box['top'], box['left'])
            x2, y2 = self._to_coords(box['bottom'], box['right'])
            x1, y2 = x1, y2
            width = x2 - x1
            height = y1 - y2

        if is_container:
            # 容器框：只绘制边框，透明度更高
            rect = patches.Rectangle((x1, y2), width, height,
                                      linewidth=1, edgecolor='#B0BEC5',
                                      facecolor='none', alpha=0.3, linestyle='--')
        else:
            # 内容框：填充背景
            rect = patches.Rectangle((x1, y2), width, height,
                                      linewidth=1.5, edgecolor='#1976D2',
                                      facecolor='#E3F2FD', alpha=0.7)
        ax.add_patch(rect)

        # 添加文本
        if box['text_lines']:
            self._draw_box_text(ax, box, x1, x1 + width, y2 + height, y2)
    
    def _draw_box_text(self, ax, box, x1, x2, y1, y2):
        """绘制框内文本"""
        cx = (x1 + x2) / 2
        text_height = y1 - y2
        
        # 清理文本
        lines = []
        for txt in box['text_lines'][:3]:
            txt = txt.strip()
            # 移除框图字符
            txt = re.sub(r'[│├┤┬┴┼─]', ' ', txt)
            txt = ' '.join(txt.split())
            if txt and len(txt) > 1:
                lines.append(txt[:35])
        
        if not lines:
            return
        
        # 计算文本位置
        line_height = text_height / (len(lines) + 1)
        
        for i, txt in enumerate(lines):
            ty = y1 - line_height * (i + 0.5)
            ax.text(cx, ty, txt, ha='center', va='center',
                    fontsize=8, fontproperties=cn_font,
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.7, pad=0.2))
    
    def _draw_arrow(self, ax, arrow):
        """绘制箭头 - 使用调整后的框位置"""
        arrow_style = dict(arrowstyle='->', color='#1976D2', lw=2, mutation_scale=10)

        # 获取来源框和目标框的调整后位置
        from_pos = None
        to_pos = None
        
        if arrow['from_box'] is not None and arrow['from_box'] in self.box_positions:
            from_pos = self.box_positions[arrow['from_box']]
        
        if arrow['to_box'] is not None and arrow['to_box'] in self.box_positions:
            to_pos = self.box_positions[arrow['to_box']]

        if arrow['dir'] == 'down':
            if from_pos and to_pos:
                # 从来源框底部中心到目标框顶部中心
                start_x = from_pos['center_x']
                start_y = from_pos['bottom_y']
                end_y = to_pos['y']
                
                # 如果目标框在来源框下方，正常绘制
                if end_y < start_y:
                    ax.annotate('', xy=(start_x, end_y), xytext=(start_x, start_y),
                               arrowprops=arrow_style)
                else:
                    # 位置反转，画个短箭头表示连接
                    mid_y = (start_y + end_y) / 2
                    ax.annotate('', xy=(start_x, mid_y - 3), xytext=(start_x, mid_y + 3),
                               arrowprops=arrow_style)
            elif from_pos:
                # 只有来源框，向下画一段
                start_x = from_pos['center_x']
                start_y = from_pos['bottom_y']
                ax.annotate('', xy=(start_x, start_y - 6), xytext=(start_x, start_y),
                           arrowprops=arrow_style)
            elif to_pos:
                # 只有目标框，从上方画下来
                end_x = to_pos['center_x']
                end_y = to_pos['y']
                ax.annotate('', xy=(end_x, end_y), xytext=(end_x, end_y + 6),
                           arrowprops=arrow_style)

        elif arrow['dir'] == 'right':
            if from_pos and to_pos:
                # 从来源框右侧到目标框左侧
                start_x = from_pos['x'] + from_pos['width']
                start_y = from_pos['y'] + from_pos['height'] / 2
                end_x = to_pos['x']
                ax.annotate('', xy=(end_x, start_y), xytext=(start_x, start_y),
                           arrowprops=arrow_style)
            elif from_pos:
                start_x = from_pos['x'] + from_pos['width']
                start_y = from_pos['y'] + from_pos['height'] / 2
                ax.annotate('', xy=(start_x + 6, start_y), xytext=(start_x, start_y),
                           arrowprops=arrow_style)


def extract_ascii_diagram(md_file):
    """从 Markdown 提取 ASCII 图"""
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    blocks = re.findall(r'```\n([\s\S]*?)```', content)
    
    best_block, best_count = None, 0
    for block in blocks:
        count = sum(1 for c in block if c in '┌┐│─├┤┬▼▲►→')
        if count > best_count:
            best_count = count
            best_block = block
    
    if best_count < 10:
        return None, 0
    
    return best_block, best_count


def process_md_file(md_file):
    """处理 Markdown 文件"""
    print(f"\nProcessing: {os.path.basename(md_file)}")
    
    diagram_text, char_count = extract_ascii_diagram(md_file)
    if not diagram_text:
        print(f"  ✗ No diagram found")
        return None
    
    print(f"  Found diagram: {char_count} chars")
    
    parser = ASCIIParser(diagram_text)
    boxes, arrows, edges = parser.parse()

    print(f"  Parsed: {len(boxes)} boxes, {len(edges)} edges")

    img_path = md_file.replace('.md', '_chart.png')
    drawer = DiagramDrawer(boxes, arrows, edges)
    drawer.draw(img_path, "Sign Language Recognition System")
    
    # 更新 Markdown
    img_rel = os.path.basename(img_path)
    img_md = f'\n\n![System Architecture]({img_rel})\n\n*图：系统架构图*\n\n'
    
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
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
        
        out_docx = out_md.replace('.md', '.docx')
        result = subprocess.run(['pandoc', out_md, '-o', out_docx,
                                '--toc', '--toc-depth=2', '--number-sections'],
                               capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✓ Generated DOCX: {out_docx}")
        
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

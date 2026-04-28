#!/usr/bin/env python3
"""
ASCII 框图转 PNG - Graphviz 自动布局版
使用 Graphviz 的 dot 引擎进行自动布局，避免框重叠
"""

import re
import os
import subprocess
import tempfile
from graphviz import Digraph


class ASCIIParser:
    """ASCII 框图解析器 - 提取框和箭头关系"""

    def __init__(self, text):
        self.lines = text.split('\n')
        self.height = len(self.lines)
        self.boxes = []
        self.arrows = []
        self.edges = []  # 框之间的连接关系

    def parse(self):
        """解析整个图"""
        self._find_all_boxes()
        self._find_all_arrows()
        self._link_arrows_to_boxes()
        self._build_edges()
        return self.boxes, self.arrows, self.edges

    def _find_all_boxes(self):
        """查找所有框"""
        used = set()

        for r in range(self.height):
            line = self.lines[r]
            for c in range(len(line)):
                if line[c] == '┌' and (r, c) not in used:
                    box = self._find_box_from_corner(r, c)
                    if box and box['width'] >= 5 and box['height'] >= 2:
                        # 跳过太大的容器框（宽度>100 或高度>30）
                        if box['width'] > 100 or box['height'] > 30:
                            continue
                        self.boxes.append(box)
                        used.add((r, c))
                        used.add((r, box['right']))
                        used.add((box['bottom'], c))
                        used.add((box['bottom'], box['right']))

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

            if len(check) <= right:
                check = check.ljust(right + 1)

            lc, rc = check[left], check[right]

            if lc == '└' and rc == '┘':
                if all(check[x] in '─┬┼' for x in range(left + 1, right)):
                    bottom = r
                    break

            if lc not in '│├┤┬┼ ' or rc not in '│├┤┬┼ ':
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

            # 找来源框
            for i, box in enumerate(self.boxes):
                if arrow['dir'] == 'down':
                    if box['bottom'] < ar and box['left'] <= ac <= box['right']:
                        if arrow['from_box'] is None or \
                           ar - box['bottom'] < ar - self.boxes[arrow['from_box']]['bottom']:
                            arrow['from_box'] = i
                elif arrow['dir'] == 'right':
                    if box['right'] < ac and box['top'] <= ar <= box['bottom']:
                        arrow['from_box'] = i

            # 找目标框
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
        """构建框之间的边"""
        used_edges = set()
        for arrow in self.arrows:
            if arrow['from_box'] is not None and arrow['to_box'] is not None:
                edge_key = (arrow['from_box'], arrow['to_box'])
                if edge_key not in used_edges:
                    self.edges.append((arrow['from_box'], arrow['to_box']))
                    used_edges.add(edge_key)


def create_graphviz_diagram(boxes, edges, output_path, title="System Architecture"):
    """使用 Graphviz 创建流程图"""
    
    # 创建 Digraph
    dot = Digraph(comment=title, engine='dot')
    
    # 设置图形属性
    dot.attr('graph', 
             rankdir='TB',  # 从上到下布局
             nodesep='0.5',  # 节点最小间距
             ranksep='0.8',  # 层级间距
             fontname='SimHei',
             fontsize='14',
             label=title,
             labelloc='t',
             pad='0.5')
    
    # 设置节点默认属性
    dot.attr('node', 
             shape='box',
             style='filled,rounded',
             fillcolor='#E3F2FD',
             color='#1976D2',
             fontname='SimHei',
             fontsize='10',
             penwidth='1.5')
    
    # 设置边默认属性
    dot.attr('edge',
             color='#1976D2',
             penwidth='2',
             arrowsize='0.8')
    
    # 添加节点
    for i, box in enumerate(boxes):
        node_id = f'n{i}'
        
        # 构建节点标签（合并多行文本）
        if box['text_lines']:
            lines = []
            for txt in box['text_lines'][:4]:
                txt = txt.strip()
                txt = re.sub(r'[│├┤┴┼─]', ' ', txt)
                txt = ' '.join(txt.split())
                if txt and len(txt) > 1:
                    lines.append(txt[:40])
            label = '\\n'.join(lines) if lines else f'Box {i}'
        else:
            label = f'Box {i}'
        
        dot.node(node_id, label)
    
    # 添加边
    for from_idx, to_idx in edges:
        dot.edge(f'n{from_idx}', f'n{to_idx}')
    
    # 渲染并保存
    try:
        # 渲染为 PNG
        output = dot.render(output_path, format='png', cleanup=True)
        print(f"  ✓ Saved: {output}.png ({len(boxes)} boxes, {len(edges)} edges)")
        return f"{output}.png"
    except Exception as e:
        print(f"  ✗ Error rendering: {e}")
        # 如果 SimHei 字体不可用，尝试使用默认字体
        dot.attr('graph', fontname='Helvetica')
        dot.attr('node', fontname='Helvetica')
        output = dot.render(output_path, format='png', cleanup=True)
        print(f"  ✓ Saved (fallback font): {output}.png")
        return f"{output}.png"


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

    # 使用 Graphviz 生成图表
    img_path_base = md_file.replace('.md', '_chart_gv')
    img_path = create_graphviz_diagram(boxes, edges, img_path_base, "Sign Language Recognition System")

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
        out_md = md_file.replace('.md', '_with_chart_gv.md')
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

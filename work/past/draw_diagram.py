#!/usr/bin/env python3
"""
生成手语识别系统架构图 - 简化版
使用 matplotlib 绘制简单的流程图
"""

import matplotlib
matplotlib.use('Agg')  # 非交互式后端
import matplotlib.pyplot as plt
import os

def draw_simple_diagram(output_path):
    """绘制简单的系统架构图"""
    
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']  # 使用英文避免字体问题
    plt.rcParams['axes.unicode_minus'] = False
    
    # 创建图形
    fig, ax = plt.subplots(figsize=(12, 8), dpi=100)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 9)
    ax.axis('off')
    
    # 标题
    ax.text(6, 8.5, 'Sign Language Recognition System Architecture', 
            ha='center', va='bottom', fontsize=14, fontweight='bold')
    
    # 定义样式
    box_color = '#E3F2FD'
    arrow_color = '#1976D2'
    
    # 绘制各层（使用英文标签）
    layers = [
        {'y': 7.2, 'h': 0.6, 'label': 'Input Layer', 
         'boxes': [('Camera\nStream', 1), ('Video\nLibrary', 5.5), ('File\nImport', 10)]},
        {'y': 5.5, 'h': 0.8, 'label': 'Feature Extraction\n(MediaPipe Holistic)', 
         'boxes': [('Hand\n42 pts', 2), ('Body\n33 pts', 5.5), ('Face\n468 pts', 9)]},
        {'y': 4.2, 'h': 0.6, 'label': 'Feature Encoding', 
         'boxes': [('Normalization', 2), ('Dimension\nReduction', 5.5), ('Feature\nConcat', 9)]},
        {'y': 2.9, 'h': 0.6, 'label': 'Storage Layer\n(FAISS Vector DB)', 
         'boxes': [('Vector Index\n[543-dim]', 3.5), ('Metadata', 8)]},
        {'y': 1.6, 'h': 0.6, 'label': 'Matching Layer', 
         'boxes': [('Similarity\nSearch (Top-K)', 3.5), ('Threshold\nDecision', 8)]},
        {'y': 0.4, 'h': 0.5, 'label': 'Output Layer', 
         'boxes': [('Result', 2), ('Score', 5.5), ('Visualization', 9)]},
    ]
    
    # 绘制层和框
    for layer in layers:
        # 层标签
        ax.text(0.2, layer['y'] + layer['h']/2, layer['label'], 
                ha='left', va='center', fontsize=8, fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='#BBDEFB', alpha=0.7))
        
        # 功能框
        for label, x in layer['boxes']:
            rect = plt.Rectangle((x, layer['y']), 2, layer['h'], 
                                linewidth=1.2, edgecolor=arrow_color, 
                                facecolor=box_color, alpha=0.6)
            ax.add_patch(rect)
            ax.text(x + 1, layer['y'] + layer['h']/2, label,
                    ha='center', va='center', fontsize=7)
    
    # 绘制箭头
    arrows = [(6, 7.2, 6, 6.3), (6, 5.5, 6, 4.8), (6, 4.2, 6, 3.5), 
              (6, 2.9, 6, 2.2), (6, 1.6, 6, 0.9)]
    for x1, y1, x2, y2 in arrows:
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                   arrowprops=dict(arrowstyle='->', color=arrow_color, lw=1.5))
    
    # 保存
    plt.tight_layout()
    plt.savefig(output_path, dpi=100, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"✓ Diagram saved: {output_path}")
    return output_path


if __name__ == '__main__':
    diagram_path = '/home/wuyangcheng/signLanguage/work/sign_language_architecture.png'
    draw_simple_diagram(diagram_path)
    
    # 更新 Markdown 文件添加图片引用
    docs = [
        '手语识别技术路线推荐_20260402_简化版.md',
        '手语识别技术路线推荐_v2_20260402_简化版.md',
        '手语动作准确度评测方案_20260402_简化版.md',
    ]
    
    for md_file in docs:
        md_path = f'/home/wuyangcheng/signLanguage/work/{md_file}'
        if os.path.exists(md_path):
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 找到插入位置
            markers = ["### 3.1 系统架构图", "## 三、推荐架构设计", "## System Architecture"]
            insert_marker = None
            for m in markers:
                if m in content:
                    insert_marker = m
                    break
            
            if insert_marker:
                idx = content.find(insert_marker)
                end_of_line = content.find('\n', idx)
                image_md = f'\n\n![System Architecture](sign_language_architecture.png)\n\n*Figure 1: System Architecture Diagram*\n\n'
                new_content = content[:end_of_line+1] + image_md + content[end_of_line+1:]
                
                output_md = md_path.replace('.md', '_带图.md')
                with open(output_md, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"✓ Updated: {output_md}")

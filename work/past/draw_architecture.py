#!/usr/bin/env python3
"""
生成手语识别系统架构图并插入 Word 文档
使用 matplotlib 绘制流程图
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from docx import Document
from docx.shared import Cm, Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os

def draw_architecture_diagram(output_path, title="手语识别系统架构图"):
    """使用 matplotlib 绘制系统架构图"""
    
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 创建图形
    fig, ax = plt.subplots(figsize=(14, 10), dpi=150)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # 标题
    ax.text(7, 9.5, title, ha='center', va='bottom', fontsize=16, fontweight='bold')
    
    # 定义颜色和样式
    box_color = '#E3F2FD'
    arrow_color = '#1976D2'
    
    # 绘制各层
    layers = [
        # 输入层 (y=8.0-8.8)
        {'y': 8.0, 'height': 0.8, 'label': '输入层', 
         'boxes': [('摄像头实时\n视频流', 1), ('标准手语\n视频库', 5.5), ('视频文件\n导入', 10)]},
        
        # 特征提取层 (y=6.0-7.2)
        {'y': 6.0, 'height': 1.2, 'label': '特征提取层\n(MediaPipe Holistic)', 
         'boxes': [('手势\n42 点', 2), ('肢体\n33 点', 6), ('面部\n468 点', 10)]},
        
        # 特征编码层 (y=4.5-5.5)
        {'y': 4.5, 'height': 1.0, 'label': '特征编码层', 
         'boxes': [('时序归一化', 2), ('空间归一化', 6), ('特征拼接', 10)]},
        
        # 存储层 (y=3.0-4.0)
        {'y': 3.0, 'height': 1.0, 'label': '存储层\n(FAISS 向量数据库)', 
         'boxes': [('向量索引\n[543 维 float]', 4), ('元数据\n{语义，路径...}', 9)]},
        
        # 匹配层 (y=1.5-2.5)
        {'y': 1.5, 'height': 1.0, 'label': '匹配层', 
         'boxes': [('相似度搜索\n(Top-K)', 4), ('阈值判定', 9)]},
        
        # 输出层 (y=0.3-1.0)
        {'y': 0.3, 'height': 0.7, 'label': '输出层', 
         'boxes': [('识别结果', 2), ('相似度分数', 6), ('可视化', 10)]},
    ]
    
    # 绘制层标签和框
    for layer in layers:
        # 层标签
        ax.text(0.3, layer['y'] + layer['height']/2, layer['label'], 
                ha='left', va='center', fontsize=9, fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='#BBDEFB', alpha=0.8))
        
        # 功能框
        for box in layer['boxes']:
            label, x = box
            rect = patches.Rectangle((x, layer['y']), 2.5, layer['height'], 
                                     linewidth=1.5, edgecolor=arrow_color, 
                                     facecolor=box_color, alpha=0.7)
            ax.add_patch(rect)
            ax.text(x + 1.25, layer['y'] + layer['height']/2, label,
                    ha='center', va='center', fontsize=8, linespacing=1.5)
    
    # 绘制箭头连接
    arrow_positions = [
        (7, 8.0, 7, 7.2),   # 输入层 → 特征提取层
        (7, 6.0, 7, 5.5),   # 特征提取层 → 特征编码层
        (7, 4.5, 7, 4.0),   # 特征编码层 → 存储层
        (7, 3.0, 7, 2.5),   # 存储层 → 匹配层
        (7, 1.5, 7, 1.0),   # 匹配层 → 输出层
    ]
    
    for x1, y1, x2, y2 in arrow_positions:
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                   arrowprops=dict(arrowstyle='->', color=arrow_color, 
                                  lw=2, mutation_scale=10))
    
    # 保存
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return output_path


def add_image_to_markdown(md_file, output_md, diagram_path):
    """在 Markdown 文件中添加架构图引用"""
    
    # 读取原始 Markdown
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找到第一个二级标题（架构设计部分）
    insert_marker = "### 3.1 系统架构图"
    if insert_marker not in content:
        insert_marker = "## 三、推荐架构设计"
    
    # 获取图片相对路径
    rel_diagram_path = os.path.basename(diagram_path)
    
    # 添加图片引用
    image_markdown = f"\n\n![手语识别系统架构图]({rel_diagram_path})\n\n*图 1: 手语识别系统架构图*\n\n"
    
    # 在标记后插入
    idx = content.find(insert_marker)
    if idx > 0:
        # 找到该行末尾
        end_of_line = content.find('\n', idx)
        new_content = content[:end_of_line+1] + image_markdown + content[end_of_line+1:]
    else:
        new_content = content
    
    # 保存新 Markdown
    with open(output_md, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✓ 已更新 Markdown: {output_md}")
    return output_md


if __name__ == '__main__':
    # 生成架构图
    diagram_path = '/home/wuyangcheng/signLanguage/work/手语识别系统架构图.png'
    draw_architecture_diagram(diagram_path)
    print(f"✓ 架构图已生成：{diagram_path}")
    
    # 为三个文档添加架构图到 Markdown
    docs = [
        ('手语识别技术路线推荐_20260402_简化版.md', '手语识别技术路线推荐_20260402_简化版_带图.md'),
        ('手语识别技术路线推荐_v2_20260402_简化版.md', '手语识别技术路线推荐_v2_20260402_简化版_带图.md'),
        ('手语动作准确度评测方案_20260402_简化版.md', '手语动作准确度评测方案_20260402_简化版_带图.md'),
    ]
    
    for md_file, output_md in docs:
        md_path = f'/home/wuyangcheng/signLanguage/work/{md_file}'
        output_path = f'/home/wuyangcheng/signLanguage/work/{output_md}'
        
        if os.path.exists(md_path):
            add_image_to_markdown(md_path, output_path, diagram_path)
    
    # 转换带图的 Markdown 为 Word
    print("\n正在生成 Word 文档...")
    import subprocess
    
    for md_file, output_md in docs:
        md_path = f'/home/wuyangcheng/signLanguage/work/{output_md}'
        docx_path = md_path.replace('.md', '.docx')
        
        if os.path.exists(md_path):
            subprocess.run([
                'pandoc', md_path, '-o', docx_path,
                '--toc', '--toc-depth=2', '--number-sections', '-M', 'lang=en'
            ], check=True)
            print(f"✓ Word 文档已生成：{docx_path}")

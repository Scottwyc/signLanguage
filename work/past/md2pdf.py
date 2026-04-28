#!/usr/bin/env python3
"""
Markdown to PDF converter for sign language technical report
使用 reportlab 生成格式规范的 PDF 报告
"""

import markdown
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import re
import os

def register_chinese_fonts():
    """注册中文字体"""
    # 尝试注册系统字体
    font_paths = [
        '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc',
    ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(pdfmetrics.TTFont('Chinese', font_path))
                print(f"成功注册中文字体：{font_path}")
                return 'Chinese'
            except:
                continue
    
    # 如果找不到中文字体，使用默认字体
    print("未找到中文字体，使用默认字体（中文可能显示异常）")
    return 'Helvetica'

def parse_markdown(md_content):
    """解析 Markdown 内容"""
    # 使用 markdown 库转换为 HTML
    html = markdown.markdown(md_content, extensions=['tables', 'fenced_code', 'toc'])
    return html

def html_to_flowables(html, styles, font_name):
    """将 HTML 转换为 reportlab flowables"""
    flowables = []
    
    # 简化处理：按行解析
    lines = html.split('\n')
    current_paragraph = []
    in_table = False
    table_data = []
    
    for line in lines:
        line = line.strip()
        
        # 跳过空行
        if not line:
            if current_paragraph:
                text = ' '.join(current_paragraph)
                flowables.append(Paragraph(text, styles['Normal']))
                flowables.append(Spacer(1, 0.3*cm))
                current_paragraph = []
            continue
        
        # 处理标题
        if line.startswith('<h1>'):
            if current_paragraph:
                text = ' '.join(current_paragraph)
                flowables.append(Paragraph(text, styles['Normal']))
                current_paragraph = []
            title = re.sub(r'<h1[^>]*>|</h1>', '', line)
            flowables.append(Paragraph(title, styles['Heading1']))
            flowables.append(Spacer(1, 0.5*cm))
        
        elif line.startswith('<h2>'):
            if current_paragraph:
                text = ' '.join(current_paragraph)
                flowables.append(Paragraph(text, styles['Normal']))
                current_paragraph = []
            title = re.sub(r'<h2[^>]*>|</h2>', '', line)
            flowables.append(Paragraph(title, styles['Heading2']))
            flowables.append(Spacer(1, 0.4*cm))
        
        elif line.startswith('<h3>'):
            if current_paragraph:
                text = ' '.join(current_paragraph)
                flowables.append(Paragraph(text, styles['Normal']))
                current_paragraph = []
            title = re.sub(r'<h3[^>]*>|</h3>', '', line)
            flowables.append(Paragraph(title, styles['Heading3']))
            flowables.append(Spacer(1, 0.3*cm))
        
        # 处理表格
        elif line.startswith('<table>'):
            in_table = True
            table_data = []
        
        elif line.startswith('</table>'):
            in_table = False
            if table_data:
                # 创建表格
                t = Table(table_data, colWidths='*')
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), font_name),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), font_name),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                flowables.append(t)
                flowables.append(Spacer(1, 0.5*cm))
        
        elif in_table and (line.startswith('<tr>') or line.startswith('<td') or line.startswith('<th')):
            # 解析表格行
            cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', line)
            if cells:
                row_data = [re.sub(r'<[^>]+>', '', cell) for cell in cells]
                table_data.append(row_data)
        
        # 处理代码块
        elif line.startswith('<pre>'):
            if current_paragraph:
                text = ' '.join(current_paragraph)
                flowables.append(Paragraph(text, styles['Normal']))
                current_paragraph = []
        
        elif line.startswith('</pre>'):
            pass
        
        # 处理普通段落
        elif not line.startswith('<') and not in_table:
            text = re.sub(r'<[^>]+>', '', line)
            if text.strip():
                current_paragraph.append(text)
    
    return flowables

def create_pdf(md_file, pdf_file):
    """创建 PDF"""
    # 注册字体
    font_name = register_chinese_fonts()
    
    # 创建文档
    doc = SimpleDocTemplate(
        pdf_file,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # 定义样式
    styles = getSampleStyleSheet()
    
    # 注册中文字体样式
    styles.add(ParagraphStyle(
        name='ChineseNormal',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=11,
        leading=18,
        alignment=TA_LEFT,
        spaceAfter=10
    ))
    
    styles.add(ParagraphStyle(
        name='ChineseHeading1',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=18,
        leading=24,
        alignment=TA_LEFT,
        spaceAfter=20,
        spaceBefore=30
    ))
    
    styles.add(ParagraphStyle(
        name='ChineseHeading2',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=14,
        leading=20,
        alignment=TA_LEFT,
        spaceAfter=15,
        spaceBefore=25
    ))
    
    styles.add(ParagraphStyle(
        name='ChineseHeading3',
        parent=styles['Heading3'],
        fontName=font_name,
        fontSize=12,
        leading=18,
        alignment=TA_LEFT,
        spaceAfter=10,
        spaceBefore=15
    ))
    
    styles.add(ParagraphStyle(
        name='ChineseCode',
        parent=styles['Code'],
        fontName='Courier',
        fontSize=9,
        leading=12,
        alignment=TA_LEFT,
        spaceAfter=10,
        spaceBefore=10
    ))
    
    # 读取 Markdown 文件
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # 解析 Markdown
    flowables = []
    
    # 手动解析内容
    lines = md_content.split('\n')
    current_section = []
    in_code_block = False
    code_lines = []
    in_table = False
    table_lines = []
    
    for line in lines:
        # 处理代码块
        if line.startswith('```'):
            if in_code_block:
                # 结束代码块
                in_code_block = False
                code_text = '\n'.join(code_lines)
                # 简化代码块处理
                for code_line in code_lines[:20]:  # 限制显示行数
                    p = Paragraph(f"<font name='Courier'>{code_line}</font>", styles['ChineseCode'])
                    flowables.append(p)
                if len(code_lines) > 20:
                    flowables.append(Paragraph(f"... ({len(code_lines)-20} more lines)", styles['Normal']))
                flowables.append(Spacer(1, 0.3*cm))
                code_lines = []
            else:
                # 开始代码块
                in_code_block = True
                if current_section:
                    text = ' '.join(current_section)
                    if text.strip():
                        flowables.append(Paragraph(text, styles['ChineseNormal']))
                    current_section = []
            continue
        
        if in_code_block:
            code_lines.append(line)
            continue
        
        # 处理表格
        if line.startswith('|') and '---' not in line:
            in_table = True
            table_lines.append(line)
            continue
        elif in_table and not line.startswith('|'):
            in_table = False
            # 解析表格
            if table_lines:
                table_data = []
                for tline in table_lines:
                    cells = [c.strip() for c in tline.split('|') if c.strip()]
                    if cells:
                        table_data.append(cells)
                
                if table_data:
                    # 创建表格
                    col_count = max(len(row) for row in table_data)
                    t = Table(table_data, colWidths=[3*cm]*min(col_count, 4))
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), font_name),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ]))
                    flowables.append(t)
                    flowables.append(Spacer(1, 0.5*cm))
            table_lines = []
        
        if in_table:
            if '---' not in line:
                table_lines.append(line)
            continue
        
        # 处理标题
        if line.startswith('# '):
            if current_section:
                text = ' '.join(current_section)
                if text.strip():
                    flowables.append(Paragraph(text, styles['ChineseNormal']))
                current_section = []
            title = line[2:].strip()
            flowables.append(Paragraph(title, styles['ChineseHeading1']))
            flowables.append(Spacer(1, 0.5*cm))
        
        elif line.startswith('## '):
            if current_section:
                text = ' '.join(current_section)
                if text.strip():
                    flowables.append(Paragraph(text, styles['ChineseNormal']))
                current_section = []
            title = line[3:].strip()
            flowables.append(Paragraph(title, styles['ChineseHeading2']))
            flowables.append(Spacer(1, 0.4*cm))
        
        elif line.startswith('### '):
            if current_section:
                text = ' '.join(current_section)
                if text.strip():
                    flowables.append(Paragraph(text, styles['ChineseNormal']))
                current_section = []
            title = line[4:].strip()
            flowables.append(Paragraph(title, styles['ChineseHeading3']))
            flowables.append(Spacer(1, 0.3*cm))
        
        elif line.startswith('- ') or line.startswith('* '):
            # 列表项
            item = line[2:].strip()
            if item:
                p = Paragraph(f"• {item}", styles['ChineseNormal'])
                flowables.append(p)
        
        elif line.strip():
            current_section.append(line.strip())
    
    # 添加剩余内容
    if current_section:
        text = ' '.join(current_section)
        if text.strip():
            flowables.append(Paragraph(text, styles['ChineseNormal']))
    
    # 构建 PDF
    doc.build(flowables)
    print(f"PDF 已生成：{pdf_file}")

if __name__ == '__main__':
    import sys
    if len(sys.argv) >= 3:
        md_file = sys.argv[1]
        pdf_file = sys.argv[2]
        create_pdf(md_file, pdf_file)
    else:
        print("用法：python md2pdf.py <input.md> <output.pdf>")

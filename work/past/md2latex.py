#!/usr/bin/env python3
"""
将 Markdown 转换为 LaTeX 并用 xelatex 编译为 PDF
支持中文
"""

import re
import os
import subprocess
import sys

def md_to_latex(md_content):
    """简单的 Markdown 转 LaTeX 转换"""
    
    # 处理代码块 - 使用 verbatim 环境
    def replace_code_block(match):
        code = match.group(2)
        # 转义 LaTeX 特殊字符
        code = code.replace('&', '\\&').replace('%', '\\%').replace('$', '\\$')
        code = code.replace('#', '\\#').replace('_', '\\_').replace('{', '\\{').replace('}', '\\}')
        return f'\\begin{{verbatim}}\n{code}\\end{{verbatim}}\n'
    
    content = re.sub(r'```(\w*)\n(.*?)```', replace_code_block, md_content, flags=re.DOTALL)
    
    # 处理行内代码
    content = re.sub(r'`([^`]+)`', r'\\texttt{\1}', content)
    
    # 处理粗体
    content = re.sub(r'\*\*([^*]+)\*\*', r'\\textbf{\1}', content)
    
    # 处理斜体
    content = re.sub(r'\*([^*]+)\*', r'\\textit{\1}', content)
    
    # 处理标题
    content = re.sub(r'^# (.+)$', r'\\section{\1}', content, flags=re.MULTILINE)
    content = re.sub(r'^## (.+)$', r'\\subsection{\1}', content, flags=re.MULTILINE)
    content = re.sub(r'^### (.+)$', r'\\subsubsection{\1}', content, flags=re.MULTILINE)
    content = re.sub(r'^#### (.+)$', r'\\paragraph{\1}', content, flags=re.MULTILINE)
    
    # 处理表格 (简单版本)
    # 这里简化处理，复杂表格需要更专业的解析
    
    # 处理列表
    content = re.sub(r'^[-*] (.+)$', r'\\item \1', content, flags=re.MULTILINE)
    
    # 处理图片
    content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'\\includegraphics[width=\\textwidth]{\2}', content)
    
    # 处理链接
    content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\\href{\2}{\1}', content)
    
    return content

def create_latex_doc(content, title="手语识别技术路线推荐报告"):
    """创建完整的 LaTeX 文档"""
    
    latex_template = f"""\\documentclass[a4paper,12pt]{{article}}
\\usepackage{{fontspec}}
\\setmainfont{{SimHei}}
\\usepackage{{geometry}}
\\usepackage{{graphicx}}
\\usepackage{{hyperref}}
\\usepackage{{longtable}}

\\geometry{{left=2.5cm, right=2.5cm, top=2.5cm, bottom=2.5cm}}

\\hypersetup{{
    colorlinks=true,
    linkcolor=blue,
    urlcolor=cyan,
}}

\\title{{\\textbf{{手语识别技术路线推荐报告}}}}
\\author{{自动生成}}
\\date{{\\today}}

\\begin{{document}}

\\maketitle

{content}

\\end{{document}}
"""
    return latex_template

def main():
    if len(sys.argv) < 2:
        print("用法：python md2latex.py <input.md> [output.pdf]")
        sys.exit(1)
    
    md_file = sys.argv[1]
    pdf_file = sys.argv[2] if len(sys.argv) > 2 else md_file.replace('.md', '.pdf')
    
    # 读取 Markdown
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    print(f"读取文件：{md_file}")
    
    # 转换为 LaTeX
    latex_content = md_to_latex(md_content)
    latex_doc = create_latex_doc(latex_content)
    
    # 写入临时 tex 文件
    tex_file = md_file.replace('.md', '.tex')
    with open(tex_file, 'w', encoding='utf-8') as f:
        f.write(latex_doc)
    
    print(f"生成 LaTeX 文件：{tex_file}")
    
    # 用 xelatex 编译
    print("正在用 xelatex 编译...")
    tex_dir = os.path.dirname(os.path.abspath(tex_file))
    
    try:
        # 编译两次以正确生成目录
        for i in range(2):
            result = subprocess.run(
                ['xelatex', '-interaction=nonstopmode', tex_file],
                cwd=tex_dir,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print(f"编译警告/错误:\n{result.stdout[-500:]}")
        
        # 移动 PDF 到目标位置
        src_pdf = tex_file.replace('.md', '.pdf').replace('.tex', '.pdf')
        if os.path.exists(src_pdf):
            os.rename(src_pdf, pdf_file)
            print(f"✓ PDF 生成成功：{pdf_file}")
        else:
            print("✗ 编译失败，未生成 PDF 文件")
            
    except Exception as e:
        print(f"✗ 编译失败：{e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

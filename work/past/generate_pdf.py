#!/usr/bin/env python3
"""
生成手语识别技术路线报告的 PDF 版本
使用 reportlab 直接生成，支持中文
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont  # 正确导入 TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
import os

# 使用中文字体（项目本地字体目录）
CHINESE_FONT = None
FONT_PATHS = [
    # 优先使用项目本地字体（无需 sudo 安装）
    '/home/wuyangcheng/signLanguage/work/fonts/SourceHanSans.otf',  # 思源黑体
    '/home/wuyangcheng/signLanguage/work/fonts/NotoSansCJK.ttc',
    # 其次是系统字体
    '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
    '/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc',
    '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc',
]

for font_path in FONT_PATHS:
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
            CHINESE_FONT = 'ChineseFont'
            print(f"✓ 找到中文字体：{font_path}")
            break
        except Exception as e:
            print(f"字体加载失败 {font_path}: {e}")
            continue

if not CHINESE_FONT:
    print("⚠ 未找到中文字体，PDF 中的中文可能显示异常")
    CHINESE_FONT = 'Helvetica'

def create_sign_language_report(output_pdf):
    """创建手语识别技术路线报告"""
    
    # 创建文档
    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2.5*cm,
        bottomMargin=2*cm,
        title="手语识别技术路线推荐报告"
    )
    
    # 构建内容
    story = []
    styles = getSampleStyleSheet()
    
    # 注册自定义样式
    styles.add(ParagraphStyle(
        name='ChineseTitle',
        parent=styles['Heading1'],
        fontName=CHINESE_FONT,
        fontSize=22,
        leading=28,
        alignment=TA_CENTER,
        spaceAfter=30,
        spaceBefore=30
    ))
    
    styles.add(ParagraphStyle(
        name='ChineseHeading1',
        parent=styles['Heading1'],
        fontName=CHINESE_FONT,
        fontSize=16,
        leading=22,
        alignment=TA_LEFT,
        spaceAfter=15,
        spaceBefore=25,
        textColor=colors.darkblue
    ))
    
    styles.add(ParagraphStyle(
        name='ChineseHeading2',
        parent=styles['Heading2'],
        fontName=CHINESE_FONT,
        fontSize=14,
        leading=20,
        alignment=TA_LEFT,
        spaceAfter=12,
        spaceBefore=20,
        textColor=colors.darkgreen
    ))
    
    styles.add(ParagraphStyle(
        name='ChineseHeading3',
        parent=styles['Heading3'],
        fontName=CHINESE_FONT,
        fontSize=12,
        leading=18,
        alignment=TA_LEFT,
        spaceAfter=10,
        spaceBefore=15
    ))
    
    styles.add(ParagraphStyle(
        name='ChineseNormal',
        parent=styles['Normal'],
        fontName=CHINESE_FONT,
        fontSize=11,
        leading=18,
        alignment=TA_JUSTIFY,
        spaceAfter=10
    ))
    
    styles.add(ParagraphStyle(
        name='ChineseCode',
        parent=styles['Code'],
        fontName='Courier',
        fontSize=9,
        leading=12,
        alignment=TA_LEFT,
        spaceAfter=8,
        spaceBefore=8,
        textColor=colors.darkred
    ))
    
    # ========== 封面 ==========
    story.append(Spacer(1, 3*cm))
    story.append(Paragraph("手语识别技术路线推荐报告", styles['ChineseTitle']))
    story.append(Paragraph("面向孤立词手语的特征提取与匹配系统", styles['ChineseHeading2']))
    story.append(Spacer(1, 2*cm))
    
    # 基本信息表格
    info_data = [
        ['生成日期', '2026-04-02'],
        ['目标场景', '孤立词手语识别，基于特征匹配的语义检索系统'],
        ['技术栈', 'MediaPipe Holistic + FAISS + Python'],
        ['适用对象', '手语识别系统开发者']
    ]
    info_table = Table(info_data, colWidths=[4*cm, 10*cm])
    info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(info_table)
    story.append(PageBreak())
    
    # ========== 摘要 ==========
    story.append(Paragraph("摘要", styles['ChineseHeading1']))
    abstract_text = """
    本报告针对用户提出的手语识别系统需求，推荐了一套完整的技术路线。系统核心思路是：
    <br/>1. 使用 MediaPipe Holistic 提取视频中的手势、肢体、面部特征
    <br/>2. 构建「手语语义 - 特征向量」键值对数据库
    <br/>3. 使用向量相似度搜索实现鲁棒匹配
    <br/><br/>
    推荐方案采用成熟开源技术，支持快速原型开发和后续扩展。
    """
    story.append(Paragraph(abstract_text, styles['ChineseNormal']))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("关键词：MediaPipe Holistic；特征提取；向量数据库；孤立词手语识别；相似度匹配", styles['ChineseNormal']))
    story.append(PageBreak())
    
    # ========== 目录 ==========
    story.append(Paragraph("目录", styles['ChineseHeading1']))
    toc_data = [
        ['1. 需求分析', '4'],
        ['2. 技术选型对比', '5'],
        ['3. 推荐架构设计', '7'],
        ['4. 实施步骤', '9'],
        ['5. 数据集推荐', '14'],
        ['6. 预期性能指标', '15'],
        ['7. 风险与应对', '16'],
        ['8. 总结与建议', '17']
    ]
    toc_table = Table(toc_data, colWidths=[12*cm, 2*cm])
    toc_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.lightgrey),
    ]))
    story.append(toc_table)
    story.append(PageBreak())
    
    # ========== 1. 需求分析 ==========
    story.append(Paragraph("1. 需求分析", styles['ChineseHeading1']))
    
    story.append(Paragraph("1.1 核心需求", styles['ChineseHeading2']))
    
    # 核心需求表格
    requirement_data = [
        ['需求', '说明', '技术映射'],
        ['特征提取', '从视频序列中提取手势、肢体、面部特征', '姿态估计 + 关键点检测'],
        ['数据库构建', '建立手语语义 - 行为特征的键值对', '向量数据库'],
        ['鲁棒匹配', '容忍一定程度的行为/视频偏差', '相似度搜索 + 阈值判定'],
        ['实时识别', '摄像头实时采集并识别', '低延迟推理'],
        ['未知语义检测', '识别已知或未知语义', '相似度阈值 + 未知类判定'],
        ['孤立词场景', '非连续语句，单个手语词', '简化时序建模']
    ]
    req_table = Table(requirement_data, colWidths=[2.5*cm, 5*cm, 5*cm])
    req_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), CHINESE_FONT),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(req_table)
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("1.2 技术挑战", styles['ChineseHeading2']))
    challenge_text = """
    1. 特征鲁棒性：不同人做同一手语动作存在差异
    <br/>2. 时序对齐：视频长度不同，需要时序归一化
    <br/>3. 多模态融合：手势、肢体、面部特征的权重分配
    <br/>4. 实时性：摄像头采集 + 特征提取 + 匹配需在 100ms 内完成
    """
    story.append(Paragraph(challenge_text, styles['ChineseNormal']))
    story.append(PageBreak())
    
    # ========== 2. 技术选型对比 ==========
    story.append(Paragraph("2. 技术选型对比", styles['ChineseHeading1']))
    
    story.append(Paragraph("2.1 姿态/关键点检测模型", styles['ChineseHeading2']))
    
    # 技术对比表格
    tech_data = [
        ['方案', 'MediaPipe Holistic', 'OpenPose', 'MoveNet', 'BlazePose'],
        ['开发商', 'Google', 'CMU', 'TensorFlow', 'Google'],
        ['检测内容', '手 + 身 + 脸', '全身 + 手', '全身', '全身'],
        ['手部关键点', '21 点/手', '21 点/手', '不支持', '21 点/手'],
        ['面部关键点', '468 点', '不支持', '不支持', '不支持'],
        ['身体关键点', '33 点', '18 点', '17 点', '33 点'],
        ['推理速度', '30-60 FPS', '5-10 FPS', '100+ FPS', '60+ FPS'],
        ['推荐度', '首选', '备选', '轻量级', '备选']
    ]
    tech_table = Table(tech_data, colWidths=[2*cm, 3.5*cm, 2.5*cm, 2.5*cm, 2.5*cm])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), CHINESE_FONT),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(tech_table)
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("推荐：MediaPipe Holistic", styles['ChineseNormal']))
    reason_text = """
    理由：唯一同时支持手、身、脸检测的开源方案；精度高，推理速度快（CPU 可达 30 FPS）；
    Python API 成熟，文档完善；支持实时视频流处理
    """
    story.append(Paragraph(reason_text, styles['ChineseNormal']))
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("2.2 向量数据库/相似度搜索", styles['ChineseHeading2']))
    
    # 向量数据库对比
    vector_data = [
        ['方案', 'FAISS', 'Milvus', 'Chroma', 'Pinecone'],
        ['类型', '库', '服务', '库', 'SaaS'],
        ['部署难度', '简单', '中等', '简单', '云服务'],
        ['支持度量', 'L2, IP, Cosine', '多种', 'Cosine, L2', '多种'],
        ['推荐度', '首选', '大规模', '轻量级', '云服务']
    ]
    vector_table = Table(vector_data, colWidths=[2*cm, 3*cm, 3*cm, 3*cm, 3*cm])
    vector_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), CHINESE_FONT),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightyellow),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    story.append(vector_table)
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("推荐：FAISS（Meta 开源，成熟稳定，支持 GPU 加速）", styles['ChineseNormal']))
    story.append(PageBreak())
    
    # ========== 3. 推荐架构设计 ==========
    story.append(Paragraph("3. 推荐架构设计", styles['ChineseHeading1']))
    
    story.append(Paragraph("3.1 系统架构", styles['ChineseHeading2']))
    arch_text = """
    输入层 → 特征提取层（MediaPipe Holistic） → 特征预处理 → 特征编码层 → 
    存储层（FAISS 向量数据库） → 匹配层（相似度搜索 + 阈值判定） → 输出层
    """
    story.append(Paragraph(arch_text, styles['ChineseNormal']))
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("3.2 特征向量设计", styles['ChineseHeading2']))
    feature_data = [
        ['特征', '维度', '说明', '权重'],
        ['左手关键点', '63 维', '21 点×3 坐标', '30%'],
        ['右手关键点', '63 维', '21 点×3 坐标', '30%'],
        ['身体关键点', '99 维', '33 点×3 坐标', '20%'],
        ['面部关键点', '~100 维', '降维处理', '20%'],
        ['总计', '~543 维/帧', 'PCA 降维', '-']
    ]
    feature_table = Table(feature_data, colWidths=[3*cm, 3*cm, 5*cm, 2*cm])
    feature_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), CHINESE_FONT),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(feature_table)
    story.append(PageBreak())
    
    # ========== 4. 实施步骤 ==========
    story.append(Paragraph("4. 实施步骤", styles['ChineseHeading1']))
    
    story.append(Paragraph("4.1 阶段 1：环境搭建（1-2 天）", styles['ChineseHeading2']))
    story.append(Paragraph("创建虚拟环境并安装依赖：", styles['ChineseNormal']))
    story.append(Paragraph("pip install mediapipe opencv-python numpy faiss-cpu scipy", styles['ChineseCode']))
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("4.2 阶段 2：特征提取模块（2-3 天）", styles['ChineseHeading2']))
    story.append(Paragraph("使用 MediaPipe Holistic 提取手势、肢体、面部特征，时序归一化处理。", styles['ChineseNormal']))
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("4.3 阶段 3：数据库构建（2-3 天）", styles['ChineseHeading2']))
    story.append(Paragraph("使用 FAISS 构建向量索引，支持余弦相似度搜索。", styles['ChineseNormal']))
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("4.4 阶段 4：实时识别（3-5 天）", styles['ChineseHeading2']))
    story.append(Paragraph("实现摄像头视频流处理，实时特征提取与匹配，可视化输出。", styles['ChineseNormal']))
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("4.5 阶段 5：优化与调优（持续）", styles['ChineseHeading2']))
    optimize_data = [
        ['优化方向', '方法', '预期提升'],
        ['特征降维', 'PCA / 自编码器', '减少存储，加速搜索'],
        ['时序建模', 'DTW 动态时间规整', '提升时序对齐鲁棒性'],
        ['度量学习', 'Triplet Loss', '提升类间区分度'],
        ['数据增强', '时空扰动', '提升泛化能力'],
        ['GPU 加速', 'FAISS GPU', '10-100x 搜索加速']
    ]
    optimize_table = Table(optimize_data, colWidths=[3*cm, 4*cm, 5*cm])
    optimize_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), CHINESE_FONT),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(optimize_table)
    story.append(PageBreak())
    
    # ========== 5. 数据集推荐 ==========
    story.append(Paragraph("5. 数据集推荐", styles['ChineseHeading1']))
    
    dataset_data = [
        ['数据集', '类型', '规模', '语言', '获取方式'],
        ['WLASL', '孤立词', '2000 词，3k 视频', 'ASL', '公开下载'],
        ['MS-ASL', '孤立词', '1k 词，25k 视频', 'ASL', '公开下载'],
        ['CSL-Daily', '连续', '100 小时，10k 句', 'CSL', '学术申请'],
        ['手语 200 词', '孤立词', '200 词', 'CSL', 'GitHub']
    ]
    dataset_table = Table(dataset_data, colWidths=[3*cm, 2*cm, 3.5*cm, 2*cm, 3.5*cm])
    dataset_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), CHINESE_FONT),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(dataset_table)
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("推荐：WLASL + 自建数据集（中文手语需自行录制）", styles['ChineseNormal']))
    story.append(PageBreak())
    
    # ========== 6. 预期性能指标 ==========
    story.append(Paragraph("6. 预期性能指标", styles['ChineseHeading1']))
    
    perf_data = [
        ['指标', '目标值', '说明'],
        ['识别准确率', '>85%', 'Top-1 准确率（已知类）'],
        ['未知类检测率', '>90%', '正确识别未知语义'],
        ['推理延迟', '<100ms', '单帧特征提取 + 搜索'],
        ['数据库规模', '1 万样本', '支持万级向量搜索'],
        ['鲁棒性', '±20% 动作偏差', '容忍动作幅度变化']
    ]
    perf_table = Table(perf_data, colWidths=[4*cm, 4*cm, 6*cm])
    perf_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), CHINESE_FONT),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightyellow),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(perf_table)
    story.append(PageBreak())
    
    # ========== 7. 风险与应对 ==========
    story.append(Paragraph("7. 风险与应对", styles['ChineseHeading1']))
    
    risk_data = [
        ['风险', '影响', '应对措施'],
        ['特征区分度不足', '相似手语混淆', '引入度量学习，训练编码器'],
        ['实时性不达标', '用户体验差', 'GPU 加速，特征降维'],
        ['数据量不足', '泛化能力差', '数据增强，迁移学习'],
        ['阈值难调', '误检/漏检', '自适应阈值，用户反馈']
    ]
    risk_table = Table(risk_data, colWidths=[4*cm, 4*cm, 6*cm])
    risk_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), CHINESE_FONT),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.pink),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(risk_table)
    story.append(PageBreak())
    
    # ========== 8. 总结与建议 ==========
    story.append(Paragraph("8. 总结与建议", styles['ChineseHeading1']))
    
    story.append(Paragraph("8.1 推荐技术栈", styles['ChineseHeading2']))
    stack_data = [
        ['组件', '推荐方案', '备选方案'],
        ['特征提取', 'MediaPipe Holistic', 'OpenPose + 面部检测'],
        ['向量数据库', 'FAISS (CPU)', 'Milvus, Chroma'],
        ['相似度度量', '余弦相似度', 'L2 距离'],
        ['开发语言', 'Python 3.8+', '-'],
        ['深度学习框架', 'PyTorch (可选)', 'TensorFlow']
    ]
    stack_table = Table(stack_data, colWidths=[3*cm, 5*cm, 5*cm])
    stack_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), CHINESE_FONT),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(stack_table)
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("8.2 实施建议", styles['ChineseHeading2']))
    suggestion_text = """
    1. 快速原型：先用 WLASL 验证流程可行性（1-2 周）
    <br/>2. 数据收集：并行录制目标场景中文手语（2-4 周）
    <br/>3. 迭代优化：根据测试结果调整特征和阈值（持续）
    <br/>4. 扩展连续：孤立词验证后扩展连续手语（后续）
    """
    story.append(Paragraph(suggestion_text, styles['ChineseNormal']))
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("8.3 下一步行动", styles['ChineseHeading2']))
    action_text = """
    1. 安装 MediaPipe，测试特征提取效果
    <br/>2. 下载 WLASL 数据集，构建验证环境
    <br/>3. 实现基础特征提取 + FAISS 搜索流程
    <br/>4. 评估基线性能，确定优化方向
    """
    story.append(Paragraph(action_text, styles['ChineseNormal']))
    story.append(Spacer(1, 1*cm))
    
    # ========== 页脚 ==========
    story.append(Paragraph("——— 报告结束 ———", styles['ChineseHeading2']))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("报告生成：2026-04-02 | 适用场景：孤立词手语识别系统开发 | 技术成熟度：生产就绪", 
                          ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER, textColor=colors.grey)))
    
    # 构建 PDF
    doc.build(story)
    print(f"✓ PDF 报告已生成：{output_pdf}")

if __name__ == '__main__':
    output_path = '/home/wuyangcheng/signLanguage/work/手语识别技术路线推荐_20260402.pdf'
    create_sign_language_report(output_path)

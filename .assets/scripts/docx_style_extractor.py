#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title DOCX 样式提取器
# @raycast.mode fullOutput

# Optional parameters:
# @raycast.icon 📄
# @raycast.packageName Document Tools
# @raycast.argument1 { "type": "text", "placeholder": "docx文件路径", "optional": true }

# Documentation:
# @raycast.description 从 Word 文档中提取所有样式定义，生成 JSON 配置文件
# @raycast.author tianli

"""
DOCX 样式提取器

功能：
1. 解析 docx 中的 styles.xml
2. 提取所有段落样式和字符样式
3. 生成人类可读的 JSON 配置
4. 可选：创建空白模板（仅保留样式）

使用：
    python docx_style_extractor.py <input.docx>
    python docx_style_extractor.py <input.docx> --output styles.json
    python docx_style_extractor.py <input.docx> --create-template template.docx
"""

import sys
import os
import json
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import OrderedDict

# 添加 _lib 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "_lib"))

try:
    from finder import get_finder_selection
except ImportError:
    def get_finder_selection():
        return []

# Word XML 命名空间
NAMESPACES = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'w14': 'http://schemas.microsoft.com/office/word/2010/wordml',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
}

# 注册命名空间（用于写入时保持前缀）
for prefix, uri in NAMESPACES.items():
    ET.register_namespace(prefix, uri)


def twip_to_pt(twip):
    """Twip 转 Point (1 pt = 20 twip)"""
    if twip is None:
        return None
    try:
        return round(int(twip) / 20, 1)
    except:
        return None


def twip_to_cm(twip):
    """Twip 转厘米 (1 cm = 567 twip)"""
    if twip is None:
        return None
    try:
        return round(int(twip) / 567, 2)
    except:
        return None


def half_pt_to_pt(half_pt):
    """半磅转磅 (Word 的 sz 属性是半磅)"""
    if half_pt is None:
        return None
    try:
        return round(int(half_pt) / 2, 1)
    except:
        return None


def parse_font(rpr_elem):
    """解析字体信息"""
    font_info = {}
    
    if rpr_elem is None:
        return font_info
    
    # 字体
    rfonts = rpr_elem.find('w:rFonts', NAMESPACES)
    if rfonts is not None:
        font_info['font_ascii'] = rfonts.get(f'{{{NAMESPACES["w"]}}}ascii')
        font_info['font_eastAsia'] = rfonts.get(f'{{{NAMESPACES["w"]}}}eastAsia')
        font_info['font_hAnsi'] = rfonts.get(f'{{{NAMESPACES["w"]}}}hAnsi')
    
    # 字号
    sz = rpr_elem.find('w:sz', NAMESPACES)
    if sz is not None:
        font_info['size_pt'] = half_pt_to_pt(sz.get(f'{{{NAMESPACES["w"]}}}val'))
    
    szCs = rpr_elem.find('w:szCs', NAMESPACES)
    if szCs is not None:
        font_info['size_cs_pt'] = half_pt_to_pt(szCs.get(f'{{{NAMESPACES["w"]}}}val'))
    
    # 加粗
    b = rpr_elem.find('w:b', NAMESPACES)
    if b is not None:
        val = b.get(f'{{{NAMESPACES["w"]}}}val')
        font_info['bold'] = val != '0' if val else True
    
    # 斜体
    i = rpr_elem.find('w:i', NAMESPACES)
    if i is not None:
        val = i.get(f'{{{NAMESPACES["w"]}}}val')
        font_info['italic'] = val != '0' if val else True
    
    # 颜色
    color = rpr_elem.find('w:color', NAMESPACES)
    if color is not None:
        font_info['color'] = color.get(f'{{{NAMESPACES["w"]}}}val')
    
    return {k: v for k, v in font_info.items() if v is not None}


def parse_paragraph_format(ppr_elem):
    """解析段落格式"""
    para_info = {}
    
    if ppr_elem is None:
        return para_info
    
    # 对齐方式
    jc = ppr_elem.find('w:jc', NAMESPACES)
    if jc is not None:
        align_map = {'left': '左对齐', 'center': '居中', 'right': '右对齐', 'both': '两端对齐'}
        val = jc.get(f'{{{NAMESPACES["w"]}}}val')
        para_info['alignment'] = align_map.get(val, val)
    
    # 缩进
    ind = ppr_elem.find('w:ind', NAMESPACES)
    if ind is not None:
        first_line = ind.get(f'{{{NAMESPACES["w"]}}}firstLine')
        first_line_chars = ind.get(f'{{{NAMESPACES["w"]}}}firstLineChars')
        left = ind.get(f'{{{NAMESPACES["w"]}}}left')
        
        if first_line:
            para_info['first_line_indent_cm'] = twip_to_cm(first_line)
        if first_line_chars:
            para_info['first_line_indent_chars'] = int(first_line_chars) / 100
        if left:
            para_info['left_indent_cm'] = twip_to_cm(left)
    
    # 行距
    spacing = ppr_elem.find('w:spacing', NAMESPACES)
    if spacing is not None:
        line = spacing.get(f'{{{NAMESPACES["w"]}}}line')
        line_rule = spacing.get(f'{{{NAMESPACES["w"]}}}lineRule')
        
        if line and line_rule == 'auto':
            # 倍数行距 (240 = 1倍)
            para_info['line_spacing'] = round(int(line) / 240, 2)
        elif line:
            para_info['line_spacing_pt'] = twip_to_pt(line)
        
        before = spacing.get(f'{{{NAMESPACES["w"]}}}before')
        after = spacing.get(f'{{{NAMESPACES["w"]}}}after')
        if before:
            para_info['space_before_pt'] = twip_to_pt(before)
        if after:
            para_info['space_after_pt'] = twip_to_pt(after)
    
    # 大纲级别
    outline_lvl = ppr_elem.find('w:outlineLvl', NAMESPACES)
    if outline_lvl is not None:
        para_info['outline_level'] = int(outline_lvl.get(f'{{{NAMESPACES["w"]}}}val')) + 1
    
    return {k: v for k, v in para_info.items() if v is not None}


def extract_styles_from_xml(styles_xml_content):
    """从 styles.xml 内容提取样式"""
    root = ET.fromstring(styles_xml_content)
    
    styles = {
        'paragraph_styles': OrderedDict(),
        'character_styles': OrderedDict(),
        'table_styles': OrderedDict(),
    }
    
    # 默认样式
    doc_defaults = root.find('w:docDefaults', NAMESPACES)
    if doc_defaults:
        rpr_default = doc_defaults.find('.//w:rPr', NAMESPACES)
        styles['default_font'] = parse_font(rpr_default)
    
    # 遍历所有样式
    for style in root.findall('w:style', NAMESPACES):
        style_type = style.get(f'{{{NAMESPACES["w"]}}}type')
        style_id = style.get(f'{{{NAMESPACES["w"]}}}styleId')
        
        # 获取样式名称
        name_elem = style.find('w:name', NAMESPACES)
        style_name = name_elem.get(f'{{{NAMESPACES["w"]}}}val') if name_elem is not None else style_id
        
        # 获取基础样式
        based_on = style.find('w:basedOn', NAMESPACES)
        based_on_id = based_on.get(f'{{{NAMESPACES["w"]}}}val') if based_on is not None else None
        
        # 构建样式信息
        style_info = OrderedDict()
        style_info['id'] = style_id
        style_info['name'] = style_name
        if based_on_id:
            style_info['based_on'] = based_on_id
        
        # 段落属性
        ppr = style.find('w:pPr', NAMESPACES)
        para_format = parse_paragraph_format(ppr)
        if para_format:
            style_info['paragraph'] = para_format
        
        # 字符属性
        rpr = style.find('w:rPr', NAMESPACES)
        font_format = parse_font(rpr)
        if font_format:
            style_info['font'] = font_format
        
        # 根据类型分类
        if style_type == 'paragraph':
            styles['paragraph_styles'][style_id] = style_info
        elif style_type == 'character':
            styles['character_styles'][style_id] = style_info
        elif style_type == 'table':
            styles['table_styles'][style_id] = style_info
    
    return styles


def extract_styles_from_docx(docx_path):
    """从 docx 文件提取样式"""
    with zipfile.ZipFile(docx_path, 'r') as zf:
        # 读取 styles.xml
        try:
            styles_content = zf.read('word/styles.xml')
            styles = extract_styles_from_xml(styles_content)
        except KeyError:
            print("❌ 错误：找不到 word/styles.xml")
            return None
        
        # 读取 numbering.xml（如果存在）
        try:
            numbering_content = zf.read('word/numbering.xml')
            styles['has_numbering'] = True
        except KeyError:
            styles['has_numbering'] = False
    
    return styles


def extract_styles_from_folder(folder_path):
    """从解构的 docx 文件夹提取样式"""
    styles_path = os.path.join(folder_path, 'word', 'styles.xml')
    
    if not os.path.exists(styles_path):
        print(f"❌ 错误：找不到 {styles_path}")
        return None
    
    with open(styles_path, 'rb') as f:
        styles_content = f.read()
    
    styles = extract_styles_from_xml(styles_content)
    
    # 检查 numbering.xml
    numbering_path = os.path.join(folder_path, 'word', 'numbering.xml')
    styles['has_numbering'] = os.path.exists(numbering_path)
    
    return styles


def create_template_from_folder(folder_path, output_path):
    """从解构的文件夹创建空白模板"""
    import shutil
    import tempfile
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        # 复制所有文件
        for item in os.listdir(folder_path):
            if item.startswith('.'):
                continue  # 跳过隐藏文件
            src = os.path.join(folder_path, item)
            dst = os.path.join(tmpdir, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns('.*'))
            else:
                shutil.copy2(src, dst)
        
        # 清空 document.xml 中的内容，保留结构
        doc_path = os.path.join(tmpdir, 'word', 'document.xml')
        if os.path.exists(doc_path):
            with open(doc_path, 'rb') as f:
                content = f.read()
            
            # 解析并清空 body
            root = ET.fromstring(content)
            body = root.find('.//w:body', NAMESPACES)
            if body is not None:
                # 保留 sectPr（节属性）- 通常在最后
                sect_pr = None
                for child in body:
                    tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                    if tag == 'sectPr':
                        sect_pr = child
                        break
                
                # 清空所有元素
                for child in list(body):
                    body.remove(child)
                
                # 添加一个空段落（确保文档有效）
                p = ET.SubElement(body, f'{{{NAMESPACES["w"]}}}p')
                pPr = ET.SubElement(p, f'{{{NAMESPACES["w"]}}}pPr')
                pStyle = ET.SubElement(pPr, f'{{{NAMESPACES["w"]}}}pStyle')
                pStyle.set(f'{{{NAMESPACES["w"]}}}val', 'ZDWP正文')
                
                # 恢复节属性（必须在最后）
                if sect_pr is not None:
                    body.append(sect_pr)
                else:
                    # 如果没有找到节属性，创建一个基本的
                    sect_pr = ET.SubElement(body, f'{{{NAMESPACES["w"]}}}sectPr')
                    pgSz = ET.SubElement(sect_pr, f'{{{NAMESPACES["w"]}}}pgSz')
                    pgSz.set(f'{{{NAMESPACES["w"]}}}w', '11906')  # A4 宽度
                    pgSz.set(f'{{{NAMESPACES["w"]}}}h', '16838')  # A4 高度
                    pgMar = ET.SubElement(sect_pr, f'{{{NAMESPACES["w"]}}}pgMar')
                    pgMar.set(f'{{{NAMESPACES["w"]}}}top', '1440')
                    pgMar.set(f'{{{NAMESPACES["w"]}}}right', '1800')
                    pgMar.set(f'{{{NAMESPACES["w"]}}}bottom', '1440')
                    pgMar.set(f'{{{NAMESPACES["w"]}}}left', '1800')
            
            # 写回
            tree = ET.ElementTree(root)
            with open(doc_path, 'wb') as f:
                tree.write(f, encoding='UTF-8', xml_declaration=True)
        
        # 打包为 docx
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root_dir, dirs, files in os.walk(tmpdir):
                # 跳过隐藏目录
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                for file in files:
                    if file.startswith('.'):
                        continue
                    file_path = os.path.join(root_dir, file)
                    arcname = os.path.relpath(file_path, tmpdir)
                    zf.write(file_path, arcname)
    
    print(f"✅ 模板已创建: {output_path}")


def print_style_summary(styles):
    """打印样式摘要"""
    print("\n" + "=" * 60)
    print("📄 DOCX 样式提取结果")
    print("=" * 60)
    
    # 统计
    para_count = len(styles.get('paragraph_styles', {}))
    char_count = len(styles.get('character_styles', {}))
    table_count = len(styles.get('table_styles', {}))
    
    print(f"\n📊 样式统计:")
    print(f"   段落样式: {para_count} 个")
    print(f"   字符样式: {char_count} 个")
    print(f"   表格样式: {table_count} 个")
    print(f"   编号定义: {'✓' if styles.get('has_numbering') else '✗'}")
    
    # 默认字体
    if 'default_font' in styles:
        print(f"\n📝 默认字体:")
        for k, v in styles['default_font'].items():
            print(f"   {k}: {v}")
    
    # 重要段落样式
    print(f"\n📌 重要段落样式:")
    important_styles = []
    for style_id, style_info in styles.get('paragraph_styles', {}).items():
        name = style_info.get('name', style_id)
        # 筛选重要样式
        if any(kw in name.lower() for kw in ['heading', '标题', 'zdwp', 'normal', '正文', '表']):
            important_styles.append(style_info)
    
    for style in important_styles[:15]:  # 最多显示15个
        name = style.get('name', style.get('id'))
        font = style.get('font', {})
        para = style.get('paragraph', {})
        
        details = []
        if font.get('font_eastAsia'):
            details.append(f"中文:{font['font_eastAsia']}")
        if font.get('size_pt'):
            details.append(f"{font['size_pt']}pt")
        if font.get('bold'):
            details.append("加粗")
        if para.get('outline_level'):
            details.append(f"大纲{para['outline_level']}级")
        if para.get('first_line_indent_cm'):
            details.append(f"首行{para['first_line_indent_cm']}cm")
        if para.get('line_spacing'):
            details.append(f"{para['line_spacing']}倍行距")
        
        detail_str = ', '.join(details) if details else '(默认)'
        print(f"   • {name}: {detail_str}")
    
    print("\n" + "=" * 60)


def main():
    # 获取输入路径
    input_path = None
    output_json = None
    create_template = None
    
    # 解析参数
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '--output' and i + 1 < len(args):
            output_json = args[i + 1]
            i += 2
        elif args[i] == '--create-template' and i + 1 < len(args):
            create_template = args[i + 1]
            i += 2
        elif not args[i].startswith('--'):
            input_path = args[i]
            i += 1
        else:
            i += 1
    
    # 如果没有输入，尝试从 Finder 获取
    if not input_path:
        selections = get_finder_selection()
        if selections:
            input_path = selections[0]
    
    if not input_path:
        print("❌ 用法: python docx_style_extractor.py <docx文件或解构文件夹>")
        print("        python docx_style_extractor.py <input> --output styles.json")
        print("        python docx_style_extractor.py <input> --create-template template.docx")
        sys.exit(1)
    
    input_path = os.path.expanduser(input_path)
    
    if not os.path.exists(input_path):
        print(f"❌ 错误：路径不存在 {input_path}")
        sys.exit(1)
    
    # 判断是文件还是文件夹
    if os.path.isdir(input_path):
        print(f"📂 分析解构文件夹: {input_path}")
        styles = extract_styles_from_folder(input_path)
        
        # 创建模板
        if create_template:
            create_template_from_folder(input_path, create_template)
    else:
        print(f"📄 分析 DOCX 文件: {input_path}")
        styles = extract_styles_from_docx(input_path)
    
    if styles is None:
        sys.exit(1)
    
    # 打印摘要
    print_style_summary(styles)
    
    # 输出 JSON
    if output_json is None:
        # 默认输出路径
        base_name = os.path.splitext(os.path.basename(input_path.rstrip('/')))[0]
        output_json = os.path.join(os.path.dirname(input_path), f"{base_name}_styles.json")
    
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(styles, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 样式配置已保存: {output_json}")
    
    # Markdown 映射建议
    print("\n" + "=" * 60)
    print("📋 Markdown → Word 样式映射建议")
    print("=" * 60)
    
    # 自动检测映射
    para_styles = styles.get('paragraph_styles', {})
    
    mappings = []
    
    # 标题映射
    for i in range(1, 5):
        for style_id, style_info in para_styles.items():
            outline = style_info.get('paragraph', {}).get('outline_level')
            if outline == i:
                mappings.append(f"{'#' * i} 标题{i}  →  {style_info.get('name', style_id)}")
                break
    
    # 正文映射
    for style_id, style_info in para_styles.items():
        name = style_info.get('name', '')
        if 'ZDWP正文' in name or (name == 'Normal' and 'ZDWP' not in ''.join(para_styles.keys())):
            mappings.append(f"普通段落    →  {name}")
            break
    
    for m in mappings:
        print(f"   {m}")
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    main()


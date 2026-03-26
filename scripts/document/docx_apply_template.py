#!/usr/bin/env python3
"""
docx_apply_template.py - 给普通 docx 套上模板样式

功能：
  从模板 docx 提取标题/正文/表格样式，注入到目标 docx 中。
  内容不变，样式替换。

用法：
  # Raycast 调用：Finder 选中 .docx 文件
  python docx_apply_template.py

  # 命令行
  python docx_apply_template.py input.docx
  python docx_apply_template.py input.docx -t template.docx -o output.docx
"""

import argparse
import os
import subprocess
import sys
import tempfile
import zipfile
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

try:
    from lxml import etree
except ImportError:
    print("❌ 需要安装 lxml: pip install lxml")
    sys.exit(1)

from docx_xml import NSMAP

# 复用 md_docx_template 的样式提取
from md_docx_template import DEFAULT_TEMPLATE, extract_styles_xml

# 放在 document/ 同级，但导入需要处理路径
sys.path.insert(0, str(Path(__file__).parent))


def apply_styles_to_docx(docx_path, styles_xml_path, output_path):
    """把模板样式注入到已有 docx 中"""

    # 读取提取的样式
    with open(styles_xml_path, "rb") as f:
        new_styles = etree.parse(f).getroot()

    with tempfile.TemporaryDirectory() as tmpdir:
        # 解压目标 docx
        with zipfile.ZipFile(docx_path, "r") as zf:
            zf.extractall(tmpdir)

        # 读取原 styles.xml
        orig_styles_path = os.path.join(tmpdir, "word", "styles.xml")
        with open(orig_styles_path, "rb") as f:
            orig_root = etree.parse(f).getroot()

        # 收集新样式的 ID
        new_style_ids = set()
        for style in new_styles.findall(".//w:style", NSMAP):
            style_id = style.get(f"{{{NSMAP['w']}}}styleId")
            new_style_ids.add(style_id)

        # 删除原文档中同名样式
        for style in orig_root.findall(".//w:style", NSMAP):
            style_id = style.get(f"{{{NSMAP['w']}}}styleId")
            if style_id in new_style_ids:
                orig_root.remove(style)

        # 添加新样式
        for style in new_styles.findall(".//w:style", NSMAP):
            orig_root.append(deepcopy(style))

        # 更新 docDefaults
        new_defaults = new_styles.find(".//w:docDefaults", NSMAP)
        if new_defaults is not None:
            old_defaults = orig_root.find(".//w:docDefaults", NSMAP)
            if old_defaults is not None:
                orig_root.remove(old_defaults)
            orig_root.insert(0, deepcopy(new_defaults))

        # 写回 styles.xml
        tree = etree.ElementTree(orig_root)
        tree.write(orig_styles_path, encoding="UTF-8", xml_declaration=True)

        # 重新打包
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root_dir, _dirs, files in os.walk(tmpdir):
                for file in files:
                    file_path = os.path.join(root_dir, file)
                    arcname = os.path.relpath(file_path, tmpdir)
                    zf.write(file_path, arcname)

    print(f"✅ 输出: {output_path}")
    return output_path


def get_finder_selection():
    """获取 Finder 选中的文件"""
    script = """
    tell application "Finder"
        set sel to selection
        if (count of sel) > 0 then
            return POSIX path of (item 1 of sel as alias)
        end if
    end tell
    """
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description="给普通 docx 套上模板样式")
    parser.add_argument("input", nargs="?", help="目标 docx 文件")
    parser.add_argument("-t", "--template", help="模板 docx 文件")
    parser.add_argument("-o", "--output", help="输出文件")

    args = parser.parse_args()

    # 无参数时从 Finder 获取选中的 .docx 文件
    if not args.input:
        finder_file = get_finder_selection()
        if finder_file and finder_file.endswith(".docx"):
            args.input = finder_file
            print(f"📄 从 Finder 获取: {os.path.basename(finder_file)}")
        else:
            print("❌ 请在 Finder 中选择一个 .docx 文件")
            sys.exit(1)

    if not os.path.exists(args.input):
        print(f"❌ 文件不存在: {args.input}")
        sys.exit(1)

    # 模板
    template = args.template or DEFAULT_TEMPLATE
    if not os.path.exists(template):
        print(f"❌ 模板不存在: {template}")
        print("   请指定模板: -t template.docx")
        sys.exit(1)

    # 输出路径
    if args.output:
        output_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        output_path = f"{base}_styled{ext}"

    # 提取模板样式 → 注入目标 docx
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"📋 模板: {os.path.basename(template)}")
        styles_path, config = extract_styles_xml(template, tmpdir)
        apply_styles_to_docx(args.input, styles_path, output_path)


if __name__ == "__main__":
    main()

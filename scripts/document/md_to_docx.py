#!/usr/bin/env python3
"""
md_to_docx.py - Markdown 转 Docx（Pandoc 版）

用法：
  # Finder 选中 .md 文件后 Raycast 调用
  python md_to_docx.py

  # 命令行
  python md_to_docx.py input.md
  python md_to_docx.py input.md -o output.docx
  python md_to_docx.py input.md -t template.docx
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

# 默认模板路径
DEFAULT_TEMPLATE = "/Users/tianli/Downloads/归档/其他文档/template.docx"


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


def convert(md_path, output_path=None, template_path=None):
    """用 Pandoc 将 Markdown 转换为 Docx"""

    md_path = Path(md_path).resolve()
    if not md_path.exists():
        print(f"❌ 文件不存在: {md_path}")
        sys.exit(1)

    if output_path is None:
        output_path = md_path.with_suffix(".docx")
    else:
        output_path = Path(output_path).resolve()

    # 构建 Pandoc 命令
    cmd = [
        "pandoc",
        str(md_path),
        "-o",
        str(output_path),
        "--from",
        "markdown",
        "--to",
        "docx",
    ]

    # 使用模板（reference-doc）
    tpl = template_path or DEFAULT_TEMPLATE
    if tpl and Path(tpl).exists():
        cmd += ["--reference-doc", str(tpl)]
        print(f"📋 模板: {Path(tpl).name}")

    print(f"📖 输入: {md_path.name}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Pandoc 转换失败:\n{result.stderr}")
        sys.exit(1)

    print(f"✅ 输出: {output_path}")
    return str(output_path)


def main():
    parser = argparse.ArgumentParser(
        description="Markdown 转 Docx（Pandoc 版）",
    )
    parser.add_argument("input", nargs="?", help="Markdown 文件路径")
    parser.add_argument("-o", "--output", help="输出 docx 文件路径")
    parser.add_argument("-t", "--template", help="参考模板 docx（Pandoc --reference-doc）")

    args = parser.parse_args()

    # 无参数时从 Finder 获取
    md_path = args.input
    if not md_path:
        finder_file = get_finder_selection()
        if finder_file and finder_file.endswith(".md"):
            md_path = finder_file
            print(f"📄 从 Finder 获取: {os.path.basename(finder_file)}")
        else:
            print("❌ 请在 Finder 中选择一个 .md 文件")
            sys.exit(1)

    convert(md_path, args.output, args.template)


if __name__ == "__main__":
    main()

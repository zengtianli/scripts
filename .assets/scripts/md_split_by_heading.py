#!/usr/bin/env python3
# @raycast.schemaVersion 1
# @raycast.title md-split
# @raycast.mode fullOutput
# @raycast.icon ✂️
# @raycast.packageName Scripts
# @raycast.description Split markdown by heading level 1
"""
按一级标题拆分 Markdown 文件
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))
from display import show_success, show_info
from file_ops import (fatal_error, show_version_info, show_help_header, show_help_footer,
                      validate_input_file, check_file_extension)
from finder import get_input_files

SCRIPT_VERSION = "1.0.0"
SCRIPT_AUTHOR = "tianli"
SCRIPT_UPDATED = "2025-01-06"


def show_version():
    """显示版本信息"""
    show_version_info(SCRIPT_VERSION, SCRIPT_AUTHOR, SCRIPT_UPDATED)


def show_help():
    """显示帮助信息"""
    show_help_header(sys.argv[0], "按一级标题拆分Markdown文件")
    print("    input.md    要拆分的Markdown文件")
    print("\n输出到 input_split/ 目录")
    show_help_footer()


def slugify(title: str) -> str:
    """将标题转换为文件名友好格式"""
    # 移除 # 和数字前缀，如 "# 1. Introduction" -> "Introduction"
    title = re.sub(r'^#*\s*\d*\.?\s*', '', title)
    # 转小写，空格变下划线
    slug = title.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)  # 移除特殊字符
    slug = re.sub(r'[\s-]+', '_', slug)   # 空格/连字符变下划线
    return slug[:50]  # 限制长度


def split_markdown(input_path: Path) -> list[tuple[str, str]]:
    """
    拆分 Markdown 文件
    返回: [(filename, content), ...]
    """
    content = input_path.read_text(encoding='utf-8')
    
    # 按一级标题拆分（# 开头，不是 ## 或更多）
    pattern = r'^(# .+)$'
    parts = re.split(pattern, content, flags=re.MULTILINE)
    
    results = []
    idx = 0
    
    # 第一部分：# 之前的内容（标题、摘要等）
    if parts[0].strip():
        results.append((f"{idx:02d}_title.md", parts[0].strip()))
        idx += 1
    
    # 后续部分：成对出现（标题, 内容）
    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            heading = parts[i]
            body = parts[i + 1] if i + 1 < len(parts) else ""
            
            # 生成文件名
            slug = slugify(heading)
            filename = f"{idx:02d}_{slug}.md"
            
            # 合并标题和内容
            full_content = f"{heading}\n{body}".strip()
            results.append((filename, full_content))
            idx += 1
    
    return results


def main():
    """主函数"""
    # 无参数时从 Finder 获取选中的文件
    if len(sys.argv) == 1:
        files = get_input_files([], expected_ext='md')
        if files:
            sys.argv.extend(files[:1])  # 只取第一个文件
    
    # 处理帮助和版本参数
    if any(arg in ("-h", "--help") for arg in sys.argv):
        show_help()
        sys.exit(0)
    if "--version" in sys.argv:
        show_version()
        sys.exit(0)
    
    # 获取参数
    args = [arg for arg in sys.argv[1:] if not arg.startswith('-')]
    
    if len(args) < 1:
        fatal_error("请提供一个 Markdown 文件，或在 Finder 中选择文件后运行")
    
    input_path = Path(args[0]).resolve()
    
    # 验证文件
    if not validate_input_file(input_path):
        sys.exit(1)
    if not check_file_extension(input_path, 'md'):
        fatal_error(f"不是 Markdown 文件: {input_path.name}")
    
    # 输出目录
    output_dir = input_path.parent / f"{input_path.stem}_split"
    output_dir.mkdir(exist_ok=True)
    
    # 拆分
    parts = split_markdown(input_path)
    
    show_info(f"输出目录: {output_dir}")
    show_info(f"拆分为 {len(parts)} 个文件:")
    
    for filename, content in parts:
        output_path = output_dir / filename
        output_path.write_text(content, encoding='utf-8')
        lines = content.count('\n') + 1
        print(f"  ✅ {filename} ({lines} 行)")
    
    show_success("拆分完成!")


if __name__ == "__main__":
    main()


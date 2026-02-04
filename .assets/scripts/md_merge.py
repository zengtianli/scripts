#!/Users/tianli/miniforge3/bin/python3
# @raycast.schemaVersion 1
# @raycast.title md-merge
# @raycast.mode fullOutput
# @raycast.icon 📝
# @raycast.packageName Scripts
# @raycast.description Merge markdown files
"""
合并多个 Markdown 文件为一个文件
"""

import sys
from pathlib import Path

from common_utils import (
    show_success, show_error, show_info, show_warning, fatal_error, 
    ProgressTracker, show_version_info, show_help_header, show_help_footer,
    validate_input_file, check_file_extension, get_input_files
)

SCRIPT_VERSION = "1.0.0"
SCRIPT_AUTHOR = "tianli"
SCRIPT_UPDATED = "2025-10-31"

def show_version():
    """显示版本信息"""
    show_version_info(SCRIPT_VERSION, SCRIPT_AUTHOR, SCRIPT_UPDATED)

def show_help():
    """显示帮助信息"""
    show_help_header(sys.argv[0], "合并多个Markdown文件")
    print("    file1.md file2.md ...  要合并的Markdown文件")
    print("    [output.md]            输出文件名 (默认为 'merged.md')")
    show_help_footer()

def merge_md_files(md_files: list, output_file: Path):
    """合并多个 Markdown 文件"""
    tracker = ProgressTracker()
    
    # 按文件名排序
    md_files = sorted(md_files)
    
    show_info(f"准备合并 {len(md_files)} 个 Markdown 文件")
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f_out:
            for i, md_file in enumerate(md_files, 1):
                md_path = Path(md_file)
                
                # 验证文件
                if not validate_input_file(md_path):
                    tracker.add_skip()
                    continue
                
                if not check_file_extension(md_path, 'md'):
                    show_warning(f"跳过非 Markdown 文件: {md_path.name}")
                    tracker.add_skip()
                    continue
                
                show_info(f"处理 ({i}/{len(md_files)}): {md_path.name}")
                
                # 读取并写入内容
                with open(md_path, 'r', encoding='utf-8') as f_in:
                    content = f_in.read()
                    f_out.write(content)
                    # 文件之间添加分隔
                    if i < len(md_files):
                        f_out.write('\n\n')
                
                tracker.add_success()
        
        show_success(f"合并完成，已保存为: {output_file.name}")
        tracker.show_summary("文件合并")
        
    except Exception as e:
        fatal_error(f"合并失败: {e}")

def main():
    """主函数"""
    # 无参数时从 Finder 获取选中的文件
    if len(sys.argv) == 1:
        files = get_input_files([], expected_ext='md')
        if files:
            sys.argv.extend(files)
    
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
        fatal_error("请提供至少一个 Markdown 文件，或在 Finder 中选择文件后运行")
    
    # 判断最后一个参数是否为输出文件
    if args[-1].endswith('.md') and len(args) > 1 and not Path(args[-1]).exists():
        output_file = Path(args[-1])
        md_files = args[:-1]
    else:
        # 默认输出到第一个文件的同级目录
        first_file = Path(args[0]).resolve()
        output_file = first_file.parent / "merged.md"
        md_files = args
    
    # 执行合并
    merge_md_files(md_files, output_file)

if __name__ == "__main__":
    main()


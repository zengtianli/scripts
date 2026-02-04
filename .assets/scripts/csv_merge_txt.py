#!/Users/tianli/miniforge3/bin/python3
# @raycast.schemaVersion 1
# @raycast.title csv-merge-txt
# @raycast.mode fullOutput
# @raycast.icon 📊
# @raycast.packageName Scripts
# @raycast.description Merge TXT files
"""
将目录中的所有 .txt 文件按列合并到一个 CSV 文件中。
文件名中的数字用于排序。
"""

import sys
import csv
import re
from pathlib import Path

from common_utils import (
    show_success, show_error, show_info, fatal_error, ProgressTracker,
    show_version_info, show_help_header, show_help_footer, get_finder_current_dir
)

SCRIPT_VERSION = "1.0.0"
SCRIPT_AUTHOR = "tianli"
SCRIPT_UPDATED = "2024-07-26"

def show_version():
    """显示版本信息"""
    show_version_info(SCRIPT_VERSION, SCRIPT_AUTHOR, SCRIPT_UPDATED)

def show_help():
    """显示帮助信息"""
    show_help_header(sys.argv[0], "合并目录中所有.txt文件为单个CSV")
    print("    [target_dir]     要处理的目录 (默认为当前目录)")
    print("    [output_file.csv] 输出的CSV文件名 (默认为 'merged.csv')")
    show_help_footer()

def merge_txt_to_csv(target_dir: Path, output_file: Path, tracker: ProgressTracker):
    """
    将目录中的所有 .txt 文件按列合并到一个 CSV 文件中。
    """
    txt_files = sorted(target_dir.glob('*.txt'))
    
    if not txt_files:
        show_error(f"在目录 '{target_dir}' 中未找到 .txt 文件。")
        return

    def extract_number(filename: Path):
        match = re.match(r'(\d+)(_\d+)?\.txt', filename.name)
        if match:
            number = int(match.group(1))
            suffix = match.group(2) or ''
            return number, suffix
        return float('inf'), '' # 将没有数字的文件排在最后

    txt_files.sort(key=extract_number)
    
    show_info(f"找到 {len(txt_files)} 个 .txt 文件进行合并。")

    # 以最长文件的行数为基准
    max_lines = 0
    for file in txt_files:
        with open(file, 'r', encoding='utf-8') as f:
            line_count = sum(1 for _ in f)
            if line_count > max_lines:
                max_lines = line_count
    
    if max_lines == 0:
        show_warning("所有 .txt 文件都为空，将生成一个空的CSV文件。")
        output_file.touch()
        show_success(f"操作完成，已生成空的CSV文件: {output_file.name}")
        return

    lines = [[] for _ in range(max_lines)]

    for file in txt_files:
        show_info(f"正在处理: {file.name}")
        tracker.add_success()
        with open(file, 'r', encoding='utf-8') as f:
            file_lines = [line.strip() for line in f.readlines()]
            for i in range(max_lines):
                lines[i].append(file_lines[i] if i < len(file_lines) else '')

    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(lines)
        show_success(f"合并完成。结果已保存为 {output_file.name} 文件。")
    except IOError as e:
        fatal_error(f"写入CSV文件失败: {e}")

def main():
    """主函数"""
    # 无参数时从 Finder 获取当前目录
    if len(sys.argv) == 1:
        finder_dir = get_finder_current_dir()
        if finder_dir:
            sys.argv.append(finder_dir)
    
    target_dir_str = "."
    output_file_str = "merged.csv"

    args = [arg for arg in sys.argv[1:] if not arg.startswith('-')]
    
    if any(arg in ("-h", "--help") for arg in sys.argv):
        show_help()
        sys.exit(0)
    if "--version" in sys.argv:
        show_version()
        sys.exit(0)
        
    if len(args) > 0:
        target_dir_str = args[0]
    if len(args) > 1:
        output_file_str = args[1]

    target_dir = Path(target_dir_str)
    output_file = Path(output_file_str)

    if not target_dir.is_dir():
        fatal_error(f"目标不是一个有效的目录: {target_dir}")

    if output_file.suffix.lower() != '.csv':
        output_file = output_file.with_suffix('.csv')

    tracker = ProgressTracker()
    merge_txt_to_csv(target_dir, output_file, tracker)
    tracker.show_summary("TXT文件合并")

if __name__ == "__main__":
    main() 
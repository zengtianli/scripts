#!/Users/tianli/miniforge3/bin/python3
# @raycast.schemaVersion 1
# @raycast.title csv-format-circles
# @raycast.mode fullOutput
# @raycast.icon 📊
# @raycast.packageName Scripts
# @raycast.description Format circles in CSV
"""
将CSV文件中指定列的数字 (1-10) 转换为带圈字符 (①-⑩)。
"""

import sys
import csv
import re
from pathlib import Path
import argparse

from common_utils import (
    show_success, show_error, show_info, fatal_error, ProgressTracker,
    validate_input_file, get_input_files
)

SCRIPT_VERSION = "1.0.0"
SCRIPT_AUTHOR = "tianli"
SCRIPT_UPDATED = "2024-07-26"

def convert_to_circle_number(text: str) -> str:
    """将数字 1-10 转换为对应的圆圈数字"""
    circle_numbers = {
        '1': '①', '2': '②', '3': '③', '4': '④', '5': '⑤',
        '6': '⑥', '7': '⑦', '8': '⑧', '9': '⑨', '10': '⑩'
    }
    # 替换文本中的数字
    for number, circle_number in circle_numbers.items():
        text = text.replace(number, circle_number)
    
    # 只保留带圈字符
    circled_only = ''.join(re.findall(r'[①-⑩]', text))
    return circled_only if circled_only else text

def process_csv_file(input_file: Path, columns: list[int], tracker: ProgressTracker):
    """处理单个CSV文件"""
    if not validate_input_file(input_file):
        tracker.add_failure()
        return

    show_info(f"正在处理文件: {input_file.name}")
    output_file = input_file.parent / f"{input_file.stem}_circled.csv"
    
    try:
        with open(input_file, 'r', newline='', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            data = list(reader)

        for row in data:
            for col_index in columns:
                if col_index < len(row):
                    row[col_index] = convert_to_circle_number(row[col_index])

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(data)

        show_success(f"已处理 {input_file.name}, 输出保存到 {output_file.name}")
        tracker.add_success()
    except Exception as e:
        show_error(f"处理文件 {input_file.name} 时出错: {e}")
        tracker.add_failure()

def main():
    """主函数"""
    # 无参数时从 Finder 获取选中的文件
    if len(sys.argv) == 1:
        files = get_input_files([], expected_ext='csv')
        if files:
            sys.argv.extend(files)
    
    parser = argparse.ArgumentParser(
        description="将CSV文件中指定列的数字转换为带圈字符。",
        add_help=False
    )
    parser.add_argument(
        'input_files',
        nargs='+',
        help="一个或多个要处理的CSV文件。"
    )
    parser.add_argument(
        '-c', '--columns',
        type=int,
        nargs='+',
        required=True,
        help="要处理的列的索引 (从0开始)。"
    )
    parser.add_argument(
        '-h', '--help',
        action='help',
        help='显示此帮助信息并退出。'
    )
    parser.add_argument(
        '--version',
        action='version',
        version=f"v{SCRIPT_VERSION}",
        help="显示版本信息并退出。"
    )

    args = parser.parse_args()
    
    tracker = ProgressTracker()
    for file_str in args.input_files:
        input_file = Path(file_str)
        process_csv_file(input_file, args.columns, tracker)
    
    tracker.show_summary("CSV数字转圈字符")

if __name__ == "__main__":
    main() 
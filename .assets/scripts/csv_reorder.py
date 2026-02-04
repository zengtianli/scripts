#!/Users/tianli/miniforge3/bin/python3
# @raycast.schemaVersion 1
# @raycast.title csv-reorder
# @raycast.mode fullOutput
# @raycast.icon 📊
# @raycast.packageName Scripts
# @raycast.description Reorder CSV columns
"""
根据一个列表文件对一个或多个CSV文件进行行重排序。
"""

import sys
import csv
from pathlib import Path
import argparse

from common_utils import (
    show_success, show_error, show_info, fatal_error, ProgressTracker,
    show_version_info, show_help_header, show_help_footer, validate_input_file,
    get_input_files
)

SCRIPT_VERSION = "1.0.0"
SCRIPT_AUTHOR = "tianli"
SCRIPT_UPDATED = "2024-07-26"

def show_version():
    """显示版本信息"""
    show_version_info(SCRIPT_VERSION, SCRIPT_AUTHOR, SCRIPT_UPDATED)

def reorder_single_csv(input_file: Path, order_list: list, tracker: ProgressTracker):
    """对单个CSV文件进行重排序"""
    if not validate_input_file(input_file):
        tracker.add_failure()
        return

    show_info(f"正在处理文件: {input_file.name}")
    output_file = input_file.parent / f"{input_file.stem}_ordered.csv"

    try:
        with open(input_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            csv_data = list(reader)
        
        # BOM处理和名称清理
        data_dict = {row[0].lstrip('\ufeff').strip(): row for row in csv_data}
        
        ordered_data = []
        found_keys = set()

        for name in order_list:
            clean_name = name.strip()
            if clean_name in data_dict:
                ordered_data.append(data_dict[clean_name])
                found_keys.add(clean_name)
            # 处理带“（在建）”后缀的情况
            elif clean_name.replace('（在建）', '') in data_dict:
                key = clean_name.replace('（在建）', '')
                ordered_data.append(data_dict[key])
                found_keys.add(key)

        # 追加排序列表中未找到的行
        for key, row in data_dict.items():
            if key not in found_keys:
                ordered_data.append(row)
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(ordered_data)
        
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
        description="根据一个列表文件对一个或多个CSV文件进行行重排序。",
        add_help=False
    )
    parser.add_argument(
        'input_files',
        nargs='+',
        help="一个或多个要处理的CSV文件。"
    )
    parser.add_argument(
        '-l', '--list',
        default='b',
        help="包含期望顺序的列表文件 (默认为 'b')。"
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

    order_file = Path(args.list)
    if not order_file.is_file():
        fatal_error(f"排序列表文件不存在: {order_file}")

    try:
        with open(order_file, 'r', encoding='utf-8') as f:
            desired_order = [row[0].strip() for row in csv.reader(f)]
    except Exception as e:
        fatal_error(f"读取排序列表文件失败: {e}")

    if not desired_order:
        fatal_error("排序列表文件为空。")

    tracker = ProgressTracker()
    for file_str in args.input_files:
        input_file = Path(file_str)
        reorder_single_csv(input_file, desired_order, tracker)
    
    tracker.show_summary("CSV文件重排序")

if __name__ == "__main__":
    main() 
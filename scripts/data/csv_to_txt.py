#!/usr/bin/env python3
"""
CSV转TXT转换工具 - 将CSV文件转换为制表符分隔的TXT文件
版本: 2.0.0
作者: tianli
更新: 2024-01-01
"""

import sys
import csv
import argparse
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))
from display import show_success, show_error, show_warning, show_info, show_processing
from file_ops import (validate_input_file, check_file_extension, fatal_error,
                      show_version_info, find_files_by_extension)
from finder import get_input_files
from progress import ProgressTracker

SCRIPT_VERSION = "2.0.0"
SCRIPT_AUTHOR = "tianli"
SCRIPT_UPDATED = "2024-01-01"

def convert_csv_to_txt_single(input_file: Path, output_file: Optional[Path] = None) -> bool:
    try:
        if not validate_input_file(input_file):
            return False
        
        if not check_file_extension(input_file, 'csv'):
            show_warning(f"跳过不支持的文件: {input_file.name}")
            return False
        
        if output_file is None:
            output_file = input_file.with_suffix('.txt')
        
        show_processing(f"转换: {input_file.name} -> {output_file.name}")
        
        with open(input_file, 'r', encoding='utf-8') as f_in, \
             open(output_file, 'w', encoding='utf-8') as f_out:
            reader = csv.reader(f_in)
            for row in reader:
                f_out.write('\t'.join(row) + '\n')
        
        show_success(f"转换完成: {output_file.name}")
        return True
        
    except Exception as e:
        show_error(f"转换失败: {input_file.name} - {e}")
        return False

def batch_process(directory: Path, recursive: bool = False) -> None:
    show_info(f"处理目录: {directory}")
    files = find_files_by_extension(directory, 'csv', recursive)
    
    if not files:
        show_warning("未找到CSV文件")
        return
    
    show_info(f"找到 {len(files)} 个CSV文件")
    tracker = ProgressTracker()
    
    for i, file in enumerate(files, 1):
        show_processing(f"进度 ({i}/{len(files)}): {file.name}")
        if convert_csv_to_txt_single(file):
            tracker.add_success()
        else:
            tracker.add_failure()
    
    tracker.show_summary("文件转换")

def show_version() -> None:
    show_version_info(SCRIPT_VERSION, SCRIPT_AUTHOR, SCRIPT_UPDATED)

def show_help() -> None:
    print(f"""
用法: python3 {sys.argv[0]} [选项] [输入] [输出]

参数:
  输入            输入CSV文件或目录
  输出            输出TXT文件（可选，仅对单文件有效）

选项:
  -r, --recursive  递归处理子目录
  -h, --help       显示此帮助信息
  --version        显示版本信息
    """)

def main():
    # 无参数时从 Finder 获取选中的文件
    if len(sys.argv) == 1:
        files = get_input_files([], expected_ext='csv')
        if files:
            sys.argv.extend(files)
    
    parser = argparse.ArgumentParser(description='CSV转TXT转换工具', add_help=False)
    parser.add_argument('input', nargs='?', help='输入CSV文件或目录')
    parser.add_argument('output', nargs='?', help='输出TXT文件')
    parser.add_argument('-r', '--recursive', action='store_true', help='递归处理子目录')
    parser.add_argument('-h', '--help', action='store_true', help='显示帮助信息')
    parser.add_argument('--version', action='store_true', help='显示版本信息')
    args = parser.parse_args()
    
    if args.help:
        show_help()
        return
    
    if args.version:
        show_version()
        return
    
    if not args.input:
        batch_process(Path.cwd())
    else:
        input_path = Path(args.input)
        if input_path.is_file():
            output_path = Path(args.output) if args.output else None
            if not convert_csv_to_txt_single(input_path, output_path):
                sys.exit(1)
        elif input_path.is_dir():
            batch_process(input_path, args.recursive)
        else:
            fatal_error(f"输入路径不存在: {input_path}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        show_warning("用户中断操作")
        sys.exit(1)
    except Exception as e:
        fatal_error(f"程序执行失败: {e}") 
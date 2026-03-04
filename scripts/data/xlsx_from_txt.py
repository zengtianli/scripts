#!/usr/bin/env python3
"""
TXT转XLSX转换工具 - 将制表符分隔的文本文件转换为Excel XLSX格式
版本: 2.0.0
作者: tianli
更新: 2024-01-01
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))
from display import show_success, show_error, show_warning, show_info, show_processing
from file_ops import (validate_input_file, check_file_extension, fatal_error,
                      check_python_packages, show_version_info, find_files_by_extension)
from finder import get_input_files
from progress import ProgressTracker

SCRIPT_VERSION = "2.0.0"
SCRIPT_AUTHOR = "tianli"
SCRIPT_UPDATED = "2024-01-01"

def check_dependencies() -> bool:
    show_info("检查依赖项...")
    if not check_python_packages('pandas', 'openpyxl'):
        return False
    show_success("依赖检查完成")
    return True

def convert_txt_to_xlsx_single(input_file: Path, output_file: Optional[Path] = None) -> bool:
    try:
        if not validate_input_file(input_file):
            return False
        
        if not check_file_extension(input_file, 'txt'):
            show_warning(f"跳过不支持的文件: {input_file.name}")
            return False
        
        if output_file is None:
            output_file = input_file.with_suffix('.xlsx')
        
        show_processing(f"转换: {input_file.name} -> {output_file.name}")
        
        import pandas as pd
        
        df = pd.read_csv(input_file, sep='\t', encoding='utf-8', engine='python')
        df.to_excel(output_file, index=False)
        
        show_success(f"转换完成: {output_file.name}")
        return True
        
    except Exception as e:
        show_error(f"转换失败: {input_file.name} - {e}")
        return False

def batch_process(directory: Path, recursive: bool = False) -> None:
    show_info(f"处理目录: {directory}")
    files = find_files_by_extension(directory, 'txt', recursive)
    
    if not files:
        show_warning("未找到TXT文件")
        return
    
    show_info(f"找到 {len(files)} 个TXT文件")
    tracker = ProgressTracker()
    
    for i, file in enumerate(files, 1):
        show_processing(f"进度 ({i}/{len(files)}): {file.name}")
        if convert_txt_to_xlsx_single(file):
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
  输入            输入TXT文件或目录
  输出            输出XLSX文件（可选，仅对单文件有效）

选项:
  -r, --recursive  递归处理子目录
  -h, --help       显示此帮助信息
  --version        显示版本信息

依赖:
  - pandas
  - openpyxl
    """)

def main():
    parser = argparse.ArgumentParser(description='TXT转XLSX转换工具', add_help=False)
    parser.add_argument('-r', '--recursive', action='store_true', help='递归处理子目录')
    parser.add_argument('-h', '--help', action='store_true', help='显示帮助信息')
    parser.add_argument('--version', action='store_true', help='显示版本信息')
    args, unknown = parser.parse_known_args()

    if args.help:
        show_help()
        return

    if args.version:
        show_version()
        return

    if not check_dependencies():
        sys.exit(1)

    # 获取输入文件列表
    input_files = [Path(f) for f in get_input_files(unknown, expected_ext='txt')]

    if not input_files:
        show_warning("未找到TXT文件")
        sys.exit(1)

    show_info(f"找到 {len(input_files)} 个TXT文件")
    tracker = ProgressTracker()

    # 批量处理文件
    for i, file_path in enumerate(input_files, 1):
        show_processing(f"进度 ({i}/{len(input_files)}): {file_path.name}")
        if convert_txt_to_xlsx_single(file_path):
            tracker.add_success()
        else:
            tracker.add_failure()

    tracker.show_summary("文件转换")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        show_warning("用户中断操作")
        sys.exit(1)
    except Exception as e:
        fatal_error(f"程序执行失败: {e}")

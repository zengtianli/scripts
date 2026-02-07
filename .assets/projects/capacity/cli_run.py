#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================
# 脚本名称: cli_run.py
# 功能描述: 纳污能力计算 - 命令行版本
# 来源工单: 水利公司需求
# 创建日期: 2025-12-18
# 更新日期: 2025-01-15 - 整理目录结构
# 作者: 开发部
# ============================================================
"""
命令行版本 - 纳污能力计算

流程：
1. 读取 输入.xlsx → 拆分为 CSV
2. 核心计算 CSV → CSV
3. 合并 CSV → 计算结果.xlsx

使用方式：
    python cli_run.py           # 完整流程
    python cli_run.py --init    # 创建示例 输入.xlsx
"""

import argparse
import sys
from pathlib import Path

# 添加 src 目录到 path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from xlsx_bridge import xlsx_to_csv, csv_to_xlsx, create_example_xlsx
import calc_core


def main():
    parser = argparse.ArgumentParser(description='水环境功能区纳污能力计算 - 命令行版本')
    parser.add_argument('--init', action='store_true', help='创建示例 输入.xlsx')
    parser.add_argument('--input', default='输入.xlsx', help='输入文件路径')
    parser.add_argument('--output', default='计算结果.xlsx', help='输出文件路径')
    
    args = parser.parse_args()
    
    base_dir = Path(__file__).parent
    input_xlsx = base_dir / args.input
    output_xlsx = base_dir / args.output
    csv_input_dir = base_dir / 'data' / 'input'
    csv_output_dir = base_dir / 'data' / 'output'
    
    print("=" * 60)
    print("水环境功能区纳污能力计算 - 命令行版本")
    print("=" * 60)
    
    if args.init:
        # 创建示例文件
        create_example_xlsx(input_xlsx)
        return
    
    # 检查输入文件
    if not input_xlsx.exists():
        print(f"\n❌ 错误: 输入文件不存在: {input_xlsx}")
        print(f"\n提示: 运行 'python cli_run.py --init' 创建示例文件")
        return
    
    # Step 1: XLSX → CSV
    print("\n" + "-" * 60)
    print("Step 1: 拆分输入文件 XLSX → CSV")
    print("-" * 60)
    xlsx_to_csv(input_xlsx, csv_input_dir)
    
    # Step 2: 核心计算
    print("\n" + "-" * 60)
    print("Step 2: 核心计算")
    print("-" * 60)
    calc_core.main(input_dir=csv_input_dir, output_dir=csv_output_dir)
    
    # Step 3: CSV → XLSX
    print("\n" + "-" * 60)
    print("Step 3: 合并结果 CSV → XLSX")
    print("-" * 60)
    csv_to_xlsx(csv_output_dir, output_xlsx)
    
    print("\n" + "=" * 60)
    print("✓ 全部完成!")
    print("=" * 60)
    print(f"\n输入文件: {input_xlsx}")
    print(f"输出文件: {output_xlsx}")


if __name__ == '__main__':
    main()

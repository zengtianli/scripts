#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
水库发电调度 CLI 入口

使用方式:
    python run.py                      # 使用 输入.xlsx，输出到 计算结果.xlsx
    python run.py --input 输入.xlsx    # 指定输入文件
    python run.py --output 计算结果.xlsx  # 指定输出文件
    python run.py --init               # 创建示例 输入.xlsx

流程：
    1. 读取 输入.xlsx → 拆分为 CSV（csv/input/）
    2. 核心计算 CSV → CSV（csv/output/）
    3. 合并 CSV → 计算结果.xlsx

来源工单: 水库发电调度界面开发
"""

import sys
import os
import time
import argparse
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from src import xlsx_bridge
from src.hydro_core import HydroElectricity, read_info_txt, read_paras


def scan_reservoirs(input_dir: Path) -> list:
    """扫描输入目录下的水库文件夹"""
    reservoirs = []
    for item in input_dir.iterdir():
        if item.is_dir() and (item / "input_水库信息.txt").exists():
            reservoirs.append(item.name)
    return sorted(reservoirs)


def main():
    parser = argparse.ArgumentParser(description='梯级水库发电调度计算 - 一键运行')
    parser.add_argument('--input', type=str, default='输入.xlsx', help='输入文件路径')
    parser.add_argument('--output', type=str, default='计算结果.xlsx', help='输出文件路径')
    parser.add_argument('--step', type=str, default='旬', choices=['日', '旬', '月'], help='计算尺度')
    parser.add_argument('--init', action='store_true', help='创建示例 输入.xlsx')
    parser.add_argument('--from-existing', action='store_true', help='从现有 input/ 目录创建 输入.xlsx')
    args = parser.parse_args()

    # 项目根目录
    base_dir = Path(__file__).parent
    input_xlsx = base_dir / args.input
    output_xlsx = base_dir / args.output
    csv_input_dir = base_dir / 'data' / 'input'
    csv_output_dir = base_dir / 'data' / 'output'

    print("=" * 60)
    print("梯级水库发电调度计算 - 一键运行")
    print("=" * 60)

    # 初始化模式
    if args.init:
        xlsx_bridge.create_example_xlsx(input_xlsx)
        return
    
    # 从现有数据创建模式
    if args.from_existing:
        existing_input = base_dir / 'input'
        xlsx_bridge.create_xlsx_from_existing(input_xlsx, existing_input)
        return
    
    # 检查输入文件
    if not input_xlsx.exists():
        print(f"\n❌ 错误: 输入文件不存在: {input_xlsx}")
        print(f"\n提示:")
        print(f"  1. 运行 'python run.py --init' 创建示例文件")
        print(f"  2. 运行 'python run.py --from-existing' 从现有 input/ 目录创建")
        return

    # ======== Step 1: XLSX → CSV ========
    print("\n" + "-" * 60)
    print("Step 1: 拆分输入文件 XLSX → CSV")
    print("-" * 60)
    result = xlsx_bridge.xlsx_to_csv(input_xlsx, csv_input_dir)
    up_res = result['up_res']
    down_res = result['down_res']

    # ======== Step 2: 核心计算 ========
    print("\n" + "-" * 60)
    print("Step 2: 核心计算")
    print("-" * 60)
    
    # 扫描水库文件夹
    reservoirs = scan_reservoirs(csv_input_dir)
    print(f"识别到水库: {reservoirs}")

    if len(reservoirs) < 2:
        print("⚠️  至少需要 2 个水库（上游+下游）")
        return

    # 读取水库参数
    sks = {}
    for res_name in reservoirs:
        sks = read_info_txt(sks, res_name, str(csv_input_dir / res_name))

    # 基本参数
    base_info = {
        "CalStep": args.step,
        "EPSYH": 0.01,
        "EPSYV": 1,
        "EPSYW": 1
    }

    # 读取计算参数
    calc_param_file = csv_input_dir / "input_计算参数.csv"
    if not calc_param_file.exists():
        # 兼容旧模式
        calc_param_file = base_dir / 'input' / "input_计算参数.xlsx"
    
    paras_dict = read_paras(str(calc_param_file))
    print(f"\n计算参数: {paras_dict}\n")

    # 读取输出列名
    output_list_file = base_dir / "src" / "output_columns.csv"
    output_list = pd.read_csv(output_list_file, sep='\t', header=None, encoding='utf-8').values[:, 0].tolist()
    print(f"输出列: {len(output_list)} 列\n")

    # 开始计算
    st = time.time()
    test = HydroElectricity(sks, base_info)
    
    up_table, down_table = test.power_operate_year_up_down(
        if_up_q_eco_as_in=paras_dict['if_q_up_eco_as_in'],
        up_res_name=paras_dict['up_res'],
        down_res_name=paras_dict['down_res'],
        up_v_special=paras_dict['up_v_special'],
        down_v_special=paras_dict['down_v_special'],
        need_add_user=paras_dict['need_add_user'],
        user_special=paras_dict['another_add'],
        user_stop_supply=paras_dict['stop_supply'],
    )
    
    calc_time = time.time() - st
    print(f"\n计算耗时: {calc_time:.2f}s")

    # 保存 CSV 结果
    csv_output_dir.mkdir(parents=True, exist_ok=True)
    original_cwd = os.getcwd()
    os.chdir(csv_output_dir)
    
    try:
        test.statistic_for_up_down(up_table, '', up_res, output_list)
        test.statistic_for_up_down(down_table, '', down_res, output_list)
    finally:
        os.chdir(original_cwd)

    # ======== Step 3: CSV → XLSX ========
    print("\n" + "-" * 60)
    print("Step 3: 合并结果 CSV → XLSX")
    print("-" * 60)
    xlsx_bridge.csv_to_xlsx(csv_output_dir, output_xlsx, up_res, down_res)

    # ======== 完成 ========
    total_time = time.time() - st
    print("\n" + "=" * 60)
    print("✓ 全部完成!")
    print("=" * 60)
    print(f"\n输入文件: {input_xlsx}")
    print(f"输出文件: {output_xlsx}")
    print(f"计算尺度: {args.step}")
    print(f"总耗时: {total_time:.2f}s")
    
    # 列出输出文件
    print("\n中间结果 (CSV):")
    for res in [up_res, down_res]:
        res_dir = csv_output_dir / res
        if res_dir.exists():
            print(f"  {res}/")
            for f in sorted(res_dir.glob("output_*.csv")):
                print(f"    - {f.name}")
    print("=" * 60)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================
# 脚本名称: xlsx_bridge.py
# 功能描述: XLSX ↔ CSV 格式转换桥梁程序
# 来源工单: 水利公司需求
# 创建日期: 2025-12-18
# 更新日期: 2025-12-18 - 简化为单一Cs/C0
# 作者: 开发部
# ============================================================
"""
桥梁程序 - XLSX 和 CSV 之间的格式转换

功能：
1. xlsx_to_csv: 将 输入.xlsx 拆分为 CSV 文件
2. csv_to_xlsx: 将 CSV 计算结果合并为 计算结果.xlsx

使用方式：
    python xlsx_bridge.py --to-csv 输入.xlsx
    python xlsx_bridge.py --to-xlsx
    python xlsx_bridge.py --init  # 创建示例 输入.xlsx
"""

import pandas as pd
from pathlib import Path
import argparse


# ============================================================
# 转换函数
# ============================================================
def xlsx_to_csv(xlsx_path: Path, output_dir: Path):
    """将 输入.xlsx 拆分为 CSV 文件"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"读取: {xlsx_path}")
    xlsx = pd.ExcelFile(xlsx_path)
    
    sheet_mapping = {
        '功能区基础信息': '功能区基础信息.csv',
        '逐日流量': '逐日流量.csv',
        '水库功能区基础信息': '水库功能区基础信息.csv',
        '水库逐日库容': '水库逐日库容.csv',
    }
    
    for sheet_name in xlsx.sheet_names:
        if sheet_name in sheet_mapping:
            df = pd.read_excel(xlsx, sheet_name=sheet_name)
            csv_path = output_dir / sheet_mapping[sheet_name]
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"  ✓ {sheet_name} → {csv_path.name}")
    
    print(f"\n输出目录: {output_dir}/")


def csv_to_xlsx(csv_dir: Path, xlsx_path: Path):
    """将 CSV 计算结果合并为 计算结果.xlsx"""
    
    # 结果文件列表
    csv_files = [
        ('逐月流量.csv', '逐月流量'),
        ('逐月流速.csv', '逐月流速'),
        ('功能区月平均流速.csv', '功能区月平均流速'),
        ('功能区月平均纳污能力.csv', '功能区月平均纳污能力'),
        ('水库逐月库容.csv', '水库逐月库容'),
        ('水库功能区月平均纳污能力.csv', '水库功能区月平均纳污能力'),
    ]
    
    print(f"合并 CSV 到: {xlsx_path}")
    
    with pd.ExcelWriter(xlsx_path, engine='openpyxl') as writer:
        for csv_name, sheet_name in csv_files:
            csv_path = csv_dir / csv_name
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                print(f"  ✓ {csv_name} → Sheet '{sheet_name}'")
    
    print(f"\n输出文件: {xlsx_path}")


def create_example_xlsx(xlsx_path: Path):
    """创建示例 输入.xlsx"""
    import numpy as np
    np.random.seed(42)
    
    print(f"创建示例文件: {xlsx_path}")
    
    # ========== 河道数据 ==========
    zones_data = {
        '功能区': ['QT-153', 'QT-154', 'QT-155', 'QT-156'],
        '名称': ['源头段', '上游段', '中游段', '下游段'],
        '水质类别': ['II', 'II', 'III', 'III'],
        'Cs': [0.5, 0.5, 1.0, 1.0],       # 目标浓度
        'C0': [0.4, 0.0, 0.8, 0.0],       # 初始浓度（0表示使用上游出流）
        '河段长度L(m)': [1000, 1500, 2000, 1800],
        '衰减系数K(1/s)': [0.001, 0.001, 0.001, 0.001],
        '不均匀系数b': [0.8, 0.8, 0.8, 0.8],
        'a': [0.3, 0.3, 0.3, 0.3],
        'β': [0.5, 0.5, 0.5, 0.5],
    }
    zones_df = pd.DataFrame(zones_data)
    
    # 逐日流量
    dates = pd.date_range('1992-01-01', '1993-12-31', freq='D')
    flow_data = {'日期': dates}
    for zone_id in zones_data['功能区']:
        flow_data[zone_id] = np.random.uniform(100, 700, len(dates))
    flow_df = pd.DataFrame(flow_data)
    
    # ========== 水库数据 ==========
    reservoir_zones_data = {
        '功能区': ['SK-01', 'SK-02'],
        '名称': ['青山水库', '碧湖水库'],
        'K(1/s)': [0.000002, 0.000002],
        'b': [0.2, 0.2],
        'Cs': [0.5, 1.0],
        'C0': [0.02, 0.02],  # 保留字段
    }
    reservoir_zones_df = pd.DataFrame(reservoir_zones_data)
    
    # 水库逐日库容
    reservoir_dates = pd.date_range('1992-04-01', '1994-03-31', freq='D')
    volume_data = {'日期': reservoir_dates}
    for zone_id in reservoir_zones_data['功能区']:
        volume_data[zone_id] = np.random.uniform(40000000, 55000000, len(reservoir_dates))
    volume_df = pd.DataFrame(volume_data)
    
    # 写入 Excel
    with pd.ExcelWriter(xlsx_path, engine='openpyxl') as writer:
        zones_df.to_excel(writer, sheet_name='功能区基础信息', index=False)
        flow_df.to_excel(writer, sheet_name='逐日流量', index=False)
        reservoir_zones_df.to_excel(writer, sheet_name='水库功能区基础信息', index=False)
        volume_df.to_excel(writer, sheet_name='水库逐日库容', index=False)
    
    print(f"  ✓ 功能区基础信息 ({len(zones_data['功能区'])}个河道功能区)")
    print(f"  ✓ 逐日流量 ({len(dates)} 天)")
    print(f"  ✓ 水库功能区基础信息 ({len(reservoir_zones_data['功能区'])}个水库)")
    print(f"  ✓ 水库逐日库容 ({len(reservoir_dates)} 天)")
    print(f"\n示例文件已创建: {xlsx_path}")


# ============================================================
# 主函数
# ============================================================
def main():
    parser = argparse.ArgumentParser(description='XLSX ↔ CSV 格式转换')
    parser.add_argument('--to-csv', metavar='XLSX', help='将 XLSX 拆分为 CSV')
    parser.add_argument('--to-xlsx', action='store_true', help='将 CSV 合并为 XLSX')
    parser.add_argument('--init', action='store_true', help='创建示例 输入.xlsx')
    parser.add_argument('--input-dir', default='csv/input', help='CSV 输入目录')
    parser.add_argument('--output-dir', default='csv/output', help='CSV 输出目录')
    
    args = parser.parse_args()
    
    base_dir = Path(__file__).parent.parent
    input_dir = base_dir / args.input_dir
    output_dir = base_dir / args.output_dir
    
    if args.init:
        create_example_xlsx(base_dir / '输入.xlsx')
    elif args.to_csv:
        xlsx_path = Path(args.to_csv)
        if not xlsx_path.is_absolute():
            xlsx_path = base_dir / xlsx_path
        xlsx_to_csv(xlsx_path, input_dir)
    elif args.to_xlsx:
        csv_to_xlsx(output_dir, base_dir / '计算结果.xlsx')
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

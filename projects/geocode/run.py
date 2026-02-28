#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地理编码工具 - 命令行统一入口

使用方式：
    python run.py reverse <输入> <输出> [--gcj02]    # 逆地理编码
    python run.py address <输入> <输出>              # 正向编码
    python run.py company <输入> <输出>              # 企业搜索
    python run.py --help                             # 帮助

输入输出支持 xlsx 或 csv 格式（推荐 xlsx）
"""
import sys
import os
from pathlib import Path

# 添加 src 目录到 path
sys.path.insert(0, str(Path(__file__).parent / 'src'))


def print_help():
    """打印帮助信息"""
    print("""
================================================================================
                        地理编码工具集
================================================================================

用法:
    python run.py <命令> <输入文件> <输出文件> [选项]

命令:
    reverse     逆地理编码（经纬度 → 地址）
    address     正向编码（地址 → 经纬度）
    company     企业搜索（公司名 → 位置）

选项:
    --gcj02     输入坐标已是 GCJ-02，跳过转换（仅 reverse）
                默认假设输入是 WGS-84，自动转换

示例:
    # 逆地理编码（WGS-84 坐标，自动转换）
    python run.py reverse data/sample/示例坐标.xlsx output.xlsx

    # 逆地理编码（已是 GCJ-02，跳过转换）
    python run.py reverse input.xlsx output.xlsx --gcj02

    # 正向编码
    python run.py address addresses.xlsx output.xlsx

    # 企业搜索
    python run.py company companies.xlsx output.xlsx

环境变量:
    AMAP_API_KEY    高德地图 API Key（必需）

================================================================================
""")


def xlsx_to_csv(xlsx_path: str) -> str:
    """将 xlsx 转换为临时 csv"""
    import pandas as pd
    csv_path = xlsx_path.rsplit('.', 1)[0] + '_temp.csv'
    df = pd.read_excel(xlsx_path)
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    return csv_path


def csv_to_xlsx(csv_path: str, xlsx_path: str):
    """将 csv 转换为 xlsx"""
    import pandas as pd
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    df.to_excel(xlsx_path, index=False)


def run_reverse(args: list):
    """运行逆地理编码"""
    from reverse_geocode import main as reverse_main
    
    # 检查参数
    if len(args) < 2:
        print("用法: python run.py reverse <输入文件> <输出文件> [--gcj02]")
        sys.exit(1)
    
    input_file = args[0]
    output_file = args[1]
    extra_args = args[2:]
    
    # 如果输入是 xlsx，转换为 csv
    temp_csv = None
    if input_file.endswith('.xlsx'):
        temp_csv = xlsx_to_csv(input_file)
        input_file = temp_csv
    
    # 确定输出文件类型
    output_is_xlsx = output_file.endswith('.xlsx')
    if output_is_xlsx:
        csv_output = output_file.rsplit('.', 1)[0] + '_temp.csv'
    else:
        csv_output = output_file
    
    # 构建参数并调用
    sys.argv = ['reverse_geocode.py', input_file, csv_output] + extra_args
    reverse_main()
    
    # 如果需要 xlsx 输出，转换
    if output_is_xlsx:
        csv_to_xlsx(csv_output, output_file)
        os.remove(csv_output)
        print(f"✅ 已转换为 Excel: {output_file}")
    
    # 清理临时文件
    if temp_csv and os.path.exists(temp_csv):
        os.remove(temp_csv)


def run_address(args: list):
    """运行正向编码"""
    from geocode_by_address import main as address_main
    
    if len(args) < 2:
        print("用法: python run.py address <输入文件> <输出文件>")
        sys.exit(1)
    
    input_file = args[0]
    output_file = args[1]
    
    # xlsx 转 csv
    temp_csv = None
    if input_file.endswith('.xlsx'):
        temp_csv = xlsx_to_csv(input_file)
        input_file = temp_csv
    
    output_is_xlsx = output_file.endswith('.xlsx')
    if output_is_xlsx:
        csv_output = output_file.rsplit('.', 1)[0] + '_temp.csv'
    else:
        csv_output = output_file
    
    sys.argv = ['geocode_by_address.py', input_file, csv_output]
    address_main()
    
    if output_is_xlsx:
        csv_to_xlsx(csv_output, output_file)
        os.remove(csv_output)
        print(f"✅ 已转换为 Excel: {output_file}")
    
    if temp_csv and os.path.exists(temp_csv):
        os.remove(temp_csv)


def run_company(args: list):
    """运行企业搜索"""
    from search_by_company import main as company_main
    
    if len(args) < 2:
        print("用法: python run.py company <输入文件> <输出文件>")
        sys.exit(1)
    
    input_file = args[0]
    output_file = args[1]
    
    temp_csv = None
    if input_file.endswith('.xlsx'):
        temp_csv = xlsx_to_csv(input_file)
        input_file = temp_csv
    
    output_is_xlsx = output_file.endswith('.xlsx')
    if output_is_xlsx:
        csv_output = output_file.rsplit('.', 1)[0] + '_temp.csv'
    else:
        csv_output = output_file
    
    sys.argv = ['search_by_company.py', input_file, csv_output]
    company_main()
    
    if output_is_xlsx:
        csv_to_xlsx(csv_output, output_file)
        os.remove(csv_output)
        print(f"✅ 已转换为 Excel: {output_file}")
    
    if temp_csv and os.path.exists(temp_csv):
        os.remove(temp_csv)


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ['-h', '--help', 'help']:
        print_help()
        sys.exit(0)
    
    command = sys.argv[1]
    args = sys.argv[2:]
    
    # 检查 API Key
    if not os.getenv('AMAP_API_KEY'):
        print("❌ 请设置环境变量 AMAP_API_KEY")
        print("   export AMAP_API_KEY='你的高德API密钥'")
        sys.exit(1)
    
    if command == 'reverse':
        run_reverse(args)
    elif command == 'address':
        run_address(args)
    elif command == 'company':
        run_company(args)
    else:
        print(f"❌ 未知命令: {command}")
        print("   使用 --help 查看帮助")
        sys.exit(1)


if __name__ == "__main__":
    main()


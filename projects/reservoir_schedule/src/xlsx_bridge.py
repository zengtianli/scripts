#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================
# 脚本名称: xlsx_bridge.py
# 功能描述: XLSX ↔ CSV 格式转换桥梁程序
# 来源工单: 水利公司需求
# 创建日期: 2025-12-27
# 作者: 开发部
# ============================================================
"""
桥梁程序 - XLSX 和 CSV 之间的格式转换

功能：
1. xlsx_to_csv: 将 输入.xlsx 拆分为 CSV 文件
2. csv_to_xlsx: 将 CSV 计算结果合并为 计算结果.xlsx
3. create_example_xlsx: 创建示例 输入.xlsx

使用方式：
    python xlsx_bridge.py --to-csv 输入.xlsx
    python xlsx_bridge.py --to-xlsx
    python xlsx_bridge.py --init  # 创建示例 输入.xlsx
"""

import pandas as pd
from pathlib import Path
import argparse


# ============================================================
# Sheet 映射配置
# ============================================================

# 输入文件 Sheet 名称 → CSV 文件名（每个水库一份）
RESERVOIR_SHEETS = {
    '水库信息': 'input_水库信息.txt',
    '水位库容': 'input_水位-库容.txt',
    '水位流量': 'input_水位-流量.txt',
    '来水系列': 'input_来水及生态系列.csv',
    '坝下需水': 'input_坝下需水系列.csv',
    '库内需水': 'input_库内需水系列.csv',
    '限制线': 'input_限制线.csv',
    '调度线': 'input_发电调度线.csv',
    '下游水位': 'input_下游水位_下游尾水位恒定.csv',
}

# 输出文件 Sheet 名称 → CSV 文件名（每个水库一份）
OUTPUT_SHEETS = {
    '逐日过程': 'output_逐日过程.csv',
    '逐月过程': 'output_逐月过程.csv',
    '逐年过程': 'output_逐年过程.csv',
    '水文年过程': 'output_水文年过程.csv',
    '汇总': 'output_汇总.csv',
}


# ============================================================
# 转换函数
# ============================================================

def xlsx_to_csv(xlsx_path: Path, output_dir: Path) -> dict:
    """
    将 输入.xlsx 拆分为 CSV 文件
    
    Args:
        xlsx_path: 输入 xlsx 文件路径
        output_dir: CSV 输出目录（csv/input/）
        
    Returns:
        dict: {'up_res': 上游水库名, 'down_res': 下游水库名, 'paras': 计算参数}
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"读取: {xlsx_path}")
    xlsx = pd.ExcelFile(xlsx_path)
    
    result = {'up_res': None, 'down_res': None, 'paras': {}}
    
    # 1. 读取计算参数
    if '计算参数' in xlsx.sheet_names:
        # 读取原始数据，不设置 header（因为第一行是"上库"列名）
        df_params = pd.read_excel(xlsx, sheet_name='计算参数', header=None)
        
        # 计算参数格式：
        # 列0: 参数名（第一行为"上库"）
        # 列1: 值（第一行为上游水库名）
        # 提取上游/下游水库名称
        for idx, row in df_params.iterrows():
            param_name = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ''
            if param_name == '上库':
                result['up_res'] = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else None
            elif param_name == '下库':
                result['down_res'] = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else None
            elif param_name not in ['', 'nan', 'NaN']:
                # 存储其他参数
                result['paras'][param_name] = row.iloc[1] if pd.notna(row.iloc[1]) else None
        
        # 保存计算参数 CSV（无 header，保持原格式）
        params_csv = output_dir / 'input_计算参数.csv'
        df_params.to_csv(params_csv, index=False, header=False, encoding='utf-8-sig')
        print(f"  ✓ 计算参数 → {params_csv.name}")
    
    up_res = result['up_res']
    down_res = result['down_res']
    
    if not up_res or not down_res:
        raise ValueError("无法从 '计算参数' Sheet 中识别上游/下游水库名称")
    
    print(f"  上游水库: {up_res}")
    print(f"  下游水库: {down_res}")
    
    # 2. 创建水库目录
    up_dir = output_dir / up_res
    down_dir = output_dir / down_res
    up_dir.mkdir(parents=True, exist_ok=True)
    down_dir.mkdir(parents=True, exist_ok=True)
    
    # 3. 拆分各水库数据
    for sheet_suffix, csv_name in RESERVOIR_SHEETS.items():
        # 上游水库
        up_sheet = f"上游_{sheet_suffix}"
        if up_sheet in xlsx.sheet_names:
            df = pd.read_excel(xlsx, sheet_name=up_sheet)
            csv_path = up_dir / csv_name
            # 根据文件扩展名决定分隔符
            if csv_name.endswith('.txt'):
                df.to_csv(csv_path, index=False, encoding='utf-8-sig', sep='\t')
            else:
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"  ✓ {up_sheet} → {up_res}/{csv_name}")
        
        # 下游水库
        down_sheet = f"下游_{sheet_suffix}"
        if down_sheet in xlsx.sheet_names:
            df = pd.read_excel(xlsx, sheet_name=down_sheet)
            csv_path = down_dir / csv_name
            if csv_name.endswith('.txt'):
                df.to_csv(csv_path, index=False, encoding='utf-8-sig', sep='\t')
            else:
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"  ✓ {down_sheet} → {down_res}/{csv_name}")
    
    print(f"\n输出目录: {output_dir}/")
    return result


def csv_to_xlsx(csv_dir: Path, xlsx_path: Path, up_res: str, down_res: str):
    """
    将 CSV 计算结果合并为 计算结果.xlsx
    
    Args:
        csv_dir: CSV 输出目录（csv/output/）
        xlsx_path: 输出 xlsx 文件路径
        up_res: 上游水库名称
        down_res: 下游水库名称
    """
    print(f"合并 CSV 到: {xlsx_path}")
    
    with pd.ExcelWriter(xlsx_path, engine='openpyxl') as writer:
        for res_name, prefix in [(up_res, '上游'), (down_res, '下游')]:
            res_dir = csv_dir / res_name
            if not res_dir.exists():
                print(f"  ⚠ 未找到 {res_name} 目录，跳过")
                continue
            
            for sheet_suffix, csv_name in OUTPUT_SHEETS.items():
                csv_path = res_dir / csv_name
                if csv_path.exists():
                    df = pd.read_csv(csv_path)
                    sheet_name = f"{prefix}_{sheet_suffix}"
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    print(f"  ✓ {res_name}/{csv_name} → Sheet '{sheet_name}'")
    
    print(f"\n输出文件: {xlsx_path}")


def create_example_xlsx(xlsx_path: Path, template_dir: Path = None):
    """
    创建示例 输入.xlsx
    
    Args:
        xlsx_path: 输出 xlsx 文件路径
        template_dir: 模板数据目录（可选，如果提供则从现有 CSV 创建）
    """
    import numpy as np
    np.random.seed(42)
    
    print(f"创建示例文件: {xlsx_path}")
    
    with pd.ExcelWriter(xlsx_path, engine='openpyxl') as writer:
        # ========== 计算参数 ==========
        params_data = {
            '参数': ['上库', '下库', '上库特征库容', '下库特征库容', 
                   '需补水的用水户（利用上库特征库容之间进行补水）', 
                   '额外再补用水户（利用上库特征库容以下进行补水）',
                   '额外再补流量', '湖南镇生态水是否入黄坛口水量平衡',
                   '当上库库容较低时（低于上库特征库容），下库停止供水的用水户'],
            '值1': ['湖南镇水库', '黄坛口水库', 59994, 7040, '衢州生活工业', None, 7.52, 1, None],
            '值2': [None, None, 55919, None, '金华', None, None, None, None],
            '值3': [None, None, None, None, '龙游', None, None, None, None],
        }
        df_params = pd.DataFrame(params_data)
        df_params.to_excel(writer, sheet_name='计算参数', index=False)
        print(f"  ✓ 计算参数")
        
        # ========== 水库数据模板 ==========
        # 为上游和下游各创建一套模板
        for prefix, res_name in [('上游', '湖南镇水库'), ('下游', '黄坛口水库')]:
            # 水库信息
            info_data = {
                '参数': ['水库名称', '水库死水位', '水库正常水位', '装机容量', '机组设计流量'],
                '值': [res_name, 196 if prefix == '上游' else 107.23, 
                      230 if prefix == '上游' else 113.23,
                      320000 if prefix == '上游' else 88000,
                      360 if prefix == '上游' else 372]
            }
            df_info = pd.DataFrame(info_data)
            df_info.to_excel(writer, sheet_name=f'{prefix}_水库信息', index=False)
            
            # 水位库容
            if prefix == '上游':
                zv_data = {'水位(m)': list(range(190, 233)), 
                          '库容(万m3)': [44884 + i*2000 for i in range(43)]}
            else:
                zv_data = {'水位(m)': [94 + i*0.5 for i in range(40)], 
                          '库容(万m3)': [1000 + i*200 for i in range(40)]}
            df_zv = pd.DataFrame(zv_data)
            df_zv.to_excel(writer, sheet_name=f'{prefix}_水位库容', index=False)
            
            # 水位流量
            zq_data = {'水位（m）': [100 + i*0.5 for i in range(10)],
                      '流量(m3/s)': [0, 50, 100, 200, 370, 520, 720, 920, 1150, 1400]}
            df_zq = pd.DataFrame(zq_data)
            df_zq.to_excel(writer, sheet_name=f'{prefix}_水位流量', index=False)
            
            # 来水系列（示例 2 年）
            dates = pd.date_range('1961-01-01', '1962-12-31', freq='10D')
            flow_data = {
                '日期': dates,
                f'{res_name[:3]}来水流量': np.random.uniform(10, 500, len(dates)),
                f'{res_name[:3]}需生态下泄流量': np.zeros(len(dates))
            }
            df_flow = pd.DataFrame(flow_data)
            df_flow.to_excel(writer, sheet_name=f'{prefix}_来水系列', index=False)
            
            # 坝下需水
            demand_data = {
                '时间': dates,
                '需水流量1': np.random.uniform(10, 30, len(dates)),
                '需水流量2': np.random.uniform(5, 15, len(dates))
            }
            df_demand = pd.DataFrame(demand_data)
            df_demand.to_excel(writer, sheet_name=f'{prefix}_坝下需水', index=False)
            
            # 库内需水
            df_internal = pd.DataFrame({'时间': dates})
            df_internal.to_excel(writer, sheet_name=f'{prefix}_库内需水', index=False)
            
            # 限制线
            months = [f'{m}月1日' for m in range(1, 13)]
            limit_data = {
                '月份': months,
                '发电死库容': [55919] * 12,
                '发电限制库容': [59994] * 12
            }
            df_limit = pd.DataFrame(limit_data)
            df_limit.to_excel(writer, sheet_name=f'{prefix}_限制线', index=False)
            
            # 调度线
            schedule_data = {
                '日期': months,
                'V1': [158424] * 12,
                'P1': [320000] * 12,
                'V2': [148589] * 12,
                'P2': [203200] * 12
            }
            df_schedule = pd.DataFrame(schedule_data)
            df_schedule.to_excel(writer, sheet_name=f'{prefix}_调度线', index=False)
            
            # 下游水位
            downstream_data = {
                'Date': [f'{m:02d}-01' for m in range(1, 13)],
                'Zdown(m)': [37] * 12
            }
            df_downstream = pd.DataFrame(downstream_data)
            df_downstream.to_excel(writer, sheet_name=f'{prefix}_下游水位', index=False)
            
            print(f"  ✓ {prefix} 水库数据（9 个 Sheet）")
    
    print(f"\n示例文件已创建: {xlsx_path}")
    print("\n⚠️ 注意：这是示例数据，请用真实数据替换！")


def create_xlsx_from_existing(xlsx_path: Path, input_dir: Path):
    """
    从现有 CSV 数据创建 输入.xlsx
    
    Args:
        xlsx_path: 输出 xlsx 文件路径
        input_dir: 现有数据目录（含水库子目录）
    """
    print(f"从现有数据创建: {xlsx_path}")
    print(f"数据目录: {input_dir}")
    
    # 扫描水库目录
    reservoir_dirs = [d for d in input_dir.iterdir() if d.is_dir()]
    
    if len(reservoir_dirs) < 2:
        raise ValueError(f"需要至少 2 个水库目录，当前只有: {[d.name for d in reservoir_dirs]}")
    
    # 假设第一个是上游，第二个是下游（按名称排序）
    reservoir_dirs.sort(key=lambda x: x.name)
    up_dir = reservoir_dirs[0]
    down_dir = reservoir_dirs[1]
    up_res = up_dir.name
    down_res = down_dir.name
    
    print(f"  上游水库: {up_res}")
    print(f"  下游水库: {down_res}")
    
    with pd.ExcelWriter(xlsx_path, engine='openpyxl') as writer:
        # 计算参数
        params_xlsx = input_dir / 'input_计算参数.xlsx'
        if params_xlsx.exists():
            df_params = pd.read_excel(params_xlsx)
            df_params.to_excel(writer, sheet_name='计算参数', index=False)
            print(f"  ✓ 计算参数")
        
        # 各水库数据
        for res_dir, prefix in [(up_dir, '上游'), (down_dir, '下游')]:
            for sheet_suffix, csv_name in RESERVOIR_SHEETS.items():
                csv_path = res_dir / csv_name
                if csv_path.exists():
                    # 根据文件扩展名决定分隔符
                    if csv_name.endswith('.txt'):
                        df = pd.read_csv(csv_path, sep='\t', encoding='utf-8')
                    else:
                        df = pd.read_csv(csv_path, encoding='utf-8')
                    
                    sheet_name = f"{prefix}_{sheet_suffix}"
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    print(f"  ✓ {res_dir.name}/{csv_name} → {sheet_name}")
    
    print(f"\n输出文件: {xlsx_path}")


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(description='XLSX ↔ CSV 格式转换')
    parser.add_argument('--to-csv', metavar='XLSX', help='将 XLSX 拆分为 CSV')
    parser.add_argument('--to-xlsx', action='store_true', help='将 CSV 合并为 XLSX')
    parser.add_argument('--init', action='store_true', help='创建示例 输入.xlsx')
    parser.add_argument('--from-existing', action='store_true', help='从现有 CSV 创建 输入.xlsx')
    parser.add_argument('--input-dir', default='csv/input', help='CSV 输入目录')
    parser.add_argument('--output-dir', default='csv/output', help='CSV 输出目录')
    parser.add_argument('--up-res', default='湖南镇水库', help='上游水库名称')
    parser.add_argument('--down-res', default='黄坛口水库', help='下游水库名称')
    
    args = parser.parse_args()
    
    # 项目根目录
    base_dir = Path(__file__).parent.parent
    input_dir = base_dir / args.input_dir
    output_dir = base_dir / args.output_dir
    
    if args.init:
        create_example_xlsx(base_dir / '输入.xlsx')
    elif args.from_existing:
        # 从现有 input 目录创建
        existing_input = base_dir / 'input'
        create_xlsx_from_existing(base_dir / '输入.xlsx', existing_input)
    elif args.to_csv:
        xlsx_path = Path(args.to_csv)
        if not xlsx_path.is_absolute():
            xlsx_path = base_dir / xlsx_path
        xlsx_to_csv(xlsx_path, input_dir)
    elif args.to_xlsx:
        csv_to_xlsx(output_dir, base_dir / '计算结果.xlsx', args.up_res, args.down_res)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()


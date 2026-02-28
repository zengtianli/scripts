#!/usr/bin/env python3
"""
Excel 转 TXT 转换脚本
将 水稻生长期.xlsx 和 灌溉制度.xlsx 转换为程序所需的 static_*.txt 文件

单位转换规则：
- 灌溉定额：m³/亩 → m³/km²（× 1500）
- 作物面积：亩 → km²（÷ 1500）

用法：直接运行，无需参数
    python xlsx_to_txt.py
"""

import os
import pandas as pd
from datetime import datetime, timedelta

# 单位转换常量
MU_PER_KM2 = 1500  # 1 km² = 1500 亩


def excel_date_to_str(serial):
    """Excel日期序列号转字符串 YYYY/MM/DD"""
    try:
        if isinstance(serial, str):
            if '月' in serial:
                # 处理 "7月15" 格式
                parts = serial.replace('月', '/').replace('日', '').strip()
                month = int(parts.split('/')[0])
                day = int(parts.split('/')[1]) if '/' in parts else 1
                return f"2025/{month:02d}/{day:02d}"
            return serial
        serial = int(serial)
        dt = datetime(1899, 12, 30) + timedelta(days=serial)
        return dt.strftime('%Y/%m/%d')
    except:
        return str(serial)


def convert_rice_growth():
    """转换水稻生长期.xlsx"""
    print("读取 水稻生长期.xlsx ...")
    df = pd.read_excel('水稻生长期.xlsx', header=None)
    
    # 生育期名称
    periods = ['泡田期', '返青', '分蘖前', '分蘖末', '拔节育穗期', '抽穗开花期', '乳熟期', '黄熟期']
    
    # 解析配置
    rice_config = {
        '早稻': {'start_row': 1, 'end_row': 2, 'quota_rows': [3, 4, 5]},
        '晚稻': {'start_row': 7, 'end_row': 8, 'quota_rows': [9, 10, 11]},
        '单季稻': {'start_row': 13, 'end_row': 14, 'quota_rows': [15, 16, 17]}
    }
    
    # 生成 static_rice_growth.txt（水稻生育期完整数据）
    lines = [
        "# 水稻生育期灌溉定额表",
        "# 来源: 水稻生长期.xlsx",
        "# 单位: m³/亩",
        "",
        "作物\t生育期\t开始日期\t结束日期\t天数\t定额_50%\t定额_75%\t定额_90%"
    ]
    
    for rice_type, cfg in rice_config.items():
        for i, period_name in enumerate(periods):
            col = i + 2
            try:
                start = excel_date_to_str(df.iloc[cfg['start_row'], col])
                end = excel_date_to_str(df.iloc[cfg['end_row'], col])
                
                # 计算天数
                try:
                    d1 = datetime.strptime(start, '%Y/%m/%d')
                    d2 = datetime.strptime(end, '%Y/%m/%d')
                    days = (d2 - d1).days + 1
                except:
                    days = 0
                
                q50 = df.iloc[cfg['quota_rows'][0], col]
                q75 = df.iloc[cfg['quota_rows'][1], col]
                q90 = df.iloc[cfg['quota_rows'][2], col]
                
                q50 = float(q50) if pd.notna(q50) else 0
                q75 = float(q75) if pd.notna(q75) else 0
                q90 = float(q90) if pd.notna(q90) else 0
                
                lines.append(f"{rice_type}\t{period_name}\t{start}\t{end}\t{days}\t{q50}\t{q75}\t{q90}")
            except Exception as e:
                print(f"  警告: {rice_type} {period_name} 解析失败: {e}")
    
    # 构建 DataFrame 返回（不写入文件）
    rice_data = []
    for rice_type, cfg in rice_config.items():
        for i, period_name in enumerate(periods):
            col = i + 2
            try:
                start = excel_date_to_str(df.iloc[cfg['start_row'], col])
                end = excel_date_to_str(df.iloc[cfg['end_row'], col])
                try:
                    d1 = datetime.strptime(start, '%Y/%m/%d')
                    d2 = datetime.strptime(end, '%Y/%m/%d')
                    days = (d2 - d1).days + 1
                except:
                    days = 0
                rice_data.append({
                    '作物': rice_type, '生育期': period_name,
                    '开始日期': start, '结束日期': end, '天数': days
                })
            except:
                pass
    
    df_rice = pd.DataFrame(rice_data)
    print("解析: 水稻生长期数据")
    
    return df_rice


def convert_irrigation_schedule():
    """转换灌溉制度.xlsx，单位从 m³/亩 转为 m³/km²"""
    print("读取 灌溉制度.xlsx ...")
    df = pd.read_excel('灌溉制度.xlsx', header=None)
    
    # 生成 static_irrigation_quota.txt（所有作物灌溉定额）
    lines = [
        "# ============================================================",
        "# 文件名称: static_irrigation_quota.txt",
        "# 文件作用: 旱地作物月度灌溉定额",
        "# 数据来源: 灌溉制度.xlsx（自动转换生成）",
        "# 单位说明: 定额(m³/km²/月)，原始数据为 m³/亩 已乘以 1500",
        f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "# ============================================================",
        "",
        "作物\t保证率\t1月\t2月\t3月\t4月\t5月\t6月\t7月\t8月\t9月\t10月\t11月\t12月\t合计"
    ]
    
    current_crop = None
    for idx in range(3, len(df)):
        row = df.iloc[idx]
        
        # 新作物
        if pd.notna(row[0]) and str(row[0]).strip():
            current_crop = str(row[0]).strip()
        
        if current_crop and pd.notna(row[1]):
            prob = row[1]
            # 月份数据：从 m³/亩 转为 m³/km²（乘以 1500）
            months = []
            total_converted = 0
            for col in range(2, 14):
                val = row[col]
                if pd.notna(val):
                    converted = int(float(val) * MU_PER_KM2)
                    months.append(str(converted))
                    total_converted += converted
                else:
                    months.append('0')
            
            line = f"{current_crop}\t{prob}\t" + '\t'.join(months) + f"\t{total_converted}"
            lines.append(line)
    
    with open('static_irrigation_quota.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print("生成: static_irrigation_quota.txt (定额已转为 m³/km²)")


def generate_compatible_files(df_rice):
    """生成兼容现有程序的水稻灌溉制度文件"""
    
    print("\n生成水稻灌溉制度文件...")
    
    # 经验参数（蒸发系数和水位控制）
    period_params = {
        '泡田期': (1.0, 20.0, 40.0, 50.0),
        '返青': (1.0, 10.0, 30.0, 40.0),
        '分蘖前': (1.2, 10.0, 30.0, 40.0),
        '分蘖末': (1.3, 5.0, 25.0, 45.0),
        '拔节育穗期': (1.45, 10.0, 30.0, 60.0),
        '抽穗开花期': (1.5, 10.0, 30.0, 60.0),
        '乳熟期': (1.4, 10.0, 30.0, 60.0),
        '黄熟期': (0.8, -20.0, 0.0, 10.0),
    }
    winter_params = (0.5, -45.0, -25.0, 0.0)
    
    def write_rice_file(rice_type, output_file, df_data):
        data = df_data[df_data['作物'] == rice_type].copy()
        if len(data) == 0:
            return
        
        lines = [
            f"# {rice_type}灌溉制度表",
            "",
            "开始日期        结束日期        生长天数  蒸发系数  水位下限(mm)  设计蓄水位(mm)  水位上限(mm)",
            "----------  ----------  ------  ----  --------  ---------  --------"
        ]
        
        # 获取年份
        first_date = data.iloc[0]['开始日期']
        year = int(first_date.split('/')[0])
        
        # 添加年初冬季
        first_start = datetime.strptime(data.iloc[0]['开始日期'], '%Y/%m/%d')
        if first_start > datetime(year, 1, 1):
            winter_end = first_start - timedelta(days=1)
            days = (winter_end - datetime(year, 1, 1)).days + 1
            lines.append(f"{year}/01/01  {winter_end.strftime('%Y/%m/%d')}  {days:<6}  {winter_params[0]:<4}  {winter_params[1]:<8}  {winter_params[2]:<9}  {winter_params[3]:<8}")
        
        # 添加生育期
        for _, row in data.iterrows():
            period = row['生育期']
            params = period_params.get(period, winter_params)
            days = int(row['天数']) if row['天数'] > 0 else 1
            lines.append(f"{row['开始日期']}  {row['结束日期']}  {days:<6}  {params[0]:<4}  {params[1]:<8}  {params[2]:<9}  {params[3]:<8}")
        
        # 添加年末冬季
        last_end = datetime.strptime(data.iloc[-1]['结束日期'], '%Y/%m/%d')
        year_end = datetime(year, 12, 31)
        if last_end < year_end:
            winter_start = last_end + timedelta(days=1)
            days = (year_end - winter_start).days + 1
            lines.append(f"{winter_start.strftime('%Y/%m/%d')}  {year}/12/31  {days:<6}  {winter_params[0]:<4}  {winter_params[1]:<8}  {winter_params[2]:<9}  {winter_params[3]:<8}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
        print(f"生成: {output_file} (兼容现有程序)")
    
    write_rice_file('单季稻', 'static_single_crop.txt', df_rice)
    
    # 双季稻 = 早稻 + 晚稻
    df_double = pd.concat([
        df_rice[df_rice['作物'] == '早稻'],
        df_rice[df_rice['作物'] == '晚稻']
    ])
    df_double['作物'] = '双季稻'
    write_rice_file('双季稻', 'static_double_crop.txt', df_double)


def add_header_to_txt_files():
    """给输入文件添加注释头（不修改数据）"""
    
    # 文件说明配置（这些文件不是由 xlsx 生成的，只添加注释头）
    file_configs = {
        'in_dry_crop_area.txt': {
            'name': '旱地作物种植面积',
            'desc': '各灌区旱地作物种植面积和保证率配置（手动维护）',
            'unit': '面积(km²)；保证率(50/75/90)',
            'source': '用户配置'
        },
        'in_JYGC.txt': {
            'name': '降雨量数据',
            'desc': '各灌区逐日降雨量预测/实测数据',
            'unit': '降雨量(mm/日)',
            'source': '气象数据'
        },
        'in_ZFGC.txt': {
            'name': '蒸发量数据',
            'desc': '各灌区逐日蒸发量预测/实测数据',
            'unit': '蒸发量(mm/日)',
            'source': '气象数据'
        },
        'in_TIME.txt': {
            'name': '时间配置',
            'desc': '计算起始日期和预测天数',
            'unit': '日期(YYYY/MM/DD)，天数(整数)',
            'source': '用户配置'
        },
        'static_fenqu.txt': {
            'name': '灌区分区数据',
            'desc': '各灌区基础面积和参数配置',
            'unit': '面积(km²)，渗漏(mm/日)，批次(整数)',
            'source': '基础数据'
        }
    }
    
    for filename, config in file_configs.items():
        if not os.path.exists(filename):
            continue
        
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 跳过已有注释头的文件
        if content.startswith('#'):
            continue
        
        header = [
            "# ============================================================",
            f"# 文件名称: {filename}",
            f"# 文件作用: {config['name']}",
            f"# 数据说明: {config['desc']}",
            f"# 单位说明: {config['unit']}",
            f"# 数据来源: {config['source']}",
            "# ============================================================",
            ""
        ]
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(header) + content)
        
        print(f"添加注释头: {filename}")


def main():
    # 切换到脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("=" * 50)
    print("      Excel → TXT 转换")
    print("=" * 50)
    print()
    
    # 转换 Excel 文件
    df_rice = convert_rice_growth()
    convert_irrigation_schedule()
    generate_compatible_files(df_rice)
    
    # 给输入文件添加注释头（不修改数据）
    print()
    add_header_to_txt_files()
    
    print()
    print("=" * 50)
    print("完成!")
    print()
    print("【由 xlsx 生成的文件】")
    print("  - static_irrigation_quota.txt  (旱地作物月度定额, m³/km²)")
    print("  - static_single_crop.txt       (单季稻灌溉制度)")
    print("  - static_double_crop.txt       (双季稻灌溉制度)")
    print()
    print("【添加注释头的文件】（数据不变）")
    print("  - in_dry_crop_area.txt  (旱地面积配置, km²)")
    print("  - in_JYGC.txt           (降雨量, mm/日)")
    print("  - in_ZFGC.txt           (蒸发量, mm/日)")
    print("  - in_TIME.txt           (时间配置)")
    print("  - static_fenqu.txt      (分区数据, km²)")
    print("=" * 50)


if __name__ == '__main__':
    main()

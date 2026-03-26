#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xlsx 转 csv 脚本

将原始年报 xlsx 拆分为细粒度 CSV：
- 命名格式：{年份}_{市}_{表名}.csv
- 表名：县级套四级分区、表1主要社会经济指标、表11供水量、表12用水量
- 按市拆分

使用：
    python -m src.convert
    python -m src.convert --force  # 强制重新生成
"""

import pandas as pd
from pathlib import Path
import re
from typing import Optional, List, Tuple


# 项目路径
PROJECT_ROOT = Path(__file__).parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
INPUT_DIR = PROJECT_ROOT / "data" / "input"

# 需要处理的表名映射（sheet 关键字 -> 输出文件名）
SHEET_MAPPING = {
    "县级套四级分区": "县级套四级分区",
    "表1主要社会经济指标": "社会经济指标",
    "社会经济": "社会经济指标",  # 2024年的格式
    "表11供水量": "供水量",
    "供水量": "供水量",  # 2024年的格式
    "表12用水量": "用水量",
    "用水量": "用水量",  # 2024年的格式
}


def extract_year_from_filename(filename: str) -> Optional[int]:
    """从文件名提取年份"""
    match = re.search(r"(\d{4})年", filename)
    if match:
        return int(match.group(1))
    return None


def find_matching_sheet(sheet_names: List[str], keyword: str) -> Optional[str]:
    """根据关键字查找匹配的 sheet"""
    for name in sheet_names:
        if keyword in name:
            return name
    return None


def clean_city_name(city: str) -> Optional[str]:
    """清理市名"""
    if pd.isna(city):
        return None
    city = str(city).split("-")[0].strip()
    # 标准化市名
    if city and city not in ["市", "NaN", "nan", ""]:
        if not city.endswith("市"):
            city = city + "市"
        return city
    return None


def process_sheet(df: pd.DataFrame, year: int, sheet_type: str) -> List[Tuple[str, pd.DataFrame]]:
    """
    处理单个 sheet，按市拆分
    
    Returns:
        List of (city_name, dataframe) tuples
    """
    results = []
    
    # 找到"市"列
    city_col = None
    for col in df.columns:
        col_str = str(col).strip()
        if col_str == "市" or "市" in col_str[:3]:
            city_col = col
            break
    
    if city_col is None:
        print(f"    ⚠️ 未找到'市'列，跳过")
        return results
    
    # 向下填充市名（处理合并单元格）
    df[city_col] = df[city_col].ffill()
    
    # 清理市名
    df["_市_cleaned"] = df[city_col].apply(clean_city_name)
    
    # 过滤掉无效的市
    df = df[df["_市_cleaned"].notna()]
    
    # 按市分组
    for city in df["_市_cleaned"].unique():
        if city:
            city_df = df[df["_市_cleaned"] == city].copy()
            # 删除临时列
            city_df = city_df.drop(columns=["_市_cleaned"])
            results.append((city, city_df))
    
    return results


def convert_xlsx_to_csv(xlsx_path: Path, force: bool = False) -> int:
    """
    转换单个 xlsx 文件
    
    Returns:
        生成的 CSV 文件数量
    """
    year = extract_year_from_filename(xlsx_path.name)
    if year is None:
        print(f"⚠️ 无法提取年份: {xlsx_path.name}")
        return 0
    
    print(f"\n📊 处理: {year}年")
    
    try:
        xlsx = pd.ExcelFile(xlsx_path)
        sheet_names = xlsx.sheet_names
        print(f"  Sheets: {sheet_names}")
    except Exception as e:
        print(f"  ❌ 读取失败: {e}")
        return 0
    
    count = 0
    
    # 遍历需要处理的表
    for keyword, output_name in SHEET_MAPPING.items():
        sheet_name = find_matching_sheet(sheet_names, keyword)
        if sheet_name is None:
            continue
        
        print(f"  📋 处理 sheet: {sheet_name} -> {output_name}")
        
        try:
            # 读取 sheet
            df = pd.read_excel(xlsx, sheet_name=sheet_name, header=None)
            
            # 跳过标题行（通常前1-2行是表头）
            # 找到数据起始行
            header_row = 0
            for i in range(min(5, len(df))):
                row = df.iloc[i]
                if any("市" in str(v) for v in row.values if pd.notna(v)):
                    header_row = i
                    break
            
            # 设置表头
            if header_row > 0:
                # 合并多行表头
                headers = []
                for col_idx in range(len(df.columns)):
                    parts = []
                    for row_idx in range(header_row + 1):
                        val = df.iloc[row_idx, col_idx]
                        if pd.notna(val):
                            val_str = str(val).strip().replace("\n", "")
                            if val_str and val_str not in parts:
                                parts.append(val_str)
                    headers.append("_".join(parts) if parts else f"col_{col_idx}")
                
                df = df.iloc[header_row + 1:].copy()
                df.columns = headers
            else:
                df.columns = [str(c).strip().replace("\n", "") for c in df.iloc[0]]
                df = df.iloc[1:].copy()
            
            df = df.reset_index(drop=True)
            
            # 删除全空行
            df = df.dropna(how="all")
            
            # 按市拆分
            city_dfs = process_sheet(df, year, output_name)
            
            for city, city_df in city_dfs:
                # 生成文件名
                filename = f"{year}_{city}_{output_name}.csv"
                output_path = INPUT_DIR / filename
                
                # 检查是否需要重新生成
                if not force and output_path.exists():
                    print(f"    ⏭️ 跳过（已存在）: {filename}")
                    continue
                
                # 保存 CSV
                city_df.to_csv(output_path, index=False, encoding="utf-8-sig")
                print(f"    ✅ 生成: {filename} ({len(city_df)} 行)")
                count += 1
                
        except Exception as e:
            print(f"    ❌ 处理失败: {e}")
            import traceback
            traceback.print_exc()
    
    return count


def convert_all(force: bool = False) -> int:
    """
    转换所有 xlsx 文件
    
    Returns:
        生成的 CSV 文件总数
    """
    print("🚀 开始转换 xlsx → csv")
    print(f"📁 输入目录: {RAW_DATA_DIR}")
    print(f"📁 输出目录: {INPUT_DIR}")
    
    # 确保输出目录存在
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 获取所有 xlsx 文件
    xlsx_files = sorted(RAW_DATA_DIR.glob("*.xlsx"))
    xlsx_files = [f for f in xlsx_files if not f.name.startswith("~$")]
    
    if not xlsx_files:
        print("❌ 未找到任何 xlsx 文件")
        return 0
    
    print(f"📊 找到 {len(xlsx_files)} 个文件")
    
    total = 0
    for xlsx_path in xlsx_files:
        count = convert_xlsx_to_csv(xlsx_path, force)
        total += count
    
    print(f"\n✅ 转换完成，共生成 {total} 个 CSV 文件")
    return total


def list_csv_files() -> List[Path]:
    """列出所有生成的 CSV 文件"""
    return sorted(INPUT_DIR.glob("*.csv"))


def get_available_years() -> List[int]:
    """获取可用的年份"""
    years = set()
    for f in list_csv_files():
        match = re.match(r"(\d{4})_", f.name)
        if match:
            years.add(int(match.group(1)))
    return sorted(years)


def get_available_cities() -> List[str]:
    """获取可用的市"""
    cities = set()
    for f in list_csv_files():
        match = re.match(r"\d{4}_(.+?)_", f.name)
        if match:
            cities.add(match.group(1))
    return sorted(cities)


def get_available_tables() -> List[str]:
    """获取可用的表名"""
    tables = set()
    for f in list_csv_files():
        match = re.match(r"\d{4}_.+?_(.+)\.csv", f.name)
        if match:
            tables.add(match.group(1))
    return sorted(tables)


if __name__ == "__main__":
    import sys
    
    force = "--force" in sys.argv
    
    convert_all(force=force)
    
    print("\n" + "=" * 50)
    print("📊 统计信息:")
    print(f"  年份: {get_available_years()}")
    print(f"  市: {get_available_cities()}")
    print(f"  表: {get_available_tables()}")
    print(f"  总文件数: {len(list_csv_files())}")



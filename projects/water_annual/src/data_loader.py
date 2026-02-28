#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据加载模块 - 按需加载拆分后的 CSV 文件

功能：
1. 读取 data/input/ 下的 CSV 文件
2. 支持按年份、市、表名筛选
3. 自动合并多个文件

CSV 命名格式：{年份}_{市}_{表名}.csv
例如：2020_湖州市_用水量.csv
"""

import pandas as pd
from pathlib import Path
import re
from typing import List, Optional


# 项目路径
PROJECT_ROOT = Path(__file__).parent.parent
INPUT_DIR = PROJECT_ROOT / "data" / "input"


# 正式的 11 个市（过滤掉"其中杭州市"、"杭嘉湖区市"等）
VALID_CITIES = [
    "杭州市", "宁波市", "温州市", "嘉兴市", "湖州市",
    "绍兴市", "金华市", "衢州市", "舟山市", "台州市", "丽水市"
]


def list_csv_files() -> List[Path]:
    """列出所有 CSV 文件"""
    return sorted(INPUT_DIR.glob("*.csv"))


def get_available_years() -> List[int]:
    """获取可用的年份"""
    years = set()
    for f in list_csv_files():
        match = re.match(r"(\d{4})_", f.name)
        if match:
            years.add(int(match.group(1)))
    return sorted(years)


def get_available_cities(only_valid: bool = True) -> List[str]:
    """
    获取可用的市
    
    Args:
        only_valid: 只返回正式的 11 个市，过滤掉"其中杭州市"等
    """
    cities = set()
    for f in list_csv_files():
        match = re.match(r"\d{4}_(.+?)_", f.name)
        if match:
            city = match.group(1)
            if only_valid:
                if city in VALID_CITIES:
                    cities.add(city)
            else:
                cities.add(city)
    return sorted(cities)


def get_available_tables() -> List[str]:
    """获取可用的表名"""
    tables = set()
    for f in list_csv_files():
        match = re.match(r"\d{4}_.+?_(.+)\.csv", f.name)
        if match:
            tables.add(match.group(1))
    return sorted(tables)


def find_csv_file(year: int, city: str, table: str) -> Optional[Path]:
    """查找特定 CSV 文件"""
    filename = f"{year}_{city}_{table}.csv"
    path = INPUT_DIR / filename
    return path if path.exists() else None


def load_csv(
    years: Optional[List[int]] = None,
    cities: Optional[List[str]] = None,
    tables: Optional[List[str]] = None,
    add_year_column: bool = True,
    add_city_column: bool = True,
    add_table_column: bool = True,
) -> pd.DataFrame:
    """
    加载并合并 CSV 文件
    
    Args:
        years: 年份列表（None 表示全部）
        cities: 市列表（None 表示全部正式的 11 个市）
        tables: 表名列表（None 表示全部）
        add_year_column: 是否添加年份列
        add_city_column: 是否添加市列
        add_table_column: 是否添加表名列
    
    Returns:
        合并后的 DataFrame
    """
    # 默认值
    if years is None:
        years = get_available_years()
    if cities is None:
        cities = get_available_cities(only_valid=True)
    if tables is None:
        tables = get_available_tables()
    
    dfs = []
    
    for year in years:
        for city in cities:
            for table in tables:
                csv_path = find_csv_file(year, city, table)
                if csv_path is None:
                    continue
                
                try:
                    df = pd.read_csv(csv_path)
                    
                    # 添加标识列
                    if add_year_column:
                        df["年份"] = year
                    if add_city_column:
                        df["市"] = city
                    if add_table_column:
                        df["表名"] = table
                    
                    dfs.append(df)
                except Exception as e:
                    print(f"⚠️ 读取失败 {csv_path.name}: {e}")
    
    if not dfs:
        return pd.DataFrame()
    
    return pd.concat(dfs, ignore_index=True)


def load_table(
    table: str,
    years: Optional[List[int]] = None,
    cities: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    加载特定表的数据
    
    Args:
        table: 表名（县级套四级分区、社会经济指标、供水量、用水量）
        years: 年份列表（None 表示全部）
        cities: 市列表（None 表示全部）
    
    Returns:
        合并后的 DataFrame
    """
    return load_csv(
        years=years,
        cities=cities,
        tables=[table],
        add_table_column=False,
    )


def get_file_stats() -> dict:
    """获取文件统计信息"""
    all_files = list_csv_files()
    
    # 按年份统计
    by_year = {}
    for f in all_files:
        match = re.match(r"(\d{4})_", f.name)
        if match:
            year = match.group(1)
            by_year[year] = by_year.get(year, 0) + 1
    
    # 按市统计（只统计正式的 11 个市）
    by_city = {}
    for f in all_files:
        match = re.match(r"\d{4}_(.+?)_", f.name)
        if match:
            city = match.group(1)
            if city in VALID_CITIES:
                by_city[city] = by_city.get(city, 0) + 1
    
    # 按表统计
    by_table = {}
    for f in all_files:
        match = re.match(r"\d{4}_.+?_(.+)\.csv", f.name)
        if match:
            table = match.group(1)
            by_table[table] = by_table.get(table, 0) + 1
    
    return {
        "total": len(all_files),
        "by_year": by_year,
        "by_city": by_city,
        "by_table": by_table,
    }


if __name__ == "__main__":
    print("📊 CSV 文件统计")
    print("=" * 50)
    
    stats = get_file_stats()
    print(f"总文件数: {stats['total']}")
    print(f"\n年份: {get_available_years()}")
    print(f"市: {get_available_cities()}")
    print(f"表: {get_available_tables()}")
    
    print("\n" + "=" * 50)
    print("📋 按年份统计:")
    for year, count in sorted(stats["by_year"].items()):
        print(f"  {year}: {count} 个文件")
    
    print("\n📋 按市统计:")
    for city, count in sorted(stats["by_city"].items()):
        print(f"  {city}: {count} 个文件")
    
    print("\n📋 按表统计:")
    for table, count in sorted(stats["by_table"].items()):
        print(f"  {table}: {count} 个文件")
    
    # 测试加载
    print("\n" + "=" * 50)
    print("🧪 测试加载: 湖州市 2019-2024 用水量")
    df = load_table(
        table="用水量",
        years=[2019, 2020, 2021, 2022, 2023, 2024],
        cities=["湖州市"],
    )
    print(f"加载行数: {len(df)}")
    if len(df) > 0:
        print(f"列: {list(df.columns)[:10]}...")

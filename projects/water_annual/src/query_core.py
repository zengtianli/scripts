#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询模块 - 按条件筛选数据

功能：
1. 按市、县区筛选
2. 按年份筛选
3. 按指标筛选
4. 汇总统计
"""

import pandas as pd
from typing import List, Optional


def query_data(
    df: pd.DataFrame,
    cities: Optional[List[str]] = None,
    counties: Optional[List[str]] = None,
    years: Optional[List[int]] = None,
    indicators: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    按条件筛选数据
    
    Args:
        df: 原始数据
        cities: 市列表（None 表示全部）
        counties: 县区列表（None 表示全部）
        years: 年份列表（None 表示全部）
        indicators: 指标列表（None 表示全部）
    
    Returns:
        筛选后的 DataFrame
    """
    result = df.copy()
    
    # 按市筛选
    if cities:
        result = result[result["市"].isin(cities)]
    
    # 按县区筛选
    if counties:
        result = result[result["县区"].isin(counties)]
    
    # 按年份筛选
    if years:
        result = result[result["年份"].isin(years)]
    
    # 选择列
    base_cols = ["年份", "市", "县区", "三级分区", "四级分区"]
    
    if indicators:
        # 只保留指定的指标列
        cols = base_cols + [col for col in indicators if col in result.columns]
    else:
        # 保留所有列
        cols = [col for col in result.columns if col in base_cols or col not in ["三级分区", "四级分区"]]
    
    # 确保列存在
    cols = [col for col in cols if col in result.columns]
    result = result[cols]
    
    # 按年份和市排序
    result = result.sort_values(["年份", "市", "县区"]).reset_index(drop=True)
    
    return result


def aggregate_by_city(
    df: pd.DataFrame,
    indicators: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    按市汇总数据
    
    Args:
        df: 筛选后的数据
        indicators: 指标列表
    
    Returns:
        汇总后的 DataFrame（行=年份，列=市）
    """
    if indicators is None:
        indicators = [col for col in df.columns if col not in ["年份", "市", "县区", "三级分区", "四级分区"]]
    
    # 按年份和市汇总
    result = df.groupby(["年份", "市"])[indicators].sum().reset_index()
    
    return result


def aggregate_by_year(
    df: pd.DataFrame,
    group_by: str = "市",
    indicators: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    按年份汇总，生成透视表
    
    Args:
        df: 筛选后的数据
        group_by: 分组字段（"市" 或 "县区"）
        indicators: 指标列表（只取第一个指标做透视）
    
    Returns:
        透视表（行=地区，列=年份）
    """
    if indicators is None or len(indicators) == 0:
        return pd.DataFrame()
    
    indicator = indicators[0]  # 只取第一个指标
    
    if indicator not in df.columns:
        return pd.DataFrame()
    
    # 按分组字段汇总
    agg_df = df.groupby(["年份", group_by])[indicator].sum().reset_index()
    
    # 透视
    pivot = agg_df.pivot(index=group_by, columns="年份", values=indicator)
    pivot = pivot.reset_index()
    
    # 添加合计列
    year_cols = [col for col in pivot.columns if isinstance(col, (int, float))]
    if year_cols:
        pivot["合计"] = pivot[year_cols].sum(axis=1)
        pivot["平均"] = pivot[year_cols].mean(axis=1).round(4)
    
    return pivot


def calculate_stats(df: pd.DataFrame, indicator: str) -> dict:
    """
    计算统计信息
    
    Args:
        df: 数据
        indicator: 指标名
    
    Returns:
        统计信息字典
    """
    if indicator not in df.columns:
        return {}
    
    values = df[indicator].dropna()
    
    return {
        "总计": round(values.sum(), 4),
        "平均": round(values.mean(), 4),
        "最大": round(values.max(), 4),
        "最小": round(values.min(), 4),
        "记录数": len(values),
    }


def compare_years(
    df: pd.DataFrame,
    year1: int,
    year2: int,
    group_by: str = "县区",
    indicators: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    对比两个年份的数据变化
    
    Args:
        df: 数据
        year1: 基准年
        year2: 对比年
        group_by: 分组字段
        indicators: 指标列表
    
    Returns:
        对比结果（包含变化量和变化率）
    """
    if indicators is None:
        indicators = ["总用水量"]
    
    df1 = df[df["年份"] == year1].copy()
    df2 = df[df["年份"] == year2].copy()
    
    # 按分组字段汇总
    agg1 = df1.groupby(group_by)[indicators].sum().reset_index()
    agg2 = df2.groupby(group_by)[indicators].sum().reset_index()
    
    # 合并
    result = agg1.merge(agg2, on=group_by, suffixes=(f"_{year1}", f"_{year2}"), how="outer")
    
    # 计算变化
    for ind in indicators:
        col1 = f"{ind}_{year1}"
        col2 = f"{ind}_{year2}"
        if col1 in result.columns and col2 in result.columns:
            result[f"{ind}_变化量"] = result[col2] - result[col1]
            result[f"{ind}_变化率%"] = ((result[col2] - result[col1]) / result[col1] * 100).round(2)
    
    return result



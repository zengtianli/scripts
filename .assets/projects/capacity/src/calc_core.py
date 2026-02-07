#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================
# 脚本名称: calc_core.py
# 功能描述: 水环境功能区纳污能力核心计算（CSV → CSV）
# 来源工单: 水利公司需求
# 创建日期: 2025-12-18
# 更新日期: 2025-12-18 - 修正公式，简化为单一Cs/C0
# 作者: 开发部
# ============================================================
"""
核心计算模块 - 只处理 CSV 文件

河道纳污能力公式：
  W = 31.536 × b × (Cs - C0 × exp(-KL/u)) × (Q×K×L/u) / (1 - exp(-KL/u))

水库纳污能力公式：
  W = 31.536 × K × V × Cs × b

流速公式：
  u = a × Q^β
"""

import pandas as pd
import numpy as np
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
import math

# ============================================================
# 常量
# ============================================================
UNIT_FACTOR = 31.536  # 单位换算系数（秒→年，mg→t）


# ============================================================
# 数据结构
# ============================================================
@dataclass
class Zone:
    """河道功能区参数"""
    zone_id: str        # 功能区编号
    name: str           # 名称
    water_class: str    # 水质类别
    length: float       # 河段长度 L (m)
    K: float            # 衰减系数 K (1/s)
    b: float            # 不均匀系数 b
    a: float            # 流速系数 a
    beta: float         # 流速指数 β
    Cs: float           # 目标浓度 (mg/L)
    C0: float           # 初始浓度 (mg/L)


@dataclass
class ReservoirZone:
    """水库功能区参数"""
    zone_id: str        # 功能区编号
    name: str           # 名称
    K: float            # 污染物综合衰减系数 K (1/s)
    b: float            # 不均匀系数 b
    Cs: float           # 目标浓度 (mg/L)
    C0: float           # 初始浓度 (mg/L)，保留字段


# ============================================================
# 读取函数
# ============================================================
def read_zones(csv_path: Path) -> List[Zone]:
    """读取功能区基础信息"""
    df = pd.read_csv(csv_path)
    zones = []
    for _, row in df.iterrows():
        zone = Zone(
            zone_id=str(row['功能区']),
            name=str(row['名称']),
            water_class=str(row['水质类别']),
            length=float(row['河段长度L(m)']),
            K=float(row['衰减系数K(1/s)']),
            b=float(row['不均匀系数b']),
            a=float(row['a']),
            beta=float(row['β']),
            Cs=float(row['Cs']) if pd.notna(row.get('Cs')) else 0.0,
            C0=float(row['C0']) if pd.notna(row.get('C0')) else 0.0,
        )
        zones.append(zone)
    return zones


def read_daily_flow(csv_path: Path) -> pd.DataFrame:
    """读取逐日流量"""
    df = pd.read_csv(csv_path)
    df['日期'] = df['日期'].apply(parse_date)
    return df


def parse_date(val):
    """解析日期（处理混合格式：字符串日期 + Excel序列号）"""
    try:
        return pd.to_datetime(val)
    except:
        try:
            return pd.Timestamp('1899-12-30') + pd.Timedelta(days=float(val))
        except:
            return pd.NaT


def read_reservoir_zones(csv_path: Path) -> List[ReservoirZone]:
    """读取水库功能区基础信息"""
    if not csv_path.exists():
        return []
    df = pd.read_csv(csv_path)
    zones = []
    for _, row in df.iterrows():
        zone = ReservoirZone(
            zone_id=str(row['功能区']),
            name=str(row['名称']),
            K=float(row['K(1/s)']),
            b=float(row['b']),
            Cs=float(row['Cs']) if pd.notna(row.get('Cs')) else 0.0,
            C0=float(row['C0']) if pd.notna(row.get('C0')) else 0.0,
        )
        zones.append(zone)
    return zones


def read_reservoir_volume(csv_path: Path) -> pd.DataFrame:
    """读取水库逐日库容"""
    if not csv_path.exists():
        return pd.DataFrame()
    df = pd.read_csv(csv_path)
    df['日期'] = df['日期'].apply(parse_date)
    return df


# ============================================================
# 计算函数
# ============================================================
def calc_monthly_flow(daily_flow: pd.DataFrame, zone_ids: List[str]) -> pd.DataFrame:
    """计算逐月流量（月平均）"""
    df = daily_flow.copy()
    df['年'] = df['日期'].dt.year
    df['月'] = df['日期'].dt.month
    monthly = df.groupby(['年', '月'])[zone_ids].mean().reset_index()
    return monthly


def calc_velocity(Q: float, a: float, beta: float) -> float:
    """计算流速: u = a × Q^β"""
    if Q <= 0:
        return 0.0
    return a * (Q ** beta)


def calc_monthly_velocity(monthly_flow: pd.DataFrame, zones: List[Zone]) -> pd.DataFrame:
    """计算逐月流速"""
    result = monthly_flow[['年', '月']].copy()
    for zone in zones:
        velocities = []
        for _, row in monthly_flow.iterrows():
            Q = row[zone.zone_id]
            u = calc_velocity(Q, zone.a, zone.beta)
            velocities.append(u)
        result[zone.zone_id] = velocities
    return result


def calc_capacity_value(Cs: float, C0: float, Q: float, u: float, 
                        K: float, L: float, b: float) -> float:
    """
    计算河道纳污能力
    
    公式: W = 31.536 × b × (Cs - C0 × exp(-KL/u)) × (Q×K×L/u) / (1 - exp(-KL/u))
    
    Args:
        Cs: 目标浓度 (mg/L)
        C0: 初始浓度 (mg/L)
        Q: 流量 (m³/s)
        u: 流速 (m/s)
        K: 衰减系数 (1/s)
        L: 河段长度 (m)
        b: 不均匀系数
    
    Returns:
        W: 纳污能力 (t/a)
    """
    if u <= 0 or Q <= 0:
        return 0.0
    
    # 计算衰减因子
    decay = math.exp(-K * L / u)
    
    # 避免除零
    if decay >= 1.0 - 1e-10:
        return 0.0
    
    # 浓度项: (Cs - C0 × decay)
    concentration_term = Cs - C0 * decay
    
    # 流量项: (Q × K × L / u) / (1 - decay)
    flow_term = (Q * K * L / u) / (1 - decay)
    
    # 纳污能力
    W = UNIT_FACTOR * b * concentration_term * flow_term
    
    return max(W, 0.0)  # 确保非负


def calc_outflow_concentration(C0: float, K: float, L: float, u: float) -> float:
    """
    计算出流浓度（用于链式传递）
    C = C0 × exp(-K × L / u)
    """
    if u <= 0:
        return C0
    return C0 * math.exp(-K * L / u)


def calc_monthly_capacity(monthly_flow: pd.DataFrame, monthly_velocity: pd.DataFrame,
                          zones: List[Zone]) -> pd.DataFrame:
    """
    计算逐月纳污能力（链式计算）
    
    每个功能区使用自己的 C0（如有），否则使用上游出流浓度
    """
    result = monthly_flow[['年', '月']].copy()
    
    for zone in zones:
        result[zone.zone_id] = 0.0
    
    # 逐行（逐月）计算
    for idx, row in monthly_flow.iterrows():
        C_current = 0.0  # 当前浓度（从上游传递）
        
        for i, zone in enumerate(zones):
            Q = row[zone.zone_id]
            u = monthly_velocity.loc[idx, zone.zone_id]
            
            # 使用该功能区的 C0（如有），否则使用上游传递的浓度
            if zone.C0 > 0:
                C0_use = zone.C0
            elif i == 0:
                # 首个功能区必须有 C0
                C0_use = zone.C0 if zone.C0 > 0 else 0.0
            else:
                C0_use = C_current
            
            # 计算纳污能力
            W = calc_capacity_value(zone.Cs, C0_use, Q, u, zone.K, zone.length, zone.b)
            result.loc[idx, zone.zone_id] = W
            
            # 计算出流浓度，传递给下游
            C_current = calc_outflow_concentration(C0_use, zone.K, zone.length, u)
    
    return result


def calc_zone_monthly_avg(df: pd.DataFrame, zone_ids: List[str], is_capacity: bool = False) -> pd.DataFrame:
    """
    计算功能区月平均值（多年平均）
    
    输入: 年 | 月 | zone1 | zone2 | ...
    输出: 功能区 | 1月 | 2月 | ... | 12月 | 年平均/年合计
    """
    monthly_avg = df.groupby('月')[zone_ids].mean()
    result = monthly_avg.T
    result.columns = [f'{m}月' for m in result.columns]
    result.index.name = '功能区'
    result = result.reset_index()
    
    month_cols = [f'{m}月' for m in range(1, 13)]
    existing_cols = [c for c in month_cols if c in result.columns]
    if is_capacity:
        result['年合计'] = result[existing_cols].sum(axis=1)
    else:
        result['年平均'] = result[existing_cols].mean(axis=1)
    
    return result


# ============================================================
# 水库计算函数
# ============================================================
def get_hydro_year(date) -> int:
    """获取水文年（4月→次年3月）"""
    if date.month >= 4:
        return date.year
    else:
        return date.year - 1


def calc_reservoir_monthly_volume(daily_volume: pd.DataFrame, zone_ids: List[str]) -> pd.DataFrame:
    """计算水库逐月库容（按水文年）"""
    df = daily_volume.copy()
    df['水文年'] = df['日期'].apply(get_hydro_year)
    df['月'] = df['日期'].dt.month
    monthly = df.groupby(['水文年', '月'])[zone_ids].mean().reset_index()
    return monthly


def calc_reservoir_capacity_value(K: float, Cs: float, V: float, b: float) -> float:
    """
    计算水库纳污能力
    
    公式: W = 31.536 × K × V × Cs × b
    
    Args:
        K: 污染物综合衰减系数 (1/s)
        Cs: 目标浓度 (mg/L)
        V: 库容 (m³)
        b: 不均匀系数
    
    Returns:
        W: 纳污能力 (t/a)
    """
    if V <= 0 or Cs <= 0:
        return 0.0
    return UNIT_FACTOR * K * V * Cs * b


def calc_reservoir_monthly_capacity(monthly_volume: pd.DataFrame,
                                    zones: List[ReservoirZone]) -> pd.DataFrame:
    """计算水库逐月纳污能力"""
    result = monthly_volume[['水文年', '月']].copy()
    
    for zone in zones:
        capacities = []
        for _, row in monthly_volume.iterrows():
            V = row[zone.zone_id]
            W = calc_reservoir_capacity_value(zone.K, zone.Cs, V, zone.b)
            capacities.append(W)
        result[zone.zone_id] = capacities
    
    return result


def calc_reservoir_zone_monthly_avg(df: pd.DataFrame, zone_ids: List[str]) -> pd.DataFrame:
    """计算水库功能区月平均纳污能力（按水文年顺序：4月→3月）"""
    monthly_avg = df.groupby('月')[zone_ids].mean()
    result = monthly_avg.T
    
    hydro_month_order = [4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3]
    result = result[[m for m in hydro_month_order if m in result.columns]]
    result.columns = [f'{m}月' for m in result.columns]
    result.index.name = '功能区'
    result = result.reset_index()
    
    month_cols = [f'{m}月' for m in hydro_month_order]
    existing_cols = [c for c in month_cols if c in result.columns]
    result['年合计'] = result[existing_cols].sum(axis=1)
    
    return result


# ============================================================
# 保存函数
# ============================================================
def save_river_results(output_dir: Path, monthly_flow: pd.DataFrame, monthly_velocity: pd.DataFrame,
                       zone_avg_velocity: pd.DataFrame, zone_avg_capacity: pd.DataFrame):
    """保存河道计算结果到 CSV"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    monthly_flow.to_csv(output_dir / '逐月流量.csv', index=False, encoding='utf-8-sig')
    monthly_velocity.to_csv(output_dir / '逐月流速.csv', index=False, encoding='utf-8-sig')
    zone_avg_velocity.to_csv(output_dir / '功能区月平均流速.csv', index=False, encoding='utf-8-sig')
    zone_avg_capacity.to_csv(output_dir / '功能区月平均纳污能力.csv', index=False, encoding='utf-8-sig')
    
    print(f"✓ 河道结果已保存到 {output_dir}/")


def save_reservoir_results(output_dir: Path, monthly_volume: pd.DataFrame,
                           zone_avg_capacity: pd.DataFrame):
    """保存水库计算结果到 CSV"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    monthly_volume.to_csv(output_dir / '水库逐月库容.csv', index=False, encoding='utf-8-sig')
    zone_avg_capacity.to_csv(output_dir / '水库功能区月平均纳污能力.csv', index=False, encoding='utf-8-sig')
    
    print(f"✓ 水库结果已保存到 {output_dir}/")


# ============================================================
# 主函数
# ============================================================
def main(input_dir: Path = None, output_dir: Path = None):
    """主计算流程"""
    base_dir = Path(__file__).parent.parent
    input_dir = input_dir or base_dir / 'csv' / 'input'
    output_dir = output_dir or base_dir / 'csv' / 'output'
    
    print("=" * 60)
    print("水环境功能区纳污能力计算 - 核心计算模块")
    print("=" * 60)
    
    # ========== 河道计算 ==========
    river_zones_path = input_dir / '功能区基础信息.csv'
    if river_zones_path.exists():
        print("\n" + "-" * 60)
        print("【河道计算】")
        print("-" * 60)
        
        # 1. 读取输入
        print("\n[1/5] 读取河道输入数据...")
        zones = read_zones(river_zones_path)
        daily_flow = read_daily_flow(input_dir / '逐日流量.csv')
        zone_ids = [z.zone_id for z in zones]
        print(f"  - 河道功能区数量: {len(zones)}")
        print(f"  - 逐日流量记录: {len(daily_flow)} 天")
        
        # 2. 计算逐月流量
        print("\n[2/5] 计算逐月流量...")
        monthly_flow = calc_monthly_flow(daily_flow, zone_ids)
        print(f"  - 逐月流量记录: {len(monthly_flow)} 月")
        
        # 3. 计算逐月流速
        print("\n[3/5] 计算逐月流速 (u = a × Q^β)...")
        monthly_velocity = calc_monthly_velocity(monthly_flow, zones)
        
        # 4. 计算逐月纳污能力
        print("\n[4/5] 计算纳污能力...")
        print("  公式: W = 31.536 × b × (Cs - C0×exp(-KL/u)) × (QKL/u) / (1 - exp(-KL/u))")
        monthly_capacity = calc_monthly_capacity(monthly_flow, monthly_velocity, zones)
        
        # 5. 计算功能区月平均
        print("\n[5/5] 计算功能区月平均...")
        zone_avg_velocity = calc_zone_monthly_avg(monthly_velocity, zone_ids, is_capacity=False)
        zone_avg_capacity = calc_zone_monthly_avg(monthly_capacity, zone_ids, is_capacity=True)
        
        # 保存河道结果
        save_river_results(output_dir, monthly_flow, monthly_velocity, zone_avg_velocity, zone_avg_capacity)
    else:
        print("\n⚠ 未找到河道功能区数据，跳过河道计算")
    
    # ========== 水库计算 ==========
    reservoir_zones_path = input_dir / '水库功能区基础信息.csv'
    if reservoir_zones_path.exists():
        print("\n" + "-" * 60)
        print("【水库计算】")
        print("-" * 60)
        
        # 1. 读取输入
        print("\n[1/4] 读取水库输入数据...")
        reservoir_zones = read_reservoir_zones(reservoir_zones_path)
        daily_volume = read_reservoir_volume(input_dir / '水库逐日库容.csv')
        reservoir_zone_ids = [z.zone_id for z in reservoir_zones]
        print(f"  - 水库功能区数量: {len(reservoir_zones)}")
        print(f"  - 逐日库容记录: {len(daily_volume)} 天")
        
        # 2. 计算逐月库容（按水文年）
        print("\n[2/4] 计算逐月库容（水文年: 4月→3月）...")
        monthly_volume = calc_reservoir_monthly_volume(daily_volume, reservoir_zone_ids)
        print(f"  - 逐月库容记录: {len(monthly_volume)} 月")
        
        # 3. 计算逐月纳污能力
        print("\n[3/4] 计算水库纳污能力...")
        print("  公式: W = 31.536 × K × V × Cs × b")
        reservoir_monthly_capacity = calc_reservoir_monthly_capacity(monthly_volume, reservoir_zones)
        
        # 4. 计算功能区月平均
        print("\n[4/4] 计算水库功能区月平均...")
        reservoir_zone_avg_capacity = calc_reservoir_zone_monthly_avg(
            reservoir_monthly_capacity, reservoir_zone_ids
        )
        
        # 保存水库结果
        save_reservoir_results(output_dir, monthly_volume, reservoir_zone_avg_capacity)
    else:
        print("\n⚠ 未找到水库功能区数据，跳过水库计算")
    
    print("\n" + "=" * 60)
    print("计算完成!")
    print("=" * 60)


if __name__ == '__main__':
    main()

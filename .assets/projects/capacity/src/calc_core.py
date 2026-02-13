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
from typing import List, Optional, Tuple, Dict
import math

# ============================================================
# 常量
# ============================================================
UNIT_FACTOR = 31.536  # 单位换算系数（秒→年，mg→t）


# ============================================================
# 数据结构
# ============================================================
@dataclass
class Branch:
    """支流信息"""
    name: str              # 支流名称（如 钱塘156-1）
    length: float          # 支流长度 L (m)
    join_position: float   # 汇入干流的位置 (m)
    C0: float              # 支流入口浓度 (mg/L)


@dataclass
class SegmentResult:
    """分段计算结果"""
    name: str        # 段名称
    seg_type: str    # "干流段", "支流", "混合", "汇总"
    length: float    # 长度 (m)
    Q: float         # 流量 (m³/s)
    C0: float        # 入口浓度 (mg/L)
    C_out: float     # 出口浓度 (mg/L)
    W: float         # 纳污能力 (t/a)
    remark: str      # 备注


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
    main_name: str = "" # 干流名称（如 钱塘156-0）
    branches: Optional[List[Branch]] = None  # 支流列表


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
def calc_monthly_flow(daily_flow: pd.DataFrame, flow_columns: List[str]) -> pd.DataFrame:
    """计算逐月流量（月平均），flow_columns 为所有需要聚合的列名"""
    df = daily_flow.copy()
    df['年'] = df['日期'].dt.year
    df['月'] = df['日期'].dt.month
    existing_cols = [c for c in flow_columns if c in df.columns]
    monthly = df.groupby(['年', '月'])[existing_cols].mean().reset_index()
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
    if u <= 0 or L <= 0:
        return C0
    return C0 * math.exp(-K * L / u)


def calc_zone_segments(zone: Zone, main_Q: float,
                       branch_flows: Optional[dict] = None) -> Tuple[List[SegmentResult], float, float]:
    """
    分段计算功能区纳污能力（含支流汇入）

    按 VBA CalcZoneSegments 逻辑：
    1. 按汇入位置排序支流
    2. 干流被支流汇入点切分为多段
    3. 每个混合点按流量加权混合浓度
    4. 只汇总干流段的 W

    Args:
        zone: 功能区参数
        main_Q: 干流流量 (m³/s)
        branch_flows: {支流名: 流量} 字典，None 则无支流

    Returns:
        (segments, total_W, final_C_out)
    """
    segments = []
    branches = zone.branches or []

    # 无支流或无流量 → 整段计算
    if not branches or main_Q <= 0:
        u = calc_velocity(main_Q, zone.a, zone.beta)
        W = calc_capacity_value(zone.Cs, zone.C0, main_Q, u, zone.K, zone.length, zone.b)
        C_out = calc_outflow_concentration(zone.C0, zone.K, zone.length, u)
        seg = SegmentResult(
            name=zone.main_name or zone.name,
            seg_type="干流段", length=zone.length,
            Q=main_Q, C0=zone.C0, C_out=C_out, W=W, remark="整段"
        )
        segments.append(seg)
        # 汇总
        segments.append(SegmentResult(
            name=f"【{zone.name} 小计】", seg_type="汇总",
            length=zone.length, Q=0, C0=zone.C0, C_out=C_out, W=W,
            remark="仅汇总干流段"
        ))
        return segments, W, C_out

    # 按汇入位置排序
    sorted_branches = sorted(branches, key=lambda br: br.join_position)

    current_pos = 0.0
    current_Q = main_Q
    current_C = zone.C0
    main_total_W = 0.0
    total_length = 0.0
    seg_num = 0

    for j, br in enumerate(sorted_branches):
        br_Q = 0.0
        if branch_flows and br.name in branch_flows:
            br_Q = branch_flows[br.name]

        # 干流段：current_pos → 汇入点
        seg_length = br.join_position - current_pos
        if seg_length > 0 and current_Q > 0:
            seg_num += 1
            u = calc_velocity(current_Q, zone.a, zone.beta)
            seg_C_out = calc_outflow_concentration(current_C, zone.K, seg_length, u)
            seg_W = calc_capacity_value(zone.Cs, current_C, current_Q, u, zone.K, seg_length, zone.b)

            remark = "起点→" + br.name + "汇入点" if j == 0 else "上一汇入点→" + br.name + "汇入点"
            segments.append(SegmentResult(
                name=f"{zone.main_name or zone.name}-段{seg_num}",
                seg_type="干流段", length=seg_length,
                Q=current_Q, C0=current_C, C_out=seg_C_out, W=seg_W,
                remark=remark
            ))
            main_total_W += seg_W
            total_length += seg_length
            current_C = seg_C_out

        # 支流自身
        br_C = br.C0
        if br_Q > 0 and br.length > 0:
            br_u = calc_velocity(br_Q, zone.a, zone.beta)
            br_C_out = calc_outflow_concentration(br_C, zone.K, br.length, br_u)
            br_W = calc_capacity_value(zone.Cs, br_C, br_Q, br_u, zone.K, br.length, zone.b)
            segments.append(SegmentResult(
                name=br.name, seg_type="支流", length=br.length,
                Q=br_Q, C0=br_C, C_out=br_C_out, W=br_W,
                remark="(不计入汇总)"
            ))
            br_C_out_final = br_C_out
        else:
            br_C_out_final = br_C

        # 混合点
        if br_Q > 0:
            mixed_Q = current_Q + br_Q
            mixed_C = (current_Q * current_C + br_Q * br_C_out_final) / mixed_Q if mixed_Q > 0 else current_C
            segments.append(SegmentResult(
                name=f"(混合点{j+1})", seg_type="混合", length=0,
                Q=mixed_Q, C0=mixed_C, C_out=0, W=0,
                remark=f"Q={current_Q:.2f}×C={current_C:.4f} + Q={br_Q:.2f}×C={br_C_out_final:.4f}"
            ))
            current_Q = mixed_Q
            current_C = mixed_C

        current_pos = br.join_position

    # 最后一段干流（最后汇入点 → 终点）
    seg_length = zone.length - current_pos
    if seg_length > 0 and current_Q > 0:
        seg_num += 1
        u = calc_velocity(current_Q, zone.a, zone.beta)
        seg_C_out = calc_outflow_concentration(current_C, zone.K, seg_length, u)
        seg_W = calc_capacity_value(zone.Cs, current_C, current_Q, u, zone.K, seg_length, zone.b)
        segments.append(SegmentResult(
            name=f"{zone.main_name or zone.name}-段{seg_num}",
            seg_type="干流段", length=seg_length,
            Q=current_Q, C0=current_C, C_out=seg_C_out, W=seg_W,
            remark="最后汇入点→终点"
        ))
        main_total_W += seg_W
        total_length += seg_length
        final_C_out = seg_C_out
    else:
        final_C_out = current_C

    # 汇总行
    segments.append(SegmentResult(
        name=f"【{zone.name} 小计】", seg_type="汇总",
        length=total_length, Q=0, C0=zone.C0, C_out=final_C_out, W=main_total_W,
        remark="仅汇总干流段"
    ))

    return segments, main_total_W, final_C_out


def calc_monthly_capacity(monthly_flow: pd.DataFrame, monthly_velocity: pd.DataFrame,
                          zones: List[Zone], flow_col_map: Optional[Dict] = None) -> pd.DataFrame:
    """
    计算逐月纳污能力（支持支流分段计算）

    Args:
        monthly_flow: 逐月流量 DataFrame
        monthly_velocity: 逐月流速 DataFrame（仅无支流时使用）
        zones: 功能区列表
        flow_col_map: {zone_id: {"main": col, "branches": [col, ...]}}
                      如果为 None，使用旧的单链模式
    """
    result = monthly_flow[['年', '月']].copy()
    zone_ids = [z.zone_id for z in zones]
    for zid in zone_ids:
        result[zid] = 0.0

    has_branches = flow_col_map is not None and any(
        z.branches for z in zones
    )

    if has_branches:
        # 新模式：逐行逐功能区调用 calc_zone_segments
        for idx, row in monthly_flow.iterrows():
            C_current = 0.0
            for i, zone in enumerate(zones):
                col_info = flow_col_map.get(zone.zone_id, {})
                main_col = col_info.get("main", zone.zone_id)
                main_Q = row.get(main_col, 0.0)
                if pd.isna(main_Q):
                    main_Q = 0.0

                # 收集支流流量
                branch_flows = {}
                for br_col in col_info.get("branches", []):
                    bq = row.get(br_col, 0.0)
                    if pd.notna(bq):
                        branch_flows[br_col] = bq

                # 使用上游传递的 C0（如果当前功能区没有自定义 C0）
                if zone.C0 > 0:
                    pass  # 使用自身 C0
                elif i > 0:
                    zone_copy = Zone(
                        zone_id=zone.zone_id, name=zone.name,
                        water_class=zone.water_class, length=zone.length,
                        K=zone.K, b=zone.b, a=zone.a, beta=zone.beta,
                        Cs=zone.Cs, C0=C_current,
                        main_name=zone.main_name, branches=zone.branches,
                    )
                    _, W, C_current = calc_zone_segments(zone_copy, main_Q, branch_flows)
                    result.loc[idx, zone.zone_id] = W
                    continue

                _, W, C_current = calc_zone_segments(zone, main_Q, branch_flows)
                result.loc[idx, zone.zone_id] = W
    else:
        # 旧模式：单链计算（无支流）
        for idx, row in monthly_flow.iterrows():
            C_current = 0.0
            for i, zone in enumerate(zones):
                Q = row[zone.zone_id]
                u = monthly_velocity.loc[idx, zone.zone_id]
                if zone.C0 > 0:
                    C0_use = zone.C0
                elif i == 0:
                    C0_use = zone.C0 if zone.C0 > 0 else 0.0
                else:
                    C0_use = C_current
                W = calc_capacity_value(zone.Cs, C0_use, Q, u, zone.K, zone.length, zone.b)
                result.loc[idx, zone.zone_id] = W
                C_current = calc_outflow_concentration(C0_use, zone.K, zone.length, u)

    return result


def calc_daily_capacity_with_segments(daily_flow: pd.DataFrame, zones: List[Zone],
                                       flow_col_map: Dict) -> Tuple[pd.DataFrame, Dict]:
    """
    逐日逐功能区分段计算纳污能力

    Returns:
        (daily_capacity_df, segment_accum)
        - daily_capacity_df: 日期 | zone1 | zone2 | ... （每日功能区总W）
        - segment_accum: {zone_id: {seg_name: {"W_sum": float, "count": int, ...}}}
          用于计算年平均分段结果
    """
    result = daily_flow[['日期']].copy()
    zone_ids = [z.zone_id for z in zones]
    for zid in zone_ids:
        result[zid] = 0.0

    # 分段累计器（用于纳污能力过程/结果表）
    seg_accum = {z.zone_id: {} for z in zones}

    for idx, row in daily_flow.iterrows():
        C_current = 0.0
        for i, zone in enumerate(zones):
            col_info = flow_col_map.get(zone.zone_id, {})
            main_col = col_info.get("main", zone.zone_id)
            main_Q = row.get(main_col, 0.0)
            if pd.isna(main_Q):
                main_Q = 0.0

            branch_flows = {}
            for br_col in col_info.get("branches", []):
                bq = row.get(br_col, 0.0)
                if pd.notna(bq):
                    branch_flows[br_col] = bq

            # 上游浓度传递
            zone_for_calc = zone
            if zone.C0 <= 0 and i > 0:
                zone_for_calc = Zone(
                    zone_id=zone.zone_id, name=zone.name,
                    water_class=zone.water_class, length=zone.length,
                    K=zone.K, b=zone.b, a=zone.a, beta=zone.beta,
                    Cs=zone.Cs, C0=C_current,
                    main_name=zone.main_name, branches=zone.branches,
                )

            segments, total_W, C_current = calc_zone_segments(zone_for_calc, main_Q, branch_flows)
            result.loc[idx, zone.zone_id] = total_W

            # 累计分段数据
            for seg in segments:
                key = seg.name
                if key not in seg_accum[zone.zone_id]:
                    seg_accum[zone.zone_id][key] = {
                        "seg_type": seg.seg_type, "length": seg.length,
                        "W_sum": 0.0, "Q_sum": 0.0, "C0_sum": 0.0,
                        "C_out_sum": 0.0, "count": 0, "remark": seg.remark,
                    }
                acc = seg_accum[zone.zone_id][key]
                acc["W_sum"] += seg.W
                acc["Q_sum"] += seg.Q
                acc["C0_sum"] += seg.C0
                acc["C_out_sum"] += seg.C_out
                acc["count"] += 1

    return result, seg_accum


def build_process_table(seg_accum: Dict, zones: List[Zone]) -> pd.DataFrame:
    """
    构建纳污能力过程表（展示全部段：干流段、支流、混合点、汇总）
    """
    rows = []
    for zone in zones:
        zone_segs = seg_accum.get(zone.zone_id, {})
        for seg_name, acc in zone_segs.items():
            cnt = acc["count"] if acc["count"] > 0 else 1
            rows.append({
                "功能区": zone.zone_id,
                "段名称": seg_name,
                "类型": acc["seg_type"],
                "长度(m)": acc["length"],
                "平均流量Q(m³/s)": round(acc["Q_sum"] / cnt, 4),
                "平均入口浓度C0(mg/L)": round(acc["C0_sum"] / cnt, 6),
                "平均出口浓度(mg/L)": round(acc["C_out_sum"] / cnt, 6),
                "年平均纳污能力W(t/a)": round(acc["W_sum"] / cnt, 4),
                "备注": acc["remark"],
            })
    return pd.DataFrame(rows)


def build_result_table(seg_accum: Dict, zones: List[Zone]) -> pd.DataFrame:
    """
    构建纳污能力结果表（只展示干流段和汇总）
    """
    rows = []
    for zone in zones:
        zone_segs = seg_accum.get(zone.zone_id, {})
        for seg_name, acc in zone_segs.items():
            if acc["seg_type"] not in ("干流段", "汇总"):
                continue
            cnt = acc["count"] if acc["count"] > 0 else 1
            rows.append({
                "功能区": zone.zone_id,
                "段名称": seg_name,
                "类型": acc["seg_type"],
                "长度(m)": acc["length"],
                "平均流量Q(m³/s)": round(acc["Q_sum"] / cnt, 4),
                "平均入口浓度C0(mg/L)": round(acc["C0_sum"] / cnt, 6),
                "平均出口浓度(mg/L)": round(acc["C_out_sum"] / cnt, 6),
                "年平均纳污能力W(t/a)": round(acc["W_sum"] / cnt, 4),
                "备注": acc["remark"],
            })
    return pd.DataFrame(rows)


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

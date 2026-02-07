#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================
# 脚本名称: web_app.py
# 功能描述: 纳污能力计算 - Web 界面版本（Streamlit）
# 来源工单: 水利公司需求
# 创建日期: 2025-12-18
# 更新日期: 2025-01-15 - 整理目录结构
# 作者: 开发部
# ============================================================
"""
Web 界面版本 - 纳污能力计算（Streamlit）

启动方式：
    streamlit run web_app.py

部署：
    - Streamlit Cloud: 连接 GitHub 仓库
    - 本地：streamlit run web_app.py --server.port 8501
"""

import streamlit as st
import pandas as pd
import io
from pathlib import Path
import sys

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from calc_core import (
    read_zones, read_daily_flow, read_reservoir_zones, read_reservoir_volume,
    calc_monthly_flow, calc_monthly_velocity, calc_monthly_capacity,
    calc_zone_monthly_avg, calc_reservoir_monthly_volume,
    calc_reservoir_monthly_capacity, calc_reservoir_zone_monthly_avg
)

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(
    page_title="纳污能力计算",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# 工具函数
# ============================================================
def find_sheet(sheet_data, keyword):
    """根据关键字查找 sheet（支持带单位的 sheet 名）"""
    for name in sheet_data.keys():
        if keyword in name:
            return name
    return None

def reorder_month_columns(df, start_month=4):
    """根据起始月份重排序 DataFrame 的月份列"""
    month_order = [(start_month + i - 1) % 12 + 1 for i in range(12)]
    month_cols = [f'{m}月' for m in month_order]
    
    # 处理带单位的年合计/年平均列
    other_cols = []
    summary_cols = []
    for c in df.columns:
        if '年合计' in c or '年平均' in c:
            summary_cols.append(c)
        elif '月' not in c:
            other_cols.append(c)
    
    final_cols = other_cols + [c for c in month_cols if c in df.columns] + summary_cols
    
    return df[[c for c in final_cols if c in df.columns]]

def add_unit_to_columns(df, unit, zone_ids=None):
    """为 DataFrame 的功能区列和年合计/年平均列添加单位"""
    rename_map = {}
    for col in df.columns:
        # 功能区列（逐月表）
        if zone_ids and col in zone_ids:
            rename_map[col] = f'{col}({unit})'
        # 年合计/年平均列（月平均表）
        elif col == '年合计':
            rename_map[col] = f'年合计({unit})'
        elif col == '年平均':
            rename_map[col] = f'年平均({unit})'
    return df.rename(columns=rename_map)

# ============================================================
# 标题
# ============================================================
st.title("🌊 水环境功能区纳污能力计算")
st.markdown("---")

# ============================================================
# 侧边栏 - 使用说明
# ============================================================
with st.sidebar:
    st.header("📖 使用说明")
    st.markdown("""
    **步骤：**
    1. 上传 `输入.xlsx` 文件
    2. 预览数据确认无误
    3. 点击「开始计算」
    4. 查看结果并下载
    
    ---
    
    **输入文件格式：**
    - Sheet 1: 功能区基础信息
    - Sheet 2: 逐日流量
    - Sheet 3: 水库功能区基础信息（可选）
    - Sheet 4: 水库逐日库容（可选）
    
    ---
    
    **计算公式：**
    
    *河道纳污能力：*
    ```
    W = 31.536 × b × (Cs - C0×e^(-KL/u)) 
        × (QKL/u) / (1 - e^(-KL/u))
    ```
    
    *水库纳污能力：*
    ```
    W = 31.536 × K × V × Cs × b
    ```
    """)
    
    st.markdown("---")
    
    # ========== 显示设置 ==========
    st.header("⚙️ 显示设置")
    
    start_month = st.selectbox(
        "月份起始",
        options=list(range(1, 13)),
        index=3,  # 默认4月（水文年）
        format_func=lambda x: f"{x}月",
        help="选择结果表格的起始月份（水文年通常从4月开始）"
    )

# ============================================================
# 文件上传
# ============================================================
st.header("📁 Step 1: 上传输入文件")

uploaded_file = st.file_uploader(
    "选择 输入.xlsx 文件",
    type=["xlsx"],
    help="支持 Excel 格式，包含功能区基础信息和逐日流量数据"
)

# 下载示例文件
sample_file = Path(__file__).parent / 'data' / 'sample' / '输入.xlsx'
if sample_file.exists():
    with open(sample_file, 'rb') as f:
        st.download_button(
            "📥 下载示例文件",
            data=f.read(),
            file_name="纳污能力计算_示例输入.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

if uploaded_file is not None:
    # ============================================================
    # 数据预览
    # ============================================================
    st.header("👁️ Step 2: 数据预览")
    
    xlsx = pd.ExcelFile(uploaded_file)
    sheet_names = xlsx.sheet_names
    
    tabs = st.tabs(sheet_names)
    
    sheet_data = {}
    for i, sheet_name in enumerate(sheet_names):
        with tabs[i]:
            df = pd.read_excel(xlsx, sheet_name=sheet_name)
            sheet_data[sheet_name] = df
            st.dataframe(df, use_container_width=True, height=300)
            st.caption(f"共 {len(df)} 行, {len(df.columns)} 列")
    
    # ============================================================
    # 计算
    # ============================================================
    st.header("🚀 Step 3: 开始计算")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        calc_button = st.button("🚀 开始计算", type="primary", use_container_width=True)
    
    if calc_button:
        results = {}
        
        with st.spinner("计算中..."):
            progress = st.progress(0)
            status = st.empty()
            
            try:
                # 查找 sheet（支持带单位的名称）
                zones_sheet = find_sheet(sheet_data, '功能区基础信息')
                flow_sheet = find_sheet(sheet_data, '逐日流量')
                reservoir_zones_sheet = find_sheet(sheet_data, '水库功能区基础信息')
                reservoir_volume_sheet = find_sheet(sheet_data, '水库逐日库容')
                
                # ========== 河道计算 ==========
                if zones_sheet and flow_sheet:
                    status.text("📊 读取河道数据...")
                    progress.progress(10)
                    
                    # 保存临时 CSV
                    zones_csv = io.StringIO()
                    sheet_data[zones_sheet].to_csv(zones_csv, index=False)
                    zones_csv.seek(0)
                    
                    flow_csv = io.StringIO()
                    sheet_data[flow_sheet].to_csv(flow_csv, index=False)
                    flow_csv.seek(0)
                    
                    # 读取数据
                    zones_df = pd.read_csv(zones_csv)
                    zones = []
                    from calc_core import Zone
                    for _, row in zones_df.iterrows():
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
                    
                    flow_csv.seek(0)
                    daily_flow = pd.read_csv(flow_csv)
                    daily_flow['日期'] = pd.to_datetime(daily_flow['日期'])
                    zone_ids = [z.zone_id for z in zones]
                    
                    status.text("📈 计算逐月流量...")
                    progress.progress(30)
                    monthly_flow = calc_monthly_flow(daily_flow, zone_ids)
                    
                    status.text("🌊 计算逐月流速...")
                    progress.progress(40)
                    monthly_velocity = calc_monthly_velocity(monthly_flow, zones)
                    
                    status.text("📊 计算纳污能力...")
                    progress.progress(50)
                    monthly_capacity = calc_monthly_capacity(monthly_flow, monthly_velocity, zones)
                    
                    status.text("📋 汇总河道结果...")
                    progress.progress(60)
                    zone_avg_velocity = calc_zone_monthly_avg(monthly_velocity, zone_ids, is_capacity=False)
                    zone_avg_capacity = calc_zone_monthly_avg(monthly_capacity, zone_ids, is_capacity=True)
                    
                    # 计算完成后添加单位（Sheet名用·替代/，避免Excel报错）
                    results['逐月流量(m³·s⁻¹)'] = add_unit_to_columns(monthly_flow, 'm³/s', zone_ids)
                    results['逐月流速(m·s⁻¹)'] = add_unit_to_columns(monthly_velocity, 'm/s', zone_ids)
                    results['功能区月平均流速(m·s⁻¹)'] = add_unit_to_columns(zone_avg_velocity, 'm/s')
                    results['功能区月平均纳污能力(t·a⁻¹)'] = add_unit_to_columns(zone_avg_capacity, 't/a')
                
                # ========== 水库计算 ==========
                if reservoir_zones_sheet and reservoir_volume_sheet:
                    status.text("🏞️ 读取水库数据...")
                    progress.progress(70)
                    
                    from calc_core import ReservoirZone
                    reservoir_zones = []
                    for _, row in sheet_data[reservoir_zones_sheet].iterrows():
                        zone = ReservoirZone(
                            zone_id=str(row['功能区']),
                            name=str(row['名称']),
                            K=float(row['K(1/s)']),
                            b=float(row['b']),
                            Cs=float(row['Cs']) if pd.notna(row.get('Cs')) else 0.0,
                            C0=float(row['C0']) if pd.notna(row.get('C0')) else 0.0,
                        )
                        reservoir_zones.append(zone)
                    
                    daily_volume = sheet_data[reservoir_volume_sheet].copy()
                    daily_volume['日期'] = pd.to_datetime(daily_volume['日期'])
                    reservoir_zone_ids = [z.zone_id for z in reservoir_zones]
                    
                    status.text("📊 计算水库逐月库容...")
                    progress.progress(80)
                    monthly_volume = calc_reservoir_monthly_volume(daily_volume, reservoir_zone_ids)
                    
                    status.text("📊 计算水库纳污能力...")
                    progress.progress(90)
                    reservoir_monthly_capacity = calc_reservoir_monthly_capacity(monthly_volume, reservoir_zones)
                    reservoir_zone_avg_capacity = calc_reservoir_zone_monthly_avg(
                        reservoir_monthly_capacity, reservoir_zone_ids
                    )
                    
                    # 计算完成后添加单位
                    results['水库逐月库容(m³)'] = add_unit_to_columns(monthly_volume, 'm³', reservoir_zone_ids)
                    results['水库功能区月平均纳污能力(t·a⁻¹)'] = add_unit_to_columns(reservoir_zone_avg_capacity, 't/a')
                
                progress.progress(100)
                status.text("✅ 计算完成！")
                
                st.success("🎉 计算完成！请查看下方结果")
                
            except Exception as e:
                st.error(f"❌ 计算出错：{str(e)}")
                st.exception(e)
        
        # ============================================================
        # 结果展示
        # ============================================================
        if results:
            st.header("📊 Step 4: 计算结果")
            
            result_tabs = st.tabs(list(results.keys()))
            
            for i, (name, df) in enumerate(results.items()):
                with result_tabs[i]:
                    # 对含月份列的表格重排序
                    if any('月' in str(c) for c in df.columns):
                        display_df = reorder_month_columns(df.copy(), start_month)
                    else:
                        display_df = df
                    
                    st.dataframe(display_df, use_container_width=True)
                    
                    # 如果是纳污能力表，显示简要统计
                    if '纳污能力' in name:
                        # 找到年合计列（可能带单位）
                        summary_col = [c for c in display_df.columns if '年合计' in c]
                        if summary_col:
                            st.markdown("**📈 年合计统计：**")
                            summary = display_df[['功能区', summary_col[0]]].copy()
                            summary[summary_col[0]] = summary[summary_col[0]].round(2)
                            st.dataframe(summary, use_container_width=True, hide_index=True)
            
            # ============================================================
            # 下载结果
            # ============================================================
            st.header("📥 Step 5: 下载结果")
            
            # 生成 Excel 文件（按用户选择的月份顺序）
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                for name, df in results.items():
                    if any('月' in str(c) for c in df.columns):
                        export_df = reorder_month_columns(df.copy(), start_month)
                    else:
                        export_df = df
                    export_df.to_excel(writer, sheet_name=name, index=False)
            output.seek(0)
            
            st.download_button(
                label="📥 下载计算结果.xlsx",
                data=output,
                file_name="计算结果.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )

else:
    # 未上传文件时显示示例
    st.info("👆 请上传 输入.xlsx 文件开始计算")
    
    with st.expander("📋 查看输入文件格式要求"):
        st.markdown("""
        ### 功能区基础信息 Sheet
        
        | 功能区 | 名称 | 水质类别 | Cs | C0 | 河段长度L(m) | 衰减系数K(1/s) | 不均匀系数b | a | β |
        |--------|------|----------|-----|-----|--------------|----------------|-------------|-----|-----|
        | QT-153 | 源头段 | II | 0.5 | 0.02 | 1000 | 0.001 | 0.8 | 0.3 | 0.5 |
        
        ### 逐日流量 Sheet
        
        | 日期 | QT-153 | QT-154 | ... |
        |------|--------|--------|-----|
        | 1992-01-01 | 324.7 | 588.7 | ... |
        
        ### 水库功能区基础信息 Sheet（可选）
        
        | 功能区 | 名称 | K(1/s) | b | Cs | C0 |
        |--------|------|--------|-----|-----|-----|
        | SK-01 | 青山水库 | 0.000002 | 0.2 | 0.5 | 0.02 |
        
        ### 水库逐日库容 Sheet（可选）
        
        | 日期 | SK-01 | SK-02 | ... |
        |------|-------|-------|-----|
        | 1992-04-01 | 45564115 | 40456955 | ... |
        """)

# ============================================================
# 页脚
# ============================================================
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "🌊 水环境功能区纳污能力计算工具 | 浙水设计"
    "</div>",
    unsafe_allow_html=True
)


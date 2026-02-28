#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
浙江省水资源年报数据查询 - Streamlit Web 界面

启动方式：
    streamlit run app.py

功能：
    - 按地区（市）查询多年数据
    - 按表名筛选（用水量、供水量、社会经济指标、县级套四级分区）
    - 导出 Excel
"""

import streamlit as st
import pandas as pd
import io
from pathlib import Path
import sys

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from data_loader import (
    load_csv,
    load_table,
    get_available_years,
    get_available_cities,
    get_available_tables,
    get_file_stats,
    find_csv_file,
)

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(
    page_title="水资源年报查询",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# 样式
# ============================================================
st.markdown("""
<style>
    .stMetric {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 0.5rem;
        color: white;
    }
    .stMetric label {
        color: rgba(255,255,255,0.8) !important;
    }
    .stMetric [data-testid="stMetricValue"] {
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 标题
# ============================================================
st.title("🌊 浙江省水资源年报数据查询")
st.caption("数据来源：2019-2024 年浙江省水资源年报")

# ============================================================
# 侧边栏 - 筛选条件
# ============================================================
with st.sidebar:
    st.header("📋 查询条件")
    
    # 获取可用选项
    available_years = get_available_years()
    available_cities = get_available_cities()
    available_tables = get_available_tables()
    
    # 选择表
    selected_table = st.selectbox(
        "📊 选择数据表",
        available_tables,
        index=available_tables.index("用水量") if "用水量" in available_tables else 0,
        help="选择要查询的数据表类型"
    )
    
    st.divider()
    
    # 选择市
    selected_cities = st.multiselect(
        "🏙️ 选择市",
        available_cities,
        default=["湖州市"],
        help="可多选，留空表示全部"
    )
    
    # 选择年份
    selected_years = st.multiselect(
        "📅 选择年份",
        available_years,
        default=available_years,
        help="可多选，留空表示全部"
    )
    
    st.divider()
    
    # 统计信息
    st.subheader("📈 数据统计")
    stats = get_file_stats()
    st.metric("CSV 文件总数", f"{stats['total']} 个")
    st.caption(f"年份: {len(available_years)} 个")
    st.caption(f"市: {len(available_cities)} 个")
    st.caption(f"数据表: {len(available_tables)} 个")

# ============================================================
# 主界面 - 数据展示
# ============================================================

# 加载数据
if selected_cities and selected_years:
    df = load_table(
        table=selected_table,
        years=selected_years,
        cities=selected_cities if selected_cities else None,
    )
    
    if len(df) > 0:
        # 显示查询结果概览
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("数据行数", f"{len(df):,}")
        with col2:
            st.metric("年份范围", f"{min(selected_years)}-{max(selected_years)}")
        with col3:
            st.metric("市数量", f"{len(selected_cities)}")
        with col4:
            st.metric("列数", f"{len(df.columns)}")
        
        st.divider()
        
        # 数据表格
        st.subheader(f"📋 {selected_table} - {', '.join(selected_cities)}")
        
        # 显示数据
        st.dataframe(
            df,
            use_container_width=True,
            height=500,
        )
        
        st.divider()
        
        # 导出功能
        st.subheader("📥 导出数据")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 导出 Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='查询结果')
            excel_data = output.getvalue()
            
            filename = f"{'_'.join(selected_cities)}_{selected_table}_{min(selected_years)}-{max(selected_years)}.xlsx"
            st.download_button(
                label="📥 下载 Excel",
                data=excel_data,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        
        with col2:
            # 导出 CSV
            csv_data = df.to_csv(index=False, encoding='utf-8-sig')
            filename = f"{'_'.join(selected_cities)}_{selected_table}_{min(selected_years)}-{max(selected_years)}.csv"
            st.download_button(
                label="📥 下载 CSV",
                data=csv_data,
                file_name=filename,
                mime="text/csv",
            )
    else:
        st.warning("⚠️ 未找到匹配的数据")
        st.info(f"查询条件：表={selected_table}, 市={selected_cities}, 年份={selected_years}")
else:
    st.info("👈 请在左侧选择查询条件")
    
    # 显示数据概览
    st.subheader("📊 数据概览")
    
    # 显示可用的 CSV 文件示例
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**可用年份:**")
        for year in available_years:
            st.write(f"- {year} 年")
    
    with col2:
        st.write("**可用数据表:**")
        for table in available_tables:
            count = stats['by_table'].get(table, 0)
            st.write(f"- {table} ({count} 个文件)")

# ============================================================
# 页脚
# ============================================================
st.divider()
st.caption("💡 提示：CSV 文件位于 `data/input/` 目录，命名格式为 `{年份}_{市}_{表名}.csv`")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地理编码工具 - Streamlit Web 界面

启动方式：
    streamlit run app.py

功能：
    - 逆地理编码（经纬度 → 地址）
    - 正向编码（地址 → 经纬度）
    - 企业搜索（公司名 → 位置）
"""

import streamlit as st
import pandas as pd
import io
import os
import time
import zipfile
import tempfile
from pathlib import Path
import sys

# ============================================================
# 路径配置
# ============================================================
PROJECT_DIR = Path(__file__).parent
SRC_DIR = PROJECT_DIR / 'src'
DATA_SAMPLE_DIR = PROJECT_DIR / 'data' / 'sample'
DATA_OUTPUT_DIR = PROJECT_DIR / 'data' / 'output'

sys.path.insert(0, str(SRC_DIR))

from reverse_geocode import reverse_geocode, wgs84_to_gcj02

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(page_title="地理编码工具", page_icon="📍", layout="wide")

# ============================================================
# 检查 API Key
# ============================================================
API_KEY = os.getenv("AMAP_API_KEY") or st.secrets.get("AMAP_API_KEY", None)

# ============================================================
# 工具函数
# ============================================================
def create_sample_zip():
    """将示例数据打包成 ZIP"""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file in DATA_SAMPLE_DIR.glob('*'):
            if file.is_file():
                zf.write(file, file.name)
    zip_buffer.seek(0)
    return zip_buffer

# ============================================================
# 侧边栏
# ============================================================
with st.sidebar:
    st.header("📖 使用说明")
    st.markdown("""
    **步骤：**
    1. 选择数据来源
    2. 选择功能类型
    3. 点击「开始处理」
    4. 查看结果并下载
    
    ---
    
    **坐标系说明：**
    
    | 坐标系 | 来源 |
    |--------|------|
    | WGS-84 | GPS、GIS软件 |
    | GCJ-02 | 高德、腾讯 |
    
    默认输入是 WGS-84，自动转换。
    """)
    
    st.markdown("---")
    
    # API Key 输入（云端部署时使用）
    if not API_KEY:
        st.warning("⚠️ 未检测到 API Key")
        api_key_input = st.text_input("输入高德 API Key", type="password")
        if api_key_input:
            API_KEY = api_key_input
            st.success("✅ API Key 已设置")
    else:
        st.success("✅ API Key 已配置")

# ============================================================
# 标题
# ============================================================
st.title("📍 地理编码工具")
st.markdown("基于高德地图 API 的坐标与地址转换")
st.markdown("---")

# ============================================================
# Step 1: 数据来源
# ============================================================
st.header("📁 Step 1: 数据来源")

col1, col2 = st.columns([2, 1])

with col1:
    data_source = st.radio(
        "选择数据来源",
        options=["sample", "upload"],
        format_func=lambda x: "使用示例数据" if x == "sample" else "上传自己的数据",
        horizontal=True
    )

with col2:
    st.download_button(
        "📥 下载示例文件",
        data=create_sample_zip(),
        file_name="示例坐标.zip",
        mime="application/zip"
    )

# 加载数据
df = None

if data_source == "sample":
    sample_file = DATA_SAMPLE_DIR / "示例坐标.xlsx"
    if sample_file.exists():
        df = pd.read_excel(sample_file)
        st.success(f"✅ 已加载示例数据：{sample_file.name}")
    else:
        st.error("❌ 示例文件不存在")
else:
    uploaded_file = st.file_uploader("上传 Excel 文件", type=["xlsx", "xls"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        st.success(f"✅ 已加载上传文件：{uploaded_file.name}")

# ============================================================
# Step 2: 功能选择
# ============================================================
if df is not None:
    st.header("🔧 Step 2: 功能选择")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        func_type = st.radio(
            "功能类型",
            ["逆地理编码", "正向编码", "企业搜索"],
            help="选择要使用的功能"
        )
    
    with col2:
        if func_type == "逆地理编码":
            coord_system = st.radio(
                "输入坐标系",
                ["WGS-84（GPS/GIS）", "GCJ-02（高德/腾讯）"],
                help="选择输入坐标的坐标系"
            )
            convert_wgs84 = coord_system.startswith("WGS-84")
        else:
            convert_wgs84 = True
    
    with col3:
        st.markdown("**功能说明：**")
        if func_type == "逆地理编码":
            st.markdown("经纬度 → 详细地址")
        elif func_type == "正向编码":
            st.markdown("详细地址 → 经纬度")
        else:
            st.markdown("公司名称 → 位置信息")

    # ============================================================
    # Step 3: 数据预览
    # ============================================================
    st.header("👁️ Step 3: 数据预览")
    st.dataframe(df.head(20), use_container_width=True)
    st.caption(f"共 {len(df)} 行, {len(df.columns)} 列")
    
    # 识别列
    if func_type == "逆地理编码":
        lng_col = None
        lat_col = None
        for col in df.columns:
            col_lower = str(col).lower()
            if col in ['经度', 'JD'] or col_lower in ['lng', 'longitude']:
                lng_col = col
            if col in ['纬度', 'WD'] or col_lower in ['lat', 'latitude']:
                lat_col = col
        
        if lng_col and lat_col:
            st.success(f"✅ 已识别坐标列：经度={lng_col}, 纬度={lat_col}")
        else:
            st.warning("⚠️ 未能识别坐标列，请确保包含 经度/纬度 或 lng/lat 列")

    # ============================================================
    # Step 4: 开始处理
    # ============================================================
    st.header("🚀 Step 4: 开始处理")
    
    if not API_KEY:
        st.error("❌ 请先配置高德 API Key（在侧边栏输入）")
    else:
        col1, col2 = st.columns([1, 3])
        
        with col1:
            process_button = st.button("🚀 开始处理", type="primary", use_container_width=True)
        
        if process_button:
            if func_type == "逆地理编码":
                if not (lng_col and lat_col):
                    st.error("❌ 无法识别坐标列")
                else:
                    with st.spinner("处理中..."):
                        progress = st.progress(0)
                        status = st.empty()
                        
                        results = []
                        total = len(df)
                        
                        for i, row in df.iterrows():
                            try:
                                lng = float(row[lng_col])
                                lat = float(row[lat_col])
                            except (ValueError, TypeError):
                                results.append({
                                    '地址': '',
                                    '省': '',
                                    '市': '',
                                    '区县': '',
                                    'GCJ02_经度': '',
                                    'GCJ02_纬度': '',
                                    '错误': '坐标格式错误'
                                })
                                continue
                            
                            # 坐标转换
                            if convert_wgs84:
                                gcj_lng, gcj_lat = wgs84_to_gcj02(lng, lat)
                            else:
                                gcj_lng, gcj_lat = lng, lat
                            
                            # 调用 API
                            result = reverse_geocode(gcj_lng, gcj_lat, API_KEY)
                            
                            results.append({
                                '地址': result.get('formatted_address', ''),
                                '省': result.get('province', ''),
                                '市': result.get('city', ''),
                                '区县': result.get('district', ''),
                                'GCJ02_经度': f"{gcj_lng:.6f}" if convert_wgs84 else '',
                                'GCJ02_纬度': f"{gcj_lat:.6f}" if convert_wgs84 else '',
                                '错误': result.get('error', '')
                            })
                            
                            progress.progress((i + 1) / total)
                            addr = result.get('formatted_address', '...')
                            status.text(f"处理 {i + 1}/{total}: {addr[:30] if addr else '...'}")
                            
                            time.sleep(0.3)  # 速率限制
                        
                        # 合并结果
                        result_df = pd.DataFrame(results)
                        output_df = pd.concat([df.reset_index(drop=True), result_df], axis=1)
                        
                        st.success(f"✅ 处理完成！共 {total} 条记录")
                        
                        # ============================================================
                        # Step 5: 结果
                        # ============================================================
                        st.header("📊 Step 5: 结果")
                        st.dataframe(output_df, use_container_width=True)
                        
                        # 统计
                        success_count = len([r for r in results if not r.get('错误')])
                        st.markdown(f"**成功率：** {success_count}/{total} ({success_count/total*100:.1f}%)")
                        
                        # ============================================================
                        # Step 6: 下载
                        # ============================================================
                        st.header("📥 Step 6: 下载结果")
                        
                        output = io.BytesIO()
                        output_df.to_excel(output, index=False, engine='openpyxl')
                        output.seek(0)
                        
                        st.download_button(
                            label="📥 下载结果.xlsx",
                            data=output,
                            file_name="地理编码结果.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            type="primary"
                        )
            
            elif func_type == "正向编码":
                st.info("🚧 正向编码功能开发中...")
            
            elif func_type == "企业搜索":
                st.info("🚧 企业搜索功能开发中...")

else:
    st.info("👆 请选择数据来源")

# ============================================================
# 页脚
# ============================================================
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "📍 地理编码工具 | 基于高德地图 API"
    "</div>",
    unsafe_allow_html=True
)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web 界面版本 - 纳污能力计算（Streamlit）
支持支流分段计算 + 多方案

启动方式：streamlit run web_app.py
"""

import streamlit as st
import pandas as pd
import io
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from calc_core import (
    calc_monthly_flow, calc_monthly_velocity, calc_monthly_capacity,
    calc_zone_monthly_avg, calc_daily_capacity_with_segments,
    build_process_table, build_result_table,
    calc_reservoir_monthly_volume, calc_reservoir_monthly_capacity,
    calc_reservoir_zone_monthly_avg,
)
from xlsx_parser import (
    parse_input_sheet, parse_flow_sheets, parse_reservoir_input,
    get_flow_column_map, read_input_sheet_raw,
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
def reorder_month_columns(df, start_month=4):
    """根据起始月份重排序 DataFrame 的月份列"""
    month_order = [(start_month + i - 1) % 12 + 1 for i in range(12)]
    month_cols = [f'{m}月' for m in month_order]
    other_cols = []
    summary_cols = []
    for c in df.columns:
        if '年合计' in c or '年平均' in c:
            summary_cols.append(c)
        elif '月' not in c:
            other_cols.append(c)
    final_cols = other_cols + [c for c in month_cols if c in df.columns] + summary_cols
    return df[[c for c in final_cols if c in df.columns]]


def add_unit_to_columns(df, unit, col_names=None):
    """为指定列和年合计/年平均列添加单位"""
    rename_map = {}
    for col in df.columns:
        if col_names and col in col_names:
            rename_map[col] = f'{col}({unit})'
        elif col == '年合计':
            rename_map[col] = f'年合计({unit})'
        elif col == '年平均':
            rename_map[col] = f'年平均({unit})'
    return df.rename(columns=rename_map)


DAILY_DISPLAY_LIMIT = 500  # 逐日结果页面展示行数上限


# ============================================================
# 标题 & 侧边栏
# ============================================================
st.title("🌊 水环境功能区纳污能力计算")
st.markdown("---")

with st.sidebar:
    st.header("📖 使用说明")
    st.markdown("""
    **步骤：**
    1. 上传 `输入.xlsx` 文件
    2. 预览数据确认无误
    3. 点击「开始计算」
    4. 查看结果并下载

    ---

    **计算公式：**

    *河道纳污能力（分段）：*
    ```
    W = 31.536 × b × (Cs - C0×e^(-KL/u))
        × (QKL/u) / (1 - e^(-KL/u))
    ```

    *支流汇入混合：*
    ```
    Q_mix = Q干 + Q支
    C_mix = (Q干×C干 + Q支×C支) / Q_mix
    ```

    *水库纳污能力：*
    ```
    W = 31.536 × K × V × Cs × b
    ```
    """)
    st.markdown("---")

    sample_file = Path(__file__).parent / 'data' / 'sample' / '示例输入.xlsx'
    if sample_file.exists():
        with open(sample_file, 'rb') as f:
            st.download_button(
                "下载示例数据 (Excel)",
                data=f.read(),
                file_name="示例输入.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    st.markdown("---")
    st.header("⚙️ 显示设置")
    start_month = st.selectbox(
        "月份起始", options=list(range(1, 13)), index=3,
        format_func=lambda x: f"{x}月",
        help="选择结果表格的起始月份（水文年通常从4月开始）"
    )

# ============================================================
# Step 1: 文件上传
# ============================================================
st.header("📁 Step 1: 上传输入文件")
uploaded_file = st.file_uploader(
    "选择 输入.xlsx 文件", type=["xlsx", "xlsm"],
    help="支持含支流的竖向输入格式，可包含多方案"
)

if uploaded_file is not None:
    # ============================================================
    # Step 2: 解析 & 预览
    # ============================================================
    st.header("👁️ Step 2: 数据预览")

    # 用 openpyxl 读取输入表原始数据
    uploaded_file.seek(0)
    try:
        ws_data = read_input_sheet_raw(uploaded_file)
        zones, scheme_count = parse_input_sheet(ws_data)
    except Exception as e:
        st.error(f"❌ 解析输入表失败：{e}")
        st.stop()

    # 用 pandas 读取所有 sheet 做预览
    uploaded_file.seek(0)
    xlsx = pd.ExcelFile(uploaded_file)

    # 解析多方案流量
    flow_sheets = parse_flow_sheets(xlsx, scheme_count)
    if not flow_sheets:
        st.error("❌ 未找到逐日流量 sheet（需包含'逐日流量'和'方案N'）")
        st.stop()

    # 解析水库（可选）
    uploaded_file.seek(0)
    reservoir_zones, reservoir_volume_df = parse_reservoir_input(xlsx)

    # 预览功能区信息
    with st.expander("📋 功能区参数", expanded=True):
        zone_info = []
        for z in zones:
            info = {
                "功能区": z.zone_id, "干流名": z.main_name,
                "Cs": z.Cs, "K(1/s)": z.K, "b": z.b,
                "a": z.a, "β": z.beta,
                "干流长度L(m)": z.length, "干流C0": z.C0,
                "支流数": len(z.branches) if z.branches else 0,
            }
            zone_info.append(info)
        st.dataframe(pd.DataFrame(zone_info), use_container_width=True, hide_index=True)

    # 预览支流信息
    branch_info = []
    for z in zones:
        for br in (z.branches or []):
            branch_info.append({
                "功能区": z.zone_id, "支流名": br.name,
                "长度L(m)": br.length, "汇入位置(m)": br.join_position,
                "C0": br.C0,
            })
    if branch_info:
        with st.expander("🌿 支流信息"):
            st.dataframe(pd.DataFrame(branch_info), use_container_width=True, hide_index=True)

    st.caption(f"共 {len(zones)} 个功能区，{scheme_count} 个方案")

    # 预览流量数据
    with st.expander("📊 逐日流量预览"):
        for s_num, flow_df in flow_sheets.items():
            st.markdown(f"**方案{s_num}** — {len(flow_df)} 天, {len(flow_df.columns)-1} 列")
            st.dataframe(flow_df.head(10), use_container_width=True, height=200)

    # ============================================================
    # Step 3: 计算
    # ============================================================
    st.header("🚀 Step 3: 开始计算")
    col1, col2 = st.columns([1, 3])
    with col1:
        calc_button = st.button("🚀 开始计算", type="primary", use_container_width=True)

    if calc_button:
        all_scheme_results = {}

        with st.spinner("计算中..."):
            progress = st.progress(0)
            status = st.empty()

            try:
                zone_ids = [z.zone_id for z in zones]

                # 构建流量列映射
                sample_flow = list(flow_sheets.values())[0]
                flow_col_map = get_flow_column_map(zones, list(sample_flow.columns))

                # 收集所有需要聚合的流量列
                all_flow_cols = []
                for info in flow_col_map.values():
                    all_flow_cols.append(info["main"])
                    all_flow_cols.extend(info["branches"])

                total_steps = scheme_count * 5
                step = 0

                for s_num in range(1, scheme_count + 1):
                    daily_flow = flow_sheets[s_num]
                    scheme_results = {}
                    prefix = f"方案{s_num}" if scheme_count > 1 else ""

                    # 1. 逐月流量
                    step += 1
                    status.text(f"📈 {prefix} 计算逐月流量...")
                    progress.progress(int(step / total_steps * 100))
                    monthly_flow = calc_monthly_flow(daily_flow, all_flow_cols)

                    # 2. 逐日分段计算（纳污能力 + 过程/结果表）
                    step += 1
                    status.text(f"📊 {prefix} 逐日分段计算纳污能力...")
                    progress.progress(int(step / total_steps * 100))
                    daily_cap, seg_accum = calc_daily_capacity_with_segments(
                        daily_flow, zones, flow_col_map
                    )

                    # 3. 逐月纳污能力（从逐日聚合）
                    step += 1
                    status.text(f"📋 {prefix} 汇总逐月纳污能力...")
                    progress.progress(int(step / total_steps * 100))
                    daily_cap_with_month = daily_cap.copy()
                    daily_cap_with_month['年'] = daily_cap_with_month['日期'].dt.year
                    daily_cap_with_month['月'] = daily_cap_with_month['日期'].dt.month
                    monthly_cap = daily_cap_with_month.groupby(['年', '月'])[zone_ids].mean().reset_index()

                    # 4. 功能区月平均
                    step += 1
                    status.text(f"📋 {prefix} 计算功能区月平均...")
                    progress.progress(int(step / total_steps * 100))
                    zone_avg_cap = calc_zone_monthly_avg(monthly_cap, zone_ids, is_capacity=True)

                    # 5. 过程表 & 结果表
                    step += 1
                    status.text(f"📋 {prefix} 生成过程/结果表...")
                    progress.progress(int(step / total_steps * 100))
                    process_table = build_process_table(seg_accum, zones)
                    result_table = build_result_table(seg_accum, zones)

                    # 组装结果
                    tag = f"（{prefix}）" if prefix else ""
                    scheme_results[f'逐日纳污能力{tag}'] = daily_cap
                    scheme_results[f'逐月纳污能力{tag}'] = add_unit_to_columns(monthly_cap, 't/a', zone_ids)
                    scheme_results[f'功能区月平均纳污能力{tag}'] = add_unit_to_columns(zone_avg_cap, 't/a')
                    scheme_results[f'纳污能力过程{tag}'] = process_table
                    scheme_results[f'纳污能力结果{tag}'] = result_table

                    all_scheme_results.update(scheme_results)

                # 水库计算
                if reservoir_zones and reservoir_volume_df is not None:
                    status.text("🏞️ 计算水库纳污能力...")
                    r_zone_ids = [z.zone_id for z in reservoir_zones]
                    monthly_vol = calc_reservoir_monthly_volume(reservoir_volume_df, r_zone_ids)
                    r_monthly_cap = calc_reservoir_monthly_capacity(monthly_vol, reservoir_zones)
                    r_zone_avg = calc_reservoir_zone_monthly_avg(r_monthly_cap, r_zone_ids)
                    all_scheme_results['水库逐月库容(m³)'] = add_unit_to_columns(monthly_vol, 'm³', r_zone_ids)
                    all_scheme_results['水库月平均纳污能力'] = add_unit_to_columns(r_zone_avg, 't/a')

                progress.progress(100)
                status.text("✅ 计算完成！")
                st.success("🎉 计算完成！请查看下方结果")

            except Exception as e:
                st.error(f"❌ 计算出错：{str(e)}")
                st.exception(e)

        # ============================================================
        # Step 4: 结果展示
        # ============================================================
        if all_scheme_results:
            st.header("📊 Step 4: 计算结果")
            result_tabs = st.tabs(list(all_scheme_results.keys()))

            for i, (name, df) in enumerate(all_scheme_results.items()):
                with result_tabs[i]:
                    if any('月' in str(c) for c in df.columns) and '日期' not in df.columns:
                        display_df = reorder_month_columns(df.copy(), start_month)
                    else:
                        display_df = df

                    # 逐日结果截断展示
                    if '逐日' in name and len(display_df) > DAILY_DISPLAY_LIMIT:
                        st.caption(f"共 {len(display_df)} 行，页面展示前 {DAILY_DISPLAY_LIMIT} 行（完整数据请下载）")
                        st.dataframe(display_df.head(DAILY_DISPLAY_LIMIT), use_container_width=True)
                    else:
                        st.dataframe(display_df, use_container_width=True)

                    # 纳污能力月平均表显示年合计统计
                    if '月平均纳污能力' in name:
                        summary_col = [c for c in display_df.columns if '年合计' in c]
                        if summary_col:
                            st.markdown("**📈 年合计统计：**")
                            summary = display_df[['功能区', summary_col[0]]].copy()
                            summary[summary_col[0]] = summary[summary_col[0]].round(2)
                            st.dataframe(summary, use_container_width=True, hide_index=True)

            # ============================================================
            # Step 5: 下载结果
            # ============================================================
            st.header("📥 Step 5: 下载结果")
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                for name, df in all_scheme_results.items():
                    if any('月' in str(c) for c in df.columns) and '日期' not in df.columns:
                        export_df = reorder_month_columns(df.copy(), start_month)
                    else:
                        export_df = df
                    # Excel sheet 名最长 31 字符
                    sheet_name = name[:31]
                    export_df.to_excel(writer, sheet_name=sheet_name, index=False)
            output.seek(0)

            st.download_button(
                label="📥 下载计算结果.xlsx",
                data=output,
                file_name="计算结果.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )

else:
    st.info("👆 请上传 输入.xlsx 文件开始计算")

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

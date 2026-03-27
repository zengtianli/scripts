#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
梯级水库发电调度界面 - Streamlit Web 应用

启动方式：
    streamlit run app.py

功能：
    - 上传 输入.xlsx（单文件）
    - 参数配置预览
    - 一键运行计算
    - 下载 计算结果.xlsx
"""

import sys
import os
import time
import io
import tempfile
from pathlib import Path
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.express as px

# 添加 src 和 lib 到路径
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "lib"))
from src import xlsx_bridge
from src.hydro_core import HydroElectricity, read_info_txt, read_paras
from hydraulic.st_utils import page_config, footer

# ============================================================
# 页面配置
# ============================================================
page_config("浙水设计-水库群多目标联合调度系统", "⚡")

# 自定义 CSS
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        font-size: 16px;
    }
    .upload-box {
        border: 2px dashed #4CAF50;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        background: #f9fff9;
    }
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        padding: 15px;
        border-radius: 8px;
        color: #155724;
    }
    .reservoir-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 10px 15px;
        border-radius: 8px;
        color: white;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 初始化 Session State
# ============================================================
if 'input_data' not in st.session_state:
    st.session_state.input_data = None  # 存储解析后的输入数据
if 'calculated' not in st.session_state:
    st.session_state.calculated = False
if 'result_xlsx' not in st.session_state:
    st.session_state.result_xlsx = None  # 存储结果文件的 bytes
if 'up_res' not in st.session_state:
    st.session_state.up_res = None
if 'down_res' not in st.session_state:
    st.session_state.down_res = None

# ============================================================
# 工具函数
# ============================================================
def parse_uploaded_xlsx(uploaded_file) -> dict:
    """解析上传的 输入.xlsx"""
    xlsx = pd.ExcelFile(uploaded_file)
    
    data = {
        'sheets': {},
        'up_res': None,
        'down_res': None,
        'params': {}
    }
    
    # 读取计算参数
    if '计算参数' in xlsx.sheet_names:
        df_params = pd.read_excel(xlsx, sheet_name='计算参数', header=None)
        data['sheets']['计算参数'] = df_params
        
        # 提取上下游水库名称
        for _, row in df_params.iterrows():
            param_name = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ''
            if param_name == '上库':
                data['up_res'] = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else None
            elif param_name == '下库':
                data['down_res'] = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else None
            elif param_name:
                data['params'][param_name] = row.iloc[1] if pd.notna(row.iloc[1]) else None
    
    # 读取其他 Sheet
    for sheet_name in xlsx.sheet_names:
        if sheet_name not in data['sheets']:
            data['sheets'][sheet_name] = pd.read_excel(xlsx, sheet_name=sheet_name)
    
    return data


def run_calculation_from_xlsx(uploaded_file, calc_step: str = "旬") -> bytes:
    """
    从上传的 xlsx 文件运行计算并返回结果 xlsx 的 bytes
    """
    base_dir = Path(__file__).parent
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # 保存上传的文件
        input_xlsx = tmpdir / "输入.xlsx"
        with open(input_xlsx, 'wb') as f:
            f.write(uploaded_file.getvalue())
        
        # CSV 目录
        csv_input_dir = tmpdir / 'data' / 'input'
        csv_output_dir = tmpdir / 'data' / 'output'
        csv_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Step 1: XLSX → CSV
        result = xlsx_bridge.xlsx_to_csv(input_xlsx, csv_input_dir)
        up_res = result['up_res']
        down_res = result['down_res']
        
        # Step 2: 核心计算
        # 扫描水库文件夹
        reservoirs = []
        for item in csv_input_dir.iterdir():
            if item.is_dir() and (item / "input_水库信息.txt").exists():
                reservoirs.append(item.name)
        reservoirs.sort()
        
        # 读取水库参数
        sks = {}
        for res_name in reservoirs:
            sks = read_info_txt(sks, res_name, str(csv_input_dir / res_name))
        
        # 基本参数
        base_info = {
            "CalStep": calc_step,
            "EPSYH": 0.01,
            "EPSYV": 1,
            "EPSYW": 1
        }
        
        # 读取计算参数（直接从 CSV 解析，避免 read_paras 路径问题）
        calc_param_file = csv_input_dir / "input_计算参数.csv"
        if calc_param_file.exists():
            paras_df = pd.read_csv(calc_param_file, header=None, index_col=0)
            paras_dict = {
                "up_res": paras_df.loc["上库"].values[0],
                "down_res": paras_df.loc["下库"].values[0],
                "up_v_special": pd.Series(paras_df.loc["上库特征库容"].values).dropna().astype(float).tolist(),
                "down_v_special": pd.Series(paras_df.loc["下库特征库容"].values).dropna().astype(float).tolist(),
                "need_add_user": pd.Series(paras_df.loc["需补水的用水户（利用上库特征库容之间进行补水）"].values).dropna().tolist(),
                "if_q_up_eco_as_in": bool(int(paras_df.loc["湖南镇生态水是否入黄坛口水量平衡"].values[0])),
                "stop_supply": pd.Series(paras_df.loc["当上库库容较低时（低于上库特征库容），下库停止供水的用水户"].values).dropna().tolist(),
            }
            # 额外补水用户
            another_add_user = pd.Series(paras_df.loc["额外再补用水户（利用上库特征库容以下进行补水）"].values).dropna()
            another_add_val = pd.Series(paras_df.loc["额外再补流量"].values).dropna()
            another_add = []
            for i_user in range(len(another_add_user)):
                tmp_add_user = another_add_user.iloc[i_user]
                try:
                    tmp_add_val = another_add_val.iloc[i_user]
                except (IndexError, ValueError):
                    tmp_add_val = -1
                another_add.append([tmp_add_user, tmp_add_val])
            paras_dict['another_add'] = another_add
        else:
            raise FileNotFoundError(f"计算参数文件不存在: {calc_param_file}")
        
        # 读取输出列名
        output_list_file = base_dir / "src" / "output_columns.csv"
        output_list = pd.read_csv(output_list_file, sep='\t', header=None, encoding='utf-8').values[:, 0].tolist()
        
        # 计算
        test = HydroElectricity(sks, base_info)
        up_table, down_table = test.power_operate_year_up_down(
            if_up_q_eco_as_in=paras_dict['if_q_up_eco_as_in'],
            up_res_name=paras_dict['up_res'],
            down_res_name=paras_dict['down_res'],
            up_v_special=paras_dict['up_v_special'],
            down_v_special=paras_dict['down_v_special'],
            need_add_user=paras_dict['need_add_user'],
            user_special=paras_dict['another_add'],
            user_stop_supply=paras_dict['stop_supply'],
        )
        
        # 保存 CSV 结果
        original_cwd = os.getcwd()
        os.chdir(csv_output_dir)
        try:
            test.statistic_for_up_down(up_table, '', up_res, output_list)
            test.statistic_for_up_down(down_table, '', down_res, output_list)
        finally:
            os.chdir(original_cwd)
        
        # Step 3: CSV → XLSX
        output_xlsx = tmpdir / "计算结果.xlsx"
        xlsx_bridge.csv_to_xlsx(csv_output_dir, output_xlsx, up_res, down_res)
        
        # 读取结果文件为 bytes
        with open(output_xlsx, 'rb') as f:
            return f.read(), up_res, down_res


# ============================================================
# 标题
# ============================================================
st.title("⚡ 浙水设计-水库群多目标联合调度系统")
st.caption("上传输入文件 → 预览参数 → 运行计算 → 下载结果")

# ============================================================
# 侧边栏 - 文件上传
# ============================================================
with st.sidebar:
    st.header("📁 数据输入")
    
    # 文件上传
    uploaded_file = st.file_uploader(
        "上传 输入.xlsx",
        type=['xlsx'],
        help="包含计算参数和上下游水库数据的 Excel 文件"
    )
    
    if uploaded_file:
        try:
            st.session_state.input_data = parse_uploaded_xlsx(uploaded_file)
            st.success("✅ 文件解析成功")
            
            data = st.session_state.input_data
            st.markdown(f"""
            **识别到的水库：**
            - 🏔️ 上游：{data['up_res']}
            - 🌊 下游：{data['down_res']}
            
            **Sheet 数量：** {len(data['sheets'])}
            """)
            
            st.session_state.up_res = data['up_res']
            st.session_state.down_res = data['down_res']
            
        except Exception as e:
            st.error(f"文件解析失败: {e}")
            st.session_state.input_data = None
    else:
        st.info("请上传 输入.xlsx 文件")
        
        # 提供示例文件下载
        sample_xlsx = Path(__file__).parent / "data" / "sample" / "输入.xlsx"
        if sample_xlsx.exists():
            with open(sample_xlsx, 'rb') as f:
                st.download_button(
                    "📥 下载示例文件",
                    data=f.read(),
                    file_name="示例_输入.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="下载示例输入文件，了解数据格式要求"
                )
    
    st.divider()
    
    # 计算参数
    st.header("🔧 计算设置")
    calc_step = st.selectbox(
        "计算尺度",
        options=["日", "旬", "月"],
        index=1,
        help="选择计算的时间步长"
    )
    
    st.divider()
    
    st.caption("V1.0 | 浙江省水利水电勘测设计院")

# ============================================================
# 主界面
# ============================================================
if st.session_state.input_data is None:
    # 未上传文件时显示说明
    st.markdown("""
    ### 👋 欢迎使用浙水设计-水库群多目标联合调度系统
    
    **使用步骤：**
    1. 在左侧上传 **输入.xlsx** 文件
    2. 预览并确认参数配置
    3. 点击「开始计算」
    4. 下载 **计算结果.xlsx**
    
    ---
    
    **输入文件格式要求：**
    
    | Sheet 名称 | 说明 |
    |-----------|------|
    | 计算参数 | 梯级调度参数（上库、下库、特征库容等） |
    | 上游_水库信息 | 上游水库基本参数 |
    | 上游_来水系列 | 上游水库来水数据 |
    | 上游_调度线 | 上游水库发电调度线 |
    | ... | 其他上游数据 |
    | 下游_水库信息 | 下游水库基本参数 |
    | 下游_来水系列 | 下游水库来水数据 |
    | ... | 其他下游数据 |
    
    """)
    
else:
    # 已上传文件，显示主界面
    data = st.session_state.input_data
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 参数配置",
        "📁 数据预览",
        "🚀 计算运行",
        "📊 结果下载"
    ])
    
    # ========== Tab 1: 参数配置 ==========
    with tab1:
        st.header("参数配置")
        
        # 计算参数
        st.subheader("🔗 梯级调度参数")
        if '计算参数' in data['sheets']:
            st.dataframe(data['sheets']['计算参数'], use_container_width=True, hide_index=True)
        
        st.divider()
        
        # 水库参数
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div class="reservoir-header">
                🏔️ 上游水库：{data['up_res']}
            </div>
            """, unsafe_allow_html=True)
            
            sheet_name = '上游_水库信息'
            if sheet_name in data['sheets']:
                st.dataframe(data['sheets'][sheet_name], use_container_width=True, hide_index=True)
            else:
                st.info("未找到上游水库信息")
        
        with col2:
            st.markdown(f"""
            <div class="reservoir-header">
                🌊 下游水库：{data['down_res']}
            </div>
            """, unsafe_allow_html=True)
            
            sheet_name = '下游_水库信息'
            if sheet_name in data['sheets']:
                st.dataframe(data['sheets'][sheet_name], use_container_width=True, hide_index=True)
            else:
                st.info("未找到下游水库信息")
    
    # ========== Tab 2: 数据预览 ==========
    with tab2:
        st.header("数据预览")
        
        # 来水系列
        st.subheader("📈 来水系列")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**{data['up_res']} 来水**")
            sheet_name = '上游_来水系列'
            if sheet_name in data['sheets']:
                df = data['sheets'][sheet_name]
                st.caption(f"数据量: {len(df)} 条")
                
                # 绘图
                if len(df.columns) >= 2:
                    date_col = df.columns[0]
                    flow_col = df.columns[1]
                    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                    df['年份'] = df[date_col].dt.year
                    yearly = df.groupby('年份')[flow_col].mean().reset_index()
                    
                    fig = px.line(yearly, x='年份', y=flow_col, title='年平均来水')
                    fig.update_layout(height=250)
                    st.plotly_chart(fig, use_container_width=True)
                
                with st.expander("查看数据"):
                    st.dataframe(df.head(50), use_container_width=True)
        
        with col2:
            st.markdown(f"**{data['down_res']} 来水**")
            sheet_name = '下游_来水系列'
            if sheet_name in data['sheets']:
                df = data['sheets'][sheet_name]
                st.caption(f"数据量: {len(df)} 条")
                
                if len(df.columns) >= 2:
                    date_col = df.columns[0]
                    flow_col = df.columns[1]
                    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                    df['年份'] = df[date_col].dt.year
                    yearly = df.groupby('年份')[flow_col].mean().reset_index()
                    
                    fig = px.line(yearly, x='年份', y=flow_col, title='年平均来水')
                    fig.update_layout(height=250)
                    st.plotly_chart(fig, use_container_width=True)
                
                with st.expander("查看数据"):
                    st.dataframe(df.head(50), use_container_width=True)
        
        st.divider()
        
        # 调度线
        st.subheader("📊 发电调度线")
        col1, col2 = st.columns(2)
        
        def plot_dispatch_line(df, title):
            """绘制调度线图表"""
            if df is None or df.empty:
                return None
            
            # 识别日期列和库容列（V开头）
            date_col = df.columns[0]
            v_cols = [col for col in df.columns if col.startswith('V')]
            
            if not v_cols:
                # 如果没有V开头的列，尝试找包含"库容"的列
                v_cols = [col for col in df.columns if '库容' in str(col) or '万m³' in str(col)]
            
            if not v_cols:
                return None
            
            # 准备绘图数据
            plot_df = df[[date_col] + v_cols].copy()
            plot_df = plot_df.melt(id_vars=[date_col], var_name='调度等级', value_name='库容(万m³)')
            
            # 转换日期为月份序号便于排序
            try:
                # 尝试解析日期格式（如 "3月1日", "03-01" 等）
                def parse_date_order(d):
                    s = str(d)
                    if '月' in s:
                        month = int(s.split('月')[0])
                    elif '-' in s:
                        month = int(s.split('-')[0])
                    else:
                        month = 0
                    return month
                
                plot_df['月份序号'] = plot_df[date_col].apply(parse_date_order)
                plot_df = plot_df.sort_values('月份序号')
            except:
                pass
            
            fig = px.line(
                plot_df, 
                x=date_col, 
                y='库容(万m³)', 
                color='调度等级',
                title=f'{title} - 发电调度线',
                markers=True
            )
            fig.update_layout(
                height=300,
                xaxis_title='日期',
                yaxis_title='库容 (万m³)',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            return fig
        
        with col1:
            sheet_name = '上游_调度线'
            if sheet_name in data['sheets']:
                st.markdown(f"**{data['up_res']}**")
                df = data['sheets'][sheet_name]
                
                # 绘制图表
                fig = plot_dispatch_line(df, data['up_res'])
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                
                with st.expander("查看调度线数据"):
                    st.dataframe(df, use_container_width=True)
        
        with col2:
            sheet_name = '下游_调度线'
            if sheet_name in data['sheets']:
                st.markdown(f"**{data['down_res']}**")
                df = data['sheets'][sheet_name]
                
                # 绘制图表
                fig = plot_dispatch_line(df, data['down_res'])
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                
                with st.expander("查看调度线数据"):
                    st.dataframe(df, use_container_width=True)
        
        st.divider()
        
        # 所有 Sheet 列表
        st.subheader("📑 所有数据表")
        all_sheets = list(data['sheets'].keys())
        selected_sheet = st.selectbox("选择 Sheet", options=all_sheets)
        if selected_sheet:
            st.dataframe(data['sheets'][selected_sheet], use_container_width=True)
    
    # ========== Tab 3: 计算运行 ==========
    with tab3:
        st.header("计算运行")
        
        # 数据检查
        st.subheader("📋 数据完整性检查")
        
        required_sheets = [
            '计算参数',
            '上游_水库信息', '上游_来水系列', '上游_调度线',
            '下游_水库信息', '下游_来水系列', '下游_调度线'
        ]
        
        checks = []
        for sheet in required_sheets:
            exists = sheet in data['sheets']
            checks.append({
                "项目": sheet,
                "状态": "✅" if exists else "❌",
                "说明": "已包含" if exists else "缺失"
            })
        
        check_df = pd.DataFrame(checks)
        st.dataframe(check_df, use_container_width=True, hide_index=True)
        
        all_ready = all(c["状态"] == "✅" for c in checks)
        
        st.divider()
        
        # 运行按钮
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if all_ready:
                if st.button("🚀 开始计算", type="primary", use_container_width=True):
                    with st.spinner("正在计算，请稍候..."):
                        progress = st.progress(0, text="初始化...")
                        
                        try:
                            progress.progress(10, text="读取输入数据...")
                            time.sleep(0.2)
                            
                            progress.progress(30, text="运行调度计算...")
                            
                            # 重新获取上传的文件
                            uploaded_file.seek(0)
                            result_bytes, up_res, down_res = run_calculation_from_xlsx(
                                uploaded_file, calc_step
                            )
                            
                            progress.progress(90, text="生成结果文件...")
                            time.sleep(0.2)
                            
                            progress.progress(100, text="完成！")
                            
                            st.session_state.calculated = True
                            st.session_state.result_xlsx = result_bytes
                            st.session_state.up_res = up_res
                            st.session_state.down_res = down_res
                            
                            st.success("✅ 计算完成！请切换到「📊 结果下载」下载结果")
                            st.balloons()
                            
                        except Exception as e:
                            st.error(f"计算出错: {e}")
                            import traceback
                            st.code(traceback.format_exc())
            else:
                st.warning("⚠️ 输入数据不完整，请检查缺失项")
                st.button("🚀 开始计算", disabled=True, use_container_width=True)
    
    # ========== Tab 4: 结果下载 ==========
    with tab4:
        st.header("结果下载")
        
        if not st.session_state.calculated or st.session_state.result_xlsx is None:
            st.info("👈 请先在「🚀 计算运行」中执行计算")
        else:
            st.success("✅ 计算已完成，可以下载结果")
            
            st.markdown(f"""
            **计算信息：**
            - 上游水库：{st.session_state.up_res}
            - 下游水库：{st.session_state.down_res}
            - 计算尺度：{calc_step}
            """)
            
            st.divider()
            
            # 下载按钮
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                st.download_button(
                    label="📥 下载 计算结果.xlsx",
                    data=st.session_state.result_xlsx,
                    file_name=f"计算结果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    use_container_width=True
                )
            
            st.divider()
            
            # 结果预览
            st.subheader("📊 结果预览")
            
            # 读取结果 xlsx
            result_xlsx = pd.ExcelFile(io.BytesIO(st.session_state.result_xlsx))
            
            result_tabs = st.tabs([f"🏔️ {st.session_state.up_res}", f"🌊 {st.session_state.down_res}"])
            
            for rtab, prefix in zip(result_tabs, ['上游', '下游']):
                with rtab:
                    # 逐日过程
                    daily_sheet = f"{prefix}_逐日过程"
                    if daily_sheet in result_xlsx.sheet_names:
                        df_daily = pd.read_excel(result_xlsx, sheet_name=daily_sheet)
                        
                        st.markdown("**逐日过程（前 50 行）**")
                        st.dataframe(df_daily.head(50), use_container_width=True)
                    
                    # 逐年过程
                    yearly_sheet = f"{prefix}_逐年过程"
                    if yearly_sheet in result_xlsx.sheet_names:
                        df_yearly = pd.read_excel(result_xlsx, sheet_name=yearly_sheet)
                        
                        st.markdown("**逐年统计**")
                        st.dataframe(df_yearly, use_container_width=True)

# ============================================================
# 页脚
# ============================================================
footer("浙水设计-水库群多目标联合调度系统 V1.0 | 浙江省水利水电勘测设计院")

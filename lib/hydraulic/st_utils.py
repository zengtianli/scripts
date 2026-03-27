#!/usr/bin/env python3
"""
水利 Streamlit 应用共享工具

提供页面配置、Excel 导出、页脚等通用组件，
减少各水利项目 Streamlit 应用的重复代码。

用法：
    from hydraulic.st_utils import page_config, excel_download, footer
"""

import io

import pandas as pd
import streamlit as st


def page_config(title: str, icon: str = "🌊", *, sidebar_state: str = "expanded"):
    """统一页面配置，所有水利应用使用 wide 布局 + 展开侧边栏。"""
    st.set_page_config(
        page_title=title,
        page_icon=icon,
        layout="wide",
        initial_sidebar_state=sidebar_state,
    )


def excel_download(
    sheets: dict,
    filename: str,
    label: str = "📥 下载 Excel",
    **button_kwargs,
):
    """多 sheet Excel 导出 + 下载按钮。

    Args:
        sheets: {sheet_name: DataFrame} 字典
        filename: 下载文件名
        label: 按钮文字
        **button_kwargs: 传递给 st.download_button 的额外参数
    """
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)
    st.download_button(
        label=label,
        data=buf.getvalue(),
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        **button_kwargs,
    )


def footer(text: str):
    """统一页脚样式。"""
    st.markdown("---")
    st.markdown(
        f"<div style='text-align:center;color:gray;font-size:14px;'>{text}</div>",
        unsafe_allow_html=True,
    )

---
name: dev-gui
description: Python GUI/Web 开发规范。Streamlit 首选、目录结构、部署流程。当开发图形界面时触发。
---

# Python GUI/Web 开发规范

> 适用于为命令行工具添加图形界面

## 技术选型决策树

```
业务工具 GUI 需求：
├─ 数据处理/计算工具 → Streamlit（首选）⭐
├─ 实时仪表盘/监控 → NiceGUI
├─ AI/ML 演示 → Gradio
├─ 复杂桌面应用 → PyQt/PySide
└─ 企业级 Web 应用 → FastAPI + 前端框架
```

## Streamlit 规范

### 目录结构

```
tool/
├── app.py              # Streamlit 入口
├── run.py              # 命令行入口（保留）
├── src/                # 核心逻辑（GUI/CLI 共用）
│   └── calc_core.py
├── requirements.txt    # 依赖
└── README.md
```

### 命名规范

| 文件 | 命名 |
|------|------|
| 单页应用入口 | `app.py` 或 `streamlit_app.py` |
| 多页应用页面 | `pages/1_数据导入.py`, `pages/2_计算.py` |

### 代码模板

```python
#!/usr/bin/env python3
"""Streamlit 界面 - [工具名称]"""

import streamlit as st
import pandas as pd
from pathlib import Path

# 页面配置（必须第一行）
st.set_page_config(
    page_title="工具名称",
    page_icon="🔧",
    layout="wide"
)

st.title("🔧 工具名称")

# 文件上传
uploaded = st.file_uploader("上传文件", type=["xlsx", "csv"])

if uploaded:
    df = pd.read_excel(uploaded)
    st.dataframe(df)
    
    if st.button("🚀 开始处理"):
        with st.spinner("处理中..."):
            result = process(df)
        st.success("✅ 完成！")
        
        st.download_button(
            "📥 下载结果",
            data=result.to_csv(index=False),
            file_name="结果.csv",
            mime="text/csv"
        )
```

### 启动命令

```bash
streamlit run app.py                    # 本地开发
streamlit run app.py --server.port 8501 # 指定端口
```

## 设计原则

1. **核心逻辑分离** - `src/` 中的代码应独立于 GUI，CLI 和 GUI 共用
2. **渐进式交互** - 先上传 → 预览 → 确认 → 执行 → 下载
3. **即时反馈** - 使用 `st.spinner()`, `st.progress()` 显示进度
4. **错误友好** - 使用 `st.error()`, `st.warning()` 展示问题

## 常见组件

| 需求 | 组件 |
|------|------|
| 文件上传 | `st.file_uploader()` |
| 数据表格 | `st.dataframe()` |
| 参数输入 | `st.number_input()`, `st.selectbox()` |
| 执行按钮 | `st.button()` |
| 进度显示 | `st.spinner()`, `st.progress()` |
| 结果下载 | `st.download_button()` |
| 分栏布局 | `st.columns()` |
| 侧边栏 | `st.sidebar` |

## 部署

详见：`references/streamlit-deploy.md`

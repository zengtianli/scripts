# 水利工具索引

> 📍 位置：`hydraulic/`
> 📊 最后更新：2025-02-06

## 工具总览

| 目录 | 功能 | 状态 | 入口文件 |
|------|------|------|----------|
| capacity/ | 纳污能力计算 | ✅ 完成 | `web_app.py` |
| geocode/ | 地理编码/逆编码 | ✅ 完成 | `app.py` |
| reservoir_schedule/ | 水库发电调度 | ✅ 完成 | `app.py` |
| irrigation/ | 灌溉需水计算 | 🔄 开发中 | `ngxs1/main.py` |
| district_scheduler/ | 区域调度模型 | 🔄 开发中 | - |
| qgis/ | QGIS 空间处理 | ✅ 完成 | `run_pipeline.sh` |
| company_query/ | 企业信息查询 | ✅ 完成 | `src/` |
| risk_data/ | 风险分析表填充 | ✅ 完成 | `*.py` |
| cad/ | CAD 脚本 | ✅ 完成 | `*.lsp` |
| rainfall/ | 降雨数据 | 📊 数据 | - |
| water_annual/ | 年度水资源数据 | 📊 数据 | - |

## 快速启动

```bash
cd ~/useful_scripts/.assets/projects

# 纳污能力（Web）
cd capacity && streamlit run web_app.py

# 地理编码（Web）
cd geocode && streamlit run app.py

# 水库调度（Web）
cd reservoir_schedule && streamlit run app.py

# QGIS 流水线
cd qgis && bash run_pipeline.sh
```

## 公共库

`_lib/` 目录包含水利工具共用的模块：
- `qgis_common/` - QGIS 脚本公共配置
- `xlsx_common/` - Excel 处理公共函数

## 详细文档

各子目录都有独立的 README.md，请查阅。

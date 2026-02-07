# 水利专用工具集

> 📦 水利领域专用工具统一入口 - 包含风险图处理、纳污能力计算、水库调度等

---

## 🎯 工具概述

| 子目录 | 功能 | 说明 |
|--------|------|------|
| `qgis/` | 风险图 QGIS 处理 | 空间数据处理流水线 |
| `risk_data/` | 风险图 Excel 填充 | 数据导入和处理 |
| `capacity/` | 纳污能力计算 | 水环境容量计算（GUI + CLI） |
| `reservoir_schedule/` | 水库调度 | 梯级水库发电调度（GUI + CLI） |
| `geocode/` | 地理编码 | 地址转坐标、企业定位 |
| `company_query/` | 企业查询 | 企业行业分类查询 |
| `cad/` | CAD 脚本 | AutoCAD LISP 脚本 |

## 📂 目录结构

```
hydraulic/
├── _lib/                    # 公共库
│   ├── qgis_common/         # QGIS 公共函数
│   └── xlsx_common/         # Excel 公共函数
│
├── capacity/                # ⭐ 纳污能力计算
│   ├── src/                 # 核心代码
│   ├── data/                # 数据目录
│   │   ├── input/           # 输入 CSV
│   │   ├── output/          # 输出 CSV
│   │   └── sample/          # 示例文件
│   ├── app.py               # Streamlit 界面
│   └── run.py               # CLI 入口
│
├── reservoir_schedule/      # ⭐ 水库调度
│   ├── src/                 # 核心代码
│   ├── data/                # 数据目录
│   │   ├── input/           # 输入 CSV（运行时按水库创建子目录）
│   │   ├── output/          # 输出 CSV（运行时按水库创建子目录）
│   │   └── sample/          # 示例文件
│   ├── docs/                # 文档
│   ├── app.py               # Streamlit 界面
│   └── run.py               # CLI 入口
│
├── qgis/                    # QGIS 空间处理
│   ├── pipeline/            # 流水线脚本 (01-13)
│   ├── tools/               # 独立工具
│   ├── _util/               # 公共模块
│   └── scripts/             # Shell 脚本
│
├── risk_data/               # 风险图 Excel 填充
│   ├── 1.x_*.py             # 数据库脚本
│   ├── 2.x_*.py             # 预报脚本
│   ├── 3.x_*.py             # 风险分析脚本
│   ├── input/               # 输入数据
│   └── output/              # 输出数据
│
├── geocode/                 # 地理编码
│   ├── src/                 # 核心脚本
│   └── data/                # 数据目录
│
├── company_query/           # 企业查询
│   ├── src/                 # 核心脚本
│   └── data/                # 数据文件
│
├── cad/                     # CAD 脚本
│   └── *.lsp                # LISP 脚本
│
├── setup.sh                 # 环境配置
└── README.md                # 本文件
```

---

## 🚀 快速开始

### GUI 工具

```bash
# 纳污能力计算界面
cd capacity && streamlit run app.py

# 水库调度界面
cd reservoir_schedule && streamlit run app.py
```

### CLI 工具

```bash
# 纳污能力计算
cd capacity
python run.py --input data/sample/输入.xlsx --output 计算结果.xlsx

# 水库调度
cd reservoir_schedule
python run.py --input data/sample/输入.xlsx --output 计算结果.xlsx
```

### 风险图处理

```bash
# QGIS 流水线
cd qgis/scripts
./run_pipeline.sh 1-5

# Excel 数据填充
cd risk_data
python 3.03_risk_protection_dike_relation.py
```

---

## 📋 risk_data 脚本列表

### 1.x 系列 - 数据库

| 脚本 | 功能 |
|------|------|
| `1.1_database_protection_area.py` | 保护片信息 |
| `1.2_database_dike_section.py` | 堤段信息 |
| `1.3_database_dike.py` | 堤防信息 |
| `1.4_database_river_centerline.py` | 河流中心线 |

### 2.x 系列 - 预报

| 脚本 | 功能 |
|------|------|
| `2.1_forecast_cross_section.py` | 断面信息 |

### 3.x 系列 - 风险分析

| 脚本 | 功能 |
|------|------|
| `3.01_risk_protection_info.py` | 保护片信息 |
| `3.02_risk_protection_region.py` | 保护片行政区域 |
| `3.03_risk_protection_dike_relation.py` | 保护片堤段关系 |
| `3.04_risk_dike_section_info.py` | 堤段信息 |
| `3.05_risk_elevation_relation.py` | 高程关系 |
| `3.06_risk_section_mileage.py` | 断面里程 |
| `3.07_risk_dike_info.py` | 堤防信息 |
| `3.08_risk_dike_profile.py` | 堤防剖面 |
| `3.09_risk_facilities.py` | 风险体信息 |

---

## 📋 QGIS 脚本列表

| 步骤 | 脚本 | 功能 |
|------|------|------|
| 1 | `01_generate_river_points.py` | 生成河段中心点 |
| 2 | `01.5_assign_lc_to_cross_sections.py` | 断面LC赋值 |
| 3 | `02_cut_dike_sections.py` | 切割堤防 |
| 4 | `03_assign_elevation_to_dike.py` | 堤段赋值高程 |
| 5 | `04_align_dike_fields.py` | 对齐堤段字段 |
| ... | ... | ... |

---

## 🔧 配置说明

### 公共库

所有脚本使用 `_lib/` 下的公共模块：

```python
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPT_DIR / '_lib'))

from qgis_common import ...  # QGIS 脚本
from xlsx_common import ...  # Excel 脚本
```

### 环境变量

```bash
source setup.sh
```

---

**版本**: 2.0.0  
**更新时间**: 2025-12-29  
**维护者**: tianli

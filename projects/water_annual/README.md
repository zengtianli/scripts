# 浙江省水资源年报数据查询工具

## 🚀 快速使用

```bash
cd ~/useful_scripts/execute/tools/hydraulic/water_annual

# 启动 Web 界面
streamlit run app.py
```

浏览器访问 http://localhost:8501

---

## 📋 功能

| 功能 | 说明 |
|-----|------|
| 按市查询 | 选择 11 个市（杭州、宁波、温州等） |
| 按年份查询 | 选择 2019-2024 年（多选） |
| 按表查询 | 用水量、供水量、社会经济指标、县级套四级分区 |
| 导出 Excel/CSV | 一键下载查询结果 |

---

## 📊 数据结构

### CSV 文件组织

```
data/
├── raw/                              # 原始 xlsx（软链接）
│   ├── 2019年_全省水资源分区基本情况表.xlsx
│   └── ...
│
└── input/                            # 拆分后的 CSV（按年份+市+表名）
    ├── 2019_杭州市_县级套四级分区.csv
    ├── 2019_杭州市_社会经济指标.csv
    ├── 2019_杭州市_供水量.csv
    ├── 2019_杭州市_用水量.csv
    ├── 2019_宁波市_县级套四级分区.csv
    ├── ...
    ├── 2024_湖州市_用水量.csv
    └── ...
```

**命名格式**: `{年份}_{市}_{表名}.csv`

### 文件统计

| 项目 | 数量 |
|-----|-----|
| CSV 文件总数 | 303 个 |
| 年份 | 6 个（2019-2024） |
| 市 | 11 个 |
| 表 | 4 个 |

---

## 🔧 脚本说明

| 脚本 | 功能 |
|-----|------|
| `app.py` | Streamlit Web 界面 |
| `run.py` | 启动脚本 |
| `src/convert.py` | xlsx → csv 转换脚本 |
| `src/data_loader.py` | 按需加载 CSV 文件 |
| `src/query_core.py` | 查询逻辑（可选） |

---

## 📦 重新生成 CSV

如果原始 xlsx 更新了，运行：

```bash
python -m src.convert --force
```

---

## 🏗️ 目录结构

```
water_annual/
├── app.py              # Streamlit Web 界面
├── run.py              # 启动脚本
├── requirements.txt    # 依赖
├── README.md
├── src/
│   ├── __init__.py
│   ├── convert.py      # xlsx → csv 转换
│   ├── data_loader.py  # 按需加载 CSV
│   └── query_core.py   # 查询逻辑
├── data/
│   ├── raw/            # 原始 xlsx（软链接）
│   └── input/          # 拆分后的 CSV
└── output/             # 导出结果
```

---

## 💡 使用示例

### Web 界面
1. 左侧选择「用水量」表
2. 选择「湖州市」
3. 选择 2019-2024 年
4. 查看数据表格
5. 点击「下载 Excel」导出

### Python 代码
```python
from src.data_loader import load_table

# 加载湖州市 2019-2024 用水量数据
df = load_table(
    table="用水量",
    years=[2019, 2020, 2021, 2022, 2023, 2024],
    cities=["湖州市"],
)
print(df)
```

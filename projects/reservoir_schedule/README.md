# 水库发电调度计算工具

湖南镇-黄坛口梯级水库发电调度计算工具。

## 目录结构

```
reservoir_schedule/
├── app.py              # Streamlit Web 界面（开发中）
├── run.py              # CLI 命令行入口
├── src/                # 核心计算模块
│   ├── __init__.py
│   ├── hydro_core.py   # 核心计算逻辑
│   └── output_columns.csv
├── input/              # 输入数据（UTF-8）
│   ├── 湖南镇水库/
│   ├── 黄坛口水库/
│   └── 计算参数.xlsx
├── output/             # 计算结果输出
├── docs/               # 文档
│   ├── PRD.md          # 需求文档
│   └── archived/       # 原始文件备份
├── requirements.txt
└── README.md
```

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 命令行运行

```bash
# 使用默认配置
python run.py

# 指定输入输出目录
python run.py --input ./input --output ./output

# 指定计算尺度
python run.py --step 日   # 日 / 旬 / 月
```

### Web 界面（开发中）

```bash
streamlit run app.py
```

## 输入文件说明

### 水库参数目录（input/湖南镇水库/）

| 文件 | 说明 |
|------|------|
| `input_水库信息.txt` | 水库基本参数 |
| `input_水位-库容.txt` | 水位-库容关系 |
| `input_水位-流量.txt` | 水位-流量关系 |
| `input_来水及生态系列.csv` | 来水序列（1961-2022） |
| `input_坝下需水系列.csv` | 坝下用水户需水 |
| `input_库内需水系列.csv` | 库内用水户需水 |
| `input_限制线.csv` | 调度限制库容线 |
| `input_发电调度线.csv` | 发电调度线 |

### 计算参数（input/计算参数.xlsx）

配置上下游水库、用水户、补水规则等。

## 输出文件

| 文件 | 说明 |
|------|------|
| `_水库名-output_逐日过程.csv` | 逐日计算过程 |
| `_水库名-output_逐月过程.csv` | 逐月统计 |
| `_水库名-output_逐年过程.csv` | 逐年统计 |
| `_水库名-output_水文年过程.csv` | 水文年统计 |

## 技术说明

- **编码**：所有输入文件使用 UTF-8 编码
- **计算尺度**：支持日、旬、月三种
- **数据范围**：1961-2022 年来水序列

## 来源

- 需求文档：`docs/PRD.md`
- 原始模型：`docs/archived/`



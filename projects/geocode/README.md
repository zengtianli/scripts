# 地理编码工具集

基于高德地图 API 的坐标与地址转换工具，支持 WGS-84 坐标自动转换。

## 🚀 快速使用

### 方式 1：Web 界面（推荐）

```bash
cd ~/useful_scripts/execute/tools/hydraulic/geocode
streamlit run app.py
```

浏览器访问 http://localhost:8501

### 方式 2：命令行

```bash
# 逆地理编码（经纬度 → 地址）
python run.py reverse data/sample/示例坐标.xlsx output.xlsx

# 正向编码（地址 → 经纬度）
python run.py address input.xlsx output.xlsx

# 企业搜索（公司名 → 位置）
python run.py company companies.xlsx output.xlsx
```

---

## 架构

```
输入.xlsx → [xlsx_bridge] → CSV → [核心处理] → CSV → [xlsx_bridge] → 输出.xlsx
```

设计理念：
- 对外接口用 xlsx：普通用户习惯 Excel
- 内部处理用 csv：编程友好，pandas 处理快

---

## 目录结构

```
geocode/
├── app.py                      # Web 界面入口
├── run.py                      # 命令行入口
├── README.md                   # 本文件
├── requirements.txt            # 依赖管理
├── data/
│   ├── input/                  # 临时输入（运行时）
│   ├── output/                 # 临时输出（运行时）
│   ├── sample/                 # 示例数据
│   │   └── 示例坐标.xlsx
│   └── archived/               # 历史数据归档
└── src/
    ├── __init__.py
    ├── reverse_geocode.py      # 逆地理编码（主力）
    ├── geocode_by_address.py   # 正向编码
    ├── search_by_company.py    # 企业搜索
    └── compare_results.py      # 结果比对
```

---

## 环境配置

```bash
export AMAP_API_KEY="你的高德API密钥"
```

---

## 功能说明

### 1. 逆地理编码（经纬度 → 地址）

**默认输入 WGS-84 坐标，自动转换为 GCJ-02：**

```bash
python run.py reverse input.xlsx output.xlsx
```

**如果输入已经是 GCJ-02（高德/腾讯坐标），跳过转换：**

```bash
python run.py reverse input.xlsx output.xlsx --gcj02
```

### 2. 正向地理编码（地址 → 经纬度）

```bash
python run.py address addresses.xlsx output.xlsx
```

### 3. 企业搜索（公司名 → 位置）

```bash
python run.py company companies.xlsx output.xlsx
```

---

## 输入格式

### 逆地理编码
需要包含经纬度列（自动识别以下列名）：
- 经度: `经度` / `JD` / `lng` / `longitude`
- 纬度: `纬度` / `WD` / `lat` / `latitude`

### 正向编码
需要包含 `地址` 列

### 企业搜索
需要包含以下任一列：`公司名称` / `用水户名称` / `企业名称` / `QYMC`

---

## 输出列

逆地理编码输出新增列：
- `地址`: 格式化地址
- `省`: 省份
- `市`: 城市
- `区县`: 区县
- `GCJ02_经度`: 转换后的经度（仅 WGS-84 模式）
- `GCJ02_纬度`: 转换后的纬度（仅 WGS-84 模式）

---

## 坐标系说明

| 坐标系 | 使用场景 |
|--------|----------|
| WGS-84 | GPS 原始坐标、国际地图、大部分 GIS 软件 |
| GCJ-02 | 高德、腾讯、谷歌中国版 |
| BD-09 | 百度地图 |

**本工具默认假设输入是 WGS-84，自动转换为 GCJ-02 后调用高德 API。**

---

## 注意事项

- API 有频率限制，脚本已内置 0.3 秒间隔和自动重试
- 中国境外坐标不做转换（WGS-84 与 GCJ-02 在境外一致）
- 建议先用小批量数据测试

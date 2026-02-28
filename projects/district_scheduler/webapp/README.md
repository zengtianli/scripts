# 浙东河区调度模型 - Web 界面

水资源调度计算的 Streamlit 可视化界面。

## 功能特性

- 🌊 19个河区水平衡计算
- 🔀 6个分水枢纽调度
- 📊 实时计算进度显示
- 📥 支持上传自定义数据
- 📦 结果打包下载

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行 Web 界面

```bash
streamlit run app.py
```

### 命令行运行

```bash
# 使用示例数据
python run.py

# 使用自定义数据
python run.py /path/to/your/data
```

## 目录结构

```
webapp/
├── app.py              # Streamlit 界面入口
├── run.py              # 命令行入口
├── requirements.txt    # 依赖列表
├── data/
│   ├── sample/         # 示例数据
│   └── output/         # 输出结果
└── src/
    ├── config.py       # 配置模块
    └── scheduler.py    # 核心调度器
```

## 输入文件要求

### 静态配置文件

| 文件 | 说明 |
|------|------|
| `static_HQ_ZQ.txt` | 河区库容曲线 |
| `static_HQ_SK.txt` | 河区-水库配置 |
| `static_SW_PS.txt` | 排水位设定 |
| `static_FSSN_RULES.txt` | 分水枢纽规则 |

### 时间序列数据

| 文件 | 说明 |
|------|------|
| `input_SK.txt` | 水库来水数据 |
| `input_SW_CS.txt` | 当前水位 |
| `input_SW_MB.txt` | 目标水位 |
| `input_FQJL.txt` | 河网供水 |
| `input_GPS_GGXS.txt` | 农业需水 |
| `input_GPS_PYCS.txt` | 平原产水 |
| `input_LS_QT.txt` | 其他外供 |
| `input_XS_ST.txt` | 生态需水 |
| `input_XS_FN.txt` | 非农需水 |

## 计算公式

```
净流量 = 合计来水 - 总需水量
日中容积 = 日初容积 + 净流量
日末容积 = 日中容积 + 缺水(浙东需供)
河区排水 = max(0, 日末容积 - 排水容积)
排末容积 = 日末容积 - 河区排水
```

## 输出文件

- `output_hq_*.txt` - 各河区计算结果
- `output_sn_*.txt` - 分水枢纽数据
- `output_hq_all.txt` - 汇总数据


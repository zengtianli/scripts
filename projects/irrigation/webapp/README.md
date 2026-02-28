# 浙东灌溉需水计算模型

基于作物需水与水量平衡的农业灌溉需水量预测系统。

## 🚀 快速使用

### 方式 1：Web 界面（推荐）

```bash
cd ~/useful_scripts/execute/tools/hydraulic/irrigation
streamlit run app.py
```

浏览器打开 http://localhost:8501

### 方式 2：命令行

```bash
# 使用默认数据目录
python run.py

# 指定数据目录
python run.py /path/to/data

# B3 NC数据模式
python run.py --b3 --year 2024
```

---

## 📁 目录结构

```
irrigation/
├── app.py                  # Streamlit Web 界面
├── run.py                  # 命令行入口
├── README.md               # 本文件
├── requirements.txt        # 依赖管理
├── data/
│   ├── input/              # 输入数据文件
│   │   ├── in_TIME.txt
│   │   ├── in_JYGC.txt
│   │   ├── in_ZFGC.txt
│   │   └── static_*.txt
│   ├── output/             # 输出结果
│   ├── sample/             # 示例数据
│   └── archived/           # 历史归档
└── src/
    ├── __init__.py
    ├── main.py             # 主程序
    ├── calculator.py       # 主计算控制器
    ├── config.py           # 全局配置
    ├── core.py             # 模拟基类
    ├── dryland_models.py   # 旱地作物模型
    ├── paddy_models.py     # 水稻灌溉模型
    ├── utils.py            # 工具函数
    ├── nc_adapter.py       # NC数据适配器
    └── evaluate.py         # 评估模块
```

---

## 🔧 计算模式

| 模式 | 说明 |
|------|------|
| **both** | 综合模式：旱地作物 + 水稻灌溉，结果合并 |
| **dryland** | 旱地作物模式：基于需水定额计算 |
| **paddy** | 水稻灌溉模式：基于水量平衡模拟 |

---

## 📥 输入文件

| 文件名 | 说明 |
|--------|------|
| `in_TIME.txt` | 预测起始时间和预测天数 |
| `in_JYGC.txt` | 降雨量数据（各分区逐日） |
| `in_ZFGC.txt` | 蒸发量数据（各分区逐日） |
| `static_fenqu.txt` | 灌区分区信息 |
| `static_single_crop.txt` | 单季稻灌溉制度表 |
| `static_double_crop.txt` | 双季稻灌溉制度表 |
| `static_crops.txt` | 作物需水参数 |
| `in_dry_crop_area.txt` | 旱地作物种植面积 |

---

## 📤 输出文件

| 文件名 | 说明 |
|--------|------|
| `OUT_GGXS_TOTAL.txt` | 合并后的总灌溉需水量 |
| `OUT_PYCS_TOTAL.txt` | 合并后的总排水量 |
| `OUT_GGXS_C.txt` | 旱地作物模式灌溉需水 |
| `OUT_GGXS_I.txt` | 水稻灌溉模式灌溉需水 |
| `OUT_PYCS_C.txt` | 旱地作物模式排水量 |
| `OUT_PYCS_I.txt` | 水稻灌溉模式排水量 |

---

## 🌍 覆盖区域

浙东地区 15 个平原区域，包括：
- 余姚平原水系（上河区、下河区、姚江上下游区、马渚中河区）
- 慈溪平原水系（西河区、中河区、东河区）
- 其他重要平原区（丰惠、南沙、绍虞等）

---

## 📋 平台版

如需接入下游平台，使用平台版（保持原始目录结构）：

```
~/useful_scripts/execute/tools/hydraulic/irrigation_platform/
```

平台版保持输入输出文件在根目录，便于平台调用。

---

## 依赖安装

```bash
pip install -r requirements.txt
```

---

*by ZDWP Tianli*


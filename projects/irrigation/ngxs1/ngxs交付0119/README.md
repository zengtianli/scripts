# 农田灌溉需水计算系统

## 环境要求

- Python 3.8+
- 依赖包：pandas, numpy

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行

```bash
python main.py
```

## 文件说明

### 输入文件（in_* 开头）

| 文件 | 说明 |
|------|------|
| `in_TIME.txt` | 计算起始时间和预测天数 |
| `in_JYGC.txt` | 降雨量数据 |
| `in_ZFGC.txt` | 蒸发量数据 |
| `in_dry_crop_area.txt` | 各灌区旱地作物种植面积 |

### 静态配置文件（static_* 开头）

| 文件 | 说明 |
|------|------|
| `static_fenqu.txt` | 灌区分区配置（面积、渗漏系数等） |
| `static_single_crop.txt` | 单季稻灌溉制度 |
| `static_double_crop.txt` | 双季稻灌溉制度 |
| `static_irrigation_quota.txt` | 旱地作物月度灌溉定额 |

### 输出文件

| 文件 | 说明 |
|------|------|
| `OUT_GGXS_TOTAL.txt` | 各灌区灌溉需水量（万m³） |
| `OUT_PYCS_TOTAL.txt` | 各灌区排水量（万m³） |

## 修改参数

- 修改预测时间：编辑 `in_TIME.txt`
- 修改气象数据：编辑 `in_JYGC.txt`（降雨）和 `in_ZFGC.txt`（蒸发）
- 修改作物面积：编辑 `in_dry_crop_area.txt`

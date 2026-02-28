# 📊 风险分析表填充脚本 - 操作手册

> 📍 脚本位置：`~/useful_scripts/execute/tools/hydraulic/xlsx/`  
> 📅 更新日期：2025-12-09  
> 🎯 将 QGIS 处理后的 GeoJSON 数据填充到风险分析 Excel 表

---

## 📋 目录

1. [概述](#1-概述)
2. [文件结构](#2-文件结构)
3. [脚本详解](#3-脚本详解)
4. [执行顺序](#4-执行顺序)
5. [常见问题](#5-常见问题)

---

## 1. 概述

### 1.1 功能说明

这套脚本用于将 QGIS 空间处理后的 GeoJSON 数据，填充到**风险分析 Excel 表**（`risk_sx.xlsx`）的各个 Sheet 中。

### 1.2 数据流向

```
┌─────────────────────────────────────────────────────────────────┐
│                        QGIS 空间处理                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ 保护片   │  │ 堤段     │  │ 断面     │  │ 堤防     │       │
│  │ env.json │  │ dd.json  │  │ dm_LC    │  │ df.json  │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
└───────┼─────────────┼─────────────┼─────────────┼─────────────┘
        │             │             │             │
        ▼             ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     xlsx 脚本填充                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ 3.01     │  │ 3.03-05  │  │ 3.06     │  │ 3.07-08  │       │
│  │ 3.02     │  │          │  │          │  │          │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
└───────┼─────────────┼─────────────┼─────────────┼─────────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  risk_sx.xlsx   │
                    │  (9个Sheet)     │
                    └─────────────────┘
```

---

## 2. 文件结构

### 2.1 输入文件目录

```
工作目录/
├── input/
│   ├── 保护片/
│   │   └── env.geojson              ← 保护片空间数据
│   ├── geojson/
│   │   ├── dd.geojson               ← 堤段空间数据
│   │   └── dd_fix.geojson           ← 堤段修复数据（含polder_id）
│   ├── baohu/
│   │   └── baohu.geojson            ← 重要设施数据
│   ├── dm_LC.geojson                ← 断面里程数据
│   ├── df_with_elevation_lc.geojson ← 堤防数据（含高程里程）
│   ├── GDP、人口、房屋、耕地、道路重新计算结果.csv
│   └── region_name_code.csv         ← 乡镇编码对照表
│
├── output/
│   └── risk_sx.xlsx                 ← 目标Excel文件
│
└── templates/
    └── risk_bx.xlsx                 ← 白溪模板（参考）
```

### 2.2 输出文件

| 文件 | 说明 |
|-----|------|
| `output/risk_sx.xlsx` | 风险分析Excel（更新9个Sheet） |
| `output/*.txt` | 各脚本生成的填充报告 |

---

## 3. 脚本详解

### 3.01 保护片信息

**脚本**: `3.01_risk_protection_info.py`

#### 📥 输入

| 文件 | 格式 | 说明 |
|-----|------|------|
| `input/保护片/env.geojson` | GeoJSON | 保护片空间数据 |
| `input/GDP、人口、房屋、耕地、道路重新计算结果.csv` | CSV | 最新统计数据（优先级最高） |

#### 📤 输出

| Sheet名称 | 说明 |
|----------|------|
| `保护片信息 ` | 保护片基本信息（21个字段） |

#### 📋 字段映射

| GeoJSON字段 | Excel字段 | 说明 |
|------------|----------|------|
| `code` | `polder_code` | 保护片编码（转大写） |
| `name` | `polder_name` | 保护片名称 |
| `area` | `areas` | 区域面积（km²） |
| `protectLand` | `cultivated_area` | 耕地面积（公顷→km²，÷100） |
| `proPeople` | `pop` | 人口（万人） |
| `gdp` | `gdp` | GDP（万元） |
| `planType` | `gh_flood` | 规划防洪标准 |
| `type` | `xz_flood` | 现在防洪标准（提取数字） |
| `isComplete` | `up_standard` | 是否达标 |
| `lng/lat` | `lgtd/lttd` | 中心点坐标 |
| `topLeftLongitude` | `ls_lgtd` | 左上角经度 |
| `bottomRightLatitude` | `rx_lttd` | 右下角纬度 |

#### 🔄 数据优先级

```
CSV数据（最新） > GeoJSON数据（原始）
```

---

### 3.02 保护片行政区域信息

**脚本**: `3.02_risk_protection_region.py`

#### 📥 输入

| 文件 | 格式 | 说明 |
|-----|------|------|
| `input/保护片/env.geojson` | GeoJSON | 保护片空间数据 |
| `input/GDP、人口、房屋、耕地、道路重新计算结果.csv` | CSV | 最新统计数据 |
| `input/region_name_code.csv` | CSV | 乡镇编码对照表 |

#### 📤 输出

| Sheet名称 | 说明 |
|----------|------|
| `保护片行政区域信息  ` | 保护片与乡镇的对应关系 |

#### 📋 字段说明

| Excel字段 | 说明 | 计算方式 |
|----------|------|---------|
| `polder_code` | 保护片编码 | 从GeoJSON提取（大写） |
| `region_code` | 区域编码（乡镇） | 从region_name_code.csv查询 |
| `weight` | 权重 | 如果跨N个乡镇，每个=1/N |
| `pop_pm` | 每平方千米人口 | 总人口÷总面积 |
| `gdp_pm` | 每平方千米GDP | 总GDP÷总面积 |

#### ⚠️ 特殊处理

- **跨乡镇保护片**：一个保护片跨多个乡镇时，会生成多行记录
- **权重分配**：按乡镇数量平均分配

---

### 3.03 保护片堤段对应关系信息

**脚本**: `3.03_risk_protection_dike_relation.py`

#### 📥 输入

| 文件 | 格式 | 说明 |
|-----|------|------|
| `input/geojson/dd_fix.geojson` | GeoJSON | 堤段数据（含polder_id） |

#### 📤 输出

| Sheet名称 | 说明 |
|----------|------|
| `保护片堤段对应关系信息` | 保护片与堤段的对应关系 |

#### 📋 字段映射

| GeoJSON字段 | Excel字段 | 说明 |
|------------|----------|------|
| `polder_id` | `polder_code` | 保护片编码（转大写） |
| `ds_code` | `ds_code` | 堤段编码 |

---

### 3.04 堤段对应信息

**脚本**: `3.04_risk_dike_section_info.py`

#### 📥 输入

| 文件 | 格式 | 说明 |
|-----|------|------|
| `input/geojson/dd.geojson` | GeoJSON | 堤段空间数据 |

#### 📤 输出

| Sheet名称 | 说明 |
|----------|------|
| `堤段对应信息` | 堤段详细信息（17个字段） |

#### 📋 字段映射

| GeoJSON字段 | Excel字段 | 说明 |
|------------|----------|------|
| `river_code` | `river_code` | 河道编码（大写） |
| `river_name` | `river_name` | 河道名称 |
| `dike_name` | `dike_code` | 堤防编码（自动生成） |
| `dike_name` | `dike_name` | 堤防名称 |
| `ds_code` | `ds_code` | 堤段编码 |
| `ds_name` | `ds_name` | 堤段名称 |
| `zya` | `zya` | 岸别（L/R） |
| `polder_id` | `polder_code` | 保护片编码（大写） |
| `ddgc` | `ddgc` | 堤顶高程（米） |
| `LC` | `lc` | 里程（米） |
| `ds_length` | `ds_length` | 堤段长度（米） |
| `lgtd/lttd` | `lgtd/lttd` | 中心点坐标 |
| `regioncode` | `region_code` | 区域编码 |

#### 🔄 水位自动计算

| 字段 | 计算公式 |
|-----|---------|
| `drz` (设计水位) | 堤顶高程 - 0.5 |
| `grz` (保证水位) | 堤顶高程 - 1.0 |
| `wrz` (警戒水位) | 堤顶高程 - 1.5 |

---

### 3.05 保护片堤段堤顶高程对应关系信息

**脚本**: `3.05_risk_elevation_relation.py`

#### 📥 输入

| 文件 | 格式 | 说明 |
|-----|------|------|
| `input/geojson/dd.geojson` | GeoJSON | 堤段空间数据 |

#### 📤 输出

| Sheet名称 | 说明 |
|----------|------|
| `保护片堤段堤顶高程对应关系信息` | 高程与里程对应关系 |

#### 📋 字段映射

| GeoJSON字段 | Excel字段 | 说明 |
|------------|----------|------|
| `polder_id` | `polder_code` | 保护片编码（大写） |
| `ds_code` | `ds_code` | 堤段编码 |
| `ddgc` | `ddgc` | 堤顶高程（米） |
| `LC` | `lc` | 里程（米） |

---

### 3.06 断面里程对应关系信息

**脚本**: `3.06_risk_section_mileage.py`

#### 📥 输入

| 文件 | 格式 | 说明 |
|-----|------|------|
| `input/dm_LC.geojson` | GeoJSON | 断面里程数据 |

#### 📤 输出

| Sheet名称 | 说明 |
|----------|------|
| `断面里程对应关系信息` | 断面编码与里程对应 |

#### 📋 字段映射

| GeoJSON字段 | Excel字段 | 说明 |
|------------|----------|------|
| `断面编` | `dot_code` | 断面编码（如sx1, sx2） |
| `LC` | `lc` | 里程（米） |

#### ⚠️ 排序规则

按断面编码**自然排序**（sx1, sx2, ..., sx10, sx11）

---

### 3.07 堤防信息

**脚本**: `3.07_risk_dike_info.py`

#### 📥 输入

| 文件 | 格式 | 说明 |
|-----|------|------|
| `input/df_with_elevation_lc.geojson` | GeoJSON | 堤防数据（含高程里程） |

#### 📤 输出

| Sheet名称 | 说明 |
|----------|------|
| `堤防信息` | 堤防详细信息（19个字段） |

#### 📋 字段映射

| GeoJSON字段 | Excel字段 | 说明 |
|------------|----------|------|
| `subCode` | `river_code` | 河流编码（大写） |
| `riverName` | `river_name` | 河流名称 |
| `dikeName` | `dike_code` | 堤防编码（自动生成） |
| `dikeName` | `dike_name` | 堤防名称 |
| `startName` | `start_name` | 起点站 |
| `endName` | `end_name` | 终点站 |
| `zya` | `zya` | 岸别 |
| `polderCode` | `polder_code` | 保护片编码（大写） |
| `qdgc/zdgc` | `qdgc/zdgc` | 起点/终点高程 |
| `qdlc/zdlc` | `qdlc/zdlc` | 起点/终点里程 |
| `dsLength` | `ds_length` | 堤段长度 |
| `lgtd/lttd` | `lgtd/lttd` | 经纬度 |
| `type` | `design_type` | 设计标准 |
| `adcdName` | `addvnm` | 所属区域 |
| `adcdCode` | `addvcd` | 区域编码 |

---

### 3.08 堤防纵剖面数据

**脚本**: `3.08_risk_dike_profile.py`

#### 📥 输入

| 文件 | 格式 | 说明 |
|-----|------|------|
| `input/geojson/dd.geojson` | GeoJSON | 堤段空间数据 |

#### 📤 输出

| Sheet名称 | 说明 |
|----------|------|
| `堤防纵剖面数据` | 纵剖面高程数据 |

#### 📋 字段说明

| Excel字段 | 计算方式 |
|----------|---------|
| `river_code` | 河道编码（大写） |
| `lc` | 里程（米） |
| `river_bottom_elevation` | 河底高程 = 堤顶高程 - 5.0 |
| `river_left_elevation` | 左岸高程（使用堤顶高程） |
| `river_right_elevation` | 右岸高程（使用堤顶高程） |
| `river_plotline` | 是否河道主线（空） |

#### ⚠️ 特殊处理

- **按(河道编码, 里程)分组**：同一里程的左右岸数据合并为一行
- **插值处理**：对左右岸高程进行线性插值填补空值
- **河底高程**：估算值（堤顶高程 - 5米）

---

### 3.09 设施信息

**脚本**: `3.09_risk_facilities.py`

#### 📥 输入

| 文件 | 格式 | 说明 |
|-----|------|------|
| `input/baohu/baohu.geojson` | GeoJSON | 重要设施数据 |
| `input/region_name_code.csv` | CSV | 乡镇编码对照表 |

#### 📤 输出

填充**10个**设施相关Sheet：

| Sheet名称 | 设施类型 | type值 |
|----------|---------|--------|
| `医院` | 医院 | 2 |
| `学校` | 学校 | 1 |
| `公园景点` | 公园景点 | 7 |
| `敬老院` | 敬老院 | 5 |
| `政府机构` | 政府部门 | 10 |
| `危化企业 重要设施基础信息` | 危化企业 | 4 |
| `移动基站` | 移动基站 | 9 |
| `兴趣点` | 兴趣点 | 6 |
| `电站` | 电站 | 8 |
| `水厂` | 水厂 | 3 |
| `重要设施` | 汇总 | 多类型 |

#### 📋 通用字段映射

| GeoJSON字段 | Excel字段 | 说明 |
|------------|----------|------|
| `县（区` | `区县级名称` | 县名称 |
| `town` | `乡镇名称` | 乡镇名称 |
| `名称` | `重要设施名称` | 设施名称 |
| `fac_code` | `设施编码` | 设施编码 |
| `地址` | `详细地址` | 详细地址 |
| `高程` | `设施高程` | 高程 |
| `经度/纬度` | `经度/纬度` | 坐标 |
| `联系电` | `联系人电话` | 联系电话 |
| `polderId` | `保护片编码` | 保护片编码（大写） |
| `grid_id` | `设施所处网格` | 网格ID |

---

## 4. 执行顺序

### 4.1 推荐执行顺序

```bash
#!/bin/bash
# 风险分析表填充 - 批量执行脚本

cd ~/useful_scripts/execute/tools/hydraulic/xlsx/

echo "=========================================="
echo "开始填充风险分析表"
echo "=========================================="

# 按依赖关系顺序执行
echo "[1/9] 填充保护片信息..."
python 3.01_risk_protection_info.py

echo "[2/9] 填充保护片行政区域信息..."
python 3.02_risk_protection_region.py

echo "[3/9] 填充保护片堤段对应关系..."
python 3.03_risk_protection_dike_relation.py

echo "[4/9] 填充堤段对应信息..."
python 3.04_risk_dike_section_info.py

echo "[5/9] 填充堤顶高程对应关系..."
python 3.05_risk_elevation_relation.py

echo "[6/9] 填充断面里程对应关系..."
python 3.06_risk_section_mileage.py

echo "[7/9] 填充堤防信息..."
python 3.07_risk_dike_info.py

echo "[8/9] 填充堤防纵剖面数据..."
python 3.08_risk_dike_profile.py

echo "[9/9] 填充设施信息..."
python 3.09_risk_facilities.py

echo "=========================================="
echo "✅ 所有Sheet填充完成！"
echo "=========================================="
```

### 4.2 单独执行

```bash
# 进入脚本目录
cd ~/useful_scripts/execute/tools/hydraulic/xlsx/

# 执行单个脚本
python 3.01_risk_protection_info.py

# 查看帮助
python 3.01_risk_protection_info.py --help  # 如果支持
```

---

## 5. 常见问题

### 5.1 文件找不到

```
✗ 错误: 找不到 GeoJSON 文件: input/保护片/env.geojson
```

**解决方案**：
1. 检查当前工作目录：`pwd`
2. 确保在正确的工作目录下运行脚本
3. 检查文件路径是否正确

### 5.2 Sheet不存在

```
✗ 错误: 未找到 sheet '保护片信息 '
```

**解决方案**：
1. 确保Excel文件是从正确的模板复制
2. 注意Sheet名称可能有**尾部空格**
3. 检查可用的Sheet名称列表

### 5.3 乡镇编码找不到

```
⚠ 警告: 未找到乡镇'XXX镇'的编码
```

**解决方案**：
1. 检查`input/region_name_code.csv`是否包含该乡镇
2. 确认乡镇名称是否完全匹配（无多余空格）

### 5.4 编码格式问题

**自动处理**：所有脚本会自动将编码转换为大写（如 `sx0001` → `SX0001`）

---

## 📊 输入输出汇总表

| 脚本 | 输入文件 | 输出Sheet | 核心功能 |
|-----|---------|----------|---------|
| `3.01` | env.geojson, CSV | 保护片信息 | 保护片基本信息 |
| `3.02` | env.geojson, CSV, region_code | 保护片行政区域信息 | 保护片-乡镇关系 |
| `3.03` | dd_fix.geojson | 保护片堤段对应关系信息 | 保护片-堤段关系 |
| `3.04` | dd.geojson | 堤段对应信息 | 堤段详细信息 |
| `3.05` | dd.geojson | 保护片堤段堤顶高程对应关系信息 | 高程-里程关系 |
| `3.06` | dm_LC.geojson | 断面里程对应关系信息 | 断面-里程关系 |
| `3.07` | df_with_elevation_lc.geojson | 堤防信息 | 堤防详细信息 |
| `3.08` | dd.geojson | 堤防纵剖面数据 | 纵剖面高程 |
| `3.09` | baohu.geojson, region_code | 10个设施Sheet | 各类设施信息 |

---

## 🔗 相关文档

| 文档 | 位置 |
|-----|------|
| QGIS空间处理手册 | `风险图/熟溪风险图操作手册.md` |
| 公共库说明 | `lib/xlsx_common/README.md` |
| 项目记忆 | `.cursor/rules/project-risk-analysis.mdc` |

---

## 🔄 版本记录

| 版本 | 日期 | 更新内容 |
|-----|------|---------|
| v1.0 | 2025-12-09 | 初始版本 |


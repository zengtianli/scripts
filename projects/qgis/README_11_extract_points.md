# 点在面内提取工具 - 使用说明

## 📌 功能说明

提取点图层A中落在面图层B内部的所有点，生成新的点图层。

## 🚀 快速开始

### 方法1：在QGIS Python控制台运行（推荐）

1. **打开QGIS，加载你的点图层和面图层**

2. **修改脚本配置**（重要！）
   
   打开 `11_extract_points_in_polygons.py`，修改这几行：
   
   ```python
   # 改成你在QGIS中的实际图层名称
   POINT_LAYER = "你的点图层名称"        # 例如: "monitoring_points"
   POLYGON_LAYER = "你的面图层名称"      # 例如: "study_area"
   OUTPUT_LAYER_NAME = "输出图层名称"    # 例如: "filtered_points"
   
   # 是否需要继承面图层的属性
   INHERIT_ATTRIBUTES = False           # True=继承, False=不继承
   ```

3. **在QGIS Python控制台运行**
   
   打开 QGIS → 插件 → Python控制台，粘贴以下代码：
   
   ```python
   exec(open('~/useful_scripts/.assets/projects/qgis/11_extract_points_in_polygons.py').read())
   ```
   
   或者使用编译方式（更稳定）：
   
   ```python
   from pathlib import Path
   script_path = Path('~/useful_scripts/.assets/projects/qgis/11_extract_points_in_polygons.py')
   exec(compile(script_path.read_text(), script_path.name, 'exec'))
   ```

4. **查看结果**
   
   - 输出图层会自动出现在 **process** 组中
   - 输入图层会自动移到 **input** 组中

### 方法2：从终端运行

```bash
cd ~/useful_scripts/.assets/projects/qgis

# 方式1: 使用便捷脚本
./run_11.sh

# 方式2: 使用通用运行脚本
./run_script.sh 11_extract_points_in_polygons.py
```

## ⚙️ 配置选项详解

### 1. 基础配置

```python
POINT_LAYER = "points"          # 点图层名称（必须修改）
POLYGON_LAYER = "polygons"      # 面图层名称（必须修改）
OUTPUT_LAYER_NAME = "result"    # 输出图层名称
```

### 2. 是否继承面图层属性

```python
INHERIT_ATTRIBUTES = False
```

- **False（默认）**：输出点只保留原点图层的属性
  - 速度快
  - 适合只需要筛选点的场景
  
- **True**：输出点会继承所在面的所有属性
  - 面图层的字段会添加 `poly_` 前缀
  - 例如：面图层有字段 `name`，输出点会有字段 `poly_name`
  - 适合需要知道点属于哪个面的场景

### 3. 空间关系类型

```python
SPATIAL_PREDICATE = [0]  # 默认：相交(intersects)
```

可选值：
- `[0]` - **相交(intersects)**：点与面有任何重叠（推荐）
- `[6]` - **包含(within)**：点必须完全在面内部（更严格）
- `[0, 6]` - 同时满足多个条件

## 💡 实际应用场景

### 场景1：提取研究区域内的采样点

```python
POINT_LAYER = "all_sampling_points"    # 所有采样点
POLYGON_LAYER = "study_area"           # 研究区域边界
OUTPUT_LAYER_NAME = "sampling_in_area"
INHERIT_ATTRIBUTES = False
```

**结果**：得到研究区域内的所有采样点

### 场景2：统计每个县的POI数量（需要县名）

```python
POINT_LAYER = "city_poi"               # 全市POI
POLYGON_LAYER = "county_boundaries"    # 县界（包含县名字段）
OUTPUT_LAYER_NAME = "poi_with_county"
INHERIT_ATTRIBUTES = True              # 继承县名
```

**结果**：每个POI点会带上 `poly_县名` 字段，可以后续统计

### 场景3：提取保护区内的监测点

```python
POINT_LAYER = "monitoring_stations"    # 监测站点
POLYGON_LAYER = "protected_zones"      # 保护区范围
OUTPUT_LAYER_NAME = "stations_in_zones"
INHERIT_ATTRIBUTES = True              # 继承保护区信息
```

**结果**：监测点带上保护区编号、等级等信息

## 📊 输出说明

运行成功后，控制台会显示：

```
✅ 点在面内提取完成！
   输出: points_in_polygons (process组)
   结果: 850/1000 个点 (85.0%)
   说明: 仅保留原点图层属性
```

统计信息包括：
- 原始点数
- 提取的点数
- 提取比例
- 字段数量
- 继承的字段（如果开启）

## ⚠️ 常见问题

### Q1: 脚本报错 "找不到图层"

**原因**：图层名称配置错误

**解决**：
1. 在QGIS中确认你的图层名称（图层面板中显示的名称）
2. 修改脚本中的 `POINT_LAYER` 和 `POLYGON_LAYER` 与实际名称完全一致

### Q2: 提取的点数为0

**可能原因**：
1. 点和面没有空间重叠
2. 坐标系不一致（脚本会自动重投影，但检查一下）
3. 使用了 `within` 而点在边界上

**解决**：
- 检查点和面是否真的有重叠（在QGIS中目视检查）
- 尝试改为 `SPATIAL_PREDICATE = [0]`（相交）

### Q3: 坐标系不一致警告

**解决**：脚本会自动重投影，不需要手动处理

### Q4: 输出点的属性字段很乱

**解决**：
- 如果不需要面属性，设置 `INHERIT_ATTRIBUTES = False`
- 如果需要面属性但字段名冲突，面字段会自动加上 `poly_` 前缀

## 🔧 技术说明

### 使用的QGIS处理算法

1. **不继承属性**：`native:extractbylocation`
   - 纯粹的空间筛选
   - 性能高

2. **继承属性**：`native:joinattributesbylocation`
   - 空间连接
   - 会添加面图层的所有字段

### 自动处理的内容

- ✅ 坐标系不一致 → 自动重投影
- ✅ 几何错误 → 自动修复
- ✅ 图层组织 → 自动分组（input/process）
- ✅ 同名图层 → 自动覆盖旧版本

## 📝 修改记录

- 2025-11-25：创建脚本，支持QGIS和终端双模式运行


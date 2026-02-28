# QGIS 工具脚本 - 快速入门指南

## 📦 最新工具（2025-11-25）

你现在有3个强大的QGIS工具脚本：

| 脚本 | 功能 | 使用场景 |
|------|------|----------|
| **11_extract_points_in_polygons.py** | 点在面内提取 | 筛选区域内的点数据 |
| **12_create_mask_layers.py** | 蒙版图层生成 | 突出显示特定区域 |
| **13_export_map_layout.py** | 地图出图 | 导出专业地图（含图例、比例尺、指北针） |

---

## 🚀 典型工作流程

### 情景：制作景宁县区域分析地图

#### 第1步：数据准备
```
在QGIS中加载：
• jingning（景宁县边界）
• RSAA（采样点数据）
• 底图（卫星影像或地形图）
```

#### 第2步：提取区域内的点
```python
# 运行脚本11：提取景宁县内的RSAA点
# 配置：POINT_LAYER = "RSAA", POLYGON_LAYER = "jingning"
exec(open('~/useful_scripts/.assets/projects/qgis/11_extract_points_in_polygons.py').read())

结果：得到 points_in_polygons 图层（景宁县内的点）
```

#### 第3步：创建蒙版突出显示
```python
# 运行脚本12：创建蒙版，突出显示景宁县
# 配置：INNER_LAYER = "jingning", OUTER_LAYER = "all"
exec(open('~/useful_scripts/.assets/projects/qgis/12_create_mask_layers.py').read())

结果：景宁县透明度50%（清晰），其他区域透明度10%（模糊）
```

#### 第4步：导出专业地图
```python
# 调整QGIS视图到合适位置
# 运行脚本13：导出地图
# 配置：MAP_TITLE = "景宁县RSAA采样点分布图"
exec(open('~/useful_scripts/.assets/projects/qgis/13_export_map_layout.py').read())

结果：桌面生成高质量地图（包含图例、比例尺、指北针）
```

---

## 📚 详细使用说明

### 工具1：点在面内提取 (11)

**用途**：筛选点数据

```python
# 配置
POINT_LAYER = "RSAA"          # 你的点图层名
POLYGON_LAYER = "jingning"    # 你的面图层名
OUTPUT_LAYER_NAME = "filtered_points"
INHERIT_ATTRIBUTES = False    # 是否继承面属性

# 运行
exec(open('.../11_extract_points_in_polygons.py').read())
```

**详细文档**：[README_11_extract_points.md](README_11_extract_points.md)

---

### 工具2：蒙版图层生成 (12)

**用途**：突出显示特定区域

```python
# 配置
INNER_LAYER = "jingning"      # 内部区域（高透明度）
OUTER_LAYER = "all"           # 外部区域："all"或具体图层
INNER_OPACITY = 50            # 内部透明度 (0-100)
OUTER_OPACITY = 10            # 外部透明度 (0-100)
MASK_COLOR = (255, 255, 255)  # 蒙版颜色(白色)

# 运行
exec(open('.../12_create_mask_layers.py').read())
```

**效果**：
- ✨ jingning 区域更透明（底图清晰）
- 🔲 其他区域被白色蒙版遮挡（弱化显示）

**详细文档**：[README_12_mask.md](README_12_mask.md)

---

### 工具3：地图出图 (13)

**用途**：导出专业地图

```python
# 配置
MAP_TITLE = "景宁县区域分析图"
OUTPUT_DIR = Path.home() / "Desktop"
OUTPUT_FORMAT = "png"         # png/pdf/jpg
PAGE_SIZE = "A3"              # A4/A3/A2/A1/A0
ORIENTATION = "landscape"     # landscape/portrait
DPI = 300                     # 分辨率

SHOW_LEGEND = True            # 图例
SHOW_SCALE_BAR = True         # 比例尺
SHOW_NORTH_ARROW = True       # 指北针

# 运行（先在QGIS中调整好视图！）
exec(open('.../13_export_map_layout.py').read())
```

**输出**：自动生成包含所有元素的专业地图

**详细文档**：[README_13_export.md](README_13_export.md)

---

## 🎯 常见应用组合

### 组合1：研究区域数据展示

```
步骤1：提取区域内的数据点 (脚本11)
步骤2：创建蒙版突出研究区 (脚本12)
步骤3：导出专业地图 (脚本13)
```

### 组合2：多区域对比

```
运行脚本11多次，提取不同区域的点
每个区域用不同颜色标注
运行脚本13导出对比图
```

### 组合3：快速出图（不需要点数据）

```
直接运行脚本13
无需脚本11和12
适合已有完整数据的情况
```

---

## ⚙️ 配置检查工具

每个脚本都有配置检查工具，运行前建议先检查：

```python
# 检查脚本11配置
exec(open('.../11_check_config.py').read())

# 检查脚本12配置
exec(open('.../12_check_mask_config.py').read())

# 脚本13无需检查，直接运行即可
```

---

## 📁 文件结构

```
tools/hydraulic/qgis/
├── 11_extract_points_in_polygons.py  # 点在面内提取
├── 11_check_config.py                # 配置检查
├── run_11.sh                         # 快速运行
│
├── 12_create_mask_layers.py          # 蒙版生成
├── 12_check_mask_config.py           # 配置检查
├── run_12.sh                         # 快速运行
│
├── 13_export_map_layout.py           # 地图出图
├── run_13.sh                         # 快速运行
│
├── qgis_util.py                      # 工具函数库
│
├── README_11_extract_points.md       # 脚本11详细说明
├── README_12_mask.md                 # 脚本12详细说明
├── README_13_export.md               # 脚本13详细说明
└── README_QUICK_START.md             # 本文件
```

---

## 💡 使用技巧

### 1. 在QGIS Python控制台运行

```python
# 方法1：直接执行（推荐）
exec(open('~/useful_scripts/.assets/projects/qgis/13_export_map_layout.py').read())

# 方法2：使用Path（更安全）
from pathlib import Path
script = Path('~/useful_scripts/.assets/projects/qgis/13_export_map_layout.py')
exec(compile(script.read_text(), script.name, 'exec'))
```

### 2. 从终端运行

```bash
cd ~/useful_scripts/.assets/projects/qgis
./run_11.sh  # 运行脚本11
./run_12.sh  # 运行脚本12
./run_13.sh  # 运行脚本13
```

### 3. 快速修改配置

打开脚本，找到 `# ============ 配置参数 ============` 部分，修改参数后保存即可。

---

## 🔧 故障排除

### 问题1：找不到图层

```
✅ 确认QGIS中已加载该图层
✅ 检查图层名称拼写（大小写敏感）
✅ 运行配置检查工具查看可用图层
```

### 问题2：ModuleNotFoundError

```
✅ 所有脚本已修复路径问题
✅ 确保在正确的目录下运行
✅ 确保qgis_util.py存在
```

### 问题3：输出结果不理想

```
脚本11：检查点和面是否有空间重叠
脚本12：调整透明度参数（INNER_OPACITY, OUTER_OPACITY）
脚本13：调整DPI、页面大小、元素开关
```

---

## 📞 快速帮助

| 需求 | 解决方案 |
|------|----------|
| 不知道图层名 | 运行配置检查工具 |
| 效果不满意 | 调整配置参数重新运行 |
| 需要修改样式 | 在QGIS中手动调整图层样式 |
| 导出失败 | 检查输出路径权限 |

---

## 🎓 学习路径

1. **入门**：先运行脚本13出图，了解基本流程
2. **进阶**：使用脚本11筛选数据
3. **高级**：组合使用脚本11、12、13制作专业地图

---

## ✨ 最佳实践

1. ✅ **运行前检查**：使用配置检查工具验证设置
2. ✅ **保存项目**：重要工作记得保存QGIS项目
3. ✅ **命名规范**：图层用英文命名，避免特殊字符
4. ✅ **视图调整**：脚本13运行前先调整好地图视图
5. ✅ **分步执行**：复杂任务分步骤进行，便于调试

---

## 📝 更新日志

- **2025-11-25**：创建三个核心工具脚本
  - 11: 点在面内提取
  - 12: 蒙版图层生成（支持"all"选项）
  - 13: 地图出图（含图例、比例尺、指北针）







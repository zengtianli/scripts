# 地图出图工具 - 使用说明

## 📌 功能说明

自动创建专业的地图布局，包含：
- ✅ 地图主体
- ✅ 图例（Legend）
- ✅ 比例尺（Scale Bar）
- ✅ 指北针（North Arrow）
- ✅ 标题
- ✅ 日期和制图信息

一键导出高质量地图（PNG/PDF/JPG）。

## 🚀 快速使用

### 1. 在QGIS中准备地图

1. **调整地图视图**
   - 缩放、平移到你想要的区域
   - 打开/关闭需要显示的图层
   - 调整图层顺序和样式

2. **确认当前视图**
   - 脚本会使用当前QGIS画布的视图范围
   - 所有可见图层都会包含在输出中

### 2. 修改配置（可选）

打开 `13_export_map_layout.py`，修改配置：

```python
# 地图标题
MAP_TITLE = "景宁县区域分析图"  # 改成你的标题

# 输出设置
OUTPUT_DIR = Path.home() / "Desktop"  # 保存位置（默认桌面）
OUTPUT_FILENAME = "map_export"        # 文件名
OUTPUT_FORMAT = "png"                 # 格式: png/pdf/jpg

# 页面设置
PAGE_SIZE = "A3"                      # A4/A3/A2/A1/A0
ORIENTATION = "landscape"             # landscape横向/portrait纵向
DPI = 300                             # 分辨率（打印用300）
```

### 3. 运行脚本

**方法1：在QGIS Python控制台（推荐）**

```python
exec(open('~/useful_scripts/.assets/projects/qgis/13_export_map_layout.py').read())
```

**方法2：从终端运行**

```bash
cd ~/useful_scripts/.assets/projects/qgis
./run_13.sh
```

### 4. 查看结果

- 文件自动保存到桌面（或指定路径）
- 文件名格式：`map_export_20251125_143052.png`（包含时间戳）
- 脚本执行完会弹窗显示文件路径，可直接打开

## ⚙️ 配置参数详解

### 标题设置

```python
MAP_TITLE = "景宁县区域分析图"       # 主标题
MAP_SUBTITLE = "2024年数据分析"      # 副标题（可选）
```

### 输出设置

```python
OUTPUT_DIR = Path.home() / "Desktop"           # 保存位置
OUTPUT_DIR = Path("/Users/tianli/Documents")   # 也可以指定绝对路径

OUTPUT_FILENAME = "jingning_map"               # 文件名（不含扩展名）
OUTPUT_FORMAT = "png"                          # 格式
```

**支持的格式**：
- `png` - PNG图片（推荐，支持透明背景）
- `pdf` - PDF文档（矢量图，可无损缩放）
- `jpg` - JPEG图片（文件小，但有损压缩）

### 页面设置

```python
PAGE_SIZE = "A3"         # 页面大小
ORIENTATION = "landscape" # 页面方向
```

**标准页面尺寸**：

| 尺寸 | 横向 (mm) | 纵向 (mm) | 适用场景 |
|------|-----------|-----------|----------|
| A4 | 297×210 | 210×297 | 报告、论文 |
| A3 | 420×297 | 297×420 | 海报、展板 |
| A2 | 594×420 | 420×594 | 大型展板 |
| A1 | 841×594 | 594×841 | 工程图纸 |
| A0 | 1189×841 | 841×1189 | 特大海报 |

**方向选择**：
- `landscape` - 横向（宽>高，推荐）
- `portrait` - 纵向（高>宽）

### 分辨率设置

```python
DPI = 300  # 每英寸点数
```

**DPI建议**：
- **72-96 DPI** - 屏幕显示、网页
- **150 DPI** - 快速预览、草稿
- **300 DPI** - 打印输出（推荐）
- **600 DPI** - 高质量打印、出版

### 元素开关

```python
SHOW_LEGEND = True        # 显示图例
SHOW_SCALE_BAR = True     # 显示比例尺
SHOW_NORTH_ARROW = True   # 显示指北针
SHOW_DATE = True          # 显示日期
SHOW_CREDITS = True       # 显示制图信息
```

### 图例设置

```python
LEGEND_TITLE = "图例"     # 图例标题
# 图例会自动包含所有可见图层
# 图例位置：地图右侧
```

### 比例尺设置

```python
SCALE_BAR_UNITS = "m"     # 单位
```

**单位选项**：
- `m` - 米（默认）
- `km` - 千米
- `ft` - 英尺

### 其他文本

```python
CREDITS_TEXT = "数据来源: QGIS"    # 制图信息
# 可以改为: "数据来源: 国家基础地理信息中心"
```

## 💡 实际应用场景

### 场景1：报告配图（A4纵向）

```python
MAP_TITLE = "研究区域位置图"
OUTPUT_FORMAT = "png"
PAGE_SIZE = "A4"
ORIENTATION = "portrait"
DPI = 300
SHOW_LEGEND = True
SHOW_SCALE_BAR = True
SHOW_NORTH_ARROW = True
```

### 场景2：大幅海报（A1横向）

```python
MAP_TITLE = "景宁县生态保护区划分"
OUTPUT_FORMAT = "pdf"  # PDF矢量图，可无损放大
PAGE_SIZE = "A1"
ORIENTATION = "landscape"
DPI = 300
```

### 场景3：网页展示（低分辨率）

```python
MAP_TITLE = "在线地图"
OUTPUT_FORMAT = "jpg"
PAGE_SIZE = "A4"
ORIENTATION = "landscape"
DPI = 96  # 屏幕分辨率
```

### 场景4：出版印刷（高质量）

```python
MAP_TITLE = "论文插图"
OUTPUT_FORMAT = "pdf"
PAGE_SIZE = "A4"
ORIENTATION = "landscape"
DPI = 600  # 高质量
```

## 🎨 布局说明

脚本自动生成的布局结构：

```
┌────────────────────────────────────────────────┐
│                 [标题]                         │
├───────────────────────────────┬────────────────┤
│                               │                │
│                               │   [图例]       │
│         [地图主体]            │                │
│                               │                │
│                               │                │
│  [比例尺]          [指北针]   │                │
├───────────────────────────────┴────────────────┤
│ [日期]                         [制图信息]      │
└────────────────────────────────────────────────┘
```

## 📊 输出示例

运行成功后会显示：

```
✅ 地图出图完成！
═══════════════════════════════════════════

📁 输出文件:
   /Users/tianli/Desktop/map_export_20251125_143052.png

📊 布局信息:
   • 布局名称: map_layout_20251125_143052
   • 页面尺寸: A3 landscape
   • 输出格式: PNG
   • 分辨率: 300 DPI

🎨 包含元素:
   ✓ 标题: 景宁县区域分析图
   ✓ 图例
   ✓ 比例尺
   ✓ 指北针
   ✓ 日期
```

## 🔧 高级技巧

### 1. 自定义页面尺寸

```python
PAGE_SIZE = "Custom"
CUSTOM_WIDTH = 420   # 宽度（毫米）
CUSTOM_HEIGHT = 297  # 高度（毫米）
```

### 2. 调整边距

```python
MARGIN_TOP = 15      # 上边距（毫米）
MARGIN_BOTTOM = 15   # 下边距
MARGIN_LEFT = 15     # 左边距
MARGIN_RIGHT = 15    # 右边距
```

### 3. 修改图例标题

```python
LEGEND_TITLE = "Legend"        # 英文
LEGEND_TITLE = "レジェンド"    # 日文
LEGEND_TITLE = ""              # 不显示标题
```

### 4. 隐藏某些元素

```python
SHOW_LEGEND = False      # 不显示图例
SHOW_SCALE_BAR = False   # 不显示比例尺
MAP_TITLE = ""           # 不显示标题
```

## ⚠️ 常见问题

### Q1: 地图范围不对

**原因**：脚本使用当前QGIS画布的视图范围

**解决**：运行脚本前，在QGIS中调整好地图视图

### Q2: 图例太长，遮挡地图

**原因**：图层太多或图层名称太长

**解决**：
1. 关闭不需要显示的图层
2. 重命名图层，使用简短名称
3. 改用更大的页面尺寸（如A3→A2）

### Q3: 比例尺单位不合适

**原因**：默认使用米(m)

**解决**：修改 `SCALE_BAR_UNITS`
```python
SCALE_BAR_UNITS = "km"  # 改为千米
```

### Q4: 指北针不显示

**原因**：找不到指北针SVG文件

**解决**：
1. 检查QGIS安装路径
2. 或设置 `SHOW_NORTH_ARROW = False` 暂时关闭

### Q5: 输出文件很大

**原因**：DPI过高或使用PNG格式

**解决**：
```python
DPI = 150           # 降低分辨率
OUTPUT_FORMAT = "jpg"  # 改用JPG（更小）
```

### Q6: PDF文件无法打开

**原因**：导出失败或文件损坏

**解决**：
1. 检查输出路径是否有写入权限
2. 改用PNG格式测试
3. 检查QGIS版本（需3.x以上）

## 📝 批量出图

如果需要导出多个地图，可以修改脚本，循环不同的视图范围：

```python
# 示例：批量导出不同区域
regions = [
    ("jingning", extent1),
    ("county", extent2),
]

for name, extent in regions:
    MAP_TITLE = f"{name}区域图"
    OUTPUT_FILENAME = f"map_{name}"
    map_item.setExtent(extent)
    # ... 导出
```

## 🎬 完整工作流程

1. **准备数据** → 加载所有需要的图层
2. **样式设计** → 设置图层颜色、符号
3. **视图调整** → 缩放到合适范围
4. **运行脚本** → 自动创建布局
5. **检查输出** → 查看导出的图片
6. **微调参数** → 如需修改，调整配置重新运行

## 💻 系统要求

- QGIS 3.x 或更高版本
- Python 3.x
- 足够的磁盘空间（高分辨率输出可能>10MB）

## 📚 相关资源

- QGIS布局管理器文档
- 地图制图规范
- 符号化样式库







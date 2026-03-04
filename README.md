# useful_scripts

macOS 个人效率工具脚本库，主要通过 Raycast 调用。包含 80+ 个功能脚本和 12 个复杂项目，覆盖文档处理、数据转换、文件操作、系统工具、秘书系统、水利工程等领域。

## 快速开始

### 环境要求

- macOS 12+
- Python 3.9+
- Node.js 18+ (for projects)
- Raycast (推荐)

### 安装依赖

```bash
# Python 依赖
pip3 install -r requirements.txt

# Node.js 项目依赖（如需使用 Streamlit 项目）
cd projects/{project_name}
pip3 install -r requirements.txt
```

### Raycast 集成

1. 打开 Raycast 设置（⌘ + ,）
2. 进入 Extensions → Script Commands
3. 添加脚本目录：`~/useful_scripts/raycast/commands`
4. 刷新脚本列表

现在可以通过 Raycast 快速调用所有脚本（68 个命令）。

## 脚本索引

### 数据处理（data/）

| 脚本 | 功能 | Raycast 命令 |
|------|------|--------------|
| csv_from_txt.py | TXT 转 CSV | ✓ |
| csv_to_txt.py | CSV 转 TXT | ✓ |
| csv_merge_txt.py | 合并 TXT 到 CSV | ✓ |
| xlsx_from_csv.py | CSV 转 Excel | ✓ |
| xlsx_from_txt.py | TXT 转 Excel | ✓ |
| xlsx_to_csv.py | Excel 转 CSV | ✓ |
| xlsx_to_txt.py | Excel 转 TXT | ✓ |
| xlsx_lowercase.py | Excel 列名转小写 | ✓ |
| xlsx_merge_tables.py | 合并多个 Excel 表 | ✓ |
| xlsx_splitsheets.py | 拆分 Excel 工作表 | ✓ |
| xlsx_encode_duplicates.py | Excel 重复项编号 | - |

### 文档处理（document/）

| 脚本 | 功能 | Raycast 命令 |
|------|------|--------------|
| docx_text_formatter.py | Word 文档格式化 | ✓ |
| docx_apply_image_caption.py | Word 图片题注 | ✓ |
| docx_zdwp_all.py | Word 一键格式化（水利） | ✓ |
| md_formatter.py | Markdown 格式化 | ✓ |
| md_merge.py | 合并 Markdown 文件 | ✓ |
| md_split_by_heading.py | 按标题拆分 Markdown | ✓ |
| md_docx_template.py | Markdown 转 Word（模板） | ✓ |
| pptx_font_yahei.py | PPT 字体统一（微软雅黑） | ✓ |
| pptx_table_style.py | PPT 表格样式 | ✓ |
| pptx_text_formatter.py | PPT 文本格式化 | ✓ |
| pptx_apply_all.py | PPT 一键格式化 | ✓ |
| pptx_to_md.py | PPT 转 Markdown | ✓ |

### 文件操作（file/）

| 脚本 | 功能 | Raycast 命令 |
|------|------|--------------|
| folder_create.py | 批量创建文件夹 | ✓ |
| folder_add_prefix.py | 文件夹批量加前缀 | ✓ |
| folder_move_up_remove.py | 文件夹上移并删除 | ✓ |
| file_copy.py | 文件复制 | - |
| file_run.py | 文件运行 | - |
| file_print.py | 文件打印 | - |

### 系统工具（system/）

| 脚本 | 功能 | Raycast 命令 |
|------|------|--------------|
| sys_app_launcher.py | 应用启动器 | ✓ |
| app_tracker.py | 应用使用追踪 | - |
| app_report.py | 应用使用报告 | - |
| display_1080.sh | 切换到 1080p | - |
| display_4k.sh | 切换到 4K | - |
| create_reminder.sh | 创建提醒事项 | - |
| daily_work_reminder.sh | 每日工作提醒 | - |
| weekly_review_reminder.sh | 周回顾提醒 | - |
| dingtalk_gov.sh | 钉钉政务版 | ✓ |

### 秘书系统（secretary/）

| 脚本 | 功能 | Raycast 命令 |
|------|------|--------------|
| sec_log.py | 秘书日志 | - |
| sec_report.py | 秘书报告 | - |
| sec_review.py | 秘书回顾 | - |
| daily_summary.py | 每日总结 | - |
| daily_report.py | 每日报告 | - |
| daily_review.py | 每日回顾 | - |
| work_log.py | 工作日志 | - |
| work_report.py | 工作报告 | - |
| personal_log.py | 个人日志 | - |
| personal_report.py | 个人报告 | - |
| learning_log.py | 学习日志 | - |
| learning_report.py | 学习报告 | - |
| investment_log.py | 投资日志 | - |
| investment_report.py | 投资报告 | - |
| life_log.py | 生活日志 | - |
| life_report.py | 生活报告 | - |
| collector.py | 数据收集器 | - |
| conversation_analyzer.py | 对话分析器 | - |
| file_tracker.py | 文件追踪器 | - |
| project_manager.py | 项目管理器 | - |

**注**：秘书系统已整合到 OA 总控（`~/Dev/oa-project`），通过 Web 界面使用。

### 网络工具（network/）

| 脚本 | 功能 | Raycast 命令 |
|------|------|--------------|
| clashx_status.sh | ClashX 状态 | ✓ |
| clashx_mode_rule.sh | ClashX 规则模式 | ✓ |
| clashx_mode_global.sh | ClashX 全局模式 | ✓ |
| clashx_mode_direct.sh | ClashX 直连模式 | ✓ |
| clashx_proxy.sh | ClashX 代理切换 | ✓ |
| clashx_enhanced.sh | ClashX 增强模式 | ✓ |

### 窗口管理（window/）

| 脚本 | 功能 | Raycast 命令 |
|------|------|--------------|
| yabai_org.py | 窗口布局管理 | ✓ |
| yabai_toggle.py | Yabai 开关 | ✓ |
| yabai_float.py | 窗口浮动 | ✓ |
| yabai_mouse_follow.py | 鼠标跟随 | ✓ |

### 通用工具（tools/）

| 脚本 | 功能 | Raycast 命令 |
|------|------|--------------|
| tts_volcano.py | 文本转语音（火山引擎） | - |
| gantt_timeline.py | 甘特图生成 | - |
| quarto_init.py | Quarto 项目初始化 | - |
| app_open.py | 应用打开 | ✓ |

### 水利工程（hy_）

| 脚本 | 功能 | Raycast 命令 |
|------|------|--------------|
| hy_capacity.sh | 纳污能力计算 | ✓ |
| hy_geocode.sh | 地理编码 | ✓ |
| hy_reservoir.sh | 水库调度 | ✓ |
| hy_water_efficiency.sh | 用水效率 | ✓ |

**注**：这些是 Streamlit 项目的快捷启动命令，实际项目在 `projects/` 目录。

## 项目索引

### Streamlit 应用

| 项目 | 功能 | 启动命令 |
|------|------|----------|
| capacity | 纳污能力计算 | `streamlit run projects/capacity/app.py` |
| geocode | 地理编码 | `streamlit run projects/geocode/app.py` |
| reservoir_schedule | 水库调度 | `streamlit run projects/reservoir_schedule/app.py` |
| irrigation | 灌溉需水 | `streamlit run projects/irrigation/webapp/app.py` |
| district_scheduler | 区域调度 | `streamlit run projects/district_scheduler/webapp/app.py` |
| water_efficiency | 用水效率 | `streamlit run projects/water_efficiency/app.py` |

### CLI 工具

| 项目 | 功能 | 使用方式 |
|------|------|----------|
| risk_data | 风险分析表填充 | `python3 projects/risk_data/main.py` |
| company_query | 企业查询 | `python3 projects/company_query/main.py` |
| qgis | QGIS 空间处理 | 见 `projects/qgis/README.md` |

### 其他项目

| 项目 | 功能 | 说明 |
|------|------|------|
| cad | CAD 脚本 | AutoCAD 自动化脚本 |
| rainfall | 降雨数据 | 降雨数据处理 |
| water_annual | 年度水资源数据 | 年度水资源数据处理 |

## 项目结构

```
useful_scripts/
├── scripts/              # 功能脚本，按类别分组
│   ├── data/             # 数据转换（11 个脚本）
│   ├── document/         # 文档处理（15 个脚本）
│   ├── file/             # 文件操作（7 个脚本）
│   ├── system/          # 系统工具（9 个脚本）
│   ├── secretary/        # 秘书系统（20 个脚本）
│   ├── network/          # 网络代理（6 个脚本）
│   ├── window/           # 窗口管理（4 个脚本）
│   └── tools/            # 杂项工具（4 个脚本）
│
├── lib/                  # 统一公共库
│   ├── core/             # 核心处理逻辑
│   │   ├── csv_core.py   # CSV 处理核心
│   │   ├── docx_core.py  # Word 处理核心
│   │   └── xlsx_core.py  # Excel 处理核心
│   ├── hydraulic/        # 水利领域专用库
│   │   ├── __init__.py   # 编码映射
│   │   └── qgis_config.py # QGIS 配置
│   ├── tools/            # 项目维护工具
│   │   ├── health_check.py # 健康检查
│   │   └── sync_index.py   # 同步索引
│   ├── asr/              # 语音识别词表数据
│   └── *.py / *.sh       # 公共模块
│       ├── common.sh     # Shell 公共库
│       ├── common_utils.py # Python 公共库
│       ├── display.sh    # 显示器管理
│       ├── file_ops.py   # 文件操作
│       ├── finder.py     # Finder 操作
│       └── excel_ops.py  # Excel 操作
│
├── projects/             # 复杂多文件项目（内部自治）
│   ├── capacity/         # 纳污能力计算（Streamlit）
│   ├── geocode/          # 地理编码（Streamlit）
│   ├── reservoir_schedule/ # 水库调度（Streamlit）
│   ├── irrigation/       # 灌溉需水（Streamlit）
│   ├── district_scheduler/ # 区域调度（Streamlit）
│   ├── water_efficiency/ # 用水效率（Streamlit）
│   ├── risk_data/        # 风险分析表填充（CLI）
│   ├── company_query/    # 企业查询（CLI）
│   ├── qgis/             # QGIS 空间处理（Pipeline）
│   ├── cad/              # CAD 脚本
│   ├── rainfall/         # 降雨数据
│   └── water_annual/     # 年度水资源数据
│
├── raycast/              # Raycast 入口
│   ├── commands/         # Shell wrapper 脚本（68 个命令）
│   └── lib/              # 运行器
│       ├── run_python.sh # Python 脚本运行器
│       └── common.sh     # 公共函数
│
├── templates/            # 模板文件
│   └── zdwp_template.docx # 水利公司 Word 模板
│
├── _index/               # 脚本索引
│   ├── by-function.md    # 按功能分类
│   ├── by-platform.md    # 按平台分类
│   └── by-type.md        # 按类型分类
│
├── docs/                 # 文档
│   └── MIGRATION_PLAN.md # 迁移计划
│
├── requirements.txt      # Python 依赖
├── CLAUDE.md             # Claude Code 说明
└── README.md             # 本文件
```

## 开发指南

### 添加新脚本

1. **在对应分类下创建脚本**

```bash
# 例如：添加数据处理脚本
touch scripts/data/new_script.py
chmod +x scripts/data/new_script.py
```

2. **添加 shebang 和导入**

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

# 添加 lib 到 sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

# 导入公共库
from common_utils import ...
from excel_ops import ...
from core.xlsx_core import ...
```

3. **创建 Raycast wrapper**

```bash
# 复制模板
cp raycast/commands/_template.sh raycast/commands/new_script.sh

# 编辑 wrapper
# 1. 修改 @raycast 元数据（title, description, icon）
# 2. 修改调用路径：run_python "data/new_script.py"
```

4. **运行健康检查**

```bash
python3 lib/tools/health_check.py
```

### 命名规范

**脚本命名**：
- 文档处理：`docx_`、`md_`、`pptx_`
- 数据转换：`xlsx_`、`csv_`
- 文件操作：`file_`、`folder_`
- 系统工具：`sys_`、`display_`
- 秘书系统：`sec_`（secretary）
- 水利领域：`hy_`（hydraulic）
- 窗口管理：`yabai_`
- 网络工具：`clashx_`

**Raycast 命令**：
- 与脚本文件名保持一致
- 使用小写 + 下划线
- 例如：`docx_text_formatter.sh` → `docx_text_formatter`

### 引用路径规范

**Shell 脚本引用库**：
```bash
# 获取脚本所在目录的父目录的父目录（即项目根目录）
source "$(dirname "$0")/../../lib/common.sh"
```

**Python 脚本引用库**：

```python
# scripts/ 下的脚本
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

# projects/ 下的脚本
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "lib"))
```

**导入公共库**：
```python
# 通用工具
from common_utils import ...

# Excel 操作
from excel_ops import ...

# 核心模块
from core.docx_core import ...
from core.xlsx_core import ...
from core.csv_core import ...

# 水利领域
from hydraulic import ...
from hydraulic.qgis_config import ...
```

### Raycast 脚本开发

**Wrapper 结构**：
```bash
#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title 脚本标题
# @raycast.mode compact
# @raycast.packageName useful_scripts
# @raycast.icon 🔧

# Optional parameters:
# @raycast.description 脚本描述

# Documentation:
# @raycast.author tianli
# @raycast.authorURL https://github.com/tianli

# 加载运行器
source "$(dirname "$0")/../lib/run_python.sh"

# 调用实际脚本
run_python "category/script_name.py"
```

**注意事项**：
- Wrapper 只负责元数据和调用，不包含业务逻辑
- 实际逻辑在 `scripts/` 目录下的脚本中
- 使用 `run_python` 函数调用 Python 脚本
- 使用相对路径（相对于 `scripts/` 目录）

### 项目元数据

每个 `projects/` 下的项目需要 `_project.yaml` 文件：

```yaml
name: project_name
title: 项目标题
description: 项目描述
type: streamlit  # 或 cli, pipeline
category: hydraulic  # 或 document, data, system
dependencies:
  - streamlit
  - pandas
  - numpy
```

## 维护

### 健康检查

检查所有脚本的引用路径是否有效：

```bash
python3 lib/tools/health_check.py
```

检查项：
- [ ] 所有 `source` 引用的文件存在
- [ ] 所有 `import` 引用的模块存在
- [ ] Raycast wrapper 引用的脚本存在
- [ ] 项目元数据文件存在

### 同步索引

更新脚本索引（`_index/` 目录）：

```bash
python3 lib/tools/sync_index.py
```

生成内容：
- `by-function.md`：按功能分类
- `by-platform.md`：按平台分类
- `by-type.md`：按类型分类

### 批量修改注意事项

- 批量修改脚本时，必须逐一检查每个脚本的所有外部引用（`source`/`import`），不能只搜索已知模式
- 恢复或删除文件时，必须处理所有关联文件（主文件、wrapper、raycast 引用）
- 修改完成后，运行 `python3 lib/tools/health_check.py` 验证

## 相关项目

- **OA 总控**：`~/Dev/oa-project` - 统一管理脚本和项目的 Web 应用
- **水利公司**：`~/Work/zdwp` - 水利工程项目
- **论文部**：`~/Personal/essays` - 论文写作
- **个人网站**：`~/Personal/website` - 个人网站
- **求职管理**：`~/Personal/resume` - 求职管理
- **工作报告**：`~/Work/reports` - 工作报告
- **学习笔记**：`~/Learn` - 学习笔记

## License

MIT

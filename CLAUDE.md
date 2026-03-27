# useful_scripts

macOS 个人效率工具脚本库，主要通过 Raycast 调用。

## 目录结构

```
scripts/              # 功能脚本，按类别分组
├── document/         # 文档处理（docx_ + md_ + pptx_）
├── data/             # 数据转换（xlsx_ + csv_）
├── file/             # 文件操作（file_ + folder_）
├── system/           # 系统工具（sys_ + display_）
├── network/          # 网络代理（clashx_）
├── window/           # 窗口管理（yabai_）
└── tools/            # 杂项工具（tts, gantt, quarto, app_open）

lib/                  # 统一公共库
├── core/             # 核心处理逻辑（csv_core, docx_core, xlsx_core）
├── hydraulic/        # 水利领域专用库（编码映射、QGIS 配置）
├── tools/            # 项目维护工具（health_check, sync_index）
├── asr/              # 语音识别词表数据
└── *.py / *.sh       # 公共模块（display, file_ops, finder, excel_ops 等）

projects/             # 复杂多文件项目（内部自治）
├── capacity/         # 纳污能力计算（Streamlit）
├── geocode/          # 地理编码（Streamlit）
├── reservoir_schedule/  # 水库调度（Streamlit）
├── irrigation/       # 灌溉需水（Streamlit）
├── district_scheduler/  # 区域调度（Streamlit）
├── risk_data/        # 风险分析表填充（CLI）
├── qgis/             # QGIS 空间处理（Pipeline）
├── company_query/    # 企业查询（CLI）
├── cad/              # CAD 脚本
├── rainfall/         # 降雨数据
├── water_annual/     # 年度水资源数据
└── water_efficiency/ # 用水效率（Streamlit）

templates/            # 模板文件（zdwp_template.docx 等）

raycast/              # Raycast 入口
├── commands/         # Shell wrapper 脚本（统一入口）
└── lib/              # 运行器（run_python.sh → 调用 lib/common.sh）

_index/               # 脚本索引（by-function, by-platform, by-type）
.oa/                  # Next.js Web 应用（统一管理脚本和项目）
```

## 开发约定

### 引用路径
- Shell 引用库：`source "$(dirname "$0")/../../lib/xxx.sh"`
- `scripts/xxx/` 下的 Python 脚本：`sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))`
- `projects/xxx/` 下的 Python 脚本：`sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "lib"))`
- 水利领域导入：`from hydraulic import ...`，`from hydraulic.qgis_config import ...`
- Excel 操作导入：`from excel_ops import ...`
- Core 模块导入：`from core.docx_core import ...`

### 命名规则
- 脚本保留功能前缀：`docx_`、`xlsx_`、`csv_`、`md_`、`pptx_`、`yabai_`、`clashx_`
- 文件/文件夹操作：`file_`、`folder_`
- 系统工具：`sys_`、`display_`
- 秘书系统：`sec_`（secretary）
- 水利领域：`hy_`（hydraulic）

### Raycast 脚本
- `raycast/commands/` 下是 Shell wrapper（含 @raycast 元数据）
- Wrapper 通过 `run_python.sh` 调用实际脚本：`run_python "document/docx_text_formatter.py"`
- 新增脚本时需同步创建对应的 wrapper

### 项目元数据
- `projects/` 下每个项目需有 `_project.yaml` 文件

## 注意事项

- 批量修改脚本时，必须逐一检查每个脚本的所有外部引用（source/import），不能只搜索已知模式
- 恢复或删除文件时，必须处理所有关联文件（主文件、wrapper、raycast 引用）
- 修改完成后，运行 `python3 lib/tools/health_check.py` 验证
- 公共库只有一套（`lib/`），不要在项目内创建独立的 _lib 目录

## 路径规范

**当前目录结构**（2026-03-04 清理后）：
- ✅ `scripts/{data,document,file,network,secretary,system,tools,window}/` - 功能脚本（按类别分组）
- ✅ `raycast/commands/` - Raycast 入口脚本（51 个命令）
- ❌ `execute/` - 已废弃，不再使用
- ❌ `.assets/scripts/` - 已废弃，不再使用

**跨仓库路径引用**：
- 水利公司：`~/Work/zdwp/`
- 论文部：`~/Personal/essays/`
- 个人网站：`~/Personal/website/`
- 求职管理：`~/Personal/resume/`
- 工作报告：`~/Work/reports/`
- 学习笔记：`~/Learn/`

**禁止的路径模式**：
- ❌ `execute/` 目录（已废弃）
- ❌ `.assets/` 目录（已废弃）
- ✅ `scripts/{category}/xxx`
- ✅ `raycast/commands/xxx`

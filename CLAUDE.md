# useful_scripts

macOS 个人效率工具脚本库，主要通过 Raycast 调用。

## 目录结构

```
.assets/
├── core/       # 核心处理逻辑（csv_core, docx_core, xlsx_core）
├── lib/        # 统一公共库（display, file_ops, finder, excel_ops 等）
│   └── hydraulic/  # 水利领域专用库（编码映射、QGIS 配置）
├── scripts/    # 功能脚本入口（所有可执行脚本）
├── projects/   # 复杂多文件项目（水利工具集，原 hydraulic/）
│   ├── capacity/           # 纳污能力计算（Streamlit）
│   ├── geocode/            # 地理编码（Streamlit）
│   ├── reservoir_schedule/ # 水库调度（Streamlit）
│   ├── irrigation/         # 灌溉需水（Streamlit）
│   ├── district_scheduler/ # 区域调度（Streamlit）
│   ├── risk_data/          # 风险分析表填充（CLI）
│   ├── qgis/               # QGIS 空间处理（Pipeline）
│   ├── company_query/      # 企业查询（CLI）
│   ├── cad/                # CAD 脚本
│   ├── rainfall/           # 降雨数据
│   └── water_annual/       # 年度水资源数据
└── templates/  # 模板文件（如 zdwp_template.docx）

raycast/        # Raycast 入口，按功能分目录
├── hydraulic/  # 水利工具 Raycast 入口
└── ...         # 其他功能目录（内容为指向 .assets/scripts/ 的符号链接）

_index/         # 脚本索引（by-function, by-platform, by-type）
.oa/            # Next.js Web 应用（统一管理脚本和项目）
```

## 开发约定

### 引用路径
- Shell 引用库：`source "$(dirname "$0")/../lib/xxx.sh"`
- `.assets/scripts/` 下的 Python 脚本：`sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))`
- `.assets/projects/xxx/` 下的 Python 脚本：`sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "lib"))`
- 脚本实体统一放 `.assets/scripts/`，Raycast 目录只放符号链接
- 水利领域导入：`from hydraulic import ...`，`from hydraulic.qgis_config import ...`
- Excel 操作导入：`from excel_ops import ...`

### 命名规则
- 脚本以功能类型为前缀：`docx_`、`xlsx_`、`csv_`、`md_`、`pptx_`、`yabai_`、`clashx_`
- 文件/文件夹操作：`file_`、`folder_`
- 系统工具：`sys_`、`display_`
- 水利 Raycast 脚本：`hy_`

### Raycast 脚本
- `raycast/` 下按功能分子目录（docx, xlsx, csv, md, pptx, yabai, clashx, hydraulic 等）
- 每个子目录中的脚本是指向 `.assets/scripts/` 的符号链接
- `raycast/hydraulic/` 下是 Shell 包装脚本（启动 Streamlit 应用）
- 新增脚本时需同步创建对应的符号链接

### 项目元数据
- `.assets/projects/` 下每个项目需有 `_project.yaml` 文件
- `.oa/scripts/sync-scripts.py` 会扫描 scripts 和 projects 生成索引

## 注意事项

- 批量修改脚本时，必须逐一检查每个脚本的所有外部引用（source/import），不能只搜索已知模式
- 恢复或删除文件时，必须处理所有关联文件（主文件、符号链接、raycast 引用）
- 修改完成后，验证所有引用路径是否有效
- 公共库只有一套（`.assets/lib/`），不要在项目内创建独立的 _lib 目录

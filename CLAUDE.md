# useful_scripts

macOS 个人效率工具脚本库，主要通过 Raycast 调用。

## 目录结构

```
.assets/
├── core/       # 核心处理逻辑（csv_core, docx_core, xlsx_core）
├── lib/        # 通用工具库（common.py, common.sh, file_utils.py 等）
├── scripts/    # 功能脚本入口（所有可执行脚本）
└── templates/  # 模板文件（如 zdwp_template.docx）

raycast/        # Raycast 入口，按功能分目录，内容为指向 .assets/scripts/ 的符号链接
_index/         # 脚本索引（by-function, by-platform, by-type）
.oa/            # Next.js Web 应用（独立子项目）
```

## 开发约定

### 引用路径
- Shell 引用库：`source "$(dirname "$0")/../lib/xxx.sh"`
- Python 引用库：`sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))`
- 脚本实体统一放 `.assets/scripts/`，Raycast 目录只放符号链接

### 命名规则
- 脚本以功能类型为前缀：`docx_`、`xlsx_`、`csv_`、`md_`、`pptx_`、`yabai_`、`clashx_`
- 文件/文件夹操作：`file_`、`folder_`
- 系统工具：`sys_`、`display_`

### Raycast 脚本
- `raycast/` 下按功能分子目录（docx, xlsx, csv, md, pptx, yabai, clashx 等）
- 每个子目录中的脚本是指向 `.assets/scripts/` 的符号链接
- 新增脚本时需同步创建对应的符号链接

## 注意事项

- 批量修改脚本时，必须逐一检查每个脚本的所有外部引用（source/import），不能只搜索已知模式
- 恢复或删除文件时，必须处理所有关联文件（主文件、符号链接、raycast 引用）
- 修改完成后，验证所有引用路径是否有效

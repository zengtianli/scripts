# useful_scripts 重构执行计划

## Context

useful_scripts 项目的 lib/ 层存在严重的代码重复：`common_utils.py`（362行）是一个上帝文件，把 `display.py`、`finder.py`、`clipboard.py`、`progress.py`、`file_utils.py`、`constants.py` 的代码全部复制了一遍。此外有 113 个断裂软链接、大量硬编码路径。本次重构目标：消除重复、自动化索引、环境解耦。

## Phase 1: 清理 lib/ 重复代码

### Step 1.1: 新建 `env.py` 替代 `constants.py`
- **文件**: `.assets/lib/env.py`（新建）
- 动态检测 `PROJECT_ROOT`、`PYTHON_PATH`、`USAGE_LOG`，不再硬编码

### Step 1.2: 重写 `__init__.py` 为统一导出入口
- **文件**: `.assets/lib/__init__.py`
- 从 `display`, `finder`, `clipboard`, `progress`, `usage_log`, `file_ops`, `env` 统一 re-export
- 同时提供 `common_utils` 兼容别名（过渡期）

### Step 1.3: 重构 `file_utils.py` → `file_ops.py`
- **文件**: `.assets/lib/file_utils.py` → 重命名为 `.assets/lib/file_ops.py`
- 移除 `launch_app`、`get_running_apps`、`launch_essential_apps`（应用启动逻辑，移入 `sys_app_launcher.py`）
- 移除 `get_clipboard_files`、`paste_files`（剪贴板文件操作，移入 `clipboard.py`）
- 保留：文件校验、批量操作、目录操作

### Step 1.4: 扩充 `clipboard.py`
- 把 `file_utils.py` 中的 `get_clipboard_files()` 和 `paste_files()` 移入

### Step 1.5: 删除重复文件
- 删除 `common_utils.py`（362行，全部重复）
- 删除 `constants.py`（19行，被 env.py 替代）
- 删除 `common.py`（32行，被 __init__.py 替代）

### Step 1.6: 迁移 18 个脚本的 import
需要修改的脚本（使用 `from common_utils import ...`）：
- `xlsx_to_txt.py`, `xlsx_from_txt.py`, `csv_merge_txt.py`, `csv_to_txt.py`
- `md_split_by_heading.py`, `xlsx_from_csv.py`, `xlsx_to_csv.py`, `csv_from_txt.py`
- `xlsx_splitsheets.py`, `md_merge.py`, `pptx_to_md.py`, `pptx_apply_all.py`
- `pptx_text_formatter.py`, `pptx_table_style.py`, `docx_zdwp_all.py`
- `pptx_font_yahei.py`, `docx_apply_image_caption.py`, `md_formatter.py`

还有：
- `xlsx_lowercase.py`：`from finder import ...` → `from lib.finder import ...`
- `yabai_org.py`：`from common import ...` → `from lib import ...`

修改方式：`from common_utils import X, Y` → `from display import X` + `from finder import Y`（直接从子模块导入，因为 sys.path 已指向 lib/）

### Step 1.7: 统一 shebang
所有 `#!/Users/tianli/miniforge3/bin/python3` → `#!/usr/bin/env python3`

### Step 1.8: 修复 `common.sh` 硬编码
- `PYTHON_PATH` 改为动态检测
- 移除指向不存在目录的常量

## Phase 2: 清理断裂软链接

### Step 2.1: 删除所有 113 个断裂软链接
涉及目录：
- `raycast/` 下的断裂链接
- `_index/` 下的断裂链接
- `.claude/skills/` 下的断裂链接

### Step 2.2: 新建 `.assets/tools/sync_index.py`
自动扫描 `.assets/scripts/` 生成：
- `raycast/` 软链接（按 @raycast.packageName 分类）
- `_index/by-type/` 软链接（按文件名前缀分类）
- `.claude/skills/` 软链接

### Step 2.3: 新建 `.assets/tools/health_check.py`
检查：断裂链接、缺失依赖、无效路径、import 引用

## Phase 3: 验证

- 逐个执行所有 Python 脚本的 `python3 script.py --help` 或 dry-run 确认 import 不报错
- 运行 `health_check.py` 确认零问题
- 运行 `sync_index.py` 确认索引完整

## 关键文件清单

| 操作 | 文件 |
|------|------|
| 新建 | `.assets/lib/env.py` |
| 新建 | `.assets/tools/sync_index.py` |
| 新建 | `.assets/tools/health_check.py` |
| 重写 | `.assets/lib/__init__.py` |
| 重命名+重构 | `.assets/lib/file_utils.py` → `.assets/lib/file_ops.py` |
| 扩充 | `.assets/lib/clipboard.py` |
| 修改 | `.assets/lib/common.sh` |
| 删除 | `.assets/lib/common_utils.py`, `.assets/lib/constants.py`, `.assets/lib/common.py` |
| 修改 import | 18+ 个 `.assets/scripts/*.py` |
| 修改 shebang | ~30 个 `.py` 文件 |
| 删除 | 113 个断裂软链接 |

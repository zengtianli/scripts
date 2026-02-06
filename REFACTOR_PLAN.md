# useful_scripts 重构方案

## 一、现状诊断

### 1.1 数据概览

| 指标 | 数值 |
|------|------|
| 总文件数 | 183 |
| 库代码 (lib/) | 13 文件, 1,660 行 |
| 核心逻辑 (core/) | 5 文件, ~850 行 |
| 业务脚本 (scripts/) | 46 文件, 7,521 行 |
| **断裂软链接** | **113 个** |
| 代码总量 | ~10,000 行 |

### 1.2 核心问题

#### P0: 大面积代码重复 — 库文件之间互相抄

这是最严重的问题。当前 lib/ 下存在**三层重复**：

```
common_utils.py (362行)  ← 巨型上帝文件，包含一切
├── 重复了 display.py 的全部 7 个函数（逐行一致）
├── 重复了 finder.py 的全部 5 个函数（逐行一致）
├── 重复了 clipboard.py 的全部 2 个函数（逐行一致）
├── 重复了 progress.py 的 ProgressTracker 类（逐行一致）
├── 重复了 file_utils.py 的 6 个函数（逐行一致）
├── 重复了 constants.py 的全部常量（逐行一致）
└── 重复了 usage_log.py 的 log_usage 逻辑
```

**结论**：`common_utils.py` 是一个 362 行的"上帝文件"，它把其他 7 个模块的代码全部复制了一遍。而那 7 个小模块也同时存在。这意味着 lib/ 下 **50% 以上的代码是重复的**。

#### P1: 113 个断裂软链接

`_index/`、`raycast/`、`.claude/skills/` 三个目录下大量软链接指向已删除的脚本。这些链接：
- 让 Raycast 显示无法执行的命令
- 让 `_index/` 索引完全失去意义
- 让 `.claude/skills/` 的引用全部失效

#### P2: 硬编码路径

```python
# 出现在 common_utils.py、constants.py、所有脚本的 shebang 中
PYTHON_PATH = "/Users/tianli/miniforge3/bin/python3"
EXECUTE_DIR = "/Users/tianli/useful_scripts/execute"  # 这个目录已经不存在了
```

换机器、换 Python 版本、换用户名 → 全部失效。

#### P3: lib/ 和 core/ 职责边界模糊

- `file_utils.py` 里有 `launch_app()`、`get_clipboard_files()` — 这不是"文件工具"
- `core/docx_core.py` 做文本格式化 — 这是 lib 级别的通用逻辑
- `common.py` 只是一个 re-export 文件，增加了一层无意义的间接

#### P4: 索引系统维护成本极高

`_index/` 提供了 by-function / by-platform / by-type 三种视图，全部靠手动维护软链接。每次增删脚本都要同步更新 3 个索引目录 + raycast/ + .claude/skills/。实际上已经完全失控（113 个断裂链接就是证据）。

---

## 二、重构目标

1. **更少的代码**：消除所有重复，库代码从 1,660 行降到 ~600 行
2. **更强的复用**：抽象出真正有用的公共模式，脚本只写业务逻辑
3. **零维护索引**：用脚本自动生成索引，不再手动维护软链接
4. **环境无关**：消除所有硬编码路径，支持任意机器部署
5. **自愈能力**：添加健康检查，自动发现断裂链接和缺失依赖

---

## 三、目标架构

### 3.1 目录结构

```
useful_scripts/
├── .assets/
│   ├── lib/                    # 公共库（唯一真相源）
│   │   ├── __init__.py         # 统一导出
│   │   ├── display.py          # UI 输出（保留，~30行）
│   │   ├── finder.py           # Finder 交互（保留，~170行）
│   │   ├── clipboard.py        # 剪贴板（保留，~20行）
│   │   ├── progress.py         # 进度跟踪（保留，~60行）
│   │   ├── usage_log.py        # 使用统计（保留，~35行）
│   │   ├── file_ops.py         # 文件操作（重构自 file_utils.py，去掉不相关的）
│   │   ├── env.py              # 环境配置（新增，替代 constants.py + 硬编码）
│   │   ├── docx_utils.py       # docx XML 操作（保留）
│   │   └── clashx.sh           # ClashX 库（保留）
│   │
│   ├── core/                   # 领域核心逻辑（保留）
│   │   ├── docx_core.py
│   │   ├── xlsx_core.py
│   │   ├── csv_core.py
│   │   └── create_zdwp_template.py
│   │
│   ├── scripts/                # 业务脚本（保留）
│   │   └── ...
│   │
│   └── tools/                  # 维护工具（新增）
│       ├── sync_index.py       # 自动同步所有索引软链接
│       ├── health_check.py     # 健康检查（断链、缺失依赖、路径有效性）
│       └── cleanup.py          # 清理断裂链接和空目录
│
├── raycast/                    # Raycast 入口（自动生成）
├── _index/                     # 多维索引（自动生成）
└── .claude/skills/             # Claude skills（软链接自动同步）
```

### 3.2 关键变化

| 变化 | 之前 | 之后 |
|------|------|------|
| 库文件数 | 13 个（大量重复） | 10 个（零重复） |
| 库代码量 | 1,660 行 | ~600 行 |
| `common_utils.py` | 362 行上帝文件 | **删除**，由 `__init__.py` 统一导出 |
| `constants.py` | 硬编码路径 | **删除**，由 `env.py` 动态检测 |
| `common.py` | 无意义 re-export | **删除**，合并到 `__init__.py` |
| 索引维护 | 手动 | `sync_index.py` 自动生成 |
| 环境依赖 | 硬编码 `/Users/tianli/...` | 动态检测 `which python3` |

---

## 四、详细设计

### 4.1 消除上帝文件 `common_utils.py`

**原则**：每个模块只定义一次，`__init__.py` 负责统一导出。

新的 `lib/__init__.py`：
```python
"""
useful_scripts 公共库
统一导出接口，脚本只需: from lib import show_success, get_input_files, ...
"""

from .display import show_success, show_error, show_warning, show_info, show_processing, show_progress
from .finder import get_finder_selection, get_finder_current_dir, get_input_files, require_single_file
from .clipboard import copy_to_clipboard, get_from_clipboard
from .progress import ProgressTracker
from .usage_log import log_usage
from .file_ops import validate_input_file, find_files_by_extension, ensure_directory, check_command_exists, fatal_error
from .env import PYTHON_PATH, PROJECT_ROOT, USAGE_LOG
```

脚本引用方式不变：
```python
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))
from lib import show_success, get_input_files, ProgressTracker
```

**删除的文件**：
- `common_utils.py` (362行) — 全部重复代码
- `constants.py` (19行) — 被 `env.py` 替代
- `common.py` (32行) — 被 `__init__.py` 替代

**净减少**：~413 行

### 4.2 新增 `env.py` — 环境自动检测

```python
"""环境配置 — 零硬编码"""
import os
import shutil
from pathlib import Path

# 项目根目录：从当前文件位置自动推导
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LIB_DIR = PROJECT_ROOT / ".assets" / "lib"
SCRIPTS_DIR = PROJECT_ROOT / ".assets" / "scripts"
CORE_DIR = PROJECT_ROOT / ".assets" / "core"

# Python 路径：动态检测
PYTHON_PATH = shutil.which("python3") or "/usr/bin/python3"

# 日志
USAGE_LOG = Path.home() / ".useful_scripts_usage.log"
```

### 4.3 重构 `file_utils.py` → `file_ops.py`

当前 `file_utils.py` (342行) 混杂了四类不相关的功能：

| 功能 | 行数 | 归属 |
|------|------|------|
| 文件校验 (validate, check_ext) | ~50行 | 保留在 `file_ops.py` |
| 应用启动 (launch_app, get_running_apps) | ~60行 | 移到 `sys_app_launcher.py` 脚本内部 |
| 剪贴板文件 (get_clipboard_files, paste_files) | ~50行 | 移到 `clipboard.py` |
| 批量文件操作 (add_prefix, move_up, flatten) | ~100行 | 保留在 `file_ops.py` |
| 文件分类 (organize_by_type) | ~40行 | 保留在 `file_ops.py` |

重构后 `file_ops.py` 只保留纯文件操作，~190 行。

### 4.4 自动索引系统

新增 `.assets/tools/sync_index.py`，核心逻辑：

```python
"""
读取 .assets/scripts/ 下所有脚本的 Raycast 元数据，
自动生成 raycast/、_index/ 下的软链接。

运行方式: python3 .assets/tools/sync_index.py
触发时机: 每次增删脚本后执行一次
"""
```

功能：
1. 扫描 `.assets/scripts/` 下所有脚本
2. 解析 `@raycast.packageName` 等元数据，确定分类
3. 自动创建/更新 `raycast/` 下的软链接
4. 自动创建/更新 `_index/by-type/`、`by-function/`、`by-platform/` 下的软链接
5. 自动清理断裂链接
6. 自动同步 `.claude/skills/` 下的引用

### 4.5 健康检查系统

新增 `.assets/tools/health_check.py`：

```
$ python3 .assets/tools/health_check.py

=== useful_scripts 健康检查 ===

[检查软链接]
  ✅ raycast/: 46 个链接全部有效
  ❌ _index/: 发现 3 个断裂链接
     - _index/by-type/docx/docx_apply_footer.py -> 目标不存在

[检查依赖]
  ✅ python-docx: 已安装
  ✅ pandas: 已安装
  ❌ markitdown: 未安装

[检查路径]
  ✅ 所有 shebang 路径有效
  ❌ common.sh 第 15 行: /Users/tianli/useful_scripts/execute 不存在

[检查引用]
  ✅ 所有 source/import 引用目标存在
```

---

## 五、脚本层面的复用优化

### 5.1 当前脚本中的重复模式

分析 46 个脚本，发现以下高频重复模式：

#### 模式 A: Raycast 脚本启动模板（出现 46 次）

每个 Python 脚本都有这段几乎一样的启动代码：

```python
#!/Users/tianli/miniforge3/bin/python3
# @raycast.schemaVersion 1
# @raycast.title xxx
# @raycast.mode fullOutput
# ...

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

from common_utils import show_success, show_error, get_input_files, ProgressTracker, log_usage

def main():
    log_usage("script_name")
    files = get_input_files(sys.argv[1:], expected_ext="docx")
    if not files:
        return
    # ... 业务逻辑

if __name__ == "__main__":
    main()
```

**优化**：在 `__init__.py` 中提供 `run_script` 装饰器：

```python
# lib/__init__.py
def run_script(name, expected_ext=None, allow_multiple=True):
    """脚本启动装饰器，自动处理日志、文件获取、异常捕获"""
    def decorator(func):
        def wrapper():
            log_usage(name)
            files = get_input_files(sys.argv[1:], expected_ext, allow_multiple)
            if not files:
                return
            try:
                func(files)
            except Exception as e:
                show_error(f"执行失败: {e}")
        return wrapper
    return decorator
```

脚本简化为：

```python
from lib import run_script, show_success

@run_script("docx_text_formatter", expected_ext="docx")
def main(files):
    for f in files:
        # 纯业务逻辑，不再写样板代码
        process(f)
        show_success(f"已处理: {f}")

main()
```

**预计减少**：每个脚本减少 ~15 行样板代码，46 个脚本共减少 ~690 行。

#### 模式 B: xlsx 转换脚本的重复结构（出现 6 次）

`xlsx_to_csv.py`、`xlsx_to_txt.py`、`xlsx_from_csv.py`、`xlsx_from_txt.py`、`csv_to_txt.py`、`csv_from_txt.py` 这 6 个脚本结构几乎一致：

```python
# 读取文件 → 用 pandas 转换格式 → 写入新文件
```

**优化**：在 `core/` 中提供通用转换函数：

```python
# core/table_convert.py
def convert_table(input_path, output_ext, **kwargs):
    """通用表格格式转换"""
    # 根据输入/输出扩展名自动选择读写方法
```

6 个脚本可以合并为 1 个 `table_convert.py`，通过参数区分行为。

#### 模式 C: pptx 系列的重复逻辑（出现 4 次）

`pptx_font_yahei.py`、`pptx_text_formatter.py`、`pptx_table_style.py`、`pptx_apply_all.py` 都有相同的"遍历所有 slide → 遍历所有 shape → 处理文本"的骨架。

**优化**：抽象出 `core/pptx_core.py`：

```python
def walk_pptx_text(pptx_path, handler_fn):
    """遍历 pptx 中所有文本 run，对每个 run 调用 handler_fn"""
```

### 5.2 预期效果

| 指标 | 重构前 | 重构后 | 减少 |
|------|--------|--------|------|
| lib/ 代码量 | 1,660 行 | ~600 行 | -64% |
| scripts/ 代码量 | 7,521 行 | ~5,500 行 | -27% |
| 总代码量 | ~10,000 行 | ~7,000 行 | -30% |
| 断裂软链接 | 113 个 | 0 个 | -100% |
| 重复函数定义 | ~40 个 | 0 个 | -100% |

---

## 六、执行计划

### Phase 1: 清理（不改变任何行为）

1. 删除 `common_utils.py`、`constants.py`、`common.py`
2. 新增 `env.py`，替代硬编码常量
3. 更新 `__init__.py` 为统一导出入口
4. 更新所有脚本的 import 语句（`from common_utils import ...` → `from lib import ...`）
5. 清理 `file_utils.py` → `file_ops.py`，把不相关的函数移到对应模块
6. 清理所有 113 个断裂软链接
7. 验证：所有脚本可正常执行

### Phase 2: 自动化（降低维护成本）

1. 实现 `sync_index.py`
2. 实现 `health_check.py`
3. 用 `sync_index.py` 重建所有索引
4. 添加 git pre-commit hook 自动运行健康检查

### Phase 3: 抽象（提升复用）

1. 实现 `run_script` 装饰器，简化脚本样板代码
2. 抽象 `core/pptx_core.py`，统一 pptx 遍历逻辑
3. 合并 6 个表格转换脚本为 `table_convert.py` + 6 个薄包装
4. 将 `docx_core.py` 中的文本格式化逻辑提升为通用 `text_format.py`

### Phase 4: 加固

1. 替换所有 shebang 中的硬编码路径为 `#!/usr/bin/env python3`
2. 添加 `requirements.txt`
3. `common.sh` 中的硬编码路径改为动态检测

---

## 七、风险与注意事项

1. **Raycast 兼容性**：Raycast 要求脚本头部有特定的 shebang 和元数据注释，修改 shebang 后需验证 Raycast 能否正常识别
2. **import 路径变更**：Phase 1 修改 import 后，必须逐个脚本验证，不能遗漏
3. **合并脚本的 Raycast 入口**：合并 6 个转换脚本后，仍需保留 6 个 Raycast 入口文件（薄包装），否则 Raycast 命令会消失
4. **向后兼容**：如果有外部系统直接调用 `from common_utils import ...`，需要在过渡期保留一个 `common_utils.py` 做 re-export（但应标记为 deprecated）

---

## 八、验收标准

- [ ] `python3 .assets/tools/health_check.py` 全部通过
- [ ] 0 个断裂软链接
- [ ] lib/ 下无重复函数定义
- [ ] 无硬编码的绝对路径（`/Users/tianli/` 出现次数 = 0，shebang 除外）
- [ ] 每个 Raycast 脚本可正常执行
- [ ] `sync_index.py` 可一键重建所有索引
- [ ] 总代码量减少 25% 以上

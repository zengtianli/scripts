---
name: script-manager
description: 脚本管理工具。当需要"创建新脚本"、"重构脚本"、"同步到 Raycast"时触发。
---

# Script Manager

> 路径：`~/useful_scripts/.claude/skills/script-manager/`
> 定位：useful_scripts 脚本库的创建、管理和维护工具

## 触发条件

- 用户说"创建新脚本"、"添加脚本"
- 用户说"重构脚本"、"规范化脚本"
- 用户说"同步到 Raycast"、"创建 Raycast wrapper"
- 用户说"验证脚本元数据"

## 核心功能

### 1. 脚本创建流程

**交互式创建**：
```bash
./scripts/create-script.sh
```

**流程**：
1. 选择脚本类别：
   - `document` - 文档处理（docx_, md_, pptx_）
   - `data` - 数据转换（xlsx_, csv_）
   - `file` - 文件操作（file_, folder_）
   - `system` - 系统工具（sys_, display_）
   - `network` - 网络代理（clashx_）
   - `window` - 窗口管理（yabai_）
   - `tools` - 杂项工具

2. 输入脚本名称（自动添加前缀）

3. 选择语言：
   - Python（推荐，功能丰富）
   - Shell（简单快速）

4. 自动生成：
   - 功能脚本：`scripts/{category}/{prefix}_{name}.{py|sh}`
   - Raycast wrapper：`raycast/commands/{prefix}-{name}.sh`

5. 运行验证：
   - 检查文件权限
   - 验证元数据完整性
   - 运行 health_check

### 2. 命名规范

**前缀规则**（基于 CLAUDE.md）：

| 类别 | 前缀 | 示例 |
|------|------|------|
| document | `docx_`, `md_`, `pptx_` | `docx_text_formatter.py` |
| data | `xlsx_`, `csv_` | `xlsx_to_csv.py` |
| file | `file_`, `folder_` | `file_rename_batch.py` |
| system | `sys_`, `display_` | `sys_cleanup.sh` |
| network | `clashx_` | `clashx_enhanced.sh` |
| window | `yabai_` | `yabai_focus_next.sh` |
| tools | 无固定前缀 | `tts_volcano.py`, `gantt_timeline.py` |

**命名格式**：
- 功能脚本：`{prefix}_{功能描述}.{py|sh}`
- Raycast wrapper：`{prefix}-{功能描述}.sh`（连字符）

### 3. 元数据规范

**Raycast wrapper 必需元数据**：
```bash
#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title {显示名称}
# @raycast.description {功能描述}
# @raycast.mode {silent|compact|fullOutput}
# @raycast.icon {emoji}
# @raycast.packageName {分类名称}
```

**可选元数据**：
```bash
# @raycast.argument1 { "type": "text", "placeholder": "提示文本" }
# @raycast.argument1 { "type": "dropdown", "placeholder": "选择", "data": [...] }
```

### 4. 脚本模板

**Python 脚本模板**（`references/script-template.py`）：
- 标准 shebang：`#!/usr/bin/env python3`
- sys.path 设置（引用 lib/）
- Finder 选择获取示例
- 错误处理和日志记录
- 详细注释

**Shell 脚本模板**（`references/script-template.sh`）：
- 标准 shebang：`#!/bin/bash`
- source common.sh
- 参数解析示例
- 错误处理

**Raycast wrapper 模板**（`references/raycast-wrapper-template.sh`）：
- 完整元数据
- 调用 run_python.sh 或 run_shell.sh

## 工具脚本

### create-script.sh
交互式创建新脚本，自动生成 wrapper。

**使用**：
```bash
cd ~/useful_scripts/.claude/skills/script-manager
./scripts/create-script.sh
```

### sync-to-raycast.sh
检查 scripts/ 下的脚本，自动创建缺失的 Raycast wrapper。

**使用**：
```bash
./scripts/sync-to-raycast.sh
```

### validate-metadata.py
验证所有 Raycast wrapper 的元数据完整性。

**使用**：
```bash
python3 ./scripts/validate-metadata.py
```

## 路径规范

**功能脚本位置**：
- ✅ `~/useful_scripts/scripts/{category}/{script}.py`
- ❌ `~/useful_scripts/execute/` - 已废弃
- ❌ `~/useful_scripts/.assets/scripts/` - 已废弃

**Raycast wrapper 位置**：
- ✅ `~/useful_scripts/raycast/commands/{script}.sh`

**公共库位置**：
- ✅ `~/useful_scripts/lib/` - 唯一公共库
- ❌ 项目内不要创建独立的 _lib 目录

## 引用路径规范

**Shell 脚本引用库**：
```bash
source "$(dirname "$0")/../../lib/common.sh"
```

**Python 脚本引用库**（scripts/ 下）：
```python
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))
```

**Python 脚本引用库**（projects/ 下）：
```python
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "lib"))
```

## 验证流程

创建或修改脚本后，必须运行：

```bash
# 1. 验证元数据
python3 .claude/skills/script-manager/scripts/validate-metadata.py

# 2. 运行健康检查
python3 lib/tools/health_check.py

# 3. 测试脚本执行
# 直接运行功能脚本或通过 Raycast 调用
```

## 修改规范

- 新增脚本类别需更新 CLAUDE.md 和本文档
- 模板修改需同步更新 references/ 下的模板文件
- 工具脚本修改需保持向后兼容
- 批量修改时必须逐一检查所有外部引用

## 注意事项

1. **完整性**：创建脚本时必须同时创建 wrapper
2. **权限**：脚本文件必须有执行权限（chmod +x）
3. **验证**：修改后必须运行 health_check
4. **关联**：删除或恢复文件时必须处理所有关联文件

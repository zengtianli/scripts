---
name: dev-memory
description: 开发部项目记忆与架构决策。命名规范、安全规范、历史决策。当需要了解项目约定时触发。
---

# 项目记忆

> 📍 位置：开发部 useful_scripts

## 项目元信息

| 属性 | 值 |
|-----|-----|
| **项目名称** | 实用脚本工具集 (Useful Scripts) |
| **项目类型** | 脚本库（基础设施） |
| **主项目路径** | `/Users/tianli/useful_scripts/` |
| **执行库路径** | `/Users/tianli/useful_scripts/execute/` |
| **Python** | `/Users/tianli/miniforge3/bin/python3` |
| **Git 控制** | 由主项目 useful_scripts 统一管理 |

## 架构决策

### 2025-12-15: 统一 Git 管理

- **决策**：execute 子目录不独立 git，由 useful_scripts 主项目统一管理
- **原因**：简化版本控制，避免嵌套 git 仓库的复杂性

### 2025-12-16: 脚本命名规范

- **决策**：所有 Shell 脚本必须带 `.sh` 或 `.zsh` 后缀
- **原因**：方便定位脚本文件，避免与系统命令冲突

### 2025-01-19: 水利工具独立

- **决策**：hydraulic 从 tools/ 提升为 execute/ 下的一级目录
- **原因**：水利工具体量大（1000+文件），独立后结构更清晰
- **新路径**：`execute/hydraulic/`

## 目录结构约定

### execute/ 内部结构

```
execute/
├── raycast/         ← Raycast 脚本（扁平化，直接放 .py/.sh）
│   ├── _lib/        公共库（可 import 的模块）
│   └── _core/       核心模块
├── tools/           ← 通用工具
│   ├── read/        读取工具
│   ├── analyze/     分析工具
│   ├── transform/   转换工具
│   └── system/      系统工具
├── hydraulic/       ← 水利专用（独立目录）
├── compare/         ← 比较工具
├── agents/          ← Agent 配置文档
├── docs/            ← 文档说明
└── archived/        ← 归档文件
```

### 命名规范

| 类型 | 命名规则 | 示例 |
|------|---------|------|
| Python 工具 | `功能_对象.py` | `read_docx.py` |
| Shell 脚本 | `功能_说明.sh` | `merge_files.sh` |
| Raycast 脚本 | `类型_动作.py` | `docx_apply_header.py` |

**重要规范**：
- 所有 Shell 脚本必须带 `.sh` 或 `.zsh` 后缀
- 禁止使用无后缀的脚本文件名
- 冗余/过时脚本放 archived/

## 安全规范

### Excel/数据文件修改前必须备份

**强制要求**：任何脚本在**覆盖写入**数据文件前，必须先自动备份原文件

```python
import shutil
from datetime import datetime
from pathlib import Path

def backup_file(file_path):
    """修改前自动备份"""
    if Path(file_path).exists():
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{file_path}.{timestamp}.bak"
        shutil.copy2(file_path, backup_path)
        print(f"📦 已备份: {backup_path}")
        return backup_path
    return None
```

## 开发新脚本流程

1. **先查** - 搜索 execute/ 是否已有类似功能
2. **定位** - 确定放 tools/、raycast/ 还是 hydraulic/
3. **命名** - 遵循命名规范
4. **文档** - 添加 --help 说明

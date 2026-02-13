# 项目结构重构 - 修复不一致并提交

## 背景

项目从旧的 `execute/` 结构迁移到 `.assets/` 体系，大量工作已完成但存在 4 处不一致，且全部变更未提交。

## 修复步骤

### 1. 修复 `.claude/skills/structure/SKILL.md`

SKILL.md 仍引用根目录 `hydraulic/`，但实际水利项目在 `.assets/projects/` 下。

修改内容：
- 核心目录结构：`hydraulic/` → `.assets/projects/`（水利项目目录）
- 补充 `.assets/lib/hydraulic/` 说明
- 水利工具规范：`hydraulic/` → `.assets/projects/`
- `_lib/` → `.assets/lib/hydraulic/`
- 位置决策树 Q1：`hydraulic/` → `.assets/projects/`
- 新建水利工具流程：引用路径更新
- 子目录需包含 `_project.yaml`（而非只有 README.md）

### 2. 修复 `.assets/tools/health_check.py`

第 20 行 `HYDRAULIC_DIR = PROJECT_ROOT / "hydraulic"` 指向不存在的目录。

修改内容：
- `HYDRAULIC_DIR` → `PROJECTS_DIR = PROJECT_ROOT / ".assets" / "projects"`
- 三个 hydraulic 检查方法中的路径引用和日志前缀同步更新
- LIB_MODULES 集合新增 `excel_ops`

### 3. 添加 `.oa/.next/` 到 `.gitignore`

当前 `.gitignore` 只有 `.DS_Store`，需要添加：
- `.oa/.next/`
- `__pycache__/`
- `*.pyc`

### 4. 删除 `SETUP_COMPLETE.md`

该文件引用大量旧路径（`tools/hydraulic/`），且本身是一次性安装报告，不需要保留在仓库中。直接删除。

### 5. 提交所有变更

分两次提交：
1. **修复提交**：上述 4 个修复
2. **主提交**：所有重构变更（lib 新增、projects 迁移、.oa 更新、CLAUDE.md、requirements.txt 等）

或合并为一次提交（因为修复和主变更属于同一次重构）。

## 涉及文件

| 操作 | 文件 |
|------|------|
| 编辑 | `.claude/skills/structure/SKILL.md` |
| 编辑 | `.assets/tools/health_check.py` |
| 编辑 | `.gitignore` |
| 删除 | `.assets/projects/SETUP_COMPLETE.md` |
| 提交 | 所有已修改 + 新增文件（排除 .oa/.next/） |

## 验证

- 运行 `python3 .assets/tools/health_check.py` 确认无错误
- `git status` 确认干净

# Hydraulic 模块重构方案 (方案 A: 轻度融入)

## Context

useful_scripts 主项目刚完成重构（消除重复代码、清理断裂链接、统一 shebang、自动化工具），但 `hydraulic/` 模块完全未被覆盖。当前 hydraulic 存在：硬编码路径 58 处（43 个文件）、11 个断裂符号链接、shebang 不规范（30 个文件）、setup.sh 指向不存在的目录、与主项目工具链完全隔离。本次重构目标是按照主项目同等标准加固 hydraulic，并在入口层做轻度集成。

---

## Phase 1: 加固（不改变行为）

### 1.1 统一 shebang（30 个文件）

将 `#!/Users/tianli/miniforge3/bin/python3` 改为 `#!/usr/bin/env python3`。

涉及文件：
- `risk_data/` 下 16 个：`1.1_*.py` ~ `3.09_*.py`、`check_excel_headers.py`、`quick_check.py`
- `qgis/pipeline/` 下：`01`、`02`、`05`、`06`、`08` 等有 shebang 的文件
- `qgis/tools/` 下：`check_config.py`、`check_mask_config.py`、`create_mask_layers.py`、`extract_points_in_polygons.py`、`export_map_layout.py`
- `qgis/_util/` 下：`qgis_util.py`、`qgis_listener.py`、`test_listener.py`、`test_qgis_util.py`

### 1.2 修复 setup.sh

- `HYDRAULIC_HOME` 改为 `$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)` 动态推导
- `HYDRAULIC_DATA_BASE` 改为 `${HYDRAULIC_DATA_BASE:-$HOME/Downloads/zdwp/...}` 环境变量 fallback
- 注释中的路径同步更新

### 1.3 修复 qgis/scripts/ 下 4 个 Shell 脚本的硬编码路径

- `run_pipeline.sh`、`run_script.sh`、`run.sh`、`run_11.sh` 等
- `SCRIPT_DIR` 改为基于 `BASH_SOURCE` 推导
- `DEFAULT_PROJECT` 改为环境变量 fallback

### 1.4 修复 QGIS Python 脚本中的 `_setup_paths()` 硬编码（~22 个文件）

- `qgis/pipeline/` 和 `qgis/tools/` 下所有包含 `_setup_paths()` 的文件
- 将 `known_paths` 中的硬编码路径改为基于 `__file__` 推导，保留 QGIS exec() 模式的 fallback
- fallback 路径更新为 `~/useful_scripts/hydraulic/qgis`

### 1.5 修复其他 Python 文件中的硬编码路径

- `qgis/_util/qgis_listener.py`：3 处硬编码
- `qgis/pipeline/99_batch_export_layers.py`：2 处硬编码输出目录
- `qgis/tools/check_config.py`、`check_mask_config.py`：各 3 处

### 1.6 清理 11 个断裂符号链接

- `water_annual/data/raw/` 下 6 个 xlsx 链接（指向不存在的 `原始年报/`）
- `risk_data/` 下 3 个数据链接（指向不存在的 Downloads 路径）
- `district_scheduler/hqdd/.cursor/rules/` 下 2 个 mdc 链接

### 1.7 验证

```bash
# 断裂链接 = 0
find hydraulic/ -type l ! -exec test -e {} \; -print
# 旧 shebang = 0
grep -rn '#!/Users/tianli/miniforge3' hydraulic/
# 旧 execute 路径 = 0
grep -rn '/Users/tianli/useful_scripts/execute' hydraulic/
# Python 语法检查
find hydraulic/ -name "*.py" -exec python3 -c "import ast; ast.parse(open('{}').read())" \;
```

---

## Phase 2: 融入主项目

### 2.1 扩展 health_check.py

**文件**: `.assets/tools/health_check.py`

新增 3 个检查方法：
- `check_hydraulic_shebangs()`：检查 hydraulic/ 下 Python shebang 规范
- `check_hydraulic_hardcoded_paths()`：检查硬编码路径（miniforge3、execute、Downloads/zdwp）
- `check_hydraulic_imports()`：检查 risk_data/ 和 qgis/ 脚本的 import 引用有效性

在 `run()` 中注册这 3 个新检查。

### 2.2 更新 structure skill

**文件**: `.claude/skills/structure/SKILL.md`

- `execute/hydraulic/` → `hydraulic/`
- `execute/raycast/` → `.assets/scripts/`（实体）+ `raycast/`（链接）
- `execute/raycast/_lib/` → `.assets/lib/`
- `execute/tools/` → `.assets/tools/`
- 更新位置决策树

### 2.3 合并 requirements.txt

- 在 `hydraulic/` 根目录创建统一的 `requirements.txt`
- 删除 `irrigation/ngxs1/ngxs交付0119/requirements.txt` 和 `irrigation/ngxs1/api/requirements.txt`（与 `irrigation/ngxs1/requirements.txt` 完全重复）
- 各子项目的 requirements.txt 保留（Streamlit Cloud 部署需要）
- 主项目 requirements.txt 末尾添加注释指向 hydraulic

---

## Phase 3: 文档更新

### 3.1 更新 hydraulic/INDEX.md
- `execute/hydraulic/` → `hydraulic/`
- 快速启动命令中的路径更新

### 3.2 更新 hydraulic/README.md
- 删除不存在的 `eco_flow/` 条目
- setup.sh 使用说明路径更新

### 3.3 更新主项目 CLAUDE.md
- 目录结构部分添加 `hydraulic/` 说明

### 3.4 更新 hydraulic/SETUP_COMPLETE.md
- 检查并修复过时路径引用

---

## 不做的事情（明确排除）

- **不合并 `_lib/`**：hydraulic 的 `_lib/`（qgis_common、xlsx_common）与主项目 `.assets/lib/` 领域不同，保持独立
- **不拆散子项目**：capacity、geocode 等保持独立目录结构
- **不合并两个 config.py 的重叠**：qgis_common 和 xlsx_common 的 config 服务不同消费者，格式不同
- **不创建 Raycast 入口**：hydraulic 工具主要通过 CLI/Streamlit 使用，不适合 Raycast 快捷调用

---

## 验收标准

- [ ] `health_check.py` 全部通过（含新增的 hydraulic 检查项）
- [ ] hydraulic/ 下 0 个断裂符号链接
- [ ] hydraulic/ 下 0 处 `#!/Users/tianli/miniforge3` shebang
- [ ] hydraulic/ 下 0 处 `/Users/tianli/useful_scripts/execute` 路径
- [ ] setup.sh 使用动态路径，可在任意目录 source
- [ ] 所有 Python 文件语法检查通过
- [ ] structure skill 中无过时路径

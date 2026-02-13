# Hydraulic 整合进 .assets 体系 — 重构方案

## Context

当前项目存在两套并行的代码体系：`.assets/`（通用脚本）和 `hydraulic/`（水利工具）。两者各自有独立的公共库、依赖管理、命名规范和入口方式，导致代码重复、结构割裂。`.oa` Web 管理界面只覆盖了 `.assets/scripts/`，完全看不到 `hydraulic/` 的工具。

**目标**：统一为一套体系 — 一套公共库、一套命名规范、一个入口（.oa），消除冗余。

---

## 一、核心设计决策

### 1. hydraulic 子模块保留为独立项目目录

每个子模块（capacity, geocode, reservoir_schedule 等）都是包含 `src/`, `data/`, `templates/` 的完整项目，不能拆散成单文件。做法是：**整体迁入 `.assets/projects/`**，共享 `.assets/lib/` 公共库。

### 2. 两套 _lib 合并为一套

- 通用部分（Excel 读写、文件操作）→ 上提到 `.assets/lib/`
- 水利领域专用部分（河流编码、QGIS 配置）→ `.assets/lib/hydraulic/`

### 3. .oa 扩展扫描范围

sync-scripts.py 增加对 `.assets/projects/` 的扫描，每个项目通过 `_project.yaml` 提供元数据。

---

## 二、目标目录结构

```
useful_scripts/
├── .assets/
│   ├── lib/                          # 统一公共库（唯一真相源）
│   │   ├── display.py                # UI 输出（已有）
│   │   ├── file_ops.py               # 文件操作（已有，需扩展）
│   │   ├── finder.py                 # Finder 交互（已有）
│   │   ├── clipboard.py              # 剪贴板（已有）
│   │   ├── usage_log.py              # 使用统计（已有）
│   │   ├── env.py                    # 环境配置（已有，需扩展）
│   │   ├── common.py                 # 兼容 shim（已有）
│   │   ├── common.sh / clashx.sh     # Shell 库（已有）
│   │   ├── excel_ops.py              # Excel 操作（新增，合并自两套体系）
│   │   └── hydraulic/                # 水利领域专用库（新增）
│   │       ├── __init__.py
│   │       ├── config.py             # 河流/流域/行政区编码映射
│   │       ├── code_utils.py         # 编码规范化工具
│   │       ├── qgis_config.py        # QGIS 专用配置
│   │       └── qgis_fields.py        # QGIS 字段定义
│   │
│   ├── core/                         # 核心处理逻辑（已有，不变）
│   │   ├── csv_core.py
│   │   ├── docx_core.py
│   │   └── xlsx_core.py
│   │
│   ├── scripts/                      # 扁平脚本入口（已有，不变）
│   │   └── ...（46 个脚本）
│   │
│   ├── projects/                     # 复杂多文件项目（新增）
│   │   ├── capacity/                 # 纳污能力计算
│   │   ├── geocode/                  # 地理编码
│   │   ├── reservoir_schedule/       # 水库调度
│   │   ├── irrigation/               # 灌溉需水
│   │   ├── district_scheduler/       # 区域调度
│   │   ├── risk_data/                # 风险分析表填充
│   │   ├── qgis/                     # QGIS 空间处理
│   │   ├── company_query/            # 企业查询
│   │   ├── cad/                      # CAD 脚本
│   │   ├── rainfall/                 # 降雨数据
│   │   ├── water_annual/             # 年度水资源
│   │   ├── setup.sh                  # 环境配置（更新路径）
│   │   ├── INDEX.md                  # 模块索引
│   │   └── README.md
│   │
│   └── templates/                    # 模板文件（已有）
│
├── raycast/
│   ├── ...（已有分类）
│   └── hydraulic/                    # 水利工具 Raycast 入口（新增）
│
├── .oa/                              # Web 管理界面（需扩展 sync-scripts.py）
├── requirements.txt                  # 根级依赖（合并 hydraulic 依赖）
└── CLAUDE.md                         # 项目说明（需更新）
```

**关键变化**：
- `hydraulic/` 整体迁入 `.assets/projects/`，顶层不再有 `hydraulic/` 目录
- `hydraulic/_lib/` 拆解合并到 `.assets/lib/` + `.assets/lib/hydraulic/`

---

## 三、公共库合并策略

### 3.1 file_ops.py — 扩展

从 `hydraulic/_lib/xlsx_common/file_utils.py` 迁入通用函数：

| 函数 | 来源 | 说明 |
|------|------|------|
| `read_geojson()` | file_utils.py | 读取 GeoJSON 文件 |
| `create_backup()` | file_utils.py | 创建带时间戳的文件备份 |
| `save_report()` | file_utils.py | 保存文本报告 |
| `check_file_exists()` | file_utils.py | **删除**（与现有版本重复） |

### 3.2 excel_ops.py — 新建

从 `hydraulic/_lib/xlsx_common/excel_utils.py` 提取通用 Excel 操作：

```python
# .assets/lib/excel_ops.py
def load_excel_sheet(excel_path, sheet_name) -> pd.DataFrame
def save_to_excel(df, excel_path, sheet_name, index=False)
def load_csv_data(csv_path, dtype=None) -> pd.DataFrame
def check_columns_exist(df, required_columns, data_desc="数据")
```

与 `core/xlsx_core.py` 不冲突 — xlsx_core 做格式转换（xlsx→csv），excel_ops 做 sheet 级数据读写。

### 3.3 lib/hydraulic/ — 水利领域专用

| 文件 | 来源 | 内容 |
|------|------|------|
| `config.py` | xlsx_common/config.py | 河流编码、流域映射、行政区映射 |
| `code_utils.py` | xlsx_common/code_utils.py | normalize_code, get_river_code, generate_dike_code 等 |
| `qgis_config.py` | qgis_common/config.py | QGIS 坐标系、图层配置、处理参数 |
| `qgis_fields.py` | qgis_common/fields.py | QGIS 图层字段规格 |

注意：河流编码在 xlsx_common 中用大写（`'SX'`），qgis_common 中用小写（`'sx'`）。合并后统一存储小写，通过参数控制返回大小写。

### 3.4 显示输出

hydraulic 脚本中的 `print("✓ ...")` / `print("✗ ...")` 应逐步迁移为 `display.py` 的 `show_success()` / `show_error()`。**渐进式改进，不在第一阶段强制**。

---

## 四、.oa 和 Raycast 适配

### 4.1 sync-scripts.py 扩展

新增扫描 `.assets/projects/`，通过 `_project.yaml` 读取元数据：

```yaml
# .assets/projects/capacity/_project.yaml
name: capacity
title: 纳污能力计算
description: 水环境功能区纳污能力计算（GUI + CLI）
type: hydraulic
icon: "🌊"
status: active
entry:
  web: web_app.py
  cli: cli_run.py
tags: [streamlit, hydraulic, calculation]
```

TYPE_MAP 新增：`"hydraulic": {"icon": "🌊", "color": "#0284C7", "name": "水利工具"}`

### 4.2 Raycast 入口

`raycast/hydraulic/` 下放置启动脚本（Shell 包装，非符号链接）：

```bash
#!/bin/bash
# @raycast.title 纳污能力计算
# @raycast.mode silent
# @raycast.icon 🌊
cd "$(dirname "$0")/../../.assets/projects/capacity"
streamlit run web_app.py
```

---

## 五、引用路径统一

### 迁移后的标准引用模式

**`.assets/scripts/` 下的脚本**（不变）：
```python
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))
```

**`.assets/projects/xxx/` 下的脚本**（统一为）：
```python
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "lib"))
# 即 .assets/projects/xxx/ → .assets/lib/
```

**具体变更**：

| 模块 | 之前 | 之后 |
|------|------|------|
| risk_data/*.py | `from xlsx_common import ...` | `from hydraulic import ...` + `from excel_ops import ...` |
| qgis/pipeline/*.py | `from qgis_common import ...` | `from hydraulic.qgis_config import ...` |
| capacity/src/*.py | 引用 xlsx_common | 引用 `excel_ops` + `hydraulic` |

---

## 六、依赖管理统一

将 `hydraulic/requirements.txt` 合并到根级 `requirements.txt`，新增：

```
# Web 框架（projects）
streamlit>=1.28.0
fastapi>=0.109.0
uvicorn>=0.27.0
python-multipart>=0.0.6

# 科学计算（projects）
scipy>=1.9.0
plotly>=5.0.0
pydantic>=2.6.0
requests>=2.26.0
```

各子项目的 `requirements.txt` 保留（Streamlit Cloud 部署需要）。

---

## 七、执行步骤

### Phase 1：准备公共库（不改变现有行为）

1. 创建 `.assets/lib/hydraulic/` 目录及 `__init__.py`
2. 创建 `lib/hydraulic/config.py` — 合并河流/流域编码映射
3. 迁移 `lib/hydraulic/code_utils.py` — 更新 import 指向新 config
4. 迁移 `lib/hydraulic/qgis_config.py` + `qgis_fields.py`
5. 创建 `lib/excel_ops.py` — 提取通用 Excel 操作函数
6. 扩展 `lib/file_ops.py` — 新增 read_geojson, create_backup, save_report
7. 扩展 `lib/env.py` — 新增 ASSETS_ROOT, PROJECTS_DIR 常量

### Phase 2：迁移项目目录

8. 创建 `.assets/projects/` 目录
9. 逐个迁移 11 个子模块：`mv hydraulic/xxx .assets/projects/xxx`
10. 迁移 setup.sh / INDEX.md / README.md 到 `.assets/projects/`
11. 为每个项目创建 `_project.yaml` 元数据文件
12. 删除 `hydraulic/_lib/`（已合并）和空的 `hydraulic/` 目录

### Phase 3：更新引用路径

13. 更新 risk_data/ 下所有脚本的 import 路径
14. 更新 qgis/ 下所有脚本的 `_setup_paths()` 和 import
15. 更新 capacity/, geocode/, reservoir_schedule/ 等 Streamlit 项目中引用 _lib 的地方
16. 更新 `.assets/projects/setup.sh` 中的路径常量

### Phase 4：适配 .oa 和 Raycast

17. 扩展 `.oa/scripts/sync-scripts.py` — 新增 projects 扫描
18. 创建 `raycast/hydraulic/` 目录及启动脚本
19. 运行 sync-scripts.py 重新生成 scripts.json

### Phase 5：收尾

20. 合并依赖到根级 `requirements.txt`
21. 更新 `CLAUDE.md` 目录结构说明
22. 更新 `.assets/tools/health_check.py` 路径引用
23. 运行 health_check 验证所有引用路径有效

---

## 八、验证方式

1. `python3 .assets/tools/health_check.py` — 检查所有引用路径
2. `python3 .oa/scripts/sync-scripts.py` — 确认 projects 被正确索引
3. 逐个测试 Streamlit 项目能否正常启动：
   - `cd .assets/projects/capacity && streamlit run web_app.py`
   - `cd .assets/projects/geocode && streamlit run app.py`
4. 测试 risk_data 脚本的 import 是否正常
5. 确认 `hydraulic/` 目录已完全清除
6. `git diff --stat` 确认没有遗漏文件

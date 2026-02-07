---
name: dev-structure
description: 开发部目录结构规范。水利工具位置、命名规则、禁止行为。当创建新文件/目录时触发。
---

# 开发部工具结构规范

> 此规范约束所有在开发部创建文件/目录时的行为
> 📅 更新：2025-02-06

## 核心目录结构

```
~/useful_scripts/
├── .assets/                     # 核心资源
│   ├── scripts/                 # 功能脚本入口（所有可执行脚本实体）
│   ├── lib/                     # 通用工具库（common.py, common.sh 等）
│   │   └── hydraulic/           # 水利领域公共库（编码映射、QGIS 配置）
│   ├── core/                    # 核心处理逻辑（csv_core, docx_core 等）
│   ├── projects/                # ⭐ 复杂多文件项目（水利工具集等）
│   ├── tools/                   # 项目工具（health_check.py 等）
│   └── templates/               # 模板文件
├── raycast/                     # Raycast 入口，按功能分目录，内容为指向 .assets/scripts/ 的符号链接
├── _index/                      # 脚本索引
├── .oa/                         # Next.js Web 应用（独立子项目）
└── CLAUDE.md                    # 项目说明
```

## 水利工具规范

**强制规则**：所有水利相关工具必须放在 `.assets/projects/` 下

### 水利工具目录结构

```
.assets/projects/
├── capacity/           # 纳污能力计算（Streamlit）
├── geocode/            # 地理编码（Streamlit）
├── reservoir_schedule/ # 水库调度（Streamlit）
├── irrigation/         # 灌溉需水（Streamlit）
├── district_scheduler/ # 区域调度（Streamlit）
├── qgis/               # QGIS 空间处理（Pipeline）
├── company_query/      # 企业查询（CLI）
├── risk_data/          # 风险分析表填充（CLI）
├── cad/                # CAD 脚本
├── rainfall/           # 降雨数据
└── water_annual/       # 年度水资源数据

.assets/lib/hydraulic/  # 水利领域公共库（编码映射、QGIS 配置）
```

### 新建水利工具流程

1. 先检查 `.assets/projects/` 下是否有类似功能目录
2. 有则在现有目录下添加，无则新建子目录
3. 子目录必须包含 `_project.yaml`
4. 目录名用英文，文件名可用中文
5. 水利公共库放 `.assets/lib/hydraulic/`，项目内不创建独立 `_lib/`

## 目录命名规范

| 类型 | 规则 | 示例 |
|------|------|------|
| 目录名 | 英文小写，下划线分隔 | `company_query/` |
| 脚本文件 | 英文小写，下划线分隔 | `calc_core.py` |
| 数据文件 | 可用中文 | `计算结果.xlsx` |
| 配置文件 | 英文 | `config.py` |

## 禁止行为

1. **禁止**在根目录创建中文目录
2. **禁止**在 `.assets/` 直接创建中文目录
3. **禁止**在 `.assets/lib/` 放完整项目工具（只放可 import 模块）
4. **禁止**在多个位置创建同功能工具
5. **禁止**创建与现有目录重复的新目录

## 位置决策树

```
新建文件/目录时：

Q1: 是水利相关吗？
  → YES: 放 .assets/projects/ 下（公共库放 .assets/lib/hydraulic/）
  → NO: 继续

Q2: 是 Raycast 脚本吗？
  → YES: 实体放 .assets/scripts/，raycast/ 下创建符号链接
  → NO: 继续

Q3: 是可复用的库模块吗？
  → YES: 放 .assets/lib/
  → NO: 继续

Q4: 是独立工具吗？
  → YES: 放 .assets/tools/
  → NO: 放合适的子目录

Q5: 是过时/冗余的文件吗？
  → YES: 删除或归档
  → NO: 根据实际情况判断
```

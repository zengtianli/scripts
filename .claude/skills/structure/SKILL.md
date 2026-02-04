---
name: dev-structure
description: 开发部目录结构规范。水利工具位置、命名规则、禁止行为。当创建新文件/目录时触发。
---

# 开发部工具结构规范

> 此规范约束所有在开发部创建文件/目录时的行为
> 📅 更新：2025-01-19

## 核心目录结构

```
~/useful_scripts/
├── execute/                      # 执行脚本（核心）
│   ├── raycast/                  # Raycast 快捷脚本（扁平化）
│   │   ├── _lib/                 # 公共库（仅放可 import 模块）
│   │   └── _core/                # 核心模块
│   ├── tools/                    # 通用工具
│   │   ├── read/                 # 读取工具
│   │   ├── analyze/              # 分析工具
│   │   ├── transform/            # 转换工具
│   │   └── system/               # 系统工具
│   ├── hydraulic/                # ⭐ 水利专用工具（独立目录）
│   ├── compare/                  # 比较工具
│   ├── docs/                     # 文档
│   └── archived/                 # 归档文件
├── system/                       # 系统服务
└── projects/                     # 项目资源
```

## 水利工具规范

**强制规则**：所有水利相关工具必须放在 `execute/hydraulic/` 下

### 水利工具目录结构

```
execute/hydraulic/
├── _lib/              # 公共库
├── capacity/          # 纳污能力计算
├── geocode/           # 地理编码
├── reservoir_schedule/# 水库调度
├── irrigation/        # 灌溉需水
├── district_scheduler/# 区域调度
├── qgis/              # QGIS 空间处理
├── company_query/     # 企业查询
├── risk_data/         # 风险分析
├── cad/               # CAD 脚本
├── rainfall/          # 降雨数据
├── water_annual/      # 年度数据
└── INDEX.md           # 总索引
```

### 新建水利工具流程

1. 先检查 `hydraulic/` 下是否有类似功能目录
2. 有则在现有目录下添加，无则新建子目录
3. 子目录必须包含 README.md
4. 目录名用英文，文件名可用中文

## 目录命名规范

| 类型 | 规则 | 示例 |
|------|------|------|
| 目录名 | 英文小写，下划线分隔 | `company_query/` |
| 脚本文件 | 英文小写，下划线分隔 | `calc_core.py` |
| 数据文件 | 可用中文 | `计算结果.xlsx` |
| 配置文件 | 英文 | `config.py` |

## 禁止行为

1. **禁止**在根目录创建中文目录
2. **禁止**在 `execute/` 直接创建中文目录
3. **禁止**在 `_lib/` 放完整项目工具（只放可 import 模块）
4. **禁止**在多个位置创建同功能工具
5. **禁止**创建与现有目录重复的新目录

## 位置决策树

```
新建文件/目录时：

Q1: 是水利相关吗？
  → YES: 放 execute/hydraulic/ 下
  → NO: 继续

Q2: 是 Raycast 脚本吗？
  → YES: 放 execute/raycast/ 根目录（扁平化）
  → NO: 继续

Q3: 是可复用的库模块吗？
  → YES: 放 execute/raycast/_lib/
  → NO: 继续

Q4: 是独立工具吗？
  → YES: 放 execute/tools/
  → NO: 放 execute/ 合适的子目录

Q5: 是过时/冗余的文件吗？
  → YES: 放 execute/archived/
  → NO: 根据实际情况判断
```

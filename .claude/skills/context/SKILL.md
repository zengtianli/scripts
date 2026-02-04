---
name: dev-context
description: 开发部项目上下文。脚本库路径、目录结构、服务对象。当在 useful_scripts 项目工作时触发。
---

# 开发部项目上下文

> 📍 位置：`/Users/tianli/useful_scripts/`

## 项目定位

这是一个**脚本工具库主项目**，为其他项目提供可复用的 Python/Shell 脚本。

## 目录结构

```
useful_scripts/
├── .cursor/
│   ├── rules/               ← Cursor 规则配置
│   └── skills-local/dev/    ← 本地 skills
├── execute/                 ← 【核心】脚本执行库
│   ├── raycast/             Raycast 快捷脚本（扁平化）
│   │   ├── _lib/            公共库
│   │   └── _core/           核心模块
│   ├── tools/               通用工具
│   │   ├── read/            读取工具
│   │   ├── analyze/         分析工具
│   │   ├── transform/       转换工具
│   │   └── system/          系统工具
│   ├── hydraulic/           ⭐ 水利专用工具
│   ├── compare/             文件比较工具
│   ├── agents/              Agent 配置
│   ├── docs/                文档说明
│   └── archived/            归档文件
├── system/                  ← 系统服务（task, backup, gitc）
└── projects/                ← 项目资源（临时）
```

## 核心原则

1. **不重复造轮子** - 开发前先查现有工具
2. **通用化设计** - 新脚本要能跨项目复用
3. **代码与数据分离** - 数据文件放 zdwp/data/

## 环境配置

| 配置项 | 值 |
|-------|-----|
| Python | `/Users/tianli/miniforge3/bin/python3` |
| 脚本库根目录 | `/Users/tianli/useful_scripts/execute/` |

## 服务对象

| 业务公司 | 路径 | 数据位置 |
|----------|------|----------|
| ZDWP 水利公司 | `~/Downloads/zdwp/` | `~/Downloads/zdwp/data/` |

## 关键路径速查

| 用途 | 路径 |
|-----|------|
| 读取文档 | `execute/tools/read/` |
| 格式修复 | `execute/raycast/docx_*.py` |
| 文件比较 | `execute/compare/` |
| Raycast 脚本 | `execute/raycast/` |
| 水利工具 | `execute/hydraulic/` |

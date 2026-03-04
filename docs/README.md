# useful_scripts 文档

本目录包含项目文档的符号链接。

## 文档位置

实际文档存储在 `~/docs/` 中，本目录通过符号链接引用：

```
docs/
└── raycast -> ~/docs/raycast/  (符号链接)
```

## 为什么使用符号链接？

1. **单一数据源**：所有文档集中在 `~/docs/` 管理
2. **避免重复**：多个项目可以共享同一份文档
3. **自动同步**：修改一处，所有引用自动更新

## 开发时

直接编辑 `~/docs/` 中的文档，项目中会自动看到更新：

```bash
# 编辑文档
vim ~/docs/raycast/command-standard.md

# 项目中自动同步
cat ~/useful_scripts/docs/raycast/command-standard.md
```

## 分享项目时

使用提供的脚本将符号链接替换为实际文件：

### 方法 1: 使用 rsync（推荐）

```bash
# 自动解引用符号链接并打包
~/useful_scripts/scripts/prepare_share.sh ~/useful_scripts
```

### 方法 2: 使用 Python 脚本

```bash
# 预览
python3 ~/useful_scripts/scripts/dereference_links.py ~/useful_scripts/docs --dry-run

# 执行替换
python3 ~/useful_scripts/scripts/dereference_links.py ~/useful_scripts/docs
```

### 方法 3: 手动使用 rsync

```bash
# -L 参数会自动跟随符号链接
rsync -avL ~/useful_scripts/ /tmp/useful_scripts_share/
tar -czf useful_scripts.tar.gz -C /tmp useful_scripts_share
```

## Git 处理

符号链接已添加到 `.gitignore`，Git 不会跟踪它们。

如果需要在 Git 中记录符号链接本身：
```bash
# 从 .gitignore 中移除
# Git 会记录符号链接（不是目标文件）
git add docs/raycast
```

## 文档结构

```
~/docs/
├── raycast/                    # Raycast 命令相关文档
│   ├── command-standard.md     # 命令规范
│   ├── commands-full-list.md   # 完整命令清单
│   ├── commands-analysis.md    # 命令分析报告
│   └── refactor-2026-03-02.md  # 重构报告
└── secretary-system/           # 秘书系统文档
    ├── README.md
    ├── Phase1完成报告.md
    ├── Phase2完成报告.md
    └── Phase3完成报告.md
```

## 相关脚本

- `scripts/dereference_links.py` - 将符号链接替换为实际文件
- `scripts/prepare_share.sh` - 一键准备项目用于分享

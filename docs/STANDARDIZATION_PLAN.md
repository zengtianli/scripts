# useful_scripts 标准化方案

**创建时间**：2026-03-04
**状态**：待批准

---

## 背景

useful_scripts 是核心脚本库，包含 81 个功能脚本和 68 个 Raycast 命令。当前已完成目录重构（scripts 按分类组织），但仍需完善文档和 Git 管理。

---

## 当前状态评估

### ✅ 已完成
- 脚本按分类组织（data/document/file/network/secretary/system/tools/window）
- Raycast 命令统一在 raycast/commands/
- 公共库在 lib/（含 core/hydraulic/tools 子模块）
- 有 CLAUDE.md 项目说明
- Git 管理（main 分支，清晰的提交历史）

### ❌ 待完成
1. **缺少 README.md**（项目概览、快速开始、脚本索引）
2. **缺少 develop 分支**（开发/稳定版本分离）
3. **5 个断裂的符号链接**（需要清理）
4. **2 个代码质量问题**（daily_summary.py 硬编码路径）
5. **临时文档堆积**（3 个 RAYCAST_*.md 文件）

---

## 标准化方案

### 方案 A：完整标准化 **【推荐】**

**包含内容**：
1. 创建 README.md（项目概览 + 脚本索引）
2. 创建 develop 分支
3. 清理断裂符号链接
4. 修复代码质量问题
5. 清理临时文档

**推荐理由**：
1. 符合工作流规范（脚本库需要 main + develop 分支）
2. 完善的文档让新用户快速上手
3. 清理断裂链接避免混淆
4. 修复代码质量问题提升可维护性

**预计时间**：1-1.5 小时

---

### 方案 B：最小化标准化

**包含内容**：
1. 仅创建 README.md
2. 清理断裂符号链接

**不推荐理由**：
- 不符合工作流规范（缺少 develop 分支）
- 代码质量问题未解决

---

## 推荐方案详细计划

### 第 1 步：创建 README.md（30分钟）

**内容结构**：
```markdown
# useful_scripts

macOS 个人效率工具脚本库，主要通过 Raycast 调用。

## 快速开始
- 环境要求
- 安装依赖
- Raycast 集成

## 脚本索引
- 按分类列出所有脚本
- 每个脚本的功能说明

## 项目结构
- scripts/：功能脚本
- raycast/：Raycast 命令
- lib/：公共库
- projects/：复杂项目

## 开发指南
- 如何添加新脚本
- 命名规范
- 引用路径规范
```

**实现方式**：
- 基于现有 CLAUDE.md 扩展
- 自动生成脚本索引（读取 scripts/ 目录）

---

### 第 2 步：创建 develop 分支（5分钟）

```bash
git checkout -b develop
git push -u origin develop
git checkout main
```

**分支策略**：
- `main`：稳定版本（生产环境）
- `develop`：开发版本（日常开发）

---

### 第 3 步：清理断裂符号链接（10分钟）

**需要删除的链接**：
1. `.claude/rules/core-minimal.mdc`
2. `.claude/skills/raycast/scripts/sys_oa_dev.sh`
3. `.claude/skills/raycast/scripts/sys_oa_zdwp.sh`
4. `_index/by-platform/raycast/sys_oa_dev.sh`
5. `_index/by-platform/raycast/sys_oa_zdwp.sh`

**操作**：
```bash
find . -type l ! -exec test -e {} \; -print | xargs rm
```

---

### 第 4 步：修复代码质量问题（15分钟）

**问题文件**：`scripts/secretary/daily_summary.py`

**修复内容**：
1. 将 shebang 改为 `#!/usr/bin/env python3`
2. 移除硬编码路径 `/Users/tianli/miniforge3/bin/python3`

---

### 第 5 步：清理临时文档（5分钟）

**需要处理的文件**：
- `RAYCAST_CLEANUP_SUMMARY.md`
- `RAYCAST_COMMANDS_ANALYSIS.md`
- `RAYCAST_FIX_PLAN.md`

**选项**：
- [ ] A. 移动到 `~/docs/sessions/2026-03/`
- [x] B. 直接删除（已完成重构，不再需要） **【推荐】**

**推荐理由**：
1. 这些是临时分析文档，重构已完成
2. 相关信息已整合到 CLAUDE.md
3. 保留会造成混淆

---

### 第 6 步：验证和提交（15分钟）

**验证清单**：
- [ ] README.md 完整且准确
- [ ] develop 分支已创建
- [ ] 断裂链接已清理
- [ ] 代码质量问题已修复
- [ ] 临时文档已清理
- [ ] health_check.py 通过

**提交**：
```bash
git add .
git commit -m "Standardize project: add README, create develop branch, cleanup broken links"
git push origin main develop
```

---

## 验证方式

### 文档验证
```bash
cat README.md
cat CLAUDE.md
```

### Git 验证
```bash
git branch -a
git log --oneline -5
```

### 健康检查
```bash
python3 lib/tools/health_check.py
```

---

## 预期成果

1. **完善的文档**
   - ✅ README.md：项目概览、快速开始、脚本索引
   - ✅ CLAUDE.md：Claude Code 说明、项目定位

2. **完整的 Git 管理**
   - ✅ main 分支（稳定版本）
   - ✅ develop 分支（开发版本）

3. **清洁的代码库**
   - ✅ 无断裂符号链接
   - ✅ 无代码质量警告
   - ✅ 无临时文档堆积

4. **通过健康检查**
   - ✅ 所有检查项通过

---

## 你的想法

> [tianli] 请确认是否批准此方案，或提出修改建议。
> /Users/tianli/useful_scripts/.oa
> 这里就不要了，因为后面都直接集成到 ~/Dev 里的oa
> ~/Dev
> ❯ l
> lrwxr-xr-x - tianli  3 Mar 15:12  configs -> /Users/tianli/Documents/sync
> lrwxr-xr-x - tianli  4 Mar 11:13  oa -> /Users/tianli/Dev/oa-project
> drwxr-xr-x - tianli  4 Mar 16:07  oa-project
> lrwxr-xr-x - tianli  3 Mar 15:12  scripts -> /Users/tianli/useful_scripts
> 我看了下，怎么那么多 ln，都不要了啊
> 要么把useful_scripts 也直接迁移到 ~/Dev里了，反正之前做过migration 的项目了，你cc记忆里有的
> config 也不要 sync了，直接 就本地了

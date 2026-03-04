# useful_scripts 迁移 + 标准化方案

**创建时间**：2026-03-04
**状态**：待批准

---

## 背景

根据用户反馈，需要进行更大的架构调整：
1. 删除 `.oa` 和 `.secretary` 目录（已整合到 `~/Dev/oa-project`）
2. 清理所有符号链接（30+ 个，太多了）
3. 将 `useful_scripts` 迁移到 `~/Dev/scripts`
4. 将 `configs` 从 sync 改为本地

**目标架构**：
```
~/Dev/
├── oa-project/          # OA 系统（已存在）
├── scripts/             # 脚本库（从 ~/useful_scripts 迁移）
└── configs/             # 配置文件（从 ~/Documents/sync 迁移，可选）
```

---

## 当前状态

### 符号链接统计（30+ 个）
- `research/*.md` → `~/docs/knowledge/`（4 个）
- `projects/*_docs` → `~/docs/projects/useful_scripts/`（12 个）
- `projects/*/README.md` → `~/docs/projects/useful_scripts/`（14 个）
- `.cursor/rules` → `.claude/rules`（1 个）
- `.cursor/skills-local` → `.claude/skills`（1 个）
- `projects_docs` → `~/docs/projects/useful_scripts`（1 个）
- 根目录的 md 符号链接（4 个）

### 冗余目录
- `.oa/`：Next.js 应用（已整合到 `~/Dev/oa-project`）
- `.secretary/`：Next.js 应用（已整合到 `~/Dev/oa-project`）

---

## 方案对比

### 方案 A：完整迁移 + 标准化 **【推荐】**

**包含内容**：
1. 删除 `.oa` 和 `.secretary` 目录
2. 清理所有符号链接（保留 `.cursor/` 下的）
3. 将 `useful_scripts` 迁移到 `~/Dev/scripts`
4. 创建 README.md
5. 创建 develop 分支
6. 修复代码质量问题
7. 清理临时文档

**推荐理由**：
1. 统一开发目录（所有开发项目在 `~/Dev/`）
2. 消除符号链接依赖（简化结构）
3. 符合工作流规范（main + develop 分支）
4. 完善的文档让新用户快速上手

**预计时间**：1.5-2 小时

---

### 方案 B：仅清理 + 标准化（不迁移）

**包含内容**：
1. 删除 `.oa` 和 `.secretary` 目录
2. 清理所有符号链接
3. 创建 README.md
4. 创建 develop 分支
5. 修复代码质量问题
6. 清理临时文档

**不推荐理由**：
- 不符合目标架构（项目仍在 `~/useful_scripts`）
- `~/Dev/scripts` 符号链接仍然存在

---

## 推荐方案详细计划（方案 A）

### 第 0 步：备份和准备（10分钟）

**备份当前状态**：
```bash
cd ~/useful_scripts
git status
git add -A
git commit -m "Backup before migration to ~/Dev/scripts"
```

**检查依赖**：
- [ ] Raycast 命令路径
- [ ] OA 系统引用
- [ ] 其他脚本引用
- [ ] 环境变量（~/.zshrc）

---

### 第 1 步：删除冗余目录（5分钟）

**删除 .oa 和 .secretary**：
```bash
cd ~/useful_scripts
rm -rf .oa .secretary
```

**理由**：
- `.oa` 已整合到 `~/Dev/oa-project`
- `.secretary` 已整合到 `~/Dev/oa-project/secretary`

---

### 第 2 步：清理符号链接（10分钟）

**处理方式**：
- [x] 保留 `.cursor/` 下的符号链接（Cursor IDE 需要）
- [x] 删除其他所有符号链接

**操作**：
```bash
cd ~/useful_scripts

# 删除 research/ 下的符号链接
rm research/*.md

# 删除 projects/ 下的符号链接
find projects -type l -delete

# 删除根目录下的符号链接（保留 .cursor/）
rm 应用使用追踪技术方案.md 多秘书系统架构.md Apple提醒事项集成方案.md TTS_PLAN.md projects_docs
```

---

### 第 3 步：迁移到 ~/Dev/scripts（20分钟）

**迁移步骤**：
```bash
# 1. 删除 ~/Dev/scripts 符号链接
rm ~/Dev/scripts

# 2. 移动目录
mv ~/useful_scripts ~/Dev/scripts

# 3. 验证
cd ~/Dev/scripts
ls -la
git status
```

**需要更新的引用**：
1. **Raycast 命令**：
   - 检查 `raycast/commands/*.sh` 是否有硬编码路径
   - 检查 `raycast/lib/run_python.sh` 路径引用

2. **OA 系统**：
   - 检查 `~/Dev/oa-project` 是否引用了 `useful_scripts`
   - 更新为 `~/Dev/scripts`

3. **全局配置**：
   - `~/.zshrc` 或 `~/.bashrc` 中的 PATH
   - `~/.claude/CLAUDE.md` 中的路径引用

---

### 第 4 步：创建 README.md（30分钟）

**内容结构**：
```markdown
# scripts

macOS 个人效率工具脚本库，主要通过 Raycast 调用。

## 快速开始

### 环境要求
- macOS 12+
- Python 3.9+
- Node.js 18+ (for projects)

### 安装依赖
```bash
pip3 install -r requirements.txt
```

### Raycast 集成
1. 打开 Raycast 设置
2. 添加脚本目录：`~/Dev/scripts/raycast/commands`
3. 刷新脚本列表

## 脚本索引

### 数据处理（data/）
- csv_from_txt.py - TXT 转 CSV
- csv_to_txt.py - CSV 转 TXT
- xlsx_from_csv.py - CSV 转 Excel
- ...

### 文档处理（document/）
- docx_text_formatter.py - Word 文档格式化
- md_formatter.py - Markdown 格式化
- pptx_font_yahei.py - PPT 字体统一
- ...

### 文件操作（file/）
- folder_create.py - 批量创建文件夹
- folder_add_prefix.py - 文件夹批量加前缀
- ...

### 系统工具（system/）
- sys_app_launcher.sh - 应用启动器
- app_tracker.py - 应用使用追踪
- ...

### 秘书系统（secretary/）
- daily_summary.py - 每日总结
- weekly_review_reminder.sh - 周回顾提醒
- ...

### 网络工具（network/）
- clashx_*.sh - ClashX 代理管理
- ...

### 窗口管理（window/）
- yabai_org.py - 窗口布局管理
- ...

### 通用工具（tools/）
- tts.py - 文本转语音
- gantt.py - 甘特图生成
- ...

## 项目结构

```
scripts/              # 功能脚本，按类别分组
├── document/         # 文档处理
├── data/             # 数据转换
├── file/             # 文件操作
├── system/           # 系统工具
├── network/          # 网络代理
├── secretary/        # 秘书系统
├── window/           # 窗口管理
└── tools/            # 杂项工具

lib/                  # 统一公共库
├── core/             # 核心处理逻辑
├── hydraulic/        # 水利领域专用库
└── tools/            # 项目维护工具

projects/             # 复杂多文件项目
├── capacity/         # 纳污能力计算
├── geocode/          # 地理编码
├── reservoir_schedule/  # 水库调度
└── ...

raycast/              # Raycast 入口
├── commands/         # Shell wrapper 脚本
└── lib/              # 运行器

templates/            # 模板文件
```

## 开发指南

### 添加新脚本

1. 在对应分类下创建脚本：
```bash
# 例如：添加数据处理脚本
touch scripts/data/new_script.py
```

2. 添加 shebang 和导入：
```python
#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from common_utils import ...
```

3. 创建 Raycast wrapper：
```bash
touch raycast/commands/new_script.sh
```

4. 运行健康检查：
```bash
python3 lib/tools/health_check.py
```

### 命名规范

- 脚本保留功能前缀：`docx_`、`xlsx_`、`csv_`、`md_`、`pptx_`
- 文件/文件夹操作：`file_`、`folder_`
- 系统工具：`sys_`、`display_`
- 秘书系统：`sec_`
- 水利领域：`hy_`

### 引用路径规范

- Shell 引用库：`source "$(dirname "$0")/../../lib/xxx.sh"`
- Python 引用库：`sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))`
- 水利领域导入：`from hydraulic import ...`
- Excel 操作导入：`from excel_ops import ...`

## 维护

### 健康检查
```bash
python3 lib/tools/health_check.py
```

### 同步索引
```bash
python3 lib/tools/sync_index.py
```

## License

MIT
```

---

### 第 5 步：创建 develop 分支（5分钟）

```bash
cd ~/Dev/scripts
git checkout -b develop
git push -u origin develop
git checkout main
```

---

### 第 6 步：修复代码质量问题（15分钟）

**问题文件**：`scripts/secretary/daily_summary.py`

**修复内容**：
1. 将 shebang 改为 `#!/usr/bin/env python3`
2. 移除硬编码路径 `/Users/tianli/miniforge3/bin/python3`

---

### 第 7 步：清理临时文档（5分钟）

**删除**：
```bash
cd ~/Dev/scripts
rm RAYCAST_CLEANUP_SUMMARY.md RAYCAST_COMMANDS_ANALYSIS.md RAYCAST_FIX_PLAN.md
```

---

### 第 8 步：更新全局配置（15分钟）

**需要更新的配置**：

1. **~/.claude/CLAUDE.md**：
```bash
# 搜索并替换
sed -i '' 's|~/useful_scripts|~/Dev/scripts|g' ~/.claude/CLAUDE.md
sed -i '' 's|/Users/tianli/useful_scripts|/Users/tianli/Dev/scripts|g' ~/.claude/CLAUDE.md
```

2. **~/.zshrc 或 ~/.bashrc**：
```bash
# 检查是否有 useful_scripts 相关的 PATH
grep useful_scripts ~/.zshrc
# 如果有，手动更新为 ~/Dev/scripts
```

3. **Raycast 配置**：
- 打开 Raycast 设置
- 更新脚本目录：`~/Dev/scripts/raycast/commands`

---

### 第 9 步：验证和提交（15分钟）

**验证清单**：
- [ ] README.md 完整且准确
- [ ] develop 分支已创建
- [ ] 符号链接已清理（除了 .cursor/）
- [ ] 代码质量问题已修复
- [ ] 临时文档已清理
- [ ] health_check.py 通过
- [ ] Raycast 命令可用
- [ ] OA 系统正常

**提交**：
```bash
cd ~/Dev/scripts
git add .
git commit -m "Migrate to ~/Dev/scripts and standardize project structure

- Remove .oa and .secretary directories (integrated into oa-project)
- Clean up 30+ symbolic links
- Add comprehensive README.md
- Create develop branch
- Fix code quality issues
- Remove temporary documentation files
"
git push origin main develop
```

---

## 风险和注意事项

### 高风险项

1. **Raycast 命令失效**
   - 风险：迁移后路径变化，Raycast 找不到脚本
   - 缓解：迁移前检查所有硬编码路径，迁移后更新 Raycast 配置

2. **OA 系统引用失效**
   - 风险：OA 系统可能引用了 `useful_scripts` 路径
   - 缓解：迁移前搜索所有引用，迁移后测试 OA 系统

3. **Git 历史丢失**
   - 风险：移动目录可能导致 Git 历史丢失
   - 缓解：使用 `mv` 而非 `cp`，保留 `.git` 目录

### 中风险项

1. **符号链接清理**
   - 风险：删除符号链接后，某些功能可能失效
   - 缓解：逐步删除，测试后再继续

2. **路径引用更新**
   - 风险：遗漏某些路径引用
   - 缓解：全局搜索 `useful_scripts` 字符串

### 低风险项

1. **临时文档删除**
   - 风险：删除后无法恢复
   - 缓解：这些是临时分析文档，重构已完成，不需要保留

---

## 回滚计划

如果迁移失败，可以回滚：

```bash
# 1. 移回原位置
mv ~/Dev/scripts ~/useful_scripts

# 2. 恢复符号链接
ln -s ~/useful_scripts ~/Dev/scripts

# 3. 恢复 Git 状态
cd ~/useful_scripts
git reset --hard HEAD~1
```

---

## 预期成果

1. **统一的开发目录**
   - ✅ 所有开发项目在 `~/Dev/`
   - ✅ 无符号链接依赖

2. **完善的文档**
   - ✅ README.md：项目概览、快速开始、脚本索引
   - ✅ CLAUDE.md：Claude Code 说明、项目定位

3. **完整的 Git 管理**
   - ✅ main 分支（稳定版本）
   - ✅ develop 分支（开发版本）

4. **清洁的代码库**
   - ✅ 无冗余目录（.oa、.secretary）
   - ✅ 无断裂符号链接
   - ✅ 无代码质量警告
   - ✅ 无临时文档堆积

5. **通过健康检查**
   - ✅ 所有检查项通过

---

## 你的想法

> [tianli] 请确认是否批准方案 A（完整迁移 + 标准化），或选择方案 B（仅清理 + 标准化）。

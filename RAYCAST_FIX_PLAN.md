# Raycast Commands 修复计划

## 问题分析

1. **OA 路径问题**：
   - **OA 总控**：`~/Dev/oa` → 符号链接到 `~/cursor-shared/.oa`
   - **启动命令**：`cd ~/Dev/oa && pnpm dev`（端口 3000）
   - **秘书系统命令**：
     - `sec_oa.sh` - 路径正确（`~/cursor-shared/.oa`），但启动命令错误（`pnpm dev:oa` 应改为 `pnpm dev`）
     - `sec_report.sh` - 指向旧路径，功能已整合到 OA
     - `sec_review.sh` - 功能已整合到 OA

2. **秘书系统命令冗余**：
   - `sec_report.sh` - 查看报告（冗余，OA 内已有 `/secretary` 页面）
   - `sec_review.sh` - 每日复盘（冗余，OA 内已有）
   - 这些功能已整合到 OA 总控，不需要单独命令

3. **窗口管理命令失效**：
   - 旧命令已删除：`yabai_*.sh`
   - 新命令未验证：`yb_*.sh`

4. **其他命令可能的路径问题**：
   - 需要验证所有命令是否正确引用 `scripts/{category}/` 下的脚本
   - 检查是否有使用废弃路径（`execute/`、`.assets/scripts/`）

## 修复方案

### 1. 秘书系统命令处理

**保留并修正**：
- `sec_oa.sh` - 修正启动命令：`pnpm dev:oa` → `pnpm dev`

**删除**（功能已整合到 OA）：
- `sec_report.sh` - 功能在 OA 的 `/secretary` 页面
- `sec_review.sh` - 功能在 OA 的 `/secretary` 页面

### 2. 窗口管理命令验证

检查 `yb_*.sh` 是否正确调用 `scripts/window/` 下的脚本：
- `yb_float.sh`
- `yb_mouse_follow.sh`
- `yb_org.sh`
- `yb_toggle.sh`

### 3. 批量验证所有命令

创建验证脚本，检查：
1. 所有 raycast 命令是否正确引用 `run_python.sh`
2. 引用的脚本路径是否存在
3. 脚本路径是否使用了废弃路径（`execute/`、`.assets/scripts/`）

## 执行步骤

1. **修正 sec_oa.sh**
   - OA 路径保持 `~/cursor-shared/.oa`（或使用 `~/Dev/oa`）
   - 修正启动命令：`pnpm dev:oa` → `pnpm dev`

2. **删除冗余秘书命令**
   - 删除 `sec_report.sh`
   - 删除 `sec_review.sh`

3. **验证窗口管理命令**
   - 检查 `yb_*.sh` 是否正确调用脚本
   - 验证对应的 Python 脚本是否存在

4. **批量验证所有命令**
   - 运行验证脚本
   - 修复发现的问题

5. **更新文档**
   - 更新 CLAUDE.md 说明秘书系统已整合到 OA
   - 记录窗口管理命令的改名（yabai → yb）

## 预期结果

- 所有 raycast 命令都能正确执行
- 无冗余命令
- 路径引用正确（使用 `scripts/{category}/`）
- 文档更新完整

# 依赖引用检查报告

生成时间：2026-03-04
检查范围：useful_scripts 迁移到 ~/Dev/scripts 的影响分析

## 检查结果汇总

### 1. Raycast 命令（~/useful_scripts/raycast/）

**状态**：✅ 无需更新

**发现**：
- 只在 `_archived` 目录下找到 2 个旧文件引用了硬编码路径
- 当前使用的命令都使用相对路径或环境变量，不受影响

**文件清单**：
```
raycast/commands/_archived/secretary_merge_20260302/sec_life_report.sh
raycast/commands/_archived/secretary_merge_20260302/sec_life_log.sh
```

---

### 2. OA 系统（~/Dev/oa-project/）

**状态**：⚠️ 需要更新

**发现**：12 个文件引用了 useful_scripts 路径

#### 2.1 关键文件（必须更新）

**API 路由**：
- `app/api/secretary/daily/route.ts`
  - 第 13 行：`python3 ~/useful_scripts/scripts/secretary/collector.py`
  - 影响：秘书系统每日数据收集功能
  - 更新方式：改为 `~/Dev/scripts/scripts/secretary/collector.py`

**数据文件**（由 sync 脚本生成）：
- `data/scripts.json`
  - 所有脚本的 `path` 和 `directory` 字段
  - 影响：脚本库页面显示和文件操作
  - 更新方式：重新运行 `pnpm run sync:scripts`

- `data/all-projects.json`
  - 所有项目的 `path` 字段
  - 影响：项目看板页面显示和文件操作
  - 更新方式：重新运行 `pnpm run sync:projects`

**文档**：
- `CLAUDE.md`
  - 第 9 行：`~/Dev/oa/`（应为 `~/Dev/oa-project/`）
  - 第 15 行：`cd ~/Dev/oa && pnpm dev`（应为 `~/Dev/oa-project/`）
  - 影响：开发文档准确性
  - 更新方式：手动修改

#### 2.2 历史文件（可选更新）

**修复脚本**（已完成历史任务）：
- `scripts/fix-subdirectory-paths.py`
- `scripts/fix-assets-paths.py`
- `scripts/fix-script-paths.js`
- `scripts/import-today-sessions.mjs`

**文档**（历史记录）：
- `PATH_FIX_REPORT.md`
- `README.md`

**Skill 参考文档**：
- `.claude/skills/module-sync/references/data-format.md`

**构建产物**：
- `.next/server/app/page.js`（重新构建后自动更新）

---

### 3. Shell 配置（~/.zshrc）

**状态**：⚠️ 需要更新

**发现**：
```bash
# 第 7 行
export PATH="$HOME/useful_scripts/.assets/scripts:$PATH"
```

**问题**：
- `.assets/scripts` 目录已废弃（2026-03-04 清理）
- 此路径已无效

**更新方式**：
- 删除此行（脚本已迁移到 `scripts/` 目录，不需要 PATH）
- 或者更新为：`export PATH="$HOME/Dev/scripts/scripts:$PATH"`（如果需要直接调用脚本）

---

### 4. 全局配置（~/.claude/CLAUDE.md）

**状态**：⚠️ 需要更新

**发现**：6 处引用，都是文档说明性质的路径示例

**引用位置**：
```
第 156 行：❌ `/Users/tianli/useful_scripts/.assets/scripts/xxx`（已废弃）
第 157 行：❌ `/Users/tianli/useful_scripts/execute/xxx`（已废弃）
第 158 行：✅ `/Users/tianli/useful_scripts/scripts/{category}/xxx`（正确）
第 159 行：✅ `/Users/tianli/useful_scripts/raycast/commands/xxx`（正确）
第 173 行：| 脚本库（旧） | `~/useful_scripts/execute/`（已废弃） |
第 174 行：| 脚本库（新） | `~/useful_scripts/scripts/{data,document,file,network,secretary,system,tools,window}/` |
第 175 行：| 脚本库（Raycast） | `~/useful_scripts/raycast/commands/` |
```

**更新方式**：
- 将所有 `useful_scripts` 替换为 `Dev/scripts`
- 更新路径规范表格

---

## 更新清单（按优先级排序）

### 高优先级（影响功能）

1. **~/.zshrc**
   - 删除或更新 PATH 配置
   - 需要：`source ~/.zshrc` 重新加载

2. **~/Dev/oa-project/app/api/secretary/daily/route.ts**
   - 更新硬编码路径
   - 需要：重启 OA 服务

3. **~/Dev/oa-project/data/scripts.json**
   - 重新运行 sync 脚本
   - 命令：`cd ~/Dev/oa-project && pnpm run sync:scripts`

4. **~/Dev/oa-project/data/all-projects.json**
   - 重新运行 sync 脚本
   - 命令：`cd ~/Dev/oa-project && pnpm run sync:projects`

### 中优先级（影响文档准确性）

5. **~/.claude/CLAUDE.md**
   - 批量替换路径引用
   - 使用：`sed -i '' 's|useful_scripts|Dev/scripts|g' ~/.claude/CLAUDE.md`

6. **~/Dev/oa-project/CLAUDE.md**
   - 手动修改 2 处路径
   - 第 9 行和第 15 行

### 低优先级（历史文件）

7. **~/Dev/oa-project/scripts/fix-*.py**
   - 可选：更新注释中的路径说明
   - 不影响功能

8. **~/Dev/oa-project/PATH_FIX_REPORT.md**
   - 可选：添加迁移记录
   - 不影响功能

---

## 迁移后验证清单

- [ ] 秘书系统每日数据收集功能正常
- [ ] OA 脚本库页面显示正确路径
- [ ] OA 项目看板页面显示正确路径
- [ ] 文件操作（打开文件/目录）功能正常
- [ ] Shell 环境加载无错误
- [ ] 全局配置文档路径正确

---

## 建议

1. **迁移前**：
   - 备份 ~/.zshrc
   - 备份 ~/Dev/oa-project/app/api/secretary/daily/route.ts

2. **迁移时**：
   - 按优先级顺序更新
   - 每更新一项，立即验证功能

3. **迁移后**：
   - 运行 OA sync 脚本重新生成数据
   - 重启 OA 服务
   - 测试秘书系统功能
   - 测试文件操作功能

4. **清理**：
   - 确认迁移成功后，可以删除 ~/useful_scripts 目录
   - 保留 7 天观察期，确保无遗漏

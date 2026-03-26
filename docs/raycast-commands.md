# Raycast 命令规范

**版本**: 1.0
**创建时间**: 2026-03-02
**适用范围**: `~/useful_scripts/raycast/commands/` 下所有命令

---

## 一、命名规范

### 1.1 文件命名

**格式**: `{prefix}_{function}.sh`

**规则**:
- 使用下划线 `_` 分隔
- 全部小写
- 前缀必须有意义且统一

### 1.2 前缀定义

| 前缀 | 含义 | 适用范围 | 示例 |
|------|------|---------|------|
| `sec_` | Secretary（秘书系统） | 工作日志、报告、回顾、OA | `sec_log.sh` |
| `hy_` | Hydraulic（水利工具） | 纳污能力、地理编码、水库调度、水效评估 | `hy_capacity.sh` |
| `yb_` | Yabai（窗口管理） | 窗口浮动、鼠标跟随、布局切换 | `yb_float.sh` |
| `docx_` | Word 文档处理 | 文档转换、格式化 | `docx_to_md.sh` |
| `xlsx_` | Excel 数据处理 | 表格转换、合并、拆分 | `xlsx_merge.sh` |
| `csv_` | CSV 数据处理 | CSV 转换 | `csv_to_txt.sh` |
| `md_` | Markdown 处理 | Markdown 格式化、合并、拆分 | `md_formatter.sh` |
| `pptx_` | PowerPoint 处理 | PPT 格式化、转换 | `pptx_to_md.sh` |
| `file_` | 文件操作 | 文件复制、打印、运行 | `file_copy.sh` |
| `folder_` | 文件夹操作 | 文件夹创建、重命名 | `folder_create.sh` |
| `clashx_` | 网络代理 | ClashX 代理管理 | `clashx_status.sh` |
| `sys_` | 系统工具 | 系统级应用启动 | `sys_oa_dev.sh` |
| `display_` | 显示设置 | 分辨率调整 | `display_4k.sh` |
| `app_` | 应用启动 | 通用应用启动 | `app_open.sh` |
| `tts_` | 文本转语音 | 语音合成 | `tts_volcano.sh` |
| `dingtalk_` | 钉钉应用 | 钉钉相关应用启动 | `dingtalk_gov.sh` |

**重要**: 前缀必须准确反映功能领域，不能混用。

---

## 二、元数据规范

### 2.1 必需字段

所有命令**必须**包含以下元数据：

```bash
# @raycast.schemaVersion 1
# @raycast.title {标题}
# @raycast.mode {模式}
# @raycast.icon {图标}
# @raycast.packageName {包名}
# @raycast.description {描述}
```

### 2.2 标题规范（@raycast.title）

**中文命令**:
- 使用中文标题
- 简洁明了（2-6 字）
- 示例: `记录日志`、`查看报告`、`纳污能力计算`

**英文命令**:
- 使用 kebab-case
- 避免 snake_case（与文件名重复）
- 示例: `xlsx-lowercase`、`file-copy`

### 2.3 描述规范（@raycast.description）

**必需**: 所有命令都必须有描述

**中文描述**:
- 一句话说明功能（20-30 字）
- 示例: `记录工作、个人、投资、学习、生活等各类日志`

**英文描述**:
- 简洁明了（15-25 字）
- 示例: `Copy selected file's filename and content to clipboard`

### 2.4 图标规范（@raycast.icon）

**图标映射表**:

| 功能类别 | 推荐图标 | 适用前缀 |
|---------|---------|---------|
| 秘书系统 | 📝 📊 🏢 | sec_ |
| 水利工具 | 🌊 💧 📍 🏗️ | hy_ |
| 窗口管理 | 🪟 🖱️ | yb_ |
| Word 文档 | 📄 | docx_ |
| Markdown | 📝 ✂️ | md_ |
| PowerPoint | 📽️ | pptx_ |
| Excel | 📊 | xlsx_ |
| CSV | 📊 | csv_ |
| 文件操作 | 📋 🖨️ 🚀 | file_ |
| 文件夹 | 📁 📝 🗂️ | folder_ |
| 网络工具 | 🌐 ⚡ 🌍 📋 🔄 ⚙️ | clashx_ |
| 系统工具 | 🛠 🌊 | sys_ |
| 显示设置 | 🖥️ 📺 | display_ |
| 应用启动 | 🚀 💼 | app_ |
| 文本转语音 | 🔊 | tts_ |

### 2.5 模式规范（@raycast.mode）

| 模式 | 使用场景 |
|------|---------|
| `fullOutput` | 需要显示输出、用户交互、数据处理 |
| `silent` | 后台启动应用、无需输出 |
| `compact` | 特殊场景（不推荐，保留兼容） |

### 2.6 包名规范（@raycast.packageName）

**推荐分组**:

| PackageName | 包含前缀 | 说明 |
|-------------|---------|------|
| 秘书系统 | sec_ | 统一使用中文 |
| Hydraulic | hy_ | 水利工具 |
| Window Manager | yb_ | 窗口管理 |
| Document Processing | docx_, md_, pptx_ | 文档处理 |
| Data Processing | xlsx_, csv_ | 数据处理 |
| File Operations | file_, folder_ | 文件操作 |
| Network | clashx_ | 网络工具 |
| System | sys_, display_ | 系统工具 |
| Apps | app_ | 应用启动 |
| Dingtalk | dingtalk_ | 钉钉应用 |
| TTS | tts_ | 文本转语音 |

**规则**:
- 所有命令都必须有 PackageName
- 同类功能使用统一的 PackageName
- 避免过于宽泛的分组（如 `Scripts`）

---

## 三、修改操作规范

### 3.1 重命名命令

**必须执行的步骤**:

1. **搜索所有引用**
   ```bash
   grep -r "旧命令名" ~/useful_scripts/
   grep -r "旧命令名" ~/docs/
   grep -r "旧命令名" ~/.oa/
   ```

2. **生成修改清单**
   - 命令文件本身
   - 所有文档（README、报告、分析文档）
   - OA 系统配置（scripts.json）
   - 其他引用

3. **逐一修改**
   - 重命名文件
   - 更新元数据
   - 更新所有文档

4. **验证无遗漏**
   ```bash
   grep -r "旧命令名" ~/useful_scripts/
   grep -r "旧命令名" ~/docs/
   ```

### 3.2 添加新命令

**检查清单**:
- [ ] 文件名符合 `{prefix}_{function}.sh` 规范
- [ ] 前缀正确且有意义
- [ ] 包含所有必需元数据
- [ ] 标题符合规范（中文简洁或英文 kebab-case）
- [ ] 有完整的描述
- [ ] 图标符合映射表
- [ ] PackageName 正确
- [ ] 模式选择合适

### 3.3 批量修改

**使用 Agent Team**:
- 搜索 agent: 生成完整修改清单
- 执行 agent: 批量修改文件和元数据
- 验证 agent: 检查无遗漏

---

## 四、验证机制

### 4.1 自动验证脚本

位置: `~/useful_scripts/scripts/validate_raycast_commands.py`

功能:
- 检查所有命令文件名是否符合规范
- 检查所有必需元数据是否存在
- 检查前缀是否在定义列表中
- 检查标题、描述、图标、PackageName 是否符合规范
- 生成验证报告

### 4.2 定期检查

**时机**:
- 添加新命令后
- 重命名命令后
- 批量修改后
- 每月定期检查

---

## 五、常见错误

### 5.1 前缀错误

❌ 错误: `sec_water_efficiency.sh`（水利工具用了秘书系统前缀）
✅ 正确: `hy_water_efficiency.sh`（已修正）

### 5.2 元数据缺失

❌ 错误: 缺少 description 或 packageName
✅ 正确: 所有必需字段都存在

### 5.3 标题风格不统一

❌ 错误: 中英文混用，snake_case 和 kebab-case 混用
✅ 正确: 中文命令用中文标题，英文命令用 kebab-case

### 5.4 修改不完整

❌ 错误: 只改了文件名，没改元数据和文档
✅ 正确: 搜索所有引用，逐一修改，验证无遗漏

---

## 六、维护流程

1. **发现问题** → 使用 Grep 搜索所有引用
2. **制定方案** → 参考本规范，生成修改清单
3. **执行修改** → 逐一修改，使用 Agent Team 提高效率
4. **验证结果** → 运行验证脚本，再次搜索确认
5. **更新规范** → 如有新情况，更新本文档

---

**最后更新**: 2026-03-02
**维护者**: Claude + User

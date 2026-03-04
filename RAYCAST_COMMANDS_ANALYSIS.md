# Raycast Commands 完整分析

## 命令清单（共 55 个）

### 网络代理（7 个）- ClashX
- `clashx_enhanced.sh` - 增强代理管理
- `clashx_mode_direct.sh` - 直连模式
- `clashx_mode_global.sh` - 全局代理
- `clashx_mode_rule.sh` - 规则模式
- `clashx_proxy.sh` - 切换代理服务器
- `clashx_status.sh` - 查看代理状态
- **状态**：✅ 保留（网络代理管理）

### 数据转换（9 个）- CSV/XLSX
- `csv_from_txt.sh` - TXT → CSV
- `csv_merge_txt.sh` - 合并 TXT 到 CSV
- `csv_to_txt.sh` - CSV → TXT
- `xlsx_from_csv.sh` - CSV → XLSX
- `xlsx_from_txt.sh` - TXT → XLSX
- `xlsx_lowercase.sh` - Excel 转小写
- `xlsx_merge_tables.sh` - 合并 Excel 表
- `xlsx_splitsheets.sh` - 拆分 Excel 工作表
- `xlsx_to_csv.sh` - XLSX → CSV
- `xlsx_to_txt.sh` - XLSX → TXT
- **状态**：✅ 保留（数据处理核心功能）

### 文档处理（12 个）- DOCX/MD/PPTX
- `docx_apply_image_caption.sh` - 应用图片标题
- `docx_text_formatter.sh` - 文本格式化
- `docx_to_md.sh` - DOCX → MD
- `docx_zdwp_all.sh` - 水利公司文档处理
- `md_docx_template.sh` - MD → DOCX（模板）
- `md_formatter.sh` - MD 格式化
- `md_merge.sh` - 合并 MD
- `md_split_by_heading.sh` - 按标题拆分 MD
- `pptx_apply_all.sh` - 应用所有格式
- `pptx_font_yahei.sh` - 字体改为雅黑
- `pptx_table_style.sh` - 表格样式
- `pptx_text_formatter.sh` - 文本格式化
- `pptx_to_md.sh` - PPTX → MD
- **状态**：✅ 保留（文档处理核心功能）

### 文件操作（6 个）
- `file_copy.sh` - 复制文件
- `file_print.sh` - 打印文件
- `file_run.sh` - 运行文件
- `folder_add_prefix.sh` - 添加前缀
- `folder_create.sh` - 创建文件夹
- `folder_move_up_remove.sh` - 上移并删除
- `folder_paste.sh` - 粘贴到 Finder 当前目录
- **状态**：✅ 保留（文件管理核心功能）

### 水利工程（4 个）
- `hy_capacity.sh` - 纳污能力计算
- `hy_geocode.sh` - 地理编码
- `hy_reservoir.sh` - 水库发电调度
- `hy_water_efficiency.sh` - 水效评估
- **状态**：✅ 保留（专业工具）

### 系统工具（6 个）
- `display_1080.sh` - 切换 1080p 分辨率
- `display_4k.sh` - 切换 4K 分辨率
- `sys_app_launcher.sh` - 应用启动器
- `tts_volcano.sh` - 火山 TTS
- **状态**：✅ 保留（系统工具）

- `sys_oa_dev.sh` - 开发部 OA
- `sys_oa_zdwp.sh` - 水利公司 OA
- **状态**：❓ 待确认（是否已整合到 OA 总控？）

### 秘书系统（3 个）
- `sec_oa.sh` - 打开 OA
- `sec_report.sh` - 查看报告
- `sec_review.sh` - 每日回顾
- **状态**：
  - ✅ `sec_oa.sh` - 保留（需修正启动命令）
  - ❌ `sec_report.sh` - **删除**（功能已整合到 OA `/secretary`）
  - ❌ `sec_review.sh` - **删除**（功能已整合到 OA `/secretary`）

### 应用启动（2 个）
- `app_open.sh` - 在指定应用中打开文件夹
- `dingtalk_gov.sh` - 启动政务钉钉
- **状态**：
  - ✅ `app_open.sh` - 保留
  - ⚠️ `dingtalk_gov.sh` - **路径问题**（引用废弃路径 `execute/apps/`）

### 窗口管理（4 个）
- `yb_float.sh` - 浮动窗口
- `yb_mouse_follow.sh` - 鼠标跟随
- `yb_org.sh` - 窗口整理
- `yb_toggle.sh` - 切换窗口管理
- **状态**：❓ 待验证（是否正确调用 `scripts/window/`）

---

## 删除建议

### 🗑️ 确定删除（2 个）

#### 1. `sec_report.sh` - 查看报告
**理由**：
- 功能已整合到 OA 总控的 `/secretary` 页面
- 与 `sec_oa.sh` 功能重复（都是打开 OA 秘书页面）
- 维护冗余命令增加复杂度

#### 2. `sec_review.sh` - 每日回顾
**理由**：
- 功能已整合到 OA 总控的 `/secretary` 页面
- 与 `sec_oa.sh` 功能重复（都是打开 OA 秘书页面）
- 维护冗余命令增加复杂度

---

## 需要修复（2 个）

### ⚠️ 路径问题

#### 1. `dingtalk_gov.sh`
**问题**：引用废弃路径 `~/useful_scripts/execute/apps/dingtalk_gov.sh`
**修复方案**：
- 选项 A：迁移到 `scripts/system/dingtalk_gov.sh`
- 选项 B：如果不常用，直接删除

#### 2. `sec_oa.sh`
**问题**：启动命令错误（`pnpm dev:oa` 应改为 `pnpm dev`）
**修复方案**：修改第 52 行：`pnpm dev:oa` → `pnpm dev`

---

## 待确认（2 个）

### ❓ 功能重复？

#### 1. `sys_oa_dev.sh` - 开发部 OA
**问题**：是否已整合到 OA 总控？
**确认**：这个命令是否还需要？功能是什么？

#### 2. `sys_oa_zdwp.sh` - 水利公司 OA
**问题**：是否已整合到 OA 总控？
**确认**：这个命令是否还需要？功能是什么？

---

## 待验证（4 个）

### 🔍 窗口管理命令

需要验证 `yb_*.sh` 是否正确调用 `scripts/window/` 下的脚本：
- `yb_float.sh`
- `yb_mouse_follow.sh`
- `yb_org.sh`
- `yb_toggle.sh`

## 执行结果（2026-03-04）

### ✅ 已完成

#### 1. 删除冗余命令（4 个）
- ✅ `sec_report.sh` - 功能已整合到 OA
- ✅ `sec_review.sh` - 功能已整合到 OA
- ✅ `sys_oa_dev.sh` - 不再需要
- ✅ `sys_oa_zdwp.sh` - 不再需要

#### 2. 修复路径问题（2 个）
- ✅ `dingtalk_gov.sh` - 迁移到 `scripts/system/dingtalk_gov.sh`
- ✅ `sec_oa.sh` - 修正启动命令（`pnpm dev:oa` → `pnpm dev`）

#### 3. 删除对应脚本（2 个）
- ✅ `scripts/system/sys_oa_dev.sh`
- ✅ `scripts/system/sys_oa_zdwp.sh`

#### 4. 验证所有命令
- ✅ 运行 `validate_raycast_commands.py`
- ✅ 所有 51 个命令通过验证

### 📊 最终状态

| 类别 | 数量 | 说明 |
|------|------|------|
| ✅ 有效命令 | 51 | 所有命令通过验证 |
| 🗑️ 已删除 | 4 | 冗余和废弃命令 |
| ⚠️ 已修复 | 2 | 路径和启动命令 |

---



| 类别 | 数量 | 说明 |
|------|------|------|
| ✅ 保留 | 45 | 核心功能，正常使用 |
| 🗑️ 删除 | 2 | `sec_report.sh`, `sec_review.sh` |
| ⚠️ 修复 | 2 | `dingtalk_gov.sh`, `sec_oa.sh` |
| ❓ 待确认 | 2 | `sys_oa_dev.sh`, `sys_oa_zdwp.sh` |
| 🔍 待验证 | 4 | `yb_*.sh` 窗口管理命令 |

**建议操作顺序**：
1. 先确认 `sys_oa_*.sh` 是否需要
2. 删除确定不需要的命令
3. 修复路径问题
4. 验证窗口管理命令
5. 批量验证所有命令

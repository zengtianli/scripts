# useful_scripts/.assets 脚本分析报告

生成时间: 2026-02-05

## 一、目录结构说明

```
.assets/
├── core/      # 核心处理逻辑（CSV/DOCX/XLSX）
├── lib/       # 通用工具库
└── scripts/   # 功能脚本入口（Raycast 指向这里）
```

---

## 二、Core 目录（核心模块）

| 文件 | 作用 | 优先级 | 使用频率 | 状态 |
|------|------|--------|----------|------|
| csv_core.py | CSV 数据处理核心 | 高 | 中 | ✅ 保留 |
| docx_core.py | Word 文档处理核心 | 高 | 高 | ✅ 保留 |
| xlsx_core.py | Excel 处理核心 | 高 | 中 | ✅ 保留 |
| create_zdwp_template.py | 创建 ZDWP 模板 | 中 | 低 | ✅ 保留 |
| __init__.py | 包初始化 | - | - | ✅ 保留 |

---

## 三、Lib 目录（工具库）

| 文件 | 作用 | 优先级 | 使用频率 | 状态 |
|------|------|--------|----------|------|
| common.sh | Shell 通用函数 | 高 | 高 | ✅ 保留 |
| clashx.sh | ClashX 代理控制 | 中 | 中 | ✅ 保留 |
| common.py | Python 通用工具 | 高 | 高 | ✅ 保留 |
| clipboard.py | 剪贴板操作 | 中 | 中 | ✅ 保留 |
| constants.py | 全局常量配置 | 高 | 高 | ✅ 保留 |
| display.py | 终端 UI 显示 | 中 | 中 | ✅ 保留 |
| docx_utils.py | Word 格式化工具 | 高 | 高 | ✅ 保留 |
| file_utils.py | 文件操作工具 | 高 | 高 | ✅ 保留 |
| finder.py | 文件选择器 | 中 | 中 | ✅ 保留 |
| progress.py | 进度条显示 | 低 | 低 | ✅ 保留 |
| usage_log.py | 使用日志记录 | 低 | 低 | ⚠️ 需确认 |
| sync_dotfiles_config.yaml | dotfiles 同步配置8839 | 低 | 低 | ⚠️ 需确认 |
| asr/ | 语音识别相关 | 低 | 低 | ⚠️ 需确认 |

---

## 四、Scripts 目录（功能脚本）

### 4.1 重复文件（与 lib/ 重复，应删除）

| 文件 | 说明 | 状态 |
|------|------|------|
| clipboard.py | 与 lib/clipboard.py 重复 | ❌ 删除 |
| common.py | 与 lib/common.py 重复 | ❌ 删除 |
| constants.py | 与 lib/constants.py 重复 | ❌ 删除 |
| display.py | 与 lib/display.py 重复 | ❌ 删除 |
| docx_utils.py | 与 lib/docx_utils.py 重复 | ❌ 删除 |
| file_utils.py | 与 lib/file_utils.py 重复 | ❌ 删除 |
| finder.py | 与 lib/finder.py 重复 | ❌ 删除 |
| progress.py | 与 lib/progress.py 重复 | ❌ 删除 |
| usage_log.py | 与 lib/usage_log.py 重复 | ❌ 删除 |

### 4.2 临时文件（应删除）

| 文件 | 说明 | 状态 |
|------|------|------|
| merged.csv | 临时合并结果 | ❌ 删除 |
| merged.txt | 临时合并结果 | ❌ 删除 |
| merged.xlsx | 临时合并结果 | ❌ 删除 |
| merged_Sheet1.csv | 临时导出 | ❌ 删除 |
| merged_Sheet1.txt | 临时导出 | ❌ 删除 |

### 4.3 DOCX 脚本（Word 处理）

| 文件 | 作用 | 优先级 | 使用频率 | 状态 |
|------|------|--------|----------|------|
| docx_zdwp_all.py | ZDWP 一键格式化 | 高 | 高 | ✅ 保留（主力） |
| docx_apply_all_marks.py | 应用所有标记 | 高 | 高 | ✅ 保留 |
| docx_apply_heading_styles.py | 应用标题样式 | 中 | 中 | ✅ 保留 |
| docx_apply_paragraph_style.py | 应用段落样式 | 中 | 中 | ✅ 保留 |
| docx_apply_table_style.py | 应用表格样式 | 中 | 中 | ✅ 保留 |
| docx_apply_image_caption.py | 图片题注 | 中 | 低 | ✅ 保留 |
| docx_apply_header.py | 应用页眉 | 中 | 低 | ✅ 保留 |
| docx_apply_footer.py | 应用页脚 | 中 | 低 | ✅ 保留 |
| docx_apply_watermark.py | 应用水印 | 低 | 低 | ✅ 保留 |
| docx_format_numbers.py | 数字格式化 | 低 | 低 | ✅ 保留 |
| docx_text_formatter.py | 文本格式化 | 中 | 中 | ✅ 保留 |
| docx_style_extractor.py | 样式提取 | 低 | 低 | ⚠️ 需确认 |
| docx_fill_template.py | 模板填充 | 中 | 低 | ✅ 保留 |
| docx_case_template.py | 案例模板 | 低 | 低 | ⚠️ 需确认 |
| docx_to_quarto.py | 转 Quarto | 低 | 低 | ⚠️ 需确认 |
| docx_from_doc.sh | doc 转 docx | 中 | 低 | ✅ 保留 |
| docx_to_md.sh | docx 转 md | 中 | 中 | ✅ 保留 |
| docx_to_pdf.sh | docx 转 pdf | 中 | 中 | ✅ 保留 |

### 4.4 XLSX 脚本（Excel 处理）

| 文件 | 作用 | 优先级 | 使用频率 | 状态 |
|------|------|--------|----------|------|
| xlsx_to_csv.py | Excel 转 CSV | 高 | 高 | ✅ 保留 |
| xlsx_to_txt.py | Excel 转 TXT | 中 | 中 | ✅ 保留 |
| xlsx_from_csv.py | CSV 转 Excel | 中 | 中 | ✅ 保留 |
| xlsx_from_txt.py | TXT 转 Excel | 中 | 低 | ✅ 保留 |
| xlsx_splitsheets.py | 拆分工作表 | 中 | 中 | ✅ 保留 |
| xlsx_merge_tables.py | 合并表格 | 中 | 中 | ✅ 保留 |
| xlsx_field_mapper.py | 字段映射 | 低 | 低 | ⚠️ 需确认 |
| xlsx_lowercase.py | 转小写 | 低 | 低 | ⚠️ 需确认 |

### 4.5 CSV 脚本

| 文件 | 作用 | 优先级 | 使用频率 | 状态 |
|------|------|--------|----------|------|
| csv_to_txt.py | CSV 转 TXT | 中 | 中 | ✅ 保留 |
| csv_from_txt.py | TXT 转 CSV | 中 | 低 | ✅ 保留 |
| csv_merge_txt.py | 合并 TXT 到 CSV | 中 | 低 | ✅ 保留 |
| csv_reorder.py | 列重排序 | 低 | 低 | ⚠️ 需确认 |
| csv_format_circles.py | 圆形格式化 | 低 | 低 | ⚠️ 需确认（特定业务） |

### 4.6 MD 脚本（Markdown 处理）

| 文件 | 作用 | 优先级 | 使用频率 | 状态 |
|------|------|--------|----------|------|
| md_docx_template.py | MD 转 DOCX（带模板） | 高 | 高 | ✅ 保留（主力） |
| md_merge.py | 合并 MD 文件 | 中 | 中 | ✅ 保留 |
| md_formatter.py | MD 格式化 | 中 | 中 | ✅ 保留 |
| md_split_by_heading.py | 按标题拆分 | 中 | 低 | ✅ 保留 |
| md_to_docx.sh | MD 转 DOCX（简单） | 低 | 低 | ⚠️ 与 md_docx_template.py 重复 |
| md_to_qmd.py | MD 转 QMD | 低 | 低 | ⚠️ 需确认 |

### 4.7 PPTX 脚本

| 文件 | 作用 | 优先级 | 使用频率 | 状态 |
|------|------|--------|----------|------|
| pptx_apply_all.py | PPT 一键格式化 | 高 | 中 | ✅ 保留 |
| pptx_font_yahei.py | 字体改微软雅黑 | 中 | 中 | ✅ 保留 |
| pptx_table_style.py | 表格样式 | 中 | 低 | ✅ 保留 |
| pptx_text_formatter.py | 文本格式化 | 中 | 低 | ✅ 保留 |
| pptx_to_md.py | PPT 转 MD | 低 | 低 | ⚠️ 需确认 |

### 4.8 PDF 脚本

| 文件 | 作用 | 优先级 | 使用频率 | 状态 |
|------|------|--------|----------|------|
| pdf_from_images.sh | 图片合成 PDF | 中 | 低 | ✅ 保留 |
| pdf_to_md.sh | PDF 转 MD | 中 | 低 | ✅ 保留 |

### 4.9 Yabai 脚本（窗口管理）

| 文件 | 作用 | 优先级 | 使用频率 | 状态 |
|------|------|--------|----------|------|
| yabai_toggle.py | 开关 yabai | 高 | 高 | ✅ 保留 |
| yabai_float.py | 浮动窗口 | 高 | 高 | ✅ 保留 |
| yabai_next.py | 下一个窗口 | 中 | 中 | ✅ 保留 |
| yabai_prev.py | 上一个窗口 | 中 | 中 | ✅ 保留 |
| yabai_move.py | 移动窗口 | 中 | 中 | ✅ 保留 |
| yabai_space.py | 空间管理 | 中 | 中 | ✅ 保留 |
| yabai_org.py | 窗口整理 | 中 | 低 | ✅ 保留 |
| yabai_focus_follow.py | 焦点跟随 | 低 | 低 | ⚠️ 需确认 |
| yabai_mouse_follow.py | 鼠标跟随 | 低 | 低 | ⚠️ 需确认 |
| yabai_sp_cr.py | 特定操作 | 低 | 低 | ⚠️ 需确认 |
| yabai_sp_ds.py | 特定操作 | 低 | 低 | ⚠️ 需确认 |

### 4.10 ClashX 脚本（代理控制）

| 文件 | 作用 | 优先级 | 使用频率 | 状态 |
|------|------|--------|----------|------|
| clashx_enhanced.sh | 增强模式 | 中 | 中 | ✅ 保留 |
| clashx_mode_direct.sh | 直连模式 | 中 | 中 | ✅ 保留 |
| clashx_mode_global.sh | 全局模式 | 中 | 中 | ✅ 保留 |
| clashx_mode_rule.sh | 规则模式 | 中 | 中 | ✅ 保留 |
| clashx_proxy.sh | 代理开关 | 中 | 中 | ✅ 保留 |
| clashx_status.sh | 状态查看 | 低 | 低 | ⚠️ 可合并到其他脚本 |

### 4.11 文件/文件夹操作

| 文件 | 作用 | 优先级 | 使用频率 | 状态 |
|------|------|--------|----------|------|
| file_copy.py | 复制文件名/内容 | 高 | 高 | ✅ 保留 |
| file_run.py | 运行脚本 | 高 | 高 | ✅ 保留 |
| file.sh | 文件操作 | 中 | 低 | ⚠️ 需确认 |
| folder_create.py | 创建文件夹 | 中 | 中 | ✅ 保留 |
| folder_add_prefix.py | 添加前缀 | 中 | 低 | ✅ 保留 |
| folder_move_up_remove.py | 上移并删除 | 中 | 低 | ✅ 保留 |
| folder_paste.sh | 粘贴到文件夹 | 中 | 中 | ✅ 保留 |
| folder_paste_simple.sh | 简单粘贴 | 低 | 低 | ⚠️ 与 folder_paste.sh 重复 |

### 4.12 系统/工具脚本

| 文件 | 作用 | 优先级 | 使用频率 | 状态 |
|------|------|--------|----------|------|
| app_open.py | 打开应用 | 高 | 高 | ✅ 保留 |
| sys_app_launcher.py | 应用启动器 | 中 | 低 | ⚠️ 与 app_open.py 重复 |
| sys_terminate_python.sh | 终止 Python 进程 | 中 | 低 | ✅ 保留 |
| display_4k.sh | 切换 4K 分辨率 | 中 | 中 | ✅ 保留 |
| display_1080.sh | 切换 1080p | 中 | 中 | ✅ 保留 |
| backup.sh | 备份脚本 | 低 | 低 | ⚠️ 需确认 |
| restic.zsh | Restic 备份 | 低 | 低 | ⚠️ 需确认 |
| task.zsh | 任务管理 | 低 | 低 | ⚠️ 需确认 |
| cursor_init.sh | Cursor 初始化 | 低 | 低 | ⚠️ 需确认 |
| cursor_sync.sh | Cursor 同步 | 低 | 低 | ⚠️ 需确认 |

### 4.13 其他/特定业务

| 文件 | 作用 | 优先级 | 使用频率 | 状态 |
|------|------|--------|----------|------|
| common_utils.py | 通用工具（被 28 个脚本依赖） | 高 | 高 | ✅ 保留（核心） |
| gantt_timeline.py | 甘特图生成 | 中 | 中 | ✅ 保留 |
| quarto_init.py | Quarto 初始化 | 低 | 低 | ⚠️ 需确认 |
| build.py | 构建脚本 | 低 | 低 | ⚠️ 需确认 |
| extract_data.py | 数据提取 | 低 | 低 | ⚠️ 需确认 |
| render.sh | 渲染脚本 | 低 | 低 | ⚠️ 需确认 |
| doc.sh | 文档脚本 | 低 | 低 | ⚠️ 需确认 |
| data.sh | 数据脚本 | 低 | 低 | ⚠️ 需确认 |
| data.yml | 数据配置 | 低 | 低 | ⚠️ 需确认 |
| _quarto.yml | Quarto 配置 | 低 | 低 | ⚠️ 需确认 |

---

## 五、清理建议汇总

### 5.1 可直接删除（14 个文件）

```
# 重复的库文件（scripts/ 下）
scripts/clipboard.py
scripts/common.py
scripts/constants.py
scripts/display.py
scripts/docx_utils.py
scripts/file_utils.py
scripts/finder.py
scripts/progress.py
scripts/usage_log.py

# 临时文件
scripts/merged.csv
scripts/merged.txt
scripts/merged.xlsx
scripts/merged_Sheet1.csv
scripts/merged_Sheet1.txt
```

### 5.2 需确认是否删除（约 20 个）

- 低频使用的特定业务脚本
- 可能已过时的工具脚本
- 功能重复的脚本（如 md_to_docx.sh vs md_docx_template.py）

### 5.3 可合并的脚本

- ClashX 系列：6 个脚本可合并为 1 个带参数的脚本
- Yabai 系列：部分功能相近的可合并
- folder_paste.sh 和 folder_paste_simple.sh
- app_open.py 和 sys_app_launcher.py

---

## 六、统计

- 总文件数：约 120 个
- 建议删除：14 个（确定）+ 约 20 个（待确认）
- 预计清理后：约 85-90 个文件

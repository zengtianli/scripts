# Raycast 脚本使用分析报告

生成时间: 2026-02-06

## 使用日志统计

日志来源: `~/.useful_scripts_usage.log`（325 条记录）

---

## 一、ClashX（6 个脚本）

| 脚本 | 功能描述 | 调用次数 | 建议 |
|------|----------|----------|------|
| clashx_enhanced.sh | 切换 ClashX Pro 的增强模式 (TUN) | 70 | ✅ 保留（主力） |
| clashx_proxy.sh | 切换 ClashX Pro 的系统代理开关 | 4 | ❌ 可删（低频） |
| clashx_status.sh | 显示 ClashX Pro 的当前状态 | 3 | ❌ 可删（低频） |
| clashx_mode_global.sh | 将 ClashX Pro 设置为全局模式 | 3 | ❌ 可删（低频） |
| clashx_mode_rule.sh | 将 ClashX Pro 设置为规则模式 | 2 | ❌ 可删（低频） |
| clashx_mode_direct.sh | 将 ClashX Pro 设置为直连模式 | 0 | ❌ 删除（无使用） |

**分析**：enhanced 是主力，其他模式切换可在 ClashX 界面操作。

---

## 二、CSV（3 个脚本）

| 脚本 | 功能描述 | 调用次数 | 建议 |
|------|----------|----------|------|
| csv_to_txt.py | 将 CSV 文件转换为制表符分隔的 TXT 文件 | 0 | ⚠️ 需确认 |
| csv_from_txt.py | 将文本文件（TXT）转换为 CSV 格式 | 0 | ⚠️ 需确认 |
| csv_merge_txt.py | 将目录中所有 TXT 文件按列合并为单个 CSV 文件 | 0 | ⚠️ 需确认 |

**分析**：日志无记录，可能偶尔使用或通过其他方式处理。

---

## 三、DOCX（4 个脚本）

| 脚本 | 功能描述 | 调用次数 | 建议 |
|------|----------|----------|------|
| docx_zdwp_all.py | 为 Word 文档应用预设的 ZDWP 标准样式集 | 18 | ✅ 保留（主力） |
| docx_text_formatter.py | 格式化 Word 文档中的文本样式 | 19 | ✅ 保留（高频） |
| docx_to_md.sh | 使用 markitdown 将 Word 文档转换为 Markdown 格式 | 13 | ✅ 保留（高频） |
| docx_apply_image_caption.py | 为 Word 文档中的图片和图名应用统一样式 | 5 | ✅ 保留（中频） |

**分析**：已精简，全部保留。

---

## 四、File/Folder（6 个脚本）

| 脚本 | 功能描述 | 调用次数 | 建议 |
|------|----------|----------|------|
| file_copy.py | 将选中文件的文件名（及可选内容）复制到剪贴板 | 0 | ⚠️ 需确认 |
| file_run.py | 运行选中的 Shell 或 Python 脚本 | 0 | ⚠️ 需确认 |
| folder_create.py | 在当前 Finder 路径下创建新文件夹 | 0 | ⚠️ 需确认 |
| folder_add_prefix.py | 将父文件夹名称作为前缀添加到其内部的文件名中 | 0 | ⚠️ 需确认 |
| folder_move_up_remove.py | 将选中文件夹的内容移至上一级目录并删除原空文件夹 | 0 | ⚠️ 需确认 |
| folder_paste.sh | 将剪贴板内容粘贴到当前 Finder 窗口指向的文件夹中 | 0 | ⚠️ 需确认 |

**分析**：日志无记录，但这些是通用文件操作工具。

---

## 五、MD（4 个脚本）

| 脚本 | 功能描述 | 调用次数 | 建议 |
|------|----------|----------|------|
| md_docx_template.py | 基于模板将 Markdown 转换为带样式的 Docx 文档 | 23 | ✅ 保留（主力） |
| md_formatter.py | 格式化 Markdown 文件内容 | 3 | ✅ 保留 |
| md_merge.py | 将多个 Markdown 文件合并为一个 | 0 | ⚠️ 需确认 |
| md_split_by_heading.py | 按一级标题将 Markdown 文件拆分为多个小文件 | 0 | ⚠️ 需确认 |

---

## 六、PDF（2 个脚本）

| 脚本 | 功能描述 | 调用次数 | 建议 |
|------|----------|----------|------|
| pdf_from_images.sh | 使用 ImageMagick 将多张图片合并转换为 PDF | 0 | ⚠️ 需确认 |
| pdf_to_md.sh | 将 PDF 文档转换为 Markdown 文本格式 | 0 | ⚠️ 需确认 |

---

## 七、PPTX（5 个脚本）

| 脚本 | 功能描述 | 调用次数 | 建议 |
|------|----------|----------|------|
| pptx_font_yahei.py | 将 PPT 幻灯片的字体统一设置为微软雅黑 | 3 | ✅ 保留 |
| pptx_text_formatter.py | 格式化 PPT 中的文本内容 | 2 | ✅ 保留 |
| pptx_apply_all.py | 为 PPT 幻灯片应用预设的所有样式 | 0 | ⚠️ 需确认（可能是主力） |
| pptx_table_style.py | 为 PPT 中的表格应用统一样式 | 1 | ⚠️ 低频 |
| pptx_to_md.py | 将 PPT 演示文稿内容转换为 Markdown 格式 | 0 | ⚠️ 需确认 |

---

## 八、System（3 个脚本）

| 脚本 | 功能描述 | 调用次数 | 建议 |
|------|----------|----------|------|
| display_4k.sh | 将外部显示器分辨率设置为 4K | 0 | ⚠️ 需确认 |
| display_1080.sh | 将外部显示器分辨率设置为 1080p 以便演示 | 0 | ⚠️ 需确认 |
| sys_terminate_python.sh | 终止所有正在运行的 Python 进程 | 0 | ⚠️ 需确认 |

---

## 九、XLSX（7 个脚本）

| 脚本 | 功能描述 | 调用次数 | 建议 |
|------|----------|----------|------|
| xlsx_lowercase.py | 将 Excel 表格中的数据转换为小写 | 7 | ✅ 保留 |
| xlsx_to_csv.py | 将 Excel 工作表转换为 CSV 格式 | 0 | ⚠️ 需确认 |
| xlsx_from_csv.py | 将 CSV 文件转换为 Excel 电子表格 | 0 | ⚠️ 需确认 |
| xlsx_to_txt.py | 将 Excel 工作表转换为 TXT 文本格式 | 0 | ⚠️ 需确认 |
| xlsx_from_txt.py | 将 TXT 文本文件转换为 Excel 电子表格 | 0 | ⚠️ 需确认 |
| xlsx_splitsheets.py | 将 Excel 中的不同工作表拆分为独立文件 | 0 | ⚠️ 需确认 |
| xlsx_merge_tables.py | 合并多个 Excel 工作表或文件 | 0 | ⚠️ 需确认 |

---

## 十、Yabai（9 个脚本）

| 脚本 | 功能描述 | 调用次数 | 建议 |
|------|----------|----------|------|
| yabai_mouse_follow.py | 切换鼠标是否随窗口焦点移动 | 26 | ✅ 保留（高频） |
| yabai_org.py | 通过临时切换 bsp 模式自动整理当前桌面的窗口布局 | 11 | ✅ 保留（高频） |
| yabai_toggle.py | 启动或停止 Yabai 窗口管理服务 | 0 | ✅ 保留（核心开关） |
| yabai_float.py | 切换当前窗口的浮动/平铺状态 | 0 | ✅ 保留（常用） |
| yabai_next.py | 将焦点切换到下一个窗口 | 2 | ❌ 可删（低频，可用快捷键） |
| yabai_prev.py | 将焦点切换到上一个窗口 | 2 | ❌ 可删（低频，可用快捷键） |
| yabai_move.py | 将当前窗口移动到指定的虚拟桌面 | 0 | ❌ 可删（无使用） |
| yabai_space.py | 将焦点切换到指定的虚拟桌面 | 0 | ❌ 可删（无使用） |
| yabai_focus_follow.py | 切换窗口焦点是否随鼠标移动 | 0 | ❌ 可删（与 mouse_follow 功能相近） |

**分析**：toggle/float/org/mouse_follow 是核心，其他可通过快捷键或 yabai 命令实现。

---

## 建议删除清单

### 确定删除（10 个）

| 分类 | 脚本 | 原因 |
|------|------|------|
| ClashX | clashx_mode_direct.sh | 无使用 |
| ClashX | clashx_mode_global.sh | 低频(3)，界面可操作 |
| ClashX | clashx_mode_rule.sh | 低频(2)，界面可操作 |
| ClashX | clashx_proxy.sh | 低频(4)，界面可操作 |
| ClashX | clashx_status.sh | 低频(3)，界面可查看 |
| Yabai | yabai_next.py | 低频(2)，快捷键可替代 |
| Yabai | yabai_prev.py | 低频(2)，快捷键可替代 |
| Yabai | yabai_move.py | 无使用 |
| Yabai | yabai_space.py | 无使用 |
| Yabai | yabai_focus_follow.py | 与 mouse_follow 功能重复 |

### 待确认（约 20 个）

主要是日志中无记录但可能偶尔使用的转换工具：
- CSV 全部 3 个
- XLSX 除 lowercase 外 6 个
- PDF 2 个
- File/Folder 6 个
- System 3 个
- MD: md_merge, md_split_by_heading
- PPTX: pptx_apply_all, pptx_table_style, pptx_to_md

---

## 当前统计

| 类别 | 数量 |
|------|------|
| 总脚本数 | 53 |
| 确定删除 | 10 |
| 待确认 | ~20 |
| 确定保留 | ~23 |

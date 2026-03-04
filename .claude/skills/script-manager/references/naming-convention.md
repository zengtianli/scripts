# 脚本命名规范

## 前缀规则

### 文档处理（document）

| 前缀 | 用途 | 示例 |
|------|------|------|
| `docx_` | Word 文档处理 | `docx_text_formatter.py` |
| `md_` | Markdown 处理 | `md_to_html.py` |
| `pptx_` | PowerPoint 处理 | `pptx_image_extractor.py` |

### 数据转换（data）

| 前缀 | 用途 | 示例 |
|------|------|------|
| `xlsx_` | Excel 处理 | `xlsx_to_csv.py` |
| `csv_` | CSV 处理 | `csv_merge.py` |

### 文件操作（file）

| 前缀 | 用途 | 示例 |
|------|------|------|
| `file_` | 文件操作 | `file_rename_batch.py` |
| `folder_` | 文件夹操作 | `folder_sync.sh` |

### 系统工具（system）

| 前缀 | 用途 | 示例 |
|------|------|------|
| `sys_` | 系统操作 | `sys_cleanup.sh` |
| `display_` | 显示器相关 | `display_resolution.sh` |

### 网络代理（network）

| 前缀 | 用途 | 示例 |
|------|------|------|
| `clashx_` | ClashX 代理管理 | `clashx_enhanced.sh` |

### 窗口管理（window）

| 前缀 | 用途 | 示例 |
|------|------|------|
| `yabai_` | Yabai 窗口管理 | `yabai_focus_next.sh` |

### 杂项工具（tools）

无固定前缀，根据功能命名：
- `tts_volcano.py` - 语音合成
- `gantt_timeline.py` - 甘特图生成
- `quarto_init.py` - Quarto 初始化
- `app_open.py` - 应用打开

### 秘书系统（secretary）

| 前缀 | 用途 | 示例 |
|------|------|------|
| `sec_` | 秘书系统功能 | `sec_schedule.py` |

### 水利领域（hydraulic）

| 前缀 | 用途 | 示例 |
|------|------|------|
| `hy_` | 水利专业工具 | `hy_capacity.py` |

## 命名格式

### 功能脚本

**格式**：`{prefix}_{功能描述}.{py|sh}`

**规则**：
- 使用下划线分隔
- 功能描述使用小写英文
- 描述要简洁明确

**示例**：
- ✅ `docx_text_formatter.py`
- ✅ `xlsx_to_csv.py`
- ✅ `file_rename_batch.py`
- ❌ `docxTextFormatter.py`（不使用驼峰）
- ❌ `docx-text-formatter.py`（不使用连字符）

### Raycast Wrapper

**格式**：`{prefix}-{功能描述}.sh`

**规则**：
- 使用连字符分隔
- 功能描述使用小写英文
- 与功能脚本名称对应

**示例**：
- ✅ `docx-text-formatter.sh` → 调用 `docx_text_formatter.py`
- ✅ `xlsx-to-csv.sh` → 调用 `xlsx_to_csv.py`
- ✅ `file-rename-batch.sh` → 调用 `file_rename_batch.py`

## 特殊情况

### 无前缀脚本（tools 类别）

当脚本功能不属于任何特定类别时，可以不使用前缀：

**示例**：
- `app_open.py` - 应用打开工具
- `tts_volcano.py` - 语音合成
- `gantt_timeline.py` - 甘特图生成

### 多功能脚本

如果脚本处理多种文件类型，使用主要功能的前缀：

**示例**：
- `docx_to_pdf.py` - 主要功能是处理 Word 文档，使用 `docx_` 前缀
- `xlsx_format_all.py` - 主要功能是处理 Excel，使用 `xlsx_` 前缀

## 版本管理

### 脚本版本

不在文件名中包含版本号，使用 git 管理版本：

- ✅ `docx_text_formatter.py`
- ❌ `docx_text_formatter_v2.py`

### 废弃脚本

将废弃的脚本移至 `raycast/commands/_archived/`：

```bash
mv raycast/commands/old-script.sh raycast/commands/_archived/
```

## 检查清单

创建新脚本时，确保：

- [ ] 功能脚本使用正确的前缀
- [ ] 功能脚本使用下划线分隔
- [ ] Raycast wrapper 使用连字符分隔
- [ ] 名称简洁明确，描述功能
- [ ] 文件扩展名正确（.py 或 .sh）
- [ ] 脚本有执行权限（chmod +x）

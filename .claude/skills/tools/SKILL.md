---
name: dev-tools
description: 开发部工具命令速查。文档读取、格式修复、文件转换、数据处理。当需要使用脚本工具时触发。
---

# 工具命令速查

> 📍 脚本库路径：`/Users/tianli/useful_scripts/execute/`
> 📍 Python：`/Users/tianli/miniforge3/bin/python3`

## 文档读取

| 需求 | 命令 |
|------|------|
| 读取 Word | `python execute/tools/read_docx.py <file.docx>` |
| 读取 Excel | `python execute/tools/read_xlsx.py <file.xlsx>` |
| 分析 Excel | `python execute/tools/analyze_xlsx.py <file>` |

## 格式修复

| 需求 | 命令 |
|------|------|
| Word 一键格式化 | `python execute/scripts/docx/docx_apply_zdwp_all.py <file>` |
| Word 文本格式 | `python execute/scripts/docx/docx_text_formatter.py <file>` |
| Word 数字字体 | `python execute/scripts/docx/docx_format_numbers_font.py <file>` |
| Word 表格样式 | `python execute/scripts/docx/docx_apply_table_style.py <file>` |

## 文件转换

| 需求 | 命令 |
|------|------|
| Word → Markdown | `bash execute/scripts/docx/docx_to_md.sh <file>` |
| Word → PDF | `bash execute/scripts/docx/docx_to_pdf.sh <file>` |
| Doc → Docx | `bash execute/scripts/docx/docx_from_doc.sh <file>` |

## 数据处理

| 需求 | 命令 |
|------|------|
| Excel 筛选 | `python execute/tools/filter_xlsx.py <file> -f "条件"` |
| 字数统计 | `python execute/tools/count_chars.py <file.md>` |
| Markdown 分割 | `python execute/tools/split_md.py <file.md>` |

## 比较工具

| 需求 | 命令 |
|------|------|
| 文件对比 | `python execute/compare/compare_files_folders.py <a> <b>` |
| Excel 对比 | `python execute/compare/compare_excel_data.py <a.xlsx> <b.xlsx>` |

## 质量检测

| 需求 | 命令 |
|------|------|
| 假大空检测 | `python execute/tools/fake_empty_detector.py <file.md>` |

## 水利专用工具

| 需求 | 命令 |
|------|------|
| 企业行业查询 | `python 水利专用/企业查询/company_industry_query.py` |
| 地址转坐标 | `python 水利专用/地理编码工具/geocode_by_address.py` |
| 企业坐标查询 | `python 水利专用/地理编码工具/search_by_company.py` |

## 使用注意

1. **Python 绝对路径**：`/Users/tianli/miniforge3/bin/python3`
2. **脚本库路径**：`/Users/tianli/useful_scripts/execute/`
3. **路径含空格**：用引号包裹
4. **检查文件存在**：执行前确认文件路径

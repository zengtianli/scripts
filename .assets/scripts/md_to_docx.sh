#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title md-to-docx
# @raycast.mode fullOutput
# @raycast.icon 📝
# @raycast.packageName Markdown
# @raycast.description Markdown转DOCX（使用pandoc）- 支持多选

source "$(dirname "$0")/_lib/common.sh"
log_script_usage "markdown/to_docx" "md"

# ===== 检查依赖 =====
if ! command -v pandoc &> /dev/null; then
    show_error "必须安装 pandoc (brew install pandoc)"
    exit 1
fi

# ===== 获取Finder选中的文件（支持多选）=====
SELECTED_FILES=$(get_finder_selection_multiple)

if [ -z "$SELECTED_FILES" ]; then
    show_error "没有在 Finder 中选择任何文件"
    exit 1
fi

# ===== 转换单个文件 =====
convert_md_to_docx() {
    local file="$1"
    local output_file="${file%.md}.docx"
    
    if pandoc "$file" -o "$output_file" 2>/dev/null; then
        return 0
    fi
    
    [ -f "$output_file" ] && rm -f "$output_file"
    return 1
}

# ===== 统计变量 =====
success_count=0
fail_count=0
skip_count=0
total_count=0

# ===== 处理每个文件 =====
while IFS= read -r SELECTED_FILE; do
    [ -z "$SELECTED_FILE" ] && continue
    
    ((total_count++))
    
    if ! check_file_extension "$SELECTED_FILE" "md"; then
        show_warning "跳过非 MD 文件: $(basename "$SELECTED_FILE")"
        ((skip_count++))
        continue
    fi
    
    if [ ! -f "$SELECTED_FILE" ]; then
        show_error "文件不存在: $(basename "$SELECTED_FILE")"
        ((fail_count++))
        continue
    fi
    
    docx_file="${SELECTED_FILE%.md}.docx"
    if [ -f "$docx_file" ]; then
        show_warning "输出文件已存在，跳过: $(basename "$docx_file")"
        ((skip_count++))
        continue
    fi
    
    show_processing "转换: $(basename "$SELECTED_FILE")"
    
    if convert_md_to_docx "$SELECTED_FILE"; then
        show_success "已转换: $(basename "$SELECTED_FILE") -> $(basename "$docx_file")"
        ((success_count++))
    else
        show_error "转换失败: $(basename "$SELECTED_FILE")"
        ((fail_count++))
    fi
    
    echo ""
done <<< "$SELECTED_FILES"

# ===== 显示统计信息 =====
echo "========================================"
echo "📊 处理完成统计"
echo "========================================"
echo "✅ 成功: $success_count 个文件"
[ $fail_count -gt 0 ] && echo "❌ 失败: $fail_count 个文件"
[ $skip_count -gt 0 ] && echo "⏭️  跳过: $skip_count 个文件"
echo "📁 总计: $total_count 个文件"

[ $fail_count -gt 0 ] && exit 1
exit 0






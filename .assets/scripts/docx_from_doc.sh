#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title doc-to-docx
# @raycast.mode fullOutput
# @raycast.icon 📄
# @raycast.packageName DOCX
# @raycast.description DOC转DOCX（使用Microsoft Word）- 支持多选

source "$(dirname "$0")/_lib/common.sh"
log_script_usage "docx/from_doc" "docx"

# ===== 检查依赖 =====
if [ ! -d "/Applications/Microsoft Word.app" ]; then
    show_error "Microsoft Word 未安装"
    exit 1
fi

# ===== 获取Finder选中的文件（支持多选）=====
SELECTED_FILES=$(get_finder_selection_multiple)

if [ -z "$SELECTED_FILES" ]; then
    show_error "没有在 Finder 中选择任何文件"
    exit 1
fi

# ===== 转换单个文件 =====
convert_doc_to_docx() {
    local file="$1"
    local full_path
    full_path=$(cd "$(dirname "$file")" && pwd)/$(basename "$file")
    local docx_file="${file%.*}.docx"
    local docx_full_path
    docx_full_path=$(cd "$(dirname "$file")" && pwd)/$(basename "$docx_file")

    local script_content="
tell application \"Microsoft Word\"
    activate
    open POSIX file \"$full_path\"
    save as active document file name \"${docx_full_path}\" file format format document
    close active window saving no
end tell
"
    
    if osascript -e "$script_content" >/dev/null 2>&1; then
        return 0
    else
        [ -f "$docx_file" ] && rm -f "$docx_file"
        return 1
    fi
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
    
    # 检查文件类型
    if ! check_file_extension "$SELECTED_FILE" "doc"; then
        show_warning "跳过非 DOC 文件: $(basename "$SELECTED_FILE")"
        ((skip_count++))
        continue
    fi
    
    if [ ! -f "$SELECTED_FILE" ]; then
        show_error "文件不存在: $(basename "$SELECTED_FILE")"
        ((fail_count++))
        continue
    fi
    
    # 检查输出文件是否已存在
    docx_file="${SELECTED_FILE%.*}.docx"
    if [ -f "$docx_file" ]; then
        show_warning "输出文件已存在，跳过: $(basename "$docx_file")"
        ((skip_count++))
        continue
    fi
    
    show_processing "转换: $(basename "$SELECTED_FILE")"
    
    if convert_doc_to_docx "$SELECTED_FILE"; then
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

#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title docx-to-pdf
# @raycast.mode fullOutput
# @raycast.icon 📄
# @raycast.packageName DOCX
# @raycast.description DOCX转PDF（优先使用Microsoft Word）- 支持多选

source "$(dirname "$0")/_lib/common.sh"
log_script_usage "docx/to_pdf" "docx"

# ===== 检查依赖 =====
HAS_WORD=false
HAS_SOFFICE=false
HAS_PANDOC=false

if [ -d "/Applications/Microsoft Word.app" ]; then
    HAS_WORD=true
fi

if command -v soffice &> /dev/null; then
    HAS_SOFFICE=true
fi

if command -v pandoc &> /dev/null; then
    HAS_PANDOC=true
fi

if [ "$HAS_WORD" = false ] && [ "$HAS_SOFFICE" = false ] && [ "$HAS_PANDOC" = false ]; then
    show_error "必须安装 Microsoft Word、LibreOffice (soffice) 或 pandoc"
    exit 1
fi

# 显示将使用的转换工具
if [ "$HAS_WORD" = true ]; then
    show_info "使用 Microsoft Word 进行转换"
elif [ "$HAS_SOFFICE" = true ]; then
    show_info "使用 LibreOffice 进行转换"
else
    show_info "使用 Pandoc 进行转换"
fi

# ===== 获取Finder选中的文件（支持多选）=====
SELECTED_FILES=$(get_finder_selection_multiple)

if [ -z "$SELECTED_FILES" ]; then
    show_error "没有在 Finder 中选择任何文件"
    exit 1
fi

# ===== 使用 Microsoft Word 转换 =====
convert_with_word() {
    local file="$1"
    local full_path
    full_path=$(cd "$(dirname "$file")" && pwd)/$(basename "$file")
    local pdf_file="${file%.docx}.pdf"
    local pdf_full_path
    pdf_full_path=$(cd "$(dirname "$file")" && pwd)/$(basename "$pdf_file")

    local script_content="
tell application \"Microsoft Word\"
    activate
    open POSIX file \"$full_path\"
    save as active document file name \"${pdf_full_path}\" file format format PDF
    close active window saving no
end tell
"
    
    if osascript -e "$script_content" >/dev/null 2>&1; then
        return 0
    else
        [ -f "$pdf_file" ] && rm -f "$pdf_file"
        return 1
    fi
}

# ===== 使用 LibreOffice 转换 =====
convert_with_soffice() {
    local file="$1"
    local outdir
    outdir=$(dirname "$file")
    
    if soffice --headless --convert-to pdf --outdir "$outdir" "$file" >/dev/null 2>&1; then
        return 0
    fi
    return 1
}

# ===== 使用 Pandoc 转换 =====
convert_with_pandoc() {
    local file="$1"
    local output_file="${file%.docx}.pdf"
    
    if pandoc "$file" -o "$output_file" >/dev/null 2>&1; then
        return 0
    fi
    return 1
}

# ===== 转换单个文件（按优先级尝试）=====
convert_docx_to_pdf() {
    local file="$1"
    
    # 优先使用 Microsoft Word
    if [ "$HAS_WORD" = true ]; then
        if convert_with_word "$file"; then
            return 0
        fi
    fi
    
    # 尝试 LibreOffice
    if [ "$HAS_SOFFICE" = true ]; then
        if convert_with_soffice "$file"; then
            return 0
        fi
    fi
    
    # 尝试 Pandoc
    if [ "$HAS_PANDOC" = true ]; then
        if convert_with_pandoc "$file"; then
            return 0
        fi
    fi
    
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
    
    if ! check_file_extension "$SELECTED_FILE" "docx"; then
        show_warning "跳过非 DOCX 文件: $(basename "$SELECTED_FILE")"
        ((skip_count++))
        continue
    fi
    
    if [ ! -f "$SELECTED_FILE" ]; then
        show_error "文件不存在: $(basename "$SELECTED_FILE")"
        ((fail_count++))
        continue
    fi
    
    pdf_file="${SELECTED_FILE%.docx}.pdf"
    if [ -f "$pdf_file" ]; then
        show_warning "输出文件已存在，跳过: $(basename "$pdf_file")"
        ((skip_count++))
        continue
    fi
    
    show_processing "转换: $(basename "$SELECTED_FILE")"
    
    if convert_docx_to_pdf "$SELECTED_FILE"; then
        show_success "已转换: $(basename "$SELECTED_FILE") -> $(basename "$pdf_file")"
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

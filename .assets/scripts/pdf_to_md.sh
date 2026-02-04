#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title pdf-to-md
# @raycast.mode fullOutput
# @raycast.icon 📕
# @raycast.packageName PDF
# @raycast.description 将PDF转换为Markdown

source "$(dirname "$0")/_lib/common.sh"
log_script_usage "pdf/to_md" "pdf"

SELECTED_FILE=$(get_finder_selection_single)

if [ -z "$SELECTED_FILE" ]; then
    show_error "没有在 Finder 中选择任何文件"
    exit 1
fi

if ! check_file_extension "$SELECTED_FILE" "pdf"; then
    show_error "请选择 PDF (.pdf) 文件"
    exit 1
fi

FILE_DIR=$(dirname "$SELECTED_FILE")
safe_cd "$FILE_DIR" || exit 1

show_processing "正在转换: $(basename "$SELECTED_FILE")"

# 使用 markitdown 转换
check_command_exists "markitdown" || exit 1

OUTPUT_FILE="${SELECTED_FILE%.pdf}.md"
if markitdown "$SELECTED_FILE" > "$OUTPUT_FILE" 2>/dev/null; then
    show_success "转换完成: $(basename "$OUTPUT_FILE")"
else
    show_error "转换失败"
    exit 1
fi

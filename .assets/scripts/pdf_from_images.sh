#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title pdf-from-images
# @raycast.mode fullOutput
# @raycast.icon 🖼️
# @raycast.packageName PDF
# @raycast.description 图片合并转 PDF（ImageMagick）

source "$(dirname "${BASH_SOURCE[0]}")/../lib/common.sh"

readonly SCRIPT_VERSION="1.0.0"
readonly SCRIPT_AUTHOR="tianli"
readonly SCRIPT_UPDATED="2024-07-25"

show_version() {
    show_version_template
}

show_help() {
    show_help_header "$0" "图片转PDF工具 - 使用 ImageMagick 转换"
    echo "    $0 [选项] [目录] [输出文件.pdf]"
    echo "    -r, --recursive  递归处理子目录中的图片"
    show_help_footer
    echo "依赖: ImageMagick (magick 命令)"
}

check_dependencies() {
    show_info "检查依赖项..."
    if ! check_command_exists "magick"; then
        show_error "ImageMagick (magick) 命令未找到. 请先安装."
        return 1
    fi
    show_success "依赖检查完成"
}

main() {
    local recursive=false
    local target_dir="."
    local output_file=""
    
    # 解析参数
    local params=()
    while (( "$#" )); do
        case "$1" in
            -r|--recursive)
                recursive=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            --version)
                show_version
                exit 0
                ;;
            -*)
                show_error "未知选项: $1"
                show_help
                exit 1
                ;;
            *)
                params+=("$1")
                shift
                ;;
        esac
    done
    
    # 设置目录和输出文件
    if [ ${#params[@]} -gt 0 ]; then target_dir="${params[0]}"; fi
    if [ ${#params[@]} -gt 1 ]; then output_file="${params[1]}"; fi
    
    if [ ! -d "$target_dir" ]; then
        fatal_error "目标目录不存在: $target_dir"
    fi
    
    # 设置默认输出文件名
    if [ -z "$output_file" ]; then
        output_file="${target_dir%/}_converted.pdf"
    fi
    
    # 检查输出文件扩展名
    if [[ "${output_file##*.}" != "pdf" ]]; then
        output_file+=".pdf"
    fi
    
    check_dependencies || exit 1
    
    show_info "开始转换..."
    show_info "目标目录: $target_dir"
    show_info "输出文件: $output_file"
    [ "$recursive" = true ] && show_info "递归模式: 已启用"
    
    local image_files=()
    local find_cmd="find '$target_dir' -maxdepth 1"
    [ "$recursive" = true ] && find_cmd="find '$target_dir'"
    
    # 查找图片文件
    while IFS= read -r -d '' file; do
        image_files+=("$file")
    done < <(eval "$find_cmd -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.gif' -o -iname '*.bmp' -o -iname '*.tiff' \) -print0" 2>/dev/null | sort -z)
    
    if [ ${#image_files[@]} -eq 0 ]; then
        show_warning "在 $target_dir 中未找到任何图片文件。"
        exit 0
    fi
    
    show_info "找到 ${#image_files[@]} 个图片文件，正在合并为 PDF..."
    
    if magick "${image_files[@]}" "$output_file"; then
        show_success "PDF已生成：$output_file"
    else
        show_error "生成PDF失败"
        [ -f "$output_file" ] && rm -f "$output_file"
        exit 1
    fi
}

main "$@" 
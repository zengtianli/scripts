#!/bin/bash
# ============================================================
# 脚本功能描述
#
# 用途：简要说明脚本的主要功能
# 使用：通过 Raycast 调用或直接运行
# ============================================================

# ============================================================
# 引用公共库
# ============================================================
source "$(dirname "$0")/../../lib/common.sh"

# ============================================================
# 配置变量
# ============================================================
readonly SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ============================================================
# 工具函数
# ============================================================

# 显示使用说明
show_usage() {
    cat <<EOF
用法: $SCRIPT_NAME [选项] [参数]

选项:
    -h, --help      显示此帮助信息
    -v, --verbose   详细输出模式
    -f, --file      指定文件路径

示例:
    $SCRIPT_NAME -f /path/to/file
    $SCRIPT_NAME --verbose
EOF
}

# 验证文件
validate_file() {
    local file="$1"
    local expected_ext="$2"

    if [ ! -f "$file" ]; then
        show_error "文件不存在: $file"
        return 1
    fi

    if [ -n "$expected_ext" ]; then
        if ! check_file_extension "$file" "$expected_ext"; then
            show_error "文件扩展名错误: 期望 $expected_ext"
            return 1
        fi
    fi

    return 0
}

# ============================================================
# 主要功能函数
# ============================================================

process_file() {
    local file="$1"

    show_processing "正在处理: $(basename "$file")"

    # TODO: 实现具体的处理逻辑

    # 示例：读取文件内容
    # local content=$(cat "$file")

    # 示例：处理内容
    # local processed=$(echo "$content" | tr '[:lower:]' '[:upper:]')

    # 示例：写入结果
    # local output="${file%.txt}_processed.txt"
    # echo "$processed" > "$output"

    show_success "处理完成"
    return 0
}

# ============================================================
# 主函数
# ============================================================

main() {
    local file_path=""
    local verbose=false

    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -v|--verbose)
                verbose=true
                shift
                ;;
            -f|--file)
                file_path="$2"
                shift 2
                ;;
            *)
                show_error "未知选项: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    # 如果没有指定文件，从 Finder 获取
    if [ -z "$file_path" ]; then
        file_path=$(get_finder_selection_single)
        if [ -z "$file_path" ]; then
            show_error "未选中文件"
            exit 1
        fi
    fi

    # 验证文件
    # if ! validate_file "$file_path" "txt"; then
    #     exit 1
    # fi

    # 处理文件
    if process_file "$file_path"; then
        exit 0
    else
        exit 1
    fi
}

# ============================================================
# 脚本入口
# ============================================================
main "$@"

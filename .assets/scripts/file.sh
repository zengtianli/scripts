#!/bin/bash
# ============================================================
# 脚本名称: file.sh
# 功能描述: 文件管理工具（比较、整理、清理）
# 来源工单: CLI工具聚合
# 工单路径: ~/cursor-shared/work/tasks/xxx/CLI工具聚合.md
# 创建日期: 2025-12-17
# 作者: 开发部
# ============================================================
# 使用说明: bash file.sh [命令] [参数]
#           bash file.sh --help  # 查看完整帮助
# ============================================================

set -euo pipefail
IFS=$'\n\t'

# ============================================================
# 加载模块
# ============================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "$SCRIPT_DIR/_lib/colors.sh"
source "$SCRIPT_DIR/_lib/ui.sh"
source "$SCRIPT_DIR/_lib/tui.sh"
source "$SCRIPT_DIR/file/config.sh"
source "$SCRIPT_DIR/file/compare.sh"
source "$SCRIPT_DIR/file/organize.sh"
source "$SCRIPT_DIR/file/manage.sh"

# ============================================================
# 帮助信息
# ============================================================
usage() {
    banner "📁 文件管理工具 - file.sh"
    
    section "命令" "⌨️"
    item "${GREEN}compare${RST}  " "比较文件/目录"
    item "${GREEN}organize${RST} " "按类型整理文件"
    item "${GREEN}rename${RST}   " "批量重命名"
    item "${GREEN}clean${RST}    " "清理空目录"
    item "${GREEN}manage${RST}   " "交互式管理面板（默认）"
    section_end
    
    section "compare 用法" "🔍"
    item "" "${DIM}file.sh compare <路径1> <路径2>${RST}"
    item "" "${DIM}file.sh compare dir1/ dir2/${RST}       # 比较目录"
    item "" "${DIM}file.sh compare f1.txt f2.txt${RST}     # 比较文件"
    item "" "${DIM}file.sh compare f1 f2 -m${RST}          # 监控模式"
    item "" "${DIM}file.sh compare f1 f2 -m 10${RST}       # 每10秒检查"
    section_end
    
    section "organize 用法" "📁"
    item "" "${DIM}file.sh organize <目录>${RST}"
    item "" "${DIM}file.sh organize ~/Downloads${RST}      # 整理下载目录"
    section_end
    
    section "rename 用法" "✏️"
    item "" "${DIM}file.sh rename <目录> --prefix <前缀>${RST}"
    item "" "${DIM}file.sh rename ./photos --prefix 2024_${RST}"
    section_end
    
    section "clean 用法" "🗑️"
    item "" "${DIM}file.sh clean <目录> [--dry-run]${RST}"
    item "" "${DIM}file.sh clean ./project${RST}           # 删除空目录"
    item "" "${DIM}file.sh clean ./project --dry-run${RST} # 仅预览"
    section_end
    
    section "选项" "🎛️"
    item "${YELLOW}-h, --help${RST}     " "显示帮助信息"
    item "${YELLOW}-m, --monitor${RST}  " "监控模式（持续比较）"
    item "${YELLOW}--prefix${RST}       " "文件名前缀"
    item "${YELLOW}--dry-run${RST}      " "模拟运行（不实际操作）"
    section_end
    
    echo
    exit 0
}

# ============================================================
# 命令处理
# ============================================================

cmd_compare() {
    local path1=""
    local path2=""
    local monitor=false
    local interval=$DEFAULT_MONITOR_INTERVAL
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -m|--monitor)
                monitor=true
                # 检查下一个参数是否是数字（间隔时间）
                if [[ $# -gt 1 ]] && [[ "$2" =~ ^[0-9]+$ ]]; then
                    interval="$2"
                    shift
                fi
                shift
                ;;
            -*)
                log_error "未知选项: $1"
                exit 1
                ;;
            *)
                if [[ -z "$path1" ]]; then
                    path1="$1"
                elif [[ -z "$path2" ]]; then
                    path2="$1"
                fi
                shift
                ;;
        esac
    done
    
    if [[ -z "$path1" ]] || [[ -z "$path2" ]]; then
        log_error "请指定两个要比较的路径"
        echo
        log_info "用法: file.sh compare <路径1> <路径2> [-m]"
        exit 1
    fi
    
    banner "📁 文件管理工具 - file.sh"
    do_file_compare "$path1" "$path2" "$monitor" "$interval"
    echo
}

cmd_organize() {
    local dir="${1:-}"
    
    if [[ -z "$dir" ]]; then
        log_error "请指定要整理的目录"
        echo
        log_info "用法: file.sh organize <目录>"
        exit 1
    fi
    
    banner "📁 文件管理工具 - file.sh"
    do_file_organize "$dir"
    echo
}

cmd_rename() {
    local dir=""
    local prefix=""
    local suffix=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --prefix)
                prefix="$2"
                shift 2
                ;;
            --suffix)
                suffix="$2"
                shift 2
                ;;
            -*)
                log_error "未知选项: $1"
                exit 1
                ;;
            *)
                dir="$1"
                shift
                ;;
        esac
    done
    
    if [[ -z "$dir" ]]; then
        log_error "请指定目录"
        echo
        log_info "用法: file.sh rename <目录> --prefix <前缀>"
        exit 1
    fi
    
    if [[ -z "$prefix" ]] && [[ -z "$suffix" ]]; then
        log_error "请指定 --prefix 或 --suffix"
        exit 1
    fi
    
    banner "📁 文件管理工具 - file.sh"
    do_file_rename "$dir" "$prefix" "$suffix"
    echo
}

cmd_clean() {
    local dir=""
    local dry_run=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run|-d)
                dry_run=true
                shift
                ;;
            -*)
                log_error "未知选项: $1"
                exit 1
                ;;
            *)
                dir="$1"
                shift
                ;;
        esac
    done
    
    if [[ -z "$dir" ]]; then
        log_error "请指定要清理的目录"
        echo
        log_info "用法: file.sh clean <目录> [--dry-run]"
        exit 1
    fi
    
    banner "📁 文件管理工具 - file.sh"
    do_file_clean "$dir" "$dry_run"
    echo
}

# ============================================================
# 主函数
# ============================================================
main() {
    # 无参数时进入交互模式
    if [[ $# -eq 0 ]]; then
        cmd_file_manage
        exit 0
    fi
    
    # 解析第一个参数
    case $1 in
        -h|--help)
            usage
            ;;
        compare)
            shift
            cmd_compare "$@"
            ;;
        organize)
            shift
            cmd_organize "$@"
            ;;
        rename)
            shift
            cmd_rename "$@"
            ;;
        clean)
            shift
            cmd_clean "$@"
            ;;
        manage)
            shift
            cmd_file_manage
            ;;
        *)
            # 如果第一个参数是路径，默认进入交互模式
            if [[ -e "$1" ]]; then
                log_info "提示: 使用 'file.sh compare $1 <路径2>' 进行比较"
                log_info "      使用 'file.sh organize $1' 整理文件"
                echo
                cmd_file_manage
            else
                log_error "未知命令: $1"
                echo
                log_info "使用 ${CYAN}--help${RST} 查看帮助"
                exit 1
            fi
            ;;
    esac
}

main "$@"
exit 0


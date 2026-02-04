#!/bin/bash
# ============================================================
# 脚本名称: data.sh
# 功能描述: 数据处理工具（Excel/CSV 转换、比较、合并）
# 来源工单: CLI工具聚合
# 工单路径: ~/cursor-shared/work/tasks/xxx/CLI工具聚合.md
# 创建日期: 2025-12-17
# 作者: 开发部
# ============================================================
# 使用说明: bash data.sh [命令] [参数]
#           bash data.sh --help  # 查看完整帮助
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
source "$SCRIPT_DIR/data/config.sh"
source "$SCRIPT_DIR/data/convert.sh"
source "$SCRIPT_DIR/data/compare.sh"
source "$SCRIPT_DIR/data/manage.sh"

# ============================================================
# 帮助信息
# ============================================================
usage() {
    banner "📊 数据处理工具 - data.sh"
    
    section "命令" "⌨️"
    item "${GREEN}convert${RST} " "格式转换（xlsx ↔ csv/txt）"
    item "${GREEN}read${RST}    " "读取 Excel 内容"
    item "${GREEN}compare${RST} " "比较两个表格"
    item "${GREEN}merge${RST}   " "合并多个表格"
    item "${GREEN}split${RST}   " "拆分工作表"
    item "${GREEN}manage${RST}  " "交互式管理面板（默认，先选文件再选操作）"
    section_end
    
    section "manage 用法" "📁"
    item "" "${DIM}data.sh${RST}                    # 扫描当前目录"
    item "" "${DIM}data.sh manage ~/Downloads${RST} # 扫描指定目录"
    item "" "${DIM}j/k${RST} 移动  ${DIM}Enter${RST} 操作  ${DIM}b${RST} 批量  ${DIM}d${RST} 比较  ${DIM}c${RST} 切换目录  ${DIM}q${RST} 退出"
    section_end
    
    section "convert 用法" "🔄"
    item "" "${DIM}data.sh convert <文件> -t <格式>${RST}"
    item "" "${DIM}data.sh convert data.xlsx -t csv${RST}   # Excel→CSV"
    item "" "${DIM}data.sh convert data.xlsx -t txt${RST}   # Excel→TXT"
    item "" "${DIM}data.sh convert data.csv -t xlsx${RST}   # CSV→Excel"
    section_end
    
    section "read 用法" "👁️"
    item "" "${DIM}data.sh read <文件> [输出文件]${RST}"
    item "" "${DIM}data.sh read data.xlsx${RST}           # 输出到终端"
    item "" "${DIM}data.sh read data.xlsx out.txt${RST}   # 保存到文件"
    section_end
    
    section "compare 用法" "🔍"
    item "" "${DIM}data.sh compare <文件1> <文件2> [容差]${RST}"
    item "" "${DIM}data.sh compare v1.xlsx v2.xlsx${RST}       # 默认容差"
    item "" "${DIM}data.sh compare v1.xlsx v2.xlsx 0.001${RST}  # 自定义容差"
    section_end
    
    section "merge 用法" "🔗"
    item "" "${DIM}data.sh merge <文件1> <文件2> ... [-o 输出文件]${RST}"
    item "" "${DIM}data.sh merge a.xlsx b.xlsx -o merged.xlsx${RST}"
    section_end
    
    section "支持格式" "📁"
    kv "Excel:" "xlsx, xls"
    kv "文本:" "csv, txt"
    section_end
    
    section "选项" "🎛️"
    item "${YELLOW}-h, --help${RST}    " "显示帮助信息"
    item "${YELLOW}-t, --to${RST}      " "目标格式"
    item "${YELLOW}-o, --output${RST}  " "输出文件"
    section_end
    
    echo
    exit 0
}

# ============================================================
# 命令处理
# ============================================================

cmd_convert() {
    local file=""
    local target=""
    local sheet=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -t|--to)
                target="$2"
                shift 2
                ;;
            -s|--sheet)
                sheet="$2"
                shift 2
                ;;
            -*)
                log_error "未知选项: $1"
                exit 1
                ;;
            *)
                file="$1"
                shift
                ;;
        esac
    done
    
    if [[ -z "$file" ]]; then
        log_error "请指定输入文件"
        echo
        log_info "用法: data.sh convert <文件> -t <格式>"
        exit 1
    fi
    
    if [[ -z "$target" ]]; then
        log_error "请指定目标格式"
        echo
        log_info "用法: data.sh convert <文件> -t <格式>"
        log_info "支持: csv, txt, xlsx"
        exit 1
    fi
    
    banner "📊 数据处理工具 - data.sh"
    do_data_convert "$file" "$target" "$sheet"
    echo
}

cmd_read() {
    local file="$1"
    local output="${2:-}"
    
    if [[ -z "$file" ]]; then
        log_error "请指定输入文件"
        echo
        log_info "用法: data.sh read <文件> [输出文件]"
        exit 1
    fi
    
    banner "📊 数据处理工具 - data.sh"
    do_data_read "$file" "$output"
    echo
}

cmd_compare() {
    local file1="${1:-}"
    local file2="${2:-}"
    local tolerance="${3:-0.00001}"
    
    if [[ -z "$file1" ]] || [[ -z "$file2" ]]; then
        log_error "请指定两个要比较的文件"
        echo
        log_info "用法: data.sh compare <文件1> <文件2> [容差]"
        exit 1
    fi
    
    banner "📊 数据处理工具 - data.sh"
    do_data_compare "$file1" "$file2" "$tolerance"
    echo
}

cmd_merge() {
    local output="merged.xlsx"
    local files=()
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -o|--output)
                output="$2"
                shift 2
                ;;
            -*)
                log_error "未知选项: $1"
                exit 1
                ;;
            *)
                files+=("$1")
                shift
                ;;
        esac
    done
    
    if [[ ${#files[@]} -lt 2 ]]; then
        log_error "至少需要 2 个文件进行合并"
        echo
        log_info "用法: data.sh merge <文件1> <文件2> ... [-o 输出文件]"
        exit 1
    fi
    
    banner "📊 数据处理工具 - data.sh"
    do_data_merge "$output" "${files[@]}"
    echo
}

cmd_split() {
    local file="${1:-}"
    
    if [[ -z "$file" ]]; then
        log_error "请指定要拆分的文件"
        echo
        log_info "用法: data.sh split <文件>"
        exit 1
    fi
    
    banner "📊 数据处理工具 - data.sh"
    do_data_split "$file"
    echo
}

# ============================================================
# 主函数
# ============================================================
main() {
    # 无参数时进入交互模式（当前目录）
    if [[ $# -eq 0 ]]; then
        cmd_manage "$(pwd)"
        exit 0
    fi
    
    # 解析第一个参数
    case $1 in
        -h|--help)
            usage
            ;;
        convert)
            shift
            cmd_convert "$@"
            ;;
        read)
            shift
            cmd_read "$@"
            ;;
        compare)
            shift
            cmd_compare "$@"
            ;;
        merge)
            shift
            cmd_merge "$@"
            ;;
        split)
            shift
            cmd_split "$@"
            ;;
        manage)
            shift
            cmd_manage "$@"
            ;;
        *)
            # 如果第一个参数是文件，默认进入交互模式
            if [[ -f "$1" ]]; then
                log_info "提示: 使用 'data.sh convert $1 -t <格式>' 进行转换"
                log_info "      使用 'data.sh read $1' 读取内容"
                echo
                cmd_manage "$(pwd)"
            elif [[ -d "$1" ]]; then
                # 如果是目录，以该目录进入交互模式
                cmd_manage "$1"
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


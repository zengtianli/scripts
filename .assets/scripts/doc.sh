#!/bin/bash
# ============================================================
# 脚本名称: doc.sh
# 功能描述: 文档处理工具（转换、读取、格式化）
# 来源工单: CLI工具聚合
# 工单路径: ~/cursor-shared/work/tasks/xxx/CLI工具聚合.md
# 创建日期: 2025-12-17
# 作者: 开发部
# ============================================================
# 使用说明: bash doc.sh [命令] [参数]
#           bash doc.sh --help  # 查看完整帮助
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
source "$SCRIPT_DIR/doc/config.sh"
source "$SCRIPT_DIR/doc/convert.sh"
source "$SCRIPT_DIR/doc/format.sh"
source "$SCRIPT_DIR/doc/manage.sh"

# ============================================================
# 帮助信息
# ============================================================
usage() {
    banner "📄 文档处理工具 - doc.sh"
    
    section "命令" "⌨️"
    item "${GREEN}convert${RST} " "格式转换（docx/pdf/pptx ↔ md ↔ docx/pdf）"
    item "${GREEN}read${RST}    " "读取文档内容"
    item "${GREEN}format${RST}  " "格式化文档（ZDWP 标准）"
    item "${GREEN}manage${RST}  " "交互式管理面板（默认，先选文件再选操作）"
    section_end
    
    section "manage 用法" "📁"
    item "" "${DIM}doc.sh${RST}                    # 扫描当前目录"
    item "" "${DIM}doc.sh manage ~/Downloads${RST} # 扫描指定目录"
    item "" "${DIM}j/k${RST} 移动  ${DIM}Enter${RST} 操作  ${DIM}b${RST} 批量  ${DIM}c${RST} 切换目录  ${DIM}r${RST} 刷新  ${DIM}q${RST} 退出"
    section_end
    
    section "convert 用法" "🔄"
    item "" "${DIM}doc.sh convert <文件> -t <格式>${RST}"
    item "" "${DIM}doc.sh convert doc.docx -t md${RST}   # DOCX→MD"
    item "" "${DIM}doc.sh convert doc.md -t docx${RST}   # MD→DOCX"
    item "" "${DIM}doc.sh convert doc.docx -t pdf${RST}  # DOCX→PDF"
    section_end
    
    section "read 用法" "👁️"
    item "" "${DIM}doc.sh read <文件> [输出文件]${RST}"
    item "" "${DIM}doc.sh read doc.docx${RST}          # 输出到终端"
    item "" "${DIM}doc.sh read doc.docx out.txt${RST}  # 保存到文件"
    section_end
    
    section "format 用法" "✨"
    item "" "${DIM}doc.sh format <文件> [模式]${RST}"
    item "" "${DIM}doc.sh format doc.docx${RST}        # ZDWP完整格式化"
    item "" "${DIM}doc.sh format doc.docx --fix${RST}  # 仅文本修复"
    item "" "${DIM}doc.sh format doc.md --fix${RST}    # MD文本修复"
    section_end
    
    section "支持格式" "📁"
    kv "输入:" "docx, pdf, pptx, md"
    kv "输出:" "md, docx, pdf"
    section_end
    
    section "选项" "🎛️"
    item "${YELLOW}-h, --help${RST}    " "显示帮助信息"
    item "${YELLOW}-t, --to${RST}      " "目标格式"
    item "${YELLOW}--fix${RST}         " "仅文本修复"
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
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -t|--to)
                target="$2"
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
        log_info "用法: doc.sh convert <文件> -t <格式>"
        exit 1
    fi
    
    if [[ -z "$target" ]]; then
        log_error "请指定目标格式"
        echo
        log_info "用法: doc.sh convert <文件> -t <格式>"
        log_info "支持: md, docx, pdf"
        exit 1
    fi
    
    banner "📄 文档处理工具 - doc.sh"
    do_convert "$file" "$target"
    echo
}

cmd_read() {
    local file="$1"
    local output="${2:-}"
    
    if [[ -z "$file" ]]; then
        log_error "请指定输入文件"
        echo
        log_info "用法: doc.sh read <文件> [输出文件]"
        exit 1
    fi
    
    banner "📄 文档处理工具 - doc.sh"
    do_read "$file" "$output"
    echo
}

cmd_format() {
    local file=""
    local mode="zdwp"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --fix|--text)
                mode="fix"
                shift
                ;;
            --zdwp|--all)
                mode="zdwp"
                shift
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
        log_info "用法: doc.sh format <文件> [--fix]"
        exit 1
    fi
    
    banner "📄 文档处理工具 - doc.sh"
    do_format "$file" "$mode"
    echo
}

# ============================================================
# 主函数
# ============================================================
main() {
    local cmd="manage"
    
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
        format)
            shift
            cmd_format "$@"
            ;;
        manage)
            shift
            cmd_manage "$@"
            ;;
        *)
            # 如果第一个参数是文件，默认执行 manage
            if [[ -f "$1" ]]; then
                log_info "提示: 使用 'doc.sh convert $1 -t <格式>' 进行转换"
                log_info "      使用 'doc.sh read $1' 读取内容"
                log_info "      使用 'doc.sh format $1' 格式化"
                echo
                cmd_manage
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


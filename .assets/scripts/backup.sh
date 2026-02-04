#!/bin/bash
# ============================================================
# 脚本名称: backup.sh
# 功能描述: 一人集团 Restic 增量备份脚本
# 来源工单: 无（存量脚本标准化）
# 创建日期: 2025-12-15
# 作者: 开发部
# ============================================================
# 使用说明: bash backup.sh [命令] [选项]
#           bash backup.sh --help  # 查看完整帮助
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
source "$SCRIPT_DIR/backup/config.sh"
source "$SCRIPT_DIR/backup/dept.sh"
source "$SCRIPT_DIR/backup/manage.sh"

# ============================================================
# 帮助信息
# ============================================================
usage() {
    banner "🗄️  一人集团 Restic 备份工具"
    
    section "命令" "⌨️"
    item "${GREEN}backup${RST}   " "执行备份（默认）"
    item "${GREEN}manage${RST}   " "交互式管理面板"
    item "${GREEN}init${RST}     " "初始化仓库"
    section_end
    
    section "manage 功能" "💡"
    item "${DIM}j/k${RST}      " "移动光标"
    item "${DIM}空格${RST}     " "选中快照"
    item "${DIM}回车${RST}     " "查看详情"
    item "${DIM}d${RST}        " "删除快照"
    item "${DIM}p${RST}        " "对比快照（选 2 个）"
    item "${DIM}r${RST}        " "恢复快照"
    section_end
    
    section "选项" "🎛️"
    item "${YELLOW}-h, --help${RST}    " "显示帮助信息"
    item "${YELLOW}-v, --verbose${RST} " "详细输出"
    item "${YELLOW}-d, --dry-run${RST} " "模拟运行"
    section_end
    
    section "示例" "📝"
    item "" "${DIM}backup.sh${RST}           ${DIM}# 执行备份${RST}"
    item "" "${DIM}backup.sh manage${RST}    ${DIM}# 打开管理面板${RST}"
    section_end
    
    section "备份目录" "📁"
    for dir in "${BACKUP_DIRS[@]}"; do
        local emoji=$(get_dept_emoji "$dir")
        local name=$(get_dept_name "$dir")
        item "$emoji" "$name (${dir/$HOME/~})"
    done
    section_end
    
    section "仓库" "🗃️"
    kv "位置:" "${RESTIC_REPO/$HOME/~}"
    section_end
    
    echo
    exit 0
}

# ============================================================
# 工具函数
# ============================================================
check_restic() {
    if ! command -v restic &> /dev/null; then
        log_error "restic 未安装"
        log_info "请运行: ${CYAN}brew install restic${RST}"
        exit 1
    fi
}

check_repo() {
    if [[ ! -d "$RESTIC_REPO" ]]; then
        log_error "仓库不存在: ${RESTIC_REPO/$HOME/~}"
        log_info "请先运行: ${CYAN}$(basename "$0") init${RST}"
        exit 1
    fi
}

# ============================================================
# 核心功能
# ============================================================
cmd_init() {
    banner "🗄️  一人集团 Restic 备份工具"
    log_step "初始化 Restic 仓库"
    
    if [[ -d "$RESTIC_REPO" ]]; then
        log_warn "仓库已存在: ${RESTIC_REPO/$HOME/~}"
        return 0
    fi
    
    mkdir -p "$(dirname "$RESTIC_REPO")"
    restic -r "$RESTIC_REPO" init
    
    echo
    log_ok "仓库初始化完成"
}

cmd_backup() {
    local dry_run="${1:-false}"
    local verbose="${2:-false}"
    
    banner "🗄️  一人集团 Restic 备份工具"
    
    # 检查目录
    section "备份目录" "📁"
    local valid_dirs=()
    for dir in "${BACKUP_DIRS[@]}"; do
        if [[ -d "$dir" ]]; then
            valid_dirs+=("$dir")
            item "$(icon_ok)" "${dir/$HOME/~}"
        else
            item "$(icon_warn)" "${DIM}${dir/$HOME/~} (不存在)${RST}"
        fi
    done
    section_end
    
    if [[ ${#valid_dirs[@]} -eq 0 ]]; then
        log_error "没有有效的备份目录"
        exit 1
    fi
    
    # 构建命令
    local -a cmd_args=(-r "$RESTIC_REPO" backup)
    cmd_args+=("${valid_dirs[@]}")
    for pattern in "${EXCLUDE_PATTERNS[@]}"; do
        cmd_args+=("--exclude=$pattern")
    done
    [[ "$verbose" == true ]] && cmd_args+=(--verbose)
    [[ "$dry_run" == true ]] && cmd_args+=(--dry-run)
    
    # 执行
    echo
    if [[ "$dry_run" == true ]]; then
        log_step "模拟备份 (dry-run)"
    else
        log_step "正在备份..."
    fi
    echo
    
    # 捕获输出并解析
    local output
    output=$(restic "${cmd_args[@]}" 2>&1) || true
    
    # 解析结果 (macOS 兼容)
    local files_new files_changed files_unchanged
    local added_size snapshot_id
    
    files_new=$(echo "$output" | sed -n 's/.*Files:[[:space:]]*\([0-9]*\) new.*/\1/p' | head -1)
    files_changed=$(echo "$output" | sed -n 's/.*Files:.*[[:space:]]\([0-9]*\) changed.*/\1/p' | head -1)
    files_unchanged=$(echo "$output" | sed -n 's/.*Files:.*[[:space:]]\([0-9]*\) unmodified.*/\1/p' | head -1)
    added_size=$(echo "$output" | sed -n 's/.*Added to the repository:[[:space:]]*\([^(]*\).*/\1/p' | head -1 | xargs)
    snapshot_id=$(echo "$output" | sed -n 's/.*snapshot \([a-f0-9]*\) saved.*/\1/p' | head -1)
    
    : "${files_new:=0}"
    : "${files_changed:=0}"
    : "${files_unchanged:=0}"
    : "${added_size:=-}"
    : "${snapshot_id:=-}"
    
    # 显示结果
    section "备份结果" "📊"
    kv "新增文件:" "$files_new" "📄"
    kv "修改文件:" "$files_changed" "📝"
    kv "未变文件:" "$files_unchanged" "📋"
    kv "数据增量:" "${added_size:-0}" "💾"
    [[ "$snapshot_id" != "-" ]] && kv "快照 ID:" "$snapshot_id" "🔖"
    section_end
    
    echo
    if [[ "$dry_run" == true ]]; then
        log_ok "模拟完成 (未实际写入)"
    else
        log_ok "备份完成！"
    fi
    echo
}

# ============================================================
# 主函数
# ============================================================
main() {
    check_restic
    
    local cmd="backup"
    local verbose=false
    local dry_run=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                usage
                ;;
            -v|--verbose)
                verbose=true
                shift
                ;;
            -d|--dry-run)
                dry_run=true
                shift
                ;;
            backup|init|manage)
                cmd="$1"
                shift
                ;;
            *)
                log_error "未知参数: $1"
                echo
                log_info "使用 ${CYAN}--help${RST} 查看完整帮助"
                echo
                usage
                ;;
        esac
    done
    
    case $cmd in
        init)      cmd_init ;;
        backup)    check_repo; cmd_backup "$dry_run" "$verbose" ;;
        manage)    check_repo; cmd_manage ;;
    esac
}

main "$@"
exit 0

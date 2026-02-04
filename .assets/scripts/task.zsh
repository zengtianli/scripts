#!/bin/zsh
# ============================================================
# task - 一人公司工单管理系统
# 来源工单: 20251215-task-system
# 总控路径: ~/cursor-shared/work/tasks/
# ============================================================

set -e

# 配置
TASKS_DIR="$HOME/cursor-shared/work/tasks"
REPORTS_DIR="$HOME/cursor-shared/work/reports"
TEMPLATE="$TASKS_DIR/_template.md"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# 状态列表
ALL_STATUSES=(backlog active review done cancelled)

# 状态图标
typeset -A STATUS_ICONS
STATUS_ICONS=(
    backlog "📋"
    active "🚀"
    review "🔍"
    done "✅"
    cancelled "❌"
)

# ============================================================
# 辅助函数
# ============================================================

print_help() {
    cat << EOF
${CYAN}task${NC} - 一人公司工单管理系统

${YELLOW}用法:${NC}
    task <命令> [参数]

${YELLOW}命令:${NC}
    ${GREEN}new${NC} <名称>              创建新工单
    ${GREEN}list${NC} [状态]             列出工单 (默认显示活跃)
    ${GREEN}show${NC} <工单>             显示工单详情
    ${GREEN}move${NC} <工单> <状态>      移动工单状态
    ${GREEN}daily${NC}                   生成每日报告
    ${GREEN}dashboard${NC}               显示仪表盘
    ${GREEN}find${NC} <关键词>           搜索工单

${YELLOW}状态:${NC}
    backlog   📋 待办池
    active    🚀 进行中
    review    🔍 待验收
    done      ✅ 已完成
    cancelled ❌ 已取消

${YELLOW}示例:${NC}
    task new "优化登录流程"
    task list active
    task move 20251215-login active
    task daily

EOF
}

get_today() {
    date "+%Y%m%d"
}

get_today_display() {
    date "+%Y-%m-%d"
}

get_month() {
    date "+%Y-%m"
}

# 查找工单文件
find_task() {
    local task_id="$1"
    local st dir
    for st in $ALL_STATUSES; do
        dir="$TASKS_DIR/$st"
        if [[ -f "$dir/$task_id.md" ]]; then
            echo "$dir/$task_id.md"
            return 0
        fi
    done
    # 也搜索 done 的子目录
    local found=$(find "$TASKS_DIR/done" -name "$task_id.md" 2>/dev/null | head -1)
    if [[ -n "$found" ]]; then
        echo "$found"
        return 0
    fi
    return 1
}

# 获取工单当前状态
get_task_status() {
    local task_id="$1"
    local st dir
    for st in $ALL_STATUSES; do
        dir="$TASKS_DIR/$st"
        if [[ -f "$dir/$task_id.md" ]]; then
            echo "$st"
            return 0
        fi
    done
    # 也搜索 done 的子目录
    if find "$TASKS_DIR/done" -name "$task_id.md" 2>/dev/null | grep -q .; then
        echo "done"
        return 0
    fi
    return 1
}

# 统计目录中的工单数
count_tasks() {
    local dir="$1"
    if [[ -d "$dir" ]]; then
        find "$dir" -maxdepth 1 -name "*.md" ! -name "_*" 2>/dev/null | wc -l | tr -d ' '
    else
        echo "0"
    fi
}

# 检查目录是否有 md 文件
has_md_files() {
    local dir="$1"
    local count=$(count_tasks "$dir")
    [[ "$count" -gt 0 ]]
}

# ============================================================
# 主要功能
# ============================================================

# 创建新工单
cmd_new() {
    local name="$1"
    if [[ -z "$name" ]]; then
        echo -e "${RED}错误: 请提供工单名称${NC}"
        echo "用法: task new <名称>"
        exit 1
    fi
    
    # 生成工单ID
    local task_id="$(get_today)-$(echo "$name" | tr ' ' '-' | tr '[:upper:]' '[:lower:]')"
    local task_file="$TASKS_DIR/backlog/$task_id.md"
    
    # 检查是否已存在
    if [[ -f "$task_file" ]]; then
        echo -e "${RED}错误: 工单已存在: $task_id${NC}"
        exit 1
    fi
    
    # 从模板创建
    if [[ -f "$TEMPLATE" ]]; then
        sed -e "s/\[任务标题\]/$name/" \
            -e "s/YYYYMMDD-xxx/$task_id/" \
            -e "s/YYYY-MM-DD/$(get_today_display)/" \
            -e "s/📋 backlog | 🚀 active | 🔍 review | ✅ done | ❌ cancelled/📋 backlog/" \
            "$TEMPLATE" > "$task_file"
    else
        cat > "$task_file" << EOF
# $name

> 状态: 📋 backlog

## 基本信息

| 项目 | 内容 |
|------|------|
| 工单编号 | $task_id |
| 创建日期 | $(get_today_display) |
| 发起人 | 用户 |
| 优先级 | 🟡 中 |

## 需求背景

...

## 验收标准

- [ ] ...

## 执行记录

| 日期 | 部门 | 操作 | 结果 |
|------|------|------|------|
| $(get_today_display) | 总控 | 创建工单 | ✅ |
EOF
    fi
    
    echo -e "${GREEN}✅ 工单已创建:${NC} $task_id"
    echo -e "   路径: $task_file"
    echo -e "   状态: 📋 backlog"
    echo ""
    echo -e "${CYAN}下一步:${NC}"
    echo "   编辑工单: code $task_file"
    echo "   开始处理: task move $task_id active"
}

# 列出工单
cmd_list() {
    local filter_status="$1"
    
    echo -e "${CYAN}📋 工单列表${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    local statuses=(backlog active review)
    if [[ -n "$filter_status" ]]; then
        statuses=("$filter_status")
    fi
    
    local s
    for s in $statuses; do
        local dir="$TASKS_DIR/$s"
        local icon="${STATUS_ICONS[$s]}"
        local count=$(count_tasks "$dir")
        
        if [[ "$count" -gt 0 ]]; then
            echo -e "\n${YELLOW}$icon ${(C)s} ($count)${NC}"
            for file in "$dir"/*.md(N); do
                [[ -f "$file" ]] || continue
                [[ "$(basename "$file")" == _* ]] && continue
                
                local task_id=$(basename "$file" .md)
                local title=$(head -1 "$file" | sed 's/^# //')
                echo -e "   ${GREEN}$task_id${NC}"
                echo -e "      $title"
            done
        fi
    done
    
    echo ""
}

# 显示工单详情
cmd_show() {
    local task_id="$1"
    if [[ -z "$task_id" ]]; then
        echo -e "${RED}错误: 请提供工单ID${NC}"
        exit 1
    fi
    
    local task_file=$(find_task "$task_id")
    if [[ -z "$task_file" ]]; then
        echo -e "${RED}错误: 找不到工单: $task_id${NC}"
        exit 1
    fi
    
    cat "$task_file"
}

# 移动工单状态
cmd_move() {
    local task_id="$1"
    local new_status="$2"
    
    if [[ -z "$task_id" || -z "$new_status" ]]; then
        echo -e "${RED}错误: 请提供工单ID和目标状态${NC}"
        echo "用法: task move <工单ID> <状态>"
        exit 1
    fi
    
    # 验证状态
    if [[ ! " ${ALL_STATUSES[*]} " =~ " $new_status " ]]; then
        echo -e "${RED}错误: 无效状态: $new_status${NC}"
        echo "有效状态: backlog, active, review, done, cancelled"
        exit 1
    fi
    
    # 查找工单
    local task_file=$(find_task "$task_id")
    if [[ -z "$task_file" ]]; then
        echo -e "${RED}错误: 找不到工单: $task_id${NC}"
        exit 1
    fi
    
    local old_status=$(get_task_status "$task_id")
    local target_dir="$TASKS_DIR/$new_status"
    
    # done 状态按月归档
    if [[ "$new_status" == "done" ]]; then
        target_dir="$TASKS_DIR/done/$(get_month)"
        mkdir -p "$target_dir"
    fi
    
    # 更新工单内文件的状态行
    local new_icon="${STATUS_ICONS[$new_status]}"
    sed -i '' "s/> 状态: .*/> 状态: $new_icon $new_status/" "$task_file"
    
    # 移动文件
    mv "$task_file" "$target_dir/"
    
    echo -e "${GREEN}✅ 工单状态已更新${NC}"
    echo -e "   工单: $task_id"
    echo -e "   ${STATUS_ICONS[$old_status]} $old_status → ${STATUS_ICONS[$new_status]} $new_status"
}

# 生成仪表盘
cmd_dashboard() {
    echo -e "${CYAN}"
    cat << 'EOF'
╔══════════════════════════════════════════════════════════╗
║           🏢 一人公司工单仪表盘                          ║
╚══════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    
    local backlog=$(count_tasks "$TASKS_DIR/backlog")
    local active=$(count_tasks "$TASKS_DIR/active")
    local review=$(count_tasks "$TASKS_DIR/review")
    local done_total=$(find "$TASKS_DIR/done" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
    
    echo -e "${YELLOW}状态概览${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    printf "  📋 待办池      %3d\n" "$backlog"
    printf "  🚀 进行中      %3d\n" "$active"
    printf "  🔍 待验收      %3d\n" "$review"
    printf "  ✅ 已完成      %3d\n" "$done_total"
    echo ""
    
    # 显示进行中的工单
    if [[ "$active" -gt 0 ]]; then
        echo -e "${YELLOW}🚀 进行中${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        for file in "$TASKS_DIR/active"/*.md(N); do
            [[ -f "$file" ]] || continue
            local task_id=$(basename "$file" .md)
            local title=$(head -1 "$file" | sed 's/^# //')
            echo -e "  ${GREEN}$task_id${NC}"
            echo "    $title"
        done
        echo ""
    fi
    
    # 显示待验收的工单
    if [[ "$review" -gt 0 ]]; then
        echo -e "${YELLOW}🔍 待验收${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        for file in "$TASKS_DIR/review"/*.md(N); do
            [[ -f "$file" ]] || continue
            local task_id=$(basename "$file" .md)
            local title=$(head -1 "$file" | sed 's/^# //')
            echo -e "  ${PURPLE}$task_id${NC}"
            echo "    $title"
        done
        echo ""
    fi
}

# 生成每日报告
cmd_daily() {
    local today=$(get_today_display)
    local report_file="$REPORTS_DIR/daily-$(get_today).md"
    
    mkdir -p "$REPORTS_DIR"
    
    local backlog=$(count_tasks "$TASKS_DIR/backlog")
    local active=$(count_tasks "$TASKS_DIR/active")
    local review=$(count_tasks "$TASKS_DIR/review")
    
    # 今日完成的工单
    local today_done_dir="$TASKS_DIR/done/$(get_month)"
    local today_done=0
    if [[ -d "$today_done_dir" ]]; then
        today_done=$(find "$today_done_dir" -name "$(get_today)*.md" 2>/dev/null | wc -l | tr -d ' ')
    fi
    
    cat > "$report_file" << EOF
# 📊 每日工单报告 - $today

## 状态概览

| 状态 | 数量 |
|------|------|
| 📋 待办 | $backlog |
| 🚀 进行中 | $active |
| 🔍 待验收 | $review |
| ✅ 今日完成 | $today_done |

## 🚀 进行中工单

EOF
    
    local has_active=false
    for file in "$TASKS_DIR/active"/*.md(N); do
        [[ -f "$file" ]] || continue
        has_active=true
        local task_id=$(basename "$file" .md)
        local title=$(head -1 "$file" | sed 's/^# //')
        echo "- **$task_id**: $title" >> "$report_file"
    done
    
    if [[ "$has_active" == false ]]; then
        echo "_暂无_" >> "$report_file"
    fi
    
    cat >> "$report_file" << EOF

## 🔍 待验收工单

EOF
    
    local has_review=false
    for file in "$TASKS_DIR/review"/*.md(N); do
        [[ -f "$file" ]] || continue
        has_review=true
        local task_id=$(basename "$file" .md)
        local title=$(head -1 "$file" | sed 's/^# //')
        echo "- **$task_id**: $title" >> "$report_file"
    done
    
    if [[ "$has_review" == false ]]; then
        echo "_暂无_" >> "$report_file"
    fi
    
    cat >> "$report_file" << EOF

---
_报告生成时间: $(date "+%Y-%m-%d %H:%M:%S")_
EOF
    
    echo -e "${GREEN}✅ 每日报告已生成${NC}"
    echo "   路径: $report_file"
    echo ""
    cat "$report_file"
}

# 搜索工单
cmd_find() {
    local keyword="$1"
    if [[ -z "$keyword" ]]; then
        echo -e "${RED}错误: 请提供搜索关键词${NC}"
        exit 1
    fi
    
    echo -e "${CYAN}🔍 搜索: $keyword${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    grep -rl "$keyword" "$TASKS_DIR" --include="*.md" 2>/dev/null | while read -r file; do
        [[ "$(basename "$file")" == _* ]] && continue
        local task_id=$(basename "$file" .md)
        local title=$(head -1 "$file" | sed 's/^# //')
        local dir=$(dirname "$file")
        local status=$(basename "$dir")
        echo -e "  ${GREEN}$task_id${NC} [${STATUS_ICONS[$status]:-📄} $status]"
        echo "    $title"
    done
}

# ============================================================
# 主入口
# ============================================================

case "${1:-help}" in
    new)
        cmd_new "$2"
        ;;
    list|ls)
        cmd_list "$2"
        ;;
    show|cat)
        cmd_show "$2"
        ;;
    move|mv)
        cmd_move "$2" "$3"
        ;;
    dashboard|dash|db)
        cmd_dashboard
        ;;
    daily)
        cmd_daily
        ;;
    find|search)
        cmd_find "$2"
        ;;
    help|--help|-h)
        print_help
        ;;
    *)
        echo -e "${RED}未知命令: $1${NC}"
        print_help
        exit 1
        ;;
esac

#!/bin/bash
# ==============================================================================
# sync_cursor.sh - 检查/修复所有项目的 Cursor 软链接状态
# 用法: bash ~/cursor-shared/scripts/sync_cursor.sh
# ==============================================================================

set -e

SHARED_DIR="$HOME/cursor-shared"
SHARED_RULES="$SHARED_DIR/rules"

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 需要同步的项目列表
PROJECTS=(
    "$HOME/useful_scripts"
    "$HOME/useful_scripts/execute"
    "$HOME/Downloads/zdwp"
    "$HOME/Documents/sync"
)

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔄 Cursor 配置同步检查${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

total_ok=0
total_broken=0
total_missing=0

for project in "${PROJECTS[@]}"; do
    if [[ ! -d "$project" ]]; then
        echo -e "${YELLOW}⚠️  项目不存在: $project${NC}"
        continue
    fi
    
    cursor_rules="$project/.cursor/rules"
    project_name=$(basename "$project")
    
    echo -e "${BLUE}📁 $project_name${NC} ($project)"
    
    if [[ ! -d "$cursor_rules" ]]; then
        echo -e "   ${YELLOW}⚠️  .cursor/rules/ 目录不存在${NC}"
        echo -e "   ${YELLOW}   运行: bash ~/cursor-shared/scripts/init_cursor.sh $project${NC}"
        ((total_missing++))
        echo ""
        continue
    fi
    
    # 检查软链接
    for link in "$cursor_rules"/shared-*.mdc "$cursor_rules"/global-*.mdc; do
        [[ -e "$link" ]] || continue
        
        link_name=$(basename "$link")
        
        if [[ -L "$link" ]]; then
            target=$(readlink "$link")
            if [[ -f "$target" ]]; then
                echo -e "   ${GREEN}✓${NC} $link_name → $target"
                ((total_ok++))
            else
                echo -e "   ${RED}✗${NC} $link_name → $target (断链!)"
                ((total_broken++))
            fi
        else
            echo -e "   ${YELLOW}⚠️${NC} $link_name (不是软链接)"
        fi
    done
    
    echo ""
done

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "📊 汇总: ${GREEN}$total_ok 正常${NC} | ${RED}$total_broken 断链${NC} | ${YELLOW}$total_missing 缺失${NC}"

if [[ $total_broken -gt 0 || $total_missing -gt 0 ]]; then
    echo ""
    echo -e "${YELLOW}💡 修复命令:${NC}"
    echo "   bash ~/cursor-shared/scripts/init_cursor.sh <项目路径>"
fi
echo ""


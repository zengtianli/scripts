#!/bin/bash
# ==============================================================================
# init_cursor.sh - 为项目初始化 Cursor 配置（软链接到共享规则）
# 用法: bash ~/cursor-shared/scripts/init_cursor.sh [项目路径]
# ==============================================================================

set -e

SHARED_DIR="$HOME/cursor-shared"
SHARED_RULES="$SHARED_DIR/rules"

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 项目路径（默认当前目录）
PROJECT_DIR="${1:-.}"
PROJECT_DIR=$(cd "$PROJECT_DIR" && pwd)
CURSOR_RULES="$PROJECT_DIR/.cursor/rules"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔧 Cursor 配置初始化${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "📁 项目路径: ${GREEN}$PROJECT_DIR${NC}"
echo -e "📁 共享规则: ${GREEN}$SHARED_RULES${NC}"
echo ""

# 创建 .cursor/rules 目录
mkdir -p "$CURSOR_RULES"
echo -e "${GREEN}✓${NC} 创建目录: .cursor/rules/"

# 共享规则列表
SHARED_RULES_LIST=(
    "shared-python.mdc"
    "shared-shell.mdc"
    "shared-script-library.mdc"
    "global-architecture.mdc"
)

# 可选规则（根据项目类型选择）
OPTIONAL_RULES=(
    "shared-pandas.mdc"
    "shared-gis.mdc"
    "shared-quarto.mdc"
    "shared-raycast.mdc"
    "shared-react.mdc"
    "shared-nvim.mdc"
)

echo ""
echo -e "${YELLOW}📋 创建共享规则软链接...${NC}"

# 创建核心规则软链接
for rule in "${SHARED_RULES_LIST[@]}"; do
    if [[ -f "$SHARED_RULES/$rule" ]]; then
        if [[ -L "$CURSOR_RULES/$rule" ]]; then
            echo -e "  ⏭️  已存在: $rule"
        else
            ln -sf "$SHARED_RULES/$rule" "$CURSOR_RULES/$rule"
            echo -e "  ${GREEN}✓${NC} 已链接: $rule"
        fi
    else
        echo -e "  ⚠️  源文件不存在: $rule"
    fi
done

echo ""
echo -e "${YELLOW}📋 可选规则（根据需要手动添加）:${NC}"
for rule in "${OPTIONAL_RULES[@]}"; do
    if [[ -f "$SHARED_RULES/$rule" ]]; then
        echo -e "  ln -sf $SHARED_RULES/$rule $CURSOR_RULES/"
    fi
done

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ 初始化完成！${NC}"
echo ""
echo -e "当前软链接状态:"
ls -la "$CURSOR_RULES/" 2>/dev/null | grep -E "\.mdc$" || echo "  (无规则文件)"
echo ""


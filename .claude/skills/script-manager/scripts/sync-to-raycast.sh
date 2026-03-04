#!/bin/bash
# ============================================================
# Raycast Wrapper 同步工具
# 用途：检查 scripts/ 下的脚本，自动创建缺失的 Raycast wrapper
# ============================================================

set -e

# 颜色定义
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# 路径定义
readonly SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
readonly SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
readonly PROJECT_ROOT="$(cd "$SKILL_DIR/../../.." && pwd)"
readonly SCRIPTS_DIR="$PROJECT_ROOT/scripts"
readonly RAYCAST_DIR="$PROJECT_ROOT/raycast/commands"

# ============================================================
# 工具函数
# ============================================================

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# ============================================================
# 类别和包名映射
# ============================================================

declare -A CATEGORY_PACKAGES=(
    ["document"]="Document"
    ["data"]="Data"
    ["file"]="File"
    ["system"]="System"
    ["network"]="Network"
    ["window"]="Window"
    ["tools"]="Tools"
    ["secretary"]="Secretary"
)

# ============================================================
# 检查和创建 wrapper
# ============================================================

check_wrapper_exists() {
    local script_file="$1"
    local wrapper_name="${script_file%.*}"  # 移除扩展名
    wrapper_name="${wrapper_name//_/-}"     # 下划线转连字符
    local wrapper_path="$RAYCAST_DIR/${wrapper_name}.sh"

    if [ -f "$wrapper_path" ]; then
        return 0  # wrapper 存在
    else
        return 1  # wrapper 不存在
    fi
}

create_wrapper() {
    local category="$1"
    local script_file="$2"
    local script_path="$3"

    local wrapper_name="${script_file%.*}"
    wrapper_name="${wrapper_name//_/-}"
    local wrapper_path="$RAYCAST_DIR/${wrapper_name}.sh"

    # 检测脚本语言
    local language="python"
    if [[ "$script_file" == *.sh ]]; then
        language="shell"
    fi

    # 生成默认元数据
    local title="$wrapper_name"
    local description="Auto-generated wrapper for $script_file"
    local mode="compact"
    local icon="🔧"
    local package="${CATEGORY_PACKAGES[$category]}"

    # 创建 wrapper
    cat > "$wrapper_path" <<EOF
#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title $title
# @raycast.description $description
# @raycast.mode $mode
# @raycast.icon $icon
# @raycast.packageName $package
EOF

    if [ "$language" = "python" ]; then
        echo "source \"\$(dirname \"\$0\")/../lib/run_python.sh\" && run_python \"$category/$script_file\" \"\$@\"" >> "$wrapper_path"
    else
        echo "source \"\$(dirname \"\$0\")/../lib/run_python.sh\" && run_shell \"$category/$script_file\" \"\$@\"" >> "$wrapper_path"
    fi

    chmod +x "$wrapper_path"
    print_success "已创建 wrapper: $wrapper_name.sh"
}

# ============================================================
# 扫描脚本
# ============================================================

scan_category() {
    local category="$1"
    local category_dir="$SCRIPTS_DIR/$category"

    if [ ! -d "$category_dir" ]; then
        return
    fi

    print_info "扫描类别: $category"

    local missing_count=0

    # 遍历该类别下的所有脚本
    for script_path in "$category_dir"/*.{py,sh}; do
        # 跳过不存在的文件（glob 未匹配时）
        [ -f "$script_path" ] || continue

        local script_file=$(basename "$script_path")

        # 检查 wrapper 是否存在
        if ! check_wrapper_exists "$script_file"; then
            print_warning "缺失 wrapper: $script_file"
            ((missing_count++))

            # 询问是否创建
            read -p "是否创建 wrapper? [y/N]: " confirm
            if [[ "$confirm" =~ ^[Yy]$ ]]; then
                create_wrapper "$category" "$script_file" "$script_path"
            fi
        fi
    done

    if [ $missing_count -eq 0 ]; then
        print_success "$category: 所有脚本都有对应的 wrapper"
    fi
}

# ============================================================
# 主函数
# ============================================================

main() {
    echo ""
    echo "=========================================="
    echo "  Raycast Wrapper 同步工具"
    echo "=========================================="
    echo ""

    # 扫描所有类别
    for category in document data file system network window tools secretary; do
        scan_category "$category"
        echo ""
    done

    print_success "扫描完成"
}

main "$@"

#!/bin/bash
# ============================================================
# 交互式脚本创建工具
# 用途：创建新的功能脚本和对应的 Raycast wrapper
# ============================================================

set -e

# 颜色定义
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# 路径定义
readonly SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
readonly SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
readonly PROJECT_ROOT="$(cd "$SKILL_DIR/../../.." && pwd)"
readonly SCRIPTS_DIR="$PROJECT_ROOT/scripts"
readonly RAYCAST_DIR="$PROJECT_ROOT/raycast/commands"
readonly TEMPLATES_DIR="$SKILL_DIR/references"

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
# 类别和前缀映射
# ============================================================

declare -A CATEGORY_PREFIXES=(
    ["document"]="docx_ md_ pptx_"
    ["data"]="xlsx_ csv_"
    ["file"]="file_ folder_"
    ["system"]="sys_ display_"
    ["network"]="clashx_"
    ["window"]="yabai_"
    ["tools"]="(无固定前缀)"
    ["secretary"]="sec_"
)

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
# 交互式输入
# ============================================================

select_category() {
    echo ""
    print_info "选择脚本类别："
    echo "1) document  - 文档处理 (docx_, md_, pptx_)"
    echo "2) data      - 数据转换 (xlsx_, csv_)"
    echo "3) file      - 文件操作 (file_, folder_)"
    echo "4) system    - 系统工具 (sys_, display_)"
    echo "5) network   - 网络代理 (clashx_)"
    echo "6) window    - 窗口管理 (yabai_)"
    echo "7) tools     - 杂项工具 (无固定前缀)"
    echo "8) secretary - 秘书系统 (sec_)"
    echo ""
    read -p "请选择 [1-8]: " choice

    case $choice in
        1) echo "document" ;;
        2) echo "data" ;;
        3) echo "file" ;;
        4) echo "system" ;;
        5) echo "network" ;;
        6) echo "window" ;;
        7) echo "tools" ;;
        8) echo "secretary" ;;
        *) print_error "无效选择"; exit 1 ;;
    esac
}

select_prefix() {
    local category="$1"
    local prefixes="${CATEGORY_PREFIXES[$category]}"

    if [ "$category" = "tools" ]; then
        echo ""
        return
    fi

    echo ""
    print_info "选择前缀："
    local i=1
    for prefix in $prefixes; do
        echo "$i) $prefix"
        ((i++))
    done
    echo ""
    read -p "请选择 [1-$((i-1))]: " choice

    local selected_prefix=$(echo "$prefixes" | awk "{print \$$choice}")
    if [ -z "$selected_prefix" ]; then
        print_error "无效选择"
        exit 1
    fi

    echo "$selected_prefix"
}

input_script_name() {
    echo ""
    read -p "输入脚本名称（不含前缀和扩展名）: " name
    # 转换为小写，替换空格为下划线
    name=$(echo "$name" | tr '[:upper:]' '[:lower:]' | tr ' ' '_')
    echo "$name"
}

select_language() {
    echo ""
    print_info "选择脚本语言："
    echo "1) Python (推荐)"
    echo "2) Shell"
    echo ""
    read -p "请选择 [1-2]: " choice

    case $choice in
        1) echo "python" ;;
        2) echo "shell" ;;
        *) print_error "无效选择"; exit 1 ;;
    esac
}

input_metadata() {
    echo ""
    read -p "脚本标题（Raycast 显示名称）: " title
    read -p "脚本描述: " description

    echo ""
    print_info "选择输出模式："
    echo "1) silent     - 无输出（后台运行）"
    echo "2) compact    - 简洁输出"
    echo "3) fullOutput - 完整输出"
    echo ""
    read -p "请选择 [1-3]: " mode_choice

    case $mode_choice in
        1) mode="silent" ;;
        2) mode="compact" ;;
        3) mode="fullOutput" ;;
        *) mode="compact" ;;
    esac

    read -p "图标 emoji: " icon
}

# ============================================================
# 文件生成
# ============================================================

create_python_script() {
    local script_path="$1"
    local script_name="$2"

    cp "$TEMPLATES_DIR/script-template.py" "$script_path"

    # 替换模板中的占位符
    sed -i '' "s/脚本功能描述/$script_name/" "$script_path"

    chmod +x "$script_path"
    print_success "已创建 Python 脚本: $script_path"
}

create_shell_script() {
    local script_path="$1"
    local script_name="$2"

    cp "$TEMPLATES_DIR/script-template.sh" "$script_path"

    # 替换模板中的占位符
    sed -i '' "s/脚本功能描述/$script_name/" "$script_path"

    chmod +x "$script_path"
    print_success "已创建 Shell 脚本: $script_path"
}

create_raycast_wrapper() {
    local wrapper_path="$1"
    local script_relative_path="$2"
    local title="$3"
    local description="$4"
    local mode="$5"
    local icon="$6"
    local package="$7"
    local language="$8"

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
        echo "source \"\$(dirname \"\$0\")/../lib/run_python.sh\" && run_python \"$script_relative_path\" \"\$@\"" >> "$wrapper_path"
    else
        echo "source \"\$(dirname \"\$0\")/../lib/run_python.sh\" && run_shell \"$script_relative_path\" \"\$@\"" >> "$wrapper_path"
    fi

    chmod +x "$wrapper_path"
    print_success "已创建 Raycast wrapper: $wrapper_path"
}

# ============================================================
# 主函数
# ============================================================

main() {
    echo ""
    echo "=========================================="
    echo "  脚本创建工具"
    echo "=========================================="

    # 1. 选择类别
    category=$(select_category)
    print_info "已选择类别: $category"

    # 2. 选择前缀
    prefix=$(select_prefix "$category")
    if [ -n "$prefix" ]; then
        print_info "已选择前缀: $prefix"
    fi

    # 3. 输入脚本名称
    script_name=$(input_script_name)
    if [ -z "$script_name" ]; then
        print_error "脚本名称不能为空"
        exit 1
    fi

    # 4. 选择语言
    language=$(select_language)
    print_info "已选择语言: $language"

    # 5. 输入元数据
    input_metadata

    # 6. 生成文件名
    if [ -n "$prefix" ]; then
        full_script_name="${prefix}${script_name}"
    else
        full_script_name="$script_name"
    fi

    if [ "$language" = "python" ]; then
        script_file="${full_script_name}.py"
    else
        script_file="${full_script_name}.sh"
    fi

    wrapper_file="${full_script_name//_/-}.sh"  # 下划线转连字符

    # 7. 生成路径
    script_path="$SCRIPTS_DIR/$category/$script_file"
    wrapper_path="$RAYCAST_DIR/$wrapper_file"
    script_relative_path="$category/$script_file"
    package="${CATEGORY_PACKAGES[$category]}"

    # 8. 检查文件是否已存在
    if [ -f "$script_path" ]; then
        print_error "脚本已存在: $script_path"
        exit 1
    fi

    if [ -f "$wrapper_path" ]; then
        print_error "Wrapper 已存在: $wrapper_path"
        exit 1
    fi

    # 9. 创建脚本
    echo ""
    print_info "正在创建文件..."

    if [ "$language" = "python" ]; then
        create_python_script "$script_path" "$full_script_name"
    else
        create_shell_script "$script_path" "$full_script_name"
    fi

    # 10. 创建 Raycast wrapper
    create_raycast_wrapper "$wrapper_path" "$script_relative_path" "$title" "$description" "$mode" "$icon" "$package" "$language"

    # 11. 完成
    echo ""
    print_success "脚本创建完成！"
    echo ""
    echo "功能脚本: $script_path"
    echo "Raycast wrapper: $wrapper_path"
    echo ""
    print_info "下一步："
    echo "1. 编辑功能脚本实现具体逻辑"
    echo "2. 运行验证: python3 $PROJECT_ROOT/lib/tools/health_check.py"
    echo "3. 在 Raycast 中测试"
}

main "$@"

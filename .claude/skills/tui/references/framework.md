# Shell TUI 框架详解

> 📅 更新：2025-12-17
> 📍 来源：backup.sh, doc.sh 开发经验

## 公共库

位置：`~/useful_scripts/system/_lib/`

### colors.sh - 颜色常量

```bash
# 重置
RST='\033[0m'

# 样式
BOLD='\033[1m'
DIM='\033[2m'
REVERSE='\033[7m'

# 前景色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'

# 高亮前景色
BRED='\033[1;31m'
BGREEN='\033[1;32m'
BYELLOW='\033[1;33m'
BBLUE='\033[1;34m'
BCYAN='\033[1;36m'
BWHITE='\033[1;37m'

# Box 字符
BOX_TL="╭"  BOX_TR="╮"
BOX_BL="╰"  BOX_BR="╯"
BOX_H="─"   BOX_V="│"
BOX_LT="├"  BOX_RT="┤"
```

### ui.sh - UI 组件

```bash
# 横线
line() {
    local char="${1:-─}" len="${2:-60}"
    printf '%*s' "$len" '' | tr ' ' "$char"
}

# Banner
banner() {
    local title="${1:-🔧 工具}"
    echo -e "${BCYAN}${BOX_TL}$(line $BOX_H 58)${BOX_TR}${RST}"
    echo -e "${BCYAN}${BOX_V}${RST}  ${BWHITE}${title}${RST}  ${BCYAN}${BOX_V}${RST}"
    echo -e "${BCYAN}${BOX_BL}$(line $BOX_H 58)${BOX_BR}${RST}"
}

# 日志
log_ok()    { echo -e "  ${BGREEN}✓${RST}  $1"; }
log_error() { echo -e "  ${BRED}✗${RST}  $1"; }
log_warn()  { echo -e "  ${BYELLOW}⚠${RST}  $1"; }
log_info()  { echo -e "  ${BBLUE}ℹ${RST}  $1"; }
log_step()  { echo -e "  ${BCYAN}➤${RST}  ${BOLD}$1${RST}"; }
```

### tui.sh - TUI 核心

```bash
# 光标控制
tui_hide_cursor() { tput civis 2>/dev/null || true; }
tui_show_cursor() { tput cnorm 2>/dev/null || true; }
tui_clear() { tput clear 2>/dev/null || clear 2>/dev/null || true; }

# 读取按键（支持方向键）
read_key() {
    local key
    IFS= read -rsn1 key
    
    if [[ "$key" == $'\x1b' ]]; then
        read -rsn2 -t 0.1 key
        case "$key" in
            '[A') echo 'up' ;;
            '[B') echo 'down' ;;
            '[C') echo 'right' ;;
            '[D') echo 'left' ;;
            *)    echo 'esc' ;;
        esac
    elif [[ "$key" == '' ]]; then
        echo 'enter'
    elif [[ "$key" == ' ' ]]; then
        echo 'space'
    else
        echo "$key"
    fi
}
```

## 主循环模板

```bash
cmd_manage() {
    # 初始化
    load_data
    tui_hide_cursor
    trap 'tui_show_cursor' EXIT INT TERM
    
    CURSOR=0
    NEED_REFRESH=true
    
    # 主循环
    while true; do
        [[ "$NEED_REFRESH" == true ]] && { draw_screen; NEED_REFRESH=false; }
        
        case $(read_key) in
            j|down) ((CURSOR < MAX-1)) && ((CURSOR++)) && NEED_REFRESH=true ;;
            k|up)   ((CURSOR > 0)) && ((CURSOR--)) && NEED_REFRESH=true ;;
            space)  toggle_select; NEED_REFRESH=true ;;
            enter)  show_detail ;;
            q)      tui_show_cursor; return 0 ;;
        esac
    done
}
```

## 踩坑记录

### 1. set -e 与 [[ ]] 返回值

**问题**: `[[ $x -lt 0 ]] && x=0` 当条件为 false 时，整行返回 1，触发 `set -e` 退出。

**解决**: 用 if 语句，或在函数末尾加 `return 0`。

### 2. 子 shell 无法访问修改后的全局数组

**问题**: `$(func)` 在子 shell 执行，无法读取父 shell 中被修改的数组。

**解决**: 直接在调用处遍历数组，不用函数返回。

```bash
# 错误
local indices=($(get_selected_indices))

# 正确
local indices=()
local i
for ((i=0; i<COUNT; i++)); do
    [[ ${SELECTED[$i]} -eq 1 ]] && indices+=("$i")
done
```

### 3. tput 在非交互环境失败

**问题**: 管道执行时 `tput clear` 返回非零。

**解决**: 加 `|| true` 容错。

### 4. printf %s 不解析 ANSI 转义

**问题**: 变量中的 `\033[...` 被原样输出。

**解决**: 用 `%b` 代替 `%s`。

### 5. for 循环 i 变量污染

**问题**: `for ((i=0; ...))` 中的 i 会覆盖外部变量。

**解决**: 在 for 前声明 `local i`。

## 完整示例

- backup.sh - 操作优先模式：`~/useful_scripts/system/backup.sh`
- doc.sh - 文件优先模式：`~/useful_scripts/system/doc.sh`

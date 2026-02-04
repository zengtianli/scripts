---
name: dev-tui
description: Shell TUI 开发规范。lazygit 风格命令行界面、公共库、常见陷阱。当开发 Shell 交互界面时触发。
---

# Shell TUI 开发规范

> 适用于开发类似 lazygit 风格的命令行交互界面

## 公共库位置

```
~/useful_scripts/system/_lib/
├── colors.sh   # 颜色常量
├── ui.sh       # UI 组件 (banner, section, log_*)
└── tui.sh      # TUI 核心 (光标、按键)
```

## 快速开始

```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 加载公共库
source "$SCRIPT_DIR/_lib/colors.sh"
source "$SCRIPT_DIR/_lib/ui.sh"
source "$SCRIPT_DIR/_lib/tui.sh"

# 使用
banner "🔧 我的工具"
log_ok "成功！"
```

## 命名规范

| 类型 | 前缀 | 示例 |
|------|------|------|
| 颜色常量 | 无/B | `RED`, `BRED` (高亮) |
| 边框字符 | BOX_ | `BOX_TL`, `BOX_H` |
| TUI 函数 | tui_ | `tui_clear`, `tui_hide_cursor` |
| UI 组件 | 无 | `banner`, `section`, `log_ok` |

## 常见陷阱

### 1. set -e 与数组访问

```bash
# ❌ 错误：[[ ]] 返回 false 会触发 exit
[[ $CURSOR -lt 0 ]] && CURSOR=0

# ✅ 正确：显式 if
if [[ $CURSOR -lt 0 ]]; then CURSOR=0; fi
```

### 2. 子 shell 无法访问修改后的数组

```bash
# ❌ 错误：子 shell 中数组是旧值
local indices=($(get_selected_indices))

# ✅ 正确：直接遍历
local indices=()
local i
for ((i=0; i<COUNT; i++)); do
    [[ ${SELECTED[$i]} -eq 1 ]] && indices+=("$i")
done
```

### 3. tput 在非交互环境失败

```bash
# ❌ 错误：管道执行时报错
tui_clear() { tput clear; }

# ✅ 正确：容错处理
tui_clear() { tput clear 2>/dev/null || clear 2>/dev/null || true; }
```

### 4. printf %s 不解析 ANSI

```bash
# ❌ 错误：颜色代码被原样输出
printf "%s\n" "$status"

# ✅ 正确：用 %b 解析转义
printf "%b\n" "$status"
```

### 5. for 循环变量作用域

```bash
# ❌ 错误：i 污染全局
for ((i=0; i<N; i++)); do ... done

# ✅ 正确：声明 local
local i
for ((i=0; i<N; i++)); do ... done
```

## 最佳实践

1. **trap 清理光标**: `trap 'tui_show_cursor' EXIT INT TERM`
2. **主循环模式**: `while true; case $(read_key) in ... esac; done`
3. **NEED_REFRESH 标记**: 避免每次按键都重绘
4. **模块化拆分**: 业务逻辑与 UI 分离

## 主循环模板

```bash
cmd_manage() {
    load_data
    tui_hide_cursor
    trap 'tui_show_cursor' EXIT INT TERM
    
    CURSOR=0
    NEED_REFRESH=true
    
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

## 参考资料

- 框架详解：`references/framework.md`
- 文件优先模式：`references/file-first.md`
- 完整示例：`~/useful_scripts/system/backup.sh`

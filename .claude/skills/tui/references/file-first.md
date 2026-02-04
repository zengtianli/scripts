# TUI 文件优先交互模式

> 📅 更新：2025-12-17
> 📍 参考实现：`system/doc.sh` + `system/doc/manage.sh`

## 设计理念

**核心原则：先选文件，再选操作**

```
用户打开工具 → 看到文件列表 → 选择文件 → 看到可用操作 → 执行
```

❌ 反模式：先选操作，再输入文件路径（反人类）
✅ 正确模式：先浏览文件，再选择操作（符合直觉）

## 目录结构

```
system/
├── _lib/                    # 公共库（所有工具共享）
│   ├── colors.sh
│   ├── ui.sh
│   └── tui.sh
├── <tool>.sh               # 主入口脚本
└── <tool>/                 # 工具模块目录
    ├── config.sh           # 配置
    ├── <功能>.sh           # 功能模块
    └── manage.sh           # TUI 管理面板
```

## 全局状态变量

```bash
# 文件列表状态
declare -a FILE_LIST=()       # 文件完整路径
declare -a FILE_NAMES=()      # 文件名
declare -a FILE_TYPES=()      # 文件扩展名
declare -a FILE_SIZES=()      # 文件大小
declare -a FILE_DATES=()      # 修改日期
CURSOR=0                      # 当前选中索引
FILE_COUNT=0                  # 文件总数

# 视图状态
NEED_REFRESH=true             # 是否需要重绘
CURRENT_DIR=""                # 当前目录
VIEW_MODE="list"              # list | action

# 操作菜单状态
ACTION_CURSOR=0               # 操作菜单光标
declare -a ACTIONS=()         # 操作 ID 列表
declare -a ACTION_NAMES=()    # 操作显示名称
```

## 核心函数

### 文件扫描 scan_files()

```bash
scan_files() {
    local dir="$1"
    
    FILE_LIST=()
    FILE_NAMES=()
    FILE_TYPES=()
    FILE_SIZES=()
    FILE_DATES=()
    
    while IFS= read -r -d '' file; do
        [[ -f "$file" ]] || continue
        
        local name ext size date
        name=$(basename "$file")
        ext="${name##*.}"
        ext=$(echo "$ext" | tr '[:upper:]' '[:lower:]')
        size=$(ls -lh "$file" 2>/dev/null | awk '{print $5}')
        date=$(stat -f "%Sm" -t "%Y-%m-%d" "$file" 2>/dev/null)
        
        FILE_LIST+=("$file")
        FILE_NAMES+=("$name")
        FILE_TYPES+=("$ext")
        FILE_SIZES+=("$size")
        FILE_DATES+=("$date")
    done < <(find "$dir" -maxdepth 1 -type f \( \
        -iname "*.docx" -o -iname "*.md" -o -iname "*.pdf" \
    \) -print0 2>/dev/null | sort -z)
    
    FILE_COUNT=${#FILE_LIST[@]}
    
    # ⚠️ 使用 if 而非 && 避免 set -e 陷阱
    if [[ $CURSOR -ge $FILE_COUNT ]]; then
        CURSOR=$((FILE_COUNT - 1))
    fi
    if [[ $CURSOR -lt 0 ]]; then
        CURSOR=0
    fi
}
```

### 获取可用操作 get_actions_for_file()

```bash
get_actions_for_file() {
    local file_type="$1"
    
    ACTIONS=()
    ACTION_NAMES=()
    
    case "$file_type" in
        docx|doc)
            ACTIONS=("to_md" "to_pdf" "read")
            ACTION_NAMES=(
                "📝 转换为 Markdown"
                "📑 转换为 PDF"
                "👁️  读取内容"
            )
            ;;
        md)
            ACTIONS=("to_docx" "read")
            ACTION_NAMES=(
                "📄 转换为 DOCX"
                "👁️  读取内容"
            )
            ;;
    esac
    
    ACTION_CURSOR=0
}
```

## 按键处理规范

### 文件列表模式

| 按键 | 功能 |
|------|------|
| `j` / `↓` | 下移光标 |
| `k` / `↑` | 上移光标 |
| `g` | 跳到第一项 |
| `G` | 跳到最后一项 |
| `Enter` | 进入操作菜单 |
| `c` | 切换目录 |
| `r` | 刷新列表 |
| `q` | 退出 |

### 操作菜单模式

| 按键 | 功能 |
|------|------|
| `j` / `↓` | 下移光标 |
| `k` / `↑` | 上移光标 |
| `Enter` | 执行操作 |
| `1-9` | 数字快捷键执行 |
| `Esc` / `q` | 返回列表 |

## UI 布局

### 文件列表布局

```
╭──────────────────────────────────────────────────────────────────╮
│  📄 工具名称                       目录: ~/Downloads              │
╰──────────────────────────────────────────────────────────────────╯

╭── 📁 文件列表 (5 个) ────────────────────────────────────────────╮
│      文件名                           类型   日期         大小   │
├──────────────────────────────────────────────────────────────────┤
│ ▸ 📄 document.docx                    docx   2024-12-17   128KB  │  ← 选中行反色
│   📝 readme.md                        md     2024-12-16   12KB   │
│   📕 report.pdf                       pdf    2024-12-15   2.1MB  │
╰──────────────────────────────────────────────────────────────────╯

╭── 💡 快捷键 ─────────────────────────────────────────────────────╮
│  j/k 移动    Enter 操作    c 切换目录    r 刷新    q 退出        │
╰──────────────────────────────────────────────────────────────────╯
```

## 常见陷阱

### 1. set -e 与 && 陷阱

```bash
# ❌ 错误
[[ $CURSOR -lt 0 ]] && CURSOR=0

# ✅ 正确
if [[ $CURSOR -lt 0 ]]; then
    CURSOR=0
fi
```

### 2. ~ 路径显示

```bash
# ❌ 错误
local dir_display="${CURRENT_DIR/$HOME/\~}"

# ✅ 正确
local dir_display="${CURRENT_DIR/$HOME/~}"
```

### 3. 数组在子 shell 中不可见

```bash
# ❌ 错误：管道创建子 shell
find ... | while read file; do
    FILE_LIST+=("$file")
done

# ✅ 正确：使用进程替换
while read -r -d '' file; do
    FILE_LIST+=("$file")
done < <(find ... -print0)
```

## 快速开始

复制 `doc.sh` + `doc/` 目录作为模板，然后：

1. 修改 `config.sh` 中的路径和依赖
2. 修改 `scan_files()` 中的文件类型匹配
3. 修改 `get_actions_for_file()` 中的操作映射
4. 实现对应的 `do_*` 功能函数
5. 更新 `usage()` 帮助信息

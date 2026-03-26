#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title 生活报告
# @raycast.mode fullOutput
# @raycast.packageName 秘书系统

# Optional parameters:
# @raycast.icon 📊
# @raycast.argument1 { "type": "text", "placeholder": "天数（默认：7）", "optional": true }
# @raycast.argument2 { "type": "dropdown", "placeholder": "模式", "optional": true, "data": [{"title": "按时间", "value": "time"}, {"title": "按类别", "value": "category"}, {"title": "统计", "value": "summary"}] }

# Documentation:
# @raycast.description 查看生活日志报告（按时间/按类别/统计）
# @raycast.author tianli
# @raycast.authorURL https://github.com/tianli

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 调用 Python 脚本
PYTHON_BIN=$(which python3)
SCRIPT_PATH="$HOME/useful_scripts/scripts/secretary/life_report.py"

# 构建参数
ARGS=()

if [ -n "$1" ]; then
    ARGS+=("-d" "$1")
fi

if [ -n "$2" ]; then
    ARGS+=("-m" "$2")
fi

"$PYTHON_BIN" "$SCRIPT_PATH" "${ARGS[@]}"

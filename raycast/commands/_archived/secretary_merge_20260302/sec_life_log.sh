#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title 生活日志
# @raycast.mode fullOutput
# @raycast.packageName 秘书系统

# Optional parameters:
# @raycast.icon 📝
# @raycast.argument1 { "type": "text", "placeholder": "记录内容（留空进入交互模式）", "optional": true }

# Documentation:
# @raycast.description 记录生活日志（健康、社交、家庭、爱好、待办、事件）
# @raycast.author tianli
# @raycast.authorURL https://github.com/tianli

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 调用 Python 脚本
PYTHON_BIN="/Users/tianli/miniforge3/bin/python3"
SCRIPT_PATH="$HOME/useful_scripts/scripts/secretary/life_log.py"

if [ -n "$1" ]; then
    # 有参数，直接记录
    "$PYTHON_BIN" "$SCRIPT_PATH" "$1"
else
    # 无参数，进入交互模式
    "$PYTHON_BIN" "$SCRIPT_PATH"
fi

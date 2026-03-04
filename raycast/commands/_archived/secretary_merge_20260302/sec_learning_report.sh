#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title 学习秘书 - 查看报告
# @raycast.mode fullOutput

# Optional parameters:
# @raycast.icon 📊
# @raycast.packageName 秘书系统
# @raycast.argument1 { "type": "text", "placeholder": "天数（默认7天）", "optional": true }

# Documentation:
# @raycast.description 查看学习报告，按时间、分类、标签统计
# @raycast.author tianli

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Python 路径
PYTHON="/Users/tianli/miniforge3/bin/python3"

# 获取天数参数（默认 7 天）
DAYS="${1:-7}"

# 执行 Python 脚本
"$PYTHON" "$SCRIPT_DIR/../../scripts/secretary/learning_report.py" "$DAYS"

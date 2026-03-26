#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title 学习秘书 - 记录笔记
# @raycast.mode fullOutput

# Optional parameters:
# @raycast.icon 📚
# @raycast.packageName 秘书系统

# Documentation:
# @raycast.description 记录学习笔记、阅读进度、课程学习等
# @raycast.author tianli

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Python 路径
PYTHON=$(which python3)

# 执行 Python 脚本
"$PYTHON" "$SCRIPT_DIR/../../scripts/secretary/learning_log.py"

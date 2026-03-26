#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title 个人报告
# @raycast.mode fullOutput
# @raycast.packageName 秘书系统

# Optional parameters:
# @raycast.icon 📊

# Documentation:
# @raycast.description 查看个人发展记录报告
# @raycast.author tianli

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 引用公共库
source "$SCRIPT_DIR/../lib/common.sh"

# 调用 Python 脚本
run_python "secretary/personal_report.py"

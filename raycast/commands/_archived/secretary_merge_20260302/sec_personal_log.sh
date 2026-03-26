#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.packageName 秘书系统
# @raycast.title 记录个人
# @raycast.description 记录投资、学习、健康、社交、家庭等个人发展内容
# @raycast.icon 🌟
# @raycast.mode fullOutput
source "$(dirname "$0")/../lib/run_python.sh" && run_python "secretary/personal_log.py" "$@"

#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title 投资记录
# @raycast.mode fullOutput
# @raycast.icon 💰
# @raycast.packageName 秘书系统
# @raycast.description 投资秘书 - 记录投资想法
source "$(dirname "$0")/../lib/run_python.sh" && run_python "secretary/investment_log.py" "$@"

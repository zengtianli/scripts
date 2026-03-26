#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title 投资报告
# @raycast.mode fullOutput
# @raycast.icon 📊
# @raycast.packageName 秘书系统
# @raycast.description 投资秘书 - 查看投资报告
# @raycast.argument1 { "type": "text", "placeholder": "天数（默认7天）", "optional": true }
source "$(dirname "$0")/../lib/run_python.sh" && run_python "secretary/investment_report.py" "$@"

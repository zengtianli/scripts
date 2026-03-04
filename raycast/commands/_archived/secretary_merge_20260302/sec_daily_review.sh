#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.packageName 秘书系统
# @raycast.title 每日回顾
# @raycast.description 添加今日评估和反思，生成完整每日总结
# @raycast.icon 📝
# @raycast.mode fullOutput
source "$(dirname "$0")/../lib/run_python.sh" && run_python "secretary/daily_summary.py" --mode review

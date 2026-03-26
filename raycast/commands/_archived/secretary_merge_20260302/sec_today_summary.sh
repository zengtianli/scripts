#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title 今日总结
# @raycast.mode fullOutput
# @raycast.icon 📊
# @raycast.packageName 秘书系统
# @raycast.description 查看今日工作汇总（应用使用 + 三个秘书记录）
source "$(dirname "$0")/../lib/run_python.sh" && run_python "secretary/daily_summary.py" --mode summary

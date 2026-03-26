#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.packageName 秘书系统
# @raycast.title 每日报告
# @raycast.description 生成每日工作报告，整合应用追踪和秘书日志
# @raycast.icon 📊
# @raycast.mode fullOutput
source "$(dirname "$0")/../lib/run_python.sh" && run_python "secretary/daily_report.py" "$@"

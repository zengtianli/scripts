#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title 本周工作报告
# @raycast.mode fullOutput
# @raycast.icon 📈
# @raycast.packageName Work Tracker
# @raycast.description 查看本周应用使用报告
source "$(dirname "$0")/../lib/run_python.sh" && run_python "system/app_report.py" --week

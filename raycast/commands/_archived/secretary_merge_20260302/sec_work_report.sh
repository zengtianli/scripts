#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title 工作报告
# @raycast.mode fullOutput
# @raycast.icon 📊
# @raycast.packageName 秘书系统
# @raycast.description 工作秘书 - 查看工作报告
source "$(dirname "$0")/../lib/run_python.sh" && run_python "secretary/work_report.py" "$@"

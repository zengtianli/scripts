#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.packageName 秘书系统
# @raycast.title 记录工作
# @raycast.description 记录工作日志、项目进展、会议记录等
# @raycast.icon 💼
# @raycast.mode fullOutput
source "$(dirname "$0")/../lib/run_python.sh" && run_python "secretary/work_log.py" "$@"

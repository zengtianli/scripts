#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title 明日计划
# @raycast.mode fullOutput
# @raycast.icon 📅
# @raycast.packageName 秘书系统
# @raycast.description 制定明日工作计划
source "$(dirname "$0")/../lib/run_python.sh" && run_python "secretary/daily_summary.py" --mode plan

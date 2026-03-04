#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title 水效评估分析系统
# @raycast.mode fullOutput
# @raycast.icon 💧
# @raycast.packageName Hydraulic
# @raycast.description 启动水效评估分析 Streamlit 应用
source "$(dirname "$0")/../lib/run_python.sh" && run_streamlit "water_efficiency" "app.py" --server.port 8502

#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title 地理编码工具
# @raycast.mode silent
# @raycast.icon 📍
# @raycast.packageName Hydraulic
# @raycast.description 启动地理编码 Streamlit 应用
source "$(dirname "$0")/../lib/run_python.sh" && run_streamlit "geocode"

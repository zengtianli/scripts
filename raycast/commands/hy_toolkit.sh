#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title 水利工具集
# @raycast.mode fullOutput
# @raycast.icon 🧰
# @raycast.packageName Hydraulic
# @raycast.description 启动水利工具集 Portal
source "$(dirname "$0")/../lib/run_python.sh" && run_streamlit "hydro_toolkit"

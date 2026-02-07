#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title 纳污能力计算
# @raycast.mode silent
# @raycast.packageName Hydraulic

# Optional parameters:
# @raycast.icon 🌊
# @raycast.description 启动纳污能力计算 Streamlit 应用

cd "$(dirname "$0")/../../.assets/projects/capacity"
open "http://localhost:8501" &
streamlit run web_app.py

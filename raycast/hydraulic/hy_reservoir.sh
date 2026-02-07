#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title 水库发电调度
# @raycast.mode silent
# @raycast.packageName Hydraulic

# Optional parameters:
# @raycast.icon 🏗️
# @raycast.description 启动水库发电调度 Streamlit 应用

cd "$(dirname "$0")/../../.assets/projects/reservoir_schedule"
open "http://localhost:8501" &
streamlit run app.py

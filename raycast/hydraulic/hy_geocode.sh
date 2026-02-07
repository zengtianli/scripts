#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title 地理编码工具
# @raycast.mode silent
# @raycast.packageName Hydraulic

# Optional parameters:
# @raycast.icon 📍
# @raycast.description 启动地理编码/逆编码 Streamlit 应用

cd "$(dirname "$0")/../../.assets/projects/geocode"
open "http://localhost:8501" &
streamlit run app.py

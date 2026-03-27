#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title 地理编码工具
# @raycast.mode fullOutput
# @raycast.icon 📍
# @raycast.packageName Hydraulic
# @raycast.description 启动地理编码 Streamlit 应用
cd "$HOME/Dev/hydro-geocode" && exec streamlit run app.py

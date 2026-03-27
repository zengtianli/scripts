#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title 纳污能力计算
# @raycast.mode fullOutput
# @raycast.icon 🌊
# @raycast.packageName Hydraulic
# @raycast.description 启动纳污能力计算 Streamlit 应用
cd "$HOME/Dev/hydro-capacity" && exec streamlit run app.py

#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title 水库发电调度
# @raycast.mode fullOutput
# @raycast.icon 🏗️
# @raycast.packageName Hydraulic
# @raycast.description 启动水库发电调度 Streamlit 应用
cd "$HOME/Dev/hydro-reservoir" && exec streamlit run app.py

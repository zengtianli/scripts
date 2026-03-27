#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title 水利工具集
# @raycast.mode fullOutput
# @raycast.icon 🧰
# @raycast.packageName Hydraulic
# @raycast.description 启动水利工具集 Portal
cd "$HOME/Dev/hydro-toolkit" && exec streamlit run app.py

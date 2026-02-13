#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title 水效评估分析系统
# @raycast.mode compact

# Optional parameters:
# @raycast.icon 💧
# @raycast.packageName Hydraulic

cd "$(dirname "$0")/../../.assets/projects/water_efficiency" || exit 1
streamlit run app.py --server.port 8502

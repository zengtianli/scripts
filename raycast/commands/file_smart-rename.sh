#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Smart Rename Downloads
# @raycast.mode fullOutput

# Optional parameters:
# @raycast.icon 🏷️
# @raycast.packageName File Utils
# @raycast.description AI-powered file analysis and rename suggestions

/Users/tianli/miniforge3/bin/python3 /Users/tianli/Dev/scripts/scripts/file/smart_rename.py analyze --all

echo ""
echo "========================================="
echo "建议表已生成: ~/Downloads/_rename_plan.md"
echo "请审核后运行: smart_rename.py execute"
echo "========================================="

#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title yabai-org
# @raycast.mode silent
# @raycast.icon 🪟
# @raycast.packageName YABAI
source "$(dirname "$0")/../lib/run_python.sh" && run_python "window/yabai_org.py" "$@"

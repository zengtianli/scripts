#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title yabai-float
# @raycast.mode silent
# @raycast.icon 🪟
source "$(dirname "$0")/../lib/run_python.sh" && run_python "window/yabai_float.py" "$@"

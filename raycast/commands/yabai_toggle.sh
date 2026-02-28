#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title yabai-toggle
# @raycast.mode fullOutput
# @raycast.icon 🪟
source "$(dirname "$0")/../lib/run_python.sh" && run_python "yabai_toggle.py" "$@"

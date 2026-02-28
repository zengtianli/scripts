#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title yabai-mouse-follow
# @raycast.mode compact
# @raycast.icon 🖱️
source "$(dirname "$0")/../lib/run_python.sh" && run_python "yabai_mouse_follow.py" "$@"

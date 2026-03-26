#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title folder-move-up-remove
# @raycast.mode fullOutput
# @raycast.icon 🗂️
# @raycast.packageName File Operations
# @raycast.description Move all files up one level and remove empty folder
source "$(dirname "$0")/../lib/run_python.sh" && run_python "file/folder_move_up_remove.py" "$@"

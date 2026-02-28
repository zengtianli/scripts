#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title folder-move-up-remove
# @raycast.mode fullOutput
# @raycast.icon 🗂️
# @raycast.packageName Folders
source "$(dirname "$0")/../lib/run_python.sh" && run_python "file/folder_move_up_remove.py" "$@"

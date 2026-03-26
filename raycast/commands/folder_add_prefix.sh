#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title folder-add-prefix
# @raycast.mode fullOutput
# @raycast.icon 📝
# @raycast.packageName File Operations
# @raycast.description Add folder name as prefix to all files in folder
source "$(dirname "$0")/../lib/run_python.sh" && run_python "file/folder_add_prefix.py" "$@"

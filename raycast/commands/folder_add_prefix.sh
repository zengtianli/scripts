#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title folder-add-prefix
# @raycast.mode fullOutput
# @raycast.icon 📝
# @raycast.packageName Folders
source "$(dirname "$0")/../lib/run_python.sh" && run_python "file/folder_add_prefix.py" "$@"

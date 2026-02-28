#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title folder-create
# @raycast.mode fullOutput
# @raycast.icon 📁
# @raycast.packageName Folders
source "$(dirname "$0")/../lib/run_python.sh" && run_python "file/folder_create.py" "$@"

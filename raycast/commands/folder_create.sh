#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title folder-create
# @raycast.mode fullOutput
# @raycast.icon 📁
# @raycast.packageName File Operations
# @raycast.description Create new folder in Finder with auto-numbering
source "$(dirname "$0")/../lib/run_python.sh" && run_python "file/folder_create.py" "$@"

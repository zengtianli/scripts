#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title xlsx-from-txt
# @raycast.mode fullOutput
# @raycast.icon 📊
# @raycast.packageName Scripts
source "$(dirname "$0")/../lib/run_python.sh" && run_python "xlsx_from_txt.py" "$@"

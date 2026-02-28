#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title xlsx-lowercase
# @raycast.mode fullOutput
# @raycast.icon 📊
# @raycast.packageName Scripts
source "$(dirname "$0")/../lib/run_python.sh" && run_python "data/xlsx_lowercase.py" "$@"

#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title xlsx-from-xls
# @raycast.description Convert .xls files to .xlsx format
# @raycast.mode fullOutput
# @raycast.icon 📊
# @raycast.packageName Scripts
source "$(dirname "$0")/../lib/run_python.sh" && run_python "data/xlsx_from_xls.py" "$@"

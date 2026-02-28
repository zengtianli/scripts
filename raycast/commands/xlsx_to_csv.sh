#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title xlsx-to-csv
# @raycast.mode fullOutput
# @raycast.icon 📊
# @raycast.packageName Scripts
source "$(dirname "$0")/../lib/run_python.sh" && run_python "xlsx_to_csv.py" "$@"

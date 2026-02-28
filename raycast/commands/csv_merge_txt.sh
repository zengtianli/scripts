#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title csv-merge-txt
# @raycast.mode fullOutput
# @raycast.icon 📊
# @raycast.packageName Scripts
source "$(dirname "$0")/../lib/run_python.sh" && run_python "csv_merge_txt.py" "$@"

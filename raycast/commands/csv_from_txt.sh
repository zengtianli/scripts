#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title csv-from-txt
# @raycast.mode fullOutput
# @raycast.icon 📊
# @raycast.packageName Scripts
source "$(dirname "$0")/../lib/run_python.sh" && run_python "csv_from_txt.py" "$@"

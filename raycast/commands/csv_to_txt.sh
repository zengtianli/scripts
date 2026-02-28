#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title csv-to-txt
# @raycast.mode fullOutput
# @raycast.icon 📊
# @raycast.packageName Scripts
source "$(dirname "$0")/../lib/run_python.sh" && run_python "data/csv_to_txt.py" "$@"

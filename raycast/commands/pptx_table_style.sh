#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title pptx-table
# @raycast.mode fullOutput
# @raycast.icon 📽️
# @raycast.packageName Scripts
source "$(dirname "$0")/../lib/run_python.sh" && run_python "pptx_table_style.py" "$@"

#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title md-format
# @raycast.mode fullOutput
# @raycast.icon 📝
# @raycast.packageName Scripts
source "$(dirname "$0")/../lib/run_python.sh" && run_python "md_formatter.py" "$@"

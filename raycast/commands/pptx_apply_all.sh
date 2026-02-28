#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title pptx-all
# @raycast.mode fullOutput
# @raycast.icon 📽️
# @raycast.packageName Scripts
source "$(dirname "$0")/../lib/run_python.sh" && run_python "pptx_apply_all.py" "$@"

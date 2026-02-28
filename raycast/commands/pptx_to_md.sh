#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title pptx-to-md
# @raycast.mode fullOutput
# @raycast.icon 📽️
# @raycast.packageName Scripts
source "$(dirname "$0")/../lib/run_python.sh" && run_python "pptx_to_md.py" "$@"
